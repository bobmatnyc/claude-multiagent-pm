# Hook Processing Service Module Structure

This directory contains the refactored hook processing service implementation, organized into focused modules for better maintainability.

## Module Overview

### Core Modules

1. **`models.py`** (~80 lines)
   - Data classes: `HookExecutionResult`, `ErrorDetectionResult`, `HookConfiguration`
   - Enums: `HookType`, `ErrorSeverity`
   - Core data structures used throughout the service

2. **`logging.py`** (~220 lines)
   - `ProjectBasedHookLogger`: Project-based hook logging with automatic directory management
   - Log rotation and cleanup functionality
   - Hook execution and error logging

3. **`error_detection.py`** (~190 lines)
   - `ErrorDetectionSystem`: System for detecting errors in subprocess transcripts
   - Pattern-based error detection
   - Agent-specific error analysis

4. **`execution.py`** (~170 lines)
   - `HookExecutionEngine`: Engine for executing hooks with sync/async support
   - Timeout handling and error management
   - Batch execution capabilities

5. **`configuration.py`** (~120 lines)
   - `HookConfigurationSystem`: Hook registration and management
   - Hook grouping by type
   - Weak reference management

6. **`monitoring.py`** (~210 lines)
   - `HookMonitoringSystem`: Performance monitoring and health tracking
   - Alert threshold management
   - Performance reporting and trends

7. **`handlers.py`** (~150 lines)
   - `SubagentStopHookExample`: Example hook implementations
   - Default error detection handlers
   - Resource exhaustion detection

8. **`utils.py`** (~50 lines)
   - Factory functions: `create_hook_processing_service`
   - Default configuration constants
   - Helper utilities

9. **`__init__.py`** (~250 lines)
   - `HookProcessingService`: Main facade class
   - Service orchestration and integration
   - Public API and re-exports

## Usage Example

```python
from claude_pm.services.hook_processing_service import (
    HookProcessingService,
    HookConfiguration,
    HookType,
    create_hook_processing_service
)

# Create and start service
service = await create_hook_processing_service({
    'max_workers': 4,
    'project_root': '/path/to/project'
})

# Register a custom hook
service.register_hook(HookConfiguration(
    hook_id='my_hook',
    hook_type=HookType.PRE_TOOL_USE,
    handler=my_handler_function,
    priority=100
))

# Process hooks
results = await service.process_hooks(
    HookType.PRE_TOOL_USE,
    {'context': 'data'}
)

# Analyze subagent transcript
analysis = await service.analyze_subagent_transcript(
    transcript="Agent output...",
    agent_type="qa_agent"
)
```

## Backward Compatibility

The original `hook_processing_service.py` file has been replaced with a stub that imports all public APIs from this directory structure. All existing imports and usage patterns continue to work without changes.

## Architecture Benefits

- **Modularity**: Each component has a clear responsibility
- **Testability**: Individual modules can be tested in isolation
- **Maintainability**: Smaller files are easier to understand and modify
- **Performance**: No impact on runtime performance
- **Extensibility**: Easy to add new hook types or handlers