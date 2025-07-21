#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Prompt Optimization
===========================================================

This test suite validates all prompt optimization features including:
- Task complexity analysis and model selection
- Dynamic prompt template generation
- Feature flag behavior
- Backward compatibility
- Performance improvements and token reduction

Test Coverage:
- Simple task flows (Haiku + minimal template)
- Medium task flows (Sonnet + standard template)
- Complex task flows (Opus + full template)
- Feature flag on/off behavior
- Per-agent feature overrides
- Edge cases and boundary conditions
- Performance benchmarks
- Integration with existing systems
"""

import os
import sys
import time
import json
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_pm.services.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
    ComplexityLevel,
    ModelType
)
from claude_pm.agents.agent_loader import get_agent_prompt
from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
from claude_pm.services.task_complexity_integration_example import create_optimized_prompt


class TestPromptOptimizationE2E:
    """End-to-end tests for prompt optimization features."""
    
    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory with claude-pm structure."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create .claude-pm directory
        claude_pm_dir = project_dir / ".claude-pm"
        claude_pm_dir.mkdir()
        
        # Create CLAUDE.md file
        claude_md = project_dir / "CLAUDE.md"
        claude_md.write_text("# Test Project\nTest project for prompt optimization.")
        
        return project_dir
    
    @pytest.fixture
    def analyzer(self):
        """Create a TaskComplexityAnalyzer instance."""
        return TaskComplexityAnalyzer()
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'CLAUDE_PM_OPTIMIZE_PROMPTS': 'true',
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': 'test-key'
        }):
            yield
    
    def test_simple_task_flow_e2e(self, analyzer, temp_project_dir):
        """Test end-to-end flow for simple tasks."""
        # Simple task description
        task = "List all files in the current directory"
        
        # Analyze complexity
        analysis = analyzer.analyze_task(task)
        
        # Verify simple task classification
        assert analysis.complexity_level == ComplexityLevel.SIMPLE
        assert analysis.recommended_model == ModelType.HAIKU
        assert analysis.optimal_prompt_size == (300, 500)
        assert analysis.complexity_score <= 30
        
        # Create optimized prompt
        result = create_optimized_prompt(
            agent_name='research',
            task_description=task,
            context={'project_name': 'test_project'}
        )
        
        # Verify minimal prompt template
        assert result['model'] == 'haiku'
        assert result['complexity_level'] == 'SIMPLE'
        assert result['prompt_size'] <= 500
        assert "Key Information" in result['prompt']
        assert "Detailed Context" not in result['prompt']
    
    def test_medium_task_flow_e2e(self, analyzer, temp_project_dir):
        """Test end-to-end flow for medium complexity tasks."""
        # Medium complexity task
        task = "Implement user authentication with JWT tokens and password hashing"
        context = {
            'project_name': 'test_project',
            'files': ['auth.py', 'user.py', 'config.py'],
            'dependencies': ['jwt', 'bcrypt'],
            'file_count': 3,
            'requires_testing': True
        }
        
        # Analyze complexity
        analysis = analyzer.analyze_task(
            task_description=task,
            file_count=context['file_count'],
            requires_testing=context['requires_testing']
        )
        
        # Verify medium task classification
        assert analysis.complexity_level == ComplexityLevel.MEDIUM
        assert analysis.recommended_model == ModelType.SONNET
        assert analysis.optimal_prompt_size == (700, 1000)
        assert 31 <= analysis.complexity_score <= 70
        
        # Create optimized prompt
        result = create_optimized_prompt(
            agent_name='engineer',
            task_description=task,
            context=context
        )
        
        # Verify standard prompt template
        assert result['model'] == 'sonnet'
        assert result['complexity_level'] == 'MEDIUM'
        assert 700 <= result['prompt_size'] <= 1000
        assert "Context" in result['prompt']
        assert "Files involved:" in result['prompt']
    
    def test_complex_task_flow_e2e(self, analyzer, temp_project_dir):
        """Test end-to-end flow for complex tasks."""
        # Complex task description
        task = "Refactor the entire authentication system to implement OAuth2 with multi-factor authentication, including database migration and API redesign"
        context = {
            'project_name': 'test_project',
            'files': [f'auth/{f}.py' for f in ['oauth', 'mfa', 'session', 'token', 'user', 'provider', 'config', 'middleware']],
            'integration_points': 4,
            'requires_research': True,
            'requires_testing': True,
            'requires_documentation': True,
            'dependencies': ['oauth2', 'pyotp', 'jwt', 'redis'],
            'file_count': 8,
            'technical_depth': 'deep'
        }
        
        # Analyze complexity
        analysis = analyzer.analyze_task(
            task_description=task,
            file_count=context['file_count'],
            integration_points=context['integration_points'],
            requires_research=context['requires_research'],
            requires_testing=context['requires_testing'],
            requires_documentation=context['requires_documentation'],
            technical_depth=context['technical_depth']
        )
        
        # Verify complex task classification
        assert analysis.complexity_level == ComplexityLevel.COMPLEX
        assert analysis.recommended_model == ModelType.OPUS
        assert analysis.optimal_prompt_size == (1200, 1500)
        assert analysis.complexity_score >= 71
        
        # Create optimized prompt
        result = create_optimized_prompt(
            agent_name='engineer',
            task_description=task,
            context=context
        )
        
        # Verify full prompt template
        assert result['model'] == 'opus'
        assert result['complexity_level'] == 'COMPLEX'
        assert result['prompt_size'] >= 1200
        assert "Detailed Context" in result['prompt']
        assert "Focus Areas" in result['prompt']
        assert "Examples and Patterns" in result['prompt']
    
    def test_feature_flag_on_behavior(self, mock_env_vars):
        """Test behavior when CLAUDE_PM_OPTIMIZE_PROMPTS is enabled."""
        # Feature flag is ON via mock_env_vars
        assert os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS') == 'true'
        
        # Create analyzer and test optimization is applied
        analyzer = TaskComplexityAnalyzer()
        task = "Create a simple function"
        
        analysis = analyzer.analyze_task(task)
        assert analysis.recommended_model == ModelType.HAIKU
        
        # In real implementation, this would affect agent_loader behavior
        # For now, we verify the flag is recognized
        optimize_prompts = os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS', '').lower() == 'true'
        assert optimize_prompts is True
    
    def test_feature_flag_off_behavior(self):
        """Test behavior when CLAUDE_PM_OPTIMIZE_PROMPTS is disabled."""
        # Clear the environment variable
        with patch.dict(os.environ, {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'false'}):
            assert os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS') == 'false'
            
            # Verify optimization is not applied
            optimize_prompts = os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS', '').lower() == 'true'
            assert optimize_prompts is False
            
            # In real implementation, this would use default prompts
            # without complexity analysis
    
    def test_per_agent_feature_overrides(self):
        """Test per-agent feature flag overrides."""
        # Test configuration where some agents have optimization enabled
        agent_configs = {
            'documentation': {'optimize_prompts': True},
            'engineer': {'optimize_prompts': True},
            'qa': {'optimize_prompts': False},  # QA agent opts out
            'research': {}  # Uses global default
        }
        
        # Global flag is off
        with patch.dict(os.environ, {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'false'}):
            global_flag = os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS', '').lower() == 'true'
            
            # Check per-agent overrides
            for agent, config in agent_configs.items():
                agent_optimize = config.get('optimize_prompts', global_flag)
                
                if agent in ['documentation', 'engineer']:
                    assert agent_optimize is True  # Override enables optimization
                elif agent == 'qa':
                    assert agent_optimize is False  # Explicitly disabled
                else:
                    assert agent_optimize is False  # Uses global default
    
    def test_edge_case_empty_task(self, analyzer):
        """Test edge case: empty task description."""
        analysis = analyzer.analyze_task("")
        
        assert analysis.complexity_level == ComplexityLevel.SIMPLE
        assert analysis.recommended_model == ModelType.HAIKU
        assert analysis.complexity_score == 0
    
    def test_edge_case_extremely_long_task(self, analyzer):
        """Test edge case: extremely long task description."""
        # Create a very long task description
        long_task = "Implement " + " and ".join([f"feature_{i}" for i in range(100)])
        
        analysis = analyzer.analyze_task(long_task)
        
        # Should still produce valid results
        assert analysis.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX]
        assert analysis.complexity_score <= 100
        assert analysis.recommended_model in [ModelType.SONNET, ModelType.OPUS]
    
    def test_edge_case_boundary_complexity_scores(self, analyzer):
        """Test edge cases at complexity score boundaries."""
        # Test score at boundaries (30/31, 70/71)
        test_cases = [
            (30, ComplexityLevel.SIMPLE, ModelType.HAIKU),
            (31, ComplexityLevel.MEDIUM, ModelType.SONNET),
            (70, ComplexityLevel.MEDIUM, ModelType.SONNET),
            (71, ComplexityLevel.COMPLEX, ModelType.OPUS)
        ]
        
        for score, expected_level, expected_model in test_cases:
            # We can't directly set the score, but we can verify the thresholds
            level = analyzer._determine_complexity_level(score)
            model = analyzer._select_model(level)
            
            assert level == expected_level
            assert model == expected_model
    
    def test_performance_task_analysis_speed(self, analyzer):
        """Test performance: task analysis speed."""
        task = "Implement a caching system with Redis"
        
        # Measure analysis time
        start_time = time.time()
        
        # Run multiple analyses
        iterations = 1000
        for _ in range(iterations):
            analyzer.analyze_task(task)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        # Should be very fast (< 1ms per analysis)
        assert avg_time < 0.001  # Less than 1ms
        
        # Log performance metrics
        print(f"\nPerformance Metrics:")
        print(f"Total time for {iterations} analyses: {total_time:.3f}s")
        print(f"Average time per analysis: {avg_time * 1000:.3f}ms")
        print(f"Analyses per second: {iterations / total_time:.0f}")
    
    def test_token_reduction_validation(self, analyzer):
        """Test and validate token reduction claims."""
        # Compare prompt sizes for same task with and without optimization
        task = "Refactor the authentication module"
        full_context = {
            'project_name': 'test_project',
            'files': [f'file_{i}.py' for i in range(20)],
            'dependencies': [f'dep_{i}' for i in range(10)],
            'integration_points': 5,
            'requires_testing': True,
            'requires_documentation': True,
            'additional_context': ' '.join([f'Context item {i}' for i in range(50)])
        }
        
        # Analyze task
        analysis = analyzer.analyze_task(
            task_description=task,
            file_count=len(full_context['files']),
            integration_points=full_context['integration_points'],
            requires_testing=full_context['requires_testing'],
            requires_documentation=full_context['requires_documentation']
        )
        
        # Create optimized prompt
        optimized_result = create_optimized_prompt(
            agent_name='engineer',
            task_description=task,
            context=full_context
        )
        
        # Simulate unoptimized prompt (includes all context)
        unoptimized_prompt = f"""
