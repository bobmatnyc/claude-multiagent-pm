# Claude PM Framework Health Monitoring System (M01-006)

## Overview

The Enhanced Automated Health Monitor provides comprehensive monitoring for the Claude PM Framework, tracking project health, service availability, framework compliance, and generating intelligent alerts and recommendations.

## Features

### Core Monitoring Capabilities
- **Service Availability**: Monitor mem0AI MCP (port 8002), Portfolio Manager (port 3000), Git Portfolio Manager (port 3001), and Claude PM Dashboard (port 5173)
- **Framework Compliance**: Validate CLAUDE.md files, TrackDown system, required directories and files
- **Project Health Assessment**: Monitor all managed projects in `~/Projects/managed/`
- **Git Repository Health**: Track commit activity, branch status, and repository health
- **Performance Metrics**: Response time tracking and performance rating
- **Intelligent Alerting**: Critical issue detection with configurable thresholds

### Enhanced Features (v2.0.0)
- **Background Monitoring**: PM2/systemd compatible continuous monitoring
- **Advanced Metrics**: Overall health scoring with weighted calculations
- **Alert Management**: Separate alert logging and threshold-based notifications
- **Status Tracking**: Monitor uptime, check counts, and alert statistics
- **Comprehensive Reporting**: JSON and Markdown reports with detailed insights

## Installation & Setup

### Using NPM Scripts (Recommended)

```bash
# Run single health check
npm run monitor:once

# Start continuous monitoring (5-minute intervals)
npm run monitor:health

# Check monitor status and latest health summary
npm run monitor:status

# View available reports
npm run monitor:reports

# Show recent alerts
npm run monitor:alerts

# Run verbose single check
npm run monitor:verbose

# Start background monitoring (10-minute intervals)
npm run monitor:background
```

### Direct Script Usage

```bash
# Single health check with verbose output
node scripts/automated-health-monitor.js once --verbose

# Continuous monitoring with custom settings
node scripts/automated-health-monitor.js monitor --interval=10 --threshold=70

# Status check
node scripts/automated-health-monitor.js status

# List reports
node scripts/automated-health-monitor.js reports

# Show alerts
node scripts/automated-health-monitor.js alerts
```

### Background Service Setup

#### Using PM2 (Recommended for Development)

```bash
# Install PM2 globally if not already installed
npm install -g pm2

# Start the health monitor service
pm2 start ecosystem.config.js

# Check service status
pm2 status claude-pm-health-monitor

# View logs
pm2 logs claude-pm-health-monitor

# Stop the service
pm2 stop claude-pm-health-monitor

# Restart the service
pm2 restart claude-pm-health-monitor

# Auto-start on system reboot
pm2 startup
pm2 save
```

#### Using systemd (Production Linux Systems)

```bash
# Copy service file to systemd directory
sudo cp claude-pm-health-monitor.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable claude-pm-health-monitor

# Start the service
sudo systemctl start claude-pm-health-monitor

# Check status
sudo systemctl status claude-pm-health-monitor

# View logs
journalctl -u claude-pm-health-monitor -f
```

## Configuration Options

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose, -v` | Enable verbose logging | false |
| `--no-alerts` | Disable alert notifications | false |
| `--no-services` | Skip service health checks | false |
| `--no-git` | Skip git repository checks | false |
| `--interval=<minutes>` | Set monitoring interval | 5 |
| `--threshold=<percentage>` | Set alert threshold | 60 |

### Examples

```bash
# Verbose single check
npm run monitor:once -- --verbose

# Custom monitoring interval and threshold
node scripts/automated-health-monitor.js monitor --interval=15 --threshold=80

# Skip service checks (useful for offline development)
node scripts/automated-health-monitor.js once --no-services

