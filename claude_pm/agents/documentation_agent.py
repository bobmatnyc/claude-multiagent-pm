"""
Documentation Agent - Project Pattern Scanning and Documentation Maintenance

This agent specializes in:
1. Scanning project documentation patterns on initialization
2. Understanding operational patterns from existing documentation
3. Maintaining operational documentation
4. Collaborating hand-in-hand with PM for documentation needs
5. Core agent functionality for documentation management
"""

import os
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field

from ..core.base_agent import BaseAgent
from ..core.config import Config
from ..services.memory.memory_trigger_service import MemoryTriggerService
from ..services.memory.trigger_orchestrator import TriggerEvent
from ..services.memory.trigger_types import TriggerType, TriggerPriority
from ..services.memory.interfaces.models import MemoryCategory
from .memory_enhanced_agents import MemoryEnhancedAgent


@dataclass
class DocumentationPattern:
    """Represents a discovered documentation pattern."""

    file_path: str
    file_type: str
    pattern_type: str
    content_summary: str
    last_modified: datetime
    size_bytes: int
    sections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.0


@dataclass
class ProjectDocumentationProfile:
    """Comprehensive project documentation profile."""

    project_root: str
    scan_timestamp: datetime
    documentation_patterns: List[DocumentationPattern] = field(default_factory=list)
    operational_patterns: Dict[str, Any] = field(default_factory=dict)
    documentation_health: Dict[str, Any] = field(default_factory=dict)
    maintenance_recommendations: List[str] = field(default_factory=list)
    missing_documentation: List[str] = field(default_factory=list)


