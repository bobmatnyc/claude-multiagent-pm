# Claude PM Framework Operations Cookbook v4.2.0

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Services](#core-services)
4. [Deployment Operations](#deployment-operations)
5. [Health Monitoring](#health-monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Service Recovery](#service-recovery)
8. [Common Operations](#common-operations)
9. [Configuration Management](#configuration-management)
10. [Learning System](#learning-system)

## Overview

This ops cookbook provides comprehensive operational guidance for the Claude PM Framework v4.2.0 - a multi-agent project management system with mem0AI integration and ai-trackdown-tools for persistent ticket management.

### Key System Components

- **Claude PM Framework Core** (`/Users/masa/Projects/claude-multiagent-pm/claude_pm/`)
- **Memory Service** (localhost:8002 with mem0AI integration)
- **AI Trackdown Tools** (Persistent ticket management)
- **Multi-Agent Orchestrator** (11-agent ecosystem)
- **Health Monitoring** (Automated health checks)
- **Configuration Management** (YAML-based config system)

### Production Deployment

- **Source Location**: `/Users/masa/Projects/claude-multiagent-pm`
- **Deployment Target**: `/Users/masa/Clients/claude-multiagent-pm`
- **Version**: 4.2.0
- **Architecture**: Pure subprocess delegation with memory integration

## System Architecture

### Framework Structure

```
claude-multiagent-pm/
├── claude_pm/                    # Core framework implementation
│   ├── services/                 # Memory, health, project services
│   ├── integrations/             # mem0AI, security integrations
│   ├── core/                     # Base services, configuration
│   └── utils/                    # AI trackdown tools, utilities
├── tasks/                        # AI-trackdown managed tickets
│   ├── epics/                    # Strategic epics
│   ├── issues/                   # Implementation issues
│   └── tasks/                    # Development tasks
├── config/                       # Configuration files
├── scripts/                      # Deployment and health scripts
├── bin/                          # CLI wrappers
└── docs/                         # Documentation
```

### Service Dependencies

#### Critical Dependencies

1. **mem0AI Service** (localhost:8002)
   - Required for memory operations
   - Auto-discovery and connection pooling
   - Fallback: Memory operations disabled

2. **AI Trackdown Tools** (@bobmatnyc/ai-trackdown-tools)
   - Required for ticket management
   - CLI commands: `aitrackdown`, `atd`
   - Fallback: File-based logging

3. **Python Environment** (>=3.8)
   - Framework runtime
   - Service orchestration
   - Required packages in `requirements/`

4. **Node.js Environment** (>=16.0.0)
   - AI trackdown tools runtime
   - CLI wrappers
   - Health monitoring scripts

#### Optional Dependencies

1. **Git Worktrees** (Multi-agent isolation)
2. **GitHub API** (Issue synchronization)
3. **Documentation Sync** (Automated doc updates)

## Core Services

### 1. Memory Service (`memory_service.py`)

**Purpose**: Central memory management with mem0AI integration

**Key Operations**:
- Connection management to localhost:8002
- Memory categorization (Project, Pattern, Team, Error)
- Async/sync operations with connection pooling
- Cache management and invalidation

**Configuration**:
```python
# Memory service configuration
{
    "host": "localhost",
    "port": 8002,
    "timeout": 30,
    "max_retries": 3,
    "connection_pool_size": 10
}
```

**Health Check**:
```bash
# Check memory service health
curl http://localhost:8002/health

# Test memory integration
python3 -c "from claude_pm.services.memory_service import get_memory_service; print(get_memory_service().client.is_connected())"
```

**Common Issues**:
- Connection timeout: Check mem0AI service status
- Memory not found: Verify project context
- Connection pool exhaustion: Restart service

### 2. Health Monitor Service (`health_monitor.py`)

**Purpose**: Comprehensive system health monitoring

**Key Operations**:
- Framework component monitoring
- AI trackdown tools health checks
- Memory service connectivity
- Background monitoring processes

**Configuration**:
```json
{
  "health_check_interval": 300,
  "enable_background_monitoring": true,
  "alert_threshold": 60
}
```

**Health Check**:
```bash
# Run health check
./scripts/health-check.sh

# Python health check
python3 -c "from claude_pm.services.health_monitor import HealthMonitorService; print('Health service available')"
```

**Monitoring Commands**:
```bash
# Background monitoring
python3 scripts/automated_health_monitor.py monitor

# One-time health check
python3 scripts/automated_health_monitor.py once

# Health status
python3 scripts/automated_health_monitor.py status
```

### 3. Project Service (`project_service.py`)

**Purpose**: Project discovery and compliance monitoring

**Key Operations**:
- Project discovery in managed directories
- Framework compliance scoring
- Git repository information
- Project lifecycle management

**Configuration**:
```python
{
    "base_path": "/Users/masa/Projects",
    "managed_path": "/Users/masa/Projects/managed",
    "auto_discovery_interval": 3600,
    "compliance_check_interval": 1800
}
```

**Health Check**:
```bash
# Check project service
python3 -c "from claude_pm.services.project_service import ProjectService; print('Project service available')"

# List discovered projects
python3 -c "from claude_pm.services.project_service import ProjectService; ps = ProjectService(); print(list(ps.get_projects().keys()))"
```

### 4. Multi-Agent Orchestrator (`multi_agent_orchestrator.py`)

**Purpose**: Coordinating 11-agent ecosystem with memory integration

**Key Operations**:
- Agent task submission and execution
- Memory-augmented context preparation
- Git worktree isolation
- Parallel execution coordination

**Configuration**:
```python
{
    "max_parallel": 5,
    "base_repo_path": "/Users/masa/Projects/claude-multiagent-pm",
    "worktree_base_path": "/Users/masa/Projects/claude-multiagent-pm/.worktrees"
}
```

**Health Check**:
```bash
# Check orchestrator status
python3 -c "from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator; print('Orchestrator available')"

# List agent types
python3 -c "from claude_pm.services.multi_agent_orchestrator import AgentType; print([a.value for a in AgentType])"
```

## Deployment Operations

### Initial Deployment

#### Prerequisites Check
```bash
# Check Node.js version
node --version  # Should be >= 16.0.0

# Check Python version
python3 --version  # Should be >= 3.8

# Check AI trackdown tools
npm list -g @bobmatnyc/ai-trackdown-tools
```

#### Installation Process
```bash
# Step 1: Install AI trackdown tools
npm install -g @bobmatnyc/ai-trackdown-tools

# Step 2: Verify installation
aitrackdown --version
atd --version

# Step 3: Deploy framework
cd /Users/masa/Projects/claude-multiagent-pm
npm run deploy

# Step 4: Validate deployment
npm run validate-deployment
```

### Redeployment Process

#### Full Redeployment
```bash
# Step 1: Backup current configuration
cp -r /Users/masa/Clients/claude-multiagent-pm/.claude-pm /tmp/claude-pm-backup

# Step 2: Clean deployment target
rm -rf /Users/masa/Clients/claude-multiagent-pm

# Step 3: Deploy from source
cd /Users/masa/Projects/claude-multiagent-pm
npm run deploy

# Step 4: Restore configuration if needed
cp -r /tmp/claude-pm-backup/.claude-pm /Users/masa/Clients/claude-multiagent-pm/

# Step 5: Validate deployment
cd /Users/masa/Clients/claude-multiagent-pm
./scripts/health-check.sh
```

#### Incremental Update
```bash
# Update specific components
cd /Users/masa/Projects/claude-multiagent-pm

# Update framework core
rsync -av claude_pm/ /Users/masa/Clients/claude-multiagent-pm/claude_pm/

# Update configuration
rsync -av config/ /Users/masa/Clients/claude-multiagent-pm/config/

# Update scripts
rsync -av scripts/ /Users/masa/Clients/claude-multiagent-pm/scripts/

# Validate update
cd /Users/masa/Clients/claude-multiagent-pm
./scripts/health-check.sh
```

## Health Monitoring

### Automated Health Checks

#### Health Check Components
1. **Framework Core**: Python modules accessibility
2. **AI Trackdown Tools**: CLI functionality
3. **Memory Service**: Connection and response
4. **Task System**: Ticket hierarchy integrity
5. **Configuration**: Required files presence

#### Health Check Script
```bash
#!/bin/bash
# Comprehensive health check

echo "🔍 Claude PM Framework Health Check"
echo "===================================="

# Check framework core
if python3 -c "import claude_pm.cli; print('✓ Framework core accessible')" 2>/dev/null; then
    echo "✓ Framework core accessible"
else
    echo "❌ Framework core issue"
    exit 1
fi

# Check AI trackdown tools
if aitrackdown --version >/dev/null 2>&1; then
    echo "✓ AI trackdown tools available"
else
    echo "❌ AI trackdown tools issue"
    exit 1
fi

# Check memory service
if curl -s http://localhost:8002/health >/dev/null 2>&1; then
    echo "✓ Memory service responsive"
else
    echo "⚠ Memory service issue"
fi

# Check task system
if [ -d "tasks" ]; then
    TOTAL_TASKS=$(find tasks -name "*.md" | wc -l)
    echo "✓ Task system operational ($TOTAL_TASKS tasks)"
else
    echo "❌ Task system missing"
    exit 1
fi

echo "✅ Health check completed"
```

#### Automated Monitoring
```bash
# Setup background monitoring
python3 scripts/automated_health_monitor.py monitor --interval=300

# View health reports
cat logs/health-report.json

# Check health dashboard
python3 -c "from claude_pm.services.health_dashboard import HealthDashboard; hd = HealthDashboard(); print(hd.get_dashboard_summary())"
```

### Health Report Structure

```json
{
  "timestamp": "2025-07-09T12:00:00Z",
  "overall_health": 95,
  "components": {
    "framework_core": {
      "status": "healthy",
      "response_time": 150,
      "last_check": "2025-07-09T12:00:00Z"
    },
    "memory_service": {
      "status": "healthy",
      "connection": true,
      "response_time": 50
    },
    "ai_trackdown_tools": {
      "status": "healthy",
      "cli_functional": true,
      "task_count": 42
    },
    "task_system": {
      "status": "healthy",
      "epics": 29,
      "issues": 39,
      "tasks": 13
    }
  },
  "alerts": [],
  "recommendations": []
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Memory Service Connection Issues

**Symptoms**:
- `ConnectionError: Failed to connect to mem0AI service`
- Memory operations timing out
- Context preparation failures

**Diagnosis**:
```bash
# Check memory service status
curl http://localhost:8002/health

# Check service logs
tail -f logs/memory_service.log

# Test connection
python3 -c "from claude_pm.services.memory_service import ClaudePMMemory; m = ClaudePMMemory(); print(m.is_connected())"
```

**Solutions**:
1. **Restart mem0AI service**: `systemctl restart mem0ai`
2. **Check port availability**: `netstat -ln | grep 8002`
3. **Verify configuration**: Check `config/memory_config.json`
4. **Clear connection pool**: Restart Python processes

#### 2. AI Trackdown Tools Issues

**Symptoms**:
- Command not found: `aitrackdown`
- CLI timeout errors
- Ticket creation failures

**Diagnosis**:
```bash
# Check installation
npm list -g @bobmatnyc/ai-trackdown-tools

# Test CLI functionality
aitrackdown --version
atd status

# Check task structure
ls -la tasks/
```

**Solutions**:
1. **Reinstall tools**: `npm install -g @bobmatnyc/ai-trackdown-tools`
2. **Fix PATH**: Add Node.js global modules to PATH
3. **Check permissions**: Ensure execute permissions on CLI
4. **Verify task structure**: Recreate `tasks/` directory structure

#### 3. Multi-Agent Orchestrator Issues

**Symptoms**:
- Agent execution failures
- Worktree creation errors
- Memory context preparation failures

**Diagnosis**:
```bash
# Check orchestrator status
python3 -c "from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator; print('Orchestrator available')"

# Check git worktree status
git worktree list

# Check memory integration
python3 -c "from claude_pm.services.mem0_context_manager import Mem0ContextManager; print('Context manager available')"
```

**Solutions**:
1. **Clean worktrees**: `git worktree prune`
2. **Check git repository**: Ensure `.git` directory exists
3. **Verify memory service**: Test memory connection
4. **Restart orchestrator**: Kill Python processes and restart

#### 4. Configuration Issues

**Symptoms**:
- Import errors
- Service initialization failures
- Path resolution issues

**Diagnosis**:
```bash
# Check configuration files
find . -name "*.json" -o -name "*.yaml" | head -10

# Verify Python path
python3 -c "import sys; print(sys.path)"

# Check environment variables
env | grep CLAUDE
```

**Solutions**:
1. **Fix Python path**: Add framework to PYTHONPATH
2. **Verify configuration**: Check JSON/YAML syntax
3. **Update paths**: Ensure absolute paths are correct
4. **Environment setup**: Source activation script

## Service Recovery

### Emergency Recovery Procedures

#### 1. Memory Service Recovery

**When to Use**: Memory service unresponsive or corrupted

**Recovery Steps**:
```bash
# Step 1: Stop memory service
sudo systemctl stop mem0ai

# Step 2: Clear memory cache
rm -rf /tmp/memory_cache/*

# Step 3: Restart service
sudo systemctl start mem0ai

# Step 4: Verify connection
curl http://localhost:8002/health

# Step 5: Test memory operations
python3 -c "from claude_pm.services.memory_service import get_memory_service; print(get_memory_service().client.is_connected())"
```

#### 2. AI Trackdown Tools Recovery

**When to Use**: CLI commands failing or data corruption

**Recovery Steps**:
```bash
# Step 1: Backup task data
cp -r tasks/ tasks-backup-$(date +%Y%m%d_%H%M%S)/

# Step 2: Reinstall tools
npm uninstall -g @bobmatnyc/ai-trackdown-tools
npm install -g @bobmatnyc/ai-trackdown-tools

# Step 3: Verify installation
aitrackdown --version
atd --version

# Step 4: Test CLI functionality
aitrackdown status
aitrackdown epic list

# Step 5: Validate task structure
find tasks/ -name "*.md" | wc -l
```

#### 3. Framework Core Recovery

**When to Use**: Framework services failing to start

**Recovery Steps**:
```bash
# Step 1: Stop all services
pkill -f claude_pm

# Step 2: Check framework integrity
python3 -c "import claude_pm; print('Framework import successful')"

# Step 3: Reinstall dependencies
pip install -r requirements/production.txt

# Step 4: Restart services
python3 -m claude_pm.cli health --start-services

# Step 5: Validate health
./scripts/health-check.sh
```

#### 4. Complete System Recovery

**When to Use**: Multiple system failures or corruption

**Recovery Steps**:
```bash
# Step 1: Create backup
tar -czf claude-pm-backup-$(date +%Y%m%d_%H%M%S).tar.gz /Users/masa/Clients/claude-multiagent-pm

# Step 2: Clean installation
rm -rf /Users/masa/Clients/claude-multiagent-pm

# Step 3: Redeploy framework
cd /Users/masa/Projects/claude-multiagent-pm
npm run deploy

# Step 4: Restore configuration
# (Restore from backup if needed)

# Step 5: Validate system
cd /Users/masa/Clients/claude-multiagent-pm
./scripts/health-check.sh
```

## Common Operations

### Daily Operations

#### 1. System Health Check
```bash
# Quick health check
./scripts/health-check.sh

# Detailed health report
python3 scripts/automated_health_monitor.py once --verbose

# Check service status
python3 -c "from claude_pm.services.health_monitor import HealthMonitorService; hms = HealthMonitorService(); print(hms.get_health_status())"
```

#### 2. Memory Service Maintenance
```bash
# Check memory statistics
python3 -c "from claude_pm.services.memory_service import get_memory_service; ms = get_memory_service(); print(ms.get_memory_stats('claude-pm'))"

# Clear memory cache
python3 -c "from claude_pm.services.memory_service import get_memory_service; ms = get_memory_service(); ms.client._invalidate_cache('claude-pm')"

# Test memory operations
python3 -c "from claude_pm.services.memory_service import get_memory_service; ms = get_memory_service(); print(ms.client.add_project_decision('test-project', 'Test decision', 'Test context'))"
```

#### 3. AI Trackdown Operations
```bash
# Check system status
aitrackdown status

# List active tickets
aitrackdown epic list --status active
aitrackdown issue list --status active
aitrackdown task list --status active

# Create new tickets
aitrackdown epic create "New Epic"
aitrackdown issue create "New Issue" --epic EP-001
aitrackdown task create "New Task" --issue ISS-001

# Update ticket status
aitrackdown issue update ISS-001 --status in-progress
aitrackdown task complete TSK-001
```

#### 4. Project Management
```bash
# Discover projects
python3 -c "from claude_pm.services.project_service import ProjectService; ps = ProjectService(); ps._discover_projects()"

# Check project compliance
python3 -c "from claude_pm.services.project_service import ProjectService; ps = ProjectService(); print(ps.get_project_stats())"

# Update project information
python3 -c "from claude_pm.services.project_service import ProjectService; ps = ProjectService(); ps.refresh_project('project-name')"
```

### Weekly Operations

#### 1. System Maintenance
```bash
# Update dependencies
pip install -r requirements/production.txt --upgrade
npm update -g @bobmatnyc/ai-trackdown-tools

# Clean up logs
find logs/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.json" -mtime +7 -delete

# Cleanup worktrees
cd /Users/masa/Projects/claude-multiagent-pm
git worktree prune
```

#### 2. Health Report Review
```bash
# Generate weekly health report
python3 scripts/automated_health_monitor.py reports --period weekly

# Review system metrics
python3 -c "from claude_pm.services.health_monitor import HealthMonitorService; hms = HealthMonitorService(); print(hms.get_last_health_report())"

# Check component trends
grep "overall_health" logs/health-*.json | tail -10
```

#### 3. Data Backup
```bash
# Backup task data
tar -czf backups/tasks-$(date +%Y%m%d).tar.gz tasks/

# Backup configuration
tar -czf backups/config-$(date +%Y%m%d).tar.gz config/

# Backup logs
tar -czf backups/logs-$(date +%Y%m%d).tar.gz logs/
```

### Monthly Operations

#### 1. System Updates
```bash
# Update framework version
cd /Users/masa/Projects/claude-multiagent-pm
git pull origin main
npm run deploy

# Update system dependencies
pip install -r requirements/production.txt --upgrade
npm update -g @bobmatnyc/ai-trackdown-tools

# Validate system after updates
./scripts/health-check.sh
```

#### 2. Performance Review
```bash
# Review memory usage
python3 -c "from claude_pm.services.memory_service import get_memory_service; ms = get_memory_service(); print(ms.stats)"

# Check orchestrator performance
python3 -c "from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator; print('Orchestrator stats available')"

# Review health trends
python3 scripts/automated_health_monitor.py reports --period monthly
```

## Configuration Management

### Configuration Files

#### 1. Health Monitoring Configuration
**Location**: `config/health_monitoring_config.json`

```json
{
  "documentation_monitoring": {
    "enabled": true,
    "check_interval": 900,
    "alert_thresholds": {
      "critical_issues": 1,
      "broken_links": 5,
      "inconsistencies": 3
    }
  },
  "ai_trackdown_monitoring": {
    "enabled": true,
    "check_interval": 300,
    "cli_timeout": 10,
    "commands_to_test": [
      "status",
      "epic list",
      "issue list",
      "task list"
    ]
  }
}
```

#### 2. Memory Service Configuration
**Location**: `claude_pm/core/memory_config.py`

```python
MEMORY_CONFIG = {
    "host": "localhost",
    "port": 8002,
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0,
    "connection_pool_size": 10,
    "cache_ttl": 300,
    "max_memory_size": 1000
}
```

#### 3. AI Trackdown Configuration
**Location**: `claude_pm/utils/ai_trackdown_tools.py`

```python
AI_TRACKDOWN_CONFIG = {
    "enabled": True,
    "timeout": 30,
    "fallback_logging": True,
    "fallback_method": "logging",
    "cli_command": "aitrackdown",
    "cli_alias": "atd"
}
```

### Environment Variables

#### Required Variables
```bash
# Python environment
export PYTHONPATH="/Users/masa/Projects/claude-multiagent-pm:$PYTHONPATH"

# Memory service
export CLAUDE_PM_MEMORY_HOST="localhost"
export CLAUDE_PM_MEMORY_PORT="8002"

# AI Trackdown
export CLAUDE_PM_AI_TRACKDOWN_ENABLED="true"
export CLAUDE_PM_AI_TRACKDOWN_TIMEOUT="30"
```

#### Optional Variables
```bash
# Debug mode
export CLAUDE_PM_DEBUG="true"

# Logging level
export CLAUDE_PM_LOG_LEVEL="INFO"

# Performance monitoring
export CLAUDE_PM_PERFORMANCE_MONITORING="true"
```

### Configuration Validation

#### Validation Script
```bash
#!/bin/bash
# Configuration validation

echo "Validating Claude PM Framework Configuration"
echo "=========================================="

# Check required files
CONFIG_FILES=(
    "config/health_monitoring_config.json"
    "config/performance_config.json"
    "config/doc_sync_config.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
        # Validate JSON syntax
        if python3 -m json.tool "$file" >/dev/null 2>&1; then
            echo "✓ $file valid JSON"
        else
            echo "❌ $file invalid JSON"
        fi
    else
        echo "❌ $file missing"
    fi
done

# Check Python configuration
if python3 -c "from claude_pm.core.config import Config; print('✓ Configuration accessible')" 2>/dev/null; then
    echo "✓ Python configuration accessible"
else
    echo "❌ Python configuration issue"
fi

# Check environment variables
if [ -n "$PYTHONPATH" ]; then
    echo "✓ PYTHONPATH set"
else
    echo "⚠ PYTHONPATH not set"
fi

echo "Configuration validation completed"
```

## Learning System

### Operational Knowledge Capture

#### 1. Issue Resolution Patterns
When resolving operational issues, capture the following information:

**Template**: `docs/OPS_LEARNING_TEMPLATE.md`

```markdown
# Operational Learning Entry

## Issue Summary
- **Date**: 2025-07-09
- **Issue**: Memory service connection timeout
- **Severity**: HIGH
- **Duration**: 30 minutes

## Context
- **System State**: Memory service unresponsive
- **Symptoms**: Connection timeouts, memory operations failing
- **Environment**: Production deployment

## Root Cause
- **Primary**: Memory service process crashed
- **Secondary**: High memory usage caused OOM
- **Contributing**: No memory monitoring alerts

## Resolution Steps
1. Checked memory service status: `systemctl status mem0ai`
2. Reviewed service logs: `journalctl -u mem0ai`
3. Identified OOM issue in logs
4. Restarted service: `systemctl restart mem0ai`
5. Implemented memory monitoring

## Prevention
- Add memory usage alerts
- Implement automatic restart on failure
- Monitor memory consumption trends

## Learning Points
- Memory service needs monitoring
- OOM issues require proactive monitoring
- Service restart procedures work effectively

## Knowledge Updates
- Updated health monitoring configuration
- Added memory usage alerts
- Documented recovery procedure
```

#### 2. Performance Optimization Patterns
Document system performance improvements:

```markdown
# Performance Optimization Learning

## Optimization Summary
- **Area**: Memory service connection pooling
- **Improvement**: 50% reduction in connection time
- **Impact**: Improved system responsiveness

## Before State
- Single connection per operation
- Average response time: 200ms
- Connection overhead: 50ms per operation

## Changes Made
1. Implemented connection pooling
2. Connection pool size: 10 connections
3. Connection reuse enabled
4. Timeout configuration optimized

## After State
- Connection reuse: 90%
- Average response time: 100ms
- Connection overhead: 5ms per operation

## Implementation
```python
# Connection pooling configuration
self._connection_pool = aiohttp.TCPConnector(
    limit=10,
    limit_per_host=5,
    ttl_dns_cache=300,
    enable_cleanup_closed=True
)
```

## Monitoring
- Monitor connection pool utilization
- Track response time trends
- Alert on connection failures
```

#### 3. Configuration Change Patterns
Track configuration changes and their impact:

```markdown
# Configuration Change Learning

## Change Summary
- **Component**: Health monitoring
- **Change**: Reduced check interval from 900s to 300s
- **Reason**: Faster issue detection

## Impact Assessment
- **Positive**: 3x faster issue detection
- **Negative**: 3x increase in CPU usage
- **Overall**: Net positive for system reliability

## Rollback Plan
- Revert to 900s interval if CPU usage becomes problematic
- Alternative: Implement adaptive monitoring

## Monitoring
- Track CPU usage trends
- Monitor alert frequency
- Measure time to detection
```

### Knowledge Management System

#### 1. Searchable Knowledge Base
Create a searchable repository of operational knowledge:

**Structure**:
```
docs/ops-knowledge/
├── issues/
│   ├── memory-service/
│   ├── ai-trackdown/
│   └── framework-core/
├── performance/
│   ├── optimizations/
│   └── benchmarks/
├── configurations/
│   ├── changes/
│   └── validations/
└── procedures/
    ├── deployments/
    └── recovery/
```

#### 2. Pattern Recognition System
Identify recurring operational patterns:

```python
# Pattern recognition for operational issues
class OperationalPatternRecognizer:
    def __init__(self):
        self.patterns = {
            'memory_service_issues': {
                'symptoms': ['connection timeout', 'memory operations failing'],
                'common_causes': ['service crash', 'OOM', 'network issues'],
                'solutions': ['restart service', 'check memory', 'verify network']
            },
            'ai_trackdown_issues': {
                'symptoms': ['CLI timeout', 'command not found'],
                'common_causes': ['package not installed', 'PATH issues'],
                'solutions': ['reinstall package', 'fix PATH', 'check permissions']
            }
        }
    
    def identify_pattern(self, symptoms):
        # Pattern matching logic
        pass
    
    def suggest_solution(self, pattern):
        # Solution recommendation
        pass
```

#### 3. Automated Learning Integration
Integrate learning into operational workflows:

```bash
# Automated learning capture
function capture_learning() {
    local issue="$1"
    local solution="$2"
    local impact="$3"
    
    # Create learning entry
    cat > "docs/ops-knowledge/issues/$(date +%Y%m%d_%H%M%S)_${issue}.md" << EOF
# Issue: ${issue}
Date: $(date)
Solution: ${solution}
Impact: ${impact}
EOF
    
    # Update knowledge base
    echo "Learning captured: ${issue}"
}

# Usage during issue resolution
capture_learning "memory-service-timeout" "restart-service" "system-restored"
```

### Continuous Improvement Framework

#### 1. Weekly Learning Review
Regular review of operational learnings:

```bash
# Weekly learning review script
#!/bin/bash

echo "Weekly Operational Learning Review"
echo "================================="

# Review recent issues
echo "Recent Issues (Last 7 days):"
find docs/ops-knowledge/issues -name "*.md" -mtime -7 -exec echo "- {}" \;

# Identify patterns
echo "Recurring Patterns:"
grep -r "Pattern:" docs/ops-knowledge/issues/ | sort | uniq -c | sort -nr

# Suggest improvements
echo "Improvement Opportunities:"
grep -r "Prevention:" docs/ops-knowledge/issues/ | cut -d: -f3 | sort | uniq

echo "Review completed"
```

#### 2. Knowledge Base Updates
Regular updates to operational procedures:

```bash
# Knowledge base update script
#!/bin/bash

echo "Updating Operational Knowledge Base"
echo "=================================="

# Update issue resolution procedures
python3 scripts/update_knowledge_base.py --category issues

# Update performance optimization patterns
python3 scripts/update_knowledge_base.py --category performance

# Update configuration change patterns
python3 scripts/update_knowledge_base.py --category configurations

echo "Knowledge base updated"
```

#### 3. Automated Recommendations
System that provides automated recommendations:

```python
# Automated recommendation system
class OperationalRecommendationEngine:
    def __init__(self):
        self.knowledge_base = self.load_knowledge_base()
        self.pattern_recognizer = OperationalPatternRecognizer()
    
    def analyze_system_state(self):
        # Analyze current system state
        health_status = self.get_health_status()
        performance_metrics = self.get_performance_metrics()
        configuration_state = self.get_configuration_state()
        
        return {
            'health': health_status,
            'performance': performance_metrics,
            'configuration': configuration_state
        }
    
    def generate_recommendations(self, system_state):
        recommendations = []
        
        # Health-based recommendations
        if system_state['health']['overall'] < 90:
            recommendations.append({
                'type': 'health',
                'priority': 'high',
                'action': 'investigate_health_issues',
                'details': system_state['health']
            })
        
        # Performance-based recommendations
        if system_state['performance']['response_time'] > 500:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'action': 'optimize_performance',
                'details': system_state['performance']
            })
        
        return recommendations
```

### Future Custom User Agent Integration

#### 1. Agent Learning Interface
Prepare for future custom user agents:

```python
# Agent learning interface
class AgentLearningInterface:
    def __init__(self):
        self.ops_knowledge = self.load_ops_knowledge()
        self.pattern_library = self.load_patterns()
    
    def get_operational_context(self, task_type):
        # Provide operational context for agent tasks
        return {
            'relevant_patterns': self.find_relevant_patterns(task_type),
            'historical_solutions': self.get_historical_solutions(task_type),
            'best_practices': self.get_best_practices(task_type)
        }
    
    def update_learning(self, task_result):
        # Update learning based on task results
        self.capture_task_outcome(task_result)
        self.update_patterns(task_result)
        self.refine_recommendations(task_result)
```

#### 2. Context Preparation
Prepare rich context for future agents:

```python
# Context preparation for future agents
class OperationalContextManager:
    def prepare_context(self, agent_type, task_description):
        context = {
            'operational_history': self.get_operational_history(task_description),
            'system_state': self.get_current_system_state(),
            'relevant_procedures': self.get_relevant_procedures(task_description),
            'known_issues': self.get_known_issues(task_description),
            'performance_baselines': self.get_performance_baselines(),
            'configuration_state': self.get_configuration_state()
        }
        
        return context
```

---

## Summary

This ops cookbook provides comprehensive operational guidance for the Claude PM Framework v4.2.0. It covers:

- **System Architecture**: Complete understanding of framework components
- **Service Management**: Detailed operations for all core services
- **Health Monitoring**: Comprehensive health checking and alerting
- **Troubleshooting**: Common issues and systematic resolution procedures
- **Recovery Procedures**: Emergency recovery for all system components
- **Configuration Management**: Complete configuration documentation
- **Learning System**: Continuous improvement through knowledge capture

The cookbook is designed to support both immediate operational needs and future custom user agent integration, providing a solid foundation for autonomous system management.

**Key Success Factors**:
1. Regular health monitoring and proactive issue detection
2. Systematic troubleshooting using documented procedures
3. Continuous learning and knowledge capture
4. Automated recovery procedures for common issues
5. Comprehensive configuration management
6. Performance optimization through pattern recognition

This operational framework ensures the Claude PM Framework remains reliable, performant, and continuously improving through systematic operational intelligence.