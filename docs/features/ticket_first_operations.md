# Ticket-First Operations Mode

## Overview

Ticket-first operations mode is a design pattern in the Claude PM Framework where all agent operations are scoped and filtered based on ticket metadata. This approach ensures that agents receive only the relevant context they need for their specific tasks, improving performance and reducing token usage.

## Key Benefits

1. **Context Isolation**: Each ticket operates with its own filtered context
2. **Performance Optimization**: Reduced token usage by filtering irrelevant files
3. **Security**: Sensitive data can be filtered based on ticket requirements
4. **Traceability**: All operations are linked to specific tickets

## How It Works

### 1. Ticket Creation

Tickets are created with metadata that defines:
- The agent type that will handle the task
- Context filtering requirements
- Priority level
- Focus areas and patterns

```python
ticket = ticketing_service.create_ticket(
    title="Update API documentation",
    description="Update docs with new endpoints",
    priority="high",
    metadata={
        "agent_type": "documentation",
        "context_requirements": {
            "focus_on": ["docs", "api", "readme"],
            "exclude": ["tests", "migrations"]
        }
    }
)
```

### 2. Context Filtering

The ContextManager uses ticket metadata to filter the full project context:

```python
filtered_context = context_manager.filter_context_for_agent(
    agent_type=ticket.metadata["agent_type"],
    full_context=full_project_context
)
```

### 3. Agent Execution

Agents receive only the filtered context relevant to their task:

```python
result = await orchestrator.delegate_to_agent(
    agent_type=ticket.metadata["agent_type"],
    task_description=f"[Ticket {ticket.id}] {ticket.title}",
    additional_context=filtered_context
)
```

## Context Filtering Rules

Each agent type has predefined filtering rules:

### Documentation Agent
- **Includes**: README, CHANGELOG, docs/, *.md files
- **Excludes**: Test files, migrations, build artifacts
- **Focus**: Documentation patterns and release notes

### QA Agent
- **Includes**: Test files, CI/CD configs, coverage reports
- **Excludes**: Documentation, deployment scripts
- **Focus**: Test patterns and quality metrics

### Engineer Agent
- **Includes**: Source code, libraries, technical specs
- **Excludes**: Tests (unless needed), documentation
- **Focus**: Implementation files and dependencies

### Security Agent
- **Includes**: Auth modules, security configs, sensitive patterns
- **Excludes**: Example files, test mocks
- **Focus**: Security-critical code and configurations

## Priority-Based Context Scoping

Ticket priority affects the amount of context provided:

- **Critical**: Full context access for urgent issues
- **High**: Extended context with relevant dependencies
- **Medium**: Standard filtered context
- **Low**: Minimal context for simple tasks

## Implementation Example

Here's a complete example of ticket-first operations:

```python
from claude_pm.orchestration.context_manager import ContextManager
from claude_pm.services.ticketing_service import TicketingService

# Initialize services
context_manager = ContextManager()
ticketing = TicketingService.get_instance()

# Create a ticket
ticket = ticketing.create_ticket(
    title="Implement user authentication",
    description="Add JWT-based auth to API",
    priority="high",
    metadata={
        "agent_type": "engineer",
        "context_requirements": {
            "include_patterns": ["auth", "user", "jwt"],
            "exclude_patterns": ["test_", "_test.py"],
            "max_file_size": 100000
        }
    }
)

# Get full project context
full_context = collect_project_context()

# Filter context based on ticket
filtered_context = context_manager.filter_context_for_agent(
    agent_type=ticket.metadata["agent_type"],
    full_context=full_context
)

# Execute with filtered context
result = execute_agent_task(ticket, filtered_context)
```

## Performance Metrics

The ticket-first approach typically achieves:
- 40-60% reduction in context size
- 50-70% reduction in token usage
- Faster agent response times
- Better focus on relevant files

## Best Practices

1. **Define Clear Metadata**: Include specific patterns and requirements in ticket metadata
2. **Use Agent Types**: Leverage predefined agent filters for common scenarios
3. **Monitor Reductions**: Track context reduction metrics to optimize filters
4. **Test Isolation**: Verify that filtered context includes all necessary files
5. **Update Filters**: Adjust filtering rules based on agent feedback

## Integration with AI Trackdown

When using ai-trackdown-pytools for ticket management:

```python
from trackdown import Ticket, TicketManager

# Create ticket with context metadata
ticket = Ticket(
    title="Security audit",
    metadata={
        "agent_type": "security",
        "context_scope": "auth_system"
    }
)

# The framework automatically applies context filtering
# based on the ticket metadata
```

## Troubleshooting

### Common Issues

1. **Missing Files**: If agents report missing files, check filter patterns
2. **Too Much Context**: Adjust exclude patterns to remove irrelevant files
3. **Performance**: Monitor token usage and adjust max_file_size limits

### Debug Mode

Enable context filtering debug logs:

```python
import logging
logging.getLogger("claude_pm.orchestration.context_manager").setLevel(logging.DEBUG)
```

## Future Enhancements

- Dynamic filter learning based on agent feedback
- Multi-ticket context sharing for related tasks
- Advanced pattern matching with regex support
- Context caching for repeated operations