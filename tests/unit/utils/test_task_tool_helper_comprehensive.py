"""
Comprehensive Unit Tests for Task Tool Helper

Complete test coverage including error cases, edge cases, and integration scenarios.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

from claude_pm.utils.task_tool_helper import (
    TaskToolHelper,
    TaskToolConfiguration,
    quick_create_subprocess,
    create_pm_shortcuts,
    validate_task_tool_integration
)
from claude_pm.core.response_types import TaskToolResponse


class TestTaskToolHelperComprehensive:
    """Comprehensive tests for TaskToolHelper to maximize coverage."""
    
    @pytest.mark.asyncio
    async def test_create_subprocess_with_orchestration_enabled(self):
        """Test subprocess creation when orchestration is enabled."""
        with patch('claude_pm.orchestration.orchestration_detector.OrchestrationDetector') as mock_detector, \
             patch('claude_pm.orchestration.backwards_compatible_orchestrator.BackwardsCompatibleOrchestrator') as mock_orchestrator:
            
            # Setup orchestration as enabled
            mock_detector_instance = Mock()
            mock_detector_instance.is_enabled.return_value = True
            mock_detector.return_value = mock_detector_instance
            
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator_instance.delegate_to_agent.return_value = {
                "success": True,
                "subprocess_id": "orch_123",
                "context_filtered": True
            }
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test with orchestration"
            )
            
            assert result["success"] is True
            assert result["subprocess_id"] == "orch_123"
            mock_orchestrator_instance.delegate_to_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_subprocess_orchestration_import_error(self):
        """Test subprocess creation when orchestration modules aren't available."""
        with patch('claude_pm.orchestration.orchestration_detector.OrchestrationDetector', side_effect=ImportError), \
             patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test without orchestration"
            )
            
            # Should fall back to standard implementation
            assert result["success"] is True
            assert "subprocess_id" in result
    
    @pytest.mark.asyncio
    async def test_create_subprocess_orchestration_exception(self):
        """Test subprocess creation when orchestration check fails."""
        with patch('claude_pm.orchestration.orchestration_detector.OrchestrationDetector') as mock_detector, \
             patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.logger') as mock_logger:
            
            # Make orchestration check fail
            mock_detector_instance = Mock()
            mock_detector_instance.is_enabled.side_effect = Exception("Check failed")
            mock_detector.return_value = mock_detector_instance
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test with failed check"
            )
            
            # Should fall back to standard implementation
            assert result["success"] is True
            mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_subprocess_with_all_parameters(self):
        """Test subprocess creation with all optional parameters."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.collect_pm_orchestrator_memory') as mock_collect:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Full prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Complex task",
                requirements=["Req1", "Req2"],
                deliverables=["Del1", "Del2"],
                dependencies=["Dep1", "Dep2"],
                priority="critical",
                memory_categories=["cat1", "cat2"],
                timeout_seconds=600,
                escalation_triggers=["Trigger1"],
                integration_notes="Important notes",
                model_override="claude-4-opus",
                performance_requirements={"speed": "fast"}
            )
            
            assert result["success"] is True
            info = result["subprocess_info"]
            assert info["requirements"] == ["Req1", "Req2"]
            assert info["deliverables"] == ["Del1", "Del2"]
            assert info["dependencies"] == ["Dep1", "Dep2"]
            assert info["priority"] == "critical"
            assert info["timeout_seconds"] == 600
            assert info["selected_model"] == "claude-4-opus"
    
    @pytest.mark.asyncio
    async def test_create_subprocess_prompt_generation_error(self):
        """Test subprocess creation when prompt generation fails."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.collect_pm_orchestrator_memory') as mock_collect:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.side_effect = Exception("Generation failed")
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test error"
            )
            
            assert isinstance(result, TaskToolResponse)
            assert result.success is False
            assert "Generation failed" in result.error
            # Error memory should be collected
            assert mock_collect.call_count == 1
            assert "error:integration" in mock_collect.call_args[1]["category"]
    
    @pytest.mark.asyncio
    async def test_create_subprocess_with_correction_capture(self):
        """Test subprocess creation with correction capture enabled."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_correction_instance = Mock()
            mock_correction_instance.create_task_tool_integration_hook.return_value = {
                "hook_id": "hook_123"
            }
            mock_correction.return_value = mock_correction_instance
            
            config = TaskToolConfiguration(correction_capture_auto_hook=True)
            helper = TaskToolHelper(config=config)
            
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test with correction"
            )
            
            assert result["success"] is True
            assert result["correction_hook"]["hook_id"] == "hook_123"
            mock_correction_instance.create_task_tool_integration_hook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_subprocess_correction_hook_error(self):
        """Test subprocess creation when correction hook fails."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction, \
             patch('claude_pm.utils.task_tool_helper.logger') as mock_logger:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_correction_instance = Mock()
            mock_correction_instance.create_task_tool_integration_hook.side_effect = Exception("Hook failed")
            mock_correction.return_value = mock_correction_instance
            
            config = TaskToolConfiguration(correction_capture_auto_hook=True)
            helper = TaskToolHelper(config=config)
            
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test hook error"
            )
            
            # Should still succeed but log error
            assert result["success"] is True
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_model_selection_with_agent_registry(self):
        """Test model selection using agent registry configuration."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.AgentRegistry') as mock_registry:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_agent_model_configuration.return_value = {
                "preferred_model": "claude-4-opus",
                "model_config": {
                    "max_tokens": 8192,
                    "context_window": 300000
                },
                "capabilities": ["advanced"],
                "complexity_level": "expert",
                "specializations": ["architecture"]
            }
            mock_registry.return_value = mock_registry_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="architecture",
                task_description="Design system"
            )
            
            assert result["success"] is True
            info = result["subprocess_info"]
            assert info["selected_model"] == "claude-4-opus"
            assert info["model_config"]["max_tokens"] == 8192
            assert info["model_config"]["selection_method"] == "agent_registry_configuration"
    
    @pytest.mark.asyncio
    async def test_model_selection_registry_exception(self):
        """Test model selection when agent registry throws exception."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.AgentRegistry') as mock_registry, \
             patch('claude_pm.utils.task_tool_helper.ModelSelector') as mock_selector, \
             patch('claude_pm.utils.task_tool_helper.logger') as mock_logger:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_agent_model_configuration.side_effect = Exception("Registry error")
            mock_registry.return_value = mock_registry_instance
            
            mock_selector_instance = Mock()
            mock_selector_instance.select_model_for_agent.return_value = (
                Mock(value="claude-sonnet-4-20250514"),
                Mock(max_tokens=4096, context_window=200000, capabilities=[], performance_profile={})
            )
            mock_selector.return_value = mock_selector_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test registry error"
            )
            
            assert result["success"] is True
            # Should fall back to ModelSelector
            mock_logger.warning.assert_called()
            mock_selector_instance.select_model_for_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_model_selection_with_model_selector(self):
        """Test model selection using ModelSelector."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.AgentRegistry') as mock_registry, \
             patch('claude_pm.utils.task_tool_helper.ModelSelector') as mock_selector:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_agent_model_configuration.return_value = None
            mock_registry.return_value = mock_registry_instance
            
            mock_selector_instance = Mock()
            mock_selector_instance.select_model_for_agent.return_value = (
                Mock(value="claude-4-opus"),
                Mock(
                    max_tokens=8192,
                    context_window=300000,
                    capabilities=["reasoning"],
                    performance_profile={"quality": "high"}
                )
            )
            mock_selector.return_value = mock_selector_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="research",
                task_description="Complex research task"
            )
            
            assert result["success"] is True
            info = result["subprocess_info"]
            assert info["selected_model"] == "claude-4-opus"
            assert info["model_config"]["selection_method"] == "intelligent_selection"
            assert "criteria" in info["model_config"]
    
    @pytest.mark.asyncio
    async def test_model_selection_selector_exception(self):
        """Test model selection when ModelSelector throws exception."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.AgentRegistry') as mock_registry, \
             patch('claude_pm.utils.task_tool_helper.ModelSelector') as mock_selector, \
             patch('claude_pm.utils.task_tool_helper.logger') as mock_logger:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_agent_model_configuration.return_value = None
            mock_registry.return_value = mock_registry_instance
            
            mock_selector_instance = Mock()
            mock_selector_instance.select_model_for_agent.side_effect = Exception("Selector error")
            mock_selector.return_value = mock_selector_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="ops",
                task_description="Test selector error"
            )
            
            assert result["success"] is True
            info = result["subprocess_info"]
            # Should fall back to default mapping
            assert info["selected_model"] == "claude-sonnet-4-20250514"
            assert info["model_config"]["selection_method"] == "fallback"
            mock_logger.warning.assert_called()
    
    
    
    def test_complete_subprocess_with_results(self):
        """Test completing subprocess with results."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.collect_pm_orchestrator_memory') as mock_collect:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm_instance.complete_delegation = Mock()
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            
            # Create subprocess first
            result = asyncio.run(helper.create_agent_subprocess(
                agent_type="qa",
                task_description="Run tests"
            ))
            subprocess_id = result["subprocess_id"]
            
            # Complete it
            results = {"tests_passed": 42, "summary": "All passed"}
            success = helper.complete_subprocess(subprocess_id, results)
            
            assert success is True
            assert subprocess_id not in helper._active_subprocesses
            
            # Check history was updated
            history_entry = next(e for e in helper._subprocess_history if e["subprocess_id"] == subprocess_id)
            assert history_entry["status"] == "completed"
            assert history_entry["results"] == results
            
            mock_pm_instance.complete_delegation.assert_called_once_with(subprocess_id, results)
            # Completion memory should be collected
            assert any("Completed Task Tool subprocess" in call[1]["content"] for call in mock_collect.call_args_list)
    
    def test_capture_correction_with_active_subprocess(self):
        """Test capturing correction for active subprocess."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_correction_instance = Mock()
            mock_correction_instance.capture_correction.return_value = "correction_456"
            mock_correction.return_value = mock_correction_instance
            
            helper = TaskToolHelper()
            
            # Create subprocess
            result = asyncio.run(helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Write code"
            ))
            subprocess_id = result["subprocess_id"]
            
            # Capture correction
            correction_id = helper.capture_correction(
                subprocess_id=subprocess_id,
                original_response="def func():",
                user_correction="def func() -> str:",
                correction_type="CONTENT_CORRECTION",
                severity="high",
                user_feedback="Add type hints"
            )
            
            assert correction_id == "correction_456"
            mock_correction_instance.capture_correction.assert_called_once()
            
            # Check correction type conversion
            call_args = mock_correction_instance.capture_correction.call_args[1]
            assert call_args["agent_type"] == "engineer"
            assert call_args["severity"] == "high"
    
    def test_capture_correction_from_history(self):
        """Test capturing correction for completed subprocess from history."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm, \
             patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            mock_correction_instance = Mock()
            mock_correction_instance.capture_correction.return_value = "correction_789"
            mock_correction.return_value = mock_correction_instance
            
            helper = TaskToolHelper()
            
            # Add to history manually
            helper._subprocess_history.append({
                "subprocess_id": "historical_123",
                "agent_type": "qa",
                "task_description": "Test historical"
            })
            
            # Capture correction
            correction_id = helper.capture_correction(
                subprocess_id="historical_123",
                original_response="test failed",
                user_correction="test passed"
            )
            
            assert correction_id == "correction_789"
    
    def test_capture_correction_exception(self):
        """Test capturing correction when exception occurs."""
        with patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction, \
             patch('claude_pm.utils.task_tool_helper.logger') as mock_logger:
            
            mock_correction_instance = Mock()
            mock_correction_instance.capture_correction.side_effect = Exception("Capture failed")
            mock_correction.return_value = mock_correction_instance
            
            helper = TaskToolHelper()
            helper._subprocess_history.append({
                "subprocess_id": "test_123",
                "agent_type": "engineer"
            })
            
            correction_id = helper.capture_correction(
                subprocess_id="test_123",
                original_response="original",
                user_correction="corrected"
            )
            
            assert correction_id == ""
            mock_logger.error.assert_called()
    
    def test_get_correction_statistics_with_error(self):
        """Test getting correction statistics when service fails."""
        with patch('claude_pm.utils.task_tool_helper.CorrectionCapture') as mock_correction:
            
            mock_correction_instance = Mock()
            mock_correction_instance.get_correction_stats.side_effect = Exception("Stats failed")
            mock_correction.return_value = mock_correction_instance
            
            helper = TaskToolHelper()
            stats = helper.get_correction_statistics()
            
            assert isinstance(stats, TaskToolResponse)
            assert stats.success is False
            assert "Stats failed" in stats.error
    
    def test_validate_integration_with_error(self):
        """Test integration validation with error."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            
            mock_pm_instance = Mock()
            mock_pm_instance.validate_agent_hierarchy.side_effect = Exception("Validation failed")
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            validation = helper.validate_integration()
            
            assert validation["valid"] is False
            assert "Validation failed" in validation["error"]
    
    @pytest.mark.asyncio
    async def test_create_shortcut_subprocess_all_types(self):
        """Test creating all shortcut subprocess types."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Shortcut prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            
            # Test all shortcuts
            shortcuts = ["push", "deploy", "test", "publish"]
            for shortcut in shortcuts:
                result = await helper.create_shortcut_subprocess(shortcut)
                assert result["success"] is True
                assert "subprocess_info" in result
    
    @pytest.mark.asyncio
    async def test_create_shortcut_subprocess_with_kwargs(self):
        """Test creating shortcut subprocess with additional kwargs."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Custom prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_shortcut_subprocess(
                "push",
                priority="urgent",
                timeout_seconds=1200
            )
            
            assert result["success"] is True
            assert result["subprocess_info"]["priority"] == "urgent"
            assert result["subprocess_info"]["timeout_seconds"] == 1200
    
    @pytest.mark.asyncio
    async def test_get_model_selection_statistics_with_selector(self):
        """Test getting model selection statistics with selector available."""
        with patch('claude_pm.utils.task_tool_helper.ModelSelector') as mock_selector:
            
            mock_selector_instance = Mock()
            mock_selector_instance.get_selection_statistics.return_value = {
                "total_selections": 100,
                "by_model": {"claude-4-opus": 60, "claude-sonnet-4-20250514": 40}
            }
            mock_selector.return_value = mock_selector_instance
            
            helper = TaskToolHelper()
            stats = helper.get_model_selection_statistics()
            
            assert stats["total_selections"] == 100
            assert stats["by_model"]["claude-4-opus"] == 60
    
    @pytest.mark.asyncio
    async def test_get_agent_registry_model_stats_with_registry(self):
        """Test getting agent registry model stats with registry available."""
        with patch('claude_pm.utils.task_tool_helper.AgentRegistry') as mock_registry:
            
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_model_usage_statistics.return_value = {
                "agents_configured": 15,
                "model_distribution": {"claude-4-opus": 10, "claude-sonnet-4-20250514": 5}
            }
            mock_registry.return_value = mock_registry_instance
            
            helper = TaskToolHelper()
            stats = await helper.get_agent_registry_model_stats()
            
            assert stats["agents_configured"] == 15
            assert stats["model_distribution"]["claude-4-opus"] == 10
    
    @pytest.mark.asyncio
    async def test_quick_create_subprocess_with_orchestration(self):
        """Test quick_create_subprocess with orchestration enabled."""
        with patch('claude_pm.orchestration.orchestration_detector.OrchestrationDetector') as mock_detector, \
             patch('claude_pm.orchestration.backwards_compatible_orchestrator.quick_delegate') as mock_delegate:
            
            mock_detector_instance = Mock()
            mock_detector_instance.is_enabled.return_value = True
            mock_detector.return_value = mock_detector_instance
            
            mock_delegate.return_value = {"success": True, "subprocess_id": "quick_123"}
            
            result = await quick_create_subprocess(
                agent_type="engineer",
                task_description="Quick task",
                requirements=["R1"],
                deliverables=["D1"]
            )
            
            assert result["success"] is True
            assert result["subprocess_id"] == "quick_123"
            mock_delegate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_quick_create_subprocess_without_orchestration(self):
        """Test quick_create_subprocess without orchestration."""
        with patch('claude_pm.orchestration.orchestration_detector.OrchestrationDetector', side_effect=ImportError), \
             patch('claude_pm.utils.task_tool_helper.TaskToolHelper') as mock_helper_class:
            
            mock_helper = AsyncMock()
            mock_helper.create_agent_subprocess.return_value = {
                "success": True,
                "subprocess_id": "standard_123"
            }
            mock_helper_class.return_value = mock_helper
            
            result = await quick_create_subprocess(
                agent_type="qa",
                task_description="Quick test"
            )
            
            assert result["success"] is True
            assert result["subprocess_id"] == "standard_123"
    
    @pytest.mark.asyncio
    async def test_create_pm_shortcuts_all(self):
        """Test creating all PM shortcuts."""
        with patch('claude_pm.utils.task_tool_helper.TaskToolHelper') as mock_helper_class:
            
            mock_helper = AsyncMock()
            mock_helper.create_shortcut_subprocess.side_effect = [
                {"success": True, "subprocess_id": "push_123"},
                {"success": True, "subprocess_id": "deploy_123"},
                {"success": True, "subprocess_id": "test_123"},
                {"success": True, "subprocess_id": "publish_123"}
            ]
            mock_helper_class.return_value = mock_helper
            
            shortcuts = await create_pm_shortcuts()
            
            assert len(shortcuts) == 4
            assert all(shortcut in shortcuts for shortcut in ["push", "deploy", "test", "publish"])
            assert all(shortcuts[s]["success"] for s in shortcuts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])