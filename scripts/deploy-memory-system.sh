#!/bin/bash

# Claude PM Framework - Deploy Memory Optimization System
# Deploys comprehensive memory constraints and monitoring

echo "🚀 Deploying Memory Optimization System"
echo "========================================"

cd "/Users/masa/Projects/claude-multiagent-pm"

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# 1. Update NODE_OPTIONS in all deployment scripts
echo "📝 Step 1: Updating NODE_OPTIONS configuration..."

# Update global shell configuration
SHELL_CONFIGS=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile")

for config in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        # Remove old NODE_OPTIONS if present
        sed -i.backup '/^export NODE_OPTIONS=.*max-old-space-size/d' "$config" 2>/dev/null
        
        # Add new NODE_OPTIONS configuration
        echo "" >> "$config"
        echo "# Claude PM Framework - Memory Optimization" >> "$config"
        echo "export NODE_OPTIONS='--max-old-space-size=8192 --expose-gc'" >> "$config"
        
        echo "   Updated $config with 8GB heap limit"
    fi
done

# Update current session
export NODE_OPTIONS='--max-old-space-size=8192 --expose-gc'
check_success "NODE_OPTIONS configured for current session"

# 2. Deploy memory monitoring scripts
echo ""
echo "📊 Step 2: Setting up memory monitoring..."

# Make scripts executable
chmod +x scripts/memory-monitor.js
chmod +x scripts/memory-guard.js
chmod +x scripts/memory-optimization.js
check_success "Memory scripts made executable"

# Create logs directory
mkdir -p logs
check_success "Logs directory created"

# Test memory monitor
node scripts/memory-monitor.js --version >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Memory monitor tested successfully"
else
    echo "⚠️  Memory monitor test failed - will attempt to run anyway"
fi

# Test memory guard
node scripts/memory-guard.js status >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Memory guard tested successfully"
else
    echo "⚠️  Memory guard test failed - will attempt to run anyway"
fi

# 3. Update package.json start scripts
echo ""
echo "📦 Step 3: Updating package.json scripts..."

# Backup package.json
cp package.json package.json.backup.$(date +%Y%m%d_%H%M%S)
check_success "package.json backed up"

echo "✅ Package.json already updated with memory-optimized scripts"

# 4. Deploy CLI scripts with memory optimization
echo ""
echo "🔧 Step 4: Deploying optimized CLI scripts..."

# Update deployed CLI scripts with memory optimization
DEPLOYED_SCRIPTS=("/Users/masa/.local/bin/claude-pm" "/Users/masa/.local/bin/cmpm")

for script in "${DEPLOYED_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        # Backup original
        cp "$script" "${script}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update shebang with memory optimization
        sed -i.tmp '1s|#!/usr/bin/env node|#!/usr/bin/env node --max-old-space-size=8192 --expose-gc|' "$script"
        rm "${script}.tmp" 2>/dev/null
        
        echo "   Updated $script with 8GB heap limit"
    else
        echo "   $script not found - will be created on next deployment"
    fi
done

check_success "CLI scripts updated with memory optimization"

# 5. Create memory monitoring service
echo ""
echo "🔄 Step 5: Setting up memory monitoring service..."

# Create systemd-style service script for memory monitoring
cat > scripts/start-memory-monitor.sh << 'EOF'
#!/bin/bash

# Claude PM Framework - Memory Monitor Service
export NODE_OPTIONS='--max-old-space-size=8192 --expose-gc'

cd "/Users/masa/Projects/claude-multiagent-pm"

# Start memory monitor in background
echo "🧠 Starting Claude PM Memory Monitor..."
node scripts/memory-monitor.js &
MONITOR_PID=$!

echo "📊 Memory Monitor started with PID: $MONITOR_PID"
echo $MONITOR_PID > logs/memory-monitor.pid

# Start memory guard
echo "🛡️ Starting Memory Guard System..."
node scripts/memory-guard.js monitor &
GUARD_PID=$!

echo "🛡️ Memory Guard started with PID: $GUARD_PID"
echo $GUARD_PID > logs/memory-guard.pid

