"""
Context Collection Module
========================

Handles collection and formatting of context for agent execution.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ContextCollector:
    """Handles context collection and formatting for orchestration."""
    
    def __init__(self, working_directory: Optional[Path] = None):
        self.working_directory = Path(working_directory) if working_directory else Path.cwd()
        
    async def collect_full_context(self) -> Dict[str, Any]:
        """
        Collect the full context for the current working directory.
        
        This includes:
        - Project files and structure
        - CLAUDE.md instructions
        - Current task information
        - Git status and recent commits
        - Active tickets
        """
        context = {
            "working_directory": str(self.working_directory),
            "timestamp": datetime.now().isoformat(),
            "files": {},
        }
        
        try:
            # Collect CLAUDE.md files
            claude_md_files = {}
            
            # Check for project CLAUDE.md
            project_claude = self.working_directory / "CLAUDE.md"
            if project_claude.exists():
                claude_md_files[str(project_claude)] = project_claude.read_text()
            
            # Check for parent CLAUDE.md
            parent_claude = self.working_directory.parent / "CLAUDE.md"
            if parent_claude.exists():
                claude_md_files[str(parent_claude)] = parent_claude.read_text()
            
            # Check for framework CLAUDE.md
            framework_claude = Path(__file__).parent.parent.parent / "framework" / "CLAUDE.md"
            if framework_claude.exists():
                claude_md_files[str(framework_claude)] = framework_claude.read_text()
            
            if claude_md_files:
                context["files"].update(claude_md_files)
                context["claude_md_content"] = claude_md_files
            
            # Collect project structure information
            # For now, we'll add a simplified version - in production this would be more comprehensive
            context["project_structure"] = {
                "type": "python_project",
                "has_git": (self.working_directory / ".git").exists(),
                "has_tests": (self.working_directory / "tests").exists(),
                "main_directories": []
            }
            
            # Add main directories
            for item in self.working_directory.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    context["project_structure"]["main_directories"].append(item.name)
            
            # Add any active task information from shared context if available
            if hasattr(self, "_task_context"):
                context["current_task"] = self._task_context
            
            logger.debug(f"Collected full context with {len(context['files'])} files")
            
        except Exception as e:
            logger.error(f"Error collecting full context: {e}")
            # Return minimal context on error
            return {
                "working_directory": str(self.working_directory),
                "timestamp": datetime.now().isoformat(),
                "error": f"Context collection error: {str(e)}"
            }
        
        return context
    
    def generate_local_usage_instructions(
        self,
        subprocess_id: str,
        agent_type: str,
        response
    ) -> str:
        """Generate usage instructions for local orchestration."""
        return f"""
Local Orchestration Execution Instructions:
===========================================

Subprocess ID: {subprocess_id}
Agent Type: {agent_type}
Orchestration Mode: LOCAL
Response Status: {response.status.value.upper()}

This task was executed using local orchestration:
- Context was automatically filtered for the agent type
- Message was routed through the internal message bus
- No external subprocess was created

Results:
{'-' * 50}
Status: {response.status.value.upper()}
{f"Error: {response.error}" if response.error else "Success"}
{f"Results: {response.data.get('result', '')}" if response.data and 'result' in response.data else ""}
{'-' * 50}

Integration Notes:
- This execution used in-process orchestration
- Context filtering reduced data transfer overhead
- Performance metrics are included in orchestration_metadata
"""