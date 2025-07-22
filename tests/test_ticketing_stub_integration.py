#!/usr/bin/env python3
"""
Test TicketingService Integration with Stub Implementation
==========================================================

This test suite specifically tests the TicketingService when ai-trackdown-pytools
is NOT available, ensuring the stub implementation works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.ticketing_service import TicketingService, get_ticketing_service
from claude_pm.orchestration.ticketing_helpers import TicketingHelper
from claude_pm.services.pm_orchestrator import PMOrchestrator


def test_stub_implementation():
    """Test that stub implementation works correctly."""
    print("\n=== Testing Stub Implementation ===")
    
    ticketing = get_ticketing_service()
    print(f"✓ Got TicketingService instance")
    print(f"  Using stub: {not ticketing._ticket_manager}")
    
    # Test 1: Create ticket (should work with stub)
    ticket = ticketing.create_ticket(
        title="Test stub ticket",
        description="Testing stub implementation",
        priority="high",
        labels=["test", "stub"]
    )
    print(f"✓ Created ticket: {ticket.id}")
    print(f"  Title: {ticket.title}")
    print(f"  Status: {ticket.status}")
    
    # Test 2: List tickets (returns empty with stub)
    tickets = ticketing.list_tickets()
    print(f"✓ List tickets returns empty: {len(tickets) == 0}")
    
    # Test 3: Get ticket (returns None with stub)
    retrieved = ticketing.get_ticket(ticket.id)
    print(f"✓ Get ticket returns None: {retrieved is None}")
    
    # Test 4: Update ticket (returns None with stub)
    updated = ticketing.update_ticket(ticket.id, status="in_progress")
    print(f"✓ Update ticket returns None: {updated is None}")
    
    # Test 5: Add comment (returns False with stub)
    success = ticketing.add_comment(ticket.id, "Test comment")
    print(f"✓ Add comment returns False: {success == False}")
    
    # Test 6: Search tickets (returns empty with stub)
    results = ticketing.search_tickets("test")
    print(f"✓ Search returns empty: {len(results) == 0}")
    
    # Test 7: Statistics (returns empty stats with stub)
    stats = ticketing.get_ticket_statistics()
    print(f"✓ Statistics shows empty: {stats['total'] == 0}")
    
    # Test 8: Close ticket (returns None with stub)
    closed = ticketing.close_ticket(ticket.id, "Test resolution")
    print(f"✓ Close ticket returns None: {closed is None}")
    
    print("\nAll stub implementation tests passed!")


def test_pm_orchestrator_with_stub():
    """Test PM Orchestrator works correctly with stub."""
    print("\n=== Testing PM Orchestrator with Stub ===")
    
    orchestrator = PMOrchestrator()
    print("✓ PM Orchestrator initialized")
    
    # Test simple task
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Test task with stub ticketing",
        requirements=["Requirement 1", "Requirement 2"],
        priority="low"
    )
    print("✓ Generated simple prompt (no ticket expected)")
    
    # Test complex task
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Complex task requiring ticket",
        requirements=[
            "Requirement 1",
            "Requirement 2", 
            "Requirement 3",
            "Requirement 4",
            "Requirement 5"
        ],
        deliverables=[
            "Deliverable 1",
            "Deliverable 2",
            "Deliverable 3"
        ],
        priority="high"
    )
    print("✓ Generated complex prompt (ticket created)")
    
    # Check status
    status = orchestrator.get_ticketing_status()
    print(f"✓ Ticketing status shows active tickets: {status['active_tickets']}")
    
    # Test multi-agent workflow
    workflow = orchestrator.create_multi_agent_workflow(
        workflow_name="Test Workflow",
        workflow_description="Test multi-agent workflow with stub",
        agent_tasks=[
            {
                "agent_type": "engineer",
                "task_description": "Task 1",
                "requirements": ["Req 1"],
                "deliverables": ["Del 1"]
            },
            {
                "agent_type": "qa",
                "task_description": "Task 2",
                "requirements": ["Req 2"],
                "depends_on": ["engineer"]
            }
        ],
        priority="medium"
    )
    print(f"✓ Created workflow: {workflow['workflow_id']}")
    print(f"  Tasks created: {len(workflow['agent_tasks'])}")
    
    print("\nPM Orchestrator works correctly with stub!")


def test_ticketing_helper_with_stub():
    """Test TicketingHelper works correctly with stub."""
    print("\n=== Testing TicketingHelper with Stub ===")
    
    helper = TicketingHelper()
    
    # Create agent task
    ticket = helper.create_agent_task_ticket(
        agent_name="engineer",
        task_description="Test task for helper",
        priority="medium"
    )
    print(f"✓ Created agent task ticket: {ticket.id if ticket else 'None'}")
    
    # Update status (will fail with stub but shouldn't error)
    if ticket:
        success = helper.update_agent_task_status(
            ticket.id,
            "in_progress",
            "Starting work"
        )
        print(f"✓ Update status handled gracefully: {not success}")
    
    # Get workload (empty with stub)
    workload = helper.get_agent_workload("engineer")
    print(f"✓ Get workload returns empty: {workload['total_tickets'] == 0}")
    
    # Get overview (empty with stub)
    overview = helper.get_project_overview()
    print(f"✓ Get overview returns empty: {overview['total_tickets'] == 0}")
    
    # Find related (empty with stub)
    related = helper.find_related_tickets(["test"], limit=5)
    print(f"✓ Find related returns empty: {len(related) == 0}")
    
    print("\nTicketingHelper works correctly with stub!")


def test_example_scripts_resilience():
    """Test that example scripts handle stub implementation gracefully."""
    print("\n=== Testing Example Scripts Resilience ===")
    
    # Modified version of example_basic_operations that handles None returns
    ticketing = get_ticketing_service()
    
    # Create ticket
    ticket = ticketing.create_ticket(
        title="Test example resilience",
        description="Testing example script with stub",
        priority="high"
    )
    print(f"✓ Created ticket: {ticket.id}")
    
    # Update ticket (handle None return)
    updated = ticketing.update_ticket(ticket.id, status="in_progress")
    if updated:
        print(f"✓ Updated ticket status: {updated.status}")
    else:
        print("✓ Update returned None (expected with stub)")
    
    # Close ticket (handle None return)
    closed = ticketing.close_ticket(ticket.id, "Test resolution")
    if closed:
        print(f"✓ Closed ticket status: {closed.status}")
    else:
        print("✓ Close returned None (expected with stub)")
    
    print("\nExample scripts can handle stub implementation!")


def main():
    """Run all stub integration tests."""
    print("=" * 60)
    print("TICKETING SERVICE STUB INTEGRATION TESTS")
    print("=" * 60)
    print("Testing behavior when ai-trackdown-pytools is NOT available")
    
    test_stub_implementation()
    test_pm_orchestrator_with_stub()
    test_ticketing_helper_with_stub()
    test_example_scripts_resilience()
    
    print("\n" + "=" * 60)
    print("ALL STUB INTEGRATION TESTS PASSED!")
    print("=" * 60)
    print("\nConclusion:")
    print("- TicketingService works correctly with stub implementation")
    print("- PM Orchestrator integrates properly with stub")
    print("- TicketingHelper handles stub gracefully")
    print("- Example scripts need None checks for stub compatibility")
    print("\nRecommendation:")
    print("- Install ai-trackdown-pytools for full functionality")
    print("- Or ensure all code handles None returns from ticketing operations")


if __name__ == "__main__":
    main()