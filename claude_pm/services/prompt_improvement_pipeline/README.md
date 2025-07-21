# Prompt Improvement Pipeline

This directory contains the refactored prompt improvement pipeline module, organized into focused sub-modules for better maintainability and clarity.

## Module Structure

### Core Components

- **`__init__.py`** (~200 lines)
  - Main `PromptImprovementPipeline` facade class
  - High-level interface for pipeline operations
  - Coordinates all sub-modules

- **`types.py`** (~72 lines)
  - Data types and enumerations
  - `PipelineConfig`, `PipelineExecution`, `PipelineResults`
  - `PipelineStage` and `PipelineStatus` enums

- **`execution_manager.py`** (~308 lines)
  - Pipeline execution orchestration
  - Stage coordination and error handling
  - Active execution management

- **`stage_handlers.py`** (~358 lines)
  - Individual pipeline stage implementations
  - Correction analysis, pattern detection, improvement generation
  - Validation, deployment, and monitoring setup

- **`analytics.py`** (~200 lines)
  - Performance metrics calculation
  - Trend analysis and recommendations
  - Report generation

- **`storage.py`** (~150 lines)
  - Data persistence operations
  - Execution and result storage
  - Archive management

- **`monitoring.py`** (~100 lines)
  - Real-time health monitoring
  - Status tracking and alerting
  - Health report generation

## Usage

```python
from claude_pm.services.prompt_improvement_pipeline import PromptImprovementPipeline

# Initialize pipeline
pipeline = PromptImprovementPipeline()

# Run full pipeline
results = await pipeline.run_full_pipeline(
    agent_types=['documentation', 'qa'],
    config=PipelineConfig(
        correction_analysis_days=30,
        auto_deployment_enabled=True
    )
)

# Check health
health = await pipeline.get_pipeline_health()

# Monitor specific execution
status = await pipeline.get_execution_status(execution_id)
```

## Backward Compatibility

The original `prompt_improvement_pipeline.py` file has been replaced with a backward compatibility stub that imports from this directory structure. All existing imports will continue to work with a deprecation warning.

## Dependencies

This module depends on:
- `claude_pm.services.correction_capture`
- `claude_pm.services.pattern_analyzer`
- `claude_pm.services.prompt_improver`
- `claude_pm.services.prompt_template_manager`
- `claude_pm.services.prompt_validator`

## Data Storage

Pipeline data is stored in:
- `~/.claude-pm/prompt_pipeline/executions/` - Execution records
- `~/.claude-pm/prompt_pipeline/results/` - Pipeline results
- `~/.claude-pm/prompt_pipeline/archives/` - Archived records

## Monitoring and Health

The pipeline includes built-in monitoring with configurable thresholds:
- Maximum active executions
- Minimum success rate
- Maximum average execution time
- Storage usage limits
- Recent failure thresholds

## Future Enhancements

Potential areas for future development:
- Real-time execution streaming
- Distributed execution support
- Advanced analytics and ML-based recommendations
- Integration with external monitoring systems
- Enhanced deployment strategies