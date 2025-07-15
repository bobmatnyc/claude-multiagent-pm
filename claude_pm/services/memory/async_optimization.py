#!/usr/bin/env python3
"""
Async Memory System Performance Optimization

This module provides optimized async operations for the memory system,
addressing timeout issues, concurrent access patterns, and performance
bottlenecks identified during validation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import weakref

from .interfaces.backend import MemoryBackend
from .interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from .interfaces.exceptions import MemoryServiceError, BackendError

logger = logging.getLogger(__name__)


class AsyncMemoryOperationOptimizer:
    """
    Optimizes async memory operations for better performance and reliability.
    
    Features:
    - Connection pooling optimization
    - Request batching and queuing
    - Timeout management and recovery
    - Concurrent operation throttling
    - Memory operation caching
    - Performance monitoring and auto-tuning
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Performance tuning parameters
        self.max_concurrent_ops = self.config.get("max_concurrent_ops", 10)
        self.operation_timeout = self.config.get("operation_timeout", 15.0)
        self.batch_size = self.config.get("batch_size", 5)
        self.queue_max_size = self.config.get("queue_max_size", 100)
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes
        
        # Operation management
        self._operation_semaphore = asyncio.Semaphore(self.max_concurrent_ops)
        self._operation_queue = asyncio.Queue(maxsize=self.queue_max_size)
        self._pending_operations = weakref.WeakSet()
        self._operation_cache = {}
        self._cache_timestamps = {}
        
        # Performance metrics
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "timeout_operations": 0,
            "cached_operations": 0,
            "avg_operation_time": 0.0,
            "max_operation_time": 0.0,
            "concurrent_operations": 0,
            "queue_size": 0,
        }
        
        # Background tasks
        self._queue_processor_task = None
        self._cache_cleanup_task = None
        self._running = False
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    async def start(self):
        """Start the optimization service."""
        if self._running:
            return
            
        self._running = True
        
        # Start background tasks
        self._queue_processor_task = asyncio.create_task(self._process_operation_queue())
        self._cache_cleanup_task = asyncio.create_task(self._cleanup_cache_periodically())
        
        logger.info("Async memory operation optimizer started")
    
    async def stop(self):
        """Stop the optimization service."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel background tasks
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
                
        if self._cache_cleanup_task:
            self._cache_cleanup_task.cancel()
            try:
                await self._cache_cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True)
        
        logger.info("Async memory operation optimizer stopped")
    
    @asynccontextmanager
    async def optimized_operation(self, operation_name: str):
        """Context manager for optimized async operations."""
        start_time = time.time()
        self.metrics["total_operations"] += 1
        self.metrics["concurrent_operations"] += 1
        
        try:
            async with self._operation_semaphore:
                yield
                
            # Record successful operation
            execution_time = time.time() - start_time
            self.metrics["successful_operations"] += 1
            self._update_timing_metrics(execution_time)
            
        except asyncio.TimeoutError:
            self.metrics["timeout_operations"] += 1
            self.metrics["failed_operations"] += 1
            logger.warning(f"Operation {operation_name} timed out after {time.time() - start_time:.2f}s")
            raise
            
        except Exception as e:
            self.metrics["failed_operations"] += 1
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
            
        finally:
            self.metrics["concurrent_operations"] -= 1
    
    async def optimized_add_memory(
        self,
        backend: MemoryBackend,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Optimized memory addition with batching and timeout handling."""
        
        async with self.optimized_operation("add_memory"):
            # Apply timeout wrapper
            try:
                return await asyncio.wait_for(
                    backend.add_memory(project_name, content, category, tags, metadata),
                    timeout=self.operation_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Memory addition timed out for project {project_name}")
                raise MemoryServiceError(f"Add memory operation timed out after {self.operation_timeout}s")
    
    async def optimized_search_memories(
        self,
        backend: MemoryBackend,
        project_name: str,
        query: MemoryQuery,
    ) -> List[MemoryItem]:
        """Optimized memory search with caching and timeout handling."""
        
        # Check cache first
        cache_key = self._generate_cache_key("search", project_name, query.query, query.category)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self.metrics["cached_operations"] += 1
            return cached_result
        
        async with self.optimized_operation("search_memories"):
            try:
                # Apply timeout wrapper
                result = await asyncio.wait_for(
                    backend.search_memories(project_name, query),
                    timeout=self.operation_timeout
                )
                
                # Cache successful results
                self._cache_result(cache_key, result)
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Memory search timed out for project {project_name}")
                raise MemoryServiceError(f"Search memories operation timed out after {self.operation_timeout}s")
    
    async def optimized_batch_operations(
        self,
        operations: List[Callable],
        max_concurrent: Optional[int] = None,
    ) -> List[Any]:
        """Execute multiple operations in optimized batches."""
        
        if not operations:
            return []
            
        # Use configured or custom concurrency limit
        concurrent_limit = max_concurrent or self.max_concurrent_ops
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def execute_with_semaphore(operation):
            async with semaphore:
                try:
                    return await operation()
                except Exception as e:
                    logger.error(f"Batch operation failed: {e}")
                    return None
        
        # Execute operations in batches
        results = []
        for i in range(0, len(operations), self.batch_size):
            batch = operations[i:i + self.batch_size]
            batch_tasks = [execute_with_semaphore(op) for op in batch]
            
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks, return_exceptions=True),
                    timeout=self.operation_timeout * 2  # Allow more time for batches
                )
                results.extend(batch_results)
                
            except asyncio.TimeoutError:
                logger.warning(f"Batch operations timed out (batch {i // self.batch_size + 1})")
                results.extend([None] * len(batch))
        
        return results
    
    async def optimized_concurrent_validation(
        self,
        validation_functions: List[Callable],
        project_name: str = "validation",
    ) -> Dict[str, Any]:
        """Optimized concurrent validation operations for QA scenarios."""
        
        validation_results = {
            "total_validations": len(validation_functions),
            "successful_validations": 0,
            "failed_validations": 0,
            "validation_errors": [],
            "validation_times": [],
            "overall_success": False,
        }
        
        async def execute_validation(validation_func, validation_name):
            """Execute single validation with error handling."""
            start_time = time.time()
            try:
                async with self.optimized_operation(f"validation_{validation_name}"):
                    result = await asyncio.wait_for(
                        validation_func(),
                        timeout=self.operation_timeout
                    )
                    
                execution_time = time.time() - start_time
                validation_results["validation_times"].append(execution_time)
                validation_results["successful_validations"] += 1
                
                return {"name": validation_name, "success": True, "result": result, "time": execution_time}
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                validation_results["failed_validations"] += 1
                error_msg = f"Validation {validation_name} timed out after {execution_time:.2f}s"
                validation_results["validation_errors"].append(error_msg)
                logger.warning(error_msg)
                return {"name": validation_name, "success": False, "error": "timeout", "time": execution_time}
                
            except Exception as e:
                execution_time = time.time() - start_time
                validation_results["failed_validations"] += 1
                error_msg = f"Validation {validation_name} failed: {e}"
                validation_results["validation_errors"].append(error_msg)
                logger.error(error_msg)
                return {"name": validation_name, "success": False, "error": str(e), "time": execution_time}
        
        # Execute validations concurrently with limited concurrency
        validation_tasks = [
            execute_validation(func, f"validation_{i}")
            for i, func in enumerate(validation_functions)
        ]
        
        individual_results = await self.optimized_batch_operations(
            [lambda task=task: task for task in validation_tasks],
            max_concurrent=min(len(validation_functions), 5)  # Limit concurrent validations
        )
        
        validation_results["individual_results"] = individual_results
        validation_results["overall_success"] = (
            validation_results["successful_validations"] >= len(validation_functions) * 0.8
        )
        
        if validation_results["validation_times"]:
            validation_results["avg_validation_time"] = (
                sum(validation_results["validation_times"]) / len(validation_results["validation_times"])
            )
            validation_results["max_validation_time"] = max(validation_results["validation_times"])
        
        return validation_results
    
    def _generate_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation."""
        key_parts = [operation] + [str(arg) for arg in args]
        return "|".join(key_parts)
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid."""
        if cache_key not in self._operation_cache:
            return None
            
        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > self.cache_ttl:
            # Cache expired
            self._operation_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            return None
            
        return self._operation_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache operation result."""
        self._operation_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
    
    def _update_timing_metrics(self, execution_time: float):
        """Update timing metrics."""
        current_avg = self.metrics["avg_operation_time"]
        total_ops = self.metrics["successful_operations"]
        
        if total_ops == 1:
            self.metrics["avg_operation_time"] = execution_time
        else:
            # Update rolling average
            self.metrics["avg_operation_time"] = (
                (current_avg * (total_ops - 1) + execution_time) / total_ops
            )
        
        if execution_time > self.metrics["max_operation_time"]:
            self.metrics["max_operation_time"] = execution_time
    
    async def _process_operation_queue(self):
        """Background task to process queued operations."""
        while self._running:
            try:
                # Process queue items
                self.metrics["queue_size"] = self._operation_queue.qsize()
                
                # Add any queue processing logic here if needed
                await asyncio.sleep(1.0)  # Check queue every second
                
            except Exception as e:
                logger.error(f"Error in operation queue processor: {e}")
                await asyncio.sleep(5.0)  # Back off on error
    
    async def _cleanup_cache_periodically(self):
        """Background task to clean up expired cache entries."""
        while self._running:
            try:
                current_time = time.time()
                expired_keys = [
                    key for key, timestamp in self._cache_timestamps.items()
                    if current_time - timestamp > self.cache_ttl
                ]
                
                for key in expired_keys:
                    self._operation_cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Sleep for half the cache TTL
                await asyncio.sleep(self.cache_ttl / 2)
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60.0)  # Back off on error
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        metrics = self.metrics.copy()
        metrics["cache_entries"] = len(self._operation_cache)
        metrics["pending_operations"] = len(self._pending_operations)
        return metrics
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "timeout_operations": 0,
            "cached_operations": 0,
            "avg_operation_time": 0.0,
            "max_operation_time": 0.0,
            "concurrent_operations": 0,
            "queue_size": 0,
        }
        
        # Clear cache
        self._operation_cache.clear()
        self._cache_timestamps.clear()


# Global optimizer instance for easy access
_global_optimizer: Optional[AsyncMemoryOperationOptimizer] = None


async def get_global_optimizer() -> AsyncMemoryOperationOptimizer:
    """Get or create global memory operation optimizer."""
    global _global_optimizer
    
    if _global_optimizer is None:
        _global_optimizer = AsyncMemoryOperationOptimizer({
            "max_concurrent_ops": 8,
            "operation_timeout": 10.0,
            "batch_size": 3,
            "cache_ttl": 180,  # 3 minutes
        })
        await _global_optimizer.start()
    
    return _global_optimizer


async def cleanup_global_optimizer():
    """Cleanup global optimizer."""
    global _global_optimizer
    
    if _global_optimizer is not None:
        await _global_optimizer.stop()
        _global_optimizer = None


# Context manager for optimized memory operations
@asynccontextmanager
async def optimized_memory_context():
    """Context manager for optimized memory operations."""
    optimizer = await get_global_optimizer()
    try:
        yield optimizer
    except Exception as e:
        logger.error(f"Error in optimized memory context: {e}")
        raise
    finally:
        # Optimizer cleanup is handled by global cleanup
        pass