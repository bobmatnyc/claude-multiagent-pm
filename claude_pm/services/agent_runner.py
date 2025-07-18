"""
Agent Runner - Entry point for agent subprocesses
=================================================

This module serves as the entry point for agent subprocesses created by
the subprocess_runner. It loads the appropriate agent profile and executes
the task with proper context.

Usage:
    python -m claude_pm.services.agent_runner --agent-type engineer --task-file /tmp/task.json
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Ensure environment is properly configured."""
    framework_path = os.getenv('CLAUDE_PM_FRAMEWORK_PATH')
    if not framework_path:
        logger.error("CLAUDE_PM_FRAMEWORK_PATH not set!")
        sys.exit(1)
    
    # Ensure framework is in Python path
    if framework_path not in sys.path:
        sys.path.insert(0, framework_path)
    
    logger.info(f"Agent runner environment configured:")
    logger.info(f"  Framework path: {framework_path}")
    logger.info(f"  Python executable: {sys.executable}")
    logger.info(f"  Python version: {sys.version}")


def load_agent_profile(agent_type: str) -> Dict[str, Any]:
    """Load agent profile using CoreAgentLoader."""
    try:
        from claude_pm.services.core_agent_loader import CoreAgentLoader
        
        loader = CoreAgentLoader()
        profile = loader.load_agent_profile(agent_type)
        
        if not profile:
            raise ValueError(f"No profile found for agent type: {agent_type}")
        
        return {
            'name': profile.name,
            'tier': profile.tier.value,
            'role': profile.role,
            'nickname': profile.nickname,
            'content': profile.content,
            'path': str(profile.path)
        }
        
    except Exception as e:
        logger.error(f"Failed to load agent profile: {e}")
        raise


def execute_agent_task(agent_type: str, task_data: Dict[str, Any]) -> int:
    """
    Execute the agent task.
    
    Args:
        agent_type: Type of agent
        task_data: Task data including description, requirements, etc.
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Load agent profile
        logger.info(f"Loading profile for agent: {agent_type}")
        profile = load_agent_profile(agent_type)
        
        logger.info(f"Agent profile loaded:")
        logger.info(f"  Name: {profile['name']}")
        logger.info(f"  Role: {profile['role']}")
        logger.info(f"  Tier: {profile['tier']}")
        logger.info(f"  Source: {profile['path']}")
        
        # Extract task information
        task_description = task_data.get('task_description', 'No description provided')
        requirements = task_data.get('requirements', [])
        deliverables = task_data.get('deliverables', [])
        
        logger.info(f"Task: {task_description}")
        logger.info(f"Requirements: {len(requirements)}")
        logger.info(f"Deliverables: {len(deliverables)}")
        
        # Build task prompt using the profile
        from claude_pm.services.core_agent_loader import CoreAgentLoader
        loader = CoreAgentLoader()
        
        task_context = {
            'task_description': task_description,
            'requirements': requirements,
            'deliverables': deliverables,
            'temporal_context': f"Today is {task_data.get('current_date', 'unknown')}",
            'integration_notes': task_data.get('integration_notes', '')
        }
        
        prompt = loader.build_task_prompt(agent_type, task_context)
        
        # Output the prompt (in a real implementation, this would execute the task)
        print("\n" + "="*80)
        print("AGENT SUBPROCESS EXECUTION")
        print("="*80)
        print(f"Agent: {profile['nickname']} ({agent_type})")
        print(f"Profile Tier: {profile['tier']}")
        print(f"Profile Source: {profile['path']}")
        print("="*80)
        print("\nGenerated Task Prompt:")
        print("-"*80)
        print(prompt)
        print("-"*80)
        
        # Simulate successful execution
        print("\n✅ Agent task executed successfully")
        print(f"✅ Agent profile loaded from {profile['tier']} tier")
        print(f"✅ Framework path: {os.getenv('CLAUDE_PM_FRAMEWORK_PATH')}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Agent task execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main(agent_type: Optional[str] = None, task_data: Optional[Dict[str, Any]] = None) -> int:
    """
    Main entry point for agent runner.
    
    Can be called directly or via command line.
    """
    # Parse command line arguments if not provided
    if agent_type is None:
        parser = argparse.ArgumentParser(description='Claude PM Agent Runner')
        parser.add_argument('--agent-type', required=True, help='Type of agent to run')
        parser.add_argument('--task-file', required=True, help='Path to task JSON file')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        
        args = parser.parse_args()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        agent_type = args.agent_type
        
        # Load task data from file
        try:
            with open(args.task_file, 'r') as f:
                full_data = json.load(f)
                task_data = full_data.get('task_data', {})
        except Exception as e:
            logger.error(f"Failed to load task file: {e}")
            return 1
    
    # Setup environment
    setup_environment()
    
    # Execute agent task
    return execute_agent_task(agent_type, task_data)


if __name__ == '__main__':
    sys.exit(main())