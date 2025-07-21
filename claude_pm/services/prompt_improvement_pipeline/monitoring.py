"""
Health monitoring and status tracking for the prompt improvement pipeline.

This module handles real-time monitoring of pipeline health, status tracking,
and alerting for pipeline operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .types import PipelineExecution, PipelineStatus
from .storage import StorageManager


@dataclass
class PipelineHealth:
    """Pipeline health status"""
    status: str  # healthy, warning, critical
    active_executions: int
    recent_failures: int
    success_rate: float
    average_execution_time: float
    storage_usage_mb: float
    alerts: List[str]
    last_check: datetime


class MonitoringManager:
    """Manages pipeline health monitoring and status tracking"""
    
    def __init__(self, storage_manager: StorageManager):
        self.logger = logging.getLogger(__name__)
        self.storage = storage_manager
        
        # Monitoring thresholds
        self.thresholds = {
            'max_active_executions': 10,
            'min_success_rate': 0.7,
            'max_avg_execution_time': 120,  # minutes
            'max_storage_usage_mb': 1000,
            'recent_failure_threshold': 3
        }
    
    async def check_pipeline_health(self) -> PipelineHealth:
        """
        Perform comprehensive health check of the pipeline
        
        Returns:
            Pipeline health status
        """
        try:
            alerts = []
            
            # Get recent executions
            recent_executions = await self.storage.list_executions(days_back=7)
            
            # Calculate metrics
            active_count = sum(1 for e in recent_executions if e['status'] == 'running')
            failure_count = sum(1 for e in recent_executions if e['status'] == 'failed')
            success_count = sum(1 for e in recent_executions if e['status'] == 'completed')
            total_count = len(recent_executions)
            
            success_rate = success_count / total_count if total_count > 0 else 0.0
            
            # Calculate average execution time
            completed_executions = [e for e in recent_executions if e.get('end_time')]
            avg_execution_time = 0.0
            
            if completed_executions:
                total_time = 0
                for exec_data in completed_executions:
                    if exec_data.get('start_time') and exec_data.get('end_time'):
                        start = datetime.fromisoformat(exec_data['start_time'])
                        end = datetime.fromisoformat(exec_data['end_time'])
                        total_time += (end - start).total_seconds() / 60
                
                avg_execution_time = total_time / len(completed_executions)
            
            # Get storage usage
            storage_stats = self.storage.get_storage_stats()
            storage_usage = storage_stats.get('total_size_mb', 0)
            
            # Check thresholds and generate alerts
            if active_count > self.thresholds['max_active_executions']:
                alerts.append(f"High number of active executions: {active_count}")
            
            if success_rate < self.thresholds['min_success_rate']:
                alerts.append(f"Low success rate: {success_rate:.2%}")
            
            if failure_count >= self.thresholds['recent_failure_threshold']:
                alerts.append(f"Multiple recent failures: {failure_count}")
            
            if avg_execution_time > self.thresholds['max_avg_execution_time']:
                alerts.append(f"High average execution time: {avg_execution_time:.1f} minutes")
            
            if storage_usage > self.thresholds['max_storage_usage_mb']:
                alerts.append(f"High storage usage: {storage_usage:.1f} MB")
            
            # Determine overall status
            if len(alerts) >= 3:
                status = "critical"
            elif len(alerts) >= 1:
                status = "warning"
            else:
                status = "healthy"
            
            return PipelineHealth(
                status=status,
                active_executions=active_count,
                recent_failures=failure_count,
                success_rate=success_rate,
                average_execution_time=avg_execution_time,
                storage_usage_mb=storage_usage,
                alerts=alerts,
                last_check=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error checking pipeline health: {e}")
            return PipelineHealth(
                status="error",
                active_executions=0,
                recent_failures=0,
                success_rate=0.0,
                average_execution_time=0.0,
                storage_usage_mb=0.0,
                alerts=[f"Health check error: {str(e)}"],
                last_check=datetime.now()
            )
    
    async def monitor_execution(self, 
                              execution_id: str,
                              check_interval: int = 60) -> Dict[str, Any]:
        """
        Monitor a specific execution
        
        Args:
            execution_id: Execution to monitor
            check_interval: Seconds between checks
            
        Returns:
            Monitoring results
        """
        try:
            execution = await self.storage.load_execution_record(execution_id)
            if not execution:
                return {'error': 'Execution not found'}
            
            monitoring_data = {
                'execution_id': execution_id,
                'status': execution.status.value,
                'current_stage': execution.current_stage.value if execution.current_stage else None,
                'runtime_minutes': 0.0,
                'progress_percentage': 0.0,
                'estimated_completion': None
            }
            
            # Calculate runtime
            if execution.start_time:
                runtime = datetime.now() - execution.start_time
                monitoring_data['runtime_minutes'] = runtime.total_seconds() / 60
            
            # Estimate progress
            if execution.current_stage:
                stage_order = list(PipelineStage)
                current_index = stage_order.index(execution.current_stage)
                monitoring_data['progress_percentage'] = (current_index + 1) / len(stage_order) * 100
                
                # Estimate completion time (simplified)
                if monitoring_data['runtime_minutes'] > 0:
                    total_estimated = monitoring_data['runtime_minutes'] / (monitoring_data['progress_percentage'] / 100)
                    remaining_minutes = total_estimated - monitoring_data['runtime_minutes']
                    monitoring_data['estimated_completion'] = (
                        datetime.now() + timedelta(minutes=remaining_minutes)
                    ).isoformat()
            
            return monitoring_data
            
        except Exception as e:
            self.logger.error(f"Error monitoring execution {execution_id}: {e}")
            return {'error': str(e)}
    
    def update_thresholds(self, new_thresholds: Dict[str, Any]):
        """Update monitoring thresholds"""
        self.thresholds.update(new_thresholds)
        self.logger.info(f"Updated monitoring thresholds: {new_thresholds}")
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Get current monitoring thresholds"""
        return self.thresholds.copy()
    
    async def generate_health_report(self) -> str:
        """Generate human-readable health report"""
        try:
            health = await self.check_pipeline_health()
            
            report = f"""
Pipeline Health Report
Generated: {health.last_check.strftime('%Y-%m-%d %H:%M:%S')}
==================================================

Overall Status: {health.status.upper()}

Metrics:
- Active Executions: {health.active_executions}
- Recent Failures: {health.recent_failures}
- Success Rate: {health.success_rate:.1%}
- Average Execution Time: {health.average_execution_time:.1f} minutes
- Storage Usage: {health.storage_usage_mb:.1f} MB

"""
            
            if health.alerts:
                report += "Alerts:\n"
                for alert in health.alerts:
                    report += f"⚠️  {alert}\n"
            else:
                report += "✅ No alerts - all systems operational\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return f"Error generating report: {str(e)}"