class DocumentationPatternScanner:
    """Scanner for project documentation patterns."""

    def __init__(self, logger):
        self.logger = logger
        self.documentation_patterns = {
            "README.md": {"type": "overview", "importance": 10, "required": True},
            "CLAUDE.md": {"type": "ai_instructions", "importance": 9, "required": True},
            "WORKFLOW.md": {"type": "process", "importance": 8, "required": False},
            "INSTRUCTIONS.md": {"type": "guidance", "importance": 7, "required": False},
            "TOOLCHAIN.md": {"type": "technical", "importance": 6, "required": False},
            "CHANGELOG.md": {"type": "history", "importance": 8, "required": True},
            "CONTRIBUTING.md": {"type": "community", "importance": 5, "required": False},
            "DEPLOYMENT.md": {"type": "operations", "importance": 7, "required": False},
            "ARCHITECTURE.md": {"type": "technical", "importance": 6, "required": False},
            "API.md": {"type": "technical", "importance": 6, "required": False},
            "TROUBLESHOOTING.md": {"type": "support", "importance": 5, "required": False},
            "FAQ.md": {"type": "support", "importance": 4, "required": False},
        }

    async def scan_project(self, project_root: str) -> ProjectDocumentationProfile:
        """
        Scan project for documentation patterns.

        Args:
            project_root: Root directory of the project

        Returns:
            Comprehensive documentation profile
        """
        self.logger.info(f"Scanning project documentation patterns in: {project_root}")

        project_path = Path(project_root)
        if not project_path.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        # Scan for documentation files
        documentation_patterns = await self._scan_documentation_files(project_path)

        # Analyze operational patterns
        operational_patterns = await self._analyze_operational_patterns(documentation_patterns)

        # Assess documentation health
        documentation_health = await self._assess_documentation_health(
            documentation_patterns, project_path
        )

        # Generate maintenance recommendations
        maintenance_recommendations = await self._generate_maintenance_recommendations(
            documentation_patterns, documentation_health
        )

        # Identify missing documentation
        missing_documentation = await self._identify_missing_documentation(
            documentation_patterns, project_path
        )

        profile = ProjectDocumentationProfile(
            project_root=str(project_path.absolute()),
            scan_timestamp=datetime.now(),
            documentation_patterns=documentation_patterns,
            operational_patterns=operational_patterns,
            documentation_health=documentation_health,
            maintenance_recommendations=maintenance_recommendations,
            missing_documentation=missing_documentation,
        )

        self.logger.info(
            f"Documentation scan complete. Found {len(documentation_patterns)} patterns"
        )
        return profile

    async def _scan_documentation_files(self, project_path: Path) -> List[DocumentationPattern]:
        """Scan for documentation files and analyze patterns."""
        patterns = []

        # Scan known documentation patterns
        for file_name, pattern_info in self.documentation_patterns.items():
            file_path = project_path / file_name
            if file_path.exists():
                pattern = await self._analyze_documentation_file(file_path, pattern_info)
                patterns.append(pattern)

        # Scan docs/ directory if exists
        docs_dir = project_path / "docs"
        if docs_dir.exists() and docs_dir.is_dir():
            for doc_file in docs_dir.rglob("*.md"):
                if doc_file.is_file():
                    pattern = await self._analyze_documentation_file(
                        doc_file, {"type": "supplementary", "importance": 4}
                    )
                    patterns.append(pattern)

        # Scan for other markdown files in root
        for md_file in project_path.glob("*.md"):
            if md_file.is_file() and md_file.name not in self.documentation_patterns:
                pattern = await self._analyze_documentation_file(
                    md_file, {"type": "additional", "importance": 3}
                )
                patterns.append(pattern)

        return patterns

    async def _analyze_documentation_file(
        self, file_path: Path, pattern_info: Dict[str, Any]
    ) -> DocumentationPattern:
        """Analyze a single documentation file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract sections from markdown
            sections = self._extract_markdown_sections(content)

            # Generate content summary
            content_summary = self._generate_content_summary(content)

            # Extract metadata
            metadata = self._extract_file_metadata(content, file_path)

            pattern = DocumentationPattern(
                file_path=str(file_path.relative_to(file_path.parent.parent)),
                file_type=pattern_info.get("type", "unknown"),
                pattern_type="documentation",
                content_summary=content_summary,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                size_bytes=file_path.stat().st_size,
                sections=sections,
                metadata=metadata,
                importance_score=pattern_info.get("importance", 1),
            )

            return pattern

        except Exception as e:
            self.logger.error(f"Error analyzing documentation file {file_path}: {e}")
            return DocumentationPattern(
                file_path=str(file_path),
                file_type=pattern_info.get("type", "unknown"),
                pattern_type="documentation",
                content_summary="Error reading file",
                last_modified=datetime.now(),
                size_bytes=0,
                importance_score=0,
            )

    def _extract_markdown_sections(self, content: str) -> List[str]:
        """Extract section headers from markdown content."""
        sections = []
        lines = content.split("\n")

        for line in lines:
            if line.startswith("#"):
                # Remove markdown header syntax and clean up
                section = re.sub(r"^#+\s*", "", line).strip()
                if section:
                    sections.append(section)

        return sections

    def _generate_content_summary(self, content: str) -> str:
        """Generate a brief summary of the content."""
        lines = content.strip().split("\n")

        # Find first substantial paragraph
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 20:
                # Return first 150 characters
                return line[:150] + "..." if len(line) > 150 else line

        return "No content summary available"

    def _extract_file_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file content."""
        metadata = {}

        # Look for YAML frontmatter
        if content.startswith("---"):
            try:
                import yaml

                frontmatter_end = content.find("---", 3)
                if frontmatter_end != -1:
                    frontmatter = content[3:frontmatter_end]
                    metadata["frontmatter"] = yaml.safe_load(frontmatter)
            except ImportError:
                pass

        # Extract other patterns
        metadata["word_count"] = len(content.split())
        metadata["line_count"] = len(content.split("\n"))
        metadata["has_code_blocks"] = "```" in content
        metadata["has_links"] = bool(re.search(r"\[.*?\]\(.*?\)", content))
        metadata["has_images"] = bool(re.search(r"!\[.*?\]\(.*?\)", content))

        return metadata

    async def _analyze_operational_patterns(
        self, patterns: List[DocumentationPattern]
    ) -> Dict[str, Any]:
        """Analyze operational patterns from documentation."""
        operational_patterns = {
            "project_structure": {},
            "workflows": [],
            "tools_and_technologies": [],
            "deployment_info": {},
            "development_practices": [],
            "communication_patterns": [],
        }

        for pattern in patterns:
            if pattern.file_type == "ai_instructions":
                # Extract AI/PM patterns from CLAUDE.md
                operational_patterns["communication_patterns"].extend(
                    self._extract_ai_patterns(pattern)
                )
            elif pattern.file_type == "process":
                # Extract workflow patterns
                operational_patterns["workflows"].extend(self._extract_workflow_patterns(pattern))
            elif pattern.file_type == "technical":
                # Extract technical patterns
                operational_patterns["tools_and_technologies"].extend(
                    self._extract_technical_patterns(pattern)
                )
            elif pattern.file_type == "operations":
                # Extract deployment patterns
                operational_patterns["deployment_info"].update(
                    self._extract_deployment_patterns(pattern)
                )

        return operational_patterns

    def _extract_ai_patterns(self, pattern: DocumentationPattern) -> List[str]:
        """Extract AI/PM communication patterns."""
        patterns_found = []
        sections = pattern.sections

        for section in sections:
            if any(
                keyword in section.lower()
                for keyword in ["role", "responsibilities", "workflow", "delegation", "orchestrat"]
            ):
                patterns_found.append(f"AI Pattern: {section}")

        return patterns_found

    def _extract_workflow_patterns(self, pattern: DocumentationPattern) -> List[str]:
        """Extract workflow patterns."""
        patterns_found = []
        sections = pattern.sections

        for section in sections:
            if any(
                keyword in section.lower()
                for keyword in ["process", "workflow", "step", "procedure", "guide"]
            ):
                patterns_found.append(f"Workflow: {section}")

        return patterns_found

    def _extract_technical_patterns(self, pattern: DocumentationPattern) -> List[str]:
        """Extract technical patterns."""
        patterns_found = []
        sections = pattern.sections

        for section in sections:
            if any(
                keyword in section.lower()
                for keyword in ["tech", "tool", "stack", "framework", "library", "dependency"]
            ):
                patterns_found.append(f"Technical: {section}")

        return patterns_found

    def _extract_deployment_patterns(self, pattern: DocumentationPattern) -> Dict[str, Any]:
        """Extract deployment patterns."""
        deployment_info = {}
        sections = pattern.sections

        for section in sections:
            if any(
                keyword in section.lower()
                for keyword in ["deploy", "production", "environment", "config", "setup"]
            ):
                deployment_info[section.lower().replace(" ", "_")] = section

        return deployment_info

    async def _assess_documentation_health(
        self, patterns: List[DocumentationPattern], project_path: Path
    ) -> Dict[str, Any]:
        """Assess overall documentation health."""
        health = {"score": 0.0, "coverage": {}, "quality": {}, "freshness": {}, "completeness": {}}

        # Coverage assessment
        required_docs = [
            name
            for name, info in self.documentation_patterns.items()
            if info.get("required", False)
        ]
        found_required = [p.file_path for p in patterns if Path(p.file_path).name in required_docs]

        health["coverage"]["required_coverage"] = len(found_required) / len(required_docs)
        health["coverage"]["total_patterns"] = len(patterns)
        health["coverage"]["missing_required"] = [
            doc for doc in required_docs if not any(Path(p.file_path).name == doc for p in patterns)
        ]

        # Quality assessment
        total_importance = sum(p.importance_score for p in patterns)
        avg_size = sum(p.size_bytes for p in patterns) / len(patterns) if patterns else 0

        health["quality"]["total_importance"] = total_importance
        health["quality"]["average_size"] = avg_size
        health["quality"]["has_substantial_content"] = avg_size > 500

        # Freshness assessment
        if patterns:
            most_recent = max(p.last_modified for p in patterns)
            oldest = min(p.last_modified for p in patterns)
            avg_age = (datetime.now() - oldest).days

            health["freshness"]["most_recent"] = most_recent.isoformat()
            health["freshness"]["oldest"] = oldest.isoformat()
            health["freshness"]["average_age_days"] = avg_age
            health["freshness"]["is_fresh"] = avg_age < 30

        # Calculate overall score
        coverage_score = health["coverage"]["required_coverage"] * 40
        quality_score = min(total_importance / 50, 1.0) * 30
        freshness_score = (1.0 if health["freshness"].get("is_fresh", False) else 0.5) * 30

        health["score"] = coverage_score + quality_score + freshness_score

        return health

    async def _generate_maintenance_recommendations(
        self, patterns: List[DocumentationPattern], health: Dict[str, Any]
    ) -> List[str]:
        """Generate documentation maintenance recommendations."""
        recommendations = []

        # Coverage recommendations
        if health["coverage"]["required_coverage"] < 1.0:
            missing = health["coverage"]["missing_required"]
            recommendations.append(f"Create missing required documentation: {', '.join(missing)}")

        # Quality recommendations
        small_files = [p for p in patterns if p.size_bytes < 200]
        if small_files:
            recommendations.append(
                f"Expand content in small documentation files: {', '.join(Path(p.file_path).name for p in small_files)}"
            )

        # Freshness recommendations
        if not health["freshness"].get("is_fresh", True):
            recommendations.append("Update outdated documentation files")

        # Structure recommendations
        if not any(p.file_type == "overview" for p in patterns):
            recommendations.append("Add project overview documentation (README.md)")

        if not any(p.file_type == "ai_instructions" for p in patterns):
            recommendations.append("Add AI instructions documentation (CLAUDE.md)")

        return recommendations

    async def _identify_missing_documentation(
        self, patterns: List[DocumentationPattern], project_path: Path
    ) -> List[str]:
        """Identify missing documentation based on project structure."""
        missing = []
        existing_files = {Path(p.file_path).name for p in patterns}

        # Check for standard documentation
        for doc_name, doc_info in self.documentation_patterns.items():
            if doc_name not in existing_files:
                if doc_info.get("required", False):
                    missing.append(f"Required: {doc_name}")
                else:
                    missing.append(f"Recommended: {doc_name}")

        # Check for project-specific documentation needs
        if (project_path / "src").exists() or (project_path / "lib").exists():
            if "API.md" not in existing_files:
                missing.append("Recommended: API.md (for code project)")

        if (project_path / "tests").exists():
            if "TESTING.md" not in existing_files:
                missing.append("Recommended: TESTING.md (testing documentation)")

        if (project_path / "docker-compose.yml").exists() or (project_path / "Dockerfile").exists():
            if "DEPLOYMENT.md" not in existing_files:
                missing.append("Recommended: DEPLOYMENT.md (for containerized project)")

        return missing


