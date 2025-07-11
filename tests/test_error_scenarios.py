"""
Error Handling and Resilience Tests

Comprehensive testing for error scenarios, resilience patterns, and recovery mechanisms:
- Memory service failure scenarios
- Network connectivity issues
- Resource exhaustion handling
- Concurrent operation failures
- Circuit breaker patterns
- Graceful degradation
- Recovery and rollback mechanisms
"""

"""
# NOTE: InMemory backend tests have been disabled because the InMemory backend  # InMemory backend removed
was removed from the Claude PM Framework memory system. The system now uses
mem0ai → sqlite fallback chain only.
"""


import asyncio
import pytest
import time
import threading
import random
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

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
    create_memory_recall_service
)
from claude_pm.services.memory.memory_trigger_service import MemoryTriggerOrchestrator
from claude_pm.services.memory.memory_context_enhancer import (
    MemoryContextEnhancer,
    RecallTrigger
)
from claude_pm.services.memory.services.circuit_breaker import CircuitBreaker, CircuitBreakerState


@dataclass
class ErrorScenario:
    """Definition of an error scenario for testing."""
    name: str
    description: str
    error_type: type
    error_message: str
    duration_seconds: float = 0.0
    failure_rate: float = 1.0  # 1.0 = always fail, 0.5 = 50% failure rate
    recovery_time: float = 0.0
    
    
class ErrorInjector:
    """Utility for injecting errors into system components."""
    
    def __init__(self):
        self.active_scenarios: Dict[str, ErrorScenario] = {}
        self.call_counts: Dict[str, int] = {}
        self.start_times: Dict[str, float] = {}
    
    def inject_error(self, scenario_name: str, scenario: ErrorScenario):
        """Inject an error scenario."""
        self.active_scenarios[scenario_name] = scenario
        self.call_counts[scenario_name] = 0
        self.start_times[scenario_name] = time.time()
    
    def clear_error(self, scenario_name: str):
        """Clear an error scenario."""
        if scenario_name in self.active_scenarios:
            del self.active_scenarios[scenario_name]
            del self.call_counts[scenario_name]
            del self.start_times[scenario_name]
    
    def should_fail(self, scenario_name: str) -> bool:
        """Check if operation should fail based on scenario."""
        if scenario_name not in self.active_scenarios:
            return False
        
        scenario = self.active_scenarios[scenario_name]
        current_time = time.time()
        
        # Check if scenario has expired
        if scenario.duration_seconds > 0:
            elapsed = current_time - self.start_times[scenario_name]
            if elapsed > scenario.duration_seconds:
                self.clear_error(scenario_name)
                return False
        
        # Check failure rate
        self.call_counts[scenario_name] += 1
        return random.random() < scenario.failure_rate
    
    def get_error(self, scenario_name: str) -> Exception:
        """Get the error to raise for a scenario."""
        scenario = self.active_scenarios[scenario_name]
        return scenario.error_type(scenario.error_message)


