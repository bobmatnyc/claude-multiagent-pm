"""
Pipeline execution management for the prompt improvement pipeline.

This module handles the orchestration and execution of pipeline runs,
including stage coordination, error handling, and status tracking.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .types import (
    PipelineStage, PipelineStatus, PipelineConfig, 
    PipelineExecution, PipelineResults
)
from .stage_handlers import StageHandlers
from .analytics import AnalyticsManager
from .storage import StorageManager


class ExecutionManager:
    """Manages pipeline execution lifecycle and coordination"""
    
    def __init__(self, base_path: str):
        self.logger = logging.getLogger(__name__)
        self.storage = StorageManager(base_path)
        self.stage_handlers = StageHandlers()
        self.analytics = AnalyticsManager()
        
        # Pipeline state
        self.active_executions: Dict[str, PipelineExecution] = {}
    
    async def run_full_pipeline(self, 
                              config: PipelineConfig,
                              agent_types: Optional[List[str]] = None) -> PipelineResults:
        """
        Run the complete prompt improvement pipeline
        
        Args:
            config: Pipeline configuration
            agent_types: Specific agent types to process (optional)
            
        Returns:
            Complete pipeline results
        """
        execution_id = self.storage.generate_execution_id()
        
        try:
            # Setup execution
            execution = PipelineExecution(
                execution_id=execution_id,
                config=config,
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
            
            correction_results = await self.stage_handlers.run_correction_analysis(execution)
            execution.stage_results['correction_analysis'] = correction_results
            
            # Stage 2: Pattern Detection
            execution.current_stage = PipelineStage.PATTERN_DETECTION
            await self._update_execution_status(execution)
            
            pattern_results = await self.stage_handlers.run_pattern_detection(
                execution, correction_results
            )
            execution.stage_results['pattern_detection'] = pattern_results
            
            # Stage 3: Improvement Generation
            execution.current_stage = PipelineStage.IMPROVEMENT_GENERATION
            await self._update_execution_status(execution)
            
            improvement_results = await self.stage_handlers.run_improvement_generation(
                execution, pattern_results
            )
            execution.stage_results['improvement_generation'] = improvement_results
            
            # Stage 4: Validation
            execution.current_stage = PipelineStage.VALIDATION
            await self._update_execution_status(execution)
            
            validation_results = await self.stage_handlers.run_validation(
                execution, improvement_results
            )
            execution.stage_results['validation'] = validation_results
            
            # Stage 5: Deployment (if enabled)
            if execution.config.auto_deployment_enabled:
                execution.current_stage = PipelineStage.DEPLOYMENT
                await self._update_execution_status(execution)
                
                deployment_results = await self.stage_handlers.run_deployment(
                    execution, validation_results
                )
                execution.stage_results['deployment'] = deployment_results
                execution.deployed_improvements = deployment_results.get('deployed_count', 0)
            
            # Stage 6: Monitoring Setup
            execution.current_stage = PipelineStage.MONITORING
            await self._update_execution_status(execution)
            
            monitoring_results = await self.stage_handlers.setup_monitoring(execution)
            execution.stage_results['monitoring'] = monitoring_results
            
            # Complete execution
            execution.status = PipelineStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.total_improvements = improvement_results.get('total_improvements', 0)
            execution.performance_metrics = self.analytics.calculate_execution_metrics(execution)
            
            # Generate comprehensive results
            results = await self._generate_pipeline_results(execution)
            
            # Save results
            await self.storage.save_pipeline_results(results)
            await self.storage.save_execution_record(execution)
            
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
                await self.storage.save_execution_record(execution)
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
            execution_id = self.storage.generate_execution_id()
            
            self.logger.info(f"Starting targeted improvement for {agent_type}")
            
            # Create targeted configuration
            config = PipelineConfig(
                agent_types=[agent_type],
                correction_analysis_days=14
            )
            
            # Run targeted stages
            results = await self.stage_handlers.run_targeted_improvement(
                execution_id, agent_type, specific_patterns
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Targeted improvement failed for {agent_type}: {e}")
            raise
    
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
            
            await self.storage.save_execution_record(execution)
            self.active_executions.pop(execution_id, None)
            
            self.logger.info(f"Cancelled pipeline execution: {execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling pipeline {execution_id}: {e}")
            return False
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get list of active executions"""
        return [
            {
                'execution_id': execution.execution_id,
                'status': execution.status.value,
                'current_stage': execution.current_stage.value if execution.current_stage else None,
                'start_time': execution.start_time.isoformat(),
                'agent_types': execution.config.agent_types
            }
            for execution in self.active_executions.values()
        ]
    
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
            recommendations = self.analytics.generate_execution_recommendations(execution)
            
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
    
    async def _update_execution_status(self, execution: PipelineExecution):
        """Update execution status"""
        try:
            await self.storage.save_execution_record(execution)
            self.logger.info(
                f"Execution {execution.execution_id} - Stage: "
                f"{execution.current_stage.value if execution.current_stage else 'None'}, "
                f"Status: {execution.status.value}"
            )
        except Exception as e:
            self.logger.error(f"Error updating execution status: {e}")