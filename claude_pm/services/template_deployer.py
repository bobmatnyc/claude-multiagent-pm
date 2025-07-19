#!/usr/bin/env python3
"""
Template Deployer Service - Extract from Parent Directory Manager
================================================================

Handles template deployment operations for the Claude PM Framework.
This module is extracted from parent_directory_manager.py as part of
the refactoring effort (ISS-0154).

Key Features:
- Framework template deployment
- Template variable substitution
- Version-aware deployment decisions
- Conflict resolution
- Template rendering

Created: 2025-07-18
Author: Engineer Agent
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum


class DeploymentDecision(Enum):
    """Deployment decision types."""
    DEPLOY = "deploy"
    SKIP = "skip"
    UPDATE = "update"
    FORCE = "force"


@dataclass
class DeploymentContext:
    """Context for template deployment."""
    target_path: Path
    template_content: str
    template_variables: Dict[str, Any]
    existing_content: Optional[str] = None
    force_deployment: bool = False
    version_info: Optional[Dict[str, str]] = None


@dataclass
class DeploymentResult:
    """Result of a template deployment."""
    success: bool
    action_taken: str
    target_path: Path
    version_deployed: Optional[str] = None
    previous_version: Optional[str] = None
    messages: List[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class TemplateDeployer:
    """
    Manages template deployment operations for the Claude PM Framework.
    
    This class provides:
    - Framework template deployment with version checking
    - Template variable substitution and rendering
    - Intelligent deployment decisions based on existing files
    - Conflict resolution and protection mechanisms
    """
    
    def __init__(self, framework_path: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize the Template Deployer.
        
        Args:
            framework_path: Path to the framework directory
            logger: Optional logger instance
        """
        self.framework_path = Path(framework_path)
        self.logger = logger or logging.getLogger(__name__)
        
        # Template patterns
        self.framework_deployment_pattern = re.compile(
            r'# Claude PM Framework Configuration - Deployment'
        )
        self.claude_md_version_pattern = re.compile(
            r'CLAUDE_MD_VERSION:\s*(\d+(?:\.\d+)?(?:\.\d+)?-\d{3})'
        )
        self.framework_version_pattern = re.compile(
            r'FRAMEWORK_VERSION:\s*(\d+(?:\.\d+)?(?:\.\d+)?)'
        )
        
    def is_framework_deployment_template(self, content: str) -> bool:
        """
        Check if content is a framework deployment template.
        
        Args:
            content: File content to check
            
        Returns:
            True if content is a framework deployment template
        """
        # Check for deployment title
        if not self.framework_deployment_pattern.search(content):
            return False
            
        # Check for metadata block
        if "<!-- CLAUDE_MD_VERSION:" not in content:
            return False
            
        # Check for deployment-specific markers
        deployment_markers = [
            "FRAMEWORK_VERSION:",
            "DEPLOYMENT_DATE:",
            "**You are operating within a Claude PM Framework deployment**"
        ]
        
        markers_found = sum(1 for marker in deployment_markers if marker in content)
        return markers_found >= 2
        
    def extract_claude_md_version(self, content: str) -> Optional[str]:
        """
        Extract CLAUDE_MD_VERSION from content.
        
        Args:
            content: File content
            
        Returns:
            Version string or None
        """
        match = self.claude_md_version_pattern.search(content)
        return match.group(1) if match else None
        
    def extract_framework_version(self, content: str) -> Optional[str]:
        """
        Extract FRAMEWORK_VERSION from content.
        
        Args:
            content: File content
            
        Returns:
            Version string or None
        """
        match = self.framework_version_pattern.search(content)
        return match.group(1) if match else None
        
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        def parse_version(v: str) -> Tuple[Tuple[int, ...], int]:
            """Parse version string into comparable components."""
            if '-' in v:
                base, serial = v.rsplit('-', 1)
                return tuple(map(int, base.split('.'))), int(serial)
            else:
                return tuple(map(int, v.split('.'))), 0
                
        try:
            v1_parsed = parse_version(version1)
            v2_parsed = parse_version(version2)
            
            if v1_parsed < v2_parsed:
                return -1
            elif v1_parsed > v2_parsed:
                return 1
            else:
                return 0
        except Exception:
            # Fallback to string comparison
            return -1 if version1 < version2 else (0 if version1 == version2 else 1)
            
    def should_skip_deployment(
        self,
        existing_content: str,
        new_content: str,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Determine if deployment should be skipped.
        
        Args:
            existing_content: Existing file content
            new_content: New template content
            force: Force deployment regardless of versions
            
        Returns:
            Tuple of (should_skip, reason)
        """
        if force:
            return False, "Force deployment requested"
            
        # Check if existing file is a framework deployment
        if not self.is_framework_deployment_template(existing_content):
            return True, "Not a framework deployment template"
            
        # Extract versions
        existing_version = self.extract_claude_md_version(existing_content)
        new_version = self.extract_claude_md_version(new_content)
        
        if not existing_version or not new_version:
            return False, "Version information missing"
            
        # Compare versions
        comparison = self.compare_versions(new_version, existing_version)
        
        if comparison == 0:
            return True, f"Same version already deployed: {existing_version}"
        elif comparison < 0:
            return True, f"Newer version already deployed: {existing_version} > {new_version}"
        else:
            return False, f"Update available: {existing_version} -> {new_version}"
            
    async def render_template(
        self,
        content: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render template content with variable substitution.
        
        Args:
            content: Template content
            variables: Variables to substitute
            
        Returns:
            Rendered content
        """
        rendered = content
        
        # Sort variables by key length (longest first) to avoid partial replacements
        sorted_vars = sorted(variables.items(), key=lambda x: len(x[0]), reverse=True)
        
        for key, value in sorted_vars:
            # Handle both {{VARIABLE}} and {{ VARIABLE }} formats
            patterns = [
                f"{{{{{key}}}}}",
                f"{{{{ {key} }}}}",
            ]
            
            for pattern in patterns:
                rendered = rendered.replace(pattern, str(value))
                
        return rendered
        
    def get_default_template_variables(
        self,
        target_directory: Path,
        deployment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get default template variables for deployment.
        
        Args:
            target_directory: Target directory for deployment
            deployment_id: Optional deployment ID
            
        Returns:
            Dictionary of template variables
        """
        from claude_pm import __version__ as framework_version
        
        # Generate deployment ID if not provided
        if deployment_id is None:
            deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Get platform-specific notes
        platform_notes = self._get_platform_notes()
        
        variables = {
            "FRAMEWORK_VERSION": framework_version,
            "DEPLOYMENT_DATE": datetime.now().isoformat(),
            "TARGET_DIRECTORY": str(target_directory),
            "DEPLOYMENT_ID": deployment_id,
            "PROJECT_ROOT": str(target_directory),
            "PLATFORM_NOTES": platform_notes,
            "PYTHON_COMMAND": "python3" if os.name != 'nt' else "python",
        }
        
        return variables
        
    def _get_platform_notes(self) -> str:
        """Get platform-specific notes for template."""
        import platform
        
        system = platform.system()
        if system == "Windows":
            return "Windows-specific: Use 'python' instead of 'python3'"
        elif system == "Darwin":
            return "macOS-specific: Ensure Python 3 is installed via Homebrew or system"
        else:
            return "Linux-specific: Use system package manager for dependencies"
            
    async def deploy_template(
        self,
        context: DeploymentContext
    ) -> DeploymentResult:
        """
        Deploy a template to target location.
        
        Args:
            context: Deployment context
            
        Returns:
            Deployment result
        """
        result = DeploymentResult(
            success=False,
            action_taken="none",
            target_path=context.target_path
        )
        
        try:
            # Check if target exists
            if context.target_path.exists():
                # Read existing content
                existing_content = context.target_path.read_text(encoding='utf-8')
                
                # Determine if we should skip
                should_skip, reason = self.should_skip_deployment(
                    existing_content,
                    context.template_content,
                    context.force_deployment
                )
                
                if should_skip:
                    result.action_taken = "skipped"
                    result.messages.append(f"Deployment skipped: {reason}")
                    result.success = True
                    return result
                    
                # Extract version info
                result.previous_version = self.extract_claude_md_version(existing_content)
                
            # Render template
            rendered_content = await self.render_template(
                context.template_content,
                context.template_variables
            )
            
            # Extract new version
            result.version_deployed = self.extract_claude_md_version(rendered_content)
            
            # Create parent directory if needed
            context.target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            context.target_path.write_text(rendered_content, encoding='utf-8')
            
            # Set result
            result.success = True
            result.action_taken = "deployed" if result.previous_version is None else "updated"
            result.messages.append(
                f"Successfully {result.action_taken} template"
            )
            
            if result.version_deployed:
                result.messages.append(f"Version: {result.version_deployed}")
                
        except Exception as e:
            result.success = False
            result.action_taken = "failed"
            result.messages.append(f"Deployment failed: {str(e)}")
            self.logger.error(f"Template deployment failed: {e}")
            
        return result
        
    def generate_next_claude_md_version(
        self,
        framework_version: str,
        existing_versions: List[str]
    ) -> str:
        """
        Generate the next CLAUDE_MD_VERSION.
        
        Args:
            framework_version: Current framework version
            existing_versions: List of existing versions
            
        Returns:
            Next version string
        """
        # Filter versions for current framework version
        current_fw_versions = [
            v for v in existing_versions
            if v.startswith(f"{framework_version}-")
        ]
        
        if not current_fw_versions:
            # First version for this framework version
            return f"{framework_version}-001"
            
        # Extract serial numbers
        serials = []
        for v in current_fw_versions:
            try:
                serial = int(v.split('-')[-1])
                serials.append(serial)
            except (ValueError, IndexError):
                continue
                
        # Get next serial
        next_serial = max(serials) + 1 if serials else 1
        
        return f"{framework_version}-{next_serial:03d}"
        
    def validate_template_integrity(self, template_path: Path) -> Dict[str, Any]:
        """
        Validate template file integrity.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Validation results
        """
        results = {
            "valid": False,
            "exists": False,
            "readable": False,
            "is_framework_template": False,
            "has_version": False,
            "has_required_variables": False,
            "errors": []
        }
        
        # Check existence
        if not template_path.exists():
            results["errors"].append("Template file does not exist")
            return results
            
        results["exists"] = True
        
        # Check readability
        try:
            content = template_path.read_text(encoding='utf-8')
            results["readable"] = True
        except Exception as e:
            results["errors"].append(f"Cannot read template: {e}")
            return results
            
        # Check if it's a framework template
        if self.is_framework_deployment_template(content):
            results["is_framework_template"] = True
        else:
            results["errors"].append("Not a valid framework deployment template")
            
        # Check version
        version = self.extract_claude_md_version(content)
        if version:
            results["has_version"] = True
        else:
            results["errors"].append("Missing CLAUDE_MD_VERSION")
            
        # Check required variables
        required_vars = [
            "{{FRAMEWORK_VERSION}}",
            "{{DEPLOYMENT_DATE}}",
            "{{DEPLOYMENT_ID}}"
        ]
        
        missing_vars = [var for var in required_vars if var not in content]
        if not missing_vars:
            results["has_required_variables"] = True
        else:
            results["errors"].append(f"Missing variables: {missing_vars}")
            
        # Set overall validity
        results["valid"] = (
            results["exists"] and
            results["readable"] and
            results["is_framework_template"] and
            results["has_version"] and
            results["has_required_variables"]
        )
        
        return results