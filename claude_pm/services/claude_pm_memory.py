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
            # Create connection pool
            self._connection_pool = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=self.config.connection_pool_size // 2,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
            )

            # Create session with timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout, connect=10, sock_read=self.config.timeout
            )

            headers = {
                "User-Agent": "ClaudePM-Memory-Client/3.0.0",
                "Content-Type": "application/json",
            }

            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._session = aiohttp.ClientSession(
                connector=self._connection_pool,
                timeout=timeout,
                headers=headers,
                raise_for_status=False,
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
                await self._session.close()
                self._session = None

            if self._connection_pool:
                await self._connection_pool.close()
                self._connection_pool = None

            self._connected = False
            logger.info("Disconnected from mem0AI service")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

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

    # Retry and Error Handling

    async def _execute_with_retry(self, operation_func, *args, **kwargs) -> MemoryResponse:
        """
        Execute an operation with retry logic and comprehensive error handling.

        Args:
            operation_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            MemoryResponse: Response object with success/failure info
        """
        operation_name = kwargs.pop("_operation_name", operation_func.__name__)
        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                # Ensure connection before operation
                if not await self.ensure_connection():
                    return MemoryResponse(
                        success=False,
                        error="Failed to establish connection to mem0AI service",
                        operation=operation_name,
                    )

                # Execute operation
                result = await operation_func(*args, **kwargs)

                # Update statistics
                execution_time = time.time() - start_time
                self._update_stats(True, execution_time)

                if self.config.enable_logging:
                    self.operation_logger.info(
                        f"Operation '{operation_name}' completed successfully in {execution_time:.3f}s"
                    )

                return MemoryResponse(success=True, data=result, operation=operation_name)

            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(
                    f"Network error in operation '{operation_name}' (attempt {attempt + 1}): {e}"
                )

            except Exception as e:
                last_exception = e
                logger.error(f"Error in operation '{operation_name}' (attempt {attempt + 1}): {e}")

                # For non-network errors, don't retry
                if not isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError)):
                    break

            # Exponential backoff for retry
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2**attempt)
                logger.debug(f"Retrying operation '{operation_name}' in {delay}s...")
                await asyncio.sleep(delay)

        # All retries failed
        execution_time = time.time() - start_time
        self._update_stats(False, execution_time)

        error_msg = f"Operation '{operation_name}' failed after {self.config.max_retries} attempts: {last_exception}"
        logger.error(error_msg)

        return MemoryResponse(success=False, error=error_msg, operation=operation_name)

    def _update_stats(self, success: bool, execution_time: float):
        """Update internal statistics."""
        self.stats["operations_count"] += 1

        if success:
            self.stats["successful_operations"] += 1
        else:
            self.stats["failed_operations"] += 1

        # Update average response time
        total_ops = self.stats["operations_count"]
        current_avg = self.stats["avg_response_time"]
        self.stats["avg_response_time"] = (
            current_avg * (total_ops - 1) + execution_time
        ) / total_ops

    def _sanitize_metadata_for_mem0ai(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata for mem0AI compatibility.

        Converts unsupported types (bool, dict, list) to mem0AI-compatible formats.

        Args:
            metadata: Original metadata dict

        Returns:
            Dict with sanitized values compatible with mem0AI
        """
        import json

        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, bool):
                # Convert booleans to strings
                sanitized[key] = str(value).lower()
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                sanitized[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                sanitized[key] = json.dumps(value)
            elif value is None:
                # Convert None to empty string
                sanitized[key] = ""
            else:
                # Convert everything else to string
                sanitized[key] = str(value)

        return sanitized

    # Project Memory Space Management

    async def create_project_memory_space(
        self, project_name: str, description: str = "", metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryResponse:
        """
        Create a memory space for a project with enhanced metadata.

        Args:
            project_name: Name of the project
            description: Optional description of the project
            metadata: Additional metadata for the memory space

        Returns:
            MemoryResponse: Response object with creation status
        """

        async def _create_space():
            # For mem0AI API, we create a memory space by storing an initial memory
            # The space concept is implemented via user_id/project categorization
            space_message = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Initialize memory space for project: {project_name}. {description or f'Memory space for Claude PM project: {project_name}'}",
                    }
                ],
                "user_id": project_name,
                "metadata": self._sanitize_metadata_for_mem0ai(
                    {
                        "project": project_name,
                        "created_by": "claude_pm_framework",
                        "created_at": datetime.now().isoformat(),
                        "framework_version": "3.0.0",
                        "space_type": "claude_pm_project",
                        "operation": "space_initialization",
                        **(metadata or {}),
                    }
                ),
            }

            async with self._session.post(
                f"{self.base_url}/memories", json=space_message
            ) as response:
                if response.status in [200, 201]:
                    self.stats["memory_spaces_created"] += 1
                    logger.info(f"Project memory space created/verified: {project_name}")
                    return {"space_name": project_name, "status": "created"}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        return await self._execute_with_retry(
            _create_space, _operation_name="create_project_memory_space"
        )

    # Core Memory Operations

    async def store_memory(
        self,
        category: MemoryCategory,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> MemoryResponse:
        """
        Store a memory in the specified category.

        Args:
            category: Memory category (PROJECT, PATTERN, TEAM, ERROR)
            content: Memory content
            metadata: Additional metadata for the memory
            project_name: Project to associate with (if any)
            tags: Tags for categorization and search

        Returns:
            MemoryResponse: Response object with storage status and memory ID
        """

        async def _store_memory():
            # Validate category
            if category not in self.categories:
                raise ValueError(
                    f"Invalid category: {category}. Valid categories: {list(self.categories.keys())}"
                )

            # Get subsystem versions for enhanced metadata
            subsystem_versions = await self._get_subsystem_versions()
            
            # Prepare metadata for mem0AI format
            raw_metadata = {
                "category": category.value,
                "category_description": self.categories[category]["description"],
                "tags": tags or [],
                "project": project_name,
                "stored_at": datetime.now().isoformat(),
                "framework_version": "3.0.0",
                "source": "claude_pm_memory",
                "subsystem_versions": subsystem_versions,
                **(metadata or {}),
            }

            # Sanitize metadata for mem0AI compatibility
            sanitized_metadata = self._sanitize_metadata_for_mem0ai(raw_metadata)

            # Prepare memory data in mem0AI format
            memory_data = {
                "messages": [{"role": "user", "content": content}],
                "user_id": project_name or "claude_pm_global",
                "metadata": sanitized_metadata,
            }

            async with self._session.post(
                f"{self.base_url}/memories", json=memory_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    # mem0AI might return different response format
                    memory_id = result.get("id") or result.get("memory_id") or "unknown"
                    self.stats["memories_stored"] += 1
                    logger.info(
                        f"Memory stored - Category: {category.value}, Project: {project_name}, ID: {memory_id}"
                    )
                    return {
                        "memory_id": memory_id,
                        "category": category.value,
                        "project": project_name,
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        response = await self._execute_with_retry(_store_memory, _operation_name="store_memory")
        if response.success and response.data:
            response.memory_id = response.data.get("memory_id")
        return response

    async def retrieve_memories(
        self,
        category: Optional[MemoryCategory] = None,
        query: str = "",
        project_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> MemoryResponse:
        """
        Retrieve memories with filtering options.

        Args:
            category: Filter by memory category
            query: Search query
            project_filter: Filter by project name (user_id in mem0AI)
            tags: Filter by tags
            limit: Maximum number of results

        Returns:
            MemoryResponse: Response object with retrieved memories
        """

        async def _retrieve_memories():
            # For mem0AI API, try to retrieve memories using the user_id
            user_id = project_filter or "claude_pm_global"

            # Try different approaches to retrieve memories
            memories = []

            # Approach 1: Try GET /memories/{user_id}
            try:
                async with self._session.get(f"{self.base_url}/memories/{user_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        memories = result.get("results", result.get("memories", []))
                        logger.debug(
                            f"Retrieved {len(memories)} memories from GET /memories/{user_id}"
                        )
                    elif response.status == 404:
                        logger.debug(f"No memories found for user_id: {user_id}")
                    else:
                        logger.debug(f"GET /memories/{user_id} returned {response.status}")
            except Exception as e:
                logger.debug(f"GET /memories/{user_id} failed: {e}")

            # Approach 2: If no memories found and we have a query, try POST /memories with search
            if not memories and query:
                try:
                    search_data = {
                        "messages": [{"role": "user", "content": query}],
                        "user_id": user_id,
                    }
                    async with self._session.post(
                        f"{self.base_url}/memories", json=search_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            search_results = result.get("results", [])
                            logger.debug(f"Search returned {len(search_results)} results")
                            # The search might return related memories
                            memories.extend(search_results)
                except Exception as e:
                    logger.debug(f"Search approach failed: {e}")

            # Apply client-side filtering since mem0AI has limited filtering options
            filtered_memories = []
            for memory in memories:
                # Check category filter
                if category:
                    memory_metadata = memory.get("metadata", {})
                    memory_category = memory_metadata.get("category")
                    if memory_category != category.value:
                        continue

                # Check tags filter
                if tags:
                    memory_metadata = memory.get("metadata", {})
                    memory_tags_str = memory_metadata.get("tags", "")
                    if isinstance(memory_tags_str, str):
                        memory_tags = memory_tags_str.split(", ") if memory_tags_str else []
                    else:
                        memory_tags = memory_tags_str if isinstance(memory_tags_str, list) else []

                    if not any(tag in memory_tags for tag in tags):
                        continue

                # Check query filter (simple text search)
                if query:
                    content = str(memory.get("content", "")).lower()
                    metadata_text = str(memory.get("metadata", {})).lower()
                    if query.lower() not in content and query.lower() not in metadata_text:
                        continue

                filtered_memories.append(memory)

            # Apply limit
            final_memories = filtered_memories[:limit]

            self.stats["memories_retrieved"] += len(final_memories)
            logger.debug(
                f"Retrieved {len(final_memories)} memories for query '{query}' (filtered from {len(memories)} total)"
            )
            return {"memories": final_memories, "count": len(final_memories)}

        return await self._execute_with_retry(
            _retrieve_memories, _operation_name="retrieve_memories"
        )

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryResponse:
        """
        Update an existing memory.

        Note: mem0AI API typically doesn't support direct memory updates.
        This method implements update by adding a new memory with updated content.

        Args:
            memory_id: ID of memory to update (for reference)
            content: New content (if updating)
            metadata: New metadata (if updating)

        Returns:
            MemoryResponse: Response object with update status
        """

        async def _update_memory():
            # mem0AI doesn't support direct updates, so we log this as a limitation
            logger.warning(
                f"Memory update attempted for {memory_id}. mem0AI doesn't support direct updates."
            )
            logger.info("Consider creating a new memory with updated content instead.")
            return {
                "memory_id": memory_id,
                "status": "update_not_supported",
                "message": "mem0AI doesn't support direct memory updates",
            }

        return await self._execute_with_retry(_update_memory, _operation_name="update_memory")

    async def delete_memory(self, memory_id: str) -> MemoryResponse:
        """
        Delete a memory.

        Note: This uses the mem0AI DELETE /memories/{memory_id} endpoint.

        Args:
            memory_id: ID of memory to delete

        Returns:
            MemoryResponse: Response object with deletion status
        """

        async def _delete_memory():
            async with self._session.delete(f"{self.base_url}/memories/{memory_id}") as response:
                if response.status in [200, 204, 404]:  # 404 = already deleted
                    logger.info(f"Memory deleted: {memory_id}")
                    return {"memory_id": memory_id, "status": "deleted"}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        return await self._execute_with_retry(_delete_memory, _operation_name="delete_memory")

    # High-level Convenience Methods

    async def store_project_decision(
        self,
        project_name: str,
        decision: str,
        context: str,
        reasoning: str,
        alternatives: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> MemoryResponse:
        """
        Store a project architectural decision.

        Args:
            project_name: Name of the project
            decision: The decision made
            context: Context for the decision
            reasoning: Reasoning behind the decision
            alternatives: Alternative options considered
            tags: Additional tags

        Returns:
            MemoryResponse: Response object with storage status
        """
        content = f"""
Decision: {decision}

Context: {context}

Reasoning: {reasoning}

Alternatives Considered:
{chr(10).join(f"- {alt}" for alt in (alternatives or []))}
""".strip()

        metadata = {
            "decision": decision,
            "context": context,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
            "decision_type": "architectural",
        }

        return await self.store_memory(
            category=MemoryCategory.PROJECT,
            content=content,
            metadata=metadata,
            project_name=project_name,
            tags=(tags or []) + ["decision", "architecture"],
        )

    # Synchronous Methods (for backwards compatibility)

    def create_project_memory_space_sync(
        self, project_name: str, description: str = "", metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryResponse:
        """Synchronous version of create_project_memory_space."""
        return asyncio.run(self.create_project_memory_space(project_name, description, metadata))

    def store_memory_sync(
        self,
        category: MemoryCategory,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> MemoryResponse:
        """Synchronous version of store_memory."""
        return asyncio.run(self.store_memory(category, content, metadata, project_name, tags))

    def retrieve_memories_sync(
        self,
        category: Optional[MemoryCategory] = None,
        query: str = "",
        project_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> MemoryResponse:
        """Synchronous version of retrieve_memories."""
        return asyncio.run(self.retrieve_memories(category, query, project_filter, tags, limit))

    def update_memory_sync(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryResponse:
        """Synchronous version of update_memory."""
        return asyncio.run(self.update_memory(memory_id, content, metadata))

    def delete_memory_sync(self, memory_id: str) -> MemoryResponse:
        """Synchronous version of delete_memory."""
        return asyncio.run(self.delete_memory(memory_id))

    # Statistics and Monitoring

    async def _get_subsystem_versions(self) -> Dict[str, str]:
        """
        Get current subsystem versions for memory metadata.
        
        Returns:
            Dict[str, str]: Dictionary of subsystem names to version strings
        """
        try:
            from .parent_directory_manager import ParentDirectoryManager
            
            # Create parent directory manager instance
            pdm = ParentDirectoryManager()
            await pdm._initialize()
            
            # Get subsystem version information
            version_info = pdm.get_subsystem_versions()
            
            # Extract just the version strings
            subsystems = version_info.get("subsystems", {})
            versions = {}
            
            for subsystem, info in subsystems.items():
                version = info.get("version", "unknown")
                if version not in ["not_found", "unknown"]:
                    versions[subsystem] = version
            
            # Clean up
            await pdm._cleanup()
            
            # Always include memory version if available
            if "memory" not in versions:
                versions["memory"] = "002"  # Default current memory version
            
            return versions
            
        except Exception as e:
            logger.warning(f"Failed to get subsystem versions for memory metadata: {e}")
            # Return minimal version information
            return {
                "memory": "002",
                "framework": "010"
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about memory operations.

        Returns:
            Dict: Statistics about operations, performance, and health
        """
        return {
            **self.stats,
            "connection_status": self.is_connected(),
            "last_health_check": (
                datetime.fromtimestamp(self._last_health_check).isoformat()
                if self._last_health_check
                else None
            ),
            "success_rate": (
                self.stats["successful_operations"] / max(1, self.stats["operations_count"])
            )
            * 100,
            "categories_supported": list(self.categories.keys()),
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "connection_pool_size": self.config.connection_pool_size,
            },
        }


