"""
Tests for the ContextManager component.
"""

import pytest
from datetime import datetime, timedelta
import json
from claude_pm.orchestration import (
    ContextManager, 
    ContextFilter, 
    AgentInteraction,
    create_context_manager
)


@pytest.fixture
def context_manager():
    """Create a fresh ContextManager instance for testing."""
    return ContextManager()


@pytest.fixture
def sample_full_context():
    """Create a sample full context for testing."""
    return {
        "files": {
            "README.md": "# Project Documentation\nThis is the main readme.",
            "CHANGELOG.md": "# Changelog\n## v1.0.0\n- Initial release",
            "src/main.py": "def main():\n    print('Hello')",
            "tests/test_main.py": "def test_main():\n    assert True",
            "docs/api.md": "# API Documentation",
            ".env": "SECRET_KEY=abc123",
            ".env.example": "SECRET_KEY=your_key_here",
            "migrations/001_initial.sql": "CREATE TABLE users;",
            "research/analysis.md": "# Research Analysis",
            "deploy/docker-compose.yml": "version: '3'"
        },
        "current_task": "Update documentation and add tests",
        "project_overview": "A Python project for demonstration",
        "test_results": {"passed": 10, "failed": 0},
        "git_status": "On branch main, nothing to commit",
        "active_tickets": ["TASK-001", "TASK-002"],
        "technical_specs": "Python 3.9+, pytest",
        "deployment_config": {"environment": "production"},
        "security_policies": "All secrets in env vars",
        "database_schema": {"tables": ["users", "posts"]}
    }


