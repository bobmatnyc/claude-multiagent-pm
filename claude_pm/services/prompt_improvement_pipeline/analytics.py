"""
Analytics and metrics calculation for the prompt improvement pipeline.

This module handles performance metrics calculation, analytics generation,
and recommendation creation based on pipeline execution data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .types import PipelineExecution, PipelineStage, PipelineStatus


class AnalyticsManager:
    """Manages analytics calculation and metrics generation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_execution_metrics(self, execution: PipelineExecution) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for pipeline execution
        
        Args:
            execution: Pipeline execution record
            
        Returns:
            Performance metrics dictionary
        """
        try:
            metrics = {
                'execution_time': self._calculate_execution_time(execution),
                'stage_metrics': self._calculate_stage_metrics(execution),
                'efficiency_metrics': self._calculate_efficiency_metrics(execution),
                'quality_metrics': self._calculate_quality_metrics(execution),
                'resource_usage': self._calculate_resource_usage(execution)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating execution metrics: {e}")
            return {}
    
    def generate_execution_recommendations(self, execution: PipelineExecution) -> List[str]:
        """
        Generate recommendations based on execution performance
        
        Args:
            execution: Pipeline execution record
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        try:
            # Analyze improvement rate
            if execution.total_improvements > 0:
                deployment_rate = execution.deployed_improvements / execution.total_improvements
                
                if deployment_rate < 0.5:
                    recommendations.append(
                        "Low deployment rate detected. Consider reviewing validation criteria "
                        "or enabling auto-deployment for validated improvements."
                    )
                elif deployment_rate > 0.9:
                    recommendations.append(
                        "High deployment rate indicates good improvement quality. "
                        "Consider increasing analysis frequency."
                    )
            
            # Analyze stage performance
            stage_results = execution.stage_results or {}
            
            # Check pattern detection efficiency
            pattern_data = stage_results.get('pattern_detection', {})
            for agent_type, patterns in pattern_data.items():
                if isinstance(patterns, dict):
                    detection_rate = patterns.get('significant_patterns', 0) / patterns.get('patterns_detected', 1)
                    if detection_rate < 0.3:
                        recommendations.append(
                            f"Low pattern significance for {agent_type}. "
                            f"Consider adjusting pattern detection threshold."
                        )
            
            # Check validation results
            validation_data = stage_results.get('validation', {})
            for agent_type, validation in validation_data.items():
                if isinstance(validation, dict):
                    validation_rate = validation.get('validation_rate', 0)
                    if validation_rate < 0.6:
                        recommendations.append(
                            f"Low validation rate for {agent_type} improvements. "
                            f"Review improvement generation criteria."
                        )
            
            # Performance recommendations
            if execution.performance_metrics:
                exec_time = execution.performance_metrics.get('execution_time', {})
                total_seconds = exec_time.get('total_seconds', 0)
                
                if total_seconds > execution.config.pipeline_timeout * 0.8:
                    recommendations.append(
                        "Pipeline execution approaching timeout threshold. "
                        "Consider optimizing stage processing or increasing timeout."
                    )
            
            # Agent-specific recommendations
            for agent_type in execution.config.agent_types:
                agent_improvements = self._get_agent_improvement_count(execution, agent_type)
                if agent_improvements == 0:
                    recommendations.append(
                        f"No improvements generated for {agent_type}. "
                        f"Check if sufficient correction data is available."
                    )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations. Please check logs."]
    
    def calculate_pipeline_trends(self, 
                                executions: List[PipelineExecution],
                                days: int = 30) -> Dict[str, Any]:
        """
        Calculate trends across multiple pipeline executions
        
        Args:
            executions: List of pipeline executions
            days: Number of days to analyze
            
        Returns:
            Trend analysis results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_executions = [e for e in executions if e.start_time >= cutoff_date]
            
            if not recent_executions:
                return {}
            
            trends = {
                'execution_count': len(recent_executions),
                'success_rate': self._calculate_success_rate(recent_executions),
                'average_execution_time': self._calculate_average_execution_time(recent_executions),
                'improvement_trends': self._calculate_improvement_trends(recent_executions),
                'deployment_trends': self._calculate_deployment_trends(recent_executions),
                'agent_performance': self._calculate_agent_performance_trends(recent_executions)
            }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating pipeline trends: {e}")
            return {}
    
    def generate_performance_report(self, 
                                  execution: PipelineExecution,
                                  include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for pipeline execution
        
        Args:
            execution: Pipeline execution record
            include_recommendations: Whether to include recommendations
            
        Returns:
            Performance report dictionary
        """
        try:
            report = {
                'execution_id': execution.execution_id,
                'summary': {
                    'status': execution.status.value,
                    'duration': self._format_duration(execution),
                    'improvements_generated': execution.total_improvements,
                    'improvements_deployed': execution.deployed_improvements,
                    'deployment_success_rate': (
                        execution.deployed_improvements / execution.total_improvements 
                        if execution.total_improvements > 0 else 0
                    )
                },
                'stage_performance': self._generate_stage_performance_report(execution),
                'agent_performance': self._generate_agent_performance_report(execution),
                'metrics': execution.performance_metrics or {}
            }
            
            if include_recommendations:
                report['recommendations'] = self.generate_execution_recommendations(execution)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}
    
    def _calculate_execution_time(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate execution time metrics"""
        if not execution.end_time:
            return {}
        
        total_seconds = (execution.end_time - execution.start_time).total_seconds()
        
        return {
            'total_seconds': total_seconds,
            'total_minutes': total_seconds / 60,
            'formatted': self._format_duration(execution)
        }
    
    def _calculate_stage_metrics(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate per-stage metrics"""
        stage_metrics = {}
        
        for stage in PipelineStage:
            stage_data = execution.stage_results.get(stage.value, {})
            if stage_data:
                stage_metrics[stage.value] = {
                    'completed': True,
                    'item_count': self._count_stage_items(stage_data)
                }
            else:
                stage_metrics[stage.value] = {
                    'completed': False,
                    'item_count': 0
                }
        
        return stage_metrics
    
    def _calculate_efficiency_metrics(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate efficiency metrics"""
        stage_results = execution.stage_results or {}
        
        # Calculate conversion rates through pipeline
        corrections_count = sum(
            data.get('corrections_found', 0) 
            for data in stage_results.get('correction_analysis', {}).values()
            if isinstance(data, dict)
        )
        
        patterns_count = sum(
            data.get('significant_patterns', 0)
            for data in stage_results.get('pattern_detection', {}).values()
            if isinstance(data, dict)
        )
        
        improvements_count = execution.total_improvements
        deployed_count = execution.deployed_improvements
        
        return {
            'correction_to_pattern_rate': patterns_count / corrections_count if corrections_count > 0 else 0,
            'pattern_to_improvement_rate': improvements_count / patterns_count if patterns_count > 0 else 0,
            'improvement_to_deployment_rate': deployed_count / improvements_count if improvements_count > 0 else 0,
            'end_to_end_efficiency': deployed_count / corrections_count if corrections_count > 0 else 0
        }
    
    def _calculate_quality_metrics(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate quality metrics"""
        validation_data = execution.stage_results.get('validation', {})
        
        total_validated = 0
        total_tested = 0
        
        for agent_data in validation_data.values():
            if isinstance(agent_data, dict):
                total_validated += agent_data.get('improvements_validated', 0)
                total_tested += agent_data.get('improvements_tested', 0)
        
        return {
            'validation_pass_rate': total_validated / total_tested if total_tested > 0 else 0,
            'improvement_quality_score': self._calculate_improvement_quality_score(execution)
        }
    
    def _calculate_resource_usage(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Calculate resource usage metrics"""
        # Placeholder for actual resource monitoring
        return {
            'api_calls': 0,  # Would track actual API usage
            'memory_usage_mb': 0,  # Would track memory
            'cpu_time_seconds': 0  # Would track CPU time
        }
    
    def _calculate_success_rate(self, executions: List[PipelineExecution]) -> float:
        """Calculate success rate across executions"""
        if not executions:
            return 0.0
        
        successful = sum(1 for e in executions if e.status == PipelineStatus.COMPLETED)
        return successful / len(executions)
    
    def _calculate_average_execution_time(self, executions: List[PipelineExecution]) -> float:
        """Calculate average execution time in minutes"""
        valid_executions = [e for e in executions if e.end_time]
        if not valid_executions:
            return 0.0
        
        total_minutes = sum(
            (e.end_time - e.start_time).total_seconds() / 60
            for e in valid_executions
        )
        
        return total_minutes / len(valid_executions)
    
    def _calculate_improvement_trends(self, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """Calculate improvement generation trends"""
        if not executions:
            return {}
        
        total_improvements = sum(e.total_improvements for e in executions)
        avg_improvements = total_improvements / len(executions)
        
        return {
            'total_improvements': total_improvements,
            'average_per_execution': avg_improvements,
            'trend': self._calculate_trend([e.total_improvements for e in executions])
        }
    
    def _calculate_deployment_trends(self, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """Calculate deployment trends"""
        if not executions:
            return {}
        
        total_deployed = sum(e.deployed_improvements for e in executions)
        deployment_rates = [
            e.deployed_improvements / e.total_improvements 
            for e in executions if e.total_improvements > 0
        ]
        
        return {
            'total_deployed': total_deployed,
            'average_deployment_rate': sum(deployment_rates) / len(deployment_rates) if deployment_rates else 0,
            'trend': self._calculate_trend(deployment_rates)
        }
    
    def _calculate_agent_performance_trends(self, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """Calculate per-agent performance trends"""
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
                agent_stats[agent_type]['improvements'] += self._get_agent_improvement_count(execution, agent_type)
                agent_stats[agent_type]['deployments'] += self._get_agent_deployment_count(execution, agent_type)
        
        return agent_stats
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _get_agent_improvement_count(self, execution: PipelineExecution, agent_type: str) -> int:
        """Get improvement count for specific agent"""
        improvements = execution.stage_results.get('improvement_generation', {}).get(agent_type, {})
        if isinstance(improvements, dict):
            return improvements.get('confident_improvements', 0)
        return 0
    
    def _get_agent_deployment_count(self, execution: PipelineExecution, agent_type: str) -> int:
        """Get deployment count for specific agent"""
        deployments = execution.stage_results.get('deployment', {}).get('deployment_details', {}).get(agent_type, {})
        if isinstance(deployments, dict):
            return deployments.get('successful', 0)
        return 0
    
    def _calculate_improvement_quality_score(self, execution: PipelineExecution) -> float:
        """Calculate overall improvement quality score"""
        # Combine validation rate and deployment rate
        validation_rate = 0.0
        deployment_rate = 0.0
        
        if execution.total_improvements > 0:
            deployment_rate = execution.deployed_improvements / execution.total_improvements
        
        validation_data = execution.stage_results.get('validation', {})
        validation_rates = [
            data.get('validation_rate', 0)
            for data in validation_data.values()
            if isinstance(data, dict)
        ]
        
        if validation_rates:
            validation_rate = sum(validation_rates) / len(validation_rates)
        
        # Weight validation more heavily than deployment
        return (validation_rate * 0.6) + (deployment_rate * 0.4)
    
    def _format_duration(self, execution: PipelineExecution) -> str:
        """Format execution duration as human-readable string"""
        if not execution.end_time:
            return "In progress"
        
        duration = execution.end_time - execution.start_time
        total_seconds = int(duration.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _count_stage_items(self, stage_data: Dict[str, Any]) -> int:
        """Count items processed in a stage"""
        count = 0
        
        for agent_data in stage_data.values():
            if isinstance(agent_data, dict):
                # Try different count fields
                count += agent_data.get('corrections_found', 0)
                count += agent_data.get('patterns_detected', 0)
                count += agent_data.get('improvements_generated', 0)
                count += agent_data.get('improvements_tested', 0)
        
        return count
    
    def _generate_stage_performance_report(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Generate detailed stage performance report"""
        report = {}
        
        for stage in PipelineStage:
            stage_data = execution.stage_results.get(stage.value, {})
            if stage_data:
                report[stage.value] = {
                    'status': 'completed',
                    'items_processed': self._count_stage_items(stage_data),
                    'agents_involved': list(stage_data.keys())
                }
            else:
                report[stage.value] = {
                    'status': 'skipped' if stage != execution.current_stage else 'in_progress',
                    'items_processed': 0,
                    'agents_involved': []
                }
        
        return report
    
    def _generate_agent_performance_report(self, execution: PipelineExecution) -> Dict[str, Any]:
        """Generate detailed agent performance report"""
        report = {}
        
        for agent_type in execution.config.agent_types:
            report[agent_type] = {
                'improvements_generated': self._get_agent_improvement_count(execution, agent_type),
                'improvements_deployed': self._get_agent_deployment_count(execution, agent_type),
                'validation_rate': self._get_agent_validation_rate(execution, agent_type),
                'deployment_success_rate': self._get_agent_deployment_rate(execution, agent_type)
            }
        
        return report
    
    def _get_agent_validation_rate(self, execution: PipelineExecution, agent_type: str) -> float:
        """Get validation rate for specific agent"""
        validation = execution.stage_results.get('validation', {}).get(agent_type, {})
        if isinstance(validation, dict):
            return validation.get('validation_rate', 0.0)
        return 0.0
    
    def _get_agent_deployment_rate(self, execution: PipelineExecution, agent_type: str) -> float:
        """Get deployment success rate for specific agent"""
        deployments = execution.stage_results.get('deployment', {}).get('deployment_details', {}).get(agent_type, {})
        if isinstance(deployments, dict):
            attempted = deployments.get('attempted', 0)
            successful = deployments.get('successful', 0)
            if attempted > 0:
                return successful / attempted
        return 0.0