# Memory Trigger Infrastructure

## Overview

The Memory Trigger Infrastructure provides automatic memory creation and management throughout the Claude PM Framework. It enables seamless capture of operational knowledge, patterns, decisions, and error resolutions without manual intervention.

## Architecture

### Core Components

1. **Memory Trigger Orchestrator** (`trigger_orchestrator.py`)
   - Central coordination of memory triggers
   - Queue management and background processing
   - Policy-based trigger evaluation
   - Performance metrics and monitoring

2. **Trigger Policy Engine** (`trigger_policies.py`)
   - Configurable policies for trigger decisions
   - Rule-based filtering and modification
   - Rate limiting and batch processing
   - Policy validation and management

3. **Framework Memory Hooks** (`framework_hooks.py`)
   - Integration points throughout the framework
   - Event-driven memory capture
   - Context-aware trigger generation
   - Convenience methods for common operations

4. **Memory Trigger Decorators** (`decorators.py`)
   - Easy-to-use decorators for automatic memory capture
   - Context managers for complex workflows
   - Function argument and result capture
   - Error handling and recovery

5. **Memory Trigger Service** (`memory_trigger_service.py`)
   - Unified service interface
   - Component orchestration and lifecycle management
   - Health monitoring and metrics collection
   - Configuration management

## Quick Start

### Basic Usage

```python
from claude_pm.services.memory import (
    create_memory_trigger_service,
    workflow_memory_trigger,
    agent_memory_trigger,
    workflow_trigger_context
)

# Initialize service
async with create_memory_trigger_service() as service:
    # Service automatically integrates with framework
    pass

# Use decorators for automatic memory capture
@workflow_memory_trigger(project_name="my-project", workflow_type="push")
async def execute_push_workflow():
    # Workflow logic here
    return {"status": "success"}

@agent_memory_trigger(agent_type="qa", project_name="my-project")
async def run_qa_validation():
    # QA logic here
    return {"tests_passed": 42}

# Use context managers for complex workflows
async with workflow_trigger_context(
    operation_name="complex_deployment",
    project_name="my-project",
    workflow_type="deploy"
) as ctx:
    # Add metadata and tags as needed
    ctx.add_metadata(environment="production")
    ctx.add_tags("production", "deployment")
    
    # Execute workflow steps
    result = await deploy_application()
    
    # Set final result
    ctx.set_result(result)
```

### Advanced Configuration

```python
# Custom configuration
config = {
    "enabled": True,
    "memory": {
        "fallback_chain": ["mem0ai", "sqlite", "memory"],
        "circuit_breaker_threshold": 5,
        "detection_timeout": 2.0
    },
    "orchestrator": {
        "max_queue_size": 1000,
        "batch_size": 10,
        "timeout_seconds": 30
    },
    "policies": {
        "enabled": True,
        "default_decision": "allow",
        "rate_limiting": True
    },
    "hooks": {
        "enabled": True,
        "capture_on_success": True,
        "capture_on_error": True,
        "capture_args": False,
        "capture_result": True
    }
}

service = create_memory_trigger_service(config)
```

## Trigger Types

### 1. Workflow Completion Triggers
- **Purpose**: Capture successful workflow patterns and outcomes
- **Category**: PATTERN
- **Priority**: HIGH
- **Examples**: Push workflows, deployment workflows, publication workflows

### 2. Issue Resolution Triggers
- **Purpose**: Capture issue resolution patterns and solutions
- **Category**: PROJECT
- **Priority**: HIGH
- **Examples**: Bug fixes, feature implementations, requirement changes

### 3. Agent Operation Triggers
- **Purpose**: Capture agent operation patterns and results
- **Category**: PATTERN
- **Priority**: MEDIUM
- **Examples**: QA validations, documentation updates, code reviews

### 4. Error Resolution Triggers
- **Purpose**: Capture error patterns and recovery solutions
- **Category**: ERROR
- **Priority**: CRITICAL
- **Examples**: Backend failures, connectivity issues, configuration errors

