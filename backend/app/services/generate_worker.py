import logging
import asyncio
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.db_file import update_db_file_status, mark_db_stack_as_processed
from app.services.database import get_session
from app.services.datasource import get_datasource_identifier_from_path
from app.services.llama_index import delete_file_llama_index
from app.database.models import File, FileStatus
from sqlalchemy.orm import Session
import json
import time
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

class GenerateServiceWorker:
    """Worker class that runs in a separate thread to process files"""
    
    def initialize(self):       
        logger.info("Initializing generate worker services...")

        # Init ollama status service for this thread
        from app.services.ollama_status import OllamaStatusService
        self.ollama_status_service = OllamaStatusService()
        self.ollama_status_service.initialize()

        # Init ingestion pipeline service for this thread
        self.ingestion_pipeline_service = IngestionPipelineService()

    def run(self):
        """Main entry point for the worker thread"""
        logger.info("Starting generate service worker")
        
        # Start processing loop
        #self.processing_loop_task = asyncio.create_task(self._processing_loop())
        self._processing_loop()
        
    def _processing_loop(self):
        """Processing loop"""
        try:
            # Wait for Ollama models to be ready
            self._wait_for_ollama_models()
            
            # Run forever
            while True:
                try:
                    # Process all files marked as processing that have been interrupted with unfinished processing
                    self._process_files_marked_as_processing()

                    # Process all queued files
                    self._process_all_queued_files()
                except Exception as e:
                    logger.error(f"Processing loop error, retrying: {str(e)}")
                    time.sleep(2)
                
                # Wait
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Processing loop error: {str(e)}")

    def _process_files_marked_as_processing(self, session):
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
                            
                        self._process_single_file(session, oldest_processing_file)
                    except Exception as e:
                        logger.error(f"Failed to process interrupted file {oldest_processing_file.path}: {str(e)}, marking as error")
                        try:
                            update_db_file_status(session, oldest_processing_file.path, FileStatus.ERROR)
                        except Exception as e:
                            logger.error(f"Failed to update file status for {oldest_processing_file.path}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process all queued files: {str(e)}")
            return False
            
    def _process_all_queued_files(self, session) -> bool:
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
                            self._process_single_file(session, queued_file)
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
                        
    
    def _wait_for_ollama_models(self):
        """Wait for Ollama models to be ready"""
        while True:
            # Check if we need to wait for Ollama models
            if self.ollama_status_service.can_process():
                return
            
            logger.info("Waiting for Ollama models to be ready before processing files...")
            time.sleep(1)
            continue

    def _notify_status_change(self):
        """Send status update"""
        pass

    def _process_single_file(self, session, file):
        """Process a single file through the ingestion pipeline"""
        try:
            # Update status to processing
            update_db_file_status(
                session,
                file.path,
                FileStatus.PROCESSING
            )
            self._notify_status_change(session)

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
            self._notify_status_change(session)
            
        except Exception as e:
            logger.error(f"Failed to process file {file.path}: {str(e)}")
            update_db_file_status(
                session,
                file.path,
                FileStatus.ERROR
            )
            self._notify_status_change(session) 

def start_generate_worker():
    """Start the generate worker"""
    generate_service = GenerateServiceWorker()
    generate_service.initialize()
    # Start the processing loop in this thread
    generate_service.run()
