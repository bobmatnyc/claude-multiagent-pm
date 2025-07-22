# Testing Guide

## Overview

This guide covers testing strategies, frameworks, and best practices for the Claude PM Framework. We maintain high quality standards through comprehensive testing at multiple levels.

## Testing Philosophy

- **Test-Driven Development (TDD)**: Write tests before implementation
- **Comprehensive Coverage**: Aim for >80% code coverage
- **Fast Feedback**: Tests should run quickly
- **Isolated Testing**: Tests should not depend on external services
- **Meaningful Tests**: Focus on behavior, not implementation details

## Testing Stack

### Python Testing
- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-timeout**: Test timeout management

### JavaScript Testing
- **Jest**: Testing framework
- **Supertest**: HTTP testing
- **Sinon**: Mocking library

### Integration Testing
- **Docker**: Containerized test environments
- **GitHub Actions**: CI/CD testing

## Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_agent_registry.py
│   ├── test_shared_cache.py
│   └── test_services.py
├── integration/             # Integration tests
│   ├── test_cli_commands.py
│   ├── test_agent_workflows.py
│   └── test_deployment.py
├── e2e/                     # End-to-end tests
│   ├── test_full_workflow.py
│   └── test_user_scenarios.py
├── fixtures/                # Test fixtures
│   ├── agents/
│   ├── configs/
│   └── data/
└── conftest.py             # Shared test configuration
```

## Writing Tests

### Unit Tests

Unit tests focus on individual components in isolation.

#### Python Unit Test Example

```python
# test_agent_registry.py
import pytest
from unittest.mock import Mock, patch
from claude_pm.core.agent_registry import AgentRegistry

class TestAgentRegistry:
    """Test cases for AgentRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create registry instance for testing."""
        return AgentRegistry()
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agent data."""
        return {
            'performance': {
                'type': 'performance',
                'specializations': ['performance', 'monitoring'],
                'path': '/test/performance-agent.md'
            },
            'security': {
                'type': 'security',
                'specializations': ['security', 'audit'],
                'path': '/test/security-agent.md'
            }
        }
    
    def test_list_agents_all(self, registry, mock_agents):
        """Test listing all agents."""
        with patch.object(registry, '_scan_directories', return_value=mock_agents):
            agents = registry.listAgents()
            
            assert len(agents) == 2
            assert 'performance' in agents
            assert 'security' in agents
    
    def test_list_agents_by_specialization(self, registry, mock_agents):
        """Test filtering agents by specialization."""
        with patch.object(registry, '_scan_directories', return_value=mock_agents):
            agents = registry.listAgents(specialization='performance')
            
            assert len(agents) == 1
            assert 'performance' in agents
    
    def test_select_optimal_agent(self, registry, mock_agents):
        """Test optimal agent selection."""
        with patch.object(registry, '_scan_directories', return_value=mock_agents):
            agents = registry.listAgents()
            optimal = registry.selectOptimalAgent(agents, 'performance_task')
            
            assert optimal is not None
            assert optimal['type'] == 'performance'
    
    @pytest.mark.parametrize("scope,expected_count", [
        ('all', 2),
        ('user', 1),
        ('system', 1),
    ])
    def test_list_agents_scope(self, registry, scope, expected_count):
        """Test agent listing with different scopes."""
        # Mock different agent locations
        mock_data = {
            'user': {'user-agent': {'type': 'custom'}},
            'system': {'system-agent': {'type': 'core'}}
        }
        
        with patch.object(registry, '_scan_directories', 
                         return_value=mock_data.get(scope, {})):
            agents = registry.listAgents()
            assert len(agents) == expected_count
```

#### JavaScript Unit Test Example

```javascript
// test_shared_cache.test.js
const SharedCache = require('../src/services/SharedCache');

describe('SharedCache', () => {
  let cache;
  
  beforeEach(() => {
    cache = new SharedCache({ maxSize: 10, ttl: 60 });
  });
  
  afterEach(() => {
    cache.clear();
  });
  
  test('should store and retrieve values', () => {
    cache.set('key1', 'value1');
    expect(cache.get('key1')).toBe('value1');
  });
  
  test('should return null for missing keys', () => {
    expect(cache.get('missing')).toBeNull();
  });
  
  test('should respect max size limit', () => {
    for (let i = 0; i < 15; i++) {
      cache.set(`key${i}`, `value${i}`);
    }
    
    expect(cache.size()).toBe(10);
    expect(cache.get('key0')).toBeNull(); // Evicted
    expect(cache.get('key14')).toBe('value14'); // Recent
  });
  
  test('should expire entries after TTL', async () => {
    cache = new SharedCache({ maxSize: 10, ttl: 0.1 }); // 100ms TTL
    cache.set('key1', 'value1');
    
    expect(cache.get('key1')).toBe('value1');
    
    await new Promise(resolve => setTimeout(resolve, 150));
    
    expect(cache.get('key1')).toBeNull();
  });
});
```

### Integration Tests

Integration tests verify that components work together correctly.

```python
# test_agent_workflows.py
import pytest
import asyncio
from claude_pm.orchestration import PMOrchestrator, TaskTool
from claude_pm.core.agent_registry import AgentRegistry

class TestAgentWorkflows:
    """Test multi-agent workflow integration."""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance."""
        orchestrator = PMOrchestrator()
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_documentation_workflow(self, orchestrator):
        """Test documentation generation workflow."""
        # Define workflow
        workflow = {
            'name': 'documentation_update',
            'tasks': [
                {
                    'agent': 'documentation',
                    'action': 'analyze_patterns',
                    'input': {'path': './src'}
                },
                {
                    'agent': 'documentation', 
                    'action': 'generate_docs',
                    'input': {'format': 'markdown'}
                }
            ]
        }
        
        # Execute workflow
        result = await orchestrator.orchestrate(workflow)
        
        # Verify results
        assert result.success
        assert len(result.task_results) == 2
        assert all(r.success for r in result.task_results)
        assert 'documentation' in result.output
    
    @pytest.mark.asyncio
    async def test_push_command_workflow(self, orchestrator):
        """Test full push command workflow."""
        # Simulate push command
        tasks = [
            ('documentation', 'generate_changelog'),
            ('qa', 'run_tests'),
            ('qa', 'run_linting'),
            ('version_control', 'commit_changes'),
            ('version_control', 'create_tag')
        ]
        
        results = []
        for agent_type, task in tasks:
            result = await orchestrator.delegate_task(
                agent_type,
                {'action': task}
            )
            results.append(result)
        
        # All tasks should succeed
        assert all(r.success for r in results)
