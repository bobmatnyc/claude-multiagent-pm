"""
Evaluation Performance Optimization
==================================

This module provides performance optimization features for the evaluation system,
including advanced caching, async processing, and performance monitoring.

Key Features:
- Advanced caching with LRU and TTL strategies
- Async batch processing with queue management
- Performance monitoring and optimization
- Resource management and throttling
- Circuit breaker pattern for reliability
- Performance profiling and analysis

Performance Targets:
- Evaluation overhead: <100ms
- Cache hit rate: >95%
- Throughput: >50 evaluations/second
- Memory usage: <500MB for cache
- Error rate: <1%
"""

import asyncio
import logging
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable
from enum import Enum
import hashlib
import json
import threading
from pathlib import Path
import sys
import traceback
import weakref

from claude_pm.core.config import Config
from claude_pm.services.mirascope_evaluator import EvaluationResult, MirascopeEvaluator
from claude_pm.services.correction_capture import CorrectionData

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies."""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    HYBRID = "hybrid"  # Combined LRU + TTL


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit breaker active
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0
    
    def update_access(self) -> None:
        """Update access metadata."""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if entry is expired."""
        return (datetime.now() - self.created_at).total_seconds() > ttl_seconds


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    peak_memory_usage: float = 0.0
    error_count: int = 0
    circuit_breaker_trips: int = 0
    
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def error_rate(self) -> float:
        """Calculate error rate."""
        return (self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0.0


class AdvancedEvaluationCache:
    """
    Advanced caching system with multiple strategies.
    
    Supports LRU, TTL, and hybrid caching strategies with
    performance monitoring and automatic optimization.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        strategy: CacheStrategy = CacheStrategy.HYBRID,
        memory_limit_mb: int = 100
    ):
        """
        Initialize advanced cache.
        
        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time to live in seconds
            strategy: Cache strategy to use
            memory_limit_mb: Memory limit in MB
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.strategy = strategy
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        
        # Storage
        self.entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self.size_bytes = 0
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info(f"Advanced cache initialized: strategy={strategy.value}, max_size={max_size}")
    
    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired()
                self._optimize_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def _cleanup_expired(self) -> None:
        """Clean up expired entries."""
        with self.lock:
            expired_keys = []
            
            for key, entry in self.entries.items():
                if entry.is_expired(self.ttl_seconds):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
                self.metrics.cache_evictions += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _optimize_cache(self) -> None:
        """Optimize cache performance."""
        with self.lock:
            # Check memory usage
            if self.size_bytes > self.memory_limit_bytes:
                self._evict_by_memory()
            
            # Update peak memory usage
            self.metrics.peak_memory_usage = max(
                self.metrics.peak_memory_usage,
                self.size_bytes / (1024 * 1024)  # MB
            )
    
    def _evict_by_memory(self) -> None:
        """Evict entries to reduce memory usage."""
        target_size = self.memory_limit_bytes * 0.8  # 80% of limit
        
        # Sort by access frequency (ascending)
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: x[1].access_count / max(1, (datetime.now() - x[1].created_at).total_seconds() / 3600)
        )
        
        evicted_count = 0
        for key, entry in sorted_entries:
            if self.size_bytes <= target_size:
                break
            
            self._remove_entry(key)
            evicted_count += 1
            self.metrics.cache_evictions += 1
        
        logger.info(f"Evicted {evicted_count} entries to reduce memory usage")
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self.entries:
            entry = self.entries.pop(key)
            self.size_bytes -= entry.size_bytes
    
    def _calculate_entry_size(self, value: Any) -> int:
        """Calculate approximate size of cache entry."""
        try:
            # Rough estimation
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return sys.getsizeof(value)
            elif isinstance(value, EvaluationResult):
                # Estimate based on content
                size = len(value.response_text.encode('utf-8'))
                size += len(str(value.to_dict()).encode('utf-8'))
                return size
            else:
                return sys.getsizeof(str(value))
        except Exception:
            return 1024  # Default 1KB
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            self.metrics.total_requests += 1
            
            if key not in self.entries:
                self.metrics.cache_misses += 1
                return None
            
            entry = self.entries[key]
            
            # Check TTL if applicable
            if self.strategy in [CacheStrategy.TTL, CacheStrategy.HYBRID]:
                if entry.is_expired(self.ttl_seconds):
                    self._remove_entry(key)
                    self.metrics.cache_misses += 1
                    self.metrics.cache_evictions += 1
                    return None
            
            # Update access metadata
            entry.update_access()
            
            # Move to end for LRU
            if self.strategy in [CacheStrategy.LRU, CacheStrategy.HYBRID]:
                self.entries.move_to_end(key)
            
            self.metrics.cache_hits += 1
            return entry.value
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        with self.lock:
            entry_size = self._calculate_entry_size(value)
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                size_bytes=entry_size
            )
            
            # Remove existing entry if present
            if key in self.entries:
                self._remove_entry(key)
            
            # Check size limits
            while (len(self.entries) >= self.max_size or 
                   self.size_bytes + entry_size > self.memory_limit_bytes):
                if not self.entries:
                    break
                
                # Evict based on strategy
                if self.strategy == CacheStrategy.LRU:
                    oldest_key = next(iter(self.entries))
                    self._remove_entry(oldest_key)
                elif self.strategy == CacheStrategy.TTL:
                    # Find expired entries first
                    expired_key = None
                    for k, e in self.entries.items():
                        if e.is_expired(self.ttl_seconds):
                            expired_key = k
                            break
                    
                    if expired_key:
                        self._remove_entry(expired_key)
                    else:
                        # Remove oldest if no expired entries
                        oldest_key = next(iter(self.entries))
                        self._remove_entry(oldest_key)
                else:  # HYBRID
                    # Try expired first, then LRU
                    expired_key = None
                    for k, e in self.entries.items():
                        if e.is_expired(self.ttl_seconds):
                            expired_key = k
                            break
                    
                    if expired_key:
                        self._remove_entry(expired_key)
                    else:
                        oldest_key = next(iter(self.entries))
                        self._remove_entry(oldest_key)
                
                self.metrics.cache_evictions += 1
            
            # Add new entry
            self.entries[key] = entry
            self.size_bytes += entry_size
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            cleared_count = len(self.entries)
            self.entries.clear()
            self.size_bytes = 0
            logger.info(f"Cleared {cleared_count} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "strategy": self.strategy.value,
                "entries": len(self.entries),
                "max_size": self.max_size,
                "size_bytes": self.size_bytes,
                "size_mb": self.size_bytes / (1024 * 1024),
                "memory_limit_mb": self.memory_limit_bytes / (1024 * 1024),
                "hit_rate": self.metrics.cache_hit_rate(),
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_evictions": self.metrics.cache_evictions,
                "total_requests": self.metrics.total_requests,
                "peak_memory_mb": self.metrics.peak_memory_usage
            }


