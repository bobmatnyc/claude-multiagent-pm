"""
Hook Processing Service - Core implementation for Claude PM Framework
Handles hook execution, error detection, and monitoring for agent workflows.

Main facade class for the hook processing service.
"""

import logging as standard_logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import HookConfiguration, HookType, HookExecutionResult
from .logging import ProjectBasedHookLogger
from .error_detection import ErrorDetectionSystem
from .execution import HookExecutionEngine
from .configuration import HookConfigurationSystem
from .monitoring import HookMonitoringSystem
from .handlers import SubagentStopHookExample
from .utils import create_hook_processing_service, DEFAULT_CONFIG


class HookProcessingService:
    """Main service for processing hooks with comprehensive error detection and monitoring."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = standard_logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize subsystems
        self.error_detection = ErrorDetectionSystem()
        self.execution_engine = HookExecutionEngine(
            max_workers=self.config.get('max_workers', 4)
        )
        self.configuration_system = HookConfigurationSystem()
        self.monitoring_system = HookMonitoringSystem(
            max_history=self.config.get('max_history', 1000)
        )
        
        # Initialize project-based logging
        self.project_logger = ProjectBasedHookLogger(
            project_root=self.config.get('project_root'),
            max_log_files=self.config.get('max_log_files', 10),
            max_log_size_mb=self.config.get('max_log_size_mb', 10)
        )
        
        # Service state
        self.is_running = False
        self.startup_time = None
        
        # Register default hooks
        self._register_default_hooks()
    
    def _register_default_hooks(self):
        """Register default hooks for common scenarios."""
        # SubagentStop error detection hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='subagent_stop_detector',
            hook_type=HookType.SUBAGENT_STOP,
            handler=self._handle_subagent_stop,
            priority=100,
            timeout=5.0,
            prefer_async=True
        ))
        
        # Performance monitoring hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='performance_monitor',
            hook_type=HookType.PERFORMANCE_MONITOR,
            handler=self._handle_performance_monitoring,
            priority=50,
            timeout=3.0,
            prefer_async=True
        ))
        
        # General error detection hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='error_detector',
            hook_type=HookType.ERROR_DETECTION,
            handler=self._handle_error_detection,
            priority=90,
            timeout=10.0,
            prefer_async=True
        ))
    
    async def _handle_subagent_stop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SubagentStop error detection."""
        transcript = context.get('transcript', '')
        agent_type = context.get('agent_type', 'unknown')
        
        # Analyze transcript for subagent stop errors
        error_results = await self.error_detection.analyze_transcript(transcript, {
            'agent_type': agent_type,
            'analysis_type': 'subagent_stop'
        })
        
        # Filter for subagent stop errors
        subagent_errors = [r for r in error_results if r.error_type == 'subagent_stop']
        
        if subagent_errors:
            self.logger.warning(f"SubagentStop errors detected for {agent_type}: {len(subagent_errors)}")
            
            # Record errors for monitoring and project logging
            for error in subagent_errors:
                self.monitoring_system.record_error_detection(error)
                self.project_logger.log_error_detection(error, context)
            
            return {
                'errors_detected': len(subagent_errors),
                'errors': [
                    {
                        'type': error.error_type,
                        'severity': error.severity.value,
                        'details': error.details,
                        'suggested_action': error.suggested_action
                    }
                    for error in subagent_errors
                ],
                'recommended_action': 'restart_subagent'
            }
        
        return {'errors_detected': 0, 'status': 'healthy'}
    
    async def _handle_performance_monitoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance monitoring."""
        execution_time = context.get('execution_time', 0.0)
        hook_id = context.get('hook_id', 'unknown')
        
        # Check for performance issues
        alerts = []
        if execution_time > 5.0:
            alerts.append({
                'type': 'slow_execution',
                'message': f"Hook {hook_id} execution time: {execution_time:.2f}s",
                'severity': 'warning'
            })
        
        return {
            'execution_time': execution_time,
            'alerts': alerts,
            'performance_report': self.monitoring_system.get_performance_report()
        }
    
    async def _handle_error_detection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general error detection."""
        transcript = context.get('transcript', '')
        agent_type = context.get('agent_type', 'unknown')
        
        # Analyze for all error types
        error_results = await self.error_detection.analyze_transcript(transcript, {
            'agent_type': agent_type,
            'analysis_type': 'general'
        })
        
        # Record errors for monitoring and project logging
        for error in error_results:
            self.monitoring_system.record_error_detection(error)
            self.project_logger.log_error_detection(error, context)
        
        return {
            'errors_detected': len(error_results),
            'errors': [
                {
                    'type': error.error_type,
                    'severity': error.severity.value,
                    'details': error.details,
                    'suggested_action': error.suggested_action
                }
                for error in error_results
            ]
        }
    
    def register_hook(self, hook_config: HookConfiguration) -> bool:
        """Register a hook configuration."""
        return self.configuration_system.register_hook(hook_config)
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook configuration."""
        return self.configuration_system.unregister_hook(hook_id)
    
    async def process_hooks(self, hook_type: HookType, context: Dict[str, Any]) -> List[HookExecutionResult]:
        """Process all hooks of a specific type."""
        if not self.is_running:
            self.logger.warning("Hook processing service is not running")
            return []
        
        # Get hooks for this type
        hooks = self.configuration_system.get_hooks_by_type(hook_type)
        if not hooks:
            return []
        
        # Execute hooks
        results = await self.execution_engine.execute_hooks_batch(hooks, context)
        
        # Record results for monitoring and project logging
        for result in results:
            self.monitoring_system.record_execution(result)
            # Find the corresponding hook configuration for project logging
            hook_config = None
            for hook in hooks:
                if hook.hook_id == result.hook_id:
                    hook_config = hook
                    break
            if hook_config:
                self.project_logger.log_hook_execution(hook_config, result, context)
        
        return results
    
    async def analyze_subagent_transcript(self, transcript: str, agent_type: str) -> Dict[str, Any]:
        """Analyze subagent transcript for errors and issues."""
        context = {
            'transcript': transcript,
            'agent_type': agent_type,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Process SubagentStop hooks
        results = await self.process_hooks(HookType.SUBAGENT_STOP, context)
        
        # Process general error detection hooks
        error_results = await self.process_hooks(HookType.ERROR_DETECTION, context)
        
        # Combine results
        all_results = results + error_results
        
        # Extract error information
        detected_errors = []
        for result in all_results:
            if result.success and result.result:
                result_data = result.result
                if isinstance(result_data, dict) and 'errors' in result_data:
                    detected_errors.extend(result_data['errors'])
        
        return {
            'analysis_complete': True,
            'transcript_length': len(transcript),
            'agent_type': agent_type,
            'errors_detected': len(detected_errors),
            'errors': detected_errors,
            'execution_results': [
                {
                    'hook_id': r.hook_id,
                    'success': r.success,
                    'execution_time': r.execution_time,
                    'error': r.error
                }
                for r in all_results
            ],
            'analysis_timestamp': context['analysis_timestamp']
        }
    
    async def start(self):
        """Start the hook processing service."""
        if self.is_running:
            self.logger.warning("Hook processing service is already running")
            return
        
        self.logger.info("Starting hook processing service...")
        self.is_running = True
        self.startup_time = datetime.now()
        
        # Perform startup health checks
        await self._perform_startup_checks()
        
        self.logger.info("Hook processing service started successfully")
    
    async def stop(self):
        """Stop the hook processing service."""
        if not self.is_running:
            self.logger.warning("Hook processing service is not running")
            return
        
        self.logger.info("Stopping hook processing service...")
        self.is_running = False
        
        # Cleanup resources
        self.execution_engine.cleanup()
        self.configuration_system.cleanup_dead_references()
        
        self.logger.info("Hook processing service stopped")
    
    async def _perform_startup_checks(self):
        """Perform startup health checks."""
        checks = [
            ('Error Detection System', self._check_error_detection_health),
            ('Execution Engine', self._check_execution_engine_health),
            ('Configuration System', self._check_configuration_health),
            ('Monitoring System', self._check_monitoring_health)
        ]
        
        for check_name, check_func in checks:
            try:
                await check_func()
                self.logger.info(f"✅ {check_name} health check passed")
            except Exception as e:
                self.logger.error(f"❌ {check_name} health check failed: {str(e)}")
                raise
    
    async def _check_error_detection_health(self):
        """Check error detection system health."""
        # Test error detection with sample data
        sample_transcript = "Test transcript with no errors"
        results = await self.error_detection.analyze_transcript(sample_transcript)
        
        # Should return empty results for clean transcript
        if not isinstance(results, list):
            raise RuntimeError("Error detection system not returning proper results")
    
    async def _check_execution_engine_health(self):
        """Check execution engine health."""
        # Test with a simple hook
        async def test_hook(context):
            return "test_result"
        
        test_config = HookConfiguration(
            hook_id='health_check_test',
            hook_type=HookType.PRE_TOOL_USE,
            handler=test_hook,
            timeout=1.0
        )
        
        result = await self.execution_engine.execute_hook(test_config, {})
        
        if not result.success:
            raise RuntimeError(f"Execution engine test failed: {result.error}")
    
    async def _check_configuration_health(self):
        """Check configuration system health."""
        stats = self.configuration_system.get_configuration_stats()
        
        if stats['total_hooks'] == 0:
            raise RuntimeError("No hooks registered in configuration system")
    
    async def _check_monitoring_health(self):
        """Check monitoring system health."""
        report = self.monitoring_system.get_performance_report()
        
        if not isinstance(report, dict):
            raise RuntimeError("Monitoring system not generating proper reports")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status."""
        return {
            'service_info': {
                'is_running': self.is_running,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'uptime_seconds': (
                    (datetime.now() - self.startup_time).total_seconds()
                    if self.startup_time else 0
                )
            },
            'error_detection_stats': self.error_detection.get_detection_stats(),
            'execution_stats': self.execution_engine.get_execution_stats(),
            'configuration_stats': self.configuration_system.get_configuration_stats(),
            'performance_report': self.monitoring_system.get_performance_report(),
            'project_logging': self.project_logger.get_project_hook_summary()
        }
    
    def get_hook_logs(self, hook_type: HookType, hook_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get project-based hook logs for a specific hook."""
        return self.project_logger.get_hook_logs(hook_type, hook_id, limit)
    
    def get_project_hook_summary(self) -> Dict[str, Any]:
        """Get summary of all project-based hook activity."""
        return self.project_logger.get_project_hook_summary()
    
    def cleanup_project_logs(self, days_old: int = 30) -> int:
        """Clean up project-based hook logs older than specified days."""
        return self.project_logger.cleanup_old_logs(days_old)


# Re-export important classes and functions
__all__ = [
    'HookProcessingService',
    'HookConfiguration',
    'HookType',
    'HookExecutionResult',
    'ErrorDetectionResult',
    'ErrorSeverity',
    'SubagentStopHookExample',
    'create_hook_processing_service',
    'DEFAULT_CONFIG'
]


# Import models for backward compatibility
from .models import ErrorSeverity, ErrorDetectionResult