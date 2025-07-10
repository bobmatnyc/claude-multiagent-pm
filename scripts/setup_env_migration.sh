#!/bin/bash
# Claude PM Framework Environment Variable Migration Setup
# This script helps set up the new CLAUDE_MULTIAGENT_PM_ environment variables permanently

set -e

echo "=== Claude PM Framework Environment Variable Migration ==="
echo "This script will help migrate from CLAUDE_PM_ to CLAUDE_MULTIAGENT_PM_ environment variables."
echo ""

# Source the migration commands
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MIGRATION_COMMANDS="$PROJECT_ROOT/env_migration_commands.sh"

if [[ ! -f "$MIGRATION_COMMANDS" ]]; then
    echo "Error: Migration commands file not found at $MIGRATION_COMMANDS"
    echo "Please run the migration script first:"
    echo "  python3 scripts/migrate_env_variables.py"
    exit 1
fi

echo "Found migration commands at: $MIGRATION_COMMANDS"
echo ""

# Display current status
echo "=== Current Environment Variable Status ==="
LEGACY_COUNT=$(env | grep -c "^CLAUDE_PM_" || true)
NEW_COUNT=$(env | grep -c "^CLAUDE_MULTIAGENT_PM_" || true)

echo "Legacy CLAUDE_PM_ variables: $LEGACY_COUNT"
echo "New CLAUDE_MULTIAGENT_PM_ variables: $NEW_COUNT"
echo ""

if [[ $LEGACY_COUNT -eq 0 ]]; then
    echo "No legacy environment variables found. Migration may not be needed."
    exit 0
fi

# Offer migration options
echo "=== Migration Options ==="
echo "1. Apply migration to current session only (temporary)"
echo "2. Add migration to shell configuration file (permanent)"
echo "3. Show migration commands (review only)"
echo "4. Exit without changes"
echo ""

read -p "Choose an option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "=== Applying Migration to Current Session ==="
        echo "Sourcing migration commands..."
        
        # Source the migration commands
        source "$MIGRATION_COMMANDS"
        
        echo "Migration applied to current session."
        echo ""
        echo "=== Verification ==="
        NEW_COUNT_AFTER=$(env | grep -c "^CLAUDE_MULTIAGENT_PM_" || true)
        echo "New CLAUDE_MULTIAGENT_PM_ variables: $NEW_COUNT_AFTER"
        
        # Test framework configuration
        echo ""
        echo "Testing framework configuration..."
        if python3 -c "from claude_pm.core.config import Config; c = Config(); print('Framework configuration loaded successfully')" 2>/dev/null; then
            echo "✓ Framework configuration test passed"
        else
            echo "✗ Framework configuration test failed"
        fi
        
        echo ""
        echo "Note: These changes are temporary and will be lost when you close this session."
        echo "To make permanent changes, run this script again and choose option 2."
        ;;
        
    2)
        echo ""
        echo "=== Adding Migration to Shell Configuration ==="
        
        # Detect shell and configuration file
        SHELL_NAME=$(basename "$SHELL")
        case "$SHELL_NAME" in
            bash)
                CONFIG_FILES=("$HOME/.bashrc" "$HOME/.bash_profile")
                ;;
            zsh)
                CONFIG_FILES=("$HOME/.zshrc" "$HOME/.zprofile")
                ;;
            *)
                CONFIG_FILES=("$HOME/.profile")
                ;;
        esac
        
        echo "Detected shell: $SHELL_NAME"
        
        # Find existing config file or create one
        TARGET_CONFIG=""
        for config_file in "${CONFIG_FILES[@]}"; do
            if [[ -f "$config_file" ]]; then
                TARGET_CONFIG="$config_file"
                break
            fi
        done
        
        if [[ -z "$TARGET_CONFIG" ]]; then
            TARGET_CONFIG="${CONFIG_FILES[0]}"
            echo "Creating new configuration file: $TARGET_CONFIG"
        else
            echo "Using existing configuration file: $TARGET_CONFIG"
        fi
        
        # Check if migration is already in config file
        if grep -q "CLAUDE_MULTIAGENT_PM_" "$TARGET_CONFIG" 2>/dev/null; then
            echo "Warning: CLAUDE_MULTIAGENT_PM_ variables already found in $TARGET_CONFIG"
            read -p "Continue anyway? (y/N): " confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                echo "Migration cancelled."
                exit 0
            fi
        fi
        
        # Create backup
        if [[ -f "$TARGET_CONFIG" ]]; then
            cp "$TARGET_CONFIG" "${TARGET_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
            echo "Created backup: ${TARGET_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Add migration commands to config file
        echo "" >> "$TARGET_CONFIG"
        echo "# Claude PM Framework Environment Variables (migrated $(date))" >> "$TARGET_CONFIG"
        grep "^export CLAUDE_MULTIAGENT_PM_" "$MIGRATION_COMMANDS" >> "$TARGET_CONFIG"
        echo "" >> "$TARGET_CONFIG"
        
        echo "✓ Migration commands added to $TARGET_CONFIG"
        echo ""
        echo "To apply the changes:"
        echo "  source $TARGET_CONFIG"
        echo "Or restart your terminal session."
        
        # Offer to apply immediately
        read -p "Apply changes to current session now? (Y/n): " apply_now
        if [[ ! "$apply_now" =~ ^[Nn]$ ]]; then
            source "$MIGRATION_COMMANDS"
            echo "✓ Changes applied to current session"
        fi
        ;;
        
    3)
        echo ""
        echo "=== Migration Commands ==="
        cat "$MIGRATION_COMMANDS"
        ;;
        
    4)
        echo "Exiting without changes."
        exit 0
        ;;
        
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
echo "=== Migration Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify the new environment variables are working:"
echo "   env | grep CLAUDE_MULTIAGENT_PM_"
echo ""
echo "2. Test the framework configuration:"
echo "   python3 -c \"from claude_pm.core.config import Config; Config()\""
echo ""
echo "3. Once confirmed working, you can remove legacy variables:"
echo "   (Run the unset commands from env_migration_commands.sh)"
echo ""
echo "For more information, see the migration report: env_migration_report.json"