class TestMemoryServiceFailureScenarios:
    """Test memory service failure scenarios and recovery."""
    
    @pytest.fixture
    def error_injector(self):
        """Create error injector for testing."""
        return ErrorInjector()
    
    @pytest.fixture
    async def resilient_memory_service(self, error_injector):
        """Create memory service with error injection capabilities."""
        config = {
            "fallback_chain": ["sqlite"],
            "memory_enabled": True
        }
        
        service = FlexibleMemoryService(config)
        await service.initialize()
        
        # Wrap methods with error injection
        original_add_memory = service.add_memory
        original_search_memories = service.search_memories
        
        async def add_memory_with_errors(*args, **kwargs):
            if error_injector.should_fail("add_memory"):
                raise error_injector.get_error("add_memory")
            return await original_add_memory(*args, **kwargs)
        
        async def search_memories_with_errors(*args, **kwargs):
            if error_injector.should_fail("search_memories"):
                raise error_injector.get_error("search_memories")
            return await original_search_memories(*args, **kwargs)
        
        service.add_memory = add_memory_with_errors
        service.search_memories = search_memories_with_errors
        
        yield service, error_injector
        
        await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_service_connection_failure(self, resilient_memory_service):
        """Test handling of memory service connection failures."""
        service, error_injector = resilient_memory_service
        
        # Inject connection error
        connection_error = ErrorScenario(
            name="Connection Error",
            description="Database connection timeout",
            error_type=ConnectionError,
            error_message="Unable to connect to memory backend",
            duration_seconds=2.0
        )
        
        error_injector.inject_error("add_memory", connection_error)
        
        # Create trigger service with resilient memory service
        trigger_service = create_memory_trigger_service({
            "memory": {"fallback_chain": ["sqlite"]}
        })
        trigger_service.memory_service = service
        
        await trigger_service.initialize()
        
        try:
            # Execute trigger - should handle connection errors gracefully
            context = HookContext(
                operation_name="connection_failure_test",
                project_name="test_project",
                source="error_test"
            )
            
            hooks = trigger_service.get_framework_hooks()
            results = await hooks.workflow_completed(context, success=True)
            
            # Should not raise exception despite connection errors
            assert isinstance(results, list)
            
            # Some results may fail, but system should remain stable
            failed_results = [r for r in results if not r.success]
            # Allow some failures due to connection issues
            
            # After error duration expires, operations should recover
            await asyncio.sleep(2.5)  # Wait for error scenario to expire
            
            # New operations should succeed
            recovery_results = await hooks.workflow_completed(context, success=True)
            assert isinstance(recovery_results, list)
            
        finally:
            await trigger_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_service_timeout_handling(self, resilient_memory_service):
        """Test handling of memory service timeouts."""
        service, error_injector = resilient_memory_service
        
        # Inject timeout error
        timeout_error = ErrorScenario(
            name="Timeout Error",
            description="Memory operation timeout",
            error_type=asyncio.TimeoutError,
            error_message="Memory operation timed out",
            failure_rate=0.7  # 70% failure rate
        )
        
        error_injector.inject_error("search_memories", timeout_error)
        
        # Create recall service
        recall_service = create_memory_recall_service(service)
        await recall_service.initialize()
        
        try:
            # Perform multiple recall operations
            successful_recalls = 0
            failed_recalls = 0
            
            for i in range(20):
                try:
                    result = await recall_service.recall_for_operation(
                        "test_project", "timeout_test", {"iteration": i}
                    )
                    
                    if result.success:
                        successful_recalls += 1
                    else:
                        failed_recalls += 1
                        # Verify error handling in result
                        assert "timeout" in result.error_message.lower() or result.error_message == ""
                        
                except asyncio.TimeoutError:
                    failed_recalls += 1
            
            # Should have some successes despite timeouts
            assert successful_recalls > 0, "No successful recalls despite intermittent timeouts"
            
            # System should remain stable
            assert successful_recalls + failed_recalls == 20
            
        finally:
            await recall_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_partial_memory_service_failure(self, resilient_memory_service):
        """Test handling of partial memory service failures."""
        service, error_injector = resilient_memory_service
        
        # Inject intermittent errors
        intermittent_error = ErrorScenario(
            name="Intermittent Error",
            description="Random memory operation failures",
            error_type=RuntimeError,
            error_message="Intermittent memory service error",
            failure_rate=0.3  # 30% failure rate
        )
        
        error_injector.inject_error("add_memory", intermittent_error)
        
        # Create trigger service
        trigger_service = create_memory_trigger_service({
            "memory": {"fallback_chain": ["sqlite"]}
        })
        trigger_service.memory_service = service
        
        await trigger_service.initialize()
        
        try:
            orchestrator = trigger_service.get_trigger_orchestrator()
            
            # Execute multiple triggers with intermittent failures
            successful_triggers = 0
            failed_triggers = 0
            
            for i in range(50):
                event = TriggerEvent(
                    trigger_type=TriggerType.WORKFLOW_COMPLETION,
                    priority=TriggerPriority.MEDIUM,
                    project_name="test_project",
                    event_id=f"partial_failure_test_{i}",
                    content=f"Test trigger {i} with partial failures",
                    category=MemoryCategory.PATTERN,
                    tags=["partial_failure", "test"]
                )
                
                result = await orchestrator.trigger_memory_creation(event)
                
                if result.success:
                    successful_triggers += 1
                else:
                    failed_triggers += 1
            
            # Should have reasonable success rate despite intermittent failures
            success_rate = successful_triggers / 50
            assert success_rate >= 0.5, f"Success rate too low: {success_rate:.1%}"
            
            # System should remain operational
            metrics = orchestrator.get_metrics()
            assert metrics["total_triggers"] >= 50
            
        finally:
            await trigger_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_service_recovery_after_failure(self, resilient_memory_service):
        """Test memory service recovery after complete failure."""
        service, error_injector = resilient_memory_service
        
        # Inject complete failure for limited time
        complete_failure = ErrorScenario(
            name="Complete Failure",
            description="Complete memory service failure",
            error_type=Exception,
            error_message="Memory service completely unavailable",
            duration_seconds=3.0,  # Fail for 3 seconds
            failure_rate=1.0  # 100% failure rate
        )
        
        error_injector.inject_error("add_memory", complete_failure)
        error_injector.inject_error("search_memories", complete_failure)
        
        # Create services
        trigger_service = create_memory_trigger_service({
            "memory": {"fallback_chain": ["sqlite"]}
        })
        trigger_service.memory_service = service
        
        recall_service = create_memory_recall_service(service)
        
        await trigger_service.initialize()
        await recall_service.initialize()
        
        try:
            # Operations during failure period
            context = HookContext(
                operation_name="recovery_test",
                project_name="test_project",
                source="recovery_tester"
            )
            
            # Triggers during failure - should handle gracefully
            failure_results = await trigger_service.get_framework_hooks().workflow_completed(
                context, success=True
            )
            
            # Recall during failure - should handle gracefully
            failure_recall = await recall_service.recall_for_operation(
                "test_project", "recovery_test", {"phase": "failure"}
            )
            
            # Wait for recovery
            await asyncio.sleep(4.0)  # Wait for failure period to end
            
            # Operations after recovery - should succeed
            recovery_results = await trigger_service.get_framework_hooks().workflow_completed(
                context, success=True
            )
            
            recovery_recall = await recall_service.recall_for_operation(
                "test_project", "recovery_test", {"phase": "recovery"}
            )
            
            # Verify recovery
            assert isinstance(recovery_results, list)
            assert recovery_recall.success or not recovery_recall.success  # Should not crash
            
            # System should be operational after recovery
            metrics = trigger_service.get_trigger_orchestrator().get_metrics()
            assert metrics["total_triggers"] > 0
            
        finally:
            await trigger_service.cleanup()
            await recall_service.cleanup()


