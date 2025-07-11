"""
Comprehensive tests for the memory recall system.

This module tests the automatic memory recall system including:
- Memory context enhancement
- Similarity matching
- Context building
- Recommendation generation
- Performance optimization
- Integration with existing framework components
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from claude_pm.services.memory import (
    FlexibleMemoryService,
    MemoryRecallService,
    MemoryRecallConfig,
    MemoryItem,
    MemoryCategory,
    MemoryQuery,
)
from claude_pm.services.memory.memory_context_enhancer import (
    MemoryContextEnhancer,
    RecallTrigger,
    RecallConfig,
)
from claude_pm.services.memory.similarity_matcher import (
    SimilarityMatcher,
    SimilarityAlgorithm,
    MatchingConfig,
)
from claude_pm.services.memory.context_builder import ContextBuilder, ContextType
from claude_pm.services.memory.recommendation_engine import RecommendationEngine, RecommendationType
from claude_pm.services.memory.performance_optimizer import (
    PerformanceOptimizer,
    OptimizationStrategy,
)


class TestMemoryContextEnhancer:
    """Test memory context enhancement functionality."""

    @pytest.fixture
    async def mock_memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=FlexibleMemoryService)
        service.search_memories = AsyncMock(
            return_value=[
                MemoryItem(
                    id="test-1",
                    content="Successful deployment to production",
                    category=MemoryCategory.PATTERN,
                    tags=["deploy", "production", "successful"],
                    metadata={"outcome": "success"},
                    created_at="2025-07-01T00:00:00Z",
                    updated_at="2025-07-01T00:00:00Z",
                    project_name="test_project",
                ),
                MemoryItem(
                    id="test-2",
                    content="Error during deployment: timeout",
                    category=MemoryCategory.ERROR,
                    tags=["deploy", "error", "timeout"],
                    metadata={"error_type": "timeout"},
                    created_at="2025-07-02T00:00:00Z",
                    updated_at="2025-07-02T00:00:00Z",
                    project_name="test_project",
                ),
            ]
        )
        return service

    @pytest.fixture
    def enhancer(self, mock_memory_service):
        """Create memory context enhancer."""
        config = RecallConfig(max_recall_time_ms=50.0)
        return MemoryContextEnhancer(mock_memory_service, config)

    @pytest.mark.asyncio
    async def test_enhance_operation_context(self, enhancer):
        """Test operation context enhancement."""
        result = await enhancer.enhance_operation_context(
            project_name="test_project",
            operation_type="deploy",
            operation_context={"environment": "production"},
            trigger=RecallTrigger.PRE_OPERATION,
        )

        assert result.operation_type == "deploy"
        assert result.recall_trigger == RecallTrigger.PRE_OPERATION
        assert result.get_total_memories() > 0
        assert len(result.recommendations) > 0
        assert result.recall_timestamp > 0

    @pytest.mark.asyncio
    async def test_caching_behavior(self, enhancer):
        """Test that caching improves performance."""
        # First call
        start_time = time.time()
        result1 = await enhancer.enhance_operation_context(
            "test_project", "deploy", {"env": "prod"}, RecallTrigger.PRE_OPERATION
        )
        first_call_time = time.time() - start_time

        # Second identical call should be faster due to caching
        start_time = time.time()
        result2 = await enhancer.enhance_operation_context(
            "test_project", "deploy", {"env": "prod"}, RecallTrigger.PRE_OPERATION
        )
        second_call_time = time.time() - start_time

        # Cache should make second call faster
        assert second_call_time < first_call_time
        assert result1.get_total_memories() == result2.get_total_memories()

    def test_performance_stats(self, enhancer):
        """Test performance statistics tracking."""
        stats = enhancer.get_performance_stats()

        assert "total_recalls" in stats
        assert "successful_recalls" in stats
        assert "cache_hit_rate" in stats
        assert "recalls_by_trigger" in stats


class TestSimilarityMatcher:
    """Test similarity matching functionality."""

    @pytest.fixture
    def sample_memories(self):
        """Create sample memories for testing."""
        return [
            MemoryItem(
                id="mem-1",
                content="Deployment to production was successful after fixing timeout issues",
                category=MemoryCategory.PATTERN,
                tags=["deploy", "production", "success"],
                metadata={},
                created_at="2025-07-01T00:00:00Z",
                updated_at="2025-07-01T00:00:00Z",
                project_name="test",
            ),
            MemoryItem(
                id="mem-2",
                content="Error during build process: missing dependencies",
                category=MemoryCategory.ERROR,
                tags=["build", "error", "dependencies"],
                metadata={},
                created_at="2025-07-02T00:00:00Z",
                updated_at="2025-07-02T00:00:00Z",
                project_name="test",
            ),
        ]

    @pytest.fixture
    def matcher(self):
        """Create similarity matcher."""
        config = MatchingConfig(min_similarity_threshold=0.1)
        return SimilarityMatcher(config)

    def test_cosine_similarity(self, matcher, sample_memories):
        """Test cosine similarity calculation."""
        query = "production deployment success"
        memory = sample_memories[0]

        result = matcher.calculate_similarity(query, memory, algorithm=SimilarityAlgorithm.COSINE)

        assert result.memory_id == "mem-1"
        assert result.algorithm_used == SimilarityAlgorithm.COSINE
        assert 0.0 <= result.similarity_score <= 1.0
        assert result.confidence > 0.0

    def test_jaccard_similarity(self, matcher, sample_memories):
        """Test Jaccard similarity calculation."""
        query = "deployment production"
        memory = sample_memories[0]

        result = matcher.calculate_similarity(query, memory, algorithm=SimilarityAlgorithm.JACCARD)

        assert result.algorithm_used == SimilarityAlgorithm.JACCARD
        assert 0.0 <= result.similarity_score <= 1.0

    def test_hybrid_similarity(self, matcher, sample_memories):
        """Test hybrid similarity calculation."""
        query = "production deployment"
        memory = sample_memories[0]

        result = matcher.calculate_similarity(query, memory, algorithm=SimilarityAlgorithm.HYBRID)

        assert result.algorithm_used == SimilarityAlgorithm.HYBRID
        assert "cosine_score" in result.match_details
        assert "semantic_score" in result.match_details
        assert "pattern_score" in result.match_details

    def test_rank_memories_by_similarity(self, matcher, sample_memories):
        """Test memory ranking by similarity."""
        query = "deployment to production"

        ranked = matcher.rank_memories_by_similarity(query, sample_memories, limit=2)

        assert len(ranked) <= 2
        assert all(isinstance(item, tuple) for item in ranked)
        assert all(len(item) == 2 for item in ranked)

        # Should be sorted by similarity score (descending)
        if len(ranked) > 1:
            assert ranked[0][1].similarity_score >= ranked[1][1].similarity_score

    def test_performance_caching(self, matcher, sample_memories):
        """Test that similarity calculations are cached."""
        query = "test query"
        memory = sample_memories[0]

        # First calculation
        result1 = matcher.calculate_similarity(query, memory)

        # Second identical calculation should hit cache
        result2 = matcher.calculate_similarity(query, memory)

        assert result1.similarity_score == result2.similarity_score

        # Check cache stats
        stats = matcher.get_performance_stats()
        assert stats["cache_hits"] > 0


class TestContextBuilder:
    """Test context building functionality."""

    @pytest.fixture
    def mock_similarity_matcher(self):
        """Create mock similarity matcher."""
        matcher = Mock(spec=SimilarityMatcher)
        return matcher

    @pytest.fixture
    def context_builder(self, mock_similarity_matcher):
        """Create context builder."""
        return ContextBuilder(mock_similarity_matcher)

    @pytest.fixture
    def sample_memory_context(self):
        """Create sample memory context."""
        from claude_pm.services.memory.memory_context_enhancer import MemoryContext

        memories = [
            MemoryItem(
                id="ctx-1",
                content="Successful API deployment with 99.9% uptime",
                category=MemoryCategory.PATTERN,
                tags=["api", "deployment", "success"],
                metadata={},
                created_at="2025-07-01T00:00:00Z",
                updated_at="2025-07-01T00:00:00Z",
                project_name="test",
            )
        ]

        return MemoryContext(
            operation_type="deploy",
            operation_context={"service": "api", "environment": "production"},
            relevant_memories=memories,
            pattern_memories=memories,
            error_memories=[],
            decision_memories=[],
            performance_memories=[],
            recall_trigger=RecallTrigger.PRE_OPERATION,
            recall_timestamp=time.time(),
            similarity_scores={"ctx-1": 0.8},
            recommendations=["Apply successful deployment patterns"],
        )

    def test_build_agent_operation_context(self, context_builder, sample_memory_context):
        """Test building context for agent operations."""
        operation_context = {
            "operation_type": "deploy",
            "agent_type": "ops",
            "target_files": ["app.py", "config.yaml"],
        }

        enriched_context = context_builder.build_context(
            ContextType.AGENT_OPERATION, operation_context, sample_memory_context
        )

        assert enriched_context.context_type == ContextType.AGENT_OPERATION
        assert enriched_context.confidence_score > 0.0
        assert len(enriched_context.recommendations) > 0
        assert enriched_context.processing_time_ms >= 0.0

    def test_build_workflow_command_context(self, context_builder, sample_memory_context):
        """Test building context for workflow commands."""
        operation_context = {
            "command_type": "deploy",
            "branch_name": "main",
            "environment": "production",
        }

        enriched_context = context_builder.build_context(
            ContextType.WORKFLOW_COMMAND, operation_context, sample_memory_context
        )

        assert enriched_context.context_type == ContextType.WORKFLOW_COMMAND
        assert "memory_insights" in enriched_context.enriched_data
        assert "temporal_context" in enriched_context.enriched_data

    def test_context_validation(self, context_builder):
        """Test context template validation."""
        template = context_builder.get_context_template(ContextType.AGENT_OPERATION)

        # Valid context
        valid_context = {"operation_type": "deploy", "agent_type": "ops"}
        is_valid, missing = template.validate_context(valid_context)
        assert is_valid
        assert len(missing) == 0

        # Invalid context
        invalid_context = {"operation_type": "deploy"}  # Missing agent_type
        is_valid, missing = template.validate_context(invalid_context)
        assert not is_valid
        assert "agent_type" in missing

    def test_get_agent_context(self, context_builder, sample_memory_context):
        """Test agent context formatting."""
        operation_context = {"operation_type": "deploy", "agent_type": "ops"}

        enriched_context = context_builder.build_context(
            ContextType.AGENT_OPERATION, operation_context, sample_memory_context
        )

        agent_context = enriched_context.get_agent_context()

        assert "operation_context" in agent_context
        assert "relevant_memories" in agent_context
        assert "recommendations" in agent_context
        assert "confidence" in agent_context


class TestRecommendationEngine:
    """Test recommendation generation functionality."""

    @pytest.fixture
    def mock_similarity_matcher(self):
        """Create mock similarity matcher."""
        return Mock(spec=SimilarityMatcher)

    @pytest.fixture
    def recommendation_engine(self, mock_similarity_matcher):
        """Create recommendation engine."""
        return RecommendationEngine(mock_similarity_matcher)

    @pytest.fixture
    def sample_enriched_context(self):
        """Create sample enriched context."""
        from claude_pm.services.memory.memory_context_enhancer import MemoryContext
        from claude_pm.services.memory.context_builder import EnrichedContext

        memories = [
            MemoryItem(
                id="rec-1",
                content="Previous deployment failed due to missing environment variables",
                category=MemoryCategory.ERROR,
                tags=["deployment", "error", "environment"],
                metadata={},
                created_at="2025-07-01T00:00:00Z",
                updated_at="2025-07-01T00:00:00Z",
                project_name="test",
            )
        ]

        memory_context = MemoryContext(
            operation_type="deploy",
            operation_context={"environment": "production"},
            relevant_memories=memories,
            pattern_memories=[],
            error_memories=memories,
            decision_memories=[],
            performance_memories=[],
            recall_trigger=RecallTrigger.PRE_OPERATION,
            recall_timestamp=time.time(),
            similarity_scores={"rec-1": 0.9},
            recommendations=[],
        )

        return EnrichedContext(
            context_type=ContextType.WORKFLOW_COMMAND,
            original_context={"command_type": "deploy"},
            memory_context=memory_context,
            enriched_data={},
            analysis_summary={"error_ratio": 0.5, "success_ratio": 0.3},
            recommendations=[],
            warnings=[],
            confidence_score=0.8,
            build_timestamp=time.time(),
            processing_time_ms=50.0,
        )

    def test_generate_error_prevention_recommendations(
        self, recommendation_engine, sample_enriched_context
    ):
        """Test error prevention recommendation generation."""
        recommendations = recommendation_engine.generate_recommendations(sample_enriched_context)

        assert recommendations.total_memories_analyzed > 0
        assert len(recommendations.recommendations) > 0

        # Should have error prevention recommendations
        error_prevention_recs = recommendations.get_by_type(RecommendationType.ERROR_PREVENTION)
        assert len(error_prevention_recs) > 0

        # Check recommendation structure
        rec = error_prevention_recs[0]
        assert rec.type == RecommendationType.ERROR_PREVENTION
        assert rec.confidence > 0.0
        assert len(rec.supporting_memories) > 0

    def test_workflow_command_recommendations(self, recommendation_engine, sample_enriched_context):
        """Test workflow command specific recommendations."""
        recommendations = recommendation_engine.generate_recommendations(sample_enriched_context)

        # Should have operation guidance recommendations
        guidance_recs = recommendations.get_by_type(RecommendationType.OPERATION_GUIDANCE)
        assert len(guidance_recs) >= 0  # May or may not have depending on context

        # Check recommendation ranking
        top_recs = recommendations.get_top_recommendations(3)
        assert len(top_recs) <= 3

        # Should be sorted by score
        if len(top_recs) > 1:
            scores = [rec.get_score() for rec in top_recs]
            assert scores == sorted(scores, reverse=True)

    def test_recommendation_filtering(self, recommendation_engine, sample_enriched_context):
        """Test recommendation filtering and deduplication."""
        recommendations = recommendation_engine.generate_recommendations(sample_enriched_context)

        # All recommendations should meet confidence threshold
        for rec in recommendations.recommendations:
            assert rec.confidence >= recommendation_engine.config.min_confidence_threshold

        # No duplicate recommendations (same type and similar title)
        titles = [rec.title for rec in recommendations.recommendations]
        assert len(titles) == len(set(titles))  # No exact duplicates


class TestMemoryRecallService:
    """Test the integrated memory recall service."""

    @pytest.fixture
    async def mock_memory_service(self):
        """Create mock memory service."""
        service = Mock(spec=FlexibleMemoryService)
        service.initialize = AsyncMock(return_value=True)
        service.search_memories = AsyncMock(return_value=[])
        service.get_service_health = AsyncMock(return_value={"status": "healthy"})
        service.cleanup = AsyncMock()
        return service

    @pytest.fixture
    async def recall_service(self, mock_memory_service):
        """Create memory recall service."""
        config = MemoryRecallConfig.default()
        service = MemoryRecallService(mock_memory_service, config)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_recall_for_operation(self, recall_service):
        """Test basic operation recall."""
        result = await recall_service.recall_for_operation(
            project_name="test_project",
            operation_type="deploy",
            operation_context={"environment": "production"},
        )

        assert result.success
        assert result.memory_context is not None
        assert result.processing_time_ms > 0.0

    @pytest.mark.asyncio
    async def test_recall_for_error_resolution(self, recall_service):
        """Test error resolution recall."""
        result = await recall_service.recall_for_error_resolution(
            project_name="test_project",
            error_type="timeout",
            error_message="Connection timeout after 30 seconds",
        )

        assert result.success
        assert result.memory_context.recall_trigger == RecallTrigger.ERROR_PREVENTION

    @pytest.mark.asyncio
    async def test_recall_timeout_handling(self, recall_service):
        """Test recall timeout handling."""
        # Configure very short timeout
        config = recall_service.get_config()
        config.recall_timeout_seconds = 0.001  # 1ms timeout
        recall_service.update_config(config)

        result = await recall_service.recall_for_operation(
            "test_project", "deploy", {"env": "prod"}
        )

        # Should handle timeout gracefully
        assert not result.success
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_concurrent_recalls(self, recall_service):
        """Test concurrent recall handling."""
        # Start multiple concurrent recalls
        tasks = []
        for i in range(3):
            task = recall_service.recall_for_operation(f"project_{i}", "deploy", {"id": i})
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(result.success for result in results)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, recall_service):
        """Test service health monitoring."""
        health = await recall_service.get_service_health()

        assert "service_initialized" in health
        assert "configuration" in health
        assert "statistics" in health
        assert "component_health" in health
        assert health["service_initialized"] is True


class TestPerformanceOptimizer:
    """Test performance optimization functionality."""

    @pytest.fixture
    async def mock_recall_service(self):
        """Create mock recall service."""
        service = Mock(spec=MemoryRecallService)
        service.get_performance_stats = Mock(
            return_value={
                "total_recalls": 100,
                "successful_recalls": 95,
                "failed_recalls": 5,
                "average_recall_time_ms": 150.0,
                "service_start_time": time.time() - 3600,
            }
        )
        service.get_config = Mock(return_value=MemoryRecallConfig.default())
        service.update_config = Mock()
        return service

    @pytest.fixture
    def optimizer(self, mock_recall_service):
        """Create performance optimizer."""
        return PerformanceOptimizer(mock_recall_service)

    @pytest.mark.asyncio
    async def test_collect_metrics(self, optimizer):
        """Test metrics collection."""
        # Add some performance data
        optimizer.record_recall_performance(80.0, True, True)
        optimizer.record_recall_performance(120.0, True, False)
        optimizer.record_recall_performance(200.0, False, False)

        metrics = await optimizer.collect_metrics()

        assert metrics.average_recall_time_ms > 0.0
        assert 0.0 <= metrics.success_rate <= 1.0
        assert 0.0 <= metrics.cache_hit_rate <= 1.0

    def test_optimization_recommendations(self, optimizer):
        """Test optimization recommendation generation."""
        from claude_pm.services.memory.performance_optimizer import PerformanceMetrics

        # Create metrics that need optimization
        metrics = PerformanceMetrics(
            average_recall_time_ms=150.0,  # Above target
            cache_hit_rate=0.1,  # Below target
            success_rate=0.8,  # Below target
        )

        recommendations = optimizer.get_optimization_recommendations(metrics)

        assert len(recommendations) > 0

        # Should have cache optimization recommendation
        cache_opt = [
            r for r in recommendations if r.strategy == OptimizationStrategy.CACHE_OPTIMIZATION
        ]
        assert len(cache_opt) > 0

        # Should have query optimization recommendation
        query_opt = [
            r for r in recommendations if r.strategy == OptimizationStrategy.QUERY_OPTIMIZATION
        ]
        assert len(query_opt) > 0

    def test_performance_targets(self, optimizer):
        """Test performance target evaluation."""
        from claude_pm.services.memory.performance_optimizer import PerformanceMetrics

        # Good metrics
        good_metrics = PerformanceMetrics(
            average_recall_time_ms=80.0,
            p95_recall_time_ms=150.0,
            success_rate=0.98,
            cache_hit_rate=0.4,
        )
        assert good_metrics.meets_performance_targets()

        # Bad metrics
        bad_metrics = PerformanceMetrics(
            average_recall_time_ms=200.0,  # Too slow
            success_rate=0.85,  # Too low
            cache_hit_rate=0.1,  # Too low
        )
        assert not bad_metrics.meets_performance_targets()

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, optimizer):
        """Test monitoring start/stop lifecycle."""
        # Start monitoring
        await optimizer.start_monitoring()
        assert optimizer._monitoring_task is not None

        # Stop monitoring
        await optimizer.stop_monitoring()
        assert optimizer._monitoring_task is None


class TestIntegration:
    """Test integration between components."""

    @pytest.mark.asyncio
    async def test_end_to_end_recall(self):
        """Test complete end-to-end recall workflow."""
        # Create in-memory backend for testing
        # # from claude_pm.services.memory.backends.memory_backend import InMemoryBackend  # InMemory backend removed  # InMemory backend removed
        from claude_pm.services.memory.services.unified_service import FlexibleMemoryService

        # Setup memory service with in-memory backend
        memory_service = FlexibleMemoryService(
            {"fallback_chain": ["sqlite"], "memory_enabled": True}
        )
        await memory_service.initialize()

        # Add test memories
        await memory_service.add_memory(
            "test_project",
            "Successful deployment to production with blue-green strategy",
            MemoryCategory.PATTERN,
            tags=["deploy", "production", "blue-green"],
            metadata={"outcome": "success", "strategy": "blue-green"},
        )

        await memory_service.add_memory(
            "test_project",
            "Deployment failed due to database migration timeout",
            MemoryCategory.ERROR,
            tags=["deploy", "error", "database", "timeout"],
            metadata={"error_type": "timeout", "component": "database"},
        )

        # Create recall service
        recall_service = MemoryRecallService(memory_service)
        await recall_service.initialize()

        # Perform recall
        result = await recall_service.recall_for_operation(
            project_name="test_project",
            operation_type="deploy",
            operation_context={"environment": "production", "strategy": "blue-green"},
        )

        # Verify results
        assert result.success
        assert result.memory_context.get_total_memories() > 0
        assert result.enriched_context is not None
        assert result.recommendations is not None
        assert len(result.recommendations.recommendations) > 0

        # Test agent context format
        agent_context = result.get_agent_summary()
        assert agent_context["memory_available"]
        assert "relevant_memories" in agent_context
        assert "recommendations" in agent_context

        # Cleanup
        await recall_service.cleanup()

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under concurrent load."""
        # # from claude_pm.services.memory.backends.memory_backend import InMemoryBackend  # InMemory backend removed  # InMemory backend removed
        from claude_pm.services.memory.services.unified_service import FlexibleMemoryService

        # Setup optimized configuration
        recall_config = RecallConfig(
            max_recall_time_ms=50.0, max_memories_per_category=5, performance_cache_size=500
        )

        config = MemoryRecallConfig(recall_config=recall_config, max_concurrent_recalls=10)

        memory_service = FlexibleMemoryService({"fallback_chain": ["sqlite"]})
        await memory_service.initialize()

        recall_service = MemoryRecallService(memory_service, config)
        await recall_service.initialize()

        # Run concurrent recalls
        start_time = time.time()
        tasks = []

        for i in range(20):
            task = recall_service.recall_for_operation(
                "test_project", "test_operation", {"iteration": i}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify performance
        assert all(result.success for result in results)
        assert total_time < 5.0  # Should complete within 5 seconds

        # Check individual recall times
        recall_times = [result.processing_time_ms for result in results]
        avg_time = sum(recall_times) / len(recall_times)
        assert avg_time < 100.0  # Average should be under 100ms

        await recall_service.cleanup()


@pytest.mark.asyncio
async def test_memory_recall_factory():
    """Test memory recall service factory function."""
    from claude_pm.services.memory import create_memory_recall_service

    # Test with default configuration
    service = create_memory_recall_service()
    assert isinstance(service, MemoryRecallService)

    # Test with custom memory service
    memory_service = FlexibleMemoryService()
    service = create_memory_recall_service(memory_service)
    assert service.memory_service is memory_service


def test_configuration_validation():
    """Test configuration validation."""
    from claude_pm.services.memory.memory_context_enhancer import RecallConfig
    from claude_pm.services.memory.similarity_matcher import MatchingConfig
    from claude_pm.services.memory.recommendation_engine import RecommendationConfig

    # Valid configurations should not raise
    RecallConfig()
    MatchingConfig()
    RecommendationConfig()

    # Invalid configurations should raise
    with pytest.raises(ValueError):
        MatchingConfig(min_similarity_threshold=1.5)  # > 1.0

    with pytest.raises(ValueError):
        RecommendationConfig(max_recommendations_per_type=-1)  # negative


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
