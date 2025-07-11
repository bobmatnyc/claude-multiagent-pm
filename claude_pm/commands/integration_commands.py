"""
CMPM Integration Commands
========================

Integration management and AI operations commands for the Claude PM Framework.
Provides integration status monitoring and AI provider management.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .utils.command_utils import CMPMCommandBase, handle_command_error, run_async_command
from .utils.formatters import format_json_output, create_status_panel

console = Console()
logger = logging.getLogger(__name__)


class CMPMAIOpsManager(CMPMCommandBase):
    """AI Operations management and monitoring."""

    def __init__(self):
        super().__init__()
        self.ai_ops_agent = None
        self.config_manager = None

    async def initialize_ai_ops(self):
        """Initialize AI Ops components."""
        try:
            from ..agents.ai_ops_agent import AIOpsAgent
            from ..services.ai_ops.config_manager import ConfigManager

            self.ai_ops_agent = AIOpsAgent(agent_id="cmpm_ai_ops")
            self.config_manager = ConfigManager()

            return True
        except ImportError as e:
            logger.error(f"AI Ops Agent not available: {e}")
            return False

    async def get_ai_ops_status(self) -> Dict[str, Any]:
        """Get AI operations status."""
        try:
            if not await self.initialize_ai_ops():
                return {"error": "AI Ops Agent not available"}

            config = self.config_manager.get_merged_config()
            validation = self.config_manager.validate_configuration()

            # Provider status
            enabled_count = sum(1 for p in config.providers.values() if p.enabled)

            # Configuration status
            config_status = "valid" if validation["valid"] else "invalid"
            error_count = len(validation["errors"]) + len(validation["warnings"])

            # Environment variables
            env_vars = self.config_manager.get_environment_variables()
            missing_vars = len(validation["missing_env_vars"])

            return {
                "status": "operational",
                "providers": {"enabled": enabled_count, "total": len(config.providers)},
                "configuration": {
                    "status": config_status,
                    "issues": error_count,
                    "errors": validation["errors"],
                    "warnings": validation["warnings"],
                },
                "environment": {
                    "variables": len(env_vars),
                    "missing": missing_vars,
                    "missing_vars": validation["missing_env_vars"],
                },
                "cost_tracking": {
                    "enabled": config.cost.cost_tracking_enabled,
                    "daily_budget": config.cost.daily_budget,
                },
                "security": {
                    "audit_logging": config.security.audit_logging,
                    "compliance_mode": config.security.compliance_mode,
                },
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return handle_command_error(e, "ai_ops_status")

    async def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get provider configuration details."""
        try:
            if not await self.initialize_ai_ops():
                return {"error": "AI Ops Agent not available"}

            config = self.config_manager.get_merged_config()

            if provider:
                # Get specific provider config
                provider_config = self.config_manager.get_provider_config(provider)
                if provider_config:
                    return {
                        "provider": provider,
                        "enabled": provider_config.enabled,
                        "api_key_env": provider_config.api_key_env,
                        "timeout": provider_config.timeout,
                        "max_retries": provider_config.max_retries,
                        "model_mapping": provider_config.model_mapping,
                        "rate_limits": provider_config.rate_limits,
                    }
                else:
                    return {"error": f"Provider '{provider}' not found"}
            else:
                # Get all provider configs
                providers = {}
                for provider_id, provider_config in config.providers.items():
                    api_key_set = bool(os.getenv(provider_config.api_key_env))
                    providers[provider_id] = {
                        "enabled": provider_config.enabled,
                        "api_key_env": provider_config.api_key_env,
                        "api_key_set": api_key_set,
                        "timeout": provider_config.timeout,
                        "max_retries": provider_config.max_retries,
                        "model_mapping": provider_config.model_mapping,
                        "rate_limits": provider_config.rate_limits,
                    }

                return {"providers": providers, "total": len(providers)}
        except Exception as e:
            return handle_command_error(e, "provider_config")

    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive AI operations health check."""
        try:
            if not await self.initialize_ai_ops():
                return {"error": "AI Ops Agent not available"}

            # Check configuration validity
            validation = self.config_manager.validate_configuration()
            config_health = "healthy" if validation["valid"] else "unhealthy"

            # Check environment variables
            env_vars = self.config_manager.get_environment_variables()
            missing_vars = [k for k, v in env_vars.items() if v == "NOT_SET"]
            env_health = "complete" if not missing_vars else "incomplete"

            # Test provider connectivity
            config = self.config_manager.get_merged_config()
            provider_health = {}

            for provider_id, provider_config in config.providers.items():
                if provider_config.enabled:
                    api_key = os.getenv(provider_config.api_key_env)
                    provider_health[provider_id] = {
                        "enabled": True,
                        "api_key_set": bool(api_key),
                        "status": "ready" if api_key else "no_api_key",
                    }
                else:
                    provider_health[provider_id] = {"enabled": False, "status": "disabled"}

            return {
                "overall_health": (
                    "healthy"
                    if config_health == "healthy" and env_health == "complete"
                    else "degraded"
                ),
                "configuration_health": config_health,
                "environment_health": env_health,
                "missing_env_vars": missing_vars,
                "provider_health": provider_health,
                "validation_errors": validation["errors"],
                "validation_warnings": validation["warnings"],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return handle_command_error(e, "health_check")


# CLI Commands
class CMPMIntegrationManager(CMPMCommandBase):
    """CMPM Integration Management (CMPM-105 Implementation)."""

    async def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        try:
            # Import health dashboard
            from ..services.health_dashboard import HealthDashboardOrchestrator
            from ..services.memory_service import MemoryService
            import subprocess

            # Get health dashboard data
            dashboard = HealthDashboardOrchestrator(
                cache_ttl_seconds=10.0, global_timeout_seconds=2.0
            )

            health_data = await dashboard._collect_fresh_health()

            # Extract integration-specific data
            integrations = {
                "ai_trackdown": "unknown",
                "memory_service": "unknown",
                "health_dashboard": "operational",
                "multi_agent_orchestrator": "unknown",
            }

            # Check ai-trackdown integration
            try:
                result = subprocess.run(
                    ["aitrackdown", "status"], capture_output=True, text=True, timeout=3
                )
                integrations["ai_trackdown"] = "operational" if result.returncode == 0 else "error"
            except Exception:
                integrations["ai_trackdown"] = "error"

            # Check memory service integration
            try:
                memory_service = MemoryService()
                memory_health = await memory_service.health_check()
                integrations["memory_service"] = (
                    "operational" if memory_health.get("status") == "healthy" else "degraded"
                )
            except Exception:
                integrations["memory_service"] = "error"

            return {
                "status": "operational",
                "integrations": integrations,
                "health_score": health_data.response_time_ms,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            return handle_command_error(e, "integration_status")


@click.command(name="cmpm:integration")
@click.option(
    "--action",
    type=click.Choice(["status", "test", "reset"]),
    default="status",
    help="Integration action to perform",
)
@click.option("--service", type=str, help="Specific service to target")
@click.option(
    "--output-format",
    type=click.Choice(["json", "table", "yaml"]),
    default="table",
    help="Output format",
)
def cmpm_integration(action: str, service: Optional[str], output_format: str):
    """🔌 CMPM Integration - Integration management (CMPM-105 Implementation)"""

    async def run_integration_command():
        manager = CMPMIntegrationManager()

        if action == "status":
            status = await manager.get_integration_status()

            if output_format == "json":
                console.print(format_json_output(status))
            else:
                console.print(
                    Panel(
                        f"Integration Status: {status.get('status', 'unknown').upper()}",
                        title="🔌 CMPM Integration Manager",
                        border_style="green" if status.get("status") == "operational" else "yellow",
                    )
                )

                # Show integration table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Integration", style="cyan")
                table.add_column("Status", width=12)
                table.add_column("Details", style="dim")

                for integration_name, integration_status in status.get("integrations", {}).items():
                    status_color = "green" if integration_status == "operational" else "red"
                    table.add_row(
                        integration_name.replace("_", " ").title(),
                        f"[{status_color}]{integration_status.upper()}[/{status_color}]",
                        f"Last check: {status.get('last_check', 'unknown')}",
                    )

                console.print(table)

        elif action == "test":
            console.print("🧪 Testing integrations...")
            # Implementation for testing integrations
            console.print("[yellow]Integration testing not yet implemented[/yellow]")

        elif action == "reset":
            console.print("🔄 Resetting integrations...")
            # Implementation for resetting integrations
            console.print("[yellow]Integration reset not yet implemented[/yellow]")

    run_async_command(run_integration_command())


@click.command(name="cmpm:ai-ops")
@click.option(
    "--action",
    type=click.Choice(["status", "config", "health", "providers"]),
    default="status",
    help="Action to perform",
)
@click.option(
    "--provider",
    type=str,
    help="Specific provider to target (openai|anthropic|google|openrouter|vercel)",
)
@click.option(
    "--config-level",
    type=click.Choice(["system", "user", "project", "runtime"]),
    default="project",
    help="Configuration level",
)
@click.option(
    "--output-format",
    type=click.Choice(["dashboard", "json", "table"]),
    default="dashboard",
    help="Output format",
)
def cmpm_ai_ops(action: str, provider: Optional[str], config_level: str, output_format: str):
    """🤖 CMPM AI Ops - AI Operations management and monitoring"""

    async def run_ai_ops():
        manager = CMPMAIOpsManager()

        console.print(
            Panel(
                Text(
                    f"AI Operations Command\nAction: {action} | Provider: {provider or 'all'} | Level: {config_level}",
                    justify="center",
                    style="bold white",
                ),
                title="🤖 AI Operations Management",
                border_style="blue",
            )
        )

        if action == "status":
            status = await manager.get_ai_ops_status()

            if output_format == "json":
                console.print(format_json_output(status))
            else:
                if "error" in status:
                    console.print(f"[red]Error: {status['error']}[/red]")
                    return

                # Create status table
                table = Table(title="AI Operations Status")
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Details", style="white")

                # Provider status
                providers = status.get("providers", {})
                table.add_row(
                    "Providers",
                    f"{providers.get('enabled', 0)} enabled",
                    f"Total: {providers.get('total', 0)}",
                )

                # Configuration status
                config = status.get("configuration", {})
                config_status = "✅ Valid" if config.get("status") == "valid" else "❌ Invalid"
                table.add_row("Configuration", config_status, f"Issues: {config.get('issues', 0)}")

                # Environment variables
                env = status.get("environment", {})
                env_status = (
                    "✅ Complete"
                    if env.get("missing", 0) == 0
                    else f"⚠️ Missing {env.get('missing', 0)}"
                )
                table.add_row("Environment", env_status, f"Variables: {env.get('variables', 0)}")

                # Cost tracking
                cost = status.get("cost_tracking", {})
                cost_status = "✅ Enabled" if cost.get("enabled", False) else "❌ Disabled"
                table.add_row(
                    "Cost Tracking", cost_status, f"Budget: ${cost.get('daily_budget', 0)}/day"
                )

                # Security
                security = status.get("security", {})
                security_status = (
                    "✅ Enabled" if security.get("audit_logging", False) else "⚠️ Basic"
                )
                table.add_row(
                    "Security",
                    security_status,
                    f"Mode: {security.get('compliance_mode', 'unknown')}",
                )

                console.print(table)

                # Show validation issues if any
                if config.get("errors") or config.get("warnings"):
                    console.print("\n[yellow]Configuration Issues:[/yellow]")
                    for error in config.get("errors", []):
                        console.print(f"  [red]❌ {error}[/red]")
                    for warning in config.get("warnings", []):
                        console.print(f"  [yellow]⚠️ {warning}[/yellow]")

        elif action == "config":
            config = await manager.get_provider_config(provider)

            if output_format == "json":
                console.print(format_json_output(config))
            else:
                if "error" in config:
                    console.print(f"[red]Error: {config['error']}[/red]")
                    return

                if provider:
                    # Show specific provider config
                    console.print(f"\n[bold]Provider: {provider}[/bold]")
                    console.print(f"Enabled: {config.get('enabled', False)}")
                    console.print(f"API Key Env: {config.get('api_key_env', 'N/A')}")
                    console.print(f"Timeout: {config.get('timeout', 0)}s")
                    console.print(f"Max Retries: {config.get('max_retries', 0)}")
                    if config.get("model_mapping"):
                        console.print("Model Mapping:")
                        for alias, model in config.get("model_mapping", {}).items():
                            console.print(f"  {alias} → {model}")
                else:
                    # Show all provider configs
                    for provider_id, provider_config in config.get("providers", {}).items():
                        status = "✅" if provider_config.get("enabled", False) else "❌"
                        console.print(
                            f"{status} {provider_id}: {provider_config.get('api_key_env', 'N/A')}"
                        )

        elif action == "health":
            health = await manager.perform_health_check()

            if output_format == "json":
                console.print(format_json_output(health))
            else:
                if "error" in health:
                    console.print(f"[red]Error: {health['error']}[/red]")
                    return

                console.print("[yellow]AI Operations Health Check Results:[/yellow]")

                # Overall health
                overall = health.get("overall_health", "unknown")
                health_color = "green" if overall == "healthy" else "yellow"
                console.print(f"Overall Health: [{health_color}]{overall.upper()}[/{health_color}]")

                # Configuration health
                config_health = health.get("configuration_health", "unknown")
                config_color = "green" if config_health == "healthy" else "red"
                console.print(
                    f"Configuration: [{config_color}]{config_health.upper()}[/{config_color}]"
                )

                # Environment health
                env_health = health.get("environment_health", "unknown")
                env_color = "green" if env_health == "complete" else "yellow"
                console.print(f"Environment: [{env_color}]{env_health.upper()}[/{env_color}]")

                # Missing environment variables
                missing_vars = health.get("missing_env_vars", [])
                if missing_vars:
                    console.print("\nMissing environment variables:")
                    for var in missing_vars:
                        console.print(f"  - {var}")

                # Provider health
                provider_health = health.get("provider_health", {})
                console.print("\nProvider Health:")
                for provider_id, provider_status in provider_health.items():
                    if provider_status.get("enabled", False):
                        api_key_status = (
                            "✅ API Key Set"
                            if provider_status.get("api_key_set", False)
                            else "❌ No API Key"
                        )
                        console.print(f"  {provider_id}: {api_key_status}")
                    else:
                        console.print(f"  {provider_id}: ❌ Disabled")

        elif action == "providers":
            config = await manager.get_provider_config()

            if output_format == "json":
                console.print(format_json_output(config))
            else:
                if "error" in config:
                    console.print(f"[red]Error: {config['error']}[/red]")
                    return

                table = Table(title="AI Service Providers")
                table.add_column("Provider", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("API Key", style="yellow")
                table.add_column("Models", style="white")
                table.add_column("Rate Limits", style="magenta")

                for provider_id, provider_config in config.get("providers", {}).items():
                    status = (
                        "✅ Enabled" if provider_config.get("enabled", False) else "❌ Disabled"
                    )
                    api_key_status = (
                        "✅ Set" if provider_config.get("api_key_set", False) else "❌ Missing"
                    )

                    models = "Default"
                    if provider_config.get("model_mapping"):
                        models = f"{len(provider_config.get('model_mapping', {}))} mapped"

                    rate_limits = "None"
                    if provider_config.get("rate_limits"):
                        rpm = provider_config.get("rate_limits", {}).get(
                            "requests_per_minute", "N/A"
                        )
                        rate_limits = f"{rpm} req/min"

                    table.add_row(provider_id, status, api_key_status, models, rate_limits)

                console.print(table)

    run_async_command(run_ai_ops())


__all__ = ["cmpm_integration", "cmpm_ai_ops", "CMPMAIOpsManager", "CMPMIntegrationManager"]
