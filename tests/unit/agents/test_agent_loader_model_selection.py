#!/usr/bin/env python3
"""
Test suite for agent_loader.py model selection functionality.

Tests the integration of TaskComplexityAnalyzer with dynamic model selection.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from claude_pm.agents.agent_loader import (
    get_agent_prompt,
    get_agent_prompt_with_model_info,
    _analyze_task_complexity,
    _get_model_config,
    get_model_selection_metrics,
    log_model_selection,
    DEFAULT_AGENT_MODELS,
    MODEL_NAME_MAPPINGS
)
from claude_pm.services.task_complexity_analyzer import ComplexityLevel, ModelType


class TestAgentLoaderModelSelection:
    """Test model selection functionality in agent_loader."""
    
    @pytest.fixture
    def mock_prompt_content(self):
        """Mock agent prompt content."""
        return "This is a test agent prompt."
    
    @pytest.fixture
    def mock_load_agent_prompt(self, mock_prompt_content):
        """Mock the load_agent_prompt_from_md function."""
        with patch('claude_pm.agents.agent_loader.load_agent_prompt_from_md') as mock:
            mock.return_value = mock_prompt_content
            yield mock
    
    @pytest.fixture
    def mock_prepend_base(self):
        """Mock the prepend_base_instructions function."""
        with patch('claude_pm.agents.agent_loader.prepend_base_instructions') as mock:
            mock.side_effect = lambda x: f"BASE_INSTRUCTIONS\n{x}"
            yield mock
    
    @pytest.fixture
    def enable_dynamic_selection(self):
        """Enable dynamic model selection for tests."""
        original = os.environ.get('ENABLE_DYNAMIC_MODEL_SELECTION')
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        yield
        if original is None:
            os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
        else:
            os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = original
    
    def test_analyze_task_complexity_simple(self):
        """Test complexity analysis for simple tasks."""
        result = _analyze_task_complexity(
            task_description="List all files in the directory",
            context_size=500
        )
        
        assert 'complexity_score' in result
        assert 'complexity_level' in result
        assert 'recommended_model' in result
        assert result['complexity_score'] <= 30
        assert result['complexity_level'] == ComplexityLevel.SIMPLE
        assert result['recommended_model'] == ModelType.HAIKU
    
    def test_analyze_task_complexity_medium(self):
        """Test complexity analysis for medium tasks."""
        # Use a more complex task to ensure it hits medium complexity
        result = _analyze_task_complexity(
            task_description="Implement a comprehensive user authentication feature with JWT tokens and OAuth integration",
            context_size=5000,
            file_count=5,
            requires_testing=True,
            requires_documentation=True,
            integration_points=2
        )
        
        assert result['complexity_score'] > 30
        assert result['complexity_score'] <= 70
        assert result['complexity_level'] == ComplexityLevel.MEDIUM
        assert result['recommended_model'] == ModelType.SONNET
    
    def test_analyze_task_complexity_complex(self):
        """Test complexity analysis for complex tasks."""
        result = _analyze_task_complexity(
            task_description="Refactor the entire authentication system with advanced security patterns",
            context_size=10000,
            file_count=10,
            integration_points=3,
            requires_research=True,
            requires_testing=True,
            requires_documentation=True,
            technical_depth="deep"
        )
        
        assert result['complexity_score'] > 70
        assert result['complexity_level'] == ComplexityLevel.COMPLEX
        assert result['recommended_model'] == ModelType.OPUS
    
    def test_analyze_task_complexity_error_handling(self):
        """Test complexity analysis error handling."""
        with patch('claude_pm.agents.agent_loader.TaskComplexityAnalyzer') as mock_analyzer:
            mock_analyzer.side_effect = Exception("Analysis failed")
            
            result = _analyze_task_complexity("Test task")
            
            assert 'error' in result
            assert result['complexity_score'] == 50
            assert result['complexity_level'] == ComplexityLevel.MEDIUM
    
    def test_get_model_config_dynamic_enabled(self, enable_dynamic_selection):
        """Test model config with dynamic selection enabled."""
        complexity_analysis = {
            'complexity_score': 85,
            'complexity_level': ComplexityLevel.COMPLEX,
            'recommended_model': ModelType.OPUS,
            'optimal_prompt_size': (1200, 1500)
        }
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            selected_model, model_config = _get_model_config('engineer', complexity_analysis)
        
        assert selected_model == MODEL_NAME_MAPPINGS[ModelType.OPUS]
        assert model_config['selection_method'] == 'dynamic_complexity_based'
        assert model_config['complexity_score'] == 85
        assert model_config['complexity_level'] == 'COMPLEX'
    
    def test_get_model_config_dynamic_disabled(self):
        """Test model config with dynamic selection disabled."""
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
        
        try:
            complexity_analysis = {
                'complexity_score': 85,
                'complexity_level': ComplexityLevel.COMPLEX,
                'recommended_model': ModelType.OPUS
            }
            
            selected_model, model_config = _get_model_config('engineer', complexity_analysis)
            
            assert selected_model == DEFAULT_AGENT_MODELS['engineer']
            assert model_config['selection_method'] == 'default_mapping'
            assert model_config['reason'] == 'dynamic_selection_disabled'
        finally:
            os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
    
    def test_get_model_config_per_agent_override(self):
        """Test per-agent override for model selection."""
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
        os.environ['CLAUDE_PM_ENGINEER_MODEL_SELECTION'] = 'true'
        
        try:
            complexity_analysis = {
                'complexity_score': 25,
                'complexity_level': ComplexityLevel.SIMPLE,
                'recommended_model': ModelType.HAIKU
            }
            
            with patch('claude_pm.agents.agent_loader.log_model_selection'):
                selected_model, model_config = _get_model_config('engineer', complexity_analysis)
            
            assert selected_model == MODEL_NAME_MAPPINGS[ModelType.HAIKU]
            assert model_config['selection_method'] == 'dynamic_complexity_based'
        finally:
            os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
            os.environ.pop('CLAUDE_PM_ENGINEER_MODEL_SELECTION', None)
    
    def test_get_agent_prompt_with_complexity(self, mock_load_agent_prompt, mock_prepend_base, enable_dynamic_selection):
        """Test get_agent_prompt with task complexity analysis."""
        kwargs = {
            'task_description': 'Implement JWT authentication',
            'context_size': 2000,
            'file_count': 2,
            'requires_testing': True
        }
        
        # Use get_agent_prompt_with_model_info to get model selection details
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info('engineer', **kwargs)
        
        # Debug print
        print(f"Enable env var: {os.environ.get('ENABLE_DYNAMIC_MODEL_SELECTION')}")
        print(f"Model config: {config}")
        
        assert 'BASE_INSTRUCTIONS' in prompt
        assert model in MODEL_NAME_MAPPINGS.values() or model in DEFAULT_AGENT_MODELS.values()
        assert config.get('selection_method') == 'dynamic_complexity_based'
    
    def test_get_agent_prompt_without_task_description(self, mock_load_agent_prompt, mock_prepend_base):
        """Test get_agent_prompt without task description uses default model."""
        prompt = get_agent_prompt('documentation')
        
        assert 'BASE_INSTRUCTIONS' in prompt
        assert 'Model Selection:' not in prompt
    
    def test_get_agent_prompt_with_model_info(self, mock_load_agent_prompt, mock_prepend_base, enable_dynamic_selection):
        """Test get_agent_prompt_with_model_info function."""
        kwargs = {
            'task_description': 'Refactor authentication system',
            'context_size': 5000,
            'file_count': 8
        }
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt, model, config = get_agent_prompt_with_model_info('engineer', **kwargs)
        
        assert 'BASE_INSTRUCTIONS' in prompt
        assert model in MODEL_NAME_MAPPINGS.values() or model in DEFAULT_AGENT_MODELS.values()
        assert 'selection_method' in config
    
    def test_get_model_selection_metrics(self):
        """Test model selection metrics retrieval."""
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
        os.environ['CLAUDE_PM_QA_MODEL_SELECTION'] = 'false'
        
        try:
            with patch('claude_pm.agents.agent_loader.SharedPromptCache') as mock_cache:
                mock_instance = Mock()
                mock_instance.get.return_value = {
                    'total_selections': 10,
                    'by_model': {'claude-sonnet-4-20250514': 7, 'claude-4-opus': 3}
                }
                mock_cache.get_instance.return_value = mock_instance
                
                metrics = get_model_selection_metrics()
                
                assert metrics['feature_flag']['global_enabled'] is True
                assert 'qa' in metrics['feature_flag']['agent_overrides']
                assert metrics['feature_flag']['agent_overrides']['qa'] is False
                assert metrics['selection_stats']['total_selections'] == 10
        finally:
            os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)
            os.environ.pop('CLAUDE_PM_QA_MODEL_SELECTION', None)
    
    def test_log_model_selection(self):
        """Test model selection logging."""
        with patch('claude_pm.agents.agent_loader.SharedPromptCache') as mock_cache:
            mock_instance = Mock()
            mock_instance.get.return_value = {
                'total_selections': 0,
                'by_model': {},
                'by_agent': {},
                'by_method': {},
                'complexity_distribution': {
                    '0-30': 0,
                    '31-70': 0,
                    '71-100': 0
                }
            }
            mock_cache.get_instance.return_value = mock_instance
            
            log_model_selection(
                agent_name='engineer',
                selected_model='claude-4-opus',
                complexity_score=85,
                selection_method='dynamic_complexity_based'
            )
            
            # Verify set was called with updated stats
            mock_instance.set.assert_called_once()
            call_args = mock_instance.set.call_args
            
            # Check positional args if present, otherwise check keyword args
            if call_args[0]:
                stats_key = call_args[0][0]
                stats = call_args[0][1]
            else:
                stats_key = call_args[1]['stats_key'] if 'stats_key' in call_args[1] else call_args[1].get('key')
                stats = call_args[1]['stats'] if 'stats' in call_args[1] else call_args[1].get('value')
            
            assert 'agent_loader:model_selection_stats' in str(stats_key)
            assert stats['total_selections'] == 1
            assert stats['by_model']['claude-4-opus'] == 1
            assert stats['complexity_distribution']['71-100'] == 1
    
    def test_model_selection_with_metadata_in_prompt(self, mock_load_agent_prompt, mock_prepend_base, enable_dynamic_selection):
        """Test that model selection metadata is added to prompt when dynamic selection is used."""
        kwargs = {
            'task_description': 'Complex refactoring task',
            'context_size': 8000,
            'file_count': 10
        }
        
        with patch('claude_pm.agents.agent_loader.log_model_selection'):
            prompt = get_agent_prompt('engineer', **kwargs)
        
        # When dynamic selection is used, metadata should be in prompt
        assert 'Model Selection:' in prompt
        assert 'Complexity:' in prompt
    
    def test_complexity_analysis_disabled(self, mock_load_agent_prompt, mock_prepend_base):
        """Test disabling complexity analysis via kwargs."""
        # Temporarily disable dynamic selection to ensure predictable behavior
        old_env = os.environ.get('ENABLE_DYNAMIC_MODEL_SELECTION')
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
        
        try:
            kwargs = {
                'task_description': 'Test task',
                'enable_complexity_analysis': False
            }
            
            # Use get_agent_prompt_with_model_info to check model selection
            prompt, model, config = get_agent_prompt_with_model_info('engineer', **kwargs)
            
            # Should use default model when dynamic selection is disabled
            assert config['selection_method'] == 'default_mapping'
            assert config['reason'] == 'dynamic_selection_disabled'
        finally:
            # Restore original env var
            if old_env is not None:
                os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = old_env
            else:
                os.environ.pop('ENABLE_DYNAMIC_MODEL_SELECTION', None)


class TestBackwardCompatibility:
    """Test backward compatibility of agent loader functions."""
    
    @pytest.fixture
    def mock_get_agent_prompt(self):
        """Mock get_agent_prompt function."""
        with patch('claude_pm.agents.agent_loader.get_agent_prompt') as mock:
            mock.return_value = "Test agent prompt"
            yield mock
    
    def test_backward_compatible_functions(self, mock_get_agent_prompt):
        """Test that backward compatible functions still work."""
        from claude_pm.agents.agent_loader import (
            get_documentation_agent_prompt,
            get_version_control_agent_prompt,
            get_qa_agent_prompt,
            get_research_agent_prompt,
            get_ops_agent_prompt,
            get_security_agent_prompt,
            get_engineer_agent_prompt,
            get_data_engineer_agent_prompt
        )
        
        # Test each function
        funcs = [
            (get_documentation_agent_prompt, "documentation"),
            (get_version_control_agent_prompt, "version_control"),
            (get_qa_agent_prompt, "qa"),
            (get_research_agent_prompt, "research"),
            (get_ops_agent_prompt, "ops"),
            (get_security_agent_prompt, "security"),
            (get_engineer_agent_prompt, "engineer"),
            (get_data_engineer_agent_prompt, "data_engineer")
        ]
        
        for func, agent_name in funcs:
            result = func()
            assert result == "Test agent prompt"
            mock_get_agent_prompt.assert_called_with(agent_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])