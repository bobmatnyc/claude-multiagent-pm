"""
Ticketing Agent - Specialized Issue Management and Ticket Operations

This agent specializes in:
1. All ticket operations (read/write) across multiple platforms
2. Support for internal AI tracking tools and external systems (Jira, etc.)
3. Abstract ticket management from PM
4. Collaborate hand-in-hand with PM for ticket needs
5. Handle ticket lifecycle management across different platforms
6. Core agent functionality for issue management
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess

from ..core.base_agent import BaseAgent
from ..core.config import Config


class TicketPlatform(Enum):
    """Supported ticketing platforms."""
    AI_TRACKDOWN = "ai_trackdown"
    JIRA = "jira"
    GITHUB = "github"
    ASANA = "asana"
    TRELLO = "trello"
    LINEAR = "linear"


class TicketStatus(Enum):
    """Universal ticket status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    CANCELLED = "cancelled"


class TicketPriority(Enum):
    """Universal ticket priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class UniversalTicket:
    """Universal ticket representation."""
    id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    platform: TicketPlatform
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    epic_id: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    platform_specific_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TicketQuery:
    """Universal ticket query."""
    platform: Optional[TicketPlatform] = None
    status: Optional[Union[TicketStatus, List[TicketStatus]]] = None
    priority: Optional[Union[TicketPriority, List[TicketPriority]]] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    epic_id: Optional[str] = None
    labels: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    text_search: Optional[str] = None
    limit: Optional[int] = None


class PlatformAdapter:
    """Base class for platform-specific adapters."""
    
    def __init__(self, platform: TicketPlatform, config: Dict[str, Any], logger):
        self.platform = platform
        self.config = config
        self.logger = logger
    
    async def initialize(self) -> bool:
        """Initialize the platform adapter."""
        raise NotImplementedError
    
    async def create_ticket(self, ticket: UniversalTicket) -> str:
        """Create a ticket and return its ID."""
        raise NotImplementedError
    
    async def get_ticket(self, ticket_id: str) -> Optional[UniversalTicket]:
        """Get a specific ticket."""
        raise NotImplementedError
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update a ticket."""
        raise NotImplementedError
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket."""
        raise NotImplementedError
    
    async def query_tickets(self, query: TicketQuery) -> List[UniversalTicket]:
        """Query tickets based on criteria."""
        raise NotImplementedError
    
    async def get_ticket_comments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get comments for a ticket."""
        raise NotImplementedError
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to a ticket."""
        raise NotImplementedError


class AITrackdownAdapter(PlatformAdapter):
    """Adapter for AI-Trackdown-Tools platform."""
    
    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(TicketPlatform.AI_TRACKDOWN, config, logger)
        self.cli_available = False
        self.base_command = "aitrackdown"
    
    async def initialize(self) -> bool:
        """Initialize AI-Trackdown adapter."""
        try:
            # Check if AI-Trackdown CLI is available
            result = await self._run_command([self.base_command, "--version"])
            self.cli_available = result["success"]
            
            if self.cli_available:
                self.logger.info("AI-Trackdown CLI available")
            else:
                self.logger.warning("AI-Trackdown CLI not available, using fallback mode")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing AI-Trackdown adapter: {e}")
            return False
    
    async def create_ticket(self, ticket: UniversalTicket) -> str:
        """Create ticket using AI-Trackdown CLI."""
        try:
            if not self.cli_available:
                return await self._create_ticket_fallback(ticket)
            
            # Determine ticket type based on epic_id or labels
            ticket_type = self._determine_ticket_type(ticket)
            
            command = [
                self.base_command, ticket_type, "create",
                "--title", ticket.title,
                "--description", ticket.description,
                "--priority", ticket.priority.value
            ]
            
            if ticket.epic_id:
                command.extend(["--epic", ticket.epic_id])
            
            if ticket.labels:
                command.extend(["--labels", ",".join(ticket.labels)])
            
            result = await self._run_command(command)
            
            if result["success"]:
                # Extract ticket ID from output
                ticket_id = self._extract_ticket_id(result["output"])
                self.logger.info(f"Created ticket {ticket_id} via AI-Trackdown")
                return ticket_id
            else:
                raise Exception(f"CLI command failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Error creating ticket: {e}")
            raise
    
    async def get_ticket(self, ticket_id: str) -> Optional[UniversalTicket]:
        """Get ticket using AI-Trackdown CLI."""
        try:
            if not self.cli_available:
                return await self._get_ticket_fallback(ticket_id)
            
            # Try different ticket types
            for ticket_type in ["issue", "task", "epic"]:
                command = [self.base_command, ticket_type, "show", ticket_id]
                result = await self._run_command(command)
                
                if result["success"]:
                    return self._parse_ticket_output(result["output"])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id}: {e}")
            return None
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket using AI-Trackdown CLI."""
        try:
            if not self.cli_available:
                return await self._update_ticket_fallback(ticket_id, updates)
            
            # Determine ticket type
            ticket_type = await self._determine_existing_ticket_type(ticket_id)
            
            command = [self.base_command, ticket_type, "update", ticket_id]
            
            if "status" in updates:
                command.extend(["--status", updates["status"]])
            
            if "priority" in updates:
                command.extend(["--priority", updates["priority"]])
            
            if "assignee" in updates:
                command.extend(["--assignee", updates["assignee"]])
            
            result = await self._run_command(command)
            return result["success"]
            
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket_id}: {e}")
            return False
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ticket (not typically supported in AI-Trackdown)."""
        self.logger.warning("Delete operation not supported for AI-Trackdown")
        return False
    
    async def query_tickets(self, query: TicketQuery) -> List[UniversalTicket]:
        """Query tickets using AI-Trackdown CLI."""
        try:
            if not self.cli_available:
                return await self._query_tickets_fallback(query)
            
            tickets = []
            
            # Query different ticket types
            for ticket_type in ["issue", "task", "epic"]:
                command = [self.base_command, ticket_type, "list"]
                
                if query.status:
                    if isinstance(query.status, list):
                        command.extend(["--status", ",".join(s.value for s in query.status)])
                    else:
                        command.extend(["--status", query.status.value])
                
                if query.priority:
                    if isinstance(query.priority, list):
                        command.extend(["--priority", ",".join(p.value for p in query.priority)])
                    else:
                        command.extend(["--priority", query.priority.value])
                
                if query.limit:
                    command.extend(["--limit", str(query.limit)])
                
                result = await self._run_command(command)
                
                if result["success"]:
                    parsed_tickets = self._parse_ticket_list(result["output"])
                    tickets.extend(parsed_tickets)
            
            return tickets
            
        except Exception as e:
            self.logger.error(f"Error querying tickets: {e}")
            return []
    
    async def get_ticket_comments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get comments for a ticket."""
        # AI-Trackdown doesn't have comment system yet
        return []
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add comment to a ticket."""
        # AI-Trackdown doesn't have comment system yet
        self.logger.info(f"Comment functionality not available for AI-Trackdown")
        return False
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run AI-Trackdown CLI command."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "returncode": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": -1
            }
    
    def _determine_ticket_type(self, ticket: UniversalTicket) -> str:
        """Determine AI-Trackdown ticket type from ticket data."""
        if ticket.epic_id:
            return "task"
        elif "epic" in ticket.labels:
            return "epic"
        else:
            return "issue"
    
    async def _determine_existing_ticket_type(self, ticket_id: str) -> str:
        """Determine type of existing ticket."""
        # Try to determine from ticket ID prefix
        if ticket_id.startswith("EP-"):
            return "epic"
        elif ticket_id.startswith("TSK-"):
            return "task"
        else:
            return "issue"
    
    def _extract_ticket_id(self, output: str) -> str:
        """Extract ticket ID from CLI output."""
        # Implementation would parse CLI output for ticket ID
        lines = output.strip().split('\n')
        for line in lines:
            if "created" in line.lower() or "id:" in line.lower():
                # Extract ID pattern
                import re
                match = re.search(r'(EP-\d+|ISS-\d+|TSK-\d+)', line)
                if match:
                    return match.group(1)
        
        # Fallback - generate ID
        return f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _parse_ticket_output(self, output: str) -> UniversalTicket:
        """Parse ticket information from CLI output."""
        # Implementation would parse CLI output into UniversalTicket
        # For now, return a basic ticket
        return UniversalTicket(
            id="PARSED-001",
            title="Parsed Ticket",
            description="Ticket parsed from CLI output",
            status=TicketStatus.TODO,
            priority=TicketPriority.MEDIUM,
            platform=TicketPlatform.AI_TRACKDOWN
        )
    
    def _parse_ticket_list(self, output: str) -> List[UniversalTicket]:
        """Parse list of tickets from CLI output."""
        # Implementation would parse CLI list output
        return []
    
    # Fallback methods for when CLI is not available
    async def _create_ticket_fallback(self, ticket: UniversalTicket) -> str:
        """Create ticket using direct file system operations."""
        self.logger.info("Using fallback method for ticket creation")
        # Implementation would create ticket files directly
        return f"FALLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async def _get_ticket_fallback(self, ticket_id: str) -> Optional[UniversalTicket]:
        """Get ticket using direct file system operations."""
        self.logger.info("Using fallback method for ticket retrieval")
        return None
    
    async def _update_ticket_fallback(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket using direct file system operations."""
        self.logger.info("Using fallback method for ticket update")
        return False
    
    async def _query_tickets_fallback(self, query: TicketQuery) -> List[UniversalTicket]:
        """Query tickets using direct file system operations."""
        self.logger.info("Using fallback method for ticket query")
        return []


