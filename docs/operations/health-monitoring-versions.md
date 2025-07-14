# Health Monitoring Integration with Subsystem Versions

## Overview

The Claude PM Framework's health monitoring system is deeply integrated with subsystem versioning to provide comprehensive system validation, performance tracking, and version-aware diagnostics. This integration ensures optimal performance while maintaining version compatibility across all framework components.

## Health Monitoring Architecture

### Version-Aware Health Checks

The health monitoring system (HEALTH_VERSION 001) incorporates subsystem version reporting in all health assessments:

```json
{
  "timestamp": "2025-07-14T14:30:25Z",
  "framework_health": {
    "status": "healthy",
    "framework_version": "010",
    "subsystem_versions": {
      "memory": "002",
      "agents": "001", 
      "ticketing": "001",
      "documentation": "001",
      "services": "001",
      "cli": "001",
      "integration": "001",
      "health": "001"
    },
    "version_compatibility": {
      "all_compatible": true,
      "validation_timestamp": "2025-07-14T14:30:25Z",
      "incompatible_subsystems": []
    }
  }
}
```

### Performance Monitoring with Version Context

Health monitoring tracks performance metrics with version correlation:

```json
{
  "performance_metrics": {
    "health_check_duration": "12.5s",
    "improvement_since_v009": "77%",
    "memory_subsystem_v002": {
      "subprocess_isolation": "optimal",
      "heap_utilization": "65%",
      "leak_detection": "active"
    },
    "version_detection_time": "1.2s",
    "compatibility_validation_time": "0.8s"
  }
}
```

## Memory System Integration (MEMORY_VERSION 002)

### Enhanced Memory Monitoring

The Memory subsystem v002 provides advanced health monitoring capabilities:

#### Real-time Memory Tracking

```javascript
// Memory monitor with version awareness
class VersionAwareMemoryMonitor extends MemoryMonitor {
    constructor() {
        super();
        this.memoryVersion = "002";
        this.frameworkVersion = "010";
        this.healthReportingInterval = 5000; // 5 seconds
    }
    
    generateHealthReport() {
        const usage = process.memoryUsage();
        return {
            memory_subsystem_version: this.memoryVersion,
            framework_version: this.frameworkVersion,
            timestamp: new Date().toISOString(),
            heap_metrics: {
                used: Math.round(usage.heapUsed / 1024 / 1024),
                total: Math.round(usage.heapTotal / 1024 / 1024),
                limit: 4096, // 4GB limit for v002
                utilization_percentage: (usage.heapUsed / (4 * 1024 * 1024 * 1024)) * 100
            },
            subprocess_metrics: {
                active_processes: this.state.activeSubprocesses.size,
                max_allowed: this.config.maxSubprocesses,
                total_subprocess_memory: this.calculateSubprocessMemory()
            },
            performance_indicators: {
                circuit_breaker_status: "normal",
                garbage_collection_pressure: this.getGCPressure(),
                memory_leak_indicators: this.detectMemoryLeaks()
            }
        };
    }
}
```

#### Memory Health Commands

```bash
# Monitor memory health with version reporting
npm run memory:health

# Real-time memory monitoring with version context
npm run memory:monitor

# Generate comprehensive memory report
npm run memory:report

# Memory system status with subprocess coordination
npm run memory:status
```

### Subprocess Manager Integration

The enhanced memory system (v002) coordinates subprocess health monitoring:

```javascript
// Subprocess health tracking
class SubprocessHealthManager {
    constructor() {
        this.memoryVersion = "002";
        this.processes = new Map();
        this.healthCheckInterval = 10000; // 10 seconds
    }
    
    monitorSubprocessHealth() {
        setInterval(() => {
            for (const [pid, process] of this.processes) {
                const metrics = this.getProcessMetrics(pid);
                
                if (metrics.memoryUsage > 1.5 * 1024 * 1024 * 1024) { // 1.5GB limit
                    this.logWarning(`Subprocess ${pid} exceeding memory limit`, {
                        memory_version: this.memoryVersion,
                        process_memory: metrics.memoryUsage,
                        limit: 1.5 * 1024 * 1024 * 1024
                    });
                    
                    this.terminateProcess(pid, "memory_limit_exceeded");
                }
            }
        }, this.healthCheckInterval);
    }
}
```

