from typing import List, Optional, Dict
import logging
import asyncio
from asyncio import Queue, Task, new_event_loop, set_event_loop, Lock as AsyncLock
import threading
import json
from pathlib import Path
from app.services.ingestion_pipeline import IngestionPipelineService
from app.services.datasource import get_datasource_name_from_path
from threading import Lock as ThreadLock

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 50  # Maximum files to process in a single batch

# TODO Fix the multiple ingestion threads issue
class GenerateService:
    """
    Service for managing the generation queue and processing of files through the ingestion pipeline.
    Implements a singleton pattern and handles batched processing of files with similar transformation stacks.
    """
    _instance = None
    _instance_lock = ThreadLock()
    _task: Optional[Task] = None
    _processing_loop = None
    _processing_thread = None
    _queue_file = Path("output/queue/generate_queue.json")
    
    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, ingestion_pipeline_service: IngestionPipelineService):
        """Initialize the service with a queue and start the processing thread"""
        if not hasattr(self, 'initialized'):
            self.ingestion_pipeline_service = ingestion_pipeline_service
            self._queue = Queue()
            self._queue_lock = AsyncLock()
            self._thread_lock = ThreadLock()
            self._ensure_queue_directory()
            self._load_queue_from_disk()
            self._start_processing_thread()
            self.initialized = True

    def _ensure_queue_directory(self):
        """Ensure the queue directory exists"""
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _persist_queue(self):
        """Save the current queue state to disk"""
        try:
            items = list(self._queue._queue)
            with open(self._queue_file, 'w') as f:
                json.dump(items, f)
            logger.info(f"Queue persisted: {len(items)} items saved to disk")
        except Exception as e:
            logger.error(f"Failed to persist queue to disk: {str(e)}")

    def _load_queue_from_disk(self):
        """Load the previously saved queue state from disk"""
        try:
            if self._queue_file.exists():
                with open(self._queue_file, 'r') as f:
                    items = json.load(f)
                    for item in items:
                        self._queue.put_nowait(item)
                    logger.info(f"Queue loaded: {len(items)} items restored from disk")
        except Exception as e:
            logger.error(f"Failed to load queue from disk: {str(e)}")

    def _start_processing_thread(self):
        """Start a dedicated thread for queue processing"""
        with self._thread_lock:
            # Only start a new thread if there isn't one running
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
        # Setup thread-local logging
        thread_logger = logging.getLogger(__name__)
        thread_logger.setLevel(logging.INFO)
        
        # Create and set event loop for this thread
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

    async def _process_queue(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Main queue processing loop that handles batching and processing of files.
        Groups files by datasource and transformation stack for efficient processing.
        """        
        while True:
            try:
                if self._queue.empty():
                    await asyncio.sleep(1)
                    continue

                # Process all current items in queue
                current_size = self._queue.qsize()
                logger.info(f"Starting processing of {current_size} items from queue")
                
                # Group items by datasource and transformation stack
                batches: Dict[tuple, List[dict]] = {}
                items_to_process = []
                
                # Get all items while preserving their original data
                for _ in range(current_size):
                    item = await self._queue.get()
                    items_to_process.append(item)
                    # Create composite key from datasource and transformation stack
                    datasource_name = get_datasource_name_from_path(item["path"])
                    stack_key = tuple(sorted(item["transformations_stack_name_list"]))
                    batch_key = (datasource_name, stack_key)
                    if batch_key not in batches:
                        batches[batch_key] = []
                    batches[batch_key].append(item)
                    self._queue.task_done()

                total_processed = 0
                total_items = len(items_to_process)
                problematic_files = []

                # Process each datasource and transformation stack group
                for (datasource_name, stack_list), items in batches.items():
                    logger.info(f"Processing {len(items)} files for datasource '{datasource_name}' with transformation stack: {list(stack_list)}")
                    file_paths = [item["path"] for item in items]
                    stack_processed = 0
                    current_batch_size = batch_size
                    
                    # Process files in smaller sub-batches
                    i = 0
                    while i < len(file_paths):
                        sub_batch = file_paths[i:i + current_batch_size]
                        sub_batch_items = items[i:i + current_batch_size]
                        
                        try:
                            await self.ingestion_pipeline_service.process_files(
                                full_file_paths=sub_batch,
                                datasource_name=datasource_name,
                                transformations_stack_name_list=list(stack_list)
                            )
                            
                            # Update progress counters
                            stack_processed += len(sub_batch)
                            total_processed += len(sub_batch)
                            
                            # Remove successfully processed items from the queue
                            for item in sub_batch_items:
                                if item in items_to_process:
                                    items_to_process.remove(item)
                            
                            # Log progress
                            logger.info(
                                f"Progress - Datasource '{datasource_name}' Stack {list(stack_list)}: "
                                f"{stack_processed}/{len(items)} files | "
                                f"Total: {total_processed}/{total_items} files ({(total_processed/total_items)*100:.1f}%)"
                            )
                            
                            # Update persisted queue with remaining items
                            await self._persist_remaining_items(items_to_process)
                            
                            # Reset batch size to default after successful processing
                            current_batch_size = batch_size
                            i += len(sub_batch)

                        except Exception as e:
                            logger.error(f"Failed to process sub-batch: {str(e)}")
                            
                            if current_batch_size == 1:
                                # If we're already processing one by one, this file is problematic
                                problematic_file = sub_batch[0]
                                logger.error(f"Identified problematic file: {problematic_file}")
                                problematic_files.append(problematic_file)
                                
                                # Skip this file and continue with the next one
                                i += 1
                                current_batch_size = batch_size  # Reset batch size
                                
                                # Remove the problematic file from items_to_process
                                for item in sub_batch_items:
                                    if item in items_to_process:
                                        items_to_process.remove(item)
                            else:
                                # Reduce batch size to 1 to identify problematic file
                                logger.info("Reducing batch size to 1 to identify problematic file")
                                current_batch_size = 1
                                # Don't increment i, retry with smaller batch size
                            
                            # Persist the updated queue state
                            await self._persist_remaining_items(items_to_process)
                            continue

                if problematic_files:
                    logger.warning(f"Completed processing with {len(problematic_files)} problematic files: {problematic_files}")
                
                logger.info(f"Completed processing batch - {total_processed}/{total_items} files processed successfully")
                
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
            
            await asyncio.sleep(1)

    async def _persist_remaining_items(self, items: List[dict]):
        """Persist the remaining items to disk"""
        try:
            with open(self._queue_file, 'w') as f:
                json.dump(items, f)
            logger.info(f"Queue persisted: {len(items)} items remaining")
        except Exception as e:
            logger.error(f"Failed to persist queue to disk: {str(e)}")

    async def add_to_queue(self, full_file_path: str, transformations_stack_name_list: List[str] = ["default"]):
        """Add a single file to the generation queue"""
        try:
            async with self._queue_lock:
                await self._queue.put({
                    "path": full_file_path,
                    "transformations_stack_name_list": transformations_stack_name_list
                })
                self._persist_queue()
        except Exception as e:
            logger.error(f"Failed to add file to queue: {str(e)}")
            raise

    async def add_batch_to_queue(self, files: List[dict]):
        """Add multiple files to the generation queue"""
        try:
            async with self._queue_lock:
                for file in files:
                    await self._queue.put({
                        "path": file["path"],
                        "transformations_stack_name_list": file.get("transformations_stack_name_list", ["default"])
                    })
                self._persist_queue()
                logger.info(f"Added batch of {len(files)} files to queue")
        except Exception as e:
            logger.error(f"Failed to add batch to queue: {str(e)}")
            raise

    def get_queue_status(self) -> dict:
        """Get the current status of the generation queue"""
        return {
            "queue_length": self._queue.qsize(),
            "queue_items": list(self._queue._queue)
        }

