"""
Enhanced mem0AI Backend

This module implements an enhanced mem0AI backend with fallback awareness.
It provides advanced memory capabilities with similarity search and intelligent indexing.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from ..interfaces.exceptions import BackendError, BackendInitializationError, AuthenticationError


class Mem0AIBackend(MemoryBackend):
    """
    Enhanced mem0AI backend with fallback awareness.
    
    This backend provides:
    - Advanced similarity search capabilities
    - Intelligent memory indexing
    - Semantic understanding
    - High-performance operations
    - API-based access to mem0AI service
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize mem0AI backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        
        # Configuration
        self.host = self.get_config("host", "localhost")
        self.port = self.get_config("port", 8002)
        self.timeout = self.get_config("timeout", 30)
        self.api_key = self.get_config("api_key")
        self.max_retries = self.get_config("max_retries", 3)
        self.retry_delay = self.get_config("retry_delay", 1.0)
        self.connection_pool_size = self.get_config("connection_pool_size", 10)
        
        # Connection management
        self.base_url = f"http://{self.host}:{self.port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self._connection_lock = asyncio.Lock()
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        
        # Request statistics
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_count": 0,
            "avg_response_time": 0.0,
            "last_error": None
        }
    
    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "mem0ai"
    
    @property
    def supports_similarity_search(self) -> bool:
        """Check if backend supports similarity search."""
        return True
    
    async def initialize(self) -> bool:
        """Initialize mem0AI connection."""
        try:
            async with self._connection_lock:
                # Check if already initialized with valid session
                if self.session and not self.session.closed and self._initialized:
                    return True
                
                # Cleanup any existing connections
                await self._cleanup_connection()
                
                # Create connection pool
                self.connector = aiohttp.TCPConnector(
                    limit=self.connection_pool_size,
                    limit_per_host=self.connection_pool_size // 2,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    enable_cleanup_closed=True
                )
                
                # Create session with timeout configuration
                timeout = aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=10,
                    sock_read=self.timeout
                )
                
                headers = {
                    "User-Agent": "ClaudePM-Memory-Client/2.0.0",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                self.session = aiohttp.ClientSession(
                    connector=self.connector,
                    timeout=timeout,
                    headers=headers,
                    raise_for_status=False
                )
                
                # Test connection
                if await self.health_check():
                    self._initialized = True
                    self._healthy = True
                    self.logger.info(f"mem0AI backend initialized: {self.base_url}")
                    return True
                else:
                    self.logger.error("mem0AI service health check failed during initialization")
                    await self._cleanup_connection()
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize mem0AI backend: {e}")
            await self._cleanup_connection()
            raise BackendInitializationError(f"mem0AI initialization failed: {e}", "mem0ai")
    
    async def health_check(self) -> bool:
        """Check mem0AI service health."""
        try:
            if not self.session:
                return False
            
            # Check if recent health check is available
            import time
            current_time = time.time()
            if current_time - self._last_health_check < self._health_check_interval:
                return self._healthy
            
            # Perform health check
            async with self.session.get(f"{self.base_url}/health") as response:
                is_healthy = response.status == 200
                self._last_health_check = current_time
                
                if is_healthy:
                    # Try to get service info
                    try:
                        data = await response.json()
                        self.logger.debug(f"mem0AI service info: {data}")
                    except:
                        pass  # Service might not return JSON
                
                return is_healthy
                
        except Exception as e:
            self.logger.debug(f"mem0AI health check failed: {e}")
            return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to mem0AI service with retry logic."""
        if not self.session:
            raise BackendError("Service not initialized", "mem0ai", "request")
        
        url = f"{self.base_url}{endpoint}"
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._stats["total_requests"] += 1
                
                # Make request
                async with self.session.request(
                    method,
                    url,
                    json=data,
                    params=params
                ) as response:
                    
                    # Handle authentication errors
                    if response.status == 401:
                        raise AuthenticationError("Authentication failed", "mem0ai")
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                    
                    # Handle other errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise BackendError(
                            f"HTTP {response.status}: {error_text}",
                            "mem0ai",
                            f"{method} {endpoint}"
                        )
                    
                    # Success
                    self._stats["successful_requests"] += 1
                    
                    # Parse response
                    try:
                        return await response.json()
                    except:
                        # Service might not return JSON for all endpoints
                        return {"status": "success", "data": await response.text()}
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                self._stats["failed_requests"] += 1
                
                if attempt < self.max_retries - 1:
                    self._stats["retry_count"] += 1
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    self.logger.debug(f"Retrying mem0AI request (attempt {attempt + 1}): {e}")
                else:
                    self.logger.error(f"mem0AI request failed after {self.max_retries} attempts: {e}")
        
        # All retries failed
        self._stats["last_error"] = str(last_error)
        raise BackendError(
            f"Request failed after {self.max_retries} attempts: {last_error}",
            "mem0ai",
            f"{method} {endpoint}",
            last_error
        )
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to mem0AI service."""
        try:
            data = {
                "content": content,
                "space_name": project_name,
                "metadata": {
                    "category": category.value,
                    "tags": tags or [],
                    "project": project_name,
                    "created_at": datetime.now().isoformat(),
                    "framework": "claude-pm",
                    **(metadata or {})
                }
            }
            
            response = await self._make_request("POST", "/memories", data=data)
            
            memory_id = response.get("id")
            if memory_id:
                self.logger.debug(f"Added memory {memory_id} to mem0AI project {project_name}")
                return memory_id
            else:
                self.logger.error(f"mem0AI did not return memory ID: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error adding memory to mem0AI: {e}")
            raise BackendError(f"Failed to add memory: {e}", "mem0ai", "add_memory", e)
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in mem0AI service."""
        try:
            params = {
                "query": query.query,
                "space_name": project_name,
                "limit": query.limit,
                "include_metadata": query.include_metadata
            }
            
            if query.category:
                params["category"] = query.category.value
            
            if query.tags:
                params["tags"] = ",".join(query.tags)
            
            if query.similarity_threshold != 0.7:
                params["similarity_threshold"] = query.similarity_threshold
            
            response = await self._make_request("GET", "/memories/search", params=params)
            
            memories = []
            for memory_data in response.get("memories", []):
                try:
                    memory = self._convert_to_memory_item(memory_data, project_name)
                    
                    # Apply additional filters
                    if self._matches_query_filters(memory, query):
                        memories.append(memory)
                        
                except Exception as e:
                    self.logger.warning(f"Error converting mem0AI memory: {e}")
                    continue
            
            self.logger.debug(f"Found {len(memories)} memories for query in {project_name}")
            return memories
            
        except Exception as e:
            self.logger.error(f"Error searching memories in mem0AI: {e}")
            raise BackendError(f"Failed to search memories: {e}", "mem0ai", "search_memories", e)
    
    def _matches_query_filters(self, memory: MemoryItem, query: MemoryQuery) -> bool:
        """Check if memory matches additional query filters."""
        # Age filters
        if query.max_age_seconds is not None or query.min_age_seconds is not None:
            age_seconds = memory.get_age_seconds()
            
            if query.max_age_seconds is not None and age_seconds > query.max_age_seconds:
                return False
            
            if query.min_age_seconds is not None and age_seconds < query.min_age_seconds:
                return False
        
        return True
    
    def _convert_to_memory_item(self, memory_data: Dict[str, Any], project_name: str) -> MemoryItem:
        """Convert mem0AI response to MemoryItem."""
        try:
            metadata = memory_data.get("metadata", {})
            
            return MemoryItem(
                id=memory_data.get("id", ""),
                content=memory_data.get("content", ""),
                category=MemoryCategory.from_string(metadata.get("category", "project")),
                tags=metadata.get("tags", []),
                metadata=metadata,
                created_at=memory_data.get("created_at", ""),
                updated_at=memory_data.get("updated_at", ""),
                project_name=project_name
            )
        except Exception as e:
            raise BackendError(f"Failed to convert mem0AI response: {e}", "mem0ai", "conversion")
    
    async def get_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            params = {"space_name": project_name}
            response = await self._make_request("GET", f"/memories/{memory_id}", params=params)
            
            if response:
                return self._convert_to_memory_item(response, project_name)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting memory {memory_id}: {e}")
            raise BackendError(f"Failed to get memory: {e}", "mem0ai", "get_memory", e)
    
    async def update_memory(
        self,
        project_name: str,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory."""
        try:
            update_data = {
                "id": memory_id,
                "space_name": project_name
            }
            
            if content is not None:
                update_data["content"] = content
            
            if tags is not None or metadata is not None:
                current_metadata = {}
                if metadata:
                    current_metadata.update(metadata)
                if tags is not None:
                    current_metadata["tags"] = tags
                
                current_metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadata"] = current_metadata
            
            response = await self._make_request("PUT", f"/memories/{memory_id}", data=update_data)
            
            success = response.get("success", True)
            if success:
                self.logger.debug(f"Updated memory {memory_id} in mem0AI project {project_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            raise BackendError(f"Failed to update memory: {e}", "mem0ai", "update_memory", e)
    
    async def delete_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> bool:
        """Delete a memory."""
        try:
            params = {"space_name": project_name}
            response = await self._make_request("DELETE", f"/memories/{memory_id}", params=params)
            
            success = response.get("success", True)
            if success:
                self.logger.debug(f"Deleted memory {memory_id} from mem0AI project {project_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            raise BackendError(f"Failed to delete memory: {e}", "mem0ai", "delete_memory", e)
    
    async def get_project_memories(
        self,
        project_name: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project."""
        try:
            params = {
                "space_name": project_name,
                "limit": limit
            }
            
            if category:
                params["category"] = category.value
            
            response = await self._make_request("GET", "/memories", params=params)
            
            memories = []
            for memory_data in response.get("memories", []):
                try:
                    memory = self._convert_to_memory_item(memory_data, project_name)
                    memories.append(memory)
                except Exception as e:
                    self.logger.warning(f"Error converting mem0AI memory: {e}")
                    continue
            
            return memories
            
        except Exception as e:
            self.logger.error(f"Error getting project memories: {e}")
            raise BackendError(f"Failed to get project memories: {e}", "mem0ai", "get_project_memories", e)
    
    async def get_memory_stats(
        self,
        project_name: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        try:
            params = {"space_name": project_name}
            response = await self._make_request("GET", "/memories/stats", params=params)
            
            stats = response.get("stats", {})
            
            # Add backend-specific information
            stats.update({
                "backend": "mem0ai",
                "service_url": self.base_url,
                "similarity_search": True,
                "api_version": response.get("api_version", "unknown")
            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            # Return basic stats structure on error
            return {
                "total": 0,
                "categories": {},
                "error": str(e),
                "backend": "mem0ai"
            }
    
    async def get_all_projects(self) -> List[str]:
        """Get list of all projects with memories."""
        try:
            response = await self._make_request("GET", "/spaces")
            
            spaces = response.get("spaces", [])
            return [space.get("name", "") for space in spaces if space.get("name")]
            
        except Exception as e:
            self.logger.error(f"Error getting all projects: {e}")
            raise BackendError(f"Failed to get all projects: {e}", "mem0ai", "get_all_projects", e)
    
    async def bulk_add_memories(
        self,
        project_name: str,
        memories: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """Add multiple memories in a single batch operation."""
        try:
            # Prepare batch data
            batch_data = {
                "space_name": project_name,
                "memories": []
            }
            
            for memory_data in memories:
                batch_data["memories"].append({
                    "content": memory_data.get("content", ""),
                    "metadata": {
                        "category": memory_data.get("category", "project"),
                        "tags": memory_data.get("tags", []),
                        "project": project_name,
                        "created_at": datetime.now().isoformat(),
                        "framework": "claude-pm",
                        **(memory_data.get("metadata", {}))
                    }
                })
            
            response = await self._make_request("POST", "/memories/batch", data=batch_data)
            
            # Extract memory IDs from response
            results = []
            for result in response.get("results", []):
                if result.get("success"):
                    results.append(result.get("id"))
                else:
                    results.append(None)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error bulk adding memories: {e}")
            # Fall back to individual additions
            return await super().bulk_add_memories(project_name, memories)
    
    async def _cleanup_connection(self):
        """Safely cleanup connection resources."""
        if self.session:
            try:
                if not self.session.closed:
                    await self.session.close()
            except Exception as e:
                self.logger.warning(f"Error closing session: {e}")
            finally:
                self.session = None
        
        if self.connector:
            try:
                if not self.connector.closed:
                    await self.connector.close()
            except Exception as e:
                self.logger.warning(f"Error closing connector: {e}")
            finally:
                self.connector = None
        
        self._initialized = False
        self._healthy = False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._cleanup_connection()
        self.logger.info("mem0AI backend cleanup completed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics."""
        return {
            "backend": "mem0ai",
            "service_url": self.base_url,
            "connection_pool_size": self.connection_pool_size,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "stats": self._stats.copy()
        }
    
    def get_features(self) -> Dict[str, bool]:
        """Get supported features."""
        features = super().get_features()
        features.update({
            "similarity_search": True,
            "semantic_understanding": True,
            "advanced_indexing": True,
            "batch_operations": True,
            "api_based": True,
            "high_performance": True,
            "scalable": True,
            "project_listing": True
        })
        return features
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about the mem0AI service."""
        try:
            response = await self._make_request("GET", "/info")
            return response
        except Exception as e:
            self.logger.error(f"Error getting service info: {e}")
            return {"error": str(e)}
    
    async def create_memory_space(self, project_name: str, description: str = "") -> bool:
        """Create a new memory space for a project."""
        try:
            data = {
                "name": project_name,
                "description": description or f"Memory space for {project_name}",
                "metadata": {
                    "framework": "claude-pm",
                    "created_at": datetime.now().isoformat()
                }
            }
            
            response = await self._make_request("POST", "/spaces", data=data)
            
            success = response.get("success", True)
            if success:
                self.logger.info(f"Created memory space for project {project_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating memory space: {e}")
            return False
    
    async def delete_memory_space(self, project_name: str) -> bool:
        """Delete a memory space and all its memories."""
        try:
            params = {"space_name": project_name}
            response = await self._make_request("DELETE", "/spaces", params=params)
            
            success = response.get("success", True)
            if success:
                self.logger.info(f"Deleted memory space for project {project_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting memory space: {e}")
            return False