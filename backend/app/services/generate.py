import datetime
from app.services.ingestion_pipeline import process_files
from app.services.db_file import update_db_file_status, mark_db_stack_as_processed, get_db_files_by_status
from app.services.database import get_session
from app.services.datasource import get_datasource_identifier_from_path
from app.services.llama_index import delete_file_llama_index
from app.services.ollama_status import is_ollama_server_reachable, wait_for_ollama_models_to_be_downloaded
from app.database.models import File, FileStatus
from app.settings.models import AppSettings

from sqlalchemy.orm import Session
import json
import time
import logging

logger = logging.getLogger("uvicorn")
    
async def process_queued_files(
        session: Session,
        app_settings: AppSettings
    ):
    """Processing loop"""
    try:
        # Check if the ollama server is reachable
        if not await is_ollama_server_reachable(app_settings.ollama.llm_host):
            # We can't process files if the ollama server is not reachable, skip this processing request
            logger.error("Ollama server is not reachable, skipping processing request")
            return

        # Wait for Ollama models to be downloaded
        await wait_for_ollama_models_to_be_downloaded(app_settings)
        
        # Run forever
        while True:
            try:
                # Process all files marked as processing that have been interrupted with unfinished processing
                _process_files_marked_as_processing(session, app_settings)

                # Process all queued files
                _process_all_queued_files(session, app_settings)
            except Exception as e:
                logger.error(f"Processing loop error, retrying: {str(e)}")
                time.sleep(2)
            
            # Wait
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"Processing loop error: {str(e)}")

def _process_files_marked_as_processing(session, app_settings: AppSettings):
    """Process all files marked as processing"""
    try:
        with get_session() as session:            
            while True:
                try:
                    # Get the files one by one so that in case of queued file changes we get the freshest database data
                    oldest_processing_file = session.query(File).filter(
                        File.status == FileStatus.PROCESSING
                    ).order_by(
                        File.uploaded_at.asc()
                    ).first()

                    # If there are no more files marked as processing, return
                    if not oldest_processing_file:
                        return

                    # Move the processed stacks to the stacks_to_process column as we will delete all already processed stacks from llama index                    
                    processed_stacks = json.loads(oldest_processing_file.processed_stacks)
                    stacks_to_process = json.loads(oldest_processing_file.stacks_to_process)
                    stacks_to_process.extend(processed_stacks)
                    oldest_processing_file.stacks_to_process = json.dumps(stacks_to_process)
                    oldest_processing_file.processed_stacks = json.dumps([])
                    session.commit()

                    logger.info(f"Reprocessing interrupted file: {oldest_processing_file.path}")
                    try:
                        delete_file_llama_index(session, oldest_processing_file.path)
                    except Exception as e:
                        logger.error(f"Failed to delete {oldest_processing_file.path} from stores: {str(e)}")
                        
                    _process_single_file(session, oldest_processing_file, app_settings)
                except Exception as e:
                    logger.error(f"Failed to process interrupted file {oldest_processing_file.path}: {str(e)}, marking as error")
                    try:
                        update_db_file_status(session, oldest_processing_file.path, FileStatus.ERROR)
                    except Exception as e:
                        logger.error(f"Failed to update file status for {oldest_processing_file.path}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        return False
        
def _process_all_queued_files(session, app_settings: AppSettings) -> bool:
    """Process all queued files"""
    try:
        with get_session() as session:
            while True:
                try:
                    # Get the files one by one so that in case of queued file changes we get the freshest database data
                    # Get oldest queued file
                    queued_file = session.query(File).filter(
                        File.status == FileStatus.QUEUED
                    ).order_by(
                        File.uploaded_at.asc()
                    ).first()
                    
                    if queued_file:
                        _process_single_file(session, queued_file, app_settings)
                    else:
                        return
                except Exception as e:
                    logger.error(f"Failed to process queued file {queued_file.path}: {str(e)}, marking as error")
                    try:
                        update_db_file_status(session, queued_file.path, FileStatus.ERROR)
                    except Exception as e:
                        logger.error(f"Failed to update file status for {queued_file.path}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        return False

def _process_single_file(session, file, app_settings: AppSettings):
    """Process a single file through the ingestion pipeline"""
    try:
        # Update status to processing
        update_db_file_status(
            session,
            file.path,
            FileStatus.PROCESSING
        )

        logger.info(f"Processing file: {file.path}")
        
        # Properly decode JSON stacks with defaults
        stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else ["default"]
        processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
        datasource_identifier = get_datasource_identifier_from_path(file.path)
        
        # Process each stack
        for stack_name in stacks_to_process:
            if not processed_stacks or stack_name not in processed_stacks:
                try:
                    process_files(
                        full_file_paths=[file.path],
                        datasource_identifier=datasource_identifier,
                        app_settings=app_settings,
                        transformations_stack_name_list=[stack_name]
                    )
                    
                    mark_db_stack_as_processed(
                        session,
                        file.path,
                        stack_name
                    )
                except Exception as e:
                    logger.error(f"Failed to process stack {stack_name}: {str(e)}")
                    continue
                    
        # Update status to completed
        update_db_file_status(
            session,
            file.path,
            FileStatus.COMPLETED
        )
        
    except Exception as e:
        logger.error(f"Failed to process file {file.path}: {str(e)}")
        update_db_file_status(
            session,
            file.path,
            FileStatus.ERROR
        )

def get_queue_status(session: Session) -> dict:
    """Get the current status of the generation queue"""
    try:
        queued_files = get_db_files_by_status(
            session, 
            FileStatus.QUEUED
        )
        processing_files = get_db_files_by_status(
            session,
            FileStatus.PROCESSING
        )
        completed_files = get_db_files_by_status(
            session,
            FileStatus.COMPLETED
        )
        
        return {
            "queued_count": len(queued_files),
            "processing_count": len(processing_files),
            "processed_files": [f.path for f in completed_files],
            "total_files": len(queued_files) + len(processing_files) + len(completed_files)
        }
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise

def should_start_processing(session: Session) -> bool:
    """Check if the processing should start"""
    
    try:
        # Try to get the oldest file that has been processing for the longest time
        oldest_processing_file = session.query(File).filter(
            File.status == FileStatus.PROCESSING
        ).order_by(
            File.processing_started_at.asc()
        ).first()

        if not oldest_processing_file:
            return True

        # If the file has been processing for more than 10 minutes, start start the processing because it is probably stuck/ the app has restarted and processing background task has not been restarted
        if oldest_processing_file.processing_started_at < datetime.now() - datetime.timedelta(seconds=600):
            return True

        # A processing is probably still running
        # TODO Make this better
        return False
    
    except Exception as e:
        logger.error(f"Failed to check if processing should start: {str(e)}")
        return False
