#!/usr/bin/env python3
"""
Example script demonstrating config aliases functionality.
Run this to see how config aliases work in practice.
"""

import tempfile
import shutil
from pathlib import Path
from claude_pm.core.config_aliases import ConfigAliasManager

def main():
    print("🎯 Claude PM Config Aliases Demo\n")
    
    # Initialize the manager
    manager = ConfigAliasManager()
    
    # Create some test directories
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test config directories
        personal_dir = Path(tmpdir) / "claude-configs" / "personal"
        work_dir = Path(tmpdir) / "claude-configs" / "work"
        dev_dir = Path(tmpdir) / "claude-configs" / "development"
        
        personal_dir.mkdir(parents=True)
        work_dir.mkdir(parents=True)
        dev_dir.mkdir(parents=True)
        
        print(f"📁 Created test directories in: {tmpdir}")
        print(f"   - {personal_dir}")
        print(f"   - {work_dir}")
        print(f"   - {dev_dir}")
        print()
        
        # Create aliases
        print("✨ Creating config aliases...")
        try:
            manager.create_alias("demo-personal", str(personal_dir))
            print(f"   ✅ Created alias 'demo-personal' → {personal_dir}")
        except Exception as e:
            print(f"   ⚠️  Could not create 'demo-personal': {e}")
        
        try:
            manager.create_alias("demo-work", str(work_dir))
            print(f"   ✅ Created alias 'demo-work' → {work_dir}")
        except Exception as e:
            print(f"   ⚠️  Could not create 'demo-work': {e}")
        
        try:
            manager.create_alias("demo-dev", str(dev_dir))
            print(f"   ✅ Created alias 'demo-dev' → {dev_dir}")
        except Exception as e:
            print(f"   ⚠️  Could not create 'demo-dev': {e}")
        print()
        
        # List all aliases
        print("📋 Listing all aliases:")
        aliases = manager.list_aliases()
        for alias in aliases:
            if isinstance(alias, tuple):
                alias_name, alias_path = alias
                print(f"   • {alias_name} → {alias_path}")
            else:
                path = manager.resolve_alias(alias)
                print(f"   • {alias} → {path}")
        print()
        
        # Demonstrate resolving aliases
        print("🔍 Resolving aliases:")
        for alias in ["demo-personal", "demo-work", "demo-dev"]:
            try:
                resolved = manager.resolve_alias(alias)
                print(f"   • claude-pm --config {alias}")
                print(f"     → claude --config-dir {resolved}")
            except Exception as e:
                print(f"   ⚠️  Could not resolve '{alias}': {e}")
        print()
        
        # Update an alias
        print("🔄 Updating an alias:")
        new_work_dir = Path(tmpdir) / "claude-configs" / "work-v2"
        new_work_dir.mkdir(parents=True)
        try:
            manager.update_alias("demo-work", str(new_work_dir))
            print(f"   ✅ Updated 'demo-work' → {new_work_dir}")
        except Exception as e:
            print(f"   ⚠️  Could not update 'demo-work': {e}")
        print()
        
        # Delete an alias
        print("🗑️  Deleting an alias:")
        try:
            manager.delete_alias("demo-dev")
            print("   ✅ Deleted alias 'demo-dev'")
        except Exception as e:
            print(f"   ⚠️  Could not delete 'demo-dev': {e}")
        print()
        
        # Final list
        print("📋 Final alias list:")
        aliases = manager.list_aliases()
        for alias in aliases:
            if isinstance(alias, tuple):
                alias_name, alias_path = alias
                print(f"   • {alias_name} → {alias_path}")
            else:
                path = manager.resolve_alias(alias)
                print(f"   • {alias} → {path}")
        print()
        
        # Show example commands
        print("💡 Example usage:")
        print("   # Create an alias")
        print("   claude-pm --create-config ~/.claude-personal personal")
        print()
        print("   # Use the alias (sets CLAUDE_CONFIG_DIR environment variable)")
        print("   claude-pm --config personal")
        print()
        print("   # List all aliases")
        print("   claude-pm --list-configs")
        print()
        print("   # Delete an alias")
        print("   claude-pm --delete-config personal")
        print()
        print("ℹ️  Note: The --config flag sets the CLAUDE_CONFIG_DIR environment variable")
        print("   before launching Claude CLI. This tells Claude where to look for its")
        print("   configuration files.")

if __name__ == "__main__":
    main()