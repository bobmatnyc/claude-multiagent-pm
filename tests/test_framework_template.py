#!/usr/bin/env python3
"""
Unit tests for Framework Template Handlebars Variables
======================================================

Tests to ensure that framework/CLAUDE.md template maintains proper handlebars
variables and doesn't get corrupted with hardcoded values during deployments.
"""

import unittest
import re
from pathlib import Path


class TestFrameworkTemplate(unittest.TestCase):
    """Test framework template integrity and handlebars variables."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.framework_root = Path(__file__).parent
        self.framework_template_path = self.framework_root / "framework" / "CLAUDE.md"
        
        # Required handlebars variables that must be present
        self.required_handlebars = {
            "CLAUDE_MD_VERSION": "Version identifier for the CLAUDE.md file",
            "FRAMEWORK_VERSION": "Framework version number",
            "DEPLOYMENT_DATE": "Date when the template was deployed",
            "LAST_UPDATED": "Last update timestamp",
            "PLATFORM": "Operating system platform",
            "PYTHON_CMD": "Python command to use",
            "DEPLOYMENT_ID": "Unique deployment identifier"
        }
        
        # Hardcoded values that should NOT be present
        self.forbidden_hardcoded_patterns = [
            r"CLAUDE_MD_VERSION:\s*[\d\.-]+(?:\s|$)",  # e.g., "CLAUDE_MD_VERSION: 4.5.1-008"
            r"FRAMEWORK_VERSION:\s*[\d\.-]+(?:\s|$)",  # e.g., "FRAMEWORK_VERSION: 4.5.1"
            r"DEPLOYMENT_DATE:\s*\d{4}-\d{2}-\d{2}T",  # e.g., "DEPLOYMENT_DATE: 2025-07-11T..."
            r"LAST_UPDATED:\s*\d{4}-\d{2}-\d{2}T",     # e.g., "LAST_UPDATED: 2025-07-11T..."
            r"\*\*Version\*\*:\s*[\d\.-]+",             # e.g., "**Version**: 4.5.1"
            r"\*\*Deployment Date\*\*:\s*\d{4}-\d{2}-\d{2}T", # e.g., "**Deployment Date**: 2025-07-11T..."
            r"\*\*Platform\*\*:\s*[a-z]+(?:\s|$)",      # e.g., "**Platform**: darwin"
            r"\*\*Python Command\*\*:\s*python[0-9]*(?:\s|$)", # e.g., "**Python Command**: python3"
        ]
    
    def test_framework_template_exists(self):
        """Test that framework template file exists."""
        self.assertTrue(
            self.framework_template_path.exists(),
            f"Framework template not found at {self.framework_template_path}"
        )
    
    def test_required_handlebars_variables_present(self):
        """Test that all required handlebars variables are present in template."""
        content = self.framework_template_path.read_text()
        
        missing_variables = []
        for var_name, description in self.required_handlebars.items():
            # Check for handlebars format: {{VARIABLE_NAME}}
            if f"{{{{{var_name}}}}}" not in content:
                missing_variables.append(f"{var_name} ({description})")
        
        self.assertEqual(
            len(missing_variables), 0,
            f"Missing required handlebars variables in framework template:\n" +
            "\n".join(f"  - {var}" for var in missing_variables)
        )
    
    def test_no_hardcoded_values_in_template(self):
        """Test that template doesn't contain hardcoded values that should be handlebars."""
        content = self.framework_template_path.read_text()
        
        violations = []
        for pattern in self.forbidden_hardcoded_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                violations.extend([f"Pattern '{pattern}' found: {match}" for match in matches])
        
        self.assertEqual(
            len(violations), 0,
            f"Found hardcoded values that should be handlebars variables:\n" +
            "\n".join(f"  - {violation}" for violation in violations)
        )
    
    def test_handlebars_syntax_validity(self):
        """Test that handlebars variables use proper syntax."""
        content = self.framework_template_path.read_text()
        
        # Find all handlebars variables
        handlebars_pattern = r"\{\{([^}]+)\}\}"
        variables = re.findall(handlebars_pattern, content)
        
        invalid_variables = []
        for var in variables:
            # Check for valid variable name (uppercase, underscores, alphanumeric)
            if not re.match(r"^[A-Z][A-Z0-9_]*$", var):
                invalid_variables.append(var)
        
        self.assertEqual(
            len(invalid_variables), 0,
            f"Found invalid handlebars variable names (should be UPPERCASE_WITH_UNDERSCORES):\n" +
            "\n".join(f"  - {{{{{var}}}}}" for var in invalid_variables)
        )
    
    def test_framework_version_consistency(self):
        """Test that VERSION file and framework template are properly structured."""
        version_file = self.framework_root / "VERSION"
        
        # VERSION file should exist
        self.assertTrue(
            version_file.exists(),
            "VERSION file not found - required for framework version resolution"
        )
        
        # VERSION file should contain a valid version
        version_content = version_file.read_text().strip()
        self.assertRegex(
            version_content,
            r"^\d+\.\d+\.\d+$",
            f"VERSION file should contain semantic version (e.g., 0.4.6), found: {version_content}"
        )
        
        # Framework template should use handlebars for version
        template_content = self.framework_template_path.read_text()
        self.assertIn(
            "{{FRAMEWORK_VERSION}}",
            template_content,
            "Framework template should use {{FRAMEWORK_VERSION}} handlebars variable"
        )
    
    def test_deployment_variables_structure(self):
        """Test that deployment-related variables are properly structured."""
        content = self.framework_template_path.read_text()
        
        # Check that metadata section uses handlebars
        metadata_patterns = [
            r"CLAUDE_MD_VERSION:\s*\{\{CLAUDE_MD_VERSION\}\}",
            r"FRAMEWORK_VERSION:\s*\{\{FRAMEWORK_VERSION\}\}",
            r"DEPLOYMENT_DATE:\s*\{\{DEPLOYMENT_DATE\}\}",
        ]
        
        missing_patterns = []
        for pattern in metadata_patterns:
            if not re.search(pattern, content):
                missing_patterns.append(pattern)
        
        self.assertEqual(
            len(missing_patterns), 0,
            f"Missing required metadata handlebars patterns:\n" +
            "\n".join(f"  - {pattern}" for pattern in missing_patterns)
        )


def run_framework_template_tests():
    """Run framework template tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFrameworkTemplate)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Testing Framework Template Integrity...")
    print("=" * 60)
    
    success = run_framework_template_tests()
    
    if success:
        print("\n✅ All framework template tests passed!")
    else:
        print("\n❌ Framework template tests failed!")
        print("\nPlease fix the issues above to ensure template integrity.")
    
    exit(0 if success else 1)