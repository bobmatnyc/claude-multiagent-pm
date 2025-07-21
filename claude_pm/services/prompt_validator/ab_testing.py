"""
A/B testing functionality for prompt comparison.

This module provides comprehensive A/B testing capabilities for comparing
two prompts, including statistical significance calculation and winner determination.
"""

import statistics
import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import TestScenario, TestResult, ABTestResult
from .test_execution import TestExecutor
from .utils import generate_ab_test_id


class ABTester:
    """Handles A/B testing between prompts"""
    
    def __init__(self, 
                 significance_threshold: float = 0.05,
                 min_sample_size: int = 10):
        self.significance_threshold = significance_threshold
        self.min_sample_size = min_sample_size
        self.logger = logging.getLogger(__name__)
        self.executor = TestExecutor()
    
    async def run_ab_test(self, 
                         prompt_a_id: str,
                         prompt_a_content: str,
                         prompt_b_id: str,
                         prompt_b_content: str,
                         scenarios: List[TestScenario],
                         sample_size: Optional[int] = None) -> ABTestResult:
        """
        Run A/B test between two prompts
        
        Args:
            prompt_a_id: First prompt identifier
            prompt_a_content: First prompt content
            prompt_b_id: Second prompt identifier
            prompt_b_content: Second prompt content
            scenarios: List of test scenarios
            sample_size: Number of tests per prompt (optional)
            
        Returns:
            A/B test result
        """
        try:
            test_id = generate_ab_test_id(prompt_a_id, prompt_b_id)
            
            # Track active test
            self.executor.track_active_test(test_id, {
                'type': 'ab_test',
                'prompt_a_id': prompt_a_id,
                'prompt_b_id': prompt_b_id,
                'scenarios': [s.scenario_id for s in scenarios]
            })
            
            # Determine sample size
            if sample_size is None:
                sample_size = max(self.min_sample_size, len(scenarios))
            
            # Run tests for both prompts
            prompt_a_results = await self._run_prompt_tests(
                prompt_a_content, scenarios, sample_size, f"{test_id}_a"
            )
            
            prompt_b_results = await self._run_prompt_tests(
                prompt_b_content, scenarios, sample_size, f"{test_id}_b"
            )
            
            # Calculate statistical significance
            significance = self._calculate_statistical_significance(prompt_a_results, prompt_b_results)
            
            # Determine winner
            winner = self._determine_winner(prompt_a_results, prompt_b_results, significance)
            
            # Calculate confidence level
            confidence_level = 1 - significance
            
            # Calculate improvement metrics
            improvement_metrics = self._calculate_improvement_metrics(prompt_a_results, prompt_b_results)
            
            # Create A/B test result
            ab_result = ABTestResult(
                test_id=test_id,
                prompt_a_id=prompt_a_id,
                prompt_b_id=prompt_b_id,
                scenarios_tested=len(scenarios),
                prompt_a_results=prompt_a_results,
                prompt_b_results=prompt_b_results,
                statistical_significance=significance,
                winner=winner,
                confidence_level=confidence_level,
                improvement_metrics=improvement_metrics,
                timestamp=datetime.now()
            )
            
            # Update test status
            self.executor.update_test_status(test_id, "completed")
            
            self.logger.info(f"A/B test completed: {test_id} - Winner: {winner or 'No significant difference'}")
            return ab_result
            
        except Exception as e:
            self.logger.error(f"Error running A/B test: {e}")
            if 'test_id' in locals():
                self.executor.update_test_status(test_id, "failed", str(e))
            raise
    
    async def _run_prompt_tests(self,
                               prompt_content: str,
                               scenarios: List[TestScenario],
                               sample_size: int,
                               test_id_prefix: str) -> List[TestResult]:
        """Run tests for a single prompt"""
        results = []
        
        for i in range(sample_size):
            scenario = random.choice(scenarios)
            result = await self.executor.run_single_test_async(
                prompt_content, scenario, f"{test_id_prefix}_{i}"
            )
            results.append(result)
        
        return results
    
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
    
    def _determine_winner(self,
                         results_a: List[TestResult],
                         results_b: List[TestResult],
                         significance: float) -> Optional[str]:
        """Determine the winner based on results and significance"""
        if significance >= self.significance_threshold:
            return None  # No significant difference
        
        # Calculate mean scores
        a_scores = [r.score for r in results_a if r.success]
        b_scores = [r.score for r in results_b if r.success]
        
        a_mean = statistics.mean(a_scores) if a_scores else 0.0
        b_mean = statistics.mean(b_scores) if b_scores else 0.0
        
        if a_mean > b_mean:
            return "prompt_a"
        elif b_mean > a_mean:
            return "prompt_b"
        else:
            return None
    
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