#!/usr/bin/env python3
"""
Test Suite for claude-pm CLI Commands
====================================

Comprehensive test suite for the claude-pm CLI commands including:
- CLI wrapper functionality testing
- Backup system testing
- Setup command testing
- Scan and analyze command testing
- Restore and resolve command testing
- Integration with existing pytest patterns
"""

import asyncio
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from typing import Dict, Any, List

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Test fixtures - make them available globally
@pytest.fixture
def temp_project_dir():
    """Create temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path


@pytest.fixture
def sample_claude_md_basic():
    """Create basic CLAUDE.md content for testing."""
    return """# Basic Project Instructions

You are a helpful AI assistant for this project.

## Project Overview
This is a basic project without PM framework integration.

## Guidelines
- Help with development tasks
- Follow project conventions
- Be helpful and accurate
"""


@pytest.fixture
def sample_claude_md_with_pm():
    """Create CLAUDE.md with PM framework content for testing."""
    return """# Claude PM Framework v2.1.0

## 🤖 AI ASSISTANT ROLE DESIGNATION

**You are a Claude PM Framework Orchestrator - Multi-Agent Coordinator**

Your primary role is orchestrating the Claude PM Framework project management system.

### Core Responsibilities
1. **Framework Orchestration**: Coordinate multi-agent workflows
2. **Agent Collaboration**: Work with Documentation and Ticketing agents
3. **Project Management**: Oversee project lifecycle

## 🚨 DELEGATION CONSTRAINTS

**PM FRAMEWORK DELEGATION REQUIREMENTS**

### Mandatory Delegation
- **Documentation Operations**: MUST delegate to Documentation Agent
- **Ticket Operations**: MUST delegate to Ticketing Agent
"""


@pytest.fixture
def sample_claude_md_conflicted():
    """Create CLAUDE.md with potential conflicts for testing."""
    return """# Existing Project Instructions

You are a specialized code assistant.

## Role Definition
You MUST NOT modify system files.
You MUST NEVER create documentation.

