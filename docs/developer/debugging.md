# Debugging Guide

## Overview

This guide provides comprehensive debugging strategies, tools, and techniques for troubleshooting issues in the Claude PM Framework. Whether you're dealing with agent failures, performance problems, or integration issues, this guide will help you diagnose and resolve them efficiently.

## Debugging Tools and Setup

### 1. Environment Setup for Debugging

```bash
# Enable debug mode
export CLAUDE_PM_DEBUG=true
export CLAUDE_PM_LOG_LEVEL=debug
export CLAUDE_PM_LOG_FILE=claude_pm_debug.log

# Enable Python debugging
export PYTHONDEBUG=1
export PYTHONASYNCIODEBUG=1

# Enable Node.js debugging
export NODE_ENV=development
export DEBUG=claude-pm:*
```

### 2. Debug Configuration

```python
# .claude-pm/debug_config.json
{
    "debug": true,
    "log_level": "debug",
    "log_format": "detailed",
    "performance_tracking": true,
    "trace_operations": [
        "agent_loading",
        "task_delegation",
        "subprocess_execution",
        "cache_operations"
    ],
    "breakpoints": {
        "agent_errors": true,
        "permission_denied": true,
        "timeout_errors": true
    }
}
```

### 3. Logging Configuration

```python
# claude_pm/debug/logger_config.py
import logging
import sys
from datetime import datetime

def setup_debug_logging():
    """Configure comprehensive debug logging."""
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(funcName)s() - '
        '%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    )
    
    # Console handler with color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(detailed_formatter)
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        'claude_pm_debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers = {
        'claude_pm.agents': logging.DEBUG,
        'claude_pm.orchestration': logging.DEBUG,
        'claude_pm.services': logging.DEBUG,
        'claude_pm.utils': logging.INFO
    }
    
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
```

## Common Issues and Solutions

### 1. Agent Loading Failures

#### Symptoms
- "Agent not found" errors
- Agent discovery returns empty results
- Custom agents not being recognized

#### Debugging Steps

```python
# Debug agent loading
from claude_pm.core.agent_registry import AgentRegistry
import logging

logging.basicConfig(level=logging.DEBUG)

# Create registry with debug output
registry = AgentRegistry()

# Check directory scanning
print("Scanning directories:")
for directory in registry._get_search_directories():
    print(f"  - {directory}: exists={directory.exists()}")

# Manually scan for agents
agents = registry.listAgents(scope='all')
print(f"\nFound {len(agents)} agents:")
for agent_id, metadata in agents.items():
    print(f"  - {agent_id}: {metadata['path']}")

# Test specific agent loading
try:
    agent = registry.load_agent('performance')
    print(f"\nLoaded agent: {agent}")
except Exception as e:
    print(f"\nFailed to load agent: {e}")
    import traceback
    traceback.print_exc()
```

#### Common Fixes
- Check file permissions: `ls -la .claude-pm/agents/`
- Verify markdown syntax in agent files
- Ensure agent metadata is properly formatted
- Check for file encoding issues (use UTF-8)

### 2. Subprocess Execution Errors

#### Symptoms
- Task Tool subprocess failures
- Timeout errors
- Permission denied errors

#### Debugging Steps

```python
# Debug subprocess execution
import subprocess
import sys

def debug_subprocess(command: list, **kwargs):
    """Execute subprocess with detailed debugging."""
    
    print(f"Command: {' '.join(command)}")
    print(f"CWD: {kwargs.get('cwd', os.getcwd())}")
    print(f"ENV: {kwargs.get('env', {})}")
    
    try:
        # Run with full output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            **kwargs
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        return result
        
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

# Test subprocess
debug_subprocess(['python', '-c', 'print("Hello from subprocess")'])
```

#### Process Monitoring

