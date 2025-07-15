#!/usr/bin/env python3
"""
Framework Deployment Validator - ISS-0112 Claude PM Transformation

Comprehensive validation system for framework deployment requirements.
Ensures framework is properly deployed before any claude-pm operations.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.base_service import BaseService
from ..core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DeploymentValidationResult:
    """Result of framework deployment validation."""
    is_valid: bool
    framework_deployed: bool
    npm_installation_found: bool
    claude_pm_directory: Optional[Path] = None
    working_directory_configured: bool = False
    validation_details: Dict[str, Any] = None
    error_message: Optional[str] = None
    actionable_guidance: List[str] = None
    
    def __post_init__(self):
        if self.validation_details is None:
            self.validation_details = {}
        if self.actionable_guidance is None:
            self.actionable_guidance = []


@dataclass 
class FrameworkComponent:
    """Framework component validation."""
    name: str
    path: Path
    required: bool = True
    valid: bool = False
    error: Optional[str] = None


class FrameworkDeploymentValidator(BaseService):
    """
    Comprehensive framework deployment validator.
    
    Validates that Claude PM framework is properly deployed with all required
    components before allowing any operations to proceed.
    """
    
    def __init__(self):
        super().__init__("framework_deployment_validator")
        self.claude_pm_home = Path.home() / ".claude-pm"
        self.expected_components = self._define_expected_components()
    
    async def _initialize(self) -> bool:
        """Initialize the deployment validator."""
        try:
            logger.debug("Initializing FrameworkDeploymentValidator")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize deployment validator: {e}")
            return False
    
    async def _cleanup(self) -> bool:
        """Cleanup deployment validator resources."""
        try:
            logger.debug("Cleaning up FrameworkDeploymentValidator")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup deployment validator: {e}")
            return False
        
    def _define_expected_components(self) -> Dict[str, FrameworkComponent]:
        """Define expected framework components."""
        base_path = self.claude_pm_home
        
        return {
            'main_directory': FrameworkComponent(
                name='Main Claude PM Directory',
                path=base_path,
                required=True
            ),
            'config_file': FrameworkComponent(
                name='Configuration File',
                path=base_path / "config.json",
                required=True
            ),
            'agents_directory': FrameworkComponent(
                name='Agents Directory',
                path=base_path / "agents",
                required=True
            ),
            'templates_directory': FrameworkComponent(
                name='Templates Directory', 
                path=base_path / "templates",
                required=True
            ),
            'framework_template': FrameworkComponent(
                name='Framework Template',
                path=base_path / "templates" / "CLAUDE.md",
                required=True
            ),
            'version_file': FrameworkComponent(
                name='Version File',
                path=base_path / "VERSION",
                required=True
            ),
            'health_monitor': FrameworkComponent(
                name='Health Monitor Config',
                path=base_path / "health" / "config.json",
                required=False
            ),
            'services_directory': FrameworkComponent(
                name='Services Directory',
                path=base_path / "services",
                required=False
            ),
        }
    
    async def validate_deployment(self, working_directory: Optional[Path] = None) -> DeploymentValidationResult:
        """
        Comprehensive deployment validation.
        
        Args:
            working_directory: Optional working directory to validate for project deployment
            
        Returns:
            DeploymentValidationResult with comprehensive validation details
        """
        logger.info("Starting comprehensive framework deployment validation")
        
        try:
            # Validate NPM installation
            npm_result = await self._validate_npm_installation()
            
            # Validate framework deployment
            framework_result = await self._validate_framework_deployment()
            
            # Validate working directory if provided
            working_dir_result = True
            if working_directory:
                working_dir_result = await self._validate_working_directory_deployment(working_directory)
            
            # Combine results
            is_valid = npm_result['valid'] and framework_result['valid'] and working_dir_result
            
            result = DeploymentValidationResult(
                is_valid=is_valid,
                framework_deployed=framework_result['valid'],
                npm_installation_found=npm_result['valid'],
                claude_pm_directory=self.claude_pm_home if self.claude_pm_home.exists() else None,
                working_directory_configured=working_dir_result,
                validation_details={
                    'npm_installation': npm_result,
                    'framework_deployment': framework_result,
                    'working_directory': working_dir_result,
                    'validation_timestamp': datetime.now().isoformat(),
                    'validator_version': '1.0.0'
                }
            )
            
            # Generate actionable guidance if validation failed
            if not is_valid:
                result.actionable_guidance = self._generate_actionable_guidance(
                    npm_result, framework_result, working_dir_result
                )
                result.error_message = self._generate_error_message(result)
            
            logger.info(f"Deployment validation completed: valid={is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Deployment validation failed: {e}")
            return DeploymentValidationResult(
                is_valid=False,
                framework_deployed=False,
                npm_installation_found=False,
                error_message=f"Validation error: {str(e)}",
                actionable_guidance=["Run 'claude-pm deploy' to fix deployment issues"]
            )
    
    async def _validate_npm_installation(self) -> Dict[str, Any]:
        """Validate NPM installation and ~/.claude-pm/ structure."""
        logger.debug("Validating NPM installation")
        
        validation = {
            'valid': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Check if ~/.claude-pm exists
            if not self.claude_pm_home.exists():
                validation['errors'].append("~/.claude-pm directory does not exist")
                validation['details']['claude_pm_home_exists'] = False
                return validation
            
            validation['details']['claude_pm_home_exists'] = True
            
            # Check for NPM installation indicators
            npm_indicators = [
                self.claude_pm_home / "package.json",
                self.claude_pm_home / "node_modules",
                self.claude_pm_home / ".npm-installation"
            ]
            
            npm_found = any(indicator.exists() for indicator in npm_indicators)
            validation['details']['npm_indicators_found'] = npm_found
            
            if not npm_found:
                validation['errors'].append("No NPM installation indicators found in ~/.claude-pm")
                return validation
            
            # Validate package.json if it exists
            package_json_path = self.claude_pm_home / "package.json"
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    if package_data.get('name') == '@bobmatnyc/claude-multiagent-pm':
                        validation['details']['correct_package'] = True
                        validation['details']['version'] = package_data.get('version')
                    else:
                        validation['errors'].append("Incorrect package name in package.json")
                        validation['details']['correct_package'] = False
                        
                except Exception as e:
                    validation['errors'].append(f"Failed to parse package.json: {e}")
                    validation['details']['package_json_valid'] = False
            
            # If we reach here with no errors, NPM installation is valid
            if not validation['errors']:
                validation['valid'] = True
                logger.debug("NPM installation validation passed")
            
            return validation
            
        except Exception as e:
            validation['errors'].append(f"NPM validation error: {e}")
            return validation
    
    async def _validate_framework_deployment(self) -> Dict[str, Any]:
        """Validate framework deployment components."""
        logger.debug("Validating framework deployment")
        
        validation = {
            'valid': False,
            'details': {},
            'errors': [],
            'components': {}
        }
        
        try:
            # Validate each component
            all_required_valid = True
            
            for component_id, component in self.expected_components.items():
                component_validation = await self._validate_component(component)
                validation['components'][component_id] = component_validation
                
                if component.required and not component_validation['valid']:
                    all_required_valid = False
                    validation['errors'].append(
                        f"Required component missing: {component.name} at {component.path}"
                    )
            
            # Check configuration validity
            config_valid = await self._validate_configuration()
            validation['details']['configuration_valid'] = config_valid
            
            if not config_valid:
                validation['errors'].append("Framework configuration is invalid")
                all_required_valid = False
            
            # Overall validation
            validation['valid'] = all_required_valid and config_valid
            
            if validation['valid']:
                logger.debug("Framework deployment validation passed")
            
            return validation
            
        except Exception as e:
            validation['errors'].append(f"Framework validation error: {e}")
            return validation
    
    async def _validate_component(self, component: FrameworkComponent) -> Dict[str, Any]:
        """Validate individual framework component."""
        validation = {
            'valid': False,
            'exists': False,
            'readable': False,
            'size': 0,
            'modified': None
        }
        
        try:
            if component.path.exists():
                validation['exists'] = True
                
                # Check if readable
                try:
                    if component.path.is_file():
                        with open(component.path, 'r') as f:
                            content = f.read(100)  # Read first 100 chars
                        validation['readable'] = True
                        validation['size'] = component.path.stat().st_size
                    elif component.path.is_dir():
                        list(component.path.iterdir())  # Try to list directory
                        validation['readable'] = True
                        validation['size'] = len(list(component.path.iterdir()))
                        
                    validation['modified'] = datetime.fromtimestamp(
                        component.path.stat().st_mtime
                    ).isoformat()
                    
                except Exception as e:
                    logger.warning(f"Component {component.name} not readable: {e}")
                    validation['readable'] = False
                
                # Component is valid if it exists and is readable
                validation['valid'] = validation['exists'] and validation['readable']
            
            return validation
            
        except Exception as e:
            logger.error(f"Component validation error for {component.name}: {e}")
            return validation
    
    async def _validate_configuration(self) -> bool:
        """Validate framework configuration files."""
        try:
            config_path = self.claude_pm_home / "config.json"
            
            if not config_path.exists():
                return False
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Validate required configuration keys
            required_keys = ['version', 'installType', 'installationComplete']
            for key in required_keys:
                if key not in config_data:
                    logger.warning(f"Missing required config key: {key}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    async def _validate_working_directory_deployment(self, working_directory: Path) -> bool:
        """Validate working directory framework deployment."""
        try:
            claude_pm_dir = working_directory / ".claude-pm"
            
            if not claude_pm_dir.exists():
                return False
            
            # Check for essential working directory components
            required_files = [
                claude_pm_dir / "CLAUDE.md",
                claude_pm_dir / "config.json"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    logger.warning(f"Missing working directory component: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Working directory validation error: {e}")
            return False
    
    def _generate_actionable_guidance(self, npm_result: Dict, framework_result: Dict, 
                                    working_dir_result: bool) -> List[str]:
        """Generate actionable guidance based on validation results."""
        guidance = []
        
        # NPM installation guidance
        if not npm_result['valid']:
            guidance.extend([
                "🚀 Install Claude PM Framework:",
                "   npm install -g @bobmatnyc/claude-multiagent-pm",
                "",
                "🔧 Alternative installation:",
                "   npx @bobmatnyc/claude-multiagent-pm deploy",
                ""
            ])
        
        # Framework deployment guidance
        if not framework_result['valid']:
            guidance.extend([
                "📦 Deploy framework to working directory:",
                "   claude-pm deploy",
                "",
                "🔍 Check deployment status:",
                "   claude-pm status --deployment",
                ""
            ])
        
        # Working directory guidance
        if not working_dir_result:
            guidance.extend([
                "📁 Initialize working directory:",
                "   claude-pm init",
                "",
                "🔄 Re-deploy framework:",
                "   claude-pm deploy --force",
                ""
            ])
        
        # General troubleshooting
        guidance.extend([
            "🆘 Get comprehensive help:",
            "   claude-pm --help",
            "",
            "🔧 System diagnostics:",
            "   claude-pm diagnose",
            ""
        ])
        
        return guidance
    
    def _generate_error_message(self, result: DeploymentValidationResult) -> str:
        """Generate comprehensive error message."""
        messages = []
        
        if not result.npm_installation_found:
            messages.append("❌ Claude PM Framework not installed via NPM")
        
        if not result.framework_deployed:
            messages.append("❌ Framework not deployed to working directory")
        
        if not result.working_directory_configured:
            messages.append("❌ Working directory not properly configured")
        
        return " | ".join(messages) if messages else "❌ Framework deployment validation failed"
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get comprehensive deployment status."""
        try:
            validation_result = await self.validate_deployment()
            
            status = {
                'deployment_valid': validation_result.is_valid,
                'npm_installation': validation_result.npm_installation_found,
                'framework_deployed': validation_result.framework_deployed,
                'claude_pm_directory': str(validation_result.claude_pm_directory) if validation_result.claude_pm_directory else None,
                'working_directory_configured': validation_result.working_directory_configured,
                'validation_details': validation_result.validation_details,
                'last_check': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {
                'deployment_valid': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def generate_deployment_report(self) -> str:
        """Generate detailed deployment validation report."""
        try:
            status = await self.get_deployment_status()
            
            report_lines = [
                "=" * 80,
                "CLAUDE PM FRAMEWORK DEPLOYMENT VALIDATION REPORT",
                "=" * 80,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "🎯 VALIDATION SUMMARY:",
                f"   Overall Status: {'✅ VALID' if status['deployment_valid'] else '❌ INVALID'}",
                f"   NPM Installation: {'✅ Found' if status['npm_installation'] else '❌ Missing'}",
                f"   Framework Deployed: {'✅ Yes' if status['framework_deployed'] else '❌ No'}",
                f"   Working Directory: {'✅ Configured' if status['working_directory_configured'] else '❌ Not Configured'}",
                "",
            ]
            
            if status.get('claude_pm_directory'):
                report_lines.extend([
                    "📁 CLAUDE PM DIRECTORY:",
                    f"   Location: {status['claude_pm_directory']}",
                    ""
                ])
            
            # Add detailed validation information
            if status.get('validation_details'):
                report_lines.extend([
                    "🔍 DETAILED VALIDATION:",
                    json.dumps(status['validation_details'], indent=2),
                    ""
                ])
            
            report_lines.append("=" * 80)
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Failed to generate deployment report: {e}")
            return f"❌ Failed to generate deployment report: {e}"