# ClaudePMMemory Setup and Configuration Guide

This guide provides step-by-step instructions for setting up and configuring the ClaudePMMemory class in your Claude PM Framework environment.

## Prerequisites

1. **Python 3.8+** with async support
2. **mem0AI service** running on port 8002
3. **Claude PM Framework** installed
4. **Required dependencies** installed

## Installation

### 1. Install Dependencies

```bash
# Install required packages
pip install aiohttp asyncio

# Or install from requirements
pip install -r requirements/base.txt
```

### 2. Verify mem0AI Service

```bash
# Check if mem0AI service is running
curl http://localhost:8002/health

# Expected response: HTTP 200 OK
```

### 3. Test Basic Connection

```python
import asyncio
from claude_pm.services.claude_pm_memory import ClaudePMMemory

async def test_connection():
    memory = ClaudePMMemory()
    connected = await memory.connect()
    print(f"Connection successful: {connected}")
    await memory.disconnect()

asyncio.run(test_connection())
```

## Configuration Options

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# mem0AI Service Configuration
CLAUDE_PM_MEMORY_HOST=localhost
CLAUDE_PM_MEMORY_PORT=8002
CLAUDE_PM_MEMORY_API_KEY=your_api_key_here
CLAUDE_PM_MEMORY_TIMEOUT=30

# Connection Pool Settings
CLAUDE_PM_MEMORY_POOL_SIZE=10
CLAUDE_PM_MEMORY_MAX_RETRIES=3
CLAUDE_PM_MEMORY_RETRY_DELAY=1.0

# Performance Settings
CLAUDE_PM_MEMORY_BATCH_SIZE=100
CLAUDE_PM_MEMORY_CACHE_TTL=300
CLAUDE_PM_MEMORY_ENABLE_LOGGING=true
```

### Configuration File

Create `config/memory_config.yaml`:

```yaml
# Claude PM Memory Configuration
memory:
  service:
    host: localhost
    port: 8002
    api_key: ${MEMORY_API_KEY}
    timeout: 30
  
  connection:
    pool_size: 10
    max_retries: 3
    retry_delay: 1.0
    enable_cleanup: true
  
  performance:
    batch_size: 100
    cache_ttl: 300
    max_memory_size: 1000
    compression_enabled: true
  
  logging:
    enable_logging: true
    log_level: INFO
    log_operations: true
    log_performance: true
```

### Python Configuration

```python
# config/memory_settings.py
from claude_pm.services.claude_pm_memory import ClaudePMConfig
import os

# Development configuration
DEV_CONFIG = ClaudePMConfig(
    host="localhost",
    port=8002,
    timeout=10,
    max_retries=2,
    retry_delay=0.5,
    connection_pool_size=5,
    enable_logging=True
)

# Production configuration
PROD_CONFIG = ClaudePMConfig(
    host=os.getenv("MEMORY_SERVICE_HOST", "memory-service"),
    port=int(os.getenv("MEMORY_SERVICE_PORT", "8002")),
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    connection_pool_size=20,
    enable_logging=True,
    api_key=os.getenv("MEMORY_SERVICE_API_KEY")
)

# Load configuration based on environment
def get_memory_config():
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return PROD_CONFIG
    return DEV_CONFIG
```

## Framework Integration

### 1. Update Claude PM Services

Add to `claude_pm/services/__init__.py`:

```python
from .claude_pm_memory import ClaudePMMemory, create_claude_pm_memory, claude_pm_memory_context

__all__ = [
    'ClaudePMMemory',
    'create_claude_pm_memory', 
    'claude_pm_memory_context'
]
```

### 2. Update Base Service

Integrate with existing service framework in `claude_pm/core/base_service.py`:

```python
class BaseService:
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(name)
        
        # Add memory service integration
        self._memory_service: Optional[ClaudePMMemory] = None
    
    async def get_memory_service(self) -> Optional[ClaudePMMemory]:
        """Get memory service instance."""
        if not self._memory_service:
            from .services.claude_pm_memory import create_claude_pm_memory
            self._memory_service = create_claude_pm_memory()
            await self._memory_service.connect()
        
        return self._memory_service
    
    async def cleanup_memory_service(self):
        """Cleanup memory service."""
        if self._memory_service:
            await self._memory_service.disconnect()
            self._memory_service = None
