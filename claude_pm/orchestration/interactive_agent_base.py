"""
Interactive Agent Base Class

This module provides the base class for agents that can request terminal control
for interactive sessions with users.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import uuid

# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
from claude_pm.orchestration.terminal_handoff import (
    HandoffRequest, HandoffResponse, HandoffPermission, 
    TerminalHandoffManager, TerminalProxy
)
from claude_pm.orchestration.message_bus import SimpleMessageBus, Request, Response

logger = get_logger(__name__)


@dataclass
class InteractiveContext:
    """Context for an interactive session."""
    session_id: str
    user_input_history: List[str]
    agent_output_history: List[str]
    session_data: Dict[str, Any]
    
    def add_interaction(self, user_input: str, agent_output: str):
        """Record an interaction in the session."""
        self.user_input_history.append(user_input)
        self.agent_output_history.append(agent_output)


class InteractiveAgentBase(ABC):
    """
    Base class for agents that can take control of the terminal.
    
    Subclasses should implement:
    - interactive_session: The main interactive loop
    - get_handoff_purpose: Describe why terminal control is needed
    - handle_request: Process non-interactive requests
    """
    
    def __init__(
        self, 
        agent_id: str,
        message_bus: SimpleMessageBus,
        handoff_manager: TerminalHandoffManager,
        default_permission: HandoffPermission = HandoffPermission.INTERACTIVE
    ):
        """
        Initialize the interactive agent.
        
        Args:
            agent_id: Unique identifier for this agent
            message_bus: Message bus for communication
            handoff_manager: Manager for terminal handoff
            default_permission: Default permission level for handoff requests
        """
        self.agent_id = agent_id
        self._message_bus = message_bus
        self._handoff_manager = handoff_manager
        self._terminal_proxy = TerminalProxy(handoff_manager)
        self._default_permission = default_permission
        self._current_session: Optional[InteractiveContext] = None
        
        # Register agent handler
        self._message_bus.register_handler(agent_id, self._handle_message)
        
        logger.info(f"Interactive agent initialized: {agent_id}")
    
    async def _handle_message(self, request: Request) -> Response:
        """
        Handle incoming messages from the message bus.
        
        Args:
            request: The incoming request
            
        Returns:
            Response to the request
        """
        try:
            # Check if this is an interactive request
            if request.data.get("interactive", False):
                return await self._handle_interactive_request(request)
            else:
                # Delegate to subclass implementation
                return await self.handle_request(request)
                
        except Exception as e:
            logger.error(f"Error handling message in {self.agent_id}: {e}", exc_info=True)
            return Response(
                request_id=request.id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_interactive_request(self, request: Request) -> Response:
        """
        Handle a request for an interactive session.
        
        Args:
            request: The request for interaction
            
        Returns:
            Response indicating session outcome
        """
        # Create handoff request
        handoff_req = HandoffRequest(
            requesting_agent=self.agent_id,
            permission_level=request.data.get("permission_level", self._default_permission),
            purpose=await self.get_handoff_purpose(request),
            estimated_duration=request.data.get("duration", 300.0),
            require_confirmation=request.data.get("require_confirmation", True),
            session_data=request.data.get("session_data", {})
        )
        
        # Request terminal handoff
        handoff_resp = await self._handoff_manager.request_handoff(handoff_req)
        
        if not handoff_resp.approved:
            return Response(
                request_id=request.id,
                agent_id=self.agent_id,
                success=False,
                error=f"Terminal handoff denied: {handoff_resp.reason}"
            )
        
        # Run interactive session
        try:
            session_id = handoff_resp.session_id
            async with self._handoff_manager.handoff_context(session_id):
                # Initialize session context
                self._current_session = InteractiveContext(
                    session_id=session_id,
                    user_input_history=[],
                    agent_output_history=[],
                    session_data=handoff_req.session_data
                )
                
                # Run the interactive session
                result = await self.interactive_session(self._current_session)
                
                return Response(
                    request_id=request.id,
                    agent_id=self.agent_id,
                    success=True,
                    data={
                        "session_id": session_id,
                        "result": result,
                        "interactions": len(self._current_session.user_input_history)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in interactive session: {e}", exc_info=True)
            return Response(
                request_id=request.id,
                agent_id=self.agent_id,
                success=False,
                error=f"Interactive session error: {str(e)}"
            )
        finally:
            self._current_session = None
    
    def write(self, content: str, error: bool = False) -> None:
        """
        Write content to the terminal during an interactive session.
        
        Args:
            content: Content to write
            error: Whether to write to stderr
            
        Raises:
            RuntimeError: If not in an interactive session
        """
        if not self._current_session:
            raise RuntimeError("Not in an interactive session")
        
        self._terminal_proxy.write_output(content, error=error)
    
    def read(self, prompt: str = "") -> str:
        """
        Read input from the terminal during an interactive session.
        
        Args:
            prompt: Optional prompt to display
            
        Returns:
            User input
            
        Raises:
            RuntimeError: If not in an interactive session
        """
        if not self._current_session:
            raise RuntimeError("Not in an interactive session")
        
        user_input = self._terminal_proxy.read_input(prompt)
        return user_input
    
    def clear_screen(self) -> None:
        """
        Clear the terminal screen during an interactive session.
        
        Raises:
            RuntimeError: If not in an interactive session
            PermissionError: If insufficient permissions
        """
        if not self._current_session:
            raise RuntimeError("Not in an interactive session")
        
        self._terminal_proxy.clear_screen()
    
    @abstractmethod
    async def interactive_session(self, context: InteractiveContext) -> Any:
        """
        Run the interactive session with the user.
        
        This method should implement the main interactive loop,
        using the write() and read() methods for I/O.
        
        Args:
            context: The session context
            
        Returns:
            Any result data from the session
        """
        pass
    
    @abstractmethod
    async def get_handoff_purpose(self, request: Request) -> str:
        """
        Get a description of why terminal control is needed.
        
        Args:
            request: The triggering request
            
        Returns:
            Human-readable description of the purpose
        """
        pass
    
    @abstractmethod
    async def handle_request(self, request: Request) -> Response:
        """
        Handle non-interactive requests.
        
        Args:
            request: The incoming request
            
        Returns:
            Response to the request
        """
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup resources."""
        self._message_bus.unregister_handler(self.agent_id)
        logger.info(f"Interactive agent shutdown: {self.agent_id}")


