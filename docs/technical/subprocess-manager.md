# Unified Subprocess Manager Documentation

## Overview

The Claude PM Framework's Unified Subprocess Manager provides a centralized, consistent system for executing external processes across the entire codebase. This consolidation addresses ISS-0176 by replacing 57 scattered subprocess calls with a single, well-tested implementation.

## Key Benefits

### 1. **Consistent Error Handling**
- All subprocess errors are handled uniformly
- Standardized timeout behavior across all operations
- Clear error messages with context

### 2. **Unified Logging**
- All subprocess operations are logged consistently
- Performance metrics tracked automatically
- Debug information available when needed

### 3. **Resource Management**
- Automatic process tracking and cleanup
- Memory usage monitoring
- Prevent zombie processes

### 4. **Enhanced Features**
- Output streaming support
- Async execution capabilities
- Process lifecycle management
- Automatic environment setup

## Usage Examples

### Basic Usage

```python
from claude_pm.utils.subprocess_manager import SubprocessManager

# Create manager instance
manager = SubprocessManager()

# Simple command execution
result = manager.run(['git', 'status'])
if result.success:
    print(result.stdout)
else:
    print(f"Error: {result.stderr}")
```

### Advanced Usage

```python
# With custom timeout
result = manager.run(['npm', 'install'], timeout=120)

# With streaming output
result = manager.run(['pytest', 'tests/'], stream_output=True)

# With custom working directory
result = manager.run(['git', 'pull'], cwd='/path/to/repo')

# Async execution
async def run_async_command():
    result = await manager.run_async(['python', 'script.py'])
    return result
```

### Configuration Options

```python
from claude_pm.utils.subprocess_manager import SubprocessManager, SubprocessConfig

# Custom configuration
config = SubprocessConfig(
    timeout=300,            # 5 minutes
    capture_output=True,    # Capture stdout/stderr
    stream_output=False,    # Don't stream to console
    text=True,              # Text mode (not binary)
    shell=False,            # Don't use shell
    memory_limit_mb=2000    # 2GB memory limit
)

manager = SubprocessManager(default_config=config)
```

## Migration Guide

### From subprocess.run()

**Before:**
```python
import subprocess
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
if result.returncode == 0:
    print(result.stdout)
```

**After:**
```python
from claude_pm.utils.subprocess_manager import SubprocessManager
manager = SubprocessManager()
result = manager.run(['git', 'status'])
if result.success:
    print(result.stdout)
```

### From subprocess.Popen()

**Before:**
```python
import subprocess
proc = subprocess.Popen(['npm', 'install'], stdout=subprocess.PIPE)
for line in proc.stdout:
    print(line.decode().rstrip())
proc.wait()
```

**After:**
```python
from claude_pm.utils.subprocess_manager import SubprocessManager
manager = SubprocessManager()
result = manager.run(['npm', 'install'], stream_output=True)
```

### Using Compatibility Layer

For minimal code changes, use the compatibility layer:

```python
# Replace this import
# import subprocess

# With this
from claude_pm.utils import subprocess_migration as subprocess

# All subprocess calls work as before
result = subprocess.run(['git', 'status'], capture_output=True)
```

## API Reference

### SubprocessManager Class

#### Methods

**`run(command, **kwargs)`**
- Execute a subprocess synchronously
- Returns: `SubprocessResult`
- Parameters:
  - `command`: List[str] or str - Command to execute
  - `timeout`: Optional[float] - Timeout in seconds
  - `cwd`: Optional[Path] - Working directory
  - `capture_output`: bool - Capture stdout/stderr
  - `stream_output`: bool - Stream output to console
  - `text`: bool - Text mode (vs binary)
  - `shell`: bool - Use shell execution
  - `env`: Optional[Dict] - Environment variables

**`run_async(command, **kwargs)`**
- Execute a subprocess asynchronously
- Returns: `SubprocessResult` (via await)
- Parameters: Same as `run()`

