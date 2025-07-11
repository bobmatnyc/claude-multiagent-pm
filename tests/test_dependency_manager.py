"""
Test suite for DependencyManager service.

Tests for CMPM-103: Dependency Management Strategy
"""

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import subprocess
from datetime import datetime

import pytest

from claude_pm.services.dependency_manager import (
    DependencyManager,
    DependencyType,
    InstallationMethod,
    DependencyInfo,
    InstallationResult,
    DependencyReport,
)


class TestDependencyManager(unittest.TestCase):
    """Test cases for DependencyManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {"check_interval": 60, "auto_install": False, "installation_timeout": 30}
        self.dependency_manager = DependencyManager(self.config)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test dependency manager initialization."""
        self.assertEqual(self.dependency_manager.name, "dependency_manager")
        self.assertEqual(self.dependency_manager.check_interval, 60)
        self.assertEqual(self.dependency_manager.auto_install, False)
        self.assertEqual(self.dependency_manager.installation_timeout, 30)
        self.assertIsInstance(self.dependency_manager._dependencies, dict)
        self.assertIsInstance(self.dependency_manager._installation_cache, dict)

    def test_core_dependencies_defined(self):
        """Test that core dependencies are properly defined."""
        self.assertIn("ai-trackdown-tools", self.dependency_manager.CORE_DEPENDENCIES)
        self.assertIn("python", self.dependency_manager.CORE_DEPENDENCIES)
        self.assertIn("node", self.dependency_manager.CORE_DEPENDENCIES)
        self.assertIn("npm", self.dependency_manager.CORE_DEPENDENCIES)
        self.assertIn("git", self.dependency_manager.CORE_DEPENDENCIES)

        # Check ai-trackdown-tools configuration
        ai_trackdown_config = self.dependency_manager.CORE_DEPENDENCIES["ai-trackdown-tools"]
        self.assertEqual(ai_trackdown_config["type"], DependencyType.AI_TRACKDOWN_TOOLS)
        self.assertEqual(ai_trackdown_config["npm_package"], "@bobmatnyc/ai-trackdown-tools")
        self.assertTrue(ai_trackdown_config["critical"])
        self.assertIn("aitrackdown", ai_trackdown_config["commands"])
        self.assertIn("atd", ai_trackdown_config["commands"])

    def test_dependency_info_creation(self):
        """Test DependencyInfo dataclass creation."""
        info = DependencyInfo(
            name="test-package",
            type=DependencyType.PYTHON_PACKAGE,
            version="1.0.0",
            is_installed=True,
            installation_method=InstallationMethod.PIP,
        )

        self.assertEqual(info.name, "test-package")
        self.assertEqual(info.type, DependencyType.PYTHON_PACKAGE)
        self.assertEqual(info.version, "1.0.0")
        self.assertTrue(info.is_installed)
        self.assertEqual(info.installation_method, InstallationMethod.PIP)

    def test_installation_result_creation(self):
        """Test InstallationResult dataclass creation."""
        result = InstallationResult(
            success=True,
            dependency_name="test-package",
            method=InstallationMethod.PIP,
            version="1.0.0",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.dependency_name, "test-package")
        self.assertEqual(result.method, InstallationMethod.PIP)
        self.assertEqual(result.version, "1.0.0")

    def test_dependency_report_creation(self):
        """Test DependencyReport dataclass creation."""
        dependencies = {
            "test-package": DependencyInfo(
                name="test-package", type=DependencyType.PYTHON_PACKAGE, is_installed=True
            )
        }

        report = DependencyReport(
            deployment_type="test",
            platform="darwin",
            timestamp=datetime.now().isoformat(),
            dependencies=dependencies,
            missing_dependencies=[],
            outdated_dependencies=[],
            installation_recommendations=[],
            health_score=100,
        )

        self.assertEqual(report.deployment_type, "test")
        self.assertEqual(report.platform, "darwin")
        self.assertEqual(len(report.dependencies), 1)
        self.assertEqual(report.health_score, 100)

    @patch("claude_pm.services.dependency_manager.subprocess.run")
    def test_detect_python_command(self, mock_run):
        """Test Python command detection."""
        # Mock successful python3 detection
        mock_run.return_value = Mock(returncode=0)

        python_cmd = self.dependency_manager._detect_python_command()
        self.assertEqual(python_cmd, "python3")

        # Mock python3 failure, python success
        mock_run.side_effect = [
            Mock(returncode=1),  # python3 fails
            Mock(returncode=0),  # python succeeds
        ]

        python_cmd = self.dependency_manager._detect_python_command()
        self.assertEqual(python_cmd, "python")  # Returns python when it succeeds

    def test_select_best_installation_method(self):
        """Test installation method selection."""
        # Test ai-trackdown-tools
        method = self.dependency_manager._select_best_installation_method(
            DependencyType.AI_TRACKDOWN_TOOLS, {}
        )
        self.assertEqual(method, InstallationMethod.NPM_GLOBAL)

        # Test Python package
        method = self.dependency_manager._select_best_installation_method(
            DependencyType.PYTHON_PACKAGE, {}
        )
        self.assertEqual(method, InstallationMethod.PIP)

        # Test NPM global
        method = self.dependency_manager._select_best_installation_method(
            DependencyType.NPM_GLOBAL, {}
        )
        self.assertEqual(method, InstallationMethod.NPM_GLOBAL)

        # Test system binary
        method = self.dependency_manager._select_best_installation_method(
            DependencyType.SYSTEM_BINARY, {}
        )
        self.assertEqual(method, InstallationMethod.SYSTEM)

    def test_parse_version_from_output(self):
        """Test version parsing from command output."""
        # Test various version formats
        test_cases = [
            ("Python 3.9.7", "3.9.7"),
            ("v1.2.3", "1.2.3"),
            ("version 2.1.0", "2.1.0"),
            ("1.0.0", "1.0.0"),
            ("Node.js v16.14.0", "16.14.0"),
            ("git version 2.32.1", "2.32.1"),
            ("npm 8.5.0", "8.5.0"),
            ("no version info", "unknown"),
        ]

        for output, expected in test_cases:
            result = self.dependency_manager._parse_version_from_output(output)
            self.assertEqual(result, expected, f"Failed for output: {output}")

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_command_available(self, mock_run_command):
        """Test command availability checking."""
        # Mock successful command check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_command_available("python3")
        self.assertTrue(result)

        # Mock failed command check
        mock_run_command.return_value = Mock(returncode=1)

        result = await self.dependency_manager._check_command_available("nonexistent")
        self.assertFalse(result)

        # Mock exception
        mock_run_command.side_effect = Exception("Command failed")

        result = await self.dependency_manager._check_command_available("error")
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_python_available(self, mock_run_command):
        """Test Python availability check."""
        # Mock successful Python check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_python_available()
        self.assertTrue(result)

        # Mock failed Python check
        mock_run_command.return_value = Mock(returncode=1)

        result = await self.dependency_manager._check_python_available()
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_node_available(self, mock_run_command):
        """Test Node.js availability check."""
        # Mock successful Node check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_node_available()
        self.assertTrue(result)

        # Mock failed Node check
        mock_run_command.return_value = Mock(returncode=1)

        result = await self.dependency_manager._check_node_available()
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_npm_available(self, mock_run_command):
        """Test npm availability check."""
        # Mock successful npm check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_npm_available()
        self.assertTrue(result)

        # Mock failed npm check
        mock_run_command.return_value = Mock(returncode=1)

        result = await self.dependency_manager._check_npm_available()
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_git_available(self, mock_run_command):
        """Test Git availability check."""
        # Mock successful Git check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_git_available()
        self.assertTrue(result)

        # Mock failed Git check
        mock_run_command.return_value = Mock(returncode=1)

        result = await self.dependency_manager._check_git_available()
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_ai_trackdown_tools_available(self, mock_run_command):
        """Test ai-trackdown-tools availability check."""
        # Mock successful aitrackdown check
        mock_run_command.return_value = Mock(returncode=0)

        result = await self.dependency_manager._check_ai_trackdown_tools_available()
        self.assertTrue(result)

        # Mock aitrackdown fail, atd success
        mock_run_command.side_effect = [
            Mock(returncode=1),  # aitrackdown fails
            Mock(returncode=0),  # atd succeeds
        ]

        result = await self.dependency_manager._check_ai_trackdown_tools_available()
        self.assertTrue(result)

        # Mock both fail
        mock_run_command.side_effect = [
            Mock(returncode=1),  # aitrackdown fails
            Mock(returncode=1),  # atd fails
        ]

        result = await self.dependency_manager._check_ai_trackdown_tools_available()
        self.assertFalse(result)

    @patch("claude_pm.services.dependency_manager.DependencyManager._check_command_available")
    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_ai_trackdown_tools_dependency(self, mock_run_command, mock_check_cmd):
        """Test ai-trackdown-tools dependency checking."""
        config = self.dependency_manager.CORE_DEPENDENCIES["ai-trackdown-tools"]

        # Mock command available
        mock_check_cmd.return_value = True
        mock_run_command.return_value = Mock(returncode=0, stdout="1.1.1")

        dependency_info = DependencyInfo(
            name="ai-trackdown-tools",
            type=DependencyType.AI_TRACKDOWN_TOOLS,
            required_version=">=1.1.0",
            last_checked=datetime.now().isoformat(),
        )

        await self.dependency_manager._check_ai_trackdown_tools(dependency_info, config)

        self.assertTrue(dependency_info.is_installed)
        self.assertEqual(dependency_info.installation_method, InstallationMethod.NPM_GLOBAL)
        self.assertEqual(dependency_info.version, "1.1.1")

    @patch("claude_pm.services.dependency_manager.DependencyManager._check_command_available")
    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_system_binary_dependency(self, mock_run_command, mock_check_cmd):
        """Test system binary dependency checking."""
        config = self.dependency_manager.CORE_DEPENDENCIES["python"]

        # Mock command available
        mock_check_cmd.return_value = True
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout="Python 3.9.7"),  # version check
            Mock(returncode=0, stdout="/usr/bin/python3"),  # which command
        ]

        dependency_info = DependencyInfo(
            name="python",
            type=DependencyType.SYSTEM_BINARY,
            required_version=">=3.8.0",
            last_checked=datetime.now().isoformat(),
        )

        await self.dependency_manager._check_system_binary(dependency_info, config)

        self.assertTrue(dependency_info.is_installed)
        self.assertEqual(dependency_info.installation_method, InstallationMethod.SYSTEM)
        self.assertEqual(dependency_info.version, "3.9.7")
        self.assertEqual(dependency_info.installation_path, "/usr/bin/python3")

    @patch("claude_pm.services.dependency_manager.importlib.import_module")
    async def test_check_python_package_dependency(self, mock_import):
        """Test Python package dependency checking."""
        # Mock successful import
        mock_module = Mock()
        mock_module.__version__ = "2.5.0"
        mock_import.return_value = mock_module

        config = {
            "type": DependencyType.PYTHON_PACKAGE,
            "package_name": "pydantic",
            "required_version": ">=2.0.0",
        }

        dependency_info = DependencyInfo(
            name="pydantic",
            type=DependencyType.PYTHON_PACKAGE,
            required_version=">=2.0.0",
            last_checked=datetime.now().isoformat(),
        )

        await self.dependency_manager._check_python_package(dependency_info, config)

        self.assertTrue(dependency_info.is_installed)
        self.assertEqual(dependency_info.installation_method, InstallationMethod.PIP)
        self.assertEqual(dependency_info.version, "2.5.0")

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_check_npm_global_dependency(self, mock_run_command):
        """Test npm global dependency checking."""
        # Mock successful npm list
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout="npm-package@1.0.0"),  # npm list
            Mock(returncode=0, stdout="npm-package@1.0.0"),  # npm list with depth
        ]

        config = {
            "type": DependencyType.NPM_GLOBAL,
            "package_name": "npm-package",
            "required_version": ">=1.0.0",
        }

        dependency_info = DependencyInfo(
            name="npm-package",
            type=DependencyType.NPM_GLOBAL,
            required_version=">=1.0.0",
            last_checked=datetime.now().isoformat(),
        )

        await self.dependency_manager._check_npm_global(dependency_info, config)

        self.assertTrue(dependency_info.is_installed)
        self.assertEqual(dependency_info.installation_method, InstallationMethod.NPM_GLOBAL)
        self.assertEqual(dependency_info.version, "1.0.0")

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_install_ai_trackdown_tools(self, mock_run_command):
        """Test ai-trackdown-tools installation."""
        config = self.dependency_manager.CORE_DEPENDENCIES["ai-trackdown-tools"]

        # Mock successful installation
        mock_run_command.return_value = Mock(
            returncode=0, stdout="+ @bobmatnyc/ai-trackdown-tools@1.1.1", stderr=""
        )

        result = await self.dependency_manager._install_ai_trackdown_tools(
            "ai-trackdown-tools", config, InstallationMethod.NPM_GLOBAL
        )

        self.assertTrue(result.success)
        self.assertEqual(result.dependency_name, "ai-trackdown-tools")
        self.assertEqual(result.method, InstallationMethod.NPM_GLOBAL)
        self.assertIsNotNone(result.logs)

        # Verify command was called correctly
        mock_run_command.assert_called_once_with(
            ["npm", "install", "-g", "@bobmatnyc/ai-trackdown-tools"],
            timeout=self.dependency_manager.installation_timeout,
        )

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_install_python_package(self, mock_run_command):
        """Test Python package installation."""
        config = {
            "type": DependencyType.PYTHON_PACKAGE,
            "package_name": "pydantic",
            "required_version": ">=2.0.0",
        }

        # Mock successful installation
        mock_run_command.return_value = Mock(
            returncode=0, stdout="Successfully installed pydantic-2.5.0", stderr=""
        )

        result = await self.dependency_manager._install_python_package(
            "pydantic", config, InstallationMethod.PIP
        )

        self.assertTrue(result.success)
        self.assertEqual(result.dependency_name, "pydantic")
        self.assertEqual(result.method, InstallationMethod.PIP)
        self.assertIsNotNone(result.logs)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_install_npm_global(self, mock_run_command):
        """Test npm global package installation."""
        config = {"type": DependencyType.NPM_GLOBAL, "package_name": "test-package"}

        # Mock successful installation
        mock_run_command.return_value = Mock(returncode=0, stdout="+ test-package@1.0.0", stderr="")

        result = await self.dependency_manager._install_npm_global(
            "test-package", config, InstallationMethod.NPM_GLOBAL
        )

        self.assertTrue(result.success)
        self.assertEqual(result.dependency_name, "test-package")
        self.assertEqual(result.method, InstallationMethod.NPM_GLOBAL)
        self.assertIsNotNone(result.logs)

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_install_npm_local(self, mock_run_command):
        """Test npm local package installation."""
        config = {"type": DependencyType.NPM_LOCAL, "package_name": "test-package"}

        # Mock successful installation
        mock_run_command.return_value = Mock(returncode=0, stdout="+ test-package@1.0.0", stderr="")

        result = await self.dependency_manager._install_npm_local(
            "test-package", config, InstallationMethod.NPM_LOCAL
        )

        self.assertTrue(result.success)
        self.assertEqual(result.dependency_name, "test-package")
        self.assertEqual(result.method, InstallationMethod.NPM_LOCAL)
        self.assertIsNotNone(result.logs)

    def test_install_system_binary(self):
        """Test system binary installation (should fail)."""
        config = {"type": DependencyType.SYSTEM_BINARY}

        # This should return failure since system binaries require manual installation
        result = asyncio.run(
            self.dependency_manager._install_system_binary(
                "test-binary", config, InstallationMethod.SYSTEM
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.dependency_name, "test-binary")
        self.assertEqual(result.method, InstallationMethod.SYSTEM)
        self.assertIn("manual installation", result.error_message)

    async def test_install_unknown_dependency(self):
        """Test installing unknown dependency."""
        result = await self.dependency_manager.install_dependency("unknown-package")

        self.assertFalse(result.success)
        self.assertEqual(result.dependency_name, "unknown-package")
        self.assertIn("Unknown dependency", result.error_message)

    @patch(
        "claude_pm.services.dependency_manager.DependencyManager._check_ai_trackdown_tools_available"
    )
    @patch("claude_pm.services.dependency_manager.DependencyManager._check_command_available")
    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_verify_ai_trackdown_tools(self, mock_run_command, mock_check_cmd, mock_check_ai):
        """Test ai-trackdown-tools verification."""
        # Mock successful verification
        mock_check_cmd.return_value = True
        mock_run_command.return_value = Mock(returncode=0, stdout="1.1.1")

        result = await self.dependency_manager.verify_ai_trackdown_tools()
        self.assertTrue(result)

        # Mock failed verification
        mock_check_cmd.return_value = False

        result = await self.dependency_manager.verify_ai_trackdown_tools()
        self.assertFalse(result)

    def test_get_dependencies(self):
        """Test getting all dependencies."""
        # Add test dependency
        test_dep = DependencyInfo(
            name="test-dep", type=DependencyType.PYTHON_PACKAGE, is_installed=True
        )
        self.dependency_manager._dependencies["test-dep"] = test_dep

        dependencies = self.dependency_manager.get_dependencies()
        self.assertIn("test-dep", dependencies)
        self.assertEqual(dependencies["test-dep"].name, "test-dep")

        # Verify it's a copy
        self.assertIsNot(dependencies, self.dependency_manager._dependencies)

    def test_get_dependency(self):
        """Test getting specific dependency."""
        # Add test dependency
        test_dep = DependencyInfo(
            name="test-dep", type=DependencyType.PYTHON_PACKAGE, is_installed=True
        )
        self.dependency_manager._dependencies["test-dep"] = test_dep

        dependency = self.dependency_manager.get_dependency("test-dep")
        self.assertIsNotNone(dependency)
        self.assertEqual(dependency.name, "test-dep")

        # Test non-existent dependency
        dependency = self.dependency_manager.get_dependency("non-existent")
        self.assertIsNone(dependency)

    def test_get_installation_result(self):
        """Test getting installation result."""
        # Add test installation result
        test_result = InstallationResult(
            success=True, dependency_name="test-dep", method=InstallationMethod.PIP
        )
        self.dependency_manager._installation_cache["test-dep"] = test_result

        result = self.dependency_manager.get_installation_result("test-dep")
        self.assertIsNotNone(result)
        self.assertEqual(result.dependency_name, "test-dep")

        # Test non-existent result
        result = self.dependency_manager.get_installation_result("non-existent")
        self.assertIsNone(result)

    async def test_generate_dependency_report(self):
        """Test dependency report generation."""
        # Add test dependencies
        installed_dep = DependencyInfo(
            name="installed-dep", type=DependencyType.PYTHON_PACKAGE, is_installed=True
        )
        missing_dep = DependencyInfo(
            name="missing-dep", type=DependencyType.PYTHON_PACKAGE, is_installed=False
        )

        self.dependency_manager._dependencies["installed-dep"] = installed_dep
        self.dependency_manager._dependencies["missing-dep"] = missing_dep

        # Mock deployment config
        self.dependency_manager.deployment_config = {"config": {"deploymentType": "test"}}

        report = await self.dependency_manager.generate_dependency_report()

        self.assertEqual(report.deployment_type, "test")
        self.assertEqual(len(report.dependencies), 2)
        self.assertIn("missing-dep", report.missing_dependencies)
        self.assertNotIn("installed-dep", report.missing_dependencies)
        self.assertEqual(report.health_score, 50)  # 1 out of 2 installed
        self.assertGreater(len(report.installation_recommendations), 0)

    async def test_get_installation_recommendations(self):
        """Test getting installation recommendations."""
        # Add test dependencies
        critical_missing = DependencyInfo(
            name="critical-missing", type=DependencyType.PYTHON_PACKAGE, is_installed=False
        )
        optional_missing = DependencyInfo(
            name="optional-missing", type=DependencyType.PYTHON_PACKAGE, is_installed=False
        )

        self.dependency_manager._dependencies["critical-missing"] = critical_missing
        self.dependency_manager._dependencies["optional-missing"] = optional_missing

        # Mock core dependencies
        self.dependency_manager.CORE_DEPENDENCIES["critical-missing"] = {"critical": True}
        self.dependency_manager.CORE_DEPENDENCIES["optional-missing"] = {"critical": False}

        recommendations = await self.dependency_manager.get_installation_recommendations()

        self.assertEqual(len(recommendations), 2)
        self.assertTrue(any("CRITICAL" in rec for rec in recommendations))
        self.assertTrue(any("critical-missing" in rec for rec in recommendations))
        self.assertTrue(any("optional-missing" in rec for rec in recommendations))


class TestDependencyManagerIntegration(unittest.TestCase):
    """Integration tests for DependencyManager."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.dependency_manager = DependencyManager()

    @patch(
        "claude_pm.services.dependency_manager.DependencyManager._initialize_deployment_integration"
    )
    async def test_service_lifecycle(self, mock_init_deployment):
        """Test complete service lifecycle."""
        # Mock deployment integration
        mock_init_deployment.return_value = None
        self.dependency_manager.deployment_config = {
            "config": {"deploymentType": "test", "frameworkPath": "/tmp/test"}
        }

        # Test initialization
        with patch.object(self.dependency_manager, "_check_all_dependencies"):
            await self.dependency_manager._initialize()

        # Test health check
        with patch.object(self.dependency_manager, "_check_python_available", return_value=True):
            with patch.object(self.dependency_manager, "_check_node_available", return_value=True):
                with patch.object(
                    self.dependency_manager, "_check_npm_available", return_value=True
                ):
                    with patch.object(
                        self.dependency_manager, "_check_git_available", return_value=True
                    ):
                        with patch.object(
                            self.dependency_manager,
                            "_check_ai_trackdown_tools_available",
                            return_value=True,
                        ):
                            with patch.object(
                                self.dependency_manager,
                                "_check_critical_dependencies",
                                return_value=True,
                            ):
                                health = await self.dependency_manager._health_check()
                                self.assertTrue(health["python_available"])
                                self.assertTrue(health["node_available"])
                                self.assertTrue(health["npm_available"])
                                self.assertTrue(health["git_available"])
                                self.assertTrue(health["ai_trackdown_tools_available"])
                                self.assertTrue(health["critical_dependencies_met"])

        # Test cleanup
        with patch.object(self.dependency_manager, "_save_dependency_state"):
            await self.dependency_manager._cleanup()

    @patch("claude_pm.services.dependency_manager.DependencyManager._run_command")
    async def test_full_dependency_check_cycle(self, mock_run_command):
        """Test full dependency checking cycle."""
        # Mock all commands as available
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout="1.1.1"),  # aitrackdown version
            Mock(returncode=0, stdout="Python 3.9.7"),  # python version
            Mock(returncode=0, stdout="/usr/bin/python3"),  # which python
            Mock(returncode=0, stdout="v16.14.0"),  # node version
            Mock(returncode=0, stdout="/usr/bin/node"),  # which node
            Mock(returncode=0, stdout="8.5.0"),  # npm version
            Mock(returncode=0, stdout="/usr/bin/npm"),  # which npm
            Mock(returncode=0, stdout="git version 2.32.1"),  # git version
            Mock(returncode=0, stdout="/usr/bin/git"),  # which git
        ]

        # Mock command availability checks
        with patch.object(self.dependency_manager, "_check_command_available", return_value=True):
            await self.dependency_manager._check_all_dependencies()

        # Verify all dependencies are tracked
        self.assertIn("ai-trackdown-tools", self.dependency_manager._dependencies)
        self.assertIn("python", self.dependency_manager._dependencies)
        self.assertIn("node", self.dependency_manager._dependencies)
        self.assertIn("npm", self.dependency_manager._dependencies)
        self.assertIn("git", self.dependency_manager._dependencies)

        # Verify installation status
        for dep_name, dep_info in self.dependency_manager._dependencies.items():
            if dep_name in self.dependency_manager.CORE_DEPENDENCIES:
                self.assertTrue(dep_info.is_installed, f"Expected {dep_name} to be installed")
                self.assertIsNotNone(dep_info.version, f"Expected version for {dep_name}")


if __name__ == "__main__":
    unittest.main()
