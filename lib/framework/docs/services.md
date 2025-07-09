# Claude PM Services Documentation

## Overview

This document provides a comprehensive overview of all local services managed by the Claude PM framework. Each service has specific operational requirements, testing procedures, and deployment responsibilities.

## Service Responsibility Model

### Clear Separation of Concerns

**Project Claude Responsibility:**
- Develop and implement service code
- Create unit tests and integration tests
- Debug and fix service-level issues
- Maintain service-specific documentation
- Ensure code quality and functionality

**Claude PM Responsibility:**
- Deploy services locally and remotely
- Manage service infrastructure and configuration
- Monitor service health and availability
- Coordinate between services and projects
- Maintain operational documentation
- Handle deployment automation and CI/CD

## Local Services Registry

### Memory & AI Services

#### mem0ai MCP Service
- **Location**: `~/Services/mem0ai-mcp/`
- **Purpose**: Persistent memory for AI agents via MCP protocol
- **Status Check**: `cd ~/Services/mem0ai-mcp && make status`
- **Start Command**: `make start` (HTTP) or `make start-stdio` (recommended)
- **Health Check**: `make health`
- **Port**: 8002 (HTTP/SSE)
- **MCP Path**: `/Users/masa/Services/mem0ai-mcp/mcp_server_stdio.py`
- **Dependencies**: OpenAI API key, ChromaDB, mem0ai library
- **Expected Status**: ✅ Running (for HTTP) / ⚡ On-demand (for stdio)

### Development Services

#### AI Code Review
- **Location**: Check `~/Projects/managed/` or ops documentation
- **Purpose**: AI-powered code review and analysis
- **Status Check**: `code-review --version` or check ops docs
- **Dependencies**: Multi-LLM provider support
- **Expected Status**: 📦 CLI tool (installed globally)

#### EVA Agent
- **Location**: `~/Projects/_archive/eva-agent/` (archived)
- **Purpose**: Enhanced Virtual Assistant with memory integration
- **Status Check**: `cd ~/Projects/_archive/eva-agent && ./eva-help`
- **Dependencies**: Memory service integration
- **Expected Status**: 📦 Archived (available for reference)

### Database Services

#### MCP Memory Service (Separate)
- **Location**: Check ops documentation for current status
- **Purpose**: PostgreSQL + Qdrant memory service
- **Status Check**: `curl http://localhost:8000/health`
- **Port**: 8000
- **Dependencies**: Docker, PostgreSQL, Qdrant
- **Expected Status**: ⚠️ Status unknown (check ops docs)

## Service Health Monitoring

### Startup Health Check Script

Create a comprehensive health check that runs on Claude PM startup:

```bash
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
```

### Quick Service Status Commands

```bash
# Check all service ports
netstat -an | grep -E "(8000|8002|3000|8001)" | sort

# Quick mem0ai status
cd ~/Services/mem0ai-mcp && make status

# Framework health
cd ~/Projects/Claude-PM && ./trackdown/scripts/health-check.sh

# Check ops documentation
cd ~/Projects/Claude-PM/ops && ls *.md
```

## Service Testing Procedures

### mem0ai MCP Service Testing

```bash
# 1. Service setup test
cd ~/Services/mem0ai-mcp
make setup

# 2. Configuration test
make check

# 3. Stdio transport test (recommended)
make start-stdio
# Should start without errors and show MCP server listening

# 4. HTTP transport test (if needed)
make start
make health

# 5. Tool functionality test (manual)
# Connect Claude Code to stdio path and test memory tools
```

### Development Tool Testing

```bash
# AI Code Review
code-review --help
code-review --version

# EVA Agent (archived)
cd ~/Projects/_archive/eva-agent
./eva-help

# Framework health
cd ~/Projects/Claude-PM
./trackdown/scripts/health-check.sh
```

## Deployment Architecture

### Local Development
- **Services**: Deployed to `~/Services/`
- **Management**: Claude PM Makefiles and scripts
- **Configuration**: Environment files and local storage
- **Monitoring**: Health checks and status commands

### Remote Deployment
- **Responsibility**: Claude PM framework
- **Platforms**: Vercel, Docker, cloud providers
- **Coordination**: Multi-project deployment strategies
- **Monitoring**: Automated health checks and alerts

## Common Issues & Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
lsof -i :8002
netstat -an | grep 8002

# Kill process on port
lsof -ti:8002 | xargs kill -9
```

### Service Dependencies
```bash
# Check Python environment
which python3
python3 --version

# Check virtual environments
ls ~/Services/*/venv

# Check API keys
grep -r "OPENAI_API_KEY" ~/Services/*/.*env
```

### Framework Issues
```bash
# Reset Claude PM framework
cd ~/Projects/Claude-PM
git status
git pull

# Check TrackDown system
ls trackdown/
cat trackdown/BACKLOG.md | head -20
```

## Integration with Claude Code

### MCP Service Configuration

For Claude Code to use local MCP services:

1. **mem0ai Memory Service**: Use stdio transport
   ```
   Path: /Users/masa/Services/mem0ai-mcp/mcp_server_stdio.py
   ```

2. **Service Health**: Ensure services are running before use
3. **Dependencies**: Verify API keys and configurations

### Service Discovery

Claude PM maintains service registry in:
- **`ops/index.md`**: Service overview and quick reference
- **`ops/[service].md`**: Detailed operational procedures
- **`docs/services.md`**: This comprehensive guide

## Future Services

### Planned Additions
- Advanced monitoring dashboard
- Automated deployment pipelines
- Multi-environment management
- Service orchestration platform

### Integration Opportunities
- Claude Code MCP extensions
- Cross-service memory sharing
- Unified logging and monitoring
- Automated testing frameworks

---

**Last Updated**: 2025-07-06  
**Framework Version**: v1.0.0-alpha  
**Maintained By**: Claude PM Framework

## Quick Reference Commands

```bash
# Service health check
cd ~/Projects/Claude-PM && bash scripts/health-check-services.sh

# mem0ai MCP status
cd ~/Services/mem0ai-mcp && make status

# Framework status
cd ~/Projects/Claude-PM && ./trackdown/scripts/health-check.sh

# View all ops docs
cd ~/Projects/Claude-PM/ops && ls *.md

# Check active ports
netstat -an | grep -E "(8000|8002|3000)" | sort
```