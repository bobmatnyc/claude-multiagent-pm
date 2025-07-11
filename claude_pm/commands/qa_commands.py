"""
CMPM QA Commands
===============

QA testing and validation commands for the Claude PM Framework.
Provides QA system monitoring, test execution, and results analysis.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..agents.enhanced_qa_agent import EnhancedQAAgent
from .utils.command_utils import CMPMCommandBase, handle_command_error, run_async_command
from .utils.formatters import format_json_output, create_status_panel

console = Console()
logger = logging.getLogger(__name__)


class CMPMQAMonitor(CMPMCommandBase):
    """CMPM QA Command Implementation with enhanced browser testing integration."""
    
    def __init__(self):
        super().__init__()
        self.qa_agent = None
    
    async def get_qa_agent(self) -> EnhancedQAAgent:
        """Get or create QA agent instance."""
        if self.qa_agent is None:
            self.qa_agent = EnhancedQAAgent(self.config)
        return self.qa_agent
    
    async def execute_qa_tests(self, test_type: str = "all", browser: bool = False, 
                              urls: List[str] = None, output_json: bool = False) -> None:
        """Execute QA tests with comprehensive reporting."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Initializing QA testing...", total=None)
            
            qa_agent = await self.get_qa_agent()
            
            if browser:
                progress.update(task, description="Executing browser-based tests...")
                test_config = {
                    "test_suite": "cmpm_browser_tests",
                    "urls": urls or ["http://localhost:3000"],
                    "scenarios": ["basic_functionality", "ui_validation"],
                    "screenshots": True,
                    "performance": True
                }
                
                results = await qa_agent.execute_browser_tests(test_config)
            else:
                progress.update(task, description=f"Running {test_type} tests...")
                results = await qa_agent.run_framework_tests(test_type)
            
            progress.update(task, description="Generating test report...")
        
        if output_json:
            # Clean results for JSON output
            clean_results = {
                "cmpm_version": "4.5.0",
                "timestamp": datetime.now().isoformat(),
                "test_type": "browser" if browser else test_type,
                "results": results
            }
            console.print(format_json_output(clean_results))
            return
        
        # Generate comprehensive dashboard
        await self._generate_qa_test_dashboard(results, test_type, browser)
    
    async def _generate_qa_test_dashboard(self, results: Dict[str, Any], test_type: str, 
                                        browser: bool) -> None:
        """Generate comprehensive QA test dashboard."""
        total_time = self.get_execution_time()
        
        # Determine status and colors
        status = results.get("status", "unknown")
        status_color = "green" if status == "success" else "yellow" if status == "partial_failure" else "red"
        
        # Create header
        test_mode = "Browser Testing" if browser else f"{test_type.title()} Testing"
        header = Panel(
            Text(f"CMPM QA Test Results - {test_mode}\nExecution Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🧪 Enhanced QA Agent Test Dashboard",
            border_style=status_color
        )
        
        console.print(header)
        console.print()
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test Category", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Results", style="dim")
        
        # Add summary row
        summary = results.get("summary", {})
        if summary:
            total_tests = summary.get("total_tests", 0)
            passed_tests = summary.get("passed_tests", 0)
            success_rate = summary.get("success_rate", 0)
            
            table.add_row(
                "Test Summary",
                f"[{status_color}]{status.upper()}[/{status_color}]",
                f"{passed_tests}/{total_tests} passed ({success_rate:.1%})"
            )
        
        # Add browser-specific results
        if browser:
            execution_summary = results.get("execution_summary", {})
            if execution_summary:
                table.add_row(
                    "Browser Tests",
                    f"[{status_color}]EXECUTED[/{status_color}]",
                    f"Screenshots: {execution_summary.get('screenshots_captured', 0)} | "
                    f"Time: {execution_summary.get('execution_time', 0):.1f}s"
                )
        
        # Add detailed results
        detailed_results = results.get("detailed_results", [])
        for result in detailed_results:
            test_name = result.get("test_type", "unknown")
            test_status = result.get("status", "unknown")
            test_color = "green" if test_status == "passed" else "red"
            
            details = ""
            if result.get("return_code") is not None:
                details += f"Exit code: {result.get('return_code')} | "
            if result.get("execution_time"):
                details += f"Time: {result.get('execution_time'):.1f}s"
            
            table.add_row(
                test_name.replace("_", " ").title(),
                f"[{test_color}]{test_status.upper()}[/{test_color}]",
                details or "No details available"
            )
        
        console.print(table)
        console.print()
        
        # Pattern analysis
        pattern_analysis = results.get("pattern_analysis", {})
        if pattern_analysis:
            pattern_text = f"""
🔍 **Pattern Analysis**: Success rate {pattern_analysis.get('success_rate', 0):.1%}
📊 **Performance**: {pattern_analysis.get('performance_trends', {}).get('average_time', 0):.1f}s average
🎯 **Recommendations**: {len(pattern_analysis.get('recommendations', []))} suggestions available
⚡ **Framework Integration**: Memory-augmented testing active
            """
            
            console.print(Panel(pattern_text.strip(), title="QA Intelligence", border_style="blue"))
            
            # Show recommendations
            recommendations = pattern_analysis.get("recommendations", [])
            if recommendations:
                console.print()
                console.print("[bold yellow]Recommendations:[/bold yellow]")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"  {i}. {rec}")
    
    async def get_qa_status(self, output_json: bool = False) -> None:
        """Get comprehensive QA system status."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Checking QA system status...", total=None)
            
            qa_agent = await self.get_qa_agent()
            status = await qa_agent.get_qa_health_status()
            
            progress.update(task, description="Generating status dashboard...")
        
        if output_json:
            clean_status = {
                "cmpm_version": "4.5.0",
                "timestamp": datetime.now().isoformat(),
                "qa_status": status
            }
            console.print(format_json_output(clean_status))
            return
        
        # Generate status dashboard
        await self._generate_qa_status_dashboard(status)
    
    async def _generate_qa_status_dashboard(self, status: Dict[str, Any]) -> None:
        """Generate QA status dashboard."""
        total_time = self.get_execution_time()
        
        # Determine overall status
        overall_status = status.get("status", "unknown")
        health_score = status.get("health_score", 0)
        status_color = "green" if overall_status == "healthy" else "yellow" if overall_status == "degraded" else "red"
        
        # Create header
        header = Panel(
            Text(f"CMPM QA System Status\nHealth Score: {health_score:.1f}%\nResponse Time: {total_time:.2f}s", 
                 justify="center", style="bold white"),
            title="🔧 Enhanced QA Agent Status",
            border_style=status_color
        )
        
        console.print(header)
        console.print()
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Details", style="dim")
        
        # Add extension health
        extension_health = status.get("extension_health", {})
        ext_status = extension_health.get("status", "unknown")
        ext_color = "green" if ext_status == "healthy" else "red"
        table.add_row(
            "Browser Extension",
            f"[{ext_color}]{ext_status.upper()}[/{ext_color}]",
            f"v{extension_health.get('extension_version', 'unknown')} | "
            f"Browsers: {', '.join(extension_health.get('connected_browsers', []))}"
        )
        
        # Add memory health
        memory_health = status.get("memory_health", {})
        mem_status = memory_health.get("status", "unknown")
        mem_color = "green" if mem_status == "healthy" else "red"
        table.add_row(
            "Memory Service",
            f"[{mem_color}]{mem_status.upper()}[/{mem_color}]",
            f"mem0AI: {'✓' if memory_health.get('mem0ai_connected') else '✗'} | "
            f"Response: {memory_health.get('response_time', 0)}ms"
        )
        
        # Add framework health
        framework_health = status.get("framework_health", {})
        framework_status = "healthy" if framework_health.get("test_commands_available") else "degraded"
        framework_color = "green" if framework_status == "healthy" else "yellow"
        table.add_row(
            "Framework Testing",
            f"[{framework_color}]{framework_status.upper()}[/{framework_color}]",
            f"Commands: {'✓' if framework_health.get('test_commands_available') else '✗'} | "
            f"Timeout: {framework_health.get('test_timeout_configured', False)}"
        )
        
        console.print(table)
        console.print()
        
        # System summary
        agent_version = status.get("agent_version", "unknown")
        capabilities = extension_health.get("test_capabilities", [])
        
        summary_text = f"""
