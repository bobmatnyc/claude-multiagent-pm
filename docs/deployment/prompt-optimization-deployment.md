# Prompt Optimization Deployment Guide

## Overview

This guide covers deploying and configuring the prompt optimization features in production environments. Follow these steps to safely roll out token optimization while monitoring performance and cost impacts.

## Pre-Deployment Checklist

### 1. Environment Validation

```bash
# Verify framework version supports optimization
claude-pm --version  # Should be 1.3.0 or higher

# Check Python environment
python -c "from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer; print('✅ Analyzer available')"

# Verify agent loader integration
python -c "from claude_pm.agents.agent_loader import get_agent_prompt_with_model_info; print('✅ Integration ready')"
```

### 2. Baseline Metrics Collection

Before enabling optimization, collect baseline metrics:

```python
# baseline_metrics.py
import json
from datetime import datetime
from your_metrics_system import get_token_usage, get_api_costs

baseline = {
    "date": datetime.now().isoformat(),
    "daily_tokens": get_token_usage(days=7),  # 7-day average
    "daily_cost": get_api_costs(days=7),
    "agent_distribution": get_agent_usage_stats(),
    "task_types": get_task_type_distribution()
}

with open("baseline_metrics.json", "w") as f:
    json.dump(baseline, f, indent=2)

print(f"Baseline captured: {baseline['daily_tokens']} tokens/day")
```

### 3. Configuration Validation

Test configuration in a staging environment:

```bash
# Test environment variables
export ENABLE_DYNAMIC_MODEL_SELECTION=true
export CLAUDE_PM_TEST_MODE=true  # Safe testing mode

# Verify settings
python -c "
import os
print(f'Model Selection: {os.getenv(\"ENABLE_DYNAMIC_MODEL_SELECTION\")}')
print(f'Test Mode: {os.getenv(\"CLAUDE_PM_TEST_MODE\")}')
"
```

## Deployment Strategies

### Option 1: Gradual Agent Rollout (Recommended)

Deploy optimization one agent at a time:

```bash
# Week 1: Low-risk agents
export CLAUDE_PM_DOCUMENTATION_MODEL_SELECTION=true
export CLAUDE_PM_RESEARCH_MODEL_SELECTION=true

# Week 2: Add QA and Ops
export CLAUDE_PM_QA_MODEL_SELECTION=true
export CLAUDE_PM_OPS_MODEL_SELECTION=true

# Week 3: Add Engineer (after validation)
export CLAUDE_PM_ENGINEER_MODEL_SELECTION=true

# Week 4: Enable globally
export ENABLE_DYNAMIC_MODEL_SELECTION=true
```

### Option 2: Percentage-Based Rollout

Use feature flags for percentage-based deployment:

```python
# feature_flag_rollout.py
import hashlib
import os

def should_enable_optimization(user_id, percentage):
    """Enable for percentage of users based on stable hash"""
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return (hash_value % 100) < percentage

# Start with 10% rollout
if should_enable_optimization(user_id, 10):
    os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
```

### Option 3: Time-Based Rollout

Enable during off-peak hours first:

```python
# time_based_rollout.py
from datetime import datetime
import os

def enable_during_off_peak():
    """Enable optimization during off-peak hours (2 AM - 6 AM)"""
    current_hour = datetime.now().hour
    if 2 <= current_hour <= 6:
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
    else:
        os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
```

## Production Configuration

### Environment Variables

```bash
# /etc/environment or .env file

# Core optimization settings
ENABLE_DYNAMIC_MODEL_SELECTION=true
ENABLE_DYNAMIC_PROMPT_TEMPLATES=true  # Default: true

# Optional: Custom thresholds
CLAUDE_PM_COMPLEXITY_SIMPLE_THRESHOLD=30
CLAUDE_PM_COMPLEXITY_MEDIUM_THRESHOLD=70

# Optional: Force specific models
# CLAUDE_PM_ENGINEER_MODEL=claude-4-opus
# CLAUDE_PM_QA_MODEL=claude-sonnet-4-20250514

# Monitoring
CLAUDE_PM_METRICS_ENABLED=true
CLAUDE_PM_METRICS_RETENTION_HOURS=168  # 7 days
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set optimization environment variables
ENV ENABLE_DYNAMIC_MODEL_SELECTION=true
ENV ENABLE_DYNAMIC_PROMPT_TEMPLATES=true

# Optional: Custom configuration
ENV CLAUDE_PM_COMPLEXITY_SIMPLE_THRESHOLD=30
ENV CLAUDE_PM_COMPLEXITY_MEDIUM_THRESHOLD=70

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install claude-pm

CMD ["python", "app.py"]
```