```python
# Monitor subprocess resource usage
import psutil
import threading

def monitor_subprocess(process):
    """Monitor subprocess resources."""
    
    def monitor():
        while process.poll() is None:
            try:
                proc = psutil.Process(process.pid)
                print(f"CPU: {proc.cpu_percent()}%, "
                      f"Memory: {proc.memory_info().rss / 1024 / 1024:.1f}MB")
                time.sleep(1)
            except psutil.NoSuchProcess:
                break
    
    thread = threading.Thread(target=monitor)
    thread.daemon = True
    thread.start()

# Use with subprocess
process = subprocess.Popen(['python', 'long_running_script.py'])
monitor_subprocess(process)
process.wait()
```

### 3. Performance Issues

#### Symptoms
- Slow agent loading
- High memory usage
- Timeout errors

#### Performance Profiling

```python
# Profile performance bottlenecks
import cProfile
import pstats
from io import StringIO

def profile_operation(func, *args, **kwargs):
    """Profile function execution."""
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()
    
    # Generate report
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print(stream.getvalue())
    return result

# Profile agent loading
from claude_pm.core.agent_registry import AgentRegistry

registry = AgentRegistry()
profile_operation(registry.listAgents)
```

#### Memory Profiling

```python
# Track memory usage
import tracemalloc
import gc

def profile_memory(func, *args, **kwargs):
    """Profile memory usage."""
    
    gc.collect()
    tracemalloc.start()
    
    # Take snapshot before
    snapshot1 = tracemalloc.take_snapshot()
    
    # Execute function
    result = func(*args, **kwargs)
    
    # Take snapshot after
    snapshot2 = tracemalloc.take_snapshot()
    
    # Compare snapshots
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    print("[ Top 10 memory allocations ]")
    for stat in top_stats[:10]:
        print(stat)
    
    return result
```

### 4. Cache Issues

#### Symptoms
- Stale data being returned
- Cache not improving performance
- Memory growth from cache

#### Cache Debugging

```python
# Debug SharedPromptCache
from claude_pm.services.shared_prompt_cache import SharedPromptCache

# Create cache with debug stats
cache = SharedPromptCache(max_size=100)

# Enable cache statistics
cache.enable_stats()

# Perform operations
for i in range(200):
    cache.set(f'key_{i}', f'value_{i}')
    if i % 2 == 0:
        cache.get(f'key_{i}')

# Get detailed stats
stats = cache.get_detailed_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Evictions: {stats['evictions']}")
print(f"Memory usage: {stats['memory_bytes'] / 1024 / 1024:.1f}MB")
print(f"Oldest entry: {stats['oldest_entry_age']:.1f}s")

# Inspect cache internals
print("\nCache contents:")
for key, (value, timestamp) in cache._cache.items():
    age = time.time() - timestamp
    print(f"  {key}: age={age:.1f}s, size={len(str(value))} bytes")
```

### 5. API Integration Issues

#### Symptoms
- API calls failing
- Rate limiting errors
- Authentication failures

#### API Debugging

```python
# Debug API calls
import aiohttp
import json

async def debug_api_call(url: str, headers: dict, data: dict):
    """Debug API request/response."""
    
    print(f"=== API Debug ===")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"\nResponse Status: {response.status}")
                print(f"Response Headers: {dict(response.headers)}")
                
                body = await response.text()
                print(f"Response Body: {body[:500]}...")
                
                if response.status != 200:
                    print(f"\nERROR: {response.status} - {body}")
                
                return response
                
        except Exception as e:
            print(f"\nException: {type(e).__name__}: {e}")
            raise

# Test API call
await debug_api_call(
    'https://api.openai.com/v1/chat/completions',
    {'Authorization': f'Bearer {api_key}'},
    {'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'test'}]}
)
```

## Advanced Debugging Techniques

### 1. Interactive Debugging

```python
# Use Python debugger
import pdb

def problematic_function(data):
    """Function with issues to debug."""
    
    # Set breakpoint
    pdb.set_trace()
    
    # Or use breakpoint() in Python 3.7+
    breakpoint()
    
    # Code continues here
    result = process_data(data)
    return result

# IPython debugging for better experience
try:
    from IPython.core.debugger import set_trace
except ImportError:
    from pdb import set_trace

# Use in code
set_trace()  # Drops into IPython debugger if available
```

### 2. Async Debugging

