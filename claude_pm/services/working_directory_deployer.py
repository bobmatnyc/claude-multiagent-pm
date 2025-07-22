#!/usr/bin/env python3
"""
Working Directory Deployer - ISS-0112 Claude PM Transformation

Deploys Claude PM framework components to working directories for project-specific operations.
Integrates with NPM installation architecture and validates deployment requirements.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.base_service import BaseService
from ..core.logging_config import get_logger
from .framework_deployment_validator import FrameworkDeploymentValidator, DeploymentValidationResult

logger = get_logger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for working directory deployment."""
    source_path: Path
    target_path: Path
    force_deployment: bool = False
    preserve_existing: bool = True
    create_backup: bool = True
    verify_after_deployment: bool = True


@dataclass
class DeploymentResult:
    """Result of working directory deployment."""
    success: bool
    target_directory: Path
    deployed_files: List[str] = None
    backup_location: Optional[Path] = None
    deployment_timestamp: str = ""
    error_message: Optional[str] = None
    validation_result: Optional[DeploymentValidationResult] = None
    
    def __post_init__(self):
        if self.deployed_files is None:
            self.deployed_files = []
        if not self.deployment_timestamp:
            self.deployment_timestamp = datetime.now().isoformat()


class WorkingDirectoryDeployer(BaseService):
    """
    Deploys Claude PM framework to working directories.
    
    Handles project-specific framework deployment with validation,
    backup, and verification capabilities.
    """
    
    def __init__(self):
        super().__init__("working_directory_deployer")
        # Try to find source installation
        self.claude_pm_home = self._find_source_installation()
        self.validator = FrameworkDeploymentValidator()
        self.template_files = self._define_template_files()
    
    async def _initialize(self) -> bool:
        """Initialize the working directory deployer."""
        try:
            logger.debug("Initializing WorkingDirectoryDeployer")
            await self.validator._initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize working directory deployer: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup working directory deployer resources."""
        try:
            logger.debug("Cleaning up WorkingDirectoryDeployer")
            await self.validator._cleanup()
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup working directory deployer: {e}")
            return False
        
    def _define_template_files(self) -> Dict[str, str]:
        """Define template files to deploy."""
        return {
            'config.json': 'templates/config/working-directory-config.json',
            'agents/project-agents.json': 'templates/project-agents.json',
            'templates/project-template.md': 'templates/project-template.md',
            'health/config.json': 'templates/health/working-directory-health.json'
        }
    
    def _find_source_installation(self) -> Path:
        """Find the source installation directory for templates."""
        # Try development directory first (for development/testing)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # Go up from services/working_directory_deployer.py
        if (project_root / "templates").exists():
            return project_root
        
        # Try NPM installation
        npm_home = Path.home() / ".claude-pm"
        if npm_home.exists() and (npm_home / "templates").exists():
            return npm_home
        
        # Default to npm home (even if doesn't exist)
        return npm_home
    
    async def deploy_to_working_directory(self, 
                                        config: Optional[DeploymentConfig] = None,
                                        working_directory: Optional[Path] = None) -> DeploymentResult:
        """
        Deploy framework to working directory.
        
        Args:
            working_directory: Target directory (defaults to current working directory)
            config: Deployment configuration
            
        Returns:
            DeploymentResult with deployment details
        """
        logger.info("Starting working directory deployment")
        
        # Set defaults
        if working_directory is None:
            working_directory = Path.cwd()
        
        if config is None:
            config = DeploymentConfig(
                source_path=self.claude_pm_home,
                target_path=working_directory / ".claude-pm"
            )
        
        try:
            # Check for tasks/ to tickets/ migration before deployment
            try:
                from ..utils.tasks_to_tickets_migration import check_and_migrate_tasks_directory
                
                migration_result = await check_and_migrate_tasks_directory(working_directory, silent=True)
                
                if migration_result.get("migrated"):
                    logger.info(f"Automatically migrated tasks/ to tickets/ in {working_directory}")
                    
            except Exception as migration_error:
                logger.warning(f"Tasks to tickets migration check failed: {migration_error}")
                # Continue with deployment even if migration fails
            
            # Pre-deployment validation
            pre_validation = await self._validate_pre_deployment(config)
            if not pre_validation['valid']:
                return DeploymentResult(
                    success=False,
                    target_directory=config.target_path,
                    error_message=f"Pre-deployment validation failed: {pre_validation['error']}"
                )
            
            # Create backup if requested
            backup_location = None
            if config.create_backup and config.target_path.exists():
                backup_location = await self._create_backup(config.target_path)
                logger.info(f"Created backup at: {backup_location}")
            
            # Perform deployment
            deployed_files = await self._deploy_files(config)
            
            # Post-deployment validation
            if config.verify_after_deployment:
                post_validation = await self.validator.validate_deployment(working_directory)
                if not post_validation.is_valid:
                    logger.warning("Post-deployment validation failed")
            else:
                post_validation = None
            
            result = DeploymentResult(
                success=True,
                target_directory=config.target_path,
                deployed_files=deployed_files,
                backup_location=backup_location,
                validation_result=post_validation
            )
            
            logger.info(f"Successfully deployed framework to {config.target_path}")
            return result
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(
                success=False,
                target_directory=config.target_path,
                error_message=str(e)
            )
    
    async def _validate_pre_deployment(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Validate deployment prerequisites."""
        validation = {
            'valid': True,
            'error': None,
            'details': {}
        }
        
        try:
            # Check source path exists (NPM installation)
            if not config.source_path.exists():
                validation['valid'] = False
                validation['error'] = f"Source path not found: {config.source_path}"
                return validation
            
            validation['details']['source_exists'] = True
            
            # Check required templates exist
            missing_templates = []
            for template_name, template_path in self.template_files.items():
                full_path = config.source_path / template_path
                if not full_path.exists():
                    missing_templates.append(template_name)
            
            if missing_templates:
                validation['valid'] = False
                validation['error'] = f"Missing templates: {', '.join(missing_templates)}"
                return validation
            
            validation['details']['templates_exist'] = True
            
            # Check target directory permissions
            # FIXED: Added validation to prevent undefined variable error when target_path is None
            if config.target_path is None:
                validation['valid'] = False
                validation['error'] = "Target path is not configured"
                return validation
            
            # Initialize parent_dir to None to prevent undefined variable error
            parent_dir = None
            
            try:
                parent_dir = config.target_path.parent
            except (AttributeError, TypeError) as e:
                validation['valid'] = False
                validation['error'] = f"Invalid target path configuration: {e}"
                return validation
            
            # Additional safety check to ensure parent_dir is defined
            if parent_dir is None:
                validation['valid'] = False
                validation['error'] = "Failed to determine parent directory"
                return validation
            
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    validation['valid'] = False
                    validation['error'] = f"Cannot create parent directory: {parent_dir}"
                    return validation
            
            validation['details']['target_writable'] = True
            
            # Check for force deployment requirement
            if config.target_path.exists() and not config.force_deployment:
                if not config.preserve_existing:
                    validation['valid'] = False
                    validation['error'] = "Target exists and force_deployment=False"
                    return validation
            
            validation['details']['deployment_allowed'] = True
            
            return validation
            
        except Exception as e:
            validation['valid'] = False
            validation['error'] = f"Pre-deployment validation error: {e}"
            return validation
    
    async def _deploy_files(self, config: DeploymentConfig) -> List[str]:
        """Deploy framework files to target directory."""
        deployed_files = []
        
        try:
            # Ensure target directory exists
            config.target_path.mkdir(parents=True, exist_ok=True)
            
            # Deploy each template file
            for target_name, source_path in self.template_files.items():
                source_file = config.source_path / source_path
                target_file = config.target_path / target_name
                
                # Ensure target subdirectory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                if source_file.exists():
                    # Deploy file with template processing
                    await self._deploy_file_with_processing(source_file, target_file, config)
                    deployed_files.append(target_name)
                    logger.debug(f"Deployed: {target_name}")
                else:
                    logger.warning(f"Source file not found: {source_file}")
            
            # Deploy core configuration
            await self._deploy_core_configuration(config)
            deployed_files.append("core-config.json")
            
            # Update deployment metadata
            await self._update_deployment_metadata(config, deployed_files)
            deployed_files.append("deployment-metadata.json")
            
            return deployed_files
            
        except Exception as e:
            logger.error(f"File deployment failed: {e}")
            raise
    
    async def _deploy_file_with_processing(self, source_file: Path, target_file: Path, 
                                         config: DeploymentConfig):
        """Deploy file with template variable processing."""
        try:
            # Read source content
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process template variables
            processed_content = await self._process_template_variables(content, config)
            
            # Write to target
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            logger.debug(f"Processed and deployed: {source_file} -> {target_file}")
            
        except Exception as e:
            logger.error(f"File processing failed for {source_file}: {e}")
            # Fallback to simple copy
            shutil.copy2(source_file, target_file)
    
    async def _process_template_variables(self, content: str, config: DeploymentConfig) -> str:
        """Process template variables in deployment content."""
        try:
            # Define template variables
            variables = {
                'DEPLOYMENT_DATE': datetime.now().isoformat(),
                'WORKING_DIRECTORY': str(config.target_path.parent),
                'FRAMEWORK_VERSION': await self._get_framework_version(),
                'DEPLOYMENT_TYPE': 'working_directory',
                'SOURCE_PATH': str(config.source_path),
                'TARGET_PATH': str(config.target_path)
            }
            
            # Replace template variables
            processed_content = content
            for var_name, var_value in variables.items():
                processed_content = processed_content.replace(f'{{{{{var_name}}}}}', str(var_value))
            
            return processed_content
            
        except Exception as e:
            logger.warning(f"Template processing failed: {e}")
            return content  # Return original content on error
    
    async def _get_framework_version(self) -> str:
        """Get framework version from various sources."""
        try:
            # Try package.json first
            package_json = self.claude_pm_home / "package.json"
            if package_json.exists():
                with open(package_json, 'r') as f:
                    data = json.load(f)
                return data.get('version', 'unknown')
            
            # Try VERSION file
            version_file = self.claude_pm_home / "VERSION"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    return f.read().strip()
            
            return 'unknown'
            
        except Exception as e:
            logger.warning(f"Failed to get framework version: {e}")
            return 'unknown'
    
    async def _deploy_core_configuration(self, config: DeploymentConfig):
        """Deploy core configuration for working directory."""
        try:
            core_config = {
                'deployment_type': 'working_directory',
                'source_installation': str(config.source_path),
                'deployed_at': datetime.now().isoformat(),
                'framework_version': await self._get_framework_version(),
                'working_directory': str(config.target_path.parent),
                'features': {
                    'agents': True,
                    'templates': True,
                    'health_monitoring': True,
                    'memory_integration': True
                },
                'paths': {
                    'agents': str(config.target_path / "agents"),
                    'templates': str(config.target_path / "templates"),
                    'health': str(config.target_path / "health"),
                    'logs': str(config.target_path / "logs")
                }
            }
            
            config_file = config.target_path / "config.json"
            with open(config_file, 'w') as f:
                json.dump(core_config, f, indent=2)
            
            logger.debug("Deployed core configuration")
            
        except Exception as e:
            logger.error(f"Core configuration deployment failed: {e}")
            raise
    
    async def _update_deployment_metadata(self, config: DeploymentConfig, deployed_files: List[str]):
        """Update deployment metadata."""
        try:
            metadata = {
                'deployment_id': hashlib.md5(
                    f"{config.target_path}{datetime.now()}".encode()
                ).hexdigest()[:8],
                'deployed_at': datetime.now().isoformat(),
                'source_path': str(config.source_path),
                'target_path': str(config.target_path),
                'deployed_files': deployed_files,
                'deployment_config': {
                    'force_deployment': config.force_deployment,
                    'preserve_existing': config.preserve_existing,
                    'create_backup': config.create_backup,
                    'verify_after_deployment': config.verify_after_deployment
                },
                'framework_version': await self._get_framework_version(),
                'deployer_version': '1.0.0'
            }
            
            metadata_file = config.target_path / "deployment-metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug("Updated deployment metadata")
            
        except Exception as e:
            logger.error(f"Metadata update failed: {e}")
            raise
    
    async def _create_backup(self, target_path: Path) -> Path:
        """Create backup of existing deployment."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{target_path.name}_backup_{timestamp}"
            backup_path = target_path.parent / backup_name
            
            if target_path.exists():
                shutil.copytree(target_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    async def verify_deployment(self, working_directory: Optional[Path] = None) -> DeploymentValidationResult:
        """Verify working directory deployment."""
        if working_directory is None:
            working_directory = Path.cwd()
        
        return await self.validator.validate_deployment(working_directory)
    
    async def get_deployment_status(self, working_directory: Optional[Path] = None) -> Dict[str, Any]:
        """Get deployment status for working directory."""
        if working_directory is None:
            working_directory = Path.cwd()
        
        try:
            claude_pm_dir = working_directory / ".claude-pm"
            
            status = {
                'deployed': claude_pm_dir.exists(),
                'working_directory': str(working_directory),
                'claude_pm_directory': str(claude_pm_dir),
                'last_check': datetime.now().isoformat()
            }
            
            if claude_pm_dir.exists():
                # Get deployment metadata
                metadata_file = claude_pm_dir / "deployment-metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    status['metadata'] = metadata
                
                # Get validation results
                validation_result = await self.verify_deployment(working_directory)
                status['validation'] = {
                    'valid': validation_result.is_valid,
                    'framework_deployed': validation_result.framework_deployed,
                    'working_directory_configured': validation_result.working_directory_configured
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {
                'deployed': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def undeploy_from_working_directory(self, working_directory: Optional[Path] = None,
                                            create_backup: bool = True) -> bool:
        """Remove framework deployment from working directory."""
        if working_directory is None:
            working_directory = Path.cwd()
        
        try:
            claude_pm_dir = working_directory / ".claude-pm"
            
            if not claude_pm_dir.exists():
                logger.info("No deployment found to remove")
                return True
            
            # Create backup if requested
            if create_backup:
                await self._create_backup(claude_pm_dir)
            
            # Remove deployment
            shutil.rmtree(claude_pm_dir)
            logger.info(f"Removed deployment from {claude_pm_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Undeployment failed: {e}")
            return False
    
    async def list_deployments(self, search_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """List framework deployments in directory tree."""
        if search_path is None:
            search_path = Path.cwd()
        
        deployments = []
        
        try:
            for claude_pm_dir in search_path.rglob(".claude-pm"):
                if claude_pm_dir.is_dir():
                    deployment_info = {
                        'path': str(claude_pm_dir),
                        'working_directory': str(claude_pm_dir.parent),
                        'discovered_at': datetime.now().isoformat()
                    }
                    
                    # Get metadata if available
                    metadata_file = claude_pm_dir / "deployment-metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            deployment_info['metadata'] = metadata
                        except Exception as e:
                            logger.warning(f"Failed to read metadata for {claude_pm_dir}: {e}")
                    
                    deployments.append(deployment_info)
            
            logger.info(f"Found {len(deployments)} deployments")
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            return []