# Mem0AI MCP Service Operations Guide

## Service Overview
Mem0AI MCP Service provides persistent memory capabilities for AI agents through the Model Context Protocol (MCP). This service enables Claude Code and other MCP clients to store, retrieve, and search memories across conversations using local storage and OpenAI API.

## Local Deployment

### Service Status
- **HTTP Transport**: Port 8002, endpoint `http://0.0.0.0:8002/sse` (Server-Sent Events)
- **Stdio Transport**: `/Users/masa/Services/mem0ai-mcp/mcp_server_stdio.py` ⭐ **RECOMMENDED**
- **Location**: `~/Services/mem0ai-mcp/`
- **Status Check**: `make status` or `netstat -an | grep 8002`
- **Health Check**: `make health`

### Service Architecture
- **MCP Server**: FastMCP with Server-Sent Events transport
- **Memory Engine**: Local mem0ai library with ChromaDB vector storage
- **Storage**: Local ChromaDB + SQLite (in `./data/` directory)
- **LLM Integration**: OpenAI API for embeddings and processing
- **Management**: Claude PM Framework with standardized Makefile

### Starting the Service
```bash
# Navigate to service directory
cd ~/Services/mem0ai-mcp

# Quick deployment (setup + start + health check)
make deploy

# Or manual management
make setup    # Initial setup
make start    # Start service
make status   # Check status
```

## Claude Code Integration

### MCP Configuration
The mem0ai MCP service supports both HTTP and stdio transports:

**HTTP Transport**: `http://0.0.0.0:8002/sse` (for web integration)
**Stdio Transport**: `/Users/masa/Services/mem0ai-mcp/mcp_server_stdio.py` ⭐ **RECOMMENDED**

For Claude Code integration, use the stdio transport by referencing the file path.

### MCP Tools Available
1. **add_memory** - Store information, code snippets, preferences, and context
2. **search_memories** - Semantic search through stored memories using natural language
3. **get_all_memories** - Retrieve all stored memories for review
4. **update_memory** - Modify existing memories by ID
5. **delete_memory** - Remove memories by ID

### Integration Steps
1. Ensure mem0ai MCP service is running: `cd ~/Services/mem0ai-mcp && make status`
2. Configure Claude Code with SSE endpoint: `http://0.0.0.0:8002/sse`
3. Verify memory tools are available in Claude Code tool list
4. Test basic functionality with `add_memory` and `search_memories`

### Verification
```bash
# Check service is running
cd ~/Services/mem0ai-mcp
make status
make health

# Test MCP endpoint manually (optional)
curl -X GET http://0.0.0.0:8002/sse \
  -H "Accept: text/event-stream"
```

## Service Management

### Claude PM Framework Commands
```bash
cd ~/Services/mem0ai-mcp

# Service lifecycle
make setup      # Initial setup with venv and dependencies
make deploy     # Full deployment (setup + start + health)
make start      # Start MCP server (HTTP/SSE)
make start-stdio # Test MCP server (stdio) ⭐ RECOMMENDED
make stop       # Stop MCP server
make restart    # Restart service
make status     # Check service status

# Monitoring and maintenance
make health     # Health check endpoint
make logs       # View recent logs
make check      # Configuration validation
make clean      # Cleanup and reset

# Development
make dev        # Setup development environment
make test       # Run tests (if available)
```

### Configuration Requirements
- **OpenAI API Key**: Required in `.env` file
- **Data Directory**: `./data/` for ChromaDB and SQLite storage
- **Log Directory**: `./logs/` for service logging
- **Virtual Environment**: `.venv/` for Python dependencies

## Environment Configuration

### Required Environment Variables
```bash
# .env file in ~/Services/mem0ai-mcp/
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

### Optional Configuration
```bash
# Service customization (optional)
MCP_HOST=0.0.0.0
MCP_PORT=8001
DATA_DIR=./data
LOG_LEVEL=INFO
```

### Initial Setup
```bash
# First time setup
cd ~/Services/mem0ai-mcp
cp .env .env.backup  # backup template
nano .env            # add your OpenAI API key
make deploy          # setup and start service
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check port 8001 is not in use
lsof -i :8001

# Verify OpenAI API key is set
cd ~/Services/mem0ai-mcp
make check

# Check dependencies
make setup

# View startup logs
make logs
```

#### OpenAI API Key Issues
```bash
# Check if API key is configured
cd ~/Services/mem0ai-mcp
grep OPENAI_API_KEY .env

# Test API key (should return model list)
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### MCP Connection Failed
```bash
# Verify service is running
cd ~/Services/mem0ai-mcp
make status

# Check MCP endpoint
curl -X GET http://0.0.0.0:8002/sse \
  -H "Accept: text/event-stream"

# Restart service if needed
make restart
```

#### Memory Tools Not Available in Claude Code
- Confirm service status: `make status`
- Verify endpoint configuration: `http://0.0.0.0:8002/sse`
- Check Claude Code MCP configuration
- Restart Claude Code after configuration changes

### Debug Commands
```bash
cd ~/Services/mem0ai-mcp

# Service diagnostics
make status          # Check if running
make health          # Health check
make logs           # View recent logs
make check          # Configuration check

# System diagnostics
ps aux | grep mcp_server
netstat -an | grep 8001
lsof -i :8001

# Test memory operations
python -c "
from mem0 import Memory;
m = Memory();
print('Memory system ready')
"
```

## Monitoring

### Automated Health Checks
```bash
cd ~/Services/mem0ai-mcp

# Claude PM framework health check
make health

# Service status with details
make status

# Recent logs
make logs

# Configuration validation
make check
```

### Claude PM Framework Integration
```bash
# JSON status for automation
make pm-status

# Full logs for monitoring
make pm-logs  

# Exit code health check
make pm-health && echo "Healthy" || echo "Unhealthy"
```

### Performance Metrics
- **Memory Storage**: Local ChromaDB vector database
- **Response Time**: Monitored via health checks
- **Resource Usage**: Python process with local storage
- **API Calls**: OpenAI API usage for embeddings and LLM

### Data Backup
```bash
cd ~/Services/mem0ai-mcp

# Backup memory data
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

---

**Last Updated**: 2025-07-06
**Service Version**: mem0ai MCP Service v1.0
**Integration Status**: MCP Server Deployed, Claude PM Framework Integrated
**Endpoint**: `http://0.0.0.0:8002/sse`