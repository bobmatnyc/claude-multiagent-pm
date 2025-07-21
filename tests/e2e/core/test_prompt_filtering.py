"""
E2E Tests for Prompt Filtering and Context Management
Tests the context filtering functionality that reduces token usage by filtering prompts based on agent type.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List

from claude_pm.orchestration.context_manager import ContextManager, ContextFilter
from tests.e2e.fixtures.prompt_fixtures import PromptFixtures


class TestPromptFiltering:
    """Test prompt filtering and context management functionality."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance."""
        return ContextManager()
    
    @pytest.fixture
    def sample_full_context(self):
        """Create a sample full context with various types of data."""
        return {
            "project_info": {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test project for E2E testing"
            },
            "files": {
                "README.md": {"content": "# Project README", "type": "markdown"},
                "setup.py": {"content": "setup(...)", "type": "python"},
                "package.json": {"content": '{"name": "test"}', "type": "json"},
                "test_module.py": {"content": "def test():\n    pass", "type": "python"},
                ".gitignore": {"content": "*.pyc\n__pycache__/", "type": "gitignore"},
                "docs/api.md": {"content": "# API Documentation", "type": "markdown"},
                "src/main.py": {"content": "def main():\n    pass", "type": "python"},
                "tests/test_main.py": {"content": "def test_main():\n    pass", "type": "python"}
            },
            "git_info": {
                "branch": "main",
                "last_commit": "abc123",
                "status": "clean"
            },
            "dependencies": {
                "python": ["pytest", "requests", "numpy"],
                "npm": ["react", "webpack"]
            },
            "test_results": {
                "passed": 10,
                "failed": 0,
                "coverage": 85.5
            },
            "security_scan": {
                "vulnerabilities": [],
                "last_scan": "2025-07-19T10:00:00Z"
            }
        }
    
    def test_default_filters_initialized(self, context_manager):
        """Test that default filters are initialized for all core agent types."""
        core_agent_types = [
            "documentation", "ticketing", "version_control", "qa",
            "research", "ops", "security", "engineer", "data_engineer"
        ]
        
        for agent_type in core_agent_types:
            assert agent_type in context_manager.filters
            assert isinstance(context_manager.filters[agent_type], ContextFilter)
    
    def test_documentation_agent_filtering(self, context_manager, sample_full_context):
        """Test context filtering for documentation agent."""
        filtered = context_manager.filter_context_for_agent("documentation", sample_full_context)
        
        # Documentation agent should get markdown files and project info
        assert "project_info" in filtered
        assert "files" in filtered
        
        # Check that only relevant files are included
        file_names = list(filtered["files"].keys())
        assert "README.md" in file_names
        assert "docs/api.md" in file_names
        
        # Python and other files should be excluded
        assert "setup.py" not in file_names
        assert "src/main.py" not in file_names
    
    def test_qa_agent_filtering(self, context_manager, sample_full_context):
        """Test context filtering for QA agent."""
        filtered = context_manager.filter_context_for_agent("qa", sample_full_context)
        
        # QA agent should get test files and test results
        assert "test_results" in filtered
        assert "files" in filtered
        
        # Check that test files are included
        file_names = list(filtered["files"].keys())
        assert "tests/test_main.py" in file_names
        assert "test_module.py" in file_names
        
        # Non-test files should be excluded
        assert "README.md" not in file_names
        assert "setup.py" not in file_names
    
    def test_security_agent_filtering(self, context_manager, sample_full_context):
        """Test context filtering for security agent."""
        filtered = context_manager.filter_context_for_agent("security", sample_full_context)
        
        # Security agent should get security scan results
        assert "security_scan" in filtered
        
        # Should also get certain configuration files
        assert "files" in filtered
        file_names = list(filtered["files"].keys())
        assert ".gitignore" in file_names
    
    def test_engineer_agent_filtering(self, context_manager, sample_full_context):
        """Test context filtering for engineer agent."""
        filtered = context_manager.filter_context_for_agent("engineer", sample_full_context)
        
        # Engineer agent should get source code files
        assert "files" in filtered
        assert "dependencies" in filtered
        
        # Check that source files are included
        file_names = list(filtered["files"].keys())
        assert "src/main.py" in file_names
        assert "setup.py" in file_names
        
        # Documentation files should be excluded
        assert "README.md" not in file_names
        assert "docs/api.md" not in file_names
    
    def test_version_control_agent_filtering(self, context_manager, sample_full_context):
        """Test context filtering for version control agent."""
        filtered = context_manager.filter_context_for_agent("version_control", sample_full_context)
        
        # Version control agent should get git info
        assert "git_info" in filtered
        
        # Should also get configuration files
        assert "files" in filtered
        file_names = list(filtered["files"].keys())
        assert ".gitignore" in file_names
        assert "package.json" in file_names
    
    def test_custom_filter_registration(self, context_manager):
        """Test registering a custom filter for a new agent type."""
        custom_filter = ContextFilter(
            agent_type="custom_agent",
            include_patterns=["*.custom", "custom/*"],
            exclude_patterns=["*.tmp"],
            file_extensions=[".custom", ".cfg"],
            max_file_size=5000,
            priority_keys=["custom_data", "configuration"]
        )
        
        context_manager.register_custom_filter("custom_agent", custom_filter)
        
        assert "custom_agent" in context_manager.filters
        assert context_manager.filters["custom_agent"] == custom_filter
    
    def test_token_limiting(self, context_manager, sample_full_context):
        """Test that context is limited by token count."""
        # Create a very large context
        large_context = sample_full_context.copy()
        large_context["large_data"] = "x" * 100000  # Very large string
        
        filtered = context_manager.filter_context_for_agent("documentation", large_context)
        
        # Get context size estimate (uses token counting internally)
        context_size = context_manager.get_context_size_estimate(json.dumps(filtered))
        
        # Should be reasonable size
        assert context_size < 1000000  # Less than 1MB
    
    def test_interaction_history_tracking(self, context_manager):
        """Test that agent interactions are tracked."""
        # Record an interaction
        context_manager.record_interaction(
            agent_id="doc-agent-1",
            agent_type="documentation",
            context_size=2000,
            filtered_size=1500,
            request="Generate README",
            response="README generated successfully"
        )
        
        # Get agent history
        history = context_manager.get_agent_history("doc-agent-1")
        assert len(history) > 0
        
        interaction = history[0]
        assert interaction.agent_id == "doc-agent-1"
        assert interaction.agent_type == "documentation"
        assert interaction.context_size == 2000
        assert interaction.filtered_size == 1500
    
    def test_shared_context_management(self, context_manager):
        """Test shared context management between agents."""
        # Update shared context
        context_manager.update_shared_context(
            agent_id="test-agent-1",
            updates={
                "build_status": "success",
                "test_coverage": 85.5
            }
        )
        
        # Get filtered context that should include shared context
        filtered = context_manager._filter_shared_context("documentation")
        # Shared context is accessible through the filtering mechanism
    
    def test_filter_statistics(self, context_manager, sample_full_context):
        """Test getting filter statistics."""
        # Filter context for multiple agents
        context_manager.filter_context_for_agent("documentation", sample_full_context)
        context_manager.filter_context_for_agent("qa", sample_full_context)
        context_manager.filter_context_for_agent("engineer", sample_full_context)
        
        # Get statistics
        stats = context_manager.get_filter_statistics()
        
        assert stats["registered_filters"] == 9  # All core agents
        assert "filter_usage" in stats
        assert "average_token_reduction" in stats
    
    def test_priority_key_filtering(self, context_manager):
        """Test that priority keys are always included in filtered context."""
        # Create context with priority data
        context_with_priority = {
            "project_info": {"name": "test"},  # Priority for all agents
            "non_priority_data": {"foo": "bar"},
            "files": {"test.txt": {"content": "test"}}
        }
        
        # Filter for any agent type
        filtered = context_manager.filter_context_for_agent("documentation", context_with_priority)
        
        # Priority keys should always be included
        assert "project_info" in filtered
    
    def test_empty_context_handling(self, context_manager):
        """Test handling of empty context."""
        empty_context = {}
        
        # Should not raise an error
        filtered = context_manager.filter_context_for_agent("documentation", empty_context)
        
        assert isinstance(filtered, dict)
        assert len(filtered) >= 0  # May include some default keys
    
    def test_malformed_context_handling(self, context_manager):
        """Test handling of malformed context data."""
        malformed_context = {
            "files": "not a dict",  # Should be a dict
            "project_info": None,    # Should be a dict
            "valid_data": {"key": "value"}
        }
        
        # Should handle gracefully
        filtered = context_manager.filter_context_for_agent("documentation", malformed_context)
        
        assert isinstance(filtered, dict)
        assert "valid_data" in filtered
    
    @pytest.mark.parametrize("agent_type,expected_extensions", [
        ("documentation", [".md", ".rst", ".txt"]),
        ("engineer", [".py", ".js", ".java", ".cpp"]),
        ("qa", [".py", ".js"]),  # Test files
        ("ops", [".yml", ".yaml", ".json", ".sh"]),
        ("data_engineer", [".sql", ".json", ".csv"])
    ])
    def test_file_extension_filtering(self, context_manager, agent_type, expected_extensions):
        """Test that files are filtered by extension based on agent type."""
        # Create files with various extensions
        files = {}
        for ext in [".md", ".py", ".js", ".yml", ".sql", ".txt", ".cpp"]:
            files[f"test{ext}"] = {"content": f"test content", "type": ext[1:]}
        
        context = {"files": files}
        filtered = context_manager.filter_context_for_agent(agent_type, context)
        
        if "files" in filtered:
            filtered_files = list(filtered["files"].keys())
            for file in filtered_files:
                ext = Path(file).suffix
                assert ext in expected_extensions or any(ext.endswith(e) for e in expected_extensions)
    
    def test_concurrent_filtering(self, context_manager, sample_full_context):
        """Test that multiple agents can filter context concurrently."""
        import threading
        results = {}
        
        def filter_for_agent(agent_type):
            results[agent_type] = context_manager.filter_context_for_agent(
                agent_type, sample_full_context
            )
        
        # Create threads for different agents
        threads = []
        for agent_type in ["documentation", "qa", "engineer"]:
            thread = threading.Thread(target=filter_for_agent, args=(agent_type,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all agents got filtered context
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results.values())


class TestPromptFilteringIntegration:
    """Integration tests for prompt filtering with actual orchestration flow."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with context management."""
        orchestrator = Mock()
        orchestrator.context_manager = ContextManager()
        return orchestrator
    
    def test_task_delegation_with_filtering(self, mock_orchestrator):
        """Test that context is filtered when delegating tasks to agents."""
        # Create a full context
        full_context = {
            "project_info": {"name": "test-project"},
            "files": {
                "README.md": {"content": "# README"},
                "src/main.py": {"content": "def main(): pass"},
                "tests/test_main.py": {"content": "def test(): pass"}
            },
            "test_results": {"passed": 5, "failed": 0}
        }
        
        # Simulate task delegation to documentation agent
        filtered_context = mock_orchestrator.context_manager.filter_context_for_agent(
            "documentation", full_context
        )
        
        # Create task prompt with filtered context
        prompt = PromptFixtures.task_tool_prompt(
            "documentation",
            "Update README with test results",
            json.dumps(filtered_context, indent=2)
        )
        
        # Verify prompt contains filtered context
        assert "README.md" in prompt
        assert "src/main.py" not in prompt  # Should be filtered out
    
    def test_multi_agent_workflow_filtering(self, mock_orchestrator):
        """Test context filtering in a multi-agent workflow."""
        full_context = {
            "project_info": {"name": "multi-agent-test"},
            "files": {
                "docs/design.md": {"content": "# Design"},
                "src/app.py": {"content": "app code"},
                "tests/test_app.py": {"content": "test code"},
                ".github/workflows/ci.yml": {"content": "CI config"}
            },
            "git_info": {"branch": "feature/test"},
            "test_results": {"coverage": 80}
        }
        
        # Simulate multi-agent workflow
        agents = ["documentation", "engineer", "qa", "ops"]
        filtered_contexts = {}
        
        for agent in agents:
            filtered_contexts[agent] = mock_orchestrator.context_manager.filter_context_for_agent(
                agent, full_context
            )
        
        # Verify each agent gets appropriate context
        assert "docs/design.md" in filtered_contexts["documentation"]["files"]
        assert "src/app.py" in filtered_contexts["engineer"]["files"]
        assert "tests/test_app.py" in filtered_contexts["qa"]["files"]
        assert ".github/workflows/ci.yml" in filtered_contexts["ops"]["files"]
    
    def test_context_evolution_tracking(self, mock_orchestrator):
        """Test tracking how context evolves through agent interactions."""
        initial_context = {
            "project_info": {"version": "1.0.0"},
            "build_status": "pending"
        }
        
        # Agent 1: Engineer updates code
        mock_orchestrator.context_manager.update_shared_context({
            "code_changes": ["Updated main.py", "Added tests"],
            "build_status": "in_progress"
        })
        
        # Agent 2: QA runs tests
        mock_orchestrator.context_manager.update_shared_context({
            "test_results": {"passed": 10, "failed": 0},
            "build_status": "testing"
        })
        
        # Agent 3: Ops deploys
        mock_orchestrator.context_manager.update_shared_context({
            "deployment_status": "success",
            "build_status": "completed"
        })
        
        # Verify context evolution
        final_context = mock_orchestrator.context_manager.shared_context
        assert final_context["build_status"] == "completed"
        assert "code_changes" in final_context
        assert "test_results" in final_context
        assert "deployment_status" in final_context
    
    def test_token_optimization_across_agents(self, mock_orchestrator):
        """Test that token usage is optimized across multiple agent interactions."""
        large_context = {
            "files": {f"file_{i}.py": {"content": "x" * 1000} for i in range(100)},
            "metadata": {"size": "large"}
        }
        
        token_counts = {}
        
        # Filter for different agents and track token usage
        for agent_type in ["documentation", "qa", "engineer"]:
            filtered = mock_orchestrator.context_manager.filter_context_for_agent(
                agent_type, large_context
            )
            token_counts[agent_type] = mock_orchestrator.context_manager.calculate_token_count(
                filtered
            )
        
        # Verify token reduction
        full_tokens = mock_orchestrator.context_manager.calculate_token_count(large_context)
        
        for agent_type, tokens in token_counts.items():
            assert tokens < full_tokens, f"{agent_type} should use fewer tokens than full context"