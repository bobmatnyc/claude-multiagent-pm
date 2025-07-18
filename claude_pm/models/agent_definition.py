#!/usr/bin/env python3
"""
Agent Definition Models
======================

Data models for representing agent definitions with structured sections.
Supports version tracking and section management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Agent type categories."""
    CORE = "core"
    SPECIALIZED = "specialized"
    PROJECT = "project"
    USER = "user"


class AgentSection(str, Enum):
    """Standard agent markdown sections."""
    PRIMARY_ROLE = "Primary Role"
    WHEN_TO_USE = "When to Use This Agent"
    CAPABILITIES = "Core Capabilities"
    AUTHORITY = "Authority & Permissions"
    WORKFLOWS = "Agent-Specific Workflows"
    ESCALATION = "Unique Escalation Triggers"
    KPI = "Key Performance Indicators"
    DEPENDENCIES = "Critical Dependencies"
    TOOLS = "Specialized Tools/Commands"


@dataclass
class AgentMetadata:
    """Agent metadata from frontmatter and footer."""
    type: AgentType = AgentType.CORE
    model_preference: str = "claude-3-sonnet"
    version: str = "1.0.0"
    last_updated: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    
    def increment_serial_version(self) -> str:
        """Increment the serial (patch) version number."""
        parts = self.version.split('.')
        if len(parts) == 3:
            major, minor, serial = parts
            try:
                new_serial = int(serial) + 1
                self.version = f"{major}.{minor}.{new_serial}"
            except ValueError:
                # If serial is not a number, just append .1
                self.version = f"{self.version}.1"
        else:
            # Invalid version format, reset to 1.0.1
            self.version = "1.0.1"
        return self.version


@dataclass
class AgentWorkflow:
    """Represents a single agent workflow."""
    name: str
    trigger: str
    process: List[str]
    output: str
    raw_yaml: Optional[str] = None


@dataclass
class AgentPermissions:
    """Agent permissions structure."""
    exclusive_write_access: List[str] = field(default_factory=list)
    forbidden_operations: List[str] = field(default_factory=list)
    read_access: List[str] = field(default_factory=list)


@dataclass
class AgentDefinition:
    """Complete agent definition with all sections."""
    # Core identification
    name: str
    title: str
    file_path: str
    
    # Metadata
    metadata: AgentMetadata
    
    # Content sections
    primary_role: str
    when_to_use: Dict[str, List[str]] = field(default_factory=dict)  # {"select": [...], "do_not_select": [...]}
    capabilities: List[str] = field(default_factory=list)
    authority: AgentPermissions = field(default_factory=AgentPermissions)
    workflows: List[AgentWorkflow] = field(default_factory=list)
    escalation_triggers: List[str] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools_commands: str = ""
    
    # Raw content for preservation
    raw_content: str = ""
    raw_sections: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "title": self.title,
            "file_path": self.file_path,
            "metadata": {
                "type": self.metadata.type.value,
                "model_preference": self.metadata.model_preference,
                "version": self.metadata.version,
                "last_updated": self.metadata.last_updated.isoformat() if self.metadata.last_updated else None,
                "author": self.metadata.author,
                "tags": self.metadata.tags,
                "specializations": self.metadata.specializations
            },
            "primary_role": self.primary_role,
            "when_to_use": self.when_to_use,
            "capabilities": self.capabilities,
            "authority": {
                "exclusive_write_access": self.authority.exclusive_write_access,
                "forbidden_operations": self.authority.forbidden_operations,
                "read_access": self.authority.read_access
            },
            "workflows": [
                {
                    "name": w.name,
                    "trigger": w.trigger,
                    "process": w.process,
                    "output": w.output
                } for w in self.workflows
            ],
            "escalation_triggers": self.escalation_triggers,
            "kpis": self.kpis,
            "dependencies": self.dependencies,
            "tools_commands": self.tools_commands
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDefinition":
        """Create from dictionary representation."""
        metadata = AgentMetadata(
            type=AgentType(data["metadata"]["type"]),
            model_preference=data["metadata"]["model_preference"],
            version=data["metadata"]["version"],
            last_updated=datetime.fromisoformat(data["metadata"]["last_updated"]) 
                if data["metadata"].get("last_updated") else None,
            author=data["metadata"].get("author"),
            tags=data["metadata"].get("tags", []),
            specializations=data["metadata"].get("specializations", [])
        )
        
        authority = AgentPermissions(
            exclusive_write_access=data["authority"].get("exclusive_write_access", []),
            forbidden_operations=data["authority"].get("forbidden_operations", []),
            read_access=data["authority"].get("read_access", [])
        )
        
        workflows = [
            AgentWorkflow(
                name=w["name"],
                trigger=w["trigger"],
                process=w["process"],
                output=w["output"]
            ) for w in data.get("workflows", [])
        ]
        
        return cls(
            name=data["name"],
            title=data["title"],
            file_path=data["file_path"],
            metadata=metadata,
            primary_role=data["primary_role"],
            when_to_use=data.get("when_to_use", {}),
            capabilities=data.get("capabilities", []),
            authority=authority,
            workflows=workflows,
            escalation_triggers=data.get("escalation_triggers", []),
            kpis=data.get("kpis", []),
            dependencies=data.get("dependencies", []),
            tools_commands=data.get("tools_commands", "")
        )