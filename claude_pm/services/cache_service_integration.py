#!/usr/bin/env python3
"""
Cache Service Integration
=========================

Integration module for SharedPromptCache with Claude PM Framework service manager.
Provides service registration, health monitoring, and lifecycle management.

Features:
- Automatic service registration with framework
- Health monitoring integration
- Performance metrics collection
- Service discovery support
- Configuration management
- Graceful shutdown handling

Usage:
    from claude_pm.services.cache_service_integration import register_cache_service
    
    # Register with service manager
    service_manager = ServiceManager()
    cache_service = register_cache_service(service_manager)
    
    # Start all services
    await service_manager.start_all()
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.service_manager import ServiceManager
from ..core.base_service import BaseService
from .shared_prompt_cache import SharedPromptCache

logger = logging.getLogger(__name__)


class CacheServiceWrapper(BaseService):
    """
    Service wrapper for SharedPromptCache to integrate with framework service manager.
    
    Provides BaseService interface while maintaining singleton pattern for cache.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cache service wrapper."""
        super().__init__("shared_prompt_cache", config)
        self._cache_instance: Optional[SharedPromptCache] = None
    
    async def _initialize(self) -> None:
        """Initialize the cache service."""
        try:
            # Get singleton cache instance
            cache_config = {
                "max_size": self.get_config("max_size", 1000),
                "max_memory_mb": self.get_config("max_memory_mb", 100),
                "default_ttl": self.get_config("default_ttl", 1800),
                "cleanup_interval": self.get_config("cleanup_interval", 300),
                "enable_metrics": self.get_config("enable_metrics", True)
            }
            
            self._cache_instance = SharedPromptCache.get_instance(cache_config)
            
            # Start the cache service if not already running
            if not self._cache_instance.running:
                await self._cache_instance.start()
            
            self.logger.info("SharedPromptCache service wrapper initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache service: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup cache service resources."""
        try:
            if self._cache_instance and self._cache_instance.running:
                await self._cache_instance.stop()
            self.logger.info("SharedPromptCache service wrapper cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up cache service: {e}")
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform cache service health checks."""
        checks = {}
        
        try:
            if self._cache_instance:
                # Delegate to cache instance health check
                cache_health = await self._cache_instance.health_check()
                checks.update(cache_health.checks)
                
                # Additional wrapper-specific checks
                checks["cache_service_available"] = True
                checks["cache_service_running"] = self._cache_instance.running
            else:
                checks["cache_service_available"] = False
                checks["cache_service_running"] = False
                
        except Exception as e:
            self.logger.error(f"Cache service health check failed: {e}")
            checks["cache_service_error"] = True
            
        return checks
    
    async def _collect_custom_metrics(self) -> None:
        """Collect cache-specific metrics."""
        try:
            if self._cache_instance:
                cache_metrics = self._cache_instance.get_metrics()
                
                # Update service metrics with cache data
                self.update_metrics(
                    cache_hits=cache_metrics["hits"],
                    cache_misses=cache_metrics["misses"],
                    cache_hit_rate=cache_metrics["hit_rate"],
                    cache_size_mb=cache_metrics["size_mb"],
                    cache_entries=cache_metrics["entry_count"],
                    cache_evictions=cache_metrics["evictions"],
                    cache_memory_usage_percent=cache_metrics["memory_usage_percent"]
                )
                
        except Exception as e:
            self.logger.warning(f"Failed to collect cache metrics: {e}")
    
    def get_cache_instance(self) -> Optional[SharedPromptCache]:
        """Get the underlying cache instance."""
        return self._cache_instance
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get detailed cache metrics."""
        if self._cache_instance:
            return self._cache_instance.get_metrics()
        return {}
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        if self._cache_instance:
            return self._cache_instance.get_cache_info()
        return {}


def register_cache_service(
    service_manager: ServiceManager,
    config: Optional[Dict[str, Any]] = None,
    auto_start: bool = True,
    critical: bool = False
) -> CacheServiceWrapper:
    """
    Register SharedPromptCache with the service manager.
    
    Args:
        service_manager: ServiceManager instance to register with
        config: Optional cache configuration
        auto_start: Whether to start automatically with start_all()
        critical: Whether this is a critical service
        
    Returns:
        CacheServiceWrapper instance
    """
    # Create cache service wrapper
    cache_service = CacheServiceWrapper(config)
    
    # Register with service manager
    service_manager.register_service(
        service=cache_service,
        dependencies=[],  # No dependencies for cache service
        startup_order=10,  # Start early but after core services
        auto_start=auto_start,
        critical=critical
    )
    
    logger.info("SharedPromptCache registered with service manager")
    return cache_service


