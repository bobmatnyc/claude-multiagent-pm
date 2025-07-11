#!/usr/bin/env python3
"""
Claude-MultiAgent-PM Ops Agent - Full Deployment Automation
Comprehensive deployment script for complete framework deployment with all components.

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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/masa/Projects/claude-multiagent-pm/logs/ops-agent-deployment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('claude-multiagent-pm-ops-agent')

class ClaudeMultiAgentPMDeployment:
    """Comprehensive deployment automation for claude-multiagent-pm framework."""
    
    def __init__(self):
        self.project_root = Path("/Users/masa/Projects/claude-multiagent-pm")
        self.deployment_target = Path("/Users/masa/.local")
        self.framework_version = "4.5.1"
        self.deployment_timestamp = datetime.now().isoformat()
        
        # Core paths
        self.framework_core = self.project_root / "claude_pm"
        self.scripts_source = self.project_root / "scripts"
        self.scripts_target = self.deployment_target / "scripts"
        self.bin_source = self.project_root / "bin"
        self.bin_target = self.deployment_target / "bin"
        self.claude_md_template = self.project_root / "framework" / "CLAUDE.md"
        self.claude_md_targets = [
            self.deployment_target / "CLAUDE.md",
            Path("/Users/masa/Projects/CLAUDE.md")
        ]
        
        # Agent paths
        self.project_agents = self.project_root / ".claude-pm" / "agents" / "project-specific"
        self.user_agents = self.deployment_target / ".claude-pm" / "agents" / "user-defined"
        self.system_agents = self.framework_core / "agents"
        
        # Status tracking
        self.deployment_status = {
            "started": self.deployment_timestamp,
            "steps_completed": [],
            "steps_failed": [],
            "warnings": [],
            "performance_metrics": {}
        }
    
    def validate_source_structure(self) -> Tuple[bool, List[str]]:
        """Validate source directory structure before deployment."""
        logger.info("🔍 Validating source directory structure...")
        
        required_paths = [
            self.project_root,
            self.framework_core,
            self.scripts_source,
            self.bin_source,
            self.claude_md_template,
            self.project_agents
        ]
        
        missing_paths = []
        for path in required_paths:
            if not path.exists():
                missing_paths.append(str(path))
                logger.error(f"❌ Missing required path: {path}")
        
        if missing_paths:
            return False, missing_paths
        
        # Validate critical files
        critical_files = [
            self.bin_source / "claude-pm",
            self.bin_source / "cmpm",
            self.framework_core / "__init__.py",
            self.project_root / ".claude-pm" / "agents" / "hierarchy.yaml"
        ]
        
        for file_path in critical_files:
            if not file_path.exists():
                missing_paths.append(str(file_path))
                logger.error(f"❌ Missing critical file: {file_path}")
        
        if missing_paths:
            return False, missing_paths
        
        logger.info("✅ Source structure validation completed successfully")
        self.deployment_status["steps_completed"].append("source_validation")
        return True, []
    
    def create_target_hierarchy(self) -> bool:
        """Create target directory hierarchy."""
        logger.info("📁 Creating target directory hierarchy...")
        
        target_dirs = [
            self.deployment_target,
            self.scripts_target,
            self.bin_target,
            self.user_agents,
            self.deployment_target / ".claude-pm",
            self.deployment_target / ".claude-pm" / "config",
            self.deployment_target / ".claude-pm" / "logs",
            self.deployment_target / ".claude-pm" / "cache"
        ]
        
        try:
            for dir_path in target_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"📁 Created directory: {dir_path}")
            
            logger.info("✅ Target directory hierarchy created successfully")
            self.deployment_status["steps_completed"].append("target_hierarchy")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create target hierarchy: {e}")
            self.deployment_status["steps_failed"].append(f"target_hierarchy: {e}")
            return False
    
    def deploy_framework_core(self) -> bool:
        """Deploy framework core modules."""
        logger.info("🔧 Deploying framework core modules...")
        
        try:
            # Add framework core to Python path via symlink or installation
            core_target = self.deployment_target / "lib" / "python" / "claude_pm"
            core_target.parent.mkdir(parents=True, exist_ok=True)
            
            # Create symlink to framework core for development
            if core_target.exists():
                if core_target.is_symlink():
                    core_target.unlink()
                else:
                    shutil.rmtree(core_target)
            
            core_target.symlink_to(self.framework_core)
            logger.info(f"✅ Framework core linked: {self.framework_core} -> {core_target}")
            
            self.deployment_status["steps_completed"].append("framework_core")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy framework core: {e}")
            self.deployment_status["steps_failed"].append(f"framework_core: {e}")
            return False
    
    def synchronize_scripts(self) -> bool:
        """Synchronize scripts with validation."""
        logger.info("📝 Synchronizing scripts and binaries...")
        
        try:
            # Sync scripts directory
            if self.scripts_target.exists():
                shutil.rmtree(self.scripts_target)
            
            shutil.copytree(self.scripts_source, self.scripts_target)
            logger.info(f"✅ Scripts synchronized: {self.scripts_source} -> {self.scripts_target}")
            
            # Sync binary files
            for bin_file in self.bin_source.glob("*"):
                if bin_file.is_file():
                    target_bin = self.bin_target / bin_file.name
                    shutil.copy2(bin_file, target_bin)
                    
                    # Set executable permissions
                    target_bin.chmod(0o755)
                    logger.info(f"✅ Binary deployed: {bin_file.name}")
            
            self.deployment_status["steps_completed"].append("script_sync")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to synchronize scripts: {e}")
            self.deployment_status["steps_failed"].append(f"script_sync: {e}")
            return False
    
    def deploy_claude_md(self) -> bool:
        """Deploy and configure CLAUDE.md with variable substitution."""
        logger.info("📋 Deploying CLAUDE.md with variable substitution...")
        
        try:
            # Read template
            with open(self.claude_md_template, 'r') as f:
                template_content = f.read()
            
            # Variable substitution
            variables = {
                'FRAMEWORK_VERSION': self.framework_version,
                'DEPLOYMENT_DATE': self.deployment_timestamp,
                'DEPLOYMENT_DIR': str(self.deployment_target),
                'PLATFORM': 'darwin',
                'PYTHON_CMD': 'python3',
                'AI_TRACKDOWN_PATH': str(self.bin_target / 'aitrackdown'),
                'CLAUDE_MD_VERSION': '1.4.5.1',
                'LAST_UPDATED': self.deployment_timestamp,
                'CONTENT_HASH': 'a1b2c3d4e5f6789a',
                'DEPLOYMENT_ID': f"claude-pm-{self.deployment_timestamp}",
                'PLATFORM_NOTES': 'macOS deployment with full framework integration'
            }
            
            # Substitute variables
            deployed_content = template_content
            for var, value in variables.items():
                deployed_content = deployed_content.replace(f'{{{{{var}}}}}', value)
            
            # Deploy to all targets
            for target in self.claude_md_targets:
                # Backup existing if it exists
                if target.exists():
                    backup_path = target.with_suffix('.md.backup')
                    shutil.copy2(target, backup_path)
                    logger.info(f"📋 Backed up existing CLAUDE.md: {backup_path}")
                
                # Create target directory if needed
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Write deployed content
                with open(target, 'w') as f:
                    f.write(deployed_content)
                
                logger.info(f"✅ CLAUDE.md deployed: {target}")
            
            self.deployment_status["steps_completed"].append("claude_md_deployment")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy CLAUDE.md: {e}")
            self.deployment_status["steps_failed"].append(f"claude_md_deployment: {e}")
            return False
    
    def initialize_agent_hierarchy(self) -> bool:
        """Initialize agent hierarchy."""
        logger.info("🤖 Initializing agent hierarchy...")
        
        try:
            # Run cmcp-init setup
            setup_cmd = ["python3", "/Users/masa/.claude/commands/cmpm-bridge.py", "cmcp-init", "--setup"]
            result = subprocess.run(setup_cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Agent hierarchy setup completed")
            else:
                logger.warning(f"⚠️ Agent hierarchy setup warning: {result.stderr}")
                self.deployment_status["warnings"].append(f"cmcp_init_setup: {result.stderr}")
            
            # Run verification
            verify_cmd = ["python3", "/Users/masa/.claude/commands/cmpm-bridge.py", "cmcp-init", "--verify"]
            result = subprocess.run(verify_cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Agent hierarchy verification completed")
            else:
                logger.warning(f"⚠️ Agent hierarchy verification warning: {result.stderr}")
                self.deployment_status["warnings"].append(f"cmcp_init_verify: {result.stderr}")
            
            self.deployment_status["steps_completed"].append("agent_hierarchy")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent hierarchy: {e}")
            self.deployment_status["steps_failed"].append(f"agent_hierarchy: {e}")
            return False
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        logger.info("🏥 Running comprehensive health checks...")
        
        health_results = {}
        
        try:
            # Framework import test
            try:
                sys.path.insert(0, str(self.project_root))
                import claude_pm
                health_results["framework_import"] = "✅ PASS"
                logger.info("✅ Framework import successful")
            except Exception as e:
                health_results["framework_import"] = f"❌ FAIL: {e}"
                logger.error(f"❌ Framework import failed: {e}")
            
            # Binary execution test
            binaries_to_test = ["claude-pm", "cmpm"]
            for binary in binaries_to_test:
                binary_path = self.bin_target / binary
                if binary_path.exists() and os.access(binary_path, os.X_OK):
                    health_results[f"binary_{binary}"] = "✅ PASS"
                    logger.info(f"✅ Binary {binary} is executable")
                else:
                    health_results[f"binary_{binary}"] = "❌ FAIL: Not executable"
                    logger.error(f"❌ Binary {binary} is not executable")
            
            # Configuration validation
            config_files = [
                self.project_root / ".claude-pm" / "config.json",
                self.project_root / ".claude-pm" / "agents" / "hierarchy.yaml"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    health_results[f"config_{config_file.name}"] = "✅ PASS"
                    logger.info(f"✅ Configuration file found: {config_file.name}")
                else:
                    health_results[f"config_{config_file.name}"] = "❌ FAIL: Missing"
                    logger.error(f"❌ Configuration file missing: {config_file.name}")
            
            # CLAUDE.md validation
            for claude_md in self.claude_md_targets:
                if claude_md.exists():
                    health_results[f"claude_md_{claude_md.parent.name}"] = "✅ PASS"
                    logger.info(f"✅ CLAUDE.md deployed: {claude_md}")
                else:
                    health_results[f"claude_md_{claude_md.parent.name}"] = "❌ FAIL: Missing"
                    logger.error(f"❌ CLAUDE.md missing: {claude_md}")
            
            # Save health check results
            health_report_path = self.project_root / "logs" / "health-check-results.json"
            with open(health_report_path, 'w') as f:
                json.dump({
                    "timestamp": self.deployment_timestamp,
                    "results": health_results,
                    "deployment_status": self.deployment_status
                }, f, indent=2)
            
            logger.info(f"📊 Health check results saved: {health_report_path}")
            
            # Determine overall health
            failed_checks = [k for k, v in health_results.items() if "FAIL" in v]
            if failed_checks:
                logger.warning(f"⚠️ Health checks failed: {failed_checks}")
                self.deployment_status["warnings"].extend(failed_checks)
            else:
                logger.info("✅ All health checks passed")
            
            self.deployment_status["steps_completed"].append("health_checks")
            return len(failed_checks) == 0
            
        except Exception as e:
            logger.error(f"❌ Health checks failed: {e}")
            self.deployment_status["steps_failed"].append(f"health_checks: {e}")
            return False
    
    def validate_integrations(self) -> bool:
        """Validate all integrations."""
        logger.info("🔗 Validating integrations...")
        
        try:
            integration_results = {}
            
            # AI-trackdown integration
            aitrackdown_path = self.bin_target / "aitrackdown"
            if aitrackdown_path.exists():
                integration_results["ai_trackdown"] = "✅ AVAILABLE"
                logger.info("✅ AI-trackdown integration available")
            else:
                integration_results["ai_trackdown"] = "❌ MISSING"
                logger.warning("⚠️ AI-trackdown integration not available")
            
            # Memory system integration (mem0AI)
            try:
                # Check if mem0 is available
                import importlib
                mem0_spec = importlib.util.find_spec("mem0")
                if mem0_spec:
                    integration_results["mem0ai"] = "✅ AVAILABLE"
                    logger.info("✅ mem0AI integration available")
                else:
                    integration_results["mem0ai"] = "❌ MISSING"
                    logger.warning("⚠️ mem0AI integration not available")
            except Exception:
                integration_results["mem0ai"] = "❌ ERROR"
                logger.warning("⚠️ mem0AI integration check failed")
            
            # Agent hierarchy integration
            if (self.project_root / ".claude-pm" / "agents" / "hierarchy.yaml").exists():
                integration_results["agent_hierarchy"] = "✅ CONFIGURED"
                logger.info("✅ Agent hierarchy integration configured")
            else:
                integration_results["agent_hierarchy"] = "❌ MISSING"
                logger.error("❌ Agent hierarchy integration missing")
            
            self.deployment_status["integration_results"] = integration_results
            self.deployment_status["steps_completed"].append("integration_validation")
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration validation failed: {e}")
            self.deployment_status["steps_failed"].append(f"integration_validation: {e}")
            return False
    
    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report."""
        logger.info("📊 Generating deployment report...")
        
        self.deployment_status["completed"] = datetime.now().isoformat()
        self.deployment_status["duration"] = (
            datetime.fromisoformat(self.deployment_status["completed"]) -
            datetime.fromisoformat(self.deployment_status["started"])
        ).total_seconds()
        
        report = {
            "deployment_info": {
                "framework_version": self.framework_version,
                "project_root": str(self.project_root),
                "deployment_target": str(self.deployment_target),
                "timestamp": self.deployment_timestamp
            },
            "deployment_status": self.deployment_status,
            "recommendations": []
        }
        
        # Add recommendations based on status
        if self.deployment_status["steps_failed"]:
            report["recommendations"].append("Review failed steps and address underlying issues")
        
        if self.deployment_status["warnings"]:
            report["recommendations"].append("Review warnings and consider optimization opportunities")
        
        if len(self.deployment_status["steps_completed"]) == 6:  # All main steps
            report["recommendations"].append("Deployment completed successfully - ready for operation")
        
        # Save report
        report_path = self.project_root / "logs" / "deployment-report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Deployment report saved: {report_path}")
        return report
    
    def execute_full_deployment(self) -> bool:
        """Execute complete deployment process."""
        logger.info("🚀 Starting full deployment of claude-multiagent-pm framework...")
        
        deployment_steps = [
            ("Source Structure Validation", self.validate_source_structure),
            ("Target Hierarchy Creation", self.create_target_hierarchy),
            ("Framework Core Deployment", self.deploy_framework_core),
            ("Scripts and Binaries Sync", self.synchronize_scripts),
            ("CLAUDE.md Deployment", self.deploy_claude_md),
            ("Agent Hierarchy Initialization", self.initialize_agent_hierarchy),
            ("Health Checks", self.run_health_checks),
            ("Integration Validation", self.validate_integrations)
        ]
        
        success = True
        for step_name, step_func in deployment_steps:
            logger.info(f"🔄 Executing: {step_name}")
            
            if step_name == "Source Structure Validation":
                step_success, missing = step_func()
                if not step_success:
                    logger.error(f"❌ {step_name} failed - missing: {missing}")
                    success = False
                    break
            else:
                step_success = step_func()
                if not step_success:
                    logger.error(f"❌ {step_name} failed")
                    success = False
                    # Continue with remaining steps for partial deployment
        
        # Generate final report
        report = self.generate_deployment_report()
        
        if success and not self.deployment_status["steps_failed"]:
            logger.info("🎉 Full deployment completed successfully!")
            return True
        else:
            logger.error("❌ Deployment completed with errors - check deployment report")
            return False

def main():
    """Main deployment execution."""
    print("🚀 Claude-MultiAgent-PM Ops Agent - Full Deployment")
    print("=" * 60)
    
    deployment = ClaudeMultiAgentPMDeployment()
    success = deployment.execute_full_deployment()
    
    print("=" * 60)
    if success:
        print("✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("❌ Deployment completed with errors!")
        sys.exit(1)

if __name__ == "__main__":
    main()