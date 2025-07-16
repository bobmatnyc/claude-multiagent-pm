"""
Model Selector Service - Intelligent model selection for agents
============================================================

This service provides intelligent model selection based on agent types, task complexity,
and performance requirements. Implements selection rules for Opus, Sonnet, and other models.

Key Features:
- Agent-type specific model selection
- Task complexity analysis
- Performance requirement matching
- Environment variable overrides
- Model fallback and error handling
- Configuration-based model mapping

Selection Rules:
- Opus: Orchestrator, Engineer agents (complex implementation tasks)
- Sonnet: Documentation, QA, Research, Ops, Security, Data Engineer agents
- Haiku: Simple tasks, rapid responses (when available)

Created: 2025-07-16
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available model types for agent selection"""
    # Claude 4 models (primary)
    OPUS_4 = "claude-4-opus"
    SONNET_4 = "claude-sonnet-4-20250514"
    # Legacy Claude 3 models (fallback)
    OPUS = "claude-3-opus-20240229"
    SONNET = "claude-3-5-sonnet-20241022"
    HAIKU = "claude-3-haiku-20240307"


@dataclass
class ModelSelectionCriteria:
    """Criteria for model selection decisions"""
    agent_type: str
    task_complexity: str = "medium"  # low, medium, high, expert
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    context_length_required: int = 8192
    reasoning_depth_required: str = "standard"  # simple, standard, deep, expert
    creativity_required: bool = False
    speed_priority: bool = False


@dataclass
class ModelConfiguration:
    """Model configuration and metadata"""
    model_id: str
    model_type: ModelType
    max_tokens: int
    context_window: int
    capabilities: List[str]
    performance_profile: Dict[str, Any]
    cost_tier: str  # low, medium, high
    speed_tier: str  # fast, medium, slow
    reasoning_tier: str  # basic, advanced, expert


