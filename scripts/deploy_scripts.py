#!/usr/bin/env python3
"""
Script Deployment Automation System
===================================

Automated deployment system to ensure script changes are properly deployed and synchronized.
Prevents issues where users run outdated scripts by implementing version checking and
automated deployment with checksums and drift detection.

Features:
- Version checking to detect script drift
- Checksum validation for integrity
- Automated deployment to ~/.local/bin/
- Integration with existing framework deployment
- Rollback capabilities
- Deployment history tracking

Usage:
    python scripts/deploy_scripts.py --deploy
    python scripts/deploy_scripts.py --check
    python scripts/deploy_scripts.py --status
    python scripts/deploy_scripts.py --rollback
"""

import os
import sys
import json
import hashlib
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScriptDeploymentManager:
    """Manages deployment and synchronization of framework scripts."""
    
    def __init__(self):
        self.framework_root = Path(__file__).parent.parent
        self.bin_dir = self.framework_root / "bin"
        self.target_dir = Path.home() / ".local" / "bin"
        self.deployment_config_dir = Path.home() / ".local" / ".claude-pm"
        self.deployment_config_file = self.deployment_config_dir / "script_deployment.json"
        
        # Integration with existing Claude PM deployment system
        self.main_deployment_config = self.deployment_config_dir / "config.json"
        
        # Ensure directories exist
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Scripts to manage
        self.managed_scripts = {
            "claude-pm": {
                "source": self.bin_dir / "claude-pm",
                "target": self.target_dir / "claude-pm",
                "type": "node",
                "description": "Main Claude PM Framework CLI"
            },
            "cmpm": {
                "source": self.bin_dir / "cmpm", 
                "target": self.target_dir / "cmpm",
                "type": "python",
                "description": "CMPM slash command wrapper"
            }
        }
        
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _inject_version_into_script(self, source_path: Path, target_path: Path):
        """Inject VERSION file content into script for local deployment."""
        try:
            # Read main VERSION file
            version_file = self.framework_root / "VERSION"
            if not version_file.exists():
                logger.warning("VERSION file not found, using package.json fallback")
                # Try package.json as fallback
                package_file = self.framework_root / "package.json"
                if package_file.exists():
                    import json
                    with open(package_file) as f:
                        pkg_data = json.load(f)
                        version_content = pkg_data.get('version', 'unknown')
                else:
                    version_content = 'unknown'
            else:
                version_content = version_file.read_text().strip()
            
            # Also deploy framework version for template management
            framework_version_file = self.framework_root / "framework" / "VERSION"
            if framework_version_file.exists():
                framework_serial = framework_version_file.read_text().strip()
                # Combined version: CLAUDE_MD_VERSION-FRAMEWORK_VERSION = main_version-serial
                combined_framework_version = f"{version_content}-{framework_serial}"
                
                # Create framework version file in deployment directory
                framework_version_target = self.target_dir / ".framework_version"
                with open(framework_version_target, 'w') as f:
                    f.write(combined_framework_version)
                logger.info(f"Deployed framework version: {combined_framework_version}")
            else:
                logger.warning("framework/VERSION not found, skipping framework version deployment")
            
            # Read source script
            with open(source_path, 'r') as f:
                script_content = f.read()
            
            # Replace the version resolution function with embedded version
            version_injection = f'''// Embedded version for local deployment
const CLAUDE_PM_VERSION = '{version_content}';'''
            
            # Find and replace the version resolution section
            import re
            
            # Pattern to match the entire version resolution section
            pattern = r'// Universal version resolution.*?const CLAUDE_PM_VERSION = resolveVersion\(\);'
            replacement = version_injection
            
            updated_content = re.sub(pattern, replacement, script_content, flags=re.DOTALL)
            
            # If pattern not found, try simpler pattern
            if updated_content == script_content:
                pattern = r'const CLAUDE_PM_VERSION = resolveVersion\(\);'
                replacement = f"const CLAUDE_PM_VERSION = '{version_content}';"
                updated_content = re.sub(pattern, replacement, script_content)
            
            # Write processed script to target
            with open(target_path, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Injected version '{version_content}' into deployed script")
            
        except Exception as e:
            logger.error(f"Failed to inject version into script: {e}")
            # Fall back to normal copy
            shutil.copy2(source_path, target_path)
    
    def get_script_version(self, script_path: Path, script_type: str) -> str:
        """Extract version information from script."""
        try:
            if script_type == "node":
                # Extract version from Node.js script
                with open(script_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'CLAUDE_PM_VERSION' in line and 'require' in line:
                            # Extract from require('../package.json').version
                            try:
                                package_json = self.framework_root / "package.json"
                                if package_json.exists():
                                    import json
                                    with open(package_json) as pf:
                                        pkg_data = json.load(pf)
                                        return pkg_data.get('version', 'unknown')
                            except Exception:
                                pass
                            break
                return "unknown"
            elif script_type == "python":
                # Extract version from Python script
                with open(script_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'version' in line.lower() or '__version__' in line:
                            # Try to extract version
                            pass
                return "unknown"
            else:
                return "unknown"
        except Exception as e:
            logger.warning(f"Could not extract version from {script_path}: {e}")
            return "unknown"
    
    def load_deployment_config(self) -> Dict:
        """Load deployment configuration."""
        if self.deployment_config_file.exists():
            try:
                with open(self.deployment_config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load deployment config: {e}")
        
        return {
            "deployments": {},
            "history": [],
            "last_check": None,
            "version": "1.0"
        }
    
    def save_deployment_config(self, config: Dict):
        """Save deployment configuration and update main deployment config."""
        try:
            with open(self.deployment_config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            # Update main deployment config with script deployment info
            self.update_main_deployment_config(config)
                
        except Exception as e:
            logger.error(f"Could not save deployment config: {e}")
    
    def update_main_deployment_config(self, script_config: Dict):
        """Update main deployment config with script deployment information."""
        try:
            main_config = {}
            if self.main_deployment_config.exists():
                with open(self.main_deployment_config, 'r') as f:
                    main_config = json.load(f)
            
            # Add script deployment section
            main_config["script_deployments"] = {
                "last_updated": datetime.now().isoformat(),
                "deployment_count": len(script_config.get("deployments", {})),
                "scripts": list(script_config.get("deployments", {}).keys()),
                "version": script_config.get("version", "1.0")
            }
            
            with open(self.main_deployment_config, 'w') as f:
                json.dump(main_config, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Could not update main deployment config: {e}")
    
    def check_script_drift(self) -> Dict[str, Dict]:
        """Check for script drift and return status."""
        drift_report = {}
        config = self.load_deployment_config()
        
        for script_name, script_info in self.managed_scripts.items():
            source_path = script_info["source"]
            target_path = script_info["target"]
            
            if not source_path.exists():
                drift_report[script_name] = {
                    "status": "source_missing",
                    "message": f"Source script {source_path} does not exist"
                }
                continue
                
            if not target_path.exists():
                drift_report[script_name] = {
                    "status": "not_deployed",
                    "message": f"Target script {target_path} does not exist"
                }
                continue
            
            # Calculate checksums
            source_checksum = self.calculate_checksum(source_path)
            target_checksum = self.calculate_checksum(target_path)
            
            # Get versions
            source_version = self.get_script_version(source_path, script_info["type"])
            
            # Check deployment history
            deployed_info = config["deployments"].get(script_name, {})
            last_deployed_checksum = deployed_info.get("checksum", "")
            
            if source_checksum != target_checksum:
                drift_report[script_name] = {
                    "status": "drift_detected",
                    "message": "Source and target checksums differ",
                    "source_checksum": source_checksum,
                    "target_checksum": target_checksum,
                    "source_version": source_version,
                    "needs_deployment": True
                }
            elif source_checksum != last_deployed_checksum:
                drift_report[script_name] = {
                    "status": "untracked_changes",
                    "message": "Changes detected since last deployment",
                    "source_checksum": source_checksum,
                    "target_checksum": target_checksum,
                    "source_version": source_version,
                    "needs_deployment": True
                }
            else:
                drift_report[script_name] = {
                    "status": "synchronized",
                    "message": "Script is up to date",
                    "source_checksum": source_checksum,
                    "target_checksum": target_checksum,
                    "source_version": source_version,
                    "needs_deployment": False
                }
        
        return drift_report
    
    def deploy_script(self, script_name: str) -> bool:
        """Deploy a specific script."""
        if script_name not in self.managed_scripts:
            logger.error(f"Unknown script: {script_name}")
            return False
        
        script_info = self.managed_scripts[script_name]
        source_path = script_info["source"]
        target_path = script_info["target"]
        
        if not source_path.exists():
            logger.error(f"Source script {source_path} does not exist")
            return False
        
        try:
            # Create backup if target exists
            if target_path.exists():
                backup_path = target_path.with_suffix(f"{target_path.suffix}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(target_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Process script content before deploying
            if script_info["type"] == "node" and script_name == "claude-pm":
                # Inject VERSION file content into Node.js script
                self._inject_version_into_script(source_path, target_path)
            else:
                # Copy script as-is for other scripts
                shutil.copy2(source_path, target_path)
            
            # Make executable
            os.chmod(target_path, 0o755)
            
            # Update deployment config
            config = self.load_deployment_config()
            checksum = self.calculate_checksum(source_path)
            version = self.get_script_version(source_path, script_info["type"])
            
            config["deployments"][script_name] = {
                "deployed_at": datetime.now().isoformat(),
                "source_path": str(source_path),
                "target_path": str(target_path),
                "checksum": checksum,
                "version": version,
                "backup_created": target_path.exists()
            }
            
            # Add to history
            config["history"].append({
                "action": "deploy",
                "script": script_name,
                "timestamp": datetime.now().isoformat(),
                "checksum": checksum,
                "version": version
            })
            
            # Keep only last 50 history entries
            config["history"] = config["history"][-50:]
            
            self.save_deployment_config(config)
            
            logger.info(f"Successfully deployed {script_name} to {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy {script_name}: {e}")
            return False
    
    def deploy_all_scripts(self) -> Dict[str, bool]:
        """Deploy all managed scripts."""
        results = {}
        
        for script_name in self.managed_scripts:
            results[script_name] = self.deploy_script(script_name)
        
        return results
    
    def verify_deployment(self) -> Dict[str, bool]:
        """Verify all deployments are working correctly."""
        verification_results = {}
        
        for script_name, script_info in self.managed_scripts.items():
            target_path = script_info["target"]
            
            if not target_path.exists():
                verification_results[script_name] = False
                continue
            
            try:
                if script_info["type"] == "node":
                    # Test Node.js script
                    result = subprocess.run(
                        [str(target_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    verification_results[script_name] = result.returncode == 0
                elif script_info["type"] == "python":
                    # Test Python script
                    result = subprocess.run(
                        [str(target_path), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    verification_results[script_name] = result.returncode == 0
                else:
                    verification_results[script_name] = True
                    
            except Exception as e:
                logger.warning(f"Could not verify {script_name}: {e}")
                verification_results[script_name] = False
        
        return verification_results
    
    def rollback_script(self, script_name: str) -> bool:
        """Rollback a script to its previous version."""
        if script_name not in self.managed_scripts:
            logger.error(f"Unknown script: {script_name}")
            return False
        
        target_path = self.managed_scripts[script_name]["target"]
        
        # Find most recent backup
        backup_pattern = f"{target_path}.backup.*"
        backups = list(target_path.parent.glob(f"{target_path.name}.backup.*"))
        
        if not backups:
            logger.error(f"No backups found for {script_name}")
            return False
        
        # Sort by modification time and get the most recent
        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        
        try:
            shutil.copy2(latest_backup, target_path)
            logger.info(f"Rolled back {script_name} from {latest_backup}")
            
            # Update deployment config
            config = self.load_deployment_config()
            config["history"].append({
                "action": "rollback",
                "script": script_name,
                "timestamp": datetime.now().isoformat(),
                "backup_used": str(latest_backup)
            })
            self.save_deployment_config(config)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback {script_name}: {e}")
            return False
    
    def print_status_report(self):
        """Print comprehensive status report."""
        print("\n" + "="*70)
        print("🚀 CLAUDE PM FRAMEWORK - SCRIPT DEPLOYMENT STATUS")
        print("="*70)
        print(f"📅 Status Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        drift_report = self.check_script_drift()
        verification_results = self.verify_deployment()
        
        print("📋 SCRIPT STATUS:")
        print("-" * 50)
        
        for script_name, script_info in self.managed_scripts.items():
            drift_info = drift_report.get(script_name, {})
            verified = verification_results.get(script_name, False)
            
            status_emoji = "✅" if drift_info.get("status") == "synchronized" and verified else "❌"
            
            print(f"{status_emoji} {script_name}")
            print(f"   Description: {script_info['description']}")
            print(f"   Source: {script_info['source']}")
            print(f"   Target: {script_info['target']}")
            print(f"   Status: {drift_info.get('status', 'unknown')}")
            print(f"   Version: {drift_info.get('source_version', 'unknown')}")
            print(f"   Verified: {'Yes' if verified else 'No'}")
            
            if drift_info.get("needs_deployment"):
                print(f"   ⚠️  Action Required: Deployment needed")
            
            print()
        
        # Summary
        total_scripts = len(self.managed_scripts)
        synchronized = sum(1 for info in drift_report.values() if info.get("status") == "synchronized")
        verified = sum(1 for result in verification_results.values() if result)
        
        print("📊 SUMMARY:")
        print("-" * 50)
        print(f"Total Scripts: {total_scripts}")
        print(f"Synchronized: {synchronized}/{total_scripts}")
        print(f"Verified: {verified}/{total_scripts}")
        
        if synchronized == total_scripts and verified == total_scripts:
            print("🎉 All scripts are synchronized and verified!")
        else:
            print("⚠️  Some scripts need attention. Run with --deploy to fix.")
        
        print()
        print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Claude PM Framework Script Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--deploy", 
        action="store_true",
        help="Deploy all scripts to ~/.local/bin/"
    )
    
    parser.add_argument(
        "--deploy-script",
        metavar="SCRIPT_NAME",
        help="Deploy specific script by name"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for script drift without deploying"
    )
    
    parser.add_argument(
        "--status",
        action="store_true", 
        help="Show comprehensive deployment status"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify deployed scripts are working"
    )
    
    parser.add_argument(
        "--rollback",
        metavar="SCRIPT_NAME",
        help="Rollback specific script to previous version"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show deployment history"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    manager = ScriptDeploymentManager()
    
    try:
        if args.deploy:
            print("🚀 Deploying all scripts...")
            results = manager.deploy_all_scripts()
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if success_count == total_count:
                print(f"✅ Successfully deployed {success_count}/{total_count} scripts")
            else:
                print(f"⚠️  Deployed {success_count}/{total_count} scripts with issues")
                sys.exit(1)
        
        elif args.deploy_script:
            print(f"🚀 Deploying {args.deploy_script}...")
            success = manager.deploy_script(args.deploy_script)
            
            if success:
                print(f"✅ Successfully deployed {args.deploy_script}")
            else:
                print(f"❌ Failed to deploy {args.deploy_script}")
                sys.exit(1)
        
        elif args.check:
            print("🔍 Checking for script drift...")
            drift_report = manager.check_script_drift()
            
            needs_deployment = any(
                info.get("needs_deployment", False) 
                for info in drift_report.values()
            )
            
            if needs_deployment:
                print("⚠️  Script drift detected!")
                for script_name, info in drift_report.items():
                    if info.get("needs_deployment"):
                        print(f"   {script_name}: {info['message']}")
                print("\nRun with --deploy to fix.")
                sys.exit(1)
            else:
                print("✅ All scripts are synchronized")
        
        elif args.verify:
            print("🔍 Verifying deployed scripts...")
            verification_results = manager.verify_deployment()
            
            all_verified = all(verification_results.values())
            
            if all_verified:
                print("✅ All scripts verified successfully")
            else:
                print("❌ Some scripts failed verification:")
                for script_name, verified in verification_results.items():
                    if not verified:
                        print(f"   {script_name}: Failed")
                sys.exit(1)
        
        elif args.rollback:
            print(f"🔄 Rolling back {args.rollback}...")
            success = manager.rollback_script(args.rollback)
            
            if success:
                print(f"✅ Successfully rolled back {args.rollback}")
            else:
                print(f"❌ Failed to rollback {args.rollback}")
                sys.exit(1)
        
        elif args.history:
            config = manager.load_deployment_config()
            history = config.get("history", [])
            
            if not history:
                print("📝 No deployment history found")
            else:
                print("📝 Deployment History:")
                print("-" * 50)
                for entry in history[-10:]:  # Show last 10 entries
                    timestamp = entry.get("timestamp", "unknown")
                    action = entry.get("action", "unknown")
                    script = entry.get("script", "unknown")
                    print(f"{timestamp}: {action} {script}")
        
        elif args.status:
            manager.print_status_report()
        
        else:
            # Default behavior - show status
            manager.print_status_report()
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()