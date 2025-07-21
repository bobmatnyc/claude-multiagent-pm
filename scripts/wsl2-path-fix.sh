#!/bin/bash
# Claude PM Framework - WSL2 PATH Configuration Fix Script
# Comprehensive fix for WSL2 PATH issues with NVM and npm global packages

echo "🐧 Claude PM Framework - WSL2 PATH Configuration Fix"
echo "=================================================="
echo ""

# Detect WSL2 environment
if [[ -z "$WSL_DISTRO_NAME" ]] && [[ -z "$WSLENV" ]]; then
    echo "❌ This script is designed for WSL2 environments only"
    echo "   Current environment does not appear to be WSL2"
    exit 1
fi

echo "✅ WSL2 Environment detected: ${WSL_DISTRO_NAME:-Unknown}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  This script should not be run as root"
    echo "   Please run as your regular user account"
    exit 1
fi

# Function to backup shell config files
backup_shell_config() {
    local config_file="$1"
    if [[ -f "$config_file" ]]; then
        local backup_file="${config_file}.claude-pm-backup-$(date +%Y%m%d-%H%M%S)"
        cp "$config_file" "$backup_file"
        echo "📁 Backed up $config_file to $backup_file"
    fi
}

# Function to add PATH configuration
add_path_config() {
    local config_file="$1"
    local npm_global_bin="$2"
    
    # Check if PATH configuration already exists
    if grep -q "Claude PM Framework" "$config_file" 2>/dev/null; then
        echo "📋 PATH configuration already exists in $config_file"
        return 0
    fi
    
    # Add PATH configuration
    cat >> "$config_file" << EOF

# Claude PM Framework - WSL2 PATH configuration
# Auto-added by WSL2 PATH fix script
export PATH="$npm_global_bin:\$PATH"

# NVM configuration (if not already present)
if [[ -d "\$HOME/.nvm" ]] && [[ -z "\$NVM_DIR" ]]; then
    export NVM_DIR="\$HOME/.nvm"
    [[ -s "\$NVM_DIR/nvm.sh" ]] && source "\$NVM_DIR/nvm.sh"
    [[ -s "\$NVM_DIR/bash_completion" ]] && source "\$NVM_DIR/bash_completion"
fi
EOF
    
    echo "✅ Added PATH configuration to $config_file"
}

# Detect npm global bin directory
echo "🔍 Detecting npm global bin directory..."

NPM_GLOBAL_BIN=""
methods=(
    "npm bin -g 2>/dev/null"
    "npm config get prefix 2>/dev/null && echo '/bin'"
    "echo \$HOME/.nvm/versions/node/\$(node --version)/bin 2>/dev/null"
)

for method in "${methods[@]}"; do
    result=$(eval "$method")
    if [[ -n "$result" ]] && [[ -d "$result" ]]; then
        NPM_GLOBAL_BIN="$result"
        echo "✅ Found npm global bin: $NPM_GLOBAL_BIN"
        break
    fi
done

if [[ -z "$NPM_GLOBAL_BIN" ]]; then
    echo "❌ Could not determine npm global bin directory"
    echo "   Please ensure Node.js and npm are properly installed"
    exit 1
fi

# Check current PATH
echo ""
echo "🔍 Current PATH analysis:"
echo "   PATH: $PATH"

if [[ ":$PATH:" == *":$NPM_GLOBAL_BIN:"* ]]; then
    echo "✅ npm global bin is already in PATH"
else
    echo "❌ npm global bin is NOT in PATH"
    echo "   Need to add: $NPM_GLOBAL_BIN"
fi

# Check command availability
echo ""
echo "🧪 Testing command availability:"

commands=("node" "npm" "claude-pm" "aitrackdown" "claude")
for cmd in "${commands[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        version=$(${cmd} --version 2>/dev/null || echo "unknown")
        echo "   ✅ $cmd: $version"
    else
        echo "   ❌ $cmd: not found"
    fi
done

echo ""

# Fix PATH configuration
echo "🔧 Fixing PATH configuration..."

# Determine shell configuration files to update
shell_configs=()
if [[ -n "$BASH_VERSION" ]] || [[ "$SHELL" == *"bash"* ]]; then
    shell_configs+=("$HOME/.bashrc")
fi
if [[ -n "$ZSH_VERSION" ]] || [[ "$SHELL" == *"zsh"* ]]; then
    shell_configs+=("$HOME/.zshrc")
fi
if [[ ${#shell_configs[@]} -eq 0 ]]; then
    # Default to .bashrc if we can't detect shell
    shell_configs+=("$HOME/.bashrc")
fi

echo "📝 Updating shell configuration files:"
for config_file in "${shell_configs[@]}"; do
    echo "   • $config_file"
    
    # Create file if it doesn't exist
    if [[ ! -f "$config_file" ]]; then
        touch "$config_file"
        echo "     📁 Created new configuration file"
    fi
    
    # Backup existing file
    backup_shell_config "$config_file"
    
    # Add PATH configuration
    add_path_config "$config_file" "$NPM_GLOBAL_BIN"
done

# Apply changes to current session
echo ""
echo "🚀 Applying changes to current session..."
export PATH="$NPM_GLOBAL_BIN:$PATH"

# Test the fix
echo ""
echo "🧪 Testing the fix:"

# Test claude-pm availability
if command -v claude-pm >/dev/null 2>&1; then
    version=$(claude-pm --version 2>/dev/null || echo "unknown")
    echo "   ✅ claude-pm: $version"
else
    echo "   ❌ claude-pm: still not found"
fi

# Test aitrackdown availability
if command -v aitrackdown >/dev/null 2>&1; then
    version=$(aitrackdown --version 2>/dev/null || echo "unknown")
    echo "   ✅ aitrackdown: $version"
else
    echo "   ⚠️  aitrackdown: not found (may need manual installation)"
    echo "      Run: pip install --user ai-trackdown-pytools==1.1.0"
fi

echo ""
echo "✅ WSL2 PATH configuration fix completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Restart your terminal or run: source ~/.bashrc"
echo "   2. Test claude-pm: claude-pm --version"
echo "   3. Install Python ticketing: pip install --user ai-trackdown-pytools==1.1.0"
echo "   4. Run full diagnostic: ~/.claude-pm/wsl2-diagnostic.sh"
echo ""
echo "🔗 If you continue to have issues:"
echo "   • GitHub Issue: https://github.com/bobmatnyc/claude-multiagent-pm/issues/1"
echo "   • Documentation: https://github.com/bobmatnyc/claude-multiagent-pm#wsl2-setup"
echo ""