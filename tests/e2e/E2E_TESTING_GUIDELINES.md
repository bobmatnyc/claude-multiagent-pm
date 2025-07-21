# E2E Testing Guidelines for Claude PM Framework

## Overview

This document provides comprehensive guidelines for writing and maintaining end-to-end (E2E) tests for the Claude PM framework. E2E tests validate complete workflows and ensure all components work together correctly.

## Directory Structure

```
tests/e2e/
├── core/              # Core functionality tests
├── fixtures/          # Test fixtures and mock data
├── utils/            # Test utilities and helpers
├── pytest.ini        # E2E-specific pytest configuration
└── E2E_TESTING_GUIDELINES.md
```

## Test Categories

### 1. Core Tests (`core/`)
Tests for fundamental framework functionality:
- Agent discovery and selection
- Orchestration flows
- Framework initialization
- Configuration management
- Prompt filtering and context management
- Integration between all components

### 2. Integration Tests
Tests for component interactions:
- Agent-to-agent communication
- Subprocess management
- API integrations
- File system operations

### 3. Workflow Tests
Complete user workflow validations:
- Project initialization
- Multi-agent task execution
- Error handling and recovery
- Performance validation

## Writing E2E Tests

### Base Test Class

All E2E tests should inherit from `BaseE2ETest`:

```python
from tests.e2e.utils import BaseE2ETest

class TestAgentDiscovery(BaseE2ETest):
    """Test agent discovery functionality."""
    
    def test_discover_core_agents(self):
        """Test discovery of core agents."""
        # Test implementation
```

### Test Structure

1. **Setup**: Use fixtures and utilities to prepare test environment
2. **Execution**: Run the actual test scenario
3. **Validation**: Assert expected outcomes
4. **Cleanup**: Automatic via BaseE2ETest

### Using Fixtures

```python
from tests.e2e.fixtures import AgentFixtures, ConfigFixtures

def test_agent_loading():
    # Create agent fixture
    doc_agent = AgentFixtures.documentation_agent()
    
    # Create configuration
    config = ConfigFixtures.base_config()
```

### Using Mocks

```python
from tests.e2e.utils import MockSystem, MockAgent

def test_with_mocks():
    # Setup mock system
    mock_system = MockSystem()
    mock_system.setup()
    
    # Create mock agent
    mock_agent = MockAgent("test_agent")
    mock_agent.configure_response("test_task", {"status": "success"})
```

## Test Naming Conventions

### File Names
- `test_<feature>_<aspect>.py`
- Example: `test_agent_discovery_core.py`

### Test Function Names
- `test_<scenario>_<expected_outcome>`
- Example: `test_discover_agents_returns_all_core_agents`

### Test Class Names
- `Test<Feature><Aspect>`
- Example: `TestAgentDiscoveryCore`

## Test Data Management

### Using Test Data Generators

```python
from tests.e2e.utils import TestDataGenerators

def test_with_generated_data():
    # Generate test agents
    agents = TestDataGenerators.generate_agent_data(count=5)
    
    # Generate test project
    project_path = TestDataGenerators.generate_test_project(
        base_path=self.test_dir,
        project_name="test_project"
    )
```

### Test Data Best Practices

1. **Isolation**: Each test should create its own data
2. **Cleanup**: Use automatic cleanup via fixtures
3. **Repeatability**: Tests must produce consistent results
4. **Performance**: Keep test data minimal but representative

## Mocking External Dependencies

### API Mocks

```python
def test_api_interaction(self):
    mock_system = MockSystem()
    mock_system.setup()
    
    # Configure API response
    mock_system.configure_mock_response(
        'openai',
        {'choices': [{'message': {'content': 'Test response'}}]}
    )
```

### Subprocess Mocks

```python
def test_subprocess_execution(self):
    # Subprocess mocks are automatically set up by MockSystem
    result = self.run_claude_pm(['init'])
    self.assert_command_success(result)
```

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.core
def test_core_functionality():
    pass

