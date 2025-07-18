#!/usr/bin/env python3
"""
Agent Management Demo
=====================

Comprehensive demonstration of the agent management service capabilities.
Shows CRUD operations, versioning, section updates, and integration.
"""

import asyncio
from pathlib import Path
from datetime import datetime

from claude_pm.services.agent_management_service import AgentManager
from claude_pm.services.agent_versioning import AgentVersionManager
from claude_pm.agents.agent_loader_integration import (
    get_enhanced_loader,
    get_agent_full_definition,
    get_agent_version,
    check_agent_capability,
    should_select_agent
)
from claude_pm.models.agent_definition import AgentSection


async def main():
    """Run comprehensive agent management demo."""
    print("=" * 60)
    print("Agent Management Service Demo")
    print("=" * 60)
    print()
    
    # Initialize services
    manager = AgentManager()
    version_mgr = AgentVersionManager()
    enhanced_loader = get_enhanced_loader()
    
    # Demo 1: List all agents with versions
    print("1. Current Agent Inventory:")
    print("-" * 40)
    agents = manager.list_agents()
    for name, info in sorted(agents.items()):
        print(f"   {name:<25} v{info['version']:<10} [{info['type']}] @ {info['location']}")
    print()
    
    # Demo 2: Read and analyze an agent
    print("2. Analyzing Documentation Agent:")
    print("-" * 40)
    doc_agent = get_agent_full_definition("documentation")
    if doc_agent:
        print(f"   Title: {doc_agent.title}")
        print(f"   Version: {doc_agent.metadata.version}")
        print(f"   Model Preference: {doc_agent.metadata.model_preference}")
        print(f"   Specializations: {', '.join(doc_agent.metadata.specializations) or 'None'}")
        print(f"   Capabilities: {len(doc_agent.capabilities)}")
        print(f"   Workflows: {len(doc_agent.workflows)}")
        print(f"   Authority:")
        print(f"     - Write Access: {len(doc_agent.authority.exclusive_write_access)} paths")
        print(f"     - Forbidden Ops: {len(doc_agent.authority.forbidden_operations)}")
        
        # Show some capabilities
        print("\n   Key Capabilities:")
        for i, cap in enumerate(doc_agent.capabilities[:3], 1):
            print(f"     {i}. {cap[:80]}...")
    print()
    
    # Demo 3: Test agent selection logic
    print("3. Agent Selection Logic Test:")
    print("-" * 40)
    test_tasks = [
        "Generate a changelog from recent commits",
        "Fix a bug in the authentication module",
        "Create API documentation for the new endpoints",
        "Optimize database query performance",
        "Review code for security vulnerabilities"
    ]
    
    agents_to_test = ["documentation", "engineer", "data_engineer", "security"]
    
    for task in test_tasks:
        print(f"\n   Task: '{task}'")
        recommendations = []
        
        for agent in agents_to_test:
            result = should_select_agent(agent, task)
            if result["should_select"]:
                recommendations.append({
                    "agent": agent,
                    "matches": result["positive_matches"],
                    "specializations": result["specializations"]
                })
        
        if recommendations:
            print("   Recommended agents:")
            for rec in recommendations:
                print(f"     - {rec['agent']}: {rec['matches'][0] if rec['matches'] else 'General match'}")
        else:
            print("   No specific agent recommendation")
    print()
    
    # Demo 4: Check agent capabilities
    print("4. Capability Checking:")
    print("-" * 40)
    capability_tests = [
        ("documentation", "changelog"),
        ("engineer", "code implementation"),
        ("qa", "testing"),
        ("security", "vulnerability"),
        ("ops", "deployment")
    ]
    
    for agent, capability in capability_tests:
        has_capability = check_agent_capability(agent, capability)
        status = "✓" if has_capability else "✗"
        print(f"   {status} {agent:<20} has '{capability}' capability")
    print()
    
    # Demo 5: Version management
    print("5. Version Management Demo:")
    print("-" * 40)
    
    # Show version operations
    test_version = "2.0.0"
    print(f"   Starting version: {test_version}")
    print(f"   After patch update: {version_mgr.increment_serial(test_version)}")
    print(f"   After minor update: {version_mgr.increment_minor(test_version)}")
    print(f"   After major update: {version_mgr.increment_major(test_version)}")
    
    # Show version comparison
    versions = ["1.9.9", "2.0.0", "2.0.1", "2.1.0", "3.0.0"]
    print("\n   Version ordering:")
    for i in range(len(versions) - 1):
        v1, v2 = versions[i], versions[i+1]
        comp = version_mgr.compare_versions(v1, v2)
        symbol = "<" if comp == -1 else "=" if comp == 0 else ">"
        print(f"     {v1} {symbol} {v2}")
    print()
    
    # Demo 6: Section update simulation
    print("6. Section Update Simulation:")
    print("-" * 40)
    print("   (Demonstrating section update without actual modification)")
    
    # Read QA agent
    qa_agent = manager.read_agent("qa-agent")
    if qa_agent:
        print(f"   Current QA Agent version: {qa_agent.metadata.version}")
        print(f"   Current capabilities count: {len(qa_agent.capabilities)}")
        
        # Simulate what would happen with an update
        new_capabilities = qa_agent.capabilities + [
            "**AI-Powered Test Generation**: Use AI to generate comprehensive test cases",
            "**Visual Regression Testing**: Detect UI changes through screenshot comparison"
        ]
        
        print(f"\n   Simulated update would:")
        print(f"     - Add 2 new capabilities (total: {len(new_capabilities)})")
        print(f"     - Increment version to: {version_mgr.increment_serial(qa_agent.metadata.version)}")
        print(f"     - Update last_modified timestamp")
    print()
    
    # Demo 7: Agent metadata extraction
    print("7. Agent Metadata Summary:")
    print("-" * 40)
    
    core_agents = ["documentation", "ticketing", "version_control", "qa", 
                   "research", "ops", "security", "engineer", "data_engineer"]
    
    print("   Agent Model Preferences:")
    for agent_name in core_agents:
        metadata = enhanced_loader.get_agent_metadata(agent_name)
        if metadata:
            print(f"     {agent_name:<20} → {metadata['model_preference']}")
    print()
    
    # Demo 8: Integration with existing loader
    print("8. Backward Compatibility Check:")
    print("-" * 40)
    
    # Test that old loader still works
    from claude_pm.agents.agent_loader import get_documentation_agent_prompt
    
    try:
        prompt = get_documentation_agent_prompt()
        print(f"   ✓ Legacy loader works: Got {len(prompt)} chars of prompt")
        print(f"   ✓ Prompt starts with: {prompt[:50]}...")
    except Exception as e:
        print(f"   ✗ Legacy loader error: {e}")
    print()
    
    print("=" * 60)
    print("✅ Agent Management Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())