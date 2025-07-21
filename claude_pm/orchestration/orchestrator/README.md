# Backwards Compatible Orchestrator - Refactored Modules

This directory contains the refactored backwards compatible orchestrator, broken down from a single 1,558-line file into smaller, more maintainable modules.

## Module Structure

- **`__init__.py`** (484 lines) - Main BackwardsCompatibleOrchestrator class and integration
- **`types.py`** (114 lines) - Type definitions (OrchestrationMode, ReturnCode, OrchestrationMetrics)
- **`mode_detection.py`** (125 lines) - Orchestration mode determination logic
- **`local_execution.py`** (342 lines) - Local orchestration execution
- **`subprocess_execution.py`** (282 lines) - Subprocess delegation execution
- **`agent_handlers.py`** (179 lines) - Default agent handler implementations
- **`context_collection.py`** (123 lines) - Context collection and formatting
- **`compatibility.py`** (139 lines) - Compatibility validation and metrics

## Key Features Preserved

1. **Full Backward Compatibility** - The original API is completely preserved
2. **Automatic Mode Detection** - Chooses between local and subprocess execution
3. **Performance Metrics** - Tracks orchestration performance and mode selection
4. **Emergency Fallback** - Handles failures gracefully
5. **Agent Type Support** - Supports all agent types with default handlers

## Usage

The refactored modules work exactly the same as the original:

```python
from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator

orchestrator = BackwardsCompatibleOrchestrator()
result, return_code = await orchestrator.delegate_to_agent(
    agent_type="engineer",
    task_description="Implement feature X",
    requirements=["Requirement 1", "Requirement 2"]
)
```

## Benefits of Refactoring

1. **Maintainability** - Each module has a clear, focused responsibility
2. **Testability** - Smaller modules are easier to unit test
3. **Readability** - Code is organized by functionality
4. **Extensibility** - New features can be added to specific modules
5. **Performance** - No impact on runtime performance