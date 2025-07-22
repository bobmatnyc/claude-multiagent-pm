#!/usr/bin/env python3
"""
TicketingService Usage Examples
===============================

This file demonstrates various usage patterns for the TicketingService
in the Claude PM Framework.

Run with: python docs/examples/ticketing_service_examples.py
"""

import asyncio
from datetime import datetime
from claude_pm.services.ticketing_service import TicketingService, get_ticketing_service
from claude_pm.orchestration.ticketing_helpers import TicketingHelper

# Example 1: Basic Ticket Operations
def example_basic_operations():
    """Basic ticket creation, reading, updating, and closing."""
    print("\n=== Example 1: Basic Ticket Operations ===")
    
    # Get the singleton instance
    ticketing = get_ticketing_service()
    
    # Create a ticket
    ticket = ticketing.create_ticket(
        title="Fix ImportError in core service",
        description="Users report ImportError when running claude-pm --version",
        priority="critical",
        assignee="research-agent",
        labels=["bug", "production", "urgent"],
        metadata={
            "error_type": "ImportError",
            "affected_versions": ["1.3.9", "1.4.0"],
            "reproduction_rate": "100%"
        }
    )
    
    print(f"Created ticket: {ticket.id}")
    print(f"  Title: {ticket.title}")
    print(f"  Priority: {ticket.priority}")
    print(f"  Assignee: {ticket.assignee}")
    
    # Update ticket
    updated = ticketing.update_ticket(
        ticket.id,
        status="in_progress",
        assignee="engineer-agent",
        metadata={"root_cause": "circular import identified"}
    )
    
    print(f"\nUpdated ticket status: {updated.status}")
    print(f"Updated assignee: {updated.assignee}")
    
    # Add comment
    ticketing.add_comment(
        ticket.id,
        "Root cause identified: Circular import between core.py and services.py",
        author="research-agent"
    )
    
    # Close ticket
    closed = ticketing.close_ticket(
        ticket.id,
        resolution="Refactored imports to eliminate circular dependency"
    )
    
    print(f"\nClosed ticket with status: {closed.status}")
    
    return ticket.id


# Example 2: PM Ticketing Helper
def example_pm_helper():
    """Using TicketingHelper for PM-specific operations."""
    print("\n=== Example 2: PM Ticketing Helper ===")
    
    helper = TicketingHelper()
    
    # Create agent task ticket
    ticket = helper.create_agent_task_ticket(
        agent_name="engineer",
        task_description="Implement user authentication system with JWT tokens",
        priority="high",
        additional_context={
            "sprint": "2025-Q1-Sprint3",
            "story_points": 8,
            "dependencies": ["database-schema", "jwt-library"]
        }
    )
    
    print(f"Created agent task: {ticket.id}")
    print(f"  Agent: engineer")
    print(f"  Priority: {ticket.priority}")
    
    # Check agent workload
    workload = helper.get_agent_workload("engineer")
    print(f"\nEngineer Agent Workload:")
    print(f"  Total tickets: {workload['total_tickets']}")
    print(f"  Open: {workload['open']}")
    print(f"  In Progress: {workload['in_progress']}")
    print(f"  High Priority: {workload['high_priority']}")
    
    # Get project overview
    overview = helper.get_project_overview()
    print(f"\nProject Overview:")
    print(f"  Total tickets: {overview['total_tickets']}")
    print(f"  Agent tasks: {overview['agent_tasks']}")
    print(f"  Agents with tasks: {overview['agents_with_tasks']}")
    
    return ticket.id


# Example 3: Multi-Agent Workflow
def example_multi_agent_workflow():
    """Orchestrating a multi-agent workflow with tickets."""
    print("\n=== Example 3: Multi-Agent Workflow ===")
    
    ticketing = get_ticketing_service()
    helper = TicketingHelper()
    
    # Parent ticket for feature
    parent = ticketing.create_ticket(
        title="Implement real-time collaboration features",
        description="Add WebSocket-based real-time updates for multi-user editing",
        priority="high",
        labels=["feature", "epic", "websocket"],
        metadata={
            "type": "epic",
            "estimated_days": 10,
            "business_value": "high"
        }
    )
    
    print(f"Created parent epic: {parent.id}")
    
    # Create subtasks for each agent
    subtasks = [
        ("research", "Research WebSocket libraries and scalability patterns", 2),
        ("engineer", "Implement WebSocket server and client", 5),
        ("security", "Security audit of WebSocket implementation", 1),
        ("qa", "Create comprehensive test suite for real-time features", 2)
    ]
    
    for agent, task, days in subtasks:
        subtask = helper.create_agent_task_ticket(
            agent_name=agent,
            task_description=task,
            priority="high",
            additional_context={
                "parent_ticket": parent.id,
                "estimated_days": days,
                "phase": subtasks.index((agent, task, days)) + 1
            }
        )
        
        print(f"  Created subtask for {agent}: {subtask.id}")
        
        # Link to parent
        ticketing.add_comment(
            parent.id,
            f"Created subtask {subtask.id} for {agent} agent: {task}",
            author="pm-orchestrator"
        )
    
    return parent.id


