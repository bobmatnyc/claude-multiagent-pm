#!/usr/bin/env python3
"""
Deployment Enforcement - ISS-0112 Claude PM Transformation

Mandatory deployment checking system that ensures framework is properly
deployed before any claude-pm operations are allowed to proceed.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .logging_config import get_logger
from ..services.framework_deployment_validator import FrameworkDeploymentValidator, DeploymentValidationResult

logger = get_logger(__name__)
console = Console()


class DeploymentEnforcementError(Exception):
    """Raised when deployment validation fails and operation cannot proceed."""
    pass


class DeploymentEnforcer:
    """
    Enforces mandatory framework deployment requirements.
    
    Validates framework deployment before allowing operations and provides
    clear guidance for resolving deployment issues.
    """
    
    def __init__(self):
        self.validator = FrameworkDeploymentValidator()
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    async def enforce_deployment_requirement(self, 
                                           working_directory: Optional[Path] = None,
                                           operation_name: str = "operation",
                                           bypass_cache: bool = False) -> DeploymentValidationResult:
        """
        Enforce deployment requirement for an operation.
        
        Args:
            working_directory: Working directory to validate
            operation_name: Name of operation being performed
            bypass_cache: Whether to bypass validation cache
            
        Returns:
            DeploymentValidationResult if validation passes
            
        Raises:
            DeploymentEnforcementError: If validation fails
        """
        logger.info(f"Enforcing deployment requirement for operation: {operation_name}")
        
        try:
            # Check cache if not bypassing
            cache_key = str(working_directory) if working_directory else "default"
            if not bypass_cache and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if self._is_cache_valid(cached_result):
                    logger.debug("Using cached validation result")
                    result = cached_result['result']
                    if not result.is_valid:
                        self._handle_deployment_failure(result, operation_name)
                    return result
            
            # Perform validation
            result = await self.validator.validate_deployment(working_directory)
            
            # Cache the result
            self._cache[cache_key] = {
                'result': result,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # Handle validation failure
            if not result.is_valid:
                self._handle_deployment_failure(result, operation_name)
            
            logger.info("Deployment requirement validation passed")
            return result
            
        except DeploymentEnforcementError:
            raise
        except Exception as e:
            logger.error(f"Deployment enforcement failed: {e}")
            raise DeploymentEnforcementError(f"Failed to validate deployment: {e}")
    
    def _is_cache_valid(self, cached_entry: Dict[str, Any]) -> bool:
        """Check if cached validation result is still valid."""
        current_time = asyncio.get_event_loop().time()
        return (current_time - cached_entry['timestamp']) < self._cache_timeout
    
    def _handle_deployment_failure(self, result: DeploymentValidationResult, operation_name: str):
        """Handle deployment validation failure with user guidance."""
        logger.error(f"Deployment validation failed for operation: {operation_name}")
        
        # Display comprehensive error message
        self._display_deployment_error(result, operation_name)
        
        # Raise enforcement error
        error_message = result.error_message or "Framework deployment validation failed"
        raise DeploymentEnforcementError(error_message)
    
    def _display_deployment_error(self, result: DeploymentValidationResult, operation_name: str):
        """Display comprehensive deployment error with actionable guidance."""
        console.print()
        
        # Main error panel
        error_panel = Panel(
            f"❌ [bold red]Claude PM Framework Deployment Required[/bold red]\n\n"
            f"Operation '[cyan]{operation_name}[/cyan]' cannot proceed without proper framework deployment.\n\n"
            f"[yellow]Issue:[/yellow] {result.error_message or 'Framework not properly deployed'}",
            title="🚫 Deployment Validation Failed",
            border_style="red",
            padding=(1, 2)
        )
        console.print(error_panel)
        
        # Validation details table
        if result.validation_details:
            console.print("\n📊 [bold]Validation Details:[/bold]")
            
            details_table = Table(show_header=True, header_style="bold magenta")
            details_table.add_column("Component", style="cyan")
            details_table.add_column("Status", style="yellow")
            
            details_table.add_row(
                "NPM Installation", 
                "✅ Found" if result.npm_installation_found else "❌ Missing"
            )
            details_table.add_row(
                "Framework Deployed",
                "✅ Yes" if result.framework_deployed else "❌ No"
            )
            details_table.add_row(
                "Working Directory",
                "✅ Configured" if result.working_directory_configured else "❌ Not Configured"
            )
            
            console.print(details_table)
        
        # Actionable guidance
        if result.actionable_guidance:
            console.print("\n🚀 [bold green]Quick Fix Instructions:[/bold green]")
            guidance_panel = Panel(
                "\n".join(result.actionable_guidance),
                title="💡 Solutions",
                border_style="green",
                padding=(1, 2)
            )
            console.print(guidance_panel)
        
        # Additional help
        console.print("\n🆘 [bold]Need More Help?[/bold]")
        console.print("   • Run '[cyan]claude-pm diagnose[/cyan]' for detailed diagnostics")
        console.print("   • Run '[cyan]claude-pm deploy --help[/cyan]' for deployment options")
        console.print("   • Visit: [link]https://github.com/bobmatnyc/claude-multiagent-pm[/link]")
        console.print()
    
    async def check_deployment_status(self, working_directory: Optional[Path] = None) -> Dict[str, Any]:
        """Check deployment status without enforcement."""
        try:
            result = await self.validator.validate_deployment(working_directory)
            return {
                'valid': result.is_valid,
                'npm_installation': result.npm_installation_found,
                'framework_deployed': result.framework_deployed,
                'working_directory_configured': result.working_directory_configured,
                'claude_pm_directory': str(result.claude_pm_directory) if result.claude_pm_directory else None,
                'validation_details': result.validation_details
            }
        except Exception as e:
            logger.error(f"Failed to check deployment status: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear validation cache."""
        self._cache.clear()
        logger.debug("Deployment validation cache cleared")


