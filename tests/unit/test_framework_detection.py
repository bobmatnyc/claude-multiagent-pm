"""
Tests for framework detection utilities.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_pm.utils.framework_detection import (
    is_framework_source_directory,
    ensure_is_framework_source,
    ensure_not_framework_source
)


class TestFrameworkDetection:
    """Test framework detection functionality."""
    
    def test_is_framework_source_directory_with_pyproject(self, tmp_path):
        """Test detection via pyproject.toml."""
        # Create a pyproject.toml with framework name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "claude-multiagent-pm"\n')
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is True
        assert "pyproject.toml (claude-multiagent-pm)" in markers
    
    def test_is_framework_source_directory_with_package_json(self, tmp_path):
        """Test detection via package.json."""
        # Create a package.json with framework name
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "@bobmatnyc/claude-multiagent-pm"}')
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is True
        assert "package.json (@bobmatnyc/claude-multiagent-pm)" in markers
    
    def test_is_framework_source_directory_with_claude_pm_dir(self, tmp_path):
        """Test detection via claude_pm directory."""
        # Create claude_pm directory
        (tmp_path / "claude_pm").mkdir()
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is True
        assert "claude_pm/ source directory" in markers
    
    def test_is_framework_source_directory_with_claude_md(self, tmp_path):
        """Test detection via CLAUDE.md."""
        # Create CLAUDE.md with developer marker
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("This file is for FRAMEWORK DEVELOPERS ONLY")
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is True
        assert "CLAUDE.md (development version)" in markers
    
    def test_is_framework_source_directory_user_project(self, tmp_path):
        """Test that user projects are not detected as framework source."""
        # Create a user project structure
        (tmp_path / ".claude-pm").mkdir()
        (tmp_path / "my_project.py").touch()
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is False
        assert len(markers) == 0
    
    def test_ensure_is_framework_source_success(self, tmp_path):
        """Test ensure_is_framework_source with framework directory."""
        # Create framework marker
        (tmp_path / "claude_pm").mkdir()
        
        # Should not raise
        ensure_is_framework_source(tmp_path)
    
    def test_ensure_is_framework_source_failure(self, tmp_path):
        """Test ensure_is_framework_source with user project."""
        # Create user project
        (tmp_path / ".claude-pm").mkdir()
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="appears to be a user project"):
            ensure_is_framework_source(tmp_path)
    
    def test_ensure_not_framework_source_success(self, tmp_path):
        """Test ensure_not_framework_source with user project."""
        # Create user project
        (tmp_path / ".claude-pm").mkdir()
        
        # Should not raise
        ensure_not_framework_source(tmp_path)
    
    def test_ensure_not_framework_source_failure(self, tmp_path):
        """Test ensure_not_framework_source with framework directory."""
        # Create framework marker
        (tmp_path / "claude_pm").mkdir()
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="appears to be the framework source"):
            ensure_not_framework_source(tmp_path)
    
    def test_multiple_framework_markers(self, tmp_path):
        """Test detection with multiple framework markers."""
        # Create multiple markers
        (tmp_path / "claude_pm").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "framework").mkdir()
        
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "claude-multiagent-pm"\n')
        
        is_source, markers = is_framework_source_directory(tmp_path)
        assert is_source is True
        assert len(markers) >= 5  # Should have multiple markers
        assert "claude_pm/ source directory" in markers
        assert "tests/ directory" in markers
        assert "scripts/ directory" in markers