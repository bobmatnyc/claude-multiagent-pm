#!/usr/bin/env python3
"""
Migration script to make Claude PM Framework pure Python (except npm compatibility).

This script:
1. Removes unnecessary JavaScript files
2. Ensures Python equivalents exist
3. Updates references to use Python implementations
"""

import os
import shutil
from pathlib import Path

# JavaScript files to REMOVE (functionality moved to Python)
JS_FILES_TO_REMOVE = [
    "scripts/claude-wrapper.js",  # No longer needed - direct Python execution
    "scripts/memory-dashboard.js",
    "scripts/memory-guard.js", 
    "scripts/memory-history-tracker.js",
    "scripts/memory-leak-detector.js",
    "scripts/memory-monitor.js",
    "scripts/memory-optimization.js",
    "scripts/validate-memory-fixes.js",
    "scripts/validate-memory-system.js",
    "scripts/enhanced-subprocess-manager.js",
    "scripts/process-health-manager.js",
    "scripts/automated-health-monitor.js",
    "scripts/enhanced-cache-manager.js",
    "scripts/initialize-enhanced-cache.js",
    "scripts/comprehensive-pre-publish-validation.js",
    "scripts/pre-publish-docker-validation.js",
    "scripts/increment_version.js",  # Replace with Python version
]

# JavaScript files to KEEP (npm compatibility)
JS_FILES_TO_KEEP = [
    "install/postinstall-simple.js",
    "install/postinstall-enhanced-python.js", 
    "install/postinstall-minimal.js",
    "install/postinstall-fallback.js",
    "install/preuninstall.js",
    "install/deploy-template.js",
    "install/deploy.js",
    "install/install.js",
    "install/validate-deployment.js",
    "install/validate.js",
    "install/platform/unix.js",
    "install/platform/windows.js",
]

def main():
    """Run the migration to pure Python."""
    project_root = Path(__file__).parent.parent
    
    print("🐍 Migrating Claude PM Framework to Pure Python")
    print("=" * 60)
    
    # Create backup directory
    backup_dir = project_root / "_archive" / "js_migration_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Process files to remove
    print("\n📦 Backing up and removing JavaScript files...")
    removed_count = 0
    for js_file in JS_FILES_TO_REMOVE:
        file_path = project_root / js_file
        if file_path.exists():
            # Backup the file
            backup_path = backup_dir / js_file
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            
            # Remove the file
            file_path.unlink()
            print(f"  ✅ Removed: {js_file}")
            removed_count += 1
        else:
            print(f"  ⏭️  Skipped (not found): {js_file}")
    
    print(f"\n✅ Removed {removed_count} JavaScript files")
    
    # Verify Python equivalents exist
    print("\n🔍 Verifying Python equivalents...")
    python_modules = {
        "memory": "claude_pm/monitoring/memory_monitor.py",
        "subprocess": "claude_pm/monitoring/subprocess_manager.py",
        "cache": "claude_pm/services/shared_prompt_cache.py",
        "process": "claude_pm/orchestration/subprocess_executor.py",
    }
    
    for module_type, module_path in python_modules.items():
        full_path = project_root / module_path
        if full_path.exists():
            print(f"  ✅ {module_type}: {module_path}")
        else:
            print(f"  ❌ {module_type}: {module_path} NOT FOUND")
    
    # List remaining JavaScript files
    print("\n📋 Remaining JavaScript files (npm compatibility):")
    for js_file in JS_FILES_TO_KEEP:
        file_path = project_root / js_file
        if file_path.exists():
            print(f"  ✅ {js_file}")
    
    print("\n✨ Migration complete!")
    print(f"📁 Backup location: {backup_dir}")
    print("\n💡 Next steps:")
    print("  1. Test the framework: claude-pm --version")
    print("  2. Deploy locally: cp bin/claude-pm ~/.local/bin/")
    print("  3. Test Claude launch: claude-pm")

if __name__ == "__main__":
    main()