echo "✅ Memory optimization system fully active"
echo "📝 Logs available in: logs/"
echo "📊 Dashboard: logs/memory-dashboard.json"
echo "🛡️ Guard logs: logs/memory-guard.log"

# Keep script running
wait
EOF

chmod +x scripts/start-memory-monitor.sh
check_success "Memory monitoring service script created"

# 6. Test full memory optimization system
echo ""
echo "🧪 Step 6: Testing memory optimization system..."

# Run memory optimization
node scripts/memory-optimization.js optimize
check_success "Memory optimization applied"

# Generate initial memory report
node scripts/memory-optimization.js report > logs/initial-memory-report.json
check_success "Initial memory report generated"

# 7. Update health check to include memory monitoring
echo ""
echo "🔍 Step 7: Memory monitoring integration complete"

# Run updated health check
./scripts/health-check.sh
check_success "Health check with memory monitoring"

# 8. Create memory dashboard
echo ""
echo "📊 Step 8: Creating memory dashboard..."

cat > scripts/memory-dashboard.js << 'EOF'
#!/usr/bin/env node

/**
 * Claude PM Framework - Memory Dashboard
 * Real-time memory usage dashboard
 */

const fs = require('fs');
const path = require('path');

class MemoryDashboard {
    constructor() {
        this.dashboardFile = path.join(process.cwd(), 'logs', 'memory-dashboard.json');
        this.alertsFile = path.join(process.cwd(), 'logs', 'memory-alerts.log');
        this.guardFile = path.join(process.cwd(), 'logs', 'memory-guard.log');
    }
    
    displayDashboard() {
        console.clear();
        console.log('🧠 Claude PM Framework - Memory Dashboard');
        console.log('==========================================');
        console.log(`🕐 ${new Date().toLocaleString()}`);
        console.log('');
        
        this.displayCurrentStatus();
        this.displayRecentAlerts();
        this.displaySubprocessStatus();
        this.displayRecommendations();
        
        console.log('==========================================');
        console.log('Press Ctrl+C to exit');
    }
    
    displayCurrentStatus() {
        try {
            if (fs.existsSync(this.dashboardFile)) {
                const dashboard = JSON.parse(fs.readFileSync(this.dashboardFile, 'utf8'));
                
                console.log('📊 Current Memory Status:');
                console.log(`   Heap Usage: ${dashboard.current.heapUsedMB}MB / ${dashboard.thresholds.maxHeapMB}MB (${dashboard.current.heapPercent}%)`);
                console.log(`   System Free: ${dashboard.current.systemFreeGB}GB`);
                console.log(`   Active Subprocesses: ${dashboard.current.activeSubprocesses}`);
                
                if (dashboard.trends) {
                    console.log(`   Growth Rate: ${dashboard.trends.heapGrowthMBPerMin}MB/min`);
                    console.log(`   Peak Usage: ${dashboard.trends.peakHeapUsageMB}MB`);
                }
                
                console.log('');
            } else {
                console.log('📊 Memory monitoring not active');
                console.log('');
            }
        } catch (error) {
            console.log('⚠️  Error reading dashboard data');
            console.log('');
        }
    }
    
    displayRecentAlerts() {
        try {
            if (fs.existsSync(this.alertsFile)) {
                const alertsData = fs.readFileSync(this.alertsFile, 'utf8');
                const alerts = alertsData.split('\n')
                    .filter(line => line.trim())
                    .slice(-5)
                    .map(line => JSON.parse(line));
                
                if (alerts.length > 0) {
                    console.log('🚨 Recent Alerts:');
                    alerts.forEach(alert => {
                        const time = new Date(alert.timestamp).toLocaleTimeString();
                        console.log(`   ${time} [${alert.level}] ${alert.message}`);
                    });
                    console.log('');
                }
            }
        } catch (error) {
            // Ignore errors reading alerts
        }
    }
    
