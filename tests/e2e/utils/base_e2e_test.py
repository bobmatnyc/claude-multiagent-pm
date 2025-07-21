"""
Base E2E Test Class for Claude Multi-Agent PM Framework

This module provides the foundational test class for all E2E tests,
ensuring consistent setup/teardown and providing common utilities.
"""

import os
import pytest
import tempfile
import shutil
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock
import asyncio


class BaseE2ETest:
    """Base class for E2E tests with common setup and utilities."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test method."""
        # Setup
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp(prefix="e2e_test_")
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Create test environment
        self._setup_test_environment()
        
        # Store original environment variables
        self.original_env = os.environ.copy()
        
        yield
        
        # Teardown
        self._teardown_test_environment()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def _setup_test_environment(self):
        """Set up the test environment with necessary directories and files."""
        os.chdir(self.test_dir)
        
        # Create standard test directory structure
        os.makedirs(".claude-pm/agents/project-specific", exist_ok=True)
        os.makedirs(".claude-pm/memory", exist_ok=True)
        os.makedirs(".claude-pm/config", exist_ok=True)
        
        # Create default config
        config = {
            "version": "1.0.0",
            "test_mode": True,
            "framework_version": "0.7.0"
        }
        with open(".claude-pm/config/test_config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _teardown_test_environment(self):
        """Clean up the test environment."""
        # Remove any test artifacts
        test_artifacts = [
            "*.log",
            "*.tmp",
            ".claude-pm-test-*"
        ]
        for pattern in test_artifacts:
            for file in Path(self.test_dir).glob(pattern):
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file, ignore_errors=True)
    
    def create_test_project(self, name: str = "test_project") -> Path:
        """Create a test project directory with basic structure."""
        project_dir = Path(self.test_dir) / name
        project_dir.mkdir(exist_ok=True)
        
        # Create project structure
        (project_dir / ".claude-pm").mkdir(exist_ok=True)
        (project_dir / ".claude-pm" / "agents").mkdir(exist_ok=True)
        
        # Create CLAUDE.md
        claude_md = project_dir / "CLAUDE.md"
        claude_md.write_text("""# Test Project Configuration

This is a test project for E2E testing.

## Configuration
- Framework Version: 0.7.0
- Test Mode: True
""")
        
        return project_dir
    
    def run_claude_pm(self, args: List[str], cwd: Optional[str] = None, 
                      env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run claude-pm CLI command and return result."""
        cmd = [sys.executable, "-m", "claude_pm.cli"] + args
        
        test_env = os.environ.copy()
        if env:
            test_env.update(env)
        
        # Add test mode flag
        test_env["CLAUDE_PM_TEST_MODE"] = "1"
        
        result = subprocess.run(
            cmd,
            cwd=cwd or self.test_dir,
            env=test_env,
            capture_output=True,
            text=True
        )
        
        return result
    
    def assert_command_success(self, result: subprocess.CompletedProcess, 
                               expected_output: Optional[str] = None):
        """Assert that a command executed successfully."""
        assert result.returncode == 0, f"Command failed with: {result.stderr}"
        
        if expected_output:
            assert expected_output in result.stdout, \
                f"Expected '{expected_output}' in output, got: {result.stdout}"
    
    def assert_command_failure(self, result: subprocess.CompletedProcess,
                               expected_error: Optional[str] = None):
        """Assert that a command failed as expected."""
        assert result.returncode != 0, "Command should have failed but succeeded"
        
        if expected_error:
            assert expected_error in result.stderr or expected_error in result.stdout, \
                f"Expected error '{expected_error}' not found in output"
    
    def create_mock_agent(self, agent_name: str, agent_type: str = "user", 
                          content: Optional[str] = None) -> Path:
        """Create a mock agent file for testing."""
        agent_dir = Path(self.test_dir) / ".claude-pm" / "agents"
        if agent_type == "project":
            agent_dir = agent_dir / "project-specific"
        elif agent_type == "user":
            agent_dir = agent_dir / "user-defined"
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        agent_file = agent_dir / f"{agent_name}.md"
        
        if content is None:
            content = f"""# {agent_name.title()} Agent

## Role
Test agent for {agent_name} operations.

## Capabilities
- Test capability 1
- Test capability 2

## Authority
- Test authority scope
"""
        
        agent_file.write_text(content)
        return agent_file
    
    async def run_async_test(self, coro):
        """Helper to run async tests."""
        return await coro
    
    def mock_external_service(self, service_name: str) -> MagicMock:
        """Create a mock for external services."""
        mock = MagicMock()
        mock.service_name = service_name
        mock.is_available = True
        mock.call_count = 0
        
        def track_calls(*args, **kwargs):
            mock.call_count += 1
            return {"status": "success", "service": service_name}
        
        mock.call = track_calls
        return mock
    
    def create_test_config(self, config_data: Dict[str, Any]) -> Path:
        """Create a test configuration file."""
        config_path = Path(self.test_dir) / ".claude-pm" / "config" / "test.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        
        return config_path
    
    def verify_file_exists(self, filepath: str) -> bool:
        """Verify that a file exists in the test directory."""
        full_path = Path(self.test_dir) / filepath
        return full_path.exists()
    
    def read_test_file(self, filepath: str) -> str:
        """Read content from a test file."""
        full_path = Path(self.test_dir) / filepath
        return full_path.read_text()
    
    def write_test_file(self, filepath: str, content: str) -> Path:
        """Write content to a test file."""
        full_path = Path(self.test_dir) / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path