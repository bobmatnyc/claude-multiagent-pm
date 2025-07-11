#!/usr/bin/env python3
"""
Test Fixtures for claude-pm CLI Testing
======================================

Comprehensive test fixtures for CLI testing including:
- Project structures and content variations
- Mock environments and services
- Test data generators
- Common assertion helpers
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock

import pytest


class CLITestFixtures:
    """Central collection of CLI test fixtures."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory(prefix="claude_pm_cli_test_") as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def cli_path(self):
        """Path to claude-pm CLI executable."""
        return Path("/Users/masa/.local/bin/claude-pm")
    
    @pytest.fixture
    def mock_subprocess_success(self):
        """Mock successful subprocess execution."""
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "Success"
        mock.stderr = ""
        return mock
    
    @pytest.fixture
    def mock_subprocess_failure(self):
        """Mock failed subprocess execution."""
        mock = MagicMock()
        mock.returncode = 1
        mock.stdout = ""
        mock.stderr = "Error occurred"
        return mock
    
    @pytest.fixture
    def mock_nodejs_available(self):
        """Mock Node.js availability."""
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "v18.17.0"
        mock.stderr = ""
        return mock
    
    @pytest.fixture
    def mock_nodejs_unavailable(self):
        """Mock Node.js unavailability."""
        mock = MagicMock()
        mock.side_effect = FileNotFoundError("node: command not found")
        return mock


