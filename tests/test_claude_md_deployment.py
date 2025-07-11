#!/usr/bin/env python3
"""
Test script for CLAUDE.md deployment functionality
"""

import sys
import os
sys.path.insert(0, '.')

from claude_pm.services.parent_directory_manager import ParentDirectoryManager
from claude_pm.commands.template_commands import deploy_claude_md

def test_claude_md_deployment():
    """Test the enhanced CLAUDE.md deployment with version checking."""
    
    print("🧪 Testing CLAUDE.md deployment functionality...")
    print("=" * 60)
    
    # Test 1: Version extraction
    print("\n1. Testing version extraction...")
    manager = ParentDirectoryManager()
    
    # Test old format
    old_content = "CLAUDE_MD_VERSION: 4.5.1"
    old_version = manager._extract_claude_md_version(old_content)
    print(f"   Old format (4.5.1): {old_version}")
    
    # Test new format
    new_content = "CLAUDE_MD_VERSION: 4.5.1-007"
    new_version = manager._extract_claude_md_version(new_content)
    print(f"   New format (4.5.1-007): {new_version}")
    
    # Test 2: Version comparison
    print("\n2. Testing version comparison...")
    comparison1 = manager._compare_versions("4.5.1", "4.5.1-001")
    print(f"   4.5.1 vs 4.5.1-001: {comparison1}")
    
    comparison2 = manager._compare_versions("4.5.1-005", "4.5.1-003")
    print(f"   4.5.1-005 vs 4.5.1-003: {comparison2}")
    
    comparison3 = manager._compare_versions("4.5.1-001", "4.5.2-001")
    print(f"   4.5.1-001 vs 4.5.2-001: {comparison3}")
    
    # Test 3: Next version generation
    print("\n3. Testing next version generation...")
    next_version1 = manager._generate_next_claude_md_version("4.5.1", "4.5.1")
    print(f"   Next after 4.5.1: {next_version1}")
    
    next_version2 = manager._generate_next_claude_md_version("4.5.1-007", "4.5.1")
    print(f"   Next after 4.5.1-007: {next_version2}")
    
    # Test 4: Deployment skip logic
    print("\n4. Testing deployment skip logic...")
    
    # Create test files
    from pathlib import Path
    import tempfile
    
    template_content = """# Claude PM Framework Configuration - Deployment

<!-- 
CLAUDE_MD_VERSION: {{CLAUDE_MD_VERSION}}
FRAMEWORK_VERSION: 4.5.1
-->

Test framework content"""
    
    target_content_newer = """# Claude PM Framework Configuration - Deployment

<!-- 
CLAUDE_MD_VERSION: 4.5.1-010
FRAMEWORK_VERSION: 4.5.1
-->

Test framework content"""
    
    target_content_older = """# Claude PM Framework Configuration - Deployment

<!-- 
CLAUDE_MD_VERSION: 4.5.1-005
FRAMEWORK_VERSION: 4.5.1
-->

Test framework content"""
    
    # Create temporary files for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as newer_file:
        newer_file.write(target_content_newer)
        newer_path = Path(newer_file.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as older_file:
        older_file.write(target_content_older)
        older_path = Path(older_file.name)
    
    try:
        # Test with newer target (should skip)
        should_skip_newer, reason_newer = manager._should_skip_deployment(
            newer_path,
            template_content
        )
        print(f"   Skip with newer target: {should_skip_newer} - {reason_newer}")
        
        # Test with older target (should deploy)
        should_skip_older, reason_older = manager._should_skip_deployment(
            older_path,
            template_content
        )
        print(f"   Skip with older target: {should_skip_older} - {reason_older}")
        
    finally:
        # Clean up temporary files
        newer_path.unlink(missing_ok=True)
        older_path.unlink(missing_ok=True)
    
    print("\n✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_claude_md_deployment()