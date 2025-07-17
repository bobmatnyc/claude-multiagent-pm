"""Test return codes from orchestration methods."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode,
    ReturnCode,
    delegate_with_compatibility
)
from claude_pm.orchestration.message_bus import Response, MessageStatus


@pytest.fixture
def orchestrator():
    """Create a test orchestrator."""
    return BackwardsCompatibleOrchestrator()


@pytest.mark.asyncio
async def test_successful_delegation_returns_success_code(orchestrator):
    """Test that successful delegation returns SUCCESS code."""
    # Mock the subprocess delegation to return success
    with patch.object(orchestrator, '_execute_subprocess_delegation') as mock_subprocess:
        mock_subprocess.return_value = (
            {
                "success": True,
                "subprocess_id": "test_123",
                "subprocess_info": {},
                "prompt": "test prompt"
            },
            ReturnCode.SUCCESS
        )
        
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type="test",
            task_description="Test successful operation"
        )
        
        assert return_code == ReturnCode.SUCCESS
        assert result["success"] is True


@pytest.mark.asyncio
async def test_agent_not_found_returns_correct_code(orchestrator):
    """Test that agent not found returns AGENT_NOT_FOUND code."""
    # Force local mode to test agent not found scenario
    orchestrator.set_force_mode(OrchestrationMode.LOCAL)
    
    # Mock components
    orchestrator._message_bus = Mock()
    orchestrator._context_manager = Mock()
    orchestrator._agent_registry = Mock()
    
    # Mock agent not found and subprocess fallback
    with patch.object(orchestrator, '_get_agent_prompt') as mock_get_prompt:
        mock_get_prompt.return_value = None  # No agent found
        
        # Mock the subprocess fallback to also fail
        with patch.object(orchestrator, '_execute_subprocess_delegation') as mock_subprocess:
            mock_subprocess.return_value = (
                {"success": False, "subprocess_id": "test_fail", "error": "Agent not found"},
                ReturnCode.AGENT_NOT_FOUND
            )
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="nonexistent_agent",
                task_description="Test agent not found"
            )
            
            assert return_code == ReturnCode.AGENT_NOT_FOUND
            assert result["success"] is False


@pytest.mark.asyncio
async def test_timeout_returns_timeout_code(orchestrator):
    """Test that timeout returns TIMEOUT code."""
    # Mock timeout error
    with patch.object(orchestrator, '_determine_orchestration_mode') as mock_mode:
        mock_mode.side_effect = asyncio.TimeoutError("Test timeout")
        
        # Mock the emergency fallback
        with patch.object(orchestrator, '_emergency_subprocess_fallback') as mock_fallback:
            mock_fallback.return_value = (
                {"success": False, "error": "Timeout after 1s", "subprocess_id": "timeout_test"},
                ReturnCode.TIMEOUT
            )
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test timeout",
                timeout_seconds=1
            )
            
            assert return_code == ReturnCode.TIMEOUT
            assert result["success"] is False
            assert "Timeout" in result.get("error", "")


@pytest.mark.asyncio
async def test_message_bus_error_returns_correct_code(orchestrator):
    """Test that message bus errors return MESSAGE_BUS_ERROR code."""
    # Force local mode
    orchestrator.set_force_mode(OrchestrationMode.LOCAL)
    
    # Mock components
    orchestrator._message_bus = AsyncMock()
    orchestrator._context_manager = Mock()
    orchestrator._agent_registry = Mock()
    orchestrator._prompt_cache = Mock()
    
    # Mock successful agent prompt
    with patch.object(orchestrator, '_get_agent_prompt') as mock_prompt:
        mock_prompt.return_value = "Test agent prompt"
        
        # Mock context collection
        with patch.object(orchestrator, '_collect_full_context') as mock_context:
            mock_context.return_value = {"files": {}}
            
            # Mock message bus error
            error_response = Response(
                request_id="test_req",
                agent_id="test",
                status=MessageStatus.FAILED,
                error="Message bus routing failed"
            )
            orchestrator._message_bus.route_message.return_value = error_response
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test message bus error"
            )
            
            assert return_code == ReturnCode.MESSAGE_BUS_ERROR
            assert result["success"] is False


@pytest.mark.asyncio
async def test_context_filtering_error_returns_correct_code(orchestrator):
    """Test that context filtering errors return CONTEXT_FILTERING_ERROR code."""
    # Force local mode
    orchestrator.set_force_mode(OrchestrationMode.LOCAL)
    
    # Mock components
    orchestrator._message_bus = AsyncMock()
    orchestrator._context_manager = Mock()
    orchestrator._agent_registry = Mock()
    orchestrator._prompt_cache = Mock()
    
    # Mock successful agent prompt
    with patch.object(orchestrator, '_get_agent_prompt') as mock_prompt:
        mock_prompt.return_value = "Test agent prompt"
        
        # Mock context collection
        with patch.object(orchestrator, '_collect_full_context') as mock_context:
            mock_context.return_value = {"files": {}}
            
            # Mock context filtering error in message bus
            error_response = Response(
                request_id="test_req",
                agent_id="test",
                status=MessageStatus.FAILED,
                error="Context filtering failed: invalid context data"
            )
            orchestrator._message_bus.route_message.return_value = error_response
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test context filtering error"
            )
            
            assert return_code == ReturnCode.CONTEXT_FILTERING_ERROR
            assert result["success"] is False


@pytest.mark.asyncio
async def test_general_failure_returns_correct_code(orchestrator):
    """Test that general failures return GENERAL_FAILURE code."""
    # Mock a general error
    with patch.object(orchestrator, '_determine_orchestration_mode') as mock_mode:
        mock_mode.side_effect = Exception("General test error")
        
        # Mock the emergency fallback
        with patch.object(orchestrator, '_emergency_subprocess_fallback') as mock_fallback:
            mock_fallback.return_value = (
                {"success": False, "error": "General test error", "subprocess_id": "error_test"},
                ReturnCode.GENERAL_FAILURE
            )
            
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="test",
                task_description="Test general failure"
            )
            
            assert return_code == ReturnCode.GENERAL_FAILURE
            assert result["success"] is False


@pytest.mark.asyncio
async def test_convenience_function_returns_tuple():
    """Test that the convenience function returns a tuple with return code."""
    with patch('claude_pm.orchestration.backwards_compatible_orchestrator.BackwardsCompatibleOrchestrator') as mock_class:
        mock_instance = mock_class.return_value
        mock_instance.delegate_to_agent.return_value = (
            {"success": True, "subprocess_id": "test_123"},
            ReturnCode.SUCCESS
        )
        
        result, return_code = await delegate_with_compatibility(
            agent_type="test",
            task_description="Test convenience function"
        )
        
        assert isinstance(result, dict)
        assert isinstance(return_code, int)
        assert return_code == ReturnCode.SUCCESS


@pytest.mark.asyncio
async def test_return_codes_in_metrics(orchestrator):
    """Test that return codes are tracked in metrics."""
    # Perform several operations with different outcomes
    
    # Success case
    with patch.object(orchestrator, '_execute_subprocess_delegation') as mock_subprocess:
        mock_subprocess.return_value = (
            {"success": True, "subprocess_id": "test_1"},
            ReturnCode.SUCCESS
        )
        await orchestrator.delegate_to_agent("test", "Success test")
    
    # Failure case
    with patch.object(orchestrator, '_determine_orchestration_mode') as mock_mode:
        mock_mode.side_effect = Exception("Test failure")
        with patch.object(orchestrator, '_emergency_subprocess_fallback') as mock_fallback:
            mock_fallback.return_value = (
                {"success": False, "error": "Test failure", "subprocess_id": "error_test"},
                ReturnCode.GENERAL_FAILURE
            )
            await orchestrator.delegate_to_agent("test", "Failure test")
    
    # Check metrics
    metrics = orchestrator.get_orchestration_metrics()
    
    assert metrics["total_orchestrations"] == 2
    assert metrics["success_count"] == 1
    assert metrics["success_rate"] == 50.0
    assert "GENERAL_FAILURE" in metrics["failure_by_code"]
    assert metrics["failure_by_code"]["GENERAL_FAILURE"] == 1


def test_return_code_constants():
    """Test that return code constants have expected values."""
    assert ReturnCode.SUCCESS == 0
    assert ReturnCode.GENERAL_FAILURE == 1
    assert ReturnCode.TIMEOUT == 2
    assert ReturnCode.CONTEXT_FILTERING_ERROR == 3
    assert ReturnCode.AGENT_NOT_FOUND == 4
    assert ReturnCode.MESSAGE_BUS_ERROR == 5