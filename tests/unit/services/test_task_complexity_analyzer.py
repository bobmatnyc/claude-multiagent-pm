#!/usr/bin/env python3
"""
Unit tests for TaskComplexityAnalyzer
=====================================

Tests the task complexity analysis functionality including:
- Complexity scoring algorithm
- Model selection logic
- Prompt size recommendations
- Various complexity factors
"""

import pytest
from unittest.mock import Mock, patch

from claude_pm.services.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
    ComplexityLevel,
    ModelType,
    ComplexityAnalysisResult,
    TaskComplexityFactors
)


class TestTaskComplexityAnalyzer:
    """Test suite for TaskComplexityAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a TaskComplexityAnalyzer instance."""
        return TaskComplexityAnalyzer()
    
    def test_simple_task_analysis(self, analyzer):
        """Test analysis of a simple task."""
        result = analyzer.analyze_task(
            task_description="Read the configuration file",
            file_count=1
        )
        
        assert result.complexity_level == ComplexityLevel.SIMPLE
        assert result.recommended_model == ModelType.HAIKU
        assert result.optimal_prompt_size == (300, 500)
        assert 0 <= result.complexity_score <= 30
    
    def test_medium_task_analysis(self, analyzer):
        """Test analysis of a medium complexity task."""
        result = analyzer.analyze_task(
            task_description="Implement user authentication with JWT tokens",
            file_count=5,  # Increased to ensure medium complexity
            context_size=6000,  # Increased context size
            requires_testing=True,
            integration_points=1  # Added integration point
        )
        
        assert result.complexity_level == ComplexityLevel.MEDIUM
        assert result.recommended_model == ModelType.SONNET
        assert result.optimal_prompt_size == (700, 1000)
        assert 31 <= result.complexity_score <= 70
    
    def test_complex_task_analysis(self, analyzer):
        """Test analysis of a complex task."""
        result = analyzer.analyze_task(
            task_description="Refactor the entire authentication module to use OAuth2",
            file_count=10,
            context_size=15000,
            integration_points=3,
            requires_research=True,
            requires_testing=True,
            requires_documentation=True,
            technical_depth="deep"
        )
        
        assert result.complexity_level == ComplexityLevel.COMPLEX
        assert result.recommended_model == ModelType.OPUS
        assert result.optimal_prompt_size == (1200, 1500)
        assert 71 <= result.complexity_score <= 100
    
    def test_verb_complexity_scoring(self, analyzer):
        """Test verb-based complexity scoring."""
        # Simple verb
        simple_result = analyzer.analyze_task("List all available users")
        assert simple_result.analysis_details["verb_complexity"] == "simple"
        
        # Medium verb
        medium_result = analyzer.analyze_task("Create a new user profile")
        assert medium_result.analysis_details["verb_complexity"] == "medium"
        
        # Complex verb
        complex_result = analyzer.analyze_task("Architect a new microservices system")
        assert complex_result.analysis_details["verb_complexity"] == "complex"
    
    def test_file_complexity_scoring(self, analyzer):
        """Test file count impact on complexity."""
        # Low file count
        result1 = analyzer.analyze_task("Update configuration", file_count=1)
        score1 = result1.scoring_breakdown["file_complexity"]
        
        # Medium file count
        result2 = analyzer.analyze_task("Update configuration", file_count=4)
        score2 = result2.scoring_breakdown["file_complexity"]
        
        # High file count
        result3 = analyzer.analyze_task("Update configuration", file_count=8)
        score3 = result3.scoring_breakdown["file_complexity"]
        
        assert score1 < score2 < score3
        assert score1 == 0
        assert score2 == 10
        assert score3 > 10
    
    def test_context_size_scoring(self, analyzer):
        """Test context size impact on complexity."""
        # Small context
        result1 = analyzer.analyze_task("Process data", context_size=500)
        score1 = result1.scoring_breakdown["context_complexity"]
        
        # Medium context
        result2 = analyzer.analyze_task("Process data", context_size=5000)
        score2 = result2.scoring_breakdown["context_complexity"]
        
        # Large context
        result3 = analyzer.analyze_task("Process data", context_size=15000)
        score3 = result3.scoring_breakdown["context_complexity"]
        
        assert score1 < score2 < score3
        assert score1 == 0
        assert score2 == 10
        assert score3 == 15
    
    def test_technical_indicators(self, analyzer):
        """Test technical indicator detection."""
        result = analyzer.analyze_task(
            "Optimize database performance and refactor authentication architecture"
        )
        
        indicators = result.analysis_details["technical_indicators"]
        assert "performance" in indicators
        assert "refactoring" in indicators
        assert "architecture" in indicators
    
    def test_step_estimation(self, analyzer):
        """Test task step estimation."""
        # Numbered steps
        result1 = analyzer.analyze_task(
            "1. Setup database 2. Create schema 3. Import data"
        )
        assert result1.analysis_details["estimated_steps"] == 3
        
        # Step words
        result2 = analyzer.analyze_task(
            "First setup the environment, then deploy, finally test"
        )
        assert result2.analysis_details["estimated_steps"] >= 2
        
        # No explicit steps
        result3 = analyzer.analyze_task("Update the configuration file")
        assert result3.analysis_details["estimated_steps"] >= 1
    
    def test_additional_requirements_scoring(self, analyzer):
        """Test scoring of additional requirements."""
        # No additional requirements
        result1 = analyzer.analyze_task("Update config")
        score1 = result1.scoring_breakdown["additional_requirements"]
        
        # Some requirements
        result2 = analyzer.analyze_task(
            "Update config",
            requires_testing=True,
            requires_documentation=True
        )
        score2 = result2.scoring_breakdown["additional_requirements"]
        
        # All requirements
        result3 = analyzer.analyze_task(
            "Update config",
            requires_research=True,
            requires_testing=True,
            requires_documentation=True
        )
        score3 = result3.scoring_breakdown["additional_requirements"]
        
        assert score1 == 0
        assert score2 == 10
        assert score3 == 15
    
    def test_technical_depth_scoring(self, analyzer):
        """Test technical depth impact on complexity."""
        # No depth specified
        result1 = analyzer.analyze_task("Update code")
        score1 = result1.scoring_breakdown["technical_depth"]
        
        # Shallow depth
        result2 = analyzer.analyze_task("Update code", technical_depth="shallow")
        score2 = result2.scoring_breakdown["technical_depth"]
        
        # Deep depth
        result3 = analyzer.analyze_task("Update code", technical_depth="deep")
        score3 = result3.scoring_breakdown["technical_depth"]
        
        assert score1 == 0
        assert score2 == 2
        assert score3 == 10
    
    def test_integration_complexity_scoring(self, analyzer):
        """Test integration points impact on complexity."""
        # No integrations
        result1 = analyzer.analyze_task("Process data", integration_points=0)
        score1 = result1.scoring_breakdown["integration_complexity"]
        
        # Some integrations
        result2 = analyzer.analyze_task("Process data", integration_points=2)
        score2 = result2.scoring_breakdown["integration_complexity"]
        
        # Many integrations (capped at 15)
        result3 = analyzer.analyze_task("Process data", integration_points=5)
        score3 = result3.scoring_breakdown["integration_complexity"]
        
        assert score1 == 0
        assert score2 == 10
        assert score3 == 15  # Capped
    
    def test_prompt_optimization_hints(self, analyzer):
        """Test prompt optimization hints generation."""
        # Simple task
        simple_result = analyzer.analyze_task("Read file contents")
        simple_hints = analyzer.get_prompt_optimization_hints(simple_result)
        
        assert simple_hints["model"] == "haiku"
        assert "use_concise_instructions" in simple_hints["optimization_strategies"]
        
        # Complex task
        complex_result = analyzer.analyze_task(
            "Refactor authentication system with new security requirements",
            file_count=20,  # Increased file count
            integration_points=5,  # Max integration points
            requires_testing=True,
            requires_documentation=True,
            technical_depth="deep"  # Added deep technical depth
        )
        complex_hints = analyzer.get_prompt_optimization_hints(complex_result)
        
        assert complex_hints["model"] == "opus"
        assert "provide_comprehensive_context" in complex_hints["optimization_strategies"]
        assert "file_organization" in complex_hints["focus_areas"]
        assert "integration_boundaries" in complex_hints["focus_areas"]
    
    def test_edge_cases(self, analyzer):
        """Test edge cases and boundary conditions."""
        # Empty description
        result1 = analyzer.analyze_task("")
        assert result1.complexity_level == ComplexityLevel.SIMPLE
        
        # Very long description
        long_desc = "x" * 500
        result2 = analyzer.analyze_task(long_desc)
        assert result2.complexity_score > 0
        
        # Maximum complexity factors
        result3 = analyzer.analyze_task(
            "Architect and implement a complete system overhaul",
            file_count=100,
            context_size=50000,
            integration_points=10,
            requires_research=True,
            requires_testing=True,
            requires_documentation=True,
            technical_depth="deep"
        )
        assert result3.complexity_score <= 100
        assert result3.complexity_level == ComplexityLevel.COMPLEX
    
    def test_scoring_breakdown_completeness(self, analyzer):
        """Test that all scoring categories are included."""
        result = analyzer.analyze_task(
            "Create a new feature",
            file_count=3,
            context_size=2000,
            integration_points=1,
            requires_testing=True,
            technical_depth="moderate"
        )
        
        expected_categories = {
            "description_complexity",
            "file_complexity",
            "context_complexity",
            "integration_complexity",
            "additional_requirements",
            "technical_depth"
        }
        
        assert set(result.scoring_breakdown.keys()) == expected_categories
        assert all(isinstance(score, int) for score in result.scoring_breakdown.values())
    
    def test_analysis_details_structure(self, analyzer):
        """Test the structure of analysis details."""
        result = analyzer.analyze_task(
            "Implement API endpoints for user management"
        )
        
        assert "verb_complexity" in result.analysis_details
        assert "technical_indicators" in result.analysis_details
        assert "task_length" in result.analysis_details
        assert "estimated_steps" in result.analysis_details
        assert "complexity_factors" in result.analysis_details
        
        factors = result.analysis_details["complexity_factors"]
        assert "file_operations" in factors
        assert "context_weight" in factors
        assert "integration_complexity" in factors
        assert "additional_requirements" in factors
    
    @patch('claude_pm.services.task_complexity_analyzer.logger')
    def test_logging(self, mock_logger):
        """Test that appropriate logging occurs."""
        # Create analyzer after patching logger
        analyzer = TaskComplexityAnalyzer()
        
        # Analyze a task
        analyzer.analyze_task("Test task")
        
        # Check that debug log was called for initialization
        assert mock_logger.debug.called
        
        # Check that info log was called for completion
        assert mock_logger.info.called
        info_call = mock_logger.info.call_args[0][0]
        assert "Task complexity analysis complete" in info_call


