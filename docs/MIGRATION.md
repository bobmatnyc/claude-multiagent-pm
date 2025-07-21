# Migration Guide: Editable Installation to PyPI

> **📌 Quick Links**
> - [Comprehensive Migration Guide](../test_pypi_installation/MIGRATION_GUIDE.md) - Detailed step-by-step guide
> - [Migration FAQ](../test_pypi_installation/MIGRATION_FAQ.md) - Frequently asked questions
> - [Troubleshooting Guide](../test_pypi_installation/MIGRATION_TROUBLESHOOTING.md) - Solutions to common issues

## Overview

Starting with version 1.3.0, the Claude Multi-Agent PM Framework is transitioning from editable (source) installations to PyPI package installations. This change improves:

- **Reliability**: Consistent package management across environments
- **Performance**: Optimized package loading and dependency resolution (50% faster startup)
- **Compatibility**: Better integration with Python packaging ecosystem
- **Security**: Verified package integrity and versioning

## Deprecation Timeline

- **v1.3.0** (January 2025 - Current): Deprecation warnings introduced, editable mode still supported
- **v1.4.0** (Q2 2025): Editable mode support limited, stronger warnings
- **v2.0.0** (Q3 2025): Editable mode support removed completely

> **⚠️ Action Required**: If you're seeing deprecation warnings, please migrate to PyPI installation within the next 6 months.

## Migration Methods

### Method 1: Automated Migration Script (Recommended)

```bash
cd ~/Projects/claude-multiagent-pm
python scripts/migrate_to_pypi.py
```

This script will:
1. Backup your user data (agents, configs, memory)
2. Uninstall the editable installation
3. Install from PyPI
4. Verify the installation
5. Provide post-migration instructions

### Method 2: Manual Migration

```bash
# 1. Backup your data (optional but recommended)
cp -r ~/.claude-pm ~/.claude-pm.backup

# 2. Uninstall editable version
pip uninstall claude-multiagent-pm

# 3. Install from PyPI
pip install claude-multiagent-pm

# 4. Verify installation
claude-pm --version
```

### Method 3: Fresh Installation

If you don't have custom configurations to preserve:

```bash
# 1. Uninstall all versions
pip uninstall claude-multiagent-pm
npm uninstall -g @bobmatnyc/claude-multiagent-pm

# 2. Clean install from npm (includes PyPI package)
npm install -g @bobmatnyc/claude-multiagent-pm

# 3. Initialize
claude-pm init
```

## Suppressing Deprecation Warnings

During the transition period, you can suppress warnings:

```bash
export CLAUDE_PM_SOURCE_MODE=deprecated
```

Add to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.) to make permanent.

## What Gets Migrated

### Preserved Data
- User-defined agents (`~/.claude-pm/agents/user-defined/`)
- Project-specific agents (`~/.claude-pm/agents/project-specific/`)
- Configuration files (`~/.claude-pm/config/`)
- Memory data (`~/.claude-pm/memory/`)
- Logs (`~/.claude-pm/logs/`)

### Not Migrated
- Source code modifications (use PyPI package as-is)
- Development tools and scripts
- Git history and branches
- Virtual environments

## Common Issues and Solutions

> **💡 For comprehensive troubleshooting**, see our [detailed troubleshooting guide](../test_pypi_installation/MIGRATION_TROUBLESHOOTING.md)

### Issue: Import Errors After Migration

**Solution**: Clear Python cache and reinstall

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
pip install --force-reinstall claude-multiagent-pm
```

### Issue: CLI Command Not Found

**Solution**: Ensure pip user bin directory is in PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Issue: Permission Errors

**Solution**: Use `--user` flag or `--break-system-packages` on newer systems

```bash
pip install --user claude-multiagent-pm
# or
pip install --user --break-system-packages claude-multiagent-pm
```

### Issue: Version Conflicts

**Solution**: Use virtual environment

```bash
python -m venv claude-pm-env
source claude-pm-env/bin/activate
pip install claude-multiagent-pm
```

### More Issues?

Check our comprehensive guides:
- [Migration FAQ](../test_pypi_installation/MIGRATION_FAQ.md) - Answers to common questions
- [Troubleshooting Guide](../test_pypi_installation/MIGRATION_TROUBLESHOOTING.md) - Detailed solutions

## Benefits of PyPI Installation

1. **Automatic Updates**: Easy version management with pip
2. **Dependency Resolution**: Proper handling of package dependencies
3. **Cross-Platform**: Consistent behavior across operating systems
4. **Package Integrity**: Verified checksums and signatures
5. **Standard Tooling**: Works with pip, pipx, poetry, etc.

## Development Workflow

For contributors who need source access:

```bash
# Clone for development
git clone https://github.com/yourusername/claude-multiagent-pm.git
cd claude-multiagent-pm

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode (for testing only)
pip install -e .

# Set environment variable to acknowledge deprecation
export CLAUDE_PM_SOURCE_MODE=deprecated
```

## Support

If you encounter issues during migration:

1. Check the [GitHub Issues](https://github.com/bobmatnyc/claude-multiagent-pm/issues)
2. Run the diagnostic command: `claude-pm health`
3. Review logs in `~/.claude-pm/logs/`
4. Contact support with migration logs

## Future Roadmap

- **v1.3.x**: Transition period with full backward compatibility
- **v1.4.x**: Enhanced PyPI features, reduced editable support
- **v2.0.0**: PyPI-only distribution, removal of legacy code

Thank you for migrating to the PyPI distribution!