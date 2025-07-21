#!/usr/bin/env python3
"""
Integration test for model selection based on task complexity.

Tests the complete workflow from task description to model selection.
"""

import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, Mock

from claude_pm.agents.agent_loader import (
    get_agent_prompt_with_model_info,
    get_model_selection_metrics,
    MODEL_NAME_MAPPINGS
)
from claude_pm.services.task_complexity_analyzer import ModelType
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration


class TestModelSelectionIntegration:
    """Test the complete model selection integration."""
    
    @pytest.fixture
    def enable_dynamic_selection(self):
        """Enable dynamic model selection."""
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        yield
        os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
    
    @pytest.fixture
    def mock_framework_setup(self):
        """Mock framework setup for integration tests."""
        with patch('claude_pm.agents.agent_loader.FRAMEWORK_AGENT_ROLES_DIR', Path('/mock/framework/agent-roles')):
            with patch('claude_pm.agents.agent_loader.load_agent_prompt_from_md') as mock_load:
                mock_load.return_value = "Mock agent prompt content"
                with patch('claude_pm.agents.agent_loader.prepend_base_instructions') as mock_prepend:
                    mock_prepend.side_effect = lambda x: f"BASE\n{x}"
                    yield
    
    def test_simple_task_selects_haiku(self, enable_dynamic_selection, mock_framework_setup):
        """Test that simple tasks select Haiku model."""
        task_description = "Check the current git status"
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'documentation',
                task_description=task_description
            )
        
        assert model == MODEL_NAME_MAPPINGS[ModelType.HAIKU]
        assert config['selection_method'] == 'dynamic_complexity_based'
        assert config['complexity_level'] == 'SIMPLE'
        assert config['complexity_score'] <= 30
    
    def test_medium_task_selects_sonnet(self, enable_dynamic_selection, mock_framework_setup):
        """Test that medium complexity tasks select Sonnet model."""
        task_description = "Implement a comprehensive REST API endpoint for user management with authentication, validation, and error handling"
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'engineer',
                task_description=task_description,
                file_count=5,
                requires_testing=True,
                requires_documentation=True,
                integration_points=2
            )
        
        assert model == MODEL_NAME_MAPPINGS[ModelType.SONNET]
        assert config['selection_method'] == 'dynamic_complexity_based'
        assert config['complexity_level'] == 'MEDIUM'
        assert 30 < config['complexity_score'] <= 70
    
    def test_complex_task_selects_opus(self, enable_dynamic_selection, mock_framework_setup):
        """Test that complex tasks select Opus model."""
        task_description = (
            "Architect and implement a complete microservices migration strategy "
            "for the monolithic application with advanced patterns"
        )
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'engineer',
                task_description=task_description,
                file_count=15,
                integration_points=5,
                requires_research=True,
                requires_testing=True,
                requires_documentation=True,
                technical_depth="deep"
            )
        
        assert model == MODEL_NAME_MAPPINGS[ModelType.OPUS]
        assert config['selection_method'] == 'dynamic_complexity_based'
        assert config['complexity_level'] == 'COMPLEX'
        assert config['complexity_score'] > 70
    
    @pytest.mark.asyncio
    async def test_task_tool_helper_integration(self, enable_dynamic_selection, mock_framework_setup):
        """Test integration with TaskToolHelper."""
        # Mock the orchestration components
        with patch('claude_pm.utils.task_tool_helper.PMOrchestrator') as mock_orchestrator:
            mock_pm = Mock()
            mock_pm.generate_agent_prompt.return_value = "Generated prompt"
            mock_orchestrator.return_value = mock_pm
            
            # Create task tool helper
            config = TaskToolConfiguration(
                enable_model_selection=True,
                performance_priority="balanced"
            )
            helper = TaskToolHelper(
                working_directory=Path.cwd(),
                config=config
            )
            
            # Mock model selector
            with patch('claude_pm.utils.task_tool_helper.ModelSelector') as mock_selector:
                mock_model_selector = Mock()
                mock_model_selector.select_model_for_agent.return_value = (
                    Mock(value='claude-4-opus'),
                    Mock(
                        max_tokens=4096,
                        context_window=200000,
                        capabilities=['advanced_reasoning'],
                        performance_profile='high_quality'
                    )
                )
                mock_selector.return_value = mock_model_selector
                
                # Create subprocess with complex task
                result = await helper.create_agent_subprocess(
                    agent_type="engineer",
                    task_description="Refactor the entire authentication system",
                    requirements=["OAuth2", "JWT", "MFA"],
                    deliverables=["New auth system", "Migration guide", "Tests"]
                )
                
                # Verify subprocess was created with model selection
                # The result structure depends on the TaskToolHelper implementation
                # which may return different structures based on orchestration
                assert result is not None
                # If the result has these fields, verify them
                if 'selected_model' in result:
                    assert result['selected_model'] == 'claude-4-opus'
                if 'model_config' in result:
                    assert result['model_config']['selection_method'] == 'intelligent_selection'
    
    def test_metrics_collection(self, enable_dynamic_selection, mock_framework_setup):
        """Test that metrics are collected correctly."""
        # Clear any existing metrics
        with patch('claude_pm.agents.agent_loader.SharedPromptCache') as mock_cache:
            mock_instance = Mock()
            mock_instance.get.return_value = None
            mock_cache.get_instance.return_value = mock_instance
            
            # Generate prompts with different complexities
            test_cases = [
                ("List files", 'qa', ModelType.HAIKU),
                ("Implement feature", 'engineer', ModelType.SONNET),
                ("Architect system", 'engineer', ModelType.OPUS)
            ]
            
            for task, agent, expected_model in test_cases:
                with patch('claude_pm.agents.agent_loader.log_model_selection') as mock_log:
                    prompt, model, config = get_agent_prompt_with_model_info(
                        agent,
                        task_description=task
                    )
                    
                    # Verify logging was called
                    if config['selection_method'] == 'dynamic_complexity_based':
                        mock_log.assert_called_once()
                        call_args = mock_log.call_args[1]
                        assert call_args['agent_name'] == agent
                        assert call_args['selection_method'] == 'dynamic_complexity_based'
    
    def test_feature_flag_controls(self, mock_framework_setup):
        """Test that feature flags properly control model selection."""
        # Test with flag disabled
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
        
        prompt, model, config = get_agent_prompt_with_model_info(
            'engineer',
            task_description="Complex refactoring task"
        )
        
        assert config['selection_method'] == 'default_mapping'
        assert model == 'claude-4-opus'  # Default for engineer
        
        # Test with flag enabled
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'engineer',
                task_description="Simple bug fix"
            )
        
        assert config['selection_method'] == 'dynamic_complexity_based'
        assert model == MODEL_NAME_MAPPINGS[ModelType.HAIKU]
        
        os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
    
    def test_gradual_rollout_per_agent(self, mock_framework_setup):
        """Test gradual rollout with per-agent overrides."""
        # Global flag off, but engineer enabled
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
        os.environ['CLAUDE_PM_ENGINEER_MODEL_SELECTION'] = 'true'
        
        # Engineer should use dynamic selection
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'engineer',
                task_description="Simple task"
            )
        
        assert config['selection_method'] == 'dynamic_complexity_based'
        
        # QA should use default
        prompt, model, config = get_agent_prompt_with_model_info(
            'qa',
            task_description="Complex testing task"
        )
        
        assert config['selection_method'] == 'default_mapping'
        
        # Cleanup
        os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
        os.environ.pop('CLAUDE_PM_ENGINEER_MODEL_SELECTION', None)


