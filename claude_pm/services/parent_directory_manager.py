#!/usr/bin/env python3
"""
Parent Directory Manager Service - CMPM-104: Parent Directory Template Installation
================================================================================

This service provides comprehensive parent directory template management with
deployment awareness, building on CMPM-101, CMPM-102, and CMPM-103.

Key Features:
- Parent directory CLAUDE.md management with deployment awareness
- Template installation workflow with conflict resolution
- Existing file detection and backup system
- Version control integration
- Cross-platform compatibility
- Integration with all previous CMPM implementations

Dependencies:
- CMPM-101 (Deployment Detection System)
- CMPM-102 (Versioned Template Management)
- CMPM-103 (Dependency Management)
"""

import os
import json
import shutil
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.base_service import BaseService
from ..core.logging_config import setup_logging
from .template_manager import TemplateManager, TemplateVersion, TemplateSource, TemplateType
from .dependency_manager import DependencyManager


class ParentDirectoryContext(Enum):
    """Context types for parent directory management."""
    DEPLOYMENT_ROOT = "deployment_root"
    PROJECT_COLLECTION = "project_collection"
    WORKSPACE_ROOT = "workspace_root"
    USER_HOME = "user_home"
    CUSTOM = "custom"


class ParentDirectoryAction(Enum):
    """Actions for parent directory operations."""
    INSTALL = "install"
    UPDATE = "update"
    BACKUP = "backup"
    RESTORE = "restore"
    VALIDATE = "validate"
    REMOVE = "remove"


@dataclass
class ParentDirectoryConfig:
    """Configuration for parent directory management."""
    target_directory: Path
    context: ParentDirectoryContext
    template_id: str
    template_variables: Dict[str, Any] = field(default_factory=dict)
    backup_enabled: bool = True
    version_control: bool = True
    conflict_resolution: str = "backup_and_replace"
    deployment_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParentDirectoryStatus:
    """Status information for parent directory files."""
    file_path: Path
    exists: bool
    is_managed: bool
    current_version: Optional[str] = None
    last_modified: Optional[datetime] = None
    checksum: Optional[str] = None
    backup_available: bool = False
    template_source: Optional[str] = None
    deployment_context: Optional[str] = None


