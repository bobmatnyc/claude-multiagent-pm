"""
Health Commands - CLI commands for framework health monitoring and diagnostics

This module provides CLI commands for:
- Framework health checks
- Service status monitoring
- System diagnostics
- Performance monitoring

Created: 2025-07-16 (Emergency restoration)
Purpose: Restore missing claude_pm.commands.health_commands import
"""

import click
import asyncio
import json
from typing import Dict, Any

from claude_pm.core.unified_core_service import get_unified_core_service, validate_core_system
from claude_pm.services.health_monitor import HealthMonitor
from claude_pm.services.performance_monitor import PerformanceMonitor

@click.group()
def health():
    """Framework health monitoring and diagnostics commands"""
    pass

@health.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed health information')
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def check(detailed, json_output):
    """Perform comprehensive framework health check"""
    
    async def _health_check():
        try:
            # Get unified core service
            core_service = await get_unified_core_service()
            
            # Perform validation
            validation_results = await validate_core_system()
            
            if json_output:
                click.echo(json.dumps(validation_results, indent=2))
                return
            
            # Format output
            overall_status = validation_results.get('overall_status', 'unknown')
            
            if overall_status == 'valid':
                click.echo(click.style("✅ Framework health: HEALTHY", fg='green'))
            elif overall_status == 'warning':
                click.echo(click.style("⚠️  Framework health: WARNING", fg='yellow'))
            else:
                click.echo(click.style("❌ Framework health: ERROR", fg='red'))
            
            if detailed:
                # Show service validation
                click.echo("\n📋 Service Validation:")
                for service, status in validation_results.get('service_validation', {}).items():
                    if isinstance(status, str) and 'error' in status:
                        click.echo(f"  ❌ {service}: {status}")
                    else:
                        click.echo(f"  ✅ {service}: operational")
                
                # Show agent discovery
                agent_discovery = validation_results.get('agent_discovery', {})
                if agent_discovery.get('status') == 'success':
                    click.echo(f"\n🤖 Agent Discovery:")
                    click.echo(f"  Discovered: {agent_discovery.get('discovered_agents', 0)} agents")
                    click.echo(f"  Validated: {agent_discovery.get('validated_agents', 0)} agents")
                    click.echo(f"  Types: {agent_discovery.get('agent_types', 0)} types")
                
                # Show errors
                errors = validation_results.get('errors', [])
                if errors:
                    click.echo(f"\n🚨 Errors ({len(errors)}):")
                    for error in errors:
                        click.echo(f"  • {error}")
        
        except Exception as e:
            if json_output:
                click.echo(json.dumps({'error': str(e)}, indent=2))
            else:
                click.echo(click.style(f"❌ Health check failed: {e}", fg='red'))
    
    # Run async function
    asyncio.run(_health_check())

@health.command()
@click.option('--json-output', '-j', is_flag=True, help='Output in JSON format')
def status(json_output):
    """Show current system status"""
    
    async def _status_check():
        try:
            core_service = await get_unified_core_service()
            status_info = await core_service.get_system_status()
            
            if json_output:
                click.echo(json.dumps(status_info, indent=2))
                return
            
            # Format status output
            overall_status = status_info.get('status', 'unknown')
            
            click.echo(f"🖥️  System Status: {overall_status.upper()}")
            click.echo(f"🔧 Initialized: {status_info.get('initialized', False)}")
            
            # Show services
            services = status_info.get('services', {})
            if services:
                click.echo(f"\n📦 Services ({len(services)}):")
                for service_name, service_status in services.items():
                    if isinstance(service_status, str) and 'error' in service_status:
                        click.echo(f"  ❌ {service_name}: {service_status}")
                    else:
                        click.echo(f"  ✅ {service_name}: operational")
            
            # Show agent registry
            agent_registry = status_info.get('agent_registry', {})
            if agent_registry and 'total_agents' in agent_registry:
                click.echo(f"\n🤖 Agent Registry:")
                click.echo(f"  Total agents: {agent_registry.get('total_agents', 0)}")
                click.echo(f"  Validated: {agent_registry.get('validated_agents', 0)}")
                click.echo(f"  Failed: {agent_registry.get('failed_agents', 0)}")
        
        except Exception as e:
            if json_output:
                click.echo(json.dumps({'error': str(e)}, indent=2))
            else:
                click.echo(click.style(f"❌ Status check failed: {e}", fg='red'))
    
    asyncio.run(_status_check())

