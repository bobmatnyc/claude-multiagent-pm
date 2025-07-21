#!/usr/bin/env python3
"""Quick test to verify current refactoring state"""

import os
import sys
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

def check_file(path, max_lines=1000):
    """Check if file exists and its line count"""
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = len(f.readlines())
        status = "✓" if lines <= max_lines else "✗"
        color = GREEN if lines <= max_lines else RED
        print(f"{color}{status}{NC} {path}: {lines} lines")
        return lines <= max_lines
    else:
        print(f"{RED}✗{NC} {path}: NOT FOUND")
        return False

def main():
    print(f"{YELLOW}Current Refactoring State Check{NC}")
    print("=" * 50)
    
    # Check main refactored files
    files = [
        ("claude_pm/services/parent_directory_manager.py", 1000),
        ("claude_pm/core/agent_registry.py", 1000),
        ("claude_pm/core/agent_registry_sync.py", 1000),
        ("claude_pm/orchestration/backwards_compatible_orchestrator.py", 1000),
    ]
    
    print("\n📁 Main Files:")
    results = []
    for filepath, max_lines in files:
        results.append(check_file(filepath, max_lines))
    
    # Check for new module directories
    print("\n📂 New Module Directories:")
    dirs = [
        "claude_pm/services/parent_directory/",
        "claude_pm/core/agent_registry/",
        "claude_pm/orchestration/orchestrator/",
    ]
    
    for dirpath in dirs:
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            print(f"{GREEN}✓{NC} {dirpath} exists")
            # List contents
            contents = os.listdir(dirpath)
            for item in contents:
                print(f"  - {item}")
        else:
            print(f"{RED}✗{NC} {dirpath} NOT FOUND")
    
    # Summary
    print("\n" + "=" * 50)
    if all(results):
        print(f"{GREEN}✅ All files are under 1000 lines!{NC}")
    else:
        print(f"{YELLOW}⚠️  Some files need attention{NC}")
        print("\nNote: The refactored module structure may not have been")
        print("created on disk yet. This is expected if the refactoring")
        print("was done in a previous session without committing.")

if __name__ == "__main__":
    main()