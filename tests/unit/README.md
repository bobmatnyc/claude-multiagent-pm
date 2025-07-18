# Unit Tests

This directory contains unit tests for individual components of the Claude Multi-Agent PM framework.

## Organization

Tests are organized by module to mirror the source code structure:

- **`/agents/`** - Tests for individual agent implementations
- **`/services/`** - Tests for service modules (e.g., memory collector, prompt cache)
- **`/core/`** - Tests for core framework components
- **`/cli/`** - Tests for CLI command parsing and execution

## Guidelines

1. Each test file should correspond to a single source module
2. Tests should be isolated and not depend on external resources
3. Use mocking for dependencies
4. Tests should be fast (< 1 second per test)
5. Follow naming convention: `test_<module_name>.py`

## Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run tests for a specific module
pytest tests/unit/agents/
pytest tests/unit/services/

# Run with verbose output
pytest tests/unit/ -v
```