class ModelSelector:
    """
    Intelligent model selector for agent-based task execution.
    
    Provides model selection based on agent types, task requirements,
    and system configuration with intelligent fallback mechanisms.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize ModelSelector with configuration."""
        self.config_path = config_path
        self.model_configurations = self._initialize_model_configurations()
        self.agent_model_mapping = self._initialize_agent_model_mapping()
        self.environment_overrides = self._load_environment_overrides()
        self.fallback_model = ModelType.SONNET_4
        
        logger.info("ModelSelector initialized with agent-specific model mapping")
    
    def _initialize_model_configurations(self) -> Dict[ModelType, ModelConfiguration]:
        """Initialize model configurations with capabilities and performance profiles."""
        return {
            ModelType.OPUS_4: ModelConfiguration(
                model_id="claude-4-opus",
                model_type=ModelType.OPUS_4,
                max_tokens=8192,
                context_window=200000,
                capabilities=[
                    "advanced_reasoning", "expert_code_generation", "system_architecture",
                    "complex_problem_solving", "strategic_planning", "deep_analysis",
                    "multi_step_implementation", "technical_leadership"
                ],
                performance_profile={
                    "reasoning_quality": "expert",
                    "code_quality": "expert",
                    "creativity": "high",
                    "speed": "medium",
                    "consistency": "expert"
                },
                cost_tier="high",
                speed_tier="medium",
                reasoning_tier="expert"
            ),
            
            ModelType.OPUS: ModelConfiguration(
                model_id="claude-3-opus-20240229",
                model_type=ModelType.OPUS,
                max_tokens=4096,
                context_window=200000,
                capabilities=[
                    "complex_reasoning", "code_generation", "system_design",
                    "architecture_planning", "creative_problem_solving",
                    "multi_step_analysis", "technical_writing"
                ],
                performance_profile={
                    "reasoning_quality": "expert",
                    "code_quality": "expert",
                    "creativity": "high",
                    "speed": "medium",
                    "consistency": "high"
                },
                cost_tier="high",
                speed_tier="slow",
                reasoning_tier="expert"
            ),
            
            ModelType.SONNET: ModelConfiguration(
                model_id="claude-3-5-sonnet-20241022",
                model_type=ModelType.SONNET,
                max_tokens=4096,
                context_window=200000,
                capabilities=[
                    "balanced_reasoning", "documentation", "analysis",
                    "testing", "research", "security_analysis",
                    "data_processing", "workflow_automation"
                ],
                performance_profile={
                    "reasoning_quality": "advanced",
                    "code_quality": "advanced",
                    "creativity": "medium",
                    "speed": "fast",
                    "consistency": "high"
                },
                cost_tier="medium",
                speed_tier="fast",
                reasoning_tier="advanced"
            ),
            
            ModelType.SONNET_4: ModelConfiguration(
                model_id="claude-sonnet-4-20250514",
                model_type=ModelType.SONNET_4,
                max_tokens=8192,
                context_window=200000,
                capabilities=[
                    "enhanced_reasoning", "advanced_code_generation",
                    "system_analysis", "optimization", "integration",
                    "performance_analysis", "strategic_planning"
                ],
                performance_profile={
                    "reasoning_quality": "expert",
                    "code_quality": "expert",
                    "creativity": "high",
                    "speed": "medium",
                    "consistency": "expert"
                },
                cost_tier="high",
                speed_tier="medium",
                reasoning_tier="expert"
            ),
            
            ModelType.HAIKU: ModelConfiguration(
                model_id="claude-3-haiku-20240307",
                model_type=ModelType.HAIKU,
                max_tokens=4096,
                context_window=200000,
                capabilities=[
                    "quick_responses", "simple_tasks", "basic_analysis",
                    "data_formatting", "simple_automation"
                ],
                performance_profile={
                    "reasoning_quality": "basic",
                    "code_quality": "basic",
                    "creativity": "low",
                    "speed": "very_fast",
                    "consistency": "medium"
                },
                cost_tier="low",
                speed_tier="very_fast",
                reasoning_tier="basic"
            )
        }
    
    def _initialize_agent_model_mapping(self) -> Dict[str, ModelType]:
        """
        Initialize agent type to model mapping based on research findings.
        
        Selection Rules:
        - Opus: Orchestrator, Engineer agents (complex implementation)
        - Sonnet: Documentation, QA, Research, Ops, Security, Data Engineer
        - Sonnet 4: Available for enhanced capabilities when specified
        """
        return {
            # Core agent types requiring Opus 4 (complex reasoning and implementation)
            'orchestrator': ModelType.OPUS_4,
            'engineer': ModelType.OPUS_4,
            'architecture': ModelType.OPUS_4,
            'system_design': ModelType.OPUS_4,
            
            # Core agent types using Sonnet 4 (balanced performance)
            'documentation': ModelType.SONNET_4,
            'qa': ModelType.SONNET_4,
            'research': ModelType.SONNET_4,
            'ops': ModelType.SONNET_4,
            'security': ModelType.SONNET_4,
            'data_engineer': ModelType.SONNET_4,
            'ticketing': ModelType.SONNET_4,
            'version_control': ModelType.SONNET_4,
            
            # Specialized agent types
            'ui_ux': ModelType.SONNET_4,
            'frontend': ModelType.SONNET_4,
            'backend': ModelType.OPUS_4,  # Complex server-side logic
            'database': ModelType.SONNET_4,
            'api': ModelType.SONNET_4,
            'testing': ModelType.SONNET_4,
            'performance': ModelType.OPUS_4,  # Complex optimization
            'monitoring': ModelType.SONNET_4,
            'analytics': ModelType.SONNET_4,
            'deployment': ModelType.SONNET_4,
            'integration': ModelType.OPUS_4,  # Complex system integration
            'workflow': ModelType.SONNET_4,
            'devops': ModelType.SONNET_4,
            'cloud': ModelType.SONNET_4,
            'infrastructure': ModelType.SONNET_4,
            'machine_learning': ModelType.OPUS_4,  # Complex ML tasks
            'data_science': ModelType.OPUS_4,  # Complex analysis
            'business_analysis': ModelType.SONNET_4,
            'project_management': ModelType.SONNET_4,
            'compliance': ModelType.SONNET_4,
            'content': ModelType.SONNET_4,
            'customer_support': ModelType.SONNET_4,
            'marketing': ModelType.SONNET_4,
            
            # Framework-specific agents
            'scaffolding': ModelType.SONNET_4,
            'code_review': ModelType.SONNET_4,
            'memory_management': ModelType.SONNET_4,
            'knowledge_base': ModelType.SONNET_4,
            'validation': ModelType.SONNET_4,
            'automation': ModelType.SONNET_4,
            
            # Custom and fallback
            'custom': ModelType.SONNET_4
        }
    
    def _load_environment_overrides(self) -> Dict[str, ModelType]:
        """Load model overrides from environment variables."""
        overrides = {}
        
        # Global model override
        global_override = os.getenv('CLAUDE_PM_MODEL_OVERRIDE')
        if global_override:
            try:
                model_type = ModelType(global_override)
                logger.info(f"Global model override: {model_type.value}")
                # Apply to all agent types
                for agent_type in self.agent_model_mapping.keys():
                    overrides[agent_type] = model_type
            except ValueError:
                logger.warning(f"Invalid global model override: {global_override}")
        
        # Agent-specific overrides
        for agent_type in self.agent_model_mapping.keys():
            env_var = f'CLAUDE_PM_MODEL_{agent_type.upper()}'
            model_override = os.getenv(env_var)
            if model_override:
                try:
                    model_type = ModelType(model_override)
                    overrides[agent_type] = model_type
                    logger.info(f"Agent-specific model override for {agent_type}: {model_type.value}")
                except ValueError:
                    logger.warning(f"Invalid model override for {agent_type}: {model_override}")
        
        return overrides
    
    def select_model_for_agent(
        self,
        agent_type: str,
        criteria: Optional[ModelSelectionCriteria] = None
    ) -> Tuple[ModelType, ModelConfiguration]:
        """
        Select optimal model for an agent based on type and criteria.
        
        Args:
            agent_type: Type of agent requiring model selection
            criteria: Optional selection criteria for advanced decision making
            
        Returns:
            Tuple of (selected_model_type, model_configuration)
        """
        try:
            # Check for environment overrides first
            if agent_type in self.environment_overrides:
                selected_model = self.environment_overrides[agent_type]
                logger.debug(f"Using environment override for {agent_type}: {selected_model.value}")
                return selected_model, self.model_configurations[selected_model]
            
            # Apply criteria-based selection if provided
            if criteria:
                selected_model = self._select_model_by_criteria(agent_type, criteria)
                if selected_model:
                    logger.debug(f"Criteria-based selection for {agent_type}: {selected_model.value}")
                    return selected_model, self.model_configurations[selected_model]
            
            # Use default agent type mapping
            if agent_type in self.agent_model_mapping:
                selected_model = self.agent_model_mapping[agent_type]
                logger.debug(f"Default mapping for {agent_type}: {selected_model.value}")
                return selected_model, self.model_configurations[selected_model]
            
            # Fallback to default model
            logger.info(f"No mapping found for agent type '{agent_type}', using fallback: {self.fallback_model.value}")
            return self.fallback_model, self.model_configurations[self.fallback_model]
            
        except Exception as e:
            logger.error(f"Error selecting model for agent {agent_type}: {e}")
            return self.fallback_model, self.model_configurations[self.fallback_model]
    
    def _select_model_by_criteria(
        self,
        agent_type: str,
        criteria: ModelSelectionCriteria
    ) -> Optional[ModelType]:
        """
        Select model based on advanced criteria analysis.
        
        Args:
            agent_type: Agent type
            criteria: Selection criteria
            
        Returns:
            Selected model type or None if no criteria match
        """
        # Priority 1: Speed requirements
        if criteria.speed_priority:
            # Use fastest model that meets minimum requirements
            if criteria.task_complexity == "low":
                return ModelType.HAIKU
            else:
                return ModelType.SONNET
        
        # Priority 2: Task complexity analysis
        if criteria.task_complexity == "expert":
            # Use most capable model for expert-level tasks
            return ModelType.OPUS_4
        elif criteria.task_complexity == "high":
            # Use advanced model for high complexity
            if agent_type in ['engineer', 'architecture', 'machine_learning']:
                return ModelType.OPUS_4
            else:
                return ModelType.SONNET_4
        elif criteria.task_complexity == "low":
            # Use efficient model for simple tasks
            return ModelType.HAIKU
        
        # Priority 3: Reasoning depth requirements
        if criteria.reasoning_depth_required == "expert":
            return ModelType.OPUS_4
        elif criteria.reasoning_depth_required == "deep":
            return ModelType.SONNET_4
        elif criteria.reasoning_depth_required == "simple":
            return ModelType.HAIKU
        
        # Priority 4: Creativity requirements
        if criteria.creativity_required:
            return ModelType.OPUS_4
        
        # Priority 5: Context length requirements
        if criteria.context_length_required > 100000:
            # All models handle large context, prefer based on other factors
            return None  # Let other criteria decide
        
        # No specific criteria matched
        return None
    
    def get_model_recommendation(
        self,
        agent_type: str,
        task_description: str = "",
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive model recommendation with analysis.
        
        Args:
            agent_type: Type of agent
            task_description: Description of the task
            performance_requirements: Performance requirements
            
        Returns:
            Dictionary containing recommendation and analysis
        """
        # Analyze task complexity from description
        criteria = self._analyze_task_requirements(task_description, performance_requirements)
        criteria.agent_type = agent_type
        
        # Select model
        selected_model, model_config = self.select_model_for_agent(agent_type, criteria)
        
        # Generate recommendation
        recommendation = {
            "recommended_model": selected_model.value,
            "model_type": selected_model.name,
            "model_configuration": {
                "max_tokens": model_config.max_tokens,
                "context_window": model_config.context_window,
                "capabilities": model_config.capabilities,
                "performance_profile": model_config.performance_profile,
                "cost_tier": model_config.cost_tier,
                "speed_tier": model_config.speed_tier
            },
            "selection_reasoning": self._generate_selection_reasoning(
                agent_type, criteria, selected_model, model_config
            ),
            "alternative_models": self._get_alternative_models(agent_type, criteria),
            "configuration_overrides": self._get_configuration_overrides(agent_type),
            "selection_criteria": {
                "task_complexity": criteria.task_complexity,
                "reasoning_depth": criteria.reasoning_depth_required,
                "speed_priority": criteria.speed_priority,
                "creativity_required": criteria.creativity_required
            }
        }
        
        return recommendation
    
    def _analyze_task_requirements(
        self,
        task_description: str,
        performance_requirements: Optional[Dict[str, Any]] = None
    ) -> ModelSelectionCriteria:
        """
        Analyze task requirements to determine selection criteria.
        
        Args:
            task_description: Task description text
            performance_requirements: Performance requirements
            
        Returns:
            ModelSelectionCriteria based on analysis
        """
        criteria = ModelSelectionCriteria(agent_type="")
        
        if not task_description:
            return criteria
        
        task_lower = task_description.lower()
        
        # Analyze complexity indicators
        complexity_indicators = {
            "expert": ["architecture", "design pattern", "optimization", "machine learning", "ai", "complex system"],
            "high": ["implement", "develop", "create", "build", "integrate", "analyze", "engineer"],
            "medium": ["update", "modify", "review", "test", "document", "configure"],
            "low": ["list", "show", "display", "format", "simple", "basic"]
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                criteria.task_complexity = level
                break
        
        # Analyze reasoning depth requirements
        if any(word in task_lower for word in ["strategy", "planning", "architecture", "design"]):
            criteria.reasoning_depth_required = "expert"
        elif any(word in task_lower for word in ["analysis", "investigation", "research"]):
            criteria.reasoning_depth_required = "deep"
        elif any(word in task_lower for word in ["simple", "basic", "quick"]):
            criteria.reasoning_depth_required = "simple"
        
        # Analyze creativity requirements
        if any(word in task_lower for word in ["creative", "innovative", "design", "brainstorm"]):
            criteria.creativity_required = True
        
        # Analyze speed requirements
        if any(word in task_lower for word in ["urgent", "quick", "fast", "immediately"]):
            criteria.speed_priority = True
        
        # Apply performance requirements
        if performance_requirements:
            if performance_requirements.get("speed_priority"):
                criteria.speed_priority = True
            if performance_requirements.get("creativity_required"):
                criteria.creativity_required = True
            if performance_requirements.get("reasoning_depth"):
                criteria.reasoning_depth_required = performance_requirements["reasoning_depth"]
        
        return criteria
    
    def _generate_selection_reasoning(
        self,
        agent_type: str,
        criteria: ModelSelectionCriteria,
        selected_model: ModelType,
        model_config: ModelConfiguration
    ) -> str:
        """Generate human-readable reasoning for model selection."""
        reasoning_parts = []
        
        # Agent type reasoning
        if agent_type in self.environment_overrides:
            reasoning_parts.append(f"Environment override specified {selected_model.value} for {agent_type} agents")
        elif agent_type in ['orchestrator', 'engineer', 'architecture']:
            reasoning_parts.append(f"{agent_type} agents require Claude 4 advanced reasoning and implementation capabilities")
        else:
            reasoning_parts.append(f"{agent_type} agents benefit from balanced performance and efficiency")
        
        # Complexity reasoning
        if criteria.task_complexity == "expert":
            reasoning_parts.append("Expert-level task complexity requires most capable model")
        elif criteria.task_complexity == "high":
            reasoning_parts.append("High complexity task benefits from advanced reasoning")
        elif criteria.task_complexity == "low":
            reasoning_parts.append("Simple task allows for efficient model selection")
        
        # Speed reasoning
        if criteria.speed_priority:
            reasoning_parts.append("Speed priority favors faster response models")
        
        # Creativity reasoning
        if criteria.creativity_required:
            reasoning_parts.append("Creative tasks benefit from models with enhanced creative capabilities")
        
        # Model characteristics
        reasoning_parts.append(f"Selected model offers {model_config.performance_profile['reasoning_quality']} reasoning quality")
        reasoning_parts.append(f"Performance tier: {model_config.speed_tier} speed, {model_config.cost_tier} cost")
        
        return ". ".join(reasoning_parts)
    
    def _get_alternative_models(
        self,
        agent_type: str,
        criteria: ModelSelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Get alternative model options with trade-off analysis."""
        alternatives = []
        
        for model_type, config in self.model_configurations.items():
            # Skip the recommended model
            recommended_model, _ = self.select_model_for_agent(agent_type, criteria)
            if model_type == recommended_model:
                continue
            
            # Analyze trade-offs
            trade_offs = []
            if config.speed_tier == "very_fast":
                trade_offs.append("faster response time")
            if config.cost_tier == "low":
                trade_offs.append("lower cost")
            if config.reasoning_tier == "expert":
                trade_offs.append("enhanced reasoning")
            
            alternatives.append({
                "model": model_type.value,
                "trade_offs": trade_offs,
                "suitability_score": self._calculate_suitability_score(config, criteria)
            })
        
        # Sort by suitability score
        alternatives.sort(key=lambda x: x["suitability_score"], reverse=True)
        return alternatives[:3]  # Return top 3 alternatives
    
    def _calculate_suitability_score(
        self,
        model_config: ModelConfiguration,
        criteria: ModelSelectionCriteria
    ) -> float:
        """Calculate suitability score for a model given criteria."""
        score = 0.0
        
        # Speed alignment
        if criteria.speed_priority:
            speed_scores = {"very_fast": 1.0, "fast": 0.8, "medium": 0.5, "slow": 0.2}
            score += speed_scores.get(model_config.speed_tier, 0.5) * 0.3
        
        # Complexity alignment
        complexity_scores = {"expert": 1.0, "advanced": 0.8, "basic": 0.4}
        if criteria.task_complexity == "expert":
            score += complexity_scores.get(model_config.reasoning_tier, 0.5) * 0.4
        elif criteria.task_complexity == "low":
            # Inverse scoring for simple tasks
            score += (1.0 - complexity_scores.get(model_config.reasoning_tier, 0.5)) * 0.4
        
        # Creativity alignment
        if criteria.creativity_required:
            creativity_scores = {"high": 1.0, "medium": 0.6, "low": 0.2}
            creativity_level = model_config.performance_profile.get("creativity", "medium")
            score += creativity_scores.get(creativity_level, 0.5) * 0.3
        
        return min(score, 1.0)
    
    def _get_configuration_overrides(self, agent_type: str) -> Dict[str, Any]:
        """Get available configuration overrides for agent type."""
        overrides = {}
        
        # Environment variable suggestions
        overrides["environment_variables"] = {
            "global_override": "CLAUDE_PM_MODEL_OVERRIDE",
            "agent_specific": f"CLAUDE_PM_MODEL_{agent_type.upper()}"
        }
        
        # Available models
        overrides["available_models"] = [model.value for model in ModelType]
        
        return overrides
    
    def validate_model_selection(
        self,
        agent_type: str,
        selected_model: str
    ) -> Dict[str, Any]:
        """
        Validate model selection for an agent type.
        
        Args:
            agent_type: Agent type
            selected_model: Selected model ID
            
        Returns:
            Validation results with recommendations
        """
        try:
            model_type = ModelType(selected_model)
            model_config = self.model_configurations[model_type]
            
            # Get recommended model for comparison
            recommended_model, recommended_config = self.select_model_for_agent(agent_type)
            
            validation = {
                "valid": True,
                "selected_model": selected_model,
                "recommended_model": recommended_model.value,
                "matches_recommendation": model_type == recommended_model,
                "model_capabilities": model_config.capabilities,
                "performance_profile": model_config.performance_profile,
                "warnings": [],
                "suggestions": []
            }
            
            # Generate warnings and suggestions
            if model_type != recommended_model:
                if model_config.reasoning_tier == "basic" and agent_type in ['engineer', 'architecture']:
                    validation["warnings"].append(f"Basic reasoning model may be insufficient for {agent_type} tasks")
                
                if model_config.speed_tier == "slow" and agent_type in ['qa', 'documentation']:
                    validation["suggestions"].append("Consider faster model for improved iteration speed")
            
            return validation
            
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid model ID: {selected_model}",
                "available_models": [model.value for model in ModelType]
            }
    
    def get_agent_model_mapping(self) -> Dict[str, str]:
        """Get current agent type to model mapping."""
        mapping = {}
        for agent_type, model_type in self.agent_model_mapping.items():
            # Apply environment overrides
            if agent_type in self.environment_overrides:
                mapping[agent_type] = self.environment_overrides[agent_type].value
            else:
                mapping[agent_type] = model_type.value
        return mapping
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get model selection statistics and analysis."""
        stats = {
            "total_agent_types": len(self.agent_model_mapping),
            "model_distribution": {},
            "environment_overrides": len(self.environment_overrides),
            "available_models": len(self.model_configurations),
            "configuration_summary": {}
        }
        
        # Calculate model distribution
        for model_type in ModelType:
            count = sum(1 for mapped_model in self.agent_model_mapping.values() 
                       if mapped_model == model_type)
            stats["model_distribution"][model_type.value] = count
        
        # Configuration summary
        for model_type, config in self.model_configurations.items():
            stats["configuration_summary"][model_type.value] = {
                "capabilities_count": len(config.capabilities),
                "cost_tier": config.cost_tier,
                "speed_tier": config.speed_tier,
                "reasoning_tier": config.reasoning_tier
            }
        
        return stats


# Helper functions for easy integration
def select_model_for_agent_type(agent_type: str) -> Tuple[str, Dict[str, Any]]:
    """
    Quick model selection helper function.
    
    Args:
        agent_type: Type of agent
        
    Returns:
        Tuple of (model_id, model_configuration_dict)
    """
    selector = ModelSelector()
    model_type, model_config = selector.select_model_for_agent(agent_type)
    
    return model_type.value, {
        "max_tokens": model_config.max_tokens,
        "context_window": model_config.context_window,
        "capabilities": model_config.capabilities,
        "performance_profile": model_config.performance_profile
    }


def get_model_recommendation_for_task(
    agent_type: str,
    task_description: str
) -> Dict[str, Any]:
    """
    Get model recommendation for a specific task.
    
    Args:
        agent_type: Type of agent
        task_description: Description of the task
        
    Returns:
        Model recommendation with analysis
    """
    selector = ModelSelector()
    return selector.get_model_recommendation(agent_type, task_description)


def validate_agent_model_configuration(
    agent_type: str,
    model_id: str
) -> bool:
    """
    Validate if a model is suitable for an agent type.
    
    Args:
        agent_type: Type of agent
        model_id: Model identifier
        
    Returns:
        True if valid configuration
    """
    selector = ModelSelector()
    validation = selector.validate_model_selection(agent_type, model_id)
    return validation["valid"]


if __name__ == "__main__":
    # Test the ModelSelector
    selector = ModelSelector()
    
    # Test agent model selection
    print("Model Selection Tests:")
    print("=" * 50)
    
    test_agents = ['engineer', 'documentation', 'qa', 'orchestrator', 'data_engineer']
    
    for agent_type in test_agents:
        model_type, model_config = selector.select_model_for_agent(agent_type)
        print(f"{agent_type:15} -> {model_type.value}")
    
    # Test criteria-based selection
    print(f"\nCriteria-based Selection:")
    print("=" * 50)
    
    criteria = ModelSelectionCriteria(
        agent_type="engineer",
        task_complexity="expert",
        creativity_required=True
    )
    
    model_type, model_config = selector.select_model_for_agent("engineer", criteria)
    print(f"Expert engineering task -> {model_type.value}")
    
    # Test recommendation system
    print(f"\nModel Recommendation:")
    print("=" * 50)
    
    recommendation = selector.get_model_recommendation(
        "engineer",
        "Implement a complex microservices architecture with AI-powered optimization"
    )
    
    print(f"Recommended: {recommendation['recommended_model']}")
    print(f"Reasoning: {recommendation['selection_reasoning']}")
    
    # Test statistics
    print(f"\nSelection Statistics:")
    print("=" * 50)
    
    stats = selector.get_selection_statistics()
    print(f"Total agent types: {stats['total_agent_types']}")
    print(f"Model distribution: {stats['model_distribution']}")