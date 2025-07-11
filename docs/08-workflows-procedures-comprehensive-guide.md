# Workflows & Procedures Comprehensive Guide - Claude PM Framework

## Overview

This comprehensive guide covers all operational workflows and procedures for the Claude PM Framework v4.5.1, including push operations, authentication setup, health monitoring procedures, troubleshooting workflows, and operational learning templates.

## Table of Contents

1. [Push Operations Workflow](#push-operations-workflow)
2. [Authentication Setup Procedures](#authentication-setup-procedures)
3. [Health Monitoring Procedures](#health-monitoring-procedures)
4. [Troubleshooting Workflows](#troubleshooting-workflows)
5. [Operational Learning Templates](#operational-learning-templates)
6. [Quick Reference Procedures](#quick-reference-procedures)
7. [Emergency Procedures](#emergency-procedures)
8. [Best Practices](#best-practices)

## Push Operations Workflow

### Overview

The comprehensive push operations workflow standardizes deployment across all projects with a single "push" command that triggers a complete deployment pipeline including version management, documentation updates, and git operations.

### Scope

**Primary Goal**: Standardize deployment across all projects with a single "push" command.

**Supported Projects**:
- `/Users/masa/Projects/managed/ai-trackdown-tools`
- `/Users/masa/Projects/claude-multiagent-pm`
- All managed projects in `/Users/masa/Projects/managed/`

### Complete Push Workflow

#### Phase 1: Pre-Push Validation

**Objectives**: Ensure project is ready for deployment

**Steps**:
1. **Check Project Status**
   ```bash
   git status
   git diff --stat
   ```

2. **Validate Build State**
   ```bash
   # For npm projects
   npm run build
   npm test
   
   # For Python projects
   python -m pytest
   pip install -r requirements.txt
   ```

3. **Dependency Verification**
   ```bash
   # Check for outdated packages
   npm outdated
   pip list --outdated
   ```

4. **Configuration Review**
   - Verify environment variables
   - Check configuration files
   - Validate deployment settings

#### Phase 2: Version Management

**Objectives**: Proper version control and tagging

**Steps**:
1. **Determine Version Bump**
   ```bash
   # Analyze changes for version impact
   git log --oneline $(git describe --tags --abbrev=0)..HEAD
   
   # Version bump rules:
   # - Major: Breaking changes
   # - Minor: New features
   # - Patch: Bug fixes
   ```

2. **Update Version Files**
   ```bash
   # For npm projects
   npm version patch|minor|major
   
   # For Python projects
   # Update __version__ in __init__.py
   # Update version in setup.py/pyproject.toml
   ```

3. **Generate Changelog**
   ```bash
   # Auto-generate changelog
   git-chglog > CHANGELOG.md
   
   # Or manual changelog update
   echo "## [$(date +%Y-%m-%d)] - Version X.Y.Z" >> CHANGELOG.md
   ```

#### Phase 3: Documentation Sync

**Objectives**: Ensure documentation is current and complete

**Steps**:
1. **Update README**
   ```bash
   # Update version badges
   sed -i "s/version-.*-blue/version-$NEW_VERSION-blue/g" README.md
   
   # Update installation instructions
   # Update usage examples
   ```

2. **API Documentation**
   ```bash
   # For Python projects
   sphinx-build -b html docs/ docs/_build/
   
   # For npm projects
   npm run docs
   ```

3. **Documentation Validation**
   ```bash
   # Check for broken links
   markdown-link-check README.md
   
   # Validate code examples
   python -m doctest README.md
   ```

#### Phase 4: Testing Pipeline

**Objectives**: Comprehensive testing before deployment

**Steps**:
1. **Unit Tests**
   ```bash
   # Python
   python -m pytest tests/ -v --cov=src/
   
   # Node.js
   npm test -- --coverage
   ```

2. **Integration Tests**
   ```bash
   # Run integration test suite
   python -m pytest tests/integration/ -v
   npm run test:integration
   ```

3. **End-to-End Tests**
   ```bash
   # Run E2E tests
   python -m pytest tests/e2e/ -v
   npm run test:e2e
   ```

4. **Security Scanning**
   ```bash
   # Python security scan
   bandit -r src/
   safety check
   
   # Node.js security audit
   npm audit
   ```

#### Phase 5: Git Operations

**Objectives**: Clean git history and proper tagging

**Steps**:
1. **Staging and Commit**
   ```bash
   # Stage all changes
   git add -A
   
   # Create release commit
   git commit -m "chore(release): version $NEW_VERSION
   
   - Updated version numbers
   - Generated changelog
   - Updated documentation"
   ```

2. **Create Release Tag**
   ```bash
   # Create annotated tag
   git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
   
   # Push tag
   git push origin "v$NEW_VERSION"
   ```

3. **Push to Repository**
   ```bash
   # Push to main branch
   git push origin main
   
   # Push all tags
   git push --tags
   ```

#### Phase 6: Deployment

**Objectives**: Deploy to target environments

**Steps**:
1. **Package Build**
   ```bash
   # Python packaging
   python -m build
   
   # Node.js packaging
   npm pack
   ```

2. **Registry Publishing**
   ```bash
   # Publish to PyPI
   python -m twine upload dist/*
   
   # Publish to npm
   npm publish
   ```

3. **Environment Deployment**
   ```bash
   # Deploy to staging
   ./scripts/deploy.sh staging
   
   # Deploy to production (if staging successful)
   ./scripts/deploy.sh production
   ```

### Push Operation Script

```bash
#!/bin/bash
# comprehensive_push.sh - Complete push operations workflow

set -e  # Exit on any error

PROJECT_DIR="$(pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
LOG_FILE="/tmp/push_${PROJECT_NAME}_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 Starting comprehensive push workflow for $PROJECT_NAME" | tee "$LOG_FILE"

# Phase 1: Pre-Push Validation
echo "📋 Phase 1: Pre-Push Validation" | tee -a "$LOG_FILE"

# Check git status
if [[ -n $(git status --porcelain) ]]; then
    echo "✅ Changes detected" | tee -a "$LOG_FILE"
else
    echo "❌ No changes to push" | tee -a "$LOG_FILE"
    exit 1
fi

# Run tests
if [[ -f "package.json" ]]; then
    echo "Running npm tests..." | tee -a "$LOG_FILE"
    npm test >> "$LOG_FILE" 2>&1
elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
    echo "Running Python tests..." | tee -a "$LOG_FILE"
    python -m pytest >> "$LOG_FILE" 2>&1
fi

# Phase 2: Version Management
echo "📊 Phase 2: Version Management" | tee -a "$LOG_FILE"

# Determine version bump
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Current version: $CURRENT_VERSION" | tee -a "$LOG_FILE"

# Ask for version bump type
read -p "Version bump (patch/minor/major): " BUMP_TYPE

if [[ -f "package.json" ]]; then
    NEW_VERSION=$(npm version "$BUMP_TYPE" --no-git-tag-version | cut -c2-)
elif [[ -f "pyproject.toml" ]]; then
    # Handle Python version bumping
    NEW_VERSION=$(python -c "
import toml
config = toml.load('pyproject.toml')
current = config['project']['version']
parts = current.split('.')
if '$BUMP_TYPE' == 'major':
    parts[0] = str(int(parts[0]) + 1)
    parts[1] = '0'
    parts[2] = '0'
elif '$BUMP_TYPE' == 'minor':
    parts[1] = str(int(parts[1]) + 1)
    parts[2] = '0'
else:
    parts[2] = str(int(parts[2]) + 1)
print('.'.join(parts))
")
fi

echo "New version: $NEW_VERSION" | tee -a "$LOG_FILE"

# Phase 3: Documentation Sync
echo "📚 Phase 3: Documentation Sync" | tee -a "$LOG_FILE"

# Update README badges
if [[ -f "README.md" ]]; then
    sed -i.bak "s/version-[^-]*-blue/version-$NEW_VERSION-blue/g" README.md
    rm README.md.bak
fi

# Phase 4: Testing Pipeline
echo "🧪 Phase 4: Testing Pipeline" | tee -a "$LOG_FILE"

# Security scanning
if command -v bandit >/dev/null 2>&1; then
    echo "Running security scan..." | tee -a "$LOG_FILE"
    bandit -r . -f json -o security_report.json >> "$LOG_FILE" 2>&1 || true
fi

# Phase 5: Git Operations
echo "📝 Phase 5: Git Operations" | tee -a "$LOG_FILE"

# Stage changes
git add -A

# Create release commit
git commit -m "chore(release): version $NEW_VERSION

- Updated version numbers
- Updated documentation
- Automated release preparation"

# Create tag
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"

# Push to repository
git push origin main
git push origin "v$NEW_VERSION"

echo "✅ Push workflow completed successfully!" | tee -a "$LOG_FILE"
echo "📋 Log file: $LOG_FILE"
```

### Quick Reference - Push Operations

```bash
# Complete push workflow
./scripts/comprehensive_push.sh

# Quick push (development)
git add -A && git commit -m "feat: quick development changes" && git push

# Emergency push (hotfix)
./scripts/emergency_push.sh --hotfix

# Rollback last push
git reset --hard HEAD~1 && git push --force-with-lease
```

## Authentication Setup Procedures

### Overview

Comprehensive authentication setup for the Claude PM Framework, covering service authentication, API keys, tokens, and secure communication protocols.

### Service Authentication Setup

#### 1. Memory Service Authentication

```bash
# Generate secure API key for memory service
MEMORY_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Configure environment variables
cat >> ~/.bashrc << EOF
export CLAUDE_PM_MEMORY_API_KEY="$MEMORY_API_KEY"
export CLAUDE_PM_MEMORY_HOST="localhost"
export CLAUDE_PM_MEMORY_PORT="8002"
EOF

# Reload environment
source ~/.bashrc
```

#### 2. GitHub API Authentication

```bash
# Create GitHub fine-grained token
echo "1. Go to https://github.com/settings/personal-access-tokens/new"
echo "2. Select repository access"
echo "3. Grant permissions: Issues (read/write), Metadata (read), Pull requests (read)"
echo "4. Copy token to clipboard"

read -p "Enter GitHub token: " GITHUB_TOKEN

# Store securely
echo "$GITHUB_TOKEN" > ~/.github_token
chmod 600 ~/.github_token

# Configure for framework
export GITHUB_TOKEN="$GITHUB_TOKEN"
```

#### 3. OpenAI API Authentication

```bash
# Configure OpenAI API key
read -p "Enter OpenAI API key: " OPENAI_API_KEY

# Store in environment
cat >> ~/.bashrc << EOF
export OPENAI_API_KEY="$OPENAI_API_KEY"
EOF

# Test authentication
python -c "
import openai
openai.api_key = '$OPENAI_API_KEY'
try:
    response = openai.models.list()
    print('✅ OpenAI authentication successful')
except Exception as e:
    print(f'❌ OpenAI authentication failed: {e}')
"
```

### Authentication Validation

```python
#!/usr/bin/env python3
"""Authentication validation script."""

import os
import asyncio
import aiohttp
from claude_pm.services.memory_service import get_memory_service

async def validate_all_authentication():
    """Validate all authentication configurations."""
    
    results = {}
    
    # 1. Memory service authentication
    try:
        memory_service = get_memory_service()
        health = await memory_service.health_check()
        results["memory_service"] = "✅ Authenticated" if health else "❌ Failed"
    except Exception as e:
        results["memory_service"] = f"❌ Error: {e}"
    
    # 2. GitHub API authentication
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {github_token}"}
                async with session.get("https://api.github.com/user", headers=headers) as response:
                    if response.status == 200:
                        results["github_api"] = "✅ Authenticated"
                    else:
                        results["github_api"] = f"❌ Failed: {response.status}"
        except Exception as e:
            results["github_api"] = f"❌ Error: {e}"
    else:
        results["github_api"] = "❌ Token not configured"
    
    # 3. OpenAI API authentication
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {openai_key}"}
                async with session.get("https://api.openai.com/v1/models", headers=headers) as response:
                    if response.status == 200:
                        results["openai_api"] = "✅ Authenticated"
                    else:
                        results["openai_api"] = f"❌ Failed: {response.status}"
        except Exception as e:
            results["openai_api"] = f"❌ Error: {e}"
    else:
        results["openai_api"] = "❌ Key not configured"
    
    # Print results
    print("🔐 Authentication Status:")
    for service, status in results.items():
        print(f"  {service}: {status}")
    
    return results

if __name__ == "__main__":
    asyncio.run(validate_all_authentication())
```

## Health Monitoring Procedures

### System Health Dashboard

The Claude PM Framework includes comprehensive health monitoring with real-time dashboards and automated alerting.

#### Health Check Procedures

```python
from claude_pm.services.health_dashboard import HealthDashboard

async def comprehensive_health_check():
    """Perform comprehensive system health check."""
    
    dashboard = HealthDashboard()
    
    # 1. Service health check
    service_health = await dashboard.check_service_health()
    print(f"Service Health: {service_health['overall_percentage']}%")
    
    for service_name, health_data in service_health['services'].items():
        status = "✅" if health_data['healthy'] else "❌"
        print(f"  {service_name}: {status} ({health_data['response_time']}ms)")
    
    # 2. Memory system health
    memory_health = await dashboard.check_memory_health()
    print(f"Memory Health: {memory_health['status']}")
    print(f"  Available backends: {memory_health['available_backends']}")
    print(f"  Active connections: {memory_health['active_connections']}")
    
    # 3. Agent system health
    agent_health = await dashboard.check_agent_health()
    print(f"Agent Health: {agent_health['availability_percentage']}%")
    print(f"  Available agents: {agent_health['available_agents']}")
    print(f"  Total agents: {agent_health['total_agents']}")
    
    # 4. Integration health
    integration_health = await dashboard.check_integration_health()
    print(f"Integration Health: {integration_health['health_percentage']}%")
    
    for integration, status in integration_health['integrations'].items():
        indicator = "✅" if status['healthy'] else "❌"
        print(f"  {integration}: {indicator}")
    
    return {
        "overall_health": dashboard.calculate_overall_health(),
        "service_health": service_health,
        "memory_health": memory_health,
        "agent_health": agent_health,
        "integration_health": integration_health
    }

# Run health check
import asyncio
health_report = asyncio.run(comprehensive_health_check())
```

#### Health Monitoring Script

```bash
#!/bin/bash
# health_monitor.sh - Continuous health monitoring

HEALTH_LOG="/var/log/claude-pm/health.log"
ALERT_THRESHOLD=70  # Alert if health drops below 70%

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get system health
    HEALTH_PERCENTAGE=$(python -c "
from claude_pm.services.health_dashboard import HealthDashboard
import asyncio
dashboard = HealthDashboard()
health = asyncio.run(dashboard.calculate_overall_health())
print(health)
")
    
    # Log health status
    echo "[$TIMESTAMP] System Health: $HEALTH_PERCENTAGE%" >> "$HEALTH_LOG"
    
    # Check for alerts
    if (( $(echo "$HEALTH_PERCENTAGE < $ALERT_THRESHOLD" | bc -l) )); then
        echo "⚠️  ALERT: System health below threshold ($HEALTH_PERCENTAGE%)" | \
            tee -a "$HEALTH_LOG"
        
        # Send notification (implement your notification method)
        # curl -X POST "your-webhook-url" -d "Health Alert: $HEALTH_PERCENTAGE%"
    fi
    
    # Wait 5 minutes
    sleep 300
done
```

### Sample Health Report

```json
{
  "timestamp": "2025-07-11T10:30:00Z",
  "overall_health": 87,
  "system_status": "healthy",
  "services": {
    "memory_service": {
      "status": "healthy",
      "response_time": 45,
      "uptime": "99.9%",
      "last_check": "2025-07-11T10:29:55Z"
    },
    "health_monitor": {
      "status": "healthy", 
      "response_time": 12,
      "uptime": "100%",
      "last_check": "2025-07-11T10:29:58Z"
    },
    "agent_orchestrator": {
      "status": "healthy",
      "response_time": 23,
      "active_agents": 8,
      "last_check": "2025-07-11T10:29:57Z"
    }
  },
  "integrations": {
    "github_api": {
      "status": "healthy",
      "rate_limit_remaining": 4500,
      "last_sync": "2025-07-11T09:45:00Z"
    },
    "memory_backends": {
      "mem0ai": "healthy",
      "sqlite": "standby",
      "tinydb": "standby"
    }
  },
  "alerts": [],
  "recommendations": [
    "Consider optimizing memory query performance",
    "GitHub API rate limit usage is normal"
  ]
}
```

## Troubleshooting Workflows

### Common Issue Resolution

#### 1. Memory Service Connection Issues

**Symptoms**: Memory operations failing, timeout errors
**Diagnostic Steps**:
```bash
# Check service status
curl http://localhost:8002/health

# Check process
ps aux | grep mem0

# Check logs
tail -f /var/log/mem0ai/service.log

# Test connectivity
python -c "
import aiohttp
import asyncio
async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8002/health') as response:
            print(f'Status: {response.status}')
            print(f'Response: {await response.text()}')
asyncio.run(test())
"
```

**Resolution Steps**:
```bash
# Restart memory service
sudo systemctl restart mem0ai

# Verify configuration
cat ~/.env | grep MEM0AI

# Test with minimal config
python -c "
from claude_pm.services.memory_service import MemoryService, MemoryConfig
config = MemoryConfig(host='localhost', port=8002, timeout=10)
service = MemoryService(config)
print('Service created successfully')
"
```

#### 2. Agent Communication Failures

**Symptoms**: Agent delegation timeouts, communication errors
**Diagnostic Steps**:
```bash
# Check agent availability
python -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
import asyncio
async def check():
    orchestrator = MultiAgentOrchestrator()
    agents = await orchestrator.get_available_agents()
    print(f'Available agents: {list(agents.keys())}')
asyncio.run(check())
"

# Test specific agent
python -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
import asyncio
async def test_agent():
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.test_delegation('research', {'task': 'test'})
    print(f'Test result: {result.success}')
asyncio.run(test_agent())
"
```

#### 3. GitHub Integration Issues

**Symptoms**: Sync failures, authentication errors
**Diagnostic Steps**:
```bash
# Test GitHub token
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user

# Check rate limits
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit

# Test repository access
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/repos/owner/repo
```

### Emergency Recovery Procedures

#### System Recovery Script

```bash
#!/bin/bash
# emergency_recovery.sh - Emergency system recovery

echo "🚨 Starting emergency recovery procedures..."

# 1. Stop all services
echo "Stopping services..."
sudo systemctl stop mem0ai || true
sudo systemctl stop claude-pm-health-monitor || true

# 2. Backup current state
echo "Creating backup..."
BACKUP_DIR="/tmp/claude-pm-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r ~/.claude-pm "$BACKUP_DIR/"
cp -r .claude-pm "$BACKUP_DIR/" 2>/dev/null || true

# 3. Reset to known good state
echo "Resetting to known good state..."
cd /Users/masa/Projects/claude-multiagent-pm
git checkout main
git pull origin main

# 4. Reinstall dependencies
echo "Reinstalling dependencies..."
pip install -r requirements/production.txt
npm install

# 5. Restart services
echo "Restarting services..."
sudo systemctl start mem0ai
sudo systemctl start claude-pm-health-monitor

# 6. Validate recovery
echo "Validating recovery..."
sleep 10

# Test memory service
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    echo "✅ Memory service recovered"
else
    echo "❌ Memory service recovery failed"
fi

# Test framework
if python -c "from claude_pm.core.config import Config; print('OK')"; then
    echo "✅ Framework imports working"
else
    echo "❌ Framework import failed"
fi

echo "🏥 Emergency recovery completed"
echo "📋 Backup location: $BACKUP_DIR"
```

## Operational Learning Templates

### Learning Template Structure

```yaml
# ops_learning_template.yaml
learning_entry:
  id: "OPS-YYYY-MM-DD-NNN"
  timestamp: "2025-07-11T10:30:00Z"
  category: "deployment" | "troubleshooting" | "optimization" | "security"
  severity: "info" | "warning" | "critical"
  
  situation:
    title: "Brief description of the situation"
    context: "Background and environmental factors"
    trigger: "What initiated this learning opportunity"
    
  problem:
    description: "Detailed problem description"
    symptoms: 
      - "Observable symptom 1"
      - "Observable symptom 2"
    impact:
      scope: "System-wide" | "Service-specific" | "User-facing"
      severity: "Low" | "Medium" | "High" | "Critical"
      
  investigation:
    steps_taken:
      - action: "Investigation step"
        outcome: "Result of the step"
        time_spent: "Duration in minutes"
    tools_used:
      - "Diagnostic tool 1"
      - "Diagnostic tool 2"
    findings:
      root_cause: "Identified root cause"
      contributing_factors:
        - "Factor 1"
        - "Factor 2"
        
  resolution:
    approach: "Description of resolution approach"
    steps:
      - action: "Resolution step"
        command: "Command executed (if applicable)"
        result: "Outcome"
    validation:
      - "Validation check 1"
      - "Validation check 2"
    time_to_resolve: "Total resolution time"
    
  lessons_learned:
    what_worked:
      - "Effective technique 1"
      - "Effective technique 2"
    what_didnt_work:
      - "Ineffective approach 1"
      - "Why it didn't work"
    prevention:
      - "How to prevent this issue"
      - "Warning signs to watch for"
    process_improvements:
      - "Process improvement 1"
      - "Process improvement 2"
      
  action_items:
    immediate:
      - task: "Immediate action required"
        owner: "Person responsible"
        deadline: "2025-07-15"
    long_term:
      - task: "Long-term improvement"
        owner: "Person responsible"
        deadline: "2025-08-01"
        
  related_documentation:
    - "Link to relevant documentation"
    - "Reference to similar incidents"
    
  tags:
    - "memory_service"
    - "authentication"
    - "performance"
```

### Example Learning Entry

```yaml
learning_entry:
  id: "OPS-2025-07-11-001"
  timestamp: "2025-07-11T14:30:00Z"
  category: "troubleshooting"
  severity: "warning"
  
  situation:
    title: "Memory service connection pool exhaustion"
    context: "High load testing with concurrent agent operations"
    trigger: "Multiple timeout errors during load test"
    
  problem:
    description: "Memory service becoming unresponsive under high concurrent load"
    symptoms:
      - "Connection timeout errors after 30 seconds"
      - "Memory service health check returning 503"
      - "Agent operations queuing up indefinitely"
    impact:
      scope: "System-wide"
      severity: "High"
      
  investigation:
    steps_taken:
      - action: "Checked memory service logs"
        outcome: "Found connection pool exhaustion messages"
        time_spent: "15"
      - action: "Monitored connection pool metrics"
        outcome: "Confirmed pool size limit reached"
        time_spent: "10"
      - action: "Analyzed concurrent request patterns"
        outcome: "Identified lack of connection reuse"
        time_spent: "20"
    tools_used:
      - "curl for health checks"
      - "Memory service admin panel"
      - "System monitoring dashboard"
    findings:
      root_cause: "Default connection pool size too small for concurrent operations"
      contributing_factors:
        - "No connection pooling in agent implementations"
        - "Synchronous operations blocking connections"
        
  resolution:
    approach: "Increase connection pool size and implement connection reuse"
    steps:
      - action: "Updated memory service configuration"
        command: "sed -i 's/pool_size=10/pool_size=50/' config.ini"
        result: "Pool size increased to 50 connections"
      - action: "Implemented connection reuse in agents"
        command: "Updated agent base class to use session pooling"
        result: "Reduced connection overhead by 80%"
      - action: "Restarted memory service"
        command: "sudo systemctl restart mem0ai"
        result: "Service restarted with new configuration"
    validation:
      - "Load test passed with 100 concurrent operations"
      - "Connection pool metrics showing healthy utilization"
      - "Response times under 100ms consistently"
    time_to_resolve: "90 minutes"
    
  lessons_learned:
    what_worked:
      - "Connection pool monitoring provided clear diagnosis"
      - "Incremental configuration changes allowed safe testing"
    what_didnt_work:
      - "Initial attempt to just restart service without config changes"
      - "Why: Didn't address root cause of pool exhaustion"
    prevention:
      - "Monitor connection pool utilization continuously"
      - "Set up alerts for pool utilization > 80%"
      - "Include connection pooling in agent design patterns"
    process_improvements:
      - "Add connection pool metrics to health dashboard"
      - "Document connection pool tuning guidelines"
      
  action_items:
    immediate:
      - task: "Add connection pool monitoring to dashboard"
        owner: "Ops Team"
        deadline: "2025-07-13"
      - task: "Update agent development guidelines"
        owner: "Architecture Team"
        deadline: "2025-07-15"
    long_term:
      - task: "Implement auto-scaling for connection pools"
        owner: "Platform Team"
        deadline: "2025-08-01"
        
  related_documentation:
    - "Memory Service Configuration Guide"
    - "Agent Development Best Practices"
    - "Load Testing Procedures"
    
  tags:
    - "memory_service"
    - "connection_pooling" 
    - "performance"
    - "load_testing"
```

## Quick Reference Procedures

### Daily Operations Checklist

```bash
#!/bin/bash
# daily_ops_checklist.sh

echo "📋 Claude PM Framework - Daily Operations Checklist"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# 1. System Health Check
echo "1. System Health Check"
HEALTH=$(python -c "
from claude_pm.services.health_dashboard import HealthDashboard
import asyncio
dashboard = HealthDashboard()
health = asyncio.run(dashboard.calculate_overall_health())
print(health)
")
echo "   Overall Health: $HEALTH%"
if (( $(echo "$HEALTH > 85" | bc -l) )); then
    echo "   ✅ Healthy"
else
    echo "   ⚠️  Needs attention"
fi
echo

# 2. Service Status Check
echo "2. Service Status Check"
services=("mem0ai" "claude-pm-health-monitor")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "   ✅ $service: Running"
    else
        echo "   ❌ $service: Stopped"
    fi
done
echo

# 3. Memory Service Check
echo "3. Memory Service Check"
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    echo "   ✅ Memory service: Healthy"
else
    echo "   ❌ Memory service: Unhealthy"
fi
echo

# 4. Disk Space Check
echo "4. Disk Space Check"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
echo "   Disk usage: $DISK_USAGE%"
if (( DISK_USAGE > 85 )); then
    echo "   ⚠️  High disk usage"
else
    echo "   ✅ Disk usage normal"
fi
echo

# 5. Log File Check
echo "5. Log File Check"
LOG_DIR="/var/log/claude-pm"
if [[ -d "$LOG_DIR" ]]; then
    LOG_COUNT=$(find "$LOG_DIR" -name "*.log" -mtime -1 | wc -l)
    echo "   Recent log files: $LOG_COUNT"
    
    # Check for errors
    ERROR_COUNT=$(grep -r "ERROR" "$LOG_DIR"/*.log 2>/dev/null | wc -l)
    if (( ERROR_COUNT > 10 )); then
        echo "   ⚠️  High error count: $ERROR_COUNT"
    else
        echo "   ✅ Error count normal: $ERROR_COUNT"
    fi
else
    echo "   ⚠️  Log directory not found"
fi
echo

echo "📊 Daily checklist completed"
```

### Emergency Response Quick Commands

```bash
# Emergency response commands

# 1. Quick system status
curl -s http://localhost:8002/health | jq '.'

# 2. Restart all services
sudo systemctl restart mem0ai claude-pm-health-monitor

# 3. Check system resources
df -h && free -h && top -bn1 | head -10

# 4. Tail critical logs
tail -f /var/log/claude-pm/*.log

# 5. Test framework imports
python -c "from claude_pm.core.config import Config; print('Framework OK')"

# 6. Network connectivity test
ping -c 3 8.8.8.8 && curl -I https://api.github.com

# 7. Quick backup
tar -czf "/tmp/claude-pm-backup-$(date +%Y%m%d_%H%M%S).tar.gz" \
    ~/.claude-pm .claude-pm 2>/dev/null

# 8. Memory service reset
sudo systemctl stop mem0ai && sleep 5 && sudo systemctl start mem0ai
```

## Best Practices

### Operational Excellence

1. **Proactive Monitoring**: Implement comprehensive monitoring before issues occur
2. **Documentation First**: Document procedures as you develop them
3. **Automated Recovery**: Automate common recovery procedures
4. **Regular Health Checks**: Perform daily health assessments
5. **Continuous Learning**: Capture and share operational learnings

### Workflow Optimization

1. **Standardized Procedures**: Use consistent procedures across all operations
2. **Version Control**: Track all operational scripts and configurations
3. **Testing**: Test all procedures in non-production environments first
4. **Rollback Plans**: Always have rollback procedures ready
5. **Communication**: Maintain clear communication during operations

### Security Practices

1. **Least Privilege**: Grant minimum required permissions
2. **Secure Storage**: Store credentials securely
3. **Regular Rotation**: Rotate API keys and tokens regularly
4. **Audit Logging**: Log all operational activities
5. **Access Control**: Implement proper access controls

## Summary

This comprehensive workflows and procedures guide provides:

### Core Workflows
- **Push Operations**: Complete deployment pipeline with version management
- **Authentication Setup**: Secure authentication for all services
- **Health Monitoring**: Comprehensive system health monitoring and alerting
- **Troubleshooting**: Systematic problem resolution workflows

### Operational Procedures
- **Emergency Recovery**: Rapid system recovery procedures
- **Daily Operations**: Routine maintenance and monitoring checklists
- **Learning Templates**: Structured approach to capturing operational knowledge
- **Quick Reference**: Fast access to common commands and procedures

### Best Practices
- **Operational Excellence**: Proactive monitoring and automated recovery
- **Security Standards**: Secure credential management and access control
- **Documentation**: Comprehensive procedure documentation and knowledge sharing
- **Continuous Improvement**: Regular review and optimization of procedures

The Claude PM Framework workflows and procedures ensure reliable, secure, and efficient operations through standardized processes, comprehensive monitoring, and systematic problem resolution.

---

**Framework Version**: 4.5.1  
**Last Updated**: 2025-07-11  
**Workflows Guide Version**: 2.0.0  
**Authority Level**: Complete Operational Management