"""
Technical Enforcement Layer (FWK-003) - Claude PM Framework Integrity System

This module implements technical enforcement mechanisms for delegation constraints
to ensure framework integrity and prevent unauthorized actions by agents.

Key Features:
- Agent permission validation based on CLAUDE.md constraints
- File access control and authorization checking
- Circular delegation detection and prevention
- Violation monitoring and reporting
- Integration with existing multi-agent orchestrator
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Agent types with specific delegation authority."""

    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA = "qa"
    RESEARCHER = "researcher"
    OPERATIONS = "operations"
    SECURITY_ENGINEER = "security_engineer"
    PERFORMANCE_ENGINEER = "performance_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    UI_UX_ENGINEER = "ui_ux_engineer"
    CODE_REVIEW_ENGINEER = "code_review_engineer"


class AgentDisplayNames:
    """Standardized display names for agents used in task prefix generation."""

    # Mapping from AgentType enum values to shortened display names
    DISPLAY_NAME_MAP = {
        AgentType.ORCHESTRATOR: "PM",
        AgentType.ARCHITECT: "Architect",
        AgentType.ENGINEER: "Engineer",
        AgentType.QA: "QA",
        AgentType.RESEARCHER: "Researcher",
        AgentType.OPERATIONS: "Ops",
        AgentType.SECURITY_ENGINEER: "Security",
        AgentType.PERFORMANCE_ENGINEER: "Performance",
        AgentType.DEVOPS_ENGINEER: "DevOps",
        AgentType.DATA_ENGINEER: "DataEng",
        AgentType.UI_UX_ENGINEER: "UIUX",
        AgentType.CODE_REVIEW_ENGINEER: "CodeReview",
    }

    # Core agent types with their display names (for framework compatibility)
    CORE_AGENT_DISPLAY_NAMES = {
        "documentation_agent": "Documenter",
        "version_control_agent": "GitAgent",
    }

    @classmethod
    def get_display_name(cls, agent_type: Union[AgentType, str]) -> str:
        """
        Get the standardized display name for an agent type.

        Args:
            agent_type: AgentType enum or string identifier

        Returns:
            Standardized display name for task prefixing
        """
        if isinstance(agent_type, AgentType):
            return cls.DISPLAY_NAME_MAP.get(agent_type, agent_type.value.title())

        # Handle string agent types (e.g., core agents)
        if isinstance(agent_type, str):
            # Check core agent mappings first
            if agent_type in cls.CORE_AGENT_DISPLAY_NAMES:
                return cls.CORE_AGENT_DISPLAY_NAMES[agent_type]

            # Try to convert to AgentType
            try:
                enum_type = AgentType(agent_type.lower())
                return cls.DISPLAY_NAME_MAP.get(enum_type, agent_type.title())
            except ValueError:
                # Fallback: format string as title case
                return agent_type.replace("_", "").title()

    @classmethod
    def get_task_prefix(cls, agent_type: Union[AgentType, str], task_description: str = "") -> str:
        """
        Generate a task prefix using the agent display name.

        Args:
            agent_type: AgentType enum or string identifier
            task_description: Optional task description for context

        Returns:
            Formatted task prefix: "[AgentName]"
        """
        display_name = cls.get_display_name(agent_type)
        return f"[{display_name}]"

    @classmethod
    def get_all_display_names(cls) -> Dict[str, str]:
        """
        Get all available agent types and their display names.

        Returns:
            Dictionary mapping agent type values to display names
        """
        result = {}

        # Add enum-based agents
        for agent_type, display_name in cls.DISPLAY_NAME_MAP.items():
            result[agent_type.value] = display_name

        # Add core agents
        result.update(cls.CORE_AGENT_DISPLAY_NAMES)

        return result


class ActionType(str, Enum):
    """Types of actions that can be performed by agents."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    CREATE = "create"
    MODIFY = "modify"


class ViolationSeverity(str, Enum):
    """Severity levels for constraint violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FileCategory(str, Enum):
    """File categories for permission enforcement."""

    SOURCE_CODE = "source_code"  # .py, .js, .ts, .java, etc.
    CONFIGURATION = "configuration"  # docker, CI/CD, deployment
    TEST_FILES = "test_files"  # .test.js, .spec.py, etc.
    DOCUMENTATION = "documentation"  # .md, .rst, .txt
    PROJECT_MANAGEMENT = "project_management"  # CLAUDE.md, BACKLOG.md, etc.
    SCAFFOLDING = "scaffolding"  # API specs, templates
    RESEARCH_DOCS = "research_docs"  # Research and analysis docs


