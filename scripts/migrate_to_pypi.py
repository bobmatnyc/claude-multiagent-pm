#!/usr/bin/env python3
"""
Claude Multi-Agent PM - Migration Helper Script
Helps users migrate from editable source installations to PyPI package installations.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import json

class PyPIMigrationHelper:
    """Helper class for migrating from editable installations to PyPI."""
    
    def __init__(self):
        self.home = Path.home()
        self.source_path = self.home / "Projects" / "claude-multiagent-pm"
        self.claude_pm_dir = self.home / ".claude-pm"
        self.backup_dir = self.claude_pm_dir / "migration_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def check_current_installation(self):
        """Check current installation status."""
        print("🔍 Checking current installation...")
        
        # Check for editable installation
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "claude-multiagent-pm"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if "Editable project location" in result.stdout:
                    print("⚠️  Found editable installation (source mode)")
                    # Extract location
                    for line in result.stdout.split('\n'):
                        if "Editable project location" in line:
                            location = line.split(":", 1)[1].strip()
                            print(f"   Location: {location}")
                    return "editable"
                else:
                    print("✅ Found PyPI installation")
                    return "pypi"
            else:
                print("❌ No installation found")
                return "none"
                
        except Exception as e:
            print(f"❌ Error checking installation: {e}")
            return "error"
            
    def backup_user_data(self):
        """Backup user data before migration."""
        print("\n📦 Creating backup of user data...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup .claude-pm directory
            if self.claude_pm_dir.exists():
                backup_items = [
                    "agents/user-defined",
                    "agents/project-specific",
                    "config",
                    "memory",
                    "logs"
                ]
                
                for item in backup_items:
                    source = self.claude_pm_dir / item
                    if source.exists():
                        dest = self.backup_dir / item
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        
                        if source.is_dir():
                            shutil.copytree(source, dest)
                            print(f"   ✅ Backed up {item}")
                        else:
                            shutil.copy2(source, dest)
                            print(f"   ✅ Backed up {item}")
                            
            # Create migration info file
            migration_info = {
                "timestamp": datetime.now().isoformat(),
                "previous_installation": "editable",
                "source_path": str(self.source_path),
                "backup_location": str(self.backup_dir)
            }
            
            with open(self.backup_dir / "migration_info.json", "w") as f:
                json.dump(migration_info, f, indent=2)
                
            print(f"\n✅ Backup created at: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"\n❌ Backup failed: {e}")
            return False
            
    def uninstall_editable(self):
        """Uninstall editable installation."""
        print("\n🗑️  Removing editable installation...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "claude-multiagent-pm"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Editable installation removed")
                return True
            else:
                print(f"❌ Failed to uninstall: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error during uninstall: {e}")
            return False
            
    def install_from_pypi(self):
        """Install from PyPI."""
        print("\n📦 Installing from PyPI...")
        
        try:
            # Try standard installation
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "claude-multiagent-pm"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Successfully installed from PyPI")
                return True
            else:
                # Try with --break-system-packages
                if "externally-managed-environment" in result.stderr:
                    print("⚠️  Retrying with --break-system-packages...")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "claude-multiagent-pm"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print("✅ Successfully installed from PyPI (with --break-system-packages)")
                        return True
                        
                print(f"❌ Installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error during installation: {e}")
            return False
            
    def verify_installation(self):
        """Verify the new installation works."""
        print("\n🔍 Verifying installation...")
        
        try:
            # Check pip show
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "claude-multiagent-pm"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "Editable project location" not in result.stdout:
                print("✅ PyPI installation verified")
                
                # Try importing
                try:
                    subprocess.run(
                        [sys.executable, "-c", "import claude_pm; print('✅ Import successful')"],
                        check=True
                    )
                except:
                    print("⚠️  Import test failed")
                    
                # Try CLI command
                try:
                    subprocess.run(
                        ["claude-pm", "--version"],
                        capture_output=True,
                        check=True
                    )
                    print("✅ CLI command working")
                except:
                    print("⚠️  CLI command not found in PATH")
                    
                return True
            else:
                print("❌ Installation verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False
            
    def update_environment(self):
        """Update environment variables for new installation."""
        print("\n🔧 Updating environment...")
        
        # Add deprecation environment variable to suppress warnings during transition
        env_file = self.home / ".bashrc"  # or .zshrc, .bash_profile etc.
        
        print("📝 Add this to your shell configuration to suppress deprecation warnings:")
        print("   export CLAUDE_PM_SOURCE_MODE=deprecated")
        print("\n📝 Remove this line after migration is complete.")
        
    def run_migration(self):
        """Run the complete migration process."""
        print("🚀 Claude PM Migration Tool - Editable to PyPI")
        print("=" * 60)
        
        # Check current installation
        current = self.check_current_installation()
        
        if current == "pypi":
            print("\n✅ Already using PyPI installation - no migration needed!")
            return True
            
        if current != "editable":
            print("\n⚠️  No editable installation found to migrate.")
            print("💡 To install from PyPI: pip install claude-multiagent-pm")
            return False
            
        # Confirm migration
        print("\n⚠️  This will migrate your editable installation to PyPI.")
        print("   Your user data will be backed up.")
        response = input("\nProceed with migration? (y/N): ").strip().lower()
        
        if response != 'y':
            print("\n❌ Migration cancelled.")
            return False
            
        # Run migration steps
        steps = [
            ("Backing up user data", self.backup_user_data),
            ("Uninstalling editable version", self.uninstall_editable),
            ("Installing from PyPI", self.install_from_pypi),
            ("Verifying installation", self.verify_installation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'=' * 60}")
            print(f"Step: {step_name}")
            print('=' * 60)
            
            if not step_func():
                print(f"\n❌ Migration failed at step: {step_name}")
                print(f"💡 Backup available at: {self.backup_dir}")
                return False
                
        # Final steps
        self.update_environment()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("1. Restart your terminal to ensure PATH updates")
        print("2. Run 'claude-pm --version' to verify")
        print("3. Run 'claude-pm init' to reinitialize if needed")
        print(f"4. Your backup is at: {self.backup_dir}")
        print("\n🎉 You're now using the PyPI version!")
        
        return True

def main():
    """Main entry point."""
    helper = PyPIMigrationHelper()
    success = helper.run_migration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()