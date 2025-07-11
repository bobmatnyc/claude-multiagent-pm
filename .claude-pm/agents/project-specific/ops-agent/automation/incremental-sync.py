#!/usr/bin/env python3
"""
Claude-MultiAgent-PM Ops Agent - Incremental Sync Automation
Synchronize changes without full redeployment for efficient development workflow.

Author: Claude-MultiAgent-PM Ops Agent
Version: 1.0.0
Date: 2025-07-11
"""

import os
import sys
import shutil
import subprocess
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/masa/Projects/claude-multiagent-pm/logs/ops-agent-sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('claude-multiagent-pm-ops-sync')

class IncrementalSyncManager:
    """Manages incremental synchronization of framework components."""
    
    def __init__(self):
        self.project_root = Path("/Users/masa/Projects/claude-multiagent-pm")
        self.deployment_target = Path("/Users/masa/.local")
        self.sync_timestamp = datetime.now().isoformat()
        
        # Sync paths configuration
        self.sync_configs = {
            "scripts": {
                "source": self.project_root / "scripts",
                "target": self.deployment_target / "scripts",
                "sync_method": "rsync",
                "validation": True,
                "backup": True
            },
            "binaries": {
                "source": self.project_root / "bin",
                "target": self.deployment_target / "bin",
                "sync_method": "copy",
                "validation": True,
                "permissions": "755"
            },
            "claude_md": {
                "source": self.project_root / "framework" / "CLAUDE.md",
                "targets": [
                    self.deployment_target / "CLAUDE.md",
                    Path("/Users/masa/Projects/CLAUDE.md")
                ],
                "sync_method": "template",
                "validation": True,
                "backup": True
            },
            "config": {
                "source": self.project_root / ".claude-pm" / "config",
                "target": self.deployment_target / ".claude-pm" / "config",
                "sync_method": "selective",
                "validation": True,
                "backup": True
            }
        }
        
        # State tracking
        self.sync_state_file = self.project_root / ".claude-pm" / "cache" / "sync-state.json"
        self.sync_state = self.load_sync_state()
        
        # Results tracking
        self.sync_results = {
            "timestamp": self.sync_timestamp,
            "changes_detected": {},
            "sync_operations": {},
            "validations": {},
            "errors": [],
            "warnings": []
        }
    
    def load_sync_state(self) -> Dict:
        """Load previous sync state for change detection."""
        if self.sync_state_file.exists():
            try:
                with open(self.sync_state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Could not load sync state: {e}")
                return {}
        return {}
    
    def save_sync_state(self) -> None:
        """Save current sync state for future change detection."""
        try:
            self.sync_state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sync_state_file, 'w') as f:
                json.dump(self.sync_state, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Could not save sync state: {e}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def calculate_directory_hash(self, dir_path: Path, extensions: Set[str] = None) -> str:
        """Calculate combined hash of directory contents."""
        if not dir_path.exists():
            return ""
        
        file_hashes = []
        try:
            for file_path in sorted(dir_path.rglob("*")):
                if file_path.is_file():
                    if extensions is None or file_path.suffix in extensions:
                        rel_path = file_path.relative_to(dir_path)
                        file_hash = self.calculate_file_hash(file_path)
                        file_hashes.append(f"{rel_path}:{file_hash}")
            
            combined = "|".join(file_hashes)
            return hashlib.sha256(combined.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate directory hash for {dir_path}: {e}")
            return ""
    
    def detect_changes(self) -> Dict[str, List[str]]:
        """Detect changes in source files and directories."""
        logger.info("🔍 Detecting changes since last sync...")
        
        changes = {}
        
        for component, config in self.sync_configs.items():
            component_changes = []
            
            if component == "scripts":
                # Check scripts directory
                current_hash = self.calculate_directory_hash(
                    config["source"], 
                    {".py", ".sh", ".js", ".json"}
                )
                previous_hash = self.sync_state.get(f"{component}_hash", "")
                
                if current_hash != previous_hash:
                    component_changes.append("scripts directory modified")
                    self.sync_state[f"{component}_hash"] = current_hash
            
            elif component == "binaries":
                # Check individual binary files
                for bin_file in config["source"].glob("*"):
                    if bin_file.is_file():
                        current_hash = self.calculate_file_hash(bin_file)
                        previous_hash = self.sync_state.get(f"binary_{bin_file.name}", "")
                        
                        if current_hash != previous_hash:
                            component_changes.append(f"binary {bin_file.name} modified")
                            self.sync_state[f"binary_{bin_file.name}"] = current_hash
            
            elif component == "claude_md":
                # Check CLAUDE.md template
                if config["source"].exists():
                    current_hash = self.calculate_file_hash(config["source"])
                    previous_hash = self.sync_state.get("claude_md_template", "")
                    
                    if current_hash != previous_hash:
                        component_changes.append("CLAUDE.md template modified")
                        self.sync_state["claude_md_template"] = current_hash
            
            elif component == "config":
                # Check configuration files
                current_hash = self.calculate_directory_hash(
                    config["source"],
                    {".json", ".yaml", ".yml"}
                )
                previous_hash = self.sync_state.get(f"{component}_hash", "")
                
                if current_hash != previous_hash:
                    component_changes.append("configuration files modified")
                    self.sync_state[f"{component}_hash"] = current_hash
            
            if component_changes:
                changes[component] = component_changes
                logger.info(f"📝 Changes detected in {component}: {component_changes}")
        
        self.sync_results["changes_detected"] = changes
        
        if not changes:
            logger.info("✅ No changes detected - system is up to date")
        
        return changes
    
    def sync_scripts(self) -> bool:
        """Synchronize scripts directory using rsync."""
        logger.info("📝 Synchronizing scripts directory...")
        
        try:
            config = self.sync_configs["scripts"]
            
            # Create backup if requested
            if config.get("backup") and config["target"].exists():
                backup_path = config["target"].with_suffix(".backup")
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(config["target"], backup_path)
                logger.info(f"📋 Scripts backup created: {backup_path}")
            
            # Execute rsync
            rsync_cmd = [
                "rsync", "-av", "--delete",
                f"{config['source']}/",
                f"{config['target']}/"
            ]
            
            result = subprocess.run(rsync_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Scripts synchronized successfully")
                self.sync_results["sync_operations"]["scripts"] = "✅ SUCCESS"
                
                # Set executable permissions for script files
                for script_file in config["target"].rglob("*.py"):
                    script_file.chmod(0o755)
                for script_file in config["target"].rglob("*.sh"):
                    script_file.chmod(0o755)
                
                return True
            else:
                logger.error(f"❌ Scripts sync failed: {result.stderr}")
                self.sync_results["sync_operations"]["scripts"] = f"❌ FAILED: {result.stderr}"
                self.sync_results["errors"].append(f"scripts_sync: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Scripts sync exception: {e}")
            self.sync_results["sync_operations"]["scripts"] = f"❌ EXCEPTION: {e}"
            self.sync_results["errors"].append(f"scripts_sync_exception: {e}")
            return False
    
    def sync_binaries(self) -> bool:
        """Synchronize binary files with permissions."""
        logger.info("⚙️ Synchronizing binary files...")
        
        try:
            config = self.sync_configs["binaries"]
            config["target"].mkdir(parents=True, exist_ok=True)
            
            synced_files = []
            
            for bin_file in config["source"].glob("*"):
                if bin_file.is_file():
                    target_bin = config["target"] / bin_file.name
                    
                    # Copy file
                    shutil.copy2(bin_file, target_bin)
                    
                    # Set permissions
                    target_bin.chmod(int(config.get("permissions", "755"), 8))
                    
                    synced_files.append(bin_file.name)
                    logger.info(f"✅ Binary synchronized: {bin_file.name}")
            
            self.sync_results["sync_operations"]["binaries"] = f"✅ SUCCESS: {synced_files}"
            return True
            
        except Exception as e:
            logger.error(f"❌ Binary sync failed: {e}")
            self.sync_results["sync_operations"]["binaries"] = f"❌ FAILED: {e}"
            self.sync_results["errors"].append(f"binary_sync: {e}")
            return False
    
    def sync_claude_md(self) -> bool:
        """Synchronize CLAUDE.md with variable substitution."""
        logger.info("📋 Synchronizing CLAUDE.md template...")
        
        try:
            config = self.sync_configs["claude_md"]
            
            # Read template
            with open(config["source"], 'r') as f:
                template_content = f.read()
            
            # Variable substitution
            variables = {
                'FRAMEWORK_VERSION': '4.5.1',
                'DEPLOYMENT_DATE': self.sync_timestamp,
                'DEPLOYMENT_DIR': str(self.deployment_target),
                'PLATFORM': 'darwin',
                'PYTHON_CMD': 'python3',
                'AI_TRACKDOWN_PATH': str(self.deployment_target / 'bin' / 'aitrackdown'),
                'CLAUDE_MD_VERSION': '1.4.5.1',
                'LAST_UPDATED': self.sync_timestamp,
                'CONTENT_HASH': 'a1b2c3d4e5f6789a',
                'DEPLOYMENT_ID': f"claude-pm-{self.sync_timestamp}",
                'PLATFORM_NOTES': 'macOS deployment with incremental sync'
            }
            
            # Substitute variables
            deployed_content = template_content
            for var, value in variables.items():
                deployed_content = deployed_content.replace(f'{{{{{var}}}}}', value)
            
            # Deploy to all targets
            deployed_targets = []
            for target in config["targets"]:
                # Create backup if requested
                if config.get("backup") and target.exists():
                    backup_path = target.with_suffix('.md.backup')
                    shutil.copy2(target, backup_path)
                
                # Create target directory if needed
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Write deployed content
                with open(target, 'w') as f:
                    f.write(deployed_content)
                
                deployed_targets.append(str(target))
                logger.info(f"✅ CLAUDE.md synchronized: {target}")
            
            self.sync_results["sync_operations"]["claude_md"] = f"✅ SUCCESS: {deployed_targets}"
            return True
            
        except Exception as e:
            logger.error(f"❌ CLAUDE.md sync failed: {e}")
            self.sync_results["sync_operations"]["claude_md"] = f"❌ FAILED: {e}"
            self.sync_results["errors"].append(f"claude_md_sync: {e}")
            return False
    
    def sync_config(self) -> bool:
        """Synchronize configuration files selectively."""
        logger.info("⚙️ Synchronizing configuration files...")
        
        try:
            config = self.sync_configs["config"]
            
            # Ensure target directory exists
            config["target"].mkdir(parents=True, exist_ok=True)
            
            # Sync specific config files
            config_files_to_sync = ["dependencies.yaml"]
            synced_files = []
            
            for config_file in config_files_to_sync:
                source_file = config["source"] / config_file
                target_file = config["target"] / config_file
                
                if source_file.exists():
                    # Create backup if requested
                    if config.get("backup") and target_file.exists():
                        backup_path = target_file.with_suffix(f"{target_file.suffix}.backup")
                        shutil.copy2(target_file, backup_path)
                    
                    # Copy file
                    shutil.copy2(source_file, target_file)
                    synced_files.append(config_file)
                    logger.info(f"✅ Config synchronized: {config_file}")
            
            self.sync_results["sync_operations"]["config"] = f"✅ SUCCESS: {synced_files}"
            return True
            
        except Exception as e:
            logger.error(f"❌ Config sync failed: {e}")
            self.sync_results["sync_operations"]["config"] = f"❌ FAILED: {e}"
            self.sync_results["errors"].append(f"config_sync: {e}")
            return False
    
    def validate_sync_operations(self) -> bool:
        """Validate sync operations completed successfully."""
        logger.info("🔍 Validating sync operations...")
        
        validation_results = {}
        overall_success = True
        
        # Validate scripts sync
        scripts_target = self.sync_configs["scripts"]["target"]
        if scripts_target.exists():
            script_count = len(list(scripts_target.rglob("*.py"))) + len(list(scripts_target.rglob("*.sh")))
            validation_results["scripts"] = f"✅ VALID: {script_count} script files"
            logger.info(f"✅ Scripts validation: {script_count} files found")
        else:
            validation_results["scripts"] = "❌ INVALID: Target directory missing"
            overall_success = False
        
        # Validate binaries sync
        binaries_target = self.sync_configs["binaries"]["target"]
        expected_binaries = ["claude-pm", "cmpm", "aitrackdown", "atd"]
        found_binaries = []
        
        for binary in expected_binaries:
            binary_path = binaries_target / binary
            if binary_path.exists() and os.access(binary_path, os.X_OK):
                found_binaries.append(binary)
        
        if found_binaries:
            validation_results["binaries"] = f"✅ VALID: {found_binaries}"
            logger.info(f"✅ Binaries validation: {found_binaries}")
        else:
            validation_results["binaries"] = "❌ INVALID: No executable binaries found"
            overall_success = False
        
        # Validate CLAUDE.md sync
        claude_md_valid = True
        for target in self.sync_configs["claude_md"]["targets"]:
            if target.exists():
                # Check if file contains expected framework version
                with open(target, 'r') as f:
                    content = f.read()
                    if "4.5.1" in content and "claude-multiagent-pm" in content.lower():
                        logger.info(f"✅ CLAUDE.md validation: {target}")
                    else:
                        claude_md_valid = False
                        logger.error(f"❌ CLAUDE.md validation failed: {target}")
            else:
                claude_md_valid = False
                logger.error(f"❌ CLAUDE.md missing: {target}")
        
        validation_results["claude_md"] = "✅ VALID" if claude_md_valid else "❌ INVALID"
        if not claude_md_valid:
            overall_success = False
        
        self.sync_results["validations"] = validation_results
        
        if overall_success:
            logger.info("✅ All sync validations passed")
        else:
            logger.error("❌ Some sync validations failed")
        
        return overall_success
    
    def restart_affected_services(self) -> bool:
        """Restart services affected by sync operations."""
        logger.info("🔄 Checking for services that need restart...")
        
        # For now, just log what would be restarted
        # In a full implementation, this would restart actual services
        
        services_to_restart = []
        
        if "scripts" in self.sync_results["changes_detected"]:
            services_to_restart.append("health-monitoring")
        
        if "binaries" in self.sync_results["changes_detected"]:
            services_to_restart.append("cli-services")
        
        if "claude_md" in self.sync_results["changes_detected"]:
            services_to_restart.append("framework-deployment")
        
        if services_to_restart:
            logger.info(f"🔄 Services requiring restart: {services_to_restart}")
            # Here we would implement actual service restart logic
            self.sync_results["service_restarts"] = services_to_restart
        else:
            logger.info("✅ No services require restart")
            self.sync_results["service_restarts"] = []
        
        return True
    
    def generate_sync_report(self) -> Dict:
        """Generate comprehensive sync report."""
        logger.info("📊 Generating sync report...")
        
        self.sync_results["completed"] = datetime.now().isoformat()
        self.sync_results["duration"] = (
            datetime.fromisoformat(self.sync_results["completed"]) -
            datetime.fromisoformat(self.sync_results["timestamp"])
        ).total_seconds()
        
        # Calculate sync summary
        changes_count = sum(len(changes) for changes in self.sync_results["changes_detected"].values())
        operations_count = len(self.sync_results["sync_operations"])
        errors_count = len(self.sync_results["errors"])
        warnings_count = len(self.sync_results["warnings"])
        
        self.sync_results["summary"] = {
            "changes_detected": changes_count,
            "operations_performed": operations_count,
            "errors": errors_count,
            "warnings": warnings_count,
            "overall_status": "✅ SUCCESS" if errors_count == 0 else f"❌ PARTIAL: {errors_count} errors"
        }
        
        # Save report
        report_path = self.project_root / "logs" / "incremental-sync-report.json"
        with open(report_path, 'w') as f:
            json.dump(self.sync_results, f, indent=2)
        
        logger.info(f"📊 Sync report saved: {report_path}")
        return self.sync_results
    
    def execute_incremental_sync(self) -> bool:
        """Execute incremental synchronization process."""
        logger.info("🔄 Starting incremental synchronization...")
        
        # Detect changes
        changes = self.detect_changes()
        
        if not changes:
            logger.info("✅ No changes detected - synchronization not needed")
            self.save_sync_state()
            return True
        
        # Execute sync operations based on detected changes
        sync_success = True
        
        if "scripts" in changes:
            if not self.sync_scripts():
                sync_success = False
        
        if "binaries" in changes:
            if not self.sync_binaries():
                sync_success = False
        
        if "claude_md" in changes:
            if not self.sync_claude_md():
                sync_success = False
        
        if "config" in changes:
            if not self.sync_config():
                sync_success = False
        
        # Validate sync operations
        if not self.validate_sync_operations():
            sync_success = False
        
        # Restart affected services
        self.restart_affected_services()
        
        # Save sync state and generate report
        self.save_sync_state()
        report = self.generate_sync_report()
        
        if sync_success:
            logger.info("🎉 Incremental synchronization completed successfully!")
            return True
        else:
            logger.error("❌ Incremental synchronization completed with errors")
            return False

def main():
    """Main sync execution."""
    print("🔄 Claude-MultiAgent-PM Ops Agent - Incremental Sync")
    print("=" * 60)
    
    sync_manager = IncrementalSyncManager()
    success = sync_manager.execute_incremental_sync()
    
    print("=" * 60)
    if success:
        print("✅ Incremental sync completed successfully!")
        sys.exit(0)
    else:
        print("❌ Incremental sync completed with errors!")
        sys.exit(1)

if __name__ == "__main__":
    main()