#!/usr/bin/env python3
"""
Simple test of the terminal handoff functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.orchestration.terminal_handoff import (
    TerminalHandoffManager,
    HandoffRequest,
    HandoffPermission
)
from claude_pm.orchestration.interactive_agent_base import SimpleInteractiveAgent
from claude_pm.orchestration.message_bus import SimpleMessageBus


async def test_terminal_handoff():
    """Test the terminal handoff functionality."""
    print("=== Terminal Handoff Test ===\n")
    
    # Create components
    message_bus = SimpleMessageBus()
    handoff_manager = TerminalHandoffManager()  # Uses default confirmation
    
    # Create and register an interactive agent
    agent = SimpleInteractiveAgent(
        agent_id="helper",
        message_bus=message_bus,
        name="Helper Agent",
        capabilities=["assist", "debug", "explain"]
    )
    
    # Register the agent with the message bus
    await message_bus.register_agent("helper", agent.handle_request)
    
    print("📋 Terminal handoff system initialized")
    print("🤖 Helper Agent ready\n")
    
    # Create a handoff request
    request = HandoffRequest(
        agent_id="helper",
        reason="User requested interactive assistance",
        expected_duration=300,  # 5 minutes
        permission_level=HandoffPermission.INTERACTIVE,
        context={
            "task": "Help user understand terminal handoff",
            "mode": "educational"
        }
    )
    
    print("🔄 Helper Agent requesting terminal control...")
    print("   Reason: User requested interactive assistance")
    print("   Permission: INTERACTIVE (can read input and write output)")
    print("   Duration: Up to 5 minutes\n")
    
    # Request handoff
    result = await handoff_manager.request_handoff(request)
    
    if result.approved:
        print(f"✅ Handoff approved! Session ID: {result.session_id[:8]}...\n")
        
        # Simulate the agent's interactive session work
        # In a real scenario, the agent would use the message bus
        # Here we'll call the agent's interactive method directly
        await agent.begin_interactive_session({
            "session_id": result.session_id,
            "task": "demonstrate",
            "context": request.context
        })
        
    else:
        print(f"❌ Handoff denied: {result.denial_reason}")
    
    print("\n✨ Test complete!")


async def test_message_bus_integration():
    """Test full message bus integration."""
    print("\n=== Message Bus Integration Test ===\n")
    
    # Create components
    message_bus = SimpleMessageBus()
    handoff_manager = TerminalHandoffManager()  # Uses default confirmation
    
    # Create a task planner agent
    from examples.terminal_handoff_example import TaskPlannerAgent
    planner = TaskPlannerAgent("planner", message_bus)
    
    print("🎯 Testing Task Planner Agent with message bus...\n")
    
    # Send a request to the planner
    from claude_pm.orchestration.message_bus import Request
    request = Request(
        agent_id="planner",
        content="Help me plan a new feature",
        context={
            "project": "Claude PM Framework",
            "interactive": True
        }
    )
    
    # This will trigger the handoff flow through the message bus
    response = await message_bus.route_message("planner", request)
    
    print(f"\n📨 Final response: {response.content}")
    print(f"✅ Success: {response.success}")


if __name__ == "__main__":
    print("\nClaude PM Framework - Terminal Handoff Demo")
    print("=" * 50)
    
    # Run the basic test
    asyncio.run(test_terminal_handoff())
    
    # Uncomment to test message bus integration
    # asyncio.run(test_message_bus_integration())