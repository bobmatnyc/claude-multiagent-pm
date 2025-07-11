"""
Test Suite for M02-014: Intelligent Workflow Selection System

This test suite validates the intelligent workflow selection capabilities,
including workflow pattern matching, success prediction, dynamic routing,
and continuous learning from outcomes.
"""

import asyncio
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Import the components being tested
from claude_pm.services.workflow_selection_engine import (
    WorkflowSelectionEngine,
    WorkflowType,
    RoutingStrategy,
    WorkflowSelectionRequest,
    WorkflowRecommendation,
    WorkflowPattern,
    create_workflow_selection_engine,
)
from claude_pm.services.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
    AgentType,
    AgentStatus,
)
from claude_pm.services.intelligent_task_planner import TaskComplexity


class TestWorkflowSelectionEngine:
    """Test the WorkflowSelectionEngine core functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for the workflow selection engine."""
        memory = Mock()
        context_manager = Mock()
        agent_memory_manager = Mock()
        task_planner = Mock()

        # Mock memory responses
        memory.retrieve_memories = AsyncMock(return_value=Mock(success=True, data={"memories": []}))
        memory.store_memory = AsyncMock(return_value=True)

        # Mock task planner decomposition
        mock_decomposition = Mock()
        mock_decomposition.complexity = TaskComplexity.MEDIUM
        mock_decomposition.total_estimated_hours = 2.0
        task_planner.decompose_task = AsyncMock(return_value=mock_decomposition)

        return {
            "memory": memory,
            "context_manager": context_manager,
            "agent_memory_manager": agent_memory_manager,
            "task_planner": task_planner,
        }

    @pytest.fixture
    def workflow_engine(self, mock_dependencies):
        """Create a WorkflowSelectionEngine instance with mocked dependencies."""
        return WorkflowSelectionEngine(
            memory=mock_dependencies["memory"],
            context_manager=mock_dependencies["context_manager"],
            agent_memory_manager=mock_dependencies["agent_memory_manager"],
            task_planner=mock_dependencies["task_planner"],
        )

    def test_initialization(self, workflow_engine):
        """Test that the workflow selection engine initializes correctly."""
        assert workflow_engine is not None
        assert hasattr(workflow_engine, "selection_rules")
        assert hasattr(workflow_engine, "routing_weights")
        assert hasattr(workflow_engine, "performance_metrics")
        assert workflow_engine.performance_metrics["total_selections"] == 0

    def test_selection_rules_initialization(self, workflow_engine):
        """Test that selection rules are properly initialized."""
        rules = workflow_engine.selection_rules

        # Check that key rule categories exist
        assert "trivial_simple" in rules
        assert "medium_balanced" in rules
        assert "complex_comprehensive" in rules
        assert "research_discovery" in rules
        assert "urgent_fast_track" in rules

        # Verify rule structure
        for rule_name, rule in rules.items():
            if "preferred_workflows" in rule:
                assert isinstance(rule["preferred_workflows"], list)
                assert all(isinstance(wf, WorkflowType) for wf in rule["preferred_workflows"])

    def test_routing_weights_initialization(self, workflow_engine):
        """Test that routing weights are properly initialized."""
        weights = workflow_engine.routing_weights

        # Check that all routing strategies have weights
        expected_strategies = [
            RoutingStrategy.PERFORMANCE_OPTIMIZED.value,
            RoutingStrategy.QUALITY_OPTIMIZED.value,
            RoutingStrategy.RESOURCE_OPTIMIZED.value,
            RoutingStrategy.BALANCED.value,
            RoutingStrategy.LEARNING_OPTIMIZED.value,
        ]

        for strategy in expected_strategies:
            assert strategy in weights
            strategy_weights = weights[strategy]
            # Weights should sum to approximately 1.0
            total_weight = sum(strategy_weights.values())
            assert 0.9 <= total_weight <= 1.1

    @pytest.mark.asyncio
    async def test_simple_workflow_selection(self, workflow_engine):
        """Test workflow selection for a simple task."""
        request = WorkflowSelectionRequest(
            task_description="Fix a simple typo in the documentation",
            priority_level="low",
            quality_requirements="standard",
        )

        recommendation = await workflow_engine.select_workflow(request)

        assert isinstance(recommendation, WorkflowRecommendation)
        assert recommendation.workflow_type in [
            WorkflowType.SIMPLE_LINEAR,
            WorkflowType.EMERGENCY_FAST_TRACK,
        ]
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.estimated_duration_minutes > 0
        assert isinstance(recommendation.reasoning, str)

    @pytest.mark.asyncio
    async def test_complex_workflow_selection(self, workflow_engine, mock_dependencies):
        """Test workflow selection for a complex task."""
        # Mock complex task decomposition
        mock_decomposition = Mock()
        mock_decomposition.complexity = TaskComplexity.COMPLEX
        mock_decomposition.total_estimated_hours = 8.0
        mock_dependencies["task_planner"].decompose_task = AsyncMock(
            return_value=mock_decomposition
        )

        request = WorkflowSelectionRequest(
            task_description="Design and implement a new microservice architecture",
            task_complexity=TaskComplexity.COMPLEX,
            priority_level="high",
            quality_requirements="critical",
        )

        recommendation = await workflow_engine.select_workflow(request)

        assert recommendation.workflow_type in [
            WorkflowType.HIERARCHICAL_REVIEW,
            WorkflowType.RESEARCH_DISCOVERY,
            WorkflowType.CRITICAL_PATH,
        ]
        assert recommendation.estimated_duration_minutes > 30  # Complex tasks take longer
        assert len(recommendation.risk_factors) > 0  # Complex tasks have risks

    @pytest.mark.asyncio
    async def test_urgent_workflow_selection(self, workflow_engine):
        """Test workflow selection for urgent tasks."""
        request = WorkflowSelectionRequest(
            task_description="Critical production bug fix",
            priority_level="critical",
            deadline=datetime.now() + timedelta(hours=2),
            quality_requirements="minimal",
        )

        recommendation = await workflow_engine.select_workflow(request)

        assert recommendation.workflow_type in [
            WorkflowType.EMERGENCY_FAST_TRACK,
            WorkflowType.SIMPLE_LINEAR,
        ]
        assert recommendation.routing_strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED
        assert recommendation.estimated_duration_minutes < 60  # Should be fast

    @pytest.mark.asyncio
    async def test_research_workflow_selection(self, workflow_engine):
        """Test workflow selection for research tasks."""
        request = WorkflowSelectionRequest(
            task_description="Research and analyze feasibility of new technology stack",
            priority_level="medium",
            quality_requirements="high",
        )

        recommendation = await workflow_engine.select_workflow(request)

        assert recommendation.workflow_type in [
            WorkflowType.RESEARCH_DISCOVERY,
            WorkflowType.ITERATIVE_REFINEMENT,
        ]
        # Research tasks should have specific optimization opportunities
        assert any("research" in opp.lower() for opp in recommendation.optimization_opportunities)

    def test_task_keyword_extraction(self, workflow_engine):
        """Test task keyword extraction functionality."""
        test_cases = [
            (
                "Build a React frontend with API integration",
                ["implementation", "frontend", "integration"],
            ),
            ("Fix database performance issues", ["fix", "optimization"]),
            ("Research machine learning frameworks", ["research"]),
            ("Deploy application to production", ["deployment"]),
            ("Write unit tests for authentication module", ["testing", "implementation"]),
        ]

        for task_description, expected_keywords in test_cases:
            keywords = workflow_engine._extract_task_keywords(task_description)
            for expected in expected_keywords:
                assert (
                    expected in keywords
                ), f"Expected '{expected}' in keywords for: {task_description}"

    def test_task_type_analysis(self, workflow_engine):
        """Test task type analysis functionality."""
        test_cases = [
            {
                "description": "Research and investigate new technology options",
                "keywords": ["research"],
                "expected": {"research_required": True, "collaboration_level": "medium"},
            },
            {
                "description": "Critical security vulnerability fix for production",
                "keywords": ["fix"],
                "expected": {"risk_level": "high"},
            },
            {
                "description": "Simple text update in documentation",
                "keywords": ["documentation"],
                "expected": {"risk_level": "low"},
            },
        ]

        for case in test_cases:
            analysis = workflow_engine._analyze_task_type(case["description"], case["keywords"])
            for key, expected_value in case["expected"].items():
                assert analysis[key] == expected_value

    @pytest.mark.asyncio
    async def test_workflow_pattern_loading(self, workflow_engine, mock_dependencies):
        """Test loading of workflow patterns from memory."""
        # Mock memory with workflow patterns
        mock_patterns = [
            {
                "id": "pattern_1",
                "content": "workflow pattern for simple tasks",
                "metadata": {
                    "pattern_data": {
                        "workflow_type": "simple_linear",
                        "success_rate": 0.85,
                        "avg_execution_time": 25,
                        "min_complexity": "simple",
                        "max_complexity": "medium",
                    }
                },
            }
        ]

        mock_dependencies["memory"].retrieve_memories = AsyncMock(
            return_value=Mock(success=True, data={"memories": mock_patterns})
        )

        request = WorkflowSelectionRequest(
            task_description="Simple implementation task", task_complexity=TaskComplexity.SIMPLE
        )

        # Mock task analysis
        task_analysis = {
            "complexity": TaskComplexity.SIMPLE,
            "keywords": ["implementation"],
            "urgency": "medium",
        }

        patterns = await workflow_engine._load_workflow_patterns(request, task_analysis)

        assert len(patterns) > 0
        assert isinstance(patterns[0], WorkflowPattern)
        assert patterns[0].workflow_type == WorkflowType.SIMPLE_LINEAR
        assert patterns[0].success_rate == 0.85

    def test_pattern_relevance_checking(self, workflow_engine):
        """Test workflow pattern relevance checking."""
        # Create test pattern
        pattern = WorkflowPattern(
            pattern_id="test_pattern",
            workflow_type=WorkflowType.SIMPLE_LINEAR,
            task_characteristics={"keywords": ["implementation", "frontend"]},
            complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.MEDIUM),
            success_rate=0.8,
            avg_execution_time=30,
            avg_resource_usage={},
            team_preferences=[],
            recent_usage_count=5,
            last_used=datetime.now(),
        )

        # Test relevant request
        relevant_request = WorkflowSelectionRequest(
            task_description="Implement frontend component", task_complexity=TaskComplexity.SIMPLE
        )

        relevant_analysis = {
            "complexity": TaskComplexity.SIMPLE,
            "keywords": ["implementation", "frontend"],
        }

        assert workflow_engine._is_pattern_relevant(pattern, relevant_request, relevant_analysis)

        # Test irrelevant request (different complexity)
        irrelevant_analysis = {
            "complexity": TaskComplexity.EPIC,
            "keywords": ["implementation", "frontend"],
        }

        assert not workflow_engine._is_pattern_relevant(
            pattern, relevant_request, irrelevant_analysis
        )

    def test_routing_strategy_determination(self, workflow_engine):
        """Test routing strategy determination logic."""
        test_cases = [
            {
                "request": WorkflowSelectionRequest(
                    task_description="Critical production issue", priority_level="critical"
                ),
                "analysis": {"urgency": "critical"},
                "expected": RoutingStrategy.PERFORMANCE_OPTIMIZED,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="High quality feature implementation",
                    quality_requirements="critical",
                ),
                "analysis": {"urgency": "medium"},
                "expected": RoutingStrategy.QUALITY_OPTIMIZED,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="Resource-constrained task",
                    resource_constraints={"limited_resources": True},
                ),
                "analysis": {"urgency": "low"},
                "expected": RoutingStrategy.RESOURCE_OPTIMIZED,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="Experimental proof of concept",
                ),
                "analysis": {"urgency": "medium"},
                "expected": RoutingStrategy.LEARNING_OPTIMIZED,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="Standard implementation task",
                ),
                "analysis": {"urgency": "medium"},
                "expected": RoutingStrategy.BALANCED,
            },
        ]

        for case in test_cases:
            strategy = workflow_engine._determine_routing_strategy(
                case["request"], case["analysis"]
            )
            assert (
                strategy == case["expected"]
            ), f"Expected {case['expected']} for: {case['request'].task_description}"

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, workflow_engine):
        """Test that performance metrics are properly tracked."""
        initial_selections = workflow_engine.performance_metrics["total_selections"]

        request = WorkflowSelectionRequest(task_description="Test task for metrics tracking")

        recommendation = await workflow_engine.select_workflow(request)

        # Check that metrics were updated
        assert workflow_engine.performance_metrics["total_selections"] == initial_selections + 1
        assert len(workflow_engine.selection_history) == 1

        # Check selection history entry
        history_entry = workflow_engine.selection_history[0]
        assert history_entry["workflow_type"] == recommendation.workflow_type.value
        assert history_entry["confidence"] == recommendation.confidence
        assert "timestamp" in history_entry

    def test_fallback_recommendation(self, workflow_engine):
        """Test fallback recommendation creation."""
        test_cases = [
            {
                "request": WorkflowSelectionRequest(
                    task_description="Critical emergency task", priority_level="critical"
                ),
                "expected_workflow": WorkflowType.EMERGENCY_FAST_TRACK,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="Research new technology options", priority_level="medium"
                ),
                "expected_workflow": WorkflowType.RESEARCH_DISCOVERY,
            },
            {
                "request": WorkflowSelectionRequest(
                    task_description="Standard implementation task", priority_level="medium"
                ),
                "expected_workflow": WorkflowType.SIMPLE_LINEAR,
            },
        ]

        for case in test_cases:
            recommendation = workflow_engine._create_fallback_recommendation(case["request"])
            assert recommendation.workflow_type == case["expected_workflow"]
            assert recommendation.confidence == 0.3  # Low confidence for fallback
            assert "fallback" in recommendation.reasoning.lower()