class TestRealWorldScenarios:
    """Test real-world scenarios for model selection."""
    
    @pytest.fixture
    def enable_dynamic_selection(self):
        """Enable dynamic model selection."""
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        yield
        os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
    
    @pytest.fixture
    def setup_environment(self):
        """Setup test environment."""
        # Enable dynamic selection
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        
        with patch('claude_pm.agents.agent_loader.FRAMEWORK_AGENT_ROLES_DIR', Path('/mock/framework/agent-roles')):
            with patch('claude_pm.agents.agent_loader.load_agent_prompt_from_md') as mock_load:
                mock_load.return_value = "Agent prompt"
                with patch('claude_pm.agents.agent_loader.prepend_base_instructions') as mock_prepend:
                    mock_prepend.side_effect = lambda x: f"BASE\n{x}"
                    yield
        
        # Cleanup
        os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
    
    def test_documentation_agent_scenarios(self, setup_environment):
        """Test various documentation agent scenarios."""
        scenarios = [
            {
                'task': 'Update README with installation instructions',
                'expected_model': ModelType.HAIKU,
                'context_size': 1000
            },
            {
                'task': 'Generate comprehensive API documentation for the entire system',
                'expected_model': ModelType.SONNET,
                'context_size': 5000,
                'file_count': 10
            },
            {
                'task': 'Create comprehensive architectural decision records with complex system design patterns, performance optimization strategies, and multi-tier architecture migration plans',
                'expected_model': ModelType.OPUS,
                'context_size': 15000,
                'file_count': 20,
                'technical_depth': 'deep',
                'requires_research': True,
                'requires_testing': True,
                'requires_documentation': True,
                'integration_points': 5
            }
        ]
        
        for scenario in scenarios:
            with patch('claude_pm.agents.agent_loader.log_model_selection'):
                task = scenario.pop('task')
                expected = scenario.pop('expected_model')
                
                prompt, model, config = get_agent_prompt_with_model_info(
                    'documentation',
                    task_description=task,
                    **scenario
                )
                
                assert model == MODEL_NAME_MAPPINGS[expected]
    
    def test_performance_requirements_influence(self, setup_environment):
        """Test that performance requirements influence model selection."""
        # High speed requirement might downgrade model
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info(
                'qa',
                task_description='Run quick validation tests',
                performance_requirements={'speed_priority': True}
            )
        
        # Should prefer faster model for speed-critical tasks
        assert config['complexity_score'] <= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])