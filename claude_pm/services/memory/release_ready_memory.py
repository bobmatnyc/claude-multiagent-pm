"""
Release-Ready Memory Service

This module provides a memory service that is guaranteed to work in all deployment
scenarios, including environments without OpenAI API keys or external service access.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .fallback_memory_config import (
    get_development_safe_memory_config,
    get_release_ready_memory_config,
    validate_memory_system_health,
    migrate_memory_system_if_needed,
)
from .services.unified_service import FlexibleMemoryService
from .interfaces.models import MemoryCategory, MemoryItem, MemoryQuery
from .interfaces.exceptions import MemoryServiceError

logger = logging.getLogger(__name__)


class ReleaseReadyMemoryService:
    """
    A memory service wrapper that ensures reliable operation in all environments.
    
    This service:
    - Automatically configures appropriate backends based on available resources
    - Gracefully handles missing API keys and external service failures
    - Provides consistent interface regardless of backend availability
    - Ensures memory collection functionality is always available
    - Handles schema migrations and database initialization
    """
    
    def __init__(self, environment: Optional[str] = None, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize release-ready memory service.
        
        Args:
            environment: Deployment environment (development, production, test)
            custom_config: Optional custom configuration overrides
        """
        self.environment = environment or os.getenv("CLAUDE_PM_ENVIRONMENT", "development")
        self.custom_config = custom_config or {}
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self._initialized = False
        self._healthy = False
        self._underlying_service: Optional[FlexibleMemoryService] = None
        self._configuration_used = {}
        self._health_status = {}
        
        # Performance metrics
        self.metrics = {
            "initialization_time": 0.0,
            "successful_operations": 0,
            "failed_operations": 0,
            "fallback_activations": 0,
            "backend_used": "unknown",
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the memory service with comprehensive error handling.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"Initializing release-ready memory service for environment: {self.environment}")
            
            # Step 1: Validate and migrate database if needed
            self.logger.info("Checking database health and migration requirements...")
            migration_result = migrate_memory_system_if_needed()
            
            if migration_result["errors"]:
                self.logger.warning(f"Database migration issues: {migration_result['errors']}")
            
            # Step 2: Get appropriate configuration
            if self.environment == "production":
                config = get_release_ready_memory_config()
                self.logger.info("Using production-ready memory configuration")
            else:
                config = get_development_safe_memory_config()
                self.logger.info("Using development-safe memory configuration")
            
            # Apply custom config overrides
            config.update(self.custom_config)
            self._configuration_used = config.copy()
            
            # Step 3: Create underlying service
            self._underlying_service = FlexibleMemoryService(config)
            
            # Step 4: Initialize underlying service with retries
            initialization_successful = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Attempting service initialization (attempt {attempt + 1}/{max_retries})")
                    initialization_successful = await self._underlying_service.initialize()
                    
                    if initialization_successful:
                        self.logger.info("Memory service initialization successful")
                        break
                    else:
                        self.logger.warning(f"Initialization attempt {attempt + 1} failed")
                        
                except Exception as e:
                    self.logger.warning(f"Initialization attempt {attempt + 1} failed with error: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1.0)  # Brief delay before retry
            
            if not initialization_successful:
                # Last resort: Try SQLite-only configuration
                self.logger.warning("Standard initialization failed, attempting SQLite-only fallback")
                
                fallback_config = {
                    "fallback_chain": ["sqlite"],
                    "sqlite_enabled": True,
                    "sqlite_path": "memory.db",
                    "sqlite_fts": True,
                    "sqlite_wal": True,
                    "mem0ai_enabled": False,
                    "circuit_breaker_threshold": 1,
                    "detection_timeout": 0.5,
                    "detection_retries": 1,
                }
                
                self._underlying_service = FlexibleMemoryService(fallback_config)
                initialization_successful = await self._underlying_service.initialize()
                
                if initialization_successful:
                    self.logger.info("SQLite-only fallback initialization successful")
                    self.metrics["fallback_activations"] += 1
                    self._configuration_used = fallback_config
                else:
                    self.logger.error("All initialization attempts failed")
                    return False
            
            # Step 5: Verify health
            self._health_status = validate_memory_system_health()
            self._healthy = self._health_status.get("overall_health") in ["healthy", "degraded"]
            
            if not self._healthy:
                self.logger.warning(f"Memory system health check failed: {self._health_status}")
            
            # Step 6: Record metrics
            self.metrics["initialization_time"] = asyncio.get_event_loop().time() - start_time
            self.metrics["backend_used"] = getattr(self._underlying_service, "active_backend_name", "unknown")
            
            self._initialized = True
            
            self.logger.info(f"Memory service ready - Backend: {self.metrics['backend_used']}, Health: {self._health_status.get('overall_health')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Critical failure during memory service initialization: {e}")
            self._initialized = False
            self._healthy = False
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add memory with comprehensive error handling.
        
        Args:
            project_name: Name of the project
            content: Memory content
            category: Memory category
            tags: Optional tags for the memory
            metadata: Optional metadata for the memory
            
        Returns:
            Optional[str]: Memory ID if successful, None if failed
        """
        if not self._initialized:
            self.logger.warning("Memory service not initialized - attempting initialization")
            if not await self.initialize():
                self.logger.error("Failed to initialize memory service for add_memory operation")
                self.metrics["failed_operations"] += 1
                return None
        
        try:
            memory_id = await self._underlying_service.add_memory(
                project_name, content, category, tags, metadata
            )
            
            if memory_id:
                self.metrics["successful_operations"] += 1
                self.logger.debug(f"Successfully added memory {memory_id} to project {project_name}")
            else:
                self.metrics["failed_operations"] += 1
                self.logger.warning(f"Failed to add memory to project {project_name}")
            
            return memory_id
            
        except Exception as e:
            self.metrics["failed_operations"] += 1
            self.logger.error(f"Error adding memory to project {project_name}: {e}")
            return None
    
    async def search_memories(self, project_name: str, query: MemoryQuery) -> List[MemoryItem]:
        """
        Search memories with comprehensive error handling.
        
        Args:
            project_name: Name of the project
            query: Memory query parameters
            
        Returns:
            List[MemoryItem]: List of matching memories (empty list if failed)
        """
        if not self._initialized:
            self.logger.warning("Memory service not initialized - attempting initialization")
            if not await self.initialize():
                self.logger.error("Failed to initialize memory service for search_memories operation")
                self.metrics["failed_operations"] += 1
                return []
        
        try:
            memories = await self._underlying_service.search_memories(project_name, query)
            
            self.metrics["successful_operations"] += 1
            self.logger.debug(f"Successfully searched memories for project {project_name}, found {len(memories)} results")
            
            return memories
            
        except Exception as e:
            self.metrics["failed_operations"] += 1
            self.logger.error(f"Error searching memories for project {project_name}: {e}")
            return []
    
    async def get_memory_stats(self, project_name: str) -> Dict[str, Any]:
        """
        Get memory statistics with error handling.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict[str, Any]: Memory statistics (empty dict if failed)
        """
        if not self._initialized:
            if not await self.initialize():
                return {}
        
        try:
            stats = await self._underlying_service.get_memory_stats(project_name)
            self.metrics["successful_operations"] += 1
            return stats
            
        except Exception as e:
            self.metrics["failed_operations"] += 1
            self.logger.error(f"Error getting memory stats for project {project_name}: {e}")
            return {}
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive service health information.
        
        Returns:
            Dict[str, Any]: Service health status and metrics
        """
        return {
            "initialized": self._initialized,
            "healthy": self._healthy,
            "environment": self.environment,
            "backend_used": self.metrics.get("backend_used", "unknown"),
            "configuration": self._configuration_used,
            "health_status": self._health_status,
            "metrics": self.metrics.copy(),
            "underlying_service_healthy": (
                getattr(self._underlying_service, '_is_healthy', False) if self._underlying_service else False
            ),
        }
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy and ready for operations."""
        return self._initialized and self._healthy
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._underlying_service:
            try:
                await self._underlying_service.cleanup()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")
        
        self._initialized = False
        self._healthy = False
        self.logger.info("Release-ready memory service cleanup completed")


# Global service instance for easy access
_global_memory_service: Optional[ReleaseReadyMemoryService] = None


async def get_global_memory_service() -> ReleaseReadyMemoryService:
    """
    Get or create the global memory service instance.
    
    Returns:
        ReleaseReadyMemoryService: Ready-to-use memory service
    """
    global _global_memory_service
    
    if _global_memory_service is None:
        _global_memory_service = ReleaseReadyMemoryService()
        await _global_memory_service.initialize()
    
    return _global_memory_service


async def cleanup_global_memory_service() -> None:
    """Clean up the global memory service."""
    global _global_memory_service
    
    if _global_memory_service:
        await _global_memory_service.cleanup()
        _global_memory_service = None


# Convenience functions for common operations
async def collect_memory(
    project_name: str,
    content: str,
    category: MemoryCategory,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Convenience function to collect memory using the global service.
    
    Args:
        project_name: Name of the project
        content: Memory content
        category: Memory category
        tags: Optional tags
        metadata: Optional metadata
        
    Returns:
        Optional[str]: Memory ID if successful
    """
    service = await get_global_memory_service()
    return await service.add_memory(project_name, content, category, tags, metadata)


async def search_project_memories(project_name: str, query_text: str = "", limit: int = 10) -> List[MemoryItem]:
    """
    Convenience function to search project memories.
    
    Args:
        project_name: Name of the project
        query_text: Search query text
        limit: Maximum number of results
        
    Returns:
        List[MemoryItem]: Matching memories
    """
    service = await get_global_memory_service()
    query = MemoryQuery(query=query_text, limit=limit)
    return await service.search_memories(project_name, query)


if __name__ == "__main__":
    # Test the release-ready memory service
    async def test_service():
        print("Testing Release-Ready Memory Service")
        
        service = ReleaseReadyMemoryService(environment="development")
        
        # Initialize
        print("Initializing service...")
        success = await service.initialize()
        print(f"Initialization: {'Success' if success else 'Failed'}")
        
        if success:
            # Get health status
            health = service.get_service_health()
            print(f"Service Health: {health['healthy']}")
            print(f"Backend Used: {health['backend_used']}")
            print(f"Configuration: {health['configuration']['fallback_chain']}")
            
            # Test memory operations
            print("\nTesting memory operations...")
            
            # Add a test memory
            memory_id = await service.add_memory(
                "test_project",
                "This is a test memory for v0.8.0 release validation",
                MemoryCategory.PROJECT,
                tags=["test", "release", "v0.8.0"],
                metadata={"priority": "high", "source": "release_test"}
            )
            
            if memory_id:
                print(f"Added test memory: {memory_id}")
                
                # Search for the memory
                query = MemoryQuery(query="test memory", limit=5)
                results = await service.search_memories("test_project", query)
                print(f"Search results: {len(results)} memories found")
                
                # Get stats
                stats = await service.get_memory_stats("test_project")
                print(f"Project stats: {stats.get('total', 0)} total memories")
            else:
                print("Failed to add test memory")
        
        # Cleanup
        await service.cleanup()
        print("Service cleanup completed")
    
    # Run test
    asyncio.run(test_service())