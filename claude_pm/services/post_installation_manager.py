#!/usr/bin/env python3
"""
PostInstallationManager Service - Claude PM Framework
=====================================================

This service implements all NPM post-installation functionality in Python,
integrated with claude-pm init command. It handles:

- Directory structure creation and component deployment
- Framework component installation to ~/.claude-pm/
- Cross-platform compatibility with clear error handling
- Installation diagnostics and status reporting
- Comprehensive installation validation with health checking

Replaces install/postinstall.js with Python implementation.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging, setup_streaming_logger, finalize_streaming_logs

console = Console()
logger = setup_logging(__name__)


@dataclass
class InstallationStep:
    """Represents a single installation step."""
    name: str
    description: str
    completed: bool = False
    error: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation check."""
    component: str
    status: str  # "success", "warning", "error"
    details: str
    critical: bool = False


@dataclass
class DeploymentPaths:
    """Standard deployment paths for framework components."""
    scripts: Path
    templates: Path
    agents: Path
    framework: Path
    schemas: Path
    config: Path
    cli: Path
    docs: Path
    bin: Path
    memory: Path
    cache: Path
    logs: Path
    index: Path


class PostInstallationManager(BaseService):
    """
    Post-installation manager for Claude PM Framework.
    
    This service handles all post-installation tasks including:
    - Framework component deployment to ~/.claude-pm/
    - Directory structure creation
    - Component validation and health checking
    - Cross-platform compatibility
    - Installation diagnostics and reporting
    """
    
    def __init__(self, working_dir: Optional[Path] = None):
        super().__init__(name="post_installation_manager")
        self.platform = platform.system().lower()
        self.working_dir = working_dir or Path.cwd()
        self.package_root = self._detect_package_root()
        self.user_home = Path.home()
        self.global_config_dir = self.user_home / ".claude-pm"
        
        # Initialize deployment paths
        self.deployment_paths = DeploymentPaths(
            scripts=self.global_config_dir / "scripts",
            templates=self.global_config_dir / "templates",
            agents=self.global_config_dir / "agents",
            framework=self.global_config_dir / "framework",
            schemas=self.global_config_dir / "schemas",
            config=self.global_config_dir / "config",
            cli=self.global_config_dir / "cli",
            docs=self.global_config_dir / "docs",
            bin=self.global_config_dir / "bin",
            memory=self.global_config_dir / "memory",
            cache=self.global_config_dir / "cache",
            logs=self.global_config_dir / "logs",
            index=self.global_config_dir / "index"
        )
        
        # Track installation steps
        self.installation_steps: List[InstallationStep] = []
        
        # Validation results
        self.validation_results: List[ValidationResult] = []
        
        # Installation state
        self.installation_state = {
            "component_deployment": False,
            "directory_structure": False,
            "memory_system": False,
            "framework_init": False,
            "health_checking": False,
            "cross_platform_compatibility": False,
            "error_handling": False
        }
        
        # Use streaming logger for clean INFO display during initialization
        self.logger = setup_streaming_logger(__name__)
        self.standard_logger = setup_logging(__name__)  # For ERROR/WARNING messages
    
    def _detect_package_root(self) -> Path:
        """Detect the package root directory."""
        # Start from current file location and work up
        current = Path(__file__).parent
        while current != current.parent:
            # Look for package.json or setup.py or pyproject.toml
            if any((current / f).exists() for f in ["package.json", "setup.py", "pyproject.toml", "claude_pm"]):
                return current
            current = current.parent
        
        # Fallback to working directory
        return self.working_dir
    
    async def _initialize(self) -> bool:
        """Initialize the PostInstallationManager service."""
        try:
            self.logger.info("Initializing PostInstallationManager service")
            
            # Create basic directory structure
            self.global_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Log initialization
            self._log_step("service_initialization", "PostInstallationManager initialized")
            
            return True
        except Exception as e:
            self.standard_logger.error(f"Failed to initialize PostInstallationManager: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup the PostInstallationManager service."""
        try:
            self.logger.info("PostInstallationManager cleanup completed")
            # Finalize streaming logs to ensure final message is visible
            finalize_streaming_logs(self.logger)
            return True
        except Exception as e:
            self.standard_logger.error(f"Failed to cleanup PostInstallationManager: {e}")
            finalize_streaming_logs(self.logger)
            return False
    
    def _log_step(self, step_name: str, description: str, completed: bool = True, error: Optional[str] = None):
        """Log an installation step."""
        step = InstallationStep(
            name=step_name,
            description=description,
            completed=completed,
            error=error,
            timestamp=datetime.now().isoformat()
        )
        self.installation_steps.append(step)
        
        if completed and not error:
            self.logger.info(f"✅ {description}")
        elif error:
            # Use standard logger for errors to ensure they appear on new lines
            self.standard_logger.error(f"❌ {description}: {error}")
        else:
            self.logger.info(f"🔄 {description}")
    
    def _add_validation_result(self, component: str, status: str, details: str, critical: bool = False):
        """Add a validation result."""
        result = ValidationResult(
            component=component,
            status=status,
            details=details,
            critical=critical
        )
        self.validation_results.append(result)
        
        if status == "error":
            # Use standard logger for errors to ensure they appear on new lines
            self.standard_logger.error(f"❌ {component}: {details}")
        elif status == "warning":
            # Use standard logger for warnings to ensure they appear on new lines
            self.standard_logger.warning(f"⚠️ {component}: {details}")
        else:
            self.logger.info(f"✅ {component}: {details}")
    
    def is_global_install(self) -> bool:
        """Check if this is a global npm installation."""
        npm_config_prefix = os.environ.get("npm_config_prefix")
        package_path = str(self.package_root)
        npm_root = os.environ.get("npm_config_globaldir") or os.environ.get("npm_root")
        
        # Enhanced debugging for global install detection
        self.logger.debug(f"Global installation detection:")
        self.logger.debug(f"  npm_config_prefix: {npm_config_prefix or 'NOT_SET'}")
        self.logger.debug(f"  npm_config_globaldir: {os.environ.get('npm_config_globaldir') or 'NOT_SET'}")
        self.logger.debug(f"  npm_root: {npm_root or 'NOT_SET'}")
        self.logger.debug(f"  Package path: {package_path}")
        
        # Enhanced global installation indicators
        indicators = {
            # Standard npm prefix detection
            "npm_prefix": npm_config_prefix and npm_config_prefix in package_path,
            
            # Standard npm global directory detection
            "npm_global_dir": npm_root and npm_root in package_path,
            
            # Enhanced global node_modules patterns
            "node_modules_global": "node_modules" in package_path and any([
                "/.npm-global/" in package_path,
                "/lib/node_modules/" in package_path,
                "\\AppData\\Roaming\\npm\\" in package_path,
                "/.npm-packages/" in package_path,
                "/npm-global/" in package_path,
                "/global/lib/node_modules/" in package_path,
                "/usr/local/lib/node_modules/" in package_path,
                "/opt/homebrew/lib/node_modules/" in package_path,
                "/.nvm/versions/node/" in package_path,
                "/nvm/versions/node/" in package_path
            ])
        }
        
        is_global = any(indicators.values())
        
        self.logger.debug(f"Global install indicators: {indicators}")
        self.logger.debug(f"Is global install: {is_global}")
        
        return is_global
    
    async def run_post_installation(self, force: bool = False) -> Dict[str, Any]:
        """
        Run complete post-installation process.
        
        Args:
            force: Force installation even if already completed
            
        Returns:
            Installation results dictionary
        """
        start_time = time.time()
        
        results = {
            "success": False,
            "global_install": self.is_global_install(),
            "platform": self.platform,
            "package_root": str(self.package_root),
            "global_config_dir": str(self.global_config_dir),
            "steps_completed": [],
            "validation_results": [],
            "installation_state": {},
            "errors": [],
            "warnings": [],
            "execution_time": 0
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Step 1: Pre-installation checks
                check_task = progress.add_task("Running pre-installation checks...", total=1)
                if await self._pre_installation_checks():
                    progress.update(check_task, completed=1)
                    results["steps_completed"].append("pre_installation_checks")
                else:
                    results["errors"].append("Pre-installation checks failed")
                    return results
                
                # Step 2: Create directory structure
                structure_task = progress.add_task("Creating directory structure...", total=1)
                if await self._create_directory_structure():
                    progress.update(structure_task, completed=1)
                    results["steps_completed"].append("directory_structure")
                    self.installation_state["directory_structure"] = True
                else:
                    results["errors"].append("Failed to create directory structure")
                    return results
                
                # Step 3: Deploy framework components
                deploy_task = progress.add_task("Deploying framework components...", total=1)
                if await self._deploy_framework_components():
                    progress.update(deploy_task, completed=1)
                    results["steps_completed"].append("component_deployment")
                    self.installation_state["component_deployment"] = True
                else:
                    results["errors"].append("Failed to deploy framework components")
                    return results
                
                # Step 4: Initialize memory system
                memory_task = progress.add_task("Initializing memory system...", total=1)
                if await self._initialize_memory_system():
                    progress.update(memory_task, completed=1)
                    results["steps_completed"].append("memory_system")
                    self.installation_state["memory_system"] = True
                else:
                    results["warnings"].append("Memory system initialization had issues")
                
                # Step 5: Configure framework
                config_task = progress.add_task("Configuring framework...", total=1)
                if await self._configure_framework():
                    progress.update(config_task, completed=1)
                    results["steps_completed"].append("framework_configuration")
                    self.installation_state["framework_init"] = True
                else:
                    results["errors"].append("Failed to configure framework")
                    return results
                
                # Step 6: Run health checks
                health_task = progress.add_task("Running health checks...", total=1)
                if await self._run_health_checks():
                    progress.update(health_task, completed=1)
                    results["steps_completed"].append("health_checks")
                    self.installation_state["health_checking"] = True
                else:
                    results["warnings"].append("Some health checks failed")
                
                # Step 7: Validate installation
                validate_task = progress.add_task("Validating installation...", total=1)
                if await self._validate_installation():
                    progress.update(validate_task, completed=1)
                    results["steps_completed"].append("installation_validation")
                    self.installation_state["cross_platform_compatibility"] = True
                else:
                    results["warnings"].append("Installation validation had issues")
                
                # Step 8: Generate installation report
                report_task = progress.add_task("Generating installation report...", total=1)
                if await self._generate_installation_report():
                    progress.update(report_task, completed=1)
                    results["steps_completed"].append("installation_report")
                else:
                    results["warnings"].append("Could not generate installation report")
                
                results["success"] = True
                results["installation_state"] = self.installation_state
                results["validation_results"] = [asdict(r) for r in self.validation_results]
                
        except Exception as e:
            self.standard_logger.error(f"Post-installation failed: {e}")
            results["errors"].append(f"Post-installation failed: {str(e)}")
            results["success"] = False
        
        finally:
            results["execution_time"] = time.time() - start_time
        
        return results
    
    async def _pre_installation_checks(self) -> bool:
        """Run pre-installation checks."""
        try:
            self._log_step("pre_checks", "Running pre-installation checks")
            
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 9):
                self._add_validation_result(
                    "python_version",
                    "error",
                    f"Python 3.9+ required, found {python_version.major}.{python_version.minor}",
                    critical=True
                )
                return False
            else:
                self._add_validation_result(
                    "python_version",
                    "success",
                    f"Python {python_version.major}.{python_version.minor} detected"
                )
            
            # Check package root
            if not self.package_root.exists():
                self._add_validation_result(
                    "package_root",
                    "error",
                    f"Package root not found: {self.package_root}",
                    critical=True
                )
                return False
            else:
                self._add_validation_result(
                    "package_root",
                    "success",
                    f"Package root found: {self.package_root}"
                )
            
            # Check write permissions
            try:
                test_dir = self.global_config_dir / "test"
                test_dir.mkdir(parents=True, exist_ok=True)
                test_file = test_dir / "test.txt"
                test_file.write_text("test")
                test_file.unlink()
                test_dir.rmdir()
                
                self._add_validation_result(
                    "write_permissions",
                    "success",
                    f"Write permissions verified for {self.global_config_dir}"
                )
            except Exception as e:
                self._add_validation_result(
                    "write_permissions",
                    "error",
                    f"No write permissions for {self.global_config_dir}: {e}",
                    critical=True
                )
                return False
            
            # Check for required dependencies
            required_modules = ["rich", "click", "pathlib"]
            for module in required_modules:
                try:
                    __import__(module)
                    self._add_validation_result(
                        f"dependency_{module}",
                        "success",
                        f"Module {module} available"
                    )
                except ImportError:
                    self._add_validation_result(
                        f"dependency_{module}",
                        "warning",
                        f"Module {module} not available"
                    )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Pre-installation checks failed: {e}")
            return False
    
    async def _create_directory_structure(self) -> bool:
        """Create the complete directory structure."""
        try:
            self._log_step("directory_structure", "Creating directory structure")
            
            # Create all deployment paths
            for path_name, path in asdict(self.deployment_paths).items():
                path = Path(path)
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {path}")
            
            # Create additional subdirectories
            subdirs = [
                self.deployment_paths.agents / "user-defined",
                self.deployment_paths.agents / "system-trained",
                self.deployment_paths.agents / "project-specific",
                self.deployment_paths.templates / "global",
                self.deployment_paths.templates / "project",
                self.deployment_paths.memory / "data",
                self.deployment_paths.memory / "backups",
                self.deployment_paths.cache / "global",
                self.deployment_paths.cache / "project",
                self.deployment_paths.logs / "system",
                self.deployment_paths.logs / "agents",
                self.deployment_paths.index / "cache"
            ]
            
            for subdir in subdirs:
                subdir.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created subdirectory: {subdir}")
            
            self._add_validation_result(
                "directory_structure",
                "success",
                f"Created directory structure in {self.global_config_dir}"
            )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Failed to create directory structure: {e}")
            self._add_validation_result(
                "directory_structure",
                "error",
                f"Failed to create directory structure: {e}",
                critical=True
            )
            return False
    
    async def _deploy_framework_components(self) -> bool:
        """Deploy framework components to global directory."""
        try:
            self._log_step("component_deployment", "Deploying framework components")
            
            # Map of source to destination paths
            component_mappings = {
                "claude_pm": self.deployment_paths.framework / "claude_pm",
                "framework": self.deployment_paths.framework / "framework",
                "scripts": self.deployment_paths.scripts,
                "bin": self.deployment_paths.bin,
                "requirements": self.deployment_paths.framework / "requirements",
                "VERSION": self.deployment_paths.framework / "VERSION",
                "README.md": self.deployment_paths.framework / "README.md"
            }
            
            deployed_count = 0
            
            for source_name, dest_path in component_mappings.items():
                source_path = self.package_root / source_name
                
                if source_path.exists():
                    try:
                        # Create parent directory
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if source_path.is_dir():
                            # Copy directory
                            if dest_path.exists():
                                shutil.rmtree(dest_path)
                            shutil.copytree(source_path, dest_path)
                        else:
                            # Copy file
                            shutil.copy2(source_path, dest_path)
                        
                        deployed_count += 1
                        self.logger.debug(f"Deployed {source_name} to {dest_path}")
                        
                    except Exception as e:
                        self.standard_logger.warning(f"Failed to deploy {source_name}: {e}")
                        self._add_validation_result(
                            f"deploy_{source_name}",
                            "warning",
                            f"Failed to deploy {source_name}: {e}"
                        )
                else:
                    self.logger.debug(f"Source not found: {source_name}")
            
            if deployed_count > 0:
                self._add_validation_result(
                    "component_deployment",
                    "success",
                    f"Deployed {deployed_count} components"
                )
                return True
            else:
                self._add_validation_result(
                    "component_deployment",
                    "warning",
                    "No components were deployed"
                )
                return False
            
        except Exception as e:
            self.standard_logger.error(f"Failed to deploy framework components: {e}")
            self._add_validation_result(
                "component_deployment",
                "error",
                f"Failed to deploy framework components: {e}",
                critical=True
            )
            return False
    
    async def _initialize_memory_system(self) -> bool:
        """Initialize the memory system."""
        try:
            self._log_step("memory_system", "Initializing memory system")
            
            # Create memory configuration
            memory_config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "claude_pm_memory",
                        "path": str(self.deployment_paths.memory / "data")
                    }
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "temperature": 0.1
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small"
                    }
                }
            }
            
            # Save memory configuration
            memory_config_path = self.deployment_paths.config / "memory.json"
            with open(memory_config_path, 'w') as f:
                json.dump(memory_config, f, indent=2)
            
            # Create memory system metadata
            memory_metadata = {
                "version": "1.0.0",
                "initialized_at": datetime.now().isoformat(),
                "system": "claude_pm_framework",
                "data_path": str(self.deployment_paths.memory / "data"),
                "backup_path": str(self.deployment_paths.memory / "backups"),
                "config_path": str(memory_config_path)
            }
            
            metadata_path = self.deployment_paths.memory / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(memory_metadata, f, indent=2)
            
            self._add_validation_result(
                "memory_system",
                "success",
                "Memory system initialized successfully"
            )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Failed to initialize memory system: {e}")
            self._add_validation_result(
                "memory_system",
                "warning",
                f"Memory system initialization failed: {e}"
            )
            return False
    
    async def _configure_framework(self) -> bool:
        """Configure the framework."""
        try:
            self._log_step("framework_configuration", "Configuring framework")
            
            # Create main framework configuration
            framework_config = {
                "claude_pm": {
                    "version": "0.7.5",
                    "mode": "user_installation",
                    "installed_at": datetime.now().isoformat(),
                    "platform": self.platform,
                    "global_install": self.is_global_install(),
                    "package_root": str(self.package_root),
                    "global_config_dir": str(self.global_config_dir)
                },
                "paths": {
                    "scripts": str(self.deployment_paths.scripts),
                    "templates": str(self.deployment_paths.templates),
                    "agents": str(self.deployment_paths.agents),
                    "memory": str(self.deployment_paths.memory),
                    "cache": str(self.deployment_paths.cache),
                    "logs": str(self.deployment_paths.logs),
                    "bin": str(self.deployment_paths.bin)
                },
                "features": {
                    "memory_system": True,
                    "agent_hierarchy": True,
                    "project_indexing": True,
                    "health_monitoring": True,
                    "template_deployment": True
                },
                "dependencies": {
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                    "platform": self.platform
                }
            }
            
            # Save framework configuration
            config_path = self.deployment_paths.config / "framework.json"
            with open(config_path, 'w') as f:
                json.dump(framework_config, f, indent=2)
            
            # Create CLI configuration
            cli_config = {
                "default_commands": {
                    "init": "claude_pm.cli.setup_commands:init",
                    "health": "claude_pm.cli.setup_commands:health",
                    "test": "claude_pm.cli.system_commands:test"
                },
                "shortcuts": {
                    "h": "health",
                    "t": "test",
                    "i": "init"
                }
            }
            
            cli_config_path = self.deployment_paths.config / "cli.json"
            with open(cli_config_path, 'w') as f:
                json.dump(cli_config, f, indent=2)
            
            self._add_validation_result(
                "framework_configuration",
                "success",
                "Framework configuration completed"
            )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Failed to configure framework: {e}")
            self._add_validation_result(
                "framework_configuration",
                "error",
                f"Framework configuration failed: {e}",
                critical=True
            )
            return False
    
    async def _run_health_checks(self) -> bool:
        """Run health checks on the installation."""
        try:
            self._log_step("health_checks", "Running health checks")
            
            health_results = []
            
            # Check directory structure
            for path_name, path in asdict(self.deployment_paths).items():
                path = Path(path)
                if path.exists():
                    health_results.append({
                        "component": f"directory_{path_name}",
                        "status": "healthy",
                        "details": f"Directory exists: {path}"
                    })
                else:
                    health_results.append({
                        "component": f"directory_{path_name}",
                        "status": "error",
                        "details": f"Directory missing: {path}"
                    })
            
            # Check configuration files
            config_files = [
                self.deployment_paths.config / "framework.json",
                self.deployment_paths.config / "cli.json",
                self.deployment_paths.config / "memory.json"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            json.load(f)
                        health_results.append({
                            "component": f"config_{config_file.stem}",
                            "status": "healthy",
                            "details": f"Configuration file valid: {config_file.name}"
                        })
                    except Exception as e:
                        health_results.append({
                            "component": f"config_{config_file.stem}",
                            "status": "error",
                            "details": f"Configuration file invalid: {e}"
                        })
                else:
                    health_results.append({
                        "component": f"config_{config_file.stem}",
                        "status": "warning",
                        "details": f"Configuration file missing: {config_file.name}"
                    })
            
            # Check component deployment
            if (self.deployment_paths.framework / "claude_pm").exists():
                health_results.append({
                    "component": "claude_pm_deployment",
                    "status": "healthy",
                    "details": "Claude PM framework deployed successfully"
                })
            else:
                health_results.append({
                    "component": "claude_pm_deployment",
                    "status": "error",
                    "details": "Claude PM framework not deployed"
                })
            
            # Save health check results
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "installation_health": health_results,
                "overall_status": "healthy" if all(r["status"] == "healthy" for r in health_results) else "issues"
            }
            
            health_report_path = self.deployment_paths.logs / "installation_health.json"
            with open(health_report_path, 'w') as f:
                json.dump(health_report, f, indent=2)
            
            # Add validation results
            for result in health_results:
                self._add_validation_result(
                    result["component"],
                    "success" if result["status"] == "healthy" else result["status"],
                    result["details"]
                )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Health checks failed: {e}")
            self._add_validation_result(
                "health_checks",
                "error",
                f"Health checks failed: {e}"
            )
            return False
    
    async def _validate_installation(self) -> bool:
        """Validate the complete installation."""
        try:
            self._log_step("installation_validation", "Validating installation")
            
            validation_checks = []
            
            # Critical path validation
            critical_paths = [
                self.deployment_paths.framework / "claude_pm",
                self.deployment_paths.config / "framework.json",
                self.deployment_paths.memory,
                self.deployment_paths.agents,
                self.deployment_paths.templates
            ]
            
            for path in critical_paths:
                if path.exists():
                    validation_checks.append({
                        "check": f"critical_path_{path.name}",
                        "status": "pass",
                        "details": f"Critical path exists: {path}"
                    })
                else:
                    validation_checks.append({
                        "check": f"critical_path_{path.name}",
                        "status": "fail",
                        "details": f"Critical path missing: {path}"
                    })
            
            # Functionality validation
            try:
                # Test import capability
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "claude_pm",
                    self.deployment_paths.framework / "claude_pm" / "__init__.py"
                )
                if spec and spec.loader:
                    validation_checks.append({
                        "check": "import_capability",
                        "status": "pass",
                        "details": "Framework import capability verified"
                    })
                else:
                    validation_checks.append({
                        "check": "import_capability",
                        "status": "fail", 
                        "details": "Framework import capability failed"
                    })
            except Exception as e:
                validation_checks.append({
                    "check": "import_capability",
                    "status": "fail",
                    "details": f"Framework import test failed: {e}"
                })
            
            # Platform compatibility
            if self.platform in ["darwin", "linux", "windows"]:
                validation_checks.append({
                    "check": "platform_compatibility",
                    "status": "pass",
                    "details": f"Platform {self.platform} is supported"
                })
            else:
                validation_checks.append({
                    "check": "platform_compatibility",
                    "status": "warning",
                    "details": f"Platform {self.platform} support is experimental"
                })
            
            # Save validation results
            validation_report = {
                "timestamp": datetime.now().isoformat(),
                "validation_checks": validation_checks,
                "overall_status": "valid" if all(c["status"] == "pass" for c in validation_checks) else "issues"
            }
            
            validation_report_path = self.deployment_paths.logs / "installation_validation.json"
            with open(validation_report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            # Add validation results
            for check in validation_checks:
                self._add_validation_result(
                    check["check"],
                    "success" if check["status"] == "pass" else check["status"],
                    check["details"]
                )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Installation validation failed: {e}")
            self._add_validation_result(
                "installation_validation",
                "error",
                f"Installation validation failed: {e}"
            )
            return False
    
    async def _generate_installation_report(self) -> bool:
        """Generate comprehensive installation report."""
        try:
            self._log_step("installation_report", "Generating installation report")
            
            report = {
                "metadata": {
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "platform": self.platform,
                    "global_install": self.is_global_install(),
                    "package_root": str(self.package_root),
                    "global_config_dir": str(self.global_config_dir)
                },
                "installation_steps": [asdict(step) for step in self.installation_steps],
                "validation_results": [asdict(result) for result in self.validation_results],
                "installation_state": self.installation_state,
                "deployment_paths": {k: str(v) for k, v in asdict(self.deployment_paths).items()},
                "summary": {
                    "total_steps": len(self.installation_steps),
                    "completed_steps": len([s for s in self.installation_steps if s.completed]),
                    "failed_steps": len([s for s in self.installation_steps if s.error]),
                    "total_validations": len(self.validation_results),
                    "successful_validations": len([v for v in self.validation_results if v.status == "success"]),
                    "failed_validations": len([v for v in self.validation_results if v.status == "error"]),
                    "warnings": len([v for v in self.validation_results if v.status == "warning"])
                }
            }
            
            # Save detailed report
            report_path = self.deployment_paths.logs / "post_installation_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Create summary report
            summary_path = self.deployment_paths.logs / "installation_summary.txt"
            with open(summary_path, 'w') as f:
                f.write("Claude PM Framework Post-Installation Summary\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Installation Date: {report['metadata']['timestamp']}\n")
                f.write(f"Platform: {report['metadata']['platform']}\n")
                f.write(f"Global Install: {report['metadata']['global_install']}\n")
                f.write(f"Config Directory: {report['metadata']['global_config_dir']}\n\n")
                
                f.write("Installation Summary:\n")
                f.write(f"  Total Steps: {report['summary']['total_steps']}\n")
                f.write(f"  Completed: {report['summary']['completed_steps']}\n")
                f.write(f"  Failed: {report['summary']['failed_steps']}\n")
                f.write(f"  Validations: {report['summary']['successful_validations']}/{report['summary']['total_validations']}\n")
                f.write(f"  Warnings: {report['summary']['warnings']}\n\n")
                
                f.write("Next Steps:\n")
                f.write("  1. Run 'claude-pm init' to complete framework setup\n")
                f.write("  2. Run 'claude-pm health' to verify installation\n")
                f.write("  3. Check documentation for usage examples\n")
            
            self._add_validation_result(
                "installation_report",
                "success",
                f"Installation report generated: {report_path}"
            )
            
            return True
            
        except Exception as e:
            self.standard_logger.error(f"Failed to generate installation report: {e}")
            self._add_validation_result(
                "installation_report",
                "error",
                f"Failed to generate installation report: {e}"
            )
            return False
    
    async def display_installation_results(self, results: Dict[str, Any]) -> None:
        """Display installation results in a formatted manner."""
        try:
            console.print("\n" + "=" * 70)
            console.print("📦 [bold blue]Claude PM Framework Post-Installation Results[/bold blue]")
            console.print("=" * 70)
            
            # Basic info
            console.print(f"📍 Package Root: {results['package_root']}")
            console.print(f"🏠 Global Config: {results['global_config_dir']}")
            console.print(f"🖥️  Platform: {results['platform']}")
            console.print(f"🌐 Global Install: {results['global_install']}")
            
            # Installation state
            console.print(f"\n📋 [bold]Installation State:[/bold]")
            state = results.get('installation_state', {})
            for component, status in state.items():
                icon = "✅" if status else "❌"
                console.print(f"   {icon} {component.replace('_', ' ').title()}: {status}")
            
            # Steps completed
            if results.get('steps_completed'):
                console.print(f"\n✅ [bold green]Completed Steps:[/bold green]")
                for step in results['steps_completed']:
                    console.print(f"   • {step.replace('_', ' ').title()}")
            
            # Validation results summary
            if results.get('validation_results'):
                console.print(f"\n🔍 [bold]Validation Results:[/bold]")
                validation_results = results['validation_results']
                
                success_count = len([v for v in validation_results if v['status'] == 'success'])
                warning_count = len([v for v in validation_results if v['status'] == 'warning'])
                error_count = len([v for v in validation_results if v['status'] == 'error'])
                
                console.print(f"   • Successful: {success_count}")
                console.print(f"   • Warnings: {warning_count}")
                console.print(f"   • Errors: {error_count}")
                
                # Show errors and warnings
                if error_count > 0:
                    console.print(f"\n❌ [bold red]Validation Errors:[/bold red]")
                    for result in validation_results:
                        if result['status'] == 'error':
                            console.print(f"   • {result['component']}: {result['details']}")
                
                if warning_count > 0:
                    console.print(f"\n⚠️  [bold yellow]Validation Warnings:[/bold yellow]")
                    for result in validation_results:
                        if result['status'] == 'warning':
                            console.print(f"   • {result['component']}: {result['details']}")
            
            # Errors and warnings from installation
            if results.get('errors'):
                console.print(f"\n❌ [bold red]Installation Errors:[/bold red]")
                for error in results['errors']:
                    console.print(f"   • {error}")
            
            if results.get('warnings'):
                console.print(f"\n⚠️  [bold yellow]Installation Warnings:[/bold yellow]")
                for warning in results['warnings']:
                    console.print(f"   • {warning}")
            
            # Success/failure summary
            if results['success']:
                console.print(f"\n✅ [bold green]Post-installation completed successfully![/bold green]")
                console.print(f"⏱️  Execution time: {results['execution_time']:.2f} seconds")
                
                console.print(f"\n🚀 [bold]Next Steps:[/bold]")
                console.print(f"   • Run 'claude-pm init' to complete framework setup")
                console.print(f"   • Run 'claude-pm health' to verify installation")
                console.print(f"   • Check ~/.claude-pm/logs/ for detailed reports")
            else:
                console.print(f"\n❌ [bold red]Post-installation failed![/bold red]")
                console.print(f"⏱️  Execution time: {results['execution_time']:.2f} seconds")
                
                console.print(f"\n🔧 [bold]Troubleshooting:[/bold]")
                console.print(f"   • Check error messages above")
                console.print(f"   • Verify write permissions to ~/.claude-pm/")
                console.print(f"   • Run 'claude-pm health' for diagnostics")
                console.print(f"   • Check logs in ~/.claude-pm/logs/")
            
            console.print("=" * 70)
            
        except Exception as e:
            self.standard_logger.error(f"Failed to display installation results: {e}")
            console.print(f"❌ Error displaying results: {e}")
    
    async def get_installation_status(self) -> Dict[str, Any]:
        """Get current installation status."""
        try:
            status = {
                "installed": False,
                "global_config_exists": self.global_config_dir.exists(),
                "components": {},
                "last_installation": None
            }
            
            # Check components
            for component_name, path in asdict(self.deployment_paths).items():
                path = Path(path)
                status["components"][component_name] = {
                    "exists": path.exists(),
                    "path": str(path)
                }
            
            # Check for installation report
            report_path = self.deployment_paths.logs / "post_installation_report.json"
            if report_path.exists():
                try:
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                    status["last_installation"] = report.get("metadata", {}).get("timestamp")
                    status["installed"] = True
                except Exception:
                    pass
            
            return status
            
        except Exception as e:
            self.standard_logger.error(f"Failed to get installation status: {e}")
            return {"installed": False, "error": str(e)}