class DocumentationMaintenanceEngine:
    """Engine for maintaining project documentation."""

    def __init__(self, logger):
        self.logger = logger

    async def maintain_documentation(self, profile: ProjectDocumentationProfile) -> Dict[str, Any]:
        """
        Maintain project documentation based on profile analysis.

        Args:
            profile: Project documentation profile

        Returns:
            Maintenance results
        """
        maintenance_results = {
            "actions_taken": [],
            "files_updated": [],
            "recommendations_addressed": 0,
            "success": True,
            "errors": [],
        }

        try:
            # Address high-priority recommendations
            for recommendation in profile.maintenance_recommendations:
                if "missing required" in recommendation.lower():
                    result = await self._create_missing_documentation(
                        recommendation, profile.project_root
                    )
                    maintenance_results["actions_taken"].append(result)
                    if result["success"]:
                        maintenance_results["files_updated"].extend(result.get("files", []))
                        maintenance_results["recommendations_addressed"] += 1
                    else:
                        maintenance_results["errors"].append(result.get("error", "Unknown error"))

            return maintenance_results

        except Exception as e:
            self.logger.error(f"Error in documentation maintenance: {e}")
            maintenance_results["success"] = False
            maintenance_results["errors"].append(str(e))
            return maintenance_results

    async def _create_missing_documentation(
        self, recommendation: str, project_root: str
    ) -> Dict[str, Any]:
        """Create missing documentation files."""
        # This would implement actual file creation
        # For now, return a simulation
        return {
            "success": True,
            "action": "create_documentation",
            "recommendation": recommendation,
            "files": [],
            "note": "Documentation creation not implemented in base version",
        }


