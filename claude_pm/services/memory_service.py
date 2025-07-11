"""
ClaudePMMemory - Core Memory Management Class for Claude PM Framework

This module provides the ClaudePMMemory class, the primary interface between
Claude PM Framework and the mem0AI service for memory-augmented project management.

Features:
- Project-specific memory spaces
- Categorized memory storage (Project, Pattern, Team, Error)
- Async/sync method support
- Connection pooling and retry logic
- Comprehensive error handling and logging
- Integration with Claude PM Framework schemas
"""

import asyncio
import aiohttp
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

# Import from the existing framework
from ..core.logging_config import get_logger
from ..core.base_service import BaseService
from ..core.connection_manager import get_connection_manager, ConnectionConfig

logger = get_logger(__name__)


class MemoryCategory(str, Enum):
    """Memory categories for Claude PM Framework."""

    PROJECT = "project"
    PATTERN = "pattern"
    TEAM = "team"
    ERROR = "error"


@dataclass
class ClaudePMConfig:
    """Configuration for ClaudePMMemory class."""

    host: str = "localhost"
    port: int = 8002
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 10
    enable_logging: bool = True
    api_key: Optional[str] = None

    # Advanced configuration
    batch_size: int = 100
    cache_ttl: int = 300  # 5 minutes
    max_memory_size: int = 1000  # MB
    compression_enabled: bool = True


