"""
Test Backwards Compatible Orchestrator
=====================================

Comprehensive tests for the BackwardsCompatibleOrchestrator to ensure
100% backwards compatibility and proper orchestration mode selection.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from claude_pm.orchestration import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    OrchestrationMetrics,
    create_backwards_compatible_orchestrator,
    delegate_with_compatibility
)
from claude_pm.utils.task_tool_helper import TaskToolConfiguration
from claude_pm.core.response_types import TaskToolResponse


class TestBackwardsCompatibleOrchestrator:
    """Test backwards compatible orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator instance for testing."""
        return BackwardsCompatibleOrchestrator(working_directory=tmp_path)
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment for testing."""
        with patch.dict(os.environ, {}, clear=True):
            yield
    
    @pytest.mark.asyncio
    async def test_initialization(self, tmp_path):
        """Test orchestrator initialization."""
        # Test default initialization
        orchestrator = BackwardsCompatibleOrchestrator()
        assert orchestrator.working_directory == Path.cwd()
        assert orchestrator.config is not None
        assert orchestrator.force_mode is None
        assert orchestrator.detector is not None
        
        # Test with custom directory
        orchestrator = BackwardsCompatibleOrchestrator(working_directory=tmp_path)
        assert orchestrator.working_directory == tmp_path
        
        # Test with custom config
        config = TaskToolConfiguration(timeout_seconds=600)
        orchestrator = BackwardsCompatibleOrchestrator(config=config)
        assert orchestrator.config.timeout_seconds == 600
        
        # Test with forced mode
        orchestrator = BackwardsCompatibleOrchestrator(force_mode=OrchestrationMode.LOCAL)
        assert orchestrator.force_mode == OrchestrationMode.LOCAL
    
    @pytest.mark.asyncio
    async def test_subprocess_fallback_when_disabled(self, orchestrator, mock_env):
        """Test fallback to subprocess when orchestration is disabled."""
        # Ensure CLAUDE_PM_ORCHESTRATION is not set
        assert "CLAUDE_PM_ORCHESTRATION" not in os.environ
        
        # Mock task tool helper
        mock_helper = AsyncMock()
        mock_helper.create_agent_subprocess = AsyncMock(return_value={
            "success": True,
            "subprocess_id": "test_123",
            "subprocess_info": {"agent_type": "test"},
            "prompt": "Test prompt"
        })
        
        with patch.object(orchestrator, '_task_tool_helper', mock_helper):
            result = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test task"
            )
        
        # Verify subprocess was called
        mock_helper.create_agent_subprocess.assert_called_once()
        assert result["success"] is True
        assert "orchestration_metadata" in result
        assert result["orchestration_metadata"]["mode"] == "subprocess"
        assert result["orchestration_metadata"]["metrics"]["fallback_reason"] == "CLAUDE_PM_ORCHESTRATION not enabled"
    
    @pytest.mark.asyncio
    async def test_local_orchestration_when_enabled(self, orchestrator, mock_env):
        """Test local orchestration when enabled."""
        # Enable orchestration
        os.environ["CLAUDE_PM_ORCHESTRATION"] = "true"
        
        # Force local mode to avoid component initialization issues in test
        orchestrator.force_mode = OrchestrationMode.LOCAL
        
        # Mock components
        mock_message_bus = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_agent_registry = AsyncMock()
        
        orchestrator._message_bus = mock_message_bus
        orchestrator._context_manager = mock_context_manager
        orchestrator._agent_registry = mock_agent_registry
        
        # Mock agent prompt
        with patch.object(orchestrator, '_get_agent_prompt', return_value="Test agent prompt"):
            # Mock context filtering
            mock_context_manager.get_filtered_context = AsyncMock(
                return_value={"filtered": "context"}
            )
            
            # Mock message routing
            from claude_pm.orchestration import Request, Response, MessageStatus
            mock_response = Response(
                request_id="test_req_123",
                status=MessageStatus.COMPLETED,
                data={"result": {"test": "result"}}
            )
            mock_message_bus.route_message = AsyncMock(return_value=mock_response)
            
            result = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test task",
                requirements=["Req 1", "Req 2"]
            )
        
        # Verify local orchestration was used
        assert result["success"] is True
        assert "local_orchestration" in result
        assert result["subprocess_info"]["orchestration_mode"] == "local"
        assert "orchestration_metadata" in result
        assert result["orchestration_metadata"]["mode"] == "local"
        
        # Verify components were called
        mock_context_manager.get_filtered_context.assert_called_once_with("test")
        mock_message_bus.route_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_api_compatibility(self, orchestrator):
        """Test that API maintains compatibility with TaskToolHelper."""
        # Force subprocess mode for predictable testing
        orchestrator.force_mode = OrchestrationMode.SUBPROCESS
        
        # Mock task tool helper
        mock_helper = AsyncMock()
        expected_result = {
            "success": True,
            "subprocess_id": "eng_20240715_120000",
            "subprocess_info": {
                "subprocess_id": "eng_20240715_120000",
                "agent_type": "engineer",
                "task_description": "Implement feature X",
                "generated_prompt": "Engineer prompt",
                "creation_time": "2024-07-15T12:00:00",
                "status": "created",
                "requirements": ["Req 1", "Req 2"],
                "deliverables": ["Del 1", "Del 2"],
                "priority": "high"
            },
            "prompt": "Engineer prompt",
            "usage_instructions": "Instructions..."
        }
        mock_helper.create_agent_subprocess = AsyncMock(return_value=expected_result)
        
        orchestrator._task_tool_helper = mock_helper
        
        # Call with all parameters
        result = await orchestrator.delegate_to_agent(
            agent_type="engineer",
            task_description="Implement feature X",
            requirements=["Req 1", "Req 2"],
            deliverables=["Del 1", "Del 2"],
            dependencies=["Dep 1"],
            priority="high",
            memory_categories=["architecture"],
            timeout_seconds=300,
            escalation_triggers=["Error", "Timeout"],
            integration_notes="Test notes",
            model_override="claude-3-opus",
            performance_requirements={"speed": "fast"}
        )
        
        # Verify all parameters were passed through
        call_args = mock_helper.create_agent_subprocess.call_args[1]
        assert call_args["agent_type"] == "engineer"
        assert call_args["task_description"] == "Implement feature X"
        assert call_args["requirements"] == ["Req 1", "Req 2"]
        assert call_args["deliverables"] == ["Del 1", "Del 2"]
        assert call_args["dependencies"] == ["Dep 1"]
        assert call_args["priority"] == "high"
        assert call_args["memory_categories"] == ["architecture"]
        assert call_args["timeout_seconds"] == 300
        assert call_args["escalation_triggers"] == ["Error", "Timeout"]
        assert call_args["integration_notes"] == "Test notes"
        assert call_args["model_override"] == "claude-3-opus"
        assert call_args["performance_requirements"] == {"speed": "fast"}
        
        # Verify result structure
        assert result["success"] is True
        assert result["subprocess_id"] == "eng_20240715_120000"
        assert "subprocess_info" in result
        assert "prompt" in result
        assert "usage_instructions" in result
    
    @pytest.mark.asyncio
    async def test_fallback_on_component_failure(self, orchestrator):
        """Test fallback to subprocess when component initialization fails."""
        # Enable orchestration
        with patch.dict(os.environ, {"CLAUDE_PM_ORCHESTRATION": "true"}):
            # Clear force mode to ensure we check components
            orchestrator.force_mode = None
            # Clear already initialized components to force re-initialization
            orchestrator._message_bus = None
            orchestrator._context_manager = None
            orchestrator._agent_registry = None
            
            # Make message bus initialization fail
            with patch('claude_pm.orchestration.backwards_compatible_orchestrator.SimpleMessageBus', side_effect=Exception("Component failure")):
                # Mock task tool helper for fallback
                mock_helper = AsyncMock()
                mock_helper.create_agent_subprocess = AsyncMock(return_value={
                    "success": True,
                    "subprocess_id": "test_123",
                    "subprocess_info": {},
                    "prompt": "Test"
                })
                orchestrator._task_tool_helper = mock_helper
                
                result = await orchestrator.delegate_to_agent(
                    agent_type="test",
                    task_description="Test task"
                )
            
            # Verify fallback occurred
            assert result["success"] is True
            assert result["orchestration_metadata"]["mode"] == "subprocess"
            # Just check that there's a fallback reason mentioning component
            fallback_reason = result["orchestration_metadata"]["metrics"]["fallback_reason"]
            assert fallback_reason is not None
            assert "Component" in fallback_reason or "component" in fallback_reason
    
    @pytest.mark.asyncio
    async def test_emergency_fallback(self, orchestrator):
        """Test emergency fallback mechanism."""
        # Make main delegation fail
        with patch.object(orchestrator, '_determine_orchestration_mode', side_effect=Exception("Critical error")):
            result = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test task"
            )
        
        # Should get TaskToolResponse or error dict
        if isinstance(result, TaskToolResponse):
            assert result.success is False
            assert "Critical error" in result.error
        else:
            assert "error" in result or "orchestration_error" in result
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, orchestrator):
        """Test orchestration metrics tracking."""
        # Force subprocess mode for testing
        orchestrator.force_mode = OrchestrationMode.SUBPROCESS
        
        # Mock task tool helper
        mock_helper = AsyncMock()
        mock_helper.create_agent_subprocess = AsyncMock(return_value={
            "success": True,
            "subprocess_id": "test_123",
            "subprocess_info": {},
            "prompt": "Test"
        })
        orchestrator._task_tool_helper = mock_helper
        
        # Execute multiple delegations
        for i in range(3):
            await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description=f"Test task {i}"
            )
        
        # Check metrics
        metrics = orchestrator.get_orchestration_metrics()
        assert metrics["total_orchestrations"] == 3
        assert metrics["subprocess_orchestrations"] == 3
        assert metrics["local_orchestrations"] == 0
        assert metrics["average_decision_time_ms"] > 0
        assert metrics["average_execution_time_ms"] > 0
        assert len(metrics["recent_metrics"]) == 3
    
    @pytest.mark.asyncio
    async def test_force_mode(self, orchestrator):
        """Test force mode functionality."""
        # Set force mode to local
        orchestrator.set_force_mode(OrchestrationMode.LOCAL)
        
        # Mock components for local execution
        with patch.object(orchestrator, '_execute_local_orchestration', 
                         return_value={"success": True, "mode": "local"}):
            result = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test"
            )
        
        assert result["mode"] == "local"
        
        # Change to subprocess
        orchestrator.set_force_mode(OrchestrationMode.SUBPROCESS)
        
        # Mock subprocess execution
        with patch.object(orchestrator, '_execute_subprocess_delegation',
                         return_value={"success": True, "mode": "subprocess"}):
            result = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test"
            )
        
        assert result["mode"] == "subprocess"
        
        # Clear force mode
        orchestrator.set_force_mode(None)
    
    @pytest.mark.asyncio
    async def test_validation(self, orchestrator):
        """Test compatibility validation."""
        # Mock a successful delegation
        with patch.object(orchestrator, 'delegate_to_agent', 
                         return_value={
                             "success": True,
                             "subprocess_id": "test_123",
                             "subprocess_info": {},
                             "prompt": "Test"
                         }):
            validation = await orchestrator.validate_compatibility()
        
        assert validation["compatible"] is True
        assert validation["checks"]["field_success"] is True
        assert validation["checks"]["field_subprocess_id"] is True
        assert validation["checks"]["field_subprocess_info"] is True
        assert validation["checks"]["field_prompt"] is True
        assert validation["checks"]["detector_available"] is True
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self, tmp_path):
        """Test convenience functions."""
        # Test create function
        orchestrator = await create_backwards_compatible_orchestrator(
            working_directory=tmp_path
        )
        assert isinstance(orchestrator, BackwardsCompatibleOrchestrator)
        assert orchestrator.working_directory == tmp_path
        
        # Test delegate function
        with patch('claude_pm.orchestration.backwards_compatible_orchestrator.BackwardsCompatibleOrchestrator') as mock_class:
            mock_instance = AsyncMock()
            mock_instance.delegate_to_agent = AsyncMock(
                return_value={"success": True}
            )
            mock_class.return_value = mock_instance
            
            result = await delegate_with_compatibility(
                agent_type="test",
                task_description="Test task"
            )
            
            assert result["success"] is True
            mock_instance.delegate_to_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prompt_formatting(self, orchestrator):
        """Test agent prompt formatting."""
        base_prompt = "This is the base agent prompt"
        
        formatted = orchestrator._format_agent_prompt(
            agent_type="engineer",
            task_description="Build feature X",
            base_prompt=base_prompt,
            requirements=["Use TypeScript", "Add tests"],
            deliverables=["Feature code", "Unit tests"],
            priority="high",
            integration_notes="Integrate with existing API"
        )
        
        assert "**Engineer Agent**:" in formatted
        assert "Build feature X" in formatted
        assert "TEMPORAL CONTEXT: Today is" in formatted
        assert "Use TypeScript" in formatted
        assert "Add tests" in formatted
        assert "Feature code" in formatted
        assert "Unit tests" in formatted
        assert "Priority: high" in formatted
        assert "Integrate with existing API" in formatted
        assert base_prompt in formatted
    
    @pytest.mark.asyncio
    async def test_local_usage_instructions(self, orchestrator):
        """Test local orchestration usage instructions generation."""
        from claude_pm.orchestration import Response, MessageStatus
        
        response = Response(
            request_id="test_123",
            status=MessageStatus.COMPLETED,
            data={"result": {"test": "result"}}
        )
        
        instructions = orchestrator._generate_local_usage_instructions(
            subprocess_id="eng_123",
            agent_type="engineer",
            response=response
        )
        
        assert "Local Orchestration Execution Instructions" in instructions
        assert "eng_123" in instructions
        assert "engineer" in instructions
        assert "LOCAL" in instructions
        assert "COMPLETED" in instructions
        assert "Success" in instructions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])