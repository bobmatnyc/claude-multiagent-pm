"""
Data models and enums for prompt validation framework.

This module contains all the data classes, enums, and type definitions
used throughout the prompt validation system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class TestType(Enum):
    """Types of validation tests"""
    AB_TEST = "ab_test"
    REGRESSION_TEST = "regression_test"
    PERFORMANCE_TEST = "performance_test"
    QUALITY_TEST = "quality_test"
    INTEGRATION_TEST = "integration_test"
    STRESS_TEST = "stress_test"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TestScenario:
    """Test scenario definition"""
    scenario_id: str
    name: str
    description: str
    agent_type: str
    task_description: str
    expected_outputs: List[str]
    evaluation_criteria: Dict[str, Any]
    test_data: Dict[str, Any]
    timeout: int = 300  # seconds
    retry_count: int = 3


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    scenario_id: str
    prompt_version: str
    execution_time: float
    success: bool
    score: float
    outputs: Dict[str, Any]
    errors: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime


@dataclass
class ABTestResult:
    """A/B test comparison result"""
    test_id: str
    prompt_a_id: str
    prompt_b_id: str
    scenarios_tested: int
    prompt_a_results: List[TestResult]
    prompt_b_results: List[TestResult]
    statistical_significance: float
    winner: Optional[str]
    confidence_level: float
    improvement_metrics: Dict[str, Any]
    timestamp: datetime


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    report_id: str
    prompt_id: str
    prompt_version: str
    validation_type: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_score: float
    test_results: List[TestResult]
    recommendations: List[str]
    timestamp: datetime