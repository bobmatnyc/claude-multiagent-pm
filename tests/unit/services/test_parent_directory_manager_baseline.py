"""
Baseline tests for ParentDirectoryManager before Phase 2 refactoring.
Focuses on testing actual available methods to establish working baseline.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from claude_pm.services.parent_directory_manager import ParentDirectoryManager


class TestParentDirectoryManagerBaseline:
    """Baseline tests for current implementation"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create a basic manager instance"""
        config = {
            "parent_directories": {
                "root_directory": str(temp_dir)
            }
        }
        return ParentDirectoryManager(config=config, quiet_mode=True)
    
    def test_init(self):
        """Test basic initialization"""
        manager = ParentDirectoryManager(quiet_mode=True)
        assert manager.quiet_mode is True
        assert manager.initialized is False
        assert isinstance(manager.config, dict)
    
    def test_init_with_config(self, temp_dir):
        """Test initialization with config"""
        config = {"parent_directories": {"root_directory": str(temp_dir)}}
        manager = ParentDirectoryManager(config=config, quiet_mode=True)
        assert manager.config == config
        assert manager.parent_dirs_config == config["parent_directories"]
    
    @patch('claude_pm.services.parent_directory_manager.logger')
    def test_log_info_if_not_quiet(self, mock_logger):
        """Test quiet mode logging"""
        # Quiet mode - should not log
        manager = ParentDirectoryManager(quiet_mode=True)
        manager._log_info_if_not_quiet("Test message")
        mock_logger.info.assert_not_called()
        
        # Verbose mode - should log
        mock_logger.reset_mock()
        manager = ParentDirectoryManager(quiet_mode=False)  
        manager._log_info_if_not_quiet("Test message")
        mock_logger.info.assert_called_once_with("Test message")
    
    def test_get_subsystem_versions(self, manager):
        """Test getting subsystem versions"""
        # Should return empty dict when no version files exist
        versions = manager.get_subsystem_versions()
        assert isinstance(versions, dict)
    
    def test_get_subsystem_version(self, manager):
        """Test getting specific subsystem version"""
        # Should return None when version file doesn't exist
        version = manager.get_subsystem_version("agents")
        assert version is None
    
    def test_get_subsystem_version_report(self, manager):
        """Test version report generation"""
        report = manager.get_subsystem_version_report()
        assert isinstance(report, dict)
        assert "report_timestamp" in report
        assert "subsystems" in report
    
    def test_get_framework_backup_status(self, manager):
        """Test framework backup status"""
        status = manager.get_framework_backup_status()
        assert isinstance(status, dict)
        assert "backup_dir" in status
        assert "backups" in status
        assert "latest_backup" in status
    
    @pytest.mark.asyncio
    async def test_async_methods_exist(self, manager):
        """Verify async methods are available"""
        # Just check they exist, don't call them
        assert hasattr(manager, 'register_parent_directory')
        assert hasattr(manager, 'get_parent_directory_status')
        assert hasattr(manager, 'list_managed_directories')
        assert hasattr(manager, 'get_operation_history')
    
    def test_should_skip_deployment(self, manager, temp_dir):
        """Test skip deployment logic"""
        target_file = temp_dir / "test.md"
        
        # Non-existent file should not skip
        skip, reason = manager._should_skip_deployment(
            target_file=target_file,
            force=False,
            skip_if_exists=True
        )
        assert skip is False
        assert reason is None
        
        # Existing file with skip_if_exists should skip
        target_file.write_text("content")
        skip, reason = manager._should_skip_deployment(
            target_file=target_file,
            force=False,
            skip_if_exists=True
        )
        assert skip is True
        assert "already exists" in reason
        
        # Force should override
        skip, reason = manager._should_skip_deployment(
            target_file=target_file,
            force=True,
            skip_if_exists=True
        )
        assert skip is False
        assert reason is None
    
    def test_file_line_count(self):
        """Verify current file size"""
        import claude_pm.services.parent_directory_manager as pdm_module
        source_file = Path(pdm_module.__file__)
        
        with open(source_file, 'r') as f:
            line_count = len(f.readlines())
        
        print(f"\nCurrent parent_directory_manager.py size: {line_count} lines")
        assert line_count > 1000  # Confirms it needs refactoring


class TestRefactoringTargets:
    """Identify refactoring targets for Phase 2"""
    
    def test_identify_large_methods(self):
        """Identify methods that should be extracted"""
        import inspect
        from claude_pm.services.parent_directory_manager import ParentDirectoryManager
        
        large_methods = []
        for name, method in inspect.getmembers(ParentDirectoryManager, predicate=inspect.ismethod):
            if name.startswith('_'):
                continue  # Skip private methods for now
            
            try:
                source = inspect.getsource(method)
                line_count = len(source.splitlines())
                if line_count > 50:
                    large_methods.append((name, line_count))
            except:
                pass
        
        # Print methods that should be refactored
        if large_methods:
            print("\nLarge methods to refactor:")
            for method, lines in sorted(large_methods, key=lambda x: x[1], reverse=True):
                print(f"  - {method}: {lines} lines")
    
    def test_analyze_dependencies(self):
        """Analyze module dependencies for extraction"""
        imports = []
        
        import claude_pm.services.parent_directory_manager as pdm_module
        source_file = Path(pdm_module.__file__)
        
        with open(source_file, 'r') as f:
            for line in f:
                if line.strip().startswith(('import ', 'from ')):
                    imports.append(line.strip())
        
        print(f"\nTotal imports: {len(imports)}")
        print("Key dependencies to consider for module extraction:")
        for imp in imports[:10]:  # First 10 imports
            print(f"  {imp}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])