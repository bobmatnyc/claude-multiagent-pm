"""
Subprocess Execution Module
==========================

Handles execution of agent tasks via subprocess delegation, maintaining
full backward compatibility with existing TaskToolHelper patterns.
"""

import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from .types import ReturnCode
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration

# Try to import SubprocessRunner (might not be available in all environments)
try:
    from claude_pm.subprocess_runner import SubprocessRunner
except ImportError:
    SubprocessRunner = None

logger = logging.getLogger(__name__)


class SubprocessExecutor:
    """Handles subprocess-based agent task execution."""
    
    def __init__(self, working_directory: Optional[str] = None, config: Optional[TaskToolConfiguration] = None):
        self.working_directory = working_directory or os.getcwd()
        self.config = config
        self._task_tool_helper = None
        self._subprocess_runner = None
        
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
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        
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
            return await self.execute_real_subprocess(
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
            return_code = ReturnCode.GENERAL_ERROR
            
        return result, return_code
    
    async def execute_real_subprocess(
        self,
        agent_type: str,
        task_description: str,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Execute task using real OS subprocess with proper environment.
        
        This creates an actual subprocess with the subprocess runner.
        """
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
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
                "return_code": return_code if return_code >= 0 else ReturnCode.GENERAL_ERROR,
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
                "usage_instructions": self.generate_real_subprocess_instructions(
                    subprocess_id, agent_type, return_code, stdout, stderr
                )
            }
            
            return result, return_code if return_code >= 0 else ReturnCode.GENERAL_ERROR
            
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
                "return_code": ReturnCode.GENERAL_ERROR,
                "error": str(e),
                "subprocess_info": {
                    "subprocess_id": subprocess_id,
                    "agent_type": agent_type,
                    "task_description": task_description,
                    "status": "failed",
                    "orchestration_mode": "real_subprocess",
                    "error": str(e)
                }
            }, ReturnCode.GENERAL_ERROR
    
    def generate_real_subprocess_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        return_code: int,
        stdout: str,
        stderr: str
    ) -> str:
        """Generate usage instructions for real subprocess execution."""
        status = "completed successfully" if return_code == 0 else f"failed with code {return_code}"
        
        instructions = [
            f"# Real Subprocess Execution ({subprocess_id})",
            f"Agent Type: {agent_type}",
            f"Status: {status}",
            ""
        ]
        
        if stdout:
            instructions.extend([
                "## Output:",
                "```",
                stdout.strip(),
                "```",
                ""
            ])
            
        if stderr:
            instructions.extend([
                "## Errors:",
                "```",
                stderr.strip(),
                "```",
                ""
            ])
            
        instructions.extend([
            "## Integration:",
            "- Process the output above according to your needs",
            "- Check return code for success/failure",
            "- Handle any errors appropriately"
        ])
        
        return "\n".join(instructions)
    
    async def emergency_subprocess_fallback(
        self,
        agent_type: str,
        task_description: str,
        error: Exception,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Emergency fallback when primary execution methods fail.
        
        This ensures we always return a valid response structure.
        """
        task_id = kwargs.get("task_id", str(uuid.uuid4())[:8])
        subprocess_id = f"{agent_type}_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.error("emergency_subprocess_fallback", extra={
            "agent_type": agent_type,
            "task_id": task_id,
            "subprocess_id": subprocess_id,
            "original_error": str(error),
            "error_type": type(error).__name__
        })
        
        # Build emergency response
        result = {
            "success": False,
            "subprocess_id": subprocess_id,
            "task_id": task_id,
            "return_code": ReturnCode.GENERAL_ERROR,
            "error": f"Emergency fallback triggered: {str(error)}",
            "subprocess_info": {
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "creation_time": datetime.now().isoformat(),
                "status": "emergency_fallback",
                "requirements": kwargs.get("requirements", []),
                "deliverables": kwargs.get("deliverables", []),
                "priority": kwargs.get("priority", "medium"),
                "orchestration_mode": "emergency_fallback",
                "task_id": task_id,
                "error": str(error)
            },
            "prompt": f"**{agent_type.title()} Agent**: {task_description}",
            "usage_instructions": f"""
# Emergency Fallback Response

An error occurred during orchestration: {str(error)}

## Manual Steps Required:
1. Review the error message above
2. Check system logs for more details
3. Consider running the task manually
4. Report persistent issues to the development team

## Task Details:
- Agent Type: {agent_type}
- Task: {task_description}
- Task ID: {task_id}
- Subprocess ID: {subprocess_id}
"""
        }
        
        return result, ReturnCode.GENERAL_ERROR