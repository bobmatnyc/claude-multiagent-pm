"""
E2E Tests for Context Management System
Tests the complete context management flow including filtering, sharing, and evolution.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List

from claude_pm.orchestration.context_manager import ContextManager, ContextFilter, AgentInteraction
from claude_pm.orchestration.orchestration_types import OrchestrationMode, OrchestrationMetrics
from tests.e2e.fixtures.context_fixtures import ContextFixtures
from tests.e2e.fixtures.prompt_fixtures import PromptFixtures


class TestContextManagement:
    """Test the context management system end-to-end."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance."""
        return ContextManager()
    
    @pytest.fixture
    def orchestration_context(self):
        """Create a sample orchestration context."""
        return {
            "task_id": "test-task-123",
            "agent_type": "documentation",
            "task_description": "Generate project documentation",
            "project_context": {
                "name": "test-project",
                "version": "1.0.0",
                "path": "/test/project"
            },
            "shared_state": {
                "last_build": "success",
                "coverage": 85.5
            },
            "parent_task_id": None,
            "correlation_id": "corr-123"
        }
    
    def test_context_lifecycle(self, context_manager):
        """Test the complete lifecycle of context management."""
        # 1. Initialize context
        initial_context = {
            "project": {"name": "lifecycle-test"},
            "status": "initialized"
        }
        
        # 2. Update shared context
        context_manager.update_shared_context(initial_context)
        assert context_manager.shared_context["status"] == "initialized"
        
        # 3. Filter for specific agent
        filtered = context_manager.filter_context_for_agent("documentation", initial_context)
        assert "project" in filtered
        
        # 4. Record interaction
        context_manager.record_interaction(
            agent_type="documentation",
            task="Initialize docs",
            result={"status": "success"},
            tokens_used=500
        )
        
        # 5. Verify interaction recorded
        assert len(context_manager.interaction_history["documentation"]) == 1
    
    def test_context_inheritance(self, context_manager):
        """Test context inheritance between parent and child tasks."""
        # Parent context
        parent_context = {
            "project": {"name": "parent-project"},
            "config": {"debug": True},
            "parent_data": "should inherit"
        }
        
        # Update shared context from parent
        context_manager.update_shared_context(parent_context)
        
        # Child task should inherit parent context
        child_context = context_manager.create_child_context(
            parent_context=parent_context,
            child_overrides={"config": {"debug": False}}
        )
        
        assert child_context["project"]["name"] == "parent-project"
        assert child_context["parent_data"] == "should inherit"
        assert child_context["config"]["debug"] is False  # Override applied
    
    def test_multi_agent_context_sharing(self, context_manager):
        """Test context sharing between multiple agents."""
        # Agent 1: Documentation creates initial docs
        doc_result = {
            "docs_created": ["README.md", "API.md"],
            "docs_path": "/docs"
        }
        context_manager.update_shared_context(doc_result)
        
        # Agent 2: QA needs to know about docs for testing
        qa_context = context_manager.filter_context_for_agent(
            "qa", 
            context_manager.shared_context
        )
        
        # QA should have access to docs info
        assert "docs_created" in qa_context
        assert "docs_path" in qa_context
        
        # Agent 3: Engineer updates based on QA feedback
        qa_feedback = {
            "test_results": {"passed": 8, "failed": 2},
            "issues": ["Missing error handling", "API docs incomplete"]
        }
        context_manager.update_shared_context(qa_feedback)
        
        # Engineer gets filtered context with relevant info
        eng_context = context_manager.filter_context_for_agent(
            "engineer",
            context_manager.shared_context
        )
        
        assert "issues" in eng_context
        assert "test_results" in eng_context
    
    def test_context_memory_limits(self, context_manager):
        """Test that context memory is limited to prevent unbounded growth."""
        # Add many interactions
        for i in range(100):
            context_manager.record_interaction(
                agent_type="test_agent",
                task=f"Task {i}",
                result={"iteration": i},
                tokens_used=100
            )
        
        # Check that old interactions are pruned
        interactions = context_manager.get_agent_interaction_history("test_agent")
        
        # Should keep only recent interactions (default limit: 50)
        assert len(interactions) <= 50
        
        # Most recent should be preserved
        assert interactions[-1].task == "Task 99"
    
    def test_context_serialization(self, context_manager):
        """Test context serialization for subprocess communication."""
        # Create complex context
        complex_context = {
            "project": {"name": "test", "version": "1.0.0"},
            "files": {"main.py": {"content": "print('hello')"}},
            "metadata": {
                "created": datetime.now().isoformat(),
                "tags": ["python", "test"]
            }
        }
        
        # Update and serialize
        context_manager.update_shared_context(complex_context)
        serialized = context_manager.serialize_context()
        
        # Should be JSON serializable
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)
        
        # Deserialize and verify
        deserialized = json.loads(json_str)
        assert deserialized["project"]["name"] == "test"
        assert "metadata" in deserialized
    
    def test_context_filtering_performance(self, context_manager):
        """Test performance of context filtering with large contexts."""
        import time
        
        # Create large context
        large_context = {
            "files": {
                f"file_{i}.py": {
                    "content": f"# File {i}\n" + "x" * 1000,
                    "metadata": {"size": 1000, "type": "python"}
                }
                for i in range(1000)
            },
            "project": {"name": "large-project"}
        }
        
        # Measure filtering time
        start_time = time.time()
        filtered = context_manager.filter_context_for_agent("documentation", large_context)
        filter_time = time.time() - start_time
        
        # Should complete quickly even with large context
        assert filter_time < 1.0  # Less than 1 second
        
        # Should significantly reduce size
        assert len(filtered.get("files", {})) < len(large_context["files"])
    
    def test_context_priority_preservation(self, context_manager):
        """Test that priority context items are always preserved."""
        context_with_priorities = {
            "critical_error": "Database connection failed",  # High priority
            "project_info": {"name": "test"},  # Standard priority
            "verbose_logs": ["log1", "log2"] * 1000,  # Low priority
            "current_task": "Fix database connection"  # High priority
        }
        
        # Filter for any agent - priority items should remain
        filtered = context_manager.filter_context_for_agent(
            "engineer", 
            context_with_priorities
        )
        
        # Critical items should be preserved
        assert "critical_error" in filtered
        assert "current_task" in filtered
        assert "project_info" in filtered
    
    def test_context_merge_strategies(self, context_manager):
        """Test different strategies for merging contexts."""
        base_context = {
            "config": {"debug": True, "port": 8080},
            "features": ["auth", "api"],
            "version": "1.0.0"
        }
        
        update_context = {
            "config": {"debug": False, "host": "localhost"},
            "features": ["ui"],
            "version": "1.1.0"
        }
        
        # Test different merge strategies
        
        # 1. Override strategy
        merged_override = context_manager.merge_contexts(
            base_context, update_context, strategy="override"
        )
        assert merged_override["config"]["debug"] is False
        assert merged_override["config"]["port"] == 8080  # Preserved
        assert merged_override["version"] == "1.1.0"
        
        # 2. Append strategy for lists
        merged_append = context_manager.merge_contexts(
            base_context, update_context, strategy="append"
        )
        assert "auth" in merged_append["features"]
        assert "ui" in merged_append["features"]
        
        # 3. Deep merge strategy
        merged_deep = context_manager.merge_contexts(
            base_context, update_context, strategy="deep"
        )
        assert merged_deep["config"]["debug"] is False
        assert merged_deep["config"]["port"] == 8080
        assert merged_deep["config"]["host"] == "localhost"
    
    def test_context_validation(self, context_manager):
        """Test context validation to ensure data integrity."""
        # Valid context
        valid_context = {
            "project_info": {"name": "test", "version": "1.0.0"},
            "files": {"main.py": {"content": "code"}},
            "metadata": {"created": "2025-07-19"}
        }
        
        # Should pass validation
        assert context_manager.validate_context(valid_context) is True
        
        # Invalid contexts
        invalid_contexts = [
            {"files": "not a dict"},  # Wrong type
            {"project_info": {"name": ""}},  # Empty required field
            {"metadata": {"created": "invalid-date"}},  # Invalid format
        ]
        
        for invalid in invalid_contexts:
            assert context_manager.validate_context(invalid) is False
    
    def test_context_access_patterns(self, context_manager):
        """Test different patterns for accessing context data."""
        context = {
            "nested": {
                "deeply": {
                    "nested": {
                        "value": "found it!"
                    }
                }
            },
            "list_data": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second"}
            ]
        }
        
        context_manager.update_shared_context(context)
        
        # Test safe access with defaults
        value = context_manager.get_context_value(
            "nested.deeply.nested.value",
            default="not found"
        )
        assert value == "found it!"
        
        # Test missing path
        missing = context_manager.get_context_value(
            "nested.deeply.missing.value",
            default="default value"
        )
        assert missing == "default value"
        
        # Test list access
        first_item = context_manager.get_context_value(
            "list_data[0].name",
            default=None
        )
        assert first_item == "first"


