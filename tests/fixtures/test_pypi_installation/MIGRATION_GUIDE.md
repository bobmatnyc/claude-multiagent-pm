# Claude PM Framework Migration Guide: Editable Installation to PyPI

## 🚀 Quick Start

If you're seeing deprecation warnings, migrate now with one command:

```bash
cd ~/Projects/claude-multiagent-pm
python scripts/migrate_to_pypi.py
```

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Migrate?](#why-migrate)
3. [Deprecation Timeline](#deprecation-timeline)
4. [Migration Methods](#migration-methods)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [FAQ](#frequently-asked-questions)
7. [Developer Guide](#developer-guide)
8. [Support](#support)

---

## Overview

Starting with version 1.3.0, the Claude Multi-Agent PM Framework is transitioning from editable (source) installations to PyPI package installations. This migration ensures better reliability, performance, and compatibility across all environments.

### What's Changing?

- **Old Method**: Installing from source with `pip install -e .`
- **New Method**: Installing from PyPI with `pip install claude-multiagent-pm`

---

## Why Migrate?

### 🎯 Key Benefits

1. **🚀 Improved Performance**
   - Optimized package loading (up to 50% faster startup)
   - Reduced memory footprint
   - Better dependency caching

2. **🔒 Enhanced Security**
   - Verified package integrity through PyPI
   - Consistent checksums and signatures
   - No risk of local modifications affecting behavior

3. **🛠️ Better Reliability**
   - Consistent behavior across machines
   - No path detection issues
   - Simplified troubleshooting

4. **📦 Standard Package Management**
   - Easy updates with `pip install --upgrade`
   - Works with pip, pipx, poetry, and other tools
   - Automatic dependency resolution

5. **🌍 Cross-Platform Compatibility**
   - Consistent installation on Windows, macOS, and Linux
   - No platform-specific path issues
   - Better CI/CD integration

---

## Deprecation Timeline

### Phase 1: v1.3.0 (Current Release)
- ⚠️ Deprecation warnings introduced
- ✅ Full backward compatibility maintained
- 📢 Migration tools and guides provided

### Phase 2: v1.4.0 (Q2 2025)
- 🚨 Stronger deprecation warnings
- ⚡ Limited support for editable mode
- 🔧 Enhanced PyPI features

### Phase 3: v2.0.0 (Q3 2025)
- ❌ Editable mode support removed
- 🎯 PyPI-only distribution
- 🚀 New features exclusive to PyPI version

---

## Migration Methods

### Method 1: Automated Migration (Recommended) 🤖

Our migration script handles everything automatically:

```bash
cd ~/Projects/claude-multiagent-pm
python scripts/migrate_to_pypi.py
```

**What the script does:**
1. ✅ Backs up your user data and configurations
2. ✅ Uninstalls the editable installation
3. ✅ Installs from PyPI
4. ✅ Verifies the installation
5. ✅ Provides post-migration instructions

### Method 2: Manual Migration 🔧

For users who prefer manual control:

```bash
# Step 1: Backup your data (optional but recommended)
cp -r ~/.claude-pm ~/.claude-pm.backup-$(date +%Y%m%d)

# Step 2: Uninstall editable version
pip uninstall -y claude-multiagent-pm

# Step 3: Install from PyPI
pip install --user claude-multiagent-pm

# Step 4: Verify installation
claude-pm --version

# Step 5: Reinitialize if needed
claude-pm init
```

### Method 3: Fresh Installation 🆕

If you don't have custom configurations to preserve:

```bash
# Step 1: Remove all versions
pip uninstall -y claude-multiagent-pm
npm uninstall -g @bobmatnyc/claude-multiagent-pm

# Step 2: Clean configuration (optional)
rm -rf ~/.claude-pm

# Step 3: Install from npm (includes PyPI package)
npm install -g @bobmatnyc/claude-multiagent-pm

# Step 4: Initialize
claude-pm init
```

---

## Common Issues & Solutions

### 🔴 Issue: Deprecation Warnings Still Appearing

**Symptoms:**
```
⚠️  DEPRECATION WARNING: Editable installation detected
```

**Solutions:**

1. **Verify installation type:**
   ```bash
   pip show claude-multiagent-pm | grep -E "Location|Editable"
   ```

2. **Force reinstall from PyPI:**
   ```bash
   pip uninstall -y claude-multiagent-pm
   pip cache purge
   pip install --force-reinstall claude-multiagent-pm
   ```

3. **Temporary suppression (development only):**
   ```bash
   export CLAUDE_PM_SOURCE_MODE=deprecated
   ```

### 🔴 Issue: Import Errors After Migration

**Symptoms:**
```python
ImportError: No module named 'claude_pm'
```

**Solutions:**

1. **Clear Python cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
   find . -name "*.pyc" -delete
   ```

2. **Verify Python path:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

3. **Reinstall with user flag:**
   ```bash
   pip install --user --force-reinstall claude-multiagent-pm
   ```

### 🔴 Issue: CLI Command Not Found

**Symptoms:**
```bash
claude-pm: command not found
```

**Solutions:**

1. **Add pip user bin to PATH:**
   ```bash
   # For bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   
   # For zsh
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

2. **Check installation location:**
   ```bash
   pip show -f claude-multiagent-pm | grep claude-pm
   ```

3. **Use Python module directly:**
   ```bash
   python -m claude_pm.cli
   ```

### 🔴 Issue: Permission Errors

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solutions:**

1. **Use user installation:**
   ```bash
   pip install --user claude-multiagent-pm
   ```

2. **For managed environments (Ubuntu 23.04+, Debian 12+):**
   ```bash
   pip install --user --break-system-packages claude-multiagent-pm
   ```

3. **Use virtual environment:**
   ```bash
   python -m venv claude-pm-env
   source claude-pm-env/bin/activate
   pip install claude-multiagent-pm
   ```

### 🔴 Issue: Version Conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages
```

**Solutions:**

1. **Update pip first:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Use constraint file:**
   ```bash
   pip install claude-multiagent-pm --constraint requirements.txt
   ```

3. **Clean install in virtual environment:**
   ```bash
   python -m venv clean-env
   source clean-env/bin/activate
   pip install claude-multiagent-pm
   ```

---

## Frequently Asked Questions

### ❓ Will I lose my custom agents and configurations?

**No!** The migration process preserves:
- ✅ User-defined agents (`~/.claude-pm/agents/user-defined/`)
- ✅ Project-specific agents (`~/.claude-pm/agents/project-specific/`)
- ✅ Configuration files (`~/.claude-pm/config/`)
- ✅ Memory data (`~/.claude-pm/memory/`)
- ✅ Logs and history

### ❓ Can I still contribute to the project?

**Yes!** For development:
```bash
# Clone for development
git clone https://github.com/yourusername/claude-multiagent-pm.git
cd claude-multiagent-pm

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Acknowledge deprecation for development
export CLAUDE_PM_SOURCE_MODE=deprecated
```

### ❓ What if I need to rollback?

The migration script creates backups:
```bash
# Find your backup
ls ~/.claude-pm/migration_backups/

# Restore if needed
cp -r ~/.claude-pm/migration_backups/[timestamp]/* ~/.claude-pm/
```

### ❓ How do I know which version I'm using?

Check your installation type:
```bash
# Show installation details
pip show claude-multiagent-pm

# Check for "Editable project location" line
# If present: You're using editable mode (deprecated)
# If absent: You're using PyPI version (good!)
```

### ❓ What about my existing projects?

Your projects will continue to work! The framework maintains full backward compatibility during the transition period.

---

## Developer Guide

### For Contributors

If you're contributing to the framework:

```bash
# 1. Fork and clone the repository
git clone https://github.com/yourusername/claude-multiagent-pm.git
cd claude-multiagent-pm

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Set deprecation acknowledgment
export CLAUDE_PM_SOURCE_MODE=deprecated

# 5. Install pre-commit hooks
pre-commit install

# 6. Run tests
pytest tests/
```

### For Package Maintainers

Building and testing the PyPI package:

```bash
# Build the package
python -m build

# Test installation locally
pip install dist/claude_multiagent_pm-*.whl

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test from TestPyPI
pip install --index-url https://test.pypi.org/simple/ claude-multiagent-pm
```

---

## Support

### Getting Help

1. **📖 Documentation**: Check our [comprehensive docs](https://github.com/bobmatnyc/claude-multiagent-pm/docs)
2. **🐛 Issues**: Report problems on [GitHub Issues](https://github.com/bobmatnyc/claude-multiagent-pm/issues)
3. **💬 Discussions**: Join our [GitHub Discussions](https://github.com/bobmatnyc/claude-multiagent-pm/discussions)
4. **🔍 Diagnostics**: Run `claude-pm health` for system diagnostics

### Diagnostic Commands

```bash
# Check system health
claude-pm health

# Verify installation
claude-pm init --verify

# View logs
ls -la ~/.claude-pm/logs/

# Test agent discovery
python -c "from claude_pm.core.agent_registry import AgentRegistry; print(AgentRegistry().listAgents())"
```

### Reporting Issues

When reporting migration issues, please include:

1. Output of `pip show claude-multiagent-pm`
2. Output of `claude-pm --version`
3. Your operating system and Python version
4. Any error messages
5. Migration log from `~/.claude-pm/migration_backups/*/migration_info.json`

---

## Thank You! 🎉

Thank you for being part of the Claude PM Framework community and for migrating to the PyPI distribution. This change ensures a more reliable and performant experience for all users.

**Happy orchestrating with Claude PM Framework!** 🚀

---

*Last updated: January 2025 | Framework Version: 1.3.0*