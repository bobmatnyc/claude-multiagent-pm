"""
Memory-Enhanced Agent System
============================

Provides memory-augmented agent operations with automatic memory triggers
for Documentation, QA, Ops, and Ticketing agents. Integrates with the
Claude PM Framework's memory trigger infrastructure to enable agents
to automatically create and recall memories during operations.

Key Features:
- Automatic memory creation for successful agent operations
- Memory recall before agent operations for context enhancement
- Agent-specific memory patterns and categorization
- Integration with three-command system (push/deploy/publish)
- Agent coordination memory patterns
- Memory-driven recommendations and learning

Architecture:
- MemoryEnhancedAgent: Base wrapper for memory-aware agents
- AgentMemoryIntegration: Service for agent memory coordination
- Memory triggers for agent operations and handoffs
- Agent-specific memory content standards
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Set
from pathlib import Path
import json
import hashlib

from ..core.base_agent import BaseAgent
from ..services.memory.memory_trigger_service import MemoryTriggerService
from ..services.memory.trigger_orchestrator import TriggerEvent, TriggerResult
from ..services.memory.trigger_types import TriggerType, TriggerPriority
from ..services.memory.interfaces.models import MemoryCategory, MemoryItem


@dataclass
class AgentMemoryPattern:
    """Represents a memory pattern for agent operations."""
    
    agent_type: str
    operation_type: str
    content_template: str
    memory_category: MemoryCategory
    tags: List[str] = field(default_factory=list)
    metadata_keys: List[str] = field(default_factory=list)
    importance_score: float = 1.0
    recall_triggers: List[str] = field(default_factory=list)
    
    def create_memory_content(self, context: Dict[str, Any]) -> str:
        """Create memory content from context using template."""
        try:
            return self.content_template.format(**context)
        except KeyError as e:
            # Handle missing template variables gracefully
            return f"{self.content_template} [Missing context: {e}]"


@dataclass
class AgentMemoryContext:
    """Context for agent memory operations."""
    
    agent_id: str
    agent_type: str
    operation: str
    project_name: str
    context: Dict[str, Any] = field(default_factory=dict)
    related_memories: List[MemoryItem] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "operation": self.operation,
            "project_name": self.project_name,
            "context": self.context,
            "related_memories": [m.to_dict() for m in self.related_memories],
            "recommendations": self.recommendations,
            "patterns_detected": self.patterns_detected
        }


class AgentMemoryPatternRegistry:
    """Registry for agent memory patterns and templates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = {}
        self._initialize_standard_patterns()
    
    def _initialize_standard_patterns(self):
        """Initialize standard memory patterns for core agents."""
        
        # Documentation Agent Patterns
        self.patterns["documentation"] = {
            "scan_project": AgentMemoryPattern(
                agent_type="documentation",
                operation_type="scan_project",
                content_template="Documentation scan completed for {project_name}. Found {patterns_found} documentation patterns with health score {health_score}. Key findings: {key_findings}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["documentation", "project_scan", "health_assessment"],
                metadata_keys=["patterns_found", "health_score", "recommendations", "missing_docs"],
                importance_score=0.8,
                recall_triggers=["documentation_validation", "project_health_check"]
            ),
            "validate_documentation": AgentMemoryPattern(
                agent_type="documentation",
                operation_type="validate_documentation",
                content_template="Documentation validation for {project_name}. Status: {validation_status}. Issues found: {issues_count}. Recommendations: {recommendations}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["documentation", "validation", "quality_check"],
                metadata_keys=["validation_status", "issues_count", "recommendations", "files_checked"],
                importance_score=0.7,
                recall_triggers=["pre_push_validation", "documentation_maintenance"]
            ),
            "documentation_maintenance": AgentMemoryPattern(
                agent_type="documentation",
                operation_type="documentation_maintenance",
                content_template="Documentation maintenance completed for {project_name}. Actions taken: {actions_taken}. Files updated: {files_updated}. Success rate: {success_rate}%",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["documentation", "maintenance", "updates"],
                metadata_keys=["actions_taken", "files_updated", "success_rate", "errors"],
                importance_score=0.6,
                recall_triggers=["documentation_maintenance", "periodic_updates"]
            )
        }
        
        # QA Agent Patterns
        self.patterns["qa"] = {
            "test_execution": AgentMemoryPattern(
                agent_type="qa",
                operation_type="test_execution",
                content_template="Test execution for {project_name}. Test type: {test_type}. Results: {passed_tests}/{total_tests} passed. Success rate: {success_rate}%. Key issues: {key_issues}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["qa", "testing", "execution"],
                metadata_keys=["test_type", "total_tests", "passed_tests", "failed_tests", "execution_time", "key_issues"],
                importance_score=0.9,
                recall_triggers=["pre_push_testing", "quality_validation"]
            ),
            "browser_testing": AgentMemoryPattern(
                agent_type="qa",
                operation_type="browser_testing",
                content_template="Browser testing for {project_name}. Scenarios: {scenarios_tested}. Results: {test_results}. Screenshots captured: {screenshots_count}. Performance metrics: {performance_summary}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["qa", "browser_testing", "ui_testing"],
                metadata_keys=["scenarios_tested", "test_results", "screenshots_count", "performance_metrics"],
                importance_score=0.8,
                recall_triggers=["ui_testing", "browser_validation"]
            ),
            "quality_validation": AgentMemoryPattern(
                agent_type="qa",
                operation_type="quality_validation",
                content_template="Quality validation for {project_name}. Validation type: {validation_type}. Status: {validation_status}. Quality score: {quality_score}. Issues: {quality_issues}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["qa", "quality", "validation"],
                metadata_keys=["validation_type", "validation_status", "quality_score", "quality_issues"],
                importance_score=0.7,
                recall_triggers=["quality_gates", "pre_deployment_validation"]
            )
        }
        
        # Ops Agent Patterns
        self.patterns["ops"] = {
            "git_operations": AgentMemoryPattern(
                agent_type="ops",
                operation_type="git_operations",
                content_template="Git operations for {project_name}. Operation: {git_operation}. Branch: {branch_name}. Status: {operation_status}. Files affected: {files_affected}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ops", "git", "version_control"],
                metadata_keys=["git_operation", "branch_name", "operation_status", "files_affected", "commit_hash"],
                importance_score=0.8,
                recall_triggers=["git_operations", "branch_management"]
            ),
            "deployment_operations": AgentMemoryPattern(
                agent_type="ops",
                operation_type="deployment_operations",
                content_template="Deployment operation for {project_name}. Type: {deployment_type}. Environment: {environment}. Status: {deployment_status}. Duration: {deployment_duration}s",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ops", "deployment", "infrastructure"],
                metadata_keys=["deployment_type", "environment", "deployment_status", "deployment_duration", "services_affected"],
                importance_score=0.9,
                recall_triggers=["deployment_operations", "infrastructure_changes"]
            ),
            "branch_management": AgentMemoryPattern(
                agent_type="ops",
                operation_type="branch_management",
                content_template="Branch management for {project_name}. Operation: {branch_operation}. Source: {source_branch}. Target: {target_branch}. Conflicts: {conflicts_detected}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ops", "git", "branch_management"],
                metadata_keys=["branch_operation", "source_branch", "target_branch", "conflicts_detected", "merge_strategy"],
                importance_score=0.7,
                recall_triggers=["branch_operations", "merge_operations"]
            )
        }
        
        # Ticketing Agent Patterns
        self.patterns["ticketing"] = {
            "ticket_creation": AgentMemoryPattern(
                agent_type="ticketing",
                operation_type="ticket_creation",
                content_template="Ticket created for {project_name}. Type: {ticket_type}. ID: {ticket_id}. Title: {ticket_title}. Priority: {priority}. Status: {ticket_status}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ticketing", "creation", "project_management"],
                metadata_keys=["ticket_type", "ticket_id", "ticket_title", "priority", "ticket_status", "assignee"],
                importance_score=0.6,
                recall_triggers=["ticket_management", "project_tracking"]
            ),
            "ticket_resolution": AgentMemoryPattern(
                agent_type="ticketing",
                operation_type="ticket_resolution",
                content_template="Ticket resolved for {project_name}. ID: {ticket_id}. Resolution: {resolution_type}. Duration: {resolution_duration}h. Actions taken: {actions_taken}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ticketing", "resolution", "completion"],
                metadata_keys=["ticket_id", "resolution_type", "resolution_duration", "actions_taken", "resolution_notes"],
                importance_score=0.8,
                recall_triggers=["ticket_resolution", "completion_patterns"]
            ),
            "status_updates": AgentMemoryPattern(
                agent_type="ticketing",
                operation_type="status_updates",
                content_template="Ticket status update for {project_name}. Tickets updated: {tickets_updated}. Status changes: {status_changes}. Sprint progress: {sprint_progress}%",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["ticketing", "status", "progress"],
                metadata_keys=["tickets_updated", "status_changes", "sprint_progress", "blockers"],
                importance_score=0.5,
                recall_triggers=["status_reporting", "sprint_planning"]
            )
        }
        
        # Agent Coordination Patterns
        self.patterns["coordination"] = {
            "agent_handoff": AgentMemoryPattern(
                agent_type="coordination",
                operation_type="agent_handoff",
                content_template="Agent handoff in {project_name}. From: {source_agent} to {target_agent}. Context: {handoff_context}. Status: {handoff_status}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["coordination", "handoff", "multi_agent"],
                metadata_keys=["source_agent", "target_agent", "handoff_context", "handoff_status", "context_data"],
                importance_score=0.7,
                recall_triggers=["agent_coordination", "multi_agent_workflows"]
            ),
            "workflow_completion": AgentMemoryPattern(
                agent_type="coordination",
                operation_type="workflow_completion",
                content_template="Workflow completed for {project_name}. Type: {workflow_type}. Agents involved: {agents_involved}. Duration: {workflow_duration}m. Success: {workflow_success}",
                memory_category=MemoryCategory.WORKFLOW,
                tags=["coordination", "workflow", "completion"],
                metadata_keys=["workflow_type", "agents_involved", "workflow_duration", "workflow_success", "quality_gates"],
                importance_score=0.9,
                recall_triggers=["workflow_patterns", "completion_analysis"]
            )
        }
        
        self.logger.info(f"Initialized {len(self.patterns)} agent memory pattern categories")
    
    def get_pattern(self, agent_type: str, operation_type: str) -> Optional[AgentMemoryPattern]:
        """Get memory pattern for agent type and operation."""
        agent_patterns = self.patterns.get(agent_type, {})
        return agent_patterns.get(operation_type)
    
    def get_patterns_by_agent(self, agent_type: str) -> Dict[str, AgentMemoryPattern]:
        """Get all patterns for a specific agent type."""
        return self.patterns.get(agent_type, {})
    
    def register_pattern(self, agent_type: str, operation_type: str, pattern: AgentMemoryPattern):
        """Register a new memory pattern."""
        if agent_type not in self.patterns:
            self.patterns[agent_type] = {}
        self.patterns[agent_type][operation_type] = pattern
        self.logger.info(f"Registered memory pattern: {agent_type}.{operation_type}")
    
    def get_recall_patterns(self, trigger: str) -> List[AgentMemoryPattern]:
        """Get patterns that should be recalled for a specific trigger."""
        recall_patterns = []
        for agent_type, patterns in self.patterns.items():
            for operation_type, pattern in patterns.items():
                if trigger in pattern.recall_triggers:
                    recall_patterns.append(pattern)
        return recall_patterns


