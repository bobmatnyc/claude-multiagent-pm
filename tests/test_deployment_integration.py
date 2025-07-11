#!/usr/bin/env python3

"""
Claude PM Framework - Deployment Integration Tests

Tests the complete deployment system including:
- Framework deployment
- AI-trackdown integration
- CLI wrapper functionality
- Health monitoring
- Configuration validation
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path


class TestDeploymentIntegration(unittest.TestCase):
    """Test suite for deployment integration"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="claude_pm_test_")
        self.framework_dir = Path(__file__).parent.parent
        self.deployment_script = self.framework_dir / "install" / "deploy.js"
        self.validation_script = self.framework_dir / "install" / "validate-deployment.js"

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_dry_run_deployment(self):
        """Test dry run deployment"""
        result = subprocess.run(
            [
                "node",
                str(self.deployment_script),
                "--target",
                self.test_dir,
                "--dry-run",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        self.assertEqual(result.returncode, 0, f"Dry run failed: {result.stderr}")
        self.assertIn("deployment completed successfully", result.stdout)
        self.assertIn("[DRY RUN]", result.stdout)

    def test_full_deployment(self):
        """Test complete deployment process"""
        result = subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        self.assertEqual(result.returncode, 0, f"Deployment failed: {result.stderr}")
        self.assertIn("deployment completed successfully", result.stdout)

        # Verify deployment structure
        self.assertTrue(Path(self.test_dir, "claude_pm").exists())
        self.assertTrue(Path(self.test_dir, "tasks").exists())
        self.assertTrue(Path(self.test_dir, "templates").exists())
        self.assertTrue(Path(self.test_dir, "schemas").exists())
        self.assertTrue(Path(self.test_dir, "bin").exists())
        self.assertTrue(Path(self.test_dir, ".claude-pm").exists())
        self.assertTrue(Path(self.test_dir, "CLAUDE.md").exists())

    def test_configuration_generation(self):
        """Test deployment configuration generation"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Check configuration file
        config_path = Path(self.test_dir, ".claude-pm", "config.json")
        self.assertTrue(config_path.exists())

        with open(config_path, "r") as f:
            config = json.load(f)

        # Verify required fields
        required_fields = ["version", "deployedAt", "platform", "deploymentDir"]
        for field in required_fields:
            self.assertIn(field, config)

        # Verify paths
        self.assertIn("paths", config)
        self.assertEqual(config["deploymentDir"], self.test_dir)
        self.assertEqual(config["paths"]["framework"], str(Path(self.test_dir, "claude_pm")))

    def test_cli_wrappers(self):
        """Test CLI wrapper creation"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Check CLI wrappers
        platform = sys.platform
        if platform == "win32":
            aitrackdown_path = Path(self.test_dir, "bin", "aitrackdown.bat")
            atd_path = Path(self.test_dir, "bin", "atd.bat")
        else:
            aitrackdown_path = Path(self.test_dir, "bin", "aitrackdown")
            atd_path = Path(self.test_dir, "bin", "atd")

        self.assertTrue(aitrackdown_path.exists())
        self.assertTrue(atd_path.exists())

        # Check executability (Unix only)
        if platform != "win32":
            self.assertTrue(os.access(aitrackdown_path, os.X_OK))
            self.assertTrue(os.access(atd_path, os.X_OK))

    def test_task_hierarchy(self):
        """Test task hierarchy initialization"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Check task hierarchy
        tasks_dir = Path(self.test_dir, "tasks")
        self.assertTrue(tasks_dir.exists())

        # Check subdirectories
        subdirs = ["epics", "issues", "tasks", "prs", "templates"]
        for subdir in subdirs:
            self.assertTrue(Path(tasks_dir, subdir).exists())

    def test_health_check_creation(self):
        """Test health check script creation"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Check health check script
        platform = sys.platform
        if platform == "win32":
            health_script = Path(self.test_dir, "scripts", "health-check.bat")
        else:
            health_script = Path(self.test_dir, "scripts", "health-check.sh")

        self.assertTrue(health_script.exists())

        # Check executability (Unix only)
        if platform != "win32":
            self.assertTrue(os.access(health_script, os.X_OK))

    def test_deployment_validation(self):
        """Test deployment validation"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Validate deployment
        result = subprocess.run(
            ["node", str(self.validation_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        self.assertEqual(result.returncode, 0, f"Validation failed: {result.stderr}")
        self.assertIn("validation completed successfully", result.stdout)

    def test_claude_config_generation(self):
        """Test CLAUDE.md generation"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Check CLAUDE.md
        claude_path = Path(self.test_dir, "CLAUDE.md")
        self.assertTrue(claude_path.exists())

        with open(claude_path, "r") as f:
            claude_content = f.read()

        # Verify required content
        self.assertIn("Claude PM Framework deployment", claude_content)
        self.assertIn(self.test_dir, claude_content)
        self.assertIn("ai-trackdown-tools", claude_content)
        self.assertIn("./bin/aitrackdown", claude_content)

    def test_platform_specific_features(self):
        """Test platform-specific features"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        platform = sys.platform

        # Check platform-specific CLI wrappers
        if platform == "win32":
            self.assertTrue(Path(self.test_dir, "bin", "aitrackdown.bat").exists())
            self.assertTrue(Path(self.test_dir, "scripts", "health-check.bat").exists())
        else:
            self.assertTrue(Path(self.test_dir, "bin", "aitrackdown").exists())
            self.assertTrue(Path(self.test_dir, "scripts", "health-check.sh").exists())

        # Check CLAUDE.md platform notes
        claude_path = Path(self.test_dir, "CLAUDE.md")
        with open(claude_path, "r") as f:
            claude_content = f.read()

        if platform == "win32":
            self.assertIn("Windows-specific", claude_content)
            self.assertIn(".bat", claude_content)
        elif platform == "darwin":
            self.assertIn("macOS-specific", claude_content)
            self.assertIn(".sh", claude_content)
        else:
            self.assertIn("Linux-specific", claude_content)
            self.assertIn(".sh", claude_content)

    def test_error_handling(self):
        """Test error handling in deployment"""
        # Test deployment to non-existent parent directory
        invalid_dir = "/nonexistent/path/deployment"

        result = subprocess.run(
            ["node", str(self.deployment_script), "--target", invalid_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Should still succeed as it creates parent directories
        self.assertEqual(result.returncode, 0)

    def test_validation_error_detection(self):
        """Test validation error detection"""
        # Deploy first
        subprocess.run(
            ["node", str(self.deployment_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        # Remove a required file
        os.remove(Path(self.test_dir, "CLAUDE.md"))

        # Validate deployment (should fail)
        result = subprocess.run(
            ["node", str(self.validation_script), "--target", self.test_dir, "--verbose"],
            capture_output=True,
            text=True,
            cwd=self.framework_dir,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR", result.stdout)


if __name__ == "__main__":
    # Change to the framework directory
    os.chdir(Path(__file__).parent.parent)

    # Run the tests
    unittest.main(verbosity=2)
