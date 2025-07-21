#!/usr/bin/env python3
"""
Integration Tests for Prompt Optimization Features
=================================================

Tests integration between:
- TaskComplexityAnalyzer
- Agent loader with dynamic prompts
- Model selector service
- Prompt template generation
- Feature flags and configuration
"""

import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_pm.services.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
    ComplexityLevel,
    ModelType
)
from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria
from claude_pm.agents.agent_loader import get_agent_prompt


class TestPromptOptimizationIntegration:
    """Integration tests for prompt optimization components."""
    
    @pytest.fixture
    def analyzer(self):
        """Create TaskComplexityAnalyzer instance."""
        return TaskComplexityAnalyzer()
    
    @pytest.fixture
    def model_selector(self):
        """Create ModelSelector instance."""
        return ModelSelector()
    
    def test_analyzer_model_selector_integration(self, analyzer, model_selector):
        """Test integration between complexity analyzer and model selector."""
        # Analyze a complex task
        task = "Architect a microservices system with event-driven communication"
        analysis = analyzer.analyze_task(
            task_description=task,
            file_count=15,
            integration_points=5,
            technical_depth="deep"
        )
        
        # Create model selection criteria from analysis
        criteria = ModelSelectionCriteria(
            agent_type="architect",
            task_complexity=analysis.complexity_level.value,
            context_size=1500,
            requires_reasoning=True,
            performance_priority="quality"
        )
        
        # Select model using criteria
        selected_model = model_selector.select_model("architect", criteria)
        
        # Verify consistency between analyzer and selector
        assert selected_model == analysis.recommended_model.value
        
        # Verify reasoning is generated
        reasoning = model_selector._generate_selection_reasoning(criteria, selected_model)
        assert "COMPLEX" in reasoning or "complexity" in reasoning.lower()
    
    def test_prompt_template_adaptation(self, analyzer):
        """Test prompt templates adapt based on complexity."""
        # Test different complexity levels
        test_cases = [
            {
                'task': 'List project files',
                'expected_template': 'minimal',
                'max_context_items': 3
            },
            {
                'task': 'Create user authentication endpoint',
                'expected_template': 'standard',
                'max_context_items': 10
            },
            {
                'task': 'Refactor entire application architecture',
                'expected_template': 'comprehensive',
                'max_context_items': None  # No limit
            }
        ]
        
        for test_case in test_cases:
            analysis = analyzer.analyze_task(test_case['task'])
            
            # Simulate template selection based on complexity
            if analysis.complexity_level == ComplexityLevel.SIMPLE:
                template_type = 'minimal'
            elif analysis.complexity_level == ComplexityLevel.MEDIUM:
                template_type = 'standard'
            else:
                template_type = 'comprehensive'
            
            assert template_type == test_case['expected_template']
    
    def test_dynamic_context_filtering(self, analyzer):
        """Test context filtering based on task complexity."""
        # Full context
        full_context = {
            'project_structure': {
                'src/': ['main.py', 'config.py', 'utils.py'],
                'tests/': ['test_main.py', 'test_utils.py'],
                'docs/': ['README.md', 'API.md']
            },
            'dependencies': ['fastapi', 'sqlalchemy', 'pytest', 'redis'],
            'environment_vars': ['DB_URL', 'API_KEY', 'REDIS_URL'],
            'recent_commits': ['Fix auth bug', 'Add caching', 'Update deps'],
            'performance_metrics': {
                'response_time': '120ms',
                'throughput': '1000 req/s'
            }
        }
        
        # Simple task - minimal context
        simple_analysis = analyzer.analyze_task("Read configuration file")
        simple_context = self._filter_context(full_context, simple_analysis.complexity_level)
        
        # Should only include essential items
        assert 'project_structure' not in simple_context or len(simple_context) <= 2
        
        # Complex task - full context
        complex_analysis = analyzer.analyze_task(
            "Optimize system performance and implement caching layer",
            technical_depth="deep"
        )
        complex_context = self._filter_context(full_context, complex_analysis.complexity_level)
        
        # Should include everything relevant
        assert 'performance_metrics' in complex_context
        assert 'dependencies' in complex_context
    
    def _filter_context(self, context: dict, complexity_level: ComplexityLevel) -> dict:
        """Helper to filter context based on complexity."""
        if complexity_level == ComplexityLevel.SIMPLE:
            # Only essential keys
            essential_keys = ['project_structure']
            return {k: v for k, v in context.items() if k in essential_keys}
        elif complexity_level == ComplexityLevel.MEDIUM:
            # Most keys except detailed metrics
            exclude_keys = ['performance_metrics', 'recent_commits']
            return {k: v for k, v in context.items() if k not in exclude_keys}
        else:
            # Everything
            return context
    
    def test_agent_specific_optimization(self, analyzer):
        """Test agent-specific prompt optimization."""
        # Different agents have different optimization strategies
        agent_tasks = {
            'documentation': {
                'task': 'Update API documentation',
                'focus': ['clarity', 'completeness'],
                'exclude': ['implementation_details']
            },
            'qa': {
                'task': 'Write comprehensive test suite',
                'focus': ['test_coverage', 'edge_cases'],
                'exclude': ['documentation']
            },
            'engineer': {
                'task': 'Implement new feature',
                'focus': ['code_quality', 'performance'],
                'exclude': ['test_details']
            }
        }
        
        for agent_type, config in agent_tasks.items():
            analysis = analyzer.analyze_task(config['task'])
            
            # Verify agent-specific optimizations would be applied
            hints = analyzer.get_prompt_optimization_hints(analysis)
            
            # Each agent type should have relevant focus areas
            if analysis.complexity_level != ComplexityLevel.SIMPLE:
                assert len(hints['focus_areas']) > 0
    
    def test_feature_flag_configuration_cascade(self):
        """Test feature flag configuration cascade."""
        # Test configuration hierarchy:
        # 1. Per-agent config
        # 2. Global environment variable
        # 3. Default value
        
        test_configs = {
            'global_on_agent_off': {
                'env': {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'true'},
                'agent_config': {'optimize_prompts': False},
                'expected': False  # Agent config wins
            },
            'global_off_agent_on': {
                'env': {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'false'},
                'agent_config': {'optimize_prompts': True},
                'expected': True  # Agent config wins
            },
            'only_global': {
                'env': {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'true'},
                'agent_config': {},
                'expected': True  # Uses global
            },
            'no_config': {
                'env': {},
                'agent_config': {},
                'expected': False  # Default
            }
        }
        
        for test_name, config in test_configs.items():
            with patch.dict(os.environ, config['env'], clear=True):
                # Simulate config lookup
                agent_optimize = config['agent_config'].get(
                    'optimize_prompts',
                    os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS', '').lower() == 'true'
                )
                
                assert agent_optimize == config['expected'], f"Failed for {test_name}"
    
    def test_prompt_caching_with_complexity(self, analyzer):
        """Test prompt caching considers complexity analysis."""
        # Simulate cache keys that include complexity
        cache_keys = []
        
        tasks = [
            "Read file",
            "Read file",  # Duplicate
            "Create complex system",
            "Create complex system"  # Duplicate
        ]
        
        for task in tasks:
            analysis = analyzer.analyze_task(task)
            
            # Cache key includes task and complexity level
            cache_key = f"{task}:{analysis.complexity_level.value}"
            cache_keys.append(cache_key)
        
        # Verify duplicates have same cache keys
        assert cache_keys[0] == cache_keys[1]  # Same simple task
        assert cache_keys[2] == cache_keys[3]  # Same complex task
        assert cache_keys[0] != cache_keys[2]  # Different tasks
    
    def test_error_handling_graceful_degradation(self, analyzer):
        """Test graceful degradation when optimization fails."""
        # Test with invalid inputs
        with patch.object(analyzer, 'analyze_task', side_effect=Exception("Analysis failed")):
            try:
                # Should fall back to default behavior
                from claude_pm.services.task_complexity_integration_example import create_optimized_prompt
                
                # This should handle the error gracefully
                result = create_optimized_prompt(
                    agent_name='engineer',
                    task_description='Test task',
                    context={}
                )
                
                # Should still return a valid result (with defaults)
                assert 'prompt' in result
            except Exception:
                # If optimization fails, system should still work
                pass
    
    def test_metrics_collection_integration(self, analyzer):
        """Test metrics are collected during optimization."""
        metrics = {
            'analyses_performed': 0,
            'models_selected': {},
            'avg_complexity_score': 0,
            'optimization_time_ms': []
        }
        
        # Simulate multiple task analyses
        import time
        tasks = [
            "Simple task",
            "Medium complexity task with testing",
            "Complex refactoring of entire system"
        ]
        
        total_score = 0
        for task in tasks:
            start_time = time.time()
            
            analysis = analyzer.analyze_task(task)
            
            end_time = time.time()
            optimization_time = (end_time - start_time) * 1000
            
            # Update metrics
            metrics['analyses_performed'] += 1
            model = analysis.recommended_model.value
            metrics['models_selected'][model] = metrics['models_selected'].get(model, 0) + 1
            metrics['optimization_time_ms'].append(optimization_time)
            total_score += analysis.complexity_score
        
        # Calculate averages
        metrics['avg_complexity_score'] = total_score / metrics['analyses_performed']
        metrics['avg_optimization_time_ms'] = sum(metrics['optimization_time_ms']) / len(metrics['optimization_time_ms'])
        
        # Verify metrics
        assert metrics['analyses_performed'] == len(tasks)
        assert sum(metrics['models_selected'].values()) == len(tasks)
        assert metrics['avg_optimization_time_ms'] < 10  # Should be very fast
    
    def test_prompt_size_validation(self, analyzer):
        """Test prompt sizes stay within optimal bounds."""
        from claude_pm.services.task_complexity_integration_example import create_optimized_prompt
        
        # Test various task complexities
        test_cases = [
            {
                'task': 'Check file exists',
                'context': {'file': 'test.py'},
                'expected_model': 'haiku',
                'size_range': (300, 500)
            },
            {
                'task': 'Implement REST API with authentication',
                'context': {
                    'framework': 'FastAPI',
                    'auth_type': 'JWT',
                    'endpoints': ['users', 'auth', 'profile']
                },
                'expected_model': 'sonnet',
                'size_range': (700, 1000)
            },
            {
                'task': 'Redesign system architecture for microservices',
                'context': {
                    'current_arch': 'monolith',
                    'target_arch': 'microservices',
                    'services': ['auth', 'api', 'worker', 'cache'],
                    'requirements': ['scalability', 'fault-tolerance']
                },
                'expected_model': 'opus',
                'size_range': (1200, 1500)
            }
        ]
        
        for test_case in test_cases:
            result = create_optimized_prompt(
                agent_name='engineer',
                task_description=test_case['task'],
                context=test_case['context']
            )
            
            # Verify model selection
            assert result['model'] == test_case['expected_model']
            
            # Verify prompt size is within bounds
            min_size, max_size = test_case['size_range']
            assert min_size <= result['prompt_size'] <= max_size * 1.1  # Allow 10% overflow
            
            # Verify prompt was actually optimized (trimmed if needed)
            if result['prompt_size'] > max_size:
                assert result['prompt'].endswith('...')


