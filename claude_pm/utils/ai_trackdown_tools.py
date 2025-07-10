"""
AI Trackdown Tools integration utilities for Claude PM Framework.

This module provides integration with ai-trackdown-tools for persistent 
issue and PR tracking across subprocess boundaries.
"""

import logging
import subprocess
import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from claude_pm.core.config import Config

logger = logging.getLogger(__name__)


class AITrackdownTools:
    """
    Integration wrapper for ai-trackdown-tools CLI.
    
    Provides persistent issue and PR tracking across subprocess boundaries
    with fallback support when ai-trackdown-tools is disabled.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize AI Trackdown Tools integration.
        
        Args:
            config: Framework configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get('use_ai_trackdown_tools', True)
        self.timeout = self.config.get('ai_trackdown_tools_timeout', 30)
        self.fallback_logging = self.config.get('ai_trackdown_tools_fallback_logging', True)
        self.fallback_method = self.config.get('fallback_tracking_method', 'logging')
        
        # CLI commands
        self.cli_command = 'aitrackdown'
        self.cli_alias = 'atd'
        
        # Check if ai-trackdown-tools is available
        self.available = self._check_availability()
        
        if not self.available and self.enabled:
            logger.warning(
                "ai-trackdown-tools is enabled but not available. "
                f"Falling back to {self.fallback_method} tracking."
            )
    
    def _check_availability(self) -> bool:
        """Check if ai-trackdown-tools is available."""
        try:
            result = subprocess.run(
                [self.cli_command, '--version'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _run_command(self, cmd: List[str]) -> Optional[Dict[str, Any]]:
        """
        Run ai-trackdown-tools command.
        
        Args:
            cmd: Command arguments
            
        Returns:
            Command output as dict or None if failed
        """
        if not self.enabled:
            self._fallback_log(f"Command skipped (disabled): {' '.join(cmd)}")
            return None
            
        if not self.available:
            self._fallback_log(f"Command failed (unavailable): {' '.join(cmd)}")
            return None
        
        try:
            full_cmd = [self.cli_command] + cmd
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # Try to parse JSON output
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Return raw output if not JSON
                    return {"output": result.stdout, "success": True}
            else:
                logger.error(f"Command failed: {' '.join(full_cmd)}")
                logger.error(f"Error: {result.stderr}")
                self._fallback_log(f"Command failed: {' '.join(full_cmd)} - {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(full_cmd)}")
            self._fallback_log(f"Command timed out: {' '.join(full_cmd)}")
            return None
        except Exception as e:
            logger.error(f"Command error: {e}")
            self._fallback_log(f"Command error: {e}")
            return None
    
    def _fallback_log(self, message: str) -> None:
        """Log to fallback method when ai-trackdown-tools is unavailable."""
        if not self.fallback_logging:
            return
            
        if self.fallback_method == 'logging':
            logger.info(f"[AI-TRACKDOWN-FALLBACK] {message}")
        elif self.fallback_method == 'file':
            fallback_file = Path.home() / ".claude-pm" / "logs" / "ai-trackdown-fallback.log"
            fallback_file.parent.mkdir(parents=True, exist_ok=True)
            with open(fallback_file, 'a') as f:
                f.write(f"[{logger.name}] {message}\\n")
    
    def create_epic(self, title: str, description: str = "") -> Optional[str]:
        """
        Create a new epic.
        
        Args:
            title: Epic title
            description: Epic description
            
        Returns:
            Epic ID if successful, None otherwise
        """
        cmd = ['epic', 'create', title]
        if description:
            cmd.extend(['--description', description])
            
        result = self._run_command(cmd)
        if result and result.get('success'):
            # Parse epic ID from output
            output = result.get('output', '')
            if 'Epic ID:' in output:
                import re
                match = re.search(r'Epic ID: (EP-\d+)', output)
                if match:
                    return match.group(1)
        return None
    
    def create_issue(self, title: str, epic_id: Optional[str] = None, description: str = "") -> Optional[str]:
        """
        Create a new issue.
        
        Args:
            title: Issue title
            epic_id: Parent epic ID (required by ai-trackdown-tools)
            description: Issue description
            
        Returns:
            Issue ID if successful, None otherwise
        """
        if not epic_id:
            self._fallback_log(f"Cannot create issue '{title}' - epic_id is required")
            return None
            
        cmd = ['issue', 'create', title, '--epic', epic_id]
        if description:
            cmd.extend(['--description', description])
            
        result = self._run_command(cmd)
        if result and result.get('success'):
            # Parse issue ID from output
            output = result.get('output', '')
            if 'Issue ID:' in output:
                import re
                match = re.search(r'Issue ID: (ISS-\d+)', output)
                if match:
                    return match.group(1)
        return None
    
    def create_task(self, title: str, issue_id: Optional[str] = None, description: str = "") -> Optional[str]:
        """
        Create a new task.
        
        Args:
            title: Task title
            issue_id: Parent issue ID (required by ai-trackdown-tools)
            description: Task description
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not issue_id:
            self._fallback_log(f"Cannot create task '{title}' - issue_id is required")
            return None
            
        cmd = ['task', 'create', title, '--issue', issue_id]
        if description:
            cmd.extend(['--description', description])
            
        result = self._run_command(cmd)
        if result and result.get('success'):
            # Parse task ID from output
            output = result.get('output', '')
            if 'Task ID:' in output:
                import re
                match = re.search(r'Task ID: (TSK-\d+)', output)
                if match:
                    return match.group(1)
        return None
    
    def update_status(self, item_type: str, item_id: str, status: str) -> bool:
        """
        Update item status.
        
        Args:
            item_type: Type of item ('epic', 'issue', 'task')
            item_id: Item ID
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        cmd = [item_type, 'update', item_id, '--status', status]
        result = self._run_command(cmd)
        return result is not None and result.get('success', False)
    
    def complete_item(self, item_type: str, item_id: str) -> bool:
        """
        Mark item as completed.
        
        Args:
            item_type: Type of item ('epic', 'issue', 'task')
            item_id: Item ID
            
        Returns:
            True if successful, False otherwise
        """
        cmd = [item_type, 'complete', item_id]
        result = self._run_command(cmd)
        return result is not None and result.get('success', False)
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get overall project status.
        
        Returns:
            Status information or None if failed
        """
        result = self._run_command(['status'])
        return result
    
    def list_items(self, item_type: str, status: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        List items of a specific type.
        
        Args:
            item_type: Type of item ('epic', 'issue', 'task')
            status: Filter by status (optional)
            
        Returns:
            List of items or None if failed
        """
        cmd = [item_type, 'list']
        if status:
            cmd.extend(['--status', status])
            
        result = self._run_command(cmd)
        if result and 'items' in result:
            return result['items']
        return None
    
    def is_enabled(self) -> bool:
        """Check if ai-trackdown-tools integration is enabled."""
        return self.enabled
    
    def is_available(self) -> bool:
        """Check if ai-trackdown-tools is available."""
        return self.available
    
    def get_fallback_method(self) -> str:
        """Get current fallback tracking method."""
        return self.fallback_method


# Global instance for easy access
_ai_trackdown_tools = None


def get_ai_trackdown_tools(config: Optional[Config] = None) -> AITrackdownTools:
    """
    Get global AI Trackdown Tools instance.
    
    Args:
        config: Framework configuration object
        
    Returns:
        AITrackdownTools instance
    """
    global _ai_trackdown_tools
    if _ai_trackdown_tools is None:
        _ai_trackdown_tools = AITrackdownTools(config)
    return _ai_trackdown_tools


def create_persistent_issue(title: str, description: str = "", epic_id: Optional[str] = None) -> Optional[str]:
    """
    Create a persistent issue that survives subprocess boundaries.
    
    Args:
        title: Issue title
        description: Issue description
        epic_id: Parent epic ID
        
    Returns:
        Issue ID if successful, None otherwise
    """
    tools = get_ai_trackdown_tools()
    return tools.create_issue(title, epic_id, description)


def update_persistent_issue(issue_id: str, status: str) -> bool:
    """
    Update persistent issue status.
    
    Args:
        issue_id: Issue ID
        status: New status
        
    Returns:
        True if successful, False otherwise
    """
    tools = get_ai_trackdown_tools()
    return tools.update_status('issue', issue_id, status)


def complete_persistent_issue(issue_id: str) -> bool:
    """
    Mark persistent issue as completed.
    
    Args:
        issue_id: Issue ID
        
    Returns:
        True if successful, False otherwise
    """
    tools = get_ai_trackdown_tools()
    return tools.complete_item('issue', issue_id)