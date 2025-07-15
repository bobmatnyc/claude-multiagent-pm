"""
Asynchronous Memory Collection Service for Claude PM Framework.

Implements fire-and-forget memory collection with background processing,
queue management, and performance optimization features.

This service provides:
- Fire-and-forget async collection API
- Background queue processing 
- Priority handling for critical operations
- Retry logic and error handling
- Performance monitoring integration
- Service lifecycle management

Performance targets:
- Collection operations: <100ms
- Agent workflow latency: <0.5s
- Queue processing: <5s
- Memory usage: <50MB overhead
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from weakref import WeakValueDictionary
import os

from ..core.base_service import BaseService
from ..core.config import Config


class MemoryPriority(Enum):
    """Priority levels for memory operations."""
    CRITICAL = "critical"    # Errors, bugs, system failures
    HIGH = "high"           # User feedback, important events
    MEDIUM = "medium"       # Standard operations
    LOW = "low"             # Background activities


class MemoryCategory(Enum):
    """Memory operation categories."""
    BUG = "bug"
    FEEDBACK = "feedback"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    QA = "qa"
    ERROR = "error"
    OPERATION = "operation"


@dataclass
class MemoryOperation:
    """Represents a queued memory operation."""
    
    id: str
    category: MemoryCategory
    content: str
    metadata: Dict[str, Any]
    priority: MemoryPriority
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    next_retry: Optional[datetime] = None
    
    def __post_init__(self):
        if self.next_retry is None:
            self.next_retry = self.created_at


@dataclass
class CollectionStats:
    """Collection performance statistics."""
    
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    retried_operations: int = 0
    average_latency: float = 0.0
    queue_size: int = 0
    batch_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100.0


class AsyncMemoryCollector(BaseService):
    """
    Fire-and-forget memory collection service.
    
    Provides asynchronous memory collection with background processing,
    queue management, retry logic, and performance optimization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the async memory collector."""
        super().__init__("async_memory_collector", config)
        
        # Configuration with defaults
        self.batch_size = self.get_config("batch_size", 10)
        self.batch_timeout = self.get_config("batch_timeout", 30.0)
        self.max_queue_size = self.get_config("max_queue_size", 1000)
        self.max_retries = self.get_config("max_retries", 3)
        self.retry_delay = self.get_config("retry_delay", 1.0)
        self.operation_timeout = self.get_config("operation_timeout", 15.0)
        self.max_concurrent_ops = self.get_config("max_concurrent_ops", 20)
        self.health_check_interval = self.get_config("health_check_interval", 60)
        
        # Internal state
        self.operation_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        self.stats = CollectionStats()
        self.operation_counter = 0
        self.active_operations: Dict[str, MemoryOperation] = {}
        self.semaphore = asyncio.Semaphore(self.max_concurrent_ops)
        
        # Memory cache for frequently accessed items
        self.cache_enabled = self.get_config("cache.enabled", True)
        self.cache_max_size = self.get_config("cache.max_size", 1000)
        self.cache_ttl = self.get_config("cache.ttl_seconds", 300)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_access_times: Dict[str, datetime] = {}
        
        # Performance monitoring
        self.performance_callbacks: List[Callable] = []
        self.start_time = time.time()
        
        self.logger.info(f"Initialized AsyncMemoryCollector with batch_size={self.batch_size}, "
                        f"max_queue_size={self.max_queue_size}, cache_enabled={self.cache_enabled}")
    
    async def _initialize(self) -> None:
        """Initialize the service."""
        self.logger.info("Initializing AsyncMemoryCollector...")
        
        # Validate configuration
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        # Initialize cache if enabled
        if self.cache_enabled:
            await self._initialize_cache()
        
        self.logger.info("AsyncMemoryCollector initialized successfully")
    
    async def _cleanup(self) -> None:
        """Cleanup service resources."""
        self.logger.info("Cleaning up AsyncMemoryCollector...")
        
        # Process remaining operations
        await self._flush_queue()
        
        # Clear cache
        if self.cache_enabled:
            self.cache.clear()
            self.cache_access_times.clear()
        
        # Clear active operations
        self.active_operations.clear()
        
        self.logger.info("AsyncMemoryCollector cleanup completed")
    
    async def _start_custom_tasks(self) -> Optional[List[asyncio.Task]]:
        """Start custom background tasks."""
        tasks = []
        
        # Queue processor task
        processor_task = asyncio.create_task(self._queue_processor())
        tasks.append(processor_task)
        
        # Retry handler task
        retry_task = asyncio.create_task(self._retry_handler())
        tasks.append(retry_task)
        
        # Cache cleanup task
        if self.cache_enabled:
            cache_task = asyncio.create_task(self._cache_cleanup())
            tasks.append(cache_task)
        
        # Performance monitor task
        monitor_task = asyncio.create_task(self._performance_monitor())
        tasks.append(monitor_task)
        
        return tasks
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform service health checks."""
        checks = {}
        
        # Queue health
        checks["queue_operational"] = not self.operation_queue.full()
        checks["queue_size_ok"] = self.operation_queue.qsize() < (self.max_queue_size * 0.9)
        
        # Performance health
        checks["success_rate_ok"] = self.stats.success_rate() >= 95.0
        checks["average_latency_ok"] = self.stats.average_latency < 5.0
        
        # Cache health (if enabled)
        if self.cache_enabled:
            checks["cache_operational"] = len(self.cache) < self.cache_max_size
        
        return checks
    
    async def collect_async(
        self,
        category: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> str:
        """
        Fire-and-forget memory collection.
        
        Args:
            category: Memory category (bug, feedback, architecture, etc.)
            content: Memory content to store
            metadata: Additional metadata
            priority: Operation priority (critical, high, medium, low)
            
        Returns:
            Operation ID for tracking
            
        Raises:
            ValueError: If invalid category or priority
            asyncio.QueueFull: If queue is full
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            try:
                mem_category = MemoryCategory(category.lower())
            except ValueError:
                raise ValueError(f"Invalid category: {category}")
            
            try:
                mem_priority = MemoryPriority(priority.lower())
            except ValueError:
                raise ValueError(f"Invalid priority: {priority}")
            
            # Create operation
            operation_id = f"op_{self.operation_counter}_{int(time.time() * 1000)}"
            self.operation_counter += 1
            
            operation = MemoryOperation(
                id=operation_id,
                category=mem_category,
                content=content,
                metadata=metadata or {},
                priority=mem_priority,
                created_at=datetime.now(),
                max_retries=self.max_retries
            )
            
            # Add to queue (non-blocking)
            try:
                self.operation_queue.put_nowait(operation)
                self.stats.total_operations += 1
                self.stats.queue_size = self.operation_queue.qsize()
                
                # Log performance-sensitive operations
                if mem_priority in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]:
                    self.logger.info(f"Queued {priority} memory operation: {operation_id}")
                
            except asyncio.QueueFull:
                self.logger.error(f"Memory collection queue full, dropping operation: {operation_id}")
                self.stats.failed_operations += 1
                raise
            
            # Update performance metrics
            operation_latency = time.time() - start_time
            self._update_average_latency(operation_latency)
            
            # Check cache for similar operations
            if self.cache_enabled:
                cache_key = f"{category}_{hash(content)}"
                if cache_key in self.cache:
                    self.stats.cache_hits += 1
                    self.cache_access_times[cache_key] = datetime.now()
                else:
                    self.stats.cache_misses += 1
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"Error in collect_async: {e}")
            self.stats.failed_operations += 1
            raise
    
    async def flush_queue(self, timeout: float = 30.0) -> int:
        """
        Force process all queued operations.
        
        Args:
            timeout: Maximum time to wait for queue processing
            
        Returns:
            Number of operations processed
        """
        self.logger.info("Flushing memory collection queue...")
        
        start_time = time.time()
        initial_size = self.operation_queue.qsize()
        
        # Wait for queue to empty or timeout
        while not self.operation_queue.empty() and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        
        processed = initial_size - self.operation_queue.qsize()
        self.logger.info(f"Flushed {processed} operations from queue")
        
        return processed
    
    async def get_stats(self) -> CollectionStats:
        """Get current collection statistics."""
        # Update queue size
        self.stats.queue_size = self.operation_queue.qsize()
        return self.stats
    
    async def add_performance_callback(self, callback: Callable) -> None:
        """Add performance monitoring callback."""
        self.performance_callbacks.append(callback)
    
    async def _queue_processor(self) -> None:
        """Background task for processing queued operations."""
        batch = []
        last_batch_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Get operation from queue with timeout
                try:
                    operation = await asyncio.wait_for(
                        self.operation_queue.get(), 
                        timeout=1.0
                    )
                    batch.append(operation)
                    
                except asyncio.TimeoutError:
                    # Check if we should process partial batch
                    if batch and (time.time() - last_batch_time) > self.batch_timeout:
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.time()
                    continue
                
                # Process batch when full or timeout reached
                should_process = (
                    len(batch) >= self.batch_size or
                    (time.time() - last_batch_time) > self.batch_timeout
                )
                
                if should_process:
                    await self._process_batch(batch)
                    batch = []
                    last_batch_time = time.time()
                
            except Exception as e:
                self.logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(1.0)
        
        # Process remaining batch on shutdown
        if batch:
            await self._process_batch(batch)
    
    async def _process_batch(self, batch: List[MemoryOperation]) -> None:
        """Process a batch of memory operations."""
        if not batch:
            return
        
        self.logger.debug(f"Processing batch of {len(batch)} operations")
        
        # Sort by priority (critical first)
        priority_order = {
            MemoryPriority.CRITICAL: 0,
            MemoryPriority.HIGH: 1,
            MemoryPriority.MEDIUM: 2,
            MemoryPriority.LOW: 3
        }
        batch.sort(key=lambda op: priority_order[op.priority])
        
        # Process operations concurrently with semaphore
        tasks = []
        for operation in batch:
            task = asyncio.create_task(self._process_operation(operation))
            tasks.append(task)
        
        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update batch stats
        self.stats.batch_operations += len(batch)
        
        # Handle failed operations
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                operation = batch[i]
                await self._handle_operation_failure(operation, result)
    
    async def _process_operation(self, operation: MemoryOperation) -> None:
        """Process a single memory operation."""
        async with self.semaphore:
            operation_start = time.time()
            
            try:
                # Add to active operations
                self.active_operations[operation.id] = operation
                
                # Simulate memory storage (replace with actual implementation)
                await self._store_memory(operation)
                
                # Update cache
                if self.cache_enabled:
                    await self._update_cache(operation)
                
                # Success
                self.stats.successful_operations += 1
                
                # Log critical operations
                if operation.priority == MemoryPriority.CRITICAL:
                    self.logger.info(f"Processed critical operation: {operation.id}")
                
            except Exception as e:
                self.logger.error(f"Failed to process operation {operation.id}: {e}")
                self.stats.failed_operations += 1
                raise
            
            finally:
                # Remove from active operations
                self.active_operations.pop(operation.id, None)
                
                # Update latency
                operation_latency = time.time() - operation_start
                self._update_average_latency(operation_latency)
    
    async def _store_memory(self, operation: MemoryOperation) -> None:
        """Store memory operation (placeholder for actual implementation)."""
        # This would integrate with the actual memory backend
        # For now, simulate storage with delay
        await asyncio.sleep(0.01)  # Simulate storage latency
        
        # In actual implementation, this would:
        # 1. Choose appropriate backend (SQLite, mem0AI)
        # 2. Format data according to backend schema
        # 3. Store with appropriate metadata
        # 4. Handle backend-specific errors
        
        self.logger.debug(f"Stored memory operation: {operation.id} "
                         f"(category: {operation.category.value}, "
                         f"priority: {operation.priority.value})")
    
    async def _handle_operation_failure(self, operation: MemoryOperation, error: Exception) -> None:
        """Handle failed memory operation."""
        operation.retry_count += 1
        
        if operation.retry_count <= operation.max_retries:
            # Calculate exponential backoff
            delay = self.retry_delay * (2 ** (operation.retry_count - 1))
            operation.next_retry = datetime.now() + timedelta(seconds=delay)
            
            # Add to retry queue
            try:
                self.retry_queue.put_nowait(operation)
                self.stats.retried_operations += 1
                
                self.logger.warning(f"Retrying operation {operation.id} "
                                   f"(attempt {operation.retry_count}/{operation.max_retries})")
                
            except asyncio.QueueFull:
                self.logger.error(f"Retry queue full, dropping operation: {operation.id}")
                self.stats.failed_operations += 1
        else:
            self.logger.error(f"Operation {operation.id} failed after {operation.max_retries} retries")
            self.stats.failed_operations += 1
    
    async def _retry_handler(self) -> None:
        """Background task for handling retries."""
        while not self._stop_event.is_set():
            try:
                # Get operation from retry queue
                try:
                    operation = await asyncio.wait_for(
                        self.retry_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if it's time to retry
                if datetime.now() >= operation.next_retry:
                    # Add back to main queue
                    try:
                        self.operation_queue.put_nowait(operation)
                    except asyncio.QueueFull:
                        self.logger.error(f"Queue full, dropping retry operation: {operation.id}")
                else:
                    # Put back in retry queue
                    try:
                        self.retry_queue.put_nowait(operation)
                    except asyncio.QueueFull:
                        self.logger.error(f"Retry queue full, dropping operation: {operation.id}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in retry handler: {e}")
                await asyncio.sleep(1.0)
    
    async def _initialize_cache(self) -> None:
        """Initialize memory cache."""
        self.logger.info(f"Initializing cache with max_size={self.cache_max_size}, "
                        f"ttl={self.cache_ttl}s")
        self.cache = {}
        self.cache_access_times = {}
    
    async def _update_cache(self, operation: MemoryOperation) -> None:
        """Update cache with operation data."""
        if not self.cache_enabled:
            return
        
        cache_key = f"{operation.category.value}_{hash(operation.content)}"
        
        # Check cache size limit
        if len(self.cache) >= self.cache_max_size:
            await self._evict_cache_entries()
        
        # Add to cache
        self.cache[cache_key] = {
            "operation_id": operation.id,
            "category": operation.category.value,
            "content": operation.content,
            "metadata": operation.metadata,
            "cached_at": datetime.now().isoformat()
        }
        
        self.cache_access_times[cache_key] = datetime.now()
    
    async def _cache_cleanup(self) -> None:
        """Background task for cache cleanup."""
        while not self._stop_event.is_set():
            try:
                if self.cache_enabled:
                    await self._evict_expired_entries()
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _evict_cache_entries(self) -> None:
        """Evict cache entries using LRU strategy."""
        if not self.cache:
            return
        
        # Sort by access time (oldest first)
        sorted_keys = sorted(
            self.cache_access_times.keys(),
            key=lambda k: self.cache_access_times[k]
        )
        
        # Remove oldest 10% of entries
        evict_count = max(1, len(sorted_keys) // 10)
        
        for key in sorted_keys[:evict_count]:
            self.cache.pop(key, None)
            self.cache_access_times.pop(key, None)
        
        self.logger.debug(f"Evicted {evict_count} cache entries")
    
    async def _evict_expired_entries(self) -> None:
        """Evict expired cache entries."""
        now = datetime.now()
        ttl_delta = timedelta(seconds=self.cache_ttl)
        
        expired_keys = []
        for key, access_time in self.cache_access_times.items():
            if now - access_time > ttl_delta:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_access_times.pop(key, None)
        
        if expired_keys:
            self.logger.debug(f"Evicted {len(expired_keys)} expired cache entries")
    
    async def _performance_monitor(self) -> None:
        """Background task for performance monitoring."""
        while not self._stop_event.is_set():
            try:
                # Collect performance metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "queue_size": self.operation_queue.qsize(),
                    "retry_queue_size": self.retry_queue.qsize(),
                    "active_operations": len(self.active_operations),
                    "cache_size": len(self.cache) if self.cache_enabled else 0,
                    "stats": self.stats
                }
                
                # Call performance callbacks
                for callback in self.performance_callbacks:
                    try:
                        await callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Performance callback error: {e}")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(60)
    
    def _update_average_latency(self, latency: float) -> None:
        """Update average latency using exponential moving average."""
        alpha = 0.1  # Smoothing factor
        if self.stats.average_latency == 0:
            self.stats.average_latency = latency
        else:
            self.stats.average_latency = alpha * latency + (1 - alpha) * self.stats.average_latency
    
    async def _collect_custom_metrics(self) -> None:
        """Collect custom service metrics."""
        # Update custom metrics
        uptime = time.time() - self.start_time
        
        self.update_metrics(
            queue_size=self.operation_queue.qsize(),
            retry_queue_size=self.retry_queue.qsize(),
            active_operations=len(self.active_operations),
            cache_size=len(self.cache) if self.cache_enabled else 0,
            success_rate=self.stats.success_rate(),
            average_latency=self.stats.average_latency,
            uptime_seconds=uptime
        )
    
    async def _flush_queue(self) -> None:
        """Flush remaining operations during shutdown."""
        self.logger.info("Flushing remaining operations...")
        
        # Process remaining operations in main queue
        remaining_ops = []
        while not self.operation_queue.empty():
            try:
                operation = self.operation_queue.get_nowait()
                remaining_ops.append(operation)
            except asyncio.QueueEmpty:
                break
        
        # Process remaining operations in retry queue
        while not self.retry_queue.empty():
            try:
                operation = self.retry_queue.get_nowait()
                remaining_ops.append(operation)
            except asyncio.QueueEmpty:
                break
        
        if remaining_ops:
            self.logger.info(f"Processing {len(remaining_ops)} remaining operations...")
            await self._process_batch(remaining_ops)
        
        self.logger.info("Queue flush completed")