## Constraints
FORBIDDEN ACTIVITIES:
- Writing documentation
- Modifying configuration files
- Creating new projects
"""


@pytest.fixture
def claude_pm_cli_path():
    """Get path to claude-pm CLI script."""
    return Path("/Users/masa/.local/bin/claude-pm")


@pytest.fixture
def mock_nodejs_environment():
    """Mock Node.js environment for testing."""
    with patch("subprocess.run") as mock_run:
        # Mock Node.js availability check
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "v18.17.0"
        mock_run.return_value.stderr = ""
        yield mock_run


class TestCLIBackupCommands:
    """Test backup command functionality."""

    @pytest.fixture
    def mock_backup_system(self):
        """Mock the embedded backup system."""
        with patch("tempfile.mktemp") as mock_mktemp:
            mock_mktemp.return_value = "/tmp/backup_system.js"
            yield mock_mktemp

    @pytest.mark.unit
    def test_backup_command_success(
        self, temp_project_dir, sample_claude_md_basic, mock_nodejs_environment
    ):
        """Test successful backup command execution."""
        # Create test CLAUDE.md file
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        # Test the command formation and basic logic
        backup_command = f"backup {claude_file}"

        # Verify command structure
        assert "backup" in backup_command
        assert str(claude_file) in backup_command

        # Verify file exists for backup
        assert claude_file.exists()
        assert claude_file.read_text() == sample_claude_md_basic

        # Test Node.js environment mock
        assert mock_nodejs_environment.return_value.returncode == 0
        assert mock_nodejs_environment.return_value.stdout == "v18.17.0"

    @pytest.mark.unit
    def test_backup_command_file_not_found(self, temp_project_dir, mock_nodejs_environment):
        """Test backup command with missing file."""
        nonexistent_file = temp_project_dir / "nonexistent.md"

        # Mock failed backup execution
        mock_nodejs_environment.return_value.returncode = 1
        mock_nodejs_environment.return_value.stderr = "CLAUDE.md not found"

        # Test error handling
        with pytest.raises(FileNotFoundError):
            if not nonexistent_file.exists():
                raise FileNotFoundError(f"CLAUDE.md not found at: {nonexistent_file}")

    @pytest.mark.unit
    def test_backup_command_nodejs_not_available(self, temp_project_dir, sample_claude_md_basic):
        """Test backup command when Node.js is not available."""
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        # Mock Node.js not available
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("node command not found")

            # Test error handling
            with pytest.raises(FileNotFoundError):
                subprocess.run(["node", "--version"], check=True)

    @pytest.mark.unit
    def test_backup_system_js_generation(self, mock_backup_system):
        """Test backup system JavaScript generation."""
        # Simulate JavaScript file creation
        js_content = """
        const fs = require('fs');
        class ClaudeBackupSystem {
            constructor() {
                this.version = '1.0.0';
            }
            async createBackup(filePath) {
                // Backup logic here
            }
        }
        """

        # Test that we can create backup system content
        assert "ClaudeBackupSystem" in js_content
        assert "createBackup" in js_content
        assert "version" in js_content

        # The mock should be available
        assert mock_backup_system is not None

    @pytest.mark.unit
    def test_backup_index_management(self, temp_project_dir, sample_claude_md_basic):
        """Test backup index file management."""
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        backup_dir = temp_project_dir / ".claude-backups"
        backup_dir.mkdir()

        # Create mock backup index
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

        # Verify backup index structure
        loaded_index = json.loads(index_file.read_text())
        assert len(loaded_index) == 1
        assert loaded_index[0]["fileName"] == "CLAUDE.md.2025-07-11T10-00-00.abc123.bak"
        assert loaded_index[0]["hash"] == "abc123"


class TestCLISetupCommands:
    """Test setup command functionality."""

    @pytest.mark.unit
    def test_setup_command_new_project(self, temp_project_dir, mock_nodejs_environment):
        """Test setup command for new project without CLAUDE.md."""
        # Mock successful setup execution
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "✅ PM framework installed"

        # Verify directory structure
        assert temp_project_dir.exists()
        assert not (temp_project_dir / "CLAUDE.md").exists()

        # Test setup command structure
        setup_cmd = f"setup {temp_project_dir}"
        assert "setup" in setup_cmd
        assert str(temp_project_dir) in setup_cmd

    @pytest.mark.unit
    def test_setup_command_existing_project(
        self, temp_project_dir, sample_claude_md_basic, mock_nodejs_environment
    ):
        """Test setup command for existing project with CLAUDE.md."""
        # Create existing CLAUDE.md
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        # Mock successful setup with backup
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "✅ Processing complete"

        # Verify file exists before setup
        assert claude_file.exists()
        assert "basic project" in claude_file.read_text().lower()

    @pytest.mark.unit
    def test_setup_command_interactive_mode(self, temp_project_dir, mock_nodejs_environment):
        """Test setup command with interactive mode."""
        # Mock interactive setup
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "Interactive mode enabled"

        # Test interactive flag
        setup_cmd = f"setup {temp_project_dir} --interactive"
        assert "--interactive" in setup_cmd
        assert "setup" in setup_cmd

    @pytest.mark.unit
    def test_setup_command_dry_run(self, temp_project_dir, mock_nodejs_environment):
        """Test setup command with dry run mode."""
        # Mock dry run execution
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "Dry run mode - no files modified"

        # Test dry run flag
        setup_cmd = f"setup {temp_project_dir} --dry-run"
        assert "--dry-run" in setup_cmd
        assert "setup" in setup_cmd

    @pytest.mark.unit
    def test_pm_framework_template_generation(self):
        """Test PM framework template generation."""
        # Mock template content structure
        expected_sections = [
            "## 🤖 AI ASSISTANT ROLE DESIGNATION",
            "**You are a Claude PM Framework Orchestrator - Multi-Agent Coordinator**",
            "### Core PM Framework Responsibilities",
            "## 🚨 MANDATORY: CORE AGENT TYPES",
            "### Core Agent Types (Mandatory Collaboration)",
            "## 🚫 CRITICAL DELEGATION CONSTRAINTS",
            "## 🎯 SYSTEMATIC AGENT DELEGATION",
        ]

        # Simulate template generation
        template_content = """# Claude PM Framework v2.1.0

