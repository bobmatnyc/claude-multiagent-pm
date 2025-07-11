#!/usr/bin/env python3
"""
Test Subprocess Profile Loading

Demonstrates how subprocesses can load their own agent profiles using the framework system.
This shows the practical bridge between Task Tool and framework components.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from claude_pm.services.framework_agent_loader import FrameworkAgentLoader

def demonstrate_subprocess_profile_loading():
    """Demonstrate how a subprocess would load its own profile"""
    print("🎭 Demonstrating Subprocess Profile Self-Loading")
    print("=" * 60)
    
    # Simulate different subprocess scenarios
    test_scenarios = [
        {
            "agent_type": "Engineer",
            "task": "Implement user authentication system",
            "context": "Need to add JWT-based login with secure password hashing"
        },
        {
            "agent_type": "Documenter", 
            "task": "Create API documentation",
            "context": "Document the new authentication endpoints and user management API"
        },
        {
            "agent_type": "QA",
            "task": "Design test suite",
            "context": "Comprehensive testing for authentication flow and edge cases"
        }
    ]
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    for scenario in test_scenarios:
        print(f"\n🔄 Subprocess: {scenario['agent_type']} Agent Starting")
        print("-" * 50)
        
        # Step 1: Agent loads its own profile
        print(f"📋 Loading {scenario['agent_type']} profile...")
        profile_instruction = loader.generate_profile_loading_instruction(scenario['agent_type'])
        
        # Step 2: Show how profile affects behavior
        print("✅ Profile loaded successfully!")
        print(f"📊 Profile length: {len(profile_instruction)} characters")
        
        # Step 3: Demonstrate enhanced context
        enhanced_task_context = f"""
{profile_instruction}

TEMPORAL CONTEXT: Today is 2025-07-11. Sprint deadline: 2025-07-18.

**Task**: {scenario['task']}
**Context**: {scenario['context']}

**Profile-Enhanced Behavior**: Operating with loaded capabilities, authority scope, and quality standards.
"""
        
        print(f"🎯 Enhanced task context: {len(enhanced_task_context)} characters")
        
        # Step 4: Show profile-specific behavior
        profile = loader.load_agent_profile(scenario['agent_type'])
        if profile:
            print(f"🔧 Authority areas: {', '.join(profile.get('authority_scope', [])[:3])}")
            print(f"🎨 Context focus: {profile.get('context_preferences', {}).get('focus', 'Not specified')[:80]}...")
            print(f"🤝 Integration partners: {len(profile.get('integration_patterns', {}))} agents")

def test_real_task_tool_integration():
    """Test how this would work with actual Task Tool subprocess"""
    print("\n\n🔗 Real Task Tool Integration Example")
    print("=" * 60)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    def create_enhanced_task_delegation(agent_type: str, task_description: str, additional_context: str = ""):
        """Create Task Tool delegation with profile loading"""
        profile_instruction = loader.generate_profile_loading_instruction(agent_type)
        
        delegation = f"""**{agent_type}**: {task_description}

{profile_instruction}

TEMPORAL CONTEXT: Today is 2025-07-11. Current sprint planning and deadline management.

**Task**: {task_description}
{additional_context}

**Instructions**: 
1. Your agent profile has been loaded automatically
2. Operate according to your defined capabilities and authority scope
3. Apply your context preferences when processing information
4. Follow your quality standards and escalation criteria
5. Coordinate with other agents as defined in your integration patterns

**Enhanced Context**: You are operating as a specialized {agent_type} agent with full profile awareness.
"""
        return delegation
    
    # Example Task Tool delegations
    examples = [
        ("Engineer", "Implement OAuth2 authentication", "**Requirements**: JWT tokens, secure password hashing, session management"),
        ("QA", "Validate authentication implementation", "**Scope**: Unit tests, integration tests, security testing"),
        ("Documenter", "Document authentication API", "**Audience**: Developer documentation and API reference")
    ]
    
    for agent_type, task, context in examples:
        print(f"\n📤 Task Tool → {agent_type} Subprocess:")
        print("-" * 30)
        
        delegation = create_enhanced_task_delegation(agent_type, task, context)
        
        # Show delegation preview
        lines = delegation.split('\n')
        print(f"📏 Delegation length: {len(delegation)} characters")
        print(f"📋 Lines: {len(lines)}")
        print("🔍 Preview (first 10 lines):")
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1:2d}: {line}")
        print("     ...")
        
        # Simulate subprocess receiving this
        print(f"✅ {agent_type} subprocess receives enhanced delegation with profile context")

def test_profile_hierarchy():
    """Test profile hierarchy and precedence"""
    print("\n\n🏗️ Testing Profile Hierarchy & Precedence")
    print("=" * 60)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    print("📁 Current directory structure:")
    if loader.framework_agents_dir:
        print(f"  Framework: {loader.framework_agents_dir}")
        for tier in ['system', 'trained', 'user']:
            tier_dir = loader.framework_agents_dir / tier
            if tier_dir.exists():
                profiles = list(tier_dir.glob("*.md"))
                print(f"    {tier}: {len(profiles)} profiles")
    
    if loader.project_agents_dir:
        print(f"  Project: {loader.project_agents_dir}")
        project_dir = loader.project_agents_dir / "project"
        if project_dir.exists():
            profiles = list(project_dir.glob("*.md"))
            print(f"    project: {len(profiles)} profiles")
        else:
            print(f"    project: (directory doesn't exist)")
    
    print("\n🔄 Testing precedence order:")
    test_agent = "Engineer"
    profile = loader.load_agent_profile(test_agent)
    if profile:
        source = profile.get('source_path', 'unknown')
        if 'framework' in source and 'system' in source:
            print(f"  ✅ {test_agent}: Loading from system tier (expected fallback)")
        elif 'project' in source:
            print(f"  ✅ {test_agent}: Loading from project tier (highest precedence)")
        else:
            print(f"  ✅ {test_agent}: Loading from {source}")
    else:
        print(f"  ❌ {test_agent}: No profile found")

if __name__ == "__main__":
    demonstrate_subprocess_profile_loading()
    test_real_task_tool_integration()
    test_profile_hierarchy()