**`get_stats()`**
- Get execution statistics
- Returns: Dict with metrics

**`terminate_all()`**
- Terminate all active processes
- Use for cleanup on shutdown

### SubprocessResult Class

#### Properties

- `command`: List[str] - Command that was executed
- `returncode`: int - Process return code
- `stdout`: str - Captured stdout
- `stderr`: str - Captured stderr
- `duration`: float - Execution time in seconds
- `timed_out`: bool - Whether timeout occurred
- `success`: bool - True if returncode == 0 and not timed_out

## Performance Considerations

### Subprocess Pooling
The manager tracks active processes to prevent resource exhaustion:
- Maximum concurrent processes enforced
- Automatic cleanup of completed processes
- Resource usage monitoring

### Memory Management
- Per-process memory limits enforced
- Peak memory usage tracked
- Automatic termination of memory-hungry processes

### Timeout Handling
- Default timeout: 5 minutes
- Graceful termination attempted first
- Force kill after grace period

## Error Handling

### Common Errors

1. **Timeout Errors**
   ```python
   result = manager.run(['long-running-command'], timeout=10)
   if result.timed_out:
       print("Command timed out")
   ```

2. **Command Not Found**
   ```python
   result = manager.run(['nonexistent-command'])
   if not result.success:
       print(f"Error: {result.stderr}")
   ```

3. **Permission Errors**
   ```python
   try:
       result = manager.run(['sudo', 'command'])
   except OSError as e:
       print(f"Permission error: {e}")
   ```

## Best Practices

1. **Always check result.success**
   ```python
   result = manager.run(['command'])
   if not result.success:
       # Handle error
       logger.error(f"Command failed: {result.stderr}")
   ```

2. **Use appropriate timeouts**
   ```python
   # Short timeout for quick commands
   result = manager.run(['echo', 'test'], timeout=5)
   
   # Longer timeout for builds
   result = manager.run(['npm', 'run', 'build'], timeout=600)
   ```

3. **Stream output for long-running commands**
   ```python
   # User can see progress
   result = manager.run(['pytest', '-v'], stream_output=True)
   ```

4. **Use async for parallel execution**
   ```python
   async def run_parallel_commands():
       tasks = [
           manager.run_async(['command1']),
           manager.run_async(['command2']),
           manager.run_async(['command3'])
       ]
       results = await asyncio.gather(*tasks)
       return results
   ```

## Integration with Framework

The SubprocessManager is integrated throughout the Claude PM Framework:

1. **Version Control Helper**: All git operations
2. **CLI Flags**: Package management commands
3. **Dependency Manager**: Pip operations
4. **Build Scripts**: Compilation and packaging
5. **Test Runners**: Test execution

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger('claude_pm.utils.subprocess_manager').setLevel(logging.DEBUG)
```

### View Statistics

```python
manager = SubprocessManager()
# ... run various commands ...
stats = manager.get_stats()
print(f"Total executed: {stats['total_executed']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average duration: {stats['average_duration']:.2f}s")
```

## Future Enhancements

1. **Process Pools**: Reusable process pools for repeated commands
2. **Caching**: Cache results for deterministic commands
3. **Remote Execution**: Support for SSH and remote command execution
4. **Advanced Monitoring**: Integration with system monitoring tools
5. **Rate Limiting**: Prevent subprocess flooding

## Migration Status

As of implementation:
- ✅ Core SubprocessManager implemented
- ✅ Compatibility layer created
- ✅ Version Control Helper migrated (11 calls)
- ✅ CLI Flags migrated (5 calls)
- ✅ Dependency Manager migrated (8 calls)
- 🔄 33 more files pending migration
- 📊 Total: 24/57 calls migrated (42%)

## Support

For issues or questions about the Subprocess Manager:
1. Check this documentation
2. Review the source code in `claude_pm/utils/subprocess_manager.py`
3. File an issue with the `subprocess-manager` label