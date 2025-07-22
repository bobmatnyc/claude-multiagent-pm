#!/usr/bin/env python3
"""Test deployment in regular project directory."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append('..')

from claude_pm.services.framework_claude_md_generator import FrameworkClaudeMdGenerator

def test_deployment():
    """Test that deployment works in regular project."""
    print("Testing CLAUDE.md deployment in regular project directory...")
    
    generator = FrameworkClaudeMdGenerator()
    
    # Try to deploy to current directory (regular project)
    try:
        success, message = generator.deploy_to_parent(Path.cwd())
        print(f"Deployment success: {success}")
        print(f"Deployment message: {message}")
    except Exception as e:
        print(f"Deployment error: {e}")
    
    # Check if deployment succeeded
    claude_md_path = Path.cwd() / "CLAUDE.md"
    if claude_md_path.exists():
        print("✅ SUCCESS: CLAUDE.md was deployed to regular project")
        print(f"   File size: {claude_md_path.stat().st_size} bytes")
    else:
        print("❌ ERROR: CLAUDE.md deployment failed in regular project!")

if __name__ == "__main__":
    test_deployment()