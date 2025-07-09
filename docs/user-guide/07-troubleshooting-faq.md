# Troubleshooting & FAQ

## Overview

This comprehensive troubleshooting guide provides solutions for common issues encountered when using the Claude Multi-Agent PM Framework (CMPM). It covers installation problems, configuration issues, agent-related errors, performance optimization, and frequently asked questions.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Agent-Related Problems](#agent-related-problems)
3. [Configuration Issues](#configuration-issues)
4. [Performance and Scalability](#performance-and-scalability)
5. [Integration Problems](#integration-problems)
6. [Health Monitoring Issues](#health-monitoring-issues)
7. [Diagnostic Tools](#diagnostic-tools)
8. [Frequently Asked Questions](#frequently-asked-questions)
9. [Support and Escalation](#support-and-escalation)

---

## Installation Issues

### Common Installation Problems

#### 1. Node.js Version Incompatibility

**Problem**: `node: command not found` or version requirements not met

**Symptoms**:
```bash
$ claude-pm --version
bash: claude-pm: command not found
```

**Solution**:
```bash
# Install Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install and use Node.js 18+ (LTS)
nvm install 18
nvm use 18
nvm alias default 18

# Verify installation
node --version  # Should output v18.x.x or higher
```

**Alternative Solutions**:
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS with Homebrew
brew install node

# Windows with Chocolatey
choco install nodejs
```

#### 2. Python Version Issues

**Problem**: `python3: command not found` or version incompatibility

**Symptoms**:
```bash
$ python3 --version
bash: python3: command not found
```

**Solution**:
```bash
# Install Python 3.9+ using pyenv
curl https://pyenv.run | bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.0
pyenv global 3.11.0

# Verify installation
python3 --version  # Should output Python 3.9.0 or higher
```

#### 3. Permission Errors

**Problem**: `EACCES: permission denied` when installing globally

**Symptoms**:
```bash
$ npm install -g claude-multiagent-pm
npm ERR! code EACCES
npm ERR! syscall mkdir
npm ERR! path /usr/local/lib/node_modules/claude-multiagent-pm
npm ERR! errno -13
npm ERR! Error: EACCES: permission denied
```

**Solution**:
```bash
# Method 1: Fix npm permissions
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}

# Method 2: Use npx instead of global install
npx claude-multiagent-pm --version

# Method 3: Configure npm to use different directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

#### 4. ai-trackdown-tools Installation Failure

**Problem**: `@bobmatnyc/ai-trackdown-tools` package not found

**Symptoms**:
```bash
$ npm install -g @bobmatnyc/ai-trackdown-tools
npm ERR! 404 Not Found - GET https://registry.npmjs.org/@bobmatnyc/ai-trackdown-tools
```

**Solution**:
```bash
# Check npm registry configuration
npm config get registry

# Install from specific registry
npm install -g @bobmatnyc/ai-trackdown-tools --registry https://registry.npmjs.org/

# Use development version if package not published
git clone https://github.com/bobmatnyc/ai-trackdown-tools.git
cd ai-trackdown-tools
npm install
npm link
```

#### 5. Python Virtual Environment Issues

**Problem**: Virtual environment not activating or packages not installing

**Symptoms**:
```bash
$ source venv/bin/activate
bash: venv/bin/activate: No such file or directory
```

**Solution**:
```bash
# Create virtual environment
python3 -m venv claude-pm-env

# Activate virtual environment
# On Unix/Linux/macOS:
source claude-pm-env/bin/activate

# On Windows:
claude-pm-env\Scripts\activate

# Verify activation
which python3  # Should point to virtual environment

# Install requirements
pip install -r requirements/base.txt
```

#### 6. Memory Service Installation Issues

**Problem**: Memory service dependencies not installing correctly

**Symptoms**:
```bash
$ python3 -c "from claude_pm.services.memory_service import MemoryService"
ModuleNotFoundError: No module named 'claude_pm.services'
```

**Solution**:
```bash
# Install with AI features
pip install claude-multiagent-pm[ai]

# Or install with all features
pip install claude-multiagent-pm[all]

# Development installation
git clone https://github.com/bobmatnyc/claude-multiagent-pm.git
cd claude-multiagent-pm
pip install -e .
```

---

## Agent-Related Problems

### Agent Startup Failures

#### 1. Agent Process Won't Start

**Problem**: Agents fail to initialize or start properly

**Symptoms**:
```bash
$ claude-pm agent start --type engineer
Error: Agent startup failed - connection timeout
```

**Diagnostic Commands**:
```bash
# Check agent system status
python3 -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
try:
    orchestrator = MultiAgentOrchestrator()
    print('✓ Agent system available')
    print(f'Available agents: {orchestrator.get_available_agents()}')
except Exception as e:
    print(f'✗ Agent system error: {e}')
"

# Check service dependencies
curl -s http://localhost:8002/health || echo "Memory service not running"
```

**Solution**:
```bash
# Start memory service first
python3 -c "
from claude_pm.services.memory_service import MemoryService
service = MemoryService()
service.start()
"

# Or use service manager
claude-multiagent-pm-service start

# Check logs for detailed error information
tail -f ~/.claude-multiagent-pm/logs/agent-orchestrator.log
```

#### 2. Agent Communication Failures

**Problem**: Agents can't communicate with each other or the orchestrator

**Symptoms**:
```bash
Error: Agent communication timeout
Warning: Agent delegation chain broken
```

**Diagnostic Commands**:
```bash
# Test agent communication
python3 -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
import asyncio

async def test_communication():
    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.health_check()
    print(f'Communication test: {result}')

asyncio.run(test_communication())
"
```

**Solution**:
```bash
# Check network connectivity
netstat -tlnp | grep 8002  # Memory service port
lsof -i :8002

# Restart agent services
claude-multiagent-pm-service restart

# Check firewall settings
sudo ufw status
```

#### 3. Agent Memory Issues

**Problem**: Agents experiencing memory leaks or high memory usage

**Symptoms**:
```bash
Warning: Agent memory usage above threshold (2GB)
Error: Agent process killed due to memory limit
```

**Diagnostic Commands**:
```bash
# Monitor memory usage
python3 -c "
import psutil
import os

def check_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f'RSS: {memory_info.rss / 1024 / 1024:.2f} MB')
    print(f'VMS: {memory_info.vms / 1024 / 1024:.2f} MB')

check_memory()
"

# Check system memory
free -h
ps aux | grep claude-pm | head -10
```

**Solution**:
```bash
# Configure memory limits
export CLAUDE_PM_MEMORY_LIMIT=1024M
export CLAUDE_PM_MAX_AGENTS=3

# Restart with memory optimization
claude-multiagent-pm-service restart --memory-limit 1024

# Monitor memory usage
watch -n 5 'ps aux | grep claude-pm'
```

---

## Configuration Issues

### Configuration File Problems

#### 1. Invalid Configuration Errors

**Problem**: Configuration file contains invalid settings

**Symptoms**:
```bash
Error: Invalid configuration in ~/.claude-multiagent-pm/config/config.yaml
JSONDecodeError: Expecting ',' delimiter: line 5 column 4
```

**Diagnostic Commands**:
```bash
# Validate JSON configuration
python3 -c "
import json
try:
    with open('~/.claude-multiagent-pm/config/config.yaml', 'r') as f:
        config = json.load(f)
    print('✓ Configuration valid')
    print(json.dumps(config, indent=2))
except Exception as e:
    print(f'✗ Configuration error: {e}')
"

# Check configuration file permissions
ls -la ~/.claude-multiagent-pm/config/config.yaml
```

**Solution**:
```bash
# Create backup and fix configuration
cp ~/.claude-multiagent-pm/config/config.yaml ~/.claude-multiagent-pm/config/config.yaml.backup

# Create new valid configuration
cat > ~/.claude-multiagent-pm/config/config.yaml << 'EOF'
{
  "version": "4.2.0",
  "python_cmd": "python3",
  "memory_service_url": "http://localhost:8002",
  "max_concurrent_agents": 5,
  "default_agent_timeout": 300,
  "log_level": "info",
  "workspace_dir": "~/Projects/claude-pm-workspace"
}
EOF
```

#### 2. Environment Variable Issues

**Problem**: Environment variables not being read or set incorrectly

**Symptoms**:
```bash
Warning: CLAUDE_PM_HOME not set, using default
Error: Environment variable CLAUDE_PM_MEMORY_URL is invalid
```

**Diagnostic Commands**:
```bash
# Check environment variables
echo "CLAUDE_PM_HOME: $CLAUDE_PM_HOME"
echo "CLAUDE_PM_MEMORY_URL: $CLAUDE_PM_MEMORY_URL"
echo "CLAUDE_PM_LOG_LEVEL: $CLAUDE_PM_LOG_LEVEL"

# List all CLAUDE_PM variables
env | grep CLAUDE_PM
```

**Solution**:
```bash
# Set environment variables
export CLAUDE_PM_HOME=~/Projects/claude-pm-workspace
export CLAUDE_PM_MEMORY_URL=http://localhost:8002
export CLAUDE_PM_LOG_LEVEL=info
export CLAUDE_PM_MAX_AGENTS=5

# Add to shell profile for persistence
cat >> ~/.bashrc << 'EOF'
# Claude PM Framework Configuration
export CLAUDE_PM_HOME=~/Projects/claude-pm-workspace
export CLAUDE_PM_CONFIG_DIR=~/.claude-multiagent-pm
export CLAUDE_PM_LOG_LEVEL=info
export CLAUDE_PM_MEMORY_URL=http://localhost:8002
export CLAUDE_PM_MAX_AGENTS=5
EOF

# Reload configuration
source ~/.bashrc
```

#### 3. Service Integration Configuration

**Problem**: External services not configured properly

**Symptoms**:
```bash
Error: mem0AI service connection failed
Warning: Authentication failed for external service
```

**Diagnostic Commands**:
```bash
# Test service endpoints
curl -s http://localhost:8002/health
curl -s http://localhost:3000/
curl -s http://localhost:3001/health

# Check authentication setup
python3 -c "
from claude_pm.integrations.security import SecurityManager
try:
    security = SecurityManager()
    print('✓ Security manager initialized')
    print(f'API keys configured: {security.list_configured_keys()}')
except Exception as e:
    print(f'✗ Security error: {e}')
"
```

**Solution**:
```bash
# Configure API keys
claude-pm config set-api-key --service mem0ai --key YOUR_API_KEY

# Check service configuration
claude-pm config validate

# Restart services with new configuration
claude-multiagent-pm-service restart
```

---

## Performance and Scalability

### Slow Response Times

#### 1. General Performance Issues

**Problem**: System responding slowly to commands

**Symptoms**:
```bash
$ claude-pm status
# Takes >10 seconds to respond
```

**Diagnostic Commands**:
```bash
# Check system performance
python3 -c "
import time
import psutil

# CPU usage
cpu_percent = psutil.cpu_percent(interval=1)
print(f'CPU Usage: {cpu_percent}%')

# Memory usage
memory = psutil.virtual_memory()
print(f'Memory Usage: {memory.percent}%')

# Disk I/O
disk = psutil.disk_usage('/')
print(f'Disk Usage: {disk.percent}%')
"

# Check for long-running processes
ps aux | grep claude-pm | grep -v grep
```

**Solution**:
```bash
# Optimize configuration
export CLAUDE_PM_WORKERS=2
export CLAUDE_PM_CACHE_SIZE=100M

# Restart with performance settings
claude-multiagent-pm-service restart --workers 2

# Monitor performance
watch -n 5 'ps aux | grep claude-pm'
```

#### 2. Memory Usage Optimization

**Problem**: High memory consumption

**Symptoms**:
```bash
Warning: Memory usage above 80%
Error: System running out of memory
```

**Diagnostic Commands**:
```bash
# Analyze memory usage
python3 -c "
import psutil
import os

def analyze_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    children = process.children(recursive=True)
    
    print(f'Main process: {memory_info.rss / 1024 / 1024:.2f} MB')
    
    total_child_memory = 0
    for child in children:
        try:
            child_memory = child.memory_info().rss
            total_child_memory += child_memory
            print(f'Child {child.pid}: {child_memory / 1024 / 1024:.2f} MB')
        except psutil.NoSuchProcess:
            pass
    
    print(f'Total child memory: {total_child_memory / 1024 / 1024:.2f} MB')

analyze_memory()
"
```

**Solution**:
```bash
# Configure memory limits
export CLAUDE_PM_MEMORY_LIMIT=512M
export CLAUDE_PM_MAX_AGENTS=3
export CLAUDE_PM_CACHE_SIZE=50M

# Use memory-optimized settings
claude-pm config set memory_optimization true
claude-pm config set max_concurrent_agents 3

# Monitor memory usage
watch -n 5 'free -h'
```

#### 3. Concurrent Operation Issues

**Problem**: System struggles with multiple concurrent operations

**Symptoms**:
```bash
Error: Maximum concurrent agents reached
Warning: Operation queued due to resource constraints
```

**Diagnostic Commands**:
```bash
# Check concurrent operations
python3 -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
orchestrator = MultiAgentOrchestrator()
print(f'Active agents: {len(orchestrator.get_active_agents())}')
print(f'Max agents: {orchestrator.get_max_agents()}')
"

# Monitor system load
uptime
cat /proc/loadavg
```

**Solution**:
```bash
# Adjust concurrency limits
export CLAUDE_PM_MAX_CONCURRENT_AGENTS=3
export CLAUDE_PM_AGENT_TIMEOUT=180

# Configure queue settings
claude-pm config set agent_queue_size 10
claude-pm config set agent_timeout 180

# Monitor concurrent operations
watch -n 2 'claude-pm status --format json | jq .active_agents'
```

---

## Integration Problems

### API Integration Failures

#### 1. External API Connection Issues

**Problem**: Cannot connect to external APIs

**Symptoms**:
```bash
Error: HTTP 503 Service Unavailable
Error: Connection timeout to external service
```

**Diagnostic Commands**:
```bash
# Test API connectivity
curl -I https://api.openai.com/v1/models
curl -I https://api.mem0.ai/v1/health

# Check DNS resolution
nslookup api.openai.com
nslookup api.mem0.ai

# Test network connectivity
ping -c 3 api.openai.com
```

**Solution**:
```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Set API timeouts
export CLAUDE_PM_API_TIMEOUT=30
export CLAUDE_PM_RETRY_ATTEMPTS=3

# Test with curl
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

#### 2. Database Connection Issues

**Problem**: Cannot connect to database services

**Symptoms**:
```bash
Error: Connection refused to database
Error: Database authentication failed
```

**Diagnostic Commands**:
```bash
# Check database service status
systemctl status postgresql
systemctl status redis

# Test database connectivity
psql -h localhost -U postgres -c "SELECT version();"
redis-cli ping
```

**Solution**:
```bash
# Start database services
sudo systemctl start postgresql
sudo systemctl start redis

# Configure database connection
claude-pm config set database_url "postgresql://user:password@localhost:5432/claude_pm"
claude-pm config set redis_url "redis://localhost:6379"

# Test database migration
claude-pm db migrate
```

#### 3. Authentication and Authorization Issues

**Problem**: Authentication failures with external services

**Symptoms**:
```bash
Error: 401 Unauthorized
Error: API key invalid or expired
```

**Diagnostic Commands**:
```bash
# Check API key configuration
claude-pm config list-keys

# Test authentication
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models

# Verify key format
python3 -c "
import os
key = os.getenv('OPENAI_API_KEY')
print(f'Key length: {len(key) if key else 0}')
print(f'Key starts with: {key[:7] if key else None}')
"
```

**Solution**:
```bash
# Set API keys
export OPENAI_API_KEY=your_openai_key_here
export MEM0_API_KEY=your_mem0_key_here

# Configure keys through CLI
claude-pm config set-api-key --service openai --key YOUR_KEY
claude-pm config set-api-key --service mem0ai --key YOUR_KEY

# Test authentication
claude-pm auth test --service openai
```

---

## Health Monitoring Issues

### Health Check Failures

#### 1. Health Monitor Not Running

**Problem**: Health monitoring service not starting

**Symptoms**:
```bash
$ npm run monitor:status
Error: Health monitor not running
```

**Diagnostic Commands**:
```bash
# Check health monitor status
ps aux | grep automated-health-monitor
pm2 status claude-pm-health-monitor

# Check logs directory
ls -la ~/Projects/Claude-PM/logs/

# Test health monitor script
node scripts/automated-health-monitor.js --help
```

**Solution**:
```bash
# Create logs directory if missing
mkdir -p ~/Projects/Claude-PM/logs/

# Start health monitor
npm run monitor:once

# Start background monitoring
pm2 start ecosystem.config.js

# Check PM2 status
pm2 status
pm2 logs claude-pm-health-monitor
```

#### 2. Service Health Checks Failing

**Problem**: Service endpoints returning errors

**Symptoms**:
```bash
Warning: mem0AI MCP service unhealthy
Error: Portfolio Manager not responding
```

**Diagnostic Commands**:
```bash
# Test individual services
curl -s http://localhost:8002/health || echo "mem0AI service down"
curl -s http://localhost:3000/ || echo "Portfolio Manager down"
curl -s http://localhost:3001/health || echo "Git Portfolio Manager down"

# Check service processes
ps aux | grep -E "(mem0|portfolio|claude-pm)"
```

**Solution**:
```bash
# Start missing services
claude-multiagent-pm-service start

# Skip service checks if not needed
npm run monitor:once -- --no-services

# Check service configuration
claude-pm config validate --services
```

#### 3. Framework Compliance Issues

**Problem**: Framework structure validation failing

**Symptoms**:
```bash
Warning: CLAUDE.md file missing in project
Error: Framework compliance below threshold
```

**Diagnostic Commands**:
```bash
# Check framework structure
ls -la CLAUDE.md
ls -la trackdown/
ls -la docs/

# Validate framework compliance
claude-pm validate --framework
```

**Solution**:
```bash
# Create missing framework files
touch CLAUDE.md
mkdir -p trackdown docs scripts

# Initialize framework structure
claude-pm init --framework-structure

# Check compliance
npm run monitor:once -- --verbose
```

---

## Diagnostic Tools

### Built-in Diagnostic Commands

#### 1. System Health Check

```bash
# Comprehensive health check
claude-pm health

# Detailed system status
claude-pm status --verbose

# Service-specific checks
claude-pm status --service memory
claude-pm status --service agents
```

#### 2. Framework Validation

```bash
# Validate framework structure
claude-pm validate --framework

# Check configuration
claude-pm config validate

# Test agent system
claude-pm agent test --all
```

#### 3. Performance Monitoring

```bash
# Monitor system performance
claude-pm monitor --performance

# Check resource usage
claude-pm stats --resources

# Analyze bottlenecks
claude-pm analyze --performance
```

### Health Monitor Commands

#### 1. Basic Health Monitoring

```bash
# Single health check
npm run monitor:once

# Verbose health check
npm run monitor:verbose

# Check monitor status
npm run monitor:status
```

#### 2. Background Monitoring

```bash
# Start continuous monitoring
npm run monitor:health

# Background monitoring with custom interval
node scripts/automated-health-monitor.js monitor --interval=10

# Check monitoring process
pm2 status claude-pm-health-monitor
```

#### 3. Alert Management

```bash
# View recent alerts
npm run monitor:alerts

# Show health reports
npm run monitor:reports

# Disable alerts temporarily
node scripts/automated-health-monitor.js monitor --no-alerts
```

### Log Analysis Tools

#### 1. Log Locations

```bash
# System logs
tail -f ~/.claude-multiagent-pm/logs/system.log

# Agent logs
tail -f ~/.claude-multiagent-pm/logs/agents.log

# Health monitor logs
tail -f ~/Projects/Claude-PM/logs/health-monitor.log

# Error logs
tail -f ~/.claude-multiagent-pm/logs/errors.log
```

#### 2. Log Analysis Commands

```bash
# Search for errors
grep -i error ~/.claude-multiagent-pm/logs/*.log

# Find performance issues
grep -i "timeout\|slow\|performance" ~/.claude-multiagent-pm/logs/*.log

# Analyze patterns
awk '/ERROR/ {print $1, $2, $5}' ~/.claude-multiagent-pm/logs/system.log
```

#### 3. Log Rotation and Management

```bash
# Check log sizes
du -h ~/.claude-multiagent-pm/logs/

# Rotate logs manually
logrotate -f ~/.claude-multiagent-pm/logrotate.conf

# Clean old logs
find ~/.claude-multiagent-pm/logs/ -name "*.log.*" -mtime +7 -delete
```

---

## Frequently Asked Questions

### General Usage Questions

#### Q: How do I know if CMPM is working correctly?

**A**: Run the comprehensive health check:
```bash
# Quick health check
claude-pm health

# Detailed system verification
./scripts/health-check.sh

# Run feature tests
python3 -c "
import claude_pm
print('✓ Framework loaded successfully')

from claude_pm.services.memory_service import MemoryService
print('✓ Memory service available')

from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
print('✓ Agent orchestration available')
"
```

#### Q: What are the minimum system requirements?

**A**: Minimum requirements:
- **CPU**: 2-core processor (x64 or ARM64)
- **RAM**: 4GB available memory
- **Storage**: 2GB free disk space
- **Network**: Stable internet connection
- **Software**: Node.js 16+, Python 3.9+

Recommended for production:
- **CPU**: 4+ cores
- **RAM**: 8GB+ available
- **Storage**: 5GB+ free space
- **Network**: High-speed internet

#### Q: How do I upgrade CMPM to a newer version?

**A**: 
```bash
# For npm installation
npm update -g claude-multiagent-pm
npm update -g @bobmatnyc/ai-trackdown-tools

# For pip installation
pip install --upgrade claude-multiagent-pm[all]

# For development installation
cd claude-multiagent-pm
git pull origin main
pip install -e .
```

### Configuration Questions

#### Q: Where are configuration files stored?

**A**: Configuration files are stored in:
- **Global config**: `~/.claude-multiagent-pm/config/config.yaml`
- **Project config**: `./claude-pm-project.json`
- **Environment variables**: Shell profile files
- **Service config**: `/etc/claude-pm/` (production)

#### Q: How do I change the default memory service URL?

**A**:
```bash
# Set environment variable
export CLAUDE_PM_MEMORY_URL=http://localhost:8003

# Or update configuration file
claude-pm config set memory_service_url http://localhost:8003

# Or edit directly
vim ~/.claude-multiagent-pm/config/config.yaml
```

#### Q: Can I disable certain features?

**A**: Yes, you can disable features through configuration:
```bash
# Disable memory integration
claude-pm config set memory_integration false

# Disable agent coordination
claude-pm config set agent_coordination false

# Disable health monitoring
claude-pm config set health_monitoring false
```

### Agent System Questions

#### Q: How many agents can run simultaneously?

**A**: The default limit is 5 concurrent agents. You can adjust this:
```bash
# Set maximum concurrent agents
export CLAUDE_PM_MAX_AGENTS=3

# Or via configuration
claude-pm config set max_concurrent_agents 3
```

#### Q: What happens when an agent fails?

**A**: CMPM has built-in error handling:
- **Auto-retry**: Failed operations retry up to 3 times
- **Graceful degradation**: System continues with reduced functionality
- **Error logging**: All failures are logged for analysis
- **Alert system**: Critical failures trigger alerts

#### Q: How do I create custom agents?

**A**: See the [Custom Agents Guide](05-custom-agents.md) for detailed instructions. Basic steps:
1. Create agent configuration file
2. Implement agent interface
3. Register with orchestrator
4. Test and deploy

### Performance Questions

#### Q: Why is CMPM using too much memory?

**A**: Common causes and solutions:
```bash
# Check memory usage
ps aux | grep claude-pm

# Reduce concurrent agents
export CLAUDE_PM_MAX_AGENTS=2

# Configure memory limits
export CLAUDE_PM_MEMORY_LIMIT=512M

# Restart with optimization
claude-multiagent-pm-service restart --memory-limit 512M
```

#### Q: How can I improve response times?

**A**: Optimization strategies:
- **Reduce concurrent agents**: Lower `max_concurrent_agents`
- **Increase timeouts**: Adjust `agent_timeout` settings
- **Use caching**: Enable memory caching
- **Optimize database**: Ensure database is properly indexed

#### Q: What causes "Connection timeout" errors?

**A**: Common causes:
- **Network issues**: Check internet connectivity
- **Service overload**: Reduce concurrent operations
- **Configuration issues**: Verify service URLs and ports
- **Firewall blocking**: Check firewall rules

### Troubleshooting Questions

#### Q: How do I reset CMPM to default settings?

**A**:
```bash
# Backup current configuration
cp -r ~/.claude-multiagent-pm ~/.claude-multiagent-pm.backup

# Remove configuration
rm -rf ~/.claude-multiagent-pm

# Reinitialize
claude-pm init

# Or restore from backup
mv ~/.claude-multiagent-pm.backup ~/.claude-multiagent-pm
```

#### Q: What should I do if agents stop responding?

**A**: Emergency recovery steps:
```bash
# Check system status
claude-pm status

# Restart agent system
claude-multiagent-pm-service restart

# Check logs for errors
tail -f ~/.claude-multiagent-pm/logs/agents.log

# Force restart if needed
pkill -f claude-pm
claude-multiagent-pm-service start
```

#### Q: How do I collect diagnostic information for support?

**A**: Gather diagnostic information:
```bash
# Create diagnostic report
claude-pm diagnostic --full > diagnostic-report.txt

# Include system information
uname -a >> diagnostic-report.txt
cat /etc/os-release >> diagnostic-report.txt

# Include configuration
cat ~/.claude-multiagent-pm/config/config.yaml >> diagnostic-report.txt

# Include recent logs
tail -100 ~/.claude-multiagent-pm/logs/system.log >> diagnostic-report.txt
```

---

## Support and Escalation

### Self-Service Resources

#### 1. Documentation

- **[Getting Started Guide](01-getting-started.md)**: Complete setup instructions
- **[Architecture Concepts](02-architecture-concepts.md)**: System design overview
- **[Slash Commands](03-slash-commands-orchestration.md)**: Command reference
- **[Directory Organization](04-directory-organization.md)**: File structure guide
- **[Custom Agents](05-custom-agents.md)**: Agent development guide

#### 2. Built-in Help

```bash
# Command help
claude-pm --help
claude-pm agent --help
claude-pm config --help

# Feature-specific help
aitrackdown --help
npm run monitor:help
```

#### 3. Health and Status Commands

```bash
# System health
claude-pm health

# Service status
claude-pm status --all

# Configuration validation
claude-pm config validate

# Performance analysis
claude-pm analyze --performance
```

### Community Support

#### 1. GitHub Issues

- **Bug Reports**: Use the issue template for bug reports
- **Feature Requests**: Submit enhancement requests
- **Questions**: Ask questions in discussions

#### 2. Documentation Updates

- **Contribute**: Submit documentation improvements
- **Examples**: Share usage examples
- **Tutorials**: Create community tutorials

### Professional Support

#### 1. Escalation Criteria

Escalate to professional support when:
- **Critical production issues**: System completely non-functional
- **Security concerns**: Potential security vulnerabilities
- **Performance degradation**: Significant performance issues
- **Data loss**: Risk of data corruption or loss

#### 2. Support Information to Provide

When contacting support, include:

**System Information**:
```bash
# Gather system info
claude-pm diagnostic --system-info

# Include versions
claude-pm --version
node --version
python3 --version
```

**Configuration Details**:
```bash
# Sanitized configuration
claude-pm config export --sanitized

# Environment variables
env | grep CLAUDE_PM
```

**Error Logs**:
```bash
# Recent errors
tail -100 ~/.claude-multiagent-pm/logs/errors.log

# System logs
tail -100 ~/.claude-multiagent-pm/logs/system.log
```

**Steps to Reproduce**:
- Clear description of the issue
- Steps to reproduce the problem
- Expected vs actual behavior
- Screenshots or error messages

#### 3. Emergency Contacts

For critical production issues:
- **GitHub Issues**: Mark as `critical` priority
- **Email**: Use emergency contact if provided
- **Support Portal**: Submit high-priority ticket

### Temporary Workarounds

#### 1. Common Workarounds

**Service Unavailable**:
```bash
# Skip service checks
npm run monitor:once -- --no-services

# Use offline mode
claude-pm --offline
```

**Memory Issues**:
```bash
# Reduce memory usage
export CLAUDE_PM_MAX_AGENTS=2
export CLAUDE_PM_MEMORY_LIMIT=256M
```

**Performance Issues**:
```bash
# Emergency performance mode
claude-pm --performance-mode emergency
```

#### 2. Rollback Procedures

**Configuration Rollback**:
```bash
# Restore from backup
cp ~/.claude-multiagent-pm.backup/config/config.yaml ~/.claude-multiagent-pm/config/config.yaml

# Restart services
claude-multiagent-pm-service restart
```

**System Rollback**:
```bash
# Downgrade to previous version
pip install claude-multiagent-pm==4.0.0

# Restore previous configuration
git checkout HEAD~1 -- ~/.claude-multiagent-pm/
```

---

## Conclusion

This troubleshooting guide covers the most common issues encountered when using CMPM. For issues not covered here:

1. **Check the logs**: Most issues are logged with detailed error messages
2. **Run diagnostics**: Use built-in diagnostic tools
3. **Consult documentation**: Review relevant sections of the user guide
4. **Seek community support**: Use GitHub issues for community help
5. **Contact professional support**: For critical issues requiring immediate attention

Remember to keep your system updated and regularly run health checks to prevent issues before they occur.

**Framework Version**: 4.2.0  
**Last Updated**: 2025-07-09  
**Support Level**: Community + Professional