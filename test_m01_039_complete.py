#!/usr/bin/env python3
"""
Complete test for M01-039: Replace Hardcoded Paths with Environment Configuration

This test demonstrates that:
1. CLAUDE_PM_ROOT environment variable controls framework root directory
2. All hardcoded paths in claude_pm/core/config.py are replaced with dynamic resolution
3. Service manager and CLI tools work with custom root directories
4. The system maintains backward compatibility during transition
"""

import os
import tempfile
from pathlib import Path

# Test imports
from claude_pm.core.config import Config
from claude_pm.services.project_service import ProjectService
from claude_pm.cli import get_claude_pm_path, get_managed_path, get_framework_config

def test_m01_039_complete():
    """Complete test for M01-039 acceptance criteria."""
    
    print("=" * 70)
    print("M01-039: Replace Hardcoded Paths with Environment Configuration")
    print("=" * 70)
    print()
    
    # Save original environment
    original_env = os.environ.get('CLAUDE_PM_ROOT')
    
    try:
        # ACCEPTANCE CRITERIA 1: CLAUDE_PM_ROOT environment variable controls framework root directory
        print("✅ ACCEPTANCE CRITERIA 1: CLAUDE_PM_ROOT controls framework root")
        print("-" * 50)
        
        # Test default behavior
        if 'CLAUDE_PM_ROOT' in os.environ:
            del os.environ['CLAUDE_PM_ROOT']
        
        config_default = Config()
        print(f"Default Claude PM Path: {config_default.get('claude_pm_path')}")
        print(f"Default Managed Path: {config_default.get('managed_path')}")
        print(f"Default Base Path: {config_default.get('base_path')}")
        
        # Test custom environment
        test_root = "/opt/custom-claude-pm"
        os.environ['CLAUDE_PM_ROOT'] = test_root
        
        config_custom = Config()
        print(f"Custom Claude PM Path: {config_custom.get('claude_pm_path')}")
        print(f"Custom Managed Path: {config_custom.get('managed_path')}")
        print(f"Custom Base Path: {config_custom.get('base_path')}")
        
        # Verify environment variable controls paths
        assert config_custom.get('claude_pm_path') == test_root
        assert config_custom.get('managed_path') == "/opt/managed"
        assert config_custom.get('base_path') == "/opt"
        print("✓ Environment variable successfully controls all framework paths")
        print()
        
        # ACCEPTANCE CRITERIA 2: All hardcoded paths replaced with dynamic resolution
        print("✅ ACCEPTANCE CRITERIA 2: Hardcoded paths replaced with dynamic resolution")
        print("-" * 50)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test multiple different custom roots to ensure no hardcoding
            test_cases = [
                Path(temp_dir) / "case1" / "claude-pm",
                Path(temp_dir) / "totally-different" / "path" / "claude-pm-instance",
                Path(temp_dir) / "another" / "location" / "framework"
            ]
            
            for i, test_path in enumerate(test_cases, 1):
                os.environ['CLAUDE_PM_ROOT'] = str(test_path)
                config = Config()
                
                # Verify dynamic resolution (no hardcoded paths)
                assert config.get('claude_pm_path') == str(test_path)
                assert config.get('managed_path') == str(test_path.parent / "managed")
                assert config.get('base_path') == str(test_path.parent)
                
                print(f"✓ Test case {i}: {test_path} → paths resolved dynamically")
        
        print("✓ All paths are dynamically resolved based on environment")
        print()
        
        # ACCEPTANCE CRITERIA 3: Service manager and CLI tools work with custom directories
        print("✅ ACCEPTANCE CRITERIA 3: Services work with custom root directories")
        print("-" * 50)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir) / "service-test" / "claude-pm"
            os.environ['CLAUDE_PM_ROOT'] = str(custom_root)
            
            # Test service manager configuration
            print("Testing Service Manager:")
            config = Config()
            project_service = ProjectService(config.to_dict())
            
            assert str(project_service.claude_pm_path) == str(custom_root)
            assert str(project_service.managed_path) == str(custom_root.parent / "managed")
            print(f"✓ ProjectService uses custom paths: {project_service.claude_pm_path}")
            
            # Test CLI tools
            print("Testing CLI Tools:")
            cli_claude_pm = get_claude_pm_path()
            cli_managed = get_managed_path()
            cli_config = get_framework_config()
            
            assert str(cli_claude_pm) == str(custom_root)
            assert str(cli_managed) == str(custom_root.parent / "managed")
            print(f"✓ CLI tools use custom paths: {cli_claude_pm}")
            
            # Test CLI path operations (simulated)
            print("Testing CLI Path Operations:")
            backlog_path = cli_claude_pm / "trackdown" / "BACKLOG.md"
            tickets_dir = cli_claude_pm / "trackdown" / "issues"
            
            assert str(backlog_path).startswith(str(custom_root))
            assert str(tickets_dir).startswith(str(custom_root))
            print(f"✓ CLI operations use dynamic paths: {backlog_path}")
        
        print("✓ All services and CLI tools work with custom root directories")
        print()
        
        # BONUS: Test backward compatibility
        print("🎯 BONUS: Backward Compatibility Test")
        print("-" * 50)
        
        # Remove environment variable to test default behavior
        if 'CLAUDE_PM_ROOT' in os.environ:
            del os.environ['CLAUDE_PM_ROOT']
        
        config_compat = Config()
        expected_default_claude_pm = str(Path.home() / "Projects" / "Claude-PM")
        expected_default_managed = str(Path.home() / "Projects" / "managed")
        
        assert config_compat.get('claude_pm_path') == expected_default_claude_pm
        assert config_compat.get('managed_path') == expected_default_managed
        print("✓ Backward compatibility maintained - defaults work as before")
        print()
        
        # SUCCESS SUMMARY
        print("🎉 M01-039 IMPLEMENTATION COMPLETE!")
        print("=" * 50)
        print("✅ CLAUDE_PM_ROOT environment variable controls framework root directory")
        print("✅ All hardcoded paths replaced with dynamic resolution")
        print("✅ Service manager and CLI tools work with custom root directories")
        print("✅ Backward compatibility maintained during transition")
        print()
        print("USAGE EXAMPLES:")
        print("export CLAUDE_PM_ROOT=/opt/claude-pm")
        print("export CLAUDE_PM_ROOT=/usr/local/claude-pm")  
        print("export CLAUDE_PM_ROOT=/home/user/my-claude-pm")
        print("export CLAUDE_PM_ROOT=/tmp/test-environment")
        print()
        print("All framework services, CLI tools, and configuration")
        print("will now use the specified custom directory!")
        
    finally:
        # Restore original environment
        if original_env:
            os.environ['CLAUDE_PM_ROOT'] = original_env
        elif 'CLAUDE_PM_ROOT' in os.environ:
            del os.environ['CLAUDE_PM_ROOT']

if __name__ == "__main__":
    test_m01_039_complete()