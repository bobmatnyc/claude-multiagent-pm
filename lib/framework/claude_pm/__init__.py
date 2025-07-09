"""
Claude Multi-Agent Project Management Framework - Python Package

A comprehensive project management framework for AI-driven development
with integrated memory management and multi-agent orchestration.
"""

__version__ = "4.0.0"
__title__ = "Claude Multi-Agent PM Framework"
__description__ = "Claude Multi-Agent Project Management Framework for AI-driven orchestration"
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