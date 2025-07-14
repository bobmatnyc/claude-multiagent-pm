# Integrations Comprehensive Guide - Claude PM Framework

## Overview

This comprehensive guide covers all integration aspects of the Claude PM Framework v4.5.1, including MCP service integration, GitHub API synchronization, memory system integration, and external service connectivity for enhanced development workflows.

## Table of Contents

1. [MCP Service Integration](#mcp-service-integration)
2. [Memory Integration](#memory-integration)
3. [GitHub API Integration](#github-api-integration)
4. [Integration Architecture](#integration-architecture)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## MCP Service Integration

### Overview

The Claude PM Framework includes comprehensive MCP (Model Context Protocol) service integration, enabling enhanced development workflows through productivity and context management tools.

### Supported MCP Services

#### MCP-Zen
**Purpose**: Second opinion service that validates responses with another LLM, plus mindfulness tools  
**Available Tools**: 
- `zen_quote` - Generate motivational zen quotes
- `breathing_exercise` - Provide breathing exercises for stress relief  
- `focus_timer` - Set focused work sessions

**Key Capability**: Provides alternative LLM perspective for response validation and decision-making

**Usage Contexts**:
- When needing a second opinion on complex technical decisions
- During critical code review processes requiring validation
- For validating architectural decisions with alternative perspective
- When seeking different approaches to challenging problems
- During stress management in development workflows

#### Context 7
**Purpose**: Up-to-date code documentation and library examples fetcher  
**Available Tools**:
- `resolve-library-id` - Resolve library names to Context7-compatible IDs
- `get-library-docs` - Fetch current documentation for any library

**Key Benefits**: Provides current, version-specific documentation instead of outdated training data

**Usage Contexts**:
- When needing current library documentation and examples
- For up-to-date API references and code samples
- When working with new or recently updated libraries
- To avoid hallucinated or outdated API information
- During development tasks requiring specific library knowledge

### Orchestrator Integration

#### Automatic Detection

The orchestrator automatically detects available MCP services during initialization and provides contextual recommendations based on:

1. **Workflow Type**: Multi-agent coordination, code development, project management
2. **Development Context**: Debugging, project switching, complex tasks
3. **Agent Task Type**: Specific agent roles and responsibilities

#### MCP-Enhanced Workflows

**Multi-Agent Coordination Workflow**

```python
# Orchestrator automatically detects and recommends:
{
    "task_start": "Use zen_quote for motivation, context_switch for project setup",
    "agent_handoff": "Use workflow_optimizer to optimize transitions", 
    "error_handling": "Use breathing_exercise for stress management",
    "task_completion": "Use project_memory to store learnings"
}
```

**Code Development Workflow**

```python
# Enhanced with productivity tools:
{
    "complex_task_start": "Use focus_timer to set dedicated work sessions",
    "debugging_session": "Use zen_quote for maintaining calm perspective", 
    "refactoring": "Use breathing_exercise before major changes"
}
```

**Library Integration Workflow**

```python
# Documentation-enhanced development:
{
    "library_selection": "Use resolve-library-id to identify proper library documentation",
    "implementation": "Use get-library-docs for current API references and examples", 
    "troubleshooting": "Use get-library-docs with specific topics for targeted help"
}
```

### Service Selection Logic

```python
def select_mcp_services_for_context(context: str, available_services: List[MCPService]) -> List[str]:
    """
    Select appropriate MCP services based on development context.
    
    Context-Service Mapping:
    - "debugging" -> MCP-Zen (breathing exercises, zen quotes)
    - "project_switching" -> Context 7 (context switching, project memory)
    - "complex_task_start" -> MCP-Zen (focus timer, motivation)
    - "multi_agent_coordination" -> Both services for comprehensive enhancement
    """
    recommendations = []
    
    if context in ["debugging", "stress_management", "difficult_bugs"]:
        if "mcp-zen" in available_services:
            recommendations.extend(["zen_quote", "breathing_exercise"])
    
    if context in ["project_switching", "context_management", "multi_project"]:
        if "context-7" in available_services:
            recommendations.extend(["context_switch", "project_memory"])
    
    if context in ["complex_task_start", "focused_work", "productivity"]:
        if "mcp-zen" in available_services:
            recommendations.append("focus_timer")
    
    return recommendations
```

### Usage Instructions for Orchestrator

#### Service Detection

The orchestrator should regularly check MCP service availability:

```python
# Check available services
mcp_status = await orchestrator.check_mcp_service_availability()

if mcp_status["orchestrator_ready"]:
    logger.info(f"Orchestrator enhanced with {mcp_status['total_services_detected']} MCP services")
else:
    logger.info("Consider installing MCP services for enhanced workflows")
```

#### Workflow Enhancement

When coordinating multi-agent tasks, the orchestrator should:

```python
# Get workflow-specific recommendations
recommendations = await orchestrator.get_mcp_service_recommendations(
    workflow_name="multi_agent_coordination"
)

# Apply recommendations to task execution
for recommendation in recommendations.get("workflow_recommendations", []):
    # Integrate MCP tools at appropriate workflow stages
    if "zen_quote" in recommendation["available_tools"]:
        # Use for motivation before complex tasks
        pass
    if "context_switch" in recommendation["available_tools"]:
        # Use for project context management
        pass
```

#### Context-Aware Service Usage

For specific development contexts:

```python
# Get services for specific contexts
debugging_services = await orchestrator.get_development_context_services("debugging")
project_switching_services = await orchestrator.get_development_context_services("project_switching")

# Apply context-specific enhancements
if debugging_services:
    # Use breathing exercises for stress management during debugging
    # Use zen quotes for maintaining perspective
    pass

if project_switching_services:
    # Use context switching tools for seamless transitions
    # Use project memory for maintaining state
    pass
```

### Configuration and Setup

#### Installation Verification

The orchestrator should verify MCP service installation:

```bash
# MCP-Zen verification
npx @modelcontextprotocol/server-zen --help

# Context 7 verification  
context-7-mcp --version
```

#### Configuration Integration

Services should be configured in Claude settings:

```json
{
  "mcpServers": {
    "zen": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-zen"]
    },
    "context7": {
      "command": "context-7-mcp", 
      "args": ["--port", "3007"]
    }
  }
}
```

## Memory Integration

### Overview

Claude PM Memory v4.0.0 delivers zero-configuration universal memory access that eliminates setup complexity while providing enterprise-grade memory management. The system automatically discovers and connects to memory services, making memory integration seamless across all agents and projects.

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
asyncio.run(zero_config_usage())
```

### Memory Categories

#### 1. Project Memory
**Purpose**: Track implementation decisions and architectural choices

```python
# Store project decisions
memory.add_project_memory(
    "Chose JWT over sessions for stateless authentication in microservices architecture"
)

# Record architectural choices
memory.add_project_memory(
    "Implemented Redis for token blacklist to handle logout securely"
)

# Store requirements and milestones
memory.add_project_memory(
    "Phase 1 MVP: User authentication, basic CRUD operations, deployment pipeline"
)
```

#### 2. Pattern Memory
**Purpose**: Successful patterns and best practices

```python
# Successful patterns for reuse
memory.add_pattern_memory(
    category="Authentication",
    pattern="JWT with refresh token rotation for enhanced security"
)

memory.add_pattern_memory(
    category="Error Handling", 
    pattern="Centralized error middleware with structured logging"
)

# Code patterns
memory.add_pattern_memory(
    category="Database",
    pattern="Repository pattern with dependency injection for testability"
)
```

#### 3. Team Memory
**Purpose**: Coding standards and team conventions

```python
# Coding standards and conventions
memory.add_team_memory(
    category="Code Style",
    standard="Use TypeScript strict mode for all new components"
)

memory.add_team_memory(
    category="Testing",
    standard="Minimum 80% test coverage for business logic"
)

# Team preferences
memory.add_team_memory(
    category="Architecture",
    standard="Prefer composition over inheritance for component design"
)
```

#### 4. Error Memory
**Purpose**: Issue patterns and resolution strategies

```python
# Common issues and solutions
memory.add_error_memory(
    error_type="CORS Configuration",
    solution="Add origin validation and credentials: true for secure cookies"
)

memory.add_error_memory(
    error_type="JWT Expiration",
    solution="Implement refresh token flow with automatic renewal"
)

# Performance issues
memory.add_error_memory(
    error_type="Database N+1 Query",
    solution="Use select_related() and prefetch_related() for Django ORM optimization"
)
```

### Configuration

#### ClaudePMConfig Options

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

#### Environment Variables

```bash
# Memory service configuration
CLAUDE_PM_MEMORY_HOST=localhost
CLAUDE_PM_MEMORY_PORT=8002
CLAUDE_PM_MEMORY_TIMEOUT=30
CLAUDE_PM_MEMORY_MAX_RETRIES=3
CLAUDE_PM_MEMORY_ENABLE_LOGGING=true

# Optional authentication
CLAUDE_PM_MEMORY_API_KEY=your_api_key_here

# Performance tuning
CLAUDE_PM_MEMORY_POOL_SIZE=10
CLAUDE_PM_MEMORY_BATCH_SIZE=100
```

### Service Health Check

```bash
# Verify memory service status
curl http://localhost:8002/health
# Expected: {"status": "healthy", "memory_service": "operational"}

# Check service version
curl http://localhost:8002/version
# Expected: {"version": "1.0.0", "api_version": "v1"}
```

### Agent Integration

```python
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator

# Memory-enhanced agent coordination
async def agent_with_memory():
    memory = create_claude_pm_memory()
    orchestrator = MultiAgentOrchestrator()
    
    # Get relevant patterns before delegation
    patterns = await memory.retrieve_memories(
        category=MemoryCategory.PATTERN,
        query="authentication security"
    )
    
    # Delegate task with memory context
    result = await orchestrator.delegate_task(
        agent_type="security",
        task="Review authentication implementation",
        context={
            "known_patterns": patterns,
            "project": "web_app_v2"
        }
    )
    
    # Store successful patterns
    if result.success:
        await memory.store_memory(
            category=MemoryCategory.PATTERN,
            content=result.pattern_summary,
            project_name="web_app_v2",
            tags=["security", "authentication", "review"]
        )
    
    return result
```

## GitHub API Integration

### Overview

This section provides comprehensive guidance for syncing Claude PM trackdown tickets to GitHub Issues using the GitHub API. It covers authentication, rate limiting, issues management, sync strategies, and implementation best practices.

### Authentication & Setup

#### Fine-Grained Tokens (Recommended)

Use fine-grained personal access tokens instead of classic PATs for better security:

```python
import requests
from typing import Dict, Any

class GitHubAPIClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        self._check_rate_limit(response)
        return response
    
    def _check_rate_limit(self, response: requests.Response):
        """Monitor rate limit headers and implement backoff if needed"""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining < 10:  # Warning threshold
            print(f"Rate limit warning: {remaining} requests remaining")
            print(f"Rate limit resets at: {reset_time}")
```

#### Required Token Permissions

For Claude PM ticket sync, your token needs these permissions:

**Repository Permissions:**
- `Issues`: Read and write (for creating/updating issues)
- `Metadata`: Read (for accessing repository metadata)
- `Pull requests`: Read (for linking issues to PRs)

**Organization Permissions (if applicable):**
- `Projects`: Read and write (for project board management)

### Rate Limiting Considerations

#### Rate Limit Monitoring

```python
import time
from typing import Optional
import logging

class RateLimitHandler:
    def __init__(self, client: GitHubAPIClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    def handle_rate_limit(self, response: requests.Response) -> bool:
        """Handle rate limit responses with exponential backoff"""
        if response.status_code == 403:
            rate_limit_exceeded = response.headers.get('X-RateLimit-Remaining') == '0'
            
            if rate_limit_exceeded:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - int(time.time()), 0) + 5  # 5 second buffer
                
                self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds")
                time.sleep(wait_time)
                return True
        
        return False
    
    def exponential_backoff(self, attempt: int, max_attempts: int = 5) -> bool:
        """Implement exponential backoff for retries"""
        if attempt >= max_attempts:
            return False
        
        wait_time = (2 ** attempt) + (random.uniform(0, 1))
        self.logger.info(f"Retry attempt {attempt + 1}, waiting {wait_time:.2f} seconds")
        time.sleep(wait_time)
        return True
```

### Issues Management via API

#### Creating Issues with Metadata

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re

@dataclass
class ClaudePMTicket:
    """Represents a Claude PM ticket from BACKLOG.md"""
    ticket_id: str
    title: str
    description: str
    epic: Optional[str]
    milestone: str
    priority: str
    story_points: int
    status: str
    labels: List[str]
    assignees: List[str]
    dependencies: List[str]

class GitHubIssueManager:
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository  # format: "owner/repo"
        self.rate_limiter = RateLimitHandler(client)
    
    def create_issue_from_ticket(self, ticket: ClaudePMTicket) -> Optional[Dict[str, Any]]:
        """Create GitHub issue from Claude PM ticket"""
        
        issue_body = self._format_issue_body(ticket)
        
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "body": issue_body,
            "labels": ticket.labels,
            "assignees": ticket.assignees
        }
        
        # Add milestone if it exists
        if milestone_number := self._get_milestone_number(ticket.milestone):
            issue_data["milestone"] = milestone_number
        
        return self._make_request_with_retry(
            "POST", 
            f"/repos/{self.repository}/issues",
            json=issue_data
        )
    
    def _format_issue_body(self, ticket: ClaudePMTicket) -> str:
        """Format issue body with Claude PM metadata"""
        body_parts = [
            f"**Claude PM Ticket:** {ticket.ticket_id}",
            f"**Priority:** {ticket.priority}",
            f"**Story Points:** {ticket.story_points}",
            f"**Milestone:** {ticket.milestone}",
        ]
        
        if ticket.epic:
            body_parts.append(f"**Epic:** {ticket.epic}")
        
        if ticket.dependencies:
            deps_list = ", ".join(ticket.dependencies)
            body_parts.append(f"**Dependencies:** {deps_list}")
        
        body_parts.extend([
            "",
            "## Description",
            ticket.description,
            "",
            "---",
            "*This issue was automatically created from Claude PM Framework trackdown system.*"
        ])
        
        return "\n".join(body_parts)
```

### Label Management System

```python
class GitHubLabelManager:
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
    
    def ensure_claude_pm_labels(self) -> bool:
        """Ensure all Claude PM labels exist in repository"""
        
        claude_pm_labels = [
            # Priority labels
            {"name": "priority-critical", "color": "B60205", "description": "Critical priority task"},
            {"name": "priority-high", "color": "D93F0B", "description": "High priority task"},
            {"name": "priority-medium", "color": "FBCA04", "description": "Medium priority task"},
            {"name": "priority-low", "color": "0E8A16", "description": "Low priority task"},
            
            # Type labels
            {"name": "type-memory", "color": "5319E7", "description": "Memory/AI related task"},
            {"name": "type-langgraph", "color": "1D76DB", "description": "LangGraph workflow task"},
            {"name": "type-infrastructure", "color": "0052CC", "description": "Infrastructure task"},
            {"name": "type-integration", "color": "5319E7", "description": "Integration task"},
            
            # Milestone labels
            {"name": "milestone-foundation", "color": "C5DEF5", "description": "M01 Foundation milestone"},
            {"name": "milestone-automation", "color": "BFD4F2", "description": "M02 Automation milestone"},
            {"name": "milestone-orchestration", "color": "D4C5F9", "description": "M03 Orchestration milestone"},
            
            # Epic labels
            {"name": "epic-fep-007", "color": "F9D0C4", "description": "Claude Max + mem0AI Enhanced Architecture"},
            {"name": "epic-fep-008", "color": "FEF2C0", "description": "Memory-Augmented Agent Ecosystem"},
            {"name": "epic-fep-009", "color": "C5DEF5", "description": "Intelligent Task Decomposition System"},
            
            # Status labels
            {"name": "status-blocked", "color": "E99695", "description": "Task is blocked"},
            {"name": "status-needs-review", "color": "FBCA04", "description": "Needs review"},
            {"name": "claude-pm-sync", "color": "7057FF", "description": "Synced from Claude PM Framework"}
        ]
        
        existing_labels = self._get_existing_labels()
        existing_names = {label['name'] for label in existing_labels}
        
        for label_data in claude_pm_labels:
            if label_data['name'] not in existing_names:
                self._create_label(label_data)
            else:
                self._update_label(label_data)
        
        return True
```

### Sync Strategy Implementation

#### Hybrid Sync Approach

```python
from enum import Enum
from datetime import datetime
import hashlib

class SyncDirection(Enum):
    CLAUDE_PM_TO_GITHUB = "claude_pm_to_github"
    GITHUB_TO_CLAUDE_PM = "github_to_claude_pm"
    BIDIRECTIONAL = "bidirectional"

class ClaudePMGitHubSync:
    def __init__(self, client: GitHubAPIClient, repository: str, 
                 backlog_path: str = "/Users/masa/Projects/claude-multiagent-pm/trackdown/BACKLOG.md"):
        self.client = client
        self.repository = repository
        self.backlog_path = backlog_path
        self.issue_manager = GitHubIssueManager(client, repository)
        self.label_manager = GitHubLabelManager(client, repository)
        
        # Sync tracking
        self.sync_records: Dict[str, SyncRecord] = {}
        self.sync_log_path = "/Users/masa/Projects/claude-multiagent-pm/sync/github_sync_log.json"
    
    def full_sync(self, direction: SyncDirection = SyncDirection.CLAUDE_PM_TO_GITHUB) -> Dict[str, Any]:
        """Perform full synchronization"""
        
        print("Starting Claude PM <-> GitHub sync...")
        
        # Ensure labels and milestones exist
        self.label_manager.ensure_claude_pm_labels()
        
        # Load existing sync records
        self._load_sync_records()
        
        if direction in [SyncDirection.CLAUDE_PM_TO_GITHUB, SyncDirection.BIDIRECTIONAL]:
            claude_results = self._sync_claude_pm_to_github()
        else:
            claude_results = {"synced": 0, "errors": 0}
        
        if direction in [SyncDirection.GITHUB_TO_CLAUDE_PM, SyncDirection.BIDIRECTIONAL]:
            github_results = self._sync_github_to_claude_pm()
        else:
            github_results = {"synced": 0, "errors": 0}
        
        # Save sync records
        self._save_sync_records()
        
        return {
            "success": True,
            "claude_pm_to_github": claude_results,
            "github_to_claude_pm": github_results,
            "timestamp": datetime.now().isoformat()
        }
```

### Complete Sync Script Example

```python
#!/usr/bin/env python3
"""
Claude PM to GitHub Issues Sync Script
Usage: python sync_github.py --repository owner/repo --token-file ~/.github_token
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Sync Claude PM tickets to GitHub Issues")
    parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--token-file", required=True, help="File containing GitHub token")
    parser.add_argument("--direction", choices=["to-github", "from-github", "bidirectional"], 
                       default="to-github", help="Sync direction")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without making changes")
    
    args = parser.parse_args()
    
    # Load token
    token_path = Path(args.token_file).expanduser()
    with open(token_path, 'r') as f:
        token = f.read().strip()
    
    # Initialize sync
    client = GitHubAPIClient(token)
    sync = ClaudePMGitHubSync(client, args.repository)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        # Implement dry run logic here
        return
    
    # Perform sync
    direction_map = {
        "to-github": SyncDirection.CLAUDE_PM_TO_GITHUB,
        "from-github": SyncDirection.GITHUB_TO_CLAUDE_PM,
        "bidirectional": SyncDirection.BIDIRECTIONAL
    }
    
    result = sync.full_sync(direction_map[args.direction])
    
    # Print results
    print(f"Sync completed at {result['timestamp']}")
    print(f"Claude PM -> GitHub: {result['claude_pm_to_github']['synced']} synced, "
          f"{result['claude_pm_to_github']['errors']} errors")
    print(f"GitHub -> Claude PM: {result['github_to_claude_pm']['synced']} synced, "
          f"{result['github_to_claude_pm']['errors']} errors")

if __name__ == "__main__":
    main()
```

## Integration Architecture

### Service Discovery and Connection

The Claude PM Framework employs automatic service discovery for all integrations:

```python
class IntegrationManager:
    def __init__(self):
        self.discovered_services = {}
        self.active_connections = {}
        
    async def discover_services(self):
        """Automatically discover available integration services"""
        
        # Memory service discovery
        if await self._check_service_health("http://localhost:8002/health"):
            self.discovered_services["memory"] = {
                "type": "mem0AI",
                "endpoint": "http://localhost:8002",
                "status": "available"
            }
        
        # MCP services discovery
        mcp_services = await self._discover_mcp_services()
        self.discovered_services.update(mcp_services)
        
        # GitHub API connectivity
        if await self._check_github_connectivity():
            self.discovered_services["github"] = {
                "type": "github_api",
                "status": "available"
            }
        
        return self.discovered_services
    
    async def _check_service_health(self, endpoint: str) -> bool:
        """Check if a service endpoint is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    return response.status == 200
        except:
            return False
    
    async def _discover_mcp_services(self) -> Dict[str, Any]:
        """Discover available MCP services"""
        mcp_services = {}
        
        # Check for MCP-Zen
        try:
            result = subprocess.run(
                ["npx", "@modelcontextprotocol/server-zen", "--help"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                mcp_services["mcp_zen"] = {
                    "type": "mcp_zen",
                    "status": "available",
                    "tools": ["zen_quote", "breathing_exercise", "focus_timer"]
                }
        except:
            pass
        
        # Check for Context 7
        try:
            result = subprocess.run(
                ["context-7-mcp", "--version"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                mcp_services["context_7"] = {
                    "type": "context_7",
                    "status": "available",
                    "tools": ["resolve-library-id", "get-library-docs"]
                }
        except:
            pass
        
        return mcp_services
```

### Integration Health Monitoring

```python
class IntegrationHealthMonitor:
    def __init__(self, integration_manager: IntegrationManager):
        self.integration_manager = integration_manager
        self.health_status = {}
        
    async def monitor_integrations(self):
        """Continuously monitor integration health"""
        while True:
            await self._check_all_integrations()
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_all_integrations(self):
        """Check health of all active integrations"""
        
        for service_name, service_info in self.integration_manager.discovered_services.items():
            try:
                if service_info["type"] == "mem0AI":
                    health = await self._check_memory_health()
                elif service_info["type"] == "github_api":
                    health = await self._check_github_health()
                elif service_info["type"].startswith("mcp_"):
                    health = await self._check_mcp_health(service_name)
                else:
                    health = {"status": "unknown"}
                
                self.health_status[service_name] = {
                    "timestamp": datetime.now().isoformat(),
                    "status": health.get("status", "unknown"),
                    "response_time": health.get("response_time", 0),
                    "error": health.get("error")
                }
                
            except Exception as e:
                self.health_status[service_name] = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of integration health"""
        total_services = len(self.health_status)
        healthy_services = sum(1 for status in self.health_status.values() 
                             if status["status"] == "healthy")
        
        return {
            "total_integrations": total_services,
            "healthy_integrations": healthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "last_check": datetime.now().isoformat(),
            "services": self.health_status
        }
```

## Best Practices

### Integration Development

1. **Progressive Enhancement**: Design integrations to enhance rather than replace core functionality
2. **Graceful Degradation**: Ensure system continues to function when integrations are unavailable
3. **Automatic Discovery**: Implement service discovery for seamless integration activation
4. **Health Monitoring**: Continuously monitor integration health and performance
5. **Error Handling**: Implement comprehensive error handling with retry mechanisms

### Performance Optimization

1. **Connection Pooling**: Use connection pooling for frequently accessed services
2. **Caching**: Implement intelligent caching for expensive operations
3. **Batch Operations**: Group related operations to reduce overhead
4. **Async Operations**: Use asynchronous operations where possible
5. **Rate Limiting**: Respect service rate limits and implement backoff strategies

### Security Considerations

1. **Authentication**: Use secure authentication methods (API keys, tokens)
2. **Authorization**: Implement proper authorization checks
3. **Data Encryption**: Encrypt sensitive data in transit and at rest
4. **Access Control**: Limit integration access to necessary resources only
5. **Audit Logging**: Log all integration activities for security auditing

### Configuration Management

1. **Environment Variables**: Use environment variables for configuration
2. **Configuration Validation**: Validate configuration at startup
3. **Hot Reloading**: Support configuration changes without restart
4. **Defaults**: Provide sensible defaults for all configuration options
5. **Documentation**: Document all configuration options clearly

## Troubleshooting

### Common Integration Issues

#### Memory Service Connection Issues

**Symptoms**:
- `ConnectionError: Failed to connect to mem0AI service`
- Memory operations timing out
- Context preparation failures

**Solutions**:
1. **Check service status**: `curl http://localhost:8002/health`
2. **Restart service**: `systemctl restart mem0ai`
3. **Verify configuration**: Check memory service configuration
4. **Check logs**: Review service logs for errors

#### MCP Service Detection Issues

**Symptoms**:
- MCP services not detected
- Tools not available in orchestrator
- Service availability timeouts

**Solutions**:
1. **Verify installation**: Check MCP service installation
2. **Check configuration**: Review Claude MCP settings
3. **Force refresh**: Restart orchestrator with service detection
4. **Review logs**: Check orchestrator logs for detection errors

#### GitHub API Issues

**Symptoms**:
- Authentication failures
- Rate limit exceeded
- Sync operation failures

**Solutions**:
1. **Check token**: Verify GitHub token validity and permissions
2. **Monitor rate limits**: Implement rate limit monitoring
3. **Review permissions**: Ensure token has required permissions
4. **Implement backoff**: Use exponential backoff for retries

### Debug Information

Enable verbose logging for troubleshooting:

```python
import logging

# Enable debug logging for all integrations
logging.getLogger("claude_pm.integrations").setLevel(logging.DEBUG)
logging.getLogger("claude_pm.services.memory").setLevel(logging.DEBUG)
logging.getLogger("claude_pm.services.github").setLevel(logging.DEBUG)

# Integration-specific debug
integration_manager = IntegrationManager()
await integration_manager.discover_services()

# Print discovered services
for service_name, service_info in integration_manager.discovered_services.items():
    print(f"Service: {service_name}")
    print(f"  Type: {service_info['type']}")
    print(f"  Status: {service_info['status']}")
    if 'tools' in service_info:
        print(f"  Tools: {service_info['tools']}")
```

### Support Resources

- **Health Monitoring**: Real-time integration health dashboard
- **Performance Metrics**: Integration performance monitoring
- **Error Tracking**: Comprehensive error logging and alerting
- **Configuration Validation**: Automated configuration validation
- **Documentation**: Comprehensive integration documentation

## Summary

This comprehensive integrations guide provides:

### Key Integration Categories
1. **MCP Services**: Productivity and context management tools
2. **Memory Integration**: Zero-configuration memory access and management
3. **GitHub API**: Issue synchronization and project management
4. **Service Discovery**: Automatic detection and connection management

### Integration Benefits
- **Enhanced Workflows**: Productivity tools and context management
- **Memory Augmentation**: Persistent knowledge and pattern recognition
- **External Connectivity**: Seamless integration with external services
- **Automated Management**: Zero-configuration setup and management

### Best Practices
- **Progressive Enhancement**: Core functionality preserved when integrations unavailable
- **Health Monitoring**: Continuous monitoring of integration health and performance
- **Security First**: Secure authentication and authorization for all integrations
- **Performance Optimization**: Efficient resource usage and intelligent caching

The Claude PM Framework integrations enhance development workflows while maintaining system reliability and security through comprehensive monitoring, graceful degradation, and robust error handling.

---

**Framework Version**: 4.5.1  
**Last Updated**: 2025-07-11  
**Integrations Guide Version**: 2.0.0  
**Authority Level**: Complete Integration Management