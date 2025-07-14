#!/usr/bin/env python3
"""
Claude PM Framework Installation Script with Python Environment Validation

Comprehensive installation script that validates Python environment,
adjusts PATH ordering, and installs all requirements properly.

Author: Engineer Agent
Date: 2025-07-14
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging
import json
from datetime import datetime

def detect_best_python():
    """
    Detect the best Python executable for Claude PM Framework.
    Prioritizes system Python over Homebrew Python.
    
    Returns:
        Path to best Python executable or None if not found
    """
    import subprocess
    import shutil
    from pathlib import Path
    
    # Priority order: system Python first, then others
    python_candidates = [
        "/usr/bin/python3",
        "/System/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
        "/usr/local/bin/python3",  # Homebrew Intel Mac
        "/opt/homebrew/bin/python3",  # Homebrew Apple Silicon
        "python3",  # PATH lookup
        "python"   # Fallback
    ]
    
    for candidate in python_candidates:
        try:
            # For absolute paths, check if file exists
            if candidate.startswith("/"):
                if not Path(candidate).exists():
                    continue
                python_path = candidate
            else:
                # For relative names, use which
                python_path = shutil.which(candidate)
                if not python_path:
                    continue
            
            # Test the Python executable
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_str = result.stdout.strip()
                # Check minimum version (3.8+)
                if "Python 3." in version_str:
                    version_parts = version_str.replace("Python ", "").split(".")
                    if len(version_parts) >= 2:
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        if major == 3 and minor >= 8:
                            # Additional validation: test basic import
                            test_result = subprocess.run(
                                [python_path, "-c", "import sys, os, json"],
                                capture_output=True,
                                timeout=5
                            )
                            if test_result.returncode == 0:
                                return python_path
                                
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError, OSError):
            continue
    
    return None

def validate_python_environment(python_executable):
    """
    Validate that a Python environment meets Claude PM requirements.
    
    Args:
        python_executable: Path to Python executable
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import subprocess
    from pathlib import Path
    
    if not Path(python_executable).exists():
        return False, f"Python executable not found: {python_executable}"
    
    try:
        # Check version
        result = subprocess.run(
            [python_executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, f"Python version check failed: {result.stderr}"
        
        # Check required modules
        required_modules = ["subprocess", "pathlib", "json", "sys", "os"]
        for module in required_modules:
            test_result = subprocess.run(
                [python_executable, "-c", f"import {module}"],
                capture_output=True,
                timeout=5
            )
            if test_result.returncode != 0:
                return False, f"Required module '{module}' not available"
        
        # Check pip
        pip_result = subprocess.run(
            [python_executable, "-m", "pip", "--version"],
            capture_output=True,
            timeout=5
        )
        if pip_result.returncode != 0:
            return False, "pip not available with this Python installation"
        
        return True, "Python environment is valid"
        
    except subprocess.TimeoutExpired:
        return False, "Python validation timed out"
    except Exception as e:
        return False, f"Python validation error: {e}"

def adjust_path_for_system_python():
    """
    Adjust PATH to prioritize system Python over Homebrew Python.
    
    Returns:
        Adjusted PATH string
    """
    import os
    
    current_path = os.environ.get("PATH", "").split(os.pathsep)
    
    # Priority paths that should come first
    priority_paths = [
        "/usr/bin",
        "/bin",
        "/usr/sbin", 
        "/sbin"
    ]
    
    # Build new PATH with system paths first
    new_path = []
    
    # Add priority paths first
    for path in priority_paths:
        if path not in new_path and os.path.exists(path):
            new_path.append(path)
    
    # Add remaining paths (excluding Homebrew paths temporarily)
    homebrew_paths = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/local/bin"]
    for path in current_path:
        if path not in new_path and path not in homebrew_paths:
            new_path.append(path)
    
    # Add Homebrew paths at the end
    for path in homebrew_paths:
        if path not in new_path and os.path.exists(path):
            new_path.append(path)
    
    return os.pathsep.join(new_path)

def setup_logging():
    """Set up logging for installation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger("ClaudePMInstaller")

def install_requirements(python_executable, requirements_file):
    """Install Python requirements using the specified Python executable."""
    logger = logging.getLogger("ClaudePMInstaller")
    
    if not Path(requirements_file).exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    logger.info(f"Installing requirements using {python_executable}")
    
    try:
        # Try standard installation first
        result = subprocess.run([
            python_executable, "-m", "pip", "install", "--user", 
            "-r", requirements_file
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("Requirements installed successfully")
            return True
        
        # If standard installation fails, try with --break-system-packages
        if ("externally-managed-environment" in result.stderr or 
            "externally managed" in result.stderr):
            
            logger.info("Retrying with --break-system-packages")
            result = subprocess.run([
                python_executable, "-m", "pip", "install", "--user",
                "--break-system-packages", "-r", requirements_file
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Requirements installed successfully (with --break-system-packages)")
                return True
        
        logger.error(f"Requirements installation failed: {result.stderr}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error("Requirements installation timed out")
        return False
    except Exception as e:
        logger.error(f"Requirements installation error: {e}")
        return False

def create_path_adjustment_script():
    """Create a script to adjust PATH for proper Python prioritization."""
    adjusted_path = adjust_path_for_system_python()
    script_path = "/tmp/claude_pm_python_path.sh"
    
    script_content = f'''#!/bin/bash
# Claude PM Python PATH Adjustment Script
# Generated: {datetime.now().isoformat()}

echo "🐍 Adjusting PATH to prioritize system Python..."

# Export the optimized PATH
export PATH="{adjusted_path}"

echo "✅ PATH adjusted successfully"
echo "🔍 Current Python: $(which python3 2>/dev/null || which python 2>/dev/null || echo 'not found')"

# Verify Python version
if command -v python3 >/dev/null 2>&1; then
    echo "📋 Python version: $(python3 --version)"
else
    echo "⚠️  Warning: python3 not found in PATH"
fi

# To make this permanent, add the following to your ~/.bashrc or ~/.zshrc:
# export PATH="{adjusted_path}"
'''
    
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        return script_path
    except Exception as e:
        print(f"❌ Failed to create PATH adjustment script: {e}")
        return None

def save_installation_report(success, python_executable, messages, errors):
    """Save installation report for troubleshooting."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "python_executable": python_executable,
        "platform": {
            "system": os.uname().sysname if hasattr(os, 'uname') else 'unknown',
            "release": os.uname().release if hasattr(os, 'uname') else 'unknown',
            "machine": os.uname().machine if hasattr(os, 'uname') else 'unknown'
        },
        "path": {
            "original": os.environ.get("PATH", ""),
            "adjusted": adjust_path_for_system_python()
        },
        "messages": messages,
        "errors": errors
    }
    
    report_path = f"/tmp/claude_pm_installation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"📊 Installation report saved: {report_path}")
        return report_path
    except Exception as e:
        print(f"⚠️  Failed to save installation report: {e}")
        return None

def main():
    """Main installation function."""
    logger = setup_logging()
    messages = []
    errors = []
    
    print("🚀 Claude PM Framework Installation with Python Validation")
    print("=" * 60)
    
    # Adjust PATH for proper Python prioritization
    print("🐍 Adjusting PATH to prioritize system Python...")
    adjusted_path = adjust_path_for_system_python()
    os.environ["PATH"] = adjusted_path
    messages.append("PATH adjusted to prioritize system Python")
    
    # Create PATH adjustment script for user
    script_path = create_path_adjustment_script()
    if script_path:
        print(f"📝 PATH adjustment script created: {script_path}")
        print(f"💡 To apply: source {script_path}")
        messages.append(f"PATH script created: {script_path}")
    
    # Detect best Python environment
    print("🔍 Detecting best Python environment...")
    python_executable = detect_best_python()
    
    if not python_executable:
        error_msg = "No suitable Python environment found"
        print(f"❌ {error_msg}")
        print("🔧 Please install Python 3.8+ from python.org")
        errors.append(error_msg)
        save_installation_report(False, None, messages, errors)
        return False
    
    # Validate Python environment
    print(f"✅ Found Python: {python_executable}")
    is_valid, validation_message = validate_python_environment(python_executable)
    
    if not is_valid:
        error_msg = f"Python validation failed: {validation_message}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        save_installation_report(False, python_executable, messages, errors)
        return False
    
    print(f"✅ Python environment validated: {validation_message}")
    messages.append(f"Python validated: {python_executable}")
    
    # Determine framework path
    framework_path = Path(__file__).parent.parent
    
    # Install requirements
    requirements_file = framework_path / "requirements" / "base.txt"
    if requirements_file.exists():
        print("📦 Installing Python requirements...")
        if not install_requirements(python_executable, str(requirements_file)):
            error_msg = "Requirements installation failed"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
            save_installation_report(False, python_executable, messages, errors)
            return False
        print("✅ Requirements installed successfully")
        messages.append("Requirements installed")
    else:
        warning_msg = f"Requirements file not found: {requirements_file}"
        print(f"⚠️  {warning_msg}")
        messages.append(warning_msg)
    
    # Install Claude PM package
    print("📦 Installing Claude PM Python package...")
    
    try:
        result = subprocess.run([
            python_executable, "-m", "pip", "install", "--user", "-e", str(framework_path)
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Claude PM package installed successfully")
            messages.append("Claude PM package installed")
        else:
            # Try with --break-system-packages
            if ("externally-managed-environment" in result.stderr or 
                "externally managed" in result.stderr):
                
                print("🔄 Retrying package installation with --break-system-packages")
                result = subprocess.run([
                    python_executable, "-m", "pip", "install", "--user",
                    "--break-system-packages", "-e", str(framework_path)
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print("✅ Claude PM package installed successfully")
                    messages.append("Claude PM package installed (with --break-system-packages)")
                else:
                    error_msg = f"Package installation failed: {result.stderr}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    save_installation_report(False, python_executable, messages, errors)
                    return False
            else:
                error_msg = f"Package installation failed: {result.stderr}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                save_installation_report(False, python_executable, messages, errors)
                return False
    
    except Exception as e:
        error_msg = f"Package installation error: {e}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        save_installation_report(False, python_executable, messages, errors)
        return False
    
    # Test the installation
    print("🧪 Testing Claude PM installation...")
    try:
        test_result = subprocess.run([
            python_executable, "-c", 
            "import claude_pm; print('✅ Claude PM import successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if test_result.returncode == 0:
            print("✅ Claude PM import test passed")
            messages.append("Claude PM import test passed")
        else:
            warning_msg = f"Import test failed: {test_result.stderr}"
            print(f"⚠️  {warning_msg}")
            messages.append(warning_msg)
    except Exception as e:
        warning_msg = f"Import test error: {e}"
        print(f"⚠️  {warning_msg}")
        messages.append(warning_msg)
    
    print("\n🎉 Claude PM Framework installation completed successfully!")
    print("🚀 You can now use: claude-pm --help")
    print(f"🐍 Python executable: {python_executable}")
    
    if script_path:
        print(f"\n💡 To make PATH changes permanent, run:")
        print(f"   source {script_path}")
        print(f"   # Then add the PATH export to your ~/.bashrc or ~/.zshrc")
    
    # Save successful installation report
    save_installation_report(True, python_executable, messages, errors)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation error: {e}")
        sys.exit(1)