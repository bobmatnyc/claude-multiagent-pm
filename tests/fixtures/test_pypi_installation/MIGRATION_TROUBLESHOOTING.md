# Claude PM Framework Migration Troubleshooting Guide

## 🚨 Quick Diagnosis

Run this command first to diagnose your installation:

```bash
python -c "
import subprocess, sys, os
print('=== Claude PM Installation Diagnosis ===')
print(f'Python: {sys.version}')
print(f'Platform: {sys.platform}')
print(f'PATH: {os.environ.get(\"PATH\", \"Not set\")}')
print('\n--- Pip Show ---')
subprocess.run([sys.executable, '-m', 'pip', 'show', 'claude-multiagent-pm'])
print('\n--- Import Test ---')
try:
    import claude_pm
    print(f'✅ Import successful: {claude_pm.__file__}')
except ImportError as e:
    print(f'❌ Import failed: {e}')
print('\n--- CLI Test ---')
subprocess.run(['which', 'claude-pm'])
"
```

---

## 🔧 Common Migration Issues

### Issue 1: Deprecation Warnings Won't Go Away

**Symptoms:**
```
⚠️  DEPRECATION WARNING: Editable installation detected
You are running Claude PM from a source directory installation.
```

**Root Causes & Solutions:**

1. **Multiple installations exist:**
   ```bash
   # Find all installations
   pip list | grep claude-multiagent-pm
   find ~ -name "claude_pm" -type d 2>/dev/null | grep -E "(site-packages|Projects)"
   
   # Clean uninstall everything
   pip uninstall -y claude-multiagent-pm
   pip cache purge
   
   # Remove egg-link files
   find ~ -name "claude-multiagent-pm.egg-link" -delete
   
   # Fresh install
   pip install claude-multiagent-pm
   ```

2. **Old PATH configuration:**
   ```bash
   # Check your PATH
   echo $PATH | tr ':' '\n' | grep -E "(claude|Projects)"
   
   # Remove old paths from ~/.bashrc or ~/.zshrc
   # Remove lines like:
   # export PATH="$HOME/Projects/claude-multiagent-pm/bin:$PATH"
   ```

3. **Cached Python bytecode:**
   ```bash
   # Clear all Python cache
   find ~ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find ~ -name "*.pyc" -delete
   find ~ -name "*.pyo" -delete
   ```

---

### Issue 2: Command Not Found After Migration

**Symptoms:**
```bash
$ claude-pm
bash: claude-pm: command not found
```

**Root Causes & Solutions:**

1. **PATH not updated:**
   ```bash
   # Find where pip installed the script
   pip show -f claude-multiagent-pm | grep -E "bin/claude-pm|scripts/claude-pm"
   
   # Add to PATH (choose based on your shell)
   # For bash:
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   
   # For zsh:
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   
   # For fish:
   set -U fish_user_paths $HOME/.local/bin $fish_user_paths
   ```

2. **Wrong Python environment:**
   ```bash
   # Check which Python you're using
   which python
   which python3
   
   # Ensure pip matches Python
   python -m pip show claude-multiagent-pm
   ```

3. **Installation location issues:**
   ```bash
   # Use Python module directly as workaround
   python -m claude_pm.cli
   
   # Create alias for convenience
   echo 'alias claude-pm="python -m claude_pm.cli"' >> ~/.bashrc
   ```

---

### Issue 3: Import Errors in Python Scripts

**Symptoms:**
```python
ImportError: No module named 'claude_pm'
# or
ModuleNotFoundError: No module named 'claude_pm'
```

**Root Causes & Solutions:**

1. **Virtual environment mismatch:**
   ```bash
   # Check if you're in a virtual environment
   which python
   
   # If in venv, install there
   pip install claude-multiagent-pm
   
   # Or deactivate and use system Python
   deactivate
   pip install --user claude-multiagent-pm
   ```

2. **PYTHONPATH issues:**
   ```bash
   # Check PYTHONPATH
   echo $PYTHONPATH
   
   # Remove old source paths
   # Remove from ~/.bashrc or ~/.zshrc:
   # export PYTHONPATH="$HOME/Projects/claude-multiagent-pm:$PYTHONPATH"
   
   # Verify Python can find the package
   python -c "import sys; print('\n'.join(sys.path))"
   ```

3. **Incomplete installation:**
   ```bash
   # Force reinstall with dependencies
   pip install --force-reinstall --no-cache-dir claude-multiagent-pm
   
   # Verify all files installed
   pip show -f claude-multiagent-pm | less
   ```

---

### Issue 4: Permission Denied Errors

**Symptoms:**
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Root Causes & Solutions:**

1. **System Python protection (Ubuntu/Debian):**
   ```bash
   # Option 1: Use --break-system-packages
   pip install --user --break-system-packages claude-multiagent-pm
   
   # Option 2: Use pipx (recommended)
   sudo apt install pipx
   pipx install claude-multiagent-pm
   
   # Option 3: Use virtual environment
   python -m venv ~/claude-pm-env
   source ~/claude-pm-env/bin/activate
   pip install claude-multiagent-pm
   ```

2. **macOS System Integrity Protection:**
   ```bash
   # Never use sudo with pip
   # Instead, use --user flag
   pip install --user claude-multiagent-pm
   
   # Or use Homebrew Python
   brew install python@3.11
   /usr/local/bin/python3.11 -m pip install claude-multiagent-pm
   ```

3. **Windows administrator issues:**
   ```cmd
   # Run as regular user with --user
   pip install --user claude-multiagent-pm
   
   # Add Scripts to PATH
   setx PATH "%PATH%;%APPDATA%\Python\Python311\Scripts"
   ```

