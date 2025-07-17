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
from ..core.logging_config import setup_logging, setup_streaming_logger, finalize_streaming_logs
from .framework_claude_md_generator import FrameworkClaudeMdGenerator
# TemplateManager and DependencyManager removed - use Claude Code Task Tool instead
import os


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

    def __init__(self, config: Optional[Dict[str, Any]] = None, quiet_mode: bool = False):
        """
        Initialize the Parent Directory Manager.

        Args:
            config: Optional configuration dictionary
            quiet_mode: If True, suppress INFO level logging
        """
        super().__init__(name="parent_directory_manager", config=config)
        # Use streaming logger during initialization for clean startup output
        if quiet_mode or os.getenv('CLAUDE_PM_QUIET_MODE') == 'true':
            # Use WARNING level for quiet mode
            self.logger = setup_logging(__name__, level="WARNING")
        else:
            self.logger = setup_streaming_logger(__name__)
        self._startup_phase = True  # Track startup phase for logging behavior
        self._quiet_mode = quiet_mode  # Store quiet mode setting

        # Integration with other CMPM services
        # template_manager and dependency_manager removed - use Claude Code Task Tool instead
        self.template_manager: Optional[Any] = None
        self.dependency_manager: Optional[Any] = None

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
        self.framework_path = self._detect_framework_path()
        self.parent_directory_manager_dir = (
            self.working_dir / ".claude-pm" / "parent_directory_manager"
        )
        
        # Framework template backup directory - using centralized backups structure
        self.framework_backups_dir = self.working_dir / ".claude-pm" / "backups" / "framework"

        # Subsystem version tracking
        self.subsystem_versions = {}

        # Initialize paths
        self._initialize_paths()

    def _log_info_if_not_quiet(self, message: str) -> None:
        """Log INFO message only if not in quiet mode."""
        if not self._quiet_mode:
            self.logger.info(message)

    def _log_protection_guidance(self, target_file: Path, skip_reason: str) -> None:
        """
        Log detailed guidance when permanent protection blocks deployment.
        
        Args:
            target_file: The file that's being protected
            skip_reason: The reason deployment was blocked
        """
        self.logger.error("")
        self.logger.error("🚫 DEPLOYMENT BLOCKED BY PERMANENT PROTECTION")
        self.logger.error("=" * 50)
        self.logger.error(f"Target file: {target_file}")
        self.logger.error(f"Protection reason: {skip_reason}")
        self.logger.error("")
        self.logger.error("📋 EXPLANATION:")
        self.logger.error("The file you're trying to deploy to is NOT a framework deployment template.")
        self.logger.error("This protection prevents overwriting project development files and custom CLAUDE.md files.")
        self.logger.error("")
        self.logger.error("✅ WHAT CAN BE REPLACED:")
        self.logger.error("• Framework deployment templates (identified by specific title and metadata)")
        self.logger.error("• Files with title: '# Claude PM Framework Configuration - Deployment'")
        self.logger.error("• Files containing framework deployment metadata blocks")
        self.logger.error("")
        self.logger.error("🛡️  WHAT IS PROTECTED:")
        self.logger.error("• Project development files")
        self.logger.error("• Custom CLAUDE.md files")
        self.logger.error("• Any file not matching framework deployment template pattern")
        self.logger.error("")
        self.logger.error("🔧 RESOLUTION OPTIONS:")
        self.logger.error("1. If this is a project development file, keep it as-is (protection working correctly)")
        self.logger.error("2. If you need framework deployment here, manually remove the file first")
        self.logger.error("3. If you need both, rename the existing file to preserve your work")
        self.logger.error("")
        self.logger.error("⚠️  IMPORTANT:")
        self.logger.error("The --force flag CANNOT override this protection by design.")
        self.logger.error("This ensures your project development files are never accidentally overwritten.")
        self.logger.error("=" * 50)

    async def _initialize(self) -> None:
        """Initialize the Parent Directory Manager service."""
        self._log_info_if_not_quiet("Initializing Parent Directory Manager...")

        try:
            # Create directory structure
            self._create_directory_structure()

            # Initialize CMPM integrations
            await self._initialize_cmpm_integrations()

            # Load existing configurations
            await self._load_managed_directories()

            # Validate deployment context
            await self._validate_deployment_context()
            
            # Validate framework template integrity on startup
            if not self._validate_framework_template_integrity():
                self.logger.warning("Framework template integrity check failed during initialization")

            # Load subsystem versions
            await self._load_subsystem_versions()

            self._log_info_if_not_quiet("Parent Directory Manager initialized successfully")
            
            # Finalize streaming logs after initialization
            finalize_streaming_logs(self.logger)
            
            # Switch to normal logging after startup
            self.logger = setup_logging(__name__)
            self._startup_phase = False

        except Exception as e:
            self.logger.error(f"Failed to initialize Parent Directory Manager: {e}")
            raise

    async def _cleanup(self) -> None:
        """Cleanup the Parent Directory Manager service."""
        self._log_info_if_not_quiet("Cleaning up Parent Directory Manager...")

        try:
            # Save current state
            await self._save_managed_directories()

            # Cleanup temporary files
            await self._cleanup_temporary_files()

            # Close CMPM integrations
            # template_manager and dependency_manager removed - no cleanup needed

            self._log_info_if_not_quiet("Parent Directory Manager cleanup completed")

        except Exception as e:
            self.logger.error(f"Failed to cleanup Parent Directory Manager: {e}")

    def _initialize_paths(self):
        """Initialize parent directory manager paths."""
        # Manager directories - using centralized backups structure
        self.backups_dir = self.working_dir / ".claude-pm" / "backups" / "parent_directory_manager"
        self.configs_dir = self.parent_directory_manager_dir / "configs"
        self.versions_dir = self.parent_directory_manager_dir / "versions"
        self.logs_dir = self.parent_directory_manager_dir / "logs"

        # Configuration files
        self.managed_directories_file = self.configs_dir / "managed_directories.json"
        self.operation_history_file = self.logs_dir / "operation_history.json"

    def _detect_framework_path(self) -> Path:
        """Detect framework path from environment or deployment structure."""
        import os
        # Try environment variable first (set by Node.js CLI)
        if framework_path := os.getenv('CLAUDE_PM_FRAMEWORK_PATH'):
            return Path(framework_path)
            
        # Try deployment directory
        if deployment_dir := os.getenv('CLAUDE_PM_DEPLOYMENT_DIR'):
            return Path(deployment_dir)
            
        # Try relative to current module
        current_dir = Path(__file__).parent.parent.parent
        if (current_dir / 'framework' / 'CLAUDE.md').exists():
            return current_dir
            
        # Fallback to working directory
        return self.working_dir

    def _create_directory_structure(self):
        """Create the parent directory manager directory structure."""
        directories = [
            self.parent_directory_manager_dir,
            self.backups_dir,
            self.configs_dir,
            self.versions_dir,
            self.logs_dir,
            self.framework_backups_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _initialize_cmpm_integrations(self):
        """Initialize integrations with other CMPM services."""
        try:
            # Template and dependency management removed - use Claude Code Task Tool instead
            self.template_manager = None
            self.dependency_manager = None

            self.logger.info("Loading CMPM integrations...")

        except Exception as e:
            self.logger.error(f"Failed to initialize CMPM integrations: {e}")
            # Continue without full integration
            self.template_manager = None
            self.dependency_manager = None

    async def _load_managed_directories(self):
        """Load existing managed directories configuration."""
        try:
            if self.managed_directories_file.exists():
                with open(self.managed_directories_file, "r") as f:
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
                        conflict_resolution=config_data.get(
                            "conflict_resolution", "backup_and_replace"
                        ),
                        deployment_metadata=config_data.get("deployment_metadata", {}),
                    )
                    self.managed_directories[key] = config

                self.logger.info(f"Loading managed directories...")

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
                    "deployment_metadata": config.deployment_metadata,
                }

            with open(self.managed_directories_file, "w") as f:
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
            # dependency_manager removed - use Claude Code Task Tool instead
            deployment_config = None
            if deployment_config:
                self.deployment_context = deployment_config
                self.logger.info(
                    f"Deployment context validated: {deployment_config.get('strategy', 'unknown')}"
                )
            else:
                self.logger.warning("No deployment context available - dependency manager removed")

        except Exception as e:
            self.logger.error(f"Failed to validate deployment context: {e}")

    async def _cleanup_temporary_files(self):
        """Cleanup temporary files and old backups."""
        try:
            # Clean up old backups
            if self.backups_dir.exists():
                cutoff_date = datetime.now().timestamp() - (
                    self.backup_retention_days * 24 * 60 * 60
                )

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
        **kwargs,
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
                deployment_metadata=kwargs.get("deployment_metadata", {}),
            )

            # Register the directory
            directory_key = str(target_directory)
            self.managed_directories[directory_key] = config

            # Save configuration
            await self._save_managed_directories()

            self.logger.info(
                f"Registered parent directory: {target_directory} with template {template_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to register parent directory {target_directory}: {e}")
            return False

    async def deploy_framework_template(
        self,
        target_directory: Path,
        force: bool = False,
    ) -> ParentDirectoryOperation:
        """
        Deploy framework template using the new generator with integrated deployment.

        Args:
            target_directory: Directory to deploy template to
            force: Force deployment even if version is current

        Returns:
            ParentDirectoryOperation result
        """
        try:
            # Use the generator's deploy_to_parent method
            generator = FrameworkClaudeMdGenerator()
            target_path = target_directory / "CLAUDE.md"
            
            # Set template variables for deployment
            import platform
            generator.template_variables = {
                'PYTHON_CMD': 'python3',
                'PLATFORM': platform.system().lower(),
                'PLATFORM_NOTES': self._get_platform_notes(),
                'DEPLOYMENT_ID': '{{DEPLOYMENT_ID}}'  # Leave as template for runtime substitution
            }
            
            # Create backup if file exists
            backup_path = None
            if target_path.exists():
                # Check if existing file is protected
                existing_content = target_path.read_text()
                
                # Check if existing file is a framework deployment template
                is_framework_template = self._is_framework_deployment_template(existing_content)
                
                if not is_framework_template:
                    # This is a project development file or other custom CLAUDE.md - PERMANENT PROTECTION
                    error_msg = "Permanent protection active: Existing file is not a framework deployment template - protecting project development file"
                    self.logger.error(f"🚫 PERMANENT PROTECTION: {error_msg}")
                    self._log_protection_guidance(target_path, error_msg)
                    
                    return ParentDirectoryOperation(
                        action=ParentDirectoryAction.INSTALL,
                        target_path=target_path,
                        success=False,
                        template_id="framework_claude_md",
                        error_message=error_msg,
                    )
                
                # Create backup since it's a framework template
                backup_path = await self._create_backup(target_path)
                if backup_path:
                    self._log_info_if_not_quiet(f"📁 Backup created: {backup_path}")
            
            # Deploy using generator (it expects a Path object)
            success, message = generator.deploy_to_parent(target_directory, force=force)
            
            if success:
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.INSTALL,
                    target_path=target_path,
                    success=True,
                    template_id="framework_claude_md",
                    backup_path=backup_path,
                    changes_made=[f"Deployed framework template to {target_path}"],
                )
            else:
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.INSTALL,
                    target_path=target_path,
                    success=False,
                    template_id="framework_claude_md",
                    error_message=f"Deployment failed: {message}",
                )
                
        except Exception as e:
            self.logger.error(f"Failed to deploy framework template to {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.INSTALL,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                template_id="framework_claude_md",
                error_message=str(e),
            )

    async def install_template_to_parent_directory(
        self,
        target_directory: Path,
        template_id: str,
        template_variables: Dict[str, Any] = None,
        force: bool = False,
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
            # Use streaming logging during deployment if we're in startup phase
            if hasattr(self, '_startup_phase') and self._startup_phase:
                # Switch to streaming logger temporarily for deployment
                original_logger = self.logger
                self.logger = setup_streaming_logger(self.logger.name)
                deployment_streaming = True
            else:
                deployment_streaming = False
            # Determine target file path
            target_file = target_directory / "CLAUDE.md"
            
            # Store target file for generator to use for version auto-increment
            self._current_target_file = target_file
            
            # FIXED: Get template from deployment framework path using generator
            content, template_version = await self._get_framework_template(template_id)
            if not content:
                # Fallback to template manager if framework template not found
                # template_manager removed - use Claude Code Task Tool instead
                raise RuntimeError(
                    "Template manager removed - use Claude Code Task Tool for template management"
                )

            # Initialize backup_path
            backup_path = None

            # Version checking is now done after template rendering
            # to ensure we have the complete template with variables

            # Check if file exists and handle conflicts
            if target_file.exists():
                existing_content = target_file.read_text()
                existing_checksum = hashlib.sha256(existing_content.encode()).hexdigest()

                # ALWAYS create backup before any file operations, regardless of force flag
                backup_path = await self._create_backup(target_file)
                if backup_path:
                    self._log_info_if_not_quiet(f"📁 Backup created: {backup_path}")
                else:
                    self.logger.warning(f"⚠️ Failed to create backup for {target_file}")

            # The generator already handles all template generation and variable substitution
            # We just need to use the content directly
            rendered_content = content
            
            if not rendered_content:
                raise RuntimeError("Failed to generate template")

            # Check if deployment should be skipped based on version comparison and file type protection
            should_skip, skip_reason, is_permanent_protection = self._should_skip_deployment(
                target_file, rendered_content, force
            )
            if should_skip:
                if is_permanent_protection:
                    # PERMANENT PROTECTION: Cannot be overridden by force flag
                    self.logger.error(f"🚫 PERMANENT PROTECTION: {skip_reason}")
                    self._log_info_if_not_quiet(f"🚫 Force flag cannot override project development file protection")
                    self._log_info_if_not_quiet(f"   • This protection prevents overwriting non-framework files")
                    self._log_info_if_not_quiet(f"   • Only framework deployment templates can be replaced")
                    
                    # Provide user guidance for permanent protection
                    self._log_protection_guidance(target_file, skip_reason)
                    
                    return ParentDirectoryOperation(
                        action=ParentDirectoryAction.INSTALL,
                        target_path=target_file,
                        success=False,
                        template_id=template_id,
                        error_message=f"Permanent protection active: {skip_reason}",
                    )
                elif not force:
                    # OVERRIDABLE PROTECTION: Can be overridden by force flag
                    operation = ParentDirectoryOperation(
                        action=ParentDirectoryAction.INSTALL,
                        target_path=target_file,
                        success=True,
                        template_id=template_id,
                        version=template_version.version if template_version else None,
                        warnings=[f"Deployment skipped: {skip_reason}"],
                    )
                    self.logger.info(f"Skipped template installation: {skip_reason}")
                    return operation
                else:
                    # FORCE OVERRIDE: Force flag overrides version checks and template validation
                    self.logger.warning(f"⚡ FORCE FLAG ACTIVE: Overriding version protection - {skip_reason}")
                    self._log_info_if_not_quiet(f"⚡ Force deployment proceeding despite version checks")
                    self._log_info_if_not_quiet(f"   • Force flag can override version checks and template validation")
                    self._log_info_if_not_quiet(f"   • Force flag CANNOT override project development file protection")
                    self._log_info_if_not_quiet(f"   • Deployment will proceed with framework template replacement")
                    # Continue with deployment

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
                changes_made=[f"Installed template {template_id} to {target_file}"],
            )

            # Store operation in history
            self.operation_history.append(operation)

            self._log_info_if_not_quiet(f"Successfully installed template {template_id} to {target_file}")
            
            # Clean up temporary attribute
            if hasattr(self, '_current_target_file'):
                del self._current_target_file
            
            # Finalize streaming logs if we used streaming logger
            if deployment_streaming:
                finalize_streaming_logs(self.logger)
                self.logger = original_logger
            
            return operation

        except Exception as e:
            self.logger.error(
                f"Failed to install template {template_id} to {target_directory}: {e}"
            )
            
            # Clean up temporary attribute
            if hasattr(self, '_current_target_file'):
                del self._current_target_file
            
            # Finalize streaming logs if we used streaming logger
            if 'deployment_streaming' in locals() and deployment_streaming:
                finalize_streaming_logs(self.logger)
                self.logger = original_logger
            
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.INSTALL,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                template_id=template_id,
                error_message=str(e),
            )

    async def update_parent_directory_template(
        self, target_directory: Path, template_variables: Dict[str, Any] = None, force: bool = False
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
            # template_manager removed - use Claude Code Task Tool instead
            raise RuntimeError(
                "Template manager removed - use Claude Code Task Tool for template management"
            )

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
                    warnings=["No changes detected"],
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
                changes_made=[f"Updated template {config.template_id} in {target_file}"],
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
                error_message=str(e),
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
                    is_managed=str(target_directory) in self.managed_directories,
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
                # template_manager removed - use Claude Code Task Tool instead
                current_version = "unknown"

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
                deployment_context=deployment_context,
            )

        except Exception as e:
            self.logger.error(f"Failed to get parent directory status for {target_directory}: {e}")
            return ParentDirectoryStatus(
                file_path=target_directory / "CLAUDE.md", exists=False, is_managed=False
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
        self, target_directory: Path, backup_timestamp: Optional[str] = None
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
                changes_made=[f"Restored {target_file} from backup {backup_file}"],
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
                error_message=str(e),
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
                    error_message="CLAUDE.md file not found",
                )

            # Check if managed
            directory_key = str(target_directory)
            if directory_key not in self.managed_directories:
                return ParentDirectoryOperation(
                    action=ParentDirectoryAction.VALIDATE,
                    target_path=target_file,
                    success=True,
                    warnings=["Directory not managed by Parent Directory Manager"],
                )

            config = self.managed_directories[directory_key]

            # Validate template if template manager available
            validation_errors = []
            validation_warnings = []

            # template_manager removed - use Claude Code Task Tool instead
            rendered_content = None

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
                warnings=validation_warnings,
            )

            return operation

        except Exception as e:
            self.logger.error(f"Failed to validate parent directory {target_directory}: {e}")
            return ParentDirectoryOperation(
                action=ParentDirectoryAction.VALIDATE,
                target_path=target_directory / "CLAUDE.md",
                success=False,
                error_message=str(e),
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
                    "last_modified": (
                        status.last_modified.isoformat() if status.last_modified else None
                    ),
                    "backup_available": status.backup_available,
                    "deployment_context": status.deployment_context,
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
            recent_operations = (
                self.operation_history[-limit:] if limit > 0 else self.operation_history
            )

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
                    "warnings": operation.warnings,
                }

                history.append(history_entry)

            return history

        except Exception as e:
            self.logger.error(f"Failed to get operation history: {e}")
            return []

    # Subsystem Version Management Methods

    async def _load_subsystem_versions(self) -> None:
        """Load subsystem versions from version files."""
        try:
            subsystem_files = {
                "memory": "MEMORY_VERSION",
                "agents": "AGENTS_VERSION", 
                "ticketing": "TICKETING_VERSION",
                "documentation": "DOCUMENTATION_VERSION",
                "services": "SERVICES_VERSION",
                "cli": "CLI_VERSION",
                "integration": "INTEGRATION_VERSION",
                "health": "HEALTH_VERSION",
                "framework": "FRAMEWORK_VERSION"
            }

            for subsystem, filename in subsystem_files.items():
                version_file = self.framework_path / filename
                if version_file.exists():
                    try:
                        version = version_file.read_text().strip()
                        self.subsystem_versions[subsystem] = {
                            "version": version,
                            "file_path": str(version_file),
                            "last_checked": datetime.now().isoformat()
                        }
                        if not (hasattr(self, '_startup_phase') and self._startup_phase):
                            self.logger.debug(f"Loaded {subsystem} version: {version}")
                    except Exception as e:
                        if not (hasattr(self, '_startup_phase') and self._startup_phase):
                            self.logger.error(f"Failed to read {subsystem} version from {version_file}: {e}")
                        self.subsystem_versions[subsystem] = {
                            "version": "unknown",
                            "file_path": str(version_file),
                            "error": str(e),
                            "last_checked": datetime.now().isoformat()
                        }
                else:
                    if not (hasattr(self, '_startup_phase') and self._startup_phase):
                        self.logger.warning(f"Subsystem version file not found: {version_file}")
                    self.subsystem_versions[subsystem] = {
                        "version": "not_found",
                        "file_path": str(version_file),
                        "last_checked": datetime.now().isoformat()
                    }

            self.logger.info(f"Loading subsystem versions...")

        except Exception as e:
            self.logger.error(f"Failed to load subsystem versions: {e}")

    def get_subsystem_versions(self) -> Dict[str, Any]:
        """
        Get all detected subsystem versions.

        Returns:
            Dictionary with subsystem version information
        """
        try:
            return {
                "framework_path": str(self.framework_path),
                "subsystems": self.subsystem_versions.copy(),
                "detection_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get subsystem versions: {e}")
            return {"error": str(e)}

    def get_subsystem_version(self, subsystem: str) -> Optional[str]:
        """
        Get version for a specific subsystem.

        Args:
            subsystem: Name of the subsystem

        Returns:
            Version string or None if not found
        """
        try:
            subsystem_info = self.subsystem_versions.get(subsystem)
            return subsystem_info.get("version") if subsystem_info else None
        except Exception as e:
            self.logger.error(f"Failed to get version for subsystem {subsystem}: {e}")
            return None

    async def validate_subsystem_compatibility(self, required_versions: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate subsystem version compatibility against requirements.

        Args:
            required_versions: Dictionary of subsystem -> required version

        Returns:
            Validation results with compatibility status
        """
        try:
            results = {
                "compatible": True,
                "validation_timestamp": datetime.now().isoformat(),
                "subsystem_checks": {}
            }

            for subsystem, required_version in required_versions.items():
                current_version = self.get_subsystem_version(subsystem)
                
                check_result = {
                    "subsystem": subsystem,
                    "required_version": required_version,
                    "current_version": current_version,
                    "compatible": False,
                    "status": "unknown"
                }

                if current_version is None or current_version in ["unknown", "not_found"]:
                    check_result["status"] = "missing"
                    results["compatible"] = False
                elif current_version == required_version:
                    check_result["compatible"] = True
                    check_result["status"] = "exact_match"
                else:
                    # Try version comparison for compatibility
                    try:
                        comparison = self._compare_subsystem_versions(current_version, required_version)
                        if comparison >= 0:
                            check_result["compatible"] = True
                            check_result["status"] = "compatible" if comparison > 0 else "exact_match"
                        else:
                            check_result["status"] = "outdated"
                            results["compatible"] = False
                    except Exception as comp_error:
                        check_result["status"] = "comparison_failed"
                        check_result["error"] = str(comp_error)
                        results["compatible"] = False

                results["subsystem_checks"][subsystem] = check_result

            return results

        except Exception as e:
            self.logger.error(f"Failed to validate subsystem compatibility: {e}")
            return {
                "compatible": False,
                "error": str(e),
                "validation_timestamp": datetime.now().isoformat()
            }

    def _compare_subsystem_versions(self, version1: str, version2: str) -> int:
        """
        Compare two subsystem version strings.
        Supports serial number format (001, 002, etc.).

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            # Handle serial number format (001, 002, etc.)
            if version1.isdigit() and version2.isdigit():
                v1_num = int(version1)
                v2_num = int(version2)
                if v1_num < v2_num:
                    return -1
                elif v1_num > v2_num:
                    return 1
                else:
                    return 0
            
            # Handle semantic versioning (x.y.z)
            if "." in version1 and "." in version2:
                v1_parts = [int(x) for x in version1.split(".")]
                v2_parts = [int(x) for x in version2.split(".")]
                
                # Pad shorter version with zeros
                max_len = max(len(v1_parts), len(v2_parts))
                v1_parts.extend([0] * (max_len - len(v1_parts)))
                v2_parts.extend([0] * (max_len - len(v2_parts)))
                
                for i in range(max_len):
                    if v1_parts[i] < v2_parts[i]:
                        return -1
                    elif v1_parts[i] > v2_parts[i]:
                        return 1
                
                return 0
            
            # String comparison fallback
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0

        except Exception as e:
            self.logger.error(f"Failed to compare subsystem versions {version1} vs {version2}: {e}")
            # If comparison fails, assume versions are different
            return -1 if version1 != version2 else 0

    async def update_subsystem_version(self, subsystem: str, new_version: str) -> bool:
        """
        Update a subsystem version file.

        Args:
            subsystem: Name of the subsystem
            new_version: New version string

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            version_files = {
                "memory": "MEMORY_VERSION",
                "agents": "AGENTS_VERSION", 
                "ticketing": "TICKETING_VERSION",
                "documentation": "DOCUMENTATION_VERSION",
                "services": "SERVICES_VERSION",
                "cli": "CLI_VERSION",
                "integration": "INTEGRATION_VERSION",
                "health": "HEALTH_VERSION",
                "framework": "FRAMEWORK_VERSION"
            }

            filename = version_files.get(subsystem)
            if not filename:
                self.logger.error(f"Unknown subsystem: {subsystem}")
                return False

            version_file = self.framework_path / filename
            
            # Backup existing version file if it exists
            if version_file.exists():
                backup_path = await self._create_backup(version_file)
                if backup_path:
                    self.logger.info(f"Created backup of {filename}: {backup_path}")

            # Write new version
            version_file.write_text(new_version.strip())
            
            # Update in-memory tracking
            self.subsystem_versions[subsystem] = {
                "version": new_version,
                "file_path": str(version_file),
                "last_updated": datetime.now().isoformat()
            }

            self.logger.info(f"Updated {subsystem} version to: {new_version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update {subsystem} version to {new_version}: {e}")
            return False

    def get_subsystem_version_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive subsystem version report.

        Returns:
            Dictionary with detailed version information
        """
        try:
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "framework_path": str(self.framework_path),
                "subsystem_count": len(self.subsystem_versions),
                "subsystems": {},
                "summary": {
                    "total": 0,
                    "found": 0,
                    "missing": 0,
                    "errors": 0
                }
            }

            for subsystem, info in self.subsystem_versions.items():
                version = info.get("version", "unknown")
                status = "found"
                
                if version == "not_found":
                    status = "missing"
                    report["summary"]["missing"] += 1
                elif version == "unknown" or "error" in info:
                    status = "error"
                    report["summary"]["errors"] += 1
                else:
                    report["summary"]["found"] += 1
                
                report["summary"]["total"] += 1
                
                report["subsystems"][subsystem] = {
                    "version": version,
                    "status": status,
                    "file_path": info.get("file_path"),
                    "last_checked": info.get("last_checked"),
                    "error": info.get("error")
                }

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate subsystem version report: {e}")
            return {
                "error": str(e),
                "report_timestamp": datetime.now().isoformat()
            }

    # Helper Methods

    def _is_framework_deployment_template(self, content: str) -> bool:
        """
        Check if content is a framework deployment template by examining metadata header.
        
        Framework deployment templates have:
        1. Title starting with "# Claude PM Framework Configuration - Deployment"
        2. HTML comment block with metadata (CLAUDE_MD_VERSION, FRAMEWORK_VERSION, etc.)
        
        Args:
            content: File content to check
            
        Returns:
            True if content is a framework deployment template, False otherwise
        """
        try:
            lines = content.split('\n')
            
            # Check for the specific title pattern
            title_found = False
            for line in lines[:5]:  # Check first 5 lines for title
                if line.strip().startswith("# Claude PM Framework Configuration - Deployment"):
                    title_found = True
                    break
            
            if not title_found:
                self.logger.debug("No framework deployment title found")
                return False
            
            # Check for HTML comment metadata block
            # Support both template format ({{VAR}}) and deployed format (actual values)
            metadata_patterns = [
                r"CLAUDE_MD_VERSION:\s*(?:\{\{CLAUDE_MD_VERSION\}\}|\d+-\d+)",
                r"FRAMEWORK_VERSION:\s*(?:\{\{FRAMEWORK_VERSION\}\}|\d+)",
                r"DEPLOYMENT_DATE:\s*(?:\{\{DEPLOYMENT_DATE\}\}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
                r"LAST_UPDATED:\s*(?:\{\{LAST_UPDATED\}\}|.*)",
                r"CONTENT_HASH:\s*(?:\{\{CONTENT_HASH\}\}|.*)"
            ]
            
            # Look for metadata patterns in the first 20 lines (where metadata should be)
            content_start = '\n'.join(lines[:20])
            
            # Check if we have at least 3 of the 5 expected metadata patterns
            pattern_matches = 0
            for pattern in metadata_patterns:
                if re.search(pattern, content_start, re.IGNORECASE):
                    pattern_matches += 1
            
            if pattern_matches >= 3:
                self.logger.debug("Framework deployment template detected: found deployment title and metadata patterns")
                return True
            else:
                self.logger.debug(f"Not a framework deployment template: found {pattern_matches}/5 metadata patterns")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to check framework deployment template: {e}")
            return False

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
                r"CLAUDE_MD_VERSION:\s*([\d\.-]+)",
                r"<!-- CLAUDE_MD_VERSION:\s*([\d\.-]+)\s*-->",
                r'CLAUDE_MD_VERSION"?:\s*"?([\d\.-]+)"?',
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
                if "-" in version_str:
                    # New format: 4.5.1-001
                    framework_part, serial_part = version_str.split("-", 1)
                    framework_parts = [int(x) for x in framework_part.split(".")]
                    serial_number = int(serial_part)
                    return framework_parts, serial_number
                else:
                    # Old format: 4.5.1 (treat as 4.5.1-000)
                    framework_parts = [int(x) for x in version_str.split(".")]
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

    def _generate_next_claude_md_version(
        self, target_file: Path, framework_version: str, new_content: str = None
    ) -> str:
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
                        lines = content.split("\n")
                        filtered_lines = []
                        for line in lines:
                            # Skip lines containing dynamic metadata
                            if any(
                                marker in line
                                for marker in [
                                    "CLAUDE_MD_VERSION:",
                                    "DEPLOYMENT_DATE:",
                                    "LAST_UPDATED:",
                                    "DEPLOYMENT_ID:",
                                    "**Deployment Date**:",
                                    "**Last Updated**:",
                                ]
                            ):
                                continue
                            # Skip lines with deployment-specific content that changes each time
                            if (
                                ("Deployment Date" in line and "2025-" in line)
                                or ("Last Updated" in line and "2025-" in line)
                                or ("Deployment ID" in line and line.strip().endswith("**"))
                            ):
                                continue
                            filtered_lines.append(line)
                        return "\n".join(filtered_lines)

                    existing_normalized = normalize_content(existing_content)
                    new_normalized = normalize_content(new_content)

                    # If content is the same (excluding version metadata), return existing version
                    if existing_normalized == new_normalized and existing_version:
                        self.logger.info(
                            f"📋 Content unchanged, keeping existing version: {existing_version}"
                        )
                        return existing_version

                if existing_version and "-" in existing_version:
                    # Existing version is in new format
                    existing_framework, existing_serial = existing_version.split("-", 1)

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

    def _should_skip_deployment(
        self, target_file: Path, template_content: str, force: bool = False
    ) -> Tuple[bool, Optional[str], bool]:
        """
        Check if deployment should be skipped based on file type and version comparison.
        
        CRITICAL PROTECTION: Only replaces files that are identified as framework deployment templates.
        Project development files and other custom CLAUDE.md files are protected.

        Args:
            target_file: Target CLAUDE.md file
            template_content: New template content to deploy
            force: Force deployment even if versions match

        Returns:
            Tuple of (should_skip, reason, is_permanent_protection)
            - should_skip: True if deployment should be skipped
            - reason: Human-readable reason for skipping
            - is_permanent_protection: True if protection cannot be overridden by force flag
        """
        try:
            self._log_info_if_not_quiet(f"🔍 Checking deployment for: {target_file}")

            if not target_file.exists():
                self._log_info_if_not_quiet(f"📝 No existing CLAUDE.md found at: {target_file}")
                return False, "Target file does not exist", False

            # Get existing file content
            existing_content = target_file.read_text()
            
            # CRITICAL: Check if existing file is a framework deployment template
            is_framework_template = self._is_framework_deployment_template(existing_content)
            
            if not is_framework_template:
                # This is a project development file or other custom CLAUDE.md - PERMANENT PROTECTION
                reason = "Existing file is not a framework deployment template - protecting project development file"
                self.logger.warning(f"🛡️  PERMANENT PROTECTION ACTIVE: {reason}")
                self._log_info_if_not_quiet(f"   • File appears to be a project development file or custom CLAUDE.md")
                self._log_info_if_not_quiet(f"   • Only framework deployment templates can be replaced")
                self._log_info_if_not_quiet(f"   • Framework deployment templates have title: '# Claude PM Framework Configuration - Deployment'")
                self._log_info_if_not_quiet(f"   • This protection CANNOT be overridden by --force flag")
                return True, reason, True  # PERMANENT PROTECTION

            self.logger.info(f"✅ Existing file is a framework deployment template - replacement allowed")

            if force:
                self.logger.info("⚡ Force flag enabled - skipping version checks")
                return False, "Force deployment requested", False

            # Get versions for comparison
            existing_version = self._extract_claude_md_version(existing_content)
            template_version = self._extract_claude_md_version(template_content)

            # Get framework template source path for logging
            framework_template_path = self.framework_path / "framework" / "CLAUDE.md"

            self.logger.info(f"📋 Version comparison:")
            self.logger.info(f"   • Source: {framework_template_path}")
            self.logger.info(f"   • Target: {target_file}")
            self.logger.info(f"   • Framework version: {template_version or 'None found'}")
            self.logger.info(f"   • Existing version: {existing_version or 'None found'}")

            if not existing_version:
                self.logger.info(
                    "⚠️  No version found in existing file - proceeding with deployment"
                )
                return False, "No version found in existing file", False

            if not template_version:
                self.logger.info("⚠️  No version found in template - proceeding with deployment")
                return False, "No version found in template", False

            # Compare versions
            comparison = self._compare_versions(existing_version, template_version)

            if comparison >= 0:
                reason = f"Existing version {existing_version} is current or newer than template version {template_version}"
                self.logger.info(f"⏭️  Skipping deployment: {reason}")
                self._log_info_if_not_quiet(f"   • This is an overridable protection - can be bypassed with --force flag")
                return True, reason, False  # Version check - can be overridden by force

            self.logger.info(
                f"✅ Template version {template_version} is newer than existing version {existing_version} - proceeding with deployment"
            )
            return (
                False,
                f"Template version {template_version} is newer than existing version {existing_version}",
                False
            )

        except Exception as e:
            self.logger.error(f"Error in deployment check: {e}")
            # If checking fails, err on the side of caution and skip deployment
            return True, f"Deployment check failed: {e} - protecting existing file", True  # Error protection - permanent

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

    async def detect_parent_directory_context(
        self, target_directory: Path
    ) -> ParentDirectoryContext:
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
            self.logger.error(
                f"Failed to detect parent directory context for {target_directory}: {e}"
            )
            return ParentDirectoryContext.CUSTOM

    async def auto_register_parent_directories(
        self, search_paths: List[Path], template_id: str = "parent_directory_claude_md"
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
                if context in [
                    ParentDirectoryContext.DEPLOYMENT_ROOT,
                    ParentDirectoryContext.PROJECT_COLLECTION,
                ]:
                    success = await self.register_parent_directory(
                        search_path,
                        context,
                        template_id,
                        self._get_default_template_variables(search_path, context),
                    )

                    if success:
                        registered_directories.append(search_path)
                        self.logger.info(f"Auto-registered parent directory: {search_path}")

            return registered_directories

        except Exception as e:
            self.logger.error(f"Failed to auto-register parent directories: {e}")
            return []

    def _get_default_template_variables(
        self, target_directory: Path, context: ParentDirectoryContext
    ) -> Dict[str, Any]:
        """Get default template variables for a directory."""
        variables = {
            "DIRECTORY_PATH": str(target_directory),
            "DIRECTORY_NAME": target_directory.name,
            "CONTEXT": context.value,
            "TIMESTAMP": datetime.now().isoformat(),
            "PLATFORM": os.name,
        }

        # Add deployment-specific variables if available
        if hasattr(self, "deployment_context") and self.deployment_context:
            variables.update(
                {
                    "DEPLOYMENT_TYPE": self.deployment_context.get("strategy", "unknown"),
                    "DEPLOYMENT_PLATFORM": self.deployment_context.get("config", {}).get(
                        "platform", "unknown"
                    ),
                }
            )

        return variables

    async def _get_framework_template(
        self, template_id: str
    ) -> Tuple[Optional[str], Optional[Any]]:
        """
        Get template from deployment framework path using the new generator.

        Args:
            template_id: Template identifier

        Returns:
            Tuple of (content, template_version) or (None, None) if not found
        """
        try:
            # Check for framework CLAUDE.md template
            if template_id in ["parent_directory_claude_md", "claude_md", "deployment_claude"]:
                # Use the new generator to create the template
                generator = FrameworkClaudeMdGenerator()
                
                # Set template variables before generation
                import platform
                generator.template_variables = {
                    'PYTHON_CMD': 'python3',
                    'PLATFORM': platform.system().lower(),
                    'PLATFORM_NOTES': self._get_platform_notes(),
                    'DEPLOYMENT_ID': '{{DEPLOYMENT_ID}}'  # Leave as template for runtime substitution
                }
                
                # Check if we have an existing file to pass for version auto-increment
                current_content = None
                if hasattr(self, '_current_target_file') and self._current_target_file.exists():
                    current_content = self._current_target_file.read_text()
                
                # Generate the template content
                content = generator.generate(current_content=current_content)
                
                # Extract the version that was generated
                generated_version = self._extract_claude_md_version(content)
                
                # Maintain backup functionality with the generated content
                framework_template_path = self.framework_path / "framework" / "CLAUDE.md"
                if framework_template_path.exists():
                    # BACKUP: Create backup before any operations
                    self._backup_framework_template(framework_template_path)

                # Create a simple template version object for compatibility
                from datetime import datetime
                import hashlib

                # Create a simple template version object that has the expected attributes
                class SimpleTemplateVersion:
                    def __init__(self, template_id, version, source, created_at, checksum, variables, metadata):
                        self.template_id = template_id
                        self.version = version
                        self.source = source
                        self.created_at = created_at
                        self.checksum = checksum
                        self.variables = variables
                        self.metadata = metadata
                
                template_version = SimpleTemplateVersion(
                    template_id=template_id,
                    version=generated_version or "deployment-current",
                    source="framework-generator",
                    created_at=datetime.now(),
                    checksum=hashlib.sha256(content.encode()).hexdigest(),
                    variables=generator.template_variables,
                    metadata={"source": "FrameworkClaudeMdGenerator"}
                )

                self._log_info_if_not_quiet(f"Using framework template from generator (version: {generated_version})")
                return content, template_version

            return None, None

        except Exception as e:
            self.logger.error(f"Failed to get framework template {template_id}: {e}")
            return None, None

    def _get_platform_notes(self) -> str:
        """
        Get platform-specific notes for the framework template.
        
        Returns:
            Platform-specific notes string
        """
        import platform
        system = platform.system().lower()
        
        if system == 'windows':
            return "Windows users may need to use 'python' instead of 'python3' depending on installation."
        elif system == 'darwin':
            return "macOS users should ensure python3 is installed via Homebrew or official Python installer."
        elif system == 'linux':
            return "Linux users may need to install python3 via their package manager if not present."
        else:
            return f"Platform-specific configuration may be required for {system}."
    
    def _get_deployment_template_variables(self) -> Dict[str, Any]:
        """
        Get deployment-specific template variables for handlebars substitution.

        Returns:
            Dictionary of deployment variables
        """
        import os
        import hashlib
        from datetime import datetime

        # Get framework version
        try:
            # Try FRAMEWORK_VERSION file first (simple incremental numbering)
            framework_version_file = self.framework_path / "FRAMEWORK_VERSION"
            if framework_version_file.exists():
                framework_version = framework_version_file.read_text().strip()
            else:
                # Try VERSION file for semantic versioning
                version_file = self.framework_path / "VERSION"
                if version_file.exists():
                    framework_version = version_file.read_text().strip()
                else:
                    # Fall back to package version
                    import claude_pm
                    framework_version = claude_pm.__version__
        except:
            # Import package version as last resort
            try:
                import claude_pm
                framework_version = claude_pm.__version__
            except:
                # This should never happen in a proper installation
                raise RuntimeError("Could not determine framework version - installation may be corrupted")

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

        # Generate current timestamp for LAST_UPDATED
        current_timestamp = datetime.now().isoformat()

        # Generate content hash based on template content and timestamp
        # This ensures content hash changes when template is updated
        template_content_seed = f"{framework_version}:{current_timestamp}:{self.framework_path}"
        content_hash = hashlib.sha256(template_content_seed.encode()).hexdigest()[:16]

        variables = {
            "FRAMEWORK_VERSION": framework_version,
            "DEPLOYMENT_DATE": deployment_date,
            "DEPLOYMENT_DIR": str(self.framework_path),
            "PLATFORM": os.name,
            "PYTHON_CMD": "python3",
            "CURRENT_DATE": datetime.now().strftime("%Y-%m-%d"),
            "CURRENT_TIMESTAMP": current_timestamp,
            "WORKING_DIR": str(self.working_dir),
            "LAST_UPDATED": current_timestamp,
            "CONTENT_HASH": content_hash,
        }

        # Add deployment context if available
        if hasattr(self, "deployment_context") and self.deployment_context:
            variables.update(
                {
                    "DEPLOYMENT_TYPE": self.deployment_context.get("strategy", "unknown"),
                    "DEPLOYMENT_PLATFORM": self.deployment_context.get("config", {}).get(
                        "platform", "unknown"
                    ),
                }
            )

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
    
    def _protect_framework_template(self, framework_template_path: Path) -> None:
        """
        Ensure framework/CLAUDE.md template is protected from deletion.
        
        Args:
            framework_template_path: Path to the framework template file
        """
        try:
            import stat
            
            # Verify the file is the correct framework template
            if framework_template_path.name != "CLAUDE.md" or "framework" not in str(framework_template_path):
                self.logger.warning(f"Framework template protection called on non-framework file: {framework_template_path}")
                return
            
            # Check if file exists and is readable
            if not framework_template_path.exists():
                self.logger.error(f"Framework template file missing: {framework_template_path}")
                return
            
            if not framework_template_path.is_file():
                self.logger.error(f"Framework template path is not a file: {framework_template_path}")
                return
            
            # Get current permissions
            current_permissions = framework_template_path.stat().st_mode
            
            # Ensure file is readable by owner and group (at minimum)
            required_permissions = stat.S_IRUSR | stat.S_IRGRP
            
            if not (current_permissions & required_permissions):
                self.logger.warning(f"Framework template has insufficient read permissions: {framework_template_path}")
                try:
                    # Add read permissions for owner and group
                    framework_template_path.chmod(current_permissions | required_permissions)
                    self.logger.info(f"Fixed read permissions for framework template: {framework_template_path}")
                except Exception as perm_error:
                    self.logger.error(f"Failed to fix framework template permissions: {perm_error}")
            
            # Verify template content integrity
            content = framework_template_path.read_text()
            if len(content.strip()) == 0:
                self.logger.error(f"Framework template is empty: {framework_template_path}")
                return
            
            # Check for expected content markers
            expected_markers = ["AI ASSISTANT ROLE DESIGNATION", "CLAUDE_MD_VERSION", "Framework Context"]
            missing_markers = [marker for marker in expected_markers if marker not in content]
            
            if missing_markers:
                self.logger.warning(f"Framework template missing expected content markers: {missing_markers}")
            
            # Log protection verification
            self.logger.debug(f"Framework template protection verified: {framework_template_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to protect framework template {framework_template_path}: {e}")
    
    def _validate_framework_template_integrity(self) -> bool:
        """
        Validate that the framework template exists and has expected content.
        
        Returns:
            True if framework template is valid, False otherwise
        """
        try:
            framework_template_path = self.framework_path / "framework" / "CLAUDE.md"
            
            if not framework_template_path.exists():
                self.logger.error(f"Framework template does not exist: {framework_template_path}")
                return False
            
            if not framework_template_path.is_file():
                self.logger.error(f"Framework template path is not a file: {framework_template_path}")
                return False
            
            # Read and validate content
            content = framework_template_path.read_text()
            
            if len(content.strip()) == 0:
                self.logger.error(f"Framework template is empty: {framework_template_path}")
                return False
            
            # Check for critical content markers
            critical_markers = [
                "AI ASSISTANT ROLE DESIGNATION",
                "CLAUDE_MD_VERSION:",
                "Framework Context"
            ]
            
            missing_critical = [marker for marker in critical_markers if marker not in content]
            
            if missing_critical:
                self.logger.error(f"Framework template missing critical content: {missing_critical}")
                return False
            
            self.logger.debug(f"Framework template integrity verified: {framework_template_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate framework template integrity: {e}")
            return False
    
    def _backup_framework_template(self, framework_template_path: Path) -> Optional[Path]:
        """
        Create a backup of the framework template, maintaining only 2 most recent copies.
        
        Args:
            framework_template_path: Path to the framework template file
            
        Returns:
            Path to the created backup or None if failed
        """
        try:
            if not framework_template_path.exists() or not framework_template_path.is_file():
                self.logger.warning(f"Cannot backup non-existent framework template: {framework_template_path}")
                return None
            
            # Verify this is actually the framework template
            if framework_template_path.name != "CLAUDE.md" or "framework" not in str(framework_template_path):
                self.logger.warning(f"Backup requested for non-framework template: {framework_template_path}")
                return None
            
            # Ensure backup directory exists
            self.framework_backups_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            backup_filename = f"framework_CLAUDE_md_{timestamp}.backup"
            backup_path = self.framework_backups_dir / backup_filename
            
            # Handle duplicate timestamps (very unlikely but possible)
            counter = 1
            while backup_path.exists():
                backup_filename = f"framework_CLAUDE_md_{timestamp}_{counter:02d}.backup"
                backup_path = self.framework_backups_dir / backup_filename
                counter += 1
            
            # Create the backup
            shutil.copy2(framework_template_path, backup_path)
            
            # Rotate backups - keep only 2 most recent
            self._rotate_framework_backups()
            
            self._log_info_if_not_quiet(f"Framework template backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to backup framework template: {e}")
            return None
    
    def _rotate_framework_backups(self) -> None:
        """
        Rotate framework template backups, keeping only the 2 most recent copies.
        """
        try:
            if not self.framework_backups_dir.exists():
                return
            
            # Find all framework backup files
            backup_pattern = "framework_CLAUDE_md_*.backup"
            backup_files = list(self.framework_backups_dir.glob(backup_pattern))
            
            if len(backup_files) <= 2:
                return  # No rotation needed
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Keep only the 2 most recent, remove the rest
            files_to_remove = backup_files[2:]
            
            for old_backup in files_to_remove:
                try:
                    old_backup.unlink()
                    self.logger.debug(f"Removed old framework backup: {old_backup}")
                except Exception as remove_error:
                    self.logger.error(f"Failed to remove old framework backup {old_backup}: {remove_error}")
            
            if files_to_remove:
                self._log_info_if_not_quiet(f"Rotated framework backups: kept 2 most recent, removed {len(files_to_remove)} old backups")
                
        except Exception as e:
            self.logger.error(f"Failed to rotate framework backups: {e}")
    
    def get_framework_backup_status(self) -> Dict[str, Any]:
        """
        Get status information about framework template backups.
        
        Returns:
            Dictionary with backup status information
        """
        try:
            framework_template_path = self.framework_path / "framework" / "CLAUDE.md"
            
            status = {
                "framework_template_exists": framework_template_path.exists(),
                "framework_template_path": str(framework_template_path),
                "backup_directory": str(self.framework_backups_dir),
                "backup_directory_exists": self.framework_backups_dir.exists(),
                "backup_count": 0,
                "backups": []
            }
            
            if self.framework_backups_dir.exists():
                backup_pattern = "framework_CLAUDE_md_*.backup"
                backup_files = list(self.framework_backups_dir.glob(backup_pattern))
                backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                
                status["backup_count"] = len(backup_files)
                
                for backup_file in backup_files:
                    backup_stat = backup_file.stat()
                    status["backups"].append({
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size": backup_stat.st_size,
                        "created": datetime.fromtimestamp(backup_stat.st_mtime).isoformat(),
                        "age_hours": round((datetime.now().timestamp() - backup_stat.st_mtime) / 3600, 2)
                    })
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get framework backup status: {e}")
            return {"error": str(e)}
