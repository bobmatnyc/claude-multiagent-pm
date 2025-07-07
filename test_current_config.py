#!/usr/bin/env python3
"""
Test script to verify current configuration behavior with CLAUDE_PM_ROOT.
"""

import os
from pathlib import Path
from claude_pm.core.config import Config

def test_current_config():
    """Test current configuration with and without CLAUDE_PM_ROOT."""
    
    # Test 1: Default behavior (no CLAUDE_PM_ROOT)
    print("=== Test 1: Default Configuration (no CLAUDE_PM_ROOT) ===")
    if 'CLAUDE_PM_ROOT' in os.environ:
        del os.environ['CLAUDE_PM_ROOT']
    
    config1 = Config()
    print(f"claude_pm_path: {config1.get('claude_pm_path')}")
    print(f"managed_path: {config1.get('managed_path')}")
    print(f"base_path: {config1.get('base_path')}")
    print()
    
    # Test 2: With CLAUDE_PM_ROOT set
    print("=== Test 2: With CLAUDE_PM_ROOT Environment Variable ===")
    test_root = "/tmp/test-claude-pm"
    os.environ['CLAUDE_PM_ROOT'] = test_root
    
    config2 = Config()
    print(f"CLAUDE_PM_ROOT: {test_root}")
    print(f"claude_pm_path: {config2.get('claude_pm_path')}")
    print(f"managed_path: {config2.get('managed_path')}")
    print(f"base_path: {config2.get('base_path')}")
    print()
    
    # Test 3: Check if paths are actually different
    print("=== Test 3: Path Differences ===")
    print(f"Default claude_pm_path != Custom claude_pm_path: {config1.get('claude_pm_path') != config2.get('claude_pm_path')}")
    print(f"Default managed_path != Custom managed_path: {config1.get('managed_path') != config2.get('managed_path')}")
    
    # Clean up
    if 'CLAUDE_PM_ROOT' in os.environ:
        del os.environ['CLAUDE_PM_ROOT']

if __name__ == "__main__":
    test_current_config()