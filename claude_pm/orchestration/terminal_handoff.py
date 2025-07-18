"""
Terminal Handoff Module for Interactive Agent Control

This module provides the infrastructure for agents to take control of the terminal
for interactive sessions while maintaining security and control boundaries.
"""

import asyncio
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable, Any, Dict, Awaitable
from enum import Enum
import signal
from contextlib import asynccontextmanager

# Use project standard logging configuration
from claude_pm.core.logging_config import get_logger
from claude_pm.orchestration.message_bus import Message, MessageStatus

logger = get_logger(__name__)


class HandoffState(Enum):
    """State of a terminal handoff session."""
    REQUESTED = "requested"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class HandoffPermission(Enum):
    """Permission levels for terminal access."""
    READ_ONLY = "read_only"      # Can only read terminal output
    INTERACTIVE = "interactive"   # Can read input and write output
    FULL_CONTROL = "full_control" # Can manipulate terminal settings


@dataclass
class HandoffRequest(Message):
    """Request for terminal handoff from an agent."""
    requesting_agent: str = ""
    permission_level: HandoffPermission = HandoffPermission.INTERACTIVE
    purpose: str = ""
    estimated_duration: float = 300.0  # 5 minutes default
    require_confirmation: bool = True
    session_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoffResponse(Message):
    """Response to a handoff request."""
    request_id: str = ""
    approved: bool = False
    session_id: Optional[str] = None
    reason: Optional[str] = None
    actual_duration: Optional[float] = None


