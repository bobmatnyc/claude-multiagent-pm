# End-to-End Tests

This directory contains comprehensive end-to-end tests that validate complete user scenarios and framework functionality.

## Infrastructure Overview

The E2E test infrastructure provides a robust foundation for testing all aspects of the Claude PM framework:

- **Base Test Class**: `BaseE2ETest` provides common setup/teardown and utilities
- **Test Fixtures**: Pre-configured agents, prompts, and configurations
- **Mock System**: Comprehensive mocking for external dependencies
- **Data Generators**: Tools to generate test data for various scenarios

## Organization

### Core Directories
- **`/core/`** - Core functionality tests (agent discovery, orchestration, etc.)
- **`/fixtures/`** - Test fixtures and mock data
- **`/utils/`** - Test utilities and helpers

### Test Categories
- **`/installation/`** - Tests for NPM package installation and initial setup
- **`/deployment/`** - Tests for complete deployment scenarios
- **`/workflows/`** - Tests for full user workflows from start to finish
- **`/version-specific/`** - Tests targeting specific framework versions

## Quick Start

### Using the Base Test Class

```python
from tests.e2e.utils import BaseE2ETest

class TestMyFeature(BaseE2ETest):
    def test_feature(self):
        # Automatic setup/teardown handled by base class
        result = self.run_claude_pm(['init'])
        self.assert_command_success(result)
```

### Using Fixtures

```python
from tests.e2e.fixtures import AgentFixtures, ConfigFixtures

def test_with_fixtures(self):
    # Use pre-configured agent
    agent = AgentFixtures.documentation_agent()
    self.create_mock_agent(agent["name"], "project", agent["content"])
    
    # Use pre-configured config
    config = ConfigFixtures.base_config()
    self.create_test_config(config)
```

### Using Mock System

```python
from tests.e2e.utils import MockSystem

def test_with_mocks(self):
    mock_system = MockSystem()
    mock_system.setup()
    
    # All external dependencies are now mocked
    # Run your tests...
    
    mock_system.teardown()
```

## Guidelines

1. **Inherit from BaseE2ETest**: All E2E tests should inherit from the base class
2. **Use Fixtures**: Leverage pre-configured fixtures for consistency
3. **Mock External Services**: Never make real API calls or network requests
4. **Isolate Tests**: Each test runs in its own temporary directory
5. **Clean Resources**: Automatic cleanup is handled by the base class
6. **Document Complex Tests**: Add clear docstrings explaining test purpose
7. **Use Test Markers**: Apply appropriate pytest markers (@pytest.mark.core, etc.)

## Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/

# Run specific test categories
pytest tests/e2e/core/
pytest tests/e2e/workflows/

# Run tests by marker
pytest tests/e2e/ -m core
pytest tests/e2e/ -m "not slow"

# Run with coverage
pytest tests/e2e/ --cov=claude_pm --cov-report=html

# Run with detailed output
pytest tests/e2e/ -v --tb=short

# Run specific test file
pytest tests/e2e/core/test_agent_discovery_example.py
```

## Test Markers

- `@pytest.mark.core` - Core functionality tests
- `@pytest.mark.orchestration` - Orchestration flow tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests taking more than 5 seconds
- `@pytest.mark.requires_setup` - Tests requiring full framework setup
- `@pytest.mark.isolated` - Tests that must run in isolation

## Writing New E2E Tests

See `E2E_TESTING_GUIDELINES.md` for comprehensive guidelines on:
- Test structure and naming conventions
- Using fixtures and utilities
- Mocking strategies
- Performance considerations
- Best practices

## Special Considerations

- Installation tests may require network access (use mocks)
- Some tests may need to be run in isolated environments
- Version-specific tests help ensure backward compatibility
- Use test data generators for consistent test data
- Monitor test execution time and mark slow tests appropriately

## Example Test

See `core/test_agent_discovery_example.py` for a complete example demonstrating:
- Base class usage
- Fixture integration
- Mock system usage
- Proper test structure
- Assertion patterns