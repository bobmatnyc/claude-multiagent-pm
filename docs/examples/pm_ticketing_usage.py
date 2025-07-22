#!/usr/bin/env python3
"""
PM Orchestrator Ticketing Usage Examples
=======================================

Examples of how the PM orchestrator uses ticketing for task management.
"""

from claude_pm.services.pm_orchestrator import PMOrchestrator


def example_basic_ticketing():
    """Example of basic ticket creation for complex tasks."""
    print("=== Basic Ticketing Example ===\n")
    
    # Initialize PM orchestrator
    orchestrator = PMOrchestrator()
    
    # Create a complex task that will automatically generate a ticket
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Implement user authentication system with JWT tokens",
        requirements=[
            "OAuth2 integration",
            "JWT token generation and validation",
            "Secure password hashing",
            "Session management",
            "Role-based access control"
        ],
        deliverables=[
            "Authentication API endpoints",
            "JWT middleware",
            "User model and database schema",
            "Unit tests with 90% coverage",
            "API documentation"
        ],
        priority="high"
    )
    
    print("Generated prompt with automatic ticket creation:")
    print("-" * 50)
    print(prompt[:500] + "...")
    print("\n")
    
    # Check ticketing status
    status = orchestrator.get_ticketing_status()
    print(f"Active tickets: {status['active_tickets']}")
    print(f"Ticket mappings: {status['ticket_mappings']}")


