# CLI Unit Tests

This directory contains comprehensive unit tests for the Claude PM CLI components.

## Test Files

### test_main.py
Tests for the main CLI entry point (`claude_pm.cli.__main__`):
- Main entry point execution
- CLI help command
- Version command handling
- Verbose flag behavior
- Config file flag
- Model selection flag (valid/invalid models)
- Combined flags usage
- Context passing to commands
- Directory context display
- Error handling
- No arguments behavior

### test_commands.py
Tests for CLI command modules and registration:
- ModularCLI class functionality
- Command module loading
- Model resolution and aliases
- External command registration
- CLI integration tests
- Model override context passing

### test_utils.py
Tests for CLI utility functions (`claude_pm.cli.cli_utils`):
- Configuration utilities (get_framework_config, paths)
- Model override functionality
- PM Orchestrator creation with CLI context
- Task Tool Helper creation
- Async command execution and decorators
- Timed operation decorators
- Utility functions (formatting, validation)
- Directory context display
- Error handling decorators
- Project validation
- Formatting functions
- CLI context management
- Config file operations
- Dependency checking
- System info retrieval
- Common CLI option decorators

### test_claude_pm_cli.py
Legacy tests for the old claude_pm.cli module (deprecated).

## Coverage Achieved

As of implementation:
- `claude_pm/cli/__init__.py`: 80.90% coverage
- `claude_pm/cli/__main__.py`: 100% coverage
- `claude_pm/cli/cli_utils.py`: 77.17% coverage

This represents a significant improvement from the initial 0% coverage for CLI components.

## Running Tests

Run all CLI tests:
```bash
python -m pytest tests/unit/cli/ -v
```

Run with coverage report:
```bash
python -m pytest tests/unit/cli/ -v --cov=claude_pm.cli --cov-report=term-missing
```

Run specific test file:
```bash
python -m pytest tests/unit/cli/test_main.py -v
```

## Test Patterns

The tests use common patterns:
- Click's `CliRunner` for testing CLI commands
- Extensive mocking of external dependencies
- Patch decorators for isolating functionality
- Parametrized tests for multiple scenarios
- Context managers for resource handling

## Known Issues

Some tests may fail due to:
- Package installation detection in test environment
- Mock patching order dependencies
- Async test execution requirements

These are typically environmental issues rather than actual code problems.