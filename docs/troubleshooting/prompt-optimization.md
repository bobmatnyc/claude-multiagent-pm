# Prompt Optimization Troubleshooting Guide

## Common Issues and Solutions

### Issue: Optimization Not Working

**Symptoms:**
- Token usage hasn't decreased after enabling optimization
- All tasks still using the same model
- No complexity analysis in logs

**Solutions:**

1. **Verify Feature Flag is Set**
   ```bash
   echo $ENABLE_DYNAMIC_MODEL_SELECTION
   # Should output: true
   
   # If not set, enable it:
   export ENABLE_DYNAMIC_MODEL_SELECTION=true
   ```

2. **Check Task Description is Provided**
   ```python
   # ❌ Won't trigger optimization
   get_agent_prompt('engineer')
   
   # ✅ Will trigger optimization
   get_agent_prompt('engineer', task_description='Implement user authentication')
   ```

3. **Enable Debug Logging**
   ```python
   import logging
   logging.getLogger('claude_pm.agents.agent_loader').setLevel(logging.DEBUG)
   logging.getLogger('claude_pm.services.task_complexity_analyzer').setLevel(logging.DEBUG)
   ```

### Issue: Wrong Model Being Selected

**Symptoms:**
- Simple tasks using Opus
- Complex tasks using Haiku
- Unexpected model selections

**Solutions:**

1. **Add More Context to Task Description**
   ```python
   # Instead of vague descriptions:
   "Fix the bug"  # Too vague for accurate analysis
   
   # Use specific descriptions:
   "Fix authentication bug where JWT tokens expire immediately after login"
   ```

2. **Provide Additional Parameters**
   ```python
   result = get_agent_prompt_with_model_info(
       'engineer',
       task_description='Refactor authentication',
       file_count=10,  # Helps determine complexity
       requires_testing=True,  # Adds to score
       technical_depth='deep'  # Indicates complexity
   )
   ```

3. **Review Complexity Analysis**
   ```python
   from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer
   
   analyzer = TaskComplexityAnalyzer()
   result = analyzer.analyze_task(task_description="Your task")
   
   print(f"Score: {result.complexity_score}")
   print(f"Breakdown: {result.scoring_breakdown}")
   ```

### Issue: Lower Than Expected Token Reduction

**Symptoms:**
- Only seeing 20-30% reduction instead of 50-66%
- Complex tasks dominating workload
- High average complexity scores

**Solutions:**

1. **Check Task Distribution**
   ```python
   metrics = get_model_selection_metrics()
   distribution = metrics['selection_stats']['complexity_distribution']
   
   print(f"Simple tasks: {distribution['0-30']}%")
   print(f"Medium tasks: {distribution['31-70']}%")
   print(f"Complex tasks: {distribution['71-100']}%")
   ```

2. **Batch Simple Tasks**
   ```python
   # Instead of multiple simple tasks:
   for file in files:
       check_file(file)  # Each incurs overhead
   
   # Batch them:
   check_files(files)  # One optimized operation
   ```

3. **Adjust Complexity Thresholds**
   ```bash
   # If your tasks are scoring too high:
   export CLAUDE_PM_COMPLEXITY_SIMPLE_THRESHOLD=35  # Default: 30
   export CLAUDE_PM_COMPLEXITY_MEDIUM_THRESHOLD=75  # Default: 70
   ```

### Issue: Performance Degradation

**Symptoms:**
- Slower response times after enabling optimization
- High analysis overhead
- Cache misses

**Solutions:**

1. **Check Cache Performance**
   ```python
   from claude_pm.services.shared_prompt_cache import SharedPromptCache
   
   cache = SharedPromptCache.get_instance()
   stats = cache.get_stats()
   
   print(f"Hit rate: {stats['hit_rate']}%")
   # Should be >95% for good performance
   ```

2. **Verify Analysis Time**
   ```python
   import time
   
   start = time.time()
   result = analyzer.analyze_task("Test task")
   duration = time.time() - start
   
   print(f"Analysis time: {duration*1000:.2f}ms")
   # Should be <1ms
   ```

3. **Clear and Rebuild Cache**
   ```python
   cache.clear()
   # Cache will rebuild automatically
   ```

### Issue: Environment Variable Not Working

**Symptoms:**
- Setting environment variables has no effect
- Per-agent overrides not working
- Feature flags ignored

**Solutions:**

1. **Check Variable Names**
   ```bash
   # Correct names:
   ENABLE_DYNAMIC_MODEL_SELECTION=true
   CLAUDE_PM_ENGINEER_MODEL_SELECTION=true
   
   # Common mistakes:
   ENABLE_MODEL_SELECTION=true  # Missing "DYNAMIC"
   CLAUDE_ENGINEER_MODEL_SELECTION=true  # Missing "PM"
   ```

