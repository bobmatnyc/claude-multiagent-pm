#!/usr/bin/env python3
"""
Test AI-Trackdown-Tools CLI integration for SystemInitAgent.

This test verifies that the CLI integration works correctly with both
available and unavailable AI-Trackdown-Tools installations.
"""

import os
import sys
import json
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.agents.system_init_agent import SystemInitAgent


class TestAITrackdownToolsIntegration:
    """Test class for AI-Trackdown-Tools CLI integration."""
    
    def setup_method(self, method):
        """Set up test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent = SystemInitAgent(working_dir=self.temp_dir)
    
    def teardown_method(self, method):
        """Tear down test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_check_aitrackdown_availability_not_available(self):
        """Test CLI availability check when not available."""
        # Test with directory that has no CLI
        result = self.agent.check_aitrackdown_availability(self.temp_dir)
        
        assert result["available"] is False
        assert result["version"] == "none"
        assert result["local_cli"] is False
        assert result["cli_path"] is None
        assert result["config_path"] is None
    
    def test_check_aitrackdown_availability_config_only(self):
        """Test CLI availability check with config but no CLI."""
        # Create .ai-trackdown directory
        (self.temp_dir / ".ai-trackdown").mkdir()
        
        result = self.agent.check_aitrackdown_availability(self.temp_dir)
        
        assert result["available"] is False
        assert result["version"] == "config-only"
        assert result["local_cli"] is False
        assert result["cli_path"] is None
        assert result["config_path"] == str(self.temp_dir / ".ai-trackdown")
        assert "note" in result
    
    def test_check_aitrackdown_availability_local_cli(self):
        """Test CLI availability check with local CLI."""
        # Create local CLI path
        bin_dir = self.temp_dir / "bin"
        bin_dir.mkdir()
        cli_path = bin_dir / "aitrackdown"
        cli_path.write_text("#!/bin/bash\necho '1.0.0'")
        cli_path.chmod(0o755)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1.0.0"
            
            result = self.agent.check_aitrackdown_availability(self.temp_dir)
            
            assert result["available"] is True
            assert result["version"] == "1.0.0"
            assert result["local_cli"] is True
            assert result["cli_path"] == str(cli_path)
    
    @patch('subprocess.run')
    def test_check_aitrackdown_availability_global_cli(self, mock_run):
        """Test CLI availability check with global CLI."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "2.0.0"
        
        result = self.agent.check_aitrackdown_availability(self.temp_dir)
        
        assert result["available"] is True
        assert result["version"] == "2.0.0"
        assert result["local_cli"] is False
        assert result["cli_path"] == "aitrackdown"
    
    def test_collect_basic_project_data(self):
        """Test basic project data collection fallback."""
        # Create some project files
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / "package.json").write_text('{"name": "test-project"}')
        (self.temp_dir / "pyproject.toml").write_text('[tool.poetry]\nname = "test"')
        
        result = self.agent.collect_basic_project_data(self.temp_dir)
        
        # Check structure
        assert "aiTrackdownTools" in result
        assert "projectData" in result
        assert "statistics" in result
        
        # Check AI-Trackdown-Tools info
        ai_info = result["aiTrackdownTools"]
        assert ai_info["available"] is False
        assert ai_info["version"] == "none"
        assert ai_info["localCli"] is False
        assert "note" in ai_info
        
        # Check project indicators
        indicators = result["projectData"]["indicators"]
        indicator_files = [ind["file"] for ind in indicators]
        assert ".git" in indicator_files
        assert "package.json" in indicator_files
        assert "pyproject.toml" in indicator_files
        
        # Check statistics
        stats = result["statistics"]
        assert stats["projectPath"] == str(self.temp_dir)
        assert stats["projectName"] == self.temp_dir.name
        assert stats["hasGit"] is True
        assert stats["hasPackageJson"] is True
        assert stats["hasPyproject"] is True
    
    @patch('subprocess.run')
    async def test_collect_project_data_via_cli_success(self, mock_run):
        """Test CLI data collection with successful CLI responses."""
        # Mock CLI availability
        with patch.object(self.agent, 'check_aitrackdown_availability') as mock_check:
            mock_check.return_value = {
                "available": True,
                "version": "1.0.0",
                "local_cli": True,
                "cli_path": "aitrackdown",
                "config_path": str(self.temp_dir / ".ai-trackdown")
            }
            
            # Mock CLI responses
            mock_responses = [
                # epic list --json
                json.dumps({"epics": [{"id": "EP-001", "status": "active"}]}),
                # issue list --json
                json.dumps({"issues": [{"id": "ISS-001", "priority": "high", "status": "in-progress"}]}),
                # task list --json
                json.dumps({"tasks": [{"id": "TSK-001", "status": "active"}]}),
                # status --stats --json
                json.dumps({"completionRate": "75%", "lastActivity": "2025-07-09", "velocity": "5 items/week"})
            ]
            
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=response) for response in mock_responses
            ]
            
            result = await self.agent.collect_project_data_via_cli(self.temp_dir)
            
            # Check structure
            assert "aiTrackdownTools" in result
            assert "projectData" in result
            assert "statistics" in result
            
            # Check AI-Trackdown-Tools info
            ai_info = result["aiTrackdownTools"]
            assert ai_info["available"] is True
            assert ai_info["version"] == "1.0.0"
            assert ai_info["localCli"] is True
            
            # Check project data
            project_data = result["projectData"]
            assert project_data["epics"]["total"] == 1
            assert project_data["epics"]["active"] == 1
            assert project_data["issues"]["total"] == 1
            assert project_data["issues"]["high"] == 1
            assert project_data["tasks"]["total"] == 1
            assert project_data["tasks"]["active"] == 1
            
            # Check statistics
            stats = result["statistics"]
            assert stats["completionRate"] == "75%"
            assert stats["lastActivity"] == "2025-07-09"
            assert stats["velocity"] == "5 items/week"
    
    @patch('subprocess.run')
    async def test_collect_project_data_via_cli_fallback(self, mock_run):
        """Test CLI data collection with fallback to basic data."""
        # Mock CLI not available
        with patch.object(self.agent, 'check_aitrackdown_availability') as mock_check:
            mock_check.return_value = {
                "available": False,
                "version": "none",
                "local_cli": False,
                "cli_path": None,
                "config_path": None
            }
            
            result = await self.agent.collect_project_data_via_cli(self.temp_dir)
            
            # Should fall back to basic data
            assert "aiTrackdownTools" in result
            assert result["aiTrackdownTools"]["available"] is False
            assert "note" in result["aiTrackdownTools"]
    
    async def test_scan_current_project_with_cli_integration(self):
        """Test project scanning with CLI integration."""
        # Create project files
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / "package.json").write_text('{"name": "test-project"}')
        
        # Mock CLI data collection
        with patch.object(self.agent, 'collect_project_data_via_cli') as mock_collect:
            mock_collect.return_value = {
                "aiTrackdownTools": {
                    "available": True,
                    "version": "1.0.0",
                    "localCli": False
                },
                "projectData": {
                    "epics": {"total": 2, "active": 1},
                    "issues": {"total": 5, "high": 2}
                },
                "statistics": {
                    "completionRate": "60%",
                    "velocity": "3 items/week"
                }
            }
            
            result = await self.agent._scan_current_project()
            
            # Check basic project info
            assert result["name"] == self.temp_dir.name
            assert result["path"] == str(self.temp_dir)
            assert result["type"] == "standalone"  # has .git
            assert result["health"] == "operational"
            
            # Check CLI integration data
            assert "aiTrackdownTools" in result
            assert result["aiTrackdownTools"]["available"] is True
            assert "projectData" in result
            assert "statistics" in result
    
    def test_detect_project_type(self):
        """Test project type detection."""
        # Test claude-pm-framework
        claude_pm_dir = self.temp_dir / "claude_pm"
        claude_pm_dir.mkdir()
        (claude_pm_dir / "__init__.py").write_text("")
        
        assert self.agent._detect_project_type(self.temp_dir) == "claude-pm-framework"
        
        # Clean up and test managed
        import shutil
        shutil.rmtree(claude_pm_dir)
        (self.temp_dir / ".claude-pm").mkdir()
        
        assert self.agent._detect_project_type(self.temp_dir) == "managed"
        
        # Clean up and test standalone
        shutil.rmtree(self.temp_dir / ".claude-pm")
        (self.temp_dir / ".git").mkdir()
        
        assert self.agent._detect_project_type(self.temp_dir) == "standalone"
        
        # Clean up and test unknown
        shutil.rmtree(self.temp_dir / ".git")
        
        assert self.agent._detect_project_type(self.temp_dir) == "unknown"


async def test_integration_flow():
    """Test the complete integration flow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a test project
        (temp_path / ".git").mkdir()
        (temp_path / "package.json").write_text('{"name": "test-project"}')
        
        # Initialize agent
        agent = SystemInitAgent(working_dir=temp_path)
        
        # Test CLI availability check
        availability = agent.check_aitrackdown_availability(temp_path)
        print(f"CLI Availability: {availability}")
        
        # Test basic project data collection
        basic_data = agent.collect_basic_project_data(temp_path)
        print(f"Basic Data: {basic_data['aiTrackdownTools']['available']}")
        
        # Test full CLI integration
        cli_data = await agent.collect_project_data_via_cli(temp_path)
        print(f"CLI Data: {cli_data['aiTrackdownTools']['available']}")
        
        # Test project scanning
        project_info = await agent._scan_current_project()
        print(f"Project Info: {project_info['name']} ({project_info['type']})")
        
        print("✅ Integration flow test completed successfully!")


if __name__ == "__main__":
    # Run integration flow test
    asyncio.run(test_integration_flow())
    print("\n🎯 All tests completed! Run with pytest for detailed testing.")