class TestComplexityAnalysisResult:
    """Test the ComplexityAnalysisResult dataclass."""
    
    def test_dataclass_creation(self):
        """Test creating a ComplexityAnalysisResult instance."""
        result = ComplexityAnalysisResult(
            complexity_score=50,
            complexity_level=ComplexityLevel.MEDIUM,
            recommended_model=ModelType.SONNET,
            optimal_prompt_size=(700, 1000),
            scoring_breakdown={"test": 10},
            analysis_details={"test": "detail"}
        )
        
        assert result.complexity_score == 50
        assert result.complexity_level == ComplexityLevel.MEDIUM
        assert result.recommended_model == ModelType.SONNET
        assert result.optimal_prompt_size == (700, 1000)
        assert result.scoring_breakdown == {"test": 10}
        assert result.analysis_details == {"test": "detail"}


class TestTaskComplexityFactors:
    """Test the TaskComplexityFactors dataclass."""
    
    def test_dataclass_defaults(self):
        """Test default values in TaskComplexityFactors."""
        factors = TaskComplexityFactors(task_description="Test task")
        
        assert factors.task_description == "Test task"
        assert factors.context_size == 0
        assert factors.file_count == 0
        assert factors.integration_points == 0
        assert factors.requires_research is False
        assert factors.requires_testing is False
        assert factors.requires_documentation is False
        assert factors.technical_depth is None