### 5. Project Milestone Triggers
- **Purpose**: Capture project progress and milestone achievements
- **Category**: PROJECT
- **Priority**: HIGH
- **Examples**: Version releases, feature completions, architectural decisions

### 6. Knowledge Capture Triggers
- **Purpose**: Capture general knowledge and insights
- **Category**: PATTERN
- **Priority**: MEDIUM
- **Examples**: Best practices, code patterns, solution approaches

### 7. Pattern Detection Triggers
- **Purpose**: Capture detected patterns and trends
- **Category**: PATTERN
- **Priority**: MEDIUM
- **Examples**: Code quality patterns, performance patterns, usage patterns

### 8. Decision Point Triggers
- **Purpose**: Capture important decisions and rationale
- **Category**: PROJECT
- **Priority**: HIGH
- **Examples**: Architecture decisions, technology choices, process changes

## Decorator Reference

### Workflow Decorators

```python
@workflow_memory_trigger(
    project_name="my-project",
    workflow_type="push",
    priority=TriggerPriority.HIGH,
    capture_result=True
)
async def my_workflow():
    pass
```

### Agent Decorators

```python
@agent_memory_trigger(
    agent_type="qa",
    project_name="my-project",
    priority=TriggerPriority.MEDIUM,
    capture_result=True
)
async def my_agent_operation():
    pass
```

### Issue Decorators

```python
@issue_memory_trigger(
    issue_id="ISS-001",
    project_name="my-project",
    priority=TriggerPriority.HIGH
)
async def resolve_issue():
    pass
```

### Error Decorators

```python
@error_memory_trigger(
    error_type="database_error",
    project_name="my-project",
    priority=TriggerPriority.CRITICAL
)
async def handle_database_error():
    pass
```

### Knowledge Decorators

```python
@knowledge_memory_trigger(
    knowledge_type="best_practices",
    project_name="my-project",
    priority=TriggerPriority.MEDIUM
)
async def capture_best_practices():
    pass
```

### Decision Decorators

```python
@decision_memory_trigger(
    decision_type="architecture",
    project_name="my-project",
    priority=TriggerPriority.HIGH
)
async def make_architecture_decision():
    pass
```

## Context Managers

### Workflow Context

```python
async with workflow_trigger_context(
    operation_name="deployment",
    project_name="my-project",
    workflow_type="deploy",
    environment="production"
) as ctx:
    # Add metadata
    ctx.add_metadata(version="1.0.0", replicas=3)
    ctx.add_tags("production", "deployment", "v1.0.0")
    
    # Execute workflow
    result = await deploy_to_production()
    
    # Set result
    ctx.set_result(result)
```

### Agent Context

```python
async with agent_trigger_context(
    operation_name="comprehensive_qa",
    project_name="my-project",
    agent_type="qa",
    test_suite="integration"
) as ctx:
    # Add test metadata
    ctx.add_metadata(coverage_threshold=80, timeout=300)
    ctx.add_tags("integration", "qa", "comprehensive")
    
    # Execute tests
    test_results = await run_integration_tests()
    
    # Set results
    ctx.set_result(test_results)
```

### Issue Context

```python
async with issue_trigger_context(
    operation_name="fix_memory_leak",
    project_name="my-project",
    issue_id="ISS-042",
    priority="critical"
) as ctx:
    # Add issue metadata
    ctx.add_metadata(component="memory_service", severity="high")
    ctx.add_tags("memory_leak", "performance", "critical")
    
    # Execute fix
    fix_result = await fix_memory_leak()
    
    # Set result
    ctx.set_result(fix_result)
```

## Policy Configuration

### Policy Rules

