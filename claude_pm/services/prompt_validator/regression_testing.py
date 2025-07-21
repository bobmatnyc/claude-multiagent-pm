"""
Regression testing functionality for prompt validation.

This module provides regression testing capabilities to detect performance
degradation between prompt versions.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from .models import TestScenario, ABTestResult
from .ab_testing import ABTester


class RegressionTester:
    """Handles regression testing between prompt versions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ab_tester = ABTester()
    
    async def run_regression_test(self, 
                                 prompt_id: str,
                                 current_content: str,
                                 previous_content: str,
                                 scenarios: List[TestScenario]) -> Dict[str, Any]:
        """
        Run regression test to compare current vs previous prompt
        
        Args:
            prompt_id: Prompt identifier
            current_content: Current prompt content
            previous_content: Previous prompt content
            scenarios: List of test scenarios
            
        Returns:
            Regression test results
        """
        try:
            # Run A/B test between current and previous
            ab_result = await self.ab_tester.run_ab_test(
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