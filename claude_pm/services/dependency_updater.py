#!/usr/bin/env python3
"""
Enhanced Dependency Updater Service for Claude PM Framework

Provides automated dependency updating with safety checks for both Python and Node.js ecosystems.
Builds on top of the existing DependencyManager to add update capabilities.
"""

import asyncio
import json
import subprocess
import logging
import re
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from dataclasses import dataclass, asdict
# import semver  # Not needed, using custom version comparison

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID, track
from rich.prompt import Confirm

from .dependency_manager import DependencyManager, DependencyInfo as BaseDependencyInfo, InstallationResult
from ..core.base_service import BaseService

console = Console()
logger = logging.getLogger(__name__)


class UpdateDependencyInfo(NamedTuple):
    """Extended dependency information for updates."""
    name: str
    current_version: str
    latest_version: str
    ecosystem: str  # 'python' or 'nodejs'
    update_available: bool
    is_major_update: bool
    is_breaking: bool
    security_update: bool
    confidence: str  # 'high', 'medium', 'low'
    changelog_url: Optional[str] = None
    breaking_changes: List[str] = None


@dataclass
class UpdateResult:
    """Result of a dependency update operation."""
    dependency: str
    success: bool
    old_version: str
    new_version: str
    ecosystem: str
    warnings: List[str]
    errors: List[str]
    test_passed: bool
    backup_created: str = None
    time_taken: float = 0.0


@dataclass
class UpdateConfig:
    """Configuration for dependency updates."""
    auto_update_minor: bool = True
    auto_update_patch: bool = True
    auto_update_major: bool = False
    run_tests_after_update: bool = True
    create_backup: bool = True
    skip_dev_dependencies: bool = False
    exclude_packages: List[str] = None
    update_schedule: Optional[str] = None  # 'daily', 'weekly', 'monthly'
    max_concurrent_updates: int = 3
    update_timeout: int = 300  # 5 minutes per update
    dry_run: bool = False


