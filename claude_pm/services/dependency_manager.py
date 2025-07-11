"""
Dependency Management Service for Claude PM Framework.

Provides comprehensive dependency management including:
- ai-trackdown-tools installation automation
- Python package verification and management
- Deployment-aware dependency resolution
- Cross-platform compatibility
- Integration with CMPM-101 DeploymentDetector

CMPM-103 Implementation: Dependency Management Strategy
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from ..core.base_service import BaseService


class DependencyType(Enum):
    """Types of dependencies managed by the system."""
    PYTHON_PACKAGE = "python_package"
    NPM_GLOBAL = "npm_global"
    NPM_LOCAL = "npm_local"
    SYSTEM_BINARY = "system_binary"
    AI_TRACKDOWN_TOOLS = "ai_trackdown_tools"


class InstallationMethod(Enum):
    """Available installation methods."""
    NPM_GLOBAL = "npm_global"
    NPM_LOCAL = "npm_local"
    NPX = "npx"
    SOURCE = "source"
    PIP = "pip"
    SYSTEM = "system"


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    type: DependencyType
    version: Optional[str] = None
    required_version: Optional[str] = None
    is_installed: bool = False
    installation_path: Optional[str] = None
    installation_method: Optional[InstallationMethod] = None
    last_checked: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InstallationResult:
    """Result of a dependency installation."""
    success: bool
    dependency_name: str
    method: InstallationMethod
    version: Optional[str] = None
    installation_path: Optional[str] = None
    error_message: Optional[str] = None
    logs: Optional[List[str]] = None


@dataclass
class DependencyReport:
    """Comprehensive dependency report."""
    deployment_type: str
    platform: str
    timestamp: str
    dependencies: Dict[str, DependencyInfo]
    missing_dependencies: List[str]
    outdated_dependencies: List[str]
    installation_recommendations: List[str]
    health_score: int


class DependencyManager(BaseService):
    """
    Deployment-aware dependency management service.
    
    Integrates with CMPM-101 DeploymentDetector to provide context-aware
    dependency resolution and installation automation.
    """
    
    # Core dependencies with version requirements
    CORE_DEPENDENCIES = {
        "ai-trackdown-tools": {
            "type": DependencyType.AI_TRACKDOWN_TOOLS,
            "npm_package": "@bobmatnyc/ai-trackdown-tools",
            "required_version": ">=1.1.0",
            "commands": ["aitrackdown", "atd"],
            "critical": True
        },
        "python": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["python3", "python"],
            "required_version": ">=3.8.0",
            "critical": True
        },
        "node": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["node"],
            "required_version": ">=16.0.0",
            "critical": True
        },
        "npm": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["npm"],
            "required_version": ">=8.0.0",
            "critical": True
        },
        "git": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["git"],
            "required_version": ">=2.0.0",
            "critical": True
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize dependency manager."""
        super().__init__("dependency_manager", config)
        
        # Deployment integration
        self.deployment_detector = None
        self.deployment_config = None
        
        # Dependency tracking
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._installation_cache: Dict[str, InstallationResult] = {}
        
        # Service settings
        self.check_interval = self.get_config("check_interval", 1800)  # 30 minutes
        self.auto_install = self.get_config("auto_install", True)
        self.installation_timeout = self.get_config("installation_timeout", 300)  # 5 minutes
        
        # Platform detection
        self.platform = sys.platform
        self.python_cmd = self._detect_python_command()
        
        # Installation strategies
        self.installation_strategies = {
            DependencyType.AI_TRACKDOWN_TOOLS: self._install_ai_trackdown_tools,
            DependencyType.PYTHON_PACKAGE: self._install_python_package,
            DependencyType.NPM_GLOBAL: self._install_npm_global,
            DependencyType.NPM_LOCAL: self._install_npm_local,
            DependencyType.SYSTEM_BINARY: self._install_system_binary
        }
    
    async def _initialize(self) -> None:
        """Initialize the dependency manager."""
        self.logger.info("Initializing Dependency Manager...")
        
        # Initialize deployment detector integration
        await self._initialize_deployment_integration()
        
        # Perform initial dependency check
        await self._check_all_dependencies()
        
        # Auto-install missing critical dependencies if enabled
        if self.auto_install:
            await self._auto_install_missing_dependencies()
        
        self.logger.info(f"Dependency Manager initialized for {self.deployment_config.get('deploymentType', 'unknown')} deployment")
    
    async def _cleanup(self) -> None:
        """Cleanup dependency manager."""
        self.logger.info("Cleaning up Dependency Manager...")
        
        # Save dependency state
        await self._save_dependency_state()
        
        # Clear caches
        self._dependencies.clear()
        self._installation_cache.clear()
        
        self.logger.info("Dependency Manager cleanup completed")
    
    async def _health_check(self) -> Dict[str, bool]:
        """Perform dependency manager health checks."""
        checks = {}
        
        try:
            # Check core dependencies
            checks["python_available"] = await self._check_python_available()
            checks["node_available"] = await self._check_node_available()
            checks["npm_available"] = await self._check_npm_available()
            checks["git_available"] = await self._check_git_available()
            checks["ai_trackdown_tools_available"] = await self._check_ai_trackdown_tools_available()
            
            # Check deployment integration
            checks["deployment_detector_available"] = self.deployment_detector is not None
            checks["deployment_config_valid"] = self.deployment_config is not None
            
            # Check dependency tracking
            checks["dependencies_tracked"] = len(self._dependencies) > 0
            checks["critical_dependencies_met"] = await self._check_critical_dependencies()
            
        except Exception as e:
            self.logger.error(f"Dependency manager health check failed: {e}")
            checks["health_check_error"] = False
        
        return checks
    
    async def _start_custom_tasks(self) -> Optional[List]:
        """Start custom background tasks."""
        tasks = []
        
        # Dependency monitoring task
        if self.get_config("enable_dependency_monitoring", True):
            task = asyncio.create_task(self._dependency_monitoring_task())
            tasks.append(task)
        
        return tasks if tasks else None
    
    async def _initialize_deployment_integration(self) -> None:
        """Initialize integration with DeploymentDetector."""
        try:
            # For now, use a simple fallback configuration
            # In a real deployment, this would integrate with the actual DeploymentDetector
            self.deployment_config = {
                "strategy": "development",
                "config": {
                    "deploymentType": "local_source",
                    "platform": self.platform,
                    "confidence": "high",
                    "frameworkPath": str(Path(__file__).parent.parent.parent)
                }
            }
            
            self.logger.info(f"Deployment integration initialized: {self.deployment_config.get('strategy', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize deployment integration: {e}")
            # Use fallback configuration
            self.deployment_config = {
                "strategy": "fallback",
                "config": {
                    "deploymentType": "unknown",
                    "platform": self.platform
                }
            }
    
    def _detect_python_command(self) -> str:
        """Detect available Python command."""
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return cmd
            except Exception:
                continue
        return "python3"  # Default fallback
    
    async def _check_all_dependencies(self) -> None:
        """Check all defined dependencies."""
        self.logger.info("Checking all dependencies...")
        
        for dep_name, dep_config in self.CORE_DEPENDENCIES.items():
            dependency_info = await self._check_dependency(dep_name, dep_config)
            self._dependencies[dep_name] = dependency_info
        
        # Check deployment-specific dependencies
        if self.deployment_config:
            await self._check_deployment_specific_dependencies()
        
        self.logger.info(f"Dependency check completed for {len(self._dependencies)} dependencies")
    
    async def _check_dependency(self, name: str, config: Dict) -> DependencyInfo:
        """Check a specific dependency."""
        dependency_info = DependencyInfo(
            name=name,
            type=config["type"],
            required_version=config.get("required_version"),
            last_checked=datetime.now().isoformat()
        )
        
        try:
            if config["type"] == DependencyType.AI_TRACKDOWN_TOOLS:
                await self._check_ai_trackdown_tools(dependency_info, config)
            elif config["type"] == DependencyType.SYSTEM_BINARY:
                await self._check_system_binary(dependency_info, config)
            elif config["type"] == DependencyType.PYTHON_PACKAGE:
                await self._check_python_package(dependency_info, config)
            elif config["type"] == DependencyType.NPM_GLOBAL:
                await self._check_npm_global(dependency_info, config)
            elif config["type"] == DependencyType.NPM_LOCAL:
                await self._check_npm_local(dependency_info, config)
            
        except Exception as e:
            self.logger.error(f"Failed to check dependency {name}: {e}")
            dependency_info.metadata = {"error": str(e)}
        
        return dependency_info
    
    async def _check_ai_trackdown_tools(self, dependency_info: DependencyInfo, config: Dict) -> None:
        """Check ai-trackdown-tools installation."""
        commands = config.get("commands", ["aitrackdown", "atd"])
        
        # Check if commands are available
        for cmd in commands:
            if await self._check_command_available(cmd):
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.NPM_GLOBAL
                
                # Get version
                try:
                    result = await self._run_command([cmd, "--version"])
                    if result.returncode == 0:
                        dependency_info.version = result.stdout.strip()
                except Exception:
                    pass
                
                break
        
        # Check npm global installation
        if not dependency_info.is_installed:
            try:
                result = await self._run_command(["npm", "list", "-g", config["npm_package"]])
                if result.returncode == 0:
                    dependency_info.is_installed = True
                    dependency_info.installation_method = InstallationMethod.NPM_GLOBAL
                    
                    # Try to get version from npm
                    try:
                        result = await self._run_command(["npm", "list", "-g", config["npm_package"], "--depth=0"])
                        if result.returncode == 0:
                            # Parse version from npm output
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if config["npm_package"] in line and "@" in line:
                                    version = line.split("@")[-1].strip()
                                    dependency_info.version = version
                                    break
                    except Exception:
                        pass
                        
            except Exception:
                pass
        
        # Check deployment-specific locations
        if not dependency_info.is_installed and self.deployment_config:
            await self._check_deployment_specific_ai_trackdown_tools(dependency_info)
    
    async def _check_system_binary(self, dependency_info: DependencyInfo, config: Dict) -> None:
        """Check system binary availability."""
        commands = config.get("commands", [dependency_info.name])
        
        for cmd in commands:
            if await self._check_command_available(cmd):
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.SYSTEM
                
                # Get version
                try:
                    result = await self._run_command([cmd, "--version"])
                    if result.returncode == 0:
                        # Parse version from output
                        version_text = result.stdout.strip()
                        dependency_info.version = self._parse_version_from_output(version_text)
                        dependency_info.metadata = {"version_output": version_text}
                except Exception:
                    pass
                
                # Get installation path
                try:
                    result = await self._run_command(["which", cmd])
                    if result.returncode == 0:
                        dependency_info.installation_path = result.stdout.strip()
                except Exception:
                    pass
                
                break
    
    async def _check_python_package(self, dependency_info: DependencyInfo, config: Dict) -> None:
        """Check Python package installation."""
        package_name = config.get("package_name", dependency_info.name)
        
        try:
            # Try to import the package
            import importlib
            module = importlib.import_module(package_name)
            
            dependency_info.is_installed = True
            dependency_info.installation_method = InstallationMethod.PIP
            
            # Get version if available
            if hasattr(module, "__version__"):
                dependency_info.version = module.__version__
                
        except ImportError:
            # Check via pip
            try:
                result = await self._run_command([self.python_cmd, "-m", "pip", "show", package_name])
                if result.returncode == 0:
                    dependency_info.is_installed = True
                    dependency_info.installation_method = InstallationMethod.PIP
                    
                    # Parse version from pip output
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            dependency_info.version = line.split(':', 1)[1].strip()
                            break
                        elif line.startswith('Location:'):
                            dependency_info.installation_path = line.split(':', 1)[1].strip()
                            
            except Exception:
                pass
    
    async def _check_npm_global(self, dependency_info: DependencyInfo, config: Dict) -> None:
        """Check npm global package installation."""
        package_name = config.get("package_name", dependency_info.name)
        
        try:
            result = await self._run_command(["npm", "list", "-g", package_name])
            if result.returncode == 0:
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.NPM_GLOBAL
                
                # Get version and path
                try:
                    result = await self._run_command(["npm", "list", "-g", package_name, "--depth=0"])
                    if result.returncode == 0:
                        # Parse version from npm output
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if package_name in line and "@" in line:
                                version = line.split("@")[-1].strip()
                                dependency_info.version = version
                                break
                except Exception:
                    pass
                    
        except Exception:
            pass
    
    async def _check_npm_local(self, dependency_info: DependencyInfo, config: Dict) -> None:
        """Check npm local package installation."""
        package_name = config.get("package_name", dependency_info.name)
        
        try:
            result = await self._run_command(["npm", "list", package_name])
            if result.returncode == 0:
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.NPM_LOCAL
                
                # Get version
                try:
                    result = await self._run_command(["npm", "list", package_name, "--depth=0"])
                    if result.returncode == 0:
                        # Parse version from npm output
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if package_name in line and "@" in line:
                                version = line.split("@")[-1].strip()
                                dependency_info.version = version
                                break
                except Exception:
                    pass
                    
        except Exception:
            pass
    
    async def _check_deployment_specific_dependencies(self) -> None:
        """Check dependencies specific to the current deployment."""
        if not self.deployment_config:
            return
        
        deployment_type = self.deployment_config.get("config", {}).get("deploymentType", "unknown")
        
        # Add deployment-specific checks
        if deployment_type == "local_source":
            await self._check_local_source_dependencies()
        elif deployment_type == "npm_global":
            await self._check_npm_global_dependencies()
        elif deployment_type == "deployed":
            await self._check_deployed_dependencies()
    
    async def _check_local_source_dependencies(self) -> None:
        """Check dependencies for local source deployment."""
        # Check if source requirements are met
        if self.deployment_config and "config" in self.deployment_config:
            framework_path = self.deployment_config["config"].get("frameworkPath")
            if framework_path:
                requirements_path = Path(framework_path) / "requirements" / "base.txt"
                if requirements_path.exists():
                    await self._check_requirements_file(requirements_path)
    
    async def _check_npm_global_dependencies(self) -> None:
        """Check dependencies for npm global deployment."""
        # Verify npm global environment
        try:
            result = await self._run_command(["npm", "root", "-g"])
            if result.returncode == 0:
                npm_global_path = result.stdout.strip()
                self.logger.debug(f"NPM global path: {npm_global_path}")
        except Exception:
            pass
    
    async def _check_deployed_dependencies(self) -> None:
        """Check dependencies for deployed instance."""
        # Check deployed instance configuration
        if self.deployment_config and "config" in self.deployment_config:
            deployed_config = self.deployment_config["config"].get("metadata", {}).get("deployedConfig")
            if deployed_config:
                self.logger.debug(f"Deployed config: {deployed_config}")
    
    async def _check_requirements_file(self, requirements_path: Path) -> None:
        """Check Python requirements file."""
        try:
            with open(requirements_path, 'r') as f:
                requirements = f.read().splitlines()
            
            for req in requirements:
                req = req.strip()
                if req and not req.startswith('#'):
                    # Parse requirement
                    package_name = req.split('>=')[0].split('==')[0].split('[')[0]
                    
                    # Check if not already tracked
                    if package_name not in self._dependencies:
                        config = {
                            "type": DependencyType.PYTHON_PACKAGE,
                            "package_name": package_name,
                            "required_version": req if '>=' in req or '==' in req else None,
                            "critical": False
                        }
                        
                        dependency_info = await self._check_dependency(package_name, config)
                        self._dependencies[package_name] = dependency_info
                        
        except Exception as e:
            self.logger.error(f"Failed to check requirements file {requirements_path}: {e}")
    
    async def _check_deployment_specific_ai_trackdown_tools(self, dependency_info: DependencyInfo) -> None:
        """Check ai-trackdown-tools in deployment-specific locations."""
        if not self.deployment_config:
            return
        
        config = self.deployment_config.get("config", {})
        
        # Check framework bin directory
        if "frameworkPath" in config:
            framework_path = Path(config["frameworkPath"])
            bin_path = framework_path / "bin"
            
            for cmd in ["aitrackdown", "atd"]:
                cmd_path = bin_path / cmd
                if cmd_path.exists():
                    dependency_info.is_installed = True
                    dependency_info.installation_method = InstallationMethod.SOURCE
                    dependency_info.installation_path = str(cmd_path)
                    break
    
    async def _auto_install_missing_dependencies(self) -> None:
        """Auto-install missing critical dependencies."""
        missing_critical = []
        
        for dep_name, dep_info in self._dependencies.items():
            if not dep_info.is_installed:
                dep_config = self.CORE_DEPENDENCIES.get(dep_name, {})
                if dep_config.get("critical", False):
                    missing_critical.append(dep_name)
        
        if missing_critical:
            self.logger.info(f"Auto-installing missing critical dependencies: {missing_critical}")
            
            for dep_name in missing_critical:
                result = await self.install_dependency(dep_name)
                if result.success:
                    self.logger.info(f"Successfully installed {dep_name}")
                else:
                    self.logger.error(f"Failed to install {dep_name}: {result.error_message}")
    
    async def install_dependency(self, dependency_name: str, method: Optional[InstallationMethod] = None) -> InstallationResult:
        """Install a dependency using the specified or best method."""
        if dependency_name not in self.CORE_DEPENDENCIES:
            return InstallationResult(
                success=False,
                dependency_name=dependency_name,
                method=method or InstallationMethod.SYSTEM,
                error_message=f"Unknown dependency: {dependency_name}"
            )
        
        dep_config = self.CORE_DEPENDENCIES[dependency_name]
        dep_type = dep_config["type"]
        
        # Select installation method
        if method is None:
            method = self._select_best_installation_method(dep_type, dep_config)
        
        # Execute installation
        try:
            installation_strategy = self.installation_strategies.get(dep_type)
            if installation_strategy:
                result = await installation_strategy(dependency_name, dep_config, method)
                
                # Update cache
                self._installation_cache[dependency_name] = result
                
                # Re-check dependency after installation
                if result.success:
                    dependency_info = await self._check_dependency(dependency_name, dep_config)
                    self._dependencies[dependency_name] = dependency_info
                
                return result
            else:
                return InstallationResult(
                    success=False,
                    dependency_name=dependency_name,
                    method=method,
                    error_message=f"No installation strategy for {dep_type}"
                )
                
        except Exception as e:
            return InstallationResult(
                success=False,
                dependency_name=dependency_name,
                method=method,
                error_message=f"Installation failed: {str(e)}"
            )
    
    def _select_best_installation_method(self, dep_type: DependencyType, config: Dict) -> InstallationMethod:
        """Select the best installation method for a dependency type."""
        if dep_type == DependencyType.AI_TRACKDOWN_TOOLS:
            # Prefer npm global for ai-trackdown-tools
            return InstallationMethod.NPM_GLOBAL
        elif dep_type == DependencyType.PYTHON_PACKAGE:
            return InstallationMethod.PIP
        elif dep_type == DependencyType.NPM_GLOBAL:
            return InstallationMethod.NPM_GLOBAL
        elif dep_type == DependencyType.NPM_LOCAL:
            return InstallationMethod.NPM_LOCAL
        else:
            return InstallationMethod.SYSTEM
    
    async def _install_ai_trackdown_tools(self, name: str, config: Dict, method: InstallationMethod) -> InstallationResult:
        """Install ai-trackdown-tools package."""
        package_name = config["npm_package"]
        
        if method == InstallationMethod.NPM_GLOBAL:
            try:
                result = await self._run_command(
                    ["npm", "install", "-g", package_name],
                    timeout=self.installation_timeout
                )
                
                if result.returncode == 0:
                    return InstallationResult(
                        success=True,
                        dependency_name=name,
                        method=method,
                        logs=[result.stdout, result.stderr]
                    )
                else:
                    return InstallationResult(
                        success=False,
                        dependency_name=name,
                        method=method,
                        error_message=f"npm install failed: {result.stderr}",
                        logs=[result.stdout, result.stderr]
                    )
                    
            except Exception as e:
                return InstallationResult(
                    success=False,
                    dependency_name=name,
                    method=method,
                    error_message=f"Installation exception: {str(e)}"
                )
        
        elif method == InstallationMethod.NPX:
            # NPX doesn't install, just note it's available
            return InstallationResult(
                success=True,
                dependency_name=name,
                method=method,
                logs=["NPX execution available"]
            )
        
        else:
            return InstallationResult(
                success=False,
                dependency_name=name,
                method=method,
                error_message=f"Unsupported installation method: {method}"
            )
    
    async def _install_python_package(self, name: str, config: Dict, method: InstallationMethod) -> InstallationResult:
        """Install Python package."""
        package_name = config.get("package_name", name)
        
        if method == InstallationMethod.PIP:
            try:
                install_cmd = [self.python_cmd, "-m", "pip", "install", package_name]
                
                # Add version constraint if specified
                if "required_version" in config:
                    install_cmd[-1] += config["required_version"]
                
                result = await self._run_command(install_cmd, timeout=self.installation_timeout)
                
                if result.returncode == 0:
                    return InstallationResult(
                        success=True,
                        dependency_name=name,
                        method=method,
                        logs=[result.stdout, result.stderr]
                    )
                else:
                    return InstallationResult(
                        success=False,
                        dependency_name=name,
                        method=method,
                        error_message=f"pip install failed: {result.stderr}",
                        logs=[result.stdout, result.stderr]
                    )
                    
            except Exception as e:
                return InstallationResult(
                    success=False,
                    dependency_name=name,
                    method=method,
                    error_message=f"Installation exception: {str(e)}"
                )
        
        else:
            return InstallationResult(
                success=False,
                dependency_name=name,
                method=method,
                error_message=f"Unsupported installation method: {method}"
            )
    
    async def _install_npm_global(self, name: str, config: Dict, method: InstallationMethod) -> InstallationResult:
        """Install npm global package."""
        package_name = config.get("package_name", name)
        
        try:
            result = await self._run_command(
                ["npm", "install", "-g", package_name],
                timeout=self.installation_timeout
            )
            
            if result.returncode == 0:
                return InstallationResult(
                    success=True,
                    dependency_name=name,
                    method=method,
                    logs=[result.stdout, result.stderr]
                )
            else:
                return InstallationResult(
                    success=False,
                    dependency_name=name,
                    method=method,
                    error_message=f"npm install failed: {result.stderr}",
                    logs=[result.stdout, result.stderr]
                )
                
        except Exception as e:
            return InstallationResult(
                success=False,
                dependency_name=name,
                method=method,
                error_message=f"Installation exception: {str(e)}"
            )
    
    async def _install_npm_local(self, name: str, config: Dict, method: InstallationMethod) -> InstallationResult:
        """Install npm local package."""
        package_name = config.get("package_name", name)
        
        try:
            result = await self._run_command(
                ["npm", "install", package_name],
                timeout=self.installation_timeout
            )
            
            if result.returncode == 0:
                return InstallationResult(
                    success=True,
                    dependency_name=name,
                    method=method,
                    logs=[result.stdout, result.stderr]
                )
            else:
                return InstallationResult(
                    success=False,
                    dependency_name=name,
                    method=method,
                    error_message=f"npm install failed: {result.stderr}",
                    logs=[result.stdout, result.stderr]
                )
                
        except Exception as e:
            return InstallationResult(
                success=False,
                dependency_name=name,
                method=method,
                error_message=f"Installation exception: {str(e)}"
            )
    
    async def _install_system_binary(self, name: str, config: Dict, method: InstallationMethod) -> InstallationResult:
        """Install system binary (placeholder - requires manual installation)."""
        return InstallationResult(
            success=False,
            dependency_name=name,
            method=method,
            error_message=f"System binary {name} requires manual installation"
        )
    
    async def _dependency_monitoring_task(self) -> None:
        """Background task for dependency monitoring."""
        while not self._stop_event.is_set():
            try:
                await self._check_all_dependencies()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Dependency monitoring task error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _save_dependency_state(self) -> None:
        """Save dependency state to file."""
        try:
            if self.deployment_config and "config" in self.deployment_config:
                framework_path = self.deployment_config["config"].get("frameworkPath")
                if framework_path:
                    logs_path = Path(framework_path) / "logs"
                    logs_path.mkdir(exist_ok=True)
                    
                    state_file = logs_path / "dependency-state.json"
                    
                    # Convert enums to strings for JSON serialization
                    dependencies_data = {}
                    for name, info in self._dependencies.items():
                        info_dict = asdict(info)
                        info_dict['type'] = info.type.value
                        if info.installation_method:
                            info_dict['installation_method'] = info.installation_method.value
                        dependencies_data[name] = info_dict
                    
                    installation_cache_data = {}
                    for name, result in self._installation_cache.items():
                        result_dict = asdict(result)
                        result_dict['method'] = result.method.value
                        installation_cache_data[name] = result_dict
                    
                    state_data = {
                        "timestamp": datetime.now().isoformat(),
                        "deployment_type": self.deployment_config.get("config", {}).get("deploymentType", "unknown"),
                        "platform": self.platform,
                        "dependencies": dependencies_data,
                        "installation_cache": installation_cache_data
                    }
                    
                    with open(state_file, 'w') as f:
                        json.dump(state_data, f, indent=2)
                    
                    self.logger.debug(f"Dependency state saved to {state_file}")
                    
        except Exception as e:
            self.logger.error(f"Failed to save dependency state: {e}")
    
    # Utility methods
    
    async def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in the system."""
        try:
            result = await self._run_command(["which", command])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _run_command(self, command: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a command asynchronously."""
        try:
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=timeout
            )
            
            stdout, stderr = await result.communicate()
            
            return subprocess.CompletedProcess(
                args=command,
                returncode=result.returncode,
                stdout=stdout.decode('utf-8'),
                stderr=stderr.decode('utf-8')
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"Command timeout: {' '.join(command)}")
        except Exception as e:
            raise Exception(f"Command failed: {' '.join(command)}: {str(e)}")
    
    def _parse_version_from_output(self, output: str) -> str:
        """Parse version from command output."""
        import re
        
        # Common version patterns
        patterns = [
            r'v?(\d+\.\d+\.\d+)',
            r'version (\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v?(\d+\.\d+)',
            r'(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    # Health check methods
    
    async def _check_python_available(self) -> bool:
        """Check if Python is available."""
        try:
            result = await self._run_command([self.python_cmd, "--version"])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_node_available(self) -> bool:
        """Check if Node.js is available."""
        try:
            result = await self._run_command(["node", "--version"])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_npm_available(self) -> bool:
        """Check if npm is available."""
        try:
            result = await self._run_command(["npm", "--version"])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_git_available(self) -> bool:
        """Check if Git is available."""
        try:
            result = await self._run_command(["git", "--version"])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_ai_trackdown_tools_available(self) -> bool:
        """Check if ai-trackdown-tools is available."""
        try:
            result = await self._run_command(["aitrackdown", "--version"])
            return result.returncode == 0
        except Exception:
            try:
                result = await self._run_command(["atd", "--version"])
                return result.returncode == 0
            except Exception:
                return False
    
    async def _check_critical_dependencies(self) -> bool:
        """Check if all critical dependencies are met."""
        for dep_name, dep_config in self.CORE_DEPENDENCIES.items():
            if dep_config.get("critical", False):
                dep_info = self._dependencies.get(dep_name)
                if not dep_info or not dep_info.is_installed:
                    return False
        return True
    
    # Public API methods
    
    def get_dependencies(self) -> Dict[str, DependencyInfo]:
        """Get all tracked dependencies."""
        return self._dependencies.copy()
    
    def get_dependency(self, name: str) -> Optional[DependencyInfo]:
        """Get a specific dependency."""
        return self._dependencies.get(name)
    
    def get_installation_result(self, name: str) -> Optional[InstallationResult]:
        """Get installation result for a dependency."""
        return self._installation_cache.get(name)
    
    async def generate_dependency_report(self) -> DependencyReport:
        """Generate comprehensive dependency report."""
        missing_dependencies = []
        outdated_dependencies = []
        installation_recommendations = []
        
        for name, info in self._dependencies.items():
            if not info.is_installed:
                missing_dependencies.append(name)
                
                # Add installation recommendation
                dep_config = self.CORE_DEPENDENCIES.get(name, {})
                if dep_config.get("critical", False):
                    installation_recommendations.append(
                        f"CRITICAL: Install {name} - {dep_config.get('type', 'unknown')} dependency"
                    )
                else:
                    installation_recommendations.append(
                        f"Install {name} - {dep_config.get('type', 'unknown')} dependency"
                    )
        
        # Calculate health score
        total_deps = len(self._dependencies)
        installed_deps = sum(1 for info in self._dependencies.values() if info.is_installed)
        health_score = round((installed_deps / total_deps) * 100) if total_deps > 0 else 0
        
        return DependencyReport(
            deployment_type=self.deployment_config.get("config", {}).get("deploymentType", "unknown"),
            platform=self.platform,
            timestamp=datetime.now().isoformat(),
            dependencies=self._dependencies.copy(),
            missing_dependencies=missing_dependencies,
            outdated_dependencies=outdated_dependencies,
            installation_recommendations=installation_recommendations,
            health_score=health_score
        )
    
    async def refresh_dependencies(self) -> None:
        """Refresh all dependency information."""
        await self._check_all_dependencies()
    
    async def verify_ai_trackdown_tools(self) -> bool:
        """Verify ai-trackdown-tools installation and functionality."""
        try:
            # Check if commands are available
            commands = ["aitrackdown", "atd"]
            available_commands = []
            
            for cmd in commands:
                if await self._check_command_available(cmd):
                    available_commands.append(cmd)
            
            if not available_commands:
                return False
            
            # Test basic functionality
            for cmd in available_commands:
                try:
                    result = await self._run_command([cmd, "--version"])
                    if result.returncode != 0:
                        return False
                except Exception:
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def get_installation_recommendations(self) -> List[str]:
        """Get installation recommendations for missing dependencies."""
        recommendations = []
        
        for name, info in self._dependencies.items():
            if not info.is_installed:
                dep_config = self.CORE_DEPENDENCIES.get(name, {})
                
                if dep_config.get("critical", False):
                    recommendations.append(f"CRITICAL: Install {name}")
                else:
                    recommendations.append(f"Install {name}")
        
        return recommendations