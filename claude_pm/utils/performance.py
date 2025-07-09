"""
Performance Utilities for Claude PM Framework.

Provides circuit breaker pattern for fault tolerance and caching for performance optimization.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Awaitable
import logging

from ..models.health import HealthReport

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    total_requests: int = 0
    failed_requests: int = 0
    success_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100


class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascade failures.
    
    Monitors failure rates and opens the circuit when failure threshold is exceeded,
    allowing the system to fail fast and recover gracefully.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        failure_rate_threshold: float = 50.0,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name for identification
            failure_threshold: Number of failures before opening circuit
            failure_rate_threshold: Percentage of failures that triggers opening
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Consecutive successes needed to close circuit from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.failure_rate_threshold = failure_rate_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._state = CircuitBreakerState.CLOSED
        self._stats = CircuitBreakerStats()
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time: Optional[float] = None
        self._logger = logging.getLogger(f"circuit_breaker.{name}")
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats
    
    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to execute
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            Exception: Original function exceptions when circuit is closed
        """
        self._stats.total_requests += 1
        
        # Check if circuit should transition from open to half-open
        if self._state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        
        try:
            # Execute the function
            result = await func()
            
            # Record success
            self._record_success()
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to half-open state."""
        self._state = CircuitBreakerState.HALF_OPEN
        self._consecutive_successes = 0
        self._stats.state_changes += 1
        self._logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
    
    def _record_success(self) -> None:
        """Record a successful operation."""
        self._stats.success_requests += 1
        self._stats.last_success_time = datetime.now()
        self._consecutive_failures = 0
        self._consecutive_successes += 1
        
        # If in half-open state, check if we should close the circuit
        if self._state == CircuitBreakerState.HALF_OPEN:
            if self._consecutive_successes >= self.success_threshold:
                self._transition_to_closed()
    
    def _record_failure(self) -> None:
        """Record a failed operation."""
        self._stats.failed_requests += 1
        self._stats.last_failure_time = datetime.now()
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        self._last_failure_time = time.time()
        
        # Check if we should open the circuit
        if self._should_open_circuit():
            self._transition_to_open()
    
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened based on failure criteria."""
        # Check consecutive failures threshold
        if self._consecutive_failures >= self.failure_threshold:
            return True
        
        # Check failure rate threshold (if we have enough data)
        if self._stats.total_requests >= self.failure_threshold:
            if self._stats.failure_rate >= self.failure_rate_threshold:
                return True
        
        return False
    
    def _transition_to_open(self) -> None:
        """Transition circuit breaker to open state."""
        self._state = CircuitBreakerState.OPEN
        self._stats.state_changes += 1
        self._logger.warning(f"Circuit breaker '{self.name}' opened due to failures")
    
    def _transition_to_closed(self) -> None:
        """Transition circuit breaker to closed state."""
        self._state = CircuitBreakerState.CLOSED
        self._stats.state_changes += 1
        self._logger.info(f"Circuit breaker '{self.name}' closed after recovery")
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitBreakerState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time = None
        self._stats.state_changes += 1
        self._logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "stats": {
                "total_requests": self._stats.total_requests,
                "failed_requests": self._stats.failed_requests,
                "success_requests": self._stats.success_requests,
                "failure_rate": self._stats.failure_rate,
                "state_changes": self._stats.state_changes,
                "last_failure_time": self._stats.last_failure_time.isoformat() if self._stats.last_failure_time else None,
                "last_success_time": self._stats.last_success_time.isoformat() if self._stats.last_success_time else None
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "failure_rate_threshold": self.failure_rate_threshold,
                "recovery_timeout": self.recovery_timeout,
                "success_threshold": self.success_threshold
            },
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
            "time_since_last_failure": time.time() - self._last_failure_time if self._last_failure_time else None
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with TTL support."""
    value: T
    created_at: float
    ttl_seconds: float
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at


class HealthCache:
    """
    High-performance cache for health reports with TTL support.
    
    Optimized for the health dashboard use case with 30-second TTL
    and target response time of <100ms for cache hits.
    """
    
    def __init__(self, default_ttl_seconds: float = 30.0, max_size: int = 100):
        """
        Initialize health cache.
        
        Args:
            default_ttl_seconds: Default TTL for cache entries
            max_size: Maximum number of cache entries
        """
        self.default_ttl_seconds = default_ttl_seconds
        self.max_size = max_size
        
        self._cache: Dict[str, CacheEntry[HealthReport]] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._logger = logging.getLogger("health_cache")
    
    def get(self, key: str) -> Optional[HealthReport]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached HealthReport if found and not expired, None otherwise
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: HealthReport, ttl_seconds: Optional[float] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: HealthReport to cache
            ttl_seconds: TTL for this entry (uses default if not specified)
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl_seconds
        
        # Enforce max size by removing oldest entries
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl_seconds
        )
        
        self._cache[key] = entry
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was found and removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._logger.info("Health cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self._logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
        self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / max(total_requests, 1)) * 100
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "current_size": len(self._cache),
            "max_size": self.max_size,
            "default_ttl_seconds": self.default_ttl_seconds
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        entries = []
        for key, entry in self._cache.items():
            entries.append({
                "key": key,
                "age_seconds": entry.age_seconds,
                "ttl_seconds": entry.ttl_seconds,
                "is_expired": entry.is_expired,
                "created_at": datetime.fromtimestamp(entry.created_at).isoformat()
            })
        
        return {
            "entries": entries,
            "stats": self.get_stats()
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def __len__(self) -> int:
        """Get number of cache entries."""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        entry = self._cache.get(key)
        return entry is not None and not entry.is_expired