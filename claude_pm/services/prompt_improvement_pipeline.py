"""
Prompt Improvement Pipeline Integration Service

This module integrates all components of the prompt improvement pipeline
including correction capture, pattern analysis, prompt improvement, template
management, and validation.

Key Features:
- End-to-end pipeline orchestration
- Automated improvement workflows
- Pipeline monitoring and health checks
- Result aggregation and reporting
- Integration with agent training system
- Performance optimization

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from pathlib import Path
import time

from claude_pm.services.correction_capture import CorrectionCapture
from claude_pm.services.pattern_analyzer import PatternAnalyzer
from claude_pm.services.prompt_improver import PromptImprover
from claude_pm.services.prompt_template_manager import PromptTemplateManager
from claude_pm.services.prompt_validator import PromptValidator


class PipelineStage(Enum):
    """Pipeline execution stages"""
    CORRECTION_ANALYSIS = "correction_analysis"
    PATTERN_DETECTION = "pattern_detection"
    IMPROVEMENT_GENERATION = "improvement_generation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    agent_types: List[str]
    correction_analysis_days: int = 30
    pattern_detection_threshold: float = 0.7
    improvement_confidence_threshold: float = 0.8
    validation_sample_size: int = 10
    auto_deployment_enabled: bool = False
    monitoring_interval: int = 3600  # seconds
    pipeline_timeout: int = 7200  # seconds


@dataclass
class PipelineExecution:
    """Pipeline execution record"""
    execution_id: str
    config: PipelineConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.IDLE
    current_stage: Optional[PipelineStage] = None
    stage_results: Dict[str, Any] = None
    total_improvements: int = 0
    deployed_improvements: int = 0
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = None


@dataclass
class PipelineResults:
    """Comprehensive pipeline results"""
    execution_id: str
    agent_results: Dict[str, Any]
    improvement_summary: Dict[str, Any]
    validation_summary: Dict[str, Any]
    deployment_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime


class PromptImprovementPipeline:
    """
    Comprehensive prompt improvement pipeline orchestration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.correction_capture = CorrectionCapture()
        self.pattern_analyzer = PatternAnalyzer()
        self.prompt_improver = PromptImprover()
        self.template_manager = PromptTemplateManager()
        self.validator = PromptValidator()
        
        # Configuration
        self.pipeline_config = PipelineConfig(
            agent_types=self.config.get('agent_types', ['Documentation', 'QA', 'Engineer', 'Ops']),
            correction_analysis_days=self.config.get('correction_analysis_days', 30),
            pattern_detection_threshold=self.config.get('pattern_detection_threshold', 0.7),
            improvement_confidence_threshold=self.config.get('improvement_confidence_threshold', 0.8),
            validation_sample_size=self.config.get('validation_sample_size', 10),
            auto_deployment_enabled=self.config.get('auto_deployment_enabled', False),
            monitoring_interval=self.config.get('monitoring_interval', 3600),
            pipeline_timeout=self.config.get('pipeline_timeout', 7200)
        )
        
        # Storage
        self.base_path = Path(self.config.get('base_path', '.claude-pm/improvement_pipeline'))
        self.executions_path = self.base_path / 'executions'
        self.results_path = self.base_path / 'results'
        self.monitoring_path = self.base_path / 'monitoring'
        
        # Create directories
        for path in [self.executions_path, self.results_path, self.monitoring_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Pipeline state
        self.active_executions: Dict[str, PipelineExecution] = {}
        self.pipeline_metrics: Dict[str, Any] = {}
        
        self.logger.info("PromptImprovementPipeline initialized successfully")
    
    async def run_full_pipeline(self, 
                              agent_types: Optional[List[str]] = None,
                              custom_config: Optional[Dict] = None) -> PipelineResults:
        """
        Run the complete prompt improvement pipeline
        
        Args:
            agent_types: Specific agent types to process (optional)
            custom_config: Custom configuration for this execution
            
        Returns:
            Complete pipeline results
        """
        execution_id = self._generate_execution_id()
        
        try:
            # Setup execution
            execution = PipelineExecution(
                execution_id=execution_id,
                config=self._merge_config(custom_config),
                start_time=datetime.now(),
                status=PipelineStatus.RUNNING,
                stage_results={}
            )
            
            if agent_types:
                execution.config.agent_types = agent_types
            
            # Track execution
            self.active_executions[execution_id] = execution
            
            # Stage 1: Correction Analysis
            execution.current_stage = PipelineStage.CORRECTION_ANALYSIS
            await self._update_execution_status(execution)
            
            correction_results = await self._run_correction_analysis(execution)
            execution.stage_results['correction_analysis'] = correction_results
            
            # Stage 2: Pattern Detection
            execution.current_stage = PipelineStage.PATTERN_DETECTION
            await self._update_execution_status(execution)
            
            pattern_results = await self._run_pattern_detection(execution, correction_results)
            execution.stage_results['pattern_detection'] = pattern_results
            
            # Stage 3: Improvement Generation
            execution.current_stage = PipelineStage.IMPROVEMENT_GENERATION
            await self._update_execution_status(execution)
            
            improvement_results = await self._run_improvement_generation(execution, pattern_results)
            execution.stage_results['improvement_generation'] = improvement_results
            
            # Stage 4: Validation
            execution.current_stage = PipelineStage.VALIDATION
            await self._update_execution_status(execution)
            
            validation_results = await self._run_validation(execution, improvement_results)
            execution.stage_results['validation'] = validation_results
            
            # Stage 5: Deployment (if enabled)
            if execution.config.auto_deployment_enabled:
                execution.current_stage = PipelineStage.DEPLOYMENT
                await self._update_execution_status(execution)
                
                deployment_results = await self._run_deployment(execution, validation_results)
                execution.stage_results['deployment'] = deployment_results
                execution.deployed_improvements = deployment_results.get('deployed_count', 0)
            
            # Stage 6: Monitoring Setup
            execution.current_stage = PipelineStage.MONITORING
            await self._update_execution_status(execution)
            
            monitoring_results = await self._setup_monitoring(execution)
            execution.stage_results['monitoring'] = monitoring_results
            
            # Complete execution
            execution.status = PipelineStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.total_improvements = improvement_results.get('total_improvements', 0)
            execution.performance_metrics = self._calculate_execution_metrics(execution)
            
            # Generate comprehensive results
            results = await self._generate_pipeline_results(execution)
            
            # Save results
            await self._save_pipeline_results(results)
            await self._save_execution_record(execution)
            
            # Clean up
            self.active_executions.pop(execution_id, None)
            
            self.logger.info(f"Pipeline execution completed: {execution_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            
            # Update execution status
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = PipelineStatus.FAILED
                execution.error_message = str(e)
                execution.end_time = datetime.now()
                await self._save_execution_record(execution)
                self.active_executions.pop(execution_id, None)
            
            raise
    
    async def run_targeted_improvement(self, 
                                     agent_type: str,
                                     specific_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run targeted improvement for specific agent type and patterns
        
        Args:
            agent_type: Target agent type
            specific_patterns: Specific patterns to address (optional)
            
        Returns:
            Targeted improvement results
        """
        try:
            execution_id = self._generate_execution_id()
            
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
    
    async def monitor_pipeline_health(self) -> Dict[str, Any]:
        """
        Monitor pipeline health and performance
        
        Returns:
            Health monitoring results
        """
        try:
            health_status = {
                'pipeline_status': 'healthy',
                'active_executions': len(self.active_executions),
                'component_health': {},
                'recent_performance': {},
                'alerts': [],
                'recommendations': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Check component health
            components = {
                'correction_capture': self.correction_capture,
                'pattern_analyzer': self.pattern_analyzer,
                'prompt_improver': self.prompt_improver,
                'template_manager': self.template_manager,
                'validator': self.validator
            }
            
            for component_name, component in components.items():
                try:
                    # Basic health check - check if component is responsive
                    if hasattr(component, 'health_check'):
                        health = await component.health_check()
                    else:
                        health = {'status': 'healthy', 'message': 'Component responsive'}
                    
                    health_status['component_health'][component_name] = health
                    
                except Exception as e:
                    health_status['component_health'][component_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    health_status['pipeline_status'] = 'degraded'
                    health_status['alerts'].append(f"Component {component_name} is unhealthy: {str(e)}")
            
            # Check recent performance
            recent_executions = await self._get_recent_executions(hours_back=24)
            
            if recent_executions:
                success_rate = len([e for e in recent_executions if e.status == PipelineStatus.COMPLETED]) / len(recent_executions)
                avg_execution_time = statistics.mean([
                    (e.end_time - e.start_time).total_seconds() 
                    for e in recent_executions 
                    if e.end_time
                ])
                
                health_status['recent_performance'] = {
                    'executions_24h': len(recent_executions),
                    'success_rate': success_rate,
                    'avg_execution_time': avg_execution_time,
                    'failed_executions': len([e for e in recent_executions if e.status == PipelineStatus.FAILED])
                }
                
                # Generate alerts
                if success_rate < 0.8:
                    health_status['alerts'].append("Low success rate in recent executions")
                    health_status['pipeline_status'] = 'degraded'
                
                if avg_execution_time > 3600:  # 1 hour
                    health_status['alerts'].append("High average execution time")
                    health_status['recommendations'].append("Consider optimizing pipeline performance")
            
            # Check active executions for issues
            for execution_id, execution in self.active_executions.items():
                runtime = (datetime.now() - execution.start_time).total_seconds()
                
                if runtime > self.pipeline_config.pipeline_timeout:
                    health_status['alerts'].append(f"Execution {execution_id} has exceeded timeout")
                    health_status['pipeline_status'] = 'degraded'
                    health_status['recommendations'].append("Review long-running executions")
            
            # Save health status
            await self._save_health_status(health_status)
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health monitoring failed: {e}")
            return {
                'pipeline_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_pipeline_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive pipeline analytics
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Pipeline analytics data
        """
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Load execution history
            executions = await self._get_executions_since(since_date)
            
            # Calculate analytics
            analytics = {
                'period': {
                    'days_back': days_back,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'execution_summary': {
                    'total_executions': len(executions),
                    'successful_executions': len([e for e in executions if e.status == PipelineStatus.COMPLETED]),
                    'failed_executions': len([e for e in executions if e.status == PipelineStatus.FAILED]),
                    'success_rate': 0.0,
                    'avg_execution_time': 0.0
                },
                'improvement_metrics': {
                    'total_improvements_generated': 0,
                    'total_improvements_deployed': 0,
                    'deployment_rate': 0.0,
                    'avg_improvements_per_execution': 0.0
                },
                'agent_performance': {},
                'trend_analysis': {},
                'recommendations': []
            }
            
            if executions:
                # Calculate execution metrics
                successful_executions = [e for e in executions if e.status == PipelineStatus.COMPLETED]
                analytics['execution_summary']['success_rate'] = len(successful_executions) / len(executions)
                
                if successful_executions:
                    execution_times = [
                        (e.end_time - e.start_time).total_seconds()
                        for e in successful_executions
                        if e.end_time
                    ]
                    
                    if execution_times:
                        analytics['execution_summary']['avg_execution_time'] = statistics.mean(execution_times)
                
                # Calculate improvement metrics
                total_improvements = sum(e.total_improvements for e in executions)
                total_deployed = sum(e.deployed_improvements for e in executions)
                
                analytics['improvement_metrics']['total_improvements_generated'] = total_improvements
                analytics['improvement_metrics']['total_improvements_deployed'] = total_deployed
                
                if total_improvements > 0:
                    analytics['improvement_metrics']['deployment_rate'] = total_deployed / total_improvements
                
                if executions:
                    analytics['improvement_metrics']['avg_improvements_per_execution'] = total_improvements / len(executions)
                
                # Analyze agent performance
                agent_stats = {}
                for execution in executions:
                    for agent_type in execution.config.agent_types:
                        if agent_type not in agent_stats:
                            agent_stats[agent_type] = {
                                'executions': 0,
                                'improvements': 0,
                                'deployments': 0
                            }
                        
                        agent_stats[agent_type]['executions'] += 1
                        # Note: This would need more detailed tracking per agent
                
                analytics['agent_performance'] = agent_stats
                
                # Trend analysis
                analytics['trend_analysis'] = self._calculate_pipeline_trends(executions)
                
                # Generate recommendations
                analytics['recommendations'] = self._generate_pipeline_recommendations(analytics)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting pipeline analytics: {e}")
            return {'error': str(e)}
    
    async def pause_pipeline(self, execution_id: str) -> bool:
        """Pause a running pipeline execution"""
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = PipelineStatus.PAUSED
            await self._update_execution_status(execution)
            
            self.logger.info(f"Paused pipeline execution: {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing pipeline {execution_id}: {e}")
            return False
    
    async def resume_pipeline(self, execution_id: str) -> bool:
        """Resume a paused pipeline execution"""
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            if execution.status != PipelineStatus.PAUSED:
                return False
            
            execution.status = PipelineStatus.RUNNING
            await self._update_execution_status(execution)
            
            self.logger.info(f"Resumed pipeline execution: {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming pipeline {execution_id}: {e}")
            return False
    
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """Cancel a running pipeline execution"""
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = PipelineStatus.FAILED
            execution.error_message = "Cancelled by user"
            execution.end_time = datetime.now()
            
            await self._save_execution_record(execution)
            self.active_executions.pop(execution_id, None)
            
            self.logger.info(f"Cancelled pipeline execution: {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling pipeline {execution_id}: {e}")
            return False
    
    # Private methods - Pipeline stages
    async def _run_correction_analysis(self, execution: PipelineExecution) -> Dict[str, Any]:
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
    
    async def _run_pattern_detection(self, 
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
    
    async def _run_improvement_generation(self, 
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
    
    async def _run_validation(self, 
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
                            execution.config.validation_sample_size
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
    
    async def _run_deployment(self, 
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
    
    async def _setup_monitoring(self, execution: PipelineExecution) -> Dict[str, Any]:
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
            
            # Schedule monitoring tasks
            await self._schedule_monitoring_tasks(execution.execution_id, monitoring_setup)
            
            return monitoring_setup
            
        except Exception as e:
            self.logger.error(f"Monitoring setup failed: {e}")
            raise
    
    # Private methods - Utilities
    async def _validate_single_improvement(self, 
                                         improvement_data: Dict[str, Any],
                                         sample_size: int) -> Dict[str, Any]:
        """Validate a single improvement"""
        try:
            # Generate test scenarios
            agent_type = improvement_data.get('agent_type', 'Engineer')
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
    
    async def _schedule_monitoring_tasks(self, 
                                       execution_id: str,
                                       monitoring_setup: Dict[str, Any]):
        """Schedule monitoring tasks for execution"""
        try:
            # This would integrate with a task scheduler
            # For now, save monitoring configuration
            monitoring_file = self.monitoring_path / f"{execution_id}_monitoring.json"
            
            with open(monitoring_file, 'w') as f:
                json.dump({
                    'execution_id': execution_id,
                    'monitoring_setup': monitoring_setup,
                    'created_at': datetime.now().isoformat()
                }, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to schedule monitoring tasks: {e}")
    
    def _calculate_pipeline_trends(self, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """Calculate pipeline trends from execution history"""
        try:
            if not executions:
                return {}
            
            # Sort by start time
            sorted_executions = sorted(executions, key=lambda e: e.start_time)
            
            # Calculate success rate trend
            success_rates = []
            for execution in sorted_executions:
                success_rates.append(1.0 if execution.status == PipelineStatus.COMPLETED else 0.0)
            
            # Calculate improvement generation trend
            improvement_counts = [e.total_improvements for e in sorted_executions]
            
            return {
                'success_rate_trend': {
                    'direction': 'improving' if success_rates[-1] > success_rates[0] else 'declining',
                    'current_rate': success_rates[-1] if success_rates else 0.0,
                    'average_rate': statistics.mean(success_rates) if success_rates else 0.0
                },
                'improvement_generation_trend': {
                    'direction': 'increasing' if improvement_counts[-1] > improvement_counts[0] else 'decreasing',
                    'current_count': improvement_counts[-1] if improvement_counts else 0,
                    'average_count': statistics.mean(improvement_counts) if improvement_counts else 0.0
                },
                'execution_frequency': len(executions) / 30  # executions per day (assuming 30 days)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating pipeline trends: {e}")
            return {}
    
    def _generate_pipeline_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        try:
            # Success rate recommendations
            success_rate = analytics['execution_summary']['success_rate']
            if success_rate < 0.8:
                recommendations.append("Pipeline success rate is below 80% - investigate common failure causes")
            
            # Execution time recommendations
            avg_time = analytics['execution_summary']['avg_execution_time']
            if avg_time > 3600:  # 1 hour
                recommendations.append("Average execution time is high - consider pipeline optimization")
            
            # Deployment rate recommendations
            deployment_rate = analytics['improvement_metrics']['deployment_rate']
            if deployment_rate < 0.5:
                recommendations.append("Low deployment rate - review validation criteria and approval process")
            
            # Improvement generation recommendations
            avg_improvements = analytics['improvement_metrics']['avg_improvements_per_execution']
            if avg_improvements < 2:
                recommendations.append("Low improvement generation - review pattern detection thresholds")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    async def _generate_pipeline_results(self, execution: PipelineExecution) -> PipelineResults:
        """Generate comprehensive pipeline results"""
        try:
            # Aggregate results by agent type
            agent_results = {}
            for agent_type in execution.config.agent_types:
                agent_results[agent_type] = {
                    'corrections': execution.stage_results.get('correction_analysis', {}).get(agent_type, {}),
                    'patterns': execution.stage_results.get('pattern_detection', {}).get(agent_type, {}),
                    'improvements': execution.stage_results.get('improvement_generation', {}).get(agent_type, {}),
                    'validation': execution.stage_results.get('validation', {}).get(agent_type, {}),
                    'deployment': execution.stage_results.get('deployment', {}).get('deployment_details', {}).get(agent_type, {})
                }
            
            # Generate summaries
            improvement_summary = {
                'total_improvements': execution.total_improvements,
                'deployed_improvements': execution.deployed_improvements,
                'deployment_rate': execution.deployed_improvements / execution.total_improvements if execution.total_improvements > 0 else 0.0
            }
            
            validation_summary = {}
            deployment_summary = execution.stage_results.get('deployment', {})
            
            # Generate recommendations
            recommendations = self._generate_execution_recommendations(execution)
            
            return PipelineResults(
                execution_id=execution.execution_id,
                agent_results=agent_results,
                improvement_summary=improvement_summary,
                validation_summary=validation_summary,
                deployment_summary=deployment_summary,
                performance_metrics=execution.performance_metrics or {},
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error generating pipeline results: {e}")
            raise
    
    def _generate_execution_recommendations(self, execution: PipelineExecution) -> List[str]:
        """Generate recommendations for specific execution"""
        recommendations = []
        
        try:
            # Check execution time
            if execution.end_time:
                execution_time = (execution.end_time - execution.start_time).total_seconds()
                if execution_time > 3600:  # 1 hour
                    recommendations.append("Execution time was high - consider optimizing pipeline stages")
            
            # Check improvement generation
            if execution.total_improvements < 2:
                recommendations.append("Low improvement generation - review pattern detection settings")
            
            # Check deployment rate
            if execution.deployed_improvements < execution.total_improvements * 0.5:
                recommendations.append("Low deployment rate - review validation criteria")
            
            # Check for errors
            if execution.error_message:
                recommendations.append(f"Execution had errors: {execution.error_message}")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating execution recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _calculate_execution_metrics(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate performance metrics for execution"""
        try:
            metrics = {
                'execution_time': 0.0,
                'total_improvements': execution.total_improvements,
                'deployed_improvements': execution.deployed_improvements,
                'deployment_rate': 0.0,
                'stage_performance': {}
            }
            
            if execution.end_time:
                metrics['execution_time'] = (execution.end_time - execution.start_time).total_seconds()
            
            if execution.total_improvements > 0:
                metrics['deployment_rate'] = execution.deployed_improvements / execution.total_improvements
            
            # Calculate stage performance (would need more detailed tracking)
            for stage_name, stage_results in execution.stage_results.items():
                metrics['stage_performance'][stage_name] = {
                    'completed': True,
                    'results_count': len(stage_results) if isinstance(stage_results, dict) else 0
                }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating execution metrics: {e}")
            return {}
    
    # Storage and state management
    async def _save_execution_record(self, execution: PipelineExecution):
        """Save execution record to storage"""
        try:
            execution_file = self.executions_path / f"{execution.execution_id}.json"
            
            with open(execution_file, 'w') as f:
                execution_dict = asdict(execution)
                execution_dict['start_time'] = execution.start_time.isoformat()
                if execution.end_time:
                    execution_dict['end_time'] = execution.end_time.isoformat()
                execution_dict['status'] = execution.status.value
                if execution.current_stage:
                    execution_dict['current_stage'] = execution.current_stage.value
                json.dump(execution_dict, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving execution record: {e}")
    
    async def _save_pipeline_results(self, results: PipelineResults):
        """Save pipeline results to storage"""
        try:
            results_file = self.results_path / f"{results.execution_id}.json"
            
            with open(results_file, 'w') as f:
                results_dict = asdict(results)
                results_dict['timestamp'] = results.timestamp.isoformat()
                json.dump(results_dict, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving pipeline results: {e}")
    
    async def _save_health_status(self, health_status: Dict[str, Any]):
        """Save health status to storage"""
        try:
            health_file = self.monitoring_path / f"health_{int(time.time())}.json"
            
            with open(health_file, 'w') as f:
                json.dump(health_status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving health status: {e}")
    
    async def _get_recent_executions(self, hours_back: int = 24) -> List[PipelineExecution]:
        """Get recent executions"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            executions = []
            
            for execution_file in self.executions_path.glob("*.json"):
                try:
                    with open(execution_file, 'r') as f:
                        data = json.load(f)
                    
                    start_time = datetime.fromisoformat(data['start_time'])
                    if start_time >= cutoff_time:
                        # Convert back to objects
                        data['start_time'] = start_time
                        if data.get('end_time'):
                            data['end_time'] = datetime.fromisoformat(data['end_time'])
                        data['status'] = PipelineStatus(data['status'])
                        if data.get('current_stage'):
                            data['current_stage'] = PipelineStage(data['current_stage'])
                        
                        executions.append(PipelineExecution(**data))
                        
                except Exception as e:
                    self.logger.error(f"Error loading execution {execution_file}: {e}")
                    continue
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Error getting recent executions: {e}")
            return []
    
    async def _get_executions_since(self, since_date: datetime) -> List[PipelineExecution]:
        """Get executions since given date"""
        try:
            executions = []
            
            for execution_file in self.executions_path.glob("*.json"):
                try:
                    with open(execution_file, 'r') as f:
                        data = json.load(f)
                    
                    start_time = datetime.fromisoformat(data['start_time'])
                    if start_time >= since_date:
                        # Convert back to objects
                        data['start_time'] = start_time
                        if data.get('end_time'):
                            data['end_time'] = datetime.fromisoformat(data['end_time'])
                        data['status'] = PipelineStatus(data['status'])
                        if data.get('current_stage'):
                            data['current_stage'] = PipelineStage(data['current_stage'])
                        
                        executions.append(PipelineExecution(**data))
                        
                except Exception as e:
                    self.logger.error(f"Error loading execution {execution_file}: {e}")
                    continue
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Error getting executions since {since_date}: {e}")
            return []
    
    async def _update_execution_status(self, execution: PipelineExecution):
        """Update execution status"""
        try:
            await self._save_execution_record(execution)
            self.logger.info(f"Execution {execution.execution_id} - Stage: {execution.current_stage.value if execution.current_stage else 'None'}, Status: {execution.status.value}")
        except Exception as e:
            self.logger.error(f"Error updating execution status: {e}")
    
    # Utility methods
    def _merge_config(self, custom_config: Optional[Dict]) -> PipelineConfig:
        """Merge custom configuration with default"""
        if not custom_config:
            return self.pipeline_config
        
        config_dict = asdict(self.pipeline_config)
        config_dict.update(custom_config)
        return PipelineConfig(**config_dict)
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        return f"pipeline_{timestamp}_{uuid.uuid4().hex[:8]}"


# Async convenience functions
async def run_pipeline_for_agents(agent_types: List[str]) -> Dict[str, Any]:
    """
    Convenience function to run pipeline for specific agents
    
    Args:
        agent_types: List of agent types to process
        
    Returns:
        Pipeline results
    """
    pipeline = PromptImprovementPipeline()
    results = await pipeline.run_full_pipeline(agent_types=agent_types)
    
    return {
        'execution_id': results.execution_id,
        'total_improvements': results.improvement_summary['total_improvements'],
        'deployed_improvements': results.improvement_summary['deployed_improvements'],
        'agent_results': results.agent_results,
        'recommendations': results.recommendations
    }


async def get_pipeline_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive pipeline dashboard
    
    Returns:
        Dashboard data
    """
    pipeline = PromptImprovementPipeline()
    
    # Get health status
    health = await pipeline.monitor_pipeline_health()
    
    # Get analytics
    analytics = await pipeline.get_pipeline_analytics()
    
    # Get active executions
    active_executions = [
        {
            'execution_id': execution.execution_id,
            'status': execution.status.value,
            'current_stage': execution.current_stage.value if execution.current_stage else None,
            'start_time': execution.start_time.isoformat(),
            'agent_types': execution.config.agent_types
        }
        for execution in pipeline.active_executions.values()
    ]
    
    return {
        'dashboard_generated': datetime.now().isoformat(),
        'health_status': health,
        'analytics': analytics,
        'active_executions': active_executions,
        'system_status': {
            'pipeline_available': health['pipeline_status'] != 'error',
            'active_executions_count': len(active_executions),
            'recent_success_rate': analytics.get('execution_summary', {}).get('success_rate', 0.0)
        }
    }


if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize pipeline
        pipeline = PromptImprovementPipeline()
        
        # Run full pipeline
        results = await pipeline.run_full_pipeline(
            agent_types=['Documentation', 'Engineer'],
            custom_config={'auto_deployment_enabled': True}
        )
        
        print(f"Pipeline completed: {results.execution_id}")
        print(f"Total improvements: {results.improvement_summary['total_improvements']}")
        print(f"Deployed improvements: {results.improvement_summary['deployed_improvements']}")
        
        # Get health status
        health = await pipeline.monitor_pipeline_health()
        print(f"Pipeline health: {health['pipeline_status']}")
        
        # Get analytics
        analytics = await pipeline.get_pipeline_analytics()
        print(f"Success rate: {analytics['execution_summary']['success_rate']:.2f}")
    
    asyncio.run(main())