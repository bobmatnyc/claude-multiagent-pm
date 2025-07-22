#!/usr/bin/env python3
"""
PM Orchestrator Demo
===================

Demonstrates the integrated ticketing functionality in PM orchestrator.
"""

import asyncio
from pathlib import Path
from claude_pm.services.pm_orchestrator import PMOrchestrator


def demo_basic_orchestration():
    """Demo basic PM orchestration with automatic ticketing."""
    print("=== PM Orchestrator Demo ===\n")
    
    # Initialize PM orchestrator
    orchestrator = PMOrchestrator()
    
    print("1. Simple task (no ticket):")
    prompt1 = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Fix a typo in the README file",
        requirements=["Find typo", "Fix it"],
        priority="low"
    )
    print(f"   Generated prompt for simple task\n")
    
    print("2. Complex task (automatic ticket):")
    prompt2 = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Implement OAuth2 authentication system",
        requirements=[
            "Design OAuth2 flow",
            "Implement authorization server",
            "Create token management",
            "Add refresh token support",
            "Implement PKCE for mobile clients"
        ],
        deliverables=[
            "OAuth2 server implementation",
            "Client libraries",
            "Token storage system",
            "Security documentation",
            "Integration tests"
        ],
        priority="high"
    )
    print(f"   Generated prompt with automatic ticket creation\n")
    
    # Check ticketing status
    status = orchestrator.get_ticketing_status()
    print(f"3. Ticketing Status:")
    print(f"   Ticketing enabled: {status['ticketing_enabled']}")
    print(f"   Active tickets: {status['active_tickets']}")
    if status['ticket_mappings']:
        print(f"   Ticket mappings:")
        for delegation_id, ticket_id in status['ticket_mappings'].items():
            print(f"     {delegation_id} -> {ticket_id}")
    print()


def demo_multi_agent_workflow():
    """Demo multi-agent workflow with coordinated ticketing."""
    print("=== Multi-Agent Workflow Demo ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create a complex workflow
    workflow = orchestrator.create_multi_agent_workflow(
        workflow_name="Implement Real-time Chat Feature",
        workflow_description="Add real-time chat functionality with WebSocket support",
        agent_tasks=[
            {
                "agent_type": "engineer",
                "task_description": "Build WebSocket server and client",
                "requirements": [
                    "WebSocket server implementation",
                    "Client connection management",
                    "Message broadcasting"
                ],
                "deliverables": [
                    "WebSocket server",
                    "Client library",
                    "Connection pool"
                ]
            },
            {
                "agent_type": "data_engineer",
                "task_description": "Design chat message storage",
                "requirements": [
                    "Message schema design",
                    "Indexing strategy",
                    "Archive system"
                ],
                "deliverables": [
                    "Database schema",
                    "Migration scripts",
                    "Performance benchmarks"
                ],
                "depends_on": ["engineer"]
            },
            {
                "agent_type": "security",
                "task_description": "Security audit and hardening",
                "requirements": [
                    "Authentication for WebSocket",
                    "Message encryption",
                    "Rate limiting"
                ],
                "deliverables": [
                    "Security report",
                    "Implementation guidelines",
                    "Penetration test results"
                ],
                "depends_on": ["engineer", "data_engineer"]
            },
            {
                "agent_type": "qa",
                "task_description": "Comprehensive testing",
                "requirements": [
                    "Load testing",
                    "Security testing",
                    "Cross-browser testing"
                ],
                "deliverables": [
                    "Test report",
                    "Performance metrics",
                    "Bug list"
                ],
                "depends_on": ["security"]
            }
        ],
        priority="critical"
    )
    
    print(f"Created workflow: {workflow['workflow_id']}")
    print(f"Master ticket: {workflow.get('master_ticket_id', 'N/A')}")
    print(f"Total tasks: {len(workflow['agent_tasks'])}")
    print(f"Tickets created: {len(workflow.get('tickets', []))}")
    
    # Show dependencies
    print("\nTask Dependencies:")
    for task in workflow['agent_tasks']:
        deps = task.get('depends_on', [])
        if deps:
            print(f"  {task['agent_type']} depends on: {', '.join(deps)}")


def demo_progress_tracking():
    """Demo progress tracking with ticket updates."""
    print("\n=== Progress Tracking Demo ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create a task that will get a ticket
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Migrate monolith to microservices architecture",
        requirements=[
            "Service decomposition analysis",
            "API gateway design",
            "Service mesh implementation",
            "Data consistency strategy"
        ],
        priority="high"
    )
    
    # Get the delegation ID
    delegation_id = orchestrator._delegation_history[-1]["delegation_id"]
    ticket_id = orchestrator._delegation_history[-1].get("ticket_id")
    
    print(f"Created task delegation: {delegation_id}")
    if ticket_id:
        print(f"Associated ticket: {ticket_id}")
    
    # Simulate progress updates
    print("\nSimulating progress updates:")
    
    progress_updates = [
        ("Started service decomposition analysis", "in_progress"),
        ("Identified 5 bounded contexts for separation", "in_progress"),
        ("Encountered data consistency challenges", "blocked"),
        ("Resolved with event sourcing pattern", "in_progress")
    ]
    
    for progress, status in progress_updates:
        success = orchestrator.update_delegation_progress(
            delegation_id=delegation_id,
            progress=progress,
            status=status
        )
        print(f"  [{status}] {progress}")
    
    # Complete the task
    print("\nCompleting task...")
    results = {
        "success": True,
        "summary": "Successfully decomposed monolith into 5 microservices"
    }
    
    orchestrator.complete_delegation(delegation_id, results)
    print("Task completed and ticket updated!")


def demo_workload_analysis():
    """Demo agent workload analysis."""
    print("\n=== Workload Analysis Demo ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create several tasks to show workload
    tasks = [
        ("engineer", "API development", "high"),
        ("engineer", "Bug fixes", "medium"),
        ("qa", "Test automation", "high"),
        ("security", "Vulnerability scan", "critical"),
        ("documentation", "API docs update", "medium")
    ]
    
    print("Creating sample tasks...")
    for agent, desc, priority in tasks:
        orchestrator.generate_agent_prompt(
            agent_type=agent,
            task_description=desc,
            requirements=["Req 1", "Req 2", "Req 3"],  # Trigger ticket creation
            priority=priority
        )
    
    # Get workload status
    status = orchestrator.get_ticketing_status()
    
    print(f"\nTicketing Overview:")
    print(f"  Total active tickets: {status['active_tickets']}")
    
    if 'agent_workload' in status:
        print("\nAgent Workload:")
        for agent, workload in status['agent_workload'].items():
            if workload['total_tickets'] > 0:
                print(f"  {agent}:")
                print(f"    Total: {workload['total_tickets']}")
                print(f"    High priority: {workload['high_priority']}")
                print(f"    Critical: {workload['critical_priority']}")


if __name__ == "__main__":
    print("Claude PM - PM Orchestrator with Ticketing Integration\n")
    
    # Run demos
    demo_basic_orchestration()
    demo_multi_agent_workflow()
    demo_progress_tracking()
    demo_workload_analysis()
    
    print("\n✅ Demo completed!")
    print("\nKey Features Demonstrated:")
    print("- Automatic ticket creation for complex tasks")
    print("- Multi-agent workflow orchestration")
    print("- Progress tracking with ticket updates")
    print("- Workload analysis across agents")
    print("\nPM now automatically tracks complex work via tickets!")