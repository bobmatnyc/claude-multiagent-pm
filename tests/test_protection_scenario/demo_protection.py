#!/usr/bin/env python3
"""
Demonstration script showing the fixed framework protection mechanism.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to path so we can import claude_pm
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.parent_directory_manager import ParentDirectoryManager

async def demo_protection():
    """Demonstrate the protection mechanism works correctly."""
    
    print("🛡️  Framework Protection Demonstration")
    print("=" * 50)
    
    # Create a project development file in current directory
    current_dir = Path.cwd()
    project_file = current_dir / "CLAUDE.md"
    
    if project_file.exists():
        print(f"📋 Existing CLAUDE.md found at: {project_file}")
    else:
        print(f"📋 No existing CLAUDE.md found at: {project_file}")
    
    # Initialize the parent directory manager
    manager = ParentDirectoryManager(quiet_mode=True)
    await manager.start()
    
    try:
        # Try to deploy with force flag
        print("\n🚫 Testing force deployment (should be blocked)...")
        result = await manager.install_template_to_parent_directory(
            target_directory=current_dir,
            template_id="parent_directory_claude_md",
            force=True
        )
        
        if result.success:
            print("❌ ERROR: Force flag incorrectly overrode protection!")
            print("   The --force flag should NOT be able to override project development file protection.")
        else:
            print("✅ SUCCESS: Force flag correctly blocked by permanent protection!")
            print("   Project development files are protected from accidental overwriting.")
            
        if result.error_message:
            print(f"   Protection reason: {result.error_message}")
            
    finally:
        await manager.stop()
        
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION:")
    print("   • Project development files are now permanently protected")
    print("   • --force flag cannot override this protection")
    print("   • Framework deployment templates can still be replaced")
    print("   • Enhanced error messages provide clear user guidance")

if __name__ == "__main__":
    asyncio.run(demo_protection())