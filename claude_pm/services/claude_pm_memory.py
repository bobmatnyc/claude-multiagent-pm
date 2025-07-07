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
                "tags": ["architecture", "decisions", "planning"]
            },
            MemoryCategory.PATTERN: {
                "description": "Successful solutions, code patterns, design patterns, and reusable approaches", 
                "fields": ["pattern_type", "use_cases", "implementation", "benefits"],
                "tags": ["patterns", "solutions", "reusable", "best-practices"]
            },
            MemoryCategory.TEAM: {
                "description": "Coding standards, team preferences, workflows, and organizational knowledge",
                "fields": ["standard_type", "enforcement_level", "examples", "tools"],
                "tags": ["standards", "team", "workflow", "conventions"]
            },
            MemoryCategory.ERROR: {
                "description": "Bug patterns, error solutions, debugging knowledge, and lessons learned",
                "fields": ["error_type", "symptoms", "root_cause", "solution", "prevention"],
                "tags": ["bugs", "debugging", "solutions", "prevention"]
            }
        }
        
        # Statistics tracking
        self.stats = {
            "operations_count": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_response_time": 0.0,
            "memory_spaces_created": 0,
            "memories_stored": 0,
            "memories_retrieved": 0
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
                '%(asctime)s - ClaudePMMemory - %(levelname)s - %(message)s'
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
                enable_cleanup_closed=True
            )
            
            # Create session with timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=10,
                sock_read=self.config.timeout
            )
            
            headers = {
                "User-Agent": "ClaudePM-Memory-Client/3.0.0",
                "Content-Type": "application/json"
            }
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self._session = aiohttp.ClientSession(
                connector=self._connection_pool,
                timeout=timeout,
                headers=headers,
                raise_for_status=False
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
        operation_name = kwargs.pop('_operation_name', operation_func.__name__)
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Ensure connection before operation
                if not await self.ensure_connection():
                    return MemoryResponse(
                        success=False,
                        error="Failed to establish connection to mem0AI service",
                        operation=operation_name
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
                
                return MemoryResponse(
                    success=True,
                    data=result,
                    operation=operation_name
                )
                
            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(f"Network error in operation '{operation_name}' (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Error in operation '{operation_name}' (attempt {attempt + 1}): {e}")
                
                # For non-network errors, don't retry
                if not isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError)):
                    break
            
            # Exponential backoff for retry
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2 ** attempt)
                logger.debug(f"Retrying operation '{operation_name}' in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries failed
        execution_time = time.time() - start_time
        self._update_stats(False, execution_time)
        
        error_msg = f"Operation '{operation_name}' failed after {self.config.max_retries} attempts: {last_exception}"
        logger.error(error_msg)
        
        return MemoryResponse(
            success=False,
            error=error_msg,
            operation=operation_name
        )
    
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
        self.stats["avg_response_time"] = (current_avg * (total_ops - 1) + execution_time) / total_ops
    
    # Project Memory Space Management
    
    async def create_project_memory_space(self, project_name: str, description: str = "", 
                                        metadata: Optional[Dict[str, Any]] = None) -> MemoryResponse:
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
            space_data = {
                "space_name": project_name,
                "description": description or f"Memory space for Claude PM project: {project_name}",
                "metadata": {
                    "project": project_name,
                    "created_by": "claude_pm_framework",
                    "created_at": datetime.now().isoformat(),
                    "framework_version": "3.0.0",
                    "space_type": "claude_pm_project",
                    **(metadata or {})
                }
            }
            
            async with self._session.post(f"{self.base_url}/spaces", json=space_data) as response:
                if response.status in [200, 201, 409]:  # 409 = already exists
                    self.stats["memory_spaces_created"] += 1
                    logger.info(f"Project memory space created/verified: {project_name}")
                    return {"space_name": project_name, "status": "created"}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        return await self._execute_with_retry(_create_space, _operation_name="create_project_memory_space")
    
    # Core Memory Operations
    
    async def store_memory(self, category: MemoryCategory, content: str, 
                          metadata: Optional[Dict[str, Any]] = None,
                          project_name: Optional[str] = None, 
                          tags: Optional[List[str]] = None) -> MemoryResponse:
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
                raise ValueError(f"Invalid category: {category}. Valid categories: {list(self.categories.keys())}")
            
            # Prepare memory data
            memory_data = {
                "content": content,
                "space_name": project_name or "claude_pm_global",
                "metadata": {
                    "category": category.value,
                    "category_description": self.categories[category]["description"],
                    "tags": tags or [],
                    "project": project_name,
                    "stored_at": datetime.now().isoformat(),
                    "framework_version": "3.0.0",
                    "source": "claude_pm_memory",
                    **(metadata or {})
                }
            }
            
            async with self._session.post(f"{self.base_url}/memories", json=memory_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    memory_id = result.get("id")
                    self.stats["memories_stored"] += 1
                    logger.info(f"Memory stored - Category: {category.value}, ID: {memory_id}")
                    return {"memory_id": memory_id, "category": category.value}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        response = await self._execute_with_retry(_store_memory, _operation_name="store_memory")
        if response.success and response.data:
            response.memory_id = response.data.get("memory_id")
        return response
    
    async def retrieve_memories(self, category: Optional[MemoryCategory] = None, 
                              query: str = "", project_filter: Optional[str] = None,
                              tags: Optional[List[str]] = None, limit: int = 10) -> MemoryResponse:
        """
        Retrieve memories with filtering options.
        
        Args:
            category: Filter by memory category
            query: Search query
            project_filter: Filter by project name
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            MemoryResponse: Response object with retrieved memories
        """
        async def _retrieve_memories():
            params = {
                "query": query,
                "limit": limit,
                "include_metadata": True
            }
            
            if project_filter:
                params["space_name"] = project_filter
            
            if category:
                params["category"] = category.value
            
            if tags:
                params["tags"] = ",".join(tags)
            
            async with self._session.get(f"{self.base_url}/memories/search", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    memories = result.get("memories", [])
                    self.stats["memories_retrieved"] += len(memories)
                    logger.debug(f"Retrieved {len(memories)} memories for query '{query}'")
                    return {"memories": memories, "count": len(memories)}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        return await self._execute_with_retry(_retrieve_memories, _operation_name="retrieve_memories")
    
    async def update_memory(self, memory_id: str, content: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> MemoryResponse:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            content: New content (if updating)
            metadata: New metadata (if updating)
            
        Returns:
            MemoryResponse: Response object with update status
        """
        async def _update_memory():
            update_data = {"id": memory_id}
            
            if content is not None:
                update_data["content"] = content
            
            if metadata is not None:
                current_metadata = metadata.copy()
                current_metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadata"] = current_metadata
            
            async with self._session.put(f"{self.base_url}/memories/{memory_id}", json=update_data) as response:
                if response.status == 200:
                    logger.info(f"Memory updated: {memory_id}")
                    return {"memory_id": memory_id, "status": "updated"}
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        
        return await self._execute_with_retry(_update_memory, _operation_name="update_memory")
    
    async def delete_memory(self, memory_id: str) -> MemoryResponse:
        """
        Delete a memory.
        
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
    
    async def store_project_decision(self, project_name: str, decision: str, 
                                   context: str, reasoning: str, 
                                   alternatives: Optional[List[str]] = None,
                                   tags: Optional[List[str]] = None) -> MemoryResponse:
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
            "decision_type": "architectural"
        }
        
        return await self.store_memory(
            category=MemoryCategory.PROJECT,
            content=content,
            metadata=metadata,
            project_name=project_name,
            tags=(tags or []) + ["decision", "architecture"]
        )
    
    # Synchronous Methods (for backwards compatibility)
    
    def create_project_memory_space_sync(self, project_name: str, description: str = "",
                                       metadata: Optional[Dict[str, Any]] = None) -> MemoryResponse:
        """Synchronous version of create_project_memory_space."""
        return asyncio.run(self.create_project_memory_space(project_name, description, metadata))
    
    def store_memory_sync(self, category: MemoryCategory, content: str,
                         metadata: Optional[Dict[str, Any]] = None,
                         project_name: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> MemoryResponse:
        """Synchronous version of store_memory."""
        return asyncio.run(self.store_memory(category, content, metadata, project_name, tags))
    
    def retrieve_memories_sync(self, category: Optional[MemoryCategory] = None,
                             query: str = "", project_filter: Optional[str] = None,
                             tags: Optional[List[str]] = None, limit: int = 10) -> MemoryResponse:
        """Synchronous version of retrieve_memories."""
        return asyncio.run(self.retrieve_memories(category, query, project_filter, tags, limit))
    
    def update_memory_sync(self, memory_id: str, content: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> MemoryResponse:
        """Synchronous version of update_memory."""
        return asyncio.run(self.update_memory(memory_id, content, metadata))
    
    def delete_memory_sync(self, memory_id: str) -> MemoryResponse:
        """Synchronous version of delete_memory."""
        return asyncio.run(self.delete_memory(memory_id))
    
    # Statistics and Monitoring
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about memory operations.
        
        Returns:
            Dict: Statistics about operations, performance, and health
        """
        return {
            **self.stats,
            "connection_status": self.is_connected(),
            "last_health_check": datetime.fromtimestamp(self._last_health_check).isoformat() if self._last_health_check else None,
            "success_rate": (self.stats["successful_operations"] / max(1, self.stats["operations_count"])) * 100,
            "categories_supported": list(self.categories.keys()),
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "connection_pool_size": self.config.connection_pool_size
            }
        }


# Factory Functions

def create_claude_pm_memory(host: str = "localhost", port: int = 8002,
                           timeout: int = 30, api_key: Optional[str] = None,
                           **kwargs) -> ClaudePMMemory:
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
    config = ClaudePMConfig(
        host=host,
        port=port,
        timeout=timeout,
        api_key=api_key,
        **kwargs
    )
    return ClaudePMMemory(config)


@asynccontextmanager
async def claude_pm_memory_context(host: str = "localhost", port: int = 8002,
                                  timeout: int = 30, api_key: Optional[str] = None,
                                  **kwargs):
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
                description="Example project for testing ClaudePMMemory"
            )
            print(f"📁 Project space created: {response.success}")
            
            # Store different types of memories
            decision_response = await memory.store_project_decision(
                project_name="example_project",
                decision="Use FastAPI for REST API",
                context="Need to build a REST API for the application",
                reasoning="FastAPI provides excellent async support and automatic OpenAPI documentation",
                alternatives=["Flask", "Django Rest Framework"],
                tags=["python", "api", "backend"]
            )
            print(f"📋 Decision stored: {decision_response.success}, ID: {decision_response.memory_id}")
            
            # Retrieve memories
            search_response = await memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query="FastAPI API",
                project_filter="example_project"
            )
            print(f"🔍 Search results: {search_response.success}, Found: {len(search_response.data.get('memories', []))}")
            
            # Get statistics
            stats = memory.get_statistics()
            print(f"📊 Statistics: {stats['successful_operations']}/{stats['operations_count']} successful operations")
            
        print("🎯 Example completed successfully!")
    
    # Run example
    asyncio.run(example_usage())