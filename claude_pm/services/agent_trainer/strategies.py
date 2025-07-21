"""
Agent Training Strategies
========================

This module contains agent-specific training strategies including abstract base class
and concrete implementations for different agent types.

Classes:
    AgentTrainingStrategy: Abstract base class for training strategies
    EngineerTrainingStrategy: Training strategy for Engineer agents
    DocumentationTrainingStrategy: Training strategy for Documentation agents
    QATrainingStrategy: Training strategy for QA agents
    GenericTrainingStrategy: Generic training strategy for other agent types
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from ...core.config import Config
from .types import LearningAdaptation, TrainingSession

logger = logging.getLogger(__name__)


class AgentTrainingStrategy(ABC):
    """Abstract base class for agent-specific training strategies."""
    
    def __init__(self, agent_type: str, config: Config):
        self.agent_type = agent_type
        self.config = config
        self.training_history: List[TrainingSession] = []
        self.adaptations: List[LearningAdaptation] = []
        
    @abstractmethod
    async def generate_training_prompt(self, context: Dict[str, Any]) -> str:
        """Generate training prompt for this agent type."""
        pass
    
    @abstractmethod
    async def evaluate_improvement(self, 
                                 original: str, 
                                 improved: str, 
                                 context: Dict[str, Any]) -> float:
        """Evaluate improvement effectiveness."""
        pass
    
    @abstractmethod
    async def adapt_strategy(self, performance_data: Dict[str, Any]) -> None:
        """Adapt training strategy based on performance."""
        pass


class EngineerTrainingStrategy(AgentTrainingStrategy):
    """Training strategy for Engineer agents."""
    
    async def generate_training_prompt(self, context: Dict[str, Any]) -> str:
        """Generate engineering-specific training prompt."""
        return f"""
        Improve the following code implementation:
        
        Original Response: {context.get('original_response', '')}
        Context: {context.get('task_description', '')}
        
        Focus on:
        1. Code efficiency and performance
        2. Best practices and design patterns
        3. Error handling and edge cases
        4. Code readability and maintainability
        5. Security considerations
        
        Provide improved implementation with:
        - Optimized algorithms
        - Proper error handling
        - Comprehensive comments
        - Unit test suggestions
        - Performance analysis
        """
    
    async def evaluate_improvement(self, 
                                 original: str, 
                                 improved: str, 
                                 context: Dict[str, Any]) -> float:
        """Evaluate code improvement."""
        score = 0.0
        
        # Check for common improvements
        if "try:" in improved and "try:" not in original:
            score += 20  # Error handling
        if "def " in improved and len(improved.split("def ")) > len(original.split("def ")):
            score += 15  # Code modularization
        if "# " in improved and "# " not in original:
            score += 10  # Documentation
        if "test" in improved.lower():
            score += 15  # Testing consideration
        if len(improved) > len(original) * 1.2:
            score += 10  # More comprehensive
        
        return min(score, 100.0)
    
    async def adapt_strategy(self, performance_data: Dict[str, Any]) -> None:
        """Adapt engineering training strategy."""
        if performance_data.get('average_score', 0) < 70:
            # Focus more on basics
            adaptation = LearningAdaptation(
                agent_type=self.agent_type,
                adaptation_type="focus_shift",
                trigger_condition="low_performance",
                adaptation_data={"focus": "basic_patterns", "complexity": "reduced"},
                effectiveness_score=0.0
            )
            self.adaptations.append(adaptation)


class DocumentationTrainingStrategy(AgentTrainingStrategy):
    """Training strategy for Documentation agents."""
    
    async def generate_training_prompt(self, context: Dict[str, Any]) -> str:
        """Generate documentation-specific training prompt."""
        return f"""
        Improve the following documentation:
        
        Original Response: {context.get('original_response', '')}
        Context: {context.get('task_description', '')}
        
        Focus on:
        1. Clear and concise explanations
        2. Proper structure and formatting
        3. Examples and use cases
        4. API documentation standards
        5. User-friendly language
        
        Provide improved documentation with:
        - Structured sections (Overview, Parameters, Examples, etc.)
        - Code examples with explanations
        - Best practices and gotchas
        - Cross-references and links
        - Version information
        """
    
    async def evaluate_improvement(self, 
                                 original: str, 
                                 improved: str, 
                                 context: Dict[str, Any]) -> float:
        """Evaluate documentation improvement."""
        score = 0.0
        
        # Check for documentation improvements
        if "##" in improved and "##" not in original:
            score += 20  # Structure
        if "```" in improved and "```" not in original:
            score += 15  # Code examples
        if "**" in improved and "**" not in original:
            score += 10  # Formatting
        if "Parameters:" in improved or "Args:" in improved:
            score += 15  # API documentation
        if len(improved) > len(original) * 1.5:
            score += 10  # More comprehensive
        
        return min(score, 100.0)
    
    async def adapt_strategy(self, performance_data: Dict[str, Any]) -> None:
        """Adapt documentation training strategy."""
        if performance_data.get('clarity_score', 0) < 70:
            adaptation = LearningAdaptation(
                agent_type=self.agent_type,
                adaptation_type="clarity_focus",
                trigger_condition="low_clarity",
                adaptation_data={"emphasis": "simple_language", "examples": "increased"},
                effectiveness_score=0.0
            )
            self.adaptations.append(adaptation)


class QATrainingStrategy(AgentTrainingStrategy):
    """Training strategy for QA agents."""
    
    async def generate_training_prompt(self, context: Dict[str, Any]) -> str:
        """Generate QA-specific training prompt."""
        return f"""
        Improve the following QA analysis:
        
        Original Response: {context.get('original_response', '')}
        Context: {context.get('task_description', '')}
        
        Focus on:
        1. Comprehensive test coverage analysis
        2. Risk assessment and mitigation
        3. Performance and security testing
        4. Detailed test results reporting
        5. Actionable recommendations
        
        Provide improved QA analysis with:
        - Detailed test metrics and coverage
        - Risk assessment matrix
        - Performance benchmarks
        - Security vulnerability analysis
        - Clear pass/fail criteria
        """
    
    async def evaluate_improvement(self, 
                                 original: str, 
                                 improved: str, 
                                 context: Dict[str, Any]) -> float:
        """Evaluate QA improvement."""
        score = 0.0
        
        # Check for QA improvements
        if "coverage" in improved.lower() and "coverage" not in original.lower():
            score += 20  # Test coverage
        if "risk" in improved.lower() and "risk" not in original.lower():
            score += 15  # Risk assessment
        if any(word in improved.lower() for word in ["performance", "security", "vulnerability"]):
            score += 15  # Comprehensive testing
        if "%" in improved and "%" not in original:
            score += 10  # Metrics
        if "recommend" in improved.lower():
            score += 10  # Actionable recommendations
        
        return min(score, 100.0)
    
    async def adapt_strategy(self, performance_data: Dict[str, Any]) -> None:
        """Adapt QA training strategy."""
        if performance_data.get('completeness_score', 0) < 70:
            adaptation = LearningAdaptation(
                agent_type=self.agent_type,
                adaptation_type="completeness_focus",
                trigger_condition="incomplete_analysis",
                adaptation_data={"checklist": "expanded", "metrics": "detailed"},
                effectiveness_score=0.0
            )
            self.adaptations.append(adaptation)


class GenericTrainingStrategy(AgentTrainingStrategy):
    """Generic training strategy for other agent types."""
    
    async def generate_training_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Improve the following response for {self.agent_type} agent:
        
        Original Response: {context.get('original_response', '')}
        Context: {context.get('task_description', '')}
        
        Focus on improving:
        1. Accuracy and correctness
        2. Completeness and thoroughness
        3. Clarity and readability
        4. Relevance to the task
        5. Professional quality
        """
    
    async def evaluate_improvement(self, original: str, improved: str, context: Dict[str, Any]) -> float:
        # Basic improvement scoring
        score = 0.0
        if len(improved) > len(original):
            score += 20
        if improved.count('.') > original.count('.'):
            score += 15
        if improved.count('\n') > original.count('\n'):
            score += 10
        return min(score, 100.0)
    
    async def adapt_strategy(self, performance_data: Dict[str, Any]) -> None:
        pass


def create_training_strategy(agent_type: str, config: Config) -> AgentTrainingStrategy:
    """Factory function to create appropriate training strategy."""
    strategies = {
        'engineer': EngineerTrainingStrategy,
        'documentation': DocumentationTrainingStrategy,
        'qa': QATrainingStrategy,
    }
    
    strategy_class = strategies.get(agent_type, GenericTrainingStrategy)
    return strategy_class(agent_type, config)