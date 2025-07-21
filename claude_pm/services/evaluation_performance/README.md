# Evaluation Performance Module

This module provides performance optimization features for the evaluation system, including advanced caching, async processing, and performance monitoring.

## Module Structure

```
evaluation_performance/
├── __init__.py          # Main facade class (EvaluationPerformanceManager)
├── cache.py            # Advanced caching system with LRU/TTL strategies
├── circuit_breaker.py  # Circuit breaker pattern for reliability
├── batch_processor.py  # Async batch processing system
├── optimized_processor.py # Evaluation-specific batch processor
├── metrics.py          # Performance metrics tracking
└── utils.py            # Helper functions and global instance management
```

## Key Components

### EvaluationPerformanceManager (`__init__.py`)
- Main coordination class for all performance features
- Manages cache, circuit breaker, and batch processor
- Provides performance statistics and monitoring

### AdvancedEvaluationCache (`cache.py`)
- Supports LRU, TTL, and hybrid caching strategies
- Memory-aware with automatic eviction
- Background cleanup for expired entries
- Thread-safe operations

### CircuitBreaker (`circuit_breaker.py`)
- Protects against cascading failures
- Three states: CLOSED, OPEN, HALF_OPEN
- Configurable failure thresholds and timeouts

### AsyncBatchProcessor (`batch_processor.py`)
- Efficient batch processing of evaluation requests
- Configurable batch sizes and concurrency
- Queue management with statistics

### OptimizedEvaluationProcessor (`optimized_processor.py`)
- Extends AsyncBatchProcessor for evaluations
- Integrates caching and circuit breaker
- Handles batch evaluation with fallback

### PerformanceMetrics (`metrics.py`)
- Tracks cache hits, misses, and evictions
- Monitors error rates and response times
- Provides performance statistics

## Usage

```python
from claude_pm.services.evaluation_performance import (
    EvaluationPerformanceManager,
    initialize_performance_manager,
    get_evaluation_performance_stats
)

# Initialize with evaluator
manager = EvaluationPerformanceManager(config)
await manager.initialize(evaluator)

# Use optimized evaluation
result = await manager.evaluate_response(
    agent_type="test",
    response_text="sample response",
    context={"key": "value"}
)

# Get performance stats
stats = manager.get_performance_stats()
```

## Performance Targets

- Evaluation overhead: <100ms
- Cache hit rate: >95%
- Throughput: >50 evaluations/second
- Memory usage: <500MB for cache
- Error rate: <1%

## Configuration

The module respects the following configuration keys:

- `evaluation_performance_enabled`: Enable/disable performance features
- `evaluation_cache_max_size`: Maximum cache entries (default: 1000)
- `evaluation_cache_ttl_seconds`: Cache TTL in seconds (default: 3600)
- `evaluation_cache_strategy`: Cache strategy (lru/ttl/hybrid, default: hybrid)
- `evaluation_cache_memory_limit_mb`: Memory limit in MB (default: 100)
- `evaluation_circuit_breaker_threshold`: Failure threshold (default: 5)
- `evaluation_circuit_breaker_timeout`: Timeout in seconds (default: 60)
- `evaluation_batch_size`: Batch size for processing (default: 10)
- `evaluation_batch_wait_ms`: Max wait for batch completion (default: 100)
- `evaluation_max_concurrent_batches`: Max concurrent batches (default: 5)