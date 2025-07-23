"""Unit tests for the ConfigAliasManager module."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from claude_pm.core.config_aliases import (
    ConfigAliasManager,
    ConfigAliasError,
    AliasNotFoundError,
    DuplicateAliasError,
    InvalidDirectoryError,
)


class TestConfigAliasManager:
    """Test cases for ConfigAliasManager."""
    
    @pytest.fixture
    def temp_aliases_file(self):
        """Create a temporary aliases file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_file = Path(f.name)
        yield temp_file
        if temp_file.exists():
            temp_file.unlink()
    
    @pytest.fixture
    def manager(self, temp_aliases_file):
        """Create a ConfigAliasManager instance for testing."""
        return ConfigAliasManager(temp_aliases_file)
    
    def test_initialization(self, temp_aliases_file):
        """Test manager initialization."""
        manager = ConfigAliasManager(temp_aliases_file)
        assert manager.aliases_file == temp_aliases_file
        assert temp_aliases_file.exists()
    
    def test_create_alias(self, manager, tmp_path):
        """Test creating a new alias."""
        test_dir = tmp_path / "test_config"
        manager.create_alias("test", str(test_dir))
        
        assert manager.alias_exists("test")
        assert manager.get_alias("test") == str(test_dir)
        assert test_dir.exists()
    
    def test_create_duplicate_alias(self, manager, tmp_path):
        """Test creating a duplicate alias raises error."""
        test_dir = tmp_path / "test_config"
        manager.create_alias("test", str(test_dir))
        
        with pytest.raises(DuplicateAliasError) as exc_info:
            manager.create_alias("test", str(tmp_path / "another_dir"))
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_alias_empty_name(self, manager):
        """Test creating alias with empty name raises error."""
        with pytest.raises(ValueError) as exc_info:
            manager.create_alias("", "/tmp/test")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_resolve_alias(self, manager, tmp_path):
        """Test resolving an alias."""
        test_dir = tmp_path / "test_config"
        manager.create_alias("test", str(test_dir))
        
        resolved = manager.resolve_alias("test")
        assert resolved == test_dir
    
    def test_resolve_nonexistent_alias(self, manager):
        """Test resolving a non-existent alias raises error."""
        with pytest.raises(AliasNotFoundError) as exc_info:
            manager.resolve_alias("nonexistent")
        
        assert "not found" in str(exc_info.value)
    
    def test_list_aliases(self, manager, tmp_path):
        """Test listing all aliases."""
        # Create multiple aliases
        aliases_data = {
            "personal": tmp_path / "personal",
            "work": tmp_path / "work",
            "test": tmp_path / "test",
        }
        
        for name, path in aliases_data.items():
            manager.create_alias(name, str(path))
        
        aliases = manager.list_aliases()
        assert len(aliases) == 3
        
        # Check they're sorted
        names = [alias[0] for alias in aliases]
        assert names == sorted(names)
    
    def test_delete_alias(self, manager, tmp_path):
        """Test deleting an alias."""
        test_dir = tmp_path / "test_config"
        manager.create_alias("test", str(test_dir))
        
        manager.delete_alias("test")
        assert not manager.alias_exists("test")
    
    def test_delete_nonexistent_alias(self, manager):
        """Test deleting a non-existent alias raises error."""
        with pytest.raises(AliasNotFoundError) as exc_info:
            manager.delete_alias("nonexistent")
        
        assert "not found" in str(exc_info.value)
    
    def test_validate_directory_creates_missing(self, tmp_path):
        """Test validate_directory creates missing directories."""
        manager = ConfigAliasManager()
        test_dir = tmp_path / "new" / "nested" / "directory"
        
        validated = manager.validate_directory(str(test_dir))
        assert validated == test_dir
        assert test_dir.exists()
    
    def test_validate_directory_file_error(self, tmp_path):
        """Test validate_directory raises error for files."""
        manager = ConfigAliasManager()
        test_file = tmp_path / "file.txt"
        test_file.touch()
        
        with pytest.raises(InvalidDirectoryError) as exc_info:
            manager.validate_directory(str(test_file))
        
        assert "is a file, not a directory" in str(exc_info.value)
    
    def test_validate_directory_expands_paths(self):
        """Test validate_directory expands ~ and environment variables."""
        manager = ConfigAliasManager()
        
        # Test home directory expansion
        home_path = manager.validate_directory("~/test_claude_pm_temp")
        assert str(home_path).startswith(str(Path.home()))
        
        # Clean up
        if home_path.exists():
            home_path.rmdir()
    
    def test_update_alias(self, manager, tmp_path):
        """Test updating an existing alias."""
        old_dir = tmp_path / "old"
        new_dir = tmp_path / "new"
        
        manager.create_alias("test", str(old_dir))
        manager.update_alias("test", str(new_dir))
        
        assert manager.get_alias("test") == str(new_dir)
    
    def test_update_nonexistent_alias(self, manager, tmp_path):
        """Test updating a non-existent alias raises error."""
        with pytest.raises(AliasNotFoundError) as exc_info:
            manager.update_alias("nonexistent", str(tmp_path))
        
        assert "not found" in str(exc_info.value)
    
    def test_get_all_aliases(self, manager, tmp_path):
        """Test getting all aliases as a dictionary."""
        aliases_data = {
            "test1": str(tmp_path / "test1"),
            "test2": str(tmp_path / "test2"),
        }
        
        for name, path in aliases_data.items():
            manager.create_alias(name, path)
        
        all_aliases = manager.get_all_aliases()
        assert all_aliases == aliases_data
    
    def test_reload_aliases(self, manager, temp_aliases_file, tmp_path):
        """Test reloading aliases from file."""
        # Create an alias
        manager.create_alias("test", str(tmp_path))
        
        # Modify the file directly
        new_data = {"modified": "/tmp/modified"}
        with open(temp_aliases_file, 'w') as f:
            json.dump(new_data, f)
        
        # Reload
        manager.reload_aliases()
        
        # Check that the manager now has the modified data
        assert not manager.alias_exists("test")
        assert manager.alias_exists("modified")
    
    def test_json_decode_error_handling(self, temp_aliases_file):
        """Test handling of corrupted JSON file."""
        # Write invalid JSON
        with open(temp_aliases_file, 'w') as f:
            f.write("invalid json{")
        
        # Should not raise, but return empty dict
        manager = ConfigAliasManager(temp_aliases_file)
        assert manager.get_all_aliases() == {}
    
    def test_permission_error_handling(self, tmp_path):
        """Test handling of permission errors."""
        # This test is platform-specific and may need adjustment
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        
        # Make directory read-only
        test_dir.chmod(0o444)
        
        manager = ConfigAliasManager()
        
        # Should raise InvalidDirectoryError when trying to validate
        # a directory we can't write to
        with pytest.raises(InvalidDirectoryError):
            manager.validate_directory(str(test_dir))
        
        # Restore permissions for cleanup
        test_dir.chmod(0o755)
    
    def test_save_aliases_error_handling(self, temp_aliases_file):
        """Test error handling when saving aliases fails."""
        manager = ConfigAliasManager(temp_aliases_file)
        
        # Make the file read-only to simulate write error
        temp_aliases_file.chmod(0o444)
        
        with pytest.raises(ConfigAliasError) as exc_info:
            manager._save_aliases({"test": "/tmp/test"})
        
        assert "Failed to save aliases" in str(exc_info.value)
        
        # Restore permissions
        temp_aliases_file.chmod(0o644)
    
    def test_load_aliases_error_handling(self, temp_aliases_file, monkeypatch):
        """Test error handling when loading aliases fails."""
        # Test general exception handling
        def mock_open_error(*args, **kwargs):
            raise OSError("Permission denied")
        
        monkeypatch.setattr("builtins.open", mock_open_error)
        
        manager = ConfigAliasManager(temp_aliases_file)
        # Should return empty dict on error
        assert manager._load_aliases() == {}
    
    def test_ensure_aliases_file_logging(self, tmp_path, caplog):
        """Test logging when creating new aliases file."""
        import logging
        caplog.set_level(logging.INFO)
        
        aliases_file = tmp_path / "new_aliases.json"
        manager = ConfigAliasManager(aliases_file)
        
        # Check that info log was created
        assert "Created new aliases file" in caplog.text
    
    def test_validate_directory_invalid_path(self, manager):
        """Test validate_directory with various invalid paths."""
        # Test with None path
        with pytest.raises(InvalidDirectoryError):
            manager.validate_directory(None)
    
    def test_validate_directory_permission_error(self, tmp_path, monkeypatch):
        """Test validate_directory when mkdir fails."""
        manager = ConfigAliasManager()
        
        # Mock mkdir to raise permission error
        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Cannot create directory")
        
        monkeypatch.setattr(Path, "mkdir", mock_mkdir)
        
        with pytest.raises(InvalidDirectoryError) as exc_info:
            manager.validate_directory(str(tmp_path / "new_dir"))
        
        assert "Cannot create directory" in str(exc_info.value)
    
    def test_validate_directory_general_error(self, tmp_path):
        """Test validate_directory with general exception."""
        manager = ConfigAliasManager()
        
        # Test with invalid path that will cause general exception
        with pytest.raises(InvalidDirectoryError) as exc_info:
            manager.validate_directory("\0invalid\0path")
        
        assert "Invalid directory path" in str(exc_info.value)
    
    def test_resolve_alias_with_invalid_directory(self, manager, tmp_path, monkeypatch):
        """Test resolve_alias when directory validation fails."""
        test_dir = tmp_path / "test_config"
        manager.create_alias("test", str(test_dir))
        
        # Mock validate_directory to raise InvalidDirectoryError
        def mock_validate_fail(path):
            raise InvalidDirectoryError("Directory no longer valid")
        
        monkeypatch.setattr(manager, "validate_directory", mock_validate_fail)
        
        # Should still return the path despite validation failure
        resolved = manager.resolve_alias("test")
        assert resolved == Path(str(test_dir))
    
    def test_create_alias_with_whitespace(self, manager, tmp_path):
        """Test creating alias with whitespace in name."""
        test_dir = tmp_path / "test_config"
        
        # Should strip whitespace
        manager.create_alias("  test  ", str(test_dir))
        assert manager.alias_exists("test")
        assert not manager.alias_exists("  test  ")
    
    def test_create_alias_with_special_chars(self, manager, tmp_path):
        """Test creating alias with special characters."""
        test_dir = tmp_path / "test_config"
        
        # Special characters should work
        special_names = ["test-alias", "test_alias", "test.alias", "test@work"]
        
        for i, name in enumerate(special_names):
            dir_path = tmp_path / f"config_{i}"
            manager.create_alias(name, str(dir_path))
            assert manager.alias_exists(name)
    
    def test_environment_variable_expansion(self, manager, monkeypatch, tmp_path):
        """Test path expansion with environment variables."""
        # Set a test environment variable
        test_path = str(tmp_path / "env_test")
        monkeypatch.setenv("TEST_CLAUDE_PATH", test_path)
        
        # Create alias with environment variable
        expanded = manager.validate_directory("$TEST_CLAUDE_PATH/config")
        assert str(expanded) == str(Path(test_path) / "config")
        assert expanded.exists()
    
    def test_validate_directory_touch_error(self, tmp_path, monkeypatch):
        """Test validate_directory when touch fails (directory not writable)."""
        manager = ConfigAliasManager()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        # Mock touch to raise permission error
        def mock_touch(self):
            raise PermissionError("Cannot write to directory")
        
        monkeypatch.setattr(Path, "touch", mock_touch)
        
        with pytest.raises(InvalidDirectoryError) as exc_info:
            manager.validate_directory(str(test_dir))
        
        assert "not writable" in str(exc_info.value)