class ProjectFixtures:
    """Test fixtures for different project structures."""
    
    @pytest.fixture
    def basic_claude_md(self):
        """Basic CLAUDE.md content."""
        return """# Basic Project Instructions

You are a helpful AI assistant for this project.

## Project Overview
This is a basic project without any special framework requirements.

## Guidelines
- Follow project conventions
- Be helpful and accurate
- Maintain consistency with existing code
- Provide clear explanations

## Tasks
1. Help with development tasks
2. Review code changes
3. Provide suggestions and improvements
4. Answer questions about the project
"""
    
    @pytest.fixture
    def pm_framework_claude_md(self):
        """CLAUDE.md with PM Framework content."""
        return """# Claude PM Framework v2.1.0

## 🤖 AI ASSISTANT ROLE DESIGNATION

**You are a Claude PM Framework Orchestrator - Multi-Agent Coordinator**

Your primary and EXCLUSIVE role is orchestrating the Claude PM Framework project management system.

### Core PM Framework Responsibilities
1. **Framework Orchestration**: Coordinate multi-agent workflows and task delegation
2. **Agent Collaboration**: Work hand-in-hand with core agent types (Documentation, Ticketing)
3. **Project Management**: Oversee project lifecycle, priorities, and deliverables
4. **Strategic Planning**: Plan and execute framework enhancements

## 🚨 MANDATORY: CORE AGENT TYPES

### Core Agent Types (Mandatory Collaboration)
1. **Documentation Agent** - **CORE AGENT TYPE**
   - **Role**: Project documentation pattern analysis
   - **Authority**: Documentation Agent has authority over all documentation decisions

2. **Ticketing Agent** - **CORE AGENT TYPE**
   - **Role**: Universal ticketing interface and lifecycle management
   - **Authority**: Ticketing Agent has authority over all ticket lifecycle decisions

## 🚫 CRITICAL DELEGATION CONSTRAINTS

**PM FRAMEWORK DELEGATION REQUIREMENTS**

### Mandatory Delegation (PM Framework)
- **Documentation Operations**: MUST delegate to Documentation Agent
- **Ticket Operations**: MUST delegate to Ticketing Agent
- **Code Operations**: MUST delegate to appropriate Engineer/Developer agents

### Framework-Allowed PM Activities
- Read project management files (CLAUDE.md, status reports)
- Create PM artifacts (status reports, task assignments)
- Coordinate and delegate work between agents

## 🎯 SYSTEMATIC AGENT DELEGATION

**Enhanced PM Framework Delegation Patterns**

### Framework Agent Delegation
- **"document"** → Documentation Agent (pattern analysis, health monitoring)
- **"ticket"** → Ticketing Agent (all ticket operations)
- **"status"** → Ticketing Agent (sprint status, ticket summaries)
- **"init"** → System Init Agent (framework initialization)
- **"test"** → QA Agent (testing coordination)
"""
    
    @pytest.fixture
    def conflicted_claude_md(self):
        """CLAUDE.md with potential conflicts."""
        return """# Specialized Project Assistant

You are a specialized code assistant with specific constraints.

## Role Definition
You are EXCLUSIVELY a code assistant. You MUST focus only on code-related tasks.

## Strict Constraints
FORBIDDEN ACTIVITIES:
- Writing documentation files
- Creating README files
- Modifying configuration files
- Creating new projects
- Managing tickets or issues
- Coordinating with other agents

## You MUST NOT:
- Delegate tasks to other agents
- Create project management artifacts
- Modify system settings
- Install frameworks

## You MUST:
- Only write and edit code files
- Focus on implementation details
- Follow existing code patterns
- Maintain backward compatibility

## Code Guidelines
1. Use consistent styling
2. Add appropriate comments
3. Follow language conventions
4. Test thoroughly
"""
    
    @pytest.fixture
    def large_claude_md(self):
        """Large CLAUDE.md file for performance testing."""
        content = """# Large Project Instructions

You are a comprehensive AI assistant for this complex project.

## Project Overview
This is a large, complex project with extensive requirements and documentation.

"""
        
        # Add large sections
        for i in range(100):
            content += f"""
## Section {i + 1}: Feature Area {i + 1}

### Overview
This section covers feature area {i + 1} with detailed requirements and guidelines.

### Requirements
- Requirement {i + 1}.1: Handle specific functionality
- Requirement {i + 1}.2: Maintain consistency
- Requirement {i + 1}.3: Provide error handling
- Requirement {i + 1}.4: Implement logging
- Requirement {i + 1}.5: Add unit tests

### Implementation Guidelines
1. Follow established patterns
2. Use appropriate abstractions
3. Implement proper error handling
4. Add comprehensive logging
5. Write thorough tests
6. Document all public APIs
7. Maintain backward compatibility
8. Consider performance implications
9. Handle edge cases
10. Provide clear error messages

### Code Examples
```python
# Example implementation for feature {i + 1}
def feature_{i + 1}_handler(input_data):
    '''Handle feature {i + 1} functionality.'''
    try:
        # Process input
        processed_data = process_input(input_data)
        
        # Validate data
        if not validate_data(processed_data):
            raise ValueError("Invalid data format")
        
        # Execute feature logic
        result = execute_feature_{i + 1}(processed_data)
        
        # Log success
        logger.info(f"Feature {i + 1} completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Feature {i + 1} failed: {{e}}")
        raise
```

### Testing Guidelines
- Write unit tests for all functions
- Include integration tests
- Test error conditions
- Verify performance requirements
- Add regression tests
"""
        
        return content
    
    @pytest.fixture
    def multi_project_structure(self, temp_workspace):
        """Create multi-project structure for testing."""
        projects = {
            "basic_project": {
                "type": "basic",
                "claude_md": """# Basic Project
You are a helpful assistant for this basic project."""
            },
            "pm_project": {
                "type": "pm_framework",
                "claude_md": """# PM Framework Project
You are a Claude PM Framework Orchestrator."""
            },
            "conflicted_project": {
                "type": "conflicted",
                "claude_md": """# Conflicted Project
You MUST NOT delegate tasks.
FORBIDDEN: Creating documentation."""
            },
            "nodejs_project": {
                "type": "nodejs",
                "claude_md": """# Node.js Project
You are a Node.js development assistant.""",
                "package_json": {
                    "name": "test-nodejs-project",
                    "version": "1.0.0",
                    "scripts": {
                        "test": "jest",
                        "start": "node index.js"
                    }
                }
            },
            "python_project": {
                "type": "python",
                "claude_md": """# Python Project
You are a Python development assistant.""",
                "pyproject_toml": """[tool.poetry]
name = "test-python-project"
version = "0.1.0"
description = "Test Python project"

[tool.poetry.dependencies]
python = "^3.9"
"""
            }
        }
        
        # Create project directories and files
        for project_name, config in projects.items():
            project_dir = temp_workspace / project_name
            project_dir.mkdir()
            
            # Create CLAUDE.md
            claude_file = project_dir / "CLAUDE.md"
            claude_file.write_text(config["claude_md"])
            
            # Create package.json if specified
            if "package_json" in config:
                package_file = project_dir / "package.json"
                package_file.write_text(json.dumps(config["package_json"], indent=2))
            
            # Create pyproject.toml if specified
            if "pyproject_toml" in config:
                pyproject_file = project_dir / "pyproject.toml"
                pyproject_file.write_text(config["pyproject_toml"])
            
            # Create .git directory to mark as git repo
            git_dir = project_dir / ".git"
            git_dir.mkdir()
        
        return temp_workspace, projects


