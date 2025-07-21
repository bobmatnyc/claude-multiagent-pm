# Prompt Optimization System

## Overview

The Claude PM Framework features a comprehensive prompt optimization system that reduces token usage by up to 66% while maintaining or improving task execution quality. This system analyzes task complexity and intelligently adapts prompts, model selection, and context to maximize efficiency.

## 🚀 Key Benefits

- **66% Token Reduction**: Average 62.3% reduction across all task types, up to 78.4% for complex tasks
- **3-Phase Optimization**: Task complexity analysis → Dynamic model selection → Adaptive prompt templates
- **<1ms Overhead**: Lightning-fast analysis with minimal performance impact
- **Cost Savings**: Reduced token usage translates directly to lower API costs
- **Improved Performance**: Smaller prompts process faster, improving response times

## 🧠 How It Works

### Phase 1: Task Complexity Analysis

The `TaskComplexityAnalyzer` evaluates multiple factors to determine task complexity:

#### Complexity Factors
- **Task Description** (0-25 points)
  - Verb complexity (simple/medium/complex verbs)
  - Description length
  - Technical keywords
  - Multi-step indicators
- **File Operations** (0-20 points)
  - Number of files involved
- **Context Size** (0-15 points)
  - Amount of context information required
- **Integration Points** (0-15 points)
  - System integration complexity
- **Additional Requirements** (0-15 points)
  - Research, testing, documentation needs
- **Technical Depth** (0-10 points)
  - Shallow, moderate, or deep technical requirements

#### Complexity Levels
- **SIMPLE (0-30)**: Basic operations, reads, listings
- **MEDIUM (31-70)**: Standard implementations, modifications
- **COMPLEX (71-100)**: Architecture, refactoring, comprehensive changes

### Phase 2: Dynamic Model Selection

Based on complexity analysis, the optimal Claude model is automatically selected:

| Complexity | Model | Use Case | Token Range |
|------------|-------|----------|-------------|
| SIMPLE | Haiku | Quick tasks, basic operations | 300-500 |
| MEDIUM | Sonnet | Standard development tasks | 700-1000 |
| COMPLEX | Opus | Architecture, complex analysis | 1200-1500 |

### Phase 3: Adaptive Prompt Templates

Base agent instructions are dynamically adjusted based on complexity:

| Template | Complexity | Size | Sections Included |
|----------|------------|------|-------------------|
| MINIMAL | 0-30 | ~580 chars | Core principles, basic communication |
| STANDARD | 31-70 | ~980 chars | Core + operational guidelines |
| FULL | 71-100 | ~1,971 chars | Complete instructions + escalation |

## 🔧 Configuration

### Global Feature Flags

```bash
# Enable prompt optimization globally
export ENABLE_DYNAMIC_MODEL_SELECTION=true

# Enable dynamic prompt templates (enabled by default)
export ENABLE_DYNAMIC_PROMPT_TEMPLATES=true
```

### Per-Agent Configuration

Control optimization for specific agents:

```bash
# Enable for specific agents
export CLAUDE_PM_ENGINEER_MODEL_SELECTION=true
export CLAUDE_PM_DOCUMENTATION_MODEL_SELECTION=true

# Disable for specific agents
export CLAUDE_PM_QA_MODEL_SELECTION=false
```

### Test Mode Behavior

In test mode, the system uses full templates for comprehensive validation:

```bash
export CLAUDE_PM_TEST_MODE=true
```

## 📊 Usage Examples

### Basic Usage with Agent Loader

```python
from claude_pm.agents.agent_loader import get_agent_prompt_with_model_info

# Simple task - automatically uses Haiku + MINIMAL template
prompt, model, config = get_agent_prompt_with_model_info(
    'documentation',
    task_description='List all markdown files in the docs folder'
)

print(f"Model: {model}")  # claude-3-haiku-20240307
print(f"Complexity: {config['complexity_level']}")  # SIMPLE
print(f"Template: {config['template_used']}")  # MINIMAL
```

### Complex Task Example

```python
# Complex task - automatically uses Opus + FULL template
prompt, model, config = get_agent_prompt_with_model_info(
    'engineer',
    task_description='Refactor the authentication system to use OAuth2 with JWT tokens',
    file_count=10,
    integration_points=3,
    requires_testing=True,
    requires_documentation=True,
    technical_depth='deep'
)

print(f"Model: {model}")  # claude-4-opus
print(f"Complexity Score: {config['complexity_score']}")  # 85
print(f"Token Reduction: {config['token_reduction_percentage']}%")  # ~72%
```

