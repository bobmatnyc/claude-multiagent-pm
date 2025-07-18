# Orchestration Default Mode Changes

## Summary
Modified the Claude PM framework to make orchestration mode the default behavior, with an opt-out mechanism instead of opt-in.

## Changes Made

### 1. OrchestrationDetector (`claude_pm/orchestration/orchestration_detector.py`)
- **Inverted Logic**: Orchestration is now ENABLED by default
- **New Flag**: Added `CLAUDE_PM_ORCHESTRATION: DISABLED` to explicitly disable orchestration
- **Legacy Support**: Kept `CLAUDE_PM_ORCHESTRATION: ENABLED` for backward compatibility
- **Modified Methods**:
  - `is_orchestration_enabled()`: Returns `True` by default unless explicitly disabled
  - Added `_detect_orchestration_disable()`: Checks for disable flag
  - Added `_detect_orchestration_enable()`: Checks for legacy enable flag
  - Added `_detect_flag()`: Generic flag detection method
  - Added `_detect_any_claude_md()`: Finds any CLAUDE.md file regardless of flags

### 2. BackwardsCompatibleOrchestrator (`claude_pm/orchestration/backwards_compatible_orchestrator.py`)
- Updated error messages to reflect new default behavior
- Changed fallback reason from "CLAUDE_PM_ORCHESTRATION not enabled" to "CLAUDE_PM_ORCHESTRATION explicitly disabled"

### 3. Tests (`tests/test_orchestration_detector.py`)
- Completely rewrote tests to reflect new default behavior
- Added tests for:
  - Default enabled behavior
  - Explicit disable flag
  - Legacy enable flag support
  - Error handling maintains default enabled state

## Usage

### To Use Orchestration (Default)
No action needed. Orchestration is enabled by default.

### To Disable Orchestration
Add the following to your CLAUDE.md file:
```
CLAUDE_PM_ORCHESTRATION: DISABLED
```

### Legacy Support
Existing CLAUDE.md files with `CLAUDE_PM_ORCHESTRATION: ENABLED` will continue to work as expected.

## Impact
- **Backward Compatible**: Existing projects with the enable flag will continue to work
- **New Default**: All new projects and projects without explicit flags will use orchestration mode
- **Opt-Out**: Projects can explicitly disable orchestration if needed

## TODO
- Update `test_backwards_compatible_orchestrator.py` to remove environment variable references
- Update any documentation that mentions environment variables for orchestration
- Consider updating the main CLAUDE.md file to mention the new default behavior

---

# Subprocess System Implementation

## Overview
Implemented a robust subprocess creation system that properly handles environment variables and ensures agent profiles can be loaded correctly in both local and subprocess orchestration modes.

## Key Components Created

### 1. `claude_pm/services/subprocess_runner.py`
- **Purpose**: Manages subprocess creation with proper environment setup
- **Key Features**:
  - Automatic framework path detection
  - Environment variable propagation (CLAUDE_PM_FRAMEWORK_PATH, PYTHONPATH)
  - Support for both sync and async subprocess execution
  - Environment testing capability
  - Standalone script generation

### 2. `claude_pm/services/agent_runner.py`
- **Purpose**: Entry point for agent subprocesses
- **Key Features**:
  - Loads agent profiles using CoreAgentLoader
  - Executes tasks with proper context
  - Can be run as a module: `python -m claude_pm.services.agent_runner`
  - Provides detailed execution output

### 3. Enhanced `claude_pm/services/core_agent_loader.py`
- **Purpose**: Improved framework path detection
- **Key Features**:
  - Multiple fallback strategies for finding framework path
  - Better handling of different deployment scenarios
  - Support for searching agent-roles in various locations

### 4. Enhanced `claude_pm/orchestration/backwards_compatible_orchestrator.py`
- **Purpose**: Added real subprocess execution capability
- **Key Features**:
  - New `_execute_real_subprocess` method
  - Environment variable `CLAUDE_PM_USE_REAL_SUBPROCESS` to enable real subprocesses
  - Maintains backwards compatibility
  - Proper error handling and fallback mechanisms

## How It Works

### Environment Setup
1. SubprocessRunner detects the framework path (usually `/path/to/project/framework`)
2. Sets `CLAUDE_PM_FRAMEWORK_PATH` environment variable
3. Configures PYTHONPATH to include the framework
4. Passes environment to subprocess

### Subprocess Execution Flow
1. Orchestrator receives agent delegation request
2. If `CLAUDE_PM_USE_REAL_SUBPROCESS=true`, uses SubprocessRunner
3. SubprocessRunner creates temporary JSON file with task data
4. Launches Python subprocess with agent_runner module
5. Agent runner loads profile and executes task
6. Results returned to orchestrator

### Framework Path Detection Strategy
1. Check `CLAUDE_PM_FRAMEWORK_PATH` environment variable
2. Search from current file location upward for `package.json`
3. Look for `framework/agent-roles` directory
4. Check common locations relative to working directory
5. Search recursively for agent-roles directory
6. Fallback to working directory

## Testing

Created `test_subprocess_system.py` that verifies:
- Environment setup is correct
- Agent profiles can be loaded
- Subprocesses execute successfully
- Both direct SubprocessRunner and orchestrator integration work

## Usage

### Enable Real Subprocesses
```bash
export CLAUDE_PM_USE_REAL_SUBPROCESS=true
```

### Run Tests
```bash
python test_subprocess_system.py
```

### Direct Subprocess Creation
```python
from claude_pm.services.subprocess_runner import SubprocessRunner

runner = SubprocessRunner()
return_code, stdout, stderr = await runner.run_agent_subprocess_async(
    agent_type='engineer',
    task_data={'task_description': 'Build feature X'},
    timeout=300
)
```

## Benefits

1. **True Process Isolation**: Subprocesses run in separate OS processes
2. **Environment Consistency**: Framework path and Python path properly configured
3. **Error Recovery**: Better error handling and debugging information
4. **Backwards Compatible**: Existing code continues to work unchanged
5. **Flexible Deployment**: Works with various project structures

## Next Steps

1. Consider making real subprocesses the default mode
2. Add subprocess pooling for performance
3. Implement subprocess health monitoring
4. Add metrics collection for subprocess performance
5. Consider adding subprocess caching for repeated tasks