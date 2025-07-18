# Integration Tests

This directory contains integration tests that verify multiple components working together.

## Organization

- **`/agents/`** - Tests for agent interactions, delegation, and communication
- **`/services/`** - Tests for service integrations (e.g., memory + prompt cache)
- **`/deployment/`** - Tests for deployment workflows and template processing
- **`/workflows/`** - Tests for multi-step workflows combining multiple features

## Guidelines

1. Integration tests can use real file I/O and network operations
2. Tests should clean up any created resources
3. Use fixtures for common test scenarios
4. Tests can take longer than unit tests but should complete within 30 seconds
5. Test realistic scenarios that users might encounter

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration category
pytest tests/integration/agents/
pytest tests/integration/workflows/

# Run with markers
pytest tests/integration/ -m "not slow"
```