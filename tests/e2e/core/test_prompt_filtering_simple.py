"""
Simplified E2E Tests for Prompt Filtering
Tests the core functionality of context filtering without assuming specific implementation details.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from claude_pm.orchestration.context_manager import ContextManager, ContextFilter


class TestPromptFilteringSimple:
    """Test prompt filtering functionality with the actual implementation."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance."""
        return ContextManager()
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample context with various data types."""
        return {
            "files": {
                "README.md": {"content": "# Project README", "type": "markdown"},
                "setup.py": {"content": "setup(...)", "type": "python"},
                "test_main.py": {"content": "def test(): pass", "type": "python"},
                "docs/api.md": {"content": "# API Documentation", "type": "markdown"}
            },
            "project_overview": "This is a test project",
            "test_results": {"passed": 10, "failed": 0},
            "git_status": "clean",
            "active_tickets": ["ISSUE-001", "ISSUE-002"]
        }
    
    def test_context_filtering_returns_expected_structure(self, context_manager, sample_context):
        """Test that filtered context has the expected structure."""
        filtered = context_manager.filter_context_for_agent("documentation", sample_context)
        
        # Should always have these fields
        assert "agent_type" in filtered
        assert "timestamp" in filtered
        assert "shared_context" in filtered
        assert filtered["agent_type"] == "documentation"
    
    def test_file_filtering_by_extension(self, context_manager, sample_context):
        """Test that files are filtered based on agent type."""
        # Documentation agent should get markdown files
        doc_filtered = context_manager.filter_context_for_agent("documentation", sample_context)
        if "files" in doc_filtered:
            for filename in doc_filtered["files"]:
                assert filename.endswith(".md") or filename.endswith("CLAUDE.md")
        
        # Engineer agent should get code files
        eng_filtered = context_manager.filter_context_for_agent("engineer", sample_context)
        if "files" in eng_filtered:
            # Engineer gets various code files
            assert any(f.endswith(".py") for f in eng_filtered["files"])
    
    def test_context_sections_included(self, context_manager):
        """Test that appropriate context sections are included for each agent."""
        # Test with specific sections
        context_with_sections = {
            "project_overview": "Test project",
            "test_results": {"passed": 5},
            "git_status": "clean",
            "deployment_config": {"env": "prod"}
        }
        
        # Documentation agent should get project_overview
        doc_filtered = context_manager.filter_context_for_agent("documentation", context_with_sections)
        assert "project_overview" in doc_filtered
        
        # QA agent should get test_results
        qa_filtered = context_manager.filter_context_for_agent("qa", context_with_sections)
        assert "test_results" in qa_filtered
        
        # Version control should get git_status
        vc_filtered = context_manager.filter_context_for_agent("version_control", context_with_sections)
        assert "git_status" in vc_filtered
        
        # Ops should get deployment_config
        ops_filtered = context_manager.filter_context_for_agent("ops", context_with_sections)
        assert "deployment_config" in ops_filtered
    
    def test_all_core_agents_have_filters(self, context_manager):
        """Test that all core agent types have filters defined."""
        core_agents = ["documentation", "qa", "engineer", "research", 
                      "version_control", "ticketing", "ops", "security", 
                      "data_engineer", "orchestrator"]
        
        for agent in core_agents:
            assert agent in context_manager.filters
    
    def test_context_size_reduction(self, context_manager):
        """Test that filtering reduces context size."""
        large_context = {
            "files": {f"file_{i}.py": {"content": "x" * 1000} for i in range(100)}
        }
        
        original_size = context_manager.get_context_size_estimate(large_context)
        filtered = context_manager.filter_context_for_agent("documentation", large_context)
        filtered_size = context_manager.get_context_size_estimate(filtered)
        
        # Filtered should be smaller than original
        assert filtered_size < original_size
    
    def test_shared_context_update_and_retrieval(self, context_manager):
        """Test updating and retrieving shared context."""
        # Update shared context
        context_manager.update_shared_context(
            agent_id="test-agent",
            updates={"status": "active", "result": "success"}
        )
        
        # Filter should include shared context
        filtered = context_manager.filter_context_for_agent("documentation", {})
        assert "shared_context" in filtered
    
    def test_interaction_recording(self, context_manager):
        """Test recording agent interactions."""
        # Record an interaction
        context_manager.record_interaction(
            agent_id="test-agent",
            agent_type="documentation",
            context_size=1000,
            filtered_size=500,
            request="Generate docs"
        )
        
        # Get history
        history = context_manager.get_agent_history("test-agent")
        assert len(history) > 0
        assert history[0].agent_type == "documentation"
    
    def test_custom_filter_creation(self, context_manager):
        """Test creating a custom filter for a new agent type."""
        # Create custom filter
        custom_filter = ContextFilter(
            agent_type="custom",
            file_extensions=[".custom"],
            include_patterns=["*.custom"],
            context_sections=["custom_data"]
        )
        
        # Register it
        context_manager.register_custom_filter("custom", custom_filter)
        
        # Should be available
        assert "custom" in context_manager.filters
    
    def test_filter_statistics_tracking(self, context_manager):
        """Test that filtering statistics are tracked."""
        # Filter some contexts
        context_manager.filter_context_for_agent("documentation", {"files": {"a.md": "content"}})
        context_manager.filter_context_for_agent("qa", {"test_results": {"passed": 5}})
        
        # Get statistics
        stats = context_manager.get_filter_statistics()
        assert "registered_filters" in stats
        assert stats["registered_filters"] > 0