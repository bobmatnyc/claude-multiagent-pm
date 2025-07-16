"""
Enhanced Shared Prompt Cache Service for Claude PM Framework v0.8.0
=================================================================

Enhanced implementation of the ICacheService interface with:
- Dependency injection integration
- Enhanced error handling and recovery
- Performance optimization and monitoring
- Service lifecycle management
- Health monitoring integration
- Circuit breaker pattern for resilience

Key Features:
- Interface-based design
- Automatic dependency resolution
- Comprehensive error handling
- Performance optimization
- Thread-safe operations
- Memory management
"""

import asyncio
import json
import logging
import threading
import time
import weakref
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
import hashlib

from ..core.interfaces import ICacheService, IConfigurationService
from ..core.enhanced_base_service import EnhancedBaseService
from ..core.container import injectable

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with comprehensive metadata."""
    key: str
    value: Any
    created_at: float
    ttl: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    hit_count: int = 0
    miss_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate for this entry."""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def touch(self) -> None:
        """Update access metrics."""
        self.access_count += 1
        self.hit_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheMetrics:
    """Enhanced cache performance metrics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    invalidations: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    evictions: int = 0
    expired_removals: int = 0
    memory_pressure_events: int = 0
    circuit_breaker_activations: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    @property
    def avg_entry_size(self) -> float:
        """Calculate average entry size."""
        return self.size_bytes / self.entry_count if self.entry_count > 0 else 0.0


@injectable(ICacheService)
class EnhancedSharedPromptCache(EnhancedBaseService, ICacheService):
    """
    Enhanced Shared Prompt Cache implementing ICacheService interface.
    
    Provides high-performance caching with comprehensive monitoring, error handling,
    and service lifecycle management.
    """
    
    _instance: Optional['EnhancedSharedPromptCache'] = None
    _instance_lock = threading.Lock()
    
    def __init__(self, config: Optional[IConfigurationService] = None):
        """Initialize the enhanced shared cache service."""
        super().__init__("enhanced_shared_prompt_cache", config)
        
        # Singleton pattern enforcement (optional)
        with EnhancedSharedPromptCache._instance_lock:
            if EnhancedSharedPromptCache._instance is None:
                EnhancedSharedPromptCache._instance = self
        
        # Cache configuration
        self._max_size = self._config.get("cache.max_size", 1000) if self._config else 1000
        self._max_memory_mb = self._config.get("cache.max_memory_mb", 100) if self._config else 100
        self._default_ttl = self._config.get("cache.default_ttl", 1800) if self._config else 1800
        self._cleanup_interval = self._config.get("cache.cleanup_interval", 300) if self._config else 300
        self._enable_metrics = self._config.get("cache.enable_metrics", True) if self._config else True
        
        # Cache storage - OrderedDict for LRU behavior
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_lock = threading.RLock()  # Reentrant lock for nested operations
        
        # Metrics and monitoring
        self._metrics = CacheMetrics()
        self._metrics_lock = threading.Lock()
        
        # Background task tracking
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Cache invalidation tracking
        self._invalidation_callbacks: Dict[str, List[Callable]] = {}
        self._namespace_dependencies: Dict[str, set] = {}
        
        # Performance optimization
        self._memory_pressure_threshold = 0.8  # 80% of max memory
        self._cleanup_batch_size = 50
        
        # Circuit breaker for cache operations
        self._circuit_breaker_threshold = 10  # failures in window
        self._circuit_breaker_window = 60  # seconds
        self._circuit_breaker_failures = []
        
        self._logger.info(
            f"Enhanced Shared Prompt Cache initialized with max_size={self._max_size}, "
            f"max_memory_mb={self._max_memory_mb}, default_ttl={self._default_ttl}s"
        )
    
    @classmethod
    def get_instance(cls, config: Optional[IConfigurationService] = None) -> 'EnhancedSharedPromptCache':
        """Get singleton instance (for backward compatibility)."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance
    
    async def _initialize(self) -> None:
        """Initialize the cache service."""
        self._logger.info("Initializing Enhanced Shared Prompt Cache service...")
        
        try:
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
            
            self._logger.info("Enhanced Shared Prompt Cache service initialized successfully")
        
        except Exception as e:
            self._logger.error(f"Failed to initialize Enhanced Shared Prompt Cache: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup cache service resources."""
        self._logger.info("Cleaning up Enhanced Shared Prompt Cache service...")
        
        try:
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clear cache
            with self._cache_lock:
                self._cache.clear()
            
            self._logger.info("Enhanced Shared Prompt Cache service cleaned up")
        
        except Exception as e:
            self._logger.error(f"Failed to cleanup Enhanced Shared Prompt Cache: {e}")
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform cache-specific health checks."""
        checks = {}
        
        try:
            # Test cache operations
            test_key = f"__health_check_{time.time()}"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Test set operation
            success = self.set(test_key, test_value, ttl=5)
            checks["cache_set"] = success
            
            if success:
                # Test get operation
                retrieved = self.get(test_key)
                checks["cache_get"] = retrieved is not None and retrieved.get("test") is True
                
                # Test delete operation
                deleted = self.delete(test_key)
                checks["cache_delete"] = deleted and self.get(test_key) is None
            
            # Check memory usage
            current_memory = self._get_memory_usage_mb()
            checks["memory_usage_ok"] = current_memory < self._max_memory_mb
            
            # Check cache size
            checks["cache_size_ok"] = len(self._cache) <= self._max_size
            
            # Check circuit breaker state
            checks["circuit_breaker_ok"] = not self._is_circuit_open()
            
            # Check hit rate (should be reasonable)
            checks["hit_rate_ok"] = self._metrics.hit_rate >= 0.3 or self._metrics.hits + self._metrics.misses < 10
        
        except Exception as e:
            self._logger.error(f"Cache health check failed: {e}")
            checks["cache_operations"] = False
        
        return checks
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key with enhanced error handling.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if self._is_circuit_open():
            self._logger.warning("Cache circuit breaker is open, returning None")
            return None
        
        try:
            with self._cache_lock:
                entry = self._cache.get(key)
                
                if entry is None:
                    # Cache miss
                    with self._metrics_lock:
                        self._metrics.misses += 1
                    self._logger.debug(f"Cache miss for key '{key}'")
                    return None
                
                if entry.is_expired:
                    # Entry expired, remove it
                    self._remove_entry(key, entry)
                    with self._metrics_lock:
                        self._metrics.misses += 1
                        self._metrics.expired_removals += 1
                    self._logger.debug(f"Cache entry expired for key '{key}'")
                    return None
                
                # Cache hit - update access metrics and move to end (LRU)
                entry.touch()
                self._cache.move_to_end(key)
                
                with self._metrics_lock:
                    self._metrics.hits += 1
                
                self._logger.debug(
                    f"Cache hit for key '{key}' (age: {entry.age_seconds:.1f}s, "
                    f"access_count: {entry.access_count})"
                )
                return entry.value
        
        except Exception as e:
            self._logger.error(f"Failed to get cache key '{key}': {e}")
            self._record_circuit_failure()
            with self._metrics_lock:
                self._metrics.misses += 1
            await self._handle_error(e, {"operation": "get", "key": key})
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set cached value with optional TTL and enhanced validation.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default_ttl if None)
            metadata: Optional metadata for the cache entry
            
        Returns:
            True if successful, False otherwise
        """
        if self._is_circuit_open():
            self._logger.warning("Cache circuit breaker is open, set operation blocked")
            return False
        
        try:
            with self._cache_lock:
                # Use default TTL if not specified
                if ttl is None:
                    ttl = self._default_ttl
                
                # Calculate entry size
                size_bytes = self._calculate_size(value)
                
                # Check memory pressure before adding
                if self._check_memory_pressure(size_bytes):
                    self._handle_memory_pressure()
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    ttl=ttl,
                    size_bytes=size_bytes,
                    metadata=metadata or {}
                )
                
                # Check if we need to evict entries
                self._ensure_cache_capacity(size_bytes)
                
                # Remove existing entry if present
                if key in self._cache:
                    old_entry = self._cache.pop(key)
                    with self._metrics_lock:
                        self._metrics.size_bytes -= old_entry.size_bytes
                
                # Add new entry (to end for LRU)
                self._cache[key] = entry
                
                # Update metrics
                with self._metrics_lock:
                    self._metrics.sets += 1
                    self._metrics.size_bytes += size_bytes
                    self._metrics.entry_count = len(self._cache)
            
            self._logger.debug(
                f"Cached key '{key}' with TTL {ttl}s, size {size_bytes} bytes"
            )
            return True
        
        except Exception as e:
            self._logger.error(f"Failed to set cache key '{key}': {e}")
            self._record_circuit_failure()
            await self._handle_error(e, {"operation": "set", "key": key, "size": size_bytes})
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value with enhanced logging.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            with self._cache_lock:
                entry = self._cache.pop(key, None)
                
                if entry is not None:
                    with self._metrics_lock:
                        self._metrics.deletes += 1
                        self._metrics.size_bytes -= entry.size_bytes
                        self._metrics.entry_count = len(self._cache)
                    
                    self._logger.debug(
                        f"Deleted cache key '{key}' (age: {entry.age_seconds:.1f}s, "
                        f"access_count: {entry.access_count})"
                    )
                    return True
                
                return False
        
        except Exception as e:
            self._logger.error(f"Failed to delete cache key '{key}': {e}")
            self._record_circuit_failure()
            return False
    
    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern with enhanced pattern matching.
        
        Args:
            pattern: Pattern to match keys (supports wildcards *)
            
        Returns:
            Number of entries invalidated
        """
        try:
            import fnmatch
            
            invalidated = 0
            
            with self._cache_lock:
                keys_to_remove = []
                
                # Support multiple pattern types
                if '*' in pattern:
                    # Wildcard pattern
                    for key in self._cache.keys():
                        if fnmatch.fnmatch(key, pattern):
                            keys_to_remove.append(key)
                elif ':' in pattern:
                    # Namespace pattern (e.g., "namespace:*")
                    namespace = pattern.split(':')[0]
                    for key in self._cache.keys():
                        if key.startswith(f"{namespace}:"):
                            keys_to_remove.append(key)
                else:
                    # Exact match
                    if pattern in self._cache:
                        keys_to_remove.append(pattern)
                
                for key in keys_to_remove:
                    entry = self._cache.pop(key)
                    with self._metrics_lock:
                        self._metrics.size_bytes -= entry.size_bytes
                    invalidated += 1
                
                with self._metrics_lock:
                    self._metrics.invalidations += invalidated
                    self._metrics.entry_count = len(self._cache)
            
            self._logger.info(f"Invalidated {invalidated} cache entries matching pattern '{pattern}'")
            
            # Trigger invalidation callbacks
            self._trigger_invalidation_callbacks(pattern)
            
            return invalidated
        
        except Exception as e:
            self._logger.error(f"Failed to invalidate pattern '{pattern}': {e}")
            self._record_circuit_failure()
            return 0
    
    def clear(self) -> None:
        """Clear all cache entries with enhanced logging."""
        try:
            with self._cache_lock:
                entry_count = len(self._cache)
                total_size = self._metrics.size_bytes
                
                self._cache.clear()
                
                with self._metrics_lock:
                    self._metrics.size_bytes = 0
                    self._metrics.entry_count = 0
                    self._metrics.invalidations += entry_count
            
            self._logger.info(
                f"Cleared all {entry_count} cache entries "
                f"(freed {total_size / 1024 / 1024:.1f} MB)"
            )
        
        except Exception as e:
            self._logger.error(f"Failed to clear cache: {e}")
            self._record_circuit_failure()
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache performance metrics."""
        with self._metrics_lock:
            return {
                "hits": self._metrics.hits,
                "misses": self._metrics.misses,
                "hit_rate": self._metrics.hit_rate,
                "miss_rate": self._metrics.miss_rate,
                "sets": self._metrics.sets,
                "deletes": self._metrics.deletes,
                "invalidations": self._metrics.invalidations,
                "size_bytes": self._metrics.size_bytes,
                "size_mb": self._metrics.size_bytes / (1024 * 1024),
                "entry_count": self._metrics.entry_count,
                "max_size": self._max_size,
                "max_memory_mb": self._max_memory_mb,
                "evictions": self._metrics.evictions,
                "expired_removals": self._metrics.expired_removals,
                "memory_usage_percent": (self._metrics.size_bytes / (1024 * 1024)) / self._max_memory_mb * 100,
                "avg_entry_size": self._metrics.avg_entry_size,
                "memory_pressure_events": self._metrics.memory_pressure_events,
                "circuit_breaker_activations": self._metrics.circuit_breaker_activations,
                "circuit_breaker_open": self._is_circuit_open()
            }
    
    def register_invalidation_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """Register a callback for cache invalidation events."""
        if pattern not in self._invalidation_callbacks:
            self._invalidation_callbacks[pattern] = []
        self._invalidation_callbacks[pattern].append(callback)
        
        self._logger.debug(f"Registered invalidation callback for pattern '{pattern}'")
    
    def remove_invalidation_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """Remove invalidation callback."""
        if pattern in self._invalidation_callbacks:
            try:
                self._invalidation_callbacks[pattern].remove(callback)
                if not self._invalidation_callbacks[pattern]:
                    del self._invalidation_callbacks[pattern]
                self._logger.debug(f"Removed invalidation callback for pattern '{pattern}'")
            except ValueError:
                pass
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information including entry details."""
        with self._cache_lock:
            entries_info = []
            total_size = 0
            
            for key, entry in self._cache.items():
                entry_info = {
                    "key": key,
                    "age_seconds": entry.age_seconds,
                    "access_count": entry.access_count,
                    "size_bytes": entry.size_bytes,
                    "is_expired": entry.is_expired,
                    "ttl": entry.ttl,
                    "hit_rate": entry.hit_rate,
                    "metadata": entry.metadata
                }
                entries_info.append(entry_info)
                total_size += entry.size_bytes
            
            return {
                "total_entries": len(self._cache),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "entries": entries_info,
                "metrics": self.get_cache_metrics(),
                "config": {
                    "max_size": self._max_size,
                    "max_memory_mb": self._max_memory_mb,
                    "default_ttl": self._default_ttl,
                    "cleanup_interval": self._cleanup_interval
                }
            }
    
    # Private implementation methods
    
    def _ensure_cache_capacity(self, new_entry_size: int) -> None:
        """Ensure cache has capacity for new entry with enhanced eviction."""
        # Check memory limit with buffer
        memory_limit_bytes = self._max_memory_mb * 1024 * 1024
        while (self._metrics.size_bytes + new_entry_size) > memory_limit_bytes:
            if not self._evict_lru_entry():
                break
        
        # Check size limit
        while len(self._cache) >= self._max_size:
            if not self._evict_lru_entry():
                break
    
    def _evict_lru_entry(self) -> bool:
        """Evict least recently used entry with enhanced logging."""
        if not self._cache:
            return False
        
        # Get LRU entry (first in OrderedDict)
        key, entry = next(iter(self._cache.items()))
        
        self._logger.debug(
            f"Evicting LRU entry '{key}' (age: {entry.age_seconds:.1f}s, "
            f"access_count: {entry.access_count}, size: {entry.size_bytes} bytes)"
        )
        
        self._remove_entry(key, entry)
        
        with self._metrics_lock:
            self._metrics.evictions += 1
        
        return True
    
    def _remove_entry(self, key: str, entry: CacheEntry) -> None:
        """Remove entry from cache and update metrics."""
        self._cache.pop(key, None)
        with self._metrics_lock:
            self._metrics.size_bytes -= entry.size_bytes
            self._metrics.entry_count = len(self._cache)
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes with enhanced accuracy."""
        try:
            # For complex objects, use JSON serialization
            if isinstance(value, (dict, list, tuple)):
                return len(json.dumps(value, default=str).encode('utf-8'))
            # For strings
            elif isinstance(value, str):
                return len(value.encode('utf-8'))
            # For bytes
            elif isinstance(value, bytes):
                return len(value)
            # For other types, fallback to string representation
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            # Fallback to simple estimation
            return len(str(value).encode('utf-8'))
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self._metrics.size_bytes / (1024 * 1024)
    
    def _check_memory_pressure(self, new_entry_size: int) -> bool:
        """Check if adding new entry would cause memory pressure."""
        total_size = self._metrics.size_bytes + new_entry_size
        memory_limit = self._max_memory_mb * 1024 * 1024
        return total_size > (memory_limit * self._memory_pressure_threshold)
    
    def _handle_memory_pressure(self) -> None:
        """Handle memory pressure by aggressive cleanup."""
        self._logger.warning("Memory pressure detected, performing aggressive cleanup")
        
        with self._metrics_lock:
            self._metrics.memory_pressure_events += 1
        
        # Remove expired entries first
        self._cleanup_expired_entries_sync()
        
        # If still under pressure, evict based on access patterns
        target_size = self._max_memory_mb * 1024 * 1024 * 0.7  # Target 70% of max
        
        with self._cache_lock:
            # Sort by access frequency and age
            entries_to_evict = []
            for key, entry in self._cache.items():
                if self._metrics.size_bytes <= target_size:
                    break
                
                # Score based on access frequency and age
                score = entry.access_count / max(1, entry.age_seconds / 3600)  # access per hour
                entries_to_evict.append((score, key, entry))
            
            # Sort by score (ascending - remove least valuable first)
            entries_to_evict.sort(key=lambda x: x[0])
            
            # Remove entries until under target
            for _, key, entry in entries_to_evict:
                if self._metrics.size_bytes <= target_size:
                    break
                
                self._remove_entry(key, entry)
                with self._metrics_lock:
                    self._metrics.evictions += 1
    
    def _cleanup_expired_entries_sync(self) -> int:
        """Synchronous cleanup of expired entries."""
        expired_count = 0
        
        with self._cache_lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                if entry.is_expired:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self._cache.pop(key)
                with self._metrics_lock:
                    self._metrics.size_bytes -= entry.size_bytes
                    self._metrics.expired_removals += 1
                expired_count += 1
            
            if expired_count > 0:
                with self._metrics_lock:
                    self._metrics.entry_count = len(self._cache)
        
        return expired_count
    
    def _trigger_invalidation_callbacks(self, pattern: str) -> None:
        """Trigger invalidation callbacks for pattern."""
        import fnmatch
        
        for callback_pattern, callbacks in self._invalidation_callbacks.items():
            if fnmatch.fnmatch(pattern, callback_pattern):
                for callback in callbacks:
                    try:
                        callback(pattern)
                    except Exception as e:
                        self._logger.error(f"Invalidation callback failed: {e}")
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        now = time.time()
        
        # Clean old failures outside the window
        self._circuit_breaker_failures = [
            failure_time for failure_time in self._circuit_breaker_failures
            if now - failure_time <= self._circuit_breaker_window
        ]
        
        return len(self._circuit_breaker_failures) >= self._circuit_breaker_threshold
    
    def _record_circuit_failure(self) -> None:
        """Record a circuit breaker failure."""
        self._circuit_breaker_failures.append(time.time())
        
        if self._is_circuit_open():
            with self._metrics_lock:
                self._metrics.circuit_breaker_activations += 1
            self._logger.warning("Cache circuit breaker activated due to failures")
    
    async def _cleanup_expired_entries(self) -> None:
        """Background task to clean up expired entries."""
        while not self._stop_event.is_set():
            try:
                expired_count = self._cleanup_expired_entries_sync()
                
                if expired_count > 0:
                    self._logger.debug(f"Cleaned up {expired_count} expired cache entries")
                
                # Wait for next cleanup interval
                await asyncio.sleep(self._cleanup_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Cache cleanup task error: {e}")
                await asyncio.sleep(self._cleanup_interval)
    
    async def _collect_custom_metrics(self) -> None:
        """Collect custom metrics for the cache service."""
        try:
            # Update service metrics with cache data
            metrics = self.get_cache_metrics()
            self.update_metrics(
                cache_hits=metrics["hits"],
                cache_misses=metrics["misses"],
                cache_hit_rate=metrics["hit_rate"],
                cache_size_mb=metrics["size_mb"],
                cache_entries=metrics["entry_count"],
                cache_evictions=metrics["evictions"],
                cache_memory_pressure_events=metrics["memory_pressure_events"],
                cache_circuit_breaker_open=metrics["circuit_breaker_open"]
            )
        except Exception as e:
            self._logger.warning(f"Failed to collect cache metrics: {e}")


# Factory function for dependency injection
def create_enhanced_shared_prompt_cache(config: Optional[IConfigurationService] = None) -> EnhancedSharedPromptCache:
    """Factory function to create enhanced shared prompt cache."""
    return EnhancedSharedPromptCache(config)