"""Agent validation system."""

import logging
from pathlib import Path
from typing import Dict, List

from .models import AgentMetadata

logger = logging.getLogger(__name__)


class AgentValidator:
    """Validates agent configurations and capabilities."""
    
    async def validate_agents(self, agents: Dict[str, AgentMetadata]) -> Dict[str, AgentMetadata]:
        """
        Enhanced agent validation with specialized agent verification for ISS-0118.
        
        Args:
            agents: Dictionary of agents to validate
            
        Returns:
            Validated agents dictionary with validation scores
        """
        validated = {}
        
        for name, metadata in agents.items():
            try:
                validation_score = 0.0
                validation_errors = []
                
                # Basic file validation
                if not Path(metadata.path).exists():
                    metadata.validated = False
                    metadata.error_message = "File not found"
                    metadata.validation_score = 0.0
                    validated[name] = metadata
                    continue
                
                validation_score += 10  # File exists
                
                # Syntax validation (basic Python syntax check)
                try:
                    with open(metadata.path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, metadata.path, 'exec')
                    validation_score += 20  # Valid syntax
                except SyntaxError as e:
                    validation_errors.append(f"Syntax error: {e}")
                    validation_score -= 10
                
                # Enhanced validation for specialized agents
                validation_score += await self._validate_specialized_agent(metadata, content)
                
                # Hybrid agent validation
                if metadata.is_hybrid:
                    validation_score += self._validate_hybrid_agent(metadata)
                
                # Capability consistency validation
                validation_score += self._validate_capability_consistency(metadata)
                
                # Framework compatibility validation
                validation_score += self._validate_framework_compatibility(metadata)
                
                # Set validation results
                metadata.validation_score = max(0.0, min(100.0, validation_score))
                metadata.validated = validation_score >= 50.0  # 50% threshold
                
                if validation_errors:
                    metadata.error_message = "; ".join(validation_errors)
                else:
                    metadata.error_message = None
                
                validated[name] = metadata
                
            except Exception as e:
                logger.warning(f"Validation error for agent {name}: {e}")
                metadata.validated = False
                metadata.error_message = str(e)
                metadata.validation_score = 0.0
                validated[name] = metadata
        
        return validated
    
    async def _validate_specialized_agent(self, metadata: AgentMetadata, content: str) -> float:
        """
        Validate specialized agent requirements and capabilities.
        
        Args:
            metadata: Agent metadata
            content: Agent file content
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        # Validate specialization alignment
        if metadata.specializations:
            score += 15  # Has specializations
            
            # Check if specializations align with agent type
            type_alignment = any(spec.lower() in metadata.type.lower() or 
                               metadata.type.lower() in spec.lower() 
                               for spec in metadata.specializations)
            if type_alignment:
                score += 10
        
        # Validate framework usage
        if metadata.frameworks:
            score += 10  # Uses frameworks
            
            # Check for proper import statements
            for framework in metadata.frameworks:
                if framework.lower() in content.lower():
                    score += 2  # Framework properly imported
        
        # Validate domain expertise
        if metadata.domains:
            score += 8  # Has domain expertise
        
        # Validate role definitions
        if metadata.roles:
            score += 7  # Has defined roles
        
        return score
    
    def _validate_hybrid_agent(self, metadata: AgentMetadata) -> float:
        """
        Validate hybrid agent configuration.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        if metadata.is_hybrid and metadata.hybrid_types:
            # Bonus for being hybrid
            score += 5
            
            # Validate hybrid type consistency
            if len(metadata.hybrid_types) >= 2:
                score += 10  # Valid hybrid combination
            
            # Check for capability coverage across types
            type_coverage = len(set(metadata.hybrid_types))
            score += type_coverage * 2  # Coverage bonus
        
        return score
    
    def _validate_capability_consistency(self, metadata: AgentMetadata) -> float:
        """
        Validate capability consistency with agent type and specializations.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        # Basic capability validation
        if metadata.capabilities:
            score += len(metadata.capabilities) * 0.5  # Base capability score
            
            # Check for consistent naming
            consistent_caps = sum(1 for cap in metadata.capabilities 
                                if not cap.startswith('_'))
            score += consistent_caps * 0.3
        
        # Validate complexity assessment
        complexity_levels = ['basic', 'intermediate', 'advanced', 'expert']
        if metadata.complexity_level in complexity_levels:
            score += 5
            
            # Bonus for higher complexity with sufficient capabilities
            complexity_index = complexity_levels.index(metadata.complexity_level)
            expected_caps = (complexity_index + 1) * 5
            if len(metadata.capabilities) >= expected_caps:
                score += 5
        
        return score
    
    def _validate_framework_compatibility(self, metadata: AgentMetadata) -> float:
        """
        Validate framework compatibility and integration.
        
        Args:
            metadata: Agent metadata
            
        Returns:
            Validation score contribution
        """
        score = 0.0
        
        if metadata.frameworks:
            # Validate framework combinations
            compatible_combinations = {
                'react': ['typescript', 'javascript', 'webpack'],
                'django': ['python', 'postgresql', 'redis'],
                'fastapi': ['python', 'pydantic', 'asyncio'],
                'kubernetes': ['docker', 'yaml', 'helm']
            }
            
            for framework in metadata.frameworks:
                if framework in compatible_combinations:
                    compatible_techs = compatible_combinations[framework]
                    compatibility_score = sum(1 for tech in compatible_techs 
                                            if any(tech in cap.lower() for cap in metadata.capabilities))
                    score += compatibility_score * 2
        
        return score
    
    def validate_single_agent(self, metadata: AgentMetadata) -> Dict[str, any]:
        """
        Validate a single agent and return detailed validation report.
        
        Args:
            metadata: Agent metadata to validate
            
        Returns:
            Validation report dictionary
        """
        validation_report = {
            'agent_name': metadata.name,
            'agent_type': metadata.type,
            'tier': metadata.tier,
            'valid': metadata.validated,
            'validation_score': metadata.validation_score,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Check basic requirements
        if not metadata.path:
            validation_report['errors'].append("No path specified for agent")
        
        if not metadata.type:
            validation_report['errors'].append("No type specified for agent")
        
        # Check file existence
        if metadata.path and not Path(metadata.path).exists():
            validation_report['errors'].append(f"Agent file not found: {metadata.path}")
        
        # Validate complexity vs capabilities
        if metadata.complexity_level == 'expert' and len(metadata.capabilities) < 15:
            validation_report['warnings'].append(
                "Agent marked as 'expert' but has limited capabilities"
            )
        
        # Check for model configuration
        if not metadata.preferred_model:
            validation_report['warnings'].append("No model configuration specified")
        
        # Provide suggestions
        if not metadata.specializations:
            validation_report['suggestions'].append(
                "Consider adding specializations to improve agent discovery"
            )
        
        if metadata.is_hybrid and len(metadata.hybrid_types) < 2:
            validation_report['suggestions'].append(
                "Hybrid agent should combine at least 2 different agent types"
            )
        
        # Update valid flag based on errors
        validation_report['valid'] = len(validation_report['errors']) == 0
        
        return validation_report