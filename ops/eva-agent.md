# EVA Agent Operations Guide

## Project Overview
EVA (Enhanced Virtual Assistant) - AI agent system with memory capabilities, MCP integration, and terminal interface.

**Repository**: `~/Projects/_archive/eva-agent/`
**Tech Stack**: Python, FastAPI, MCP, Memory Services
**Purpose**: Intelligent AI agent with persistent memory and tool integration

## Local Development

### Prerequisites
```bash
# Python 3.8+
python3 --version
pip3 --version

# Virtual environment
cd ~/Projects/_archive/eva-agent
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Development installation
pip install -e .
```

### Environment Configuration
**File**: `.env`
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=claude-...
OPENROUTER_API_KEY=...

# Memory Service
MEMORY_SERVICE_URL=http://localhost:8000
MEMORY_SERVICE_API_KEY=...

# MCP Configuration
MCP_SERVER_PORT=8765
MCP_LOG_LEVEL=INFO

# EVA Configuration
EVA_LOG_LEVEL=DEBUG
EVA_MEMORY_ENABLED=true
EVA_WEB_INTERFACE=true
```

## Core Services

### EVA Agent Commands
```bash
# Main EVA agent
./eva

# Ask EVA a question
./eva-ask "What projects am I working on?"

# Stream responses
./eva-stream

# Help system
./eva-help

# Test EVA functionality
./eva-test

# Web interface
./eva-web

# MCP server
./eva-server
```

### Memory Service
```bash
# Start memory service
python simple_memory_service.py

# Run memory tests
python test_memory_tools.py

# Memory training
python run_memory_training.py
```

### MCP Integration
```bash
# Start MCP server
python run_mcp_server.py

# Test MCP functionality
python test_eva_tools.py

# MCP server on custom port
python run_mcp_server.py --port 8765
```

## Training & Development

### Character Training
```bash
# Level 1 training (basic)
python run_level1_training.py

# Level 2 training (intermediate)
python run_level2_training.py

# Level 3 training (advanced)
python run_level3_training.py

# Emergency training
python test_eva_emergency_training.py

# Character development
python test_eva_character_training.py
```

### Testing Suite
```bash
# Core functionality tests
python test_eva_direct.py

# Live system tests
python test_eva_live.py
python verify_eva_live.py

# Identity tests
python test_eva_identity.py

# Architecture tests
python test_corrected_architecture.py
```

## Web Interface

### Starting Web Interface
```bash
# Standard web interface
python web_interface.py

# Custom port
python web_interface.py --port 8080

# Debug mode
python web_interface.py --debug
```

### Web Interface Features
- Chat interface with EVA
- Memory browsing and management
- Tool execution monitoring
- System status dashboard
- Training progress tracking

### API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Chat with EVA
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello EVA"}'

# Memory operations
curl http://localhost:8000/memory/status
curl http://localhost:8000/memory/search?q=projects
```

## Memory System

### Memory Architecture
- **Short-term Memory**: Active conversation context
- **Long-term Memory**: Persistent knowledge and experiences
- **Episodic Memory**: Specific events and interactions
- **Semantic Memory**: Facts and general knowledge

### Memory Commands
```bash
# Memory status
python -c "from eva.memory import MemoryService; MemoryService().status()"

# Search memory
python -c "from eva.memory import MemoryService; print(MemoryService().search('projects'))"

# Add memory
python -c "from eva.memory import MemoryService; MemoryService().add('User working on Claude-PM project')"
```

### Memory Service Configuration
```python
# memory_config.py
MEMORY_CONFIG = {
    "storage_type": "vector",  # vector, sql, hybrid
    "vector_db": "qdrant",     # qdrant, pinecone, weaviate
    "embedding_model": "openai",
    "chunk_size": 1000,
    "overlap": 200,
    "similarity_threshold": 0.8
}
```

## MCP Server

### Server Configuration
```bash
# Start MCP server
python run_mcp_server.py

# Custom configuration
python run_mcp_server.py \
  --port 8765 \
  --log-level DEBUG \
  --memory-enabled
```

### Available Tools
- **memory_search** - Search EVA's memory
- **memory_add** - Add to EVA's memory
- **system_status** - Get system status
- **execute_command** - Execute system commands
- **file_operations** - File read/write operations
- **web_search** - Search the web
- **code_analysis** - Analyze code files

### MCP Client Configuration
```json
{
  "mcpServers": {
    "eva": {
      "command": "python",
      "args": ["~/Projects/_archive/eva-agent/run_mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "MEMORY_SERVICE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Remote Deployment

### Docker Deployment
```bash
# Build container
docker build -t eva-agent .

# Run container
docker run -d \
  --name eva-agent \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  eva-agent

# Check logs
docker logs eva-agent
```

### Production Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  eva-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MEMORY_SERVICE_URL=http://memory:8001
      - EVA_LOG_LEVEL=INFO
    depends_on:
      - memory
      
  memory:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
      
volumes:
  qdrant_data:
```

### Environment Variables (Production)
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=claude-...
MEMORY_SERVICE_URL=http://memory:8001
EVA_LOG_LEVEL=INFO
EVA_WEB_INTERFACE=true
MCP_SERVER_PORT=8765
```

## Monitoring

### Health Checks
```bash
# System health
python -c "from eva.system import health_check; health_check()"

# Memory service health
curl http://localhost:8000/health

# MCP server health
python test_eva_tools.py
```

### Performance Metrics
- Response time per query
- Memory search performance
- Token usage tracking
- MCP tool execution times

### Logging
**Locations**:
- Main log: `eva.log`
- Memory service: `memory_service.log`
- Web interface: `web_interface.log`
- MCP server: `mcp_server.log`

## Troubleshooting

### Common Issues

#### Memory Service Connection
```bash
# Check memory service
curl http://localhost:8000/health

# Restart memory service
python simple_memory_service.py

# Check memory configuration
python -c "from eva.config import MEMORY_CONFIG; print(MEMORY_CONFIG)"
```

#### MCP Server Issues
```bash
# Test MCP server
python test_eva_tools.py

# Check MCP port
netstat -an | grep 8765

# Restart MCP server
python run_mcp_server.py --port 8765
```

#### API Key Problems
```bash
# Verify API keys
python test_openrouter.py

# Test specific provider
python -c "from eva.llm import test_provider; test_provider('openai')"
```

#### Training Issues
```bash
# Quick training test
python quick_eva_test.py

# Reset training data
rm -rf eva_training_data/

# Verify training
python test_eva_character_training.py
```

### Debug Commands
```bash
# Debug mode
python run_eva_agent.py --debug

# Verbose logging
EVA_LOG_LEVEL=DEBUG python eva

# Memory debug
python test_memory_tools.py --verbose

# MCP debug
python run_mcp_server.py --log-level DEBUG
```

## Maintenance

### Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update EVA core
git pull origin main
pip install -e .

# Update memory models
python update_memory_models.py
```

### Backup & Recovery
```bash
# Backup memory
python backup_memory.py --output eva_memory_backup.json

# Restore memory
python restore_memory.py --input eva_memory_backup.json

# Export training data
python export_training.py --format json
```

### Cleanup
```bash
# Clear logs
rm -f *.log

# Clear memory cache
python clear_memory_cache.py

# Reset EVA personality
python reset_eva_personality.py
```

---

**Repository**: ~/Projects/_archive/eva-agent/
**Status**: Archived Project
**Main Commands**: `./eva`, `./eva-ask`, `./eva-web`
**Last Updated**: 2025-07-05
**Memory Service**: Port 8000
**MCP Server**: Port 8765