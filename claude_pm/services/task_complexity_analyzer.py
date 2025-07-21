#!/usr/bin/env python3
"""
Task Complexity Analyzer
========================

Analyzes task complexity to enable dynamic prompt generation and model selection.
Provides complexity scoring based on various factors including task description,
required actions, context size, and technical indicators.

Key Features:
- Complexity scoring algorithm with multiple factors
- Three-tier complexity levels: SIMPLE, MEDIUM, COMPLEX
- Model selection mapping based on complexity
- Optimal prompt size recommendations
- Integration with agent_loader workflow

Usage:
    from claude_pm.services.task_complexity_analyzer import TaskComplexityAnalyzer
    
    analyzer = TaskComplexityAnalyzer()
    result = analyzer.analyze_task(
        task_description="Refactor the authentication module",
        context_size=1500,
        file_count=3
    )
    
    print(f"Complexity: {result.complexity_level}")
    print(f"Recommended model: {result.recommended_model}")
    print(f"Optimal prompt size: {result.optimal_prompt_size}")
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Module-level logger
logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """Task complexity levels."""
    SIMPLE = "SIMPLE"
    MEDIUM = "MEDIUM"
    COMPLEX = "COMPLEX"


class ModelType(Enum):
    """Available model types for task execution."""
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


@dataclass
class ComplexityAnalysisResult:
    """Result of task complexity analysis."""
    complexity_score: int
    complexity_level: ComplexityLevel
    recommended_model: ModelType
    optimal_prompt_size: Tuple[int, int]  # (min, max) characters
    scoring_breakdown: Dict[str, int]
    analysis_details: Dict[str, any]


@dataclass
class TaskComplexityFactors:
    """Factors contributing to task complexity."""
    task_description: str
    context_size: int = 0
    file_count: int = 0
    integration_points: int = 0
    requires_research: bool = False
    requires_testing: bool = False
    requires_documentation: bool = False
    technical_depth: Optional[str] = None  # "shallow", "moderate", "deep"


class TaskComplexityAnalyzer:
    """
    Analyzes task complexity to determine optimal prompt generation strategy.
    """
    
    # Verb complexity mappings
    SIMPLE_VERBS = {
        "read", "list", "get", "fetch", "show", "display", "view",
        "check", "verify", "find", "search", "look"
    }
    
    MEDIUM_VERBS = {
        "create", "update", "modify", "add", "remove", "delete",
        "implement", "fix", "debug", "test", "validate", "integrate"
    }
    
    COMPLEX_VERBS = {
        "refactor", "architect", "design", "optimize", "analyze",
        "migrate", "transform", "orchestrate", "coordinate", "restructure"
    }
    
    # Technical keywords indicating complexity
    TECHNICAL_KEYWORDS = {
        "simple": ["basic", "simple", "straightforward", "trivial"],
        "medium": ["standard", "typical", "moderate", "conventional"],
        "complex": ["advanced", "complex", "sophisticated", "intricate", "comprehensive"]
    }
    
    # Model selection thresholds
    COMPLEXITY_THRESHOLDS = {
        ComplexityLevel.SIMPLE: (0, 30),
        ComplexityLevel.MEDIUM: (31, 70),
        ComplexityLevel.COMPLEX: (71, 100)
    }
    
    # Model prompt size recommendations
    PROMPT_SIZE_RECOMMENDATIONS = {
        ModelType.HAIKU: (300, 500),
        ModelType.SONNET: (700, 1000),
        ModelType.OPUS: (1200, 1500)
    }
    
    def __init__(self):
        """Initialize the task complexity analyzer."""
        logger.debug("TaskComplexityAnalyzer initialized")
    
    def analyze_task(
        self,
        task_description: str,
        context_size: int = 0,
        file_count: int = 0,
        integration_points: int = 0,
        requires_research: bool = False,
        requires_testing: bool = False,
        requires_documentation: bool = False,
        technical_depth: Optional[str] = None
    ) -> ComplexityAnalysisResult:
        """
        Analyze task complexity and provide recommendations.
        
        Args:
            task_description: Description of the task to analyze
            context_size: Size of context in characters
            file_count: Number of files involved
            integration_points: Number of system integration points
            requires_research: Whether task requires research
            requires_testing: Whether task requires testing
            requires_documentation: Whether task requires documentation
            technical_depth: Technical depth assessment
            
        Returns:
            ComplexityAnalysisResult with scoring and recommendations
        """
        factors = TaskComplexityFactors(
            task_description=task_description,
            context_size=context_size,
            file_count=file_count,
            integration_points=integration_points,
            requires_research=requires_research,
            requires_testing=requires_testing,
            requires_documentation=requires_documentation,
            technical_depth=technical_depth
        )
        
        # Calculate complexity scores
        scoring_breakdown = self._calculate_complexity_scores(factors)
        total_score = sum(scoring_breakdown.values())
        
        # Normalize score to 0-100 range
        normalized_score = min(100, max(0, total_score))
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(normalized_score)
        
        # Select appropriate model
        recommended_model = self._select_model(complexity_level)
        
        # Get optimal prompt size
        optimal_prompt_size = self.PROMPT_SIZE_RECOMMENDATIONS[recommended_model]
        
        # Compile analysis details
        analysis_details = {
            "verb_complexity": self._analyze_verb_complexity(task_description),
            "technical_indicators": self._analyze_technical_indicators(task_description),
            "task_length": len(task_description),
            "estimated_steps": self._estimate_task_steps(task_description),
            "complexity_factors": {
                "file_operations": file_count,
                "context_weight": self._calculate_context_weight(context_size),
                "integration_complexity": integration_points,
                "additional_requirements": sum([
                    requires_research,
                    requires_testing,
                    requires_documentation
                ])
            }
        }
        
        logger.info(
            f"Task complexity analysis complete: "
            f"score={normalized_score}, level={complexity_level.value}, "
            f"model={recommended_model.value}"
        )
        
        return ComplexityAnalysisResult(
            complexity_score=normalized_score,
            complexity_level=complexity_level,
            recommended_model=recommended_model,
            optimal_prompt_size=optimal_prompt_size,
            scoring_breakdown=scoring_breakdown,
            analysis_details=analysis_details
        )
    
    def _calculate_complexity_scores(self, factors: TaskComplexityFactors) -> Dict[str, int]:
        """
        Calculate individual complexity scores for different factors.
        
        Args:
            factors: Task complexity factors
            
        Returns:
            Dictionary of score breakdowns
        """
        scores = {}
        
        # Task description complexity (0-25 points)
        scores["description_complexity"] = self._score_description_complexity(
            factors.task_description
        )
        
        # File operation complexity (0-20 points)
        scores["file_complexity"] = self._score_file_complexity(factors.file_count)
        
        # Context size complexity (0-15 points)
        scores["context_complexity"] = self._score_context_complexity(
            factors.context_size
        )
        
        # Integration complexity (0-15 points)
        scores["integration_complexity"] = min(15, factors.integration_points * 5)
        
        # Additional requirements (0-15 points)
        additional_score = 0
        if factors.requires_research:
            additional_score += 5
        if factors.requires_testing:
            additional_score += 5
        if factors.requires_documentation:
            additional_score += 5
        scores["additional_requirements"] = additional_score
        
        # Technical depth (0-10 points)
        depth_scores = {
            None: 0,
            "shallow": 2,
            "moderate": 5,
            "deep": 10
        }
        scores["technical_depth"] = depth_scores.get(factors.technical_depth, 0)
        
        return scores
    
    def _score_description_complexity(self, description: str) -> int:
        """
        Score complexity based on task description analysis.
        
        Args:
            description: Task description text
            
        Returns:
            Complexity score (0-25)
        """
        score = 0
        description_lower = description.lower()
        
        # Verb complexity (0-10 points)
        words = description_lower.split()
        for word in words:
            if word in self.SIMPLE_VERBS:
                score += 2
                break
            elif word in self.MEDIUM_VERBS:
                score += 5
                break
            elif word in self.COMPLEX_VERBS:
                score += 10
                break
        
        # Length complexity (0-5 points)
        if len(description) > 200:
            score += 5
        elif len(description) > 100:
            score += 3
        elif len(description) > 50:
            score += 1
        
        # Technical keyword analysis (0-5 points)
        for level, keywords in self.TECHNICAL_KEYWORDS.items():
            if any(keyword in description_lower for keyword in keywords):
                if level == "complex":
                    score += 5
                elif level == "medium":
                    score += 3
                elif level == "simple":
                    score += 1
                break
        
        # Multi-step indicator (0-5 points)
        step_indicators = r'\d+\.|step|phase|stage|first|second|then|finally'
        if re.search(step_indicators, description_lower):
            score += 5
        
        return min(25, score)
    
    def _score_file_complexity(self, file_count: int) -> int:
        """
        Score complexity based on number of files.
        
        Args:
            file_count: Number of files involved
            
        Returns:
            Complexity score (0-20)
        """
        if file_count <= 2:
            return 0
        elif file_count <= 5:
            return 10
        else:
            return min(20, 10 + (file_count - 5) * 2)
    
    def _score_context_complexity(self, context_size: int) -> int:
        """
        Score complexity based on context size.
        
        Args:
            context_size: Size of context in characters
            
        Returns:
            Complexity score (0-15)
        """
        if context_size < 1000:
            return 0
        elif context_size < 5000:
            return 5
        elif context_size < 10000:
            return 10
        else:
            return 15
    
    def _determine_complexity_level(self, score: int) -> ComplexityLevel:
        """
        Determine complexity level from score.
        
        Args:
            score: Normalized complexity score (0-100)
            
        Returns:
            Complexity level
        """
        for level, (min_score, max_score) in self.COMPLEXITY_THRESHOLDS.items():
            if min_score <= score <= max_score:
                return level
        
        # Default to COMPLEX if score is out of range
        return ComplexityLevel.COMPLEX
    
    def _select_model(self, complexity_level: ComplexityLevel) -> ModelType:
        """
        Select appropriate model based on complexity level.
        
        Args:
            complexity_level: Task complexity level
            
        Returns:
            Recommended model type
        """
        model_mapping = {
            ComplexityLevel.SIMPLE: ModelType.HAIKU,
            ComplexityLevel.MEDIUM: ModelType.SONNET,
            ComplexityLevel.COMPLEX: ModelType.OPUS
        }
        
        return model_mapping.get(complexity_level, ModelType.OPUS)
    
    def _analyze_verb_complexity(self, description: str) -> str:
        """
        Analyze and categorize verb complexity in task description.
        
        Args:
            description: Task description
            
        Returns:
            Verb complexity category
        """
        description_lower = description.lower()
        words = description_lower.split()
        
        for word in words:
            if word in self.COMPLEX_VERBS:
                return "complex"
            elif word in self.MEDIUM_VERBS:
                return "medium"
            elif word in self.SIMPLE_VERBS:
                return "simple"
        
        return "unknown"
    
    def _analyze_technical_indicators(self, description: str) -> List[str]:
        """
        Extract technical indicators from task description.
        
        Args:
            description: Task description
            
        Returns:
            List of technical indicators found
        """
        indicators = []
        description_lower = description.lower()
        
        # Check for technical patterns
        patterns = {
            "architecture": r"architect|design|pattern|structure",
            "performance": r"optimi|performance|speed|efficiency",
            "refactoring": r"refactor|restructure|reorganize",
            "integration": r"integrat|connect|interface|api",
            "testing": r"test|qa|quality|validation",
            "security": r"security|auth|encrypt|permission"
        }
        
        for indicator, pattern in patterns.items():
            if re.search(pattern, description_lower):
                indicators.append(indicator)
        
        return indicators
    
    def _estimate_task_steps(self, description: str) -> int:
        """
        Estimate number of steps in task.
        
        Args:
            description: Task description
            
        Returns:
            Estimated number of steps
        """
        # Look for numbered lists or step indicators
        numbered_pattern = r'\d+\.'
        step_words = ["first", "second", "then", "next", "finally", "step"]
        
        numbered_matches = len(re.findall(numbered_pattern, description))
        step_word_count = sum(1 for word in step_words if word in description.lower())
        
        # Estimate based on findings
        if numbered_matches > 0:
            return numbered_matches
        elif step_word_count > 0:
            return max(2, step_word_count)
        else:
            # Default estimate based on description length
            return max(1, len(description) // 100)
    
    def _calculate_context_weight(self, context_size: int) -> str:
        """
        Calculate context weight category.
        
        Args:
            context_size: Size of context in characters
            
        Returns:
            Context weight category
        """
        if context_size < 1000:
            return "minimal"
        elif context_size < 5000:
            return "standard"
        else:
            return "comprehensive"
    
    def get_prompt_optimization_hints(
        self,
        analysis_result: ComplexityAnalysisResult
    ) -> Dict[str, any]:
        """
        Get prompt optimization hints based on analysis.
        
        Args:
            analysis_result: Result from task analysis
            
        Returns:
            Dictionary of optimization hints
        """
        hints = {
            "model": analysis_result.recommended_model.value,
            "prompt_size_range": analysis_result.optimal_prompt_size,
            "focus_areas": [],
            "optimization_strategies": []
        }
        
        # Add focus areas based on complexity factors
        if analysis_result.analysis_details["verb_complexity"] == "complex":
            hints["focus_areas"].append("detailed_instructions")
            hints["optimization_strategies"].append("break_down_complex_operations")
        
        if analysis_result.scoring_breakdown.get("file_complexity", 0) > 10:
            hints["focus_areas"].append("file_organization")
            hints["optimization_strategies"].append("batch_file_operations")
        
        if analysis_result.scoring_breakdown.get("integration_complexity", 0) > 10:
            hints["focus_areas"].append("integration_boundaries")
            hints["optimization_strategies"].append("define_clear_interfaces")
        
        # Add strategies based on complexity level
        if analysis_result.complexity_level == ComplexityLevel.SIMPLE:
            hints["optimization_strategies"].extend([
                "use_concise_instructions",
                "minimize_context_overhead"
            ])
        elif analysis_result.complexity_level == ComplexityLevel.COMPLEX:
            hints["optimization_strategies"].extend([
                "provide_comprehensive_context",
                "include_examples_and_patterns",
                "define_clear_success_criteria"
            ])
        
        return hints