```

### 3. Service Manager Integration

Update `claude_pm/core/service_manager.py`:

```python
from .services.claude_pm_memory import ClaudePMMemory, create_claude_pm_memory

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.memory_service: Optional[ClaudePMMemory] = None
    
    async def start_services(self):
        """Start all services including memory service."""
        try:
            # Initialize memory service
            self.memory_service = create_claude_pm_memory()
            await self.memory_service.connect()
            
            self.logger.info("Memory service started successfully")
            
            # Start other services...
            
        except Exception as e:
            self.logger.error(f"Failed to start memory service: {e}")
            raise
    
    async def stop_services(self):
        """Stop all services."""
        if self.memory_service:
            await self.memory_service.disconnect()
            self.memory_service = None
        
        # Stop other services...
```

## Project Setup Examples

### 1. Simple Project Setup

```python
# examples/simple_setup.py
import asyncio
from claude_pm.services.claude_pm_memory import claude_pm_memory_context, MemoryCategory

async def setup_project():
    async with claude_pm_memory_context() as memory:
        # Create project memory space
        project_response = await memory.create_project_memory_space(
            project_name="my_first_project",
            description="Learning to use ClaudePM Memory"
        )
        
        if project_response.success:
            print("✅ Project memory space created")
            
            # Store initial decision
            decision_response = await memory.store_project_decision(
                project_name="my_first_project",
                decision="Use ClaudePM for project management",
                context="Need intelligent memory for project decisions",
                reasoning="ClaudePM provides AI-enhanced memory capabilities"
            )
            
            print(f"✅ Initial decision stored: {decision_response.memory_id}")
        else:
            print(f"❌ Failed to create project: {project_response.error}")

asyncio.run(setup_project())
```

### 2. Team Project Setup

```python
# examples/team_setup.py
import asyncio
from claude_pm.services.claude_pm_memory import claude_pm_memory_context, MemoryCategory

async def setup_team_project():
    async with claude_pm_memory_context() as memory:
        project_name = "team_collaboration_platform"
        
        # Create project space
        await memory.create_project_memory_space(
            project_name=project_name,
            description="Team collaboration platform with real-time features",
            metadata={
                "team_size": 8,
                "duration_months": 6,
                "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
                "budget": "high"
            }
        )
        
        # Store team standards
        standards = [
            {
                "name": "Python Code Style",
                "description": "Use Black formatter with 88 character line length",
                "examples": ["black --line-length 88 .", "import isort"],
                "enforcement": "required"
            },
            {
                "name": "Git Workflow", 
                "description": "Feature branch workflow with PR reviews",
                "examples": ["git checkout -b feature/new-feature", "git push origin feature/new-feature"],
                "enforcement": "required"
            },
            {
                "name": "Testing Standards",
                "description": "Minimum 80% test coverage with pytest",
                "examples": ["pytest --cov=src --cov-report=html", "pytest tests/"],
                "enforcement": "recommended"
            }
        ]
        
        for standard in standards:
            await memory.store_team_standard(
                project_name=project_name,
                standard_name=standard["name"],
                description=standard["description"],
                examples=standard["examples"],
                enforcement_level=standard["enforcement"],
                tags=["team", "standards", "workflow"]
            )
        
        # Store architectural decisions
        decisions = [
            {
                "decision": "Use FastAPI for backend API",
                "context": "Need high-performance async API with automatic documentation",
                "reasoning": "FastAPI provides excellent performance, type hints, and OpenAPI support",
                "alternatives": ["Flask", "Django Rest Framework", "Tornado"]
            },
            {
                "decision": "Use PostgreSQL for primary database",
                "context": "Need ACID compliance and complex query support",
                "reasoning": "PostgreSQL offers excellent performance, JSON support, and reliability",
                "alternatives": ["MySQL", "MongoDB", "SQLite"]
            },
            {
                "decision": "Use React for frontend",
                "context": "Need interactive user interface with real-time updates",
                "reasoning": "React provides component-based architecture and excellent ecosystem",
                "alternatives": ["Vue.js", "Angular", "Svelte"]
            }
        ]
        
        for decision in decisions:
            await memory.store_project_decision(
                project_name=project_name,
                decision=decision["decision"],
                context=decision["context"],
                reasoning=decision["reasoning"],
                alternatives=decision["alternatives"],
                tags=["architecture", "technology"]
            )
        
        print(f"✅ Team project '{project_name}' setup complete!")
        
        # Get project statistics
        stats_response = await memory.get_project_statistics(project_name)
        if stats_response.success:
            stats = stats_response.data
            print(f"📊 Project has {stats['total_memories']} memories stored")
            print(f"📊 Categories: {stats['by_category']}")

