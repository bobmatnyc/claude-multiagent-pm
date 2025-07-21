"""
Pipeline stage implementations for the prompt improvement pipeline.

This module contains the implementations for each stage of the pipeline,
including correction analysis, pattern detection, improvement generation,
validation, deployment, and monitoring setup.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from claude_pm.services.correction_capture import CorrectionCapture
from claude_pm.services.pattern_analyzer import PatternAnalyzer
from claude_pm.services.prompt_improver import PromptImprover
from claude_pm.services.template_manager import TemplateManager as PromptTemplateManager
from claude_pm.services.prompt_validator import PromptValidator

from .types import PipelineExecution


class StageHandlers:
    """Handles execution of individual pipeline stages"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.correction_capture = CorrectionCapture()
        self.pattern_analyzer = PatternAnalyzer()
        self.prompt_improver = PromptImprover()
        self.template_manager = PromptTemplateManager()
        self.validator = PromptValidator()
    
    async def run_correction_analysis(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Run correction analysis stage"""
        try:
            results = {}
            
            for agent_type in execution.config.agent_types:
                corrections = await self.correction_capture.get_corrections_for_agent(
                    agent_type, 
                    days_back=execution.config.correction_analysis_days
                )
                
                results[agent_type] = {
                    'corrections_found': len(corrections),
                    'corrections': [asdict(c) for c in corrections]
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Correction analysis failed: {e}")
            raise
    
    async def run_pattern_detection(self, 
                                   execution: PipelineExecution,
                                   correction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run pattern detection stage"""
        try:
            results = {}
            
            for agent_type in execution.config.agent_types:
                if agent_type in correction_results:
                    # Convert corrections back to objects (simplified)
                    corrections = correction_results[agent_type]['corrections']
                    
                    # Analyze patterns
                    patterns = await self.pattern_analyzer.analyze_correction_patterns(
                        corrections, 
                        agent_type
                    )
                    
                    # Filter by confidence threshold
                    significant_patterns = [
                        p for p in patterns 
                        if p.confidence >= execution.config.pattern_detection_threshold
                    ]
                    
                    results[agent_type] = {
                        'patterns_detected': len(patterns),
                        'significant_patterns': len(significant_patterns),
                        'patterns': [asdict(p) for p in significant_patterns]
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")
            raise
    
    async def run_improvement_generation(self, 
                                        execution: PipelineExecution,
                                        pattern_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run improvement generation stage"""
        try:
            results = {}
            total_improvements = 0
            
            for agent_type in execution.config.agent_types:
                if agent_type in pattern_results:
                    # Convert patterns back to objects (simplified)
                    pattern_data = pattern_results[agent_type]['patterns']
                    
                    # Generate improvements
                    improvements = await self.prompt_improver.generate_prompt_improvements(pattern_data)
                    
                    # Filter by confidence threshold
                    confident_improvements = [
                        i for i in improvements 
                        if i.confidence_score >= execution.config.improvement_confidence_threshold
                    ]
                    
                    results[agent_type] = {
                        'improvements_generated': len(improvements),
                        'confident_improvements': len(confident_improvements),
                        'improvements': [asdict(i) for i in confident_improvements]
                    }
                    
                    total_improvements += len(confident_improvements)
            
            results['total_improvements'] = total_improvements
            return results
            
        except Exception as e:
            self.logger.error(f"Improvement generation failed: {e}")
            raise
    
    async def run_validation(self, 
                            execution: PipelineExecution,
                            improvement_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation stage"""
        try:
            results = {}
            
            for agent_type in execution.config.agent_types:
                if agent_type in improvement_results:
                    improvements = improvement_results[agent_type]['improvements']
                    
                    # Validate improvements
                    validated_improvements = []
                    
                    for improvement_data in improvements:
                        # Run validation test
                        validation_result = await self._validate_single_improvement(
                            improvement_data, 
                            execution.config.validation_sample_size,
                            agent_type
                        )
                        
                        if validation_result['approved']:
                            validated_improvements.append({
                                **improvement_data,
                                'validation_result': validation_result
                            })
                    
                    results[agent_type] = {
                        'improvements_tested': len(improvements),
                        'improvements_validated': len(validated_improvements),
                        'validation_rate': len(validated_improvements) / len(improvements) if improvements else 0.0,
                        'validated_improvements': validated_improvements
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            raise
    
    async def run_deployment(self, 
                            execution: PipelineExecution,
                            validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run deployment stage"""
        try:
            results = {
                'deployed_count': 0,
                'failed_deployments': 0,
                'deployment_details': {}
            }
            
            for agent_type in execution.config.agent_types:
                if agent_type in validation_results:
                    validated_improvements = validation_results[agent_type]['validated_improvements']
                    
                    agent_deployments = {
                        'attempted': 0,
                        'successful': 0,
                        'failed': 0
                    }
                    
                    for improvement in validated_improvements:
                        agent_deployments['attempted'] += 1
                        
                        try:
                            # Deploy improvement
                            deployment_result = await self._deploy_improvement(improvement, agent_type)
                            
                            if deployment_result['success']:
                                agent_deployments['successful'] += 1
                                results['deployed_count'] += 1
                            else:
                                agent_deployments['failed'] += 1
                                results['failed_deployments'] += 1
                            
                        except Exception as e:
                            self.logger.error(f"Deployment failed for {agent_type}: {e}")
                            agent_deployments['failed'] += 1
                            results['failed_deployments'] += 1
                    
                    results['deployment_details'][agent_type] = agent_deployments
            
            return results
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            raise
    
    async def setup_monitoring(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Setup monitoring for deployed improvements"""
        try:
            monitoring_setup = {
                'monitoring_enabled': True,
                'monitoring_interval': execution.config.monitoring_interval,
                'metrics_to_track': [
                    'success_rate',
                    'response_quality',
                    'execution_time',
                    'error_rate'
                ],
                'alert_thresholds': {
                    'success_rate_min': 0.8,
                    'response_quality_min': 0.7,
                    'execution_time_max': 30.0,
                    'error_rate_max': 0.1
                }
            }
            
            # Schedule monitoring tasks (implementation would integrate with task scheduler)
            monitoring_setup['scheduled_tasks'] = []
            
            return monitoring_setup
            
        except Exception as e:
            self.logger.error(f"Monitoring setup failed: {e}")
            raise
    
    async def run_targeted_improvement(self, 
                                     execution_id: str,
                                     agent_type: str,
                                     specific_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run targeted improvement for specific agent and patterns"""
        try:
            self.logger.info(f"Starting targeted improvement for {agent_type}")
            
            # Get recent corrections for agent
            corrections = await self.correction_capture.get_corrections_for_agent(agent_type, days_back=14)
            
            # Analyze patterns
            patterns = await self.pattern_analyzer.analyze_correction_patterns(corrections, agent_type)
            
            # Filter patterns if specified
            if specific_patterns:
                patterns = [p for p in patterns if p.pattern_id in specific_patterns]
            
            # Generate improvements
            improvements = await self.prompt_improver.generate_prompt_improvements(patterns)
            
            # Validate improvements
            validated_improvements = await self.prompt_improver.validate_improvements(improvements)
            
            # Create summary
            results = {
                'execution_id': execution_id,
                'agent_type': agent_type,
                'patterns_analyzed': len(patterns),
                'improvements_generated': len(improvements),
                'improvements_validated': len(validated_improvements),
                'patterns': [asdict(p) for p in patterns],
                'improvements': [asdict(i) for i in improvements],
                'validated_improvements': [asdict(v) for v in validated_improvements],
                'timestamp': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Targeted improvement failed for {agent_type}: {e}")
            raise
    
    async def _validate_single_improvement(self, 
                                         improvement_data: Dict[str, Any],
                                         sample_size: int,
                                         agent_type: str) -> Dict[str, Any]:
        """Validate a single improvement"""
        try:
            # Generate test scenarios
            scenarios = await self.validator.generate_test_scenarios(agent_type, "medium", 3)
            
            # Run validation
            report = await self.validator.run_validation_test(
                prompt_id=improvement_data['improvement_id'],
                prompt_content=improvement_data['improved_prompt'],
                scenarios=[s.scenario_id for s in scenarios]
            )
            
            # Determine approval
            approved = (report.overall_score >= 0.7 and 
                       report.passed_tests / report.total_tests >= 0.8)
            
            return {
                'approved': approved,
                'overall_score': report.overall_score,
                'success_rate': report.passed_tests / report.total_tests,
                'recommendations': report.recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Improvement validation failed: {e}")
            return {
                'approved': False,
                'error': str(e)
            }
    
    async def _deploy_improvement(self, 
                                improvement: Dict[str, Any],
                                agent_type: str) -> Dict[str, Any]:
        """Deploy a single improvement"""
        try:
            # Create template version
            template_version = await self.template_manager.create_template(
                template_id=f"{agent_type}_improved_{improvement['improvement_id'][:8]}",
                content=improvement['improved_prompt'],
                template_type=self.template_manager.TemplateType.AGENT_PROMPT,
                agent_type=agent_type,
                author="pipeline_system"
            )
            
            # Deploy to agent
            deployment = await self.template_manager.deploy_template(
                template_id=template_version.template_id,
                version=template_version.version,
                target_agents=[agent_type]
            )
            
            return {
                'success': deployment.status == "deployed",
                'template_id': template_version.template_id,
                'deployment_id': deployment.deployment_id
            }
            
        except Exception as e:
            self.logger.error(f"Improvement deployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }