#!/bin/bash
# Add Context 7 to Claude Desktop Configuration
# This script adds Context 7 MCP service to your Claude Desktop configuration

set -e

echo "🔧 Adding Context 7 to Claude Desktop Configuration"
echo "=================================================="

# Find Claude Desktop config file location
CLAUDE_CONFIG_LOCATIONS=(
    "$HOME/.config/claude-desktop/claude_desktop_config.json"
    "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    "$HOME/AppData/Roaming/Claude/claude_desktop_config.json"
)

CLAUDE_CONFIG=""
for location in "${CLAUDE_CONFIG_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        CLAUDE_CONFIG="$location"
        echo "✓ Found Claude config at: $location"
        break
    fi
done

if [ -z "$CLAUDE_CONFIG" ]; then
    echo "⚠️  Claude Desktop config not found. Checking common locations..."
    
    # Try to create the most common location
    CLAUDE_CONFIG="$HOME/.config/claude-desktop/claude_desktop_config.json"
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"
    
    echo "📁 Creating new config at: $CLAUDE_CONFIG"
fi

# Backup existing config if it exists
if [ -f "$CLAUDE_CONFIG" ]; then
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✓ Backed up existing config"
fi

# Read existing config or create new one
if [ -f "$CLAUDE_CONFIG" ] && [ -s "$CLAUDE_CONFIG" ]; then
    echo "📖 Reading existing Claude configuration..."
    
    # Check if it already has Context 7
    if grep -q "context7\|@upstash/context7-mcp" "$CLAUDE_CONFIG"; then
        echo "✓ Context 7 already configured in Claude Desktop"
        echo "🔄 Current configuration:"
        cat "$CLAUDE_CONFIG"
        exit 0
    fi
    
    # Use jq to add Context 7 if jq is available
    if command -v jq >/dev/null 2>&1; then
        echo "🔧 Adding Context 7 using jq..."
        
        # Add Context 7 to existing mcpServers
        jq '.mcpServers.context7 = {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
        }' "$CLAUDE_CONFIG" > "$CLAUDE_CONFIG.tmp" && mv "$CLAUDE_CONFIG.tmp" "$CLAUDE_CONFIG"
        
    else
        echo "⚠️  jq not available. Please manually add Context 7 to your Claude config."
        echo "📋 Add this to your mcpServers section:"
        cat << 'EOF'
"context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp"]
}
EOF
    fi
else
    echo "📝 Creating new Claude Desktop configuration..."
    
    cat > "$CLAUDE_CONFIG" << 'EOF'
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
EOF
fi

echo ""
echo "✅ Context 7 Configuration Complete!"
echo "===================================="
echo ""
echo "📁 Configuration file: $CLAUDE_CONFIG"
echo ""
echo "🔄 Current configuration:"
cat "$CLAUDE_CONFIG"
echo ""
echo "📋 Next Steps:"
echo "1. Restart Claude Desktop completely"
echo "2. Context 7 should appear alongside zen in your MCP servers"
echo "3. Use 'resolve-library-id' and 'get-library-docs' tools"
echo ""
echo "💡 Usage Examples:"
echo "• 'Get React documentation. use context7'"
echo "• 'Show me Next.js routing examples. use context7'"
echo ""
echo "🔧 If Context 7 still doesn't appear:"
echo "1. Check Claude Desktop logs for errors"
echo "2. Verify npx can run: npx -y @upstash/context7-mcp --help"
echo "3. Try restarting your computer"
echo ""
echo "📞 Configuration saved! Please restart Claude Desktop."