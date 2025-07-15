# Hook Processing Service Documentation

## Overview

The Hook Processing Service is a comprehensive system for managing and executing hooks in agent workflows, with specialized focus on error detection and subprocess monitoring. It provides real-time error detection, performance monitoring, and automated recovery mechanisms for Claude PM Framework agents.

## Key Features

- **Real-time Error Detection**: Automated parsing of subprocess transcripts for error patterns
- **SubagentStop Detection**: Specialized detection for agent crashes and subprocess failures
- **Performance Monitoring**: Comprehensive performance metrics and alerting
- **Concurrent Execution**: Async/await support for parallel hook processing
- **Extensible Architecture**: Plugin-based hook system with configurable priorities
- **Resource Management**: Automatic cleanup and memory management

## Architecture Components

### 1. ErrorDetectionSystem

Analyzes subprocess transcripts and agent outputs for error patterns:

```python
from claude_pm.services.hook_processing_service import ErrorDetectionSystem

# Initialize error detection
error_detector = ErrorDetectionSystem()

# Analyze transcript for errors
transcript = """
Agent starting...
ERROR: subprocess failed with exit code 1
Memory allocation failed
"""

results = await error_detector.analyze_transcript(transcript)
for result in results:
    print(f"Error detected: {result.error_type} - {result.severity}")
```

### 2. HookExecutionEngine

Manages hook execution with timeout and concurrency support:

```python
from claude_pm.services.hook_processing_service import HookExecutionEngine, HookConfiguration, HookType

# Create execution engine
engine = HookExecutionEngine(max_workers=4)

# Define hook function
async def my_hook(context):
    return {"processed": True, "data": context.get("input_data")}

# Create hook configuration
hook_config = HookConfiguration(
    hook_id="my_processing_hook",
    hook_type=HookType.PRE_TOOL_USE,
    handler=my_hook,
    priority=100,
    timeout=30.0
)

# Execute hook
result = await engine.execute_hook(hook_config, {"input_data": "test"})
print(f"Hook execution: {'Success' if result.success else 'Failed'}")
```

### 3. HookConfigurationSystem

Manages hook registration and organization:

```python
from claude_pm.services.hook_processing_service import HookConfigurationSystem

# Initialize configuration system
config_system = HookConfigurationSystem()

# Register hook
success = config_system.register_hook(hook_config)

# Get hooks by type
pre_tool_hooks = config_system.get_hooks_by_type(HookType.PRE_TOOL_USE)

# Enable/disable hooks
config_system.update_hook_status("my_processing_hook", enabled=False)
```

### 4. HookMonitoringSystem

Tracks performance and provides analytics:

```python
from claude_pm.services.hook_processing_service import HookMonitoringSystem

# Initialize monitoring
monitoring = HookMonitoringSystem(max_history=1000)

# Record execution results
monitoring.record_execution(execution_result)

# Get performance report
report = monitoring.get_performance_report()
print(f"Success rate: {report['recent_statistics']['success_rate']:.2%}")
```

### 5. HookProcessingService

Main service that orchestrates all components:

```python
from claude_pm.services.hook_processing_service import create_hook_processing_service

# Create and start service
service = await create_hook_processing_service({
    'max_workers': 4,
    'max_history': 1000
})

# Analyze subagent transcript
result = await service.analyze_subagent_transcript(
    transcript="Agent output with potential errors...",
    agent_type="documentation_agent"
)

# Process hooks by type
hook_results = await service.process_hooks(
    HookType.PRE_TOOL_USE,
    {"tool_name": "generate_docs", "context": {...}}
)

# Stop service when done
await service.stop()
```

## Hook Types

### Available Hook Types

1. **PRE_TOOL_USE**: Executed before tool usage
2. **POST_TOOL_USE**: Executed after tool completion
3. **SUBAGENT_STOP**: Triggered when subagent failures are detected
4. **ERROR_DETECTION**: General error detection and analysis
5. **PERFORMANCE_MONITOR**: Performance monitoring and optimization
6. **WORKFLOW_TRANSITION**: Workflow state changes

### Hook Priority System

