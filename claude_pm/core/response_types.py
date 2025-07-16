"""
Response Types for Claude PM Framework
=====================================

Standard response types for consistent error handling and communication
across all services and subprocess creators.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TaskToolResponse:
    """
    Standard response object for Task Tool subprocess operations.
    
    Provides consistent structure for all subprocess creators and
    service operations to ensure reliable error handling and feedback.
    """
    request_id: str
    success: bool
    enhanced_prompt: Optional[str] = None
    error: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}


@dataclass  
class ServiceResponse:
    """
    Standard response object for service operations.
    
    Used for service health checks, initialization, and general operations
    that need consistent error reporting.
    """
    operation_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class HealthCheckResponse:
    """
    Standard response object for health check operations.
    
    Provides structured health status reporting across all framework
    components and services.
    """
    check_id: str
    healthy: bool
    checks: Dict[str, bool] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.checks is None:
            self.checks = {}
        if self.metrics is None:
            self.metrics = {}