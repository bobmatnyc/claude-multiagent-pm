"""
Claude PM Framework Models Package.

Contains data models for health monitoring, service management,
agent definitions, and other core framework components.
"""

from .health import (
    HealthStatus,
    HealthReport,
    HealthDashboard,
    ServiceHealthReport,
    SubsystemHealth,
)

from .agent_definition import (
    AgentDefinition,
    AgentMetadata,
    AgentType,
    AgentSection,
    AgentWorkflow,
    AgentPermissions,
)

__all__ = [
    # Health models
    "HealthStatus",
    "HealthReport",
    "HealthDashboard",
    "ServiceHealthReport",
    "SubsystemHealth",
    # Agent models
    "AgentDefinition",
    "AgentMetadata",
    "AgentType",
    "AgentSection",
    "AgentWorkflow",
    "AgentPermissions",
]