class TestIntelligentWorkflowOrchestrator:
    """Test the intelligent workflow orchestration functionality."""

    @pytest.fixture
    def mock_memory_service(self):
        """Create mock memory service."""
        memory_service = Mock()
        memory_service.search = AsyncMock(return_value=Mock(success=True, data=[]))
        memory_service.store = AsyncMock(return_value=True)
        return memory_service

    @pytest.fixture
    def intelligent_orchestrator(self, mock_memory_service):
        """Create MultiAgentOrchestrator with mocked dependencies."""
        # Create a mock workflow engine
        mock_engine = Mock()
        mock_engine.select_workflow = AsyncMock(
            return_value=WorkflowRecommendation(
                workflow_type=WorkflowType.SIMPLE_LINEAR,
                confidence=0.8,
                reasoning="Test recommendation",
                predicted_success_rate=0.85,
                estimated_duration_minutes=30,
                resource_requirements={"agents": 1},
                routing_strategy=RoutingStrategy.BALANCED,
                optimization_opportunities=["test optimization"],
            )
        )

        # Create orchestrator with mocked workflow engine
        orchestrator = MultiAgentOrchestrator(
            base_repo_path="/tmp/test_repo", memory=mock_memory_service
        )
        orchestrator.workflow_engine = mock_engine
        return orchestrator

    def test_initialization(self, intelligent_orchestrator):
        """Test that the intelligent orchestrator initializes correctly."""
        assert intelligent_orchestrator is not None
        assert hasattr(intelligent_orchestrator, "workflow_engine")
        assert hasattr(intelligent_orchestrator, "memory")
        assert intelligent_orchestrator.memory is not None

    @pytest.mark.asyncio
    async def test_intelligent_task_execution(self, intelligent_orchestrator):
        """Test intelligent task execution with workflow selection."""
        # Create test task request
        task_request = {
            "task_description": "Test task for intelligent workflow",
            "user_id": "test_user",
            "project_id": "test_project",
            "context": {"test": True},
        }

        # Execute task through orchestrator
        result = await intelligent_orchestrator.execute_task(task_request)

        # Verify intelligent workflow selection was applied
        assert result is not None
        assert "task_id" in result
        assert "status" in result
        assert result["status"] in [status.value for status in AgentStatus]

        # Check that workflow engine was called
        intelligent_orchestrator.workflow_engine.select_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_selection_with_context(self, intelligent_orchestrator):
        """Test workflow selection with contextual task information."""
        task_request = {
            "task_description": "Implement new feature with testing",
            "project_id": "test_project",
            "priority": "high",
            "deadline": datetime.now() + timedelta(hours=24),
            "quality_requirements": "standard",
            "user_id": "test_user",
        }

        result = await intelligent_orchestrator.execute_task(task_request)

        # Verify the workflow engine was called
        intelligent_orchestrator.workflow_engine.select_workflow.assert_called_once()

        # Verify result structure
        assert result is not None
        assert "task_id" in result
        assert "status" in result

    def test_workflow_configuration(self, intelligent_orchestrator):
        """Test workflow configuration based on recommendation."""
        # Test workflow configuration mapping
        test_recommendations = [
            WorkflowType.PARALLEL_MULTI_AGENT,
            WorkflowType.HIERARCHICAL_REVIEW,
            WorkflowType.EMERGENCY_FAST_TRACK,
        ]

        for workflow_type in test_recommendations:
            recommendation = WorkflowRecommendation(
                workflow_type=workflow_type,
                confidence=0.8,
                reasoning="Test recommendation",
                predicted_success_rate=0.8,
                estimated_duration_minutes=30,
                resource_requirements={"agents": 2},
                routing_strategy=RoutingStrategy.BALANCED,
            )

            # Verify recommendation is valid
            assert recommendation.workflow_type == workflow_type
            assert recommendation.confidence > 0

    @pytest.mark.asyncio
    async def test_orchestrator_metrics(self, intelligent_orchestrator):
        """Test orchestrator metrics collection."""
        # Execute a test task
        task_request = {
            "task_description": "Test task for metrics",
            "user_id": "test_user",
            "project_id": "test_project",
        }

        result = await intelligent_orchestrator.execute_task(task_request)

        # Verify metrics can be collected
        metrics = intelligent_orchestrator.get_metrics()
        assert metrics is not None
        assert isinstance(metrics, dict)


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_simple_task_end_to_end(self):
        """Test complete workflow selection for a simple task."""
        # This would be an integration test that tests the full flow
        # from task description to workflow recommendation
        pass

    @pytest.mark.asyncio
    async def test_complex_task_end_to_end(self):
        """Test complete workflow selection for a complex task."""
        # This would test complex task handling with multiple agents
        # and review gates
        pass

    @pytest.mark.asyncio
    async def test_learning_from_outcomes(self):
        """Test that the system learns from workflow outcomes."""
        # This would test the feedback loop and pattern learning
        pass


# Performance and load testing
class TestPerformance:
    """Test performance characteristics of the workflow selection system."""

    @pytest.mark.asyncio
    async def test_selection_performance(self):
        """Test that workflow selection performs within acceptable time limits."""
        # Test that selection completes within reasonable time (e.g., < 1 second)
        pass

    @pytest.mark.asyncio
    async def test_concurrent_selections(self):
        """Test handling of concurrent workflow selections."""
        # Test thread safety and performance under concurrent load
        pass


if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short"])
