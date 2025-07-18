#!/usr/bin/env python3
"""
Quick test script to validate auto-setup functionality.

This script performs rapid tests to verify:
1. CLI auto-creates .claude-pm when missing
2. Orchestration logging creates directories when needed
3. No errors occur during normal operation
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# Framework path
framework_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_path))


def test_cli_auto_setup():
    """Test CLI auto-setup in a fresh directory."""
    print("Testing CLI auto-setup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Run claude-pm --version
        result = subprocess.run(
            [sys.executable, str(framework_path / "bin" / "claude-pm"), "--version"],
            capture_output=True,
            text=True
        )
        
        # Check if .claude-pm was created
        if Path(".claude-pm").exists():
            print("✅ CLI auto-created .claude-pm directory")
            
            # Check subdirectories
            expected = ["logs", "agents", "config", "templates", "memory", "framework_backups"]
            for subdir in expected:
                if Path(f".claude-pm/{subdir}").exists():
                    print(f"  ✓ Created {subdir}/")
                else:
                    print(f"  ✗ Missing {subdir}/")
        else:
            print("❌ CLI did NOT create .claude-pm directory")
            
        print(f"CLI output: {result.stdout}")
        if result.stderr:
            print(f"CLI errors: {result.stderr}")


def test_orchestration_auto_setup():
    """Test orchestration logging auto-setup."""
    print("\nTesting orchestration auto-setup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        try:
            # Import orchestration and create logger
            from claude_pm.orchestration.logging_setup import get_orchestration_logger
            
            logger = get_orchestration_logger("test")
            logger.info("Test message")
            
            # Check if directories were created
            if Path(".claude-pm/logs").exists():
                print("✅ Orchestration auto-created .claude-pm/logs directory")
                
                # Check if log file exists
                if Path(".claude-pm/logs/orchestration.log").exists():
                    print("  ✓ Created orchestration.log")
                else:
                    print("  ✗ Missing orchestration.log")
            else:
                print("❌ Orchestration did NOT create directories")
                
        except Exception as e:
            print(f"❌ Orchestration import failed: {e}")


def test_permission_fallback():
    """Test fallback when permissions are denied."""
    print("\nTesting permission denied fallback...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        restricted_dir = Path(tmpdir) / "restricted"
        restricted_dir.mkdir()
        os.chdir(restricted_dir)
        
        # Make directory read-only
        os.chmod(restricted_dir, 0o555)
        
        try:
            from claude_pm.orchestration.logging_setup import get_orchestration_logger
            import warnings
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                logger = get_orchestration_logger("test")
                
                # Check for warning
                if any("Could not create .claude-pm" in str(warning.message) for warning in w):
                    print("✅ Permission denied handled gracefully with warning")
                else:
                    print("⚠️  No warning issued for permission denied")
                    
        except Exception as e:
            print(f"❌ Permission test failed: {e}")
        finally:
            # Restore permissions
            os.chmod(restricted_dir, 0o755)


def main():
    """Run quick tests."""
    print("🚀 Quick Auto-Setup Validation")
    print("=" * 50)
    
    # Save original directory
    original_cwd = os.getcwd()
    
    try:
        test_cli_auto_setup()
        test_orchestration_auto_setup()
        test_permission_fallback()
        
        print("\n✅ Quick tests completed!")
        
    finally:
        # Restore original directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()