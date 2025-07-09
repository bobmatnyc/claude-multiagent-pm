#!/usr/bin/env python3
"""
AI-Trackdown-Tools CLI Integration Demo for CMCP-init

This demo showcases the new CLI integration capabilities of the SystemInitAgent,
including:
1. CLI availability detection
2. Rich project data collection via CLI
3. Graceful fallback when CLI is not available
4. Cross-directory functionality
5. Enhanced project indexing

Usage:
    python examples/ai_trackdown_tools_integration_demo.py
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.agents.system_init_agent import SystemInitAgent
from claude_pm.core.config import Config
from claude_pm.utils.ai_trackdown_tools import (
    get_ai_trackdown_tools,
    create_persistent_issue,
    update_persistent_issue,
    complete_persistent_issue
)
from rich.console import Console
from rich.panel import Panel
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


async def demo_cli_integration():
    """Demonstrate AI-Trackdown-Tools CLI integration features."""
    
    console.print(Panel.fit(
        "🚀 AI-Trackdown-Tools CLI Integration Demo\n"
        "ISS-0055: Implement AI-Trackdown-Tools Project Indexing",
        style="bold blue"
    ))
    
    # 1. Demonstrate CLI availability detection
    console.print("\n📍 [bold]1. CLI Availability Detection[/bold]")
    console.print("="*50)
    
    current_dir = Path.cwd()
    agent = SystemInitAgent(working_dir=current_dir)
    
    availability = agent.check_aitrackdown_availability(current_dir)
    
    if availability["available"]:
        console.print("✅ [bold green]AI-Trackdown-Tools CLI Available![/bold green]")
        console.print(f"   • Version: {availability['version']}")
        console.print(f"   • Type: {'Local' if availability['local_cli'] else 'Global'}")
        console.print(f"   • CLI Path: {availability['cli_path']}")
        console.print(f"   • Config Path: {availability['config_path']}")
    else:
        console.print("❌ [bold red]AI-Trackdown-Tools CLI Not Available[/bold red]")
        console.print(f"   • Status: {availability['version']}")
        if availability.get("note"):
            console.print(f"   • Note: {availability['note']}")
    
    # 2. Demonstrate project data collection
    console.print("\n📊 [bold]2. Project Data Collection[/bold]")
    console.print("="*50)
    
    if availability["available"]:
        console.print("🔍 Collecting rich project data via CLI...")
        project_data = await agent.collect_project_data_via_cli(current_dir)
        
        # Display CLI data
        ai_info = project_data.get("aiTrackdownTools", {})
        console.print(f"   • CLI Version: {ai_info.get('version', 'Unknown')}")
        console.print(f"   • CLI Type: {'Local' if ai_info.get('localCli') else 'Global'}")
        
        # Display project data
        proj_data = project_data.get("projectData", {})
        if proj_data:
            console.print("   • Project Data:")
            for key, value in proj_data.items():
                if isinstance(value, dict) and not value.get("error"):
                    console.print(f"     - {key.title()}: {value.get('total', 'N/A')} total")
        
        # Display statistics
        stats = project_data.get("statistics", {})
        if stats and not stats.get("error"):
            console.print("   • Statistics:")
            for key, value in stats.items():
                console.print(f"     - {key}: {value}")
    
    else:
        console.print("🔍 Collecting basic project data (CLI fallback)...")
        project_data = agent.collect_basic_project_data(current_dir)
        
        # Display basic data
        ai_info = project_data.get("aiTrackdownTools", {})
        console.print(f"   • CLI Status: {ai_info.get('version', 'Unknown')}")
        console.print(f"   • Note: {ai_info.get('note', 'No note')}")
        
        # Display indicators
        indicators = project_data.get("projectData", {}).get("indicators", [])
        if indicators:
            console.print("   • Project Indicators:")
            for indicator in indicators:
                console.print(f"     - {indicator['file']}: {indicator['description']}")
        
        # Display basic stats
        stats = project_data.get("statistics", {})
        if stats:
            console.print("   • Basic Statistics:")
            console.print(f"     - File Count: {stats.get('fileCount', 'Unknown')}")
            console.print(f"     - Has Git: {stats.get('hasGit', False)}")
            console.print(f"     - Has package.json: {stats.get('hasPackageJson', False)}")
    
    # 3. Demonstrate enhanced project scanning
    console.print("\n🔍 [bold]3. Enhanced Project Scanning[/bold]")
    console.print("="*50)
    
    console.print("🔍 Scanning current project with CLI integration...")
    project_info = await agent._scan_current_project()
    
    if project_info:
        console.print(f"   • Project Name: {project_info.get('name', 'Unknown')}")
        console.print(f"   • Project Type: {project_info.get('type', 'Unknown')}")
        console.print(f"   • Project Path: {project_info.get('path', 'Unknown')}")
        console.print(f"   • Health Status: {project_info.get('health', 'Unknown')}")
        console.print(f"   • Last Access: {project_info.get('lastAccess', 'Unknown')}")
        
        # Show CLI integration status
        ai_info = project_info.get("aiTrackdownTools", {})
        if ai_info:
            console.print(f"   • CLI Integration: {'✅ Available' if ai_info.get('available') else '❌ Not Available'}")
    
    # 4. Demonstrate cross-directory functionality
    console.print("\n🔄 [bold]4. Cross-Directory Functionality[/bold]")
    console.print("="*50)
    
    # Create a temporary directory to demonstrate switching
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some project files
        (temp_path / ".git").mkdir()
        (temp_path / "package.json").write_text('{"name": "demo-project"}')
        (temp_path / "README.md").write_text("# Demo Project")
        
        console.print(f"🔄 Switching to temporary directory: {temp_path}")
        
        # Switch to new directory
        switch_result = await agent.switch_project_directory(temp_path)
        
        if switch_result["success"]:
            console.print("✅ Successfully switched directories!")
            console.print(f"   • Old Directory: {switch_result['old_directory']}")
            console.print(f"   • New Directory: {switch_result['new_directory']}")
            console.print(f"   • Index Updated: {switch_result['index_updated']}")
            
            # Show project data for new directory
            new_proj_data = switch_result.get("project_data", {})
            if new_proj_data:
                ai_info = new_proj_data.get("aiTrackdownTools", {})
                console.print(f"   • CLI Available: {'✅ Yes' if ai_info.get('available') else '❌ No'}")
        else:
            console.print(f"❌ Failed to switch directories: {switch_result.get('error')}")
    
    # 5. Demonstrate enhanced initialization
    console.print("\n🚀 [bold]5. Enhanced CMCP-init with CLI Integration[/bold]")
    console.print("="*50)
    
    # Show the enhanced initialization capabilities
    console.print("📋 Enhanced initialization capabilities:")
    console.print("   • CLI-aware project indexing")
    console.print("   • Rich project data collection")
    console.print("   • Graceful fallback when CLI unavailable")
    console.print("   • Cross-directory project switching")
    console.print("   • Enhanced project health monitoring")
    
    # 6. Show rich project information
    console.print("\n📈 [bold]6. Rich Project Information Display[/bold]")
    console.print("="*50)
    
    await agent.display_rich_project_information()
    
    console.print("\n🎉 [bold green]Demo completed successfully![/bold green]")
    console.print("\n📚 [bold]Key Features Demonstrated:[/bold]")
    console.print("   ✅ CLI availability detection with local/global support")
    console.print("   ✅ Rich project data collection via ai-trackdown-tools")
    console.print("   ✅ Graceful fallback to basic scanning when CLI unavailable")
    console.print("   ✅ Cross-directory functionality with project switching")
    console.print("   ✅ Enhanced project indexing with CLI data")
    console.print("   ✅ Rich project information display")
    
    console.print("\n🎯 [bold]Next Steps:[/bold]")
    console.print("   • Run 'cmcp-init --setup' to initialize with CLI integration")
    console.print("   • Use 'cmcp-init --show-index' to view project index")
    console.print("   • Use 'cmcp-init --rich-info' to display rich project information")
    console.print("   • Install ai-trackdown-tools globally for full features")


async def demo_project_types():
    """Demonstrate project type detection."""
    
    console.print(Panel.fit(
        "🔍 Project Type Detection Demo",
        style="bold cyan"
    ))
    
    agent = SystemInitAgent()
    
    # Test different project types
    test_cases = [
        ("Claude PM Framework", "claude_pm/__init__.py"),
        ("Managed Project", ".claude-multiagent-pm/"),
        ("Standalone Project", ".git/"),
        ("Unknown Project", "random_file.txt")
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for project_name, indicator in test_cases:
            # Clean directory
            for item in temp_path.iterdir():
                if item.is_dir():
                    import shutil
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            # Create indicator
            if "/" in indicator:
                # Directory
                (temp_path / indicator).mkdir(parents=True, exist_ok=True)
            else:
                # File
                (temp_path / indicator).write_text("")
            
            # Test detection
            detected_type = agent._detect_project_type(temp_path)
            
            console.print(f"📂 {project_name}")
            console.print(f"   • Indicator: {indicator}")
            console.print(f"   • Detected Type: {detected_type}")
            console.print()


async def demonstrate_legacy_features():
    """Demonstrate legacy ai-trackdown-tools features for comparison."""
    
    console.print(Panel.fit(
        "🔄 Legacy AI-Trackdown-Tools Features",
        style="bold yellow"
    ))
    
    logger.info("=== Legacy AI Trackdown Tools Integration ===")
    
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
    
    # Show how the legacy and new systems complement each other
    console.print("\n🔗 [bold]Legacy vs New CLI Integration:[/bold]")
    console.print("   • Legacy: Direct API calls for ticket creation/management")
    console.print("   • New: CLI-based project indexing and data collection")
    console.print("   • Together: Comprehensive project management with rich data")


async def main():
    """Main demo function."""
    
    try:
        await demo_cli_integration()
        console.print("\n" + "="*70 + "\n")
        await demo_project_types()
        console.print("\n" + "="*70 + "\n")
        await demonstrate_legacy_features()
        
        console.print("\n🎉 [bold green]All demos completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Demo failed: {e}[/bold red]")
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())