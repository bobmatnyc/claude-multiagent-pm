"""
Comprehensive test suite for hook processing service.
Tests all components including error detection, execution engine, and monitoring.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from claude_pm.services.hook_processing_service import (
    HookProcessingService, HookConfiguration, HookType, ErrorSeverity,
    ErrorDetectionSystem, HookExecutionEngine, HookConfigurationSystem,
    HookMonitoringSystem, HookExecutionResult, ErrorDetectionResult,
    create_hook_processing_service
)
from claude_pm.services.hook_examples import (
    AgentIntegrationHooks, HookProcessingDemo, quick_error_analysis
)


class TestErrorDetectionSystem:
    """Test suite for error detection system."""
    
    @pytest.fixture
    def error_detection_system(self):
        return ErrorDetectionSystem()
    
    @pytest.mark.asyncio
    async def test_subagent_stop_detection(self, error_detection_system):
        """Test detection of subagent stop errors."""
        transcript = """
        Agent starting...
        Processing request...
        ERROR: subprocess failed with exit code 1
        Agent process terminated unexpectedly
        Memory allocation failed
        """
        
        results = await error_detection_system.analyze_transcript(transcript)
        
        assert len(results) > 0
        subagent_errors = [r for r in results if r.error_type == 'subagent_stop']
        assert len(subagent_errors) > 0
        
        error = subagent_errors[0]
        assert error.error_detected is True
        assert error.severity == ErrorSeverity.HIGH
        assert error.suggested_action == 'restart_subagent'
    
    @pytest.mark.asyncio
    async def test_version_mismatch_detection(self, error_detection_system):
        """Test detection of version mismatch errors."""
        transcript = """
        Loading dependencies...
        Package version mismatch detected
        Requires version 2.0 but found 1.5
        Dependency version conflict
        """
        
        results = await error_detection_system.analyze_transcript(transcript)
        
        version_errors = [r for r in results if r.error_type == 'version_mismatch']
        assert len(version_errors) > 0
        
        error = version_errors[0]
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.suggested_action == 'update_dependencies'
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_detection(self, error_detection_system):
        """Test detection of resource exhaustion errors."""
        transcript = """
        Processing large dataset...
        Out of memory error
        Memory exhausted during operation
        System resources unavailable
        """
        
        results = await error_detection_system.analyze_transcript(transcript)
        
        resource_errors = [r for r in results if r.error_type == 'resource_exhaustion']
        assert len(resource_errors) > 0
        
        error = resource_errors[0]
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.suggested_action == 'cleanup_resources'
    
    @pytest.mark.asyncio
    async def test_network_issues_detection(self, error_detection_system):
        """Test detection of network-related errors."""
        transcript = """
        Connecting to API...
        Network timeout occurred
        Connection refused by server
        SSL handshake failed
        """
        
        results = await error_detection_system.analyze_transcript(transcript)
        
        network_errors = [r for r in results if r.error_type == 'network_issues']
        assert len(network_errors) > 0
        
        error = network_errors[0]
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.suggested_action == 'retry_with_backoff'
    
    @pytest.mark.asyncio
    async def test_clean_transcript_no_errors(self, error_detection_system):
        """Test that clean transcripts don't trigger false positives."""
        transcript = """
        Agent starting...
        Processing completed successfully
        All operations finished without errors
        Agent shutting down normally
        """
        
        results = await error_detection_system.analyze_transcript(transcript)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_agent_specific_errors(self, error_detection_system):
        """Test agent-specific error detection."""
        # Documentation agent output
        doc_output = """
        Generating documentation...
        Markdown parse error in file.md
        Documentation build failed
        Template not found
        """
        
        results = await error_detection_system.analyze_agent_output(doc_output, 'documentation_agent')
        
        assert len(results) > 0
        doc_errors = [r for r in results if 'documentation_agent_error' in r.error_type]
        assert len(doc_errors) > 0
    
    def test_detection_stats(self, error_detection_system):
        """Test detection statistics tracking."""
        stats = error_detection_system.get_detection_stats()
        
        assert 'total_analyses' in stats
        assert 'errors_detected' in stats
        assert 'error_rate' in stats
        assert 'patterns_count' in stats
        assert stats['patterns_count'] > 0


