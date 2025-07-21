#!/usr/bin/env python3
"""
Simple test script to verify wheel installation and contents.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_wheel_installation(wheel_path: str) -> bool:
    """Test installing the wheel and verify key functionality."""
    print(f"Testing wheel: {wheel_path}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a virtual environment
        venv_path = Path(tmpdir) / "test_venv"
        print(f"Creating virtual environment at {venv_path}")
        
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Failed to create venv: {result.stderr}")
            return False
        
        # Get the python executable in the venv
        venv_python = venv_path / "bin" / "python"
        if not venv_python.exists():
            venv_python = venv_path / "Scripts" / "python.exe"  # Windows
        
        # Install the wheel
        print(f"Installing wheel...")
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", wheel_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Failed to install wheel: {result.stderr}")
            return False
        
        # Test basic imports
        print("Testing imports...")
        test_script = """
import claude_pm
from claude_pm.cli import main
from claude_pm.core import ServiceManager
print(f"Claude PM version: {claude_pm.__version__}")

# Check if framework data exists using importlib.resources (Python 3.9+)
try:
    from importlib import resources
    # Check if the data directory exists
    data_path = resources.files('claude_pm') / 'data' / 'framework'
    if data_path.exists():
        print("✓ Framework data directory found")
        claude_md = data_path / 'CLAUDE.md'
        if claude_md.exists():
            print("✓ framework/CLAUDE.md found in package data")
            # Read first few lines to verify
            with claude_md.open('r') as f:
                lines = f.readlines()[:3]
                print(f"  First line: {lines[0].strip()}")
        else:
            print("✗ framework/CLAUDE.md NOT found in package data")
    else:
        print("✗ Framework data directory NOT found")
except Exception as e:
    print(f"Error accessing framework data: {e}")
"""
        
        result = subprocess.run(
            [str(venv_python), "-c", test_script],
            capture_output=True,
            text=True
        )
        
        print("Test output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        if result.returncode != 0:
            print("Import tests failed!")
            return False
        
        # Test CLI entry point
        print("\nTesting CLI entry point...")
        result = subprocess.run(
            [str(venv_python), "-m", "claude_pm.cli", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"CLI version: {result.stdout.strip()}")
        else:
            print(f"CLI test failed: {result.stderr}")
            return False
        
        print("\n✓ All tests passed!")
        return True


def main():
    """Main function."""
    if len(sys.argv) > 1:
        wheel_path = sys.argv[1]
    else:
        # Look for wheel in dist/
        wheel_files = list(Path("dist").glob("*.whl"))
        if not wheel_files:
            print("No wheel files found in dist/")
            return 1
        wheel_path = str(wheel_files[0])
    
    if test_wheel_installation(wheel_path):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())