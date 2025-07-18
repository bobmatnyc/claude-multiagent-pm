# Subprocess Creation and Delegation in Claude PM Framework

## Overview

The Claude PM Framework uses a sophisticated orchestration system that delegates work from a central Project Manager (PM) orchestrator to specialized agent subprocesses. This document details the subprocess creation mechanism, delegation patterns, and critical environment configuration requirements.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PM Orchestrator (Parent)                      │
│  - Manages overall project coordination                              │
│  - Delegates specific tasks to specialized agents                    │
│  - Maintains CLAUDE_PM_FRAMEWORK_PATH environment                   │
└───────────────┬─────────────────────────────────────┬───────────────┘
                │                                     │
                │ Task Tool Delegation                │ Task Tool Delegation
                │                                     │
┌───────────────▼─────────────────┐   ┌──────────────▼──────────────────┐
│    Engineer Agent (Subprocess)   │   │  Documentation Agent (Subprocess) │
│  - Isolated execution context    │   │  - Isolated execution context     │
│  - REQUIRES env var inheritance  │   │  - REQUIRES env var inheritance   │
│  - Loads specific agent profile  │   │  - Loads specific agent profile   │
└──────────────────────────────────┘   └───────────────────────────────────┘
```

## Orchestration Modes

The framework supports two distinct orchestration modes:

### 1. Local Orchestration Mode
- **Detection**: No Task Tool in user prompt
- **Behavior**: PM executes actions directly without subprocess delegation
- **Use Case**: Simple operations, direct user commands
- **Performance**: Faster, no subprocess overhead
- **Agent Loading**: Direct import from framework paths

### 2. Subprocess Delegation Mode
- **Detection**: Task Tool present in user prompt
- **Behavior**: PM creates isolated subprocesses for each agent
- **Use Case**: Complex multi-agent workflows, isolation required
- **Performance**: Overhead from subprocess creation
- **Agent Loading**: REQUIRES proper environment configuration

## Critical Environment Variable: CLAUDE_PM_FRAMEWORK_PATH

### The Problem

When the PM orchestrator creates a subprocess via Task Tool, the subprocess runs in an isolated environment that doesn't automatically inherit the parent's Python path configuration. This causes agent profile loading failures.

### Root Cause

1. **Parent Process**: Has framework directory in `sys.path`
2. **Subprocess Creation**: New Python interpreter with clean environment
3. **Missing Path**: Framework modules not accessible
4. **Import Failure**: Agent profiles cannot be loaded

### The Solution

The framework MUST set and propagate `CLAUDE_PM_FRAMEWORK_PATH` environment variable:

```python
# In parent orchestrator
import os
import sys

# Ensure framework path is set
framework_path = find_framework_root()
os.environ['CLAUDE_PM_FRAMEWORK_PATH'] = framework_path

# When creating subprocess
subprocess_env = os.environ.copy()  # Inherits CLAUDE_PM_FRAMEWORK_PATH
```

## Subprocess Creation Flow

### 1. Task Identification
```python
# PM Orchestrator identifies task requiring delegation
task_type = analyze_user_request()
agent_type = map_task_to_agent(task_type)
```

### 2. Environment Preparation
```python
# CRITICAL: Set framework path BEFORE subprocess creation
def prepare_subprocess_environment():
    env = os.environ.copy()
    
    # Ensure framework path is set
    if 'CLAUDE_PM_FRAMEWORK_PATH' not in env:
        framework_path = find_framework_root()
        env['CLAUDE_PM_FRAMEWORK_PATH'] = framework_path
    
    return env
```

### 3. Agent Profile Resolution
```python
# In subprocess, agent profile loading
def load_agent_profile():
    # CRITICAL: Add framework path to sys.path
    framework_path = os.environ.get('CLAUDE_PM_FRAMEWORK_PATH')
    if framework_path and framework_path not in sys.path:
        sys.path.insert(0, framework_path)
    
    # Now can import agent profiles
    from claude_pm.agents import load_agent_config
    return load_agent_config(agent_type)
```

### 4. Subprocess Execution
```python
# Task Tool creates subprocess with proper environment
def create_agent_subprocess(agent_type, task_description):
    env = prepare_subprocess_environment()
    
    # Create subprocess with inherited environment
    result = subprocess.run(
        ['python', '-m', 'claude_pm.agent_runner', agent_type],
        env=env,  # CRITICAL: Pass prepared environment
        input=task_description,
        capture_output=True
    )
    
    return result
```

## Framework Path Detection

The framework uses multiple strategies to locate its root directory:

### Detection Priority Order

1. **Environment Variable**: `CLAUDE_PM_FRAMEWORK_PATH`
2. **Import Location**: Location of `claude_pm` package
3. **Script Location**: Directory containing current script
4. **Working Directory**: Current working directory traversal

### Implementation

```python
def find_framework_root():
    # 1. Check environment variable
    if 'CLAUDE_PM_FRAMEWORK_PATH' in os.environ:
        return os.environ['CLAUDE_PM_FRAMEWORK_PATH']
    
    # 2. Check import location
    try:
        import claude_pm
        return os.path.dirname(os.path.dirname(claude_pm.__file__))
    except ImportError:
        pass
    
    # 3. Check script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if 'claude_pm' in script_dir:
        # Navigate up to framework root
        while not os.path.exists(os.path.join(script_dir, 'claude_pm')):
            script_dir = os.path.dirname(script_dir)
        return script_dir
    
    # 4. Working directory traversal
    current = os.getcwd()
    while current != '/':
        if os.path.exists(os.path.join(current, 'claude_pm')):
            return current
        current = os.path.dirname(current)
    
    raise RuntimeError("Cannot locate Claude PM Framework")
