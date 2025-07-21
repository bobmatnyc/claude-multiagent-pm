"""
Prompt Improvement Pipeline - Automated prompt engineering optimization.

This module provides a comprehensive pipeline for analyzing correction patterns,
generating prompt improvements, and validating changes before deployment.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .types import (
    PipelineConfig, PipelineExecution, PipelineResults,
    PipelineStage, PipelineStatus
)
from .execution_manager import ExecutionManager
from .analytics import AnalyticsManager
from .storage import StorageManager
from .monitoring import MonitoringManager


class PromptImprovementPipeline:
    """
    Main facade for the prompt improvement pipeline.
    
    This class provides a high-level interface to the complete pipeline functionality,
    including execution, monitoring, analytics, and result management.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the prompt improvement pipeline
        
        Args:
            base_path: Base directory for pipeline data storage
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up base path
        if base_path is None:
            base_path = str(Path.home() / ".claude-pm" / "prompt_pipeline")
        
        # Initialize components
        self.storage = StorageManager(base_path)
        self.execution_manager = ExecutionManager(base_path)
        self.analytics = AnalyticsManager()
        self.monitoring = MonitoringManager(self.storage)
        
        self.logger.info(f"Initialized prompt improvement pipeline at {base_path}")
    
    async def run_full_pipeline(self, 
                              agent_types: Optional[List[str]] = None,
                              config: Optional[PipelineConfig] = None) -> PipelineResults:
        """
        Run the complete prompt improvement pipeline
        
        Args:
            agent_types: Specific agent types to process (optional)
            config: Pipeline configuration (optional)
            
        Returns:
            Comprehensive pipeline results
        """
        # Use default config if not provided
        if config is None:
            config = PipelineConfig(
                agent_types=agent_types or [],
                correction_analysis_days=30,
                pattern_detection_threshold=0.7,
                improvement_confidence_threshold=0.8,
                validation_sample_size=10,
                auto_deployment_enabled=False,
                monitoring_interval=3600
            )
        
        return await self.execution_manager.run_full_pipeline(config, agent_types)
    
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
        return await self.execution_manager.run_targeted_improvement(
            agent_type, specific_patterns
        )
    
    async def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get current pipeline health status
        
        Returns:
            Pipeline health information
        """
        health = await self.monitoring.check_pipeline_health()
        return {
            'status': health.status,
            'active_executions': health.active_executions,
            'recent_failures': health.recent_failures,
            'success_rate': health.success_rate,
            'average_execution_time': health.average_execution_time,
            'storage_usage_mb': health.storage_usage_mb,
            'alerts': health.alerts,
            'last_check': health.last_check.isoformat()
        }
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of a specific pipeline execution
        
        Args:
            execution_id: ID of execution to check
            
        Returns:
            Execution status information
        """
        return await self.monitoring.monitor_execution(execution_id)
    
    async def list_executions(self, 
                            status: Optional[str] = None,
                            days_back: int = 30) -> List[Dict[str, Any]]:
        """
        List pipeline executions with optional filtering
        
        Args:
            status: Filter by status (optional)
            days_back: Number of days to look back
            
        Returns:
            List of execution summaries
        """
        status_enum = PipelineStatus(status) if status else None
        return await self.storage.list_executions(status_enum, days_back)
    
    async def get_execution_report(self, execution_id: str) -> Dict[str, Any]:
        """
        Get comprehensive report for a pipeline execution
        
        Args:
            execution_id: ID of execution
            
        Returns:
            Detailed execution report
        """
        execution = await self.storage.load_execution_record(execution_id)
        if not execution:
            return {'error': 'Execution not found'}
        
        return self.analytics.generate_performance_report(execution)
    
    async def get_pipeline_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get pipeline performance trends
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend analysis results
        """
        # Load recent executions
        executions_data = await self.storage.list_executions(days_back=days)
        
        # Load full execution records
        executions = []
        for exec_summary in executions_data:
            execution = await self.storage.load_execution_record(exec_summary['execution_id'])
            if execution:
                executions.append(execution)
        
        return self.analytics.calculate_pipeline_trends(executions, days)
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active pipeline executions
        
        Returns:
            List of active execution summaries
        """
        return self.execution_manager.get_active_executions()
    
    async def pause_execution(self, execution_id: str) -> bool:
        """
        Pause a running pipeline execution
        
        Args:
            execution_id: ID of execution to pause
            
        Returns:
            True if paused successfully
        """
        return await self.execution_manager.pause_pipeline(execution_id)
    
    async def resume_execution(self, execution_id: str) -> bool:
        """
        Resume a paused pipeline execution
        
        Args:
            execution_id: ID of execution to resume
            
        Returns:
            True if resumed successfully
        """
        return await self.execution_manager.resume_pipeline(execution_id)
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running pipeline execution
        
        Args:
            execution_id: ID of execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        return await self.execution_manager.cancel_pipeline(execution_id)
    
    async def cleanup_old_data(self, 
                             archive_days: int = 90,
                             delete_days: int = 365) -> Dict[str, int]:
        """
        Clean up old pipeline data
        
        Args:
            archive_days: Days before archiving records
            delete_days: Days before deleting archived records
            
        Returns:
            Cleanup statistics
        """
        archived = await self.storage.archive_old_records(archive_days)
        deleted = await self.storage.cleanup_archives(delete_days)
        
        return {
            'records_archived': archived,
            'records_deleted': deleted
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics
        
        Returns:
            Storage statistics
        """
        return self.storage.get_storage_stats()
    
    def update_monitoring_thresholds(self, thresholds: Dict[str, Any]):
        """
        Update monitoring thresholds
        
        Args:
            thresholds: New threshold values
        """
        self.monitoring.update_thresholds(thresholds)
    
    def get_monitoring_thresholds(self) -> Dict[str, Any]:
        """
        Get current monitoring thresholds
        
        Returns:
            Current threshold values
        """
        return self.monitoring.get_thresholds()
    
    async def generate_health_report(self) -> str:
        """
        Generate human-readable health report
        
        Returns:
            Formatted health report
        """
        return await self.monitoring.generate_health_report()


# Export main classes and types
__all__ = [
    'PromptImprovementPipeline',
    'PipelineConfig',
    'PipelineExecution',
    'PipelineResults',
    'PipelineStage',
    'PipelineStatus'
]