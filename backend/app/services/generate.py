from typing import List, Optional, Dict
import logging
import asyncio
from asyncio import Task, new_event_loop, set_event_loop
import threading
from threading import Lock as ThreadLock
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.datasource import get_datasource_identifier_from_path
from app.database.models import File, FileStatus

logger = logging.getLogger(__name__)

class GenerateService:
    """
    Service for managing the generation queue and processing of files through the ingestion pipeline.
    Uses database status tracking and processes files one by one.
    """
    _instance = None
    _instance_lock = ThreadLock()
    _task: Optional[Task] = None
    _processing_loop = None
    _processing_thread = None
    
    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, ingestion_pipeline_service: IngestionPipelineService):
        """Initialize the service and start the processing thread"""
        if not hasattr(self, 'initialized'):
            self.ingestion_pipeline_service = ingestion_pipeline_service
            self._thread_lock = ThreadLock()
            self._start_processing_thread()
            self.initialized = True

    def _start_processing_thread(self):
        """Start a dedicated thread for queue processing"""
        with self._thread_lock:
            if self._processing_thread is None or not self._processing_thread.is_alive():
                logger.info("Starting new processing thread")
                self._processing_thread = threading.Thread(
                    target=self._run_processing_loop,
                    daemon=True,
                    name="GenerateServiceWorker"
                )
                self._processing_thread.start()
                logger.info("Processing thread started")
            else:
                logger.info("Processing thread already running")

    def _run_processing_loop(self):
        """Initialize and run the async processing loop in the dedicated thread"""
        thread_logger = logging.getLogger(__name__)
        thread_logger.setLevel(logging.INFO)
        
        loop = new_event_loop()
        set_event_loop(loop)
        self._processing_loop = loop
        
        thread_logger.info("Processing loop initialized")
        
        try:
            loop.run_until_complete(self._process_queue())
        except Exception as e:
            thread_logger.error(f"Processing loop failed: {str(e)}")
        finally:
            loop.close()

    async def _process_queue(self):
        """
        Main processing loop that handles one file at a time.
        Checks for interrupted files first, then processes the oldest queued file.
        """
        while True:
            try:
                from app.services import ServiceManager
                service_manager = ServiceManager.get_instance()
                
                with service_manager.db_service.get_session() as session:
                    # First check for any files marked as PROCESSING (interrupted)
                    processing_files = service_manager.db_file_service.get_files_by_status(
                        session,
                        FileStatus.PROCESSING
                    )
                    
                    if processing_files:
                        # Process interrupted files first
                        for file in processing_files:
                            # TODO: Delete the file from the vector store and docstore and reprocess
                            logger.info(f"Reprocessing interrupted file: {file.path}")
                            await self._process_single_file(session, file)
                            continue
                    
                    # Get the oldest queued file
                    queued_file = session.query(File).filter(
                        File.status == FileStatus.QUEUED
                    ).order_by(
                        File.uploaded_at.asc()
                    ).first()
                    
                    if not queued_file:
                        await asyncio.sleep(1)
                        continue

                    # Process the single file
                    await self._process_single_file(session, queued_file)
                    
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
            
            await asyncio.sleep(1)

    async def _process_single_file(self, session, file):
        """Process a single file through the ingestion pipeline"""
        try:
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            
            # Update status to processing
            service_manager.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.PROCESSING
            )
            
            # Get transformations stack (default if not specified)
            transformations_stack_name_list = ["default"]
            datasource_identifier = get_datasource_identifier_from_path(file.path)
            
            # Process the file
            await self.ingestion_pipeline_service.process_files(
                full_file_paths=[file.path],
                datasource_identifier=datasource_identifier,
                transformations_stack_name_list=transformations_stack_name_list
            )
            
            # Update status to completed
            service_manager.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.COMPLETED
            )
            
        except Exception as e:
            logger.error(f"Failed to process file {file.path}: {str(e)}")
            service_manager.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.ERROR,
                str(e)
            )

    async def add_to_queue(self, file_info: dict):
        """Add a single file to the processing queue"""
        try:
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            
            with service_manager.db_service.get_session() as session:
                service_manager.db_file_service.update_file_status(
                    session,
                    file_info["path"],
                    FileStatus.QUEUED
                )
                
        except Exception as e:
            logger.error(f"Failed to add file to queue: {str(e)}")
            raise

    async def add_batch_to_queue(self, files: List[dict]):
        """Add multiple files to the processing queue"""
        try:
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            
            with service_manager.db_service.get_session() as session:
                for file in files:
                    service_manager.db_file_service.update_file_status(
                        session,
                        file["path"],
                        FileStatus.QUEUED
                    )
                logger.info(f"Added batch of {len(files)} files to queue")
                
        except Exception as e:
            logger.error(f"Failed to add batch to queue: {str(e)}")
            raise

    def get_queue_status(self) -> dict:
        """Get the current status of the generation queue"""
        try:
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            
            with service_manager.db_service.get_session() as session:
                queued_files = service_manager.db_file_service.get_files_by_status(
                    session, 
                    FileStatus.QUEUED
                )
                processing_files = service_manager.db_file_service.get_files_by_status(
                    session,
                    FileStatus.PROCESSING
                )
                
                return {
                    "queued_count": len(queued_files),
                    "processing_count": len(processing_files),
                    "queued_files": [f.path for f in queued_files],
                    "processing_files": [f.path for f in processing_files]
                }
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            raise

