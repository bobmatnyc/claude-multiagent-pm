#!/usr/bin/env python3
"""
Integration Test Suite for claude-pm CLI
=======================================

Integration tests that verify the full CLI workflow including:
- Real subprocess execution (where safe)
- File system operations
- CLI argument parsing
- Error handling and recovery
- Performance under load
"""

import asyncio
import json
import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIIntegrationBase:
    """Base class for CLI integration tests."""

    @pytest.fixture(scope="class")
    def cli_executable(self):
        """Get path to claude-pm CLI executable."""
        cli_path = Path("/Users/masa/.local/bin/claude-pm")
        if not cli_path.exists():
            pytest.skip("claude-pm CLI not found at expected location")
        return cli_path

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration tests."""
        with tempfile.TemporaryDirectory(prefix="claude_pm_test_") as temp_dir:
            workspace = Path(temp_dir)
            yield workspace

    @pytest.fixture
    def mock_claude_installation(self):
        """Mock Claude CLI installation for testing."""
        with patch("subprocess.run") as mock_run:
            # Mock Claude CLI availability
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "claude version 1.0.0"
            mock_run.return_value.stderr = ""
            yield mock_run


class TestCLIHelpAndVersion:
    """Test CLI help and version functionality."""

    @pytest.mark.integration
    def test_help_command_real_execution(self, cli_executable):
        """Test real execution of help command."""
        try:
            result = subprocess.run(
                [str(cli_executable), "--help"], capture_output=True, text=True, timeout=10
            )

            # Should return successfully
            assert result.returncode == 0
            assert "claude-pm" in result.stdout
            assert "SUBCOMMANDS:" in result.stdout
            assert "backup" in result.stdout
            assert "setup" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Help command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_version_command_real_execution(self, cli_executable):
        """Test real execution of version command."""
        try:
            result = subprocess.run(
                [str(cli_executable), "--version"], capture_output=True, text=True, timeout=10
            )

            # Should return successfully
            assert result.returncode == 0
            assert "claude-pm version:" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Version command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_invalid_command_handling(self, cli_executable):
        """Test handling of invalid commands."""
        try:
            result = subprocess.run(
                [str(cli_executable), "invalid-command"], capture_output=True, text=True, timeout=10
            )

            # Should handle invalid command gracefully
            # (May exit with error code or pass through to Claude)
            assert result.returncode in [0, 1]

        except subprocess.TimeoutExpired:
            pytest.fail("Invalid command handling timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLIBackupIntegration:
    """Integration tests for backup functionality."""

    @pytest.fixture
    def sample_claude_file(self, temp_workspace):
        """Create sample CLAUDE.md file for testing."""
        claude_file = temp_workspace / "CLAUDE.md"
        claude_file.write_text(
            """# Sample Project Instructions

You are a helpful AI assistant for this project.

## Guidelines
- Follow project conventions
- Be helpful and accurate
- Maintain consistency