🧪 **QA Agent Version**: Enhanced QA Agent v{agent_version}
🔗 **Browser Integration**: Extension capabilities: {', '.join(capabilities)}
🧠 **Memory Integration**: Pattern recognition and test intelligence active
⚡ **Performance**: {total_time:.2f}s status check | {health_score:.1f}% system health
        """
        
        console.print(Panel(summary_text.strip(), title="QA System Summary", border_style="blue"))
    
    async def get_qa_results(self, output_format: str = "dashboard", limit: int = 10) -> None:
        """Get QA test results with memory-augmented analysis."""
        try:
            # In a real implementation, this would retrieve from memory service
            # For now, we'll show a placeholder dashboard
            
            if output_format == "json":
                results = {
                    "cmpm_version": "4.5.0",
                    "timestamp": datetime.now().isoformat(),
                    "results_available": False,
                    "message": "Results retrieval from memory service not yet implemented",
                    "limit": limit
                }
                console.print(format_json_output(results))
                return
            
            # Generate results dashboard
            header = Panel(
                Text(f"QA Results Dashboard\nFormat: {output_format} | Limit: {limit}", 
                     justify="center", style="bold white"),
                title="📊 Test Results & Patterns",
                border_style="cyan"
            )
            
            console.print(header)
            console.print()
            
            # Show placeholder content
            console.print("[dim]Recent test results would be displayed here.[/dim]")
            console.print("[dim]Memory-augmented pattern analysis would show trends and recommendations.[/dim]")
            console.print()
            console.print("[yellow]Note: This is a placeholder implementation. Full results retrieval")
            console.print("from memory service will be available in the complete implementation.[/yellow]")
            
        except Exception as e:
            error_response = handle_command_error(e, "qa_results")
            console.print(f"[red]Error retrieving QA results: {error_response['error']}[/red]")


# CLI Commands
@click.command(name="cmpm:qa-status")
@click.option("--output-json", is_flag=True, help="Output QA status as JSON")
def cmpm_qa_status(output_json: bool):
    """🔧 CMPM QA Status - QA extension status and health monitoring"""
    
    async def run_qa_status_check():
        monitor = CMPMQAMonitor()
        await monitor.get_qa_status(output_json=output_json)
    
    run_async_command(run_qa_status_check())


@click.command(name="cmpm:qa-test")
@click.option("--type", "test_type", default="all", help="Test type (all|unit|lint|framework)")
@click.option("--browser", is_flag=True, help="Execute browser-based tests")
@click.option("--urls", multiple=True, help="URLs to test (for browser tests)")
@click.option("--output-json", is_flag=True, help="Output test results as JSON")
def cmpm_qa_test(test_type: str, browser: bool, urls: Tuple[str, ...], output_json: bool):
    """🧪 CMPM QA Test - Execute browser-based tests and framework validation"""
    
    async def run_qa_tests():
        monitor = CMPMQAMonitor()
        url_list = list(urls) if urls else None
        await monitor.execute_qa_tests(
            test_type=test_type,
            browser=browser,
            urls=url_list,
            output_json=output_json
        )
    
    run_async_command(run_qa_tests())


@click.command(name="cmpm:qa-results")
@click.option("--format", "output_format", default="dashboard", help="Output format (dashboard|json|report)")
@click.option("--limit", type=int, default=10, help="Limit number of results to show")
def cmpm_qa_results(output_format: str, limit: int):
    """📊 CMPM QA Results - View test results and patterns with memory-augmented analysis"""
    
    async def run_qa_results():
        monitor = CMPMQAMonitor()
        await monitor.get_qa_results(output_format=output_format, limit=limit)
    
    run_async_command(run_qa_results())


__all__ = [
    'cmpm_qa_status',
    'cmpm_qa_test',
    'cmpm_qa_results',
    'CMPMQAMonitor'
]