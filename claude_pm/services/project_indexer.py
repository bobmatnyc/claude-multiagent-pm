#!/usr/bin/env python3
"""
Project Indexer Service - MEM-007 Implementation

This service scans managed projects and extracts comprehensive metadata for storage
in mem0AI, enabling instant project context retrieval and reducing credit usage.

Features:
- Scans /Users/masa/Projects/managed/ directory for projects
- Extracts metadata: tech stack, features, architecture, recent bugs
- Stores structured data in mem0AI memory system
- Provides fast retrieval with sub-second response times
- Background indexing with change detection
- Performance monitoring and cache optimization
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging_config import get_logger
from ..services.claude_pm_memory import ClaudePMMemory, MemoryCategory, create_claude_pm_memory
from ..services.memory_cache import MemoryCache, create_memory_cache

logger = get_logger(__name__)


class ProjectType(str, Enum):
    """Project type classification."""
    WEB_APP = "web_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    API_SERVICE = "api_service"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    DATA_SCIENCE = "data_science"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


class TechStack(str, Enum):
    """Common technology stacks."""
    TYPESCRIPT_NODE = "typescript_node"
    TYPESCRIPT_REACT = "typescript_react"
    TYPESCRIPT_NEXTJS = "typescript_nextjs"
    PYTHON = "python"
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_DJANGO = "python_django"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


@dataclass
class ProjectMetadata:
    """Comprehensive project metadata structure."""
    # Basic Information
    name: str
    path: str
    type: ProjectType
    tech_stack: TechStack
    description: str
    status: str = "active"
    
    # Technical Details
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    key_files: List[str] = field(default_factory=list)
    
    # Features and Architecture
    features: List[str] = field(default_factory=list)
    architecture_decisions: List[str] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    
    # Operational Data
    recent_bugs: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    deployment_info: Dict[str, Any] = field(default_factory=dict)
    
    # Development Context
    development_workflow: List[str] = field(default_factory=list)
    testing_approach: str = ""
    ci_cd_info: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    last_indexed: datetime = field(default_factory=datetime.now)
    file_count: int = 0
    size_mb: float = 0.0
    last_modified: datetime = field(default_factory=datetime.now)
    checksum: str = ""
    
    # Tags for classification
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type.value,
            "tech_stack": self.tech_stack.value,
            "description": self.description,
            "status": self.status,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "key_files": self.key_files,
            "features": self.features,
            "architecture_decisions": self.architecture_decisions,
            "design_patterns": self.design_patterns,
            "recent_bugs": self.recent_bugs,
            "performance_issues": self.performance_issues,
            "deployment_info": self.deployment_info,
            "development_workflow": self.development_workflow,
            "testing_approach": self.testing_approach,
            "ci_cd_info": self.ci_cd_info,
            "last_indexed": self.last_indexed.isoformat(),
            "file_count": self.file_count,
            "size_mb": self.size_mb,
            "last_modified": self.last_modified.isoformat(),
            "checksum": self.checksum,
            "tags": self.tags
        }


class ProjectIndexer:
    """
    Project Indexer Service for MEM-007
    
    Scans managed projects directory and extracts comprehensive metadata
    for storage in mem0AI memory system.
    """
    
    def __init__(self, managed_path: Optional[str] = None):
        """Initialize the Project Indexer."""
        self.managed_path = Path(managed_path or "/Users/masa/Projects/managed")
        self.memory: Optional[ClaudePMMemory] = None
        self.local_cache: Optional[MemoryCache] = None
        
        # Performance tracking
        self.stats = {
            "projects_scanned": 0,
            "projects_indexed": 0,
            "projects_updated": 0,
            "total_scan_time": 0.0,
            "total_index_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        # File patterns for analysis
        self.config_files = {
            "package.json": self._analyze_package_json,
            "pyproject.toml": self._analyze_pyproject_toml,
            "requirements.txt": self._analyze_requirements_txt,
            "Cargo.toml": self._analyze_cargo_toml,
            "go.mod": self._analyze_go_mod,
            "pom.xml": self._analyze_pom_xml,
            "Makefile": self._analyze_makefile,
            "Dockerfile": self._analyze_dockerfile,
            "docker-compose.yml": self._analyze_docker_compose,
            "CLAUDE.md": self._analyze_claude_md,
            "README.md": self._analyze_readme_md,
            ".gitignore": self._analyze_gitignore
        }
        
        # Content analysis patterns
        self.tech_patterns = {
            TechStack.TYPESCRIPT_NEXTJS: ["next.config", "next-env.d.ts", "pages/", "app/"],
            TechStack.TYPESCRIPT_REACT: ["react", "jsx", "tsx", "components/"],
            TechStack.TYPESCRIPT_NODE: ["typescript", "node_modules", "dist/", "src/"],
            TechStack.PYTHON_FASTAPI: ["fastapi", "uvicorn", "main.py", "routers/"],
            TechStack.PYTHON_DJANGO: ["django", "manage.py", "settings.py", "models.py"],
            TechStack.PYTHON: ["python", ".py", "requirements.txt", "pyproject.toml"],
            TechStack.RUST: ["Cargo.toml", "src/main.rs", "src/lib.rs"],
            TechStack.GO: ["go.mod", "go.sum", "main.go"],
            TechStack.JAVA: ["pom.xml", "build.gradle", ".java", "src/main/java/"]
        }
        
    async def initialize(self) -> bool:
        """Initialize the indexer with memory connection."""
        try:
            # Initialize mem0AI connection
            self.memory = create_claude_pm_memory()
            await self.memory.connect()
            
            # Initialize local cache fallback
            self.local_cache = create_memory_cache()
            
            if not self.memory.is_connected():
                logger.warning("Failed to connect to mem0AI service, using local cache only")
                logger.info("Project indexer initialized with local cache fallback")
                return True
            
            # Create project indexing memory space
            response = await self.memory.create_project_memory_space(
                project_name="project_index",
                description="Project metadata index for instant retrieval",
                metadata={
                    "indexer_version": "1.0.0",
                    "managed_path": str(self.managed_path),
                    "purpose": "project_metadata_indexing"
                }
            )
            
            if response.success:
                logger.info("Project indexer initialized successfully with mem0AI and local cache")
                return True
            else:
                logger.error(f"Failed to create project index memory space: {response.error}")
                logger.info("Continuing with local cache only")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize project indexer: {e}")
            # Try to continue with local cache only
            try:
                self.local_cache = create_memory_cache()
                logger.info("Initialized project indexer with local cache fallback only")
                return True
            except Exception as cache_error:
                logger.error(f"Failed to initialize local cache: {cache_error}")
                return False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.memory:
            await self.memory.disconnect()
    
    async def scan_and_index_all(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Scan all managed projects and index them.
        
        Args:
            force_refresh: Force re-indexing even if projects haven't changed
            
        Returns:
            Dict with scan results and statistics
        """
        start_time = time.time()
        results = {
            "scan_started": datetime.now().isoformat(),
            "projects_found": 0,
            "projects_indexed": 0,
            "projects_updated": 0,
            "projects_skipped": 0,
            "errors": [],
            "performance": {}
        }
        
        try:
            if not self.managed_path.exists():
                error_msg = f"Managed path does not exist: {self.managed_path}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results
            
            logger.info(f"Starting project scan of {self.managed_path}")
            
            # Discover all project directories
            project_dirs = [
                d for d in self.managed_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
            ]
            
            results["projects_found"] = len(project_dirs)
            logger.info(f"Found {len(project_dirs)} potential projects")
            
            # Process each project
            for project_dir in project_dirs:
                try:
                    project_result = await self._index_project(project_dir, force_refresh)
                    
                    if project_result["action"] == "indexed":
                        results["projects_indexed"] += 1
                    elif project_result["action"] == "updated":
                        results["projects_updated"] += 1
                    elif project_result["action"] == "skipped":
                        results["projects_skipped"] += 1
                    
                    if project_result.get("error"):
                        results["errors"].append(f"{project_dir.name}: {project_result['error']}")
                        
                except Exception as e:
                    error_msg = f"Error processing {project_dir.name}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    self.stats["errors"] += 1
            
            # Update statistics
            scan_time = time.time() - start_time
            self.stats["total_scan_time"] += scan_time
            
            results["performance"] = {
                "scan_time_seconds": scan_time,
                "avg_time_per_project": scan_time / max(1, len(project_dirs)),
                "projects_per_second": len(project_dirs) / scan_time if scan_time > 0 else 0
            }
            
            results["scan_completed"] = datetime.now().isoformat()
            logger.info(f"Project scan completed in {scan_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Fatal error during project scan: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            
        return results
    
    async def _index_project(self, project_dir: Path, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Index a single project directory.
        
        Args:
            project_dir: Path to project directory
            force_refresh: Force re-indexing
            
        Returns:
            Dict with indexing result
        """
        result = {
            "project": project_dir.name,
            "action": "skipped",
            "error": None,
            "metadata": None
        }
        
        try:
            # Check if project needs indexing
            if not force_refresh:
                needs_indexing = await self._project_needs_indexing(project_dir)
                if not needs_indexing:
                    result["action"] = "skipped"
                    self.stats["cache_hits"] += 1
                    return result
            
            self.stats["cache_misses"] += 1
            
            # Extract project metadata
            logger.debug(f"Extracting metadata for {project_dir.name}")
            metadata = await self._extract_project_metadata(project_dir)
            
            if not metadata:
                result["error"] = "Failed to extract metadata"
                return result
            
            # Store in memory
            success = await self._store_project_metadata(metadata)
            
            if success:
                result["action"] = "indexed"
                result["metadata"] = metadata.to_dict()
                self.stats["projects_indexed"] += 1
                logger.info(f"Successfully indexed project: {project_dir.name}")
            else:
                result["error"] = "Failed to store metadata in memory"
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error indexing project {project_dir.name}: {e}")
            
        return result
    
    async def _project_needs_indexing(self, project_dir: Path) -> bool:
        """
        Check if a project needs re-indexing based on modification time.
        
        Args:
            project_dir: Project directory path
            
        Returns:
            True if project needs indexing
        """
        try:
            # Check if we have existing metadata
            existing_metadata = await self._get_existing_metadata(project_dir.name)
            
            if not existing_metadata:
                return True
            
            # Check if project files have been modified
            last_indexed = datetime.fromisoformat(existing_metadata.get("last_indexed", "1900-01-01"))
            project_modified = self._get_project_last_modified(project_dir)
            
            # Re-index if project was modified after last indexing
            return project_modified > last_indexed
            
        except Exception as e:
            logger.debug(f"Error checking indexing need for {project_dir.name}: {e}")
            return True  # Default to indexing on error
    
    async def _get_existing_metadata(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get existing project metadata from memory."""
        try:
            if not self.memory:
                return None
            
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query=f"project_metadata {project_name}",
                project_filter="project_index",
                limit=1
            )
            
            if response.success and response.data and response.data.get("memories"):
                memory = response.data["memories"][0]
                metadata = memory.get("metadata", {})
                return metadata.get("project_data")
            
        except Exception as e:
            logger.debug(f"Error retrieving existing metadata for {project_name}: {e}")
            
        return None
    
    def _get_project_last_modified(self, project_dir: Path) -> datetime:
        """Get the last modification time of a project."""
        try:
            # Check modification times of key files
            key_files = ["CLAUDE.md", "package.json", "pyproject.toml", "README.md"]
            latest_time = datetime.fromtimestamp(project_dir.stat().st_mtime)
            
            for file_name in key_files:
                file_path = project_dir / file_name
                if file_path.exists():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time > latest_time:
                        latest_time = file_time
            
            return latest_time
            
        except Exception:
            return datetime.now()
    
    async def _extract_project_metadata(self, project_dir: Path) -> Optional[ProjectMetadata]:
        """
        Extract comprehensive metadata from a project directory.
        
        Args:
            project_dir: Project directory path
            
        Returns:
            ProjectMetadata object or None
        """
        try:
            metadata = ProjectMetadata(
                name=project_dir.name,
                path=str(project_dir),
                type=ProjectType.UNKNOWN,
                tech_stack=TechStack.UNKNOWN,
                description="",
                last_modified=self._get_project_last_modified(project_dir)
            )
            
            # Calculate project size and file count
            metadata.file_count, metadata.size_mb = self._calculate_project_size(project_dir)
            
            # Analyze configuration files
            await self._analyze_config_files(project_dir, metadata)
            
            # Detect tech stack and project type
            self._detect_tech_stack(project_dir, metadata)
            self._detect_project_type(project_dir, metadata)
            
            # Extract features and architecture decisions
            await self._extract_features(project_dir, metadata)
            await self._extract_architecture_decisions(project_dir, metadata)
            
            # Analyze development workflow
            await self._analyze_development_workflow(project_dir, metadata)
            
            # Generate checksum for change detection
            metadata.checksum = self._calculate_project_checksum(project_dir)
            
            # Generate tags
            self._generate_tags(metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {project_dir.name}: {e}")
            return None
    
    def _calculate_project_size(self, project_dir: Path) -> Tuple[int, float]:
        """Calculate project file count and size."""
        try:
            file_count = 0
            total_size = 0
            
            # Skip common ignore patterns
            ignore_patterns = {
                "node_modules", ".git", "__pycache__", ".venv", "venv", 
                "dist", "build", "target", ".next", "coverage"
            }
            
            for item in project_dir.rglob("*"):
                # Skip if any parent directory is in ignore patterns
                if any(part in ignore_patterns for part in item.parts):
                    continue
                    
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
            
            size_mb = total_size / (1024 * 1024)
            return file_count, size_mb
            
        except Exception:
            return 0, 0.0
    
    async def _analyze_config_files(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Analyze configuration files to extract metadata."""
        for file_name, analyzer in self.config_files.items():
            file_path = project_dir / file_name
            if file_path.exists():
                try:
                    await analyzer(file_path, metadata)
                    metadata.key_files.append(file_name)
                except Exception as e:
                    logger.debug(f"Error analyzing {file_name} in {project_dir.name}: {e}")
    
    async def _analyze_package_json(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze package.json file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract basic info
            if not metadata.description and data.get("description"):
                metadata.description = data["description"]
            
            # Extract dependencies
            deps = list(data.get("dependencies", {}).keys())
            dev_deps = list(data.get("devDependencies", {}).keys())
            metadata.dependencies.extend(deps + dev_deps)
            
            # Extract scripts for workflow analysis
            scripts = data.get("scripts", {})
            metadata.development_workflow.extend([
                f"npm run {script}" for script in scripts.keys()
            ])
            
            # Detect frameworks
            if "next" in deps:
                metadata.frameworks.append("Next.js")
            if "react" in deps:
                metadata.frameworks.append("React")
            if "typescript" in dev_deps:
                metadata.languages.append("TypeScript")
            if "express" in deps:
                metadata.frameworks.append("Express")
            
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
    
    async def _analyze_pyproject_toml(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze pyproject.toml file."""
        try:
            import tomli
            
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
            
            project_info = data.get("project", {})
            
            # Extract basic info
            if not metadata.description and project_info.get("description"):
                metadata.description = project_info["description"]
            
            # Extract dependencies
            deps = project_info.get("dependencies", [])
            metadata.dependencies.extend(deps)
            
            # Extract optional dependencies
            optional_deps = project_info.get("optional-dependencies", {})
            for group_deps in optional_deps.values():
                metadata.dependencies.extend(group_deps)
            
            # Detect frameworks
            deps_str = " ".join(deps)
            if "fastapi" in deps_str:
                metadata.frameworks.append("FastAPI")
            if "django" in deps_str:
                metadata.frameworks.append("Django")
            if "flask" in deps_str:
                metadata.frameworks.append("Flask")
            
            metadata.languages.append("Python")
            
        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml: {e}")
    
    async def _analyze_requirements_txt(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze requirements.txt file."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before any version specifiers)
                    pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                    deps.append(pkg_name)
            
            metadata.dependencies.extend(deps)
            metadata.languages.append("Python")
            
        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")
    
    async def _analyze_cargo_toml(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze Cargo.toml file."""
        try:
            import tomli
            
            with open(file_path, 'rb') as f:
                data = tomli.load(f)
            
            package_info = data.get("package", {})
            
            if not metadata.description and package_info.get("description"):
                metadata.description = package_info["description"]
            
            # Extract dependencies
            deps = list(data.get("dependencies", {}).keys())
            metadata.dependencies.extend(deps)
            
            metadata.languages.append("Rust")
            
        except Exception as e:
            logger.debug(f"Error parsing Cargo.toml: {e}")
    
    async def _analyze_go_mod(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze go.mod file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract module name and dependencies
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('module '):
                    module_name = line.replace('module ', '')
                    if not metadata.description:
                        metadata.description = f"Go module: {module_name}"
                elif line and not line.startswith('//') and '/' in line:
                    # Likely a dependency
                    dep = line.split()[0]
                    if dep not in ['module', 'go', 'require', ')']:
                        metadata.dependencies.append(dep)
            
            metadata.languages.append("Go")
            
        except Exception as e:
            logger.debug(f"Error parsing go.mod: {e}")
    
    async def _analyze_pom_xml(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze pom.xml file."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract project info (handling XML namespaces)
            for desc in root.iter():
                if desc.tag.endswith('description') and desc.text:
                    if not metadata.description:
                        metadata.description = desc.text
                    break
            
            # Extract dependencies
            for dep in root.iter():
                if dep.tag.endswith('artifactId') and dep.text:
                    metadata.dependencies.append(dep.text)
            
            metadata.languages.append("Java")
            
        except Exception as e:
            logger.debug(f"Error parsing pom.xml: {e}")
    
    async def _analyze_makefile(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze Makefile."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract make targets
            lines = content.split('\n')
            targets = []
            for line in lines:
                if ':' in line and not line.startswith('\t') and not line.startswith('#'):
                    target = line.split(':')[0].strip()
                    if target and not target.startswith('.'):
                        targets.append(f"make {target}")
            
            metadata.development_workflow.extend(targets)
            
        except Exception as e:
            logger.debug(f"Error parsing Makefile: {e}")
    
    async def _analyze_dockerfile(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze Dockerfile."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract base image and key info
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('FROM '):
                    base_image = line.replace('FROM ', '').split(':')[0]
                    metadata.deployment_info["base_image"] = base_image
                    metadata.deployment_info["containerized"] = True
                    break
            
            metadata.deployment_info["docker"] = True
            
        except Exception as e:
            logger.debug(f"Error parsing Dockerfile: {e}")
    
    async def _analyze_docker_compose(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze docker-compose.yml."""
        try:
            import yaml
            
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            services = data.get("services", {})
            metadata.deployment_info["services"] = list(services.keys())
            metadata.deployment_info["docker_compose"] = True
            
        except Exception as e:
            logger.debug(f"Error parsing docker-compose.yml: {e}")
    
    async def _analyze_claude_md(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze CLAUDE.md file for project insights."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract project overview
            lines = content.split('\n')
            in_overview = False
            overview_text = []
            
            for line in lines:
                if '## Project Overview' in line:
                    in_overview = True
                    continue
                elif line.startswith('##') and in_overview:
                    break
                elif in_overview and line.strip():
                    overview_text.append(line.strip())
            
            if overview_text and not metadata.description:
                metadata.description = ' '.join(overview_text[:2])  # First 2 sentences
            
            # Extract features, architecture decisions, etc.
            self._extract_from_markdown_content(content, metadata)
            
        except Exception as e:
            logger.debug(f"Error parsing CLAUDE.md: {e}")
    
    async def _analyze_readme_md(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze README.md file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract description from README if not already set
            if not metadata.description:
                lines = content.split('\n')
                for line in lines[1:10]:  # Check first 10 lines
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 20:
                        metadata.description = line
                        break
            
            self._extract_from_markdown_content(content, metadata)
            
        except Exception as e:
            logger.debug(f"Error parsing README.md: {e}")
    
    async def _analyze_gitignore(self, file_path: Path, metadata: ProjectMetadata) -> None:
        """Analyze .gitignore for tech stack hints."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Tech stack indicators
            if 'node_modules' in content:
                metadata.languages.append("JavaScript/TypeScript")
            if '__pycache__' in content or '*.pyc' in content:
                metadata.languages.append("Python")
            if 'target/' in content:
                metadata.languages.append("Rust")
            if '*.class' in content:
                metadata.languages.append("Java")
            
        except Exception as e:
            logger.debug(f"Error parsing .gitignore: {e}")
    
    def _extract_from_markdown_content(self, content: str, metadata: ProjectMetadata) -> None:
        """Extract information from markdown content."""
        content_lower = content.lower()
        
        # Extract features
        if 'features' in content_lower:
            # Simple feature extraction
            lines = content.split('\n')
            in_features = False
            for line in lines:
                if 'feature' in line.lower() and ('##' in line or '*' in line):
                    in_features = True
                elif in_features and line.strip().startswith('-'):
                    feature = line.strip('- ').strip()
                    if feature and len(feature) < 100:
                        metadata.features.append(feature)
                elif in_features and line.startswith('#'):
                    break
        
        # Extract architecture decisions
        if 'architecture' in content_lower or 'decision' in content_lower:
            lines = content.split('\n')
            for line in lines:
                if ('architecture' in line.lower() or 'decision' in line.lower()) and len(line) < 200:
                    metadata.architecture_decisions.append(line.strip())
    
    def _detect_tech_stack(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Detect technology stack based on files and dependencies."""
        # Check for specific file patterns
        for tech_stack, patterns in self.tech_patterns.items():
            matches = 0
            for pattern in patterns:
                if pattern.endswith('/'):
                    # Directory pattern
                    if (project_dir / pattern.rstrip('/')).exists():
                        matches += 1
                else:
                    # File pattern
                    if list(project_dir.glob(f"**/{pattern}")):
                        matches += 1
            
            # If we match most patterns, assign this tech stack
            if matches >= len(patterns) // 2:
                metadata.tech_stack = tech_stack
                break
        
        # Refine based on dependencies
        deps_str = ' '.join(metadata.dependencies).lower()
        
        if 'next' in deps_str and metadata.tech_stack == TechStack.TYPESCRIPT_REACT:
            metadata.tech_stack = TechStack.TYPESCRIPT_NEXTJS
        elif 'fastapi' in deps_str:
            metadata.tech_stack = TechStack.PYTHON_FASTAPI
        elif 'django' in deps_str:
            metadata.tech_stack = TechStack.PYTHON_DJANGO
    
    def _detect_project_type(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Detect project type based on structure and metadata."""
        # Check for specific indicators
        if (project_dir / "bin").exists() or any("cli" in dep for dep in metadata.dependencies):
            metadata.type = ProjectType.CLI_TOOL
        elif (project_dir / "src" / "pages").exists() or (project_dir / "app").exists():
            metadata.type = ProjectType.WEB_APP
        elif "fastapi" in metadata.dependencies or "django" in metadata.dependencies:
            metadata.type = ProjectType.API_SERVICE
        elif (project_dir / "docs").exists() and len(list(project_dir.glob("**/*.md"))) > 5:
            metadata.type = ProjectType.DOCUMENTATION
        elif any("lib" in str(f) for f in project_dir.iterdir() if f.is_dir()):
            metadata.type = ProjectType.LIBRARY
        elif "next" in metadata.dependencies:
            metadata.type = ProjectType.WEB_APP
        else:
            # Default based on tech stack
            if metadata.tech_stack in [TechStack.TYPESCRIPT_NEXTJS, TechStack.TYPESCRIPT_REACT]:
                metadata.type = ProjectType.WEB_APP
            elif metadata.tech_stack in [TechStack.PYTHON_FASTAPI, TechStack.PYTHON_DJANGO]:
                metadata.type = ProjectType.API_SERVICE
    
    async def _extract_features(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Extract project features from various sources."""
        # Check common feature indicators
        if (project_dir / "components").exists():
            metadata.features.append("Component-based architecture")
        if (project_dir / "api").exists():
            metadata.features.append("API endpoints")
        if (project_dir / "tests").exists() or (project_dir / "test").exists():
            metadata.features.append("Test suite")
        if any("docker" in f.name.lower() for f in project_dir.iterdir()):
            metadata.features.append("Containerization")
        if (project_dir / ".github").exists():
            metadata.features.append("GitHub Actions CI/CD")
        
        # Check dependencies for features
        deps_str = ' '.join(metadata.dependencies).lower()
        if "auth" in deps_str:
            metadata.features.append("Authentication")
        if "database" in deps_str or "postgres" in deps_str or "mysql" in deps_str:
            metadata.features.append("Database integration")
        if "redis" in deps_str:
            metadata.features.append("Caching")
        if "websocket" in deps_str:
            metadata.features.append("Real-time communication")
    
    async def _extract_architecture_decisions(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Extract architecture decisions from documentation."""
        # Check for architecture documentation
        arch_files = list(project_dir.glob("**/ARCHITECTURE*.md")) + \
                    list(project_dir.glob("**/architecture*.md")) + \
                    list(project_dir.glob("**/ADR*.md"))
        
        for arch_file in arch_files:
            try:
                with open(arch_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract decision summaries
                lines = content.split('\n')
                for line in lines:
                    if ('decision' in line.lower() or 'choose' in line.lower()) and len(line) < 150:
                        metadata.architecture_decisions.append(line.strip())
                        
            except Exception:
                continue
    
    async def _analyze_development_workflow(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Analyze development workflow and testing approach."""
        # Check for CI/CD files
        if (project_dir / ".github" / "workflows").exists():
            metadata.ci_cd_info["platform"] = "GitHub Actions"
            workflow_files = list((project_dir / ".github" / "workflows").glob("*.yml"))
            metadata.ci_cd_info["workflows"] = [f.stem for f in workflow_files]
        
        # Check for testing setup
        test_dirs = ["tests", "test", "__tests__", "spec"]
        test_files = []
        for test_dir in test_dirs:
            test_path = project_dir / test_dir
            if test_path.exists():
                test_files.extend(list(test_path.glob("**/*test*")))
                test_files.extend(list(test_path.glob("**/*spec*")))
        
        if test_files:
            metadata.testing_approach = f"Comprehensive testing with {len(test_files)} test files"
        elif any("test" in dep for dep in metadata.dependencies):
            metadata.testing_approach = "Testing framework configured"
        else:
            metadata.testing_approach = "No explicit testing setup"
    
    def _calculate_project_checksum(self, project_dir: Path) -> str:
        """Calculate a checksum for the project to detect changes."""
        try:
            # Use key files for checksum calculation
            key_files = ["CLAUDE.md", "package.json", "pyproject.toml", "README.md", "Makefile"]
            content_pieces = []
            
            for file_name in key_files:
                file_path = project_dir / file_name
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content_pieces.append(f.read()[:1000])  # First 1000 chars
                    except Exception:
                        continue
            
            # Include directory structure
            dirs = [d.name for d in project_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            content_pieces.append(','.join(sorted(dirs)))
            
            # Calculate hash
            content = '\n'.join(content_pieces)
            return hashlib.md5(content.encode('utf-8')).hexdigest()
            
        except Exception:
            return ""
    
    def _generate_tags(self, metadata: ProjectMetadata) -> None:
        """Generate tags for project categorization."""
        tags = set()
        
        # Type and tech stack tags
        tags.add(metadata.type.value)
        tags.add(metadata.tech_stack.value)
        
        # Language tags
        for lang in metadata.languages:
            tags.add(lang.lower().replace('/', '_'))
        
        # Framework tags
        for framework in metadata.frameworks:
            tags.add(framework.lower().replace('.', '').replace(' ', '_'))
        
        # Feature tags
        for feature in metadata.features:
            if len(feature) < 30:  # Only short feature names
                tags.add(feature.lower().replace(' ', '_'))
        
        # Size tags
        if metadata.size_mb > 100:
            tags.add("large_project")
        elif metadata.size_mb > 10:
            tags.add("medium_project")
        else:
            tags.add("small_project")
        
        # Status tags
        tags.add(metadata.status)
        
        metadata.tags = list(tags)
    
    async def _store_project_metadata(self, metadata: ProjectMetadata) -> bool:
        """Store project metadata in mem0AI memory and local cache."""
        try:
            # Create memory content
            content = f"""
Project: {metadata.name}
Type: {metadata.type.value}
Tech Stack: {metadata.tech_stack.value}
Description: {metadata.description}

Languages: {', '.join(metadata.languages)}
Frameworks: {', '.join(metadata.frameworks)}
Key Features: {', '.join(metadata.features[:5])}  # Top 5 features

Architecture Decisions:
{chr(10).join(f"- {decision}" for decision in metadata.architecture_decisions[:3])}

Development Workflow:
{chr(10).join(f"- {workflow}" for workflow in metadata.development_workflow[:5])}

Deployment: {metadata.deployment_info}
Testing: {metadata.testing_approach}

Project Size: {metadata.file_count} files, {metadata.size_mb:.1f} MB
Last Modified: {metadata.last_modified.strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

            # Prepare metadata
            store_metadata = {
                "project_name": metadata.name,
                "project_type": metadata.type.value,
                "tech_stack": metadata.tech_stack.value,
                "project_data": metadata.to_dict(),
                "indexed_at": datetime.now().isoformat(),
                "indexer_version": "1.0.0"
            }
            
            tags = ["project_metadata", "indexed_project"] + metadata.tags
            
            mem0ai_success = False
            local_cache_success = False
            
            # Try to store in mem0AI
            if self.memory and self.memory.is_connected():
                try:
                    response = await self.memory.store_memory(
                        category=MemoryCategory.PROJECT,
                        content=content,
                        metadata=store_metadata,
                        project_name="project_index",
                        tags=tags
                    )
                    
                    if response.success:
                        mem0ai_success = True
                        logger.debug(f"Stored {metadata.name} in mem0AI")
                    else:
                        logger.warning(f"Failed to store {metadata.name} in mem0AI: {response.error}")
                except Exception as e:
                    logger.warning(f"mem0AI storage failed for {metadata.name}: {e}")
            
            # Always try to store in local cache as backup
            if self.local_cache:
                try:
                    local_cache_success = await self.local_cache.store_project_memory(
                        project_name=metadata.name,
                        content=content,
                        metadata=store_metadata,
                        category="project",
                        tags=tags
                    )
                    
                    if local_cache_success:
                        logger.debug(f"Stored {metadata.name} in local cache")
                    else:
                        logger.warning(f"Failed to store {metadata.name} in local cache")
                except Exception as e:
                    logger.warning(f"Local cache storage failed for {metadata.name}: {e}")
            
            # Consider success if either storage method worked
            if mem0ai_success or local_cache_success:
                logger.debug(f"Successfully stored metadata for project: {metadata.name}")
                return True
            else:
                logger.error(f"Failed to store metadata in both mem0AI and local cache for {metadata.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing metadata for {metadata.name}: {e}")
            return False
    
    async def get_project_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive project information by name.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict with project information or None
        """
        try:
            if not self.memory:
                return None
            
            # Search for project metadata
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query=f"project_metadata {project_name}",
                project_filter="project_index",
                tags=["project_metadata"],
                limit=1
            )
            
            if response.success and response.data and response.data.get("memories"):
                memory = response.data["memories"][0]
                metadata = memory.get("metadata", {})
                project_data = metadata.get("project_data")
                
                if project_data:
                    # Add retrieval metadata
                    project_data["retrieved_at"] = datetime.now().isoformat()
                    project_data["memory_id"] = memory.get("id")
                    return project_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving project info for {project_name}: {e}")
            return None
    
    async def search_projects(self, query: str, project_type: Optional[str] = None,
                            tech_stack: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search projects based on query and filters.
        
        Args:
            query: Search query
            project_type: Filter by project type
            tech_stack: Filter by tech stack
            limit: Maximum results
            
        Returns:
            List of matching projects
        """
        try:
            if not self.memory:
                return []
            
            # Build search tags
            search_tags = ["project_metadata"]
            if project_type:
                search_tags.append(project_type)
            if tech_stack:
                search_tags.append(tech_stack)
            
            # Search memories
            response = await self.memory.retrieve_memories(
                category=MemoryCategory.PROJECT,
                query=query,
                project_filter="project_index",
                tags=search_tags,
                limit=limit
            )
            
            if response.success and response.data and response.data.get("memories"):
                projects = []
                for memory in response.data["memories"]:
                    metadata = memory.get("metadata", {})
                    project_data = metadata.get("project_data")
                    if project_data:
                        projects.append(project_data)
                
                return projects
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []
    
    def get_indexer_statistics(self) -> Dict[str, Any]:
        """Get indexer performance statistics."""
        return {
            **self.stats,
            "managed_path": str(self.managed_path),
            "memory_connected": self.memory.is_connected() if self.memory else False,
            "cache_hit_rate": (self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])) * 100,
            "success_rate": (self.stats["projects_indexed"] / max(1, self.stats["projects_scanned"])) * 100 if self.stats["projects_scanned"] > 0 else 0,
            "avg_index_time": self.stats["total_index_time"] / max(1, self.stats["projects_indexed"]) if self.stats["projects_indexed"] > 0 else 0
        }


# Factory function
def create_project_indexer(managed_path: Optional[str] = None) -> ProjectIndexer:
    """Create a project indexer instance."""
    return ProjectIndexer(managed_path)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of ProjectIndexer."""
        print("🔍 Project Indexer Example Usage")
        
        indexer = create_project_indexer()
        
        try:
            # Initialize
            if not await indexer.initialize():
                print("❌ Failed to initialize indexer")
                return
            
            print("✅ Indexer initialized")
            
            # Scan and index all projects
            results = await indexer.scan_and_index_all()
            print(f"📊 Scan Results: {results['projects_found']} found, {results['projects_indexed']} indexed")
            
            # Get project info
            project_info = await indexer.get_project_info("ai-code-review")
            if project_info:
                print(f"📋 Project Info: {project_info['name']} - {project_info['description'][:100]}...")
            
            # Search projects
            projects = await indexer.search_projects("typescript", limit=5)
            print(f"🔍 Found {len(projects)} TypeScript projects")
            
            # Get statistics
            stats = indexer.get_indexer_statistics()
            print(f"📈 Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
            
        finally:
            await indexer.cleanup()
        
        print("✅ Example completed!")
    
    # Run example
    asyncio.run(example_usage())