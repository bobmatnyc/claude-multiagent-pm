#!/usr/bin/env python3
"""
Verify wheel build includes all necessary files.
"""

import sys
import zipfile
from pathlib import Path


def verify_wheel(wheel_path: str) -> bool:
    """Verify wheel contents."""
    print(f"Verifying wheel: {wheel_path}")
    
    required_files = [
        "claude_pm/__init__.py",
        "claude_pm/cli.py",
        "claude_pm/data/framework/CLAUDE.md",
        "claude_pm/data/framework/agent-roles/base_agent.md",
    ]
    
    required_patterns = [
        ("Python files", ".py", 200),  # At least 200 Python files
        ("Markdown files", ".md", 30),  # At least 30 markdown files
        ("Framework files", "data/framework/", 10),  # At least 10 framework files
    ]
    
    with zipfile.ZipFile(wheel_path, 'r') as whl:
        file_list = whl.namelist()
        print(f"\nTotal files in wheel: {len(file_list)}")
        
        # Check required files
        print("\nChecking required files:")
        all_found = True
        for req_file in required_files:
            if req_file in file_list:
                print(f"  ✓ {req_file}")
            else:
                print(f"  ✗ {req_file} - NOT FOUND")
                all_found = False
        
        # Check patterns
        print("\nChecking file patterns:")
        for desc, pattern, min_count in required_patterns:
            if pattern.startswith("."):
                count = len([f for f in file_list if f.endswith(pattern)])
            else:
                count = len([f for f in file_list if pattern in f])
            
            if count >= min_count:
                print(f"  ✓ {desc}: {count} files (minimum: {min_count})")
            else:
                print(f"  ✗ {desc}: {count} files (minimum: {min_count}) - INSUFFICIENT")
                all_found = False
        
        # Show some framework files
        print("\nSample framework files:")
        framework_files = [f for f in file_list if "data/framework/" in f][:10]
        for f in framework_files:
            print(f"  - {f}")
        
        return all_found


def main():
    """Main function."""
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        print("No wheel files found in dist/")
        return 1
    
    wheel_path = str(wheel_files[0])
    
    if verify_wheel(wheel_path):
        print("\n✅ Wheel verification PASSED!")
        print(f"\nWheel is ready for deployment: {wheel_path}")
        print(f"To install: pip install {wheel_path}")
        return 0
    else:
        print("\n❌ Wheel verification FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())