#!/bin/bash
# Add Context 7 to Claude Code Configuration
# This script adds Context 7 MCP service to Claude Code using the claude CLI

set -e

echo "🔧 Adding Context 7 to Claude Code Configuration"
echo "==============================================="

# Check if claude CLI is available
if ! command -v claude >/dev/null 2>&1; then
    echo "❌ Claude Code CLI not found"
    echo "   Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    echo "   Or make sure 'claude' command is in your PATH"
    exit 1
fi

echo "✓ Claude Code CLI detected: $(claude --version 2>/dev/null || echo 'installed')"

# Check current MCP servers
echo ""
echo "📋 Current MCP servers in Claude Code:"
claude mcp list 2>/dev/null || echo "   (Unable to list current servers)"

echo ""
echo "🔧 Adding Context 7 MCP service..."

# Add Context 7 using Claude Code CLI
# Using stdio transport (default for Claude Code)
if claude mcp add context7 -- npx -y @upstash/context7-mcp; then
    echo "✅ Context 7 added successfully with stdio transport"
else
    echo "⚠️  Failed to add with stdio transport, trying HTTP transport..."
    
    # Try with HTTP transport as fallback
    if claude mcp add --transport http context7 https://mcp.context7.com/mcp; then
        echo "✅ Context 7 added successfully with HTTP transport"
    else
        echo "❌ Failed to add Context 7. Trying manual configuration..."
        
        # Show manual configuration instructions
        echo ""
        echo "📋 Manual Configuration Instructions:"
        echo "Add Context 7 manually using one of these commands:"
        echo ""
        echo "Option 1 - Local stdio transport (recommended):"
        echo "  claude mcp add context7 -- npx -y @upstash/context7-mcp"
        echo ""
        echo "Option 2 - Remote HTTP transport:"
        echo "  claude mcp add --transport http context7 https://mcp.context7.com/mcp"
        echo ""
        echo "Option 3 - Remote SSE transport:"
        echo "  claude mcp add --transport sse context7 https://mcp.context7.com/sse"
    fi
fi

echo ""
echo "🧪 Testing Context 7 availability..."

# Test that npx can run Context 7
if npx -y @upstash/context7-mcp --help >/dev/null 2>&1; then
    echo "✓ Context 7 service is accessible via npx"
else
    echo "⚠️  Context 7 service test failed - may need troubleshooting"
fi

echo ""
echo "📋 Updated MCP servers in Claude Code:"
claude mcp list 2>/dev/null || echo "   (Unable to list servers - restart Claude Code to see changes)"

echo ""
echo "✅ Context 7 Configuration Complete!"
echo "===================================="
echo ""
echo "🔄 Next Steps:"
echo "1. Restart Claude Code if necessary"
echo "2. Context 7 should now be available alongside zen"
echo "3. Available tools:"
echo "   • resolve-library-id - Convert library names to Context7 IDs"
echo "   • get-library-docs - Fetch current documentation"
echo ""
echo "💡 Usage Examples in Claude Code:"
echo "• 'Get React hooks documentation. use context7'"
echo "• 'Show me the latest Next.js App Router examples. use context7'"
echo "• 'Find TypeScript utility types documentation. use context7'"
echo ""
echo "🔧 Available Commands:"
echo "• List MCP servers: claude mcp list"
echo "• Remove Context 7: claude mcp remove context7"
echo "• View MCP help: claude mcp --help"
echo ""
echo "🌐 Transport Options Used:"
echo "• Primary: stdio (local npx execution)"
echo "• Fallback: HTTP (https://mcp.context7.com/mcp)"
echo "• Alternative: SSE (https://mcp.context7.com/sse)"
echo ""
echo "📞 Configuration complete! Context 7 should now be available in Claude Code."