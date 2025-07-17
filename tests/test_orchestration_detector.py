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
    
    def test_orchestration_enabled_current_dir(self):
        """Test detection when CLAUDE.md with flag exists in current directory."""
        # Create CLAUDE.md with orchestration flag
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Project Config\nCLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_orchestration_disabled_no_flag(self):
        """Test detection when CLAUDE.md exists but without flag."""
        # Create CLAUDE.md without orchestration flag
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("# Project Config\nSome other content\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_orchestration_disabled_no_file(self):
        """Test detection when no CLAUDE.md exists."""
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    @unittest.skipUnless(is_case_sensitive_filesystem(), "Requires case-sensitive filesystem")
    def test_case_sensitive_filename(self):
        """Test that filename matching is case-sensitive."""
        # Create claude.md (lowercase) with flag - should not be detected
        claude_md = self.test_path / "claude.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_case_sensitive_flag(self):
        """Test that flag matching is case-sensitive."""
        # Create CLAUDE.md with lowercase flag - should not be detected
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("claude_pm_orchestration: enabled\n")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_parent_directory_search(self):
        """Test searching in parent directories."""
        # Create nested directory structure
        nested_path = self.test_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)
        
        # Create CLAUDE.md in level1
        claude_md = self.test_path / "level1" / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Detector starting from level3 should find it (within 3 parent levels)
        detector = OrchestrationDetector(nested_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_max_parent_levels_limit(self):
        """Test that search stops after MAX_PARENT_LEVELS."""
        # Create deeply nested directory structure
        nested_path = self.test_path / "l1" / "l2" / "l3" / "l4" / "l5"
        nested_path.mkdir(parents=True)
        
        # Create CLAUDE.md at root (4 levels up from l5)
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Detector starting from l5 should not find it (beyond 3 parent levels)
        detector = OrchestrationDetector(nested_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_get_claude_md_path_when_enabled(self):
        """Test getting path to CLAUDE.md when orchestration is enabled."""
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        path = detector.get_claude_md_path()
        self.assertEqual(path, claude_md)
    
    def test_get_claude_md_path_when_disabled(self):
        """Test getting path to CLAUDE.md when orchestration is disabled."""
        detector = OrchestrationDetector(self.test_path)
        path = detector.get_claude_md_path()
        self.assertIsNone(path)
    
    def test_permission_error_handling(self):
        """Test handling of permission errors when reading CLAUDE.md."""
        # Create CLAUDE.md
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            detector = OrchestrationDetector(self.test_path)
            self.assertFalse(detector.is_orchestration_enabled())
    
    def test_io_error_handling(self):
        """Test handling of IO errors when reading CLAUDE.md."""
        # Create CLAUDE.md  
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("Disk error")):
            detector = OrchestrationDetector(self.test_path)
            self.assertFalse(detector.is_orchestration_enabled())
    
    def test_claude_md_is_directory(self):
        """Test handling when CLAUDE.md is a directory instead of file."""
        # Create CLAUDE.md as a directory
        claude_md_dir = self.test_path / "CLAUDE.md"
        claude_md_dir.mkdir()
        
        detector = OrchestrationDetector(self.test_path)
        self.assertFalse(detector.is_orchestration_enabled())
    
    def test_flag_in_middle_of_file(self):
        """Test detection when flag is in the middle of the file."""
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("""
# Project Configuration

Some content before the flag.

CLAUDE_PM_ORCHESTRATION: ENABLED

Some content after the flag.
""")
        
        detector = OrchestrationDetector(self.test_path)
        self.assertTrue(detector.is_orchestration_enabled())
    
    def test_multiple_claude_md_files(self):
        """Test that nearest CLAUDE.md is used when multiple exist."""
        # Create nested structure
        nested_path = self.test_path / "level1" / "level2"
        nested_path.mkdir(parents=True)
        
        # Create CLAUDE.md at root without flag
        root_claude = self.test_path / "CLAUDE.md"
        root_claude.write_text("No orchestration flag here\n")
        
        # Create CLAUDE.md at level1 with flag
        level1_claude = self.test_path / "level1" / "CLAUDE.md"
        level1_claude.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        # Detector from level2 should find level1 first
        detector = OrchestrationDetector(nested_path)
        self.assertTrue(detector.is_orchestration_enabled())
        self.assertEqual(detector.get_claude_md_path(), level1_claude)
    
    @patch('claude_pm.orchestration.orchestration_detector.logger')
    def test_logging_enabled(self, mock_logger):
        """Test that appropriate log messages are generated when enabled."""
        claude_md = self.test_path / "CLAUDE.md"
        claude_md.write_text("CLAUDE_PM_ORCHESTRATION: ENABLED\n")
        
        detector = OrchestrationDetector(self.test_path)
        detector.is_orchestration_enabled()
        
        # Check that info log was called
        mock_logger.info.assert_called()
    
    @patch('claude_pm.orchestration.orchestration_detector.logger')
    def test_logging_disabled(self, mock_logger):
        """Test that appropriate log messages are generated when disabled."""
        detector = OrchestrationDetector(self.test_path)
        detector.is_orchestration_enabled()
        
        # Check that debug log was called
        mock_logger.debug.assert_called()


if __name__ == '__main__':
    unittest.main()