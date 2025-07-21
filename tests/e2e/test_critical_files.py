#!/usr/bin/env python3
"""
Unit tests to verify critical files exist and have correct content.

This test suite ensures that essential framework files are present and valid,
preventing accidental deletion or corruption during cleanup operations.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCriticalFiles(unittest.TestCase):
    """Test suite for verifying critical framework files."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.claude_md_path = self.project_root / "CLAUDE.md"
    
    def test_claude_md_exists(self):
        """Test that CLAUDE.md exists in the project root."""
        self.assertTrue(
            self.claude_md_path.exists(),
            f"CRITICAL: CLAUDE.md not found at {self.claude_md_path}\n"
            "This file contains critical framework protection rules and must not be deleted!"
        )
    
    def test_claude_md_not_empty(self):
        """Test that CLAUDE.md is not empty."""
        self.assertTrue(
            self.claude_md_path.exists(),
            f"CLAUDE.md not found at {self.claude_md_path}"
        )
        
        file_size = self.claude_md_path.stat().st_size
        self.assertGreater(
            file_size, 1024,  # At least 1KB
            f"CLAUDE.md appears to be corrupted or empty (size: {file_size} bytes). "
            "Expected size > 1KB for a valid framework rules file."
        )
    
    def test_claude_md_contains_critical_phrase(self):
        """Test that CLAUDE.md contains the expected critical phrase."""
        self.assertTrue(
            self.claude_md_path.exists(),
            f"CLAUDE.md not found at {self.claude_md_path}"
        )
        
        content = self.claude_md_path.read_text(encoding='utf-8')
        critical_phrase = "Claude Multi-Agent PM Project Development Rules"
        
        self.assertIn(
            critical_phrase,
            content,
            f"CLAUDE.md is missing the critical phrase: '{critical_phrase}'\n"
            "This indicates the file may be corrupted or replaced with incorrect content."
        )
    
    def test_claude_md_has_expected_sections(self):
        """Test that CLAUDE.md contains expected key sections."""
        self.assertTrue(
            self.claude_md_path.exists(),
            f"CLAUDE.md not found at {self.claude_md_path}"
        )
        
        content = self.claude_md_path.read_text(encoding='utf-8')
        
        # Key sections that should exist
        expected_sections = [
            "CRITICAL FRAMEWORK PROTECTION RULES",
            "ABSOLUTE PROHIBITIONS",
            "FRAMEWORK TEMPLATE PROTECTION SYSTEM",
            "DEVELOPMENT WORKFLOW RULES",
            "CRITICAL FILE LOCATIONS"
        ]
        
        missing_sections = []
        for section in expected_sections:
            if section not in content:
                missing_sections.append(section)
        
        self.assertEqual(
            len(missing_sections), 0,
            f"CLAUDE.md is missing critical sections: {', '.join(missing_sections)}\n"
            "This indicates the file structure may be corrupted."
        )
    
    def test_claude_md_framework_protection_warnings(self):
        """Test that CLAUDE.md contains framework protection warnings."""
        self.assertTrue(
            self.claude_md_path.exists(),
            f"CLAUDE.md not found at {self.claude_md_path}"
        )
        
        content = self.claude_md_path.read_text(encoding='utf-8')
        
        # Critical warnings that must be present
        critical_warnings = [
            "NEVER DELETE OR MODIFY `framework/CLAUDE.md`",
            "This file is ESSENTIAL to framework operation",
            "Deletion of this file will break ALL framework deployments"
        ]
        
        missing_warnings = []
        for warning in critical_warnings:
            if warning not in content:
                missing_warnings.append(warning)
        
        self.assertEqual(
            len(missing_warnings), 0,
            f"CLAUDE.md is missing critical protection warnings: {', '.join(missing_warnings)}\n"
            "These warnings are essential for preventing accidental deletion."
        )
    
    def test_version_file_exists(self):
        """Test that VERSION file exists (another critical file)."""
        version_path = self.project_root / "VERSION"
        self.assertTrue(
            version_path.exists(),
            f"VERSION file not found at {version_path}\n"
            "This file is critical for version management and must not be deleted!"
        )
    
    def test_framework_claude_md_exists(self):
        """Test that framework/CLAUDE.md exists (the master template)."""
        framework_claude_md = self.project_root / "framework" / "CLAUDE.md"
        self.assertTrue(
            framework_claude_md.exists(),
            f"framework/CLAUDE.md not found at {framework_claude_md}\n"
            "This is the master template for ALL framework deployments and MUST NOT be deleted!"
        )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)