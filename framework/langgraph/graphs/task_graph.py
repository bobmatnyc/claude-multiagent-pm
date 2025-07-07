"""
Task workflow graph for single task execution.

Implements the core task execution workflow using LangGraph StateGraph,
with intelligent routing based on complexity and memory integration.
"""

import asyncio
import time
from typing import Dict, Any, Literal, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from ..states.base import TaskState, create_task_state, TaskComplexity, WorkflowStatus
from ..utils.checkpointing import create_checkpointer
from ..utils.config import load_langgraph_config, get_model_for_agent
from ..utils.metrics import get_metrics_collector

try:
    from ....core.logging_config import get_logger
except ImportError:
    # Fallback for testing
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class TaskWorkflowGraph:
    """
    Main task execution workflow using LangGraph.
    
    Orchestrates task execution through multiple agents with intelligent
    routing based on complexity, memory integration, and human approval
    when required.
    """
    
    def __init__(self, memory_client=None, config=None):
        """
        Initialize task workflow graph.
        
        Args:
            memory_client: Optional mem0AI client for memory integration
            config: Optional configuration override
        """
        self.memory_client = memory_client
        self.config = config or load_langgraph_config()
        self.checkpointer = create_checkpointer(
            self.config.get("persistence.database_path")
        )
        self.metrics_collector = get_metrics_collector(
            self.config.get("monitoring.metrics_file")
        )
        
        # Build the workflow graph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Construct the task workflow graph."""
        # Create the graph
        workflow = StateGraph(TaskState)
        
        # Add nodes
        workflow.add_node("memory_init", self._memory_init_node)
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("architect", self._architect_node)
        workflow.add_node("engineer", self._engineer_node)
        workflow.add_node("qa", self._qa_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("memory_store", self._memory_store_node)
        
        # Define edges
        workflow.add_edge(START, "memory_init")
        workflow.add_edge("memory_init", "orchestrator")
        
        # Conditional routing from orchestrator based on complexity
        workflow.add_conditional_edges(
            "orchestrator",
            self._route_by_complexity,
            {
                "simple": "engineer",
                "standard": "architect",
                "complex": "human_approval",
                "human_required": "human_approval"
            }
        )
        
        # Architecture to engineering flow
        workflow.add_edge("architect", "engineer")
        workflow.add_edge("human_approval", "architect")
        
        # Engineering to QA
        workflow.add_edge("engineer", "qa")
        
        # QA routing
        workflow.add_conditional_edges(
            "qa",
            self._route_by_qa_result,
            {
                "pass": "memory_store",
                "fail": "engineer",
                "needs_review": "human_approval"
            }
        )
        
        # Final memory storage
        workflow.add_edge("memory_store", END)
        
        # For now, compile without checkpointer for basic functionality
        # TODO: Fix checkpointer interface compatibility in next iteration
        return workflow.compile()
    
    async def _memory_init_node(self, state: TaskState) -> Dict[str, Any]:
        """Initialize task with memory context."""
        start_time = time.time()
        
        try:
            # Record metrics
            workflow_id = state["id"]
            self.metrics_collector.record_agent_execution(
                workflow_id, "memory_init"
            )
            
            # Load memory context if available
            memory_context = {}
            if self.memory_client:
                # Search for similar tasks
                similar_tasks = await self._search_similar_tasks(state["task_description"])
                memory_context["similar_tasks"] = similar_tasks
                
                # Get relevant patterns
                patterns = await self._get_relevant_patterns(state["task_description"])
                memory_context["patterns"] = patterns
                
                self.metrics_collector.record_memory_operation(workflow_id, "context_load")
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "memory_init", execution_time
            )
            
            return {
                "memory_context": memory_context,
                "status": WorkflowStatus.IN_PROGRESS.value,
                "messages": state["messages"] + [{
                    "agent_id": "memory_init",
                    "role": "system", 
                    "content": f"Loaded memory context with {len(memory_context)} items",
                    "timestamp": datetime.now().isoformat()
                }]
            }
            
        except Exception as e:
            logger.error(f"Memory initialization failed: {e}")
            return {
                "errors": state["errors"] + [{
                    "type": "memory_init_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _orchestrator_node(self, state: TaskState) -> Dict[str, Any]:
        """Main orchestrator that analyzes task and determines routing."""
        start_time = time.time()
        workflow_id = state["id"]
        
        try:
            # Analyze task complexity
            task_description = state["task_description"]
            memory_context = state.get("memory_context", {})
            
            # Simple heuristic-based complexity analysis
            complexity = self._analyze_task_complexity(task_description, memory_context)
            
            # Check if human approval is required
            human_required = self._requires_human_approval(task_description, complexity)
            
            # Estimate cost and time
            cost_estimate = self._estimate_cost(complexity, task_description)
            time_estimate = self._estimate_time(complexity, task_description)
            
            # Determine required agents
            required_agents = self._determine_required_agents(complexity)
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "orchestrator", execution_time
            )
            
            self.metrics_collector.record_agent_execution(
                workflow_id, "orchestrator", 0, 0.0  # No tokens for simple analysis
            )
            
            return {
                "complexity": complexity,
                "assigned_agents": required_agents,
                "cost_estimate": cost_estimate,
                "time_estimate": time_estimate,
                "approval_required": human_required,
                "status": WorkflowStatus.IN_PROGRESS.value,
                "messages": state["messages"] + [{
                    "agent_id": "orchestrator",
                    "role": "orchestrator",
                    "content": f"Task analyzed: complexity={complexity}, agents={required_agents}",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "complexity": complexity,
                        "cost_estimate": cost_estimate,
                        "time_estimate": time_estimate
                    }
                }]
            }
            
        except Exception as e:
            logger.error(f"Orchestrator analysis failed: {e}")
            self.metrics_collector.record_error(
                workflow_id, "orchestrator_error", str(e), "orchestrator"
            )
            return {
                "errors": state["errors"] + [{
                    "type": "orchestrator_error", 
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _architect_node(self, state: TaskState) -> Dict[str, Any]:
        """Architect agent for design and planning."""
        start_time = time.time()
        workflow_id = state["id"]
        
        try:
            # Simulate architecture work
            await asyncio.sleep(0.1)  # Placeholder for actual LLM call
            
            architecture_design = {
                "approach": "modular_design",
                "components": ["interface", "business_logic", "data_layer"],
                "patterns": ["repository", "service"],
                "considerations": ["scalability", "maintainability", "testability"]
            }
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "architect", execution_time, 150, 0.01  # Estimated tokens/cost
            )
            
            self.metrics_collector.record_agent_execution(
                workflow_id, "architect", 150, 0.01
            )
            
            return {
                "results": {
                    **state.get("results", {}),
                    "architecture": architecture_design
                },
                "messages": state["messages"] + [{
                    "agent_id": "architect",
                    "role": "architect",
                    "content": "Architecture design completed",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": architecture_design
                }]
            }
            
        except Exception as e:
            logger.error(f"Architect node failed: {e}")
            self.metrics_collector.record_error(
                workflow_id, "architect_error", str(e), "architect"
            )
            return {
                "errors": state["errors"] + [{
                    "type": "architect_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _engineer_node(self, state: TaskState) -> Dict[str, Any]:
        """Engineer agent for implementation."""
        start_time = time.time()
        workflow_id = state["id"]
        
        try:
            # Simulate engineering work
            await asyncio.sleep(0.2)  # Placeholder for actual implementation
            
            implementation_result = {
                "status": "implemented",
                "files_created": ["main.py", "utils.py", "tests.py"],
                "lines_of_code": 150,
                "test_coverage": 85.0
            }
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "engineer", execution_time, 300, 0.02  # Estimated tokens/cost
            )
            
            self.metrics_collector.record_agent_execution(
                workflow_id, "engineer", 300, 0.02
            )
            
            return {
                "results": {
                    **state.get("results", {}),
                    "implementation": implementation_result
                },
                "deliverables": [{
                    "type": "code_implementation",
                    "files": implementation_result["files_created"],
                    "timestamp": datetime.now().isoformat()
                }],
                "messages": state["messages"] + [{
                    "agent_id": "engineer", 
                    "role": "engineer",
                    "content": "Implementation completed",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": implementation_result
                }]
            }
            
        except Exception as e:
            logger.error(f"Engineer node failed: {e}")
            self.metrics_collector.record_error(
                workflow_id, "engineer_error", str(e), "engineer"
            )
            return {
                "errors": state["errors"] + [{
                    "type": "engineer_error",
                    "message": str(e), 
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _qa_node(self, state: TaskState) -> Dict[str, Any]:
        """QA agent for testing and validation."""
        start_time = time.time()
        workflow_id = state["id"]
        
        try:
            # Simulate QA work
            await asyncio.sleep(0.1)  # Placeholder for actual testing
            
            qa_result = {
                "tests_run": 25,
                "tests_passed": 24,
                "tests_failed": 1,
                "coverage": 85.0,
                "issues": [
                    {"severity": "low", "description": "Minor formatting issue"}
                ],
                "overall_quality": "good"
            }
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "qa", execution_time, 100, 0.008  # Estimated tokens/cost
            )
            
            self.metrics_collector.record_agent_execution(
                workflow_id, "qa", 100, 0.008
            )
            
            # Increment retry count for loop prevention
            current_retries = state.get("metadata", {}).get("qa_retries", 0)
            updated_metadata = {
                **state.get("metadata", {}),
                "qa_retries": current_retries + 1
            }
            
            return {
                "results": {
                    **state.get("results", {}),
                    "qa": qa_result
                },
                "quality_checks": qa_result,
                "metadata": updated_metadata,
                "messages": state["messages"] + [{
                    "agent_id": "qa",
                    "role": "qa",
                    "content": f"QA completed: {qa_result['tests_passed']}/{qa_result['tests_run']} tests passed",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": qa_result
                }]
            }
            
        except Exception as e:
            logger.error(f"QA node failed: {e}")
            self.metrics_collector.record_error(
                workflow_id, "qa_error", str(e), "qa"
            )
            return {
                "errors": state["errors"] + [{
                    "type": "qa_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _human_approval_node(self, state: TaskState) -> Dict[str, Any]:
        """Human approval node for complex tasks."""
        workflow_id = state["id"]
        
        try:
            # For demo purposes, auto-approve
            # In real implementation, this would wait for human input
            approval_result = {
                "approved": True,
                "approver": "system_auto",
                "timestamp": datetime.now().isoformat(),
                "feedback": "Auto-approved for demo"
            }
            
            self.metrics_collector.record_human_intervention(workflow_id)
            
            return {
                "approval_status": "approved",
                "messages": state["messages"] + [{
                    "agent_id": "human_approval",
                    "role": "human",
                    "content": "Approval granted",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": approval_result
                }]
            }
            
        except Exception as e:
            logger.error(f"Human approval node failed: {e}")
            return {
                "approval_status": "failed",
                "errors": state["errors"] + [{
                    "type": "approval_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    async def _memory_store_node(self, state: TaskState) -> Dict[str, Any]:
        """Store results and learnings in memory."""
        start_time = time.time()
        workflow_id = state["id"]
        
        try:
            # Store completion patterns if memory client available
            if self.memory_client:
                await self._store_completion_patterns(state)
                self.metrics_collector.record_memory_operation(workflow_id, "pattern_store")
            
            execution_time = int((time.time() - start_time) * 1000)
            self.checkpointer.record_agent_execution(
                workflow_id, "memory_store", execution_time
            )
            
            return {
                "status": WorkflowStatus.COMPLETED.value,
                "messages": state["messages"] + [{
                    "agent_id": "memory_store",
                    "role": "system",
                    "content": "Task completed and patterns stored",
                    "timestamp": datetime.now().isoformat()
                }]
            }
            
        except Exception as e:
            logger.error(f"Memory store node failed: {e}")
            return {
                "errors": state["errors"] + [{
                    "type": "memory_store_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }]
            }
    
    def _route_by_complexity(self, state: TaskState) -> Literal["simple", "standard", "complex", "human_required"]:
        """Route based on task complexity analysis."""
        if state.get("approval_required", False):
            return "human_required"
        
        complexity = state.get("complexity", "standard")
        return complexity
    
    def _route_by_qa_result(self, state: TaskState) -> Literal["pass", "fail", "needs_review"]:
        """Route based on QA results."""
        qa_result = state.get("quality_checks", {})
        
        # Check for critical issues
        issues = qa_result.get("issues", [])
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        
        # Prevent infinite loops - check if we've already retried
        retry_count = state.get("metadata", {}).get("qa_retries", 0)
        
        if critical_issues and retry_count < 2:
            return "needs_review"
        elif qa_result.get("tests_failed", 0) > 0 and retry_count < 1:
            return "fail"
        else:
            return "pass"
    
    def _analyze_task_complexity(self, task_description: str, memory_context: Dict) -> str:
        """Analyze task complexity using heuristics and memory."""
        # Simple keyword-based analysis
        task_lower = task_description.lower()
        
        simple_keywords = ["fix typo", "update readme", "add comment", "rename"]
        complex_keywords = ["refactor", "migrate", "redesign", "optimize", "security"]
        
        if any(keyword in task_lower for keyword in simple_keywords):
            return TaskComplexity.SIMPLE.value
        elif any(keyword in task_lower for keyword in complex_keywords):
            return TaskComplexity.COMPLEX.value
        else:
            return TaskComplexity.STANDARD.value
    
    def _requires_human_approval(self, task_description: str, complexity: str) -> bool:
        """Determine if human approval is required."""
        if complexity == TaskComplexity.COMPLEX.value:
            return True
        
        # Check for security-related keywords
        security_keywords = ["security", "auth", "permission", "access", "password"]
        return any(keyword in task_description.lower() for keyword in security_keywords)
    
    def _estimate_cost(self, complexity: str, task_description: str) -> Dict[str, float]:
        """Estimate cost based on complexity."""
        base_costs = {
            TaskComplexity.SIMPLE.value: 0.01,
            TaskComplexity.STANDARD.value: 0.05,
            TaskComplexity.COMPLEX.value: 0.15
        }
        
        return {
            "estimated_usd": base_costs.get(complexity, 0.05),
            "confidence": 0.7
        }
    
    def _estimate_time(self, complexity: str, task_description: str) -> int:
        """Estimate time in minutes based on complexity."""
        base_times = {
            TaskComplexity.SIMPLE.value: 5,
            TaskComplexity.STANDARD.value: 15,
            TaskComplexity.COMPLEX.value: 45
        }
        
        return base_times.get(complexity, 15)
    
    def _determine_required_agents(self, complexity: str) -> List[str]:
        """Determine required agents based on complexity."""
        base_agents = ["orchestrator", "engineer", "qa"]
        
        if complexity in [TaskComplexity.STANDARD.value, TaskComplexity.COMPLEX.value]:
            base_agents.insert(1, "architect")
        
        return base_agents
    
    async def _search_similar_tasks(self, task_description: str) -> List[Dict]:
        """Search for similar tasks in memory (placeholder)."""
        # Placeholder - would use mem0AI search
        return []
    
    async def _get_relevant_patterns(self, task_description: str) -> List[Dict]:
        """Get relevant patterns from memory (placeholder)."""
        # Placeholder - would use mem0AI pattern search
        return []
    
    async def _store_completion_patterns(self, state: TaskState) -> None:
        """Store completion patterns in memory (placeholder)."""
        # Placeholder - would store patterns in mem0AI
        pass
    
    async def execute(
        self,
        task_description: str,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task through the workflow.
        
        Args:
            task_description: Description of the task to execute
            context: Optional context dictionary
            user_id: Optional user identifier
            project_id: Optional project identifier
            
        Returns:
            Dict[str, Any]: Final workflow state
        """
        # Generate unique task ID
        task_id = f"task_{int(time.time() * 1000)}"
        
        # Start metrics collection
        metrics = self.metrics_collector.start_workflow(task_id, "task")
        
        # Create initial state
        initial_state = create_task_state(
            task_id=task_id,
            task_description=task_description,
            user_id=user_id,
            project_id=project_id
        )
        
        # Add context if provided
        if context:
            initial_state["context"].update(context)
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": task_id}}
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Finish metrics collection
            self.metrics_collector.finish_workflow(task_id)
            
            logger.info(f"Task {task_id} completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.metrics_collector.record_error(task_id, "execution_error", str(e), "system")
            self.metrics_collector.finish_workflow(task_id)
            raise