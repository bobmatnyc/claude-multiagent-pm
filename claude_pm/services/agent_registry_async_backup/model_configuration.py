"""Model selection and configuration for agents."""

import re
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from claude_pm.services.model_selector import ModelSelector, ModelSelectionCriteria

logger = logging.getLogger(__name__)


class ModelConfigurator:
    """Handles model selection and configuration for agents."""
    
    def __init__(self, model_selector: Optional[ModelSelector] = None):
        """Initialize model configurator with optional model selector."""
        self.model_selector = model_selector or ModelSelector()
    
    async def extract_model_configuration(
        self, 
        agent_file: Path, 
        agent_type: str, 
        complexity_level: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract model configuration from agent file and apply intelligent selection.
        
        Args:
            agent_file: Path to agent file
            agent_type: Agent type classification
            complexity_level: Assessed complexity level
            
        Returns:
            Tuple of (preferred_model, model_config)
        """
        try:
            # Check for explicit model configuration in agent file
            content = agent_file.read_text(encoding='utf-8')
            preferred_model = None
            model_config = {}
            
            # Parse explicit model preferences from agent file
            explicit_model = self._parse_explicit_model_config(content)
            if explicit_model:
                preferred_model = explicit_model["model_id"]
                model_config = explicit_model.get("config", {})
                logger.debug(f"Found explicit model configuration in {agent_file.name}: {preferred_model}")
            
            # If no explicit configuration, use intelligent selection
            if not preferred_model:
                # Create selection criteria based on agent analysis
                criteria = ModelSelectionCriteria(
                    agent_type=agent_type,
                    task_complexity=complexity_level,
                    performance_requirements=self._analyze_performance_requirements(content),
                    reasoning_depth_required=self._analyze_reasoning_requirements(content, agent_type),
                    creativity_required=self._analyze_creativity_requirements(content),
                    speed_priority=self._analyze_speed_requirements(content)
                )
                
                # Select model using ModelSelector
                model_type, model_configuration = self.model_selector.select_model_for_agent(
                    agent_type, criteria
                )
                
                preferred_model = model_type.value
                model_config = {
                    "max_tokens": model_configuration.max_tokens,
                    "context_window": model_configuration.context_window,
                    "selection_criteria": {
                        "task_complexity": criteria.task_complexity,
                        "reasoning_depth": criteria.reasoning_depth_required,
                        "speed_priority": criteria.speed_priority,
                        "creativity_required": criteria.creativity_required
                    },
                    "capabilities": model_configuration.capabilities,
                    "performance_profile": model_configuration.performance_profile,
                    "auto_selected": True
                }
                
                logger.debug(f"Auto-selected model for {agent_type}: {preferred_model}")
            
            return preferred_model, model_config
            
        except Exception as e:
            logger.warning(f"Error extracting model configuration from {agent_file}: {e}")
            # Fallback to default model selection
            try:
                model_type, model_configuration = self.model_selector.select_model_for_agent(agent_type)
                return model_type.value, {
                    "max_tokens": model_configuration.max_tokens,
                    "fallback_selection": True,
                    "error": str(e)
                }
            except Exception as fallback_error:
                logger.error(f"Fallback model selection failed: {fallback_error}")
                return None, {"error": str(e), "fallback_error": str(fallback_error)}
    
    def _parse_explicit_model_config(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse explicit model configuration from agent file content.
        
        Looks for patterns like:
        - MODEL_PREFERENCE = "claude-3-opus-20240229"
        - PREFERRED_MODEL = "claude-3-5-sonnet-20241022"
        - model_config = {"model": "claude-3-opus-20240229", "max_tokens": 4096}
        """
        # Pattern for direct model assignment
        model_patterns = [
            r'MODEL_PREFERENCE\s*=\s*["\']([^"\']+)["\']',
            r'PREFERRED_MODEL\s*=\s*["\']([^"\']+)["\']',
            r'model\s*=\s*["\']([^"\']+)["\']',
            r'MODEL\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                model_id = match.group(1)
                return {"model_id": model_id, "config": {"explicit": True}}
        
        # Pattern for configuration dictionary
        config_pattern = r'model_config\s*=\s*\{([^}]+)\}'
        config_match = re.search(config_pattern, content, re.IGNORECASE)
        if config_match:
            try:
                # Simple parsing of model config dictionary
                config_str = config_match.group(1)
                model_match = re.search(r'["\']model["\']:\s*["\']([^"\']+)["\']', config_str)
                if model_match:
                    return {
                        "model_id": model_match.group(1),
                        "config": {"explicit": True, "from_dict": True}
                    }
            except Exception as e:
                logger.warning(f"Error parsing model config dictionary: {e}")
        
        return None
    
    def _analyze_performance_requirements(self, content: str) -> Dict[str, Any]:
        """Analyze performance requirements from agent file content."""
        requirements = {}
        content_lower = content.lower()
        
        # Speed requirements
        if any(keyword in content_lower for keyword in ['fast', 'quick', 'rapid', 'immediate']):
            requirements["speed_priority"] = True
        
        # Quality requirements  
        if any(keyword in content_lower for keyword in ['quality', 'accurate', 'precise', 'detailed']):
            requirements["quality_priority"] = True
            
        # Resource constraints
        if any(keyword in content_lower for keyword in ['efficient', 'lightweight', 'minimal']):
            requirements["resource_efficiency"] = True
            
        return requirements
    
    def _analyze_reasoning_requirements(self, content: str, agent_type: str) -> str:
        """Analyze reasoning depth requirements from content and agent type."""
        content_lower = content.lower()
        
        # Expert reasoning indicators
        if any(keyword in content_lower for keyword in [
            'architecture', 'design pattern', 'complex system', 'optimization',
            'strategic', 'planning', 'analysis', 'research'
        ]):
            return "expert"
        
        # Deep reasoning indicators
        if any(keyword in content_lower for keyword in [
            'investigate', 'analyze', 'evaluate', 'assess', 'compare'
        ]):
            return "deep"
        
        # Simple reasoning indicators
        if any(keyword in content_lower for keyword in [
            'format', 'display', 'show', 'list', 'basic'
        ]):
            return "simple"
        
        # Agent type-based defaults
        if agent_type in ['engineer', 'architecture', 'orchestrator']:
            return "expert"
        elif agent_type in ['research', 'analysis', 'qa']:
            return "deep"
        else:
            return "standard"
    
    def _analyze_creativity_requirements(self, content: str) -> bool:
        """Analyze creativity requirements from agent file content."""
        content_lower = content.lower()
        
        creativity_indicators = [
            'creative', 'innovative', 'design', 'brainstorm', 'ideate',
            'generate', 'invent', 'original', 'novel'
        ]
        
        return any(indicator in content_lower for indicator in creativity_indicators)
    
    def _analyze_speed_requirements(self, content: str) -> bool:
        """Analyze speed priority requirements from agent file content."""
        content_lower = content.lower()
        
        speed_indicators = [
            'urgent', 'quick', 'fast', 'immediate', 'rapid', 'asap',
            'real-time', 'instant', 'responsive'
        ]
        
        return any(indicator in content_lower for indicator in speed_indicators)