#!/usr/bin/env python3
"""
Template Commands Module
=======================

Command-line interface for template management and deployment operations.
Provides functions for deploying CLAUDE.md templates and template processing.

Framework Version: 014
Implementation: 2025-07-16
"""

import asyncio
import logging
import click
from pathlib import Path
from typing import Optional, Dict, Any

from ..services.parent_directory_manager import ParentDirectoryManager
from ..core.config import Config

logger = logging.getLogger(__name__)


async def deploy_claude_md(target_directory: Optional[str] = None,
                          force: bool = False,
                          show_version_check: bool = False) -> Dict[str, Any]:
    """
    Deploy CLAUDE.md template to target directory.
    
    Args:
        target_directory: Target directory for deployment
        force: Force deployment even if version check fails
        show_version_check: Show version comparison details
        
    Returns:
        Deployment result information
    """
    try:
        # Initialize parent directory manager
        manager = ParentDirectoryManager()
        await manager._initialize()
        
        # Determine target directory
        if target_directory:
            target_path = Path(target_directory)
        else:
            # Default to parent of current directory
            target_path = Path.cwd().parent
        
        # Perform deployment
        result = await manager.deploy_framework_template(
            target_directory=str(target_path),
            force_deploy=force
        )
        
        deployment_info = {
            'success': result,
            'target_directory': str(target_path),
            'force_used': force,
            'timestamp': manager.deployment_timestamp if hasattr(manager, 'deployment_timestamp') else None
        }
        
        if show_version_check:
            # Add version check information if available
            deployment_info['version_check_details'] = {
                'template_version': getattr(manager, 'template_version', 'unknown'),
                'target_version': getattr(manager, 'target_version', 'unknown'),
                'version_comparison': getattr(manager, 'version_comparison_result', 'unknown')
            }
        
        return deployment_info
        
    except Exception as e:
        logger.error(f"Error deploying CLAUDE.md: {e}")
        return {
            'success': False,
            'error': str(e),
            'target_directory': target_directory,
            'force_used': force
        }


def get_template(template_name: str = "default") -> str:
    """
    Get template content by name.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Template content as string
    """
    try:
        # For now, return a basic template
        # This could be expanded to support multiple templates
        
        if template_name == "default" or template_name == "claude_md":
            # Return basic CLAUDE.md template structure
            return """# Claude PM Framework Configuration - Template

<!-- 
CLAUDE_MD_VERSION: 014-001
FRAMEWORK_VERSION: 014
DEPLOYMENT_DATE: {deployment_date}
LAST_UPDATED: {last_updated}
CONTENT_HASH: {content_hash}
-->

## 🤖 AI ASSISTANT ROLE DESIGNATION

**You are operating within a Claude PM Framework deployment**

Your primary role is operating as a multi-agent orchestrator.

## Template Content
This is a basic template structure for CLAUDE.md files.
"""
        
        elif template_name == "task_tool":
            return """**{agent_name}**: {task_description}

TEMPORAL CONTEXT: Today is {current_date}. Apply date awareness to task execution.

**Task**: {task_details}

**Context**: {task_context}

**Authority**: {agent_authority}
**Expected Results**: {expected_deliverables}
"""
        
        else:
            logger.warning(f"Unknown template: {template_name}")
            return f"# Template: {template_name}\n\nTemplate content not found."
            
    except Exception as e:
        logger.error(f"Error getting template {template_name}: {e}")
        return f"# Error: Failed to load template {template_name}"


async def process_template(template_content: str, 
                          variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Process template content with variable substitution.
    
    Args:
        template_content: Template content to process
        variables: Variables for substitution
        
    Returns:
        Processed template content
    """
    try:
        if not variables:
            variables = {}
        
        # Basic variable substitution
        processed_content = template_content
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            processed_content = processed_content.replace(placeholder, str(value))
        
        return processed_content
        
    except Exception as e:
        logger.error(f"Error processing template: {e}")
        return template_content


def list_available_templates() -> list:
    """
    List available templates.
    
    Returns:
        List of available template names
    """
    return [
        "default",
        "claude_md", 
        "task_tool"
    ]


# CLI command functions for backwards compatibility
def deploy_command(args):
    """CLI command for deployment."""
    return asyncio.run(deploy_claude_md(
        target_directory=getattr(args, 'target', None),
        force=getattr(args, 'force', False),
        show_version_check=getattr(args, 'show_version', False)
    ))


def template_command(args):
    """CLI command for template operations."""
    template_name = getattr(args, 'name', 'default')
    return get_template(template_name)


# Click command group for template operations
@click.group()
def template():
    """Template management commands."""
    pass


@template.command("deploy-claude-md")
@click.option('--target', '-t', help='Target directory for deployment')
@click.option('--force', '-f', is_flag=True, help='Force deployment even if version check fails')
@click.option('--show-version-check', is_flag=True, help='Show version comparison details')
def deploy_claude_md_cmd(target, force, show_version_check):
    """Deploy CLAUDE.md template to target directory."""
    try:
        result = asyncio.run(deploy_claude_md(target, force, show_version_check))
        
        if result['success']:
            click.echo(f"✅ Successfully deployed CLAUDE.md to {result['target_directory']}")
            if show_version_check and 'version_check_details' in result:
                details = result['version_check_details']
                click.echo(f"Template version: {details['template_version']}")
                click.echo(f"Target version: {details['target_version']}")
                click.echo(f"Version comparison: {details['version_comparison']}")
        else:
            click.echo(f"❌ Failed to deploy CLAUDE.md: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@template.command("get")
@click.argument('template_name', default='default')
def get_template_cmd(template_name):
    """Get template content by name."""
    try:
        content = get_template(template_name)
        click.echo(content)
    except Exception as e:
        click.echo(f"❌ Error getting template: {e}")


@template.command("list")
def list_templates_cmd():
    """List available templates."""
    try:
        templates = list_available_templates()
        click.echo("Available templates:")
        for tmpl in templates:
            click.echo(f"  • {tmpl}")
    except Exception as e:
        click.echo(f"❌ Error listing templates: {e}")


if __name__ == "__main__":
    # Demo functionality
    async def demo():
        """Demonstrate template commands."""
        print("🔧 Template Commands Demo")
        print("=" * 40)
        
        # List templates
        templates = list_available_templates()
        print(f"Available templates: {templates}")
        
        # Get a template
        template_content = get_template("task_tool")
        print(f"\nTask Tool Template:\n{template_content}")
        
        # Process template with variables
        variables = {
            'agent_name': 'Engineer',
            'task_description': 'Implement authentication system',
            'current_date': '2025-07-16',
            'task_details': 'Create JWT-based authentication',
            'task_context': 'REST API development',
            'agent_authority': 'Code implementation',
            'expected_deliverables': 'Authentication middleware and tests'
        }
        
        processed = await process_template(template_content, variables)
        print(f"\nProcessed Template:\n{processed}")
    
    # Run demo
    asyncio.run(demo())