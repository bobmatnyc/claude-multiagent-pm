"""
Claude Multi-Agent Project Management Framework - Python Package

A comprehensive project management framework for AI-driven development
with integrated memory management and multi-agent orchestration.
"""

# Load environment variables from .env file
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load .env file from project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, skip loading

# Check for deprecated editable installation
try:
    from .utils.deprecation import check_editable_installation
    check_editable_installation()  # Explicitly call the check
except ImportError:
    pass  # Deprecation module not available

# Load version dynamically from package.json/VERSION file
try:
    from .utils.version_loader import get_package_version
    __version__ = get_package_version()
except ImportError:
    # Fallback if version_loader is not available
    __version__ = "1.4.6"
__title__ = "Claude Multi-Agent PM Framework"
__description__ = "Claude Multi-Agent Project Management Framework for AI-driven orchestration"
__author__ = "Robert (Masa) Matsuoka"
__email__ = "masa@matsuoka.com"
__license__ = "MIT"

from .core.base_service import BaseService
from .core.service_manager import ServiceManager
from .services.health_monitor import HealthMonitorService
from .services.project_service import ProjectService

__all__ = [
    "BaseService",
    "ServiceManager",
    "HealthMonitorService",
    "MemoryCategory",
    "ProjectService",
]