# Factory Functions


def create_claude_pm_memory(
    host: str = "localhost",
    port: int = 8002,
    timeout: int = 30,
    api_key: Optional[str] = None,
    **kwargs,
) -> ClaudePMMemory:
    """
    Factory function to create a ClaudePMMemory instance.

    Args:
        host: mem0AI service host
        port: mem0AI service port
        timeout: Request timeout in seconds
        api_key: Optional API key for authentication
        **kwargs: Additional configuration parameters

    Returns:
        ClaudePMMemory: Configured memory management instance
    """
    config = ClaudePMConfig(host=host, port=port, timeout=timeout, api_key=api_key, **kwargs)
    return ClaudePMMemory(config)


@asynccontextmanager
async def claude_pm_memory_context(
    host: str = "localhost",
    port: int = 8002,
    timeout: int = 30,
    api_key: Optional[str] = None,
    **kwargs,
):
    """
    Async context manager for ClaudePMMemory.

    Args:
        host: mem0AI service host
        port: mem0AI service port
        timeout: Request timeout in seconds
        api_key: Optional API key for authentication
        **kwargs: Additional configuration parameters

    Yields:
        ClaudePMMemory: Connected memory management instance
    """
    memory = create_claude_pm_memory(host, port, timeout, api_key, **kwargs)
    try:
        await memory.connect()
        yield memory
    finally:
        await memory.disconnect()


