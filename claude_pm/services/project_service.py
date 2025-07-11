"""
Project Service for Claude PM Framework.

Provides project management capabilities including:
- Project discovery and registration
- Framework compliance monitoring
- Project lifecycle management
- Integration with TrackDown system
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..core.base_service import BaseService


@dataclass
class ProjectInfo:
    """Information about a managed project."""

    name: str
    path: str
    type: str  # managed, standalone, framework
    status: str  # active, inactive, archived
    compliance_score: int
    last_activity: str
    framework_files: Dict[str, bool]
    git_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComplianceCheck:
    """Result of a project compliance check."""

    project_name: str
    score: int
    max_score: int
    passed_checks: int
    total_checks: int
    missing_files: List[str]
    recommendations: List[str]
    last_check: str


class ProjectService(BaseService):
    """
    Service for managing Claude PM projects and framework compliance.

    Provides:
    - Project discovery and registration
    - Framework compliance monitoring
    - Project health tracking
    - TrackDown system integration
    """

    REQUIRED_FILES = {
        "CLAUDE.md": {"weight": 30, "critical": True},
        "README.md": {"weight": 20, "critical": True},
        "trackdown/BACKLOG.md": {"weight": 15, "critical": False},
        "docs/INSTRUCTIONS.md": {"weight": 10, "critical": False},
        "docs/PROJECT.md": {"weight": 10, "critical": False},
        "docs/TOOLCHAIN.md": {"weight": 10, "critical": False},
        "docs/WORKFLOW.md": {"weight": 5, "critical": False},
    }

    def __init__(self, config: Optional[Dict] = None):
        """Initialize project service."""
        super().__init__("project_service", config)

        # Project paths
        self.base_path = Path(self.get_config("base_path", Path.home() / "Projects"))
        self.claude_pm_path = Path(self.get_config("claude_pm_path", self.base_path / "Claude-PM"))
        self.managed_path = Path(self.get_config("managed_path", self.base_path / "managed"))

        # Service settings
        self.auto_discovery_interval = self.get_config("auto_discovery_interval", 3600)  # 1 hour
        self.compliance_check_interval = self.get_config(
            "compliance_check_interval", 1800
        )  # 30 minutes

        # Project registry
        self._projects: Dict[str, ProjectInfo] = {}
        self._compliance_cache: Dict[str, ComplianceCheck] = {}

        # Supported project types
        self.project_types = {
            "managed": "Claude PM managed project",
            "standalone": "Standalone project with Claude PM integration",
            "framework": "Claude PM framework project",
        }

    async def _initialize(self) -> None:
        """Initialize the project service."""
        self.logger.info("Initializing Project Service...")

        # Verify paths exist
        self._ensure_paths_exist()

        # Discover existing projects
        await self._discover_projects()

        # Run initial compliance checks
        await self._check_all_compliance()

        self.logger.info(f"Project Service initialized with {len(self._projects)} projects")

    async def _cleanup(self) -> None:
        """Cleanup project service."""
        self.logger.info("Cleaning up Project Service...")

        # Save project registry
        await self._save_project_registry()

        # Clear caches
        self._projects.clear()
        self._compliance_cache.clear()

        self.logger.info("Project Service cleanup completed")

    async def _health_check(self) -> Dict[str, bool]:
        """Perform project service health checks."""
        checks = {}

        try:
            # Check if required paths exist
            checks["base_path_exists"] = self.base_path.exists()
            checks["claude_pm_path_exists"] = self.claude_pm_path.exists()
            checks["managed_path_exists"] = self.managed_path.exists()

            # Check project registry health
            checks["projects_registered"] = len(self._projects) > 0
            checks["compliance_cache_healthy"] = (
                len(self._compliance_cache) >= len(self._projects) * 0.8
            )

            # Check project accessibility
            accessible_projects = 0
            for project in self._projects.values():
                if Path(project.path).exists():
                    accessible_projects += 1

            checks["projects_accessible"] = accessible_projects >= len(self._projects) * 0.9

        except Exception as e:
            self.logger.error(f"Project service health check failed: {e}")
            checks["health_check_error"] = False

        return checks

    async def _start_custom_tasks(self) -> Optional[List]:
        """Start custom background tasks."""
        import asyncio

        tasks = []

        # Auto-discovery task
        if self.get_config("enable_auto_discovery", True):
            task = asyncio.create_task(self._auto_discovery_task())
            tasks.append(task)

        # Compliance monitoring task
        if self.get_config("enable_compliance_monitoring", True):
            task = asyncio.create_task(self._compliance_monitoring_task())
            tasks.append(task)

        return tasks if tasks else None

    def _ensure_paths_exist(self) -> None:
        """Ensure required paths exist."""
        paths_to_create = [
            self.managed_path,
            self.claude_pm_path / "logs",
            self.claude_pm_path / "trackdown",
        ]

        for path in paths_to_create:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured path exists: {path}")

    async def _discover_projects(self) -> None:
        """Discover projects in the filesystem with timeout protection."""
        self.logger.info("Discovering projects...")

        discovered_count = 0
        discovery_timeout = 30.0  # 30 second timeout for discovery

        try:
            # Use asyncio timeout to prevent blocking
            async def _discover_with_timeout():
                # Discover managed projects
                if self.managed_path.exists():
                    for project_path in self.managed_path.iterdir():
                        if project_path.is_dir() and not project_path.name.startswith("."):
                            project_info = await self._analyze_project(project_path, "managed")
                            if project_info:
                                self._projects[project_info.name] = project_info
                                nonlocal discovered_count
                                discovered_count += 1

                # Discover other projects in base path
                excluded_dirs = {"managed", "Claude-PM", "node_modules", ".git", "__pycache__"}
                if self.base_path.exists():
                    for project_path in self.base_path.iterdir():
                        if (
                            project_path.is_dir()
                            and not project_path.name.startswith(".")
                            and project_path.name not in excluded_dirs
                        ):
                            project_info = await self._analyze_project(project_path, "standalone")
                            if project_info:
                                self._projects[project_info.name] = project_info
                                discovered_count += 1

                # Add Claude PM framework as a special project
                if self.claude_pm_path.exists():
                    framework_info = await self._analyze_project(self.claude_pm_path, "framework")
                    if framework_info:
                        framework_info.name = "Claude-PM-Framework"
                        self._projects[framework_info.name] = framework_info
                        discovered_count += 1

                return discovered_count

            # Run discovery with timeout
            discovered_count = await asyncio.wait_for(_discover_with_timeout(), timeout=discovery_timeout)
            self.logger.info(f"Discovered {discovered_count} projects")

        except asyncio.TimeoutError:
            self.logger.warning(f"Project discovery timed out after {discovery_timeout}s, discovered {discovered_count} projects so far")
        except Exception as e:
            self.logger.error(f"Error during project discovery: {e}")
            self.logger.info(f"Discovered {discovered_count} projects before error")

    async def _analyze_project(
        self, project_path: Path, project_type: str
    ) -> Optional[ProjectInfo]:
        """Analyze a project directory and create ProjectInfo."""
        try:
            # Basic project information
            project_name = project_path.name

            # Check if it's a valid project (has some required files)
            has_claude_md = (project_path / "CLAUDE.md").exists()
            has_readme = (project_path / "README.md").exists()

            if not (has_claude_md or has_readme):
                return None  # Not a Claude PM project

            # Determine project status
            status = await self._determine_project_status(project_path)

            # Check framework files
            framework_files = {}
            for file_name in self.REQUIRED_FILES.keys():
                file_path = project_path / file_name
                framework_files[file_name] = file_path.exists()

            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(framework_files)

            # Get last activity
            last_activity = await self._get_last_activity(project_path)

            # Get git information
            git_info = await self._get_git_info(project_path)

            # Create project info
            project_info = ProjectInfo(
                name=project_name,
                path=str(project_path),
                type=project_type,
                status=status,
                compliance_score=compliance_score,
                last_activity=last_activity,
                framework_files=framework_files,
                git_info=git_info,
                metadata={"discovered_at": datetime.now().isoformat(), "analyzer_version": "1.0.0"},
            )

            return project_info

        except Exception as e:
            self.logger.warning(f"Failed to analyze project {project_path}: {e}")
            return None

    async def _determine_project_status(self, project_path: Path) -> str:
        """Determine project status based on activity and files."""
        # Check for recent git activity
        git_dir = project_path / ".git"
        if git_dir.exists():
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "log", "-1", "--format=%cd", "--date=iso"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    last_commit = datetime.fromisoformat(result.stdout.strip().replace(" ", "T"))
                    days_since = (datetime.now() - last_commit).days

                    if days_since <= 7:
                        return "active"
                    elif days_since <= 30:
                        return "recent"
                    else:
                        return "inactive"

            except Exception:
                pass

        # Check for recent file modifications
        try:
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not any(
                    part.startswith(".") for part in file_path.parts
                ):
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    days_since = (datetime.now() - mtime).days

                    if days_since <= 7:
                        return "active"

        except Exception:
            pass

        return "inactive"

    def _calculate_compliance_score(self, framework_files: Dict[str, bool]) -> int:
        """Calculate compliance score based on framework files."""
        total_weight = 0
        achieved_weight = 0

        for file_name, exists in framework_files.items():
            file_config = self.REQUIRED_FILES.get(file_name, {"weight": 1})
            weight = file_config["weight"]

            total_weight += weight
            if exists:
                achieved_weight += weight

        return round((achieved_weight / total_weight) * 100) if total_weight > 0 else 0

    async def _get_last_activity(self, project_path: Path) -> str:
        """Get last activity timestamp for a project."""
        try:
            latest_time = None

            # Check git commits
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "log", "-1", "--format=%cd", "--date=iso"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    git_time_str = result.stdout.strip().replace(" ", "T")
                    try:
                        git_time = datetime.fromisoformat(git_time_str)
                        # Ensure timezone awareness
                        if git_time.tzinfo is None:
                            git_time = git_time.replace(tzinfo=timezone.utc)
                        latest_time = git_time
                    except ValueError:
                        # If git time parsing fails, continue without git time
                        pass

            except Exception:
                pass

            # Check file modifications (optimized - limited scope for performance)
            # Only check important files, not ALL files recursively
            important_patterns = [
                "*.md", "*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml", 
                "package.json", "requirements.txt", "Makefile", "Dockerfile"
            ]
            
            files_checked = 0
            max_files = 100  # Limit for performance
            
            # Check root directory files first
            for pattern in important_patterns:
                for file_path in project_path.glob(pattern):
                    if files_checked >= max_files:
                        break
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                        if latest_time is None or mtime > latest_time:
                            latest_time = mtime
                        files_checked += 1
                
                if files_checked >= max_files:
                    break
            
            # If we haven't hit the limit, check one level deep
            if files_checked < max_files:
                for subdir in project_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name not in {'node_modules', '__pycache__', '.git'}:
                        for pattern in important_patterns:
                            for file_path in subdir.glob(pattern):
                                if files_checked >= max_files:
                                    break
                                if file_path.is_file():
                                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                                    if latest_time is None or mtime > latest_time:
                                        latest_time = mtime
                                    files_checked += 1
                            
                            if files_checked >= max_files:
                                break
                    
                    if files_checked >= max_files:
                        break

            return latest_time.isoformat() if latest_time else datetime.min.replace(tzinfo=timezone.utc).isoformat()

        except Exception as e:
            self.logger.warning(f"Failed to get last activity for {project_path}: {e}")
            return datetime.min.replace(tzinfo=timezone.utc).isoformat()

    async def _get_git_info(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Get git information for a project."""
        git_dir = project_path / ".git"
        if not git_dir.exists():
            return None

        try:
            import subprocess

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            remote_url = result.stdout.strip() if result.returncode == 0 else None

            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            has_changes = bool(result.stdout.strip()) if result.returncode == 0 else False

            return {
                "current_branch": current_branch,
                "remote_url": remote_url,
                "has_uncommitted_changes": has_changes,
                "is_git_repo": True,
            }

        except Exception as e:
            self.logger.warning(f"Failed to get git info for {project_path}: {e}")
            return {"is_git_repo": True, "error": str(e)}

    async def _check_all_compliance(self) -> None:
        """Check compliance for all registered projects."""
        self.logger.info("Checking compliance for all projects...")

        for project_name, project_info in self._projects.items():
            compliance = await self._check_project_compliance(project_info)
            self._compliance_cache[project_name] = compliance

        self.logger.info(f"Compliance checked for {len(self._compliance_cache)} projects")

    async def _check_project_compliance(self, project_info: ProjectInfo) -> ComplianceCheck:
        """Check compliance for a specific project."""
        project_path = Path(project_info.path)

        passed_checks = 0
        total_checks = len(self.REQUIRED_FILES)
        missing_files = []
        recommendations = []

        total_score = 0
        achieved_score = 0

        for file_name, file_config in self.REQUIRED_FILES.items():
            file_path = project_path / file_name
            weight = file_config["weight"]
            is_critical = file_config["critical"]

            total_score += weight

            if file_path.exists():
                passed_checks += 1
                achieved_score += weight
            else:
                missing_files.append(file_name)

                if is_critical:
                    recommendations.append(f"CRITICAL: Create {file_name}")
                else:
                    recommendations.append(f"Recommended: Create {file_name}")

        # Additional checks
        if project_path.name != "Claude-PM-Framework":  # Skip for framework itself
            # Check for trackdown directory
            trackdown_dir = project_path / "trackdown"
            if not trackdown_dir.exists():
                recommendations.append("Create trackdown/ directory for project management")

            # Check for docs directory
            docs_dir = project_path / "docs"
            if not docs_dir.exists():
                recommendations.append("Create docs/ directory for documentation")

        compliance_score = round((achieved_score / total_score) * 100) if total_score > 0 else 0

        return ComplianceCheck(
            project_name=project_info.name,
            score=compliance_score,
            max_score=total_score,
            passed_checks=passed_checks,
            total_checks=total_checks,
            missing_files=missing_files,
            recommendations=recommendations,
            last_check=datetime.now().isoformat(),
        )

    async def _auto_discovery_task(self) -> None:
        """Background task for automatic project discovery."""
        while not self._stop_event.is_set():
            try:
                await self._discover_projects()
                await asyncio.sleep(self.auto_discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-discovery task error: {e}")
                await asyncio.sleep(self.auto_discovery_interval)

    async def _compliance_monitoring_task(self) -> None:
        """Background task for compliance monitoring."""
        while not self._stop_event.is_set():
            try:
                await self._check_all_compliance()
                await asyncio.sleep(self.compliance_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Compliance monitoring task error: {e}")
                await asyncio.sleep(self.compliance_check_interval)

    async def _save_project_registry(self) -> None:
        """Save project registry to file."""
        try:
            registry_file = self.claude_pm_path / "logs" / "project-registry.json"
            registry_data = {
                "timestamp": datetime.now().isoformat(),
                "projects": {name: asdict(info) for name, info in self._projects.items()},
                "compliance": {
                    name: asdict(check) for name, check in self._compliance_cache.items()
                },
            }

            with open(registry_file, "w") as f:
                json.dump(registry_data, f, indent=2)

            self.logger.debug(f"Project registry saved to {registry_file}")

        except Exception as e:
            self.logger.error(f"Failed to save project registry: {e}")

    # Public API methods

    def get_projects(self) -> Dict[str, ProjectInfo]:
        """Get all registered projects."""
        return self._projects.copy()

    def get_project(self, name: str) -> Optional[ProjectInfo]:
        """Get a specific project by name."""
        return self._projects.get(name)

    def get_compliance(self, name: str) -> Optional[ComplianceCheck]:
        """Get compliance information for a project."""
        return self._compliance_cache.get(name)

    async def refresh_project(self, name: str) -> bool:
        """Refresh information for a specific project."""
        project_info = self._projects.get(name)
        if not project_info:
            return False

        try:
            # Re-analyze project
            updated_info = await self._analyze_project(Path(project_info.path), project_info.type)
            if updated_info:
                self._projects[name] = updated_info

                # Update compliance
                compliance = await self._check_project_compliance(updated_info)
                self._compliance_cache[name] = compliance

                return True

        except Exception as e:
            self.logger.error(f"Failed to refresh project {name}: {e}")

        return False

    async def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        stats = {
            "total_projects": len(self._projects),
            "by_type": {},
            "by_status": {},
            "compliance_summary": {
                "average_score": 0,
                "compliant_projects": 0,
                "non_compliant_projects": 0,
            },
        }

        # Count by type and status
        for project in self._projects.values():
            # By type
            if project.type not in stats["by_type"]:
                stats["by_type"][project.type] = 0
            stats["by_type"][project.type] += 1

            # By status
            if project.status not in stats["by_status"]:
                stats["by_status"][project.status] = 0
            stats["by_status"][project.status] += 1

        # Compliance statistics
        if self._compliance_cache:
            total_score = sum(check.score for check in self._compliance_cache.values())
            stats["compliance_summary"]["average_score"] = total_score // len(
                self._compliance_cache
            )

            for check in self._compliance_cache.values():
                if check.score >= 80:
                    stats["compliance_summary"]["compliant_projects"] += 1
                else:
                    stats["compliance_summary"]["non_compliant_projects"] += 1

        return stats
