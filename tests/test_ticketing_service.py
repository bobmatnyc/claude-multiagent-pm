#!/usr/bin/env python3
"""
Test file for TicketingService
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services import TicketingService, get_ticketing_service


def test_ticketing_service():
    """Test basic ticketing service functionality."""
    print("Testing TicketingService...")
    
    # Get singleton instance
    ticketing = get_ticketing_service()
    print(f"✓ Got ticketing service instance: {ticketing}")
    
    # Test creating a ticket
    try:
        ticket = ticketing.create_ticket(
            title="Test ticket from TicketingService",
            description="This is a test ticket created by the new TicketingService wrapper",
            priority="high",
            labels=["test", "service-integration"]
        )
        print(f"✓ Created ticket: {ticket.id} - {ticket.title}")
    except Exception as e:
        print(f"✗ Failed to create ticket: {e}")
        return
    
    # Test listing tickets
    try:
        tickets = ticketing.list_tickets(status="open", limit=5)
        print(f"✓ Listed {len(tickets)} open tickets")
        for t in tickets:
            print(f"  - {t.id}: {t.title} ({t.status})")
    except Exception as e:
        print(f"✗ Failed to list tickets: {e}")
    
    # Test updating a ticket
    try:
        if ticket:
            updated = ticketing.update_ticket(
                ticket.id,
                status="in_progress",
                assignee="engineer-agent"
            )
            print(f"✓ Updated ticket {updated.id} - status: {updated.status}, assignee: {updated.assignee}")
    except Exception as e:
        print(f"✗ Failed to update ticket: {e}")
    
    # Test adding a comment
    try:
        if ticket:
            success = ticketing.add_comment(
                ticket.id,
                "This is a test comment from the TicketingService test",
                author="test-script"
            )
            print(f"✓ Added comment to ticket: {success}")
    except Exception as e:
        print(f"✗ Failed to add comment: {e}")
    
    # Test getting statistics
    try:
        stats = ticketing.get_ticket_statistics()
        print(f"✓ Got ticket statistics: {stats}")
    except Exception as e:
        print(f"✗ Failed to get statistics: {e}")
    
    print("\nTicketingService test complete!")


if __name__ == "__main__":
    test_ticketing_service()