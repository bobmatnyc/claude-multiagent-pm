"""
Template Manager Service - Template management and processing system

This module provides comprehensive template management functionality including:
- Template discovery and loading from multiple sources
- Template processing with variable substitution
- Template validation and metadata management
- Integration with deployment and project systems
- Support for project, ticket, agent, and document templates

Created: 2025-07-16 (Framework completion)
Purpose: Complete standardized error handling system with missing template_manager
"""

import asyncio
import logging
import json
import re
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from claude_pm.core.response_types import ServiceResponse, TaskToolResponse

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of templates supported by the system"""
    PROJECT = "project"
    TICKET = "ticket"
    AGENT = "agent"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    CONFIG = "config"
    SCRIPT = "script"


class TemplateSource(Enum):
    """Sources where templates can be found"""
    FRAMEWORK = "framework"
    USER = "user"
    PROJECT = "project"
    SYSTEM = "system"


class TemplateVersion(Enum):
    """Template version formats"""
    V1 = "v1"
    V2 = "v2"
    LEGACY = "legacy"


@dataclass
class TemplateMetadata:
    """Metadata about a template"""
    name: str
    type: TemplateType
    source: TemplateSource
    version: TemplateVersion
    description: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    author: Optional[str] = None
    file_path: Optional[Path] = None


@dataclass
class TemplateProcessingResult:
    """Result of template processing operation"""
    success: bool
    template_name: str
    output_path: Optional[Path] = None
    processed_content: Optional[str] = None
    variables_used: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None


class TemplateManager:
    """
    Template Manager Service - Comprehensive template management
    
    Features:
    - Multi-source template discovery (framework, user, project)
    - Template processing with Handlebars-style variable substitution
    - Template metadata management and validation
    - Template deployment and copying operations
    - Integration with project and deployment systems
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize template manager
        
        Args:
            config: Configuration dictionary with options
        """
        self.name = "template_manager"
        self.config = config or {}
        
        # Configuration options
        self.template_extensions = self.config.get("template_extensions", [".template", ".tmpl", ".tpl"])
        self.variable_pattern = self.config.get("variable_pattern", r"\{\{(\w+)\}\}")
        self.enable_caching = self.config.get("enable_caching", True)
        
        # State tracking
        self._templates: Dict[str, TemplateMetadata] = {}
        self._template_cache: Dict[str, str] = {}
        self._template_sources: List[Path] = []
        self._initialized = False
        
        logger.info(f"TemplateManager initialized with config: {self.config}")
    
    async def initialize(self) -> ServiceResponse:
        """
        Initialize template manager service
        
        Returns:
            ServiceResponse indicating initialization success
        """
        try:
            logger.info("Initializing template manager...")
            
            # Discover template sources
            await self._discover_template_sources()
            
            # Load templates from all sources
            await self._load_templates()
            
            self._initialized = True
            logger.info(f"Template manager initialized successfully with {len(self._templates)} templates")
            
            return ServiceResponse(
                operation_id="template_manager_init",
                success=True,
                data={
                    "initialized": True,
                    "templates_loaded": len(self._templates),
                    "sources_discovered": len(self._template_sources)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize template manager: {e}")
            return ServiceResponse(
                operation_id="template_manager_init",
                success=False,
                error=str(e)
            )
    
    async def _discover_template_sources(self) -> None:
        """Discover all available template sources"""
        self._template_sources = []
        
        # Check if we're running from a wheel installation
        is_wheel_install = False
        try:
            import claude_pm
            package_path = Path(claude_pm.__file__).parent
            path_str = str(package_path.resolve())
            is_wheel_install = 'site-packages' in path_str or 'dist-packages' in path_str
        except Exception:
            pass
        
        # Framework templates (highest priority)
        framework_templates = Path.cwd() / "framework" / "templates"
        if framework_templates.exists():
            self._template_sources.append(framework_templates)
            logger.debug(f"Found framework templates: {framework_templates}")
        
        # Project templates
        project_templates = Path.cwd() / ".claude-pm" / "templates"
        if project_templates.exists():
            self._template_sources.append(project_templates)
            logger.debug(f"Found project templates: {project_templates}")
        
        # User templates
        try:
            user_home = Path.home()
            user_templates = user_home / ".claude-pm" / "templates"
            if user_templates.exists():
                self._template_sources.append(user_templates)
                logger.debug(f"Found user templates: {user_templates}")
        except Exception as e:
            logger.warning(f"Failed to check user templates: {e}")
        
        # System templates (from package)
        try:
            import claude_pm
            package_path = Path(claude_pm.__file__).parent
            
            # For wheel installations, check the data directory
            if is_wheel_install:
                data_templates = package_path / "data" / "templates"
                if data_templates.exists():
                    self._template_sources.append(data_templates)
                    logger.debug(f"Found system templates in data directory: {data_templates}")
                else:
                    # Fallback to legacy location
                    system_templates = package_path / "templates"
                    if system_templates.exists():
                        self._template_sources.append(system_templates)
                        logger.debug(f"Found system templates: {system_templates}")
            else:
                # Source installation
                system_templates = package_path / "templates"
                if system_templates.exists():
                    self._template_sources.append(system_templates)
                    logger.debug(f"Found system templates: {system_templates}")
        except Exception as e:
            logger.warning(f"Failed to find system templates: {e}")
        
        logger.info(f"Discovered {len(self._template_sources)} template sources")
    
    async def _load_templates(self) -> None:
        """Load templates from all discovered sources"""
        self._templates = {}
        
        for source_path in self._template_sources:
            await self._load_templates_from_source(source_path)
    
    async def _load_templates_from_source(self, source_path: Path) -> None:
        """Load templates from a specific source directory"""
        try:
            source_type = self._determine_source_type(source_path)
            
            # Recursively find all template files
            for template_file in source_path.rglob("*"):
                if template_file.is_file() and any(
                    str(template_file).endswith(ext) for ext in self.template_extensions
                ):
                    await self._load_template_file(template_file, source_type)
                    
        except Exception as e:
            logger.warning(f"Failed to load templates from {source_path}: {e}")
    
    def _determine_source_type(self, source_path: Path) -> TemplateSource:
        """Determine the source type based on path"""
        path_str = str(source_path)
        
        if "framework" in path_str:
            return TemplateSource.FRAMEWORK
        elif ".claude-pm" in path_str and str(Path.home()) in path_str:
            return TemplateSource.USER
        elif ".claude-pm" in path_str:
            return TemplateSource.PROJECT
        else:
            return TemplateSource.SYSTEM
    
    async def _load_template_file(self, template_file: Path, source_type: TemplateSource) -> None:
        """Load a single template file"""
        try:
            # Extract template name and type
            template_name = template_file.stem
            template_type = self._determine_template_type(template_file)
            
            # Read template content
            content = template_file.read_text(encoding='utf-8')
            
            # Extract variables from content
            variables = self._extract_variables(content)
            
            # Create metadata
            metadata = TemplateMetadata(
                name=template_name,
                type=template_type,
                source=source_type,
                version=TemplateVersion.V2,  # Default to V2
                variables=variables,
                file_path=template_file,
                modified_date=datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
            )
            
            # Cache content if enabled
            if self.enable_caching:
                self._template_cache[template_name] = content
            
            # Store metadata
            self._templates[template_name] = metadata
            logger.debug(f"Loaded template: {template_name} from {source_type.value}")
            
        except Exception as e:
            logger.warning(f"Failed to load template file {template_file}: {e}")
    
    def _determine_template_type(self, template_file: Path) -> TemplateType:
        """Determine template type based on file path and name"""
        path_parts = template_file.parts
        name_lower = template_file.name.lower()
        
        # Check path for type indicators
        for part in path_parts:
            part_lower = part.lower()
            if part_lower in ["projects", "project"]:
                return TemplateType.PROJECT
            elif part_lower in ["tickets", "ticket", "issues", "issue"]:
                return TemplateType.TICKET
            elif part_lower in ["agents", "agent"]:
                return TemplateType.AGENT
            elif part_lower in ["documents", "docs", "documentation"]:
                return TemplateType.DOCUMENT
            elif part_lower in ["workflows", "workflow"]:
                return TemplateType.WORKFLOW
            elif part_lower in ["configs", "config", "configuration"]:
                return TemplateType.CONFIG
            elif part_lower in ["scripts", "script"]:
                return TemplateType.SCRIPT
        
        # Check filename for type indicators
        if any(keyword in name_lower for keyword in ["project", "proj"]):
            return TemplateType.PROJECT
        elif any(keyword in name_lower for keyword in ["ticket", "issue", "task"]):
            return TemplateType.TICKET
        elif any(keyword in name_lower for keyword in ["agent", "bot"]):
            return TemplateType.AGENT
        elif any(keyword in name_lower for keyword in ["doc", "readme", "guide"]):
            return TemplateType.DOCUMENT
        elif any(keyword in name_lower for keyword in ["workflow", "flow"]):
            return TemplateType.WORKFLOW
        elif any(keyword in name_lower for keyword in ["config", "cfg"]):
            return TemplateType.CONFIG
        elif any(keyword in name_lower for keyword in ["script", "sh", "py"]):
            return TemplateType.SCRIPT
        
        # Default to document
        return TemplateType.DOCUMENT
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content"""
        variables = []
        matches = re.finditer(self.variable_pattern, content)
        
        for match in matches:
            var_name = match.group(1)
            if var_name not in variables:
                variables.append(var_name)
        
        return sorted(variables)
    
    async def process_template(
        self, 
        template_name: str, 
        variables: Dict[str, str], 
        output_path: Optional[Path] = None
    ) -> TemplateProcessingResult:
        """
        Process a template with variable substitution
        
        Args:
            template_name: Name of template to process
            variables: Dictionary of variable values
            output_path: Optional path to write processed template
            
        Returns:
            TemplateProcessingResult with operation details
        """
        start_time = datetime.now()
        
        try:
            # Get template metadata
            metadata = self._templates.get(template_name)
            if not metadata:
                return TemplateProcessingResult(
                    success=False,
                    template_name=template_name,
                    error_message=f"Template '{template_name}' not found"
                )
            
            # Load template content
            content = await self._get_template_content(template_name)
            if not content:
                return TemplateProcessingResult(
                    success=False,
                    template_name=template_name,
                    error_message=f"Failed to load template content for '{template_name}'"
                )
            
            # Process variables
            processed_content, warnings = self._substitute_variables(content, variables, metadata.variables)
            
            # Write to output path if specified
            if output_path:
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(processed_content, encoding='utf-8')
                except Exception as e:
                    return TemplateProcessingResult(
                        success=False,
                        template_name=template_name,
                        error_message=f"Failed to write output file: {e}"
                    )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return TemplateProcessingResult(
                success=True,
                template_name=template_name,
                output_path=output_path,
                processed_content=processed_content,
                variables_used=variables,
                warnings=warnings,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return TemplateProcessingResult(
                success=False,
                template_name=template_name,
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    async def _get_template_content(self, template_name: str) -> Optional[str]:
        """Get template content from cache or file"""
        # Check cache first
        if self.enable_caching and template_name in self._template_cache:
            return self._template_cache[template_name]
        
        # Load from file
        metadata = self._templates.get(template_name)
        if metadata and metadata.file_path and metadata.file_path.exists():
            try:
                content = metadata.file_path.read_text(encoding='utf-8')
                
                # Cache if enabled
                if self.enable_caching:
                    self._template_cache[template_name] = content
                
                return content
            except Exception as e:
                logger.error(f"Failed to read template file {metadata.file_path}: {e}")
        
        return None
    
    def _substitute_variables(
        self, 
        content: str, 
        variables: Dict[str, str], 
        expected_variables: List[str]
    ) -> tuple[str, List[str]]:
        """
        Substitute variables in template content
        
        Returns:
            Tuple of (processed_content, warnings)
        """
        warnings = []
        processed_content = content
        
        # Check for missing variables
        for var_name in expected_variables:
            if var_name not in variables:
                warnings.append(f"Missing value for variable: {var_name}")
        
        # Substitute variables
        for var_name, var_value in variables.items():
            pattern = f"{{{{{var_name}}}}}"
            processed_content = processed_content.replace(pattern, str(var_value))
        
        # Check for unsubstituted variables
        remaining_vars = re.findall(self.variable_pattern, processed_content)
        for var_name in remaining_vars:
            if var_name not in [w.split(": ")[1] for w in warnings if "Missing value" in w]:
                warnings.append(f"Unsubstituted variable: {var_name}")
        
        return processed_content, warnings
    
    async def copy_template(
        self, 
        template_name: str, 
        destination: Path,
        variables: Optional[Dict[str, str]] = None
    ) -> ServiceResponse:
        """
        Copy and optionally process a template to a destination
        
        Args:
            template_name: Name of template to copy
            destination: Destination path
            variables: Optional variables for processing
            
        Returns:
            ServiceResponse with operation details
        """
        try:
            metadata = self._templates.get(template_name)
            if not metadata:
                return ServiceResponse(
                    operation_id="copy_template",
                    success=False,
                    error=f"Template '{template_name}' not found"
                )
            
            if not metadata.file_path or not metadata.file_path.exists():
                return ServiceResponse(
                    operation_id="copy_template",
                    success=False,
                    error=f"Template file not found: {metadata.file_path}"
                )
            
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy and process if variables provided
            if variables:
                result = await self.process_template(template_name, variables, destination)
                if result.success:
                    return ServiceResponse(
                        operation_id="copy_template",
                        success=True,
                        data={
                            "template_name": template_name,
                            "destination": str(destination),
                            "processed": True,
                            "variables_used": result.variables_used,
                            "warnings": result.warnings
                        }
                    )
                else:
                    return ServiceResponse(
                        operation_id="copy_template",
                        success=False,
                        error=result.error_message
                    )
            else:
                # Simple copy without processing
                shutil.copy2(metadata.file_path, destination)
                return ServiceResponse(
                    operation_id="copy_template",
                    success=True,
                    data={
                        "template_name": template_name,
                        "destination": str(destination),
                        "processed": False
                    }
                )
                
        except Exception as e:
            return ServiceResponse(
                operation_id="copy_template",
                success=False,
                error=str(e)
            )
    
    def list_templates(
        self, 
        template_type: Optional[TemplateType] = None,
        source: Optional[TemplateSource] = None
    ) -> List[TemplateMetadata]:
        """
        List available templates with optional filtering
        
        Args:
            template_type: Optional filter by template type
            source: Optional filter by source
            
        Returns:
            List of template metadata
        """
        templates = list(self._templates.values())
        
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        
        if source:
            templates = [t for t in templates if t.source == source]
        
        return sorted(templates, key=lambda t: t.name)
    
    def get_template_metadata(self, template_name: str) -> Optional[TemplateMetadata]:
        """Get metadata for a specific template"""
        return self._templates.get(template_name)
    
    async def validate_template(self, template_name: str) -> ServiceResponse:
        """
        Validate a template for correctness
        
        Args:
            template_name: Name of template to validate
            
        Returns:
            ServiceResponse with validation results
        """
        try:
            metadata = self._templates.get(template_name)
            if not metadata:
                return ServiceResponse(
                    operation_id="validate_template",
                    success=False,
                    error=f"Template '{template_name}' not found"
                )
            
            validation_results = {
                "template_name": template_name,
                "file_exists": metadata.file_path and metadata.file_path.exists(),
                "variables_found": len(metadata.variables),
                "syntax_errors": [],
                "warnings": []
            }
            
            # Check file exists
            if not validation_results["file_exists"]:
                validation_results["syntax_errors"].append("Template file does not exist")
                return ServiceResponse(
                    operation_id="validate_template",
                    success=False,
                    data=validation_results,
                    error="Template file validation failed"
                )
            
            # Load and validate content
            content = await self._get_template_content(template_name)
            if not content:
                validation_results["syntax_errors"].append("Could not read template content")
            else:
                # Check for malformed variables
                malformed_vars = re.findall(r'\{[^}]*\}', content)
                for var in malformed_vars:
                    if not re.match(self.variable_pattern, var):
                        validation_results["syntax_errors"].append(f"Malformed variable: {var}")
                
                # Check for empty variables
                if not metadata.variables:
                    validation_results["warnings"].append("Template contains no variables")
            
            success = len(validation_results["syntax_errors"]) == 0
            
            return ServiceResponse(
                operation_id="validate_template",
                success=success,
                data=validation_results,
                error="Template validation failed" if not success else None
            )
            
        except Exception as e:
            return ServiceResponse(
                operation_id="validate_template",
                success=False,
                error=str(e)
            )
    
    async def refresh_templates(self) -> ServiceResponse:
        """
        Refresh template discovery and loading
        
        Returns:
            ServiceResponse with refresh results
        """
        try:
            logger.info("Refreshing template discovery...")
            
            # Clear caches
            self._templates.clear()
            self._template_cache.clear()
            
            # Rediscover and reload
            await self._discover_template_sources()
            await self._load_templates()
            
            return ServiceResponse(
                operation_id="refresh_templates",
                success=True,
                data={
                    "templates_loaded": len(self._templates),
                    "sources_discovered": len(self._template_sources)
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                operation_id="refresh_templates",
                success=False,
                error=str(e)
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get template manager status"""
        return {
            "initialized": self._initialized,
            "templates_loaded": len(self._templates),
            "sources_discovered": len(self._template_sources),
            "cache_enabled": self.enable_caching,
            "cached_templates": len(self._template_cache)
        }


# Export key classes and functions
__all__ = [
    'TemplateManager',
    'TemplateType',
    'TemplateSource', 
    'TemplateVersion',
    'TemplateMetadata',
    'TemplateProcessingResult'
]