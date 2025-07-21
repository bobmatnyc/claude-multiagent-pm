"""
System for monitoring hook performance and health.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from .models import HookExecutionResult, ErrorDetectionResult, ErrorSeverity


class HookMonitoringSystem:
    """System for monitoring hook performance and health."""
    
    def __init__(self, max_history: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        self.execution_history: List[HookExecutionResult] = []
        self.error_history: List[ErrorDetectionResult] = []
        self.performance_metrics = {
            'total_hooks_executed': 0,
            'total_errors_detected': 0,
            'average_execution_time': 0.0,
            'peak_execution_time': 0.0,
            'last_updated': datetime.now()
        }
        self.alert_thresholds = {
            'execution_time': 10.0,  # seconds
            'error_rate': 0.1,  # 10%
            'failure_rate': 0.05  # 5%
        }
    
    def record_execution(self, result: HookExecutionResult):
        """Record a hook execution result."""
        self.execution_history.append(result)
        
        # Maintain history size
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)
        
        # Update metrics
        self.performance_metrics['total_hooks_executed'] += 1
        
        if result.execution_time > self.performance_metrics['peak_execution_time']:
            self.performance_metrics['peak_execution_time'] = result.execution_time
        
        # Update average execution time
        self._update_average_execution_time(result.execution_time)
        
        # Check for alerts
        self._check_performance_alerts(result)
    
    def record_error_detection(self, result: ErrorDetectionResult):
        """Record an error detection result."""
        self.error_history.append(result)
        
        # Maintain history size
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        self.performance_metrics['total_errors_detected'] += 1
        self.performance_metrics['last_updated'] = datetime.now()
        
        # Log critical errors
        if result.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error detected: {result.error_type}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        recent_executions = self.execution_history[-100:]  # Last 100 executions
        recent_errors = self.error_history[-100:]  # Last 100 errors
        
        # Calculate rates
        success_rate = 0.0
        failure_rate = 0.0
        if recent_executions:
            successful = sum(1 for r in recent_executions if r.success)
            success_rate = successful / len(recent_executions)
            failure_rate = (len(recent_executions) - successful) / len(recent_executions)
        
        # Error severity distribution
        error_severity_dist = {}
        for severity in ErrorSeverity:
            error_severity_dist[severity.value] = sum(
                1 for r in recent_errors if r.severity == severity
            )
        
        return {
            'performance_metrics': self.performance_metrics,
            'recent_statistics': {
                'success_rate': success_rate,
                'failure_rate': failure_rate,
                'error_rate': len(recent_errors) / max(1, len(recent_executions)),
                'executions_count': len(recent_executions),
                'errors_count': len(recent_errors)
            },
            'error_severity_distribution': error_severity_dist,
            'top_errors': self._get_top_errors(),
            'performance_trends': self._get_performance_trends(),
            'alerts': self._get_active_alerts()
        }
    
    def _update_average_execution_time(self, execution_time: float):
        """Update running average of execution time."""
        current_avg = self.performance_metrics['average_execution_time']
        total_executions = self.performance_metrics['total_hooks_executed']
        
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.performance_metrics['average_execution_time'] = new_avg
        self.performance_metrics['last_updated'] = datetime.now()
    
    def _check_performance_alerts(self, result: HookExecutionResult):
        """Check for performance alerts based on thresholds."""
        alerts = []
        
        # Execution time alert
        if result.execution_time > self.alert_thresholds['execution_time']:
            alerts.append({
                'type': 'slow_execution',
                'message': f"Hook {result.hook_id} took {result.execution_time:.2f}s",
                'severity': 'warning'
            })
        
        # Calculate recent failure rate
        recent_executions = self.execution_history[-50:]  # Last 50 executions
        if len(recent_executions) >= 10:
            failure_rate = sum(1 for r in recent_executions if not r.success) / len(recent_executions)
            if failure_rate > self.alert_thresholds['failure_rate']:
                alerts.append({
                    'type': 'high_failure_rate',
                    'message': f"Failure rate {failure_rate:.2%} exceeds threshold",
                    'severity': 'critical'
                })
        
        # Log alerts
        for alert in alerts:
            if alert['severity'] == 'critical':
                self.logger.critical(alert['message'])
            else:
                self.logger.warning(alert['message'])
    
    def _get_top_errors(self) -> List[Dict[str, Any]]:
        """Get most common errors."""
        error_counts = {}
        for error in self.error_history:
            key = error.error_type
            if key not in error_counts:
                error_counts[key] = {'count': 0, 'latest': error}
            error_counts[key]['count'] += 1
            if error.timestamp > error_counts[key]['latest'].timestamp:
                error_counts[key]['latest'] = error
        
        # Sort by count and return top 5
        top_errors = sorted(error_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        return [
            {
                'error_type': error_type,
                'count': data['count'],
                'latest_occurrence': data['latest'].timestamp.isoformat(),
                'severity': data['latest'].severity.value
            }
            for error_type, data in top_errors
        ]
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends."""
        if len(self.execution_history) < 10:
            return {'insufficient_data': True}
        
        # Calculate trends for last 50 executions
        recent = self.execution_history[-50:]
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        first_avg = sum(r.execution_time for r in first_half) / len(first_half)
        second_avg = sum(r.execution_time for r in second_half) / len(second_half)
        
        return {
            'execution_time_trend': 'improving' if second_avg < first_avg else 'degrading',
            'trend_percentage': abs((second_avg - first_avg) / first_avg) * 100,
            'first_half_avg': first_avg,
            'second_half_avg': second_avg
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        alerts = []
        
        # Check current failure rate
        recent_executions = self.execution_history[-20:]
        if len(recent_executions) >= 5:
            failure_rate = sum(1 for r in recent_executions if not r.success) / len(recent_executions)
            if failure_rate > self.alert_thresholds['failure_rate']:
                alerts.append({
                    'type': 'high_failure_rate',
                    'severity': 'critical',
                    'message': f"Current failure rate: {failure_rate:.2%}",
                    'threshold': self.alert_thresholds['failure_rate']
                })
        
        # Check recent error rate
        recent_errors = len([e for e in self.error_history if 
                           (datetime.now() - e.timestamp).total_seconds() < 300])  # Last 5 minutes
        if recent_errors > 5:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'message': f"Multiple errors in last 5 minutes: {recent_errors}",
                'threshold': 5
            })
        
        return alerts