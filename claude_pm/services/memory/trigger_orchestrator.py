"""
Memory Trigger Orchestrator

Central coordination system for memory triggers throughout the Claude PM Framework.
Handles automatic memory creation based on framework events, workflow completions,
and agent operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import functools
import weakref

from .interfaces.models import MemoryCategory, MemoryItem
from .interfaces.exceptions import MemoryServiceError
from .services.unified_service import FlexibleMemoryService
from .trigger_types import TriggerType, TriggerPriority


@dataclass
class TriggerEvent:
    """Event data for memory trigger activation."""
    
    trigger_type: TriggerType
    priority: TriggerPriority
    project_name: str
    event_id: str
    content: str
    category: MemoryCategory
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = "framework"
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trigger event to dictionary."""
        return {
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "project_name": self.project_name,
            "event_id": self.event_id,
            "content": self.content,
            "category": self.category.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "source": self.source,
            "context": self.context
        }


@dataclass
class TriggerResult:
    """Result of memory trigger processing."""
    
    success: bool
    memory_id: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0
    backend_used: Optional[str] = None
    skipped_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trigger result to dictionary."""
        return {
            "success": self.success,
            "memory_id": self.memory_id,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms,
            "backend_used": self.backend_used,
            "skipped_reason": self.skipped_reason
        }


class MemoryTriggerOrchestrator:
    """
    Central orchestrator for memory triggers throughout the framework.
    
    Coordinates automatic memory creation based on framework events,
    workflow completions, and agent operations with policy-based
    decision making and performance optimization.
    """
    
    def __init__(self, memory_service: FlexibleMemoryService, config: Dict[str, Any] = None):
        """
        Initialize the memory trigger orchestrator.
        
        Args:
            memory_service: The memory service instance
            config: Configuration dictionary
        """
        self.memory_service = memory_service
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self._initialized = False
        self._enabled = self.config.get("enabled", True)
        self._trigger_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._active_triggers: Set[str] = set()
        
        # Trigger registry
        self._trigger_handlers: Dict[TriggerType, List[Callable]] = {}
        self._trigger_policies: Dict[TriggerType, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = {
            "total_triggers": 0,
            "successful_triggers": 0,
            "failed_triggers": 0,
            "skipped_triggers": 0,
            "processing_time_total": 0.0,
            "triggers_by_type": {},
            "triggers_by_priority": {},
            "last_trigger_time": 0.0
        }
        
        # Initialize default policies
        self._setup_default_policies()
        
        # Weak references to prevent circular dependencies
        self._registered_objects: weakref.WeakSet = weakref.WeakSet()
    
    def _setup_default_policies(self):
        """Setup default trigger policies."""
        self._trigger_policies = {
            TriggerType.WORKFLOW_COMPLETION: {
                "enabled": True,
                "min_priority": TriggerPriority.MEDIUM,
                "max_queue_size": 100,
                "batch_size": 10,
                "timeout_seconds": 30
            },
            TriggerType.ISSUE_RESOLUTION: {
                "enabled": True,
                "min_priority": TriggerPriority.HIGH,
                "max_queue_size": 50,
                "batch_size": 5,
                "timeout_seconds": 15
            },
            TriggerType.AGENT_OPERATION: {
                "enabled": True,
                "min_priority": TriggerPriority.MEDIUM,
                "max_queue_size": 200,
                "batch_size": 20,
                "timeout_seconds": 60
            },
            TriggerType.ERROR_RESOLUTION: {
                "enabled": True,
                "min_priority": TriggerPriority.CRITICAL,
                "max_queue_size": 25,
                "batch_size": 3,
                "timeout_seconds": 10
            },
            TriggerType.PROJECT_MILESTONE: {
                "enabled": True,
                "min_priority": TriggerPriority.HIGH,
                "max_queue_size": 30,
                "batch_size": 5,
                "timeout_seconds": 20
            },
            TriggerType.KNOWLEDGE_CAPTURE: {
                "enabled": True,
                "min_priority": TriggerPriority.LOW,
                "max_queue_size": 500,
                "batch_size": 50,
                "timeout_seconds": 120
            },
            TriggerType.PATTERN_DETECTION: {
                "enabled": True,
                "min_priority": TriggerPriority.MEDIUM,
                "max_queue_size": 100,
                "batch_size": 10,
                "timeout_seconds": 45
            },
            TriggerType.DECISION_POINT: {
                "enabled": True,
                "min_priority": TriggerPriority.HIGH,
                "max_queue_size": 50,
                "batch_size": 8,
                "timeout_seconds": 25
            }
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the memory trigger orchestrator.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            self.logger.info("Initializing memory trigger orchestrator...")
            
            # Ensure memory service is initialized
            if not self.memory_service._initialized:
                await self.memory_service.initialize()
            
            # Start processing task
            if self._enabled:
                self._processing_task = asyncio.create_task(self._process_trigger_queue())
                self.logger.info("Memory trigger processing task started")
            
            self._initialized = True
            self.logger.info("Memory trigger orchestrator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory trigger orchestrator: {e}")
            return False
    
    async def trigger_memory_creation(self, event: TriggerEvent) -> TriggerResult:
        """
        Trigger memory creation for a specific event.
        
        Args:
            event: The trigger event data
            
        Returns:
            TriggerResult: Result of trigger processing
        """
        if not self._enabled:
            return TriggerResult(
                success=False,
                skipped_reason="Memory triggers disabled"
            )
        
        if not self._initialized:
            return TriggerResult(
                success=False,
                error="Memory trigger orchestrator not initialized"
            )
        
        start_time = time.time()
        
        try:
            # Check if trigger should be processed
            if not await self._should_process_trigger(event):
                return TriggerResult(
                    success=False,
                    skipped_reason="Trigger filtered by policy"
                )
            
            # Add to processing queue
            await self._trigger_queue.put(event)
            
            # Update metrics
            self.metrics["total_triggers"] += 1
            self.metrics["triggers_by_type"][event.trigger_type.value] = (
                self.metrics["triggers_by_type"].get(event.trigger_type.value, 0) + 1
            )
            self.metrics["triggers_by_priority"][event.priority.value] = (
                self.metrics["triggers_by_priority"].get(event.priority.value, 0) + 1
            )
            
            # For critical triggers, process immediately
            if event.priority == TriggerPriority.CRITICAL:
                return await self._process_trigger_immediate(event)
            
            return TriggerResult(
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000,
                skipped_reason="Queued for background processing"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to trigger memory creation: {e}")
            return TriggerResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _should_process_trigger(self, event: TriggerEvent) -> bool:
        """
        Check if a trigger should be processed based on policies.
        
        Args:
            event: The trigger event
            
        Returns:
            bool: True if trigger should be processed
        """
        policy = self._trigger_policies.get(event.trigger_type, {})
        
        # Check if trigger type is enabled
        if not policy.get("enabled", True):
            return False
        
        # Check minimum priority
        min_priority = policy.get("min_priority", TriggerPriority.LOW)
        if event.priority.value < min_priority.value:
            return False
        
        # Check if event is duplicate (prevent spam)
        if event.event_id in self._active_triggers:
            return False
        
        # Check queue size limits
        max_queue_size = policy.get("max_queue_size", 100)
        if self._trigger_queue.qsize() >= max_queue_size:
            self.logger.warning(f"Trigger queue full for {event.trigger_type.value}, skipping")
            return False
        
        return True
    
    async def _process_trigger_immediate(self, event: TriggerEvent) -> TriggerResult:
        """
        Process a trigger immediately (for critical triggers).
        
        Args:
            event: The trigger event
            
        Returns:
            TriggerResult: Processing result
        """
        start_time = time.time()
        
        try:
            # Create memory directly
            memory_id = await self.memory_service.add_memory(
                project_name=event.project_name,
                content=event.content,
                category=event.category,
                tags=event.tags,
                metadata={
                    **event.metadata,
                    "trigger_type": event.trigger_type.value,
                    "trigger_priority": event.priority.value,
                    "event_id": event.event_id,
                    "source": event.source,
                    "context": event.context
                }
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            if memory_id:
                self.metrics["successful_triggers"] += 1
                self.metrics["processing_time_total"] += processing_time
                self.metrics["last_trigger_time"] = time.time()
                
                return TriggerResult(
                    success=True,
                    memory_id=memory_id,
                    processing_time_ms=processing_time,
                    backend_used=self.memory_service.get_active_backend_name()
                )
            else:
                self.metrics["failed_triggers"] += 1
                return TriggerResult(
                    success=False,
                    error="Memory service returned None memory_id",
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            self.metrics["failed_triggers"] += 1
            return TriggerResult(
                success=False,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _process_trigger_queue(self):
        """Background task to process trigger queue."""
        self.logger.info("Starting trigger queue processing task")
        
        while True:
            try:
                # Get batch of triggers to process
                batch = []
                policy = self._trigger_policies.get(TriggerType.WORKFLOW_COMPLETION, {})
                batch_size = policy.get("batch_size", 10)
                timeout = policy.get("timeout_seconds", 30)
                
                # Collect batch
                try:
                    for _ in range(batch_size):
                        event = await asyncio.wait_for(
                            self._trigger_queue.get(), 
                            timeout=1.0
                        )
                        batch.append(event)
                except asyncio.TimeoutError:
                    # Process whatever we have
                    pass
                
                if not batch:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process batch
                await self._process_trigger_batch(batch)
                
            except Exception as e:
                self.logger.error(f"Error in trigger queue processing: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _process_trigger_batch(self, batch: List[TriggerEvent]):
        """
        Process a batch of triggers.
        
        Args:
            batch: List of trigger events to process
        """
        if not batch:
            return
        
        self.logger.debug(f"Processing trigger batch of {len(batch)} events")
        
        for event in batch:
            try:
                # Mark as active
                self._active_triggers.add(event.event_id)
                
                # Process trigger
                result = await self._process_trigger_immediate(event)
                
                if result.success:
                    self.logger.debug(f"Successfully processed trigger {event.event_id}")
                else:
                    self.logger.warning(f"Failed to process trigger {event.event_id}: {result.error}")
                
            except Exception as e:
                self.logger.error(f"Error processing trigger {event.event_id}: {e}")
                self.metrics["failed_triggers"] += 1
            
            finally:
                # Remove from active set
                self._active_triggers.discard(event.event_id)
    
    def register_trigger_handler(self, trigger_type: TriggerType, handler: Callable):
        """
        Register a custom trigger handler.
        
        Args:
            trigger_type: Type of trigger to handle
            handler: Handler function
        """
        if trigger_type not in self._trigger_handlers:
            self._trigger_handlers[trigger_type] = []
        
        self._trigger_handlers[trigger_type].append(handler)
        self.logger.info(f"Registered trigger handler for {trigger_type.value}")
    
    def update_trigger_policy(self, trigger_type: TriggerType, policy: Dict[str, Any]):
        """
        Update policy for a specific trigger type.
        
        Args:
            trigger_type: Type of trigger to update
            policy: New policy configuration
        """
        if trigger_type not in self._trigger_policies:
            self._trigger_policies[trigger_type] = {}
        
        self._trigger_policies[trigger_type].update(policy)
        self.logger.info(f"Updated trigger policy for {trigger_type.value}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get trigger orchestrator metrics.
        
        Returns:
            Dict[str, Any]: Metrics dictionary
        """
        return {
            **self.metrics,
            "queue_size": self._trigger_queue.qsize(),
            "active_triggers": len(self._active_triggers),
            "enabled": self._enabled,
            "initialized": self._initialized,
            "policies": {
                trigger_type.value: policy 
                for trigger_type, policy in self._trigger_policies.items()
            }
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Dict[str, Any]: Queue status information
        """
        return {
            "queue_size": self._trigger_queue.qsize(),
            "active_triggers": len(self._active_triggers),
            "processing_task_running": (
                self._processing_task and not self._processing_task.done()
            ),
            "enabled": self._enabled
        }
    
    async def flush_queue(self) -> int:
        """
        Flush all pending triggers in the queue.
        
        Returns:
            int: Number of triggers processed
        """
        if not self._initialized:
            return 0
        
        processed = 0
        
        # Process all remaining triggers
        while not self._trigger_queue.empty():
            try:
                event = await self._trigger_queue.get()
                result = await self._process_trigger_immediate(event)
                
                if result.success:
                    processed += 1
                    
            except Exception as e:
                self.logger.error(f"Error flushing trigger queue: {e}")
                break
        
        self.logger.info(f"Flushed {processed} triggers from queue")
        return processed
    
    async def cleanup(self):
        """Cleanup trigger orchestrator resources."""
        self.logger.info("Cleaning up memory trigger orchestrator...")
        
        # Stop processing task
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining triggers
        await self.flush_queue()
        
        # Reset state
        self._initialized = False
        self._active_triggers.clear()
        
        self.logger.info("Memory trigger orchestrator cleanup completed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MemoryTriggerOrchestrator(enabled={self._enabled}, "
            f"initialized={self._initialized}, "
            f"queue_size={self._trigger_queue.qsize()}, "
            f"active_triggers={len(self._active_triggers)})"
        )