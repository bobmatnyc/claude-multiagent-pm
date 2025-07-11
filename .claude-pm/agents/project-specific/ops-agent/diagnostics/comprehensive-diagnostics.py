#!/usr/bin/env python3
"""
Claude-MultiAgent-PM Ops Agent - Comprehensive Diagnostics
Advanced diagnostic procedures for troubleshooting and system health analysis.

Author: Claude-MultiAgent-PM Ops Agent
Version: 1.0.0
Date: 2025-07-11
"""

import os
import sys
import json
import subprocess
import logging
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/masa/Projects/claude-multiagent-pm/logs/ops-agent-diagnostics.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('claude-multiagent-pm-ops-diagnostics')

class ComprehensiveDiagnostics:
    """Advanced diagnostic system for claude-multiagent-pm framework."""
    
    def __init__(self):
        self.project_root = Path("/Users/masa/Projects/claude-multiagent-pm")
        self.deployment_target = Path("/Users/masa/.local")
        self.diagnosis_timestamp = datetime.now().isoformat()
        
        # Diagnostic results
        self.diagnostic_results = {
            "timestamp": self.diagnosis_timestamp,
            "framework_info": {
                "version": "4.5.1",
                "project_root": str(self.project_root),
                "deployment_target": str(self.deployment_target)
            },
            "health_checks": {},
            "performance_metrics": {},
            "integration_status": {},
            "configuration_validation": {},
            "troubleshooting_analysis": {},
            "recommendations": [],
            "critical_issues": [],
            "warnings": []
        }
    
    def check_framework_modules(self) -> Dict[str, Any]:
        """Check framework module availability and health."""
        logger.info("🔍 Checking framework modules...")
        
        module_results = {}
        
        # Core framework modules to check
        core_modules = [
            "claude_pm",
            "claude_pm.core.config",
            "claude_pm.core.enforcement",
            "claude_pm.core.service_manager",
            "claude_pm.services.multi_agent_orchestrator",
            "claude_pm.services.intelligent_task_planner",
            "claude_pm.services.health_dashboard",
            "claude_pm.services.parent_directory_manager"
        ]
        
        # Add project root to Python path
        sys.path.insert(0, str(self.project_root))
        
        for module_name in core_modules:
            try:
                module = importlib.import_module(module_name)
                module_results[module_name] = {
                    "status": "✅ AVAILABLE",
                    "path": getattr(module, "__file__", "built-in"),
                    "version": getattr(module, "__version__", "unknown")
                }
                logger.info(f"✅ Module {module_name} available")
            except ImportError as e:
                module_results[module_name] = {
                    "status": f"❌ IMPORT_ERROR: {e}",
                    "path": None,
                    "version": None
                }
                logger.error(f"❌ Module {module_name} import failed: {e}")
                self.diagnostic_results["critical_issues"].append(f"Module import failure: {module_name}")
            except Exception as e:
                module_results[module_name] = {
                    "status": f"❌ ERROR: {e}",
                    "path": None,
                    "version": None
                }
                logger.error(f"❌ Module {module_name} error: {e}")
        
        return module_results
    
    def check_agent_hierarchy(self) -> Dict[str, Any]:
        """Check agent hierarchy configuration and health."""
        logger.info("🤖 Checking agent hierarchy...")
        
        hierarchy_results = {}
        
        # Check hierarchy configuration file
        hierarchy_config = self.project_root / ".claude-pm" / "agents" / "hierarchy.yaml"
        if hierarchy_config.exists():
            hierarchy_results["config_file"] = "✅ EXISTS"
            try:
                import yaml
                with open(hierarchy_config, 'r') as f:
                    config_data = yaml.safe_load(f)
                hierarchy_results["config_data"] = config_data
                hierarchy_results["config_validation"] = "✅ VALID"
                logger.info("✅ Agent hierarchy configuration valid")
            except Exception as e:
                hierarchy_results["config_validation"] = f"❌ INVALID: {e}"
                logger.error(f"❌ Agent hierarchy config invalid: {e}")
                self.diagnostic_results["critical_issues"].append(f"Agent hierarchy config invalid: {e}")
        else:
            hierarchy_results["config_file"] = "❌ MISSING"
            logger.error("❌ Agent hierarchy configuration missing")
            self.diagnostic_results["critical_issues"].append("Agent hierarchy configuration missing")
        
        # Check agent registry
        registry_file = self.project_root / ".claude-pm" / "agents" / "registry.json"
        if registry_file.exists():
            hierarchy_results["registry_file"] = "✅ EXISTS"
            try:
                with open(registry_file, 'r') as f:
                    registry_data = json.load(f)
                hierarchy_results["registry_data"] = registry_data
                hierarchy_results["registry_validation"] = "✅ VALID"
                logger.info("✅ Agent registry valid")
            except Exception as e:
                hierarchy_results["registry_validation"] = f"❌ INVALID: {e}"
                logger.error(f"❌ Agent registry invalid: {e}")
                self.diagnostic_results["warnings"].append(f"Agent registry invalid: {e}")
        else:
            hierarchy_results["registry_file"] = "❌ MISSING"
            logger.error("❌ Agent registry missing")
            self.diagnostic_results["warnings"].append("Agent registry missing")
        
        # Check agent directories
        agent_dirs = {
            "project_specific": self.project_root / ".claude-pm" / "agents" / "project-specific",
            "user_defined": self.deployment_target / ".claude-pm" / "agents" / "user-defined",
            "system_agents": self.project_root / "claude_pm" / "agents"
        }
        
        for dir_name, dir_path in agent_dirs.items():
            if dir_path.exists():
                agent_count = len(list(dir_path.rglob("*.py")))
                hierarchy_results[f"{dir_name}_directory"] = f"✅ EXISTS ({agent_count} agents)"
                logger.info(f"✅ {dir_name} directory exists with {agent_count} agents")
            else:
                hierarchy_results[f"{dir_name}_directory"] = "❌ MISSING"
                logger.warning(f"⚠️ {dir_name} directory missing")
                self.diagnostic_results["warnings"].append(f"{dir_name} agent directory missing")
        
        return hierarchy_results
    
    def check_script_synchronization(self) -> Dict[str, Any]:
        """Check script synchronization status."""
        logger.info("📝 Checking script synchronization...")
        
        sync_results = {}
        
        # Check source and target script directories
        scripts_source = self.project_root / "scripts"
        scripts_target = self.deployment_target / "scripts"
        
        if scripts_source.exists():
            source_scripts = list(scripts_source.rglob("*.py")) + list(scripts_source.rglob("*.sh"))
            sync_results["source_scripts"] = f"✅ {len(source_scripts)} scripts"
            logger.info(f"✅ Source scripts: {len(source_scripts)} files")
        else:
            sync_results["source_scripts"] = "❌ SOURCE_MISSING"
            logger.error("❌ Source scripts directory missing")
            self.diagnostic_results["critical_issues"].append("Source scripts directory missing")
        
        if scripts_target.exists():
            target_scripts = list(scripts_target.rglob("*.py")) + list(scripts_target.rglob("*.sh"))
            sync_results["target_scripts"] = f"✅ {len(target_scripts)} scripts"
            logger.info(f"✅ Target scripts: {len(target_scripts)} files")
            
            # Check if target scripts are executable
            executable_count = 0
            for script in target_scripts:
                if os.access(script, os.X_OK):
                    executable_count += 1
            
            sync_results["executable_scripts"] = f"✅ {executable_count}/{len(target_scripts)} executable"
            
            if executable_count < len(target_scripts):
                self.diagnostic_results["warnings"].append(
                    f"{len(target_scripts) - executable_count} scripts are not executable"
                )
        else:
            sync_results["target_scripts"] = "❌ TARGET_MISSING"
            logger.error("❌ Target scripts directory missing")
            self.diagnostic_results["critical_issues"].append("Target scripts directory missing")
        
        # Check sync state
        sync_state_file = self.project_root / ".claude-pm" / "cache" / "sync-state.json"
        if sync_state_file.exists():
            try:
                with open(sync_state_file, 'r') as f:
                    sync_state = json.load(f)
                sync_results["sync_state"] = "✅ AVAILABLE"
                sync_results["last_sync"] = sync_state.get("last_sync", "unknown")
                logger.info(f"✅ Sync state available, last sync: {sync_results['last_sync']}")
            except Exception as e:
                sync_results["sync_state"] = f"❌ INVALID: {e}"
                logger.error(f"❌ Sync state invalid: {e}")
        else:
            sync_results["sync_state"] = "⚠️ NO_HISTORY"
            logger.warning("⚠️ No sync state history found")
        
        return sync_results
    
    def check_claude_md_deployment(self) -> Dict[str, Any]:
        """Check CLAUDE.md deployment status."""
        logger.info("📋 Checking CLAUDE.md deployment...")
        
        claude_md_results = {}
        
        # Check template source
        template_source = self.project_root / "framework" / "CLAUDE.md"
        if template_source.exists():
            claude_md_results["template_source"] = "✅ EXISTS"
            logger.info("✅ CLAUDE.md template source exists")
        else:
            claude_md_results["template_source"] = "❌ MISSING"
            logger.error("❌ CLAUDE.md template source missing")
            self.diagnostic_results["critical_issues"].append("CLAUDE.md template source missing")
        
        # Check deployment targets
        deployment_targets = [
            self.deployment_target / "CLAUDE.md",
            Path("/Users/masa/Projects/CLAUDE.md")
        ]
        
        for i, target in enumerate(deployment_targets):
            target_key = f"deployment_target_{i+1}"
            if target.exists():
                # Validate content
                try:
                    with open(target, 'r') as f:
                        content = f.read()
                    
                    # Check for framework indicators
                    if "4.5.1" in content and "claude-multiagent-pm" in content.lower():
                        claude_md_results[target_key] = f"✅ VALID ({target})"
                        logger.info(f"✅ CLAUDE.md deployment valid: {target}")
                    else:
                        claude_md_results[target_key] = f"⚠️ OUTDATED ({target})"
                        logger.warning(f"⚠️ CLAUDE.md may be outdated: {target}")
                        self.diagnostic_results["warnings"].append(f"CLAUDE.md may be outdated: {target}")
                except Exception as e:
                    claude_md_results[target_key] = f"❌ READ_ERROR ({target}): {e}"
                    logger.error(f"❌ Cannot read CLAUDE.md: {target}: {e}")
            else:
                claude_md_results[target_key] = f"❌ MISSING ({target})"
                logger.error(f"❌ CLAUDE.md deployment missing: {target}")
                self.diagnostic_results["warnings"].append(f"CLAUDE.md deployment missing: {target}")
        
        return claude_md_results
    
    def check_binary_deployment(self) -> Dict[str, Any]:
        """Check binary deployment status."""
        logger.info("⚙️ Checking binary deployment...")
        
        binary_results = {}
        
        # Expected binaries
        expected_binaries = ["claude-pm", "cmpm", "aitrackdown", "atd"]
        
        # Check source binaries
        bin_source = self.project_root / "bin"
        if bin_source.exists():
            source_binaries = [f.name for f in bin_source.glob("*") if f.is_file()]
            binary_results["source_binaries"] = f"✅ {source_binaries}"
            logger.info(f"✅ Source binaries: {source_binaries}")
        else:
            binary_results["source_binaries"] = "❌ SOURCE_MISSING"
            logger.error("❌ Source binaries directory missing")
            self.diagnostic_results["critical_issues"].append("Source binaries directory missing")
        
        # Check target binaries
        bin_target = self.deployment_target / "bin"
        if bin_target.exists():
            target_binaries = [f.name for f in bin_target.glob("*") if f.is_file()]
            binary_results["target_binaries"] = f"✅ {target_binaries}"
            logger.info(f"✅ Target binaries: {target_binaries}")
            
            # Check executable permissions
            executable_binaries = []
            for binary in expected_binaries:
                binary_path = bin_target / binary
                if binary_path.exists() and os.access(binary_path, os.X_OK):
                    executable_binaries.append(binary)
            
            binary_results["executable_binaries"] = f"✅ {executable_binaries}"
            
            missing_binaries = set(expected_binaries) - set(executable_binaries)
            if missing_binaries:
                self.diagnostic_results["warnings"].append(
                    f"Missing or non-executable binaries: {missing_binaries}"
                )
        else:
            binary_results["target_binaries"] = "❌ TARGET_MISSING"
            logger.error("❌ Target binaries directory missing")
            self.diagnostic_results["critical_issues"].append("Target binaries directory missing")
        
        return binary_results
    
    def check_integration_status(self) -> Dict[str, Any]:
        """Check external integration status."""
        logger.info("🔗 Checking integration status...")
        
        integration_results = {}
        
        # mem0AI integration
        try:
            import mem0
            integration_results["mem0ai"] = f"✅ AVAILABLE (version: {getattr(mem0, '__version__', 'unknown')})"
            logger.info("✅ mem0AI integration available")
        except ImportError:
            integration_results["mem0ai"] = "❌ NOT_INSTALLED"
            logger.warning("⚠️ mem0AI not installed")
            self.diagnostic_results["warnings"].append("mem0AI integration not available")
        except Exception as e:
            integration_results["mem0ai"] = f"❌ ERROR: {e}"
            logger.error(f"❌ mem0AI integration error: {e}")
        
        # AI-trackdown tools integration
        aitrackdown_path = self.deployment_target / "bin" / "aitrackdown"
        if aitrackdown_path.exists() and os.access(aitrackdown_path, os.X_OK):
            try:
                result = subprocess.run([str(aitrackdown_path), "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    integration_results["ai_trackdown"] = f"✅ FUNCTIONAL ({result.stdout.strip()})"
                    logger.info("✅ AI-trackdown integration functional")
                else:
                    integration_results["ai_trackdown"] = f"⚠️ ISSUES: {result.stderr}"
                    logger.warning(f"⚠️ AI-trackdown issues: {result.stderr}")
            except subprocess.TimeoutExpired:
                integration_results["ai_trackdown"] = "⚠️ TIMEOUT"
                logger.warning("⚠️ AI-trackdown command timeout")
            except Exception as e:
                integration_results["ai_trackdown"] = f"❌ ERROR: {e}"
                logger.error(f"❌ AI-trackdown error: {e}")
        else:
            integration_results["ai_trackdown"] = "❌ NOT_AVAILABLE"
            logger.error("❌ AI-trackdown not available")
            self.diagnostic_results["warnings"].append("AI-trackdown integration not available")
        
        # Node.js availability (for AI-trackdown)
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                integration_results["nodejs"] = f"✅ AVAILABLE ({result.stdout.strip()})"
                logger.info(f"✅ Node.js available: {result.stdout.strip()}")
            else:
                integration_results["nodejs"] = "❌ NOT_FUNCTIONAL"
                logger.error("❌ Node.js not functional")
        except Exception as e:
            integration_results["nodejs"] = f"❌ NOT_AVAILABLE: {e}"
            logger.error(f"❌ Node.js not available: {e}")
            self.diagnostic_results["warnings"].append("Node.js not available for AI-trackdown")
        
        return integration_results
    
    def analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze system performance metrics."""
        logger.info("📊 Analyzing performance metrics...")
        
        performance_results = {}
        
        # Framework startup time simulation
        try:
            start_time = datetime.now()
            sys.path.insert(0, str(self.project_root))
            import claude_pm
            end_time = datetime.now()
            startup_time = (end_time - start_time).total_seconds()
            
            performance_results["framework_startup"] = f"✅ {startup_time:.3f}s"
            if startup_time > 2.0:
                self.diagnostic_results["warnings"].append(f"Slow framework startup: {startup_time:.3f}s")
            logger.info(f"✅ Framework startup time: {startup_time:.3f}s")
        except Exception as e:
            performance_results["framework_startup"] = f"❌ ERROR: {e}"
            logger.error(f"❌ Framework startup test failed: {e}")
        
        # Disk space analysis
        try:
            import shutil
            
            # Check project root disk usage
            project_usage = shutil.disk_usage(self.project_root)
            performance_results["project_disk_free"] = f"✅ {project_usage.free / (1024**3):.1f}GB free"
            
            # Check deployment target disk usage
            deployment_usage = shutil.disk_usage(self.deployment_target)
            performance_results["deployment_disk_free"] = f"✅ {deployment_usage.free / (1024**3):.1f}GB free"
            
            if project_usage.free < 1024**3:  # Less than 1GB free
                self.diagnostic_results["warnings"].append("Low disk space on project volume")
            
            logger.info(f"✅ Disk space analysis completed")
        except Exception as e:
            performance_results["disk_analysis"] = f"❌ ERROR: {e}"
            logger.error(f"❌ Disk space analysis failed: {e}")
        
        # Memory usage estimation
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            performance_results["system_memory"] = {
                "total": f"{memory_info.total / (1024**3):.1f}GB",
                "available": f"{memory_info.available / (1024**3):.1f}GB",
                "percent_used": f"{memory_info.percent}%"
            }
            
            if memory_info.percent > 90:
                self.diagnostic_results["warnings"].append(f"High memory usage: {memory_info.percent}%")
            
            logger.info(f"✅ Memory analysis: {memory_info.percent}% used")
        except ImportError:
            performance_results["system_memory"] = "⚠️ psutil not available"
            logger.warning("⚠️ psutil not available for memory analysis")
        except Exception as e:
            performance_results["system_memory"] = f"❌ ERROR: {e}"
            logger.error(f"❌ Memory analysis failed: {e}")
        
        return performance_results
    
    def generate_troubleshooting_recommendations(self) -> List[str]:
        """Generate troubleshooting recommendations based on findings."""
        logger.info("🔧 Generating troubleshooting recommendations...")
        
        recommendations = []
        
        # Critical issues recommendations
        if self.diagnostic_results["critical_issues"]:
            recommendations.append("🚨 CRITICAL: Address critical issues immediately:")
            for issue in self.diagnostic_results["critical_issues"]:
                recommendations.append(f"   - {issue}")
            recommendations.append("")
        
        # Module import issues
        if any("IMPORT_ERROR" in str(result) for result in self.diagnostic_results["health_checks"].get("framework_modules", {}).values()):
            recommendations.extend([
                "🔧 Framework Module Issues:",
                "   - Verify Python path includes project root",
                "   - Check for missing dependencies in requirements.txt",
                "   - Run: python -c 'import claude_pm' to test core import",
                "   - Consider running full deployment to fix module paths",
                ""
            ])
        
        # Agent hierarchy issues
        hierarchy_results = self.diagnostic_results["health_checks"].get("agent_hierarchy", {})
        if "❌" in str(hierarchy_results):
            recommendations.extend([
                "🤖 Agent Hierarchy Issues:",
                "   - Run: python ~/.claude/commands/cmpm-bridge.py cmcp-init --setup",
                "   - Verify .claude-pm directory structure exists",
                "   - Check agent hierarchy YAML configuration",
                "   - Ensure proper file permissions on agent directories",
                ""
            ])
        
        # Script sync issues
        script_results = self.diagnostic_results["health_checks"].get("script_sync", {})
        if "❌" in str(script_results) or "TARGET_MISSING" in str(script_results):
            recommendations.extend([
                "📝 Script Synchronization Issues:",
                "   - Run incremental sync: python automation/incremental-sync.py",
                "   - Check source scripts directory permissions",
                "   - Verify rsync is available and functional",
                "   - Consider full deployment if sync continues to fail",
                ""
            ])
        
        # Binary deployment issues
        binary_results = self.diagnostic_results["health_checks"].get("binary_deployment", {})
        if "❌" in str(binary_results):
            recommendations.extend([
                "⚙️ Binary Deployment Issues:",
                "   - Sync binaries: rsync -av bin/ ~/.local/bin/",
                "   - Set executable permissions: chmod +x ~/.local/bin/*",
                "   - Verify PATH includes ~/.local/bin",
                "   - Test binary execution: ~/.local/bin/claude-pm --version",
                ""
            ])
        
        # Integration issues
        integration_results = self.diagnostic_results.get("integration_status", {})
        if "❌" in str(integration_results) or "NOT_AVAILABLE" in str(integration_results):
            recommendations.extend([
                "🔗 Integration Issues:",
                "   - Install mem0: pip install mem0ai==0.1.113",
                "   - Install Node.js for AI-trackdown tools",
                "   - Verify external service connectivity",
                "   - Check integration configuration files",
                ""
            ])
        
        # Performance optimization
        performance_results = self.diagnostic_results.get("performance_metrics", {})
        if any("⚠️" in str(result) for result in performance_results.values()):
            recommendations.extend([
                "📊 Performance Optimization:",
                "   - Clear unnecessary log files and caches",
                "   - Optimize Python imports and module loading",
                "   - Consider increasing system resources if needed",
                "   - Review and cleanup old backup files",
                ""
            ])
        
        # General maintenance
        if self.diagnostic_results["warnings"]:
            recommendations.extend([
                "🧹 General Maintenance:",
                "   - Review and address all warnings",
                "   - Update framework to latest version if available",
                "   - Run health checks regularly",
                "   - Maintain regular backup schedule",
                ""
            ])
        
        if not recommendations:
            recommendations.append("✅ System appears healthy - no specific recommendations")
        
        return recommendations
    
    def save_diagnostic_report(self) -> Path:
        """Save comprehensive diagnostic report."""
        logger.info("💾 Saving diagnostic report...")
        
        # Add recommendations to results
        self.diagnostic_results["recommendations"] = self.generate_troubleshooting_recommendations()
        
        # Add summary
        critical_count = len(self.diagnostic_results["critical_issues"])
        warning_count = len(self.diagnostic_results["warnings"])
        
        self.diagnostic_results["summary"] = {
            "overall_health": "🚨 CRITICAL" if critical_count > 0 else ("⚠️ WARNINGS" if warning_count > 0 else "✅ HEALTHY"),
            "critical_issues": critical_count,
            "warnings": warning_count,
            "diagnostic_completion": datetime.now().isoformat()
        }
        
        # Save to file
        report_path = self.project_root / "logs" / "comprehensive-diagnostics-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(self.diagnostic_results, f, indent=2)
        
        logger.info(f"💾 Diagnostic report saved: {report_path}")
        return report_path
    
    def run_comprehensive_diagnostics(self) -> bool:
        """Run complete diagnostic suite."""
        logger.info("🔍 Starting comprehensive diagnostics...")
        
        # Execute all diagnostic checks
        diagnostic_checks = [
            ("Framework Modules", self.check_framework_modules),
            ("Agent Hierarchy", self.check_agent_hierarchy),
            ("Script Synchronization", self.check_script_synchronization),
            ("CLAUDE.md Deployment", self.check_claude_md_deployment),
            ("Binary Deployment", self.check_binary_deployment)
        ]
        
        for check_name, check_func in diagnostic_checks:
            logger.info(f"🔄 Running: {check_name}")
            try:
                result = check_func()
                self.diagnostic_results["health_checks"][check_name.lower().replace(" ", "_")] = result
            except Exception as e:
                logger.error(f"❌ {check_name} diagnostic failed: {e}")
                self.diagnostic_results["health_checks"][check_name.lower().replace(" ", "_")] = f"❌ ERROR: {e}"
                self.diagnostic_results["critical_issues"].append(f"{check_name} diagnostic failed: {e}")
        
        # Run additional analyses
        self.diagnostic_results["integration_status"] = self.check_integration_status()
        self.diagnostic_results["performance_metrics"] = self.analyze_performance_metrics()
        
        # Save report
        report_path = self.save_diagnostic_report()
        
        # Determine overall success
        critical_issues = len(self.diagnostic_results["critical_issues"])
        
        if critical_issues == 0:
            logger.info("🎉 Comprehensive diagnostics completed - system healthy!")
            return True
        else:
            logger.error(f"❌ Comprehensive diagnostics found {critical_issues} critical issues")
            return False

def main():
    """Main diagnostic execution."""
    print("🔍 Claude-MultiAgent-PM Ops Agent - Comprehensive Diagnostics")
    print("=" * 70)
    
    diagnostics = ComprehensiveDiagnostics()
    success = diagnostics.run_comprehensive_diagnostics()
    
    print("=" * 70)
    print("📊 Diagnostic Summary:")
    summary = diagnostics.diagnostic_results["summary"]
    print(f"   Overall Health: {summary['overall_health']}")
    print(f"   Critical Issues: {summary['critical_issues']}")
    print(f"   Warnings: {summary['warnings']}")
    
    if summary['critical_issues'] > 0:
        print("\n🚨 Critical Issues Found:")
        for issue in diagnostics.diagnostic_results["critical_issues"]:
            print(f"   - {issue}")
    
    if diagnostics.diagnostic_results["recommendations"]:
        print("\n🔧 Recommendations:")
        for rec in diagnostics.diagnostic_results["recommendations"][:5]:  # Show first 5
            print(f"   {rec}")
    
    print("=" * 70)
    if success:
        print("✅ Diagnostics completed successfully!")
        sys.exit(0)
    else:
        print("❌ Diagnostics found critical issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()