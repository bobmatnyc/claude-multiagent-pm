# Defensive Programming Guide

## Quick Reference

This guide provides defensive programming patterns used throughout the Claude PM framework to prevent common runtime errors.

## Lazy Initialization Pattern

### The Problem
Components initialized lazily can be `None` when accessed, causing `AttributeError`.

### The Solution
Always check component existence before use.

### ✅ Correct Pattern
```python
class Service:
    def __init__(self):
        self._component = None  # Lazy init
    
    def use_component(self):
        # Defensive check
        if not self._component:
            self._component = Component()
            self._setup_component()
        
        # Safe to use
        return self._component.method()
```

### ❌ Anti-Patterns to Avoid

**Direct Property Access Without Check:**
```python
@property
def component(self):
    return self._component  # Can be None!

# Later...
self.component.method()  # AttributeError!
```

**Assuming Initialization Order:**
```python
def __init__(self):
    self._bus = None
    self._use_bus()  # Error! Not initialized yet

def _use_bus(self):
    self._bus.send()  # AttributeError!
```

## Real-World Example: Message Bus Fix

### Before (Broken)
```python
async def orchestrate(self, agent_type, request_data):
    # Direct use without check
    response = await self._message_bus.send_request(
        agent_id=agent_type,
        request_data=request_data
    )  # AttributeError if _message_bus is None
```

### After (Fixed)
```python
async def orchestrate(self, agent_type, request_data):
    # Defensive initialization
    if not self._message_bus:
        self._message_bus = SimpleMessageBus()
        self._register_default_agent_handlers()
        logger.debug("message_bus_initialized")
    
    # Now safe to use
    response = await self._message_bus.send_request(
        agent_id=agent_type,
        request_data=request_data
    )
```

## Common Patterns in Claude PM

### 1. Component Initialization
```python
# Pattern used in orchestration
if not self._context_manager:
    self._context_manager = create_context_manager()

if not self._agent_registry:
    self._agent_registry = AgentRegistry()
```

### 2. Safe Property Access
```python
@property
def cache(self):
    """Safe lazy property access."""
    if self._cache is None:
        self._cache = SharedPromptCache()
    return self._cache
```

### 3. Initialization Validation
```python
def validate_setup(self):
    """Ensure all components are initialized."""
    required = {
        "message_bus": self._message_bus,
        "context_manager": self._context_manager,
        "registry": self._agent_registry
    }
    
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise RuntimeError(f"Missing components: {missing}")
```

## Best Practices

### 1. Initialize on First Use
```python
def get_component(self):
    if not self._component:
        self._component = self._create_component()
    return self._component
```

### 2. Group Related Initializations
```python
def _ensure_messaging_ready(self):
    """Initialize all messaging components together."""
    if not self._message_bus:
        self._message_bus = SimpleMessageBus()
        self._register_handlers()
        self._setup_routing()
```

### 3. Log Initialization Events
```python
if not self._service:
    logger.debug("Initializing service")
    self._service = Service()
    logger.info("Service initialized successfully")
```

### 4. Fail Fast with Clear Errors
```python
def require_component(self):
    if not self._component:
        raise RuntimeError(
            "Component not initialized. Call initialize() first."
        )
    return self._component
```

## Testing Defensive Code

### Unit Test Pattern
```python
def test_lazy_initialization():
    """Test component initializes on first use."""
    service = Service()
    assert service._component is None
    
    # First use triggers initialization
    result = service.use_component()
    assert service._component is not None
    
    # Subsequent uses reuse component
    component_ref = service._component
    service.use_component()
    assert service._component is component_ref
```

### Integration Test Pattern
```python
async def test_orchestration_initialization():
    """Test orchestrator handles uninitialized state."""
    orch = BackwardsCompatibleOrchestrator()
    
    # Should not fail even if components not initialized
    response = await orch.orchestrate_agent(
        "documentation",
        {"task": "test"}
    )
    
    # Verify components were initialized
    assert orch._message_bus is not None
    assert len(orch._message_bus.registered_agents) > 0
```

## Checklist for Code Review

When reviewing code with lazy initialization:

- [ ] All nullable components have defensive checks before use
- [ ] Initialization happens in logical groups
- [ ] Initialization is logged for debugging
- [ ] Error messages clearly indicate what needs initialization
- [ ] Tests verify both initialized and uninitialized states
- [ ] No assumptions about initialization order
- [ ] Thread-safety considered for concurrent access

## Related Issues
- [ISS-0128: Message Bus NoneType Error](../../tickets/issues/ISS-0128-message-bus-initialization-fix.md)
- [Orchestration Patterns](../technical/orchestration-patterns.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)