class CircuitBreaker:
    """
    Circuit breaker pattern for evaluation system reliability.
    
    Protects against cascading failures and provides fallback behavior.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Timeout before attempting half-open
            success_threshold: Number of successes to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        
        self.lock = threading.RLock()
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={timeout_seconds}s")
    
    def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Awaitable[Any]:
        """Execute function with circuit breaker protection."""
        return self._call_async(func, *args, **kwargs)
    
    async def _call_async(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - calls are blocked")
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() > self.timeout_seconds
    
    def _record_success(self) -> None:
        """Record successful operation."""
        with self.lock:
            self.success_count += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker CLOSED - normal operation resumed")
    
    def _record_failure(self) -> None:
        """Record failed operation."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker OPEN - blocking calls after {self.failure_count} failures")
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning("Circuit breaker returned to OPEN state after failure in HALF_OPEN")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "timeout_seconds": self.timeout_seconds,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
            }


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


class OptimizedEvaluationProcessor(AsyncBatchProcessor):
    """
    Optimized evaluation processor using batch processing.
    
    Extends AsyncBatchProcessor for evaluation-specific optimizations.
    """
    
    def __init__(
        self,
        evaluator: MirascopeEvaluator,
        cache: AdvancedEvaluationCache,
        circuit_breaker: CircuitBreaker,
        **kwargs
    ):
        """
        Initialize optimized processor.
        
        Args:
            evaluator: Mirascope evaluator instance
            cache: Advanced cache instance
            circuit_breaker: Circuit breaker instance
        """
        super().__init__(**kwargs)
        self.evaluator = evaluator
        self.cache = cache
        self.circuit_breaker = circuit_breaker
    
    async def _process_items(self, items: List[Dict[str, Any]]) -> List[Any]:
        """Process evaluation items in batch."""
        results = []
        
        # Separate cached and non-cached items
        cached_items = []
        non_cached_items = []
        cache_keys = []
        
        for item in items:
            cache_key = self._generate_cache_key(item)
            cache_keys.append(cache_key)
            
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                cached_items.append(cached_result)
                non_cached_items.append(None)
            else:
                cached_items.append(None)
                non_cached_items.append(item)
        
        # Process non-cached items
        evaluation_results = []
        for item in non_cached_items:
            if item is None:
                evaluation_results.append(None)
            else:
                try:
                    result = await self.circuit_breaker.call(
                        self.evaluator.evaluate_response,
                        item["agent_type"],
                        item["response_text"],
                        item["context"],
                        item.get("correction_id")
                    )
                    evaluation_results.append(result)
                except Exception as e:
                    evaluation_results.append(e)
        
        # Combine cached and evaluated results
        eval_index = 0
        for i, cached_result in enumerate(cached_items):
            if cached_result is not None:
                results.append(cached_result)
            else:
                eval_result = evaluation_results[eval_index]
                eval_index += 1
                
                if isinstance(eval_result, Exception):
                    results.append(eval_result)
                else:
                    # Cache the result
                    self.cache.put(cache_keys[i], eval_result)
                    results.append(eval_result)
        
        return results
    
    def _generate_cache_key(self, item: Dict[str, Any]) -> str:
        """Generate cache key for evaluation item."""
        content = f"{item['agent_type']}:{item['response_text']}:{json.dumps(item['context'], sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()


