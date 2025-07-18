# Test Fixtures

This directory contains test data, mock objects, and sample configurations used across the test suite.

## Organization

- **`/agents/`** - Mock agent configurations and prompts
- **`/projects/`** - Sample project structures for testing
- **`/data/`** - Test data files (JSON, YAML, etc.)

## Usage

```python
# Example: Using agent fixtures
from tests.fixtures.agents import mock_documentation_agent

def test_agent_loading():
    agent = mock_documentation_agent()
    assert agent.name == "Documentation Agent"
```

## Guidelines

1. Fixtures should be reusable across multiple tests
2. Keep fixtures minimal but representative
3. Document any special setup requirements
4. Version fixtures if they change significantly
5. Use factory functions for dynamic fixture generation

## Common Fixtures

### Agent Fixtures
- Mock agent configurations
- Sample agent prompts
- Agent hierarchy structures

### Project Fixtures
- Minimal project structures
- Complex multi-agent projects
- Projects with various configurations

### Data Fixtures
- Sample configuration files
- Test data for validation
- Mock API responses