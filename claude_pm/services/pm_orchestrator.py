"""
PM Orchestrator Integration - Agent Prompt Builder Integration
============================================================

This module provides seamless integration between the PM orchestrator and the agent prompt builder,
enabling automatic prompt generation for Task Tool subprocess delegation.

Key Features:
- Automatic agent prompt generation from three-tier hierarchy
- Task Tool compatibility layer
- Memory collection integration
- Hierarchy precedence resolution
- Real-time prompt building for PM delegation

Usage Example:
    from claude_pm.services.pm_orchestrator import PMOrchestrator
    
    # Initialize orchestrator
    orchestrator = PMOrchestrator()
    
    # Generate prompt for Task Tool delegation
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Implement JWT authentication system",
        requirements=["Security best practices", "Token expiration handling"],
        deliverables=["Working auth system", "Unit tests", "Documentation"]
    )
    
    # Use prompt directly with Task Tool
    # (prompt is ready for subprocess creation)
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Add the scripts directory to the path so we can import agent_prompt_builder
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

# Import SharedPromptCache for performance optimization
try:
    from .shared_prompt_cache import SharedPromptCache
    SHARED_CACHE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SharedPromptCache not available: {e}")
    SHARED_CACHE_AVAILABLE = False

try:
    from agent_prompt_builder import AgentPromptBuilder, TaskContext, AgentProfile, AgentTier
except ImportError as e:
    logging.error(f"Failed to import agent_prompt_builder: {e}")
    # Fallback minimal implementation
    class AgentPromptBuilder:
        def __init__(self, working_directory=None):
            self.working_directory = Path(working_directory or os.getcwd())
        
        def build_task_tool_prompt(self, agent_name: str, task_context: Any) -> str:
            return f"**{agent_name.title()}**: {task_context.description} + MEMORY COLLECTION REQUIRED"
    
    class TaskContext:
        def __init__(self, description: str, **kwargs):
            self.description = description
            for k, v in kwargs.items():
                setattr(self, k, v)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentDelegationContext:
    """Context for agent delegation with PM orchestrator integration."""
    agent_type: str
    task_description: str
    temporal_context: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: str = "medium"
    memory_categories: List[str] = field(default_factory=list)
    integration_notes: str = ""
    escalation_triggers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default temporal context if not provided."""
        if not self.temporal_context:
            self.temporal_context = f"Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution and PM coordination."


