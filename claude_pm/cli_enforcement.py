"""
CLI commands for the Technical Enforcement Layer (FWK-003)

Provides command-line interface for enforcement system management,
violation monitoring, and framework integrity checking.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .core.enforcement import (
    get_enforcement_engine,
    enforce_file_access,
    validate_agent_action,
    AgentType,
    ViolationSeverity,
)


console = Console()


@click.group(name="enforcement")
def enforcement_cli():
    """Technical Enforcement Layer (FWK-003) commands."""
    pass


@enforcement_cli.command()
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format for status display",
)
def status(output_format: str):
    """Show enforcement system status and statistics."""
    try:
        engine = get_enforcement_engine()
        stats = engine.get_enforcement_stats()

        if output_format == "json":
            console.print(json.dumps(stats, indent=2, default=str))
            return

        # Create status panel
        status_text = "🟢 ACTIVE" if stats["enforcement_enabled"] else "🔴 INACTIVE"
        status_panel = Panel(
            f"[bold]Technical Enforcement Layer Status: {status_text}[/bold]",
            title="🔒 Framework Protection Status",
            border_style="green" if stats["enforcement_enabled"] else "red",
        )
        console.print(status_panel)

        # Create statistics table
        stats_table = Table(title="📊 Enforcement Statistics")
        stats_table.add_column("Metric", style="cyan", no_wrap=True)
        stats_table.add_column("Value", style="magenta")
        stats_table.add_column("Description", style="white")

        stats_table.add_row(
            "Total Violations", str(stats["total_violations"]), "All constraint violations detected"
        )
        stats_table.add_row(
            "Active Alerts", str(stats["active_alerts"]), "Unacknowledged violation alerts"
        )
        stats_table.add_row(
            "Critical Violations",
            str(stats["critical_violations"]),
            "High-severity framework violations",
        )
        stats_table.add_row(
            "Active Chains",
            str(stats["delegation_chains_active"]),
            "Active delegation chains being tracked",
        )

        console.print(stats_table)

        # Show recent violations if any
        if stats["recent_violations"]:
            violations_table = Table(title="⚠️ Recent Violations (Last 5)")
            violations_table.add_column("Time", style="cyan")
            violations_table.add_column("Agent", style="yellow")
            violations_table.add_column("Type", style="red")
            violations_table.add_column("Severity", style="magenta")

            for violation in stats["recent_violations"][-5:]:
                timestamp = datetime.fromisoformat(violation["timestamp"]).strftime("%H:%M:%S")
                violations_table.add_row(
                    timestamp,
                    violation["agent"],
                    violation["violation_type"],
                    violation["severity"].upper(),
                )

            console.print(violations_table)

    except Exception as e:
        console.print(f"[red]Error getting enforcement status: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
@click.argument("agent_type")
@click.argument("file_path")
@click.option(
    "--action",
    default="read",
    type=click.Choice(["read", "write", "execute"]),
    help="Action type to validate",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
def validate(agent_type: str, file_path: str, action: str, verbose: bool):
    """Validate if an agent can perform an action on a file."""
    try:
        # Validate the action
        result = validate_agent_action(agent_type, action, file_path)

        # Show result
        if result.is_valid:
            console.print(f"[green]✅ AUTHORIZED[/green]: {agent_type} can {action} {file_path}")
        else:
            console.print(f"[red]❌ BLOCKED[/red]: {agent_type} cannot {action} {file_path}")

        if verbose or not result.is_valid:
            # Show file category
            file_category = result.context.get("file_category", "unknown")
            console.print(f"[dim]File Category: {file_category}[/dim]")

            # Show violations
            if result.violations:
                console.print("\n[red]🚨 Violations:[/red]")
                for i, violation in enumerate(result.violations, 1):
                    console.print(
                        f"  {i}. [red]{violation.violation_type}[/red] ({violation.severity.value})"
                    )
                    console.print(f"     {violation.description}")
                    if violation.resolution_guidance:
                        console.print(
                            f"     [yellow]💡 Resolution: {violation.resolution_guidance}[/yellow]"
                        )
                    console.print()

            # Show warnings
            if result.warnings:
                console.print("\n[yellow]⚠️ Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")

        # Exit with error code if blocked
        if not result.is_valid:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error validating action: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
@click.option(
    "--severity",
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Filter alerts by minimum severity level",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format for alerts",
)
def alerts(severity: Optional[str], output_format: str):
    """Show active violation alerts."""
    try:
        engine = get_enforcement_engine()
        monitor = engine.violation_monitor
        alerts_list = monitor.get_violation_alerts()

        # Filter by severity if specified
        if severity:
            severity_enum = ViolationSeverity(severity)
            severity_order = {
                ViolationSeverity.LOW: 1,
                ViolationSeverity.MEDIUM: 2,
                ViolationSeverity.HIGH: 3,
                ViolationSeverity.CRITICAL: 4,
            }
            min_level = severity_order[severity_enum]
            alerts_list = [
                a for a in alerts_list if severity_order[a.violation.severity] >= min_level
            ]

        if output_format == "json":
            alerts_data = []
            for alert in alerts_list:
                alerts_data.append(
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.alert_level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "violation_type": alert.violation.violation_type,
                        "agent": str(alert.violation.agent),
                        "resource": str(alert.violation.action.resource_path),
                    }
                )
            console.print(json.dumps(alerts_data, indent=2))
            return

        if not alerts_list:
            console.print("[green]✅ No active alerts[/green]")
            return

        # Create alerts table
        alerts_table = Table(title=f"🚨 Active Violation Alerts ({len(alerts_list)})")
        alerts_table.add_column("Alert ID", style="cyan")
        alerts_table.add_column("Severity", style="red")
        alerts_table.add_column("Agent", style="yellow")
        alerts_table.add_column("Type", style="magenta")
        alerts_table.add_column("Time", style="white")
        alerts_table.add_column("Message", style="white")

        for alert in alerts_list:
            # Color code severity
            severity_colors = {
                ViolationSeverity.LOW: "green",
                ViolationSeverity.MEDIUM: "yellow",
                ViolationSeverity.HIGH: "red",
                ViolationSeverity.CRITICAL: "bold red",
            }
            severity_color = severity_colors.get(alert.violation.severity, "white")

            alerts_table.add_row(
                alert.alert_id,
                f"[{severity_color}]{alert.alert_level.value.upper()}[/{severity_color}]",
                str(alert.violation.agent),
                alert.violation.violation_type,
                alert.timestamp.strftime("%H:%M:%S"),
                alert.message[:60] + "..." if len(alert.message) > 60 else alert.message,
            )

        console.print(alerts_table)

    except Exception as e:
        console.print(f"[red]Error getting alerts: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
@click.argument("alert_id")
def acknowledge(alert_id: str):
    """Acknowledge a violation alert."""
    try:
        engine = get_enforcement_engine()
        monitor = engine.violation_monitor

        success = monitor.acknowledge_alert(alert_id)

        if success:
            console.print(f"[green]✅ Alert {alert_id} acknowledged[/green]")
        else:
            console.print(f"[red]❌ Alert {alert_id} not found[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error acknowledging alert: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
@click.option("--hours", default=24, type=int, help="Number of hours to include in report")
@click.option(
    "--format",
    "output_format",
    default="summary",
    type=click.Choice(["summary", "detailed", "json"]),
    help="Report format",
)
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
def report(hours: int, output_format: str, output: Optional[str]):
    """Generate violation report."""
    try:
        engine = get_enforcement_engine()
        monitor = engine.violation_monitor

        # Calculate time range
        end_time = datetime.now()
        start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if hours != 24:
            from datetime import timedelta

            start_time = end_time - timedelta(hours=hours)

        # Generate report
        report_obj = monitor.generate_violation_report(start_time, end_time)

        if output_format == "json":
            report_data = {
                "report_id": report_obj.report_id,
                "start_time": report_obj.start_time.isoformat(),
                "end_time": report_obj.end_time.isoformat(),
                "summary": report_obj.summary,
                "recommendations": report_obj.recommendations,
                "violations": [
                    {
                        "violation_id": v.violation_id,
                        "agent": str(v.agent),
                        "violation_type": v.violation_type,
                        "severity": v.severity.value,
                        "description": v.description,
                        "timestamp": v.timestamp.isoformat(),
                    }
                    for v in report_obj.violations
                ],
            }

            output_text = json.dumps(report_data, indent=2)

        else:
            # Create formatted report
            lines = []
            lines.append(f"🔒 TECHNICAL ENFORCEMENT REPORT")
            lines.append(f"Report ID: {report_obj.report_id}")
            lines.append(
                f"Period: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            lines.append(f"Duration: {hours} hours")
            lines.append("")

            # Summary
            lines.append("📊 SUMMARY")
            lines.append(f"Total Violations: {report_obj.summary['total_violations']}")

            if report_obj.summary["by_severity"]:
                lines.append("\nBy Severity:")
                for severity, count in report_obj.summary["by_severity"].items():
                    lines.append(f"  {severity.upper()}: {count}")

            if report_obj.summary["by_agent_type"]:
                lines.append("\nBy Agent Type:")
                for agent_type, count in report_obj.summary["by_agent_type"].items():
                    lines.append(f"  {agent_type.upper()}: {count}")

            if report_obj.summary["by_violation_type"]:
                lines.append("\nBy Violation Type:")
                for vtype, count in report_obj.summary["by_violation_type"].items():
                    lines.append(f"  {vtype}: {count}")

            # Recommendations
            if report_obj.recommendations:
                lines.append("\n💡 RECOMMENDATIONS")
                for i, rec in enumerate(report_obj.recommendations, 1):
                    lines.append(f"{i}. {rec}")

            # Detailed violations if requested
            if output_format == "detailed" and report_obj.violations:
                lines.append(f"\n🚨 VIOLATIONS DETAIL ({len(report_obj.violations)})")
                for i, violation in enumerate(report_obj.violations, 1):
                    lines.append(f"\n{i}. {violation.violation_type} ({violation.severity.value})")
                    lines.append(f"   Agent: {violation.agent}")
                    lines.append(f"   Time: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    lines.append(f"   Description: {violation.description}")
                    if violation.resolution_guidance:
                        lines.append(f"   Resolution: {violation.resolution_guidance}")

            output_text = "\n".join(lines)

        # Output to file or console
        if output:
            Path(output).write_text(output_text)
            console.print(f"[green]✅ Report saved to {output}[/green]")
        else:
            if output_format == "json":
                console.print(output_text)
            else:
                console.print(Panel(output_text, title="📋 Violation Report", border_style="blue"))

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
@click.confirmation_option(prompt="Are you sure you want to disable enforcement?")
def disable():
    """Disable enforcement system (for debugging/testing only)."""
    try:
        engine = get_enforcement_engine()
        engine.disable_enforcement()
        console.print("[yellow]⚠️ Enforcement system DISABLED[/yellow]")
        console.print("[red]WARNING: Framework protection is now inactive![/red]")

    except Exception as e:
        console.print(f"[red]Error disabling enforcement: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
def enable():
    """Enable enforcement system."""
    try:
        engine = get_enforcement_engine()
        engine.enable_enforcement()
        console.print("[green]✅ Enforcement system ENABLED[/green]")
        console.print("[green]Framework protection is now active[/green]")

    except Exception as e:
        console.print(f"[red]Error enabling enforcement: {e}[/red]")
        sys.exit(1)


@enforcement_cli.command()
def test():
    """Run enforcement system self-tests."""
    try:
        console.print("[cyan]🧪 Running enforcement system self-tests...[/cyan]")

        test_scenarios = [
            # Should pass
            ("engineer", "src/main.py", "write", True, "Engineer writing code"),
            ("qa", "tests/test_main.py", "write", True, "QA writing tests"),
            ("operations", "Dockerfile", "write", True, "Ops configuring deployment"),
            ("orchestrator", "CLAUDE.md", "write", True, "Orchestrator managing PM files"),
            # Should fail
            ("orchestrator", "src/main.py", "write", False, "Orchestrator writing code (CRITICAL)"),
            ("engineer", "CLAUDE.md", "write", False, "Engineer accessing PM files"),
            ("qa", "src/main.py", "write", False, "QA writing code"),
            ("operations", "src/main.py", "write", False, "Ops writing code"),
        ]

        passed = 0
        failed = 0

        test_table = Table(title="🧪 Enforcement Self-Tests")
        test_table.add_column("Test", style="white")
        test_table.add_column("Expected", style="cyan")
        test_table.add_column("Result", style="magenta")
        test_table.add_column("Status", style="green")

        for agent_type, file_path, action, expected, description in test_scenarios:
            result = enforce_file_access(agent_type, file_path, action)

            expected_text = "ALLOW" if expected else "BLOCK"
            result_text = "ALLOW" if result else "BLOCK"

            if result == expected:
                status = "[green]✅ PASS[/green]"
                passed += 1
            else:
                status = "[red]❌ FAIL[/red]"
                failed += 1

            test_table.add_row(description, expected_text, result_text, status)

        console.print(test_table)

        # Summary
        total = passed + failed
        if failed == 0:
            console.print(
                f"\n[green]✅ All {total} tests passed! Enforcement system is working correctly.[/green]"
            )
        else:
            console.print(
                f"\n[red]❌ {failed}/{total} tests failed! Enforcement system has issues.[/red]"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error running self-tests: {e}[/red]")
        sys.exit(1)


# For integration with main CLI
if __name__ == "__main__":
    enforcement_cli()
