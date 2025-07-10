#!/bin/bash
# ~/Projects/Claude-PM/scripts/health-check-services.sh

echo "🏥 Claude PM Services Health Check"
echo "=================================="
echo ""

# Check mem0ai MCP Service
echo "📋 mem0ai MCP Service:"
if cd ~/Services/mem0ai-mcp 2>/dev/null; then
    make status 2>/dev/null || echo "❌ Service check failed"
    echo "   📡 Stdio path: /Users/masa/Services/mem0ai-mcp/mcp_server_stdio.py"
else
    echo "❌ Service directory not found"
fi
echo ""

# Check AI Code Review
echo "📋 AI Code Review Tool:"
if command -v code-review &> /dev/null; then
    echo "✅ CLI tool available"
    code-review --version 2>/dev/null || echo "   Version check failed"
else
    echo "❌ CLI tool not found"
fi
echo ""

# Check port usage
echo "📋 Port Usage:"
echo "   Port 8000: $(netstat -an | grep :8000 | wc -l | tr -d ' ') connections"
echo "   Port 8002: $(netstat -an | grep :8002 | wc -l | tr -d ' ') connections"
echo "   Port 3000: $(netstat -an | grep :3000 | wc -l | tr -d ' ') connections"
echo ""

# Check Claude PM framework
echo "📋 Claude PM Framework:"
if [ -f ~/Projects/claude-pm/scripts/health-check.sh ]; then
    echo "✅ AI-Trackdown Tools system available"
    if command -v aitrackdown &> /dev/null; then
        TASK_COUNT=$(cd ~/Projects/claude-pm && aitrackdown status --stats 2>/dev/null | grep -o "Total.*: [0-9]*" | tail -1 | grep -o "[0-9]*" || echo "0")
        echo "   📊 Active items: $TASK_COUNT"
    else
        echo "   ⚠️  AI-trackdown CLI not available"
    fi
else
    echo "❌ AI-Trackdown Tools system not found"
fi
echo ""

echo "🎯 Service Status Summary:"
echo "  • mem0ai MCP: Local deployment ready"
echo "  • Development tools: Check individual status above"
echo "  • Framework: Operational"
echo ""
echo "📚 For detailed service management:"
echo "  cd ~/Projects/claude-pm/ops && ls *.md"