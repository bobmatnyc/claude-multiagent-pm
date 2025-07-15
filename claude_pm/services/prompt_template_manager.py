"""
Prompt Template Management System

This module provides comprehensive prompt template management capabilities
including versioning, rollback, comparison, and template validation.

Key Features:
- Template versioning and history tracking
- Rollback capabilities with change impact analysis
- Template comparison and diff functionality
- Template validation and testing
- Agent-specific template management
- Template deployment and distribution

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import difflib
from pathlib import Path
import shutil
import re
import yaml


class TemplateStatus(Enum):
    """Template status options"""
    DRAFT = "draft"
    TESTING = "testing"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class TemplateType(Enum):
    """Template type options"""
    AGENT_PROMPT = "agent_prompt"
    SYSTEM_PROMPT = "system_prompt"
    TASK_TEMPLATE = "task_template"
    RESPONSE_TEMPLATE = "response_template"
    VALIDATION_TEMPLATE = "validation_template"


@dataclass
class TemplateVersion:
    """Represents a version of a template"""
    template_id: str
    version: str
    content: str
    metadata: Dict[str, Any]
    author: str
    timestamp: datetime
    status: TemplateStatus
    parent_version: Optional[str] = None
    change_summary: str = ""
    validation_results: Optional[Dict[str, Any]] = None
    usage_metrics: Optional[Dict[str, Any]] = None
    rollback_info: Optional[Dict[str, Any]] = None


@dataclass
class TemplateComparison:
    """Comparison between two template versions"""
    template_id: str
    version_a: str
    version_b: str
    diff_html: str
    diff_text: str
    change_summary: str
    similarity_score: float
    impact_analysis: Dict[str, Any]
    timestamp: datetime


@dataclass
class TemplateDeployment:
    """Template deployment record"""
    deployment_id: str
    template_id: str
    version: str
    target_agents: List[str]
    deployment_timestamp: datetime
    status: str
    rollback_plan: Dict[str, Any]
    health_checks: List[Dict[str, Any]]


class PromptTemplateManager:
    """
    Comprehensive prompt template management system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_versions = self.config.get('max_versions', 20)
        self.backup_retention_days = self.config.get('backup_retention_days', 90)
        self.auto_backup = self.config.get('auto_backup', True)
        
        # Storage paths
        self.base_path = Path(self.config.get('base_path', '.claude-pm/template_management'))
        self.templates_path = self.base_path / 'templates'
        self.versions_path = self.base_path / 'versions'
        self.comparisons_path = self.base_path / 'comparisons'
        self.deployments_path = self.base_path / 'deployments'
        self.backups_path = self.base_path / 'backups'
        
        # Create directories
        for path in [self.templates_path, self.versions_path, self.comparisons_path, 
                    self.deployments_path, self.backups_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self.templates_cache: Dict[str, List[TemplateVersion]] = {}
        self.comparisons_cache: Dict[str, TemplateComparison] = {}
        self.deployments_cache: Dict[str, TemplateDeployment] = {}
        
        # Template registry
        self.template_registry: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("PromptTemplateManager initialized successfully")
    
    async def create_template(self, 
                            template_id: str,
                            content: str,
                            template_type: TemplateType,
                            agent_type: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            author: str = "system") -> TemplateVersion:
        """
        Create a new template
        
        Args:
            template_id: Unique identifier for template
            content: Template content
            template_type: Type of template
            agent_type: Target agent type (optional)
            metadata: Additional metadata
            author: Template author
            
        Returns:
            Created template version
        """
        try:
            # Validate template
            validation_results = await self._validate_template(content, template_type, agent_type)
            
            # Create template version
            template_version = TemplateVersion(
                template_id=template_id,
                version="1.0.0",
                content=content,
                metadata={
                    'template_type': template_type.value,
                    'agent_type': agent_type,
                    'created_at': datetime.now().isoformat(),
                    **(metadata or {})
                },
                author=author,
                timestamp=datetime.now(),
                status=TemplateStatus.DRAFT,
                change_summary="Initial template creation",
                validation_results=validation_results
            )
            
            # Save template
            await self._save_template_version(template_version)
            
            # Update registry
            await self._update_template_registry(template_id, template_version)
            
            # Auto-backup if enabled
            if self.auto_backup:
                await self._create_backup(template_id, "creation")
            
            self.logger.info(f"Created template {template_id} version {template_version.version}")
            return template_version
            
        except Exception as e:
            self.logger.error(f"Error creating template {template_id}: {e}")
            raise
    
    async def update_template(self, 
                            template_id: str,
                            content: str,
                            change_summary: str = "",
                            author: str = "system") -> TemplateVersion:
        """
        Update an existing template
        
        Args:
            template_id: Template identifier
            content: New content
            change_summary: Summary of changes
            author: Author of changes
            
        Returns:
            New template version
        """
        try:
            # Get current version
            current_version = await self.get_latest_version(template_id)
            if not current_version:
                raise ValueError(f"Template {template_id} not found")
            
            # Check if content has changed
            if current_version.content == content:
                self.logger.info(f"No changes detected for template {template_id}")
                return current_version
            
            # Generate new version number
            new_version = self._increment_version(current_version.version)
            
            # Validate new content
            template_type = TemplateType(current_version.metadata['template_type'])
            agent_type = current_version.metadata.get('agent_type')
            validation_results = await self._validate_template(content, template_type, agent_type)
            
            # Create new template version
            new_template_version = TemplateVersion(
                template_id=template_id,
                version=new_version,
                content=content,
                metadata={
                    **current_version.metadata,
                    'updated_at': datetime.now().isoformat()
                },
                author=author,
                timestamp=datetime.now(),
                status=TemplateStatus.DRAFT,
                parent_version=current_version.version,
                change_summary=change_summary,
                validation_results=validation_results
            )
            
            # Save new version
            await self._save_template_version(new_template_version)
            
            # Update registry
            await self._update_template_registry(template_id, new_template_version)
            
            # Create comparison
            comparison = await self.compare_versions(
                template_id, 
                current_version.version, 
                new_version
            )
            
            # Auto-backup if enabled
            if self.auto_backup:
                await self._create_backup(template_id, f"update_to_{new_version}")
            
            self.logger.info(f"Updated template {template_id} to version {new_version}")
            return new_template_version
            
        except Exception as e:
            self.logger.error(f"Error updating template {template_id}: {e}")
            raise
    
    async def get_template_versions(self, 
                                  template_id: str,
                                  limit: Optional[int] = None) -> List[TemplateVersion]:
        """
        Get all versions of a template
        
        Args:
            template_id: Template identifier
            limit: Maximum number of versions to return
            
        Returns:
            List of template versions
        """
        try:
            # Check cache first
            if template_id in self.templates_cache:
                versions = self.templates_cache[template_id]
            else:
                versions = await self._load_template_versions(template_id)
                self.templates_cache[template_id] = versions
            
            # Sort by version (newest first)
            versions.sort(key=lambda v: v.timestamp, reverse=True)
            
            if limit:
                versions = versions[:limit]
            
            return versions
            
        except Exception as e:
            self.logger.error(f"Error getting template versions for {template_id}: {e}")
            return []
    
    async def get_latest_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the latest version of a template"""
        versions = await self.get_template_versions(template_id, limit=1)
        return versions[0] if versions else None
    
    async def get_active_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the active version of a template"""
        versions = await self.get_template_versions(template_id)
        
        # Find active version
        for version in versions:
            if version.status == TemplateStatus.ACTIVE:
                return version
        
        return None
    
    async def activate_version(self, 
                             template_id: str,
                             version: str,
                             author: str = "system") -> bool:
        """
        Activate a specific template version
        
        Args:
            template_id: Template identifier
            version: Version to activate
            author: Author of activation
            
        Returns:
            True if activation successful
        """
        try:
            # Get all versions
            versions = await self.get_template_versions(template_id)
            
            # Find target version
            target_version = None
            for v in versions:
                if v.version == version:
                    target_version = v
                    break
            
            if not target_version:
                raise ValueError(f"Version {version} not found for template {template_id}")
            
            # Deactivate current active version
            for v in versions:
                if v.status == TemplateStatus.ACTIVE:
                    v.status = TemplateStatus.APPROVED
                    await self._save_template_version(v)
            
            # Activate target version
            target_version.status = TemplateStatus.ACTIVE
            target_version.metadata['activated_by'] = author
            target_version.metadata['activated_at'] = datetime.now().isoformat()
            await self._save_template_version(target_version)
            
            # Update cache
            self.templates_cache[template_id] = versions
            
            # Create backup
            if self.auto_backup:
                await self._create_backup(template_id, f"activate_{version}")
            
            self.logger.info(f"Activated template {template_id} version {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error activating template {template_id} version {version}: {e}")
            return False
    
    async def rollback_template(self, 
                              template_id: str,
                              target_version: str,
                              reason: str = "",
                              author: str = "system") -> bool:
        """
        Rollback template to a previous version
        
        Args:
            template_id: Template identifier
            target_version: Version to rollback to
            reason: Reason for rollback
            author: Author of rollback
            
        Returns:
            True if rollback successful
        """
        try:
            # Get current active version
            current_version = await self.get_active_version(template_id)
            if not current_version:
                raise ValueError(f"No active version found for template {template_id}")
            
            # Get target version
            versions = await self.get_template_versions(template_id)
            target = None
            for v in versions:
                if v.version == target_version:
                    target = v
                    break
            
            if not target:
                raise ValueError(f"Target version {target_version} not found")
            
            # Validate rollback
            rollback_impact = await self._analyze_rollback_impact(
                template_id, 
                current_version.version, 
                target_version
            )
            
            # Create rollback info
            rollback_info = {
                'rollback_from': current_version.version,
                'rollback_to': target_version,
                'reason': reason,
                'author': author,
                'timestamp': datetime.now().isoformat(),
                'impact_analysis': rollback_impact
            }
            
            # Deactivate current version
            current_version.status = TemplateStatus.DEPRECATED
            current_version.rollback_info = rollback_info
            await self._save_template_version(current_version)
            
            # Activate target version
            target.status = TemplateStatus.ACTIVE
            target.metadata['rolled_back_from'] = current_version.version
            target.metadata['rollback_reason'] = reason
            target.metadata['rollback_at'] = datetime.now().isoformat()
            await self._save_template_version(target)
            
            # Update cache
            self.templates_cache[template_id] = versions
            
            # Create backup
            if self.auto_backup:
                await self._create_backup(template_id, f"rollback_to_{target_version}")
            
            self.logger.info(f"Rolled back template {template_id} from {current_version.version} to {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back template {template_id}: {e}")
            return False
    
    async def compare_versions(self, 
                             template_id: str,
                             version_a: str,
                             version_b: str) -> TemplateComparison:
        """
        Compare two template versions
        
        Args:
            template_id: Template identifier
            version_a: First version to compare
            version_b: Second version to compare
            
        Returns:
            Template comparison result
        """
        try:
            # Get versions
            versions = await self.get_template_versions(template_id)
            
            template_a = None
            template_b = None
            
            for v in versions:
                if v.version == version_a:
                    template_a = v
                elif v.version == version_b:
                    template_b = v
            
            if not template_a:
                raise ValueError(f"Version {version_a} not found")
            if not template_b:
                raise ValueError(f"Version {version_b} not found")
            
            # Generate diff
            diff_html = self._generate_html_diff(template_a.content, template_b.content)
            diff_text = self._generate_text_diff(template_a.content, template_b.content)
            
            # Calculate similarity
            similarity_score = self._calculate_similarity(template_a.content, template_b.content)
            
            # Generate change summary
            change_summary = self._generate_change_summary(template_a.content, template_b.content)
            
            # Analyze impact
            impact_analysis = await self._analyze_change_impact(template_a, template_b)
            
            comparison = TemplateComparison(
                template_id=template_id,
                version_a=version_a,
                version_b=version_b,
                diff_html=diff_html,
                diff_text=diff_text,
                change_summary=change_summary,
                similarity_score=similarity_score,
                impact_analysis=impact_analysis,
                timestamp=datetime.now()
            )
            
            # Cache comparison
            comparison_key = f"{template_id}_{version_a}_{version_b}"
            self.comparisons_cache[comparison_key] = comparison
            
            # Save comparison
            await self._save_comparison(comparison)
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing versions for {template_id}: {e}")
            raise
    
    async def deploy_template(self, 
                            template_id: str,
                            version: str,
                            target_agents: List[str],
                            deployment_config: Optional[Dict[str, Any]] = None) -> TemplateDeployment:
        """
        Deploy a template version to target agents
        
        Args:
            template_id: Template identifier
            version: Version to deploy
            target_agents: List of target agent types
            deployment_config: Deployment configuration
            
        Returns:
            Deployment record
        """
        try:
            # Get template version
            template_version = None
            versions = await self.get_template_versions(template_id)
            
            for v in versions:
                if v.version == version:
                    template_version = v
                    break
            
            if not template_version:
                raise ValueError(f"Version {version} not found for template {template_id}")
            
            # Validate deployment
            deployment_validation = await self._validate_deployment(
                template_version, 
                target_agents, 
                deployment_config
            )
            
            if not deployment_validation['valid']:
                raise ValueError(f"Deployment validation failed: {deployment_validation['reason']}")
            
            # Create deployment record
            deployment_id = self._generate_deployment_id(template_id, version)
            
            deployment = TemplateDeployment(
                deployment_id=deployment_id,
                template_id=template_id,
                version=version,
                target_agents=target_agents,
                deployment_timestamp=datetime.now(),
                status="deploying",
                rollback_plan=await self._create_rollback_plan(template_id, version, target_agents),
                health_checks=[]
            )
            
            # Execute deployment
            deployment_result = await self._execute_deployment(deployment, template_version)
            
            deployment.status = "deployed" if deployment_result['success'] else "failed"
            deployment.health_checks = deployment_result.get('health_checks', [])
            
            # Save deployment
            await self._save_deployment(deployment)
            
            # Cache deployment
            self.deployments_cache[deployment_id] = deployment
            
            self.logger.info(f"Deployed template {template_id} version {version} to {len(target_agents)} agents")
            return deployment
            
        except Exception as e:
            self.logger.error(f"Error deploying template {template_id}: {e}")
            raise
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status and health checks"""
        try:
            deployment = self.deployments_cache.get(deployment_id)
            if not deployment:
                deployment = await self._load_deployment(deployment_id)
            
            if not deployment:
                return None
            
            # Run health checks
            health_status = await self._run_health_checks(deployment)
            
            return {
                'deployment_id': deployment_id,
                'template_id': deployment.template_id,
                'version': deployment.version,
                'status': deployment.status,
                'target_agents': deployment.target_agents,
                'deployment_timestamp': deployment.deployment_timestamp.isoformat(),
                'health_status': health_status,
                'health_checks': deployment.health_checks
            }
            
        except Exception as e:
            self.logger.error(f"Error getting deployment status for {deployment_id}: {e}")
            return None
    
    async def list_templates(self, 
                           template_type: Optional[TemplateType] = None,
                           agent_type: Optional[str] = None,
                           status: Optional[TemplateStatus] = None) -> List[Dict[str, Any]]:
        """
        List templates with optional filtering
        
        Args:
            template_type: Filter by template type
            agent_type: Filter by agent type
            status: Filter by status
            
        Returns:
            List of template summaries
        """
        try:
            # Load template registry
            registry = await self._load_template_registry()
            
            templates = []
            
            for template_id, template_info in registry.items():
                # Apply filters
                if template_type and template_info.get('template_type') != template_type.value:
                    continue
                
                if agent_type and template_info.get('agent_type') != agent_type:
                    continue
                
                if status and template_info.get('current_status') != status.value:
                    continue
                
                templates.append({
                    'template_id': template_id,
                    'template_type': template_info.get('template_type'),
                    'agent_type': template_info.get('agent_type'),
                    'current_version': template_info.get('current_version'),
                    'current_status': template_info.get('current_status'),
                    'last_updated': template_info.get('last_updated'),
                    'author': template_info.get('author'),
                    'version_count': template_info.get('version_count', 0)
                })
            
            # Sort by last updated
            templates.sort(key=lambda t: t.get('last_updated', ''), reverse=True)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Error listing templates: {e}")
            return []
    
    async def archive_template(self, 
                             template_id: str,
                             reason: str = "",
                             author: str = "system") -> bool:
        """
        Archive a template (mark as archived)
        
        Args:
            template_id: Template identifier
            reason: Reason for archival
            author: Author of archival
            
        Returns:
            True if archival successful
        """
        try:
            # Get all versions
            versions = await self.get_template_versions(template_id)
            
            if not versions:
                raise ValueError(f"Template {template_id} not found")
            
            # Archive all versions
            for version in versions:
                version.status = TemplateStatus.ARCHIVED
                version.metadata['archived_by'] = author
                version.metadata['archived_at'] = datetime.now().isoformat()
                version.metadata['archive_reason'] = reason
                await self._save_template_version(version)
            
            # Update cache
            self.templates_cache[template_id] = versions
            
            # Update registry
            await self._update_template_registry(template_id, versions[0])
            
            # Create backup
            if self.auto_backup:
                await self._create_backup(template_id, "archive")
            
            self.logger.info(f"Archived template {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error archiving template {template_id}: {e}")
            return False
    
    async def cleanup_old_versions(self, 
                                 template_id: Optional[str] = None,
                                 days_old: int = 90) -> Dict[str, Any]:
        """
        Clean up old template versions
        
        Args:
            template_id: Specific template to clean (optional)
            days_old: Age threshold for cleanup
            
        Returns:
            Cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleanup_results = {
                'templates_processed': 0,
                'versions_removed': 0,
                'space_freed': 0
            }
            
            # Get template list
            if template_id:
                template_ids = [template_id]
            else:
                registry = await self._load_template_registry()
                template_ids = list(registry.keys())
            
            for tid in template_ids:
                versions = await self.get_template_versions(tid)
                
                # Keep recent versions and active/approved versions
                versions_to_keep = []
                versions_to_remove = []
                
                for version in versions:
                    if (version.timestamp > cutoff_date or 
                        version.status in [TemplateStatus.ACTIVE, TemplateStatus.APPROVED]):
                        versions_to_keep.append(version)
                    else:
                        versions_to_remove.append(version)
                
                # Ensure we keep at least the minimum number of versions
                if len(versions_to_keep) < 3:
                    # Keep the 3 most recent versions
                    all_versions = sorted(versions, key=lambda v: v.timestamp, reverse=True)
                    versions_to_keep = all_versions[:3]
                    versions_to_remove = all_versions[3:]
                
                # Remove old versions
                for version in versions_to_remove:
                    await self._remove_version(tid, version.version)
                    cleanup_results['versions_removed'] += 1
                
                # Update cache
                self.templates_cache[tid] = versions_to_keep
                
                cleanup_results['templates_processed'] += 1
            
            self.logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {'error': str(e)}
    
    # Private methods
    async def _validate_template(self, 
                               content: str,
                               template_type: TemplateType,
                               agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Validate template content"""
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'suggestions': []
            }
            
            # Basic validation
            if not content.strip():
                validation_results['valid'] = False
                validation_results['errors'].append("Template content cannot be empty")
                return validation_results
            
            # Template type specific validation
            if template_type == TemplateType.AGENT_PROMPT:
                await self._validate_agent_prompt(content, agent_type, validation_results)
            elif template_type == TemplateType.SYSTEM_PROMPT:
                await self._validate_system_prompt(content, validation_results)
            elif template_type == TemplateType.TASK_TEMPLATE:
                await self._validate_task_template(content, validation_results)
            
            return validation_results
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'suggestions': []
            }
    
    async def _validate_agent_prompt(self, 
                                   content: str,
                                   agent_type: Optional[str],
                                   validation_results: Dict[str, Any]):
        """Validate agent prompt template"""
        # Check for required sections
        required_sections = ['**Task**', '**Context**', '**Authority**']
        for section in required_sections:
            if section not in content:
                validation_results['warnings'].append(f"Missing recommended section: {section}")
        
        # Check for agent-specific requirements
        if agent_type:
            agent_requirements = {
                'Documentation': ['changelog', 'version', 'documentation'],
                'QA': ['test', 'validation', 'quality'],
                'Engineer': ['code', 'implementation', 'development'],
                'Ops': ['deployment', 'operations', 'infrastructure']
            }
            
            if agent_type in agent_requirements:
                for requirement in agent_requirements[agent_type]:
                    if requirement.lower() not in content.lower():
                        validation_results['suggestions'].append(
                            f"Consider adding {requirement} guidance for {agent_type} agent"
                        )
    
    async def _validate_system_prompt(self, content: str, validation_results: Dict[str, Any]):
        """Validate system prompt template"""
        # Check for system-level requirements
        system_requirements = ['role', 'behavior', 'constraints']
        for requirement in system_requirements:
            if requirement.lower() not in content.lower():
                validation_results['suggestions'].append(
                    f"Consider defining {requirement} in system prompt"
                )
    
    async def _validate_task_template(self, content: str, validation_results: Dict[str, Any]):
        """Validate task template"""
        # Check for task structure
        task_elements = ['objective', 'steps', 'deliverables']
        for element in task_elements:
            if element.lower() not in content.lower():
                validation_results['suggestions'].append(
                    f"Consider adding {element} to task template"
                )
    
    def _increment_version(self, current_version: str) -> str:
        """Increment version number"""
        try:
            parts = current_version.split('.')
            if len(parts) != 3:
                return "1.0.0"
            
            major, minor, patch = map(int, parts)
            return f"{major}.{minor}.{patch + 1}"
            
        except Exception:
            return "1.0.0"
    
    def _generate_html_diff(self, content_a: str, content_b: str) -> str:
        """Generate HTML diff between two content strings"""
        try:
            differ = difflib.HtmlDiff()
            return differ.make_file(
                content_a.splitlines(),
                content_b.splitlines(),
                "Version A",
                "Version B"
            )
        except Exception as e:
            self.logger.error(f"Error generating HTML diff: {e}")
            return f"<p>Error generating diff: {str(e)}</p>"
    
    def _generate_text_diff(self, content_a: str, content_b: str) -> str:
        """Generate text diff between two content strings"""
        try:
            differ = difflib.unified_diff(
                content_a.splitlines(keepends=True),
                content_b.splitlines(keepends=True),
                fromfile="Version A",
                tofile="Version B"
            )
            return ''.join(differ)
        except Exception as e:
            self.logger.error(f"Error generating text diff: {e}")
            return f"Error generating diff: {str(e)}"
    
    def _calculate_similarity(self, content_a: str, content_b: str) -> float:
        """Calculate similarity between two content strings"""
        try:
            matcher = difflib.SequenceMatcher(None, content_a, content_b)
            return matcher.ratio()
        except Exception:
            return 0.0
    
    def _generate_change_summary(self, content_a: str, content_b: str) -> str:
        """Generate summary of changes between two content strings"""
        try:
            lines_a = content_a.splitlines()
            lines_b = content_b.splitlines()
            
            matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
            changes = []
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    changes.append(f"Modified {i2-i1} lines")
                elif tag == 'delete':
                    changes.append(f"Deleted {i2-i1} lines")
                elif tag == 'insert':
                    changes.append(f"Added {j2-j1} lines")
            
            if not changes:
                return "No changes detected"
            
            return "; ".join(changes)
            
        except Exception as e:
            return f"Error generating change summary: {str(e)}"
    
    async def _analyze_change_impact(self, 
                                   template_a: TemplateVersion,
                                   template_b: TemplateVersion) -> Dict[str, Any]:
        """Analyze impact of changes between templates"""
        try:
            impact_analysis = {
                'content_changes': {
                    'lines_added': 0,
                    'lines_removed': 0,
                    'lines_modified': 0
                },
                'structural_changes': [],
                'semantic_changes': [],
                'risk_assessment': 'low'
            }
            
            # Analyze content changes
            lines_a = template_a.content.splitlines()
            lines_b = template_b.content.splitlines()
            
            matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    impact_analysis['content_changes']['lines_modified'] += max(i2-i1, j2-j1)
                elif tag == 'delete':
                    impact_analysis['content_changes']['lines_removed'] += i2-i1
                elif tag == 'insert':
                    impact_analysis['content_changes']['lines_added'] += j2-j1
            
            # Analyze structural changes
            sections_a = re.findall(r'\*\*([^*]+)\*\*', template_a.content)
            sections_b = re.findall(r'\*\*([^*]+)\*\*', template_b.content)
            
            added_sections = set(sections_b) - set(sections_a)
            removed_sections = set(sections_a) - set(sections_b)
            
            if added_sections:
                impact_analysis['structural_changes'].append(f"Added sections: {', '.join(added_sections)}")
            if removed_sections:
                impact_analysis['structural_changes'].append(f"Removed sections: {', '.join(removed_sections)}")
            
            # Calculate risk assessment
            total_changes = sum(impact_analysis['content_changes'].values())
            
            if total_changes > 50 or removed_sections:
                impact_analysis['risk_assessment'] = 'high'
            elif total_changes > 20 or added_sections:
                impact_analysis['risk_assessment'] = 'medium'
            else:
                impact_analysis['risk_assessment'] = 'low'
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing change impact: {e}")
            return {'error': str(e)}
    
    async def _analyze_rollback_impact(self, 
                                     template_id: str,
                                     current_version: str,
                                     target_version: str) -> Dict[str, Any]:
        """Analyze impact of rolling back to target version"""
        try:
            comparison = await self.compare_versions(template_id, target_version, current_version)
            
            return {
                'rollback_changes': comparison.change_summary,
                'similarity_to_current': comparison.similarity_score,
                'impact_analysis': comparison.impact_analysis,
                'recommendation': (
                    "Safe to rollback" if comparison.similarity_score > 0.8 else
                    "Review changes carefully" if comparison.similarity_score > 0.6 else
                    "High impact rollback - proceed with caution"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing rollback impact: {e}")
            return {'error': str(e)}
    
    async def _validate_deployment(self, 
                                 template_version: TemplateVersion,
                                 target_agents: List[str],
                                 deployment_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate deployment configuration"""
        try:
            validation = {
                'valid': True,
                'reason': '',
                'warnings': []
            }
            
            # Check template status
            if template_version.status not in [TemplateStatus.APPROVED, TemplateStatus.ACTIVE]:
                validation['valid'] = False
                validation['reason'] = f"Template status is {template_version.status.value}, not approved for deployment"
                return validation
            
            # Check validation results
            if template_version.validation_results and not template_version.validation_results.get('valid', True):
                validation['valid'] = False
                validation['reason'] = "Template has validation errors"
                return validation
            
            # Check agent compatibility
            template_agent_type = template_version.metadata.get('agent_type')
            if template_agent_type and template_agent_type not in target_agents:
                validation['warnings'].append(
                    f"Template designed for {template_agent_type} but deploying to {target_agents}"
                )
            
            return validation
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f"Validation error: {str(e)}",
                'warnings': []
            }
    
    async def _create_rollback_plan(self, 
                                  template_id: str,
                                  version: str,
                                  target_agents: List[str]) -> Dict[str, Any]:
        """Create rollback plan for deployment"""
        try:
            # Get current active version for each agent
            current_versions = {}
            for agent in target_agents:
                current_version = await self.get_active_version(f"{template_id}_{agent}")
                if current_version:
                    current_versions[agent] = current_version.version
            
            return {
                'rollback_versions': current_versions,
                'rollback_procedure': [
                    "1. Stop deployment process",
                    "2. Restore previous template versions",
                    "3. Restart affected agents",
                    "4. Verify rollback success"
                ],
                'validation_steps': [
                    "Check agent response quality",
                    "Verify template functionality",
                    "Monitor performance metrics"
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _execute_deployment(self, 
                                deployment: TemplateDeployment,
                                template_version: TemplateVersion) -> Dict[str, Any]:
        """Execute template deployment"""
        try:
            # This would integrate with actual agent deployment system
            # For now, simulate deployment
            
            deployment_result = {
                'success': True,
                'deployed_agents': [],
                'failed_agents': [],
                'health_checks': []
            }
            
            for agent in deployment.target_agents:
                try:
                    # Simulate agent deployment
                    agent_deployment = await self._deploy_to_agent(agent, template_version)
                    
                    if agent_deployment['success']:
                        deployment_result['deployed_agents'].append(agent)
                    else:
                        deployment_result['failed_agents'].append({
                            'agent': agent,
                            'error': agent_deployment['error']
                        })
                        deployment_result['success'] = False
                    
                except Exception as e:
                    deployment_result['failed_agents'].append({
                        'agent': agent,
                        'error': str(e)
                    })
                    deployment_result['success'] = False
            
            return deployment_result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'deployed_agents': [],
                'failed_agents': deployment.target_agents
            }
    
    async def _deploy_to_agent(self, 
                             agent: str,
                             template_version: TemplateVersion) -> Dict[str, Any]:
        """Deploy template to specific agent"""
        try:
            # This would integrate with actual agent management system
            # For now, save template to agent-specific location
            
            agent_template_path = self.templates_path / f"{template_version.template_id}_{agent}.txt"
            
            with open(agent_template_path, 'w') as f:
                f.write(template_version.content)
            
            return {
                'success': True,
                'deployment_path': str(agent_template_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _run_health_checks(self, deployment: TemplateDeployment) -> Dict[str, Any]:
        """Run health checks for deployment"""
        try:
            health_status = {
                'overall_health': 'healthy',
                'agent_health': {},
                'last_check': datetime.now().isoformat()
            }
            
            for agent in deployment.target_agents:
                # Simulate health check
                agent_health = {
                    'status': 'healthy',
                    'response_time': 100,  # ms
                    'error_rate': 0.0,
                    'last_response': datetime.now().isoformat()
                }
                
                health_status['agent_health'][agent] = agent_health
            
            return health_status
            
        except Exception as e:
            return {
                'overall_health': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _generate_deployment_id(self, template_id: str, version: str) -> str:
        """Generate unique deployment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(f"{template_id}_{version}_{timestamp}".encode()).hexdigest()[:8]
        return f"deploy_{timestamp}_{hash_val}"
    
    # Storage methods
    async def _save_template_version(self, template_version: TemplateVersion):
        """Save template version to storage"""
        try:
            version_file = self.versions_path / f"{template_version.template_id}_{template_version.version}.json"
            
            with open(version_file, 'w') as f:
                # Convert datetime objects to ISO format
                version_dict = asdict(template_version)
                version_dict['timestamp'] = template_version.timestamp.isoformat()
                version_dict['status'] = template_version.status.value
                json.dump(version_dict, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving template version: {e}")
    
    async def _load_template_versions(self, template_id: str) -> List[TemplateVersion]:
        """Load template versions from storage"""
        try:
            versions = []
            pattern = f"{template_id}_*.json"
            
            for version_file in self.versions_path.glob(pattern):
                try:
                    with open(version_file, 'r') as f:
                        data = json.load(f)
                    
                    # Convert back to objects
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    data['status'] = TemplateStatus(data['status'])
                    
                    versions.append(TemplateVersion(**data))
                    
                except Exception as e:
                    self.logger.error(f"Error loading version file {version_file}: {e}")
                    continue
            
            return versions
            
        except Exception as e:
            self.logger.error(f"Error loading template versions for {template_id}: {e}")
            return []
    
    async def _save_comparison(self, comparison: TemplateComparison):
        """Save comparison to storage"""
        try:
            comparison_file = self.comparisons_path / f"{comparison.template_id}_{comparison.version_a}_{comparison.version_b}.json"
            
            with open(comparison_file, 'w') as f:
                comparison_dict = asdict(comparison)
                comparison_dict['timestamp'] = comparison.timestamp.isoformat()
                json.dump(comparison_dict, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving comparison: {e}")
    
    async def _save_deployment(self, deployment: TemplateDeployment):
        """Save deployment to storage"""
        try:
            deployment_file = self.deployments_path / f"{deployment.deployment_id}.json"
            
            with open(deployment_file, 'w') as f:
                deployment_dict = asdict(deployment)
                deployment_dict['deployment_timestamp'] = deployment.deployment_timestamp.isoformat()
                json.dump(deployment_dict, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving deployment: {e}")
    
    async def _load_deployment(self, deployment_id: str) -> Optional[TemplateDeployment]:
        """Load deployment from storage"""
        try:
            deployment_file = self.deployments_path / f"{deployment_id}.json"
            
            if not deployment_file.exists():
                return None
            
            with open(deployment_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to objects
            data['deployment_timestamp'] = datetime.fromisoformat(data['deployment_timestamp'])
            
            return TemplateDeployment(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading deployment {deployment_id}: {e}")
            return None
    
    async def _update_template_registry(self, template_id: str, template_version: TemplateVersion):
        """Update template registry"""
        try:
            registry_file = self.base_path / 'template_registry.json'
            
            # Load existing registry
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            else:
                registry = {}
            
            # Update registry entry
            registry[template_id] = {
                'template_type': template_version.metadata.get('template_type'),
                'agent_type': template_version.metadata.get('agent_type'),
                'current_version': template_version.version,
                'current_status': template_version.status.value,
                'last_updated': template_version.timestamp.isoformat(),
                'author': template_version.author,
                'version_count': len(await self.get_template_versions(template_id))
            }
            
            # Save updated registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error updating template registry: {e}")
    
    async def _load_template_registry(self) -> Dict[str, Any]:
        """Load template registry"""
        try:
            registry_file = self.base_path / 'template_registry.json'
            
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    return json.load(f)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error loading template registry: {e}")
            return {}
    
    async def _create_backup(self, template_id: str, reason: str):
        """Create backup of template"""
        try:
            if not self.auto_backup:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backups_path / f"{template_id}_{timestamp}_{reason}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup all versions
            versions = await self.get_template_versions(template_id)
            for version in versions:
                backup_file = backup_dir / f"{version.version}.json"
                with open(backup_file, 'w') as f:
                    version_dict = asdict(version)
                    version_dict['timestamp'] = version.timestamp.isoformat()
                    version_dict['status'] = version.status.value
                    json.dump(version_dict, f, indent=2)
            
            # Cleanup old backups
            await self._cleanup_old_backups(template_id)
            
        except Exception as e:
            self.logger.error(f"Error creating backup for {template_id}: {e}")
    
    async def _cleanup_old_backups(self, template_id: str):
        """Cleanup old backups"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            for backup_dir in self.backups_path.glob(f"{template_id}_*"):
                try:
                    # Extract timestamp from directory name
                    timestamp_str = backup_dir.name.split('_')[1]
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d")
                    
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        
                except Exception as e:
                    self.logger.error(f"Error processing backup directory {backup_dir}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    async def _remove_version(self, template_id: str, version: str):
        """Remove a specific version"""
        try:
            version_file = self.versions_path / f"{template_id}_{version}.json"
            if version_file.exists():
                version_file.unlink()
            
        except Exception as e:
            self.logger.error(f"Error removing version {version} for {template_id}: {e}")


# Async convenience functions
async def create_agent_template(agent_type: str, 
                              content: str,
                              author: str = "system") -> TemplateVersion:
    """
    Convenience function to create agent template
    
    Args:
        agent_type: Type of agent
        content: Template content
        author: Template author
        
    Returns:
        Created template version
    """
    manager = PromptTemplateManager()
    template_id = f"{agent_type}_prompt"
    
    return await manager.create_template(
        template_id=template_id,
        content=content,
        template_type=TemplateType.AGENT_PROMPT,
        agent_type=agent_type,
        author=author
    )


async def get_deployment_dashboard() -> Dict[str, Any]:
    """
    Get deployment dashboard with current status
    
    Returns:
        Dashboard data
    """
    manager = PromptTemplateManager()
    
    # Get all templates
    templates = await manager.list_templates()
    
    # Get deployment status
    deployment_files = list(manager.deployments_path.glob("*.json"))
    active_deployments = []
    
    for deployment_file in deployment_files:
        deployment = await manager._load_deployment(deployment_file.stem)
        if deployment and deployment.status == "deployed":
            status = await manager.get_deployment_status(deployment.deployment_id)
            if status:
                active_deployments.append(status)
    
    return {
        'dashboard_generated': datetime.now().isoformat(),
        'summary': {
            'total_templates': len(templates),
            'active_deployments': len(active_deployments),
            'template_types': len(set(t.get('template_type') for t in templates)),
            'agent_types': len(set(t.get('agent_type') for t in templates if t.get('agent_type')))
        },
        'templates': templates,
        'active_deployments': active_deployments
    }


if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize manager
        manager = PromptTemplateManager()
        
        # Create a template
        template = await manager.create_template(
            template_id="test_template",
            content="Test template content",
            template_type=TemplateType.AGENT_PROMPT,
            agent_type="Documentation"
        )
        
        print(f"Created template: {template.template_id} version {template.version}")
        
        # Update template
        updated = await manager.update_template(
            template_id="test_template",
            content="Updated test template content",
            change_summary="Added more details"
        )
        
        print(f"Updated template: {updated.template_id} version {updated.version}")
        
        # Compare versions
        comparison = await manager.compare_versions(
            template_id="test_template",
            version_a="1.0.0",
            version_b="1.0.1"
        )
        
        print(f"Comparison similarity: {comparison.similarity_score}")
    
    asyncio.run(main())