class PMOrchestrator:
    """
    PM Orchestrator with Agent Prompt Builder Integration
    
    Provides seamless integration between PM orchestrator functionality and
    the agent prompt builder for automated Task Tool subprocess delegation.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize PM orchestrator with agent prompt builder integration."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.agent_builder = AgentPromptBuilder(self.working_directory)
        self._delegation_history: List[Dict[str, Any]] = []
        self._active_delegations: Dict[str, AgentDelegationContext] = {}
        
        # Initialize shared cache for delegation optimization
        self._shared_cache = None
        if SHARED_CACHE_AVAILABLE:
            try:
                self._shared_cache = SharedPromptCache.get_instance({
                    "max_size": 200,  # Smaller cache for delegation data
                    "max_memory_mb": 20,  # 20MB memory limit
                    "default_ttl": 900,  # 15 minutes TTL for delegation data
                    "enable_metrics": True
                })
                logger.info("PMOrchestrator: SharedPromptCache integration enabled")
            except Exception as e:
                logger.warning(f"PMOrchestrator: Failed to initialize SharedPromptCache: {e}")
                self._shared_cache = None
        
        logger.info(f"PMOrchestrator initialized with working directory: {self.working_directory}")
        logger.info(f"  Shared cache: {'enabled' if self._shared_cache else 'disabled'}")
    
    def generate_agent_prompt(
        self,
        agent_type: str,
        task_description: str,
        requirements: Optional[List[str]] = None,
        deliverables: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        priority: str = "medium",
        memory_categories: Optional[List[str]] = None,
        integration_notes: str = "",
        escalation_triggers: Optional[List[str]] = None
    ) -> str:
        """
        Generate a complete Task Tool prompt for agent delegation.
        
        Args:
            agent_type: Type of agent to delegate to (e.g., 'engineer', 'documentation')
            task_description: Clear description of the task
            requirements: List of specific requirements
            deliverables: List of expected deliverables
            dependencies: List of task dependencies
            priority: Task priority (low, medium, high)
            memory_categories: Memory categories for collection
            integration_notes: Additional integration context
            escalation_triggers: Conditions for escalation back to PM
            
        Returns:
            Complete Task Tool prompt ready for subprocess creation
        """
        try:
            # Check shared cache for similar delegations
            delegation_cache_key = None
            if self._shared_cache:
                import hashlib
                cache_input = f"{agent_type}:{task_description}:{str(requirements)}:{str(deliverables)}"
                cache_hash = hashlib.md5(cache_input.encode()).hexdigest()[:12]
                delegation_cache_key = f"delegation_prompt:{agent_type}:{cache_hash}"
                
                cached_prompt = self._shared_cache.get(delegation_cache_key)
                if cached_prompt:
                    logger.debug(f"Retrieved cached delegation prompt for {agent_type}")
                    return cached_prompt
            
            # Create delegation context
            delegation_context = AgentDelegationContext(
                agent_type=agent_type,
                task_description=task_description,
                requirements=requirements or [],
                deliverables=deliverables or [],
                dependencies=dependencies or [],
                priority=priority,
                memory_categories=memory_categories or [],
                integration_notes=integration_notes,
                escalation_triggers=escalation_triggers or []
            )
            
            # Create task context for agent prompt builder
            task_context = TaskContext(
                description=task_description,
                temporal_context=delegation_context.temporal_context,
                specific_requirements=delegation_context.requirements,
                expected_deliverables=delegation_context.deliverables,
                dependencies=delegation_context.dependencies,
                priority=delegation_context.priority,
                memory_categories=delegation_context.memory_categories
            )
            
            # Generate base prompt using agent prompt builder
            base_prompt = self.agent_builder.build_task_tool_prompt(agent_type, task_context)
            
            # Enhance prompt with PM orchestrator integration
            enhanced_prompt = self._enhance_prompt_with_pm_integration(
                base_prompt, delegation_context
            )
            
            # Track delegation
            delegation_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._active_delegations[delegation_id] = delegation_context
            
            # Add to history
            self._delegation_history.append({
                "delegation_id": delegation_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "timestamp": datetime.now().isoformat(),
                "status": "delegated"
            })
            
            logger.info(f"Generated prompt for {agent_type} delegation: {delegation_id}")
            
            # Cache the generated prompt if shared cache is available
            if self._shared_cache and delegation_cache_key:
                self._shared_cache.set(delegation_cache_key, enhanced_prompt, ttl=900)  # 15 minutes
                logger.debug(f"Cached delegation prompt for {agent_type}")
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error generating agent prompt: {e}")
            # Return a basic fallback prompt
            return f"""**{agent_type.title()}**: {task_description} + MEMORY COLLECTION REQUIRED

TEMPORAL CONTEXT: Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.

**Task**: {task_description}

**Requirements**:
{chr(10).join(f"- {req}" for req in (requirements or []))}

**Expected Deliverables**:
{chr(10).join(f"- {deliverable}" for deliverable in (deliverables or []))}

**Authority**: {agent_type.title()} operations + memory collection
**Memory Categories**: {', '.join(memory_categories or ['bug', 'feedback', 'architecture:design'])}
**Priority**: {priority}

**Error Note**: Basic fallback prompt used due to builder error: {str(e)}
"""
    
    def _enhance_prompt_with_pm_integration(
        self, 
        base_prompt: str, 
        delegation_context: AgentDelegationContext
    ) -> str:
        """Enhance base prompt with PM orchestrator integration features."""
        
        # Add PM integration section
        pm_integration_section = f"""
**PM Orchestrator Integration**:
- **Delegation ID**: {delegation_context.agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}
- **PM Coordination**: Report progress and escalate issues back to PM orchestrator
- **Cross-Agent Workflow**: This task may integrate with other agent outputs
- **Integration Notes**: {delegation_context.integration_notes or "Standard PM workflow integration"}

**Escalation Triggers**:
{chr(10).join(f"- {trigger}" for trigger in delegation_context.escalation_triggers) if delegation_context.escalation_triggers else "- Task completion issues or blockers"}
{chr(10).join(f"- {trigger}" for trigger in ["Required dependencies unavailable", "Quality standards not achievable", "Timeline conflicts"])}