2. **Verify in Python Environment**
   ```python
   import os
   print(os.environ.get('ENABLE_DYNAMIC_MODEL_SELECTION'))
   print(os.environ.get('CLAUDE_PM_ENGINEER_MODEL_SELECTION'))
   ```

3. **Check Load Order**
   ```bash
   # Ensure variables are set before starting Python:
   export ENABLE_DYNAMIC_MODEL_SELECTION=true
   python your_script.py
   
   # Not inside Python after import
   ```

### Issue: Metrics Not Collecting

**Symptoms:**
- `get_model_selection_metrics()` returns empty data
- No statistics available
- Metrics not updating

**Solutions:**

1. **Ensure Tasks Are Being Processed**
   ```python
   # Metrics only collect when tasks are analyzed
   # Run some tasks first:
   for i in range(10):
       get_agent_prompt('engineer', task_description=f'Task {i}')
   
   # Then check metrics:
   metrics = get_model_selection_metrics()
   ```

2. **Check Cache TTL**
   ```python
   # Metrics are stored with 24-hour TTL
   # For testing, you might want shorter TTL:
   cache.set('model_selection:metrics', metrics, ttl=300)  # 5 minutes
   ```

3. **Enable Metrics Logging**
   ```python
   # Add logging to track metric updates
   logging.getLogger('claude_pm.agents.agent_loader').setLevel(logging.INFO)
   ```

### Issue: Test Mode Override

**Symptoms:**
- Optimization disabled in test mode
- Always using FULL templates
- Model selection ignored during tests

**Solutions:**

1. **Check Test Mode Setting**
   ```bash
   echo $CLAUDE_PM_TEST_MODE
   # If "true", optimization may be limited
   ```

2. **Override for Specific Tests**
   ```python
   # Temporarily disable test mode for optimization testing
   import os
   original = os.environ.get('CLAUDE_PM_TEST_MODE')
   os.environ['CLAUDE_PM_TEST_MODE'] = 'false'
   
   # Run optimization tests
   
   # Restore original
   if original:
       os.environ['CLAUDE_PM_TEST_MODE'] = original
   ```

## Diagnostic Commands

### Full System Check

```python
# diagnostic.py
import os
from claude_pm.agents.agent_loader import get_model_selection_metrics
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer
from claude_pm.services.shared_prompt_cache import SharedPromptCache

print("=== Prompt Optimization Diagnostics ===")
print(f"Feature Flag: {os.environ.get('ENABLE_DYNAMIC_MODEL_SELECTION', 'false')}")
print(f"Test Mode: {os.environ.get('CLAUDE_PM_TEST_MODE', 'false')}")

# Test analyzer
analyzer = TaskComplexityAnalyzer()
test_result = analyzer.analyze_task("Implement user authentication")
print(f"\nTest Analysis:")
print(f"  Score: {test_result.complexity_score}")
print(f"  Level: {test_result.complexity_level.value}")
print(f"  Model: {test_result.recommended_model.value}")

# Check cache
cache = SharedPromptCache.get_instance()
print(f"\nCache Stats:")
print(f"  Entries: {len(cache._cache)}")

# Check metrics
metrics = get_model_selection_metrics()
if metrics['selection_stats']['total_selections'] > 0:
    print(f"\nMetrics:")
    print(f"  Total: {metrics['selection_stats']['total_selections']}")
    print(f"  By Model: {metrics['selection_stats']['by_model']}")
else:
    print("\nNo metrics collected yet")
```

### Performance Test

```python
# performance_test.py
import time
from claude_pm.agents.agent_loader import get_agent_prompt_with_model_info

tasks = [
    ("List files", "simple"),
    ("Fix authentication bug", "medium"),
    ("Refactor entire system", "complex")
]

print("=== Performance Test ===")
for task, expected in tasks:
    start = time.time()
    _, model, config = get_agent_prompt_with_model_info(
        'engineer',
        task_description=task
    )
    duration = (time.time() - start) * 1000
    
    print(f"\nTask: {task}")
    print(f"  Time: {duration:.2f}ms")
    print(f"  Model: {model}")
    print(f"  Complexity: {config['complexity_level']}")
    print(f"  Expected: {expected}")
```

## Getting Help

If issues persist after trying these solutions:

1. **Check Documentation**
   - [Feature Documentation](../features/prompt-optimization.md)
   - [User Guide](../guides/prompt-optimization-guide.md)
   - [API Reference](../api/task-complexity-analyzer.md)

2. **Enable Full Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **File an Issue**
   Include:
   - Diagnostic output
   - Environment variables
   - Sample task that's not working
   - Expected vs actual behavior

---

**Troubleshooting Guide Version**: 1.0.0  
**Last Updated**: 2025-07-20