@dataclass
class ParentDirectoryOperation:
    """Result of a parent directory operation."""
    action: ParentDirectoryAction
    target_path: Path
    success: bool
    template_id: Optional[str] = None
    version: Optional[str] = None
    backup_path: Optional[Path] = None
    error_message: Optional[str] = None
    changes_made: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ParentDirectoryManager(BaseService):
    """
    Parent Directory Template Management Service for Claude PM Framework.
    
    This service provides:
    - Parent directory CLAUDE.md management with deployment awareness
    - Template installation workflow with conflict resolution
    - Existing file detection and backup system
    - Version control integration
    - Integration with CMPM-101, CMPM-102, and CMPM-103
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Parent Directory Manager.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(name="parent_directory_manager", config=config)
        self.logger = setup_logging(__name__)
        
        # Integration with other CMPM services
        self.template_manager: Optional[TemplateManager] = None
        self.dependency_manager: Optional[DependencyManager] = None
        
        # Parent directory management state
        self.managed_directories: Dict[str, ParentDirectoryConfig] = {}
        self.operation_history: List[ParentDirectoryOperation] = []
        
        # Configuration
        self.backup_retention_days = self.get_config("backup_retention_days", 30)
        self.auto_backup_enabled = self.get_config("auto_backup_enabled", True)
        self.version_control_enabled = self.get_config("version_control_enabled", True)
        self.deployment_aware = self.get_config("deployment_aware", True)
        
        # Working paths
        self.working_dir = Path.cwd()
        self.framework_path = self.working_dir
        self.parent_directory_manager_dir = self.working_dir / ".claude-pm" / "parent_directory_manager"
        
        # Initialize paths
        self._initialize_paths()
    
    async def _initialize(self) -> None:
        """Initialize the Parent Directory Manager service."""
        self.logger.info("Initializing Parent Directory Manager...")
        
        try:
            # Create directory structure
            self._create_directory_structure()
            
            # Initialize CMPM integrations
            await self._initialize_cmpm_integrations()
            
            # Load existing configurations
            await self._load_managed_directories()
            
            # Validate deployment context
            await self._validate_deployment_context()
            
            self.logger.info("Parent Directory Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Parent Directory Manager: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup the Parent Directory Manager service."""
        self.logger.info("Cleaning up Parent Directory Manager...")
        
        try:
            # Save current state
            await self._save_managed_directories()
            
            # Cleanup temporary files
            await self._cleanup_temporary_files()
            
            # Close CMPM integrations
            if self.template_manager:
                await self.template_manager._cleanup()
            
            if self.dependency_manager:
                await self.dependency_manager._cleanup()
            
            self.logger.info("Parent Directory Manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup Parent Directory Manager: {e}")
    
    def _initialize_paths(self):
        """Initialize parent directory manager paths."""
        # Manager directories
        self.backups_dir = self.parent_directory_manager_dir / "backups"
        self.configs_dir = self.parent_directory_manager_dir / "configs"
        self.versions_dir = self.parent_directory_manager_dir / "versions"
        self.logs_dir = self.parent_directory_manager_dir / "logs"
        
        # Configuration files
        self.managed_directories_file = self.configs_dir / "managed_directories.json"
        self.operation_history_file = self.logs_dir / "operation_history.json"
    
    def _create_directory_structure(self):
        """Create the parent directory manager directory structure."""
        directories = [
            self.parent_directory_manager_dir,
            self.backups_dir,
            self.configs_dir,
            self.versions_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _initialize_cmpm_integrations(self):
        """Initialize integrations with other CMPM services."""
        try:
            # Initialize Template Manager (CMPM-102)
            self.template_manager = TemplateManager()
            await self.template_manager._initialize()
            
            # Initialize Dependency Manager (CMPM-103)
            self.dependency_manager = DependencyManager()
            await self.dependency_manager._initialize()
            
            self.logger.info("CMPM integrations initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CMPM integrations: {e}")
            # Continue without full integration
            self.template_manager = None
            self.dependency_manager = None
    
    async def _load_managed_directories(self):
        """Load existing managed directories configuration."""
        try:
            if self.managed_directories_file.exists():
                with open(self.managed_directories_file, 'r') as f:
                    data = json.load(f)
                
                # Convert loaded data to ParentDirectoryConfig objects
                for key, config_data in data.items():
                    config = ParentDirectoryConfig(
                        target_directory=Path(config_data["target_directory"]),
                        context=ParentDirectoryContext(config_data["context"]),
                        template_id=config_data["template_id"],
                        template_variables=config_data.get("template_variables", {}),
                        backup_enabled=config_data.get("backup_enabled", True),
                        version_control=config_data.get("version_control", True),
                        conflict_resolution=config_data.get("conflict_resolution", "backup_and_replace"),
                        deployment_metadata=config_data.get("deployment_metadata", {})
                    )
                    self.managed_directories[key] = config
                
                self.logger.info(f"Loaded {len(self.managed_directories)} managed directories")
        
        except Exception as e:
            self.logger.error(f"Failed to load managed directories: {e}")
    
    async def _save_managed_directories(self):
        """Save managed directories configuration."""
        try:
            # Convert ParentDirectoryConfig objects to serializable format
            data = {}
            for key, config in self.managed_directories.items():
                data[key] = {
                    "target_directory": str(config.target_directory),
                    "context": config.context.value,
                    "template_id": config.template_id,
                    "template_variables": config.template_variables,
                    "backup_enabled": config.backup_enabled,
                    "version_control": config.version_control,
                    "conflict_resolution": config.conflict_resolution,
                    "deployment_metadata": config.deployment_metadata
                }
            
            with open(self.managed_directories_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("Managed directories configuration saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save managed directories: {e}")
    
    async def _validate_deployment_context(self):
        """Validate deployment context using CMPM-101."""
        try:
            if not self.deployment_aware:
                return
            
            # Use dependency manager to get deployment context
            if self.dependency_manager:
                deployment_config = getattr(self.dependency_manager, 'deployment_config', None)
                if deployment_config:
                    self.deployment_context = deployment_config
                    self.logger.info(f"Deployment context validated: {deployment_config.get('strategy', 'unknown')}")
                else:
                    self.logger.warning("No deployment context available from dependency manager")
            else:
                self.logger.warning("Dependency manager not available for deployment context")
        
        except Exception as e:
            self.logger.error(f"Failed to validate deployment context: {e}")
    
    async def _cleanup_temporary_files(self):
        """Cleanup temporary files and old backups."""
        try:
            # Clean up old backups
            if self.backups_dir.exists():
                cutoff_date = datetime.now().timestamp() - (self.backup_retention_days * 24 * 60 * 60)
                
                for backup_file in self.backups_dir.rglob("*"):
                    if backup_file.is_file():
                        file_mtime = backup_file.stat().st_mtime
                        if file_mtime < cutoff_date:
                            backup_file.unlink()
                            self.logger.debug(f"Removed old backup: {backup_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup temporary files: {e}")
    
    # Public API Methods
    
    async def register_parent_directory(
        self,
        target_directory: Path,
        context: ParentDirectoryContext,
        template_id: str,
        template_variables: Dict[str, Any] = None,
        **kwargs
    ) -> bool:
        """
        Register a parent directory for management.
        
        Args:
            target_directory: Directory to manage
            context: Context type for the directory
            template_id: Template to use for management
            template_variables: Variables for template rendering
            **kwargs: Additional configuration options
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate inputs
            if not target_directory.exists():
                raise ValueError(f"Target directory does not exist: {target_directory}")
            
            if not target_directory.is_dir():
                raise ValueError(f"Target path is not a directory: {target_directory}")
            
            # Create configuration
            config = ParentDirectoryConfig(
                target_directory=target_directory,
                context=context,
                template_id=template_id,
                template_variables=template_variables or {},
                backup_enabled=kwargs.get("backup_enabled", True),
                version_control=kwargs.get("version_control", True),
                conflict_resolution=kwargs.get("conflict_resolution", "backup_and_replace"),
                deployment_metadata=kwargs.get("deployment_metadata", {})
            )
            
            # Register the directory
            directory_key = str(target_directory)
            self.managed_directories[directory_key] = config
            
            # Save configuration
            await self._save_managed_directories()
            
            self.logger.info(f"Registered parent directory: {target_directory} with template {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register parent directory {target_directory}: {e}")
            return False
    
    async def install_template_to_parent_directory(
        self,
        target_directory: Path,
        template_id: str,
        template_variables: Dict[str, Any] = None,
        force: bool = False
    ) -> ParentDirectoryOperation:
        """
        Install a template to a parent directory with version checking.
        
        Args:
            target_directory: Directory to install template to
            template_id: Template to install
            template_variables: Variables for template rendering
            force: Force installation even if version is current (overrides version checking)
            
        Returns:
            ParentDirectoryOperation result
        """
        try:
            # FIXED: Get template from deployment framework path
            content, template_version = await self._get_framework_template(template_id)
            if not content:
                # Fallback to template manager if framework template not found
                if not self.template_manager:
                    raise RuntimeError("Template manager not available and framework template not found")
                
                template_data = await self.template_manager.get_template(template_id)
                if not template_data:
                    raise ValueError(f"Template not found: {template_id}")
                
                content, template_version = template_data
            
            # Determine target file path
            target_file = target_directory / "CLAUDE.md"
            
            # Initialize backup_path
            backup_path = None
            
            # Version checking is now done after template rendering
            # to ensure we have the complete template with variables
            
            # Check if file exists and handle conflicts
            if target_file.exists() and not force:
                existing_content = target_file.read_text()
                existing_checksum = hashlib.sha256(existing_content.encode()).hexdigest()
                
                # Create backup if enabled
                if self.auto_backup_enabled:
                    backup_path = await self._create_backup(target_file)
            
            # Render template with variables including deployment context
            merged_variables = self._get_deployment_template_variables()
            if template_version and hasattr(template_version, 'variables'):
                merged_variables.update(template_version.variables)
            merged_variables.update(template_variables or {})
            
            # Add CLAUDE_MD_VERSION to template variables if not present
            if 'CLAUDE_MD_VERSION' not in merged_variables:
                # Generate temporary content for comparison first
                framework_version = merged_variables.get('FRAMEWORK_VERSION', '4.5.1')
                temp_variables = merged_variables.copy()
                temp_variables['CLAUDE_MD_VERSION'] = 'TEMP'  # Placeholder for template rendering
                
                # Render template with placeholder to get content for comparison
                temp_content = await self._render_template_content(content, temp_variables)
                
                # Generate version based on content comparison
                claude_md_version = self._generate_next_claude_md_version(target_file, framework_version, temp_content)
                merged_variables['CLAUDE_MD_VERSION'] = claude_md_version
                
                self.logger.info(f"🔢 Generated CLAUDE.md version: {claude_md_version}")
                self.logger.info(f"   • Framework version: {framework_version}")
                self.logger.info(f"   • Target file: {target_file}")
            
            # Direct template rendering with handlebars substitution
            rendered_content = await self._render_template_content(content, merged_variables)
            
            if not rendered_content:
                raise RuntimeError("Failed to render template")
            
            # Check if deployment should be skipped based on version comparison
            should_skip, skip_reason = self._should_skip_deployment(target_file, rendered_content, force)
            if should_skip:
                # Return successful operation but with warning about skipping
                operation = ParentDirectoryOperation(
                    action=ParentDirectoryAction.INSTALL,
                    target_path=target_file,
                    success=True,
                    template_id=template_id,
                    version=template_version.version if template_version else None,
                    warnings=[f"Deployment skipped: {skip_reason}"]
                )
                
                self.logger.info(f"Skipped template installation: {skip_reason}")
                return operation
            
            # Write the rendered content
            target_file.write_text(rendered_content)
            
            # Create operation result
            operation = ParentDirectoryOperation(
                action=ParentDirectoryAction.INSTALL,
                target_path=target_file,
                success=True,
                template_id=template_id,
                version=template_version.version,
                backup_path=backup_path,
                changes_made=[f"Installed template {template_id} to {target_file}"]
            )
            
            # Store operation in history
            self.operation_history.append(operation)
            
            self.logger.info(f"Successfully installed template {template_id} to {target_file}")
            return operation
            
        except Exception as e:
            self.logger.error(f"Failed to install template {template_id} to {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.INSTALL,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                template_id=template_id,
                error_message=str(e)
            )
    
    async def update_parent_directory_template(
        self,
        target_directory: Path,
        template_variables: Dict[str, Any] = None,
        force: bool = False
    ) -> ParentDirectoryOperation:
        """
        Update a template in a parent directory.
        
        Args:
            target_directory: Directory containing template to update
            template_variables: New variables for template rendering
            force: Force update even if no changes detected
            
        Returns:
            ParentDirectoryOperation result
        """
        try:
            # Check if directory is managed
            directory_key = str(target_directory)
            if directory_key not in self.managed_directories:
                raise ValueError(f"Directory not managed: {target_directory}")
            
            config = self.managed_directories[directory_key]
            
            # Get current status
            status = await self.get_parent_directory_status(target_directory)
            
            if not status.exists:
                # File doesn't exist, perform installation
                return await self.install_template_to_parent_directory(
                    target_directory, config.template_id, template_variables
                )
            
            # Update template variables if provided
            if template_variables:
                config.template_variables.update(template_variables)
            
            # Get template and render
            template_data = await self.template_manager.get_template(config.template_id)
            if not template_data:
                raise ValueError(f"Template not found: {config.template_id}")
            
            content, template_version = template_data
            
            # Render with updated variables
            rendered_content = await self.template_manager.render_template(
                config.template_id, config.template_variables
            )
            
            if not rendered_content:
                raise RuntimeError("Failed to render template")
            
            # Check if content has changed
            target_file = target_directory / "CLAUDE.md"
            current_content = target_file.read_text()
            
            if current_content == rendered_content and not force:
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.UPDATE,
                    target_path=target_file,
                    success=True,
                    template_id=config.template_id,
                    version=template_version.version,
                    warnings=["No changes detected"]
                )
            
            # Create backup if enabled
            backup_path = None
            if self.auto_backup_enabled:
                backup_path = await self._create_backup(target_file)
            
            # Write updated content
            target_file.write_text(rendered_content)
            
            # Update configuration
            await self._save_managed_directories()
            
            # Create operation result
            operation = ParentDirectoryOperation(
                action=ParentDirectoryAction.UPDATE,
                target_path=target_file,
                success=True,
                template_id=config.template_id,
                version=template_version.version,
                backup_path=backup_path,
                changes_made=[f"Updated template {config.template_id} in {target_file}"]
            )
            
            # Store operation in history
            self.operation_history.append(operation)
            
            self.logger.info(f"Successfully updated template {config.template_id} in {target_file}")
            return operation
            
        except Exception as e:
            self.logger.error(f"Failed to update template in {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.UPDATE,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                error_message=str(e)
            )
    
    async def get_parent_directory_status(self, target_directory: Path) -> ParentDirectoryStatus:
        """
        Get status of a parent directory.
        
        Args:
            target_directory: Directory to check
            
        Returns:
            ParentDirectoryStatus object
        """
        try:
            target_file = target_directory / "CLAUDE.md"
            
            # Check if file exists
            if not target_file.exists():
                return ParentDirectoryStatus(
                    file_path=target_file,
                    exists=False,
                    is_managed=str(target_directory) in self.managed_directories
                )
            
            # Get file information
            stat = target_file.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Calculate checksum
            content = target_file.read_text()
            checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if managed
            directory_key = str(target_directory)
            is_managed = directory_key in self.managed_directories
            
            # Get template source if managed
            template_source = None
            current_version = None
            deployment_context = None
            
            if is_managed:
                config = self.managed_directories[directory_key]
                template_source = config.template_id
                
                # Get template version
                if self.template_manager:
                    template_data = await self.template_manager.get_template(config.template_id)
                    if template_data:
                        _, template_version = template_data
                        current_version = template_version.version
                
                deployment_context = config.deployment_metadata.get("deployment_type")
            
            # Check for backups
            backup_available = False
            if self.backups_dir.exists():
                backup_pattern = f"*{target_file.name}*"
                backup_files = list(self.backups_dir.glob(backup_pattern))
                backup_available = len(backup_files) > 0
            
            return ParentDirectoryStatus(
                file_path=target_file,
                exists=True,
                is_managed=is_managed,
                current_version=current_version,
                last_modified=last_modified,
                checksum=checksum,
                backup_available=backup_available,
                template_source=template_source,
                deployment_context=deployment_context
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get parent directory status for {target_directory}: {e}")
            return ParentDirectoryStatus(
                file_path=target_directory / "CLAUDE.md",
                exists=False,
                is_managed=False
            )
    
    async def backup_parent_directory(self, target_directory: Path) -> Optional[Path]:
        """
        Create a backup of a parent directory's CLAUDE.md file.
        
        Args:
            target_directory: Directory containing file to backup
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            target_file = target_directory / "CLAUDE.md"
            
            if not target_file.exists():
                self.logger.warning(f"No CLAUDE.md file to backup in {target_directory}")
                return None
            
            return await self._create_backup(target_file)
            
        except Exception as e:
            self.logger.error(f"Failed to backup parent directory {target_directory}: {e}")
            return None
    
    async def restore_parent_directory(
        self,
        target_directory: Path,
        backup_timestamp: Optional[str] = None
    ) -> ParentDirectoryOperation:
        """
        Restore a parent directory from backup.
        
        Args:
            target_directory: Directory to restore
            backup_timestamp: Specific backup to restore (latest if None)
            
        Returns:
            ParentDirectoryOperation result
        """
        try:
            target_file = target_directory / "CLAUDE.md"
            
            # Find backup files
            backup_pattern = f"*{target_file.name}*"
            backup_files = list(self.backups_dir.glob(backup_pattern))
            
            if not backup_files:
                raise ValueError(f"No backup files found for {target_file}")
            
            # Select backup file
            if backup_timestamp:
                backup_file = None
                for bf in backup_files:
                    if backup_timestamp in bf.name:
                        backup_file = bf
                        break
                
                if not backup_file:
                    raise ValueError(f"No backup found for timestamp: {backup_timestamp}")
            else:
                # Use most recent backup
                backup_file = max(backup_files, key=lambda f: f.stat().st_mtime)
            
            # Create backup of current file if it exists
            current_backup = None
            if target_file.exists():
                current_backup = await self._create_backup(target_file)
            
            # Restore from backup
            shutil.copy2(backup_file, target_file)
            
            # Create operation result
            operation = ParentDirectoryOperation(
                action=ParentDirectoryAction.RESTORE,
                target_path=target_file,
                success=True,
                backup_path=current_backup,
                changes_made=[f"Restored {target_file} from backup {backup_file}"]
            )
            
            # Store operation in history
            self.operation_history.append(operation)
            
            self.logger.info(f"Successfully restored {target_file} from backup")
            return operation
            
        except Exception as e:
            self.logger.error(f"Failed to restore parent directory {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.RESTORE,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                error_message=str(e)
            )
    
    async def validate_parent_directory(self, target_directory: Path) -> ParentDirectoryOperation:
        """
        Validate a parent directory's template.
        
        Args:
            target_directory: Directory to validate
            
        Returns:
            ParentDirectoryOperation result
        """
        try:
            target_file = target_directory / "CLAUDE.md"
            
            if not target_file.exists():
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.VALIDATE,
                    target_path=target_file,
                    success=False,
                    error_message="CLAUDE.md file not found"
                )
            
            # Check if managed
            directory_key = str(target_directory)
            if directory_key not in self.managed_directories:
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.VALIDATE,
                    target_path=target_file,
                    success=True,
                    warnings=["Directory not managed by Parent Directory Manager"]
                )
            
            config = self.managed_directories[directory_key]
            
            # Validate template if template manager available
            validation_errors = []
            validation_warnings = []
            
            if self.template_manager:
                # Get expected content
                rendered_content = await self.template_manager.render_template(
                    config.template_id, config.template_variables
                )
                
                if rendered_content:
                    # Compare with actual content
                    actual_content = target_file.read_text()
                    
                    if actual_content != rendered_content:
                        validation_warnings.append("Content differs from expected template output")
                else:
                    validation_errors.append("Failed to render template for validation")
            
            # Check file permissions
            if not os.access(target_file, os.R_OK):
                validation_errors.append("File is not readable")
            
            if not os.access(target_file, os.W_OK):
                validation_warnings.append("File is not writable")
            
            # Create operation result
            operation = ParentDirectoryOperation(
                action=ParentDirectoryAction.VALIDATE,
                target_path=target_file,
                success=len(validation_errors) == 0,
                template_id=config.template_id,
                error_message="; ".join(validation_errors) if validation_errors else None,
                warnings=validation_warnings
            )
            
            return operation
            
        except Exception as e:
            self.logger.error(f"Failed to validate parent directory {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.VALIDATE,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                error_message=str(e)
            )
    
    async def list_managed_directories(self) -> List[Dict[str, Any]]:
        """
        List all managed directories.
        
        Returns:
            List of managed directory information
        """
        try:
            directories = []
            
            for directory_key, config in self.managed_directories.items():
                # Get current status
                status = await self.get_parent_directory_status(config.target_directory)
                
                directory_info = {
                    "directory": str(config.target_directory),
                    "context": config.context.value,
                    "template_id": config.template_id,
                    "exists": status.exists,
                    "is_managed": status.is_managed,
                    "current_version": status.current_version,
                    "last_modified": status.last_modified.isoformat() if status.last_modified else None,
                    "backup_available": status.backup_available,
                    "deployment_context": status.deployment_context
                }
                
                directories.append(directory_info)
            
            return directories
            
        except Exception as e:
            self.logger.error(f"Failed to list managed directories: {e}")
            return []
    
    async def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of operation history entries
        """
        try:
            history = []
            
            # Get most recent operations
            recent_operations = self.operation_history[-limit:] if limit > 0 else self.operation_history
            
            for operation in recent_operations:
                history_entry = {
                    "action": operation.action.value,
                    "target_path": str(operation.target_path),
                    "success": operation.success,
                    "template_id": operation.template_id,
                    "version": operation.version,
                    "backup_path": str(operation.backup_path) if operation.backup_path else None,
                    "error_message": operation.error_message,
                    "changes_made": operation.changes_made,
                    "warnings": operation.warnings
                }
                
                history.append(history_entry)
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get operation history: {e}")
            return []
    
    # Helper Methods
    
    def _extract_claude_md_version(self, content: str) -> Optional[str]:
        """
        Extract CLAUDE_MD_VERSION from file content.
        Supports both old format (4.5.1) and new format (4.5.1-001).
        
        Args:
            content: File content to parse
            
        Returns:
            Version string or None if not found
        """
        try:
            # Look for CLAUDE_MD_VERSION in HTML comment or frontmatter
            # Updated patterns to support both formats: 4.5.1 and 4.5.1-001
            patterns = [
                r'CLAUDE_MD_VERSION:\s*([\d\.-]+)',
                r'<!-- CLAUDE_MD_VERSION:\s*([\d\.-]+)\s*-->',
                r'CLAUDE_MD_VERSION"?:\s*"?([\d\.-]+)"?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract CLAUDE_MD_VERSION: {e}")
            return None
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings supporting both formats:
        - Old format: 4.5.1
        - New format: 4.5.1-001
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            def parse_claude_md_version(version_str):
                """Parse CLAUDE.md version in format framework_version-serial_number"""
                if '-' in version_str:
                    # New format: 4.5.1-001
                    framework_part, serial_part = version_str.split('-', 1)
                    framework_parts = [int(x) for x in framework_part.split('.')]
                    serial_number = int(serial_part)
                    return framework_parts, serial_number
                else:
                    # Old format: 4.5.1 (treat as 4.5.1-000)
                    framework_parts = [int(x) for x in version_str.split('.')]
                    serial_number = 0
                    return framework_parts, serial_number
            
            v1_framework, v1_serial = parse_claude_md_version(version1)
            v2_framework, v2_serial = parse_claude_md_version(version2)
            
            # Pad shorter framework version with zeros
            max_len = max(len(v1_framework), len(v2_framework))
            v1_framework.extend([0] * (max_len - len(v1_framework)))
            v2_framework.extend([0] * (max_len - len(v2_framework)))
            
            # First compare framework versions
            for i in range(max_len):
                if v1_framework[i] < v2_framework[i]:
                    return -1
                elif v1_framework[i] > v2_framework[i]:
                    return 1
            
            # Framework versions are equal, compare serial numbers
            if v1_serial < v2_serial:
                return -1
            elif v1_serial > v2_serial:
                return 1
            else:
                return 0
            
        except Exception as e:
            self.logger.error(f"Failed to compare versions {version1} vs {version2}: {e}")
            # If comparison fails, assume versions are different
            return -1 if version1 != version2 else 0
    
    def _generate_next_claude_md_version(self, target_file: Path, framework_version: str, new_content: str = None) -> str:
        """
        Generate the next CLAUDE.md version number in format framework_version-serial.
        Only increments version if content would actually change.
        
        Args:
            target_file: Target CLAUDE.md file to check for existing version
            framework_version: Current framework version (e.g., "4.5.1")
            new_content: New content to compare against existing (optional)
            
        Returns:
            Next version string (e.g., "4.5.1-001")
        """
        try:
            # Check if target file exists and extract current version
            if target_file.exists():
                existing_content = target_file.read_text()
                existing_version = self._extract_claude_md_version(existing_content)
                
                # If we have new content, check if it would actually be different
                if new_content:
                    # Remove version-specific and timestamp lines for content comparison
                    def normalize_content(content):
                        lines = content.split('\n')
                        filtered_lines = []
                        for line in lines:
                            # Skip lines containing dynamic metadata
                            if any(marker in line for marker in [
                                'CLAUDE_MD_VERSION:', 'DEPLOYMENT_DATE:', 'LAST_UPDATED:', 
                                'DEPLOYMENT_ID:', '**Deployment Date**:', '**Last Updated**:'
                            ]):
                                continue
                            # Skip lines with deployment-specific content that changes each time
                            if ('Deployment Date' in line and '2025-' in line) or \
                               ('Last Updated' in line and '2025-' in line) or \
                               ('Deployment ID' in line and line.strip().endswith('**')):
                                continue
                            filtered_lines.append(line)
                        return '\n'.join(filtered_lines)
                    
                    existing_normalized = normalize_content(existing_content)
                    new_normalized = normalize_content(new_content)
                    
                    # If content is the same (excluding version metadata), return existing version
                    if existing_normalized == new_normalized and existing_version:
                        self.logger.info(f"📋 Content unchanged, keeping existing version: {existing_version}")
                        return existing_version
                
                if existing_version and '-' in existing_version:
                    # Existing version is in new format
                    existing_framework, existing_serial = existing_version.split('-', 1)
                    
                    if existing_framework == framework_version:
                        # Same framework version, increment serial
                        next_serial = int(existing_serial) + 1
                        return f"{framework_version}-{next_serial:03d}"
                    else:
                        # Different framework version, start with serial 001
                        return f"{framework_version}-001"
                else:
                    # Existing version is old format or no version, start with serial 001
                    return f"{framework_version}-001"
            else:
                # No existing file, start with serial 001
                return f"{framework_version}-001"
                
        except Exception as e:
            self.logger.error(f"Failed to generate next CLAUDE.md version: {e}")
            # Fallback to serial 001
            return f"{framework_version}-001"
    
    def _should_skip_deployment(self, target_file: Path, template_content: str, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Check if deployment should be skipped based on version comparison.
        
        Args:
            target_file: Target CLAUDE.md file
            template_content: New template content to deploy
            force: Force deployment even if versions match
            
        Returns:
            Tuple of (should_skip, reason)
        """
        try:
            self.logger.info(f"🔍 Checking deployment for: {target_file}")
            
            if force:
                self.logger.info("⚡ Force flag enabled - skipping version checks")
                return False, "Force deployment requested"
            
            if not target_file.exists():
                self.logger.info(f"📝 No existing CLAUDE.md found at: {target_file}")
                return False, "Target file does not exist"
            
            # Get existing file content and version
            existing_content = target_file.read_text()
            existing_version = self._extract_claude_md_version(existing_content)
            
            # Get template version
            template_version = self._extract_claude_md_version(template_content)
            
            # Get framework template source path for logging
            framework_template_path = self.framework_path / "framework" / "CLAUDE.md"
            
            self.logger.info(f"📋 Version comparison:")
            self.logger.info(f"   • Source: {framework_template_path}")
            self.logger.info(f"   • Target: {target_file}")
            self.logger.info(f"   • Framework version: {template_version or 'None found'}")
            self.logger.info(f"   • Existing version: {existing_version or 'None found'}")
            
            if not existing_version:
                self.logger.info("⚠️  No version found in existing file - proceeding with deployment")
                return False, "No version found in existing file"
            
            if not template_version:
                self.logger.info("⚠️  No version found in template - proceeding with deployment")
                return False, "No version found in template"
            
            # Compare versions
            comparison = self._compare_versions(existing_version, template_version)
            
            if comparison >= 0:
                reason = f"Existing version {existing_version} is current or newer than template version {template_version}"
                self.logger.info(f"⏭️  Skipping deployment: {reason}")
                return True, reason
            
            self.logger.info(f"✅ Template version {template_version} is newer than existing version {existing_version} - proceeding with deployment")
            return False, f"Template version {template_version} is newer than existing version {existing_version}"
            
        except Exception as e:
            self.logger.error(f"Error in version check: {e}")
            # If version checking fails, proceed with deployment
            return False, f"Version checking failed: {e}"
    
    async def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file."""
        try:
            if not file_path.exists():
                return None
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.name}_{timestamp}.backup"
            backup_path = self.backups_dir / backup_filename
            
            # If backup file already exists (same timestamp), add a counter
            counter = 1
            while backup_path.exists():
                backup_filename = f"{file_path.name}_{timestamp}_{counter:02d}.backup"
                backup_path = self.backups_dir / backup_filename
                counter += 1
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            
            self.logger.debug(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    async def detect_parent_directory_context(self, target_directory: Path) -> ParentDirectoryContext:
        """
        Detect the context of a parent directory.
        
        Args:
            target_directory: Directory to analyze
            
        Returns:
            ParentDirectoryContext enum value
        """
        try:
            # Check if it's the user home directory
            if target_directory == Path.home():
                return ParentDirectoryContext.USER_HOME
            
            # Check if it contains a deployment (has claude-multiagent-pm subdirectory)
            if (target_directory / "claude-multiagent-pm").exists():
                return ParentDirectoryContext.DEPLOYMENT_ROOT
            
            # Check if it contains multiple projects
            subdirs = [d for d in target_directory.iterdir() if d.is_dir()]
            project_indicators = [".git", "package.json", "pyproject.toml", "Cargo.toml"]
            
            project_count = 0
            for subdir in subdirs:
                if any((subdir / indicator).exists() for indicator in project_indicators):
                    project_count += 1
            
            if project_count > 1:
                return ParentDirectoryContext.PROJECT_COLLECTION
            
            # Check if it's a workspace root
            workspace_indicators = [".vscode", ".idea", "workspace.json"]
            if any((target_directory / indicator).exists() for indicator in workspace_indicators):
                return ParentDirectoryContext.WORKSPACE_ROOT
            
            # Default to custom
            return ParentDirectoryContext.CUSTOM
            
        except Exception as e:
            self.logger.error(f"Failed to detect parent directory context for {target_directory}: {e}")
            return ParentDirectoryContext.CUSTOM
    
    async def auto_register_parent_directories(
        self,
        search_paths: List[Path],
        template_id: str = "parent_directory_claude_md"
    ) -> List[Path]:
        """
        Automatically register parent directories that should be managed.
        
        Args:
            search_paths: Paths to search for parent directories
            template_id: Template to use for auto-registration
            
        Returns:
            List of registered directories
        """
        try:
            registered_directories = []
            
            for search_path in search_paths:
                if not search_path.exists() or not search_path.is_dir():
                    continue
                
                # Check if this directory should be managed
                context = await self.detect_parent_directory_context(search_path)
                
                # Skip user home directory unless explicitly configured
                if context == ParentDirectoryContext.USER_HOME:
                    continue
                
                # Auto-register if it looks like a deployment root or project collection
                if context in [ParentDirectoryContext.DEPLOYMENT_ROOT, ParentDirectoryContext.PROJECT_COLLECTION]:
                    success = await self.register_parent_directory(
                        search_path,
                        context,
                        template_id,
                        self._get_default_template_variables(search_path, context)
                    )
                    
                    if success:
                        registered_directories.append(search_path)
                        self.logger.info(f"Auto-registered parent directory: {search_path}")
            
            return registered_directories
            
        except Exception as e:
            self.logger.error(f"Failed to auto-register parent directories: {e}")
            return []
    
    def _get_default_template_variables(
        self,
        target_directory: Path,
        context: ParentDirectoryContext
    ) -> Dict[str, Any]:
        """Get default template variables for a directory."""
        variables = {
            "DIRECTORY_PATH": str(target_directory),
            "DIRECTORY_NAME": target_directory.name,
            "CONTEXT": context.value,
            "TIMESTAMP": datetime.now().isoformat(),
            "PLATFORM": os.name
        }
        
        # Add deployment-specific variables if available
        if hasattr(self, 'deployment_context') and self.deployment_context:
            variables.update({
                "DEPLOYMENT_TYPE": self.deployment_context.get("strategy", "unknown"),
                "DEPLOYMENT_PLATFORM": self.deployment_context.get("config", {}).get("platform", "unknown")
            })
        
        return variables
    
    async def _get_framework_template(self, template_id: str) -> Tuple[Optional[str], Optional[Any]]:
        """
        Get template from deployment framework path.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Tuple of (content, template_version) or (None, None) if not found
        """
        try:
            # Check for framework CLAUDE.md template
            if template_id in ["parent_directory_claude_md", "claude_md", "deployment_claude"]:
                framework_template_path = self.framework_path / "framework" / "CLAUDE.md"
                
                if framework_template_path.exists():
                    content = framework_template_path.read_text()
                    
                    # Create a simple template version object
                    from .template_manager import TemplateVersion, TemplateSource
                    from datetime import datetime
                    import hashlib
                    
                    template_version = TemplateVersion(
                        template_id=template_id,
                        version="deployment-current",
                        source=TemplateSource.FRAMEWORK,
                        created_at=datetime.now(),
                        checksum=hashlib.sha256(content.encode()).hexdigest(),
                        variables={},
                        metadata={"source_path": str(framework_template_path)}
                    )
                    
                    self.logger.info(f"Using framework template from: {framework_template_path}")
                    return content, template_version
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Failed to get framework template {template_id}: {e}")
            return None, None
    
    def _get_deployment_template_variables(self) -> Dict[str, Any]:
        """
        Get deployment-specific template variables for handlebars substitution.
        
        Returns:
            Dictionary of deployment variables
        """
        import os
        from datetime import datetime
        
        # Get framework version
        try:
            version_file = self.framework_path / "VERSION"
            if version_file.exists():
                framework_version = version_file.read_text().strip()
            else:
                framework_version = "4.5.1"
        except:
            framework_version = "4.5.1"
        
        # Get deployment date from config or use current time
        try:
            deployment_config_path = self.framework_path / ".claude-pm" / "config.json"
            if deployment_config_path.exists():
                import json
                with open(deployment_config_path) as f:
                    config = json.load(f)
                    deployment_date = config.get("deployment_date", datetime.now().isoformat())
            else:
                deployment_date = datetime.now().isoformat()
        except:
            deployment_date = datetime.now().isoformat()
        
        variables = {
            "FRAMEWORK_VERSION": framework_version,
            "DEPLOYMENT_DATE": deployment_date,
            "DEPLOYMENT_DIR": str(self.framework_path),
            "PLATFORM": os.name,
            "PYTHON_CMD": "python3",
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "CURRENT_TIMESTAMP": datetime.now().isoformat(),
            "WORKING_DIR": str(self.working_dir)
        }
        
        # Add deployment context if available
        if hasattr(self, 'deployment_context') and self.deployment_context:
            variables.update({
                "DEPLOYMENT_TYPE": self.deployment_context.get("strategy", "unknown"),
                "DEPLOYMENT_PLATFORM": self.deployment_context.get("config", {}).get("platform", "unknown")
            })
        
        return variables
    
    async def _render_template_content(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Render template content with handlebars-style variable substitution.
        
        Args:
            content: Template content with {{VARIABLE}} placeholders
            variables: Variables to substitute
            
        Returns:
            Rendered content
        """
        try:
            rendered_content = content
            
            # Replace handlebars-style variables
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
            
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"Failed to render template content: {e}")
            return content