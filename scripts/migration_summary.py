#!/usr/bin/env python3
"""
Migration Summary Script
=======================

Provides a comprehensive summary of the environment variable migration
from CLAUDE_PM_ to CLAUDE_MULTIAGENT_PM_ prefix.
"""

import os
import sys
from pathlib import Path
import json

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n--- {title} ---")

def check_migration_files():
    """Check if migration files exist."""
    project_root = Path(__file__).parent.parent
    migration_files = [
        "scripts/migrate_env_variables.py",
        "scripts/setup_env_migration.sh",
        "scripts/validate_env_migration.py",
        "env_migration_commands.sh",
        "env_migration_report.json",
        "docs/ENVIRONMENT_VARIABLE_MIGRATION.md"
    ]
    
    print_section("Migration Files Status")
    all_exist = True
    for file_path in migration_files:
        full_path = project_root / file_path
        status = "✅ EXISTS" if full_path.exists() else "❌ MISSING"
        print(f"{status}: {file_path}")
        if not full_path.exists():
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """Check current environment variable status."""
    print_section("Current Environment Variables")
    
    legacy_vars = [k for k in os.environ.keys() if k.startswith('CLAUDE_PM_')]
    new_vars = [k for k in os.environ.keys() if k.startswith('CLAUDE_MULTIAGENT_PM_')]
    
    print(f"Legacy CLAUDE_PM_ variables: {len(legacy_vars)}")
    if legacy_vars:
        print("Sample legacy vars:", legacy_vars[:3])
    
    print(f"New CLAUDE_MULTIAGENT_PM_ variables: {len(new_vars)}")
    if new_vars:
        print("Sample new vars:", new_vars[:3])
    
    return len(legacy_vars), len(new_vars)

def check_framework_configuration():
    """Test framework configuration."""
    print_section("Framework Configuration Test")
    
    try:
        from claude_pm.core.config import Config
        config = Config()
        
        # Test key configuration values
        claude_pm_path = config.get("claude_pm_path")
        managed_path = config.get("managed_path")
        memory_enabled = config.get("memory_enabled")
        
        print("✅ Framework configuration loaded successfully")
        print(f"Claude PM Path: {claude_pm_path}")
        print(f"Managed Path: {managed_path}")
        print(f"Memory Enabled: {memory_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework configuration failed: {e}")
        return False

def load_migration_report():
    """Load and display migration report."""
    print_section("Migration Report Summary")
    
    report_path = Path(__file__).parent.parent / "env_migration_report.json"
    if not report_path.exists():
        print("❌ Migration report not found. Please run migrate_env_variables.py first.")
        return None
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        print(f"Migration timestamp: {report.get('timestamp', 'Unknown')}")
        print(f"Legacy variables found: {report.get('legacy_variables_found', 0)}")
        print(f"Variables to migrate: {len(report.get('migration_map', {}))}")
        
        # Show sample mapping
        if 'migration_map' in report and report['migration_map']:
            print("\nSample variable mappings:")
            for i, (old, new) in enumerate(list(report['migration_map'].items())[:5]):
                print(f"  {old} → {new}")
            if len(report['migration_map']) > 5:
                print(f"  ... and {len(report['migration_map']) - 5} more")
        
        return report
        
    except Exception as e:
        print(f"❌ Error loading migration report: {e}")
        return None

def print_next_steps(legacy_count, new_count):
    """Print recommended next steps."""
    print_section("Recommended Next Steps")
    
    if legacy_count > 0 and new_count == 0:
        print("🔄 MIGRATION NEEDED")
        print("1. Run: python3 scripts/migrate_env_variables.py")
        print("2. Run: scripts/setup_env_migration.sh")
        print("3. Choose option 2 for permanent migration")
        print("4. Restart terminal or source shell config")
        print("5. Run: python3 scripts/validate_env_migration.py")
        
    elif legacy_count > 0 and new_count > 0:
        print("⚠️  PARTIAL MIGRATION")
        print("You have both legacy and new variables.")
        print("1. Remove legacy variables after confirming new ones work")
        print("2. Run: python3 scripts/validate_env_migration.py")
        
    elif legacy_count == 0 and new_count > 0:
        print("✅ MIGRATION COMPLETE")
        print("You're using the new variable format.")
        print("1. Run: python3 scripts/validate_env_migration.py")
        print("2. Update any documentation or scripts")
        
    else:
        print("❓ NO VARIABLES DETECTED")
        print("No Claude PM environment variables found.")
        print("1. Check if you're in the right environment")
        print("2. Set up environment variables as needed")

def print_troubleshooting():
    """Print troubleshooting information."""
    print_section("Troubleshooting")
    
    print("Common Issues:")
    print("• Variables not persisting: Use option 2 in setup script for permanent migration")
    print("• Framework warnings: Ensure new variables are set and restart terminal")
    print("• Migration script errors: Check permissions and file access")
    print("• Configuration issues: Verify Python environment and claude_pm module")
    
    print("\nFor help:")
    print("• Review: docs/ENVIRONMENT_VARIABLE_MIGRATION.md")
    print("• Run: python3 scripts/validate_env_migration.py")
    print("• Check migration files in project root")

def main():
    """Main summary routine."""
    print_header("Claude PM Framework Environment Variable Migration Summary")
    
    # Check migration files
    files_exist = check_migration_files()
    
    # Check environment variables
    legacy_count, new_count = check_environment_variables()
    
    # Test framework configuration
    config_works = check_framework_configuration()
    
    # Load migration report
    report = load_migration_report()
    
    # Print next steps
    print_next_steps(legacy_count, new_count)
    
    # Print troubleshooting
    print_troubleshooting()
    
    # Final status
    print_header("Migration Status Summary")
    
    print(f"Migration tools: {'✅ Ready' if files_exist else '❌ Missing files'}")
    print(f"Framework config: {'✅ Working' if config_works else '❌ Issues detected'}")
    print(f"Legacy variables: {legacy_count} found")
    print(f"New variables: {new_count} found")
    
    if files_exist and config_works:
        if legacy_count > 0 and new_count == 0:
            print("\n🎯 STATUS: Ready for migration")
            print("   Run setup script to complete migration.")
        elif legacy_count > 0 and new_count > 0:
            print("\n⚠️  STATUS: Partial migration")
            print("   Clean up legacy variables after validation.")
        elif new_count > 0:
            print("\n✅ STATUS: Migration complete")
            print("   Using new variable format.")
        else:
            print("\n❓ STATUS: No variables detected")
            print("   Set up environment variables as needed.")
    else:
        print("\n❌ STATUS: Issues detected")
        print("   Resolve issues before proceeding with migration.")
    
    print("\nFor detailed instructions, see:")
    print("docs/ENVIRONMENT_VARIABLE_MIGRATION.md")

if __name__ == "__main__":
    main()