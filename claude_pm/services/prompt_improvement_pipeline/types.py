"""
Data types and enums for the prompt improvement pipeline.

This module contains all data classes and enumerations used across
the prompt improvement pipeline components.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class PipelineStage(Enum):
    """Pipeline execution stages"""
    CORRECTION_ANALYSIS = "correction_analysis"
    PATTERN_DETECTION = "pattern_detection"
    IMPROVEMENT_GENERATION = "improvement_generation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    agent_types: List[str]
    correction_analysis_days: int = 30
    pattern_detection_threshold: float = 0.7
    improvement_confidence_threshold: float = 0.8
    validation_sample_size: int = 10
    auto_deployment_enabled: bool = False
    monitoring_interval: int = 3600  # seconds
    pipeline_timeout: int = 7200  # seconds


@dataclass
class PipelineExecution:
    """Pipeline execution record"""
    execution_id: str
    config: PipelineConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.IDLE
    current_stage: Optional[PipelineStage] = None
    stage_results: Dict[str, Any] = None
    total_improvements: int = 0
    deployed_improvements: int = 0
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = None


@dataclass
class PipelineResults:
    """Comprehensive pipeline results"""
    execution_id: str
    agent_results: Dict[str, Any]
    improvement_summary: Dict[str, Any]
    validation_summary: Dict[str, Any]
    deployment_summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime