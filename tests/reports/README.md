# Test Reports Directory

This directory contains generated test reports and artifacts. These files are not tracked in git.

## Directory Structure

- `coverage/` - Test coverage reports (HTML, XML, JSON)
- `results/` - Test execution results (JSON, XML, JUnit format)
- `validation/` - QA validation reports and artifacts

## Running Tests

Tests are configured via `tests/config/pytest.ini` and will automatically generate reports here.

```bash
# Run all tests with coverage
pytest

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m e2e

# Generate HTML coverage report
pytest --cov-report=html
```

## Viewing Reports

- Coverage HTML: Open `coverage/html/index.html` in a browser
- JUnit results: `results/junit.xml` (for CI/CD integration)
- Coverage XML: `coverage/coverage.xml` (for tools like Codecov)