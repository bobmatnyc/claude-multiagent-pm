# Claude PM Memory Integration Guide v3.1.0

This guide provides comprehensive documentation for using the zero-configuration memory integration in Claude PM Framework v3.1.0.

## Overview

Claude PM Memory v3.1.0 delivers zero-configuration universal memory access that eliminates setup complexity while providing enterprise-grade memory management. The system automatically discovers and connects to memory services, making memory integration seamless across all agents and projects.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Integration Examples](#integration-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### Zero-Configuration Memory Access

```python
# Zero-configuration memory access - no setup required
from config.memory_config import create_claude_pm_memory

# Automatic service discovery and connection
memory = create_claude_pm_memory()

# Instant memory operations - no configuration needed
async def zero_config_usage():
    async with claude_pm_memory_context() as memory:
        # Create a project memory space
        response = await memory.create_project_memory_space("my_project")
        print(f"Space created: {response.success}")
        
        # Store a project decision
        decision_response = await memory.store_project_decision(
            project_name="my_project",
            decision="Use FastAPI for REST API",
            context="Need high-performance async API",
            reasoning="FastAPI provides excellent performance and documentation",
            alternatives=["Flask", "Django Rest Framework"]
        )
        print(f"Decision stored: {decision_response.memory_id}")

# Run the example
asyncio.run(basic_usage())
```

### Synchronous Usage

```python
from claude_pm.services.claude_pm_memory import create_claude_pm_memory, MemoryCategory

# Create memory instance
memory = create_claude_pm_memory()

# Use synchronous methods
response = memory.create_project_memory_space_sync("my_project")
print(f"Space created: {response.success}")

memory_response = memory.store_memory_sync(
    category=MemoryCategory.PATTERN,
    content="Repository pattern for database access",
    project_name="my_project",
    tags=["pattern", "database"]
)
print(f"Memory stored: {memory_response.memory_id}")
```

## Configuration

### ClaudePMConfig Options

```python
from claude_pm.services.claude_pm_memory import ClaudePMConfig, ClaudePMMemory

config = ClaudePMConfig(
    host="localhost",              # mem0AI service host
    port=8002,                     # mem0AI service port
    timeout=30,                    # Request timeout in seconds
    max_retries=3,                 # Maximum retry attempts
    retry_delay=1.0,               # Initial retry delay
    connection_pool_size=10,       # HTTP connection pool size
    enable_logging=True,           # Enable operation logging
    api_key=None,                  # Optional API key
    
    # Advanced options
    batch_size=100,                # Batch operation size
    cache_ttl=300,                 # Cache TTL in seconds
    max_memory_size=1000,          # Max memory usage in MB
    compression_enabled=True       # Enable compression
)

memory = ClaudePMMemory(config)
```

### Environment Variables

You can also configure using environment variables:

```bash
export CLAUDE_PM_MEMORY_HOST=localhost
export CLAUDE_PM_MEMORY_PORT=8002
export CLAUDE_PM_MEMORY_API_KEY=your_api_key
export CLAUDE_PM_MEMORY_TIMEOUT=30
```

## Core Concepts

### Memory Categories

ClaudePMMemory supports four main memory categories:

1. **PROJECT**: Architectural decisions, requirements, milestones
2. **PATTERN**: Successful solutions, code patterns, best practices  
3. **TEAM**: Coding standards, team preferences, workflows
4. **ERROR**: Bug patterns, error solutions, debugging knowledge

### Memory Response Object

All operations return a `MemoryResponse` object:

```python
@dataclass
class MemoryResponse:
    success: bool                    # Operation success status
    data: Optional[Dict[str, Any]]   # Response data
    error: Optional[str]             # Error message if failed
    memory_id: Optional[str]         # Memory ID for storage operations
    operation: Optional[str]         # Operation name
    timestamp: datetime              # Operation timestamp
```

### Project Memory Spaces

Each project gets its own isolated memory space:

```python
# Create project space
await memory.create_project_memory_space(
    project_name="ecommerce_platform",
    description="E-commerce platform development project",
    metadata={
        "team": "backend_team",
        "priority": "high",
        "deadline": "2024-03-01"
    }
)
```

## API Reference

### Connection Management

#### `async connect() -> bool`
Connect to mem0AI service with connection pooling.

#### `async disconnect() -> None`  
Disconnect and cleanup resources.

#### `is_connected() -> bool`
Check connection status.

#### `async ensure_connection() -> bool`
Ensure connection is active, reconnect if necessary.

### Project Memory Spaces

#### `async create_project_memory_space(project_name: str, description: str = "", metadata: Optional[Dict] = None) -> MemoryResponse`
Create an isolated memory space for a project.

#### `async delete_project_memory_space(project_name: str) -> MemoryResponse`
Delete a project memory space.

#### `async list_project_spaces() -> MemoryResponse`
List all project memory spaces.

### Core Memory Operations

#### `async store_memory(category: MemoryCategory, content: str, metadata: Optional[Dict] = None, project_name: Optional[str] = None, tags: Optional[List[str]] = None) -> MemoryResponse`
Store a memory in the specified category.

#### `async retrieve_memories(category: Optional[MemoryCategory] = None, query: str = "", project_filter: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 10) -> MemoryResponse`
Retrieve memories with filtering options.

#### `async update_memory(memory_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> MemoryResponse`
Update an existing memory.

#### `async delete_memory(memory_id: str) -> MemoryResponse`
Delete a memory.

#### `async get_memory_by_id(memory_id: str) -> MemoryResponse`
Get a specific memory by ID.

### High-Level Convenience Methods

#### `async store_project_decision(project_name: str, decision: str, context: str, reasoning: str, alternatives: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> MemoryResponse`
Store an architectural decision.

#### `async store_code_pattern(project_name: str, pattern_name: str, description: str, code: str, use_cases: List[str], tags: Optional[List[str]] = None) -> MemoryResponse`
Store a reusable code pattern.

#### `async store_error_solution(project_name: str, error_description: str, solution: str, root_cause: str, prevention: str, tags: Optional[List[str]] = None) -> MemoryResponse`
Store an error solution.

#### `async store_team_standard(project_name: str, standard_name: str, description: str, examples: List[str], enforcement_level: str = "recommended", tags: Optional[List[str]] = None) -> MemoryResponse`
Store a team coding standard.

### Statistics and Monitoring

#### `get_statistics() -> Dict[str, Any]`
Get comprehensive operation statistics.

#### `async get_project_statistics(project_name: str) -> MemoryResponse`
Get statistics for a specific project.

## Integration Examples

### 1. Framework Integration

```python
# claude_pm/integrations/memory_enhanced_agent.py
from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory

class MemoryEnhancedAgent:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.memory = ClaudePMMemory()
        
    async def start(self):
        """Initialize agent with memory capabilities."""
        await self.memory.connect()
        await self.memory.create_project_memory_space(self.project_name)
    
    async def remember_decision(self, decision: str, context: str, reasoning: str):
        """Store architectural decisions for future reference."""
        return await self.memory.store_project_decision(
            project_name=self.project_name,
            decision=decision,
            context=context,
            reasoning=reasoning
        )
    
    async def find_similar_patterns(self, query: str):
        """Find similar code patterns from memory."""
        return await self.memory.retrieve_memories(
            category=MemoryCategory.PATTERN,
            query=query,
            project_filter=self.project_name
        )
    
    async def learn_from_error(self, error: str, solution: str, root_cause: str):
        """Store error solutions for future debugging."""
        return await self.memory.store_error_solution(
            project_name=self.project_name,
            error_description=error,
            solution=solution,
            root_cause=root_cause,
            prevention=f"Implement validation to prevent {root_cause}"
        )
```

### 2. Project Management Integration

```python
# claude_pm/services/enhanced_project_service.py
from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory

class EnhancedProjectService:
    def __init__(self):
        self.memory = ClaudePMMemory()
    
    async def create_project(self, project_data: dict):
        """Create project with memory space."""
        project_name = project_data["name"]
        
        # Create project memory space
        memory_response = await self.memory.create_project_memory_space(
            project_name=project_name,
            description=project_data.get("description", ""),
            metadata={
                "created_by": project_data.get("owner"),
                "team_size": project_data.get("team_size", 0),
                "technology_stack": project_data.get("tech_stack", [])
            }
        )
        
        if memory_response.success:
            # Store initial project decisions
            for decision in project_data.get("initial_decisions", []):
                await self.memory.store_project_decision(
                    project_name=project_name,
                    decision=decision["name"],
                    context=decision["context"],
                    reasoning=decision["reasoning"]
                )
        
        return memory_response
    
    async def get_project_insights(self, project_name: str):
        """Get AI-powered project insights from memory."""
        stats = await self.memory.get_project_statistics(project_name)
        
        # Retrieve key memories for insights
        decisions = await self.memory.retrieve_memories(
            category=MemoryCategory.PROJECT,
            project_filter=project_name,
            limit=50
        )
        
        patterns = await self.memory.retrieve_memories(
            category=MemoryCategory.PATTERN,
            project_filter=project_name,
            limit=20
        )
        
        errors = await self.memory.retrieve_memories(
            category=MemoryCategory.ERROR,
            project_filter=project_name,
            limit=10
        )
        
        return {
            "statistics": stats.data if stats.success else {},
            "key_decisions": decisions.data if decisions.success else [],
            "successful_patterns": patterns.data if patterns.success else [],
            "resolved_errors": errors.data if errors.success else []
        }
```

### 3. CLI Integration

```python
# claude_pm/cli/memory_commands.py
import click
from claude_pm.services.claude_pm_memory import create_claude_pm_memory, MemoryCategory

@click.group()
def memory():
    """Memory management commands."""
    pass

@memory.command()
@click.argument('project_name')
@click.option('--description', help='Project description')
def create_space(project_name, description):
    """Create a memory space for a project."""
    memory = create_claude_pm_memory()
    response = memory.create_project_memory_space_sync(project_name, description or "")
    
    if response.success:
        click.echo(f"✅ Memory space created for project: {project_name}")
    else:
        click.echo(f"❌ Failed to create memory space: {response.error}")

@memory.command()
@click.argument('project_name')
@click.argument('decision')
@click.option('--context', required=True, help='Decision context')
@click.option('--reasoning', required=True, help='Decision reasoning')
@click.option('--alternatives', help='Comma-separated alternatives')
def store_decision(project_name, decision, context, reasoning, alternatives):
    """Store a project decision."""
    memory = create_claude_pm_memory()
    
    alt_list = alternatives.split(',') if alternatives else []
    
    response = memory.store_memory_sync(
        category=MemoryCategory.PROJECT,
        content=f"Decision: {decision}\nContext: {context}\nReasoning: {reasoning}",
        project_name=project_name,
        metadata={
            "decision": decision,
            "context": context,
            "reasoning": reasoning,
            "alternatives": alt_list
        },
        tags=["decision", "architecture"]
    )
    
    if response.success:
        click.echo(f"✅ Decision stored with ID: {response.memory_id}")
    else:
        click.echo(f"❌ Failed to store decision: {response.error}")

@memory.command()
@click.argument('project_name')
@click.argument('query')
@click.option('--category', type=click.Choice(['project', 'pattern', 'team', 'error']))
@click.option('--limit', default=10, help='Maximum results')
def search(project_name, query, category, limit):
    """Search memories in a project."""
    memory = create_claude_pm_memory()
    
    cat = None
    if category:
        cat = MemoryCategory(category)
    
    response = memory.retrieve_memories_sync(
        category=cat,
        query=query,
        project_filter=project_name,
        limit=limit
    )
    
    if response.success:
        memories = response.data.get('memories', [])
        click.echo(f"Found {len(memories)} memories:")
        for i, mem in enumerate(memories, 1):
            click.echo(f"{i}. {mem.get('content', '')[:100]}...")
    else:
        click.echo(f"❌ Search failed: {response.error}")
```

## Best Practices

### 1. Connection Management

```python
# ✅ Use async context manager for automatic cleanup
async with claude_pm_memory_context() as memory:
    # Your operations here
    pass

# ✅ Or manage connections explicitly
memory = ClaudePMMemory()
try:
    await memory.connect()
    # Your operations here
finally:
    await memory.disconnect()
```

### 2. Error Handling

```python
# ✅ Always check response.success
response = await memory.store_memory(...)
if response.success:
    print(f"Memory stored: {response.memory_id}")
else:
    print(f"Error: {response.error}")
    # Handle error appropriately

# ✅ Use try-catch for connection errors
try:
    async with claude_pm_memory_context() as memory:
        response = await memory.store_memory(...)
except Exception as e:
    print(f"Connection failed: {e}")
```

### 3. Memory Organization

```python
# ✅ Use descriptive project names
await memory.create_project_memory_space("ecommerce_backend_v2")

# ✅ Use consistent tagging
await memory.store_memory(
    category=MemoryCategory.PATTERN,
    content="Repository pattern implementation",
    tags=["pattern", "database", "python", "sqlalchemy"]
)

# ✅ Include rich metadata
await memory.store_project_decision(
    project_name="ecommerce_backend",
    decision="Use PostgreSQL for primary database",
    context="Need ACID compliance and complex queries",
    reasoning="PostgreSQL provides excellent performance and features",
    alternatives=["MySQL", "MongoDB"],
    tags=["database", "architecture", "postgresql"]
)
```

### 4. Performance Optimization

```python
# ✅ Use appropriate batch sizes for bulk operations
config = ClaudePMConfig(
    connection_pool_size=20,    # Higher for concurrent operations
    batch_size=50,              # Optimize based on memory size
    cache_ttl=600              # Longer for stable data
)

# ✅ Filter searches to reduce response size
response = await memory.retrieve_memories(
    category=MemoryCategory.PATTERN,
    project_filter="specific_project",
    tags=["python", "database"],
    limit=10  # Don't retrieve more than needed
)
```

## Troubleshooting

### Common Issues

#### 1. Connection Failures

```python
# Check mem0AI service status
memory = ClaudePMMemory()
if not await memory.connect():
    print("❌ Cannot connect to mem0AI service")
    print("✅ Ensure mem0AI is running on localhost:8002")
```

#### 2. Memory Storage Failures

```python
# Validate category before storing
if category not in [MemoryCategory.PROJECT, MemoryCategory.PATTERN, 
                   MemoryCategory.TEAM, MemoryCategory.ERROR]:
    print("❌ Invalid memory category")

# Check content size
if len(content) > 10000:  # Adjust based on your limits
    print("⚠️  Content might be too large")
```

#### 3. Search Performance Issues

```python
# Use specific queries instead of broad searches
response = await memory.retrieve_memories(
    query="FastAPI async database connection",  # ✅ Specific
    # query="database",  # ❌ Too broad
    category=MemoryCategory.PATTERN,
    limit=5
)
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('claude_pm.services.claude_pm_memory').setLevel(logging.DEBUG)

# Check statistics for performance insights
stats = memory.get_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Average response time: {stats['avg_response_time']:.3f}s")
```

### Health Monitoring

```python
# Regular health checks
async def monitor_memory_health():
    memory = ClaudePMMemory()
    
    if await memory.connect():
        stats = memory.get_statistics()
        
        # Check success rate
        if stats['success_rate'] < 95:
            print("⚠️  Memory service success rate is low")
        
        # Check response time
        if stats['avg_response_time'] > 1.0:
            print("⚠️  Memory service response time is high")
        
        await memory.disconnect()
    else:
        print("❌ Memory service is unavailable")
```

## Configuration Examples

### Development Environment

```python
dev_config = ClaudePMConfig(
    host="localhost",
    port=8002,
    timeout=10,
    max_retries=2,
    enable_logging=True
)
```

### Production Environment

```python
prod_config = ClaudePMConfig(
    host="memory-service.internal",
    port=8002,
    timeout=30,
    max_retries=3,
    connection_pool_size=50,
    enable_logging=True,
    api_key=os.getenv("MEMORY_SERVICE_API_KEY")
)
```

### High-Performance Environment

```python
perf_config = ClaudePMConfig(
    connection_pool_size=100,
    batch_size=200,
    cache_ttl=900,  # 15 minutes
    compression_enabled=True,
    max_memory_size=2000  # 2GB
)
```

## Next Steps

1. **Integration**: Integrate ClaudePMMemory into your Claude PM workflows
2. **Monitoring**: Set up health monitoring and alerting
3. **Optimization**: Profile and optimize for your specific use case
4. **Extension**: Build custom memory types for specialized needs
5. **Backup**: Implement memory backup and disaster recovery

For more information, see:
- [ClaudePM Framework Documentation](../README.md)
- [mem0AI Integration Guide](../integrations/mem0ai_integration.py)
- [Memory Schema Reference](../schemas/memory-schemas.py)