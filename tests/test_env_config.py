#!/usr/bin/env python3
"""
Test script to verify CLAUDE_PM_ROOT environment variable configuration works
"""

import os
import sys
from pathlib import Path

# Add the claude_pm module to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.core.config import Config


def test_environment_configuration():
    """Test the environment variable configuration"""
    print("🧪 Testing CLAUDE_PM_ROOT Environment Configuration")
    print("=" * 60)
    
    # Test 1: Default configuration (no env var set)
    print("\n1️⃣ Testing default configuration (no CLAUDE_PM_ROOT set)")
    
    # Temporarily unset the environment variable if it exists
    original_root = os.environ.get("CLAUDE_PM_ROOT")
    if "CLAUDE_PM_ROOT" in os.environ:
        del os.environ["CLAUDE_PM_ROOT"]
    
    config = Config()
    claude_pm_path = config.get("claude_pm_path")
    managed_path = config.get("managed_path")
    
    print(f"   Claude PM Path: {claude_pm_path}")
    print(f"   Managed Path: {managed_path}")
    print(f"   Expected Default: {Path.home() / 'Projects' / 'Claude-PM'}")
    
    default_expected = str(Path.home() / "Projects" / "Claude-PM")
    if claude_pm_path == default_expected:
        print("   ✅ Default path configuration PASSED")
    else:
        print("   ❌ Default path configuration FAILED")
    
    # Test 2: Custom environment variable
    print("\n2️⃣ Testing custom CLAUDE_PM_ROOT configuration")
    
    custom_root = "/tmp/test-claude-pm"
    os.environ["CLAUDE_PM_ROOT"] = custom_root
    
    # Create new config to pick up env var
    config = Config()
    claude_pm_path = config.get("claude_pm_path")
    managed_path = config.get("managed_path")
    
    print(f"   CLAUDE_PM_ROOT set to: {custom_root}")
    print(f"   Claude PM Path: {claude_pm_path}")
    print(f"   Managed Path: {managed_path}")
    
    if claude_pm_path == custom_root:
        print("   ✅ Custom environment configuration PASSED")
    else:
        print("   ❌ Custom environment configuration FAILED")
    
    # Test 3: Verify automated health monitor uses env var
    print("\n3️⃣ Testing automated health monitor path configuration")
    
    try:
        from scripts.automated_health_monitor import ClaudePMHealthMonitor
        
        # This should now use the environment variable
        monitor = ClaudePMHealthMonitor()
        monitor_path = str(monitor.claude_pm_path)
        
        print(f"   Health Monitor Claude PM Path: {monitor_path}")
        
        if monitor_path == custom_root:
            print("   ✅ Health monitor environment configuration PASSED")
        else:
            print("   ❌ Health monitor environment configuration FAILED")
            
    except Exception as e:
        print(f"   ⚠️  Could not test health monitor: {e}")
    
    # Restore original environment variable
    if original_root:
        os.environ["CLAUDE_PM_ROOT"] = original_root
    elif "CLAUDE_PM_ROOT" in os.environ:
        del os.environ["CLAUDE_PM_ROOT"]
    
    print("\n🎯 Configuration Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_environment_configuration()