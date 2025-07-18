"""
Terminal Handoff Example

This example demonstrates how an agent can request terminal control
for an interactive session with the user.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude_pm.orchestration.message_bus import SimpleMessageBus, Request, Response
from claude_pm.orchestration.terminal_handoff import (
    TerminalHandoffManager, HandoffPermission
)
from claude_pm.orchestration.interactive_agent_base import InteractiveAgentBase, InteractiveContext


class DebuggerAgent(InteractiveAgentBase):
    """
    Example agent that provides an interactive debugging session.
    """
    
    def __init__(self, message_bus, handoff_manager):
        super().__init__(
            agent_id="debugger",
            message_bus=message_bus,
            handoff_manager=handoff_manager,
            default_permission=HandoffPermission.INTERACTIVE
        )
        self.breakpoints = set()
        self.variables = {}
    
    async def interactive_session(self, context: InteractiveContext) -> dict:
        """Run an interactive debugging session."""
        self.write("\n" + "="*60 + "\n")
        self.write("🐛 Interactive Debugger Session\n")
        self.write("="*60 + "\n\n")
        
        self.write("Available commands:\n")
        self.write("  - break <line>  : Set a breakpoint\n")
        self.write("  - clear <line>  : Clear a breakpoint\n")
        self.write("  - list          : List all breakpoints\n")
        self.write("  - vars          : Show variables\n")
        self.write("  - set <var> <val>: Set a variable\n")
        self.write("  - continue      : Continue execution\n")
        self.write("  - exit          : End session\n\n")
        
        command_count = 0
        
        while True:
            try:
                user_input = self.read("(debugger) ")
                
                if not user_input.strip():
                    continue
                
                parts = user_input.strip().split()
                cmd = parts[0].lower()
                
                if cmd in ['exit', 'quit']:
                    self.write("Ending debug session...\n")
                    break
                
                elif cmd == 'break' and len(parts) > 1:
                    line = int(parts[1])
                    self.breakpoints.add(line)
                    self.write(f"Breakpoint set at line {line}\n")
                
                elif cmd == 'clear' and len(parts) > 1:
                    line = int(parts[1])
                    self.breakpoints.discard(line)
                    self.write(f"Breakpoint cleared at line {line}\n")
                
                elif cmd == 'list':
                    if self.breakpoints:
                        self.write("Active breakpoints:\n")
                        for bp in sorted(self.breakpoints):
                            self.write(f"  - Line {bp}\n")
                    else:
                        self.write("No active breakpoints\n")
                
                elif cmd == 'vars':
                    if self.variables:
                        self.write("Variables:\n")
                        for var, val in self.variables.items():
                            self.write(f"  {var} = {val}\n")
                    else:
                        self.write("No variables set\n")
                
                elif cmd == 'set' and len(parts) > 2:
                    var_name = parts[1]
                    var_value = ' '.join(parts[2:])
                    self.variables[var_name] = var_value
                    self.write(f"Set {var_name} = {var_value}\n")
                
                elif cmd == 'continue':
                    self.write("Continuing execution...\n")
                    # Simulate some execution
                    await asyncio.sleep(1)
                    self.write("Execution paused at next breakpoint\n")
                
                else:
                    self.write(f"Unknown command: {cmd}\n")
                
                command_count += 1
                context.add_interaction(user_input, f"Processed command: {cmd}")
                
            except ValueError as e:
                self.write(f"Error: Invalid argument - {e}\n")
            except Exception as e:
                self.write(f"Error: {e}\n")
        
        self.write("\n" + "="*60 + "\n")
        self.write("Debug session completed.\n")
        
        return {
            "commands_executed": command_count,
            "breakpoints_set": len(self.breakpoints),
            "variables_defined": len(self.variables)
        }
    
    async def get_handoff_purpose(self, request: Request) -> str:
        """Describe why we need terminal control."""
        return "Interactive debugging session to help diagnose code issues"
    
    async def handle_request(self, request: Request) -> Response:
        """Handle non-interactive debug requests."""
        
        action = request.data.get("action")
        
        if action == "get_breakpoints":
            return Response(
                request_id=request.id,
                agent_id=self.agent_id,
                success=True,
                data={"breakpoints": list(self.breakpoints)}
            )
        
        return Response(
            request_id=request.id,
            agent_id=self.agent_id,
            success=False,
            error=f"Unknown action: {action}"
        )


class TaskPlannerAgent(InteractiveAgentBase):
    """
    Example agent that helps plan tasks interactively.
    """
    
    def __init__(self, message_bus, handoff_manager):
        super().__init__(
            agent_id="task_planner",
            message_bus=message_bus,
            handoff_manager=handoff_manager,
            default_permission=HandoffPermission.INTERACTIVE
        )
    
    async def interactive_session(self, context: InteractiveContext) -> dict:
        """Run an interactive task planning session."""
        self.write("\n" + "="*60 + "\n")
        self.write("📋 Interactive Task Planning Session\n")
        self.write("="*60 + "\n\n")
        
        self.write("Let's plan your tasks together!\n\n")
        
        tasks = []
        
        # Collect project information
        project_name = self.read("What's the project name? ")
        context.add_interaction("project_name", project_name)
        
        self.write(f"\nGreat! Let's plan tasks for '{project_name}'.\n")
        self.write("Enter tasks one by one (empty line to finish):\n\n")
        
        while True:
            task = self.read(f"Task {len(tasks) + 1}: ")
            
            if not task.strip():
                break
            
            priority = self.read("  Priority (high/medium/low): ").lower()
            if priority not in ['high', 'medium', 'low']:
                priority = 'medium'
            
            estimate = self.read("  Time estimate (hours): ")
            try:
                hours = float(estimate)
            except:
                hours = 1.0
            
            tasks.append({
                "description": task,
                "priority": priority,
                "estimate_hours": hours
            })
            
            self.write("\n")
        
        # Summary
        self.write("\n" + "-"*40 + "\n")
        self.write("Task Summary:\n")
        self.write("-"*40 + "\n")
        
        total_hours = 0
        for i, task in enumerate(tasks, 1):
            self.write(f"{i}. {task['description']}\n")
            self.write(f"   Priority: {task['priority']}, Estimate: {task['estimate_hours']}h\n")
            total_hours += task['estimate_hours']
        
        self.write(f"\nTotal estimated time: {total_hours} hours\n")
        
        # Ask for confirmation
        confirm = self.read("\nSave this task plan? (y/n): ")
        saved = confirm.lower() == 'y'
        
        if saved:
            self.write("Task plan saved successfully!\n")
        else:
            self.write("Task plan discarded.\n")
        
        return {
            "project": project_name,
            "tasks": tasks,
            "total_hours": total_hours,
            "saved": saved
        }
    
    async def get_handoff_purpose(self, request: Request) -> str:
        """Describe why we need terminal control."""
        return "Interactive task planning session to organize project work"
    
    async def handle_request(self, request: Request) -> Response:
        """Handle non-interactive planning requests."""
        
        return Response(
            request_id=request.id,
            agent_id=self.agent_id,
            success=True,
            data={"message": "Use interactive mode for task planning"}
        )


async def main():
    """Run the terminal handoff example."""
    print("Terminal Handoff Example")
    print("========================\n")
    
    # Create message bus and handoff manager
    message_bus = SimpleMessageBus()
    handoff_manager = TerminalHandoffManager()
    
    # Create agents
    debugger = DebuggerAgent(message_bus, handoff_manager)
    planner = TaskPlannerAgent(message_bus, handoff_manager)
    
    print("Available agents:")
    print("  - debugger: Interactive debugging session")
    print("  - task_planner: Interactive task planning\n")
    
    try:
        while True:
            print("\nOptions:")
            print("1. Start debugging session")
            print("2. Start task planning session")
            print("3. Check debugger breakpoints")
            print("4. Exit")
            
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice == '1':
                # Request interactive debugging session
                response = await message_bus.send_request(
                    "debugger",
                    {
                        "interactive": True,
                        "session_type": "debug"
                    }
                )
                print(f"\nSession result: {response.data}\n")
                
            elif choice == '2':
                # Request interactive task planning
                response = await message_bus.send_request(
                    "task_planner",
                    {
                        "interactive": True,
                        "session_type": "planning"
                    }
                )
                print(f"\nSession result: {response.data}\n")
                
            elif choice == '3':
                # Non-interactive request
                response = await message_bus.send_request(
                    "debugger",
                    {"action": "get_breakpoints"}
                )
                print(f"\nBreakpoints: {response.data.get('breakpoints', [])}\n")
                
            elif choice == '4':
                print("Exiting...")
                break
                
            else:
                print("Invalid option. Please try again.")
                
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        # Cleanup
        await debugger.shutdown()
        await planner.shutdown()
        await message_bus.shutdown()
        print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())