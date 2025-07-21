"""
Shared pytest fixtures and configuration for all tests.
"""
import os
import sys
import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Generator, Any, Dict
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env() -> Generator[Dict[str, str], None, None]:
    """Mock environment variables for testing."""
    original_env = os.environ.copy()
    test_env = {
        "CLAUDE_PM_TEST": "true",
        "CLAUDE_PM_HOME": str(Path.home() / ".claude-pm-test"),
        "CLAUDE_PM_LOG_LEVEL": "DEBUG",
    }
    os.environ.update(test_env)
    yield test_env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_api_keys() -> Dict[str, str]:
    """Mock API keys for testing."""
    return {
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OPENAI_API_KEY": "test-openai-key",
    }


@pytest.fixture
def claude_pm_home(temp_dir: Path) -> Path:
    """Create a mock claude-pm home directory."""
    home = temp_dir / ".claude-pm"
    home.mkdir(exist_ok=True)
    
    # Create standard subdirectories
    (home / "agents").mkdir(exist_ok=True)
    (home / "config").mkdir(exist_ok=True)
    (home / "logs").mkdir(exist_ok=True)
    (home / "cache").mkdir(exist_ok=True)
    
    return home


@pytest.fixture
def mock_git_repo(temp_dir: Path) -> Path:
    """Create a mock git repository."""
    repo_path = temp_dir / "test-repo"
    repo_path.mkdir()
    
    # Initialize git repo
    os.system(f"cd {repo_path} && git init --quiet")
    
    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repository")
    os.system(f"cd {repo_path} && git add . && git commit -m 'Initial commit' --quiet")
    
    return repo_path


@pytest.fixture
def cleanup_test_artifacts():
    """Clean up test artifacts before and after tests."""
    # Pre-test cleanup
    artifacts_dirs = [
        Path("tests/reports/results"),
        Path("tests/reports/coverage"),
        Path("tests/reports/validation"),
    ]
    
    for dir_path in artifacts_dirs:
        if dir_path.exists():
            for file in dir_path.glob("*"):
                if file.is_file():
                    file.unlink()
    
    yield
    
    # Post-test cleanup is optional (keeps last test results)


@pytest.fixture
def setup_test_environment(claude_pm_home: Path, mock_env: Dict[str, str]):
    """Set up complete test environment."""
    # Configure test environment
    os.environ["CLAUDE_PM_HOME"] = str(claude_pm_home)
    
    yield {
        "home": claude_pm_home,
        "env": mock_env,
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    def _mock_response(content: str = "Test response", tool_calls: list = None):
        response = Mock()
        response.content = content
        response.tool_calls = tool_calls or []
        return response
    
    return _mock_response


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry for testing."""
    registry = Mock()
    registry.list_agents.return_value = {
        "documentation": {"type": "documentation", "path": "agents/documentation.md"},
        "qa": {"type": "qa", "path": "agents/qa.md"},
        "engineer": {"type": "engineer", "path": "agents/engineer.md"},
    }
    registry.get_agent.return_value = {"type": "test", "content": "Test agent"}
    return registry


# Test markers for categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "qa: QA validation tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")
    config.addinivalue_line("markers", "slow: Slow tests (>5s)")
    config.addinivalue_line("markers", "requires_api: Tests requiring API keys")
    config.addinivalue_line("markers", "requires_network: Tests requiring network")


# Async test support
@pytest.fixture
def async_test():
    """Support for async test functions."""
    def _wrapper(coro):
        return asyncio.run(coro)
    return _wrapper