"""
Example E2E Test: Agent Discovery

This test demonstrates how to use the E2E test infrastructure
to test agent discovery functionality.
"""

import pytest
from pathlib import Path
from tests.e2e.utils import BaseE2ETest, MockSystem
from tests.e2e.fixtures import AgentFixtures, ConfigFixtures


class TestAgentDiscoveryE2E(BaseE2ETest):
    """E2E tests for agent discovery functionality."""
    
    @pytest.mark.core
    def test_discover_core_agents(self):
        """Test discovery of core framework agents."""
        # Create test agents
        for agent_data in AgentFixtures.all_core_agents():
            self.create_mock_agent(
                agent_data["name"],
                "project",
                agent_data["content"]
            )
        
        # Run discovery command
        result = self.run_claude_pm(["agents", "list"])
        
        # Validate discovery
        self.assert_command_success(result)
        
        # Check all core agents are discovered
        output = result.stdout
        core_agents = ["documentation", "qa", "engineer", "version_control", 
                      "research", "ops", "security", "ticketing", "data_engineer"]
        
        for agent in core_agents:
            assert agent in output, f"Core agent '{agent}' not found in discovery"
    
    @pytest.mark.core
    def test_agent_precedence(self):
        """Test agent directory precedence (project > user > system)."""
        # Create same agent in different directories
        agent_name = "test_agent"
        
        # Project agent (highest precedence)
        project_agent = self.create_mock_agent(
            agent_name, "project",
            "# Project Test Agent\nProject-specific version"
        )
        
        # User agent (medium precedence) 
        user_dir = Path(self.test_dir) / ".claude-pm" / "agents" / "user-defined"
        user_dir.mkdir(parents=True, exist_ok=True)
        user_agent = user_dir / f"{agent_name}.md"
        user_agent.write_text("# User Test Agent\nUser-defined version")
        
        # System agent would be lowest precedence
        
        # Test precedence
        result = self.run_claude_pm(["agents", "show", agent_name])
        self.assert_command_success(result)
        
        # Should show project version
        assert "Project-specific version" in result.stdout
        assert "User-defined version" not in result.stdout
    
    @pytest.mark.core
    @pytest.mark.slow
    def test_agent_discovery_with_specializations(self):
        """Test discovering agents by specialization."""
        # Create agents with different specializations
        test_agents = [
            AgentFixtures.custom_agent(
                "performance_agent",
                ["performance", "optimization"],
                ["Monitor performance", "Optimize code"]
            ),
            AgentFixtures.custom_agent(
                "ui_agent",
                ["ui_ux", "frontend"],
                ["Design interfaces", "Implement UI"]
            ),
            AgentFixtures.custom_agent(
                "data_agent",
                ["data", "analytics"],
                ["Process data", "Generate reports"]
            )
        ]
        
        for agent_data in test_agents:
            AgentFixtures.create_mock_agent_file(
                Path(self.test_dir) / ".claude-pm" / "agents",
                agent_data
            )
        
        # Test specialization discovery
        result = self.run_claude_pm(
            ["agents", "list", "--specialization", "performance"]
        )
        self.assert_command_success(result)
        assert "performance_agent" in result.stdout
        assert "ui_agent" not in result.stdout
    
    @pytest.mark.orchestration
    def test_agent_selection_for_task(self):
        """Test automatic agent selection based on task requirements."""
        # Setup mock system
        mock_system = MockSystem()
        mock_system.setup()
        
        # Create specialized agents
        agents = [
            AgentFixtures.documentation_agent(),
            AgentFixtures.qa_agent(),
            AgentFixtures.engineer_agent()
        ]
        
        for agent_data in agents:
            self.create_mock_agent(
                agent_data["name"],
                "project",
                agent_data["content"]
            )
        
        # Test task delegation
        test_cases = [
            ("Generate changelog for version 1.0.0", "documentation"),
            ("Run unit tests for new feature", "qa"),
            ("Implement user authentication", "engineer")
        ]
        
        for task, expected_agent in test_cases:
            result = self.run_claude_pm(["task", "delegate", task])
            self.assert_command_success(result)
            assert expected_agent in result.stdout.lower()
    
    @pytest.mark.integration
    def test_agent_registry_caching(self):
        """Test agent registry caching for performance."""
        # Create configuration with caching enabled
        config = ConfigFixtures.merge_configs(
            ConfigFixtures.base_config(),
            ConfigFixtures.agent_registry_config()
        )
        config_path = self.create_test_config(config)
        
        # Create multiple agents
        for i in range(10):
            self.create_mock_agent(f"test_agent_{i}", "project")
        
        # First discovery (cache miss)
        import time
        start_time = time.time()
        result1 = self.run_claude_pm(["agents", "list"])
        first_duration = time.time() - start_time
        self.assert_command_success(result1)
        
        # Second discovery (cache hit - should be faster)
        start_time = time.time()
        result2 = self.run_claude_pm(["agents", "list"])
        second_duration = time.time() - start_time
        self.assert_command_success(result2)
        
        # Cache should make second call faster
        assert second_duration < first_duration * 0.5, \
            "Cache doesn't seem to be working effectively"
        
        # Results should be identical
        assert result1.stdout == result2.stdout
    
    @pytest.mark.isolated
    def test_agent_discovery_error_handling(self):
        """Test error handling in agent discovery."""
        # Test with corrupted agent file
        bad_agent = self.create_mock_agent(
            "corrupted_agent", "project",
            "This is not valid agent format"
        )
        
        # Discovery should handle gracefully
        result = self.run_claude_pm(["agents", "list"])
        
        # Should succeed but potentially warn about corrupted agent
        assert result.returncode == 0 or "warning" in result.stderr.lower()
        
        # Test with missing directory
        import shutil
        shutil.rmtree(Path(self.test_dir) / ".claude-pm" / "agents")
        
        result = self.run_claude_pm(["agents", "list"])
        # Should handle missing directory gracefully
        assert result.returncode == 0 or "not found" in result.stderr