class PMCollaborationInterface:
    """Interface for collaborating with PM on documentation matters."""

    def __init__(self, agent, logger):
        self.agent = agent
        self.logger = logger

    async def report_documentation_status(
        self, profile: ProjectDocumentationProfile
    ) -> Dict[str, Any]:
        """Report documentation status to PM."""
        status_report = {
            "project_root": profile.project_root,
            "scan_timestamp": profile.scan_timestamp.isoformat(),
            "health_score": profile.documentation_health.get("score", 0),
            "patterns_found": len(profile.documentation_patterns),
            "critical_issues": [],
            "recommendations": profile.maintenance_recommendations[:5],  # Top 5
            "missing_documentation": profile.missing_documentation,
        }

        # Identify critical issues
        if profile.documentation_health["coverage"]["required_coverage"] < 0.8:
            status_report["critical_issues"].append("Missing required documentation files")

        if profile.documentation_health.get("score", 0) < 60:
            status_report["critical_issues"].append("Low documentation quality score")

        # Send to PM
        await self.agent.collaborate_with_pm(
            f"Documentation status report for {Path(profile.project_root).name}",
            context=status_report,
            priority="high" if status_report["critical_issues"] else "normal",
        )

        return status_report

    async def request_documentation_guidance(
        self, question: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request guidance from PM on documentation matters."""
        await self.agent.collaborate_with_pm(
            f"Documentation guidance needed: {question}", context=context, priority="normal"
        )

        return {"guidance_requested": True, "question": question}


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent - Core agent for project pattern scanning and documentation maintenance.

    Responsibilities:
    1. Scan project documentation patterns on initialization
    2. Understand operational patterns from existing documentation
    3. Maintain operational documentation
    4. Collaborate hand-in-hand with PM for documentation needs
    5. Core agent functionality for documentation management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Documentation Agent."""
        super().__init__(
            agent_id="documentation-agent",
            agent_type="documentation",
            capabilities=[
                "project_pattern_scanning",
                "documentation_analysis",
                "operational_pattern_recognition",
                "documentation_maintenance",
                "pm_collaboration",
                "content_quality_assessment",
                "maintenance_recommendations",
                "documentation_health_monitoring",
                "memory_integration",  # New memory capability
            ],
            config=config,
            tier="system",  # Core agent
        )

        # Initialize components
        self.pattern_scanner = DocumentationPatternScanner(self.logger)
        self.maintenance_engine = DocumentationMaintenanceEngine(self.logger)
        self.pm_collaboration = PMCollaborationInterface(self, self.logger)

        # Memory integration
        self.memory_service: Optional[MemoryTriggerService] = None
        self.memory_enhanced = False

        # State
        self.current_project_profile: Optional[ProjectDocumentationProfile] = None
        self.last_scan_timestamp: Optional[datetime] = None

        self.logger.info("Documentation Agent initialized successfully")

    async def _initialize(self) -> None:
        """Initialize the Documentation Agent."""
        try:
            # Auto-scan current project if in a project directory
            current_dir = Path.cwd()
            if await self._is_project_directory(current_dir):
                self.logger.info("Project directory detected, initiating auto-scan")
                await self.scan_project_patterns(str(current_dir))

            self.logger.info("Documentation Agent initialization complete")

        except Exception as e:
            self.logger.error(f"Error initializing Documentation Agent: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup Documentation Agent resources."""
        try:
            # Save current state if needed
            if self.current_project_profile:
                await self._save_project_profile()

            self.logger.info("Documentation Agent cleanup complete")

        except Exception as e:
            self.logger.error(f"Error cleaning up Documentation Agent: {e}")
            raise

    async def _execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """Execute Documentation Agent operations."""
        context = context or {}

        if operation == "scan_project_patterns":
            project_root = kwargs.get("project_root") or context.get("project_root")
            if not project_root:
                raise ValueError("project_root required for scan_project_patterns")
            return await self.scan_project_patterns(project_root)

        elif operation == "get_documentation_status":
            return await self.get_documentation_status()

        elif operation == "maintain_documentation":
            return await self.maintain_documentation()

        elif operation == "analyze_operational_patterns":
            return await self.analyze_operational_patterns()

        elif operation == "report_to_pm":
            return await self.report_status_to_pm()

        elif operation == "validate_documentation_health":
            project_root = kwargs.get("project_root") or context.get("project_root")
            return await self.validate_documentation_health(project_root)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def scan_project_patterns(self, project_root: str) -> Dict[str, Any]:
        """
        Scan project for documentation patterns and initialize understanding.

        Args:
            project_root: Root directory of the project to scan

        Returns:
            Scan results with patterns found
        """
        try:
            self.logger.info(f"Scanning project patterns: {project_root}")

            # Perform comprehensive scan
            profile = await self.pattern_scanner.scan_project(project_root)
            self.current_project_profile = profile
            self.last_scan_timestamp = datetime.now()

            # Report to PM
            await self.pm_collaboration.report_documentation_status(profile)

            # Create memory trigger for successful scan
            result = {
                "success": True,
                "project_root": project_root,
                "patterns_found": len(profile.documentation_patterns),
                "health_score": profile.documentation_health.get("score", 0),
                "recommendations": len(profile.maintenance_recommendations),
                "scan_timestamp": profile.scan_timestamp.isoformat(),
            }

            # Create memory trigger
            await self._create_memory_trigger(
                "scan_project_patterns",
                {
                    "project_name": Path(project_root).name,
                    "patterns_found": len(profile.documentation_patterns),
                    "health_score": profile.documentation_health.get("score", 0),
                    "recommendations": profile.maintenance_recommendations,
                },
                result,
            )

            return result

        except Exception as e:
            self.logger.error(f"Error scanning project patterns: {e}")
            return {"success": False, "error": str(e)}

    async def get_documentation_status(self) -> Dict[str, Any]:
        """Get current documentation status."""
        if not self.current_project_profile:
            return {"status": "no_project_scanned", "message": "No project has been scanned yet"}

        return {
            "status": "active",
            "project_root": self.current_project_profile.project_root,
            "last_scan": self.current_project_profile.scan_timestamp.isoformat(),
            "health_score": self.current_project_profile.documentation_health.get("score", 0),
            "patterns_count": len(self.current_project_profile.documentation_patterns),
            "recommendations_count": len(self.current_project_profile.maintenance_recommendations),
            "missing_docs_count": len(self.current_project_profile.missing_documentation),
        }

    async def maintain_documentation(self) -> Dict[str, Any]:
        """Maintain project documentation."""
        if not self.current_project_profile:
            return {"success": False, "error": "No project profile available"}

        try:
            results = await self.maintenance_engine.maintain_documentation(
                self.current_project_profile
            )

            # Notify PM of maintenance results
            if results["actions_taken"]:
                await self.collaborate_with_pm(
                    "Documentation maintenance completed", context=results, priority="normal"
                )

            return results

        except Exception as e:
            self.logger.error(f"Error maintaining documentation: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_operational_patterns(self) -> Dict[str, Any]:
        """Analyze operational patterns from documentation."""
        if not self.current_project_profile:
            return {"success": False, "error": "No project profile available"}

        return {
            "success": True,
            "operational_patterns": self.current_project_profile.operational_patterns,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    async def report_status_to_pm(self) -> Dict[str, Any]:
        """Report comprehensive status to PM."""
        if not self.current_project_profile:
            await self.collaborate_with_pm(
                "Documentation Agent status: No project scanned", priority="low"
            )
            return {"reported": True, "status": "no_project"}

        status_report = await self.pm_collaboration.report_documentation_status(
            self.current_project_profile
        )

        return {"reported": True, "status": "active", "report": status_report}

    async def validate_documentation_health(
        self, project_root: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate documentation health for a project."""
        if project_root:
            # Scan new project
            await self.scan_project_patterns(project_root)

        if not self.current_project_profile:
            return {"success": False, "error": "No project profile available"}

        health = self.current_project_profile.documentation_health

        result = {
            "success": True,
            "health_score": health.get("score", 0),
            "coverage": health.get("coverage", {}),
            "quality": health.get("quality", {}),
            "freshness": health.get("freshness", {}),
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Create memory trigger for documentation validation
        await self._create_memory_trigger(
            "validate_documentation_health",
            {
                "project_name": (
                    Path(project_root).name
                    if project_root
                    else Path(self.current_project_profile.project_root).name
                ),
                "validation_status": "healthy" if health.get("score", 0) >= 70 else "degraded",
                "issues_count": len(health.get("coverage", {}).get("missing_required", [])),
                "health_score": health.get("score", 0),
            },
            result,
        )

        return result

    async def _is_project_directory(self, path: Path) -> bool:
        """Check if directory appears to be a project directory."""
        project_indicators = [
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "pom.xml",
            "README.md",
            "CLAUDE.md",
            ".git",
            "src",
            "lib",
        ]

        return any((path / indicator).exists() for indicator in project_indicators)

    async def _save_project_profile(self) -> None:
        """Save current project profile (if needed for persistence)."""
        # Implementation would depend on persistence requirements
        self.logger.debug("Project profile save requested (not implemented)")

    def _should_notify_pm(self, operation: str, result: Any) -> bool:
        """Determine if PM should be notified of operation completion."""
        # Notify PM for scan operations and critical maintenance
        pm_notify_operations = [
            "scan_project_patterns",
            "maintain_documentation",
            "validate_documentation_health",
        ]
        return operation in pm_notify_operations

    # Memory Integration Methods

    def enable_memory_integration(self, memory_service: MemoryTriggerService):
        """Enable memory integration for the Documentation Agent."""
        self.memory_service = memory_service
        self.memory_enhanced = True
        self.logger.info("Documentation Agent memory integration enabled")

    async def _create_memory_trigger(self, operation: str, context: Dict[str, Any], result: Any):
        """Create memory trigger for documentation operations."""
        if not self.memory_enhanced or not self.memory_service:
            return

        try:
            # Prepare memory content based on operation
            memory_content = self._generate_memory_content(operation, context, result)

            # Prepare metadata
            metadata = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "operation": operation,
                "project_name": context.get("project_name", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "success": self._is_operation_successful(result),
            }

            # Add operation-specific metadata
            if operation == "scan_project_patterns":
                metadata.update(
                    {
                        "patterns_found": context.get("patterns_found", 0),
                        "health_score": context.get("health_score", 0),
                        "recommendations": len(context.get("recommendations", [])),
                    }
                )
            elif operation == "validate_documentation_health":
                metadata.update(
                    {
                        "validation_status": context.get("validation_status", "unknown"),
                        "issues_count": context.get("issues_count", 0),
                    }
                )
            elif operation == "maintain_documentation":
                metadata.update(
                    {
                        "actions_taken": len(context.get("actions_taken", [])),
                        "files_updated": len(context.get("files_updated", [])),
                    }
                )

            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.OPERATION_COMPLETION,
                priority=TriggerPriority.MEDIUM,
                project_name=context.get("project_name", "unknown"),
                event_id=f"doc_agent_{operation}_{int(time.time())}",
                content=memory_content,
                category=MemoryCategory.WORKFLOW,
                tags=["documentation", operation, self.agent_type],
                metadata=metadata,
                source="documentation_agent",
                context=context,
            )

            # Process trigger
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.logger.info(f"Created memory trigger for operation: {operation}")

        except Exception as e:
            self.logger.error(f"Failed to create memory trigger for {operation}: {e}")

    def _generate_memory_content(self, operation: str, context: Dict[str, Any], result: Any) -> str:
        """Generate memory content for documentation operations."""
        project_name = context.get("project_name", "unknown")

        if operation == "scan_project_patterns":
            patterns_found = context.get("patterns_found", 0)
            health_score = context.get("health_score", 0)
            return f"Documentation scan completed for {project_name}. Found {patterns_found} patterns with health score {health_score}."

        elif operation == "validate_documentation_health":
            validation_status = context.get("validation_status", "unknown")
            issues_count = context.get("issues_count", 0)
            return f"Documentation validation for {project_name}. Status: {validation_status}, Issues: {issues_count}."

        elif operation == "maintain_documentation":
            actions_taken = len(context.get("actions_taken", []))
            files_updated = len(context.get("files_updated", []))
            return f"Documentation maintenance for {project_name}. Actions: {actions_taken}, Files updated: {files_updated}."

        else:
            return f"Documentation operation {operation} completed for {project_name}."

    def _is_operation_successful(self, result: Any) -> bool:
        """Determine if operation was successful."""
        if isinstance(result, dict):
            return result.get("success", True)
        return True

    async def _recall_operation_memories(
        self, operation: str, context: Dict[str, Any]
    ) -> List[Any]:
        """Recall relevant memories for documentation operations."""
        if not self.memory_enhanced or not self.memory_service:
            return []

        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return []

            # Build search query
            search_query = f"documentation {operation} {context.get('project_name', '')}"

            # Search for relevant memories
            memories = await memory_service.search_memories(
                query=search_query,
                filters={
                    "agent_type": self.agent_type,
                    "operation": operation,
                    "project_name": context.get("project_name"),
                },
                limit=5,
            )

            self.logger.info(f"Recalled {len(memories)} memories for operation: {operation}")
            return memories

        except Exception as e:
            self.logger.error(f"Failed to recall memories for {operation}: {e}")
            return []