class TestContextIntegrationScenarios:
    """Test complex integration scenarios for context management."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with context management."""
        orchestrator = Mock()
        orchestrator.context_manager = ContextManager()
        orchestrator.agent_registry = Mock()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_push_workflow_context_flow(self, mock_orchestrator):
        """Test context flow in a complete push workflow."""
        # Initial context
        initial_context = {
            "command": "push",
            "project": {"name": "test-app", "version": "1.2.3"},
            "git": {"branch": "main", "changes": ["file1.py", "file2.py"]}
        }
        
        # Step 1: Documentation agent generates changelog
        doc_context = mock_orchestrator.context_manager.filter_context_for_agent(
            "documentation", initial_context
        )
        assert "project" in doc_context
        
        # Documentation agent result
        doc_result = {
            "changelog": "## v1.2.3\n- Updated file1.py\n- Fixed file2.py",
            "version_impact": "patch"
        }
        mock_orchestrator.context_manager.update_shared_context(doc_result)
        
        # Step 2: QA agent runs tests
        qa_context = mock_orchestrator.context_manager.filter_context_for_agent(
            "qa", mock_orchestrator.context_manager.shared_context
        )
        assert "changelog" in qa_context  # Should see doc results
        
        # QA result
        qa_result = {
            "tests": {"passed": 50, "failed": 0},
            "coverage": 92.5,
            "quality_gate": "passed"
        }
        mock_orchestrator.context_manager.update_shared_context(qa_result)
        
        # Step 3: Version control agent creates release
        vc_context = mock_orchestrator.context_manager.filter_context_for_agent(
            "version_control", mock_orchestrator.context_manager.shared_context
        )
        assert "version_impact" in vc_context
        assert "quality_gate" in vc_context
        
        # Final context should have all results
        final_context = mock_orchestrator.context_manager.shared_context
        assert "changelog" in final_context
        assert "tests" in final_context
        assert "quality_gate" in final_context
    
    def test_error_propagation_through_context(self, mock_orchestrator):
        """Test how errors are propagated through context."""
        # Initial task
        initial_context = {"task": "deploy", "target": "production"}
        
        # Agent 1 encounters error
        error_result = {
            "status": "error",
            "error": {
                "type": "ValidationError",
                "message": "Missing required config",
                "details": {"missing": ["API_KEY", "DB_URL"]}
            }
        }
        
        mock_orchestrator.context_manager.update_shared_context(error_result)
        
        # Subsequent agents should see error in context
        next_context = mock_orchestrator.context_manager.filter_context_for_agent(
            "ops", mock_orchestrator.context_manager.shared_context
        )
        
        assert "error" in next_context
        assert next_context["status"] == "error"
        
        # Should prevent dangerous operations
        can_proceed = mock_orchestrator.context_manager.check_safe_to_proceed()
        assert can_proceed is False
    
    def test_context_based_agent_selection(self, mock_orchestrator):
        """Test selecting agents based on context content."""
        # Context indicates need for specific agent types
        context_scenarios = [
            {
                "context": {"files": {"setup.py": {}, "requirements.txt": {}}},
                "expected_agent": "engineer"  # Python project
            },
            {
                "context": {"security_scan": {"vulnerabilities": ["CVE-2023-123"]}},
                "expected_agent": "security"  # Security issue
            },
            {
                "context": {"test_failure": True, "failing_tests": ["test_auth.py"]},
                "expected_agent": "qa"  # Test failure
            }
        ]
        
        for scenario in context_scenarios:
            suggested_agent = mock_orchestrator.context_manager.suggest_agent_for_context(
                scenario["context"]
            )
            assert suggested_agent == scenario["expected_agent"]
    
    def test_context_recovery_after_failure(self, mock_orchestrator):
        """Test context recovery mechanisms after agent failures."""
        # Create checkpoint
        checkpoint_context = {
            "stage": "pre-deployment",
            "completed_steps": ["build", "test"],
            "next_step": "deploy"
        }
        
        checkpoint_id = mock_orchestrator.context_manager.create_checkpoint(
            checkpoint_context
        )
        
        # Simulate failure
        mock_orchestrator.context_manager.update_shared_context({
            "status": "failed",
            "failed_step": "deploy",
            "error": "Connection timeout"
        })
        
        # Restore from checkpoint
        restored = mock_orchestrator.context_manager.restore_checkpoint(checkpoint_id)
        
        assert restored["stage"] == "pre-deployment"
        assert restored["next_step"] == "deploy"
        assert "error" not in restored  # Clean state
    
    def test_context_analytics(self, mock_orchestrator):
        """Test analytics and insights from context history."""
        # Simulate multiple task executions
        for i in range(10):
            mock_orchestrator.context_manager.record_interaction(
                agent_type="qa",
                task=f"Run tests #{i}",
                result={
                    "passed": 45 + i,
                    "failed": 5 - min(i, 5),
                    "duration": 30 + (i * 2)
                },
                tokens_used=1000 + (i * 100)
            )
        
        # Get analytics
        analytics = mock_orchestrator.context_manager.get_analytics()
        
        assert "average_tokens_per_task" in analytics
        assert "most_active_agent" in analytics
        assert "task_success_rate" in analytics
        assert analytics["most_active_agent"] == "qa"
        
        # Trend analysis
        trends = mock_orchestrator.context_manager.analyze_trends()
        assert "test_improvement" in trends
        assert trends["test_improvement"] > 0  # Tests improving over time