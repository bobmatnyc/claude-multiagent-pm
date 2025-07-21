# Backwards Compatible Orchestrator Refactoring Plan

## Current Structure Analysis
- Total: 1,558 lines
- Main class (BackwardsCompatibleOrchestrator): ~1,420 lines
- Supporting classes: ~138 lines

## Proposed Module Structure

```
claude_pm/orchestration/orchestrator/
├── __init__.py                    # Main BackwardsCompatibleOrchestrator class (~300 lines)
├── types.py                        # OrchestrationMode, ReturnCode, OrchestrationMetrics (~100 lines)
├── mode_detection.py               # Orchestration mode determination logic (~200 lines)
├── local_execution.py              # Local orchestration execution (~250 lines)
├── subprocess_execution.py         # Subprocess delegation execution (~250 lines)
├── agent_handlers.py               # Default agent handler implementations (~200 lines)
├── context_collection.py           # Context collection and formatting (~150 lines)
├── compatibility.py                # Compatibility validation and utilities (~100 lines)
└── README.md                       # Documentation
```

## Extraction Plan

### 1. types.py
- OrchestrationMode enum
- ReturnCode class
- OrchestrationMetrics dataclass

### 2. mode_detection.py
- `_determine_orchestration_mode()` method
- Related detection logic

### 3. local_execution.py
- `_execute_local_orchestration()` method
- Local agent invocation logic
- Response formatting for local execution

### 4. subprocess_execution.py
- `_execute_subprocess_delegation()` method
- `_execute_real_subprocess()` method
- `_generate_real_subprocess_instructions()` method
- `_emergency_subprocess_fallback()` method

### 5. agent_handlers.py
- `_register_default_agent_handlers()` method
- All the default agent handler implementations

### 6. context_collection.py
- `_collect_full_context()` method
- `_format_agent_prompt()` method
- Context formatting utilities

### 7. compatibility.py
- `validate_compatibility()` method
- Compatibility checking utilities
- Return code helpers

### 8. Main class (__init__.py)
- Constructor
- Main `delegate_to_agent()` method
- Public API methods
- Orchestration of the extracted modules

## Backward Compatibility Strategy
- Create wrapper at original location that imports from new structure
- Maintain all public method signatures
- No breaking changes to existing imports