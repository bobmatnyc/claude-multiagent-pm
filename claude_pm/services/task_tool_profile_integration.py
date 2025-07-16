#!/usr/bin/env python3
"""
Task Tool Profile Integration Service
====================================

Integration service that connects the AgentProfileLoader with the Task Tool subprocess system.
Enhances subprocess creation with improved prompts and agent profile integration.

Key Features:
- Task Tool subprocess creation with enhanced prompts
- Agent profile integration for improved context
- Improved prompt deployment and validation
- Performance optimization with SharedPromptCache
- Training system integration for continuous improvement
- Framework version 014 compliance

Framework Version: 014
Implementation: 2025-07-15
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from ..core.base_service import BaseService
from ..core.config import Config
from .agent_profile_loader import AgentProfileLoader, AgentProfile, ImprovedPrompt
from .shared_prompt_cache import SharedPromptCache
from .agent_registry import AgentRegistry
from .agent_training_integration import AgentTrainingIntegration

logger = logging.getLogger(__name__)


@dataclass
class TaskToolRequest:
    """Task Tool subprocess creation request."""
    agent_name: str
    task_description: str
    context: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: str = "medium"
    memory_categories: List[str] = field(default_factory=list)
    
    # Enhanced attributes
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    enhanced_prompts: bool = True
    training_integration: bool = True
    
    @property
    def task_context(self) -> Dict[str, Any]:
        """Get task context for prompt building."""
        return {
            'task_description': self.task_description,
            'requirements': self.requirements,
            'deliverables': self.deliverables,
            'dependencies': self.dependencies,
            'priority': self.priority,
            'memory_categories': self.memory_categories,
            'context': self.context,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TaskToolResponse:
    """Task Tool subprocess creation response."""
    request_id: str
    success: bool
    enhanced_prompt: Optional[str] = None
    agent_profile: Optional[AgentProfile] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # Enhanced attributes
    prompt_improvement_score: float = 0.0
    training_session_id: Optional[str] = None
    cache_hit: bool = False
    response_time_ms: float = 0.0


class TaskToolProfileIntegration(BaseService):
    """
    Task Tool Profile Integration Service
    
    Provides enhanced subprocess creation with agent profile integration,
    improved prompts, and training system connectivity.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Task Tool integration service."""
        super().__init__(name="task_tool_profile_integration", config=config)
        
        # Core services
        self.agent_loader = None
        self.shared_cache = None
        self.agent_registry = None
        self.training_integration = None
        
        # Performance tracking
        self.performance_metrics = {
            'subprocess_requests': 0,
            'successful_enhancements': 0,
            'failed_enhancements': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'training_integrations': 0,
            'average_response_time_ms': 0.0
        }
        
        # Request history
        self.request_history: List[TaskToolRequest] = []
        self.max_history_size = 1000
        
        # Template cache
        self.template_cache: Dict[str, str] = {}
        
        logger.info("TaskToolProfileIntegration initialized")
    
    async def _initialize(self) -> None:
        """Initialize the service and its dependencies."""
        logger.info("Initializing TaskToolProfileIntegration service...")
        
        # Initialize AgentProfileLoader
        try:
            self.agent_loader = AgentProfileLoader(self.config)
            await self.agent_loader.start()
            logger.info("AgentProfileLoader integration enabled")
        except Exception as e:
            logger.error(f"Failed to initialize AgentProfileLoader: {e}")
            raise
        
        # Initialize SharedPromptCache
        try:
            self.shared_cache = SharedPromptCache.get_instance({
                "max_size": 2000,
                "max_memory_mb": 200,
                "default_ttl": 3600,
                "enable_metrics": True
            })
            logger.info("SharedPromptCache integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize SharedPromptCache: {e}")
            self.shared_cache = None
        
        # Initialize AgentRegistry
        try:
            self.agent_registry = AgentRegistry(cache_service=self.shared_cache)
            await self.agent_registry.discover_agents()
            logger.info("AgentRegistry integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize AgentRegistry: {e}")
            self.agent_registry = None
        
        # Initialize TrainingIntegration
        try:
            self.training_integration = AgentTrainingIntegration(self.config)
            await self.training_integration.start_integration()
            logger.info("Training integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize training integration: {e}")
            self.training_integration = None
        
        logger.info("TaskToolProfileIntegration service initialized successfully")
    
    async def _cleanup(self) -> None:
        """Cleanup service resources."""
        logger.info("Cleaning up TaskToolProfileIntegration service...")
        
        # Stop services
        if self.agent_loader:
            await self.agent_loader.stop()
        
        if self.training_integration:
            await self.training_integration.stop_integration()
        
        # Clear caches
        self.template_cache.clear()
        self.request_history.clear()
        
        logger.info("TaskToolProfileIntegration service cleaned up")
    
    async def create_enhanced_subprocess(self, request: TaskToolRequest) -> TaskToolResponse:
        """
        Create enhanced Task Tool subprocess with agent profile integration.
        
        Args:
            request: Task Tool creation request
            
        Returns:
            Enhanced subprocess response
        """
        start_time = datetime.now()
        
        try:
            # Update performance metrics
            self.performance_metrics['subprocess_requests'] += 1
            
            # Add to request history
            self._add_to_history(request)
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_prompt = await self._get_cached_prompt(cache_key)
            
            if cached_prompt:
                self.performance_metrics['cache_hits'] += 1
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return TaskToolResponse(
                    request_id=request.request_id,
                    success=True,
                    enhanced_prompt=cached_prompt,
                    performance_metrics=self.performance_metrics.copy(),
                    cache_hit=True,
                    response_time_ms=response_time
                )
            
            self.performance_metrics['cache_misses'] += 1
            
            # Load agent profile
            agent_profile = await self.agent_loader.load_agent_profile(request.agent_name)
            if not agent_profile:
                self.performance_metrics['failed_enhancements'] += 1
                return TaskToolResponse(
                    request_id=request.request_id,
                    success=False,
                    error=f"Agent profile not found: {request.agent_name}"
                )
            
            # Build enhanced prompt
            enhanced_prompt = await self._build_enhanced_prompt(request, agent_profile)
            
            # Cache the prompt
            await self._cache_prompt(cache_key, enhanced_prompt)
            
            # Integration with training system
            training_session_id = None
            improvement_score = 0.0
            
            if request.training_integration and self.training_integration:
                training_result = await self._integrate_with_training(request, agent_profile)
                training_session_id = training_result.get('training_session_id')
                improvement_score = training_result.get('improvement_score', 0.0)
                
                if training_session_id:
                    self.performance_metrics['training_integrations'] += 1
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update average response time
            self._update_average_response_time(response_time)
            
            # Update success metrics
            self.performance_metrics['successful_enhancements'] += 1
            
            return TaskToolResponse(
                request_id=request.request_id,
                success=True,
                enhanced_prompt=enhanced_prompt,
                agent_profile=agent_profile,
                performance_metrics=self.performance_metrics.copy(),
                prompt_improvement_score=improvement_score,
                training_session_id=training_session_id,
                cache_hit=False,
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Error creating enhanced subprocess: {e}")
            self.performance_metrics['failed_enhancements'] += 1
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return TaskToolResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                performance_metrics=self.performance_metrics.copy(),
                response_time_ms=response_time
            )
    
    async def _build_enhanced_prompt(self, request: TaskToolRequest, agent_profile: AgentProfile) -> str:
        """Build enhanced prompt with agent profile integration."""
        try:
            # Use AgentProfileLoader to build enhanced prompt
            enhanced_prompt = await self.agent_loader.build_enhanced_task_prompt(
                request.agent_name, 
                request.task_context
            )
            
            # Add Task Tool specific enhancements
            task_tool_enhanced = f"""
{enhanced_prompt}