class TestContextManager:
    """Test ContextManager functionality."""
    
    def test_initialization(self, context_manager):
        """Test ContextManager initialization."""
        # Check that default filters are loaded
        assert len(context_manager.filters) == 9
        assert "documentation" in context_manager.filters
        assert "qa" in context_manager.filters
        assert "engineer" in context_manager.filters
        assert "research" in context_manager.filters
        assert "version_control" in context_manager.filters
        assert "ticketing" in context_manager.filters
        assert "ops" in context_manager.filters
        assert "security" in context_manager.filters
        assert "data_engineer" in context_manager.filters
        
        # Check empty history and shared context
        assert len(context_manager.interaction_history) == 0
        assert len(context_manager.shared_context) == 0
    
    def test_filter_context_documentation_agent(self, context_manager, sample_full_context):
        """Test context filtering for documentation agent."""
        filtered = context_manager.filter_context_for_agent("documentation", sample_full_context)
        
        # Should include documentation files
        assert "files" in filtered
        assert "README.md" in filtered["files"]
        assert "CHANGELOG.md" in filtered["files"]
        assert "docs/api.md" in filtered["files"]
        
        # Should not include code files
        assert "src/main.py" not in filtered["files"]
        assert "tests/test_main.py" not in filtered["files"]
        
        # Should include relevant context sections
        assert "project_overview" in filtered
        
        # Should include task since it mentions documentation
        assert "current_task" in filtered
        assert filtered["task_relevance_score"] > 0
    
    def test_filter_context_qa_agent(self, context_manager, sample_full_context):
        """Test context filtering for QA agent."""
        filtered = context_manager.filter_context_for_agent("qa", sample_full_context)
        
        # Should include test files
        assert "files" in filtered
        assert "tests/test_main.py" in filtered["files"]
        
        # Should not include documentation files
        assert "README.md" not in filtered["files"]
        
        # Should include test results
        assert "test_results" in filtered
        
        # Should include task since it mentions tests
        assert "current_task" in filtered
        assert filtered["task_relevance_score"] > 0
    
    def test_filter_context_engineer_agent(self, context_manager, sample_full_context):
        """Test context filtering for engineer agent."""
        filtered = context_manager.filter_context_for_agent("engineer", sample_full_context)
        
        # Should include code files
        assert "files" in filtered
        assert "src/main.py" in filtered["files"]
        
        # Should not include test files (excluded pattern)
        assert "tests/test_main.py" not in filtered["files"]
        
        # Should include technical specs
        assert "technical_specs" in filtered
    
    def test_filter_context_security_agent(self, context_manager, sample_full_context):
        """Test context filtering for security agent."""
        filtered = context_manager.filter_context_for_agent("security", sample_full_context)
        
        # Should include security-related files
        assert "files" in filtered
        assert ".env" in filtered["files"]
        
        # Should exclude .env.example (excluded pattern)
        assert ".env.example" not in filtered["files"]
        
        # Should include security policies
        assert "security_policies" in filtered
    
    def test_filter_context_unknown_agent(self, context_manager, sample_full_context):
        """Test context filtering for unknown agent type."""
        filtered = context_manager.filter_context_for_agent("unknown_type", sample_full_context)
        
        # Should return full context for unknown agent type
        assert filtered == sample_full_context
    
    def test_register_custom_filter(self, context_manager):
        """Test registering a custom agent filter."""
        custom_filter = ContextFilter(
            agent_type="custom",
            include_patterns=[r"custom_"],
            file_extensions=[".custom"],
            priority_keywords=["custom", "special"]
        )
        
        context_manager.register_custom_filter("custom", custom_filter)
        
        assert "custom" in context_manager.filters
        assert context_manager.filters["custom"].agent_type == "custom"
    
    def test_update_shared_context(self, context_manager):
        """Test updating shared context."""
        agent_id = "doc_agent_001"
        updates = {
            "latest_version": "1.0.0",
            "changelog_updated": True
        }
        
        context_manager.update_shared_context(agent_id, updates)
        
        # Check shared context was updated
        assert f"{agent_id}_latest_version" in context_manager.shared_context
        assert f"{agent_id}_changelog_updated" in context_manager.shared_context
        
        # Check structure of shared context
        version_entry = context_manager.shared_context[f"{agent_id}_latest_version"]
        assert version_entry["value"] == "1.0.0"
        assert version_entry["agent_id"] == agent_id
        assert "timestamp" in version_entry
    
    def test_record_interaction(self, context_manager):
        """Test recording agent interactions."""
        agent_id = "qa_agent_001"
        agent_type = "qa"
        
        # Record multiple interactions
        for i in range(5):
            context_manager.record_interaction(
                agent_id=agent_id,
                agent_type=agent_type,
                context_size=10000 + i * 1000,
                filtered_size=3000 + i * 100,
                request=f"Test request {i}",
                response=f"Test response {i}",
                additional_context_requested=(i % 2 == 0)
            )
        
        # Check interactions were recorded
        assert agent_id in context_manager.interaction_history
        history = context_manager.interaction_history[agent_id]
        assert len(history) == 5
        
        # Check interaction properties
        last_interaction = history[-1]
        assert last_interaction.agent_id == agent_id
        assert last_interaction.agent_type == agent_type
        assert last_interaction.request == "Test request 4"
        assert last_interaction.response == "Test response 4"
        assert last_interaction.additional_context_requested is True  # 4 % 2 == 0
    
    def test_get_agent_history(self, context_manager):
        """Test getting agent history (last 3 interactions)."""
        agent_id = "eng_agent_001"
        
        # Record 5 interactions
        for i in range(5):
            context_manager.record_interaction(
                agent_id=agent_id,
                agent_type="engineer",
                context_size=10000,
                filtered_size=3000,
                request=f"Request {i}"
            )
        
        # Get last 3 interactions
        recent_history = context_manager.get_agent_history(agent_id)
        
        assert len(recent_history) == 3
        assert recent_history[0].request == "Request 2"
        assert recent_history[1].request == "Request 3"
        assert recent_history[2].request == "Request 4"
    
    def test_get_agent_history_empty(self, context_manager):
        """Test getting history for agent with no interactions."""
        history = context_manager.get_agent_history("non_existent_agent")
        assert history == []
    
    def test_context_size_estimation(self, context_manager):
        """Test token count estimation."""
        # Test string
        text = "Hello, world! This is a test string."
        size = context_manager.get_context_size_estimate(text)
        assert size > 0
        assert size < 20  # Should be around 8-10 tokens
        
        # Test dictionary
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        size = context_manager.get_context_size_estimate(data)
        assert size > 0
        
        # Test large context
        large_context = {"data": "x" * 10000}
        size = context_manager.get_context_size_estimate(large_context)
        assert size > 1000  # Should be significant (tokenizer is efficient with repeated chars)
    
    def test_file_truncation(self, context_manager):
        """Test that large files are truncated."""
        large_content = "x" * 200000  # 200k characters
        context = {
            "files": {
                "large_file.txt": large_content,
                "small_file.txt": "Small content"
            }
        }
        
        # Filter for documentation agent (includes .txt files)
        filtered = context_manager.filter_context_for_agent("documentation", context)
        
        # Check large file was truncated
        assert "large_file.txt" in filtered["files"]
        assert len(filtered["files"]["large_file.txt"]) < 200000
        assert "... [truncated]" in filtered["files"]["large_file.txt"]
        
        # Small file should not be truncated
        assert filtered["files"]["small_file.txt"] == "Small content"
    
    def test_filter_statistics(self, context_manager):
        """Test getting filter statistics."""
        # Record some interactions
        context_manager.record_interaction(
            "doc_1", "documentation", 10000, 3000
        )
        context_manager.record_interaction(
            "qa_1", "qa", 8000, 2000
        )
        context_manager.record_interaction(
            "doc_2", "documentation", 12000, 3500
        )
        
        stats = context_manager.get_filter_statistics()
        
        assert stats["registered_filters"] == 9
        assert stats["total_interactions"] == 3
        assert stats["agents_tracked"] == 3
        
        # Check average reductions
        avg_reductions = stats["average_token_reduction_by_type"]
        assert "documentation" in avg_reductions
        assert "qa" in avg_reductions
        
        # Documentation reduction should be around 70%
        doc_reduction = avg_reductions["documentation"]
        assert 65 < doc_reduction < 75
        
        # QA reduction should be around 75%
        qa_reduction = avg_reductions["qa"]
        assert 70 < qa_reduction < 80
    
    def test_clear_old_shared_context(self, context_manager):
        """Test clearing old shared context items."""
        # Add some context items with old timestamps
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        recent_time = datetime.now().isoformat()
        
        context_manager.shared_context["old_item"] = {
            "value": "old",
            "timestamp": old_time,
            "agent_id": "test"
        }
        context_manager.shared_context["recent_item"] = {
            "value": "recent",
            "timestamp": recent_time,
            "agent_id": "test"
        }
        
        # Clear items older than 24 hours
        removed = context_manager.clear_old_shared_context(max_age_hours=24)
        
        assert removed == 1
        assert "old_item" not in context_manager.shared_context
        assert "recent_item" in context_manager.shared_context
    
    def test_interaction_history_limit(self, context_manager):
        """Test that interaction history is limited to prevent memory bloat."""
        agent_id = "test_agent"
        
        # Record 15 interactions
        for i in range(15):
            context_manager.record_interaction(
                agent_id=agent_id,
                agent_type="test",
                context_size=1000,
                filtered_size=500,
                request=f"Request {i}"
            )
        
        # Should only keep last 10
        assert len(context_manager.interaction_history[agent_id]) == 10
        
        # First interaction should be Request 5 (0-4 were dropped)
        first = context_manager.interaction_history[agent_id][0]
        assert first.request == "Request 5"
        
        # Last should be Request 14
        last = context_manager.interaction_history[agent_id][-1]
        assert last.request == "Request 14"
    
    def test_filter_shared_context(self, context_manager):
        """Test filtering shared context based on agent relationships."""
        # Add shared context from various agents
        context_manager.shared_context["documentation_version"] = {
            "value": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "agent_id": "doc_agent"
        }
        context_manager.shared_context["qa_test_results"] = {
            "value": {"passed": 10},
            "timestamp": datetime.now().isoformat(),
            "agent_id": "qa_agent"
        }
        context_manager.shared_context["security_audit"] = {
            "value": "passed",
            "timestamp": datetime.now().isoformat(),
            "agent_id": "sec_agent"
        }
        
        # Filter context for QA agent (should see engineer, documentation, and security)
        filtered = context_manager.filter_context_for_agent("qa", {})
        shared = filtered["shared_context"]
        
        # QA should see documentation and security (both are related)
        assert "documentation_version" in shared
        assert "security_audit" in shared  # QA is related to security
        
        # Test research agent which should not see security
        filtered_research = context_manager.filter_context_for_agent("research", {})
        shared_research = filtered_research["shared_context"]
        
        # Research should see documentation (related via engineer) but not security
        assert "documentation_version" in shared_research
        assert "security_audit" not in shared_research
    
    def test_create_context_manager_factory(self):
        """Test the factory function."""
        cm = create_context_manager()
        assert isinstance(cm, ContextManager)
        assert len(cm.filters) == 9


