#!/usr/bin/env python3
"""
Installation State Detection Module - Claude Multi-Agent PM Framework

Provides intelligent detection of framework installation state and auto-initialization
capabilities for claude-pm init command.
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from ..core.logging_config import setup_streaming_logger, finalize_streaming_logs


@dataclass
class InstallationState:
    """Represents the current installation state of the framework."""
    
    is_complete: bool = False
    needs_post_install: bool = True
    framework_deployed: bool = False
    memory_system_configured: bool = False
    config_valid: bool = False
    components_deployed: bool = False
    
    missing_components: List[str] = None
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.missing_components is None:
            self.missing_components = []
        if self.validation_errors is None:
            self.validation_errors = []


class InstallationStateDetector:
    """Detects and validates Claude PM Framework installation state."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.user_home = Path.home()
        self.global_config_dir = self.user_home / ".claude-pm"
        
        # Required components for complete installation
        self.required_components = {
            "config": self.global_config_dir / "config.json",
            "framework": self.global_config_dir / "framework",
            "scripts": self.global_config_dir / "scripts",
            "templates": self.global_config_dir / "templates",
            "agents": self.global_config_dir / "agents",
            "cli": self.global_config_dir / "cli",
            "bin": self.global_config_dir / "bin"
        }
        
        # Memory system indicators
        self.memory_indicators = [
            self.global_config_dir / "memory",
            self.user_home / ".mem0",
            self.global_config_dir / "config" / "memory.json"
        ]
    
    async def detect_installation_state(self) -> InstallationState:
        """
        Detect the current installation state of the framework.
        
        Returns:
            InstallationState: Current state with detailed information
        """
        # Setup streaming logger for installation detection
        logger = setup_streaming_logger("installation_detector")
        
        try:
            state = InstallationState()
            
            logger.info("🔍 Detecting framework installation state...")
            
            # Check if global config directory exists
            logger.info("📁 Checking global configuration directory...")
            if not self.global_config_dir.exists():
                state.needs_post_install = True
                state.missing_components.append("global_config_directory")
                finalize_streaming_logs(logger)
                return state
            
            # Check required components
            logger.info("🔧 Validating required components...")
            missing_components = []
            for component, path in self.required_components.items():
                if not path.exists():
                    missing_components.append(component)
            
            state.missing_components = missing_components
            state.components_deployed = len(missing_components) == 0
            
            # Check config validity
            logger.info("⚙️  Validating configuration files...")
            state.config_valid = await self._validate_config()
            
            # Check memory system
            logger.info("🧠 Checking memory system configuration...")
            state.memory_system_configured = await self._check_memory_system()
            
            # Check framework deployment
            logger.info("🚀 Checking framework deployment status...")
            state.framework_deployed = await self._check_framework_deployment()
            
            # Determine if post-install is needed
            logger.info("📋 Evaluating installation requirements...")
            state.needs_post_install = (
                len(missing_components) > 0 or 
                not state.config_valid or 
                not state.framework_deployed
            )
            
            # Overall completion status
            state.is_complete = (
                state.components_deployed and 
                state.config_valid and 
                state.framework_deployed
            )
            
            # Final status message
            if state.is_complete:
                logger.info("✅ Framework installation state detection complete")
            else:
                logger.info("⚠️ Framework installation issues detected")
                
            # Finalize streaming output
            finalize_streaming_logs(logger)
            
            return state
            
        except Exception as e:
            # Ensure we finalize streaming on errors
            finalize_streaming_logs(logger)
            logger.error(f"Installation state detection failed: {e}")
            raise
    
    async def _validate_config(self) -> bool:
        """Validate the main configuration file."""
        try:
            config_path = self.global_config_dir / "config.json"
            if not config_path.exists():
                return False
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required config keys
            required_keys = ["installType", "version", "installationComplete"]
            for key in required_keys:
                if key not in config:
                    return False
            
            # Check that installation is marked complete
            return config.get("installationComplete", False)
            
        except (json.JSONDecodeError, OSError) as e:
            return False
    
    async def _check_memory_system(self) -> bool:
        """Check if memory system is properly configured."""
        try:
            # Check for memory directories
            for indicator in self.memory_indicators:
                if indicator.exists():
                    return True
            
            # Check if mem0AI is available
            try:
                result = subprocess.run(
                    ["python3", "-c", "import mem0; print('available')"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return False
            
        except Exception:
            return False
    
    async def _check_framework_deployment(self) -> bool:
        """Check if framework is properly deployed."""
        try:
            # Check for framework initialization marker
            init_marker = self.global_config_dir / "framework_init.json"
            if init_marker.exists():
                with open(init_marker, 'r') as f:
                    marker_data = json.load(f)
                    return marker_data.get("initialized", False)
            
            # Check for CLAUDE.md template
            claude_md = self.global_config_dir / "framework" / "CLAUDE.md"
            if claude_md.exists():
                return True
                
            return False
            
        except Exception:
            return False
    
    async def run_post_install_setup(self, force: bool = False) -> bool:
        """
        Run post-install setup automatically.
        
        Args:
            force: Force re-installation even if already set up
            
        Returns:
            bool: True if setup was successful
        """
        self.console.print("[yellow]⚠️  Framework setup incomplete - running post-install setup...[/yellow]")
        
        # Find postinstall script
        postinstall_paths = [
            Path(__file__).parent.parent.parent / "install" / "postinstall.js",
            Path(__file__).parent.parent.parent / "install" / "postinstall-enhanced.js"
        ]
        
        for postinstall_path in postinstall_paths:
            if postinstall_path.exists():
                self.console.print(f"[dim]✅ Found postinstall script: {postinstall_path}[/dim]")
                self.console.print("[dim]🚀 Executing post-install setup...[/dim]")
                
                try:
                    # Run the postinstall script
                    result = subprocess.run(
                        ["node", str(postinstall_path)],
                        cwd=str(postinstall_path.parent.parent),
                        capture_output=True,
                        text=True,
                        timeout=120  # 2 minutes timeout
                    )
                    
                    if result.returncode == 0:
                        self.console.print("[green]✅ Post-install setup completed successfully![/green]")
                        return True
                    else:
                        self.console.print(f"[red]❌ Post-install setup failed[/red]")
                        if result.stderr:
                            self.console.print(f"[red]   Error: {result.stderr}[/red]")
                        return False
                        
                except subprocess.TimeoutExpired:
                    self.console.print("[red]❌ Post-install setup timed out[/red]")
                    return False
                except Exception as e:
                    self.console.print(f"[red]❌ Post-install setup error: {e}[/red]")
                    return False
        
        self.console.print("[red]❌ No postinstall script found[/red]")
        return False
    
    def display_installation_state(self, state: InstallationState) -> None:
        """Display detailed installation state information."""
        
        if state.is_complete:
            status_color = "green"
            status_text = "✅ Complete"
        elif state.needs_post_install:
            status_color = "yellow"
            status_text = "⚠️ Needs Post-Install"
        else:
            status_color = "red"
            status_text = "❌ Incomplete"
        
        panel_content = f"""
[bold]Installation Status:[/bold] [{status_color}]{status_text}[/{status_color}]
[bold]Framework Deployed:[/bold] {"✅" if state.framework_deployed else "❌"}
[bold]Components Deployed:[/bold] {"✅" if state.components_deployed else "❌"}
[bold]Config Valid:[/bold] {"✅" if state.config_valid else "❌"}
[bold]Memory System:[/bold] {"✅" if state.memory_system_configured else "❌"}
"""
        
        if state.missing_components:
            panel_content += f"""
[bold]Missing Components:[/bold] {', '.join(state.missing_components)}
"""
        
        if state.validation_errors:
            panel_content += f"""
[bold]Validation Errors:[/bold]
{chr(10).join(f"  • {error}" for error in state.validation_errors)}
"""
        
        self.console.print(Panel(panel_content.strip(), title="Claude PM Framework Installation State"))
    
    async def validate_installation(self) -> Tuple[bool, List[str]]:
        """
        Validate the installation and return detailed results.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, validation_messages)
        """
        state = await self.detect_installation_state()
        messages = []
        
        if state.is_complete:
            messages.append("✅ Framework installation is complete and valid")
            return True, messages
        
        if state.needs_post_install:
            messages.append("⚠️ Framework needs post-install setup")
        
        if state.missing_components:
            messages.append(f"❌ Missing components: {', '.join(state.missing_components)}")
        
        if not state.config_valid:
            messages.append("❌ Configuration file is invalid or missing")
        
        if not state.framework_deployed:
            messages.append("❌ Framework is not properly deployed")
        
        if not state.memory_system_configured:
            messages.append("⚠️ Memory system is not configured")
        
        return False, messages