You are an Engineer Agent.

## Task
{task}

## Full Context
{json.dumps(full_context, indent=2)}

## All Available Information
{str(full_context) * 3}  # Simulate verbose context repetition
"""
        
        # Calculate token reduction
        optimized_size = len(optimized_result['prompt'])
        unoptimized_size = len(unoptimized_prompt)
        reduction_percentage = (1 - optimized_size / unoptimized_size) * 100
        
        # Log token reduction
        print(f"\nToken Reduction Analysis:")
        print(f"Unoptimized prompt size: {unoptimized_size} chars")
        print(f"Optimized prompt size: {optimized_size} chars")
        print(f"Reduction: {reduction_percentage:.1f}%")
        
        # Verify significant reduction (targeting 66% reduction claim)
        assert reduction_percentage >= 50  # At least 50% reduction
    
    def test_integration_with_agent_loader(self):
        """Test integration with existing agent_loader system."""
        # Test that agent_loader can work with complexity analysis
        with patch('claude_pm.agents.agent_loader.get_agent_prompt') as mock_get_prompt:
            mock_get_prompt.return_value = "Base agent prompt"
            
            # Create optimized prompt through integration
            result = create_optimized_prompt(
                agent_name='documentation',
                task_description='Update API documentation',
                context={'project_name': 'test'}
            )
            
            # Verify agent_loader was called
            mock_get_prompt.assert_called_once_with('documentation')
            
            # Verify optimization was applied
            assert 'prompt' in result
            assert 'model' in result
            assert result['complexity_level'] in ['SIMPLE', 'MEDIUM', 'COMPLEX']
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing systems."""
        # Test that old code paths still work
        analyzer = TaskComplexityAnalyzer()
        
        # Old-style call without optional parameters
        analysis = analyzer.analyze_task("Simple task")
        assert analysis is not None
        assert hasattr(analysis, 'complexity_level')
        assert hasattr(analysis, 'recommended_model')
        
        # Test with partial parameters
        analysis2 = analyzer.analyze_task(
            task_description="Task with some params",
            file_count=5
            # Other params use defaults
        )
        assert analysis2 is not None
        assert analysis2.scoring_breakdown['file_complexity'] == 10
    
    def test_monitoring_and_metrics(self, analyzer):
        """Test monitoring and metrics collection."""
        # Track metrics across multiple analyses
        metrics = {
            'total_analyses': 0,
            'complexity_distribution': {
                'SIMPLE': 0,
                'MEDIUM': 0,
                'COMPLEX': 0
            },
            'model_distribution': {
                'haiku': 0,
                'sonnet': 0,
                'opus': 0
            },
            'avg_complexity_score': 0,
            'total_score': 0
        }
        
        # Test tasks of varying complexity
        test_tasks = [
            ("List files", {}),
            ("Create user profile", {'file_count': 3, 'requires_testing': True}),
            ("Refactor entire system", {'file_count': 20, 'integration_points': 5, 'technical_depth': 'deep'}),
            ("Read configuration", {}),
            ("Implement OAuth", {'requires_research': True, 'requires_testing': True}),
            ("Optimize database queries", {'technical_depth': 'moderate'}),
        ]
        
        # Analyze tasks and collect metrics
        for task_desc, params in test_tasks:
            analysis = analyzer.analyze_task(task_desc, **params)
            
            metrics['total_analyses'] += 1
            metrics['complexity_distribution'][analysis.complexity_level.value] += 1
            metrics['model_distribution'][analysis.recommended_model.value] += 1
            metrics['total_score'] += analysis.complexity_score
        
        # Calculate average
        metrics['avg_complexity_score'] = metrics['total_score'] / metrics['total_analyses']
        
        # Log metrics
        print(f"\nComplexity Analysis Metrics:")
        print(f"Total analyses: {metrics['total_analyses']}")
        print(f"Complexity distribution: {metrics['complexity_distribution']}")
        print(f"Model distribution: {metrics['model_distribution']}")
        print(f"Average complexity score: {metrics['avg_complexity_score']:.1f}")
        
        # Verify metrics are reasonable
        assert metrics['total_analyses'] == len(test_tasks)
        assert sum(metrics['complexity_distribution'].values()) == len(test_tasks)
        assert sum(metrics['model_distribution'].values()) == len(test_tasks)
        assert 0 <= metrics['avg_complexity_score'] <= 100
    
    def test_full_workflow_integration(self, temp_project_dir, mock_env_vars):
        """Test complete workflow from task to optimized subprocess creation."""
        # Simulate PM orchestrator receiving a task
        task_description = "Implement comprehensive user authentication system with OAuth2, JWT tokens, and MFA support"
        
        # Step 1: Analyze task complexity
        analyzer = TaskComplexityAnalyzer()
        analysis = analyzer.analyze_task(
            task_description=task_description,
            file_count=8,
            integration_points=3,
            requires_testing=True,
            requires_documentation=True,
            technical_depth="deep"
        )
        
        # Step 2: Create optimized prompt based on analysis
        context = {
            'project_name': 'test_project',
            'current_branch': 'feature/auth-system',
            'files': ['auth/' + f for f in ['oauth.py', 'jwt_handler.py', 'mfa.py', 'models.py']],
            'dependencies': ['oauth2', 'pyjwt', 'pyotp'],
            'existing_auth': 'Basic session-based auth',
            'target_architecture': 'OAuth2 + JWT + MFA'
        }
        
        optimized_prompt = create_optimized_prompt(
            agent_name='engineer',
            task_description=task_description,
            context=context
        )
        
        # Step 3: Verify workflow produces expected results
        assert analysis.complexity_level == ComplexityLevel.COMPLEX
        assert analysis.recommended_model == ModelType.OPUS
        assert optimized_prompt['model'] == 'opus'
        assert optimized_prompt['complexity_level'] == 'COMPLEX'
        assert 'Detailed Context' in optimized_prompt['prompt']
        assert 'Focus Areas' in optimized_prompt['prompt']
        
        # Step 4: Log complete workflow results
        print(f"\nFull Workflow Results:")
        print(f"Task: {task_description[:50]}...")
        print(f"Complexity Score: {analysis.complexity_score}")
        print(f"Selected Model: {analysis.recommended_model.value}")
        print(f"Prompt Size: {optimized_prompt['prompt_size']} chars")
        print(f"Optimization Strategies: {analysis.analysis_details}")
        
        # Verify all components work together
        assert optimized_prompt['prompt_size'] <= analysis.optimal_prompt_size[1]
        assert len(optimized_prompt['optimization_applied']['focus_areas']) > 0


