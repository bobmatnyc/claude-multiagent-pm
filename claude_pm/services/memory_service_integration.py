"""
Memory Service Integration for Claude PM Framework.

Provides integration between AsyncMemoryCollector and the service management
framework, including service registration, configuration, and lifecycle management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.service_manager import ServiceManager
from .async_memory_collector import AsyncMemoryCollector, MemoryCategory, MemoryPriority


class MemoryServiceIntegration:
    """
    Integration service for async memory collection.
    
    Handles service registration, configuration, and provides
    convenience methods for memory collection operations.
    """
    
    def __init__(self, service_manager: ServiceManager):
        """Initialize memory service integration."""
        self.service_manager = service_manager
        self.logger = logging.getLogger(__name__)
        self._collector: Optional[AsyncMemoryCollector] = None
    
    async def register_async_memory_collector(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncMemoryCollector:
        """
        Register AsyncMemoryCollector with the service manager.
        
        Args:
            config: Optional configuration for the collector
            
        Returns:
            Configured AsyncMemoryCollector instance
        """
        # Default configuration
        default_config = {
            "batch_size": 10,
            "batch_timeout": 30.0,
            "max_queue_size": 1000,
            "max_retries": 3,
            "retry_delay": 1.0,
            "operation_timeout": 15.0,
            "max_concurrent_ops": 20,
            "health_check_interval": 60,
            "cache": {
                "enabled": True,
                "max_size": 1000,
                "ttl_seconds": 300
            }
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        # Create collector instance
        collector = AsyncMemoryCollector(default_config)
        
        # Register with service manager
        self.service_manager.register_service(
            service=collector,
            dependencies=[],  # No dependencies for now
            startup_order=10,  # Start after core services
            auto_start=True,
            critical=False  # Not critical for framework operation
        )
        
        self._collector = collector
        self.logger.info("AsyncMemoryCollector registered with service manager")
        
        return collector
    
    async def get_collector(self) -> Optional[AsyncMemoryCollector]:
        """Get the registered async memory collector."""
        if self._collector:
            return self._collector
        
        # Try to get from service manager
        collector = self.service_manager.get_service("async_memory_collector")
        if isinstance(collector, AsyncMemoryCollector):
            self._collector = collector
            return collector
        
        return None
    
    async def collect_bug(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "high"
    ) -> Optional[str]:
        """
        Collect bug information asynchronously.
        
        Args:
            content: Bug description
            metadata: Additional bug metadata
            priority: Priority level
            
        Returns:
            Operation ID if successful, None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            self.logger.warning("AsyncMemoryCollector not available for bug collection")
            return None
        
        try:
            return await collector.collect_async(
                category="bug",
                content=content,
                metadata=metadata or {},
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to collect bug information: {e}")
            return None
    
    async def collect_feedback(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> Optional[str]:
        """
        Collect user feedback asynchronously.
        
        Args:
            content: Feedback content
            metadata: Additional feedback metadata
            priority: Priority level
            
        Returns:
            Operation ID if successful, None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            self.logger.warning("AsyncMemoryCollector not available for feedback collection")
            return None
        
        try:
            return await collector.collect_async(
                category="feedback",
                content=content,
                metadata=metadata or {},
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to collect feedback: {e}")
            return None
    
    async def collect_error(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "critical"
    ) -> Optional[str]:
        """
        Collect error information asynchronously.
        
        Args:
            content: Error description
            metadata: Additional error metadata
            priority: Priority level
            
        Returns:
            Operation ID if successful, None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            self.logger.warning("AsyncMemoryCollector not available for error collection")
            return None
        
        try:
            return await collector.collect_async(
                category="error",
                content=content,
                metadata=metadata or {},
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to collect error information: {e}")
            return None
    
    async def collect_performance_data(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> Optional[str]:
        """
        Collect performance data asynchronously.
        
        Args:
            content: Performance data description
            metadata: Additional performance metadata
            priority: Priority level
            
        Returns:
            Operation ID if successful, None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            self.logger.warning("AsyncMemoryCollector not available for performance data collection")
            return None
        
        try:
            return await collector.collect_async(
                category="performance",
                content=content,
                metadata=metadata or {},
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to collect performance data: {e}")
            return None
    
    async def collect_architecture_info(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> Optional[str]:
        """
        Collect architecture information asynchronously.
        
        Args:
            content: Architecture information
            metadata: Additional architecture metadata
            priority: Priority level
            
        Returns:
            Operation ID if successful, None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            self.logger.warning("AsyncMemoryCollector not available for architecture info collection")
            return None
        
        try:
            return await collector.collect_async(
                category="architecture",
                content=content,
                metadata=metadata or {},
                priority=priority
            )
        except Exception as e:
            self.logger.error(f"Failed to collect architecture information: {e}")
            return None
    
    async def get_collection_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get collection statistics from the async memory collector.
        
        Returns:
            Statistics dictionary or None if collector unavailable
        """
        collector = await self.get_collector()
        if not collector:
            return None
        
        try:
            stats = await collector.get_stats()
            return {
                "total_operations": stats.total_operations,
                "successful_operations": stats.successful_operations,
                "failed_operations": stats.failed_operations,
                "retried_operations": stats.retried_operations,
                "success_rate": stats.success_rate(),
                "average_latency": stats.average_latency,
                "queue_size": stats.queue_size,
                "batch_operations": stats.batch_operations,
                "cache_hits": stats.cache_hits,
                "cache_misses": stats.cache_misses
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return None
    
    async def flush_collector(self, timeout: float = 30.0) -> Optional[int]:
        """
        Flush the memory collector queue.
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            Number of operations processed or None if unavailable
        """
        collector = await self.get_collector()
        if not collector:
            return None
        
        try:
            return await collector.flush_queue(timeout)
        except Exception as e:
            self.logger.error(f"Failed to flush collector: {e}")
            return None


# Convenience functions for easy access
_integration_instance: Optional[MemoryServiceIntegration] = None


def get_memory_integration() -> Optional[MemoryServiceIntegration]:
    """Get the global memory service integration instance."""
    return _integration_instance


def set_memory_integration(integration: MemoryServiceIntegration) -> None:
    """Set the global memory service integration instance."""
    global _integration_instance
    _integration_instance = integration


async def quick_collect_bug(content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Quick bug collection using global integration."""
    integration = get_memory_integration()
    if integration:
        return await integration.collect_bug(content, metadata)
    return None


async def quick_collect_feedback(content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Quick feedback collection using global integration."""
    integration = get_memory_integration()
    if integration:
        return await integration.collect_feedback(content, metadata)
    return None


async def quick_collect_error(content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Quick error collection using global integration."""
    integration = get_memory_integration()
    if integration:
        return await integration.collect_error(content, metadata)
    return None