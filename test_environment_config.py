#!/usr/bin/env python3
"""
Comprehensive test for CLAUDE_PM_ROOT environment variable integration.
"""

import os
import tempfile
from pathlib import Path
from claude_pm.core.config import Config
from claude_pm.services.project_service import ProjectService
from claude_pm.cli import get_claude_pm_path, get_managed_path, get_framework_config

def test_environment_config():
    """Test complete environment variable configuration."""
    
    print("=== CLAUDE PM Framework Environment Configuration Test ===\n")
    
    # Save original environment
    original_env = os.environ.get('CLAUDE_PM_ROOT')
    
    try:
        # Test 1: Default behavior
        print("Test 1: Default Configuration")
        print("-" * 40)
        if 'CLAUDE_PM_ROOT' in os.environ:
            del os.environ['CLAUDE_PM_ROOT']
        
        config = Config()
        print(f"✓ Base Path: {config.get('base_path')}")
        print(f"✓ Claude PM Path: {config.get('claude_pm_path')}")
        print(f"✓ Managed Path: {config.get('managed_path')}")
        print()
        
        # Test 2: Custom environment
        print("Test 2: Custom CLAUDE_PM_ROOT")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "custom-claude-pm"
            os.environ['CLAUDE_PM_ROOT'] = str(custom_root)
            
            config = Config()
            print(f"✓ CLAUDE_PM_ROOT: {custom_root}")
            print(f"✓ Base Path: {config.get('base_path')}")
            print(f"✓ Claude PM Path: {config.get('claude_pm_path')}")
            print(f"✓ Managed Path: {config.get('managed_path')}")
            
            # Verify paths are correctly set
            assert config.get('claude_pm_path') == str(custom_root)
            assert config.get('base_path') == str(custom_root.parent)
            assert config.get('managed_path') == str(custom_root.parent / "managed")
            print("✓ Path validation passed")
            print()
        
        # Test 3: CLI helper functions
        print("Test 3: CLI Helper Functions")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "cli-test-root"
            os.environ['CLAUDE_PM_ROOT'] = str(custom_root)
            
            claude_pm_path = get_claude_pm_path()
            managed_path = get_managed_path()
            framework_config = get_framework_config()
            
            print(f"✓ CLI Claude PM Path: {claude_pm_path}")
            print(f"✓ CLI Managed Path: {managed_path}")
            print(f"✓ CLI Base Path: {framework_config.get('base_path')}")
            
            # Verify CLI functions return correct paths
            assert str(claude_pm_path) == str(custom_root)
            assert str(managed_path) == str(custom_root.parent / "managed")
            print("✓ CLI function validation passed")
            print()
        
        # Test 4: Service configuration
        print("Test 4: Service Configuration")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "service-test-root"
            os.environ['CLAUDE_PM_ROOT'] = str(custom_root)
            
            # Create a project service with custom config
            config = Config()
            project_service = ProjectService(config.to_dict())
            
            print(f"✓ Service Base Path: {project_service.base_path}")
            print(f"✓ Service Claude PM Path: {project_service.claude_pm_path}")
            print(f"✓ Service Managed Path: {project_service.managed_path}")
            
            # Verify service uses custom paths
            assert str(project_service.claude_pm_path) == str(custom_root)
            assert str(project_service.managed_path) == str(custom_root.parent / "managed")
            print("✓ Service configuration validation passed")
            print()
        
        # Test 5: Path independence
        print("Test 5: Path Independence")
        print("-" * 40)
        
        # Test different custom roots
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "completely-different" / "path" / "root2"
            
            # Test first root
            os.environ['CLAUDE_PM_ROOT'] = str(root1)
            config1 = Config()
            
            # Test second root  
            os.environ['CLAUDE_PM_ROOT'] = str(root2)
            config2 = Config()
            
            print(f"✓ Root 1 Claude PM: {config1.get('claude_pm_path')}")
            print(f"✓ Root 1 Managed: {config1.get('managed_path')}")
            print(f"✓ Root 2 Claude PM: {config2.get('claude_pm_path')}")
            print(f"✓ Root 2 Managed: {config2.get('managed_path')}")
            
            # Verify different roots produce different paths
            assert config1.get('claude_pm_path') != config2.get('claude_pm_path')
            assert config1.get('managed_path') != config2.get('managed_path')
            assert config1.get('base_path') != config2.get('base_path')
            print("✓ Path independence validation passed")
            print()
        
        print("🎉 All tests passed! CLAUDE_PM_ROOT environment variable is working correctly.")
        print("\nUsage Examples:")
        print("export CLAUDE_PM_ROOT=/opt/claude-pm")
        print("export CLAUDE_PM_ROOT=/Users/username/custom-location/claude-pm")
        print("export CLAUDE_PM_ROOT=/tmp/test-environment/claude-pm")
        
    finally:
        # Restore original environment
        if original_env:
            os.environ['CLAUDE_PM_ROOT'] = original_env
        elif 'CLAUDE_PM_ROOT' in os.environ:
            del os.environ['CLAUDE_PM_ROOT']

if __name__ == "__main__":
    test_environment_config()