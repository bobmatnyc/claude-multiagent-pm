#!/usr/bin/env python3
"""
Task Tool Profile Integration Service

Provides seamless integration between agent profiles and Task Tool subprocess delegation.
Enables orchestrator to enhance subprocess context with agent-specific knowledge and capabilities.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from pathlib import Path

from .agent_profile_loader import AgentProfileLoader, AgentProfile

logger = logging.getLogger(__name__)


class TaskToolProfileIntegrator:
    """
    Integration service for enhancing Task Tool subprocesses with agent profiles.
    
    Provides standardized pattern for loading agent profiles and injecting
    profile-enhanced context into subprocess delegations.
    """
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize Task Tool profile integrator."""
        self.working_directory = working_directory
        self.profile_loader: Optional[AgentProfileLoader] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize profile loader and integration system."""
        if self._initialized:
            return
            
        self.profile_loader = AgentProfileLoader(self.working_directory)
        await self.profile_loader.initialize()
        self._initialized = True
        
        logger.info("Task Tool profile integration initialized")
        
    async def enhance_task_delegation(
        self, 
        agent_name: str, 
        task_description: str,
        task_context: str = "",
        additional_context: Dict[str, Any] = None
    ) -> str:
        """
        Enhance Task Tool delegation with agent profile context.
        
        Args:
            agent_name: Name of target agent (e.g., 'engineer', 'documentation')
            task_description: Clear description of the task to delegate
            task_context: Specific context for this task
            additional_context: Additional context to include
            
        Returns:
            Enhanced Task Tool delegation instruction
        """
        if not self._initialized:
            await self.initialize()
            
        # Load agent profile
        profile = await self.profile_loader.load_profile(agent_name)
        
        if not profile:
            # Fallback to basic delegation without profile
            logger.warning(f"No profile found for {agent_name}, using basic delegation")
            return self._create_basic_delegation(agent_name, task_description, task_context)
            
        # Generate profile-enhanced delegation
        return self._create_enhanced_delegation(profile, task_description, task_context, additional_context)
        
    def _create_basic_delegation(self, agent_name: str, task_description: str, task_context: str) -> str:
        """Create basic Task Tool delegation without profile enhancement."""
        return f"""**{agent_name.title()} Agent**: {task_description}

TEMPORAL CONTEXT: Today is {{current_date}}. Apply date awareness to task execution.

**Task**: {task_description}

**Context**: {task_context}

**Authority**: Standard agent permissions
**Expected Results**: Task completion and status report
**Escalation**: Report issues or blockers to PM
"""

    def _create_enhanced_delegation(
        self, 
        profile: AgentProfile, 
        task_description: str, 
        task_context: str,
        additional_context: Dict[str, Any] = None
    ) -> str:
        """Create enhanced Task Tool delegation with profile context."""
        
        # Generate profile context
        profile_context = self.profile_loader.generate_subprocess_context(profile, task_context)
        
        # Build enhanced delegation
        delegation = f"""**{profile.role} Agent**: {task_description}

TEMPORAL CONTEXT: Today is {{current_date}}. Apply date awareness to:
- Task prioritization and urgency assessment
- Sprint planning and deadline considerations
- Timeline constraints and dependency management

{profile_context}

**Task Breakdown**:
1. {task_description}
2. Apply agent-specific capabilities and authority scope
3. Follow profile-defined escalation triggers
4. Coordinate according to profile protocols

**Enhanced Context**:
- Primary Focus: {task_context}
- Profile Tier: {profile.tier.value} (precedence in capability resolution)
- Collaboration Style: {profile.context_preferences.get('collaboration_style', 'Coordinate')}
"""

        # Add capabilities-specific guidance
        if profile.capabilities:
            capability_guidance = []
            for cap in profile.capabilities[:3]:  # Top 3 capabilities
                capability_guidance.append(f"- Leverage: {cap}")
            delegation += f"\n**Capability Application**:\n{chr(10).join(capability_guidance)}\n"
            
        # Add authority scope
        if profile.authority_scope:
            authority_items = []
            for auth in profile.authority_scope[:3]:  # Top 3 authority items
                authority_items.append(f"- Authorized: {auth}")
            delegation += f"\n**Authority Scope**:\n{chr(10).join(authority_items)}\n"
            
        # Add coordination protocols
        if profile.coordination_protocols:
            protocol_items = []
            for agent_type, protocol in profile.coordination_protocols.items():
                protocol_items.append(f"- {agent_type.title()}: {protocol}")
            delegation += f"\n**Coordination Protocols**:\n{chr(10).join(protocol_items)}\n"
            
        # Add escalation triggers
        if profile.escalation_triggers:
            trigger_items = []
            for trigger in profile.escalation_triggers[:2]:  # Top 2 triggers
                trigger_items.append(f"- {trigger}")
            delegation += f"\n**Escalation Triggers**:\n{chr(10).join(trigger_items)}\n"
            
        # Add additional context if provided
        if additional_context:
            delegation += f"\n**Additional Context**:\n"
            for key, value in additional_context.items():
                delegation += f"- {key.replace('_', ' ').title()}: {value}\n"
                
        # Standard delegation footer
        delegation += f"""
**Expected Results**: 
- Task completion using profile-specific capabilities
- Status report with profile-contextualized insights
- Escalation alerts for profile-defined trigger conditions

