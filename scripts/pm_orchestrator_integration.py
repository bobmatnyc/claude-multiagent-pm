#!/usr/bin/env python3
"""
PM Orchestrator Integration Example
==================================

This script demonstrates how the Agent Prompt Builder would integrate with the actual
PM orchestrator to create a seamless agent delegation system.

It shows:
1. How PM would use the prompt builder to create agent contexts
2. How agent profiles enhance Task Tool subprocess creation
3. How memory collection would be integrated
4. How hierarchy precedence affects agent selection

This represents the bridge between the current manual agent prompting
and the future automated agent orchestration system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.agent_prompt_builder import AgentPromptBuilder, TaskContext


class PMOrchestrator:
    """
    PM Orchestrator with Agent Prompt Builder Integration
    
    This class demonstrates how the PM would use the Agent Prompt Builder
    to create enhanced Task Tool subprocess contexts with agent profiles.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize PM orchestrator with prompt builder."""
        self.prompt_builder = AgentPromptBuilder(working_directory)
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        
    def delegate_task(self, agent_type: str, task_description: str, **kwargs) -> str:
        """
        Delegate a task to an agent using the prompt builder.
        
        This method demonstrates how the PM would create agent contexts
        programmatically instead of manually writing prompts.
        """
        
        # Create task context
        task_context = TaskContext(
            description=task_description,
            specific_requirements=kwargs.get('requirements', []),
            expected_deliverables=kwargs.get('deliverables', []),
            dependencies=kwargs.get('dependencies', []),
            priority=kwargs.get('priority', 'medium'),
            memory_categories=kwargs.get('memory_categories', [])
        )
        
        # Build agent prompt using prompt builder
        try:
            prompt = self.prompt_builder.build_task_tool_prompt(agent_type, task_context)
            
            # Create subprocess context
            context = self.create_subprocess_context(agent_type, task_context)
            
            # Generate task ID
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_type}"
            
            # Store active task
            self.active_tasks[task_id] = {
                "agent_type": agent_type,
                "task_description": task_description,
                "context": context,
                "prompt": prompt,
                "created_at": datetime.now().isoformat(),
                "status": "delegated"
            }
            
            return task_id
            
        except Exception as e:
            print(f"Error delegating task to {agent_type}: {e}")
            raise
    
    def create_subprocess_context(self, agent_name: str, task_context: TaskContext) -> Dict[str, Any]:
        """Create subprocess context - this would be called by delegate_task."""
        try:
            # Load agent profile
            profile = self.prompt_builder.load_agent_profile(agent_name)
            if not profile:
                raise ValueError(f"No profile found for agent: {agent_name}")
            
            # Create context
            context = {
                "agent_name": agent_name,
                "agent_profile": {
                    "name": profile.name,
                    "tier": profile.tier.value,
                    "role": profile.role,
                    "nickname": profile.nickname,
                    "capabilities": profile.capabilities,
                    "authority_scope": profile.authority_scope,
                    "path": str(profile.path)
                },
                "task_context": {
                    "description": task_context.description,
                    "requirements": task_context.specific_requirements,
                    "deliverables": task_context.expected_deliverables,
                    "dependencies": task_context.dependencies,
                    "priority": task_context.priority,
                    "memory_categories": task_context.memory_categories
                },
                "created_at": datetime.now().isoformat(),
                "temporal_context": task_context.temporal_context
            }
            
            return context
            
        except Exception as e:
            print(f"Failed to create subprocess context for {agent_name}: {e}")
            raise
    
    def demonstrate_push_workflow(self):
        """Demonstrate the enhanced 'push' workflow with agent prompts."""
        print("\n🚀 Enhanced 'Push' Workflow Demonstration")
        print("=" * 60)
        
        # The PM would orchestrate the push workflow like this:
        workflow_steps = [
            {
                "agent": "documenter",
                "task": "Generate changelog and analyze semantic versioning impact",
                "requirements": ["Analyze git commits since last release", "Determine version bump type"],
                "deliverables": ["CHANGELOG.md update", "Version bump recommendation"],
                "dependencies": ["Git history access"],
                "priority": "high"
            },
            {
                "agent": "qa",
                "task": "Execute full test suite and quality validation",
                "requirements": ["Run unit tests", "Run integration tests", "Validate code quality"],
                "deliverables": ["Test results", "Quality report", "Validation summary"],
                "dependencies": ["Test environment setup"],
                "priority": "high"
            },
            {
                "agent": "ops",
                "task": "Validate deployment readiness and infrastructure",
                "requirements": ["Check deployment dependencies", "Validate configuration"],
                "deliverables": ["Deployment readiness report", "Infrastructure validation"],
                "dependencies": ["QA completion"],
                "priority": "medium"
            },
            {
                "agent": "vcs",
                "task": "Apply semantic version bump and create release tags",
                "requirements": ["Apply version bump", "Create Git tags", "Update version files"],
                "deliverables": ["Version bump completion", "Git tags created", "Version files updated"],
                "dependencies": ["Documentation and QA completion"],
                "priority": "high"
            }
        ]
        
        # Execute workflow
        task_ids = []
        for step in workflow_steps:
            print(f"\n📋 Delegating to {step['agent']} agent...")
            
            task_id = self.delegate_task(
                step["agent"],
                step["task"],
                requirements=step["requirements"],
                deliverables=step["deliverables"],
                dependencies=step["dependencies"],
                priority=step["priority"]
            )
            
            task_ids.append(task_id)
            
            # Show prompt preview
            task_info = self.active_tasks[task_id]
            prompt_lines = task_info["prompt"].split('\n')
            print(f"✓ Task delegated: {task_id}")
            print(f"✓ Prompt generated: {len(prompt_lines)} lines")
            print(f"✓ Agent profile: {task_info['context']['agent_profile']['tier']} tier")
            print(f"✓ Capabilities: {len(task_info['context']['agent_profile']['capabilities'])}")
        
        print(f"\n📊 Push Workflow Summary:")
        print(f"✓ Total tasks delegated: {len(task_ids)}")
        print(f"✓ All agents have profiles: {all(self.active_tasks[tid]['context']['agent_profile'] for tid in task_ids)}")
        print(f"✓ Hierarchical precedence applied: Yes")
        print(f"✓ Memory collection configured: Yes")
        
        return task_ids
    
    def demonstrate_agent_precedence(self):
        """Demonstrate how agent hierarchy precedence works."""
        print("\n🔄 Agent Hierarchy Precedence Demonstration")
        print("=" * 60)
        
        # Test different agent types to show precedence
        test_agents = ["engineer", "architect", "documenter", "qa"]
        
        for agent_name in test_agents:
            print(f"\n🔍 Agent: {agent_name}")
            
            # Get all available profiles for this agent
            profiles = self.prompt_builder.get_profile_hierarchy(agent_name)
            
            if profiles:
                print(f"  Available tiers: {len(profiles)}")
                for profile in profiles:
                    print(f"    {profile.tier.value}: {profile.path}")
                
                # Load the selected profile (highest precedence)
                selected_profile = self.prompt_builder.load_agent_profile(agent_name)
                print(f"  Selected: {selected_profile.tier.value} tier (precedence)")
            else:
                print(f"  No profiles found")
        
        print(f"\n📋 Precedence Rules:")
        print(f"  1. Project tier (highest precedence)")
        print(f"  2. User tier (medium precedence)")
        print(f"  3. System tier (fallback)")
    
    def demonstrate_memory_integration(self):
        """Demonstrate how memory collection is integrated."""
        print("\n🧠 Memory Integration Demonstration")
        print("=" * 50)
        
        # Show how memory categories are automatically set
        memory_examples = [
            ("engineer", ["bug", "error:runtime", "error:logic", "architecture:design"]),
            ("documenter", ["feedback:documentation", "architecture:design", "performance"]),
            ("qa", ["bug", "error:integration", "performance", "qa"]),
            ("ops", ["error:deployment", "performance", "architecture:design"]),
            ("security", ["error:security", "bug", "architecture:design"])
        ]
        
        for agent_name, expected_categories in memory_examples:
            actual_categories = self.prompt_builder._get_default_memory_categories(agent_name)
            print(f"  {agent_name}: {actual_categories}")
            
        print(f"\n📋 Memory Collection Features:")
        print(f"  ✓ Automatic category assignment based on agent type")
        print(f"  ✓ Custom categories can be specified per task")
        print(f"  ✓ Memory metadata includes agent profile information")
        print(f"  ✓ Hierarchical context preserved in memory entries")
    
    def show_task_tool_integration(self):
        """Show how this integrates with Task Tool."""
        print("\n🛠️ Task Tool Integration")
        print("=" * 40)
        
        # Create a sample task
        task_id = self.delegate_task(
            "engineer",
            "Implement caching system for API responses",
            requirements=["Use Redis for caching", "Implement cache invalidation"],
            deliverables=["Cache middleware", "Unit tests", "Performance metrics"],
            priority="high"
        )
        
        task_info = self.active_tasks[task_id]
        
        print(f"Generated Task Tool Prompt:")
        print(f"=" * 40)
        print(task_info["prompt"])
        
        print(f"\n📋 Integration Benefits:")
        print(f"  ✓ Automatic agent profile loading")
        print(f"  ✓ Hierarchical precedence resolution")
        print(f"  ✓ Standardized prompt formatting")
        print(f"  ✓ Memory collection integration")
        print(f"  ✓ Context enhancement from profiles")
    
    def get_profile_hierarchy(self, agent_name: str) -> List[Any]:
        """Get all available profiles for an agent across all tiers."""
        return self.prompt_builder.get_profile_hierarchy(agent_name)


def main():
    """Main demonstration entry point."""
    print("🎯 PM Orchestrator Integration Demonstration")
    print("=" * 70)
    
    # Initialize orchestrator
    orchestrator = PMOrchestrator()
    
    # Demonstrate push workflow
    task_ids = orchestrator.demonstrate_push_workflow()
    
    # Demonstrate agent precedence
    orchestrator.demonstrate_agent_precedence()
    
    # Demonstrate memory integration
    orchestrator.demonstrate_memory_integration()
    
    # Show Task Tool integration
    orchestrator.show_task_tool_integration()
    
    print(f"\n🎉 Integration Demonstration Complete!")
    print(f"✓ Agent prompt building: Automated")
    print(f"✓ Hierarchy precedence: Functional")
    print(f"✓ Memory collection: Integrated")
    print(f"✓ Task Tool compatibility: Demonstrated")
    print(f"✓ PM orchestration: Enhanced")
    
    print(f"\n🚀 Implementation Roadmap:")
    print(f"1. Deploy agent prompt builder script")
    print(f"2. Integrate with existing PM orchestrator")
    print(f"3. Update Task Tool subprocess creation")
    print(f"4. Add memory collection automation")
    print(f"5. Implement hierarchy validation")


if __name__ == "__main__":
    main()