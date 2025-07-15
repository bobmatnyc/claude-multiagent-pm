"""
Prompt Validation and Testing Framework

This module provides comprehensive validation and testing capabilities for
prompt improvements including A/B testing, effectiveness measurement, and
quality assurance.

Key Features:
- A/B testing framework for prompt comparison
- Effectiveness measurement and metrics
- Quality assurance validation
- Performance benchmarking
- Regression testing
- Automated test scenario generation

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import random
import time
import hashlib
from pathlib import Path
import concurrent.futures
from contextlib import asynccontextmanager


class TestType(Enum):
    """Types of validation tests"""
    AB_TEST = "ab_test"
    REGRESSION_TEST = "regression_test"
    PERFORMANCE_TEST = "performance_test"
    QUALITY_TEST = "quality_test"
    INTEGRATION_TEST = "integration_test"
    STRESS_TEST = "stress_test"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TestScenario:
    """Test scenario definition"""
    scenario_id: str
    name: str
    description: str
    agent_type: str
    task_description: str
    expected_outputs: List[str]
    evaluation_criteria: Dict[str, Any]
    test_data: Dict[str, Any]
    timeout: int = 300  # seconds
    retry_count: int = 3


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    scenario_id: str
    prompt_version: str
    execution_time: float
    success: bool
    score: float
    outputs: Dict[str, Any]
    errors: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime


@dataclass
class ABTestResult:
    """A/B test comparison result"""
    test_id: str
    prompt_a_id: str
    prompt_b_id: str
    scenarios_tested: int
    prompt_a_results: List[TestResult]
    prompt_b_results: List[TestResult]
    statistical_significance: float
    winner: Optional[str]
    confidence_level: float
    improvement_metrics: Dict[str, Any]
    timestamp: datetime


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    report_id: str
    prompt_id: str
    prompt_version: str
    validation_type: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_score: float
    test_results: List[TestResult]
    recommendations: List[str]
    timestamp: datetime


class PromptValidator:
    """
    Comprehensive prompt validation and testing framework
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_concurrent_tests = self.config.get('max_concurrent_tests', 5)
        self.default_timeout = self.config.get('default_timeout', 300)
        self.significance_threshold = self.config.get('significance_threshold', 0.05)
        self.min_sample_size = self.config.get('min_sample_size', 10)
        
        # Storage paths
        self.base_path = Path(self.config.get('base_path', '.claude-pm/prompt_validation'))
        self.scenarios_path = self.base_path / 'scenarios'
        self.results_path = self.base_path / 'results'
        self.reports_path = self.base_path / 'reports'
        self.ab_tests_path = self.base_path / 'ab_tests'
        
        # Create directories
        for path in [self.scenarios_path, self.results_path, self.reports_path, self.ab_tests_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Test scenario registry
        self.scenario_registry: Dict[str, TestScenario] = {}
        
        # Active tests tracking
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        
        # Test results cache
        self.results_cache: Dict[str, List[TestResult]] = {}
        
        self.logger.info("PromptValidator initialized successfully")
    
    async def create_test_scenario(self, 
                                 name: str,
                                 description: str,
                                 agent_type: str,
                                 task_description: str,
                                 expected_outputs: List[str],
                                 evaluation_criteria: Dict[str, Any],
                                 test_data: Optional[Dict[str, Any]] = None) -> TestScenario:
        """
        Create a new test scenario
        
        Args:
            name: Scenario name
            description: Scenario description
            agent_type: Target agent type
            task_description: Task to be performed
            expected_outputs: Expected output patterns
            evaluation_criteria: Evaluation criteria and weights
            test_data: Additional test data
            
        Returns:
            Created test scenario
        """
        try:
            scenario = TestScenario(
                scenario_id=self._generate_scenario_id(name),
                name=name,
                description=description,
                agent_type=agent_type,
                task_description=task_description,
                expected_outputs=expected_outputs,
                evaluation_criteria=evaluation_criteria,
                test_data=test_data or {}
            )
            
            # Save scenario
            await self._save_scenario(scenario)
            
            # Register scenario
            self.scenario_registry[scenario.scenario_id] = scenario
            
            self.logger.info(f"Created test scenario: {scenario.scenario_id}")
            return scenario
            
        except Exception as e:
            self.logger.error(f"Error creating test scenario: {e}")
            raise
    
    async def run_validation_test(self, 
                                prompt_id: str,
                                prompt_content: str,
                                scenarios: List[str],
                                test_type: TestType = TestType.QUALITY_TEST) -> ValidationReport:
        """
        Run validation test for a prompt
        
        Args:
            prompt_id: Prompt identifier
            prompt_content: Prompt content to test
            scenarios: List of scenario IDs to test
            test_type: Type of validation test
            
        Returns:
            Validation report
        """
        try:
            test_id = self._generate_test_id(prompt_id, test_type)
            
            # Track active test
            self.active_tests[test_id] = {
                'prompt_id': prompt_id,
                'status': TestStatus.RUNNING,
                'start_time': datetime.now(),
                'scenarios': scenarios
            }
            
            # Load test scenarios
            test_scenarios = []
            for scenario_id in scenarios:
                scenario = await self._load_scenario(scenario_id)
                if scenario:
                    test_scenarios.append(scenario)
            
            if not test_scenarios:
                raise ValueError("No valid test scenarios found")
            
            # Run tests
            test_results = []
            
            # Use ThreadPoolExecutor for concurrent testing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tests) as executor:
                # Submit all test tasks
                future_to_scenario = {
                    executor.submit(self._run_single_test, prompt_content, scenario, test_id): scenario
                    for scenario in test_scenarios
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_scenario):
                    scenario = future_to_scenario[future]
                    try:
                        result = future.result()
                        test_results.append(result)
                    except Exception as e:
                        self.logger.error(f"Test failed for scenario {scenario.scenario_id}: {e}")
                        # Create failure result
                        failure_result = TestResult(
                            test_id=test_id,
                            scenario_id=scenario.scenario_id,
                            prompt_version=prompt_id,
                            execution_time=0.0,
                            success=False,
                            score=0.0,
                            outputs={},
                            errors=[str(e)],
                            metrics={},
                            timestamp=datetime.now()
                        )
                        test_results.append(failure_result)
            
            # Calculate overall metrics
            passed_tests = len([r for r in test_results if r.success])
            failed_tests = len([r for r in test_results if not r.success])
            
            scores = [r.score for r in test_results if r.success]
            overall_score = statistics.mean(scores) if scores else 0.0
            
            # Generate recommendations
            recommendations = self._generate_recommendations(test_results)
            
            # Create validation report
            report = ValidationReport(
                report_id=self._generate_report_id(prompt_id),
                prompt_id=prompt_id,
                prompt_version=prompt_id,  # Could be enhanced with version tracking
                validation_type=test_type.value,
                total_tests=len(test_results),
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                overall_score=overall_score,
                test_results=test_results,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Save results
            await self._save_validation_report(report)
            
            # Update active tests
            self.active_tests[test_id]['status'] = TestStatus.COMPLETED
            self.active_tests[test_id]['end_time'] = datetime.now()
            
            self.logger.info(f"Validation test completed: {test_id} - {passed_tests}/{len(test_results)} passed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error running validation test: {e}")
            if test_id in self.active_tests:
                self.active_tests[test_id]['status'] = TestStatus.FAILED
                self.active_tests[test_id]['error'] = str(e)
            raise
    
    async def run_ab_test(self, 
                        prompt_a_id: str,
                        prompt_a_content: str,
                        prompt_b_id: str,
                        prompt_b_content: str,
                        scenarios: List[str],
                        sample_size: Optional[int] = None) -> ABTestResult:
        """
        Run A/B test between two prompts
        
        Args:
            prompt_a_id: First prompt identifier
            prompt_a_content: First prompt content
            prompt_b_id: Second prompt identifier
            prompt_b_content: Second prompt content
            scenarios: List of scenario IDs to test
            sample_size: Number of tests per prompt (optional)
            
        Returns:
            A/B test result
        """
        try:
            test_id = self._generate_ab_test_id(prompt_a_id, prompt_b_id)
            
            # Track active test
            self.active_tests[test_id] = {
                'type': 'ab_test',
                'prompt_a_id': prompt_a_id,
                'prompt_b_id': prompt_b_id,
                'status': TestStatus.RUNNING,
                'start_time': datetime.now(),
                'scenarios': scenarios
            }
            
            # Load test scenarios
            test_scenarios = []
            for scenario_id in scenarios:
                scenario = await self._load_scenario(scenario_id)
                if scenario:
                    test_scenarios.append(scenario)
            
            if not test_scenarios:
                raise ValueError("No valid test scenarios found")
            
            # Determine sample size
            if sample_size is None:
                sample_size = max(self.min_sample_size, len(test_scenarios))
            
            # Run tests for both prompts
            prompt_a_results = []
            prompt_b_results = []
            
            # Test prompt A
            for i in range(sample_size):
                scenario = random.choice(test_scenarios)
                result = await self._run_single_test_async(prompt_a_content, scenario, f"{test_id}_a_{i}")
                prompt_a_results.append(result)
            
            # Test prompt B
            for i in range(sample_size):
                scenario = random.choice(test_scenarios)
                result = await self._run_single_test_async(prompt_b_content, scenario, f"{test_id}_b_{i}")
                prompt_b_results.append(result)
            
            # Calculate statistical significance
            significance = self._calculate_statistical_significance(prompt_a_results, prompt_b_results)
            
            # Determine winner
            a_scores = [r.score for r in prompt_a_results if r.success]
            b_scores = [r.score for r in prompt_b_results if r.success]
            
            a_mean = statistics.mean(a_scores) if a_scores else 0.0
            b_mean = statistics.mean(b_scores) if b_scores else 0.0
            
            winner = None
            if significance < self.significance_threshold:
                if a_mean > b_mean:
                    winner = prompt_a_id
                elif b_mean > a_mean:
                    winner = prompt_b_id
            
            # Calculate confidence level
            confidence_level = 1 - significance
            
            # Calculate improvement metrics
            improvement_metrics = self._calculate_improvement_metrics(prompt_a_results, prompt_b_results)
            
            # Create A/B test result
            ab_result = ABTestResult(
                test_id=test_id,
                prompt_a_id=prompt_a_id,
                prompt_b_id=prompt_b_id,
                scenarios_tested=len(test_scenarios),
                prompt_a_results=prompt_a_results,
                prompt_b_results=prompt_b_results,
                statistical_significance=significance,
                winner=winner,
                confidence_level=confidence_level,
                improvement_metrics=improvement_metrics,
                timestamp=datetime.now()
            )
            
            # Save A/B test result
            await self._save_ab_test_result(ab_result)
            
            # Update active tests
            self.active_tests[test_id]['status'] = TestStatus.COMPLETED
            self.active_tests[test_id]['end_time'] = datetime.now()
            
            self.logger.info(f"A/B test completed: {test_id} - Winner: {winner or 'No significant difference'}")
            return ab_result
            
        except Exception as e:
            self.logger.error(f"Error running A/B test: {e}")
            if test_id in self.active_tests:
                self.active_tests[test_id]['status'] = TestStatus.FAILED
                self.active_tests[test_id]['error'] = str(e)
            raise
    
    async def run_regression_test(self, 
                                prompt_id: str,
                                current_content: str,
                                previous_content: str,
                                scenarios: List[str]) -> Dict[str, Any]:
        """
        Run regression test to compare current vs previous prompt
        
        Args:
            prompt_id: Prompt identifier
            current_content: Current prompt content
            previous_content: Previous prompt content
            scenarios: List of scenario IDs to test
            
        Returns:
            Regression test results
        """
        try:
            # Run A/B test between current and previous
            ab_result = await self.run_ab_test(
                prompt_a_id=f"{prompt_id}_previous",
                prompt_a_content=previous_content,
                prompt_b_id=f"{prompt_id}_current",
                prompt_b_content=current_content,
                scenarios=scenarios
            )
            
            # Analyze regression
            regression_analysis = self._analyze_regression(ab_result)
            
            return {
                'regression_detected': regression_analysis['regression_detected'],
                'performance_change': regression_analysis['performance_change'],
                'affected_scenarios': regression_analysis['affected_scenarios'],
                'recommendations': regression_analysis['recommendations'],
                'ab_test_result': ab_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error running regression test: {e}")
            raise
    
    async def run_performance_benchmark(self, 
                                      prompt_id: str,
                                      prompt_content: str,
                                      scenarios: List[str],
                                      iterations: int = 10) -> Dict[str, Any]:
        """
        Run performance benchmark test
        
        Args:
            prompt_id: Prompt identifier
            prompt_content: Prompt content
            scenarios: List of scenario IDs to test
            iterations: Number of iterations per scenario
            
        Returns:
            Performance benchmark results
        """
        try:
            benchmark_results = {
                'prompt_id': prompt_id,
                'scenarios_tested': len(scenarios),
                'iterations_per_scenario': iterations,
                'results': [],
                'performance_metrics': {},
                'timestamp': datetime.now().isoformat()
            }
            
            for scenario_id in scenarios:
                scenario = await self._load_scenario(scenario_id)
                if not scenario:
                    continue
                
                scenario_results = []
                
                for i in range(iterations):
                    start_time = time.time()
                    result = await self._run_single_test_async(
                        prompt_content, 
                        scenario, 
                        f"{prompt_id}_perf_{scenario_id}_{i}"
                    )
                    end_time = time.time()
                    
                    scenario_results.append({
                        'iteration': i,
                        'execution_time': end_time - start_time,
                        'success': result.success,
                        'score': result.score,
                        'memory_usage': result.metrics.get('memory_usage', 0),
                        'token_count': result.metrics.get('token_count', 0)
                    })
                
                # Calculate scenario performance metrics
                execution_times = [r['execution_time'] for r in scenario_results]
                success_rate = len([r for r in scenario_results if r['success']]) / len(scenario_results)
                
                scenario_metrics = {
                    'scenario_id': scenario_id,
                    'avg_execution_time': statistics.mean(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                    'success_rate': success_rate,
                    'throughput': 1.0 / statistics.mean(execution_times) if execution_times else 0,
                    'results': scenario_results
                }
                
                benchmark_results['results'].append(scenario_metrics)
            
            # Calculate overall performance metrics
            all_execution_times = []
            all_success_rates = []
            
            for scenario_result in benchmark_results['results']:
                all_execution_times.append(scenario_result['avg_execution_time'])
                all_success_rates.append(scenario_result['success_rate'])
            
            benchmark_results['performance_metrics'] = {
                'overall_avg_execution_time': statistics.mean(all_execution_times) if all_execution_times else 0,
                'overall_success_rate': statistics.mean(all_success_rates) if all_success_rates else 0,
                'overall_throughput': len(scenarios) * iterations / sum(all_execution_times) if all_execution_times else 0,
                'consistency_score': 1.0 - (statistics.stdev(all_execution_times) / statistics.mean(all_execution_times)) if all_execution_times and statistics.mean(all_execution_times) > 0 else 0
            }
            
            # Save benchmark results
            await self._save_benchmark_results(benchmark_results)
            
            return benchmark_results
            
        except Exception as e:
            self.logger.error(f"Error running performance benchmark: {e}")
            raise
    
    async def generate_test_scenarios(self, 
                                    agent_type: str,
                                    difficulty_level: str = "medium",
                                    count: int = 5) -> List[TestScenario]:
        """
        Generate test scenarios automatically
        
        Args:
            agent_type: Target agent type
            difficulty_level: Difficulty level (easy, medium, hard)
            count: Number of scenarios to generate
            
        Returns:
            List of generated test scenarios
        """
        try:
            scenarios = []
            
            # Define scenario templates by agent type
            scenario_templates = {
                'Documentation': [
                    {
                        'name': 'Generate API Documentation',
                        'task': 'Generate comprehensive API documentation',
                        'expected_outputs': ['endpoints', 'parameters', 'examples', 'responses'],
                        'criteria': {'completeness': 0.3, 'accuracy': 0.4, 'clarity': 0.3}
                    },
                    {
                        'name': 'Create Changelog',
                        'task': 'Create changelog from git commits',
                        'expected_outputs': ['version', 'changes', 'date', 'impact'],
                        'criteria': {'completeness': 0.4, 'accuracy': 0.3, 'format': 0.3}
                    }
                ],
                'QA': [
                    {
                        'name': 'Test Suite Execution',
                        'task': 'Execute comprehensive test suite',
                        'expected_outputs': ['test_results', 'coverage', 'failures', 'recommendations'],
                        'criteria': {'thoroughness': 0.4, 'accuracy': 0.3, 'reporting': 0.3}
                    },
                    {
                        'name': 'Code Quality Check',
                        'task': 'Perform code quality analysis',
                        'expected_outputs': ['quality_score', 'issues', 'suggestions', 'metrics'],
                        'criteria': {'completeness': 0.3, 'accuracy': 0.4, 'actionability': 0.3}
                    }
                ],
                'Engineer': [
                    {
                        'name': 'Feature Implementation',
                        'task': 'Implement new feature based on requirements',
                        'expected_outputs': ['code', 'tests', 'documentation', 'examples'],
                        'criteria': {'functionality': 0.4, 'quality': 0.3, 'maintainability': 0.3}
                    },
                    {
                        'name': 'Bug Fix',
                        'task': 'Fix reported bug with detailed analysis',
                        'expected_outputs': ['fix', 'explanation', 'tests', 'prevention'],
                        'criteria': {'correctness': 0.5, 'completeness': 0.3, 'prevention': 0.2}
                    }
                ]
            }
            
            templates = scenario_templates.get(agent_type, [])
            
            for i in range(min(count, len(templates))):
                template = templates[i]
                
                # Adjust complexity based on difficulty level
                complexity_multiplier = {
                    'easy': 0.5,
                    'medium': 1.0,
                    'hard': 1.5
                }[difficulty_level]
                
                # Generate test data
                test_data = self._generate_test_data(agent_type, template, complexity_multiplier)
                
                scenario = await self.create_test_scenario(
                    name=f"{template['name']} - {difficulty_level}",
                    description=f"Auto-generated {difficulty_level} scenario for {agent_type}",
                    agent_type=agent_type,
                    task_description=template['task'],
                    expected_outputs=template['expected_outputs'],
                    evaluation_criteria=template['criteria'],
                    test_data=test_data
                )
                
                scenarios.append(scenario)
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Error generating test scenarios: {e}")
            return []
    
    async def get_test_analytics(self, 
                               prompt_id: Optional[str] = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """
        Get test analytics and metrics
        
        Args:
            prompt_id: Specific prompt to analyze (optional)
            days_back: Number of days to analyze
            
        Returns:
            Test analytics data
        """
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Load test results
            all_results = await self._load_test_results_since(since_date)
            
            if prompt_id:
                all_results = [r for r in all_results if r.prompt_version == prompt_id]
            
            # Calculate analytics
            analytics = {
                'period': {
                    'days_back': days_back,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'summary': {
                    'total_tests': len(all_results),
                    'passed_tests': len([r for r in all_results if r.success]),
                    'failed_tests': len([r for r in all_results if not r.success]),
                    'average_score': statistics.mean([r.score for r in all_results if r.success]) if all_results else 0.0,
                    'success_rate': len([r for r in all_results if r.success]) / len(all_results) if all_results else 0.0
                },
                'performance_metrics': {
                    'avg_execution_time': statistics.mean([r.execution_time for r in all_results]) if all_results else 0.0,
                    'min_execution_time': min([r.execution_time for r in all_results]) if all_results else 0.0,
                    'max_execution_time': max([r.execution_time for r in all_results]) if all_results else 0.0
                },
                'test_trends': self._calculate_test_trends(all_results),
                'scenario_analysis': self._analyze_scenario_performance(all_results),
                'recent_tests': [
                    {
                        'test_id': r.test_id,
                        'scenario_id': r.scenario_id,
                        'success': r.success,
                        'score': r.score,
                        'execution_time': r.execution_time,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in sorted(all_results, key=lambda x: x.timestamp, reverse=True)[:10]
                ]
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting test analytics: {e}")
            return {'error': str(e)}
    
    # Private methods
    def _run_single_test(self, 
                        prompt_content: str,
                        scenario: TestScenario,
                        test_id: str) -> TestResult:
        """Run a single test (synchronous)"""
        try:
            start_time = time.time()
            
            # This would integrate with actual agent execution system
            # For now, simulate test execution
            success, score, outputs, metrics = self._simulate_test_execution(prompt_content, scenario)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                prompt_version=prompt_content[:50],  # Truncated for ID
                execution_time=execution_time,
                success=success,
                score=score,
                outputs=outputs,
                errors=[],
                metrics=metrics,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                prompt_version=prompt_content[:50],
                execution_time=0.0,
                success=False,
                score=0.0,
                outputs={},
                errors=[str(e)],
                metrics={},
                timestamp=datetime.now()
            )
    
    async def _run_single_test_async(self, 
                                   prompt_content: str,
                                   scenario: TestScenario,
                                   test_id: str) -> TestResult:
        """Run a single test (asynchronous)"""
        try:
            start_time = time.time()
            
            # Simulate async test execution
            await asyncio.sleep(0.1)  # Simulate some async work
            success, score, outputs, metrics = self._simulate_test_execution(prompt_content, scenario)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                prompt_version=prompt_content[:50],
                execution_time=execution_time,
                success=success,
                score=score,
                outputs=outputs,
                errors=[],
                metrics=metrics,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return TestResult(
                test_id=test_id,
                scenario_id=scenario.scenario_id,
                prompt_version=prompt_content[:50],
                execution_time=0.0,
                success=False,
                score=0.0,
                outputs={},
                errors=[str(e)],
                metrics={},
                timestamp=datetime.now()
            )
    
    def _simulate_test_execution(self, 
                               prompt_content: str,
                               scenario: TestScenario) -> Tuple[bool, float, Dict[str, Any], Dict[str, Any]]:
        """Simulate test execution (would be replaced with actual agent execution)"""
        # Simulate varying performance based on prompt content and scenario
        base_score = 0.7
        
        # Adjust score based on prompt length (longer prompts might be more detailed)
        length_factor = min(1.0, len(prompt_content) / 1000)
        
        # Adjust score based on expected outputs presence
        output_factor = 0.0
        for expected_output in scenario.expected_outputs:
            if expected_output.lower() in prompt_content.lower():
                output_factor += 0.1
        
        # Add some randomness
        random_factor = random.uniform(-0.2, 0.2)
        
        final_score = max(0.0, min(1.0, base_score + length_factor * 0.2 + output_factor + random_factor))
        
        # Determine success based on score
        success = final_score >= 0.6
        
        # Generate mock outputs
        outputs = {
            'generated_content': f"Mock output for {scenario.name}",
            'completeness': final_score,
            'quality_metrics': {
                'relevance': final_score * 0.9,
                'accuracy': final_score * 1.1,
                'clarity': final_score * 0.8
            }
        }
        
        # Generate mock metrics
        metrics = {
            'token_count': len(prompt_content.split()) + random.randint(100, 500),
            'memory_usage': random.randint(50, 200),
            'api_calls': random.randint(1, 5)
        }
        
        return success, final_score, outputs, metrics
    
    def _calculate_statistical_significance(self, 
                                          results_a: List[TestResult],
                                          results_b: List[TestResult]) -> float:
        """Calculate statistical significance between two result sets"""
        try:
            # Extract scores for successful tests
            scores_a = [r.score for r in results_a if r.success]
            scores_b = [r.score for r in results_b if r.success]
            
            if not scores_a or not scores_b:
                return 1.0  # No significance if no successful tests
            
            # Simple t-test approximation
            mean_a = statistics.mean(scores_a)
            mean_b = statistics.mean(scores_b)
            
            if len(scores_a) > 1:
                std_a = statistics.stdev(scores_a)
            else:
                std_a = 0.0
                
            if len(scores_b) > 1:
                std_b = statistics.stdev(scores_b)
            else:
                std_b = 0.0
            
            # Pooled standard error
            n_a = len(scores_a)
            n_b = len(scores_b)
            
            if n_a + n_b < 4:
                return 1.0  # Not enough data
            
            pooled_std = ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2)
            pooled_std = pooled_std**0.5
            
            if pooled_std == 0:
                return 0.0 if mean_a != mean_b else 1.0
            
            # T-statistic
            t_stat = (mean_a - mean_b) / (pooled_std * (1/n_a + 1/n_b)**0.5)
            
            # Approximate p-value (simplified)
            p_value = 2 * (1 - min(0.999, abs(t_stat) / 3))
            
            return p_value
            
        except Exception as e:
            self.logger.error(f"Error calculating statistical significance: {e}")
            return 1.0
    
    def _calculate_improvement_metrics(self, 
                                     results_a: List[TestResult],
                                     results_b: List[TestResult]) -> Dict[str, Any]:
        """Calculate improvement metrics between two result sets"""
        try:
            # Success rates
            success_rate_a = len([r for r in results_a if r.success]) / len(results_a) if results_a else 0.0
            success_rate_b = len([r for r in results_b if r.success]) / len(results_b) if results_b else 0.0
            
            # Average scores
            scores_a = [r.score for r in results_a if r.success]
            scores_b = [r.score for r in results_b if r.success]
            
            avg_score_a = statistics.mean(scores_a) if scores_a else 0.0
            avg_score_b = statistics.mean(scores_b) if scores_b else 0.0
            
            # Execution times
            exec_times_a = [r.execution_time for r in results_a]
            exec_times_b = [r.execution_time for r in results_b]
            
            avg_exec_time_a = statistics.mean(exec_times_a) if exec_times_a else 0.0
            avg_exec_time_b = statistics.mean(exec_times_b) if exec_times_b else 0.0
            
            return {
                'success_rate_improvement': success_rate_b - success_rate_a,
                'score_improvement': avg_score_b - avg_score_a,
                'execution_time_improvement': avg_exec_time_a - avg_exec_time_b,  # Negative means faster
                'relative_success_improvement': (success_rate_b - success_rate_a) / success_rate_a if success_rate_a > 0 else 0.0,
                'relative_score_improvement': (avg_score_b - avg_score_a) / avg_score_a if avg_score_a > 0 else 0.0,
                'relative_time_improvement': (avg_exec_time_a - avg_exec_time_b) / avg_exec_time_a if avg_exec_time_a > 0 else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating improvement metrics: {e}")
            return {}
    
    def _analyze_regression(self, ab_result: ABTestResult) -> Dict[str, Any]:
        """Analyze regression from A/B test results"""
        try:
            # Check if current version (B) is worse than previous (A)
            improvement_metrics = ab_result.improvement_metrics
            
            regression_detected = False
            affected_scenarios = []
            
            # Check for regression indicators
            if improvement_metrics.get('success_rate_improvement', 0) < -0.1:
                regression_detected = True
                affected_scenarios.append('Success rate decreased significantly')
            
            if improvement_metrics.get('score_improvement', 0) < -0.15:
                regression_detected = True
                affected_scenarios.append('Quality score decreased significantly')
            
            if improvement_metrics.get('execution_time_improvement', 0) < -2.0:
                regression_detected = True
                affected_scenarios.append('Execution time increased significantly')
            
            # Performance change summary
            performance_change = {
                'success_rate_change': improvement_metrics.get('success_rate_improvement', 0),
                'score_change': improvement_metrics.get('score_improvement', 0),
                'time_change': improvement_metrics.get('execution_time_improvement', 0)
            }
            
            # Generate recommendations
            recommendations = []
            if regression_detected:
                recommendations.append("Consider rolling back to previous version")
                recommendations.append("Investigate root cause of performance degradation")
                recommendations.append("Run additional targeted tests")
            else:
                recommendations.append("No significant regression detected")
                recommendations.append("Monitor performance in production")
            
            return {
                'regression_detected': regression_detected,
                'performance_change': performance_change,
                'affected_scenarios': affected_scenarios,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing regression: {e}")
            return {
                'regression_detected': False,
                'performance_change': {},
                'affected_scenarios': [],
                'recommendations': ['Error analyzing regression']
            }
    
    def _generate_recommendations(self, test_results: List[TestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        try:
            # Calculate metrics
            success_rate = len([r for r in test_results if r.success]) / len(test_results)
            avg_score = statistics.mean([r.score for r in test_results if r.success])
            
            # Generate recommendations based on performance
            if success_rate < 0.7:
                recommendations.append("Low success rate - review prompt clarity and instructions")
            
            if avg_score < 0.6:
                recommendations.append("Low quality scores - enhance prompt with better examples and guidance")
            
            # Analyze common failure patterns
            failed_scenarios = [r.scenario_id for r in test_results if not r.success]
            if failed_scenarios:
                scenario_counts = {}
                for scenario_id in failed_scenarios:
                    scenario_counts[scenario_id] = scenario_counts.get(scenario_id, 0) + 1
                
                most_failed = max(scenario_counts, key=scenario_counts.get)
                recommendations.append(f"Focus on improving performance for scenario: {most_failed}")
            
            # Performance recommendations
            slow_tests = [r for r in test_results if r.execution_time > 5.0]
            if slow_tests:
                recommendations.append("Consider optimizing prompt for better performance")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _generate_test_data(self, 
                          agent_type: str,
                          template: Dict[str, Any],
                          complexity_multiplier: float) -> Dict[str, Any]:
        """Generate test data for scenario"""
        base_test_data = {
            'complexity_level': complexity_multiplier,
            'timeout_factor': complexity_multiplier,
            'expected_quality_threshold': 0.8 / complexity_multiplier
        }
        
        # Agent-specific test data
        if agent_type == 'Documentation':
            base_test_data.update({
                'doc_type': 'api' if 'API' in template['name'] else 'changelog',
                'detail_level': 'high' if complexity_multiplier > 1.0 else 'medium',
                'include_examples': True
            })
        elif agent_type == 'QA':
            base_test_data.update({
                'test_coverage_requirement': 0.9 if complexity_multiplier > 1.0 else 0.7,
                'failure_analysis_required': complexity_multiplier > 1.0,
                'performance_testing': complexity_multiplier > 1.0
            })
        elif agent_type == 'Engineer':
            base_test_data.update({
                'code_complexity': 'high' if complexity_multiplier > 1.0 else 'medium',
                'testing_required': True,
                'documentation_required': complexity_multiplier > 0.5
            })
        
        return base_test_data
    
    def _calculate_test_trends(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate test trends over time"""
        try:
            if not results:
                return {}
            
            # Sort by timestamp
            sorted_results = sorted(results, key=lambda r: r.timestamp)
            
            # Calculate daily trends
            daily_stats = {}
            for result in sorted_results:
                date_key = result.timestamp.date()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'total': 0,
                        'passed': 0,
                        'scores': []
                    }
                
                daily_stats[date_key]['total'] += 1
                if result.success:
                    daily_stats[date_key]['passed'] += 1
                    daily_stats[date_key]['scores'].append(result.score)
            
            # Calculate trend metrics
            dates = sorted(daily_stats.keys())
            success_rates = []
            avg_scores = []
            
            for date in dates:
                stats = daily_stats[date]
                success_rate = stats['passed'] / stats['total']
                avg_score = statistics.mean(stats['scores']) if stats['scores'] else 0.0
                
                success_rates.append(success_rate)
                avg_scores.append(avg_score)
            
            # Calculate trend direction
            if len(success_rates) >= 2:
                success_trend = "improving" if success_rates[-1] > success_rates[0] else "declining"
                score_trend = "improving" if avg_scores[-1] > avg_scores[0] else "declining"
            else:
                success_trend = "stable"
                score_trend = "stable"
            
            return {
                'success_rate_trend': success_trend,
                'score_trend': score_trend,
                'daily_stats': {
                    str(date): {
                        'success_rate': daily_stats[date]['passed'] / daily_stats[date]['total'],
                        'avg_score': statistics.mean(daily_stats[date]['scores']) if daily_stats[date]['scores'] else 0.0,
                        'total_tests': daily_stats[date]['total']
                    }
                    for date in dates
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating test trends: {e}")
            return {}
    
    def _analyze_scenario_performance(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze performance by scenario"""
        try:
            scenario_stats = {}
            
            for result in results:
                scenario_id = result.scenario_id
                if scenario_id not in scenario_stats:
                    scenario_stats[scenario_id] = {
                        'total_tests': 0,
                        'passed_tests': 0,
                        'scores': [],
                        'execution_times': []
                    }
                
                stats = scenario_stats[scenario_id]
                stats['total_tests'] += 1
                stats['execution_times'].append(result.execution_time)
                
                if result.success:
                    stats['passed_tests'] += 1
                    stats['scores'].append(result.score)
            
            # Calculate metrics for each scenario
            scenario_analysis = {}
            for scenario_id, stats in scenario_stats.items():
                scenario_analysis[scenario_id] = {
                    'success_rate': stats['passed_tests'] / stats['total_tests'],
                    'avg_score': statistics.mean(stats['scores']) if stats['scores'] else 0.0,
                    'avg_execution_time': statistics.mean(stats['execution_times']),
                    'total_tests': stats['total_tests']
                }
            
            return scenario_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing scenario performance: {e}")
            return {}
    
    # Storage methods
    async def _save_scenario(self, scenario: TestScenario):
        """Save test scenario to storage"""
        try:
            scenario_file = self.scenarios_path / f"{scenario.scenario_id}.json"
            with open(scenario_file, 'w') as f:
                json.dump(asdict(scenario), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving scenario: {e}")
    
    async def _load_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Load test scenario from storage"""
        try:
            scenario_file = self.scenarios_path / f"{scenario_id}.json"
            if not scenario_file.exists():
                return None
            
            with open(scenario_file, 'r') as f:
                data = json.load(f)
            
            return TestScenario(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading scenario {scenario_id}: {e}")
            return None
    
    async def _save_validation_report(self, report: ValidationReport):
        """Save validation report to storage"""
        try:
            report_file = self.reports_path / f"{report.report_id}.json"
            with open(report_file, 'w') as f:
                report_dict = asdict(report)
                report_dict['timestamp'] = report.timestamp.isoformat()
                # Convert test results
                report_dict['test_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in report.test_results
                ]
                json.dump(report_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving validation report: {e}")
    
    async def _save_ab_test_result(self, ab_result: ABTestResult):
        """Save A/B test result to storage"""
        try:
            ab_file = self.ab_tests_path / f"{ab_result.test_id}.json"
            with open(ab_file, 'w') as f:
                ab_dict = asdict(ab_result)
                ab_dict['timestamp'] = ab_result.timestamp.isoformat()
                # Convert test results
                ab_dict['prompt_a_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in ab_result.prompt_a_results
                ]
                ab_dict['prompt_b_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in ab_result.prompt_b_results
                ]
                json.dump(ab_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving A/B test result: {e}")
    
    async def _save_benchmark_results(self, benchmark_results: Dict[str, Any]):
        """Save benchmark results to storage"""
        try:
            benchmark_file = self.results_path / f"benchmark_{benchmark_results['prompt_id']}_{int(time.time())}.json"
            with open(benchmark_file, 'w') as f:
                json.dump(benchmark_results, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving benchmark results: {e}")
    
    async def _load_test_results_since(self, since_date: datetime) -> List[TestResult]:
        """Load test results since given date"""
        results = []
        
        try:
            # Load from validation reports
            for report_file in self.reports_path.glob("*.json"):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    report_timestamp = datetime.fromisoformat(report_data['timestamp'])
                    if report_timestamp >= since_date:
                        for result_data in report_data['test_results']:
                            result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                            results.append(TestResult(**result_data))
                            
                except Exception as e:
                    self.logger.error(f"Error loading report {report_file}: {e}")
                    continue
            
            # Load from A/B test results
            for ab_file in self.ab_tests_path.glob("*.json"):
                try:
                    with open(ab_file, 'r') as f:
                        ab_data = json.load(f)
                    
                    ab_timestamp = datetime.fromisoformat(ab_data['timestamp'])
                    if ab_timestamp >= since_date:
                        for result_data in ab_data['prompt_a_results'] + ab_data['prompt_b_results']:
                            result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                            results.append(TestResult(**result_data))
                            
                except Exception as e:
                    self.logger.error(f"Error loading A/B test {ab_file}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error loading test results since {since_date}: {e}")
        
        return results
    
    # Utility methods
    def _generate_scenario_id(self, name: str) -> str:
        """Generate unique scenario ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"scenario_{timestamp}_{hash_val}"
    
    def _generate_test_id(self, prompt_id: str, test_type: TestType) -> str:
        """Generate unique test ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(f"{prompt_id}_{test_type.value}".encode()).hexdigest()[:8]
        return f"test_{timestamp}_{hash_val}"
    
    def _generate_ab_test_id(self, prompt_a_id: str, prompt_b_id: str) -> str:
        """Generate unique A/B test ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(f"{prompt_a_id}_{prompt_b_id}".encode()).hexdigest()[:8]
        return f"ab_test_{timestamp}_{hash_val}"
    
    def _generate_report_id(self, prompt_id: str) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(prompt_id.encode()).hexdigest()[:8]
        return f"report_{timestamp}_{hash_val}"


# Async convenience functions
async def run_quick_validation(prompt_content: str, 
                             agent_type: str = "Engineer") -> Dict[str, Any]:
    """
    Quick validation test for a prompt
    
    Args:
        prompt_content: Prompt content to validate
        agent_type: Target agent type
        
    Returns:
        Quick validation results
    """
    validator = PromptValidator()
    
    # Generate test scenarios
    scenarios = await validator.generate_test_scenarios(agent_type, "medium", 3)
    scenario_ids = [s.scenario_id for s in scenarios]
    
    # Run validation
    report = await validator.run_validation_test(
        prompt_id=f"quick_test_{int(time.time())}",
        prompt_content=prompt_content,
        scenarios=scenario_ids
    )
    
    return {
        'overall_score': report.overall_score,
        'success_rate': report.passed_tests / report.total_tests,
        'recommendations': report.recommendations,
        'test_details': [
            {
                'scenario_id': r.scenario_id,
                'success': r.success,
                'score': r.score,
                'execution_time': r.execution_time
            }
            for r in report.test_results
        ]
    }


async def compare_prompts(prompt_a: str, 
                        prompt_b: str,
                        agent_type: str = "Engineer") -> Dict[str, Any]:
    """
    Compare two prompts using A/B testing
    
    Args:
        prompt_a: First prompt to compare
        prompt_b: Second prompt to compare
        agent_type: Target agent type
        
    Returns:
        Comparison results
    """
    validator = PromptValidator()
    
    # Generate test scenarios
    scenarios = await validator.generate_test_scenarios(agent_type, "medium", 5)
    scenario_ids = [s.scenario_id for s in scenarios]
    
    # Run A/B test
    ab_result = await validator.run_ab_test(
        prompt_a_id="prompt_a",
        prompt_a_content=prompt_a,
        prompt_b_id="prompt_b",
        prompt_b_content=prompt_b,
        scenarios=scenario_ids
    )
    
    return {
        'winner': ab_result.winner,
        'confidence_level': ab_result.confidence_level,
        'statistical_significance': ab_result.statistical_significance,
        'improvement_metrics': ab_result.improvement_metrics,
        'recommendation': (
            f"Prompt {ab_result.winner} is significantly better" if ab_result.winner 
            else "No significant difference between prompts"
        )
    }


if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize validator
        validator = PromptValidator()
        
        # Create test scenario
        scenario = await validator.create_test_scenario(
            name="Test Code Generation",
            description="Test ability to generate code",
            agent_type="Engineer",
            task_description="Generate a Python function",
            expected_outputs=["function", "docstring", "tests"],
            evaluation_criteria={"functionality": 0.5, "quality": 0.3, "documentation": 0.2}
        )
        
        # Test a prompt
        test_prompt = "Generate a Python function that calculates fibonacci numbers"
        
        report = await validator.run_validation_test(
            prompt_id="test_prompt",
            prompt_content=test_prompt,
            scenarios=[scenario.scenario_id]
        )
        
        print(f"Validation completed: {report.passed_tests}/{report.total_tests} passed")
        print(f"Overall score: {report.overall_score}")
    
    asyncio.run(main())