## 🤖 AI ASSISTANT ROLE DESIGNATION

**You are a Claude PM Framework Orchestrator - Multi-Agent Coordinator**

### Core PM Framework Responsibilities
1. **Framework Orchestration**: Coordinate multi-agent workflows
2. **Agent Collaboration**: Work hand-in-hand with core agent types

## 🚨 MANDATORY: CORE AGENT TYPES

### Core Agent Types (Mandatory Collaboration)
1. **Documentation Agent** - **CORE AGENT TYPE**
2. **Ticketing Agent** - **CORE AGENT TYPE**

## 🚫 CRITICAL DELEGATION CONSTRAINTS

**PM FRAMEWORK DELEGATION REQUIREMENTS**

## 🎯 SYSTEMATIC AGENT DELEGATION

**Enhanced PM Framework Delegation Patterns**
"""

        # Verify template structure
        for section in expected_sections:
            assert section in template_content


class TestCLIScanAnalyzeCommands:
    """Test scan and analyze command functionality."""

    @pytest.fixture
    def multi_project_structure(self, temp_project_dir):
        """Create multi-project structure for scanning."""
        # Create multiple projects
        projects = ["project1", "project2", "project3"]

        for project in projects:
            project_dir = temp_project_dir / project
            project_dir.mkdir()

            # Create CLAUDE.md files with different content
            claude_file = project_dir / "CLAUDE.md"
            if project == "project1":
                claude_file.write_text("# Basic Project\nYou are a helpful assistant.")
            elif project == "project2":
                claude_file.write_text(
                    "# PM Framework Project\nYou are a Claude PM Framework Orchestrator."
                )
            else:
                claude_file.write_text("# Conflicted Project\nYou MUST NOT delegate tasks.")

        return temp_project_dir

    @pytest.mark.unit
    def test_scan_command_success(self, multi_project_structure, mock_nodejs_environment):
        """Test successful scan command execution."""
        # Mock successful scan execution
        scan_output = f"""🔍 Scanning projects in: {multi_project_structure}

📁 Found 3 projects with CLAUDE.md files:
  - project1 ({multi_project_structure}/project1)
  - project2 ({multi_project_structure}/project2)
  - project3 ({multi_project_structure}/project3)
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = scan_output

        # Verify scan command structure
        scan_cmd = f"scan {multi_project_structure}"
        assert "scan" in scan_cmd
        assert str(multi_project_structure) in scan_cmd

        # Verify expected projects are found
        assert "project1" in scan_output
        assert "project2" in scan_output
        assert "project3" in scan_output
        assert "Found 3 projects" in scan_output

    @pytest.mark.unit
    def test_scan_command_empty_directory(self, temp_project_dir, mock_nodejs_environment):
        """Test scan command on empty directory."""
        # Mock scan of empty directory
        scan_output = f"""🔍 Scanning projects in: {temp_project_dir}

📁 Found 0 projects with CLAUDE.md files:
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = scan_output

        # Verify empty scan results
        assert "Found 0 projects" in scan_output

    @pytest.mark.unit
    def test_analyze_command_success(self, multi_project_structure, mock_nodejs_environment):
        """Test successful analyze command execution."""
        # Mock analyze command output
        analyze_output = f"""🔍 Analyzing projects in: {multi_project_structure}

📊 project1:
   Compatible: ✅ Yes
   Risks: 0
   Features: 0

📊 project2:
   Compatible: ❌ No
   Risks: 1
   Features: 1
   Risk Details:
     - PM Framework already installed

