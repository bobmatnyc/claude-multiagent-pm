#!/usr/bin/env python3
"""
Comprehensive Test Suite for TicketingService Integration
=========================================================

Tests all aspects of TicketingService integration:
1. TicketingService core functionality
2. PM orchestrator automatic ticket creation
3. Multi-agent workflow scenarios
4. Error handling and edge cases
5. Example scripts functionality
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.ticketing_service import TicketingService, TicketData, get_ticketing_service
from claude_pm.orchestration.ticketing_helpers import TicketingHelper, quick_create_task, get_workload_summary
from claude_pm.services.pm_orchestrator import PMOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results and generate report."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_test(self, name: str, passed: bool, details: str = "", error: Exception = None):
        """Add test result."""
        self.results.append({
            "name": name,
            "passed": passed,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            if error:
                self.errors.append((name, error))
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({self.passed/total*100:.1f}%)")
        print(f"Failed: {self.failed} ({self.failed/total*100:.1f}%)")
        
        if self.errors:
            print("\nErrors:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        print("=" * 70)
    
    def save_report(self, filename: str):
        """Save detailed report to file."""
        report = {
            "summary": {
                "total": self.passed + self.failed,
                "passed": self.passed,
                "failed": self.failed,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results,
            "errors": [(name, str(error)) for name, error in self.errors]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {filename}")


def test_ticketing_service_core(results: TestResults):
    """Test core TicketingService functionality."""
    print("\n=== Testing Core TicketingService ===")
    
    # Test 1: Get singleton instance
    try:
        ticketing = get_ticketing_service()
        results.add_test("Get TicketingService instance", True, f"Instance: {ticketing}")
    except Exception as e:
        results.add_test("Get TicketingService instance", False, error=e)
        return
    
    # Test 2: Create ticket
    try:
        ticket = ticketing.create_ticket(
            title="Test ticket - Core functionality",
            description="Testing core TicketingService create functionality",
            priority="high",
            labels=["test", "core"]
        )
        results.add_test("Create ticket", True, f"Created ticket: {ticket.id}")
        created_ticket_id = ticket.id
    except Exception as e:
        results.add_test("Create ticket", False, error=e)
        created_ticket_id = None
    
    # Test 3: List tickets
    try:
        tickets = ticketing.list_tickets(limit=10)
        results.add_test("List tickets", True, f"Found {len(tickets)} tickets")
    except Exception as e:
        results.add_test("List tickets", False, error=e)
    
    # Test 4: Get specific ticket
    try:
        if created_ticket_id:
            ticket = ticketing.get_ticket(created_ticket_id)
            results.add_test("Get specific ticket", ticket is not None, 
                           f"Retrieved: {ticket.id if ticket else 'None'}")
        else:
            results.add_test("Get specific ticket", False, "No ticket ID available")
    except Exception as e:
        results.add_test("Get specific ticket", False, error=e)
    
    # Test 5: Update ticket
    try:
        if created_ticket_id:
            updated = ticketing.update_ticket(
                created_ticket_id,
                status="in_progress",
                assignee="test-agent"
            )
            results.add_test("Update ticket", updated is not None,
                           f"Updated status: {updated.status if updated else 'Failed'}")
        else:
            results.add_test("Update ticket", False, "No ticket ID available")
    except Exception as e:
        results.add_test("Update ticket", False, error=e)
    
    # Test 6: Add comment
    try:
        if created_ticket_id:
            success = ticketing.add_comment(
                created_ticket_id,
                "Test comment from comprehensive test suite",
                author="test-suite"
            )
            results.add_test("Add comment", success, f"Comment added: {success}")
        else:
            results.add_test("Add comment", False, "No ticket ID available")
    except Exception as e:
        results.add_test("Add comment", False, error=e)
    
    # Test 7: Search tickets
    try:
        search_results = ticketing.search_tickets("test", limit=5)
        results.add_test("Search tickets", True, f"Found {len(search_results)} results")
    except Exception as e:
        results.add_test("Search tickets", False, error=e)
    
    # Test 8: Get statistics
    try:
        stats = ticketing.get_ticket_statistics()
        results.add_test("Get statistics", True, f"Stats: {stats}")
    except Exception as e:
        results.add_test("Get statistics", False, error=e)
    
    # Test 9: Close ticket
    try:
        if created_ticket_id:
            closed = ticketing.close_ticket(
                created_ticket_id,
                resolution="Test completed successfully"
            )
            results.add_test("Close ticket", closed is not None,
                           f"Closed ticket: {closed.id if closed else 'Failed'}")
        else:
            results.add_test("Close ticket", False, "No ticket ID available")
    except Exception as e:
        results.add_test("Close ticket", False, error=e)


def test_ticketing_helpers(results: TestResults):
    """Test TicketingHelper functionality."""
    print("\n=== Testing TicketingHelper ===")
    
    helper = TicketingHelper()
    
    # Test 1: Create agent task ticket
    try:
        ticket = helper.create_agent_task_ticket(
            agent_name="engineer",
            task_description="Implement test feature for helper validation",
            priority="medium",
            additional_context={"test": True, "suite": "comprehensive"}
        )
        results.add_test("Create agent task ticket", ticket is not None,
                       f"Created: {ticket.id if ticket else 'Failed'}")
        helper_ticket_id = ticket.id if ticket else None
    except Exception as e:
        results.add_test("Create agent task ticket", False, error=e)
        helper_ticket_id = None
    
    # Test 2: Update agent task status
    try:
        if helper_ticket_id:
            success = helper.update_agent_task_status(
                helper_ticket_id,
                "in_progress",
                "Starting work on test feature"
            )
            results.add_test("Update agent task status", success,
                           f"Updated: {success}")
        else:
            results.add_test("Update agent task status", False, "No ticket ID")
    except Exception as e:
        results.add_test("Update agent task status", False, error=e)
    
    # Test 3: Get agent workload
    try:
        workload = helper.get_agent_workload("engineer")
        results.add_test("Get agent workload", True,
                       f"Engineer workload: {workload}")
    except Exception as e:
        results.add_test("Get agent workload", False, error=e)
    
    # Test 4: Get project overview
    try:
        overview = helper.get_project_overview()
        results.add_test("Get project overview", True,
                       f"Overview: Total tickets = {overview.get('total_tickets', 0)}")
    except Exception as e:
        results.add_test("Get project overview", False, error=e)
    
    # Test 5: Find related tickets
    try:
        related = helper.find_related_tickets(["test", "engineer"], limit=5)
        results.add_test("Find related tickets", True,
                       f"Found {len(related)} related tickets")
    except Exception as e:
        results.add_test("Find related tickets", False, error=e)
    
    # Test 6: Quick create task
    try:
        quick_ticket_id = quick_create_task("qa", "Test quick task creation", "low")
        results.add_test("Quick create task", quick_ticket_id is not None,
                       f"Created: {quick_ticket_id}")
    except Exception as e:
        results.add_test("Quick create task", False, error=e)
    
    # Test 7: Get workload summary
    try:
        summary = get_workload_summary()
        results.add_test("Get workload summary", True,
                       f"Agents with tasks: {list(summary.keys())}")
    except Exception as e:
        results.add_test("Get workload summary", False, error=e)


def test_pm_orchestrator_integration(results: TestResults):
    """Test PM Orchestrator ticketing integration."""
    print("\n=== Testing PM Orchestrator Integration ===")
    
    try:
        orchestrator = PMOrchestrator()
        results.add_test("Initialize PM Orchestrator", True)
    except Exception as e:
        results.add_test("Initialize PM Orchestrator", False, error=e)
        return
    
    # Test 1: Simple task (no ticket expected)
    try:
        prompt = orchestrator.generate_agent_prompt(
            agent_type="engineer",
            task_description="Fix typo in comment",
            requirements=["Find typo", "Fix it"],
            priority="low"
        )
        results.add_test("Generate simple prompt (no ticket)", True,
                       "Prompt generated for simple task")
    except Exception as e:
        results.add_test("Generate simple prompt (no ticket)", False, error=e)
    
    # Test 2: Complex task (ticket expected)
    try:
        prompt = orchestrator.generate_agent_prompt(
            agent_type="engineer",
            task_description="Implement comprehensive authentication system",
            requirements=[
                "Design auth architecture",
                "Implement OAuth2 flow",
                "Create JWT handling",
                "Add session management",
                "Implement RBAC"
            ],
            deliverables=[
                "Auth service implementation",
                "API documentation",
                "Integration tests",
                "Security audit report"
            ],
            priority="high"
        )
        results.add_test("Generate complex prompt (ticket expected)", True,
                       "Prompt generated for complex task")
    except Exception as e:
        results.add_test("Generate complex prompt (ticket expected)", False, error=e)
    
    # Test 3: Multi-agent workflow
    try:
        workflow = orchestrator.create_multi_agent_workflow(
            workflow_name="Test Feature Release",
            workflow_description="Complete test feature implementation and release",
            agent_tasks=[
                {
                    "agent_type": "engineer",
                    "task_description": "Implement test feature",
                    "requirements": ["Design feature", "Write code", "Unit tests"],
                    "deliverables": ["Feature code", "Tests"]
                },
                {
                    "agent_type": "qa",
                    "task_description": "Test the feature",
                    "requirements": ["Integration tests", "E2E tests"],
                    "deliverables": ["Test report"],
                    "depends_on": ["engineer"]
                },
                {
                    "agent_type": "documentation",
                    "task_description": "Document the feature",
                    "requirements": ["API docs", "User guide"],
                    "deliverables": ["Documentation"],
                    "depends_on": ["engineer", "qa"]
                }
            ],
            priority="medium"
        )
        results.add_test("Create multi-agent workflow", True,
                       f"Workflow created: {workflow.get('workflow_id', 'Unknown')}")
    except Exception as e:
        results.add_test("Create multi-agent workflow", False, error=e)
    
    # Test 4: Get ticketing status
    try:
        status = orchestrator.get_ticketing_status()
        results.add_test("Get ticketing status", True,
                       f"Active tickets: {status.get('active_tickets', 0)}")
    except Exception as e:
        results.add_test("Get ticketing status", False, error=e)
    
    # Test 5: Update delegation progress
    try:
        if orchestrator._delegation_history:
            delegation_id = orchestrator._delegation_history[-1]["delegation_id"]
            success = orchestrator.update_delegation_progress(
                delegation_id,
                "Test progress update",
                "in_progress"
            )
            results.add_test("Update delegation progress", success,
                           f"Updated delegation: {delegation_id}")
        else:
            results.add_test("Update delegation progress", False,
                           "No delegations available")
    except Exception as e:
        results.add_test("Update delegation progress", False, error=e)


def test_error_handling(results: TestResults):
    """Test error handling and edge cases."""
    print("\n=== Testing Error Handling ===")
    
    ticketing = get_ticketing_service()
    
    # Test 1: Invalid ticket ID
    try:
        ticket = ticketing.get_ticket("INVALID-ID-12345")
        results.add_test("Get invalid ticket", ticket is None,
                       "Correctly returned None for invalid ID")
    except Exception as e:
        results.add_test("Get invalid ticket", False, error=e)
    
    # Test 2: Update non-existent ticket
    try:
        updated = ticketing.update_ticket("INVALID-ID-12345", status="closed")
        results.add_test("Update non-existent ticket", updated is None,
                       "Correctly returned None for invalid update")
    except Exception as e:
        results.add_test("Update non-existent ticket", False, error=e)
    
    # Test 3: Empty search
    try:
        results_list = ticketing.search_tickets("", limit=5)
        results.add_test("Empty search query", True,
                       f"Handled empty search: {len(results_list)} results")
    except Exception as e:
        results.add_test("Empty search query", False, error=e)
    
    # Test 4: Invalid priority
    try:
        ticket = ticketing.create_ticket(
            title="Test invalid priority",
            description="Testing invalid priority handling",
            priority="invalid_priority"
        )
        results.add_test("Create ticket with invalid priority", True,
                       "Handled invalid priority gracefully")
    except Exception as e:
        results.add_test("Create ticket with invalid priority", False, error=e)
    
    # Test 5: Large batch operations
    try:
        helper = TicketingHelper()
        # Create multiple tickets rapidly
        for i in range(5):
            helper.create_agent_task_ticket(
                agent_name="test",
                task_description=f"Batch test task {i}",
                priority="low"
            )
        results.add_test("Batch ticket creation", True,
                       "Created 5 tickets in batch")
    except Exception as e:
        results.add_test("Batch ticket creation", False, error=e)


def test_example_scripts(results: TestResults):
    """Test that example scripts work correctly."""
    print("\n=== Testing Example Scripts ===")
    
    # Test 1: Basic ticketing example
    try:
        from docs.examples.ticketing_service_examples import example_basic_operations
        # Run basic usage example
        example_basic_operations()
        results.add_test("Run basic usage example", True,
                       "Basic example executed successfully")
    except Exception as e:
        results.add_test("Run basic usage example", False, error=e)
    
    # Test 2: PM ticketing usage example functions
    try:
        from docs.examples.pm_ticketing_usage import (
            example_basic_ticketing,
            example_conditional_ticketing
        )
        
        # Run basic ticketing example
        example_basic_ticketing()
        results.add_test("Run PM basic ticketing example", True,
                       "PM basic example executed successfully")
        
        # Run conditional ticketing example
        example_conditional_ticketing()
        results.add_test("Run PM conditional ticketing example", True,
                       "PM conditional example executed successfully")
    except Exception as e:
        results.add_test("Run PM ticketing examples", False, error=e)


def run_all_tests():
    """Run all comprehensive tests."""
    print("=" * 70)
    print("COMPREHENSIVE TICKETING SERVICE INTEGRATION TEST")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    
    results = TestResults()
    
    # Run test suites
    test_ticketing_service_core(results)
    test_ticketing_helpers(results)
    test_pm_orchestrator_integration(results)
    test_error_handling(results)
    test_example_scripts(results)
    
    # Print summary
    results.print_summary()
    
    # Save detailed report
    report_path = Path(__file__).parent / "reports" / "ticketing_integration_test_report.json"
    report_path.parent.mkdir(exist_ok=True)
    results.save_report(str(report_path))
    
    # Return success/failure
    return results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)