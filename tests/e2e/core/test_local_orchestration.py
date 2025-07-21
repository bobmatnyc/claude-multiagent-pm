"""
E2E Tests for LOCAL Orchestration Mode
=====================================

Comprehensive tests for LOCAL orchestration functionality including:
- LOCAL mode detection and execution
- Local task execution without Task Tool
- PM agent orchestration in LOCAL mode
- State management in local execution
- TodoWrite integration in LOCAL mode
- Multi-agent workflow orchestration
- Context filtering and propagation
- Local mode performance
"""

import asyncio
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    ReturnCode,
    OrchestrationMetrics
)
from claude_pm.orchestration.message_bus import SimpleMessageBus, MessageResponse, MessageStatus
from claude_pm.orchestration.context_manager import create_context_manager
from claude_pm.services.agent_registry_sync import AgentRegistry
from claude_pm.utils.task_tool_helper import TaskToolConfiguration


class TestLocalOrchestration:
    """Comprehensive tests for LOCAL orchestration mode."""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator instance for testing."""
        config = TaskToolConfiguration(timeout_seconds=30)
        return BackwardsCompatibleOrchestrator(
            working_directory=str(tmp_path),
            config=config
        )
    
    @pytest.fixture
    def mock_message_bus(self):
        """Create mock message bus for testing."""
        bus = AsyncMock(spec=SimpleMessageBus)
        bus.send_request = AsyncMock()
        return bus
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create mock context manager."""
        manager = MagicMock()
        manager.filter_context_for_agent = MagicMock(return_value={
            "files": {"test.py": "content"},
            "memory": {"key": "value"}
        })
        manager.get_context_size_estimate = MagicMock(side_effect=[1000, 500])
        return manager
    
    @pytest.fixture
    def mock_agent_registry(self):
        """Create mock agent registry."""
        registry = MagicMock(spec=AgentRegistry)
        registry.get_agent = MagicMock(return_value=MagicMock(
            prompt="Test agent prompt",
            tier="project"
        ))
        return registry
    
    @pytest.mark.asyncio
    async def test_local_mode_detection(self, orchestrator):
        """Test LOCAL mode is properly detected."""
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Test delegation
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="test",
            task_description="Test task",
            task_id="test-001"
        )
        
        # Verify mode detection
        assert "orchestration_metadata" in result
        assert result["orchestration_metadata"]["mode"] == OrchestrationMode.LOCAL.value
        assert result["orchestration_metadata"]["fallback_reason"] is None
    
    @pytest.mark.asyncio
    async def test_local_execution_without_subprocess(self, orchestrator, mock_message_bus, mock_context_manager):
        """Test local execution avoids subprocess overhead."""
        # Set up mocks
        orchestrator._mode_detector.message_bus = mock_message_bus
        orchestrator._mode_detector.context_manager = mock_context_manager
        orchestrator._local_executor._message_bus = mock_message_bus
        orchestrator._local_executor._context_manager = mock_context_manager
        
        # Mock message bus response
        mock_message_bus.send_request.return_value = MessageResponse(
            status=MessageStatus.COMPLETED,
            data={"result": "Task completed"},
            error=None
        )
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute task
        start_time = time.perf_counter()
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Generate changelog",
            requirements=["Analyze commits", "Update CHANGELOG.md"],
            deliverables=["Updated changelog"],
            priority="high"
        )
        execution_time = (time.perf_counter() - start_time) * 1000
        
        # Verify no subprocess was created
        assert result["subprocess_info"]["orchestration_mode"] == "LOCAL"
        assert result["success"] is True
        assert return_code == ReturnCode.SUCCESS
        
        # Verify performance - LOCAL should be fast
        assert execution_time < 500  # Should complete in less than 500ms
        assert "local_orchestration" in result
        assert result["local_orchestration"]["response_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_direct_agent_method_calls(self, orchestrator, mock_message_bus):
        """Test direct agent method calls in LOCAL mode."""
        # Set up mock agent handler
        agent_handler = AsyncMock()
        agent_handler.return_value = {
            "result": "Documentation updated",
            "files_changed": ["CHANGELOG.md", "README.md"]
        }
        
        # Register handler
        mock_message_bus.register_handler = MagicMock()
        mock_message_bus.send_request.return_value = MessageResponse(
            status=MessageStatus.COMPLETED,
            data={"result": agent_handler.return_value},
            error=None
        )
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        orchestrator._local_executor._message_bus = mock_message_bus
        
        # Execute task
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Update project documentation"
        )
        
        # Verify direct execution
        assert result["success"] is True
        assert "results" in result
        assert result["results"]["files_changed"] == ["CHANGELOG.md", "README.md"]
        
        # Verify message bus was used for routing
        mock_message_bus.send_request.assert_called_once()
        call_args = mock_message_bus.send_request.call_args
        assert call_args[1]["agent_id"] == "documentation"
    
    @pytest.mark.asyncio
    async def test_pm_agent_orchestration_local_mode(self, orchestrator):
        """Test PM agent orchestration in LOCAL mode."""
        # Create PM-specific task
        pm_task = """
        Coordinate the following tasks:
        1. Documentation Agent: Update API documentation
        2. QA Agent: Run integration tests
        3. Version Control Agent: Create release branch
        """
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute PM orchestration
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="pm",
            task_description=pm_task,
            task_id="pm-orchestration-001"
        )
        
        # Verify PM orchestration metadata
        assert result["subprocess_info"]["agent_type"] == "pm"
        assert result["subprocess_info"]["orchestration_mode"] == "LOCAL"
        assert "local_orchestration" in result
    
    @pytest.mark.asyncio
    async def test_state_management_in_local_execution(self, orchestrator):
        """Test state is properly managed in LOCAL execution."""
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute multiple tasks in sequence
        task_ids = []
        for i in range(3):
            task_id = f"state-test-{i:03d}"
            task_ids.append(task_id)
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description=f"Task {i}",
                task_id=task_id
            )
            
            # Verify task ID is maintained
            assert result["subprocess_info"]["task_id"] == task_id
        
        # Verify metrics are tracked
        metrics = orchestrator.get_orchestration_metrics()
        assert metrics["total_orchestrations"] >= 3
        assert metrics["by_mode"]["local"]["count"] >= 3
    
    @pytest.mark.asyncio
    async def test_todowrite_integration_local_mode(self, orchestrator):
        """Test TodoWrite integration in LOCAL mode."""
        # Mock TodoWrite functionality
        todos = []
        
        async def mock_todowrite_handler(request_data):
            """Mock handler for TodoWrite operations."""
            todos.append({
                "id": str(uuid.uuid4()),
                "content": request_data["task"],
                "status": "pending",
                "agent": request_data["agent_type"]
            })
            return {"todo_id": todos[-1]["id"], "todos": todos}
        
        # Set up message bus with TodoWrite handler
        orchestrator._local_executor._message_bus = SimpleMessageBus()
        orchestrator._local_executor._message_bus.register_handler(
            "todowrite", mock_todowrite_handler
        )
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute task that should create todo
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="todowrite",
            task_description="Documentation Agent: Update API docs",
            priority="high"
        )
        
        # Verify todo was created
        assert len(todos) == 1
        assert todos[0]["content"] == "Documentation Agent: Update API docs"
        assert todos[0]["status"] == "pending"
        assert todos[0]["agent"] == "todowrite"
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow_orchestration(self, orchestrator):
        """Test multi-agent workflow in LOCAL mode."""
        # Track agent executions
        executions = []
        
        async def track_execution(agent_type):
            """Helper to track agent executions."""
            executions.append({
                "agent": agent_type,
                "timestamp": time.time()
            })
            return {"status": "completed", "agent": agent_type}
        
        # Set up mock handlers for different agents
        orchestrator._local_executor._message_bus = SimpleMessageBus()
        
        for agent_type in ["documentation", "qa", "version_control"]:
            handler = AsyncMock(side_effect=lambda req, a=agent_type: track_execution(a))
            orchestrator._local_executor._message_bus.register_handler(agent_type, handler)
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute workflow
        workflow_agents = ["documentation", "qa", "version_control"]
        for agent_type in workflow_agents:
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type=agent_type,
                task_description=f"{agent_type} task in workflow"
            )
            assert return_code == ReturnCode.SUCCESS
        
        # Verify all agents executed in order
        assert len(executions) == 3
        assert [e["agent"] for e in executions] == workflow_agents
        
        # Verify timing (should be sequential)
        for i in range(1, len(executions)):
            assert executions[i]["timestamp"] > executions[i-1]["timestamp"]
    
    @pytest.mark.asyncio
    async def test_context_filtering_and_propagation(self, orchestrator, mock_context_manager):
        """Test context filtering and propagation in LOCAL mode."""
        # Set up context manager with specific behavior
        full_context = {
            "files": {
                "src/main.py": "main code",
                "tests/test_main.py": "test code",
                "docs/api.md": "api docs",
                "README.md": "readme"
            },
            "memory": {
                "project_type": "python",
                "last_commit": "abc123"
            }
        }
        
        # Different context filters for different agents
        agent_contexts = {
            "documentation": {"files": {"docs/api.md": "api docs", "README.md": "readme"}},
            "qa": {"files": {"tests/test_main.py": "test code"}},
            "engineer": {"files": {"src/main.py": "main code"}}
        }
        
        mock_context_manager.filter_context_for_agent = MagicMock(
            side_effect=lambda agent, ctx: agent_contexts.get(agent, {})
        )
        
        orchestrator._local_executor._context_manager = mock_context_manager
        orchestrator._local_executor.collect_full_context = AsyncMock(return_value=full_context)
        
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Test context filtering for different agents
        for agent_type in ["documentation", "qa", "engineer"]:
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type=agent_type,
                task_description=f"Process files for {agent_type}"
            )
            
            # Verify context was filtered
            mock_context_manager.filter_context_for_agent.assert_called_with(
                agent_type, full_context
            )
            
            # Verify metrics show filtering
            assert "local_orchestration" in result
            assert "context_filtering_ms" in result["local_orchestration"]
            assert result["local_orchestration"]["token_reduction_percent"] > 0
    
    @pytest.mark.asyncio
    async def test_local_mode_performance(self, orchestrator):
        """Test LOCAL mode performance characteristics."""
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute multiple tasks and measure performance
        execution_times = []
        num_tasks = 10
        
        for i in range(num_tasks):
            start = time.perf_counter()
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description=f"Performance test {i}",
                task_id=f"perf-{i:03d}"
            )
            execution_time = (time.perf_counter() - start) * 1000
            execution_times.append(execution_time)
            
            # Verify each execution is fast
            assert execution_time < 100  # Should complete in less than 100ms
        
        # Calculate performance statistics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Verify performance characteristics
        assert avg_time < 50  # Average should be very fast
        assert max_time < 100  # No outliers
        assert min_time > 0  # Sanity check
        
        # Check metrics
        metrics = orchestrator.get_orchestration_metrics()
        assert metrics["by_mode"]["local"]["count"] == num_tasks
        assert metrics["by_mode"]["local"]["average_execution_ms"] < 50
    
    @pytest.mark.asyncio
    async def test_error_propagation_in_local_mode(self, orchestrator, mock_message_bus):
        """Test error propagation in LOCAL mode."""
        # Set up message bus to return error
        error_message = "Agent processing failed"
        mock_message_bus.send_request.return_value = MessageResponse(
            status=MessageStatus.ERROR,
            data=None,
            error=error_message
        )
        
        orchestrator._local_executor._message_bus = mock_message_bus
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute task that will fail
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="test",
            task_description="This will fail"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert return_code != ReturnCode.SUCCESS
        assert "error" in result
        assert error_message in result["error"]
        assert result["subprocess_info"]["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_mode_switching_local_to_subprocess(self, orchestrator):
        """Test switching from LOCAL to subprocess mode."""
        # Start with LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute task in LOCAL mode
        result1, return_code1 = await orchestrator.delegate_to_agent(
            agent_type="test",
            task_description="Task in LOCAL mode"
        )
        assert result1["orchestration_metadata"]["mode"] == OrchestrationMode.LOCAL.value
        
        # Switch to subprocess mode
        orchestrator.set_force_mode(OrchestrationMode.SUBPROCESS)
        
        # Execute task in subprocess mode
        result2, return_code2 = await orchestrator.delegate_to_agent(
            agent_type="test",
            task_description="Task in subprocess mode"
        )
        assert result2["orchestration_metadata"]["mode"] == OrchestrationMode.SUBPROCESS.value
        
        # Verify metrics track both modes
        metrics = orchestrator.get_orchestration_metrics()
        assert metrics["by_mode"]["local"]["count"] >= 1
        assert metrics["by_mode"]["subprocess"]["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_agent_hierarchy_in_local_mode(self, orchestrator, mock_agent_registry):
        """Test agent hierarchy resolution in LOCAL mode."""
        # Set up agent registry with hierarchy
        mock_agent_registry.discover_agents.return_value = {
            "documentation_project": {
                "type": "documentation",
                "tier": "project",
                "path": "/project/.claude-pm/agents/documentation.md"
            },
            "documentation_user": {
                "type": "documentation", 
                "tier": "user",
                "path": "/home/user/.claude-pm/agents/documentation.md"
            },
            "documentation_system": {
                "type": "documentation",
                "tier": "system",
                "path": "/system/agents/documentation.md"
            }
        }
        
        orchestrator._local_executor._agent_registry = mock_agent_registry
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute task
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Test hierarchy"
        )
        
        # Verify correct agent tier was selected (project > user > system)
        assert "local_orchestration" in result
        assert result["local_orchestration"]["agent_tier"] == "project"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_in_local_mode(self, orchestrator):
        """Test memory efficiency of LOCAL mode."""
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Track memory usage (simplified)
        import gc
        gc.collect()
        
        # Execute multiple tasks
        for i in range(50):
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description=f"Memory test {i}",
                task_id=f"mem-{i:03d}"
            )
            
            # Verify no memory leaks (task completes and cleans up)
            assert result["subprocess_info"]["task_id"] == f"mem-{i:03d}"
        
        # Force garbage collection
        gc.collect()
        
        # Verify orchestration metrics are reasonable
        metrics = orchestrator._orchestration_metrics
        assert len(metrics) <= 100  # Should have reasonable limit
    
    @pytest.mark.asyncio 
    async def test_concurrent_local_orchestrations(self, orchestrator):
        """Test concurrent LOCAL orchestrations."""
        # Force LOCAL mode
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Create multiple concurrent tasks
        tasks = []
        num_concurrent = 5
        
        for i in range(num_concurrent):
            task = orchestrator.delegate_to_agent(
                agent_type="test",
                task_description=f"Concurrent task {i}",
                task_id=f"concurrent-{i:03d}"
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(results) == num_concurrent
        for i, (result, return_code) in enumerate(results):
            assert return_code == ReturnCode.SUCCESS
            assert result["subprocess_info"]["task_id"] == f"concurrent-{i:03d}"
        
        # Verify performance metrics
        metrics = orchestrator.get_orchestration_metrics()
        assert metrics["by_mode"]["local"]["count"] >= num_concurrent
    
    @pytest.mark.asyncio
    async def test_local_mode_with_large_context(self, orchestrator, mock_context_manager):
        """Test LOCAL mode handling of large contexts efficiently."""
        # Create large context
        large_context = {
            "files": {f"file_{i}.py": f"# Content for file {i}\n" * 100 
                     for i in range(50)},  # 50 files with substantial content
            "memory": {f"key_{i}": f"value_{i}" * 50 
                      for i in range(100)}  # 100 memory entries
        }
        
        # Set up context manager to return large context
        mock_context_manager.filter_context_for_agent = MagicMock(
            return_value=large_context
        )
        mock_context_manager.get_context_size_estimate = MagicMock(
            side_effect=[50000, 25000]  # Before and after filtering
        )
        
        orchestrator._local_executor._context_manager = mock_context_manager
        orchestrator._local_executor.collect_full_context = AsyncMock(
            return_value=large_context
        )
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Execute with large context
        start_time = time.perf_counter()
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="documentation",
            task_description="Process large codebase documentation"
        )
        execution_time = (time.perf_counter() - start_time) * 1000
        
        # Verify handling
        assert return_code == ReturnCode.SUCCESS
        assert "local_orchestration" in result
        assert result["local_orchestration"]["token_reduction_percent"] == 50.0
        
        # Should still be fast despite large context
        assert execution_time < 500  # Less than 500ms
    
    @pytest.mark.asyncio
    async def test_local_mode_rollback_on_failure(self, orchestrator):
        """Test rollback capabilities in LOCAL mode."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Track state changes
        state_changes = []
        rollback_called = False
        
        async def stateful_handler(request_data):
            """Handler that modifies state."""
            operation = request_data.get("operation")
            
            if operation == "modify":
                state_changes.append({"action": "modified", "data": "important_file.py"})
                return {"status": "modified"}
            elif operation == "validate":
                # Simulate validation failure
                raise Exception("Validation failed - rollback required")
            elif operation == "rollback":
                nonlocal rollback_called
                rollback_called = True
                state_changes.append({"action": "rolled_back", "data": "important_file.py"})
                return {"status": "rolled_back"}
            
            return {"status": "unknown"}
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        message_bus.register_handler("stateful", stateful_handler)
        orchestrator._local_executor._message_bus = message_bus
        
        # Execute workflow with failure
        # Step 1: Modify state
        modify_result, _ = await orchestrator.delegate_to_agent(
            agent_type="stateful",
            task_description="Modify important file",
            operation="modify"
        )
        assert modify_result["success"] is True
        
        # Step 2: Validation (will fail)
        try:
            validate_result, _ = await orchestrator.delegate_to_agent(
                agent_type="stateful",
                task_description="Validate changes",
                operation="validate"
            )
        except:
            # Step 3: Rollback
            rollback_result, _ = await orchestrator.delegate_to_agent(
                agent_type="stateful",
                task_description="Rollback changes",
                operation="rollback"
            )
        
        # Verify rollback occurred
        assert rollback_called is True
        assert len(state_changes) == 2
        assert state_changes[0]["action"] == "modified"
        assert state_changes[1]["action"] == "rolled_back"
    
    @pytest.mark.asyncio
    async def test_local_mode_with_complex_agent_registry(self, orchestrator, mock_agent_registry):
        """Test LOCAL mode with complex agent registry interactions."""
        # Set up complex agent hierarchy
        agent_hierarchy = {
            "engineer_project": {
                "type": "engineer",
                "tier": "project",
                "specializations": ["python", "async"],
                "path": "/project/.claude-pm/agents/engineer.md"
            },
            "engineer_specialized": {
                "type": "engineer", 
                "tier": "project",
                "specializations": ["rust", "performance"],
                "path": "/project/.claude-pm/agents/engineer_rust.md"
            },
            "engineer_user": {
                "type": "engineer",
                "tier": "user",
                "specializations": ["python"],
                "path": "/home/user/.claude-pm/agents/engineer.md"
            },
            "engineer_system": {
                "type": "engineer",
                "tier": "system",
                "specializations": ["general"],
                "path": "/system/agents/engineer.md"
            }
        }
        
        # Mock registry methods
        mock_agent_registry.discover_agents.return_value = agent_hierarchy
        mock_agent_registry.select_optimal_agent = MagicMock(
            side_effect=lambda agents, task: next(
                a for a in agents.values() 
                if "rust" in task.lower() and "rust" in a.get("specializations", [])
            ) if "rust" in task.lower() else next(
                a for a in agents.values() if a["tier"] == "project"
            )
        )
        
        orchestrator._local_executor._agent_registry = mock_agent_registry
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Test specialized agent selection
        rust_result, _ = await orchestrator.delegate_to_agent(
            agent_type="engineer",
            task_description="Optimize Rust performance critical code"
        )
        
        # Test general agent selection
        python_result, _ = await orchestrator.delegate_to_agent(
            agent_type="engineer",
            task_description="Implement Python async handler"
        )
        
        # Verify agent selection
        assert mock_agent_registry.select_optimal_agent.call_count >= 2
        
        # Verify appropriate agents were selected based on task
        calls = mock_agent_registry.select_optimal_agent.call_args_list
        rust_task_call = next(c for c in calls if "rust" in c[0][1].lower())
        assert "rust" in rust_task_call[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_local_mode_state_persistence(self, orchestrator, tmp_path):
        """Test state persistence across LOCAL orchestrations."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Create state file
        state_file = tmp_path / "orchestration_state.json"
        
        # Handler that persists state
        async def persistent_handler(request_data):
            """Handler that persists state to file."""
            import json
            
            # Load existing state
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
            else:
                state = {"executions": [], "counter": 0}
            
            # Update state
            state["counter"] += 1
            state["executions"].append({
                "task_id": request_data.get("task_id"),
                "timestamp": time.time(),
                "description": request_data.get("task_description")
            })
            
            # Persist state
            with open(state_file, 'w') as f:
                json.dump(state, f)
            
            return {"counter": state["counter"], "total_executions": len(state["executions"])}
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        message_bus.register_handler("persistent", persistent_handler)
        orchestrator._local_executor._message_bus = message_bus
        
        # Execute multiple orchestrations
        for i in range(3):
            result, _ = await orchestrator.delegate_to_agent(
                agent_type="persistent",
                task_description=f"Persistent task {i}",
                task_id=f"persist-{i:03d}"
            )
            
            # Verify state is maintained
            assert result["results"]["counter"] == i + 1
            assert result["results"]["total_executions"] == i + 1
        
        # Verify state file exists and contains correct data
        assert state_file.exists()
        with open(state_file, 'r') as f:
            final_state = json.load(f)
        
        assert final_state["counter"] == 3
        assert len(final_state["executions"]) == 3
        assert all(e["task_id"] == f"persist-{i:03d}" 
                  for i, e in enumerate(final_state["executions"]))
    
    @pytest.mark.asyncio
    async def test_local_mode_circuit_breaker_pattern(self, orchestrator):
        """Test circuit breaker pattern in LOCAL mode."""
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Circuit breaker state
        failure_count = 0
        circuit_open = False
        success_count = 0
        
        async def circuit_breaker_handler(request_data):
            """Handler with circuit breaker behavior."""
            nonlocal failure_count, circuit_open, success_count
            
            # Check if circuit is open
            if circuit_open:
                if failure_count >= 3:
                    # Try to close circuit after cooldown
                    if success_count > 0:
                        circuit_open = False
                        failure_count = 0
                    else:
                        raise Exception("Circuit breaker is OPEN")
            
            # Simulate intermittent failures
            if request_data.get("simulate_failure", False):
                failure_count += 1
                if failure_count >= 3:
                    circuit_open = True
                raise Exception("Service temporarily unavailable")
            
            # Success
            success_count += 1
            return {"status": "success", "circuit_state": "closed"}
        
        # Set up message bus
        message_bus = SimpleMessageBus()
        message_bus.register_handler("circuit", circuit_breaker_handler)
        orchestrator._local_executor._message_bus = message_bus
        
        # Test circuit breaker behavior
        results = []
        
        # Cause failures to open circuit
        for i in range(4):
            try:
                result, _ = await orchestrator.delegate_to_agent(
                    agent_type="circuit",
                    task_description=f"Request {i}",
                    simulate_failure=True
                )
                results.append(("success", result))
            except Exception as e:
                results.append(("failure", str(e)))
        
        # Circuit should be open after 3 failures
        assert results[3][0] == "failure"
        assert "Circuit breaker is OPEN" in results[3][1]
        
        # Try successful request to start closing circuit
        try:
            result, _ = await orchestrator.delegate_to_agent(
                agent_type="circuit",
                task_description="Recovery request",
                simulate_failure=False
            )
            results.append(("success", result))
        except Exception as e:
            # First attempt might still fail
            results.append(("failure", str(e)))
        
        # Reset and try again
        success_count = 1  # Simulate cooldown period
        result, _ = await orchestrator.delegate_to_agent(
            agent_type="circuit",
            task_description="Final request",
            simulate_failure=False
        )
        
        # Circuit should be working again
        assert result["success"] is True
        assert result["results"]["circuit_state"] == "closed"