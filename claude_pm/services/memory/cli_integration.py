"""
CLI Integration for Memory Triggers

Integration points for adding memory triggers to existing CLI commands
and workflow operations in the Claude PM Framework.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from functools import wraps
import click

from .memory_trigger_service import MemoryTriggerService, get_global_memory_trigger_service
from .decorators import workflow_memory_trigger, agent_memory_trigger, set_global_hooks
from .framework_hooks import HookContext


logger = logging.getLogger(__name__)


def cli_memory_trigger(
    operation_type: str = "workflow",
    project_name: str = "claude-multiagent-pm",
    capture_result: bool = True
):
    """
    Decorator for CLI commands to add memory triggers.
    
    Args:
        operation_type: Type of operation (workflow, agent, issue, etc.)
        project_name: Project name
        capture_result: Whether to capture command result
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get global memory trigger service
            service = await get_global_memory_trigger_service()
            
            if not service:
                # No memory triggers configured, execute normally
                return await func(*args, **kwargs)
            
            hooks = service.get_framework_hooks()
            if not hooks:
                return await func(*args, **kwargs)
            
            # Create hook context
            context = HookContext(
                operation_name=func.__name__,
                project_name=project_name,
                source="cli",
                tags=["cli", operation_type]
            )
            
            success = False
            result = None
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                success = True
                
                # Execute completion hook
                if operation_type == "workflow":
                    await hooks.workflow_completed(
                        context,
                        success=success,
                        workflow_type=func.__name__,
                        result=result if capture_result else None
                    )
                elif operation_type == "agent":
                    await hooks.agent_operation_completed(
                        context,
                        agent_type=func.__name__,
                        success=success,
                        result=result if capture_result else None
                    )
                
                return result
                
            except Exception as e:
                success = False
                
                # Execute error hook
                await hooks.workflow_error(
                    context,
                    success=success,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't easily integrate async hooks
            # So we just execute the function normally
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class MemoryIntegratedCLI:
    """
    CLI integration helper for memory triggers.
    
    Provides methods to integrate memory triggers into existing
    CLI commands and workflow operations.
    """
    
    def __init__(self, service: Optional[MemoryTriggerService] = None):
        """
        Initialize CLI integration.
        
        Args:
            service: Memory trigger service instance
        """
        self.service = service
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize CLI integration."""
        if not self.service:
            self.service = await get_global_memory_trigger_service()
        
        if self.service:
            self.logger.info("Memory trigger CLI integration initialized")
        else:
            self.logger.warning("No memory trigger service available")
    
    async def execute_with_memory_trigger(
        self,
        operation_name: str,
        operation_func,
        project_name: str = "claude-multiagent-pm",
        operation_type: str = "workflow",
        **kwargs
    ):
        """
        Execute a function with memory trigger integration.
        
        Args:
            operation_name: Name of the operation
            operation_func: Function to execute
            project_name: Project name
            operation_type: Type of operation
            **kwargs: Additional arguments
        """
        if not self.service:
            # No memory triggers, execute normally
            return await operation_func(**kwargs)
        
        hooks = self.service.get_framework_hooks()
        if not hooks:
            return await operation_func(**kwargs)
        
        # Create hook context
        context = HookContext(
            operation_name=operation_name,
            project_name=project_name,
            source="cli",
            tags=["cli", operation_type]
        )
        
        success = False
        result = None
        
        try:
            # Execute function
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(**kwargs)
            else:
                result = operation_func(**kwargs)
            
            success = True
            
            # Execute completion hook
            if operation_type == "workflow":
                await hooks.workflow_completed(
                    context,
                    success=success,
                    workflow_type=operation_name,
                    result=result
                )
            elif operation_type == "agent":
                await hooks.agent_operation_completed(
                    context,
                    agent_type=operation_name,
                    success=success,
                    result=result
                )
            
            return result
            
        except Exception as e:
            success = False
            
            # Execute error hook
            await hooks.workflow_error(
                context,
                success=success,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get memory trigger status for CLI display."""
        if not self.service:
            return {"enabled": False, "status": "not_configured"}
        
        try:
            # Get service metrics
            metrics = asyncio.run(self.service.get_service_metrics())
            
            return {
                "enabled": True,
                "status": "active",
                "memory_service": metrics.get("memory_service", {}),
                "trigger_orchestrator": metrics.get("trigger_orchestrator", {}),
                "policy_engine": metrics.get("policy_engine", {}),
                "framework_hooks": metrics.get("framework_hooks", {})
            }
            
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }


# Example CLI command integration

