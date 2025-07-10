#!/usr/bin/env python3
"""
Environment Variable Migration Validation Script
===============================================

Validates that the Claude PM Framework works correctly with the new CLAUDE_MULTIAGENT_PM_ 
environment variables and that deprecation warnings are eliminated.
"""

import os
import sys
import tempfile
import subprocess
import json
from pathlib import Path

def setup_test_environment():
    """Set up test environment with new variables."""
    # Load migration commands
    migration_file = Path(__file__).parent.parent / "env_migration_commands.sh"
    if not migration_file.exists():
        print("❌ Migration commands file not found. Please run migrate_env_variables.py first.")
        return False
    
    # Parse export commands from migration file
    new_env_vars = {}
    with open(migration_file, 'r') as f:
        for line in f:
            if line.startswith('export CLAUDE_MULTIAGENT_PM_'):
                # Parse: export VAR_NAME="value"
                parts = line.strip().split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].replace('export ', '')
                    var_value = parts[1].strip('"')
                    new_env_vars[var_name] = var_value
    
    print(f"✓ Parsed {len(new_env_vars)} new environment variables")
    return new_env_vars

def test_configuration_with_new_vars(new_env_vars):
    """Test framework configuration with new environment variables."""
    print("\n=== Testing Framework Configuration with New Variables ===")
    
    # Create a test environment with new variables
    test_env = os.environ.copy()
    
    # Remove legacy variables to ensure clean test
    legacy_vars_to_remove = [k for k in test_env.keys() if k.startswith('CLAUDE_PM_')]
    for var in legacy_vars_to_remove:
        del test_env[var]
    
    # Add new variables
    test_env.update(new_env_vars)
    
    print(f"✓ Removed {len(legacy_vars_to_remove)} legacy variables from test environment")
    print(f"✓ Added {len(new_env_vars)} new variables to test environment")
    
    # Test framework configuration
    test_script = '''
import sys
import os
import logging

# Set up logging to capture warnings
import io
log_capture = io.StringIO()
handler = logging.StreamHandler(log_capture)
handler.setLevel(logging.WARNING)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
root_logger.addHandler(handler)

try:
    from claude_pm.core.config import Config
    config = Config()
    
    # Test basic configuration loading
    claude_pm_path = config.get("claude_pm_path")
    managed_path = config.get("managed_path")
    memory_enabled = config.get("memory_enabled")
    memory_service_url = config.get("memory_service_url")
    
    # Get captured logs
    log_output = log_capture.getvalue()
    
    # Output results
    print("=== Configuration Values ===")
    print(f"Claude PM Path: {claude_pm_path}")
    print(f"Managed Path: {managed_path}")
    print(f"Memory Enabled: {memory_enabled}")
    print(f"Memory Service URL: {memory_service_url}")
    
    print("\\n=== Warning Messages ===")
    if log_output.strip():
        print("WARNINGS DETECTED:")
        print(log_output)
        print("VALIDATION: FAILED - Warnings still present")
        sys.exit(1)
    else:
        print("No warnings detected")
        print("VALIDATION: PASSED - No deprecation warnings")
        sys.exit(0)
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''
    
    # Run the test in a subprocess with new environment
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("=== Test Output ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== Error Output ===")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Framework configuration test PASSED - No deprecation warnings!")
            return True
        else:
            print("❌ Framework configuration test FAILED - Warnings still present")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_configuration_with_legacy_vars():
    """Test framework configuration with legacy variables to confirm warnings."""
    print("\n=== Testing Framework Configuration with Legacy Variables ===")
    
    # Create test environment with only legacy variables
    test_env = os.environ.copy()
    
    # Remove any new variables
    new_vars_to_remove = [k for k in test_env.keys() if k.startswith('CLAUDE_MULTIAGENT_PM_')]
    for var in new_vars_to_remove:
        del test_env[var]
    
    print(f"✓ Removed {len(new_vars_to_remove)} new variables to ensure legacy-only test")
    
    # Test script that should produce warnings
    test_script = '''
import sys
import logging
import io

# Capture warnings
log_capture = io.StringIO()
handler = logging.StreamHandler(log_capture)
handler.setLevel(logging.WARNING)

root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
root_logger.addHandler(handler)

try:
    from claude_pm.core.config import Config
    config = Config()
    
    # Get captured logs
    log_output = log_capture.getvalue()
    
    print("=== Legacy Variable Test ===")
    if "legacy" in log_output.lower() or "deprecated" in log_output.lower():
        print("✓ Deprecation warnings detected as expected")
        print("Sample warning:", log_output.split("\\n")[0][:100] + "...")
        sys.exit(0)
    else:
        print("❌ No deprecation warnings found - this is unexpected")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Legacy variable test PASSED - Warnings detected as expected")
            return True
        else:
            print("❌ Legacy variable test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Legacy test failed: {e}")
        return False

def generate_validation_report():
    """Generate a validation report."""
    migration_file = Path(__file__).parent.parent / "env_migration_report.json"
    
    report = {
        "validation_timestamp": subprocess.check_output(['date'], text=True).strip(),
        "validation_status": "completed",
        "tests_performed": [
            "Environment variable parsing",
            "Framework configuration with new variables",
            "Framework configuration with legacy variables",
            "Deprecation warning validation"
        ],
        "migration_files_created": [
            "scripts/migrate_env_variables.py",
            "scripts/setup_env_migration.sh", 
            "scripts/validate_env_migration.py",
            "env_migration_commands.sh",
            "env_migration_report.json"
        ],
        "next_steps": [
            "Apply migration permanently using setup_env_migration.sh",
            "Remove legacy environment variables once confirmed working",
            "Update any deployment scripts or documentation",
            "Verify other team members apply the same migration"
        ]
    }
    
    validation_report_path = Path(__file__).parent.parent / "env_migration_validation_report.json"
    with open(validation_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Validation report saved to: {validation_report_path}")

def main():
    """Main validation routine."""
    print("=== Claude PM Framework Environment Variable Migration Validation ===\n")
    
    # Step 1: Set up test environment
    new_env_vars = setup_test_environment()
    if not new_env_vars:
        sys.exit(1)
    
    # Step 2: Test with legacy variables (should produce warnings)
    legacy_test_passed = test_configuration_with_legacy_vars()
    
    # Step 3: Test with new variables (should not produce warnings)
    new_test_passed = test_configuration_with_new_vars(new_env_vars)
    
    # Step 4: Generate validation report
    generate_validation_report()
    
    # Final results
    print("\n=== Validation Summary ===")
    print(f"Legacy variable warning test: {'✅ PASSED' if legacy_test_passed else '❌ FAILED'}")
    print(f"New variable clean test: {'✅ PASSED' if new_test_passed else '❌ FAILED'}")
    
    if legacy_test_passed and new_test_passed:
        print("\n🎉 Environment variable migration validation SUCCESSFUL!")
        print("\nThe migration is working correctly:")
        print("- Legacy variables still produce deprecation warnings")
        print("- New variables work without warnings")
        print("- Framework configuration loads correctly with both")
        
        print("\nTo complete the migration:")
        print("1. Run: scripts/setup_env_migration.sh")
        print("2. Choose option 2 to make changes permanent")
        print("3. Restart your terminal or source your shell config")
        print("4. Remove legacy variables once confirmed working")
        
        sys.exit(0)
    else:
        print("\n❌ Environment variable migration validation FAILED!")
        print("Please review the test output above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()