```

## Delegation Patterns

### Standard Delegation Template

```python
"""
**[Agent Type] Agent**: [Clear task description]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to task.

**Task**: [Detailed task breakdown]
1. [Specific action 1]
2. [Specific action 2]
3. [Specific action 3]

**Context**: [Relevant project context]
**Authority**: [Agent permissions and scope]
**Expected Results**: [Specific deliverables]
"""
```

### Multi-Agent Coordination

```python
# PM orchestrates multiple agents
def coordinate_release_workflow():
    # 1. Documentation Agent
    changelog = delegate_to_agent(
        agent_type='documentation',
        task='Generate changelog from commits'
    )
    
    # 2. QA Agent
    test_results = delegate_to_agent(
        agent_type='qa',
        task='Run comprehensive test suite'
    )
    
    # 3. Version Control Agent
    if test_results.success:
        version_bump = delegate_to_agent(
            agent_type='version_control',
            task='Apply semantic version bump'
        )
```

## Common Issues and Troubleshooting

### Issue 1: Agent Profile Import Failures

**Symptoms:**
- `ModuleNotFoundError: No module named 'claude_pm.agents'`
- Agent subprocess fails to load configuration

**Root Cause:**
- Missing `CLAUDE_PM_FRAMEWORK_PATH` environment variable
- Framework directory not in subprocess Python path

**Solution:**
```python
# Ensure environment variable is set BEFORE subprocess creation
os.environ['CLAUDE_PM_FRAMEWORK_PATH'] = framework_path
```

### Issue 2: Subprocess Cannot Find Framework Modules

**Symptoms:**
- Import errors in subprocess but not in parent
- Agent-specific modules not accessible

**Root Cause:**
- Python path not properly configured in subprocess
- Environment variables not inherited

**Solution:**
```python
# In subprocess initialization
framework_path = os.environ.get('CLAUDE_PM_FRAMEWORK_PATH')
if framework_path:
    sys.path.insert(0, framework_path)
```

### Issue 3: Inconsistent Behavior Between Modes

**Symptoms:**
- Direct PM execution works, delegation fails
- Different results in local vs subprocess mode

**Root Cause:**
- Environment differences between modes
- Missing context in subprocess

**Solution:**
- Ensure complete environment inheritance
- Pass all required context to subprocess
- Test both modes during development

### Issue 4: Framework Path Detection Failures

**Symptoms:**
- "Cannot locate Claude PM Framework" errors
- Inconsistent path resolution

**Root Cause:**
- Framework installed in non-standard location
- Missing environment configuration

**Solution:**
```bash
# Set environment variable explicitly
export CLAUDE_PM_FRAMEWORK_PATH=/path/to/claude-multiagent-pm

# Or in Python
os.environ['CLAUDE_PM_FRAMEWORK_PATH'] = '/path/to/framework'
```

## Best Practices

### 1. Always Set Environment Variables
```python
# At framework initialization
def initialize_framework():
    framework_path = find_framework_root()
    os.environ['CLAUDE_PM_FRAMEWORK_PATH'] = framework_path
    return framework_path
```

### 2. Validate Environment Before Delegation
```python
def validate_delegation_environment():
    required_vars = ['CLAUDE_PM_FRAMEWORK_PATH']
    missing = [var for var in required_vars if var not in os.environ]
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {missing}")
```

### 3. Use Explicit Path Configuration
```python
# In agent subprocess
def configure_agent_environment():
    # Add framework to path
    framework_path = os.environ.get('CLAUDE_PM_FRAMEWORK_PATH')
    if framework_path:
        sys.path.insert(0, framework_path)
    
    # Verify imports work
    try:
        import claude_pm.agents
    except ImportError as e:
        raise RuntimeError(f"Framework not properly configured: {e}")
```

### 4. Test Both Orchestration Modes
```python
# Test harness for both modes
def test_orchestration_modes():
    # Test local mode
    result_local = execute_local_mode(task)
    
    # Test subprocess mode
    result_subprocess = execute_subprocess_mode(task)
    
    # Verify consistency
    assert result_local == result_subprocess
```

## Security Considerations

### 1. Environment Variable Sanitization
- Filter sensitive variables before subprocess creation
- Only pass required framework configuration

### 2. Subprocess Isolation
- Each agent runs in isolated context
- Limited access to parent process resources
- Controlled communication channel

### 3. Path Validation
- Validate framework paths before use
- Prevent path traversal attacks
- Ensure paths point to legitimate framework

## Performance Optimization

### 1. Environment Caching
```python
# Cache prepared environment
_cached_subprocess_env = None

def get_subprocess_environment():
    global _cached_subprocess_env
    if _cached_subprocess_env is None:
        _cached_subprocess_env = prepare_subprocess_environment()
    return _cached_subprocess_env.copy()
```

### 2. Agent Pool Management
- Reuse agent subprocesses when possible
- Implement subprocess pooling for frequent operations
- Monitor subprocess lifecycle

### 3. Selective Delegation
- Use local mode for simple operations
- Reserve subprocess delegation for complex tasks
- Balance isolation needs with performance

## Conclusion

Proper subprocess creation and delegation is critical for the Claude PM Framework's multi-agent orchestration. The key requirement is ensuring `CLAUDE_PM_FRAMEWORK_PATH` is set and properly inherited by all subprocesses. Following the patterns and practices in this document will ensure reliable agent coordination and task execution.

## References

- [Claude PM Framework Architecture](./ARCHITECTURE.md)
- [Agent System Documentation](../agents/AGENT_SYSTEM.md)
- [Task Tool Documentation](./TASK_TOOL.md)
- [Environment Configuration Guide](../setup/ENVIRONMENT.md)