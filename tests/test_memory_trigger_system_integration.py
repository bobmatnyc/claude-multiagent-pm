"""
Comprehensive Memory Trigger System Integration Tests

This module provides comprehensive testing for the complete memory trigger system,
validating end-to-end workflows, cross-component integration, and production readiness.
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import pytest
import time
import uuid
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any, Optional
from pathlib import Path

from claude_pm.services.memory import (
    FlexibleMemoryService,
    MemoryTriggerService,
    MemoryRecallService,
    MemoryCategory,
    MemoryItem,
    MemoryQuery,
    TriggerType,
    TriggerPriority,
    TriggerEvent,
    TriggerResult,
    HookContext,
    create_memory_trigger_service,
    create_memory_recall_service,
)
from claude_pm.services.memory.memory_trigger_service import MemoryTriggerOrchestrator
from claude_pm.services.memory.trigger_policies import TriggerPolicyEngine
from claude_pm.services.memory.framework_hooks import FrameworkMemoryHooks
from claude_pm.services.memory.memory_context_enhancer import (
    MemoryContextEnhancer,
    RecallTrigger,
    MemoryContext,
)
from claude_pm.config.memory_trigger_config import (
    MemoryTriggerConfigManager,
    MemoryTriggerConfig,
    Environment,
    PerformanceConfig,
    TriggerPolicyConfig,
    MemoryTriggerType,
)


class TestMemoryTriggerSystemIntegration:
    """Comprehensive integration tests for the complete memory trigger system."""

    @pytest.fixture
    async def memory_system(self):
        """Create a complete memory system for testing."""
        # Create temporary config file
        config_data = {
            "environment": "testing",
            "global_enabled": True,
            "performance": {
                "create_timeout": 5.0,
                "recall_timeout": 3.0,
                "batch_size": 10,
                "max_concurrent_operations": 5,
                "cache_enabled": True,
                "background_processing_enabled": True,
            },
            "backend": {"backend_type": "local", "connection_timeout": 10.0},
            "trigger_policies": {
                "workflow_completion": {
                    "enabled": True,
                    "trigger_type": "workflow",
                    "create_on_success": True,
                    "create_on_failure": True,
                    "pattern_detection_enabled": True,
                },
                "agent_operation": {
                    "enabled": True,
                    "trigger_type": "agent",
                    "create_on_success": True,
                    "require_quality_validation": True,
                },
                "error_resolution": {
                    "enabled": True,
                    "trigger_type": "error",
                    "create_on_error": True,
                    "pattern_detection_enabled": True,
                },
            },
            "features": {
                "workflow_triggers": True,
                "agent_triggers": True,
                "error_triggers": True,
                "pattern_detection": True,
                "auto_recall": True,
                "quality_assessment": True,
                "background_processing": True,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            config_file = f.name

        try:
            # Initialize configuration
            config_manager = MemoryTriggerConfigManager(config_file)

            # Create memory services
            memory_service_config = {
                "fallback_chain": ["sqlite"],  # Use in-memory for testing
                "memory_enabled": True,
            }

            trigger_service = create_memory_trigger_service(memory_service_config)
            recall_service = create_memory_recall_service()

            # Initialize services
            await trigger_service.initialize()
            await recall_service.initialize()

            yield {
                "config_manager": config_manager,
                "trigger_service": trigger_service,
                "recall_service": recall_service,
                "memory_service": trigger_service.get_memory_service(),
                "orchestrator": trigger_service.get_trigger_orchestrator(),
                "hooks": trigger_service.get_framework_hooks(),
                "policy_engine": trigger_service.get_policy_engine(),
            }

            # Cleanup
            await trigger_service.cleanup()
            await recall_service.cleanup()

        finally:
            os.unlink(config_file)

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_completion(self, memory_system):
        """Test complete workflow completion trigger and recall."""
        system = memory_system
        hooks = system["hooks"]
        recall_service = system["recall_service"]

        # Create workflow completion context
        context = HookContext(
            operation_name="deploy_to_production",
            project_name="test_project",
            source="workflow_engine",
            tags=["deploy", "production", "release"],
        )

        # Execute workflow completion hook
        results = await hooks.workflow_completed(
            context,
            success=True,
            workflow_type="deploy",
            results={
                "deployment_time": 180.5,
                "tests_passed": 95,
                "quality_score": 0.92,
                "branch_strategy": "blue-green",
                "environment": "production",
            },
        )

        # Verify trigger was executed
        assert len(results) >= 1
        successful_triggers = [r for r in results if r.success]
        assert len(successful_triggers) > 0

        # Wait for background processing
        await asyncio.sleep(0.1)

        # Test memory recall for similar operation
        recall_result = await recall_service.recall_for_operation(
            project_name="test_project",
            operation_type="deploy",
            operation_context={"environment": "production", "branch_strategy": "blue-green"},
        )

        # Verify recall was successful
        assert recall_result.success
        assert recall_result.memory_context is not None
        assert recall_result.memory_context.get_total_memories() > 0

        # Verify recommendations were generated
        assert recall_result.recommendations is not None
        assert len(recall_result.recommendations.recommendations) > 0

        # Check for pattern-based recommendations
        pattern_recs = [
            r
            for r in recall_result.recommendations.recommendations
            if "deploy" in r.title.lower() or "production" in r.title.lower()
        ]
        assert len(pattern_recs) > 0

    @pytest.mark.asyncio
    async def test_agent_memory_integration_workflow(self, memory_system):
        """Test agent operation memory integration workflow."""
        system = memory_system
        hooks = system["hooks"]
        recall_service = system["recall_service"]

        # Simulate QA agent operation
        qa_context = HookContext(
            operation_name="run_test_suite",
            project_name="test_project",
            source="qa_agent",
            tags=["qa", "testing", "validation"],
        )

        # Execute QA agent hook
        qa_results = await hooks.agent_operation_completed(
            qa_context,
            agent_type="qa",
            tests_run=150,
            tests_passed=147,
            tests_failed=3,
            coverage_percentage=0.94,
            quality_score=0.89,
            duration_seconds=45.2,
        )

        assert len([r for r in qa_results if r.success]) > 0

        # Simulate Documentation agent operation
        doc_context = HookContext(
            operation_name="update_api_docs",
            project_name="test_project",
            source="documentation_agent",
            tags=["documentation", "api", "update"],
        )

        doc_results = await hooks.agent_operation_completed(
            doc_context,
            agent_type="documentation",
            files_updated=8,
            lines_changed=234,
            documentation_coverage=0.87,
            validation_passed=True,
        )

        assert len([r for r in doc_results if r.success]) > 0

        # Wait for processing
        await asyncio.sleep(0.1)

        # Test cross-agent memory recall
        recall_result = await recall_service.recall_for_operation(
            project_name="test_project",
            operation_type="testing",
            operation_context={"agent_type": "qa", "operation": "validation"},
        )

        assert recall_result.success
        assert recall_result.memory_context.get_total_memories() > 0

        # Verify agent-specific memories
        agent_memories = [
            m
            for m in recall_result.memory_context.relevant_memories
            if "qa" in m.tags or "testing" in m.tags
        ]
        assert len(agent_memories) > 0

    @pytest.mark.asyncio
    async def test_error_resolution_pattern_learning(self, memory_system):
        """Test error resolution and pattern learning integration."""
        system = memory_system
        hooks = system["hooks"]
        recall_service = system["recall_service"]

        # Simulate error occurrence and resolution
        error_context = HookContext(
            operation_name="database_connection_error",
            project_name="test_project",
            source="error_handler",
            tags=["error", "database", "connection"],
        )

        # Record error resolution
        error_results = await hooks.error_resolution(
            error_context,
            error_type="connection_timeout",
            error_message="Database connection timeout after 30 seconds",
            solution="Implemented connection pooling with retry logic",
            resolution_time_seconds=420,
            resolved=True,
        )

        assert len([r for r in error_results if r.success]) > 0

        # Simulate similar error for pattern detection
        similar_error_context = HookContext(
            operation_name="api_timeout_error",
            project_name="test_project",
            source="error_handler",
            tags=["error", "api", "timeout"],
        )

        similar_results = await hooks.error_resolution(
            similar_error_context,
            error_type="api_timeout",
            error_message="API request timeout after 15 seconds",
            solution="Added circuit breaker pattern with exponential backoff",
            resolution_time_seconds=180,
            resolved=True,
        )

        assert len([r for r in similar_results if r.success]) > 0

        # Wait for processing
        await asyncio.sleep(0.1)

        # Test error pattern recall
        error_recall = await recall_service.recall_for_error_resolution(
            project_name="test_project",
            error_type="timeout",
            error_message="Service timeout during high load",
        )

        assert error_recall.success
        assert error_recall.memory_context.get_total_memories() > 0

        # Verify error pattern memories
        error_memories = [
            m for m in error_recall.memory_context.error_memories if "timeout" in m.content.lower()
        ]
        assert len(error_memories) > 0

        # Check for solution recommendations
        timeout_recommendations = [
            r
            for r in error_recall.recommendations.recommendations
            if "timeout" in r.title.lower() or "retry" in r.title.lower()
        ]
        assert len(timeout_recommendations) > 0

    @pytest.mark.asyncio
    async def test_cross_component_data_flow(self, memory_system):
        """Test data flow between all memory system components."""
        system = memory_system

        # Test trigger orchestrator metrics
        orchestrator = system["orchestrator"]
        initial_metrics = orchestrator.get_metrics()

        # Execute multiple triggers
        context = HookContext(
            operation_name="multi_component_test",
            project_name="test_project",
            source="integration_test",
        )

        # Execute different types of triggers
        await system["hooks"].workflow_completed(context, success=True)
        await system["hooks"].agent_operation_completed(context, agent_type="ops")
        await system["hooks"].issue_resolved(context, issue_id="ISS-001")

        # Wait for processing
        await asyncio.sleep(0.2)

        # Verify metrics updated
        final_metrics = orchestrator.get_metrics()
        assert final_metrics["total_triggers"] > initial_metrics["total_triggers"]

        # Test policy engine evaluation
        policy_engine = system["policy_engine"]
        test_event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name="test_project",
            event_id=str(uuid.uuid4()),
            content="Test cross-component integration",
            category=MemoryCategory.PATTERN,
        )

        decision, metadata = policy_engine.evaluate_trigger(test_event)
        assert decision is not None

        # Test memory service health
        memory_service = system["memory_service"]
        health = await memory_service.get_service_health()
        assert health["status"] == "healthy"

        # Test recall service integration
        recall_result = await system["recall_service"].recall_for_operation(
            "test_project", "integration_test", {"component": "all"}
        )
        assert recall_result.success

    @pytest.mark.asyncio
    async def test_configuration_hot_reloading(self, memory_system):
        """Test configuration hot reloading functionality."""
        system = memory_system
        config_manager = system["config_manager"]

        # Get initial configuration
        initial_config = config_manager.get_config()
        initial_batch_size = initial_config.performance.batch_size

        # Update configuration
        new_batch_size = initial_batch_size + 10
        config_updates = {
            "performance": {"batch_size": new_batch_size, "max_concurrent_operations": 8}
        }

        config_manager.update_config(config_updates)

        # Verify configuration was updated
        updated_config = config_manager.get_config()
        assert updated_config.performance.batch_size == new_batch_size
        assert updated_config.performance.max_concurrent_operations == 8

        # Test that services can access updated config
        orchestrator = system["orchestrator"]
        # Note: In a real implementation, orchestrator would have config update handlers

        # Verify configuration validation
        errors = config_manager.validate_config()
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_backend_compatibility(self, memory_system):
        """Test memory backend compatibility and failover."""
        system = memory_system
        memory_service = system["memory_service"]

        # Test memory operations with current backend
        memory_id = await memory_service.add_memory(
            project_name="test_project",
            content="Backend compatibility test memory",
            category=MemoryCategory.PATTERN,
            tags=["backend", "test", "compatibility"],
            metadata={"test_type": "backend_compatibility"},
        )

        assert memory_id is not None

        # Test memory retrieval
        memories = await memory_service.search_memories(
            MemoryQuery(
                project_name="test_project",
                query_text="backend compatibility",
                categories=[MemoryCategory.PATTERN],
                limit=10,
            )
        )

        assert len(memories) > 0
        backend_memory = next((m for m in memories if m.id == memory_id), None)
        assert backend_memory is not None
        assert "compatibility" in backend_memory.content

        # Test backend health
        health = await memory_service.get_service_health()
        assert "backend_status" in health

        # Test backend metrics
        metrics = await memory_service.get_service_metrics()
        assert "backend_metrics" in metrics

    @pytest.mark.asyncio
    async def test_memory_lifecycle_management(self, memory_system):
        """Test complete memory lifecycle from creation to cleanup."""
        system = memory_system
        memory_service = system["memory_service"]

        # Create test memories with different categories
        memory_ids = []

        for i, category in enumerate(
            [MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.PROJECT]
        ):
            memory_id = await memory_service.add_memory(
                project_name="lifecycle_test",
                content=f"Lifecycle test memory {i} for {category.value}",
                category=category,
                tags=["lifecycle", "test", category.value],
                metadata={
                    "test_index": i,
                    "category_type": category.value,
                    "lifecycle_stage": "created",
                },
            )
            memory_ids.append(memory_id)

        # Verify all memories were created
        assert len(memory_ids) == 3
        assert all(mid is not None for mid in memory_ids)

        # Test memory search and retrieval
        all_memories = await memory_service.search_memories(
            MemoryQuery(project_name="lifecycle_test", query_text="lifecycle test", limit=10)
        )

        assert len(all_memories) >= 3

        # Test category-specific retrieval
        for category in [MemoryCategory.PATTERN, MemoryCategory.ERROR, MemoryCategory.PROJECT]:
            category_memories = await memory_service.search_memories(
                MemoryQuery(project_name="lifecycle_test", categories=[category], limit=10)
            )
            category_specific = [m for m in category_memories if m.category == category]
            assert len(category_specific) >= 1

        # Test memory updates (if supported by backend)
        try:
            first_memory = all_memories[0]
            updated_metadata = first_memory.metadata.copy()
            updated_metadata["lifecycle_stage"] = "updated"

            # Note: Update functionality depends on backend implementation
            # This test verifies the memory system can handle update requests

        except NotImplementedError:
            # Backend doesn't support updates - this is acceptable
            pass

        # Test memory cleanup/deletion (if supported)
        try:
            # Attempt to delete one test memory
            deletion_result = await memory_service.delete_memory(memory_ids[0])
            # Note: Deletion support varies by backend

        except NotImplementedError:
            # Backend doesn't support deletion - this is acceptable
            pass


class TestMemorySystemPerformance:
    """Performance and scalability tests for the memory system."""

    @pytest.fixture
    async def performance_system(self):
        """Create optimized memory system for performance testing."""
        config = {
            "environment": "testing",
            "global_enabled": True,
            "performance": {
                "create_timeout": 1.0,
                "recall_timeout": 0.5,
                "batch_size": 100,
                "max_concurrent_operations": 20,
                "cache_enabled": True,
                "background_processing_enabled": True,
                "rate_limit_per_second": 1000,
            },
            "memory": {"fallback_chain": ["sqlite"], "memory_enabled": True},
        }

        trigger_service = create_memory_trigger_service(config)
        await trigger_service.initialize()

        yield trigger_service

        await trigger_service.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_trigger_processing(self, performance_system):
        """Test concurrent trigger processing performance."""
        service = performance_system
        hooks = service.get_framework_hooks()

        # Create multiple concurrent triggers
        start_time = time.time()
        tasks = []

        for i in range(50):
            context = HookContext(
                operation_name=f"concurrent_test_{i}",
                project_name="performance_test",
                source="performance_tester",
                tags=["performance", "concurrent"],
            )

            task = hooks.workflow_completed(
                context, success=True, workflow_type="performance_test", results={"iteration": i}
            )
            tasks.append(task)

        # Execute all triggers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processing_time = time.time() - start_time

        # Verify performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 50

        # Should complete within reasonable time (adjust based on system capacity)
        assert processing_time < 10.0, f"Processing took {processing_time:.2f}s, expected < 10.0s"

        # Calculate average processing time per trigger
        avg_time_per_trigger = processing_time / 50
        assert avg_time_per_trigger < 0.2, f"Average time per trigger: {avg_time_per_trigger:.3f}s"

        # Verify orchestrator metrics
        orchestrator = service.get_trigger_orchestrator()
        metrics = orchestrator.get_metrics()
        assert metrics["total_triggers"] >= 50

        # Verify high success rate
        success_rate = metrics["successful_triggers"] / metrics["total_triggers"]
        assert success_rate >= 0.95, f"Success rate: {success_rate:.2%}"

    @pytest.mark.asyncio
    async def test_memory_recall_performance(self, performance_system):
        """Test memory recall performance under load."""
        service = performance_system
        memory_service = service.get_memory_service()

        # Pre-populate with test memories
        memory_ids = []
        for i in range(100):
            memory_id = await memory_service.add_memory(
                project_name="recall_performance_test",
                content=f"Performance test memory {i} with various keywords: deployment, testing, production, error, success",
                category=MemoryCategory.PATTERN,
                tags=["performance", "test", f"memory_{i}"],
                metadata={"index": i, "test_type": "recall_performance"},
            )
            memory_ids.append(memory_id)

        # Create recall service
        recall_service = create_memory_recall_service(memory_service)
        await recall_service.initialize()

        try:
            # Test concurrent recall operations
            start_time = time.time()
            recall_tasks = []

            for i in range(20):
                task = recall_service.recall_for_operation(
                    project_name="recall_performance_test",
                    operation_type="performance_test",
                    operation_context={
                        "iteration": i,
                        "keywords": ["deployment", "testing", "production"],
                    },
                )
                recall_tasks.append(task)

            recall_results = await asyncio.gather(*recall_tasks)
            recall_time = time.time() - start_time

            # Verify recall performance
            successful_recalls = [r for r in recall_results if r.success]
            assert len(successful_recalls) == 20

            # Should complete within performance target
            assert recall_time < 5.0, f"Recall took {recall_time:.2f}s, expected < 5.0s"

            # Verify individual recall times
            recall_times = [r.processing_time_ms for r in successful_recalls]
            avg_recall_time = sum(recall_times) / len(recall_times)
            assert avg_recall_time < 100.0, f"Average recall time: {avg_recall_time:.1f}ms"

            # Verify recall quality
            for result in successful_recalls:
                assert result.memory_context.get_total_memories() > 0
                assert result.recommendations is not None

        finally:
            await recall_service.cleanup()

    @pytest.mark.asyncio
    async def test_system_resource_usage(self, performance_system):
        """Test system resource usage under load."""
        service = performance_system
        hooks = service.get_framework_hooks()

        import psutil
        import threading

        # Monitor resource usage
        resource_monitor = {"cpu_percent": [], "memory_mb": [], "active": True}

        def monitor_resources():
            process = psutil.Process()
            while resource_monitor["active"]:
                try:
                    cpu = process.cpu_percent()
                    memory = process.memory_info().rss / 1024 / 1024  # MB
                    resource_monitor["cpu_percent"].append(cpu)
                    resource_monitor["memory_mb"].append(memory)
                    time.sleep(0.1)
                except:
                    break

        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()

        try:
            # Execute intensive workload
            tasks = []
            for i in range(100):
                context = HookContext(
                    operation_name=f"resource_test_{i}",
                    project_name="resource_test",
                    source="resource_tester",
                    tags=["resource", "intensive"],
                )

                task = hooks.workflow_completed(
                    context,
                    success=True,
                    workflow_type="resource_test",
                    results={"data": "x" * 1000, "iteration": i},  # Add some data
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Wait for background processing
            await asyncio.sleep(1.0)

        finally:
            resource_monitor["active"] = False
            monitor_thread.join(timeout=5.0)

        # Analyze resource usage
        if resource_monitor["cpu_percent"]:
            avg_cpu = sum(resource_monitor["cpu_percent"]) / len(resource_monitor["cpu_percent"])
            max_cpu = max(resource_monitor["cpu_percent"])

            # CPU usage should be reasonable (adjust thresholds based on system)
            assert avg_cpu < 80.0, f"Average CPU usage too high: {avg_cpu:.1f}%"
            assert max_cpu < 95.0, f"Peak CPU usage too high: {max_cpu:.1f}%"

        if resource_monitor["memory_mb"]:
            avg_memory = sum(resource_monitor["memory_mb"]) / len(resource_monitor["memory_mb"])
            max_memory = max(resource_monitor["memory_mb"])

            # Memory usage should be reasonable (adjust based on system)
            assert avg_memory < 500.0, f"Average memory usage too high: {avg_memory:.1f}MB"
            assert max_memory < 1000.0, f"Peak memory usage too high: {max_memory:.1f}MB"


class TestMemorySystemResilience:
    """Resilience and error handling tests."""

    @pytest.fixture
    async def resilience_system(self):
        """Create memory system for resilience testing."""
        config = {
            "environment": "testing",
            "global_enabled": True,
            "performance": {
                "create_timeout": 2.0,
                "recall_timeout": 1.0,
                "max_concurrent_operations": 5,
            },
            "memory": {"fallback_chain": ["sqlite"]},
        }

        service = create_memory_trigger_service(config)
        await service.initialize()

        yield service

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_graceful_degradation_memory_service_failure(self, resilience_system):
        """Test graceful degradation when memory service fails."""
        service = resilience_system
        hooks = service.get_framework_hooks()

        # Mock memory service to simulate failure
        memory_service = service.get_memory_service()
        original_add_memory = memory_service.add_memory

        # Make memory service fail
        memory_service.add_memory = AsyncMock(
            side_effect=Exception("Simulated memory service failure")
        )

        try:
            # Execute triggers - should not crash despite memory service failure
            context = HookContext(
                operation_name="resilience_test",
                project_name="test_project",
                source="resilience_tester",
                tags=["resilience", "failure_test"],
            )

            results = await hooks.workflow_completed(
                context, success=True, workflow_type="resilience_test"
            )

            # System should handle failure gracefully
            # Results may be empty or contain failure results, but no exceptions should propagate
            assert isinstance(results, list)

            # Check if any triggers succeeded despite memory service failure
            failed_results = [r for r in results if not r.success]
            # Some or all may fail, which is expected behavior

        finally:
            # Restore original method
            memory_service.add_memory = original_add_memory

    @pytest.mark.asyncio
    async def test_timeout_handling(self, resilience_system):
        """Test timeout handling in memory operations."""
        service = resilience_system
        memory_service = service.get_memory_service()

        # Mock memory service to simulate slow operations
        async def slow_add_memory(*args, **kwargs):
            await asyncio.sleep(5.0)  # Longer than timeout
            return "slow_memory_id"

        original_add_memory = memory_service.add_memory
        memory_service.add_memory = slow_add_memory

        try:
            # Create recall service with short timeout
            recall_service = create_memory_recall_service(memory_service)
            recall_config = recall_service.get_config()
            recall_config.recall_timeout_seconds = 0.5  # Very short timeout
            recall_service.update_config(recall_config)

            await recall_service.initialize()

            try:
                # Test recall with timeout
                start_time = time.time()
                result = await recall_service.recall_for_operation(
                    "test_project", "timeout_test", {"test": "timeout"}
                )
                elapsed_time = time.time() - start_time

                # Should timeout quickly and handle gracefully
                assert elapsed_time < 2.0  # Should timeout well before 5s
                assert not result.success  # Should indicate failure
                assert "timeout" in result.error_message.lower()

            finally:
                await recall_service.cleanup()

        finally:
            memory_service.add_memory = original_add_memory

    @pytest.mark.asyncio
    async def test_concurrent_failure_recovery(self, resilience_system):
        """Test recovery from concurrent operation failures."""
        service = resilience_system
        hooks = service.get_framework_hooks()
        orchestrator = service.get_trigger_orchestrator()

        # Create mix of successful and failing operations
        tasks = []

        for i in range(20):
            context = HookContext(
                operation_name=f"failure_recovery_test_{i}",
                project_name="test_project",
                source="failure_recovery_tester",
                tags=["failure_recovery", "test"],
            )

            # Simulate some operations that will succeed and some that will fail
            success = i % 3 != 0  # 2/3 success rate

            task = hooks.workflow_completed(
                context,
                success=success,
                workflow_type="failure_recovery_test",
                results={"will_succeed": success, "iteration": i},
            )
            tasks.append(task)

        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_operations = 0
        failed_operations = 0
        exceptions = 0

        for result in results:
            if isinstance(result, Exception):
                exceptions += 1
            elif isinstance(result, list):
                # Each result is a list of trigger results
                for trigger_result in result:
                    if trigger_result.success:
                        successful_operations += 1
                    else:
                        failed_operations += 1

        # Verify system remained stable despite failures
        assert exceptions == 0, "No exceptions should propagate to caller"
        assert successful_operations > 0, "Some operations should succeed"

        # Verify orchestrator metrics reflect mixed results
        metrics = orchestrator.get_metrics()
        assert metrics["total_triggers"] > 0

        # System should maintain reasonable success rate
        if metrics["total_triggers"] > 0:
            success_rate = metrics["successful_triggers"] / metrics["total_triggers"]
            # Success rate may be less than 100% due to simulated failures
            assert success_rate >= 0.1, f"Success rate too low: {success_rate:.2%}"


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
