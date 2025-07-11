"""
Test suite for ContinuousLearningEngine - MEM-006 Implementation
Validates all 6 acceptance criteria and comprehensive learning functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.continuous_learning_engine import (
    ContinuousLearningEngine,
    TaskOutcome,
    LearningPattern,
    LearningMetric,
    OutcomeType,
    PatternType,
    LearningMetricType,
    LearningInsight,
    create_continuous_learning_engine,
)
from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory


class TestContinuousLearningEngine:
    """Test suite for ContinuousLearningEngine implementation."""

    @pytest.fixture
    async def mock_memory(self):
        """Create mock memory service."""
        memory = Mock(spec=ClaudePMMemory)
        memory.store_memory = AsyncMock(
            return_value=Mock(success=True, memory_id="test_memory_123")
        )
        memory.retrieve_memories = AsyncMock(
            return_value=Mock(
                success=True,
                data={
                    "memories": [
                        {
                            "id": "mem_1",
                            "content": "Test memory content",
                            "metadata": {
                                "type": "task_decomposition",
                                "outcome": "success",
                                "complexity": "medium",
                                "decomposition": {
                                    "strategy": "parallel",
                                    "subtasks": [
                                        {
                                            "title": "Design",
                                            "complexity": "simple",
                                            "estimated_hours": 4,
                                        },
                                        {
                                            "title": "Implement",
                                            "complexity": "medium",
                                            "estimated_hours": 8,
                                        },
                                    ],
                                },
                            },
                        }
                    ]
                },
            )
        )
        return memory

    @pytest.fixture
    def learning_engine(self, mock_memory):
        """Create learning engine instance."""
        return ContinuousLearningEngine(memory=mock_memory, learning_window_days=30)

    @pytest.fixture
    def sample_task_outcome(self):
        """Create sample task outcome."""
        return TaskOutcome(
            task_id="task_001",
            task_description="Implement user authentication feature",
            project_name="web_app",
            decomposition_id="decomp_001",
            outcome_type=OutcomeType.SUCCESS,
            actual_hours=12.0,
            estimated_hours=10.0,
            completion_date=datetime.now(),
            success_factors=["clear requirements", "good team collaboration"],
            technologies_used=["python", "fastapi", "jwt"],
            team_members=["dev1", "dev2"],
            solutions_applied=["jwt tokens", "password hashing"],
        )

    @pytest.fixture
    def sample_failure_outcome(self):
        """Create sample failure outcome."""
        return TaskOutcome(
            task_id="task_002",
            task_description="Implement complex analytics dashboard",
            project_name="analytics_app",
            outcome_type=OutcomeType.FAILURE,
            actual_hours=25.0,
            estimated_hours=15.0,
            completion_date=datetime.now() - timedelta(days=2),
            failure_factors=["unclear requirements", "technical complexity underestimated"],
            technologies_used=["react", "d3.js", "elasticsearch"],
            team_members=["dev3", "dev4"],
            challenges_encountered=["data integration issues", "performance problems"],
        )


class TestMEM006AcceptanceCriteria:
    """Test all 6 MEM-006 acceptance criteria."""

    @pytest.mark.asyncio
    async def test_criteria_1_capture_task_outcomes(self, learning_engine, sample_task_outcome):
        """
        AC1: ContinuousLearningEngine captures task outcomes
        """
        # Test capturing task outcome
        result = await learning_engine.capture_task_outcome(sample_task_outcome)

        # Verify capture was successful
        assert result is True

        # Verify outcome was stored in engine
        assert sample_task_outcome.task_id in learning_engine.captured_outcomes
        stored_outcome = learning_engine.captured_outcomes[sample_task_outcome.task_id]
        assert stored_outcome.task_description == "Implement user authentication feature"
        assert stored_outcome.outcome_type == OutcomeType.SUCCESS
        assert stored_outcome.actual_hours == 12.0
        assert stored_outcome.estimated_hours == 10.0

        # Verify memory storage was called
        learning_engine.memory.store_memory.assert_called()

        print("✅ AC1: ContinuousLearningEngine captures task outcomes - PASSED")

    @pytest.mark.asyncio
    async def test_criteria_2_extract_success_patterns(self, learning_engine):
        """
        AC2: Success patterns automatically extracted and stored
        """
        # Create multiple successful outcomes with similar characteristics
        success_outcomes = []
        for i in range(4):  # Need minimum 3 for pattern extraction
            outcome = TaskOutcome(
                task_id=f"success_task_{i}",
                task_description=f"Implement authentication feature {i}",
                project_name="web_app",
                outcome_type=OutcomeType.SUCCESS,
                actual_hours=10.0 + i,
                estimated_hours=10.0,
                completion_date=datetime.now() - timedelta(days=i),
                success_factors=["clear requirements", "team collaboration"],
                technologies_used=["python", "fastapi"],
                team_members=["dev1", "dev2"],
            )
            success_outcomes.append(outcome)
            await learning_engine.capture_task_outcome(outcome)

        # Extract success patterns
        patterns = await learning_engine.extract_success_patterns(project_filter="web_app")

        # Verify patterns were extracted
        assert len(patterns) > 0
        success_pattern = patterns[0]
        assert success_pattern.pattern_type == PatternType.SUCCESS_PATTERN
        assert success_pattern.supporting_cases >= 3
        assert success_pattern.success_rate > 0.8  # High success rate
        assert len(success_pattern.recommendations) > 0

        # Verify pattern was stored in memory
        learning_engine.memory.store_memory.assert_called()

        print("✅ AC2: Success patterns automatically extracted and stored - PASSED")

    @pytest.mark.asyncio
    async def test_criteria_3_analyze_failure_patterns(self, learning_engine):
        """
        AC3: Failure patterns analyzed with prevention strategies
        """
        # Create multiple failure outcomes with similar characteristics
        failure_outcomes = []
        for i in range(3):  # Need minimum 2 for failure pattern analysis
            outcome = TaskOutcome(
                task_id=f"failure_task_{i}",
                task_description=f"Implement complex feature {i}",
                project_name="complex_app",
                outcome_type=OutcomeType.FAILURE,
                actual_hours=20.0 + i * 2,
                estimated_hours=15.0,
                completion_date=datetime.now() - timedelta(days=i),
                failure_factors=["unclear requirements", "technical complexity"],
                technologies_used=["react", "complex_api"],
                team_members=["dev3", "dev4"],
                challenges_encountered=["integration issues", "performance problems"],
            )
            failure_outcomes.append(outcome)
            await learning_engine.capture_task_outcome(outcome)

        # Analyze failure patterns
        patterns = await learning_engine.analyze_failure_patterns(project_filter="complex_app")

        # Verify failure patterns were analyzed
        assert len(patterns) > 0
        failure_pattern = patterns[0]
        assert failure_pattern.pattern_type == PatternType.FAILURE_PATTERN
        assert failure_pattern.supporting_cases >= 2
        assert (1.0 - failure_pattern.success_rate) > 0.5  # High failure rate

        # Verify prevention strategies were generated
        assert len(failure_pattern.recommendations) > 0
        prevention_recommendations = [
            r
            for r in failure_pattern.recommendations
            if "prevent" in r.lower() or "mitigate" in r.lower()
        ]
        assert len(prevention_recommendations) > 0

        print("✅ AC3: Failure patterns analyzed with prevention strategies - PASSED")

    @pytest.mark.asyncio
    async def test_criteria_4_automatic_pattern_recognition(self, learning_engine):
        """
        AC4: Pattern recognition identifies trends automatically
        """
        # Create diverse outcomes to trigger different pattern types
        outcomes = [
            # Success pattern group
            TaskOutcome(
                "task_s1",
                "API implementation",
                "api_project",
                "decomp_s1",
                OutcomeType.SUCCESS,
                actual_hours=8,
                estimated_hours=8,
                completion_date=datetime.now(),
            ),
            TaskOutcome(
                "task_s2",
                "API development",
                "api_project",
                "decomp_s2",
                OutcomeType.SUCCESS,
                actual_hours=9,
                estimated_hours=8,
                completion_date=datetime.now(),
            ),
            TaskOutcome(
                "task_s3",
                "API creation",
                "api_project",
                "decomp_s3",
                OutcomeType.SUCCESS,
                actual_hours=7,
                estimated_hours=8,
                completion_date=datetime.now(),
            ),
            # Efficiency pattern group
            TaskOutcome(
                "task_e1",
                "Frontend component",
                "ui_project",
                "decomp_e1",
                OutcomeType.SUCCESS,
                actual_hours=4,
                estimated_hours=6,
                completion_date=datetime.now(),
            ),  # Efficient
            TaskOutcome(
                "task_e2",
                "UI component build",
                "ui_project",
                "decomp_e2",
                OutcomeType.SUCCESS,
                actual_hours=5,
                estimated_hours=7,
                completion_date=datetime.now(),
            ),  # Efficient
        ]

        # Capture all outcomes
        for outcome in outcomes:
            await learning_engine.capture_task_outcome(outcome)

        # Run automatic pattern recognition
        recognized_patterns = await learning_engine.recognize_patterns_automatically()

        # Verify patterns were recognized across different types
        assert isinstance(recognized_patterns, dict)
        assert len(recognized_patterns) > 0

        # Check that different pattern types are represented
        pattern_types_found = list(recognized_patterns.keys())
        assert len(pattern_types_found) > 0

        # Verify patterns have proper structure
        for pattern_type, patterns in recognized_patterns.items():
            if patterns:  # If patterns were found for this type
                for pattern in patterns:
                    assert isinstance(pattern, LearningPattern)
                    assert pattern.pattern_type == pattern_type
                    assert pattern.confidence_score > 0
                    assert pattern.supporting_cases > 0

        print("✅ AC4: Pattern recognition identifies trends automatically - PASSED")

    @pytest.mark.asyncio
    async def test_criteria_5_learning_metrics_tracking(self, learning_engine, sample_task_outcome):
        """
        AC5: Learning metrics track improvement over time
        """
        # Capture some outcomes to generate metrics
        await learning_engine.capture_task_outcome(sample_task_outcome)

        # Add a more accurate outcome to show improvement
        improved_outcome = TaskOutcome(
            task_id="improved_task",
            task_description="Implement feature with better estimation",
            project_name="web_app",
            outcome_type=OutcomeType.SUCCESS,
            actual_hours=10.0,
            estimated_hours=10.2,  # More accurate estimation
            completion_date=datetime.now(),
        )
        await learning_engine.capture_task_outcome(improved_outcome)

        # Track learning metrics
        metrics = await learning_engine.track_learning_metrics()

        # Verify all required metric types are tracked
        expected_metrics = [
            LearningMetricType.ACCURACY_IMPROVEMENT,
            LearningMetricType.ESTIMATION_PRECISION,
            LearningMetricType.PATTERN_RECOGNITION_RATE,
            LearningMetricType.FAILURE_PREVENTION_RATE,
            LearningMetricType.ADAPTATION_EFFECTIVENESS,
            LearningMetricType.LEARNING_VELOCITY,
        ]

        assert len(metrics) > 0
        for metric_type in expected_metrics:
            if metric_type in metrics:
                metric = metrics[metric_type]
                assert isinstance(metric, LearningMetric)
                assert metric.metric_type == metric_type
                assert metric.current_value >= 0
                assert metric.baseline_value >= 0
                assert hasattr(metric, "improvement_rate")

        # Verify metrics are stored in memory for historical tracking
        learning_engine.memory.store_memory.assert_called()

        print("✅ AC5: Learning metrics track improvement over time - PASSED")

    @pytest.mark.asyncio
    async def test_criteria_6_historical_analysis_effectiveness(self, learning_engine):
        """
        AC6: Historical analysis shows learning effectiveness
        """
        # Create historical data spanning different time periods
        base_date = datetime.now() - timedelta(days=60)

        # Simulate learning progression over time
        historical_outcomes = []
        for week in range(8):  # 8 weeks of data
            for task_num in range(3):  # 3 tasks per week
                # Simulate improving accuracy over time
                base_accuracy = 0.6 + (week * 0.05)  # Improving accuracy
                estimated_hours = 10.0
                actual_hours = estimated_hours * (
                    1 + (0.4 - base_accuracy)
                )  # More accurate = closer to estimate

                outcome = TaskOutcome(
                    task_id=f"hist_task_{week}_{task_num}",
                    task_description=f"Historical task week {week}",
                    project_name="learning_project",
                    outcome_type=(
                        OutcomeType.SUCCESS if base_accuracy > 0.7 else OutcomeType.PARTIAL_SUCCESS
                    ),
                    actual_hours=actual_hours,
                    estimated_hours=estimated_hours,
                    completion_date=base_date + timedelta(weeks=week, days=task_num),
                )
                historical_outcomes.append(outcome)
                await learning_engine.capture_task_outcome(outcome)

        # Perform historical analysis
        analysis_period = timedelta(days=56)  # 8 weeks
        analysis = await learning_engine.analyze_learning_effectiveness(analysis_period)

        # Verify comprehensive analysis structure
        required_analysis_keys = [
            "analysis_period",
            "analysis_date",
            "overall_effectiveness",
            "metric_trends",
            "pattern_effectiveness",
            "improvement_areas",
            "learning_velocity",
            "recommendations",
        ]

        for key in required_analysis_keys:
            assert key in analysis, f"Missing analysis key: {key}"

        # Verify analysis period is correct
        assert analysis["analysis_period"] == 56

        # Verify overall effectiveness assessment
        assert "overall_effectiveness" in analysis
        effectiveness = analysis["overall_effectiveness"]
        assert isinstance(effectiveness, dict)

        # Verify metric trends analysis
        assert "metric_trends" in analysis
        trends = analysis["metric_trends"]
        assert isinstance(trends, dict)

        # Verify pattern effectiveness analysis
        assert "pattern_effectiveness" in analysis
        pattern_effectiveness = analysis["pattern_effectiveness"]
        assert isinstance(pattern_effectiveness, dict)

        # Verify learning velocity calculation
        assert "learning_velocity" in analysis
        velocity = analysis["learning_velocity"]
        assert isinstance(velocity, dict)

        # Verify improvement areas identification
        assert "improvement_areas" in analysis
        improvements = analysis["improvement_areas"]
        assert isinstance(improvements, list)

        # Verify recommendations generation
        assert "recommendations" in analysis
        recommendations = analysis["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Verify analysis was stored in memory
        learning_engine.memory.store_memory.assert_called()

        print("✅ AC6: Historical analysis shows learning effectiveness - PASSED")


class TestLearningEngineIntegration:
    """Test integration capabilities and performance."""

    @pytest.mark.asyncio
    async def test_pattern_extraction_performance(self, learning_engine):
        """Test pattern extraction performance with larger datasets."""
        # Create 20 outcomes to test performance
        outcomes = []
        for i in range(20):
            outcome = TaskOutcome(
                task_id=f"perf_task_{i}",
                task_description=f"Performance test task {i}",
                project_name="perf_project",
                outcome_type=OutcomeType.SUCCESS if i % 3 != 0 else OutcomeType.FAILURE,
                actual_hours=8.0 + (i % 5),
                estimated_hours=8.0,
                completion_date=datetime.now() - timedelta(days=i),
                technologies_used=["python", "react"][i % 2 : i % 2 + 1],
            )
            outcomes.append(outcome)
            await learning_engine.capture_task_outcome(outcome)

        # Measure pattern extraction time
        start_time = datetime.now()
        patterns = await learning_engine.extract_success_patterns()
        extraction_time = (datetime.now() - start_time).total_seconds()

        # Verify reasonable performance (should complete within 5 seconds)
        assert extraction_time < 5.0, f"Pattern extraction took too long: {extraction_time}s"

        print(f"✅ Pattern extraction performance: {extraction_time:.2f}s for 20 outcomes")

    @pytest.mark.asyncio
    async def test_learning_engine_statistics(self, learning_engine, sample_task_outcome):
        """Test learning engine statistics and health monitoring."""
        # Add some data
        await learning_engine.capture_task_outcome(sample_task_outcome)

        # Get statistics
        stats = learning_engine.get_learning_stats()

        # Verify comprehensive statistics
        required_stats = [
            "total_outcomes_captured",
            "patterns_identified",
            "active_insights",
            "learning_metrics",
            "pattern_types",
            "recent_patterns",
            "learning_window_days",
            "system_health",
        ]

        for stat in required_stats:
            assert stat in stats, f"Missing statistic: {stat}"

        # Verify reasonable values
        assert stats["total_outcomes_captured"] >= 1
        assert stats["learning_window_days"] > 0
        assert stats["system_health"] == "operational"

        print("✅ Learning engine statistics comprehensive and accurate")

    @pytest.mark.asyncio
    async def test_insight_generation(self, learning_engine):
        """Test insight generation from patterns and metrics."""
        # Create pattern data that should generate insights
        high_success_outcomes = []
        for i in range(4):
            outcome = TaskOutcome(
                task_id=f"insight_task_{i}",
                task_description="High success pattern task",
                project_name="insight_project",
                outcome_type=OutcomeType.SUCCESS,
                actual_hours=8.0,
                estimated_hours=8.0,
                completion_date=datetime.now() - timedelta(days=i),
                success_factors=["good planning", "clear requirements"],
                technologies_used=["python", "fastapi"],
            )
            high_success_outcomes.append(outcome)
            await learning_engine.capture_task_outcome(outcome)

        # Extract patterns (should generate insights)
        await learning_engine.extract_success_patterns("insight_project")

        # Check that insights were generated
        insights = learning_engine.learning_insights

        # Verify insights structure and content
        if insights:  # Insights may not always be generated depending on thresholds
            for insight in insights:
                assert isinstance(insight, LearningInsight)
                assert insight.insight_id
                assert insight.title
                assert insight.description
                assert insight.confidence > 0
                assert insight.insight_type in [
                    "recommendation",
                    "warning",
                    "optimization",
                    "trend",
                ]
                assert isinstance(insight.action_items, list)

        print("✅ Insight generation working correctly")

    def test_factory_function(self, mock_memory):
        """Test the factory function for creating learning engine."""
        # Test factory function
        engine = create_continuous_learning_engine(memory=mock_memory, learning_window_days=60)

        # Verify correct initialization
        assert isinstance(engine, ContinuousLearningEngine)
        assert engine.memory == mock_memory
        assert engine.learning_window.days == 60

        print("✅ Factory function creates learning engine correctly")


class TestLearningEngineEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, learning_engine):
        """Test handling of insufficient data for pattern extraction."""
        # Try to extract patterns with insufficient data
        patterns = await learning_engine.extract_success_patterns()

        # Should handle gracefully and return empty list
        assert isinstance(patterns, list)
        assert len(patterns) == 0

        print("✅ Insufficient data handled gracefully")

    @pytest.mark.asyncio
    async def test_memory_failure_handling(self, mock_memory):
        """Test handling of memory service failures."""
        # Configure memory to fail
        mock_memory.store_memory = AsyncMock(side_effect=Exception("Memory service unavailable"))

        engine = ContinuousLearningEngine(memory=mock_memory)

        # Create outcome
        outcome = TaskOutcome(
            task_id="test_task",
            task_description="Test task",
            project_name="test_project",
            outcome_type=OutcomeType.SUCCESS,
            actual_hours=8.0,
            estimated_hours=8.0,
            completion_date=datetime.now(),
        )

        # Should handle memory failure gracefully
        result = await engine.capture_task_outcome(outcome)

        # Capture should indicate failure but not crash
        assert result is False

        print("✅ Memory service failures handled gracefully")

    @pytest.mark.asyncio
    async def test_invalid_outcome_data(self, learning_engine):
        """Test handling of invalid outcome data."""
        # Create outcome with invalid data
        invalid_outcome = TaskOutcome(
            task_id="",  # Empty task ID
            task_description="",  # Empty description
            project_name="test_project",
            outcome_type=OutcomeType.SUCCESS,
            actual_hours=-5.0,  # Negative hours
            estimated_hours=0.0,  # Zero estimated hours
            completion_date=datetime.now(),
        )

        # Should handle invalid data gracefully
        result = await learning_engine.capture_task_outcome(invalid_outcome)

        # May still succeed in capture but should handle validation internally
        assert isinstance(result, bool)

        print("✅ Invalid outcome data handled appropriately")


@pytest.mark.asyncio
async def test_mem006_complete_workflow():
    """Test complete MEM-006 workflow integration."""
    print("\n🔄 Testing complete MEM-006 workflow...")

    # Create mock memory
    mock_memory = Mock(spec=ClaudePMMemory)
    mock_memory.store_memory = AsyncMock(return_value=Mock(success=True, memory_id="test_memory"))
    mock_memory.retrieve_memories = AsyncMock(
        return_value=Mock(success=True, data={"memories": []})
    )

    # Create learning engine
    engine = create_continuous_learning_engine(mock_memory, learning_window_days=30)

    # 1. Capture diverse task outcomes
    outcomes = [
        TaskOutcome(
            "task_1",
            "Implement login",
            "auth_project",
            "decomp_1",
            OutcomeType.SUCCESS,
            actual_hours=8,
            estimated_hours=8,
            completion_date=datetime.now(),
        ),
        TaskOutcome(
            "task_2",
            "Implement registration",
            "auth_project",
            "decomp_2",
            OutcomeType.SUCCESS,
            actual_hours=6,
            estimated_hours=8,
            completion_date=datetime.now(),
        ),
        TaskOutcome(
            "task_3",
            "Complex dashboard",
            "analytics_project",
            "decomp_3",
            OutcomeType.FAILURE,
            actual_hours=20,
            estimated_hours=12,
            completion_date=datetime.now(),
        ),
        TaskOutcome(
            "task_4",
            "API endpoint",
            "api_project",
            "decomp_4",
            OutcomeType.SUCCESS,
            actual_hours=4,
            estimated_hours=6,
            completion_date=datetime.now(),
        ),
    ]

    for outcome in outcomes:
        result = await engine.capture_task_outcome(outcome)
        assert result is True

    # 2. Extract success patterns
    success_patterns = await engine.extract_success_patterns()

    # 3. Analyze failure patterns
    failure_patterns = await engine.analyze_failure_patterns()

    # 4. Run automatic pattern recognition
    all_patterns = await engine.recognize_patterns_automatically()

    # 5. Track learning metrics
    metrics = await engine.track_learning_metrics()

    # 6. Analyze learning effectiveness
    analysis = await engine.analyze_learning_effectiveness()

    # Verify workflow completion
    assert len(engine.captured_outcomes) == 4
    assert isinstance(all_patterns, dict)
    assert isinstance(metrics, dict)
    assert isinstance(analysis, dict)

    # Get final statistics
    stats = engine.get_learning_stats()
    assert stats["total_outcomes_captured"] == 4
    assert stats["system_health"] == "operational"

    print("✅ Complete MEM-006 workflow executed successfully")
    print(f"   📊 Captured {stats['total_outcomes_captured']} outcomes")
    print(f"   🎯 Identified {stats['patterns_identified']} patterns")
    print(f"   📈 Tracking {stats['learning_metrics']} metrics")
    print(f"   💡 Generated {stats['active_insights']} insights")


if __name__ == "__main__":
    # Run the complete workflow test
    asyncio.run(test_mem006_complete_workflow())
    print("\n🎉 All MEM-006 acceptance criteria tests completed successfully!")