```python
from claude_pm.services.memory import PolicyRule, PolicyDecision

# Allow critical issues
critical_rule = PolicyRule(
    name="critical_issues",
    condition="priority:critical",
    action=PolicyDecision.ALLOW,
    priority=200
)

# Batch low priority items
batch_rule = PolicyRule(
    name="batch_low_priority",
    condition="priority:low",
    action=PolicyDecision.BATCH,
    priority=10
)

# Modify test failures
modify_rule = PolicyRule(
    name="test_failures",
    condition="metadata:success=false",
    action=PolicyDecision.MODIFY,
    priority=100,
    metadata={"modified_priority": "high"}
)
```

### Policy Conditions

- **Type conditions**: `type:workflow_completion`
- **Priority conditions**: `priority:high`
- **Project conditions**: `project:my-project*`
- **Source conditions**: `source:qa_agent`
- **Content conditions**: `content:error`
- **Tag conditions**: `tag:production`
- **Metadata conditions**: `metadata:success=true`

## Integration Examples

### CLI Integration

```python
from claude_pm.services.memory.cli_integration import cli_memory_trigger

@cli_memory_trigger(operation_type="workflow", capture_result=True)
async def push_command(project: str, branch: str):
    # CLI command logic
    return {"success": True, "branch": branch}
```

### Service Integration

```python
from claude_pm.services.memory import MemoryTriggerService

class MyService:
    def __init__(self):
        self.memory_service = MemoryTriggerService()
    
    async def initialize(self):
        await self.memory_service.initialize()
    
    @workflow_memory_trigger(project_name="my-project", workflow_type="process")
    async def process_data(self, data):
        # Service logic
        return {"processed": len(data)}
```

### Framework Integration

```python
from claude_pm.services.memory import initialize_global_memory_trigger_service

# Initialize during framework startup
async def initialize_framework():
    # Initialize memory triggers
    await initialize_global_memory_trigger_service({
        "enabled": True,
        "memory": {"fallback_chain": ["mem0ai", "sqlite"]}
    })
    
    # Other framework initialization
    pass
```

## Monitoring and Metrics

### Service Health

```python
# Get service health
health = await service.get_service_health()

print(f"Service Status: {health['service_initialized']}")
print(f"Memory Service: {health['memory_service']['status']}")
print(f"Trigger Orchestrator: {health['trigger_orchestrator']['status']}")
print(f"Policy Engine: {health['policy_engine']['status']}")
print(f"Framework Hooks: {health['framework_hooks']['status']}")
```

### Metrics Collection

```python
# Get service metrics
metrics = await service.get_service_metrics()

# Memory service metrics
memory_metrics = metrics['memory_service']
print(f"Total Operations: {memory_metrics['total_operations']}")
print(f"Successful Operations: {memory_metrics['successful_operations']}")

# Trigger orchestrator metrics
trigger_metrics = metrics['trigger_orchestrator']
print(f"Total Triggers: {trigger_metrics['total_triggers']}")
print(f"Successful Triggers: {trigger_metrics['successful_triggers']}")
print(f"Queue Size: {trigger_metrics['queue_size']}")

# Framework hooks metrics
hooks_metrics = metrics['framework_hooks']
print(f"Hooks Executed: {hooks_metrics['hooks_executed']}")
print(f"Memory Captures: {hooks_metrics['memory_captures']}")
```

## Performance Considerations

### Asynchronous Processing

- All memory operations are asynchronous and non-blocking
- Background queue processing for non-critical triggers
- Immediate processing for critical triggers
- Graceful degradation when memory service unavailable

### Resource Management

- Configurable queue sizes and batch processing
- Circuit breaker patterns for backend failures
- Automatic fallback to alternative backends
- Memory cleanup and resource deallocation

### Scalability

- Horizontal scaling through multiple service instances
- Load balancing across memory backends
- Caching and performance optimization
- Metrics and monitoring for performance tuning

## Testing

### Unit Tests