class MemoryEnhancedAgent:
    """
    Base wrapper for memory-enhanced agent operations.
    
    Wraps existing agents to provide automatic memory triggers
    for operations and memory recall for context enhancement.
    """
    
    def __init__(self, wrapped_agent: BaseAgent, memory_service: MemoryTriggerService):
        self.wrapped_agent = wrapped_agent
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__)
        self.pattern_registry = AgentMemoryPatternRegistry()
        
        # Memory configuration
        self.memory_enabled = True
        self.auto_recall_enabled = True
        self.memory_context_size = 10  # Max memories to recall for context
        
        # Agent memory metrics
        self.memory_operations_count = 0
        self.memory_recall_count = 0
        self.memory_creation_count = 0
        
        self.logger.info(f"Enhanced agent with memory capabilities: {wrapped_agent.agent_id}")
    
    async def execute_with_memory(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute agent operation with automatic memory integration.
        
        Args:
            operation: Operation to execute
            context: Operation context
            **kwargs: Additional operation parameters
            
        Returns:
            Operation result with memory context
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # Step 1: Recall relevant memories before operation
            memory_context = await self._recall_memories_for_operation(operation, context)
            
            # Step 2: Enhance context with memory insights
            enhanced_context = await self._enhance_context_with_memory(context, memory_context)
            
            # Step 3: Execute the wrapped agent operation
            result = await self.wrapped_agent.execute(
                operation=operation,
                context=enhanced_context,
                **kwargs
            )
            
            # Step 4: Create memory for successful operation
            if self._should_create_memory(operation, result):
                await self._create_operation_memory(operation, enhanced_context, result)
            
            # Step 5: Update memory context and return enhanced result
            execution_time = time.time() - start_time
            enhanced_result = await self._enhance_result_with_memory(
                result, memory_context, execution_time
            )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Memory-enhanced operation failed: {operation} - {e}")
            
            # Create memory for failed operation (for learning)
            if self.memory_enabled:
                await self._create_error_memory(operation, context, str(e))
            
            raise
    
    async def _recall_memories_for_operation(
        self,
        operation: str,
        context: Dict[str, Any]
    ) -> AgentMemoryContext:
        """Recall relevant memories for the operation."""
        if not self.auto_recall_enabled:
            return AgentMemoryContext(
                agent_id=self.wrapped_agent.agent_id,
                agent_type=self.wrapped_agent.agent_type,
                operation=operation,
                project_name=context.get("project_name", "unknown")
            )
        
        try:
            # Get memory service
            memory_service = self.memory_service.get_memory_service()
            if not memory_service:
                self.logger.warning("Memory service not available for recall")
                return AgentMemoryContext(
                    agent_id=self.wrapped_agent.agent_id,
                    agent_type=self.wrapped_agent.agent_type,
                    operation=operation,
                    project_name=context.get("project_name", "unknown")
                )
            
            # Build search query for relevant memories
            search_query = self._build_memory_search_query(operation, context)
            
            # Search for relevant memories
            memories = await memory_service.search_memories(
                query=search_query,
                filters={
                    "agent_type": self.wrapped_agent.agent_type,
                    "project_name": context.get("project_name")
                },
                limit=self.memory_context_size
            )
            
            # Analyze patterns and generate recommendations
            patterns = self._analyze_memory_patterns(memories)
            recommendations = self._generate_memory_recommendations(memories, operation)
            
            self.memory_recall_count += 1
            
            return AgentMemoryContext(
                agent_id=self.wrapped_agent.agent_id,
                agent_type=self.wrapped_agent.agent_type,
                operation=operation,
                project_name=context.get("project_name", "unknown"),
                context=context,
                related_memories=memories,
                recommendations=recommendations,
                patterns_detected=patterns
            )
            
        except Exception as e:
            self.logger.error(f"Memory recall failed for operation {operation}: {e}")
            return AgentMemoryContext(
                agent_id=self.wrapped_agent.agent_id,
                agent_type=self.wrapped_agent.agent_type,
                operation=operation,
                project_name=context.get("project_name", "unknown")
            )
    
    def _build_memory_search_query(self, operation: str, context: Dict[str, Any]) -> str:
        """Build search query for memory recall."""
        query_parts = [
            f"agent:{self.wrapped_agent.agent_type}",
            f"operation:{operation}",
            f"project:{context.get('project_name', 'unknown')}"
        ]
        
        # Add context-specific terms
        if context.get("test_type"):
            query_parts.append(f"test_type:{context['test_type']}")
        if context.get("deployment_type"):
            query_parts.append(f"deployment:{context['deployment_type']}")
        if context.get("branch_name"):
            query_parts.append(f"branch:{context['branch_name']}")
        
        return " ".join(query_parts)
    
    def _analyze_memory_patterns(self, memories: List[MemoryItem]) -> List[str]:
        """Analyze patterns from recalled memories."""
        if not memories:
            return []
        
        patterns = []
        
        # Analyze success/failure patterns
        success_count = sum(1 for m in memories if m.metadata.get("success", True))
        if success_count < len(memories) * 0.7:  # Less than 70% success rate
            patterns.append("frequent_failures")
        
        # Analyze timing patterns
        execution_times = [m.metadata.get("execution_time", 0) for m in memories]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            if avg_time > 300:  # More than 5 minutes
                patterns.append("slow_execution")
        
        # Analyze error patterns
        error_types = [m.metadata.get("error_type") for m in memories if m.metadata.get("error_type")]
        if error_types:
            from collections import Counter
            common_errors = Counter(error_types).most_common(2)
            patterns.extend([f"common_error_{error}" for error, count in common_errors])
        
        return patterns
    
    def _generate_memory_recommendations(
        self,
        memories: List[MemoryItem],
        operation: str
    ) -> List[str]:
        """Generate recommendations based on memory analysis."""
        if not memories:
            return ["No historical data available for this operation"]
        
        recommendations = []
        
        # Success rate recommendations
        success_rate = sum(1 for m in memories if m.metadata.get("success", True)) / len(memories)
        if success_rate < 0.7:
            recommendations.append(f"Operation has {success_rate:.1%} success rate - consider reviewing approach")
        
        # Performance recommendations
        execution_times = [m.metadata.get("execution_time", 0) for m in memories]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            if avg_time > 300:
                recommendations.append(f"Average execution time is {avg_time:.1f}s - consider optimization")
        
        # Pattern-based recommendations
        error_patterns = [m.metadata.get("error_type") for m in memories if m.metadata.get("error_type")]
        if error_patterns:
            recommendations.append("Review common error patterns before proceeding")
        
        # Operation-specific recommendations
        if operation == "test_execution":
            failed_tests = [m for m in memories if m.metadata.get("failed_tests", 0) > 0]
            if failed_tests:
                recommendations.append("Previous test failures detected - ensure fixes are applied")
        
        return recommendations
    
    async def _enhance_context_with_memory(
        self,
        context: Dict[str, Any],
        memory_context: AgentMemoryContext
    ) -> Dict[str, Any]:
        """Enhance operation context with memory insights."""
        enhanced_context = context.copy()
        
        # Add memory insights
        enhanced_context["memory_insights"] = {
            "related_memories_count": len(memory_context.related_memories),
            "recommendations": memory_context.recommendations,
            "patterns_detected": memory_context.patterns_detected,
            "historical_success_rate": self._calculate_success_rate(memory_context.related_memories)
        }
        
        # Add specific enhancements based on patterns
        if "frequent_failures" in memory_context.patterns_detected:
            enhanced_context["risk_level"] = "high"
            enhanced_context["require_validation"] = True
        
        if "slow_execution" in memory_context.patterns_detected:
            enhanced_context["timeout_extension"] = True
            enhanced_context["performance_monitoring"] = True
        
        return enhanced_context
    
    def _calculate_success_rate(self, memories: List[MemoryItem]) -> float:
        """Calculate success rate from memory items."""
        if not memories:
            return 0.0
        
        success_count = sum(1 for m in memories if m.metadata.get("success", True))
        return success_count / len(memories)
    
    async def _create_operation_memory(
        self,
        operation: str,
        context: Dict[str, Any],
        result: Any
    ) -> Optional[str]:
        """Create memory for successful operation."""
        if not self.memory_enabled:
            return None
        
        try:
            # Get memory pattern for operation
            pattern = self.pattern_registry.get_pattern(
                self.wrapped_agent.agent_type,
                operation
            )
            
            if not pattern:
                # Create default pattern
                pattern = AgentMemoryPattern(
                    agent_type=self.wrapped_agent.agent_type,
                    operation_type=operation,
                    content_template=f"Operation {operation} completed for {{project_name}}",
                    memory_category=MemoryCategory.WORKFLOW,
                    tags=[self.wrapped_agent.agent_type, operation]
                )
            
            # Prepare memory content
            memory_content = pattern.create_memory_content(context)
            
            # Prepare metadata
            memory_metadata = {
                "agent_id": self.wrapped_agent.agent_id,
                "agent_type": self.wrapped_agent.agent_type,
                "operation": operation,
                "project_name": context.get("project_name", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "execution_time": context.get("execution_time", 0),
                "result_summary": str(result)[:500]  # Truncate for storage
            }
            
            # Add pattern-specific metadata
            for key in pattern.metadata_keys:
                if key in context:
                    memory_metadata[key] = context[key]
            
            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.OPERATION_COMPLETION,
                priority=TriggerPriority.MEDIUM,
                project_name=context.get("project_name", "unknown"),
                event_id=f"{self.wrapped_agent.agent_id}_{operation}_{int(time.time())}",
                content=memory_content,
                category=pattern.memory_category,
                tags=pattern.tags,
                metadata=memory_metadata,
                source=f"agent_{self.wrapped_agent.agent_type}",
                context=context
            )
            
            # Trigger memory creation
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.memory_creation_count += 1
                self.logger.info(f"Created memory for operation: {operation}")
                return trigger_event.event_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to create operation memory: {e}")
            return None
    
    async def _create_error_memory(
        self,
        operation: str,
        context: Dict[str, Any],
        error: str
    ) -> Optional[str]:
        """Create memory for failed operation."""
        try:
            # Create error memory content
            memory_content = f"Operation {operation} failed for {context.get('project_name', 'unknown')}: {error}"
            
            # Prepare error metadata
            memory_metadata = {
                "agent_id": self.wrapped_agent.agent_id,
                "agent_type": self.wrapped_agent.agent_type,
                "operation": operation,
                "project_name": context.get("project_name", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": error,
                "error_type": self._classify_error(error)
            }
            
            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.ERROR,
                priority=TriggerPriority.HIGH,
                project_name=context.get("project_name", "unknown"),
                event_id=f"{self.wrapped_agent.agent_id}_error_{int(time.time())}",
                content=memory_content,
                category=MemoryCategory.ERROR,
                tags=[self.wrapped_agent.agent_type, operation, "error"],
                metadata=memory_metadata,
                source=f"agent_{self.wrapped_agent.agent_type}",
                context=context
            )
            
            # Trigger memory creation
            orchestrator = self.memory_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                self.logger.info(f"Created error memory for operation: {operation}")
                return trigger_event.event_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to create error memory: {e}")
            return None
    
    def _classify_error(self, error: str) -> str:
        """Classify error type for pattern analysis."""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        elif "permission" in error_lower or "access" in error_lower:
            return "permission"
        elif "file not found" in error_lower or "path" in error_lower:
            return "file_system"
        elif "memory" in error_lower or "out of" in error_lower:
            return "resource"
        else:
            return "unknown"
    
    def _should_create_memory(self, operation: str, result: Any) -> bool:
        """Determine if memory should be created for this operation."""
        if not self.memory_enabled:
            return False
        
        # Always create memory for important operations
        important_operations = [
            "test_execution", "deployment_operations", "documentation_validation",
            "git_operations", "ticket_resolution", "workflow_completion"
        ]
        
        if operation in important_operations:
            return True
        
        # Create memory for operations that took significant time
        if hasattr(result, 'execution_time') and result.execution_time > 30:
            return True
        
        # Create memory for operations with significant results
        if isinstance(result, dict) and result.get("success") is not None:
            return True
        
        return False
    
    async def _enhance_result_with_memory(
        self,
        result: Any,
        memory_context: AgentMemoryContext,
        execution_time: float
    ) -> Any:
        """Enhance operation result with memory context."""
        if isinstance(result, dict):
            # Add memory context to result
            result["memory_context"] = {
                "related_memories_count": len(memory_context.related_memories),
                "recommendations_provided": len(memory_context.recommendations),
                "patterns_detected": memory_context.patterns_detected,
                "memory_enhanced": True,
                "execution_time": execution_time
            }
            
            # Add specific memory insights
            if memory_context.recommendations:
                result["memory_recommendations"] = memory_context.recommendations
            
            if memory_context.patterns_detected:
                result["memory_patterns"] = memory_context.patterns_detected
        
        return result
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory integration metrics."""
        return {
            "memory_enabled": self.memory_enabled,
            "auto_recall_enabled": self.auto_recall_enabled,
            "memory_operations_count": self.memory_operations_count,
            "memory_recall_count": self.memory_recall_count,
            "memory_creation_count": self.memory_creation_count,
            "memory_context_size": self.memory_context_size,
            "agent_id": self.wrapped_agent.agent_id,
            "agent_type": self.wrapped_agent.agent_type
        }
    
    def configure_memory(self, config: Dict[str, Any]):
        """Configure memory behavior for the agent."""
        self.memory_enabled = config.get("memory_enabled", True)
        self.auto_recall_enabled = config.get("auto_recall_enabled", True)
        self.memory_context_size = config.get("memory_context_size", 10)
        
        self.logger.info(f"Memory configuration updated for agent: {self.wrapped_agent.agent_id}")
    
    # Delegate all other methods to wrapped agent
    def __getattr__(self, name):
        """Delegate attribute access to wrapped agent."""
        return getattr(self.wrapped_agent, name)