---

### Issue 5: Version Conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Root Causes & Solutions:**

1. **Outdated pip:**
   ```bash
   # Upgrade pip first
   python -m pip install --upgrade pip
   
   # Then install
   pip install claude-multiagent-pm
   ```

2. **Conflicting dependencies:**
   ```bash
   # Install in isolated environment
   pip install --force-reinstall --no-deps claude-multiagent-pm
   pip install claude-multiagent-pm  # To get dependencies
   
   # Or use constraints file
   pip install claude-multiagent-pm --constraint requirements.txt
   ```

3. **Old package versions:**
   ```bash
   # Clean install
   pip list | grep claude > old-packages.txt
   pip uninstall -y claude-multiagent-pm
   pip cache purge
   pip install claude-multiagent-pm
   ```

---

### Issue 6: npm/Node.js Integration Issues

**Symptoms:**
```
npm WARN claude-multiagent-pm@1.3.0 requires a peer of python@>=3.8
```

**Root Causes & Solutions:**

1. **npm postinstall failures:**
   ```bash
   # Install Python package separately
   pip install claude-multiagent-pm
   
   # Then install npm package without scripts
   npm install -g @bobmatnyc/claude-multiagent-pm --ignore-scripts
   ```

2. **Global npm permissions:**
   ```bash
   # Configure npm to use user directory
   npm config set prefix ~/.npm-global
   echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   
   # Reinstall
   npm install -g @bobmatnyc/claude-multiagent-pm
   ```

---

## 🔍 Advanced Debugging

### Debug Installation Details

```bash
# Create diagnostic report
cat > diagnose_claude_pm.py << 'EOF'
import sys
import os
import subprocess
import json
from pathlib import Path

def diagnose():
    report = {
        "python_version": sys.version,
        "platform": sys.platform,
        "path_entries": sys.path,
        "env_vars": {
            "PATH": os.environ.get("PATH", "").split(":"),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "").split(":") if os.environ.get("PYTHONPATH") else [],
            "CLAUDE_PM_SOURCE_MODE": os.environ.get("CLAUDE_PM_SOURCE_MODE", "not set")
        }
    }
    
    # Check pip installation
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "claude-multiagent-pm"],
            capture_output=True, text=True
        )
        report["pip_show"] = result.stdout
        report["is_editable"] = "Editable project location" in result.stdout
    except Exception as e:
        report["pip_show_error"] = str(e)
    
    # Check import
    try:
        import claude_pm
        report["import_success"] = True
        report["package_location"] = claude_pm.__file__
    except ImportError as e:
        report["import_success"] = False
        report["import_error"] = str(e)
    
    # Check CLI
    try:
        cli_path = subprocess.run(
            ["which", "claude-pm"],
            capture_output=True, text=True
        ).stdout.strip()
        report["cli_path"] = cli_path or "not found"
    except:
        report["cli_path"] = "error checking"
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    diagnose()
EOF

python diagnose_claude_pm.py > claude_pm_diagnosis.json
cat claude_pm_diagnosis.json
```

### Check for Conflicting Installations

```bash
# Find all Claude PM related files
find ~ -name "*claude*pm*" -type f 2>/dev/null | grep -E "(bin/|scripts/)" | sort

# Check all Python site-packages
python -c "import site; print('\n'.join(site.getsitepackages()))"

# Look for egg-link files
find ~ -name "*.egg-link" 2>/dev/null | grep claude
```

### Test Installation Methods

```bash
# Test 1: Direct module execution
python -c "import claude_pm; print(claude_pm.__version__)"

# Test 2: CLI via Python
python -m claude_pm.cli --version

# Test 3: Direct CLI
claude-pm --version

# Test 4: Full path CLI
~/.local/bin/claude-pm --version
```

---

## 💊 Quick Fixes

### Nuclear Option: Complete Clean Reinstall

```bash
#!/bin/bash
# Save this as clean_reinstall.sh

echo "🧹 Cleaning all Claude PM installations..."

# Uninstall all versions
pip uninstall -y claude-multiagent-pm
npm uninstall -g @bobmatnyc/claude-multiagent-pm

# Remove all caches
pip cache purge
find ~ -name "*.pyc" -delete 2>/dev/null
find ~ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find ~ -name "*claude*pm*.egg-link" -delete 2>/dev/null

# Remove old source paths from shell config
sed -i.bak '/claude-multiagent-pm/d' ~/.bashrc ~/.zshrc 2>/dev/null

# Fresh install
echo "📦 Installing fresh from PyPI..."
pip install --user claude-multiagent-pm

echo "✅ Complete! Restart your terminal and run: claude-pm --version"
```

### Environment Variable Reset

```bash
# Add to ~/.bashrc or ~/.zshrc
unset PYTHONPATH
unset CLAUDE_PM_SOURCE_MODE
export PATH="$HOME/.local/bin:$PATH"
```

---

## 📞 Getting More Help

If issues persist after trying these solutions:

1. **Generate full diagnostic report:**
   ```bash
   claude-pm health --verbose > diagnostic_report.txt 2>&1
   ```

2. **Create GitHub issue with:**
   - Diagnostic report
   - Steps you've tried
   - Error messages
   - OS and Python version

3. **Join the discussion:**
   - [GitHub Discussions](https://github.com/bobmatnyc/claude-multiagent-pm/discussions)
   - Include your `claude_pm_diagnosis.json`

Remember: Most migration issues are related to leftover files from old installations. A clean uninstall/reinstall usually resolves them!

---

*Last updated: January 2025 | Framework Version: 1.3.0*