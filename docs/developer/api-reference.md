# API Reference

## Overview

This document provides a comprehensive API reference for the Claude PM Framework's core modules and services. The framework is organized into several key namespaces, each serving a specific purpose in the multi-agent orchestration system.

## Core Modules

### claude_pm.core

The core module contains fundamental classes and utilities used throughout the framework.

#### AgentRegistry

```python
from claude_pm.core.agent_registry import AgentRegistry

class AgentRegistry:
    """Dynamic agent discovery and management system."""
    
    def __init__(self, prompt_cache=None):
        """Initialize the agent registry.
        
        Args:
            prompt_cache: Optional SharedPromptCache instance
        """
    
    def listAgents(self, 
                   scope='all',
                   specializations=None,
                   task_capability=None,
                   include_tracking=False) -> Dict[str, AgentMetadata]:
        """List available agents with filtering options.
        
        Args:
            scope: 'all', 'project', 'user', or 'system'
            specializations: List of required specializations
            task_capability: Specific task capability filter
            include_tracking: Include modification timestamps
            
        Returns:
            Dictionary mapping agent IDs to metadata
        """
    
    def selectOptimalAgent(self, agents: Dict, task_type: str) -> Agent:
        """Select the best agent for a given task.
        
        Args:
            agents: Dictionary of available agents
            task_type: Type of task to perform
            
        Returns:
            Selected Agent instance
        """
    
    def health_check(self) -> Dict[str, Any]:
        """Perform registry health check.
        
        Returns:
            Health status dictionary
        """
```

#### BaseService

```python
from claude_pm.core.base_service import BaseService

class BaseService:
    """Base class for all framework services."""
    
    async def initialize(self) -> None:
        """Initialize the service.
        
        Must be called before using the service.
        """
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
```

#### ConfigService

```python
from claude_pm.core.config_service import ConfigService

class ConfigService(BaseService):
    """Configuration management service."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
    
    def load_from_file(self, filepath: str) -> None:
        """Load configuration from file.
        
        Args:
            filepath: Path to configuration file
        """
```

### claude_pm.services

The services module contains specialized services that provide specific functionality.

#### SharedPromptCache

```python
from claude_pm.services.shared_prompt_cache import SharedPromptCache

class SharedPromptCache:
    """High-performance caching system for agent prompts."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize cache.
        
        Args:
            max_size: Maximum cache entries
            ttl: Time-to-live in seconds
        """
    
    def get(self, key: str) -> Optional[str]:
        """Retrieve cached prompt.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
    
    def set(self, key: str, value: str) -> None:
        """Cache a prompt.
        
        Args:
            key: Cache key
            value: Prompt content
        """
    
    def invalidate(self, pattern: str = None) -> int:
        """Invalidate cache entries.
        
        Args:
            pattern: Optional glob pattern
            
        Returns:
            Number of entries invalidated
        """
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache performance metrics
        """
```

#### HealthMonitor

```python
from claude_pm.services.health_monitor import HealthMonitor

class HealthMonitor(BaseService):
    """System health monitoring service."""
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check.
        
        Returns:
            Health status for all components
        """
    
    def check_framework_health(self) -> Dict[str, Any]:
        """Check framework-specific health.
        
        Returns:
            Framework health metrics
        """
    
    async def monitor_performance(self, 
                                  duration: int = 60) -> Dict[str, Any]:
        """Monitor system performance.
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            Performance metrics
        """
```

#### TemplateManager

```python
from claude_pm.services.template_manager import TemplateManager

class TemplateManager(BaseService):
    """Template processing and management service."""
    
    def process_template(self, 
                        template_path: str,
                        variables: Dict[str, Any]) -> str:
        """Process template with variables.
        
        Args:
            template_path: Path to template file
            variables: Template variables
            
        Returns:
            Processed template content
        """
    
    def get_available_templates(self) -> List[str]:
        """List available templates.
        
        Returns:
            List of template names
        """
```

### claude_pm.agents

The agents module contains agent-related functionality.

#### BaseAgent

```python
from claude_pm.agents.base_agent import BaseAgent

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, agent_id: str, metadata: Dict[str, Any]):
        """Initialize agent.
        
        Args:
            agent_id: Unique agent identifier
            metadata: Agent metadata
        """
    
    async def execute(self, 
                     task: Dict[str, Any],
                     context: Dict[str, Any]) -> AgentResult:
        """Execute agent task.
        
        Args:
            task: Task specification
            context: Execution context
            
        Returns:
            AgentResult with execution outcome
        """
    
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities.
        
        Returns:
            List of capability identifiers
        """
```

#### AgentResult

```python
from claude_pm.agents import AgentResult

@dataclass
class AgentResult:
    """Result of agent execution."""
    
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
```

### claude_pm.orchestration

The orchestration module handles multi-agent coordination.

#### PMOrchestrator

```python
from claude_pm.orchestration import PMOrchestrator

class PMOrchestrator:
    """Main orchestration coordinator."""
    
    async def orchestrate(self, 
                         workflow: Dict[str, Any]) -> OrchestratorResult:
        """Orchestrate multi-agent workflow.
        
        Args:
            workflow: Workflow specification
            
        Returns:
            OrchestratorResult with outcomes
        """
    
    async def delegate_task(self,
                           agent_id: str,
                           task: Dict[str, Any],
                           timeout: Optional[int] = None) -> AgentResult:
        """Delegate task to specific agent.
        
        Args:
            agent_id: Target agent ID
            task: Task specification
            timeout: Optional timeout in seconds
            
        Returns:
            AgentResult from execution
        """
```

