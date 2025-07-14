#!/usr/bin/env python3
"""
Update configuration files with current version information.

This script updates configuration files (config.json, framework.yaml, etc.)
with the current package and framework versions loaded dynamically.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.utils.version_loader import update_config_files


def main():
    """Main function to update configuration files."""
    parser = argparse.ArgumentParser(
        description="Update configuration files with current version information"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    print("🔄 Updating Configuration Files with Current Versions")
    print("=" * 60)
    
    # Run the update
    result = update_config_files(dry_run=args.dry_run)
    
    if args.dry_run:
        print("📋 DRY RUN - No changes were made")
        print()
    
    # Display results
    if result['changes']:
        print(f"📝 Found {len(result['changes'])} changes:")
        for change in result['changes']:
            print(f"  - {change}")
        print()
    else:
        print("✅ No version updates needed - all configurations are current")
        print()
    
    if result['updated_files']:
        print(f"📁 Updated {len(result['updated_files'])} files:")
        for file_path in result['updated_files']:
            print(f"  - {file_path}")
        print()
    
    if result['errors']:
        print(f"❌ Encountered {len(result['errors'])} errors:")
        for error in result['errors']:
            print(f"  - {error}")
        print()
    
    # Show summary
    if not args.dry_run:
        if result['updated_files'] and not result['errors']:
            print("🎉 Configuration files updated successfully!")
        elif result['errors']:
            print("⚠️ Configuration update completed with errors")
            sys.exit(1)
        else:
            print("✅ All configuration files are up to date")
    else:
        if result['changes']:
            print("💡 Run without --dry-run to apply these changes")
        else:
            print("✅ All configuration files are up to date")


if __name__ == "__main__":
    main()