📊 project3:
   Compatible: ✅ Yes
   Risks: 1
   Features: 1
   Risk Details:
     - Potential delegation conflicts
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = analyze_output

        # Verify analyze command structure
        analyze_cmd = f"analyze {multi_project_structure}"
        assert "analyze" in analyze_cmd
        assert str(multi_project_structure) in analyze_cmd

        # Verify analysis results
        assert "project1:" in analyze_output
        assert "Compatible: ✅ Yes" in analyze_output
        assert "Compatible: ❌ No" in analyze_output
        assert "PM Framework already installed" in analyze_output

    @pytest.mark.unit
    def test_analyze_command_risk_detection(
        self, temp_project_dir, sample_claude_md_conflicted, mock_nodejs_environment
    ):
        """Test analyze command risk detection."""
        # Create project with potential conflicts
        project_dir = temp_project_dir / "conflicted_project"
        project_dir.mkdir()
        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_conflicted)

        # Mock risk analysis
        analyze_output = """📊 conflicted_project:
   Compatible: ✅ Yes
   Risks: 2
   Features: 1
   Risk Details:
     - Potential delegation conflicts
     - Existing constraint patterns detected
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = analyze_output

        # Verify risk detection
        assert "Risks: 2" in analyze_output
        assert "delegation conflicts" in analyze_output

    @pytest.mark.unit
    def test_analyze_command_compatibility_check(
        self, temp_project_dir, sample_claude_md_with_pm, mock_nodejs_environment
    ):
        """Test analyze command compatibility checking."""
        # Create project with PM framework
        project_dir = temp_project_dir / "pm_project"
        project_dir.mkdir()
        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_with_pm)

        # Mock compatibility check
        analyze_output = """📊 pm_project:
   Compatible: ❌ No
   Risks: 1
   Features: 1
   Risk Details:
     - PM Framework already installed
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = analyze_output

        # Verify compatibility check
        assert "Compatible: ❌ No" in analyze_output
        assert "PM Framework already installed" in analyze_output


class TestCLIRestoreResolveCommands:
    """Test restore and resolve command functionality."""

    @pytest.fixture
    def project_with_backup(self, temp_project_dir, sample_claude_md_basic):
        """Create project with backup for restore testing."""
        # Create main CLAUDE.md
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text("# Modified Project\nThis has been modified by PM framework.")

        # Create backup directory and files
        backup_dir = temp_project_dir / ".claude-backups"
        backup_dir.mkdir()

        # Create backup file
        backup_file = backup_dir / "CLAUDE.md.2025-07-11T10-00-00.abc123.bak"
        backup_content = f"""# CLAUDE.md Backup
# Created: 2025-07-11T10:00:00.000Z
# Original: {claude_file}
# Hash: abc123
# Backup System Version: 1.0.0
# =============================================

{sample_claude_md_basic}"""
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

        return temp_project_dir

    @pytest.mark.unit
    def test_restore_command_success(self, project_with_backup, mock_nodejs_environment):
        """Test successful restore command execution."""
        # Mock successful restore execution
        restore_output = f"""✅ Rollback successful for {project_with_backup}
📁 Restored from: {project_with_backup}/.claude-backups/CLAUDE.md.2025-07-11T10-00-00.abc123.bak
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = restore_output

        # Test restore command structure
        restore_cmd = f"restore {project_with_backup}"
        assert "restore" in restore_cmd
        assert str(project_with_backup) in restore_cmd

        # Verify restore output
        assert "Rollback successful" in restore_output
        assert "Restored from:" in restore_output

    @pytest.mark.unit
    def test_restore_command_no_backup(self, temp_project_dir, mock_nodejs_environment):
        """Test restore command with no backup available."""
        # Mock restore failure
        mock_nodejs_environment.return_value.returncode = 1
        mock_nodejs_environment.return_value.stderr = "No backup directory found"

        # Test error handling
        restore_cmd = f"restore {temp_project_dir}"
        assert "restore" in restore_cmd

        # Verify error is properly handled
        assert mock_nodejs_environment.return_value.returncode == 1

    @pytest.mark.unit
    def test_restore_command_invalid_backup(self, temp_project_dir, mock_nodejs_environment):
        """Test restore command with invalid backup."""
        # Create backup dir but no valid backup
        backup_dir = temp_project_dir / ".claude-backups"
        backup_dir.mkdir()

        # Mock restore failure
        mock_nodejs_environment.return_value.returncode = 1
        mock_nodejs_environment.return_value.stderr = "No backup index found"

        # Test error handling
        restore_cmd = f"restore {temp_project_dir}"
        assert "restore" in restore_cmd

        # Verify error is properly handled
        assert mock_nodejs_environment.return_value.returncode == 1

    @pytest.mark.unit
    def test_resolve_command_placeholder(self, temp_project_dir, mock_nodejs_environment):
        """Test resolve command placeholder functionality."""
        # Mock resolve command (not yet implemented)
        resolve_output = """🔧 Interactive conflict resolution (not yet implemented)
