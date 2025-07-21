# Claude PM Framework Migration FAQ

## 🤔 Frequently Asked Questions About PyPI Migration

### General Questions

#### Q: Why is the framework moving away from editable installations?

**A:** The migration to PyPI installations provides several critical benefits:
- **Consistency**: Every user gets the same tested version
- **Reliability**: No more "works on my machine" issues
- **Performance**: 50% faster startup times with optimized package loading
- **Security**: Verified packages with integrity checks
- **Simplicity**: Standard Python package management tools

#### Q: When will editable installations stop working?

**A:** We follow a phased deprecation approach:
- **Now - v1.4.0**: Full compatibility with deprecation warnings
- **v1.4.0 - v2.0.0**: Limited support, stronger warnings
- **v2.0.0+**: Editable support removed completely

You have approximately 6 months to migrate at your convenience.

#### Q: Will this affect my existing projects?

**A:** No! Your existing projects will continue to work:
- All project configurations remain unchanged
- Agent definitions stay in the same locations
- Memory and logs are preserved
- Full backward compatibility during transition

---

### Technical Questions

#### Q: What's the difference between editable and PyPI installation?

**A:** 

| Aspect | Editable Installation | PyPI Installation |
|--------|----------------------|-------------------|
| **Install Command** | `pip install -e .` | `pip install claude-multiagent-pm` |
| **Location** | Your local directory | Python site-packages |
| **Updates** | Manual git pull | `pip install --upgrade` |
| **Modifications** | Direct code editing | Package immutable |
| **Performance** | Slower startup | Optimized loading |

#### Q: How do I check which installation type I'm using?

**A:** Run this command:
```bash
pip show claude-multiagent-pm | grep -E "Location|Editable"
```

- If you see "Editable project location": You're using editable mode (deprecated)
- If you only see "Location": You're using PyPI installation (good!)

#### Q: Can I use both installations simultaneously?

**A:** No, this can cause conflicts. You should:
1. Uninstall all existing versions
2. Choose one installation method
3. Stick with PyPI for production use

---

### Migration Process Questions

#### Q: What exactly does the migration script do?

**A:** The migration script (`scripts/migrate_to_pypi.py`) performs these steps:

1. **Detection Phase**
   - Checks current installation type
   - Identifies user data locations

2. **Backup Phase**
   - Creates timestamped backup of ~/.claude-pm
   - Saves migration metadata

3. **Uninstall Phase**
   - Removes editable installation
   - Clears Python cache

4. **Install Phase**
   - Installs from PyPI
   - Handles system-specific flags

5. **Verification Phase**
   - Tests import functionality
   - Validates CLI availability

#### Q: What if the migration fails?

**A:** The script creates automatic backups. To recover:

```bash
# Find your backup
ls ~/.claude-pm/migration_backups/

# Restore (replace timestamp with your backup)
cp -r ~/.claude-pm/migration_backups/20250120_123456/* ~/.claude-pm/

# Reinstall editable version temporarily
cd ~/Projects/claude-multiagent-pm
pip install -e .
export CLAUDE_PM_SOURCE_MODE=deprecated
```

#### Q: Can I migrate without the script?

**A:** Yes! Manual migration is simple:

```bash
# 1. Uninstall editable
pip uninstall -y claude-multiagent-pm

# 2. Install from PyPI
pip install claude-multiagent-pm

# 3. Verify
claude-pm --version
```

---

### Troubleshooting Questions

#### Q: I'm getting "externally-managed-environment" errors

**A:** Modern Linux distributions (Ubuntu 23.04+, Debian 12+) protect system Python. Solutions:

1. **Use --break-system-packages flag:**
   ```bash
   pip install --user --break-system-packages claude-multiagent-pm
   ```

2. **Use pipx (recommended):**
   ```bash
   pipx install claude-multiagent-pm
   ```

3. **Use virtual environment:**
   ```bash
   python -m venv claude-env
   source claude-env/bin/activate
   pip install claude-multiagent-pm
   ```

#### Q: The CLI command isn't found after migration

**A:** The command is installed but not in your PATH:

1. **Add to PATH (permanent fix):**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Use full path (temporary):**
   ```bash
   ~/.local/bin/claude-pm --version
   ```

3. **Use Python module:**
   ```bash
   python -m claude_pm.cli
   ```

#### Q: I'm seeing deprecation warnings even after migration

**A:** This usually means remnants of the old installation:

1. **Check for multiple installations:**
   ```bash
   pip list | grep claude-multiagent-pm
   which -a claude-pm
   ```