@health.command()
@click.option('--watch', '-w', is_flag=True, help='Watch performance metrics continuously')
@click.option('--interval', '-i', default=5, help='Watch interval in seconds')
def performance(watch, interval):
    """Show performance metrics"""
    
    async def _performance_check():
        try:
            perf_monitor = PerformanceMonitor()
            await perf_monitor.initialize()
            
            if watch:
                click.echo("📊 Performance monitoring (Press Ctrl+C to stop)")
                try:
                    while True:
                        metrics = await perf_monitor.get_current_metrics()
                        
                        # Clear screen and show metrics
                        click.clear()
                        click.echo("📊 Performance Metrics:")
                        
                        for metric_name, metric_value in metrics.items():
                            if isinstance(metric_value, (int, float)):
                                click.echo(f"  {metric_name}: {metric_value:.2f}")
                            else:
                                click.echo(f"  {metric_name}: {metric_value}")
                        
                        await asyncio.sleep(interval)
                
                except KeyboardInterrupt:
                    click.echo("\n👋 Performance monitoring stopped")
            else:
                metrics = await perf_monitor.get_current_metrics()
                
                click.echo("📊 Performance Metrics:")
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        click.echo(f"  {metric_name}: {metric_value:.2f}")
                    else:
                        click.echo(f"  {metric_name}: {metric_value}")
        
        except Exception as e:
            click.echo(click.style(f"❌ Performance check failed: {e}", fg='red'))
    
    asyncio.run(_performance_check())

@health.command()
@click.option('--force', '-f', is_flag=True, help='Force agent rediscovery')
def agents(force):
    """Show agent registry status"""
    
    async def _agents_check():
        try:
            core_service = await get_unified_core_service()
            agent_registry = await core_service.get_agent_registry()
            
            # Discover agents
            agents = await agent_registry.discover_agents(force_refresh=force)
            
            click.echo(f"🤖 Agent Registry Status:")
            click.echo(f"  Total agents: {len(agents)}")
            
            # Group by tier
            by_tier = {}
            by_type = {}
            validated_count = 0
            
            for agent_name, metadata in agents.items():
                # Count by tier
                tier = metadata.tier
                by_tier[tier] = by_tier.get(tier, 0) + 1
                
                # Count by type
                agent_type = metadata.type
                by_type[agent_type] = by_type.get(agent_type, 0) + 1
                
                # Count validated
                if metadata.validated:
                    validated_count += 1
            
            click.echo(f"  Validated: {validated_count}")
            click.echo(f"  Failed: {len(agents) - validated_count}")
            
            # Show distribution by tier
            if by_tier:
                click.echo(f"\n📂 By Tier:")
                for tier, count in by_tier.items():
                    click.echo(f"  {tier}: {count}")
            
            # Show distribution by type
            if by_type:
                click.echo(f"\n🏷️  By Type:")
                for agent_type, count in sorted(by_type.items()):
                    click.echo(f"  {agent_type}: {count}")
        
        except Exception as e:
            click.echo(click.style(f"❌ Agent check failed: {e}", fg='red'))
    
    asyncio.run(_agents_check())

@health.command()
def monitor():
    """Start interactive health monitoring dashboard"""
    
    async def _monitor():
        try:
            health_monitor = HealthMonitor()
            await health_monitor.initialize()
            await health_monitor.start_monitoring()
            
            click.echo("🖥️  Health monitoring started (Press Ctrl+C to stop)")
            
            try:
                while True:
                    health_status = await health_monitor.get_health_status()
                    
                    # Clear screen and show dashboard
                    click.clear()
                    click.echo("🖥️  Framework Health Dashboard")
                    click.echo("=" * 40)
                    
                    # Show overall status
                    overall_status = health_status.get('status', 'unknown')
                    if overall_status == 'healthy':
                        click.echo(click.style("Status: HEALTHY ✅", fg='green'))
                    elif overall_status == 'warning':
                        click.echo(click.style("Status: WARNING ⚠️", fg='yellow'))
                    else:
                        click.echo(click.style("Status: ERROR ❌", fg='red'))
                    
                    # Show components
                    components = health_status.get('components', {})
                    if components:
                        click.echo("\nComponents:")
                        for component, status in components.items():
                            status_emoji = "✅" if status == "healthy" else "❌"
                            click.echo(f"  {component}: {status} {status_emoji}")
                    
                    # Show last check time
                    last_check = health_status.get('last_check')
                    if last_check:
                        click.echo(f"\nLast check: {last_check}")
                    
                    await asyncio.sleep(5)
            
            except KeyboardInterrupt:
                click.echo("\n👋 Health monitoring stopped")
                await health_monitor.stop_monitoring()
        
        except Exception as e:
            click.echo(click.style(f"❌ Health monitoring failed: {e}", fg='red'))
    
    asyncio.run(_monitor())

# Export the health commands group for CLI integration
health_commands = health

# Add the group to CLI
if __name__ == '__main__':
    health()