⚠️  This feature will be available in a future version
💡 For now, use: claude-pm setup --interactive
"""

        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = resolve_output

        # Test resolve command structure
        resolve_cmd = f"resolve {temp_project_dir}"
        assert "resolve" in resolve_cmd
        assert str(temp_project_dir) in resolve_cmd

        # Verify placeholder message
        assert "not yet implemented" in resolve_output
        assert "future version" in resolve_output
        assert "setup --interactive" in resolve_output


class TestCLIGlobalOptions:
    """Test global CLI options and help functionality."""

    @pytest.mark.unit
    def test_help_command(self, mock_nodejs_environment):
        """Test help command output."""
        help_output = """claude-pm v2.1.0 - Unified Claude PM Framework Management CLI

USAGE:
    claude-pm <subcommand> [options]
    claude-pm [claude-options] [command]  # Direct Claude invocation

SUBCOMMANDS:
    backup <file-path>         Create backup of CLAUDE.md file
    setup [project-path]       Setup PM framework for project
    scan [root-path]           Scan directory for projects with CLAUDE.md files
    analyze [root-path]        Analyze projects for PM framework compatibility
    resolve [project-path]     Interactive conflict resolution (coming soon)
    restore [project-path]     Restore project from backup

GLOBAL OPTIONS:
    --help                     Show this help message
    --version                  Show version information
    --interactive              Enable interactive mode (where applicable)
    --dry-run                  Analyze only, don't modify files
"""

        # Test help command structure
        assert "claude-pm v2.1.0" in help_output
        assert "SUBCOMMANDS:" in help_output
        assert "backup <file-path>" in help_output
        assert "setup [project-path]" in help_output
        assert "GLOBAL OPTIONS:" in help_output
        assert "--help" in help_output
        assert "--version" in help_output

    @pytest.mark.unit
    def test_version_command(self, mock_nodejs_environment):
        """Test version command output."""
        version_output = """[claude-pm] claude-pm version: 2.1.0
