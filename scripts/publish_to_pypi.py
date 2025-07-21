#!/usr/bin/env python3
"""
PyPI Publication Script for Claude Multi-Agent PM Framework

This script handles the publication of the claude-multiagent-pm package to PyPI.
It includes safety checks, version validation, and automated publication steps.

Author: Claude Multi-Agent PM Team
Date: 2025-07-20
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import json
import toml
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from claude_pm._version import __version__
except ImportError:
    __version__ = "unknown"


class PyPIPublisher:
    """Handles PyPI publication for claude-multiagent-pm package."""
    
    def __init__(self, test_pypi: bool = True):
        """Initialize publisher with PyPI repository selection."""
        self.test_pypi = test_pypi
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for publication."""
        print("🔍 Checking prerequisites...")
        
        # Check if twine is installed
        try:
            subprocess.run(["twine", "--version"], check=True, capture_output=True)
            print("✅ twine is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ twine is not installed. Run: pip install twine")
            return False
        
        # Check if build is installed
        try:
            subprocess.run([sys.executable, "-m", "build", "--version"], 
                         check=True, capture_output=True)
            print("✅ build is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ build is not installed. Run: pip install build")
            return False
        
        # Check if dist directory exists and has recent builds
        if not self.dist_dir.exists():
            print("❌ No dist directory found. Run build first.")
            return False
        
        wheel_files = list(self.dist_dir.glob("*.whl"))
        tar_files = list(self.dist_dir.glob("*.tar.gz"))
        
        if not wheel_files or not tar_files:
            print("❌ No distribution files found in dist/")
            return False
        
        print(f"✅ Found {len(wheel_files)} wheel file(s) and {len(tar_files)} source distribution(s)")
        
        # Check for PyPI credentials
        if self.test_pypi:
            if not os.environ.get("TWINE_TEST_TOKEN") and not os.path.exists(os.path.expanduser("~/.pypirc")):
                print("⚠️  No Test PyPI credentials found. Set TWINE_TEST_TOKEN or configure ~/.pypirc")
                print("   Get your token from: https://test.pypi.org/manage/account/token/")
        else:
            if not os.environ.get("TWINE_TOKEN") and not os.path.exists(os.path.expanduser("~/.pypirc")):
                print("⚠️  No PyPI credentials found. Set TWINE_TOKEN or configure ~/.pypirc")
                print("   Get your token from: https://pypi.org/manage/account/token/")
        
        return True
    
    def get_package_version(self) -> str:
        """Get the current package version from pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        return data['project']['version']
    
    def clean_dist(self):
        """Clean the dist directory of old builds."""
        print("🧹 Cleaning dist directory...")
        if self.dist_dir.exists():
            for file in self.dist_dir.iterdir():
                if file.suffix in ['.whl', '.tar.gz']:
                    file.unlink()
                    print(f"   Removed: {file.name}")
    
    def build_package(self) -> bool:
        """Build the package distributions."""
        print("🔨 Building package distributions...")
        
        try:
            subprocess.run(
                [sys.executable, "-m", "build"],
                cwd=self.project_root,
                check=True
            )
            print("✅ Package built successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            return False
    
    def check_package(self) -> bool:
        """Check the package with twine check."""
        print("🔍 Checking package integrity...")
        
        try:
            subprocess.run(
                ["twine", "check", "dist/*"],
                cwd=self.project_root,
                check=True
            )
            print("✅ Package check passed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Package check failed: {e}")
            return False
    
    def upload_package(self, skip_existing: bool = True) -> bool:
        """Upload the package to PyPI."""
        repository = "testpypi" if self.test_pypi else "pypi"
        print(f"📤 Uploading to {repository}...")
        
        cmd = ["twine", "upload"]
        
        if self.test_pypi:
            cmd.extend(["--repository", "testpypi"])
        
        if skip_existing:
            cmd.append("--skip-existing")
        
        # Use environment variable for token if available
        env = os.environ.copy()
        if self.test_pypi and "TWINE_TEST_TOKEN" in os.environ:
            env["TWINE_USERNAME"] = "__token__"
            env["TWINE_PASSWORD"] = os.environ["TWINE_TEST_TOKEN"]
        elif not self.test_pypi and "TWINE_TOKEN" in os.environ:
            env["TWINE_USERNAME"] = "__token__"
            env["TWINE_PASSWORD"] = os.environ["TWINE_TOKEN"]
        
        cmd.append("dist/*")
        
        try:
            subprocess.run(cmd, cwd=self.project_root, env=env, check=True)
            print(f"✅ Successfully uploaded to {repository}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def publish(self, clean: bool = True, build: bool = True, 
                check: bool = True, skip_existing: bool = True) -> bool:
        """Run the full publication process."""
        version = self.get_package_version()
        repository = "Test PyPI" if self.test_pypi else "PyPI"
        
        print(f"""
🚀 Publishing claude-multiagent-pm v{version} to {repository}
{'='*60}
        """)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Clean if requested
        if clean:
            self.clean_dist()
        
        # Build if requested
        if build:
            if not self.build_package():
                return False
        
        # Check package
        if check:
            if not self.check_package():
                return False
        
        # Upload
        if not self.upload_package(skip_existing=skip_existing):
            return False
        
        # Print success message with URLs
        if self.test_pypi:
            url = f"https://test.pypi.org/project/claude-multiagent-pm/{version}/"
            install_cmd = f"pip install -i https://test.pypi.org/simple/ claude-multiagent-pm=={version}"
        else:
            url = f"https://pypi.org/project/claude-multiagent-pm/{version}/"
            install_cmd = f"pip install claude-multiagent-pm=={version}"
        
        print(f"""
🎉 Publication successful!
{'='*60}
📦 Package: claude-multiagent-pm v{version}
🔗 URL: {url}
📥 Install: {install_cmd}
        """)
        
        return True


def main():
    """Main entry point for the publication script."""
    parser = argparse.ArgumentParser(
        description="Publish claude-multiagent-pm to PyPI"
    )
    parser.add_argument(
        "--production", 
        action="store_true",
        help="Publish to production PyPI (default is Test PyPI)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean dist directory before building"
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Don't build package (use existing dist files)"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Skip twine check validation"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Don't skip existing versions (will fail if version exists)"
    )
    
    args = parser.parse_args()
    
    # Create publisher
    publisher = PyPIPublisher(test_pypi=not args.production)
    
    # Run publication
    success = publisher.publish(
        clean=not args.no_clean,
        build=not args.no_build,
        check=not args.no_check,
        skip_existing=not args.no_skip_existing
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()