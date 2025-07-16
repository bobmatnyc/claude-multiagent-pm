# Model Configuration System

The Claude PM Framework model configuration system provides production-ready default model assignments for different agent types, with comprehensive environment variable overrides and validation.

## Overview

This system implements the research findings for optimal model assignments:
- **Opus models**: For orchestrator and engineer agents (complex implementation tasks)
- **Sonnet models**: For documentation, QA, research, ops, security, and data engineer agents

## Quick Start

```python
from claude_pm.config import get_model_for_agent, validate_configuration

# Get model assignment for an agent
model_id = get_model_for_agent("engineer")  # Returns: claude-3-opus-20240229

# Validate configuration
validation = validate_configuration()
print(f"Configuration valid: {validation['overall_valid']}")
```

## Default Model Assignments

### Opus Models (High Capability, Complex Tasks)
- `orchestrator`: Project orchestration and coordination
- `engineer`: Code implementation and development
- `architecture`: System architecture design
- `performance`: Performance optimization
- `integration`: Complex system integration
- `backend`: Server-side logic implementation
- `machine_learning`: ML model development
- `data_science`: Complex data analysis

### Sonnet Models (Balanced Performance)
- `documentation`: Documentation analysis and generation
- `qa`: Quality assurance and testing
- `research`: Investigation and analysis
- `ops`: Operations and deployment
- `security`: Security analysis and auditing
- `data_engineer`: Data pipeline management
- `ticketing`: Ticket management
- `version_control`: Git operations
- `ui_ux`: User interface design
- `frontend`: Frontend development
- `database`: Database management
- `api`: API development
- `testing`: Test automation
- `monitoring`: System monitoring
- `analytics`: Data analytics
- `deployment`: Deployment automation
- And many more...

## Environment Variable Overrides

### Global Override
```bash
# Override all agents to use Sonnet
export CLAUDE_PM_MODEL_OVERRIDE=claude-3-5-sonnet-20241022
```

### Agent-Specific Overrides
```bash
# Override specific agents
export CLAUDE_PM_MODEL_ENGINEER=claude-3-opus-20240229
export CLAUDE_PM_MODEL_DOCUMENTATION=claude-3-5-sonnet-20241022
export CLAUDE_PM_MODEL_QA=claude-3-5-sonnet-20241022
```

### Configuration Settings
```bash
# Framework settings
export CLAUDE_PM_DEPLOYMENT_ENV=production
export CLAUDE_PM_MODEL_CACHE_ENABLED=true
export CLAUDE_PM_MODEL_CACHE_TTL=600
export CLAUDE_PM_MODEL_VALIDATION_ENABLED=true
export CLAUDE_PM_MODEL_FALLBACK_ENABLED=true
export CLAUDE_PM_MODEL_DEBUG_LOGGING=false
```

## Available Models

- `claude-3-opus-20240229`: Highest capability, slower, higher cost
- `claude-3-5-sonnet-20241022`: Balanced performance (recommended default)
- `claude-sonnet-4-20250514`: Enhanced capabilities, medium cost
- `claude-3-haiku-20240307`: Fastest, lowest cost, basic capabilities

## Configuration Components

### 1. Default Model Configuration (`default_model_config.py`)
- Production-ready default assignments
- Model capability validation
- Environment variable integration

### 2. Environment Defaults (`model_env_defaults.py`)
- Environment variable management
- Deployment-specific settings
- Configuration templates

### 3. System Agent Configuration (`system_agent_config.py`)
- Agent metadata with model preferences
- Capability and specialization mapping
- Performance requirements

### 4. Integrated Configuration (`model_configuration.py`)
- Unified configuration interface
- Priority-based model selection
- Comprehensive validation

### 5. Framework Initialization (`framework_initialization.py`)
- Startup integration
- Health checks
- Service container registration

## Usage Examples

### Basic Usage
```python
from claude_pm.config import get_model_for_agent

# Get model for different agents
orchestrator_model = get_model_for_agent("orchestrator")
engineer_model = get_model_for_agent("engineer")
documentation_model = get_model_for_agent("documentation")
```

### Advanced Configuration
```python
from claude_pm.config import (
    get_integrated_model_config,
    validate_model_configuration,
    initialize_model_configuration_defaults
)

# Get full configuration manager
config = get_integrated_model_config()

# Get all agent models
all_models = config.get_all_agent_models()

# Validate configuration
validation = validate_model_configuration()

# Initialize defaults
init_results = initialize_model_configuration_defaults()
```

### Framework Initialization
```python
import asyncio
from claude_pm.config import initialize_framework_model_configuration

async def init_framework():
    status = await initialize_framework_model_configuration(
        validate_config=True,
        set_env_defaults=True,
        override_existing_env=False
    )
    
    print(f"Initialization successful: {status.success}")
    print(f"Agents configured: {status.agents_configured}")
    print(f"Environment variables set: {status.environment_variables_set}")

asyncio.run(init_framework())
```

### Generate Configuration Files
```python
from pathlib import Path
from claude_pm.config import get_integrated_model_config

config = get_integrated_model_config()

# Generate .env file and templates
output_dir = Path("./config_output")
files = config.generate_configuration_files(output_dir)

print(f"Generated files: {list(files.keys())}")
```

## API Reference

See individual module docstrings for detailed API documentation:

- `default_model_config.py`: Default model assignments
- `model_env_defaults.py`: Environment variable management
- `system_agent_config.py`: System agent configuration
- `model_configuration.py`: Integrated configuration interface
- `framework_initialization.py`: Framework startup integration