"""
Subprocess Execution Module
==========================

This module handles subprocess delegation execution, including both simulated
subprocess execution and real OS subprocess execution.
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from ..utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
from ..core.logging_config import get_logger
from .orchestration_types import ReturnCode

# Import subprocess runner for real subprocess creation
try:
    from claude_pm.services.subprocess_runner import SubprocessRunner
except ImportError:
    SubprocessRunner = None

logger = get_logger(__name__)


class SubprocessExecutor:
    """Handles subprocess execution for the orchestrator."""
    
    def __init__(self, working_directory: Path, config: TaskToolConfiguration):
        self.working_directory = working_directory
        self.config = config
        self._task_tool_helper: Optional[TaskToolHelper] = None
        self._subprocess_runner: Optional[SubprocessRunner] = None
    
    async def execute_subprocess_delegation(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using traditional subprocess delegation.
        
        This maintains full compatibility with existing code.
        """
        task_id = kwargs.get("task_id", str(asyncio.current_task().get_name())[:8])
        
        logger.warning("subprocess_delegation_start", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "reason": "fallback_to_subprocess",
            "note": "Using slower SUBPROCESS mode - consider fixing initialization errors for instant LOCAL mode"
        })
        
        # Check if we should use real subprocess (when SubprocessRunner is available)
        use_real_subprocess = (
            SubprocessRunner is not None and 
            os.getenv('CLAUDE_PM_USE_REAL_SUBPROCESS', 'false').lower() == 'true'
        )
        
        if use_real_subprocess:
            # Use real subprocess via SubprocessRunner
            return await self._execute_real_subprocess(
                agent_type=agent_type,
                task_description=task_description,
                **kwargs
            )
        
        # Otherwise use traditional TaskToolHelper approach
        # Initialize task tool helper if needed
        if not self._task_tool_helper:
            # Check for test mode environment variable to enable verbose logging
            test_mode = os.environ.get('CLAUDE_PM_TEST_MODE', '').lower() == 'true'
            
            self._task_tool_helper = TaskToolHelper(
                working_directory=self.working_directory,
                config=self.config,
                verbose=test_mode  # Enable verbose when in test mode
            )
        
        start_time = time.perf_counter()
        
        # Remove task_id from kwargs before passing to TaskToolHelper
        clean_kwargs = {k: v for k, v in kwargs.items() if k != "task_id"}
        
        # Delegate to task tool helper
        result = await self._task_tool_helper.create_agent_subprocess(
            agent_type=agent_type,
            task_description=task_description,
            **clean_kwargs
        )
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        logger.info("subprocess_delegation_complete", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "execution_time_ms": execution_time,
            "success": result.get("success", False) if isinstance(result, dict) else False
        })
        
        # Add task_id to result for tracking
        if isinstance(result, dict):
            result["task_id"] = task_id
        
        # Determine return code based on result
        return_code = ReturnCode.SUCCESS
        if isinstance(result, dict) and not result.get("success", True):
            return_code = ReturnCode.GENERAL_FAILURE
            
        return result, return_code
    
    async def _execute_real_subprocess(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using real OS subprocess with proper environment.
        
        This creates an actual subprocess with the subprocess runner.
        """
        task_id = kwargs.get("task_id", str(asyncio.current_task().get_name())[:8])
        subprocess_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("real_subprocess_execution_start", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "subprocess_id": subprocess_id
        })
        
        try:
            # Initialize subprocess runner if needed
            if not self._subprocess_runner:
                self._subprocess_runner = SubprocessRunner()
                
                # Test environment setup
                test_result = self._subprocess_runner.test_environment()
                if not test_result.get('success'):
                    logger.error("subprocess_environment_test_failed", extra={
                        "error": test_result.get('error'),
                        "task_id": task_id
                    })
                    raise RuntimeError(f"Subprocess environment test failed: {test_result.get('error')}")
            
            # Prepare task data
            task_data = {
                'task_description': task_description,
                'requirements': kwargs.get('requirements', []),
                'deliverables': kwargs.get('deliverables', []),
                'dependencies': kwargs.get('dependencies', []),
                'priority': kwargs.get('priority', 'medium'),
                'memory_categories': kwargs.get('memory_categories', []),
                'escalation_triggers': kwargs.get('escalation_triggers', []),
                'integration_notes': kwargs.get('integration_notes', ''),
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'task_id': task_id,
                'subprocess_id': subprocess_id
            }
            
            # Run subprocess
            start_time = time.perf_counter()
            return_code, stdout, stderr = await self._subprocess_runner.run_agent_subprocess_async(
                agent_type=agent_type,
                task_data=task_data,
                timeout=kwargs.get('timeout_seconds', 300)
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Parse results
            success = return_code == 0
            
            logger.info("real_subprocess_execution_complete", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "subprocess_id": subprocess_id,
                "return_code": return_code,
                "execution_time_ms": execution_time,
                "success": success
            })
            
            # Build result
            result = {
                "success": success,
                "subprocess_id": subprocess_id,
                "task_id": task_id,
                "return_code": return_code if return_code >= 0 else ReturnCode.GENERAL_FAILURE,
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "creation_time": datetime.now().isoformat(),
                    "status": "completed" if success else "failed",
                    "requirements": kwargs.get("requirements", []),
                    "deliverables": kwargs.get("deliverables", []),
                    "priority": kwargs.get("priority", "medium"),
                    "orchestration_mode": "real_subprocess",
                    "task_id": task_id,
                    "execution_time_ms": execution_time
                },
                "stdout": stdout,
                "stderr": stderr,
                "prompt": f"**{agent_type.title()} Agent**: {task_description}",
                "usage_instructions": self._generate_real_subprocess_instructions(
                    subprocess_id, agent_type, return_code, stdout, stderr
                )
            }
            
            return result, return_code if return_code >= 0 else ReturnCode.GENERAL_FAILURE
            
        except Exception as e:
            logger.error("real_subprocess_execution_failed", extra={
                "agent_type": agent_type,
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Return error result
            return {
                "success": False,
                "subprocess_id": subprocess_id,
                "task_id": task_id,
                "return_code": ReturnCode.GENERAL_FAILURE,
                "error": str(e),
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "status": "failed",
                    "orchestration_mode": "real_subprocess",
                    "error": str(e)
                }
            }, ReturnCode.GENERAL_FAILURE
    
    def _generate_real_subprocess_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        return_code: int,
        stdout: str,
        stderr: str
    ) -> str:
        """Generate usage instructions for real subprocess execution."""
        return f"""
Real Subprocess Execution Instructions:
======================================

Subprocess ID: {subprocess_id}
Agent Type: {agent_type}
Return Code: {return_code}
Status: {'SUCCESS' if return_code == 0 else 'FAILED'}

This task was executed in a real OS subprocess:
- Environment variables were properly configured
- Agent profile was loaded from framework
- Subprocess had isolated execution context

Output:
{'-' * 50}
{stdout[:1000]}{'... (truncated)' if len(stdout) > 1000 else ''}
{'-' * 50}

{'Errors:' if stderr else ''}
{'='*50 if stderr else ''}
{stderr[:500] if stderr else ''}
{'='*50 if stderr else ''}

Integration Notes:
- Real subprocess execution provides true isolation
- Framework path and environment were properly set
- Agent profiles were successfully loaded
"""