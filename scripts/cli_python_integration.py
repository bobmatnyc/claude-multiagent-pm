#!/usr/bin/env python3
"""
CLI Python Integration for Claude PM Framework

Integrates Python environment management into the claude-pm CLI scripts
to ensure proper Python version detection and PATH ordering.

Author: Engineer Agent
Date: 2025-07-14
Memory Collection: Tracks CLI integration issues and user feedback
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Import our Python Environment Manager
try:
    from python_environment_manager import PythonEnvironmentManager, PythonEnvironment
except ImportError:
    # If running from a different location, try to import from the same directory
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    from python_environment_manager import PythonEnvironmentManager, PythonEnvironment


class CLIPythonIntegration:
    """
    Integrates Python environment management into Claude PM CLI scripts.
    
    Features:
    - Automatic Python detection and validation
    - PATH adjustment for CLI execution
    - Python environment error handling
    - CLI script modification for better Python support
    - Memory collection for CLI issues
    """
    
    def __init__(self, framework_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """Initialize CLI Python Integration."""
        self.framework_path = Path(framework_path) if framework_path else Path(__file__).parent.parent
        self.logger = logger or self._setup_logger()
        self.python_manager = PythonEnvironmentManager(logger)
        self.memory_collection = []
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for CLI Python Integration."""
        logger = logging.getLogger("CLIPythonIntegration")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def collect_memory(self, category: str, priority: str, content: str, 
                      metadata: Optional[Dict] = None) -> None:
        """Collect memory for CLI integration issues and feedback."""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "priority": priority,
            "content": content,
            "metadata": metadata or {},
            "source_agent": "Engineer",
            "project_context": "cli_python_integration",
            "resolution_status": "open"
        }
        self.memory_collection.append(memory_entry)
        self.logger.info(f"Memory collected: {category} - {priority} - {content[:50]}...")
    
    def detect_and_validate_python_for_cli(self) -> Tuple[Optional[str], List[str]]:
        """
        Detect and validate the best Python executable for CLI usage.
        
        Returns:
            Tuple of (python_executable_path, list_of_validation_messages)
        """
        messages = []
        
        # Get the best Python environment
        best_env = self.python_manager.get_best_python_environment()
        
        if not best_env:
            messages.append("❌ No suitable Python environment found")
            self.collect_memory(
                "error:integration", "critical",
                "No suitable Python environment found for CLI"
            )
            return None, messages
        
        # Validate the environment
        is_valid, issues = self.python_manager.validate_python_environment(best_env.executable)
        
        if not is_valid:
            messages.append(f"❌ Best Python environment has issues:")
            for issue in issues:
                messages.append(f"   - {issue}")
            self.collect_memory(
                "error:integration", "high",
                f"Python environment validation failed: {'; '.join(issues)}"
            )
            return None, messages
        
        messages.append(f"✅ Valid Python environment: {best_env.executable}")
        messages.append(f"   Version: {best_env.version}")
        messages.append(f"   Type: {'System' if best_env.is_system else 'Homebrew' if best_env.is_homebrew else 'Other'}")
        
        return best_env.executable, messages
    
    def generate_python_shebang_line(self, python_executable: Optional[str] = None) -> str:
        """
        Generate an appropriate shebang line for Python scripts.
        
        Args:
            python_executable: Optional specific Python executable to use
            
        Returns:
            Shebang line string
        """
        if python_executable is None:
            python_executable, _ = self.detect_and_validate_python_for_cli()
        
        if python_executable and Path(python_executable).exists():
            return f"#!{python_executable}"
        else:
            # Fallback to env-based detection
            return "#!/usr/bin/env python3"
    
    def create_python_detector_function(self) -> str:
        """
        Create a Python detection function that can be embedded in CLI scripts.
        
        Returns:
            Python code as string for embedding in CLI scripts
        """
        return '''
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
'''
    
    def create_enhanced_cli_script(self, original_script_path: str, 
                                 output_path: Optional[str] = None) -> str:
        """
        Create an enhanced version of a CLI script with Python environment management.
        
        Args:
            original_script_path: Path to the original CLI script
            output_path: Optional custom output path for enhanced script
            
        Returns:
            Path to the enhanced CLI script
        """
        original_path = Path(original_script_path)
        
        if not original_path.exists():
            raise FileNotFoundError(f"Original CLI script not found: {original_script_path}")
        
        if output_path is None:
            output_path = str(original_path.parent / f"{original_path.stem}_enhanced{original_path.suffix}")
        
        # Read original script
        try:
            with open(original_path, 'r') as f:
                original_content = f.read()
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Failed to read original CLI script {original_script_path}: {e}"
            )
            raise
        
        # Generate enhanced script content
        best_python, _ = self.detect_and_validate_python_for_cli()
        shebang_line = self.generate_python_shebang_line(best_python)
        detector_functions = self.create_python_detector_function()
        
        enhanced_content = f'''{shebang_line}
"""
Enhanced Claude PM CLI Script with Python Environment Management

This script includes automatic Python environment detection and PATH adjustment
to ensure proper Python version and prioritization.

Enhanced by: Engineer Agent
Date: {datetime.now().isoformat()}
Original: {original_script_path}
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

{detector_functions}

def setup_python_environment():
    """
    Set up the Python environment for Claude PM Framework execution.
    
    Returns:
        Tuple of (success, python_executable, messages)
    """
    messages = []
    
    # Adjust PATH to prioritize system Python
    adjusted_path = adjust_path_for_system_python()
    os.environ["PATH"] = adjusted_path
    messages.append("✅ PATH adjusted to prioritize system Python")
    
    # Detect best Python
    python_executable = detect_best_python()
    if not python_executable:
        messages.append("❌ No suitable Python environment found")
        return False, None, messages
    
    # Validate Python environment
    is_valid, validation_message = validate_python_environment(python_executable)
    if not is_valid:
        messages.append(f"❌ Python validation failed: {{validation_message}}")
        return False, python_executable, messages
    
    messages.append(f"✅ Using Python: {{python_executable}}")
    return True, python_executable, messages

# Set up Python environment at script start
PYTHON_SETUP_SUCCESS, DETECTED_PYTHON, SETUP_MESSAGES = setup_python_environment()

if not PYTHON_SETUP_SUCCESS:
    print("❌ Python environment setup failed:")
    for msg in SETUP_MESSAGES:
        print(f"   {{msg}}")
    print()
    print("🔧 Troubleshooting:")
    print("   • Install Python 3.8+ from python.org")
    print("   • Ensure system Python is in PATH")
    print("   • Run: claude-pm --system-info")
    sys.exit(1)

# Display setup success (only in verbose mode)
if "--verbose" in sys.argv or "--debug" in sys.argv:
    print("🐍 Python Environment Setup:")
    for msg in SETUP_MESSAGES:
        print(f"   {{msg}}")
    print()

# Override sys.executable to use detected Python
if DETECTED_PYTHON and DETECTED_PYTHON != sys.executable:
    # For subprocess calls, we'll use DETECTED_PYTHON
    CLAUDE_PM_PYTHON = DETECTED_PYTHON
else:
    CLAUDE_PM_PYTHON = sys.executable

# Original script content follows below
# =======================================

{original_content}
'''
        
        # Write enhanced script
        try:
            with open(output_path, 'w') as f:
                f.write(enhanced_content)
            
            # Copy permissions from original
            original_stat = original_path.stat()
            os.chmod(output_path, original_stat.st_mode)
            
            self.logger.info(f"Enhanced CLI script created: {output_path}")
            return output_path
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Failed to create enhanced CLI script: {e}"
            )
            raise
    
    def patch_existing_cli_script(self, script_path: str, backup: bool = True) -> bool:
        """
        Patch an existing CLI script to include Python environment management.
        
        Args:
            script_path: Path to the CLI script to patch
            backup: Whether to create a backup of the original script
            
        Returns:
            True if patching succeeded, False otherwise
        """
        script_file = Path(script_path)
        
        if not script_file.exists():
            self.collect_memory(
                "error:integration", "high",
                f"CLI script not found for patching: {script_path}"
            )
            return False
        
        try:
            # Create backup if requested
            if backup:
                backup_path = f"{script_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(script_path, backup_path)
                self.logger.info(f"Backup created: {backup_path}")
            
            # Read current content
            with open(script_file, 'r') as f:
                content = f.read()
            
            # Check if already patched
            if "# Enhanced by: Engineer Agent" in content:
                self.logger.info("Script already patched")
                return True
            
            # Add Python environment setup after imports but before main logic
            detector_functions = self.create_python_detector_function()
            
            # Find insertion point (after imports, before main functions)
            lines = content.split('\n')
            insertion_point = 0
            
            # Look for the end of imports or the beginning of functions/classes
            for i, line in enumerate(lines):
                if (line.strip().startswith('def ') or 
                    line.strip().startswith('class ') or
                    line.strip().startswith('if __name__')):
                    insertion_point = i
                    break
                elif line.strip() and not (line.strip().startswith('#') or 
                                          line.strip().startswith('import ') or
                                          line.strip().startswith('from ')):
                    insertion_point = i
                    break
            
            # Insert Python environment management code
            enhancement_code = f'''
# =======================================
# Python Environment Management Enhancement
# Enhanced by: Engineer Agent
# Date: {datetime.now().isoformat()}
# =======================================

{detector_functions}

# Set up Python environment for Claude PM Framework
def _setup_claude_pm_python_environment():
    """Setup Python environment with proper PATH and version detection."""
    # Adjust PATH to prioritize system Python
    adjusted_path = adjust_path_for_system_python()
    os.environ["PATH"] = adjusted_path
    
    # Detect and validate Python
    python_executable = detect_best_python()
    if python_executable:
        is_valid, _ = validate_python_environment(python_executable)
        if is_valid:
            return python_executable
    
    return None

# Initialize Python environment
_CLAUDE_PM_PYTHON = _setup_claude_pm_python_environment()

# =======================================
# End Python Environment Management
# =======================================

'''
            
            # Insert the enhancement code
            lines.insert(insertion_point, enhancement_code)
            
            # Write patched content
            with open(script_file, 'w') as f:
                f.write('\n'.join(lines))
            
            self.logger.info(f"Successfully patched CLI script: {script_path}")
            return True
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Failed to patch CLI script {script_path}: {e}"
            )
            self.logger.error(f"Failed to patch CLI script: {e}")
            return False
    
    def create_installation_script(self, output_path: Optional[str] = None) -> str:
        """
        Create a comprehensive installation script with Python environment validation.
        
        Args:
            output_path: Optional custom output path for installation script
            
        Returns:
            Path to the created installation script
        """
        if output_path is None:
            output_path = str(self.framework_path / "scripts" / "install_with_python_validation.py")
        
        best_python, validation_messages = self.detect_and_validate_python_for_cli()
        requirements_path = self.framework_path / "requirements" / "base.txt"
        
        installation_script = f'''#!/usr/bin/env python3
"""
Claude PM Framework Installation Script with Python Environment Validation

Comprehensive installation script that validates Python environment,
adjusts PATH ordering, and installs all requirements properly.

Author: Engineer Agent
Date: {datetime.now().isoformat()}
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

{self.create_python_detector_function()}

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
        logger.error(f"Requirements file not found: {{requirements_file}}")
        return False
    
    logger.info(f"Installing requirements using {{python_executable}}")
    
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
        
        logger.error(f"Requirements installation failed: {{result.stderr}}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error("Requirements installation timed out")
        return False
    except Exception as e:
        logger.error(f"Requirements installation error: {{e}}")
        return False

def main():
    """Main installation function."""
    logger = setup_logging()
    
    logger.info("🚀 Claude PM Framework Installation with Python Validation")
    logger.info("=" * 60)
    
    # Adjust PATH for proper Python prioritization
    logger.info("🐍 Adjusting PATH to prioritize system Python...")
    adjusted_path = adjust_path_for_system_python()
    os.environ["PATH"] = adjusted_path
    
    # Detect best Python environment
    logger.info("🔍 Detecting best Python environment...")
    python_executable = detect_best_python()
    
    if not python_executable:
        logger.error("❌ No suitable Python environment found")
        logger.error("🔧 Please install Python 3.8+ from python.org")
        return False
    
    # Validate Python environment
    logger.info(f"✅ Found Python: {{python_executable}}")
    is_valid, validation_message = validate_python_environment(python_executable)
    
    if not is_valid:
        logger.error(f"❌ Python validation failed: {{validation_message}}")
        return False
    
    logger.info(f"✅ Python environment validated: {{validation_message}}")
    
    # Install requirements
    requirements_file = "{requirements_path}"
    if Path(requirements_file).exists():
        logger.info("📦 Installing Python requirements...")
        if not install_requirements(python_executable, requirements_file):
            logger.error("❌ Requirements installation failed")
            return False
        logger.info("✅ Requirements installed successfully")
    else:
        logger.warning(f"⚠️  Requirements file not found: {{requirements_file}}")
    
    # Install Claude PM package
    logger.info("📦 Installing Claude PM Python package...")
    framework_path = Path(__file__).parent.parent
    
    try:
        result = subprocess.run([
            python_executable, "-m", "pip", "install", "--user", "-e", str(framework_path)
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info("✅ Claude PM package installed successfully")
        else:
            # Try with --break-system-packages
            if ("externally-managed-environment" in result.stderr or 
                "externally managed" in result.stderr):
                
                logger.info("Retrying package installation with --break-system-packages")
                result = subprocess.run([
                    python_executable, "-m", "pip", "install", "--user",
                    "--break-system-packages", "-e", str(framework_path)
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("✅ Claude PM package installed successfully")
                else:
                    logger.error(f"❌ Package installation failed: {{result.stderr}}")
                    return False
            else:
                logger.error(f"❌ Package installation failed: {{result.stderr}}")
                return False
    
    except Exception as e:
        logger.error(f"❌ Package installation error: {{e}}")
        return False
    
    logger.info("🎉 Claude PM Framework installation completed successfully!")
    logger.info("🚀 You can now use: claude-pm --help")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation error: {{e}}")
        sys.exit(1)
'''
        
        try:
            with open(output_path, 'w') as f:
                f.write(installation_script)
            
            # Make script executable
            os.chmod(output_path, 0o755)
            
            self.logger.info(f"Installation script created: {output_path}")
            return output_path
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Failed to create installation script: {e}"
            )
            raise
    
    def create_user_guidance_document(self, output_path: Optional[str] = None) -> str:
        """
        Create comprehensive user guidance for Python environment configuration.
        
        Args:
            output_path: Optional custom output path for guidance document
            
        Returns:
            Path to the created guidance document
        """
        if output_path is None:
            output_path = str(self.framework_path / "docs" / "python_environment_guide.md")
        
        # Ensure docs directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Analyze current environment for guidance
        environments = self.python_manager.detect_all_python_environments()
        path_analysis = self.python_manager.analyze_current_path()
        best_env = self.python_manager.get_best_python_environment()
        
        guidance_content = f'''# Python Environment Configuration Guide for Claude PM Framework

*Generated by Engineer Agent on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## Overview

Claude PM Framework requires Python 3.8+ and proper PATH configuration to function correctly. This guide helps you configure your Python environment for optimal framework performance.

## Current Environment Analysis

### Detected Python Environments

{chr(10).join([
    f"- **{env.executable}**"
    f"  - Version: {env.version}"
    f"  - Type: {'System' if env.is_system else 'Homebrew' if env.is_homebrew else 'PyEnv' if env.is_pyenv else 'Other'}"
    f"  - Status: {'✅ Works' if env.works else '❌ Issues'}"
    + (f"  - Error: {env.error_message}" if env.error_message else "")
    for env in environments
]) if environments else "- No Python environments detected"}

### PATH Analysis

**Python-related paths found:** {len(path_analysis.python_paths)}

**Issues detected:**
{chr(10).join([f"- ⚠️  {issue}" for issue in path_analysis.path_issues]) if path_analysis.path_issues else "- ✅ No PATH issues detected"}

### Recommended Python

{f"**Best environment:** {best_env.executable} (v{best_env.version})" if best_env else "**No suitable environment found**"}

## Common Issues and Solutions

### Issue 1: Homebrew Python Prioritized Over System Python

**Problem:** Homebrew Python appears before system Python in PATH, causing conflicts.

**Symptoms:**
- CLI commands fail with import errors
- Wrong Python version being used
- Package installation issues

**Solution:**
```bash
# Create PATH adjustment script
python3 /path/to/claude-multiagent-pm/scripts/python_environment_manager.py --create-path-script

# Apply the PATH adjustment
source /tmp/adjust_python_path.sh

# Verify the fix
which python3
python3 --version
```

### Issue 2: Python Version Too Old

**Problem:** System has Python < 3.8, which doesn't meet minimum requirements.

**Solution:**
1. **Install Python 3.8+ from python.org:**
   - Download from https://www.python.org/downloads/
   - Run the installer
   - Ensure "Add Python to PATH" is checked

2. **Verify installation:**
   ```bash
   python3 --version
   # Should show Python 3.8 or higher
   ```

### Issue 3: Missing Python Dependencies

**Problem:** Required packages (click, rich, etc.) not installed.

**Solution:**
```bash
# Auto-install using our installation script
python3 /path/to/claude-multiagent-pm/scripts/install_with_python_validation.py

# Or manually install requirements
python3 -m pip install --user -r requirements/base.txt
```

### Issue 4: "Externally Managed Environment" Error

**Problem:** Modern Python installations block pip installs outside virtual environments.

**Solution:**
```bash
# Use --break-system-packages flag (safe for user installs)
python3 -m pip install --user --break-system-packages -r requirements/base.txt

# Or our installation script handles this automatically
python3 scripts/install_with_python_validation.py
```

## Platform-Specific Guidance

### macOS

**Recommended Setup:**
1. Use system Python (`/usr/bin/python3`) for Claude PM
2. Install Homebrew Python for development if needed
3. Ensure system paths come first in PATH

**PATH Order (recommended):**
```
/usr/bin
/bin
/usr/sbin
/sbin
/Library/Frameworks/Python.framework/Versions/Current/bin
/usr/local/bin
/opt/homebrew/bin  # Homebrew comes last
```

**Quick Fix Script:**
```bash
# Download and run PATH adjustment
curl -O https://raw.githubusercontent.com/your-repo/scripts/python_environment_manager.py
python3 python_environment_manager.py --create-path-script
source /tmp/adjust_python_path.sh
```

### Linux

**Recommended Setup:**
1. Use system Python (`/usr/bin/python3`)
2. Install python3-pip if not available
3. Use virtual environments for development

**Common Commands:**
```bash
# Install Python 3.8+ on Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3.8-pip

# Install on CentOS/RHEL
sudo yum install python38 python38-pip

# Or use pyenv for version management
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

### Windows

**Recommended Setup:**
1. Install Python from python.org
2. Use Python Launcher (`py`) for version selection
3. Ensure Python is in PATH

**Common Commands:**
```cmd
# Check available versions
py -0

# Use specific version
py -3.8 -m pip install --user -r requirements/base.txt

# Install Claude PM
py -3.8 -m pip install --user -e .
```

## Verification Commands

After configuration, verify your setup:

```bash
# 1. Check Python environment
python3 scripts/python_environment_manager.py --detect

# 2. Validate specific Python
python3 scripts/python_environment_manager.py --validate /usr/bin/python3

# 3. Generate comprehensive report
python3 scripts/python_environment_manager.py --generate-report

# 4. Test Claude PM CLI
claude-pm --system-info
```

## Troubleshooting Commands

```bash
# Comprehensive Python analysis
python3 scripts/python_environment_manager.py --detect --analyze-path --best-env

# Create PATH adjustment script
python3 scripts/python_environment_manager.py --create-path-script

# Install requirements with validation
python3 scripts/install_with_python_validation.py

# Generate diagnostic report
python3 scripts/python_environment_manager.py --generate-report --verbose
```

## Automation Scripts

The framework provides several automation scripts:

1. **`python_environment_manager.py`** - Comprehensive Python environment management
2. **`install_with_python_validation.py`** - Installation with validation
3. **`cli_python_integration.py`** - CLI enhancement and patching

## Getting Help

If you encounter issues:

1. Run diagnostics: `python3 scripts/python_environment_manager.py --generate-report`
2. Check logs in the generated report
3. Create an issue with the diagnostic report attached
4. Use `claude-pm --system-info` for framework status

## Best Practices

1. **Always use system Python for Claude PM**
2. **Keep Homebrew Python for development only**
3. **Use virtual environments for project development**
4. **Regularly update Python and dependencies**
5. **Test changes with validation scripts**

---

*This guide is automatically updated based on your current environment. For the latest version, run the Python environment manager.*
'''
        
        try:
            with open(output_path, 'w') as f:
                f.write(guidance_content)
            
            self.logger.info(f"User guidance document created: {output_path}")
            return output_path
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "medium",
                f"Failed to create user guidance document: {e}"
            )
            raise


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CLI Python Integration for Claude PM Framework"
    )
    parser.add_argument("--detect-python", action="store_true",
                       help="Detect and validate Python for CLI usage")
    parser.add_argument("--create-enhanced-cli", type=str, metavar="SCRIPT_PATH",
                       help="Create enhanced version of CLI script")
    parser.add_argument("--patch-cli", type=str, metavar="SCRIPT_PATH", 
                       help="Patch existing CLI script with Python management")
    parser.add_argument("--create-installer", type=str, nargs="?", const=None,
                       help="Create installation script with Python validation")
    parser.add_argument("--create-guide", type=str, nargs="?", const=None,
                       help="Create user guidance document")
    parser.add_argument("--framework-path", type=str,
                       help="Path to Claude PM Framework directory")
    parser.add_argument("--no-backup", action="store_true",
                       help="Don't create backup when patching")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    integration = CLIPythonIntegration(args.framework_path)
    
    try:
        if args.detect_python:
            python_exe, messages = integration.detect_and_validate_python_for_cli()
            print("🐍 Python Detection Results:")
            for message in messages:
                print(f"   {message}")
            if python_exe:
                print(f"\n✅ Recommended Python: {python_exe}")
            else:
                print("\n❌ No suitable Python found")
        
        if args.create_enhanced_cli:
            output_path = integration.create_enhanced_cli_script(args.create_enhanced_cli)
            print(f"\n📝 Enhanced CLI script created: {output_path}")
        
        if args.patch_cli:
            success = integration.patch_existing_cli_script(
                args.patch_cli, 
                backup=not args.no_backup
            )
            if success:
                print(f"\n✅ CLI script patched successfully: {args.patch_cli}")
            else:
                print(f"\n❌ Failed to patch CLI script: {args.patch_cli}")
        
        if args.create_installer is not None:
            installer_path = integration.create_installation_script(args.create_installer)
            print(f"\n📦 Installation script created: {installer_path}")
        
        if args.create_guide is not None:
            guide_path = integration.create_user_guidance_document(args.create_guide)
            print(f"\n📖 User guidance document created: {guide_path}")
        
        # Save memory collection if any data was collected
        if integration.memory_collection:
            memory_data = {
                "timestamp": datetime.now().isoformat(),
                "total_entries": len(integration.memory_collection),
                "entries": integration.memory_collection
            }
            
            memory_path = f"/tmp/cli_integration_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(memory_path, 'w') as f:
                import json
                json.dump(memory_data, f, indent=2, default=str)
            print(f"\n🧠 Memory collection saved: {memory_path}")
    
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()