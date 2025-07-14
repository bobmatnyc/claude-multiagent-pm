#!/usr/bin/env python3
"""
Unified Deployment Strategy
==========================

Enhanced symlink-based deployment system that ensures execution consistency
and prevents deployment/execution mismatches through reliable symlink management.

Features:
- Enhanced symlink management with forced recreation
- Deployment validation and integrity checking
- Single source of truth for all executable scripts
- Automatic PATH resolution and validation
- Version consistency across all script locations
- Post-deployment validation and testing
- Comprehensive error handling and recovery
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
from typing import Dict, List, Optional, Tuple, Union
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedDeploymentManager:
    """
    Manages unified deployment strategy using enhanced symlink management
    to prevent script inconsistencies and ensure execution matches deployment.
    """
    
    def __init__(self):
        self.framework_root = Path(__file__).parent.parent
        self.bin_dir = self.framework_root / "bin"
        self.target_dir = Path.home() / ".local" / "bin"
        self.deployment_config_dir = Path.home() / ".local" / ".claude-pm"
        self.deployment_config_file = self.deployment_config_dir / "unified_deployment.json"
        
        # Ensure directories exist
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Scripts to manage with source-of-truth approach
        self.managed_scripts = {
            "claude-pm": {
                "source": self.bin_dir / "claude-pm",
                "target": self.target_dir / "claude-pm",
                "type": "python",
                "description": "Main Claude PM Framework CLI",
                "deployment_strategy": "symlink"
            },
            "cmpm": {
                "source": self.bin_dir / "cmpm",
                "target": self.target_dir / "cmpm",
                "type": "python",
                "description": "CMPM slash command wrapper",
                "deployment_strategy": "symlink"
            }
        }
        
        # Version tracking
        self.version_file = self.framework_root / "VERSION"
        self.package_json = self.framework_root / "package.json"
        
    def get_framework_version(self) -> str:
        """Get the current framework version."""
        try:
            if self.package_json.exists():
                import json
                with open(self.package_json) as f:
                    data = json.load(f)
                    return data.get('version', 'unknown')
            elif self.version_file.exists():
                return self.version_file.read_text().strip()
            else:
                return 'unknown'
        except Exception as e:
            logger.warning(f"Could not determine framework version: {e}")
            return 'unknown'
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def is_symlink_valid(self, symlink_path: Path, target_path: Path) -> bool:
        """
        Check if a symlink is valid and points to the correct target.
        
        Args:
            symlink_path: Path to the symlink
            target_path: Expected target path
            
        Returns:
            bool: True if symlink is valid and points to target
        """
        try:
            if not symlink_path.exists():
                return False
                
            if not symlink_path.is_symlink():
                return False
                
            # Check if symlink points to the correct target
            resolved_target = symlink_path.resolve()
            expected_target = target_path.resolve()
            
            return resolved_target == expected_target
            
        except Exception as e:
            logger.warning(f"Could not validate symlink {symlink_path}: {e}")
            return False
    
    def create_enhanced_symlink(self, source_path: Path, target_path: Path, force: bool = True) -> bool:
        """
        Create enhanced symlink with forced recreation and validation.
        
        Args:
            source_path: Source file to link to
            target_path: Target symlink path
            force: Force recreation of existing symlinks
            
        Returns:
            bool: True if symlink created successfully
        """
        try:
            # Ensure source exists
            if not source_path.exists():
                logger.error(f"Source file {source_path} does not exist")
                return False
                
            # Remove existing target if force is True
            if force and target_path.exists():
                if target_path.is_symlink():
                    target_path.unlink()
                    logger.info(f"Removed existing symlink: {target_path}")
                else:
                    # Create backup if it's a regular file
                    backup_path = target_path.with_suffix(f"{target_path.suffix}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    shutil.move(target_path, backup_path)
                    logger.info(f"Backed up regular file to: {backup_path}")
            
            # Create symlink
            target_path.symlink_to(source_path)
            logger.info(f"Created symlink: {target_path} -> {source_path}")
            
            # Validate symlink
            if self.is_symlink_valid(target_path, source_path):
                logger.info(f"Symlink validation successful: {target_path}")
                return True
            else:
                logger.error(f"Symlink validation failed: {target_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create symlink {target_path} -> {source_path}: {e}")
            return False
    
    def validate_path_resolution(self, script_name: str) -> Dict[str, any]:
        """
        Validate that PATH resolution points to the correct script.
        
        Args:
            script_name: Name of the script to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Use 'which' to find the script in PATH
            result = subprocess.run(
                ['which', script_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    'valid': False,
                    'error': f"Script '{script_name}' not found in PATH",
                    'path_location': None,
                    'expected_location': None
                }
            
            path_location = Path(result.stdout.strip())
            expected_location = self.managed_scripts[script_name]["target"]
            
            # Check if PATH points to our managed location
            path_resolved = path_location.resolve()
            expected_resolved = expected_location.resolve()
            
            if path_resolved == expected_resolved:
                return {
                    'valid': True,
                    'path_location': str(path_location),
                    'expected_location': str(expected_location),
                    'resolved_target': str(path_resolved)
                }
            else:
                return {
                    'valid': False,
                    'error': f"PATH points to {path_location} but expected {expected_location}",
                    'path_location': str(path_location),
                    'expected_location': str(expected_location),
                    'resolved_target': str(path_resolved)
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f"Failed to validate PATH resolution: {e}",
                'path_location': None,
                'expected_location': None
            }
    
    def deploy_script_unified(self, script_name: str) -> bool:
        """
        Deploy a script using unified deployment strategy.
        
        Args:
            script_name: Name of the script to deploy
            
        Returns:
            bool: True if deployment successful
        """
        if script_name not in self.managed_scripts:
            logger.error(f"Unknown script: {script_name}")
            return False
            
        script_info = self.managed_scripts[script_name]
        source_path = script_info["source"]
        target_path = script_info["target"]
        strategy = script_info["deployment_strategy"]
        
        logger.info(f"Deploying {script_name} using {strategy} strategy")
        
        if strategy == "symlink":
            # Use enhanced symlink management
            success = self.create_enhanced_symlink(source_path, target_path, force=True)
            
            if success:
                # Validate PATH resolution
                path_validation = self.validate_path_resolution(script_name)
                if not path_validation['valid']:
                    logger.warning(f"PATH validation failed for {script_name}: {path_validation['error']}")
                    # Continue deployment but note the issue
                
                # Update deployment config
                self.update_deployment_config(script_name, source_path, target_path, strategy)
                logger.info(f"Successfully deployed {script_name}")
                return True
            else:
                logger.error(f"Failed to deploy {script_name}")
                return False
        else:
            logger.error(f"Unknown deployment strategy: {strategy}")
            return False
    
    def update_deployment_config(self, script_name: str, source_path: Path, target_path: Path, strategy: str):
        """Update deployment configuration with deployment information."""
        try:
            config = self.load_deployment_config()
            
            # Calculate metadata
            source_checksum = self.calculate_checksum(source_path)
            framework_version = self.get_framework_version()
            
            # Update deployment record
            config["deployments"][script_name] = {
                "deployed_at": datetime.now().isoformat(),
                "source_path": str(source_path),
                "target_path": str(target_path),
                "deployment_strategy": strategy,
                "source_checksum": source_checksum,
                "framework_version": framework_version,
                "is_symlink": target_path.is_symlink() if target_path.exists() else False,
                "path_validation": self.validate_path_resolution(script_name)
            }
            
            # Add to history
            config["history"].append({
                "action": "deploy",
                "script": script_name,
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy,
                "source_checksum": source_checksum,
                "framework_version": framework_version
            })
            
            # Keep only last 100 history entries
            config["history"] = config["history"][-100:]
            
            self.save_deployment_config(config)
            
        except Exception as e:
            logger.error(f"Failed to update deployment config: {e}")
    
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
            "version": "2.0",
            "deployment_strategy": "unified_symlink"
        }
    
    def save_deployment_config(self, config: Dict):
        """Save deployment configuration."""
        try:
            with open(self.deployment_config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save deployment config: {e}")
    
    def verify_deployment_integrity(self) -> Dict[str, Dict]:
        """
        Verify the integrity of all deployed scripts.
        
        Returns:
            dict: Verification results for each script
        """
        verification_results = {}
        
        for script_name, script_info in self.managed_scripts.items():
            source_path = script_info["source"]
            target_path = script_info["target"]
            
            # Check if source exists
            if not source_path.exists():
                verification_results[script_name] = {
                    "status": "source_missing",
                    "message": f"Source file {source_path} does not exist"
                }
                continue
            
            # Check if target exists
            if not target_path.exists():
                verification_results[script_name] = {
                    "status": "target_missing",
                    "message": f"Target {target_path} does not exist"
                }
                continue
            
            # Check if symlink is valid
            if not self.is_symlink_valid(target_path, source_path):
                verification_results[script_name] = {
                    "status": "symlink_invalid",
                    "message": f"Symlink {target_path} is invalid or points to wrong target"
                }
                continue
            
            # Check PATH resolution
            path_validation = self.validate_path_resolution(script_name)
            if not path_validation['valid']:
                verification_results[script_name] = {
                    "status": "path_mismatch",
                    "message": f"PATH resolution issue: {path_validation['error']}"
                }
                continue
            
            # Test script execution
            try:
                result = subprocess.run(
                    [str(target_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    verification_results[script_name] = {
                        "status": "verified",
                        "message": "Script deployment verified successfully",
                        "version_output": result.stdout.strip()
                    }
                else:
                    verification_results[script_name] = {
                        "status": "execution_failed",
                        "message": f"Script execution failed: {result.stderr.strip()}"
                    }
                    
            except subprocess.TimeoutExpired:
                verification_results[script_name] = {
                    "status": "execution_timeout",
                    "message": "Script execution timed out"
                }
            except Exception as e:
                verification_results[script_name] = {
                    "status": "execution_error",
                    "message": f"Script execution error: {e}"
                }
        
        return verification_results
    
    def deploy_all_scripts(self) -> Dict[str, bool]:
        """Deploy all managed scripts using unified strategy."""
        logger.info("Starting unified deployment for all scripts")
        
        results = {}
        for script_name in self.managed_scripts:
            results[script_name] = self.deploy_script_unified(script_name)
        
        # Verify all deployments
        verification_results = self.verify_deployment_integrity()
        
        logger.info("Unified deployment completed")
        return results
    
    def check_deployment_health(self) -> Dict[str, any]:
        """Check the health of the deployment system."""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "framework_version": self.get_framework_version(),
            "deployment_strategy": "unified_symlink",
            "scripts": {},
            "overall_status": "healthy"
        }
        
        verification_results = self.verify_deployment_integrity()
        
        for script_name, verification in verification_results.items():
            script_info = self.managed_scripts[script_name]
            
            health_report["scripts"][script_name] = {
                "source_path": str(script_info["source"]),
                "target_path": str(script_info["target"]),
                "deployment_strategy": script_info["deployment_strategy"],
                "verification_status": verification["status"],
                "verification_message": verification["message"],
                "path_validation": self.validate_path_resolution(script_name)
            }
            
            # Update overall status
            if verification["status"] != "verified":
                health_report["overall_status"] = "unhealthy"
        
        return health_report
    
    def fix_deployment_issues(self) -> Dict[str, bool]:
        """Automatically fix common deployment issues."""
        logger.info("Attempting to fix deployment issues")
        
        fix_results = {}
        
        # Check each script and fix issues
        for script_name, script_info in self.managed_scripts.items():
            try:
                source_path = script_info["source"]
                target_path = script_info["target"]
                
                # Fix missing or invalid symlinks
                if not target_path.exists() or not self.is_symlink_valid(target_path, source_path):
                    logger.info(f"Fixing symlink for {script_name}")
                    fix_results[script_name] = self.create_enhanced_symlink(source_path, target_path, force=True)
                else:
                    fix_results[script_name] = True
                    
            except Exception as e:
                logger.error(f"Failed to fix {script_name}: {e}")
                fix_results[script_name] = False
        
        return fix_results
    
    def print_deployment_status(self):
        """Print comprehensive deployment status report."""
        print("\n" + "="*80)
        print("🚀 CLAUDE PM FRAMEWORK - UNIFIED DEPLOYMENT STATUS")
        print("="*80)
        print(f"📅 Status Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Deployment Strategy: Enhanced Symlink Management")
        print(f"📦 Framework Version: {self.get_framework_version()}")
        print()
        
        health_report = self.check_deployment_health()
        
        print("📋 SCRIPT DEPLOYMENT STATUS:")
        print("-" * 60)
        
        for script_name, script_health in health_report["scripts"].items():
            status_emoji = "✅" if script_health["verification_status"] == "verified" else "❌"
            
            print(f"{status_emoji} {script_name}")
            print(f"   Source: {script_health['source_path']}")
            print(f"   Target: {script_health['target_path']}")
            print(f"   Strategy: {script_health['deployment_strategy']}")
            print(f"   Status: {script_health['verification_status']}")
            print(f"   Message: {script_health['verification_message']}")
            
            # PATH validation details
            path_val = script_health["path_validation"]
            if path_val["valid"]:
                print(f"   PATH: ✅ Resolves correctly to {path_val['resolved_target']}")
            else:
                print(f"   PATH: ❌ {path_val['error']}")
            
            print()
        
        # Overall health summary
        print("📊 DEPLOYMENT HEALTH SUMMARY:")
        print("-" * 60)
        
        total_scripts = len(self.managed_scripts)
        verified_scripts = sum(1 for s in health_report["scripts"].values() if s["verification_status"] == "verified")
        
        print(f"Total Scripts: {total_scripts}")
        print(f"Verified: {verified_scripts}/{total_scripts}")
        print(f"Overall Status: {health_report['overall_status'].upper()}")
        
        if health_report["overall_status"] == "healthy":
            print("🎉 All scripts are properly deployed and verified!")
        else:
            print("⚠️  Some scripts have issues. Run with --fix to attempt automatic repair.")
        
        print()
        print("="*80)


def main():
    """Main entry point for unified deployment management."""
    parser = argparse.ArgumentParser(
        description="Claude PM Framework Unified Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy all scripts using unified strategy"
    )
    
    parser.add_argument(
        "--deploy-script",
        metavar="SCRIPT_NAME",
        help="Deploy specific script using unified strategy"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify deployment integrity"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show comprehensive deployment status"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check deployment health"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix deployment issues"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    manager = UnifiedDeploymentManager()
    
    try:
        if args.deploy:
            print("🚀 Starting unified deployment...")
            results = manager.deploy_all_scripts()
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if success_count == total_count:
                print(f"✅ Successfully deployed {success_count}/{total_count} scripts")
            else:
                print(f"⚠️  Deployed {success_count}/{total_count} scripts with issues")
                sys.exit(1)
        
        elif args.deploy_script:
            print(f"🚀 Deploying {args.deploy_script} using unified strategy...")
            success = manager.deploy_script_unified(args.deploy_script)
            
            if success:
                print(f"✅ Successfully deployed {args.deploy_script}")
            else:
                print(f"❌ Failed to deploy {args.deploy_script}")
                sys.exit(1)
        
        elif args.verify:
            print("🔍 Verifying deployment integrity...")
            verification_results = manager.verify_deployment_integrity()
            
            all_verified = all(
                result["status"] == "verified"
                for result in verification_results.values()
            )
            
            if all_verified:
                print("✅ All scripts verified successfully")
            else:
                print("❌ Some scripts failed verification:")
                for script_name, result in verification_results.items():
                    if result["status"] != "verified":
                        print(f"   {script_name}: {result['message']}")
                sys.exit(1)
        
        elif args.health:
            print("🏥 Checking deployment health...")
            health_report = manager.check_deployment_health()
            
            if health_report["overall_status"] == "healthy":
                print("✅ Deployment system is healthy")
            else:
                print("❌ Deployment system has issues")
                sys.exit(1)
        
        elif args.fix:
            print("🔧 Attempting to fix deployment issues...")
            fix_results = manager.fix_deployment_issues()
            
            fixed_count = sum(1 for success in fix_results.values() if success)
            total_count = len(fix_results)
            
            if fixed_count == total_count:
                print(f"✅ Successfully fixed {fixed_count}/{total_count} scripts")
            else:
                print(f"⚠️  Fixed {fixed_count}/{total_count} scripts")
                sys.exit(1)
        
        elif args.status:
            manager.print_deployment_status()
        
        else:
            # Default behavior - show status
            manager.print_deployment_status()
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()