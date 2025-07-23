#!/usr/bin/env python3
"""
Test Suite for Ticket-First Operations Mode
==========================================

This module tests the ticket-first operations mode where tickets are created
before operations, enabling proper context filtering and isolation.

The ticket-first mode follows this flow:
1. Create ticket with specific scope and requirements
2. Filter context based on ticket metadata
3. Execute operation with filtered context
4. Verify proper isolation and boundaries

Key Test Scenarios:
- Basic ticket creation and context filtering
- Multiple ticket types with different context requirements
- Context isolation between concurrent tickets
- Ticket metadata driving context selection
- Integration with ContextManager filtering
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

# Import framework components
from claude_pm.orchestration.context_manager import ContextManager, ContextFilter
from claude_pm.services.ticketing_service import TicketingService, TicketData
from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode
)


class TestTicketFirstOperations:
    """Test suite for ticket-first operations mode."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix="test_ticket_first_")
        
        # Create project structure
        project_structure = {
            ".claude-pm": {
                "agents": {
                    "user-agents": {},
                    "project-specific": {}
                },
                "tickets": {},
                "CLAUDE.md": "# Test Project Instructions\n\n## Ticket-First Mode Testing"
            },
            "src": {
                "main.py": "# Main application code\nprint('Hello, World!')",
                "utils.py": "# Utility functions\ndef helper(): pass",
                "database.py": "# Database operations\nclass DB: pass"
            },
            "tests": {
                "test_main.py": "# Unit tests\ndef test_main(): pass",
                "test_utils.py": "# Utils tests\ndef test_helper(): pass"
            },
            "docs": {
                "README.md": "# Project Documentation",
                "API.md": "# API Documentation",
                "CHANGELOG.md": "# Changelog\n## v1.0.0\n- Initial release"
            },
            "infrastructure": {
                "docker-compose.yml": "version: '3'\nservices:\n  app:\n    image: app:latest",
                "deploy.sh": "#!/bin/bash\necho 'Deploying...'"
            },
            "migrations": {
                "001_initial.sql": "CREATE TABLE users (id INT PRIMARY KEY);",
                "002_add_emails.sql": "ALTER TABLE users ADD COLUMN email VARCHAR(255);"
            }
        }
        
        # Create directory structure
        def create_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                if isinstance(content, dict):
                    path.mkdir(parents=True, exist_ok=True)
                    create_structure(path, content)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
        
        create_structure(Path(temp_dir), project_structure)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def context_manager(self):
        """Create a ContextManager instance for testing."""
        return ContextManager()
    
    @pytest.fixture
    def mock_ticketing_service(self):
        """Create a mock ticketing service."""
        service = Mock(spec=TicketingService)
        
        # Track created tickets
        service.tickets = {}
        service.ticket_counter = 0
        
        def create_ticket(**kwargs):
            service.ticket_counter += 1
            ticket_id = f"TEST-{service.ticket_counter:03d}"
            ticket = TicketData(
                id=ticket_id,
                title=kwargs.get('title', 'Test Ticket'),
                description=kwargs.get('description', 'Test Description'),
                status=kwargs.get('status', 'open'),
                priority=kwargs.get('priority', 'medium'),
                labels=kwargs.get('labels', []),
                metadata=kwargs.get('metadata', {}),
                created_at=datetime.now()
            )
            service.tickets[ticket_id] = ticket
            return ticket
        
        service.create_ticket = Mock(side_effect=create_ticket)
        service.get_ticket = Mock(side_effect=lambda id: service.tickets.get(id))
        service.update_ticket = Mock(side_effect=lambda id, **kwargs: service.tickets[id].__dict__.update(kwargs))
        
        return service
    
    def test_basic_ticket_context_filtering(self, context_manager, mock_ticketing_service, temp_project_dir):
        """Test basic ticket creation and context filtering flow."""
        # Create a ticket for documentation task
        ticket = mock_ticketing_service.create_ticket(
            title="Update project documentation",
            description="Update README and API docs with new features",
            priority="high",
            labels=["documentation", "urgent"],
            metadata={
                "agent_type": "documentation",
                "context_requirements": ["docs", "changelog"],
                "exclude_patterns": ["tests", "migrations"]
            }
        )
        
        assert ticket.id == "TEST-001"
        assert ticket.metadata["agent_type"] == "documentation"
        
        # Create full context from project
        full_context = {
            "project_root": temp_project_dir,
            "files": {
                f"{temp_project_dir}/src/main.py": "# Main application code\nprint('Hello, World!')",
                f"{temp_project_dir}/tests/test_main.py": "# Unit tests\ndef test_main(): pass",
                f"{temp_project_dir}/docs/README.md": "# Project Documentation",
                f"{temp_project_dir}/docs/API.md": "# API Documentation",
                f"{temp_project_dir}/migrations/001_initial.sql": "CREATE TABLE users (id INT PRIMARY KEY);"
            },
            "current_task": f"Working on ticket {ticket.id}: {ticket.title}"
        }
        
        # Filter context based on ticket metadata
        filtered_context = context_manager.filter_context_for_agent(
            agent_type=ticket.metadata["agent_type"],
            full_context=full_context
        )
        
        # Verify context filtering
        assert "files" in filtered_context
        filtered_files = list(filtered_context["files"].keys())
        
        # Should include documentation files
        assert any("README.md" in f for f in filtered_files)
        assert any("API.md" in f for f in filtered_files)
        
        # Should exclude test and migration files
        assert not any("test_main.py" in f for f in filtered_files)
        assert not any("001_initial.sql" in f for f in filtered_files)
        
        # Should include current task with ticket reference
        assert filtered_context["current_task"] == f"Working on ticket {ticket.id}: {ticket.title}"
    
    def test_multiple_ticket_types_context_isolation(self, context_manager, mock_ticketing_service, temp_project_dir):
        """Test context isolation between different ticket types."""
        # Create tickets for different agent types
        tickets = {
            "qa": mock_ticketing_service.create_ticket(
                title="Run test suite validation",
                description="Execute all tests and verify coverage",
                metadata={
                    "agent_type": "qa",
                    "context_requirements": ["tests", "coverage"],
                    "focus_areas": ["unit_tests", "integration_tests"]
                }
            ),
            "engineer": mock_ticketing_service.create_ticket(
                title="Implement new feature",
                description="Add user authentication",
                metadata={
                    "agent_type": "engineer",
                    "context_requirements": ["src", "database"],
                    "exclude_patterns": ["test_"]
                }
            ),
            "ops": mock_ticketing_service.create_ticket(
                title="Deploy to staging",
                description="Deploy latest changes to staging environment",
                metadata={
                    "agent_type": "ops",
                    "context_requirements": ["infrastructure", "deploy"],
                    "include_patterns": ["docker", "deploy", "yml"]
                }
            )
        }
        
        # Create full context
        full_context = {
            "project_root": temp_project_dir,
            "files": {
                f"{temp_project_dir}/src/main.py": "# Main application code",
                f"{temp_project_dir}/src/database.py": "# Database operations",
                f"{temp_project_dir}/tests/test_main.py": "# Unit tests",
                f"{temp_project_dir}/infrastructure/docker-compose.yml": "version: '3'",
                f"{temp_project_dir}/infrastructure/deploy.sh": "#!/bin/bash"
            }
        }
        
        # Filter context for each ticket type
        contexts = {}
        for ticket_type, ticket in tickets.items():
            contexts[ticket_type] = context_manager.filter_context_for_agent(
                agent_type=ticket.metadata["agent_type"],
                full_context={**full_context, "current_ticket": ticket.id}
            )
        
        # Verify QA context
        qa_files = list(contexts["qa"]["files"].keys())
        assert any("test_main.py" in f for f in qa_files)
        # QA agent might see some source files for test coverage analysis
        
        # Verify Engineer context
        eng_files = list(contexts["engineer"]["files"].keys())
        assert any("main.py" in f for f in eng_files)
        assert any("database.py" in f for f in eng_files)
        # Engineer filter explicitly excludes test_ patterns
        
        # Verify Ops context
        ops_files = list(contexts["ops"]["files"].keys())
        assert any("docker-compose.yml" in f for f in ops_files)
        assert any("deploy.sh" in f for f in ops_files)
        # Ops focuses on infrastructure files
    
    def test_ticket_metadata_driven_filtering(self, context_manager, mock_ticketing_service):
        """Test how ticket metadata drives context filtering decisions."""
        # Create ticket with specific filtering metadata
        ticket = mock_ticketing_service.create_ticket(
            title="Security audit",
            description="Perform security audit on authentication system",
            metadata={
                "agent_type": "security",
                "context_requirements": {
                    "include_patterns": ["auth", "security", "password", "token"],
                    "exclude_patterns": ["test", "mock", "example"],
                    "max_file_size": 50000,
                    "priority_keywords": ["authentication", "authorization", "encryption"]
                },
                "scan_depth": "deep",
                "include_dependencies": True
            }
        )
        
        # Create custom filter based on ticket metadata
        custom_filter = ContextFilter(
            agent_type="security",
            include_patterns=ticket.metadata["context_requirements"]["include_patterns"],
            exclude_patterns=ticket.metadata["context_requirements"]["exclude_patterns"],
            max_file_size=ticket.metadata["context_requirements"]["max_file_size"],
            priority_keywords=ticket.metadata["context_requirements"]["priority_keywords"]
        )
        
        # Register custom filter
        context_manager.register_custom_filter("security", custom_filter)
        
        # Test with sample files
        full_context = {
            "files": {
                "src/auth/login.py": "# Authentication logic" * 1000,  # Large file
                "src/auth/token.py": "# Token generation",
                "tests/test_auth.py": "# Auth tests",
                "examples/auth_example.py": "# Example code",
                "src/utils/helpers.py": "# Generic helpers"
            },
            "current_task": "Security audit for authentication"
        }
        
        filtered_context = context_manager.filter_context_for_agent(
            agent_type="security",
            full_context=full_context
        )
        
        # Verify filtering based on ticket metadata
        filtered_files = filtered_context.get("files", {})
        
        # Should include auth files
        assert "src/auth/login.py" in filtered_files
        assert "src/auth/token.py" in filtered_files
        
        # Should exclude test and example files based on exclude patterns
        assert "tests/test_auth.py" not in filtered_files
        assert "examples/auth_example.py" not in filtered_files
        
        # Check that auth files are included
        assert any("auth" in f for f in filtered_files)
        
        # Verify file size truncation
        assert len(filtered_files.get("src/auth/login.py", "")) < 50000
        assert "truncated" in filtered_files.get("src/auth/login.py", "")
    
    def test_concurrent_ticket_isolation(self, context_manager, mock_ticketing_service):
        """Test that concurrent tickets maintain proper context isolation."""
        # Create multiple concurrent tickets
        tickets = []
        for i in range(3):
            ticket = mock_ticketing_service.create_ticket(
                title=f"Concurrent task {i}",
                description=f"Task {i} description",
                metadata={
                    "agent_type": ["documentation", "qa", "engineer"][i],
                    "context_id": f"context_{i}",
                    "isolation_level": "strict"
                }
            )
            tickets.append(ticket)
        
        # Simulate concurrent context filtering
        contexts = []
        for ticket in tickets:
            # Each ticket gets its own context view
            full_context = {
                "ticket_id": ticket.id,
                "files": {
                    "README.md": "# Documentation",
                    "test_file.py": "# Test code",
                    "main.py": "# Main code"
                },
                "shared_data": {
                    "project_name": "Test Project",
                    "version": "1.0.0"
                }
            }
            
            filtered = context_manager.filter_context_for_agent(
                agent_type=ticket.metadata["agent_type"],
                full_context=full_context
            )
            
            # Add ticket-specific context
            filtered["ticket_context"] = {
                "ticket_id": ticket.id,
                "context_id": ticket.metadata["context_id"]
            }
            
            contexts.append(filtered)
        
        # Verify each context is isolated
        assert len(contexts) == 3
        
        # Each context should have different files based on agent type
        doc_files = list(contexts[0].get("files", {}).keys())
        qa_files = list(contexts[1].get("files", {}).keys())
        eng_files = list(contexts[2].get("files", {}).keys())
        
        assert "README.md" in doc_files
        assert "test_file.py" in qa_files
        assert "main.py" in eng_files
        
        # Verify ticket-specific context is maintained
        for i, context in enumerate(contexts):
            assert context["ticket_context"]["ticket_id"] == tickets[i].id
            assert context["ticket_context"]["context_id"] == f"context_{i}"
    
    @pytest.mark.asyncio
    async def test_ticket_first_orchestration_flow(self, mock_ticketing_service):
        """Test complete ticket-first orchestration flow."""
        # Mock orchestrator
        orchestrator = Mock(spec=BackwardsCompatibleOrchestrator)
        orchestrator.delegate_to_agent = AsyncMock()
        
        # Create ticket first
        ticket = mock_ticketing_service.create_ticket(
            title="Implement user authentication",
            description="Add JWT-based authentication to the API",
            priority="high",
            metadata={
                "agent_type": "engineer",
                "subtasks": [
                    "Design authentication schema",
                    "Implement JWT token generation",
                    "Add authentication middleware",
                    "Write unit tests"
                ],
                "dependencies": ["database", "security"]
            }
        )
        
        # Simulate ticket-first delegation
        async def delegate_with_ticket(ticket_id: str):
            # Get ticket
            ticket = mock_ticketing_service.get_ticket(ticket_id)
            
            # Prepare context based on ticket
            task_context = {
                "ticket": {
                    "id": ticket.id,
                    "title": ticket.title,
                    "description": ticket.description,
                    "metadata": ticket.metadata
                },
                "filtered_for": ticket.metadata["agent_type"],
                "subtasks": ticket.metadata.get("subtasks", [])
            }
            
            # Delegate to appropriate agent
            result = await orchestrator.delegate_to_agent(
                agent_type=ticket.metadata["agent_type"],
                task_description=f"[Ticket {ticket.id}] {ticket.title}",
                additional_context=task_context
            )
            
            return result
        
        # Execute delegation
        orchestrator.delegate_to_agent.return_value = ({
            "success": True,
            "ticket_id": ticket.id,
            "completed_subtasks": ["Design authentication schema"],
            "agent_type": "engineer"
        }, 0)
        
        result = await delegate_with_ticket(ticket.id)
        
        # Verify orchestration
        assert result[0]["success"] is True
        assert result[0]["ticket_id"] == ticket.id
        assert result[0]["agent_type"] == "engineer"
        
        # Verify delegate was called with ticket context
        orchestrator.delegate_to_agent.assert_called_once()
        call_args = orchestrator.delegate_to_agent.call_args
        assert "[Ticket TEST-001]" in call_args[1]["task_description"]
        assert call_args[1]["additional_context"]["ticket"]["id"] == ticket.id
    
    def test_ticket_priority_context_filtering(self, context_manager, mock_ticketing_service):
        """Test how ticket priority affects context filtering."""
        # Create tickets with different priorities
        tickets = {
            "critical": mock_ticketing_service.create_ticket(
                title="Critical security fix",
                priority="critical",
                metadata={
                    "agent_type": "security",
                    "context_scope": "full",  # Critical gets full context
                    "include_sensitive": True
                }
            ),
            "low": mock_ticketing_service.create_ticket(
                title="Update documentation typo",
                priority="low",
                metadata={
                    "agent_type": "documentation",
                    "context_scope": "minimal",  # Low priority gets minimal context
                    "max_files": 5
                }
            )
        }
        
        # Full context with many files
        full_context = {
            "files": {f"file_{i}.py": f"Content {i}" for i in range(20)},
            "sensitive_data": {
                "api_keys": ["key1", "key2"],
                "database_credentials": "postgres://user:pass@localhost"
            }
        }
        
        # Filter for critical ticket
        critical_context = context_manager.filter_context_for_agent(
            agent_type=tickets["critical"].metadata["agent_type"],
            full_context={
                **full_context,
                "ticket_priority": "critical",
                "include_all": True
            }
        )
        
        # Filter for low priority ticket
        low_context = context_manager.filter_context_for_agent(
            agent_type=tickets["low"].metadata["agent_type"],
            full_context={
                **full_context,
                "ticket_priority": "low",
                "limit_files": 5
            }
        )
        
        # Critical ticket should have more context
        assert len(critical_context.get("files", {})) > len(low_context.get("files", {}))
        
        # Low priority should have limited files
        assert len(low_context.get("files", {})) <= 5
    
    def test_ticket_lifecycle_context_updates(self, context_manager, mock_ticketing_service):
        """Test how context changes through ticket lifecycle."""
        # Create ticket
        ticket = mock_ticketing_service.create_ticket(
            title="Feature implementation",
            status="open",
            metadata={
                "agent_type": "engineer",
                "phase": "planning"
            }
        )
        
        # Phase 1: Planning - minimal context
        planning_context = context_manager.filter_context_for_agent(
            agent_type="engineer",
            full_context={
                "files": {"spec.md": "Specification", "code.py": "Implementation"},
                "ticket_phase": "planning"
            }
        )
        
        # Update ticket to implementation phase
        mock_ticketing_service.update_ticket(
            ticket.id,
            status="in_progress",
            metadata={**ticket.metadata, "phase": "implementation"}
        )
        
        # Phase 2: Implementation - full code context
        impl_context = context_manager.filter_context_for_agent(
            agent_type="engineer",
            full_context={
                "files": {"spec.md": "Specification", "code.py": "Implementation"},
                "ticket_phase": "implementation",
                "include_code": True
            }
        )
        
        # Update ticket to review phase
        mock_ticketing_service.update_ticket(
            ticket.id,
            status="review",
            metadata={**ticket.metadata, "phase": "review"}
        )
        
        # Phase 3: Review - include tests
        review_context = context_manager.filter_context_for_agent(
            agent_type="qa",
            full_context={
                "files": {
                    "spec.md": "Specification", 
                    "code.py": "Implementation",
                    "test_code.py": "Tests"
                },
                "ticket_phase": "review"
            }
        )
        
        # Verify context evolution
        assert len(impl_context.get("files", {})) >= len(planning_context.get("files", {}))
        assert "test_code.py" in review_context.get("files", {})
    
    def test_ticket_metadata_inheritance(self, mock_ticketing_service):
        """Test how child tickets inherit metadata from parent tickets."""
        # Create parent epic
        epic = mock_ticketing_service.create_ticket(
            title="Implement authentication system",
            labels=["epic", "security"],
            metadata={
                "agent_types": ["security", "engineer", "qa"],
                "context_requirements": {
                    "include_patterns": ["auth", "security"],
                    "security_level": "high"
                },
                "child_tickets": []
            }
        )
        
        # Create child tickets that inherit from epic
        child_tickets = []
        for subtask in ["Design auth schema", "Implement JWT", "Write tests"]:
            child = mock_ticketing_service.create_ticket(
                title=subtask,
                labels=["subtask"],
                metadata={
                    "parent_id": epic.id,
                    "inherited_metadata": epic.metadata["context_requirements"],
                    "agent_type": ["engineer", "engineer", "qa"][len(child_tickets)]
                }
            )
            child_tickets.append(child)
            
            # Update parent to track children
            epic.metadata["child_tickets"].append(child.id)
        
        # Verify inheritance
        for child in child_tickets:
            assert child.metadata["parent_id"] == epic.id
            assert child.metadata["inherited_metadata"]["security_level"] == "high"
            assert "auth" in child.metadata["inherited_metadata"]["include_patterns"]
    
    def test_context_filtering_performance_metrics(self, context_manager, mock_ticketing_service):
        """Test and measure context filtering performance for ticket-first mode."""
        import time
        
        # Create ticket with specific filtering requirements
        ticket = mock_ticketing_service.create_ticket(
            title="Performance testing",
            metadata={
                "agent_type": "qa",
                "performance_test": True
            }
        )
        
        # Create large context to test performance
        large_context = {
            "files": {f"file_{i}.py": f"Content {i}" * 100 for i in range(100)},
            "metadata": {f"key_{i}": f"value_{i}" for i in range(1000)}
        }
        
        # Measure filtering time
        start_time = time.time()
        filtered_context = context_manager.filter_context_for_agent(
            agent_type="qa",
            full_context=large_context
        )
        filtering_time = time.time() - start_time
        
        # Get context statistics
        stats = context_manager.get_filter_statistics()
        
        # Verify performance
        assert filtering_time < 1.0  # Should filter in under 1 second
        assert "files" in filtered_context
        assert len(filtered_context["files"]) < len(large_context["files"])
        
        # Log performance metrics
        print(f"\nPerformance Metrics:")
        print(f"- Filtering time: {filtering_time:.3f}s")
        print(f"- Original files: {len(large_context['files'])}")
        print(f"- Filtered files: {len(filtered_context['files'])}")
        print(f"- Reduction: {(1 - len(filtered_context['files'])/len(large_context['files']))*100:.1f}%")


