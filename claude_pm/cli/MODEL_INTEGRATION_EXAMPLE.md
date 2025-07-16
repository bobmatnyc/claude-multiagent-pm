# CLI Model Override Integration Example

This document demonstrates how to integrate the `--model` CLI flag in your commands.

## Basic Usage

Users can override the AI model selection for any command:

```bash
# Use Claude Sonnet 4 for a command
claude-pm --model sonnet status

# Use Claude 4 Opus for complex tasks
claude-pm --model opus test

# Use Claude 3 Haiku for simple tasks
claude-pm --model haiku agents status

# Use full model ID
claude-pm --model claude-sonnet-4-20250514 models --verbose
```

## Available Model Aliases

- `sonnet` → `claude-sonnet-4-20250514` (Claude Sonnet 4 - recommended for most tasks)
- `opus` → `claude-4-opus` (Claude 4 Opus - for complex reasoning tasks)
- `haiku` → `claude-3-haiku-20240307` (Claude 3 Haiku - for simple, fast tasks)
- `sonnet3` → `claude-3-5-sonnet-20241022` (Claude 3.5 Sonnet - legacy)
- `opus3` → `claude-3-opus-20240229` (Claude 3 Opus - legacy)

## Integration in Commands

### Method 1: Using get_model_override()

```python
import click
from ..cli.cli_utils import get_model_override

@cli_group.command()
@click.pass_context
def my_command(ctx):
    """Example command that respects model override."""
    model_override = get_model_override(ctx)
    
    if model_override:
        print(f"Using overridden model: {model_override}")
        # Use the specified model for AI operations
    else:
        print("Using default model selection")
        # Use default model selection
```

### Method 2: Using create_model_selector_with_override()

```python
import click
from ..cli.cli_utils import create_model_selector_with_override

@cli_group.command()
@click.pass_context
def my_command(ctx):
    """Example command using ModelSelector with override."""
    # Create selector with CLI override applied
    selector = create_model_selector_with_override(ctx)
    
    # Select model for specific agent type
    model_type, config = selector.select_model_for_agent('engineer')
    
    print(f"Selected model: {model_type.value}")
    print(f"Max tokens: {config.max_tokens}")
    print(f"Reasoning tier: {config.reasoning_tier}")
```

### Method 3: Environment Variable Override

The CLI automatically sets `CLAUDE_PM_MODEL_OVERRIDE` environment variable when `--model` is used. Existing code that checks environment variables will automatically pick up the override:

```python
import os
from ..services.model_selector import ModelSelector

def my_function():
    # ModelSelector automatically checks CLAUDE_PM_MODEL_OVERRIDE
    selector = ModelSelector()
    model_type, config = selector.select_model_for_agent('qa')
    
    # Will use CLI override if --model flag was used
    return model_type.value
```

## Model Command

Use the `models` command to explore available options:

```bash
# Show basic model information
claude-pm models

# Show detailed model configurations
claude-pm models --verbose

# Show model aliases
claude-pm models --aliases

# Check current override
claude-pm --model opus models
```

## Validation

The CLI validates model inputs and provides helpful error messages:

```bash
# Valid aliases are accepted
claude-pm --model sonnet status  # ✅ Works

# Invalid inputs show warning but continue with defaults
claude-pm --model invalid-model status  # ⚠️ Warning shown, continues with default

# Full model IDs are validated
claude-pm --model claude-sonnet-4-20250514 status  # ✅ Works
```

## Best Practices

1. **Use aliases for common models**: `sonnet`, `opus`, `haiku` are easier to remember
2. **Check for overrides in commands**: Use `get_model_override()` to respect user choice
3. **Provide model-aware help**: Show users which model will be used for different operations
4. **Validate compatibility**: Some operations may require specific model capabilities

## Integration with Task Tool

When creating subprocess agents via Task Tool, the model override is automatically applied through the environment variable mechanism. No special integration needed for Task Tool workflows.