class BackupFixtures:
    """Test fixtures for backup functionality."""
    
    @pytest.fixture
    def backup_index_data(self):
        """Sample backup index data."""
        return [
            {
                "fileName": "CLAUDE.md.2025-07-11T10-00-00.abc123.bak",
                "timestamp": "2025-07-11T10:00:00.000Z",
                "hash": "abc123",
                "originalPath": "/test/project/CLAUDE.md"
            },
            {
                "fileName": "CLAUDE.md.2025-07-11T09-00-00.def456.bak",
                "timestamp": "2025-07-11T09:00:00.000Z",
                "hash": "def456",
                "originalPath": "/test/project/CLAUDE.md"
            }
        ]
    
    @pytest.fixture
    def backup_file_content(self):
        """Sample backup file content."""
        return """# CLAUDE.md Backup
# Created: 2025-07-11T10:00:00.000Z
# Original: /test/project/CLAUDE.md
# Hash: abc123
# Backup System Version: 1.0.0
# =============================================

# Original Project Instructions

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
    
    @pytest.fixture
    def project_with_backup(self, temp_workspace, backup_index_data, backup_file_content):
        """Create project with backup structure."""
        project_dir = temp_workspace / "backup_test_project"
        project_dir.mkdir()
        
        # Create current CLAUDE.md
        claude_file = project_dir / "CLAUDE.md"
        claude_file.write_text("""# Modified Project
This file has been modified by PM framework.

## PM Framework Content
You are a Claude PM Framework Orchestrator.
""")
        
        # Create backup directory
        backup_dir = project_dir / ".claude-backups"
        backup_dir.mkdir()
        
        # Create backup files
        for backup_info in backup_index_data:
            backup_file = backup_dir / backup_info["fileName"]
            backup_file.write_text(backup_file_content)
        
        # Create backup index
        index_file = backup_dir / "backup-index.json"
        index_file.write_text(json.dumps(backup_index_data, indent=2))
        
        return project_dir


class MockEnvironmentFixtures:
    """Test fixtures for mocking external dependencies."""
    
    @pytest.fixture
    def mock_nodejs_environment(self):
        """Mock complete Node.js environment."""
        return {
            "node_version": "v18.17.0",
            "npm_version": "9.8.1",
            "available": True,
            "commands": {
                "node --version": "v18.17.0",
                "npm --version": "9.8.1",
                "node backup.js": "Backup system ready"
            }
        }
    
    @pytest.fixture
    def mock_cli_responses(self):
        """Mock CLI command responses."""
        return {
            "help": """claude-pm v2.1.0 - Unified Claude PM Framework Management CLI

USAGE:
    claude-pm <subcommand> [options]

SUBCOMMANDS:
    backup <file-path>         Create backup of CLAUDE.md file
    setup [project-path]       Setup PM framework for project
    scan [root-path]           Scan directory for projects
    analyze [root-path]        Analyze projects for compatibility
    restore [project-path]     Restore project from backup
""",
            "version": """[claude-pm] claude-pm version: 2.1.0
[claude-pm] Claude CLI version: 1.0.0
[claude-pm] Node.js version: v18.17.0
""",
            "backup_success": "✅ Backup created: /path/to/backup.bak",
            "backup_error": "❌ Error: CLAUDE.md not found at: /path/to/file",
            "setup_success": "✅ PM framework installed at: /path/to/CLAUDE.md",
            "setup_processing": "✅ Processing complete\n📊 Conflicts: 0\n📁 Backup: /path/to/backup.bak",
            "scan_results": """🔍 Scanning projects in: /test/workspace

📁 Found 3 projects with CLAUDE.md files:
  - basic_project (/test/workspace/basic_project)
  - pm_project (/test/workspace/pm_project)
  - conflicted_project (/test/workspace/conflicted_project)