# Example 4: Ticket Search and Analytics
def example_search_analytics():
    """Searching tickets and generating analytics."""
    print("\n=== Example 4: Ticket Search and Analytics ===")
    
    ticketing = get_ticketing_service()
    
    # Search for tickets
    import_issues = ticketing.search_tickets("ImportError", limit=5)
    print(f"Found {len(import_issues)} tickets related to ImportError")
    
    for ticket in import_issues:
        print(f"  - {ticket.id}: {ticket.title} ({ticket.status})")
    
    # Get statistics
    stats = ticketing.get_ticket_statistics()
    print(f"\nTicket Statistics:")
    print(f"  Total tickets: {stats.get('total', 0)}")
    print(f"  By status: {stats.get('by_status', {})}")
    print(f"  By priority: {stats.get('by_priority', {})}")
    print(f"  Unassigned: {stats.get('unassigned', 0)}")
    
    # List high-priority tickets
    urgent = ticketing.list_tickets(
        priority="critical",
        status="open",
        limit=3
    )
    
    print(f"\nUrgent open tickets ({len(urgent)}):")
    for ticket in urgent:
        print(f"  - {ticket.id}: {ticket.title}")
        print(f"    Assignee: {ticket.assignee or 'Unassigned'}")


# Example 5: Async Operations
async def example_async_operations():
    """Using async methods for concurrent operations."""
    print("\n=== Example 5: Async Operations ===")
    
    ticketing = get_ticketing_service()
    
    # Create multiple tickets concurrently
    tasks = []
    for i in range(3):
        task = ticketing.acreate_ticket(
            title=f"Async task {i+1}",
            description=f"Test async ticket creation {i+1}",
            priority="medium",
            labels=["async", "test"]
        )
        tasks.append(task)
    
    # Wait for all tickets to be created
    tickets = await asyncio.gather(*tasks)
    
    print(f"Created {len(tickets)} tickets asynchronously:")
    for ticket in tickets:
        print(f"  - {ticket.id}: {ticket.title}")
    
    # List tickets asynchronously
    open_tickets = await ticketing.alist_tickets(status="open", limit=5)
    print(f"\nFound {len(open_tickets)} open tickets asynchronously")
    
    return [t.id for t in tickets]


# Example 6: Error Handling Patterns
def example_error_handling():
    """Demonstrating error handling patterns."""
    print("\n=== Example 6: Error Handling Patterns ===")
    
    ticketing = get_ticketing_service()
    
    # Try to get non-existent ticket
    missing = ticketing.get_ticket("INVALID-ID-12345")
    if missing is None:
        print("Handled missing ticket gracefully: None returned")
    
    # Safe ticket operation wrapper
    def safe_update(ticket_id, **kwargs):
        try:
            return ticketing.update_ticket(ticket_id, **kwargs)
        except Exception as e:
            print(f"Failed to update ticket: {e}")
            return None
    
    # Try updating non-existent ticket
    result = safe_update("INVALID-ID", status="closed")
    if result is None:
        print("Handled invalid update gracefully")
    
    # Create ticket with validation
    def create_validated_ticket(title, description, priority="medium"):
        # Validate inputs
        if not title or len(title) < 5:
            raise ValueError("Title must be at least 5 characters")
        
        if priority not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"Invalid priority: {priority}")
        
        return ticketing.create_ticket(
            title=title,
            description=description,
            priority=priority
        )
    
    try:
        # This will fail validation
        create_validated_ticket("Bad", "Too short title", "invalid")
    except ValueError as e:
        print(f"Validation error caught: {e}")
    
    # Create valid ticket
    valid = create_validated_ticket(
        "Valid ticket with proper title",
        "This ticket passes all validation",
        "medium"
    )
    print(f"Created valid ticket: {valid.id}")


# Example 7: Workflow Automation
def example_workflow_automation():
    """Automating common ticketing workflows."""
    print("\n=== Example 7: Workflow Automation ===")
    
    ticketing = get_ticketing_service()
    helper = TicketingHelper()
    
    def create_bug_workflow(error_details):
        """Automated bug ticket creation with workflow."""
        # Create main bug ticket
        bug = ticketing.create_ticket(
            title=f"Bug: {error_details['summary']}",
            description=error_details['full_description'],
            priority="critical" if error_details.get('production') else "high",
            labels=["bug", "auto-created"],
            metadata={
                "error_type": error_details['type'],
                "stack_trace": error_details.get('stack_trace', ''),
                "user_reports": error_details.get('reports', 1)
            }
        )
        
        # Auto-assign based on error type
        if "import" in error_details['type'].lower():
            ticketing.update_ticket(bug.id, assignee="research-agent")
        elif "security" in error_details['type'].lower():
            ticketing.update_ticket(bug.id, assignee="security-agent")
        else:
            ticketing.update_ticket(bug.id, assignee="engineer-agent")
        
        # Add initial triage comment
        ticketing.add_comment(
            bug.id,
            f"Auto-created from error report. Type: {error_details['type']}",
            author="automation"
        )
        
        return bug
    
    # Test the automation
    error = {
        "summary": "ImportError in production",
        "full_description": "ImportError when loading unified_core_service module",
        "type": "ImportError",
        "production": True,
        "stack_trace": "Traceback...",
        "reports": 5
    }
    
    automated_bug = create_bug_workflow(error)
    print(f"Automated bug ticket created: {automated_bug.id}")
    print(f"  Auto-assigned to: {automated_bug.assignee}")
    
    return automated_bug.id


# Run all examples
def main():
    """Run all examples."""
    print("Claude PM TicketingService Examples")
    print("===================================")
    
    # Run synchronous examples
    ticket1 = example_basic_operations()
    ticket2 = example_pm_helper()
    ticket3 = example_multi_agent_workflow()
    example_search_analytics()
    
    # Run async example
    print("\nRunning async example...")
    async_tickets = asyncio.run(example_async_operations())
    
    example_error_handling()
    ticket7 = example_workflow_automation()
    
    print("\n=== Summary ===")
    print("Examples completed successfully!")
    print(f"Created tickets: {ticket1}, {ticket2}, {ticket3}, {ticket7}")
    print(f"Async tickets: {async_tickets}")


if __name__ == "__main__":
    main()