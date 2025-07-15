"""Core Claude PM Framework components."""

from .base_service import BaseService
from .base_agent import BaseAgent
from .service_manager import ServiceManager
from .config import Config
from .logging_config import setup_logging
from .enforcement import (
    EnforcementEngine,
    DelegationEnforcer,
    AgentCapabilityManager,
    ViolationMonitor,
    Agent,
    Action,
    AgentPermissions,
    ConstraintViolation,
    ValidationResult,
    AgentType,
    ActionType,
    ViolationSeverity,
    FileCategory,
    get_enforcement_engine,
    enforce_file_access,
    validate_agent_action,
)

def validate_core_system():
    """Validate core system health and operational stability."""
    try:
        # Test basic imports
        from .service_manager import ServiceManager
        from .config import Config
        from .base_service import BaseService
        
        # Test service manager initialization
        manager = ServiceManager()
        
        # Test configuration system
        config = Config()
        
        print("✅ Core system validation passed")
        print(f"  - Service manager: {manager}")
        print(f"  - Configuration: {config}")
        print(f"  - Base services: {BaseService}")
        
        return True
        
    except Exception as e:
        print(f"❌ Core system validation failed: {e}")
        return False

__all__ = [
    "BaseService",
    "BaseAgent",
    "ServiceManager",
    "Config",
    "setup_logging",
    "EnforcementEngine",
    "DelegationEnforcer",
    "AgentCapabilityManager",
    "ViolationMonitor",
    "Agent",
    "Action",
    "AgentPermissions",
    "ConstraintViolation",
    "ValidationResult",
    "AgentType",
    "ActionType",
    "ViolationSeverity",
    "FileCategory",
    "get_enforcement_engine",
    "enforce_file_access",
    "validate_agent_action",
    "validate_core_system",
]
