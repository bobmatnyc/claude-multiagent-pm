"""
Subprocess Runner - Proper subprocess creation with environment handling
======================================================================

This module provides robust subprocess creation for the Claude PM framework,
ensuring that all necessary environment variables are properly set before
subprocess creation.

Key Features:
- Automatic framework path detection and environment setup
- Proper PYTHONPATH configuration
- Environment variable propagation
- Error handling and logging
- Support for both sync and async subprocess creation
"""

import os
import sys
import subprocess
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class SubprocessRunner:
    """
    Manages subprocess creation with proper environment setup.
    
    Ensures that all subprocesses have access to:
    - CLAUDE_PM_FRAMEWORK_PATH
    - Proper PYTHONPATH
    - Agent profiles and framework resources
    """
    
    def __init__(self, framework_path: Optional[Path] = None):
        """Initialize subprocess runner with framework path detection."""
        self.framework_path = framework_path or self._detect_framework_path()
        self.python_executable = sys.executable
        
        logger.info(f"SubprocessRunner initialized with framework path: {self.framework_path}")
        logger.info(f"Python executable: {self.python_executable}")
    
    def _detect_framework_path(self) -> Path:
        """Detect the framework path."""
        # Try environment variable first
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
        
        # Try to find from current file location
        current_file = Path(__file__)
        
        # Go up until we find the project root (has package.json)
        current_dir = current_file.parent
        while current_dir != current_dir.parent:
            if (current_dir / 'package.json').exists():
                # Check if we have framework/agent-roles
                framework_dir = current_dir / 'framework'
                if framework_dir.exists() and (framework_dir / 'agent-roles').exists():
                    return framework_dir
                # Otherwise return project root
                return current_dir
            current_dir = current_dir.parent
        
        # Fallback to current working directory
        cwd = Path.cwd()
        # Check if framework subdirectory exists
        framework_dir = cwd / 'framework'
        if framework_dir.exists() and (framework_dir / 'agent-roles').exists():
            return framework_dir
        
        return cwd
    
    def _prepare_environment(self, env_override: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepare environment variables for subprocess.
        
        Args:
            env_override: Additional environment variables to set
            
        Returns:
            Complete environment dictionary
        """
        # Start with current environment
        env = os.environ.copy()
        
        # Set critical framework paths
        env['CLAUDE_PM_FRAMEWORK_PATH'] = str(self.framework_path)
        
        # Set Python path to include framework
        python_paths = [str(self.framework_path)]
        
        # Add existing PYTHONPATH if any
        if existing_path := env.get('PYTHONPATH'):
            python_paths.extend(existing_path.split(os.pathsep))
        
        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        
        # Add deployment information
        env['CLAUDE_PM_DEPLOYMENT_TYPE'] = 'subprocess'
        env['CLAUDE_PM_SUBPROCESS_RUNNER'] = 'true'
        
        # Apply any overrides
        if env_override:
            env.update(env_override)
        
        logger.debug(f"Prepared environment with {len(env)} variables")
        logger.debug(f"CLAUDE_PM_FRAMEWORK_PATH: {env['CLAUDE_PM_FRAMEWORK_PATH']}")
        logger.debug(f"PYTHONPATH: {env['PYTHONPATH']}")
        
        return env
    
    def run_agent_subprocess(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        timeout: Optional[int] = None,
        env_override: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, str]:
        """
        Run an agent subprocess synchronously.
        
        Args:
            agent_type: Type of agent to run
            task_data: Task data to pass to agent
            timeout: Timeout in seconds
            env_override: Additional environment variables
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        # Prepare environment
        env = self._prepare_environment(env_override)
        
        # Create a temporary file for task data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            json.dump({
                'agent_type': agent_type,
                'task_data': task_data
            }, tf)
            task_file = tf.name
        
        try:
            # Build command
            cmd = [
                self.python_executable,
                '-m', 'claude_pm.services.agent_runner',
                '--agent-type', agent_type,
                '--task-file', task_file
            ]
            
            logger.info(f"Running agent subprocess: {agent_type}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Run subprocess
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"Agent subprocess completed with return code: {result.returncode}")
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Agent subprocess timed out after {timeout}s")
            return -1, "", f"Timeout after {timeout} seconds"
        except Exception as e:
            logger.error(f"Error running agent subprocess: {e}")
            return -1, "", str(e)
        finally:
            # Clean up temp file
            try:
                os.unlink(task_file)
            except:
                pass
    
    async def run_agent_subprocess_async(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        timeout: Optional[int] = None,
        env_override: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, str]:
        """
        Run an agent subprocess asynchronously.
        
        Args:
            agent_type: Type of agent to run
            task_data: Task data to pass to agent
            timeout: Timeout in seconds
            env_override: Additional environment variables
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        # Prepare environment
        env = self._prepare_environment(env_override)
        
        # Create a temporary file for task data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            json.dump({
                'agent_type': agent_type,
                'task_data': task_data
            }, tf)
            task_file = tf.name
        
        try:
            # Build command
            cmd = [
                self.python_executable,
                '-m', 'claude_pm.services.agent_runner',
                '--agent-type', agent_type,
                '--task-file', task_file
            ]
            
            logger.info(f"Running agent subprocess async: {agent_type}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Create subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                stdout_str = stdout.decode('utf-8') if stdout else ""
                stderr_str = stderr.decode('utf-8') if stderr else ""
                
                logger.info(f"Agent subprocess completed with return code: {proc.returncode}")
                
                return proc.returncode or 0, stdout_str, stderr_str
                
            except asyncio.TimeoutError:
                logger.error(f"Agent subprocess timed out after {timeout}s")
                try:
                    proc.terminate()
                    await asyncio.sleep(0.5)
                    if proc.returncode is None:
                        proc.kill()
                except:
                    pass
                return -1, "", f"Timeout after {timeout} seconds"
                
        except Exception as e:
            logger.error(f"Error running agent subprocess: {e}")
            return -1, "", str(e)
        finally:
            # Clean up temp file
            try:
                os.unlink(task_file)
            except:
                pass
    
    def create_standalone_script(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create a standalone Python script that can be run as a subprocess.
        
        Args:
            agent_type: Type of agent
            task_data: Task data
            output_path: Where to save the script
            
        Returns:
            Path to created script
        """
        if not output_path:
            output_path = Path(tempfile.mktemp(suffix='.py'))
        
        script_content = f"""#!/usr/bin/env python3
# Auto-generated agent subprocess script
import os
import sys
import json

# Ensure framework path is set
os.environ['CLAUDE_PM_FRAMEWORK_PATH'] = {repr(str(self.framework_path))}

# Add framework to Python path
sys.path.insert(0, {repr(str(self.framework_path))})

# Import and run agent
from claude_pm.services.agent_runner import main

# Task data
task_data = {repr(task_data)}

# Run agent
if __name__ == '__main__':
    sys.exit(main('{agent_type}', task_data))
"""
        
        output_path.write_text(script_content)
        output_path.chmod(0o755)  # Make executable
        
        logger.info(f"Created standalone agent script: {output_path}")
        
        return output_path
    
    def test_environment(self) -> Dict[str, Any]:
        """Test that the environment is properly configured."""
        env = self._prepare_environment()
        
        # Test Python import
        test_script = """
import sys
import json
import os

# Set framework path from environment
framework_path = os.environ.get('CLAUDE_PM_FRAMEWORK_PATH', '')

try:
    from claude_pm.services.core_agent_loader import CoreAgentLoader
    loader = CoreAgentLoader()
    agents = loader.list_available_agents()
    result = {
        'success': True,
        'framework_path': loader.framework_path.as_posix(),
        'env_framework_path': framework_path,
        'agents': agents,
        'python_path': sys.path[:5]  # First 5 entries
    }
except Exception as e:
    result = {
        'success': False,
        'error': str(e),
        'env_framework_path': framework_path,
        'python_path': sys.path[:5]
    }

print(json.dumps(result))
"""
        
        try:
            result = subprocess.run(
                [self.python_executable, '-c', test_script],
                env=env,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {
                    'success': False,
                    'error': f"Script failed with return code {result.returncode}",
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Test failed: {str(e)}"
            }


# Convenience functions

def create_subprocess_runner(framework_path: Optional[Path] = None) -> SubprocessRunner:
    """Create a subprocess runner instance."""
    return SubprocessRunner(framework_path)


def run_agent_subprocess(
    agent_type: str,
    task_data: Dict[str, Any],
    timeout: Optional[int] = None,
    framework_path: Optional[Path] = None
) -> Tuple[int, str, str]:
    """Quick helper to run an agent subprocess."""
    runner = SubprocessRunner(framework_path)
    return runner.run_agent_subprocess(agent_type, task_data, timeout)


async def run_agent_subprocess_async(
    agent_type: str,
    task_data: Dict[str, Any],
    timeout: Optional[int] = None,
    framework_path: Optional[Path] = None
) -> Tuple[int, str, str]:
    """Quick helper to run an agent subprocess asynchronously."""
    runner = SubprocessRunner(framework_path)
    return await runner.run_agent_subprocess_async(agent_type, task_data, timeout)