### Kubernetes Configuration

```yaml
# claude-pm-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: claude-pm-optimization
data:
  ENABLE_DYNAMIC_MODEL_SELECTION: "true"
  ENABLE_DYNAMIC_PROMPT_TEMPLATES: "true"
  CLAUDE_PM_COMPLEXITY_SIMPLE_THRESHOLD: "30"
  CLAUDE_PM_COMPLEXITY_MEDIUM_THRESHOLD: "70"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-pm-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-app:latest
        envFrom:
        - configMapRef:
            name: claude-pm-optimization
```

## Monitoring Setup

### 1. Metrics Collection

```python
# monitoring/optimization_metrics.py
import time
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
optimization_counter = Counter(
    'claude_pm_optimizations_total',
    'Total number of optimized prompts',
    ['agent', 'model', 'complexity']
)

token_reduction_histogram = Histogram(
    'claude_pm_token_reduction_percent',
    'Token reduction percentage',
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90]
)

active_optimizations = Gauge(
    'claude_pm_active_optimizations',
    'Currently active optimization settings'
)

# Hook into agent loader
def monitor_optimization(agent_name, model, complexity, reduction):
    optimization_counter.labels(
        agent=agent_name,
        model=model,
        complexity=complexity
    ).inc()
    
    token_reduction_histogram.observe(reduction)
```

### 2. Dashboard Configuration

```yaml
# grafana-dashboard.json
{
  "dashboard": {
    "title": "Claude PM Optimization Metrics",
    "panels": [
      {
        "title": "Token Reduction by Agent",
        "targets": [{
          "expr": "avg by (agent) (claude_pm_token_reduction_percent)"
        }]
      },
      {
        "title": "Model Selection Distribution",
        "targets": [{
          "expr": "sum by (model) (rate(claude_pm_optimizations_total[5m]))"
        }]
      },
      {
        "title": "Complexity Distribution",
        "targets": [{
          "expr": "sum by (complexity) (claude_pm_optimizations_total)"
        }]
      }
    ]
  }
}
```

### 3. Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: claude_pm_optimization
    rules:
      - alert: LowTokenReduction
        expr: avg(claude_pm_token_reduction_percent) < 30
        for: 1h
        annotations:
          summary: "Token reduction below expected threshold"
          
      - alert: HighComplexityRatio
        expr: |
          sum(rate(claude_pm_optimizations_total{complexity="COMPLEX"}[5m])) /
          sum(rate(claude_pm_optimizations_total[5m])) > 0.5
        for: 30m
        annotations:
          summary: "High ratio of complex tasks"
```

## Rollback Procedures

### Quick Rollback

```bash
# Disable optimization immediately
export ENABLE_DYNAMIC_MODEL_SELECTION=false

# Or for specific agents
export CLAUDE_PM_ENGINEER_MODEL_SELECTION=false
export CLAUDE_PM_QA_MODEL_SELECTION=false
```

### Gradual Rollback

```python
# rollback_optimization.py
import os
import time

def gradual_rollback(agents, delay_minutes=60):
    """Gradually disable optimization for agents"""
    for agent in agents:
        env_var = f"CLAUDE_PM_{agent.upper()}_MODEL_SELECTION"
        os.environ[env_var] = "false"
        print(f"Disabled optimization for {agent}")
        time.sleep(delay_minutes * 60)
    
    # Finally disable globally
    os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = "false"
    print("Global optimization disabled")

# Rollback order (reverse of deployment)
gradual_rollback(['engineer', 'ops', 'qa', 'research', 'documentation'])
```

## Performance Validation

### Load Testing

```python
# load_test_optimization.py
import asyncio
import time
from claude_pm.utils.task_tool_helper import TaskToolHelper

