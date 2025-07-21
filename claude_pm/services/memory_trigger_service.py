"""
Memory Trigger Service - Event-driven memory management with intelligent triggers

This service provides:
- Event-based memory triggers
- Intelligent memory collection
- Context-aware memory storage
- Automatic memory categorization
- Performance monitoring

Created: 2025-07-16 (Emergency restoration)
Purpose: Restore missing claude_pm.services.memory_trigger_service import
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from claude_pm.services.memory import (
    FlexibleMemoryService, 
    MemoryCategory, 
    MemoryQuery,
    MemoryItem,
    create_flexible_memory_service
)

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    """Types of memory triggers"""
    PROJECT_START = "project_start"
    PROJECT_END = "project_end"
    TASK_COMPLETION = "task_completion"
    ERROR_OCCURRENCE = "error_occurrence"
    DECISION_POINT = "decision_point"
    WORKFLOW_STEP = "workflow_step"
    AGENT_INTERACTION = "agent_interaction"
    PERFORMANCE_METRIC = "performance_metric"
    CONFIGURATION_CHANGE = "configuration_change"
    DEPLOYMENT_EVENT = "deployment_event"

class TriggerPriority(Enum):
    """Priority levels for memory triggers"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TriggerEvent:
    """Memory trigger event data"""
    trigger_type: TriggerType
    priority: TriggerPriority
    project_id: str
    context: Dict[str, Any]
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TriggerRule:
    """Rule for memory trigger activation"""
    name: str
    trigger_type: TriggerType
    condition: Callable[[TriggerEvent], bool]
    memory_category: MemoryCategory
    priority_threshold: TriggerPriority
    enabled: bool = True
    description: str = ""

