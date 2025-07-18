#!/usr/bin/env python3
"""
Ensure aitrackdown alias is available across platforms.

This script checks if the 'aitrackdown' command is available, and if not,
creates the appropriate alias based on the operating system.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path


def is_command_available(command):
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


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


def get_npm_global_prefix():
    """Get npm global installation prefix."""
    success, stdout, _ = run_command(["npm", "config", "get", "prefix"])
    if success:
        return stdout.strip()
    return None


def get_npm_global_bin():
    """Get npm global bin directory."""
    prefix = get_npm_global_prefix()
    if not prefix:
        return None
    
    system = platform.system()
    if system == "Windows":
        return os.path.join(prefix, "node_modules", ".bin")
    else:
        return os.path.join(prefix, "bin")


def find_ai_trackdown_tools():
    """Find ai-trackdown-tools installation."""
    # Check if ai-trackdown-tools is installed
    npm_bin = get_npm_global_bin()
    if not npm_bin:
        return None, None
    
    system = platform.system()
    
    # Look for the actual executable
    if system == "Windows":
        # On Windows, look for .cmd and .ps1 files
        for ext in [".cmd", ".ps1", ".bat"]:
            ai_trackdown_path = os.path.join(npm_bin, f"ai-trackdown-tools{ext}")
            if os.path.exists(ai_trackdown_path):
                return ai_trackdown_path, npm_bin
    else:
        # On Unix-like systems
        ai_trackdown_path = os.path.join(npm_bin, "ai-trackdown-tools")
        if os.path.exists(ai_trackdown_path):
            return ai_trackdown_path, npm_bin
    
    return None, npm_bin


def create_unix_alias(source_path, target_dir):
    """Create Unix/Linux/macOS alias (symlink)."""
    target_path = os.path.join(target_dir, "aitrackdown")
    
    try:
        # Remove existing symlink if it exists
        if os.path.islink(target_path):
            os.unlink(target_path)
        elif os.path.exists(target_path):
            os.remove(target_path)
        
        # Create new symlink
        os.symlink(source_path, target_path)
        
        # Make sure it's executable
        os.chmod(target_path, 0o755)
        
        return True, f"Created symlink: {target_path} -> {source_path}"
    except Exception as e:
        return False, f"Failed to create symlink: {str(e)}"


def create_windows_alias(source_path, target_dir):
    """Create Windows alias (batch file)."""
    target_path = os.path.join(target_dir, "aitrackdown.cmd")
    
    try:
        # Create batch file content
        batch_content = f"""@echo off
"{source_path}" %*
"""
        
        # Write batch file
        with open(target_path, 'w') as f:
            f.write(batch_content)
        
        return True, f"Created batch file: {target_path}"
    except Exception as e:
        return False, f"Failed to create batch file: {str(e)}"


def create_shell_alias_instructions():
    """Generate instructions for manual shell alias creation."""
    shell = os.environ.get('SHELL', '/bin/bash')
    shell_name = os.path.basename(shell)
    
    instructions = {
        'bash': {
            'file': '~/.bashrc or ~/.bash_profile',
            'command': 'alias aitrackdown="ai-trackdown-tools"'
        },
        'zsh': {
            'file': '~/.zshrc',
            'command': 'alias aitrackdown="ai-trackdown-tools"'
        },
        'fish': {
            'file': '~/.config/fish/config.fish',
            'command': 'alias aitrackdown="ai-trackdown-tools"'
        }
    }
    
    shell_info = instructions.get(shell_name, instructions['bash'])
    
    return f"""
To create a shell alias manually, add this line to {shell_info['file']}:
{shell_info['command']}

Then reload your shell configuration:
source {shell_info['file']}
"""


def ensure_aitrackdown_alias():
    """Main function to ensure aitrackdown alias is available."""
    status = {
        'success': False,
        'message': '',
        'actions': [],
        'platform': platform.system(),
        'already_available': False
    }
    
    # Check if aitrackdown is already available
    if is_command_available('aitrackdown'):
        status['success'] = True
        status['already_available'] = True
        status['message'] = 'aitrackdown command is already available'
        return status
    
    # Check if ai-trackdown-tools is available
    if not is_command_available('ai-trackdown-tools'):
        status['message'] = 'ai-trackdown-tools is not installed. Please install @bobmatnyc/ai-trackdown-tools'
        status['actions'].append('npm install -g @bobmatnyc/ai-trackdown-tools')
        return status
    
    # Find ai-trackdown-tools installation
    ai_trackdown_path, npm_bin = find_ai_trackdown_tools()
    
    if not ai_trackdown_path:
        status['message'] = 'ai-trackdown-tools is installed but the executable was not found'
        return status
    
    # Create alias based on platform
    system = platform.system()
    
    if system in ['Linux', 'Darwin']:  # Unix-like systems
        success, message = create_unix_alias(ai_trackdown_path, npm_bin)
        status['success'] = success
        status['message'] = message
        status['actions'].append(f"Created Unix symlink in {npm_bin}")
        
        if not success:
            # Provide fallback instructions
            status['actions'].append(create_shell_alias_instructions())
    
    elif system == 'Windows':
        success, message = create_windows_alias(ai_trackdown_path, npm_bin)
        status['success'] = success
        status['message'] = message
        status['actions'].append(f"Created Windows batch file in {npm_bin}")
    
    else:
        status['message'] = f'Unsupported platform: {system}'
        status['actions'].append(create_shell_alias_instructions())
    
    return status


def main():
    """Main entry point."""
    print("Ensuring aitrackdown alias is available...")
    
    result = ensure_aitrackdown_alias()
    
    # Print results
    print(f"\nPlatform: {result['platform']}")
    print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"Message: {result['message']}")
    
    if result['actions']:
        print("\nActions taken:")
        for action in result['actions']:
            print(f"  - {action}")
    
    # Return appropriate exit code
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())