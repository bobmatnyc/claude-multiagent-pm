"""
Workflow tracking service for CLI workflow status management.

Manages running workflows, their status, and provides CLI status reporting
for LangGraph workflow executions.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.config import Config
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class WorkflowTracker:
    """
    Tracks workflow executions for CLI status reporting.
    
    Provides persistence and status management for LangGraph workflows
    initiated through CLI commands.
    """
    
    def __init__(self):
        """Initialize workflow tracker with persistent storage."""
        self.config = Config()
        claude_pm_root = self.config.get("claude_pm_path")
        self.storage_dir = Path(claude_pm_root) / "runtime" / "workflows"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.storage_dir / "workflow_status.json"
        
        # Load existing workflows
        self._workflows = self._load_workflows()
    
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflows from persistent storage."""
        if not self.status_file.exists():
            return {}
        
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading workflow status: {e}")
            return {}
    
    def _save_workflows(self):
        """Save workflows to persistent storage."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self._workflows, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving workflow status: {e}")
    
    def start_workflow(self, workflow_name: str, task_description: str, 
                      complexity: str = "medium", priority: str = "medium") -> str:
        """
        Register a new workflow execution.
        
        Args:
            workflow_name: Name of the workflow type
            task_description: Description of the task
            complexity: Workflow complexity level
            priority: Task priority level
            
        Returns:
            Unique workflow ID
        """
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        
        workflow_data = {
            "id": workflow_id,
            "name": workflow_name,
            "task": task_description,
            "complexity": complexity,
            "priority": priority,
            "status": "running",
            "progress": 0,
            "current_agent": "Orchestrator",
            "current_state": "initialization",
            "started_at": datetime.now().isoformat(),
            "estimated_completion": self._estimate_completion(complexity),
            "agents_assigned": [],
            "steps_completed": [],
            "last_update": datetime.now().isoformat()
        }
        
        self._workflows[workflow_id] = workflow_data
        self._save_workflows()
        
        logger.info(f"Started workflow {workflow_id}: {workflow_name}")
        return workflow_id
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]):
        """
        Update workflow status and progress.
        
        Args:
            workflow_id: Workflow identifier
            updates: Dictionary of fields to update
        """
        if workflow_id not in self._workflows:
            logger.warning(f"Workflow {workflow_id} not found for update")
            return
        
        workflow = self._workflows[workflow_id]
        workflow.update(updates)
        workflow["last_update"] = datetime.now().isoformat()
        
        self._save_workflows()
        logger.debug(f"Updated workflow {workflow_id}")
    
    def complete_workflow(self, workflow_id: str, result: Optional[Dict[str, Any]] = None):
        """
        Mark workflow as completed.
        
        Args:
            workflow_id: Workflow identifier
            result: Optional result data
        """
        if workflow_id not in self._workflows:
            logger.warning(f"Workflow {workflow_id} not found for completion")
            return
        
        updates = {
            "status": "completed",
            "progress": 100,
            "completed_at": datetime.now().isoformat()
        }
        
        if result:
            updates["result"] = result
        
        self.update_workflow(workflow_id, updates)
        logger.info(f"Completed workflow {workflow_id}")
    
    def fail_workflow(self, workflow_id: str, error: str):
        """
        Mark workflow as failed.
        
        Args:
            workflow_id: Workflow identifier
            error: Error description
        """
        if workflow_id not in self._workflows:
            logger.warning(f"Workflow {workflow_id} not found for failure")
            return
        
        updates = {
            "status": "failed",
            "error": error,
            "failed_at": datetime.now().isoformat()
        }
        
        self.update_workflow(workflow_id, updates)
        logger.error(f"Failed workflow {workflow_id}: {error}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow data by ID."""
        return self._workflows.get(workflow_id)
    
    def get_running_workflows(self) -> List[Dict[str, Any]]:
        """Get all currently running workflows."""
        return [
            workflow for workflow in self._workflows.values()
            if workflow.get("status") == "running"
        ]
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflows sorted by start time."""
        workflows = list(self._workflows.values())
        workflows.sort(key=lambda w: w.get("started_at", ""), reverse=True)
        return workflows[:limit]
    
    def cleanup_old_workflows(self, days: int = 7):
        """Remove workflow records older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        workflows_to_remove = []
        for workflow_id, workflow in self._workflows.items():
            try:
                started_at = datetime.fromisoformat(workflow["started_at"])
                if started_at.timestamp() < cutoff:
                    workflows_to_remove.append(workflow_id)
            except (ValueError, KeyError):
                # Remove workflows with invalid timestamps
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self._workflows[workflow_id]
        
        if workflows_to_remove:
            self._save_workflows()
            logger.info(f"Cleaned up {len(workflows_to_remove)} old workflows")
    
    def _estimate_completion(self, complexity: str) -> str:
        """Estimate completion time based on complexity."""
        now = datetime.now()
        
        if complexity == "simple":
            completion = now.timestamp() + (60 * 60)  # 1 hour
        elif complexity == "complex":
            completion = now.timestamp() + (6 * 60 * 60)  # 6 hours
        else:  # medium
            completion = now.timestamp() + (2 * 60 * 60)  # 2 hours
        
        return datetime.fromtimestamp(completion).isoformat()


# Global workflow tracker instance
_workflow_tracker = None


def get_workflow_tracker() -> WorkflowTracker:
    """Get global workflow tracker instance."""
    global _workflow_tracker
    if _workflow_tracker is None:
        _workflow_tracker = WorkflowTracker()
    return _workflow_tracker