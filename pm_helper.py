#!/usr/bin/env python3
"""
PM Helper - Quick Integration for Current Session
=================================================

This is a simplified helper that you can use directly in your current PM session
to generate Task Tool prompts automatically using the agent prompt builder.

Usage in PM session:
    from pm_helper import generate_task_prompt, quick_engineer, quick_docs, quick_qa
    
    # Generate any agent prompt
    prompt = generate_task_prompt(
        agent_type="engineer",
        task="Implement feature X",
        requirements=["Req 1", "Req 2"]
    )
    
    # Use quick shortcuts
    engineer_prompt = quick_engineer("Build authentication system")
    docs_prompt = quick_docs("Update API documentation")
    qa_prompt = quick_qa("Test deployment process")
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add claude_pm to path
sys.path.insert(0, str(Path(__file__).parent / "claude_pm"))

try:
    from claude_pm.services.pm_orchestrator import PMOrchestrator
    from claude_pm.utils.task_tool_helper import TaskToolHelper
    
    # Initialize global instances
    _orchestrator = None
    _helper = None
    
    def get_orchestrator():
        global _orchestrator
        if _orchestrator is None:
            _orchestrator = PMOrchestrator()
        return _orchestrator
    
    def get_helper():
        global _helper
        if _helper is None:
            _helper = TaskToolHelper()
        return _helper
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("PM Helper not available - using fallback")
    
    def get_orchestrator():
        return None
    
    def get_helper():
        return None


def generate_task_prompt(
    agent_type: str,
    task: str,
    requirements: Optional[List[str]] = None,
    deliverables: Optional[List[str]] = None,
    priority: str = "medium"
) -> str:
    """
    Generate a Task Tool prompt for any agent type.
    
    Args:
        agent_type: Agent type (engineer, documenter, qa, ops, security, etc.)
        task: Task description
        requirements: List of requirements
        deliverables: List of expected deliverables
        priority: Task priority (low, medium, high)
        
    Returns:
        Complete Task Tool prompt ready for subprocess creation
    """
    orchestrator = get_orchestrator()
    if not orchestrator:
        return f"**{agent_type.title()}**: {task} + MEMORY COLLECTION REQUIRED"
    
    try:
        return orchestrator.generate_agent_prompt(
            agent_type=agent_type,
            task_description=task,
            requirements=requirements or [],
            deliverables=deliverables or [],
            priority=priority
        )
    except Exception as e:
        return f"**{agent_type.title()}**: {task} + MEMORY COLLECTION REQUIRED\n\n**Error**: {str(e)}"


def quick_engineer(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick engineer agent prompt generation."""
    return generate_task_prompt(
        agent_type="engineer",
        task=task,
        requirements=requirements or ["Follow coding best practices", "Include error handling"],
        deliverables=["Working implementation", "Code documentation", "Unit tests"]
    )


