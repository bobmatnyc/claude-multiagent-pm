# Async-by-Default Hook Processing with Project-Based Logging

## Overview

The Hook Processing Service has been enhanced to default to async execution and implement comprehensive project-based logging. This improvement provides better performance and detailed logging capabilities for hook execution monitoring.

## Key Features

### 1. Async-by-Default Execution
- **Default Behavior**: All hooks now prefer async execution unless explicitly configured otherwise
- **Backward Compatibility**: Existing sync hooks continue to work but run in async mode via executor
- **Force Sync Option**: New `force_sync` parameter allows explicit sync execution when needed

### 2. Project-Based Hook Logging
- **Automatic Directory Creation**: Creates `$PWD/.claude-pm/hooks/logs/` directory structure
- **Hook Type Organization**: Separate subdirectories for each hook type
- **Log Rotation**: Automatic log file rotation based on size limits
- **Log Cleanup**: Configurable retention of log files per hook type

### 3. Enhanced Configuration Options
- **`prefer_async`**: Default `True` - enables async execution
- **`force_sync`**: Default `False` - forces sync execution when `True`
- **`max_log_files`**: Maximum number of log files to retain per hook type
- **`max_log_size_mb`**: Maximum size of individual log files in MB
- **`project_root`**: Project root directory (defaults to current working directory)

## Usage Examples

### Basic Hook Registration (Async by Default)

```python
from claude_pm.services.hook_processing_service import HookProcessingService, HookConfiguration, HookType

# Create service with project-based logging
service = HookProcessingService({
    'project_root': '/path/to/project',
    'max_log_files': 10,
    'max_log_size_mb': 10
})

# Register async hook (preferred)
async def async_hook(context):
    await asyncio.sleep(0.1)  # Async work
    return "Async result"

hook_config = HookConfiguration(
    hook_id='my_async_hook',
    hook_type=HookType.PRE_TOOL_USE,
    handler=async_hook,
    prefer_async=True  # Default
)

service.register_hook(hook_config)
```

### Sync Hook with Async Execution

```python
# Register sync hook (runs in async mode by default)
def sync_hook(context):
    return "Sync result"

hook_config = HookConfiguration(
    hook_id='my_sync_hook',
    hook_type=HookType.POST_TOOL_USE,
    handler=sync_hook,
    prefer_async=True  # Will run in executor
)

service.register_hook(hook_config)
```

### Force Sync Execution

```python
# Force sync execution
def force_sync_hook(context):
    return "Force sync result"

hook_config = HookConfiguration(
    hook_id='my_force_sync_hook',
    hook_type=HookType.ERROR_DETECTION,
    handler=force_sync_hook,
    prefer_async=True,
    force_sync=True  # Forces sync execution
)

service.register_hook(hook_config)
```

## Project-Based Logging

### Directory Structure

```
$PWD/.claude-pm/hooks/logs/
├── pre_tool_use/
│   ├── my_hook_20250715.log
│   └── my_hook_20250715.20250715_143022.log (rotated)
├── post_tool_use/
│   └── validation_hook_20250715.log
├── error_detection/
│   └── error_detection_20250715.log
└── performance_monitor/
    └── performance_monitor_20250715.log
```

### Log Entry Format

```json
{
  "timestamp": "2025-07-15T09:43:52.338289",
  "hook_id": "my_async_hook",
  "hook_type": "pre_tool_use",
  "success": true,
  "execution_time": 0.1010751724243164,
  "priority": 100,
  "timeout": 30.0,
  "prefer_async": true,
  "force_sync": false,
  "context_keys": ["test_data"],
  "result_type": "str",
  "error": null,
  "metadata": {
    "execution_mode": "async",
    "prefer_async": true,
    "force_sync": false,
    "is_async_handler": true
  }
}
```

### Error Detection Logging

```json
{
  "timestamp": "2025-07-15T09:43:52.340123",
  "error_type": "subagent_stop",
  "severity": "high",
  "error_detected": true,
  "details": {
    "matched_pattern": "subprocess\\s+(?:failed|error|crashed|terminated)",
    "matched_text": "subprocess failed",
    "context": "Agent starting...\\nERROR: subprocess failed with exit code 1\\nMemory allocation failed",
    "position": 25,
    "analysis_context": {"agent_type": "test_agent"}
  },
  "suggested_action": "restart_subagent",
  "context": {"transcript": "...", "agent_type": "test_agent"}
}
```