asyncio.run(setup_team_project())
```

## Health Monitoring Setup

### 1. Health Check Service

```python
# claude_pm/monitoring/memory_health.py
import asyncio
import logging
from datetime import datetime
from claude_pm.services.claude_pm_memory import create_claude_pm_memory

class MemoryHealthMonitor:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        self.memory = create_claude_pm_memory()
        self.is_running = False
    
    async def start_monitoring(self):
        """Start health monitoring."""
        self.is_running = True
        self.logger.info("Starting memory service health monitoring")
        
        while self.is_running:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def perform_health_check(self):
        """Perform comprehensive health check."""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "connection_status": False,
            "response_time": 0.0,
            "statistics": {},
            "alerts": []
        }
        
        try:
            # Test connection
            start_time = datetime.now()
            connected = await self.memory.connect()
            end_time = datetime.now()
            
            health_data["connection_status"] = connected
            health_data["response_time"] = (end_time - start_time).total_seconds()
            
            if connected:
                # Get statistics
                stats = self.memory.get_statistics()
                health_data["statistics"] = stats
                
                # Check for issues
                if stats["success_rate"] < 95:
                    health_data["alerts"].append("Low success rate")
                
                if stats["avg_response_time"] > 2.0:
                    health_data["alerts"].append("High response time")
                
                await self.memory.disconnect()
            else:
                health_data["alerts"].append("Connection failed")
            
        except Exception as e:
            health_data["alerts"].append(f"Health check error: {e}")
        
        # Log health status
        if health_data["alerts"]:
            self.logger.warning(f"Memory service health issues: {health_data['alerts']}")
        else:
            self.logger.info("Memory service health check passed")
        
        return health_data
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_running = False
        self.logger.info("Stopping memory service health monitoring")

# Usage
monitor = MemoryHealthMonitor(check_interval=30)
asyncio.run(monitor.start_monitoring())
```

### 2. Integration with Health Monitor Service

```python
# claude_pm/services/health_monitor.py (update existing)
from .monitoring.memory_health import MemoryHealthMonitor

class HealthMonitor(BaseService):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("health_monitor", config)
        self.memory_monitor = MemoryHealthMonitor()
    
    async def _start_custom_tasks(self) -> Optional[List[asyncio.Task]]:
        """Start health monitoring tasks."""
        tasks = []
        
        # Start memory health monitoring
        task = asyncio.create_task(self.memory_monitor.start_monitoring())
        tasks.append(task)
        
        return tasks
    
    async def _cleanup(self):
        """Cleanup health monitoring."""
        self.memory_monitor.stop_monitoring()
        await super()._cleanup()
```

## Testing Setup

### 1. Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from claude_pm.services.claude_pm_memory import ClaudePMConfig, ClaudePMMemory

@pytest.fixture
def test_memory_config():
    """Test configuration for memory service."""
    return ClaudePMConfig(
        host="localhost",
        port=8002,
        timeout=5,
        max_retries=1,
        retry_delay=0.1,
        connection_pool_size=2,
        enable_logging=False
    )

@pytest.fixture
async def memory_service(test_memory_config):
    """Create and connect memory service for testing."""
    memory = ClaudePMMemory(test_memory_config)
    connected = await memory.connect()
    
    if not connected:
        pytest.skip("mem0AI service not available for testing")
    
    yield memory
    
    await memory.disconnect()

@pytest.fixture
def test_project_name():
    """Generate unique test project name."""
    import uuid
    return f"test_project_{uuid.uuid4().hex[:8]}"
```

### 2. Integration Tests

