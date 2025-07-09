#!/usr/bin/env python3
"""
Project Memory Manager - MEM-007 Fast Retrieval Component

This service provides instant project context retrieval from the indexed project metadata,
enabling sub-second response times and massive credit usage reduction.

Features:
- Sub-second project metadata retrieval
- Intelligent caching and optimization
- Query optimization and result ranking
- Context-aware project recommendations
- Performance monitoring and analytics
- Batch operations for efficiency
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging_config import get_logger
from ..services.claude_pm_memory import ClaudePMMemory, MemoryCategory, create_claude_pm_memory
from ..services.memory_cache import MemoryCache, create_memory_cache

logger = get_logger(__name__)


class SearchMode(str, Enum):
    """Search mode options."""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ProjectRanking(str, Enum):
    """Project ranking criteria."""
    RELEVANCE = "relevance"
    RECENCY = "recency"
    SIZE = "size"
    ACTIVITY = "activity"
    POPULARITY = "popularity"


@dataclass
class SearchResult:
    """Search result with metadata."""
    project_name: str
    project_data: Dict[str, Any]
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    retrieved_at: datetime = field(default_factory=datetime.now)
    cache_hit: bool = False


@dataclass
class SearchQuery:
    """Structured search query."""
    query: str
    mode: SearchMode = SearchMode.HYBRID
    ranking: ProjectRanking = ProjectRanking.RELEVANCE
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    include_metadata: bool = True
    
    def to_cache_key(self) -> str:
        """Generate cache key for this query."""
        return f"{self.query}_{self.mode.value}_{self.ranking.value}_{hash(str(sorted(self.filters.items())))}"


class ProjectMemoryManager:
    """
    Fast project memory retrieval manager for MEM-007
    
    Provides optimized, cached access to project metadata with intelligent
    ranking and filtering capabilities.
    """
    
    def __init__(self):
        """Initialize the Project Memory Manager."""
        self.memory: Optional[ClaudePMMemory] = None
        self.local_cache: Optional[MemoryCache] = None
        
        # Performance caching
        self.query_cache: Dict[str, Tuple[List[SearchResult], datetime]] = {}
        self.project_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)  # 15-minute cache TTL
        
        # Performance tracking
        self.stats = {
            "queries_total": 0,
            "queries_cached": 0,
            "queries_memory": 0,
            "avg_response_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "total_projects_indexed": 0,
            "last_index_refresh": None
        }
        
        # Query optimization
        self.popular_queries: Dict[str, int] = {}
        self.query_performance: Dict[str, List[float]] = {}
        
        # Search improvements
        self.synonym_map = {
            "js": ["javascript", "typescript", "node"],
            "ts": ["typescript", "javascript"],
            "py": ["python"],
            "api": ["rest", "graphql", "endpoint", "service"],
            "web": ["frontend", "ui", "react", "vue", "angular"],
            "backend": ["api", "server", "service"],
            "mobile": ["ios", "android", "react-native", "flutter"],
            "data": ["analytics", "ml", "ai", "database", "etl"]
        }
    
    async def initialize(self) -> bool:
        """Initialize the memory manager."""
        try:
            # Initialize mem0AI connection
            self.memory = create_claude_pm_memory()
            await self.memory.connect()
            
            # Initialize local cache fallback
            self.local_cache = create_memory_cache()
            
            if not self.memory.is_connected():
                logger.warning("Failed to connect to mem0AI service, using local cache only")
                # Continue with local cache only
            else:
                logger.info("Connected to mem0AI service")
            
            # Warm up cache with recent queries
            await self._warm_up_cache()
            
            logger.info("Project Memory Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Project Memory Manager: {e}")
            # Try to continue with local cache only
            try:
                self.local_cache = create_memory_cache()
                logger.info("Initialized with local cache fallback only")
                return True
            except Exception as cache_error:
                logger.error(f"Failed to initialize local cache: {cache_error}")
                return False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.memory:
            await self.memory.disconnect()
    
    async def get_project_info(self, project_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive project information with caching.
        
        Args:
            project_name: Name of the project
            use_cache: Whether to use cached results
            
        Returns:
            Dict with project information or None
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if use_cache and project_name in self.project_cache:
                cached_data, cached_time = self.project_cache[project_name]
                if datetime.now() - cached_time < self.cache_ttl:
                    self.stats["queries_cached"] += 1
                    response_time = (time.time() - start_time) * 1000
                    self._update_performance_stats(response_time, True)
                    
                    # Add cache metadata
                    result = cached_data.copy()
                    result["cache_hit"] = True
                    result["retrieved_at"] = datetime.now().isoformat()
                    return result
            
            # Try mem0AI first, then fall back to local cache
            project_data = None
            source = "unknown"
            
            # Attempt mem0AI retrieval
            if self.memory and self.memory.is_connected():
                try:
                    response = await self.memory.retrieve_memories(
                        category=MemoryCategory.PROJECT,
                        query=f"Project: {project_name}",
                        project_filter="project_index",
                        tags=["project_metadata"],
                        limit=1
                    )
                    
                    self.stats["queries_memory"] += 1
                    
                    if response.success and response.data and response.data.get("memories"):
                        memory = response.data["memories"][0]
                        metadata = memory.get("metadata", {})
                        project_data = metadata.get("project_data")
                        source = "mem0ai"
                        logger.debug(f"Retrieved {project_name} from mem0AI")
                except Exception as e:
                    logger.debug(f"mem0AI retrieval failed for {project_name}: {e}")
            
            # Fall back to local cache if mem0AI didn't work
            if not project_data and self.local_cache:
                try:
                    cache_entry = await self.local_cache.get_project_memory(project_name)
                    if cache_entry and cache_entry.get("metadata", {}).get("project_data"):
                        project_data = cache_entry["metadata"]["project_data"]
                        source = "local_cache"
                        logger.debug(f"Retrieved {project_name} from local cache")
                except Exception as e:
                    logger.debug(f"Local cache retrieval failed for {project_name}: {e}")
            
            if project_data:
                # Enhance with retrieval metadata
                enhanced_data = project_data.copy()
                enhanced_data.update({
                    "cache_hit": False,
                    "retrieved_at": datetime.now().isoformat(),
                    "source": source,
                    "confidence_score": 1.0  # Exact match
                })
                
                # Cache the result
                if use_cache:
                    self.project_cache[project_name] = (enhanced_data, datetime.now())
                
                response_time = (time.time() - start_time) * 1000
                self._update_performance_stats(response_time, False)
                
                return enhanced_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving project info for {project_name}: {e}")
            return None
    
    async def search_projects(self, search_query: SearchQuery) -> List[SearchResult]:
        """
        Search projects with intelligent ranking and caching.
        
        Args:
            search_query: Structured search query
            
        Returns:
            List of ranked search results
        """
        start_time = time.time()
        cache_key = search_query.to_cache_key()
        
        try:
            self.stats["queries_total"] += 1
            self._track_popular_query(search_query.query)
            
            # Check cache first
            if cache_key in self.query_cache:
                cached_results, cached_time = self.query_cache[cache_key]
                if datetime.now() - cached_time < self.cache_ttl:
                    self.stats["queries_cached"] += 1
                    response_time = (time.time() - start_time) * 1000
                    self._update_performance_stats(response_time, True)
                    
                    # Mark as cache hits
                    for result in cached_results:
                        result.cache_hit = True
                        result.retrieved_at = datetime.now()
                    
                    return cached_results
            
            # Execute search
            results = await self._execute_search(search_query)
            
            # Cache results
            self.query_cache[cache_key] = (results, datetime.now())
            
            response_time = (time.time() - start_time) * 1000
            self._update_performance_stats(response_time, False)
            self._track_query_performance(cache_key, response_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []
    
    async def _execute_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """Execute the actual search operation."""
        if not self.memory:
            return []
        
        # Expand query with synonyms
        expanded_query = self._expand_query_with_synonyms(search_query.query)
        
        # Build search tags
        search_tags = ["project_metadata"]
        if search_query.filters.get("project_type"):
            search_tags.append(search_query.filters["project_type"])
        if search_query.filters.get("tech_stack"):
            search_tags.append(search_query.filters["tech_stack"])
        if search_query.filters.get("language"):
            search_tags.append(search_query.filters["language"].lower())
        
        # Execute search based on mode
        if search_query.mode == SearchMode.EXACT:
            memories_response = await self._exact_search(expanded_query, search_tags, search_query.limit)
        elif search_query.mode == SearchMode.FUZZY:
            memories_response = await self._fuzzy_search(expanded_query, search_tags, search_query.limit)
        elif search_query.mode == SearchMode.SEMANTIC:
            memories_response = await self._semantic_search(expanded_query, search_tags, search_query.limit)
        else:  # HYBRID
            memories_response = await self._hybrid_search(expanded_query, search_tags, search_query.limit)
        
        # Process results
        if not (memories_response.success and memories_response.data and memories_response.data.get("memories")):
            return []
        
        # Convert to SearchResult objects
        results = []
        for memory in memories_response.data["memories"]:
            metadata = memory.get("metadata", {})
            project_data = metadata.get("project_data")
            
            if project_data:
                # Calculate relevance score
                relevance_score, match_reasons = self._calculate_relevance_score(
                    project_data, search_query.query, expanded_query
                )
                
                result = SearchResult(
                    project_name=project_data["name"],
                    project_data=project_data,
                    relevance_score=relevance_score,
                    match_reasons=match_reasons,
                    cache_hit=False
                )
                results.append(result)
        
        # Apply ranking
        results = self._rank_results(results, search_query.ranking)
        
        # Apply additional filters
        results = self._apply_filters(results, search_query.filters)
        
        return results[:search_query.limit]
    
    async def _exact_search(self, query: str, tags: List[str], limit: int):
        """Perform exact search."""
        return await self.memory.retrieve_memories(
            category=MemoryCategory.PROJECT,
            query=query,
            project_filter="project_index",
            tags=tags,
            limit=limit
        )
    
    async def _fuzzy_search(self, query: str, tags: List[str], limit: int):
        """Perform fuzzy search with query variations."""
        # Try multiple query variations
        query_variations = [
            query,
            query.lower(),
            query.replace("-", " "),
            query.replace("_", " ")
        ]
        
        all_results = []
        for variation in query_variations:
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query=variation,
                project_filter="project_index",
                tags=tags,
                limit=limit
            )
            
            if response.success and response.data:
                all_results.extend(response.data.get("memories", []))
        
        # Remove duplicates and return
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.get("id") not in seen_ids:
                seen_ids.add(result.get("id"))
                unique_results.append(result)
        
        return type(response)(
            success=True,
            data={"memories": unique_results[:limit]}
        )
    
    async def _semantic_search(self, query: str, tags: List[str], limit: int):
        """Perform semantic search (placeholder for future enhancement)."""
        # For now, use enhanced exact search
        # TODO: Implement true semantic search with embeddings
        return await self._exact_search(query, tags, limit)
    
    async def _hybrid_search(self, query: str, tags: List[str], limit: int):
        """Perform hybrid search combining multiple approaches."""
        # Combine exact and fuzzy search results
        exact_results = await self._exact_search(query, tags, limit // 2)
        fuzzy_results = await self._fuzzy_search(query, tags, limit // 2)
        
        # Merge results
        all_memories = []
        if exact_results.success and exact_results.data:
            all_memories.extend(exact_results.data.get("memories", []))
        if fuzzy_results.success and fuzzy_results.data:
            all_memories.extend(fuzzy_results.data.get("memories", []))
        
        # Remove duplicates
        seen_ids = set()
        unique_memories = []
        for memory in all_memories:
            if memory.get("id") not in seen_ids:
                seen_ids.add(memory.get("id"))
                unique_memories.append(memory)
        
        return type(exact_results)(
            success=True,
            data={"memories": unique_memories[:limit]}
        )
    
    def _expand_query_with_synonyms(self, query: str) -> str:
        """Expand query with synonyms for better matching."""
        words = query.lower().split()
        expanded_words = []
        
        for word in words:
            expanded_words.append(word)
            if word in self.synonym_map:
                expanded_words.extend(self.synonym_map[word])
        
        return " ".join(expanded_words)
    
    def _calculate_relevance_score(self, project_data: Dict[str, Any], 
                                 original_query: str, expanded_query: str) -> Tuple[float, List[str]]:
        """Calculate relevance score and match reasons."""
        score = 0.0
        match_reasons = []
        
        query_terms = set(original_query.lower().split())
        expanded_terms = set(expanded_query.lower().split())
        
        # Name match (highest weight)
        name_terms = set(project_data.get("name", "").lower().split("-"))
        name_matches = query_terms.intersection(name_terms)
        if name_matches:
            score += len(name_matches) * 2.0
            match_reasons.append(f"Name match: {', '.join(name_matches)}")
        
        # Description match
        description = project_data.get("description", "").lower()
        desc_matches = [term for term in query_terms if term in description]
        if desc_matches:
            score += len(desc_matches) * 1.5
            match_reasons.append(f"Description match: {', '.join(desc_matches)}")
        
        # Tech stack match
        tech_stack = project_data.get("tech_stack", "").lower()
        tech_matches = [term for term in expanded_terms if term in tech_stack]
        if tech_matches:
            score += len(tech_matches) * 1.2
            match_reasons.append(f"Tech stack match: {tech_stack}")
        
        # Language match
        languages = [lang.lower() for lang in project_data.get("languages", [])]
        lang_matches = [term for term in expanded_terms for lang in languages if term in lang]
        if lang_matches:
            score += len(lang_matches) * 1.0
            match_reasons.append(f"Language match: {', '.join(set(lang_matches))}")
        
        # Framework match
        frameworks = [fw.lower() for fw in project_data.get("frameworks", [])]
        fw_matches = [term for term in expanded_terms for fw in frameworks if term in fw]
        if fw_matches:
            score += len(fw_matches) * 1.0
            match_reasons.append(f"Framework match: {', '.join(set(fw_matches))}")
        
        # Feature match
        features = [f.lower() for f in project_data.get("features", [])]
        feature_matches = [term for term in expanded_terms for feat in features if term in feat]
        if feature_matches:
            score += len(feature_matches) * 0.8
            match_reasons.append(f"Feature match: {len(feature_matches)} features")
        
        # Tag match
        tags = [tag.lower() for tag in project_data.get("tags", [])]
        tag_matches = [term for term in expanded_terms for tag in tags if term in tag]
        if tag_matches:
            score += len(tag_matches) * 0.6
            match_reasons.append(f"Tag match: {len(tag_matches)} tags")
        
        # Normalize score (0-1 range)
        max_possible_score = len(query_terms) * 5.0  # Rough estimate
        normalized_score = min(1.0, score / max_possible_score) if max_possible_score > 0 else 0.0
        
        return normalized_score, match_reasons
    
    def _rank_results(self, results: List[SearchResult], ranking: ProjectRanking) -> List[SearchResult]:
        """Rank search results based on ranking criteria."""
        if ranking == ProjectRanking.RELEVANCE:
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
        
        elif ranking == ProjectRanking.RECENCY:
            return sorted(results, key=lambda r: r.project_data.get("last_modified", "1900-01-01"), reverse=True)
        
        elif ranking == ProjectRanking.SIZE:
            return sorted(results, key=lambda r: r.project_data.get("size_mb", 0), reverse=True)
        
        elif ranking == ProjectRanking.ACTIVITY:
            # Use last modified as proxy for activity
            return sorted(results, key=lambda r: r.project_data.get("last_modified", "1900-01-01"), reverse=True)
        
        elif ranking == ProjectRanking.POPULARITY:
            # Use feature count as proxy for popularity
            return sorted(results, key=lambda r: len(r.project_data.get("features", [])), reverse=True)
        
        return results
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply additional filters to results."""
        filtered_results = []
        
        for result in results:
            project_data = result.project_data
            
            # Size filter
            if "min_size_mb" in filters and project_data.get("size_mb", 0) < filters["min_size_mb"]:
                continue
            if "max_size_mb" in filters and project_data.get("size_mb", 0) > filters["max_size_mb"]:
                continue
            
            # Date filter
            if "modified_after" in filters:
                last_modified = project_data.get("last_modified", "1900-01-01")
                if last_modified < filters["modified_after"]:
                    continue
            
            # Feature filter
            if "has_features" in filters:
                required_features = set(filters["has_features"])
                project_features = set(f.lower() for f in project_data.get("features", []))
                if not required_features.intersection(project_features):
                    continue
            
            # Status filter
            if "status" in filters and project_data.get("status") != filters["status"]:
                continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    async def get_project_recommendations(self, current_project: str, limit: int = 5) -> List[SearchResult]:
        """
        Get project recommendations based on current project.
        
        Args:
            current_project: Name of current project
            limit: Maximum recommendations
            
        Returns:
            List of recommended projects
        """
        try:
            # Get current project info
            current_info = await self.get_project_info(current_project)
            if not current_info:
                return []
            
            # Build recommendation query based on tech stack and type
            tech_stack = current_info.get("tech_stack", "")
            project_type = current_info.get("type", "")
            languages = current_info.get("languages", [])
            
            query_terms = [tech_stack, project_type] + languages[:2]  # Top 2 languages
            query = " ".join(filter(None, query_terms))
            
            # Search for similar projects
            search_query = SearchQuery(
                query=query,
                mode=SearchMode.SEMANTIC,
                ranking=ProjectRanking.RELEVANCE,
                limit=limit + 1  # +1 to exclude current project
            )
            
            results = await self.search_projects(search_query)
            
            # Remove current project from results
            recommendations = [r for r in results if r.project_name != current_project]
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommendations for {current_project}: {e}")
            return []
    
    async def get_project_summary(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a concise project summary for quick reference.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict with project summary
        """
        try:
            project_info = await self.get_project_info(project_name)
            if not project_info:
                return None
            
            # Create concise summary
            summary = {
                "name": project_info["name"],
                "type": project_info.get("type", "unknown"),
                "tech_stack": project_info.get("tech_stack", "unknown"),
                "description": project_info.get("description", "")[:200] + "..." if len(project_info.get("description", "")) > 200 else project_info.get("description", ""),
                "main_languages": project_info.get("languages", [])[:3],
                "key_frameworks": project_info.get("frameworks", [])[:3],
                "top_features": project_info.get("features", [])[:5],
                "size": f"{project_info.get('file_count', 0)} files, {project_info.get('size_mb', 0):.1f}MB",
                "last_updated": project_info.get("last_modified", "unknown"),
                "development_commands": project_info.get("development_workflow", [])[:3],
                "quick_facts": self._generate_quick_facts(project_info)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for {project_name}: {e}")
            return None
    
    def _generate_quick_facts(self, project_info: Dict[str, Any]) -> List[str]:
        """Generate quick facts about the project."""
        facts = []
        
        # Size facts
        size_mb = project_info.get("size_mb", 0)
        if size_mb > 100:
            facts.append("Large codebase")
        elif size_mb > 10:
            facts.append("Medium-sized project")
        else:
            facts.append("Compact project")
        
        # Feature facts
        features = project_info.get("features", [])
        if "Test suite" in features:
            facts.append("Well-tested")
        if "Containerization" in features:
            facts.append("Dockerized")
        if "GitHub Actions CI/CD" in features:
            facts.append("CI/CD enabled")
        
        # Tech facts
        tech_stack = project_info.get("tech_stack", "")
        if "typescript" in tech_stack.lower():
            facts.append("TypeScript")
        if "python" in tech_stack.lower():
            facts.append("Python")
        
        return facts
    
    async def _warm_up_cache(self) -> None:
        """Warm up cache with common queries."""
        common_queries = [
            "typescript", "python", "react", "api", "web", "cli", "tool",
            "nextjs", "fastapi", "docker", "test", "data"
        ]
        
        for query in common_queries:
            try:
                search_query = SearchQuery(query=query, limit=5)
                await self.search_projects(search_query)
            except Exception:
                continue  # Ignore errors during warm-up
    
    def _track_popular_query(self, query: str) -> None:
        """Track popular queries for optimization."""
        query_key = query.lower().strip()
        self.popular_queries[query_key] = self.popular_queries.get(query_key, 0) + 1
    
    def _track_query_performance(self, cache_key: str, response_time_ms: float) -> None:
        """Track query performance for optimization."""
        if cache_key not in self.query_performance:
            self.query_performance[cache_key] = []
        
        self.query_performance[cache_key].append(response_time_ms)
        
        # Keep only last 10 measurements
        if len(self.query_performance[cache_key]) > 10:
            self.query_performance[cache_key] = self.query_performance[cache_key][-10:]
    
    def _update_performance_stats(self, response_time_ms: float, was_cached: bool) -> None:
        """Update performance statistics."""
        # Update average response time
        current_avg = self.stats["avg_response_time_ms"]
        total_queries = self.stats["queries_total"]
        
        if total_queries > 0:
            self.stats["avg_response_time_ms"] = (current_avg * (total_queries - 1) + response_time_ms) / total_queries
        else:
            self.stats["avg_response_time_ms"] = response_time_ms
        
        # Update cache hit rate
        if total_queries > 0:
            self.stats["cache_hit_rate"] = (self.stats["queries_cached"] / total_queries) * 100
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            **self.stats,
            "cache_size": len(self.query_cache),
            "project_cache_size": len(self.project_cache),
            "popular_queries": dict(sorted(self.popular_queries.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_query_performance": {
                cache_key: sum(times) / len(times)
                for cache_key, times in self.query_performance.items()
                if times
            },
            "memory_connected": self.memory.is_connected() if self.memory else False
        }
    
    async def clear_cache(self) -> None:
        """Clear all cached data."""
        self.query_cache.clear()
        self.project_cache.clear()
        logger.info("Project memory cache cleared")
    
    async def refresh_project(self, project_name: str) -> bool:
        """
        Force refresh a specific project's cached data.
        
        Args:
            project_name: Name of project to refresh
            
        Returns:
            True if successfully refreshed
        """
        try:
            # Remove from cache
            if project_name in self.project_cache:
                del self.project_cache[project_name]
            
            # Clear related query cache entries
            keys_to_remove = [key for key in self.query_cache.keys() if project_name.lower() in key.lower()]
            for key in keys_to_remove:
                del self.query_cache[key]
            
            # Force fresh retrieval
            fresh_data = await self.get_project_info(project_name, use_cache=False)
            
            return fresh_data is not None
            
        except Exception as e:
            logger.error(f"Error refreshing project {project_name}: {e}")
            return False


# Factory function
def create_project_memory_manager() -> ProjectMemoryManager:
    """Create a project memory manager instance."""
    return ProjectMemoryManager()


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of ProjectMemoryManager."""
        print("⚡ Project Memory Manager Example Usage")
        
        manager = create_project_memory_manager()
        
        try:
            # Initialize
            if not await manager.initialize():
                print("❌ Failed to initialize memory manager")
                return
            
            print("✅ Memory manager initialized")
            
            # Quick project info
            project_info = await manager.get_project_info("ai-code-review")
            if project_info:
                print(f"📋 Quick Info: {project_info['name']} - {project_info['type']}")
            
            # Search projects
            search_query = SearchQuery(
                query="typescript react",
                mode=SearchMode.HYBRID,
                ranking=ProjectRanking.RELEVANCE,
                limit=3
            )
            
            results = await manager.search_projects(search_query)
            print(f"🔍 Search Results: Found {len(results)} projects")
            
            for result in results:
                print(f"  - {result.project_name}: {result.relevance_score:.2f} ({', '.join(result.match_reasons)})")
            
            # Get recommendations
            recommendations = await manager.get_project_recommendations("ai-code-review", limit=3)
            print(f"💡 Recommendations: {[r.project_name for r in recommendations]}")
            
            # Performance stats
            stats = manager.get_performance_stats()
            print(f"📈 Performance: {stats['avg_response_time_ms']:.1f}ms avg, {stats['cache_hit_rate']:.1f}% cache hit rate")
            
        finally:
            await manager.cleanup()
        
        print("✅ Example completed!")
    
    # Run example
    asyncio.run(example_usage())