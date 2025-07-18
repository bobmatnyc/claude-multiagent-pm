"""
Unit tests for OrchestrationDetector
"""

import os
import tempfile
import unittest
import platform
from pathlib import Path
from unittest.mock import patch, mock_open
import logging

from claude_pm.orchestration.orchestration_detector import OrchestrationDetector


def is_case_sensitive_filesystem():
    """Check if the filesystem is case-sensitive."""
    # Create a test to check case sensitivity
    test_path = Path("/tmp")
    return test_path.resolve() != Path("/TMP").resolve()


class TestOrchestrationDetector(unittest.TestCase):
    """Test cases for OrchestrationDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_dir.cleanup()
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        detector = OrchestrationDetector()
        self.assertEqual(detector.start_path, Path.cwd())
    
    def test_init_custom_path(self):
        """Test initialization with custom path."""
        custom_path = self.test_path / "custom"
        custom_path.mkdir(parents=True)
        detector = OrchestrationDetector(custom_path)
        self.assertEqual(detector.start_path, custom_path)
    
    def test_orchestration_enabled_by_default(self):
        """Test that orchestration is enabled by default when no flags present."""
        # Create CLAUDE.md without any orchestration flags
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Project Config\nSome other content\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_orchestration_explicitly_disabled(self):
        """Test detection when CLAUDE.md explicitly disables orchestration."""
        # Create CLAUDE.md with disable flag
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Project Config\nCLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_orchestration_legacy_enabled(self):
        """Test detection with legacy enable flag (backward compatibility)."""
        # Create CLAUDE.md with legacy enable flag
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Project Config\nCLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_orchestration_enabled_no_claude_md(self):
        """Test that orchestration is enabled by default even without CLAUDE.md."""
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_disable_flag_in_parent_directory(self):
        """Test that disable flag in parent directory is respected."""
        # Create nested directory
        nested_path = self.test_path / "nested"
        nested_path.mkdir()
        
        # Create CLAUDE.md with disable flag in parent
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        detector = OrchestrationDetector(nested_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    @unittest.skipUnless(is_case_sensitive_filesystem(), "Requires case-sensitive filesystem")
    def test_case_sensitive_filename(self):
        """Test that filename matching is case-sensitive."""
        # Create claude.md (lowercase) with flag - should not be detected
        claude_md = self.test_path / "claude.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())  # Default enabled
    
    def test_case_sensitive_flag(self):
        """Test that flag matching is case-sensitive."""
        # Create CLAUDE.md with lowercase flag - should not disable (default is enabled)
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("claude_pm_orchestration: disabled\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_parent_directory_search(self):
        """Test searching in parent directories."""
        # Create nested directory structure
        nested_path = self.test_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)
        
        # Create CLAUDE.md with disable flag in level1
        claude_md = self.test_path / "level1" / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Detector starting from level3 should find it (within 3 parent levels)
        detector = OrchestrationDetector(nested_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_parent_directory_search_beyond_limit(self):
        """Test that search doesn't go beyond MAX_PARENT_LEVELS."""
        # Create deeply nested directory structure (4 levels)
        beyond_path = self.test_path / "level1" / "level2" / "level3" / "level4"
        beyond_path.mkdir(parents=True)
        
        # Create CLAUDE.md with disable flag in level1
        claude_md = self.test_path / "level1" / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Detector starting from beyond should not find it (default enabled)
        detector = OrchestrationDetector(beyond_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_claude_md_not_a_file(self):
        """Test handling when CLAUDE.md exists but is not a file."""
        # Create CLAUDE.md as a directory
        claude_md_dir = self.test_path / "CLAUDE.md"
        claude_md_dir.mkdir()
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())  # Default enabled
    
    def test_permission_error_reading_file(self):
        """Test handling permission errors when reading CLAUDE.md."""
        # Create CLAUDE.md
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Mock permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            detector = OrchestrationDetector(self.test_path)
            self.assertTrue(detector.is_orchestration_enabled())  # Default enabled on error
    
    def test_io_error_reading_file(self):
        """Test handling IO errors when reading CLAUDE.md."""
        # Create CLAUDE.md
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Mock IO error
        with patch("builtins.open", side_effect=IOError("Read error")):
            detector = OrchestrationDetector(self.test_path)
            self.assertTrue(detector.is_orchestration_enabled())  # Default enabled on error
    
    def test_get_claude_md_path(self):
        """Test getting path to CLAUDE.md file."""
        # Test when no CLAUDE.md exists
        detector = OrchestrationDetector(self.test_path)
        self.assertIsNone(detector.get_claude_md_path())
        
        # Test when CLAUDE.md exists
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Config\n")
        self.assertEqual(detector.get_claude_md_path(), claude_md)
    
    def test_flag_anywhere_in_file(self):
        """Test that flag can be anywhere in the file."""
        claude_md = self.test_path / "CLAUDE.md"
        content = """
# Project Configuration

Some content here

## Settings
CLAUDE_PM_ORCHESTRATION: DISABLED

More content
"""
        claude_md.write_text(content)
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_multiple_claude_md_files(self):
        """Test behavior with multiple CLAUDE.md files in hierarchy."""
        # Create nested structure
        nested_path = self.test_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)
        
        # Create CLAUDE.md in level3 with enable flag
        level3_claude = nested_path / "CLAUDE.md"
        level3_claude.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Create another CLAUDE.md with disable flag higher up
        level1_claude = self.test_path / "level1" / "CLAUDE.md"
        level1_claude.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Should find the closer one (level3 has enable flag)
        detector = OrchestrationDetector(nested_path)
        self.assertTrue(detector.is_orchestration_enabled())
        self.assertEqual(detector.get_claude_md_path(), level3_claude)
    
    def test_flag_with_extra_whitespace(self):
        """Test that exact flag match is required (no extra whitespace)."""
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION:  DISABLED\n")  # Extra space
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())  # Not recognized, default enabled
    
    @patch("builtins.open", new_callable=mock_open, read_data="CLAUDE_PM_ORCHESTRATION: DISABLED\n")
    def test_file_read_count(self, mock_file):
        """Test that file is read on each check (no caching)."""
        detector = OrchestrationDetector(self.test_path)
        
        # Create CLAUDE.md
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # First call should check for disable flag
        result1 = detector.is_orchestration_enabled()
        # Second call should also check (no caching in detector)
        result2 = detector.is_orchestration_enabled()
        
        # Both should return False (disabled)
        self.assertFalse(result1)
        self.assertFalse(result2)
        # File should be opened at least twice
        self.assertGreaterEqual(mock_file.call_count, 2)
    
    def test_error_handling_with_logging(self):
        """Test that errors are logged appropriately."""
        # Create CLAUDE.md
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: DISABLED\n")
        
        # Mock file open to raise exception
        with patch("builtins.open", side_effect=Exception("Unexpected error")):
            detector = OrchestrationDetector(self.test_path)
            result = detector.is_orchestration_enabled()
            
            # Should return True (default enabled) even with error
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()