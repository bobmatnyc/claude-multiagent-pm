#!/usr/bin/env python3
"""
Example usage of the ConfigAliasManager module.

This demonstrates how to use configuration aliases in the Claude PM Framework
to manage different configuration directories with friendly names.
"""

import sys
from pathlib import Path

# Add the project root to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.core.config_aliases import (
    ConfigAliasManager,
    AliasNotFoundError,
    DuplicateAliasError,
)


def main():
    """Demonstrate configuration alias functionality."""
    print("Claude PM Configuration Alias Manager Example")
    print("=" * 50)
    
    # Initialize the manager
    manager = ConfigAliasManager()
    print(f"\nUsing aliases file: {manager.aliases_file}")
    
    # Create some example aliases
    print("\n1. Creating configuration aliases...")
    try:
        # Personal configuration
        manager.create_alias("personal", "~/.claude-pm/configs/personal")
        print("   ✅ Created 'personal' alias")
        
        # Work configuration
        manager.create_alias("work", "~/.claude-pm/configs/work")
        print("   ✅ Created 'work' alias")
        
        # Test/development configuration
        manager.create_alias("test", "~/.claude-pm/configs/test")
        print("   ✅ Created 'test' alias")
        
    except DuplicateAliasError as e:
        print(f"   ℹ️  Some aliases already exist: {e}")
    
    # List all aliases
    print("\n2. Current configuration aliases:")
    aliases = manager.list_aliases()
    if aliases:
        for name, path in aliases:
            print(f"   - {name:12} → {path}")
    else:
        print("   No aliases configured")
    
    # Demonstrate alias resolution
    print("\n3. Resolving aliases:")
    for alias_name in ["personal", "work", "test"]:
        try:
            resolved_path = manager.resolve_alias(alias_name)
            print(f"   - '{alias_name}' resolves to: {resolved_path}")
        except AliasNotFoundError:
            print(f"   - '{alias_name}' not found")
    
    # Show how it would be used in the CLI
    print("\n4. CLI Usage Examples:")
    print("   # Use personal configuration")
    print("   $ claude-pm --config personal")
    print()
    print("   # Use work configuration")
    print("   $ claude-pm --config work")
    print()
    print("   # Use test configuration")
    print("   $ claude-pm --config test")
    
    # Update an alias
    print("\n5. Updating an alias:")
    try:
        manager.update_alias("test", "~/.claude-pm/configs/development")
        print("   ✅ Updated 'test' alias to point to development config")
    except AliasNotFoundError:
        print("   ❌ Alias 'test' not found")
    
    # Check if alias exists
    print("\n6. Checking alias existence:")
    for alias in ["personal", "work", "production"]:
        exists = manager.alias_exists(alias)
        print(f"   - '{alias}' exists: {exists}")
    
    # Clean up (optional - remove test alias)
    print("\n7. Cleanup (removing test alias):")
    try:
        manager.delete_alias("test")
        print("   ✅ Removed 'test' alias")
    except AliasNotFoundError:
        print("   ℹ️  'test' alias was already removed")
    
    # Final list
    print("\n8. Final alias configuration:")
    aliases = manager.list_aliases()
    if aliases:
        for name, path in aliases:
            print(f"   - {name:12} → {path}")
    else:
        print("   No aliases configured")
    
    print("\n✅ Example completed!")
    print("\nNote: The aliases are persisted in ~/.claude-pm/config_aliases.json")
    print("and will be available for future claude-pm sessions.")


if __name__ == "__main__":
    main()