#### TaskTool

```python
from claude_pm.orchestration import TaskTool

class TaskTool:
    """Subprocess creation and management."""
    
    @staticmethod
    async def create_subprocess(agent_type: str,
                               task_description: str,
                               context: Dict[str, Any]) -> SubprocessResult:
        """Create agent subprocess.
        
        Args:
            agent_type: Type of agent to spawn
            task_description: Task description
            context: Execution context
            
        Returns:
            SubprocessResult with outcome
        """
```

### claude_pm.utils

Utility functions and helpers.

#### TaskToolHelper

```python
from claude_pm.utils.task_tool_helper import TaskToolHelper

class TaskToolHelper:
    """Helper functions for Task Tool operations."""
    
    @staticmethod
    def format_delegation(agent_nickname: str,
                         task: str,
                         context: Dict[str, Any]) -> str:
        """Format standard delegation prompt.
        
        Args:
            agent_nickname: Agent's short name
            task: Task description
            context: Task context
            
        Returns:
            Formatted delegation prompt
        """
    
    @staticmethod
    def parse_agent_result(output: str) -> Dict[str, Any]:
        """Parse agent output.
        
        Args:
            output: Raw agent output
            
        Returns:
            Parsed result dictionary
        """
```

#### Performance

```python
from claude_pm.utils.performance import PerformanceMonitor

class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    def __init__(self):
        """Initialize performance monitor."""
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Timer ID
        """
    
    def end_timer(self, timer_id: str) -> float:
        """End timing and get duration.
        
        Args:
            timer_id: Timer ID from start_timer
            
        Returns:
            Duration in seconds
        """
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics.
        
        Returns:
            Performance statistics
        """
```

## CLI Commands

### claude_pm.cli

Main CLI entry points and command handlers.

```python
from claude_pm.cli import cli_main

def cli_main(args: List[str] = None) -> int:
    """Main CLI entry point.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success)
    """
```

### claude_pm.cmpm_commands

Productivity commands for the cmpm interface.

```python
from claude_pm.cmpm_commands import (
    push_command,
    deploy_command,
    publish_command
)

def push_command(args: argparse.Namespace) -> int:
    """Execute push workflow.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """

def deploy_command(args: argparse.Namespace) -> int:
    """Execute deployment workflow.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """

def publish_command(args: argparse.Namespace) -> int:
    """Execute publication workflow.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
```

## Environment Variables

### Core Configuration

- `CLAUDE_PM_CONFIG_PATH`: Path to configuration file
- `CLAUDE_PM_LOG_LEVEL`: Logging level (debug, info, warning, error)
- `CLAUDE_PM_DEBUG`: Enable debug mode (true/false)

### API Keys

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

### Performance

- `CLAUDE_PM_CACHE_ENABLED`: Enable caching (true/false)
- `CLAUDE_PM_CACHE_TTL`: Cache time-to-live in seconds
- `CLAUDE_PM_MAX_CONCURRENT_AGENTS`: Maximum concurrent agents

### Model Configuration

- `CLAUDE_PM_DEFAULT_MODEL`: Default AI model
- `CLAUDE_PM_TEMPERATURE`: Model temperature (0.0-1.0)
- `CLAUDE_PM_MAX_TOKENS`: Maximum tokens per request

## Error Handling

### Exception Classes

```python
from claude_pm.exceptions import (
    FrameworkError,
    AgentNotFoundError,
    TaskTimeoutError,
    ConfigurationError,
    ServiceError
)

class FrameworkError(Exception):
    """Base exception for framework errors."""

class AgentNotFoundError(FrameworkError):
    """Raised when requested agent is not found."""

class TaskTimeoutError(FrameworkError):
    """Raised when task execution times out."""

class ConfigurationError(FrameworkError):
    """Raised for configuration issues."""

class ServiceError(FrameworkError):
    """Raised for service-related errors."""
```

### Error Context

All framework exceptions include contextual information:

```python
try:
    result = await orchestrator.delegate_task(agent_id, task)
except AgentNotFoundError as e:
    print(f"Agent error: {e}")
    print(f"Agent ID: {e.agent_id}")
    print(f"Available agents: {e.available_agents}")
```

## Hooks and Extensions

### Agent Hooks

```python
from claude_pm.hooks import AgentHooks

class CustomAgentHooks(AgentHooks):
    """Custom agent lifecycle hooks."""
    
    async def pre_execute(self, agent: BaseAgent, task: Dict) -> Dict:
        """Called before agent execution.
        
        Args:
            agent: Agent instance
            task: Task specification
            
        Returns:
            Modified task specification
        """
    
    async def post_execute(self, agent: BaseAgent, 
                          result: AgentResult) -> AgentResult:
        """Called after agent execution.
        
        Args:
            agent: Agent instance
            result: Execution result
            
        Returns:
            Modified result
        """
```

### Service Extensions

```python
from claude_pm.extensions import ServiceExtension

class CustomServiceExtension(ServiceExtension):
    """Custom service extension."""
    
    def register(self, service_manager: ServiceManager) -> None:
        """Register extension with service manager.
        
        Args:
            service_manager: Framework service manager
        """
```

---

*For more examples and usage patterns, see the source code and test files.*