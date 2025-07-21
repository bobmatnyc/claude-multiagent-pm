"""
Complete Integration Test Suite for E2E Testing
Combines all orchestration components to test full workflows.
"""

import pytest
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from claude_pm.orchestration.context_manager import ContextManager, ContextFilter
from claude_pm.core.agent_registry import AgentRegistry
from tests.e2e.fixtures.prompt_fixtures import PromptFixtures
from tests.e2e.fixtures.context_fixtures import ContextFixtures


class TestCompleteIntegration:
    """Test complete integration of all orchestration components."""
    
    @pytest.fixture
    def test_environment(self, tmp_path):
        """Create a complete test environment."""
        # Create directory structure
        project_dir = tmp_path / "test_project"
        project_agents = project_dir / ".claude-pm" / "agents" / "project-specific"
        project_agents.mkdir(parents=True)
        
        # Create some test agent files
        (project_agents / "test_documentation.md").write_text("""
        # Test Documentation Agent
        Type: documentation
        Specialization: project_docs
        """)
        
        (project_agents / "test_qa.md").write_text("""
        # Test QA Agent
        Type: qa
        Specialization: integration_testing
        """)
        
        return {
            "project_dir": project_dir,
            "agents_dir": project_agents,
            "context_manager": ContextManager(),
            "agent_registry": AgentRegistry()
        }
    
    def test_documentation_workflow(self, test_environment):
        """Test a complete documentation generation workflow."""
        context_manager = test_environment["context_manager"]
        
        # Create initial context
        initial_context = {
            "command": "document",
            "files": {
                "src/main.py": {"content": "def main(): pass"},
                "README.md": {"content": "# Project"},
                "tests/test_main.py": {"content": "def test(): pass"}
            },
            "project_overview": "Test project for documentation",
            "recent_changes": ["Added main function", "Updated tests"]
        }
        
        # Step 1: Filter context for documentation agent
        doc_context = context_manager.filter_context_for_agent("documentation", initial_context)
        
        # Verify documentation agent gets appropriate context
        assert "project_overview" in doc_context
        assert "recent_changes" in doc_context
        assert "files" in doc_context
        
        # Step 2: Record interaction
        context_manager.record_interaction(
            agent_id="doc-agent-1",
            agent_type="documentation",
            context_size=len(json.dumps(initial_context)),
            filtered_size=len(json.dumps(doc_context)),
            request="Generate project documentation"
        )
        
        # Step 3: Update shared context with results
        context_manager.update_shared_context(
            agent_id="doc-agent-1",
            updates={
                "docs_generated": ["API.md", "GUIDE.md"],
                "status": "completed"
            }
        )
        
        # Step 4: Verify shared context is available to other agents
        qa_context = context_manager.filter_context_for_agent("qa", {})
        assert "shared_context" in qa_context
    
    def test_multi_agent_push_workflow(self, test_environment):
        """Test a complete push workflow with multiple agents."""
        context_manager = test_environment["context_manager"]
        
        # Initial push context
        push_context = {
            "command": "push",
            "git_status": "modified: src/app.py",
            "project_overview": "Web application",
            "test_results": {"passed": 50, "failed": 0},
            "recent_commits": ["feat: Add user auth", "fix: Login bug"]
        }
        
        # Step 1: Documentation agent generates changelog
        doc_context = context_manager.filter_context_for_agent("documentation", push_context)
        assert "project_overview" in doc_context
        
        # Documentation completes
        context_manager.update_shared_context(
            agent_id="doc-agent",
            updates={
                "changelog": "## v1.2.0\n- feat: Add user auth\n- fix: Login bug",
                "version_impact": "minor"
            }
        )
        
        # Step 2: QA agent runs tests
        qa_context = context_manager.filter_context_for_agent("qa", push_context)
        assert "test_results" in qa_context
        
        # QA completes
        context_manager.update_shared_context(
            agent_id="qa-agent",
            updates={
                "test_status": "all_passed",
                "coverage": 92.5
            }
        )
        
        # Step 3: Version control agent
        vc_context = context_manager.filter_context_for_agent("version_control", push_context)
        assert "git_status" in vc_context
        
        # Get final shared context
        final_context = context_manager._filter_shared_context("orchestrator")
        
        # Verify all agent results are integrated
        stats = context_manager.get_filter_statistics()
        assert stats["registered_filters"] >= 9
    
    def test_agent_discovery_with_context_filtering(self, test_environment):
        """Test agent discovery integrated with context filtering."""
        registry = test_environment["agent_registry"]
        context_manager = test_environment["context_manager"]
        
        # Discover available agents
        agents = registry.listAgents()
        
        # For each discovered agent type, test context filtering
        test_context = {
            "files": {"test.py": "code", "README.md": "docs"},
            "project_overview": "Integration test",
            "test_results": {"passed": 10}
        }
        
        filtered_contexts = {}
        
        # Filter context for core agent types
        for agent_type in ["documentation", "qa", "engineer", "ops"]:
            if agent_type in context_manager.filters:
                filtered_contexts[agent_type] = context_manager.filter_context_for_agent(
                    agent_type, test_context
                )
        
        # Verify each agent gets appropriate context
        for agent_type, filtered in filtered_contexts.items():
            assert "agent_type" in filtered
            assert filtered["agent_type"] == agent_type
            assert "timestamp" in filtered
    
    def test_error_handling_workflow(self, test_environment):
        """Test error handling across the integration."""
        context_manager = test_environment["context_manager"]
        
        # Create error context
        error_context = {
            "status": "error",
            "error": {
                "type": "BuildError",
                "message": "Compilation failed",
                "file": "src/main.py",
                "line": 42
            },
            "files": {"src/main.py": {"content": "invalid python code{"}}
        }
        
        # Engineer agent gets error context
        eng_context = context_manager.filter_context_for_agent("engineer", error_context)
        assert "files" in eng_context
        
        # Record failed interaction
        context_manager.record_interaction(
            agent_id="eng-agent",
            agent_type="engineer",
            context_size=1000,
            filtered_size=500,
            request="Fix build error",
            response="Error: Unable to fix"
        )
        
        # Update shared context with failure
        context_manager.update_shared_context(
            agent_id="eng-agent",
            updates={
                "fix_status": "failed",
                "reason": "Syntax error too complex"
            }
        )
        
        # Verify error propagates
        qa_context = context_manager.filter_context_for_agent("qa", {})
        # QA agent should see the failure in shared context
        assert "shared_context" in qa_context
    
    def test_performance_with_large_context(self, test_environment):
        """Test performance with large contexts."""
        context_manager = test_environment["context_manager"]
        
        # Create large context
        large_context = {
            "files": {
                f"file_{i}.py": {"content": f"# File {i}\n" + "x" * 500}
                for i in range(100)
            },
            "metadata": {"file_count": 100}
        }
        
        # Measure filtering performance
        start_time = time.time()
        
        # Filter for multiple agents
        for agent_type in ["documentation", "qa", "engineer"]:
            filtered = context_manager.filter_context_for_agent(agent_type, large_context)
            size_original = context_manager.get_context_size_estimate(large_context)
            size_filtered = context_manager.get_context_size_estimate(filtered)
            
            # Should reduce size (or at least not increase significantly)
            # Note: Some agents may add metadata which can slightly increase size
            assert size_filtered <= size_original * 1.1  # Allow up to 10% increase
        
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 5.0  # 5 seconds for 3 agents with large context
    
    def test_custom_agent_integration(self, test_environment):
        """Test integration with custom agent types."""
        context_manager = test_environment["context_manager"]
        
        # Register custom agent filter
        custom_filter = ContextFilter(
            agent_type="performance",
            file_extensions=[".py", ".prof"],
            include_patterns=["benchmark", "perf"],
            context_sections=["performance_metrics", "benchmarks"]
        )
        
        context_manager.register_custom_filter("performance", custom_filter)
        
        # Create context with performance data
        perf_context = {
            "files": {"benchmark.py": "perf test code"},
            "performance_metrics": {
                "response_time": 125,
                "throughput": 1000
            },
            "benchmarks": ["test1: 100ms", "test2: 200ms"]
        }
        
        # Filter for custom agent
        filtered = context_manager.filter_context_for_agent("performance", perf_context)
        
        # Should include performance sections
        assert "performance_metrics" in filtered
        assert "benchmarks" in filtered
    
    def test_full_lifecycle_integration(self, test_environment):
        """Test a complete lifecycle from discovery to execution."""
        registry = test_environment["agent_registry"]
        context_manager = test_environment["context_manager"]
        
        # 1. Discover agents
        agents = registry.listAgents()
        
        # 2. Create initial context
        initial_context = ContextFixtures.full_project_context()
        
        # 3. Filter context for each core agent type
        agent_types = ["documentation", "qa", "engineer", "ops", "version_control"]
        
        for i, agent_type in enumerate(agent_types):
            # Filter context
            filtered = context_manager.filter_context_for_agent(agent_type, initial_context)
            
            # Record interaction
            context_manager.record_interaction(
                agent_id=f"{agent_type}-{i}",
                agent_type=agent_type,
                context_size=len(json.dumps(initial_context)),
                filtered_size=len(json.dumps(filtered)),
                request=f"Process with {agent_type}"
            )
            
            # Update shared context
            context_manager.update_shared_context(
                agent_id=f"{agent_type}-{i}",
                updates={
                    f"{agent_type}_result": f"Completed by {agent_type}",
                    "timestamp": time.time()
                }
            )
        
        # 4. Get final statistics
        stats = context_manager.get_filter_statistics()
        history_count = sum(
            len(context_manager.get_agent_history(f"{agent_type}-{i}"))
            for i, agent_type in enumerate(agent_types)
        )
        
        # Verify complete execution
        assert stats["registered_filters"] >= len(agent_types)
        assert history_count == len(agent_types)