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

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import (
    TestType, TestStatus, TestScenario, TestResult, 
    ABTestResult, ValidationReport
)
from .test_execution import TestExecutor
from .ab_testing import ABTester
from .regression_testing import RegressionTester
from .performance_benchmarking import PerformanceBenchmarker
from .scenario_management import ScenarioManager
from .analytics import AnalyticsEngine
from .storage import StorageManager
from .utils import (
    generate_test_id, generate_report_id,
    generate_recommendations
)


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
        
        # Initialize components
        self.executor = TestExecutor(self.max_concurrent_tests, self.default_timeout)
        self.ab_tester = ABTester(self.significance_threshold, self.min_sample_size)
        self.regression_tester = RegressionTester()
        self.benchmarker = PerformanceBenchmarker()
        self.scenario_manager = ScenarioManager()
        self.analytics_engine = AnalyticsEngine()
        self.storage_manager = StorageManager(self.config.get('base_path', '.claude-pm/prompt_validation'))
        
        # Results cache
        self.results_cache: Dict[str, List[TestResult]] = {}
        
        self.logger.info("PromptValidator initialized successfully")
    
    # Scenario management
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
        scenario = await self.scenario_manager.create_test_scenario(
            name, description, agent_type, task_description,
            expected_outputs, evaluation_criteria, test_data
        )
        
        # Save scenario
        await self.storage_manager.save_scenario(scenario)
        
        return scenario
    
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
        scenarios = await self.scenario_manager.generate_test_scenarios(
            agent_type, difficulty_level, count
        )
        
        # Save generated scenarios
        for scenario in scenarios:
            await self.storage_manager.save_scenario(scenario)
        
        return scenarios
    
    # Validation testing
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
            test_id = generate_test_id(prompt_id, test_type.value)
            
            # Track active test
            self.executor.track_active_test(test_id, {
                'prompt_id': prompt_id,
                'scenarios': scenarios
            })
            
            # Load test scenarios
            test_scenarios = []
            for scenario_id in scenarios:
                scenario = await self.storage_manager.load_scenario(scenario_id)
                if scenario:
                    test_scenarios.append(scenario)
            
            if not test_scenarios:
                raise ValueError("No valid test scenarios found")
            
            # Run tests
            test_results = self.executor.run_concurrent_tests(
                prompt_content, test_scenarios, test_id
            )
            
            # Calculate overall metrics
            passed_tests = len([r for r in test_results if r.success])
            failed_tests = len([r for r in test_results if not r.success])
            
            scores = [r.score for r in test_results if r.success]
            overall_score = sum(scores) / len(scores) if scores else 0.0
            
            # Generate recommendations
            recommendations = generate_recommendations(test_results)
            
            # Create validation report
            report = ValidationReport(
                report_id=generate_report_id(prompt_id),
                prompt_id=prompt_id,
                prompt_version=prompt_id,
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
            await self.storage_manager.save_validation_report(report)
            
            # Update test status
            self.executor.update_test_status(test_id, TestStatus.COMPLETED)
            
            self.logger.info(f"Validation test completed: {test_id} - {passed_tests}/{len(test_results)} passed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error running validation test: {e}")
            if 'test_id' in locals():
                self.executor.update_test_status(test_id, TestStatus.FAILED, str(e))
            raise
    
    # A/B testing
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
        # Load test scenarios
        test_scenarios = []
        for scenario_id in scenarios:
            scenario = await self.storage_manager.load_scenario(scenario_id)
            if scenario:
                test_scenarios.append(scenario)
        
        if not test_scenarios:
            raise ValueError("No valid test scenarios found")
        
        # Run A/B test
        ab_result = await self.ab_tester.run_ab_test(
            prompt_a_id, prompt_a_content,
            prompt_b_id, prompt_b_content,
            test_scenarios, sample_size
        )
        
        # Save result
        await self.storage_manager.save_ab_test_result(ab_result)
        
        return ab_result
    
    # Regression testing
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
        # Load test scenarios
        test_scenarios = []
        for scenario_id in scenarios:
            scenario = await self.storage_manager.load_scenario(scenario_id)
            if scenario:
                test_scenarios.append(scenario)
        
        if not test_scenarios:
            raise ValueError("No valid test scenarios found")
        
        return await self.regression_tester.run_regression_test(
            prompt_id, current_content, previous_content, test_scenarios
        )
    
    # Performance benchmarking
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
        # Load test scenarios
        test_scenarios = []
        for scenario_id in scenarios:
            scenario = await self.storage_manager.load_scenario(scenario_id)
            if scenario:
                test_scenarios.append(scenario)
        
        if not test_scenarios:
            raise ValueError("No valid test scenarios found")
        
        results = await self.benchmarker.run_performance_benchmark(
            prompt_id, prompt_content, test_scenarios, iterations
        )
        
        # Save results
        await self.storage_manager.save_benchmark_results(results)
        
        return results
    
    # Analytics
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
        # Load test results
        since_date = datetime.now() - timedelta(days=days_back)
        all_results = await self.storage_manager.load_test_results_since(since_date)
        
        return await self.analytics_engine.get_test_analytics(
            all_results, prompt_id, days_back
        )


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


# Export main classes and functions
__all__ = [
    'PromptValidator',
    'TestType',
    'TestStatus',
    'TestScenario',
    'TestResult',
    'ABTestResult',
    'ValidationReport',
    'run_quick_validation',
    'compare_prompts'
]