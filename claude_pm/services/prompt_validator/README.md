# Prompt Validator Module Structure

This directory contains the refactored prompt validation framework, organized into focused modules for better maintainability and clarity.

## Module Organization

### Core Components

- **`models.py`** (~80 lines)
  - Data classes: `TestScenario`, `TestResult`, `ABTestResult`, `ValidationReport`
  - Enums: `TestType`, `TestStatus`
  - Core data structures used throughout the system

- **`test_execution.py`** (~180 lines)
  - `TestExecutor` class for running individual and concurrent tests
  - Test execution logic and result collection
  - Active test tracking and status management

- **`ab_testing.py`** (~200 lines)
  - `ABTester` class for A/B testing functionality
  - Statistical significance calculation
  - Winner determination and improvement metrics

- **`regression_testing.py`** (~100 lines)
  - `RegressionTester` class for regression detection
  - Performance degradation analysis
  - Version comparison functionality

- **`performance_benchmarking.py`** (~150 lines)
  - `PerformanceBenchmarker` class for performance testing
  - Iteration-based benchmarking
  - Performance metrics and ratings

- **`scenario_management.py`** (~200 lines)
  - `ScenarioManager` class for test scenario creation
  - Automated scenario generation
  - Agent-specific scenario templates

- **`analytics.py`** (~200 lines)
  - `AnalyticsEngine` class for trend analysis
  - Test performance analytics
  - Quality insights generation

- **`storage.py`** (~150 lines)
  - `StorageManager` class for data persistence
  - JSON-based storage for scenarios, results, and reports
  - Data export/import functionality

- **`utils.py`** (~50 lines)
  - Utility functions for ID generation
  - Recommendation generation
  - Metrics formatting

- **`__init__.py`** (~200 lines)
  - Main `PromptValidator` facade class
  - Public API exports
  - Convenience functions

## Usage

The module maintains full backward compatibility. All existing code using `prompt_validator` will continue to work:

```python
from claude_pm.services.prompt_validator import PromptValidator

# Or using the backward compatibility stub
from claude_pm.services import prompt_validator
```

## Architecture

The refactored structure follows these principles:

1. **Single Responsibility**: Each module has a focused purpose
2. **Dependency Management**: Clear dependencies between modules
3. **Testability**: Smaller modules are easier to test
4. **Maintainability**: Related functionality is grouped together

## Module Dependencies

```
__init__.py (Main Facade)
    ├── models.py (Data structures)
    ├── test_execution.py
    ├── ab_testing.py
    │   └── test_execution.py
    ├── regression_testing.py
    │   └── ab_testing.py
    ├── performance_benchmarking.py
    │   └── test_execution.py
    ├── scenario_management.py
    │   └── models.py
    ├── analytics.py
    │   └── models.py
    ├── storage.py
    │   └── models.py
    └── utils.py
        └── models.py
```

## Testing

Each module can be tested independently:

```bash
python -m pytest tests/unit/services/prompt_validator/test_models.py
python -m pytest tests/unit/services/prompt_validator/test_ab_testing.py
# etc.
```

## Future Enhancements

The modular structure makes it easy to:
- Add new test types
- Implement different storage backends
- Extend analytics capabilities
- Add more sophisticated statistical tests