Hooks are executed in priority order (highest to lowest):
- Priority 100: Critical system hooks
- Priority 90: Error detection hooks
- Priority 80: Agent-specific hooks
- Priority 50: Default processing hooks
- Priority 10: Cleanup and logging hooks

## Error Detection Patterns

### Supported Error Types

1. **subagent_stop**: Subprocess failures and agent crashes
2. **version_mismatch**: Dependency version conflicts
3. **resource_exhaustion**: Memory, disk, or connection limits
4. **network_issues**: Network connectivity problems
5. **data_corruption**: Data integrity issues

### Pattern Examples

```python
# Subagent stop patterns
patterns = [
    r'subprocess\s+(?:failed|error|crashed|terminated)',
    r'agent\s+(?:stopped|failed|crashed|terminated)',
    r'memory\s+(?:error|exceeded|allocation\s+failed)',
    r'timeout.*agent',
]

# Network issue patterns
network_patterns = [
    r'network\s+(?:error|timeout|unreachable)',
    r'connection\s+(?:refused|timeout|reset)',
    r'ssl\s+(?:error|handshake\s+failed)',
]
```

## Agent Integration Examples

### Documentation Agent Hooks

```python
from claude_pm.services.hook_examples import AgentIntegrationHooks

async def setup_documentation_monitoring():
    # Create service
    service = await create_hook_processing_service()
    
    # Setup integration hooks
    integration = AgentIntegrationHooks(service)
    await integration.setup_documentation_agent_hooks()
    
    # Test documentation agent
    context = {
        'tool_name': 'generate_api_docs',
        'agent_context': {
            'project_root': '/project/path',
            'documentation_type': 'api',
            'target_audience': 'developers'
        }
    }
    
    # Execute pre-tool hooks
    results = await service.process_hooks(HookType.PRE_TOOL_USE, context)
    
    return service
```

### QA Agent Hooks

```python
async def setup_qa_monitoring():
    service = await create_hook_processing_service()
    integration = AgentIntegrationHooks(service)
    await integration.setup_qa_agent_hooks()
    
    # Test QA agent
    context = {
        'test_config': {
            'test_paths': ['tests/'],
            'parallel_execution': True
        },
        'test_results': {
            'passed': 45,
            'failed': 3,
            'coverage': 78.5
        }
    }
    
    # Execute post-tool hooks
    results = await service.process_hooks(HookType.POST_TOOL_USE, context)
    
    return service
```

### Version Control Agent Hooks

```python
async def setup_version_control_monitoring():
    service = await create_hook_processing_service()
    integration = AgentIntegrationHooks(service)
    await integration.setup_version_control_hooks()
    
    # Test version control operations
    context = {
        'git_command': 'git push origin main',
        'repo_state': {
            'has_uncommitted_changes': False,
            'current_branch': 'main'
        }
    }
    
    # Execute pre-git hooks
    results = await service.process_hooks(HookType.PRE_TOOL_USE, context)
    
    return service
```

## Performance Monitoring

### Key Metrics

- **Execution Time**: Average and peak execution times
- **Success Rate**: Percentage of successful hook executions
- **Error Rate**: Frequency of error detection
- **Throughput**: Hooks processed per second
- **Resource Usage**: Memory and CPU utilization

### Alert Thresholds

```python
# Configure alert thresholds
config = {
    'alert_thresholds': {
        'execution_time': 10.0,  # seconds
        'error_rate': 0.1,       # 10%
        'failure_rate': 0.05     # 5%
    }
}

service = await create_hook_processing_service(config)
```

### Performance Report

```python
# Get comprehensive performance report
report = service.monitoring_system.get_performance_report()

print(f"Total executions: {report['performance_metrics']['total_hooks_executed']}")
print(f"Success rate: {report['recent_statistics']['success_rate']:.2%}")
print(f"Average execution time: {report['performance_metrics']['average_execution_time']:.3f}s")

# Check for alerts
for alert in report['alerts']:
    print(f"Alert: {alert['type']} - {alert['message']}")
```

## Error Recovery Strategies

### Automatic Recovery Actions

1. **restart_subagent**: Restart failed agent subprocess
2. **update_dependencies**: Update conflicting dependencies
3. **cleanup_resources**: Free up system resources
4. **retry_with_backoff**: Retry operation with exponential backoff
5. **restore_from_backup**: Restore corrupted data