```

### End-to-End Tests

E2E tests verify complete user workflows.

```python
# test_user_scenarios.py
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path

class TestUserScenarios:
    """Test real-world user scenarios."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_new_project_setup(self, temp_project):
        """Test setting up a new project."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_project)
            
            # Initialize project
            result = subprocess.run(
                ['claude-pm', 'init'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Verify structure created
            assert (temp_project / '.claude-pm').exists()
            assert (temp_project / '.claude-pm' / 'config.json').exists()
            
            # Test basic command
            result = subprocess.run(
                ['claude-pm', 'status'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert 'Framework: Operational' in result.stdout
            
        finally:
            os.chdir(original_cwd)
    
    def test_custom_agent_creation(self, temp_project):
        """Test creating and using custom agent."""
        os.chdir(temp_project)
        
        # Create custom agent
        agents_dir = temp_project / '.claude-pm' / 'agents'
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        agent_content = """
# Custom Test Agent

## Agent Profile
- **Nickname**: Tester
- **Type**: testing
- **Specializations**: ['testing', 'validation']
- **Authority**: Test execution

## When to Use
Testing scenarios
"""
        
        (agents_dir / 'test-agent.md').write_text(agent_content)
        
        # Verify agent discovery
        result = subprocess.run(
            ['python', '-c', '''
from claude_pm.core.agent_registry import AgentRegistry
registry = AgentRegistry()
agents = registry.listAgents()
print("test-agent" in agents)
'''],
            capture_output=True,
            text=True
        )
        assert 'True' in result.stdout
```

## Testing Patterns

### 1. Mocking External Services

```python
# Mock AI API calls
@patch('claude_pm.services.ai_service.call_api')
def test_ai_integration(mock_api):
    """Test AI service integration."""
    mock_api.return_value = {
        'response': 'Mocked AI response',
        'tokens': 100
    }
    
    service = AIService()
    result = service.process_request('test prompt')
    
    assert result['response'] == 'Mocked AI response'
    mock_api.assert_called_once_with('test prompt')
```

### 2. Async Testing

```python
# Test async operations
@pytest.mark.asyncio
async def test_concurrent_agents():
    """Test concurrent agent execution."""
    orchestrator = PMOrchestrator()
    
    # Create multiple tasks
    tasks = [
        orchestrator.delegate_task('qa', {'action': 'test'}),
        orchestrator.delegate_task('documentation', {'action': 'scan'}),
        orchestrator.delegate_task('security', {'action': 'audit'})
    ]
    
    # Execute concurrently
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(r.success for r in results)
```

### 3. Fixture Patterns

```python
# Reusable test fixtures
@pytest.fixture(scope='session')
def test_config():
    """Shared test configuration."""
    return {
        'debug': True,
        'cache_enabled': False,
        'timeout': 5
    }

@pytest.fixture
def mock_filesystem(tmp_path):
    """Mock filesystem structure."""
    # Create test structure
    (tmp_path / 'src').mkdir()
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'docs').mkdir()
    
    # Add test files
    (tmp_path / 'src' / 'main.py').write_text('# Main file')
    (tmp_path / 'tests' / 'test_main.py').write_text('# Test file')
    
    return tmp_path
```

### 4. Parameterized Testing

```python
# Test multiple scenarios efficiently
@pytest.mark.parametrize("agent_type,expected_nickname", [
    ('documentation', 'Documenter'),
    ('qa', 'QA'),
    ('version_control', 'Versioner'),
    ('security', 'Security'),
])
def test_agent_nicknames(agent_type, expected_nickname):
    """Test agent nickname mapping."""
    agent = load_agent(agent_type)
    assert agent.nickname == expected_nickname

@pytest.mark.parametrize("invalid_input,expected_error", [
    (None, ValueError),
    ('', ValueError),
    ({'invalid': 'structure'}, TypeError),
])
def test_input_validation(invalid_input, expected_error):
    """Test input validation."""
    with pytest.raises(expected_error):
        process_input(invalid_input)
```

## Test Coverage

### Running Coverage Reports

```bash
# Python coverage
pytest --cov=claude_pm --cov-report=html --cov-report=term

# JavaScript coverage
npm run test:coverage

# Combined coverage report
npm run coverage:all
```

### Coverage Requirements

- **Overall**: >80% coverage
- **Core modules**: >90% coverage
- **New features**: 100% coverage
- **Bug fixes**: Include regression tests

### Interpreting Coverage

```bash
# Example coverage output
Name                              Stmts   Miss  Cover
-----------------------------------------------------
claude_pm/__init__.py                 5      0   100%
claude_pm/core/agent_registry.py    125     10    92%
claude_pm/services/cache.py          89      5    94%
claude_pm/utils/helpers.py           45      8    82%
-----------------------------------------------------
TOTAL                               892    115    87%
```

## Performance Testing

### Benchmarking

```python
# test_performance.py
import pytest
import time
from claude_pm.utils.performance import benchmark

class TestPerformance:
    """Performance regression tests."""
    
    @benchmark(max_time=0.1)  # 100ms limit
    def test_agent_loading_performance(self):
        """Test agent loading stays fast."""
        registry = AgentRegistry()
        agents = registry.listAgents()
        assert len(agents) > 0
    
    @benchmark(max_time=0.05)  # 50ms limit
    def test_cache_performance(self):
        """Test cache operations are fast."""
        cache = SharedPromptCache()
        
        # Write operations
        for i in range(1000):
            cache.set(f'key_{i}', f'value_{i}')
        
        # Read operations
        for i in range(1000):
            value = cache.get(f'key_{i}')
            assert value == f'value_{i}'
```

### Load Testing

```python
# test_load.py
import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.load
async def test_concurrent_load():
    """Test system under concurrent load."""
    orchestrator = PMOrchestrator()
    
    async def run_task(i):
        """Run single task."""
        return await orchestrator.delegate_task(
            'qa',
            {'action': 'test', 'id': i}
        )
    
    # Run 100 concurrent tasks
    tasks = [run_task(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    # Verify success rate
    success_rate = sum(1 for r in results if r.success) / len(results)
    assert success_rate > 0.95  # 95% success rate
```

## Debugging Tests

### 1. Verbose Output

```bash
# Run with verbose output
pytest -vv tests/test_specific.py

# Show print statements
pytest -s tests/test_specific.py

# Combined
pytest -vvs tests/test_specific.py
```

### 2. Debugging Failed Tests

```python
# Use pytest debugging
pytest --pdb tests/test_specific.py  # Drop into debugger on failure

# Or use breakpoints
def test_complex_logic():
    data = prepare_data()
    
    # Add breakpoint
    import pdb; pdb.set_trace()
    
    result = process_data(data)
    assert result.success
```

### 3. Test Isolation

```bash
# Run single test
pytest tests/test_file.py::TestClass::test_method

# Run tests matching pattern
pytest -k "agent and not slow"

# Run marked tests
pytest -m "unit and not integration"
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
        node-version: [16.x, 18.x, 20.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements/dev.txt
        npm install
    
    - name: Run tests
      run: |
        pytest --cov=claude_pm
        npm test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Best Practices

### 1. Test Naming
- Use descriptive test names
- Follow pattern: `test_<what>_<condition>_<expected>`
- Group related tests in classes

### 2. Test Independence
- Tests should not depend on execution order
- Clean up resources in teardown
- Use fixtures for shared setup

### 3. Test Data
- Use fixtures for test data
- Keep test data minimal but realistic
- Store large test data in separate files

### 4. Error Testing
- Test both success and failure paths
- Verify error messages are helpful
- Test edge cases and boundaries

### 5. Documentation
- Document complex test logic
- Explain why, not what
- Include examples for complex patterns

## Next Steps

- Review [API Reference](./api-reference.md) for testable interfaces
- See [Debugging Guide](./debugging.md) for troubleshooting
- Check [Performance Guide](./performance.md) for optimization
- Read [Contributing Guide](./contributing.md) for submission process

---

*Remember: Good tests enable confident refactoring and prevent regressions.*