```python
# tests/integration/test_memory_integration.py
import pytest
from claude_pm.services.claude_pm_memory import MemoryCategory

@pytest.mark.asyncio
class TestMemoryIntegration:
    
    async def test_project_lifecycle(self, memory_service, test_project_name):
        """Test complete project memory lifecycle."""
        # Create project space
        response = await memory_service.create_project_memory_space(test_project_name)
        assert response.success
        
        # Store decision
        decision_response = await memory_service.store_project_decision(
            project_name=test_project_name,
            decision="Use pytest for testing",
            context="Need reliable testing framework",
            reasoning="Pytest provides excellent fixtures and plugins"
        )
        assert decision_response.success
        
        # Search memories
        search_response = await memory_service.retrieve_memories(
            category=MemoryCategory.PROJECT,
            query="pytest",
            project_filter=test_project_name
        )
        assert search_response.success
        assert len(search_response.data["memories"]) > 0
        
        # Get statistics
        stats_response = await memory_service.get_project_statistics(test_project_name)
        assert stats_response.success
        assert stats_response.data["total_memories"] > 0
```

## Production Deployment

### 1. Docker Configuration

```dockerfile
# Dockerfile.memory-service
FROM python:3.9-slim

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/production.txt

COPY claude_pm/ claude_pm/
COPY config/ config/

# Environment variables
ENV CLAUDE_PM_MEMORY_HOST=memory-service
ENV CLAUDE_PM_MEMORY_PORT=8002
ENV CLAUDE_PM_MEMORY_POOL_SIZE=50
ENV CLAUDE_PM_MEMORY_ENABLE_LOGGING=true

CMD ["python", "-m", "claude_pm.services.memory_service"]
```

### 2. Docker Compose

```yaml
# docker-compose.memory.yml
version: '3.8'

services:
  memory-service:
    image: mem0ai/mem0:latest
    ports:
      - "8002:8002"
    environment:
      - MEM0_API_KEY=${MEM0_API_KEY}
    volumes:
      - memory_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  claude-pm:
    build:
      context: .
      dockerfile: Dockerfile.memory-service
    depends_on:
      - memory-service
    environment:
      - CLAUDE_PM_MEMORY_HOST=memory-service
      - CLAUDE_PM_MEMORY_PORT=8002
      - CLAUDE_PM_MEMORY_API_KEY=${MEM0_API_KEY}
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

volumes:
  memory_data:
```

### 3. Kubernetes Deployment

```yaml
# k8s/memory-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memory-service
  template:
    metadata:
      labels:
        app: memory-service
    spec:
      containers:
      - name: memory-service
        image: mem0ai/mem0:latest
        ports:
        - containerPort: 8002
        env:
        - name: MEM0_API_KEY
          valueFrom:
            secretKeyRef:
              name: memory-secrets
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: memory-service
spec:
  selector:
    app: memory-service
  ports:
  - port: 8002
    targetPort: 8002
  type: ClusterIP
```

## Troubleshooting

### Common Setup Issues

1. **Connection Refused**
   ```bash
   # Check if mem0AI service is running
   curl http://localhost:8002/health
   
   # Check logs
   docker logs memory-service
   ```

2. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la config/
   
   # Fix permissions
   chmod 644 config/memory_config.yaml
   ```

3. **Import Errors**
   ```python
   # Verify installation
   python -c "from claude_pm.services.claude_pm_memory import ClaudePMMemory; print('OK')"
   ```

4. **Memory Issues**
   ```python
   # Check memory usage
   import psutil
   print(f"Memory usage: {psutil.virtual_memory().percent}%")
   ```

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('claude_pm.services.claude_pm_memory')
logger.setLevel(logging.DEBUG)
```

## Next Steps

1. **Start with simple setup** and verify connectivity
2. **Create your first project** memory space
3. **Store some test memories** to verify functionality
4. **Set up health monitoring** for production use
5. **Integrate with your workflows** and agents
6. **Monitor performance** and optimize configuration

For more advanced usage, see:
- [Integration Guide](CLAUDE_PM_MEMORY_INTEGRATION.md)
- [API Reference](../claude_pm/services/claude_pm_memory.py)
- [Example Projects](../examples/)