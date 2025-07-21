#!/usr/bin/env python3
"""
Ensure ai-trackdown-pytools is available and properly configured.

This script checks if the 'ai-trackdown-pytools' Python package is installed,
and provides instructions for installation if not available.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path


def is_module_available(module_name):
    """Check if a Python module is available."""
    try:
        import importlib
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def run_command(cmd, capture_output=True, shell=False):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def get_ai_trackdown_version():
    """Get installed ai-trackdown-pytools version."""
    try:
        import ai_trackdown
        return getattr(ai_trackdown, '__version__', 'unknown')
    except ImportError:
        return None


def check_ai_trackdown_functionality():
    """Check if ai-trackdown-pytools is functional."""
    try:
        # Test basic import
        import ai_trackdown
        from ai_trackdown.models import Task, Issue, Epic
        
        # Test basic functionality
        test_task = Task(
            id="TSK-TEST-001",
            title="Test Task",
            description="Testing ai-trackdown functionality",
            status="open",
            priority="medium"
        )
        
        return True, "ai-trackdown-pytools is fully functional"
    except Exception as e:
        return False, f"ai-trackdown-pytools error: {str(e)}"


def install_ai_trackdown():
    """Install ai-trackdown-pytools package."""
    try:
        # Try to install using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "ai-trackdown-pytools==1.1.0"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, "ai-trackdown-pytools installed successfully"
        else:
            # Try with --break-system-packages for externally managed environments
            if "externally-managed-environment" in result.stderr:
                result2 = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "ai-trackdown-pytools==1.1.0"],
                    capture_output=True,
                    text=True
                )
                if result2.returncode == 0:
                    return True, "ai-trackdown-pytools installed successfully (with --break-system-packages)"
            
            return False, f"Failed to install: {result.stderr}"
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def get_installation_instructions():
    """Generate installation instructions for ai-trackdown-pytools."""
    return """
To install ai-trackdown-pytools:

1. Using pip (recommended):
   pip install --user ai-trackdown-pytools==1.1.0

2. If you encounter "externally-managed-environment" error:
   pip install --user --break-system-packages ai-trackdown-pytools==1.1.0

3. For system-wide installation (requires sudo):
   sudo pip install ai-trackdown-pytools==1.1.0

4. Using virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install ai-trackdown-pytools==1.1.0

After installation, verify with:
   python -c "import ai_trackdown; print('ai-trackdown-pytools is ready!')"
"""


def ensure_ai_trackdown_pytools():
    """Main function to ensure ai-trackdown-pytools is available."""
    status = {
        'success': False,
        'message': '',
        'actions': [],
        'platform': platform.system(),
        'already_available': False,
        'version': None
    }
    
    # Check if ai-trackdown-pytools is already available
    if is_module_available('ai_trackdown'):
        version = get_ai_trackdown_version()
        functional, func_msg = check_ai_trackdown_functionality()
        
        status['success'] = functional
        status['already_available'] = True
        status['version'] = version
        status['message'] = func_msg
        
        if functional:
            status['actions'].append(f"ai-trackdown-pytools version {version} is installed and functional")
        else:
            status['actions'].append("ai-trackdown-pytools is installed but has issues")
            status['actions'].append("Try reinstalling: pip install --user --force-reinstall ai-trackdown-pytools==1.1.0")
        
        return status
    
    # ai-trackdown-pytools is not installed
    status['message'] = 'ai-trackdown-pytools is not installed'
    
    # Try to install it
    print("\nAttempting to install ai-trackdown-pytools...")
    success, install_msg = install_ai_trackdown()
    
    if success:
        # Verify installation
        if is_module_available('ai_trackdown'):
            version = get_ai_trackdown_version()
            functional, func_msg = check_ai_trackdown_functionality()
            
            status['success'] = functional
            status['version'] = version
            status['message'] = install_msg
            status['actions'].append(f"Installed ai-trackdown-pytools version {version}")
            
            if functional:
                status['actions'].append("ai-trackdown-pytools is ready to use!")
            else:
                status['actions'].append("Installation succeeded but functionality check failed")
                status['actions'].append(func_msg)
        else:
            status['message'] = "Installation appeared to succeed but module not found"
            status['actions'].append("Try manual installation:")
            status['actions'].append(get_installation_instructions())
    else:
        status['message'] = install_msg
        status['actions'].append("Automatic installation failed. Manual installation required:")
        status['actions'].append(get_installation_instructions())
    
    return status


def main():
    """Main entry point."""
    print("Ensuring ai-trackdown-pytools is available...")
    
    result = ensure_ai_trackdown_pytools()
    
    # Print results
    print(f"\nPlatform: {result['platform']}")
    print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"Message: {result['message']}")
    
    if result['version']:
        print(f"Version: {result['version']}")
    
    if result['actions']:
        print("\nDetails:")
        for action in result['actions']:
            # Handle multi-line actions (like instructions)
            if '\n' in str(action):
                print(action)
            else:
                print(f"  - {action}")
    
    # Return appropriate exit code
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())