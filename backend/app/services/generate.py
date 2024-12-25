import json
from typing import List, Optional, Dict
import logging
import asyncio
from asyncio import Task, new_event_loop, set_event_loop
import threading
from threading import Lock as ThreadLock
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.db_file import DBFileService
from app.services.database import DatabaseService
from app.services.llama_index import LlamaIndexService
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
    
    def __init__(self, ingestion_pipeline_service: IngestionPipelineService, db_service: DatabaseService, db_file_service: DBFileService, llama_index_service: LlamaIndexService):
        """Initialize the service and start the processing thread"""
        if not hasattr(self, 'initialized'):
            self.ingestion_pipeline_service = ingestion_pipeline_service
            self.db_service = db_service
            self.db_file_service = db_file_service
            self.llama_index_service = llama_index_service
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
                with self.db_service.get_session() as session:
                    
                    # While there is files with status PROCESSING, process them
                    while True:
                        oldest_processing_file = session.query(File).filter(
                            File.status == FileStatus.PROCESSING
                        ).order_by(
                            File.uploaded_at.asc()
                        ).first()
                        if not oldest_processing_file:
                            break
                        else:
                            logger.info(f"Reprocessing interrupted file: {oldest_processing_file.path}")

                            # Try to delete the file from the vector store and docstore
                            try:
                                self.llama_index_service.delete_file(oldest_processing_file.path)
                            except Exception as e:
                                logger.error(f"Failed to delete {oldest_processing_file.path} from vector store and docstore for reprocessing, proceeding with reprocessing : {str(e)}")

                            # Process the file
                            await self._process_single_file(session, oldest_processing_file)
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
            # Update status to processing
            self.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.PROCESSING
            )
            
            # Get stacks to process from the file
            stacks_to_process = file.stacks_to_process
            datasource_identifier = get_datasource_identifier_from_path(file.path)
            
            # Process each stack that hasn't been processed yet
            for stack_name in stacks_to_process:
                if stack_name not in file.processed_stacks:
                    try:
                        # Process the file with this stack
                        await self.ingestion_pipeline_service.process_files(
                            full_file_paths=[file.path],
                            datasource_identifier=datasource_identifier,
                            transformations_stack_name_list=[stack_name]
                        )
                        
                        # Add stack to processed stacks
                        self.db_file_service.mark_stack_as_processed(
                            session,
                            file.path,
                            stack_name
                        )
                    except Exception as e:
                        logger.error(f"Failed to process stack {stack_name} for file {file.path}: {str(e)}")
                        # Continue with next stack instead of failing completely
                        continue
            
            # Update status to completed
            self.db_file_service.update_file_status(
                session,
                file.path,
                FileStatus.COMPLETED
            )
            
        except Exception as e:
            logger.error(f"Failed to process file {file.path}: {str(e)}")
            try:
                self.db_file_service.update_file_status(
                    session,
                    file.path,
                    FileStatus.ERROR
                )
            except Exception as e:
                logger.error(f"Failed to update file status for {file.path}: {str(e)}")

    async def add_files_to_queue(self, files: List[dict]):
        """Add multiple files to the processing queue"""
        try:
            with self.db_service.get_session() as session:
                for file in files:
                    # Get the stacks to process from the file and parse it into a json object dict
                    stacks_to_process = json.loads(file.get("transformations_stack_name_list", ["default"]))
                    self.db_file_service.update_file_status(
                        session,
                        file["path"],
                        FileStatus.QUEUED,
                        stacks_to_process
                    )
                logger.info(f"Added batch of {len(files)} files to queue")
                
        except Exception as e:
            logger.error(f"Failed to add batch to queue: {str(e)}")
            raise

    def get_queue_status(self) -> dict:
        """Get the current status of the generation queue"""
        try:
            with self.db_service.get_session() as session:
                queued_files = self.db_file_service.get_files_by_status(
                    session, 
                    FileStatus.QUEUED
                )
                processing_files = self.db_file_service.get_files_by_status(
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

