# Claude PM Framework Troubleshooting Guide v4.2.0

## Table of Contents

1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Common Issues](#common-issues)
3. [Service-Specific Troubleshooting](#service-specific-troubleshooting)
4. [Error Patterns and Solutions](#error-patterns-and-solutions)
5. [Log Analysis](#log-analysis)
6. [Recovery Procedures](#recovery-procedures)
7. [Performance Issues](#performance-issues)
8. [Configuration Problems](#configuration-problems)
9. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostic Commands

### System Status Check
```bash
# Quick health check
./scripts/health-check.sh

# Framework status
python3 -c "import claude_pm; print('Framework accessible')"

# AI trackdown status
aitrackdown status

# Memory service status
curl -s http://localhost:8002/health | jq .
```

### Component Status
```bash
# Check all services
python3 -c "
from claude_pm.services.health_monitor import HealthMonitorService
from claude_pm.services.memory_service import get_memory_service
from claude_pm.services.project_service import ProjectService

print('Health Monitor:', HealthMonitorService().is_healthy())
print('Memory Service:', get_memory_service().is_healthy())
print('Project Service:', ProjectService().is_healthy())
"

# Check AI trackdown integration
python3 -c "
from claude_pm.utils.ai_trackdown_tools import get_ai_trackdown_tools
tools = get_ai_trackdown_tools()
print('AI Trackdown Enabled:', tools.is_enabled())
print('AI Trackdown Available:', tools.is_available())
"
```

### Log Location Check
```bash
# Main log files
ls -la logs/
tail -f logs/health-monitor.log
tail -f logs/memory_service.log
tail -f logs/ai_trackdown_health.json
```

## Common Issues

### 1. Framework Import Errors

#### Symptoms
- `ImportError: No module named 'claude_pm'`
- `ModuleNotFoundError: No module named 'claude_pm.services'`
- Python import failures

#### Diagnosis
```bash
# Check Python path
python3 -c "import sys; print('\\n'.join(sys.path))"

# Check if framework directory exists
ls -la claude_pm/

# Check framework structure
find claude_pm/ -name "*.py" | head -10

# Test import
python3 -c "import claude_pm; print('Success')"
```

#### Solutions
1. **Fix Python Path**:
   ```bash
   export PYTHONPATH="/Users/masa/Projects/claude-multiagent-pm:$PYTHONPATH"
   echo 'export PYTHONPATH="/Users/masa/Projects/claude-multiagent-pm:$PYTHONPATH"' >> ~/.bashrc
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements/production.txt
   ```

3. **Check Working Directory**:
   ```bash
   cd /Users/masa/Projects/claude-multiagent-pm
   python3 -c "import claude_pm; print('Success')"
   ```

### 2. AI Trackdown Tools Not Found

#### Symptoms
- `command not found: aitrackdown`
- `command not found: atd`
- CLI timeout errors

#### Diagnosis
```bash
# Check global npm packages
npm list -g @bobmatnyc/ai-trackdown-tools

# Check PATH
echo $PATH | grep -o '[^:]*' | grep node

# Check node modules
ls -la /Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/ai-trackdown-tools

# Test CLI directly
node /Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/ai-trackdown-tools/dist/index.js --version
```

#### Solutions
1. **Reinstall AI Trackdown Tools**:
   ```bash
   npm uninstall -g @bobmatnyc/ai-trackdown-tools
   npm install -g @bobmatnyc/ai-trackdown-tools
   ```

2. **Fix PATH**:
   ```bash
   export PATH="/Users/masa/.nvm/versions/node/v20.19.0/bin:$PATH"
   ```

3. **Use Direct Path**:
   ```bash
   node /Users/masa/.nvm/versions/node/v20.19.0/lib/node_modules/@bobmatnyc/ai-trackdown-tools/dist/index.js status
   ```

4. **Check CLI Wrappers**:
   ```bash
   ls -la bin/aitrackdown
   cat bin/aitrackdown
   chmod +x bin/aitrackdown
   ```

### 3. Memory Service Connection Issues

#### Symptoms
- `Connection refused` to localhost:8002
- Memory operations timing out
- Context preparation failures

#### Diagnosis
```bash
# Check if service is running
curl -s http://localhost:8002/health

# Check port availability
netstat -an | grep 8002
lsof -i :8002

# Test memory service
python3 -c "
from claude_pm.services.memory_service import ClaudePMMemory
memory = ClaudePMMemory()
print('Connected:', memory.is_connected())
"
```

#### Solutions
1. **Start mem0AI Service**:
   ```bash
   # If using systemd
   sudo systemctl start mem0ai
   sudo systemctl enable mem0ai
   
   # If using manual start
   python3 -m mem0ai.server --host localhost --port 8002
   ```

2. **Check Service Configuration**:
   ```bash
   # Check configuration
   cat config/memory_config.json
   
   # Test with different host/port
   python3 -c "
   from claude_pm.services.memory_service import ClaudePMMemory, ClaudePMConfig
   config = ClaudePMConfig(host='localhost', port=8002)
   memory = ClaudePMMemory(config)
   print('Service accessible:', memory._health_check())
   "
   ```

3. **Fallback Mode**:
   ```bash
   # Disable memory service temporarily
   python3 -c "
   from claude_pm.core.config import Config
   config = Config()
   config.set('memory_service_enabled', False)
   print('Memory service disabled')
   "
   ```

### 4. Health Check Failures

#### Symptoms
- Health check script returns errors
- Component health checks fail
- System health percentage low

#### Diagnosis
```bash
# Run verbose health check
./scripts/health-check.sh 2>&1 | tee health_check.log

# Check individual components
python3 -c "
from claude_pm.services.health_monitor import HealthMonitorService
hms = HealthMonitorService()
print('Health checks:', hms._health_check())
"

# Check health report
cat logs/health-report.json | jq .
```

#### Solutions
1. **Fix Individual Components**:
   ```bash
   # Fix each failing component based on health report
   # Example: Fix memory service
   curl http://localhost:8002/health || echo "Memory service down"
   
   # Example: Fix AI trackdown
   aitrackdown --version || echo "AI trackdown issue"
   ```

2. **Restart Services**:
   ```bash
   # Restart all services
   pkill -f claude_pm
   python3 -m claude_pm.cli health --restart-services
   ```

3. **Check Dependencies**:
   ```bash
   # Check Python dependencies
   pip check
   
   # Check Node.js dependencies
   npm doctor
   ```

### 5. Task System Issues

#### Symptoms
- Task creation failures
- Missing task directories
- Ticket hierarchy corruption

#### Diagnosis
```bash
# Check task structure
ls -la tasks/
find tasks/ -name "*.md" | wc -l

# Check task integrity
python3 -c "
from claude_pm.utils.ai_trackdown_tools import get_ai_trackdown_tools
tools = get_ai_trackdown_tools()
print('Task system status:', tools.get_status())
"

# Test task creation
aitrackdown epic create "Test Epic" --description "Test"
```

#### Solutions
1. **Recreate Task Structure**:
   ```bash
   mkdir -p tasks/{epics,issues,tasks,prs}
   mkdir -p tasks/templates
   ```

2. **Fix Task Templates**:
   ```bash
   # Copy templates from source
   cp -r templates/epic-default.yaml tasks/templates/
   cp -r templates/issue-default.yaml tasks/templates/
   cp -r templates/task-default.yaml tasks/templates/
   ```

3. **Validate Task Data**:
   ```bash
   # Check for corrupted files
   find tasks/ -name "*.md" -exec head -1 {} \; | grep -v "^#"
   
   # Fix permissions
   chmod -R 644 tasks/
   ```

## Service-Specific Troubleshooting

### Memory Service Issues

#### Connection Pool Exhaustion
```bash
# Symptoms: "Connection pool exhausted"
# Check pool status
python3 -c "
from claude_pm.services.memory_service import get_memory_service
ms = get_memory_service()
print('Pool stats:', ms.client._connection_pool)
"

# Solution: Restart service
python3 -c "
from claude_pm.services.memory_service import get_memory_service
ms = get_memory_service()
ms.client.disconnect()
ms.client.connect()
"
```

#### Memory Cache Issues
```bash
# Clear memory cache
python3 -c "
from claude_pm.services.memory_service import get_memory_service
ms = get_memory_service()
ms.client._memory_cache.clear()
ms.client._cache_expiry.clear()
print('Cache cleared')
"
```

### Health Monitor Issues

#### Background Monitoring Failures
```bash
# Check background process
ps aux | grep health_monitor

# Check monitoring logs
tail -f logs/health-monitor.log

# Restart monitoring
python3 scripts/automated_health_monitor.py monitor --restart
```

#### Health Report Generation Issues
```bash
# Generate health report manually
python3 scripts/automated_health_monitor.py once --verbose

# Check report format
cat logs/health-report.json | jq . || echo "Invalid JSON"

# Fix report corruption
rm logs/health-report.json
python3 scripts/automated_health_monitor.py once
```

### Project Service Issues

#### Project Discovery Failures
```bash
# Check project paths
python3 -c "
from claude_pm.services.project_service import ProjectService
ps = ProjectService()
print('Base path:', ps.base_path)
print('Managed path:', ps.managed_path)
print('Paths exist:', ps.base_path.exists(), ps.managed_path.exists())
"

# Run discovery manually
python3 -c "
from claude_pm.services.project_service import ProjectService
ps = ProjectService()
ps._discover_projects()
print('Projects found:', len(ps.get_projects()))
"
```

#### Compliance Check Issues
```bash
# Check compliance for specific project
python3 -c "
from claude_pm.services.project_service import ProjectService
ps = ProjectService()
projects = ps.get_projects()
for name, project in projects.items():
    compliance = ps.get_compliance(name)
    print(f'{name}: {compliance.score}% compliance')
"
```

### Multi-Agent Orchestrator Issues

#### Agent Execution Failures
```bash
# Check orchestrator status
python3 -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator
from claude_pm.services.memory_service import get_memory_service
memory = get_memory_service()
orchestrator = MultiAgentOrchestrator('/Users/masa/Projects/claude-multiagent-pm', memory.client)
print('Orchestrator stats:', orchestrator.get_orchestrator_stats())
"

# Check git worktrees
cd /Users/masa/Projects/claude-multiagent-pm
git worktree list
git worktree prune
```

#### Memory Context Preparation Issues
```bash
# Test context preparation
python3 -c "
from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator, AgentType
from claude_pm.services.memory_service import get_memory_service
memory = get_memory_service()
orchestrator = MultiAgentOrchestrator('/Users/masa/Projects/claude-multiagent-pm', memory.client)
context = orchestrator.prepare_memory_context(AgentType.ENGINEER, 'test-project', 'test task')
print('Context prepared:', len(context.get('relevant_memories', {})))
"
```

## Error Patterns and Solutions

### Pattern 1: Service Initialization Failures

#### Error Pattern
```
ERROR: Service initialization failed
ERROR: Failed to initialize service_name
ERROR: Service dependency not available
```

#### Solution Steps
1. **Check Dependencies**:
   ```bash
   # Check service dependencies
   python3 -c "
   from claude_pm.services.service_name import ServiceName
   service = ServiceName()
   print('Dependencies:', service.check_dependencies())
   "
   ```

2. **Initialize in Order**:
   ```bash
   # Initialize services in dependency order
   python3 -c "
   from claude_pm.core.service_manager import ServiceManager
   manager = ServiceManager()
   manager.initialize_services()
   "
   ```

### Pattern 2: Configuration Validation Errors

#### Error Pattern
```
ERROR: Configuration validation failed
ERROR: Invalid configuration for component
ERROR: Required configuration missing
```

#### Solution Steps
1. **Validate Configuration**:
   ```bash
   # Check configuration files
   find config/ -name "*.json" -exec python3 -m json.tool {} \;
   
   # Check YAML files
   find config/ -name "*.yaml" -exec python3 -c "import yaml; yaml.safe_load(open('{}'))" \;
   ```

2. **Fix Configuration**:
   ```bash
   # Copy default configuration
   cp config/default_config.json config/config.json
   
   # Validate after fix
   python3 -c "
   from claude_pm.core.config import Config
   config = Config()
   print('Configuration valid:', config.validate())
   "
   ```

### Pattern 3: Network Connection Errors

#### Error Pattern
```
ERROR: Connection refused
ERROR: Timeout connecting to service
ERROR: Network unreachable
```

#### Solution Steps
1. **Check Network Connectivity**:
   ```bash
   # Test local connections
   nc -zv localhost 8002
   
   # Check network interfaces
   ifconfig | grep inet
   
   # Test DNS resolution
   nslookup localhost
   ```

2. **Fix Network Issues**:
   ```bash
   # Restart network service (if needed)
   sudo systemctl restart networking
   
   # Reset network stack
   sudo ifconfig lo0 down && sudo ifconfig lo0 up
   ```

### Pattern 4: Permission Errors

#### Error Pattern
```
ERROR: Permission denied
ERROR: Access denied to resource
ERROR: Insufficient permissions
```

#### Solution Steps
1. **Check File Permissions**:
   ```bash
   # Check key files
   ls -la claude_pm/
   ls -la bin/
   ls -la config/
   
   # Fix permissions
   chmod -R 755 bin/
   chmod -R 644 config/
   ```

2. **Check Process Permissions**:
   ```bash
   # Check running processes
   ps aux | grep claude_pm
   
   # Check file ownership
   ls -la | grep claude_pm
   ```

## Log Analysis

### Log File Locations
```bash
# Main log files
logs/health-monitor.log                 # Health monitoring
logs/memory_service.log                 # Memory service
logs/ai_trackdown_health.json          # AI trackdown health
logs/enhanced_doc_sync.log              # Documentation sync
logs/health-report.json                 # System health report
```

### Log Analysis Commands
```bash
# Check for errors
grep -i error logs/*.log

# Check for warnings
grep -i warning logs/*.log

# Monitor real-time logs
tail -f logs/health-monitor.log

# Analyze health trends
jq '.overall_health' logs/health-*.json | sort -n

# Check service response times
jq '.components[].response_time' logs/health-report.json
```

### Log Rotation
```bash
# Manual log rotation
find logs/ -name "*.log" -size +10M -exec gzip {} \;

# Archive old logs
find logs/ -name "*.log.gz" -mtime +30 -delete

# Setup log rotation
cat > /etc/logrotate.d/claude-pm << EOF
/Users/masa/Projects/claude-multiagent-pm/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
```

## Recovery Procedures

### Quick Recovery Checklist
```bash
# 1. Stop all services
pkill -f claude_pm

# 2. Check system resources
df -h
free -m
ps aux | head -20

# 3. Clear temporary files
rm -rf /tmp/claude_pm_*
rm -rf /tmp/memory_cache/*

# 4. Restart services
python3 -m claude_pm.cli health --restart-services

# 5. Validate system
./scripts/health-check.sh
```

### Service Recovery Order
1. **Memory Service** (if external)
2. **Health Monitor**
3. **Project Service**
4. **Multi-Agent Orchestrator**
5. **AI Trackdown Integration**

### Recovery Validation
```bash
# Validate each service after recovery
python3 -c "
from claude_pm.services.health_monitor import HealthMonitorService
from claude_pm.services.memory_service import get_memory_service
from claude_pm.services.project_service import ProjectService

services = [
    ('Health Monitor', HealthMonitorService()),
    ('Memory Service', get_memory_service()),
    ('Project Service', ProjectService())
]

for name, service in services:
    try:
        status = service.is_healthy()
        print(f'{name}: {'✓' if status else '✗'}')
    except Exception as e:
        print(f'{name}: ERROR - {e}')
"
```

## Performance Issues

### Memory Usage Issues
```bash
# Check memory usage
python3 -c "
import psutil
import os

process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f'Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB')
print(f'Virtual memory: {memory_info.vms / 1024 / 1024:.2f} MB')
"

# Check memory leaks
python3 -c "
from claude_pm.services.memory_service import get_memory_service
import gc

# Force garbage collection
gc.collect()
print('Garbage collected')

# Check memory service stats
ms = get_memory_service()
print('Memory service stats:', ms.stats)
"
```

### CPU Usage Issues
```bash
# Check CPU usage
top -p $(pgrep -f claude_pm)

# Profile CPU usage
python3 -c "
import cProfile
import pstats
from claude_pm.services.health_monitor import HealthMonitorService

# Profile health check
cProfile.run('HealthMonitorService()._health_check()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(10)
"
```

### Network Performance Issues
```bash
# Check network latency
ping -c 5 localhost

# Test memory service response time
time curl -s http://localhost:8002/health

# Check connection pool performance
python3 -c "
from claude_pm.services.memory_service import get_memory_service
import time

ms = get_memory_service()
start = time.time()
for i in range(10):
    ms.client.is_connected()
end = time.time()
print(f'Average connection check time: {(end - start) / 10:.3f}s')
"
```

## Configuration Problems

### Configuration File Issues
```bash
# Validate all configuration files
find config/ -name "*.json" -exec sh -c 'echo "Checking $1:"; python3 -m json.tool "$1" > /dev/null && echo "✓ Valid" || echo "✗ Invalid"' _ {} \;

# Check for missing configuration
python3 -c "
from claude_pm.core.config import Config
config = Config()
required_keys = ['memory_service_host', 'memory_service_port', 'ai_trackdown_enabled']
for key in required_keys:
    value = config.get(key)
    print(f'{key}: {value if value is not None else 'MISSING'}')
"
```

### Environment Variable Issues
```bash
# Check environment variables
env | grep CLAUDE_PM

# Set required environment variables
export CLAUDE_PM_MEMORY_HOST=localhost
export CLAUDE_PM_MEMORY_PORT=8002
export CLAUDE_PM_AI_TRACKDOWN_ENABLED=true

# Validate environment
python3 -c "
import os
required_vars = ['CLAUDE_PM_MEMORY_HOST', 'CLAUDE_PM_MEMORY_PORT']
for var in required_vars:
    value = os.getenv(var)
    print(f'{var}: {value if value else 'NOT SET'}')
"
```

## Emergency Procedures

### Complete System Recovery
```bash
# 1. Create emergency backup
tar -czf emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz /Users/masa/Projects/claude-multiagent-pm

# 2. Stop all processes
pkill -f claude_pm
pkill -f mem0ai
pkill -f aitrackdown

# 3. Clear all temporary data
rm -rf /tmp/claude_pm_*
rm -rf /tmp/memory_cache/*
rm -rf logs/*.log

# 4. Reinstall dependencies
pip install -r requirements/production.txt
npm install -g @bobmatnyc/ai-trackdown-tools

# 5. Validate installation
python3 -c "import claude_pm; print('Framework accessible')"
aitrackdown --version

# 6. Restart services
python3 -m claude_pm.cli health --restart-services

# 7. Full system validation
./scripts/health-check.sh
```

### Emergency Contacts and Resources
```bash
# Log locations for support
echo "Emergency log collection:"
echo "========================"
echo "1. Health logs: logs/health-*.log"
echo "2. Service logs: logs/*_service.log"
echo "3. Error logs: logs/errors.log"
echo "4. Configuration: config/"
echo "5. System info: uname -a; python3 --version; node --version"

# Create support bundle
tar -czf support_bundle_$(date +%Y%m%d_%H%M%S).tar.gz \
    logs/ \
    config/ \
    --exclude='*.pyc' \
    --exclude='__pycache__'
```

### Rollback Procedures
```bash
# Rollback to previous version
if [ -f "backup/claude-pm-backup.tar.gz" ]; then
    echo "Rolling back to previous version..."
    
    # Stop services
    pkill -f claude_pm
    
    # Backup current state
    mv /Users/masa/Projects/claude-multiagent-pm /Users/masa/Projects/claude-multiagent-pm.failed
    
    # Restore from backup
    tar -xzf backup/claude-pm-backup.tar.gz -C /Users/masa/Projects/
    
    # Restart services
    cd /Users/masa/Projects/claude-multiagent-pm
    ./scripts/health-check.sh
    
    echo "Rollback completed"
else
    echo "No backup available for rollback"
fi
```

---

## Quick Reference

### Essential Commands
```bash
# System health
./scripts/health-check.sh

# Service status
python3 -c "from claude_pm.services.health_monitor import HealthMonitorService; print(HealthMonitorService().get_health_status())"

# Memory service
curl http://localhost:8002/health

# AI trackdown
aitrackdown status

# Component validation
python3 -c "import claude_pm; print('Framework OK')"
```

### Log Files
- Health: `logs/health-monitor.log`
- Memory: `logs/memory_service.log`
- AI Trackdown: `logs/ai_trackdown_health.json`
- System: `logs/health-report.json`

### Configuration
- Health: `config/health_monitoring_config.json`
- Memory: `claude_pm/core/memory_config.py`
- AI Trackdown: `claude_pm/utils/ai_trackdown_tools.py`

### Recovery
1. Stop services: `pkill -f claude_pm`
2. Clear temp: `rm -rf /tmp/claude_pm_*`
3. Restart: `python3 -m claude_pm.cli health --restart-services`
4. Validate: `./scripts/health-check.sh`

This troubleshooting guide provides systematic approaches to diagnosing and resolving issues in the Claude PM Framework. Always start with the quick diagnostic commands and progress through the specific troubleshooting sections as needed.