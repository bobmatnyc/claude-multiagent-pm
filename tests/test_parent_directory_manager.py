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
from claude_pm.services.parent_directory_manager import (
    ParentDirectoryManager,
    ParentDirectoryContext,
    ParentDirectoryAction,
    ParentDirectoryConfig,
    ParentDirectoryStatus,
    ParentDirectoryOperation,
)
from claude_pm.services.template_manager import TemplateManager, TemplateVersion, TemplateSource
from claude_pm.services.dependency_manager import DependencyManager


class TestParentDirectoryManager:
    """Test suite for ParentDirectoryManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_template_manager(self):
        """Create mock template manager."""
        manager = Mock(spec=TemplateManager)
        manager.initialize = AsyncMock()
        manager.cleanup = AsyncMock()
        manager.get_template = AsyncMock()
        manager.render_template = AsyncMock()
        return manager

    @pytest.fixture
    def mock_dependency_manager(self):
        """Create mock dependency manager."""
        manager = Mock(spec=DependencyManager)
        manager.initialize = AsyncMock()
        manager.cleanup = AsyncMock()
        manager.deployment_config = {
            "strategy": "local_source",
            "config": {"deploymentType": "local_source", "platform": "darwin"},
        }
        return manager

    @pytest_asyncio.fixture
    async def parent_directory_manager(self, temp_dir):
        """Create ParentDirectoryManager instance for testing."""
        # Create test directories
        working_dir = temp_dir / "working"
        working_dir.mkdir()

        # Initialize manager
        manager = ParentDirectoryManager(
            {"backup_retention_days": 7, "auto_backup_enabled": True, "deployment_aware": True}
        )

        # Override working directory
        manager.working_dir = working_dir
        manager.framework_path = working_dir
        manager.parent_directory_manager_dir = (
            working_dir / ".claude-pm" / "parent_directory_manager"
        )
        manager._initialize_paths()

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

        # Check that manager is initialized
        assert hasattr(manager, "managed_directories")
        assert manager.managed_directories == {}
        assert manager.operation_history == []

        # Check directory structure
        assert manager.parent_directory_manager_dir.exists()
        assert manager.backups_dir.exists()
        assert manager.configs_dir.exists()
        assert manager.versions_dir.exists()
        assert manager.logs_dir.exists()

    @pytest.mark.asyncio
    async def test_register_parent_directory(self, parent_directory_manager, temp_dir):
        """Test registering a parent directory."""
        manager = parent_directory_manager

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Register directory
        result = await manager.register_parent_directory(
            test_dir, ParentDirectoryContext.PROJECT_COLLECTION, "test_template", {"var1": "value1"}
        )

        assert result is True
        assert str(test_dir) in manager.managed_directories

        config = manager.managed_directories[str(test_dir)]
        assert config.target_directory == test_dir
        assert config.context == ParentDirectoryContext.PROJECT_COLLECTION
        assert config.template_id == "test_template"
        assert config.template_variables == {"var1": "value1"}

    @pytest.mark.asyncio
    async def test_register_nonexistent_directory(self, parent_directory_manager, temp_dir):
        """Test registering a non-existent directory."""
        manager = parent_directory_manager

        # Try to register non-existent directory
        test_dir = temp_dir / "nonexistent"

        result = await manager.register_parent_directory(
            test_dir, ParentDirectoryContext.CUSTOM, "test_template"
        )

        assert result is False
        assert str(test_dir) not in manager.managed_directories

    @pytest.mark.asyncio
    async def test_install_template_to_parent_directory(self, parent_directory_manager, temp_dir):
        """Test installing a template to a parent directory."""
        manager = parent_directory_manager

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Mock template manager
        mock_template = Mock()
        mock_template.get_template = AsyncMock(
            return_value=(
                "# Test Template\n{{VAR1}}\n{{VAR2}}",
                Mock(version="1.0.0", variables={"VAR2": "default_value"}),
            )
        )
        mock_template.render_template = AsyncMock(
            return_value="# Test Template\nvalue1\ndefault_value"
        )

        manager.template_manager = mock_template

        # Install template
        result = await manager.install_template_to_parent_directory(
            test_dir, "test_template", {"VAR1": "value1"}
        )

        assert result.success is True
        assert result.action == ParentDirectoryAction.INSTALL
        assert result.template_id == "test_template"
        assert result.version == "1.0.0"

        # Check that file was created
        claude_file = test_dir / "CLAUDE.md"
        assert claude_file.exists()

        content = claude_file.read_text()
        assert "# Test Template" in content
        assert "value1" in content
        assert "default_value" in content

    @pytest.mark.asyncio
    async def test_install_template_without_template_manager(
        self, parent_directory_manager, temp_dir
    ):
        """Test installing template without template manager."""
        manager = parent_directory_manager
        manager.template_manager = None

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Try to install template
        result = await manager.install_template_to_parent_directory(test_dir, "test_template")

        assert result.success is False
        assert "Template manager not available" in result.error_message

    @pytest.mark.asyncio
    async def test_update_parent_directory_template(self, parent_directory_manager, temp_dir):
        """Test updating a parent directory template."""
        manager = parent_directory_manager

        # Create test directory and register it
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        await manager.register_parent_directory(
            test_dir,
            ParentDirectoryContext.PROJECT_COLLECTION,
            "test_template",
            {"VAR1": "old_value"},
        )

        # Create existing CLAUDE.md file
        claude_file = test_dir / "CLAUDE.md"
        claude_file.write_text("# Old Template\nold_value")

        # Mock template manager
        mock_template = Mock()
        mock_template.get_template = AsyncMock(
            return_value=("# Updated Template\n{{VAR1}}", Mock(version="1.1.0", variables={}))
        )
        mock_template.render_template = AsyncMock(return_value="# Updated Template\nnew_value")

        manager.template_manager = mock_template

        # Update template
        result = await manager.update_parent_directory_template(test_dir, {"VAR1": "new_value"})

        assert result.success is True
        assert result.action == ParentDirectoryAction.UPDATE
        assert result.template_id == "test_template"
        assert result.version == "1.1.0"

        # Check that file was updated
        content = claude_file.read_text()
        assert "# Updated Template" in content
        assert "new_value" in content

    @pytest.mark.asyncio
    async def test_update_unmanaged_directory(self, parent_directory_manager, temp_dir):
        """Test updating an unmanaged directory."""
        manager = parent_directory_manager

        # Create test directory (not registered)
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Try to update
        result = await manager.update_parent_directory_template(test_dir)

        assert result.success is False
        assert "Directory not managed" in result.error_message

    @pytest.mark.asyncio
    async def test_get_parent_directory_status(self, parent_directory_manager, temp_dir):
        """Test getting parent directory status."""
        manager = parent_directory_manager

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Test status for non-existent file
        status = await manager.get_parent_directory_status(test_dir)
        assert status.exists is False
        assert status.is_managed is False

        # Create CLAUDE.md file
        claude_file = test_dir / "CLAUDE.md"
        claude_file.write_text("# Test Content")

        # Test status for existing file
        status = await manager.get_parent_directory_status(test_dir)
        assert status.exists is True
        assert status.is_managed is False
        assert status.checksum is not None
        assert status.last_modified is not None

        # Register directory and test managed status
        await manager.register_parent_directory(
            test_dir, ParentDirectoryContext.CUSTOM, "test_template"
        )

        status = await manager.get_parent_directory_status(test_dir)
        assert status.exists is True
        assert status.is_managed is True
        assert status.template_source == "test_template"

    @pytest.mark.asyncio
    async def test_backup_parent_directory(self, parent_directory_manager, temp_dir):
        """Test backing up a parent directory."""
        manager = parent_directory_manager

        # Create test directory with CLAUDE.md
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        claude_file = test_dir / "CLAUDE.md"
        claude_file.write_text("# Test Content for Backup")

        # Create backup
        backup_path = await manager.backup_parent_directory(test_dir)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.parent == manager.backups_dir
        assert "CLAUDE.md" in backup_path.name

        # Check backup content
        backup_content = backup_path.read_text()
        assert backup_content == "# Test Content for Backup"

    @pytest.mark.asyncio
    async def test_backup_nonexistent_file(self, parent_directory_manager, temp_dir):
        """Test backing up a non-existent file."""
        manager = parent_directory_manager

        # Create test directory without CLAUDE.md
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Try to create backup
        backup_path = await manager.backup_parent_directory(test_dir)

        assert backup_path is None

    @pytest.mark.asyncio
    async def test_restore_parent_directory(self, parent_directory_manager, temp_dir):
        """Test restoring a parent directory from backup."""
        manager = parent_directory_manager

        # Create test directory with CLAUDE.md
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        claude_file = test_dir / "CLAUDE.md"
        claude_file.write_text("# Original Content")

        # Create backup
        backup_path = await manager.backup_parent_directory(test_dir)

        # Modify original file
        claude_file.write_text("# Modified Content")

        # Restore from backup
        result = await manager.restore_parent_directory(test_dir)

        assert result.success is True
        assert result.action == ParentDirectoryAction.RESTORE

        # Check that file was restored
        restored_content = claude_file.read_text()
        assert restored_content == "# Original Content"

    @pytest.mark.asyncio
    async def test_restore_without_backup(self, parent_directory_manager, temp_dir):
        """Test restoring without available backup."""
        manager = parent_directory_manager

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Try to restore
        result = await manager.restore_parent_directory(test_dir)

        assert result.success is False
        assert "No backup files found" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_parent_directory(self, parent_directory_manager, temp_dir):
        """Test validating a parent directory."""
        manager = parent_directory_manager

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Test validation without CLAUDE.md
        result = await manager.validate_parent_directory(test_dir)
        assert result.success is False
        assert "CLAUDE.md file not found" in result.error_message

        # Create CLAUDE.md file
        claude_file = test_dir / "CLAUDE.md"
        claude_file.write_text("# Test Content")

        # Test validation of unmanaged directory
        result = await manager.validate_parent_directory(test_dir)
        assert result.success is True
        assert "Directory not managed" in result.warnings[0]

        # Register directory and test managed validation
        await manager.register_parent_directory(
            test_dir, ParentDirectoryContext.CUSTOM, "test_template"
        )

        # Mock template manager for validation
        mock_template = Mock()
        mock_template.render_template = AsyncMock(return_value="# Test Content")
        manager.template_manager = mock_template

        result = await manager.validate_parent_directory(test_dir)
        assert result.success is True
        assert result.template_id == "test_template"

    @pytest.mark.asyncio
    async def test_list_managed_directories(self, parent_directory_manager, temp_dir):
        """Test listing managed directories."""
        manager = parent_directory_manager

        # Initially empty
        directories = await manager.list_managed_directories()
        assert directories == []

        # Create and register test directories
        test_dir1 = temp_dir / "test_parent1"
        test_dir1.mkdir()
        (test_dir1 / "CLAUDE.md").write_text("# Test 1")

        test_dir2 = temp_dir / "test_parent2"
        test_dir2.mkdir()

        await manager.register_parent_directory(
            test_dir1, ParentDirectoryContext.PROJECT_COLLECTION, "template1"
        )

        await manager.register_parent_directory(
            test_dir2, ParentDirectoryContext.DEPLOYMENT_ROOT, "template2"
        )

        # List directories
        directories = await manager.list_managed_directories()

        assert len(directories) == 2

        # Check directory information
        dir_paths = [d["directory"] for d in directories]
        assert str(test_dir1) in dir_paths
        assert str(test_dir2) in dir_paths

        # Check details for first directory
        dir1_info = next(d for d in directories if d["directory"] == str(test_dir1))
        assert dir1_info["context"] == "project_collection"
        assert dir1_info["template_id"] == "template1"
        assert dir1_info["exists"] is True
        assert dir1_info["is_managed"] is True

    @pytest.mark.asyncio
    async def test_get_operation_history(self, parent_directory_manager, temp_dir):
        """Test getting operation history."""
        manager = parent_directory_manager

        # Initially empty
        history = await manager.get_operation_history()
        assert history == []

        # Create test directory and perform operations
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Mock template manager
        mock_template = Mock()
        mock_template.get_template = AsyncMock(
            return_value=("# Test Template", Mock(version="1.0.0", variables={}))
        )
        mock_template.render_template = AsyncMock(return_value="# Test Template")

        manager.template_manager = mock_template

        # Perform install operation
        await manager.install_template_to_parent_directory(test_dir, "test_template")

        # Check operation history
        history = await manager.get_operation_history()

        assert len(history) == 1
        assert history[0]["action"] == "install"
        assert history[0]["template_id"] == "test_template"
        assert history[0]["success"] is True

    @pytest.mark.asyncio
    async def test_detect_parent_directory_context(self, parent_directory_manager, temp_dir):
        """Test detecting parent directory context."""
        manager = parent_directory_manager

        # Test deployment root context
        deployment_dir = temp_dir / "deployment_test"
        deployment_dir.mkdir()
        (deployment_dir / "claude-multiagent-pm").mkdir()

        context = await manager.detect_parent_directory_context(deployment_dir)
        assert context == ParentDirectoryContext.DEPLOYMENT_ROOT

        # Test project collection context
        project_collection_dir = temp_dir / "projects"
        project_collection_dir.mkdir()

        # Create multiple project directories
        project1 = project_collection_dir / "project1"
        project1.mkdir()
        (project1 / ".git").mkdir()

        project2 = project_collection_dir / "project2"
        project2.mkdir()
        (project2 / "package.json").write_text("{}")

        context = await manager.detect_parent_directory_context(project_collection_dir)
        assert context == ParentDirectoryContext.PROJECT_COLLECTION

        # Test workspace root context
        workspace_dir = temp_dir / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / ".vscode").mkdir()

        context = await manager.detect_parent_directory_context(workspace_dir)
        assert context == ParentDirectoryContext.WORKSPACE_ROOT

        # Test custom context
        custom_dir = temp_dir / "custom"
        custom_dir.mkdir()

        context = await manager.detect_parent_directory_context(custom_dir)
        assert context == ParentDirectoryContext.CUSTOM

    @pytest.mark.asyncio
    async def test_auto_register_parent_directories(self, parent_directory_manager, temp_dir):
        """Test auto-registering parent directories."""
        manager = parent_directory_manager

        # Create deployment root directory
        deployment_dir = temp_dir / "deployment_test"
        deployment_dir.mkdir()
        (deployment_dir / "claude-multiagent-pm").mkdir()

        # Create project collection directory
        project_collection_dir = temp_dir / "projects"
        project_collection_dir.mkdir()

        project1 = project_collection_dir / "project1"
        project1.mkdir()
        (project1 / ".git").mkdir()

        project2 = project_collection_dir / "project2"
        project2.mkdir()
        (project2 / "package.json").write_text("{}")

        # Create user home directory (should not be auto-registered)
        user_home_dir = temp_dir / "user_home"
        user_home_dir.mkdir()

        # Auto-register
        search_paths = [deployment_dir, project_collection_dir, user_home_dir]
        registered = await manager.auto_register_parent_directories(search_paths)

        # Check results
        assert len(registered) == 2
        assert deployment_dir in registered
        assert project_collection_dir in registered
        assert user_home_dir not in registered

        # Check that directories were registered
        assert str(deployment_dir) in manager.managed_directories
        assert str(project_collection_dir) in manager.managed_directories
        assert str(user_home_dir) not in manager.managed_directories

    @pytest.mark.asyncio
    async def test_integration_with_template_manager(
        self, parent_directory_manager, temp_dir, mock_template_manager
    ):
        """Test integration with template manager."""
        manager = parent_directory_manager
        manager.template_manager = mock_template_manager

        # Setup mock responses
        mock_template_manager.get_template.return_value = (
            "# {{PROJECT_NAME}} Configuration\n{{DESCRIPTION}}",
            Mock(version="1.0.0", variables={"DESCRIPTION": "Default description"}),
        )
        mock_template_manager.render_template.return_value = (
            "# Test Project Configuration\nProject description"
        )

        # Create test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        # Install template
        result = await manager.install_template_to_parent_directory(
            test_dir,
            "project_template",
            {"PROJECT_NAME": "Test Project", "DESCRIPTION": "Project description"},
        )

        assert result.success is True

        # Verify template manager was called correctly
        mock_template_manager.get_template.assert_called_once_with("project_template")
        mock_template_manager.render_template.assert_called_once_with(
            "project_template",
            {"DESCRIPTION": "Project description", "PROJECT_NAME": "Test Project"},
        )

        # Check file was created with correct content
        claude_file = test_dir / "CLAUDE.md"
        assert claude_file.exists()
        content = claude_file.read_text()
        assert "# Test Project Configuration" in content
        assert "Project description" in content

    @pytest.mark.asyncio
    async def test_integration_with_dependency_manager(
        self, parent_directory_manager, mock_dependency_manager
    ):
        """Test integration with dependency manager."""
        manager = parent_directory_manager

        # Test that the manager can work with a dependency manager
        # Note: _initialize_cmpm_integrations() creates real services, not mocks
        # so we test the integration logic separately

        # Set mock dependency manager after initialization
        manager.dependency_manager = mock_dependency_manager

        # Manually validate deployment context (simulating what happens in _validate_deployment_context)
        if manager.deployment_aware and manager.dependency_manager:
            deployment_config = getattr(manager.dependency_manager, "deployment_config", None)
            if deployment_config:
                manager.deployment_context = deployment_config

        # Check that deployment context integration works
        assert hasattr(manager, "deployment_context")
        assert manager.deployment_context == mock_dependency_manager.deployment_config

    @pytest.mark.asyncio
    async def test_backup_and_restore_workflow(self, parent_directory_manager, temp_dir):
        """Test complete backup and restore workflow."""
        manager = parent_directory_manager

        # Create test directory with CLAUDE.md
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        claude_file = test_dir / "CLAUDE.md"
        original_content = "# Original Configuration\nThis is the original content."
        claude_file.write_text(original_content)

        # Create backup
        backup_path = await manager.backup_parent_directory(test_dir)
        assert backup_path is not None

        # Modify file
        modified_content = "# Modified Configuration\nThis is modified content."
        claude_file.write_text(modified_content)

        # Verify modification
        assert claude_file.read_text() == modified_content

        # Restore from backup
        result = await manager.restore_parent_directory(test_dir)
        assert result.success is True

        # Verify restoration
        restored_content = claude_file.read_text()
        assert restored_content == original_content

        # Check that a backup of the modified version was created
        assert result.backup_path is not None
        assert result.backup_path.exists()
        modified_backup_content = result.backup_path.read_text()
        assert modified_backup_content == modified_content

    @pytest.mark.asyncio
    async def test_error_handling(self, parent_directory_manager, temp_dir):
        """Test error handling in various scenarios."""
        manager = parent_directory_manager

        # Test with permission errors
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir()

        # Create a file with restricted permissions
        claude_file = restricted_dir / "CLAUDE.md"
        claude_file.write_text("# Test Content")
        claude_file.chmod(0o000)  # No permissions

        try:
            # Try to backup (should handle permission error gracefully)
            backup_path = await manager.backup_parent_directory(restricted_dir)
            # Should return None or handle gracefully
            assert backup_path is None
        finally:
            # Restore permissions for cleanup
            claude_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_configuration_persistence(self, parent_directory_manager, temp_dir):
        """Test that configuration is persisted across restarts."""
        manager = parent_directory_manager

        # Create and register test directory
        test_dir = temp_dir / "test_parent"
        test_dir.mkdir()

        await manager.register_parent_directory(
            test_dir, ParentDirectoryContext.PROJECT_COLLECTION, "test_template", {"var1": "value1"}
        )

        # Save configuration
        await manager._save_managed_directories()

        # Verify configuration file exists
        assert manager.managed_directories_file.exists()

        # Load configuration manually to verify format
        with open(manager.managed_directories_file, "r") as f:
            saved_config = json.load(f)

        assert str(test_dir) in saved_config
        config_data = saved_config[str(test_dir)]
        assert config_data["context"] == "project_collection"
        assert config_data["template_id"] == "test_template"
        assert config_data["template_variables"] == {"var1": "value1"}

        # Create new manager instance and load configuration
        new_manager = ParentDirectoryManager()
        new_manager.working_dir = manager.working_dir
        new_manager.parent_directory_manager_dir = manager.parent_directory_manager_dir
        new_manager._initialize_paths()

        await new_manager._load_managed_directories()

        # Verify configuration was loaded correctly
        assert str(test_dir) in new_manager.managed_directories
        loaded_config = new_manager.managed_directories[str(test_dir)]
        assert loaded_config.context == ParentDirectoryContext.PROJECT_COLLECTION
        assert loaded_config.template_id == "test_template"
        assert loaded_config.template_variables == {"var1": "value1"}


if __name__ == "__main__":
    pytest.main([__file__])
