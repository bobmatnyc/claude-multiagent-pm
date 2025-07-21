#!/usr/bin/env python3
"""
Unit tests for Parent Directory Manager Service (CMPM-104).

Tests cover:
- Parent directory registration and management
- Template installation and updates
- Backup and restore operations
- Deployment awareness integration
- Integration with CMPM-101, CMPM-102, and CMPM-103
"""

import asyncio
import json
import tempfile
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the service to test
from claude_pm.services.parent_directory_manager import ParentDirectoryManager

# Import models and enums from the correct locations
from claude_pm.services.parent_directory_manager.operations import ParentDirectoryContext
from claude_pm.services.parent_directory_manager.state_manager import (
    ParentDirectoryStatus,
    ParentDirectoryOperation,
    ParentDirectoryAction
)
from claude_pm.services.parent_directory_manager.config_manager import ParentDirectoryConfig


class TestParentDirectoryManager:
    """Test suite for ParentDirectoryManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_template_manager(self):
        """Create mock template manager - no longer used."""
        return None

    @pytest.fixture
    def mock_dependency_manager(self):
        """Create mock dependency manager - no longer used."""
        return None

    @pytest_asyncio.fixture
    async def parent_directory_manager(self, temp_dir):
        """Create ParentDirectoryManager instance for testing."""
        # Create test directories
        working_dir = temp_dir / "working"
        working_dir.mkdir()

        # Initialize manager with quiet mode to reduce test output
        manager = ParentDirectoryManager(
            {"backup_retention_days": 7, "auto_backup_enabled": True, "deployment_aware": True},
            quiet_mode=True
        )

        # Override working directory
        manager.working_dir = working_dir
        manager.framework_path = working_dir
        manager.parent_directory_manager_dir = (
            working_dir / ".claude-pm" / "parent_directory_manager"
        )
        
        # Manually initialize paths to ensure correct structure
        manager.backups_dir = working_dir / ".claude-pm" / "backups" / "parent_directory_manager"
        manager.configs_dir = manager.parent_directory_manager_dir / "configs"
        manager.versions_dir = manager.parent_directory_manager_dir / "versions"
        manager.logs_dir = manager.parent_directory_manager_dir / "logs"
        manager.framework_backups_dir = working_dir / ".claude-pm" / "backups" / "framework"
        
        manager.managed_directories_file = manager.configs_dir / "managed_directories.json"
        manager.operation_history_file = manager.logs_dir / "operation_history.json"
        
        # Create necessary directories manually since we're overriding paths
        for dir_path in [manager.configs_dir, manager.versions_dir, manager.logs_dir, manager.backups_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create initial files
        manager.managed_directories_file.write_text("{}")
        manager.operation_history_file.write_text("[]")

        # Initialize
        await manager._initialize()

        yield manager

        # Cleanup
        try:
            await manager._cleanup()
        except:
            pass

    @pytest.mark.asyncio
    async def test_initialization(self, parent_directory_manager):
        """Test ParentDirectoryManager initialization."""
        manager = parent_directory_manager

        # Verify directories were created
        assert manager.configs_dir.exists()
        assert manager.versions_dir.exists()
        assert manager.logs_dir.exists()
        assert manager.backups_dir.exists()

        # Verify initial files
        assert manager.managed_directories_file.exists()
        assert manager.operation_history_file.exists()

    @pytest.mark.asyncio
    async def test_register_parent_directory(self, parent_directory_manager, temp_dir):
        """Test parent directory registration."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "parent_project"
        parent_dir.mkdir()

        # Register parent directory
        result = await manager.register_parent_directory(
            parent_directory=parent_dir,
            context=ParentDirectoryContext.PROJECT_COLLECTION,
            metadata={"project_type": "microservices"}
        )

        assert result["success"] is True
        assert result["directory"] == str(parent_dir)

        # Verify registration was saved
        managed_dirs = manager._load_managed_directories()
        assert str(parent_dir) in managed_dirs

    @pytest.mark.asyncio
    async def test_install_parent_template(self, parent_directory_manager, temp_dir):
        """Test parent template installation."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "parent_with_template"
        parent_dir.mkdir()

        # Register and install template
        result = await manager.install_parent_template(
            parent_directory=parent_dir,
            template_variables={
                "project_type": "monorepo",
                "organization": "test_org"
            }
        )

        assert result["success"] is True
        assert result["template_path"] == str(parent_dir / "CLAUDE.md")

        # Verify template was created
        template_path = parent_dir / "CLAUDE.md"
        assert template_path.exists()

    @pytest.mark.asyncio
    async def test_detect_existing_templates(self, parent_directory_manager, temp_dir):
        """Test detection of existing templates."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "parent_with_existing"
        parent_dir.mkdir()

        # Create existing template
        existing_template = parent_dir / "CLAUDE.md"
        existing_template.write_text("# Existing Template")

        # Detect existing template
        existing = await manager.detect_existing_template(parent_dir)
        assert existing is not None
        assert existing["path"] == str(existing_template)
        assert existing["content"] == "# Existing Template"

    @pytest.mark.asyncio
    async def test_backup_existing_template(self, parent_directory_manager, temp_dir):
        """Test backup of existing templates."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "parent_with_backup"
        parent_dir.mkdir()

        # Create template to backup
        template_path = parent_dir / "CLAUDE.md"
        template_content = "# Original Template"
        template_path.write_text(template_content)

        # Register directory first
        await manager.register_parent_directory(parent_dir, ParentDirectoryContext.PROJECT_COLLECTION)

        # Backup template
        backup_path = await manager.backup_existing_template(template_path)
        assert backup_path is not None
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == template_content

    @pytest.mark.asyncio
    async def test_update_template_with_backup(self, parent_directory_manager, temp_dir):
        """Test template update with automatic backup."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "parent_update"
        parent_dir.mkdir()

        # Create initial template
        template_path = parent_dir / "CLAUDE.md"
        original_content = "# Original Content"
        template_path.write_text(original_content)

        # Register directory
        await manager.register_parent_directory(parent_dir, ParentDirectoryContext.PROJECT_COLLECTION)

        # Update template
        result = await manager.update_parent_template(
            parent_directory=parent_dir,
            template_variables={"version": "2.0"},
            force=False
        )

        assert result["success"] is True
        assert result["backup_created"] is True

        # Verify backup was created
        backups = list(manager.backups_dir.glob("**/CLAUDE.md.backup.*"))
        assert len(backups) > 0

    @pytest.mark.asyncio
    async def test_list_managed_directories(self, parent_directory_manager, temp_dir):
        """Test listing managed directories."""
        manager = parent_directory_manager

        # Register multiple directories
        dirs = []
        for i in range(3):
            parent_dir = temp_dir / f"parent_{i}"
            parent_dir.mkdir()
            dirs.append(parent_dir)
            await manager.register_parent_directory(
                parent_dir,
                ParentDirectoryContext.PROJECT_COLLECTION,
                metadata={"index": i}
            )

        # List managed directories
        managed = await manager.list_managed_directories()
        assert len(managed) >= 3

        # Verify all registered directories are listed
        managed_paths = [item["directory"] for item in managed]
        for dir_path in dirs:
            assert str(dir_path) in managed_paths

    @pytest.mark.asyncio
    async def test_deployment_awareness(self, parent_directory_manager, temp_dir):
        """Test deployment awareness integration."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "deployed_parent"
        parent_dir.mkdir()

        # Create deployment marker
        (parent_dir / ".claude-pm").mkdir()
        (parent_dir / ".claude-pm" / "deployment.json").write_text(
            json.dumps({"deployed": True, "version": "1.0.0"})
        )

        # Register with deployment awareness
        result = await manager.register_parent_directory(
            parent_dir,
            ParentDirectoryContext.DEPLOYMENT_ROOT
        )

        assert result["success"] is True
        assert result.get("deployment_info") is not None

    @pytest.mark.asyncio
    async def test_health_check(self, parent_directory_manager):
        """Test health check functionality."""
        manager = parent_directory_manager

        # Perform health check
        health = await manager._health_check()

        assert isinstance(health, dict)
        assert "directories_exist" in health
        assert "managed_directories_file" in health
        assert "backup_system" in health

    @pytest.mark.asyncio
    async def test_operation_history(self, parent_directory_manager, temp_dir):
        """Test operation history tracking."""
        manager = parent_directory_manager
        parent_dir = temp_dir / "history_test"
        parent_dir.mkdir()

        # Perform operations
        await manager.register_parent_directory(parent_dir, ParentDirectoryContext.PROJECT_COLLECTION)
        await manager.install_parent_template(parent_dir)

        # Verify operation history
        history = manager._load_operation_history()
        assert len(history) >= 2

        # Check operations are recorded
        operation_types = [op.get("operation") for op in history]
        assert any("register" in op for op in operation_types)
        assert any("install" in op for op in operation_types)

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, parent_directory_manager, temp_dir):
        """Test cleanup of old backups."""
        manager = parent_directory_manager
        
        # Create old backup files
        old_backup = manager.backups_dir / "old_backup.tar.gz"
        old_backup.parent.mkdir(parents=True, exist_ok=True)
        old_backup.write_text("old data")
        
        # Modify time to be older than retention period
        import time
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        os.utime(old_backup, (old_time, old_time))
        
        # Run cleanup
        await manager._cleanup_old_backups()
        
        # Verify old backup was removed
        assert not old_backup.exists()

    @pytest.mark.asyncio
    async def test_framework_protection(self, parent_directory_manager, temp_dir):
        """Test framework CLAUDE.md protection."""
        manager = parent_directory_manager
        
        # Create framework CLAUDE.md
        framework_claude = temp_dir / "working" / "framework" / "CLAUDE.md"
        framework_claude.parent.mkdir(parents=True, exist_ok=True)
        framework_claude.write_text("# Framework Template - DO NOT MODIFY")
        
        # Verify protection
        is_protected = await manager._is_framework_template(framework_claude)
        assert is_protected is True

    @pytest.mark.asyncio
    async def test_error_handling(self, parent_directory_manager):
        """Test error handling for invalid operations."""
        manager = parent_directory_manager
        
        # Test with non-existent directory
        result = await manager.register_parent_directory(
            Path("/non/existent/directory"),
            ParentDirectoryContext.CUSTOM
        )
        
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])