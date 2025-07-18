#!/usr/bin/env python3
"""
Simple synchronous terminal handoff demo.
"""

import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.orchestration.terminal_handoff import HandoffPermission


class SimpleTerminalHandoff:
    """Simple synchronous terminal handoff for local orchestration."""
    
    def __init__(self):
        self.active_session = None
        self.original_functions = {}
    
    def request_handoff(self, agent_name: str, reason: str) -> bool:
        """Request terminal handoff."""
        print(f"\n🔄 {agent_name} is requesting terminal control")
        print(f"   Reason: {reason}")
        response = input("   Allow? (y/n): ").strip().lower()
        
        if response == 'y':
            self.active_session = {
                'agent': agent_name,
                'reason': reason
            }
            return True
        return False
    
    def return_control(self):
        """Return control to the orchestrator."""
        if self.active_session:
            print(f"\n✅ {self.active_session['agent']} returning control")
            self.active_session = None


class InteractiveAgent:
    """Simple interactive agent that can take over the terminal."""
    
    def __init__(self, name: str, handoff_manager: SimpleTerminalHandoff):
        self.name = name
        self.handoff = handoff_manager
    
    def execute_interactive_task(self, task: str):
        """Execute a task that needs user interaction."""
        # Request terminal control
        if not self.handoff.request_handoff(self.name, f"Need input for: {task}"):
            print(f"❌ {self.name}: Unable to get terminal access, using defaults")
            return {"result": "completed_with_defaults"}
        
        # Now we have terminal control
        print(f"\n{'='*50}")
        print(f"🤖 {self.name} Interactive Session")
        print(f"{'='*50}\n")
        
        results = {}
        
        if task == "debug_code":
            print("I found an issue in your code that needs clarification.")
            print("\nThe variable 'config' is undefined. How should I handle this?")
            print("1) Use default configuration")
            print("2) Load from config file")
            print("3) Ask user for config values")
            
            choice = input("\nYour choice (1-3): ").strip()
            results['config_choice'] = choice
            
            if choice == '3':
                api_key = input("Enter API key: ").strip()
                results['api_key'] = api_key[:4] + "..." if api_key else "none"
            
            print(f"\n✅ Got it! I'll implement option {choice}")
            
        elif task == "plan_feature":
            print("Let's plan this feature together!")
            feature_name = input("\nWhat's the feature name? ").strip()
            
            print(f"\nGreat! Planning '{feature_name}'")
            print("\nWhat components do we need? (enter blank line to finish)")
            
            components = []
            while True:
                comp = input(f"Component {len(components)+1}: ").strip()
                if not comp:
                    break
                components.append(comp)
            
            results['feature'] = feature_name
            results['components'] = components
            
            print(f"\n✅ Feature plan created with {len(components)} components")
        
        # Return control
        self.handoff.return_control()
        return results


def demo_local_orchestration():
    """Demonstrate local orchestration with terminal handoff."""
    print("Claude PM Framework - Local Orchestration with Terminal Handoff")
    print("="*60)
    
    # Create handoff manager
    handoff = SimpleTerminalHandoff()
    
    # Create agents
    debugger = InteractiveAgent("Debugger Agent", handoff)
    planner = InteractiveAgent("Planning Agent", handoff)
    
    print("\n📋 Available agents:")
    print("   - Debugger Agent: Can interactively debug code issues")
    print("   - Planning Agent: Can help plan features interactively")
    
    while True:
        print("\n" + "-"*60)
        print("What would you like to do?")
        print("1) Debug code issue")
        print("2) Plan a new feature")
        print("3) Exit")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == '1':
            # PM delegates to debugger agent
            print("\n🎯 PM: Delegating to Debugger Agent...")
            result = debugger.execute_interactive_task("debug_code")
            print(f"\n📊 PM: Received result: {result}")
            
        elif choice == '2':
            # PM delegates to planner agent
            print("\n🎯 PM: Delegating to Planning Agent...")
            result = planner.execute_interactive_task("plan_feature")
            print(f"\n📊 PM: Received result: {result}")
            
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    # In real usage, this would be integrated with the orchestrator
    # For now, we'll simulate the PM role
    demo_local_orchestration()