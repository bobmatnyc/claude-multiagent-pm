#!/usr/bin/env python3
"""
Subsystem Version Validation Script for Claude PM Framework.

This script validates that all required subsystem versions are present
and compatible with the current framework deployment.

Usage:
    python scripts/validate_subsystem_versions.py
    python scripts/validate_subsystem_versions.py --detailed
    python scripts/validate_subsystem_versions.py --export report.json
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import from claude_pm
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.utils.subsystem_versions import SubsystemVersionManager, VersionStatus


async def validate_framework_versions(detailed: bool = False, export_path: str = None) -> bool:
    """
    Validate framework subsystem versions.
    
    Args:
        detailed: Show detailed information
        export_path: Path to export results (optional)
        
    Returns:
        True if all validations pass, False otherwise
    """
    print("🔢 Claude PM Framework - Subsystem Version Validation")
    print("=" * 60)
    
    try:
        # Create version manager
        manager = SubsystemVersionManager()
        
        # Scan current versions
        print("📡 Scanning subsystem versions...")
        await manager.scan_subsystem_versions()
        
        # Get summary report
        report = manager.get_summary_report()
        summary = report["summary"]
        
        print(f"Framework Path: {report['framework_path']}")
        print(f"Scan Time: {report['scan_timestamp']}")
        print()
        
        # Display summary
        print("📊 Version Summary:")
        print(f"  Total Subsystems: {summary['total_subsystems']}")
        print(f"  Found: {summary['found']} ✅")
        print(f"  Missing: {summary['missing']} ❌")
        print(f"  Errors: {summary['errors']} ⚠️")
        print(f"  Coverage: {summary['coverage_percentage']:.1f}%")
        print()
        
        # Display detailed information if requested
        if detailed:
            print("📋 Detailed Subsystem Information:")
            for name, info in report["subsystems"].items():
                status_icon = {
                    "found": "✅",
                    "missing": "❌", 
                    "error": "⚠️"
                }.get(info["status"], "❓")
                
                print(f"  {status_icon} {name.title()}: {info['version']}")
                if detailed and info["error"]:
                    print(f"    Error: {info['error']}")
                if detailed:
                    print(f"    File: {info['file_path']}")
            print()
        
        # Check for critical missing subsystems
        critical_subsystems = ["memory", "framework"]
        missing_critical = [
            name for name, info in report["subsystems"].items()
            if name in critical_subsystems and info["status"] != "found"
        ]
        
        # Validate compatibility with expected versions
        expected_versions = {
            "memory": "002",
            "framework": "010"
        }
        
        print("🔍 Compatibility Validation:")
        compatibility_checks = await manager.validate_compatibility(expected_versions)
        
        all_compatible = True
        for check in compatibility_checks:
            status_icon = "✅" if check.compatible else "❌"
            print(f"  {status_icon} {check.subsystem.title()}: {check.current_version} vs {check.required_version} required")
            if not check.compatible:
                all_compatible = False
                print(f"    Issue: {check.message}")
        
        print()
        
        # Overall validation result
        validation_passed = (
            summary["missing"] == 0 and 
            summary["errors"] == 0 and 
            len(missing_critical) == 0 and
            all_compatible
        )
        
        if validation_passed:
            print("🎉 All subsystem version validations PASSED!")
            exit_code = 0
        else:
            print("❌ Subsystem version validation FAILED!")
            
            if missing_critical:
                print(f"  Critical subsystems missing: {', '.join(missing_critical)}")
            if not all_compatible:
                print("  Version compatibility issues detected")
            if summary["errors"] > 0:
                print(f"  {summary['errors']} subsystems have errors")
                
            exit_code = 1
        
        # Export results if requested
        if export_path:
            export_data = {
                **report,
                "compatibility_checks": [
                    {
                        "subsystem": check.subsystem,
                        "required_version": check.required_version,
                        "current_version": check.current_version,
                        "compatible": check.compatible,
                        "status": check.status.value,
                        "message": check.message
                    }
                    for check in compatibility_checks
                ],
                "validation_result": {
                    "passed": validation_passed,
                    "missing_critical": missing_critical,
                    "all_compatible": all_compatible
                }
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"📄 Results exported to: {export_path}")
        
        return validation_passed
        
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        return False


async def create_missing_versions():
    """Create missing version files with default values."""
    print("🔧 Creating missing subsystem version files...")
    
    default_versions = {
        "memory": "002",
        "agents": "001",
        "ticketing": "001", 
        "documentation": "001",
        "services": "001",
        "cli": "001",
        "integration": "001",
        "health": "001"
    }
    
    manager = SubsystemVersionManager()
    created_count = 0
    
    for subsystem, default_version in default_versions.items():
        current_version = manager.get_version(subsystem)
        if not current_version:
            success = await manager.update_version(subsystem, default_version, backup=False)
            if success:
                print(f"  ✅ Created {subsystem}: {default_version}")
                created_count += 1
            else:
                print(f"  ❌ Failed to create {subsystem}")
    
    if created_count > 0:
        print(f"🎉 Created {created_count} missing version files")
    else:
        print("ℹ️ All version files already exist")


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate Claude PM Framework subsystem versions"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true", 
        help="Show detailed version information"
    )
    parser.add_argument(
        "--export", 
        type=str, 
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create missing version files with default values"
    )
    
    args = parser.parse_args()
    
    async def run_validation():
        if args.create_missing:
            await create_missing_versions()
            print()
        
        validation_passed = await validate_framework_versions(
            detailed=args.detailed,
            export_path=args.export
        )
        
        # Exit with appropriate code
        sys.exit(0 if validation_passed else 1)
    
    try:
        asyncio.run(run_validation())
    except KeyboardInterrupt:
        print("\n🛑 Validation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()