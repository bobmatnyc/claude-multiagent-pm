"""
Test scenario creation and management functionality.

This module handles the creation, generation, and management of test scenarios
for prompt validation.
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .models import TestScenario


class ScenarioManager:
    """Manages test scenario creation and generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scenario_registry: Dict[str, TestScenario] = {}
        
        # Define scenario templates by agent type
        self.scenario_templates = {
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
            ],
            'Research': [
                {
                    'name': 'Technology Research',
                    'task': 'Research and evaluate new technology options',
                    'expected_outputs': ['analysis', 'comparison', 'recommendations', 'risks'],
                    'criteria': {'depth': 0.4, 'accuracy': 0.3, 'practicality': 0.3}
                },
                {
                    'name': 'Best Practices Analysis',
                    'task': 'Analyze and document best practices',
                    'expected_outputs': ['guidelines', 'examples', 'anti-patterns', 'references'],
                    'criteria': {'relevance': 0.3, 'completeness': 0.4, 'clarity': 0.3}
                }
            ],
            'Security': [
                {
                    'name': 'Security Audit',
                    'task': 'Perform comprehensive security audit',
                    'expected_outputs': ['vulnerabilities', 'severity', 'fixes', 'recommendations'],
                    'criteria': {'thoroughness': 0.5, 'accuracy': 0.3, 'actionability': 0.2}
                },
                {
                    'name': 'Threat Modeling',
                    'task': 'Create threat model for system',
                    'expected_outputs': ['threats', 'mitigations', 'risk_assessment', 'priorities'],
                    'criteria': {'completeness': 0.4, 'practicality': 0.3, 'clarity': 0.3}
                }
            ]
        }
    
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
            
            # Register scenario
            self.scenario_registry[scenario.scenario_id] = scenario
            
            self.logger.info(f"Created test scenario: {scenario.scenario_id}")
            return scenario
            
        except Exception as e:
            self.logger.error(f"Error creating test scenario: {e}")
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
            
            templates = self.scenario_templates.get(agent_type, [])
            
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
    
    def get_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Get a scenario from the registry"""
        return self.scenario_registry.get(scenario_id)
    
    def list_scenarios(self, agent_type: Optional[str] = None) -> List[TestScenario]:
        """List all scenarios, optionally filtered by agent type"""
        scenarios = list(self.scenario_registry.values())
        
        if agent_type:
            scenarios = [s for s in scenarios if s.agent_type == agent_type]
        
        return scenarios
    
    def _generate_scenario_id(self, name: str) -> str:
        """Generate unique scenario ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"scenario_{timestamp}_{hash_val}"
    
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
        elif agent_type == 'Research':
            base_test_data.update({
                'research_depth': 'comprehensive' if complexity_multiplier > 1.0 else 'standard',
                'sources_required': int(5 * complexity_multiplier),
                'comparison_required': True
            })
        elif agent_type == 'Security':
            base_test_data.update({
                'scan_depth': 'deep' if complexity_multiplier > 1.0 else 'standard',
                'exploit_testing': complexity_multiplier > 1.0,
                'compliance_check': True
            })
        
        return base_test_data