#!/usr/bin/env python3
"""
Quick Python Environment Fix for Claude PM Framework

This script can be run immediately to diagnose and fix Python environment issues,
particularly PATH ordering problems where Homebrew Python is prioritized over system Python.

Usage:
    python3 scripts/quick_python_fix.py
    python3 scripts/quick_python_fix.py --fix
    python3 scripts/quick_python_fix.py --test

Author: Engineer Agent
Date: 2025-07-14
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime

def detect_python_issue():
    """Quick detection of Python environment issues."""
    issues = []
    
    print("🔍 Detecting Python environment issues...")
    
    # Check current Python
    current_python = shutil.which("python3")
    if current_python:
        print(f"📍 Current python3: {current_python}")
        
        # Check if it's Homebrew Python
        if "/opt/homebrew" in current_python or "/usr/local" in current_python:
            issues.append("Homebrew Python is prioritized over system Python")
            print("⚠️  Issue: Homebrew Python has higher priority than system Python")
        
        # Check version
        try:
            version_result = subprocess.run([current_python, "--version"], 
                                          capture_output=True, text=True, timeout=5)
            if version_result.returncode == 0:
                print(f"📋 Version: {version_result.stdout.strip()}")
            else:
                issues.append("Python version check failed")
        except Exception as e:
            issues.append(f"Python version check error: {e}")
    else:
        issues.append("python3 not found in PATH")
        print("❌ python3 not found in PATH")
    
    # Check system Python availability
    system_python = "/usr/bin/python3"
    if Path(system_python).exists():
        print(f"✅ System Python available: {system_python}")
        try:
            version_result = subprocess.run([system_python, "--version"], 
                                          capture_output=True, text=True, timeout=5)
            if version_result.returncode == 0:
                print(f"📋 System Python version: {version_result.stdout.strip()}")
        except Exception:
            pass
    else:
        issues.append("System Python not available")
        print("❌ System Python not available at /usr/bin/python3")
    
    # Check PATH order
    current_path = os.environ.get("PATH", "").split(os.pathsep)
    usr_bin_priority = None
    homebrew_priority = None
    
    for i, path_entry in enumerate(current_path):
        if path_entry == "/usr/bin":
            usr_bin_priority = i
        elif "/opt/homebrew/bin" in path_entry or "/usr/local/bin" in path_entry:
            if homebrew_priority is None:
                homebrew_priority = i
    
    if usr_bin_priority is not None and homebrew_priority is not None:
        if homebrew_priority < usr_bin_priority:
            issues.append("Homebrew paths appear before system paths in PATH")
            print(f"⚠️  Issue: Homebrew path (position {homebrew_priority}) before system path (position {usr_bin_priority})")
    
    return issues

def create_fix_script():
    """Create a PATH fix script."""
    current_path = os.environ.get("PATH", "").split(os.pathsep)
    
    # Build recommended PATH
    priority_paths = ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    user_paths = [str(Path.home() / ".local" / "bin")]
    homebrew_paths = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/local/bin"]
    
    new_path = []
    
    # Add priority paths first
    for path in priority_paths:
        if Path(path).exists() and path not in new_path:
            new_path.append(path)
    
    # Add user paths
    for path in user_paths:
        if Path(path).exists() and path not in new_path:
            new_path.append(path)
    
    # Add remaining paths (excluding Homebrew for now)
    for path in current_path:
        if path not in new_path and not any(hb in path for hb in homebrew_paths):
            new_path.append(path)
    
    # Add Homebrew paths at the end
    for path in homebrew_paths:
        if Path(path).exists() and path not in new_path:
            new_path.append(path)
    
    recommended_path = os.pathsep.join(new_path)
    
    # Create fix script
    script_path = "/tmp/claude_pm_python_fix.sh"
    script_content = f'''#!/bin/bash
# Claude PM Python Environment Fix Script
# Generated: {datetime.now().isoformat()}
# 
# This script adjusts your PATH to prioritize system Python over Homebrew Python

echo "🐍 Claude PM Python Environment Fix"
echo "===================================="

echo "📊 Current PATH analysis:"
echo "Original PATH entries: {len(current_path)}"
echo "Recommended PATH entries: {len(new_path)}"

echo ""
echo "🔧 Applying PATH fix..."

# Export the optimized PATH
export PATH="{recommended_path}"

echo "✅ PATH updated successfully!"
echo ""

echo "🔍 Verification:"
echo "Current python3: $(which python3 2>/dev/null || echo 'not found')"
if command -v python3 >/dev/null 2>&1; then
    echo "Python version: $(python3 --version)"
else
    echo "⚠️  Warning: python3 still not found"
fi

echo ""
echo "📋 First 10 PATH entries:"
echo "$PATH" | tr ':' '\\n' | head -10 | nl

echo ""
echo "💡 To make this change permanent:"
echo "   1. Add this line to your ~/.bashrc or ~/.zshrc:"
echo "   export PATH=\"{recommended_path}\""
echo ""
echo "   2. Or run: echo 'export PATH=\"{recommended_path}\"' >> ~/.bashrc"
echo "   3. Then restart your terminal or run: source ~/.bashrc"

echo ""
echo "🧪 Test the fix:"
echo "   claude-pm --system-info"
echo "   python3 --version"
'''
    
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        return script_path
    except Exception as e:
        print(f"❌ Failed to create fix script: {e}")
        return None

def test_python_environment():
    """Test Python environment functionality."""
    print("🧪 Testing Python environment...")
    
    tests = []
    
    # Test 1: Python executable
    python_exe = shutil.which("python3")
    if python_exe:
        tests.append(("Python executable found", True, python_exe))
    else:
        tests.append(("Python executable found", False, "Not found"))
    
    # Test 2: Python version
    if python_exe:
        try:
            result = subprocess.run([python_exe, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                # Check if version is 3.8+
                if "Python 3." in version:
                    version_parts = version.replace("Python ", "").split(".")
                    if len(version_parts) >= 2:
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        if major == 3 and minor >= 8:
                            tests.append(("Python version 3.8+", True, version))
                        else:
                            tests.append(("Python version 3.8+", False, f"{version} (too old)"))
                    else:
                        tests.append(("Python version 3.8+", False, f"Cannot parse: {version}"))
                else:
                    tests.append(("Python version 3.8+", False, f"Not Python 3: {version}"))
            else:
                tests.append(("Python version check", False, result.stderr))
        except Exception as e:
            tests.append(("Python version check", False, str(e)))
    
    # Test 3: Basic imports
    if python_exe:
        try:
            result = subprocess.run([python_exe, "-c", "import sys, os, json, pathlib"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tests.append(("Basic imports", True, "All required modules available"))
            else:
                tests.append(("Basic imports", False, result.stderr))
        except Exception as e:
            tests.append(("Basic imports", False, str(e)))
    
    # Test 4: pip availability
    if python_exe:
        try:
            result = subprocess.run([python_exe, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tests.append(("pip availability", True, result.stdout.strip()))
            else:
                tests.append(("pip availability", False, "pip not available"))
        except Exception as e:
            tests.append(("pip availability", False, str(e)))
    
    # Display results
    print("\n📋 Test Results:")
    print("-" * 50)
    passed = 0
    for test_name, success, details in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"     {details}")
        if success:
            passed += 1
    
    print("-" * 50)
    print(f"Summary: {passed}/{len(tests)} tests passed")
    
    return passed == len(tests)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick Python Environment Fix for Claude PM")
    parser.add_argument("--fix", action="store_true", help="Create and display fix script")
    parser.add_argument("--test", action="store_true", help="Test Python environment")
    parser.add_argument("--apply", action="store_true", help="Apply the fix to current session")
    
    args = parser.parse_args()
    
    print("🐍 Claude PM Quick Python Environment Fix")
    print("=" * 50)
    
    # Detect issues
    issues = detect_python_issue()
    
    print(f"\n📊 Issues detected: {len(issues)}")
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("   ✅ No issues detected!")
    
    if args.test:
        print("\n" + "=" * 50)
        test_success = test_python_environment()
        if test_success:
            print("\n✅ All tests passed! Python environment is working correctly.")
        else:
            print("\n❌ Some tests failed. Python environment needs attention.")
    
    if args.fix or (issues and not args.test):
        print("\n" + "=" * 50)
        script_path = create_fix_script()
        if script_path:
            print(f"✅ Fix script created: {script_path}")
            print("\n💡 To apply the fix:")
            print(f"   source {script_path}")
            print("\n🔍 To see what the script does:")
            print(f"   cat {script_path}")
            
            if args.apply:
                print("\n🔧 Applying fix to current session...")
                # This won't persist outside this script, but shows what would happen
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                    # Extract the PATH from the script
                    for line in content.split('\n'):
                        if line.startswith('export PATH='):
                            new_path = line.split('=', 1)[1].strip('"')
                            os.environ['PATH'] = new_path
                            print("✅ PATH updated for this session")
                            print(f"🔍 New python3: {shutil.which('python3')}")
                            break
                except Exception as e:
                    print(f"❌ Failed to apply fix: {e}")
        else:
            print("❌ Failed to create fix script")
    
    if not any([args.fix, args.test, args.apply]) and issues:
        print("\n💡 Next steps:")
        print("   --fix    Create a fix script")
        print("   --test   Test Python environment")
        print("   --apply  Apply fix to current session")
        print("\nExample: python3 scripts/quick_python_fix.py --fix")

if __name__ == "__main__":
    main()