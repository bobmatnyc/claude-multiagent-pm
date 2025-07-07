# MCP Memory Service Operations Guide

## Project Overview
Model Context Protocol (MCP) memory service providing persistent memory capabilities for AI agents and applications.

**Repository**: `~/Projects/_archive/mcp-memory-service/`
**Tech Stack**: Python, FastAPI, Docker, MCP Protocol
**Purpose**: Persistent memory layer for AI systems with MCP integration

## Local Development

### Prerequisites
```bash
# Python 3.8+
python3 --version
pip3 --version

# Docker (optional)
docker --version
docker-compose --version

# Node.js (for some utilities)
node --version
npm --version
```

### Installation
```bash
cd ~/Projects/_archive/mcp-memory-service

# Python setup
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Development installation
pip install -e .
```

### Environment Configuration
**File**: `.env`
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/memory_db
VECTOR_DB_URL=http://localhost:6333  # Qdrant

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=claude-...

# Service Configuration
MEMORY_SERVICE_PORT=8000
MCP_SERVER_PORT=8765
LOG_LEVEL=INFO

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=...

# Embeddings
EMBEDDING_MODEL=openai
EMBEDDING_DIMENSIONS=1536
```

## Core Services

### Memory Service
```bash
# Start memory service
python run_memory_service.py

# Custom port
python run_memory_service.py --port 8001

# Debug mode
python run_memory_service.py --debug
```

### MCP Server
```bash
# Start MCP server
python run_mcp_server.py

# Custom configuration
python run_mcp_server.py \
  --port 8765 \
  --memory-url http://localhost:8000 \
  --log-level DEBUG
```

## Docker Deployment

### Development Environment
```bash
# Start all services
docker-compose up -d

# Development with auto-reload
docker-compose -f docker-compose.dev.yml up

# View logs
docker-compose logs -f memory-service

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Production build
docker-compose -f docker-compose.production.yml up -d

# Scale services
docker-compose -f docker-compose.production.yml up --scale memory-service=3

# Health check
docker-compose ps
```

### Service Architecture
```yaml
# docker-compose.yml
services:
  memory-service:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - qdrant
      
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: memory_db
      POSTGRES_USER: memory_user
      POSTGRES_PASSWORD: memory_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
```

## API Endpoints

### Memory Operations
```bash
# Store memory
curl -X POST http://localhost:8000/memory \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User is working on Claude-PM project",
    "metadata": {"type": "project", "priority": "high"},
    "user_id": "user123"
  }'

# Search memory
curl "http://localhost:8000/memory/search?q=project&user_id=user123"

# Get memory by ID
curl http://localhost:8000/memory/123

# Update memory
curl -X PUT http://localhost:8000/memory/123 \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated content"}'

# Delete memory
curl -X DELETE http://localhost:8000/memory/123
```

### Memory Collections
```bash
# Create collection
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "projects", "description": "Project memories"}'

# List collections
curl http://localhost:8000/collections

# Add memory to collection
curl -X POST http://localhost:8000/collections/projects/memories \
  -H "Content-Type: application/json" \
  -d '{"content": "Memory content"}'
```

### System Operations
```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/status

# Metrics
curl http://localhost:8000/metrics

