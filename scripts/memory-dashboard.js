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