class DependencyUpdater(BaseService):
    """Enhanced dependency management service with auto-update capabilities."""
    
    def __init__(self, config: Optional[Dict] = None, project_root: Optional[Path] = None):
        """Initialize dependency updater."""
        super().__init__("dependency_updater", config)
        
        self.project_root = project_root or Path.cwd()
        self.backup_dir = self.project_root / ".claude-pm" / "dependency_backups"
        self.config_file = self.project_root / ".claude-pm" / "dependency_config.json"
        self.last_update_file = self.project_root / ".claude-pm" / "last_dependency_update.json"
        self.update_config = self._load_update_config()
        
        # Initialize base dependency manager
        self.base_manager = DependencyManager(config)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Package manager detection cache
        self._package_managers_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    async def _initialize(self) -> None:
        """Initialize the dependency updater."""
        self.logger.info("Initializing Dependency Updater...")
        
        # Initialize base dependency manager
        await self.base_manager._initialize()
        
        # Detect available package managers
        await self.detect_package_managers()
        
        self.logger.info("Dependency Updater initialized successfully")

    async def _cleanup(self) -> None:
        """Cleanup dependency updater."""
        self.logger.info("Cleaning up Dependency Updater...")
        
        # Save configuration
        self._save_update_config()
        
        # Cleanup base manager
        if self.base_manager:
            await self.base_manager._cleanup()
        
        self.logger.info("Dependency Updater cleanup completed")

    def _load_update_config(self) -> UpdateConfig:
        """Load dependency update configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                return UpdateConfig(**data)
            except Exception as e:
                logger.warning(f"Error loading dependency config: {e}")
        
        return UpdateConfig()

    def _save_update_config(self) -> None:
        """Save dependency update configuration."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(asdict(self.update_config), f, indent=2)

    def _save_last_update(self, updates: List[UpdateResult]) -> None:
        """Save information about the last update session."""
        update_info = {
            "timestamp": datetime.now().isoformat(),
            "updates": [asdict(update) for update in updates],
            "success_count": sum(1 for u in updates if u.success),
            "total_count": len(updates),
            "test_success_count": sum(1 for u in updates if u.test_passed)
        }
        
        with open(self.last_update_file, 'w') as f:
            json.dump(update_info, f, indent=2)

    async def detect_package_managers(self) -> Dict[str, bool]:
        """Detect which package managers are available in the project."""
        current_time = datetime.now()
        
        # Use cache if available and not expired
        if (self._package_managers_cache and self._cache_timestamp and 
            (current_time - self._cache_timestamp).total_seconds() < self._cache_ttl):
            return self._package_managers_cache
        
        managers = {
            # Python package managers
            'pip': True,  # Always available with Python
            'poetry': (self.project_root / "pyproject.toml").exists() and await self._check_command("poetry"),
            'pipenv': (self.project_root / "Pipfile").exists() and await self._check_command("pipenv"),
            'conda': await self._check_command("conda"),
            
            # Node.js package managers
            'npm': (self.project_root / "package.json").exists() and await self._check_command("npm"),
            'yarn': (self.project_root / "yarn.lock").exists() and await self._check_command("yarn"),
            'pnpm': (self.project_root / "pnpm-lock.yaml").exists() and await self._check_command("pnpm"),
        }
        
        available_managers = {k: v for k, v in managers.items() if v}
        
        # Cache results
        self._package_managers_cache = available_managers
        self._cache_timestamp = current_time
        
        return available_managers

    async def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            result = await self._run_command([command, "--version"], timeout=5)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def get_python_dependencies(self) -> List[UpdateDependencyInfo]:
        """Get Python dependency information with update details."""
        dependencies = []
        
        try:
            # Check pyproject.toml dependencies
            if (self.project_root / "pyproject.toml").exists():
                dependencies.extend(await self._get_pyproject_dependencies())
            
            # Check requirements files
            for req_file in self.project_root.glob("requirements*.txt"):
                dependencies.extend(await self._get_requirements_dependencies(req_file))
            
            # Check requirements directory
            req_dir = self.project_root / "requirements"
            if req_dir.exists():
                for req_file in req_dir.glob("*.txt"):
                    dependencies.extend(await self._get_requirements_dependencies(req_file))
                    
        except Exception as e:
            logger.error(f"Error getting Python dependencies: {e}")
        
        return dependencies

    async def _get_pyproject_dependencies(self) -> List[UpdateDependencyInfo]:
        """Parse dependencies from pyproject.toml."""
        dependencies = []
        
        try:
            # Try tomllib first (Python 3.11+), then tomli, then toml
            try:
                import tomllib
                with open(self.project_root / "pyproject.toml", 'rb') as f:
                    data = tomllib.load(f)
            except ImportError:
                try:
                    import tomli
                    with open(self.project_root / "pyproject.toml", 'rb') as f:
                        data = tomli.load(f)
                except ImportError:
                    import toml
                    with open(self.project_root / "pyproject.toml", 'r') as f:
                        data = toml.load(f)
            
            # Main dependencies
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    dep_info = await self._parse_python_dependency(dep)
                    if dep_info:
                        dependencies.append(dep_info)
            
            # Optional dependencies
            if "project" in data and "optional-dependencies" in data["project"]:
                for group, deps in data["project"]["optional-dependencies"].items():
                    if not self.update_config.skip_dev_dependencies or group != "dev":
                        for dep in deps:
                            dep_info = await self._parse_python_dependency(dep)
                            if dep_info:
                                dependencies.append(dep_info)
                                
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")
        
        return dependencies

    async def _get_requirements_dependencies(self, req_file: Path) -> List[UpdateDependencyInfo]:
        """Parse dependencies from requirements file."""
        dependencies = []
        
        try:
            with open(req_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-r"):
                        dep_info = await self._parse_python_dependency(line)
                        if dep_info:
                            dependencies.append(dep_info)
                            
        except Exception as e:
            logger.error(f"Error parsing {req_file}: {e}")
        
        return dependencies

    async def _parse_python_dependency(self, dep_spec: str) -> Optional[UpdateDependencyInfo]:
        """Parse a Python dependency specification."""
        # Remove comments and whitespace
        dep_spec = dep_spec.split("#")[0].strip()
        if not dep_spec:
            return None
        
        # Extract package name and version constraint
        match = re.match(r"([a-zA-Z0-9_-]+)(?:\[.*?\])?([>=<~!]+.*)?", dep_spec)
        if not match:
            return None
        
        package_name = match.group(1)
        
        # Skip if in exclude list
        if self.update_config.exclude_packages and package_name in self.update_config.exclude_packages:
            return None
        
        try:
            # Get current version
            current_version = await self._get_python_package_version(package_name)
            if not current_version:
                return None
            
            # Get latest version
            latest_version = await self._get_latest_python_version(package_name)
            if not latest_version:
                return None
            
            # Check for updates and analyze them
            update_available = self._compare_versions(current_version, latest_version) < 0
            is_major_update = self._is_major_update(current_version, latest_version)
            
            # Get additional information
            security_update = await self._check_python_security_update(package_name, current_version, latest_version)
            changelog_url = f"https://pypi.org/project/{package_name}/#history"
            
            # Determine confidence level
            confidence = self._determine_update_confidence(current_version, latest_version, package_name)
            
            return UpdateDependencyInfo(
                name=package_name,
                current_version=current_version,
                latest_version=latest_version,
                ecosystem="python",
                update_available=update_available,
                is_major_update=is_major_update,
                is_breaking=is_major_update,  # Simplified - major updates might be breaking
                security_update=security_update,
                confidence=confidence,
                changelog_url=changelog_url
            )
            
        except Exception as e:
            logger.debug(f"Error processing Python package {package_name}: {e}")
            return None

    async def _get_python_package_version(self, package_name: str) -> Optional[str]:
        """Get currently installed version of a Python package."""
        try:
            result = await self._run_command(["pip", "show", package_name])
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
        except Exception as e:
            logger.debug(f"Error getting version for {package_name}: {e}")
        
        return None

    async def _get_latest_python_version(self, package_name: str) -> Optional[str]:
        """Get latest available version of a Python package from PyPI."""
        try:
            # Try using pip index versions (pip 21.2+)
            result = await self._run_command(["pip", "index", "versions", package_name])
            if result.returncode == 0:
                # Parse output to get latest version
                lines = result.stdout.split("\n")
                for line in lines:
                    if "Available versions:" in line:
                        versions = line.split(":", 1)[1].strip().split(", ")
                        if versions and versions[0]:
                            return versions[0]
        except Exception:
            # Fallback to PyPI API
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return data["info"]["version"]
            except Exception as e:
                logger.debug(f"Error getting latest version for {package_name}: {e}")
        
        return None

    async def get_nodejs_dependencies(self) -> List[UpdateDependencyInfo]:
        """Get Node.js dependency information with update details."""
        dependencies = []
        
        if not (self.project_root / "package.json").exists():
            return dependencies
        
        try:
            with open(self.project_root / "package.json") as f:
                package_data = json.load(f)
            
            # Regular dependencies
            if "dependencies" in package_data:
                for name, version in package_data["dependencies"].items():
                    dep_info = await self._parse_nodejs_dependency(name, version, False)
                    if dep_info:
                        dependencies.append(dep_info)
            
            # Dev dependencies
            if not self.update_config.skip_dev_dependencies and "devDependencies" in package_data:
                for name, version in package_data["devDependencies"].items():
                    dep_info = await self._parse_nodejs_dependency(name, version, True)
                    if dep_info:
                        dependencies.append(dep_info)
                        
        except Exception as e:
            logger.error(f"Error getting Node.js dependencies: {e}")
        
        return dependencies

    async def _parse_nodejs_dependency(self, name: str, version_spec: str, is_dev: bool) -> Optional[UpdateDependencyInfo]:
        """Parse a Node.js dependency."""
        # Skip if in exclude list
        if self.update_config.exclude_packages and name in self.update_config.exclude_packages:
            return None
        
        try:
            # Get current version
            current_version = await self._get_nodejs_package_version(name)
            if not current_version:
                return None
            
            # Get latest version
            latest_version = await self._get_latest_nodejs_version(name)
            if not latest_version:
                return None
            
            # Check for updates and analyze them
            update_available = self._compare_versions(current_version, latest_version) < 0
            is_major_update = self._is_major_update(current_version, latest_version)
            
            # Get additional information
            security_update = await self._check_nodejs_security_update(name, current_version, latest_version)
            changelog_url = f"https://www.npmjs.com/package/{name}?activeTab=versions"
            
            # Determine confidence level
            confidence = self._determine_update_confidence(current_version, latest_version, name)
            
            return UpdateDependencyInfo(
                name=name,
                current_version=current_version,
                latest_version=latest_version,
                ecosystem="nodejs",
                update_available=update_available,
                is_major_update=is_major_update,
                is_breaking=is_major_update,
                security_update=security_update,
                confidence=confidence,
                changelog_url=changelog_url
            )
            
        except Exception as e:
            logger.debug(f"Error processing Node.js package {name}: {e}")
            return None

    async def _get_nodejs_package_version(self, package_name: str) -> Optional[str]:
        """Get currently installed version of a Node.js package."""
        try:
            result = await self._run_command(["npm", "list", package_name, "--depth=0", "--json"])
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if "dependencies" in data and package_name in data["dependencies"]:
                    return data["dependencies"][package_name]["version"]
        except Exception as e:
            logger.debug(f"Error getting Node.js version for {package_name}: {e}")
        
        return None

    async def _get_latest_nodejs_version(self, package_name: str) -> Optional[str]:
        """Get latest available version of a Node.js package from npm."""
        try:
            result = await self._run_command(["npm", "view", package_name, "version"])
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Error getting latest Node.js version for {package_name}: {e}")
        
        return None

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two semantic versions. Returns -1, 0, or 1."""
        def normalize_version(v):
            # Remove prefixes like 'v', '^', '~' and clean version string
            v = re.sub(r'^[v=^~]', '', v)
            # Handle pre-release versions
            v = v.split('-')[0].split('+')[0]
            parts = v.split('.')
            # Pad with zeros to ensure 3 parts
            while len(parts) < 3:
                parts.append('0')
            return [int(x) for x in parts[:3] if x.isdigit()]
        
        try:
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            for a, b in zip(v1_parts, v2_parts):
                if a < b:
                    return -1
                elif a > b:
                    return 1
            
            return 0
            
        except Exception:
            # Fallback to string comparison
            return -1 if version1 < version2 else (1 if version1 > version2 else 0)

    def _is_major_update(self, current: str, latest: str) -> bool:
        """Check if this is a major version update."""
        try:
            def get_major_version(v):
                v = re.sub(r'^[v=^~]', '', v)
                v = v.split('-')[0].split('+')[0]
                return int(v.split('.')[0])
            
            return get_major_version(current) < get_major_version(latest)
        except Exception:
            return False

    def _determine_update_confidence(self, current: str, latest: str, package_name: str) -> str:
        """Determine confidence level for the update."""
        if not self._is_major_update(current, latest):
            return "high"  # Minor/patch updates are generally safe
        
        # For major updates, check some heuristics
        try:
            current_major = int(current.split('.')[0])
            latest_major = int(latest.split('.')[0])
            
            if latest_major - current_major > 2:
                return "low"  # Multiple major versions behind
            elif latest_major - current_major > 1:
                return "medium"  # One major version behind
            else:
                return "medium"  # One major version update
        except Exception:
            return "low"

    async def _check_python_security_update(self, package: str, current: str, latest: str) -> bool:
        """Check if there are security fixes in the update."""
        # This would typically integrate with vulnerability databases
        # For now, this is a placeholder that could be enhanced with actual security data
        try:
            # Check if pip-audit is available and use it
            if await self._check_command("pip-audit"):
                result = await self._run_command(["pip-audit", "--format", "json", "--require", f"{package}=={current}"])
                if result.returncode != 0:  # Non-zero means vulnerabilities found
                    return True
        except Exception:
            pass
        
        return False

    async def _check_nodejs_security_update(self, package: str, current: str, latest: str) -> bool:
        """Check if there are security fixes in the Node.js update."""
        try:
            # Use npm audit to check for vulnerabilities
            result = await self._run_command(["npm", "audit", "--audit-level", "moderate", "--json"])
            if result.returncode != 0:
                try:
                    data = json.loads(result.stdout)
                    vulnerabilities = data.get("vulnerabilities", {})
                    return package in vulnerabilities
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        
        return False

    async def create_backup(self) -> str:
        """Create backup of current dependency files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        files_backed_up = []
        
        # Backup Python files
        for file_name in ["pyproject.toml", "requirements.txt", "Pipfile", "Pipfile.lock", "poetry.lock"]:
            source = self.project_root / file_name
            if source.exists():
                shutil.copy2(source, backup_path / file_name)
                files_backed_up.append(file_name)
        
        # Backup requirements directory
        req_dir = self.project_root / "requirements"
        if req_dir.exists():
            shutil.copytree(req_dir, backup_path / "requirements", dirs_exist_ok=True)
            files_backed_up.append("requirements/")
        
        # Backup Node.js files
        for file_name in ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
            source = self.project_root / file_name
            if source.exists():
                shutil.copy2(source, backup_path / file_name)
                files_backed_up.append(file_name)
        
        # Save backup metadata
        metadata = {
            "timestamp": timestamp,
            "files": files_backed_up,
            "project_root": str(self.project_root)
        }
        
        with open(backup_path / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        console.print(f"[green]✓[/green] Backup created: {backup_name} ({len(files_backed_up)} files)")
        return backup_name

    async def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            console.print(f"[red]✗[/red] Backup {backup_name} not found")
            return False
        
        try:
            # Read backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                files_to_restore = metadata.get("files", [])
            else:
                files_to_restore = [f.name for f in backup_path.iterdir() if f.is_file()]
            
            # Restore all backed up files
            for backup_file in backup_path.rglob("*"):
                if backup_file.is_file() and backup_file.name != "backup_metadata.json":
                    relative_path = backup_file.relative_to(backup_path)
                    target_path = self.project_root / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, target_path)
            
            console.print(f"[green]✓[/green] Restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Error restoring backup: {e}")
            return False

    async def update_dependencies(self, 
                                dependencies: List[UpdateDependencyInfo], 
                                dry_run: bool = False) -> List[UpdateResult]:
        """Update dependencies with progress tracking."""
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No actual updates will be performed[/yellow]")
        
        results = []
        
        # Create backup if enabled and not dry run
        backup_name = None
        if self.update_config.create_backup and not dry_run:
            backup_name = await self.create_backup()
        
        # Filter dependencies based on config
        filtered_deps = []
        for dep in dependencies:
            if not dep.update_available:
                continue
            
            # Check update policy
            if dep.is_major_update and not self.update_config.auto_update_major:
                console.print(f"[yellow]⚠[/yellow] Skipping major update for {dep.name} ({dep.current_version} → {dep.latest_version})")
                continue
            
            filtered_deps.append(dep)
        
        if not filtered_deps:
            console.print("[yellow]No dependencies to update based on current configuration[/yellow]")
            return results
        
        # Update dependencies with progress bar
        with Progress() as progress:
            task = progress.add_task("Updating dependencies...", total=len(filtered_deps))
            
            # Use semaphore to limit concurrent updates
            semaphore = asyncio.Semaphore(self.update_config.max_concurrent_updates)
            
            async def update_single_dependency(dep: UpdateDependencyInfo) -> UpdateResult:
                async with semaphore:
                    return await self._update_single_dependency(dep, dry_run, backup_name)
            
            # Execute updates
            tasks = [update_single_dependency(dep) for dep in filtered_deps]
            
            for i, coro in enumerate(asyncio.as_completed(tasks)):
                result = await coro
                results.append(result)
                progress.update(task, advance=1)
                
                # Display immediate result
                status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                console.print(f"{status} {result.dependency}: {result.old_version} → {result.new_version}")
        
        # Save update results
        if not dry_run:
            self._save_last_update(results)
        
        return results

    async def _update_single_dependency(self, 
                                      dep: UpdateDependencyInfo, 
                                      dry_run: bool,
                                      backup_name: str) -> UpdateResult:
        """Update a single dependency."""
        start_time = datetime.now()
        
        result = UpdateResult(
            dependency=dep.name,
            success=False,
            old_version=dep.current_version,
            new_version=dep.latest_version,
            ecosystem=dep.ecosystem,
            warnings=[],
            errors=[],
            test_passed=False,
            backup_created=backup_name
        )
        
        if dry_run:
            result.success = True
            result.warnings.append("Dry run - no actual update performed")
            return result
        
        try:
            # Perform the update
            if dep.ecosystem == "python":
                success = await self._update_python_dependency(dep)
            elif dep.ecosystem == "nodejs":
                success = await self._update_nodejs_dependency(dep)
            else:
                result.errors.append(f"Unsupported ecosystem: {dep.ecosystem}")
                return result
            
            result.success = success
            
            # Run tests if configured and update was successful
            if success and self.update_config.run_tests_after_update:
                result.test_passed = await self._run_tests()
                if not result.test_passed:
                    result.warnings.append("Tests failed after update")
            
            # Add warnings for risky updates
            if dep.is_major_update:
                result.warnings.append("Major version update - review for breaking changes")
            if dep.confidence == "low":
                result.warnings.append("Low confidence update - thorough testing recommended")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Error updating {dep.name}: {e}")
        
        result.time_taken = (datetime.now() - start_time).total_seconds()
        return result

    async def _update_python_dependency(self, dep: UpdateDependencyInfo) -> bool:
        """Update a Python dependency."""
        managers = await self.detect_package_managers()
        
        try:
            if managers.get("poetry"):
                return await self._update_with_poetry(dep)
            elif managers.get("pipenv"):
                return await self._update_with_pipenv(dep)
            else:
                return await self._update_with_pip(dep)
        except Exception as e:
            logger.error(f"Error updating Python dependency {dep.name}: {e}")
            return False

    async def _update_with_pip(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using pip."""
        cmd = ["pip", "install", "--upgrade", f"{dep.name}=={dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _update_with_poetry(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using poetry."""
        cmd = ["poetry", "add", f"{dep.name}@{dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _update_with_pipenv(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using pipenv."""
        cmd = ["pipenv", "install", f"{dep.name}=={dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _update_nodejs_dependency(self, dep: UpdateDependencyInfo) -> bool:
        """Update a Node.js dependency."""
        managers = await self.detect_package_managers()
        
        try:
            if managers.get("yarn"):
                return await self._update_with_yarn(dep)
            elif managers.get("pnpm"):
                return await self._update_with_pnpm(dep)
            else:
                return await self._update_with_npm(dep)
        except Exception as e:
            logger.error(f"Error updating Node.js dependency {dep.name}: {e}")
            return False

    async def _update_with_npm(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using npm."""
        cmd = ["npm", "install", f"{dep.name}@{dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _update_with_yarn(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using yarn."""
        cmd = ["yarn", "add", f"{dep.name}@{dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _update_with_pnpm(self, dep: UpdateDependencyInfo) -> bool:
        """Update dependency using pnpm."""
        cmd = ["pnpm", "add", f"{dep.name}@{dep.latest_version}"]
        result = await self._run_command(cmd, timeout=self.update_config.update_timeout)
        return result.returncode == 0

    async def _run_tests(self) -> bool:
        """Run project tests to verify updates."""
        try:
            # Try pytest first
            if (self.project_root / "pytest.ini").exists() or (self.project_root / "pyproject.toml").exists():
                result = await self._run_command(["pytest", "--tb=short", "-q"], timeout=300)
                if result.returncode == 0:
                    return True
            
            # Try npm test
            if (self.project_root / "package.json").exists():
                result = await self._run_command(["npm", "test"], timeout=300)
                if result.returncode == 0:
                    return True
            
            # If no tests found, assume success
            return True
            
        except Exception as e:
            logger.debug(f"Error running tests: {e}")
            return False

    async def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd or self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )
        except asyncio.TimeoutError:
            try:
                process.terminate()
                await process.wait()
            except:
                pass
            raise subprocess.TimeoutExpired(cmd, timeout)

    async def check_security_vulnerabilities(self) -> Dict[str, List[str]]:
        """Check for security vulnerabilities in dependencies."""
        vulnerabilities = {"python": [], "nodejs": []}
        
        try:
            # Check Python vulnerabilities with pip-audit if available
            if await self._check_command("pip-audit"):
                result = await self._run_command(["pip-audit", "--format", "json"])
                if result.returncode != 0:  # Non-zero means vulnerabilities found
                    try:
                        data = json.loads(result.stdout)
                        for vuln in data.get("vulnerabilities", []):
                            vulnerabilities["python"].append(vuln["package"])
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.debug(f"Error checking Python security: {e}")
        
        try:
            # Check Node.js vulnerabilities
            if (self.project_root / "package.json").exists():
                result = await self._run_command(["npm", "audit", "--json"])
                if result.returncode != 0:  # npm audit returns non-zero for vulnerabilities
                    try:
                        data = json.loads(result.stdout)
                        for vuln_id, vuln in data.get("vulnerabilities", {}).items():
                            vulnerabilities["nodejs"].append(vuln["name"])
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.debug(f"Error checking Node.js security: {e}")
        
        return vulnerabilities

    def display_dependency_status(self, dependencies: List[UpdateDependencyInfo]) -> None:
        """Display dependency status in a rich table."""
        if not dependencies:
            console.print("[yellow]No dependencies found[/yellow]")
            return
        
        # Group by ecosystem
        python_deps = [d for d in dependencies if d.ecosystem == "python"]
        nodejs_deps = [d for d in dependencies if d.ecosystem == "nodejs"]
        
        if python_deps:
            self._display_ecosystem_table("Python Dependencies", python_deps)
        
        if nodejs_deps:
            self._display_ecosystem_table("Node.js Dependencies", nodejs_deps)

    def _display_ecosystem_table(self, title: str, dependencies: List[UpdateDependencyInfo]) -> None:
        """Display dependencies for a specific ecosystem."""
        table = Table(title=title)
        table.add_column("Package", style="cyan")
        table.add_column("Current", style="blue")
        table.add_column("Latest", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Confidence", style="white")
        
        for dep in dependencies:
            if dep.update_available:
                if dep.is_major_update:
                    status = "[red]Major Update[/red]"
                    update_type = "[red]⚠ Breaking[/red]" if dep.is_breaking else "[yellow]Major[/yellow]"
                else:
                    status = "[green]Update Available[/green]"
                    update_type = "[green]Minor/Patch[/green]"
            else:
                status = "[dim]Up to date[/dim]"
                update_type = "[dim]None[/dim]"
            
            if dep.security_update:
                status = "[red bold]Security Update![/red bold]"
            
            confidence_color = {
                "high": "[green]High[/green]",
                "medium": "[yellow]Medium[/yellow]", 
                "low": "[red]Low[/red]"
            }.get(dep.confidence, "[dim]Unknown[/dim]")
            
            table.add_row(
                dep.name,
                dep.current_version,
                dep.latest_version,
                status,
                update_type,
                confidence_color
            )
        
        console.print(table)

    def display_update_results(self, results: List[UpdateResult]) -> None:
        """Display update results."""
        if not results:
            console.print("[yellow]No updates performed[/yellow]")
            return
        
        success_count = sum(1 for r in results if r.success)
        test_success_count = sum(1 for r in results if r.test_passed)
        
        console.print(Panel(
            f"Updated {success_count}/{len(results)} dependencies\n"
            f"Tests passed: {test_success_count}/{len(results)}",
            title="Update Summary",
            style="green" if success_count == len(results) else "yellow"
        ))
        
        # Show detailed results
        table = Table(title="Update Details")
        table.add_column("Package", style="cyan")
        table.add_column("Ecosystem", style="blue")
        table.add_column("Old Version", style="red")
        table.add_column("New Version", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Tests", style="magenta")
        table.add_column("Time", style="white")
        
        for result in results:
            status = "[green]✓ Success[/green]" if result.success else "[red]✗ Failed[/red]"
            test_status = (
                "[green]✓ Passed[/green]" if result.test_passed 
                else "[red]✗ Failed[/red]" if result.success 
                else "[dim]N/A[/dim]"
            )
            
            time_str = f"{result.time_taken:.1f}s" if result.time_taken > 0 else "N/A"
            
            table.add_row(
                result.dependency,
                result.ecosystem,
                result.old_version,
                result.new_version,
                status,
                test_status,
                time_str
            )
        
        console.print(table)
        
        # Show warnings and errors
        for result in results:
            if result.warnings:
                console.print(f"[yellow]⚠ {result.dependency}:[/yellow] {', '.join(result.warnings)}")
            if result.errors:
                console.print(f"[red]✗ {result.dependency}:[/red] {', '.join(result.errors)}")

    async def get_update_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for dependency updates."""
        python_deps = await self.get_python_dependencies()
        nodejs_deps = await self.get_nodejs_dependencies()
        all_deps = python_deps + nodejs_deps
        
        recommendations = {
            "total_dependencies": len(all_deps),
            "updates_available": len([d for d in all_deps if d.update_available]),
            "security_updates": len([d for d in all_deps if d.security_update]),
            "major_updates": len([d for d in all_deps if d.is_major_update and d.update_available]),
            "safe_updates": len([d for d in all_deps if d.update_available and not d.is_major_update]),
            "high_confidence_updates": len([d for d in all_deps if d.update_available and d.confidence == "high"]),
            "last_update": self._get_last_update_time(),
            "recommendations": []
        }
        
        # Add specific recommendations
        if recommendations["security_updates"] > 0:
            recommendations["recommendations"].append({
                "priority": "critical",
                "action": "security_update",
                "message": f"Apply {recommendations['security_updates']} security updates immediately"
            })
        
        if recommendations["high_confidence_updates"] > 0:
            recommendations["recommendations"].append({
                "priority": "high",
                "action": "safe_update",
                "message": f"Apply {recommendations['high_confidence_updates']} high-confidence updates"
            })
        
        if recommendations["safe_updates"] > 0:
            recommendations["recommendations"].append({
                "priority": "medium",
                "action": "safe_update",
                "message": f"Apply {recommendations['safe_updates']} safe (minor/patch) updates"
            })
        
        if recommendations["major_updates"] > 0:
            recommendations["recommendations"].append({
                "priority": "low",
                "action": "major_update",
                "message": f"Review {recommendations['major_updates']} major updates (may have breaking changes)"
            })
        
        return recommendations

    def _get_last_update_time(self) -> Optional[str]:
        """Get the timestamp of the last dependency update."""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file) as f:
                    data = json.load(f)
                return data.get("timestamp")
            except Exception:
                pass
        return None

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "backup_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        backups.append({
                            "name": backup_dir.name,
                            "timestamp": metadata.get("timestamp"),
                            "files": len(metadata.get("files", [])),
                            "path": str(backup_dir)
                        })
                    except Exception:
                        # Fallback for backups without metadata
                        backups.append({
                            "name": backup_dir.name,
                            "timestamp": backup_dir.name.replace("backup_", "").replace("_", " "),
                            "files": len(list(backup_dir.iterdir())),
                            "path": str(backup_dir)
                        })
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)