```bash
# Run memory trigger tests
python -m pytest tests/test_memory_trigger_infrastructure.py -v

# Run specific test categories
python -m pytest tests/test_memory_trigger_infrastructure.py::TestTriggerOrchestrator -v
python -m pytest tests/test_memory_trigger_infrastructure.py::TestTriggerPolicyEngine -v
python -m pytest tests/test_memory_trigger_infrastructure.py::TestMemoryTriggerDecorators -v
```

### Integration Tests

```bash
# Run integration tests
python -m pytest tests/test_memory_trigger_infrastructure.py::TestIntegrationScenarios -v
```

### Demo

```python
# Run the comprehensive demo
python claude_pm/services/memory/examples/framework_integration.py
```

## Configuration Reference

### Memory Service Configuration

```python
"memory": {
    "fallback_chain": ["mem0ai", "sqlite", "tinydb", "memory"],
    "circuit_breaker_threshold": 5,
    "circuit_breaker_recovery": 60,
    "detection_timeout": 2.0,
    "detection_retries": 3,
    "metrics_retention": 86400,
    "mem0ai_enabled": True,
    "sqlite_enabled": True,
    "tinydb_enabled": True,
    "memory_enabled": True
}
```

### Trigger Orchestrator Configuration

```python
"orchestrator": {
    "enabled": True,
    "max_queue_size": 1000,
    "batch_size": 10,
    "timeout_seconds": 30,
    "processing_interval": 1.0
}
```

### Policy Engine Configuration

```python
"policies": {
    "enabled": True,
    "default_decision": "allow",
    "rate_limiting": True,
    "max_rate_per_hour": 1000,
    "max_rate_per_minute": 100
}
```

### Framework Hooks Configuration

```python
"hooks": {
    "enabled": True,
    "capture_on_success": True,
    "capture_on_error": True,
    "capture_args": False,
    "capture_result": True,
    "max_content_length": 10000,
    "max_metadata_size": 5000
}
```

## Troubleshooting

### Common Issues

1. **Memory Service Not Available**
   - Check memory service backend configuration
   - Verify network connectivity to mem0AI service
   - Ensure fallback backends are configured

2. **Triggers Not Firing**
   - Check trigger orchestrator configuration
   - Verify policy engine rules
   - Ensure global hooks are set

3. **Performance Issues**
   - Adjust queue sizes and batch processing
   - Review policy rules and rate limiting
   - Monitor backend performance

4. **Memory Storage Issues**
   - Check backend storage capacity
   - Verify memory cleanup processes
   - Monitor memory usage patterns

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('claude_pm.services.memory').setLevel(logging.DEBUG)

# Check service status
service = await get_global_memory_trigger_service()
health = await service.get_service_health()
print(json.dumps(health, indent=2))
```

## Best Practices

1. **Use Appropriate Trigger Types**
   - Choose the right trigger type for your use case
   - Set appropriate priorities
   - Use meaningful tags and metadata

2. **Configure Policies Wisely**
   - Start with permissive policies
   - Gradually add restrictions based on usage
   - Monitor policy effectiveness

3. **Handle Errors Gracefully**
   - Always handle memory service unavailability
   - Implement fallback mechanisms
   - Log errors appropriately

4. **Monitor Performance**
   - Track memory trigger metrics
   - Monitor backend performance
   - Adjust configuration based on usage patterns

5. **Test Thoroughly**
   - Test memory triggers in development
   - Verify trigger behavior in different scenarios
   - Test fallback mechanisms

## Contributing

When contributing to the memory trigger infrastructure:

1. **Follow Existing Patterns**
   - Use existing decorators and context managers
   - Follow naming conventions
   - Maintain consistency with framework patterns

2. **Add Tests**
   - Write unit tests for new functionality
   - Add integration tests for complex scenarios
   - Update test documentation

3. **Update Documentation**
   - Document new trigger types
   - Update configuration reference
   - Add examples for new features

4. **Consider Performance**
   - Ensure asynchronous operations
   - Avoid blocking operations
   - Consider memory and resource usage

## License

This memory trigger infrastructure is part of the Claude PM Framework and is subject to the same license terms.