def example_multi_agent_workflow():
    """Example of multi-agent workflow with ticketing."""
    print("\n=== Multi-Agent Workflow Example ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create a complex workflow that requires multiple agents
    workflow = orchestrator.create_multi_agent_workflow(
        workflow_name="Release Version 2.0",
        workflow_description="Complete release process for version 2.0 including development, testing, and deployment",
        agent_tasks=[
            {
                "agent_type": "engineer",
                "task_description": "Implement remaining features for v2.0",
                "requirements": [
                    "Complete API v2 endpoints",
                    "Implement new dashboard UI",
                    "Add performance optimizations"
                ],
                "deliverables": [
                    "Completed feature code",
                    "Unit tests",
                    "Performance benchmarks"
                ]
            },
            {
                "agent_type": "qa",
                "task_description": "Comprehensive testing of v2.0 features",
                "requirements": [
                    "Test all new features",
                    "Regression testing",
                    "Performance testing",
                    "Security testing"
                ],
                "deliverables": [
                    "Test report",
                    "Bug list",
                    "Performance metrics",
                    "Security audit"
                ],
                "depends_on": ["engineer"]
            },
            {
                "agent_type": "documentation",
                "task_description": "Update all documentation for v2.0",
                "requirements": [
                    "Update API documentation",
                    "Create migration guide",
                    "Update user manual"
                ],
                "deliverables": [
                    "API reference v2.0",
                    "Migration guide",
                    "Updated user documentation",
                    "Release notes"
                ],
                "depends_on": ["engineer", "qa"]
            },
            {
                "agent_type": "ops",
                "task_description": "Deploy v2.0 to production",
                "requirements": [
                    "Prepare deployment scripts",
                    "Database migrations",
                    "Zero-downtime deployment"
                ],
                "deliverables": [
                    "Deployment completed",
                    "Monitoring configured",
                    "Rollback plan ready"
                ],
                "depends_on": ["qa", "documentation"]
            }
        ],
        priority="critical"
    )
    
    print(f"Created workflow: {workflow['workflow_id']}")
    print(f"Master ticket: {workflow.get('master_ticket_id', 'N/A')}")
    print(f"Agent tasks created: {len(workflow['agent_tasks'])}")
    print(f"Tickets created: {len(workflow['tickets'])}")
    
    # Show task dependencies
    print("\nTask Dependencies:")
    for task in workflow['agent_tasks']:
        deps = task.get('depends_on', [])
        if deps:
            print(f"  {task['agent_type']} depends on: {', '.join(deps)}")


def example_progress_tracking():
    """Example of tracking progress with ticket updates."""
    print("\n=== Progress Tracking Example ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create a task
    prompt = orchestrator.generate_agent_prompt(
        agent_type="data_engineer",
        task_description="Migrate database from PostgreSQL to distributed architecture",
        requirements=[
            "Design distributed schema",
            "Create migration scripts",
            "Implement data synchronization",
            "Zero data loss guarantee"
        ],
        deliverables=[
            "Distributed database design",
            "Migration scripts and tools",
            "Data validation reports",
            "Performance benchmarks"
        ],
        priority="high"
    )
    
    # Get delegation ID
    delegation_id = orchestrator._delegation_history[-1]["delegation_id"]
    print(f"Created delegation: {delegation_id}")
    
    # Simulate progress updates
    progress_updates = [
        ("Completed schema design, starting migration script development", "in_progress"),
        ("Migration scripts ready, testing on staging environment", "in_progress"),
        ("Issue found: performance degradation in distributed queries", "blocked"),
        ("Resolved performance issue with query optimization", "in_progress"),
        ("All tests passing, ready for production migration", "in_progress")
    ]
    
    for progress, status in progress_updates:
        success = orchestrator.update_delegation_progress(
            delegation_id=delegation_id,
            progress=progress,
            status=status
        )
        print(f"Progress update ({status}): {progress}")
    
    # Complete the task
    results = {
        "success": True,
        "summary": "Database successfully migrated to distributed architecture. Performance improved by 3x."
    }
    
    orchestrator.complete_delegation(delegation_id, results)
    print("\nTask completed successfully!")


def example_workload_analysis():
    """Example of analyzing agent workload through tickets."""
    print("\n=== Workload Analysis Example ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Create several tasks for different agents
    tasks = [
        ("engineer", "Implement new API endpoints", ["high", "medium", "medium"]),
        ("qa", "Test new features", ["medium", "high", "low"]),
        ("documentation", "Update API docs", ["medium", "low"]),
        ("security", "Security audit", ["critical"]),
        ("engineer", "Fix critical bugs", ["critical", "high"]),
        ("data_engineer", "Optimize database queries", ["medium", "medium"])
    ]
    
    for agent, description, priorities in tasks:
        for priority in priorities:
            orchestrator.generate_agent_prompt(
                agent_type=agent,
                task_description=f"{description} - Priority: {priority}",
                requirements=["Requirement 1", "Requirement 2", "Requirement 3"],
                priority=priority
            )
    
    # Get ticketing status with workload
    status = orchestrator.get_ticketing_status()
    
    print("Agent Workload Summary:")
    print("-" * 50)
    
    if "agent_workload" in status:
        for agent, workload in status["agent_workload"].items():
            print(f"\n{agent.upper()} Agent:")
            print(f"  Total tickets: {workload['total_tickets']}")
            print(f"  Open: {workload['open']}")
            print(f"  In Progress: {workload['in_progress']}")
            print(f"  High Priority: {workload['high_priority']}")
            print(f"  Critical: {workload['critical_priority']}")
    
    if "project_overview" in status:
        overview = status["project_overview"]
        print(f"\nProject Overview:")
        print(f"  Total tickets: {overview.get('total_tickets', 0)}")
        print(f"  Agent tasks: {overview.get('agent_tasks', 0)}")
        print(f"  Status breakdown: {overview.get('by_status', {})}")


def example_conditional_ticketing():
    """Example showing when tickets are and aren't created."""
    print("\n=== Conditional Ticketing Example ===\n")
    
    orchestrator = PMOrchestrator()
    
    # Simple task - no ticket
    print("1. Simple task (no ticket expected):")
    prompt1 = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Fix typo in README",
        requirements=["Find typo", "Fix it"],
        priority="low"
    )
    
    # Complex task - ticket created
    print("\n2. Complex task (ticket expected):")
    prompt2 = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Refactor authentication system for microservices",
        requirements=[
            "Design new auth architecture",
            "Implement service-to-service auth",
            "Create auth gateway",
            "Update all services"
        ],
        deliverables=[
            "Architecture design doc",
            "Auth service implementation",
            "Service migration guide",
            "Integration tests"
        ],
        priority="medium"  # Even medium priority gets ticket due to complexity
    )
    
    # High priority - always gets ticket
    print("\n3. High priority task (ticket expected):")
    prompt3 = orchestrator.generate_agent_prompt(
        agent_type="security",
        task_description="Fix security vulnerability",
        requirements=["Patch vulnerability", "Test fix"],
        priority="critical"
    )
    
    # Multi-agent coordination - ticket created
    print("\n4. Multi-agent task (ticket expected):")
    prompt4 = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Coordinate with multiple agents to implement new feature",
        requirements=["Design feature", "Implement code"],
        priority="medium"
    )
    
    # Check which tasks got tickets
    status = orchestrator.get_ticketing_status()
    print(f"\nTotal tickets created: {status['active_tickets']}")
    print("Ticket mappings:")
    for delegation_id, ticket_id in status['ticket_mappings'].items():
        agent_type = delegation_id.split('_')[0]
        print(f"  {agent_type} task -> Ticket {ticket_id}")


if __name__ == "__main__":
    # Run all examples
    example_basic_ticketing()
    example_multi_agent_workflow()
    example_progress_tracking()
    example_workload_analysis()
    example_conditional_ticketing()