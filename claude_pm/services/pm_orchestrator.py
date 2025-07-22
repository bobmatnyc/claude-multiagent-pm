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
    from claude_pm.services import PMOrchestrator
    
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

# Import SharedPromptCache for performance optimization
try:
    from .shared_prompt_cache import SharedPromptCache
    SHARED_CACHE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SharedPromptCache not available: {e}")
    SHARED_CACHE_AVAILABLE = False

# Import core agent loading functionality
try:
    from .core_agent_loader import CoreAgentLoader
    AGENT_LOADER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Failed to import CoreAgentLoader, will create simple loader: {e}")
    AGENT_LOADER_AVAILABLE = False

# Import ticketing service for task tracking
try:
    from .ticketing_service import TicketingService, TicketData
    TICKETING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TicketingService not available: {e}")
    TICKETING_AVAILABLE = False

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
    
    def __init__(self, working_directory: Optional[Path] = None, model_override: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        """Initialize PM orchestrator with core agent loader integration."""
        self.working_directory = Path(working_directory or os.getcwd())
        self._delegation_history: List[Dict[str, Any]] = []
        self._active_delegations: Dict[str, AgentDelegationContext] = {}
        self._delegation_tickets: Dict[str, str] = {}  # Maps delegation_id to ticket_id
        
        # Check for test mode environment variable
        test_mode = os.environ.get('CLAUDE_PM_TEST_MODE', '').lower() == 'true'
        
        # Enable verbose logging if test mode is active OR verbose flag is set
        self.verbose = verbose or test_mode
        
        # If test mode enabled verbose logging, log this fact
        if test_mode and not verbose:
            logger.info("Test mode detected: Enabling verbose prompt logging automatically")
        
        # Initialize synchronous core agent loader
        if AGENT_LOADER_AVAILABLE:
            try:
                self._agent_loader = CoreAgentLoader(self.working_directory)
                logger.info("CoreAgentLoader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CoreAgentLoader: {e}")
                self._agent_loader = None
        else:
            self._agent_loader = None
        
        # Model configuration from CLI override
        self.model_override = model_override
        self.model_config = model_config or {}
        if model_override:
            self.model_config.update({
                "source": "cli_override",
                "selection_method": "user_specified",
                "override_active": True
            })
        
        # Initialize model selector with override support
        self._model_selector = None
        self._initialize_model_selector()
        
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
        
        # Initialize ticketing service integration
        self._ticketing_service = None
        self._ticketing_helper = None
        self._auto_ticket_threshold = 3  # Auto-create tickets for tasks requiring 3+ agents
        if TICKETING_AVAILABLE:
            try:
                self._ticketing_service = TicketingService.get_instance()
                # Import TicketingHelper locally to avoid circular imports
                from ..orchestration.ticketing_helpers import TicketingHelper
                self._ticketing_helper = TicketingHelper()
                logger.info("PMOrchestrator: TicketingService integration enabled")
            except Exception as e:
                logger.warning(f"PMOrchestrator: Failed to initialize TicketingService: {e}")
                self._ticketing_service = None
                self._ticketing_helper = None
        
        logger.info(f"PMOrchestrator initialized with working directory: {self.working_directory}")
        logger.info(f"  Shared cache: {'enabled' if self._shared_cache else 'disabled'}")
        logger.info(f"  Model override: {self.model_override or 'none'}")
        logger.info(f"  Verbose mode: {self.verbose}")
        logger.info(f"  Ticketing: {'enabled' if self._ticketing_service else 'disabled'}")
        if self.model_override:
            logger.info(f"  Override source: {self.model_config.get('source', 'unknown')}")
    
    
    def _should_create_ticket(self, delegation_context: AgentDelegationContext) -> bool:
        """
        Determine if a ticket should be created for this delegation.
        
        Criteria:
        - Task has high or critical priority
        - Task has 3+ requirements or deliverables
        - Task description indicates multi-agent coordination
        - Task has explicit escalation triggers
        """
        if not self._ticketing_service:
            return False
            
        # High priority tasks always get tickets
        if delegation_context.priority in ["high", "critical"]:
            return True
        
        # Complex tasks with many requirements/deliverables
        if (len(delegation_context.requirements) >= self._auto_ticket_threshold or 
            len(delegation_context.deliverables) >= self._auto_ticket_threshold):
            return True
        
        # Multi-agent coordination keywords
        multi_agent_keywords = ["coordinate", "multiple agents", "cross-agent", 
                               "workflow", "integration", "multi-step"]
        task_lower = delegation_context.task_description.lower()
        if any(keyword in task_lower for keyword in multi_agent_keywords):
            return True
        
        # Has explicit escalation triggers
        if delegation_context.escalation_triggers:
            return True
        
        return False
    
    def _initialize_model_selector(self):
        """Initialize model selector with CLI override support."""
        try:
            # Import ModelSelector with override support
            import os
            from claude_pm.services.model_selector import ModelSelector
            
            # Set environment override if CLI model is specified
            if self.model_override:
                old_override = os.environ.get('CLAUDE_PM_MODEL_OVERRIDE')
                os.environ['CLAUDE_PM_MODEL_OVERRIDE'] = self.model_override
                
                try:
                    self._model_selector = ModelSelector()
                    logger.debug(f"ModelSelector initialized with CLI override: {self.model_override}")
                finally:
                    # Restore original environment
                    if old_override is not None:
                        os.environ['CLAUDE_PM_MODEL_OVERRIDE'] = old_override
                    else:
                        os.environ.pop('CLAUDE_PM_MODEL_OVERRIDE', None)
            else:
                self._model_selector = ModelSelector()
                logger.debug("ModelSelector initialized with default configuration")
                
        except ImportError as e:
            logger.warning(f"ModelSelector not available: {e}")
            self._model_selector = None
        except Exception as e:
            logger.error(f"Failed to initialize ModelSelector: {e}")
            self._model_selector = None
    
    def _log_prompt_to_file(self, prompt: str, agent_type: str, task_description: str, 
                           model_info: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Log prompts to JSON files when verbose mode is enabled.
        
        Args:
            prompt: The generated prompt text
            agent_type: Type of agent being prompted
            task_description: Description of the task
            model_info: Model configuration and selection info
            
        Returns:
            Path to the log file if created, None otherwise
        """
        if not self.verbose:
            return None
            
        try:
            # Create log directory structure
            now = datetime.now()
            
            # Check for custom prompts directory from environment
            prompts_dir_env = os.environ.get('CLAUDE_PM_PROMPTS_DIR')
            if prompts_dir_env:
                # Use the custom prompts directory
                log_dir = Path(prompts_dir_env) / now.strftime("%Y-%m-%d")
            else:
                # Use default location
                log_dir = self.working_directory / ".claude-pm" / "logs" / "prompts" / now.strftime("%Y-%m-%d")
            
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            timestamp = now.strftime("%H%M%S_%f")[:-3]  # Include milliseconds
            filename = f"prompt_{agent_type}_{timestamp}.json"
            log_path = log_dir / filename
            
            # Prepare log entry
            log_entry = {
                "timestamp": now.isoformat(),
                "agent_type": agent_type,
                "task_description": task_description,
                "prompt_text": prompt,
                "metadata": {
                    "framework_version": "014",
                    "delegation_id": f"{agent_type}_{now.strftime('%Y%m%d_%H%M%S')}",
                    "working_directory": str(self.working_directory),
                    "prompt_length": len(prompt),
                    "verbose_mode": True
                }
            }
            
            # Add model info if available
            if model_info:
                log_entry["model_info"] = model_info
            elif self.model_override:
                log_entry["model_info"] = {
                    "selected_model": self.model_override,
                    "source": "cli_override"
                }
            
            # Write log file
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Logged prompt to: {log_path}")
            return str(log_path)
            
        except Exception as e:
            logger.warning(f"Failed to log prompt to file: {e}")
            return None
    
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
        escalation_triggers: Optional[List[str]] = None,
        selected_model: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None
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
            selected_model: Optionally selected model for the agent
            model_config: Model configuration metadata
            
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
            
            # Create task context for core agent loader
            task_context = {
                'task_description': task_description,
                'temporal_context': delegation_context.temporal_context,
                'requirements': delegation_context.requirements,
                'deliverables': delegation_context.deliverables,
                'dependencies': delegation_context.dependencies,
                'priority': delegation_context.priority,
                'memory_categories': delegation_context.memory_categories,
                'integration_notes': integration_notes,
                'escalation_triggers': escalation_triggers or []
            }
            
            # Generate base prompt using core agent loader (synchronous)
            if self._agent_loader:
                base_prompt = self._agent_loader.build_task_prompt(agent_type, task_context)
            else:
                # Fallback if loader not available
                base_prompt = f"**{agent_type.title()}**: {task_description}\nTEMPORAL CONTEXT: {delegation_context.temporal_context}"
            
            # Use orchestrator model override if no specific model provided
            effective_model = selected_model or self.model_override
            effective_config = model_config or {}
            
            # Merge with orchestrator model config
            if self.model_config:
                effective_config = {**self.model_config, **effective_config}
            
            # Get model selection from model selector if available
            if not effective_model and self._model_selector:
                try:
                    model_type, model_configuration = self._model_selector.select_model_for_agent(agent_type)
                    effective_model = model_type.value
                    effective_config.update({
                        "max_tokens": model_configuration.max_tokens,
                        "performance_profile": model_configuration.performance_profile,
                        "selection_method": "agent_specific",
                        "source": "model_selector"
                    })
                    logger.debug(f"Model selector chose {effective_model} for {agent_type}")
                except Exception as e:
                    logger.warning(f"Model selector failed for {agent_type}: {e}")
            
            # Enhance prompt with PM orchestrator integration and model configuration
            enhanced_prompt = self._enhance_prompt_with_pm_integration(
                base_prompt, delegation_context, effective_model, effective_config
            )
            
            # Track delegation
            delegation_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._active_delegations[delegation_id] = delegation_context
            
            # Create ticket if criteria met
            ticket_id = None
            if self._should_create_ticket(delegation_context):
                try:
                    ticket = self._ticketing_helper.create_agent_task_ticket(
                        agent_name=agent_type,
                        task_description=task_description,
                        priority=priority,
                        additional_context={
                            "delegation_id": delegation_id,
                            "requirements": requirements,
                            "deliverables": deliverables,
                            "dependencies": dependencies,
                            "model": effective_model or "default"
                        }
                    )
                    if ticket:
                        ticket_id = ticket.id
                        self._delegation_tickets[delegation_id] = ticket_id
                        logger.info(f"Created ticket {ticket_id} for {agent_type} delegation")
                        
                        # Add ticket reference to prompt
                        enhanced_prompt = enhanced_prompt.replace(
                            f"**Delegation ID**: {delegation_id}",
                            f"**Delegation ID**: {delegation_id}\n- **Ticket ID**: {ticket_id}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to create ticket for delegation: {e}")
            
            # Add to history
            self._delegation_history.append({
                "delegation_id": delegation_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "timestamp": datetime.now().isoformat(),
                "status": "delegated",
                "ticket_id": ticket_id
            })
            
            logger.info(f"Generated prompt for {agent_type} delegation: {delegation_id}")
            
            # Log prompt to file if verbose mode is enabled
            if self.verbose:
                log_path = self._log_prompt_to_file(
                    prompt=enhanced_prompt,
                    agent_type=agent_type,
                    task_description=task_description,
                    model_info={
                        "selected_model": effective_model,
                        **effective_config
                    } if effective_model else None
                )
                if log_path:
                    logger.info(f"Prompt logged to: {log_path}")
            
            # Cache the generated prompt if shared cache is available
            if self._shared_cache and delegation_cache_key:
                self._shared_cache.set(delegation_cache_key, enhanced_prompt, ttl=900)  # 15 minutes
                logger.debug(f"Cached delegation prompt for {agent_type}")
            
            return enhanced_prompt
            
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except Exception as e:
            logger.error(f"Error generating agent prompt: {e}")
            # Re-raise the error instead of providing fallback
            raise RuntimeError(f"Failed to generate agent prompt: {e}") from e
    
    def _enhance_prompt_with_pm_integration(
        self, 
        base_prompt: str, 
        delegation_context: AgentDelegationContext,
        selected_model: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance base prompt with PM orchestrator integration features."""
        
        # Add PM integration section with model configuration
        model_info_section = ""
        if selected_model and model_config:
            selection_method = model_config.get("selection_method", "unknown")
            source = model_config.get("source", "unknown")
            max_tokens = model_config.get("max_tokens", "unknown")
            
            model_info_section = f"""
**Model Configuration**:
- **Selected Model**: {selected_model}
- **Selection Method**: {selection_method}
- **Configuration Source**: {source}
- **Max Tokens**: {max_tokens}
- **Performance Profile**: {model_config.get("performance_profile", {}).get("reasoning_quality", "standard")} reasoning quality
"""
            
            # Add criteria if available
            if "criteria" in model_config:
                criteria = model_config["criteria"]
                model_info_section += f"""- **Task Analysis**: {criteria.get("task_complexity", "medium")} complexity, {criteria.get("reasoning_depth", "standard")} reasoning depth
- **Optimization**: {'Speed priority' if criteria.get("speed_priority") else 'Quality priority'}, {'Creativity enabled' if criteria.get("creativity_required") else 'Standard processing'}
"""
        
        pm_integration_section = f"""
**PM Orchestrator Integration**:
- **Delegation ID**: {delegation_context.agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}
- **PM Coordination**: Report progress and escalate issues back to PM orchestrator
- **Cross-Agent Workflow**: This task may integrate with other agent outputs
- **Integration Notes**: {delegation_context.integration_notes or "Standard PM workflow integration"}
{model_info_section}
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
            
            # Update ticket if exists
            if delegation_id in self._delegation_tickets and self._ticketing_helper:
                ticket_id = self._delegation_tickets[delegation_id]
                try:
                    success = results.get("success", True)
                    status = "resolved" if success else "closed"
                    comment = f"Task completed by {self._active_delegations[delegation_id].agent_type} agent.\n"
                    comment += f"Success: {success}\n"
                    if "summary" in results:
                        comment += f"Summary: {results['summary']}"
                    
                    self._ticketing_helper.update_agent_task_status(
                        ticket_id=ticket_id,
                        status=status,
                        comment=comment
                    )
                    logger.info(f"Updated ticket {ticket_id} to {status}")
                except Exception as e:
                    logger.warning(f"Failed to update ticket {ticket_id}: {e}")
            
            # Remove from active delegations
            del self._active_delegations[delegation_id]
            if delegation_id in self._delegation_tickets:
                del self._delegation_tickets[delegation_id]
            
            logger.info(f"Completed delegation: {delegation_id}")
            return True
        
        return False
    
    def list_available_agents(self) -> Dict[str, List[str]]:
        """List all available agents from the core agent loader."""
        try:
            if self._agent_loader:
                return self._agent_loader.list_available_agents()
            else:
                raise RuntimeError("Agent loader not available")
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
            validation_results = {}
            
            if self._agent_loader:
                # Basic validation - check if we can list agents
                agents = self._agent_loader.list_available_agents()
                validation_results["valid"] = len(agents) > 0
                validation_results["agent_count"] = sum(len(tier_agents) for tier_agents in agents.values())
                validation_results["tiers_found"] = list(agents.keys())
            
            # Add PM orchestrator specific validations
            validation_results["pm_integration"] = {
                "active_delegations": len(self._active_delegations),
                "loader_available": self._agent_loader is not None,
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
                    "loader_available": False,
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
        
        # Agent loader is synchronous and doesn't track metrics
        
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
        
        # Agent loader uses core shared cache, no need for separate invalidation
    
    def get_agent_profile_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent profile."""
        try:
            if self._agent_loader:
                profile = self._agent_loader.load_agent_profile(agent_type)
                if profile:
                    return {
                        "name": profile.name,
                        "tier": profile.tier.value,
                        "role": profile.role,
                        "nickname": profile.nickname,
                        "profile_path": str(profile.path),
                        "profile_id": profile.profile_id
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting agent profile info: {e}")
            return None
    
    def get_ticketing_status(self) -> Dict[str, Any]:
        """Get current ticketing system status and statistics."""
        status = {
            "ticketing_enabled": self._ticketing_service is not None,
            "active_tickets": len(self._delegation_tickets),
            "ticket_mappings": dict(self._delegation_tickets)
        }
        
        if self._ticketing_helper:
            try:
                # Get project overview
                overview = self._ticketing_helper.get_project_overview()
                status["project_overview"] = overview
                
                # Get workload by agent
                workload = {}
                for agent_type in ["documentation", "engineer", "qa", "version_control", 
                                  "research", "ops", "security", "data_engineer"]:
                    agent_workload = self._ticketing_helper.get_agent_workload(agent_type)
                    if agent_workload.get("total_tickets", 0) > 0:
                        workload[agent_type] = agent_workload
                
                status["agent_workload"] = workload
            except Exception as e:
                logger.error(f"Error getting ticketing status: {e}")
                status["error"] = str(e)
        
        return status
    
    def update_delegation_progress(
        self, 
        delegation_id: str, 
        progress: str,
        status: str = "in_progress"
    ) -> bool:
        """
        Update progress on a delegation and its associated ticket.
        
        Args:
            delegation_id: The delegation identifier
            progress: Progress update message
            status: New status (in_progress, blocked, etc.)
            
        Returns:
            True if update successful
        """
        if delegation_id not in self._active_delegations:
            return False
        
        # Update delegation history
        for entry in self._delegation_history:
            if entry["delegation_id"] == delegation_id:
                entry["last_update"] = datetime.now().isoformat()
                entry["status"] = status
                if "progress_updates" not in entry:
                    entry["progress_updates"] = []
                entry["progress_updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": progress,
                    "status": status
                })
                break
        
        # Update ticket if exists
        if delegation_id in self._delegation_tickets and self._ticketing_helper:
            ticket_id = self._delegation_tickets[delegation_id]
            try:
                # Map PM status to ticket status
                ticket_status_map = {
                    "in_progress": "in_progress",
                    "blocked": "in_progress",  # Keep as in_progress but add comment
                    "waiting": "in_progress",
                    "delegated": "open"
                }
                
                ticket_status = ticket_status_map.get(status, "in_progress")
                
                # Add progress comment
                comment = f"Progress Update: {progress}"
                if status == "blocked":
                    comment = f"BLOCKED: {progress}"
                
                self._ticketing_service.add_comment(
                    ticket_id=ticket_id,
                    comment=comment,
                    author="pm_orchestrator"
                )
                
                # Update status if changed
                if ticket_status != "in_progress" or status == "blocked":
                    self._ticketing_service.update_ticket(
                        ticket_id=ticket_id,
                        status=ticket_status
                    )
                
                logger.info(f"Updated ticket {ticket_id} progress: {progress}")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to update ticket {ticket_id}: {e}")
        
        return True
    
    def create_multi_agent_workflow(
        self,
        workflow_name: str,
        workflow_description: str,
        agent_tasks: List[Dict[str, Any]],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a multi-agent workflow with automatic ticket creation.
        
        Args:
            workflow_name: Name of the workflow
            workflow_description: Overall workflow description
            agent_tasks: List of agent task definitions, each containing:
                - agent_type: Type of agent
                - task_description: Task for the agent
                - requirements: Optional requirements list
                - deliverables: Optional deliverables list
                - depends_on: Optional list of agent_types this depends on
            priority: Overall workflow priority
            
        Returns:
            Dictionary with workflow information and created tickets
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_result = {
            "workflow_id": workflow_id,
            "name": workflow_name,
            "description": workflow_description,
            "priority": priority,
            "agent_tasks": [],
            "tickets": []
        }
        
        # Create master workflow ticket if ticketing available
        master_ticket_id = None
        if self._ticketing_helper:
            try:
                master_ticket = self._ticketing_service.create_ticket(
                    title=f"[Workflow] {workflow_name}",
                    description=workflow_description,
                    priority=priority,
                    labels=["workflow", "multi-agent"],
                    metadata={
                        "workflow_id": workflow_id,
                        "agent_count": len(agent_tasks),
                        "created_by": "pm_orchestrator"
                    }
                )
                master_ticket_id = master_ticket.id
                workflow_result["master_ticket_id"] = master_ticket_id
                logger.info(f"Created master workflow ticket: {master_ticket_id}")
            except Exception as e:
                logger.warning(f"Failed to create master workflow ticket: {e}")
        
        # Process each agent task
        for i, task_def in enumerate(agent_tasks):
            agent_type = task_def.get("agent_type")
            task_description = task_def.get("task_description")
            requirements = task_def.get("requirements", [])
            deliverables = task_def.get("deliverables", [])
            depends_on = task_def.get("depends_on", [])
            
            # Generate prompt for this agent
            prompt = self.generate_agent_prompt(
                agent_type=agent_type,
                task_description=task_description,
                requirements=requirements,
                deliverables=deliverables,
                priority=priority,
                integration_notes=f"Part of workflow: {workflow_name}"
            )
            
            # Get delegation ID from history (last added)
            delegation_id = self._delegation_history[-1]["delegation_id"]
            ticket_id = self._delegation_history[-1].get("ticket_id")
            
            task_info = {
                "agent_type": agent_type,
                "delegation_id": delegation_id,
                "ticket_id": ticket_id,
                "depends_on": depends_on,
                "prompt_generated": True
            }
            
            workflow_result["agent_tasks"].append(task_info)
            if ticket_id:
                workflow_result["tickets"].append(ticket_id)
                
                # Link to master ticket if available
                if master_ticket_id and self._ticketing_service:
                    try:
                        self._ticketing_service.add_comment(
                            ticket_id=ticket_id,
                            comment=f"Part of workflow: {workflow_name} (Master ticket: {master_ticket_id})",
                            author="pm_orchestrator"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to link ticket {ticket_id} to workflow: {e}")
        
        logger.info(f"Created multi-agent workflow {workflow_id} with {len(agent_tasks)} tasks")
        return workflow_result


# Helper functions for easy PM orchestrator integration
def quick_delegate(
    agent_type: str,
    task_description: str,
    requirements: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    working_directory: Optional[Path] = None,
    model_override: Optional[str] = None,
    model_config: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> str:
    """
    Quick delegation helper for PM orchestrator.
    
    Args:
        agent_type: Type of agent to delegate to
        task_description: Task description
        requirements: List of requirements
        deliverables: List of expected deliverables
        working_directory: Working directory path
        model_override: Model override from CLI
        model_config: Model configuration metadata
        verbose: Enable verbose logging
        
    Returns:
        Complete Task Tool prompt ready for subprocess creation
    """
    orchestrator = PMOrchestrator(working_directory, model_override, model_config, verbose)
    return orchestrator.generate_agent_prompt(
        agent_type=agent_type,
        task_description=task_description,
        requirements=requirements,
        deliverables=deliverables
    )


def create_shortcut_prompts(model_override: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None, verbose: bool = False) -> Dict[str, str]:
    """Create shortcut prompts for common PM orchestrator operations."""
    orchestrator = PMOrchestrator(model_override=model_override, model_config=model_config, verbose=verbose)
    
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