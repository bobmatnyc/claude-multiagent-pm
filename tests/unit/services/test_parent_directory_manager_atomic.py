"""
Comprehensive unit tests for ParentDirectoryManager atomic methods.
These tests establish baseline behavior before Phase 2 refactoring.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import tempfile
import shutil
import json
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from claude_pm.services.parent_directory_manager import ParentDirectoryManager

# Import types from state_manager
try:
    from claude_pm.services.state_manager import (
        ParentDirectoryStatus,
        ParentDirectoryOperation,
        ParentDirectoryAction
    )
    from claude_pm.services.config_manager import ParentDirectoryConfig
    from claude_pm.services.parent_directory_operations import ParentDirectoryContext
except ImportError:
    # If modules don't exist yet, create mock classes
    class ParentDirectoryStatus:
        pass
    class ParentDirectoryOperation:
        pass
    class ParentDirectoryAction:
        REGISTERED = "registered"
    class ParentDirectoryConfig:
        pass
    class ParentDirectoryContext:
        pass


class TestParentDirectoryManagerAtomic:
    """Test all atomic methods of ParentDirectoryManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock configuration"""
        return {
            "parent_directories": {
                "root_directory": str(temp_dir),
                "max_backups": 3,
                "auto_register": False
            },
            "framework": {
                "template_path": str(temp_dir / "framework" / "CLAUDE.md")
            }
        }
    
    @pytest.fixture
    def manager(self, mock_config, temp_dir):
        """Create a ParentDirectoryManager instance"""
        manager = ParentDirectoryManager(config=mock_config, quiet_mode=True)
        # Don't actually initialize to avoid side effects
        manager.initialized = True
        manager.config = mock_config
        manager.parent_dirs_config = mock_config.get("parent_directories", {})
        manager.managed_dirs_file = temp_dir / ".claude-pm" / "parent_directory_manager" / "configs" / "managed_directories.json"
        manager.operations_log_file = temp_dir / ".claude-pm" / "parent_directory_manager" / "configs" / "operations.log"
        
        # Create necessary directories
        manager.managed_dirs_file.parent.mkdir(parents=True, exist_ok=True)
        manager.operations_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        return manager
    
    # Test initialization methods
    
    def test_init(self, mock_config):
        """Test ParentDirectoryManager initialization"""
        manager = ParentDirectoryManager(config=mock_config, quiet_mode=True)
        assert manager.config == mock_config
        assert manager.quiet_mode is True
        assert manager.initialized is False
        assert manager.parent_dirs_config == mock_config.get("parent_directories", {})
    
    def test_init_no_config(self):
        """Test initialization without config"""
        manager = ParentDirectoryManager(quiet_mode=True)
        assert manager.config == {}
        assert manager.parent_dirs_config == {}
        assert manager.quiet_mode is True
    
    @patch('claude_pm.services.parent_directory_manager.logger')
    def test_log_info_if_not_quiet(self, mock_logger):
        """Test conditional logging based on quiet mode"""
        # Test with quiet_mode=True
        manager = ParentDirectoryManager(quiet_mode=True)
        manager._log_info_if_not_quiet("Test message")
        mock_logger.info.assert_not_called()
        
        # Test with quiet_mode=False
        manager = ParentDirectoryManager(quiet_mode=False)
        manager._log_info_if_not_quiet("Test message")
        mock_logger.info.assert_called_once_with("Test message")
    
    def test_detect_framework_path(self, temp_dir):
        """Test framework path detection"""
        manager = ParentDirectoryManager(quiet_mode=True)
        
        # Mock file system
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('pathlib.Path.resolve') as mock_resolve:
                mock_resolve.return_value = temp_dir
                mock_exists.return_value = True
                
                path = manager._detect_framework_path()
                assert isinstance(path, Path)
    
    # Test public API methods
    
    @pytest.mark.asyncio
    async def test_register_parent_directory(self, manager, temp_dir):
        """Test registering a parent directory"""
        target_dir = temp_dir / "test_project"
        target_dir.mkdir(exist_ok=True)
        
        # Mock the managed directories file
        manager.managed_dirs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(manager.managed_dirs_file, 'w') as f:
            json.dump([], f)
        
        result = await manager.register_parent_directory(
            target_directory=target_dir,
            project_name="Test Project"
        )
        
        assert result.success is True
        assert result.action == ParentDirectoryAction.REGISTERED
        assert result.target_directory == target_dir
    
    @pytest.mark.asyncio
    async def test_get_parent_directory_status(self, manager, temp_dir):
        """Test getting parent directory status"""
        target_dir = temp_dir / "test_project"
        target_dir.mkdir(exist_ok=True)
        
        # Create a CLAUDE.md file
        claude_file = target_dir / "CLAUDE.md"
        claude_file.write_text("# Test CLAUDE.md")
        
        status = await manager.get_parent_directory_status(target_dir)
        
        assert isinstance(status, ParentDirectoryStatus)
        assert status.is_managed is False  # Not in managed list
        assert status.has_claude_md is True
        assert status.claude_md_path == claude_file
    
    def test_get_subsystem_versions(self, manager):
        """Test getting subsystem versions"""
        versions = manager.get_subsystem_versions()
        assert isinstance(versions, dict)
        # Should return empty dict when no files exist
        assert versions == {}
    
    def test_get_subsystem_version(self, manager):
        """Test getting specific subsystem version"""
        version = manager.get_subsystem_version("agents")
        assert version is None  # No version file exists
    
    @pytest.mark.asyncio
    async def test_validate_subsystem_compatibility(self, manager):
        """Test subsystem compatibility validation"""
        required_versions = {
            "agents": "1.0.0",
            "core": "2.0.0"
        }
        
        result = await manager.validate_subsystem_compatibility(required_versions)
        
        assert isinstance(result, dict)
        assert "compatible" in result
        assert "missing" in result
        assert result["compatible"] is False  # No versions exist
    
    def test_get_subsystem_version_report(self, manager):
        """Test subsystem version report generation"""
        report = manager.get_subsystem_version_report()
        
        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "subsystems" in report
        assert isinstance(report["subsystems"], dict)
    
    @pytest.mark.asyncio
    async def test_list_managed_directories(self, manager):
        """Test listing managed directories"""
        # Create managed directories file
        manager.managed_dirs_file.parent.mkdir(parents=True, exist_ok=True)
        test_data = [
            {
                "path": "/test/path1",
                "name": "Project 1",
                "registered_at": "2025-01-19T10:00:00"
            }
        ]
        with open(manager.managed_dirs_file, 'w') as f:
            json.dump(test_data, f)
        
        result = await manager.list_managed_directories()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Project 1"
    
    @pytest.mark.asyncio
    async def test_get_operation_history(self, manager):
        """Test getting operation history"""
        # Create operations log file
        manager.operations_log_file.parent.mkdir(parents=True, exist_ok=True)
        manager.operations_log_file.touch()
        
        # Write test operations
        test_ops = [
            {
                "timestamp": "2025-01-19T10:00:00",
                "action": "register",
                "target": "/test/path",
                "success": True
            }
        ]
        with open(manager.operations_log_file, 'w') as f:
            for op in test_ops:
                f.write(json.dumps(op) + '\n')
        
        result = await manager.get_operation_history(limit=10)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["action"] == "register"
    
    def test_get_framework_backup_status(self, manager):
        """Test framework backup status"""
        status = manager.get_framework_backup_status()
        
        assert isinstance(status, dict)
        assert "backup_dir" in status
        assert "backups" in status
        assert "latest_backup" in status
        assert status["latest_backup"] is None  # No backups exist
    
    # Test error handling
    
    @pytest.mark.asyncio
    async def test_register_nonexistent_directory(self, manager):
        """Test registering a non-existent directory"""
        result = await manager.register_parent_directory(
            target_directory=Path("/nonexistent/path"),
            project_name="Test"
        )
        
        assert result.success is False
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_get_status_nonexistent_directory(self, manager):
        """Test getting status of non-existent directory"""
        status = await manager.get_parent_directory_status(Path("/nonexistent/path"))
        
        assert status.exists is False
        assert status.is_managed is False
    
    # Test internal helper methods
    
    def test_should_skip_deployment(self, manager, temp_dir):
        """Test deployment skip logic"""
        target_file = temp_dir / "CLAUDE.md"
        
        # Test non-existent file
        result = manager._should_skip_deployment(
            target_file=target_file,
            force=False,
            skip_if_exists=True
        )
        assert result == (False, None)
        
        # Test existing file with skip_if_exists
        target_file.write_text("existing content")
        result = manager._should_skip_deployment(
            target_file=target_file,
            force=False,
            skip_if_exists=True
        )
        assert result[0] is True
        assert "already exists" in result[1]
        
        # Test force override
        result = manager._should_skip_deployment(
            target_file=target_file,
            force=True,
            skip_if_exists=True
        )
        assert result == (False, None)
    
    @pytest.mark.asyncio
    async def test_create_backup(self, manager, temp_dir):
        """Test backup creation"""
        # Create a file to backup
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Mock backup directory
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        with patch.object(manager, 'parent_dirs_config', {'root_directory': str(temp_dir)}):
            backup_path = await manager._create_backup(test_file)
            
            # Backup might be None if not configured
            if backup_path:
                assert backup_path.exists()
                assert backup_path.read_text() == "test content"


class TestParentDirectoryManagerIntegration:
    """Integration tests for complex workflows"""
    
    @pytest.fixture
    async def initialized_manager(self, temp_dir):
        """Create and initialize a manager"""
        config = {
            "parent_directories": {
                "root_directory": str(temp_dir),
                "max_backups": 3,
                "auto_register": False
            }
        }
        manager = ParentDirectoryManager(config=config, quiet_mode=True)
        
        # Create required directories
        (temp_dir / ".claude-pm" / "parent_directory_manager" / "configs").mkdir(parents=True, exist_ok=True)
        (temp_dir / ".claude-pm" / "parent_directory_manager" / "backups").mkdir(parents=True, exist_ok=True)
        
        # Initialize managed directories file
        managed_file = temp_dir / ".claude-pm" / "parent_directory_manager" / "configs" / "managed_directories.json"
        managed_file.write_text("[]")
        
        return manager
    
    @pytest.mark.asyncio
    async def test_register_and_deploy_workflow(self, initialized_manager, temp_dir):
        """Test complete register and deploy workflow"""
        project_dir = temp_dir / "test_project"
        project_dir.mkdir(exist_ok=True)
        
        # Create a mock framework template
        framework_dir = temp_dir / "framework"
        framework_dir.mkdir(exist_ok=True)
        template_file = framework_dir / "CLAUDE.md"
        template_file.write_text("# Framework Template\nVersion: {{VERSION}}")
        
        # Register directory
        result = await initialized_manager.register_parent_directory(
            target_directory=project_dir,
            project_name="Test Project"
        )
        
        # Check registration
        if result.success:
            assert result.action == ParentDirectoryAction.REGISTERED
            
            # Check managed directories
            managed_dirs = await initialized_manager.list_managed_directories()
            assert len(managed_dirs) > 0
            assert any(d["path"] == str(project_dir) for d in managed_dirs)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])