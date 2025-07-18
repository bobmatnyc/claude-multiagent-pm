#!/usr/bin/env python3
"""
Simple test to verify agent prompt loading functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.agent_registry import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache

async def test_agent_discovery():
    """Test basic agent discovery"""
    print("Testing Agent Discovery...")
    print("-" * 50)
    
    # Initialize registry
    cache = SharedPromptCache.get_instance()
    registry = AgentRegistry(cache_service=cache)
    
    # Discover agents
    agents = await registry.discover_agents(force_refresh=True)
    
    print(f"Found {len(agents)} agents:")
    for name, metadata in agents.items():
        print(f"  - {name}: {metadata.type} ({metadata.path})")
    
    print("\n" + "-" * 50)
    return agents

async def test_agent_prompt_extraction():
    """Test agent prompt extraction from Python files"""
    print("\nTesting Agent Prompt Extraction...")
    print("-" * 50)
    
    # Import agent modules to check prompt constants
    agent_modules = {
        'documentation': 'claude_pm.agents.documentation_agent',
        'qa': 'claude_pm.agents.qa_agent',
        'research': 'claude_pm.agents.research_agent',
        'engineer': 'claude_pm.agents.engineer_agent',
    }
    
    for agent_name, module_path in agent_modules.items():
        try:
            module = __import__(module_path, fromlist=['*'])
            
            # Look for prompt constant
            prompt_var_names = [
                f'{agent_name.upper()}_AGENT_PROMPT',
                f'{agent_name.upper()}_PROMPT',
                'AGENT_PROMPT',
                'PROMPT'
            ]
            
            prompt_found = False
            for var_name in prompt_var_names:
                if hasattr(module, var_name):
                    prompt = getattr(module, var_name)
                    print(f"\n{agent_name}: Found prompt variable '{var_name}'")
                    print(f"  Preview: {prompt[:100]}...")
                    prompt_found = True
                    break
            
            if not prompt_found:
                print(f"\n{agent_name}: No prompt constant found")
                # List available attributes
                attrs = [attr for attr in dir(module) if not attr.startswith('_')]
                print(f"  Available attributes: {', '.join(attrs[:5])}...")
                
        except Exception as e:
            print(f"\n{agent_name}: Error loading module - {str(e)}")
    
    print("\n" + "-" * 50)

async def test_orchestrator_agent_loading():
    """Test how the orchestrator loads agent prompts"""
    print("\nTesting Orchestrator Agent Loading...")
    print("-" * 50)
    
    from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
    
    orchestrator = BackwardsCompatibleOrchestrator()
    
    # Test loading prompts for various agents
    test_agents = ['documentation', 'qa', 'research', 'engineer']
    
    for agent_type in test_agents:
        print(f"\nTesting {agent_type} agent:")
        
        # Test the internal prompt loading method
        prompt = await orchestrator._get_agent_prompt(agent_type)
        
        if prompt:
            print(f"  ✅ Prompt loaded successfully")
            print(f"  Length: {len(prompt)} characters")
            print(f"  Preview: {prompt[:100]}...")
        else:
            print(f"  ❌ Failed to load prompt")
            
            # Try to understand why
            if orchestrator._agent_registry:
                agent_meta = await orchestrator._agent_registry.get_agent(agent_type)
                if agent_meta:
                    print(f"  Agent found in registry: {agent_meta.name}")
                    print(f"  Path: {agent_meta.path}")
                else:
                    print(f"  Agent not found in registry")
            else:
                print(f"  No agent registry initialized")
    
    print("\n" + "-" * 50)

async def main():
    """Run all tests"""
    print("="*60)
    print(" Simple Agent Loading Test")
    print("="*60)
    
    # Run tests
    agents = await test_agent_discovery()
    await test_agent_prompt_extraction()
    await test_orchestrator_agent_loading()
    
    print("\n" + "="*60)
    print(" Test Complete")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())