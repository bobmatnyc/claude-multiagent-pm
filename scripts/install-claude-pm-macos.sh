#!/bin/bash

# Claude PM Framework macOS Quick Installer
# This script handles the common "externally-managed-environment" error
# by using pipx for installation

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║    Claude PM Framework macOS Installer       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Function to print colored output
print_status() {
    echo -e "\033[1;34m==>\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m✅\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m❌\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m⚠️\033[0m $1"
}

# Check OS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer is for macOS only. Detected OS: $OSTYPE"
    exit 1
fi

# Check if Homebrew is installed
print_status "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_error "Homebrew is not installed."
    echo "Please install Homebrew from https://brew.sh"
    echo ""
    echo "Run this command:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
else
    print_success "Homebrew found"
fi

# Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
    print_error "Python 3.8+ is required. Found: Python $PYTHON_VERSION"
    echo "Install a newer Python with: brew install python@3.11"
    exit 1
else
    print_success "Python $PYTHON_VERSION found"
fi

# Check if pipx is installed
print_status "Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    print_warning "pipx not found. Installing..."
    brew install pipx
    
    print_status "Setting up pipx PATH..."
    pipx ensurepath
    
    # Source the appropriate shell config
    if [[ -f "$HOME/.zshrc" ]]; then
        source "$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        source "$HOME/.bashrc"
    fi
    
    # Check if pipx is now available
    if ! command -v pipx &> /dev/null; then
        print_warning "pipx installed but not in PATH yet."
        echo ""
        echo "Please run these commands:"
        echo "  source ~/.zshrc  # or ~/.bashrc"
        echo "  ./install-claude-pm-macos.sh"
        echo ""
        echo "Or manually add to PATH:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        exit 0
    fi
else
    print_success "pipx found"
fi

# Check if Claude PM is already installed
if command -v claude-pm &> /dev/null; then
    print_warning "Claude PM Framework is already installed"
    echo "Current version: $(claude-pm --version 2>&1 || echo 'unknown')"
    echo ""
    read -p "Do you want to reinstall/upgrade? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installation cancelled"
        exit 0
    fi
    
    print_status "Uninstalling existing installation..."
    pipx uninstall claude-multiagent-pm || true
fi

# Install Claude PM Framework
print_status "Installing Claude PM Framework..."
if pipx install @bobmatnyc/claude-multiagent-pm; then
    print_success "Claude PM Framework installed successfully!"
else
    print_error "Installation failed"
    echo ""
    echo "Trying alternative installation method..."
    
    # Try with --force flag
    if pipx install --force @bobmatnyc/claude-multiagent-pm; then
        print_success "Claude PM Framework installed successfully (forced)!"
    else
        print_error "Alternative installation also failed"
        echo ""
        echo "Please try manual installation:"
        echo "1. Create a virtual environment:"
        echo "   python3 -m venv ~/claude-pm-env"
        echo "   source ~/claude-pm-env/bin/activate"
        echo "   pip install @bobmatnyc/claude-multiagent-pm"
        echo ""
        echo "2. Or use pip with user flag:"
        echo "   pip install --user @bobmatnyc/claude-multiagent-pm"
        exit 1
    fi
fi

# Install common dependencies that might be missing
print_status "Checking Python dependencies..."
DEPS_TO_CHECK=(
    "python-frontmatter"
    "mistune"
    "click"
    "rich"
    "pydantic"
    "pyyaml"
    "python-dotenv"
)

MISSING_DEPS=()
for dep in "${DEPS_TO_CHECK[@]}"; do
    if ! pipx runpip claude-multiagent-pm show "$dep" &> /dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    print_warning "Installing missing dependencies: ${MISSING_DEPS[*]}"
    pipx inject claude-multiagent-pm "${MISSING_DEPS[@]}"
    print_success "Dependencies installed"
fi

# Verify installation
print_status "Verifying installation..."
if command -v claude-pm &> /dev/null; then
    VERSION=$(claude-pm --version 2>&1 || echo "Version check failed")
    print_success "Claude PM is ready to use!"
    echo ""
    echo "📍 Installation Summary:"
    echo "   • Command: claude-pm"
    echo "   • Version: $VERSION"
    echo "   • Location: $(which claude-pm)"
    echo ""
    echo "🚀 Quick Start:"
    echo "   1. cd to your project directory"
    echo "   2. Run: claude-pm init"
    echo "   3. Run: claude-pm"
    echo ""
    echo "📚 Documentation:"
    echo "   • macOS Guide: docs/MACOS_INSTALLATION_GUIDE.md"
    echo "   • Troubleshooting: docs/TROUBLESHOOTING.md"
    echo "   • User Guide: docs/user-guide.md"
else
    print_error "Installation verification failed"
    echo "claude-pm command not found in PATH"
    echo ""
    echo "Try adding to PATH manually:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# Test Python imports
print_status "Testing Python imports..."
if python3 -c "import claude_pm" 2>/dev/null; then
    print_success "Python module import successful"
else
    print_warning "Direct Python import failed (this is normal with pipx)"
    echo "The CLI will still work correctly"
fi

print_success "Installation complete! 🎉"