from typing import List, Optional
import logging
import asyncio
from asyncio import Queue, Task, create_task, new_event_loop, set_event_loop
import threading
import json
import os
from pathlib import Path
from app.services.ingestion_pipeline import IngestionPipelineService

import logging
logger = logging.getLogger(__name__)

class GenerateService:
    # Singleton instance
    _instance = None
    _task: Optional[Task] = None
    _processing_loop = None
    _processing_thread = None
    _queue_file = Path("output/queue/generate_queue.json")

    def __init__(self):
        self.ingestion_pipeline_service = IngestionPipelineService()
        self._queue = Queue()
        self._ensure_queue_directory()
        self._load_queue_from_disk()
        # Directly start the processing task in the background
        self._start_processing_thread()

    def _ensure_queue_directory(self):
        """Ensure the queue directory exists"""
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue_from_disk(self):
        """Load the queue from disk if it exists"""
        try:
            if self._queue_file.exists():
                with open(self._queue_file, 'r') as f:
                    items = json.load(f)
                    for item in items:
                        self._queue.put_nowait(item)
                    logger.info(f"Loaded {len(items)} items from queue file")
        except Exception as e:
            logger.error(f"Error loading queue from disk: {str(e)}")

    def _save_queue_to_disk(self):
        """Save the current queue to disk"""
        try:
            # Get all items from queue without removing them
            items = list(self._queue._queue)
            with open(self._queue_file, 'w') as f:
                json.dump(items, f)
            logger.info(f"Saved {len(items)} items to queue file")
        except Exception as e:
            logger.error(f"Error saving queue to disk: {str(e)}")

    def _start_processing_thread(self):
        """Start a new thread with its own event loop for processing"""
        if self._processing_thread is None or not self._processing_thread.is_alive():
            self._processing_thread = threading.Thread(target=self._run_processing_loop, daemon=True, name="GenerateServiceWorker")
            self._processing_thread.start()
   
    def _run_processing_loop(self):
        """Run the processing loop in a separate thread"""
        # Setup the logger for this thread
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        # Create a new event loop for this thread
        loop = new_event_loop()
        set_event_loop(loop)
        self._processing_loop = loop
        
        logger.info("Started processing loop in separate thread")

        # Create and start the processing task
        try:
            loop.run_until_complete(self._process_queue())
        except Exception as e:
            logger.error(f"Error in processing loop: {str(e)}")
        finally:
            loop.close()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GenerateService()
        return cls._instance

    @classmethod
    async def add_to_queue(cls, full_file_path: str):
        """Add a single file to the generation queue"""
        try:
            instance = cls.get_instance()
            instance._queue.put_nowait(full_file_path)
            instance._save_queue_to_disk()
            logger.info(f"Added file {full_file_path} to generation queue")
            return

        except Exception as e:
            logger.error(f"Error adding file {full_file_path} to generation queue: {str(e)}")
            raise e

    @classmethod
    async def add_batch_to_queue(cls, full_file_paths: List[str]):
        """Add multiple files to the generation queue"""
        
        try:
            instance = cls.get_instance()
            for full_file_path in full_file_paths:
                instance._queue.put_nowait(full_file_path)
            instance._save_queue_to_disk()
            logger.info(f"Added batch of {len(full_file_paths)} files to generation queue")
            
            return

        except Exception as e:
            logger.error(f"Error adding batch of {len(full_file_paths)} files to generation queue: {str(e)}")
            raise e

    async def _process_queue(self):
        """Process items in the queue one at a time"""        
        # Process the queue indefinitely
        # Setup the logger for this thread
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        while True:

            try:
                
                if self._queue.empty():
                    #logger.info("Generation queue is empty, waiting for new files")
                    await asyncio.sleep(1)
                    continue

                # Get the next file from the queue
                full_file_path = await self._queue.get()
                logger.info(f"Processing file {full_file_path} from generation queue")

                # Run the ingestion pipeline on the file
                await self.ingestion_pipeline_service.ingest_file(
                    full_file_path=full_file_path,
                    logger=logger
                )

                # Mark the file as processed in the queue
                self._queue.task_done()
                # Save updated queue to disk
                self._save_queue_to_disk()
                    
                logger.info(f"Successfully processed file {full_file_path}")
            except Exception as e:
                logger.error(f"Error processing file {full_file_path}: {str(e)}")

            # Small delay to prevent resource hogging
            await asyncio.sleep(0.1)


    @classmethod
    def get_queue_status(cls) -> dict:
        """Get the current status of the generation queue"""
        return {
            #"queue_length": len(cls._queue),
            "queue_items": list(cls._queue)
        }