@pytest.mark.slow
@pytest.mark.orchestration
def test_complex_orchestration():
    pass

@pytest.mark.requires_setup
def test_with_full_setup():
    pass
```

## Running E2E Tests

### Run All E2E Tests
```bash
pytest tests/e2e/
```

### Run Specific Category
```bash
pytest tests/e2e/ -m core
pytest tests/e2e/ -m "not slow"
```

### Run with Coverage
```bash
pytest tests/e2e/ --cov=claude_pm --cov-report=html
```

## Performance Considerations

1. **Test Isolation**: Each test runs in its own temporary directory
2. **Parallel Execution**: Tests should be independent for parallel runs
3. **Resource Cleanup**: Automatic cleanup prevents resource leaks
4. **Mock Usage**: Use mocks for external services to improve speed

## Common Patterns

### Testing CLI Commands

```python
def test_cli_command(self):
    result = self.run_claude_pm(['init', '--setup'])
    self.assert_command_success(result, "Framework initialized")
```

### Testing Agent Interactions

```python
def test_agent_interaction(self):
    # Create agents
    doc_agent = self.create_mock_agent("documentation", "core")
    qa_agent = self.create_mock_agent("qa", "core")
    
    # Test interaction
    orchestrator = MockOrchestrator()
    orchestrator.register_agent(MockAgent("documentation"))
    orchestrator.register_agent(MockAgent("qa"))
    
    result = orchestrator.delegate_task("documentation", "Generate changelog", {})
    assert result['status'] == 'success'
```

### Testing Prompt Filtering and Context Management

```python
def test_context_filtering(self):
    # Initialize context manager
    context_manager = ContextManager()
    
    # Create test context
    test_context = {
        "files": {"main.py": "code", "README.md": "docs"},
        "project_overview": "Test project",
        "test_results": {"passed": 10}
    }
    
    # Filter for documentation agent
    doc_context = context_manager.filter_context_for_agent("documentation", test_context)
    
    # Verify appropriate filtering
    assert "project_overview" in doc_context
    assert "files" in doc_context
    # Test files might be filtered based on extensions
```

### Testing Shared Context Updates

```python
def test_shared_context_workflow(self):
    context_manager = ContextManager()
    
    # Agent 1 updates shared context
    context_manager.update_shared_context(
        agent_id="doc-agent-1",
        updates={"changelog": "## v1.0.0\n- Initial release"}
    )
    
    # Agent 2 can access shared context
    qa_context = context_manager.filter_context_for_agent("qa", {})
    assert "shared_context" in qa_context
    # Shared context contains results from other agents
```

### Testing Integration Workflows

```python
def test_multi_agent_workflow(self):
    context_manager = ContextManager()
    
    # Initial context
    context = {
        "command": "push",
        "git_status": "modified: src/app.py",
        "test_results": {"passed": 50, "failed": 0}
    }
    
    # Documentation agent phase
    doc_context = context_manager.filter_context_for_agent("documentation", context)
    context_manager.update_shared_context(
        agent_id="doc-agent",
        updates={"changelog": "Generated changelog", "version_impact": "minor"}
    )
    
    # QA agent phase  
    qa_context = context_manager.filter_context_for_agent("qa", context)
    context_manager.update_shared_context(
        agent_id="qa-agent",
        updates={"test_status": "all_passed", "coverage": 92.5}
    )
    
    # Version control agent phase
    vc_context = context_manager.filter_context_for_agent("version_control", context)
    # Each agent gets filtered context and can see shared results
