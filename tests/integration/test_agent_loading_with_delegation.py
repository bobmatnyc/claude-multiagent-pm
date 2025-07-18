#!/usr/bin/env python3
"""
Test agent prompt loading with actual delegation to trigger initialization
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator

async def test_with_orchestration_enabled():
    """Test agent prompt loading with orchestration enabled"""
    print("Testing with CLAUDE_PM_ORCHESTRATION=true")
    print("-" * 50)
    
    # Set environment variable
    os.environ['CLAUDE_PM_ORCHESTRATION'] = 'true'
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Trigger a delegation to force component initialization
    print("\nTriggering delegation to initialize components...")
    try:
        result, return_code = await orchestrator.delegate_to_agent(
            agent_type='research',
            task_description='Test task to trigger initialization'
        )
        print(f"Delegation result: success={result.get('success')}, mode={result.get('orchestration_metadata', {}).get('mode')}")
    except Exception as e:
        print(f"Delegation error: {e}")
    
    # Now test agent prompt loading
    print("\nTesting agent prompt loading after initialization...")
    test_agents = ['documentation', 'qa', 'research', 'engineer']
    
    for agent_type in test_agents:
        prompt = await orchestrator._get_agent_prompt(agent_type)
        if prompt:
            print(f"✅ {agent_type}: Loaded successfully ({len(prompt)} chars)")
        else:
            print(f"❌ {agent_type}: Failed to load")
    
    # Check if components are initialized
    print("\nComponent status:")
    print(f"  Message Bus: {'✅' if orchestrator._message_bus else '❌'}")
    print(f"  Context Manager: {'✅' if orchestrator._context_manager else '❌'}")
    print(f"  Agent Registry: {'✅' if orchestrator._agent_registry else '❌'}")
    print(f"  Prompt Cache: {'✅' if orchestrator._prompt_cache else '❌'}")

async def main():
    await test_with_orchestration_enabled()

if __name__ == "__main__":
    asyncio.run(main())