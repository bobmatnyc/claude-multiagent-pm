#!/usr/bin/env python3
"""
Performance tests for Mem0ContextManager.
Tests context preparation performance under various scenarios.
"""

import asyncio
import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.mem0_context_manager import (
    Mem0ContextManager, ContextRequest, ContextType, ContextScope
)
from claude_pm.services.memory_service import MemoryCategory


class MemoryResponse:
    """Mock memory response."""
    def __init__(self, success: bool, data: Dict[str, Any], message: str):
        self.success = success
        self.data = data
        self.message = message


class MockMemory:
    """Mock memory service for performance testing."""
    
    def __init__(self, response_delay: float = 0.01):
        self.response_delay = response_delay
        self.operations_count = 0
        
    async def retrieve_memories(self, **kwargs) -> MemoryResponse:
        """Mock memory retrieval with configurable delay."""
        self.operations_count += 1
        await asyncio.sleep(self.response_delay)
        
        # Return mock memories
        mock_memories = [
            {
                "id": f"mem_{i}",
                "content": f"Mock memory content {i}",
                "metadata": {
                    "category": kwargs.get("category", "pattern").value,
                    "project": kwargs.get("project_filter", "test_project"),
                    "tags": ["test", "performance"],
                    "stored_at": "2023-12-01T10:00:00Z",
                    "security_level": "public",
                    "team_access": "all"
                }
            }
            for i in range(min(kwargs.get("limit", 10), 10))
        ]
        
        return MemoryResponse(
            success=True,
            data={"memories": mock_memories},
            message="Success"
        )


async def test_basic_context_preparation_performance(context_manager):
    """Test basic context preparation performance."""
    request = ContextRequest(
        context_type=ContextType.AGENT_TASK,
        scope=ContextScope.PROJECT_SPECIFIC,
        project_name="test_project",
        agent_type="engineer",
        task_description="Test task",
        keywords=["test", "performance"],
        max_memories=20
    )
    
    # Measure single preparation time
    start_time = time.time()
    context = await context_manager.prepare_context(request)
    end_time = time.time()
    
    preparation_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Assert performance expectations
    assert preparation_time < 500, f"Context preparation took {preparation_time}ms, should be < 500ms"
    assert context.preparation_time_ms > 0, "Context should record preparation time"
    assert context.total_memories > 0, "Context should contain memories"
    
    print(f"✅ Basic context preparation: {preparation_time:.2f}ms")


async def test_parallel_context_preparation_performance(context_manager):
    """Test parallel context preparation performance."""
    requests = [
        ContextRequest(
            context_type=ContextType.AGENT_TASK,
            scope=ContextScope.PROJECT_SPECIFIC,
            project_name="test_project",
            agent_type=f"agent_{i}",
            task_description=f"Test task {i}",
            keywords=["test", "performance"],
            max_memories=10
        )
        for i in range(5)
    ]
    
    # Measure parallel preparation time
    start_time = time.time()
    contexts = await asyncio.gather(*[
        context_manager.prepare_context(request) for request in requests
    ])
    end_time = time.time()
    
    parallel_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Assert performance expectations
    assert parallel_time < 1000, f"Parallel context preparation took {parallel_time}ms, should be < 1000ms"
    assert len(contexts) == 5, "Should return 5 contexts"
    
    # Check that parallel execution is faster than sequential
    # Sequential would be approximately 5 * single_time
    estimated_sequential_time = 5 * 100  # Conservative estimate
    assert parallel_time < estimated_sequential_time, "Parallel execution should be faster than sequential"
    
    print(f"✅ Parallel context preparation (5 contexts): {parallel_time:.2f}ms")


