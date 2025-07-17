"""
Example usage of SimpleMessageBus for agent communication.

This example demonstrates:
- Basic request/response pattern
- Multi-agent communication
- Error handling
- Timeout management
"""

import asyncio
import logging
from claude_pm.orchestration import (
    SimpleMessageBus,
    Request,
    Response,
    MessageStatus
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def calculator_agent(request: Request) -> Response:
    """
    Simple calculator agent that performs basic math operations.
    """
    operation = request.data.get("operation")
    a = request.data.get("a", 0)
    b = request.data.get("b", 0)
    
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
        return Response(
            request_id=request.id,
            agent_id="calculator",
            data={"result": result, "operation": operation}
        )
        
    except Exception as e:
        return Response(
            request_id=request.id,
            agent_id="calculator",
            success=False,
            error=str(e)
        )


async def formatter_agent(request: Request) -> Response:
    """
    Formatter agent that formats calculation results.
    """
    result = request.data.get("result")
    operation = request.data.get("operation")
    
    if result is None:
        return Response(
            request_id=request.id,
            agent_id="formatter",
            success=False,
            error="No result provided"
        )
        
    formatted = f"The {operation} result is: {result}"
    
    return Response(
        request_id=request.id,
        agent_id="formatter",
        data={"formatted": formatted}
    )


async def orchestrator_agent(request: Request, bus: SimpleMessageBus) -> Response:
    """
    Orchestrator agent that coordinates calculator and formatter.
    """
    # First, calculate
    calc_response = await bus.send_request(
        "calculator",
        {
            "operation": request.data.get("operation"),
            "a": request.data.get("a"),
            "b": request.data.get("b")
        }
    )
    
    if not calc_response.success:
        return Response(
            request_id=request.id,
            agent_id="orchestrator",
            success=False,
            error=f"Calculation failed: {calc_response.error}"
        )
        
    # Then format the result
    format_response = await bus.send_request(
        "formatter",
        {
            "result": calc_response.data["result"],
            "operation": calc_response.data["operation"]
        }
    )
    
    if not format_response.success:
        return Response(
            request_id=request.id,
            agent_id="orchestrator",
            success=False,
            error=f"Formatting failed: {format_response.error}"
        )
        
    return Response(
        request_id=request.id,
        agent_id="orchestrator",
        data={
            "result": calc_response.data["result"],
            "formatted": format_response.data["formatted"]
        }
    )


async def slow_agent(request: Request) -> Response:
    """
    Slow agent for demonstrating timeouts.
    """
    delay = request.data.get("delay", 5)
    await asyncio.sleep(delay)
    
    return Response(
        request_id=request.id,
        agent_id="slow",
        data={"message": f"Completed after {delay} seconds"}
    )


async def main():
    """Run example demonstrations."""
    # Create message bus
    bus = SimpleMessageBus()
    
    # Register agents
    bus.register_handler("calculator", calculator_agent)
    bus.register_handler("formatter", formatter_agent)
    bus.register_handler("slow", slow_agent)
    
    # Register orchestrator with bus access
    async def orchestrator_wrapper(request: Request) -> Response:
        return await orchestrator_agent(request, bus)
    
    bus.register_handler("orchestrator", orchestrator_wrapper)
    
    print("=== SimpleMessageBus Example ===\n")
    
    # Example 1: Direct calculation
    print("1. Direct calculation:")
    response = await bus.send_request(
        "calculator",
        {"operation": "multiply", "a": 6, "b": 7}
    )
    print(f"   Result: {response.data['result']}")
    print(f"   Success: {response.success}\n")
    
    # Example 2: Error handling
    print("2. Error handling (division by zero):")
    response = await bus.send_request(
        "calculator",
        {"operation": "divide", "a": 10, "b": 0}
    )
    print(f"   Success: {response.success}")
    print(f"   Error: {response.error}\n")
    
    # Example 3: Multi-agent orchestration
    print("3. Multi-agent orchestration:")
    response = await bus.send_request(
        "orchestrator",
        {"operation": "add", "a": 15, "b": 25}
    )
    print(f"   Result: {response.data['result']}")
    print(f"   Formatted: {response.data['formatted']}\n")
    
    # Example 4: Timeout handling
    print("4. Timeout handling:")
    response = await bus.send_request(
        "slow",
        {"delay": 2},
        timeout=1.0  # Will timeout
    )
    print(f"   Success: {response.success}")
    print(f"   Status: {response.status}")
    print(f"   Error: {response.error}\n")
    
    # Example 5: Concurrent requests
    print("5. Concurrent requests:")
    tasks = [
        bus.send_request("calculator", {"operation": "add", "a": i, "b": i})
        for i in range(5)
    ]
    responses = await asyncio.gather(*tasks)
    for i, resp in enumerate(responses):
        print(f"   Request {i}: {resp.data['result']}")
    
    # Show bus status
    print(f"\nMessage Bus Status:")
    print(f"   Registered agents: {bus.registered_agents}")
    print(f"   Pending requests: {bus.pending_request_count}")
    
    # Shutdown
    await bus.shutdown()
    print("\nMessage bus shut down successfully.")


if __name__ == "__main__":
    asyncio.run(main())