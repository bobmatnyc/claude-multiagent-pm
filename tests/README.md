# Claude Multi-Agent PM Test Suite

This directory contains the comprehensive test suite for the Claude Multi-Agent PM framework.

## Test Organization Status

**✅ REORGANIZATION COMPLETE - All Phases Finished (2025-07-18)**
- Phase 1: ✅ Complete - Directory structure created
- Phase 2: ✅ Complete - Core unit tests migrated
- Phase 3: ✅ Complete - Agent and service tests migrated
- Phase 4: ✅ Complete - Performance and utility tests migrated
- Phase 5: ✅ Complete - Final cleanup and validation completed

See `reports/test_reorganization_final_report.md` for complete details.

## Directory Structure

### Core Test Categories

#### `/unit/`
Unit tests for individual components, organized by module:
- **`/agents/`** - Tests for agent implementations
- **`/services/`** - Tests for service modules
- **`/core/`** - Tests for core framework functionality
- **`/cli/`** - Tests for CLI commands and flags

#### `/integration/`
Integration tests that verify multiple components working together:
- **`/agents/`** - Agent interaction and delegation tests
- **`/services/`** - Service integration tests
- **`/deployment/`** - Deployment workflow tests
- **`/workflows/`** - End-to-end workflow tests

#### `/e2e/`
End-to-end tests simulating real user scenarios:
- **`/installation/`** - NPM installation and setup tests
- **`/deployment/`** - Full deployment scenarios
- **`/workflows/`** - Complete user workflow tests
- **`/version-specific/`** - Tests for specific framework versions

#### `/performance/`
Performance benchmarks and optimization tests

### Support Directories

#### `/fixtures/`
Test data and mock objects:
- **`/agents/`** - Mock agent configurations
- **`/projects/`** - Sample project structures
- **`/data/`** - Test data files

#### `/utils/`
Test utilities and helper functions

#### `/reports/`
Test execution reports and artifacts:
- **`/coverage/`** - Code coverage reports
- **`/results/`** - Test execution results
- **`/validation/`** - Validation reports

#### `/legacy/`
Older tests preserved for reference (to be migrated or removed)

#### `/config/`
Test configuration files

#### `/scripts/`
Test automation and runner scripts

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test category
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Run with coverage
```bash
pytest tests/ --cov=claude_pm --cov-report=html
```

### Run performance tests
```bash
pytest tests/performance/ -v
```

## Test Organization Guidelines

1. **Unit tests** should be fast, isolated, and test single components
2. **Integration tests** should verify component interactions
3. **E2E tests** should simulate real user workflows
4. **Performance tests** should be run separately and track metrics

## Contributing

When adding new tests:
1. Place them in the appropriate category directory
2. Follow existing naming conventions (test_*.py)
3. Include docstrings explaining what is being tested
4. Use appropriate fixtures from `/fixtures/`
5. Update this README if adding new test categories