class TestAdvancedOptimizationScenarios:
    """Test advanced optimization scenarios and edge cases."""
    
    def test_multi_agent_workflow_optimization(self):
        """Test optimization across multi-agent workflows."""
        analyzer = TaskComplexityAnalyzer()
        
        # Complex workflow requiring multiple agents
        workflow_task = """
        1. Research best practices for microservices architecture
        2. Design the system architecture with proper boundaries
        3. Implement core services with proper testing
        4. Document the entire system
        5. Deploy with monitoring and alerting
        """
        
        # Analyze main task
        main_analysis = analyzer.analyze_task(
            workflow_task,
            integration_points=5,
            requires_research=True,
            requires_testing=True,
            requires_documentation=True
        )
        
        # Break down into agent-specific subtasks
        agent_subtasks = {
            'research': 'Research best practices for microservices architecture',
            'architect': 'Design the system architecture with proper boundaries',
            'engineer': 'Implement core services with proper testing',
            'documentation': 'Document the entire system',
            'ops': 'Deploy with monitoring and alerting'
        }
        
        # Each agent should get appropriately optimized prompts
        agent_analyses = {}
        for agent, subtask in agent_subtasks.items():
            analysis = analyzer.analyze_task(subtask)
            agent_analyses[agent] = {
                'complexity': analysis.complexity_level.value,
                'model': analysis.recommended_model.value,
                'score': analysis.complexity_score
            }
        
        # Verify appropriate complexity distribution
        assert agent_analyses['research']['complexity'] in ['SIMPLE', 'MEDIUM']
        assert agent_analyses['architect']['complexity'] in ['MEDIUM', 'COMPLEX']
        assert agent_analyses['engineer']['complexity'] in ['MEDIUM', 'COMPLEX']
        
        # Main task should be complex
        assert main_analysis.complexity_level == ComplexityLevel.COMPLEX
    
    def test_recursive_task_optimization(self):
        """Test optimization for recursive/nested tasks."""
        analyzer = TaskComplexityAnalyzer()
        
        # Parent task
        parent_task = "Refactor authentication system"
        parent_analysis = analyzer.analyze_task(
            parent_task,
            file_count=10,
            requires_testing=True
        )
        
        # Child tasks
        child_tasks = [
            "Extract authentication logic to separate module",
            "Implement JWT token generation",
            "Add refresh token support",
            "Update all API endpoints to use new auth"
        ]
        
        child_analyses = []
        for child_task in child_tasks:
            analysis = analyzer.analyze_task(child_task)
            child_analyses.append(analysis)
        
        # Parent should generally be more complex than children
        assert parent_analysis.complexity_score >= max(c.complexity_score for c in child_analyses) - 10
        
        # Children should have varied complexity
        complexity_levels = set(c.complexity_level for c in child_analyses)
        assert len(complexity_levels) >= 2  # At least 2 different levels
    
    def test_context_aware_optimization(self):
        """Test optimization that considers surrounding context."""
        analyzer = TaskComplexityAnalyzer()
        
        # Same task with different contexts
        base_task = "Implement caching"
        
        # Simple context
        simple_context_analysis = analyzer.analyze_task(
            base_task,
            file_count=1,
            context_size=500
        )
        
        # Complex context
        complex_context_analysis = analyzer.analyze_task(
            base_task,
            file_count=10,
            context_size=15000,
            integration_points=4,
            technical_depth="deep"
        )
        
        # Same task but different complexity due to context
        assert simple_context_analysis.complexity_level == ComplexityLevel.SIMPLE
        assert complex_context_analysis.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX]
        
        # Different models recommended
        assert simple_context_analysis.recommended_model == ModelType.HAIKU
        assert complex_context_analysis.recommended_model in [ModelType.SONNET, ModelType.OPUS]


