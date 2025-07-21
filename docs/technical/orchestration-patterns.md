# Orchestration Patterns and Best Practices

## Overview

The Claude PM framework uses a sophisticated orchestration system that supports multiple modes of operation. This document covers key patterns, defensive programming techniques, and troubleshooting guidance.

## Orchestration Modes

### LOCAL Mode (Default)
- **Performance**: ~200ms response time
- **Characteristics**: In-process message passing, instant agent responses
- **Use Case**: Default mode for optimal performance
- **Components**: SimpleMessageBus, ContextManager, integrated handlers

### SUBPROCESS Mode
- **Performance**: 30+ seconds response time
- **Characteristics**: External process spawning, full isolation
- **Use Case**: When complete isolation is required
- **Enable**: Set `CLAUDE_PM_FORCE_SUBPROCESS_MODE=true`

### HYBRID Mode
- **Performance**: Variable based on agent complexity
- **Characteristics**: Mix of local and subprocess execution
- **Use Case**: Complex workflows requiring both speed and isolation

## Defensive Programming Patterns

### 1. Lazy Initialization with Defensive Checks

The orchestration system uses lazy initialization to improve startup performance. However, this requires defensive checks before component usage:

```python
# Pattern: Check and initialize before use
if not self._message_bus:
    self._message_bus = SimpleMessageBus()
    self._register_default_agent_handlers()
    logger.debug("message_bus_initialized")

# Safe to use after initialization check
response = await self._message_bus.send_request(...)
```

### 2. Component Initialization Order

Components must be initialized in the correct order to avoid NoneType errors:

1. **Message Bus**: Core communication infrastructure
2. **Context Manager**: Context filtering and management
3. **Agent Handlers**: Type-specific request handlers
4. **Auxiliary Services**: Registry, cache, runners

### 3. Error Prevention Pattern

```python
# Anti-pattern: Direct property access without initialization
@property
def message_bus(self):
    return self._message_bus  # Can return None!

# Better pattern: Initialize on first access
@property
def message_bus(self):
    if not self._message_bus:
        self._message_bus = SimpleMessageBus()
        self._register_default_agent_handlers()
    return self._message_bus

# Best pattern: Explicit initialization check before use
async def orchestrate(self, request):
    # Ensure initialization
    if not self._message_bus:
        self._message_bus = SimpleMessageBus()
        self._register_default_agent_handlers()
    
    # Now safe to use
    return await self._message_bus.send_request(...)
```

## Message Bus Architecture

### Component Structure
```
BackwardsCompatibleOrchestrator
├── _message_bus (SimpleMessageBus)
├── _context_manager (ContextManager)
├── _agent_registry (AgentRegistry)
└── _handlers (Dict[str, Callable])
```

### Message Flow
1. **Request Creation**: Agent request with context and parameters
2. **Bus Routing**: Message bus routes to appropriate handler
3. **Handler Execution**: Agent-specific logic processes request
4. **Response Return**: Structured response back through bus

### Handler Registration
```python
def _register_default_agent_handlers(self):
    """Register handlers for all core agent types."""
    agent_types = [
        "documentation", "qa", "engineer", "research",
        "version_control", "ticketing", "ops", "security",
        "data_engineer", "architect", "pm", "performance",
        "ux", "scaffolding"
    ]
    
    for agent_type in agent_types:
        handler = create_agent_handler(agent_type)
        self._message_bus.register_handler(agent_type, handler)
```

## Common Issues and Solutions

### Issue: AttributeError 'NoneType' object has no attribute 'send_request'

**Root Cause**: Message bus accessed before initialization in LOCAL mode.

**Symptoms**:
- Orchestration failures
- Agent delegation errors
- Performance degradation (fallback to subprocess)

**Solution**: Ensure defensive initialization checks are in place:

```python
# Add this check before any message_bus usage
if not self._message_bus:
    self._message_bus = SimpleMessageBus()
    self._register_default_agent_handlers()
```

### Issue: Slow Agent Response Times

**Root Cause**: System falling back to SUBPROCESS mode due to initialization failures.

**Symptoms**:
- 30+ second response times
- "Starting subprocess" messages in logs
- High CPU usage from process spawning

**Solution**: 
1. Check orchestration mode: `echo $CLAUDE_PM_ORCHESTRATION_MODE`
2. Ensure LOCAL mode is default (remove subprocess override)
3. Verify component initialization is successful

### Issue: Handler Registration Failures

**Root Cause**: Attempting to register handlers before message bus exists.

**Symptoms**:
- "No handler registered for agent" errors
- Agent delegation failures
- Incomplete orchestration

**Solution**: Ensure registration happens after bus initialization:

```python
if not self._message_bus:
    self._message_bus = SimpleMessageBus()
# Now safe to register
self._register_default_agent_handlers()
```

## Performance Optimization

### LOCAL Mode Benefits
- **150x faster** than subprocess mode
- No process spawn overhead
- Shared memory context
- Instant message routing

### Monitoring Performance
```python
# Log mode and timing
logger.info(f"Orchestration mode: {self.mode}")
start_time = time.perf_counter()
response = await self.orchestrate(...)
duration = time.perf_counter() - start_time
logger.info(f"Orchestration completed in {duration:.3f}s")
```

### Performance Thresholds
- **LOCAL**: < 1 second expected
- **SUBPROCESS**: 20-40 seconds normal
- **HYBRID**: Variable, monitor per-agent

## Best Practices

### 1. Always Use Defensive Initialization
- Check component existence before use
- Initialize in consistent order
- Log initialization events

### 2. Monitor Orchestration Mode
- Default to LOCAL for performance
- Use SUBPROCESS only when needed
- Log mode changes and reasons

### 3. Handle Initialization Failures Gracefully
- Provide fallback mechanisms
- Log detailed error context
- Maintain system stability

### 4. Test Component Integration
```python
async def validate_orchestration_setup(self):
    """Validate all orchestration components are ready."""
    checks = {
        "message_bus": self._message_bus is not None,
        "context_manager": self._context_manager is not None,
        "handlers_registered": len(self._message_bus.registered_agents) > 0
    }
    
    if not all(checks.values()):
        logger.error(f"Orchestration validation failed: {checks}")
        return False
    
    return True
```

## Related Documentation
- [Message Bus Implementation](../api/message-bus.md)
- [Context Manager Guide](../api/context-manager.md)
- [Agent Handler Patterns](../development/agent-handlers.md)
- [Performance Tuning](../operations/performance-tuning.md)