2. **Clean uninstall and reinstall:**
   ```bash
   pip uninstall -y claude-multiagent-pm
   pip cache purge
   find ~ -name "claude_pm*.egg-link" -delete
   pip install claude-multiagent-pm
   ```

3. **Check Python path:**
   ```bash
   python -c "import claude_pm; print(claude_pm.__file__)"
   ```

---

### Development Questions

#### Q: I'm a contributor. How do I develop without warnings?

**A:** Set the deprecation acknowledgment environment variable:

```bash
# Add to your shell configuration
export CLAUDE_PM_SOURCE_MODE=deprecated

# Or set it per-session
CLAUDE_PM_SOURCE_MODE=deprecated claude-pm
```

#### Q: How do I test both installation types?

**A:** Use separate virtual environments:

```bash
# Test PyPI installation
python -m venv test-pypi
source test-pypi/bin/activate
pip install claude-multiagent-pm
claude-pm --version
deactivate

# Test editable installation
python -m venv test-editable
source test-editable/bin/activate
cd ~/Projects/claude-multiagent-pm
pip install -e .
export CLAUDE_PM_SOURCE_MODE=deprecated
claude-pm --version
```

#### Q: Will my pull requests still work?

**A:** Yes! The development workflow remains the same:
- Fork and clone as usual
- Use editable install for development
- Set deprecation environment variable
- Submit PRs normally

---

### Data and Configuration Questions

#### Q: What happens to my custom agents?

**A:** All custom agents are preserved:
- User agents: `~/.claude-pm/agents/user-defined/`
- Project agents: `.claude-pm/agents/project-specific/`
- No changes to agent file locations
- Full compatibility maintained

#### Q: Will my API keys and configurations transfer?

**A:** Yes! All configurations are preserved:
- API keys remain in the same location
- Environment variables unchanged
- Config files stay in ~/.claude-pm/config/
- No manual reconfiguration needed

#### Q: What about my project memory and logs?

**A:** Everything is preserved:
- Memory data: `~/.claude-pm/memory/`
- Logs: `~/.claude-pm/logs/`
- Project history maintained
- No data loss during migration

---

### Platform-Specific Questions

#### Q: Does this affect Windows users differently?

**A:** Windows users may need slight adjustments:

1. **Use pip with --user flag:**
   ```cmd
   pip install --user claude-multiagent-pm
   ```

2. **Add to PATH:**
   ```cmd
   setx PATH "%PATH%;%APPDATA%\Python\Scripts"
   ```

3. **Use py launcher:**
   ```cmd
   py -m claude_pm.cli
   ```

#### Q: What about macOS with Homebrew Python?

**A:** Homebrew Python users should:

1. **Avoid sudo:**
   ```bash
   pip install --user claude-multiagent-pm
   ```

2. **Check PATH includes:**
   ```bash
   export PATH="$HOME/Library/Python/3.x/bin:$PATH"
   ```

3. **Or use pipx:**
   ```bash
   brew install pipx
   pipx install claude-multiagent-pm
   ```

#### Q: Linux package manager conflicts?

**A:** For system-managed Python:

1. **Use --break-system-packages:**
   ```bash
   pip install --user --break-system-packages claude-multiagent-pm
   ```

2. **Or use pipx (recommended):**
   ```bash
   sudo apt install pipx  # or equivalent
   pipx install claude-multiagent-pm
   ```

---

### Future Questions

#### Q: What new features will PyPI-only version have?

**A:** PyPI distribution enables:
- Faster startup and improved performance
- Better dependency management
- Automatic security updates
- Cross-platform wheel distributions
- Integration with enterprise package managers

#### Q: Will prices or licensing change?

**A:** No! The framework remains:
- Open source under the same license
- Free to use for all users
- No paid tiers or restrictions
- Community-driven development

#### Q: How can I help with the migration?

**A:** You can help by:
- Testing the PyPI installation
- Reporting migration issues
- Updating documentation
- Helping other users migrate
- Contributing to migration tools

---

## 🆘 Still Need Help?

If your question isn't answered here:

1. **Check the full migration guide**: [MIGRATION.md](./MIGRATION.md)
2. **Search existing issues**: [GitHub Issues](https://github.com/bobmatnyc/claude-multiagent-pm/issues)
3. **Ask the community**: [GitHub Discussions](https://github.com/bobmatnyc/claude-multiagent-pm/discussions)
4. **Run diagnostics**: `claude-pm health --verbose`

Remember: The migration is designed to be smooth and preserve all your work. Take your time, and don't hesitate to ask for help!

---

*Last updated: January 2025 | Framework Version: 1.3.0*