## Health Monitoring Commands with Version Integration

### System Health Commands

```bash
# Comprehensive system health with version validation
npm run monitor:health

# Single health check with detailed version information
npm run monitor:once --verbose

# Health status including subsystem version compatibility
npm run monitor:status

# Generate health reports with version context
npm run monitor:reports

# Monitor alerts with version-specific thresholds
npm run monitor:alerts
```

### Memory-Specific Health Commands

```bash
# Memory health monitoring (MEMORY_VERSION 002)
npm run memory:health

# Memory optimization with health reporting
npm run memory:optimize

# Memory leak detection with version context
npm run memory:leak-detect

# Process health management
npm run monitor:health-manager

# Memory history tracking
npm run monitor:history-tracking
```

## Automated Health Monitoring

### Health Check Configuration

The automated health monitor integrates version checking:

```javascript
// scripts/automated-health-monitor.js
class AutomatedHealthMonitor {
    constructor() {
        this.config = {
            healthCheckInterval: 60000, // 1 minute
            versionValidationInterval: 300000, // 5 minutes
            memoryThresholds: {
                v002: {
                    warning: 70, // 70% for memory v002
                    critical: 80, // 80% for memory v002
                    circuitBreaker: 85 // 85% circuit breaker
                }
            }
        };
    }
    
    async performVersionAwareHealthCheck() {
        const results = {
            timestamp: new Date().toISOString(),
            health_status: "checking",
            subsystem_health: {}
        };
        
        try {
            // Validate subsystem versions
            const versionResults = await this.validateSubsystemVersions();
            results.version_compatibility = versionResults;
            
            // Memory system health (v002 specific)
            const memoryHealth = await this.checkMemoryHealth();
            results.subsystem_health.memory = memoryHealth;
            
            // Framework health
            const frameworkHealth = await this.checkFrameworkHealth();
            results.subsystem_health.framework = frameworkHealth;
            
            results.health_status = this.determineOverallHealth(results);
            
        } catch (error) {
            results.health_status = "error";
            results.error = error.message;
        }
        
        return results;
    }
}
```

### Performance Optimization Tracking

Health monitoring tracks performance improvements across versions:

```json
{
  "performance_tracking": {
    "framework_009_baseline": {
      "health_check_duration": "50s",
      "memory_detection_time": "5s",
      "subprocess_coordination": "basic"
    },
    "framework_010_memory_002": {
      "health_check_duration": "12.5s",
      "improvement_percentage": "77%",
      "memory_detection_time": "1.2s",
      "subprocess_coordination": "advanced",
      "new_capabilities": [
        "predictive_memory_alerts",
        "subprocess_isolation",
        "circuit_breaker_protection"
      ]
    }
  }
}
```

## Health Report Generation

### Comprehensive Health Reports

```bash
# Generate full health report with version analysis
python -c "
import asyncio
import json
from claude_pm.services.health_monitor import HealthMonitor
from claude_pm.utils.subsystem_versions import SubsystemVersionManager

async def generate_health_report():
    # Initialize services
    health_monitor = HealthMonitor()
    version_manager = SubsystemVersionManager()
    
    # Scan versions
    await version_manager.scan_subsystem_versions()
    
    # Generate comprehensive report
    report = {
        'timestamp': '2025-07-14T14:30:25Z',
        'framework_version': '010',
        'subsystem_versions': dict(version_manager.subsystem_info),
        'health_metrics': await health_monitor.get_comprehensive_health(),
        'performance_optimization': {
            'memory_v002_enhancements': True,
            'subprocess_coordination': True,
            'health_check_speed': '77% improvement'
        }
    }
    
    print(json.dumps(report, indent=2))

asyncio.run(generate_health_report())
"
```

### Alerting with Version Context

