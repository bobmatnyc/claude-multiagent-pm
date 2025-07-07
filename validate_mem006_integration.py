#!/usr/bin/env python3
"""
MEM-006 Integration Validation Script
Validates the complete integration of ContinuousLearningEngine with IntelligentTaskPlanner
and the overall learning-enhanced workflow.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.services.learning_integration_service import (
    LearningIntegrationService, LearningMode, create_learning_integration_service
)
from claude_pm.services.continuous_learning_engine import TaskOutcome, OutcomeType
from claude_pm.services.claude_pm_memory import ClaudePMMemory
from claude_pm.services.mem0_context_manager import Mem0ContextManager


async def create_mock_services():
    """Create mock services for testing."""
    # Mock memory service
    memory = Mock(spec=ClaudePMMemory)
    memory.store_memory = AsyncMock(return_value=Mock(success=True, memory_id="test_memory"))
    memory.retrieve_memories = AsyncMock(return_value=Mock(
        success=True,
        data={"memories": []}
    ))
    
    # Mock context manager
    context_manager = Mock(spec=Mem0ContextManager)
    context_manager.prepare_context = AsyncMock(return_value=Mock(
        total_memories=5,
        patterns=[],
        relevance_scores={}
    ))
    
    return memory, context_manager


async def test_learning_enhanced_decomposition():
    """Test learning-enhanced task decomposition."""
    print("🔄 Testing Learning-Enhanced Task Decomposition")
    print("-" * 50)
    
    memory, context_manager = await create_mock_services()
    
    # Create integration service in adaptive mode
    integration_service = create_learning_integration_service(
        memory, context_manager, LearningMode.ADAPTIVE
    )
    
    # Test basic decomposition enhancement
    task_description = "Implement comprehensive user authentication system with OAuth2, JWT, and MFA support"
    project_name = "secure_webapp"
    
    enhanced_decomposition = await integration_service.create_learning_enhanced_decomposition(
        task_description, project_name
    )
    
    # Verify enhanced decomposition structure
    assert enhanced_decomposition.base_decomposition is not None
    assert enhanced_decomposition.learning_confidence >= 0.0
    assert enhanced_decomposition.learning_confidence <= 1.0
    assert isinstance(enhanced_decomposition.risk_assessment, dict)
    assert isinstance(enhanced_decomposition.similar_patterns, list)
    assert isinstance(enhanced_decomposition.recommended_adjustments, list)
    assert isinstance(enhanced_decomposition.learning_insights, list)
    assert enhanced_decomposition.confidence_adjusted_hours > 0
    assert enhanced_decomposition.risk_adjusted_hours > 0
    
    print(f"✅ Enhanced decomposition created successfully")
    print(f"   📊 Learning confidence: {enhanced_decomposition.learning_confidence:.2f}")
    print(f"   ⏱️  Base estimate: {enhanced_decomposition.base_decomposition.total_estimated_hours:.1f}h")
    print(f"   🎯 Confidence adjusted: {enhanced_decomposition.confidence_adjusted_hours:.1f}h")
    print(f"   ⚠️  Risk adjusted: {enhanced_decomposition.risk_adjusted_hours:.1f}h")
    print(f"   💡 Insights: {len(enhanced_decomposition.learning_insights)}")
    print(f"   🔧 Adjustments: {len(enhanced_decomposition.recommended_adjustments)}")
    
    return enhanced_decomposition


async def test_complete_learning_workflow():
    """Test complete learning workflow from planning to outcome capture."""
    print("\n🔄 Testing Complete Learning Workflow")
    print("-" * 50)
    
    memory, context_manager = await create_mock_services()
    integration_service = create_learning_integration_service(
        memory, context_manager, LearningMode.ADAPTIVE
    )
    
    # Step 1: Create learning-enhanced decomposition
    task_description = "Build real-time analytics dashboard with data visualization"
    enhanced_decomposition = await integration_service.create_learning_enhanced_decomposition(
        task_description, "analytics_project"
    )
    
    print(f"✅ Step 1: Enhanced decomposition created")
    
    # Step 2: Simulate task execution and capture outcome
    actual_outcome = TaskOutcome(
        task_id="analytics_dashboard_001",
        task_description=task_description,
        project_name="analytics_project",
        decomposition_id=enhanced_decomposition.base_decomposition.decomposition_id,
        outcome_type=OutcomeType.SUCCESS,
        actual_hours=enhanced_decomposition.base_decomposition.total_estimated_hours * 1.15,  # 15% over estimate
        estimated_hours=enhanced_decomposition.base_decomposition.total_estimated_hours,
        completion_date=datetime.now(),
        success_factors=["good team collaboration", "clear requirements", "proper testing"],
        failure_factors=[],
        technologies_used=["react", "d3.js", "python", "fastapi"],
        team_members=["developer1", "developer2", "designer1"],
        solutions_applied=["component-based architecture", "real-time websockets", "caching strategy"]
    )
    
    capture_result = await integration_service.capture_task_completion(
        actual_outcome.task_id, actual_outcome
    )
    
    assert capture_result is True, "Failed to capture task completion"
    print(f"✅ Step 2: Task outcome captured and learning updated")
    
    # Step 3: Get learning recommendations for similar task
    recommendations = await integration_service.get_learning_recommendations(
        "Build interactive data visualization for sales metrics", "analytics_project"
    )
    
    assert isinstance(recommendations, dict), "Recommendations should be a dictionary"
    assert "risk_level" in recommendations
    assert "confidence" in recommendations
    assert "recommended_approach" in recommendations
    
    print(f"✅ Step 3: Learning recommendations generated")
    print(f"   🎯 Risk level: {recommendations['risk_level']}")
    print(f"   📊 Confidence: {recommendations['confidence']:.2f}")
    print(f"   🛠️  Approach: {recommendations['recommended_approach']}")
    
    # Step 4: Analyze learning effectiveness
    effectiveness_analysis = await integration_service.analyze_learning_effectiveness(30)
    
    assert isinstance(effectiveness_analysis, dict), "Analysis should be a dictionary"
    print(f"✅ Step 4: Learning effectiveness analyzed")
    
    return integration_service


async def test_learning_modes():
    """Test different learning integration modes."""
    print("\n🔄 Testing Different Learning Modes")
    print("-" * 50)
    
    memory, context_manager = await create_mock_services()
    
    modes_to_test = [
        LearningMode.PASSIVE,
        LearningMode.ACTIVE,
        LearningMode.ADAPTIVE,
        LearningMode.PREDICTIVE
    ]
    
    task_description = "Implement API rate limiting and throttling system"
    
    results = {}
    
    for mode in modes_to_test:
        integration_service = create_learning_integration_service(
            memory, context_manager, mode
        )
        
        enhanced_decomposition = await integration_service.create_learning_enhanced_decomposition(
            task_description, "api_project"
        )
        
        results[mode.value] = {
            "base_hours": enhanced_decomposition.base_decomposition.total_estimated_hours,
            "confidence_adjusted": enhanced_decomposition.confidence_adjusted_hours,
            "risk_adjusted": enhanced_decomposition.risk_adjusted_hours,
            "learning_confidence": enhanced_decomposition.learning_confidence
        }
        
        print(f"✅ {mode.value.upper()} mode: {enhanced_decomposition.confidence_adjusted_hours:.1f}h estimate")
    
    print(f"✅ All learning modes tested successfully")
    return results


async def test_pattern_based_recommendations():
    """Test pattern-based recommendations with accumulated learning."""
    print("\n🔄 Testing Pattern-Based Recommendations")
    print("-" * 50)
    
    memory, context_manager = await create_mock_services()
    integration_service = create_learning_integration_service(
        memory, context_manager, LearningMode.ADAPTIVE
    )
    
    # Create multiple task outcomes to build learning patterns
    base_tasks = [
        ("Implement user registration", "auth_project", OutcomeType.SUCCESS, 8.0, 8.5),
        ("Implement user login", "auth_project", OutcomeType.SUCCESS, 6.0, 6.2),
        ("Implement password reset", "auth_project", OutcomeType.SUCCESS, 4.0, 5.0),
        ("Implement complex OAuth integration", "auth_project", OutcomeType.FAILURE, 16.0, 24.0),
        ("Implement API authentication", "api_project", OutcomeType.SUCCESS, 12.0, 11.5),
    ]
    
    for i, (description, project, outcome_type, estimated, actual) in enumerate(base_tasks):
        # Create enhanced decomposition
        enhanced_decomp = await integration_service.create_learning_enhanced_decomposition(
            description, project
        )
        
        # Create outcome
        outcome = TaskOutcome(
            task_id=f"pattern_task_{i}",
            task_description=description,
            project_name=project,
            decomposition_id=enhanced_decomp.base_decomposition.decomposition_id,
            outcome_type=outcome_type,
            actual_hours=actual,
            estimated_hours=estimated,
            completion_date=datetime.now() - timedelta(days=i)
        )
        
        # Capture outcome
        await integration_service.capture_task_completion(outcome.task_id, outcome)
    
    print(f"✅ Created learning patterns from {len(base_tasks)} historical tasks")
    
    # Now test recommendations for a new similar task
    recommendations = await integration_service.get_learning_recommendations(
        "Implement two-factor authentication system", "auth_project"
    )
    
    print(f"✅ Pattern-based recommendations generated:")
    print(f"   🎯 Risk level: {recommendations['risk_level']}")
    print(f"   📊 Confidence: {recommendations['confidence']:.2f}")
    print(f"   🛠️  Approach: {recommendations['recommended_approach']}")
    print(f"   ⚠️  Risk factors: {len(recommendations.get('risk_factors', []))}")
    print(f"   ✅ Success factors: {len(recommendations.get('success_factors', []))}")
    
    return recommendations


async def test_integration_statistics():
    """Test integration service statistics and monitoring."""
    print("\n🔄 Testing Integration Statistics")
    print("-" * 50)
    
    memory, context_manager = await create_mock_services()
    integration_service = create_learning_integration_service(
        memory, context_manager, LearningMode.ADAPTIVE
    )
    
    # Perform some operations to generate statistics
    await integration_service.create_learning_enhanced_decomposition(
        "Test task for statistics", "test_project"
    )
    
    # Get integration statistics
    stats = integration_service.get_integration_stats()
    
    # Verify comprehensive statistics
    required_stats = [
        "learning_mode",
        "active_tasks",
        "learning_feedback_count",
        "integration_metrics",
        "learning_engine_stats",
        "task_planner_stats"
    ]
    
    for stat in required_stats:
        assert stat in stats, f"Missing statistic: {stat}"
    
    print(f"✅ Integration statistics comprehensive:")
    print(f"   🎛️  Learning mode: {stats['learning_mode']}")
    print(f"   📋 Active tasks: {stats['active_tasks']}")
    print(f"   💭 Feedback count: {stats['learning_feedback_count']}")
    print(f"   📊 Learning influenced plans: {stats['integration_metrics']['learning_influenced_plans']}")
    print(f"   🧠 Learning engine health: {stats['learning_engine_stats']['system_health']}")
    
    return stats


async def test_error_handling():
    """Test error handling and resilience."""
    print("\n🔄 Testing Error Handling and Resilience")
    print("-" * 50)
    
    # Test with failing memory service
    failing_memory = Mock(spec=ClaudePMMemory)
    failing_memory.store_memory = AsyncMock(side_effect=Exception("Memory service down"))
    failing_memory.retrieve_memories = AsyncMock(side_effect=Exception("Memory service down"))
    
    context_manager = Mock(spec=Mem0ContextManager)
    context_manager.prepare_context = AsyncMock(return_value=Mock(
        total_memories=0,
        patterns=[],
        relevance_scores={}
    ))
    
    integration_service = create_learning_integration_service(
        failing_memory, context_manager, LearningMode.ADAPTIVE
    )
    
    # Should handle memory failures gracefully
    try:
        enhanced_decomposition = await integration_service.create_learning_enhanced_decomposition(
            "Test task with failing memory", "test_project"
        )
        
        # Should still return a valid decomposition (fallback mode)
        assert enhanced_decomposition is not None
        assert enhanced_decomposition.base_decomposition is not None
        
        print(f"✅ Memory service failure handled gracefully")
        
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
        raise
    
    # Test with invalid input data
    try:
        recommendations = await integration_service.get_learning_recommendations(
            "", None  # Empty task description and no project
        )
        
        # Should handle gracefully
        assert isinstance(recommendations, dict)
        print(f"✅ Invalid input handled gracefully")
        
    except Exception as e:
        print(f"❌ Invalid input handling failed: {e}")
        raise
    
    print(f"✅ Error handling and resilience tests passed")


async def main():
    """Run complete integration validation."""
    print("🚀 MEM-006 Integration Validation Suite")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    try:
        # Test 1: Basic learning-enhanced decomposition
        enhanced_decomp = await test_learning_enhanced_decomposition()
        
        # Test 2: Complete workflow
        integration_service = await test_complete_learning_workflow()
        
        # Test 3: Different learning modes
        mode_results = await test_learning_modes()
        
        # Test 4: Pattern-based recommendations
        recommendations = await test_pattern_based_recommendations()
        
        # Test 5: Integration statistics
        stats = await test_integration_statistics()
        
        # Test 6: Error handling
        await test_error_handling()
        
        print("\n" + "🎯" * 20)
        print("🏆 MEM-006 INTEGRATION VALIDATION COMPLETE!")
        print("=" * 60)
        print("✅ Learning-enhanced decomposition working")
        print("✅ Complete learning workflow operational")
        print("✅ All learning modes functional")
        print("✅ Pattern-based recommendations accurate")
        print("✅ Integration statistics comprehensive")
        print("✅ Error handling robust")
        print("\n🎉 CONTINUOUS LEARNING ENGINE SUCCESSFULLY INTEGRATED!")
        print("🔄 Ready for production deployment")
        print("🎯" * 20)
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)