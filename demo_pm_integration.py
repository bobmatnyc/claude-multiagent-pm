#!/usr/bin/env python3
"""
PM Orchestrator Integration Demo
===============================

This demo script showcases the complete integration between PM orchestrator and
agent prompt builder, demonstrating automated Task Tool subprocess creation.

Features Demonstrated:
1. PM Orchestrator initialization with agent hierarchy
2. Automatic prompt generation from agent profiles
3. Task Tool subprocess creation workflow
4. Hierarchy precedence resolution
5. Memory collection integration
6. Real-time delegation tracking

Usage:
    python demo_pm_integration.py
    python demo_pm_integration.py --test-agent engineer
    python demo_pm_integration.py --show-shortcuts
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add claude_pm to path
sys.path.insert(0, str(Path(__file__).parent / "claude_pm"))

try:
    from claude_pm.services.pm_orchestrator import PMOrchestrator
    from claude_pm.utils.task_tool_helper import TaskToolHelper, quick_create_subprocess, create_pm_shortcuts
    from claude_pm.utils.task_tool_helper import validate_task_tool_integration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure claude_pm is in your Python path")
    sys.exit(1)


def demo_pm_orchestrator_initialization():
    """Demo PM orchestrator initialization and basic functionality."""
    print("🚀 PM Orchestrator Initialization Demo")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = PMOrchestrator()
    print(f"✅ PM Orchestrator initialized")
    print(f"   Working Directory: {orchestrator.working_directory}")
    
    # Test agent hierarchy validation
    validation = orchestrator.validate_agent_hierarchy()
    print(f"✅ Agent hierarchy valid: {validation.get('valid', False)}")
    
    # List available agents
    agents = orchestrator.list_available_agents()
    print(f"✅ Available agents:")
    for tier, agent_list in agents.items():
        print(f"   {tier.upper()}: {len(agent_list)} agents")
        for agent in agent_list[:3]:  # Show first 3
            print(f"     - {agent}")
        if len(agent_list) > 3:
            print(f"     ... and {len(agent_list) - 3} more")
    
    return orchestrator


def demo_agent_prompt_generation(orchestrator, agent_type="engineer"):
    """Demo automatic agent prompt generation."""
    print(f"\n🤖 Agent Prompt Generation Demo - {agent_type.title()}")
    print("=" * 60)
    
    # Get agent profile info
    profile_info = orchestrator.get_agent_profile_info(agent_type)
    if profile_info:
        print(f"✅ Agent Profile Found:")
        print(f"   Name: {profile_info['name']}")
        print(f"   Tier: {profile_info['tier']}")
        print(f"   Role: {profile_info['role']}")
        print(f"   Capabilities: {len(profile_info['capabilities'])} defined")
        print(f"   Authority Scope: {len(profile_info['authority_scope'])} items")
        print(f"   Profile Path: {profile_info['profile_path']}")
    else:
        print(f"❌ No profile found for {agent_type}")
        return None
    
    # Generate prompt
    prompt = orchestrator.generate_agent_prompt(
        agent_type=agent_type,
        task_description=f"Demonstrate {agent_type} agent integration with PM orchestrator",
        requirements=[
            "Show automated prompt generation",
            "Demonstrate hierarchy precedence",
            "Validate Task Tool compatibility",
            "Test memory collection integration"
        ],
        deliverables=[
            "Integration validation report",
            "Automated prompt demonstration",
            "Task Tool subprocess proof",
            "Memory collection verification"
        ],
        dependencies=[
            "PM orchestrator initialization",
            "Agent profile availability",
            "Task Tool helper integration"
        ],
        priority="medium",
        memory_categories=["architecture:design", "integration", "qa"],
        escalation_triggers=[
            "Integration failures",
            "Prompt generation errors",
            "Task Tool compatibility issues"
        ],
        integration_notes="This is a demonstration of automated PM orchestrator integration"
    )
    
    print(f"✅ Generated Prompt:")
    print(f"   Length: {len(prompt)} characters")
    print(f"   Lines: {len(prompt.split(chr(10)))} lines")
    print(f"   Contains Memory Collection: {'MEMORY COLLECTION REQUIRED' in prompt}")
    print(f"   Contains Temporal Context: {'TEMPORAL CONTEXT' in prompt}")
    print(f"   Contains Agent Profile: {'Agent Profile Integration' in prompt}")
    
    return prompt


def demo_task_tool_helper_integration():
    """Demo Task Tool helper integration."""
    print(f"\n🛠️ Task Tool Helper Integration Demo")
    print("=" * 60)
    
    # Initialize helper
    helper = TaskToolHelper()
    print(f"✅ Task Tool Helper initialized")
    
    # Validate integration
    validation = helper.validate_integration()
    print(f"✅ Integration validation: {validation.get('valid', False)}")
    
    # Create test subprocess
    result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Test Task Tool helper integration with PM orchestrator",
        requirements=["Validate automatic prompt generation", "Test subprocess tracking"],
        deliverables=["Integration test results", "Subprocess validation"],
        priority="high",
        memory_categories=["integration", "qa", "architecture:design"]
    )
    
    if result['success']:
        print(f"✅ Task Tool subprocess created:")
        print(f"   Subprocess ID: {result['subprocess_id']}")
        print(f"   Prompt Length: {len(result['prompt'])} characters")
        print(f"   Agent Type: {result['subprocess_info']['agent_type']}")
        print(f"   Priority: {result['subprocess_info']['priority']}")
        print(f"   Memory Categories: {result['subprocess_info']['memory_categories']}")
    else:
        print(f"❌ Subprocess creation failed: {result['error']}")
    
    # Show delegation status
    status = helper.get_delegation_status()
    print(f"✅ Delegation Status:")
    print(f"   Active Subprocesses: {status['active_subprocesses']}")
    print(f"   Total Subprocesses: {status['total_subprocesses']}")
    print(f"   Active Agents: {status['active_agents']}")
    
    return helper, result


def demo_pm_shortcuts():
    """Demo PM orchestrator shortcuts."""
    print(f"\n⚡ PM Shortcuts Demo")
    print("=" * 60)
    
    helper = TaskToolHelper()
    
    # Test different shortcuts
    shortcuts = ["push", "deploy", "test", "publish"]
    
    for shortcut in shortcuts:
        print(f"\n--- {shortcut.upper()} Shortcut ---")
        result = helper.create_shortcut_subprocess(shortcut)
        
        if result['success']:
            print(f"✅ {shortcut} subprocess created")
            print(f"   Agent: {result['subprocess_info']['agent_type']}")
            print(f"   Task: {result['subprocess_info']['task_description'][:50]}...")
            print(f"   Deliverables: {len(result['subprocess_info']['deliverables'])} items")
        else:
            print(f"❌ {shortcut} subprocess failed: {result['error']}")


def demo_hierarchy_precedence():
    """Demo agent hierarchy precedence resolution."""
    print(f"\n🏗️ Agent Hierarchy Precedence Demo")
    print("=" * 60)
    
    orchestrator = PMOrchestrator()
    
    # Test agents from different tiers
    test_agents = [
        ("engineer", "Test system tier fallback"),
        ("documenter", "Test system tier with profile"),
        ("pm", "Test project tier override"),
        ("architect", "Test project tier specialization")
    ]
    
    for agent_type, description in test_agents:
        print(f"\n--- {agent_type.title()} Agent Hierarchy ---")
        
        # Get profile info to show tier precedence
        profile_info = orchestrator.get_agent_profile_info(agent_type)
        if profile_info:
            print(f"✅ Loaded from {profile_info['tier']} tier")
            print(f"   Profile: {profile_info['name']}")
            print(f"   Path: {profile_info['profile_path']}")
            
            # Show hierarchy profiles available
            try:
                hierarchy_profiles = orchestrator.agent_builder.get_profile_hierarchy(agent_type)
                if hierarchy_profiles:
                    print(f"   Available in {len(hierarchy_profiles)} tiers:")
                    for profile in hierarchy_profiles:
                        print(f"     - {profile.tier.value}: {profile.path}")
            except Exception as e:
                print(f"   Hierarchy check failed: {e}")
        else:
            print(f"❌ No profile found for {agent_type}")


def demo_complete_workflow():
    """Demo complete PM orchestrator workflow."""
    print(f"\n🎯 Complete PM Orchestrator Workflow Demo")
    print("=" * 60)
    
    # Step 1: Initialize PM orchestrator
    print("Step 1: Initialize PM Orchestrator")
    orchestrator = demo_pm_orchestrator_initialization()
    
    # Step 2: Generate agent prompt
    print("\nStep 2: Generate Agent Prompt")
    prompt = demo_agent_prompt_generation(orchestrator, "engineer")
    
    # Step 3: Create Task Tool subprocess
    print("\nStep 3: Create Task Tool Subprocess")
    helper, result = demo_task_tool_helper_integration()
    
    # Step 4: Show generated prompt for copy/paste
    if result and result['success']:
        print("\nStep 4: Generated Prompt for Task Tool")
        print("=" * 60)
        print("Copy the following prompt and paste it into a Task Tool subprocess:")
        print("-" * 60)
        print(result['prompt'])
        print("-" * 60)
        print("\nUsage Instructions:")
        print("1. Copy the prompt above")
        print("2. Create a new Task Tool subprocess")
        print("3. Paste the prompt as the subprocess content")
        print("4. The subprocess will have full agent context and PM integration")
    
    # Step 5: Show delegation tracking
    print("\nStep 5: Delegation Tracking")
    delegation_summary = helper.generate_delegation_summary()
    print(delegation_summary)


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="PM Orchestrator Integration Demo")
    parser.add_argument("--test-agent", type=str, default="engineer", 
                       help="Agent type to test (default: engineer)")
    parser.add_argument("--show-shortcuts", action="store_true",
                       help="Show PM shortcuts demo")
    parser.add_argument("--show-hierarchy", action="store_true",
                       help="Show hierarchy precedence demo")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only run validation tests")
    parser.add_argument("--full-workflow", action="store_true",
                       help="Run complete workflow demo")
    
    args = parser.parse_args()
    
    print(f"🎭 PM Orchestrator Integration Demo")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {Path.cwd()}")
    print()
    
    try:
        if args.validate_only:
            # Run validation only
            validation = validate_task_tool_integration()
            print("🔍 Integration Validation Results:")
            print(json.dumps(validation, indent=2))
            
        elif args.show_shortcuts:
            # Show shortcuts demo
            demo_pm_shortcuts()
            
        elif args.show_hierarchy:
            # Show hierarchy precedence demo
            demo_hierarchy_precedence()
            
        elif args.full_workflow:
            # Run complete workflow
            demo_complete_workflow()
            
        else:
            # Run basic demo
            orchestrator = demo_pm_orchestrator_initialization()
            prompt = demo_agent_prompt_generation(orchestrator, args.test_agent)
            
            if prompt:
                print(f"\n📋 Generated Prompt Preview (first 200 chars):")
                print("-" * 60)
                print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
                print("-" * 60)
                
                print(f"\n💡 To use this prompt:")
                print("1. Copy the generated prompt")
                print("2. Create a Task Tool subprocess")
                print("3. Paste the prompt as subprocess content")
                print("4. The agent will have full context and PM integration")
        
        print(f"\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()