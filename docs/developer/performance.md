# Performance Guide

## Overview

This guide covers performance optimization techniques, monitoring strategies, and best practices for the Claude PM Framework. The framework is designed for high performance with features like SharedPromptCache providing 99.7% improvement in agent loading times.

## Performance Architecture

### Key Performance Features

1. **SharedPromptCache**: LRU cache with automatic invalidation
2. **Lazy Loading**: On-demand component initialization
3. **Async Operations**: Non-blocking I/O throughout
4. **Agent Pooling**: Reusable agent instances
5. **Optimized Discovery**: Efficient directory scanning with caching

### Performance Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Cold Start | <500ms | ~450ms |
| Warm Start | <200ms | ~180ms |
| Agent Discovery | <100ms | ~80ms |
| Agent Loading | <50ms | ~15ms (cached) |
| Task Delegation | <100ms | ~90ms |
| Cache Hit Rate | >95% | 97.3% |

## Profiling and Monitoring

### 1. Python Profiling

#### CPU Profiling

```python
# profile_agent_loading.py
import cProfile
import pstats
from claude_pm.core.agent_registry import AgentRegistry

def profile_agent_loading():
    """Profile agent loading performance."""
    registry = AgentRegistry()
    
    # Profile the operation
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Operation to profile
    for _ in range(100):
        agents = registry.listAgents()
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

if __name__ == '__main__':
    profile_agent_loading()
```

#### Memory Profiling

```python
# profile_memory.py
from memory_profiler import profile
from claude_pm.services.shared_prompt_cache import SharedPromptCache

@profile
def test_cache_memory():
    """Profile cache memory usage."""
    cache = SharedPromptCache(max_size=1000)
    
    # Fill cache
    for i in range(1000):
        cache.set(f'key_{i}', f'value_{i}' * 100)
    
    # Access patterns
    for i in range(5000):
        cache.get(f'key_{i % 1000}')
    
    # Clear cache
    cache.clear()

# Run with: python -m memory_profiler profile_memory.py
```

### 2. Performance Monitoring

#### Built-in Performance Monitor

```python
from claude_pm.utils.performance import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Monitor operations
timer_id = monitor.start_timer('agent_workflow')

# ... perform operations ...

duration = monitor.end_timer(timer_id)
print(f"Workflow completed in {duration:.3f}s")

# Get aggregate metrics
metrics = monitor.get_metrics()
print(f"Average duration: {metrics['agent_workflow']['avg']:.3f}s")
print(f"95th percentile: {metrics['agent_workflow']['p95']:.3f}s")
```

#### Custom Performance Tracking

```python
import time
from functools import wraps
from typing import Callable, Dict, List

class PerformanceTracker:
    """Custom performance tracking."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def track(self, operation: str) -> Callable:
        """Decorator for tracking operation performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    self._record(operation, duration)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    self._record(operation, duration)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record(self, operation: str, duration: float):
        """Record metric."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
    
    def report(self) -> Dict[str, Dict[str, float]]:
        """Generate performance report."""
        report = {}
        for operation, durations in self.metrics.items():
            if durations:
                report[operation] = {
                    'count': len(durations),
                    'total': sum(durations),
                    'avg': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'p95': sorted(durations)[int(len(durations) * 0.95)]
                }
        return report

# Usage
tracker = PerformanceTracker()

@tracker.track('agent_loading')
async def load_agents():
    # ... implementation ...
    pass
```

## Optimization Techniques

### 1. Caching Strategies

#### SharedPromptCache Optimization

```python
# Optimize cache configuration
from claude_pm.services.shared_prompt_cache import SharedPromptCache

# Configure for your workload
cache = SharedPromptCache(
    max_size=2000,      # Increase for larger agent sets
    ttl=7200,          # 2 hours for stable environments
    eviction_policy='lru'  # Least Recently Used
)

# Preload frequently used agents
frequently_used = ['documentation', 'qa', 'engineer']
for agent_id in frequently_used:
    prompt = load_agent_prompt(agent_id)
    cache.set(f'agent:{agent_id}', prompt)

# Monitor cache performance
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Evictions: {stats['evictions']}")
```

#### Custom Caching Layer

```python
from functools import lru_cache
import hashlib

class CachedAgentLoader:
    """Optimized agent loader with caching."""
    
    @lru_cache(maxsize=128)
    def load_agent_metadata(self, agent_path: str) -> Dict:
        """Load and cache agent metadata."""
        # Expensive operation cached
        return self._parse_agent_file(agent_path)
    
    @lru_cache(maxsize=256)
    def get_agent_checksum(self, agent_path: str) -> str:
        """Get cached file checksum."""
        with open(agent_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def invalidate_if_changed(self, agent_path: str):
        """Invalidate cache if file changed."""
        current_checksum = self._calculate_checksum(agent_path)
        cached_checksum = self.get_agent_checksum(agent_path)
        
        if current_checksum != cached_checksum:
            self.load_agent_metadata.cache_clear()
            self.get_agent_checksum.cache_clear()
```