async def test_context_caching_performance(context_manager):
    """Test context caching performance improvement."""
    request = ContextRequest(
        context_type=ContextType.AGENT_TASK,
        scope=ContextScope.PROJECT_SPECIFIC,
        project_name="test_project",
        agent_type="engineer",
        task_description="Test caching",
        keywords=["test", "cache"],
        max_memories=20
    )
    
    # First request (cache miss)
    start_time = time.time()
    context1 = await context_manager.prepare_context(request)
    first_time = (time.time() - start_time) * 1000
    
    # Second request (cache hit)
    start_time = time.time()
    context2 = await context_manager.prepare_context(request)
    second_time = (time.time() - start_time) * 1000
    
    # Assert caching performance
    assert second_time < first_time / 2, f"Cached request ({second_time:.2f}ms) should be much faster than first ({first_time:.2f}ms)"
    assert context1.context_id != context2.context_id, "Cached context should have different ID"
    assert context1.total_memories == context2.total_memories, "Cached context should have same memory count"
    
    print(f"✅ Context caching: First {first_time:.2f}ms, Cached {second_time:.2f}ms")


async def test_large_context_preparation_performance(context_manager):
    """Test performance with large context requests."""
    request = ContextRequest(
        context_type=ContextType.AGENT_TASK,
        scope=ContextScope.CROSS_PROJECT,
        project_name="large_project",
        agent_type="architect",
        task_description="Large scale architecture design with multiple patterns and considerations",
        keywords=["architecture", "patterns", "scalability", "performance", "security", "design"],
        categories=[MemoryCategory.PATTERN, MemoryCategory.PROJECT, MemoryCategory.TEAM, MemoryCategory.ERROR],
        max_memories=50
    )
    
    # Measure large context preparation
    start_time = time.time()
    context = await context_manager.prepare_context(request)
    end_time = time.time()
    
    preparation_time = (end_time - start_time) * 1000
    
    # Assert performance for large context
    assert preparation_time < 2000, f"Large context preparation took {preparation_time}ms, should be < 2000ms"
    assert context.total_memories > 0, "Large context should contain memories"
    
    print(f"✅ Large context preparation: {preparation_time:.2f}ms")


async def test_context_filtering_performance(context_manager):
    """Test performance of context filtering operations."""
    request = ContextRequest(
        context_type=ContextType.CODE_REVIEW,
        scope=ContextScope.PROJECT_SPECIFIC,
        project_name="test_project",
        agent_type="code_review_engineer",
        task_description="Comprehensive code review with security and performance analysis",
        keywords=["code_review", "security", "performance", "quality"],
        max_memories=30
    )
    
    # Measure context preparation with filtering
    start_time = time.time()
    context = await context_manager.prepare_context(request)
    end_time = time.time()
    
    preparation_time = (end_time - start_time) * 1000
    
    # Assert filtering performance
    assert preparation_time < 1000, f"Context with filtering took {preparation_time}ms, should be < 1000ms"
    assert len(context.context_filters_applied) > 0, "Context should have filters applied"
    assert context.security_level in ["public", "team_only"], "Context should have security level set"
    
    print(f"✅ Context filtering: {preparation_time:.2f}ms with {len(context.context_filters_applied)} filters")


async def test_memory_retrieval_performance_under_load(context_manager):
    """Test memory retrieval performance under concurrent load."""
    # Create multiple different requests to avoid caching
    requests = [
        ContextRequest(
            context_type=ContextType.AGENT_TASK,
            scope=ContextScope.PROJECT_SPECIFIC,
            project_name=f"project_{i}",
            agent_type="engineer",
            task_description=f"Load test task {i}",
            keywords=[f"load_{i}", "test"],
            max_memories=15
        )
        for i in range(10)
    ]
    
    # Measure concurrent load performance
    start_time = time.time()
    contexts = await asyncio.gather(*[
        context_manager.prepare_context(request) for request in requests
    ])
    end_time = time.time()
    
    total_time = (end_time - start_time) * 1000
    average_time = total_time / len(contexts)
    
    # Assert load performance
    assert total_time < 3000, f"Load test took {total_time}ms, should be < 3000ms"
    assert average_time < 300, f"Average per context was {average_time}ms, should be < 300ms"
    assert len(contexts) == 10, "Should handle all 10 concurrent requests"
    
    print(f"✅ Load test (10 concurrent): {total_time:.2f}ms total, {average_time:.2f}ms average")


