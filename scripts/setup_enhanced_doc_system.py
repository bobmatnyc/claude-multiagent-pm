#!/usr/bin/env python3
"""
Enhanced Documentation System Setup
FWK-008: Complete Documentation Synchronization System Setup

This script sets up the complete enhanced documentation synchronization system
including all components, configurations, and integrations.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class EnhancedDocSystemSetup:
    """Setup manager for the enhanced documentation synchronization system"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.scripts_dir = self.claude_pm_root / "scripts"
        self.config_dir = self.claude_pm_root / "config"
        self.logs_dir = self.claude_pm_root / "logs"
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def setup_complete_system(self) -> bool:
        """Setup the complete enhanced documentation system"""
        print("🚀 Setting up Enhanced Documentation Synchronization System")
        print("=" * 60)
        
        success = True
        
        # Step 1: Create configurations
        print("\n1️⃣ Creating system configurations...")
        success &= self._create_configurations()
        
        # Step 2: Install pre-commit hooks
        print("\n2️⃣ Installing pre-commit hooks...")
        success &= self._install_hooks()
        
        # Step 3: Setup systemd service (optional)
        print("\n3️⃣ Creating systemd service file...")
        success &= self._create_systemd_service()
        
        # Step 4: Setup cron job (optional)
        print("\n4️⃣ Creating cron job...")
        success &= self._create_cron_job()
        
        # Step 5: Create CLI alias
        print("\n5️⃣ Setting up CLI aliases...")
        success &= self._setup_cli_aliases()
        
        # Step 6: Run initial validation
        print("\n6️⃣ Running initial system validation...")
        success &= self._run_initial_validation()
        
        # Step 7: Setup health monitoring integration
        print("\n7️⃣ Integrating with health monitoring...")
        success &= self._setup_health_integration()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ Enhanced Documentation System setup completed successfully!")
            self._print_next_steps()
        else:
            print("❌ Setup completed with some issues. Check messages above.")
        
        return success

    def _create_configurations(self) -> bool:
        """Create system configuration files"""
        try:
            # Enhanced documentation sync configuration
            doc_sync_config = {
                "claude_pm_root": str(self.claude_pm_root),
                "notifications_enabled": True,
                "notification_methods": ["file", "log"],
                "email_enabled": False,
                "email_recipients": [],
                "slack_enabled": False,
                "slack_webhook_url": "",
                "sync_interval": 300,
                "validation_interval": 180,
                "notification_check_interval": 600,
                "force_sync_interval": 3600,
                "health_check_interval": 900,
                "significant_change_threshold": 5.0,
                "notification_cooldown": 3600,
                "alert_on_inconsistencies": True,
                "health_monitoring_enabled": True,
                "strict_validation": True,
                "auto_fix_inconsistencies": False,
                "log_level": "INFO",
                "max_log_files": 10,
                "max_report_files": 50,
                "validation_rules": {
                    "check_internal_links": True,
                    "validate_path_references": True,
                    "cross_file_consistency": True,
                    "progressive_structure_compliance": True,
                    "health_integration": True
                },
                "severity_thresholds": {
                    "critical": 0,
                    "high": 3,
                    "medium": 10,
                    "low": 25
                }
            }
            
            config_file = self.config_dir / "enhanced_doc_sync_config.json"
            with open(config_file, 'w') as f:
                json.dump(doc_sync_config, f, indent=2)
            
            print(f"  ✅ Created configuration: {config_file}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating configurations: {e}")
            return False

    def _install_hooks(self) -> bool:
        """Install enhanced pre-commit hooks"""
        try:
            from enhanced_doc_sync import create_enhanced_pre_commit_hook
            success = create_enhanced_pre_commit_hook()
            
            if success:
                print("  ✅ Enhanced pre-commit hooks installed")
            else:
                print("  ❌ Failed to install pre-commit hooks")
            
            return success
            
        except Exception as e:
            print(f"  ❌ Error installing hooks: {e}")
            return False

    def _create_systemd_service(self) -> bool:
        """Create systemd service file"""
        try:
            from enhanced_automated_doc_sync import create_enhanced_systemd_service
            service_file = create_enhanced_systemd_service()
            print(f"  ✅ Created systemd service: {service_file}")
            print("     To install: sudo cp enhanced-claude-pm-doc-sync.service /etc/systemd/system/")
            print("     To enable: sudo systemctl enable enhanced-claude-pm-doc-sync.service")
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating systemd service: {e}")
            return False

    def _create_cron_job(self) -> bool:
        """Create cron job file"""
        try:
            from enhanced_automated_doc_sync import create_enhanced_cron_job
            cron_file = create_enhanced_cron_job()
            print(f"  ✅ Created cron job: {cron_file}")
            print(f"     To install: crontab {cron_file}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating cron job: {e}")
            return False

    def _setup_cli_aliases(self) -> bool:
        """Setup CLI aliases for easy access"""
        try:
            # Create a convenient wrapper script
            wrapper_script = self.claude_pm_root / "doc-validate"
            wrapper_content = f"""#!/bin/bash
# Enhanced Documentation Validation CLI Wrapper
exec python3 "{self.scripts_dir}/doc_validation_cli.py" "$@"
"""
            
            with open(wrapper_script, 'w') as f:
                f.write(wrapper_content)
            
            # Make executable
            os.chmod(wrapper_script, 0o755)
            
            print(f"  ✅ Created CLI wrapper: {wrapper_script}")
            print("     Usage: ./doc-validate status")
            print("     Add to PATH for global access")
            return True
            
        except Exception as e:
            print(f"  ❌ Error setting up CLI aliases: {e}")
            return False

    def _run_initial_validation(self) -> bool:
        """Run initial system validation"""
        try:
            print("  🔍 Running initial validation...")
            
            # Import and run validation
            from enhanced_doc_sync import EnhancedDocumentationSyncManager
            sync_manager = EnhancedDocumentationSyncManager(str(self.claude_pm_root))
            
            success = sync_manager.sync_documentation(validate_only=True)
            
            if success:
                print("  ✅ Initial validation completed successfully")
            else:
                print("  ⚠️ Initial validation found issues (this is expected)")
                print("     Run './doc-validate status' for details")
            
            return True  # Always return True for initial setup
            
        except Exception as e:
            print(f"  ❌ Error running initial validation: {e}")
            return False

    def _setup_health_integration(self) -> bool:
        """Setup health monitoring integration"""
        try:
            # Create health monitoring configuration
            health_config = {
                "documentation_monitoring": {
                    "enabled": True,
                    "check_interval": 900,
                    "alert_thresholds": {
                        "critical_issues": 1,
                        "broken_links": 5,
                        "inconsistencies": 3
                    },
                    "integration_endpoints": {
                        "health_file": str(self.logs_dir / "enhanced_doc_sync_health.json"),
                        "stats_file": str(self.logs_dir / "latest_enhanced_doc_stats.json")
                    }
                }
            }
            
            health_config_file = self.config_dir / "health_monitoring_config.json"
            with open(health_config_file, 'w') as f:
                json.dump(health_config, f, indent=2)
            
            print(f"  ✅ Created health monitoring config: {health_config_file}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error setting up health integration: {e}")
            return False

    def _print_next_steps(self):
        """Print next steps for the user"""
        print("\n📋 Next Steps:")
        print("1. Run validation: ./doc-validate status")
        print("2. Fix any issues: ./doc-validate sync")
        print("3. Install systemd service (optional):")
        print("   sudo cp enhanced-claude-pm-doc-sync.service /etc/systemd/system/")
        print("   sudo systemctl enable enhanced-claude-pm-doc-sync.service")
        print("4. Or install cron job (alternative):")
        print("   crontab enhanced-claude-pm-doc-sync.cron")
        print("5. Check health: ./doc-validate health")
        
        print("\n🔧 Available Commands:")
        print("  ./doc-validate status          # Show current status")
        print("  ./doc-validate validate        # Run validation")
        print("  ./doc-validate sync            # Run synchronization")
        print("  ./doc-validate fix-links       # Fix broken links")
        print("  ./doc-validate notify          # Check notifications")
        print("  ./doc-validate health          # Health check")
        print("  ./doc-validate report          # Show latest report")
        
        print(f"\n📁 Key Files:")
        print(f"  Config: {self.config_dir}/enhanced_doc_sync_config.json")
        print(f"  Logs: {self.logs_dir}/enhanced_doc_sync.log")
        print(f"  Reports: {self.logs_dir}/enhanced_doc_sync_report_*.md")
        print(f"  Health: {self.logs_dir}/enhanced_doc_sync_health.json")

    def verify_system(self) -> bool:
        """Verify the enhanced documentation system is working"""
        print("🔍 Verifying Enhanced Documentation System")
        print("=" * 50)
        
        checks = [
            ("Configuration files", self._check_configs),
            ("Pre-commit hooks", self._check_hooks),
            ("Core scripts", self._check_scripts),
            ("System permissions", self._check_permissions),
            ("Initial validation", self._check_validation)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            print(f"\n{check_name}:")
            passed = check_func()
            all_passed &= passed
            print(f"  {'✅ PASS' if passed else '❌ FAIL'}")
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ System verification completed successfully!")
        else:
            print("❌ System verification found issues. Please review above.")
        
        return all_passed

    def _check_configs(self) -> bool:
        """Check configuration files"""
        try:
            config_file = self.config_dir / "enhanced_doc_sync_config.json"
            if not config_file.exists():
                print(f"  ❌ Missing: {config_file}")
                return False
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            required_keys = ["claude_pm_root", "notifications_enabled", "validation_rules"]
            for key in required_keys:
                if key not in config:
                    print(f"  ❌ Missing config key: {key}")
                    return False
            
            print(f"  ✅ Configuration valid: {config_file}")
            return True
            
        except Exception as e:
            print(f"  ❌ Config check failed: {e}")
            return False

    def _check_hooks(self) -> bool:
        """Check pre-commit hooks"""
        try:
            hook_file = self.claude_pm_root / ".git" / "hooks" / "pre-commit"
            if not hook_file.exists():
                print(f"  ❌ Missing: {hook_file}")
                return False
            
            if not os.access(hook_file, os.X_OK):
                print(f"  ❌ Not executable: {hook_file}")
                return False
            
            print(f"  ✅ Pre-commit hook installed and executable")
            return True
            
        except Exception as e:
            print(f"  ❌ Hook check failed: {e}")
            return False

    def _check_scripts(self) -> bool:
        """Check core scripts"""
        try:
            required_scripts = [
                "enhanced_doc_sync.py",
                "enhanced_doc_notification_system.py",
                "enhanced_automated_doc_sync.py",
                "doc_validation_cli.py"
            ]
            
            for script in required_scripts:
                script_path = self.scripts_dir / script
                if not script_path.exists():
                    print(f"  ❌ Missing: {script_path}")
                    return False
            
            print(f"  ✅ All core scripts present")
            return True
            
        except Exception as e:
            print(f"  ❌ Script check failed: {e}")
            return False

    def _check_permissions(self) -> bool:
        """Check system permissions"""
        try:
            # Check directory permissions
            for directory in [self.logs_dir, self.config_dir]:
                if not os.access(directory, os.W_OK):
                    print(f"  ❌ No write permission: {directory}")
                    return False
            
            print(f"  ✅ Directory permissions OK")
            return True
            
        except Exception as e:
            print(f"  ❌ Permission check failed: {e}")
            return False

    def _check_validation(self) -> bool:
        """Check that validation can run"""
        try:
            from enhanced_doc_sync import EnhancedDocumentationSyncManager
            sync_manager = EnhancedDocumentationSyncManager(str(self.claude_pm_root))
            
            # Quick validation test
            tickets = sync_manager.parse_progressive_tickets()
            if len(tickets) == 0:
                print(f"  ❌ No tickets parsed from progressive structure")
                return False
            
            print(f"  ✅ Validation system functional ({len(tickets)} tickets found)")
            return True
            
        except Exception as e:
            print(f"  ❌ Validation check failed: {e}")
            return False


def main():
    """Main setup entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Documentation System Setup for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root",
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing system, don't setup"
    )
    
    args = parser.parse_args()
    
    setup = EnhancedDocSystemSetup(args.claude_pm_root)
    
    if args.verify_only:
        success = setup.verify_system()
    else:
        success = setup.setup_complete_system()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())