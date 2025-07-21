"""
Improvement validation and testing module

This module handles the validation of prompt improvements using A/B testing
and performance metrics.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import logging
import statistics
from typing import Dict, List, Any, Optional

from .models import PromptImprovement, STATUS_APPROVED, STATUS_REJECTED, STATUS_ERROR


class ImprovementValidator:
    """Validates prompt improvements using A/B testing and metrics"""
    
    def __init__(self, improvement_threshold: float = 0.7, 
                 logger: Optional[logging.Logger] = None):
        self.improvement_threshold = improvement_threshold
        self.logger = logger or logging.getLogger(__name__)
        self.evaluation_system = None  # Placeholder until service is available
        
    async def validate_improvements(self, improvements: List[PromptImprovement]) -> List[PromptImprovement]:
        """
        Validate prompt improvements using A/B testing and metrics
        
        Args:
            improvements: List of improvements to validate
            
        Returns:
            List of validated improvements
        """
        validated = []
        
        for improvement in improvements:
            try:
                # Run validation tests
                validation_result = await self._run_validation_test(improvement)
                
                if validation_result['success']:
                    improvement.validation_status = STATUS_APPROVED
                    improvement.effectiveness_score = validation_result['effectiveness']
                    validated.append(improvement)
                else:
                    improvement.validation_status = STATUS_REJECTED
                    improvement.rollback_reason = validation_result.get('reason', 'Validation failed')
                
            except Exception as e:
                self.logger.error(f"Error validating improvement {improvement.improvement_id}: {e}")
                improvement.validation_status = STATUS_ERROR
                improvement.rollback_reason = str(e)
        
        self.logger.info(f"Validated {len(validated)} out of {len(improvements)} improvements")
        return validated
    
    async def _run_validation_test(self, improvement: PromptImprovement) -> Dict[str, Any]:
        """Run validation test for improvement"""
        try:
            # Create test scenarios
            test_scenarios = await self._create_test_scenarios(improvement.agent_type)
            
            # Test original prompt
            original_results = await self._test_prompt_performance(
                improvement.original_prompt, 
                test_scenarios
            )
            
            # Test improved prompt
            improved_results = await self._test_prompt_performance(
                improvement.improved_prompt, 
                test_scenarios
            )
            
            # Calculate effectiveness
            effectiveness = self._calculate_effectiveness(original_results, improved_results)
            
            # Success criteria
            success = effectiveness > self.improvement_threshold
            
            return {
                'success': success,
                'effectiveness': effectiveness,
                'original_score': original_results['average_score'],
                'improved_score': improved_results['average_score'],
                'reason': f"Effectiveness: {effectiveness:.2f}" if success else "Below threshold"
            }
            
        except Exception as e:
            return {
                'success': False,
                'effectiveness': 0.0,
                'reason': f"Validation error: {str(e)}"
            }
    
    async def _create_test_scenarios(self, agent_type: str) -> List[Dict[str, Any]]:
        """Create test scenarios for agent type"""
        scenarios = {
            'Documentation': [
                {'task': 'Generate changelog', 'expected_elements': ['version', 'changes', 'date']},
                {'task': 'Update README', 'expected_elements': ['structure', 'examples', 'usage']},
                {'task': 'API documentation', 'expected_elements': ['endpoints', 'parameters', 'responses']}
            ],
            'QA': [
                {'task': 'Run test suite', 'expected_elements': ['coverage', 'results', 'failures']},
                {'task': 'Validate code', 'expected_elements': ['syntax', 'logic', 'standards']},
                {'task': 'Performance test', 'expected_elements': ['metrics', 'benchmarks', 'analysis']}
            ],
            'Engineer': [
                {'task': 'Implement feature', 'expected_elements': ['code', 'tests', 'documentation']},
                {'task': 'Fix bug', 'expected_elements': ['diagnosis', 'solution', 'prevention']},
                {'task': 'Optimize performance', 'expected_elements': ['analysis', 'improvements', 'metrics']}
            ]
        }
        
        return scenarios.get(agent_type, [
            {'task': 'Generic task', 'expected_elements': ['completion', 'quality', 'documentation']}
        ])
    
    async def _test_prompt_performance(self, prompt: str, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test prompt performance against scenarios"""
        results = []
        
        for scenario in scenarios:
            try:
                # Use evaluation system to test prompt
                if self.evaluation_system:
                    result = await self.evaluation_system.evaluate_prompt(
                        prompt, 
                        scenario['task'], 
                        scenario['expected_elements']
                    )
                else:
                    # Placeholder result when evaluation system is not available
                    result = {
                        'success': True,
                        'score': 0.5,
                        'details': 'Evaluation system not available - placeholder result'
                    }
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error testing scenario: {e}")
                results.append({'score': 0.0, 'error': str(e)})
        
        # Calculate average performance
        scores = [r.get('score', 0.0) for r in results]
        average_score = statistics.mean(scores) if scores else 0.0
        
        return {
            'results': results,
            'average_score': average_score,
            'total_scenarios': len(scenarios),
            'successful_scenarios': len([r for r in results if r.get('score', 0) > 0.5])
        }
    
    def _calculate_effectiveness(self, original: Dict[str, Any], improved: Dict[str, Any]) -> float:
        """Calculate improvement effectiveness"""
        original_score = original.get('average_score', 0.0)
        improved_score = improved.get('average_score', 0.0)
        
        if original_score == 0:
            return 1.0 if improved_score > 0 else 0.0
        
        return (improved_score - original_score) / original_score