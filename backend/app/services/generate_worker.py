import logging
import asyncio
from asyncio import new_event_loop, set_event_loop
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.db_file import get_files_by_status, update_file_status, mark_stack_as_processed
from app.services.database import get_session
from app.services.llama_index import delete_file_llama_index
from app.services.datasource import get_datasource_identifier_from_path
from app.database.models import File, FileStatus
import json
from multiprocessing import Queue
from app.services.ollama_status import OllamaStatusService
class GenerateServiceWorker:
    """Worker class that runs in a separate thread to process files"""
    
    def __init__(self, status_queue: Queue):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.status_queue = status_queue
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console_handler)

        self.logger.info("Initializing generate worker services...")

        # Ollama status service
        self.ollama_status_service = OllamaStatusService()
        self.ollama_status_service.initialize()
        
        self.ingestion_pipeline_service = IngestionPipelineService()

    def run(self):
        """Main entry point for the worker thread"""
        self.logger.info("Starting generate service worker")
        
        # Create new event loop for this thread
        loop = new_event_loop()
        set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._process_queue())
        except Exception as e:
            self.logger.error(f"Worker failed: {str(e)}")
        finally:
            loop.close()
            
    async def _process_queue(self):
        """Main processing loop"""
        while True:
            try:
                # Check if we need to wait for Ollama models
                if not self.ollama_status_service.can_process():
                    self.logger.info("Waiting for Ollama models to be ready before processing files...")
                    await asyncio.sleep(1)
                    continue
                
                with get_session() as session:
                    # Process interrupted files first
                    while True:
                        oldest_processing_file = session.query(File).filter(
                            File.status == FileStatus.PROCESSING
                        ).order_by(
                            File.uploaded_at.asc()
                        ).first()

                        # Move the processed stacks to the stacks_to_process column as we will delete all already processed stacks from llama index
                        if oldest_processing_file:
                            processed_stacks = json.loads(oldest_processing_file.processed_stacks)
                            stacks_to_process = json.loads(oldest_processing_file.stacks_to_process)
                            stacks_to_process.extend(processed_stacks)
                            oldest_processing_file.stacks_to_process = json.dumps(stacks_to_process)
                            oldest_processing_file.processed_stacks = json.dumps([])
                            session.commit()
                        
                        if not oldest_processing_file:
                            break
                            
                        self.logger.info(f"Reprocessing interrupted file: {oldest_processing_file.path}")
                        try:
                            delete_file_llama_index(oldest_processing_file.path)
                        except Exception as e:
                            self.logger.error(f"Failed to delete {oldest_processing_file.path} from stores: {str(e)}")
                            
                        await self._process_single_file(session, oldest_processing_file)
                        
                    # Get oldest queued file
                    queued_file = session.query(File).filter(
                        File.status == FileStatus.QUEUED
                    ).order_by(
                        File.uploaded_at.asc()
                    ).first()
                    
                    if queued_file:
                        await self._process_single_file(session, queued_file)
                    else:
                        await asyncio.sleep(1)
                        
            except Exception as e:
                self.logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(1)
                
    async def _notify_status_change(self, session):
        """Send status update through IPC queue"""
        try:
            status = {
                "queued_count": len(get_files_by_status(session, FileStatus.QUEUED)),
                "processing_count": len(get_files_by_status(session, FileStatus.PROCESSING)),
                "processed_files": [f.path for f in get_files_by_status(session, FileStatus.COMPLETED)]
            }
            self.status_queue.put(status)
        except Exception as e:
            self.logger.error(f"Failed to notify status change: {e}")

    async def _process_single_file(self, session, file):
        """Process a single file through the ingestion pipeline"""
        try:
            # Update status to processing
            update_file_status(
                session,
                file.path,
                FileStatus.PROCESSING
            )
            await self._notify_status_change(session)

            self.logger.info(f"Processing file: {file.path}")
            
            # Properly decode JSON stacks with defaults
            stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else ["default"]
            processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
            datasource_identifier = get_datasource_identifier_from_path(file.path)
            
            # Process each stack
            for stack_name in stacks_to_process:
                if not processed_stacks or stack_name not in processed_stacks:
                    try:
                        await self.ingestion_pipeline_service.process_files(
                            full_file_paths=[file.path],
                            datasource_identifier=datasource_identifier,
                            transformations_stack_name_list=[stack_name]
                        )
                        
                        mark_stack_as_processed(
                            session,
                            file.path,
                            stack_name
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to process stack {stack_name}: {str(e)}")
                        continue
                        
            # Update status to completed
            update_file_status(
                session,
                file.path,
                FileStatus.COMPLETED
            )
            await self._notify_status_change(session)
            
        except Exception as e:
            self.logger.error(f"Failed to process file {file.path}: {str(e)}")
            update_file_status(
                session,
                file.path,
                FileStatus.ERROR
            )
            await self._notify_status_change(session) 