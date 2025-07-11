"""
Tests for Memory Trigger Infrastructure

Unit tests for the memory trigger system components including
trigger orchestrator, policy engine, framework hooks, and decorators.
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
from unittest.mock import Mock, AsyncMock, patch

from claude_pm.services.memory import (
    MemoryTriggerService,
    MemoryTriggerOrchestrator,
    TriggerPolicyEngine,
    FrameworkMemoryHooks,
    TriggerType,
    TriggerPriority,
    TriggerEvent,
    TriggerResult,
    PolicyRule,
    PolicyConfig,
    PolicyDecision,
    HookContext,
    MemoryCategory,
    FlexibleMemoryService,
    create_memory_trigger_service,
    workflow_memory_trigger,
    agent_memory_trigger,
    issue_memory_trigger,
    error_memory_trigger,
    workflow_trigger_context,
    agent_trigger_context,
    set_global_hooks,
    get_global_hooks,
)


class TestTriggerOrchestrator:
    """Test cases for MemoryTriggerOrchestrator."""

    @pytest.fixture
    async def mock_memory_service(self):
        """Create a mock memory service."""
        service = Mock(spec=FlexibleMemoryService)
        service._initialized = True
        service.add_memory = AsyncMock(return_value="test-memory-id")
        service.get_active_backend_name = Mock(return_value="test-backend")
        return service

    @pytest.fixture
    async def orchestrator(self, mock_memory_service):
        """Create a trigger orchestrator for testing."""
        config = {"enabled": True, "max_queue_size": 10, "batch_size": 5, "timeout_seconds": 1}
        orchestrator = MemoryTriggerOrchestrator(mock_memory_service, config)
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.cleanup()

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mock_memory_service):
        """Test orchestrator initialization."""
        orchestrator = MemoryTriggerOrchestrator(mock_memory_service)

        assert not orchestrator._initialized
        assert orchestrator._enabled

        result = await orchestrator.initialize()
        assert result is True
        assert orchestrator._initialized

        await orchestrator.cleanup()

    @pytest.mark.asyncio
    async def test_trigger_memory_creation(self, orchestrator):
        """Test triggering memory creation."""
        event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Test workflow completed successfully",
            category=MemoryCategory.PATTERN,
            tags=["test", "workflow"],
            metadata={"success": True},
        )

        result = await orchestrator.trigger_memory_creation(event)

        assert isinstance(result, TriggerResult)
        assert result.success
        assert result.memory_id == "test-memory-id"
        assert result.backend_used == "test-backend"

    @pytest.mark.asyncio
    async def test_critical_trigger_immediate_processing(self, orchestrator):
        """Test that critical triggers are processed immediately."""
        event = TriggerEvent(
            trigger_type=TriggerType.ERROR_RESOLUTION,
            priority=TriggerPriority.CRITICAL,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Critical error resolved",
            category=MemoryCategory.ERROR,
            tags=["error", "critical"],
        )

        result = await orchestrator.trigger_memory_creation(event)

        assert result.success
        assert result.memory_id == "test-memory-id"
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, orchestrator):
        """Test that metrics are properly tracked."""
        event = TriggerEvent(
            trigger_type=TriggerType.AGENT_OPERATION,
            priority=TriggerPriority.MEDIUM,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Agent operation completed",
            category=MemoryCategory.PATTERN,
            tags=["agent"],
        )

        initial_metrics = orchestrator.get_metrics()
        initial_count = initial_metrics["total_triggers"]

        await orchestrator.trigger_memory_creation(event)

        final_metrics = orchestrator.get_metrics()
        assert final_metrics["total_triggers"] == initial_count + 1
        assert final_metrics["successful_triggers"] >= 1


class TestTriggerPolicyEngine:
    """Test cases for TriggerPolicyEngine."""

    @pytest.fixture
    def policy_engine(self):
        """Create a policy engine for testing."""
        return TriggerPolicyEngine()

    def test_policy_engine_initialization(self, policy_engine):
        """Test policy engine initialization."""
        assert len(policy_engine.policies) > 0
        assert TriggerType.WORKFLOW_COMPLETION in policy_engine.policies
        assert TriggerType.ERROR_RESOLUTION in policy_engine.policies

    def test_evaluate_trigger_allow(self, policy_engine):
        """Test trigger evaluation that should be allowed."""
        event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Test workflow completed",
            category=MemoryCategory.PATTERN,
            metadata={"success": True},
        )

        decision, metadata = policy_engine.evaluate_trigger(event)
        assert decision == PolicyDecision.ALLOW

    def test_evaluate_trigger_with_rule_match(self, policy_engine):
        """Test trigger evaluation with rule matching."""
        # Add a custom rule
        rule = PolicyRule(
            name="test_rule",
            condition="content:test",
            action=PolicyDecision.MODIFY,
            priority=100,
            metadata={"test": True},
        )

        policy_engine.add_policy_rule(TriggerType.WORKFLOW_COMPLETION, rule)

        event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Test workflow completed",
            category=MemoryCategory.PATTERN,
        )

        decision, metadata = policy_engine.evaluate_trigger(event)
        assert decision == PolicyDecision.MODIFY
        assert metadata.get("test") is True

    def test_policy_rule_matching(self, policy_engine):
        """Test policy rule condition matching."""
        rule = PolicyRule(
            name="project_rule",
            condition="project:test-*",
            action=PolicyDecision.ALLOW,
            priority=50,
        )

        event = TriggerEvent(
            trigger_type=TriggerType.WORKFLOW_COMPLETION,
            priority=TriggerPriority.HIGH,
            project_name="test-project",
            event_id=str(uuid.uuid4()),
            content="Test content",
            category=MemoryCategory.PATTERN,
        )

        assert rule.matches(event)

        # Test non-matching project
        event.project_name = "different-project"
        assert not rule.matches(event)

    def test_policy_validation(self, policy_engine):
        """Test policy configuration validation."""
        # Valid policy
        valid_policy = PolicyConfig(
            enabled=True,
            batch_settings={"batch_size": 10, "batch_timeout": 30},
            rate_limits={"per_hour": 100},
        )

        errors = policy_engine.validate_policy_config(valid_policy)
        assert len(errors) == 0

        # Invalid policy
        invalid_policy = PolicyConfig(
            enabled=True,
            batch_settings={"batch_size": 0, "batch_timeout": -1},
            rate_limits={"per_hour": -5},
        )

        errors = policy_engine.validate_policy_config(invalid_policy)
        assert len(errors) > 0


class TestFrameworkMemoryHooks:
    """Test cases for FrameworkMemoryHooks."""

    @pytest.fixture
    async def setup_hooks(self):
        """Setup framework hooks for testing."""
        # Mock dependencies
        memory_service = Mock(spec=FlexibleMemoryService)
        memory_service._initialized = True
        memory_service.add_memory = AsyncMock(return_value="test-memory-id")

        orchestrator = Mock(spec=MemoryTriggerOrchestrator)
        orchestrator.trigger_memory_creation = AsyncMock(
            return_value=TriggerResult(success=True, memory_id="test-memory-id")
        )

        policy_engine = Mock(spec=TriggerPolicyEngine)

        # Create hooks
        hooks = FrameworkMemoryHooks(
            memory_service=memory_service,
            trigger_orchestrator=orchestrator,
            policy_engine=policy_engine,
        )

        return hooks, orchestrator

    @pytest.mark.asyncio
    async def test_hook_execution(self, setup_hooks):
        """Test hook execution."""
        hooks, orchestrator = setup_hooks

        context = HookContext(
            operation_name="test_operation", project_name="test-project", source="test_source"
        )

        results = await hooks.execute_hook("workflow_complete", context, success=True)

        assert len(results) == 1
        assert results[0].success
        assert orchestrator.trigger_memory_creation.called

    @pytest.mark.asyncio
    async def test_hook_registration(self, setup_hooks):
        """Test hook registration."""
        hooks, _ = setup_hooks

        callback_called = False

        def test_callback(context, **kwargs):
            nonlocal callback_called
            callback_called = True

        hooks.register_hook("test_hook", test_callback)

        context = HookContext(
            operation_name="test_operation", project_name="test-project", source="test_source"
        )

        await hooks.execute_hook("test_hook", context)

        assert callback_called

    @pytest.mark.asyncio
    async def test_convenience_methods(self, setup_hooks):
        """Test convenience hook methods."""
        hooks, orchestrator = setup_hooks

        context = HookContext(
            operation_name="test_workflow", project_name="test-project", source="workflow_engine"
        )

        # Test workflow completion hook
        results = await hooks.workflow_completed(context, success=True)
        assert len(results) == 1
        assert results[0].success

        # Test agent operation hook
        results = await hooks.agent_operation_completed(context, agent_type="qa")
        assert len(results) == 1
        assert results[0].success

        # Test issue resolution hook
        results = await hooks.issue_resolved(context, issue_id="ISS-001")
        assert len(results) == 1
        assert results[0].success

    def test_hook_metrics(self, setup_hooks):
        """Test hook metrics collection."""
        hooks, _ = setup_hooks

        metrics = hooks.get_metrics()

        assert "hooks_executed" in metrics
        assert "successful_hooks" in metrics
        assert "failed_hooks" in metrics
        assert "memory_captures" in metrics
        assert "registered_hooks" in metrics


class TestMemoryTriggerDecorators:
    """Test cases for memory trigger decorators."""

    @pytest.fixture
    async def setup_decorators(self):
        """Setup decorators for testing."""
        # Create mock hooks
        hooks = Mock(spec=FrameworkMemoryHooks)
        hooks._enabled = True
        hooks.execute_hook = AsyncMock(
            return_value=[TriggerResult(success=True, memory_id="test-memory-id")]
        )

        # Set global hooks
        set_global_hooks(hooks)

        yield hooks

        # Clean up
        set_global_hooks(None)

    @pytest.mark.asyncio
    async def test_workflow_memory_trigger_decorator(self, setup_decorators):
        """Test workflow memory trigger decorator."""
        hooks = setup_decorators

        @workflow_memory_trigger(project_name="test-project", workflow_type="test")
        async def test_workflow():
            return {"status": "success"}

        result = await test_workflow()

        assert result["status"] == "success"
        assert hooks.execute_hook.called

    @pytest.mark.asyncio
    async def test_agent_memory_trigger_decorator(self, setup_decorators):
        """Test agent memory trigger decorator."""
        hooks = setup_decorators

        @agent_memory_trigger(agent_type="qa", project_name="test-project")
        async def test_agent_operation():
            return {"tests_passed": 10}

        result = await test_agent_operation()

        assert result["tests_passed"] == 10
        assert hooks.execute_hook.called

    @pytest.mark.asyncio
    async def test_issue_memory_trigger_decorator(self, setup_decorators):
        """Test issue memory trigger decorator."""
        hooks = setup_decorators

        @issue_memory_trigger(issue_id="ISS-001", project_name="test-project")
        async def test_issue_resolution():
            return {"issue_resolved": True}

        result = await test_issue_resolution()

        assert result["issue_resolved"] is True
        assert hooks.execute_hook.called

    @pytest.mark.asyncio
    async def test_error_memory_trigger_decorator(self, setup_decorators):
        """Test error memory trigger decorator."""
        hooks = setup_decorators

        @error_memory_trigger(error_type="test_error", project_name="test-project")
        async def test_error_handling():
            return {"error_handled": True}

        result = await test_error_handling()

        assert result["error_handled"] is True
        assert hooks.execute_hook.called

    @pytest.mark.asyncio
    async def test_decorator_error_handling(self, setup_decorators):
        """Test decorator behavior on function errors."""
        hooks = setup_decorators

        @workflow_memory_trigger(project_name="test-project", workflow_type="test")
        async def failing_workflow():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_workflow()

        # Hook should still be called for error case
        assert hooks.execute_hook.called

    @pytest.mark.asyncio
    async def test_workflow_trigger_context_manager(self, setup_decorators):
        """Test workflow trigger context manager."""
        hooks = setup_decorators

        async with workflow_trigger_context(
            operation_name="test_workflow", project_name="test-project", workflow_type="test"
        ) as ctx:
            ctx.add_metadata(step="processing")
            ctx.add_tags("test", "context")
            ctx.set_result({"status": "completed"})

        # Hook should be called twice (start and complete)
        assert hooks.execute_hook.call_count >= 1

    @pytest.mark.asyncio
    async def test_agent_trigger_context_manager(self, setup_decorators):
        """Test agent trigger context manager."""
        hooks = setup_decorators

        async with agent_trigger_context(
            operation_name="test_agent_op", project_name="test-project", agent_type="qa"
        ) as ctx:
            ctx.add_metadata(tests_run=25)
            ctx.add_tags("qa", "testing")
            ctx.set_result({"success_rate": 0.96})

        # Hook should be called
        assert hooks.execute_hook.called


class TestMemoryTriggerService:
    """Test cases for MemoryTriggerService."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        config = {
            "enabled": True,
            "memory": {"fallback_chain": ["sqlite"]},  # Use in-memory for testing
        }

        service = create_memory_trigger_service(config)

        assert not service._initialized
        assert service._enabled

        result = await service.initialize()
        assert result is True
        assert service._initialized

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_health_check(self):
        """Test service health check."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            health = await service.get_service_health()

            assert health["service_initialized"] is True
            assert health["service_enabled"] is True
            assert "memory_service" in health
            assert "trigger_orchestrator" in health
            assert "policy_engine" in health
            assert "framework_hooks" in health

    @pytest.mark.asyncio
    async def test_service_metrics(self):
        """Test service metrics collection."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            metrics = await service.get_service_metrics()

            assert "memory_service" in metrics
            assert "trigger_orchestrator" in metrics
            assert "policy_engine" in metrics
            assert "framework_hooks" in metrics

    @pytest.mark.asyncio
    async def test_service_components_access(self):
        """Test access to service components."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            assert service.get_memory_service() is not None
            assert service.get_trigger_orchestrator() is not None
            assert service.get_policy_engine() is not None
            assert service.get_framework_hooks() is not None


class TestIntegrationScenarios:
    """Integration test scenarios."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_trigger(self):
        """Test complete workflow trigger scenario."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            # Get hooks instance
            hooks = service.get_framework_hooks()

            # Create hook context
            context = HookContext(
                operation_name="test_workflow",
                project_name="test-project",
                source="workflow_engine",
                tags=["test", "integration"],
            )

            # Execute workflow completion hook
            results = await hooks.workflow_completed(
                context, success=True, workflow_type="test", results={"status": "completed"}
            )

            # Verify results
            assert len(results) >= 1
            # Note: Results may be empty if trigger was queued for background processing

    @pytest.mark.asyncio
    async def test_end_to_end_agent_trigger(self):
        """Test complete agent trigger scenario."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            # Get hooks instance
            hooks = service.get_framework_hooks()

            # Create hook context
            context = HookContext(
                operation_name="qa_validation",
                project_name="test-project",
                source="qa_agent",
                tags=["qa", "testing"],
            )

            # Execute agent operation hook
            results = await hooks.agent_operation_completed(
                context, agent_type="qa", tests_run=50, success_rate=0.98
            )

            # Verify results
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_error_handling_scenario(self):
        """Test error handling scenario."""
        config = {"enabled": True, "memory": {"fallback_chain": ["sqlite"]}}

        async with create_memory_trigger_service(config) as service:
            # Get hooks instance
            hooks = service.get_framework_hooks()

            # Create hook context
            context = HookContext(
                operation_name="error_recovery",
                project_name="test-project",
                source="error_handler",
                tags=["error", "recovery"],
            )

            # Execute error resolution hook
            results = await hooks.error_resolution(
                context,
                error_type="connection_timeout",
                error_message="Database connection timeout",
                solution="Implemented retry with exponential backoff",
            )

            # Verify results
            assert len(results) >= 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
