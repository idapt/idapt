import threading
from threading import Lock as ThreadLock
import logging
import json
from typing import List, Set
from app.database.models import FileStatus
from app.services.db_file import get_db_files_by_status, update_db_file_status
from app.services.generate_worker import GenerateServiceWorker
from sqlalchemy.orm import Session
from fastapi import WebSocket
from multiprocessing import Queue
import asyncio

logger = logging.getLogger(__name__)

class GenerateService:
    """Service for managing the generation queue and processing of files"""
    _instance = None
    _instance_lock = ThreadLock()
    _is_processing = False
    _active_connections: Set[WebSocket] = set()
    _status_queue = Queue()
    
    @classmethod
    def get_instance(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self._worker = None
        self._worker_thread = None
        
    async def start_processing(self):
        """Start the worker if not already running"""
        with self._instance_lock:
            if not self._is_processing:
                self._is_processing = True
                self._worker = GenerateServiceWorker(self._status_queue)
                self._worker_thread = threading.Thread(
                    target=self._worker.run,
                    daemon=True,
                    name="GenerateServiceWorker"
                )
                self._worker_thread.start()
                asyncio.create_task(self._process_status_updates())

    async def _process_status_updates(self):
        """Process status updates from worker and broadcast to websockets"""
        while self._is_processing:
            try:
                if not self._status_queue.empty():
                    status = self._status_queue.get_nowait()
                    if status.get("processing_complete", False):
                        self._is_processing = False
                    await self.broadcast_status(status)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing status updates: {e}")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self._active_connections.add(websocket)
        # Send initial status
        status = self.get_queue_status()
        await self.broadcast_status(status)

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self._active_connections.remove(websocket)

    async def broadcast_status(self, status=None):
        """Broadcast status to all connected clients"""
        if not self._active_connections:
            return
            
        if status is None:
            status = self.get_queue_status()
            
        for connection in self._active_connections.copy():
            try:
                await connection.send_text(json.dumps(status))
            except Exception:
                await self.disconnect(connection)

#def add_files_to_queue(self, files: List[dict]):
#    """Add files to the generation queue"""
#    try:
#        with get_session() as session:
#            for file in files:
#                update_file_status(
#                    session,
#                    file["path"],
#                    FileStatus.QUEUED,
#                    file.get("transformations_stack_name_list", ["default"])
#                )
#            session.commit()
#
#        return {
#            "status": "queued",
#            "message": f"Added {len(files)} files to generation queue",
#            "queue_status": self.get_queue_status()
#        }
#    except Exception as e:
#        logger.error(f"Failed to add files to generation queue: {str(e)}")
#        raise
    
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