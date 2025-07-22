#!/usr/bin/env python3
"""
Test Docker installations for claude-multiagent-pm
"""

import sys
import subprocess
import traceback

# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_header(title):
    """Print a formatted header"""
    print(f"\n{YELLOW}{'='*60}{NC}")
    print(f"{YELLOW}{title}{NC}")
    print(f"{YELLOW}{'='*60}{NC}")

def test_result(test_name, passed, error=None):
    """Print test result"""
    if passed:
        print(f"{GREEN}✓{NC} {test_name}")
        return True
    else:
        print(f"{RED}✗{NC} {test_name}")
        if error:
            print(f"  Error: {error}")
        return False

def test_pypi_installation():
    """Test PyPI installation in Docker"""
    print_header("Testing PyPI Installation")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Import claude_pm
    try:
        import claude_pm
        test_result("Import claude_pm", True)
        tests_passed += 1
    except Exception as e:
        test_result("Import claude_pm", False, str(e))
        tests_failed += 1
    
    # Test 2: Check version
    try:
        import claude_pm
        version = claude_pm.__version__
        test_result(f"Check version: {version}", True)
        tests_passed += 1
    except Exception as e:
        test_result("Check version", False, str(e))
        tests_failed += 1
    
    # Test 3: Import ai-trackdown-pytools
    try:
        import ai_trackdown
        test_result("Import ai-trackdown-pytools", True)
        tests_passed += 1
    except Exception as e:
        test_result("Import ai-trackdown-pytools", False, str(e))
        tests_failed += 1
    
    # Test 4: CLI command
    try:
        result = subprocess.run(['claude-pm', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            test_result(f"CLI command works: {result.stdout.strip()}", True)
            tests_passed += 1
        else:
            test_result("CLI command works", False, f"Exit code: {result.returncode}, Error: {result.stderr}")
            tests_failed += 1
    except Exception as e:
        test_result("CLI command works", False, str(e))
        tests_failed += 1
    
    # Test 5: Core imports
    try:
        from claude_pm.core import AgentRegistry
        from claude_pm.services import ParentDirectoryManager
        test_result("Core imports work", True)
        tests_passed += 1
    except Exception as e:
        test_result("Core imports work", False, str(e))
        tests_failed += 1
    
    # Test 6: Check for dependency conflicts
    try:
        result = subprocess.run(['pip', 'check'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            test_result("No dependency conflicts", True)
            tests_passed += 1
        else:
            test_result("No dependency conflicts", False, result.stdout)
            tests_failed += 1
    except Exception as e:
        test_result("No dependency conflicts", False, str(e))
        tests_failed += 1
    
    return tests_passed, tests_failed

def test_npm_installation():
    """Test NPM installation (if Node.js is available)"""
    print_header("Testing NPM Installation")
    
    tests_passed = 0
    tests_failed = 0
    
    # Check if Node.js is available
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("Node.js not available in this container, skipping NPM tests")
            return tests_passed, tests_failed
    except:
        print("Node.js not available in this container, skipping NPM tests")
        return tests_passed, tests_failed
    
    # Test 1: Check if claude-pm command exists
    try:
        result = subprocess.run(['which', 'claude-pm'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            test_result(f"claude-pm command found: {result.stdout.strip()}", True)
            tests_passed += 1
        else:
            test_result("claude-pm command found", False, "Command not found")
            tests_failed += 1
    except Exception as e:
        test_result("claude-pm command found", False, str(e))
        tests_failed += 1
    
    # Test 2: Run claude-pm version
    try:
        result = subprocess.run(['claude-pm', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            test_result(f"NPM CLI version: {result.stdout.strip()}", True)
            tests_passed += 1
        else:
            test_result("NPM CLI version", False, f"Exit code: {result.returncode}")
            tests_failed += 1
    except Exception as e:
        test_result("NPM CLI version", False, str(e))
        tests_failed += 1
    
    return tests_passed, tests_failed

def main():
    """Run all tests"""
    print(f"{YELLOW}Claude PM Docker Installation Tests{NC}")
    
    total_passed = 0
    total_failed = 0
    
    # Test PyPI installation
    passed, failed = test_pypi_installation()
    total_passed += passed
    total_failed += failed
    
    # Test NPM installation
    passed, failed = test_npm_installation()
    total_passed += passed
    total_failed += failed
    
    # Summary
    print_header("Test Summary")
    print(f"\nTotal Tests: {total_passed + total_failed}")
    print(f"Passed: {GREEN}{total_passed}{NC}")
    print(f"Failed: {RED}{total_failed}{NC}")
    
    if total_failed == 0:
        print(f"\n{GREEN}✅ All tests passed!{NC}")
        return 0
    else:
        print(f"\n{RED}❌ Some tests failed.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())