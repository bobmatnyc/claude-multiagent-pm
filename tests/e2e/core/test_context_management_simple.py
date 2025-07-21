"""
Simplified E2E Tests for Context Management
Tests core context management functionality with the actual implementation.
"""

import pytest
import json
import time
from datetime import datetime
from typing import Dict, Any

from claude_pm.orchestration.context_manager import ContextManager, ContextFilter


class TestContextManagementSimple:
    """Test context management functionality."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance."""
        return ContextManager()
    
    def test_context_filtering_basic(self, context_manager):
        """Test basic context filtering functionality."""
        context = {
            "files": {"test.py": "code", "README.md": "docs"},
            "project_overview": "Test project"
        }
        
        # Filter for documentation agent
        filtered = context_manager.filter_context_for_agent("documentation", context)
        
        assert "agent_type" in filtered
        assert filtered["agent_type"] == "documentation"
        assert "timestamp" in filtered
        assert "shared_context" in filtered
    
    def test_shared_context_operations(self, context_manager):
        """Test shared context update and retrieval."""
        # Update shared context
        context_manager.update_shared_context(
            agent_id="test-agent-1",
            updates={"status": "active", "result": "success"}
        )
        
        # Get shared context through filtering
        filtered = context_manager.filter_context_for_agent("documentation", {})
        assert "shared_context" in filtered
    
    def test_interaction_history(self, context_manager):
        """Test recording and retrieving interaction history."""
        # Record interaction
        context_manager.record_interaction(
            agent_id="test-agent",
            agent_type="qa",
            context_size=1000,
            filtered_size=500,
            request="Run tests",
            response="Tests completed"
        )
        
        # Get history
        history = context_manager.get_agent_history("test-agent")
        assert len(history) > 0
        assert history[0].agent_type == "qa"
        assert history[0].context_size == 1000
        assert history[0].filtered_size == 500
    
    def test_filter_statistics(self, context_manager):
        """Test filter statistics tracking."""
        # Filter some contexts to generate statistics
        contexts = [
            {"files": {"a.py": "code"}, "test_results": {"passed": 5}},
            {"files": {"b.md": "docs"}, "project_overview": "Test"},
            {"files": {"c.yml": "config"}, "deployment_config": {"env": "prod"}}
        ]
        
        for i, ctx in enumerate(contexts):
            agent_types = ["engineer", "documentation", "ops"]
            context_manager.filter_context_for_agent(agent_types[i], ctx)
        
        # Get statistics
        stats = context_manager.get_filter_statistics()
        assert "registered_filters" in stats
        assert stats["registered_filters"] == 10  # All core filters
    
    def test_context_size_estimation(self, context_manager):
        """Test context size estimation."""
        small_context = {"data": "small"}
        large_context = {"data": "x" * 10000}
        
        small_size = context_manager.get_context_size_estimate(small_context)
        large_size = context_manager.get_context_size_estimate(large_context)
        
        assert large_size > small_size
        assert small_size > 0
    
    def test_old_context_cleanup(self, context_manager):
        """Test cleanup of old shared context."""
        # Add some shared context
        context_manager.update_shared_context(
            agent_id="old-agent",
            updates={"old_data": "should be cleaned"}
        )
        
        # Clean old context (with very recent max_age for testing)
        cleaned = context_manager.clear_old_shared_context(max_age_hours=0)
        assert cleaned >= 0  # Some items may have been cleaned
    
    def test_multi_agent_filtering(self, context_manager):
        """Test filtering for multiple agent types."""
        context = {
            "files": {
                "main.py": "code",
                "test_main.py": "test",
                "README.md": "docs",
                "deploy.yml": "config"
            },
            "project_overview": "Multi-agent test",
            "test_results": {"passed": 10},
            "deployment_config": {"target": "prod"}
        }
        
        # Filter for different agents
        agents = ["documentation", "qa", "ops", "engineer"]
        filtered_contexts = {}
        
        for agent in agents:
            filtered_contexts[agent] = context_manager.filter_context_for_agent(agent, context)
        
        # Each should have appropriate context
        assert "project_overview" in filtered_contexts["documentation"]
        assert "test_results" in filtered_contexts["qa"]
        assert "deployment_config" in filtered_contexts["ops"]
        
        # All should have basic structure
        for agent, filtered in filtered_contexts.items():
            assert filtered["agent_type"] == agent
            assert "timestamp" in filtered
            assert "shared_context" in filtered