### With Task Tool Helper Integration

```python
from claude_pm.utils.task_tool_helper import TaskToolHelper

helper = TaskToolHelper()

# The helper automatically applies optimization
result = await helper.create_agent_subprocess(
    agent_type="engineer",
    task_description="Implement payment processing with Stripe",
    requirements=["PCI compliance", "webhook handling"],
    performance_requirements={"reliability": "critical"}
)

# Optimization details in result
print(f"Selected Model: {result['selected_model']}")
print(f"Complexity Analysis: {result['model_config']}")
print(f"Token Savings: {result['optimization_metrics']['token_reduction']}%")
```

## 📈 Performance Metrics

### Token Reduction by Complexity

| Task Type | Average Reduction | Min | Max |
|-----------|------------------|-----|-----|
| SIMPLE | 52.1% | 48.2% | 56.8% |
| MEDIUM | 64.5% | 59.4% | 69.1% |
| COMPLEX | 71.8% | 67.3% | 78.4% |

### Processing Performance

- **Analysis Speed**: <0.007ms average (135,000+ analyses/second)
- **Optimization Overhead**: <1ms per request
- **Cache Hit Rate**: 99.7% for repeated agent access
- **Memory Impact**: Negligible with caching

### Real-World Impact

Based on typical task distribution (70% simple, 20% medium, 10% complex):
- **Overall Token Reduction**: 55-60%
- **Cost Savings**: 50-65% reduction in API costs
- **Response Time**: 30-40% faster due to smaller prompts

## 🔍 Monitoring and Analytics

### View Optimization Metrics

```python
from claude_pm.agents.agent_loader import get_model_selection_metrics

metrics = get_model_selection_metrics()

# Feature status
print(f"Optimization Enabled: {metrics['feature_flag']['global_enabled']}")
print(f"Agent Overrides: {metrics['feature_flag']['agent_overrides']}")

# Performance statistics
stats = metrics['selection_stats']
print(f"Total Optimizations: {stats['total_selections']}")
print(f"By Model: {stats['by_model']}")
print(f"Complexity Distribution: {stats['complexity_distribution']}")
print(f"Average Token Reduction: {stats['average_token_reduction']}%")
```

### Optimization Hints

Get specific optimization recommendations:

```python
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer

analyzer = TaskComplexityAnalyzer()
result = analyzer.analyze_task(
    task_description="Your task description",
    context_size=5000,
    file_count=3
)

hints = analyzer.get_prompt_optimization_hints(result)
print(f"Focus Areas: {hints['focus_areas']}")
print(f"Strategies: {hints['optimization_strategies']}")
```

## 🛠️ Troubleshooting

### Optimization Not Working

1. **Check Feature Flags**
   ```bash
   echo $ENABLE_DYNAMIC_MODEL_SELECTION
   echo $ENABLE_DYNAMIC_PROMPT_TEMPLATES
   ```

2. **Verify Task Description**
   ```python
   # Must provide task_description for analysis
   get_agent_prompt('engineer', task_description='Implement feature')
   ```

3. **Enable Debug Logging**
   ```python
   import logging
   logging.getLogger('claude_pm.agents.agent_loader').setLevel(logging.DEBUG)
   logging.getLogger('claude_pm.services.task_complexity_analyzer').setLevel(logging.DEBUG)
   ```

### Unexpected Model Selection

Review the complexity analysis breakdown:

```python
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer

analyzer = TaskComplexityAnalyzer()
result = analyzer.analyze_task(
    task_description="Your task here",
    file_count=5,
    requires_testing=True
)

print(f"Total Score: {result.complexity_score}")
print(f"Score Breakdown: {result.scoring_breakdown}")
print(f"Analysis Details: {result.analysis_details}")
```

### Force Specific Configuration

Override automatic selection when needed:

```python
# Force specific model
result = await helper.create_agent_subprocess(
    agent_type="qa",
    task_description="Critical validation",
    model_override="claude-4-opus"  # Force Opus
)

# Force specific template
from claude_pm.agents.base_agent_loader import prepend_base_instructions, PromptTemplate

prompt = prepend_base_instructions(
    agent_prompt,
    template=PromptTemplate.FULL  # Force FULL template
)
```

## 🚀 Best Practices

### 1. Gradual Rollout

Start with low-risk agents:

