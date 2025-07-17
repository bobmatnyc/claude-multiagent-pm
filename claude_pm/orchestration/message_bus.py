"""
Simple Message Bus for async request/response communication.

This module provides a lightweight message bus implementation for coordinating
async communication between agents without external dependencies.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Awaitable
from enum import Enum

# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
logger = get_logger(__name__)


class MessageStatus(Enum):
    """Status of a message in the system."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Message:
    """Base message class with correlation ID and metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING


@dataclass
class Request(Message):
    """Request message for initiating async operations."""
    timeout: float = 30.0  # Default 30 second timeout
    reply_to: Optional[str] = None


@dataclass
class Response(Message):
    """Response message containing operation results."""
    request_id: str = ""
    success: bool = True
    error: Optional[str] = None
    
    def __post_init__(self):
        """Set correlation_id to match request_id if not set."""
        if not self.correlation_id and self.request_id:
            self.correlation_id = self.request_id


class SimpleMessageBus:
    """
    Simple async message bus for request/response communication.
    
    Features:
    - Async request/response pattern with correlation IDs
    - Configurable timeouts (default 30 seconds)
    - Multiple concurrent message handling
    - Error handling and timeout management
    - Thread-safe operations
    
    Example:
        ```python
        bus = SimpleMessageBus()
        
        # Register a handler
        async def handler(request: Request) -> Response:
            result = await process_request(request.data)
            return Response(
                request_id=request.id,
                agent_id="my_agent",
                data={"result": result}
            )
        
        bus.register_handler("my_agent", handler)
        
        # Send a request
        response = await bus.send_request(
            "my_agent",
            {"action": "process", "input": "data"}
        )
        ```
    """
    
    def __init__(self):
        """Initialize the message bus."""
        self._handlers: Dict[str, Callable[[Request], Awaitable[Response]]] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._active_tasks: set = set()
        self._shutdown = False
        
    def register_handler(
        self, 
        agent_id: str, 
        handler: Callable[[Request], Awaitable[Response]]
    ) -> None:
        """
        Register a handler for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            handler: Async function that processes requests and returns responses
            
        Raises:
            ValueError: If handler is already registered for agent_id
        """
        if agent_id in self._handlers:
            raise ValueError(f"Handler already registered for agent: {agent_id}")
            
        self._handlers[agent_id] = handler
        logger.info(f"Registered handler for agent: {agent_id}")
        
    def unregister_handler(self, agent_id: str) -> None:
        """
        Unregister a handler for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self._handlers:
            del self._handlers[agent_id]
            logger.info(f"Unregistered handler for agent: {agent_id}")
            
    async def send_request(
        self, 
        agent_id: str, 
        request_data: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Response:
        """
        Send an async request to an agent and wait for response.
        
        Args:
            agent_id: Target agent identifier
            request_data: Request payload data
            timeout: Optional timeout override (defaults to 30 seconds)
            
        Returns:
            Response from the agent
            
        Raises:
            RuntimeError: If message bus is shutdown
            ValueError: If no handler registered for agent_id
            asyncio.TimeoutError: If request times out
            Exception: If handler raises an exception
        """
        if self._shutdown:
            raise RuntimeError("Message bus is shutting down")
            
        if agent_id not in self._handlers:
            raise ValueError(f"No handler registered for agent: {agent_id}")
            
        # Create request
        request = Request(
            agent_id=agent_id,
            data=request_data,
            timeout=timeout or 30.0
        )
        
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request.id] = future
        
        # Create task to handle request
        task = asyncio.create_task(
            self._process_request(agent_id, request)
        )
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(
                future, 
                timeout=request.timeout
            )
            return response
            
        except asyncio.TimeoutError:
            # Clean up pending request
            self._pending_requests.pop(request.id, None)
            
            # Create timeout response
            timeout_response = Response(
                request_id=request.id,
                agent_id=agent_id,
                success=False,
                status=MessageStatus.TIMEOUT,
                error=f"Request timed out after {request.timeout} seconds"
            )
            
            logger.warning(
                f"Request {request.id} to agent {agent_id} timed out"
            )
            
            return timeout_response
            
        except Exception as e:
            # Clean up pending request
            self._pending_requests.pop(request.id, None)
            raise
            
    async def _process_request(self, agent_id: str, request: Request) -> None:
        """
        Process a request using the registered handler.
        
        Args:
            agent_id: Target agent identifier
            request: Request to process
        """
        future = self._pending_requests.get(request.id)
        if not future:
            return
            
        try:
            # Update request status
            request.status = MessageStatus.PROCESSING
            
            # Get handler and process request
            handler = self._handlers[agent_id]
            response = await handler(request)
            
            # Ensure response has correct request_id
            response.request_id = request.id
            response.status = MessageStatus.COMPLETED
            
            # Set future result
            if not future.done():
                future.set_result(response)
                
        except Exception as e:
            # Create error response
            error_response = Response(
                request_id=request.id,
                agent_id=agent_id,
                success=False,
                status=MessageStatus.ERROR,
                error=f"Handler error: {str(e)}"
            )
            
            logger.error(
                f"Error processing request {request.id} for agent {agent_id}: {e}",
                exc_info=True
            )
            
            # Set error response
            if not future.done():
                future.set_result(error_response)
                
        finally:
            # Clean up pending request
            self._pending_requests.pop(request.id, None)
            
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the message bus.
        
        Waits for all active tasks to complete.
        """
        logger.info("Shutting down message bus")
        self._shutdown = True
        
        # Cancel all pending requests
        for request_id, future in self._pending_requests.items():
            if not future.done():
                future.cancel()
                
        # Wait for active tasks to complete
        if self._active_tasks:
            await asyncio.gather(
                *self._active_tasks, 
                return_exceptions=True
            )
            
        self._handlers.clear()
        self._pending_requests.clear()
        logger.info("Message bus shutdown complete")
        
    @property
    def registered_agents(self) -> list[str]:
        """Get list of registered agent IDs."""
        return list(self._handlers.keys())
        
    @property
    def pending_request_count(self) -> int:
        """Get count of pending requests."""
        return len(self._pending_requests)
        
    @property
    def is_shutdown(self) -> bool:
        """Check if message bus is shutdown."""
        return self._shutdown