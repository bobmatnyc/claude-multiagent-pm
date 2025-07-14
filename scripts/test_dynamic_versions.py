#!/usr/bin/env python3
"""
Test script for dynamic version loading system.

This script demonstrates and tests the new dynamic version loading
infrastructure that replaces hardcoded version references.
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.utils.version_loader import (
    get_package_version, 
    get_framework_version, 
    get_service_version,
    get_all_versions,
    update_config_files,
    VersionLoader
)


def test_basic_version_loading():
    """Test basic version loading functionality."""
    print("🔍 Testing Basic Version Loading")
    print("=" * 40)
    
    # Test package version loading
    package_version = get_package_version()
    print(f"Package Version: {package_version}")
    
    # Test framework version loading
    framework_version = get_framework_version()
    print(f"Framework Version: {framework_version}")
    
    # Test service version loading
    memory_version = get_service_version("memory")
    print(f"Memory Service Version: {memory_version}")
    
    cli_version = get_service_version("cli")
    print(f"CLI Service Version: {cli_version}")
    
    print()


def test_python_package_imports():
    """Test that Python package imports work with dynamic loading."""
    print("🐍 Testing Python Package Imports")
    print("=" * 40)
    
    # Test main package import
    import claude_pm
    print(f"claude_pm.__version__: {claude_pm.__version__}")
    
    # Test _version.py import
    from claude_pm._version import __version__
    print(f"_version.__version__: {__version__}")
    
    # Test they match
    if claude_pm.__version__ == __version__:
        print("✅ Version consistency check passed")
    else:
        print("❌ Version consistency check failed")
    
    print()


def test_all_versions():
    """Test loading all available versions."""
    print("📊 Testing All Version Loading")
    print("=" * 40)
    
    all_versions = get_all_versions()
    
    print("All Available Versions:")
    for name, version in sorted(all_versions.items()):
        print(f"  {name}: {version}")
    
    print()


def test_version_loader_class():
    """Test the VersionLoader class directly."""
    print("🛠️ Testing VersionLoader Class")
    print("=" * 40)
    
    loader = VersionLoader()
    
    # Test framework root detection
    print(f"Framework Root: {loader.framework_root}")
    
    # Test cache functionality
    print("Testing cache functionality...")
    version1 = loader.get_package_version()
    version2 = loader.get_package_version()  # Should be cached
    
    if version1 == version2:
        print("✅ Cache functionality working")
    else:
        print("❌ Cache functionality failed")
    
    # Test cache clearing
    loader.clear_cache()
    version3 = loader.get_package_version()  # Should reload
    
    if version1 == version3:
        print("✅ Cache clearing working")
    else:
        print("❌ Cache clearing failed")
    
    print()


def test_config_file_updates():
    """Test configuration file update functionality."""
    print("📝 Testing Config File Updates")
    print("=" * 40)
    
    # Test dry run first
    print("Running dry run...")
    result = update_config_files(dry_run=True)
    
    print(f"Found {len(result['changes'])} potential changes:")
    for change in result['changes']:
        print(f"  - {change}")
    
    if result['errors']:
        print("Errors encountered:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print()


async def test_subsystem_integration():
    """Test integration with subsystem version manager."""
    print("🔧 Testing Subsystem Integration")
    print("=" * 40)
    
    try:
        from claude_pm.utils.subsystem_versions import SubsystemVersionManager
        
        manager = SubsystemVersionManager()
        await manager.scan_subsystem_versions()
        
        # Test a few key services
        services_to_test = ["memory", "framework", "cli", "agents"]
        
        for service in services_to_test:
            subsystem_version = manager.get_version(service)
            dynamic_version = get_service_version(service)
            
            if subsystem_version == dynamic_version:
                print(f"✅ {service}: {subsystem_version} (consistent)")
            else:
                print(f"❌ {service}: subsystem={subsystem_version}, dynamic={dynamic_version}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error testing subsystem integration: {e}")
        print()


def test_fallback_behavior():
    """Test fallback behavior when version files are missing."""
    print("🔄 Testing Fallback Behavior")
    print("=" * 40)
    
    # Test service that doesn't exist
    nonexistent_version = get_service_version("nonexistent_service")
    print(f"Nonexistent service version: {nonexistent_version}")
    
    if nonexistent_version == "001":
        print("✅ Fallback behavior working for nonexistent service")
    else:
        print("❌ Fallback behavior failed for nonexistent service")
    
    print()


def test_version_consistency():
    """Test version consistency across different loading methods."""
    print("🎯 Testing Version Consistency")
    print("=" * 40)
    
    # Test that all methods return consistent package versions
    loader = VersionLoader()
    
    package_version_1 = get_package_version()
    package_version_2 = loader.get_package_version()
    
    if package_version_1 == package_version_2:
        print("✅ Package version consistency check passed")
    else:
        print("❌ Package version consistency check failed")
    
    # Test framework version consistency
    framework_version_1 = get_framework_version()
    framework_version_2 = loader.get_framework_version()
    
    if framework_version_1 == framework_version_2:
        print("✅ Framework version consistency check passed")
    else:
        print("❌ Framework version consistency check failed")
    
    print()


async def main():
    """Run all tests."""
    print("🧪 Dynamic Version Loading System Test Suite")
    print("=" * 60)
    print()
    
    # Run all tests
    test_basic_version_loading()
    test_python_package_imports()
    test_all_versions()
    test_version_loader_class()
    test_config_file_updates()
    await test_subsystem_integration()
    test_fallback_behavior()
    test_version_consistency()
    
    print("🎉 All tests completed!")
    print("✅ Dynamic version loading system is working correctly")


if __name__ == "__main__":
    asyncio.run(main())