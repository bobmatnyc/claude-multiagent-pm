"""
Framework Memory Hooks

Integration layer for automatic memory creation throughout the Claude PM Framework.
Provides hooks into workflow operations, agent completions, and system events
for seamless memory capture.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
import inspect

from .trigger_types import TriggerType, TriggerPriority
from .trigger_policies import TriggerPolicyEngine
from .services.unified_service import FlexibleMemoryService
from .interfaces.models import MemoryCategory

# Forward declarations to avoid circular imports
MemoryTriggerOrchestrator = None
TriggerEvent = None
TriggerResult = None


@dataclass
class HookContext:
    """Context information for memory hook execution."""
    
    operation_name: str
    project_name: str
    source: str
    start_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def duration_ms(self) -> float:
        """Get operation duration in milliseconds."""
        return (time.time() - self.start_time) * 1000


class FrameworkMemoryHooks:
    """
    Framework-wide memory hooks for automatic memory creation.
    
    Provides integration points throughout the framework for capturing
    memories from workflows, agent operations, and system events.
    """
    
    def __init__(
        self, 
        memory_service: FlexibleMemoryService,
        trigger_orchestrator,
        policy_engine: TriggerPolicyEngine,
        config: Dict[str, Any] = None
    ):
        """
        Initialize framework memory hooks.
        
        Args:
            memory_service: The memory service instance
            trigger_orchestrator: The trigger orchestrator
            policy_engine: The policy engine
            config: Configuration dictionary
        """
        self.memory_service = memory_service
        self.trigger_orchestrator = trigger_orchestrator
        self.policy_engine = policy_engine
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self._enabled = self.config.get("enabled", True)
        self._hook_registry: Dict[str, List[Callable]] = {}
        self._active_contexts: Dict[str, HookContext] = {}
        
        # Performance metrics
        self.metrics = {
            "hooks_executed": 0,
            "successful_hooks": 0,
            "failed_hooks": 0,
            "memory_captures": 0,
            "average_hook_time": 0.0,
            "hooks_by_type": {}
        }
        
        # Initialize core hooks
        self._initialize_core_hooks()
    
    def _initialize_core_hooks(self):
        """Initialize core framework hooks."""
        self.logger.info("Initializing core framework memory hooks")
        
        # Register built-in hook types
        self._hook_registry.update({
            "workflow_start": [],
            "workflow_complete": [],
            "workflow_error": [],
            "agent_operation_start": [],
            "agent_operation_complete": [],
            "agent_operation_error": [],
            "issue_created": [],
            "issue_resolved": [],
            "issue_error": [],
            "project_milestone": [],
            "error_resolution": [],
            "knowledge_capture": [],
            "pattern_detection": [],
            "decision_point": []
        })
    
    def register_hook(self, hook_type: str, callback: Callable):
        """
        Register a memory hook callback.
        
        Args:
            hook_type: Type of hook to register
            callback: Callback function to execute
        """
        if hook_type not in self._hook_registry:
            self._hook_registry[hook_type] = []
        
        self._hook_registry[hook_type].append(callback)
        self.logger.debug(f"Registered hook callback for type: {hook_type}")
    
    def unregister_hook(self, hook_type: str, callback: Callable) -> bool:
        """
        Unregister a memory hook callback.
        
        Args:
            hook_type: Type of hook to unregister
            callback: Callback function to remove
            
        Returns:
            bool: True if callback was removed
        """
        if hook_type in self._hook_registry:
            try:
                self._hook_registry[hook_type].remove(callback)
                self.logger.debug(f"Unregistered hook callback for type: {hook_type}")
                return True
            except ValueError:
                pass
        
        return False
    
    async def execute_hook(self, hook_type: str, context: HookContext, **kwargs) -> List:
        """
        Execute all registered hooks for a given type.
        
        Args:
            hook_type: Type of hook to execute
            context: Hook execution context
            **kwargs: Additional hook arguments
            
        Returns:
            List[TriggerResult]: Results from all triggered memories
        """
        if not self._enabled:
            return []
        
        start_time = time.time()
        results = []
        
        try:
            # Update metrics
            self.metrics["hooks_executed"] += 1
            self.metrics["hooks_by_type"][hook_type] = (
                self.metrics["hooks_by_type"].get(hook_type, 0) + 1
            )
            
            # Execute registered callbacks
            callbacks = self._hook_registry.get(hook_type, [])
            for callback in callbacks:
                try:
                    # Execute callback (may be async or sync)
                    if inspect.iscoroutinefunction(callback):
                        await callback(context, **kwargs)
                    else:
                        callback(context, **kwargs)
                        
                except Exception as e:
                    self.logger.error(f"Hook callback failed for {hook_type}: {e}")
            
            # Create memory trigger event
            trigger_event = self._create_trigger_event(hook_type, context, **kwargs)
            
            if trigger_event:
                # Trigger memory creation
                result = await self.trigger_orchestrator.trigger_memory_creation(trigger_event)
                results.append(result)
                
                if result.success:
                    self.metrics["memory_captures"] += 1
            
            # Update metrics
            self.metrics["successful_hooks"] += 1
            hook_time = (time.time() - start_time) * 1000
            self.metrics["average_hook_time"] = (
                (self.metrics["average_hook_time"] * (self.metrics["hooks_executed"] - 1) + hook_time) /
                self.metrics["hooks_executed"]
            )
            
        except Exception as e:
            self.logger.error(f"Hook execution failed for {hook_type}: {e}")
            self.metrics["failed_hooks"] += 1
        
        return results
    
    def _create_trigger_event(
        self, 
        hook_type: str, 
        context: HookContext, 
        **kwargs
    ) -> Optional[TriggerEvent]:
        """
        Create a trigger event from hook execution.
        
        Args:
            hook_type: Type of hook
            context: Hook execution context
            **kwargs: Additional context
            
        Returns:
            Optional[TriggerEvent]: Trigger event if created
        """
        try:
            # Map hook type to trigger type
            trigger_type_map = {
                "workflow_complete": TriggerType.WORKFLOW_COMPLETION,
                "workflow_error": TriggerType.ERROR_RESOLUTION,
                "agent_operation_complete": TriggerType.AGENT_OPERATION,
                "agent_operation_error": TriggerType.ERROR_RESOLUTION,
                "issue_resolved": TriggerType.ISSUE_RESOLUTION,
                "issue_error": TriggerType.ERROR_RESOLUTION,
                "project_milestone": TriggerType.PROJECT_MILESTONE,
                "error_resolution": TriggerType.ERROR_RESOLUTION,
                "knowledge_capture": TriggerType.KNOWLEDGE_CAPTURE,
                "pattern_detection": TriggerType.PATTERN_DETECTION,
                "decision_point": TriggerType.DECISION_POINT
            }
            
            trigger_type = trigger_type_map.get(hook_type)
            if not trigger_type:
                return None
            
            # Determine priority based on hook type and context
            priority = self._determine_priority(hook_type, context, **kwargs)
            
            # Determine memory category
            category = self._determine_category(hook_type, context, **kwargs)
            
            # Generate content
            content = self._generate_content(hook_type, context, **kwargs)
            
            # Generate tags
            tags = self._generate_tags(hook_type, context, **kwargs)
            
            # Create trigger event
            return TriggerEvent(
                trigger_type=trigger_type,
                priority=priority,
                project_name=context.project_name,
                event_id=str(uuid.uuid4()),
                content=content,
                category=category,
                tags=tags,
                metadata={
                    **context.metadata,
                    "hook_type": hook_type,
                    "operation_name": context.operation_name,
                    "source": context.source,
                    "duration_ms": context.duration_ms(),
                    **kwargs
                },
                source=context.source,
                context={
                    "hook_type": hook_type,
                    "operation_name": context.operation_name,
                    "duration_ms": context.duration_ms()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create trigger event for hook {hook_type}: {e}")
            return None
    
    def _determine_priority(self, hook_type: str, context: HookContext, **kwargs) -> TriggerPriority:
        """Determine priority for memory trigger based on hook type and context."""
        
        # Error-related hooks are critical
        if "error" in hook_type:
            return TriggerPriority.CRITICAL
        
        # Workflow completions are high priority
        if "workflow_complete" in hook_type:
            return TriggerPriority.HIGH
        
        # Agent operations are medium priority
        if "agent_operation" in hook_type:
            return TriggerPriority.MEDIUM
        
        # Issue resolution is high priority
        if "issue_resolved" in hook_type:
            return TriggerPriority.HIGH
        
        # Project milestones are high priority
        if "project_milestone" in hook_type:
            return TriggerPriority.HIGH
        
        # Decision points are high priority
        if "decision_point" in hook_type:
            return TriggerPriority.HIGH
        
        # Default to medium priority
        return TriggerPriority.MEDIUM
    
    def _determine_category(self, hook_type: str, context: HookContext, **kwargs) -> MemoryCategory:
        """Determine memory category based on hook type and context."""
        
        # Error-related hooks go to error category
        if "error" in hook_type:
            return MemoryCategory.ERROR
        
        # Workflow and agent operations are patterns
        if "workflow" in hook_type or "agent_operation" in hook_type:
            return MemoryCategory.PATTERN
        
        # Issue resolution is project-related
        if "issue" in hook_type:
            return MemoryCategory.PROJECT
        
        # Project milestones are project-related
        if "project_milestone" in hook_type:
            return MemoryCategory.PROJECT
        
        # Decision points are project-related
        if "decision_point" in hook_type:
            return MemoryCategory.PROJECT
        
        # Knowledge capture is pattern-related
        if "knowledge_capture" in hook_type:
            return MemoryCategory.PATTERN
        
        # Pattern detection is pattern-related
        if "pattern_detection" in hook_type:
            return MemoryCategory.PATTERN
        
        # Default to project
        return MemoryCategory.PROJECT
    
    def _generate_content(self, hook_type: str, context: HookContext, **kwargs) -> str:
        """Generate memory content based on hook type and context."""
        
        base_content = f"Framework operation: {context.operation_name}"
        
        if hook_type == "workflow_complete":
            success = kwargs.get("success", False)
            status = "successful" if success else "failed"
            base_content = f"Workflow '{context.operation_name}' completed {status}"
            
            if success:
                base_content += f" in {context.duration_ms():.1f}ms"
            
            # Add workflow details
            if "workflow_type" in kwargs:
                base_content += f" (type: {kwargs['workflow_type']})"
            
            if "results" in kwargs:
                base_content += f"\nResults: {kwargs['results']}"
        
        elif hook_type == "agent_operation_complete":
            agent_type = kwargs.get("agent_type", "unknown")
            base_content = f"Agent operation completed: {agent_type} - {context.operation_name}"
            
            if context.duration_ms() > 0:
                base_content += f" (Duration: {context.duration_ms():.1f}ms)"
            
            if "results" in kwargs:
                base_content += f"\nResults: {kwargs['results']}"
        
        elif hook_type == "issue_resolved":
            issue_id = kwargs.get("issue_id", "unknown")
            base_content = f"Issue resolved: {issue_id}"
            
            if "resolution" in kwargs:
                base_content += f"\nResolution: {kwargs['resolution']}"
        
        elif "error" in hook_type:
            error_type = kwargs.get("error_type", "unknown")
            base_content = f"Error resolution: {error_type}"
            
            if "error_message" in kwargs:
                base_content += f"\nError: {kwargs['error_message']}"
            
            if "solution" in kwargs:
                base_content += f"\nSolution: {kwargs['solution']}"
        
        elif hook_type == "project_milestone":
            milestone = kwargs.get("milestone", "unknown")
            base_content = f"Project milestone reached: {milestone}"
            
            if "description" in kwargs:
                base_content += f"\nDescription: {kwargs['description']}"
        
        elif hook_type == "decision_point":
            decision = kwargs.get("decision", "unknown")
            base_content = f"Decision point: {decision}"
            
            if "rationale" in kwargs:
                base_content += f"\nRationale: {kwargs['rationale']}"
        
        elif hook_type == "knowledge_capture":
            knowledge_type = kwargs.get("knowledge_type", "general")
            base_content = f"Knowledge captured: {knowledge_type}"
            
            if "content" in kwargs:
                base_content += f"\nContent: {kwargs['content']}"
        
        elif hook_type == "pattern_detection":
            pattern_type = kwargs.get("pattern_type", "unknown")
            base_content = f"Pattern detected: {pattern_type}"
            
            if "description" in kwargs:
                base_content += f"\nDescription: {kwargs['description']}"
        
        return base_content
    
    def _generate_tags(self, hook_type: str, context: HookContext, **kwargs) -> List[str]:
        """Generate memory tags based on hook type and context."""
        
        tags = [
            hook_type,
            context.source,
            context.operation_name
        ]
        
        # Add context-specific tags
        if context.tags:
            tags.extend(context.tags)
        
        # Add hook-specific tags
        if hook_type == "workflow_complete":
            tags.append("workflow")
            if kwargs.get("success", False):
                tags.append("success")
            else:
                tags.append("failure")
        
        elif hook_type == "agent_operation_complete":
            tags.append("agent_operation")
            if "agent_type" in kwargs:
                tags.append(kwargs["agent_type"])
        
        elif hook_type == "issue_resolved":
            tags.append("issue_resolution")
            if "issue_id" in kwargs:
                tags.append(kwargs["issue_id"])
        
        elif "error" in hook_type:
            tags.append("error_resolution")
            if "error_type" in kwargs:
                tags.append(kwargs["error_type"])
        
        elif hook_type == "project_milestone":
            tags.append("milestone")
            if "milestone" in kwargs:
                tags.append(kwargs["milestone"])
        
        elif hook_type == "decision_point":
            tags.append("decision")
            if "decision" in kwargs:
                tags.append(kwargs["decision"])
        
        elif hook_type == "knowledge_capture":
            tags.append("knowledge")
            if "knowledge_type" in kwargs:
                tags.append(kwargs["knowledge_type"])
        
        elif hook_type == "pattern_detection":
            tags.append("pattern")
            if "pattern_type" in kwargs:
                tags.append(kwargs["pattern_type"])
        
        # Remove duplicates and empty tags
        tags = list(set(tag for tag in tags if tag))
        
        return tags
    
    # Convenience methods for common hooks
    
    async def workflow_started(self, context: HookContext, **kwargs) -> List:
        """Hook for workflow start."""
        return await self.execute_hook("workflow_start", context, **kwargs)
    
    async def workflow_completed(self, context: HookContext, **kwargs) -> List:
        """Hook for workflow completion."""
        return await self.execute_hook("workflow_complete", context, **kwargs)
    
    async def workflow_error(self, context: HookContext, **kwargs) -> List:
        """Hook for workflow errors."""
        return await self.execute_hook("workflow_error", context, **kwargs)
    
    async def agent_operation_started(self, context: HookContext, **kwargs) -> List:
        """Hook for agent operation start."""
        return await self.execute_hook("agent_operation_start", context, **kwargs)
    
    async def agent_operation_completed(self, context: HookContext, **kwargs) -> List:
        """Hook for agent operation completion."""
        return await self.execute_hook("agent_operation_complete", context, **kwargs)
    
    async def agent_operation_error(self, context: HookContext, **kwargs) -> List:
        """Hook for agent operation errors."""
        return await self.execute_hook("agent_operation_error", context, **kwargs)
    
    async def issue_created(self, context: HookContext, **kwargs) -> List:
        """Hook for issue creation."""
        return await self.execute_hook("issue_created", context, **kwargs)
    
    async def issue_resolved(self, context: HookContext, **kwargs) -> List:
        """Hook for issue resolution."""
        return await self.execute_hook("issue_resolved", context, **kwargs)
    
    async def issue_error(self, context: HookContext, **kwargs) -> List:
        """Hook for issue errors."""
        return await self.execute_hook("issue_error", context, **kwargs)
    
    async def project_milestone(self, context: HookContext, **kwargs) -> List:
        """Hook for project milestones."""
        return await self.execute_hook("project_milestone", context, **kwargs)
    
    async def error_resolution(self, context: HookContext, **kwargs) -> List:
        """Hook for error resolution."""
        return await self.execute_hook("error_resolution", context, **kwargs)
    
    async def knowledge_capture(self, context: HookContext, **kwargs) -> List:
        """Hook for knowledge capture."""
        return await self.execute_hook("knowledge_capture", context, **kwargs)
    
    async def pattern_detection(self, context: HookContext, **kwargs) -> List:
        """Hook for pattern detection."""
        return await self.execute_hook("pattern_detection", context, **kwargs)
    
    async def decision_point(self, context: HookContext, **kwargs) -> List:
        """Hook for decision points."""
        return await self.execute_hook("decision_point", context, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get framework hooks metrics."""
        return {
            **self.metrics,
            "enabled": self._enabled,
            "registered_hooks": {
                hook_type: len(callbacks)
                for hook_type, callbacks in self._hook_registry.items()
            },
            "active_contexts": len(self._active_contexts)
        }
    
    def get_hook_registry(self) -> Dict[str, int]:
        """Get hook registry summary."""
        return {
            hook_type: len(callbacks)
            for hook_type, callbacks in self._hook_registry.items()
        }
    
    def enable(self):
        """Enable framework hooks."""
        self._enabled = True
        self.logger.info("Framework memory hooks enabled")
    
    def disable(self):
        """Disable framework hooks."""
        self._enabled = False
        self.logger.info("Framework memory hooks disabled")
    
    def reset_metrics(self):
        """Reset hook metrics."""
        self.metrics = {
            "hooks_executed": 0,
            "successful_hooks": 0,
            "failed_hooks": 0,
            "memory_captures": 0,
            "average_hook_time": 0.0,
            "hooks_by_type": {}
        }
        self.logger.info("Reset framework hooks metrics")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FrameworkMemoryHooks(enabled={self._enabled}, "
            f"hooks={len(self._hook_registry)}, "
            f"executed={self.metrics['hooks_executed']})"
        )