class JiraAdapter(PlatformAdapter):
    """Adapter for Jira platform."""
    
    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(TicketPlatform.JIRA, config, logger)
        self.api_client = None
    
    async def initialize(self) -> bool:
        """Initialize Jira adapter."""
        try:
            # Would initialize Jira API client
            self.logger.info("Jira adapter initialized (placeholder)")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Jira adapter: {e}")
            return False
    
    async def create_ticket(self, ticket: UniversalTicket) -> str:
        """Create Jira ticket."""
        # Implementation would use Jira API
        self.logger.info("Jira ticket creation not implemented")
        return "JIRA-PLACEHOLDER"
    
    async def get_ticket(self, ticket_id: str) -> Optional[UniversalTicket]:
        """Get Jira ticket."""
        # Implementation would use Jira API
        return None
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update Jira ticket."""
        # Implementation would use Jira API
        return False
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete Jira ticket."""
        # Implementation would use Jira API
        return False
    
    async def query_tickets(self, query: TicketQuery) -> List[UniversalTicket]:
        """Query Jira tickets."""
        # Implementation would use Jira API
        return []
    
    async def get_ticket_comments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get Jira ticket comments."""
        return []
    
    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add comment to Jira ticket."""
        return False


class PlatformAbstractionLayer:
    """Abstraction layer for multiple ticketing platforms."""
    
    def __init__(self, logger):
        self.logger = logger
        self.adapters: Dict[TicketPlatform, PlatformAdapter] = {}
        self.primary_platform: Optional[TicketPlatform] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize platform adapters."""
        platform_configs = config.get("platforms", {})
        
        # Initialize AI-Trackdown (primary)
        if "ai_trackdown" in platform_configs or not platform_configs:
            ai_config = platform_configs.get("ai_trackdown", {})
            adapter = AITrackdownAdapter(ai_config, self.logger)
            if await adapter.initialize():
                self.adapters[TicketPlatform.AI_TRACKDOWN] = adapter
                self.primary_platform = TicketPlatform.AI_TRACKDOWN
                self.logger.info("AI-Trackdown adapter initialized as primary")
        
        # Initialize other platforms if configured
        if "jira" in platform_configs:
            jira_config = platform_configs["jira"]
            adapter = JiraAdapter(jira_config, self.logger)
            if await adapter.initialize():
                self.adapters[TicketPlatform.JIRA] = adapter
                self.logger.info("Jira adapter initialized")
    
    def get_adapter(self, platform: Optional[TicketPlatform] = None) -> PlatformAdapter:
        """Get platform adapter."""
        if platform is None:
            platform = self.primary_platform
        
        if platform not in self.adapters:
            raise ValueError(f"Platform {platform} not available")
        
        return self.adapters[platform]
    
    def get_available_platforms(self) -> List[TicketPlatform]:
        """Get list of available platforms."""
        return list(self.adapters.keys())


class UniversalTicketInterface:
    """Universal interface for ticket operations across platforms."""
    
    def __init__(self, platform_layer: PlatformAbstractionLayer, logger):
        self.platform_layer = platform_layer
        self.logger = logger
    
    async def create_ticket(
        self, 
        title: str,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        status: TicketStatus = TicketStatus.TODO,
        platform: Optional[TicketPlatform] = None,
        **kwargs
    ) -> str:
        """Create a ticket on specified platform."""
        adapter = self.platform_layer.get_adapter(platform)
        
        ticket = UniversalTicket(
            id="",  # Will be assigned by platform
            title=title,
            description=description,
            status=status,
            priority=priority,
            platform=adapter.platform,
            assignee=kwargs.get("assignee"),
            reporter=kwargs.get("reporter"),
            epic_id=kwargs.get("epic_id"),
            labels=kwargs.get("labels", []),
            due_date=kwargs.get("due_date"),
            custom_fields=kwargs.get("custom_fields", {})
        )
        
        ticket_id = await adapter.create_ticket(ticket)
        self.logger.info(f"Created ticket {ticket_id} on {adapter.platform.value}")
        return ticket_id
    
    async def get_ticket(
        self, 
        ticket_id: str, 
        platform: Optional[TicketPlatform] = None
    ) -> Optional[UniversalTicket]:
        """Get a ticket from specified platform."""
        adapter = self.platform_layer.get_adapter(platform)
        return await adapter.get_ticket(ticket_id)
    
    async def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        platform: Optional[TicketPlatform] = None
    ) -> bool:
        """Update a ticket on specified platform."""
        adapter = self.platform_layer.get_adapter(platform)
        success = await adapter.update_ticket(ticket_id, updates)
        
        if success:
            self.logger.info(f"Updated ticket {ticket_id} on {adapter.platform.value}")
        
        return success
    
    async def query_tickets(
        self,
        query: TicketQuery,
        platform: Optional[TicketPlatform] = None
    ) -> List[UniversalTicket]:
        """Query tickets from specified platform."""
        adapter = self.platform_layer.get_adapter(platform)
        return await adapter.query_tickets(query)
    
    async def add_comment(
        self,
        ticket_id: str,
        comment: str,
        platform: Optional[TicketPlatform] = None
    ) -> bool:
        """Add comment to a ticket."""
        adapter = self.platform_layer.get_adapter(platform)
        return await adapter.add_comment(ticket_id, comment)


class TicketLifecycleManager:
    """Manager for ticket lifecycle operations."""
    
    def __init__(self, ticket_interface: UniversalTicketInterface, logger):
        self.ticket_interface = ticket_interface
        self.logger = logger
    
    async def transition_ticket(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        platform: Optional[TicketPlatform] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Transition ticket to new status."""
        try:
            # Get current ticket
            ticket = await self.ticket_interface.get_ticket(ticket_id, platform)
            if not ticket:
                self.logger.error(f"Ticket {ticket_id} not found")
                return False
            
            # Validate transition
            if not self._is_valid_transition(ticket.status, new_status):
                self.logger.warning(
                    f"Invalid transition from {ticket.status.value} to {new_status.value}"
                )
                return False
            
            # Update ticket status
            success = await self.ticket_interface.update_ticket(
                ticket_id, {"status": new_status.value}, platform
            )
            
            # Add comment if provided
            if success and comment:
                await self.ticket_interface.add_comment(ticket_id, comment, platform)
            
            if success:
                self.logger.info(
                    f"Transitioned ticket {ticket_id} from {ticket.status.value} to {new_status.value}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error transitioning ticket {ticket_id}: {e}")
            return False
    
    def _is_valid_transition(self, current: TicketStatus, new: TicketStatus) -> bool:
        """Validate if status transition is allowed."""
        # Define valid transitions
        valid_transitions = {
            TicketStatus.TODO: [TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED],
            TicketStatus.IN_PROGRESS: [TicketStatus.BLOCKED, TicketStatus.REVIEW, TicketStatus.DONE, TicketStatus.CANCELLED],
            TicketStatus.BLOCKED: [TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED],
            TicketStatus.REVIEW: [TicketStatus.IN_PROGRESS, TicketStatus.TESTING, TicketStatus.DONE],
            TicketStatus.TESTING: [TicketStatus.REVIEW, TicketStatus.DONE, TicketStatus.IN_PROGRESS],
            TicketStatus.DONE: [],  # Final state
            TicketStatus.CANCELLED: []  # Final state
        }
        
        return new in valid_transitions.get(current, [])
    
    async def assign_ticket(
        self,
        ticket_id: str,
        assignee: str,
        platform: Optional[TicketPlatform] = None
    ) -> bool:
        """Assign ticket to user."""
        return await self.ticket_interface.update_ticket(
            ticket_id, {"assignee": assignee}, platform
        )
    
    async def set_priority(
        self,
        ticket_id: str,
        priority: TicketPriority,
        platform: Optional[TicketPlatform] = None
    ) -> bool:
        """Set ticket priority."""
        return await self.ticket_interface.update_ticket(
            ticket_id, {"priority": priority.value}, platform
        )