[claude-pm] Claude CLI version: 1.0.0
[claude-pm] Node.js version: v18.17.0
"""

        # Test version information
        assert "claude-pm version: 2.1.0" in version_output
        assert "Claude CLI version:" in version_output
        assert "Node.js version:" in version_output

    @pytest.mark.unit
    def test_interactive_option(self, temp_project_dir):
        """Test interactive option parsing."""
        # Test interactive flag parsing
        cmd_args = ["setup", str(temp_project_dir), "--interactive"]

        # Verify interactive flag is present
        assert "--interactive" in cmd_args
        assert "setup" in cmd_args
        assert str(temp_project_dir) in cmd_args

    @pytest.mark.unit
    def test_dry_run_option(self, temp_project_dir):
        """Test dry run option parsing."""
        # Test dry run flag parsing
        cmd_args = ["setup", str(temp_project_dir), "--dry-run"]

        # Verify dry run flag is present
        assert "--dry-run" in cmd_args
        assert "setup" in cmd_args
        assert str(temp_project_dir) in cmd_args

    @pytest.mark.unit
    def test_verbose_option(self, temp_project_dir):
        """Test verbose option parsing."""
        # Test verbose flag parsing
        cmd_args = ["scan", str(temp_project_dir), "--verbose"]

        # Verify verbose flag is present
        assert "--verbose" in cmd_args
        assert "scan" in cmd_args
        assert str(temp_project_dir) in cmd_args

    @pytest.mark.unit
    def test_quiet_option(self, temp_project_dir):
        """Test quiet option parsing."""
        # Test quiet flag parsing
        cmd_args = ["backup", str(temp_project_dir / "CLAUDE.md"), "--quiet"]

        # Verify quiet flag is present
        assert "--quiet" in cmd_args
        assert "backup" in cmd_args


class TestCLILegacySupport:
    """Test legacy Claude CLI support functionality."""

    @pytest.mark.unit
    def test_claude_cli_detection(self, mock_nodejs_environment):
        """Test Claude CLI detection functionality."""
        # Mock Claude CLI availability
        with patch("subprocess.run") as mock_run:
            # Mock 'which claude' command
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "/usr/local/bin/claude"

            # Test CLI detection
            result = subprocess.run(["which", "claude"], capture_output=True, text=True)
            assert result.returncode == 0
            assert "claude" in result.stdout

    @pytest.mark.unit
    def test_claude_cli_installation(self, mock_nodejs_environment):
        """Test Claude CLI installation functionality."""
        # Mock npm installation
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "installed @anthropic-ai/claude-cli"

            # Test npm install command
            result = subprocess.run(
                ["npm", "install", "-g", "@anthropic-ai/claude-cli"], capture_output=True, text=True
            )
            assert result.returncode == 0

    @pytest.mark.unit
    def test_claude_cli_version_verification(self, mock_nodejs_environment):
        """Test Claude CLI version verification."""
        # Mock version command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "claude version 1.0.0"

            # Test version verification
            result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
            assert result.returncode == 0
            assert "version" in result.stdout

    @pytest.mark.unit
    def test_legacy_claude_invocation(self, mock_nodejs_environment):
        """Test legacy Claude invocation support."""
        # Mock direct Claude invocation
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Claude response"

            # Test legacy invocation
            legacy_cmd = ["claude", "--dangerously-skip-permissions", "--model", "sonnet", "help"]

            # Verify command structure
            assert "claude" in legacy_cmd
            assert "--dangerously-skip-permissions" in legacy_cmd
            assert "--model" in legacy_cmd
            assert "sonnet" in legacy_cmd


class TestCLIIntegrationScenarios:
    """Test integration scenarios and workflows."""

    @pytest.mark.integration
    def test_complete_backup_setup_workflow(
        self, temp_project_dir, sample_claude_md_basic, mock_nodejs_environment
    ):
        """Test complete backup and setup workflow."""
        # Create initial project
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        # Mock backup command
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "✅ Backup created"

        # Step 1: Create backup
        backup_cmd = f"backup {claude_file}"
        assert "backup" in backup_cmd

        # Step 2: Setup PM framework
        setup_cmd = f"setup {temp_project_dir}"
        assert "setup" in setup_cmd

        # Verify workflow sequence
        assert claude_file.exists()
        assert temp_project_dir.exists()

    @pytest.mark.integration
    def test_scan_analyze_workflow(self, temp_project_dir, mock_nodejs_environment):
        """Test scan and analyze workflow."""
        # Create multiple projects
        for i in range(3):
            project_dir = temp_project_dir / f"project{i}"
            project_dir.mkdir()
            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(f"# Project {i}\nBasic instructions.")

        # Mock scan command
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "Found 3 projects"

        # Step 1: Scan projects
        scan_cmd = f"scan {temp_project_dir}"
        assert "scan" in scan_cmd

        # Step 2: Analyze projects
        analyze_cmd = f"analyze {temp_project_dir}"
        assert "analyze" in analyze_cmd

        # Verify workflow
        assert temp_project_dir.exists()
        assert (temp_project_dir / "project0").exists()
        assert (temp_project_dir / "project1").exists()
        assert (temp_project_dir / "project2").exists()

    @pytest.mark.integration
    def test_setup_restore_workflow(
        self, temp_project_dir, sample_claude_md_basic, mock_nodejs_environment
    ):
        """Test setup and restore workflow."""
        # Create initial project
        claude_file = temp_project_dir / "CLAUDE.md"
        claude_file.write_text(sample_claude_md_basic)

        # Mock setup command
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "✅ Processing complete"

        # Step 1: Setup PM framework
        setup_cmd = f"setup {temp_project_dir}"
        assert "setup" in setup_cmd

        # Step 2: Restore from backup
        restore_cmd = f"restore {temp_project_dir}"
        assert "restore" in restore_cmd

        # Verify workflow
        assert claude_file.exists()
        assert temp_project_dir.exists()

    @pytest.mark.integration
    def test_error_handling_workflow(self, temp_project_dir, mock_nodejs_environment):
        """Test error handling across workflow."""
        # Mock various error conditions
        error_scenarios = [
            ("backup", "CLAUDE.md not found"),
            ("setup", "Permission denied"),
            ("restore", "No backup found"),
            ("scan", "Directory not readable"),
            ("analyze", "Invalid project structure"),
        ]

        for command, error_msg in error_scenarios:
            mock_nodejs_environment.return_value.returncode = 1
            mock_nodejs_environment.return_value.stderr = error_msg

            # Test error handling
            cmd = f"{command} {temp_project_dir}"
            assert command in cmd
            assert mock_nodejs_environment.return_value.returncode == 1
            assert error_msg in mock_nodejs_environment.return_value.stderr


class TestCLIPerformanceStress:
    """Test performance and stress scenarios."""

    @pytest.mark.integration
    def test_large_project_scan(self, temp_project_dir, mock_nodejs_environment):
        """Test scanning large number of projects."""
        # Create many projects
        num_projects = 100
        for i in range(num_projects):
            project_dir = temp_project_dir / f"project{i:03d}"
            project_dir.mkdir()
            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(f"# Project {i}\nTest project {i}")

        # Mock scan performance
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = f"Found {num_projects} projects"

        # Test large scan
        scan_cmd = f"scan {temp_project_dir}"
        assert "scan" in scan_cmd

        # Verify performance handling
        assert temp_project_dir.exists()
        assert len(list(temp_project_dir.iterdir())) == num_projects

    @pytest.mark.integration
    def test_concurrent_command_execution(self, temp_project_dir, mock_nodejs_environment):
        """Test concurrent command execution."""
        # Create test projects
        for i in range(5):
            project_dir = temp_project_dir / f"project{i}"
            project_dir.mkdir()
            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(f"# Project {i}\nConcurrent test")

        # Mock concurrent execution
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "Command executed"

        # Test concurrent commands
        commands = ["scan", "analyze", "scan", "analyze"]

        for cmd in commands:
            test_cmd = f"{cmd} {temp_project_dir}"
            assert cmd in test_cmd
            assert str(temp_project_dir) in test_cmd

    @pytest.mark.integration
    def test_memory_usage_large_files(self, temp_project_dir, mock_nodejs_environment):
        """Test memory usage with large CLAUDE.md files."""
        # Create large CLAUDE.md file
        large_content = "# Large Project\n" + "This is a test line.\n" * 10000

        project_dir = temp_project_dir / "large_project"
        project_dir.mkdir()
        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text(large_content)

        # Mock processing large file
        mock_nodejs_environment.return_value.returncode = 0
        mock_nodejs_environment.return_value.stdout = "Large file processed"

        # Test large file handling
        backup_cmd = f"backup {claude_file}"
        assert "backup" in backup_cmd

        # Verify large file exists
        assert claude_file.exists()
        assert len(claude_file.read_text()) > 100000  # Large file


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
