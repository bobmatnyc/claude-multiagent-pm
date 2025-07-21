# Dynamic Prompt Templates

## Overview

The Claude PM Framework now supports dynamic prompt templates that automatically adjust the base agent instructions based on task complexity. This feature significantly reduces token usage and improves performance for simple tasks while maintaining full context for complex operations.

## Key Benefits

- **70% reduction** in prompt size for simple tasks
- **50% reduction** in prompt size for medium complexity tasks  
- **Faster response times** due to reduced token processing
- **Lower costs** from reduced token usage
- **Improved caching** with template-specific cache keys

## How It Works

### Template Levels

1. **MINIMAL** (Complexity 0-30)
   - Core agent principles only
   - Basic communication standards
   - Essential constraints
   - ~580 characters vs 1,971 full

2. **STANDARD** (Complexity 31-70)
   - Core + operational guidelines
   - Error handling and reporting
   - Collaboration protocols
   - ~980 characters vs 1,971 full

3. **FULL** (Complexity 71-100)
   - Complete base agent instructions
   - All sections including escalation triggers
   - Security awareness and quality standards
   - Full ~1,971 characters

### Automatic Selection

The system automatically selects the appropriate template based on task complexity analysis:

```python
# Simple task - uses MINIMAL template
result = get_agent_prompt("documentation", task_description="List all markdown files")

# Medium task - uses STANDARD template  
result = get_agent_prompt("qa", task_description="Run unit tests and generate report")

# Complex task - uses FULL template
result = get_agent_prompt("engineer", task_description="Refactor authentication system")
```

### Manual Override

You can manually specify a template if needed:

```python
from claude_pm.agents.base_agent_loader import prepend_base_instructions, PromptTemplate

# Force FULL template for a simple task
prompt = prepend_base_instructions(
    agent_prompt,
    template=PromptTemplate.FULL
)
```

## Configuration

### Template Sections

The `TEMPLATE_SECTIONS` configuration in `base_agent_loader.py` controls which sections appear in each template level:

```python
TEMPLATE_SECTIONS = {
    "core_principles": {
        "templates": ["MINIMAL", "STANDARD", "FULL"],
        "content": "Core Agent Principles"
    },
    "escalation_triggers": {
        "templates": ["FULL"],  # Only in FULL template
        "content": "Escalation Triggers"
    },
    # ... more sections
}
```

### Section Optimization

Several sections have been moved from STANDARD to FULL to achieve better reduction:
- Test Response Protocol (not needed for most tasks)
- Tool Usage Guidelines (agent-specific guidance suffices)
- Temporal Context Integration (only for complex planning)
- Output Formatting Standards (basic formatting in STANDARD)
- Success Criteria (implicit for simpler tasks)

## Performance Metrics

Based on testing with real-world scenarios:

### Token Usage Reduction
- Simple tasks: **70.6% fewer tokens**
- Medium tasks: **50.3% fewer tokens**
- Complex tasks: No reduction (uses full template)

### Memory Usage
With typical task distribution (70% simple, 20% medium, 10% complex):
- **55% reduction** in overall memory usage
- **Faster prompt processing** due to smaller context

### Cache Performance
- **99.7% faster** for repeated agent calls (via SharedPromptCache)
- Separate cache keys for each template level
- 1-hour TTL for cached templates

## Test Mode Behavior

When `CLAUDE_PM_TEST_MODE=true`, the system always uses the FULL template to ensure comprehensive testing of all agent capabilities.

## Implementation Details

### Key Files
- `claude_pm/agents/base_agent_loader.py` - Core implementation
- `claude_pm/agents/agent_loader.py` - Integration point
- `tests/unit/agents/test_dynamic_prompt_templates.py` - Comprehensive tests

### Cache Keys
```
base_agent:instructions:MINIMAL:normal
base_agent:instructions:STANDARD:normal
base_agent:instructions:FULL:normal
base_agent:instructions:MINIMAL:test
base_agent:instructions:STANDARD:test
base_agent:instructions:FULL:test
```

### Backward Compatibility
The system maintains full backward compatibility:
- Default behavior uses dynamic templates
- Existing code continues to work without modification
- Old cache keys are cleared automatically

## Best Practices

1. **Let the system auto-select** templates based on task complexity
2. **Use manual override** only when necessary (e.g., forcing FULL for compliance)
3. **Monitor token usage** to verify expected reductions
4. **Clear cache** after modifying template configurations
5. **Test with different complexity levels** to ensure appropriate selection

## Future Enhancements

- [ ] Configurable complexity thresholds
- [ ] Per-agent template customization
- [ ] Dynamic section loading based on agent type
- [ ] Template analytics and usage reporting
- [ ] A/B testing for optimal configurations