class TestTicketFirstIntegration:
    """Integration tests for ticket-first mode with real components."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix="test_ticket_first_integration_")
        
        # Create project structure
        project_structure = {
            ".claude-pm": {
                "agents": {},
                "CLAUDE.md": "# Test Project"
            },
            "src": {
                "main.py": "# Main code",
                "utils.py": "# Utils"
            },
            "tests": {
                "test_main.py": "# Tests"
            },
            "docs": {
                "README.md": "# README"
            }
        }
        
        # Create directory structure
        def create_structure(base_path: Path, structure: Dict):
            for name, content in structure.items():
                path = base_path / name
                if isinstance(content, dict):
                    path.mkdir(parents=True, exist_ok=True)
                    create_structure(path, content)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
        
        create_structure(Path(temp_dir), project_structure)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_real_orchestrator_ticket_flow(self):
        """Test ticket-first flow with real orchestrator (mocked backend)."""
        # Create orchestrator
        orchestrator = BackwardsCompatibleOrchestrator()
        
        # Mock the subprocess execution
        with patch.object(orchestrator, '_execute_subprocess_delegation') as mock_subprocess:
            mock_subprocess.return_value = ({
                "success": True,
                "subprocess_id": "test_123",
                "message": "Task completed successfully"
            }, 0)
            
            # Create ticket context
            ticket_context = {
                "ticket": {
                    "id": "INT-001",
                    "title": "Integration test task",
                    "agent_type": "engineer"
                }
            }
            
            # Execute delegation with ticket context
            result, return_code = await orchestrator.delegate_to_agent(
                agent_type="engineer",
                task_description="[Ticket INT-001] Integration test task",
                additional_context=ticket_context
            )
            
            assert result["success"] is True
            assert return_code == 0
            
            # Verify subprocess was called
            mock_subprocess.assert_called_once()
    
    def test_context_manager_with_real_files(self, temp_project_dir):
        """Test context manager with real file system."""
        context_manager = ContextManager()
        
        # Create real context from temp directory
        from pathlib import Path
        project_path = Path(temp_project_dir)
        
        # Read actual files
        files = {}
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                try:
                    files[str(file_path)] = file_path.read_text()
                except:
                    pass  # Skip binary files
        
        full_context = {
            "project_root": str(project_path),
            "files": files
        }
        
        # Test filtering for different agent types
        for agent_type in ["documentation", "qa", "engineer", "ops"]:
            filtered = context_manager.filter_context_for_agent(
                agent_type=agent_type,
                full_context=full_context
            )
            
            assert "files" in filtered
            assert len(filtered["files"]) <= len(files)
            
            # Verify agent-specific files are included
            if agent_type == "documentation":
                assert any("README.md" in f for f in filtered["files"])
            elif agent_type == "qa":
                assert any("test_" in f for f in filtered["files"])
            elif agent_type == "engineer":
                assert any(".py" in f for f in filtered["files"])
            elif agent_type == "ops":
                assert any("docker" in f or "deploy" in f for f in filtered["files"])


def generate_ticket_first_documentation():
    """Generate documentation for ticket-first operations mode."""
    documentation = """
    # Ticket-First Operations Mode Documentation
    
    ## Overview
    
    Ticket-first operations mode ensures that all agent operations are scoped
    and filtered based on ticket metadata. This provides:
    
    1. **Context Isolation**: Each ticket gets its own filtered context
    2. **Performance Optimization**: Only relevant files are included
    3. **Security**: Sensitive data is filtered based on ticket requirements
    4. **Traceability**: All operations are linked to tickets
    
    ## Flow Diagram
    
    ```
    Create Ticket
         |
         v
    Extract Metadata
         |
         v
    Configure Context Filter
         |
         v
    Execute Operation
         |
         v
    Update Ticket Status
    ```
    
    ## Implementation Example
    
    ```python
    # 1. Create ticket with specific requirements
    ticket = ticketing_service.create_ticket(
        title="Implement feature X",
        metadata={
            "agent_type": "engineer",
            "context_requirements": {
                "include_patterns": ["src/", "lib/"],
                "exclude_patterns": ["test_", "_test.py"],
                "max_file_size": 100000
            }
        }
    )
    
    # 2. Filter context based on ticket
    filtered_context = context_manager.filter_context_for_agent(
        agent_type=ticket.metadata["agent_type"],
        full_context=full_context
    )
    
    # 3. Execute operation with filtered context
    result = await orchestrator.delegate_to_agent(
        agent_type=ticket.metadata["agent_type"],
        task_description=f"[Ticket {ticket.id}] {ticket.title}",
        additional_context=filtered_context
    )
    ```
    
    ## Benefits
    
    - **Reduced Token Usage**: Only relevant context is sent to agents
    - **Better Focus**: Agents see only what they need for the task
    - **Improved Security**: Sensitive data is filtered appropriately
    - **Performance**: Faster processing with smaller context
    """
    
    print(documentation)
    return documentation


def test_documentation_generation():
    """Test that documentation can be generated."""
    doc = generate_ticket_first_documentation()
    assert "Ticket-First Operations Mode Documentation" in doc
    assert "Overview" in doc
    assert "Flow Diagram" in doc
    assert "Implementation Example" in doc
    assert "Benefits" in doc


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])