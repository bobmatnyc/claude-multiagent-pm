# Specific Code Optimization Examples for Claude PM

Based on the comprehensive semantic analysis of the claude_pm codebase, here are specific code examples demonstrating optimization opportunities:

## 📊 Analysis Summary
- **Total Files**: 293
- **Total Lines**: 90,349
- **Async Files**: 154 (52.6%)
- **Type Hint Coverage**: 71.4% functions, 49.6% parameters
- **Total Classes**: 548 (168 dataclasses)
- **Subprocess Usage**: 57 calls across 19 files

## 1. Async Optimization Opportunities

### Current State: 2,445 async constructs (1,107 async functions)
The codebase is heavily async with potential for optimization:

```python
# Example: Unnecessary async function (no await inside)
async def get_config_value(self, key: str) -> str:
    """This doesn't need to be async."""
    return self.config.get(key, "")

# Optimized: Regular function
def get_config_value(self, key: str) -> str:
    """Synchronous config access."""
    return self.config.get(key, "")
```

### Async Context Manager Optimization
With only 26 async context managers vs 1,312 await expressions:

```python
# Current: Manual resource management
async def process_file(self, path: Path):
    file_handle = await open_async(path)
    try:
        content = await file_handle.read()
        result = await self.process(content)
    finally:
        await file_handle.close()
    return result

# Optimized: Using async context manager
async def process_file(self, path: Path):
    async with aiofiles.open(path) as f:
        content = await f.read()
        return await self.process(content)
```

## 2. Type Hint Improvements

### Current Coverage: 71.4% functions, 49.6% parameters
Need to improve parameter type hints:

```python
# Current: Missing parameter types
def merge_configs(base, override, deep=True):
    """Merge configurations."""
    if deep:
        return deep_merge(base, override)
    return {**base, **override}

# Optimized: Full type hints
from typing import Dict, Any, TypeVar, overload

ConfigDict = Dict[str, Any]

@overload
def merge_configs(base: ConfigDict, override: ConfigDict, deep: bool = True) -> ConfigDict: ...

def merge_configs(base: ConfigDict, override: ConfigDict, deep: bool = True) -> ConfigDict:
    """Merge configurations with type safety.
    
    Args:
        base: Base configuration dictionary
        override: Override values to merge
        deep: Whether to perform deep merge
        
    Returns:
        Merged configuration dictionary
    """
    if deep:
        return deep_merge(base, override)
    return {**base, **override}
```

## 3. Dataclass Usage Expansion

### Current: 168 dataclasses out of 548 classes (30.7%)
Expand dataclass usage for better code organization:

```python
# Current: Regular class with boilerplate
class AgentConfig:
    def __init__(self, name: str, type: str, version: str = "1.0.0"):
        self.name = name
        self.type = type
        self.version = version
        self.patterns = []
        self.metadata = {}
    
    def __repr__(self):
        return f"AgentConfig(name={self.name}, type={self.type})"

# Optimized: Using dataclass
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class AgentConfig:
    """Agent configuration with automatic methods."""
    name: str
    type: str
    version: str = "1.0.0"
    patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate configuration."""
        return bool(self.name and self.type)
```

## 4. Subprocess Management Consolidation

### Current: 57 subprocess calls across 19 files
Centralize subprocess handling:

```python
# Current: Scattered subprocess calls
# In file A:
result = subprocess.run(["git", "status"], capture_output=True)

# In file B:
proc = await asyncio.create_subprocess_exec("npm", "install")

# Optimized: Centralized subprocess manager
from typing import List, Optional, Union, Tuple
import asyncio
import subprocess

class SubprocessManager:
    """Centralized subprocess handling with logging and error management."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._running_processes: List[asyncio.subprocess.Process] = []
    
    async def run_async(
        self, 
        cmd: List[str], 
        cwd: Optional[Path] = None,
        timeout: Optional[float] = None
    ) -> Tuple[str, str, int]:
        """Run subprocess asynchronously with proper cleanup."""
        self.logger.info(f"Running async: {' '.join(cmd)}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            self._running_processes.append(proc)
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=timeout
            )
            
            return (
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else "",
                proc.returncode or 0
            )
        finally:
            if proc in self._running_processes:
                self._running_processes.remove(proc)
    
    def run_sync(
        self, 
        cmd: List[str], 
        cwd: Optional[Path] = None,
        timeout: Optional[float] = None
    ) -> subprocess.CompletedProcess:
        """Run subprocess synchronously."""
        self.logger.info(f"Running sync: {' '.join(cmd)}")
        return subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            timeout=timeout
        )
```

## 5. Import Optimization

### Current: 50+ unique imports with heavy usage
Optimize imports based on usage patterns:

```python
# Top imports by usage:
# typing: 249 occurrences
# logging: 174 occurrences
# pathlib: 148 occurrences
# datetime: 137 occurrences
# asyncio: 94 occurrences

# Optimized: Common imports module
# claude_pm/common_imports.py
"""Common imports used across the codebase."""
from typing import (
    Dict, List, Optional, Union, Any, 
    Tuple, Set, Type, TypeVar, Protocol,
    AsyncIterator, Awaitable, Callable
)
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import asyncio

# Re-export commonly used items
__all__ = [
    'Dict', 'List', 'Optional', 'Union', 'Any',
    'Path', 'datetime', 'dataclass', 'field',
    'logging', 'asyncio'
]
```

## 6. Caching Strategy

### Add caching to frequently called functions:

```python
# Current: No caching
def load_agent_config(self, agent_id: str) -> Dict:
    """Load agent configuration from disk."""
    path = self.config_dir / f"{agent_id}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)

# Optimized: With LRU cache
from functools import lru_cache
import hashlib

class AgentConfigLoader:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self._cache_keys: Dict[str, str] = {}
    
    @lru_cache(maxsize=128)
    def _load_cached(self, agent_id: str, file_hash: str) -> Dict:
        """Load with cache based on file content hash."""
        path = self.config_dir / f"{agent_id}.yaml"
        with open(path) as f:
            return yaml.safe_load(f)
    
    def load_agent_config(self, agent_id: str) -> Dict:
        """Load agent configuration with intelligent caching."""
        path = self.config_dir / f"{agent_id}.yaml"
        
        # Check file hash for cache invalidation
        with open(path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        return self._load_cached(agent_id, file_hash)
```

## 7. Error Handling Patterns

### Standardize error handling across async operations:

```python
# Current: Inconsistent error handling
async def process_agent_task(self, task):
    try:
        result = await self.agent.process(task)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

# Optimized: Structured error handling
from typing import TypeVar, Union, Optional, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """Result wrapper for better error handling."""
    value: Optional[T] = None
    error: Optional[Exception] = None
    
    @property
    def is_success(self) -> bool:
        return self.error is None
    
    @property
    def is_failure(self) -> bool:
        return self.error is not None

class AgentProcessor:
    async def process_agent_task(self, task: Dict) -> Result[Dict]:
        """Process task with structured error handling."""
        try:
            result = await self.agent.process(task)
            return Result(value=result)
        except asyncio.TimeoutError:
            self.logger.error(f"Task timeout: {task.get('id')}")
            return Result(error=TimeoutError("Agent processing timeout"))
        except Exception as e:
            self.logger.exception(f"Task failed: {task.get('id')}")
            return Result(error=e)
```

## 8. Performance Monitoring

### Add performance monitoring to async operations:

```python
# Optimized: Performance tracking decorator
import time
from functools import wraps
from typing import Callable, Any

def track_performance(metric_name: str):
    """Decorator to track async function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start
                logger.info(f"{metric_name} completed in {duration:.3f}s")
                # Could also send to metrics system
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(f"{metric_name} failed after {duration:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                logger.info(f"{metric_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(f"{metric_name} failed after {duration:.3f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Usage:
@track_performance("agent_orchestration")
async def orchestrate_agents(self, task: Dict) -> Dict:
    """Orchestrate multiple agents with performance tracking."""
    results = await asyncio.gather(
        self.documentation_agent.process(task),
        self.qa_agent.validate(task),
        self.security_agent.scan(task)
    )
    return self.merge_results(results)
```

## 9. Modern Python Features

### Use Python 3.11+ features for better performance:

```python
# Use match/case for complex conditionals
def process_agent_response(response: Dict) -> Dict:
    """Process response based on type."""
    match response.get('type'):
        case 'documentation':
            return self.process_documentation(response)
        case 'qa' | 'test':
            return self.process_qa(response)
        case 'security' if response.get('severity') == 'high':
            return self.process_critical_security(response)
        case _:
            return self.process_default(response)

# Use ExceptionGroup for better error handling
async def run_agents_parallel(self, tasks: List[Dict]) -> List[Dict]:
    """Run multiple agents with proper error grouping."""
    errors = []
    results = []
    
    async with asyncio.TaskGroup() as tg:
        for task in tasks:
            try:
                result = await tg.create_task(self.process_task(task))
                results.append(result)
            except Exception as e:
                errors.append(e)
    
    if errors:
        raise ExceptionGroup("Agent processing errors", errors)
    
    return results
```

## Summary of Recommended Optimizations

1. **Async Cleanup**: Review 1,107 async functions for unnecessary async declarations
2. **Type Coverage**: Increase parameter type hints from 49.6% to 90%+
3. **Dataclass Adoption**: Expand from 30.7% to 60%+ of suitable classes
4. **Subprocess Consolidation**: Create central SubprocessManager for 57 calls
5. **Import Organization**: Create common imports module to reduce redundancy
6. **Caching Strategy**: Add LRU caching to file/config loading operations
7. **Error Handling**: Implement Result type pattern for better error management
8. **Performance Tracking**: Add monitoring to critical async operations
9. **Modern Python**: Adopt Python 3.11+ features for cleaner code

These optimizations would significantly improve code maintainability, type safety, and performance monitoring capabilities while maintaining the framework's async-first architecture.
EOF < /dev/null