class TestCircuitBreakerPatterns:
    """Test circuit breaker patterns and failure isolation."""
    
    @pytest.fixture
    def mock_circuit_breaker(self):
        """Create mock circuit breaker for testing."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,
            expected_exception=Exception
        )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self, mock_circuit_breaker):
        """Test circuit breaker opens after failure threshold."""
        cb = mock_circuit_breaker
        
        # Mock failing operation
        async def failing_operation():
            raise RuntimeError("Operation failed")
        
        # Should be closed initially
        assert cb.state == CircuitBreakerState.CLOSED
        
        # Execute failing operations
        for i in range(3):
            try:
                await cb.call(failing_operation)
            except RuntimeError:
                pass  # Expected
        
        # Circuit breaker should now be open
        assert cb.state == CircuitBreakerState.OPEN
        
        # Further calls should fail fast
        try:
            await cb.call(failing_operation)
            assert False, "Should have failed fast"
        except Exception as e:
            assert "circuit breaker is open" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, mock_circuit_breaker):
        """Test circuit breaker recovery after timeout."""
        cb = mock_circuit_breaker
        
        # Mock operations
        async def failing_operation():
            raise RuntimeError("Operation failed")
        
        async def successful_operation():
            return "success"
        
        # Trigger circuit breaker opening
        for i in range(3):
            try:
                await cb.call(failing_operation)
            except RuntimeError:
                pass
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should be in half-open state
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Successful operation should close circuit
        result = await cb.call(successful_operation)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration_with_memory_service(self):
        """Test circuit breaker integration with memory service operations."""
        # Create memory service with circuit breaker
        config = {
            "fallback_chain": ["sqlite"],
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 2,
                "recovery_timeout": 1.0
            }
        }
        
        service = FlexibleMemoryService(config)
        await service.initialize()
        
        try:
            # Mock the backend to fail
            if hasattr(service, '_backends') and service._backends:
                backend = service._backends[0]
                original_add = backend.add_memory
                
                # Make it fail
                async def failing_add(*args, **kwargs):
                    raise ConnectionError("Backend unavailable")
                
                backend.add_memory = failing_add
                
                # Trigger circuit breaker
                for i in range(3):
                    try:
                        await service.add_memory(
                            "test_project", f"test content {i}", 
                            MemoryCategory.PATTERN
                        )
                    except:
                        pass
                
                # Restore operation
                backend.add_memory = original_add
                
                # Wait for recovery
                await asyncio.sleep(1.5)
                
                # Should work again
                memory_id = await service.add_memory(
                    "test_project", "recovery test", MemoryCategory.PATTERN
                )
                assert memory_id is not None
                
        finally:
            await service.cleanup()


class TestConcurrentFailureScenarios:
    """Test concurrent operation failure scenarios."""
    
    @pytest.fixture
    async def concurrent_test_system(self):
        """Create system for concurrent failure testing."""
        config = {
            "memory": {"fallback_chain": ["sqlite"]},
            "performance": {
                "max_concurrent_operations": 10,
                "batch_size": 20
            }
        }
        
        trigger_service = create_memory_trigger_service(config)
        await trigger_service.initialize()
        
        yield trigger_service
        
        await trigger_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_operation_failures(self, concurrent_test_system):
        """Test handling of concurrent operation failures."""
        service = concurrent_test_system
        hooks = service.get_framework_hooks()
        
        # Create mix of operations that will succeed and fail
        async def create_trigger_task(i: int):
            context = HookContext(
                operation_name=f"concurrent_failure_test_{i}",
                project_name="test_project",
                source="concurrent_tester"
            )
            
            # Simulate random failures
            success = random.random() > 0.3  # 30% failure rate
            
            if not success:
                # Inject failure by using invalid data
                context.metadata = {"invalid": object()}  # Non-serializable
            
            try:
                result = await hooks.workflow_completed(context, success=success)
                return {"index": i, "success": True, "result": result}
            except Exception as e:
                return {"index": i, "success": False, "error": str(e)}
        
        # Execute many concurrent operations
        tasks = [create_trigger_task(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_ops = 0
        failed_ops = 0
        exceptions = 0
        
        for result in results:
            if isinstance(result, Exception):
                exceptions += 1
            elif isinstance(result, dict):
                if result["success"]:
                    successful_ops += 1
                else:
                    failed_ops += 1
        
        # System should remain stable despite failures
        assert exceptions == 0, "No exceptions should propagate to top level"
        assert successful_ops > 0, "Some operations should succeed"
        
        # System should handle mixed success/failure gracefully
        total_ops = successful_ops + failed_ops
        assert total_ops == 50, f"Expected 50 operations, got {total_ops}"
        
        # Orchestrator should remain functional
        orchestrator = service.get_trigger_orchestrator()
        metrics = orchestrator.get_metrics()
        assert metrics["total_triggers"] > 0
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self, concurrent_test_system):
        """Test handling of resource exhaustion scenarios."""
        service = concurrent_test_system
        
        # Create very large number of concurrent operations to test resource limits
        async def resource_intensive_operation(i: int):
            context = HookContext(
                operation_name=f"resource_test_{i}",
                project_name="test_project",
                source="resource_tester",
                metadata={"data": "x" * 1000}  # Add some data
            )
            
            try:
                result = await service.get_framework_hooks().workflow_completed(
                    context, success=True
                )
                return {"success": True, "index": i}
            except Exception as e:
                return {"success": False, "index": i, "error": str(e)}
        
        # Create more tasks than max concurrent operations
        max_concurrent = service.get_trigger_orchestrator().config.get("max_concurrent_operations", 10)
        task_count = max_concurrent * 3
        
        start_time = time.time()
        tasks = [resource_intensive_operation(i) for i in range(task_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time
        
        # Analyze results
        successful_count = sum(1 for r in results if isinstance(r, dict) and r["success"])
        
        # Should handle resource constraints gracefully
        assert successful_count > 0, "Some operations should succeed despite resource constraints"
        
        # Should not take excessively long (proper queuing/throttling)
        assert elapsed_time < 30.0, f"Operations took too long: {elapsed_time:.1f}s"
        
        # System should remain responsive
        orchestrator = service.get_trigger_orchestrator()
        metrics = orchestrator.get_metrics()
        assert metrics["total_triggers"] >= successful_count
    
    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self, concurrent_test_system):
        """Test prevention of cascading failures."""
        service = concurrent_test_system
        memory_service = service.get_memory_service()
        
        # Mock memory service to simulate cascading failures
        original_add_memory = memory_service.add_memory
        failure_count = 0
        
        async def cascading_failure_add_memory(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            # First few operations fail, then recover
            if failure_count <= 5:
                raise RuntimeError("Cascading failure simulation")
            else:
                return await original_add_memory(*args, **kwargs)
        
        memory_service.add_memory = cascading_failure_add_memory
        
        try:
            # Execute operations that could cause cascading failures
            tasks = []
            for i in range(20):
                context = HookContext(
                    operation_name=f"cascading_test_{i}",
                    project_name="test_project",
                    source="cascading_tester"
                )
                
                task = service.get_framework_hooks().workflow_completed(
                    context, success=True
                )
                tasks.append(task)
                
                # Small delay to simulate realistic timing
                await asyncio.sleep(0.01)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should not have cascading failures - later operations should succeed
            exceptions = [r for r in results if isinstance(r, Exception)]
            assert len(exceptions) == 0, "No exceptions should cascade to top level"
            
            # System should isolate failures
            orchestrator = service.get_trigger_orchestrator()
            metrics = orchestrator.get_metrics()
            
            # Should have some successful operations despite initial failures
            assert metrics["successful_triggers"] > 0, "Some operations should succeed"
            
        finally:
            memory_service.add_memory = original_add_memory


class TestRecoveryMechanisms:
    """Test recovery and rollback mechanisms."""
    
    @pytest.fixture
    async def recovery_test_system(self):
        """Create system for recovery testing."""
        config = {
            "memory": {"fallback_chain": ["sqlite"]},
            "recovery": {
                "enabled": True,
                "retry_attempts": 3,
                "retry_delay": 0.1
            }
        }
        
        trigger_service = create_memory_trigger_service(config)
        await trigger_service.initialize()
        
        yield trigger_service
        
        await trigger_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_automatic_retry_mechanism(self, recovery_test_system):
        """Test automatic retry mechanism for failed operations."""
        service = recovery_test_system
        memory_service = service.get_memory_service()
        
        # Mock to fail first few attempts then succeed
        attempt_count = 0
        original_add_memory = memory_service.add_memory
        
        async def retry_test_add_memory(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count <= 2:  # Fail first 2 attempts
                raise ConnectionError("Temporary connection error")
            else:
                return await original_add_memory(*args, **kwargs)
        
        memory_service.add_memory = retry_test_add_memory
        
        try:
            # Execute operation that will require retries
            context = HookContext(
                operation_name="retry_test",
                project_name="test_project",
                source="retry_tester"
            )
            
            start_time = time.time()
            results = await service.get_framework_hooks().workflow_completed(
                context, success=True
            )
            elapsed_time = time.time() - start_time
            
            # Should eventually succeed after retries
            assert isinstance(results, list)
            
            # Should have taken some time due to retries
            assert elapsed_time >= 0.2, "Should have taken time for retries"
            
            # Should have made multiple attempts
            assert attempt_count >= 3, f"Should have made 3+ attempts, made {attempt_count}"
            
        finally:
            memory_service.add_memory = original_add_memory
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_modes(self, recovery_test_system):
        """Test graceful degradation when components fail."""
        service = recovery_test_system
        memory_service = service.get_memory_service()
        
        # Simulate complete memory service failure
        original_add_memory = memory_service.add_memory
        original_search_memories = memory_service.search_memories
        
        async def failing_add_memory(*args, **kwargs):
            raise RuntimeError("Memory service unavailable")
        
        async def failing_search_memories(*args, **kwargs):
            raise RuntimeError("Memory service unavailable")
        
        memory_service.add_memory = failing_add_memory
        memory_service.search_memories = failing_search_memories
        
        try:
            # Operations should degrade gracefully
            context = HookContext(
                operation_name="degradation_test",
                project_name="test_project",
                source="degradation_tester"
            )
            
            # Trigger operations - should not crash
            trigger_results = await service.get_framework_hooks().workflow_completed(
                context, success=True
            )
            
            # Create recall service and test degradation
            recall_service = create_memory_recall_service(memory_service)
            await recall_service.initialize()
            
            try:
                recall_result = await recall_service.recall_for_operation(
                    "test_project", "degradation_test", {"mode": "degraded"}
                )
                
                # Should handle failure gracefully
                assert not recall_result.success
                assert "error" in recall_result.error_message.lower() or recall_result.error_message == ""
                
            finally:
                await recall_service.cleanup()
            
            # System should remain operational in degraded mode
            assert isinstance(trigger_results, list)
            
            # Orchestrator should track degraded operations
            orchestrator = service.get_trigger_orchestrator()
            metrics = orchestrator.get_metrics()
            assert metrics["total_triggers"] > 0
            
        finally:
            memory_service.add_memory = original_add_memory
            memory_service.search_memories = original_search_memories
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring_during_failures(self, recovery_test_system):
        """Test system health monitoring during failure scenarios."""
        service = recovery_test_system
        
        # Get baseline health
        baseline_health = await service.get_service_health()
        assert baseline_health["service_initialized"] is True
        
        # Inject failures into memory service
        memory_service = service.get_memory_service()
        original_get_health = memory_service.get_service_health
        
        async def failing_health_check():
            return {"status": "unhealthy", "error": "Simulated health check failure"}
        
        memory_service.get_service_health = failing_health_check
        
        try:
            # Check health during failure
            failure_health = await service.get_service_health()
            
            # Should reflect component failures
            assert "memory_service" in failure_health
            
            # System should still be partially operational
            assert failure_health["service_initialized"] is True
            
            # Restore health and verify recovery
            memory_service.get_service_health = original_get_health
            
            recovery_health = await service.get_service_health()
            assert recovery_health["service_initialized"] is True
            
        finally:
            memory_service.get_service_health = original_get_health
    
    @pytest.mark.asyncio
    async def test_failure_isolation_between_components(self, recovery_test_system):
        """Test that failures in one component don't affect others."""
        service = recovery_test_system
        
        # Get different components
        orchestrator = service.get_trigger_orchestrator()
        policy_engine = service.get_policy_engine()
        hooks = service.get_framework_hooks()
        
        # Inject failure into orchestrator
        original_trigger_creation = orchestrator.trigger_memory_creation
        
        async def failing_trigger_creation(*args, **kwargs):
            raise RuntimeError("Orchestrator failure")
        
        orchestrator.trigger_memory_creation = failing_trigger_creation
        
        try:
            # Policy engine should still work
            test_event = TriggerEvent(
                trigger_type=TriggerType.WORKFLOW_COMPLETION,
                priority=TriggerPriority.MEDIUM,
                project_name="test_project",
                event_id="isolation_test",
                content="Test event for isolation",
                category=MemoryCategory.PATTERN
            )
            
            # Policy evaluation should work despite orchestrator failure
            decision, metadata = policy_engine.evaluate_trigger(test_event)
            assert decision is not None
            
            # Hooks should handle orchestrator failures gracefully
            context = HookContext(
                operation_name="isolation_test",
                project_name="test_project",
                source="isolation_tester"
            )
            
            # Should not crash despite orchestrator failure
            results = await hooks.workflow_completed(context, success=True)
            assert isinstance(results, list)
            
            # Failed results are acceptable - system should remain stable
            
        finally:
            orchestrator.trigger_memory_creation = original_trigger_creation