""",
            "analyze_results": """🔍 Analyzing projects in: /test/workspace

📊 basic_project:
   Compatible: ✅ Yes
   Risks: 0
   Features: 0

📊 pm_project:
   Compatible: ❌ No
   Risks: 1
   Features: 1
   Risk Details:
     - PM Framework already installed

📊 conflicted_project:
   Compatible: ✅ Yes
   Risks: 1
   Features: 1
   Risk Details:
     - Potential delegation conflicts
""",
            "restore_success": "✅ Rollback successful for /test/project\n📁 Restored from: /test/project/.claude-backups/backup.bak",
            "restore_error": "❌ Rollback failed: No backup directory found"
        }
    
    @pytest.fixture
    def mock_backup_system_js(self):
        """Mock backup system JavaScript code."""
        return """
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class ClaudeBackupSystem {
    constructor() {
        this.version = '1.0.0';
        this.backupDir = '.claude-backups';
    }

    async createBackup(filePath) {
        // Mock backup creation
        return '/mock/backup/path.bak';
    }

    async processFile(filePath, pmFrameworkPath, options = {}) {
        // Mock file processing
        return {
            success: true,
            backupPath: '/mock/backup/path.bak',
            conflicts: [],
            error: null
        };
    }

    async rollbackProject(projectPath) {
        // Mock rollback
        return {
            success: true,
            error: null,
            restoredFrom: '/mock/backup/path.bak'
        };
    }

    scanProjects(rootPath) {
        // Mock project scanning
        return [
            { name: 'project1', path: '/mock/project1', claudeFile: '/mock/project1/CLAUDE.md' },
            { name: 'project2', path: '/mock/project2', claudeFile: '/mock/project2/CLAUDE.md' }
        ];
    }

    analyzeProject(project) {
        // Mock project analysis
        return {
            project: project.name,
            path: project.path,
            compatible: true,
            risks: [],
            recommendations: [],
            existingFeatures: []
        };
    }
}

module.exports = ClaudeBackupSystem;
"""


class AssertionHelpers:
    """Helper methods for common assertions."""
    
    @staticmethod
    def assert_claude_md_structure(content: str, expected_type: str = "basic"):
        """Assert CLAUDE.md has expected structure."""
        assert isinstance(content, str)
        assert len(content.strip()) > 0
        
        if expected_type == "pm_framework":
            assert "Claude PM Framework" in content
            assert "Orchestrator" in content
            assert "DELEGATION CONSTRAINTS" in content
        elif expected_type == "basic":
            assert "helpful" in content.lower() or "assistant" in content.lower()
        elif expected_type == "conflicted":
            assert "FORBIDDEN" in content or "MUST NOT" in content
    
    @staticmethod
    def assert_backup_structure(backup_dir: Path):
        """Assert backup directory has expected structure."""
        assert backup_dir.exists()
        assert backup_dir.is_dir()
        
        # Check for backup index
        index_file = backup_dir / "backup-index.json"
        if index_file.exists():
            # Validate index structure
            index_data = json.loads(index_file.read_text())
            assert isinstance(index_data, list)
            
            for entry in index_data:
                assert "fileName" in entry
                assert "timestamp" in entry
                assert "hash" in entry
                assert "originalPath" in entry
    
    @staticmethod
    def assert_cli_output_structure(output: str, command: str):
        """Assert CLI output has expected structure."""
        assert isinstance(output, str)
        
        if command == "help":
            assert "claude-pm" in output
            assert "SUBCOMMANDS:" in output
        elif command == "version":
            assert "version" in output.lower()
        elif command == "scan":
            assert "Found" in output or "Scanning" in output
        elif command == "analyze":
            assert "Analyzing" in output or "Compatible:" in output
        elif command == "backup":
            assert "Backup" in output or "✅" in output or "❌" in output
        elif command == "setup":
            assert "PM framework" in output or "✅" in output or "❌" in output
        elif command == "restore":
            assert "Rollback" in output or "✅" in output or "❌" in output


# Export all fixture classes for easy import
__all__ = [
    'CLITestFixtures',
    'ProjectFixtures', 
    'BackupFixtures',
    'MockEnvironmentFixtures',
    'AssertionHelpers'
]