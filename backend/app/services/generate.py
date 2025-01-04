import threading
from threading import Lock as ThreadLock
import logging
import json
from typing import List, Set
from app.database.models import FileStatus
from app.services.database import get_session
from app.services.db_file import DBFileService
from app.services.generate_worker import GenerateServiceWorker
from requests import Session
from fastapi import WebSocket
from multiprocessing import Queue
import asyncio
from asyncio import Queue as AsyncQueue

class GenerateService:
    """Service for managing the generation queue and processing of files"""
    _instance = None
    _instance_lock = ThreadLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
            
    def __init__(self, db_file_service : DBFileService):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger(__name__)
            self.db_file_service = db_file_service
            
            # IPC Queue for worker -> service communication
            self.status_queue = Queue()
            
            # Create and start worker thread
            self._worker = GenerateServiceWorker(self.status_queue)
            self._worker_thread = threading.Thread(
                target=self._worker.run,
                daemon=True,
                name="GenerateServiceWorker"
            )
            self._worker_thread.start()
            
            # Start the status broadcast loop
            self._start_status_broadcast_loop()
            
            self.active_connections: Set[WebSocket] = set()
            
    def _start_status_broadcast_loop(self):
        """Start the background task to process status updates"""
        asyncio.create_task(self._process_status_updates())

    async def _process_status_updates(self):
        """Process status updates from the worker and broadcast to websockets"""
        while True:
            try:
                # Check for status updates without blocking
                if not self.status_queue.empty():
                    status = self.status_queue.get_nowait()
                    await self.broadcast_status(status)
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
            except Exception as e:
                self.logger.error(f"Error processing status updates: {e}")
                await asyncio.sleep(1)  # Longer delay on error

    async def add_files_to_queue(self, files: List[dict], session: Session):
        """Add multiple files to the processing queue"""
        try:
            for file in files:
                stacks_to_process : List[str] = file.get("transformations_stack_name_list", ["default"])
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
            
        await self.broadcast_status()
            
    def get_queue_status(self) -> dict:
        """Get the current status of the generation queue"""
        try:
            with get_session() as session:
                queued_files = self.db_file_service.get_files_by_status(
                    session, 
                    FileStatus.QUEUED
                )
                processing_files = self.db_file_service.get_files_by_status(
                    session,
                    FileStatus.PROCESSING
                )
                completed_files = self.db_file_service.get_files_by_status(
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
            self.logger.error(f"Failed to get queue status: {str(e)}")
            raise

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        # Send initial status
        status = self.get_queue_status()
        await self.broadcast_status(status)

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self.active_connections.remove(websocket)

    async def broadcast_status(self, status=None):
        """Broadcast status to all connected clients"""
        if not self.active_connections:
            return
            
        if status is None:
            status = self.get_queue_status()
            
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(status))
            except Exception:
                await self.disconnect(connection)

