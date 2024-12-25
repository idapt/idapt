import logging
import asyncio
from asyncio import new_event_loop, set_event_loop
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.db_file import DBFileService
from app.services.database import DatabaseService
from app.services.llama_index import LlamaIndexService
from app.services.datasource import DatasourceService, get_datasource_identifier_from_path
from app.services.file_manager import FileManagerService
from app.services.file_system import FileSystemService
from app.database.models import File, FileStatus
import json

class GenerateServiceWorker:
    """Worker class that runs in a separate thread to process files"""
    
    def __init__(
        self
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console_handler)

        self.logger.info("Initializing generate worker services...")
        
        # Core services with their own thread safety
        self.db_service = DatabaseService()
        self.db_file_service = DBFileService()
  
        self.llama_index_service = LlamaIndexService()

        self.file_system_service = FileSystemService()

        self.file_manager_service = FileManagerService(
            self.db_service, 
            self.db_file_service,
            self.file_system_service,
            self.llama_index_service
        )
        
        self.datasource_service = DatasourceService(
            self.db_service,
            self.db_file_service,
            self.file_manager_service
        )

        self.ingestion_pipeline_service = IngestionPipelineService(
            self.db_file_service,
            self.db_service,
            self.datasource_service
        )

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
                with self.db_service.get_session() as session:
                    # Process interrupted files first
                    while True:
                        oldest_processing_file = session.query(File).filter(
                            File.status == FileStatus.PROCESSING
                        ).order_by(
                            File.uploaded_at.asc()
                        ).first()
                        
                        if not oldest_processing_file:
                            break
                            
                        self.logger.info(f"Reprocessing interrupted file: {oldest_processing_file.path}")
                        try:
                            self.llama_index_service.delete_file(oldest_processing_file.path)
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
                
    async def _process_single_file(self, session, file):
        """Process a single file through the ingestion pipeline"""
        try:
            self.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.PROCESSING
            )
            
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
                        
                        self.db_file_service.mark_stack_as_processed(
                            session,
                            file.path,
                            stack_name
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to process stack {stack_name}: {str(e)}")
                        continue
                        
            self.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.COMPLETED
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process file {file.path}: {str(e)}")
            self.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.ERROR
            ) 