class TestHookExecutionEngine:
    """Test suite for hook execution engine."""
    
    @pytest.fixture
    def execution_engine(self):
        return HookExecutionEngine(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_async_hook_execution(self, execution_engine):
        """Test execution of async hooks."""
        async def test_async_hook(context):
            await asyncio.sleep(0.1)
            return {'result': 'async_success', 'context': context}
        
        hook_config = HookConfiguration(
            hook_id='test_async_hook',
            hook_type=HookType.PRE_TOOL_USE,
            handler=test_async_hook,
            timeout=5.0
        )
        
        context = {'test_data': 'value'}
        result = await execution_engine.execute_hook(hook_config, context)
        
        assert result.success is True
        assert result.hook_id == 'test_async_hook'
        assert result.result['result'] == 'async_success'
        assert result.execution_time > 0.1
    
    @pytest.mark.asyncio
    async def test_sync_hook_execution(self, execution_engine):
        """Test execution of synchronous hooks."""
        def test_sync_hook(context):
            return {'result': 'sync_success', 'data': context.get('test_data')}
        
        hook_config = HookConfiguration(
            hook_id='test_sync_hook',
            hook_type=HookType.POST_TOOL_USE,
            handler=test_sync_hook,
            timeout=5.0
        )
        
        context = {'test_data': 'sync_value'}
        result = await execution_engine.execute_hook(hook_config, context)
        
        assert result.success is True
        assert result.result['result'] == 'sync_success'
        assert result.result['data'] == 'sync_value'
    
    @pytest.mark.asyncio
    async def test_hook_timeout(self, execution_engine):
        """Test hook execution timeout handling."""
        async def slow_hook(context):
            await asyncio.sleep(2.0)  # Longer than timeout
            return 'should_not_reach'
        
        hook_config = HookConfiguration(
            hook_id='slow_hook',
            hook_type=HookType.PRE_TOOL_USE,
            handler=slow_hook,
            timeout=0.5  # Short timeout
        )
        
        result = await execution_engine.execute_hook(hook_config, {})
        
        assert result.success is False
        assert 'timed out' in result.error
        assert result.execution_time >= 0.5
    
    @pytest.mark.asyncio
    async def test_hook_exception_handling(self, execution_engine):
        """Test handling of exceptions in hooks."""
        async def failing_hook(context):
            raise ValueError("Test exception")
        
        hook_config = HookConfiguration(
            hook_id='failing_hook',
            hook_type=HookType.ERROR_DETECTION,
            handler=failing_hook,
            timeout=5.0
        )
        
        result = await execution_engine.execute_hook(hook_config, {})
        
        assert result.success is False
        assert 'Test exception' in result.error
        assert result.metadata['exception_type'] == 'ValueError'
    
    @pytest.mark.asyncio
    async def test_batch_execution(self, execution_engine):
        """Test batch execution of multiple hooks."""
        async def hook1(context):
            return 'result1'
        
        async def hook2(context):
            return 'result2'
        
        def hook3(context):
            return 'result3'
        
        hooks = [
            HookConfiguration('hook1', HookType.PRE_TOOL_USE, hook1, priority=3),
            HookConfiguration('hook2', HookType.PRE_TOOL_USE, hook2, priority=2),
            HookConfiguration('hook3', HookType.PRE_TOOL_USE, hook3, priority=1),
        ]
        
        results = await execution_engine.execute_hooks_batch(hooks, {})
        
        assert len(results) == 3
        assert all(r.success for r in results)
        
        # Check execution order (should be by priority)
        assert results[0].hook_id == 'hook1'  # Priority 3
        assert results[1].hook_id == 'hook2'  # Priority 2
        assert results[2].hook_id == 'hook3'  # Priority 1
    
    def test_execution_stats(self, execution_engine):
        """Test execution statistics tracking."""
        stats = execution_engine.get_execution_stats()
        
        assert 'total_executions' in stats
        assert 'successful_executions' in stats
        assert 'failed_executions' in stats
        assert 'success_rate' in stats
        assert 'failure_rate' in stats
        assert 'average_execution_time' in stats


class TestHookConfigurationSystem:
    """Test suite for hook configuration system."""
    
    @pytest.fixture
    def config_system(self):
        return HookConfigurationSystem()
    
    def test_hook_registration(self, config_system):
        """Test hook registration."""
        def test_handler(context):
            return 'test'
        
        hook_config = HookConfiguration(
            hook_id='test_hook',
            hook_type=HookType.PRE_TOOL_USE,
            handler=test_handler
        )
        
        success = config_system.register_hook(hook_config)
        assert success is True
        
        # Check hook is stored
        retrieved = config_system.get_hook('test_hook')
        assert retrieved is not None
        assert retrieved.hook_id == 'test_hook'
    
    def test_hook_unregistration(self, config_system):
        """Test hook unregistration."""
        def test_handler(context):
            return 'test'
        
        hook_config = HookConfiguration(
            hook_id='removable_hook',
            hook_type=HookType.POST_TOOL_USE,
            handler=test_handler
        )
        
        config_system.register_hook(hook_config)
        success = config_system.unregister_hook('removable_hook')
        assert success is True
        
        # Check hook is removed
        retrieved = config_system.get_hook('removable_hook')
        assert retrieved is None
    
    def test_hooks_by_type(self, config_system):
        """Test getting hooks by type."""
        def handler1(context):
            return '1'
        
        def handler2(context):
            return '2'
        
        hook1 = HookConfiguration('hook1', HookType.PRE_TOOL_USE, handler1, priority=2)
        hook2 = HookConfiguration('hook2', HookType.PRE_TOOL_USE, handler2, priority=1)
        hook3 = HookConfiguration('hook3', HookType.POST_TOOL_USE, handler1, priority=3)
        
        config_system.register_hook(hook1)
        config_system.register_hook(hook2)
        config_system.register_hook(hook3)
        
        pre_hooks = config_system.get_hooks_by_type(HookType.PRE_TOOL_USE)
        post_hooks = config_system.get_hooks_by_type(HookType.POST_TOOL_USE)
        
        assert len(pre_hooks) == 2
        assert len(post_hooks) == 1
        
        # Check priority ordering
        assert pre_hooks[0].priority == 2  # Higher priority first
        assert pre_hooks[1].priority == 1
    
    def test_hook_status_update(self, config_system):
        """Test enabling/disabling hooks."""
        def test_handler(context):
            return 'test'
        
        hook_config = HookConfiguration(
            hook_id='status_test_hook',
            hook_type=HookType.ERROR_DETECTION,
            handler=test_handler,
            enabled=True
        )
        
        config_system.register_hook(hook_config)
        
        # Disable hook
        success = config_system.update_hook_status('status_test_hook', False)
        assert success is True
        
        hook = config_system.get_hook('status_test_hook')
        assert hook.enabled is False
        
        # Should not appear in enabled hooks list
        enabled_hooks = config_system.get_hooks_by_type(HookType.ERROR_DETECTION)
        assert len([h for h in enabled_hooks if h.hook_id == 'status_test_hook']) == 0
    
    def test_configuration_stats(self, config_system):
        """Test configuration statistics."""
        def test_handler(context):
            return 'test'
        
        # Add some hooks
        for i in range(3):
            hook = HookConfiguration(
                hook_id=f'stats_hook_{i}',
                hook_type=HookType.PRE_TOOL_USE,
                handler=test_handler,
                enabled=(i % 2 == 0)  # Alternate enabled/disabled
            )
            config_system.register_hook(hook)
        
        stats = config_system.get_configuration_stats()
        
        assert stats['total_hooks'] == 3
        assert stats['enabled_hooks'] == 2  # 0 and 2 are enabled
        assert stats['disabled_hooks'] == 1  # 1 is disabled


class TestHookMonitoringSystem:
    """Test suite for hook monitoring system."""
    
    @pytest.fixture
    def monitoring_system(self):
        return HookMonitoringSystem(max_history=50)
    
    def test_execution_recording(self, monitoring_system):
        """Test recording of hook execution results."""
        result = HookExecutionResult(
            hook_id='test_hook',
            success=True,
            execution_time=1.5,
            result={'data': 'test'}
        )
        
        monitoring_system.record_execution(result)
        
        assert monitoring_system.performance_metrics['total_hooks_executed'] == 1
        assert monitoring_system.performance_metrics['peak_execution_time'] == 1.5
        assert len(monitoring_system.execution_history) == 1
    
    def test_error_recording(self, monitoring_system):
        """Test recording of error detection results."""
        error_result = ErrorDetectionResult(
            error_detected=True,
            error_type='test_error',
            severity=ErrorSeverity.HIGH,
            details={'test': 'data'}
        )
        
        monitoring_system.record_error_detection(error_result)
        
        assert monitoring_system.performance_metrics['total_errors_detected'] == 1
        assert len(monitoring_system.error_history) == 1
    
    def test_performance_report(self, monitoring_system):
        """Test performance report generation."""
        # Add some execution results
        for i in range(10):
            result = HookExecutionResult(
                hook_id=f'hook_{i}',
                success=(i % 4 != 0),  # 75% success rate
                execution_time=0.5 + (i * 0.1)
            )
            monitoring_system.record_execution(result)
        
        # Add some errors
        for i in range(3):
            error = ErrorDetectionResult(
                error_detected=True,
                error_type=f'error_{i}',
                severity=ErrorSeverity.MEDIUM,
                details={}
            )
            monitoring_system.record_error_detection(error)
        
        report = monitoring_system.get_performance_report()
        
        assert 'performance_metrics' in report
        assert 'recent_statistics' in report
        assert 'error_severity_distribution' in report
        
        stats = report['recent_statistics']
        assert stats['success_rate'] == 0.75  # 75% success
        assert stats['executions_count'] == 10
        assert stats['errors_count'] == 3
    
    def test_history_limit(self, monitoring_system):
        """Test that history is properly limited."""
        # Add more results than the limit
        for i in range(60):  # More than max_history of 50
            result = HookExecutionResult(
                hook_id=f'hook_{i}',
                success=True,
                execution_time=0.1
            )
            monitoring_system.record_execution(result)
        
        assert len(monitoring_system.execution_history) == 50  # Should be limited
        # Should have most recent results
        assert monitoring_system.execution_history[-1].hook_id == 'hook_59'


class TestHookProcessingService:
    """Test suite for main hook processing service."""
    
    @pytest.fixture
    async def service(self):
        config = {
            'max_workers': 2,
            'max_history': 100
        }
        service = HookProcessingService(config)
        await service.start()
        yield service
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown(self):
        """Test service startup and shutdown."""
        service = HookProcessingService()
        
        assert service.is_running is False
        
        await service.start()
        assert service.is_running is True
        assert service.startup_time is not None
        
        await service.stop()
        assert service.is_running is False
    
    @pytest.mark.asyncio
    async def test_hook_registration_integration(self, service):
        """Test hook registration integration."""
        async def test_hook(context):
            return {'integrated': True}
        
        hook_config = HookConfiguration(
            hook_id='integration_hook',
            hook_type=HookType.PRE_TOOL_USE,
            handler=test_hook
        )
        
        success = service.register_hook(hook_config)
        assert success is True
        
        # Test hook execution
        results = await service.process_hooks(HookType.PRE_TOOL_USE, {'test': 'data'})
        
        integration_results = [r for r in results if r.hook_id == 'integration_hook']
        assert len(integration_results) > 0
        assert integration_results[0].success is True
    
    @pytest.mark.asyncio
    async def test_subagent_transcript_analysis(self, service):
        """Test complete subagent transcript analysis."""
        transcript = """
        Documentation Agent starting...
        Processing markdown files...
        ERROR: subprocess failed with exit code 1
        Memory allocation failed
        Agent terminated unexpectedly
        """
        
        result = await service.analyze_subagent_transcript(transcript, 'documentation_agent')
        
        assert result['analysis_complete'] is True
        assert result['agent_type'] == 'documentation_agent'
        assert result['transcript_length'] == len(transcript)
        assert result['errors_detected'] >= 0
        assert 'execution_results' in result
        assert 'analysis_timestamp' in result
    
    @pytest.mark.asyncio
    async def test_default_hooks_registration(self, service):
        """Test that default hooks are properly registered."""
        status = service.get_service_status()
        config_stats = status['configuration_stats']
        
        assert config_stats['total_hooks'] > 0
        assert config_stats['enabled_hooks'] > 0
        
        # Check specific default hooks exist
        subagent_hooks = service.configuration_system.get_hooks_by_type(HookType.SUBAGENT_STOP)
        assert len(subagent_hooks) > 0
        
        performance_hooks = service.configuration_system.get_hooks_by_type(HookType.PERFORMANCE_MONITOR)
        assert len(performance_hooks) > 0
    
    def test_service_status(self, service):
        """Test service status reporting."""
        status = service.get_service_status()
        
        assert 'service_info' in status
        assert 'error_detection_stats' in status
        assert 'execution_stats' in status
        assert 'configuration_stats' in status
        assert 'performance_report' in status
        
        service_info = status['service_info']
        assert service_info['is_running'] is True
        assert service_info['startup_time'] is not None


class TestAgentIntegrationHooks:
    """Test suite for agent integration hooks."""
    
    @pytest_asyncio.fixture
    async def integration_hooks(self):
        service = HookProcessingService()
        await service.start()
        hooks = AgentIntegrationHooks(service)
        yield hooks
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_documentation_agent_setup(self, integration_hooks):
        """Test documentation agent hooks setup."""
        await integration_hooks.setup_documentation_agent_hooks()
        
        service = integration_hooks.service
        
        # Check hooks are registered
        pre_hooks = service.configuration_system.get_hooks_by_type(HookType.PRE_TOOL_USE)
        post_hooks = service.configuration_system.get_hooks_by_type(HookType.POST_TOOL_USE)
        error_hooks = service.configuration_system.get_hooks_by_type(HookType.ERROR_DETECTION)
        
        doc_pre_hooks = [h for h in pre_hooks if 'doc_agent' in h.hook_id]
        doc_post_hooks = [h for h in post_hooks if 'doc_agent' in h.hook_id]
        doc_error_hooks = [h for h in error_hooks if 'doc_agent' in h.hook_id]
        
        assert len(doc_pre_hooks) > 0
        assert len(doc_post_hooks) > 0
        assert len(doc_error_hooks) > 0
    
    @pytest.mark.asyncio
    async def test_qa_agent_setup(self, integration_hooks):
        """Test QA agent hooks setup."""
        await integration_hooks.setup_qa_agent_hooks()
        
        service = integration_hooks.service
        
        # Check QA-specific hooks are registered
        pre_hooks = service.configuration_system.get_hooks_by_type(HookType.PRE_TOOL_USE)
        post_hooks = service.configuration_system.get_hooks_by_type(HookType.POST_TOOL_USE)
        subagent_hooks = service.configuration_system.get_hooks_by_type(HookType.SUBAGENT_STOP)
        
        qa_hooks = [h for h in (pre_hooks + post_hooks + subagent_hooks) if 'qa_agent' in h.hook_id]
        assert len(qa_hooks) >= 3  # pre, post, and failure detection
    
    @pytest.mark.asyncio
    async def test_version_control_agent_setup(self, integration_hooks):
        """Test version control agent hooks setup."""
        await integration_hooks.setup_version_control_hooks()
        
        service = integration_hooks.service
        
        # Check VC-specific hooks are registered
        all_hooks = []
        for hook_type in HookType:
            all_hooks.extend(service.configuration_system.get_hooks_by_type(hook_type))
        
        vc_hooks = [h for h in all_hooks if 'vc_agent' in h.hook_id]
        assert len(vc_hooks) >= 3  # pre-git, post-git, and conflict detection
    
    def test_integration_stats(self, integration_hooks):
        """Test integration statistics tracking."""
        stats = integration_hooks.get_integration_stats()
        
        assert 'agents_monitored' in stats
        assert 'errors_prevented' in stats
        assert 'restarts_triggered' in stats
        assert 'service_status' in stats


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    @pytest.mark.asyncio
    async def test_quick_error_analysis(self):
        """Test quick error analysis utility."""
        transcript = """
        Processing request...
        Subprocess failed with error
        Agent terminated unexpectedly
        """
        
        result = await quick_error_analysis(transcript, 'test_agent')
        
        assert 'analysis_complete' in result
        assert result['agent_type'] == 'test_agent'
        assert 'errors_detected' in result
    
    @pytest.mark.asyncio
    async def test_create_hook_processing_service(self):
        """Test service creation utility."""
        config = {
            'max_workers': 1,
            'max_history': 10
        }
        
        service = await create_hook_processing_service(config)
        
        try:
            assert service.is_running is True
            assert service.config == config
            
            status = service.get_service_status()
            assert status['service_info']['is_running'] is True
            
        finally:
            await service.stop()


class TestHookProcessingDemo:
    """Test suite for demonstration functionality."""
    
    @pytest.fixture
    def demo(self):
        return HookProcessingDemo()
    
    @pytest.mark.asyncio
    async def test_demo_setup(self, demo):
        """Test demonstration environment setup."""
        await demo.setup_demo_environment()
        
        try:
            assert demo.service is not None
            assert demo.integration_hooks is not None
            assert demo.service.is_running is True
            
        finally:
            if demo.service:
                await demo.service.stop()
    
    @pytest.mark.asyncio
    async def test_subagent_stop_demonstration(self, demo):
        """Test SubagentStop demonstration."""
        await demo.setup_demo_environment()
        
        try:
            # This should complete without errors
            await demo.demonstrate_subagent_stop_detection()
            
        finally:
            if demo.service:
                await demo.service.stop()


# Performance and stress tests
class TestPerformanceAndStress:
    """Performance and stress test suite."""
    
    @pytest.mark.asyncio
    async def test_concurrent_hook_execution(self):
        """Test concurrent execution of multiple hooks."""
        service = await create_hook_processing_service({'max_workers': 4})
        
        try:
            # Register multiple hooks
            for i in range(10):
                async def test_hook(context, hook_id=i):
                    await asyncio.sleep(0.1)
                    return f'result_{hook_id}'
                
                hook = HookConfiguration(
                    hook_id=f'concurrent_hook_{i}',
                    hook_type=HookType.PRE_TOOL_USE,
                    handler=test_hook,
                    priority=i
                )
                service.register_hook(hook)
            
            # Execute all hooks concurrently
            start_time = time.time()
            results = await service.process_hooks(HookType.PRE_TOOL_USE, {})
            execution_time = time.time() - start_time
            
            assert len(results) == 10
            assert all(r.success for r in results)
            # Should be faster than sequential execution due to concurrency
            assert execution_time < 1.0  # Less than 10 * 0.1s
            
        finally:
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_large_transcript_analysis(self):
        """Test analysis of large transcripts."""
        # Create a large transcript with multiple error patterns
        error_patterns = [
            "subprocess failed with exit code 1",
            "memory allocation failed",
            "network timeout occurred",
            "version mismatch detected",
            "out of memory error"
        ]
        
        # Create large transcript (simulate real-world scenarios)
        large_transcript = ""
        for i in range(1000):
            if i % 100 == 0:  # Add errors periodically
                large_transcript += f"Line {i}: {error_patterns[i // 100 % len(error_patterns)]}\n"
            else:
                large_transcript += f"Line {i}: Normal processing output\n"
        
        service = await create_hook_processing_service()
        
        try:
            start_time = time.time()
            result = await service.analyze_subagent_transcript(large_transcript, 'test_agent')
            analysis_time = time.time() - start_time
            
            assert result['analysis_complete'] is True
            assert result['errors_detected'] > 0
            # Should complete in reasonable time
            assert analysis_time < 5.0
            
        finally:
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability over many operations."""
        service = await create_hook_processing_service({'max_history': 100})
        
        try:
            # Perform many operations to test memory stability
            for i in range(500):
                # Alternate between different operations
                if i % 3 == 0:
                    await service.analyze_subagent_transcript(
                        f"Test transcript {i} with some content",
                        'test_agent'
                    )
                elif i % 3 == 1:
                    await service.process_hooks(HookType.PERFORMANCE_MONITOR, {'iteration': i})
                else:
                    await service.process_hooks(HookType.ERROR_DETECTION, {'data': f'test_{i}'})
            
            # Service should still be responsive
            status = service.get_service_status()
            assert status['service_info']['is_running'] is True
            
            # History should be properly limited
            history_len = len(service.monitoring_system.execution_history)
            assert history_len <= 100  # Respects max_history setting
            
        finally:
            await service.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])