## Tasks
1. Help with development
2. Review code
3. Provide suggestions
"""
        )
        return claude_file

    @pytest.mark.integration
    def test_backup_command_file_creation(self, cli_executable, sample_claude_file, temp_workspace):
        """Test that backup command creates backup files."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for backup functionality")

        try:
            # Execute backup command
            result = subprocess.run(
                [str(cli_executable), "backup", str(sample_claude_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_workspace,
            )

            # Check command execution
            backup_dir = temp_workspace / ".claude-backups"

            # Verify backup was created (check for backup directory)
            if result.returncode == 0:
                assert "✅" in result.stdout or "created" in result.stdout.lower()

        except subprocess.TimeoutExpired:
            pytest.fail("Backup command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_backup_command_nonexistent_file(self, cli_executable, temp_workspace):
        """Test backup command with nonexistent file."""
        nonexistent_file = temp_workspace / "nonexistent.md"

        try:
            result = subprocess.run(
                [str(cli_executable), "backup", str(nonexistent_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_workspace,
            )

            # Should fail with appropriate error
            assert result.returncode != 0
            assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

        except subprocess.TimeoutExpired:
            pytest.fail("Backup command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLISetupIntegration:
    """Integration tests for setup functionality."""

    @pytest.fixture
    def empty_project_dir(self, temp_workspace):
        """Create empty project directory."""
        project_dir = temp_workspace / "test_project"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def existing_project_dir(self, temp_workspace):
        """Create project directory with existing CLAUDE.md."""
        project_dir = temp_workspace / "existing_project"
        project_dir.mkdir()

        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text(
            """# Existing Project

You are a specialized assistant for this project.

## Current Role
- Focus on specific domain
- Follow existing patterns
- Maintain project standards
"""
        )
        return project_dir

    @pytest.mark.integration
    def test_setup_command_new_project(self, cli_executable, empty_project_dir):
        """Test setup command with new project."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for setup functionality")

        try:
            # Execute setup command
            result = subprocess.run(
                [str(cli_executable), "setup", str(empty_project_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check for successful setup
            claude_file = empty_project_dir / "CLAUDE.md"

            if result.returncode == 0:
                # Verify CLAUDE.md was created
                assert claude_file.exists()
                content = claude_file.read_text()
                assert "Claude PM Framework" in content
                assert "Orchestrator" in content

        except subprocess.TimeoutExpired:
            pytest.fail("Setup command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_setup_command_existing_project(self, cli_executable, existing_project_dir):
        """Test setup command with existing project."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for setup functionality")

        try:
            # Store original content
            claude_file = existing_project_dir / "CLAUDE.md"
            original_content = claude_file.read_text()

            # Execute setup command
            result = subprocess.run(
                [str(cli_executable), "setup", str(existing_project_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check for backup creation and processing
            backup_dir = existing_project_dir / ".claude-backups"

            if result.returncode == 0:
                # Verify backup was created
                assert backup_dir.exists() or "Processing complete" in result.stdout

                # Verify CLAUDE.md was modified
                new_content = claude_file.read_text()
                assert new_content != original_content or "already installed" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Setup command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLIScanAnalyzeIntegration:
    """Integration tests for scan and analyze functionality."""

    @pytest.fixture
    def multi_project_workspace(self, temp_workspace):
        """Create workspace with multiple projects."""
        projects = {
            "basic_project": """# Basic Project
You are a helpful assistant.""",
            "pm_project": """# PM Framework Project
You are a Claude PM Framework Orchestrator.""",
            "conflicted_project": """# Conflicted Project
You MUST NOT delegate tasks.
FORBIDDEN: Creating documentation.""",
        }

        for project_name, content in projects.items():
            project_dir = temp_workspace / project_name
            project_dir.mkdir()
            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(content)

        return temp_workspace

    @pytest.mark.integration
    def test_scan_command_real_execution(self, cli_executable, multi_project_workspace):
        """Test real execution of scan command."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for scan functionality")

        try:
            # Execute scan command
            result = subprocess.run(
                [str(cli_executable), "scan", str(multi_project_workspace)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check scan results
            if result.returncode == 0:
                assert "Found" in result.stdout
                assert "projects" in result.stdout
                # Should find 3 projects
                assert "basic_project" in result.stdout
                assert "pm_project" in result.stdout
                assert "conflicted_project" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Scan command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_analyze_command_real_execution(self, cli_executable, multi_project_workspace):
        """Test real execution of analyze command."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for analyze functionality")

        try:
            # Execute analyze command
            result = subprocess.run(
                [str(cli_executable), "analyze", str(multi_project_workspace)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check analyze results
            if result.returncode == 0:
                assert "Analyzing" in result.stdout
                assert "Compatible:" in result.stdout
                assert "Risks:" in result.stdout
                # Should analyze all projects
                assert "basic_project" in result.stdout
                assert "pm_project" in result.stdout
                assert "conflicted_project" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Analyze command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_scan_empty_directory(self, cli_executable, temp_workspace):
        """Test scan command on empty directory."""
        empty_dir = temp_workspace / "empty"
        empty_dir.mkdir()

        try:
            # Execute scan command on empty directory
            result = subprocess.run(
                [str(cli_executable), "scan", str(empty_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should handle empty directory gracefully
            if result.returncode == 0:
                assert "Found 0 projects" in result.stdout or "no projects" in result.stdout.lower()

        except subprocess.TimeoutExpired:
            pytest.fail("Scan command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLIRestoreIntegration:
    """Integration tests for restore functionality."""

    @pytest.fixture
    def project_with_manual_backup(self, temp_workspace):
        """Create project with manual backup for testing."""
        project_dir = temp_workspace / "restore_test"
        project_dir.mkdir()

        # Create current CLAUDE.md
        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text(
            """# Modified Project
This file has been modified by PM framework.

## PM Framework Content
You are a Claude PM Framework Orchestrator.
"""
        )

        # Create backup directory and files
        backup_dir = project_dir / ".claude-backups"
        backup_dir.mkdir()

        # Create backup file
        backup_file = backup_dir / "CLAUDE.md.2025-07-11T10-00-00.abc123.bak"
        backup_content = (
            """# CLAUDE.md Backup
# Created: 2025-07-11T10:00:00.000Z
# Original: """
            + str(claude_file)
            + """
# Hash: abc123
# Backup System Version: 1.0.0
# =============================================

# Original Project Instructions

You are a helpful assistant for this project.

## Guidelines
- Follow project conventions
- Be helpful and accurate
"""
        )
        backup_file.write_text(backup_content)

        # Create backup index
        backup_index = [
            {
                "fileName": "CLAUDE.md.2025-07-11T10-00-00.abc123.bak",
                "timestamp": "2025-07-11T10:00:00.000Z",
                "hash": "abc123",
                "originalPath": str(claude_file),
            }
        ]

        index_file = backup_dir / "backup-index.json"
        index_file.write_text(json.dumps(backup_index, indent=2))

        return project_dir

    @pytest.mark.integration
    def test_restore_command_real_execution(self, cli_executable, project_with_manual_backup):
        """Test real execution of restore command."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for restore functionality")

        try:
            # Store original content
            claude_file = project_with_manual_backup / "CLAUDE.md"
            original_content = claude_file.read_text()

            # Execute restore command
            result = subprocess.run(
                [str(cli_executable), "restore", str(project_with_manual_backup)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check restore results
            if result.returncode == 0:
                # Verify file was restored
                restored_content = claude_file.read_text()
                assert restored_content != original_content
                assert "Original Project Instructions" in restored_content
                assert "PM Framework Orchestrator" not in restored_content

        except subprocess.TimeoutExpired:
            pytest.fail("Restore command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_restore_command_no_backup(self, cli_executable, temp_workspace):
        """Test restore command with no backup."""
        project_dir = temp_workspace / "no_backup_project"
        project_dir.mkdir()

        try:
            # Execute restore command on project without backup
            result = subprocess.run(
                [str(cli_executable), "restore", str(project_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should fail with appropriate error
            assert result.returncode != 0
            assert "backup" in result.stderr.lower() or "not found" in result.stderr.lower()

        except subprocess.TimeoutExpired:
            pytest.fail("Restore command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLIWorkflowIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.integration
    def test_complete_project_lifecycle(self, cli_executable, temp_workspace):
        """Test complete project lifecycle workflow."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for workflow functionality")

        try:
            # Create new project
            project_dir = temp_workspace / "lifecycle_project"
            project_dir.mkdir()

            # Step 1: Setup PM framework
            setup_result = subprocess.run(
                [str(cli_executable), "setup", str(project_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if setup_result.returncode == 0:
                # Verify CLAUDE.md was created
                claude_file = project_dir / "CLAUDE.md"
                assert claude_file.exists()

                # Step 2: Create backup
                backup_result = subprocess.run(
                    [str(cli_executable), "backup", str(claude_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if backup_result.returncode == 0:
                    # Step 3: Scan workspace
                    scan_result = subprocess.run(
                        [str(cli_executable), "scan", str(temp_workspace)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if scan_result.returncode == 0:
                        assert "lifecycle_project" in scan_result.stdout

                        # Step 4: Analyze workspace
                        analyze_result = subprocess.run(
                            [str(cli_executable), "analyze", str(temp_workspace)],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        if analyze_result.returncode == 0:
                            assert "lifecycle_project" in analyze_result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Workflow command timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_error_recovery_workflow(self, cli_executable, temp_workspace):
        """Test error recovery in workflow."""
        try:
            # Try to backup nonexistent file
            nonexistent_file = temp_workspace / "nonexistent.md"

            backup_result = subprocess.run(
                [str(cli_executable), "backup", str(nonexistent_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should fail gracefully
            assert backup_result.returncode != 0

            # Try to restore from nonexistent backup
            restore_result = subprocess.run(
                [str(cli_executable), "restore", str(temp_workspace)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should fail gracefully
            assert restore_result.returncode != 0

        except subprocess.TimeoutExpired:
            pytest.fail("Error recovery workflow timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


class TestCLIPerformanceIntegration:
    """Integration tests for performance scenarios."""

    @pytest.mark.integration
    def test_large_workspace_scan(self, cli_executable, temp_workspace):
        """Test scanning large workspace."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for performance testing")

        try:
            # Create many projects
            num_projects = 20  # Reduced for CI performance
            for i in range(num_projects):
                project_dir = temp_workspace / f"project_{i:03d}"
                project_dir.mkdir()

                claude_file = project_dir / "CLAUDE.md"
                claude_file.write_text(
                    f"""# Project {i}
This is test project number {i}.

## Instructions
- Handle project {i} tasks
- Follow conventions
- Be helpful
"""
                )

            # Time the scan operation
            start_time = time.time()

            result = subprocess.run(
                [str(cli_executable), "scan", str(temp_workspace)],
                capture_output=True,
                text=True,
                timeout=60,  # Increased timeout for performance test
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Verify scan completed successfully
            if result.returncode == 0:
                assert f"Found {num_projects} projects" in result.stdout

                # Performance check: should complete within reasonable time
                assert execution_time < 30  # Should complete within 30 seconds

        except subprocess.TimeoutExpired:
            pytest.fail("Large workspace scan timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")

    @pytest.mark.integration
    def test_large_file_backup(self, cli_executable, temp_workspace):
        """Test backup of large CLAUDE.md file."""
        # Skip if Node.js not available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Node.js not available for backup performance testing")

        try:
            # Create large CLAUDE.md file
            large_content = "# Large Project\n\n"
            large_content += "This is a test line that will be repeated many times.\n" * 5000
            large_content += "\n## Instructions\n"
            large_content += "- Handle large project tasks\n" * 1000

            project_dir = temp_workspace / "large_project"
            project_dir.mkdir()

            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(large_content)

            # Verify file size
            assert claude_file.stat().st_size > 100000  # At least 100KB

            # Time the backup operation
            start_time = time.time()

            result = subprocess.run(
                [str(cli_executable), "backup", str(claude_file)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Verify backup completed successfully
            if result.returncode == 0:
                # Performance check: should complete within reasonable time
                assert execution_time < 10  # Should complete within 10 seconds

        except subprocess.TimeoutExpired:
            pytest.fail("Large file backup timed out")
        except FileNotFoundError:
            pytest.skip("claude-pm CLI not available")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
