# Health Monitoring System (M01-006)

## Quick Start

The Claude Multi-Agent PM Framework includes a comprehensive automated health monitoring system that tracks project health, service availability, framework compliance, and generates intelligent alerts.

### Basic Usage

```bash
# Run single health check
claude-multiagent-pm health check

# Start continuous monitoring 
claude-multiagent-pm health monitor

# Check current status
claude-multiagent-pm health status

# View recent alerts
claude-multiagent-pm health alerts

# Setup monitoring system
npm run monitor:setup
```

### Key Features

- **🔍 Service Monitoring**: Track mem0AI MCP (port 8002), Portfolio Manager (port 3000), and other services
- **📋 Framework Compliance**: Validate CLAUDE.md files, TrackDown system, and project structure
- **📊 Project Health**: Monitor all managed projects in `~/Projects/managed/`
- **🚨 Intelligent Alerts**: Critical issue detection with configurable thresholds
- **📈 Performance Metrics**: Response time tracking and health scoring
- **🔄 Background Monitoring**: PM2/systemd compatible continuous monitoring

### Monitoring Outputs

The system generates comprehensive reports in `~/Projects/Claude-PM/logs/`:

- **health-report.json**: Detailed JSON report with all metrics
- **health-summary.md**: Human-readable markdown summary  
- **health-monitor.log**: Monitoring activity logs
- **health-alerts.log**: Critical alerts and warnings

### Background Service

For continuous monitoring, use PM2:

```bash
# Start background monitoring service
pm2 start ecosystem.config.js

# View status and logs
pm2 status claude-pm-health-monitor
pm2 logs claude-pm-health-monitor
```

### Health Scoring

The system calculates an overall health score based on:
- **Project Health (40%)**: Percentage of healthy projects
- **Service Health (35%)**: Percentage of healthy services  
- **Framework Compliance (25%)**: Structure and documentation compliance

### Configuration

Customize monitoring with command-line options:

```bash
# Custom interval and threshold
node scripts/automated-health-monitor.js monitor --interval=10 --threshold=70

# Verbose output
npm run monitor:verbose

# Skip certain checks
node scripts/automated-health-monitor.js once --no-services --no-git
```

## Complete Documentation

For full documentation, setup instructions, and advanced configuration:
- **[Health Monitoring Guide](docs/HEALTH_MONITORING.md)** - Complete setup and usage guide
- **[Sample Reports](docs/SAMPLE_HEALTH_REPORT.md)** - Example outputs and report structures

## Integration with Existing Tools

The enhanced monitoring system works alongside existing Claude PM tools:

```bash
# Traditional bash health check
npm run health-check

# Enhanced automated monitoring  
npm run monitor:once

# Both provide complementary insights
```

The automated health monitor provides deeper insights, alerting capabilities, and background monitoring while the traditional health check offers quick framework validation.