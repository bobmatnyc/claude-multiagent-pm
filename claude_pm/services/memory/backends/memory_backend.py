"""
In-Memory Backend

This module implements an in-memory storage backend for testing and development.
It provides fast, temporary storage with no persistence.
"""

import asyncio
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading
import time

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from ..interfaces.exceptions import BackendError


class InMemoryBackend(MemoryBackend):
    """
    In-memory backend for testing and development.
    
    This backend provides:
    - Ultra-fast operations
    - No persistence (data lost on restart)
    - Thread-safe operations
    - Ideal for testing and development
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize in-memory backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        
        # Configuration
        self.max_memory_size = self.get_config("max_memory_size", 1000)  # Maximum memories to store
        self.enable_expiration = self.get_config("enable_expiration", False)
        self.default_ttl = self.get_config("default_ttl", 3600)  # 1 hour default TTL
        
        # Internal state
        self.logger = logging.getLogger(__name__)
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._creation_order: List[str] = []  # Track insertion order
        self._access_times: Dict[str, float] = {}  # Track access times for LRU
        self._expiration_times: Dict[str, float] = {}  # Track expiration times
        
        # Statistics
        self._stats = {
            "total_memories": 0,
            "operations_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60  # seconds
        self._stop_cleanup = False
    
    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "memory"
    
    @property
    def supports_similarity_search(self) -> bool:
        """Check if backend supports similarity search."""
        return False  # Basic text search only
    
    async def initialize(self) -> bool:
        """Initialize in-memory storage."""
        try:
            # Start cleanup task if expiration is enabled
            if self.enable_expiration:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_memories())
            
            self._initialized = True
            self._healthy = True
            
            self.logger.info("In-memory backend initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize in-memory backend: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Always healthy for in-memory backend."""
        return True
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to in-memory storage."""
        try:
            with self._lock:
                memory_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                current_time = time.time()
                
                # Check if we need to evict memories
                if len(self._memories) >= self.max_memory_size:
                    self._evict_least_recently_used()
                
                # Create memory document
                memory_data = {
                    "id": memory_id,
                    "project_name": project_name,
                    "content": content,
                    "category": category.value,
                    "tags": tags or [],
                    "metadata": metadata or {},
                    "created_at": now,
                    "updated_at": now
                }
                
                # Store memory
                self._memories[memory_id] = memory_data
                self._creation_order.append(memory_id)
                self._access_times[memory_id] = current_time
                
                # Set expiration time if enabled
                if self.enable_expiration:
                    ttl = metadata.get("ttl", self.default_ttl) if metadata else self.default_ttl
                    self._expiration_times[memory_id] = current_time + ttl
                
                # Update stats
                self._stats["total_memories"] += 1
                self._stats["operations_count"] += 1
                
                self.logger.debug(f"Added memory {memory_id} to project {project_name}")
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Error adding memory to in-memory storage: {e}")
            raise BackendError(f"Failed to add memory: {e}", "memory", "add_memory", e)
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in in-memory storage."""
        try:
            with self._lock:
                results = []
                current_time = time.time()
                
                for memory_id, memory_data in self._memories.items():
                    # Check expiration
                    if self.enable_expiration and memory_id in self._expiration_times:
                        if current_time > self._expiration_times[memory_id]:
                            continue  # Skip expired memory
                    
                    # Filter by project
                    if memory_data["project_name"] != project_name:
                        continue
                    
                    # Filter by category
                    if query.category and memory_data["category"] != query.category.value:
                        continue
                    
                    # Text search
                    if query.query.strip():
                        query_lower = query.query.strip().lower()
                        content_match = query_lower in memory_data["content"].lower()
                        tags_match = any(query_lower in tag.lower() for tag in memory_data["tags"])
                        metadata_match = query_lower in str(memory_data["metadata"]).lower()
                        
                        if not (content_match or tags_match or metadata_match):
                            continue
                    
                    # Tag filters
                    if query.tags:
                        memory_tags = [tag.lower() for tag in memory_data["tags"]]
                        if not all(tag.lower() in memory_tags for tag in query.tags):
                            continue
                    
                    # Convert to MemoryItem
                    memory = self._convert_to_memory_item(memory_data)
                    
                    # Apply additional filters
                    if self._matches_query_filters(memory, query):
                        results.append(memory)
                        
                        # Update access time
                        self._access_times[memory_id] = current_time
                
                # Sort results
                results.sort(key=lambda m: m.created_at, reverse=True)
                
                # Apply limit and offset
                start_idx = query.offset
                end_idx = start_idx + query.limit
                final_results = results[start_idx:end_idx]
                
                # Update stats
                self._stats["operations_count"] += 1
                if results:
                    self._stats["cache_hits"] += 1
                else:
                    self._stats["cache_misses"] += 1
                
                return final_results
                
        except Exception as e:
            self.logger.error(f"Error searching memories in in-memory storage: {e}")
            raise BackendError(f"Failed to search memories: {e}", "memory", "search_memories", e)
    
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
    
    def _convert_to_memory_item(self, memory_data: Dict[str, Any]) -> MemoryItem:
        """Convert memory data to MemoryItem."""
        try:
            return MemoryItem(
                id=memory_data["id"],
                project_name=memory_data["project_name"],
                content=memory_data["content"],
                category=MemoryCategory.from_string(memory_data["category"]),
                tags=memory_data["tags"],
                metadata=memory_data["metadata"],
                created_at=memory_data["created_at"],
                updated_at=memory_data["updated_at"]
            )
        except Exception as e:
            raise BackendError(f"Failed to convert to memory item: {e}", "memory", "conversion")
    
    async def get_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            with self._lock:
                if memory_id not in self._memories:
                    return None
                
                memory_data = self._memories[memory_id]
                
                # Check project match
                if memory_data["project_name"] != project_name:
                    return None
                
                # Check expiration
                current_time = time.time()
                if self.enable_expiration and memory_id in self._expiration_times:
                    if current_time > self._expiration_times[memory_id]:
                        # Memory expired, remove it
                        self._remove_memory(memory_id)
                        return None
                
                # Update access time
                self._access_times[memory_id] = current_time
                
                # Update stats
                self._stats["operations_count"] += 1
                self._stats["cache_hits"] += 1
                
                return self._convert_to_memory_item(memory_data)
                
        except Exception as e:
            self.logger.error(f"Error getting memory {memory_id}: {e}")
            raise BackendError(f"Failed to get memory: {e}", "memory", "get_memory", e)
    
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
            with self._lock:
                if memory_id not in self._memories:
                    return False
                
                memory_data = self._memories[memory_id]
                
                # Check project match
                if memory_data["project_name"] != project_name:
                    return False
                
                # Check expiration
                current_time = time.time()
                if self.enable_expiration and memory_id in self._expiration_times:
                    if current_time > self._expiration_times[memory_id]:
                        # Memory expired, remove it
                        self._remove_memory(memory_id)
                        return False
                
                # Update fields
                if content is not None:
                    memory_data["content"] = content
                
                if tags is not None:
                    memory_data["tags"] = tags
                
                if metadata is not None:
                    memory_data["metadata"] = metadata
                
                memory_data["updated_at"] = datetime.now().isoformat()
                
                # Update access time
                self._access_times[memory_id] = current_time
                
                # Update expiration if new TTL provided
                if self.enable_expiration and metadata and "ttl" in metadata:
                    self._expiration_times[memory_id] = current_time + metadata["ttl"]
                
                # Update stats
                self._stats["operations_count"] += 1
                
                self.logger.debug(f"Updated memory {memory_id} in project {project_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            raise BackendError(f"Failed to update memory: {e}", "memory", "update_memory", e)
    
    async def delete_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> bool:
        """Delete a memory."""
        try:
            with self._lock:
                if memory_id not in self._memories:
                    return False
                
                memory_data = self._memories[memory_id]
                
                # Check project match
                if memory_data["project_name"] != project_name:
                    return False
                
                # Remove memory
                self._remove_memory(memory_id)
                
                # Update stats
                self._stats["operations_count"] += 1
                
                self.logger.debug(f"Deleted memory {memory_id} from project {project_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            raise BackendError(f"Failed to delete memory: {e}", "memory", "delete_memory", e)
    
    def _remove_memory(self, memory_id: str):
        """Remove memory from all internal structures."""
        self._memories.pop(memory_id, None)
        self._access_times.pop(memory_id, None)
        self._expiration_times.pop(memory_id, None)
        
        if memory_id in self._creation_order:
            self._creation_order.remove(memory_id)
    
    def _evict_least_recently_used(self):
        """Evict the least recently used memory."""
        if not self._access_times:
            return
        
        # Find least recently used memory
        lru_memory_id = min(self._access_times, key=self._access_times.get)
        
        # Remove it
        self._remove_memory(lru_memory_id)
        
        # Update stats
        self._stats["evictions"] += 1
        
        self.logger.debug(f"Evicted memory {lru_memory_id} (LRU)")
    
    async def get_project_memories(
        self,
        project_name: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project."""
        try:
            with self._lock:
                memories = []
                current_time = time.time()
                
                for memory_id, memory_data in self._memories.items():
                    # Check expiration
                    if self.enable_expiration and memory_id in self._expiration_times:
                        if current_time > self._expiration_times[memory_id]:
                            continue
                    
                    # Filter by project
                    if memory_data["project_name"] != project_name:
                        continue
                    
                    # Filter by category
                    if category and memory_data["category"] != category.value:
                        continue
                    
                    # Convert to MemoryItem
                    memory = self._convert_to_memory_item(memory_data)
                    memories.append(memory)
                    
                    # Update access time
                    self._access_times[memory_id] = current_time
                
                # Sort by created_at descending
                memories.sort(key=lambda m: m.created_at, reverse=True)
                
                # Apply limit
                result = memories[:limit]
                
                # Update stats
                self._stats["operations_count"] += 1
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error getting project memories: {e}")
            raise BackendError(f"Failed to get project memories: {e}", "memory", "get_project_memories", e)
    
    async def get_memory_stats(
        self,
        project_name: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        try:
            with self._lock:
                project_memories = []
                current_time = time.time()
                
                for memory_id, memory_data in self._memories.items():
                    # Check expiration
                    if self.enable_expiration and memory_id in self._expiration_times:
                        if current_time > self._expiration_times[memory_id]:
                            continue
                    
                    # Filter by project
                    if memory_data["project_name"] == project_name:
                        project_memories.append(memory_data)
                
                # Calculate stats
                total_count = len(project_memories)
                categories = {}
                
                most_recent = None
                oldest = None
                
                for memory_data in project_memories:
                    # Count by category
                    category = memory_data.get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1
                    
                    # Track most recent and oldest
                    created_at = memory_data.get("created_at", "")
                    if created_at:
                        if most_recent is None or created_at > most_recent:
                            most_recent = created_at
                        if oldest is None or created_at < oldest:
                            oldest = created_at
                
                return {
                    "total": total_count,
                    "categories": categories,
                    "most_recent": most_recent,
                    "oldest": oldest,
                    "backend": "memory",
                    "max_capacity": self.max_memory_size,
                    "current_usage": len(self._memories),
                    "expiration_enabled": self.enable_expiration,
                    "backend_stats": self._stats.copy()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            raise BackendError(f"Failed to get memory stats: {e}", "memory", "get_memory_stats", e)
    
    async def get_all_projects(self) -> List[str]:
        """Get list of all projects with memories."""
        try:
            with self._lock:
                projects = set()
                current_time = time.time()
                
                for memory_id, memory_data in self._memories.items():
                    # Check expiration
                    if self.enable_expiration and memory_id in self._expiration_times:
                        if current_time > self._expiration_times[memory_id]:
                            continue
                    
                    project_name = memory_data.get("project_name")
                    if project_name:
                        projects.add(project_name)
                
                return sorted(list(projects))
                
        except Exception as e:
            self.logger.error(f"Error getting all projects: {e}")
            raise BackendError(f"Failed to get all projects: {e}", "memory", "get_all_projects", e)
    
    async def _cleanup_expired_memories(self):
        """Background task to clean up expired memories."""
        while not self._stop_cleanup:
            try:
                current_time = time.time()
                expired_ids = []
                
                with self._lock:
                    for memory_id, expiration_time in self._expiration_times.items():
                        if current_time > expiration_time:
                            expired_ids.append(memory_id)
                
                # Remove expired memories
                for memory_id in expired_ids:
                    with self._lock:
                        self._remove_memory(memory_id)
                        self._stats["expirations"] += 1
                
                if expired_ids:
                    self.logger.debug(f"Cleaned up {len(expired_ids)} expired memories")
                
                await asyncio.sleep(self._cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(self._cleanup_interval)
    
    def clear_all_memories(self):
        """Clear all memories (for testing)."""
        with self._lock:
            self._memories.clear()
            self._creation_order.clear()
            self._access_times.clear()
            self._expiration_times.clear()
            self._stats = {
                "total_memories": 0,
                "operations_count": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "evictions": 0,
                "expirations": 0
            }
        
        self.logger.info("Cleared all memories")
    
    def get_backend_stats(self) -> Dict[str, Any]:
        """Get backend-specific statistics."""
        with self._lock:
            return {
                "total_memories": len(self._memories),
                "max_capacity": self.max_memory_size,
                "usage_percentage": (len(self._memories) / self.max_memory_size) * 100,
                "expiration_enabled": self.enable_expiration,
                "active_expirations": len(self._expiration_times) if self.enable_expiration else 0,
                "stats": self._stats.copy()
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Stop cleanup task
        self._stop_cleanup = True
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all memories
        self.clear_all_memories()
        
        self.logger.info("In-memory backend cleanup completed")
    
    def get_features(self) -> Dict[str, bool]:
        """Get supported features."""
        features = super().get_features()
        features.update({
            "speed": True,
            "testing": True,
            "expiration": self.enable_expiration,
            "lru_eviction": True,
            "statistics": True,
            "project_listing": True,
            "temporary_storage": True,
            "thread_safe": True
        })
        return features