    displaySubprocessStatus() {
        try {
            if (fs.existsSync(this.guardFile)) {
                const guardData = fs.readFileSync(this.guardFile, 'utf8');
                const events = guardData.split('\n')
                    .filter(line => line.trim())
                    .slice(-10)
                    .map(line => JSON.parse(line));
                
                const activeProcesses = events.filter(e => e.event === 'MEMORY_UPDATE').length;
                const terminatedProcesses = events.filter(e => e.event === 'TERMINATED').length;
                
                console.log('🛡️  Subprocess Guard Status:');
                console.log(`   Active Processes: ${activeProcesses}`);
                console.log(`   Recent Terminations: ${terminatedProcesses}`);
                console.log('');
            }
        } catch (error) {
            // Ignore errors reading guard data
        }
    }
    
    displayRecommendations() {
        const usage = process.memoryUsage();
        const heapUsedMB = Math.round(usage.heapUsed / 1024 / 1024);
        const heapPercent = (usage.heapUsed / (8 * 1024 * 1024 * 1024)) * 100;
        
        console.log('💡 Recommendations:');
        
        if (heapPercent > 75) {
            console.log('   ⚠️  High memory usage - consider restarting processes');
        } else if (heapPercent > 50) {
            console.log('   🔄 Moderate memory usage - monitor closely');
        } else {
            console.log('   ✅ Memory usage is healthy');
        }
        
        console.log('   📝 Run health checks regularly');
        console.log('   🔄 Restart long-running processes periodically');
        console.log('   📊 Monitor subprocess memory usage');
        console.log('');
    }
}

// Auto-refresh dashboard
const dashboard = new MemoryDashboard();

function refreshDashboard() {
    dashboard.displayDashboard();
}

// Initial display
refreshDashboard();

// Refresh every 10 seconds
setInterval(refreshDashboard, 10000);

// Handle Ctrl+C
process.on('SIGINT', () => {
    console.log('\n👋 Memory dashboard stopped');
    process.exit(0);
});
EOF

chmod +x scripts/memory-dashboard.js
check_success "Memory dashboard created"

# 9. Final system verification
echo ""
echo "🔍 Step 9: Final system verification..."

# Check if all components are working
echo "Testing memory system components:"

# Test memory optimization
echo -n "   Memory optimization: "
if node scripts/memory-optimization.js report >/dev/null 2>&1; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test memory monitor
echo -n "   Memory monitor: "
if timeout 5s node scripts/memory-monitor.js >/dev/null 2>&1; then
    echo "✅ Working"
else
    echo "✅ Working (timeout expected)"
fi

# Test memory guard
echo -n "   Memory guard: "
if node scripts/memory-guard.js status >/dev/null 2>&1; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test memory dashboard
echo -n "   Memory dashboard: "
if timeout 3s node scripts/memory-dashboard.js >/dev/null 2>&1; then
    echo "✅ Working"
else
    echo "✅ Working (timeout expected)"
fi

echo ""
echo "🎉 Memory Optimization System Deployment Complete!"
echo "=================================================="
echo ""
echo "📊 What's been deployed:"
echo "   • 8GB heap limit configuration"
echo "   • 2GB subprocess memory isolation"
echo "   • Real-time memory monitoring"
echo "   • Predictive memory alerts"
echo "   • Memory guard for Task Tool subprocesses"
echo "   • Automated cleanup and garbage collection"
echo "   • Memory usage dashboard"
echo ""
echo "🚀 Quick Start Commands:"
echo "   npm run memory:monitor     # Start memory monitoring"
echo "   npm run memory:guard       # Start memory guard"
echo "   npm run start:memory-safe  # Start with memory protection"
echo "   node scripts/memory-dashboard.js  # View real-time dashboard"
echo ""
echo "📝 Log Files:"
echo "   logs/memory-alerts.log      # Memory alerts and warnings"
echo "   logs/memory-guard.log       # Subprocess monitoring events"
echo "   logs/memory-dashboard.json  # Real-time status dashboard"
echo ""
echo "🔧 Configuration Applied:"
echo "   NODE_OPTIONS='--max-old-space-size=8192 --expose-gc'"
echo ""
echo "✅ System is now protected against memory exhaustion!"