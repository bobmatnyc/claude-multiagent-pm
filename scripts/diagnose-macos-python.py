#!/usr/bin/env python3
"""
Diagnose macOS Python environment and suggest Claude PM installation methods.

This script helps macOS users understand their Python setup and choose
the best installation method for Claude PM Framework.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class Colors:
    """Terminal color codes"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_os():
    """Check if running on macOS"""
    print_header("Operating System Check")
    
    os_type = platform.system()
    os_version = platform.version()
    
    if os_type == "Darwin":
        print_success(f"Running on macOS: {platform.mac_ver()[0]}")
        return True
    else:
        print_error(f"This script is for macOS. Detected: {os_type}")
        return False

def check_python():
    """Check Python installation details"""
    print_header("Python Environment")
    
    # Python version
    python_version = sys.version.split()[0]
    print_info(f"Python version: {python_version}")
    
    # Python executable
    print_info(f"Python path: {sys.executable}")
    
    # Check if it's Homebrew Python
    if "/opt/homebrew" in sys.executable or "/usr/local/Cellar" in sys.executable:
        print_warning("Using Homebrew Python - may have 'externally-managed-environment' restrictions")
        return "homebrew"
    elif "/System/Library" in sys.executable:
        print_warning("Using System Python - not recommended")
        return "system"
    elif "venv" in sys.executable or "virtualenv" in sys.executable:
        print_success("Running in a virtual environment")
        return "venv"
    else:
        print_info("Using custom Python installation")
        return "custom"

def check_pip():
    """Check pip installation and restrictions"""
    print_header("Pip Configuration")
    
    # Check if pip exists
    stdout, stderr, code = run_command("python3 -m pip --version")
    if code == 0:
        print_success(f"pip installed: {stdout}")
    else:
        print_error("pip not found")
        return False
    
    # Try a test install to check for restrictions
    print_info("Testing pip restrictions...")
    stdout, stderr, code = run_command("python3 -m pip install --dry-run --user requests 2>&1")
    
    if "externally-managed-environment" in stderr or "externally-managed-environment" in stdout:
        print_error("PEP 668 restriction detected: Cannot install packages globally")
        return "restricted"
    elif code == 0:
        print_success("pip can install packages")
        return "unrestricted"
    else:
        print_warning("pip status unclear")
        return "unknown"

def check_tools():
    """Check for installation tools"""
    print_header("Available Installation Tools")
    
    tools = {}
    
    # Check Homebrew
    stdout, _, code = run_command("brew --version")
    if code == 0:
        print_success(f"Homebrew installed: {stdout.split()[1]}")
        tools['brew'] = True
    else:
        print_warning("Homebrew not installed")
        tools['brew'] = False
    
    # Check pipx
    stdout, _, code = run_command("pipx --version")
    if code == 0:
        print_success(f"pipx installed: {stdout}")
        tools['pipx'] = True
    else:
        print_warning("pipx not installed (recommended for CLI tools)")
        tools['pipx'] = False
    
    # Check npm
    stdout, _, code = run_command("npm --version")
    if code == 0:
        print_success(f"npm installed: {stdout}")
        tools['npm'] = True
    else:
        print_warning("npm not installed")
        tools['npm'] = False
    
    return tools

def suggest_installation_method(python_type, pip_status, tools):
    """Suggest the best installation method based on environment"""
    print_header("Recommended Installation Method")
    
    if python_type == "venv":
        print_success("You're in a virtual environment - use standard pip install:")
        print(f"\n{Colors.BOLD}pip install @bobmatnyc/claude-multiagent-pm{Colors.END}\n")
        return
    
    if pip_status == "restricted" or python_type == "homebrew":
        print_info("Your Python has installation restrictions. Here are your options:\n")
        
        # Option 1: pipx (recommended)
        print(f"{Colors.BOLD}Option 1: pipx (RECOMMENDED){Colors.END}")
        if tools.get('pipx'):
            print_success("pipx is already installed!")
        else:
            print("Install pipx first:")
            print("  brew install pipx")
            print("  pipx ensurepath")
        print("\nThen install Claude PM:")
        print(f"{Colors.BOLD}  pipx install @bobmatnyc/claude-multiagent-pm{Colors.END}\n")
        
        # Option 2: Virtual environment
        print(f"{Colors.BOLD}Option 2: Virtual Environment{Colors.END}")
        print("Create a dedicated environment:")
        print("  python3 -m venv ~/claude-pm-env")
        print("  source ~/claude-pm-env/bin/activate")
        print("  pip install @bobmatnyc/claude-multiagent-pm\n")
        
        # Option 3: User install with break flag
        print(f"{Colors.BOLD}Option 3: User Install (use with caution){Colors.END}")
        print("Force user installation:")
        print("  pip install --user --break-system-packages @bobmatnyc/claude-multiagent-pm\n")
        
        # Quick installer
        print(f"{Colors.BOLD}Or use our Quick Installer:{Colors.END}")
        print("  curl -fsSL https://raw.githubusercontent.com/bobmatnyc/claude-multiagent-pm/main/scripts/install-claude-pm-macos.sh | bash\n")
    
    else:
        print_success("Your Python environment allows standard installation:")
        print(f"\n{Colors.BOLD}npm install -g @bobmatnyc/claude-multiagent-pm{Colors.END}\n")

def check_existing_installation():
    """Check if Claude PM is already installed"""
    print_header("Existing Installation Check")
    
    # Check CLI
    stdout, _, code = run_command("claude-pm --version")
    if code == 0:
        print_success(f"Claude PM CLI installed: {stdout}")
        
        # Find location
        stdout, _, _ = run_command("which claude-pm")
        if stdout:
            print_info(f"Location: {stdout}")
    else:
        print_info("Claude PM CLI not found in PATH")
    
    # Check Python module
    try:
        import claude_pm
        print_success(f"Claude PM Python module installed: {claude_pm.__version__}")
    except ImportError:
        print_info("Claude PM Python module not installed")

def main():
    """Main diagnostic function"""
    print_header("Claude PM macOS Installation Diagnostic")
    print("This tool will help you choose the best installation method\n")
    
    # Run checks
    if not check_os():
        return
    
    python_type = check_python()
    pip_status = check_pip()
    tools = check_tools()
    check_existing_installation()
    
    # Provide recommendations
    suggest_installation_method(python_type, pip_status, tools)
    
    # Additional resources
    print_header("Additional Resources")
    print("📚 Full macOS Installation Guide:")
    print("   https://github.com/bobmatnyc/claude-multiagent-pm/blob/main/docs/MACOS_INSTALLATION_GUIDE.md")
    print("\n🛠️  Troubleshooting Guide:")
    print("   https://github.com/bobmatnyc/claude-multiagent-pm/blob/main/docs/TROUBLESHOOTING.md")
    print("\n💬 Need help? Open an issue:")
    print("   https://github.com/bobmatnyc/claude-multiagent-pm/issues")

if __name__ == "__main__":
    main()