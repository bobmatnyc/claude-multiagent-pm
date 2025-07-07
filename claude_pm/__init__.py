"""
Claude PM Framework - Python Package

A comprehensive project management framework for AI-driven development
with integrated memory management and multi-agent orchestration.
"""

__version__ = "3.1.0"
__title__ = "Claude PM Framework"
__description__ = "Multi-Agent Orchestration Framework for AI-driven project management"
__author__ = "Robert (Masa) Matsuoka"
__email__ = "masa@matsuoka.com"
__license__ = "MIT"

from .core.base_service import BaseService
from .core.service_manager import ServiceManager
from .services.health_monitor import HealthMonitorService
from .services.memory_service import MemoryCategory
from .services.project_service import ProjectService

__all__ = [
    "BaseService",
    "ServiceManager", 
    "HealthMonitorService",
    "MemoryCategory",
    "ProjectService",
]