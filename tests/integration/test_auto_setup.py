#!/usr/bin/env python3
"""
Comprehensive test script for auto-setup functionality.

Tests both CLI auto-setup and orchestration logging auto-setup in various scenarios:
1. Fresh directory with no .claude-pm
2. Directory with existing .claude-pm
3. Permission-denied scenario
4. CLI command usage
5. Direct orchestration import
"""

import os
import sys
import shutil
import tempfile
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add framework to path for imports
framework_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_path))

# Test results tracking
test_results = []


def log_test(test_name, status, details=""):
    """Log test result."""
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    # Color output
    color = "\033[92m" if status == "PASS" else "\033[91m"  # Green for pass, red for fail
    reset = "\033[0m"
    
    print(f"{color}[{status}]{reset} {test_name}")
    if details:
        print(f"      {details}")


def test_fresh_directory():
    """Test auto-setup in a fresh directory with no .claude-pm."""
    print("\n=== Testing Fresh Directory Auto-Setup ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "fresh_project"
        test_dir.mkdir()
        
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Test 1: CLI command in fresh directory
            result = subprocess.run(
                [sys.executable, str(framework_path / "bin" / "claude-pm"), "--version"],
                capture_output=True,
                text=True
            )
            
            if (test_dir / ".claude-pm").exists():
                log_test("CLI auto-creates .claude-pm in fresh directory", "PASS")
                
                # Check subdirectories
                expected_dirs = ["logs", "agents", "config", "templates", "memory", "framework_backups"]
                missing = []
                for subdir in expected_dirs:
                    if not (test_dir / ".claude-pm" / subdir).exists():
                        missing.append(subdir)
                
                if not missing:
                    log_test("CLI creates all required subdirectories", "PASS")
                else:
                    log_test("CLI creates all required subdirectories", "FAIL", f"Missing: {missing}")
                
                # Check project config
                project_config = test_dir / ".claude-pm" / "config" / "project.json"
                if project_config.exists():
                    with open(project_config) as f:
                        config = json.load(f)
                    if config.get("auto_initialized"):
                        log_test("CLI creates project config with auto_initialized flag", "PASS")
                    else:
                        log_test("CLI creates project config with auto_initialized flag", "FAIL", "Flag not set")
                else:
                    log_test("CLI creates project config with auto_initialized flag", "FAIL", "Config not created")
            else:
                log_test("CLI auto-creates .claude-pm in fresh directory", "FAIL", "Directory not created")
            
            # Test 2: Direct orchestration import
            # Clean up first
            if (test_dir / ".claude-pm").exists():
                shutil.rmtree(test_dir / ".claude-pm")
            
            # Import orchestration module
            try:
                from claude_pm.orchestration.logging_setup import get_orchestration_logger
                logger = get_orchestration_logger("test", working_directory=test_dir)
                
                if (test_dir / ".claude-pm").exists():
                    log_test("Orchestration auto-creates .claude-pm on import", "PASS")
                    
                    # Check if logs directory was created
                    if (test_dir / ".claude-pm" / "logs").exists():
                        log_test("Orchestration creates logs directory", "PASS")
                    else:
                        log_test("Orchestration creates logs directory", "FAIL")
                else:
                    log_test("Orchestration auto-creates .claude-pm on import", "FAIL")
                    
            except Exception as e:
                log_test("Orchestration auto-creates .claude-pm on import", "FAIL", str(e))
                
        finally:
            os.chdir(original_cwd)


def test_existing_directory():
    """Test auto-setup behavior with existing .claude-pm directory."""
    print("\n=== Testing Existing Directory Behavior ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "existing_project"
        test_dir.mkdir()
        
        # Create existing .claude-pm with partial structure
        claude_pm_dir = test_dir / ".claude-pm"
        claude_pm_dir.mkdir()
        (claude_pm_dir / "logs").mkdir()
        
        # Create a marker file
        marker = claude_pm_dir / "existing_marker.txt"
        marker.write_text("This directory already existed")
        
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Test CLI behavior
            result = subprocess.run(
                [sys.executable, str(framework_path / "bin" / "claude-pm"), "--version"],
                capture_output=True,
                text=True
            )
            
            # Check that marker file still exists
            if marker.exists():
                log_test("CLI preserves existing .claude-pm contents", "PASS")
            else:
                log_test("CLI preserves existing .claude-pm contents", "FAIL", "Marker file deleted")
            
            # Check that missing directories were created
            if (claude_pm_dir / "agents").exists():
                log_test("CLI creates missing subdirectories in existing .claude-pm", "PASS")
            else:
                log_test("CLI creates missing subdirectories in existing .claude-pm", "FAIL")
                
        finally:
            os.chdir(original_cwd)


def test_permission_denied():
    """Test fallback behavior when permissions are denied."""
    print("\n=== Testing Permission Denied Fallback ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "restricted_project"
        test_dir.mkdir()
        
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Make directory read-only to simulate permission denied
            os.chmod(test_dir, 0o555)
            
            # Test orchestration fallback
            try:
                from claude_pm.orchestration.logging_setup import get_orchestration_logger
                import warnings
                
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    logger = get_orchestration_logger("test", working_directory=test_dir)
                    
                    # Check if warning was issued
                    if any("Could not create .claude-pm" in str(warning.message) for warning in w):
                        log_test("Orchestration issues warning on permission denied", "PASS")
                        
                        # Check if fallback to temp directory worked
                        if any("claude-pm-logs" in str(warning.message) for warning in w):
                            log_test("Orchestration falls back to temp directory", "PASS")
                        else:
                            log_test("Orchestration falls back to temp directory", "FAIL", "No temp dir in warning")
                    else:
                        log_test("Orchestration issues warning on permission denied", "FAIL", "No warning issued")
                        
            except Exception as e:
                log_test("Orchestration handles permission denied gracefully", "FAIL", str(e))
            
        finally:
            # Restore permissions
            os.chmod(test_dir, 0o755)
            os.chdir(original_cwd)


def test_cli_commands():
    """Test auto-setup with various CLI commands."""
    print("\n=== Testing CLI Commands Auto-Setup ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "cli_test"
        test_dir.mkdir()
        
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Test various commands that should trigger auto-setup
            commands = [
                ["--version"],
                ["--help"],
                ["--system-info"],
                ["--deployment-info"],
            ]
            
            for cmd in commands:
                # Clean up between tests
                if (test_dir / ".claude-pm").exists():
                    shutil.rmtree(test_dir / ".claude-pm")
                
                result = subprocess.run(
                    [sys.executable, str(framework_path / "bin" / "claude-pm")] + cmd,
                    capture_output=True,
                    text=True
                )
                
                if (test_dir / ".claude-pm").exists():
                    log_test(f"CLI auto-setup works with {' '.join(cmd)}", "PASS")
                else:
                    log_test(f"CLI auto-setup works with {' '.join(cmd)}", "FAIL")
            
            # Test cleanup command (should NOT create .claude-pm)
            if (test_dir / ".claude-pm").exists():
                shutil.rmtree(test_dir / ".claude-pm")
            
            result = subprocess.run(
                [sys.executable, str(framework_path / "bin" / "claude-pm"), "--cleanup", "--help"],
                capture_output=True,
                text=True
            )
            
            if not (test_dir / ".claude-pm").exists():
                log_test("CLI cleanup command does NOT trigger auto-setup", "PASS")
            else:
                log_test("CLI cleanup command does NOT trigger auto-setup", "FAIL", ".claude-pm created")
                
        finally:
            os.chdir(original_cwd)


def test_orchestration_direct_import():
    """Test orchestration logging auto-setup via direct import."""
    print("\n=== Testing Direct Orchestration Import ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "import_test"
        test_dir.mkdir()
        
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Test importing various orchestration modules
            modules = [
                "claude_pm.orchestration.backwards_compatible_orchestrator",
                "claude_pm.orchestration.context_manager",
                "claude_pm.orchestration.message_bus",
            ]
            
            for module_name in modules:
                # Clean up between tests
                if (test_dir / ".claude-pm").exists():
                    shutil.rmtree(test_dir / ".claude-pm")
                
                try:
                    # Import module
                    module = __import__(module_name, fromlist=[''])
                    
                    # The import alone might not trigger setup, but using logging should
                    from claude_pm.orchestration.logging_setup import get_orchestration_logger
                    logger = get_orchestration_logger(module_name, working_directory=test_dir)
                    logger.info("Test log message")
                    
                    if (test_dir / ".claude-pm" / "logs").exists():
                        log_test(f"Import {module_name.split('.')[-1]} creates log directory", "PASS")
                        
                        # Check if log file was created
                        log_file = test_dir / ".claude-pm" / "logs" / "orchestration.log"
                        if log_file.exists():
                            log_test(f"Import {module_name.split('.')[-1]} creates log file", "PASS")
                        else:
                            log_test(f"Import {module_name.split('.')[-1]} creates log file", "FAIL")
                    else:
                        log_test(f"Import {module_name.split('.')[-1]} creates log directory", "FAIL")
                        
                except Exception as e:
                    log_test(f"Import {module_name.split('.')[-1]}", "FAIL", str(e))
                    
        finally:
            os.chdir(original_cwd)


def test_no_regression():
    """Test that existing functionality still works."""
    print("\n=== Testing No Regression ===")
    
    # Test init command still works
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "init_test"
        test_dir.mkdir()
        
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        try:
            # Run init command
            result = subprocess.run(
                [sys.executable, str(framework_path / "bin" / "claude-pm"), "init", "--force"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log_test("Init command still works", "PASS")
            else:
                log_test("Init command still works", "FAIL", f"Exit code: {result.returncode}")
            
            # Check that directories were created properly
            if (test_dir / ".claude-pm").exists():
                log_test("Init creates .claude-pm directory", "PASS")
            else:
                log_test("Init creates .claude-pm directory", "FAIL")
                
        except subprocess.TimeoutExpired:
            log_test("Init command completes within timeout", "FAIL", "Command timed out")
        finally:
            os.chdir(original_cwd)


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\nFailed tests:")
        for result in test_results:
            if result["status"] == "FAIL":
                print(f"  - {result['test']}")
                if result["details"]:
                    print(f"    Details: {result['details']}")
    
    # Save detailed results
    results_file = framework_path / "test_auto_setup_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": passed/total*100
            },
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")


def main():
    """Run all tests."""
    print("🧪 Claude PM Auto-Setup Test Suite")
    print("=" * 60)
    
    # Run all test suites
    test_fresh_directory()
    test_existing_directory()
    test_permission_denied()
    test_cli_commands()
    test_orchestration_direct_import()
    test_no_regression()
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    main()