"""
Async batch processor for efficient evaluation processing.

Manages queues, batching, and parallel processing of evaluation requests.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """
    Async batch processor for efficient evaluation processing.
    
    Manages queues, batching, and parallel processing of evaluation requests.
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_batch_wait_ms: int = 100,
        max_concurrent_batches: int = 5,
        queue_size: int = 1000
    ):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Maximum items per batch
            max_batch_wait_ms: Maximum wait time for batch completion
            max_concurrent_batches: Maximum concurrent batches
            queue_size: Maximum queue size
        """
        self.batch_size = batch_size
        self.max_batch_wait_ms = max_batch_wait_ms
        self.max_concurrent_batches = max_concurrent_batches
        
        # Queue management
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.active_batches = 0
        self.batch_semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        # Background processing
        self.processor_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
        # Statistics
        self.processed_items = 0
        self.processed_batches = 0
        self.total_wait_time = 0.0
        self.total_process_time = 0.0
        
        logger.info(f"Batch processor initialized: batch_size={batch_size}, max_concurrent={max_concurrent_batches}")
    
    async def start(self) -> None:
        """Start batch processing."""
        if self.processor_task is None:
            self.processor_task = asyncio.create_task(self._process_loop())
            logger.info("Batch processor started")
    
    async def stop(self) -> None:
        """Stop batch processing."""
        self.shutdown_event.set()
        
        if self.processor_task:
            await self.processor_task
            self.processor_task = None
        
        logger.info("Batch processor stopped")
    
    async def submit(self, item: Any) -> Any:
        """Submit item for batch processing."""
        future = asyncio.Future()
        
        try:
            await self.queue.put((item, future))
            return await future
        except asyncio.QueueFull:
            raise Exception("Batch processor queue is full")
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while not self.shutdown_event.is_set():
            try:
                batch = await self._collect_batch()
                
                if batch:
                    await self._process_batch(batch)
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(0.1)
    
    async def _collect_batch(self) -> List[Tuple[Any, asyncio.Future]]:
        """Collect items into a batch."""
        batch = []
        deadline = asyncio.get_event_loop().time() + (self.max_batch_wait_ms / 1000.0)
        
        while len(batch) < self.batch_size and asyncio.get_event_loop().time() < deadline:
            try:
                timeout = max(0.01, deadline - asyncio.get_event_loop().time())
                item, future = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                batch.append((item, future))
            except asyncio.TimeoutError:
                break
        
        return batch
    
    async def _process_batch(self, batch: List[Tuple[Any, asyncio.Future]]) -> None:
        """Process a batch of items."""
        if not batch:
            return
        
        async with self.batch_semaphore:
            self.active_batches += 1
            start_time = time.time()
            
            try:
                # Process items in parallel within the batch
                items = [item for item, future in batch]
                results = await self._process_items(items)
                
                # Set results on futures
                for (item, future), result in zip(batch, results):
                    if not future.done():
                        future.set_result(result)
                
                # Update statistics
                self.processed_items += len(batch)
                self.processed_batches += 1
                self.total_process_time += time.time() - start_time
                
            except Exception as e:
                # Set exception on all futures
                for item, future in batch:
                    if not future.done():
                        future.set_exception(e)
                
                logger.error(f"Batch processing failed: {e}")
            
            finally:
                self.active_batches -= 1
    
    async def _process_items(self, items: List[Any]) -> List[Any]:
        """Process items in batch - to be overridden by subclasses."""
        # Default implementation - process items individually
        results = []
        for item in items:
            try:
                result = await self._process_single_item(item)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        return results
    
    async def _process_single_item(self, item: Any) -> Any:
        """Process single item - to be overridden by subclasses."""
        # Default implementation
        return item
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processor statistics."""
        return {
            "batch_size": self.batch_size,
            "queue_size": self.queue.qsize(),
            "active_batches": self.active_batches,
            "processed_items": self.processed_items,
            "processed_batches": self.processed_batches,
            "average_batch_time": (self.total_process_time / self.processed_batches) if self.processed_batches > 0 else 0,
            "items_per_second": self.processed_items / self.total_process_time if self.total_process_time > 0 else 0
        }