"""
Mock System for E2E Testing

Provides comprehensive mocking capabilities for external dependencies.
"""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import MagicMock, patch, AsyncMock
import json
import asyncio
from pathlib import Path
import subprocess
from datetime import datetime


class MockSystem:
    """Comprehensive mock system for external dependencies."""
    
    def __init__(self):
        self.mocks = {}
        self.call_history = []
        self.patches = []
    
    def setup(self):
        """Set up all mocks."""
        self._setup_api_mocks()
        self._setup_subprocess_mocks()
        self._setup_file_system_mocks()
        self._setup_network_mocks()
    
    def teardown(self):
        """Tear down all mocks."""
        for p in self.patches:
            p.stop()
        self.patches.clear()
        self.mocks.clear()
        self.call_history.clear()
    
    def _setup_api_mocks(self):
        """Set up API mocks for OpenAI and Anthropic."""
        # OpenAI Mock
        openai_mock = MagicMock()
        openai_mock.chat.completions.create = self._mock_openai_completion
        self.mocks['openai'] = openai_mock
        
        # Anthropic Mock
        anthropic_mock = MagicMock()
        anthropic_mock.messages.create = self._mock_anthropic_message
        self.mocks['anthropic'] = anthropic_mock
    
    def _setup_subprocess_mocks(self):
        """Set up subprocess mocks."""
        self.subprocess_mock = MagicMock()
        self.subprocess_mock.run = self._mock_subprocess_run
        self.subprocess_mock.Popen = self._mock_subprocess_popen
        
        subprocess_patch = patch('subprocess.run', self.subprocess_mock.run)
        popen_patch = patch('subprocess.Popen', self.subprocess_mock.Popen)
        
        self.patches.extend([subprocess_patch, popen_patch])
        subprocess_patch.start()
        popen_patch.start()
        
        self.mocks['subprocess'] = self.subprocess_mock
    
    def _setup_file_system_mocks(self):
        """Set up file system mocks."""
        self.fs_mock = MagicMock()
        self.mocks['filesystem'] = self.fs_mock
    
    def _setup_network_mocks(self):
        """Set up network-related mocks."""
        self.network_mock = MagicMock()
        self.mocks['network'] = self.network_mock
    
    def _mock_openai_completion(self, **kwargs):
        """Mock OpenAI completion response."""
        self._record_call('openai.completion', kwargs)
        
        return MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Mock OpenAI response for: " + kwargs.get('messages', [{}])[-1].get('content', ''),
                        role="assistant"
                    ),
                    finish_reason="stop"
                )
            ],
            usage=MagicMock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
    
    def _mock_anthropic_message(self, **kwargs):
        """Mock Anthropic message response."""
        self._record_call('anthropic.message', kwargs)
        
        return MagicMock(
            content=[
                MagicMock(
                    text="Mock Anthropic response for: " + kwargs.get('messages', [{}])[-1].get('content', ''),
                    type="text"
                )
            ],
            usage=MagicMock(
                input_tokens=10,
                output_tokens=20
            )
        )
    
    def _mock_subprocess_run(self, cmd, **kwargs):
        """Mock subprocess.run response."""
        self._record_call('subprocess.run', {'cmd': cmd, **kwargs})
        
        # Simulate different command responses
        if 'claude-pm' in str(cmd):
            return self._mock_claude_pm_command(cmd, **kwargs)
        elif 'git' in str(cmd):
            return self._mock_git_command(cmd, **kwargs)
        else:
            return subprocess.CompletedProcess(
                cmd, 0, 
                stdout="Mock command output", 
                stderr=""
            )
    
    def _mock_subprocess_popen(self, cmd, **kwargs):
        """Mock subprocess.Popen response."""
        self._record_call('subprocess.Popen', {'cmd': cmd, **kwargs})
        
        mock_process = MagicMock()
        mock_process.communicate = MagicMock(return_value=("Mock output", ""))
        mock_process.returncode = 0
        mock_process.pid = 12345
        
        return mock_process
    
    def _mock_claude_pm_command(self, cmd: List[str], **kwargs):
        """Mock claude-pm specific commands."""
        if '--version' in cmd:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="claude-pm version 0.7.0",
                stderr=""
            )
        elif 'init' in cmd:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="Framework initialized successfully",
                stderr=""
            )
        else:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="Command executed successfully",
                stderr=""
            )
    
    def _mock_git_command(self, cmd: List[str], **kwargs):
        """Mock git specific commands."""
        if 'status' in cmd:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="On branch main\nnothing to commit, working tree clean",
                stderr=""
            )
        elif 'log' in cmd:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="commit abc123\nAuthor: Test\nDate: 2025-07-19\n\nTest commit",
                stderr=""
            )
        else:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="Git command executed",
                stderr=""
            )
    
    def _record_call(self, service: str, data: Dict[str, Any]):
        """Record a mock call for analysis."""
        self.call_history.append({
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def get_call_history(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get call history, optionally filtered by service."""
        if service:
            return [call for call in self.call_history if call['service'] == service]
        return self.call_history
    
    def add_custom_mock(self, name: str, mock_object: Any):
        """Add a custom mock to the system."""
        self.mocks[name] = mock_object
    
    def configure_mock_response(self, service: str, response_data: Any):
        """Configure a specific response for a mock."""
        if service in self.mocks:
            if hasattr(self.mocks[service], 'return_value'):
                self.mocks[service].return_value = response_data
            else:
                # For more complex mocks, store configuration
                self.mocks[service]._configured_response = response_data


class MockAgent:
    """Mock agent for testing agent interactions."""
    
    def __init__(self, name: str, agent_type: str = "mock"):
        self.name = name
        self.agent_type = agent_type
        self.call_history = []
        self.responses = {}
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock task."""
        self.call_history.append({
            'task': task,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # Return configured response or default
        if task in self.responses:
            return self.responses[task]
        
        return {
            'status': 'success',
            'agent': self.name,
            'result': f"Mock {self.name} completed: {task}",
            'artifacts': []
        }
    
    def configure_response(self, task: str, response: Dict[str, Any]):
        """Configure a specific response for a task."""
        self.responses[task] = response
    
    async def execute_task_async(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock task asynchronously."""
        await asyncio.sleep(0.1)  # Simulate async work
        return self.execute_task(task, context)


class MockOrchestrator:
    """Mock orchestrator for testing orchestration flows."""
    
    def __init__(self):
        self.agents = {}
        self.execution_history = []
    
    def register_agent(self, agent: MockAgent):
        """Register a mock agent."""
        self.agents[agent.name] = agent
    
    def delegate_task(self, agent_name: str, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task to a mock agent."""
        if agent_name not in self.agents:
            return {
                'status': 'error',
                'error': f"Agent {agent_name} not found"
            }
        
        result = self.agents[agent_name].execute_task(task, context)
        
        self.execution_history.append({
            'agent': agent_name,
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    async def delegate_task_async(self, agent_name: str, task: str, 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task asynchronously."""
        if agent_name not in self.agents:
            return {
                'status': 'error',
                'error': f"Agent {agent_name} not found"
            }
        
        result = await self.agents[agent_name].execute_task_async(task, context)
        
        self.execution_history.append({
            'agent': agent_name,
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result