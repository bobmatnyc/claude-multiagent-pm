# Operations Documentation Index

## Overview
This directory contains operational documentation for all managed projects in the Claude PM ecosystem. Each project has specific deployment, configuration, and maintenance procedures documented here.

## Managed Projects

### Core Framework
- **[claude-pm](claude-pm.md)** - Claude PM framework operations and coordination
  - TrackDown task management system
  - Framework health monitoring
  - Cross-project integration
  - Milestone management

### Memory & AI Services
- **[mem0ai](mem0ai.md)** - Memory layer MCP service for persistent AI agent memory
  - MCP Server on port 8002 with SSE transport
  - Local ChromaDB storage with OpenAI integration
  - Claude PM Framework Makefile integration

### AI Tools & Agents
- **[ai-code-review](ai-code-review.md)** - AI-powered code review CLI tool
  - Multi-LLM provider support (Anthropic, Google, OpenAI, OpenRouter)
  - CLI and CI/CD integration with TypeScript/Biome toolchain
  - Pattern analysis, security review, and performance optimization

- **[eva-agent](eva-agent.md)** - Enhanced Virtual Assistant agent system
  - Memory-enabled AI agent
  - MCP integration and web interface
  - Training and character development

### MCP Services
- **[mcp-memory-service](mcp-memory-service.md)** - Persistent memory service with MCP protocol
  - PostgreSQL and Qdrant integration
  - Docker deployment architecture
  - Memory operations and search

### Deployment Platforms
- **[vercel](vercel.md)** - Vercel deployment procedures
  - Local development setup
  - Remote deployment workflows
  - Environment configuration

## Operations Standards

### Documentation Structure
Each project ops file should include:
- **Service Overview** - Purpose and architecture
- **Local Deployment** - Development setup
- **Remote Deployment** - Production procedures
- **Configuration** - Environment and settings
- **Monitoring** - Health checks and metrics
- **Troubleshooting** - Common issues and solutions

### File Naming Convention
- `[project-name].md` - Main project operations guide
- `[project-name]-[environment].md` - Environment-specific procedures (if needed)

### Update Procedures
1. Document all operational changes immediately
2. Include version information and last updated date
3. Test procedures before documenting
4. Reference from main CLAUDE.md for discoverability

## Quick Reference

### Common Operations
```bash
# Navigate to Claude-PM ops directory
cd ~/Projects/Claude-PM/ops

# View available documentation
ls -la *.md

# Framework health check
../trackdown/scripts/health-check.sh

# Check all services status
netstat -an | grep -E "(8002|8000|8765|3000)"

# Update project mapping
python ../integration/update_mapping.py
```

### Project Quick Commands
```bash
# mem0ai MCP service
cd ~/Services/mem0ai-mcp && make status

# AI code review
code-review --help

# EVA agent
cd ~/Projects/_archive/eva-agent && ./eva-help

# MCP memory service
curl http://localhost:8000/health
```

### Emergency Contacts
- **Framework Issues**: Reference main CLAUDE.md
- **Service Issues**: Check individual project ops files
- **Deployment Issues**: Reference platform-specific guides

---

**Directory**: ~/Projects/Claude-PM/ops/
**Last Updated**: 2025-07-06
**Framework Version**: v1.0.0-alpha