"""
SQLite Memory Backend

This module implements a SQLite-based memory backend with full-text search capabilities.
It provides a lightweight, file-based storage solution with excellent performance.
"""

import asyncio
import aiosqlite
import sqlite3
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..interfaces.backend import MemoryBackend
from ..interfaces.models import MemoryItem, MemoryQuery, MemoryCategory, HealthStatus
from ..interfaces.exceptions import BackendError, BackendInitializationError


class SQLiteBackend(MemoryBackend):
    """
    SQLite-based memory backend with full feature parity.
    
    This backend provides:
    - Full-text search using SQLite FTS5
    - ACID transactions
    - WAL mode for better concurrency
    - Efficient indexing
    - Backup and recovery
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SQLite backend.
        
        Args:
            config: Backend configuration
        """
        super().__init__(config)
        
        # Configuration
        self.db_path = self.get_config("db_path", "memory.db")
        self.enable_fts = self.get_config("enable_fts", True)
        self.enable_wal = self.get_config("enable_wal", True)
        self.pragma_settings = self.get_config("pragma_settings", {
            "synchronous": "NORMAL",
            "cache_size": 10000,
            "temp_store": "MEMORY",
            "mmap_size": 268435456  # 256MB
        })
        
        # Internal state
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[aiosqlite.Connection] = None
        self._connection_lock = asyncio.Lock()
        self._schema_version = 1
    
    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "sqlite"
    
    @property
    def supports_similarity_search(self) -> bool:
        """Check if backend supports similarity search."""
        return self.enable_fts
    
    async def initialize(self) -> bool:
        """Initialize SQLite database."""
        try:
            async with self._connection_lock:
                if self._connection:
                    return True
                
                # Ensure directory exists
                db_path = Path(self.db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Connect to database
                self._connection = await aiosqlite.connect(self.db_path)
                
                # Configure database
                await self._configure_database()
                
                # Create schema
                await self._create_schema()
                
                # Verify schema
                await self._verify_schema()
                
                self._initialized = True
                self._healthy = True
                
                self.logger.info(f"SQLite backend initialized: {self.db_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite backend: {e}")
            await self._safe_close()
            raise BackendInitializationError(f"SQLite initialization failed: {e}", "sqlite")
    
    async def _configure_database(self):
        """Configure SQLite database settings."""
        try:
            # Enable WAL mode for better concurrency
            if self.enable_wal:
                await self._connection.execute("PRAGMA journal_mode=WAL")
            
            # Apply pragma settings
            for pragma, value in self.pragma_settings.items():
                await self._connection.execute(f"PRAGMA {pragma}={value}")
            
            # Enable foreign key constraints
            await self._connection.execute("PRAGMA foreign_keys=ON")
            
        except Exception as e:
            raise BackendInitializationError(f"Database configuration failed: {e}", "sqlite", "configuration")
    
    async def _create_schema(self):
        """Create database schema."""
        try:
            # Main memories table
            await self._connection.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    metadata TEXT,  -- JSON object
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes
            await self._connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_project 
                ON memories(project_name)
            ''')
            
            await self._connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_category 
                ON memories(category)
            ''')
            
            await self._connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_created_at 
                ON memories(created_at)
            ''')
            
            await self._connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_project_category 
                ON memories(project_name, category)
            ''')
            
            # Full-text search table if enabled
            if self.enable_fts:
                await self._create_fts_schema()
            
            # Schema version table
            await self._connection.execute('''
                CREATE TABLE IF NOT EXISTS schema_info (
                    version INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    description TEXT
                )
            ''')
            
            # Insert schema version if not exists
            await self._connection.execute('''
                INSERT OR IGNORE INTO schema_info (version, created_at, description)
                VALUES (?, ?, ?)
            ''', (self._schema_version, datetime.now().isoformat(), "Initial schema"))
            
            await self._connection.commit()
            
        except Exception as e:
            raise BackendInitializationError(f"Schema creation failed: {e}", "sqlite", "schema")
    
    async def _create_fts_schema(self):
        """Create full-text search schema."""
        try:
            # Create FTS5 virtual table
            await self._connection.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    project_name UNINDEXED,
                    content,
                    category UNINDEXED,
                    tags UNINDEXED,
                    content='memories',
                    content_rowid='rowid'
                )
            ''')
            
            # Triggers to keep FTS in sync
            await self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS memories_fts_insert 
                AFTER INSERT ON memories 
                BEGIN
                    INSERT INTO memories_fts(id, project_name, content, category, tags)
                    VALUES (new.id, new.project_name, new.content, new.category, new.tags);
                END
            ''')
            
            await self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS memories_fts_update 
                AFTER UPDATE ON memories 
                BEGIN
                    INSERT INTO memories_fts(memories_fts, id, project_name, content, category, tags)
                    VALUES ('delete', old.id, old.project_name, old.content, old.category, old.tags);
                    INSERT INTO memories_fts(id, project_name, content, category, tags)
                    VALUES (new.id, new.project_name, new.content, new.category, new.tags);
                END
            ''')
            
            await self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS memories_fts_delete 
                AFTER DELETE ON memories 
                BEGIN
                    INSERT INTO memories_fts(memories_fts, id, project_name, content, category, tags)
                    VALUES ('delete', old.id, old.project_name, old.content, old.category, old.tags);
                END
            ''')
            
        except Exception as e:
            raise BackendInitializationError(f"FTS schema creation failed: {e}", "sqlite", "fts")
    
    async def _verify_schema(self):
        """Verify database schema is correct."""
        try:
            # Check if main table exists
            cursor = await self._connection.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='memories'
            ''')
            if not await cursor.fetchone():
                raise BackendInitializationError("memories table not found", "sqlite", "verification")
            
            # Check if FTS table exists when enabled
            if self.enable_fts:
                cursor = await self._connection.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='memories_fts'
                ''')
                if not await cursor.fetchone():
                    raise BackendInitializationError("memories_fts table not found", "sqlite", "verification")
            
            # Check schema version
            cursor = await self._connection.execute('''
                SELECT version FROM schema_info ORDER BY version DESC LIMIT 1
            ''')
            version_row = await cursor.fetchone()
            if not version_row or version_row[0] != self._schema_version:
                self.logger.warning(f"Schema version mismatch: expected {self._schema_version}, got {version_row[0] if version_row else 'none'}")
            
        except Exception as e:
            raise BackendInitializationError(f"Schema verification failed: {e}", "sqlite", "verification")
    
    async def health_check(self) -> bool:
        """Check SQLite database health."""
        try:
            if not self._connection:
                return False
            
            # Simple query to test database
            cursor = await self._connection.execute("SELECT 1")
            result = await cursor.fetchone()
            
            # Check if FTS is working (if enabled)
            if self.enable_fts:
                cursor = await self._connection.execute("SELECT count(*) FROM memories_fts")
                await cursor.fetchone()
            
            return result is not None
            
        except Exception as e:
            self.logger.debug(f"SQLite health check failed: {e}")
            return False
    
    async def add_memory(
        self,
        project_name: str,
        content: str,
        category: MemoryCategory,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add memory to SQLite database."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "add_memory")
                
                memory_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                tags_json = json.dumps(tags or [])
                metadata_json = json.dumps(metadata or {})
                
                await self._connection.execute('''
                    INSERT INTO memories (id, project_name, content, category, tags, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (memory_id, project_name, content, category.value, tags_json, metadata_json, now, now))
                
                await self._connection.commit()
                
                self.logger.debug(f"Added memory {memory_id} to project {project_name}")
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Error adding memory to SQLite: {e}")
            raise BackendError(f"Failed to add memory: {e}", "sqlite", "add_memory", e)
    
    async def search_memories(
        self,
        project_name: str,
        query: MemoryQuery
    ) -> List[MemoryItem]:
        """Search memories in SQLite database."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "search_memories")
                
                sql_params = [project_name]
                
                # Choose search method based on FTS availability and query
                if self.enable_fts and query.query.strip():
                    sql, params = self._build_fts_query(query, sql_params)
                else:
                    sql, params = self._build_standard_query(query, sql_params)
                
                # Execute query
                cursor = await self._connection.execute(sql, params)
                rows = await cursor.fetchall()
                
                # Convert to MemoryItem objects
                memories = []
                for row in rows:
                    try:
                        memory = self._convert_row_to_memory_item(row)
                        # Apply additional filters
                        if self._matches_query_filters(memory, query):
                            memories.append(memory)
                    except Exception as e:
                        self.logger.warning(f"Error converting row to memory item: {e}")
                        continue
                
                # Sort by relevance if FTS was used, otherwise by created_at
                if self.enable_fts and query.query.strip():
                    # FTS already provides relevance ordering
                    pass
                else:
                    memories.sort(key=lambda m: m.created_at, reverse=True)
                
                return memories[:query.limit]
                
        except Exception as e:
            self.logger.error(f"Error searching memories in SQLite: {e}")
            raise BackendError(f"Failed to search memories: {e}", "sqlite", "search_memories", e)
    
    def _build_fts_query(self, query: MemoryQuery, sql_params: List[Any]) -> tuple[str, List[Any]]:
        """Build FTS query."""
        sql = '''
            SELECT m.* FROM memories m
            JOIN memories_fts fts ON m.id = fts.id
            WHERE m.project_name = ? AND memories_fts MATCH ?
        '''
        
        # Build FTS query string
        fts_query = query.query.strip()
        if not fts_query:
            fts_query = "*"
        
        sql_params.append(fts_query)
        
        # Add category filter
        if query.category:
            sql += ' AND m.category = ?'
            sql_params.append(query.category.value)
        
        # Add tag filter
        if query.tags:
            for tag in query.tags:
                sql += ' AND m.tags LIKE ?'
                sql_params.append(f'%"{tag}"%')
        
        # Add ordering and limit
        sql += ' ORDER BY bm25(memories_fts) LIMIT ?'
        sql_params.append(query.limit * 2)  # Get more results for post-filtering
        
        if query.offset:
            sql += ' OFFSET ?'
            sql_params.append(query.offset)
        
        return sql, sql_params
    
    def _build_standard_query(self, query: MemoryQuery, sql_params: List[Any]) -> tuple[str, List[Any]]:
        """Build standard SQL query."""
        sql = 'SELECT * FROM memories WHERE project_name = ?'
        
        # Add text search if query provided
        if query.query.strip():
            sql += ' AND content LIKE ?'
            sql_params.append(f'%{query.query}%')
        
        # Add category filter
        if query.category:
            sql += ' AND category = ?'
            sql_params.append(query.category.value)
        
        # Add tag filter
        if query.tags:
            for tag in query.tags:
                sql += ' AND tags LIKE ?'
                sql_params.append(f'%"{tag}"%')
        
        # Add ordering and limit
        sql += ' ORDER BY created_at DESC LIMIT ?'
        sql_params.append(query.limit * 2)  # Get more results for post-filtering
        
        if query.offset:
            sql += ' OFFSET ?'
            sql_params.append(query.offset)
        
        return sql, sql_params
    
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
    
    def _convert_row_to_memory_item(self, row: tuple) -> MemoryItem:
        """Convert SQLite row to MemoryItem."""
        try:
            tags = json.loads(row[4]) if row[4] else []
            metadata = json.loads(row[5]) if row[5] else {}
            
            return MemoryItem(
                id=row[0],
                project_name=row[1],
                content=row[2],
                category=MemoryCategory.from_string(row[3]),
                tags=tags,
                metadata=metadata,
                created_at=row[6],
                updated_at=row[7]
            )
        except Exception as e:
            raise BackendError(f"Failed to convert row to memory item: {e}", "sqlite", "conversion")
    
    async def get_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "get_memory")
                
                cursor = await self._connection.execute('''
                    SELECT * FROM memories 
                    WHERE id = ? AND project_name = ?
                ''', (memory_id, project_name))
                
                row = await cursor.fetchone()
                if row:
                    return self._convert_row_to_memory_item(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting memory {memory_id}: {e}")
            raise BackendError(f"Failed to get memory: {e}", "sqlite", "get_memory", e)
    
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
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "update_memory")
                
                # Build update query
                update_fields = []
                params = []
                
                if content is not None:
                    update_fields.append("content = ?")
                    params.append(content)
                
                if tags is not None:
                    update_fields.append("tags = ?")
                    params.append(json.dumps(tags))
                
                if metadata is not None:
                    update_fields.append("metadata = ?")
                    params.append(json.dumps(metadata))
                
                if not update_fields:
                    return True  # Nothing to update
                
                update_fields.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                
                # Add WHERE clause parameters
                params.extend([memory_id, project_name])
                
                sql = f'''
                    UPDATE memories 
                    SET {', '.join(update_fields)}
                    WHERE id = ? AND project_name = ?
                '''
                
                cursor = await self._connection.execute(sql, params)
                await self._connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error updating memory {memory_id}: {e}")
            raise BackendError(f"Failed to update memory: {e}", "sqlite", "update_memory", e)
    
    async def delete_memory(
        self,
        project_name: str,
        memory_id: str
    ) -> bool:
        """Delete a memory."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "delete_memory")
                
                cursor = await self._connection.execute('''
                    DELETE FROM memories 
                    WHERE id = ? AND project_name = ?
                ''', (memory_id, project_name))
                
                await self._connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error deleting memory {memory_id}: {e}")
            raise BackendError(f"Failed to delete memory: {e}", "sqlite", "delete_memory", e)
    
    async def get_project_memories(
        self,
        project_name: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Get all memories for a project."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "get_project_memories")
                
                sql = 'SELECT * FROM memories WHERE project_name = ?'
                params = [project_name]
                
                if category:
                    sql += ' AND category = ?'
                    params.append(category.value)
                
                sql += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor = await self._connection.execute(sql, params)
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    try:
                        memory = self._convert_row_to_memory_item(row)
                        memories.append(memory)
                    except Exception as e:
                        self.logger.warning(f"Error converting row to memory item: {e}")
                        continue
                
                return memories
                
        except Exception as e:
            self.logger.error(f"Error getting project memories: {e}")
            raise BackendError(f"Failed to get project memories: {e}", "sqlite", "get_project_memories", e)
    
    async def get_memory_stats(
        self,
        project_name: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "get_memory_stats")
                
                # Total count
                cursor = await self._connection.execute('''
                    SELECT COUNT(*) FROM memories WHERE project_name = ?
                ''', (project_name,))
                total_count = (await cursor.fetchone())[0]
                
                # Count by category
                cursor = await self._connection.execute('''
                    SELECT category, COUNT(*) FROM memories 
                    WHERE project_name = ? 
                    GROUP BY category
                ''', (project_name,))
                
                categories = {}
                for row in await cursor.fetchall():
                    categories[row[0]] = row[1]
                
                # Recent activity
                cursor = await self._connection.execute('''
                    SELECT created_at FROM memories 
                    WHERE project_name = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (project_name,))
                
                recent_row = await cursor.fetchone()
                most_recent = recent_row[0] if recent_row else None
                
                # Oldest memory
                cursor = await self._connection.execute('''
                    SELECT created_at FROM memories 
                    WHERE project_name = ? 
                    ORDER BY created_at ASC 
                    LIMIT 1
                ''', (project_name,))
                
                oldest_row = await cursor.fetchone()
                oldest = oldest_row[0] if oldest_row else None
                
                return {
                    "total": total_count,
                    "categories": categories,
                    "most_recent": most_recent,
                    "oldest": oldest,
                    "backend": "sqlite",
                    "database_path": self.db_path,
                    "fts_enabled": self.enable_fts
                }
                
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            raise BackendError(f"Failed to get memory stats: {e}", "sqlite", "get_memory_stats", e)
    
    async def get_all_projects(self) -> List[str]:
        """Get list of all projects with memories."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "get_all_projects")
                
                cursor = await self._connection.execute('''
                    SELECT DISTINCT project_name FROM memories 
                    ORDER BY project_name
                ''')
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting all projects: {e}")
            raise BackendError(f"Failed to get all projects: {e}", "sqlite", "get_all_projects", e)
    
    async def create_backup(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            async with self._connection_lock:
                if not self._connection:
                    raise BackendError("Database not initialized", "sqlite", "create_backup")
                
                # Use SQLite backup API
                backup_conn = await aiosqlite.connect(backup_path)
                try:
                    await self._connection.backup(backup_conn)
                    return True
                finally:
                    await backup_conn.close()
                    
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise BackendError(f"Failed to create backup: {e}", "sqlite", "create_backup", e)
    
    async def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup."""
        try:
            if not Path(backup_path).exists():
                raise BackendError(f"Backup file not found: {backup_path}", "sqlite", "restore_backup")
            
            # Close current connection
            await self._safe_close()
            
            # Copy backup to current database
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # Re-initialize
            return await self.initialize()
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            raise BackendError(f"Failed to restore backup: {e}", "sqlite", "restore_backup", e)
    
    async def _safe_close(self):
        """Safely close database connection."""
        if self._connection:
            try:
                await self._connection.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None
                self._initialized = False
                self._healthy = False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._safe_close()
        self.logger.info("SQLite backend cleanup completed")
    
    def get_features(self) -> Dict[str, bool]:
        """Get supported features."""
        features = super().get_features()
        features.update({
            "full_text_search": self.enable_fts,
            "backup": True,
            "restore": True,
            "transactions": True,
            "project_listing": True,
            "bulk_operations": True,
            "indexing": True,
            "wal_mode": self.enable_wal
        })
        return features