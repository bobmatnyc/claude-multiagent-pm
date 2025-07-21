"""Metadata extraction functionality for agents."""

import ast
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from .models import AgentMetadata
from .classification import AgentClassifier
from .model_configuration import ModelConfigurator

logger = logging.getLogger(__name__)


@dataclass
class MetadataExtractor:
    """Extracts metadata from agent files."""
    classifier: AgentClassifier
    model_configurator: ModelConfigurator
    
    async def extract_agent_metadata(self, agent_file: Path, tier: str) -> Optional[AgentMetadata]:
        """
        Extract metadata from agent file.
        
        Args:
            agent_file: Path to agent file
            tier: Hierarchy tier
            
        Returns:
            AgentMetadata or None if extraction fails
        """
        try:
            # Get file stats
            stat = agent_file.stat()
            file_size = stat.st_size
            last_modified = stat.st_mtime
            
            # Determine agent name and type
            agent_name = agent_file.stem
            agent_type = self.classifier.classify_agent_type(agent_name, agent_file)
            
            # Read file for additional metadata
            description, version, capabilities = await self._parse_agent_file(agent_file)
            
            # Enhanced metadata extraction for ISS-0118
            specializations, frameworks, domains, roles = self._extract_specialized_metadata(capabilities)
            is_hybrid, hybrid_types = self.classifier.detect_hybrid_agent(agent_type, specializations)
            complexity_level = self.classifier.assess_complexity_level(capabilities, specializations)
            
            # Extract model configuration from agent file
            preferred_model, model_config = await self.model_configurator.extract_model_configuration(
                agent_file, agent_type, complexity_level
            )
            
            return AgentMetadata(
                name=agent_name,
                type=agent_type,
                path=str(agent_file),
                tier=tier,
                description=description,
                version=version,
                capabilities=capabilities,
                last_modified=last_modified,
                file_size=file_size,
                validated=False,  # Will be validated later
                specializations=specializations,
                frameworks=frameworks,
                domains=domains,
                roles=roles,
                is_hybrid=is_hybrid,
                hybrid_types=hybrid_types,
                complexity_level=complexity_level,
                preferred_model=preferred_model,
                model_config=model_config
            )
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {agent_file}: {e}")
            return None
    
    async def _parse_agent_file(self, agent_file: Path) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Enhanced agent file parsing with specialized capability detection for ISS-0118.
        
        Args:
            agent_file: Path to agent file
            
        Returns:
            Tuple of (description, version, capabilities)
        """
        description = None
        version = None
        capabilities = []
        
        try:
            content = agent_file.read_text(encoding='utf-8')
            
            # Extract docstring description with specialization detection
            if '"""' in content:
                docstring_start = content.find('"""')
                if docstring_start != -1:
                    docstring_end = content.find('"""', docstring_start + 3)
                    if docstring_end != -1:
                        docstring = content[docstring_start + 3:docstring_end].strip()
                        # Use first line as description
                        description = docstring.split('\n')[0].strip()
                        
                        # Extract specialization hints from docstring
                        docstring_lower = docstring.lower()
                        specialization_indicators = [
                            'specializes in', 'specialized for', 'expert in', 'focused on',
                            'handles', 'manages', 'responsible for', 'domain:', 'specialty:'
                        ]
                        for indicator in specialization_indicators:
                            if indicator in docstring_lower:
                                # Extract text after indicator as specialization capability
                                spec_start = docstring_lower.find(indicator) + len(indicator)
                                spec_text = docstring[spec_start:spec_start+100].strip()
                                if spec_text:
                                    capabilities.append(f"specialization:{spec_text.split('.')[0].strip()}")
            
            # Extract version information
            if 'VERSION' in content or '__version__' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'VERSION' in line or '__version__' in line:
                        if '=' in line:
                            version_part = line.split('=')[1].strip().strip('"\'')
                            version = version_part
                            break
            
            # Enhanced capability extraction from methods/functions
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('def ') and not line.startswith('def _'):
                    # Extract public method names as capabilities
                    method_name = line.split('(')[0].replace('def ', '').strip()
                    if method_name not in ['__init__', '__str__', '__repr__']:
                        capabilities.append(method_name)
                elif line.startswith('async def ') and not line.startswith('async def _'):
                    # Extract async method names as capabilities
                    method_name = line.split('(')[0].replace('async def ', '').strip()
                    if method_name not in ['__init__', '__str__', '__repr__']:
                        capabilities.append(f"async_{method_name}")
            
            # Extract capabilities from class definitions and inheritance
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Add class name as capability
                        capabilities.append(f"class:{node.name}")
                        
                        # Extract base classes as capability indicators
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                capabilities.append(f"inherits:{base.id}")
                            elif isinstance(base, ast.Attribute):
                                capabilities.append(f"inherits:{base.attr}")
            except SyntaxError:
                pass  # Skip AST parsing if syntax errors
            
            # Extract framework and library capabilities from imports
            framework_capabilities = self._extract_framework_capabilities(content)
            capabilities.extend(framework_capabilities)
            
            # Extract role and domain capabilities from comments
            role_capabilities = self._extract_role_capabilities(content)
            capabilities.extend(role_capabilities)
        
        except Exception as e:
            logger.warning(f"Error parsing agent file {agent_file}: {e}")
        
        return description, version, capabilities
    
    def _extract_framework_capabilities(self, content: str) -> List[str]:
        """Extract framework and library capabilities from import statements."""
        capabilities = []
        
        framework_patterns = {
            'fastapi': ['fastapi', 'pydantic'],
            'django': ['django'],
            'flask': ['flask'],
            'react': ['react', '@types/react'],
            'vue': ['vue', '@vue/'],
            'angular': ['@angular/', 'angular'],
            'express': ['express'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['torch', 'pytorch'],
            'pandas': ['pandas'],
            'numpy': ['numpy'],
            'selenium': ['selenium'],
            'pytest': ['pytest'],
            'jest': ['jest'],
            'docker': ['docker'],
            'kubernetes': ['kubernetes', 'kubectl'],
            'aws': ['boto3', 'aws-'],
            'azure': ['azure-'],
            'gcp': ['google-cloud-'],
            'redis': ['redis'],
            'mongodb': ['pymongo', 'mongodb'],
            'postgresql': ['psycopg2', 'postgresql'],
            'mysql': ['mysql', 'pymysql'],
            'graphql': ['graphql'],
            'rest_api': ['requests', 'urllib'],
            'machine_learning': ['scikit-learn', 'sklearn'],
            'data_analysis': ['matplotlib', 'seaborn'],
            'async_processing': ['asyncio', 'aiohttp'],
            'task_queue': ['celery', 'rq'],
            'monitoring': ['prometheus', 'grafana'],
            'logging': ['loguru', 'structlog']
        }
        
        content_lower = content.lower()
        
        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                if f'import {pattern}' in content_lower or f'from {pattern}' in content_lower:
                    capabilities.append(f'framework:{framework}')
                    break
        
        return capabilities
    
    def _extract_role_capabilities(self, content: str) -> List[str]:
        """Extract role and domain capabilities from comments and docstrings."""
        capabilities = []
        
        role_patterns = {
            'ui_designer': ['ui design', 'user interface', 'interface design'],
            'ux_specialist': ['user experience', 'ux research', 'usability'],
            'frontend_developer': ['frontend development', 'client-side', 'web development'],
            'backend_developer': ['backend development', 'server-side', 'api development'],
            'database_administrator': ['database admin', 'db management', 'database design'],
            'devops_engineer': ['devops', 'ci/cd', 'deployment automation'],
            'security_specialist': ['security analysis', 'vulnerability assessment', 'penetration testing'],
            'performance_engineer': ['performance optimization', 'load testing', 'benchmarking'],
            'quality_assurance': ['quality assurance', 'test automation', 'qa testing'],
            'data_scientist': ['data science', 'machine learning', 'statistical analysis'],
            'business_analyst': ['business analysis', 'requirements gathering', 'process mapping'],
            'project_manager': ['project management', 'agile', 'scrum master'],
            'technical_writer': ['technical writing', 'documentation', 'content creation'],
            'integration_specialist': ['system integration', 'api integration', 'middleware'],
            'architecture_specialist': ['system architecture', 'software architecture', 'design patterns']
        }
        
        content_lower = content.lower()
        
        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    capabilities.append(f'role:{role}')
                    break
        
        # Extract domain capabilities from comments
        domain_keywords = {
            'e_commerce': ['e-commerce', 'shopping', 'payment', 'order'],
            'healthcare': ['healthcare', 'medical', 'patient', 'clinical'],
            'finance': ['financial', 'banking', 'trading', 'investment'],
            'education': ['education', 'learning', 'student', 'course'],
            'gaming': ['gaming', 'game', 'player', 'score'],
            'social_media': ['social', 'feed', 'post', 'like', 'share'],
            'iot': ['iot', 'sensor', 'device', 'telemetry'],
            'blockchain': ['blockchain', 'crypto', 'smart contract', 'web3'],
            'ai_ml': ['artificial intelligence', 'machine learning', 'neural network'],
            'cloud_native': ['cloud native', 'microservices', 'serverless']
        }
        
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    capabilities.append(f'domain:{domain}')
                    break
        
        return capabilities
    
    def _extract_specialized_metadata(self, capabilities: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Extract specialized metadata from capabilities list."""
        specializations = []
        frameworks = []
        domains = []
        roles = []
        
        for capability in capabilities:
            if capability.startswith('specialization:'):
                specializations.append(capability.replace('specialization:', ''))
            elif capability.startswith('framework:'):
                frameworks.append(capability.replace('framework:', ''))
            elif capability.startswith('domain:'):
                domains.append(capability.replace('domain:', ''))
            elif capability.startswith('role:'):
                roles.append(capability.replace('role:', ''))
        
        return specializations, frameworks, domains, roles