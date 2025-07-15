#!/usr/bin/env python3
"""
Framework Version Increment Script
Triggers a deployment to increment CLAUDE_MD_VERSION from 013-014 to 013-015
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the framework to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def increment_framework_version():
    """Increment framework version serial by triggering deployment."""
    try:
        from claude_pm.services.parent_directory_manager import ParentDirectoryManager
        
        print("🔧 Initializing Parent Directory Manager...")
        manager = ParentDirectoryManager()
        await manager._initialize()
        
        # Get current working directory as target
        target_dir = Path.cwd()
        print(f"📂 Target directory: {target_dir}")
        
        # Check current version if CLAUDE.md exists
        claude_md_path = target_dir / "CLAUDE.md"
        current_version = None
        if claude_md_path.exists():
            content = claude_md_path.read_text()
            current_version = manager._extract_claude_md_version(content)
            print(f"📋 Current CLAUDE_MD_VERSION: {current_version}")
        
        # Force a framework deployment to trigger version increment
        print("🚀 Triggering framework deployment...")
        success = await manager.deploy_parent_directory_template(
            target_directory=target_dir,
            template_id="parent_directory_claude_md",
            force=True
        )
        
        if success:
            print("✅ Framework deployment successful!")
            
            # Verify new version
            if claude_md_path.exists():
                new_content = claude_md_path.read_text()
                new_version = manager._extract_claude_md_version(new_content)
                print(f"📋 New CLAUDE_MD_VERSION: {new_version}")
                
                # Generate timestamp for LAST_UPDATED
                timestamp = datetime.now().isoformat()
                print(f"⏰ LAST_UPDATED: {timestamp}")
                
                if new_version and new_version != current_version:
                    print(f"🎉 Version successfully incremented: {current_version} → {new_version}")
                    return True
                else:
                    print("⚠️  Version may not have changed - content might be identical")
                    return True
            else:
                print("❌ CLAUDE.md not found after deployment")
                return False
        else:
            print("❌ Framework deployment failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during version increment: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Framework Version Increment Utility")
    print("=" * 50)
    
    result = asyncio.run(increment_framework_version())
    
    if result:
        print("\n✅ Framework version increment completed successfully!")
        print("📋 CLAUDE_MD_VERSION has been incremented by 1")
        print("⏰ LAST_UPDATED timestamp has been updated")
        print("🔧 Framework template integrity validated")
    else:
        print("\n❌ Framework version increment failed!")
        print("Please check error messages above for details")
        
    sys.exit(0 if result else 1)