class EvaluationPerformanceManager:
    """
    Main performance manager for evaluation system.
    
    Coordinates caching, batching, and performance optimization.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize performance manager.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("evaluation_performance_enabled", True)
        
        # Initialize components
        self.cache = AdvancedEvaluationCache(
            max_size=self.config.get("evaluation_cache_max_size", 1000),
            ttl_seconds=self.config.get("evaluation_cache_ttl_seconds", 3600),
            strategy=CacheStrategy(self.config.get("evaluation_cache_strategy", "hybrid")),
            memory_limit_mb=self.config.get("evaluation_cache_memory_limit_mb", 100)
        )
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("evaluation_circuit_breaker_threshold", 5),
            timeout_seconds=self.config.get("evaluation_circuit_breaker_timeout", 60),
            success_threshold=self.config.get("evaluation_circuit_breaker_success_threshold", 3)
        )
        
        # Will be initialized with evaluator
        self.processor: Optional[OptimizedEvaluationProcessor] = None
        self.evaluator: Optional[MirascopeEvaluator] = None
        
        # Performance tracking
        self.start_time = datetime.now()
        self.total_evaluations = 0
        self.total_time = 0.0
        
        if self.enabled:
            logger.info("Evaluation performance manager initialized")
    
    async def initialize(self, evaluator: MirascopeEvaluator) -> None:
        """Initialize with evaluator instance."""
        self.evaluator = evaluator
        
        # Initialize batch processor
        self.processor = OptimizedEvaluationProcessor(
            evaluator=evaluator,
            cache=self.cache,
            circuit_breaker=self.circuit_breaker,
            batch_size=self.config.get("evaluation_batch_size", 10),
            max_batch_wait_ms=self.config.get("evaluation_batch_wait_ms", 100),
            max_concurrent_batches=self.config.get("evaluation_max_concurrent_batches", 5)
        )
        
        # Start background tasks
        await self.cache.start_cleanup_task()
        await self.processor.start()
        
        logger.info("Performance manager initialized with evaluator")
    
    async def shutdown(self) -> None:
        """Shutdown performance manager."""
        if self.processor:
            await self.processor.stop()
        
        await self.cache.stop_cleanup_task()
        
        logger.info("Performance manager shutdown complete")
    
    async def evaluate_response(
        self,
        agent_type: str,
        response_text: str,
        context: Dict[str, Any],
        correction_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate response with performance optimization.
        
        Args:
            agent_type: Type of agent
            response_text: Response to evaluate
            context: Context information
            correction_id: Optional correction ID
            
        Returns:
            Evaluation result
        """
        if not self.enabled or not self.processor:
            # Fallback to direct evaluation
            return await self.evaluator.evaluate_response(
                agent_type, response_text, context, correction_id
            )
        
        start_time = time.time()
        
        try:
            # Submit to batch processor
            item = {
                "agent_type": agent_type,
                "response_text": response_text,
                "context": context,
                "correction_id": correction_id
            }
            
            result = await self.processor.submit(item)
            
            # Handle exceptions
            if isinstance(result, Exception):
                raise result
            
            # Update performance metrics
            self.total_evaluations += 1
            self.total_time += time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized evaluation failed: {e}")
            
            # Fallback to direct evaluation
            return await self.evaluator.evaluate_response(
                agent_type, response_text, context, correction_id
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            "enabled": self.enabled,
            "uptime_seconds": uptime,
            "total_evaluations": self.total_evaluations,
            "average_evaluation_time": self.total_time / self.total_evaluations if self.total_evaluations > 0 else 0,
            "evaluations_per_second": self.total_evaluations / uptime if uptime > 0 else 0,
            "cache_stats": self.cache.get_stats(),
            "circuit_breaker_state": self.circuit_breaker.get_state(),
            "processor_stats": self.processor.get_stats() if self.processor else None
        }
        
        return stats
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear performance cache."""
        self.cache.clear()
        
        return {
            "cache_cleared": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_circuit_breaker(self) -> Dict[str, Any]:
        """Reset circuit breaker to closed state."""
        with self.circuit_breaker.lock:
            self.circuit_breaker.state = CircuitBreakerState.CLOSED
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.success_count = 0
            self.circuit_breaker.last_failure_time = None
        
        return {
            "circuit_breaker_reset": True,
            "timestamp": datetime.now().isoformat()
        }


# Global performance manager instance
_performance_manager: Optional[EvaluationPerformanceManager] = None


def get_performance_manager(config: Optional[Config] = None) -> EvaluationPerformanceManager:
    """Get global performance manager instance."""
    global _performance_manager
    
    if _performance_manager is None:
        _performance_manager = EvaluationPerformanceManager(config)
    
    return _performance_manager


async def initialize_performance_manager(evaluator: MirascopeEvaluator, config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize the performance manager."""
    try:
        manager = get_performance_manager(config)
        await manager.initialize(evaluator)
        
        stats = manager.get_performance_stats()
        
        return {
            "initialized": True,
            "performance_enabled": manager.enabled,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize performance manager: {e}")
        return {"initialized": False, "error": str(e)}


async def shutdown_performance_manager() -> None:
    """Shutdown the performance manager."""
    global _performance_manager
    
    if _performance_manager:
        await _performance_manager.shutdown()
        _performance_manager = None


# Helper functions
async def optimized_evaluate_response(
    agent_type: str,
    response_text: str,
    context: Dict[str, Any],
    correction_id: Optional[str] = None,
    config: Optional[Config] = None
) -> EvaluationResult:
    """
    Evaluate response with performance optimization.
    
    Args:
        agent_type: Type of agent
        response_text: Response to evaluate
        context: Context information
        correction_id: Optional correction ID
        config: Optional configuration
        
    Returns:
        Evaluation result
    """
    manager = get_performance_manager(config)
    return await manager.evaluate_response(agent_type, response_text, context, correction_id)


def get_evaluation_performance_stats(config: Optional[Config] = None) -> Dict[str, Any]:
    """Get evaluation performance statistics."""
    manager = get_performance_manager(config)
    return manager.get_performance_stats()


if __name__ == "__main__":
    # Test the performance system
    print("Testing Evaluation Performance System")
    print("=" * 50)
    
    # Test cache
    cache = AdvancedEvaluationCache(max_size=100, ttl_seconds=10)
    
    # Test operations
    cache.put("test_key", "test_value")
    value = cache.get("test_key")
    print(f"Cache test: {value}")
    
    # Test circuit breaker
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=5)
    
    async def test_function():
        return "success"
    
    async def test_circuit_breaker():
        try:
            result = await circuit_breaker.call(test_function)
            print(f"Circuit breaker test: {result}")
        except Exception as e:
            print(f"Circuit breaker error: {e}")
    
    # Test batch processor
    processor = AsyncBatchProcessor(batch_size=5, max_batch_wait_ms=50)
    
    async def test_batch_processor():
        await processor.start()
        
        # Submit test items
        results = await asyncio.gather(
            processor.submit("item1"),
            processor.submit("item2"),
            processor.submit("item3")
        )
        
        print(f"Batch processor results: {results}")
        
        await processor.stop()
    
    # Run tests
    async def run_tests():
        await test_circuit_breaker()
        await test_batch_processor()
        
        # Test cache cleanup
        await cache.start_cleanup_task()
        await asyncio.sleep(0.1)
        await cache.stop_cleanup_task()
        
        # Get stats
        cache_stats = cache.get_stats()
        print(f"Cache stats: {cache_stats}")
    
    asyncio.run(run_tests())