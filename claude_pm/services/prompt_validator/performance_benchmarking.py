"""
Performance benchmarking functionality for prompt validation.

This module provides performance benchmarking capabilities to measure
and analyze prompt execution performance across multiple iterations.
"""

import time
import statistics
import logging
from typing import Dict, List, Any
from datetime import datetime

from .models import TestScenario
from .test_execution import TestExecutor


class PerformanceBenchmarker:
    """Handles performance benchmarking for prompts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.executor = TestExecutor()
    
    async def run_performance_benchmark(self, 
                                       prompt_id: str,
                                       prompt_content: str,
                                       scenarios: List[TestScenario],
                                       iterations: int = 10) -> Dict[str, Any]:
        """
        Run performance benchmark test
        
        Args:
            prompt_id: Prompt identifier
            prompt_content: Prompt content
            scenarios: List of test scenarios
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
            
            for scenario in scenarios:
                scenario_results = await self._benchmark_scenario(
                    prompt_content, scenario, iterations, prompt_id
                )
                
                # Calculate scenario performance metrics
                scenario_metrics = self._calculate_scenario_metrics(scenario_results)
                scenario_metrics['scenario_id'] = scenario.scenario_id
                scenario_metrics['results'] = scenario_results
                
                benchmark_results['results'].append(scenario_metrics)
            
            # Calculate overall performance metrics
            benchmark_results['performance_metrics'] = self._calculate_overall_metrics(
                benchmark_results['results']
            )
            
            return benchmark_results
            
        except Exception as e:
            self.logger.error(f"Error running performance benchmark: {e}")
            raise
    
    async def _benchmark_scenario(self,
                                 prompt_content: str,
                                 scenario: TestScenario,
                                 iterations: int,
                                 prompt_id: str) -> List[Dict[str, Any]]:
        """Benchmark a single scenario"""
        scenario_results = []
        
        for i in range(iterations):
            start_time = time.time()
            result = await self.executor.run_single_test_async(
                prompt_content, 
                scenario, 
                f"{prompt_id}_perf_{scenario.scenario_id}_{i}"
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
        
        return scenario_results
    
    def _calculate_scenario_metrics(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for a single scenario"""
        execution_times = [r['execution_time'] for r in scenario_results]
        success_rate = len([r for r in scenario_results if r['success']]) / len(scenario_results)
        
        metrics = {
            'avg_execution_time': statistics.mean(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'std_execution_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'success_rate': success_rate,
            'throughput': 1.0 / statistics.mean(execution_times) if execution_times else 0,
        }
        
        # Add percentiles
        if len(execution_times) >= 10:
            sorted_times = sorted(execution_times)
            metrics['p50_execution_time'] = sorted_times[len(sorted_times) // 2]
            metrics['p95_execution_time'] = sorted_times[int(len(sorted_times) * 0.95)]
            metrics['p99_execution_time'] = sorted_times[int(len(sorted_times) * 0.99)]
        
        return metrics
    
    def _calculate_overall_metrics(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall performance metrics across all scenarios"""
        all_execution_times = []
        all_success_rates = []
        
        for scenario_result in scenario_results:
            all_execution_times.append(scenario_result['avg_execution_time'])
            all_success_rates.append(scenario_result['success_rate'])
        
        overall_metrics = {
            'overall_avg_execution_time': statistics.mean(all_execution_times) if all_execution_times else 0,
            'overall_success_rate': statistics.mean(all_success_rates) if all_success_rates else 0,
            'overall_throughput': sum(1.0 / t for t in all_execution_times) if all_execution_times else 0,
            'consistency_score': self._calculate_consistency_score(all_execution_times)
        }
        
        # Performance rating
        overall_metrics['performance_rating'] = self._calculate_performance_rating(overall_metrics)
        
        return overall_metrics
    
    def _calculate_consistency_score(self, execution_times: List[float]) -> float:
        """Calculate consistency score (0-1, higher is better)"""
        if not execution_times or len(execution_times) < 2:
            return 1.0
        
        mean_time = statistics.mean(execution_times)
        if mean_time == 0:
            return 1.0
        
        std_time = statistics.stdev(execution_times)
        # Lower coefficient of variation means more consistent
        cv = std_time / mean_time
        # Convert to 0-1 score where 1 is most consistent
        return max(0, 1.0 - cv)
    
    def _calculate_performance_rating(self, metrics: Dict[str, Any]) -> str:
        """Calculate overall performance rating"""
        score = 0
        
        # Success rate component (40%)
        score += metrics['overall_success_rate'] * 0.4
        
        # Speed component (30%) - normalize to 0-1
        # Assume <1s is excellent, >5s is poor
        avg_time = metrics['overall_avg_execution_time']
        if avg_time < 1.0:
            score += 0.3
        elif avg_time < 2.0:
            score += 0.2
        elif avg_time < 5.0:
            score += 0.1
        
        # Consistency component (30%)
        score += metrics['consistency_score'] * 0.3
        
        # Rating
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Average"
        else:
            return "Poor"