class TestContextFilter:
    """Test ContextFilter dataclass."""
    
    def test_default_values(self):
        """Test ContextFilter default values."""
        filter_config = ContextFilter(agent_type="test")
        
        assert filter_config.agent_type == "test"
        assert filter_config.include_patterns == []
        assert filter_config.exclude_patterns == []
        assert filter_config.file_extensions == []
        assert filter_config.directory_patterns == []
        assert filter_config.max_file_size == 100000
        assert filter_config.priority_keywords == []
        assert filter_config.context_sections == []
    
    def test_custom_values(self):
        """Test ContextFilter with custom values."""
        filter_config = ContextFilter(
            agent_type="custom",
            include_patterns=[r"test_"],
            file_extensions=[".py"],
            max_file_size=50000
        )
        
        assert filter_config.agent_type == "custom"
        assert filter_config.include_patterns == [r"test_"]
        assert filter_config.file_extensions == [".py"]
        assert filter_config.max_file_size == 50000


class TestAgentInteraction:
    """Test AgentInteraction dataclass."""
    
    def test_required_fields(self):
        """Test AgentInteraction with required fields only."""
        interaction = AgentInteraction(
            timestamp=datetime.now(),
            agent_id="test_001",
            agent_type="test",
            context_size=10000,
            filtered_size=3000
        )
        
        assert interaction.agent_id == "test_001"
        assert interaction.agent_type == "test"
        assert interaction.context_size == 10000
        assert interaction.filtered_size == 3000
        assert interaction.request is None
        assert interaction.response is None
        assert interaction.additional_context_requested is False
    
    def test_all_fields(self):
        """Test AgentInteraction with all fields."""
        now = datetime.now()
        interaction = AgentInteraction(
            timestamp=now,
            agent_id="test_002",
            agent_type="engineer",
            context_size=15000,
            filtered_size=4000,
            request="Implement feature X",
            response="Feature X implemented",
            additional_context_requested=True
        )
        
        assert interaction.timestamp == now
        assert interaction.request == "Implement feature X"
        assert interaction.response == "Feature X implemented"
        assert interaction.additional_context_requested is True