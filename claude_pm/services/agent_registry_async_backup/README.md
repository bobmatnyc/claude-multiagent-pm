# Agent Registry Async Backup Module

This directory contains the refactored agent registry async backup implementation, split from the original 2,050-line monolithic file into a well-organized modular structure.

## Module Structure

### Core Components

- **`__init__.py`** (~250 lines) - Main AgentRegistry facade class that orchestrates all components
- **`models.py`** (~50 lines) - Data models including AgentMetadata dataclass
- **`discovery.py`** (~200 lines) - Agent discovery and file system scanning functionality
- **`metadata_extractor.py`** (~300 lines) - Metadata extraction from agent files
- **`model_configuration.py`** (~200 lines) - Model selection and configuration logic
- **`classification.py`** (~250 lines) - Agent type classification and complexity assessment
- **`validation.py`** (~200 lines) - Agent validation system
- **`query_api.py`** (~300 lines) - Search and query methods for agents
- **`analytics.py`** (~350 lines) - Statistics and analytics functionality
- **`sync_wrappers.py`** (~120 lines) - Synchronous method wrappers for async operations
- **`health_check.py`** (~160 lines) - Health monitoring system

## Key Features

### Agent Discovery
- Two-tier hierarchy discovery (user → system)
- Directory scanning with performance optimization
- Agent metadata collection and caching
- Support for 35+ specialized agent types beyond core 9

### Model Integration
- Automatic model selection based on agent complexity
- Model configuration extraction from agent files
- Validation and recommendations for model usage
- Integration with ModelSelector service

### Performance Optimization
- SharedPromptCache integration for 99.7% performance improvement
- Discovery result caching with configurable TTL
- Efficient file scanning and metadata extraction

### Validation and Health
- Comprehensive agent validation with scoring
- Framework compatibility checks
- Health monitoring with detailed diagnostics
- Error handling and recovery

## Usage

The module maintains full backward compatibility through the stub file `agent_registry_async_backup.py`:

```python
from claude_pm.services.agent_registry_async_backup import AgentRegistry, AgentMetadata

# Create registry instance
registry = AgentRegistry()

# Discover agents
agents = await registry.discover_agents()

# Query agents
documentation_agents = await registry.list_agents(agent_type='documentation')
specialized_agents = await registry.get_specialized_agents('ui_ux')

# Get analytics
stats = await registry.get_enhanced_registry_stats()
```

## Architecture

The refactored architecture follows single-responsibility principle:

1. **Discovery Layer** - Handles file system traversal and agent discovery
2. **Extraction Layer** - Extracts and processes agent metadata
3. **Classification Layer** - Classifies agents by type and complexity
4. **Validation Layer** - Validates agent configurations
5. **Query Layer** - Provides search and filtering capabilities
6. **Analytics Layer** - Generates statistics and reports
7. **Health Layer** - Monitors system health

## Migration Notes

This refactoring was completed as part of EP-0043 to improve code maintainability. The original 2,050-line file has been split into focused modules while maintaining 100% API compatibility.