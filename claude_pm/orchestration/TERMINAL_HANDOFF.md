# Terminal Handoff Mechanism

The terminal handoff mechanism allows agents to request control of the terminal for interactive sessions with users. This enables agents to create rich, interactive experiences while maintaining security and control boundaries.

## Core Components

### 1. TerminalHandoffManager
Manages terminal handoff sessions with the following features:
- Secure handoff request/approval process
- Session state management
- Emergency interrupt handling (Ctrl+C)
- Automatic timeout management
- Session suspension/resumption

### 2. InteractiveAgentBase
Base class for agents that can take control of the terminal. Agents must implement:
- `interactive_session()`: The main interactive loop
- `get_handoff_purpose()`: Describe why terminal control is needed
- `handle_request()`: Process non-interactive requests

### 3. TerminalProxy
Provides controlled access to stdin/stdout/stderr based on permission levels:
- **READ_ONLY**: Can only read terminal output
- **INTERACTIVE**: Can read input and write output (default)
- **FULL_CONTROL**: Can manipulate terminal settings

## Usage Example

```python
from claude_pm.orchestration import (
    SimpleMessageBus,
    TerminalHandoffManager,
    InteractiveAgentBase,
    InteractiveContext
)

class MyInteractiveAgent(InteractiveAgentBase):
    async def interactive_session(self, context: InteractiveContext) -> dict:
        # Use self.write() and self.read() for I/O
        self.write("Welcome to interactive mode!\n")
        user_input = self.read("Enter command: ")
        
        # Process interaction
        context.add_interaction(user_input, "Response")
        
        return {"status": "completed"}
    
    async def get_handoff_purpose(self, request) -> str:
        return "Interactive configuration wizard"
    
    async def handle_request(self, request):
        # Handle non-interactive requests
        pass

# Initialize components
bus = SimpleMessageBus()
handoff_manager = TerminalHandoffManager()
agent = MyInteractiveAgent("my_agent", bus, handoff_manager)

# Request interactive session
response = await bus.send_request(
    "my_agent", 
    {"interactive": True}
)
```

## Security Features

1. **Confirmation Required**: By default, users must approve handoff requests
2. **Emergency Exit**: Ctrl+C immediately cancels the session
3. **Automatic Timeout**: Sessions have configurable timeouts
4. **Permission Levels**: Control what agents can do with the terminal
5. **Session History**: Track all handoff sessions for audit

## Integration with Local Orchestration

The terminal handoff mechanism integrates seamlessly with the local orchestration system:

1. Agents can request terminal control through the message bus
2. The orchestrator can coordinate multiple interactive sessions
3. Context is preserved across handoffs
4. Safety mechanisms prevent conflicts between agents

## Example Agents

See `examples/terminal_handoff_example.py` for complete examples:
- **DebuggerAgent**: Interactive debugging with breakpoints
- **TaskPlannerAgent**: Interactive task planning wizard

## Best Practices

1. Always provide clear purpose descriptions
2. Keep interactive sessions focused and time-bounded
3. Handle interrupts gracefully
4. Preserve context for session history
5. Use appropriate permission levels
6. Test emergency exit handling