**Integration**: Results will be analyzed through {profile.tier.value}-tier profile lens for optimal PM coordination and next-step planning.
"""
        
        return delegation
        
    async def create_multi_agent_coordination(
        self, 
        agents_and_tasks: Dict[str, str],
        coordination_context: str = ""
    ) -> Dict[str, str]:
        """
        Create coordinated multi-agent Task Tool delegations with profile awareness.
        
        Args:
            agents_and_tasks: Dict mapping agent names to task descriptions
            coordination_context: Overall coordination context
            
        Returns:
            Dict mapping agent names to enhanced delegation instructions
        """
        if not self._initialized:
            await self.initialize()
            
        coordinated_delegations = {}
        
        # Load all profiles first for coordination planning
        agent_profiles = {}
        for agent_name in agents_and_tasks.keys():
            profile = await self.profile_loader.load_profile(agent_name)
            if profile:
                agent_profiles[agent_name] = profile
                
        # Create coordinated delegations
        for agent_name, task_description in agents_and_tasks.items():
            
            # Build coordination context for this agent
            coordination_notes = []
            if agent_name in agent_profiles:
                profile = agent_profiles[agent_name]
                
                # Add coordination with other agents
                for other_agent, other_profile in agent_profiles.items():
                    if other_agent != agent_name:
                        if other_agent in profile.coordination_protocols:
                            coordination_notes.append(
                                f"Coordinate with {other_agent} Agent: {profile.coordination_protocols[other_agent]}"
                            )
                            
            coordination_context_enhanced = coordination_context
            if coordination_notes:
                coordination_context_enhanced += f"\n\nCoordination Requirements:\n{chr(10).join(coordination_notes)}"
                
            # Create enhanced delegation
            delegation = await self.enhance_task_delegation(
                agent_name, 
                task_description, 
                coordination_context_enhanced,
                {
                    "multi_agent_context": True,
                    "coordinated_agents": list(agents_and_tasks.keys()),
                    "coordination_sequence": list(agents_and_tasks.keys()).index(agent_name) + 1
                }
            )
            
            coordinated_delegations[agent_name] = delegation
            
        return coordinated_delegations
        
    async def get_profile_summary(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get summary of agent profile for PM visibility."""
        if not self._initialized:
            await self.initialize()
            
        profile = await self.profile_loader.load_profile(agent_name)
        if not profile:
            return None
            
        return {
            "agent_name": profile.name,
            "role": profile.role,
            "tier": profile.tier.value,
            "capabilities_count": len(profile.capabilities),
            "authority_scope_count": len(profile.authority_scope),
            "escalation_triggers_count": len(profile.escalation_triggers),
            "coordination_protocols": list(profile.coordination_protocols.keys()),
            "context_preferences": profile.context_preferences,
            "profile_path": str(profile.path)
        }
        
    async def list_available_agent_profiles(self) -> Dict[str, Dict[str, Any]]:
        """List all available agent profiles with summaries."""
        if not self._initialized:
            await self.initialize()
            
        available_profiles = await self.profile_loader.list_available_profiles()
        profile_summaries = {}
        
        for tier, agent_names in available_profiles.items():
            for agent_name in agent_names:
                profile_summary = await self.get_profile_summary(agent_name)
                if profile_summary:
                    profile_summaries[f"{agent_name}_{tier.value}"] = profile_summary
                    
        return profile_summaries
        
    def create_profile_loading_instruction(self, agent_name: str) -> str:
        """
        Create standardized instruction for subprocess to load agent profile.
        
        This provides a consistent pattern for subprocesses to load their own profiles
        for enhanced context awareness.
        """
        return f"""
**PROFILE LOADING INSTRUCTION**

Before proceeding with task execution, load your agent profile for enhanced context:

```python
# Profile Loading Pattern
from claude_pm.services.agent_profile_loader import AgentProfileLoader
from pathlib import Path

async def load_my_profile():
    loader = AgentProfileLoader(working_directory=Path.cwd())
    await loader.initialize()
    profile = await loader.load_profile('{agent_name}')
    
    if profile:
        # Use profile context for task execution
        print(f"Loaded {{profile.role}} profile from {{profile.tier.value}} tier")
        return profile
    else:
        print("No profile found - using standard capabilities")
        return None

# Load profile at start of subprocess
my_profile = await load_my_profile()
```

**Profile Integration Benefits**:
- Enhanced capability awareness
- Proper authority scope understanding
- Context-specific escalation triggers
- Coordination protocol knowledge
- Memory integration preferences

**Fallback Behavior**: If profile loading fails, continue with standard agent capabilities.
"""

# Global integrator instance for framework use
_global_integrator: Optional[TaskToolProfileIntegrator] = None

async def get_task_tool_integrator(working_directory: Optional[Path] = None) -> TaskToolProfileIntegrator:
    """Get global Task Tool profile integrator instance."""
    global _global_integrator
    
    if _global_integrator is None:
        _global_integrator = TaskToolProfileIntegrator(working_directory)
        await _global_integrator.initialize()
        
    return _global_integrator

# Convenience functions for common patterns
async def enhance_engineer_delegation(task_description: str, technical_context: str = "") -> str:
    """Enhance Task Tool delegation for Engineer Agent."""
    integrator = await get_task_tool_integrator()
    return await integrator.enhance_task_delegation('engineer', task_description, technical_context)

async def enhance_documentation_delegation(task_description: str, doc_context: str = "") -> str:
    """Enhance Task Tool delegation for Documentation Agent.""" 
    integrator = await get_task_tool_integrator()
    return await integrator.enhance_task_delegation('documentation', task_description, doc_context)

async def enhance_qa_delegation(task_description: str, quality_context: str = "") -> str:
    """Enhance Task Tool delegation for QA Agent."""
    integrator = await get_task_tool_integrator()
    return await integrator.enhance_task_delegation('qa', task_description, quality_context)

async def enhance_ops_delegation(task_description: str, ops_context: str = "") -> str:
    """Enhance Task Tool delegation for Ops Agent."""
    integrator = await get_task_tool_integrator()
    return await integrator.enhance_task_delegation('ops', task_description, ops_context)