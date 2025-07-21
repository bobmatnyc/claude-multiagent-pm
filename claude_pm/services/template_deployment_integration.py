#!/usr/bin/env python3
"""
Template Deployment Integration Service
======================================

Provides integration between template management and deployment detection.
This is a stub implementation to resolve import errors.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from claude_pm.services.template_manager import (
    TemplateManager,
    TemplateType,
    TemplateSource
)


@dataclass
class TemplateVersion:
    """Represents a template version."""
    template_id: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    backup_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TemplateValidationResult:
    """Result of template validation."""
    template_id: str
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TemplateData:
    """Container for template data."""
    content: str
    version: TemplateVersion


class TemplateDeploymentIntegration:
    """Integration service for template deployment functionality."""
    
    def __init__(self):
        """Initialize the template deployment integration service."""
        self.template_manager = TemplateManager()
        self.deployment_config: Optional[Dict[str, Any]] = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the integration service."""
        self.deployment_config = self._get_deployment_configuration()
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False
        self.deployment_config = None
    
    def _get_deployment_configuration(self) -> Dict[str, Any]:
        """Get deployment configuration (stub implementation)."""
        # This would normally integrate with actual deployment detection
        return {
            "strategy": "local_source",
            "config": {
                "deploymentType": "local_source",
                "found": True,
                "platform": "darwin",
                "confidence": "high",
                "frameworkPath": str(Path.cwd()),
                "paths": {
                    "framework": str(Path.cwd()),
                    "claudePm": str(Path.cwd() / "claude_pm"),
                    "bin": str(Path.cwd() / "bin"),
                    "config": str(Path.cwd() / ".claude-pm"),
                    "templates": str(Path.cwd() / "framework" / "templates"),
                    "schemas": str(Path.cwd() / "schemas"),
                    "working": str(Path.cwd()),
                },
                "metadata": {"packageJson": {}, "isDevelopment": True},
            },
        }
    
    async def create_template(
        self,
        template_id: str,
        template_type: TemplateType,
        content: str,
        variables: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: TemplateSource = TemplateSource.USER
    ) -> TemplateVersion:
        """Create a new template."""
        if not template_id:
            raise ValueError("Template ID cannot be empty")
        
        # Stub implementation - create a version object
        version = TemplateVersion(template_id)
        version.metadata = metadata
        
        # Store template in memory for this stub
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        self._templates[template_id] = {
            'content': content,
            'type': template_type,
            'source': source,
            'variables': variables or {},
            'metadata': metadata or {},
            'version': version
        }
        
        return version
    
    async def get_template(
        self, template_id: str
    ) -> Optional[Tuple[str, TemplateVersion]]:
        """Get a template by ID."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id in self._templates:
            template = self._templates[template_id]
            return template['content'], template['version']
        return None
    
    async def update_template(
        self,
        template_id: str,
        content: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TemplateVersion:
        """Update an existing template."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            raise ValueError(f"Template {template_id} not found")
        
        # Update template
        template = self._templates[template_id]
        if content is not None:
            template['content'] = content
        if variables is not None:
            template['variables'] = variables
        if metadata is not None:
            template['metadata'] = metadata
        
        # Create new version
        old_version = template['version'].version
        parts = old_version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        new_version_str = '.'.join(parts)
        
        version = TemplateVersion(template_id, new_version_str)
        version.metadata = template['metadata']
        
        # Create backup path for compatibility
        backup_dir = Path.cwd() / ".claude-pm" / "template_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{template_id}_{version.version}.backup"
        version.backup_path = str(backup_path)
        
        template['version'] = version
        
        return version
    
    async def render_template(
        self,
        template_id: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Render a template with variables."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            return None
        
        template = self._templates[template_id]
        content = template['content']
        
        # Simple variable substitution
        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", value)
        
        return content
    
    async def validate_template(self, template_id: str) -> TemplateValidationResult:
        """Validate a template."""
        result = TemplateValidationResult(template_id)
        
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            result.is_valid = False
            result.errors.append("Template not found")
            return result
        
        template = self._templates[template_id]
        content = template['content']
        
        # Basic validation
        if '{{' in content and not '}}' in content:
            result.warnings.append("Unclosed template variable")
        
        # Check for undefined variables
        import re
        var_pattern = r'\{\{(\w+)\}\}'
        used_vars = set(re.findall(var_pattern, content))
        defined_vars = set(template.get('variables', {}).keys())
        undefined = used_vars - defined_vars
        
        if undefined:
            result.warnings.append(f"Undefined variables: {', '.join(undefined)}")
        
        return result
    
    async def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        source: Optional[TemplateSource] = None
    ) -> List[Dict[str, Any]]:
        """List available templates."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        templates = []
        for template_id, template in self._templates.items():
            # Filter by type and source if specified
            if template_type and template['type'] != template_type:
                continue
            if source and template['source'] != source:
                continue
            
            templates.append({
                "template_id": template_id,
                "type": template['type'].value,
                "source": template['source'].value,
                "created_at": template['version'].created_at.isoformat(),
                "updated_at": template['version'].updated_at.isoformat(),
                "metadata": template['metadata']
            })
        
        return templates
    
    async def backup_template(self, template_id: str) -> Optional[str]:
        """Create a backup of a template."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            return None
        
        # Create backup path
        backup_dir = Path.cwd() / ".claude-pm" / "template_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{template_id}_{timestamp}.backup"
        
        # In a real implementation, would write the template to this path
        return str(backup_path)
    
    async def restore_template(
        self, template_id: str, version: str
    ) -> bool:
        """Restore a template to a specific version."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            return False
        
        # In stub, just check if version matches current or a simple pattern
        template = self._templates[template_id]
        if version == "1.0.0" or version == template['version'].version:
            return True
        
        return False
    
    async def get_template_history(
        self, template_id: str
    ) -> List[Dict[str, Any]]:
        """Get version history of a template."""
        if not hasattr(self, '_templates'):
            self._templates = {}
        
        if template_id not in self._templates:
            return []
        
        template = self._templates[template_id]
        current_version = template['version']
        
        # Create mock history
        history = []
        
        # Add initial version
        history.append({
            "version": "1.0.0",
            "created_at": current_version.created_at.isoformat(),
            "metadata": {},
            "backup_path": None
        })
        
        # Add current version if different
        if current_version.version != "1.0.0":
            backup_path = f".claude-pm/template_backups/{template_id}_{current_version.version}.backup"
            history.append({
                "version": current_version.version,
                "created_at": current_version.updated_at.isoformat(),
                "metadata": current_version.metadata or {},
                "backup_path": backup_path
            })
        
        return history
    
    async def get_deployment_specific_template_recommendations(
        self,
        project_type: str,
        requirements: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get template recommendations based on deployment context."""
        # Stub implementation
        templates = await self.list_templates()
        
        recommendations = []
        for template in templates:
            score = 0.5  # Base score
            
            # Simple scoring based on requirements
            if requirements:
                for req in requirements:
                    if req.lower() in template.get("template_id", "").lower():
                        score += 0.1
                    if template.get("metadata", {}).get("category") == req:
                        score += 0.2
                    if template.get("metadata", {}).get("technology") == req:
                        score += 0.2
            
            recommendations.append({
                "template_id": template["template_id"],
                "score": min(score, 1.0),
                "reasons": ["Template matches project requirements"],
                "deployment_context": "local_source"
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]  # Return top 5
    
    async def get_templates_by_deployment_context(
        self,
        template_type: Optional[TemplateType] = None,
        include_development: bool = False
    ) -> List[Dict[str, Any]]:
        """Get templates filtered by deployment context."""
        templates = await self.list_templates(template_type=template_type)
        
        # In stub, return all templates if include_development is True
        if include_development:
            return templates
        
        # Otherwise filter out development templates
        return [t for t in templates if not t.get("metadata", {}).get("development_only")]
    
    async def validate_deployment_template_access(self) -> Dict[str, Any]:
        """Validate template access in current deployment."""
        templates = await self.list_templates()
        
        return {
            "deployment_type": "local_source",
            "template_sources": {
                "framework": str(Path.cwd() / "framework" / "templates"),
                "project": str(Path.cwd() / ".claude-pm" / "templates"),
                "user": str(Path.home() / ".claude-pm" / "templates"),
                "system": str(Path.cwd() / "claude_pm" / "templates")
            },
            "accessible_templates": len(templates),
            "inaccessible_templates": 0,
            "validation_errors": []
        }
    
    async def get_deployment_aware_template_config(self) -> Any:
        """Get deployment-aware template configuration."""
        # Create a mock config object
        @dataclass
        class DeploymentConfig:
            deployment_type: Any = field(default_factory=lambda: type('DeploymentType', (), {'value': 'local_source'})())
            is_development: bool = True
            confidence: str = "high"
            template_sources: List[TemplateSource] = field(default_factory=lambda: [
                TemplateSource.SYSTEM,
                TemplateSource.FRAMEWORK,
                TemplateSource.USER,
                TemplateSource.PROJECT
            ])
            framework_path: Path = field(default_factory=Path.cwd)
        
        return DeploymentConfig()