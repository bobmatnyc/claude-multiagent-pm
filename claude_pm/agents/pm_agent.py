"""
PM Agent - Project Management and Epic Creation Agent
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..core.base_agent import BaseAgent


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
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
                "quality_assurance"
            ],
            config=config,
            tier="system"
        )
        
        # PM-specific configurations
        self.prioritization_weights = {
            "business_value": 0.4,
            "technical_complexity": 0.3,
            "risk_level": 0.2,
            "dependency_impact": 0.1
        }
        
        self.agent_specializations = {
            "architect": ["system_design", "scaffolding", "api_design"],
            "engineer": ["frontend", "backend", "api_implementation"],
            "qa": ["testing", "validation", "quality_assurance"],
            "operations": ["deployment", "infrastructure", "monitoring"],
            "design": ["ui_design", "ux_design", "user_research"]
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
            with open(design_doc_path, 'r', encoding='utf-8') as f:
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
                "success_criteria": self._extract_success_criteria(content)
            }
            
            # Store analysis in memory (placeholder for memory integration)
            self.logger.info(f"Project analysis completed: {project_analysis['project_type']}")
            
            return project_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing project requirements: {e}")
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
            "survey creation", "multi-stakeholder", "scoring engine", "admin dashboard",
            "user authentication", "data export", "real-time", "responsive design",
            "role-based access", "schema validation", "analytics", "reporting"
        ]
        
        content_lower = content.lower()
        for pattern in feature_patterns:
            if pattern in content_lower:
                features.append(pattern.replace("_", " ").title())
        
        return features
    
    def _assess_complexity(self, content: str) -> str:
        """Assess project complexity"""
        complexity_indicators = [
            "multi-stakeholder", "real-time", "authentication", "complex scoring",
            "admin dashboard", "data export", "schema validation", "role-based",
            "analytics", "reporting", "api integration", "microservices"
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in content_lower)
        
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
        base_timeline = {
            "low": 10,
            "medium": 20,
            "high": 35
        }
        
        # Feature multipliers
        feature_multipliers = {
            "Survey Creation": 1.2,
            "Multi-Stakeholder": 1.3,
            "Scoring Engine": 1.4,
            "Admin Dashboard": 1.2,
            "Data Export": 1.1,
            "Real-Time": 1.5,
            "Authentication": 1.1
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
                "deployment": int(estimated_days * 0.1)
            }
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
            criteria.extend([
                "All core features implemented and functional",
                "System passes all quality gates",
                "Performance meets requirements",
                "Security requirements satisfied"
            ])
        
        # Add default criteria
        criteria.extend([
            "Project delivered on time",
            "Code quality standards met",
            "Documentation complete",
            "Stakeholder acceptance achieved"
        ])
        
        return criteria
    
    async def create_project_plan(self, project_analysis: Dict[str, Any], project_name: str) -> ProjectPlan:
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
            resource_allocation = self._allocate_resources(epics, project_analysis["required_agents"])
            
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
                success_metrics=project_analysis["success_criteria"]
            )
            
            # Store project plan (placeholder for memory integration)
            self.logger.info(f"Project plan created: {project_name}")
            
            return project_plan
            
        except Exception as e:
            self.logger.error(f"Error creating project plan: {e}")
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
                "Git repository initialized with proper .gitignore"
            ],
            priority="high",
            estimated_points=5,
            assigned_agents=["architect", "operations"],
            target_completion=datetime.now() + timedelta(days=2)
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
                "API structure established"
            ],
            priority="high",
            estimated_points=8,
            dependencies=["EP-001"],
            assigned_agents=["architect", "engineer"],
            target_completion=datetime.now() + timedelta(days=5)
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
                    "Progress tracking implemented"
                ],
                priority="high",
                estimated_points=13,
                dependencies=["EP-002"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=10)
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
                    "Analytics dashboard implemented"
                ],
                priority="medium",
                estimated_points=10,
                dependencies=["EP-003"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=13)
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
                    "Administrative reporting complete"
                ],
                priority="medium",
                estimated_points=8,
                dependencies=["EP-002"],
                assigned_agents=["engineer"],
                target_completion=datetime.now() + timedelta(days=15)
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
                "Security validation performed"
            ],
            priority="medium",
            estimated_points=6,
            dependencies=["EP-003", "EP-004", "EP-005"],
            assigned_agents=["qa", "engineer"],
            target_completion=datetime.now() + timedelta(days=18)
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
                "Documentation complete"
            ],
            priority="low",
            estimated_points=4,
            dependencies=["EP-006"],
            assigned_agents=["operations"],
            target_completion=datetime.now() + timedelta(days=20)
        )
        epics.append(deployment_epic)
        
        return epics
    
    def _create_project_timeline(self, project_analysis: Dict[str, Any], epics: List[Epic]) -> Dict[str, Any]:
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
                "dependencies": epic.dependencies
            }
        
        timeline["epics"] = epic_timeline
        return timeline
    
    def _allocate_resources(self, epics: List[Epic], required_agents: List[str]) -> Dict[str, List[str]]:
        """Allocate resources to epics"""
        resource_allocation = {}
        
        for epic in epics:
            resource_allocation[epic.id] = epic.assigned_agents
        
        return resource_allocation
    
    def _create_milestones(self, timeline: Dict[str, Any], epics: List[Epic]) -> List[Dict[str, Any]]:
        """Create project milestones"""
        milestones = []
        
        # Phase milestones
        milestones.append({
            "name": "Project Setup Complete",
            "description": "Initial project structure and configuration ready",
            "date": datetime.now() + timedelta(days=timeline["phases"]["setup"]),
            "criteria": ["All setup epics completed", "Development environment ready"]
        })
        
        milestones.append({
            "name": "Core Features Complete",
            "description": "All core functionality implemented and tested",
            "date": datetime.now() + timedelta(days=timeline["phases"]["setup"] + timeline["phases"]["core_development"]),
            "criteria": ["Core epics completed", "Basic functionality working"]
        })
        
        milestones.append({
            "name": "Production Ready",
            "description": "Application ready for production deployment",
            "date": datetime.now() + timedelta(days=timeline["total_days"]),
            "criteria": ["All epics completed", "Quality gates passed", "Documentation complete"]
        })
        
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
                    self.logger.warning(f"Epic {epic.id} is blocked: {epic_result.get('blocker_reason', 'Unknown')}")
                    # Handle blockers or escalate
                    await self._handle_epic_blocker(epic, epic_result)
            
            # Generate final project report
            project_status = self._generate_project_status(execution_results)
            
            return {
                "project_id": project_plan.project_id,
                "status": project_status,
                "execution_results": execution_results,
                "completion_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error orchestrating project execution: {e}")
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
            self.logger.error(f"Error creating epic ticket: {e}")
            raise
    
    def _sort_epics_by_dependencies(self, epics: List[Epic]) -> List[Epic]:
        """Sort epics by dependencies (topological sort)"""
        sorted_epics = []
        remaining_epics = epics.copy()
        
        while remaining_epics:
            # Find epics with no unresolved dependencies
            ready_epics = [
                epic for epic in remaining_epics
                if not epic.dependencies or all(
                    dep in [completed.id for completed in sorted_epics]
                    for dep in epic.dependencies
                )
            ]
            
            if not ready_epics:
                # Circular dependency or other issue
                self.logger.warning("Circular dependency detected, proceeding with remaining epics")
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
                "completion_date": datetime.now().isoformat() if status == "completed" else None
            }
            
        except Exception as e:
            self.logger.error(f"Error executing epic {epic.id}: {e}")
            return {
                "epic_id": epic.id,
                "status": "failed",
                "error": str(e),
                "agent_results": {}
            }
    
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
            self.logger.error(f"Error delegating to {agent_type}: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _simulate_architect_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate architect agent work"""
        # This would be replaced with actual architect agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["system_design", "api_specifications", "data_models"],
            "message": f"Architecture work completed for {epic.title}"
        }
    
    async def _simulate_engineer_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate engineer agent work"""
        # This would be replaced with actual engineer agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["implementation", "unit_tests", "documentation"],
            "message": f"Engineering work completed for {epic.title}"
        }
    
    async def _simulate_qa_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate QA agent work"""
        # This would be replaced with actual QA agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["test_cases", "test_execution", "quality_report"],
            "message": f"QA work completed for {epic.title}"
        }
    
    async def _simulate_operations_work(self, epic: Epic) -> Dict[str, Any]:
        """Simulate operations agent work"""
        # This would be replaced with actual operations agent calls
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "status": "completed",
            "deliverables": ["deployment_config", "monitoring_setup", "documentation"],
            "message": f"Operations work completed for {epic.title}"
        }
    
    async def _update_epic_status(self, epic_id: str, status: str) -> None:
        """Update epic status in tracking system"""
        try:
            # Placeholder for trackdown service integration
            self.logger.info(f"Epic {epic_id} status updated to {status}")
        except Exception as e:
            self.logger.error(f"Error updating epic status: {e}")
    
    async def _handle_epic_blocker(self, epic: Epic, epic_result: Dict[str, Any]) -> None:
        """Handle epic blockers"""
        blocker_reason = epic_result.get("blocker_reason", "Unknown blocker")
        
        # Log the blocker
        self.logger.warning(f"Epic {epic.id} blocked: {blocker_reason}")
        
        # Store blocker information (placeholder for memory integration)
        self.logger.warning(f"Epic blocker recorded: {epic.id} - {blocker_reason}")
        
        # Attempt to resolve or escalate
        # For now, we'll just log it
        self.logger.info(f"Escalating blocker for epic {epic.id}")
    
    def _generate_project_status(self, execution_results: Dict[str, Any]) -> str:
        """Generate overall project status"""
        completed_epics = sum(1 for result in execution_results.values() if result["status"] == "completed")
        total_epics = len(execution_results)
        failed_epics = sum(1 for result in execution_results.values() if result["status"] == "failed")
        
        if failed_epics > 0:
            return "failed"
        elif completed_epics == total_epics:
            return "completed"
        else:
            return "in_progress"
    
    async def _execute_operation(
        self, 
        operation: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
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
                raise ValueError("project_analysis and project_name required for create_project_plan")
            return await self.create_project_plan(project_analysis, project_name)
        
        elif operation == "orchestrate_project_execution":
            project_plan = kwargs.get("project_plan") or context.get("project_plan")
            if not project_plan:
                raise ValueError("project_plan required for orchestrate_project_execution")
            return await self.orchestrate_project_execution(project_plan)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")