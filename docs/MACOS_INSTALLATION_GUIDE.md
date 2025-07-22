# macOS Installation Guide for Claude PM Framework

This guide provides comprehensive installation instructions for macOS users, particularly addressing the common "externally-managed-environment" error when using Homebrew Python.

## Table of Contents
- [Quick Start](#quick-start)
- [Understanding the Error](#understanding-the-error)
- [Installation Methods](#installation-methods)
  - [Method 1: pipx (Recommended)](#method-1-pipx-recommended)
  - [Method 2: Virtual Environment](#method-2-virtual-environment)
  - [Method 3: User Installation](#method-3-user-installation)
- [Quick Installation Script](#quick-installation-script)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

## Quick Start

For most macOS users with Homebrew Python, use pipx:

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install Claude PM Framework
pipx install @bobmatnyc/claude-multiagent-pm

# Run Claude PM
claude-pm
```

## Understanding the Error

When installing on macOS with Homebrew Python, you may encounter:

```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.

    If you wish to install a Python library that isn't in Homebrew,
    use a virtual environment:

    python3 -m venv path/to/venv
    source path/to/venv/bin/activate
    python3 -m pip install xyz
```

This error occurs because Homebrew Python follows [PEP 668](https://peps.python.org/pep-0668/), which prevents pip from installing packages globally to avoid conflicts with system package managers.

## Installation Methods

### Method 1: pipx (Recommended)

pipx is the recommended tool for installing Python CLI applications on macOS. It automatically creates isolated environments for each application.

```bash
# Step 1: Install pipx
brew install pipx
pipx ensurepath

# Step 2: Restart your terminal or reload PATH
source ~/.zshrc  # or ~/.bashrc

# Step 3: Install Claude PM Framework
pipx install @bobmatnyc/claude-multiagent-pm

# Step 4: Verify installation
claude-pm --version
```

**Advantages:**
- Automatic isolation from system Python
- Easy updates with `pipx upgrade`
- Clean uninstall with `pipx uninstall`
- No manual environment management

### Method 2: Virtual Environment

Create a dedicated virtual environment for Claude PM:

```bash
# Step 1: Create a virtual environment
python3 -m venv ~/claude-pm-env

# Step 2: Activate the environment
source ~/claude-pm-env/bin/activate

# Step 3: Install Claude PM Framework
pip install @bobmatnyc/claude-multiagent-pm

# Step 4: Create an alias for easy access
echo 'alias claude-pm="source ~/claude-pm-env/bin/activate && claude-pm"' >> ~/.zshrc
source ~/.zshrc

# Step 5: Use Claude PM
claude-pm --version
```

**Note:** You'll need to activate the environment each time or use the alias.

### Method 3: User Installation

Install to your user directory without affecting system packages:

```bash
# Option A: Force user installation (if pip supports it)
pip install --user @bobmatnyc/claude-multiagent-pm

# Option B: Break system packages flag (use with caution)
pip install --user --break-system-packages @bobmatnyc/claude-multiagent-pm

# Add user bin to PATH if not already there
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
claude-pm --version
```

**Warning:** The `--break-system-packages` flag should be used cautiously as it bypasses important safety mechanisms.

## Quick Installation Script

Save this as `install-claude-pm-macos.sh`:

```bash
#!/bin/bash

echo "Claude PM Framework macOS Installer"
echo "==================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is not installed. Please install from https://brew.sh"
    exit 1
fi

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    brew install pipx
    pipx ensurepath
    echo "Please restart your terminal and run this script again."
    exit 0
fi

# Install Claude PM Framework
echo "Installing Claude PM Framework..."
pipx install @bobmatnyc/claude-multiagent-pm

# Verify installation
if command -v claude-pm &> /dev/null; then
    echo "✅ Installation successful!"
    echo "Claude PM version: $(claude-pm --version)"
    echo ""
    echo "Next steps:"
    echo "1. cd to your project directory"
    echo "2. Run: claude-pm"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
```

Make it executable and run:
```bash
chmod +x install-claude-pm-macos.sh
./install-claude-pm-macos.sh
```

## Troubleshooting

### pipx: command not found

If pipx isn't in your PATH after installation:

```bash
# For zsh (default on modern macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Python Dependencies

If you encounter missing Python dependencies after installation:

```bash
# With pipx
pipx inject claude-multiagent-pm python-frontmatter mistune click rich pydantic

# With virtual environment (activate it first)
pip install python-frontmatter mistune click rich pydantic pyyaml python-dotenv
```

### Permission Errors

If you get permission errors:

```bash
# Check directory permissions
ls -la ~/.local/bin
ls -la ~/.local/pipx

# Fix permissions if needed
chmod 755 ~/.local/bin
chmod 755 ~/.local/pipx
```

### Multiple Python Versions

If you have multiple Python versions:

```bash
# Use specific Python version with pipx
pipx install --python python3.11 @bobmatnyc/claude-multiagent-pm

# Use specific Python version with venv
python3.11 -m venv ~/claude-pm-env
```

## Verification

After installation, verify everything is working:

```bash
# Check CLI is accessible
claude-pm --version

# Test basic initialization
cd /tmp
mkdir test-claude-pm
cd test-claude-pm
claude-pm init

# Verify Python imports
python3 -c "from claude_pm.core.agent_registry import AgentRegistry; print('✅ AgentRegistry OK')"
python3 -c "import claude_pm; print(f'✅ Claude PM version: {claude_pm.__version__}')"
```

## Best Practices

1. **Use pipx for CLI tools**: It's designed specifically for Python command-line applications
2. **Keep environments isolated**: Don't mix project dependencies with CLI tools
3. **Regular updates**: Update with `pipx upgrade claude-multiagent-pm`
4. **Check compatibility**: Ensure your Python version is ≥ 3.8

## Additional Resources

- [pipx documentation](https://pypa.github.io/pipx/)
- [PEP 668 - Externally Managed Environments](https://peps.python.org/pep-0668/)
- [Claude PM Framework Documentation](../README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

If you continue to experience issues, please:
1. Check the [main troubleshooting guide](./TROUBLESHOOTING.md)
2. Open an issue with your specific error message
3. Include your macOS version and Python version (`python3 --version`)