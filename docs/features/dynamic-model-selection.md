# Dynamic Model Selection Based on Task Complexity

## Overview

The Claude PM Framework now supports dynamic model selection based on task complexity analysis. This feature automatically selects the most appropriate Claude model (Haiku, Sonnet, or Opus) based on the complexity of the task being delegated to agents.

## How It Works

### 1. Task Complexity Analysis

When a task is delegated to an agent, the framework analyzes various factors to determine complexity:

- **Task Description**: Verb complexity, technical keywords, multi-step indicators
- **Context Size**: Amount of context information required
- **File Operations**: Number of files involved
- **Integration Points**: System integration complexity
- **Additional Requirements**: Research, testing, documentation needs
- **Technical Depth**: Shallow, moderate, or deep technical requirements

### 2. Complexity Scoring

The analyzer produces a complexity score (0-100) and categorizes tasks into three levels:

- **SIMPLE (0-30)**: Basic operations like listing, reading, or simple checks
- **MEDIUM (31-70)**: Standard implementation, bug fixes, or moderate changes
- **COMPLEX (71-100)**: Architecture, refactoring, or comprehensive system changes

### 3. Model Selection

Based on the complexity level, the appropriate model is selected:

- **Haiku**: For SIMPLE tasks (fastest, most cost-effective)
- **Sonnet**: For MEDIUM tasks (balanced performance and capability)
- **Opus**: For COMPLEX tasks (highest capability for demanding work)

## Configuration

### Feature Flag

Dynamic model selection is controlled by an environment variable:

```bash
# Enable globally
export ENABLE_DYNAMIC_MODEL_SELECTION=true

# Disable globally (default)
export ENABLE_DYNAMIC_MODEL_SELECTION=false
```

### Per-Agent Overrides

You can enable/disable dynamic selection for specific agents:

```bash
# Enable for engineer agent only
export CLAUDE_PM_ENGINEER_MODEL_SELECTION=true

# Disable for QA agent specifically
export CLAUDE_PM_QA_MODEL_SELECTION=false
```

### Default Models

When dynamic selection is disabled, agents use their default models:

- **Orchestrator, Engineer, Architecture**: Opus (complex work)
- **Documentation, QA, Research, Ops, Security, Data Engineer**: Sonnet (balanced)

## Usage Examples

### Basic Usage

```python
from claude_pm.agents.agent_loader import get_agent_prompt_with_model_info

# Simple task - will select Haiku
prompt, model, config = get_agent_prompt_with_model_info(
    'documentation',
    task_description='List all markdown files in the docs folder'
)

# Complex task - will select Opus
prompt, model, config = get_agent_prompt_with_model_info(
    'engineer',
    task_description='Refactor the authentication system with OAuth2 and JWT',
    file_count=10,
    integration_points=3,
    requires_testing=True,
    technical_depth='deep'
)
```

### With Task Tool Helper

```python
from claude_pm.utils.task_tool_helper import TaskToolHelper

helper = TaskToolHelper()

# The helper automatically uses complexity analysis
result = await helper.create_agent_subprocess(
    agent_type="engineer",
    task_description="Implement new payment processing system",
    requirements=["PCI compliance", "Stripe integration"],
    performance_requirements={"reliability": "critical"}
)

# Model selection is included in the result
print(f"Selected model: {result['selected_model']}")
print(f"Complexity: {result['model_config']['complexity_level']}")
```

## Metrics and Monitoring

### View Selection Metrics

```python
from claude_pm.agents.agent_loader import get_model_selection_metrics

metrics = get_model_selection_metrics()

# Feature flag status
print(f"Global enabled: {metrics['feature_flag']['global_enabled']}")
print(f"Agent overrides: {metrics['feature_flag']['agent_overrides']}")

# Selection statistics
stats = metrics['selection_stats']
print(f"Total selections: {stats['total_selections']}")
print(f"By model: {stats['by_model']}")
print(f"Complexity distribution: {stats['complexity_distribution']}")
```

### Metrics Collected

- Total model selections
- Selections by model type
- Selections by agent
- Selection method (dynamic vs default)
- Complexity score distribution

## Best Practices

### 1. Gradual Rollout

Start with a single agent type:

```bash
# Test with documentation agent first
export CLAUDE_PM_DOCUMENTATION_MODEL_SELECTION=true

# Monitor performance and costs
# Then expand to other agents
```

### 2. Monitor Token Usage

Track token usage before and after enabling:

```python
# Metrics are automatically collected in SharedPromptCache
# Review after 24 hours of usage
metrics = get_model_selection_metrics()
```

### 3. Provide Complexity Hints

Help the analyzer make better decisions:

```python
# Provide additional context for accurate analysis
prompt = get_agent_prompt(
    'engineer',
    task_description='Implement feature',
    file_count=5,  # Helps determine complexity
    requires_testing=True,  # Adds to complexity score
    technical_depth='moderate'  # Influences model selection
)
```

### 4. Override When Needed

For critical tasks, you can still specify a model:

```python
# In TaskToolHelper
result = await helper.create_agent_subprocess(
    agent_type="qa",
    task_description="Simple check",
    model_override="claude-4-opus"  # Force Opus for critical validation
)
```

## Performance Optimization

### Optimal Prompt Sizes

Each model has recommended prompt size ranges:

- **Haiku**: 300-500 characters (concise, focused)
- **Sonnet**: 700-1000 characters (balanced detail)
- **Opus**: 1200-1500 characters (comprehensive context)

The analyzer provides these recommendations in the analysis results.

### Caching

Model selection results are cached with agent prompts, ensuring:

- No repeated analysis for the same task
- 99.7% performance improvement via SharedPromptCache
- 1-hour TTL for dynamic adaptation

## Troubleshooting

### Dynamic Selection Not Working

1. Check feature flag:
   ```bash
   echo $ENABLE_DYNAMIC_MODEL_SELECTION
   ```

2. Verify task description is provided:
   ```python
   # This won't trigger dynamic selection
   get_agent_prompt('engineer')
   
   # This will
   get_agent_prompt('engineer', task_description='Implement feature')
   ```

3. Check logs for selection decisions:
   ```python
   # Enable logging
   import logging
   logging.getLogger('claude_pm.agents.agent_loader').setLevel(logging.INFO)
   ```

### Unexpected Model Selection

Review the complexity analysis:

```python
from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer

analyzer = TaskComplexityAnalyzer()
result = analyzer.analyze_task(
    task_description="Your task here",
    # ... other parameters
)

print(f"Score: {result.complexity_score}")
print(f"Breakdown: {result.scoring_breakdown}")
print(f"Details: {result.analysis_details}")
```

## Future Enhancements

- Machine learning-based model selection
- Cost optimization algorithms
- Performance feedback loop
- Custom complexity scoring rules
- A/B testing framework for model selection strategies