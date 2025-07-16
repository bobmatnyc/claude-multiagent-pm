#!/usr/bin/env python3
"""
Performance Utilities Module
============================

Utilities for performance monitoring, circuit breaking, caching, and optimization.
Provides core infrastructure for health monitoring and performance management.

Framework Version: 014
Implementation: 2025-07-16
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, Generic, TypeVar
import threading
from concurrent.futures import Future

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with TTL and metadata."""
    value: T
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl_seconds <= 0:
            return False  # No expiration
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time
    
    def access(self) -> T:
        """Access the cached value and update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value


class CircuitBreaker:
    """
    Circuit breaker for handling service failures gracefully.
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide automatic recovery testing.
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception,
                 name: str = "CircuitBreaker"):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            expected_exception: Exception type that counts as failure
            name: Name for logging and identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.circuit_open_count = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Circuit breaker '{self.name}' initialized: "
                   f"threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for wrapping functions with circuit breaker."""
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return sync_wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        with self._lock:
            self.total_requests += 1
            
            # Check circuit state
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
                else:
                    logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting request")
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open"
                    )
            
            # Attempt the call
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call async function with circuit breaker protection."""
        with self._lock:
            self.total_requests += 1
            
            # Check circuit state
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
                else:
                    logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting request")
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open"
                    )
        
        # Attempt the call (outside lock to avoid blocking other requests)
        try:
            result = await func(*args, **kwargs)
            with self._lock:
                self._on_success()
            return result
            
        except self.expected_exception as e:
            with self._lock:
                self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request."""
        self.successful_requests += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Recovery successful, close circuit
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' recovered, moved to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed request."""
        self.failed_requests += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitBreakerState.OPEN:
                self.state = CircuitBreakerState.OPEN
                self.circuit_open_count += 1
                logger.warning(f"Circuit breaker '{self.name}' OPENED after "
                             f"{self.failure_count} failures")
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
        
        return {
            'name': self.name,
            'state': self.state.value,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate_percent': success_rate,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'circuit_open_count': self.circuit_open_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }
    
    def reset(self):
        """Manually reset circuit breaker."""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class HealthCache:
    """
    High-performance cache for health monitoring data.
    
    Provides TTL-based caching with automatic cleanup and statistics.
    """
    
    def __init__(self,
                 default_ttl: int = 300,
                 max_size: int = 1000,
                 cleanup_interval: int = 60):
        """
        Initialize health cache.
        
        Args:
            default_ttl: Default TTL in seconds
            max_size: Maximum number of cache entries
            cleanup_interval: Seconds between cleanup runs
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.cleanups = 0
        
        # Background cleanup
        self._cleanup_timer: Optional[threading.Timer] = None
        self._start_cleanup_timer()
        
        logger.info(f"HealthCache initialized: ttl={default_ttl}s, max_size={max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            
            if not entry:
                self.misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl
            )
            
            # Check size limit
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("HealthCache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.cleanups += 1
                logger.debug(f"HealthCache cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry to make room."""
        if not self._cache:
            return
        
        # Find oldest entry by creation time
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        
        del self._cache[oldest_key]
        self.evictions += 1
        logger.debug(f"HealthCache evicted oldest entry: {oldest_key}")
    
    def _start_cleanup_timer(self) -> None:
        """Start background cleanup timer."""
        def cleanup_task():
            try:
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"HealthCache cleanup error: {e}")
            finally:
                # Schedule next cleanup
                self._cleanup_timer = threading.Timer(
                    self.cleanup_interval,
                    cleanup_task
                )
                self._cleanup_timer.daemon = True
                self._cleanup_timer.start()
        
        self._cleanup_timer = threading.Timer(
            self.cleanup_interval,
            cleanup_task
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': hit_rate,
                'evictions': self.evictions,
                'cleanups': self.cleanups,
                'default_ttl': self.default_ttl
            }
    
    def __del__(self):
        """Cleanup timer on destruction."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()


class PerformanceMonitor:
    """Monitor performance metrics and provide insights."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, unit: str = ""):
        """Record a performance metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = {
                    'values': [],
                    'unit': unit,
                    'count': 0,
                    'total': 0.0,
                    'min': float('inf'),
                    'max': float('-inf')
                }
            
            metric = self.metrics[name]
            metric['values'].append(value)
            metric['count'] += 1
            metric['total'] += value
            metric['min'] = min(metric['min'], value)
            metric['max'] = max(metric['max'], value)
            
            # Keep only last 100 values
            if len(metric['values']) > 100:
                metric['values'] = metric['values'][-100:]
    
    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a metric."""
        with self._lock:
            if name not in self.metrics:
                return None
            
            metric = self.metrics[name]
            avg = metric['total'] / metric['count'] if metric['count'] > 0 else 0.0
            
            return {
                'name': name,
                'unit': metric['unit'],
                'count': metric['count'],
                'average': avg,
                'minimum': metric['min'] if metric['min'] != float('inf') else 0.0,
                'maximum': metric['max'] if metric['max'] != float('-inf') else 0.0,
                'latest': metric['values'][-1] if metric['values'] else 0.0
            }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metric summaries."""
        with self._lock:
            return {
                name: self.get_metric_summary(name)
                for name in self.metrics.keys()
            }
    
    def get_uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time


# Factory functions
def create_circuit_breaker(name: str = "default",
                          failure_threshold: int = 5,
                          recovery_timeout: int = 60) -> CircuitBreaker:
    """Create a circuit breaker with specified parameters."""
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name
    )


def create_health_cache(ttl: int = 300,
                       max_size: int = 1000) -> HealthCache:
    """Create a health cache with specified parameters."""
    return HealthCache(
        default_ttl=ttl,
        max_size=max_size
    )


def create_performance_monitor() -> PerformanceMonitor:
    """Create a performance monitor."""
    return PerformanceMonitor()


if __name__ == "__main__":
    # Demo functionality
    async def demo():
        """Demonstrate performance utilities."""
        print("⚡ Performance Utilities Demo")
        print("=" * 40)
        
        # Circuit breaker demo
        print("\n🔌 Circuit Breaker Demo")
        breaker = create_circuit_breaker("demo", failure_threshold=2, recovery_timeout=1)
        
        @breaker
        async def flaky_service(should_fail: bool = False):
            if should_fail:
                raise Exception("Service failure")
            return "Success!"
        
        # Test successful calls
        try:
            result = await flaky_service(False)
            print(f"Success: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test failures to open circuit
        for i in range(3):
            try:
                await flaky_service(True)
            except Exception as e:
                print(f"Failure {i+1}: {type(e).__name__}")
        
        print(f"Circuit state: {breaker.get_state()}")
        print(f"Circuit stats: {breaker.get_stats()}")
        
        # Cache demo
        print("\n🗄️ Health Cache Demo")
        cache = create_health_cache(ttl=2, max_size=5)
        
        cache.set("key1", "value1")
        cache.set("key2", {"data": "complex"})
        
        print(f"Get key1: {cache.get('key1')}")
        print(f"Get key2: {cache.get('key2')}")
        print(f"Get missing: {cache.get('missing')}")
        
        # Wait for expiration
        await asyncio.sleep(3)
        print(f"Get key1 after TTL: {cache.get('key1')}")
        
        print(f"Cache stats: {cache.get_stats()}")
        
        # Performance monitor demo
        print("\n📊 Performance Monitor Demo")
        monitor = create_performance_monitor()
        
        # Record some metrics
        for i in range(10):
            monitor.record_metric("response_time", i * 0.1, "seconds")
            monitor.record_metric("cpu_usage", 20 + i * 2, "percent")
        
        print(f"Response time summary: {monitor.get_metric_summary('response_time')}")
        print(f"CPU usage summary: {monitor.get_metric_summary('cpu_usage')}")
        print(f"Uptime: {monitor.get_uptime():.2f} seconds")
    
    # Run demo
    asyncio.run(demo())