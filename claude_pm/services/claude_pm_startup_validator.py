#!/usr/bin/env python3
"""
Claude PM Startup Validator - Parent CLAUDE.md Change Detection System
=====================================================================

This module provides comprehensive startup validation for Claude PM Framework,
including parent directory CLAUDE.md change detection and user notification.

Key Features:
- Detects parent directory CLAUDE.md files and compares with framework template
- Version comparison using framework VERSION files
- Fallback to modification time comparison when version metadata unavailable
- Clear user notifications with actionable guidance
- Integration with existing claude-pm startup validation flow

Integration Points:
- Called from bin/claude-pm during startup validation (display_comprehensive_status)
- Works with framework template at framework/CLAUDE.md
- Uses framework/VERSION for template version reference
- Provides user-friendly update guidance

Implementation Notes:
- Framework template version extracted from framework/VERSION file
- Parent file version extracted from FRAMEWORK_VERSION metadata in deployed files
- Graceful fallback to file modification time comparison
- Error handling for filesystem access issues
- Memory collection integration for bugs and user feedback
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Service version for this component
STARTUP_VALIDATOR_VERSION = "001"


class StartupValidator:
    """
    Claude PM Framework startup validation with parent CLAUDE.md change detection.
    
    This class provides comprehensive startup validation including framework
    deployment checks, parent directory template status, and user notifications.
    """
    
    def __init__(self, framework_path: Path, console=None):
        """
        Initialize startup validator.
        
        Args:
            framework_path: Path to Claude PM framework root directory
            console: Rich console instance for output formatting
        """
        self.framework_path = framework_path
        self.console = console
        self.framework_template = framework_path / "framework" / "CLAUDE.md"
        self.framework_version_file = framework_path / "framework" / "VERSION"
        
    def check_parent_claude_md_status(self, target_directory: Optional[Path] = None) -> Dict[str, Any]:
        """
        Check parent directory CLAUDE.md file status against framework template.
        
        This is the core function that detects whether a parent directory CLAUDE.md
        file needs updating by comparing it against the framework template.
        
        Args:
            target_directory: Directory to check (defaults to current working directory)
            
        Returns:
            Dict with comprehensive check results:
            - needs_update: bool - True if parent file needs updating
            - parent_exists: bool - True if parent CLAUDE.md exists
            - parent_path: Path - Path to parent CLAUDE.md file
            - template_version: str - Framework template version
            - parent_version: str - Parent file version (if available)
            - status_message: str - Human-readable status description
            - update_reason: str - Reason why update is needed (if applicable)
        """
        try:
            # Determine target directory
            if target_directory is None:
                target_directory = Path.cwd()
            
            parent_claude_md = target_directory / "CLAUDE.md"
            
            # Check if framework template exists
            if not self.framework_template.exists():
                return {
                    "needs_update": False,
                    "parent_exists": parent_claude_md.exists(),
                    "parent_path": parent_claude_md,
                    "template_version": "unknown",
                    "parent_version": "unknown",
                    "status_message": "Framework template not found - cannot check for updates",
                    "update_reason": "template_missing"
                }
            
            # Extract template version from framework VERSION file
            template_version = self._get_framework_template_version()
            
            # Check if parent CLAUDE.md exists
            if not parent_claude_md.exists():
                return {
                    "needs_update": False,
                    "parent_exists": False,
                    "parent_path": parent_claude_md,
                    "template_version": template_version,
                    "parent_version": "none",
                    "status_message": f"No CLAUDE.md in current directory ({target_directory.name})",
                    "update_reason": "no_parent_file"
                }
            
            # Extract version from parent CLAUDE.md
            parent_version = self._get_parent_file_version(parent_claude_md)
            
            # Determine if update is needed and generate status message
            update_result = self._compare_versions(
                parent_version, template_version, 
                parent_claude_md, self.framework_template
            )
            
            return {
                "needs_update": update_result["needs_update"],
                "parent_exists": True,
                "parent_path": parent_claude_md,
                "template_version": template_version,
                "parent_version": parent_version,
                "status_message": update_result["status_message"],
                "update_reason": update_result["update_reason"]
            }
            
        except Exception as e:
            return {
                "needs_update": False,
                "parent_exists": False,
                "parent_path": Path.cwd() / "CLAUDE.md",
                "template_version": "unknown",
                "parent_version": "unknown",
                "status_message": f"Error checking parent CLAUDE.md status: {e}",
                "update_reason": "check_error"
            }
    
    def _get_framework_template_version(self) -> str:
        """
        Extract framework template version from framework/VERSION file.
        
        Returns:
            Framework version string or "unknown" if not available
        """
        try:
            if self.framework_version_file.exists():
                return self.framework_version_file.read_text().strip()
        except Exception:
            pass
        return "unknown"
    
    def _get_parent_file_version(self, parent_file: Path) -> str:
        """
        Extract version from parent CLAUDE.md file.
        
        Looks for FRAMEWORK_VERSION metadata in the deployed template.
        
        Args:
            parent_file: Path to parent CLAUDE.md file
            
        Returns:
            Parent file version string or "unknown" if not available
        """
        try:
            parent_content = parent_file.read_text()
            # Look for FRAMEWORK_VERSION in the deployed template
            version_match = re.search(r'FRAMEWORK_VERSION:\s*(\S+)', parent_content)
            if version_match:
                return version_match.group(1)
        except Exception:
            pass
        return "unknown"
    
    def _compare_versions(self, parent_version: str, template_version: str, 
                         parent_file: Path, template_file: Path) -> Dict[str, Any]:
        """
        Compare parent and template versions to determine update status.
        
        Uses version comparison first, falls back to modification time comparison.
        
        Args:
            parent_version: Version string from parent file
            template_version: Version string from template
            parent_file: Path to parent file
            template_file: Path to template file
            
        Returns:
            Dict with comparison results:
            - needs_update: bool
            - status_message: str
            - update_reason: str
        """
        if parent_version == "unknown" or template_version == "unknown":
            # If we can't determine versions, check file modification times
            try:
                parent_mtime = parent_file.stat().st_mtime
                template_mtime = template_file.stat().st_mtime
                
                if template_mtime > parent_mtime:
                    return {
                        "needs_update": True,
                        "status_message": "Framework template is newer than parent CLAUDE.md",
                        "update_reason": "newer_template_mtime"
                    }
                else:
                    return {
                        "needs_update": False,
                        "status_message": "Parent CLAUDE.md appears current (based on modification time)",
                        "update_reason": "current_by_mtime"
                    }
            except Exception:
                return {
                    "needs_update": False,
                    "status_message": "Cannot determine update status - version information unavailable",
                    "update_reason": "comparison_error"
                }
        else:
            # Compare version strings
            if parent_version != template_version:
                return {
                    "needs_update": True,
                    "status_message": f"Update available: {parent_version} → {template_version}",
                    "update_reason": "version_mismatch"
                }
            else:
                return {
                    "needs_update": False,
                    "status_message": f"Parent CLAUDE.md is current (version {parent_version})",
                    "update_reason": "current_by_version"
                }
    
    def display_parent_claude_md_notification(self, check_result: Dict[str, Any]) -> None:
        """
        Display notification about parent CLAUDE.md status with actionable guidance.
        
        This function provides user-friendly notifications about the status of their
        parent directory CLAUDE.md file, with clear guidance on how to update.
        
        Args:
            check_result: Result dict from check_parent_claude_md_status()
        """
        if not self.console:
            # Fallback to print if no console available
            self._display_notification_fallback(check_result)
            return
            
        if not check_result["parent_exists"]:
            # No parent CLAUDE.md - this is normal for many directories
            self.console.print(f"[dim]📄 Parent CLAUDE.md: {check_result['status_message']}[/dim]")
            return
        
        if check_result["needs_update"]:
            # Parent file needs updating
            self.console.print("")
            self.console.print("[bold yellow]📄 CLAUDE.md Update Available[/bold yellow]")
            self.console.print("─" * 50)
            self.console.print(f"📍 Location: {check_result['parent_path']}")
            self.console.print(f"📊 Status: {check_result['status_message']}")
            self.console.print("")
            self.console.print("[bold]💡 How to update:[/bold]")
            self.console.print("   • claude-pm init          (recommended - updates all framework files)")
            self.console.print("   • claude-pm setup         (alternative update method)")
            self.console.print("   • claude-pm deploy        (force deployment)")
            self.console.print("")
            self.console.print("[dim]💬 This update will bring your CLAUDE.md file up to date with the latest[/dim]")
            self.console.print("[dim]   framework features, agent types, and configuration options.[/dim]")
            self.console.print("")
        else:
            # Parent file is current
            self.console.print(f"[green]📄 Parent CLAUDE.md: {check_result['status_message']}[/green]")
    
    def _display_notification_fallback(self, check_result: Dict[str, Any]) -> None:
        """
        Fallback notification display when Rich console is not available.
        
        Args:
            check_result: Result dict from check_parent_claude_md_status()
        """
        if not check_result["parent_exists"]:
            print(f"📄 Parent CLAUDE.md: {check_result['status_message']}")
            return
        
        if check_result["needs_update"]:
            print("")
            print("📄 CLAUDE.md Update Available")
            print("─" * 50)
            print(f"📍 Location: {check_result['parent_path']}")
            print(f"📊 Status: {check_result['status_message']}")
            print("")
            print("💡 How to update:")
            print("   • claude-pm init          (recommended - updates all framework files)")
            print("   • claude-pm setup         (alternative update method)")
            print("   • claude-pm deploy        (force deployment)")
            print("")
            print("💬 This update will bring your CLAUDE.md file up to date with the latest")
            print("   framework features, agent types, and configuration options.")
            print("")
        else:
            print(f"📄 Parent CLAUDE.md: {check_result['status_message']}")


def validate_parent_claude_md_integration() -> bool:
    """
    Validate that parent CLAUDE.md checking is properly integrated into claude-pm.
    
    This function can be used to verify the integration is working correctly.
    
    Returns:
        True if integration is working, False otherwise
    """
    try:
        # Check if claude-pm script contains the parent checking functions
        claude_pm_script = Path.home() / ".local" / "bin" / "claude-pm"
        if not claude_pm_script.exists():
            return False
        
        content = claude_pm_script.read_text()
        
        # Check for required functions
        required_functions = [
            "check_parent_claude_md_status",
            "display_parent_claude_md_notification"
        ]
        
        for func in required_functions:
            if func not in content:
                return False
        
        # Check for integration in display_comprehensive_status
        integration_check = "parent_check = check_parent_claude_md_status()"
        if integration_check not in content:
            return False
        
        return True
        
    except Exception:
        return False


# Memory collection integration for startup validation issues
def collect_startup_validation_memory(issue_type: str, details: Dict[str, Any], 
                                    memory_system=None) -> None:
    """
    Collect memory about startup validation issues for continuous improvement.
    
    Args:
        issue_type: Type of issue (version_check_error, template_missing, etc.)
        details: Detailed information about the issue
        memory_system: Memory system instance for storage
    """
    if memory_system is None:
        return  # Skip if no memory system available
    
    try:
        memory_entry = {
            "category": "startup_validation",
            "issue_type": issue_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "component": "claude_pm_startup_validator",
            "version": STARTUP_VALIDATOR_VERSION
        }
        
        memory_system.add(
            f"Startup validation issue: {issue_type}",
            metadata=memory_entry
        )
    except Exception:
        # Silent failure for memory collection
        pass


if __name__ == "__main__":
    # Test the startup validator
    framework_path = Path("/Users/masa/Projects/claude-multiagent-pm")
    validator = StartupValidator(framework_path)
    
    # Test in current directory
    result = validator.check_parent_claude_md_status()
    print("Parent CLAUDE.md Status Check Results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Test integration validation
    integration_valid = validate_parent_claude_md_integration()
    print(f"\nIntegration validation: {'✅ PASSED' if integration_valid else '❌ FAILED'}")