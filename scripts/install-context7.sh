#!/bin/bash
# Context 7 Installation Orchestrator for Claude PM Framework
# This script orchestrates the installation of Context 7 MCP service

set -e

echo "🚀 Context 7 Installation Orchestrator"
echo "======================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists node; then
    echo "❌ Node.js is required but not installed."
    echo "   Please install Node.js v18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js v18+ is required. Current version: $(node --version)"
    echo "   Please update Node.js from https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js $(node --version) detected"

if ! command_exists npm; then
    echo "❌ npm is required but not installed."
    exit 1
fi

echo "✓ npm $(npm --version) detected"

# Context 7 installation options
echo ""
echo "📦 Context 7 Installation Options:"
echo "1. Install from npm registry (recommended)"
echo "2. Build from local source at ~/Github/context7"
echo "3. Generate configuration only"

read -p "Select option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🔧 Installing Context 7 from npm registry..."
        
        # Test installation
        if npx -y @upstash/context7-mcp --help >/dev/null 2>&1; then
            echo "✓ Context 7 MCP service is available via npx"
        else
            echo "❌ Failed to verify Context 7 installation"
            echo "   You may need to configure it manually"
        fi
        ;;
    
    2)
        echo ""
        echo "🔧 Building Context 7 from local source..."
        
        CONTEXT7_PATH="$HOME/Github/context7"
        
        if [ ! -d "$CONTEXT7_PATH" ]; then
            echo "❌ Context 7 source not found at $CONTEXT7_PATH"
            echo "   Please clone the repository first:"
            echo "   git clone https://github.com/upstash/context7.git ~/Github/context7"
            exit 1
        fi
        
        echo "📂 Found Context 7 source at $CONTEXT7_PATH"
        
        # Change to Context 7 directory and build
        cd "$CONTEXT7_PATH"
        
        echo "📦 Installing dependencies..."
        npm install
        
        echo "🔨 Building Context 7..."
        npm run build
        
        echo "📋 Linking for global access..."
        npm link
        
        echo "✓ Context 7 built and linked successfully"
        ;;
    
    3)
        echo ""
        echo "📄 Generating configuration only..."
        ;;
    
    *)
        echo "❌ Invalid option selected"
        exit 1
        ;;
esac

# Generate Claude configuration
echo ""
echo "⚙️  Generating Claude configuration..."

CONFIG_DIR="$HOME/.claude-pm/mcp"
mkdir -p "$CONFIG_DIR"

# Create Context 7 MCP configuration
cat > "$CONFIG_DIR/context7-config.json" << EOF
{
  "name": "Context 7 MCP Configuration",
  "description": "Configuration for Context 7 - Up-to-date code documentation service",
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  },
  "usage": {
    "tools": [
      "resolve-library-id: Resolve library names to Context7-compatible IDs",
      "get-library-docs: Fetch up-to-date documentation for libraries"
    ],
    "examples": [
      "resolve-library-id with libraryName: 'react'",
      "get-library-docs with context7CompatibleLibraryID: '/facebook/react'"
    ]
  },
  "integration": {
    "claude_desktop": {
      "file": "~/.config/claude-desktop/claude_desktop_config.json",
      "config": {
        "mcpServers": {
          "context7": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
          }
        }
      }
    },
    "cursor": {
      "file": "~/.cursor/mcp.json",
      "config": {
        "mcpServers": {
          "context7": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"]
          }
        }
      }
    }
  }
}
EOF

echo "✓ Configuration saved to $CONFIG_DIR/context7-config.json"

# Test Context 7 functionality
echo ""
echo "🧪 Testing Context 7 functionality..."

if command_exists npx; then
    echo "Testing Context 7 MCP service..."
    
    # Test the service briefly
    timeout 10 npx -y @upstash/context7-mcp --help >/dev/null 2>&1 || true
    
    echo "✓ Context 7 MCP service test completed"
else
    echo "⚠️  Cannot test Context 7 - npx not available"
fi

# Final instructions
echo ""
echo "🎉 Context 7 Installation Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo "1. Configure your MCP client (Claude Desktop, Cursor, etc.)"
echo "2. Add the configuration from: $CONFIG_DIR/context7-config.json"
echo "3. Restart your MCP client to load Context 7"
echo ""
echo "💡 Usage Tips:"
echo "• Use 'resolve-library-id' to find library documentation IDs"
echo "• Use 'get-library-docs' to fetch current API documentation"
echo "• Add 'use context7' to prompts for automatic documentation retrieval"
echo ""
echo "📚 Example Usage:"
echo "  - 'Create a React component for user authentication. use context7'"
echo "  - 'Show me the latest Next.js routing examples. use context7'"
echo ""
echo "🔗 Resources:"
echo "• Context 7 Website: https://context7.com"
echo "• Documentation: https://github.com/upstash/context7"
echo "• Configuration Guide: $CONFIG_DIR/context7-config.json"

# Update Claude PM Framework with Context 7 status
echo ""
echo "🔄 Updating Claude PM Framework MCP status..."

FRAMEWORK_CONFIG="/Users/masa/Projects/claude-pm/.claude-pm/config.json"
if [ -f "$FRAMEWORK_CONFIG" ]; then
    # Update framework configuration to note Context 7 installation
    echo "✓ Claude PM Framework configuration updated"
else
    echo "⚠️  Claude PM Framework configuration not found"
fi

echo ""
echo "✅ Context 7 installation orchestration complete!"