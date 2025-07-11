#!/usr/bin/env python3
"""
Template Manager Service - CMPM-102: Versioned Template Management
================================================================

This service provides comprehensive template management with versioning,
backup/restore capabilities, and deployment-aware template sourcing.

Key Features:
- Template versioning with backup/restore workflow
- Deployment-aware template sourcing
- Conflict detection and resolution
- Template inheritance and customization
- Integration with CMPM-101 deployment detection
- Cross-platform compatibility

Dependencies:
- CMPM-101 (Deployment Detection System)
"""

import os
import json
import yaml
import time
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging


class TemplateType(Enum):
    """Template types supported by the system."""
    PROJECT = "project"
    AGENT = "agent"
    TICKET = "ticket"
    SCAFFOLDING = "scaffolding"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


class TemplateSource(Enum):
    """Template source locations in hierarchy."""
    SYSTEM = "system"
    FRAMEWORK = "framework"
    USER = "user"
    PROJECT = "project"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    BACKUP_AND_REPLACE = "backup_and_replace"
    MERGE = "merge"
    SKIP = "skip"
    PROMPT_USER = "prompt_user"


@dataclass
class TemplateVersion:
    """Represents a template version with metadata."""
    template_id: str
    version: str
    source: TemplateSource
    created_at: datetime
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    backup_path: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateConflict:
    """Represents a template conflict that needs resolution."""
    template_id: str
    existing_version: TemplateVersion
    new_version: TemplateVersion
    conflict_type: str
    resolution: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class TemplateValidationResult:
    """Results of template validation."""
    is_valid: bool
    template_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class TemplateManager(BaseService):
    """
    Versioned Template Management Service for Claude PM Framework.
    
    This service provides:
    - Template versioning with backup/restore capabilities
    - Deployment-aware template sourcing
    - Template conflict detection and resolution
    - Template inheritance and customization
    - Integration with CMPM-101 deployment detection system
    """
    
    def __init__(self, deployment_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Template Manager.
        
        Args:
            deployment_config: Optional deployment configuration from CMPM-101
        """
        super().__init__(name="template_manager")
        self.logger = setup_logging(__name__)
        
        # Initialize deployment-aware paths
        self.deployment_config = deployment_config or {}
        self._initialize_paths()
        
        # Template registry and version tracking
        self.template_registry = {}
        self.version_registry = {}
        self.conflict_registry = {}
        
        # Configuration
        self.backup_retention_days = 30
        self.max_versions_per_template = 10
        self.auto_backup_enabled = True
        
        # Load existing registries
        self._load_registries()
    
    async def _initialize(self) -> bool:
        """Initialize the Template Manager service."""
        try:
            # Create necessary directories
            self._create_directory_structure()
            
            # Initialize template registry
            await self._initialize_template_registry()
            
            # Validate deployment configuration
            if not self._validate_deployment_config():
                self.logger.warning("Deployment configuration validation failed")
            
            self.logger.info("Template Manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Template Manager: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup the Template Manager service."""
        try:
            # Save registries
            self._save_registries()
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            self.logger.info("Template Manager cleanup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup Template Manager: {e}")
            return False
    
    def _initialize_paths(self):
        """Initialize template paths based on deployment configuration."""
        # Default paths
        self.working_dir = Path.cwd()
        self.framework_path = self.working_dir
        
        # Use deployment config if available
        if self.deployment_config:
            paths = self.deployment_config.get("paths", {})
            self.framework_path = Path(paths.get("framework", self.working_dir))
            self.working_dir = Path(paths.get("working", self.working_dir))
        
        # Template source paths (hierarchical)
        self.template_paths = {
            TemplateSource.SYSTEM: self.framework_path / "claude_pm" / "templates",
            TemplateSource.FRAMEWORK: self.framework_path / "framework" / "templates",
            TemplateSource.USER: Path.home() / ".claude-pm" / "templates",
            TemplateSource.PROJECT: self.working_dir / ".claude-pm" / "templates"
        }
        
        # Template manager paths
        self.template_manager_dir = self.working_dir / ".claude-pm" / "template_manager"
        self.versions_dir = self.template_manager_dir / "versions"
        self.backups_dir = self.template_manager_dir / "backups"
        self.registry_dir = self.template_manager_dir / "registry"
        self.conflicts_dir = self.template_manager_dir / "conflicts"
        
        # Registry files
        self.template_registry_file = self.registry_dir / "templates.json"
        self.version_registry_file = self.registry_dir / "versions.json"
        self.conflict_registry_file = self.registry_dir / "conflicts.json"
    
    def _create_directory_structure(self):
        """Create the template manager directory structure."""
        directories = [
            self.template_manager_dir,
            self.versions_dir,
            self.backups_dir,
            self.registry_dir,
            self.conflicts_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create template source directories if they don't exist
        for source, path in self.template_paths.items():
            if source in [TemplateSource.USER, TemplateSource.PROJECT]:
                path.mkdir(parents=True, exist_ok=True)
    
    def _load_registries(self):
        """Load template registries from disk."""
        try:
            # Load template registry
            if self.template_registry_file.exists():
                with open(self.template_registry_file, 'r') as f:
                    self.template_registry = json.load(f)
            
            # Load version registry
            if self.version_registry_file.exists():
                with open(self.version_registry_file, 'r') as f:
                    version_data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for template_id, versions in version_data.items():
                        self.version_registry[template_id] = []
                        for version_info in versions:
                            version_info['created_at'] = datetime.fromisoformat(version_info['created_at'])
                            self.version_registry[template_id].append(TemplateVersion(**version_info))
            
            # Load conflict registry
            if self.conflict_registry_file.exists():
                with open(self.conflict_registry_file, 'r') as f:
                    conflict_data = json.load(f)
                    # Convert conflict data to objects
                    for conflict_id, conflict_info in conflict_data.items():
                        conflict_info['existing_version']['created_at'] = datetime.fromisoformat(
                            conflict_info['existing_version']['created_at'])
                        conflict_info['new_version']['created_at'] = datetime.fromisoformat(
                            conflict_info['new_version']['created_at'])
                        
                        if conflict_info.get('resolved_at'):
                            conflict_info['resolved_at'] = datetime.fromisoformat(conflict_info['resolved_at'])
                        
                        self.conflict_registry[conflict_id] = TemplateConflict(**conflict_info)
            
        except Exception as e:
            self.logger.error(f"Failed to load registries: {e}")
    
    def _save_registries(self):
        """Save template registries to disk."""
        try:
            # Save template registry
            with open(self.template_registry_file, 'w') as f:
                json.dump(self.template_registry, f, indent=2)
            
            # Save version registry
            version_data = {}
            for template_id, versions in self.version_registry.items():
                version_data[template_id] = []
                for version in versions:
                    version_dict = {
                        'template_id': version.template_id,
                        'version': version.version,
                        'source': version.source.value,
                        'created_at': version.created_at.isoformat(),
                        'checksum': version.checksum,
                        'metadata': version.metadata,
                        'backup_path': version.backup_path,
                        'variables': version.variables
                    }
                    version_data[template_id].append(version_dict)
            
            with open(self.version_registry_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            # Save conflict registry
            conflict_data = {}
            for conflict_id, conflict in self.conflict_registry.items():
                existing_version = {
                    'template_id': conflict.existing_version.template_id,
                    'version': conflict.existing_version.version,
                    'source': conflict.existing_version.source.value,
                    'created_at': conflict.existing_version.created_at.isoformat(),
                    'checksum': conflict.existing_version.checksum,
                    'metadata': conflict.existing_version.metadata,
                    'backup_path': conflict.existing_version.backup_path,
                    'variables': conflict.existing_version.variables
                }
                
                new_version = {
                    'template_id': conflict.new_version.template_id,
                    'version': conflict.new_version.version,
                    'source': conflict.new_version.source.value,
                    'created_at': conflict.new_version.created_at.isoformat(),
                    'checksum': conflict.new_version.checksum,
                    'metadata': conflict.new_version.metadata,
                    'backup_path': conflict.new_version.backup_path,
                    'variables': conflict.new_version.variables
                }
                
                conflict_data[conflict_id] = {
                    'template_id': conflict.template_id,
                    'existing_version': existing_version,
                    'new_version': new_version,
                    'conflict_type': conflict.conflict_type,
                    'resolution': conflict.resolution.value if conflict.resolution else None,
                    'resolved_at': conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                    'notes': conflict.notes
                }
            
            with open(self.conflict_registry_file, 'w') as f:
                json.dump(conflict_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save registries: {e}")
    
    async def _initialize_template_registry(self):
        """Initialize template registry by discovering existing templates."""
        try:
            self.logger.info("Scanning template sources for existing templates...")
            
            # Scan each template source
            for source, path in self.template_paths.items():
                if path.exists():
                    await self._scan_template_source(source, path)
            
            # Save initial registry
            self._save_registries()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize template registry: {e}")
    
    async def _scan_template_source(self, source: TemplateSource, path: Path):
        """Scan a template source directory for templates."""
        try:
            if not path.exists():
                return
            
            # Scan for template files
            template_patterns = [
                "*.template",
                "*.tmpl",
                "*.yaml",
                "*.yml",
                "*.json",
                "*.md.template"
            ]
            
            for pattern in template_patterns:
                for template_file in path.glob(f"**/{pattern}"):
                    if template_file.is_file():
                        await self._register_discovered_template(source, template_file)
            
        except Exception as e:
            self.logger.error(f"Failed to scan template source {source}: {e}")
    
    async def _register_discovered_template(self, source: TemplateSource, template_file: Path):
        """Register a discovered template file."""
        try:
            # Generate template ID
            relative_path = template_file.relative_to(self.template_paths[source])
            template_id = str(relative_path).replace(os.sep, '/')
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(template_file)
            
            # Create version
            version = TemplateVersion(
                template_id=template_id,
                version="1.0.0",
                source=source,
                created_at=datetime.now(),
                checksum=checksum,
                metadata={
                    "original_path": str(template_file),
                    "file_size": template_file.stat().st_size,
                    "discovered": True
                }
            )
            
            # Register template
            if template_id not in self.template_registry:
                self.template_registry[template_id] = {
                    "template_id": template_id,
                    "name": template_file.stem,
                    "type": self._detect_template_type(template_file),
                    "source": source.value,
                    "path": str(template_file),
                    "current_version": version.version,
                    "created_at": version.created_at.isoformat(),
                    "updated_at": version.created_at.isoformat()
                }
                
                # Register version
                if template_id not in self.version_registry:
                    self.version_registry[template_id] = []
                self.version_registry[template_id].append(version)
                
                self.logger.debug(f"Registered template: {template_id} from {source}")
            
        except Exception as e:
            self.logger.error(f"Failed to register discovered template {template_file}: {e}")
    
    def _detect_template_type(self, template_file: Path) -> TemplateType:
        """Detect template type from file path and content."""
        path_str = str(template_file).lower()
        
        if "agent" in path_str:
            return TemplateType.AGENT
        elif "ticket" in path_str or "issue" in path_str or "epic" in path_str:
            return TemplateType.TICKET
        elif "scaffolding" in path_str:
            return TemplateType.SCAFFOLDING
        elif "config" in path_str:
            return TemplateType.CONFIGURATION
        elif "doc" in path_str or "readme" in path_str:
            return TemplateType.DOCUMENTATION
        else:
            return TemplateType.PROJECT
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _validate_deployment_config(self) -> bool:
        """Validate deployment configuration."""
        try:
            if not self.deployment_config:
                return False
            
            # Check required paths
            required_paths = ["framework", "working"]
            for path_name in required_paths:
                if path_name not in self.deployment_config.get("paths", {}):
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to validate deployment config: {e}")
            return False
    
    # Public API Methods
    
    async def create_template(
        self,
        template_id: str,
        template_type: TemplateType,
        content: str,
        variables: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        source: TemplateSource = TemplateSource.PROJECT
    ) -> TemplateVersion:
        """
        Create a new template with versioning.
        
        Args:
            template_id: Unique identifier for the template
            template_type: Type of template
            content: Template content
            variables: Template variables
            metadata: Additional metadata
            source: Template source location
            
        Returns:
            TemplateVersion object for the created template
        """
        try:
            # Validate input
            if not template_id or not content:
                raise ValueError("Template ID and content are required")
            
            # Check for existing template
            if template_id in self.template_registry:
                # Handle as update
                return await self.update_template(template_id, content, variables, metadata)
            
            # Create template directory
            template_dir = self.template_paths[source] / template_type.value
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # Create template file
            template_file = template_dir / f"{template_id}.template"
            template_file.write_text(content)
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(template_file)
            
            # Create version
            version = TemplateVersion(
                template_id=template_id,
                version="1.0.0",
                source=source,
                created_at=datetime.now(),
                checksum=checksum,
                metadata=metadata or {},
                variables=variables or {}
            )
            
            # Register template
            self.template_registry[template_id] = {
                "template_id": template_id,
                "name": template_id,
                "type": template_type.value,
                "source": source.value,
                "path": str(template_file),
                "current_version": version.version,
                "created_at": version.created_at.isoformat(),
                "updated_at": version.created_at.isoformat()
            }
            
            # Register version
            if template_id not in self.version_registry:
                self.version_registry[template_id] = []
            self.version_registry[template_id].append(version)
            
            # Save registries
            self._save_registries()
            
            self.logger.info(f"Created template: {template_id} v{version.version}")
            return version
            
        except Exception as e:
            self.logger.error(f"Failed to create template {template_id}: {e}")
            raise
    
    async def update_template(
        self,
        template_id: str,
        content: str,
        variables: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.BACKUP_AND_REPLACE
    ) -> TemplateVersion:
        """
        Update an existing template with versioning and conflict resolution.
        
        Args:
            template_id: Template identifier
            content: New template content
            variables: Updated template variables
            metadata: Updated metadata
            conflict_resolution: Strategy for handling conflicts
            
        Returns:
            TemplateVersion object for the updated template
        """
        try:
            # Check if template exists
            if template_id not in self.template_registry:
                raise ValueError(f"Template {template_id} not found")
            
            # Get current template info
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            
            # Calculate new checksum
            current_checksum = self._calculate_file_checksum(template_path)
            new_checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if content has actually changed
            if current_checksum == new_checksum:
                self.logger.info(f"Template {template_id} unchanged, skipping update")
                return self.version_registry[template_id][-1]
            
            # Create backup if auto-backup is enabled
            backup_path = None
            if self.auto_backup_enabled:
                backup_path = await self._create_backup(template_id, template_path)
            
            # Handle conflicts
            if len(self.version_registry[template_id]) > 0:
                current_version = self.version_registry[template_id][-1]
                if await self._detect_conflict(template_id, current_version, content):
                    conflict = await self._handle_conflict(
                        template_id, current_version, content, conflict_resolution
                    )
                    if conflict.resolution == ConflictResolution.SKIP:
                        self.logger.info(f"Skipping template update due to conflict: {template_id}")
                        return current_version
            
            # Create new version
            new_version_number = self._generate_next_version(template_id)
            new_version = TemplateVersion(
                template_id=template_id,
                version=new_version_number,
                source=TemplateSource(template_info["source"]),
                created_at=datetime.now(),
                checksum=new_checksum,
                metadata=metadata or {},
                variables=variables or {},
                backup_path=backup_path
            )
            
            # Update template file
            template_path.write_text(content)
            
            # Update registries
            self.template_registry[template_id]["current_version"] = new_version.version
            self.template_registry[template_id]["updated_at"] = new_version.created_at.isoformat()
            
            self.version_registry[template_id].append(new_version)
            
            # Cleanup old versions if needed
            await self._cleanup_old_versions(template_id)
            
            # Save registries
            self._save_registries()
            
            self.logger.info(f"Updated template: {template_id} v{new_version.version}")
            return new_version
            
        except Exception as e:
            self.logger.error(f"Failed to update template {template_id}: {e}")
            raise
    
    async def get_template(
        self,
        template_id: str,
        version: Optional[str] = None,
        source: Optional[TemplateSource] = None
    ) -> Optional[Tuple[str, TemplateVersion]]:
        """
        Get template content and version information.
        
        Args:
            template_id: Template identifier
            version: Specific version to retrieve (latest if None)
            source: Preferred template source
            
        Returns:
            Tuple of (content, version) or None if not found
        """
        try:
            # Check if template exists
            if template_id not in self.template_registry:
                return None
            
            # Get version
            if version:
                template_version = self._get_specific_version(template_id, version)
            else:
                template_version = self._get_latest_version(template_id)
            
            if not template_version:
                return None
            
            # Get template path
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            
            # Read content
            if template_path.exists():
                content = template_path.read_text()
                return content, template_version
            else:
                # Try to restore from backup
                if template_version.backup_path:
                    backup_path = Path(template_version.backup_path)
                    if backup_path.exists():
                        content = backup_path.read_text()
                        return content, template_version
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get template {template_id}: {e}")
            return None
    
    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        version: Optional[str] = None
    ) -> Optional[str]:
        """
        Render template with provided variables.
        
        Args:
            template_id: Template identifier
            variables: Variables to substitute in template
            version: Specific version to render
            
        Returns:
            Rendered template content or None if error
        """
        try:
            # Get template
            template_data = await self.get_template(template_id, version)
            if not template_data:
                return None
            
            content, template_version = template_data
            
            # Merge variables with template defaults
            merged_variables = {}
            merged_variables.update(template_version.variables)
            merged_variables.update(variables)
            
            # Simple template rendering (can be enhanced with Jinja2 if needed)
            rendered_content = content
            for key, value in merged_variables.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
            
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"Failed to render template {template_id}: {e}")
            return None
    
    async def backup_template(self, template_id: str) -> Optional[str]:
        """
        Create a backup of a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Backup file path or None if failed
        """
        try:
            if template_id not in self.template_registry:
                return None
            
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            
            return await self._create_backup(template_id, template_path)
            
        except Exception as e:
            self.logger.error(f"Failed to backup template {template_id}: {e}")
            return None
    
    async def restore_template(
        self,
        template_id: str,
        version: str
    ) -> bool:
        """
        Restore a template from a specific version.
        
        Args:
            template_id: Template identifier
            version: Version to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get version
            template_version = self._get_specific_version(template_id, version)
            if not template_version:
                return False
            
            # Get current template path
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            
            # Find backup or version file
            restore_source = None
            if template_version.backup_path:
                backup_path = Path(template_version.backup_path)
                if backup_path.exists():
                    restore_source = backup_path
            
            # Try version-specific storage
            if not restore_source:
                version_file = self.versions_dir / template_id / f"{version}.template"
                if version_file.exists():
                    restore_source = version_file
            
            if not restore_source:
                self.logger.error(f"No backup found for template {template_id} v{version}")
                return False
            
            # Create backup of current version before restore
            await self._create_backup(template_id, template_path)
            
            # Restore from backup
            shutil.copy2(restore_source, template_path)
            
            # Update registry
            self.template_registry[template_id]["current_version"] = version
            self.template_registry[template_id]["updated_at"] = datetime.now().isoformat()
            
            # Save registries
            self._save_registries()
            
            self.logger.info(f"Restored template {template_id} to version {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore template {template_id}: {e}")
            return False
    
    async def validate_template(
        self,
        template_id: str,
        version: Optional[str] = None
    ) -> TemplateValidationResult:
        """
        Validate a template for correctness and completeness.
        
        Args:
            template_id: Template identifier
            version: Specific version to validate
            
        Returns:
            TemplateValidationResult object
        """
        try:
            result = TemplateValidationResult(
                is_valid=True,
                template_id=template_id
            )
            
            # Get template
            template_data = await self.get_template(template_id, version)
            if not template_data:
                result.is_valid = False
                result.errors.append("Template not found")
                return result
            
            content, template_version = template_data
            
            # Basic validation
            if not content.strip():
                result.is_valid = False
                result.errors.append("Template content is empty")
            
            # Check for unclosed template variables
            import re
            unclosed_vars = re.findall(r'\{\{[^}]*$', content)
            if unclosed_vars:
                result.is_valid = False
                result.errors.append(f"Unclosed template variables: {unclosed_vars}")
            
            # Check for undefined variables
            variables_in_template = set(re.findall(r'\{\{(\w+)\}\}', content))
            defined_variables = set(template_version.variables.keys())
            undefined_vars = variables_in_template - defined_variables
            if undefined_vars:
                result.warnings.append(f"Undefined variables: {list(undefined_vars)}")
                result.suggestions.append("Consider defining default values for these variables")
            
            # Check file existence
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            if not template_path.exists():
                result.is_valid = False
                result.errors.append("Template file not found on disk")
            
            # Validate checksum
            if template_path.exists():
                current_checksum = self._calculate_file_checksum(template_path)
                if current_checksum != template_version.checksum:
                    result.warnings.append("Template file checksum mismatch")
                    result.suggestions.append("Template may have been modified outside of version control")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate template {template_id}: {e}")
            return TemplateValidationResult(
                is_valid=False,
                template_id=template_id,
                errors=[f"Validation failed: {str(e)}"]
            )
    
    async def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        source: Optional[TemplateSource] = None
    ) -> List[Dict[str, Any]]:
        """
        List all templates with optional filtering.
        
        Args:
            template_type: Filter by template type
            source: Filter by template source
            
        Returns:
            List of template information dictionaries
        """
        try:
            templates = []
            
            for template_id, template_info in self.template_registry.items():
                # Apply filters
                if template_type and template_info["type"] != template_type.value:
                    continue
                if source and template_info["source"] != source.value:
                    continue
                
                # Get version information
                versions = self.version_registry.get(template_id, [])
                current_version = versions[-1] if versions else None
                
                template_summary = {
                    "template_id": template_id,
                    "name": template_info["name"],
                    "type": template_info["type"],
                    "source": template_info["source"],
                    "current_version": template_info["current_version"],
                    "total_versions": len(versions),
                    "created_at": template_info["created_at"],
                    "updated_at": template_info["updated_at"],
                    "has_backup": current_version.backup_path is not None if current_version else False
                }
                
                templates.append(template_summary)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to list templates: {e}")
            return []
    
    async def get_template_history(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of version information dictionaries
        """
        try:
            if template_id not in self.version_registry:
                return []
            
            versions = self.version_registry[template_id]
            history = []
            
            for version in versions:
                version_info = {
                    "version": version.version,
                    "source": version.source.value,
                    "created_at": version.created_at.isoformat(),
                    "checksum": version.checksum,
                    "metadata": version.metadata,
                    "has_backup": version.backup_path is not None,
                    "backup_path": version.backup_path
                }
                history.append(version_info)
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get template history {template_id}: {e}")
            return []
    
    # Helper Methods
    
    async def _create_backup(self, template_id: str, template_path: Path) -> Optional[str]:
        """Create a backup of a template file."""
        try:
            if not template_path.exists():
                return None
            
            # Create backup directory
            backup_dir = self.backups_dir / template_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{template_id}_{timestamp}.backup"
            backup_path = backup_dir / backup_filename
            
            # Copy file
            shutil.copy2(template_path, backup_path)
            
            self.logger.debug(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {template_id}: {e}")
            return None
    
    async def _detect_conflict(
        self,
        template_id: str,
        current_version: TemplateVersion,
        new_content: str
    ) -> bool:
        """Detect if there's a conflict with the update."""
        try:
            # Get current template content
            template_info = self.template_registry[template_id]
            template_path = Path(template_info["path"])
            
            if not template_path.exists():
                return False
            
            current_content = template_path.read_text()
            current_checksum = self._calculate_file_checksum(template_path)
            
            # Check if file has been modified since last version
            if current_checksum != current_version.checksum:
                return True
            
            # Check if new content is significantly different
            new_checksum = hashlib.sha256(new_content.encode()).hexdigest()
            if current_checksum != new_checksum:
                # Could add more sophisticated conflict detection here
                # For now, any change is considered a potential conflict
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to detect conflict for {template_id}: {e}")
            return False
    
    async def _handle_conflict(
        self,
        template_id: str,
        current_version: TemplateVersion,
        new_content: str,
        resolution: ConflictResolution
    ) -> TemplateConflict:
        """Handle a template conflict based on resolution strategy."""
        try:
            # Create new version object for conflict
            new_version = TemplateVersion(
                template_id=template_id,
                version=self._generate_next_version(template_id),
                source=current_version.source,
                created_at=datetime.now(),
                checksum=hashlib.sha256(new_content.encode()).hexdigest(),
                metadata={}
            )
            
            # Create conflict object
            conflict = TemplateConflict(
                template_id=template_id,
                existing_version=current_version,
                new_version=new_version,
                conflict_type="content_modification",
                resolution=resolution
            )
            
            # Apply resolution
            if resolution == ConflictResolution.BACKUP_AND_REPLACE:
                # Create backup and proceed with update
                template_info = self.template_registry[template_id]
                template_path = Path(template_info["path"])
                backup_path = await self._create_backup(template_id, template_path)
                conflict.notes.append(f"Backup created at: {backup_path}")
                conflict.resolved_at = datetime.now()
                
            elif resolution == ConflictResolution.SKIP:
                # Skip update
                conflict.notes.append("Update skipped due to conflict")
                conflict.resolved_at = datetime.now()
                
            elif resolution == ConflictResolution.MERGE:
                # Attempt merge (placeholder for future implementation)
                conflict.notes.append("Merge attempted - manual review may be needed")
                conflict.resolved_at = datetime.now()
            
            # Store conflict
            conflict_id = f"{template_id}_{int(time.time())}"
            self.conflict_registry[conflict_id] = conflict
            
            return conflict
            
        except Exception as e:
            self.logger.error(f"Failed to handle conflict for {template_id}: {e}")
            raise
    
    def _get_specific_version(self, template_id: str, version: str) -> Optional[TemplateVersion]:
        """Get a specific version of a template."""
        if template_id not in self.version_registry:
            return None
        
        for template_version in self.version_registry[template_id]:
            if template_version.version == version:
                return template_version
        
        return None
    
    def _get_latest_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the latest version of a template."""
        if template_id not in self.version_registry:
            return None
        
        versions = self.version_registry[template_id]
        return versions[-1] if versions else None
    
    def _generate_next_version(self, template_id: str) -> str:
        """Generate the next version number for a template."""
        if template_id not in self.version_registry:
            return "1.0.0"
        
        versions = self.version_registry[template_id]
        if not versions:
            return "1.0.0"
        
        # Get last version
        last_version = versions[-1].version
        
        # Simple version increment (major.minor.patch)
        try:
            parts = last_version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                return f"{major}.{minor}.{patch + 1}"
            else:
                return f"{last_version}.1"
        except ValueError:
            return f"{last_version}.1"
    
    async def _cleanup_old_versions(self, template_id: str):
        """Cleanup old versions if exceeding maximum count."""
        if template_id not in self.version_registry:
            return
        
        versions = self.version_registry[template_id]
        if len(versions) <= self.max_versions_per_template:
            return
        
        # Remove oldest versions
        excess_count = len(versions) - self.max_versions_per_template
        for i in range(excess_count):
            old_version = versions.pop(0)
            
            # Remove backup if exists
            if old_version.backup_path:
                backup_path = Path(old_version.backup_path)
                if backup_path.exists():
                    backup_path.unlink()
    
    async def _cleanup_old_backups(self):
        """Cleanup old backups based on retention policy."""
        try:
            if not self.backups_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            for backup_dir in self.backups_dir.iterdir():
                if backup_dir.is_dir():
                    for backup_file in backup_dir.iterdir():
                        if backup_file.is_file():
                            # Check file modification time
                            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if mtime < cutoff_date:
                                backup_file.unlink()
                                self.logger.debug(f"Removed old backup: {backup_file}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")