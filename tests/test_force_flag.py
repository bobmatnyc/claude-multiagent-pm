#!/usr/bin/env python3
"""
Test script to verify --force flag functionality.
"""
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path


def test_force_flag():
    """Test that --force flag suppresses INFO logging."""
    print("Testing --force flag functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save current directory
        original_cwd = Path.cwd()
        
        try:
            # Change to temp directory
            os.chdir(temp_path)
            
            # Run claude-pm init --force and capture output
            result = subprocess.run([
                str(original_cwd / "bin" / "claude-pm"),
                "init",
                "--force"
            ], capture_output=True, text=True, timeout=30)
            
            print("Return code:", result.returncode)
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
            
            # Check if INFO logging was suppressed
            if "INFO" in result.stderr:
                print("❌ FAILED: INFO logging was not suppressed")
                return False
            else:
                print("✅ SUCCESS: INFO logging was suppressed")
                return True
                
        finally:
            # Restore original directory
            os.chdir(original_cwd)


if __name__ == "__main__":
    success = test_force_flag()
    sys.exit(0 if success else 1)