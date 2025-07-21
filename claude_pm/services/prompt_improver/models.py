"""
Data models and enums for prompt improvement system

This module contains all data models, enums, and dataclasses used throughout
the prompt improvement system.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ImprovementStrategy(Enum):
    """Improvement strategy types"""
    ADDITIVE = "additive"          # Add context/instructions
    REPLACEMENT = "replacement"    # Replace problematic sections
    CONTEXTUAL = "contextual"      # Context-aware improvements
    STRUCTURAL = "structural"      # Structural prompt changes


@dataclass
class PromptImprovement:
    """Represents a single prompt improvement"""
    improvement_id: str
    agent_type: str
    strategy: ImprovementStrategy
    original_prompt: str
    improved_prompt: str
    improvement_reason: str
    confidence_score: float
    timestamp: datetime
    version: str
    validation_status: str = "pending"
    effectiveness_score: Optional[float] = None
    rollback_reason: Optional[str] = None


@dataclass
class CorrectionPattern:
    """Represents a pattern found in corrections"""
    pattern_id: str
    agent_type: str
    pattern_type: str
    frequency: int
    severity: str
    common_issues: List[str]
    suggested_improvement: str
    confidence: float
    first_seen: datetime
    last_seen: datetime


@dataclass
class ImprovementMetrics:
    """Metrics for improvement effectiveness"""
    improvement_id: str
    success_rate: float
    error_reduction: float
    performance_improvement: float
    user_satisfaction: float
    rollback_rate: float
    adoption_rate: float


# Configuration defaults
DEFAULT_IMPROVEMENT_THRESHOLD = 0.7
DEFAULT_PATTERN_MIN_FREQUENCY = 3
DEFAULT_VALIDATION_TIMEOUT = 300

# Agent type constants
AGENT_TYPES = [
    'Documentation',
    'QA', 
    'Engineer',
    'Ops',
    'Research',
    'Security',
    'Version Control',
    'Ticketing',
    'Data Engineer'
]

# Severity levels
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# Validation statuses
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_ROLLED_BACK = "rolled_back"
STATUS_ERROR = "error"