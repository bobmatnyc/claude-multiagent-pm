# Performance Tuning Guide

## Overview

This guide covers performance optimization techniques for the Claude PM framework, including orchestration modes, caching strategies, and common performance issues.

## Orchestration Performance

### Mode Comparison

| Mode | Response Time | Use Case | Resource Usage |
|------|--------------|----------|----------------|
| LOCAL | ~200ms | Default, optimal performance | Low (in-process) |
| SUBPROCESS | 30-40s | Complete isolation needed | High (process spawning) |
| HYBRID | Variable | Complex workflows | Medium |

### Optimizing for LOCAL Mode

LOCAL mode provides 150x performance improvement over SUBPROCESS mode. To ensure you're using LOCAL mode:

1. **Check Current Mode:**
   ```bash
   echo $CLAUDE_PM_ORCHESTRATION_MODE
   ```

2. **Remove Subprocess Overrides:**
   ```bash
   unset CLAUDE_PM_FORCE_SUBPROCESS_MODE
   ```

3. **Verify Performance:**
   ```bash
   time claude-pm orchestrate documentation "Generate quick summary"
   ```

### Common Performance Issues

#### Issue: Slow Agent Responses (30+ seconds)

**Symptoms:**
- Agent queries take 30-40 seconds
- High CPU usage during queries
- "Starting subprocess" messages in logs

**Root Cause:** System falling back to SUBPROCESS mode

**Solution:**
```python
# Ensure LOCAL mode components are initialized
if not self._message_bus:
    self._message_bus = SimpleMessageBus()
    self._register_default_agent_handlers()
```

#### Issue: Memory Usage Growth

**Symptoms:**
- Growing memory usage over time
- Slow response after extended use

**Solution:** Enable prompt caching and cleanup:
```python
# Use shared prompt cache
cache = SharedPromptCache()
cache.cleanup_old_entries(max_age_hours=24)
```

## Caching Strategies

### 1. Shared Prompt Cache

The SharedPromptCache provides 99.7% performance improvement for repeated agent loads:

```python
from claude_pm.services.shared_prompt_cache import SharedPromptCache

# Initialize with cache
cache = SharedPromptCache()
registry = AgentRegistry(prompt_cache=cache)

# Preload frequently used agents
cache.preload_agent_prompts(['documentation', 'qa', 'engineer'])
```

### 2. Context Manager Caching

Reduce context filtering overhead:

```python
# Cache CLAUDE.md deduplication
context_manager._claude_md_cache[file_hash] = {
    'content': filtered_content,
    'timestamp': time.time()
}
```

### 3. Agent Registry Caching

Cache agent discovery results:

```python
# Cache agent listings
@lru_cache(maxsize=100)
def list_agents_cached(self, scope='all'):
    return self.listAgents(scope=scope)
```

## Performance Monitoring

### 1. Orchestration Metrics

```python
# Get performance metrics
metrics = orchestrator.get_orchestration_metrics()
print(f"Total orchestrations: {metrics['total_orchestrations']}")
print(f"Average response time: {metrics['average_response_time_ms']}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']}%")
```

### 2. Logging Performance Data

```python
import time
import logging

logger = logging.getLogger(__name__)

start = time.perf_counter()
response = await orchestrate_agent(agent_type, request)
duration = time.perf_counter() - start

logger.info(f"Agent {agent_type} responded in {duration:.3f}s")
```

### 3. Performance Benchmarks

Run the performance benchmark suite:

```bash
python scripts/performance_benchmark.py
```

Expected results:
- LOCAL mode: < 500ms per orchestration
- Registry lookup: < 10ms
- Context filtering: < 100ms per MB

## Optimization Techniques

### 1. Batch Operations

```python
# Batch multiple agent queries
async def batch_orchestrate(queries):
    tasks = [
        orchestrate_agent(q['agent'], q['request'])
        for q in queries
    ]
    return await asyncio.gather(*tasks)
```

### 2. Lazy Loading

```python
# Only load what's needed
def get_agent_lazy(self, agent_type):
    if agent_type not in self._loaded_agents:
        self._loaded_agents[agent_type] = self._load_agent(agent_type)
    return self._loaded_agents[agent_type]
```

### 3. Connection Pooling

```python
# Reuse HTTP connections for AI APIs
import httpx

async_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=10),
    timeout=30.0
)
```

### 4. Async Processing

```python
# Use async for I/O operations
async def process_files(file_paths):
    tasks = [read_file_async(path) for path in file_paths]
    return await asyncio.gather(*tasks)
```

## Configuration Tuning

### 1. Environment Variables

```bash
# Optimize for performance
export CLAUDE_PM_ORCHESTRATION_MODE=LOCAL
export CLAUDE_PM_CACHE_ENABLED=true
export CLAUDE_PM_MAX_WORKERS=4
export CLAUDE_PM_REQUEST_TIMEOUT=30
```

### 2. Memory Limits

```python
# Configure memory limits
import resource

# Set max memory to 2GB
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))
```

### 3. Logging Optimization

```python
# Reduce logging overhead in production
import logging

# Only log warnings and above
logging.getLogger('claude_pm').setLevel(logging.WARNING)

# Disable debug logging for performance
logging.getLogger('claude_pm.orchestration').setLevel(logging.INFO)
```

## Profiling and Analysis

### 1. CPU Profiling

```bash
# Profile CPU usage
python -m cProfile -o profile.stats scripts/orchestrate_test.py
python -m pstats profile.stats
```

### 2. Memory Profiling

```bash
# Profile memory usage
pip install memory-profiler
python -m memory_profiler scripts/orchestrate_test.py
```

### 3. Async Profiling

```python
import asyncio
import time

async def profile_async_operation():
    start = time.perf_counter()
    await your_async_operation()
    duration = time.perf_counter() - start
    print(f"Operation took {duration:.3f}s")
```

## Best Practices

1. **Always Use LOCAL Mode** unless isolation is required
2. **Enable Caching** for repeated operations
3. **Monitor Performance** with metrics and logging
4. **Profile Before Optimizing** to identify bottlenecks
5. **Batch Operations** when possible
6. **Use Async I/O** for file and network operations
7. **Implement Timeouts** to prevent hanging operations

## Troubleshooting Performance

### Quick Diagnostics

```bash
# Check orchestration mode and performance
python3 -c "
import asyncio
import time
from claude_pm.orchestration import create_backwards_compatible_orchestrator

async def diagnose():
    orch = create_backwards_compatible_orchestrator()
    print(f'Mode: {orch.mode}')
    
    start = time.perf_counter()
    await orch.orchestrate_agent('qa', {'task': 'test'})
    duration = time.perf_counter() - start
    
    print(f'Response time: {duration:.3f}s')
    if duration > 1.0:
        print('WARNING: Slow response detected!')
        print('Check orchestration mode and initialization')

asyncio.run(diagnose())
"
```

## Related Documentation
- [ISS-0128: Message Bus Performance Fix](../../tasks/issues/ISS-0128-message-bus-initialization-fix.md)
- [Orchestration Patterns](../technical/orchestration-patterns.md)
- [Defensive Programming Guide](../development/defensive-programming-guide.md)