class MemoryTriggerService:
    """
    Memory Trigger Service - Event-driven memory management
    
    Features:
    - Event-based memory collection
    - Intelligent trigger rules
    - Context-aware memory storage
    - Performance monitoring
    - Async processing
    """
    
    def __init__(self, memory_service: Optional[FlexibleMemoryService] = None):
        """Initialize memory trigger service"""
        self.memory_service = memory_service or create_flexible_memory_service()
        self.trigger_rules: List[TriggerRule] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_processed': 0,
            'memories_created': 0,
            'errors': 0,
            'last_processed': None
        }
        self._running = False
        
        # Initialize default trigger rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default memory trigger rules"""
        
        # Project lifecycle triggers
        self.add_trigger_rule(TriggerRule(
            name="project_start_memory",
            trigger_type=TriggerType.PROJECT_START,
            condition=lambda event: True,  # Always trigger
            memory_category=MemoryCategory.PROJECT,
            priority_threshold=TriggerPriority.MEDIUM,
            description="Capture project start events"
        ))
        
        self.add_trigger_rule(TriggerRule(
            name="project_completion_memory",
            trigger_type=TriggerType.PROJECT_END,
            condition=lambda event: True,
            memory_category=MemoryCategory.PROJECT,
            priority_threshold=TriggerPriority.HIGH,
            description="Capture project completion events"
        ))
        
        # Error and decision triggers
        self.add_trigger_rule(TriggerRule(
            name="error_memory",
            trigger_type=TriggerType.ERROR_OCCURRENCE,
            condition=lambda event: event.priority in [TriggerPriority.HIGH, TriggerPriority.CRITICAL],
            memory_category=MemoryCategory.ERROR,
            priority_threshold=TriggerPriority.HIGH,
            description="Capture significant errors for learning"
        ))
        
        self.add_trigger_rule(TriggerRule(
            name="decision_memory",
            trigger_type=TriggerType.DECISION_POINT,
            condition=lambda event: True,
            memory_category=MemoryCategory.DECISION,
            priority_threshold=TriggerPriority.MEDIUM,
            description="Capture important decisions"
        ))
        
        # Workflow and agent triggers
        self.add_trigger_rule(TriggerRule(
            name="workflow_memory",
            trigger_type=TriggerType.WORKFLOW_STEP,
            condition=lambda event: event.context.get('completed', False),
            memory_category=MemoryCategory.WORKFLOW,
            priority_threshold=TriggerPriority.LOW,
            description="Capture workflow step completions"
        ))
        
        self.add_trigger_rule(TriggerRule(
            name="agent_interaction_memory",
            trigger_type=TriggerType.AGENT_INTERACTION,
            condition=lambda event: event.context.get('success', True),
            memory_category=MemoryCategory.AGENT,
            priority_threshold=TriggerPriority.LOW,
            description="Capture successful agent interactions"
        ))
    
    async def initialize(self) -> bool:
        """Initialize the memory trigger service"""
        try:
            logger.info("Initializing memory trigger service...")
            
            # Initialize memory service
            if not await self.memory_service.initialize():
                logger.error("Failed to initialize memory service")
                return False
            
            # Start event processing
            await self.start_processing()
            
            logger.info("Memory trigger service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize memory trigger service: {e}")
            return False
    
    async def start_processing(self):
        """Start processing trigger events"""
        if self._running:
            return
        
        self._running = True
        self.processing_task = asyncio.create_task(self._process_events())
        logger.info("Memory trigger event processing started")
    
    async def stop_processing(self):
        """Stop processing trigger events"""
        if not self._running:
            return
        
        self._running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Memory trigger event processing stopped")
    
    async def _process_events(self):
        """Process events from the queue"""
        while self._running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_trigger_event(event)
                self.stats['events_processed'] += 1
                self.stats['last_processed'] = datetime.now()
                
            except asyncio.TimeoutError:
                continue  # No events to process
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing trigger event: {e}")
                self.stats['errors'] += 1
    
    async def _handle_trigger_event(self, event: TriggerEvent):
        """Handle a trigger event"""
        try:
            logger.debug(f"Processing trigger event: {event.trigger_type} for project {event.project_id}")
            
            # Find matching trigger rules
            matching_rules = [
                rule for rule in self.trigger_rules
                if (rule.enabled and 
                    rule.trigger_type == event.trigger_type and
                    self._meets_priority_threshold(event.priority, rule.priority_threshold) and
                    rule.condition(event))
            ]
            
            if not matching_rules:
                logger.debug(f"No matching rules for event: {event.trigger_type}")
                return
            
            # Process each matching rule
            for rule in matching_rules:
                await self._execute_trigger_rule(rule, event)
                
        except Exception as e:
            logger.error(f"Error handling trigger event: {e}")
            self.stats['errors'] += 1
    
    async def _execute_trigger_rule(self, rule: TriggerRule, event: TriggerEvent):
        """Execute a trigger rule"""
        try:
            # Generate memory content from event
            memory_content = self._generate_memory_content(event, rule)
            
            # Create memory metadata
            memory_metadata = {
                'trigger_type': event.trigger_type.value,
                'trigger_rule': rule.name,
                'priority': event.priority.value,
                'source': event.source,
                'timestamp': event.timestamp.isoformat(),
                'context': event.context,
                'event_metadata': event.metadata
            }
            
            # Add memory
            memory_id = await self.memory_service.add_memory(
                project_id=event.project_id,
                content=memory_content,
                category=rule.memory_category
            )
            
            self.stats['memories_created'] += 1
            logger.debug(f"Created memory {memory_id} from rule {rule.name}")
            
        except Exception as e:
            logger.error(f"Error executing trigger rule {rule.name}: {e}")
            self.stats['errors'] += 1
    
    def _generate_memory_content(self, event: TriggerEvent, rule: TriggerRule) -> str:
        """Generate memory content from trigger event"""
        content_parts = []
        
        # Add basic event information
        content_parts.append(f"Event: {event.trigger_type.value}")
        content_parts.append(f"Priority: {event.priority.value}")
        content_parts.append(f"Source: {event.source}")
        content_parts.append(f"Timestamp: {event.timestamp.isoformat()}")
        
        # Add context information
        if event.context:
            content_parts.append("Context:")
            for key, value in event.context.items():
                content_parts.append(f"  {key}: {value}")
        
        # Add event metadata
        if event.metadata:
            content_parts.append("Metadata:")
            for key, value in event.metadata.items():
                content_parts.append(f"  {key}: {value}")
        
        return "\n".join(content_parts)
    
    def _meets_priority_threshold(self, event_priority: TriggerPriority, threshold: TriggerPriority) -> bool:
        """Check if event priority meets rule threshold"""
        priority_levels = {
            TriggerPriority.LOW: 1,
            TriggerPriority.MEDIUM: 2,
            TriggerPriority.HIGH: 3,
            TriggerPriority.CRITICAL: 4
        }
        
        return priority_levels[event_priority] >= priority_levels[threshold]
    
    async def trigger_event(self, event: TriggerEvent):
        """Add a trigger event to the processing queue"""
        try:
            await self.event_queue.put(event)
            logger.debug(f"Queued trigger event: {event.trigger_type} for project {event.project_id}")
        except Exception as e:
            logger.error(f"Error queuing trigger event: {e}")
    
    def add_trigger_rule(self, rule: TriggerRule):
        """Add a trigger rule"""
        self.trigger_rules.append(rule)
        logger.debug(f"Added trigger rule: {rule.name}")
    
    def remove_trigger_rule(self, rule_name: str) -> bool:
        """Remove a trigger rule by name"""
        for i, rule in enumerate(self.trigger_rules):
            if rule.name == rule_name:
                del self.trigger_rules[i]
                logger.debug(f"Removed trigger rule: {rule_name}")
                return True
        return False
    
    def get_trigger_rules(self) -> List[TriggerRule]:
        """Get all trigger rules"""
        return self.trigger_rules.copy()
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a trigger rule"""
        for rule in self.trigger_rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.debug(f"Enabled trigger rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a trigger rule"""
        for rule in self.trigger_rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.debug(f"Disabled trigger rule: {rule_name}")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'events_processed': self.stats['events_processed'],
            'memories_created': self.stats['memories_created'],
            'errors': self.stats['errors'],
            'last_processed': self.stats['last_processed'].isoformat() if self.stats['last_processed'] else None,
            'queue_size': self.event_queue.qsize(),
            'running': self._running,
            'total_rules': len(self.trigger_rules),
            'enabled_rules': len([r for r in self.trigger_rules if r.enabled])
        }
    
    async def search_triggered_memories(self, project_id: str, trigger_type: Optional[TriggerType] = None, 
                                      category: Optional[MemoryCategory] = None, 
                                      limit: int = 10) -> List[MemoryItem]:
        """Search memories created by triggers"""
        query = MemoryQuery(
            text=trigger_type.value if trigger_type else "",
            categories=[category] if category else None,
            limit=limit
        )
        
        memories = await self.memory_service.search_memories(project_id, query)
        
        # Filter by trigger type if specified
        if trigger_type:
            memories = [
                m for m in memories 
                if m.metadata.get('trigger_type') == trigger_type.value
            ]
        
        return memories
    
    async def shutdown(self):
        """Shutdown the service"""
        await self.stop_processing()
        logger.info("Memory trigger service shutdown complete")

# Convenience functions
async def create_memory_trigger_service(memory_service: Optional[FlexibleMemoryService] = None) -> MemoryTriggerService:
    """Create and initialize a memory trigger service"""
    service = MemoryTriggerService(memory_service)
    await service.initialize()
    return service

def create_trigger_event(trigger_type: TriggerType, project_id: str, 
                        context: Dict[str, Any], source: str,
                        priority: TriggerPriority = TriggerPriority.MEDIUM,
                        metadata: Optional[Dict[str, Any]] = None) -> TriggerEvent:
    """Create a trigger event"""
    return TriggerEvent(
        trigger_type=trigger_type,
        priority=priority,
        project_id=project_id,
        context=context,
        timestamp=datetime.now(),
        source=source,
        metadata=metadata or {}
    )

# Export key classes and functions
__all__ = [
    'MemoryTriggerService',
    'TriggerEvent',
    'TriggerRule',
    'TriggerType', 
    'TriggerPriority',
    'create_memory_trigger_service',
    'create_trigger_event'
]