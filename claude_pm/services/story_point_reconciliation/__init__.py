"""
Story Point Reconciliation Analysis System

This module provides functionality to analyze closed tickets and compare
initial story point estimates with actual work performed, helping teams
improve their estimation accuracy through data-driven insights.

Main components:
- Data collection from Git, PRs, and ticketing system
- Metrics calculation and normalization
- Pattern detection and analysis
- Reporting and visualization
"""

from .models import (
    EstimationUnit,
    TicketReconciliation,
    WorkMetrics,
    EstimationPattern,
    TeamMetrics,
    ReconciliationReport
)

from .collectors import (
    GitMetricsCollector,
    TicketDataCollector,
    WorkMetricsCollector
)

from .analyzer import (
    ReconciliationAnalyzer,
    PatternDetector,
    AccuracyCalculator
)

from .storage import ReconciliationStorage
from .reporter import ReconciliationReporter

__all__ = [
    # Models
    'EstimationUnit',
    'TicketReconciliation',
    'WorkMetrics',
    'EstimationPattern',
    'TeamMetrics',
    'ReconciliationReport',
    
    # Collectors
    'GitMetricsCollector',
    'TicketDataCollector',
    'WorkMetricsCollector',
    
    # Analyzers
    'ReconciliationAnalyzer',
    'PatternDetector',
    'AccuracyCalculator',
    
    # Storage
    'ReconciliationStorage',
    
    # Reporting
    'ReconciliationReporter'
]

__version__ = "1.0.0"