# Database stats
curl http://localhost:8000/stats
```

## MCP Integration

### MCP Tools Available
- **memory_store** - Store new memory
- **memory_search** - Search existing memories
- **memory_get** - Get specific memory
- **memory_update** - Update memory content
- **memory_delete** - Delete memory
- **collection_create** - Create memory collection
- **collection_list** - List collections

### MCP Client Configuration
```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["~/Projects/_archive/mcp-memory-service/run_mcp_server.py"],
      "env": {
        "MEMORY_SERVICE_URL": "http://localhost:8000",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### MCP Usage Examples
```python
# Using MCP client
from mcp import Client

client = Client("memory")

# Store memory
await client.call_tool("memory_store", {
    "content": "Important project decision",
    "metadata": {"type": "decision"},
    "user_id": "user123"
})

# Search memories
results = await client.call_tool("memory_search", {
    "query": "project decisions",
    "user_id": "user123",
    "limit": 10
})
```

## Configuration

### Memory Service Configuration
```python
# config.py
MEMORY_CONFIG = {
    "database": {
        "url": "postgresql://user:pass@localhost:5432/memory_db",
        "pool_size": 10,
        "echo": False
    },
    "vector_db": {
        "type": "qdrant",
        "url": "http://localhost:6333",
        "collection_name": "memories",
        "dimension": 1536
    },
    "embeddings": {
        "provider": "openai",
        "model": "text-embedding-ada-002",
        "api_key": "sk-..."
    },
    "search": {
        "similarity_threshold": 0.8,
        "max_results": 50,
        "rerank": True
    }
}
```

### MCP Server Configuration
```python
# mcp_config.py
MCP_CONFIG = {
    "server": {
        "name": "memory-service",
        "version": "1.0.0",
        "port": 8765
    },
    "tools": {
        "memory_store": {"enabled": True},
        "memory_search": {"enabled": True},
        "memory_get": {"enabled": True},
        "memory_update": {"enabled": True},
        "memory_delete": {"enabled": True}
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
```

## Database Management

### PostgreSQL Operations
```bash
# Connect to database
psql -h localhost -U memory_user -d memory_db

# Backup database
pg_dump -h localhost -U memory_user memory_db > backup.sql

# Restore database
psql -h localhost -U memory_user memory_db < backup.sql

# Run migrations
python manage.py migrate
```

### Qdrant Operations
```bash
# Check Qdrant status
curl http://localhost:6333/health

# List collections
curl http://localhost:6333/collections

# Collection info
curl http://localhost:6333/collections/memories

# Create collection
curl -X PUT http://localhost:6333/collections/memories \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

## Monitoring

### Health Checks
```bash
# Service health
curl http://localhost:8000/health

# Database connectivity
python -c "from memory_service.db import check_db_connection; check_db_connection()"

# Vector database health
curl http://localhost:6333/health

# MCP server health
python test_mcp_connection.py
```

### Performance Monitoring
```bash
# Memory service metrics
curl http://localhost:8000/metrics

# Database performance
python monitor_db_performance.py

# Vector search performance
python benchmark_search.py
```

### Logging
**Locations**:
- Memory service: `memory_service.log`
- MCP server: `mcp_server.log`
- Database: `database.log`
- Vector operations: `vector.log`

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Test database connection
python -c "from memory_service.db import test_connection; test_connection()"

# Check PostgreSQL status
docker-compose ps postgres

# Reset database
docker-compose down postgres
docker volume rm mcp-memory-service_postgres_data
docker-compose up postgres
```

#### Vector Database Issues
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Restart Qdrant
docker-compose restart qdrant

# Clear vector data
curl -X DELETE http://localhost:6333/collections/memories
```

#### MCP Server Issues
```bash
# Test MCP server
python test_mcp_server.py

# Check MCP port
netstat -an | grep 8765

# Debug MCP communication
python debug_mcp_protocol.py
```

#### Memory Search Issues
```bash
# Test embedding generation
python test_embeddings.py

# Verify vector similarity
python test_vector_search.py

# Check search parameters
python debug_search_query.py
```

### Debug Commands
```bash
# Debug mode startup
python run_memory_service.py --debug

# Verbose MCP logging
MCP_LOG_LEVEL=DEBUG python run_mcp_server.py

# Database query logging
DATABASE_ECHO=true python run_memory_service.py

# Vector operation debugging
VECTOR_DEBUG=true python run_memory_service.py
```

## Maintenance

### Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Docker images
docker-compose pull
docker-compose up -d --force-recreate

# Database migrations
python migrate_database.py
```

### Backup & Recovery
```bash
# Full backup
python backup_full_system.py --output backup_$(date +%Y%m%d).tar.gz

# Memory data backup
python backup_memories.py --format json

# Vector data backup
python backup_vectors.py --collection memories

# Restore from backup
python restore_system.py --input backup_20250705.tar.gz
```

### Cleanup
```bash
# Clear old memories (90+ days)
python cleanup_old_memories.py --days 90

# Vacuum database
python vacuum_database.py

# Optimize vector index
python optimize_vector_index.py

# Clear logs
find . -name "*.log" -mtime +30 -delete
```

---

**Repository**: ~/Projects/_archive/mcp-memory-service/
**Status**: Archived Project
**Memory Service**: Port 8000
**MCP Server**: Port 8765
**Database**: PostgreSQL + Qdrant
**Last Updated**: 2025-07-05
**Docker**: Multi-service architecture