### Custom Recovery Hooks

```python
async def custom_recovery_hook(context):
    """Custom recovery logic for specific error types."""
    error_type = context.get('error_type')
    
    if error_type == 'subagent_stop':
        # Restart agent with updated configuration
        await restart_agent_with_config(context)
        return {'action': 'agent_restarted', 'success': True}
    
    elif error_type == 'resource_exhaustion':
        # Clean up resources and retry
        await cleanup_system_resources()
        return {'action': 'resources_cleaned', 'success': True}
    
    return {'action': 'no_recovery', 'success': False}

# Register recovery hook
recovery_config = HookConfiguration(
    hook_id='custom_recovery',
    hook_type=HookType.SUBAGENT_STOP,
    handler=custom_recovery_hook,
    priority=95
)

service.register_hook(recovery_config)
```

## Best Practices

### 1. Hook Design

- **Keep hooks focused**: Each hook should have a single responsibility
- **Use appropriate priorities**: Higher priority for critical operations
- **Handle exceptions**: Always include proper error handling
- **Set reasonable timeouts**: Prevent hanging operations

### 2. Error Pattern Definition

- **Be specific**: Use precise regex patterns to avoid false positives
- **Test thoroughly**: Validate patterns with real transcript data
- **Document patterns**: Include comments explaining pattern purpose
- **Regular updates**: Keep patterns current with system changes

### 3. Performance Optimization

- **Limit hook complexity**: Keep hook logic simple and fast
- **Use batch processing**: Process multiple items together when possible
- **Monitor resource usage**: Track memory and CPU consumption
- **Implement caching**: Cache frequently accessed data

### 4. Testing and Validation

- **Unit test hooks**: Test individual hook functions
- **Integration testing**: Test complete workflows
- **Performance testing**: Validate under realistic loads
- **Error scenario testing**: Test recovery mechanisms

## Troubleshooting

### Common Issues

1. **Hook Timeouts**
   - Increase timeout values for complex operations
   - Optimize hook logic to reduce execution time
   - Use async/await for I/O operations

2. **Memory Issues**
   - Reduce max_history setting
   - Implement proper cleanup in hooks
   - Monitor memory usage in production

3. **False Positives**
   - Refine error detection patterns
   - Add context-aware filtering
   - Implement pattern validation

4. **Performance Degradation**
   - Reduce number of concurrent workers
   - Optimize hook execution logic
   - Implement result caching

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create service with debug configuration
service = await create_hook_processing_service({
    'max_workers': 1,  # Reduce concurrency for debugging
    'max_history': 10  # Limit history for easier analysis
})

# Get detailed status
status = service.get_service_status()
print(json.dumps(status, indent=2, default=str))
```

## Example: Complete Integration

```python
import asyncio
import logging
from claude_pm.services.hook_processing_service import create_hook_processing_service
from claude_pm.services.hook_examples import AgentIntegrationHooks

async def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create service
    service = await create_hook_processing_service({
        'max_workers': 4,
        'max_history': 1000,
        'alert_thresholds': {
            'execution_time': 15.0,
            'error_rate': 0.15,
            'failure_rate': 0.08
        }
    })
    
    try:
        # Setup agent integration
        integration = AgentIntegrationHooks(service)
        await integration.setup_documentation_agent_hooks()
        await integration.setup_qa_agent_hooks()
        await integration.setup_version_control_hooks()
        
        # Example: Analyze problematic transcript
        transcript = """
        Documentation Agent starting...
        Processing markdown files...
        ERROR: subprocess failed with exit code 1
        Memory allocation failed
        Agent process terminated unexpectedly
        """
        
        result = await service.analyze_subagent_transcript(
            transcript, 
            'documentation_agent'
        )
        
        print(f"Analysis complete: {result['errors_detected']} errors detected")
        
        # Get service status
        status = service.get_service_status()
        print(f"Service status: {status['service_info']['is_running']}")
        
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive hook processing service provides robust error detection, monitoring, and recovery capabilities for Claude PM Framework agents, with special focus on SubagentStop detection and automated recovery mechanisms.