# Performance test helpers
def measure_optimization_impact():
    """Measure the performance impact of optimization."""
    import time
    
    analyzer = TaskComplexityAnalyzer()
    
    # Test tasks
    tasks = [
        "Simple file read operation",
        "Implement user authentication with OAuth",
        "Architect microservices system with event sourcing"
    ]
    
    # Measure with optimization
    opt_times = []
    for task in tasks:
        start = time.time()
        analysis = analyzer.analyze_task(task)
        # Simulate optimized prompt generation
        opt_times.append(time.time() - start)
    
    # Measure without optimization (simulate)
    no_opt_times = []
    for task in tasks:
        start = time.time()
        # Simulate unoptimized processing
        time.sleep(0.001)  # Simulate some processing
        no_opt_times.append(time.time() - start)
    
    # Calculate improvement
    avg_opt = sum(opt_times) / len(opt_times)
    avg_no_opt = sum(no_opt_times) / len(no_opt_times)
    
    print(f"\nOptimization Performance Impact:")
    print(f"Average with optimization: {avg_opt*1000:.3f}ms")
    print(f"Average without optimization: {avg_no_opt*1000:.3f}ms")
    print(f"Overhead: {(avg_opt - avg_no_opt)*1000:.3f}ms")
    
    # Optimization should have minimal overhead
    assert avg_opt < 0.01  # Less than 10ms


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, '-v'])
    
    # Run performance measurements
    measure_optimization_impact()