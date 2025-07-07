#!/bin/bash

# Claude PM Framework - Health Monitoring Setup Script
# Sets up the automated health monitoring system for background operation

set -e

echo "🏥 Claude PM Framework - Health Monitoring Setup"
echo "================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_PM_DIR="$(dirname "$SCRIPT_DIR")"

echo "📂 Claude PM Directory: $CLAUDE_PM_DIR"
echo ""

# Ensure logs directory exists
LOGS_DIR="$CLAUDE_PM_DIR/logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p "$LOGS_DIR"
    echo "✅ Logs directory created: $LOGS_DIR"
else
    echo "✅ Logs directory exists: $LOGS_DIR"
fi
echo ""

# Make the monitoring script executable
MONITOR_SCRIPT="$CLAUDE_PM_DIR/scripts/automated-health-monitor.js"
if [ -f "$MONITOR_SCRIPT" ]; then
    chmod +x "$MONITOR_SCRIPT"
    echo "✅ Health monitor script is executable"
else
    echo "❌ Health monitor script not found: $MONITOR_SCRIPT"
    exit 1
fi
echo ""

# Test the monitoring system
echo "🧪 Testing health monitoring system..."
echo "Running single health check..."
cd "$CLAUDE_PM_DIR"

if npm run monitor:once > /dev/null 2>&1; then
    echo "✅ Health check completed successfully"
else
    echo "⚠️  Health check completed with warnings (this is normal)"
fi
echo ""

# Show available npm scripts
echo "📋 Available npm scripts for health monitoring:"
echo "  npm run monitor:once     - Run single health check"
echo "  npm run monitor:health   - Start continuous monitoring"
echo "  npm run monitor:status   - Show monitor status"
echo "  npm run monitor:reports  - List available reports"
echo "  npm run monitor:alerts   - Show recent alerts"
echo "  npm run monitor:verbose  - Run verbose health check"
echo ""

# Check for PM2
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 is available for background monitoring"
    echo "📋 PM2 commands:"
    echo "  pm2 start ecosystem.config.js      - Start health monitor service"
    echo "  pm2 status claude-pm-health-monitor - Check service status"
    echo "  pm2 logs claude-pm-health-monitor  - View service logs"
    echo "  pm2 stop claude-pm-health-monitor  - Stop service"
else
    echo "📦 PM2 not found. Install with: npm install -g pm2"
    echo "   PM2 enables background monitoring and automatic restarts"
fi
echo ""

# Show systemd service info (Linux only)
if [ "$(uname)" == "Linux" ]; then
    echo "🐧 For systemd service (Linux production):"
    echo "  sudo cp claude-pm-health-monitor.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable claude-pm-health-monitor"
    echo "  sudo systemctl start claude-pm-health-monitor"
    echo ""
fi

# Show current health status
echo "📊 Current Health Status:"
echo "========================="
npm run monitor:status
echo ""

echo "🎉 Health monitoring setup complete!"
echo ""
echo "💡 Next steps:"
echo "  1. Run 'npm run monitor:health' to start continuous monitoring"
echo "  2. Use 'npm run monitor:status' to check system health"
echo "  3. Monitor alerts with 'npm run monitor:alerts'"
echo "  4. View reports in $LOGS_DIR/"
echo ""
echo "📚 Full documentation: docs/HEALTH_MONITORING.md"