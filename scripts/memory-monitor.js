#!/usr/bin/env node

/**
 * Claude PM Framework - Real-time Memory Monitor with Predictive Alerts
 * 
 * Advanced memory monitoring system with 8GB heap management and subprocess isolation
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class MemoryMonitor {
    constructor() {
        this.config = {
            maxHeapSize: 8 * 1024 * 1024 * 1024,      // 8GB total heap
            subprocessLimit: 2 * 1024 * 1024 * 1024,  // 2GB per subprocess
            criticalThreshold: 0.85,                   // 85% of max heap
            warningThreshold: 0.75,                    // 75% of max heap
            monitorInterval: 5000,                     // 5 second intervals
            alertCooldown: 30000,                      // 30 second alert cooldown
            maxSubprocesses: 4                         // Maximum concurrent subprocesses
        };
        
        this.state = {
            activeSubprocesses: new Map(),
            lastAlert: 0,
            alertCount: 0,
            monitoringStarted: Date.now(),
            memoryHistory: [],
            predictions: []
        };
        
        this.setupMonitoring();
    }
    
    setupMonitoring() {
        console.log('🧠 Claude PM Memory Monitor - Starting Advanced Monitoring');
        console.log(`📊 Configuration:`);
        console.log(`   Max Heap: ${Math.round(this.config.maxHeapSize / 1024 / 1024 / 1024)}GB`);
        console.log(`   Subprocess Limit: ${Math.round(this.config.subprocessLimit / 1024 / 1024 / 1024)}GB`);
        console.log(`   Max Concurrent Subprocesses: ${this.config.maxSubprocesses}`);
        console.log(`   Monitor Interval: ${this.config.monitorInterval}ms`);
        
        this.startRealTimeMonitoring();
        this.setupSignalHandlers();
        this.initializeDashboard();
    }
    
    startRealTimeMonitoring() {
        this.monitoringInterval = setInterval(() => {
            this.performMemoryCheck();
        }, this.config.monitorInterval);
        
        // Additional subprocess monitoring
        this.subprocessInterval = setInterval(() => {
            this.monitorSubprocesses();
        }, this.config.monitorInterval * 2);
        
        console.log('✅ Real-time monitoring active');
    }
    
    performMemoryCheck() {
        const usage = process.memoryUsage();
        const systemMem = this.getSystemMemoryInfo();
        const timestamp = Date.now();
        
        const memorySnapshot = {
            timestamp,
            heapUsed: usage.heapUsed,
            heapTotal: usage.heapTotal,
            external: usage.external,
            rss: usage.rss,
            systemFree: systemMem.free,
            systemTotal: systemMem.total,
            subprocessCount: this.state.activeSubprocesses.size
        };
        
        this.state.memoryHistory.push(memorySnapshot);
        
        // Keep only last 100 snapshots for predictions
        if (this.state.memoryHistory.length > 100) {
            this.state.memoryHistory = this.state.memoryHistory.slice(-100);
        }
        
        this.analyzeMemoryTrends(memorySnapshot);
        this.checkThresholds(memorySnapshot);
        this.updateDashboard(memorySnapshot);
    }
    
    analyzeMemoryTrends(current) {
        if (this.state.memoryHistory.length < 10) return;
        
        const recent = this.state.memoryHistory.slice(-10);
        const growthRate = this.calculateGrowthRate(recent);
        const predictedUsage = this.predictMemoryUsage(current, growthRate);
        
        this.state.predictions.push({
            timestamp: current.timestamp,
            currentUsage: current.heapUsed,
            growthRate,
            predictedUsageIn60s: predictedUsage.in60s,
            predictedUsageIn300s: predictedUsage.in300s,
            timeToLimit: predictedUsage.timeToLimit
        });
        
        // Keep only last 20 predictions
        if (this.state.predictions.length > 20) {
            this.state.predictions = this.state.predictions.slice(-20);
        }
        
        this.checkPredictiveAlerts(predictedUsage);
    }
    
    calculateGrowthRate(snapshots) {
        if (snapshots.length < 2) return 0;
        
        const first = snapshots[0];
        const last = snapshots[snapshots.length - 1];
        const timeDiff = last.timestamp - first.timestamp;
        const memoryDiff = last.heapUsed - first.heapUsed;
        
        return timeDiff > 0 ? (memoryDiff / timeDiff) * 1000 : 0; // bytes per second
    }
    
    predictMemoryUsage(current, growthRate) {
        const currentUsage = current.heapUsed;
        const maxSafeUsage = this.config.maxHeapSize * this.config.criticalThreshold;
        
        return {
            in60s: Math.max(0, currentUsage + (growthRate * 60)),
            in300s: Math.max(0, currentUsage + (growthRate * 300)),
            timeToLimit: growthRate > 0 ? Math.round((maxSafeUsage - currentUsage) / growthRate) : Infinity
        };
    }
    
    checkPredictiveAlerts(prediction) {
        const criticalUsage = this.config.maxHeapSize * this.config.criticalThreshold;
        
        if (prediction.timeToLimit < 120 && prediction.timeToLimit > 0) {
            this.triggerPredictiveAlert('CRITICAL', `Memory limit will be reached in ${prediction.timeToLimit}s`);
        } else if (prediction.in60s > criticalUsage) {
            this.triggerPredictiveAlert('WARNING', 'Memory usage trending toward critical levels');
        }
    }
    
    checkThresholds(snapshot) {
        const heapPercent = snapshot.heapUsed / this.config.maxHeapSize;
        const systemPercent = (snapshot.systemTotal - snapshot.systemFree) / snapshot.systemTotal;
        
        if (heapPercent >= this.config.criticalThreshold) {
            this.triggerAlert('CRITICAL', `Heap usage at ${Math.round(heapPercent * 100)}%`);
            this.executeEmergencyCleanup();
        } else if (heapPercent >= this.config.warningThreshold) {
            this.triggerAlert('WARNING', `Heap usage at ${Math.round(heapPercent * 100)}%`);
            this.executeProactiveCleanup();
        }
        
        if (systemPercent >= 0.9) {
            this.triggerAlert('SYSTEM', `System memory at ${Math.round(systemPercent * 100)}%`);
        }
    }
    
    triggerAlert(level, message) {
        const now = Date.now();
        if (now - this.state.lastAlert < this.config.alertCooldown) return;
        
        this.state.lastAlert = now;
        this.state.alertCount++;
        
        const alertSymbol = level === 'CRITICAL' ? '🚨' : level === 'WARNING' ? '⚠️' : '🔔';
        console.log(`${alertSymbol} [${level}] ${message}`);
        
        this.logAlert(level, message);
    }
    
    triggerPredictiveAlert(level, message) {
        const now = Date.now();
        if (now - this.state.lastAlert < this.config.alertCooldown / 2) return;
        
        console.log(`🔮 [PREDICTIVE-${level}] ${message}`);
        this.logAlert(`PREDICTIVE-${level}`, message);
    }
    
    logAlert(level, message) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            memoryUsage: process.memoryUsage(),
            systemMemory: this.getSystemMemoryInfo(),
            activeSubprocesses: this.state.activeSubprocesses.size
        };
        
        const logFile = path.join(process.cwd(), 'logs', 'memory-alerts.log');
        fs.mkdirSync(path.dirname(logFile), { recursive: true });
        fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
    }
    
    executeEmergencyCleanup() {
        console.log('🚨 EMERGENCY CLEANUP INITIATED');
        
        // Force garbage collection multiple times
        if (global.gc) {
            for (let i = 0; i < 5; i++) {
                global.gc();
                console.log(`   Emergency GC pass ${i + 1} completed`);
            }
        }
        
        // Terminate excess subprocesses
        this.terminateExcessSubprocesses();
        
        // Clear caches
        this.clearAllCaches();
        
        const afterUsage = process.memoryUsage();
        console.log(`✅ Emergency cleanup complete - heap: ${Math.round(afterUsage.heapUsed / 1024 / 1024)}MB`);
    }
    
    executeProactiveCleanup() {
        console.log('🔄 Proactive cleanup initiated');
        
        if (global.gc) {
            global.gc();
        }
        
        this.clearCaches();
        
        const afterUsage = process.memoryUsage();
        console.log(`✅ Proactive cleanup complete - heap: ${Math.round(afterUsage.heapUsed / 1024 / 1024)}MB`);
    }
    
    monitorSubprocesses() {
        try {
            const psOutput = execSync('ps aux | grep -E "(node|python|claude)" | grep -v grep', { encoding: 'utf8' });
            const processes = psOutput.split('\n').filter(line => line.trim());
            
            for (const line of processes) {
                const parts = line.split(/\s+/);
                if (parts.length < 11) continue;
                
                const pid = parseInt(parts[1]);
                const memUsageKB = parseInt(parts[5]);
                const memUsageBytes = memUsageKB * 1024;
                
                if (pid === process.pid) continue;
                
                // Check subprocess memory limits
                if (memUsageBytes > this.config.subprocessLimit) {
                    console.log(`🔪 Subprocess PID ${pid} exceeds 2GB limit (${Math.round(memUsageBytes / 1024 / 1024)}MB) - terminating`);
                    this.terminateSubprocess(pid, memUsageBytes);
                }
                
                // Track active subprocesses
                this.state.activeSubprocesses.set(pid, {
                    pid,
                    memoryUsage: memUsageBytes,
                    lastSeen: Date.now()
                });
            }
            
            // Clean up stale subprocess entries
            this.cleanupStaleSubprocesses();
            
        } catch (error) {
            console.log(`⚠️ Error monitoring subprocesses: ${error.message}`);
        }
    }
    
    terminateSubprocess(pid, memoryUsage) {
        try {
            process.kill(pid, 'SIGTERM');
            console.log(`   Sent SIGTERM to PID ${pid}`);
            
            setTimeout(() => {
                try {
                    process.kill(pid, 'SIGKILL');
                    console.log(`   Sent SIGKILL to PID ${pid}`);
                } catch (e) {
                    // Process already terminated
                }
            }, 5000);
            
            this.logAlert('SUBPROCESS_TERMINATED', `PID ${pid} terminated for exceeding memory limit (${Math.round(memoryUsage / 1024 / 1024)}MB)`);
            
        } catch (error) {
            console.log(`   Failed to terminate PID ${pid}: ${error.message}`);
        }
    }
    
    terminateExcessSubprocesses() {
        if (this.state.activeSubprocesses.size <= this.config.maxSubprocesses) return;
        
        console.log(`🔪 Terminating excess subprocesses (${this.state.activeSubprocesses.size}/${this.config.maxSubprocesses})`);
        
        // Sort by memory usage (highest first)
        const sortedProcesses = Array.from(this.state.activeSubprocesses.values())
            .sort((a, b) => b.memoryUsage - a.memoryUsage);
        
        const excess = sortedProcesses.slice(this.config.maxSubprocesses);
        excess.forEach(proc => {
            this.terminateSubprocess(proc.pid, proc.memoryUsage);
        });
    }
    
    cleanupStaleSubprocesses() {
        const now = Date.now();
        const staleThreshold = 60000; // 1 minute
        
        for (const [pid, proc] of this.state.activeSubprocesses) {
            if (now - proc.lastSeen > staleThreshold) {
                this.state.activeSubprocesses.delete(pid);
            }
        }
    }
    
    clearAllCaches() {
        this.clearCaches();
        this.clearRequireCache();
        this.clearGlobalObjects();
    }
    
    clearCaches() {
        if (global._claudePMCache) {
            global._claudePMCache.clear();
            global._claudePMCache = null;
        }
        
        if (global._deploymentCache) {
            global._deploymentCache.clear();
            global._deploymentCache = null;
        }
        
        if (global._memoryCache) {
            global._memoryCache.clear();
            global._memoryCache = null;
        }
    }
    
    clearRequireCache() {
        Object.keys(require.cache).forEach(key => {
            if (key.includes('node_modules') && !key.includes('@') && !key.includes('core')) {
                delete require.cache[key];
            }
        });
    }
    
    clearGlobalObjects() {
        // Clear any large global objects
        ['_taskToolCache', '_agentCache', '_documentCache'].forEach(key => {
            if (global[key]) {
                if (typeof global[key].clear === 'function') {
                    global[key].clear();
                }
                global[key] = null;
            }
        });
    }
    
    getSystemMemoryInfo() {
        return {
            total: os.totalmem(),
            free: os.freemem(),
            used: os.totalmem() - os.freemem()
        };
    }
    
    initializeDashboard() {
        this.dashboardFile = path.join(process.cwd(), 'logs', 'memory-dashboard.json');
        fs.mkdirSync(path.dirname(this.dashboardFile), { recursive: true });
        
        console.log(`📊 Memory dashboard initialized: ${this.dashboardFile}`);
    }
    
    updateDashboard(snapshot) {
        const dashboard = {
            timestamp: new Date().toISOString(),
            uptime: Date.now() - this.state.monitoringStarted,
            current: {
                heapUsedMB: Math.round(snapshot.heapUsed / 1024 / 1024),
                heapTotalMB: Math.round(snapshot.heapTotal / 1024 / 1024),
                heapPercent: Math.round((snapshot.heapUsed / this.config.maxHeapSize) * 100),
                externalMB: Math.round(snapshot.external / 1024 / 1024),
                rssMB: Math.round(snapshot.rss / 1024 / 1024),
                systemFreeGB: Math.round(snapshot.systemFree / 1024 / 1024 / 1024),
                activeSubprocesses: snapshot.subprocessCount
            },
            thresholds: {
                warningMB: Math.round((this.config.maxHeapSize * this.config.warningThreshold) / 1024 / 1024),
                criticalMB: Math.round((this.config.maxHeapSize * this.config.criticalThreshold) / 1024 / 1024),
                maxHeapMB: Math.round(this.config.maxHeapSize / 1024 / 1024),
                subprocessLimitMB: Math.round(this.config.subprocessLimit / 1024 / 1024)
            },
            alerts: {
                totalCount: this.state.alertCount,
                lastAlert: this.state.lastAlert,
                cooldownRemaining: Math.max(0, this.config.alertCooldown - (Date.now() - this.state.lastAlert))
            },
            predictions: this.state.predictions.slice(-5),
            trends: this.calculateTrends()
        };
        
        fs.writeFileSync(this.dashboardFile, JSON.stringify(dashboard, null, 2));
    }
    
    calculateTrends() {
        if (this.state.memoryHistory.length < 10) return null;
        
        const recent = this.state.memoryHistory.slice(-10);
        const oldest = recent[0];
        const newest = recent[recent.length - 1];
        
        return {
            heapGrowthMBPerMin: Math.round(((newest.heapUsed - oldest.heapUsed) / (newest.timestamp - oldest.timestamp)) * 60000 / 1024 / 1024),
            avgHeapUsageMB: Math.round(recent.reduce((sum, s) => sum + s.heapUsed, 0) / recent.length / 1024 / 1024),
            peakHeapUsageMB: Math.round(Math.max(...recent.map(s => s.heapUsed)) / 1024 / 1024)
        };
    }
    
    setupSignalHandlers() {
        ['SIGINT', 'SIGTERM', 'exit'].forEach(signal => {
            process.on(signal, () => {
                this.shutdown();
                if (signal !== 'exit') {
                    process.exit(0);
                }
            });
        });
    }
    
    shutdown() {
        console.log('🛑 Memory monitor shutting down...');
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        if (this.subprocessInterval) {
            clearInterval(this.subprocessInterval);
        }
        
        // Generate final report
        this.generateFinalReport();
        
        console.log('✅ Memory monitor shutdown complete');
    }
    
    generateFinalReport() {
        const reportPath = path.join(process.cwd(), 'logs', `memory-monitor-report-${Date.now()}.json`);
        const report = {
            session: {
                started: new Date(this.state.monitoringStarted).toISOString(),
                ended: new Date().toISOString(),
                duration: Date.now() - this.state.monitoringStarted,
                totalAlerts: this.state.alertCount
            },
            configuration: this.config,
            finalMemoryUsage: process.memoryUsage(),
            systemMemory: this.getSystemMemoryInfo(),
            memoryHistory: this.state.memoryHistory.slice(-50),
            predictions: this.state.predictions.slice(-10),
            activeSubprocesses: Array.from(this.state.activeSubprocesses.values())
        };
        
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`📊 Final report saved: ${reportPath}`);
    }
}

// CLI Interface
if (require.main === module) {
    const monitor = new MemoryMonitor();
    
    console.log('🧠 Memory Monitor Active - Press Ctrl+C to stop');
    console.log('📊 Dashboard updates every 5 seconds');
    console.log('🔮 Predictive alerts enabled');
    
    // Keep process alive
    setInterval(() => {
        // Monitoring runs in background
    }, 60000);
}

module.exports = MemoryMonitor;