class TicketingAgent(BaseAgent):
    """
    Ticketing Agent - Core agent for specialized issue management and ticket operations.
    
    Responsibilities:
    1. All ticket operations (read/write) across multiple platforms
    2. Support for internal AI tracking tools and external systems (Jira, etc.)
    3. Abstract ticket management from PM
    4. Collaborate hand-in-hand with PM for ticket needs
    5. Handle ticket lifecycle management across different platforms
    6. Core agent functionality for issue management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Ticketing Agent."""
        super().__init__(
            agent_id="ticketing-agent",
            agent_type="ticketing",
            capabilities=[
                "universal_ticket_operations",
                "multi_platform_support",
                "ticket_lifecycle_management",
                "pm_collaboration",
                "ai_trackdown_integration",
                "external_platform_integration",
                "ticket_query_and_search",
                "automated_ticket_transitions",
                "ticket_health_monitoring"
            ],
            config=config,
            tier="system"  # Core agent
        )
        
        # Initialize components
        self.platform_layer = PlatformAbstractionLayer(self.logger)
        self.ticket_interface: Optional[UniversalTicketInterface] = None
        self.lifecycle_manager: Optional[TicketLifecycleManager] = None
        
        # State tracking
        self.active_tickets: Dict[str, UniversalTicket] = {}
        self.platform_status: Dict[TicketPlatform, bool] = {}
        
        self.logger.info("Ticketing Agent initialized successfully")
    
    async def _initialize(self) -> None:
        """Initialize the Ticketing Agent."""
        try:
            # Initialize platform layer
            platform_config = self.config.get("ticketing", {})
            await self.platform_layer.initialize(platform_config)
            
            # Initialize interfaces
            self.ticket_interface = UniversalTicketInterface(self.platform_layer, self.logger)
            self.lifecycle_manager = TicketLifecycleManager(self.ticket_interface, self.logger)
            
            # Update platform status
            available_platforms = self.platform_layer.get_available_platforms()
            for platform in TicketPlatform:
                self.platform_status[platform] = platform in available_platforms
            
            self.logger.info(f"Ticketing Agent initialized with platforms: {[p.value for p in available_platforms]}")
            
        except Exception as e:
            self.logger.error(f"Error initializing Ticketing Agent: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup Ticketing Agent resources."""
        try:
            # Save state if needed
            self.logger.info("Ticketing Agent cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Ticketing Agent: {e}")
            raise
    
    async def _execute_operation(
        self, 
        operation: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute Ticketing Agent operations."""
        context = context or {}
        
        if operation == "create_ticket":
            return await self.create_ticket(**kwargs)
        
        elif operation == "get_ticket":
            ticket_id = kwargs.get("ticket_id") or context.get("ticket_id")
            platform = kwargs.get("platform") or context.get("platform")
            return await self.get_ticket(ticket_id, platform)
        
        elif operation == "update_ticket":
            ticket_id = kwargs.get("ticket_id") or context.get("ticket_id")
            updates = kwargs.get("updates") or context.get("updates", {})
            platform = kwargs.get("platform") or context.get("platform")
            return await self.update_ticket(ticket_id, updates, platform)
        
        elif operation == "query_tickets":
            query_params = kwargs.get("query") or context.get("query", {})
            platform = kwargs.get("platform") or context.get("platform")
            return await self.query_tickets(query_params, platform)
        
        elif operation == "transition_ticket":
            ticket_id = kwargs.get("ticket_id") or context.get("ticket_id")
            new_status = kwargs.get("status") or context.get("status")
            platform = kwargs.get("platform") or context.get("platform")
            comment = kwargs.get("comment") or context.get("comment")
            return await self.transition_ticket(ticket_id, new_status, platform, comment)
        
        elif operation == "get_platform_status":
            return await self.get_platform_status()
        
        elif operation == "health_check_tickets":
            return await self.health_check_tickets()
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        platform: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new ticket."""
        try:
            if not self.ticket_interface:
                raise Exception("Ticket interface not initialized")
            
            # Convert string priority to enum
            priority_enum = TicketPriority(priority.lower())
            
            # Convert platform string to enum if provided
            platform_enum = None
            if platform:
                platform_enum = TicketPlatform(platform.lower())
            
            ticket_id = await self.ticket_interface.create_ticket(
                title=title,
                description=description,
                priority=priority_enum,
                platform=platform_enum,
                **kwargs
            )
            
            # Notify PM
            await self.collaborate_with_pm(
                f"Created ticket: {title}",
                context={"ticket_id": ticket_id, "priority": priority},
                priority="normal"
            )
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "platform": platform or "primary"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_ticket(
        self, 
        ticket_id: str, 
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific ticket."""
        try:
            if not self.ticket_interface:
                raise Exception("Ticket interface not initialized")
            
            platform_enum = None
            if platform:
                platform_enum = TicketPlatform(platform.lower())
            
            ticket = await self.ticket_interface.get_ticket(ticket_id, platform_enum)
            
            if ticket:
                return {
                    "success": True,
                    "ticket": {
                        "id": ticket.id,
                        "title": ticket.title,
                        "description": ticket.description,
                        "status": ticket.status.value,
                        "priority": ticket.priority.value,
                        "platform": ticket.platform.value,
                        "assignee": ticket.assignee,
                        "created_date": ticket.created_date.isoformat() if ticket.created_date else None,
                        "labels": ticket.labels
                    }
                }
            else:
                return {"success": False, "error": "Ticket not found"}
                
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a ticket."""
        try:
            if not self.ticket_interface:
                raise Exception("Ticket interface not initialized")
            
            platform_enum = None
            if platform:
                platform_enum = TicketPlatform(platform.lower())
            
            success = await self.ticket_interface.update_ticket(
                ticket_id, updates, platform_enum
            )
            
            if success:
                # Notify PM for significant updates
                if any(key in updates for key in ["status", "priority", "assignee"]):
                    await self.collaborate_with_pm(
                        f"Updated ticket {ticket_id}",
                        context={"ticket_id": ticket_id, "updates": updates},
                        priority="normal"
                    )
            
            return {"success": success}
            
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def query_tickets(
        self,
        query_params: Dict[str, Any],
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query tickets based on criteria."""
        try:
            if not self.ticket_interface:
                raise Exception("Ticket interface not initialized")
            
            # Build query object
            query = TicketQuery()
            
            if platform:
                query.platform = TicketPlatform(platform.lower())
            
            if "status" in query_params:
                status_val = query_params["status"]
                if isinstance(status_val, list):
                    query.status = [TicketStatus(s) for s in status_val]
                else:
                    query.status = TicketStatus(status_val)
            
            if "priority" in query_params:
                priority_val = query_params["priority"]
                if isinstance(priority_val, list):
                    query.priority = [TicketPriority(p) for p in priority_val]
                else:
                    query.priority = TicketPriority(priority_val)
            
            if "assignee" in query_params:
                query.assignee = query_params["assignee"]
            
            if "limit" in query_params:
                query.limit = query_params["limit"]
            
            tickets = await self.ticket_interface.query_tickets(query)
            
            return {
                "success": True,
                "tickets": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status.value,
                        "priority": t.priority.value,
                        "platform": t.platform.value,
                        "assignee": t.assignee
                    }
                    for t in tickets
                ],
                "count": len(tickets)
            }
            
        except Exception as e:
            self.logger.error(f"Error querying tickets: {e}")
            return {"success": False, "error": str(e)}
    
    async def transition_ticket(
        self,
        ticket_id: str,
        new_status: str,
        platform: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transition ticket to new status."""
        try:
            if not self.lifecycle_manager:
                raise Exception("Lifecycle manager not initialized")
            
            status_enum = TicketStatus(new_status.lower())
            platform_enum = None
            if platform:
                platform_enum = TicketPlatform(platform.lower())
            
            success = await self.lifecycle_manager.transition_ticket(
                ticket_id, status_enum, platform_enum, comment
            )
            
            if success:
                await self.collaborate_with_pm(
                    f"Transitioned ticket {ticket_id} to {new_status}",
                    context={"ticket_id": ticket_id, "new_status": new_status},
                    priority="normal"
                )
            
            return {"success": success}
            
        except Exception as e:
            self.logger.error(f"Error transitioning ticket {ticket_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms."""
        return {
            "platforms": {
                platform.value: {"available": status, "primary": platform == self.platform_layer.primary_platform}
                for platform, status in self.platform_status.items()
            },
            "primary_platform": self.platform_layer.primary_platform.value if self.platform_layer.primary_platform else None
        }
    
    async def health_check_tickets(self) -> Dict[str, Any]:
        """Perform health check on ticket operations."""
        health_results = {
            "overall_health": "healthy",
            "platform_health": {},
            "recent_operations": self.operations_count,
            "issues": []
        }
        
        # Check each platform
        for platform, available in self.platform_status.items():
            if available:
                try:
                    # Try a simple query to test platform
                    query = TicketQuery(limit=1)
                    tickets = await self.ticket_interface.query_tickets(query, platform)
                    health_results["platform_health"][platform.value] = "healthy"
                except Exception as e:
                    health_results["platform_health"][platform.value] = "unhealthy"
                    health_results["issues"].append(f"{platform.value}: {str(e)}")
            else:
                health_results["platform_health"][platform.value] = "unavailable"
        
        # Determine overall health
        if health_results["issues"]:
            health_results["overall_health"] = "degraded"
        
        return health_results
    
    def _should_notify_pm(self, operation: str, result: Any) -> bool:
        """Determine if PM should be notified of operation completion."""
        # Notify PM for ticket creation, critical updates, and transitions
        pm_notify_operations = [
            "create_ticket", "transition_ticket", "health_check_tickets"
        ]
        return operation in pm_notify_operations