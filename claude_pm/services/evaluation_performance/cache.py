"""
Advanced caching system for evaluation performance.

Provides LRU, TTL, and hybrid caching strategies with performance monitoring
and automatic optimization.
"""

import asyncio
import logging
import sys
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..evaluation_performance.metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


class CacheStrategy:
    """Cache strategies."""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    HYBRID = "hybrid"  # Combined LRU + TTL


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
        strategy: str = CacheStrategy.HYBRID,
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
        
        logger.info(f"Advanced cache initialized: strategy={strategy}, max_size={max_size}")
    
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
            elif hasattr(value, 'to_dict'):
                # Handle EvaluationResult objects
                size = len(getattr(value, 'response_text', '').encode('utf-8'))
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
                "strategy": self.strategy,
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