class SimpleInteractiveAgent(InteractiveAgentBase):
    """
    Simple example implementation of an interactive agent.
    
    This agent demonstrates basic interactive capabilities like
    asking questions and processing responses.
    """
    
    async def interactive_session(self, context: InteractiveContext) -> Dict[str, Any]:
        """Run a simple Q&A interactive session."""
        self.write("=== Interactive Session Started ===\n")
        self.write(f"Agent: {self.agent_id}\n")
        self.write("Type 'exit' to end the session.\n\n")
        
        responses = []
        
        while True:
            # Ask a question
            user_input = self.read("You: ")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                self.write("Agent: Goodbye!\n")
                break
            
            # Process input (simple echo for demo)
            response = f"I heard you say: '{user_input}'"
            self.write(f"Agent: {response}\n")
            
            # Record interaction
            context.add_interaction(user_input, response)
            responses.append({"input": user_input, "response": response})
        
        self.write("\n=== Session Ended ===\n")
        
        return {
            "total_interactions": len(responses),
            "responses": responses
        }
    
    async def get_handoff_purpose(self, request: Request) -> str:
        """Describe the purpose of this handoff."""
        return f"Interactive Q&A session requested by {self.agent_id}"
    
    async def handle_request(self, request: Request) -> Response:
        """Handle non-interactive requests."""
        # Simple echo for non-interactive requests
        return Response(
            request_id=request.id,
            agent_id=self.agent_id,
            success=True,
            data={
                "echo": request.data,
                "message": "Non-interactive request processed"
            }
        )