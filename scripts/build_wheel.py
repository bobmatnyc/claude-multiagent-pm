#!/usr/bin/env python3
"""
Build script for creating Python wheels for claude-multiagent-pm.

This script automates the wheel building process and includes validation
to ensure all necessary files are included in the distribution.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime


def log(message: str, level: str = "INFO") -> None:
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_command(cmd: list, cwd: str = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr


def clean_build_dirs() -> None:
    """Clean existing build directories."""
    dirs_to_clean = ["build", "dist", "*.egg-info", "claude_pm.egg-info"]
    for dir_pattern in dirs_to_clean:
        for path in Path(".").glob(dir_pattern):
            if path.is_dir():
                log(f"Removing {path}")
                shutil.rmtree(path)


def check_prerequisites() -> bool:
    """Check if required tools are installed."""
    required_tools = ["python3"]
    
    for tool in required_tools:
        ret_code, _, _ = run_command(["which", tool])
        if ret_code != 0:
            log(f"Required tool '{tool}' not found", "ERROR")
            return False
    
    # Check for build package
    ret_code, _, _ = run_command([sys.executable, "-m", "pip", "show", "build"])
    if ret_code != 0:
        log("Installing 'build' package...", "INFO")
        ret_code, _, _ = run_command([sys.executable, "-m", "pip", "install", "build"])
        if ret_code != 0:
            log("Failed to install 'build' package", "ERROR")
            return False
    
    return True


def validate_wheel_contents(wheel_path: str) -> bool:
    """Validate that the wheel contains all necessary files."""
    required_files = [
        "claude_pm/__init__.py",
        "claude_pm/cli.py",
        "claude_pm-1.2.3.dist-info/METADATA",
        "claude_pm-1.2.3.dist-info/entry_points.txt",
    ]
    
    required_patterns = [
        "claude_pm/data/framework/CLAUDE.md",
        "claude_pm/agents/",
        "claude_pm/services/",
        "claude_pm/orchestration/",
    ]
    
    log(f"Validating wheel contents: {wheel_path}")
    
    with zipfile.ZipFile(wheel_path, 'r') as whl:
        file_list = whl.namelist()
        
        # Check required files
        for req_file in required_files:
            if req_file not in file_list:
                log(f"Missing required file: {req_file}", "ERROR")
                return False
        
        # Check required patterns
        for pattern in required_patterns:
            if not any(pattern in f for f in file_list):
                log(f"Missing files matching pattern: {pattern}", "ERROR")
                return False
        
        # Check for framework/CLAUDE.md specifically
        framework_claude_found = any("claude_pm/data/framework/CLAUDE.md" in f for f in file_list)
        if not framework_claude_found:
            log("Critical file claude_pm/data/framework/CLAUDE.md not found in wheel!", "ERROR")
            return False
        
        # Log some statistics
        md_files = [f for f in file_list if f.endswith('.md')]
        py_files = [f for f in file_list if f.endswith('.py')]
        log(f"Wheel contains {len(file_list)} files total")
        log(f"  - {len(py_files)} Python files")
        log(f"  - {len(md_files)} Markdown files")
        
    return True


def build_wheel() -> bool:
    """Build the wheel using python -m build."""
    log("Building wheel...")
    
    # Use python -m build for modern wheel building
    ret_code, stdout, stderr = run_command([sys.executable, "-m", "build", "--wheel"])
    
    if ret_code != 0:
        log("Build failed!", "ERROR")
        log(f"stdout: {stdout}")
        log(f"stderr: {stderr}")
        return False
    
    log("Build completed successfully")
    
    # Find the built wheel
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        log("No wheel file found in dist/", "ERROR")
        return False
    
    wheel_path = wheel_files[0]
    log(f"Built wheel: {wheel_path}")
    
    # Validate wheel contents
    if not validate_wheel_contents(str(wheel_path)):
        log("Wheel validation failed!", "ERROR")
        return False
    
    log("Wheel validation passed", "SUCCESS")
    return True


def test_wheel_installation(wheel_path: str) -> bool:
    """Test installing the wheel in a temporary environment."""
    log("Testing wheel installation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a virtual environment
        venv_path = Path(tmpdir) / "venv"
        ret_code, _, _ = run_command([sys.executable, "-m", "venv", str(venv_path)])
        if ret_code != 0:
            log("Failed to create virtual environment", "ERROR")
            return False
        
        # Get the python executable in the venv
        venv_python = venv_path / "bin" / "python"
        if not venv_python.exists():
            venv_python = venv_path / "Scripts" / "python.exe"  # Windows
        
        # Install the wheel
        ret_code, stdout, stderr = run_command([
            str(venv_python), "-m", "pip", "install", wheel_path
        ])
        
        if ret_code != 0:
            log("Failed to install wheel", "ERROR")
            log(f"stderr: {stderr}")
            return False
        
        # Test imports
        test_imports = [
            "import claude_pm",
            "from claude_pm.cli import main",
            "from claude_pm.core import ServiceManager",
        ]
        
        for test_import in test_imports:
            ret_code, _, stderr = run_command([
                str(venv_python), "-c", test_import
            ])
            if ret_code != 0:
                log(f"Import test failed: {test_import}", "ERROR")
                log(f"stderr: {stderr}")
                return False
        
        # Test CLI entry points
        ret_code, stdout, _ = run_command([
            str(venv_python), "-m", "claude_pm.cli", "--version"
        ])
        if ret_code != 0:
            log("CLI entry point test failed", "ERROR")
            return False
        
        log(f"CLI version output: {stdout.strip()}")
        
    log("Installation test passed", "SUCCESS")
    return True


def main():
    """Main build process."""
    log("Starting claude-multiagent-pm wheel build process")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    log(f"Working directory: {os.getcwd()}")
    
    # Check prerequisites
    if not check_prerequisites():
        log("Prerequisites check failed", "ERROR")
        return 1
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the wheel
    if not build_wheel():
        log("Build process failed", "ERROR")
        return 1
    
    # Find the built wheel
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        log("No wheel file found after build", "ERROR")
        return 1
    
    wheel_path = str(wheel_files[0])
    
    # Test the wheel
    if not test_wheel_installation(wheel_path):
        log("Wheel installation test failed", "ERROR")
        return 1
    
    log(f"Build successful! Wheel available at: {wheel_path}", "SUCCESS")
    log(f"To install: pip install {wheel_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())