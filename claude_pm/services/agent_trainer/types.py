"""
Agent Trainer Data Models and Types
==================================

This module contains all data models, enums, and type definitions for the agent training system.
Part of the Phase 2 refactoring to modularize agent_trainer.py.

Classes:
    TrainingMode: Enum for training modes
    TrainingDataFormat: Enum for data formats
    TrainingTemplate: Training template data model
    TrainingSession: Individual training session data model
    LearningAdaptation: Real-time learning adaptation data model
    PerformancePrediction: Performance prediction and trend analysis data model
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class TrainingMode(Enum):
    """Training modes for different scenarios."""
    CONTINUOUS = "continuous"
    BATCH = "batch"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    MULTI_MODAL = "multi_modal"
    DISTRIBUTED = "distributed"


class TrainingDataFormat(Enum):
    """Supported training data formats."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    CONVERSATION = "conversation"
    MIXED = "mixed"


@dataclass
class TrainingTemplate:
    """Training template for agent-specific improvement."""
    agent_type: str
    template_id: str
    description: str
    training_strategy: str
    prompt_template: str
    success_criteria: List[str]
    improvement_areas: List[str]
    data_format: TrainingDataFormat
    complexity_level: str = "intermediate"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class TrainingSession:
    """Individual training session data."""
    session_id: str
    agent_type: str
    training_mode: TrainingMode
    template_id: str
    original_response: str
    improved_response: str
    evaluation_before: Optional[Any] = None  # EvaluationResult type
    evaluation_after: Optional[Any] = None  # EvaluationResult type
    improvement_score: float = 0.0
    training_duration: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['timestamp'] = self.timestamp.isoformat()
        # Convert evaluation results
        if self.evaluation_before:
            data['evaluation_before'] = self.evaluation_before.to_dict()
        if self.evaluation_after:
            data['evaluation_after'] = self.evaluation_after.to_dict()
        return data


@dataclass
class LearningAdaptation:
    """Real-time learning adaptation data."""
    agent_type: str
    adaptation_type: str
    trigger_condition: str
    adaptation_data: Dict[str, Any]
    effectiveness_score: float
    applied_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['applied_at'] = self.applied_at.isoformat()
        return data


@dataclass
class PerformancePrediction:
    """Performance prediction and trend analysis."""
    agent_type: str
    prediction_type: str
    current_score: float
    predicted_score: float
    confidence: float
    trend_direction: str  # "improving", "declining", "stable"
    time_horizon: int  # days
    factors: List[str]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data