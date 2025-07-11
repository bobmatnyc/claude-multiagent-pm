"""
Memory Context Enhancer

This module implements intelligent memory retrieval before operations to enhance
decision-making and prevent repeated mistakes. It automatically retrieves relevant
memories based on operation context and provides enhanced context for agents.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from .interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from .services.unified_service import FlexibleMemoryService


class RecallTrigger(str, Enum):
    """Types of memory recall triggers."""

    PRE_OPERATION = "pre_operation"  # Before agent operations
    SIMILAR_CONTEXT = "similar_context"  # When similar operations detected
    ERROR_PREVENTION = "error_prevention"  # When error patterns recognized
    DECISION_SUPPORT = "decision_support"  # For strategic decision points
    WORKFLOW_CONTEXT = "workflow_context"  # For push/deploy/publish workflows


@dataclass
class MemoryContext:
    """Enhanced context with relevant memories."""

    operation_type: str
    operation_context: Dict[str, Any]
    relevant_memories: List[MemoryItem]
    pattern_memories: List[MemoryItem]
    error_memories: List[MemoryItem]
    decision_memories: List[MemoryItem]
    performance_memories: List[MemoryItem]
    recall_trigger: RecallTrigger
    recall_timestamp: float
    similarity_scores: Dict[str, float]
    recommendations: List[str]

    def get_total_memories(self) -> int:
        """Get total count of all memories."""
        return (
            len(self.relevant_memories)
            + len(self.pattern_memories)
            + len(self.error_memories)
            + len(self.decision_memories)
            + len(self.performance_memories)
        )

    def get_memory_categories(self) -> Dict[str, int]:
        """Get count of memories by category."""
        all_memories = (
            self.relevant_memories
            + self.pattern_memories
            + self.error_memories
            + self.decision_memories
            + self.performance_memories
        )

        categories = {}
        for memory in all_memories:
            category = memory.category.value
            categories[category] = categories.get(category, 0) + 1

        return categories

    def get_top_recommendations(self, limit: int = 5) -> List[str]:
        """Get top recommendations based on memory analysis."""
        return self.recommendations[:limit]


@dataclass
class RecallConfig:
    """Configuration for memory recall operations."""

    max_recall_time_ms: float = 100.0  # Target recall time under 100ms
    max_memories_per_category: int = 10  # Limit memories per category
    similarity_threshold: float = 0.7  # Minimum similarity score
    enable_semantic_search: bool = True  # Use semantic search if available
    enable_pattern_matching: bool = True  # Use pattern matching
    enable_temporal_weighting: bool = True  # Weight recent memories higher
    max_memory_age_days: int = 90  # Maximum age of memories to consider
    performance_cache_size: int = 1000  # Cache size for performance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "max_recall_time_ms": self.max_recall_time_ms,
            "max_memories_per_category": self.max_memories_per_category,
            "similarity_threshold": self.similarity_threshold,
            "enable_semantic_search": self.enable_semantic_search,
            "enable_pattern_matching": self.enable_pattern_matching,
            "enable_temporal_weighting": self.enable_temporal_weighting,
            "max_memory_age_days": self.max_memory_age_days,
            "performance_cache_size": self.performance_cache_size,
        }


class MemoryContextEnhancer:
    """
    Intelligent memory retrieval and context enhancement system.

    This class automatically retrieves relevant memories before operations
    to enhance decision-making and prevent repeated mistakes. It provides
    fast, context-aware memory recall with semantic and pattern matching.
    """

    def __init__(
        self, memory_service: FlexibleMemoryService, config: Optional[RecallConfig] = None
    ):
        """
        Initialize the memory context enhancer.

        Args:
            memory_service: The unified memory service instance
            config: Configuration for recall operations
        """
        self.memory_service = memory_service
        self.config = config or RecallConfig()
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self.recall_stats = {
            "total_recalls": 0,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "average_recall_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "recalls_by_trigger": {trigger.value: 0 for trigger in RecallTrigger},
        }

        # Simple in-memory cache for performance
        self._recall_cache: Dict[str, Tuple[MemoryContext, float]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

        # Context analysis patterns
        self.operation_patterns = {
            "push": ["git", "commit", "deploy", "push", "release"],
            "deploy": ["deploy", "deployment", "environment", "service", "startup"],
            "publish": ["publish", "package", "registry", "version", "release"],
            "test": ["test", "testing", "qa", "validation", "quality"],
            "documentation": ["docs", "documentation", "readme", "guide"],
            "error": ["error", "exception", "failure", "bug", "fix"],
            "performance": ["performance", "optimization", "speed", "memory", "cpu"],
        }

    async def enhance_operation_context(
        self,
        project_name: str,
        operation_type: str,
        operation_context: Dict[str, Any],
        trigger: RecallTrigger = RecallTrigger.PRE_OPERATION,
    ) -> MemoryContext:
        """
        Enhance operation context with relevant memories.

        Args:
            project_name: Name of the project
            operation_type: Type of operation (push, deploy, publish, etc.)
            operation_context: Current operation context
            trigger: What triggered the memory recall

        Returns:
            MemoryContext: Enhanced context with relevant memories
        """
        start_time = time.time()
        self.recall_stats["total_recalls"] += 1
        self.recall_stats["recalls_by_trigger"][trigger.value] += 1

        try:
            # Check cache first
            cache_key = self._generate_cache_key(
                project_name, operation_type, operation_context, trigger
            )

            cached_context = self._get_cached_context(cache_key)
            if cached_context:
                self.recall_stats["cache_hits"] += 1
                self.logger.debug(f"Cache hit for operation {operation_type}")
                return cached_context

            self.recall_stats["cache_misses"] += 1

            # Perform intelligent memory recall
            memory_context = await self._perform_intelligent_recall(
                project_name, operation_type, operation_context, trigger
            )

            # Cache the result
            self._cache_context(cache_key, memory_context)

            # Update performance stats
            recall_time_ms = (time.time() - start_time) * 1000
            self._update_performance_stats(recall_time_ms, True)

            self.logger.info(
                f"Memory recall completed for {operation_type} in {recall_time_ms:.2f}ms "
                f"(found {memory_context.get_total_memories()} memories)"
            )

            return memory_context

        except Exception as e:
            # Update error stats
            recall_time_ms = (time.time() - start_time) * 1000
            self._update_performance_stats(recall_time_ms, False)

            self.logger.error(f"Memory recall failed for {operation_type}: {e}")

            # Return empty context on failure
            return MemoryContext(
                operation_type=operation_type,
                operation_context=operation_context,
                relevant_memories=[],
                pattern_memories=[],
                error_memories=[],
                decision_memories=[],
                performance_memories=[],
                recall_trigger=trigger,
                recall_timestamp=time.time(),
                similarity_scores={},
                recommendations=[],
            )

    async def _perform_intelligent_recall(
        self,
        project_name: str,
        operation_type: str,
        operation_context: Dict[str, Any],
        trigger: RecallTrigger,
    ) -> MemoryContext:
        """
        Perform intelligent memory recall based on operation context.

        Args:
            project_name: Name of the project
            operation_type: Type of operation
            operation_context: Current operation context
            trigger: What triggered the recall

        Returns:
            MemoryContext: Enhanced memory context
        """
        # Build search queries for different memory categories
        queries = self._build_search_queries(operation_type, operation_context)

        # Execute parallel searches for different memory types
        search_tasks = []

        # Pattern memories - successful operation patterns
        if self.config.enable_pattern_matching:
            pattern_query = MemoryQuery(
                query=queries["pattern"],
                category=MemoryCategory.PATTERN,
                limit=self.config.max_memories_per_category,
                similarity_threshold=self.config.similarity_threshold,
            )
            search_tasks.append(
                ("pattern", self.memory_service.search_memories(project_name, pattern_query))
            )

        # Error memories - previous error patterns and resolutions
        error_query = MemoryQuery(
            query=queries["error"],
            category=MemoryCategory.ERROR,
            limit=self.config.max_memories_per_category,
            similarity_threshold=self.config.similarity_threshold,
        )
        search_tasks.append(
            ("error", self.memory_service.search_memories(project_name, error_query))
        )

        # Project memories - architectural decisions and requirements
        project_query = MemoryQuery(
            query=queries["project"],
            category=MemoryCategory.PROJECT,
            limit=self.config.max_memories_per_category,
            similarity_threshold=self.config.similarity_threshold,
        )
        search_tasks.append(
            ("project", self.memory_service.search_memories(project_name, project_query))
        )

        # Team memories - coding standards and workflows
        team_query = MemoryQuery(
            query=queries["team"],
            category=MemoryCategory.TEAM,
            limit=self.config.max_memories_per_category,
            similarity_threshold=self.config.similarity_threshold,
        )
        search_tasks.append(("team", self.memory_service.search_memories(project_name, team_query)))

        # Execute all searches concurrently
        search_results = {}
        for category, task in search_tasks:
            try:
                search_results[category] = await task
            except Exception as e:
                self.logger.warning(f"Search failed for category {category}: {e}")
                search_results[category] = []

        # Categorize memories by type
        pattern_memories = search_results.get("pattern", [])
        error_memories = search_results.get("error", [])
        project_memories = search_results.get("project", [])
        team_memories = search_results.get("team", [])

        # Identify decision and performance memories from project memories
        decision_memories = [
            memory
            for memory in project_memories
            if self._is_decision_memory(memory, operation_context)
        ]

        performance_memories = [
            memory
            for memory in pattern_memories
            if self._is_performance_memory(memory, operation_context)
        ]

        # Combine all relevant memories
        all_memories = pattern_memories + error_memories + project_memories + team_memories
        relevant_memories = self._rank_memories_by_relevance(
            all_memories, operation_type, operation_context
        )

        # Calculate similarity scores
        similarity_scores = self._calculate_similarity_scores(
            relevant_memories, operation_type, operation_context
        )

        # Generate recommendations based on memories
        recommendations = self._generate_recommendations(
            relevant_memories, pattern_memories, error_memories, operation_type
        )

        return MemoryContext(
            operation_type=operation_type,
            operation_context=operation_context,
            relevant_memories=relevant_memories,
            pattern_memories=pattern_memories,
            error_memories=error_memories,
            decision_memories=decision_memories,
            performance_memories=performance_memories,
            recall_trigger=trigger,
            recall_timestamp=time.time(),
            similarity_scores=similarity_scores,
            recommendations=recommendations,
        )

    def _build_search_queries(
        self, operation_type: str, operation_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build search queries for different memory categories.

        Args:
            operation_type: Type of operation
            operation_context: Current operation context

        Returns:
            Dict[str, str]: Search queries by category
        """
        # Extract context keywords
        context_keywords = []

        # Add operation type patterns
        if operation_type in self.operation_patterns:
            context_keywords.extend(self.operation_patterns[operation_type])

        # Extract keywords from operation context
        for key, value in operation_context.items():
            if isinstance(value, str):
                context_keywords.append(value.lower())
            elif isinstance(value, list):
                context_keywords.extend([str(v).lower() for v in value])

        # Remove duplicates and empty strings
        context_keywords = list(set([k for k in context_keywords if k]))

        # Build category-specific queries
        base_query = " ".join(context_keywords[:10])  # Limit to avoid too long queries

        return {
            "pattern": f"{operation_type} {base_query} successful solution approach",
            "error": f"{operation_type} {base_query} error failure bug fix",
            "project": f"{operation_type} {base_query} architecture decision requirement",
            "team": f"{operation_type} {base_query} workflow standard practice",
        }

    def _is_decision_memory(self, memory: MemoryItem, operation_context: Dict[str, Any]) -> bool:
        """
        Check if a memory is related to strategic decisions.

        Args:
            memory: Memory item to check
            operation_context: Current operation context

        Returns:
            bool: True if memory is decision-related
        """
        decision_keywords = [
            "decision",
            "choice",
            "approach",
            "strategy",
            "architecture",
            "design",
            "requirement",
            "specification",
            "mandate",
        ]

        content_lower = memory.content.lower()
        return any(keyword in content_lower for keyword in decision_keywords)

    def _is_performance_memory(self, memory: MemoryItem, operation_context: Dict[str, Any]) -> bool:
        """
        Check if a memory is related to performance optimization.

        Args:
            memory: Memory item to check
            operation_context: Current operation context

        Returns:
            bool: True if memory is performance-related
        """
        performance_keywords = [
            "performance",
            "optimization",
            "speed",
            "memory",
            "cpu",
            "bottleneck",
            "latency",
            "throughput",
            "efficiency",
        ]

        content_lower = memory.content.lower()
        return any(keyword in content_lower for keyword in performance_keywords)

    def _rank_memories_by_relevance(
        self, memories: List[MemoryItem], operation_type: str, operation_context: Dict[str, Any]
    ) -> List[MemoryItem]:
        """
        Rank memories by relevance to current operation.

        Args:
            memories: List of memories to rank
            operation_type: Type of operation
            operation_context: Current operation context

        Returns:
            List[MemoryItem]: Memories ranked by relevance
        """
        # Simple relevance scoring based on content matching
        scored_memories = []

        for memory in memories:
            score = self._calculate_relevance_score(memory, operation_type, operation_context)
            scored_memories.append((memory, score))

        # Sort by score (descending) and return memories
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [
            memory for memory, _ in scored_memories[: self.config.max_memories_per_category * 2]
        ]

    def _calculate_relevance_score(
        self, memory: MemoryItem, operation_type: str, operation_context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score for a memory.

        Args:
            memory: Memory item
            operation_type: Type of operation
            operation_context: Current operation context

        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        score = 0.0

        # Operation type match
        if operation_type.lower() in memory.content.lower():
            score += 0.3

        # Tag matches
        for tag in memory.tags:
            if tag.lower() in operation_type.lower():
                score += 0.2

        # Context keyword matches
        context_text = " ".join([str(v) for v in operation_context.values()])
        content_lower = memory.content.lower()

        for word in context_text.lower().split():
            if len(word) > 3 and word in content_lower:
                score += 0.1

        # Temporal weighting - recent memories score higher
        if self.config.enable_temporal_weighting:
            age_seconds = memory.get_age_seconds()
            max_age_seconds = self.config.max_memory_age_days * 24 * 3600

            if age_seconds < max_age_seconds:
                temporal_weight = 1.0 - (age_seconds / max_age_seconds)
                score *= 0.5 + 0.5 * temporal_weight  # Weight between 0.5 and 1.0

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_similarity_scores(
        self, memories: List[MemoryItem], operation_type: str, operation_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate similarity scores for memories.

        Args:
            memories: List of memories
            operation_type: Type of operation
            operation_context: Current operation context

        Returns:
            Dict[str, float]: Similarity scores by memory ID
        """
        scores = {}

        for memory in memories:
            # Simple text-based similarity for now
            # In a production system, this could use semantic embeddings
            score = self._calculate_relevance_score(memory, operation_type, operation_context)
            scores[memory.id] = score

        return scores

    def _generate_recommendations(
        self,
        relevant_memories: List[MemoryItem],
        pattern_memories: List[MemoryItem],
        error_memories: List[MemoryItem],
        operation_type: str,
    ) -> List[str]:
        """
        Generate recommendations based on memory analysis.

        Args:
            relevant_memories: All relevant memories
            pattern_memories: Successful pattern memories
            error_memories: Error-related memories
            operation_type: Type of operation

        Returns:
            List[str]: List of recommendations
        """
        recommendations = []

        # Pattern-based recommendations
        if pattern_memories:
            recommendations.append(
                f"Consider applying successful {operation_type} patterns from previous operations"
            )

            # Extract specific patterns from successful memories
            for memory in pattern_memories[:3]:  # Top 3 patterns
                if "successful" in memory.content.lower():
                    recommendations.append(f"Review: {memory.content[:100]}...")

        # Error prevention recommendations
        if error_memories:
            recommendations.append(
                f"Be aware of common {operation_type} errors from previous operations"
            )

            # Extract specific error warnings
            for memory in error_memories[:2]:  # Top 2 errors
                if "error" in memory.content.lower() or "failure" in memory.content.lower():
                    recommendations.append(f"Avoid: {memory.content[:100]}...")

        # General recommendations based on operation type
        if operation_type == "push":
            recommendations.append("Ensure all tests pass before pushing")
            recommendations.append("Verify documentation is up to date")
        elif operation_type == "deploy":
            recommendations.append("Check environment configuration")
            recommendations.append("Verify service dependencies are available")
        elif operation_type == "publish":
            recommendations.append("Ensure version number is incremented")
            recommendations.append("Verify package metadata is complete")

        return recommendations[:10]  # Limit to 10 recommendations

    def _generate_cache_key(
        self,
        project_name: str,
        operation_type: str,
        operation_context: Dict[str, Any],
        trigger: RecallTrigger,
    ) -> str:
        """
        Generate cache key for memory context.

        Args:
            project_name: Name of the project
            operation_type: Type of operation
            operation_context: Current operation context
            trigger: Recall trigger

        Returns:
            str: Cache key
        """
        # Create a simple hash-like key from the context
        context_str = str(sorted(operation_context.items()))
        return f"{project_name}:{operation_type}:{trigger.value}:{hash(context_str)}"

    def _get_cached_context(self, cache_key: str) -> Optional[MemoryContext]:
        """
        Get cached memory context if still valid.

        Args:
            cache_key: Cache key

        Returns:
            Optional[MemoryContext]: Cached context if valid
        """
        if cache_key not in self._recall_cache:
            return None

        context, timestamp = self._recall_cache[cache_key]

        # Check if cache entry is still valid
        if time.time() - timestamp > self._cache_ttl_seconds:
            del self._recall_cache[cache_key]
            return None

        return context

    def _cache_context(self, cache_key: str, context: MemoryContext):
        """
        Cache memory context.

        Args:
            cache_key: Cache key
            context: Memory context to cache
        """
        # Implement LRU eviction if cache is full
        if len(self._recall_cache) >= self.config.performance_cache_size:
            # Remove oldest entry
            oldest_key = min(self._recall_cache.keys(), key=lambda k: self._recall_cache[k][1])
            del self._recall_cache[oldest_key]

        self._recall_cache[cache_key] = (context, time.time())

    def _update_performance_stats(self, recall_time_ms: float, success: bool):
        """
        Update performance statistics.

        Args:
            recall_time_ms: Time taken for recall in milliseconds
            success: Whether the recall was successful
        """
        if success:
            self.recall_stats["successful_recalls"] += 1
        else:
            self.recall_stats["failed_recalls"] += 1

        # Update average recall time
        total_recalls = self.recall_stats["total_recalls"]
        current_avg = self.recall_stats["average_recall_time_ms"]

        self.recall_stats["average_recall_time_ms"] = (
            current_avg * (total_recalls - 1) + recall_time_ms
        ) / total_recalls

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.

        Returns:
            Dict[str, Any]: Performance statistics
        """
        stats = self.recall_stats.copy()

        # Add cache statistics
        stats["cache_size"] = len(self._recall_cache)
        stats["cache_hit_rate"] = (
            self.recall_stats["cache_hits"]
            / max(self.recall_stats["cache_hits"] + self.recall_stats["cache_misses"], 1)
        ) * 100

        # Add success rate
        stats["success_rate"] = (
            self.recall_stats["successful_recalls"] / max(self.recall_stats["total_recalls"], 1)
        ) * 100

        return stats

    def reset_stats(self):
        """Reset performance statistics."""
        self.recall_stats = {
            "total_recalls": 0,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "average_recall_time_ms": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "recalls_by_trigger": {trigger.value: 0 for trigger in RecallTrigger},
        }
        self._recall_cache.clear()

    def clear_cache(self):
        """Clear the memory recall cache."""
        self._recall_cache.clear()
        self.logger.info("Memory recall cache cleared")

    def get_config(self) -> RecallConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, config: RecallConfig):
        """
        Update configuration.

        Args:
            config: New configuration
        """
        self.config = config
        self.logger.info("Memory recall configuration updated")
