#!/usr/bin/env python3
"""
AI Trackdown Tools Integration Demo for Claude PM Framework.

This example demonstrates how ai-trackdown-tools provides persistent 
issue and PR tracking across subprocess boundaries, enabling coordinated
multi-agent workflows.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the framework to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.core.config import Config
from claude_pm.utils.ai_trackdown_tools import (
    get_ai_trackdown_tools,
    create_persistent_issue,
    update_persistent_issue,
    complete_persistent_issue
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_persistent_tracking():
    """Demonstrate persistent issue tracking across subprocess boundaries."""
    
    logger.info("=== AI Trackdown Tools Integration Demo ===")
    
    # Initialize configuration
    config = Config()
    
    # Get ai-trackdown-tools instance
    tools = get_ai_trackdown_tools(config)
    
    # Check if ai-trackdown-tools is available
    logger.info(f"ai-trackdown-tools enabled: {tools.is_enabled()}")
    logger.info(f"ai-trackdown-tools available: {tools.is_available()}")
    
    if not tools.is_available():
        logger.warning(f"ai-trackdown-tools not available. Fallback method: {tools.get_fallback_method()}")
        logger.info("This demo will show fallback behavior.")
    
    # Demonstrate epic creation
    logger.info("\\n--- Creating Epic ---")
    epic_id = tools.create_epic(
        title="Multi-Agent Coordination Demo",
        description="Demonstrate how multiple agents coordinate through persistent tickets"
    )
    logger.info(f"Created epic: {epic_id}")
    
    # Demonstrate issue creation (simulating Agent A)
    logger.info("\\n--- Agent A: Creating Issues ---")
    issue_1 = create_persistent_issue(
        title="Implement user authentication system",
        description="Set up JWT-based authentication with refresh tokens",
        epic_id=epic_id
    )
    logger.info(f"Agent A created issue: {issue_1}")
    
    issue_2 = create_persistent_issue(
        title="Create user dashboard",
        description="Build responsive user dashboard with real-time updates",
        epic_id=epic_id
    )
    logger.info(f"Agent A created issue: {issue_2}")
    
    # Demonstrate task creation (simulating Agent B)
    logger.info("\\n--- Agent B: Creating Tasks ---")
    task_1 = tools.create_task(
        title="Set up JWT token generation",
        issue_id=issue_1,
        description="Implement JWT token generation and validation"
    )
    logger.info(f"Agent B created task: {task_1}")
    
    task_2 = tools.create_task(
        title="Design dashboard layout",
        issue_id=issue_2,
        description="Create responsive layout with modern UI components"
    )
    logger.info(f"Agent B created task: {task_2}")
    
    # Demonstrate status updates (simulating Agent C)
    logger.info("\\n--- Agent C: Updating Status ---")
    if issue_1:
        success = update_persistent_issue(issue_1, "IN_PROGRESS")
        logger.info(f"Agent C updated issue {issue_1} to IN_PROGRESS: {success}")
    
    if task_1:
        success = tools.update_status("task", task_1, "IN_PROGRESS")
        logger.info(f"Agent C updated task {task_1} to IN_PROGRESS: {success}")
    
    # Demonstrate completion (simulating Agent D)
    logger.info("\\n--- Agent D: Completing Work ---")
    if task_1:
        success = tools.complete_item("task", task_1)
        logger.info(f"Agent D completed task {task_1}: {success}")
    
    if issue_1:
        success = complete_persistent_issue(issue_1)
        logger.info(f"Agent D completed issue {issue_1}: {success}")
    
    # Show overall project status
    logger.info("\\n--- Project Status ---")
    status = tools.get_status()
    if status:
        logger.info("Project status retrieved successfully")
        logger.info(f"Status data: {status}")
    else:
        logger.info("Status retrieval failed or not available")
    
    # List all items
    logger.info("\\n--- Listing All Items ---")
    epics = tools.list_items("epic")
    issues = tools.list_items("issue")
    tasks = tools.list_items("task")
    
    logger.info(f"Epics: {len(epics) if epics else 0}")
    logger.info(f"Issues: {len(issues) if issues else 0}")
    logger.info(f"Tasks: {len(tasks) if tasks else 0}")


async def demonstrate_configuration_flexibility():
    """Demonstrate configuration flexibility and fallback behavior."""
    
    logger.info("\\n=== Configuration Flexibility Demo ===")
    
    # Test with different configurations
    configs = [
        {"use_ai_trackdown_tools": True, "fallback_tracking_method": "logging"},
        {"use_ai_trackdown_tools": False, "fallback_tracking_method": "file"},
        {"use_ai_trackdown_tools": True, "fallback_tracking_method": "disabled"}
    ]
    
    for i, config_dict in enumerate(configs):
        logger.info(f"\\n--- Configuration {i+1}: {config_dict} ---")
        
        config = Config(config_dict)
        tools = get_ai_trackdown_tools(config)
        
        logger.info(f"Enabled: {tools.is_enabled()}")
        logger.info(f"Available: {tools.is_available()}")
        logger.info(f"Fallback method: {tools.get_fallback_method()}")
        
        # Try to create an issue
        issue_id = tools.create_issue(
            title=f"Test issue - Config {i+1}",
            description=f"Testing configuration {config_dict}"
        )
        logger.info(f"Created issue: {issue_id}")


async def demonstrate_error_handling():
    """Demonstrate error handling and graceful degradation."""
    
    logger.info("\\n=== Error Handling Demo ===")
    
    config = Config()
    tools = get_ai_trackdown_tools(config)
    
    # Test invalid operations
    logger.info("\\n--- Testing Invalid Operations ---")
    
    # Try to update non-existent issue
    success = tools.update_status("issue", "INVALID-001", "COMPLETED")
    logger.info(f"Update non-existent issue: {success}")
    
    # Try to complete non-existent task
    success = tools.complete_item("task", "INVALID-001")
    logger.info(f"Complete non-existent task: {success}")
    
    # Test timeout behavior (if available)
    logger.info("\\n--- Testing Timeout Behavior ---")
    
    # Create tools with very short timeout
    short_timeout_config = Config({"ai_trackdown_tools_timeout": 0.1})
    timeout_tools = get_ai_trackdown_tools(short_timeout_config)
    
    # This should timeout or fail gracefully
    status = timeout_tools.get_status()
    logger.info(f"Short timeout status: {status}")


async def main():
    """Main demo function."""
    
    try:
        await demonstrate_persistent_tracking()
        await demonstrate_configuration_flexibility()
        await demonstrate_error_handling()
        
        logger.info("\\n=== Demo Complete ===")
        logger.info("ai-trackdown-tools integration provides:")
        logger.info("1. Persistent state across subprocess boundaries")
        logger.info("2. Hierarchical project organization")
        logger.info("3. Multi-agent coordination capabilities")
        logger.info("4. Configurable integration with fallback support")
        logger.info("5. Graceful error handling and degradation")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())