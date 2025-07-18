# End-to-End Tests

This directory contains end-to-end tests that simulate complete user scenarios.

## Organization

- **`/installation/`** - Tests for NPM package installation and initial setup
- **`/deployment/`** - Tests for complete deployment scenarios
- **`/workflows/`** - Tests for full user workflows from start to finish
- **`/version-specific/`** - Tests targeting specific framework versions

## Guidelines

1. E2E tests simulate real user interactions
2. Tests may create temporary directories and projects
3. All created resources must be cleaned up
4. Tests can be slower but should provide comprehensive validation
5. Include tests for error scenarios and edge cases

## Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/

# Run specific scenario tests
pytest tests/e2e/installation/
pytest tests/e2e/workflows/

# Run with detailed output
pytest tests/e2e/ -v --tb=short

# Run version-specific tests
pytest tests/e2e/version-specific/ -k "v0.7"
```

## Special Considerations

- Installation tests may require network access
- Some tests may need to be run in isolated environments
- Version-specific tests help ensure backward compatibility