#!/usr/bin/env python3
"""
Framework Integrity Test Runner
===============================

Runs tests to ensure framework integrity, including:
- Template handlebars variable validation
- VERSION file consistency
- Configuration integrity

This script is designed to be run in CI/CD pipelines or before deployments
to catch template corruption and configuration issues early.
"""

import sys
import subprocess
from pathlib import Path


def run_framework_template_tests():
    """Run framework template integrity tests."""
    print("🧪 Running Framework Template Tests...")
    print("-" * 50)
    
    # Run the template tests
    test_script = Path(__file__).parent.parent / "test_framework_template.py"
    result = subprocess.run([sys.executable, str(test_script)], 
                          capture_output=False, text=True)
    
    return result.returncode == 0


def run_version_consistency_tests():
    """Run version consistency tests."""
    print("\n🔍 Running Version Consistency Tests...")
    print("-" * 50)
    
    framework_root = Path(__file__).parent.parent
    
    # Check VERSION file exists and is valid
    version_file = framework_root / "VERSION"
    if not version_file.exists():
        print("❌ VERSION file not found!")
        return False
    
    version_content = version_file.read_text().strip()
    if not version_content:
        print("❌ VERSION file is empty!")
        return False
    
    print(f"✅ VERSION file contains: {version_content}")
    
    # Check package.json consistency
    package_file = framework_root / "package.json"
    if package_file.exists():
        import json
        with open(package_file) as f:
            pkg_data = json.load(f)
        
        pkg_version = pkg_data.get('version')
        if pkg_version != version_content:
            print(f"⚠️  VERSION file ({version_content}) != package.json ({pkg_version})")
            print("   Consider synchronizing versions")
        else:
            print(f"✅ package.json version matches: {pkg_version}")
    
    # Check Python package version
    init_file = framework_root / "claude_pm" / "__init__.py"
    if init_file.exists():
        init_content = init_file.read_text()
        import re
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
        if version_match:
            py_version = version_match.group(1)
            if py_version != version_content:
                print(f"⚠️  VERSION file ({version_content}) != Python package ({py_version})")
                print("   Consider synchronizing versions")
            else:
                print(f"✅ Python package version matches: {py_version}")
    
    return True


def run_template_deployment_test():
    """Run a test deployment to validate template processing."""
    print("\n🚀 Running Template Deployment Test...")
    print("-" * 50)
    
    try:
        # Test template processing without module import
        framework_root = Path(__file__).parent.parent
        
        # Test template variable generation
        test_variables = {
            "FRAMEWORK_VERSION": "0.4.6",
            "DEPLOYMENT_DATE": "2025-07-11T14:00:00.000000",
            "PLATFORM": "darwin", 
            "PYTHON_CMD": "python3",
            "LAST_UPDATED": "2025-07-11T14:00:00.000000",
            "CLAUDE_MD_VERSION": "0.4.6-001"
        }
        
        # Read framework template
        framework_template = framework_root / "framework" / "CLAUDE.md"
        if not framework_template.exists():
            print("❌ Framework template not found!")
            return False
        
        template_content = framework_template.read_text()
        
        # Check that all required variables are in template
        missing_vars = []
        for var_name in test_variables.keys():
            if f"{{{{{var_name}}}}}" not in template_content:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Missing handlebars variables: {', '.join(missing_vars)}")
            return False
        
        # Check that no hardcoded versions remain
        import re
        hardcoded_patterns = [
            r"CLAUDE_MD_VERSION:\s*[\d\.-]+",
            r"FRAMEWORK_VERSION:\s*[\d\.-]+", 
            r"\*\*Version\*\*:\s*[\d\.-]+",
        ]
        
        hardcoded_found = []
        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, template_content)
            if matches:
                hardcoded_found.extend(matches)
        
        if hardcoded_found:
            print(f"❌ Found hardcoded values that should be handlebars: {hardcoded_found}")
            return False
        
        print("✅ Template deployment test passed")
        return True
        
    except Exception as e:
        print(f"❌ Template deployment test failed: {e}")
        return False


def main():
    """Run all framework integrity tests."""
    print("🛡️  CLAUDE PM FRAMEWORK INTEGRITY TESTS")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("Framework Template Tests", run_framework_template_tests),
        ("Version Consistency Tests", run_version_consistency_tests),
        ("Template Deployment Test", run_template_deployment_test),
    ]
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL FRAMEWORK INTEGRITY TESTS PASSED!")
        print("\nFramework is ready for deployment.")
    else:
        print("❌ SOME FRAMEWORK INTEGRITY TESTS FAILED!")
        print("\nPlease fix the issues above before deploying.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())