**PM Workflow Integration**:
- **Task Completion**: Mark task as complete and report results to PM
- **Progress Updates**: Provide regular status updates for PM coordination
- **Resource Conflicts**: Escalate any resource or dependency conflicts
- **Quality Validation**: Ensure deliverables meet PM quality standards
"""
        
        # Insert PM integration section before the final profile note
        if "**Profile-Enhanced Context**:" in base_prompt:
            parts = base_prompt.split("**Profile-Enhanced Context**:")
            enhanced_prompt = parts[0] + pm_integration_section + "\n**Profile-Enhanced Context**:" + parts[1]
        else:
            enhanced_prompt = base_prompt + pm_integration_section
        
        return enhanced_prompt
    
    def get_delegation_status(self, delegation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of active delegations."""
        if delegation_id:
            return {
                "delegation_id": delegation_id,
                "context": self._active_delegations.get(delegation_id),
                "active": delegation_id in self._active_delegations
            }
        
        return {
            "active_delegations": len(self._active_delegations),
            "total_delegations": len(self._delegation_history),
            "active_agents": list(set(ctx.agent_type for ctx in self._active_delegations.values())),
            "recent_delegations": self._delegation_history[-5:] if self._delegation_history else []
        }
    
    def complete_delegation(self, delegation_id: str, results: Dict[str, Any]) -> bool:
        """Mark delegation as complete and process results."""
        if delegation_id in self._active_delegations:
            # Update delegation history
            for entry in self._delegation_history:
                if entry["delegation_id"] == delegation_id:
                    entry["status"] = "completed"
                    entry["completion_time"] = datetime.now().isoformat()
                    entry["results"] = results
                    break
            
            # Remove from active delegations
            del self._active_delegations[delegation_id]
            
            logger.info(f"Completed delegation: {delegation_id}")
            return True
        
        return False
    
    def list_available_agents(self) -> Dict[str, List[str]]:
        """List all available agents from the agent prompt builder."""
        try:
            return {
                tier.value: agents 
                for tier, agents in self.agent_builder.list_available_agents().items()
            }
        except Exception as e:
            logger.error(f"Error listing available agents: {e}")
            return {
                "system": ["engineer", "documentation", "qa", "ops", "security", "research"],
                "user": [],
                "project": []
            }
    
    def validate_agent_hierarchy(self) -> Dict[str, Any]:
        """Validate agent hierarchy for PM orchestrator integration."""
        try:
            validation_results = self.agent_builder.validate_hierarchy()
            
            # Add PM orchestrator specific validations
            validation_results["pm_integration"] = {
                "active_delegations": len(self._active_delegations),
                "builder_available": hasattr(self.agent_builder, 'build_task_tool_prompt'),
                "working_directory": str(self.working_directory),
                "hierarchy_accessible": True
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating agent hierarchy: {e}")
            return {
                "valid": False,
                "issues": [f"Hierarchy validation failed: {str(e)}"],
                "pm_integration": {
                    "active_delegations": len(self._active_delegations),
                    "builder_available": False,
                    "working_directory": str(self.working_directory),
                    "hierarchy_accessible": False
                }
            }
    
    def create_agent_deployment_structure(self) -> Dict[str, bool]:
        """Create agent deployment structure for PM orchestrator."""
        try:
            return self.agent_builder.create_deployment_structure()
        except Exception as e:
            logger.error(f"Error creating deployment structure: {e}")
            return {"deployment_failed": False}
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics from both agent builder and PM orchestrator."""
        metrics = {
            "pm_orchestrator_cache_available": self._shared_cache is not None,
            "pm_orchestrator_cache_metrics": None,
            "agent_builder_cache_metrics": None
        }
        
        # Get PM orchestrator cache metrics
        if self._shared_cache:
            metrics["pm_orchestrator_cache_metrics"] = self._shared_cache.get_metrics()
        
        # Get agent builder cache metrics
        try:
            metrics["agent_builder_cache_metrics"] = self.agent_builder.get_cache_metrics()
        except Exception as e:
            logger.warning(f"Failed to get agent builder cache metrics: {e}")
        
        return metrics
    
    def invalidate_cache(self, agent_type: Optional[str] = None, pattern: Optional[str] = None) -> None:
        """
        Invalidate cache entries for specific agent type or pattern.
        
        Args:
            agent_type: Specific agent type to invalidate
            pattern: Pattern to match for invalidation
        """
        if self._shared_cache:
            if pattern:
                invalidated = self._shared_cache.invalidate(pattern)
                logger.info(f"Invalidated {invalidated} cache entries matching pattern: {pattern}")
            elif agent_type:
                invalidated = self._shared_cache.invalidate(f"delegation_prompt:{agent_type}:*")
                logger.info(f"Invalidated {invalidated} delegation cache entries for agent: {agent_type}")
            else:
                invalidated = self._shared_cache.invalidate("delegation_prompt:*")
                logger.info(f"Invalidated {invalidated} delegation cache entries")
        
        # Also invalidate agent builder cache
        try:
            self.agent_builder.invalidate_cache(agent_type)
        except Exception as e:
            logger.warning(f"Failed to invalidate agent builder cache: {e}")
    
    def get_agent_profile_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent profile."""
        try:
            profile = self.agent_builder.load_agent_profile(agent_type)
            if profile:
                return {
                    "name": profile.name,
                    "tier": profile.tier.value,
                    "role": profile.role,
                    "nickname": profile.nickname,
                    "capabilities": profile.capabilities,
                    "authority_scope": profile.authority_scope,
                    "profile_path": str(profile.path),
                    "profile_id": profile.profile_id
                }
            return None
        except Exception as e:
            logger.error(f"Error getting agent profile info: {e}")
            return None


# Helper functions for easy PM orchestrator integration
def quick_delegate(
    agent_type: str,
    task_description: str,
    requirements: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    working_directory: Optional[Path] = None
) -> str:
    """
    Quick delegation helper for PM orchestrator.
    
    Args:
        agent_type: Type of agent to delegate to
        task_description: Task description
        requirements: List of requirements
        deliverables: List of expected deliverables
        working_directory: Working directory path
        
    Returns:
        Complete Task Tool prompt ready for subprocess creation
    """
    orchestrator = PMOrchestrator(working_directory)
    return orchestrator.generate_agent_prompt(
        agent_type=agent_type,
        task_description=task_description,
        requirements=requirements,
        deliverables=deliverables
    )


def create_shortcut_prompts() -> Dict[str, str]:
    """Create shortcut prompts for common PM orchestrator operations."""
    orchestrator = PMOrchestrator()
    
    shortcuts = {
        "push": orchestrator.generate_agent_prompt(
            agent_type="documentation",
            task_description="Generate changelog and analyze semantic versioning impact for push operation",
            requirements=["Analyze git commit history", "Determine version bump needed"],
            deliverables=["Changelog content", "Version bump recommendation", "Release notes"]
        ),
        "deploy": orchestrator.generate_agent_prompt(
            agent_type="ops",
            task_description="Execute local deployment operations with validation",
            requirements=["Deploy framework files", "Validate deployment"],
            deliverables=["Deployment status report", "Validation results"]
        ),
        "test": orchestrator.generate_agent_prompt(
            agent_type="qa",
            task_description="Execute comprehensive test suite and validation",
            requirements=["Run all tests", "Validate quality standards"],
            deliverables=["Test results", "Quality validation report"]
        )
    }
    
    return shortcuts


# Memory collection helper for PM orchestrator
def collect_pm_orchestrator_memory(
    category: str,
    content: str,
    priority: str = "medium",
    delegation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect memory for PM orchestrator operations.
    
    Args:
        category: Memory category (bug, feedback, architecture:design, etc.)
        content: Memory content
        priority: Priority level (low, medium, high, critical)
        delegation_id: Optional delegation ID for context
        
    Returns:
        Memory collection result
    """
    memory_entry = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "priority": priority,
        "content": content,
        "source_agent": "pm_orchestrator",
        "project_context": str(Path.cwd()),
        "delegation_id": delegation_id,
        "metadata": {
            "integration_type": "pm_orchestrator",
            "framework_version": "012"
        }
    }
    
    # TODO: Integrate with actual memory collection system
    logger.info(f"PM Orchestrator memory collected: {category} - {content[:50]}...")
    
    return {
        "success": True,
        "memory_id": f"pm_orch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "entry": memory_entry
    }


if __name__ == "__main__":
    # Test the PM orchestrator integration
    orchestrator = PMOrchestrator()
    
    # Test agent prompt generation
    prompt = orchestrator.generate_agent_prompt(
        agent_type="engineer",
        task_description="Test PM orchestrator integration",
        requirements=["Create test functions", "Verify functionality"],
        deliverables=["Working test suite", "Integration validation"]
    )
    
    print("Generated Task Tool Prompt:")
    print("=" * 50)
    print(prompt)
    
    # Test status tracking
    status = orchestrator.get_delegation_status()
    print(f"\nDelegation Status: {status}")
    
    # Test agent listing
    agents = orchestrator.list_available_agents()
    print(f"\nAvailable Agents: {agents}")