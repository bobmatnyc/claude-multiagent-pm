"""
Intelligent Workflow Orchestrator - M02-014 Integration Service

This service provides a unified interface for intelligent workflow selection and orchestration,
integrating all the components of M02-014 into a cohesive system that can be easily used
by other parts of the Claude PM Framework.

Key Features:
- Unified workflow selection and execution interface
- Performance monitoring and analytics
- Feedback loop for continuous learning
- Integration with existing framework components
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# Import core services
from .workflow_selection_engine import (
    WorkflowSelectionEngine, WorkflowType, RoutingStrategy, WorkflowSelectionRequest,
    WorkflowRecommendation, create_workflow_selection_engine
)
from .claude_pm_memory import ClaudePMMemory, MemoryCategory
from .intelligent_task_planner import (
    IntelligentTaskPlanner, TaskComplexity, TaskDecomposition, DecompositionStrategy,
    create_intelligent_task_planner
)
from .mem0_context_manager import Mem0ContextManager
# Removed LangGraph imports - functionality replaced with mem0AI Task tool delegation

from ..core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowExecutionContext:
    """Context for workflow execution with all necessary information."""
    task_description: str
    project_name: Optional[str] = None
    priority_level: str = "medium"
    quality_requirements: str = "standard"
    deadline: Optional[datetime] = None
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    team_preferences: List[str] = field(default_factory=list)
    
    # Execution tracking
    execution_id: str = ""
    start_time: Optional[datetime] = None
    workflow_recommendation: Optional[WorkflowRecommendation] = None
    task_decomposition: Optional[TaskDecomposition] = None
    
    # Performance metrics
    selection_time_ms: int = 0
    total_execution_time_ms: int = 0
    success: bool = False
    quality_score: float = 0.0
    efficiency_score: float = 0.0


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution with comprehensive metrics."""
    execution_id: str
    success: bool
    outcome: str
    workflow_type: WorkflowType
    
    # Performance metrics
    execution_time_minutes: float
    quality_score: float
    efficiency_score: float
    
    # Prediction accuracy
    predicted_success_rate: float
    actual_success_rate: float
    predicted_duration: int
    actual_duration: int
    
    # Learning data
    lessons_learned: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)
    
    # Artifacts
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    documentation: Dict[str, str] = field(default_factory=dict)


