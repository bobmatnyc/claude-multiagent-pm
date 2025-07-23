#!/usr/bin/env python3
"""
Python version of increment_version script.
Increments version numbers in various project files.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

def increment_version(version_string, increment_type='patch'):
    """
    Increment a semantic version string.
    
    Args:
        version_string: Version string like "1.4.7"
        increment_type: 'major', 'minor', or 'patch'
    
    Returns:
        New version string
    """
    # Remove 'v' prefix if present
    version = version_string.lstrip('v')
    
    # Parse version
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise ValueError(f"Invalid version format: {version_string}")
    
    major, minor, patch = map(int, match.groups())
    
    # Increment based on type
    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")
    
    return f"{major}.{minor}.{patch}"

def update_package_json(file_path, new_version):
    """Update version in package.json."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    data['version'] = new_version
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')  # Add trailing newline

def update_pyproject_toml(file_path, new_version):
    """Update version in pyproject.toml."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update version line
    content = re.sub(
        r'^version = "[^"]*"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    with open(file_path, 'w') as f:
        f.write(content)

def update_version_file(file_path, new_version):
    """Update plain VERSION file."""
    with open(file_path, 'w') as f:
        f.write(new_version + '\n')

def update_python_version_file(file_path, new_version):
    """Update _version.py file."""
    content = f'"""Version information for claude_pm package."""\n\n__version__ = "{new_version}"\n'
    with open(file_path, 'w') as f:
        f.write(content)

def main():
    """Main function to increment versions across all files."""
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Parse arguments
    increment_type = 'patch'  # default
    if len(sys.argv) > 1:
        if sys.argv[1] in ['major', 'minor', 'patch']:
            increment_type = sys.argv[1]
        else:
            print(f"Usage: {sys.argv[0]} [major|minor|patch]")
            sys.exit(1)
    
    # Read current version from package.json
    package_json_path = project_root / 'package.json'
    with open(package_json_path, 'r') as f:
        current_version = json.load(f)['version']
    
    # Calculate new version
    new_version = increment_version(current_version, increment_type)
    
    print(f"📦 Incrementing version: {current_version} → {new_version}")
    
    # Update all version files
    files_to_update = {
        'package.json': (package_json_path, update_package_json),
        'pyproject.toml': (project_root / 'pyproject.toml', update_pyproject_toml),
        'VERSION': (project_root / 'VERSION', update_version_file),
        '_version.py': (project_root / 'claude_pm' / '_version.py', update_python_version_file),
    }
    
    for file_name, (file_path, update_func) in files_to_update.items():
        try:
            if file_path.exists():
                update_func(file_path, new_version)
                print(f"  ✅ Updated {file_name}")
            else:
                print(f"  ⏭️  Skipped {file_name} (not found)")
        except Exception as e:
            print(f"  ❌ Failed to update {file_name}: {e}")
    
    print(f"\n✨ Version updated to {new_version}")
    print("\n💡 Next steps:")
    print("  1. Update CHANGELOG.md")
    print("  2. Commit changes: git commit -m 'chore: bump version to {}'".format(new_version))
    print("  3. Tag release: git tag v{}".format(new_version))

if __name__ == "__main__":
    main()