async def load_test(num_requests=100):
    """Test optimization under load"""
    helper = TaskToolHelper()
    
    tasks = [
        ("List files", "simple"),
        ("Implement feature", "medium"),
        ("Refactor system", "complex")
    ] * (num_requests // 3)
    
    start_time = time.time()
    results = []
    
    for task, complexity in tasks:
        result = await helper.create_agent_subprocess(
            agent_type="engineer",
            task_description=task
        )
        results.append({
            'task': task,
            'model': result.get('selected_model'),
            'time': time.time() - start_time
        })
    
    # Analyze results
    avg_time = sum(r['time'] for r in results) / len(results)
    model_distribution = {}
    for r in results:
        model = r['model']
        model_distribution[model] = model_distribution.get(model, 0) + 1
    
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Model distribution: {model_distribution}")

# Run load test
asyncio.run(load_test())
```

### Cost Analysis

```python
# cost_analysis.py
from claude_pm.agents.agent_loader import get_model_selection_metrics
import json

def analyze_cost_impact():
    """Analyze cost impact of optimization"""
    metrics = get_model_selection_metrics()
    
    # Model costs (example rates)
    model_costs = {
        'claude-3-haiku-20240307': 0.25,  # per million tokens
        'claude-sonnet-4-20250514': 3.00,
        'claude-4-opus': 15.00
    }
    
    # Calculate weighted average cost
    total_requests = metrics['selection_stats']['total_selections']
    by_model = metrics['selection_stats']['by_model']
    
    weighted_cost = 0
    for model, count in by_model.items():
        weight = count / total_requests
        cost = model_costs.get(model, 0)
        weighted_cost += weight * cost
    
    # Compare with baseline (all Sonnet)
    baseline_cost = model_costs['claude-sonnet-4-20250514']
    savings_percent = ((baseline_cost - weighted_cost) / baseline_cost) * 100
    
    report = {
        'total_requests': total_requests,
        'model_distribution': by_model,
        'weighted_cost_per_million': weighted_cost,
        'baseline_cost_per_million': baseline_cost,
        'savings_percent': savings_percent,
        'complexity_distribution': metrics['selection_stats']['complexity_distribution']
    }
    
    print(json.dumps(report, indent=2))
    return report

# Run analysis
analyze_cost_impact()
```

## Post-Deployment Checklist

### Week 1
- [ ] Monitor token usage reduction
- [ ] Check model selection distribution
- [ ] Verify no quality degradation
- [ ] Review any error logs
- [ ] Collect user feedback

### Week 2
- [ ] Analyze cost savings
- [ ] Adjust complexity thresholds if needed
- [ ] Expand to additional agents
- [ ] Update monitoring dashboards

### Month 1
- [ ] Complete cost-benefit analysis
- [ ] Document optimization patterns
- [ ] Plan full rollout if not complete
- [ ] Share learnings with team

## Troubleshooting Common Issues

### Issue: Lower than expected token reduction

```bash
# Check task complexity distribution
python -c "
from claude_pm.agents.agent_loader import get_model_selection_metrics
metrics = get_model_selection_metrics()
print(metrics['selection_stats']['complexity_distribution'])
"

# If mostly complex tasks, this is expected
# Consider adjusting thresholds if needed
```

### Issue: Unexpected model selections

```bash
# Enable debug logging
export CLAUDE_PM_LOG_LEVEL=DEBUG

# Run a test task and check logs
claude-pm "Your test task here"

# Review complexity analysis in logs
```

### Issue: Performance degradation

```python
# Check cache hit rates
from claude_pm.services.shared_prompt_cache import SharedPromptCache
cache = SharedPromptCache.get_instance()
stats = cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']}%")

# If low, investigate cache configuration
```

## Security Considerations

1. **API Keys**: Ensure different API keys for different models if using multiple accounts
2. **Rate Limits**: Monitor rate limits for each model type
3. **Data Privacy**: Ensure optimization doesn't log sensitive task descriptions
4. **Audit Logging**: Track all model selection decisions for compliance

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: 2025-07-20  
**For Framework Version**: 1.3.0+