## Service API Updates

### New Methods

```python
# Get project hook logs
logs = service.get_hook_logs(HookType.PRE_TOOL_USE, 'my_hook', limit=100)

# Get project hook summary
summary = service.get_project_hook_summary()

# Clean up old logs
cleaned_count = service.cleanup_project_logs(days_old=30)
```

### Enhanced Service Status

```python
status = service.get_service_status()
# Now includes:
# - project_logging: Project-based logging summary
# - Enhanced execution stats with async/sync breakdown
```

## Configuration Options

### Service Configuration

```python
config = {
    'max_workers': 4,
    'max_history': 1000,
    'max_log_files': 10,          # New: Max log files per hook type
    'max_log_size_mb': 10,        # New: Max log file size in MB
    'project_root': None,         # New: Project root (defaults to CWD)
    'alert_thresholds': {
        'execution_time': 10.0,
        'error_rate': 0.1,
        'failure_rate': 0.05
    },
    'async_by_default': True      # New: Default async behavior
}
```

### Hook Configuration

```python
hook_config = HookConfiguration(
    hook_id='my_hook',
    hook_type=HookType.PRE_TOOL_USE,
    handler=my_handler,
    priority=100,
    enabled=True,
    timeout=30.0,
    retry_count=3,
    prefer_async=True,    # New: Prefer async execution
    force_sync=False,     # New: Force sync execution
    metadata={}
)
```

## Performance Improvements

### Async Execution Benefits
- **Concurrent Processing**: Multiple hooks can run concurrently
- **Better Resource Utilization**: Non-blocking execution for I/O operations
- **Scalability**: Improved performance under high load

### Execution Mode Tracking
- **Detailed Metadata**: Track execution mode for each hook
- **Performance Analysis**: Monitor async vs sync execution patterns
- **Optimization Insights**: Identify hooks that benefit from async execution

## Migration Guide

### Existing Code Compatibility
- **No Breaking Changes**: Existing hooks continue to work unchanged
- **Default Behavior**: Hooks now run in async mode by default
- **Opt-out Option**: Use `force_sync=True` to maintain sync behavior

### Best Practices
1. **New Hooks**: Write async handlers for better performance
2. **Existing Hooks**: Review and convert to async where beneficial
3. **I/O Operations**: Always use async for network/file operations
4. **CPU-Intensive Tasks**: Consider `force_sync=True` for heavy computation

## Testing

Run the test suite to verify the implementation:

```bash
python test_async_hook_processing.py
```

The test covers:
- ✅ Async hook registration and execution
- ✅ Sync hook execution in async mode
- ✅ Force sync execution
- ✅ Project-based logging directory creation
- ✅ Log file rotation and cleanup
- ✅ Error detection logging
- ✅ Service status with project logging
- ✅ Hook log retrieval

## Troubleshooting

### Common Issues

1. **Log Directory Creation Failures**
   - Ensure write permissions on project root
   - Check available disk space
   - Verify project root path is valid

2. **Async Execution Errors**
   - Review handler for async compatibility
   - Check for blocking operations in async handlers
   - Consider using `force_sync=True` for problematic handlers

3. **Log File Rotation Issues**
   - Verify log file size limits are appropriate
   - Check disk space for log rotation
   - Ensure proper cleanup of old log files

### Performance Monitoring

```python
# Monitor hook execution patterns
status = service.get_service_status()
exec_stats = status['execution_stats']
project_logs = status['project_logging']

print(f"Success rate: {exec_stats['success_rate']:.2%}")
print(f"Average execution time: {exec_stats['average_execution_time']:.4f}s")
print(f"Total log files: {project_logs['total_log_files']}")
```

## Future Enhancements

### Planned Features
- **Log Streaming**: Real-time log streaming for monitoring
- **Metrics Export**: Export metrics to external monitoring systems
- **Advanced Filtering**: Enhanced log filtering and search capabilities
- **Compression**: Automatic compression of rotated log files
- **Alerting**: Configurable alerting based on hook performance

### API Improvements
- **Batch Hook Operations**: Bulk hook registration and management
- **Hook Dependencies**: Define execution order dependencies
- **Conditional Execution**: Execute hooks based on context conditions
- **Resource Management**: Advanced resource allocation and limiting

---

**Implementation Date**: 2025-07-15  
**Version**: 1.0.0  
**Status**: ✅ Complete and Tested