def get_cache_service_from_manager(service_manager: ServiceManager) -> Optional[SharedPromptCache]:
    """
    Get SharedPromptCache instance from service manager.
    
    Args:
        service_manager: ServiceManager instance
        
    Returns:
        SharedPromptCache instance if available, None otherwise
    """
    try:
        service_info = service_manager.get_service("shared_prompt_cache")
        if service_info and isinstance(service_info.service, CacheServiceWrapper):
            return service_info.service.get_cache_instance()
    except Exception as e:
        logger.warning(f"Failed to get cache service from manager: {e}")
    
    return None


def create_cache_service_config(
    max_size: int = 1000,
    max_memory_mb: int = 100,
    default_ttl: int = 1800,
    cleanup_interval: int = 300,
    enable_metrics: bool = True
) -> Dict[str, Any]:
    """
    Create cache service configuration.
    
    Args:
        max_size: Maximum number of cache entries
        max_memory_mb: Maximum memory usage in MB
        default_ttl: Default TTL in seconds
        cleanup_interval: Cleanup interval in seconds
        enable_metrics: Whether to enable metrics collection
        
    Returns:
        Configuration dictionary
    """
    return {
        "max_size": max_size,
        "max_memory_mb": max_memory_mb,
        "default_ttl": default_ttl,
        "cleanup_interval": cleanup_interval,
        "enable_metrics": enable_metrics
    }


async def initialize_cache_service_standalone(
    config: Optional[Dict[str, Any]] = None
) -> SharedPromptCache:
    """
    Initialize SharedPromptCache as standalone service (without service manager).
    
    Args:
        config: Optional cache configuration
        
    Returns:
        SharedPromptCache instance
    """
    cache = SharedPromptCache.get_instance(config)
    
    if not cache.running:
        await cache.start()
    
    logger.info("SharedPromptCache initialized as standalone service")
    return cache


# Performance monitoring helpers
def monitor_cache_performance(cache: SharedPromptCache, interval: int = 60) -> None:
    """
    Start background task to monitor cache performance.
    
    Args:
        cache: SharedPromptCache instance to monitor
        interval: Monitoring interval in seconds
    """
    async def performance_monitor():
        """Background task for performance monitoring."""
        while cache.running:
            try:
                metrics = cache.get_metrics()
                
                # Log performance metrics
                logger.info(f"Cache Performance: "
                          f"Hit Rate: {metrics['hit_rate']:.2%}, "
                          f"Entries: {metrics['entry_count']}, "
                          f"Memory: {metrics['size_mb']:.1f}MB")
                
                # Alert on low hit rate
                if metrics['hit_rate'] < 0.5 and metrics['hits'] + metrics['misses'] > 100:
                    logger.warning(f"Low cache hit rate: {metrics['hit_rate']:.2%}")
                
                # Alert on high memory usage
                if metrics['memory_usage_percent'] > 80:
                    logger.warning(f"High cache memory usage: {metrics['memory_usage_percent']:.1f}%")
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache performance monitoring error: {e}")
                await asyncio.sleep(interval)
    
    # Start monitoring task
    asyncio.create_task(performance_monitor())
    logger.info(f"Cache performance monitoring started (interval: {interval}s)")


if __name__ == "__main__":
    # Demo service integration
    async def demo():
        """Demonstrate cache service integration."""
        print("🚀 Cache Service Integration Demo")
        print("=" * 50)
        
        # Create service manager
        service_manager = ServiceManager()
        
        # Register cache service
        cache_config = create_cache_service_config(
            max_size=100,
            max_memory_mb=10,
            default_ttl=300
        )
        
        cache_service = register_cache_service(
            service_manager, 
            cache_config, 
            auto_start=True
        )
        
        try:
            # Start all services
            print("\n🏁 Starting services...")
            await service_manager.start_all()
            
            # Get cache instance
            cache = cache_service.get_cache_instance()
            if cache:
                print("✅ Cache service started successfully")
                
                # Test cache operations
                cache.set("test:key", {"data": "test_value"})
                result = cache.get("test:key")
                print(f"📝 Cache test: {result}")
                
                # Show metrics
                metrics = cache_service.get_cache_metrics()
                print(f"📊 Cache metrics: {metrics}")
                
                # Monitor performance briefly
                monitor_cache_performance(cache, interval=5)
                await asyncio.sleep(10)
            
        finally:
            # Stop all services
            print("\n🛑 Stopping services...")
            await service_manager.stop_all()
            print("✅ Demo completed")
    
    # Run demo
    asyncio.run(demo())