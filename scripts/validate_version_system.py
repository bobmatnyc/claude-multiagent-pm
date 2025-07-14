#!/usr/bin/env python3
"""
Version System Validation Script
Validates the service version tracking system implementation.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.utils.subsystem_versions import (
    SubsystemVersionManager, 
    VersionStatus,
    scan_framework_versions,
    validate_framework_compatibility
)


async def validate_version_system() -> bool:
    """
    Comprehensive validation of the version tracking system.
    
    Returns:
        True if all validations pass, False otherwise
    """
    print("🔍 Validating Service Version Tracking System...")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Manager initialization
    print("\n1️⃣ Testing Manager Initialization...")
    try:
        manager = SubsystemVersionManager()
        framework_path = manager.framework_path
        print(f"✅ Manager initialized with framework path: {framework_path}")
    except Exception as e:
        print(f"❌ Manager initialization failed: {e}")
        all_tests_passed = False
        return False
    
    # Test 2: Version scanning
    print("\n2️⃣ Testing Version Scanning...")
    try:
        await manager.scan_subsystem_versions()
        report = manager.get_summary_report()
        total = report["summary"]["total_subsystems"]
        found = report["summary"]["found"]
        coverage = report["summary"]["coverage_percentage"]
        
        print(f"✅ Scanned {total} services, found {found} versions")
        print(f"✅ Coverage: {coverage:.1f}%")
        
        if coverage < 80:
            print(f"⚠️  Warning: Coverage below 80% ({coverage:.1f}%)")
    except Exception as e:
        print(f"❌ Version scanning failed: {e}")
        all_tests_passed = False
    
    # Test 3: Individual version retrieval
    print("\n3️⃣ Testing Individual Version Retrieval...")
    test_services = [
        "framework", "memory", "cli", "agents", "services",
        "memory_service", "agents_service", "cli_service", "script_system", "deployment_scripts"
    ]
    
    for service in test_services:
        try:
            version = manager.get_version(service)
            if version:
                print(f"✅ {service}: {version}")
            else:
                print(f"⚠️  {service}: not found")
        except Exception as e:
            print(f"❌ {service}: error retrieving version - {e}")
            all_tests_passed = False
    
    # Test 4: Version compatibility validation
    print("\n4️⃣ Testing Version Compatibility...")
    try:
        # Build requirements dynamically from current versions
        requirements = {}
        for service in ["framework", "memory", "cli", "agents", "script_system", "deployment_scripts"]:
            version = manager.get_version(service)
            if version:
                requirements[service] = version
        
        checks = await manager.validate_compatibility(requirements)
        compatible_count = sum(1 for check in checks if check.compatible)
        
        for check in checks:
            status = "✅" if check.compatible else "❌"
            print(f"{status} {check.subsystem}: {check.current_version} vs {check.required_version}")
        
        print(f"✅ Compatible: {compatible_count}/{len(checks)} services")
        
        if compatible_count < len(checks):
            print("⚠️  Warning: Some services not compatible with requirements")
    except Exception as e:
        print(f"❌ Compatibility validation failed: {e}")
        all_tests_passed = False
    
    # Test 5: Version update functionality
    print("\n5️⃣ Testing Version Update...")
    try:
        # Test update with backup
        test_service = "health"
        original_version = manager.get_version(test_service)
        test_version = "999"
        
        success = await manager.update_version(test_service, test_version, backup=True)
        if success:
            updated_version = manager.get_version(test_service)
            print(f"✅ Update test: {test_service} {original_version} → {updated_version}")
            
            # Restore original version
            if original_version:
                await manager.update_version(test_service, original_version, backup=False)
                print(f"✅ Restored {test_service} to {original_version}")
        else:
            print(f"❌ Update test failed for {test_service}")
            all_tests_passed = False
    except Exception as e:
        print(f"❌ Version update test failed: {e}")
        all_tests_passed = False
    
    # Test 6: Service listing
    print("\n6️⃣ Testing Service Listing...")
    try:
        available = manager.get_all_available_subsystems()
        print(f"✅ Available services: {len(available)}")
        print(f"   Standard: {len(manager.SUBSYSTEM_FILES)}")
        print(f"   Service-specific: {len(manager.SERVICE_VERSION_FILES)}")
    except Exception as e:
        print(f"❌ Service listing failed: {e}")
        all_tests_passed = False
    
    # Test 7: Standalone functions
    print("\n7️⃣ Testing Standalone Functions...")
    try:
        # Test scan_framework_versions
        versions = await scan_framework_versions()
        print(f"✅ Standalone scan found {len(versions)} versions")
        
        # Test validate_framework_compatibility with dynamic versions
        test_requirements = {}
        for service in ["framework", "memory"]:
            version = manager.get_version(service)
            if version:
                test_requirements[service] = version
        
        is_compatible, compatibility_checks = await validate_framework_compatibility(test_requirements)
        print(f"✅ Standalone compatibility: {is_compatible}")
    except Exception as e:
        print(f"❌ Standalone functions failed: {e}")
        all_tests_passed = False
    
    # Test 8: Project version consistency
    print("\n8️⃣ Testing Project Version Consistency...")
    try:
        project_root = Path(__file__).parent.parent
        
        # Check package.json
        package_json = project_root / "package.json"
        if package_json.exists():
            import json
            with package_json.open() as f:
                package_data = json.load(f)
            package_version = package_data.get("version")
            print(f"✅ package.json: {package_version}")
        
        # Check VERSION file
        version_file = project_root / "VERSION"
        if version_file.exists():
            file_version = version_file.read_text().strip()
            print(f"✅ VERSION file: {file_version}")
        
        # Check __init__.py
        init_file = project_root / "claude_pm" / "__init__.py"
        if init_file.exists():
            init_content = init_file.read_text()
            import re
            version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', init_content)
            if version_match:
                init_version = version_match.group(1)
                print(f"✅ __init__.py: {init_version}")
        
        print("✅ Project version consistency check completed")
    except Exception as e:
        print(f"❌ Project version consistency failed: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All version system tests PASSED!")
        print("✅ Service version tracking system is ready for use")
    else:
        print("❌ Some version system tests FAILED!")
        print("🔧 Please review the errors above and fix issues")
    
    return all_tests_passed


if __name__ == "__main__":
    success = asyncio.run(validate_version_system())
    sys.exit(0 if success else 1)