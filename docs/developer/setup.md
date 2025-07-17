# Development Setup Guide

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, Windows (with WSL2)
- **Node.js**: ≥16.0.0 (recommend 18.x or 20.x)
- **Python**: ≥3.8.0 (recommend 3.10 or 3.11)
- **Git**: ≥2.0.0
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 1GB free space

### Required Tools

```bash
# Check versions
node --version    # Should be ≥16.0.0
python3 --version # Should be ≥3.8.0
git --version     # Should be ≥2.0.0

# Package managers
npm --version     # Comes with Node.js
pip3 --version    # Comes with Python
```

## Getting Started

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Bobjayafam/claude-multiagent-pm.git
cd claude-multiagent-pm

# Or use SSH
git clone git@github.com:Bobjayafam/claude-multiagent-pm.git
cd claude-multiagent-pm
```

### 2. Install Dependencies

#### Node.js Dependencies

```bash
# Install Node.js dependencies
npm install

# Install global CLI tools (for testing)
npm install -g .
```

#### Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements/dev.txt

# Install the package in development mode
pip install -e .
```

### 3. Environment Configuration

#### Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env  # Or use your preferred editor
```

#### Required Environment Variables

```bash
# .env file
# AI API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Model Configuration
CLAUDE_PM_DEFAULT_MODEL=claude-3-sonnet-20240229
CLAUDE_PM_TEMPERATURE=0.7

# Optional: Performance Settings
CLAUDE_PM_CACHE_ENABLED=true
CLAUDE_PM_MAX_CONCURRENT_AGENTS=10

# Optional: Development Settings
CLAUDE_PM_DEBUG=true
CLAUDE_PM_LOG_LEVEL=debug
```

### 4. Verify Installation

```bash
# Run framework health check
python -m claude_pm.cli init --verify

# Test CLI commands
claude-pm --version
claude-pm status

# Run basic tests
npm test
python -m pytest tests/
```

## Development Workflow

### 1. Project Structure

```
claude-multiagent-pm/
├── claude_pm/           # Python source code
│   ├── agents/         # Core system agents
│   ├── core/           # Core framework modules
│   ├── services/       # Service implementations
│   └── utils/          # Utility functions
├── bin/                # Executable scripts
├── scripts/            # Development scripts
├── tests/              # Test suites
├── docs/               # Documentation
├── framework/          # Framework templates
└── package.json        # Node.js configuration
```

### 2. Development Commands

```bash
# Start development mode
npm run dev

# Run tests
npm test                    # All tests
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests

# Linting and formatting
npm run lint               # Check code style
npm run lint:fix          # Auto-fix issues
npm run format            # Format code

# Python-specific commands
python -m pytest          # Run Python tests
python -m black .         # Format Python code
python -m flake8          # Lint Python code
```

### 3. Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: Add new feature"

# Push to remote
git push origin feature/your-feature-name

# Create pull request via GitHub
```

### 4. Testing Your Changes

```bash
# Test locally with development version
npm link                   # Link local version globally
cd /tmp/test-project      # Go to test project
claude-pm                 # Test your changes

# Unlink when done
npm unlink @bobmatnyc/claude-multiagent-pm
```

## IDE Setup

### Visual Studio Code

#### Recommended Extensions

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "streetsidesoftware.code-spell-checker",
    "eamodio.gitlens"
  ]
}
```

#### Workspace Settings

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### PyCharm

1. Open project as Python project
2. Configure Python interpreter to use virtual environment
3. Enable Node.js support
4. Configure code style settings

## Common Development Tasks

### 1. Adding a New Agent

```bash
# Create agent file
touch claude_pm/agents/my_new_agent.md

# Add agent metadata and implementation
# See agent-development.md for details

# Register in agent registry
# Update tests
```

### 2. Adding a New Service

```python
# Create service file
# claude_pm/services/my_service.py

from claude_pm.core.base_service import BaseService

class MyService(BaseService):
    """New service implementation."""
    
    async def initialize(self):
        """Initialize service."""
        pass
    
    async def execute(self, **kwargs):
        """Execute service logic."""
        pass
```

### 3. Adding CLI Commands

```javascript
// Add to claude_pm/cmpm_commands.py
def my_command(args):
    """New command implementation."""
    pass

# Register in CLI parser
```

## Troubleshooting

### Common Issues

#### 1. Python Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in development mode
pip install -e .

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

#### 2. Node.js Module Issues

```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force
```

#### 3. Permission Errors

```bash
# Fix file permissions
chmod +x bin/claude-pm
chmod +x scripts/*.sh

# Fix npm permissions (global install)
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
```

### Debug Mode

```bash
# Enable debug logging
export CLAUDE_PM_DEBUG=true
export CLAUDE_PM_LOG_LEVEL=debug

# Run with verbose output
claude-pm --verbose
claude-pm --debug
```

## Performance Profiling

### Python Profiling

```bash
# Profile Python code
python -m cProfile -o profile.stats your_script.py

# Analyze profile
python -m pstats profile.stats
```

### Node.js Profiling

```bash
# Profile Node.js code
node --prof your_script.js

# Process profile
node --prof-process isolate-*.log > profile.txt
```

## Development Best Practices

### 1. Code Style
- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript
- Write clear, self-documenting code
- Add inline comments for complex logic

### 2. Testing
- Write tests for new features
- Maintain test coverage >80%
- Test edge cases and error conditions
- Use meaningful test descriptions

### 3. Documentation
- Update documentation with changes
- Include code examples
- Document breaking changes
- Add inline documentation

### 4. Performance
- Profile before optimizing
- Use caching appropriately
- Minimize file I/O operations
- Lazy load when possible

## Next Steps

- Read the [Contributing Guide](./contributing.md) for contribution guidelines
- Review [Agent Development](./agent-development.md) for creating agents
- Check [API Reference](./api-reference.md) for detailed API documentation
- See [Testing Guide](./testing.md) for testing strategies

---

*For questions or issues, see the [Debugging Guide](./debugging.md) or open a GitHub issue.*