@dataclass
class HandoffSession:
    """Active terminal handoff session."""
    id: str
    agent_id: str
    permission_level: HandoffPermission
    state: HandoffState
    started_at: datetime
    ended_at: Optional[datetime] = None
    suspend_count: int = 0
    session_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds."""
        end_time = self.ended_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.state == HandoffState.ACTIVE


class TerminalHandoffManager:
    """
    Manages terminal handoff sessions for interactive agents.
    
    Features:
    - Secure handoff request/approval process
    - Session state management
    - Emergency interrupt handling (Ctrl+C)
    - Automatic timeout management
    - Session suspension/resumption
    """
    
    def __init__(self, confirm_callback: Optional[Callable[[HandoffRequest], Awaitable[bool]]] = None):
        """
        Initialize the terminal handoff manager.
        
        Args:
            confirm_callback: Optional async callback for confirming handoff requests.
                             If not provided, uses default console confirmation.
        """
        self._active_session: Optional[HandoffSession] = None
        self._session_history: list[HandoffSession] = []
        self._confirm_callback = confirm_callback or self._default_confirm
        self._original_handlers: Dict[int, Any] = {}
        self._emergency_exit_enabled = True
        
    async def request_handoff(self, request: HandoffRequest) -> HandoffResponse:
        """
        Process a terminal handoff request from an agent.
        
        Args:
            request: The handoff request details
            
        Returns:
            HandoffResponse indicating approval or rejection
        """
        logger.info(f"Terminal handoff requested by agent: {request.requesting_agent}")
        
        # Check if there's already an active session
        if self._active_session and self._active_session.is_active:
            return HandoffResponse(
                request_id=request.id,
                approved=False,
                reason="Another session is already active"
            )
        
        # Confirm handoff if required
        approved = True
        if request.require_confirmation:
            approved = await self._confirm_callback(request)
        
        if not approved:
            logger.info(f"Terminal handoff denied for agent: {request.requesting_agent}")
            return HandoffResponse(
                request_id=request.id,
                approved=False,
                reason="User denied handoff request"
            )
        
        # Create and activate session
        session = HandoffSession(
            id=request.id,
            agent_id=request.requesting_agent,
            permission_level=request.permission_level,
            state=HandoffState.ACTIVE,
            started_at=datetime.now(timezone.utc),
            session_data=request.session_data
        )
        
        self._active_session = session
        self._setup_emergency_exit()
        
        logger.info(f"Terminal handoff approved for agent: {request.requesting_agent}")
        
        return HandoffResponse(
            request_id=request.id,
            approved=True,
            session_id=session.id
        )
    
    async def end_handoff(self, session_id: str, reason: Optional[str] = None) -> bool:
        """
        End an active handoff session.
        
        Args:
            session_id: ID of the session to end
            reason: Optional reason for ending the session
            
        Returns:
            bool: True if session was ended, False if not found
        """
        if not self._active_session or self._active_session.id != session_id:
            return False
        
        self._active_session.state = HandoffState.COMPLETED
        self._active_session.ended_at = datetime.now(timezone.utc)
        
        # Move to history
        self._session_history.append(self._active_session)
        
        # Restore original handlers
        self._restore_handlers()
        
        logger.info(
            f"Terminal handoff ended for agent: {self._active_session.agent_id} "
            f"(duration: {self._active_session.duration:.1f}s)"
        )
        
        self._active_session = None
        return True
    
    async def suspend_handoff(self, session_id: str) -> bool:
        """
        Temporarily suspend an active handoff session.
        
        Args:
            session_id: ID of the session to suspend
            
        Returns:
            bool: True if session was suspended, False if not found
        """
        if not self._active_session or self._active_session.id != session_id:
            return False
        
        if self._active_session.state != HandoffState.ACTIVE:
            return False
        
        self._active_session.state = HandoffState.SUSPENDED
        self._active_session.suspend_count += 1
        
        logger.info(f"Terminal handoff suspended for agent: {self._active_session.agent_id}")
        return True
    
    async def resume_handoff(self, session_id: str) -> bool:
        """
        Resume a suspended handoff session.
        
        Args:
            session_id: ID of the session to resume
            
        Returns:
            bool: True if session was resumed, False if not found
        """
        if not self._active_session or self._active_session.id != session_id:
            return False
        
        if self._active_session.state != HandoffState.SUSPENDED:
            return False
        
        self._active_session.state = HandoffState.ACTIVE
        
        logger.info(f"Terminal handoff resumed for agent: {self._active_session.agent_id}")
        return True
    
    def get_active_session(self) -> Optional[HandoffSession]:
        """Get the currently active handoff session."""
        return self._active_session
    
    def get_session_history(self, agent_id: Optional[str] = None) -> list[HandoffSession]:
        """
        Get handoff session history.
        
        Args:
            agent_id: Optional filter by agent ID
            
        Returns:
            List of historical sessions
        """
        if agent_id:
            return [s for s in self._session_history if s.agent_id == agent_id]
        return self._session_history.copy()
    
    def _setup_emergency_exit(self):
        """Setup emergency exit handler (Ctrl+C)."""
        if not self._emergency_exit_enabled:
            return
            
        def emergency_handler(signum, frame):
            if self._active_session:
                logger.warning(
                    f"Emergency exit triggered during handoff session: "
                    f"{self._active_session.agent_id}"
                )
                self._active_session.state = HandoffState.CANCELLED
                self._active_session.ended_at = datetime.now(timezone.utc)
                self._session_history.append(self._active_session)
                self._active_session = None
                self._restore_handlers()
            # Re-raise to allow normal interrupt handling
            raise KeyboardInterrupt()
        
        # Store original handler
        self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, emergency_handler)
    
    def _restore_handlers(self):
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)
        self._original_handlers.clear()
    
    async def _default_confirm(self, request: HandoffRequest) -> bool:
        """
        Default confirmation callback using console input.
        
        Args:
            request: The handoff request to confirm
            
        Returns:
            bool: True if approved, False otherwise
        """
        print(f"\n{'='*50}")
        print(f"Terminal Handoff Request")
        print(f"{'='*50}")
        print(f"Agent: {request.requesting_agent}")
        print(f"Purpose: {request.purpose}")
        print(f"Permission: {request.permission_level.value}")
        print(f"Est. Duration: {request.estimated_duration}s")
        print(f"{'='*50}")
        
        response = input("Allow terminal handoff? (y/n): ").strip().lower()
        return response == 'y'
    
    @asynccontextmanager
    async def handoff_context(self, session_id: str):
        """
        Context manager for terminal handoff sessions.
        
        Args:
            session_id: The session ID to manage
            
        Yields:
            The active HandoffSession
        """
        session = self._active_session
        if not session or session.id != session_id:
            raise ValueError(f"No active session with ID: {session_id}")
        
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in handoff session: {e}")
            session.state = HandoffState.ERROR
            raise
        finally:
            if session.state == HandoffState.ACTIVE:
                await self.end_handoff(session_id)


class TerminalProxy:
    """
    Proxy for terminal I/O during handoff sessions.
    
    Provides controlled access to stdin/stdout/stderr based on
    the permission level of the active session.
    """
    
    def __init__(self, manager: TerminalHandoffManager):
        """
        Initialize the terminal proxy.
        
        Args:
            manager: The handoff manager to check permissions
        """
        self._manager = manager
        self._original_stdin = sys.stdin
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
    
    def read_input(self, prompt: str = "") -> str:
        """
        Read input from terminal if permitted.
        
        Args:
            prompt: Optional prompt to display
            
        Returns:
            User input string
            
        Raises:
            PermissionError: If no active session or insufficient permissions
        """
        session = self._manager.get_active_session()
        if not session:
            raise PermissionError("No active handoff session")
        
        if session.permission_level == HandoffPermission.READ_ONLY:
            raise PermissionError("Session does not have input permissions")
        
        if prompt:
            self._original_stdout.write(prompt)
            self._original_stdout.flush()
        
        return self._original_stdin.readline().rstrip('\n')
    
    def write_output(self, content: str, error: bool = False) -> None:
        """
        Write output to terminal if permitted.
        
        Args:
            content: Content to write
            error: Whether to write to stderr instead of stdout
            
        Raises:
            PermissionError: If no active session
        """
        session = self._manager.get_active_session()
        if not session:
            raise PermissionError("No active handoff session")
        
        target = self._original_stderr if error else self._original_stdout
        target.write(content)
        target.flush()
    
    def clear_screen(self) -> None:
        """
        Clear the terminal screen if permitted.
        
        Raises:
            PermissionError: If insufficient permissions
        """
        session = self._manager.get_active_session()
        if not session:
            raise PermissionError("No active handoff session")
        
        if session.permission_level != HandoffPermission.FULL_CONTROL:
            raise PermissionError("Session does not have full control permissions")
        
        # Clear screen command based on OS
        os.system('cls' if os.name == 'nt' else 'clear')