```javascript
// Version-aware alerting system
class VersionAwareAlerting {
    constructor() {
        this.alertThresholds = {
            memory_v002: {
                heap_usage: 80,
                subprocess_count: 2,
                gc_pressure: 70
            },
            framework_010: {
                health_check_duration: 15000, // 15 seconds
                compatibility_failures: 0
            }
        };
    }
    
    generateAlert(metric, value, subsystem, version) {
        const threshold = this.alertThresholds[`${subsystem}_v${version}`];
        
        if (value > threshold[metric]) {
            return {
                alert_type: "version_specific_threshold_exceeded",
                subsystem: subsystem,
                version: version,
                metric: metric,
                value: value,
                threshold: threshold[metric],
                timestamp: new Date().toISOString(),
                recommended_action: this.getRecommendedAction(subsystem, version, metric)
            };
        }
        
        return null;
    }
}
```

## Integration with CI/CD

### Health Monitoring in Pipelines

```yaml
# .github/workflows/health-monitoring.yml
name: Health Monitoring with Version Validation

on:
  push:
    branches: [ main, develop ]
  schedule:
    - cron: '*/15 * * * *' # Every 15 minutes

jobs:
  health-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm install
    
    - name: Validate subsystem versions
      run: |
        python -m claude_pm.cli validate-versions --detailed
    
    - name: Run health monitoring
      run: |
        npm run monitor:once --verbose
    
    - name: Memory system health check
      run: |
        npm run memory:health
    
    - name: Generate health report
      run: |
        npm run monitor:reports > health-report.json
    
    - name: Upload health artifacts
      uses: actions/upload-artifact@v3
      with:
        name: health-reports
        path: |
          health-report.json
          logs/memory-usage-*.json
```

## Troubleshooting with Health Integration

### Version-Specific Health Issues

```bash
# Diagnose memory system (v002) issues
npm run memory:monitor &
MONITOR_PID=$!

# Check subprocess coordination
ps aux | grep memory
netstat -tulpn | grep 8002

# Validate memory thresholds
node -e "
const monitor = require('./scripts/memory-monitor.js');
console.log('Memory thresholds for v002:');
console.log(JSON.stringify(monitor.config, null, 2));
"

# Stop monitoring
kill $MONITOR_PID
```

### Health History Analysis

```bash
# Analyze health trends across versions
python -c "
import json
from pathlib import Path

# Load health history
history_files = list(Path('logs').glob('health-*.json'))
history_files.sort()

for file in history_files[-5:]:  # Last 5 health reports
    with open(file) as f:
        data = json.load(f)
    
    print(f'Report: {file.name}')
    print(f'Framework: {data.get(\"framework_version\", \"unknown\")}')
    print(f'Memory Version: {data.get(\"subsystem_versions\", {}).get(\"memory\", \"unknown\")}')
    print(f'Health Duration: {data.get(\"performance_metrics\", {}).get(\"health_check_duration\", \"unknown\")}')
    print('---')
"
```

## Best Practices for Health Monitoring Integration

### Development Guidelines

1. **Version-Aware Monitoring**: Always include version context in health metrics
2. **Performance Tracking**: Monitor performance improvements across versions
3. **Threshold Management**: Adjust health thresholds based on subsystem versions
4. **Alert Correlation**: Correlate alerts with specific subsystem versions
5. **Historical Analysis**: Track health trends across version changes

### Operational Guidelines

1. **Regular Validation**: Perform version validation as part of health checks
2. **Memory Monitoring**: Continuously monitor memory subsystem v002 performance
3. **Subprocess Tracking**: Monitor subprocess coordination and isolation
4. **Performance Baselines**: Maintain performance baselines for each version
5. **Incident Response**: Include version information in incident reports

### Monitoring Standards

1. **Health Check Frequency**: Monitor health every 5 seconds for critical systems
2. **Version Validation**: Validate compatibility every 5 minutes
3. **Performance Tracking**: Track health check duration improvements
4. **Memory Limits**: Enforce 4GB heap and 1.5GB subprocess limits
5. **Circuit Breaker**: Implement automatic process termination at 85% memory usage

This comprehensive health monitoring integration ensures that subsystem versions are properly tracked, validated, and optimized across the entire Claude PM Framework lifecycle.