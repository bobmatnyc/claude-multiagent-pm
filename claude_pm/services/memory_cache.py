#!/usr/bin/env python3
"""
Memory Cache - Local file-based cache for project metadata
Provides fast fallback access when mem0AI service has limited functionality
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Dict[str, Any]
    stored_at: str
    category: str
    project_name: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MemoryCache:
    """
    Local file-based cache for project metadata with fast search capabilities.
    
    This serves as a fallback when mem0AI service has limited functionality,
    providing sub-second retrieval times for project information.
    """
    
    def __init__(self, cache_dir: str = None):
        """Initialize memory cache."""
        if cache_dir is None:
            cache_dir = Path.home() / ".claude_pm" / "memory_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.project_cache_file = self.cache_dir / "projects.json"
        self.metadata_cache_file = self.cache_dir / "metadata.json"
        
        # In-memory cache for performance
        self._project_cache: Dict[str, Dict[str, Any]] = {}
        self._metadata_cache: Dict[str, Any] = {}
        self._last_loaded = None
        self._cache_ttl = timedelta(hours=1)  # Reload from disk every hour
        
        # Load cache on initialization
        asyncio.create_task(self._load_cache())
    
    async def _load_cache(self):
        """Load cache from disk."""
        try:
            # Load project cache
            if self.project_cache_file.exists():
                with open(self.project_cache_file, 'r') as f:
                    self._project_cache = json.load(f)
                logger.debug(f"Loaded {len(self._project_cache)} projects from cache")
            
            # Load metadata cache
            if self.metadata_cache_file.exists():
                with open(self.metadata_cache_file, 'r') as f:
                    self._metadata_cache = json.load(f)
                logger.debug(f"Loaded metadata cache")
            
            self._last_loaded = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self._project_cache = {}
            self._metadata_cache = {}
    
    async def _save_cache(self):
        """Save cache to disk."""
        try:
            # Save project cache
            with open(self.project_cache_file, 'w') as f:
                json.dump(self._project_cache, f, indent=2, default=str)
            
            # Save metadata cache
            with open(self.metadata_cache_file, 'w') as f:
                json.dump(self._metadata_cache, f, indent=2, default=str)
            
            logger.debug(f"Saved cache with {len(self._project_cache)} projects")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    async def _ensure_cache_fresh(self):
        """Ensure cache is fresh, reload if needed."""
        if (self._last_loaded is None or 
            datetime.now() - self._last_loaded > self._cache_ttl):
            await self._load_cache()
    
    async def store_project_memory(self, project_name: str, content: str, 
                                 metadata: Dict[str, Any], category: str = "project",
                                 tags: List[str] = None) -> bool:
        """
        Store project memory in cache.
        
        Args:
            project_name: Name of the project
            content: Memory content
            metadata: Memory metadata
            category: Memory category
            tags: Memory tags
            
        Returns:
            bool: True if stored successfully
        """
        try:
            await self._ensure_cache_fresh()
            
            entry = CacheEntry(
                data={
                    "content": content,
                    "metadata": metadata,
                    "project_name": project_name
                },
                stored_at=datetime.now().isoformat(),
                category=category,
                project_name=project_name,
                tags=tags or []
            )
            
            # Store in project cache
            self._project_cache[project_name] = asdict(entry)
            
            # Update metadata cache
            self._metadata_cache["last_update"] = datetime.now().isoformat()
            self._metadata_cache["total_projects"] = len(self._project_cache)
            
            # Save to disk
            await self._save_cache()
            
            logger.debug(f"Stored project memory: {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store project memory for {project_name}: {e}")
            return False
    
    async def get_project_memory(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get project memory from cache.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict with project memory or None
        """
        try:
            await self._ensure_cache_fresh()
            
            if project_name in self._project_cache:
                entry = self._project_cache[project_name]
                logger.debug(f"Retrieved project memory: {project_name}")
                return entry["data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get project memory for {project_name}: {e}")
            return None
    
    async def search_projects(self, query: str, category: str = None, 
                            tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search projects in cache.
        
        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of matching project memories
        """
        try:
            await self._ensure_cache_fresh()
            
            results = []
            query_lower = query.lower() if query else ""
            
            for project_name, entry in self._project_cache.items():
                # Category filter
                if category and entry.get("category") != category:
                    continue
                
                # Tags filter
                if tags:
                    entry_tags = entry.get("tags", [])
                    if not any(tag in entry_tags for tag in tags):
                        continue
                
                # Query filter
                if query:
                    content = str(entry["data"].get("content", "")).lower()
                    metadata_text = str(entry["data"].get("metadata", {})).lower()
                    project_name_lower = project_name.lower()
                    
                    if (query_lower not in content and 
                        query_lower not in metadata_text and 
                        query_lower not in project_name_lower):
                        continue
                
                # Calculate relevance score
                relevance_score = 1.0
                if query:
                    relevance_score = self._calculate_relevance(query, entry, project_name)
                
                results.append({
                    "project_name": project_name,
                    "data": entry["data"],
                    "relevance_score": relevance_score,
                    "stored_at": entry["stored_at"]
                })
            
            # Sort by relevance and apply limit
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            logger.debug(f"Search '{query}' found {len(results[:limit])} results")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search projects: {e}")
            return []
    
    def _calculate_relevance(self, query: str, entry: Dict[str, Any], project_name: str) -> float:
        """Calculate relevance score for search results."""
        score = 0.0
        query_terms = query.lower().split()
        
        # Project name match (highest weight)
        for term in query_terms:
            if term in project_name.lower():
                score += 2.0
        
        # Content match
        content = str(entry["data"].get("content", "")).lower()
        for term in query_terms:
            if term in content:
                score += 1.0
        
        # Metadata match
        metadata = entry["data"].get("metadata", {})
        metadata_text = str(metadata).lower()
        for term in query_terms:
            if term in metadata_text:
                score += 0.5
        
        # Normalize score
        max_score = len(query_terms) * 3.5
        return min(1.0, score / max_score) if max_score > 0 else 0.0
    
    async def get_all_projects(self) -> List[str]:
        """Get list of all cached project names."""
        await self._ensure_cache_fresh()
        return list(self._project_cache.keys())
    
    async def clear_cache(self):
        """Clear all cached data."""
        self._project_cache.clear()
        self._metadata_cache.clear()
        
        # Remove cache files
        if self.project_cache_file.exists():
            self.project_cache_file.unlink()
        if self.metadata_cache_file.exists():
            self.metadata_cache_file.unlink()
        
        logger.info("Memory cache cleared")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        await self._ensure_cache_fresh()
        
        return {
            "total_projects": len(self._project_cache),
            "cache_dir": str(self.cache_dir),
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "cache_files_exist": {
                "projects": self.project_cache_file.exists(),
                "metadata": self.metadata_cache_file.exists()
            }
        }


# Factory function
def create_memory_cache(cache_dir: str = None) -> MemoryCache:
    """Create a memory cache instance."""
    return MemoryCache(cache_dir)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of MemoryCache."""
        print("📦 Memory Cache Example Usage")
        
        cache = create_memory_cache()
        
        # Store a project
        await cache.store_project_memory(
            project_name="test-project",
            content="Test project for caching",
            metadata={
                "type": "web_app",
                "tech_stack": "typescript_react",
                "description": "A test project"
            },
            tags=["test", "web_app", "typescript"]
        )
        
        # Retrieve project
        project_data = await cache.get_project_memory("test-project")
        if project_data:
            print(f"✅ Retrieved: {project_data['metadata']['description']}")
        
        # Search projects
        results = await cache.search_projects("typescript", limit=5)
        print(f"🔍 Search found {len(results)} results")
        
        # Get stats
        stats = await cache.get_cache_stats()
        print(f"📊 Cache stats: {stats['total_projects']} projects")
        
        print("✅ Example completed!")
    
    # Run example
    asyncio.run(example_usage())