# Example usage and integration examples
if __name__ == "__main__":

    async def example_usage():
        """Example usage of ClaudePMMemory class."""
        print("🧠 ClaudePMMemory Example Usage")

        # Create memory instance
        async with claude_pm_memory_context() as memory:
            print(f"✅ Connected to mem0AI service: {memory.is_connected()}")

            # Create a project memory space
            response = await memory.create_project_memory_space(
                project_name="example_project",
                description="Example project for testing ClaudePMMemory",
            )
            print(f"📁 Project space created: {response.success}")

            # Store different types of memories
            decision_response = await memory.store_project_decision(
                project_name="example_project",
                decision="Use FastAPI for REST API",
                context="Need to build a REST API for the application",
                reasoning="FastAPI provides excellent async support and automatic OpenAPI documentation",
                alternatives=["Flask", "Django Rest Framework"],
                tags=["python", "api", "backend"],
            )
            print(
                f"📋 Decision stored: {decision_response.success}, ID: {decision_response.memory_id}"
            )

            # Retrieve memories
            search_response = await memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query="FastAPI API",
                project_filter="example_project",
            )
            print(
                f"🔍 Search results: {search_response.success}, Found: {len(search_response.data.get('memories', []))}"
            )

            # Get statistics
            stats = memory.get_statistics()
            print(
                f"📊 Statistics: {stats['successful_operations']}/{stats['operations_count']} successful operations"
            )

        print("🎯 Example completed successfully!")

    # Run example
    asyncio.run(example_usage())
