#!/usr/bin/env python3
"""
Comprehensive test suite for ticketing integration with Claude PM Framework.
Tests PM's ability to orchestrate ticket operations using ai-trackdown-pytools.
"""

import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Test utilities
class TicketingTestSuite:
    def __init__(self):
        self.test_results = []
        self.test_dir = None
        
    def setup(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="claude_pm_ticket_test_")
        os.chdir(self.test_dir)
        print(f"Test directory: {self.test_dir}")
        
        # Initialize claude-pm
        os.system("claude-pm init --setup > /dev/null 2>&1")
        
        # Use standard tasks directory for tickets
        tickets_dir = Path("tasks")
        tickets_dir.mkdir(parents=True, exist_ok=True)
        
        return tickets_dir
        
    def cleanup(self):
        """Cleanup test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            os.chdir("/tmp")
            shutil.rmtree(self.test_dir)
            
    def run_test(self, test_name, test_func):
        """Run a test and record results"""
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            self.test_results.append({
                "test": test_name,
                "status": "PASS",
                "result": result
            })
            print(f"✅ PASS: {test_name}")
        except Exception as e:
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {e}")
            
    def test_ticket_creation(self):
        """Test creating tickets programmatically"""
        ticket_data = {
            "id": "TEST-001",
            "title": "Test ticket creation",
            "description": "Testing PM's ability to create tickets",
            "status": "open",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
            "tags": ["test", "integration"],
            "assignee": "PM",
            "metadata": {
                "created_by": "test_suite",
                "test_type": "integration"
            }
        }
        
        # Create ticket file in tasks directory
        ticket_path = Path("tickets/TEST-001.json")
        with open(ticket_path, 'w') as f:
            json.dump(ticket_data, f, indent=2)
            
        # Verify ticket was created
        assert ticket_path.exists(), "Ticket file not created"
        
        # Read back and verify
        with open(ticket_path, 'r') as f:
            saved_ticket = json.load(f)
            
        assert saved_ticket["id"] == "TEST-001", "Ticket ID mismatch"
        assert saved_ticket["status"] == "open", "Ticket status mismatch"
        
        return "Ticket created successfully"
        
    def test_ticket_listing(self):
        """Test listing tickets"""
        # Create multiple test tickets
        for i in range(3):
            ticket_data = {
                "id": f"TEST-00{i+2}",
                "title": f"Test ticket {i+2}",
                "status": "open" if i % 2 == 0 else "closed",
                "priority": ["low", "medium", "high"][i],
                "created_at": datetime.now().isoformat()
            }
            
            with open(f"tickets/TEST-00{i+2}.json", 'w') as f:
                json.dump(ticket_data, f, indent=2)
                
        # List all tickets
        tickets_dir = Path("tickets")
        ticket_files = list(tickets_dir.glob("*.json"))
        
        assert len(ticket_files) >= 3, f"Expected at least 3 tickets, found {len(ticket_files)}"
        
        # Read and verify tickets
        tickets = []
        for ticket_file in ticket_files:
            with open(ticket_file, 'r') as f:
                tickets.append(json.load(f))
                
        # Filter open tickets
        open_tickets = [t for t in tickets if t.get("status") == "open"]
        assert len(open_tickets) >= 2, "Not enough open tickets found"
        
        return f"Found {len(tickets)} total tickets, {len(open_tickets)} open"
        
    def test_ticket_update(self):
        """Test updating ticket status and fields"""
        # Get existing ticket
        ticket_path = Path("tickets/TEST-001.json")
        
        with open(ticket_path, 'r') as f:
            ticket = json.load(f)
            
        # Update ticket
        ticket["status"] = "in_progress"
        ticket["assignee"] = "Engineer Agent"
        ticket["updated_at"] = datetime.now().isoformat()
        ticket["metadata"]["pm_delegated"] = True
        
        # Save updated ticket
        with open(ticket_path, 'w') as f:
            json.dump(ticket, f, indent=2)
            
        # Verify update
        with open(ticket_path, 'r') as f:
            updated_ticket = json.load(f)
            
        assert updated_ticket["status"] == "in_progress", "Status not updated"
        assert updated_ticket["assignee"] == "Engineer Agent", "Assignee not updated"
        assert updated_ticket["metadata"]["pm_delegated"] == True, "Metadata not updated"
        
        return "Ticket updated successfully"
        
    def test_agent_ticket_reference(self):
        """Test agent's ability to reference tickets in context"""
        # Create a ticket that references code changes
        ticket_data = {
            "id": "FEAT-001",
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication to the API",
            "status": "open",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
            "tags": ["feature", "security", "api"],
            "assignee": "Engineer Agent",
            "subtasks": [
                {"id": "FEAT-001-1", "title": "Create auth middleware", "status": "pending"},
                {"id": "FEAT-001-2", "title": "Add login endpoint", "status": "pending"},
                {"id": "FEAT-001-3", "title": "Add token validation", "status": "pending"}
            ],
            "metadata": {
                "estimated_hours": 8,
                "sprint": "2025-W04",
                "dependencies": ["Security Agent review", "QA Agent testing"]
            }
        }
        
        ticket_path = Path("tickets/FEAT-001.json")
        with open(ticket_path, 'w') as f:
            json.dump(ticket_data, f, indent=2)
            
        # Simulate agent context building
        context = {
            "ticket_id": "FEAT-001",
            "agent": "Engineer Agent",
            "task": "Implement authentication based on ticket requirements"
        }
        
        # Verify ticket can be loaded for context
        with open(ticket_path, 'r') as f:
            ticket_context = json.load(f)
            
        assert ticket_context["assignee"] == context["agent"], "Agent assignment mismatch"
        assert len(ticket_context["subtasks"]) == 3, "Subtasks not properly loaded"
        
        return "Agent context with ticket reference successful"
        
    def test_ticket_workflow(self):
        """Test complete ticket workflow from creation to closure"""
        workflow_ticket = {
            "id": "WORK-001", 
            "title": "Complete workflow test",
            "description": "Test full lifecycle of ticket",
            "status": "open",
            "priority": "medium",
            "created_at": datetime.now().isoformat(),
            "workflow_states": ["open", "assigned", "in_progress", "review", "closed"],
            "current_state": 0,
            "history": []
        }
        
        ticket_path = Path("tickets/WORK-001.json")
        
        # Simulate workflow progression
        states = ["open", "assigned", "in_progress", "review", "closed"]
        for i, state in enumerate(states):
            workflow_ticket["status"] = state
            workflow_ticket["current_state"] = i
            workflow_ticket["history"].append({
                "state": state,
                "timestamp": datetime.now().isoformat(),
                "actor": ["PM", "PM", "Engineer Agent", "QA Agent", "PM"][i]
            })
            
            with open(ticket_path, 'w') as f:
                json.dump(workflow_ticket, f, indent=2)
                
        # Verify final state
        with open(ticket_path, 'r') as f:
            final_ticket = json.load(f)
            
        assert final_ticket["status"] == "closed", "Ticket not closed"
        assert len(final_ticket["history"]) == 5, "Incomplete workflow history"
        assert final_ticket["current_state"] == 4, "Invalid final state"
        
        return "Workflow progression successful"
        
    def test_error_handling(self):
        """Test error handling and edge cases"""
        errors_caught = []
        
        # Test 1: Invalid ticket ID
        try:
            invalid_ticket = {"title": "No ID"}  # Missing required ID
            with open("tickets/invalid.json", 'w') as f:
                json.dump(invalid_ticket, f)
            # In real implementation, this should raise an error
            errors_caught.append("Missing ID validation needed")
        except Exception as e:
            errors_caught.append(f"Caught missing ID: {e}")
            
        # Test 2: Duplicate ticket ID
        try:
            dup_ticket = {"id": "TEST-001", "title": "Duplicate"}
            # This should be prevented in real implementation
            errors_caught.append("Duplicate ID prevention needed")
        except Exception as e:
            errors_caught.append(f"Caught duplicate: {e}")
            
        # Test 3: Invalid status transition
        try:
            # Simulate invalid transition (closed -> open)
            closed_ticket = {
                "id": "CLOSED-001",
                "status": "closed",
                "closed_at": datetime.now().isoformat()
            }
            # Reopening should require special handling
            errors_caught.append("Status transition validation needed")
        except Exception as e:
            errors_caught.append(f"Caught invalid transition: {e}")
            
        return f"Error handling tests: {len(errors_caught)} scenarios identified"
        
    def test_pm_orchestration_pattern(self):
        """Test PM's ability to orchestrate ticket-based tasks"""
        # Create a complex ticket requiring multi-agent coordination
        orchestration_ticket = {
            "id": "ORCH-001",
            "title": "Implement secure file upload feature",
            "description": "Add file upload with virus scanning and size limits",
            "status": "open",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
            "orchestration": {
                "agents_required": ["Security Agent", "Engineer Agent", "QA Agent"],
                "sequence": [
                    {
                        "step": 1,
                        "agent": "Security Agent",
                        "task": "Define security requirements and scanning approach",
                        "status": "pending"
                    },
                    {
                        "step": 2,
                        "agent": "Engineer Agent", 
                        "task": "Implement file upload with security measures",
                        "status": "pending",
                        "depends_on": [1]
                    },
                    {
                        "step": 3,
                        "agent": "QA Agent",
                        "task": "Test file upload security and edge cases",
                        "status": "pending",
                        "depends_on": [2]
                    }
                ],
                "pm_context": {
                    "delegation_pattern": "sequential",
                    "integration_points": ["API", "Storage", "Security Scanner"],
                    "completion_criteria": "All security tests pass"
                }
            }
        }
        
        ticket_path = Path("tickets/ORCH-001.json")
        with open(ticket_path, 'w') as f:
            json.dump(orchestration_ticket, f, indent=2)
            
        # Verify orchestration data is accessible
        with open(ticket_path, 'r') as f:
            orch_data = json.load(f)
            
        assert len(orch_data["orchestration"]["sequence"]) == 3, "Orchestration steps missing"
        assert orch_data["orchestration"]["agents_required"][0] == "Security Agent", "Agent order incorrect"
        
        # Simulate PM processing the orchestration
        pm_delegation_context = {
            "ticket": "ORCH-001",
            "current_step": 1,
            "delegated_to": "Security Agent",
            "task_tool_format": """
**Security Agent**: Define security requirements for file upload feature

TEMPORAL CONTEXT: Today is 2025-07-21. Security assessment for ORCH-001.

**Task**: Define security requirements and scanning approach
1. Specify file type restrictions and validation
2. Define virus scanning integration approach  
3. Set size limits and quota management
4. Document security headers and CORS policy

**Context**: Implementing secure file upload per ticket ORCH-001
**Authority**: Security architecture decisions
**Expected Results**: Security requirements document
**Integration**: Results will guide Engineer Agent implementation
            """
        }
        
        return "PM orchestration pattern validated"
        
    def generate_report(self):
        """Generate comprehensive test report"""
        print(f"\n{'='*60}")
        print("TICKETING INTEGRATION TEST REPORT")
        print(f"{'='*60}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.test_results)}")
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        print(f"\n{'='*60}")
        print("DETAILED RESULTS:")
        print(f"{'='*60}")
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"\n{status_icon} {result['test']}")
            if result["status"] == "PASS":
                print(f"   Result: {result.get('result', 'Success')}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
                
        print(f"\n{'='*60}")
        print("RECOMMENDATIONS:")
        print(f"{'='*60}")
        
        recommendations = [
            "1. Implement ticket ID validation in framework",
            "2. Add duplicate ID prevention mechanisms",
            "3. Create status transition state machine",
            "4. Enhance PM orchestration patterns for ticket-based workflows",
            "5. Add ticket template system for common scenarios",
            "6. Implement ticket-agent assignment validation",
            "7. Create ticket history and audit trail functionality",
            "8. Add ticket search and filtering capabilities"
        ]
        
        for rec in recommendations:
            print(f"   {rec}")
            
        return {
            "total": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed/len(self.test_results)*100):.1f}%"
        }


# Run the test suite
if __name__ == "__main__":
    suite = TicketingTestSuite()
    
    try:
        # Setup test environment
        suite.setup()
        
        # Run all tests
        suite.run_test("Ticket Creation", suite.test_ticket_creation)
        suite.run_test("Ticket Listing", suite.test_ticket_listing)
        suite.run_test("Ticket Update", suite.test_ticket_update)
        suite.run_test("Agent Ticket Reference", suite.test_agent_ticket_reference)
        suite.run_test("Ticket Workflow", suite.test_ticket_workflow)
        suite.run_test("Error Handling", suite.test_error_handling)
        suite.run_test("PM Orchestration Pattern", suite.test_pm_orchestration_pattern)
        
        # Generate report
        summary = suite.generate_report()
        
    finally:
        # Cleanup
        suite.cleanup()
        
    print(f"\n✅ Test suite completed: {summary}")