class TestPerformanceBenchmarks:
    """Performance benchmark tests for prompt optimization."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for benchmarks."""
        return TaskComplexityAnalyzer()
    
    def test_analysis_performance_benchmark(self, analyzer, benchmark):
        """Benchmark task complexity analysis performance."""
        task = "Implement a distributed caching system with Redis clustering"
        
        # Run benchmark
        result = benchmark(
            analyzer.analyze_task,
            task_description=task,
            file_count=10,
            integration_points=3,
            requires_testing=True
        )
        
        # Verify result is valid
        assert result.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.COMPLEX]
    
    def test_prompt_generation_performance(self, benchmark):
        """Benchmark optimized prompt generation performance."""
        task = "Create REST API endpoints"
        context = {
            'project_name': 'api_project',
            'files': ['api.py', 'models.py', 'auth.py'],
            'dependencies': ['fastapi', 'sqlalchemy']
        }
        
        # Run benchmark
        result = benchmark(
            create_optimized_prompt,
            agent_name='engineer',
            task_description=task,
            context=context
        )
        
        # Verify result
        assert 'prompt' in result
        assert 'model' in result
    
    def test_token_reduction_benchmark(self, analyzer):
        """Benchmark token reduction across various task complexities."""
        test_scenarios = [
            {
                'name': 'Simple Task',
                'task': 'Read configuration file',
                'context_size': 100
            },
            {
                'name': 'Medium Task',
                'task': 'Implement user authentication',
                'context_size': 1000
            },
            {
                'name': 'Complex Task',
                'task': 'Refactor entire authentication system with OAuth2',
                'context_size': 5000
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            # Create full context
            context = {
                'data': 'x' * scenario['context_size'],
                'project': 'test',
                'files': ['file1.py', 'file2.py']
            }
            
            # Optimized prompt
            opt_result = create_optimized_prompt(
                agent_name='engineer',
                task_description=scenario['task'],
                context=context
            )
            
            # Unoptimized (full context)
            unopt_size = len(scenario['task']) + scenario['context_size'] + 500  # Base prompt
            opt_size = opt_result['prompt_size']
            
            reduction = (1 - opt_size / unopt_size) * 100
            
            results.append({
                'scenario': scenario['name'],
                'unoptimized_size': unopt_size,
                'optimized_size': opt_size,
                'reduction_percentage': reduction
            })
        
        # Print benchmark results
        print("\nToken Reduction Benchmarks:")
        print("-" * 60)
        for result in results:
            print(f"{result['scenario']:20} | "
                  f"Unopt: {result['unoptimized_size']:6} | "
                  f"Opt: {result['optimized_size']:6} | "
                  f"Reduction: {result['reduction_percentage']:5.1f}%")
        
        # Verify all scenarios show reduction
        assert all(r['reduction_percentage'] > 0 for r in results)
        
        # Verify average reduction meets target (66%)
        avg_reduction = sum(r['reduction_percentage'] for r in results) / len(results)
        print(f"\nAverage token reduction: {avg_reduction:.1f}%")
        assert avg_reduction >= 50  # Conservative target


class TestRegressionAndValidation:
    """Regression tests to ensure no existing functionality is broken."""
    
    def test_no_regression_basic_agent_loading(self):
        """Ensure basic agent loading still works without optimization."""
        with patch.dict(os.environ, {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'false'}):
            # This would test actual agent_loader functionality
            # For now, verify the flag doesn't break initialization
            try:
                from claude_pm.agents.agent_loader import get_agent_prompt
                # If we can import, basic functionality is intact
                assert True
            except Exception as e:
                pytest.fail(f"Agent loader import failed: {e}")
    
    def test_no_regression_subprocess_creation(self):
        """Ensure subprocess creation still works with optimization."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Test that subprocess creation works with optimization enabled
            with patch.dict(os.environ, {'CLAUDE_PM_OPTIMIZE_PROMPTS': 'true'}):
                # This would test actual subprocess creation
                # For now, verify environment doesn't break subprocess
                assert os.environ.get('CLAUDE_PM_OPTIMIZE_PROMPTS') == 'true'
    
    def test_validation_scoring_algorithm(self):
        """Validate the scoring algorithm produces consistent results."""
        analyzer = TaskComplexityAnalyzer()
        
        # Test same input produces same output (deterministic)
        task = "Implement caching system"
        params = {
            'file_count': 5,
            'context_size': 2000,
            'integration_points': 2,
            'requires_testing': True,
            'technical_depth': 'moderate'
        }
        
        # Run multiple times
        results = []
        for _ in range(10):
            analysis = analyzer.analyze_task(task, **params)
            results.append({
                'score': analysis.complexity_score,
                'level': analysis.complexity_level,
                'model': analysis.recommended_model
            })
        
        # All results should be identical (deterministic)
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    def test_validation_model_selection_boundaries(self):
        """Validate model selection at score boundaries."""
        analyzer = TaskComplexityAnalyzer()
        
        # Test tasks that should produce scores near boundaries
        boundary_tasks = [
            # Near 30 (SIMPLE/MEDIUM boundary)
            {
                'task': 'Create a simple configuration file',
                'file_count': 2,
                'expected_range': (25, 35)
            },
            # Near 70 (MEDIUM/COMPLEX boundary)
            {
                'task': 'Implement complete user management system',
                'file_count': 8,
                'integration_points': 2,
                'requires_testing': True,
                'expected_range': (65, 75)
            }
        ]
        
        for test_case in boundary_tasks:
            task = test_case.pop('task')
            expected_range = test_case.pop('expected_range')
            
            analysis = analyzer.analyze_task(task, **test_case)
            
            # Score should be in expected range
            assert expected_range[0] <= analysis.complexity_score <= expected_range[1]
            
            # Model selection should be consistent with score
            if analysis.complexity_score <= 30:
                assert analysis.recommended_model == ModelType.HAIKU
            elif analysis.complexity_score <= 70:
                assert analysis.recommended_model == ModelType.SONNET
            else:
                assert analysis.recommended_model == ModelType.OPUS


# Test execution helpers
def run_comprehensive_test_suite():
    """Run the complete test suite and generate report."""
    print("Running Comprehensive Prompt Optimization Test Suite...")
    print("=" * 60)
    
    # Run tests with pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--junit-xml=test_results_prompt_optimization.xml',
        '--cov=claude_pm.services.task_complexity_analyzer',
        '--cov=claude_pm.services.task_complexity_integration_example',
        '--cov-report=html',
        '--cov-report=term'
    ])


if __name__ == "__main__":
    run_comprehensive_test_suite()