```

### Testing Custom Agent Filters

```python
def test_custom_agent_filter(self):
    context_manager = ContextManager()
    
    # Register custom filter for performance agent
    custom_filter = ContextFilter(
        agent_type="performance",
        file_extensions=[".py", ".prof"],
        include_patterns=["benchmark", "perf"],
        context_sections=["performance_metrics", "benchmarks"]
    )
    
    context_manager.register_custom_filter("performance", custom_filter)
    
    # Test filtering
    context = {
        "files": {"benchmark.py": "perf code"},
        "performance_metrics": {"response_time": 125},
        "benchmarks": ["test1: 100ms"]
    }
    
    filtered = context_manager.filter_context_for_agent("performance", context)
    assert "performance_metrics" in filtered
```

### Testing Error Scenarios

```python
def test_error_handling(self):
    # Test missing configuration
    result = self.run_claude_pm(['init'], env={'CLAUDE_PM_CONFIG': '/nonexistent'})
    self.assert_command_failure(result, "Configuration not found")
```

## Debugging E2E Tests

### Enable Debug Output
```bash
pytest tests/e2e/ -v -s --log-cli-level=DEBUG
```

### Inspect Test Artifacts
```python
def test_with_artifacts(self):
    # Test artifacts are saved in self.test_dir
    print(f"Test directory: {self.test_dir}")
    
    # Keep test directory for inspection
    import pdb; pdb.set_trace()
```

### Check Mock Call History
```python
def test_mock_calls(self):
    mock_system = MockSystem()
    mock_system.setup()
    
    # Run test
    # ...
    
    # Check calls
    calls = mock_system.get_call_history('subprocess.run')
    print(f"Subprocess calls: {calls}")
```

## Best Practices

1. **Independent Tests**: Each test should be completely independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Proper Cleanup**: Rely on automatic cleanup, don't manual cleanup
4. **Mock External Services**: Never make real API calls in tests
5. **Test One Thing**: Each test should validate a single behavior
6. **Use Fixtures**: Leverage fixtures for common setups
7. **Document Complex Tests**: Add docstrings explaining test purpose
8. **Handle Async Code**: Use `run_async_test` helper for async operations

## Contributing New E2E Tests

1. Identify the feature or workflow to test
2. Create appropriate test file in correct directory
3. Inherit from `BaseE2ETest`
4. Use fixtures and utilities where appropriate
5. Add proper markers and documentation
6. Ensure tests pass locally before submitting
7. Update this guide if introducing new patterns

## Test Coverage and Results

### Current E2E Test Coverage

The E2E test suite includes comprehensive coverage for:

1. **Prompt Filtering** (`test_prompt_filtering_simple.py` - 9 tests)
   - Context structure validation
   - File extension filtering
   - Context section inclusion
   - Core agent filter verification
   - Context size reduction
   - Shared context operations
   - Interaction recording
   - Custom filter creation
   - Filter statistics tracking

2. **Context Management** (`test_context_management_simple.py` - 7 tests)
   - Basic context filtering
   - Shared context operations
   - Interaction history tracking
   - Filter statistics
   - Context size estimation
   - Old context cleanup
   - Multi-agent filtering

3. **Integration Testing** (`test_integration_complete.py` - 7 tests)
   - Documentation workflow
   - Multi-agent push workflow
   - Agent discovery with context filtering
   - Error handling workflow
   - Performance with large contexts
   - Custom agent integration
   - Full lifecycle integration

### Coverage Achievements

- **Total E2E Tests**: 23 tests across 3 test files
- **Execution Time**: ~5.1 seconds for full suite
- **Context Manager Coverage**: 60.92% (primary orchestration component)
- **All Tests Passing**: 100% success rate

### Key Coverage Areas

1. **Context Filtering**: Validates agent-specific context filtering reduces token usage
2. **Shared Context**: Tests inter-agent communication through shared context
3. **Performance**: Ensures filtering completes quickly even with large contexts
4. **Integration**: Validates complete multi-agent workflows function correctly
5. **Error Handling**: Tests graceful error propagation between agents

## Maintenance

- Review and update tests when framework changes
- Remove obsolete tests
- Keep test data generators up to date
- Monitor test execution time
- Maintain test coverage above 80%
- Track coverage improvements over time