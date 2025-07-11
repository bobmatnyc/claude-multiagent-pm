#!/usr/bin/env python3
"""
Template Deployment Integration Service - CMPM-102 Extension
==========================================================

This service provides integration between the Template Manager and
CMPM-101 Deployment Detection System for deployment-aware template
management.

Features:
- Integration with CMPM-101 deployment detection
- Deployment-aware template path resolution
- Template sourcing based on deployment type
- Cross-deployment template synchronization
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging
from .template_manager import TemplateManager, TemplateSource, TemplateType


class DeploymentType(Enum):
    """Deployment types from CMPM-101."""
    LOCAL_SOURCE = "local_source"
    NPM_GLOBAL = "npm_global"
    NPX = "npx"
    NPM_LOCAL = "npm_local"
    DEPLOYED = "deployed"
    ENVIRONMENT = "environment"
    FALLBACK = "fallback"


@dataclass
class DeploymentAwareTemplateConfig:
    """Configuration for deployment-aware template management."""
    deployment_type: DeploymentType
    framework_path: Path
    template_sources: Dict[TemplateSource, Path]
    deployment_metadata: Dict[str, Any]
    confidence: str
    is_development: bool = False


class TemplateDeploymentIntegration(BaseService):
    """
    Service for integrating template management with deployment detection.
    
    This service bridges the Template Manager with the deployment detection
    system to provide deployment-aware template sourcing and management.
    """
    
    def __init__(self):
        super().__init__(name="template_deployment_integration")
        self.logger = setup_logging(__name__)
        self.deployment_detector = None
        self.template_manager = None
        self.deployment_config = None
    
    async def _initialize(self) -> bool:
        """Initialize the template deployment integration service."""
        try:
            # Initialize deployment detector
            await self._initialize_deployment_detector()
            
            # Get deployment configuration
            self.deployment_config = await self._get_deployment_configuration()
            
            # Initialize template manager with deployment config
            self.template_manager = TemplateManager(self.deployment_config)
            await self.template_manager.initialize()
            
            self.logger.info("Template Deployment Integration initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Template Deployment Integration: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup the template deployment integration service."""
        try:
            if self.template_manager:
                await self.template_manager.cleanup()
            
            self.logger.info("Template Deployment Integration cleanup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Template Deployment Integration: {e}")
            return False
    
    async def _initialize_deployment_detector(self):
        """Initialize the deployment detector from CMPM-101."""
        try:
            # Import the deployment detector from the CLI module
            # This uses the existing CMPM-101 implementation
            from importlib import import_module
            
            # Check if we can import the deployment detector
            try:
                # Try to import from the bin directory
                import sys
                bin_path = Path(__file__).parent.parent.parent / "bin"
                if str(bin_path) not in sys.path:
                    sys.path.insert(0, str(bin_path))
                
                # Import the deployment detector class
                claude_pm_module = import_module("claude-pm")
                self.deployment_detector = claude_pm_module.DeploymentDetector()
                
            except ImportError:
                # Fallback: Run the CLI command to get deployment info
                self.logger.warning("Could not import DeploymentDetector, using CLI fallback")
                self.deployment_detector = None
        except Exception as e:
            self.logger.error(f"Failed to initialize deployment detector: {e}")
            self.deployment_detector = None
    
    async def _get_deployment_configuration(self) -> Dict[str, Any]:
        """Get deployment configuration from CMCP-101."""
        try:
            if self.deployment_detector:
                # Use the deployment detector directly
                deployment_strategy = self.deployment_detector.getDeploymentStrategy()
                return deployment_strategy
            else:
                # Fallback: Use CLI command
                return await self._get_deployment_config_via_cli()
        except Exception as e:
            self.logger.error(f"Failed to get deployment configuration: {e}")
            return self._get_fallback_deployment_config()
    
    async def _get_deployment_config_via_cli(self) -> Dict[str, Any]:
        """Get deployment configuration via CLI command."""
        try:
            # Find the claude-pm CLI
            cli_candidates = [
                Path(__file__).parent.parent.parent / "bin" / "claude-pm",
                "claude-pm",
                "npx claude-pm"
            ]
            
            cli_command = None
            for candidate in cli_candidates:
                if isinstance(candidate, Path) and candidate.exists():
                    cli_command = str(candidate)
                    break
                elif isinstance(candidate, str):
                    # Try to run the command to see if it exists
                    try:
                        result = subprocess.run(
                            [candidate, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            cli_command = candidate
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
            
            if not cli_command:
                self.logger.warning("Could not find claude-pm CLI")
                return self._get_fallback_deployment_config()
            
            # Run deployment info command
            result = subprocess.run(
                [cli_command, "--deployment-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse the JSON output
                deployment_info = json.loads(result.stdout)
                return deployment_info
            else:
                self.logger.warning(f"CLI command failed: {result.stderr}")
                return self._get_fallback_deployment_config()
        except Exception as e:
            self.logger.error(f"Failed to get deployment config via CLI: {e}")
            return self._get_fallback_deployment_config()
    
    def _get_fallback_deployment_config(self) -> Dict[str, Any]:
        """Get fallback deployment configuration."""
        working_dir = Path.cwd()
        
        # Try to detect framework path
        framework_path = working_dir
        if (working_dir / "claude_pm" / "__init__.py").exists():
            framework_path = working_dir
        elif (working_dir.parent / "claude_pm" / "__init__.py").exists():
            framework_path = working_dir.parent
        else:
            # Default to current directory
            framework_path = working_dir
        
        return {
            "strategy": "fallback",
            "config": {
                "deploymentType": "fallback",
                "found": True,
                "platform": "unknown",
                "confidence": "low",
                "frameworkPath": str(framework_path),
                "paths": {
                    "framework": str(framework_path),
                    "working": str(working_dir),
                    "templates": str(framework_path / "templates"),
                    "config": str(framework_path / ".claude-pm")
                }
            }
        }
    
    async def get_deployment_aware_template_config(self) -> DeploymentAwareTemplateConfig:
        """Get deployment-aware template configuration."""
        try:
            if not self.deployment_config:
                self.deployment_config = await self._get_deployment_configuration()
            
            config = self.deployment_config.get("config", {})
            deployment_type = DeploymentType(config.get("deploymentType", "fallback"))
            
            # Get paths from deployment config
            paths = config.get("paths", {})
            framework_path = Path(paths.get("framework", Path.cwd()))
            
            # Build template sources based on deployment type
            template_sources = self._build_template_sources(deployment_type, framework_path)
            
            return DeploymentAwareTemplateConfig(
                deployment_type=deployment_type,
                framework_path=framework_path,
                template_sources=template_sources,
                deployment_metadata=config.get("metadata", {}),
                confidence=config.get("confidence", "unknown"),
                is_development=deployment_type == DeploymentType.LOCAL_SOURCE
            )
        except Exception as e:
            self.logger.error(f"Failed to get deployment-aware template config: {e}")
            # Return fallback config
            return DeploymentAwareTemplateConfig(
                deployment_type=DeploymentType.FALLBACK,
                framework_path=Path.cwd(),
                template_sources=self._build_template_sources(DeploymentType.FALLBACK, Path.cwd()),
                deployment_metadata={},
                confidence="low",
                is_development=False
            )
    
    def _build_template_sources(
        self,
        deployment_type: DeploymentType,
        framework_path: Path
    ) -> Dict[TemplateSource, Path]:
        """Build template sources based on deployment type."""
        working_dir = Path.cwd()
        
        # Base template sources
        template_sources = {
            TemplateSource.SYSTEM: framework_path / "claude_pm" / "templates",
            TemplateSource.FRAMEWORK: framework_path / "framework" / "templates",
            TemplateSource.USER: Path.home() / ".claude-pm" / "templates",
            TemplateSource.PROJECT: working_dir / ".claude-pm" / "templates"
        }
        
        # Adjust paths based on deployment type
        if deployment_type == DeploymentType.LOCAL_SOURCE:
            # Development mode - use source paths
            template_sources[TemplateSource.SYSTEM] = framework_path / "claude_pm" / "templates"
            template_sources[TemplateSource.FRAMEWORK] = framework_path / "framework" / "templates"
        
        elif deployment_type == DeploymentType.NPM_GLOBAL:
            # Global installation - use global paths
            template_sources[TemplateSource.SYSTEM] = framework_path / "claude_pm" / "templates"
            template_sources[TemplateSource.FRAMEWORK] = framework_path / "framework" / "templates"
        
        elif deployment_type == DeploymentType.DEPLOYED:
            # Deployed instance - use deployment paths
            template_sources[TemplateSource.SYSTEM] = framework_path / "claude_pm" / "templates"
            template_sources[TemplateSource.FRAMEWORK] = framework_path / "framework" / "templates"
        
        return template_sources
    
    async def get_templates_by_deployment_context(
        self,
        template_type: Optional[TemplateType] = None,
        include_development: bool = False
    ) -> List[Dict[str, Any]]:
        """Get templates filtered by deployment context."""
        try:
            if not self.template_manager:
                return []
            
            # Get deployment config
            deployment_config = await self.get_deployment_aware_template_config()
            
            # Get all templates
            all_templates = await self.template_manager.list_templates(template_type)
            
            # Filter by deployment context
            filtered_templates = []
            for template in all_templates:
                # Include/exclude based on deployment context
                template_source = TemplateSource(template["source"])
                
                # Always include project and user templates
                if template_source in [TemplateSource.PROJECT, TemplateSource.USER]:
                    filtered_templates.append(template)
                    continue
                
                # Include system/framework templates based on deployment type
                if template_source in [TemplateSource.SYSTEM, TemplateSource.FRAMEWORK]:
                    # Check if this source is available in current deployment
                    source_path = deployment_config.template_sources.get(template_source)
                    if source_path and source_path.exists():
                        filtered_templates.append(template)
                        continue
                
                # Include development templates if requested
                if include_development and deployment_config.is_development:
                    filtered_templates.append(template)
            
            return filtered_templates
        except Exception as e:
            self.logger.error(f"Failed to get templates by deployment context: {e}")
            return []
    
    async def sync_templates_across_deployments(
        self,
        source_deployment: str,
        target_deployment: str,
        template_types: List[TemplateType] = None
    ) -> bool:
        """Sync templates between different deployments."""
        try:
            # This is a placeholder for future implementation
            # Would involve copying templates between deployment locations
            self.logger.info(f"Template sync requested: {source_deployment} -> {target_deployment}")
            
            # For now, just log the request
            self.logger.warning("Template sync across deployments not yet implemented")
            return False
        except Exception as e:
            self.logger.error(f"Failed to sync templates across deployments: {e}")
            return False
    
    async def validate_deployment_template_access(self) -> Dict[str, Any]:
        """Validate template access in current deployment."""
        try:
            deployment_config = await self.get_deployment_aware_template_config()
            
            validation_results = {
                "deployment_type": deployment_config.deployment_type.value,
                "framework_path": str(deployment_config.framework_path),
                "confidence": deployment_config.confidence,
                "template_sources": {},
                "accessible_templates": 0,
                "inaccessible_templates": 0,
                "warnings": []
            }
            
            # Check each template source
            for source, path in deployment_config.template_sources.items():
                source_info = {
                    "path": str(path),
                    "exists": path.exists(),
                    "readable": False,
                    "template_count": 0
                }
                
                if path.exists():
                    try:
                        # Check if we can read the directory
                        if path.is_dir():
                            source_info["readable"] = True
                            
                            # Count templates
                            template_patterns = ["*.template", "*.tmpl", "*.yaml", "*.yml"]
                            for pattern in template_patterns:
                                source_info["template_count"] += len(list(path.glob(f"**/{pattern}")))
                            
                            validation_results["accessible_templates"] += source_info["template_count"]
                        else:
                            validation_results["warnings"].append(f"Template source {source.value} is not a directory: {path}")
                    except PermissionError:
                        validation_results["warnings"].append(f"Permission denied accessing template source {source.value}: {path}")
                else:
                    validation_results["inaccessible_templates"] += 1
                    validation_results["warnings"].append(f"Template source {source.value} not found: {path}")
                
                validation_results["template_sources"][source.value] = source_info
            
            return validation_results
        except Exception as e:
            self.logger.error(f"Failed to validate deployment template access: {e}")
            return {
                "deployment_type": "error",
                "error": str(e),
                "accessible_templates": 0,
                "inaccessible_templates": 0,
                "warnings": [f"Validation failed: {str(e)}"]
            }
    
    async def get_deployment_specific_template_recommendations(
        self,
        project_type: str,
        requirements: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get template recommendations based on deployment context."""
        try:
            deployment_config = await self.get_deployment_aware_template_config()
            recommendations = []
            
            # Get available templates
            available_templates = await self.get_templates_by_deployment_context()
            
            # Score templates based on deployment context and requirements
            for template in available_templates:
                score = 0
                reasons = []
                
                # Base score for template availability
                score += 10
                reasons.append("Template is available in current deployment")
                
                # Boost score for user/project templates
                if template["source"] in ["user", "project"]:
                    score += 20
                    reasons.append("Custom template (user/project specific)")
                
                # Boost score for development templates in development deployment
                if deployment_config.is_development and template["source"] == "system":
                    score += 15
                    reasons.append("Development template in development deployment")
                
                # Match template type to project type
                if template["type"] == project_type:
                    score += 30
                    reasons.append(f"Template type matches project type ({project_type})")
                
                # Check requirements matching (if provided)
                if requirements:
                    # This would need more sophisticated matching
                    # For now, just give a small boost
                    score += 5
                    reasons.append("Requirements considered")
                
                recommendation = {
                    "template_id": template["template_id"],
                    "template_name": template["name"],
                    "template_type": template["type"],
                    "source": template["source"],
                    "score": score,
                    "reasons": reasons,
                    "deployment_context": deployment_config.deployment_type.value
                }
                
                recommendations.append(recommendation)
            
            # Sort by score (highest first)
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            
            return recommendations
        except Exception as e:
            self.logger.error(f"Failed to get deployment-specific template recommendations: {e}")
            return []
    
    # Public API methods that delegate to template manager
    
    async def create_template(self, *args, **kwargs):
        """Create template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.create_template(*args, **kwargs)
    
    async def update_template(self, *args, **kwargs):
        """Update template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.update_template(*args, **kwargs)
    
    async def get_template(self, *args, **kwargs):
        """Get template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.get_template(*args, **kwargs)
    
    async def render_template(self, *args, **kwargs):
        """Render template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.render_template(*args, **kwargs)
    
    async def backup_template(self, *args, **kwargs):
        """Backup template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.backup_template(*args, **kwargs)
    
    async def restore_template(self, *args, **kwargs):
        """Restore template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.restore_template(*args, **kwargs)
    
    async def validate_template(self, *args, **kwargs):
        """Validate template (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.validate_template(*args, **kwargs)
    
    async def list_templates(self, *args, **kwargs):
        """List templates (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.list_templates(*args, **kwargs)
    
    async def get_template_history(self, *args, **kwargs):
        """Get template history (delegates to template manager)."""
        if not self.template_manager:
            raise RuntimeError("Template manager not initialized")
        return await self.template_manager.get_template_history(*args, **kwargs)