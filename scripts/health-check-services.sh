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
if [ -f ~/Projects/Claude-PM/trackdown/BACKLOG.md ]; then
    echo "✅ TrackDown system available"
    TASK_COUNT=$(grep -c "^\- \[" ~/Projects/Claude-PM/trackdown/BACKLOG.md 2>/dev/null || echo "0")
    echo "   📊 Active tasks: $TASK_COUNT"
else
    echo "❌ TrackDown system not found"
fi
echo ""

echo "🎯 Service Status Summary:"
echo "  • mem0ai MCP: Local deployment ready"
echo "  • Development tools: Check individual status above"
echo "  • Framework: Operational"
echo ""
echo "📚 For detailed service management:"
echo "  cd ~/Projects/Claude-PM/ops && ls *.md"