# Disable alerts
node scripts/automated-health-monitor.js monitor --no-alerts
```

## Output Files

The monitoring system generates several output files in `~/Projects/Claude-PM/logs/`:

### Core Reports
- **`health-report.json`**: Comprehensive JSON report with all metrics
- **`health-summary.md`**: Human-readable markdown summary
- **`health-monitor.log`**: Detailed monitoring logs
- **`monitor-status.json`**: Monitor process status and statistics

### Alert and Error Logs
- **`health-alerts.log`**: Critical alerts and warnings
- **`health-monitor-error.log`**: PM2 error logs (if using PM2)
- **`health-monitor-out.log`**: PM2 output logs (if using PM2)
- **`health-monitor-combined.log`**: PM2 combined logs (if using PM2)

## Monitoring Metrics

### Overall Health Score
The system calculates a weighted overall health score based on:
- **Project Health (40%)**: Percentage of healthy projects
- **Service Health (35%)**: Percentage of healthy services
- **Framework Compliance (25%)**: Framework structure compliance

### Project Health Criteria
For each project, the system checks:
- **Required Files**: CLAUDE.md, README.md (70% of score)
- **Recommended Files**: trackdown/BACKLOG.md, docs/INSTRUCTIONS.md, package.json (30% of score)
- **Git Activity**: Recent commits and repository health
- **Build Configuration**: Presence of build/dependency files

### Service Health Monitoring
For each service, the system monitors:
- **Port Availability**: Check if service port is listening
- **HTTP Response**: Validate service endpoint responses
- **Response Time**: Track performance metrics
- **Process Status**: Check service process health (where applicable)

### Framework Compliance
The system validates:
- **Required Files**: trackdown/BACKLOG.md, CLAUDE.md, README.md, package.json
- **Required Directories**: trackdown/, docs/, scripts/, logs/
- **Optional Files**: Additional documentation and configuration files
- **TrackDown Health**: Ticket analysis and activity tracking

## Alert System

### Alert Levels
- **Critical**: Immediate attention required (critical services down, health < threshold)
- **Warning**: Issues that should be addressed (framework compliance issues)
- **Info**: General notifications and status updates

### Alert Triggers
- Overall health below configured threshold (default 60%)
- Critical services unavailable or unhealthy
- Framework compliance below 50%
- Critical projects with multiple issues
- Service response times degraded

### Alert Management
```bash
# View recent alerts
npm run monitor:alerts

# Check alert count in status
npm run monitor:status

# Disable alerts temporarily
node scripts/automated-health-monitor.js monitor --no-alerts
```

## Integration with Existing Scripts

The health monitor integrates with existing Claude PM scripts:

```bash
# Traditional health check (bash script)
npm run health-check

# Enhanced automated monitoring
npm run monitor:once

# Both can be used together for comprehensive health assessment
```

## Troubleshooting

### Common Issues

#### Monitor Not Starting
```bash
# Check if logs directory exists
ls -la ~/Projects/Claude-PM/logs/

# Create logs directory if missing
mkdir -p ~/Projects/Claude-PM/logs/

# Check for permission issues
chmod 755 ~/Projects/Claude-PM/scripts/automated-health-monitor.js
```

#### Service Checks Failing
```bash
# Test individual service endpoints
curl http://localhost:8002/health  # mem0AI MCP
curl http://localhost:3000/        # Portfolio Manager
curl http://localhost:3001/health  # Git Portfolio Manager

# Skip service checks if services are not running
npm run monitor:once -- --no-services
```

#### High Alert Volume
```bash
# Increase alert threshold to reduce sensitivity
node scripts/automated-health-monitor.js monitor --threshold=80

# Disable alerts temporarily
node scripts/automated-health-monitor.js monitor --no-alerts
```

### Debug Mode
```bash
# Run with verbose logging for debugging
npm run monitor:verbose

# Check monitor status
npm run monitor:status

# View detailed logs
tail -f ~/Projects/Claude-PM/logs/health-monitor.log
```

## Best Practices

### Development Environment
- Use PM2 for background monitoring during development
- Set appropriate check intervals (5-10 minutes for active development)
- Enable verbose logging for troubleshooting
- Monitor alerts to catch issues early

### Production Environment
- Use systemd for production deployments
- Set conservative alert thresholds to avoid false positives
- Monitor logs regularly for performance insights
- Set up log rotation for long-running monitors

### Performance Optimization
- Adjust check intervals based on system load
- Disable unnecessary checks (--no-git, --no-services) when not needed
- Monitor memory usage for long-running processes
- Use PM2 memory restart limits to prevent memory leaks

## API Integration

The health monitor can be integrated into other systems:

```javascript
const ClaudePMHealthMonitor = require('./scripts/automated-health-monitor.js');

// Create monitor instance
const monitor = new ClaudePMHealthMonitor({
  interval: 300000,     // 5 minutes
  alertThreshold: 60,   // 60%
  enableAlerting: true,
  verbose: false
});

// Run single check
await monitor.runHealthCheck();

// Access health report
console.log(monitor.healthReport);

// Start continuous monitoring
monitor.startContinuousMonitoring();
```

## Changelog

### v2.0.0 (M01-006 Implementation)
- Enhanced service monitoring with port checking and performance metrics
- Comprehensive framework compliance validation
- Managed projects health assessment
- Intelligent alerting system with configurable thresholds
- Background monitoring with PM2/systemd support
- Advanced health scoring with weighted calculations
- Status tracking and alert management
- Comprehensive CLI interface with multiple commands
- Integration with npm scripts for easy access

### v1.0.0 (Initial Implementation)
- Basic health checking functionality
- Service availability monitoring
- Framework structure validation
- Project health assessment
- Simple reporting system

---

For more information about the Claude PM Framework, see the [main documentation](../README.md) and [TrackDown system](../trackdown/README.md).