### 2. Async Optimization

#### Concurrent Operations

```python
import asyncio
from typing import List, Dict

async def optimized_multi_agent_execution(tasks: List[Dict]) -> List[Dict]:
    """Execute multiple agent tasks concurrently."""
    
    # Create task coroutines
    coroutines = []
    for task in tasks:
        coro = execute_agent_task(task['agent'], task['input'])
        coroutines.append(coro)
    
    # Execute concurrently with limited concurrency
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
    
    async def bounded_task(coro):
        async with semaphore:
            return await coro
    
    bounded_coroutines = [bounded_task(coro) for coro in coroutines]
    results = await asyncio.gather(*bounded_coroutines, return_exceptions=True)
    
    # Process results
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                'success': False,
                'error': str(result),
                'task': tasks[i]
            })
        else:
            processed_results.append({
                'success': True,
                'result': result,
                'task': tasks[i]
            })
    
    return processed_results
```

#### Async Context Managers

```python
class OptimizedAgentContext:
    """Optimized agent execution context."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.resources = []
    
    async def __aenter__(self):
        """Efficiently acquire resources."""
        # Parallel resource acquisition
        self.resources = await asyncio.gather(
            self._load_agent(),
            self._setup_environment(),
            self._acquire_locks()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        # Parallel cleanup
        await asyncio.gather(
            self._cleanup_environment(),
            self._release_locks(),
            return_exceptions=True
        )
```

### 3. Memory Optimization

#### Object Pooling

```python
from queue import Queue
from contextlib import contextmanager

class AgentPool:
    """Reusable agent instance pool."""
    
    def __init__(self, agent_type: str, pool_size: int = 5):
        self.agent_type = agent_type
        self.pool = Queue(maxsize=pool_size)
        
        # Pre-populate pool
        for _ in range(pool_size):
            agent = self._create_agent()
            self.pool.put(agent)
    
    @contextmanager
    def acquire(self):
        """Acquire agent from pool."""
        agent = self.pool.get()
        try:
            # Reset agent state
            agent.reset()
            yield agent
        finally:
            # Return to pool
            self.pool.put(agent)
    
    def _create_agent(self):
        """Create new agent instance."""
        return Agent(self.agent_type)

# Usage
pool = AgentPool('documentation', pool_size=3)

with pool.acquire() as agent:
    result = agent.execute(task)
```

#### Memory-Efficient Data Structures

```python
import sys
from dataclasses import dataclass
from typing import Optional

# Use slots for memory efficiency
@dataclass
class EfficientAgentMetadata:
    """Memory-efficient agent metadata."""
    __slots__ = ['id', 'type', 'specializations', 'path', 'checksum']
    
    id: str
    type: str
    specializations: tuple  # Immutable, more efficient than list
    path: str
    checksum: Optional[str] = None

# Compare memory usage
regular_dict = {'id': 'test', 'type': 'qa', 'specializations': ['testing']}
efficient_obj = EfficientAgentMetadata('test', 'qa', ('testing',), '/path')

print(f"Dict size: {sys.getsizeof(regular_dict)} bytes")
print(f"Efficient object size: {sys.getsizeof(efficient_obj)} bytes")
```

### 4. I/O Optimization

#### Batch File Operations

```python
import asyncio
import aiofiles
from pathlib import Path

async def batch_read_agents(agent_paths: List[Path]) -> Dict[str, str]:
    """Read multiple agent files efficiently."""
    
    async def read_file(path: Path) -> tuple[str, str]:
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
        return path.stem, content
    
    # Read all files concurrently
    tasks = [read_file(path) for path in agent_paths]
    results = await asyncio.gather(*tasks)
    
    return dict(results)

# Usage
agent_dir = Path('.claude-pm/agents')
agent_paths = list(agent_dir.glob('*.md'))
agents_content = await batch_read_agents(agent_paths)
```

#### Lazy File Loading

```python
class LazyAgentLoader:
    """Load agent content only when needed."""
    
    def __init__(self, agent_path: Path):
        self.path = agent_path
        self._content = None
        self._metadata = None
    
    @property
    def metadata(self) -> Dict:
        """Load metadata lazily."""
        if self._metadata is None:
            # Only read first few lines for metadata
            with open(self.path, 'r') as f:
                header = []
                for i, line in enumerate(f):
                    if i > 20:  # Metadata in first 20 lines
                        break
                    header.append(line)
            
            self._metadata = self._parse_metadata(header)
        return self._metadata
    
    @property
    def content(self) -> str:
        """Load full content lazily."""
        if self._content is None:
            self._content = self.path.read_text()
        return self._content
```

## Database and Storage Optimization