@dataclass
class Agent:
    """Agent representation for enforcement purposes."""

    agent_id: str
    agent_type: AgentType
    project_name: Optional[str] = None
    working_directory: Optional[Path] = None
    capabilities: Set[str] = field(default_factory=set)

    def __str__(self) -> str:
        return f"{self.agent_type.value}[{self.agent_id}]"

    def get_display_name(self) -> str:
        """Get the standardized display name for this agent."""
        return AgentDisplayNames.get_display_name(self.agent_type)

    def get_task_prefix(self) -> str:
        """Get the task prefix for this agent."""
        return AgentDisplayNames.get_task_prefix(self.agent_type)


@dataclass
class Action:
    """Action representation for validation."""

    action_type: ActionType
    resource_path: Path
    agent: Agent
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.action_type.value}({self.resource_path})"


@dataclass
class AgentPermissions:
    """Permissions for a specific agent type."""

    agent_type: AgentType
    allowed_file_categories: Set[FileCategory]
    forbidden_file_categories: Set[FileCategory]
    allowed_action_types: Set[ActionType]
    can_delegate: bool = False
    max_parallel_instances: int = 1
    special_permissions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""

    violation_id: str
    agent: Agent
    action: Action
    violation_type: str
    severity: ViolationSeverity
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolution_guidance: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    agent: Agent
    action: Action
    violations: List[ConstraintViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert for violation monitoring."""

    alert_id: str
    violation: ConstraintViolation
    alert_level: ViolationSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


@dataclass
class ViolationReport:
    """Comprehensive violation report."""

    report_id: str
    start_time: datetime
    end_time: datetime
    violations: List[ConstraintViolation]
    summary: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)


class FileClassifier:
    """Classifies files into categories for permission enforcement."""

    # File extension mappings to categories (order matters - more specific patterns first)
    FILE_CATEGORY_PATTERNS = {
        FileCategory.TEST_FILES: [
            r"test_.*\.py$",
            r".*_test\.py$",
            r"\.test\.js$",
            r"\.spec\.js$",
            r"\.test\.ts$",
            r"\.spec\.ts$",
            r"^test/",
            r"^tests/",
            r"/test/",
            r"/tests/",
            r"__tests__/.*",
            r"spec/.*",
        ],
        FileCategory.PROJECT_MANAGEMENT: [
            r"^CLAUDE\.md$",
            r"^BACKLOG\.md$",
            r"^MILESTONES\.md$",
            r"trackdown/.*\.md$",
            r"\.ticket$",
            r"STATUS.*\.md$",
        ],
        FileCategory.RESEARCH_DOCS: [
            r"research/.*\.md$",
            r"analysis/.*\.md$",
            r"docs/research/.*",
            r"investigation/.*\.md$",
            r"evaluation/.*\.md$",
        ],
        FileCategory.SCAFFOLDING: [
            r"\.template$",
            r"scaffold/.*",
            r"templates/.*",
            r"api-spec/.*",
            r"openapi.*\.yml$",
            r"swagger.*\.yml$",
        ],
        FileCategory.CONFIGURATION: [
            r"docker.*",
            r"^Dockerfile$",
            r"\.yml$",
            r"\.yaml$",
            r"\.toml$",
            r"\.ini$",
            r"\.conf$",
            r"\.config$",
            r"\.env$",
            r"requirements\.txt$",
            r"package\.json$",
            r"pyproject\.toml$",
            r"^Makefile$",
            r"\.sh$",
            r"\.bat$",
            r"\.cmd$",
        ],
        FileCategory.DOCUMENTATION: [
            r"\.md$",
            r"\.rst$",
            r"\.txt$",
            r"\.doc$",
            r"\.docx$",
            r"README.*",
            r"CHANGELOG.*",
            r"LICENSE.*",
            r"CONTRIBUTING.*",
        ],
        FileCategory.SOURCE_CODE: [
            r"\.py$",
            r"\.js$",
            r"\.ts$",
            r"\.jsx$",
            r"\.tsx$",
            r"\.java$",
            r"\.cpp$",
            r"\.c$",
            r"\.h$",
            r"\.go$",
            r"\.rs$",
            r"\.php$",
            r"\.rb$",
            r"\.swift$",
            r"\.kt$",
            r"\.scala$",
            r"\.cs$",
        ],
    }

    @classmethod
    def classify_file(cls, file_path: Union[str, Path]) -> FileCategory:
        """
        Classify a file into a permission category.

        Args:
            file_path: Path to the file to classify

        Returns:
            FileCategory for the file
        """
        path_str = str(file_path).lower()

        # Check each category's patterns
        for category, patterns in cls.FILE_CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_str):
                    return category

        # Default to source code if no match
        return FileCategory.SOURCE_CODE


class AgentCapabilityManager:
    """Manages agent capabilities and permission validation."""

    def __init__(self):
        """Initialize the capability manager with CLAUDE.md constraints."""
        self.agent_permissions = self._initialize_agent_permissions()
        logger.info("AgentCapabilityManager initialized with delegation constraints")

    def _initialize_agent_permissions(self) -> Dict[AgentType, AgentPermissions]:
        """Initialize agent permissions based on CLAUDE.md constraints."""
        permissions = {}

        # Orchestrator Agent - PM tasks only, NEVER codes
        permissions[AgentType.ORCHESTRATOR] = AgentPermissions(
            agent_type=AgentType.ORCHESTRATOR,
            allowed_file_categories={
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.DOCUMENTATION,
                FileCategory.RESEARCH_DOCS,
            },
            forbidden_file_categories={
                FileCategory.SOURCE_CODE,
                FileCategory.CONFIGURATION,
                FileCategory.TEST_FILES,
                FileCategory.SCAFFOLDING,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=True,
            max_parallel_instances=1,
            special_permissions={
                "can_orchestrate": True,
                "can_create_tickets": True,
                "can_coordinate_agents": True,
            },
        )

        # Engineer Agent - ONLY source code
        permissions[AgentType.ENGINEER] = AgentPermissions(
            agent_type=AgentType.ENGINEER,
            allowed_file_categories={FileCategory.SOURCE_CODE},
            forbidden_file_categories={
                FileCategory.CONFIGURATION,
                FileCategory.TEST_FILES,
                FileCategory.DOCUMENTATION,
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.SCAFFOLDING,
                FileCategory.RESEARCH_DOCS,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=False,
            max_parallel_instances=5,  # Multiple engineers allowed
            special_permissions={"can_implement": True, "can_debug": True},
        )

        # Operations Agent - Configuration only
        permissions[AgentType.OPERATIONS] = AgentPermissions(
            agent_type=AgentType.OPERATIONS,
            allowed_file_categories={FileCategory.CONFIGURATION},
            forbidden_file_categories={
                FileCategory.SOURCE_CODE,
                FileCategory.TEST_FILES,
                FileCategory.DOCUMENTATION,
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.SCAFFOLDING,
                FileCategory.RESEARCH_DOCS,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=False,
            max_parallel_instances=1,
            special_permissions={"can_deploy": True, "can_configure": True},
        )

        # QA Agent - Tests only
        permissions[AgentType.QA] = AgentPermissions(
            agent_type=AgentType.QA,
            allowed_file_categories={FileCategory.TEST_FILES},
            forbidden_file_categories={
                FileCategory.SOURCE_CODE,
                FileCategory.CONFIGURATION,
                FileCategory.DOCUMENTATION,
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.SCAFFOLDING,
                FileCategory.RESEARCH_DOCS,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=False,
            max_parallel_instances=1,
            special_permissions={"can_test": True, "can_validate": True},
        )

        # Research Agent - Documentation only
        permissions[AgentType.RESEARCHER] = AgentPermissions(
            agent_type=AgentType.RESEARCHER,
            allowed_file_categories={FileCategory.RESEARCH_DOCS, FileCategory.DOCUMENTATION},
            forbidden_file_categories={
                FileCategory.SOURCE_CODE,
                FileCategory.CONFIGURATION,
                FileCategory.TEST_FILES,
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.SCAFFOLDING,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=False,
            max_parallel_instances=1,
            special_permissions={"can_research": True, "can_analyze": True},
        )

        # Architect Agent - Scaffolding only
        permissions[AgentType.ARCHITECT] = AgentPermissions(
            agent_type=AgentType.ARCHITECT,
            allowed_file_categories={FileCategory.SCAFFOLDING, FileCategory.DOCUMENTATION},
            forbidden_file_categories={
                FileCategory.SOURCE_CODE,
                FileCategory.CONFIGURATION,
                FileCategory.TEST_FILES,
                FileCategory.PROJECT_MANAGEMENT,
                FileCategory.RESEARCH_DOCS,
            },
            allowed_action_types={
                ActionType.READ,
                ActionType.WRITE,
                ActionType.CREATE,
                ActionType.MODIFY,
            },
            can_delegate=False,
            max_parallel_instances=1,
            special_permissions={"can_design": True, "can_architect": True},
        )

        # Specialist Engineers - Based on their specific roles
        for agent_type in [
            AgentType.SECURITY_ENGINEER,
            AgentType.PERFORMANCE_ENGINEER,
            AgentType.DEVOPS_ENGINEER,
            AgentType.DATA_ENGINEER,
            AgentType.UI_UX_ENGINEER,
            AgentType.CODE_REVIEW_ENGINEER,
        ]:
            permissions[agent_type] = AgentPermissions(
                agent_type=agent_type,
                allowed_file_categories={
                    FileCategory.SOURCE_CODE,  # Can analyze code
                    FileCategory.DOCUMENTATION,  # Can document findings
                },
                forbidden_file_categories={
                    FileCategory.PROJECT_MANAGEMENT,
                    FileCategory.SCAFFOLDING,
                },
                allowed_action_types={ActionType.READ, ActionType.WRITE, ActionType.CREATE},
                can_delegate=False,
                max_parallel_instances=1,
                special_permissions={"specialist_analysis": True},
            )

        return permissions

    def get_agent_permissions(self, agent_type: AgentType) -> AgentPermissions:
        """Get permissions for a specific agent type."""
        return self.agent_permissions.get(
            agent_type,
            AgentPermissions(
                agent_type=agent_type,
                allowed_file_categories=set(),
                forbidden_file_categories=set(),
                allowed_action_types=set(),
            ),
        )

    def validate_agent_action(self, agent: Agent, action: Action) -> ValidationResult:
        """
        Validate if an agent is authorized to perform an action.

        Args:
            agent: Agent attempting the action
            action: Action to validate

        Returns:
            ValidationResult with validation outcome
        """
        violations = []
        warnings = []

        # Get agent permissions
        permissions = self.get_agent_permissions(agent.agent_type)

        # Classify the target file
        file_category = FileClassifier.classify_file(action.resource_path)

        # Check if action type is allowed
        if action.action_type not in permissions.allowed_action_types:
            violations.append(
                ConstraintViolation(
                    violation_id=f"action-{agent.agent_id}-{datetime.now().timestamp()}",
                    agent=agent,
                    action=action,
                    violation_type="unauthorized_action_type",
                    severity=ViolationSeverity.HIGH,
                    description=f"Agent {agent.agent_type.value} is not authorized to perform {action.action_type.value} actions",
                    resolution_guidance=f"This action type should be delegated to an appropriate agent",
                )
            )

        # Check file category permissions
        if file_category in permissions.forbidden_file_categories:
            violations.append(
                ConstraintViolation(
                    violation_id=f"file-{agent.agent_id}-{datetime.now().timestamp()}",
                    agent=agent,
                    action=action,
                    violation_type="forbidden_file_access",
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Agent {agent.agent_type.value} is forbidden from accessing {file_category.value} files",
                    resolution_guidance=f"This file type should be handled by: {self._get_authorized_agents_for_category(file_category)}",
                )
            )

        elif file_category not in permissions.allowed_file_categories:
            warnings.append(
                f"Agent {agent.agent_type.value} accessing {file_category.value} files - verify authorization"
            )

        # Specific enforcement for critical constraints
        if agent.agent_type == AgentType.ORCHESTRATOR and file_category == FileCategory.SOURCE_CODE:
            violations.append(
                ConstraintViolation(
                    violation_id=f"critical-{agent.agent_id}-{datetime.now().timestamp()}",
                    agent=agent,
                    action=action,
                    violation_type="orchestrator_code_access",
                    severity=ViolationSeverity.CRITICAL,
                    description="CRITICAL VIOLATION: Orchestrator agent attempting to access source code - NEVER ALLOWED",
                    resolution_guidance="Orchestrator must delegate all code work to Engineer agents",
                )
            )

        # Make existing violations critical if they involve orchestrator and code
        for violation in violations:
            if (
                violation.violation_type == "forbidden_file_access"
                and agent.agent_type == AgentType.ORCHESTRATOR
                and file_category == FileCategory.SOURCE_CODE
            ):
                violation.severity = ViolationSeverity.CRITICAL
                violation.description = f"CRITICAL VIOLATION: {violation.description}"

        is_valid = len(violations) == 0

        return ValidationResult(
            is_valid=is_valid,
            agent=agent,
            action=action,
            violations=violations,
            warnings=warnings,
            context={
                "file_category": file_category.value,
                "permissions_checked": True,
                "agent_permissions": permissions,
            },
        )

    def check_authorization(self, agent: Agent, resource: str) -> bool:
        """
        Quick authorization check for a resource.

        Args:
            agent: Agent requesting access
            resource: Resource path or identifier

        Returns:
            True if authorized, False otherwise
        """
        action = Action(action_type=ActionType.READ, resource_path=Path(resource), agent=agent)

        result = self.validate_agent_action(agent, action)
        return result.is_valid

    def _get_authorized_agents_for_category(self, category: FileCategory) -> str:
        """Get which agents are authorized for a file category."""
        authorized = []
        for agent_type, permissions in self.agent_permissions.items():
            if category in permissions.allowed_file_categories:
                authorized.append(agent_type.value)
        return ", ".join(authorized) if authorized else "None"


class DelegationEnforcer:
    """Core enforcement engine for delegation constraints."""

    def __init__(self, capability_manager: AgentCapabilityManager):
        """Initialize the delegation enforcer."""
        self.capability_manager = capability_manager
        self.delegation_chains: Dict[str, List[Agent]] = {}
        logger.info("DelegationEnforcer initialized")

    def validate_file_access(self, agent_type: str, file_path: str) -> bool:
        """
        Validate if an agent type can access a specific file.

        Args:
            agent_type: Type of agent (string)
            file_path: Path to file being accessed

        Returns:
            True if access is allowed, False otherwise
        """
        try:
            agent_enum = AgentType(agent_type.lower())
            agent = Agent(agent_id=f"temp-{agent_type}", agent_type=agent_enum)

            return self.capability_manager.check_authorization(agent, file_path)

        except ValueError:
            logger.warning(f"Unknown agent type: {agent_type}")
            return False

    def enforce_delegation_constraints(self, agent: Agent, action: Action) -> bool:
        """
        Enforce delegation constraints for an agent action.

        Args:
            agent: Agent attempting the action
            action: Action to validate

        Returns:
            True if action is allowed, False otherwise
        """
        result = self.capability_manager.validate_agent_action(agent, action)

        if not result.is_valid:
            logger.error(f"Delegation constraint violation: {agent} -> {action}")
            for violation in result.violations:
                logger.error(f"  Violation: {violation.description}")

        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  Warning: {warning}")

        return result.is_valid

    def detect_circular_delegation(self, delegation_chain: List[Agent]) -> bool:
        """
        Detect circular delegation patterns.

        Args:
            delegation_chain: Chain of agents in delegation

        Returns:
            True if circular delegation detected, False otherwise
        """
        agent_types_seen = set()

        for agent in delegation_chain:
            if agent.agent_type in agent_types_seen:
                logger.error(
                    f"Circular delegation detected: {[a.agent_type.value for a in delegation_chain]}"
                )
                return True
            agent_types_seen.add(agent.agent_type)

        return False

    def start_delegation_chain(self, initiator: Agent, chain_id: str) -> None:
        """Start tracking a delegation chain."""
        self.delegation_chains[chain_id] = [initiator]
        logger.debug(f"Started delegation chain {chain_id} with {initiator}")

    def add_to_delegation_chain(self, chain_id: str, delegatee: Agent) -> bool:
        """
        Add an agent to a delegation chain and check for circular delegation.

        Args:
            chain_id: Delegation chain identifier
            delegatee: Agent being delegated to

        Returns:
            True if delegation is valid, False if circular
        """
        if chain_id not in self.delegation_chains:
            logger.error(f"Unknown delegation chain: {chain_id}")
            return False

        test_chain = self.delegation_chains[chain_id] + [delegatee]

        if self.detect_circular_delegation(test_chain):
            return False

        self.delegation_chains[chain_id].append(delegatee)
        logger.debug(f"Added {delegatee} to delegation chain {chain_id}")
        return True

    def end_delegation_chain(self, chain_id: str) -> Optional[List[Agent]]:
        """End and return a delegation chain."""
        return self.delegation_chains.pop(chain_id, None)


class ViolationMonitor:
    """Monitors and tracks constraint violations."""

    def __init__(self):
        """Initialize the violation monitor."""
        self.violations: List[ConstraintViolation] = []
        self.alerts: List[Alert] = []
        self.alert_counter = 0
        logger.info("ViolationMonitor initialized")

    def track_violation(self, violation: ConstraintViolation) -> None:
        """
        Track a constraint violation.

        Args:
            violation: Violation to track
        """
        self.violations.append(violation)

        # Create alert for high/critical violations
        if violation.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]:
            alert = Alert(
                alert_id=f"alert-{self.alert_counter}",
                violation=violation,
                alert_level=violation.severity,
                message=f"[{violation.severity.value.upper()}] {violation.description}",
            )
            self.alerts.append(alert)
            self.alert_counter += 1

            logger.error(f"VIOLATION ALERT: {alert.message}")

        logger.warning(f"Tracked violation: {violation.violation_type} by {violation.agent}")

    def get_violation_alerts(self) -> List[Alert]:
        """Get all unacknowledged violation alerts."""
        return [alert for alert in self.alerts if not alert.acknowledged]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Acknowledged alert: {alert_id}")
                return True
        return False

    def generate_violation_report(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> ViolationReport:
        """
        Generate a comprehensive violation report.

        Args:
            start_time: Start time for report (optional)
            end_time: End time for report (optional)

        Returns:
            ViolationReport with analysis
        """
        if start_time is None:
            start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if end_time is None:
            end_time = datetime.now()

        # Filter violations by time range
        filtered_violations = [v for v in self.violations if start_time <= v.timestamp <= end_time]

        # Generate summary statistics
        summary = {
            "total_violations": len(filtered_violations),
            "by_severity": {},
            "by_agent_type": {},
            "by_violation_type": {},
            "most_common_violations": [],
        }

        # Aggregate by severity
        for violation in filtered_violations:
            severity = violation.severity.value
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

        # Aggregate by agent type
        for violation in filtered_violations:
            agent_type = violation.agent.agent_type.value
            summary["by_agent_type"][agent_type] = summary["by_agent_type"].get(agent_type, 0) + 1

        # Aggregate by violation type
        for violation in filtered_violations:
            vtype = violation.violation_type
            summary["by_violation_type"][vtype] = summary["by_violation_type"].get(vtype, 0) + 1

        # Generate recommendations
        recommendations = []
        if summary["by_severity"].get("critical", 0) > 0:
            recommendations.append("URGENT: Address critical violations immediately")
        if summary["by_agent_type"].get("orchestrator", 0) > 0:
            recommendations.append("Review orchestrator delegation patterns")
        if summary["total_violations"] > 10:
            recommendations.append("Consider additional agent training on delegation constraints")

        return ViolationReport(
            report_id=f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            start_time=start_time,
            end_time=end_time,
            violations=filtered_violations,
            summary=summary,
            recommendations=recommendations,
        )

    def get_critical_violations(self) -> List[ConstraintViolation]:
        """Get all critical violations."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]


class EnforcementEngine:
    """Main enforcement engine that coordinates all enforcement components."""

    def __init__(self):
        """Initialize the enforcement engine."""
        self.capability_manager = AgentCapabilityManager()
        self.delegation_enforcer = DelegationEnforcer(self.capability_manager)
        self.violation_monitor = ViolationMonitor()
        self.enabled = True
        logger.info("EnforcementEngine initialized - Framework integrity protection active")

    def validate_action(self, agent: Agent, action: Action) -> ValidationResult:
        """
        Validate an agent action through the complete enforcement pipeline.

        Args:
            agent: Agent attempting the action
            action: Action to validate

        Returns:
            ValidationResult with complete validation
        """
        if not self.enabled:
            return ValidationResult(is_valid=True, agent=agent, action=action)

        # Validate through capability manager
        result = self.capability_manager.validate_agent_action(agent, action)

        # Track violations
        for violation in result.violations:
            self.violation_monitor.track_violation(violation)

        # Log enforcement action
        if result.is_valid:
            logger.debug(f"Action authorized: {agent} -> {action}")
        else:
            logger.error(f"Action DENIED: {agent} -> {action}")
            logger.error(f"Violations: {[v.description for v in result.violations]}")

        return result

    def enforce_file_access(
        self, agent_type: str, file_path: str, action_type: str = "read"
    ) -> bool:
        """
        Convenience method for file access enforcement.

        Args:
            agent_type: Type of agent as string
            file_path: Path to file
            action_type: Type of action (read, write, etc.)

        Returns:
            True if access allowed, False otherwise
        """
        try:
            agent_enum = AgentType(agent_type.lower())
            action_enum = ActionType(action_type.lower())

            agent = Agent(agent_id=f"enforce-{agent_type}", agent_type=agent_enum)
            action = Action(action_type=action_enum, resource_path=Path(file_path), agent=agent)

            result = self.validate_action(agent, action)
            return result.is_valid

        except (ValueError, Exception) as e:
            logger.error(f"Enforcement error: {e}")
            return False

    def get_enforcement_stats(self) -> Dict[str, Any]:
        """Get comprehensive enforcement statistics."""
        recent_violations = self.violation_monitor.violations[-10:]  # Last 10
        alerts = self.violation_monitor.get_violation_alerts()

        return {
            "enforcement_enabled": self.enabled,
            "total_violations": len(self.violation_monitor.violations),
            "active_alerts": len(alerts),
            "critical_violations": len(self.violation_monitor.get_critical_violations()),
            "recent_violations": [
                {
                    "agent": str(v.agent),
                    "violation_type": v.violation_type,
                    "severity": v.severity.value,
                    "timestamp": v.timestamp.isoformat(),
                }
                for v in recent_violations
            ],
            "delegation_chains_active": len(self.delegation_enforcer.delegation_chains),
        }

    def generate_daily_report(self) -> ViolationReport:
        """Generate daily violation report."""
        return self.violation_monitor.generate_violation_report()

    def enable_enforcement(self) -> None:
        """Enable enforcement engine."""
        self.enabled = True
        logger.info("Enforcement engine ENABLED - Framework protection active")

    def disable_enforcement(self) -> None:
        """Disable enforcement engine (for testing/debugging)."""
        self.enabled = False
        logger.warning("Enforcement engine DISABLED - Framework protection inactive")


# Global enforcement engine instance
_enforcement_engine: Optional[EnforcementEngine] = None


def get_enforcement_engine() -> EnforcementEngine:
    """Get the global enforcement engine instance."""
    global _enforcement_engine
    if _enforcement_engine is None:
        _enforcement_engine = EnforcementEngine()
    return _enforcement_engine


def enforce_file_access(agent_type: str, file_path: str, action_type: str = "read") -> bool:
    """
    Convenience function for file access enforcement.

    Args:
        agent_type: Type of agent as string
        file_path: Path to file
        action_type: Type of action

    Returns:
        True if access allowed, False otherwise
    """
    engine = get_enforcement_engine()
    return engine.enforce_file_access(agent_type, file_path, action_type)


def validate_agent_action(
    agent_type: str, action_type: str, resource_path: str, agent_id: str = None
) -> ValidationResult:
    """
    Convenience function for agent action validation.

    Args:
        agent_type: Type of agent as string
        action_type: Type of action as string
        resource_path: Path to resource
        agent_id: Optional agent ID

    Returns:
        ValidationResult with validation outcome
    """
    try:
        agent_enum = AgentType(agent_type.lower())
        action_enum = ActionType(action_type.lower())

        agent = Agent(agent_id=agent_id or f"validate-{agent_type}", agent_type=agent_enum)
        action = Action(action_type=action_enum, resource_path=Path(resource_path), agent=agent)

        engine = get_enforcement_engine()
        return engine.validate_action(agent, action)

    except (ValueError, Exception) as e:
        logger.error(f"Validation error: {e}")
        # Return failed validation
        dummy_agent = Agent(agent_id="error", agent_type=AgentType.ORCHESTRATOR)
        dummy_action = Action(
            action_type=ActionType.READ, resource_path=Path(resource_path), agent=dummy_agent
        )
        return ValidationResult(
            is_valid=False,
            agent=dummy_agent,
            action=dummy_action,
            violations=[
                ConstraintViolation(
                    violation_id="validation-error",
                    agent=dummy_agent,
                    action=dummy_action,
                    violation_type="validation_error",
                    severity=ViolationSeverity.HIGH,
                    description=f"Validation error: {str(e)}",
                )
            ],
        )
