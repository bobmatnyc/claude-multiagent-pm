"""
Memory Backend Interface

This module defines the abstract base class for memory backends.
All memory backends must implement this interface to ensure consistency.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from .models import MemoryItem, MemoryQuery, MemoryCategory, HealthStatus, MemoryStatistics


class MemoryBackend(ABC):
    """
    Abstract base class for memory backends.

    This interface defines the contract that all memory backends must implement.
    It ensures consistency across different storage backends while allowing for
    backend-specific optimizations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory backend.

        Args:
            config: Backend-specific configuration options
        """
        self.config = config or {}
        self._initialized = False
        self._healthy = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the backend service.

        This method should set up any necessary connections, create databases,
        or perform other initialization tasks.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the backend is healthy and responsive.

        Returns:
            bool: True if backend is healthy, False otherwise
        """
        pass

    async def get_health_status(self) -> HealthStatus:
        """
        Get detailed health status information.

        Returns:
            HealthStatus: Detailed health information
        """
        import time

        start_time = time.time()

        try:
            is_healthy = await self.health_check()
            response_time_ms = (time.time() - start_time) * 1000

            return HealthStatus(
                backend_name=self.backend_name,
                is_healthy=is_healthy,
                response_time_ms=response_time_ms,
                features=self.get_features(),
            )
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthStatus(
                backend_name=self.backend_name,
                is_healthy=False,
                response_time_ms=response_time_ms,
                error_message=str(e),
                features=self.get_features(),
            )

    @abstractmethod
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add a memory item to the backend.

        Args:
            project_name: Name of the project
            content: Memory content
            category: Memory category
            tags: Optional tags for the memory
            metadata: Optional additional metadata

        Returns:
            Optional[str]: Memory ID if successful, None otherwise
        """
        pass

    @abstractmethod
    async def search_memories(self, project_name: str, query: MemoryQuery) -> List[MemoryItem]:
        """
        Search for memories matching the query.

        Args:
            project_name: Name of the project
            query: Search query parameters

        Returns:
            List[MemoryItem]: List of matching memories
        """
        pass

    @abstractmethod
    async def get_memory(self, project_name: str, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory by ID.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier

        Returns:
            Optional[MemoryItem]: Memory item if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_memory(
        self,
        project_name: str,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing memory.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier
            content: New content (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if update was successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete_memory(self, project_name: str, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            project_name: Name of the project
            memory_id: Memory identifier

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_project_memories(
        self, project_name: str, category: Optional[MemoryCategory] = None, limit: int = 100
    ) -> List[MemoryItem]:
        """
        Get all memories for a project.

        Args:
            project_name: Name of the project
            category: Optional category filter
            limit: Maximum number of memories to return

        Returns:
            List[MemoryItem]: List of memories
        """
        pass

    @abstractmethod
    async def get_memory_stats(self, project_name: str) -> Dict[str, Any]:
        """
        Get memory statistics for a project.

        Args:
            project_name: Name of the project

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        pass

    async def get_all_projects(self) -> List[str]:
        """
        Get list of all projects with memories.

        Returns:
            List[str]: List of project names
        """
        # Default implementation returns empty list
        # Backends should override this if they can efficiently list projects
        return []

    async def bulk_add_memories(
        self, project_name: str, memories: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Add multiple memories in a single operation.

        Args:
            project_name: Name of the project
            memories: List of memory data dictionaries

        Returns:
            List[Optional[str]]: List of memory IDs (None for failures)
        """
        # Default implementation adds memories one by one
        # Backends can override for more efficient bulk operations
        results = []
        for memory_data in memories:
            try:
                memory_id = await self.add_memory(
                    project_name,
                    memory_data.get("content", ""),
                    MemoryCategory.from_string(memory_data.get("category", "project")),
                    memory_data.get("tags"),
                    memory_data.get("metadata"),
                )
                results.append(memory_id)
            except Exception:
                results.append(None)

        return results

    async def bulk_delete_memories(self, project_name: str, memory_ids: List[str]) -> List[bool]:
        """
        Delete multiple memories in a single operation.

        Args:
            project_name: Name of the project
            memory_ids: List of memory IDs to delete

        Returns:
            List[bool]: List of deletion results
        """
        # Default implementation deletes memories one by one
        # Backends can override for more efficient bulk operations
        results = []
        for memory_id in memory_ids:
            try:
                result = await self.delete_memory(project_name, memory_id)
                results.append(result)
            except Exception:
                results.append(False)

        return results

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup resources used by the backend.

        This method should close connections, clean up temporary files,
        and perform other cleanup tasks.
        """
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """
        Get the name of the backend.

        Returns:
            str: Backend name
        """
        pass

    @property
    @abstractmethod
    def supports_similarity_search(self) -> bool:
        """
        Check if the backend supports similarity search.

        Returns:
            bool: True if similarity search is supported
        """
        pass

    def get_features(self) -> Dict[str, bool]:
        """
        Get supported features of the backend.

        Returns:
            Dict[str, bool]: Feature support mapping
        """
        return {
            "similarity_search": self.supports_similarity_search,
            "full_text_search": hasattr(self, "full_text_search"),
            "bulk_operations": hasattr(self, "bulk_add_memories"),
            "transactions": hasattr(self, "begin_transaction"),
            "backup": hasattr(self, "create_backup"),
            "restore": hasattr(self, "restore_backup"),
            "async_operations": True,  # All backends are async
            "project_listing": hasattr(self, "get_all_projects"),
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)

    def is_initialized(self) -> bool:
        """
        Check if the backend is initialized.

        Returns:
            bool: True if initialized
        """
        return self._initialized

    def is_healthy(self) -> bool:
        """
        Check if the backend is healthy (cached).

        Returns:
            bool: True if healthy
        """
        return self._healthy

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the backend."""
        return (
            f"{self.__class__.__name__}(name={self.backend_name}, initialized={self._initialized})"
        )
