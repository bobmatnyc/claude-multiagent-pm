#!/usr/bin/env python3
"""
Test PyPI Installation Script for Claude Multi-Agent PM Framework

This script tests installation from Test PyPI to ensure the package works correctly
before publishing to production PyPI.

Author: Claude Multi-Agent PM Team
Date: 2025-07-20
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import argparse
import venv
from typing import Optional, List, Tuple


class TestPyPIValidator:
    """Validates package installation from Test PyPI."""
    
    def __init__(self, version: Optional[str] = None):
        """Initialize validator with optional version specification."""
        self.version = version
        self.test_dir = None
        self.venv_path = None
        
    def create_test_environment(self) -> Path:
        """Create a clean test environment."""
        print("🔧 Creating test environment...")
        
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="claude_pm_test_")
        print(f"   Created test directory: {self.test_dir}")
        
        # Create virtual environment
        self.venv_path = Path(self.test_dir) / "venv"
        venv.create(self.venv_path, with_pip=True)
        print(f"   Created virtual environment: {self.venv_path}")
        
        return Path(self.test_dir)
    
    def get_pip_command(self) -> List[str]:
        """Get the pip command for the virtual environment."""
        if sys.platform == "win32":
            return [str(self.venv_path / "Scripts" / "python"), "-m", "pip"]
        else:
            return [str(self.venv_path / "bin" / "python"), "-m", "pip"]
    
    def get_python_command(self) -> List[str]:
        """Get the python command for the virtual environment."""
        if sys.platform == "win32":
            return [str(self.venv_path / "Scripts" / "python")]
        else:
            return [str(self.venv_path / "bin" / "python")]
    
    def install_from_test_pypi(self) -> bool:
        """Install the package from Test PyPI."""
        print("\n📦 Installing from Test PyPI...")
        
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip first
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        
        # Build install command
        install_cmd = pip_cmd + [
            "install",
            "--index-url", "https://test.pypi.org/simple/",
            "--extra-index-url", "https://pypi.org/simple/"  # For dependencies
        ]
        
        if self.version:
            install_cmd.append(f"claude-multiagent-pm=={self.version}")
        else:
            install_cmd.append("claude-multiagent-pm")
        
        try:
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Package installed successfully")
                return True
            else:
                print("❌ Installation failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False
    
    def test_import(self) -> bool:
        """Test that the package can be imported."""
        print("\n🔍 Testing package import...")
        
        python_cmd = self.get_python_command()
        
        test_code = """
import claude_pm
print(f"✅ Successfully imported claude_pm")
print(f"   Version: {claude_pm.__version__}")

# Test core imports
from claude_pm.core import BaseService, ServiceManager
print("✅ Core imports successful")

# Test service imports
from claude_pm.services import (
    AgentRegistry,
    ParentDirectoryManager,
    HealthMonitor
)
print("✅ Service imports successful")

# Test orchestration imports
from claude_pm.orchestration import BackwardsCompatibleOrchestrator
print("✅ Orchestration imports successful")
"""
        
        try:
            result = subprocess.run(
                python_cmd + ["-c", test_code],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print("❌ Import test failed")
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Import test error: {e}")
            return False
    
    def test_cli_commands(self) -> bool:
        """Test CLI commands."""
        print("\n🔍 Testing CLI commands...")
        
        # Get the claude-pm command path
        if sys.platform == "win32":
            cli_cmd = str(self.venv_path / "Scripts" / "claude-pm")
        else:
            cli_cmd = str(self.venv_path / "bin" / "claude-pm")
        
        tests = [
            (["--version"], "Version check"),
            (["--help"], "Help command"),
            (["init", "--help"], "Init help"),
        ]
        
        all_passed = True
        
        for args, description in tests:
            print(f"\n   Testing: {description}")
            try:
                result = subprocess.run(
                    [cli_cmd] + args,
                    capture_output=True,
                    text=True,
                    cwd=self.test_dir
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {description} passed")
                    if "--version" in args:
                        print(f"      Output: {result.stdout.strip()}")
                else:
                    print(f"   ❌ {description} failed")
                    print(f"      Error: {result.stderr}")
                    all_passed = False
                    
            except FileNotFoundError:
                print(f"   ❌ CLI command not found: {cli_cmd}")
                all_passed = False
            except Exception as e:
                print(f"   ❌ Error testing {description}: {e}")
                all_passed = False
        
        return all_passed
    
    def test_basic_functionality(self) -> bool:
        """Test basic framework functionality."""
        print("\n🔍 Testing basic functionality...")
        
        python_cmd = self.get_python_command()
        
        # Test service initialization
        test_code = """
import asyncio
from claude_pm.core import ServiceManager
from claude_pm.services import HealthMonitor

async def test_services():
    # Initialize service manager
    manager = ServiceManager()
    print("✅ ServiceManager initialized")
    
    # Test health monitor
    health = HealthMonitor()
    await health.initialize()
    print("✅ HealthMonitor initialized")
    
    # Check system health
    health_status = await health.check_system_health()
    print(f"✅ System health check completed: {health_status['overall_status']}")
    
    return True

# Run the test
result = asyncio.run(test_services())
print(f"\\n✅ All functionality tests passed")
"""
        
        try:
            result = subprocess.run(
                python_cmd + ["-c", test_code],
                capture_output=True,
                text=True,
                cwd=self.test_dir
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print("❌ Functionality test failed")
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Functionality test error: {e}")
            return False
    
    def cleanup(self):
        """Clean up test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            print("\n🧹 Cleaning up test environment...")
            try:
                shutil.rmtree(self.test_dir)
                print("✅ Test environment cleaned up")
            except Exception as e:
                print(f"⚠️  Could not clean up test directory: {e}")
    
    def run_validation(self) -> bool:
        """Run complete validation suite."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║           Test PyPI Installation Validation                   ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        if self.version:
            print(f"Testing version: {self.version}")
        else:
            print("Testing latest version")
        
        try:
            # Create test environment
            self.create_test_environment()
            
            # Run tests
            tests = [
                ("Installation", self.install_from_test_pypi),
                ("Import Test", self.test_import),
                ("CLI Commands", self.test_cli_commands),
                ("Basic Functionality", self.test_basic_functionality),
            ]
            
            results = {}
            for test_name, test_func in tests:
                print(f"\n{'='*60}")
                results[test_name] = test_func()
            
            # Summary
            print(f"\n{'='*60}")
            print("SUMMARY")
            print(f"{'='*60}")
            
            passed = sum(1 for v in results.values() if v)
            total = len(results)
            
            for test_name, result in results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{test_name}: {status}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n🎉 All tests passed! Package is ready for production.")
                print("\nTo publish to production PyPI:")
                print("  python scripts/publish_to_pypi.py --production")
                return True
            else:
                print("\n❌ Some tests failed. Please fix issues before publishing.")
                return False
                
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test claude-multiagent-pm installation from Test PyPI"
    )
    parser.add_argument(
        "--version",
        help="Specific version to test (default: latest)"
    )
    parser.add_argument(
        "--keep-env",
        action="store_true",
        help="Don't clean up test environment after testing"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = TestPyPIValidator(version=args.version)
    
    # Run validation
    try:
        success = validator.run_validation()
        if args.keep_env:
            print(f"\nTest environment kept at: {validator.test_dir}")
            validator.test_dir = None  # Prevent cleanup
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()