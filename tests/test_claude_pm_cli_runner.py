#!/usr/bin/env python3
"""
Test Runner for claude-pm CLI Tests
==================================

Specialized test runner for CLI tests that integrates with the project's
testing infrastructure and provides specific CLI test configurations.
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


class CLITestRunner:
    """Test runner for claude-pm CLI tests."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the test runner."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.cli_tests = ["test_claude_pm_cli.py", "test_claude_pm_cli_integration.py"]

    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if all prerequisites are available."""
        checks = {}

        # Check Node.js availability
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=5
            )
            checks["nodejs"] = result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            checks["nodejs"] = False

        # Check claude-pm CLI availability
        cli_path = Path("/Users/masa/.local/bin/claude-pm")
        checks["claude_pm_cli"] = cli_path.exists()

        # Check npm availability (needed for some tests)
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
            checks["npm"] = result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            checks["npm"] = False

        # Check pytest availability
        try:
            import pytest

            checks["pytest"] = True
        except ImportError:
            checks["pytest"] = False

        return checks

    def run_unit_tests(self, verbose: bool = False) -> int:
        """Run unit tests only."""
        args = [
            "-m",
            "pytest",
            str(self.test_dir / "test_claude_pm_cli.py"),
            "-m",
            "unit",
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def run_integration_tests(self, verbose: bool = False) -> int:
        """Run integration tests only."""
        args = [
            "-m",
            "pytest",
            str(self.test_dir / "test_claude_pm_cli_integration.py"),
            "-m",
            "integration",
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def run_all_cli_tests(self, verbose: bool = False) -> int:
        """Run all CLI tests."""
        args = [
            "-m",
            "pytest",
            str(self.test_dir / "test_claude_pm_cli.py"),
            str(self.test_dir / "test_claude_pm_cli_integration.py"),
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def run_with_coverage(self, verbose: bool = False) -> int:
        """Run CLI tests with coverage reporting."""
        args = [
            "-m",
            "pytest",
            str(self.test_dir / "test_claude_pm_cli.py"),
            str(self.test_dir / "test_claude_pm_cli_integration.py"),
            "--cov=claude_pm",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def run_quick_tests(self) -> int:
        """Run quick tests (unit tests only, no integration)."""
        args = [
            "-m",
            "pytest",
            str(self.test_dir / "test_claude_pm_cli.py"),
            "-m",
            "unit",
            "-x",  # Stop on first failure
            "--tb=short",
        ]

        return subprocess.run([sys.executable] + args).returncode

    def run_specific_test(self, test_name: str, verbose: bool = False) -> int:
        """Run a specific test by name."""
        args = [
            "-m",
            "pytest",
            "-k",
            test_name,
            str(self.test_dir / "test_claude_pm_cli.py"),
            str(self.test_dir / "test_claude_pm_cli_integration.py"),
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def run_test_class(self, class_name: str, verbose: bool = False) -> int:
        """Run a specific test class."""
        args = [
            "-m",
            "pytest",
            "-k",
            class_name,
            str(self.test_dir / "test_claude_pm_cli.py"),
            str(self.test_dir / "test_claude_pm_cli_integration.py"),
            "--tb=short",
        ]

        if verbose:
            args.append("-v")

        return subprocess.run([sys.executable] + args).returncode

    def print_prerequisites_report(self):
        """Print a report of prerequisites status."""
        print("CLI Test Prerequisites Report")
        print("=" * 40)

        checks = self.check_prerequisites()

        for name, available in checks.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"{name.ljust(15)}: {status}")

        print("\nRecommendations:")

        if not checks.get("nodejs", False):
            print("- Install Node.js from https://nodejs.org/")

        if not checks.get("npm", False):
            print("- Install npm (usually comes with Node.js)")

        if not checks.get("claude_pm_cli", False):
            print("- Install claude-pm CLI at /Users/masa/.local/bin/claude-pm")

        if not checks.get("pytest", False):
            print("- Install pytest: pip install pytest")

        print("\nTest Categories:")
        print("- Unit tests: Don't require external dependencies")
        print("- Integration tests: Require Node.js and claude-pm CLI")

        # Determine what can be run
        can_run_unit = checks.get("pytest", False)
        can_run_integration = all(
            [
                checks.get("pytest", False),
                checks.get("nodejs", False),
                checks.get("claude_pm_cli", False),
            ]
        )

        print(f"\nCan run unit tests: {'✅ Yes' if can_run_unit else '❌ No'}")
        print(f"Can run integration tests: {'✅ Yes' if can_run_integration else '❌ No'}")

    def print_test_summary(self):
        """Print a summary of available tests."""
        print("CLI Test Summary")
        print("=" * 40)

        test_categories = {
            "Unit Tests": [
                "TestCLIBackupCommands",
                "TestCLISetupCommands",
                "TestCLIScanAnalyzeCommands",
                "TestCLIRestoreResolveCommands",
                "TestCLIGlobalOptions",
                "TestCLILegacySupport",
            ],
            "Integration Tests": [
                "TestCLIHelpAndVersion",
                "TestCLIBackupIntegration",
                "TestCLISetupIntegration",
                "TestCLIScanAnalyzeIntegration",
                "TestCLIRestoreIntegration",
                "TestCLIWorkflowIntegration",
                "TestCLIPerformanceIntegration",
            ],
        }

        for category, test_classes in test_categories.items():
            print(f"\n{category}:")
            for test_class in test_classes:
                print(f"  - {test_class}")

        print("\nTest Commands:")
        print("  python -m tests.test_claude_pm_cli_runner unit      # Run unit tests")
        print("  python -m tests.test_claude_pm_cli_runner integration # Run integration tests")
        print("  python -m tests.test_claude_pm_cli_runner all       # Run all tests")
        print("  python -m tests.test_claude_pm_cli_runner quick     # Run quick tests")
        print("  python -m tests.test_claude_pm_cli_runner coverage  # Run with coverage")


def main():
    """Main entry point for the test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test runner for claude-pm CLI tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        choices=["unit", "integration", "all", "quick", "coverage", "prerequisites", "summary"],
        help="Test command to run",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument("-k", "--keyword", help="Run tests matching keyword")

    parser.add_argument("--class", dest="test_class", help="Run specific test class")

    args = parser.parse_args()

    runner = CLITestRunner()

    if args.command == "prerequisites":
        runner.print_prerequisites_report()
        return 0

    if args.command == "summary":
        runner.print_test_summary()
        return 0

    # Check prerequisites before running tests
    checks = runner.check_prerequisites()

    if args.command in ["integration", "all"] and not checks.get("nodejs", False):
        print("⚠️  Warning: Node.js not available. Integration tests may fail.")
        print("Run 'python -m tests.test_claude_pm_cli_runner prerequisites' for details.")
        print()

    if args.keyword:
        return runner.run_specific_test(args.keyword, args.verbose)

    if args.test_class:
        return runner.run_test_class(args.test_class, args.verbose)

    # Run the specified command
    if args.command == "unit":
        return runner.run_unit_tests(args.verbose)
    elif args.command == "integration":
        return runner.run_integration_tests(args.verbose)
    elif args.command == "all":
        return runner.run_all_cli_tests(args.verbose)
    elif args.command == "quick":
        return runner.run_quick_tests()
    elif args.command == "coverage":
        return runner.run_with_coverage(args.verbose)

    return 1


if __name__ == "__main__":
    sys.exit(main())