@click.command()
@click.option('--project', default='claude-multiagent-pm', help='Project name')
@click.option('--branch', default='main', help='Git branch')
@cli_memory_trigger(operation_type="workflow", capture_result=True)
async def push_command(project: str, branch: str):
    """
    Example push command with memory trigger integration.
    """
    click.echo(f"Executing push workflow for {project} on branch {branch}")
    
    # Simulate push workflow steps
    steps = [
        "documentation_validation",
        "quality_checks", 
        "git_operations"
    ]
    
    results = {"steps": steps, "success": True}
    
    for step in steps:
        click.echo(f"  ✓ {step}")
        await asyncio.sleep(0.1)
    
    click.echo(f"✅ Push workflow completed successfully")
    return results


@click.command()
@click.option('--project', default='claude-multiagent-pm', help='Project name')
@click.option('--test-suite', default='all', help='Test suite to run')
@cli_memory_trigger(operation_type="agent", capture_result=True)
async def qa_command(project: str, test_suite: str):
    """
    Example QA command with memory trigger integration.
    """
    click.echo(f"Executing QA validation for {project} with test suite {test_suite}")
    
    # Simulate QA validation
    results = {
        "test_suite": test_suite,
        "tests_run": 42,
        "tests_passed": 40,
        "tests_failed": 2,
        "success": True
    }
    
    click.echo(f"  Tests run: {results['tests_run']}")
    click.echo(f"  Tests passed: {results['tests_passed']}")
    click.echo(f"  Tests failed: {results['tests_failed']}")
    
    await asyncio.sleep(0.2)
    
    click.echo(f"✅ QA validation completed")
    return results


@click.command()
@click.option('--project', default='claude-multiagent-pm', help='Project name')
@click.option('--environment', default='local', help='Deployment environment')
@cli_memory_trigger(operation_type="workflow", capture_result=True)
async def deploy_command(project: str, environment: str):
    """
    Example deploy command with memory trigger integration.
    """
    click.echo(f"Executing deployment for {project} to {environment}")
    
    # Simulate deployment
    steps = [
        "environment_preparation",
        "service_deployment",
        "health_validation"
    ]
    
    results = {"steps": steps, "environment": environment, "success": True}
    
    for step in steps:
        click.echo(f"  ✓ {step}")
        await asyncio.sleep(0.1)
    
    click.echo(f"✅ Deployment to {environment} completed successfully")
    return results


@click.command()
@click.pass_context
def memory_status(ctx):
    """
    Show memory trigger status.
    """
    cli_integration = MemoryIntegratedCLI()
    
    # Run async initialization
    async def get_status():
        await cli_integration.initialize()
        return cli_integration.get_memory_status()
    
    try:
        status = asyncio.run(get_status())
        
        click.echo("Memory Trigger Status:")
        click.echo(f"  Enabled: {status['enabled']}")
        click.echo(f"  Status: {status['status']}")
        
        if status['enabled'] and status['status'] == 'active':
            if 'memory_service' in status:
                click.echo(f"  Memory Service: {status['memory_service'].get('total_operations', 0)} operations")
            
            if 'framework_hooks' in status:
                hooks_stats = status['framework_hooks']
                click.echo(f"  Hooks Executed: {hooks_stats.get('hooks_executed', 0)}")
                click.echo(f"  Memory Captures: {hooks_stats.get('memory_captures', 0)}")
        
        elif status['status'] == 'error':
            click.echo(f"  Error: {status.get('error', 'Unknown error')}")
        
    except Exception as e:
        click.echo(f"Error getting memory status: {e}")


# Example CLI group with memory integration

@click.group()
def memory_cli():
    """Memory trigger CLI commands."""
    pass


# Add commands to group
memory_cli.add_command(push_command, name="push")
memory_cli.add_command(qa_command, name="qa")
memory_cli.add_command(deploy_command, name="deploy")
memory_cli.add_command(memory_status, name="status")


# Integration with existing framework CLI

def integrate_memory_triggers_with_cli(cli_app):
    """
    Integrate memory triggers with existing CLI application.
    
    Args:
        cli_app: Click CLI application
    """
    # Add memory status command
    cli_app.add_command(memory_status, name="memory-status")
    
    # Add memory CLI group
    cli_app.add_command(memory_cli, name="memory")


# Example usage in framework CLI module

def setup_memory_trigger_cli_integration():
    """
    Setup memory trigger CLI integration.
    
    This function should be called during framework CLI initialization.
    """
    logger.info("Setting up memory trigger CLI integration")
    
    # This would typically be called from the main CLI module
    # to integrate memory triggers with existing commands
    
    # Example:
    # from claude_pm.cli import cli
    # integrate_memory_triggers_with_cli(cli)


if __name__ == "__main__":
    # Example usage
    memory_cli()