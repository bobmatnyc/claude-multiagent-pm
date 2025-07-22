#!/usr/bin/env python3
"""
Test PM's ability to create tickets programmatically.
Simulates how PM would create tickets based on user requests.
"""

import json
from datetime import datetime
from pathlib import Path

def pm_create_ticket(ticket_type, title, description, priority="medium", tags=None, orchestration=None):
    """
    Simulate PM creating a ticket based on user request.
    This is how PM would programmatically create tickets.
    """
    
    # Ensure tickets directory exists
    tickets_dir = Path("tasks")
    tickets_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate ticket ID
    existing_tickets = list(tickets_dir.glob(f"{ticket_type}-2025-*.json"))
    next_id = len(existing_tickets) + 1
    ticket_id = f"{ticket_type}-2025-{next_id:03d}"
    
    # Create ticket data
    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "status": "open",
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "created_by": "PM",
        "tags": tags or [],
        "assignee": "PM",  # PM initially owns all tickets
        "metadata": {
            "source": "user_request",
            "pm_created": True,
            "creation_method": "programmatic"
        }
    }
    
    # Add orchestration if provided
    if orchestration:
        ticket["orchestration"] = orchestration
        
    # Save ticket
    ticket_path = tickets_dir / f"{ticket_id}.json"
    with open(ticket_path, 'w') as f:
        json.dump(ticket, f, indent=2)
        
    return ticket_id, ticket_path

# Test PM ticket creation scenarios
print("🎫 Testing PM Ticket Creation Capabilities\n")

# Scenario 1: User reports a bug
print("Scenario 1: User reports a bug")
print("User: 'The framework is throwing errors when I try to use the Research Agent'")
print("\nPM Action: Creating bug ticket...")

bug_id, bug_path = pm_create_ticket(
    ticket_type="BUG",
    title="Research Agent initialization error",
    description="User reports errors when trying to use Research Agent. Need to investigate and fix.",
    priority="high",
    tags=["bug", "research-agent", "user-reported"],
    orchestration={
        "agents_required": ["Research Agent", "Engineer Agent", "QA Agent"],
        "workflow": "investigate -> fix -> test"
    }
)

print(f"✅ Created ticket: {bug_id}")
print(f"   File: {bug_path}")

# Scenario 2: User requests a feature
print("\n\nScenario 2: User requests a feature")
print("User: 'Can you add support for GitLab integration alongside GitHub?'")
print("\nPM Action: Creating feature ticket...")

feat_id, feat_path = pm_create_ticket(
    ticket_type="FEAT",
    title="Add GitLab integration support",
    description="Add support for GitLab repositories in addition to GitHub. Should support same operations.",
    priority="medium",
    tags=["feature", "integration", "gitlab"],
    orchestration={
        "agents_required": ["Research Agent", "Engineer Agent", "Documentation Agent", "QA Agent"],
        "workflow": "research -> design -> implement -> document -> test"
    }
)

print(f"✅ Created ticket: {feat_id}")
print(f"   File: {feat_path}")

# Scenario 3: PM identifies improvement opportunity
print("\n\nScenario 3: PM identifies improvement opportunity")
print("PM: 'I notice we need better error handling in agent delegation'")
print("\nPM Action: Creating improvement ticket...")

improve_id, improve_path = pm_create_ticket(
    ticket_type="IMPROVE",
    title="Enhance error handling in agent delegation",
    description="Improve error handling and recovery when agent delegations fail. Add retry logic and better error messages.",
    priority="medium", 
    tags=["improvement", "error-handling", "agents"],
    orchestration={
        "agents_required": ["Engineer Agent", "QA Agent"],
        "workflow": "implement -> test"
    }
)

print(f"✅ Created ticket: {improve_id}")
print(f"   File: {improve_path}")

# Verify all tickets were created
print("\n\n=== Verification ===")
tickets_dir = Path("tasks")
all_tickets = list(tickets_dir.glob("*.json"))
print(f"Total tickets in system: {len(all_tickets)}")

print("\nListing all tickets:")
for ticket_file in sorted(all_tickets):
    with open(ticket_file, 'r') as f:
        ticket = json.load(f)
    
    status_icon = "🔴" if ticket["status"] == "open" else "🟡" if ticket["status"] == "in_progress" else "🟢"
    pm_icon = "🤖" if ticket.get("created_by") == "PM" else "👤"
    
    print(f"  {status_icon} {pm_icon} {ticket['id']}: {ticket['title']}")
    print(f"      Priority: {ticket['priority']} | Status: {ticket['status']}")
    
print("\n✅ PM can successfully create tickets programmatically!")
print("   This enables PM to track work items and coordinate agents effectively.")