```python
# Debug async operations
import asyncio
import functools

def async_debug(func):
    """Decorator for debugging async functions."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        print(f"[ASYNC] Entering {func_name}")
        print(f"[ASYNC] Args: {args}")
        print(f"[ASYNC] Kwargs: {kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            print(f"[ASYNC] {func_name} completed successfully")
            return result
        except Exception as e:
            print(f"[ASYNC] {func_name} failed: {e}")
            raise
    
    return wrapper

# Use decorator
@async_debug
async def fetch_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 3. Trace Execution

```python
# Trace code execution
import sys

def trace_calls(frame, event, arg):
    """Trace function calls."""
    if event != 'call':
        return
    
    code = frame.f_code
    filename = code.co_filename
    
    # Only trace our code
    if 'claude_pm' in filename:
        func_name = code.co_name
        print(f"Calling {filename}:{func_name}")
    
    return trace_calls

# Enable tracing
sys.settrace(trace_calls)

# Your code here
registry = AgentRegistry()
agents = registry.listAgents()

# Disable tracing
sys.settrace(None)
```

### 4. Debug Context Manager

```python
# Context manager for debugging
from contextlib import contextmanager
import time
import tracemalloc

@contextmanager
def debug_context(operation_name: str):
    """Comprehensive debugging context."""
    
    print(f"\n{'='*60}")
    print(f"Starting: {operation_name}")
    print(f"{'='*60}")
    
    # Start tracking
    start_time = time.time()
    tracemalloc.start()
    start_snapshot = tracemalloc.take_snapshot()
    
    try:
        yield
    except Exception as e:
        print(f"\nERROR in {operation_name}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # End tracking
        end_time = time.time()
        end_snapshot = tracemalloc.take_snapshot()
        
        # Report stats
        duration = end_time - start_time
        print(f"\nCompleted: {operation_name}")
        print(f"Duration: {duration:.3f}s")
        
        # Memory stats
        stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        if stats:
            print("\nTop memory allocations:")
            for stat in stats[:5]:
                print(f"  {stat}")
        
        tracemalloc.stop()
        print(f"{'='*60}\n")

# Usage
with debug_context("Agent Loading"):
    registry = AgentRegistry()
    agents = registry.listAgents()
```

## Framework-Specific Debugging

### 1. Agent Registry Debugging

```python
# Debug agent registry issues
from claude_pm.core.agent_registry import AgentRegistry

class DebugAgentRegistry(AgentRegistry):
    """Agent registry with enhanced debugging."""
    
    def _scan_directory(self, directory: Path) -> Dict[str, AgentMetadata]:
        """Scan directory with detailed logging."""
        
        print(f"\nScanning directory: {directory}")
        
        if not directory.exists():
            print(f"  ❌ Directory does not exist")
            return {}
        
        agents = {}
        for file_path in directory.glob('*.md'):
            print(f"  📄 Found file: {file_path.name}")
            
            try:
                metadata = self._parse_agent_file(file_path)
                agents[metadata['id']] = metadata
                print(f"    ✅ Parsed successfully: {metadata['type']}")
            except Exception as e:
                print(f"    ❌ Parse failed: {e}")
        
        print(f"  Total agents found: {len(agents)}")
        return agents

# Use debug registry
debug_registry = DebugAgentRegistry()
agents = debug_registry.listAgents()
```

### 2. Task Tool Debugging

```python
# Debug task tool execution
from claude_pm.orchestration import TaskTool

class DebugTaskTool(TaskTool):
    """Task tool with debugging capabilities."""
    
    @staticmethod
    async def create_subprocess(agent_type: str, task: str, context: dict):
        """Create subprocess with debugging."""
        
        print(f"\n{'='*60}")
        print(f"Task Tool Debug")
        print(f"{'='*60}")
        print(f"Agent Type: {agent_type}")
        print(f"Task: {task[:100]}...")
        print(f"Context Keys: {list(context.keys())}")
        
        # Time the execution
        start = time.time()
        
        try:
            result = await super().create_subprocess(agent_type, task, context)
            duration = time.time() - start
            
            print(f"\nExecution completed in {duration:.2f}s")
            print(f"Success: {result.success}")
            
            if not result.success:
                print(f"Error: {result.error}")
            
            return result
            
        except Exception as e:
            print(f"\nException during execution: {e}")
            raise
```

### 3. Cache Performance Debugging

```python
# Debug cache performance
from claude_pm.services.shared_prompt_cache import SharedPromptCache

def analyze_cache_performance():
    """Analyze cache performance characteristics."""
    
    cache = SharedPromptCache(max_size=1000)
    
    # Test different access patterns
    patterns = {
        'sequential': lambda i: f'key_{i}',
        'repeated': lambda i: f'key_{i % 100}',
        'random': lambda i: f'key_{random.randint(0, 1000)}'
    }
    
    for pattern_name, key_func in patterns.items():
        print(f"\n{pattern_name.upper()} Access Pattern:")
        
        # Reset cache
        cache.clear()
        hits = misses = 0
        
        # Run pattern
        start = time.time()
        for i in range(10000):
            key = key_func(i)
            
            if cache.get(key):
                hits += 1
            else:
                misses += 1
                cache.set(key, f'value_{i}')
        
        duration = time.time() - start
        hit_rate = hits / (hits + misses) * 100
        
        print(f"  Duration: {duration:.3f}s")
        print(f"  Hit Rate: {hit_rate:.1f}%")
        print(f"  Hits: {hits}, Misses: {misses}")
        print(f"  Ops/sec: {10000 / duration:.0f}")
```

## Debugging Tools Integration

### 1. VS Code Debugging

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Claude PM",
            "type": "python",
            "request": "launch",
            "module": "claude_pm.cli",
            "args": ["--debug"],
            "env": {
                "CLAUDE_PM_DEBUG": "true",
                "PYTHONPATH": "${workspaceFolder}"
            },
            "justMyCode": false
        },
        {
            "name": "Debug Specific Agent",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/debug_agent.py",
            "args": ["--agent", "documentation"],
            "console": "integratedTerminal"
        }
    ]
}
```

### 2. PyCharm Debugging

```python
# debug_config.py for PyCharm
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable all debug flags
os.environ['CLAUDE_PM_DEBUG'] = 'true'
os.environ['PYTHONDEBUG'] = '1'

# Import and run
from claude_pm.cli import cli_main
cli_main(['--debug'])
```

## Debugging Checklist

### Initial Investigation
- [ ] Enable debug mode and verbose logging
- [ ] Check error messages and stack traces
- [ ] Verify environment variables and configuration
- [ ] Test with minimal reproduction case
- [ ] Check system resources (CPU, memory, disk)

### Agent Issues
- [ ] Verify agent file exists and is readable
- [ ] Check agent metadata format
- [ ] Test agent discovery manually
- [ ] Verify agent permissions and sandboxing
- [ ] Check for naming conflicts

### Performance Issues
- [ ] Profile CPU usage with cProfile
- [ ] Check memory usage with tracemalloc
- [ ] Monitor cache hit rates
- [ ] Analyze I/O operations
- [ ] Check for blocking operations

### Integration Issues
- [ ] Verify API keys and credentials
- [ ] Check network connectivity
- [ ] Monitor rate limits
- [ ] Test with minimal API calls
- [ ] Check response formats

### Framework Issues
- [ ] Verify installation completeness
- [ ] Check version compatibility
- [ ] Test core components individually
- [ ] Review recent changes
- [ ] Check for circular dependencies

## Getting Help

If you're still stuck after following this guide:

1. **Search existing issues**: Check GitHub issues for similar problems
2. **Create minimal reproduction**: Isolate the issue to smallest possible code
3. **Gather debug information**: Logs, stack traces, environment details
4. **Open an issue**: Provide all relevant information

Include in your issue:
- Framework version
- Operating system
- Python/Node.js versions
- Complete error messages
- Steps to reproduce
- Debug logs

---

*Remember: Good debugging is methodical. Start with the simplest explanation and work your way up.*