def quick_docs(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick documentation agent prompt generation."""
    return generate_task_prompt(
        agent_type="documenter",
        task=task,
        requirements=requirements or ["Clear and concise writing", "Include examples"],
        deliverables=["Updated documentation", "Changelog entry", "Version notes"]
    )


def quick_qa(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick QA agent prompt generation."""
    return generate_task_prompt(
        agent_type="qa",
        task=task,
        requirements=requirements or ["Comprehensive testing", "Quality validation"],
        deliverables=["Test results", "Quality report", "Issue identification"]
    )


def quick_ops(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick Ops agent prompt generation."""
    return generate_task_prompt(
        agent_type="ops",
        task=task,
        requirements=requirements or ["Deployment best practices", "Rollback strategy"],
        deliverables=["Deployment status", "Operations report", "Monitoring setup"]
    )


def quick_security(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick Security agent prompt generation."""
    return generate_task_prompt(
        agent_type="security",
        task=task,
        requirements=requirements or ["Security best practices", "Vulnerability assessment"],
        deliverables=["Security analysis", "Vulnerability report", "Mitigation plan"]
    )


def quick_research(task: str, requirements: Optional[List[str]] = None) -> str:
    """Quick Research agent prompt generation."""
    return generate_task_prompt(
        agent_type="researcher",
        task=task,
        requirements=requirements or ["Thorough investigation", "Multiple sources"],
        deliverables=["Research report", "Analysis summary", "Recommendations"]
    )


def create_shortcut_prompt(shortcut_type: str) -> str:
    """Create PM shortcut prompts (push, deploy, test, publish)."""
    helper = get_helper()
    if not helper:
        return f"**{shortcut_type.title()}**: Execute {shortcut_type} operation + MEMORY COLLECTION REQUIRED"
    
    try:
        result = helper.create_shortcut_subprocess(shortcut_type)
        if result['success']:
            return result['prompt']
        else:
            return f"**{shortcut_type.title()}**: Execute {shortcut_type} operation + MEMORY COLLECTION REQUIRED\n\n**Error**: {result['error']}"
    except Exception as e:
        return f"**{shortcut_type.title()}**: Execute {shortcut_type} operation + MEMORY COLLECTION REQUIRED\n\n**Error**: {str(e)}"


def push_prompt() -> str:
    """Generate push shortcut prompt."""
    return create_shortcut_prompt("push")


def deploy_prompt() -> str:
    """Generate deploy shortcut prompt."""
    return create_shortcut_prompt("deploy")


def test_prompt() -> str:
    """Generate test shortcut prompt."""
    return create_shortcut_prompt("test")


def publish_prompt() -> str:
    """Generate publish shortcut prompt."""
    return create_shortcut_prompt("publish")


def list_available_agents() -> dict:
    """List all available agents."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        return {"system": ["engineer", "documenter", "qa", "ops", "security", "researcher"]}
    
    try:
        return orchestrator.list_available_agents()
    except Exception as e:
        return {"error": str(e)}


def validate_integration() -> dict:
    """Validate PM orchestrator integration."""
    helper = get_helper()
    if not helper:
        return {"valid": False, "error": "Helper not available"}
    
    try:
        return helper.validate_integration()
    except Exception as e:
        return {"valid": False, "error": str(e)}


def usage_examples():
    """Show usage examples."""
    return """
PM Helper Usage Examples:
========================

1. Basic agent prompt generation:
   prompt = generate_task_prompt("engineer", "Implement JWT auth", ["Security", "Testing"])

2. Quick shortcuts:
   engineer_prompt = quick_engineer("Build REST API")
   docs_prompt = quick_docs("Update README")
   qa_prompt = quick_qa("Test deployment")

3. PM shortcuts:
   push_prompt()    # For version control and release
   deploy_prompt()  # For deployment operations
   test_prompt()    # For testing workflows
   publish_prompt() # For package publication

4. Agent discovery:
   agents = list_available_agents()
   print(f"Available agents: {agents}")

5. Integration validation:
   status = validate_integration()
   print(f"Integration valid: {status['valid']}")

Copy any generated prompt and paste it into a Task Tool subprocess!
"""


if __name__ == "__main__":
    print("🎯 PM Helper - Quick Integration Test")
    print("=" * 50)
    
    # Test basic functionality
    print("Testing basic functionality...")
    
    # Test agent listing
    agents = list_available_agents()
    print(f"✅ Available agents: {len(agents.get('system', []))} system agents")
    
    # Test integration validation
    validation = validate_integration()
    print(f"✅ Integration valid: {validation.get('valid', False)}")
    
    # Test prompt generation
    test_prompt = generate_task_prompt("engineer", "Test PM helper integration")
    print(f"✅ Generated prompt: {len(test_prompt)} characters")
    
    # Test quick shortcuts
    engineer_prompt = quick_engineer("Test engineering workflow")
    print(f"✅ Engineer shortcut: {len(engineer_prompt)} characters")
    
    # Test PM shortcuts
    push_example = push_prompt()
    print(f"✅ Push shortcut: {len(push_example)} characters")
    
    print("\n📋 Usage Examples:")
    print(usage_examples())
    
    print("\n🚀 PM Helper is ready to use!")
    print("Import this file in your PM session to use the helper functions.")