"""
Test execution logic for prompt validation.

This module handles the core test execution functionality including
single test runs, concurrent execution, and result collection.
"""

import asyncio
import time
import random
import logging
import concurrent.futures
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from .models import TestScenario, TestResult, TestType, TestStatus


class TestExecutor:
    """Handles test execution and management"""
    
    def __init__(self, max_concurrent_tests: int = 5, default_timeout: int = 300):
        self.max_concurrent_tests = max_concurrent_tests
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)
        self.active_tests: Dict[str, Dict[str, Any]] = {}
    
    def run_single_test(self, 
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
    
    async def run_single_test_async(self, 
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
    
    def run_concurrent_tests(self,
                           prompt_content: str,
                           scenarios: List[TestScenario],
                           test_id_prefix: str) -> List[TestResult]:
        """Run multiple tests concurrently"""
        test_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tests) as executor:
            # Submit all test tasks
            future_to_scenario = {
                executor.submit(self.run_single_test, prompt_content, scenario, f"{test_id_prefix}_{i}"): scenario
                for i, scenario in enumerate(scenarios)
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
                        test_id=f"{test_id_prefix}_error",
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
                    test_results.append(failure_result)
        
        return test_results
    
    def track_active_test(self, test_id: str, test_info: Dict[str, Any]):
        """Track an active test"""
        self.active_tests[test_id] = {
            **test_info,
            'status': TestStatus.RUNNING,
            'start_time': datetime.now()
        }
    
    def update_test_status(self, test_id: str, status: TestStatus, error: Optional[str] = None):
        """Update test status"""
        if test_id in self.active_tests:
            self.active_tests[test_id]['status'] = status
            self.active_tests[test_id]['end_time'] = datetime.now()
            if error:
                self.active_tests[test_id]['error'] = error
    
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