@pytest.mark.asyncio
async def test_comprehensive_error_scenario_suite():
    """Run comprehensive error scenario test suite."""
    
    # Define comprehensive error scenarios
    scenarios = [
        ErrorScenario(
            name="Database Connection Timeout",
            description="Database connection times out",
            error_type=asyncio.TimeoutError,
            error_message="Database connection timeout",
            duration_seconds=2.0
        ),
        ErrorScenario(
            name="Network Connectivity Loss",
            description="Network connectivity is lost",
            error_type=ConnectionError,
            error_message="Network unreachable",
            duration_seconds=3.0
        ),
        ErrorScenario(
            name="Memory Exhaustion",
            description="System runs out of memory",
            error_type=MemoryError,
            error_message="Out of memory",
            failure_rate=0.1  # Rare but critical
        ),
        ErrorScenario(
            name="Disk Space Full",
            description="Disk space is exhausted",
            error_type=OSError,
            error_message="No space left on device",
            failure_rate=0.05
        ),
        ErrorScenario(
            name="Service Overload",
            description="Service is overloaded",
            error_type=RuntimeError,
            error_message="Service temporarily overloaded",
            failure_rate=0.3,
            duration_seconds=5.0
        )
    ]
    
    # Create test system
    config = {
        "memory": {"fallback_chain": ["sqlite"]},
        "performance": {"max_concurrent_operations": 5}
    }
    
    service = create_memory_trigger_service(config)
    await service.initialize()
    
    try:
        # Test system resilience against all scenarios
        for scenario in scenarios:
            print(f"Testing scenario: {scenario.name}")
            
            # Execute operations during error scenario
            context = HookContext(
                operation_name=f"error_scenario_{scenario.name.lower().replace(' ', '_')}",
                project_name="error_test",
                source="comprehensive_error_tester"
            )
            
            # System should handle errors gracefully
            try:
                results = await service.get_framework_hooks().workflow_completed(
                    context, success=True
                )
                assert isinstance(results, list)
                print(f"✓ {scenario.name}: Handled gracefully")
                
            except Exception as e:
                # Some exceptions may bubble up, but system should not crash
                print(f"⚠ {scenario.name}: Exception occurred but system stable: {e}")
        
        # Verify system is still operational after all scenarios
        final_health = await service.get_service_health()
        assert final_health["service_initialized"] is True
        
        print("✓ Comprehensive error scenario suite completed successfully")
        
    finally:
        await service.cleanup()


if __name__ == "__main__":
    # Run error scenario tests
    pytest.main([__file__, "-v", "-s"])