**Task Tool Integration**:
- **Request ID**: {request.request_id}
- **Request Timestamp**: {request.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **Enhanced Prompts**: {'Enabled' if request.enhanced_prompts else 'Disabled'}
- **Training Integration**: {'Enabled' if request.training_integration else 'Disabled'}
- **Performance Optimization**: {'SharedPromptCache' if self.shared_cache else 'Basic'}

**Subprocess Enhancement Context**:
This subprocess has been enhanced with comprehensive agent profile integration, 
improved prompt system, and training-based optimization for maximum effectiveness.
The agent profile provides specialized context, capabilities, and operational patterns
optimized for this specific agent type and task requirements.

**Framework Compliance**: Task Tool Profile Integration v014 - Full framework integration
"""
            
            return task_tool_enhanced
            
        except Exception as e:
            logger.error(f"Error building enhanced prompt: {e}")
            # Fallback to basic prompt
            return self._build_basic_prompt(request, agent_profile)
    
    def _build_basic_prompt(self, request: TaskToolRequest, agent_profile: AgentProfile) -> str:
        """Build basic prompt as fallback."""
        return f"""**{agent_profile.nickname}**: {request.task_description}

TEMPORAL CONTEXT: Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.

**Task Requirements**:
{chr(10).join(f"- {req}" for req in request.requirements)}

**Expected Deliverables**:
{chr(10).join(f"- {deliverable}" for deliverable in request.deliverables)}

**Dependencies**:
{chr(10).join(f"- {dep}" for dep in request.dependencies)}

**Authority**: {agent_profile.role} operations
**Priority**: {request.priority}

**Profile Context**: Basic agent profile integration from {agent_profile.tier.value} tier.
"""
    
    async def _integrate_with_training(self, request: TaskToolRequest, agent_profile: AgentProfile) -> Dict[str, Any]:
        """Integrate with training system for continuous improvement."""
        try:
            if not self.training_integration:
                return {}
            
            # Check if there's an improved prompt available
            if agent_profile.has_improved_prompt:
                return {
                    'training_session_id': agent_profile.improved_prompt.training_session_id,
                    'improvement_score': agent_profile.improved_prompt.improvement_score,
                    'integration_type': 'existing_improved_prompt'
                }
            
            # Create training context for future improvements
            training_context = {
                'agent_type': request.agent_name,
                'task_description': request.task_description,
                'context': request.context,
                'requirements': request.requirements,
                'request_id': request.request_id,
                'timestamp': request.timestamp.isoformat()
            }
            
            # This would be used for training when user provides corrections
            return {
                'training_context': training_context,
                'integration_type': 'training_ready'
            }
            
        except Exception as e:
            logger.error(f"Error integrating with training system: {e}")
            return {}
    
    def _generate_cache_key(self, request: TaskToolRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        
        # Create hash from request components
        key_components = [
            request.agent_name,
            request.task_description,
            json.dumps(request.requirements, sort_keys=True),
            json.dumps(request.deliverables, sort_keys=True),
            request.priority
        ]
        
        key_string = "|".join(key_components)
        hash_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"task_tool_enhanced:{request.agent_name}:{hash_key}"
    
    async def _get_cached_prompt(self, cache_key: str) -> Optional[str]:
        """Get cached prompt if available."""
        if self.shared_cache:
            return self.shared_cache.get(cache_key)
        return None
    
    async def _cache_prompt(self, cache_key: str, prompt: str) -> None:
        """Cache prompt for future use."""
        if self.shared_cache:
            self.shared_cache.set(cache_key, prompt, ttl=3600)  # 1 hour TTL
    
    def _add_to_history(self, request: TaskToolRequest) -> None:
        """Add request to history."""
        self.request_history.append(request)
        
        # Trim history if too large
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
    
    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time."""
        current_avg = self.performance_metrics['average_response_time_ms']
        request_count = self.performance_metrics['subprocess_requests']
        
        if request_count > 0:
            self.performance_metrics['average_response_time_ms'] = (
                (current_avg * (request_count - 1) + response_time) / request_count
            )
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and metrics."""
        status = {
            'service_running': self.running,
            'integration_components': {
                'agent_loader': self.agent_loader is not None,
                'shared_cache': self.shared_cache is not None,
                'agent_registry': self.agent_registry is not None,
                'training_integration': self.training_integration is not None
            },
            'performance_metrics': self.performance_metrics.copy(),
            'request_history_size': len(self.request_history),
            'cache_efficiency': self._calculate_cache_efficiency(),
            'service_health': await self._check_service_health()
        }
        
        # Add agent loader metrics
        if self.agent_loader:
            loader_metrics = await self.agent_loader.get_performance_metrics()
            status['agent_loader_metrics'] = loader_metrics
        
        # Add shared cache metrics
        if self.shared_cache:
            cache_metrics = self.shared_cache.get_metrics()
            status['shared_cache_metrics'] = cache_metrics
        
        return status
    
    def _calculate_cache_efficiency(self) -> float:
        """Calculate cache efficiency percentage."""
        total_requests = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        if total_requests == 0:
            return 0.0
        return (self.performance_metrics['cache_hits'] / total_requests) * 100
    
    async def _check_service_health(self) -> Dict[str, Any]:
        """Check service health."""
        health = {
            'overall_health': 'healthy',
            'components': {}
        }
        
        # Check agent loader
        if self.agent_loader:
            try:
                validation = await self.agent_loader.validate_profile_integration()
                health['components']['agent_loader'] = {
                    'status': 'healthy' if validation['valid'] else 'degraded',
                    'issues': len(validation['issues']),
                    'warnings': len(validation['warnings'])
                }
            except Exception as e:
                health['components']['agent_loader'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Check shared cache
        if self.shared_cache:
            try:
                cache_metrics = self.shared_cache.get_metrics()
                health['components']['shared_cache'] = {
                    'status': 'healthy',
                    'hit_rate': cache_metrics.get('hit_rate', 0.0),
                    'size_mb': cache_metrics.get('size_mb', 0.0)
                }
            except Exception as e:
                health['components']['shared_cache'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Determine overall health
        component_statuses = [comp.get('status', 'unknown') for comp in health['components'].values()]
        if 'error' in component_statuses:
            health['overall_health'] = 'error'
        elif 'degraded' in component_statuses:
            health['overall_health'] = 'degraded'
        
        return health
    
    async def create_subprocess_from_dict(self, request_data: Dict[str, Any]) -> TaskToolResponse:
        """
        Create subprocess from dictionary data.
        
        Args:
            request_data: Dictionary with request parameters
            
        Returns:
            Enhanced subprocess response
        """
        try:
            # Create request object
            request = TaskToolRequest(
                agent_name=request_data['agent_name'],
                task_description=request_data['task_description'],
                context=request_data.get('context', {}),
                requirements=request_data.get('requirements', []),
                deliverables=request_data.get('deliverables', []),
                dependencies=request_data.get('dependencies', []),
                priority=request_data.get('priority', 'medium'),
                memory_categories=request_data.get('memory_categories', []),
                enhanced_prompts=request_data.get('enhanced_prompts', True),
                training_integration=request_data.get('training_integration', True)
            )
            
            return await self.create_enhanced_subprocess(request)
            
        except Exception as e:
            logger.error(f"Error creating subprocess from dict: {e}")
            return TaskToolResponse(
                request_id=str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    async def batch_create_subprocesses(self, requests: List[TaskToolRequest]) -> List[TaskToolResponse]:
        """
        Create multiple subprocesses in batch.
        
        Args:
            requests: List of subprocess requests
            
        Returns:
            List of responses
        """
        try:
            # Create tasks for parallel execution
            tasks = [self.create_enhanced_subprocess(request) for request in requests]
            
            # Execute in parallel
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            results = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    results.append(TaskToolResponse(
                        request_id=requests[i].request_id,
                        success=False,
                        error=str(response)
                    ))
                else:
                    results.append(response)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch subprocess creation: {e}")
            return [TaskToolResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            ) for request in requests]
    
    async def get_request_history(self, 
                                agent_name: Optional[str] = None,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get request history with optional filtering.
        
        Args:
            agent_name: Filter by agent name
            limit: Maximum number of entries
            
        Returns:
            List of request history entries
        """
        try:
            history = self.request_history
            
            # Filter by agent name if specified
            if agent_name:
                history = [req for req in history if req.agent_name == agent_name]
            
            # Apply limit if specified
            if limit:
                history = history[-limit:]
            
            # Convert to dictionary format
            return [
                {
                    'request_id': req.request_id,
                    'agent_name': req.agent_name,
                    'task_description': req.task_description,
                    'timestamp': req.timestamp.isoformat(),
                    'priority': req.priority,
                    'enhanced_prompts': req.enhanced_prompts,
                    'training_integration': req.training_integration
                }
                for req in history
            ]
            
        except Exception as e:
            logger.error(f"Error getting request history: {e}")
            return []
    
    async def enhance_task_delegation(self, agent_name: str, task_description: str, context: str = "") -> str:
        """
        Enhance task delegation with agent profile integration.
        
        Args:
            agent_name: Name of the agent to delegate to
            task_description: Description of the task
            context: Additional context for the task
            
        Returns:
            Enhanced delegation prompt
        """
        try:
            # Create a TaskToolRequest
            request = TaskToolRequest(
                agent_name=agent_name,
                task_description=task_description,
                context={'additional_context': context},
                requirements=[],
                deliverables=[],
                priority='medium'
            )
            
            # Create enhanced subprocess
            response = await self.create_enhanced_subprocess(request)
            
            if response.success and response.enhanced_prompt:
                return response.enhanced_prompt
            else:
                # Fallback to basic delegation
                return f"""**{agent_name.title()}**: {task_description}

TEMPORAL CONTEXT: Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.

**Task Context**: {context}

**Authority**: {agent_name} operations
**Expected Results**: Task completion with operational insights
"""
                
        except Exception as e:
            logger.error(f"Error enhancing task delegation: {e}")
            # Fallback to basic delegation
            return f"""**{agent_name.title()}**: {task_description}

TEMPORAL CONTEXT: Today is {datetime.now().strftime('%B %d, %Y')}. Apply date awareness to task execution.

**Task Context**: {context}

**Authority**: {agent_name} operations
**Expected Results**: Task completion with operational insights
"""


# Factory function
def create_task_tool_integration(config: Optional[Config] = None) -> TaskToolProfileIntegration:
    """Create a TaskToolProfileIntegration instance."""
    return TaskToolProfileIntegration(config)


# Factory function for getting integrator instance
async def get_task_tool_integrator(config: Optional[Config] = None) -> TaskToolProfileIntegration:
    """
    Get a configured and initialized TaskToolProfileIntegration instance.
    
    Args:
        config: Optional configuration object
        
    Returns:
        Initialized TaskToolProfileIntegration instance
    """
    integration = create_task_tool_integration(config)
    await integration.start()
    return integration


# Convenience functions for common operations
async def create_enhanced_subprocess_prompt(agent_name: str, 
                                          task_description: str,
                                          context: Optional[Dict[str, Any]] = None,
                                          requirements: Optional[List[str]] = None,
                                          deliverables: Optional[List[str]] = None) -> str:
    """
    Convenience function to create enhanced subprocess prompt.
    
    Args:
        agent_name: Name of the agent
        task_description: Description of the task
        context: Additional context
        requirements: Task requirements
        deliverables: Expected deliverables
        
    Returns:
        Enhanced subprocess prompt
    """
    integration = create_task_tool_integration()
    await integration.start()
    
    try:
        request = TaskToolRequest(
            agent_name=agent_name,
            task_description=task_description,
            context=context or {},
            requirements=requirements or [],
            deliverables=deliverables or []
        )
        
        response = await integration.create_enhanced_subprocess(request)
        return response.enhanced_prompt or ""
        
    finally:
        await integration.stop()


if __name__ == "__main__":
    # Demo and testing
    async def demo():
        """Demonstrate TaskToolProfileIntegration usage."""
        print("🚀 TaskToolProfileIntegration Demo")
        print("=" * 50)
        
        # Initialize integration
        integration = create_task_tool_integration()
        await integration.start()
        
        try:
            # Create a test request
            request = TaskToolRequest(
                agent_name="engineer",
                task_description="Implement JWT authentication system",
                requirements=[
                    "Use secure token generation",
                    "Implement token expiration",
                    "Add refresh token support"
                ],
                deliverables=[
                    "JWT authentication middleware",
                    "Token validation service",
                    "Unit tests for auth system"
                ],
                priority="high"
            )
            
            # Create enhanced subprocess
            print(f"\n📋 Creating enhanced subprocess for {request.agent_name}")
            response = await integration.create_enhanced_subprocess(request)
            
            if response.success:
                print(f"✅ Successfully created enhanced subprocess")
                print(f"  Request ID: {response.request_id}")
                print(f"  Cache Hit: {response.cache_hit}")
                print(f"  Response Time: {response.response_time_ms:.2f}ms")
                print(f"  Improvement Score: {response.prompt_improvement_score}")
                
                if response.enhanced_prompt:
                    print(f"\n📝 Enhanced Prompt (first 500 chars):")
                    print(response.enhanced_prompt[:500] + "...")
            else:
                print(f"❌ Failed to create subprocess: {response.error}")
            
            # Get integration status
            status = await integration.get_integration_status()
            print(f"\n📊 Integration Status:")
            print(f"  Service Running: {status['service_running']}")
            print(f"  Total Requests: {status['performance_metrics']['subprocess_requests']}")
            print(f"  Success Rate: {status['performance_metrics']['successful_enhancements']}/{status['performance_metrics']['subprocess_requests']}")
            print(f"  Cache Efficiency: {status['cache_efficiency']:.1f}%")
            print(f"  Overall Health: {status['service_health']['overall_health']}")
            
        finally:
            await integration.stop()
            print("\n✅ Demo completed")
    
    # Run demo
    asyncio.run(demo())


# Alias for backwards compatibility with test imports
TaskToolProfileIntegrator = TaskToolProfileIntegration

__all__ = [
    'TaskToolProfileIntegration',
    'TaskToolProfileIntegrator',
    'TaskToolRequest', 
    'TaskToolResponse',
    'create_task_tool_integration',
    'get_task_tool_integrator',
    'create_enhanced_subprocess_prompt',
]