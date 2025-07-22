#!/usr/bin/env python3
"""
Test PM Orchestrator Ticketing Integration
=========================================

Tests the integration of TicketingService with PM orchestrator functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from claude_pm.services.pm_orchestrator import PMOrchestrator
from claude_pm.services.ticketing_service import TicketData


class TestPMTicketingIntegration:
    """Test PM orchestrator ticketing integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def mock_ticketing_service(self):
        """Create mock ticketing service."""
        mock_service = Mock()
        mock_service.create_ticket.return_value = TicketData(
            id="CLAUDE-001",
            title="Test Ticket",
            description="Test Description",
            status="open",
            priority="medium"
        )
        mock_service.update_ticket.return_value = TicketData(
            id="CLAUDE-001",
            title="Test Ticket",
            description="Test Description",
            status="resolved",
            priority="medium"
        )
        mock_service.add_comment.return_value = True
        return mock_service
    
    @pytest.fixture
    def mock_ticketing_helper(self):
        """Create mock ticketing helper."""
        mock_helper = Mock()
        mock_helper.create_agent_task_ticket.return_value = TicketData(
            id="CLAUDE-001",
            title="[Engineer] Test Task",
            description="Test task description",
            status="open",
            priority="high"
        )
        mock_helper.update_agent_task_status.return_value = True
        mock_helper.get_project_overview.return_value = {
            "total_tickets": 5,
            "agent_tasks": 3,
            "by_status": {"open": 2, "in_progress": 2, "resolved": 1}
        }
        mock_helper.get_agent_workload.return_value = {
            "agent": "engineer",
            "total_tickets": 2,
            "open": 1,
            "in_progress": 1
        }
        return mock_helper
    
    def test_pm_orchestrator_ticketing_init(self, temp_dir):
        """Test PM orchestrator initializes with ticketing support."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Verify ticketing was initialized
                    mock_ts.get_instance.assert_called_once()
                    mock_th.assert_called_once()
    
    def test_ticket_creation_for_complex_task(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test that tickets are created for complex tasks."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Create a complex task that should trigger ticket creation
                    prompt = orchestrator.generate_agent_prompt(
                        agent_type="engineer",
                        task_description="Implement multi-agent coordination system",
                        requirements=["Requirement 1", "Requirement 2", "Requirement 3"],
                        deliverables=["Deliverable 1", "Deliverable 2", "Deliverable 3"],
                        priority="high"
                    )
                    
                    # Verify ticket was created
                    mock_ticketing_helper.create_agent_task_ticket.assert_called_once()
                    call_args = mock_ticketing_helper.create_agent_task_ticket.call_args
                    assert call_args[1]["agent_name"] == "engineer"
                    assert call_args[1]["priority"] == "high"
                    
                    # Verify ticket ID is in prompt
                    assert "CLAUDE-001" in prompt
    
    def test_ticket_not_created_for_simple_task(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test that tickets are not created for simple tasks."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Create a simple task that should NOT trigger ticket creation
                    prompt = orchestrator.generate_agent_prompt(
                        agent_type="engineer",
                        task_description="Fix a typo in documentation",
                        requirements=["Fix typo"],
                        deliverables=["Updated docs"],
                        priority="low"
                    )
                    
                    # Verify ticket was NOT created
                    mock_ticketing_helper.create_agent_task_ticket.assert_not_called()
    
    def test_complete_delegation_updates_ticket(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test that completing a delegation updates the associated ticket."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Create a task with ticket
                    prompt = orchestrator.generate_agent_prompt(
                        agent_type="engineer",
                        task_description="Implement feature with multiple steps",
                        requirements=["Step 1", "Step 2", "Step 3"],
                        priority="high"
                    )
                    
                    # Get delegation ID
                    delegation_id = orchestrator._delegation_history[-1]["delegation_id"]
                    
                    # Complete the delegation
                    results = {
                        "success": True,
                        "summary": "Feature implemented successfully"
                    }
                    orchestrator.complete_delegation(delegation_id, results)
                    
                    # Verify ticket was updated
                    mock_ticketing_helper.update_agent_task_status.assert_called_once()
                    call_args = mock_ticketing_helper.update_agent_task_status.call_args
                    assert call_args[1]["status"] == "resolved"
                    assert "Feature implemented successfully" in call_args[1]["comment"]
    
    def test_multi_agent_workflow_creation(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test creation of multi-agent workflows with tickets."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Create multi-agent workflow
                    workflow = orchestrator.create_multi_agent_workflow(
                        workflow_name="Deploy New Feature",
                        workflow_description="Complete workflow for deploying a new feature",
                        agent_tasks=[
                            {
                                "agent_type": "engineer",
                                "task_description": "Implement the feature",
                                "requirements": ["Requirement 1", "Requirement 2"],
                                "deliverables": ["Working code", "Tests"]
                            },
                            {
                                "agent_type": "qa",
                                "task_description": "Test the feature",
                                "requirements": ["Test plan", "Test cases"],
                                "deliverables": ["Test results", "Bug reports"],
                                "depends_on": ["engineer"]
                            },
                            {
                                "agent_type": "documentation",
                                "task_description": "Document the feature",
                                "requirements": ["Feature spec", "API docs"],
                                "deliverables": ["User guide", "API reference"],
                                "depends_on": ["engineer", "qa"]
                            }
                        ],
                        priority="high"
                    )
                    
                    # Verify workflow was created
                    assert workflow["workflow_id"].startswith("workflow_")
                    assert len(workflow["agent_tasks"]) == 3
                    assert workflow["master_ticket_id"] == "CLAUDE-001"
                    
                    # Verify master ticket was created
                    mock_ticketing_service.create_ticket.assert_called_once()
                    
                    # Verify agent task tickets were created (high priority triggers tickets)
                    assert mock_ticketing_helper.create_agent_task_ticket.call_count >= 3
    
    def test_get_ticketing_status(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test getting ticketing status and workload."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Get ticketing status
                    status = orchestrator.get_ticketing_status()
                    
                    # Verify status structure
                    assert status["ticketing_enabled"] is True
                    assert "project_overview" in status
                    assert status["project_overview"]["total_tickets"] == 5
                    assert "agent_workload" in status
    
    def test_update_delegation_progress(self, temp_dir, mock_ticketing_service, mock_ticketing_helper):
        """Test updating delegation progress updates ticket."""
        with patch('claude_pm.services.pm_orchestrator.TICKETING_AVAILABLE', True):
            with patch('claude_pm.services.pm_orchestrator.TicketingService') as mock_ts:
                with patch('claude_pm.services.pm_orchestrator.TicketingHelper') as mock_th:
                    # Setup mocks
                    mock_ts.get_instance.return_value = mock_ticketing_service
                    mock_th.return_value = mock_ticketing_helper
                    
                    orchestrator = PMOrchestrator(working_directory=temp_dir)
                    
                    # Create a task with ticket
                    prompt = orchestrator.generate_agent_prompt(
                        agent_type="engineer",
                        task_description="Long running task",
                        requirements=["Step 1", "Step 2", "Step 3"],
                        priority="high"
                    )
                    
                    # Get delegation ID
                    delegation_id = orchestrator._delegation_history[-1]["delegation_id"]
                    
                    # Update progress
                    success = orchestrator.update_delegation_progress(
                        delegation_id=delegation_id,
                        progress="Completed step 1, starting step 2",
                        status="in_progress"
                    )
                    
                    assert success is True
                    
                    # Verify comment was added to ticket
                    mock_ticketing_service.add_comment.assert_called_once()
                    call_args = mock_ticketing_service.add_comment.call_args
                    assert "Progress Update:" in call_args[1]["comment"]
                    assert "Completed step 1" in call_args[1]["comment"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])