---
issue_id: ISS-0128
title: Test Directory Reorganization - Clean Structure and Categorization
description: Reorganize 76+ test files from root into a clean hierarchical structure with clear separation by test type
status: planning
priority: high
assignee: masa
created_date: 2025-07-18T19:08:11.444Z
updated_date: 2025-07-18T19:09:20.328Z
estimated_tokens: 0
actual_tokens: 0
ai_context:
  - context/requirements
  - context/constraints
  - context/assumptions
  - context/dependencies
sync_status: local
related_tasks:
  - TSK-0027
  - TSK-0028
  - TSK-0029
  - TSK-0030
  - TSK-0031
related_issues: []
tags:
  - testing
  - refactoring
  - quality
completion_percentage: 0
blocked_by: []
blocks: []
content: >-
  # Issue: Test Directory Reorganization - Clean Structure and Categorization


  ## Problem Statement


  The test directory currently contains 76+ test files mixed at the root level with poor organization and
  categorization. This makes it difficult to:

  - Navigate and find specific tests

  - Understand test coverage and types

  - Run specific test categories

  - Maintain test code effectively


  ### Current Issues:

  - 76+ test files all mixed at root level

  - No separation between unit, integration, and e2e tests

  - Non-test files (utilities, fixtures) mixed with actual tests

  - Unclear naming conventions

  - Difficult to run specific test categories


  ## Proposed Solution


  Reorganize tests into a clear hierarchical structure similar to the successful docs/ reorganization:


  ### Proposed Structure:

  ```

  tests/

  ├── unit/                    # Unit tests organized by module

  │   ├── agents/             # Agent-specific unit tests

  │   ├── core/               # Core functionality tests

  │   ├── services/           # Service layer tests

  │   └── utils/              # Utility function tests

  ├── integration/            # Integration tests

  │   ├── api/               # API integration tests

  │   ├── database/          # Database integration tests

  │   └── services/          # Service integration tests

  ├── e2e/                    # End-to-end tests

  │   ├── workflows/         # Complete workflow tests

  │   └── scenarios/         # User scenario tests

  ├── performance/            # Performance and load tests

  ├── fixtures/               # Test data and fixtures

  │   ├── data/              # Test data files

  │   └── mocks/             # Mock objects and stubs

  └── config/                 # Test configuration
      ├── jest.config.js     # Jest configuration
      ├── pytest.ini         # Pytest configuration
      └── test-utils.js      # Shared test utilities
  ```


  ## Benefits


  1. **Improved Organization**: Clear separation of test types

  2. **Better Navigation**: Easy to find and run specific tests

  3. **Scalability**: Structure supports growth

  4. **Maintenance**: Easier to maintain and update tests

  5. **CI/CD Integration**: Can run specific test suites in pipelines

  6. **Documentation**: Clear structure is self-documenting


  ## Implementation Phases


  ### Phase 1: Backup and create test directory structure

  - Create full backup of current test files

  - Create new directory structure

  - Verify backup integrity


  ### Phase 2: Organize unit tests by module

  - Identify all unit tests

  - Move to appropriate subdirectories

  - Update import paths


  ### Phase 3: Migrate integration and e2e tests

  - Identify integration tests

  - Identify e2e tests

  - Move to respective directories


  ### Phase 4: Setup test configuration and utilities

  - Move test utilities to config/

  - Setup jest.config.js

  - Setup pytest.ini

  - Create shared test utilities


  ### Phase 5: Cleanup and validate test suite

  - Remove old test files

  - Run full test suite

  - Validate all tests pass

  - Update CI/CD pipelines


  ## Acceptance Criteria

  - [ ] All existing tests remain functional and runnable

  - [ ] Clear separation between unit, integration, and e2e tests

  - [ ] Test configuration files properly organized

  - [ ] Test utilities and fixtures in dedicated directories

  - [ ] Documentation created for test organization

  - [ ] CI/CD pipelines updated to use new structure

  - [ ] No regression in test coverage

  - [ ] Team can easily navigate and run specific test categories


  ## Notes

  - Similar reorganization to the successful docs/ directory cleanup

  - Must preserve all test functionality

  - Multi-phase approach to minimize risk

  - Each phase will be tracked as a separate task
file_path: /Users/masa/Projects/claude-multiagent-pm/tasks/issues/ISS-0128-test-directory-reorganization-clean-structure-and-categorization.md
---

# Issue: Test Directory Reorganization - Clean Structure and Categorization

## Problem Statement

The test directory currently contains 76+ test files mixed at the root level with poor organization and categorization. This makes it difficult to:
- Navigate and find specific tests
- Understand test coverage and types
- Run specific test categories
- Maintain test code effectively

### Current Issues:
- 76+ test files all mixed at root level
- No separation between unit, integration, and e2e tests
- Non-test files (utilities, fixtures) mixed with actual tests
- Unclear naming conventions
- Difficult to run specific test categories

## Proposed Solution

Reorganize tests into a clear hierarchical structure similar to the successful docs/ reorganization:

### Proposed Structure:
```
tests/
├── unit/                    # Unit tests organized by module
│   ├── agents/             # Agent-specific unit tests
│   ├── core/               # Core functionality tests
│   ├── services/           # Service layer tests
│   └── utils/              # Utility function tests
├── integration/            # Integration tests
│   ├── api/               # API integration tests
│   ├── database/          # Database integration tests
│   └── services/          # Service integration tests
├── e2e/                    # End-to-end tests
│   ├── workflows/         # Complete workflow tests
│   └── scenarios/         # User scenario tests
├── performance/            # Performance and load tests
├── fixtures/               # Test data and fixtures
│   ├── data/              # Test data files
│   └── mocks/             # Mock objects and stubs
└── config/                 # Test configuration
    ├── jest.config.js     # Jest configuration
    ├── pytest.ini         # Pytest configuration
    └── test-utils.js      # Shared test utilities
```

## Benefits

1. **Improved Organization**: Clear separation of test types
2. **Better Navigation**: Easy to find and run specific tests
3. **Scalability**: Structure supports growth
4. **Maintenance**: Easier to maintain and update tests
5. **CI/CD Integration**: Can run specific test suites in pipelines
6. **Documentation**: Clear structure is self-documenting

## Implementation Phases

### Phase 1: Backup and create test directory structure
- Create full backup of current test files
- Create new directory structure
- Verify backup integrity

### Phase 2: Organize unit tests by module
- Identify all unit tests
- Move to appropriate subdirectories
- Update import paths

### Phase 3: Migrate integration and e2e tests
- Identify integration tests
- Identify e2e tests
- Move to respective directories

### Phase 4: Setup test configuration and utilities
- Move test utilities to config/
- Setup jest.config.js
- Setup pytest.ini
- Create shared test utilities

### Phase 5: Cleanup and validate test suite
- Remove old test files
- Run full test suite
- Validate all tests pass
- Update CI/CD pipelines

## Acceptance Criteria
- [ ] All existing tests remain functional and runnable
- [ ] Clear separation between unit, integration, and e2e tests
- [ ] Test configuration files properly organized
- [ ] Test utilities and fixtures in dedicated directories
- [ ] Documentation created for test organization
- [ ] CI/CD pipelines updated to use new structure
- [ ] No regression in test coverage
- [ ] Team can easily navigate and run specific test categories

## Notes
- Similar reorganization to the successful docs/ directory cleanup
- Must preserve all test functionality
- Multi-phase approach to minimize risk
- Each phase will be tracked as a separate task