# Global enforcer instance
_enforcer = None


def get_deployment_enforcer() -> DeploymentEnforcer:
    """Get global deployment enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = DeploymentEnforcer()
    return _enforcer


def require_deployment(operation_name: Optional[str] = None,
                      working_directory: Optional[Path] = None,
                      bypass_cache: bool = False):
    """
    Decorator to enforce deployment requirement for CLI commands.
    
    Args:
        operation_name: Name of operation (defaults to function name)
        working_directory: Working directory to validate
        bypass_cache: Whether to bypass validation cache
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine operation name
            op_name = operation_name or func.__name__
            
            # Run enforcement
            try:
                enforcer = get_deployment_enforcer()
                
                # For async functions
                if asyncio.iscoroutinefunction(func):
                    async def async_wrapper():
                        await enforcer.enforce_deployment_requirement(
                            working_directory=working_directory,
                            operation_name=op_name,
                            bypass_cache=bypass_cache
                        )
                        return await func(*args, **kwargs)
                    return asyncio.run(async_wrapper())
                else:
                    # For sync functions
                    async def sync_wrapper():
                        await enforcer.enforce_deployment_requirement(
                            working_directory=working_directory,
                            operation_name=op_name,
                            bypass_cache=bypass_cache
                        )
                        return func(*args, **kwargs)
                    return asyncio.run(sync_wrapper())
                    
            except DeploymentEnforcementError:
                # Exit with error code for CLI
                sys.exit(1)
            except Exception as e:
                logger.error(f"Deployment enforcement error: {e}")
                console.print(f"❌ [red]Failed to validate deployment: {e}[/red]")
                sys.exit(1)
        
        return wrapper
    return decorator


def require_deployment_async(operation_name: Optional[str] = None,
                           working_directory: Optional[Path] = None,
                           bypass_cache: bool = False):
    """
    Async decorator to enforce deployment requirement for async CLI commands.
    
    Args:
        operation_name: Name of operation (defaults to function name)
        working_directory: Working directory to validate
        bypass_cache: Whether to bypass validation cache
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine operation name
            op_name = operation_name or func.__name__
            
            try:
                enforcer = get_deployment_enforcer()
                await enforcer.enforce_deployment_requirement(
                    working_directory=working_directory,
                    operation_name=op_name,
                    bypass_cache=bypass_cache
                )
                return await func(*args, **kwargs)
                
            except DeploymentEnforcementError:
                # Exit with error code for CLI
                sys.exit(1)
            except Exception as e:
                logger.error(f"Deployment enforcement error: {e}")
                console.print(f"❌ [red]Failed to validate deployment: {e}[/red]")
                sys.exit(1)
        
        return wrapper
    return decorator


async def validate_deployment_for_cli(working_directory: Optional[Path] = None) -> bool:
    """
    Validate deployment for CLI operations.
    
    Returns True if valid, exits with error if invalid.
    """
    try:
        enforcer = get_deployment_enforcer()
        await enforcer.enforce_deployment_requirement(
            working_directory=working_directory,
            operation_name="CLI operation"
        )
        return True
    except DeploymentEnforcementError:
        sys.exit(1)
    except Exception as e:
        logger.error(f"CLI deployment validation error: {e}")
        console.print(f"❌ [red]Failed to validate deployment: {e}[/red]")
        sys.exit(1)


def deployment_status_summary() -> str:
    """Get deployment status summary for CLI display."""
    try:
        enforcer = get_deployment_enforcer()
        status = asyncio.run(enforcer.check_deployment_status())
        
        if status['valid']:
            return "✅ Framework properly deployed"
        else:
            components = []
            if not status.get('npm_installation'):
                components.append("NPM installation")
            if not status.get('framework_deployed'):
                components.append("Framework deployment")
            if not status.get('working_directory_configured'):
                components.append("Working directory configuration")
            
            return f"❌ Missing: {', '.join(components)}"
            
    except Exception as e:
        return f"❌ Status check failed: {e}"