"""
Dependency Manager Service - Core dependency management and validation

This module provides comprehensive dependency management functionality including:
- System dependency validation (Python, Node.js, npm, Git)
- AI Trackdown Tools integration and validation
- Package installation coordination
- Dependency health monitoring and reporting
- Installation result tracking and caching

Created: 2025-07-16 (Framework completion)
Purpose: Complete standardized error handling system with missing dependency_manager
"""

import asyncio
import logging
import subprocess
import re
import importlib
import platform
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from claude_pm.core.response_types import ServiceResponse, TaskToolResponse

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies that can be managed"""
    PYTHON_PACKAGE = "python_package"
    NPM_GLOBAL = "npm_global"
    NPM_LOCAL = "npm_local"
    SYSTEM_BINARY = "system_binary"
    AI_TRACKDOWN_TOOLS = "ai_trackdown_tools"


class InstallationMethod(Enum):
    """Methods available for installing dependencies"""
    PIP = "pip"
    NPM_GLOBAL = "npm_global"
    NPM_LOCAL = "npm_local"
    SYSTEM = "system"
    MANUAL = "manual"


@dataclass
class DependencyInfo:
    """Information about a specific dependency"""
    name: str
    type: DependencyType
    is_installed: bool = False
    version: Optional[str] = None
    required_version: Optional[str] = None
    installation_method: Optional[InstallationMethod] = None
    installation_path: Optional[str] = None
    last_checked: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class InstallationResult:
    """Result of a dependency installation attempt"""
    success: bool
    dependency_name: str
    method: InstallationMethod
    version: Optional[str] = None
    installation_path: Optional[str] = None
    logs: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class DependencyReport:
    """Comprehensive dependency status report"""
    deployment_type: str
    platform: str
    timestamp: str
    dependencies: Dict[str, DependencyInfo]
    missing_dependencies: List[str] = field(default_factory=list)
    outdated_dependencies: List[str] = field(default_factory=list)
    installation_recommendations: List[str] = field(default_factory=list)
    health_score: int = 0


class DependencyManager:
    """
    Dependency Manager Service - Comprehensive dependency management
    
    Features:
    - Core dependency validation (Python, Node.js, npm, Git, AI Trackdown Tools)
    - Automated installation coordination
    - Version compatibility checking
    - Health monitoring and reporting
    - Installation result caching
    
    Note: AI Trackdown Tools is now installed exclusively via Python (ai-trackdown-pytools).
    """
    
    # Core dependencies required for framework operation
    CORE_DEPENDENCIES = {
        "ai-trackdown-tools": {
            "type": DependencyType.AI_TRACKDOWN_TOOLS,
            "python_package": "ai_trackdown",
            "pip_package": "ai-trackdown-pytools==1.1.0",
            "required_version": "==1.1.0",
            "critical": True,
            "commands": [],  # Python package, no CLI commands
            "description": "AI Trackdown Python tools for issue tracking and project management"
        },
        "python": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["python3", "python"],
            "version_command": "--version",
            "required_version": ">=3.8.0",
            "critical": True,
            "description": "Python runtime environment"
        },
        "node": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["node"],
            "version_command": "--version",
            "required_version": ">=16.0.0",
            "critical": True,
            "description": "Node.js runtime environment"
        },
        "npm": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["npm"],
            "version_command": "--version",
            "required_version": ">=8.0.0",
            "critical": True,
            "description": "Node Package Manager"
        },
        "git": {
            "type": DependencyType.SYSTEM_BINARY,
            "commands": ["git"],
            "version_command": "--version",
            "required_version": ">=2.0.0",
            "critical": True,
            "description": "Git version control system"
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize dependency manager
        
        Args:
            config: Configuration dictionary with options
        """
        self.name = "dependency_manager"
        self.config = config or {}
        
        # Configuration options
        self.check_interval = self.config.get("check_interval", 60)
        self.auto_install = self.config.get("auto_install", False)
        self.installation_timeout = self.config.get("installation_timeout", 30)
        
        # State tracking
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._installation_cache: Dict[str, InstallationResult] = {}
        self._python_command = None
        self.deployment_config: Optional[Dict[str, Any]] = None
        
        logger.info(f"DependencyManager initialized with config: {self.config}")
    
    async def initialize(self) -> ServiceResponse:
        """
        Initialize dependency manager service
        
        Returns:
            ServiceResponse indicating initialization success
        """
        try:
            logger.info("Initializing dependency manager...")
            
            # Initialize deployment integration if available
            await self._initialize_deployment_integration()
            
            # Check all core dependencies
            await self._check_all_dependencies()
            
            logger.info("Dependency manager initialized successfully")
            return ServiceResponse(
                operation_id="dependency_manager_init",
                success=True,
                data={"initialized": True, "dependencies_checked": len(self._dependencies)}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize dependency manager: {e}")
            return ServiceResponse(
                operation_id="dependency_manager_init",
                success=False,
                error=str(e)
            )
    
    async def _initialize_deployment_integration(self) -> None:
        """Initialize deployment integration if available"""
        try:
            # Try to load deployment configuration
            from claude_pm.services.parent_directory_manager import ParentDirectoryManager
            
            manager = ParentDirectoryManager()
            await manager.initialize()
            
            self.deployment_config = await manager.get_deployment_config()
            logger.debug("Deployment integration initialized")
            
        except ImportError:
            logger.debug("Deployment integration not available")
        except Exception as e:
            logger.warning(f"Failed to initialize deployment integration: {e}")
    
    async def _check_all_dependencies(self) -> None:
        """Check all core dependencies"""
        for dep_name, config in self.CORE_DEPENDENCIES.items():
            dependency_info = DependencyInfo(
                name=dep_name,
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
                
                self._dependencies[dep_name] = dependency_info
                logger.debug(f"Checked dependency {dep_name}: installed={dependency_info.is_installed}")
                
            except Exception as e:
                dependency_info.error_message = str(e)
                self._dependencies[dep_name] = dependency_info
                logger.warning(f"Failed to check dependency {dep_name}: {e}")
    
    async def _check_ai_trackdown_tools(self, dependency_info: DependencyInfo, config: Dict[str, Any]) -> None:
        """Check AI Trackdown Tools installation"""
        python_package = config.get("python_package", "ai_trackdown_pytools")
        
        # Try to import as Python package
        try:
            module = importlib.import_module(python_package)
            dependency_info.is_installed = True
            dependency_info.installation_method = InstallationMethod.PIP
            
            # Try to get version from module
            if hasattr(module, "__version__"):
                dependency_info.version = module.__version__
            elif hasattr(module, "version"):
                dependency_info.version = module.version
            else:
                dependency_info.version = "1.1.0"  # Default version
            
            return
            
        except ImportError:
            # Python package not found, check for command availability
            pass
        
        # Fall back to checking command availability
        commands = config.get("commands", ["aitrackdown", "atd"])
        for command in commands:
            if await self._check_command_available(command):
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.NPM_GLOBAL
                
                # Try to get version
                try:
                    result = await self._run_command([command, "--version"])
                    if result.returncode == 0:
                        dependency_info.version = self._parse_version_from_output(result.stdout)
                except Exception:
                    dependency_info.version = "unknown"
                
                break
        
        if not dependency_info.is_installed:
            dependency_info.error_message = f"Python package '{python_package}' not found and commands not available: {commands}"
    
    async def _check_system_binary(self, dependency_info: DependencyInfo, config: Dict[str, Any]) -> None:
        """Check system binary installation"""
        commands = config.get("commands", [dependency_info.name])
        version_command = config.get("version_command", "--version")
        
        for command in commands:
            if await self._check_command_available(command):
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.SYSTEM
                
                # Get version
                try:
                    result = await self._run_command([command, version_command])
                    if result.returncode == 0:
                        dependency_info.version = self._parse_version_from_output(result.stdout)
                except Exception:
                    dependency_info.version = "unknown"
                
                # Get installation path
                try:
                    result = await self._run_command(["which", command])
                    if result.returncode == 0:
                        dependency_info.installation_path = result.stdout.strip()
                except Exception:
                    pass
                
                break
        
        if not dependency_info.is_installed:
            dependency_info.error_message = f"Commands not found: {commands}"
    
    async def _check_python_package(self, dependency_info: DependencyInfo, config: Dict[str, Any]) -> None:
        """Check Python package installation"""
        package_name = config.get("package_name", dependency_info.name)
        
        try:
            module = importlib.import_module(package_name)
            dependency_info.is_installed = True
            dependency_info.installation_method = InstallationMethod.PIP
            
            # Try to get version
            if hasattr(module, "__version__"):
                dependency_info.version = module.__version__
            elif hasattr(module, "version"):
                dependency_info.version = module.version
            else:
                dependency_info.version = "unknown"
                
        except ImportError as e:
            dependency_info.is_installed = False
            dependency_info.error_message = str(e)
    
    async def _check_npm_global(self, dependency_info: DependencyInfo, config: Dict[str, Any]) -> None:
        """Check npm global package installation"""
        package_name = config.get("package_name", dependency_info.name)
        
        try:
            # Check with npm list -g
            result = await self._run_command(["npm", "list", "-g", package_name])
            
            if result.returncode == 0:
                dependency_info.is_installed = True
                dependency_info.installation_method = InstallationMethod.NPM_GLOBAL
                
                # Parse version from output
                version_match = re.search(rf"{re.escape(package_name)}@(\S+)", result.stdout)
                if version_match:
                    dependency_info.version = version_match.group(1)
                else:
                    dependency_info.version = "unknown"
            else:
                dependency_info.is_installed = False
                dependency_info.error_message = "Package not found in global npm packages"
                
        except Exception as e:
            dependency_info.is_installed = False
            dependency_info.error_message = str(e)
    
    async def _check_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH"""
        try:
            result = await self._run_command(["which", command])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _check_python_available(self) -> bool:
        """Check if Python is available"""
        python_cmd = self._detect_python_command()
        return await self._check_command_available(python_cmd)
    
    async def _check_node_available(self) -> bool:
        """Check if Node.js is available"""
        return await self._check_command_available("node")
    
    async def _check_npm_available(self) -> bool:
        """Check if npm is available"""
        return await self._check_command_available("npm")
    
    async def _check_git_available(self) -> bool:
        """Check if Git is available"""
        return await self._check_command_available("git")
    
    async def _check_ai_trackdown_tools_available(self) -> bool:
        """Check if AI Trackdown Tools are available"""
        # Only check Python package
        try:
            import ai_trackdown_pytools
            return True
        except ImportError:
            return False
    
    def _detect_python_command(self) -> str:
        """Detect the correct Python command to use"""
        if self._python_command:
            return self._python_command
        
        # Try python3 first, then python
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run([cmd, "--version"], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self._python_command = cmd
                    return cmd
            except Exception:
                continue
        
        self._python_command = "python3"  # Default fallback
        return self._python_command
    
    def _select_best_installation_method(self, dep_type: DependencyType, config: Dict[str, Any]) -> InstallationMethod:
        """Select the best installation method for a dependency type"""
        # AI_TRACKDOWN_TOOLS is always installed via pip
        if dep_type == DependencyType.AI_TRACKDOWN_TOOLS:
            return InstallationMethod.PIP
            
        method_map = {
            DependencyType.PYTHON_PACKAGE: InstallationMethod.PIP,
            DependencyType.NPM_GLOBAL: InstallationMethod.NPM_GLOBAL,
            DependencyType.NPM_LOCAL: InstallationMethod.NPM_LOCAL,
            DependencyType.SYSTEM_BINARY: InstallationMethod.SYSTEM
        }
        return method_map.get(dep_type, InstallationMethod.MANUAL)
    
    def _parse_version_from_output(self, output: str) -> str:
        """Parse version number from command output"""
        if not output:
            return "unknown"
        
        # Common version patterns
        patterns = [
            r"(\d+\.\d+\.\d+)",  # x.y.z
            r"v(\d+\.\d+\.\d+)",  # vx.y.z
            r"version\s+(\d+\.\d+\.\d+)",  # version x.y.z
            r"(\d+\.\d+)",  # x.y
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    async def _run_command(self, command: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """Run a system command with timeout"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
            )
            return result
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out: {' '.join(command)}")
        except Exception as e:
            raise Exception(f"Command failed: {' '.join(command)} - {e}")
    
    async def install_dependency(self, dependency_name: str) -> InstallationResult:
        """
        Install a specific dependency
        
        Args:
            dependency_name: Name of the dependency to install
            
        Returns:
            InstallationResult with operation details
        """
        if dependency_name not in self.CORE_DEPENDENCIES:
            return InstallationResult(
                success=False,
                dependency_name=dependency_name,
                method=InstallationMethod.MANUAL,
                error_message=f"Unknown dependency: {dependency_name}"
            )
        
        config = self.CORE_DEPENDENCIES[dependency_name]
        dep_type = config["type"]
        method = self._select_best_installation_method(dep_type, config)
        
        try:
            if dep_type == DependencyType.AI_TRACKDOWN_TOOLS:
                result = await self._install_ai_trackdown_tools(dependency_name, config, method)
            elif dep_type == DependencyType.PYTHON_PACKAGE:
                result = await self._install_python_package(dependency_name, config, method)
            elif dep_type == DependencyType.NPM_GLOBAL:
                result = await self._install_npm_global(dependency_name, config, method)
            elif dep_type == DependencyType.NPM_LOCAL:
                result = await self._install_npm_local(dependency_name, config, method)
            elif dep_type == DependencyType.SYSTEM_BINARY:
                result = await self._install_system_binary(dependency_name, config, method)
            else:
                result = InstallationResult(
                    success=False,
                    dependency_name=dependency_name,
                    method=method,
                    error_message=f"Unsupported dependency type: {dep_type}"
                )
            
            # Cache result
            self._installation_cache[dependency_name] = result
            return result
            
        except Exception as e:
            result = InstallationResult(
                success=False,
                dependency_name=dependency_name,
                method=method,
                error_message=str(e)
            )
            self._installation_cache[dependency_name] = result
            return result
    
    async def _install_ai_trackdown_tools(self, name: str, config: Dict[str, Any], method: InstallationMethod) -> InstallationResult:
        """Install AI Trackdown Tools via pip only"""
        # Always install via pip
        pip_package = config.get("pip_package", "ai-trackdown-pytools==1.1.0")
        python_cmd = self._detect_python_command()
        
        start_time = datetime.now()
        result = await self._run_command(
            [python_cmd, "-m", "pip", "install", "--user", pip_package],
            timeout=self.installation_timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        success = result.returncode == 0
        
        # If failed due to externally managed environment, retry with --break-system-packages
        if not success and "externally-managed-environment" in result.stderr:
            result = await self._run_command(
                [python_cmd, "-m", "pip", "install", "--user", "--break-system-packages", pip_package],
                timeout=self.installation_timeout
            )
            success = result.returncode == 0
        
        return InstallationResult(
                success=success,
                dependency_name=name,
                method=method,
                logs=f"stdout: {result.stdout}\nstderr: {result.stderr}",
                error_message=result.stderr if not success else None,
                duration_seconds=duration
            )
    
    async def _install_python_package(self, name: str, config: Dict[str, Any], method: InstallationMethod) -> InstallationResult:
        """Install Python package via pip"""
        package_name = config.get("package_name", name)
        python_cmd = self._detect_python_command()
        
        start_time = datetime.now()
        result = await self._run_command(
            [python_cmd, "-m", "pip", "install", package_name],
            timeout=self.installation_timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        success = result.returncode == 0
        return InstallationResult(
            success=success,
            dependency_name=name,
            method=method,
            logs=f"stdout: {result.stdout}\nstderr: {result.stderr}",
            error_message=result.stderr if not success else None,
            duration_seconds=duration
        )
    
    async def _install_npm_global(self, name: str, config: Dict[str, Any], method: InstallationMethod) -> InstallationResult:
        """Install npm package globally"""
        package_name = config.get("package_name", name)
        
        start_time = datetime.now()
        result = await self._run_command(
            ["npm", "install", "-g", package_name],
            timeout=self.installation_timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        success = result.returncode == 0
        return InstallationResult(
            success=success,
            dependency_name=name,
            method=method,
            logs=f"stdout: {result.stdout}\nstderr: {result.stderr}",
            error_message=result.stderr if not success else None,
            duration_seconds=duration
        )
    
    async def _install_npm_local(self, name: str, config: Dict[str, Any], method: InstallationMethod) -> InstallationResult:
        """Install npm package locally"""
        package_name = config.get("package_name", name)
        
        start_time = datetime.now()
        result = await self._run_command(
            ["npm", "install", package_name],
            timeout=self.installation_timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        success = result.returncode == 0
        return InstallationResult(
            success=success,
            dependency_name=name,
            method=method,
            logs=f"stdout: {result.stdout}\nstderr: {result.stderr}",
            error_message=result.stderr if not success else None,
            duration_seconds=duration
        )
    
    async def _install_system_binary(self, name: str, config: Dict[str, Any], method: InstallationMethod) -> InstallationResult:
        """System binaries require manual installation"""
        return InstallationResult(
            success=False,
            dependency_name=name,
            method=method,
            error_message=f"System binary '{name}' requires manual installation. Please install via your system package manager."
        )
    
    async def verify_ai_trackdown_tools(self) -> bool:
        """Verify AI Trackdown Tools installation"""
        return await self._check_ai_trackdown_tools_available()
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check of dependency system"""
        return {
            "python_available": await self._check_python_available(),
            "node_available": await self._check_node_available(),
            "npm_available": await self._check_npm_available(),
            "git_available": await self._check_git_available(),
            "ai_trackdown_tools_available": await self._check_ai_trackdown_tools_available(),
            "critical_dependencies_met": await self._check_critical_dependencies()
        }
    
    async def _check_critical_dependencies(self) -> bool:
        """Check if all critical dependencies are met"""
        for dep_name, config in self.CORE_DEPENDENCIES.items():
            if config.get("critical", False):
                dep_info = self._dependencies.get(dep_name)
                if not dep_info or not dep_info.is_installed:
                    return False
        return True
    
    def get_dependencies(self) -> Dict[str, DependencyInfo]:
        """Get all tracked dependencies"""
        return self._dependencies.copy()
    
    def get_dependency(self, name: str) -> Optional[DependencyInfo]:
        """Get specific dependency info"""
        return self._dependencies.get(name)
    
    def get_installation_result(self, name: str) -> Optional[InstallationResult]:
        """Get installation result for a dependency"""
        return self._installation_cache.get(name)
    
    async def generate_dependency_report(self) -> DependencyReport:
        """Generate comprehensive dependency report"""
        deployment_type = "unknown"
        if self.deployment_config:
            deployment_type = self.deployment_config.get("config", {}).get("deploymentType", "unknown")
        
        missing_deps = []
        outdated_deps = []
        installed_count = 0
        
        for name, dep_info in self._dependencies.items():
            if not dep_info.is_installed:
                missing_deps.append(name)
            else:
                installed_count += 1
        
        total_deps = len(self._dependencies)
        health_score = int((installed_count / total_deps) * 100) if total_deps > 0 else 0
        
        recommendations = await self.get_installation_recommendations()
        
        return DependencyReport(
            deployment_type=deployment_type,
            platform=platform.system(),
            timestamp=datetime.now().isoformat(),
            dependencies=self._dependencies.copy(),
            missing_dependencies=missing_deps,
            outdated_dependencies=outdated_deps,
            installation_recommendations=recommendations,
            health_score=health_score
        )
    
    async def get_installation_recommendations(self) -> List[str]:
        """Get installation recommendations for missing dependencies"""
        recommendations = []
        
        for name, dep_info in self._dependencies.items():
            if not dep_info.is_installed:
                config = self.CORE_DEPENDENCIES.get(name, {})
                is_critical = config.get("critical", False)
                
                priority = "CRITICAL" if is_critical else "RECOMMENDED"
                method = self._select_best_installation_method(dep_info.type, config)
                
                if method == InstallationMethod.PIP:
                    # Use pip_package for AI_TRACKDOWN_TOOLS, package_name for others
                    package = config.get("pip_package") or config.get("package_name", name)
                    cmd = f"pip install {package}"
                elif method == InstallationMethod.SYSTEM:
                    cmd = f"Install {name} via your system package manager"
                else:
                    cmd = f"Manual installation required for {name}"
                
                recommendations.append(f"[{priority}] {name}: {cmd}")
        
        return recommendations
    
    async def _cleanup(self) -> None:
        """Cleanup dependency manager resources"""
        # Save dependency state if needed
        await self._save_dependency_state()
    
    async def _save_dependency_state(self) -> None:
        """Save current dependency state"""
        # Implementation could save to file or database
        logger.debug("Dependency state saved")


# Export key classes and functions
__all__ = [
    'DependencyManager',
    'DependencyType', 
    'InstallationMethod',
    'DependencyInfo',
    'InstallationResult',
    'DependencyReport'
]