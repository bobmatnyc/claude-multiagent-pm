"""
Agent Fixtures for E2E Testing

Provides pre-configured agent fixtures and mock agents for testing.
"""

from typing import Dict, Any, List
from pathlib import Path
import json


class AgentFixtures:
    """Collection of agent fixtures for testing."""
    
    @staticmethod
    def documentation_agent() -> Dict[str, Any]:
        """Create a documentation agent fixture."""
        return {
            "name": "documentation",
            "type": "core",
            "specializations": ["documentation", "changelog", "versioning"],
            "content": """# Documentation Agent

## Role
Handles all documentation operations including changelog generation and version analysis.

## Capabilities
- Analyze documentation patterns
- Generate changelogs from git commits
- Determine semantic version impacts
- Update version-related documentation

## Authority
- ALL documentation operations
- Changelog generation and management
- Version documentation updates

## Integration Points
- Works with Version Control Agent for git operations
- Coordinates with QA Agent for release validation
"""
        }
    
    @staticmethod
    def qa_agent() -> Dict[str, Any]:
        """Create a QA agent fixture."""
        return {
            "name": "qa",
            "type": "core", 
            "specializations": ["testing", "validation", "quality"],
            "content": """# QA Agent

## Role
Ensures quality through comprehensive testing and validation.

## Capabilities
- Execute test suites
- Validate code quality
- Perform integration testing
- Check deployment readiness

## Authority
- ALL testing operations
- Quality gate enforcement
- Test report generation

## Integration Points
- Validates Engineer Agent implementations
- Coordinates with Documentation Agent for test docs
- Works with Ops Agent for deployment validation
"""
        }
    
    @staticmethod
    def engineer_agent() -> Dict[str, Any]:
        """Create an engineer agent fixture."""
        return {
            "name": "engineer",
            "type": "core",
            "specializations": ["implementation", "development", "coding"],
            "content": """# Engineer Agent

## Role
Implements code changes and handles all development tasks.

## Capabilities
- Write and modify code
- Create inline documentation
- Implement features and fixes
- Ensure code standards

## Authority
- ALL code implementation
- Inline documentation creation
- Code structure decisions

## Integration Points
- Receives specs from Documentation Agent
- Code validated by QA Agent
- Coordinates with Version Control Agent
"""
        }
    
    @staticmethod
    def custom_agent(name: str, specializations: List[str], 
                     capabilities: List[str]) -> Dict[str, Any]:
        """Create a custom agent fixture."""
        return {
            "name": name,
            "type": "custom",
            "specializations": specializations,
            "content": f"""# {name.title()} Agent

## Role
Custom agent for {', '.join(specializations)} operations.

## Capabilities
{chr(10).join(f'- {cap}' for cap in capabilities)}

## Authority
- Domain-specific operations
- Specialized task execution

## Integration Points
- Coordinates with core agents as needed
- Provides specialized functionality
"""
        }
    
    @staticmethod
    def create_agent_registry_entry(agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent registry entry from agent data."""
        return {
            "id": agent_data["name"],
            "type": agent_data["type"],
            "path": f".claude-pm/agents/{agent_data['name']}.md",
            "specializations": agent_data.get("specializations", []),
            "last_modified": "2025-07-19T12:00:00Z",
            "metadata": {
                "version": "1.0.0",
                "active": True,
                "priority": 1 if agent_data["type"] == "core" else 2
            }
        }
    
    @staticmethod
    def create_mock_agent_file(agent_dir: Path, agent_data: Dict[str, Any]) -> Path:
        """Create a mock agent file from agent data."""
        agent_file = agent_dir / f"{agent_data['name']}.md"
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        agent_file.write_text(agent_data["content"])
        return agent_file
    
    @staticmethod
    def all_core_agents() -> List[Dict[str, Any]]:
        """Get all core agent fixtures."""
        return [
            AgentFixtures.documentation_agent(),
            AgentFixtures.qa_agent(),
            AgentFixtures.engineer_agent(),
            {
                "name": "version_control",
                "type": "core",
                "specializations": ["git", "versioning", "branching"],
                "content": """# Version Control Agent

## Role
Manages all Git operations and version control tasks.

## Capabilities
- Git operations (commit, branch, merge)
- Version management
- Branch lifecycle management
- Tag creation and management

## Authority
- ALL Git operations
- Version control decisions
"""
            },
            {
                "name": "research",
                "type": "core",
                "specializations": ["investigation", "analysis", "research"],
                "content": """# Research Agent

## Role
Conducts research and investigation tasks.

## Capabilities
- Investigate technologies
- Analyze codebases
- Research best practices
- Gather requirements

## Authority
- Research operations
- Analysis decisions
"""
            },
            {
                "name": "ops",
                "type": "core",
                "specializations": ["deployment", "operations", "infrastructure"],
                "content": """# Ops Agent

## Role
Handles deployment and operational tasks.

## Capabilities
- Deploy applications
- Manage infrastructure
- Monitor systems
- Handle operations

## Authority
- ALL deployment operations
- Infrastructure decisions
"""
            },
            {
                "name": "security",
                "type": "core",
                "specializations": ["security", "vulnerability", "compliance"],
                "content": """# Security Agent

## Role
Ensures security and compliance.

## Capabilities
- Security analysis
- Vulnerability assessment
- Compliance checking
- Security recommendations

## Authority
- ALL security decisions
- Vulnerability management
"""
            },
            {
                "name": "ticketing",
                "type": "core",
                "specializations": ["tickets", "issues", "tracking"],
                "content": """# Ticketing Agent

## Role
Manages tickets and issue tracking.

## Capabilities
- Create and update tickets
- Track issue lifecycle
- Generate reports
- Manage workflows

## Authority
- ALL ticket operations
- Issue tracking decisions
"""
            },
            {
                "name": "data_engineer",
                "type": "core",
                "specializations": ["data", "database", "api"],
                "content": """# Data Engineer Agent

## Role
Manages data operations and API integrations.

## Capabilities
- Database management
- API integrations
- Data pipeline design
- Performance optimization

## Authority
- ALL data operations
- API management decisions
"""
            }
        ]