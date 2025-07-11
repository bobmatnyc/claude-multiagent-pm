"""
Memory Recall Service

This module provides the main integration layer for the automatic memory recall
system. It orchestrates the interaction between memory context enhancement,
similarity matching, context building, and recommendation generation to provide
a unified interface for intelligent memory-driven operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

from .memory.services.unified_service import FlexibleMemoryService
from .memory.memory_context_enhancer import (
    MemoryContextEnhancer,
    MemoryContext,
    RecallTrigger,
    RecallConfig,
)
from .memory.similarity_matcher import SimilarityMatcher, MatchingConfig, SimilarityAlgorithm
from .memory.context_builder import ContextBuilder, EnrichedContext, ContextType, ContextTemplate
from .memory.recommendation_engine import (
    RecommendationEngine,
    RecommendationSet,
    RecommendationConfig,
    RecommendationType,
)
from .memory.interfaces.models import MemoryItem, MemoryQuery, MemoryCategory
from .memory.interfaces.exceptions import MemoryServiceError


@dataclass
class MemoryRecallConfig:
    """Configuration for the memory recall service."""

    # Memory context enhancer configuration
    recall_config: RecallConfig

    # Similarity matcher configuration
    matching_config: MatchingConfig

    # Recommendation engine configuration
    recommendation_config: RecommendationConfig

    # Service-level configuration
    enable_automatic_recall: bool = True
    enable_context_enrichment: bool = True
    enable_recommendations: bool = True
    max_concurrent_recalls: int = 5
    recall_timeout_seconds: float = 10.0
    cache_enabled: bool = True
    performance_monitoring: bool = True

    @classmethod
    def default(cls) -> "MemoryRecallConfig":
        """Create default configuration."""
        return cls(
            recall_config=RecallConfig(),
            matching_config=MatchingConfig(),
            recommendation_config=RecommendationConfig(),
        )

    def validate(self):
        """Validate configuration values."""
        if self.max_concurrent_recalls <= 0:
            raise ValueError("max_concurrent_recalls must be positive")
        if self.recall_timeout_seconds <= 0:
            raise ValueError("recall_timeout_seconds must be positive")

        # Validate sub-configurations
        self.matching_config.validate()
        self.recommendation_config.validate()


@dataclass
class MemoryRecallResult:
    """Complete result of memory recall operation."""

    success: bool
    memory_context: Optional[MemoryContext]
    enriched_context: Optional[EnrichedContext]
    recommendations: Optional[RecommendationSet]
    processing_time_ms: float
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "success": self.success,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
        }

        if self.memory_context:
            result["memory_context"] = {
                "operation_type": self.memory_context.operation_type,
                "recall_trigger": self.memory_context.recall_trigger.value,
                "total_memories": self.memory_context.get_total_memories(),
                "categories": self.memory_context.get_memory_categories(),
                "recommendations_count": len(self.memory_context.recommendations),
            }

        if self.enriched_context:
            result["enriched_context"] = self.enriched_context.to_dict()

        if self.recommendations:
            result["recommendations"] = self.recommendations.to_dict()

        return result

    def get_agent_summary(self) -> Dict[str, Any]:
        """Get a summary formatted for agent consumption."""
        if not self.success:
            return {"memory_available": False, "error": self.error_message, "recommendations": []}

        summary = {"memory_available": True, "processing_time_ms": self.processing_time_ms}

        if self.enriched_context:
            summary.update(self.enriched_context.get_agent_context())

        if self.recommendations:
            summary["structured_recommendations"] = [
                {
                    "type": rec.type.value,
                    "priority": rec.priority,
                    "title": rec.title,
                    "description": rec.description,
                    "confidence": rec.confidence,
                }
                for rec in self.recommendations.get_top_recommendations(5)
            ]

        return summary


class MemoryRecallService:
    """
    Unified memory recall service for intelligent memory-driven operations.

    This service orchestrates the complete memory recall pipeline:
    1. Memory context enhancement (intelligent retrieval)
    2. Context building (enrichment with analysis)
    3. Recommendation generation (memory-driven suggestions)

    It provides a simple interface for agents and framework components to
    leverage historical knowledge for better decision-making.
    """

    def __init__(
        self, memory_service: FlexibleMemoryService, config: Optional[MemoryRecallConfig] = None
    ):
        """
        Initialize the memory recall service.

        Args:
            memory_service: The unified memory service instance
            config: Configuration for recall operations
        """
        self.memory_service = memory_service
        self.config = config or MemoryRecallConfig.default()
        self.config.validate()
        self.logger = logging.getLogger(__name__)

        # Initialize component services
        self.similarity_matcher = SimilarityMatcher(self.config.matching_config)
        self.memory_enhancer = MemoryContextEnhancer(self.memory_service, self.config.recall_config)
        self.context_builder = ContextBuilder(self.similarity_matcher)
        self.recommendation_engine = RecommendationEngine(
            self.similarity_matcher, self.config.recommendation_config
        )

        # Service state
        self._initialized = False
        self._active_recalls = 0
        self._recall_semaphore = asyncio.Semaphore(self.config.max_concurrent_recalls)

        # Performance tracking
        self.service_stats = {
            "total_recalls": 0,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "recalls_by_trigger": {trigger.value: 0 for trigger in RecallTrigger},
            "recalls_by_context_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "average_recall_time_ms": 0.0,
            "concurrent_recalls_peak": 0,
            "cache_hit_rate": 0.0,
            "service_start_time": time.time(),
        }

    async def initialize(self) -> bool:
        """
        Initialize the memory recall service.

        Returns:
            bool: True if initialization was successful
        """
        if self._initialized:
            return True

        try:
            self.logger.info("Initializing memory recall service...")

            # Ensure memory service is initialized
            if not await self.memory_service.initialize():
                raise MemoryServiceError("Failed to initialize underlying memory service")

            self._initialized = True
            self.logger.info("Memory recall service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize memory recall service: {e}")
            self._initialized = False
            return False

    async def recall_for_operation(
        self,
        project_name: str,
        operation_type: str,
        operation_context: Dict[str, Any],
        context_type: ContextType = ContextType.AGENT_OPERATION,
        trigger: RecallTrigger = RecallTrigger.PRE_OPERATION,
        include_recommendations: bool = True,
    ) -> MemoryRecallResult:
        """
        Perform complete memory recall for an operation.

        Args:
            project_name: Name of the project
            operation_type: Type of operation (push, deploy, test, etc.)
            operation_context: Current operation context
            context_type: Type of context to build
            trigger: What triggered the memory recall
            include_recommendations: Whether to generate recommendations

        Returns:
            MemoryRecallResult: Complete recall result
        """
        if not self._initialized:
            raise MemoryServiceError("Memory recall service not initialized")

        start_time = time.time()
        self.service_stats["total_recalls"] += 1
        self.service_stats["recalls_by_trigger"][trigger.value] += 1
        self.service_stats["recalls_by_context_type"][context_type.value] += 1

        async with self._recall_semaphore:
            self._active_recalls += 1
            self.service_stats["concurrent_recalls_peak"] = max(
                self.service_stats["concurrent_recalls_peak"], self._active_recalls
            )

            try:
                # Add timeout protection
                result = await asyncio.wait_for(
                    self._perform_complete_recall(
                        project_name,
                        operation_type,
                        operation_context,
                        context_type,
                        trigger,
                        include_recommendations,
                    ),
                    timeout=self.config.recall_timeout_seconds,
                )

                # Update success stats
                processing_time_ms = (time.time() - start_time) * 1000
                self._update_recall_stats(processing_time_ms, True)
                result.processing_time_ms = processing_time_ms

                self.logger.info(
                    f"Memory recall completed for {operation_type} in {processing_time_ms:.2f}ms"
                )

                return result

            except asyncio.TimeoutError:
                # Handle timeout
                processing_time_ms = (time.time() - start_time) * 1000
                self._update_recall_stats(processing_time_ms, False)

                error_msg = f"Memory recall timed out after {self.config.recall_timeout_seconds}s"
                self.logger.warning(error_msg)

                return MemoryRecallResult(
                    success=False,
                    memory_context=None,
                    enriched_context=None,
                    recommendations=None,
                    processing_time_ms=processing_time_ms,
                    error_message=error_msg,
                )

            except Exception as e:
                # Handle general errors
                processing_time_ms = (time.time() - start_time) * 1000
                self._update_recall_stats(processing_time_ms, False)

                error_msg = f"Memory recall failed: {str(e)}"
                self.logger.error(error_msg)

                return MemoryRecallResult(
                    success=False,
                    memory_context=None,
                    enriched_context=None,
                    recommendations=None,
                    processing_time_ms=processing_time_ms,
                    error_message=error_msg,
                )

            finally:
                self._active_recalls -= 1

    async def _perform_complete_recall(
        self,
        project_name: str,
        operation_type: str,
        operation_context: Dict[str, Any],
        context_type: ContextType,
        trigger: RecallTrigger,
        include_recommendations: bool,
    ) -> MemoryRecallResult:
        """Perform the complete memory recall pipeline."""

        # Step 1: Enhance operation context with relevant memories
        memory_context = await self.memory_enhancer.enhance_operation_context(
            project_name, operation_type, operation_context, trigger
        )

        # Step 2: Build enriched context if enabled
        enriched_context = None
        if self.config.enable_context_enrichment:
            enriched_context = self.context_builder.build_context(
                context_type, operation_context, memory_context
            )

        # Step 3: Generate recommendations if enabled and requested
        recommendations = None
        if self.config.enable_recommendations and include_recommendations and enriched_context:
            recommendations = self.recommendation_engine.generate_recommendations(enriched_context)

        return MemoryRecallResult(
            success=True,
            memory_context=memory_context,
            enriched_context=enriched_context,
            recommendations=recommendations,
            processing_time_ms=0.0,  # Will be set by caller
        )

    async def recall_for_error_resolution(
        self,
        project_name: str,
        error_type: str,
        error_message: str,
        error_context: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecallResult:
        """
        Specialized recall for error resolution scenarios.

        Args:
            project_name: Name of the project
            error_type: Type of error
            error_message: Error message
            error_context: Additional error context

        Returns:
            MemoryRecallResult: Recall result with error-specific insights
        """
        operation_context = {
            "error_type": error_type,
            "error_message": error_message,
            "error_context": error_context or {},
        }

        return await self.recall_for_operation(
            project_name=project_name,
            operation_type="error_resolution",
            operation_context=operation_context,
            context_type=ContextType.ERROR_RESOLUTION,
            trigger=RecallTrigger.ERROR_PREVENTION,
            include_recommendations=True,
        )

    async def recall_for_performance_optimization(
        self,
        project_name: str,
        performance_metric: str,
        current_performance: str,
        target_performance: Optional[str] = None,
        optimization_context: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecallResult:
        """
        Specialized recall for performance optimization scenarios.

        Args:
            project_name: Name of the project
            performance_metric: Performance metric to optimize
            current_performance: Current performance level
            target_performance: Target performance level
            optimization_context: Additional optimization context

        Returns:
            MemoryRecallResult: Recall result with performance insights
        """
        operation_context = {
            "performance_metric": performance_metric,
            "current_performance": current_performance,
            "target_performance": target_performance,
            "optimization_context": optimization_context or {},
        }

        return await self.recall_for_operation(
            project_name=project_name,
            operation_type="performance_optimization",
            operation_context=operation_context,
            context_type=ContextType.PERFORMANCE_OPT,
            trigger=RecallTrigger.DECISION_SUPPORT,
            include_recommendations=True,
        )

    async def recall_for_decision_support(
        self,
        project_name: str,
        decision_type: str,
        decision_context: Dict[str, Any],
        alternatives: Optional[List[str]] = None,
    ) -> MemoryRecallResult:
        """
        Specialized recall for decision support scenarios.

        Args:
            project_name: Name of the project
            decision_type: Type of decision
            decision_context: Decision context
            alternatives: Available alternatives

        Returns:
            MemoryRecallResult: Recall result with decision insights
        """
        operation_context = {
            "decision_type": decision_type,
            "decision_context": decision_context,
            "alternatives": alternatives or [],
        }

        return await self.recall_for_operation(
            project_name=project_name,
            operation_type="decision_support",
            operation_context=operation_context,
            context_type=ContextType.DECISION_SUPPORT,
            trigger=RecallTrigger.DECISION_SUPPORT,
            include_recommendations=True,
        )

    async def recall_for_workflow_command(
        self, project_name: str, command_type: str, command_context: Dict[str, Any]
    ) -> MemoryRecallResult:
        """
        Specialized recall for workflow commands (push, deploy, publish).

        Args:
            project_name: Name of the project
            command_type: Type of command (push, deploy, publish)
            command_context: Command context

        Returns:
            MemoryRecallResult: Recall result with workflow insights
        """
        operation_context = {"command_type": command_type, **command_context}

        return await self.recall_for_operation(
            project_name=project_name,
            operation_type=command_type,
            operation_context=operation_context,
            context_type=ContextType.WORKFLOW_COMMAND,
            trigger=RecallTrigger.WORKFLOW_CONTEXT,
            include_recommendations=True,
        )

    async def get_similar_operations(
        self,
        project_name: str,
        operation_context: Dict[str, Any],
        similarity_threshold: float = 0.7,
        limit: int = 10,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Find similar operations from memory.

        Args:
            project_name: Name of the project
            operation_context: Operation context to match
            similarity_threshold: Minimum similarity threshold
            limit: Maximum number of results

        Returns:
            List[Tuple[MemoryItem, float]]: Similar operations with scores
        """
        if not self._initialized:
            raise MemoryServiceError("Memory recall service not initialized")

        # Build query from operation context
        query_text = " ".join([str(v) for v in operation_context.values()])

        # Search for relevant memories
        memories = await self.memory_service.search_memories(
            project_name,
            MemoryQuery(
                query=query_text,
                limit=limit * 2,  # Get more to filter
                similarity_threshold=similarity_threshold
                * 0.8,  # Lower threshold for initial search
            ),
        )

        # Rank by similarity
        similar_operations = self.similarity_matcher.rank_memories_by_similarity(
            query_text, memories, operation_context, limit=limit
        )

        # Filter by final threshold
        filtered_operations = [
            (memory, result.similarity_score)
            for memory, result in similar_operations
            if result.similarity_score >= similarity_threshold
        ]

        return filtered_operations

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive service health information.

        Returns:
            Dict[str, Any]: Service health data
        """
        health_data = {
            "service_initialized": self._initialized,
            "active_recalls": self._active_recalls,
            "configuration": {
                "max_concurrent_recalls": self.config.max_concurrent_recalls,
                "recall_timeout_seconds": self.config.recall_timeout_seconds,
                "automatic_recall_enabled": self.config.enable_automatic_recall,
                "context_enrichment_enabled": self.config.enable_context_enrichment,
                "recommendations_enabled": self.config.enable_recommendations,
            },
            "statistics": self.service_stats.copy(),
            "component_health": {},
        }

        # Get component health
        try:
            health_data["component_health"][
                "memory_service"
            ] = await self.memory_service.get_service_health()
        except Exception as e:
            health_data["component_health"]["memory_service"] = {"error": str(e)}

        # Get component performance stats
        health_data["component_performance"] = {
            "memory_enhancer": self.memory_enhancer.get_performance_stats(),
            "similarity_matcher": self.similarity_matcher.get_performance_stats(),
            "context_builder": self.context_builder.get_performance_stats(),
            "recommendation_engine": self.recommendation_engine.get_performance_stats(),
        }

        return health_data

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.service_stats.copy()

        # Calculate derived metrics
        total_recalls = self.service_stats["total_recalls"]
        if total_recalls > 0:
            stats["success_rate"] = (self.service_stats["successful_recalls"] / total_recalls) * 100
        else:
            stats["success_rate"] = 0.0

        # Add component stats
        stats["component_stats"] = {
            "memory_enhancer": self.memory_enhancer.get_performance_stats(),
            "similarity_matcher": self.similarity_matcher.get_performance_stats(),
            "context_builder": self.context_builder.get_performance_stats(),
            "recommendation_engine": self.recommendation_engine.get_performance_stats(),
        }

        return stats

    def _update_recall_stats(self, processing_time_ms: float, success: bool):
        """Update recall statistics."""
        if success:
            self.service_stats["successful_recalls"] += 1
        else:
            self.service_stats["failed_recalls"] += 1

        # Update average recall time
        total_recalls = self.service_stats["total_recalls"]
        current_avg = self.service_stats["average_recall_time_ms"]

        self.service_stats["average_recall_time_ms"] = (
            current_avg * (total_recalls - 1) + processing_time_ms
        ) / total_recalls

        # Update cache hit rate (approximation from components)
        memory_stats = self.memory_enhancer.get_performance_stats()
        if "cache_hit_rate" in memory_stats:
            self.service_stats["cache_hit_rate"] = memory_stats["cache_hit_rate"]

    def reset_stats(self):
        """Reset all performance statistics."""
        self.service_stats = {
            "total_recalls": 0,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "recalls_by_trigger": {trigger.value: 0 for trigger in RecallTrigger},
            "recalls_by_context_type": {ctx_type.value: 0 for ctx_type in ContextType},
            "average_recall_time_ms": 0.0,
            "concurrent_recalls_peak": 0,
            "cache_hit_rate": 0.0,
            "service_start_time": time.time(),
        }

        # Reset component stats
        self.memory_enhancer.reset_stats()
        self.similarity_matcher.reset_stats()
        self.context_builder.reset_stats()
        self.recommendation_engine.reset_stats()

    def clear_caches(self):
        """Clear all component caches."""
        if self.config.cache_enabled:
            self.memory_enhancer.clear_cache()
            self.similarity_matcher.clear_cache()
            self.logger.info("All memory recall caches cleared")

    def get_config(self) -> MemoryRecallConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, config: MemoryRecallConfig):
        """
        Update service configuration.

        Args:
            config: New configuration
        """
        config.validate()
        old_config = self.config
        self.config = config

        # Update component configurations
        self.memory_enhancer.update_config(config.recall_config)
        self.similarity_matcher.update_config(config.matching_config)
        self.recommendation_engine.update_config(config.recommendation_config)

        # Update semaphore if concurrent limit changed
        if old_config.max_concurrent_recalls != config.max_concurrent_recalls:
            self._recall_semaphore = asyncio.Semaphore(config.max_concurrent_recalls)

        self.logger.info("Memory recall service configuration updated")

    async def cleanup(self):
        """Cleanup service resources."""
        self.logger.info("Cleaning up memory recall service...")

        # Wait for active recalls to complete
        while self._active_recalls > 0:
            await asyncio.sleep(0.1)

        # Clear caches
        self.clear_caches()

        # Cleanup memory service
        await self.memory_service.cleanup()

        self._initialized = False
        self.logger.info("Memory recall service cleanup completed")

    @asynccontextmanager
    async def recall_context(self, **kwargs):
        """
        Async context manager for memory recall operations.

        Usage:
            async with recall_service.recall_context() as service:
                result = await service.recall_for_operation(...)
        """
        if not self._initialized:
            await self.initialize()

        try:
            yield self
        finally:
            # Context cleanup if needed
            pass

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MemoryRecallService(initialized={self._initialized}, "
            f"active_recalls={self._active_recalls}, "
            f"total_recalls={self.service_stats['total_recalls']})"
        )
