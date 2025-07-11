# Claude PM Framework - Testing Guide

## Overview

This document provides comprehensive testing guidelines for the Claude PM Framework, including CLI testing, unit testing, integration testing, and CI/CD integration. The framework uses pytest as the primary testing framework with extensive CLI testing capabilities.

## Table of Contents

- [Testing Architecture](#testing-architecture)
- [CLI Testing](#cli-testing)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Test Markers and Categories](#test-markers-and-categories)
- [Coverage and Reporting](#coverage-and-reporting)
- [CI/CD Integration](#ci-cd-integration)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Testing Architecture

The Claude PM Framework follows a comprehensive testing architecture that includes:

### Test Types

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **CLI Tests** - Test command-line interface functionality
4. **End-to-End Tests** - Test complete workflows
5. **Performance Tests** - Test system performance and scalability

### Test Structure

```
tests/
├── test_claude_pm_cli.py              # CLI command testing
├── test_claude_pm_cli_integration.py  # CLI integration tests
├── test_claude_pm_cli_fixtures.py     # CLI test fixtures
├── test_claude_pm_cli_runner.py       # CLI test runner utilities
├── test_*.py                          # Component-specific tests
└── conftest.py                        # Global test configuration
```

## CLI Testing

### CLI Testing Architecture

The Claude PM Framework includes comprehensive CLI testing capabilities that test both the command-line interface and the underlying framework functionality. The CLI testing architecture consists of several key components:

#### Test Files for CLI Testing

The framework includes specialized test files for CLI functionality:

- **`test_claude_pm_cli.py`** - Main CLI command tests (29 comprehensive tests)
- **`test_claude_pm_cli_integration.py`** - CLI integration tests with services
- **`test_claude_pm_cli_fixtures.py`** - Shared fixtures for CLI testing
- **`test_claude_pm_cli_runner.py`** - CLI test runner utilities and helpers

#### CLI Test Categories

1. **Command Testing** - Tests individual CLI commands
2. **Integration Testing** - Tests CLI integration with framework services
3. **Fixture Testing** - Tests shared testing utilities
4. **Runner Testing** - Tests CLI execution and process management

#### Test Organization

The CLI tests follow a class-based organization pattern:

```python
class TestClaudePMCLI:
    """Main CLI command tests."""
    
    def test_health_command(self):
        """Test health command functionality."""
        pass
    
    def test_service_commands(self):
        """Test service management commands."""
        pass

class TestCLIIntegration:
    """CLI integration tests."""
    
    @pytest.mark.integration
    def test_cli_service_integration(self):
        """Test CLI integration with services."""
        pass
```

### Claude PM Test Command

The framework provides a unified `claude-pm test` command that integrates with the existing pytest configuration and provides extensive testing capabilities:

```bash
# Run all tests
claude-pm test

# Run specific test categories
claude-pm test --unit
claude-pm test --integration

# Run with coverage
claude-pm test --coverage

# Run with watch mode (auto-rerun on file changes)
claude-pm test --watch

# Run specific test patterns
claude-pm test --pattern "test_cli*"
claude-pm test --pattern "test_memory*"

# Run with HTML coverage report
claude-pm test --coverage --html

# Run tests in parallel
claude-pm test --parallel --workers 8

# Run with verbose output
claude-pm test --verbose

# Stop on first failure
claude-pm test --failfast

# Pass arguments directly to pytest
claude-pm test -- --pdb
claude-pm test -- -k "test_health"
```

### CLI Test Options

The `claude-pm test` command supports all major pytest options:

#### Test Categories
- `--unit` - Run unit tests only (@pytest.mark.unit)
- `--integration` - Run integration tests only (@pytest.mark.integration)
- `--slow` - Include slow tests (normally excluded)
- `--mem0ai` - Run mem0AI integration tests

#### Output and Reporting
- `--coverage` - Generate coverage reports
- `--html` - Generate HTML coverage report
- `--xml` - Generate XML coverage report
- `--json` - Output results in JSON format
- `--verbose` - Verbose test output
- `--quiet` - Minimal output

#### Test Selection
- `--pattern PATTERN` - Run tests matching pattern
- `--module MODULE` - Run tests from specific module
- `--function FUNCTION` - Run specific test function
- `--marker MARKER` - Run tests with specific marker

#### Development Options
- `--watch` - Watch for file changes and re-run tests
- `--failfast` - Stop on first failure
- `--lf` - Run last failed tests only
- `--cache-clear` - Clear pytest cache

### CLI Testing Examples

```bash
# Development workflow
claude-pm test --unit --coverage --watch

# CI/CD pipeline
claude-pm test --coverage --xml --quiet

# Debug specific CLI functionality
claude-pm test --verbose --pattern "test_health_command"

# Integration testing
claude-pm test --integration --mem0ai --slow

# Performance testing
claude-pm test --marker performance --verbose
```

## Running Tests

### Using Claude PM CLI

The recommended way to run tests is through the `claude-pm test` command:

```bash
# Quick test run
claude-pm test

# Full test suite with coverage
claude-pm test --coverage --html

# Development mode
claude-pm test --unit --watch
```

### Using Make Commands

The framework provides Make targets for testing:

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run tests with coverage
make test-cov

# Run mem0AI integration tests
make test-mem0ai
```

### Direct pytest Usage

You can also run pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_pm --cov-report=html

# Run specific test file
pytest tests/test_claude_pm_cli.py

# Run with markers
pytest -m "unit and not slow"
```

## Test Organization

### Test Files Structure

Tests are organized by functionality and component:

```python
# tests/test_claude_pm_cli.py
class TestClaudePMCLI:
    """Test suite for Claude PM CLI commands."""
    
    def test_health_command(self):
        """Test health command functionality."""
        pass
    
    def test_service_commands(self):
        """Test service management commands."""
        pass

# tests/test_claude_pm_cli_integration.py
class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    @pytest.mark.integration
    def test_cli_service_integration(self):
        """Test CLI integration with services."""
        pass
```

### Test Fixtures

Common test fixtures are defined in `test_claude_pm_cli_fixtures.py`:

```python
@pytest.fixture
def temp_project_dir():
    """Create temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_claude_pm_config():
    """Mock Claude PM configuration for testing."""
    return {
        "claude_pm_path": "/tmp/test-claude-pm",
        "managed_path": "/tmp/test-managed",
        "mem0ai_host": "localhost",
        "mem0ai_port": 8002
    }

@pytest.fixture
def cli_runner():
    """CLI test runner with proper setup."""
    from click.testing import CliRunner
    return CliRunner()
```

## Test Markers and Categories

### Available Markers

The framework uses pytest markers to categorize tests:

```python
# Unit tests - fast, isolated tests
@pytest.mark.unit
def test_config_validation():
    pass

# Integration tests - test component interactions
@pytest.mark.integration
def test_service_integration():
    pass

# Performance tests - test system performance
@pytest.mark.slow
def test_performance_benchmark():
    pass

# Slow tests - tests that take significant time
@pytest.mark.slow
def test_large_dataset_processing():
    pass

# Memory tests - tests requiring mem0AI service
@pytest.mark.mem0ai
def test_memory_service_integration():
    pass

# Health tests - health monitoring tests
@pytest.mark.health
def test_health_monitoring():
    pass
```

### Marker Configuration

Markers are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "mem0ai: marks tests that require mem0ai service",
    "health: marks tests for health monitoring"
]
```

## Coverage and Reporting

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.coverage.run]
branch = true
source = ["claude_pm"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/venv/*",
    "*/.venv/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "@(abc\\.)?abstractmethod"
]
show_missing = true
precision = 2
```

### Coverage Reports

Generate different types of coverage reports:

```bash
# Terminal coverage report
claude-pm test --coverage

# HTML coverage report
claude-pm test --coverage --html

# XML coverage report (for CI/CD)
claude-pm test --coverage --xml

# Combined coverage report
claude-pm test --coverage --html --xml
```

Coverage reports are generated in:
- HTML: `coverage_html_report/`
- XML: `coverage.xml`
- Terminal: stdout

## CI/CD Integration

### GitHub Actions Integration

The framework includes full GitHub Actions integration for automated testing. Here's the recommended workflow configuration:

```yaml
name: Claude PM Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install-dev
    
    - name: Run unit tests
      run: |
        claude-pm test --unit --coverage --xml --quiet
    
    - name: Run integration tests
      run: |
        claude-pm test --integration --quiet
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results-${{ matrix.python-version }}
        path: |
          coverage.xml
          coverage_html_report/
          
  integration:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        make install-dev
    
    - name: Run comprehensive tests
      run: |
        claude-pm test --integration --mem0ai --slow --coverage --html
    
    - name: Upload integration test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: integration-test-results
        path: coverage_html_report/
```

### CI/CD Best Practices

1. **Parallel Testing Strategy**
   ```yaml
   - name: Run tests in parallel
     run: |
       claude-pm test --parallel --workers 4 --coverage --xml
   ```

2. **Test Caching**
   ```yaml
   - name: Cache test dependencies
     uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements/dev.txt') }}
   ```

3. **Failure Handling**
   ```yaml
   - name: Run tests with failfast
     run: |
       claude-pm test --failfast --verbose
   ```

### Pre-commit Integration

Tests can be run as pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run Tests
        entry: claude-pm test --unit --quiet
        language: system
        pass_filenames: false
```

### Docker Testing

Run tests in containerized environment:

```dockerfile
# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .[dev]

CMD ["claude-pm", "test", "--coverage", "--xml"]
```

```bash
# Run tests in Docker
docker build -f Dockerfile.test -t claude-pm-tests .
docker run --rm claude-pm-tests
```

## Writing Tests

### Unit Test Example

```python
"""Unit tests for memory service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from claude_pm.services.memory_service import MemoryService
from claude_pm.core.config import Config

class TestMemoryService:
    """Test suite for MemoryService."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.get.return_value = "test-value"
        return config
    
    @pytest.fixture
    def memory_service(self, mock_config):
        """Create memory service instance for testing."""
        return MemoryService(config=mock_config)
    
    @pytest.mark.unit
    def test_service_initialization(self, memory_service):
        """Test service initialization."""
        assert memory_service is not None
        assert memory_service.config is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_service):
        """Test successful memory storage."""
        # Mock HTTP client
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {"id": "test-id"}
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Test memory storage
            result = await memory_service.store_memory("test-project", "test-content")
            
            assert result == "test-id"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_store_memory_validation_error(self, memory_service):
        """Test memory storage with invalid input."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            await memory_service.store_memory("", "content")
```

### Integration Test Example

```python
"""Integration tests for CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from claude_pm.cli import cli

class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    @pytest.fixture
    def cli_runner(self):
        """CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.integration
    def test_health_command_integration(self, cli_runner):
        """Test health command integration."""
        result = cli_runner.invoke(cli, ['health'])
        
        assert result.exit_code == 0
        assert "Health Dashboard" in result.output
        assert "Framework Services" in result.output
    
    @pytest.mark.integration
    @pytest.mark.mem0ai
    def test_memory_service_integration(self, cli_runner):
        """Test memory service integration."""
        result = cli_runner.invoke(cli, ['memory', 'search', 'test-query'])
        
        # Should handle gracefully if service is not available
        assert result.exit_code in [0, 1]  # Success or expected failure
```

### CLI Test Example

```python
"""CLI-specific tests."""
import pytest
import subprocess
from pathlib import Path

class TestCLICommands:
    """Test CLI commands directly."""
    
    @pytest.mark.cli
    def test_claude_pm_help(self):
        """Test claude-pm help command."""
        result = subprocess.run(
            ["claude-pm", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "Claude Multi-Agent Project Management" in result.stdout
    
    @pytest.mark.cli
    def test_claude_pm_version(self):
        """Test claude-pm version command."""
        result = subprocess.run(
            ["claude-pm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        assert result.returncode == 0
        assert "version" in result.stdout.lower()
    
    @pytest.mark.cli
    def test_claude_pm_test_command(self):
        """Test claude-pm test command."""
        result = subprocess.run(
            ["claude-pm", "test", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "test" in result.stdout.lower()
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Install package in development mode
pip install -e .

# Or use path setup
export PYTHONPATH="${PYTHONPATH}:/path/to/claude-multiagent-pm"
```

#### 2. Test Discovery Issues
```bash
# Error: No tests found
# Solution: Check test file naming
pytest --collect-only  # Show discovered tests

# Ensure test files follow naming convention
test_*.py or *_test.py
```

#### 3. Fixture Conflicts
```bash
# Error: Fixture conflicts
# Solution: Use unique fixture names
@pytest.fixture(name="unique_fixture_name")
def my_fixture():
    pass
```

#### 4. Async Test Issues
```bash
# Error: RuntimeError: This event loop is already running
# Solution: Use pytest-asyncio properly
pip install pytest-asyncio

# Mark async tests
@pytest.mark.asyncio
async def test_async_function():
    pass
```

#### 5. CLI Test Failures
```bash
# Error: CLI command not found
# Solution: Install package or use python -m
python -m claude_pm.cli health

# Or ensure package is installed
pip install -e .
```

#### 6. Test Watch Mode Issues
```bash
# Error: pytest-watch not installed
# Solution: Install development dependencies
pip install pytest-watch

# Or use the standard pytest watch alternative
claude-pm test --watch
```

#### 7. Parallel Testing Issues
```bash
# Error: pytest-xdist not installed
# Solution: Install parallel testing support
pip install pytest-xdist

# Run tests in parallel
claude-pm test --parallel --workers 4
```

### Debug Test Failures

```bash
# Run with verbose output
claude-pm test --verbose

# Run with pdb on failure
claude-pm test -- --pdb

# Run specific failing test
claude-pm test --pattern "test_failing_function"

# Show test execution details
claude-pm test --verbose -- --tb=long

# Debug CLI command execution
claude-pm test --pattern "test_cli*" --verbose

# Run tests with coverage and debugging
claude-pm test --coverage --verbose --pattern "test_specific_issue"

# Use pytest's built-in debugging
claude-pm test -- --lf --pdb  # Last failed with debugger
```

### Memory and Performance Issues

```bash
# Monitor memory usage
claude-pm test --verbose --profile

# Run tests with memory profiling
python -m memory_profiler -m pytest

# Check for memory leaks
valgrind --tool=memcheck python -m pytest
```

## Best Practices

### Test Organization

1. **Use Descriptive Test Names**
   ```python
   # Good
   def test_memory_service_stores_project_decision_successfully():
       pass
   
   # Avoid
   def test_memory():
       pass
   ```

2. **Group Related Tests**
   ```python
   class TestMemoryService:
       """All memory service tests."""
       
       class TestStore:
           """Memory storage tests."""
           pass
       
       class TestRetrieve:
           """Memory retrieval tests."""
           pass
   ```

3. **Use Fixtures for Setup**
   ```python
   @pytest.fixture
   def memory_service_with_data():
       """Memory service with test data."""
       service = MemoryService()
       service.store("test-data")
       return service
   ```

### Test Quality

1. **Test One Thing at a Time**
   ```python
   # Good
   def test_config_validation_requires_host():
       pass
   
   def test_config_validation_requires_port():
       pass
   
   # Avoid
   def test_config_validation():
       # Tests multiple things
       pass
   ```

2. **Use Meaningful Assertions**
   ```python
   # Good
   assert result.status == "success"
   assert result.message == "Memory stored successfully"
   
   # Avoid
   assert result  # Too generic
   ```

3. **Test Edge Cases**
   ```python
   def test_memory_service_handles_empty_content():
       pass
   
   def test_memory_service_handles_very_large_content():
       pass
   
   def test_memory_service_handles_special_characters():
       pass
   ```

### Performance Testing

1. **Use Benchmarks**
   ```python
   @pytest.mark.benchmark
   def test_memory_service_performance(benchmark):
       result = benchmark(memory_service.store, "test-content")
       assert result is not None
   ```

2. **Monitor Resource Usage**
   ```python
   import psutil
   
   def test_memory_usage_stays_reasonable():
       initial_memory = psutil.Process().memory_info().rss
       # Perform operation
       final_memory = psutil.Process().memory_info().rss
       assert final_memory - initial_memory < 50_000_000  # 50MB limit
   ```

### CI/CD Best Practices

1. **Fail Fast**
   ```yaml
   # Run quick tests first
   - name: Unit Tests
     run: claude-pm test --unit --failfast
   
   - name: Integration Tests
     run: claude-pm test --integration
   ```

2. **Parallel Testing**
   ```yaml
   # Use pytest-xdist for parallel testing
   - name: Run Tests
     run: claude-pm test --parallel --workers 4
   ```

3. **Test Matrix**
   ```yaml
   strategy:
     matrix:
       python-version: [3.9, 3.10, 3.11, 3.12]
       os: [ubuntu-latest, windows-latest, macos-latest]
   ```

### Documentation

1. **Document Test Purpose**
   ```python
   def test_memory_service_concurrent_access():
       """
       Test that memory service handles concurrent access correctly.
       
       This test verifies that multiple simultaneous requests to the
       memory service don't cause data corruption or deadlocks.
       """
       pass
   ```

2. **Include Examples**
   ```python
   def test_config_parsing():
       """
       Test configuration parsing.
       
       Example:
           config = Config({"host": "localhost", "port": 8002})
           assert config.host == "localhost"
       """
       pass
   ```

### Contributing Guidelines for CLI Testing

When adding new CLI tests, follow these guidelines:

1. **Test File Naming**
   - Use `test_claude_pm_cli_*.py` for CLI-specific tests
   - Use `test_*_integration.py` for integration tests
   - Use `test_*_fixtures.py` for shared fixtures

2. **Test Class Organization**
   ```python
   class TestClaudePMCommand:
       """Tests for a specific CLI command."""
       
       def test_command_success(self):
           """Test successful command execution."""
           pass
       
       def test_command_error_handling(self):
           """Test command error handling."""
           pass
       
       def test_command_options(self):
           """Test command options and flags."""
           pass
   ```

3. **Use Appropriate Markers**
   ```python
   @pytest.mark.unit
   def test_fast_unit_test():
       pass
   
   @pytest.mark.integration
   def test_service_integration():
       pass
   
   @pytest.mark.slow
   def test_long_running_operation():
       pass
   ```

4. **CLI Test Patterns**
   ```python
   def test_cli_command_with_runner(self, cli_runner):
       """Test using Click's test runner."""
       from claude_pm.cli import cli
       
       result = cli_runner.invoke(cli, ['health'])
       assert result.exit_code == 0
       assert "Health Dashboard" in result.output
   
   def test_cli_command_with_subprocess(self):
       """Test using subprocess for integration testing."""
       result = subprocess.run(
           ["claude-pm", "test", "--help"],
           capture_output=True,
           text=True
       )
       assert result.returncode == 0
       assert "Run tests" in result.stdout
   ```

5. **Testing CLI Options**
   ```python
   @pytest.mark.parametrize("options,expected", [
       (["--unit"], "unit tests"),
       (["--integration"], "integration tests"),
       (["--coverage"], "coverage report"),
       (["--verbose"], "verbose output"),
   ])
   def test_cli_options(self, cli_runner, options, expected):
       """Test various CLI options."""
       result = cli_runner.invoke(cli, ['test'] + options)
       # Assert expected behavior
   ```

## Summary

The Claude PM Framework provides comprehensive testing capabilities through:

### Core Testing Features
- **Unified CLI Testing**: `claude-pm test` command with extensive options and pytest integration
- **Comprehensive Test Architecture**: 29 CLI tests across 4 specialized test files
- **Multiple Test Categories**: Unit, integration, performance, and memory tests
- **Advanced Testing Options**: Parallel execution, watch mode, pattern matching, and failfast
- **Full Coverage Integration**: HTML, XML, and terminal coverage reports with detailed metrics

### Testing Infrastructure
- **Class-based Test Organization**: Following Python standards with fixtures and markers
- **Pytest Integration**: Full pytest compatibility with custom markers and configuration
- **CI/CD Ready**: GitHub Actions workflows, pre-commit hooks, and Docker support
- **Development Tools**: Watch mode, debugging, profiling, and parallel execution
- **Make Target Integration**: Compatible with existing Make-based workflows

### CLI Testing Architecture
- **Command Testing**: Individual CLI command functionality
- **Integration Testing**: CLI interaction with framework services
- **Fixture System**: Shared testing utilities and temporary environments
- **Runner Testing**: CLI execution and process management testing

### Advanced Features
- **Parallel Testing**: Multi-worker test execution with pytest-xdist
- **Watch Mode**: Automatic test re-running on file changes
- **Coverage Analysis**: Branch coverage, missing line detection, and threshold enforcement
- **Performance Testing**: Memory profiling, benchmarking, and resource monitoring
- **Debugging Support**: PDB integration, verbose output, and test isolation

For more information, refer to:
- [Python Standards](PYTHON_STANDARDS.md) for coding standards
- [Framework Overview](FRAMEWORK_OVERVIEW.md) for architecture details
- [OPS Cookbook](OPS_COOKBOOK.md) for operational procedures

---

**Last Updated**: 2025-07-11
**Version**: 4.1.0
**Author**: Claude Documentation Agent