```bash
# Phase 1: Documentation and Research agents
export CLAUDE_PM_DOCUMENTATION_MODEL_SELECTION=true
export CLAUDE_PM_RESEARCH_MODEL_SELECTION=true

# Phase 2: Add QA and Ops after validation
export CLAUDE_PM_QA_MODEL_SELECTION=true
export CLAUDE_PM_OPS_MODEL_SELECTION=true

# Phase 3: Enable globally after success
export ENABLE_DYNAMIC_MODEL_SELECTION=true
```

### 2. Provide Context for Better Analysis

```python
# Include relevant parameters for accurate complexity assessment
prompt = get_agent_prompt(
    'engineer',
    task_description='Implement OAuth2 authentication',
    file_count=8,  # Helps determine complexity
    integration_points=2,  # External service integrations
    requires_testing=True,  # Adds to complexity score
    requires_documentation=True,  # Additional requirement
    technical_depth='deep'  # Architecture-level changes
)
```

### 3. Monitor Token Usage

Track before and after metrics:

```python
# Before enabling optimization
baseline_metrics = capture_current_metrics()

# After 24 hours with optimization
optimized_metrics = get_model_selection_metrics()

# Compare results
reduction = calculate_token_reduction(baseline_metrics, optimized_metrics)
print(f"Token usage reduced by {reduction}%")
```

### 4. Use Appropriate Complexity Hints

Help the analyzer understand your task:

- **Simple**: "list", "check", "verify", "read"
- **Medium**: "implement", "update", "fix", "test"
- **Complex**: "refactor", "architect", "optimize", "migrate"

## 🔄 Migration Guide

### From Non-Optimized Setup

1. **Baseline Metrics**: Capture current token usage
2. **Enable for Test Agent**: Start with one agent type
3. **Monitor for 24 Hours**: Track performance and costs
4. **Review Metrics**: Ensure expected reductions
5. **Gradual Expansion**: Enable for more agents
6. **Full Rollout**: Enable globally when confident

### Configuration Migration

```bash
# Old configuration (no optimization)
# No environment variables needed

# New configuration (with optimization)
export ENABLE_DYNAMIC_MODEL_SELECTION=true
export ENABLE_DYNAMIC_PROMPT_TEMPLATES=true  # Already default

# Optional: Configure thresholds (advanced)
export CLAUDE_PM_COMPLEXITY_SIMPLE_THRESHOLD=30
export CLAUDE_PM_COMPLEXITY_MEDIUM_THRESHOLD=70
```

## 🎯 Advanced Features

### Custom Complexity Scoring

Override default scoring for specific use cases:

```python
# Custom scoring for your domain
def custom_complexity_scorer(task_description, **kwargs):
    score = 0
    
    # Domain-specific keywords
    if 'kubernetes' in task_description.lower():
        score += 20  # K8s tasks are inherently complex
    
    if 'database migration' in task_description.lower():
        score += 30  # Migrations are high-risk
    
    return score

# Apply custom scoring
analyzer = TaskComplexityAnalyzer()
base_result = analyzer.analyze_task(task_description)
custom_score = custom_complexity_scorer(task_description)
final_score = base_result.complexity_score + custom_score
```

### A/B Testing

Compare optimized vs non-optimized performance:

```python
# A/B test configuration
def should_optimize(task_id):
    # 50/50 split for testing
    return hash(task_id) % 2 == 0

# Track metrics for both groups
if should_optimize(task_id):
    os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'true'
    group = 'optimized'
else:
    os.environ['ENABLE_DYNAMIC_MODEL_SELECTION'] = 'false'
    group = 'control'

# Execute task and track metrics
result = execute_task(task)
track_metrics(group, result)
```

## 🔮 Future Enhancements

- **Machine Learning Model Selection**: Learn optimal model selection from historical data
- **Cost Optimization Engine**: Balance performance vs cost based on budget constraints
- **Dynamic Threshold Adjustment**: Automatically tune complexity thresholds
- **Multi-Model Strategies**: Use multiple models for different parts of complex tasks
- **Prompt Compression**: Advanced compression techniques for further reduction

## 📚 Related Documentation

- [Dynamic Model Selection](./dynamic-model-selection.md) - Detailed model selection guide
- [Dynamic Prompt Templates](./dynamic-prompt-templates.md) - Template system details
- [Task Complexity Analyzer API](../api/task-complexity-analyzer.md) - API reference
- [Performance Benchmarks](../reports/prompt_optimization_test_report.md) - Detailed test results

---

**Documentation Version**: 1.0.0  
**Feature Version**: ISS-0168 (90% Complete)  
**Last Updated**: 2025-07-20