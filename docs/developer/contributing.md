# Contributing Guide

Thank you for your interest in contributing to the Claude PM Framework! This guide provides everything you need to know about contributing code, documentation, and ideas to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful** of differing viewpoints and experiences
- **Be constructive** in your feedback and criticism
- **Be inclusive** and welcoming to all contributors
- **Be professional** in all interactions

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/claude-multiagent-pm.git
cd claude-multiagent-pm
git remote add upstream https://github.com/Bobjayafam/claude-multiagent-pm.git
```

### 2. Set Up Development Environment

Follow the [Development Setup Guide](./setup.md) to configure your environment.

### 3. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# Or for bugs: git checkout -b fix/issue-description
```

## Contribution Types

### 1. Bug Reports

**Before reporting a bug:**
- Search existing issues to avoid duplicates
- Try to reproduce with the latest version
- Collect relevant information (logs, environment, steps)

**Bug report template:**
```markdown
### Description
Clear description of the bug

### Steps to Reproduce
1. Step one
2. Step two
3. ...

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: [e.g., macOS 13.0]
- Node.js: [e.g., 18.16.0]
- Python: [e.g., 3.10.0]
- Framework Version: [e.g., 0.9.3]

### Additional Context
Any other relevant information, logs, or screenshots
```

### 2. Feature Requests

**Before requesting a feature:**
- Check if it's already requested or in development
- Consider if it aligns with project goals
- Think about implementation complexity

**Feature request template:**
```markdown
### Feature Description
Clear description of the proposed feature

### Use Case
Why is this feature needed? What problem does it solve?

### Proposed Implementation
How might this be implemented? (optional)

### Alternatives Considered
What alternatives have you considered?

### Additional Context
Any mockups, examples, or references
```

### 3. Code Contributions

#### Code Style

**Python Code Style:**
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

```python
# Good
async def process_agent_task(
    agent_id: str,
    task_data: Dict[str, Any],
    timeout: Optional[int] = None
) -> AgentResult:
    """Process a task using the specified agent.
    
    Args:
        agent_id: Unique identifier for the agent
        task_data: Task parameters and context
        timeout: Optional timeout in seconds
        
    Returns:
        AgentResult containing execution status and output
        
    Raises:
        AgentNotFoundError: If agent_id is invalid
        TaskTimeoutError: If execution exceeds timeout
    """
    # Implementation
```

**JavaScript/TypeScript Code Style:**
- Use ESLint and Prettier configurations
- Prefer async/await over callbacks
- Use meaningful function names
- Document complex logic

```javascript
// Good
/**
 * Initialize the framework with given configuration
 * @param {Object} config - Framework configuration
 * @returns {Promise<void>}
 */
async function initializeFramework(config) {
  validateConfig(config);
  await loadAgents();
  await setupServices();
  logger.info('Framework initialized successfully');
}
```

#### Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or fixes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

**Examples:**
```bash
# Feature
git commit -m "feat(agents): Add performance monitoring agent"

# Bug fix
git commit -m "fix(cli): Resolve path issues on Windows"

# Documentation
git commit -m "docs(api): Update agent registry documentation"

# With body
git commit -m "feat(cache): Implement shared prompt cache

- Add LRU cache with 99.7% performance improvement
- Implement automatic cache invalidation
- Add cache metrics and monitoring

Closes #123"
```

#### Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Update documentation
   - Add tests for new features
   - Run linting and formatting

2. **PR title format:**
   ```
   <type>(<scope>): <description>
   ```

3. **PR description template:**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] Breaking changes documented
   
   ## Related Issues
   Closes #123
   Related to #456
   ```

### 4. Documentation Contributions

#### Documentation Style

- Write in clear, concise English
- Use active voice
- Include code examples
- Keep paragraphs short
- Use proper markdown formatting

#### Documentation Structure

```markdown
# Page Title

Brief introduction paragraph explaining the topic.

## Main Section

### Subsection

Content with **emphasis** where needed.

```python
# Code example
def example():
    pass
```

> **Note**: Important information

> **Warning**: Critical warnings

## See Also

- [Related Topic](./related.md)
- [Another Topic](./another.md)
```

## Testing Requirements

### Running Tests

```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests
npm run test:integration

# Python tests
python -m pytest

# Specific test file
python -m pytest tests/test_specific.py

# With coverage
npm run test:coverage
```

### Writing Tests

**Test file naming:**
- Unit tests: `test_<module_name>.py` or `<module>.test.js`
- Integration tests: `test_integration_<feature>.py`

**Test structure:**
```python
# Python example
import pytest
from claude_pm.services import MyService

class TestMyService:
    """Test cases for MyService."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MyService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.initialized is False
        service.initialize()
        assert service.initialized is True
    
    @pytest.mark.asyncio
    async def test_async_operation(self, service):
        """Test async operation."""
        result = await service.process()
        assert result.success is True
```

## Review Process

### What to Expect

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainers review within 2-3 days
3. **Feedback**: Constructive feedback and suggestions
4. **Iterations**: May require changes based on feedback
5. **Merge**: Once approved, changes are merged

### Review Criteria

- **Code Quality**: Clean, readable, maintainable
- **Testing**: Adequate test coverage
- **Documentation**: Updated as needed
- **Performance**: No significant regressions
- **Security**: No security vulnerabilities
- **Compatibility**: Backwards compatible

## Release Process

### Version Numbering

We follow Semantic Versioning (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., 0.9.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

### Release Cycle

1. **Development**: Features developed in feature branches
2. **Testing**: Comprehensive testing in develop branch
3. **Release Candidate**: RC testing for major releases
4. **Release**: Tagged release with changelog
5. **Deployment**: NPM and PyPI publication

## Getting Help

### Resources

- **Documentation**: Read existing docs first
- **Issues**: Search closed issues
- **Discussions**: Check GitHub Discussions
- **Discord**: Join our community (if available)

### Asking Questions

When asking for help:
1. Search existing resources
2. Provide context and code examples
3. Describe what you've tried
4. Include error messages and logs

## Recognition

Contributors are recognized in:
- Release notes
- Contributors file
- Project README
- Annual contributor report

## Advanced Contributing

### Becoming a Maintainer

Active contributors may be invited to become maintainers. Criteria:
- Consistent quality contributions
- Good understanding of the codebase
- Helpful in community discussions
- Commitment to project values

### Architecture Changes

For significant architecture changes:
1. Discuss in an issue first
2. Create an RFC (Request for Comments)
3. Get community feedback
4. Implement after approval

---

*Thank you for contributing to the Claude PM Framework! Your efforts help make this project better for everyone.*