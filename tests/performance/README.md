# Performance Tests

This directory contains performance benchmarks and optimization tests for the Claude Multi-Agent PM framework.

## Test Categories

### Benchmarks
- Agent loading performance
- Prompt cache efficiency
- Memory collector performance
- File I/O operations
- Subprocess creation overhead

### Optimization Tests
- SharedPromptCache 99.7% improvement validation
- Async operation performance
- Batch processing efficiency
- Resource usage monitoring

## Running Performance Tests

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run with benchmark plugin
pytest tests/performance/ --benchmark-only

# Generate performance report
pytest tests/performance/ --benchmark-json=reports/performance.json
```

## Guidelines

1. Performance tests should be deterministic
2. Use consistent test data sizes
3. Run multiple iterations for accuracy
4. Compare against baseline metrics
5. Document any performance regressions

## Metrics Tracked

- Execution time
- Memory usage
- CPU utilization
- I/O operations
- Cache hit rates

## Performance Goals

- Agent loading: < 100ms
- Prompt cache hit: < 5ms  
- Memory collection: < 50ms per operation
- Subprocess creation: < 500ms