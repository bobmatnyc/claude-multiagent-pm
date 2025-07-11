"""
TinyDB Memory Backend

This module implements a TinyDB-based memory backend for simple deployments.
TinyDB provides a lightweight, JSON-based document storage solution.
"""

import asyncio
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import threading

try:
    from tinydb import TinyDB, Query
    from tinydb.storages import JSONStorage
    TINYDB_AVAILABLE = True
except ImportError:
    TINYDB_AVAILABLE = False

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from ..interfaces.exceptions import BackendError, BackendInitializationError


class TinyDBBackend(MemoryBackend):
    """
    TinyDB-based memory backend for simple deployments.
    
    This backend provides:
    - JSON-based document storage
    - Simple query capabilities
    - Lightweight deployment
    - File-based persistence
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize TinyDB backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        
        if not TINYDB_AVAILABLE:
            raise BackendInitializationError(
                "TinyDB not available. Install with: pip install tinydb",
                "tinydb", "import"
            )
        
        # Configuration
        self.db_path = self.get_config("db_path", "memory.json")
        self.indent = self.get_config("indent", 2)
        self.ensure_ascii = self.get_config("ensure_ascii", False)
        
        # Internal state
        self.logger = logging.getLogger(__name__)
        self._db: Optional[TinyDB] = None
        self._lock = threading.RLock()
        
        # Query cache for performance
        self._query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self._cache_timestamps: Dict[str, float] = {}
    
    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "tinydb"
    
    @property
    def supports_similarity_search(self) -> bool:
        """Check if backend supports similarity search."""
        return False  # TinyDB has limited text search capabilities
    
    async def initialize(self) -> bool:
        """Initialize TinyDB database."""
        try:
            # Ensure directory exists
            db_path = Path(self.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create TinyDB instance
            self._db = TinyDB(
                self.db_path,
                storage=JSONStorage,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii
            )
            
            # Verify database is working
            if not await self.health_check():
                raise BackendInitializationError("TinyDB health check failed", "tinydb")
            
            self._initialized = True
            self._healthy = True
            
            self.logger.info(f"TinyDB backend initialized: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TinyDB backend: {e}")
            self._safe_close()
            raise BackendInitializationError(f"TinyDB initialization failed: {e}", "tinydb")
    
    async def health_check(self) -> bool:
        """Check TinyDB database health."""
        try:
            if not self._db:
                return False
            
            # Simple test - try to access the database
            with self._lock:
                _ = len(self._db.all())
            
            return True
            
        except Exception as e:
            self.logger.debug(f"TinyDB health check failed: {e}")
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to TinyDB database."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "add_memory")
                
                memory_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                document = {
                    "id": memory_id,
                    "project_name": project_name,
                    "content": content,
                    "category": category.value,
                    "tags": tags or [],
                    "metadata": metadata or {},
                    "created_at": now,
                    "updated_at": now
                }
                
                self._db.insert(document)
                
                # Invalidate cache
                self._invalidate_cache(project_name)
                
                self.logger.debug(f"Added memory {memory_id} to project {project_name}")
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Error adding memory to TinyDB: {e}")
            raise BackendError(f"Failed to add memory: {e}", "tinydb", "add_memory", e)
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in TinyDB database."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "search_memories")
                
                # Check cache first
                cache_key = self._get_cache_key(project_name, query)
                cached_results = self._get_cached_results(cache_key)
                if cached_results is not None:
                    return [self._convert_to_memory_item(doc) for doc in cached_results]
                
                # Build query
                Memory = Query()
                search_query = Memory.project_name == project_name
                
                # Add category filter
                if query.category:
                    search_query &= Memory.category == query.category.value
                
                # Add text search (simple contains search)
                if query.query.strip():
                    text_query = query.query.strip().lower()
                    search_query &= (
                        Memory.content.search(text_query) |
                        Memory.tags.any(lambda tag: text_query in tag.lower())
                    )
                
                # Add tag filters
                if query.tags:
                    for tag in query.tags:
                        search_query &= Memory.tags.any(lambda t: t.lower() == tag.lower())
                
                # Execute search
                results = self._db.search(search_query)
                
                # Apply additional filters
                filtered_results = []
                for doc in results:
                    memory = self._convert_to_memory_item(doc)
                    if self._matches_query_filters(memory, query):
                        filtered_results.append(memory)
                
                # Sort results
                filtered_results.sort(key=lambda m: m.created_at, reverse=True)
                
                # Apply limit and offset
                start_idx = query.offset
                end_idx = start_idx + query.limit
                final_results = filtered_results[start_idx:end_idx]
                
                # Cache results
                self._cache_results(cache_key, [m.to_dict() for m in final_results])
                
                return final_results
                
        except Exception as e:
            self.logger.error(f"Error searching memories in TinyDB: {e}")
            raise BackendError(f"Failed to search memories: {e}", "tinydb", "search_memories", e)
    
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
    
    def _convert_to_memory_item(self, doc: Dict[str, Any]) -> MemoryItem:
        """Convert TinyDB document to MemoryItem."""
        try:
            return MemoryItem(
                id=doc.get("id", ""),
                project_name=doc.get("project_name", ""),
                content=doc.get("content", ""),
                category=MemoryCategory.from_string(doc.get("category", "project")),
                tags=doc.get("tags", []),
                metadata=doc.get("metadata", {}),
                created_at=doc.get("created_at", ""),
                updated_at=doc.get("updated_at", "")
            )
        except Exception as e:
            raise BackendError(f"Failed to convert document to memory item: {e}", "tinydb", "conversion")
    
    async def get_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "get_memory")
                
                Memory = Query()
                query = (Memory.id == memory_id) & (Memory.project_name == project_name)
                
                doc = self._db.get(query)
                if doc:
                    return self._convert_to_memory_item(doc)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting memory {memory_id}: {e}")
            raise BackendError(f"Failed to get memory: {e}", "tinydb", "get_memory", e)
    
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
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "update_memory")
                
                Memory = Query()
                query = (Memory.id == memory_id) & (Memory.project_name == project_name)
                
                # Check if memory exists
                if not self._db.get(query):
                    return False
                
                # Build update data
                update_data = {"updated_at": datetime.now().isoformat()}
                
                if content is not None:
                    update_data["content"] = content
                
                if tags is not None:
                    update_data["tags"] = tags
                
                if metadata is not None:
                    update_data["metadata"] = metadata
                
                # Update document
                self._db.update(update_data, query)
                
                # Invalidate cache
                self._invalidate_cache(project_name)
                
                self.logger.debug(f"Updated memory {memory_id} in project {project_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            raise BackendError(f"Failed to update memory: {e}", "tinydb", "update_memory", e)
    
    async def delete_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> bool:
        """Delete a memory."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "delete_memory")
                
                Memory = Query()
                query = (Memory.id == memory_id) & (Memory.project_name == project_name)
                
                # Delete document
                removed = self._db.remove(query)
                
                # Invalidate cache
                self._invalidate_cache(project_name)
                
                success = len(removed) > 0
                if success:
                    self.logger.debug(f"Deleted memory {memory_id} from project {project_name}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            raise BackendError(f"Failed to delete memory: {e}", "tinydb", "delete_memory", e)
    
    async def get_project_memories(
        self,
        project_name: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "get_project_memories")
                
                Memory = Query()
                query = Memory.project_name == project_name
                
                if category:
                    query &= Memory.category == category.value
                
                # Get all matching documents
                docs = self._db.search(query)
                
                # Convert to memory items
                memories = []
                for doc in docs:
                    try:
                        memory = self._convert_to_memory_item(doc)
                        memories.append(memory)
                    except Exception as e:
                        self.logger.warning(f"Error converting document to memory item: {e}")
                        continue
                
                # Sort by created_at descending
                memories.sort(key=lambda m: m.created_at, reverse=True)
                
                # Apply limit
                return memories[:limit]
                
        except Exception as e:
            self.logger.error(f"Error getting project memories: {e}")
            raise BackendError(f"Failed to get project memories: {e}", "tinydb", "get_project_memories", e)
    
    async def get_memory_stats(
        self,
        project_name: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "get_memory_stats")
                
                Memory = Query()
                project_query = Memory.project_name == project_name
                
                # Get all memories for project
                memories = self._db.search(project_query)
                
                # Calculate stats
                total_count = len(memories)
                categories = {}
                
                most_recent = None
                oldest = None
                
                for memory in memories:
                    # Count by category
                    category = memory.get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1
                    
                    # Track most recent and oldest
                    created_at = memory.get("created_at", "")
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
                    "backend": "tinydb",
                    "database_path": self.db_path
                }
                
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            raise BackendError(f"Failed to get memory stats: {e}", "tinydb", "get_memory_stats", e)
    
    async def get_all_projects(self) -> List[str]:
        """Get list of all projects with memories."""
        try:
            with self._lock:
                if not self._db:
                    raise BackendError("Database not initialized", "tinydb", "get_all_projects")
                
                # Get all unique project names
                projects = set()
                for doc in self._db.all():
                    project_name = doc.get("project_name")
                    if project_name:
                        projects.add(project_name)
                
                return sorted(list(projects))
                
        except Exception as e:
            self.logger.error(f"Error getting all projects: {e}")
            raise BackendError(f"Failed to get all projects: {e}", "tinydb", "get_all_projects", e)
    
    def _get_cache_key(self, project_name: str, query: MemoryQuery) -> str:
        """Generate cache key for query."""
        query_str = f"{project_name}:{query.query}:{query.category}:{query.limit}:{query.offset}"
        if query.tags:
            query_str += f":{','.join(sorted(query.tags))}"
        return query_str
    
    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if valid."""
        if cache_key in self._query_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self._cache_ttl:
                return self._query_cache[cache_key]
        return None
    
    def _cache_results(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cache query results."""
        self._query_cache[cache_key] = results
        self._cache_timestamps[cache_key] = time.time()
        
        # Clean old cache entries
        self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self._cache_ttl
        ]
        
        for key in expired_keys:
            self._query_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    def _invalidate_cache(self, project_name: str):
        """Invalidate cache entries for a project."""
        keys_to_remove = [
            key for key in self._query_cache.keys()
            if key.startswith(f"{project_name}:")
        ]
        
        for key in keys_to_remove:
            self._query_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    def _safe_close(self):
        """Safely close database connection."""
        if self._db:
            try:
                self._db.close()
            except Exception as e:
                self.logger.warning(f"Error closing TinyDB: {e}")
            finally:
                self._db = None
                self._initialized = False
                self._healthy = False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        with self._lock:
            self._safe_close()
            
            # Clear caches
            self._query_cache.clear()
            self._cache_timestamps.clear()
        
        self.logger.info("TinyDB backend cleanup completed")
    
    def get_features(self) -> Dict[str, bool]:
        """Get supported features."""
        features = super().get_features()
        features.update({
            "full_text_search": False,
            "json_storage": True,
            "simplicity": True,
            "project_listing": True,
            "lightweight": True,
            "file_based": True
        })
        return features
    
    async def create_backup(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            import shutil
            
            if not Path(self.db_path).exists():
                raise BackendError(f"Database file not found: {self.db_path}", "tinydb", "create_backup")
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise BackendError(f"Failed to create backup: {e}", "tinydb", "create_backup", e)
    
    async def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup."""
        try:
            import shutil
            
            if not Path(backup_path).exists():
                raise BackendError(f"Backup file not found: {backup_path}", "tinydb", "restore_backup")
            
            # Close current database
            self._safe_close()
            
            # Copy backup to current database
            shutil.copy2(backup_path, self.db_path)
            
            # Re-initialize
            success = await self.initialize()
            
            if success:
                self.logger.info(f"Restored from backup: {backup_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            raise BackendError(f"Failed to restore backup: {e}", "tinydb", "restore_backup", e)