async def test_pattern_recognition_performance(context_manager):
    """Test pattern recognition performance impact."""
    request = ContextRequest(
        context_type=ContextType.PATTERN_MATCHING,
        scope=ContextScope.GLOBAL_PATTERNS,
        keywords=["pattern", "recognition", "performance"],
        categories=[MemoryCategory.PATTERN],
        max_memories=25
    )
    
    # Measure pattern recognition performance
    start_time = time.time()
    context = await context_manager.prepare_context(request)
    end_time = time.time()
    
    preparation_time = (end_time - start_time) * 1000
    
    # Assert pattern recognition performance
    assert preparation_time < 800, f"Pattern recognition took {preparation_time}ms, should be < 800ms"
    assert len(context.patterns) > 0, "Context should contain patterns"
    
    print(f"✅ Pattern recognition: {preparation_time:.2f}ms")


async def test_context_stats_performance(context_manager):
    """Test context statistics performance."""
    # Prepare several contexts first
    requests = [
        ContextRequest(
            context_type=ContextType.AGENT_TASK,
            scope=ContextScope.PROJECT_SPECIFIC,
            project_name="stats_project",
            agent_type=f"agent_{i}",
            task_description=f"Stats test {i}",
            keywords=["stats", "test"],
            max_memories=10
        )
        for i in range(3)
    ]
    
    # Prepare contexts
    contexts = await asyncio.gather(*[
        context_manager.prepare_context(request) for request in requests
    ])
    
    # Measure stats performance
    start_time = time.time()
    stats = context_manager.get_context_stats()
    end_time = time.time()
    
    stats_time = (end_time - start_time) * 1000
    
    # Assert stats performance
    assert stats_time < 10, f"Stats retrieval took {stats_time}ms, should be < 10ms"
    assert "cached_contexts" in stats, "Stats should include cached contexts"
    assert "agent_roles_supported" in stats, "Stats should include agent roles"
    assert stats["cached_contexts"] >= 3, "Should have cached contexts"
    
    print(f"✅ Context stats: {stats_time:.2f}ms")


async def run_performance_benchmark():
    """Run comprehensive performance benchmark."""
    print("🚀 Starting Mem0ContextManager Performance Benchmark")
    print("=" * 60)
    
    # Initialize mock memory with realistic delay
    mock_memory = MockMemory(response_delay=0.05)  # 50ms delay
    context_manager = Mem0ContextManager(mock_memory)
    
    # Run all performance tests
    test_functions = [
        test_basic_context_preparation_performance,
        test_parallel_context_preparation_performance,
        test_context_caching_performance,
        test_large_context_preparation_performance,
        test_context_filtering_performance,
        test_memory_retrieval_performance_under_load,
        test_pattern_recognition_performance,
        test_context_stats_performance
    ]
    
    results = []
    
    for test_func in test_functions:
        print(f"\n🔧 Running {test_func.__name__}...")
        try:
            start_time = time.time()
            await test_func(context_manager)
            end_time = time.time()
            test_time = (end_time - start_time) * 1000
            results.append(test_time)
            print(f"   ✅ Completed in {test_time:.2f}ms")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append(None)
    
    # Performance summary
    print("\n📊 Performance Summary:")
    print("=" * 40)
    valid_results = [r for r in results if r is not None]
    if valid_results:
        print(f"Tests Passed: {len(valid_results)}/{len(test_functions)}")
        print(f"Total Test Time: {sum(valid_results):.2f}ms")
        print(f"Average Test Time: {statistics.mean(valid_results):.2f}ms")
        print(f"Memory Operations: {mock_memory.operations_count}")
    
    print("\n🎯 Performance Test Complete!")
    return len(valid_results) == len(test_functions)


if __name__ == "__main__":
    # Run performance benchmark
    success = asyncio.run(run_performance_benchmark())
    
    if success:
        print("\n✅ All performance tests passed!")
    else:
        print("\n❌ Some performance tests failed!")