import logging
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.db_file import update_db_file_status, mark_db_stack_as_processed, get_db_files_by_status
from app.services.database import get_session
from app.services.datasource import get_datasource_identifier_from_path
from app.services.llama_index import delete_file_llama_index
from app.services.ollama_status import wait_for_ollama_models
from app.database.models import File, FileStatus
from sqlalchemy.orm import Session
import json
import time

logger = logging.getLogger(__name__)
    
def process_queued_files(session: Session):
    """Processing loop"""
    try:
        # Wait for Ollama models to be ready
        wait_for_ollama_models()
        
        # Run forever
        while True:
            try:
                # Process all files marked as processing that have been interrupted with unfinished processing
                _process_files_marked_as_processing(session)

                # Process all queued files
                _process_all_queued_files(session)
            except Exception as e:
                logger.error(f"Processing loop error, retrying: {str(e)}")
                time.sleep(2)
            
            # Wait
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"Processing loop error: {str(e)}")

def _process_files_marked_as_processing(session):
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
                        
                    _process_single_file(session, oldest_processing_file)
                except Exception as e:
                    logger.error(f"Failed to process interrupted file {oldest_processing_file.path}: {str(e)}, marking as error")
                    try:
                        update_db_file_status(session, oldest_processing_file.path, FileStatus.ERROR)
                    except Exception as e:
                        logger.error(f"Failed to update file status for {oldest_processing_file.path}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        return False
        
def _process_all_queued_files(session) -> bool:
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
                        _process_single_file(session, queued_file)
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

def _process_single_file(self, session, file):
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
                    self.ingestion_pipeline_service.process_files(
                        full_file_paths=[file.path],
                        datasource_identifier=datasource_identifier,
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