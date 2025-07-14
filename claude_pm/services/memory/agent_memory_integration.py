"""
Agent Memory Integration Helper

This module provides utilities for integrating memory collection across all agent types
in the Claude PM Framework. It handles memory service initialization, agent registration,
and memory collection compliance validation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .memory_trigger_service import MemoryTriggerService, create_memory_trigger_service
from .interfaces.models import MemoryCategory
from ..memory.interfaces.exceptions import MemoryServiceError


class AgentMemoryIntegration:
    """
    Manages memory integration across all agent types.
    
    Provides centralized memory service management, agent registration,
    compliance validation, and health monitoring for memory collection.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize agent memory integration.
        
        Args:
            config: Memory integration configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Memory service instance
        self.memory_service: Optional[MemoryTriggerService] = None
        
        # Registered agents
        self.registered_agents: Dict[str, Any] = {}
        self.agent_memory_stats: Dict[str, Dict[str, Any]] = {}
        
        # Integration state
        self._initialized = False
        self.integration_enabled = self.config.get("enabled", True)
        
        # Compliance tracking
        self.compliance_requirements = {
            "memory_integration_capability": True,
            "memory_service_connected": True,
            "memory_auto_collect_enabled": True,
            "memory_health_check_passing": True,
        }
    
    async def initialize(self) -> bool:
        """
        Initialize memory integration system.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True
        
        if not self.integration_enabled:
            self.logger.info("Agent memory integration disabled")
            return True
        
        try:
            self.logger.info("Initializing agent memory integration...")
            
            # Create memory trigger service
            memory_config = self.config.get("memory_service", {})
            self.memory_service = create_memory_trigger_service(memory_config)
            
            # Initialize memory service
            if not await self.memory_service.initialize():
                raise MemoryServiceError("Failed to initialize memory trigger service")
            
            self._initialized = True
            self.logger.info("Agent memory integration initialized successfully")
            
            # Collect initialization memory
            await self._collect_integration_memory(
                "agent_memory_integration_initialized",
                MemoryCategory.SYSTEM,
                {"config": self.config, "enabled": self.integration_enabled}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent memory integration: {e}")
            self._initialized = False
            return False
    
    async def register_agent(self, agent: Any) -> bool:
        """
        Register an agent for memory integration.
        
        Args:
            agent: Agent instance to register
            
        Returns:
            bool: True if registration successful
        """
        if not self._initialized or not self.integration_enabled:
            return False
        
        try:
            agent_id = getattr(agent, 'agent_id', str(id(agent)))
            agent_type = getattr(agent, 'agent_type', 'unknown')
            
            self.logger.info(f"Registering agent for memory integration: {agent_id} ({agent_type})")
            
            # Enable memory integration on the agent
            result = await agent.enable_memory_integration(self.memory_service)
            
            if not result.get("success", False):
                self.logger.error(f"Failed to enable memory integration for agent {agent_id}: {result.get('error')}")
                return False
            
            # Register agent
            self.registered_agents[agent_id] = {
                "agent": agent,
                "agent_type": agent_type,
                "registration_time": asyncio.get_event_loop().time(),
                "memory_enabled": True,
            }
            
            # Initialize agent memory stats
            self.agent_memory_stats[agent_id] = {
                "memories_collected": 0,
                "errors_collected": 0,
                "feedback_collected": 0,
                "performance_observations": 0,
                "last_memory_time": None,
            }
            
            self.logger.info(f"Agent {agent_id} registered for memory integration")
            
            # Collect registration memory
            await self._collect_integration_memory(
                f"agent_registered_for_memory_integration: {agent_id}",
                MemoryCategory.SYSTEM,
                {"agent_id": agent_id, "agent_type": agent_type}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent for memory integration: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from memory integration.
        
        Args:
            agent_id: Agent ID to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        if agent_id not in self.registered_agents:
            return True
        
        try:
            agent_info = self.registered_agents[agent_id]
            agent = agent_info["agent"]
            
            # Disable memory integration on the agent
            await agent.disable_memory_integration()
            
            # Remove from tracking
            del self.registered_agents[agent_id]
            del self.agent_memory_stats[agent_id]
            
            self.logger.info(f"Agent {agent_id} unregistered from memory integration")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def validate_compliance(self) -> Dict[str, Any]:
        """
        Validate memory collection compliance across all registered agents.
        
        Returns:
            Dict[str, Any]: Compliance validation results
        """
        if not self._initialized:
            return {
                "compliant": False,
                "error": "Memory integration not initialized"
            }
        
        compliance_results = {
            "compliant": True,
            "total_agents": len(self.registered_agents),
            "compliant_agents": 0,
            "non_compliant_agents": 0,
            "agent_results": {},
            "overall_issues": [],
        }
        
        try:
            for agent_id, agent_info in self.registered_agents.items():
                agent = agent_info["agent"]
                agent_compliance = await self._validate_agent_compliance(agent)
                
                compliance_results["agent_results"][agent_id] = agent_compliance
                
                if agent_compliance["compliant"]:
                    compliance_results["compliant_agents"] += 1
                else:
                    compliance_results["non_compliant_agents"] += 1
                    compliance_results["compliant"] = False
                    compliance_results["overall_issues"].extend(agent_compliance["issues"])
            
            # Collect compliance validation memory
            await self._collect_integration_memory(
                "memory_compliance_validation_completed",
                MemoryCategory.SYSTEM,
                compliance_results
            )
            
            return compliance_results
            
        except Exception as e:
            self.logger.error(f"Failed to validate compliance: {e}")
            return {
                "compliant": False,
                "error": str(e),
                "total_agents": len(self.registered_agents)
            }
    
    async def _validate_agent_compliance(self, agent: Any) -> Dict[str, Any]:
        """
        Validate compliance for a single agent.
        
        Args:
            agent: Agent to validate
            
        Returns:
            Dict[str, Any]: Agent compliance results
        """
        agent_id = getattr(agent, 'agent_id', 'unknown')
        compliance_result = {
            "compliant": True,
            "issues": [],
            "checks": {}
        }
        
        try:
            # Check memory integration capability
            capabilities = getattr(agent, 'capabilities', [])
            has_memory_capability = "memory_integration" in capabilities
            compliance_result["checks"]["memory_integration_capability"] = has_memory_capability
            
            if not has_memory_capability:
                compliance_result["compliant"] = False
                compliance_result["issues"].append("Missing memory_integration capability")
            
            # Check memory service connection
            memory_service_connected = getattr(agent, 'memory_service', None) is not None
            compliance_result["checks"]["memory_service_connected"] = memory_service_connected
            
            if not memory_service_connected:
                compliance_result["compliant"] = False
                compliance_result["issues"].append("Memory service not connected")
            
            # Check memory auto-collect enabled
            memory_auto_collect = getattr(agent, 'memory_auto_collect', False)
            compliance_result["checks"]["memory_auto_collect_enabled"] = memory_auto_collect
            
            if not memory_auto_collect:
                compliance_result["compliant"] = False
                compliance_result["issues"].append("Memory auto-collect not enabled")
            
            # Check memory health
            if memory_service_connected:
                memory_health = await agent.get_memory_health_status()
                memory_healthy = memory_health.get("memory_health") == "healthy"
                compliance_result["checks"]["memory_health_check_passing"] = memory_healthy
                
                if not memory_healthy:
                    compliance_result["compliant"] = False
                    compliance_result["issues"].append(f"Memory health check failed: {memory_health.get('memory_health')}")
            else:
                compliance_result["checks"]["memory_health_check_passing"] = False
            
            return compliance_result
            
        except Exception as e:
            return {
                "compliant": False,
                "issues": [f"Compliance validation error: {e}"],
                "checks": {},
                "error": str(e)
            }
    
    async def get_integration_health(self) -> Dict[str, Any]:
        """
        Get comprehensive memory integration health status.
        
        Returns:
            Dict[str, Any]: Integration health information
        """
        health_data = {
            "integration_initialized": self._initialized,
            "integration_enabled": self.integration_enabled,
            "memory_service_available": self.memory_service is not None,
            "registered_agents_count": len(self.registered_agents),
            "agent_stats": self.agent_memory_stats.copy(),
        }
        
        if self.memory_service:
            try:
                memory_service = self.memory_service.get_memory_service()
                if memory_service:
                    memory_health = await memory_service.get_service_health()
                    health_data["memory_service_health"] = memory_health
            except Exception as e:
                health_data["memory_service_error"] = str(e)
        
        return health_data
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get memory collection statistics across all agents.
        
        Returns:
            Dict[str, Any]: Memory statistics
        """
        if not self.memory_service:
            return {"error": "Memory service not available"}
        
        try:
            stats = {
                "total_agents": len(self.registered_agents),
                "agent_stats": self.agent_memory_stats.copy(),
                "integration_stats": {
                    "registration_errors": 0,
                    "compliance_violations": 0,
                    "memory_collection_errors": 0,
                }
            }
            
            # Get memory service statistics
            memory_service = self.memory_service.get_memory_service()
            if memory_service:
                memory_stats = await memory_service.get_service_health()
                stats["memory_service_stats"] = memory_stats.get("metrics", {})
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _collect_integration_memory(
        self,
        content: str,
        category: MemoryCategory,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Collect memory for integration events.
        
        Args:
            content: Memory content
            category: Memory category
            metadata: Optional metadata
            
        Returns:
            Optional[str]: Memory ID if successful
        """
        if not self.memory_service:
            return None
        
        try:
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                return None
            
            enhanced_metadata = {
                "source": "agent_memory_integration",
                "integration_enabled": self.integration_enabled,
                "registered_agents_count": len(self.registered_agents),
                **(metadata or {})
            }
            
            return await memory_service.add_memory(
                project_name="framework_integration",
                content=content,
                category=category,
                tags=["integration", "memory", "agent"],
                metadata=enhanced_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect integration memory: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup memory integration resources."""
        try:
            # Unregister all agents
            for agent_id in list(self.registered_agents.keys()):
                await self.unregister_agent(agent_id)
            
            # Cleanup memory service
            if self.memory_service:
                await self.memory_service.cleanup()
            
            self._initialized = False
            self.logger.info("Agent memory integration cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during memory integration cleanup: {e}")


# Global memory integration instance
_global_memory_integration: Optional[AgentMemoryIntegration] = None


async def get_global_memory_integration() -> Optional[AgentMemoryIntegration]:
    """Get the global memory integration instance."""
    return _global_memory_integration


async def initialize_global_memory_integration(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Initialize the global memory integration instance.
    
    Args:
        config: Memory integration configuration
        
    Returns:
        bool: True if initialization successful
    """
    global _global_memory_integration
    
    if _global_memory_integration is not None:
        return True
    
    _global_memory_integration = AgentMemoryIntegration(config)
    return await _global_memory_integration.initialize()


async def cleanup_global_memory_integration():
    """Cleanup the global memory integration instance."""
    global _global_memory_integration
    
    if _global_memory_integration:
        await _global_memory_integration.cleanup()
        _global_memory_integration = None


async def register_agent_for_memory(agent: Any) -> bool:
    """
    Register an agent for memory integration using the global instance.
    
    Args:
        agent: Agent to register
        
    Returns:
        bool: True if registration successful
    """
    integration = await get_global_memory_integration()
    if integration:
        return await integration.register_agent(agent)
    return False


async def validate_global_memory_compliance() -> Dict[str, Any]:
    """
    Validate memory compliance across all registered agents.
    
    Returns:
        Dict[str, Any]: Compliance validation results
    """
    integration = await get_global_memory_integration()
    if integration:
        return await integration.validate_compliance()
    return {"compliant": False, "error": "Memory integration not initialized"}