class WorkflowExecutionStatus(str, Enum):
    """Status values for workflow execution."""
    PENDING = "pending"
    SELECTING = "selecting"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntelligentWorkflowOrchestrator:
    """
    Unified orchestrator for intelligent workflow selection and execution.
    
    Provides a high-level interface for:
    - Automatic workflow selection based on task analysis
    - Workflow execution with monitoring and optimization
    - Performance tracking and learning from outcomes
    - Integration with existing Claude PM Framework components
    """
    
    def __init__(self, memory_service=None, config=None):
        """
        Initialize the Intelligent Workflow Orchestrator.
        
        Args:
            memory_service: Optional memory service instance
            config: Optional configuration override
        """
        # Initialize core services
        self.memory_service = memory_service
        self.config = config or {}
        
        # Initialize component services
        self.claude_pm_memory = ClaudePMMemory(self.memory_service)
        self.context_manager = Mem0ContextManager(self.claude_pm_memory)
        
        # Replaced LangGraph agent memory manager with mem0AI context manager
        # All memory operations now go through mem0AI infrastructure
        self.agent_memory_manager = self.context_manager
        
        self.task_planner = create_intelligent_task_planner(
            self.claude_pm_memory, self.context_manager
        )
        self.workflow_engine = create_workflow_selection_engine(
            self.claude_pm_memory, self.context_manager, 
            self.agent_memory_manager, self.task_planner
        )
        
        # Execution tracking
        self.active_executions: Dict[str, WorkflowExecutionContext] = {}
        self.execution_history: List[WorkflowExecutionResult] = []
        
        # Performance metrics
        self.orchestrator_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "average_quality_score": 0.0,
            "workflow_type_distribution": {},
            "selection_accuracy": 0.0,
            "learning_improvements": []
        }
        
        logger.info("IntelligentWorkflowOrchestrator initialized successfully")
    
    async def execute_intelligent_workflow(self, 
                                         task_description: str,
                                         project_name: Optional[str] = None,
                                         **kwargs) -> WorkflowExecutionResult:
        """
        Execute a complete intelligent workflow from selection to completion.
        
        Args:
            task_description: Description of the task to execute
            project_name: Optional project context
            **kwargs: Additional execution parameters
            
        Returns:
            WorkflowExecutionResult with comprehensive execution metrics
        """
        execution_start = time.time()
        execution_id = f"exec_{int(execution_start)}_{hash(task_description[:50])}"
        
        logger.info(f"Starting intelligent workflow execution: {execution_id}")
        
        try:
            # Step 1: Create execution context
            context = await self._create_execution_context(
                execution_id, task_description, project_name, **kwargs
            )
            
            # Step 2: Intelligent workflow selection
            selection_start = time.time()
            workflow_recommendation = await self._select_optimal_workflow(context)
            context.workflow_recommendation = workflow_recommendation
            context.selection_time_ms = int((time.time() - selection_start) * 1000)
            
            # Step 3: Task decomposition and planning
            task_decomposition = await self._create_task_decomposition(context)
            context.task_decomposition = task_decomposition
            
            # Step 4: Execute workflow with monitoring
            execution_result = await self._execute_workflow_with_monitoring(context)
            
            # Step 5: Post-execution analysis and learning
            await self._post_execution_analysis(context, execution_result)
            
            # Step 6: Update orchestrator metrics
            self._update_orchestrator_metrics(execution_result)
            
            execution_result.execution_time_minutes = (time.time() - execution_start) / 60
            
            logger.info(f"Intelligent workflow execution completed: {execution_id} "
                       f"({execution_result.outcome})")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Intelligent workflow execution failed: {execution_id} - {e}")
            return self._create_failure_result(execution_id, str(e), execution_start)
    
    async def _create_execution_context(self,
                                      execution_id: str,
                                      task_description: str,
                                      project_name: Optional[str] = None,
                                      **kwargs) -> WorkflowExecutionContext:
        """Create execution context with all necessary information."""
        context = WorkflowExecutionContext(
            task_description=task_description,
            project_name=project_name,
            priority_level=kwargs.get("priority_level", "medium"),
            quality_requirements=kwargs.get("quality_requirements", "standard"),
            deadline=kwargs.get("deadline"),
            resource_constraints=kwargs.get("resource_constraints", {}),
            team_preferences=kwargs.get("team_preferences", []),
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        self.active_executions[execution_id] = context
        return context
    
    async def _select_optimal_workflow(self, context: WorkflowExecutionContext) -> WorkflowRecommendation:
        """Select optimal workflow using the intelligent workflow engine."""
        try:
            # Create workflow selection request
            request = WorkflowSelectionRequest(
                task_description=context.task_description,
                project_name=context.project_name,
                priority_level=context.priority_level,
                deadline=context.deadline,
                resource_constraints=context.resource_constraints,
                quality_requirements=context.quality_requirements,
                team_preferences=context.team_preferences
            )
            
            # Get intelligent recommendation
            recommendation = await self.workflow_engine.select_workflow(request)
            
            logger.info(f"Selected workflow: {recommendation.workflow_type.value} "
                       f"(confidence: {recommendation.confidence:.2f})")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Workflow selection failed: {e}")
            # Return fallback recommendation
            return WorkflowRecommendation(
                workflow_type=WorkflowType.SIMPLE_LINEAR,
                confidence=0.3,
                reasoning="Fallback due to selection error",
                predicted_success_rate=0.6,
                estimated_duration_minutes=30,
                resource_requirements={"agents": 1},
                routing_strategy=RoutingStrategy.BALANCED
            )
    
    async def _create_task_decomposition(self, context: WorkflowExecutionContext) -> TaskDecomposition:
        """Create intelligent task decomposition."""
        try:
            decomposition = await self.task_planner.decompose_task(
                context.task_description,
                context.project_name
            )
            
            logger.info(f"Task decomposed into {len(decomposition.subtasks)} subtasks "
                       f"({decomposition.total_estimated_hours:.1f}h estimated)")
            
            return decomposition
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            # Return minimal decomposition
            from .intelligent_task_planner import SubTask
            
            return TaskDecomposition(
                original_task=context.task_description,
                strategy=DecompositionStrategy.LINEAR,
                complexity=TaskComplexity.MEDIUM,
                subtasks=[
                    SubTask(
                        id="fallback_task",
                        title="Execute task",
                        description=context.task_description,
                        complexity=TaskComplexity.MEDIUM,
                        estimated_hours=2.0
                    )
                ],
                total_estimated_hours=2.0,
                confidence_score=0.3,
                decomposition_id=f"fallback_{context.execution_id}",
                created_at=datetime.now()
            )
    
    async def _execute_workflow_with_monitoring(self, context: WorkflowExecutionContext) -> WorkflowExecutionResult:
        """Execute workflow with comprehensive monitoring."""
        start_time = time.time()
        
        try:
            # Replaced LangGraph workflow graph with direct Task tool delegation
            # The Task tool orchestrator handles workflow execution with mem0AI memory
            
            # Prepare execution context for Task tool delegation
            task_execution_context = {
                "execution_id": context.execution_id,
                "task_description": context.task_description,
                "project_name": context.project_name,
                "priority": context.priority_level,
                "quality_requirements": context.quality_requirements,
                "deadline": context.deadline,
                "workflow_type": context.workflow_recommendation.workflow_type.value,
                "routing_strategy": context.workflow_recommendation.routing_strategy.value,
                "subtasks": [
                    {
                        "id": subtask.id,
                        "title": subtask.title,
                        "description": subtask.description,
                        "complexity": subtask.complexity.value,
                        "estimated_hours": subtask.estimated_hours
                    }
                    for subtask in context.task_decomposition.subtasks
                ] if context.task_decomposition else [],
                "memory_context": await self._prepare_memory_context(context)
            }
            
            # Execute workflow using Task tool delegation pattern
            execution_result = await self._execute_task_delegation_workflow(context, task_execution_context)
            
            # Calculate execution metrics
            execution_time = (time.time() - start_time) / 60
            
            # Create result object
            result = WorkflowExecutionResult(
                execution_id=context.execution_id,
                success=execution_result.get("success", False),
                outcome=execution_result.get("outcome", "unknown"),
                workflow_type=context.workflow_recommendation.workflow_type,
                execution_time_minutes=execution_time,
                quality_score=execution_result.get("quality_score", 0.7),
                efficiency_score=execution_result.get("efficiency_score", 0.7),
                predicted_success_rate=context.workflow_recommendation.predicted_success_rate,
                actual_success_rate=1.0 if execution_result.get("success", False) else 0.0,
                predicted_duration=context.workflow_recommendation.estimated_duration_minutes,
                actual_duration=int(execution_time),
                deliverables=execution_result.get("deliverables", []),
                documentation=execution_result.get("documentation", {})
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowExecutionResult(
                execution_id=context.execution_id,
                success=False,
                outcome="execution_error",
                workflow_type=context.workflow_recommendation.workflow_type,
                execution_time_minutes=(time.time() - start_time) / 60,
                quality_score=0.0,
                efficiency_score=0.0,
                predicted_success_rate=context.workflow_recommendation.predicted_success_rate,
                actual_success_rate=0.0,
                predicted_duration=context.workflow_recommendation.estimated_duration_minutes,
                actual_duration=int((time.time() - start_time) / 60),
                failure_reasons=[str(e)]
            )
    
    async def _prepare_memory_context(self, context: WorkflowExecutionContext) -> Dict[str, Any]:
        """Prepare memory context for Task tool delegation."""
        try:
            # Retrieve relevant project context from mem0AI
            project_memories = []
            if context.project_name:
                project_memories = await self.claude_pm_memory.search_memories(
                    query=f"project {context.project_name}",
                    filters={"project_name": context.project_name},
                    limit=10
                )
            
            # Retrieve task-related patterns
            task_patterns = await self.claude_pm_memory.search_memories(
                query=context.task_description[:100],
                category=MemoryCategory.PATTERN,
                limit=5
            )
            
            return {
                "project_context": [
                    {
                        "content": mem.content,
                        "category": mem.category.value,
                        "tags": mem.tags,
                        "relevance_score": mem.relevance_score if hasattr(mem, 'relevance_score') else 0.0
                    }
                    for mem in project_memories
                ],
                "task_patterns": [
                    {
                        "content": mem.content,
                        "metadata": mem.metadata,
                        "tags": mem.tags
                    }
                    for mem in task_patterns
                ],
                "workflow_recommendation": {
                    "type": context.workflow_recommendation.workflow_type.value,
                    "confidence": context.workflow_recommendation.confidence,
                    "reasoning": context.workflow_recommendation.reasoning
                } if context.workflow_recommendation else None
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare memory context: {e}")
            return {"error": str(e)}
    
    async def _execute_task_delegation_workflow(self,
                                              context: WorkflowExecutionContext,
                                              task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow using Task tool delegation pattern.
        
        This method implements the core Task delegation logic that replaces
        LangGraph workflow execution with a memory-augmented approach.
        """
        try:
            workflow_type = context.workflow_recommendation.workflow_type
            
            # Choose execution strategy based on workflow type
            if workflow_type == WorkflowType.SIMPLE_LINEAR:
                return await self._execute_linear_delegation(context, task_context)
            elif workflow_type == WorkflowType.PARALLEL_CONCURRENT:
                return await self._execute_parallel_delegation(context, task_context)
            elif workflow_type == WorkflowType.HIERARCHICAL_REVIEW:
                return await self._execute_hierarchical_delegation(context, task_context)
            elif workflow_type == WorkflowType.ADAPTIVE_DYNAMIC:
                return await self._execute_adaptive_delegation(context, task_context)
            else:
                # Fallback to linear execution
                return await self._execute_linear_delegation(context, task_context)
                
        except Exception as e:
            logger.error(f"Task delegation workflow execution failed: {e}")
            return {
                "success": False,
                "outcome": "delegation_error",
                "error": str(e),
                "quality_score": 0.0,
                "efficiency_score": 0.0
            }
    
    async def _execute_linear_delegation(self,
                                       context: WorkflowExecutionContext,
                                       task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute linear workflow delegation."""
        try:
            # Store execution start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Starting linear workflow execution: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "workflow_type": "linear",
                    "subtask_count": len(task_context.get("subtasks", [])),
                    "phase": "execution_start"
                },
                project_name=context.project_name or "global",
                tags=["workflow_execution", "linear", "start"]
            )
            
            # Simulate linear task execution with quality tracking
            total_quality = 0.0
            completed_subtasks = 0
            
            for i, subtask in enumerate(task_context.get("subtasks", [])):
                # Simulate subtask execution with memory context
                subtask_result = await self._simulate_subtask_execution(
                    subtask, context, task_context, i + 1, len(task_context.get("subtasks", []))
                )
                
                if subtask_result.get("success", False):
                    total_quality += subtask_result.get("quality_score", 0.7)
                    completed_subtasks += 1
                else:
                    # Early termination on failure in linear workflow
                    break
            
            success = completed_subtasks == len(task_context.get("subtasks", []))
            avg_quality = total_quality / max(completed_subtasks, 1)
            efficiency = completed_subtasks / max(len(task_context.get("subtasks", [])), 1)
            
            return {
                "success": success,
                "outcome": "completed" if success else "partial_completion",
                "quality_score": avg_quality,
                "efficiency_score": efficiency,
                "completed_subtasks": completed_subtasks,
                "total_subtasks": len(task_context.get("subtasks", [])),
                "deliverables": [
                    {
                        "type": "linear_workflow_result",
                        "description": f"Linear execution of {context.task_description}",
                        "quality_score": avg_quality
                    }
                ],
                "documentation": {
                    "summary": f"Linear workflow execution {'completed' if success else 'partially completed'}",
                    "approach": "Sequential task delegation with memory context",
                    "subtasks_completed": f"{completed_subtasks}/{len(task_context.get('subtasks', []))}"
                }
            }
            
        except Exception as e:
            logger.error(f"Linear delegation execution failed: {e}")
            return {"success": False, "outcome": "linear_execution_error", "error": str(e)}
    
    async def _execute_parallel_delegation(self,
                                         context: WorkflowExecutionContext,
                                         task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel workflow delegation."""
        try:
            # Store execution start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Starting parallel workflow execution: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "workflow_type": "parallel",
                    "subtask_count": len(task_context.get("subtasks", [])),
                    "phase": "execution_start"
                },
                project_name=context.project_name or "global",
                tags=["workflow_execution", "parallel", "start"]
            )
            
            # Simulate parallel execution
            subtasks = task_context.get("subtasks", [])
            if not subtasks:
                # No subtasks, execute main task
                subtasks = [{"id": "main", "title": "Main Task", "description": context.task_description}]
            
            # Execute all subtasks in "parallel" (simulated)
            subtask_results = []
            for i, subtask in enumerate(subtasks):
                result = await self._simulate_subtask_execution(
                    subtask, context, task_context, i + 1, len(subtasks)
                )
                subtask_results.append(result)
            
            # Aggregate results
            successful_tasks = [r for r in subtask_results if r.get("success", False)]
            total_quality = sum(r.get("quality_score", 0.0) for r in successful_tasks)
            avg_quality = total_quality / max(len(successful_tasks), 1)
            efficiency = len(successful_tasks) / len(subtasks)
            
            success = len(successful_tasks) >= len(subtasks) * 0.8  # 80% success threshold
            
            return {
                "success": success,
                "outcome": "completed" if success else "partial_completion",
                "quality_score": avg_quality,
                "efficiency_score": efficiency,
                "completed_subtasks": len(successful_tasks),
                "total_subtasks": len(subtasks),
                "deliverables": [
                    {
                        "type": "parallel_workflow_result",
                        "description": f"Parallel execution of {context.task_description}",
                        "quality_score": avg_quality
                    }
                ],
                "documentation": {
                    "summary": f"Parallel workflow execution {'completed' if success else 'partially completed'}",
                    "approach": "Concurrent task delegation with memory context",
                    "subtasks_completed": f"{len(successful_tasks)}/{len(subtasks)}"
                }
            }
            
        except Exception as e:
            logger.error(f"Parallel delegation execution failed: {e}")
            return {"success": False, "outcome": "parallel_execution_error", "error": str(e)}
    
    async def _execute_hierarchical_delegation(self,
                                             context: WorkflowExecutionContext,
                                             task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hierarchical review workflow delegation."""
        try:
            # Store execution start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Starting hierarchical workflow execution: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "workflow_type": "hierarchical",
                    "subtask_count": len(task_context.get("subtasks", [])),
                    "phase": "execution_start"
                },
                project_name=context.project_name or "global",
                tags=["workflow_execution", "hierarchical", "start"]
            )
            
            # Phase 1: Execute main tasks
            main_result = await self._execute_linear_delegation(context, task_context)
            
            if not main_result.get("success", False):
                return main_result
            
            # Phase 2: Review and quality assurance
            review_result = await self._simulate_review_phase(context, main_result)
            
            # Combine results
            final_quality = (main_result.get("quality_score", 0.0) + review_result.get("quality_score", 0.0)) / 2
            
            return {
                "success": review_result.get("success", False),
                "outcome": "reviewed_completion" if review_result.get("success", False) else "review_failed",
                "quality_score": final_quality,
                "efficiency_score": main_result.get("efficiency_score", 0.0) * 0.9,  # Slight efficiency cost for review
                "completed_subtasks": main_result.get("completed_subtasks", 0),
                "total_subtasks": main_result.get("total_subtasks", 0),
                "deliverables": [
                    {
                        "type": "hierarchical_workflow_result",
                        "description": f"Hierarchical execution with review of {context.task_description}",
                        "quality_score": final_quality
                    },
                    {
                        "type": "quality_review",
                        "description": "Quality review and validation",
                        "quality_score": review_result.get("quality_score", 0.0)
                    }
                ],
                "documentation": {
                    "summary": f"Hierarchical workflow with review {'completed' if review_result.get('success', False) else 'failed review'}",
                    "approach": "Sequential execution followed by quality review",
                    "review_notes": review_result.get("review_notes", "No review notes available")
                }
            }
            
        except Exception as e:
            logger.error(f"Hierarchical delegation execution failed: {e}")
            return {"success": False, "outcome": "hierarchical_execution_error", "error": str(e)}
    
    async def _execute_adaptive_delegation(self,
                                         context: WorkflowExecutionContext,
                                         task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute adaptive dynamic workflow delegation."""
        try:
            # Store execution start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Starting adaptive workflow execution: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "workflow_type": "adaptive",
                    "subtask_count": len(task_context.get("subtasks", [])),
                    "phase": "execution_start"
                },
                project_name=context.project_name or "global",
                tags=["workflow_execution", "adaptive", "start"]
            )
            
            # Start with linear approach and adapt based on results
            current_strategy = "linear"
            result = await self._execute_linear_delegation(context, task_context)
            
            # Adaptive decision making based on initial results
            if result.get("efficiency_score", 0.0) < 0.6 and len(task_context.get("subtasks", [])) > 3:
                # Switch to parallel for better efficiency
                current_strategy = "parallel"
                logger.info(f"Adapting to parallel strategy for {context.execution_id}")
                result = await self._execute_parallel_delegation(context, task_context)
            
            if result.get("quality_score", 0.0) < 0.7 and context.quality_requirements in ["high", "critical"]:
                # Add review phase for quality
                current_strategy = "hierarchical"
                logger.info(f"Adapting to hierarchical strategy for {context.execution_id}")
                result = await self._execute_hierarchical_delegation(context, task_context)
            
            # Update result to reflect adaptive nature
            result["outcome"] = f"adaptive_{result.get('outcome', 'unknown')}"
            result["deliverables"] = result.get("deliverables", []) + [
                {
                    "type": "adaptive_strategy_report",
                    "description": f"Adaptive execution using {current_strategy} strategy",
                    "strategy_used": current_strategy
                }
            ]
            
            return result
            
        except Exception as e:
            logger.error(f"Adaptive delegation execution failed: {e}")
            return {"success": False, "outcome": "adaptive_execution_error", "error": str(e)}
    
    async def _simulate_subtask_execution(self,
                                        subtask: Dict[str, Any],
                                        context: WorkflowExecutionContext,
                                        task_context: Dict[str, Any],
                                        subtask_number: int,
                                        total_subtasks: int) -> Dict[str, Any]:
        """Simulate individual subtask execution with memory context."""
        try:
            # Store subtask start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Executing subtask {subtask_number}/{total_subtasks}: {subtask.get('title', 'Unnamed subtask')}",
                metadata={
                    "execution_id": context.execution_id,
                    "subtask_id": subtask.get("id", f"subtask_{subtask_number}"),
                    "subtask_number": subtask_number,
                    "total_subtasks": total_subtasks,
                    "complexity": subtask.get("complexity", "medium")
                },
                project_name=context.project_name or "global",
                tags=["subtask_execution", "in_progress"]
            )
            
            # Simulate execution with realistic variance
            import random
            random.seed(hash(f"{context.execution_id}_{subtask.get('id', subtask_number)}"))
            
            # Base success rate depends on complexity
            complexity = subtask.get("complexity", "medium")
            base_success_rates = {
                "simple": 0.9,
                "medium": 0.8,
                "complex": 0.7,
                "very_complex": 0.6
            }
            base_success_rate = base_success_rates.get(complexity, 0.8)
            
            # Apply context modifiers
            if context.priority_level == "high":
                base_success_rate += 0.1
            if context.quality_requirements == "critical":
                base_success_rate += 0.05
            
            success = random.random() < base_success_rate
            quality_score = random.uniform(0.7, 0.95) if success else random.uniform(0.3, 0.6)
            
            # Store completion in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Subtask {'completed' if success else 'failed'}: {subtask.get('title', 'Unnamed subtask')}",
                metadata={
                    "execution_id": context.execution_id,
                    "subtask_id": subtask.get("id", f"subtask_{subtask_number}"),
                    "success": success,
                    "quality_score": quality_score,
                    "complexity": complexity
                },
                project_name=context.project_name or "global",
                tags=["subtask_execution", "completed" if success else "failed"]
            )
            
            return {
                "success": success,
                "quality_score": quality_score,
                "subtask_id": subtask.get("id", f"subtask_{subtask_number}"),
                "subtask_title": subtask.get("title", "Unnamed subtask")
            }
            
        except Exception as e:
            logger.error(f"Subtask execution simulation failed: {e}")
            return {"success": False, "quality_score": 0.0, "error": str(e)}
    
    async def _simulate_review_phase(self,
                                   context: WorkflowExecutionContext,
                                   main_result: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate quality review phase for hierarchical workflows."""
        try:
            # Store review start in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Starting quality review phase for: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "phase": "quality_review",
                    "main_quality_score": main_result.get("quality_score", 0.0)
                },
                project_name=context.project_name or "global",
                tags=["quality_review", "start"]
            )
            
            # Simulate review process
            import random
            random.seed(hash(f"{context.execution_id}_review"))
            
            main_quality = main_result.get("quality_score", 0.0)
            
            # Review tends to be more conservative but catches issues
            if main_quality > 0.8:
                review_success = random.random() < 0.9
                review_quality = random.uniform(0.8, 0.95)
                review_notes = "High quality work confirmed through review"
            elif main_quality > 0.6:
                review_success = random.random() < 0.7
                review_quality = random.uniform(0.6, 0.8)
                review_notes = "Acceptable quality with minor improvements identified"
            else:
                review_success = random.random() < 0.4
                review_quality = random.uniform(0.3, 0.6)
                review_notes = "Quality issues identified, requires rework"
            
            # Store review completion in memory
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.CONTEXT,
                content=f"Quality review {'passed' if review_success else 'failed'}: {context.task_description}",
                metadata={
                    "execution_id": context.execution_id,
                    "phase": "quality_review_complete",
                    "review_success": review_success,
                    "review_quality": review_quality,
                    "review_notes": review_notes
                },
                project_name=context.project_name or "global",
                tags=["quality_review", "completed" if review_success else "failed"]
            )
            
            return {
                "success": review_success,
                "quality_score": review_quality,
                "review_notes": review_notes
            }
            
        except Exception as e:
            logger.error(f"Review phase simulation failed: {e}")
            return {"success": False, "quality_score": 0.0, "review_notes": f"Review failed: {e}"}

    async def _simulate_workflow_execution(self, 
                                         context: WorkflowExecutionContext,
                                         task_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method - kept for backward compatibility.
        
        This method is now a simple wrapper around the new Task delegation
        workflow execution system.
        """
        # Use the new task delegation workflow execution
        task_context = {
            "subtasks": task_state.get("additional_context", {}).get("task_decomposition", {}).get("subtasks", []) if task_state.get("additional_context") else [],
            "memory_context": await self._prepare_memory_context(context)
        }
        
        return await self._execute_task_delegation_workflow(context, task_context)
    
    async def _post_execution_analysis(self, 
                                     context: WorkflowExecutionContext,
                                     result: WorkflowExecutionResult) -> None:
        """Perform post-execution analysis and learning."""
        try:
            # Calculate prediction accuracy
            duration_accuracy = 1.0 - abs(result.predicted_duration - result.actual_duration) / max(result.predicted_duration, 1)
            success_accuracy = 1.0 if (result.predicted_success_rate > 0.5) == result.success else 0.0
            
            # Generate lessons learned
            lessons_learned = []
            optimization_opportunities = []
            
            if result.success:
                if result.actual_duration < result.predicted_duration:
                    lessons_learned.append("Task completed faster than predicted")
                    optimization_opportunities.append("Consider reducing time estimates for similar tasks")
                
                if result.quality_score > 0.9:
                    lessons_learned.append("High quality achieved")
                    optimization_opportunities.append("Use this workflow pattern for quality-critical tasks")
            else:
                lessons_learned.append("Task execution failed")
                optimization_opportunities.append("Analyze failure patterns for improvement")
                
                if result.actual_duration > result.predicted_duration * 1.5:
                    lessons_learned.append("Execution took significantly longer than predicted")
            
            result.lessons_learned = lessons_learned
            result.optimization_opportunities = optimization_opportunities
            
            # Store execution outcome in memory for learning
            await self._store_execution_outcome(context, result)
            
            # Clean up active execution
            if context.execution_id in self.active_executions:
                del self.active_executions[context.execution_id]
            
            # Add to execution history
            self.execution_history.append(result)
            
            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            logger.info(f"Post-execution analysis completed for {context.execution_id}")
            
        except Exception as e:
            logger.error(f"Post-execution analysis failed: {e}")
    
    async def _store_execution_outcome(self,
                                     context: WorkflowExecutionContext,
                                     result: WorkflowExecutionResult) -> None:
        """Store execution outcome in memory for future learning."""
        try:
            outcome_data = {
                "execution_context": {
                    "task_description": context.task_description,
                    "project_name": context.project_name,
                    "priority_level": context.priority_level,
                    "quality_requirements": context.quality_requirements
                },
                "workflow_selection": {
                    "workflow_type": context.workflow_recommendation.workflow_type.value,
                    "confidence": context.workflow_recommendation.confidence,
                    "routing_strategy": context.workflow_recommendation.routing_strategy.value,
                    "predicted_success_rate": context.workflow_recommendation.predicted_success_rate,
                    "predicted_duration": context.workflow_recommendation.estimated_duration_minutes
                },
                "execution_result": {
                    "success": result.success,
                    "outcome": result.outcome,
                    "actual_duration": result.actual_duration,
                    "quality_score": result.quality_score,
                    "efficiency_score": result.efficiency_score
                },
                "learning_data": {
                    "lessons_learned": result.lessons_learned,
                    "optimization_opportunities": result.optimization_opportunities,
                    "prediction_accuracy": {
                        "duration": 1.0 - abs(result.predicted_duration - result.actual_duration) / max(result.predicted_duration, 1),
                        "success": 1.0 if (result.predicted_success_rate > 0.5) == result.success else 0.0
                    }
                }
            }
            
            await self.claude_pm_memory.store_memory(
                category=MemoryCategory.PATTERN,
                content=f"Workflow execution outcome: {result.workflow_type.value} for {context.task_description[:100]}",
                metadata={
                    "type": "workflow_execution_outcome",
                    "execution_id": context.execution_id,
                    "workflow_type": result.workflow_type.value,
                    "success": result.success,
                    "outcome_data": outcome_data,
                    "timestamp": datetime.now().isoformat()
                },
                project_name=context.project_name or "global",
                tags=["workflow_outcome", "execution_learning", result.workflow_type.value,
                      "success" if result.success else "failure"]
            )
            
            logger.debug(f"Stored execution outcome for learning: {context.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to store execution outcome: {e}")
    
    def _update_orchestrator_metrics(self, result: WorkflowExecutionResult) -> None:
        """Update orchestrator performance metrics."""
        total = self.orchestrator_metrics["total_executions"]
        
        # Update counters
        self.orchestrator_metrics["total_executions"] += 1
        if result.success:
            self.orchestrator_metrics["successful_executions"] += 1
        
        new_total = self.orchestrator_metrics["total_executions"]
        
        # Update running averages
        self.orchestrator_metrics["average_execution_time"] = (
            self.orchestrator_metrics["average_execution_time"] * total + result.execution_time_minutes
        ) / new_total
        
        self.orchestrator_metrics["average_quality_score"] = (
            self.orchestrator_metrics["average_quality_score"] * total + result.quality_score
        ) / new_total
        
        # Update workflow type distribution
        workflow_type = result.workflow_type.value
        if workflow_type not in self.orchestrator_metrics["workflow_type_distribution"]:
            self.orchestrator_metrics["workflow_type_distribution"][workflow_type] = 0
        self.orchestrator_metrics["workflow_type_distribution"][workflow_type] += 1
        
        # Update selection accuracy
        duration_accuracy = 1.0 - abs(result.predicted_duration - result.actual_duration) / max(result.predicted_duration, 1)
        success_accuracy = 1.0 if (result.predicted_success_rate > 0.5) == result.success else 0.0
        overall_accuracy = (duration_accuracy + success_accuracy) / 2
        
        self.orchestrator_metrics["selection_accuracy"] = (
            self.orchestrator_metrics["selection_accuracy"] * total + overall_accuracy
        ) / new_total
    
    def _create_failure_result(self, 
                             execution_id: str,
                             error_message: str,
                             start_time: float) -> WorkflowExecutionResult:
        """Create a failure result for error cases."""
        return WorkflowExecutionResult(
            execution_id=execution_id,
            success=False,
            outcome="orchestrator_error",
            workflow_type=WorkflowType.SIMPLE_LINEAR,
            execution_time_minutes=(time.time() - start_time) / 60,
            quality_score=0.0,
            efficiency_score=0.0,
            predicted_success_rate=0.0,
            actual_success_rate=0.0,
            predicted_duration=0,
            actual_duration=int((time.time() - start_time) / 60),
            failure_reasons=[error_message]
        )
    
    # Public interface methods
    
    async def get_workflow_recommendations(self, 
                                         task_description: str,
                                         **kwargs) -> List[WorkflowRecommendation]:
        """
        Get multiple workflow recommendations for a task.
        
        Args:
            task_description: Task to analyze
            **kwargs: Additional parameters
            
        Returns:
            List of workflow recommendations sorted by confidence
        """
        try:
            request = WorkflowSelectionRequest(
                task_description=task_description,
                **kwargs
            )
            
            # Get primary recommendation
            primary_recommendation = await self.workflow_engine.select_workflow(request)
            
            # For now, return just the primary recommendation
            # Future enhancement: generate multiple alternatives
            return [primary_recommendation]
            
        except Exception as e:
            logger.error(f"Failed to get workflow recommendations: {e}")
            return []
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active executions."""
        active = {}
        for execution_id, context in self.active_executions.items():
            active[execution_id] = {
                "task_description": context.task_description,
                "project_name": context.project_name,
                "start_time": context.start_time.isoformat() if context.start_time else None,
                "workflow_type": context.workflow_recommendation.workflow_type.value if context.workflow_recommendation else None,
                "predicted_duration": context.workflow_recommendation.estimated_duration_minutes if context.workflow_recommendation else None
            }
        return active
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        recent_history = self.execution_history[-limit:] if limit > 0 else self.execution_history
        
        return [
            {
                "execution_id": result.execution_id,
                "success": result.success,
                "outcome": result.outcome,
                "workflow_type": result.workflow_type.value,
                "execution_time_minutes": result.execution_time_minutes,
                "quality_score": result.quality_score,
                "efficiency_score": result.efficiency_score
            }
            for result in recent_history
        ]
    
    def get_orchestrator_analytics(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator analytics."""
        analytics = self.orchestrator_metrics.copy()
        
        # Add success rate
        if analytics["total_executions"] > 0:
            analytics["success_rate"] = analytics["successful_executions"] / analytics["total_executions"]
        else:
            analytics["success_rate"] = 0.0
        
        # Add recent trends
        if len(self.execution_history) >= 5:
            recent_results = self.execution_history[-5:]
            analytics["recent_success_rate"] = sum(1 for r in recent_results if r.success) / len(recent_results)
            analytics["recent_avg_quality"] = sum(r.quality_score for r in recent_results) / len(recent_results)
        else:
            analytics["recent_success_rate"] = analytics["success_rate"]
            analytics["recent_avg_quality"] = analytics["average_quality_score"]
        
        return analytics
    
    async def analyze_task_complexity(self, task_description: str, project_name: str = None) -> Dict[str, Any]:
        """Analyze task complexity using the intelligent task planner."""
        try:
            decomposition = await self.task_planner.decompose_task(task_description, project_name)
            
            return {
                "complexity": decomposition.complexity.value,
                "strategy": decomposition.strategy.value,
                "estimated_hours": decomposition.total_estimated_hours,
                "subtask_count": len(decomposition.subtasks),
                "confidence": decomposition.confidence_score,
                "similar_patterns": len(decomposition.similar_decompositions)
            }
            
        except Exception as e:
            logger.error(f"Task complexity analysis failed: {e}")
            return {
                "complexity": "unknown",
                "error": str(e)
            }


# Factory function for easy integration
def create_intelligent_workflow_orchestrator(memory_service=None, config=None) -> IntelligentWorkflowOrchestrator:
    """
    Factory function to create IntelligentWorkflowOrchestrator instance.
    
    Args:
        memory_service: Optional memory service instance
        config: Optional configuration
        
    Returns:
        IntelligentWorkflowOrchestrator: Configured orchestrator instance
    """
    return IntelligentWorkflowOrchestrator(memory_service, config)