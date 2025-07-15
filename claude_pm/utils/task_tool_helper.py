"""
Task Tool Helper - PM Orchestrator Integration
==============================================

This module provides Task Tool compatibility layer and helper functions for seamless
integration between PM orchestrator and agent prompt builder.

Key Features:
- Task Tool subprocess creation helpers
- Automatic prompt generation and formatting
- Agent delegation workflow management
- Real-time integration with PM orchestrator
- Memory collection integration

Usage Example:
    from claude_pm.utils.task_tool_helper import TaskToolHelper
    
    # Initialize helper
    helper = TaskToolHelper()
    
    # Create Task Tool subprocess with automatic prompt generation
    subprocess_result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Implement JWT authentication",
        requirements=["Security best practices", "Token expiration"],
        deliverables=["Auth system", "Tests", "Documentation"]
    )
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import PM orchestrator
try:
    from claude_pm.services.pm_orchestrator import PMOrchestrator, AgentDelegationContext, collect_pm_orchestrator_memory
except ImportError as e:
    logging.error(f"Failed to import PM orchestrator: {e}")
    # Fallback minimal implementation
    class PMOrchestrator:
        def __init__(self, working_directory=None):
            self.working_directory = Path(working_directory or os.getcwd())
        
        def generate_agent_prompt(self, **kwargs) -> str:
            return f"**{kwargs.get('agent_type', 'Agent').title()}**: {kwargs.get('task_description', 'Task')} + MEMORY COLLECTION REQUIRED"
    
    def collect_pm_orchestrator_memory(**kwargs):
        return {"success": True, "memory_id": "fallback"}

# Import correction capture system
try:
    from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType, capture_subprocess_correction
except ImportError as e:
    logging.error(f"Failed to import correction capture: {e}")
    # Fallback implementation
    class CorrectionCapture:
        def __init__(self):
            self.enabled = False
        
        def create_task_tool_integration_hook(self, *args, **kwargs):
            return {"hook_id": "disabled"}
    
    def capture_subprocess_correction(*args, **kwargs):
        return "disabled"
    
    class CorrectionType:
        CONTENT_CORRECTION = "content_correction"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskToolConfiguration:
    """Configuration for Task Tool subprocess creation."""
    timeout_seconds: int = 300
    memory_collection_required: bool = True
    auto_escalation: bool = True
    progress_tracking: bool = True
    integration_validation: bool = True
    correction_capture_enabled: bool = True
    correction_capture_auto_hook: bool = True


class TaskToolHelper:
    """
    Task Tool Helper with PM Orchestrator Integration
    
    Provides seamless Task Tool subprocess creation with automatic prompt generation,
    delegation tracking, and PM orchestrator integration.
    """
    
    def __init__(self, working_directory: Optional[Path] = None, config: Optional[TaskToolConfiguration] = None):
        """Initialize Task Tool helper with PM orchestrator integration."""
        self.working_directory = Path(working_directory or os.getcwd())
        self.config = config or TaskToolConfiguration()
        self.pm_orchestrator = PMOrchestrator(self.working_directory)
        self._active_subprocesses: Dict[str, Dict[str, Any]] = {}
        self._subprocess_history: List[Dict[str, Any]] = []
        
        # Initialize correction capture system
        self.correction_capture = None
        if self.config.correction_capture_enabled:
            try:
                self.correction_capture = CorrectionCapture()
                logger.info("Correction capture system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize correction capture: {e}")
                self.correction_capture = None
        
        logger.info(f"TaskToolHelper initialized with working directory: {self.working_directory}")
    
    def create_agent_subprocess(
        self,
        agent_type: str,
        task_description: str,
        requirements: Optional[List[str]] = None,
        deliverables: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        priority: str = "medium",
        memory_categories: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = None,
        escalation_triggers: Optional[List[str]] = None,
        integration_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Create Task Tool subprocess with automatic prompt generation.
        
        Args:
            agent_type: Type of agent to create subprocess for
            task_description: Clear description of the task
            requirements: List of specific requirements
            deliverables: List of expected deliverables
            dependencies: List of task dependencies
            priority: Task priority (low, medium, high)
            memory_categories: Memory categories for collection
            timeout_seconds: Subprocess timeout
            escalation_triggers: Conditions for escalation
            integration_notes: Additional integration context
            
        Returns:
            Dictionary containing subprocess information and generated prompt
        """
        try:
            # Generate subprocess ID
            subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate prompt using PM orchestrator
            prompt = self.pm_orchestrator.generate_agent_prompt(
                agent_type=agent_type,
                task_description=task_description,
                requirements=requirements,
                deliverables=deliverables,
                dependencies=dependencies,
                priority=priority,
                memory_categories=memory_categories,
                escalation_triggers=escalation_triggers,
                integration_notes=integration_notes
            )
            
            # Create subprocess information
            subprocess_info = {
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "generated_prompt": prompt,
                "creation_time": datetime.now().isoformat(),
                "status": "created",
                "timeout_seconds": timeout_seconds or self.config.timeout_seconds,
                "requirements": requirements or [],
                "deliverables": deliverables or [],
                "dependencies": dependencies or [],
                "priority": priority,
                "memory_categories": memory_categories or [],
                "escalation_triggers": escalation_triggers or [],
                "integration_notes": integration_notes
            }
            
            # Track active subprocess
            self._active_subprocesses[subprocess_id] = subprocess_info
            
            # Add to history
            self._subprocess_history.append({
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "creation_time": datetime.now().isoformat(),
                "status": "created"
            })
            
            # Collect memory for subprocess creation
            if self.config.memory_collection_required:
                collect_pm_orchestrator_memory(
                    category="architecture:design",
                    content=f"Created Task Tool subprocess for {agent_type}: {task_description}",
                    priority="medium",
                    delegation_id=subprocess_id
                )
            
            # Create correction capture hook
            correction_hook = None
            if self.config.correction_capture_auto_hook and self.correction_capture:
                try:
                    correction_hook = self.correction_capture.create_task_tool_integration_hook(
                        subprocess_id=subprocess_id,
                        agent_type=agent_type,
                        task_description=task_description
                    )
                    logger.info(f"Created correction capture hook: {correction_hook.get('hook_id', 'unknown')}")
                except Exception as e:
                    logger.error(f"Failed to create correction capture hook: {e}")
            
            logger.info(f"Created Task Tool subprocess: {subprocess_id}")
            
            return {
                "success": True,
                "subprocess_id": subprocess_id,
                "subprocess_info": subprocess_info,
                "prompt": prompt,
                "usage_instructions": self._generate_usage_instructions(subprocess_info),
                "correction_hook": correction_hook
            }
            
        except Exception as e:
            logger.error(f"Error creating Task Tool subprocess: {e}")
            
            # Collect error memory
            if self.config.memory_collection_required:
                collect_pm_orchestrator_memory(
                    category="error:integration",
                    content=f"Failed to create Task Tool subprocess for {agent_type}: {str(e)}",
                    priority="high"
                )
            
            return {
                "success": False,
                "error": str(e),
                "fallback_prompt": f"**{agent_type.title()}**: {task_description} + MEMORY COLLECTION REQUIRED"
            }
    
    def _generate_usage_instructions(self, subprocess_info: Dict[str, Any]) -> str:
        """Generate usage instructions for Task Tool subprocess."""
        correction_status = "enabled" if self.correction_capture else "disabled"
        
        return f"""
Task Tool Subprocess Usage Instructions:
========================================

Subprocess ID: {subprocess_info['subprocess_id']}
Agent Type: {subprocess_info['agent_type']}
Creation Time: {subprocess_info['creation_time']}

To use this subprocess:
1. Copy the generated prompt below
2. Create a new Task Tool subprocess
3. Paste the prompt as the subprocess content
4. Monitor subprocess progress
5. Report completion back to PM orchestrator

Generated Prompt:
{'-' * 50}
{subprocess_info['generated_prompt']}
{'-' * 50}

Integration Notes:
- This subprocess is tracked by PM orchestrator
- Memory collection is required for all operations
- Escalation triggers are configured for automatic PM notification
- Progress updates should be provided regularly
- Correction capture is {correction_status} for automatic prompt improvement

Correction Capture Usage:
- If the subprocess response needs correction, use the capture_correction method
- This will help improve future agent responses automatically
- Corrections are stored for evaluation and prompt optimization
"""
    
    def get_subprocess_status(self, subprocess_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of Task Tool subprocesses."""
        if subprocess_id:
            return {
                "subprocess_id": subprocess_id,
                "info": self._active_subprocesses.get(subprocess_id),
                "active": subprocess_id in self._active_subprocesses
            }
        
        return {
            "active_subprocesses": len(self._active_subprocesses),
            "total_subprocesses": len(self._subprocess_history),
            "active_agents": list(set(info["agent_type"] for info in self._active_subprocesses.values())),
            "recent_subprocesses": self._subprocess_history[-5:] if self._subprocess_history else []
        }
    
    def complete_subprocess(self, subprocess_id: str, results: Dict[str, Any]) -> bool:
        """Mark subprocess as complete and process results."""
        if subprocess_id in self._active_subprocesses:
            # Update subprocess info
            self._active_subprocesses[subprocess_id]["status"] = "completed"
            self._active_subprocesses[subprocess_id]["completion_time"] = datetime.now().isoformat()
            self._active_subprocesses[subprocess_id]["results"] = results
            
            # Update history
            for entry in self._subprocess_history:
                if entry["subprocess_id"] == subprocess_id:
                    entry["status"] = "completed"
                    entry["completion_time"] = datetime.now().isoformat()
                    entry["results"] = results
                    break
            
            # Complete delegation in PM orchestrator
            self.pm_orchestrator.complete_delegation(subprocess_id, results)
            
            # Remove from active tracking
            del self._active_subprocesses[subprocess_id]
            
            # Collect completion memory
            if self.config.memory_collection_required:
                collect_pm_orchestrator_memory(
                    category="architecture:design",
                    content=f"Completed Task Tool subprocess {subprocess_id}: {results.get('summary', 'No summary')}",
                    priority="medium",
                    delegation_id=subprocess_id
                )
            
            logger.info(f"Completed Task Tool subprocess: {subprocess_id}")
            return True
        
        return False
    
    def capture_correction(
        self,
        subprocess_id: str,
        original_response: str,
        user_correction: str,
        correction_type: str = "content_correction",
        severity: str = "medium",
        user_feedback: Optional[str] = None
    ) -> str:
        """
        Capture a correction for a subprocess response.
        
        Args:
            subprocess_id: ID of the subprocess
            original_response: Original agent response
            user_correction: User's correction
            correction_type: Type of correction
            severity: Severity level
            user_feedback: Additional feedback
            
        Returns:
            Correction ID
        """
        if not self.correction_capture:
            logger.warning("Correction capture not enabled")
            return ""
        
        # Get subprocess info
        subprocess_info = self._active_subprocesses.get(subprocess_id)
        if not subprocess_info:
            # Check history
            for entry in self._subprocess_history:
                if entry["subprocess_id"] == subprocess_id:
                    subprocess_info = entry
                    break
        
        if not subprocess_info:
            logger.error(f"Subprocess {subprocess_id} not found")
            return ""
        
        try:
            # Convert string correction type to enum
            correction_type_enum = getattr(CorrectionType, correction_type.upper(), CorrectionType.CONTENT_CORRECTION)
            
            correction_id = self.correction_capture.capture_correction(
                agent_type=subprocess_info["agent_type"],
                original_response=original_response,
                user_correction=user_correction,
                context={
                    "subprocess_id": subprocess_id,
                    "task_description": subprocess_info.get("task_description", ""),
                    "working_directory": str(self.working_directory)
                },
                correction_type=correction_type_enum,
                subprocess_id=subprocess_id,
                task_description=subprocess_info.get("task_description", ""),
                severity=severity,
                user_feedback=user_feedback
            )
            
            logger.info(f"Captured correction {correction_id} for subprocess {subprocess_id}")
            return correction_id
            
        except Exception as e:
            logger.error(f"Failed to capture correction: {e}")
            return ""
    
    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get correction capture statistics."""
        if not self.correction_capture:
            return {"enabled": False, "message": "Correction capture not enabled"}
        
        try:
            stats = self.correction_capture.get_correction_stats()
            return {
                "enabled": True,
                "statistics": stats,
                "storage_path": str(self.correction_capture.storage_config.storage_path)
            }
        except Exception as e:
            logger.error(f"Failed to get correction statistics: {e}")
            return {"enabled": True, "error": str(e)}
    
    def list_available_agents(self) -> Dict[str, List[str]]:
        """List all available agents for Task Tool subprocess creation."""
        return self.pm_orchestrator.list_available_agents()
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate Task Tool helper integration with PM orchestrator."""
        try:
            # Test PM orchestrator integration
            pm_validation = self.pm_orchestrator.validate_agent_hierarchy()
            
            # Test agent listing
            agents = self.pm_orchestrator.list_available_agents()
            
            # Test prompt generation
            test_prompt = self.pm_orchestrator.generate_agent_prompt(
                agent_type="engineer",
                task_description="Integration validation test",
                requirements=["Test functionality"],
                deliverables=["Validation report"]
            )
            
            return {
                "valid": True,
                "pm_orchestrator_integration": pm_validation.get("valid", False),
                "available_agents": agents,
                "prompt_generation": len(test_prompt) > 0,
                "active_subprocesses": len(self._active_subprocesses),
                "total_subprocesses": len(self._subprocess_history),
                "working_directory": str(self.working_directory),
                "config": {
                    "timeout_seconds": self.config.timeout_seconds,
                    "memory_collection_required": self.config.memory_collection_required,
                    "auto_escalation": self.config.auto_escalation,
                    "progress_tracking": self.config.progress_tracking,
                    "integration_validation": self.config.integration_validation,
                    "correction_capture_enabled": self.config.correction_capture_enabled,
                    "correction_capture_auto_hook": self.config.correction_capture_auto_hook
                },
                "correction_capture": {
                    "enabled": self.correction_capture is not None,
                    "service_active": self.correction_capture.enabled if self.correction_capture else False
                }
            }
            
        except Exception as e:
            logger.error(f"Integration validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "working_directory": str(self.working_directory)
            }
    
    def create_shortcut_subprocess(self, shortcut_type: str, **kwargs) -> Dict[str, Any]:
        """Create subprocess for common PM orchestrator shortcuts."""
        shortcut_mapping = {
            "push": {
                "agent_type": "documentation",
                "task_description": "Generate changelog and analyze semantic versioning impact for push operation",
                "requirements": ["Analyze git commit history", "Determine version bump needed"],
                "deliverables": ["Changelog content", "Version bump recommendation", "Release notes"]
            },
            "deploy": {
                "agent_type": "ops",
                "task_description": "Execute local deployment operations with validation",
                "requirements": ["Deploy framework files", "Validate deployment"],
                "deliverables": ["Deployment status report", "Validation results"]
            },
            "test": {
                "agent_type": "qa",
                "task_description": "Execute comprehensive test suite and validation",
                "requirements": ["Run all tests", "Validate quality standards"],
                "deliverables": ["Test results", "Quality validation report"]
            },
            "publish": {
                "agent_type": "ops",
                "task_description": "Execute package publication pipeline",
                "requirements": ["Validate package integrity", "Publish to registry"],
                "deliverables": ["Publication status", "Version confirmation"]
            }
        }
        
        if shortcut_type not in shortcut_mapping:
            return {
                "success": False,
                "error": f"Unknown shortcut type: {shortcut_type}",
                "available_shortcuts": list(shortcut_mapping.keys())
            }
        
        # Merge shortcut defaults with provided kwargs
        shortcut_config = shortcut_mapping[shortcut_type]
        shortcut_config.update(kwargs)
        
        return self.create_agent_subprocess(**shortcut_config)
    
    def generate_delegation_summary(self) -> str:
        """Generate a summary of current Task Tool delegations."""
        active_count = len(self._active_subprocesses)
        total_count = len(self._subprocess_history)
        
        summary = f"""
Task Tool Helper - Delegation Summary
=====================================

Current Status:
- Active Subprocesses: {active_count}
- Total Subprocesses Created: {total_count}
- Working Directory: {self.working_directory}

Active Delegations:
"""
        
        if self._active_subprocesses:
            for subprocess_id, info in self._active_subprocesses.items():
                summary += f"""
- {subprocess_id}:
  - Agent: {info['agent_type']}
  - Task: {info['task_description'][:50]}...
  - Priority: {info['priority']}
  - Created: {info['creation_time']}
"""
        else:
            summary += "  (No active delegations)\n"
        
        summary += f"""
Recent History:
"""
        
        if self._subprocess_history:
            for entry in self._subprocess_history[-3:]:
                summary += f"""
- {entry['subprocess_id']}:
  - Agent: {entry['agent_type']}
  - Task: {entry['task_description'][:50]}...
  - Status: {entry['status']}
  - Created: {entry['creation_time']}
"""
        else:
            summary += "  (No delegation history)\n"
        
        return summary


# Helper functions for easy integration
def quick_create_subprocess(
    agent_type: str,
    task_description: str,
    requirements: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    working_directory: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Quick subprocess creation helper.
    
    Args:
        agent_type: Type of agent to create subprocess for
        task_description: Task description
        requirements: List of requirements
        deliverables: List of expected deliverables
        working_directory: Working directory path
        
    Returns:
        Subprocess creation result with generated prompt
    """
    helper = TaskToolHelper(working_directory)
    return helper.create_agent_subprocess(
        agent_type=agent_type,
        task_description=task_description,
        requirements=requirements,
        deliverables=deliverables
    )


def create_pm_shortcuts() -> Dict[str, Dict[str, Any]]:
    """Create all PM orchestrator shortcuts as Task Tool subprocesses."""
    helper = TaskToolHelper()
    
    shortcuts = {}
    shortcut_types = ["push", "deploy", "test", "publish"]
    
    for shortcut_type in shortcut_types:
        shortcuts[shortcut_type] = helper.create_shortcut_subprocess(shortcut_type)
    
    return shortcuts


def validate_task_tool_integration() -> Dict[str, Any]:
    """Validate Task Tool helper integration with PM orchestrator."""
    helper = TaskToolHelper()
    return helper.validate_integration()


if __name__ == "__main__":
    # Test the Task Tool helper
    helper = TaskToolHelper()
    
    # Test subprocess creation
    result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Test Task Tool helper integration",
        requirements=["Create integration test", "Verify functionality"],
        deliverables=["Working test", "Integration validation"]
    )
    
    print("Task Tool Subprocess Creation Result:")
    print("=" * 50)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Subprocess ID: {result['subprocess_id']}")
        print(f"Generated Prompt Length: {len(result['prompt'])} characters")
        print("\nUsage Instructions:")
        print(result['usage_instructions'])
    else:
        print(f"Error: {result['error']}")
    
    # Test status tracking
    status = helper.get_subprocess_status()
    print(f"\nHelper Status: {status}")
    
    # Test validation
    validation = helper.validate_integration()
    print(f"\nIntegration Validation: {validation['valid']}")
    
    # Generate delegation summary
    summary = helper.generate_delegation_summary()
    print(f"\nDelegation Summary:\n{summary}")