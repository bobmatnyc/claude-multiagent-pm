# Claude PM Troubleshooting Guide

## Common Issues and Solutions

### ModuleNotFoundError: No module named 'frontmatter'

**Problem**: When trying to import AgentRegistry or other components, you may encounter:
```
ModuleNotFoundError: No module named 'frontmatter'
```

**Cause**: The `python-frontmatter` and `mistune` dependencies were not included in earlier versions of the npm package installation process.

**Solution**:

1. **For new installations**: The dependencies are now included in the installation process and will be installed automatically.

2. **For existing installations**: Run the missing dependencies installer:
   ```bash
   npm run install:missing-deps
   ```
   
   Or manually:
   ```bash
   python3 scripts/install_missing_dependencies.py
   ```

3. **Alternative manual installation**:
   ```bash
   pip install --user python-frontmatter>=1.0.0 mistune>=3.0.0
   ```

   If you encounter "externally-managed-environment" errors:
   ```bash
   pip install --user --break-system-packages python-frontmatter>=1.0.0 mistune>=3.0.0
   ```

### Other Missing Dependencies

The framework requires several Python packages. If you encounter import errors for any of these modules:
- click
- rich
- pydantic
- yaml (pyyaml)
- dotenv (python-dotenv)
- requests
- openai
- aiohttp
- httpx
- typer
- toml
- psutil
- pathspec

Run the missing dependencies installer as shown above, or install all base requirements:
```bash
pip install -r requirements/base.txt
```

### Verifying Installation

After fixing dependencies, verify the installation:
```bash
claude-pm --version
python3 -c "from claude_pm.core.agent_registry import AgentRegistry; print('AgentRegistry OK')"
```

Both commands should execute without errors.