### 1. Connection Pooling

```python
import asyncpg
from contextlib import asynccontextmanager

class DatabasePool:
    """Optimized database connection pool."""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 20):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=10,
            max_queries=50000,
            max_cached_statement_lifetime=300
        )
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        async with self.pool.acquire() as conn:
            # Set performance options
            await conn.execute('SET jit = off')  # Disable JIT for short queries
            yield conn
    
    async def close(self):
        """Close connection pool."""
        await self.pool.close()
```

### 2. Batch Operations

```python
async def batch_insert_metrics(metrics: List[Dict]):
    """Efficiently insert multiple metrics."""
    
    async with db_pool.acquire() as conn:
        # Prepare statement once
        stmt = await conn.prepare('''
            INSERT INTO metrics (timestamp, operation, duration, success)
            VALUES ($1, $2, $3, $4)
        ''')
        
        # Batch insert
        await conn.executemany(
            stmt,
            [(m['timestamp'], m['operation'], m['duration'], m['success']) 
             for m in metrics]
        )
```

## Network Optimization

### 1. Connection Reuse

```python
import aiohttp
from typing import Optional

class OptimizedHTTPClient:
    """HTTP client with connection pooling."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create session with optimized settings."""
        timeout = aiohttp.ClientTimeout(total=30, connect=5)
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host limit
            ttl_dns_cache=300,  # DNS cache timeout
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'ClaudePM/0.9.3'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session."""
        await self.session.close()
    
    async def fetch_batch(self, urls: List[str]) -> List[Dict]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def fetch_one(self, url: str) -> Dict:
        """Fetch single URL with retry."""
        for attempt in range(3):
            try:
                async with self.session.get(url) as response:
                    return {
                        'url': url,
                        'status': response.status,
                        'data': await response.json()
                    }
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Framework-Specific Optimizations

### 1. Agent Registry Optimization

```python
# Optimized agent discovery
class OptimizedAgentRegistry(AgentRegistry):
    """Performance-optimized agent registry."""
    
    def __init__(self):
        super().__init__()
        self._discovery_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 60  # 1 minute
    
    def listAgents(self, **kwargs) -> Dict[str, AgentMetadata]:
        """List agents with caching."""
        # Create cache key from kwargs
        cache_key = str(sorted(kwargs.items()))
        
        # Check cache validity
        now = time.time()
        if (cache_key in self._discovery_cache and 
            now - self._cache_timestamp < self._cache_ttl):
            return self._discovery_cache[cache_key]
        
        # Perform discovery
        agents = super().listAgents(**kwargs)
        
        # Update cache
        self._discovery_cache[cache_key] = agents
        self._cache_timestamp = now
        
        return agents
```

### 2. Task Queue Optimization

```python
import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedTask:
    """Task with priority for optimal scheduling."""
    priority: int
    task: Any = field(compare=False)
    
class OptimizedTaskQueue:
    """Priority-based task queue."""
    
    def __init__(self):
        self._queue = []
        self._counter = 0
    
    def add_task(self, task: Dict, priority: int = 5):
        """Add task with priority (lower = higher priority)."""
        heapq.heappush(self._queue, PrioritizedTask(priority, task))
    
    def get_next_task(self) -> Optional[Dict]:
        """Get highest priority task."""
        if self._queue:
            return heapq.heappop(self._queue).task
        return None
    
    def add_urgent_task(self, task: Dict):
        """Add urgent task with highest priority."""
        self.add_task(task, priority=1)
```

## Performance Best Practices

### 1. Measure First
- Profile before optimizing
- Focus on bottlenecks
- Set performance budgets

### 2. Cache Wisely
- Cache expensive operations
- Set appropriate TTLs
- Monitor cache hit rates

### 3. Async Everything
- Use async/await throughout
- Avoid blocking operations
- Leverage concurrency

### 4. Resource Management
- Use connection pooling
- Implement circuit breakers
- Clean up resources properly

### 5. Monitoring
- Track key metrics
- Set up alerts
- Regular performance reviews

## Performance Checklist

- [ ] Profile code changes for performance impact
- [ ] Add caching for expensive operations
- [ ] Use async operations for I/O
- [ ] Implement connection pooling
- [ ] Add performance tests
- [ ] Monitor production metrics
- [ ] Document performance characteristics
- [ ] Set performance budgets

## Tools and Resources

### Profiling Tools
- **cProfile**: CPU profiling
- **memory_profiler**: Memory profiling
- **py-spy**: Sampling profiler
- **line_profiler**: Line-by-line profiling

### Monitoring Tools
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **DataDog**: APM and monitoring
- **New Relic**: Application monitoring

### Testing Tools
- **locust**: Load testing
- **pytest-benchmark**: Benchmark tests
- **apache bench**: HTTP load testing

---

*Remember: Premature optimization is the root of all evil. Profile first, optimize second.*