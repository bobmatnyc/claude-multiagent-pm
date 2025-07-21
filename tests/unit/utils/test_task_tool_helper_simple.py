"""
Simplified Unit Tests for Task Tool Helper

Tests core functionality with minimal mocking to improve coverage.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from claude_pm.utils.task_tool_helper import (
    TaskToolHelper,
    TaskToolConfiguration,
    quick_create_subprocess,
    validate_task_tool_integration
)
from claude_pm.core.response_types import TaskToolResponse


class TestTaskToolHelperCore:
    """Test TaskToolHelper core functionality with minimal mocking."""
    
    def test_initialization_defaults(self):
        """Test TaskToolHelper initialization with defaults."""
        helper = TaskToolHelper()
        
        assert helper.working_directory == Path.cwd()
        assert helper.config.timeout_seconds == 300
        assert helper.config.memory_collection_required is True
        assert len(helper._active_subprocesses) == 0
        assert len(helper._subprocess_history) == 0
    
    def test_initialization_with_config(self):
        """Test TaskToolHelper initialization with custom config."""
        config = TaskToolConfiguration(
            timeout_seconds=600,
            memory_collection_required=False,
            model_override="claude-4-opus"
        )
        helper = TaskToolHelper(config=config)
        
        assert helper.config.timeout_seconds == 600
        assert helper.config.memory_collection_required is False
        assert helper.config.model_override == "claude-4-opus"
    
    def test_initialization_with_model_override(self):
        """Test TaskToolHelper initialization with model override."""
        helper = TaskToolHelper(model_override="claude-4-opus")
        
        assert helper.config.model_override == "claude-4-opus"
    
    @pytest.mark.asyncio
    async def test_create_agent_subprocess_basic(self):
        """Test basic subprocess creation."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            # Setup minimal mock
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_agent_subprocess(
                agent_type="engineer",
                task_description="Test task"
            )
            
            assert result["success"] is True
            assert "subprocess_id" in result
            assert result["subprocess_id"].startswith("engineer_")
            assert result["prompt"] == "Test prompt"
    
    def test_get_subprocess_status_empty(self):
        """Test subprocess status when no subprocesses exist."""
        helper = TaskToolHelper()
        status = helper.get_subprocess_status()
        
        assert status["active_subprocesses"] == 0
        assert status["total_subprocesses"] == 0
        assert status["active_agents"] == []
        assert status["recent_subprocesses"] == []
    
    def test_complete_subprocess_not_found(self):
        """Test completing non-existent subprocess."""
        helper = TaskToolHelper()
        success = helper.complete_subprocess("nonexistent", {"result": "test"})
        
        assert success is False
    
    def test_list_available_agents(self):
        """Test listing available agents."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            mock_pm_instance = Mock()
            mock_pm_instance.list_available_agents.return_value = {
                "system": ["engineer", "qa"],
                "user": [],
                "project": []
            }
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            agents = helper.list_available_agents()
            
            assert "system" in agents
            assert "engineer" in agents["system"]
    
    def test_generate_delegation_summary_empty(self):
        """Test delegation summary with no subprocesses."""
        helper = TaskToolHelper()
        summary = helper.generate_delegation_summary()
        
        assert "Active Subprocesses: 0" in summary
        assert "Total Subprocesses Created: 0" in summary
        assert "(No active delegations)" in summary
    
    def test_task_complexity_analysis(self):
        """Test task complexity analysis."""
        helper = TaskToolHelper()
        
        # Test expert complexity
        assert helper._analyze_task_complexity("Design complex machine learning architecture") == "expert"
        assert helper._analyze_task_complexity("AI algorithm optimization") == "expert"
        
        # Test high complexity
        assert helper._analyze_task_complexity("Implement authentication system") == "high"
        assert helper._analyze_task_complexity("Build distributed system") == "high"
        
        # Test low complexity
        assert helper._analyze_task_complexity("List files in directory") == "low"
        assert helper._analyze_task_complexity("Show simple output") == "low"
        
        # Test medium complexity (default)
        assert helper._analyze_task_complexity("Update documentation") == "medium"
        assert helper._analyze_task_complexity("") == "medium"
        assert helper._analyze_task_complexity(None) == "medium"
    
    def test_reasoning_depth_determination(self):
        """Test reasoning depth determination."""
        helper = TaskToolHelper()
        
        # Agent-based defaults
        assert helper._determine_reasoning_depth("engineer", "Build") == "expert"
        assert helper._determine_reasoning_depth("architecture", "Design") == "expert"
        assert helper._determine_reasoning_depth("orchestrator", "Manage") == "expert"
        assert helper._determine_reasoning_depth("research", "Analyze") == "deep"
        assert helper._determine_reasoning_depth("qa", "Test") == "deep"
        assert helper._determine_reasoning_depth("documentation", "Write") == "standard"
        
        # Task-based overrides
        assert helper._determine_reasoning_depth("qa", "Plan testing strategy") == "expert"
        assert helper._determine_reasoning_depth("ops", "Analyze performance") == "deep"
        assert helper._determine_reasoning_depth("security", "Quick check") == "simple"
    
    def test_check_creativity_requirements(self):
        """Test creativity requirement checking."""
        helper = TaskToolHelper()
        
        assert helper._check_creativity_requirements("Create innovative solution") is True
        assert helper._check_creativity_requirements("Design new system") is True
        assert helper._check_creativity_requirements("Brainstorm ideas") is True
        assert helper._check_creativity_requirements("Generate novel approach") is True
        
        assert helper._check_creativity_requirements("Update existing code") is False
        assert helper._check_creativity_requirements("Fix bug") is False
        assert helper._check_creativity_requirements("") is False
    
    def test_check_speed_priority(self):
        """Test speed priority checking."""
        helper = TaskToolHelper()
        
        # Check task description
        assert helper._check_speed_priority("Urgent fix needed", None) is True
        assert helper._check_speed_priority("Quick analysis", None) is True
        assert helper._check_speed_priority("ASAP deployment", None) is True
        assert helper._check_speed_priority("Real-time processing", None) is True
        
        assert helper._check_speed_priority("Thorough analysis", None) is False
        assert helper._check_speed_priority("", None) is False
        
        # Check performance requirements
        assert helper._check_speed_priority("Task", {"speed_priority": True}) is True
        assert helper._check_speed_priority("Task", {"speed_priority": False}) is False
    
    def test_configure_model_selection(self):
        """Test model selection configuration."""
        helper = TaskToolHelper()
        
        # Valid configuration
        success = helper.configure_model_selection(
            enable_model_selection=False,
            model_override="claude-4-opus",
            performance_priority="quality"
        )
        
        assert success is True
        assert helper.config.enable_model_selection is False
        assert helper.config.model_override == "claude-4-opus"
        assert helper.config.performance_priority == "quality"
        
        # Invalid performance priority
        success = helper.configure_model_selection(performance_priority="invalid")
        assert success is False
    
    def test_get_correction_statistics_disabled(self):
        """Test correction statistics when disabled."""
        config = TaskToolConfiguration(correction_capture_enabled=False)
        helper = TaskToolHelper(config=config)
        
        stats = helper.get_correction_statistics()
        
        assert stats["enabled"] is False
        assert stats["message"] == "Correction capture not enabled"
    
    def test_capture_correction_disabled(self):
        """Test correction capture when disabled."""
        config = TaskToolConfiguration(correction_capture_enabled=False)
        helper = TaskToolHelper(config=config)
        
        result = helper.capture_correction(
            subprocess_id="test",
            original_response="original",
            user_correction="corrected"
        )
        
        assert result == ""
    
    def test_capture_correction_no_subprocess(self):
        """Test correction capture with non-existent subprocess."""
        helper = TaskToolHelper()
        
        result = helper.capture_correction(
            subprocess_id="nonexistent",
            original_response="original",
            user_correction="corrected"
        )
        
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_model_selection_fallback(self):
        """Test model selection fallback mechanism."""
        # Disable model selection to force fallback
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        # Test fallback for different agent types
        model, config = await helper._select_model_for_subprocess(
            "engineer", "Test task"
        )
        assert model == "claude-4-opus"  # Default for engineer
        assert config["selection_method"] == "fallback"
        
        model, config = await helper._select_model_for_subprocess(
            "documentation", "Test task"
        )
        assert model == "claude-sonnet-4-20250514"  # Default for documentation
        assert config["selection_method"] == "fallback"
        
        model, config = await helper._select_model_for_subprocess(
            "unknown_agent", "Test task"
        )
        assert model == "claude-sonnet-4-20250514"  # Default fallback
        assert config["selection_method"] == "fallback"
    
    @pytest.mark.asyncio
    async def test_model_selection_with_override(self):
        """Test model selection with explicit override."""
        helper = TaskToolHelper()
        
        model, config = await helper._select_model_for_subprocess(
            "engineer", "Test task", model_override="claude-4-opus"
        )
        
        assert model == "claude-4-opus"
        assert config["override"] is True
        assert config["source"] == "explicit_override"
    
    def test_validate_integration_basic(self):
        """Test basic integration validation."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            mock_pm_instance = Mock()
            mock_pm_instance.validate_agent_hierarchy.return_value = {"valid": True}
            mock_pm_instance.list_available_agents.return_value = {"system": ["engineer"]}
            mock_pm_instance.generate_agent_prompt.return_value = "Test prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            validation = helper.validate_integration()
            
            assert validation["valid"] is True
            assert validation["working_directory"] == str(Path.cwd())
            assert validation["config"]["timeout_seconds"] == 300
    
    @pytest.mark.asyncio
    async def test_create_shortcut_subprocess_push(self):
        """Test creating push shortcut subprocess."""
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_pm:
            mock_pm_instance = Mock()
            mock_pm_instance.generate_agent_prompt.return_value = "Push prompt"
            mock_pm.return_value = mock_pm_instance
            
            helper = TaskToolHelper()
            result = await helper.create_shortcut_subprocess("push")
            
            assert result["success"] is True
            assert result["subprocess_info"]["agent_type"] == "documentation"
            assert "changelog" in result["subprocess_info"]["task_description"].lower()
    
    @pytest.mark.asyncio
    async def test_create_shortcut_subprocess_invalid(self):
        """Test creating invalid shortcut subprocess."""
        helper = TaskToolHelper()
        result = await helper.create_shortcut_subprocess("invalid_shortcut")
        
        assert isinstance(result, TaskToolResponse)
        assert result.success is False
        assert "Unknown shortcut type" in result.error
    
    def test_model_selection_performance_priority(self):
        """Test performance priority in model selection."""
        helper = TaskToolHelper()
        
        # Test speed priority
        helper.config.performance_priority = "speed"
        criteria = helper._create_selection_criteria("qa", "urgent task")
        assert criteria.speed_priority is True
        
        # Test quality priority  
        helper.config.performance_priority = "quality"
        criteria = helper._create_selection_criteria("qa", "simple task")
        # Low complexity should be upgraded to medium
        assert criteria.task_complexity == "medium"
    
    @pytest.mark.asyncio
    async def test_get_agent_model_recommendation_no_selector(self):
        """Test model recommendation without selector."""
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        recommendation = await helper.get_agent_model_recommendation("engineer", "Test")
        
        assert "error" in recommendation
        assert recommendation["error"] == "Model selection not available"
        assert recommendation["fallback_model"] == "claude-sonnet-4-20250514"
    
    @pytest.mark.asyncio
    async def test_validate_model_configuration_no_selector(self):
        """Test model validation without selector."""
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        validation = await helper.validate_model_configuration("engineer", "claude-4-opus")
        
        assert validation["valid"] is False
        assert validation["error"] == "Model selection not available"
    
    def test_get_available_models_no_selector(self):
        """Test getting available models without selector."""
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        models = helper.get_available_models()
        
        assert models == ["claude-sonnet-4-20250514", "claude-4-opus"]
    
    def test_get_model_selection_statistics_no_selector(self):
        """Test model selection stats without selector."""
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        stats = helper.get_model_selection_statistics()
        
        assert stats["error"] == "Model selection not available"
    
    @pytest.mark.asyncio
    async def test_get_agent_registry_model_stats_no_registry(self):
        """Test agent registry stats without registry."""
        config = TaskToolConfiguration(enable_model_selection=False)
        helper = TaskToolHelper(config=config)
        
        stats = await helper.get_agent_registry_model_stats()
        
        assert stats["error"] == "Agent registry not available"


class TestHelperFunctions:
    """Test standalone helper functions."""
    
    def test_validate_task_tool_integration_function(self):
        """Test validate_task_tool_integration function."""
        with patch('claude_pm.utils.task_tool_helper.TaskToolHelper') as mock_helper_class:
            mock_helper = Mock()
            mock_helper.validate_integration.return_value = {"valid": True}
            mock_helper_class.return_value = mock_helper
            
            result = validate_task_tool_integration()
            
            assert result["valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])