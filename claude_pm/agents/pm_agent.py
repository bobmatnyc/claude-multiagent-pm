"""
PM Agent - Project Management and Epic Creation Agent
"""

import os
import sys
import json
import yaml
import asyncio
import subprocess
import time
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from claude_pm.core.base_agent import BaseAgent
from claude_pm.core.config import Config
from claude_pm.core.logging_config import setup_logging, setup_streaming_logger, finalize_streaming_logs
from claude_pm.core.connection_manager import get_connection_manager
from claude_pm.services.post_installation_manager import PostInstallationManager


@dataclass
class Epic:
    """Represents a project epic"""

    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str
    estimated_points: int
    dependencies: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    status: str = "pending"
    assigned_agents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    target_completion: Optional[datetime] = None


@dataclass
class ProjectPlan:
    """Represents a comprehensive project plan"""

    project_id: str
    name: str
    description: str
    epics: List[Epic]
    timeline: Dict[str, Any]
    resource_allocation: Dict[str, List[str]]
    risk_assessment: List[str]
    milestones: List[Dict[str, Any]]
    stakeholders: List[str]
    success_metrics: List[str]


class PMAgent(BaseAgent):
    """
    Project Management Agent for epic creation, task orchestration, and project oversight.

    This agent:
    1. Analyzes project requirements and creates comprehensive project plans
    2. Breaks down projects into manageable epics and tasks
    3. Orchestrates multi-agent collaboration
    4. Tracks progress and manages dependencies
    5. Communicates with stakeholders and reports status
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, working_dir: Path = None, project_dir: Path = None):
        super().__init__(
            agent_id="pm-agent",
            agent_type="pm",
            capabilities=[
                "epic_creation",
                "task_orchestration",
                "project_planning",
                "stakeholder_coordination",
                "progress_tracking",
                "resource_allocation",
                "risk_management",
                "quality_assurance",
                "system_initialization",
                "framework_setup",
                "dependency_verification",
                "configuration_management",
                "directory_management",
                "project_indexing",
                "cli_integration",
                "multi_project_orchestration",
                "health_monitoring",
                "diagnostics",
            ],
            config=config,
            tier="system",
        )
        
        # System initialization capabilities
        self.working_dir = working_dir or Path.cwd()
        self.project_dir = project_dir or self._detect_project_directory()
        self.framework_path = self._discover_framework_path()
        self.local_config_dir = self.working_dir / ".claude-pm"
        self.project_config_dir = self.project_dir / ".claude-pm"
        self.framework_config_dir = (
            self.framework_path / ".claude-pm" if self.framework_path else None
        )
        self.console = Console()
        # Use streaming logger for clean INFO display during initialization
        self.logger = setup_streaming_logger(__name__)
        self.standard_logger = setup_logging(__name__)  # For ERROR/WARNING messages

        # PM-specific configurations
        self.prioritization_weights = {
            "business_value": 0.4,
            "technical_complexity": 0.3,
            "risk_level": 0.2,
            "dependency_impact": 0.1,
        }

        self.agent_specializations = {
            "architect": ["system_design", "scaffolding", "api_design"],
            "engineer": ["frontend", "backend", "api_implementation"],
            "qa": ["testing", "validation", "quality_assurance"],
            "operations": ["deployment", "infrastructure", "monitoring"],
            "design": ["ui_design", "ux_design", "user_research"],
        }

    async def analyze_project_requirements(self, design_doc_path: str) -> Dict[str, Any]:
        """
        Analyze project requirements from design documents.

        Args:
            design_doc_path: Path to the design document

        Returns:
            Structured analysis of project requirements
        """
        try:
            with open(design_doc_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract key project information
            project_analysis = {
                "project_type": self._determine_project_type(content),
                "technology_stack": self._extract_technology_stack(content),
                "core_features": self._extract_core_features(content),
                "complexity_assessment": self._assess_complexity(content),
                "timeline_estimate": self._estimate_timeline(content),
                "required_agents": self._identify_required_agents(content),
                "risk_factors": self._identify_risks(content),
                "success_criteria": self._extract_success_criteria(content),
            }

            # Store analysis in memory (placeholder for memory integration)
            self.logger.info(f"Project analysis completed: {project_analysis['project_type']}")

            return project_analysis

        except Exception as e:
            self.standard_logger.error(f"Error analyzing project requirements: {e}")
            raise

    def _determine_project_type(self, content: str) -> str:
        """Determine the type of project from content"""
        content_lower = content.lower()

        if "survey" in content_lower and "multi-stakeholder" in content_lower:
            return "survey_platform"
        elif "web app" in content_lower or "web application" in content_lower:
            return "web_application"
        elif "api" in content_lower and "backend" in content_lower:
            return "api_service"
        elif "dashboard" in content_lower or "admin" in content_lower:
            return "dashboard_application"
        else:
            return "general_application"

    def _extract_technology_stack(self, content: str) -> Dict[str, str]:
        """Extract technology stack from content"""
        tech_stack = {}

        # Frontend framework detection
        if "next.js" in content.lower():
            tech_stack["frontend"] = "next.js"
        elif "react" in content.lower():
            tech_stack["frontend"] = "react"
        elif "vue" in content.lower():
            tech_stack["frontend"] = "vue"

        # Backend technology
        if "fastapi" in content.lower():
            tech_stack["backend"] = "fastapi"
        elif "node.js" in content.lower():
            tech_stack["backend"] = "node.js"
        elif "express" in content.lower():
            tech_stack["backend"] = "express"

        # Database
        if "postgresql" in content.lower():
            tech_stack["database"] = "postgresql"
        elif "mongodb" in content.lower():
            tech_stack["database"] = "mongodb"
        elif "sqlite" in content.lower():
            tech_stack["database"] = "sqlite"

        # Styling
        if "tailwind" in content.lower():
            tech_stack["styling"] = "tailwindcss"
        elif "styled-components" in content.lower():
            tech_stack["styling"] = "styled-components"

        # State management
        if "zustand" in content.lower():
            tech_stack["state"] = "zustand"
        elif "redux" in content.lower():
            tech_stack["state"] = "redux"

        return tech_stack

    def _extract_core_features(self, content: str) -> List[str]:
        """Extract core features from content"""
        features = []

        # Common feature patterns
        feature_patterns = [
            "survey creation",
            "multi-stakeholder",
            "scoring engine",
            "admin dashboard",
            "user authentication",
            "data export",
            "real-time",
            "responsive design",
            "role-based access",
            "schema validation",
            "analytics",
            "reporting",
        ]

        content_lower = content.lower()
        for pattern in feature_patterns:
            if pattern in content_lower:
                features.append(pattern.replace("_", " ").title())

        return features

    def _assess_complexity(self, content: str) -> str:
        """Assess project complexity"""
        complexity_indicators = [
            "multi-stakeholder",
            "real-time",
            "authentication",
            "complex scoring",
            "admin dashboard",
            "data export",
            "schema validation",
            "role-based",
            "analytics",
            "reporting",
            "api integration",
            "microservices",
        ]

        content_lower = content.lower()
        indicator_count = sum(
            1 for indicator in complexity_indicators if indicator in content_lower
        )

        if indicator_count >= 8:
            return "high"
        elif indicator_count >= 5:
            return "medium"
        else:
            return "low"

    def _estimate_timeline(self, content: str) -> Dict[str, Any]:
        """Estimate project timeline"""
        complexity = self._assess_complexity(content)
        features = self._extract_core_features(content)

        # Base timeline estimates (in days)
        base_timeline = {"low": 10, "medium": 20, "high": 35}

        # Feature multipliers
        feature_multipliers = {
            "Survey Creation": 1.2,
            "Multi-Stakeholder": 1.3,
            "Scoring Engine": 1.4,
            "Admin Dashboard": 1.2,
            "Data Export": 1.1,
            "Real-Time": 1.5,
            "Authentication": 1.1,
        }

        base_days = base_timeline[complexity]
        multiplier = 1.0

        for feature in features:
            if feature in feature_multipliers:
                multiplier *= feature_multipliers[feature]

        estimated_days = int(base_days * multiplier)

        return {
            "total_days": estimated_days,
            "phases": {
                "planning": 2,
                "setup": 3,
                "core_development": int(estimated_days * 0.6),
                "testing": int(estimated_days * 0.2),
                "deployment": int(estimated_days * 0.1),
            },
        }

    def _identify_required_agents(self, content: str) -> List[str]:
        """Identify required agents for the project"""
        required_agents = ["architect", "engineer"]  # Always needed

        content_lower = content.lower()

        if "admin" in content_lower or "dashboard" in content_lower:
            required_agents.append("engineer")  # Additional frontend work

        if "api" in content_lower or "backend" in content_lower:
            required_agents.append("engineer")  # Backend specialist

        if "deploy" in content_lower or "production" in content_lower:
            required_agents.append("operations")

        if "test" in content_lower or "qa" in content_lower:
            required_agents.append("qa")

        if "ui" in content_lower or "ux" in content_lower or "design" in content_lower:
            required_agents.append("design")

        return list(set(required_agents))

    def _identify_risks(self, content: str) -> List[str]:
        """Identify potential project risks"""
        risks = []

        content_lower = content.lower()

        if "complex" in content_lower or "advanced" in content_lower:
            risks.append("Technical complexity may lead to delays")

        if "multi-stakeholder" in content_lower:
            risks.append("Coordination complexity with multiple stakeholders")

        if "real-time" in content_lower:
            risks.append("Real-time features may require additional infrastructure")

        if "authentication" in content_lower:
            risks.append("Security requirements may add complexity")

        if "export" in content_lower:
            risks.append("Data export features may have performance implications")

        return risks

    def _extract_success_criteria(self, content: str) -> List[str]:
        """Extract success criteria from content"""
        criteria = []

        # Look for explicit success criteria
        if "success criteria" in content.lower():
            # Extract criteria from success criteria section
            criteria.extend(
                [
                    "All core features implemented and functional",
                    "System passes all quality gates",
                    "Performance meets requirements",
                    "Security requirements satisfied",
                ]
            )

        # Add default criteria
        criteria.extend(
            [
                "Project delivered on time",
                "Code quality standards met",
                "Documentation complete",
                "Stakeholder acceptance achieved",
            ]
        )

        return criteria

    async def create_project_plan(
        self, project_analysis: Dict[str, Any], project_name: str
    ) -> ProjectPlan:
        """
        Create a comprehensive project plan based on analysis.

        Args:
            project_analysis: Analysis results from analyze_project_requirements
            project_name: Name of the project

        Returns:
            Comprehensive project plan
        """
        try:
            # Create project epics
            epics = await self._create_project_epics(project_analysis)

            # Create timeline
            timeline = self._create_project_timeline(project_analysis, epics)

            # Allocate resources
            resource_allocation = self._allocate_resources(
                epics, project_analysis["required_agents"]
            )

            # Create milestones
            milestones = self._create_milestones(timeline, epics)

            project_plan = ProjectPlan(
                project_id=f"proj-{project_name.lower().replace(' ', '-')}",
                name=project_name,
                description=f"Implementation of {project_name} based on design requirements",
                epics=epics,
                timeline=timeline,
                resource_allocation=resource_allocation,
                risk_assessment=project_analysis["risk_factors"],
                milestones=milestones,
                stakeholders=["pm", "architect", "engineer", "qa"],
                success_metrics=project_analysis["success_criteria"],
            )

            # Store project plan (placeholder for memory integration)
            self.logger.info(f"Project plan created: {project_name}")

            return project_plan

        except Exception as e:
            self.standard_logger.error(f"Error creating project plan: {e}")
            raise

    async def _create_project_epics(self, project_analysis: Dict[str, Any]) -> List[Epic]:
        """Create epics based on project analysis"""
        epics = []

        # Epic 1: Project Setup and Scaffolding
        setup_epic = Epic(
            id="EP-001",
            title="Project Setup and Scaffolding",
            description="Initialize project structure, configure build tools, and set up development environment",
            acceptance_criteria=[
                "Project structure created with proper directory organization",
                "Build tools configured (Next.js, TypeScript, Tailwind)",
                "Development environment setup complete",
                "Initial configuration files in place",
                "Git repository initialized with proper .gitignore",
            ],
            priority="high",
            estimated_points=5,
            assigned_agents=["architect", "operations"],
            target_completion=datetime.now() + timedelta(days=2),
        )
        epics.append(setup_epic)

        # Epic 2: Core Infrastructure
        infrastructure_epic = Epic(
            id="EP-002",
            title="Core Infrastructure Development",
            description="Implement core system infrastructure, data models, and base components",
            acceptance_criteria=[
                "Data models and types defined",
                "Storage system implemented",
                "Base UI components created",
                "Authentication system setup",
                "API structure established",
            ],
            priority="high",
            estimated_points=8,
            dependencies=["EP-001"],
            assigned_agents=["architect", "engineer"],
            target_completion=datetime.now() + timedelta(days=5),
        )
        epics.append(infrastructure_epic)

        # Epic 3: Survey Engine
        if "survey" in project_analysis["project_type"]:
            survey_epic = Epic(
                id="EP-003",
                title="Survey Engine Implementation",
                description="Implement schema-driven survey engine with multi-stakeholder support",
                acceptance_criteria=[
                    "Survey schema system implemented",
                    "Question rendering engine working",
                    "Multi-stakeholder filtering functional",
                    "Survey validation system complete",
                    "Progress tracking implemented",
                ],
                priority="high",
                estimated_points=13,
                dependencies=["EP-002"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=10),
            )
            epics.append(survey_epic)

        # Epic 4: Scoring System
        if "scoring" in str(project_analysis["core_features"]).lower():
            scoring_epic = Epic(
                id="EP-004",
                title="Scoring and Analytics System",
                description="Implement weighted scoring engine and results analytics",
                acceptance_criteria=[
                    "Weighted scoring algorithm implemented",
                    "Multi-stakeholder score aggregation working",
                    "Maturity level determination functional",
                    "Results visualization complete",
                    "Analytics dashboard implemented",
                ],
                priority="medium",
                estimated_points=10,
                dependencies=["EP-003"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=13),
            )
            epics.append(scoring_epic)

        # Epic 5: Admin Dashboard
        if "admin" in str(project_analysis["core_features"]).lower():
            admin_epic = Epic(
                id="EP-005",
                title="Admin Dashboard and Management",
                description="Implement comprehensive admin dashboard with survey management",
                acceptance_criteria=[
                    "Admin authentication system working",
                    "Survey management interface complete",
                    "Response viewing and management functional",
                    "Data export capabilities implemented",
                    "Administrative reporting complete",
                ],
                priority="medium",
                estimated_points=8,
                dependencies=["EP-002"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=15),
            )
            epics.append(admin_epic)

        # Epic 6: Testing and Quality Assurance
        qa_epic = Epic(
            id="EP-006",
            title="Testing and Quality Assurance",
            description="Comprehensive testing suite and quality validation",
            acceptance_criteria=[
                "Unit tests implemented for core functions",
                "Integration tests for API endpoints",
                "E2E tests for user workflows",
                "Performance testing complete",
                "Security validation performed",
            ],
            priority="medium",
            estimated_points=6,
            dependencies=["EP-003", "EP-004", "EP-005"],
            assigned_agents=["qa", "engineer"],
            target_completion=datetime.now() + timedelta(days=18),
        )
        epics.append(qa_epic)

        # Epic 7: Deployment and Operations
        deployment_epic = Epic(
            id="EP-007",
            title="Deployment and Operations Setup",
            description="Production deployment configuration and operational monitoring",
            acceptance_criteria=[
                "Production deployment pipeline configured",
                "Environment variables and secrets managed",
                "Monitoring and logging setup",
                "Performance optimization applied",
                "Documentation complete",
            ],
            priority="low",
            estimated_points=4,
            dependencies=["EP-006"],
            assigned_agents=["operations"],
            target_completion=datetime.now() + timedelta(days=20),
        )
        epics.append(deployment_epic)

        return epics

    def _create_project_timeline(
        self, project_analysis: Dict[str, Any], epics: List[Epic]
    ) -> Dict[str, Any]:
        """Create project timeline"""
        timeline = project_analysis["timeline_estimate"]

        # Add epic-specific timeline
        epic_timeline = {}
        for epic in epics:
            epic_timeline[epic.id] = {
                "title": epic.title,
                "start_date": epic.target_completion - timedelta(days=epic.estimated_points),
                "end_date": epic.target_completion,
                "duration_days": epic.estimated_points,
                "dependencies": epic.dependencies,
            }

        timeline["epics"] = epic_timeline
        return timeline

    def _allocate_resources(
        self, epics: List[Epic], required_agents: List[str]
    ) -> Dict[str, List[str]]:
        """Allocate resources to epics"""
        resource_allocation = {}

        for epic in epics:
            resource_allocation[epic.id] = epic.assigned_agents

        return resource_allocation

    def _create_milestones(
        self, timeline: Dict[str, Any], epics: List[Epic]
    ) -> List[Dict[str, Any]]:
        """Create project milestones"""
        milestones = []

        # Phase milestones
        milestones.append(
            {
                "name": "Project Setup Complete",
                "description": "Initial project structure and configuration ready",
                "date": datetime.now() + timedelta(days=timeline["phases"]["setup"]),
                "criteria": ["All setup epics completed", "Development environment ready"],
            }
        )

        milestones.append(
            {
                "name": "Core Features Complete",
                "description": "All core functionality implemented and tested",
                "date": datetime.now()
                + timedelta(
                    days=timeline["phases"]["setup"] + timeline["phases"]["core_development"]
                ),
                "criteria": ["Core epics completed", "Basic functionality working"],
            }
        )

        milestones.append(
            {
                "name": "Production Ready",
                "description": "Application ready for production deployment",
                "date": datetime.now() + timedelta(days=timeline["total_days"]),
                "criteria": [
                    "All epics completed",
                    "Quality gates passed",
                    "Documentation complete",
                ],
            }
        )

        return milestones

    async def orchestrate_project_execution(self, project_plan: ProjectPlan) -> Dict[str, Any]:
        """
        Orchestrate the execution of the project plan.

        Args:
            project_plan: The project plan to execute

        Returns:
            Execution results and status
        """
        try:
            self.logger.info(f"Starting orchestration of project: {project_plan.name}")

            # Create tracking tickets for all epics
            for epic in project_plan.epics:
                await self._create_epic_ticket(epic)

            # Execute epics in dependency order
            execution_results = {}

            for epic in self._sort_epics_by_dependencies(project_plan.epics):
                self.logger.info(f"Executing epic: {epic.title}")

                # Execute epic
                epic_result = await self._execute_epic(epic)
                execution_results[epic.id] = epic_result

                # Update epic status
                await self._update_epic_status(epic.id, epic_result["status"])

                # Check for blockers
                if epic_result["status"] == "blocked":
                    self.standard_logger.warning(
                        f"Epic {epic.id} is blocked: {epic_result.get('blocker_reason', 'Unknown')}"
                    )
                    # Handle blockers or escalate
                    await self._handle_epic_blocker(epic, epic_result)

            # Generate final project report
            project_status = self._generate_project_status(execution_results)

            return {
                "project_id": project_plan.project_id,
                "status": project_status,
                "execution_results": execution_results,
                "completion_date": datetime.now().isoformat(),
            }

        except Exception as e:
            self.standard_logger.error(f"Error orchestrating project execution: {e}")
            raise

    async def _create_epic_ticket(self, epic: Epic) -> str:
        """Create a tracking ticket for an epic"""
        try:
            # Placeholder for trackdown service integration
            self.logger.info(f"Creating epic ticket: {epic.title}")

            # Generate placeholder ticket ID
            ticket_id = f"EP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Log epic creation
            self.logger.info(f"Epic {ticket_id} created: {epic.title}")

            return ticket_id

        except Exception as e:
            self.standard_logger.error(f"Error creating epic ticket: {e}")
            raise

    def _sort_epics_by_dependencies(self, epics: List[Epic]) -> List[Epic]:
        """Sort epics by dependencies (topological sort)"""
        sorted_epics = []
        remaining_epics = epics.copy()

        while remaining_epics:
            # Find epics with no unresolved dependencies
            ready_epics = [
                epic
                for epic in remaining_epics
                if not epic.dependencies
                or all(
                    dep in [completed.id for completed in sorted_epics] for dep in epic.dependencies
                )
            ]

            if not ready_epics:
                # Circular dependency or other issue
                self.standard_logger.warning("Circular dependency detected, proceeding with remaining epics")
                ready_epics = remaining_epics

            # Add ready epics to sorted list
            for epic in ready_epics:
                sorted_epics.append(epic)
                remaining_epics.remove(epic)

        return sorted_epics

    async def _execute_epic(self, epic: Epic) -> Dict[str, Any]:
        """Execute a single epic"""
        try:
            self.logger.info(f"Executing epic {epic.id}: {epic.title}")

            # Delegate to appropriate agents
            results = {}

            for agent_type in epic.assigned_agents:
                agent_result = await self._delegate_to_agent(agent_type, epic)
                results[agent_type] = agent_result

            # Determine overall epic status
            if all(result["status"] == "completed" for result in results.values()):
                status = "completed"
            elif any(result["status"] == "failed" for result in results.values()):
                status = "failed"
            elif any(result["status"] == "blocked" for result in results.values()):
                status = "blocked"
            else:
                status = "in_progress"

            return {
                "epic_id": epic.id,
                "status": status,
                "agent_results": results,
                "completion_date": datetime.now().isoformat() if status == "completed" else None,
            }

        except Exception as e:
            self.standard_logger.error(f"Error executing epic {epic.id}: {e}")
            return {"epic_id": epic.id, "status": "failed", "error": str(e), "agent_results": {}}

    async def _delegate_to_agent(self, agent_type: str, epic: Epic) -> Dict[str, Any]:
        """Delegate epic work to specific agent type"""
        try:
            # This is where we would integrate with the actual agent system
            # For now, we'll simulate the delegation

            self.logger.info(f"Delegating to {agent_type} agent for epic {epic.id}")

            # Simulate agent work (in real implementation, this would call actual agents)
            if agent_type == "architect":
                return await self._simulate_architect_work(epic)
            elif agent_type == "engineer":
                return await self._simulate_engineer_work(epic)
            elif agent_type == "qa":
                return await self._simulate_qa_work(epic)
            elif agent_type == "operations":
                return await self._simulate_operations_work(epic)
            else:
                return {"status": "completed", "message": f"Work delegated to {agent_type}"}

        except Exception as e:
            self.standard_logger.error(f"Error delegating to {agent_type}: {e}")
            return {"status": "failed", "error": str(e)}

    async def _simulate_architect_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate architect agent work"""
        # This would be replaced with actual architect agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["system_design", "api_specifications", "data_models"],
            "message": f"Architecture work completed for {epic.title}",
        }

    async def _simulate_engineer_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate engineer agent work"""
        # This would be replaced with actual engineer agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["implementation", "unit_tests", "documentation"],
            "message": f"Engineering work completed for {epic.title}",
        }

    async def _simulate_qa_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate QA agent work"""
        # This would be replaced with actual QA agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["test_cases", "test_execution", "quality_report"],
            "message": f"QA work completed for {epic.title}",
        }

    async def _simulate_operations_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate operations agent work"""
        # This would be replaced with actual operations agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["deployment_config", "monitoring_setup", "documentation"],
            "message": f"Operations work completed for {epic.title}",
        }

    async def _update_epic_status(self, epic_id: str, status: str) -> None:
        """Update epic status in tracking system"""
        try:
            # Placeholder for trackdown service integration
            self.logger.info(f"Epic {epic_id} status updated to {status}")
        except Exception as e:
            self.standard_logger.error(f"Error updating epic status: {e}")

    async def _handle_epic_blocker(self, epic: Epic, epic_result: Dict[str, Any]) -> None:
        """Handle epic blockers"""
        blocker_reason = epic_result.get("blocker_reason", "Unknown blocker")

        # Log the blocker
        self.standard_logger.warning(f"Epic {epic.id} blocked: {blocker_reason}")

        # Store blocker information (placeholder for memory integration)
        self.standard_logger.warning(f"Epic blocker recorded: {epic.id} - {blocker_reason}")

        # Attempt to resolve or escalate
        # For now, we'll just log it
        self.logger.info(f"Escalating blocker for epic {epic.id}")

    def _generate_project_status(self, execution_results: Dict[str, Any]) -> str:
        """Generate overall project status"""
        completed_epics = sum(
            1 for result in execution_results.values() if result["status"] == "completed"
        )
        total_epics = len(execution_results)
        failed_epics = sum(
            1 for result in execution_results.values() if result["status"] == "failed"
        )

        if failed_epics > 0:
            return "failed"
        elif completed_epics == total_epics:
            return "completed"
        else:
            return "in_progress"

    async def _execute_operation(
        self, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Any:
        """Execute PM Agent operations."""
        context = context or {}

        if operation == "analyze_project_requirements":
            design_doc_path = kwargs.get("design_doc_path") or context.get("design_doc_path")
            if not design_doc_path:
                raise ValueError("design_doc_path required for analyze_project_requirements")
            return await self.analyze_project_requirements(design_doc_path)

        elif operation == "create_project_plan":
            project_analysis = kwargs.get("project_analysis") or context.get("project_analysis")
            project_name = kwargs.get("project_name") or context.get("project_name")
            if not project_analysis or not project_name:
                raise ValueError(
                    "project_analysis and project_name required for create_project_plan"
                )
            return await self.create_project_plan(project_analysis, project_name)

        elif operation == "orchestrate_project_execution":
            project_plan = kwargs.get("project_plan") or context.get("project_plan")
            if not project_plan:
                raise ValueError("project_plan required for orchestrate_project_execution")
            return await self.orchestrate_project_execution(project_plan)

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _initialize(self) -> None:
        """Initialize the PM Agent."""
        try:
            # Initialize any required resources
            self.logger.info("PM Agent initialized successfully")
        except Exception as e:
            self.standard_logger.error(f"Failed to initialize PM Agent: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup PM Agent resources."""
        try:
            # Cleanup any resources
            self.logger.info("PM Agent cleanup completed")
            # Finalize streaming logs to ensure final message is visible
            finalize_streaming_logs(self.logger)
        except Exception as e:
            self.standard_logger.error(f"Failed to cleanup PM Agent: {e}")
            finalize_streaming_logs(self.logger)
            raise

    # ===============================================
    # SYSTEM INITIALIZATION METHODS
    # (Integrated from SystemInitAgent)
    # ===============================================
    
    def _detect_project_directory(self) -> Path:
        """
        Detect the project directory for the current context.

        Project directory detection logic:
        1. Look for project indicators (.git, package.json, pyproject.toml, etc.)
        2. Check for existing .claude-pm directory
        3. Use working directory as fallback
        """
        current = self.working_dir

        # Project indicators
        project_files = [
            ".git",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            ".claude-pm",
        ]

        # Walk up the directory tree to find project root
        while current != current.parent:
            for indicator in project_files:
                if (current / indicator).exists():
                    return current
            current = current.parent

        # Fallback to working directory
        return self.working_dir

    def _discover_framework_path(self) -> Optional[Path]:
        """Discover the Claude PM Framework installation path."""
        # Check environment variable first
        env_path = os.environ.get("CLAUDE_PM_FRAMEWORK_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)

        # Check common installation locations
        home = Path.home()
        candidates = [
            home / "Projects" / "claude-pm",
            home / "Clients" / "claude-pm",
            Path.cwd(),
            Path.cwd().parent,
        ]

        for candidate in candidates:
            if candidate.exists() and (candidate / "claude_pm" / "__init__.py").exists():
                return candidate

        return None

    async def initialize_framework(self, force: bool = False) -> Dict[str, Any]:
        """
        Initialize the Claude PM Framework in the current directory.

        Args:
            force: Force reinitialize even if already set up

        Returns:
            Dict containing initialization results and status
        """
        self.logger.info(f"Starting framework initialization in {self.working_dir}")

        results = {
            "success": False,
            "working_directory": str(self.working_dir),
            "framework_location": str(self.framework_path),
            "steps_completed": [],
            "errors": [],
            "setup_status": "unknown",
        }

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:

                # Step 1: Check existing setup
                check_task = progress.add_task("Checking existing setup...", total=1)
                local_config_exists = self.local_config_dir.exists()

                if local_config_exists and not force:
                    progress.update(check_task, completed=1)
                    results["setup_status"] = "already_exists"
                    results["success"] = True
                    results["steps_completed"].append("check_existing")
                    return results

                progress.update(check_task, completed=1)
                results["steps_completed"].append("check_existing")

                # Step 2: Create directory structure
                structure_task = progress.add_task("Creating directory structure...", total=1)
                if self._create_directory_structure():
                    progress.update(structure_task, completed=1)
                    results["steps_completed"].append("directory_structure")
                else:
                    results["errors"].append("Failed to create directory structure")
                    return results

                # Step 3: Generate configuration files
                config_task = progress.add_task("Generating configuration files...", total=1)
                if await self._generate_configuration_files():
                    progress.update(config_task, completed=1)
                    results["steps_completed"].append("configuration_files")
                else:
                    results["errors"].append("Failed to generate configuration files")
                    return results

                # Step 4: Verify dependencies
                deps_task = progress.add_task("Verifying dependencies...", total=1)
                dependency_status = await self._verify_dependencies()
                results["dependencies"] = dependency_status
                progress.update(deps_task, completed=1)
                results["steps_completed"].append("dependency_verification")

                # Step 5: Final setup status
                results["setup_status"] = self._get_final_setup_status(dependency_status)
                results["success"] = True

        except Exception as e:
            self.standard_logger.error(f"Framework initialization failed: {e}")
            results["errors"].append(f"Initialization failed: {str(e)}")
            results["success"] = False
        finally:
            # Finalize streaming logs to ensure final messages are visible
            finalize_streaming_logs(self.logger)

        return results

    def _create_directory_structure(self) -> bool:
        """
        Create the enhanced .claude-pm directory structure with three-tier agent hierarchy.

        Creates three types of directories:
        1. Framework directory: Global user agents, system training data
        2. Working directory: Current working location config
        3. Project directory: Project-specific agents and configurations

        Agent Hierarchy Structure:
        - System Agents: /framework/claude_pm/agents/ (core framework)
        - User Agents: ~/.claude-pm/agents/user-defined/ (global)
        - Project Agents: $PROJECT/.claude-pm/agents/project-specific/ (local)
        """
        try:
            # Framework directory structure (global) - ENHANCED WITH AGENT HIERARCHY
            if self.framework_config_dir:
                framework_dirs = [
                    self.framework_config_dir,
                    self.framework_config_dir / "config",
                    self.framework_config_dir / "agents" / "user-defined",  # Global user agents
                    self.framework_config_dir
                    / "agents"
                    / "user-defined"
                    / "templates",  # User agent templates
                    self.framework_config_dir / "agents" / "system-trained",  # System training data
                    self.framework_config_dir
                    / "agents"
                    / "system-trained"
                    / "patterns",  # Learned patterns
                    self.framework_config_dir / "templates" / "global",
                    self.framework_config_dir / "templates" / "agents",  # Agent templates
                    self.framework_config_dir / "logs" / "framework",
                    self.framework_config_dir / "logs" / "agents",  # Agent-specific logs
                    self.framework_config_dir / "cache" / "global",
                    self.framework_config_dir / "cache" / "agents",  # Agent cache
                ]

                for directory in framework_dirs:
                    directory.mkdir(parents=True, exist_ok=True)

            # Working directory structure (current session) - ENHANCED WITH AGENT HIERARCHY
            working_dirs = [
                self.local_config_dir,
                self.local_config_dir / "config",
                self.local_config_dir / "agents" / "project-specific",  # Project-local agents
                self.local_config_dir
                / "agents"
                / "project-specific"
                / "templates",  # Project agent templates
                self.local_config_dir
                / "agents"
                / "project-specific"
                / "config",  # Project agent config
                self.local_config_dir / "agents" / "hierarchy",  # Agent hierarchy metadata
                self.local_config_dir / "index",  # Project indexing system
                self.local_config_dir / "index" / "cache",  # Index cache files
                self.local_config_dir / "index" / "agents",  # Agent index data
                self.local_config_dir / "sessions",
                self.local_config_dir / "logs" / "working",
                self.local_config_dir / "logs" / "init",  # Initialization logs
                self.local_config_dir / "logs" / "agents",  # Agent operation logs
                self.local_config_dir / "cache" / "working",
                self.local_config_dir / "cache" / "agents",  # Agent cache
                self.local_config_dir / "templates" / "project",  # Project templates
                self.local_config_dir / "templates" / "agents",  # Agent templates
                self.local_config_dir / "memory",  # Memory system storage
            ]

            for directory in working_dirs:
                directory.mkdir(parents=True, exist_ok=True)

            # Project directory structure (project-specific) - ENHANCED WITH AGENT HIERARCHY
            if self.project_dir != self.working_dir:
                project_dirs = [
                    self.project_config_dir,
                    self.project_config_dir / "config",
                    self.project_config_dir / "agents" / "project-specific",  # Project agents
                    self.project_config_dir
                    / "agents"
                    / "project-specific"
                    / "templates",  # Project agent templates
                    self.project_config_dir
                    / "agents"
                    / "project-specific"
                    / "config",  # Project agent config
                    self.project_config_dir / "agents" / "hierarchy",  # Agent hierarchy metadata
                    self.project_config_dir / "templates" / "project",
                    self.project_config_dir / "templates" / "agents",  # Agent templates
                    self.project_config_dir / "logs" / "project",
                    self.project_config_dir / "logs" / "agents",  # Agent operation logs
                    self.project_config_dir / "cache" / "project",
                    self.project_config_dir / "cache" / "agents",  # Agent cache
                    self.project_config_dir / "memory",  # Memory system storage
                ]

                for directory in project_dirs:
                    directory.mkdir(parents=True, exist_ok=True)

            # Create initial README files and agent hierarchy metadata
            self._create_initial_readme_files()
            self._create_agent_hierarchy_metadata()

            return True
        except Exception as e:
            self.standard_logger.error(f"Failed to create directory structure: {e}")
            return False

    def _create_initial_readme_files(self):
        """Create initial README files for guidance across all directory types."""
        
        # Framework directory READMEs (global)
        if self.framework_config_dir:
            framework_readme_contents = {
                "README.md": """# Claude PM Framework - Global Configuration

This directory contains global framework configuration and user agents.

## Directory Structure
- `agents/user-defined/`: Global user-defined agents (available across all projects)
- `agents/system-trained/`: System training data and learned patterns
- `templates/global/`: Global templates available to all projects
- `logs/framework/`: Framework-level operation logs
- `cache/global/`: Global cache and state files

## Multi-Project Orchestration
This framework acts as a multi-project orchestrator, managing:
- Global user agents shared across projects
- System-trained prompts and behaviors
- Framework-level configuration and settings
""",
                "agents/user-defined/README.md": """# Global User-Defined Agents

This directory contains user-defined agents that are available across ALL projects.

## Purpose
- Global agents that can be used in any project
- Shared agent behaviors and capabilities
- Framework-level agent definitions

## Structure
- Place your global agent files here
- Follow the framework's agent template structure
- Use the `.py` extension for Python agents
- Include proper documentation and type hints

## Usage
Global agents are automatically available to all projects using this framework.
""",
            }

            for path, content in framework_readme_contents.items():
                readme_path = self.framework_config_dir / path
                readme_path.parent.mkdir(parents=True, exist_ok=True)
                readme_path.write_text(content)

        # Working directory READMEs (current session)
        working_readme_contents = {
            "README.md": """# Claude PM Framework - Working Directory

This directory contains configuration for the current working session.

## Directory Structure
- `config/`: Working directory specific configuration
- `sessions/`: Session data and state
- `logs/working/`: Working directory operation logs
- `cache/working/`: Working directory cache files
- `memory/`: Memory system storage for bugs and feedback

## Purpose
This configuration manages the current working session and provides:
- Session-specific settings
- Working directory context
- Temporary session data
- Memory collection for continuous improvement
""",
            "memory/README.md": """# Memory System Storage

This directory contains memory entries for bugs, feedback, and operational insights.

## Purpose
- Store bug reports and error tracking
- Collect user feedback and suggestions
- Record architectural decisions and insights
- Track performance observations and optimizations

## Structure
- Memory entries are stored as JSON files
- Each entry includes timestamp, category, priority, and content
- Categories: bug, feedback, architecture, performance, integration, qa

## Usage
This directory is managed automatically by the PM agent's memory collection system.
""",
        }

        for path, content in working_readme_contents.items():
            readme_path = self.local_config_dir / path
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            readme_path.write_text(content)

    def _create_agent_hierarchy_metadata(self):
        """Create agent hierarchy metadata files for three-tier system."""
        
        # Framework-level hierarchy metadata (global)
        if self.framework_config_dir:
            framework_hierarchy = {
                "hierarchy_version": "1.0",
                "tier": "framework",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent_tiers": {
                    "system": {
                        "path": "./claude_pm/agents/",
                        "priority": 1,
                        "description": "Core framework agents with highest authority",
                        "immutable": True,
                        "examples": [
                            "pm_agent.py",
                            "orchestrator_agent.py",
                            "ops_agent.py",
                        ],
                    },
                    "user": {
                        "path": "./agents/user-defined/",
                        "priority": 2,
                        "description": "Global user-defined agents across all projects",
                        "immutable": False,
                        "examples": ["custom_engineer_agent.py", "personal_qa_agent.py"],
                    },
                    "project": {
                        "path": "PROJECT/.claude-pm/agents/project-specific/",
                        "priority": 3,
                        "description": "Project-specific agents with highest precedence",
                        "immutable": False,
                        "examples": ["project_engineer_agent.py", "project_security_agent.py"],
                    },
                },
                "loading_rules": {
                    "precedence_order": ["project", "user", "system"],
                    "conflict_resolution": "highest_priority_wins",
                    "fallback_enabled": True,
                    "inheritance_enabled": True,
                },
            }

            framework_hierarchy_path = self.framework_config_dir / "agents" / "hierarchy.yaml"
            framework_hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(framework_hierarchy_path, "w") as f:
                yaml.dump(framework_hierarchy, f, default_flow_style=False, indent=2)

        # Working directory hierarchy metadata with PM agent as system init handler
        working_hierarchy = {
            "hierarchy_version": "1.0",
            "tier": "working",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "working_directory": str(self.working_dir),
            "project_directory": str(self.project_dir),
            "framework_location": str(self.framework_path),
            "system_init_handler": "pm_agent",
            "agent_discovery": {
                "auto_discovery": True,
                "scan_depth": 2,
                "file_patterns": ["*.py"],
                "exclude_patterns": ["__*", ".*", "test_*"],
            },
            "agent_loading": {
                "lazy_loading": True,
                "cache_agents": True,
                "reload_on_change": True,
                "validation_enabled": True,
            },
            "hierarchy_paths": {
                "system_agents": (
                    str(self.framework_path / "claude_pm" / "agents")
                    if self.framework_path
                    else None
                ),
                "user_agents": (
                    str(self.framework_config_dir / "agents" / "user-defined")
                    if self.framework_config_dir
                    else None
                ),
                "project_agents": str(self.local_config_dir / "agents" / "project-specific"),
            },
        }

        working_hierarchy_path = self.local_config_dir / "agents" / "hierarchy.yaml"
        working_hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
        with open(working_hierarchy_path, "w") as f:
            yaml.dump(working_hierarchy, f, default_flow_style=False, indent=2)

    async def _generate_configuration_files(self) -> bool:
        """Generate configuration files for multi-project setup."""
        try:
            # Generate framework-level configuration (global)
            if self.framework_config_dir:
                framework_config = {
                    "claude-pm": {
                        "version": "4.2.3",
                        "mode": "multi-project-orchestrator",
                        "framework_location": str(self.framework_path),
                        "initialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "agent_id": "pm-agent",
                        "system_init_handler": "pm_agent",
                    },
                    "global_agents": {
                        "user_defined_path": "./agents/user-defined",
                        "system_trained_path": "./agents/system-trained",
                        "auto_discover": True,
                        "load_on_startup": True,
                    },
                    "templates": {
                        "global_templates_path": "./templates/global",
                        "inheritance_enabled": True,
                    },
                    "dependencies": {
                        "mem0ai": {
                            "service_url": "http://localhost:8002",
                            "health_endpoint": "/health",
                            "required": True,
                        },
                        "ai-trackdown-tools": {
                            "package": "@bobmatnyc/ai-trackdown-tools",
                            "command": "aitrackdown",
                            "required": True,
                        },
                        "claude-pm-portfolio-manager": {
                            "package": "@bobmatnyc/claude-pm-portfolio-manager",
                            "required": False,
                        },
                    },
                }

                framework_config_path = self.framework_config_dir / "config" / "framework.yaml"
                with open(framework_config_path, "w") as f:
                    yaml.dump(framework_config, f, default_flow_style=False, indent=2)

            # Generate working directory configuration
            working_config = {
                "claude-pm": {
                    "version": "4.2.3",
                    "mode": "working-directory",
                    "working_directory": str(self.working_dir),
                    "project_directory": str(self.project_dir),
                    "framework_location": str(self.framework_path),
                    "initialized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_project_specific": self.project_dir != self.working_dir,
                    "system_init_handler": "pm_agent",
                },
                "session": {
                    "session_id": f"working-{int(time.time())}",
                    "session_path": "./sessions",
                    "auto_save": True,
                },
                "logging": {
                    "level": "INFO",
                    "log_dir": "./logs/working",
                    "rotate_logs": True,
                    "max_log_size": "10MB",
                },
                "memory": {
                    "enabled": True,
                    "storage_path": "./memory",
                    "categories": ["bug", "feedback", "architecture", "performance", "integration", "qa"],
                    "auto_collection": True,
                },
            }

            working_config_path = self.local_config_dir / "config" / "working.yaml"
            with open(working_config_path, "w") as f:
                yaml.dump(working_config, f, default_flow_style=False, indent=2)

            # Generate agents configuration with PM agent as system init handler
            agents_config = {
                "agent_hierarchy": {
                    "system_agents": {
                        "path": (
                            str(self.framework_path / "claude_pm" / "agents")
                            if self.framework_path
                            else None
                        ),
                        "priority": 1,
                        "immutable": True,
                        "description": "Core framework agents with highest authority",
                        "system_init_handler": "pm_agent",
                    },
                    "user_agents": {
                        "path": (
                            str(self.framework_config_dir / "agents" / "user-defined")
                            if self.framework_config_dir
                            else None
                        ),
                        "priority": 2,
                        "immutable": False,
                        "description": "Global user-defined agents across all projects",
                    },
                    "project_agents": {
                        "path": str(self.local_config_dir / "agents" / "project-specific"),
                        "priority": 3,
                        "immutable": False,
                        "description": "Project-specific agents with highest precedence",
                    },
                },
                "agent_loading": {
                    "auto_discover": True,
                    "precedence_order": ["project_agents", "user_agents", "system_agents"],
                    "conflict_resolution": "highest_priority_wins",
                    "fallback_enabled": True,
                    "lazy_loading": True,
                    "cache_agents": True,
                    "reload_on_change": True,
                    "validation_enabled": True,
                },
                "agent_types": {
                    "pm": {
                        "system": "pm_agent.py",
                        "user": "custom_pm_agent.py",
                        "project": "project_pm_agent.py",
                        "responsibilities": ["system_initialization", "project_management", "agent_orchestration"],
                    },
                    "engineer": {
                        "system": "system_engineer_agent.py",
                        "user": "custom_engineer_agent.py",
                        "project": "project_engineer_agent.py",
                    },
                    "ops": {
                        "system": "ops_agent.py",
                        "user": "personal_ops_agent.py",
                        "project": "project_ops_agent.py",
                    },
                    "qa": {
                        "system": "qa_agent.py",
                        "user": "custom_qa_agent.py",
                        "project": "project_qa_agent.py",
                    },
                },
            }

            agents_config_path = self.local_config_dir / "config" / "agents.yaml"
            with open(agents_config_path, "w") as f:
                yaml.dump(agents_config, f, default_flow_style=False, indent=2)

            return True
        except Exception as e:
            self.standard_logger.error(f"Failed to generate configuration files: {e}")
            return False

    async def _verify_dependencies(self) -> Dict[str, Dict[str, str]]:
        """Verify all framework dependencies."""
        dependencies = {
            "mem0ai": await self._check_mem0ai_service(),
            "ai_trackdown_tools": await self._check_ai_trackdown_tools(),
            "claude_pm_portfolio_manager": await self._check_claude_pm_portfolio_manager(),
            "framework_core": await self._check_framework_core(),
            "python_environment": await self._check_python_environment(),
            "node_environment": await self._check_node_environment(),
        }

        # Save dependency status (only if directory exists)
        if self.local_config_dir.exists():
            dependencies_config = {
                "last_checked": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": dependencies,
                "checked_by": "pm-agent",
            }

            dependencies_config_path = self.local_config_dir / "config" / "dependencies.yaml"
            dependencies_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dependencies_config_path, "w") as f:
                yaml.dump(dependencies_config, f, default_flow_style=False, indent=2)

        return dependencies

    async def _check_mem0ai_service(self) -> Dict[str, str]:
        """Check mem0AI service availability using connection manager."""
        try:
            # Use connection manager for proper session lifecycle
            conn_manager = await get_connection_manager()
            session = await conn_manager.get_session(
                service_name="pm_agent_mem0ai_check", timeout=aiohttp.ClientTimeout(total=5.0)
            )

            async with session.get("http://localhost:8002/health") as response:
                if response.status == 200:
                    return {
                        "status": "✅ ONLINE",
                        "version": "active",
                        "details": "Service responding",
                    }
                else:
                    return {
                        "status": "⚠️ DEGRADED",
                        "version": "unknown",
                        "details": f"HTTP {response.status}",
                    }
        except Exception as e:
            return {"status": "❌ OFFLINE", "version": "unknown", "details": str(e)}

    async def _check_ai_trackdown_tools(self) -> Dict[str, str]:
        """Check ai-trackdown-tools package with enhanced detection."""
        try:
            # Enhanced CLI detection
            availability = self.check_aitrackdown_availability(self.working_dir)

            if availability["available"]:
                return {
                    "status": "✅ INSTALLED",
                    "version": availability["version"],
                    "details": f"CLI available ({'local' if availability['local_cli'] else 'global'})",
                }
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "CLI not available"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}

    async def _check_claude_pm_portfolio_manager(self) -> Dict[str, str]:
        """Check claude-pm-portfolio-manager package."""
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "@bobmatnyc/claude-pm-portfolio-manager"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                version_line = [
                    line
                    for line in result.stdout.split("\n")
                    if "@bobmatnyc/claude-pm-portfolio-manager" in line
                ]
                version = version_line[0].split("@")[-1] if version_line else "unknown"
                return {
                    "status": "✅ INSTALLED",
                    "version": version,
                    "details": "NPM package available",
                }
            else:
                return {
                    "status": "❌ MISSING",
                    "version": "none",
                    "details": "NPM package not found",
                }
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}

    async def _check_framework_core(self) -> Dict[str, str]:
        """Check framework core installation."""
        try:
            if self.framework_path and (self.framework_path / "claude_pm" / "__init__.py").exists():
                version_file = self.framework_path / "VERSION"
                version = version_file.read_text().strip() if version_file.exists() else "unknown"
                return {
                    "status": "✅ INSTALLED",
                    "version": version,
                    "details": f"Framework at {self.framework_path}",
                }
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "Framework not found"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}

    async def _check_python_environment(self) -> Dict[str, str]:
        """Check Python environment and required packages."""
        try:
            required_packages = ["rich", "pydantic", "aiohttp", "yaml", "asyncio"]
            missing_packages = []

            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)

            if not missing_packages:
                return {
                    "status": "✅ READY",
                    "version": f"Python {sys.version.split()[0]}",
                    "details": "All required packages available",
                }
            else:
                return {
                    "status": "⚠️ PARTIAL",
                    "version": f"Python {sys.version.split()[0]}",
                    "details": f"Missing: {', '.join(missing_packages)}",
                }
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}

    async def _check_node_environment(self) -> Dict[str, str]:
        """Check Node.js environment."""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                return {"status": "✅ READY", "version": version, "details": "Node.js available"}
            else:
                return {"status": "❌ MISSING", "version": "none", "details": "Node.js not found"}
        except Exception as e:
            return {"status": "❌ ERROR", "version": "unknown", "details": str(e)}

    def _get_final_setup_status(self, dependencies: Dict[str, Dict[str, str]]) -> str:
        """Get overall setup status based on dependencies."""
        all_ready = all(dep["status"].startswith("✅") for dep in dependencies.values())
        some_ready = any(dep["status"].startswith("✅") for dep in dependencies.values())

        if all_ready:
            return "✅ READY"
        elif some_ready:
            return "⚠️ PARTIAL"
        else:
            return "❌ NEEDS_SETUP"

    def check_aitrackdown_availability(self, project_path: Path) -> Dict[str, Any]:
        """
        Check if ai-trackdown-tools is available in project directory.

        Args:
            project_path: Path to check for CLI availability

        Returns:
            Dict with availability status, version, and CLI type
        """
        try:
            # Check for local CLI wrappers first
            local_cli_paths = [
                project_path / "bin" / "aitrackdown",
                project_path / "bin" / "atd",
                project_path / "node_modules" / ".bin" / "aitrackdown",
                project_path / "node_modules" / ".bin" / "atd",
            ]

            for cli_path in local_cli_paths:
                if cli_path.exists() and cli_path.is_file():
                    # Check if it's executable
                    if os.access(cli_path, os.X_OK):
                        version = self._get_cli_version(str(cli_path))
                        return {
                            "available": True,
                            "version": version,
                            "local_cli": True,
                            "cli_path": str(cli_path),
                            "config_path": str(project_path / ".ai-trackdown"),
                        }

            # Check for global installation
            global_commands = ["aitrackdown", "atd"]
            for cmd in global_commands:
                try:
                    result = subprocess.run(
                        [cmd, "--version"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        return {
                            "available": True,
                            "version": version,
                            "local_cli": False,
                            "cli_path": cmd,
                            "config_path": str(project_path / ".ai-trackdown"),
                        }
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    continue

            return {
                "available": False,
                "version": "none",
                "local_cli": False,
                "cli_path": None,
                "config_path": None,
            }

        except Exception as e:
            self.standard_logger.error(f"Error checking ai-trackdown-tools availability: {e}")
            return {
                "available": False,
                "version": "error",
                "local_cli": False,
                "cli_path": None,
                "config_path": None,
                "error": str(e),
            }

    def _get_cli_version(self, cli_path: str) -> str:
        """Get version from CLI command."""
        try:
            result = subprocess.run(
                [cli_path, "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "unknown"
        except Exception:
            return "unknown"

    async def display_initialization_report(self, results: Dict[str, Any]):
        """Display comprehensive initialization report."""
        self.console.print("\n" + "=" * 60)
        self.console.print(
            "🤖 [bold blue]PM Agent - Multi-Project Orchestrator Report[/bold blue]"
        )
        self.console.print("=" * 60)

        # Basic info
        self.console.print(f"📍 Working Directory: {results['working_directory']}")
        self.console.print(f"📂 Framework Location: {results['framework_location']}")
        self.console.print(f"🎯 Project Directory: {self.project_dir}")
        self.console.print(
            f"🏗️  Multi-Project Mode: {'Yes' if self.project_dir != self.working_dir else 'No'}"
        )
        self.console.print(f"🎯 Setup Status: [{results['setup_status']}]")

        # Dependencies table
        if "dependencies" in results:
            self.console.print(f"\n🔧 [bold]Dependencies Status:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Component", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Version", justify="center")
            table.add_column("Details", style="dim")

            for name, info in results["dependencies"].items():
                display_name = name.replace("_", " ").title()
                table.add_row(display_name, info["status"], info["version"], info["details"])

            self.console.print(table)

        # Success/failure summary
        if results["success"]:
            self.console.print(
                f"\n✅ [bold green]Framework initialization completed successfully![/bold green]"
            )
        else:
            self.console.print(f"\n❌ [bold red]Framework initialization failed![/bold red]")

        self.console.print("=" * 60)

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostics for the framework setup."""
        diagnostics = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "working_directory": str(self.working_dir),
            "framework_path": str(self.framework_path),
            "local_config_exists": self.local_config_dir.exists(),
            "dependencies": await self._verify_dependencies(),
            "troubleshooting": await self.troubleshoot_setup_issues(),
            "recommendations": [],
        }

        # Generate recommendations
        if not diagnostics["local_config_exists"]:
            diagnostics["recommendations"].append(
                "Run initialization: python ~/.claude/commands/cmpm-bridge.py init --setup"
            )

        # Check for critical issues
        critical_deps = ["framework_core", "python_environment"]
        for dep in critical_deps:
            if dep in diagnostics["dependencies"] and diagnostics["dependencies"][dep][
                "status"
            ].startswith("❌"):
                diagnostics["recommendations"].append(
                    f"Critical: Fix {dep.replace('_', ' ').title()} installation"
                )

        return diagnostics

    async def troubleshoot_setup_issues(self) -> Dict[str, Any]:
        """Troubleshoot common setup issues and provide solutions."""
        issues = []
        solutions = []

        # Check if framework path exists
        if not self.framework_path:
            issues.append("Claude PM Framework not found")
            solutions.append(
                "Install framework: git clone https://github.com/bobmatnyc/claude-multiagent-pm.git ~/Projects/claude-pm"
            )

        # Check dependencies
        dependencies = await self._verify_dependencies()

        for name, info in dependencies.items():
            if info["status"].startswith("❌"):
                issues.append(f"{name.replace('_', ' ').title()} not available")

                if name == "mem0ai":
                    solutions.append("Start mem0AI service: Follow the mem0AI installation guide")
                elif name == "ai_trackdown_tools":
                    solutions.append(
                        "Install ai-trackdown-tools: npm install -g @bobmatnyc/ai-trackdown-tools"
                    )
                elif name == "claude_pm_portfolio_manager":
                    solutions.append(
                        "Install portfolio manager: npm install -g @bobmatnyc/claude-pm-portfolio-manager"
                    )
                elif name == "node_environment":
                    solutions.append("Install Node.js: https://nodejs.org/en/download/")

        return {"issues": issues, "solutions": solutions, "dependencies": dependencies}

    # Memory collection method to track bugs, feedback, and integration insights
    async def collect_memory(self, category: str, content: str, priority: str = "medium") -> None:
        """Collect and store memory for bugs, feedback, and integration insights."""
        try:
            memory_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "category": category,
                "priority": priority,
                "source_agent": "pm_agent",
                "project_context": str(self.working_dir),
                "content": content,
                "integration_context": "system_init_agent_consolidation",
            }
            
            # Log the memory entry
            self.logger.info(f"Memory collected: {category} - {content}")
            
            # Store in memory system (placeholder for actual memory integration)
            memory_file = self.local_config_dir / "memory" / f"{category}_{int(time.time())}.json"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(memory_file, "w") as f:
                json.dump(memory_entry, f, indent=2)
                
        except Exception as e:
            self.standard_logger.error(f"Failed to collect memory: {e}")

    # Enhanced method to handle system initialization operations
    async def handle_system_initialization(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Handle system initialization operations that were previously in SystemInitAgent."""
        try:
            if operation == "initialize_framework":
                force = kwargs.get("force", False)
                return await self.initialize_framework(force=force)
            elif operation == "verify_dependencies":
                return await self._verify_dependencies()
            elif operation == "run_diagnostics":
                return await self.run_diagnostics()
            elif operation == "troubleshoot_setup":
                return await self.troubleshoot_setup_issues()
            elif operation == "display_report":
                results = kwargs.get("results", {})
                await self.display_initialization_report(results)
                return {"status": "report_displayed"}
            else:
                raise ValueError(f"Unknown system initialization operation: {operation}")
        except Exception as e:
            await self.collect_memory("bug", f"System initialization operation failed: {operation} - {str(e)}", "high")
            raise

    # End of System Initialization Methods
    # ===========================================
