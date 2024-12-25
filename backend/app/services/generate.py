import threading
from threading import Lock as ThreadLock
import logging
import json
from typing import List
from app.database.models import FileStatus
from app.services.database import DatabaseService
from app.services.db_file import DBFileService
from app.services.generate_worker import GenerateServiceWorker

class GenerateService:
    """Service for managing the generation queue and processing of files"""
    _instance = None
    _instance_lock = ThreadLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
            
    def __init__(self, db_service : DatabaseService, db_file_service : DBFileService):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            self.db_service = db_service
            self.db_file_service = db_file_service
            
            # Create and start worker thread
            self._worker = GenerateServiceWorker()
            self._worker_thread = threading.Thread(
                target=self._worker.run,
                daemon=True,
                name="GenerateServiceWorker"
            )
            self._worker_thread.start()
            self.initialized = True
            
    async def add_files_to_queue(self, files: List[dict]):
        """Add multiple files to the processing queue"""
        try:
            with self.db_service.get_session() as session:
                for file in files:
                    stacks_to_process : List[str] = file.get("transformations_stack_name_list", ["default"])
                    self.logger.error(f"Stacks to process 1: {stacks_to_process}")
                    self.logger.error(f"Stacks to process type: {type(stacks_to_process)}")
                    self.db_file_service.update_file_status(
                        session,
                        file["path"],
                        FileStatus.QUEUED,
                        stacks_to_process
                    )
                self.logger.info(f"Added batch of {len(files)} files to queue")
                
        except Exception as e:
            self.logger.error(f"Failed to add batch to queue: {str(e)}")
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
            self.logger.error(f"Failed to get queue status: {str(e)}")
            raise

