#!/usr/bin/env python3
"""
Validate EP-0043 Refactoring - Safe local testing
Ensures all refactored modules work correctly without affecting system installation
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

def validate_imports():
    """Validate all refactored module imports"""
    print_header("1. Import Validation")
    
    tests = {
        "ParentDirectoryManager": lambda: importlib.import_module('claude_pm.services.parent_directory_manager').ParentDirectoryManager,
        "AgentRegistry": lambda: importlib.import_module('claude_pm.core.agent_registry').AgentRegistry,
        "AgentMetadata": lambda: importlib.import_module('claude_pm.core.agent_registry').AgentMetadata,
        "BackwardsCompatibleOrchestrator": lambda: importlib.import_module('claude_pm.orchestration').BackwardsCompatibleOrchestrator,
    }
    
    all_passed = True
    for name, import_func in tests.items():
        try:
            import_func()
            test_result(f"Import {name}", True)
        except Exception as e:
            test_result(f"Import {name}", False, str(e))
            all_passed = False
    
    return all_passed

def validate_module_structure():
    """Validate new module structure exists"""
    print_header("2. Module Structure Validation")
    
    expected_modules = [
        # Parent Directory Manager modules
        "claude_pm/services/parent_directory/__init__.py",
        "claude_pm/services/parent_directory/manager.py",
        "claude_pm/services/parent_directory/backup_manager.py",
        "claude_pm/services/parent_directory/template_deployer.py",
        "claude_pm/services/parent_directory/framework_protector.py",
        "claude_pm/services/parent_directory/version_control_helper.py",
        
        # Agent Registry modules
        "claude_pm/core/agent_registry/__init__.py",
        "claude_pm/core/agent_registry/registry.py",
        "claude_pm/core/agent_registry/discovery.py",
        "claude_pm/core/agent_registry/models.py",
        "claude_pm/core/agent_registry/validation.py",
        "claude_pm/core/agent_registry/cache.py",
        
        # Orchestrator modules
        "claude_pm/orchestration/orchestrator/__init__.py",
        "claude_pm/orchestration/orchestrator/orchestrator.py",
        "claude_pm/orchestration/orchestrator/agent_coordinator.py",
        "claude_pm/orchestration/orchestrator/task_delegator.py",
        "claude_pm/orchestration/orchestrator/result_aggregator.py",
    ]
    
    all_passed = True
    for module_path in expected_modules:
        full_path = project_root / module_path
        exists = full_path.exists()
        test_result(f"Module exists: {module_path}", exists)
        if not exists:
            all_passed = False
    
    return all_passed

def validate_file_sizes():
    """Validate that refactored files are under 1000 lines"""
    print_header("3. File Size Validation")
    
    files_to_check = [
        "claude_pm/services/parent_directory_manager.py",
        "claude_pm/core/agent_registry.py",
        "claude_pm/core/agent_registry_sync.py",
        "claude_pm/orchestration/backwards_compatible_orchestrator.py",
    ]
    
    all_passed = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                line_count = len(f.readlines())
            passed = line_count <= 1000
            test_result(f"{file_path}: {line_count} lines", passed)
            if not passed:
                all_passed = False
        else:
            test_result(f"{file_path} exists", False)
            all_passed = False
    
    return all_passed

def validate_api_compatibility():
    """Validate API compatibility of refactored modules"""
    print_header("4. API Compatibility Validation")
    
    all_passed = True
    
    # Test ParentDirectoryManager instantiation
    try:
        from claude_pm.services.parent_directory_manager import ParentDirectoryManager
        # Don't actually instantiate to avoid side effects
        test_result("ParentDirectoryManager class accessible", True)
    except Exception as e:
        test_result("ParentDirectoryManager class accessible", False, str(e))
        all_passed = False
    
    # Test AgentRegistry methods exist
    try:
        from claude_pm.core.agent_registry import AgentRegistry
        methods = ['listAgents', 'loadAgent', 'getAgentMetadata']
        for method in methods:
            has_method = hasattr(AgentRegistry, method)
            test_result(f"AgentRegistry.{method} exists", has_method)
            if not has_method:
                all_passed = False
    except Exception as e:
        test_result("AgentRegistry methods check", False, str(e))
        all_passed = False
    
    return all_passed

def generate_report(results):
    """Generate a summary report"""
    print_header("Test Summary")
    
    total_passed = sum(1 for r in results.values() if r)
    total_tests = len(results)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {GREEN}{total_passed}{NC}")
    print(f"Failed: {RED}{total_tests - total_passed}{NC}")
    
    if total_passed == total_tests:
        print(f"\n{GREEN}✅ All validations passed! Safe to proceed with deployment.{NC}")
        return 0
    else:
        print(f"\n{RED}❌ Some validations failed. Please fix issues before deployment.{NC}")
        return 1

def main():
    """Run all validation tests"""
    print(f"{YELLOW}EP-0043 Refactoring Validation - Local Test{NC}")
    print(f"Project Root: {project_root}")
    
    results = {
        "imports": validate_imports(),
        "structure": validate_module_structure(),
        "file_sizes": validate_file_sizes(),
        "api_compatibility": validate_api_compatibility(),
    }
    
    return generate_report(results)

if __name__ == "__main__":
    sys.exit(main())