@dataclass
class MemoryResponse:
    """Response object for memory operations."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    memory_id: Optional[str] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryItem:
    """Represents a memory item in the mem0AI system."""

    id: str
    content: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class MemoryQuery:
    """Query parameters for memory search."""

    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    include_metadata: bool = True


class ClaudePMMemory:
    """
    Core Memory Management Class for Claude PM Framework

    This class serves as the primary interface between Claude PM Framework
    and the mem0AI service, providing comprehensive memory management
    capabilities for project management workflows.

    Key Features:
    - Project-specific memory spaces with isolation
    - Categorized memory storage (Project, Pattern, Team, Error)
    - Both async and sync method support
    - Connection pooling for performance
    - Comprehensive error handling and retry logic
    - Integration with existing Claude PM schemas
    - Monitoring and logging capabilities
    """

    def __init__(self, config: Optional[ClaudePMConfig] = None):
        """
        Initialize ClaudePMMemory with configuration.

        Args:
            config: Configuration object. If None, uses defaults.
        """
        self.config = config or ClaudePMConfig()
        self.base_url = f"http://{self.config.host}:{self.config.port}"

        # Connection management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connection_pool: Optional[aiohttp.TCPConnector] = None
        self._connected = False
        self._last_health_check = 0

        # Memory categories with enhanced descriptions
        self.categories = {
            MemoryCategory.PROJECT: {
                "description": "Architectural decisions, requirements, milestones, and project-specific knowledge",
                "fields": ["decision_type", "reasoning", "alternatives", "impact"],
                "tags": ["architecture", "decisions", "planning"],
            },
            MemoryCategory.PATTERN: {
                "description": "Successful solutions, code patterns, design patterns, and reusable approaches",
                "fields": ["pattern_type", "use_cases", "implementation", "benefits"],
                "tags": ["patterns", "solutions", "reusable", "best-practices"],
            },
            MemoryCategory.TEAM: {
                "description": "Coding standards, team preferences, workflows, and organizational knowledge",
                "fields": ["standard_type", "enforcement_level", "examples", "tools"],
                "tags": ["standards", "team", "workflow", "conventions"],
            },
            MemoryCategory.ERROR: {
                "description": "Bug patterns, error solutions, debugging knowledge, and lessons learned",
                "fields": ["error_type", "symptoms", "root_cause", "solution", "prevention"],
                "tags": ["bugs", "debugging", "solutions", "prevention"],
            },
        }

        # Statistics tracking
        self.stats = {
            "operations_count": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_response_time": 0.0,
            "memory_spaces_created": 0,
            "memories_stored": 0,
            "memories_retrieved": 0,
        }

        # Initialize logging
        if self.config.enable_logging:
            self._setup_logging()

    def _setup_logging(self):
        """Setup enhanced logging for memory operations."""
        self.operation_logger = logging.getLogger(f"{__name__}.operations")
        self.performance_logger = logging.getLogger(f"{__name__}.performance")

        # Add handlers if not already present
        if not self.operation_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - ClaudePMMemory - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.operation_logger.addHandler(handler)
            self.operation_logger.setLevel(logging.INFO)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    # Connection Management

    async def connect(self) -> bool:
        """
        Connect to mem0AI service with connection pooling.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Check if already connected
            if self._session and not self._session.closed and self._connected:
                return True

            # Get connection manager
            conn_manager = await get_connection_manager()

            # Create connection config
            conn_config = ConnectionConfig(
                pool_size=self.config.connection_pool_size,
                timeout=self.config.timeout,
                connect_timeout=10,
            )

            # Setup headers
            headers = {
                "User-Agent": "ClaudePM-Memory-Client/3.0.0",
                "Content-Type": "application/json",
            }

            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            # Get managed session
            self._session = await conn_manager.get_session(
                service_name=f"memory_service_{id(self)}", config=conn_config, headers=headers
            )

            # Test connection with health check
            if await self._health_check():
                self._connected = True
                self._last_health_check = time.time()
                logger.info(f"ClaudePMMemory connected to mem0AI service at {self.base_url}")
                return True
            else:
                logger.error("mem0AI service health check failed during connection")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Failed to connect to mem0AI service: {e}")
            await self.disconnect()
            return False

    async def disconnect(self) -> None:
        """Disconnect from mem0AI service and cleanup resources."""
        try:
            if self._session:
                # Properly close the aiohttp session
                if not self._session.closed:
                    await self._session.close()
                    logger.debug("Closed aiohttp session")

                # Clear session reference
                self._session = None

            if self._connection_pool:
                # Close connection pool if it exists
                if not self._connection_pool.closed:
                    await self._connection_pool.close()
                    logger.debug("Closed connection pool")

                self._connection_pool = None

            self._connected = False
            logger.info("Disconnected from mem0AI service with proper cleanup")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            # Ensure resources are always cleared
            if self._session and not self._session.closed:
                try:
                    await self._session.close()
                except Exception as cleanup_error:
                    logger.warning(f"Final session cleanup error: {cleanup_error}")

            if self._connection_pool and not self._connection_pool.closed:
                try:
                    await self._connection_pool.close()
                except Exception as cleanup_error:
                    logger.warning(f"Final connection pool cleanup error: {cleanup_error}")

            self._session = None
            self._connection_pool = None
            self._connected = False

    async def _health_check(self) -> bool:
        """
        Check if mem0AI service is healthy.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            if not self._session:
                return False

            async with self._session.get(f"{self.base_url}/health") as response:
                is_healthy = response.status == 200

                if is_healthy:
                    self._last_health_check = time.time()

                return is_healthy

        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def is_connected(self) -> bool:
        """
        Check if connected to mem0AI service.

        Returns:
            bool: True if connected and healthy, False otherwise
        """
        if not self._connected or not self._session:
            return False

        # Check if health check is recent (within last 5 minutes)
        if time.time() - self._last_health_check > 300:
            # Health check is stale, should re-check
            return False

        return True

    async def ensure_connection(self) -> bool:
        """
        Ensure connection is active, reconnect if necessary.

        Returns:
            bool: True if connection is active, False otherwise
        """
        if not self.is_connected():
            logger.info("Connection lost, attempting to reconnect...")
            return await self.connect()
        return True

    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add a memory to the project memory space.

        Args:
            project_name: Project identifier
            content: Memory content
            category: Memory category (from MEMORY_CATEGORIES)
            tags: Optional tags for the memory
            metadata: Optional additional metadata

        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            if category not in self.MEMORY_CATEGORIES:
                self.logger.warning(f"Unknown memory category: {category}")

            if not self._session:
                self.logger.error("Memory service not initialized")
                return None

            # Prepare memory data
            memory_data = {
                "content": content,
                "space_name": project_name,
                "metadata": {
                    "category": category,
                    "tags": tags or [],
                    "project": project_name,
                    "created_at": datetime.now().isoformat(),
                    **(metadata or {}),
                },
            }

            async with self._session.post(
                f"{self.base_url}/memories", json=memory_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    memory_id = result.get("id")

                    # Invalidate cache for this project
                    self._invalidate_cache(project_name)

                    self.logger.info(f"Added memory to {project_name}: {memory_id}")
                    return memory_id
                else:
                    self.logger.error(f"Failed to add memory: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error adding memory to {project_name}: {e}")
            return None

    async def search_memories(self, project_name: str, query: MemoryQuery) -> List[MemoryItem]:
        """
        Search memories in a project space.

        Args:
            project_name: Project identifier
            query: Memory query parameters

        Returns:
            List of matching memory items
        """
        try:
            # Check cache first
            cache_key = f"{project_name}:{query.query}:{query.category}:{query.limit}"
            if self._is_cache_valid(cache_key):
                return self._memory_cache[cache_key]

            if not self._session:
                self.logger.error("Memory service not initialized")
                return []

            # Prepare search parameters
            search_params = {
                "query": query.query,
                "space_name": project_name,
                "limit": query.limit,
                "include_metadata": query.include_metadata,
            }

            if query.category:
                search_params["category"] = query.category

            if query.tags:
                search_params["tags"] = query.tags

            async with self._session.get(
                f"{self.base_url}/memories/search", params=search_params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    memories = []

                    for memory_data in result.get("memories", []):
                        memory = MemoryItem(
                            id=memory_data.get("id", ""),
                            content=memory_data.get("content", ""),
                            category=memory_data.get("metadata", {}).get("category", "unknown"),
                            tags=memory_data.get("metadata", {}).get("tags", []),
                            metadata=memory_data.get("metadata", {}),
                            created_at=memory_data.get("created_at", ""),
                            updated_at=memory_data.get("updated_at", ""),
                        )
                        memories.append(memory)

                    # Cache the results
                    self._cache_memories(cache_key, memories)

                    self.logger.debug(f"Found {len(memories)} memories for query in {project_name}")
                    return memories
                else:
                    self.logger.error(f"Memory search failed: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error searching memories in {project_name}: {e}")
            return []

    async def get_memory(self, project_name: str, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            if not self._session:
                return None

            async with self._session.get(f"{self.base_url}/memories/{memory_id}") as response:
                if response.status == 200:
                    memory_data = await response.json()

                    return MemoryItem(
                        id=memory_data.get("id", ""),
                        content=memory_data.get("content", ""),
                        category=memory_data.get("metadata", {}).get("category", "unknown"),
                        tags=memory_data.get("metadata", {}).get("tags", []),
                        metadata=memory_data.get("metadata", {}),
                        created_at=memory_data.get("created_at", ""),
                        updated_at=memory_data.get("updated_at", ""),
                    )
                else:
                    self.logger.error(f"Failed to get memory {memory_id}: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting memory {memory_id}: {e}")
            return None

    async def update_memory(
        self,
        project_name: str,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing memory."""
        try:
            if not self._session:
                return False

            update_data = {"id": memory_id}

            if content is not None:
                update_data["content"] = content

            if tags is not None or metadata is not None:
                current_metadata = {}
                if metadata:
                    current_metadata.update(metadata)
                if tags is not None:
                    current_metadata["tags"] = tags

                update_data["metadata"] = current_metadata

            async with self._session.put(
                f"{self.base_url}/memories/{memory_id}", json=update_data
            ) as response:
                if response.status == 200:
                    # Invalidate cache
                    self._invalidate_cache(project_name)
                    self.logger.info(f"Updated memory {memory_id} in {project_name}")
                    return True
                else:
                    self.logger.error(f"Failed to update memory {memory_id}: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    async def delete_memory(self, project_name: str, memory_id: str) -> bool:
        """Delete a memory."""
        try:
            if not self._session:
                return False

            async with self._session.delete(f"{self.base_url}/memories/{memory_id}") as response:
                if response.status in [200, 204]:
                    # Invalidate cache
                    self._invalidate_cache(project_name)
                    self.logger.info(f"Deleted memory {memory_id} from {project_name}")
                    return True
                else:
                    self.logger.error(f"Failed to delete memory {memory_id}: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    async def get_project_memories(
        self, project_name: str, category: Optional[str] = None, limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project, optionally filtered by category."""
        query = MemoryQuery(query="", category=category, limit=limit)  # Empty query to get all

        return await self.search_memories(project_name, query)

    async def get_memory_stats(self, project_name: str) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        try:
            stats = {"total": 0, "categories": {}}

            # Get all memories
            memories = await self.get_project_memories(project_name, limit=1000)
            stats["total"] = len(memories)

            # Count by category
            for memory in memories:
                category = memory.category
                if category not in stats["categories"]:
                    stats["categories"][category] = 0
                stats["categories"][category] += 1

            return stats

        except Exception as e:
            self.logger.error(f"Error getting memory stats for {project_name}: {e}")
            return {"total": 0, "categories": {}, "error": str(e)}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid."""
        if cache_key not in self._memory_cache:
            return False

        expiry = self._cache_expiry.get(cache_key)
        if not expiry:
            return False

        return datetime.now() < expiry

    def _cache_memories(self, cache_key: str, memories: List[MemoryItem]) -> None:
        """Cache memory search results."""
        self._memory_cache[cache_key] = memories
        self._cache_expiry[cache_key] = datetime.now().timestamp() + self._cache_ttl

    def _invalidate_cache(self, project_name: str) -> None:
        """Invalidate cache entries for a project."""
        keys_to_remove = [
            key for key in self._memory_cache.keys() if key.startswith(f"{project_name}:")
        ]
        for key in keys_to_remove:
            self._memory_cache.pop(key, None)
            self._cache_expiry.pop(key, None)

    async def _auto_sync_task(self) -> None:
        """Background task for automatic memory synchronization."""
        while not self._stop_event.is_set():
            try:
                # Perform any necessary sync operations
                await self._sync_memories()

                await asyncio.sleep(self.auto_sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-sync task error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _sync_memories(self) -> None:
        """Synchronize memories (placeholder for future implementation)."""
        # This could include:
        # - Backing up memories to local storage
        # - Syncing with external systems
        # - Cleaning up old cache entries
        pass

    # Convenience methods for specific memory types

    async def add_project_decision(
        self, project_name: str, decision: str, context: str, tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Add a project decision memory."""
        content = f"Decision: {decision}\nContext: {context}"
        return await self.add_memory(
            project_name,
            content,
            "project",
            tags or ["decision"],
            {"decision": decision, "context": context},
        )

    async def add_code_pattern(
        self,
        project_name: str,
        pattern_name: str,
        code: str,
        description: str,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Add a code pattern memory."""
        content = f"Pattern: {pattern_name}\nDescription: {description}\nCode:\n{code}"
        return await self.add_memory(
            project_name,
            content,
            "pattern",
            tags or ["pattern", "code"],
            {"pattern_name": pattern_name, "code": code, "description": description},
        )

    async def add_error_solution(
        self, project_name: str, error: str, solution: str, tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Add an error solution memory."""
        content = f"Error: {error}\nSolution: {solution}"
        return await self.add_memory(
            project_name,
            content,
            "error",
            tags or ["error", "solution"],
            {"error": error, "solution": solution},
        )


# Create a simple service wrapper class for compatibility with the service manager
class MemoryService(BaseService):
    """
    Service wrapper for ClaudePMMemory to integrate with Claude PM Framework service manager.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize memory service."""
        super().__init__("memory_service", config)

        # Initialize the core memory client
        mem_config = ClaudePMConfig(
            host=self.get_config("mem0ai_host", "localhost"),
            port=self.get_config("mem0ai_port", 8002),
            timeout=self.get_config("mem0ai_timeout", 30),
        )
        self.client = ClaudePMMemory(mem_config)

    async def _initialize(self) -> None:
        """Initialize the memory service."""
        self.logger.info("Initializing Memory Service...")
        await self.client.connect()
        self.logger.info("Memory Service initialized")

    async def _cleanup(self) -> None:
        """Cleanup memory service."""
        self.logger.info("Cleaning up Memory Service...")
        await self.client.disconnect()
        self.logger.info("Memory Service cleanup completed")

    async def _health_check(self) -> Dict[str, bool]:
        """Perform memory service health checks."""
        checks = {}

        try:
            # Check if client is initialized
            checks["client_initialized"] = self.client._session is not None

            # Check connection to mem0AI service
            checks["mem0ai_connection"] = self.client.is_connected()

        except Exception as e:
            self.logger.error(f"Memory service health check failed: {e}")
            checks["health_check_error"] = False

        return checks


def get_memory_service(config: Optional[Dict] = None) -> MemoryService:
    """Factory function to create a MemoryService instance."""
    return MemoryService(config)
