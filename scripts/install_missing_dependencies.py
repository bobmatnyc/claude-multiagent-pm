#!/usr/bin/env python3
"""
Install Missing Dependencies Script
===================================

This script ensures all required Python dependencies are installed,
particularly those that might have been missed during npm installation.
"""

import subprocess
import sys
import os
from pathlib import Path


def find_python_command():
    """Find the appropriate Python command."""
    commands = ['python3', 'python']
    for cmd in commands:
        try:
            result = subprocess.run(
                [cmd, '--version'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            if result.returncode == 0 and 'Python 3.' in result.stdout:
                return cmd
        except:
            continue
    return None


def install_dependency(python_cmd, package, use_break_system=False):
    """Install a single dependency."""
    print(f"Installing {package}...")
    
    try:
        cmd = [python_cmd, '-m', 'pip', 'install', '--user']
        if use_break_system:
            cmd.append('--break-system-packages')
        cmd.append(package)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ {package} installed successfully")
            return True
        else:
            # Check if we need --break-system-packages
            if 'externally-managed-environment' in result.stderr or 'externally managed' in result.stderr:
                if not use_break_system:
                    print(f"   Retrying with --break-system-packages...")
                    return install_dependency(python_cmd, package, use_break_system=True)
            
            print(f"❌ Failed to install {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing {package}: {str(e)}")
        return False


def check_dependency(python_cmd, module_name):
    """Check if a Python module is importable."""
    try:
        result = subprocess.run(
            [python_cmd, '-c', f'import {module_name}; print("{module_name} available")'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def main():
    """Main installation routine."""
    print("🔧 Claude PM Missing Dependencies Installer")
    print("=" * 50)
    
    # Find Python command
    python_cmd = find_python_command()
    if not python_cmd:
        print("❌ Python 3.8+ not found. Please install Python 3.8 or newer.")
        sys.exit(1)
    
    print(f"✅ Using Python: {python_cmd}")
    
    # Dependencies to check and install
    dependencies = [
        ('python-frontmatter>=1.0.0', 'frontmatter'),
        ('mistune>=3.0.0', 'mistune'),
        ('click>=8.1.0', 'click'),
        ('rich>=13.7.0', 'rich'),
        ('pydantic>=2.5.0', 'pydantic'),
        ('pyyaml>=6.0.1', 'yaml'),
        ('python-dotenv>=1.0.0', 'dotenv'),
        ('requests>=2.31.0', 'requests'),
        ('openai>=1.0.0', 'openai'),
        ('aiohttp>=3.9.0', 'aiohttp'),
        ('httpx>=0.25.0', 'httpx'),
        ('typer>=0.9.0', 'typer'),
        ('toml>=0.10.2', 'toml'),
        ('psutil>=5.9.0', 'psutil'),
        ('pathspec>=0.11.0', 'pathspec')
    ]
    
    missing_deps = []
    
    # Check which dependencies are missing
    print("\n📋 Checking installed dependencies...")
    for package, module in dependencies:
        if check_dependency(python_cmd, module):
            print(f"   ✅ {module}")
        else:
            print(f"   ❌ {module} (missing)")
            missing_deps.append(package)
    
    if not missing_deps:
        print("\n✅ All dependencies are already installed!")
        return
    
    # Install missing dependencies
    print(f"\n📦 Installing {len(missing_deps)} missing dependencies...")
    success_count = 0
    
    for dep in missing_deps:
        if install_dependency(python_cmd, dep):
            success_count += 1
    
    # Verify installation
    print("\n🔍 Verifying installation...")
    
    # Check Claude PM package
    claude_pm_available = check_dependency(python_cmd, 'claude_pm')
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")
    print(f"   Dependencies installed: {success_count}/{len(missing_deps)}")
    print(f"   Claude PM package: {'✅ Available' if claude_pm_available else '❌ Not available'}")
    
    if success_count == len(missing_deps):
        print("\n✅ All missing dependencies installed successfully!")
        print("\n🚀 Next steps:")
        print("   1. Run 'claude-pm --version' to verify CLI")
        print("   2. Run 'claude-pm init' to initialize framework")
    else:
        print("\n⚠️  Some dependencies failed to install.")
        print("   Try running 'pip install -r requirements/base.txt' manually")
        
        # If claude_pm not available, suggest installing the package
        if not claude_pm_available:
            print("\n💡 Claude PM package not found. Install it with:")
            print(f"   cd {Path(__file__).parent.parent}")
            print(f"   {python_cmd} -m pip install -e .")


if __name__ == "__main__":
    main()