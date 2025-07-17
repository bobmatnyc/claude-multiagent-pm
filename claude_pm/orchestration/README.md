# Claude PM Orchestration Module

This module provides core components for local agent orchestration, enabling asynchronous communication between agents without external dependencies.

## Components

### 1. OrchestrationDetector
Detects and validates local orchestration configuration.

**Features:**
- Validates presence of `.claude-pm/orchestration.yaml`
- Ensures proper configuration structure
- Handles missing or invalid configuration gracefully

**Usage:**
```python
from claude_pm.orchestration import OrchestrationDetector

detector = OrchestrationDetector()
is_configured = await detector.is_orchestration_configured()
config = await detector.get_configuration()
```

### 2. SimpleMessageBus
Provides async request/response communication between agents.

**Features:**
- UUID-based message correlation
- Configurable timeouts (default 30 seconds)
- Concurrent message handling
- Error handling and timeout management
- Thread-safe operations

**Usage:**
```python
from claude_pm.orchestration import SimpleMessageBus, Request, Response

# Create message bus
bus = SimpleMessageBus()

# Register handler
async def handler(request: Request) -> Response:
    result = await process_request(request.data)
    return Response(
        request_id=request.id,
        agent_id="my_agent",
        data={"result": result}
    )

bus.register_handler("my_agent", handler)

# Send request
response = await bus.send_request(
    "my_agent",
    {"action": "process", "input": "data"},
    timeout=30.0
)

# Shutdown when done
await bus.shutdown()
```

## Message Types

### Message
Base message class with correlation ID and metadata.

### Request
Request message for initiating async operations.
- Includes timeout specification
- Tracks agent target
- Contains request data payload

### Response
Response message containing operation results.
- Links to original request via request_id
- Includes success/failure status
- Can contain error information

### MessageStatus
Enum representing message processing states:
- `PENDING`: Message created but not processed
- `PROCESSING`: Handler is actively processing
- `COMPLETED`: Successfully processed
- `TIMEOUT`: Request timed out
- `ERROR`: Handler raised an exception

## Integration Example

```python
import asyncio
from claude_pm.orchestration import SimpleMessageBus, Request, Response

async def math_agent(request: Request) -> Response:
    """Simple math operations agent."""
    op = request.data.get("operation")
    a = request.data.get("a", 0)
    b = request.data.get("b", 0)
    
    result = {
        "add": a + b,
        "multiply": a * b,
        "subtract": a - b
    }.get(op, 0)
    
    return Response(
        request_id=request.id,
        agent_id="math",
        data={"result": result}
    )

async def main():
    bus = SimpleMessageBus()
    bus.register_handler("math", math_agent)
    
    # Send multiple concurrent requests
    tasks = [
        bus.send_request("math", {"operation": "add", "a": 5, "b": 3}),
        bus.send_request("math", {"operation": "multiply", "a": 4, "b": 7}),
        bus.send_request("math", {"operation": "subtract", "a": 10, "b": 4})
    ]
    
    responses = await asyncio.gather(*tasks)
    for resp in responses:
        print(f"Result: {resp.data['result']}")
    
    await bus.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Design Principles

1. **No External Dependencies**: Uses only Python standard library
2. **Async-First**: Built on asyncio for scalability
3. **Simple API**: Easy to understand and use
4. **Error Resilient**: Graceful error handling and timeouts
5. **Thread-Safe**: Safe for concurrent operations

## Future Enhancements

- Message persistence for durability
- Priority-based message processing
- Message routing patterns (pub/sub, fanout)
- Performance metrics and monitoring
- Dead letter queue for failed messages