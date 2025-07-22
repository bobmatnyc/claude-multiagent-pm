#!/usr/bin/env python3
"""
Ticketing Helpers for PM Orchestration
=====================================

Convenience functions and patterns for PM orchestrators to use
the TicketingService effectively.
"""

from typing import Dict, List, Optional, Any
from claude_pm.services.ticketing_service import TicketingService, TicketData, get_ticketing_service
import logging

logger = logging.getLogger(__name__)


class TicketingHelper:
    """Helper class for PM orchestration ticket operations."""
    
    def __init__(self):
        """Initialize with ticketing service."""
        self.ticketing = get_ticketing_service()
    
    def create_agent_task_ticket(
        self,
        agent_name: str,
        task_description: str,
        priority: str = "medium",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Optional[TicketData]:
        """
        Create a ticket for an agent task.
        
        Args:
            agent_name: Name of the agent (e.g., "engineer", "documentation")
            task_description: Description of the task
            priority: Task priority
            additional_context: Additional metadata
            
        Returns:
            Created ticket or None on failure
        """
        try:
            # Format title with agent name
            title = f"[{agent_name.title()}] {task_description[:100]}"
            
            # Build metadata
            metadata = {
                "agent": agent_name,
                "task_type": "agent_delegation",
                "created_by": "pm_orchestrator"
            }
            if additional_context:
                metadata.update(additional_context)
            
            # Create ticket
            ticket = self.ticketing.create_ticket(
                title=title,
                description=task_description,
                priority=priority,
                assignee=f"{agent_name}-agent",
                labels=["agent-task", agent_name],
                metadata=metadata
            )
            
            logger.info(f"Created agent task ticket {ticket.id} for {agent_name}")
            return ticket
            
        except Exception as e:
            logger.error(f"Failed to create agent task ticket: {e}")
            return None
    
    def update_agent_task_status(
        self,
        ticket_id: str,
        status: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Update status of an agent task ticket.
        
        Args:
            ticket_id: Ticket identifier
            status: New status
            comment: Optional status comment
            
        Returns:
            True if successful
        """
        try:
            # Update ticket
            updated = self.ticketing.update_ticket(ticket_id, status=status)
            
            if updated and comment:
                self.ticketing.add_comment(
                    ticket_id,
                    comment,
                    author="pm_orchestrator"
                )
            
            return updated is not None
            
        except Exception as e:
            logger.error(f"Failed to update ticket {ticket_id}: {e}")
            return False
    
    def get_agent_workload(self, agent_name: str) -> Dict[str, Any]:
        """
        Get workload summary for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with workload information
        """
        try:
            # Get all tickets assigned to this agent
            tickets = self.ticketing.list_tickets(
                assignee=f"{agent_name}-agent"
            )
            
            # Calculate workload
            workload = {
                "agent": agent_name,
                "total_tickets": len(tickets),
                "open": len([t for t in tickets if t.status == "open"]),
                "in_progress": len([t for t in tickets if t.status == "in_progress"]),
                "high_priority": len([t for t in tickets if t.priority == "high"]),
                "critical_priority": len([t for t in tickets if t.priority == "critical"])
            }
            
            return workload
            
        except Exception as e:
            logger.error(f"Failed to get agent workload: {e}")
            return {}
    
    def get_project_overview(self) -> Dict[str, Any]:
        """
        Get overall project ticket overview.
        
        Returns:
            Dictionary with project statistics
        """
        try:
            stats = self.ticketing.get_ticket_statistics()
            
            # Add PM-specific insights
            all_tickets = self.ticketing.list_tickets()
            agent_tickets = [t for t in all_tickets if "agent-task" in t.labels]
            
            overview = {
                "total_tickets": stats.get("total", 0),
                "agent_tasks": len(agent_tickets),
                "by_status": stats.get("by_status", {}),
                "by_priority": stats.get("by_priority", {}),
                "agents_with_tasks": list(set(
                    t.assignee.replace("-agent", "") 
                    for t in agent_tickets 
                    if t.assignee
                ))
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Failed to get project overview: {e}")
            return {}
    
    def find_related_tickets(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[TicketData]:
        """
        Find tickets related to given keywords.
        
        Args:
            keywords: List of keywords to search
            limit: Maximum results
            
        Returns:
            List of related tickets
        """
        try:
            # Search for each keyword
            all_results = []
            for keyword in keywords:
                results = self.ticketing.search_tickets(keyword, limit=limit)
                all_results.extend(results)
            
            # Deduplicate by ticket ID
            seen = set()
            unique_results = []
            for ticket in all_results:
                if ticket.id not in seen:
                    seen.add(ticket.id)
                    unique_results.append(ticket)
            
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find related tickets: {e}")
            return []


# Convenience functions for direct use

def quick_create_task(
    agent: str,
    task: str,
    priority: str = "medium"
) -> Optional[str]:
    """
    Quick function to create an agent task ticket.
    
    Args:
        agent: Agent name
        task: Task description
        priority: Priority level
        
    Returns:
        Ticket ID or None
    """
    helper = TicketingHelper()
    ticket = helper.create_agent_task_ticket(agent, task, priority)
    return ticket.id if ticket else None


def quick_update_status(ticket_id: str, status: str) -> bool:
    """
    Quick function to update ticket status.
    
    Args:
        ticket_id: Ticket ID
        status: New status
        
    Returns:
        Success boolean
    """
    helper = TicketingHelper()
    return helper.update_agent_task_status(ticket_id, status)


def get_workload_summary() -> Dict[str, Dict[str, Any]]:
    """
    Get workload summary for all agents.
    
    Returns:
        Dictionary mapping agent names to workload info
    """
    helper = TicketingHelper()
    agents = ["documentation", "engineer", "qa", "version_control", 
              "research", "ops", "security", "data_engineer"]
    
    summary = {}
    for agent in agents:
        workload = helper.get_agent_workload(agent)
        if workload.get("total_tickets", 0) > 0:
            summary[agent] = workload
    
    return summary