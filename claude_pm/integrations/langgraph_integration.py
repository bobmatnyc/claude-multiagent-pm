"""
LangGraph Integration for Claude PM Framework.

Provides integration with LangGraph for multi-agent workflows,
state management, and complex decision-making processes.

Note: This integration is managed by the ops agent as part of the
Claude PM service mesh architecture.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Status of a LangGraph workflow."""
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowNode:
    """Definition of a workflow node."""
    name: str
    function: Callable
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    retry_count: int = 0
    description: str = ""


@dataclass
class WorkflowState:
    """State of a workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    current_node: Optional[str] = None
    completed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LangGraphConfig:
    """Configuration for LangGraph integration."""
    enable_state_persistence: bool = True
    max_workflow_duration: int = 3600  # 1 hour
    enable_checkpoints: bool = True
    checkpoint_interval: int = 300  # 5 minutes
    max_parallel_workflows: int = 10
    enable_monitoring: bool = True


class LangGraphIntegration:
    """
    Integration with LangGraph for multi-agent workflow orchestration.
    
    Provides:
    - Workflow definition and execution
    - State management and persistence
    - Multi-agent coordination
    - Error handling and recovery
    - Integration with Claude PM memory system
    
    Note: This is a framework integration managed by the ops agent.
    Actual LangGraph workflows are executed through the service mesh.
    """
    
    def __init__(self, config: Optional[LangGraphConfig] = None):
        """Initialize LangGraph integration."""
        self.config = config or LangGraphConfig()
        
        # Workflow registry
        self._workflows: Dict[str, Dict[str, WorkflowNode]] = {}
        self._active_workflows: Dict[str, WorkflowState] = {}
        
        # State management
        self._state_store: Dict[str, Any] = {}
        self._checkpoints: Dict[str, List[Dict[str, Any]]] = {}
        
        # Pre-defined Claude PM workflows
        self._register_builtin_workflows()
    
    def _register_builtin_workflows(self) -> None:
        """Register built-in Claude PM workflows."""
        # Project setup workflow
        self.register_workflow("project_setup", {
            "validate_requirements": WorkflowNode(
                name="validate_requirements",
                function=self._validate_project_requirements,
                description="Validate project setup requirements"
            ),
            "create_structure": WorkflowNode(
                name="create_structure", 
                function=self._create_project_structure,
                dependencies=["validate_requirements"],
                description="Create project directory structure"
            ),
            "initialize_tracking": WorkflowNode(
                name="initialize_tracking",
                function=self._initialize_project_tracking,
                dependencies=["create_structure"],
                description="Initialize TrackDown system"
            ),
            "setup_memory": WorkflowNode(
                name="setup_memory",
                function=self._setup_project_memory,
                dependencies=["create_structure"],
                description="Setup project memory space"
            ),
            "finalize_setup": WorkflowNode(
                name="finalize_setup",
                function=self._finalize_project_setup,
                dependencies=["initialize_tracking", "setup_memory"],
                description="Finalize project setup"
            )
        })
        
        # Health monitoring workflow
        self.register_workflow("health_monitoring", {
            "collect_metrics": WorkflowNode(
                name="collect_metrics",
                function=self._collect_health_metrics,
                description="Collect system health metrics"
            ),
            "analyze_trends": WorkflowNode(
                name="analyze_trends",
                function=self._analyze_health_trends,
                dependencies=["collect_metrics"],
                description="Analyze health trends"
            ),
            "generate_alerts": WorkflowNode(
                name="generate_alerts",
                function=self._generate_health_alerts,
                dependencies=["analyze_trends"],
                description="Generate health alerts if needed"
            ),
            "update_dashboard": WorkflowNode(
                name="update_dashboard",
                function=self._update_health_dashboard,
                dependencies=["analyze_trends"],
                description="Update health monitoring dashboard"
            )
        })
        
        # Code review workflow
        self.register_workflow("code_review", {
            "analyze_changes": WorkflowNode(
                name="analyze_changes",
                function=self._analyze_code_changes,
                description="Analyze code changes"
            ),
            "check_standards": WorkflowNode(
                name="check_standards",
                function=self._check_coding_standards,
                dependencies=["analyze_changes"],
                description="Check coding standards compliance"
            ),
            "security_scan": WorkflowNode(
                name="security_scan",
                function=self._perform_security_scan,
                dependencies=["analyze_changes"],
                description="Perform security scan"
            ),
            "generate_feedback": WorkflowNode(
                name="generate_feedback",
                function=self._generate_review_feedback,
                dependencies=["check_standards", "security_scan"],
                description="Generate review feedback"
            )
        })
    
    # Workflow Management
    
    def register_workflow(self, workflow_name: str, nodes: Dict[str, WorkflowNode]) -> bool:
        """Register a workflow definition."""
        try:
            # Validate workflow structure
            if not self._validate_workflow_structure(nodes):
                logger.error(f"Invalid workflow structure for {workflow_name}")
                return False
            
            self._workflows[workflow_name] = nodes
            logger.info(f"Registered workflow: {workflow_name} with {len(nodes)} nodes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow_name}: {e}")
            return False
    
    def _validate_workflow_structure(self, nodes: Dict[str, WorkflowNode]) -> bool:
        """Validate workflow structure for cycles and dependencies."""
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_name: str) -> bool:
            if node_name in rec_stack:
                return True
            
            if node_name in visited:
                return False
            
            visited.add(node_name)
            rec_stack.add(node_name)
            
            node = nodes.get(node_name)
            if node:
                for dep in node.dependencies:
                    if dep in nodes and has_cycle(dep):
                        return True
            
            rec_stack.remove(node_name)
            return False
        
        # Check all nodes for cycles
        for node_name in nodes:
            if node_name not in visited:
                if has_cycle(node_name):
                    logger.error(f"Circular dependency detected in workflow starting from {node_name}")
                    return False
        
        # Check that all dependencies exist
        for node_name, node in nodes.items():
            for dep in node.dependencies:
                if dep not in nodes:
                    logger.error(f"Node {node_name} depends on non-existent node {dep}")
                    return False
        
        return True
    
    async def start_workflow(
        self,
        workflow_name: str,
        initial_data: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None
    ) -> Optional[str]:
        """Start a workflow execution."""
        try:
            if workflow_name not in self._workflows:
                logger.error(f"Unknown workflow: {workflow_name}")
                return None
            
            # Generate workflow ID if not provided
            if not workflow_id:
                workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check if we're at max capacity
            if len(self._active_workflows) >= self.config.max_parallel_workflows:
                logger.error("Maximum parallel workflows reached")
                return None
            
            # Create workflow state
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.PENDING,
                data=initial_data or {},
                start_time=datetime.now(),
                metadata={
                    "workflow_name": workflow_name,
                    "created_by": "claude_pm_framework"
                }
            )
            
            self._active_workflows[workflow_id] = workflow_state
            
            # Start workflow execution
            asyncio.create_task(self._execute_workflow(workflow_name, workflow_id))
            
            logger.info(f"Started workflow {workflow_name} with ID: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_name}: {e}")
            return None
    
    async def _execute_workflow(self, workflow_name: str, workflow_id: str) -> None:
        """Execute a workflow."""
        try:
            workflow_state = self._active_workflows[workflow_id]
            workflow_nodes = self._workflows[workflow_name]
            
            workflow_state.status = WorkflowStatus.RUNNING
            
            # Build execution order (topological sort)
            execution_order = self._get_execution_order(workflow_nodes)
            
            for node_name in execution_order:
                node = workflow_nodes[node_name]
                
                # Check if all dependencies are completed
                if not all(dep in workflow_state.completed_nodes for dep in node.dependencies):
                    logger.error(f"Dependencies not met for node {node_name}")
                    workflow_state.status = WorkflowStatus.FAILED
                    workflow_state.error = f"Dependencies not met for node {node_name}"
                    break
                
                # Execute node
                workflow_state.current_node = node_name
                
                try:
                    logger.info(f"Executing node {node_name} in workflow {workflow_id}")
                    
                    # Execute with timeout if specified
                    if node.timeout:
                        result = await asyncio.wait_for(
                            node.function(workflow_state.data),
                            timeout=node.timeout
                        )
                    else:
                        result = await node.function(workflow_state.data)
                    
                    # Update workflow data with result
                    if isinstance(result, dict):
                        workflow_state.data.update(result)
                    
                    workflow_state.completed_nodes.append(node_name)
                    logger.info(f"Completed node {node_name} in workflow {workflow_id}")
                    
                    # Create checkpoint if enabled
                    if self.config.enable_checkpoints:
                        await self._create_checkpoint(workflow_id)
                    
                except asyncio.TimeoutError:
                    logger.error(f"Node {node_name} timed out in workflow {workflow_id}")
                    workflow_state.failed_nodes.append(node_name)
                    workflow_state.status = WorkflowStatus.FAILED
                    workflow_state.error = f"Node {node_name} timed out"
                    break
                    
                except Exception as e:
                    logger.error(f"Node {node_name} failed in workflow {workflow_id}: {e}")
                    workflow_state.failed_nodes.append(node_name)
                    
                    # Retry logic
                    if node.retry_count > 0:
                        logger.info(f"Retrying node {node_name} ({node.retry_count} retries left)")
                        node.retry_count -= 1
                        # Retry logic would go here
                    else:
                        workflow_state.status = WorkflowStatus.FAILED
                        workflow_state.error = f"Node {node_name} failed: {str(e)}"
                        break
            
            # Finalize workflow
            if workflow_state.status == WorkflowStatus.RUNNING:
                workflow_state.status = WorkflowStatus.COMPLETED
                logger.info(f"Workflow {workflow_id} completed successfully")
            
            workflow_state.end_time = datetime.now()
            workflow_state.current_node = None
            
        except Exception as e:
            logger.error(f"Workflow execution failed for {workflow_id}: {e}")
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error = str(e)
            workflow_state.end_time = datetime.now()
    
    def _get_execution_order(self, nodes: Dict[str, WorkflowNode]) -> List[str]:
        """Get execution order using topological sort."""
        in_degree = {name: len(node.dependencies) for name, node in nodes.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Update in-degrees for dependent nodes
            for name, node in nodes.items():
                if current in node.dependencies:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
        
        return result
    
    async def _create_checkpoint(self, workflow_id: str) -> None:
        """Create a checkpoint for workflow state."""
        try:
            workflow_state = self._active_workflows.get(workflow_id)
            if not workflow_state:
                return
            
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "status": workflow_state.status.value,
                "current_node": workflow_state.current_node,
                "completed_nodes": workflow_state.completed_nodes.copy(),
                "data": workflow_state.data.copy()
            }
            
            if workflow_id not in self._checkpoints:
                self._checkpoints[workflow_id] = []
            
            self._checkpoints[workflow_id].append(checkpoint)
            
            # Keep only last 10 checkpoints
            if len(self._checkpoints[workflow_id]) > 10:
                self._checkpoints[workflow_id] = self._checkpoints[workflow_id][-10:]
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint for workflow {workflow_id}: {e}")
    
    # Workflow Status and Control
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get status of a workflow."""
        return self._active_workflows.get(workflow_id)
    
    def list_active_workflows(self) -> List[str]:
        """List IDs of active workflows."""
        return list(self._active_workflows.keys())
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        try:
            workflow_state = self._active_workflows.get(workflow_id)
            if not workflow_state:
                return False
            
            if workflow_state.status == WorkflowStatus.RUNNING:
                workflow_state.status = WorkflowStatus.CANCELLED
                workflow_state.end_time = datetime.now()
                logger.info(f"Cancelled workflow {workflow_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            return False
    
    # Built-in workflow functions
    
    async def _validate_project_requirements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project setup requirements."""
        # Placeholder implementation
        return {"validation_passed": True, "requirements_met": True}
    
    async def _create_project_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project directory structure."""
        # Placeholder implementation
        return {"structure_created": True, "directories": ["docs", "trackdown", "src"]}
    
    async def _initialize_project_tracking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize project tracking system."""
        # Placeholder implementation
        return {"tracking_initialized": True, "backlog_created": True}
    
    async def _setup_project_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Setup project memory space."""
        # Placeholder implementation
        return {"memory_space_created": True, "categories_initialized": True}
    
    async def _finalize_project_setup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize project setup."""
        # Placeholder implementation  
        return {"setup_completed": True, "project_ready": True}
    
    async def _collect_health_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect system health metrics."""
        # Placeholder implementation
        return {"metrics_collected": True, "health_score": 85}
    
    async def _analyze_health_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze health trends."""
        # Placeholder implementation
        return {"trends_analyzed": True, "trend_direction": "stable"}
    
    async def _generate_health_alerts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health alerts."""
        # Placeholder implementation
        return {"alerts_generated": 0, "alert_level": "none"}
    
    async def _update_health_dashboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update health monitoring dashboard."""
        # Placeholder implementation
        return {"dashboard_updated": True, "last_update": datetime.now().isoformat()}
    
    async def _analyze_code_changes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code changes."""
        # Placeholder implementation
        return {"changes_analyzed": True, "files_changed": 5}
    
    async def _check_coding_standards(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check coding standards compliance."""
        # Placeholder implementation
        return {"standards_checked": True, "compliance_score": 90}
    
    async def _perform_security_scan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security scan."""
        # Placeholder implementation
        return {"security_scan_completed": True, "vulnerabilities_found": 0}
    
    async def _generate_review_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate review feedback."""
        # Placeholder implementation
        return {"feedback_generated": True, "recommendations": ["Good code quality"]}


# Factory function for easy instantiation
def create_langgraph_integration(
    enable_state_persistence: bool = True,
    max_workflow_duration: int = 3600,
    max_parallel_workflows: int = 10
) -> LangGraphIntegration:
    """Create a LangGraph integration with specified configuration."""
    config = LangGraphConfig(
        enable_state_persistence=enable_state_persistence,
        max_workflow_duration=max_workflow_duration,
        max_parallel_workflows=max_parallel_workflows
    )
    return LangGraphIntegration(config)