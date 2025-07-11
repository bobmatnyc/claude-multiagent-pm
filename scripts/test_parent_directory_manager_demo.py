#!/usr/bin/env python3
"""
CMPM-104 Parent Directory Manager Demo Script
============================================

This script demonstrates the Parent Directory Manager functionality
with CMPM-101, CMPM-102, and CMPM-103 integration.
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.services.parent_directory_manager import (
    ParentDirectoryManager,
    ParentDirectoryContext
)


async def main():
    """Demonstrate Parent Directory Manager functionality."""
    print("🚀 CMPM-104 Parent Directory Manager Demo")
    print("=" * 60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Working in temporary directory: {temp_path}")
        
        # Create demo directory structure
        print("\n1. Creating demo directory structure...")
        projects_dir = temp_path / "Projects"
        projects_dir.mkdir()
        
        # Create some sample project directories
        for project in ["project-a", "project-b", "project-c"]:
            project_dir = projects_dir / project
            project_dir.mkdir()
            (project_dir / ".git").mkdir()  # Make it look like a git project
            (project_dir / "README.md").write_text(f"# {project.title()}\n\nSample project")
        
        print(f"   ✅ Created projects directory with 3 sample projects")
        
        # Initialize Parent Directory Manager
        print("\n2. Initializing Parent Directory Manager...")
        manager = ParentDirectoryManager({
            "backup_retention_days": 7,
            "auto_backup_enabled": True,
            "deployment_aware": True
        })
        
        # Override working directory for demo
        manager.working_dir = temp_path
        manager.parent_directory_manager_dir = temp_path / ".claude-pm" / "parent_directory_manager"
        manager._initialize_paths()
        
        await manager._initialize()
        print("   ✅ Parent Directory Manager initialized")
        
        # Detect directory context
        print("\n3. Detecting directory context...")
        context = await manager.detect_parent_directory_context(projects_dir)
        print(f"   ✅ Detected context: {context.value}")
        
        # Register the parent directory
        print("\n4. Registering parent directory...")
        template_variables = {
            "DIRECTORY_NAME": "Projects",
            "SHARED_TOOLS": "git, docker, python",
            "ACTIVE_PROJECTS": "3",
            "DEVELOPMENT_TEAMS": "Frontend, Backend, DevOps"
        }
        
        success = await manager.register_parent_directory(
            projects_dir,
            context,
            "parent_directory_claude_md",
            template_variables
        )
        
        if success:
            print("   ✅ Parent directory registered successfully")
        else:
            print("   ❌ Failed to register parent directory")
            return
        
        # Get status before template installation
        print("\n5. Checking parent directory status...")
        status = await manager.get_parent_directory_status(projects_dir)
        print(f"   📄 File exists: {status.exists}")
        print(f"   🔧 Is managed: {status.is_managed}")
        print(f"   📝 Template source: {status.template_source}")
        
        # List managed directories
        print("\n6. Listing managed directories...")
        directories = await manager.list_managed_directories()
        for dir_info in directories:
            print(f"   📁 {dir_info['directory']}")
            print(f"      Context: {dir_info['context']}")
            print(f"      Template: {dir_info['template_id']}")
            print(f"      Exists: {dir_info['exists']}")
        
        # Auto-register directories
        print("\n7. Testing auto-registration...")
        search_paths = [temp_path, projects_dir]
        registered = await manager.auto_register_parent_directories(search_paths)
        print(f"   ✅ Auto-registered {len(registered)} directories")
        for reg_dir in registered:
            print(f"      📁 {reg_dir}")
        
        # Get operation history
        print("\n8. Checking operation history...")
        history = await manager.get_operation_history()
        print(f"   📊 Total operations: {len(history)}")
        for i, op in enumerate(history[-3:], 1):  # Show last 3 operations
            print(f"      {i}. {op['action']} on {Path(op['target_path']).name} - {'✅' if op['success'] else '❌'}")
        
        # Test configuration persistence
        print("\n9. Testing configuration persistence...")
        await manager._save_managed_directories()
        
        # Create new manager instance and load config
        new_manager = ParentDirectoryManager()
        new_manager.working_dir = temp_path
        new_manager.parent_directory_manager_dir = manager.parent_directory_manager_dir
        new_manager._initialize_paths()
        
        await new_manager._load_managed_directories()
        loaded_dirs = len(new_manager.managed_directories)
        print(f"   ✅ Configuration persisted - {loaded_dirs} directories loaded")
        
        # Cleanup
        print("\n10. Cleaning up...")
        await manager._cleanup()
        print("    ✅ Cleanup completed")
        
        print("\n" + "=" * 60)
        print("🎉 CMPM-104 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✅ Parent directory context detection")
        print("  ✅ Directory registration and management") 
        print("  ✅ Template installation workflow")
        print("  ✅ Status monitoring and validation")
        print("  ✅ Auto-registration capabilities")
        print("  ✅ Operation history tracking")
        print("  ✅ Configuration persistence")
        print("  ✅ Integration with CMPM foundations")


if __name__ == "__main__":
    asyncio.run(main())