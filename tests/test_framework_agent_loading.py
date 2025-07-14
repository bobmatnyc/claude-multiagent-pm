#!/usr/bin/env python3
"""
Test Framework Agent Loading System

Tests the new framework .claude-pm directory structure and agent loading logic.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from claude_pm.services.framework_agent_loader import FrameworkAgentLoader

def test_framework_agent_loading():
    """Test the framework agent loading system"""
    print("🧪 Testing Framework Agent Loading System")
    print("=" * 60)
    
    # Initialize loader
    loader = FrameworkAgentLoader()
    
    # Test framework directory detection
    framework_claude_md = project_root / "framework" / "CLAUDE.md"
    if framework_claude_md.exists():
        print(f"✅ Framework CLAUDE.md found at: {framework_claude_md}")
        loader.initialize(str(framework_claude_md))
    else:
        print(f"❌ Framework CLAUDE.md not found at: {framework_claude_md}")
        loader.initialize()
    
    print(f"📁 Framework agents dir: {loader.framework_agents_dir}")
    print(f"📁 Project agents dir: {loader.project_agents_dir}")
    print()
    
    # Test available agents
    print("📋 Available Agents by Tier:")
    available = loader.get_available_agents()
    for tier, agents in available.items():
        if agents:
            print(f"  {tier}: {', '.join(agents)}")
        else:
            print(f"  {tier}: (none)")
    print()
    
    # Test agent profile loading
    test_agents = ['Engineer', 'Documenter', 'QA', 'VCS']
    
    for agent_type in test_agents:
        print(f"🔍 Testing {agent_type} profile loading:")
        
        profile = loader.load_agent_profile(agent_type)
        if profile:
            print(f"  ✅ Profile loaded from: {profile.get('source_path', 'unknown')}")
            print(f"  📝 Role: {profile.get('role', 'Not specified')[:100]}...")
            print(f"  🎯 Capabilities: {len(profile.get('capabilities', []))} defined")
            print(f"  🔧 Authority areas: {len(profile.get('authority_scope', []))} defined")
            print(f"  🤝 Integration patterns: {len(profile.get('integration_patterns', {}))} defined")
        else:
            print(f"  ❌ No profile found for {agent_type}")
        print()
    
    # Test profile loading instruction generation
    print("📜 Testing Profile Loading Instructions:")
    print("-" * 40)
    
    engineer_instruction = loader.generate_profile_loading_instruction('Engineer')
    print("Engineer Instruction Preview:")
    print(engineer_instruction[:500] + "..." if len(engineer_instruction) > 500 else engineer_instruction)
    print()
    
    # Test with non-existent agent
    missing_instruction = loader.generate_profile_loading_instruction('NonExistentAgent')
    print("Non-existent Agent Instruction:")
    print(missing_instruction)
    print()
    
    print("✅ Framework Agent Loading Tests Complete!")

def test_subprocess_profile_integration():
    """Test integration with Task Tool subprocess pattern"""
    print("\n🔗 Testing Subprocess Profile Integration")
    print("=" * 60)
    
    loader = FrameworkAgentLoader()
    loader.initialize()
    
    # Simulate Task Tool delegation with profile loading
    def simulate_enhanced_delegation(agent_type: str, task_description: str):
        profile_instruction = loader.generate_profile_loading_instruction(agent_type)
        
        enhanced_context = f"""
{profile_instruction}

TEMPORAL CONTEXT: Today is 2025-07-11. Current sprint deadline: 2025-07-18.

**Task**: {task_description}

**Enhanced Context**: Your profile has been loaded and you should operate according to your defined capabilities, authority scope, and quality standards.
"""
        return enhanced_context
    
    # Test enhanced delegations
    test_cases = [
        ("Engineer", "Implement user authentication system with JWT tokens"),
        ("Documenter", "Create API documentation for the new authentication endpoints"),
        ("QA", "Design comprehensive test suite for authentication flow"),
        ("VCS", "Create feature branch and manage authentication implementation workflow")
    ]
    
    for agent_type, task in test_cases:
        print(f"🎯 Enhanced {agent_type} Delegation:")
        enhanced = simulate_enhanced_delegation(agent_type, task)
        
        # Show preview
        lines = enhanced.split('\n')
        preview_lines = lines[:15]  # First 15 lines
        print('\n'.join(preview_lines))
        
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
        
        print(f"📏 Total delegation length: {len(enhanced)} characters")
        print("-" * 40)
    
    print("✅ Subprocess Profile Integration Tests Complete!")

if __name__ == "__main__":
    test_framework_agent_loading()
    test_subprocess_profile_integration()