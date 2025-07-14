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
            maxHeapSize: 4 * 1024 * 1024 * 1024,      // 4GB total heap (REDUCED)
            subprocessLimit: 1.5 * 1024 * 1024 * 1024,  // 1.5GB per subprocess (REDUCED)
            criticalThreshold: 0.8,                    // 80% of max heap (REDUCED)
            warningThreshold: 0.7,                     // 70% of max heap (REDUCED)
            monitorInterval: 5000,                     // 5 second intervals
            alertCooldown: 15000,                      // 15 second alert cooldown (REDUCED)
            maxSubprocesses: 2,                        // Maximum concurrent subprocesses (REDUCED)
            subprocessTimeout: 300000,                 // 5 minute subprocess timeout
            processCleanupInterval: 30000              // Clean subprocess map every 30 seconds
        };
        
        this.state = {
            activeSubprocesses: new Map(),
            subprocessHistory: new Map(), // Track process creation/termination times
            lastAlert: 0,
            alertCount: 0,
            monitoringStarted: Date.now(),
            memoryHistory: [],
            predictions: [],
            lastSubprocessCleanup: 0
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
        this.startSubprocessCleanup();
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
    
    startSubprocessCleanup() {
        this.subprocessCleanupInterval = setInterval(() => {
            this.performSubprocessCleanup();
        }, this.config.processCleanupInterval);
        
        console.log('🧹 Subprocess cleanup monitoring started');
    }
    
    performSubprocessCleanup() {
        const now = Date.now();
        if (now - this.state.lastSubprocessCleanup < this.config.processCleanupInterval) {
            return;
        }
        
        this.state.lastSubprocessCleanup = now;
        
        // Clean up stale subprocess entries
        this.cleanupStaleSubprocesses();
        
        // Force cleanup of global activeSubprocesses if it exists
        this.cleanupGlobalSubprocessMaps();
        
        // Terminate long-running subprocesses
        this.terminateLongRunningSubprocesses();
        
        console.log(`🧹 Subprocess cleanup complete - tracking ${this.state.activeSubprocesses.size} processes`);
    }
    
    cleanupGlobalSubprocessMaps() {
        console.log('🧹 Advanced global subprocess map cleanup with enhanced manager integration...');
        
        // Try to use Enhanced Subprocess Manager if available
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const subprocessManager = getSubprocessManager();
            
            console.log('   Using Enhanced Subprocess Manager for comprehensive cleanup...');
            
            // Perform comprehensive cleanup through the enhanced manager
            subprocessManager.forceCleanup();
            
            // Get performance metrics
            const metrics = subprocessManager.getPerformanceMetrics();
            const activeCount = subprocessManager.getActiveSubprocessCount();
            
            console.log(`   Enhanced cleanup complete: ${activeCount} active, ${metrics.totalSubprocessesTerminated} terminated`);
            
            // Validate zero memory retention
            const validation = subprocessManager.validateZeroMemoryRetention();
            if (!validation.isValid) {
                console.log('   ⚠️ Memory retention detected, performing fallback cleanup...');
                this.fallbackGlobalSubprocessCleanup();
            } else {
                console.log('   ✅ Zero memory retention validated');
            }
            
        } catch (error) {
            console.log('   Enhanced Subprocess Manager not available, using basic cleanup...');
            this.fallbackGlobalSubprocessCleanup();
        }
    }
    
    fallbackGlobalSubprocessCleanup() {
        // Clean up global subprocess tracking that causes memory leaks
        if (global.activeSubprocesses && global.activeSubprocesses instanceof Map) {
            const initialSize = global.activeSubprocesses.size;
            
            // Remove entries for processes that no longer exist
            for (const [pid, processInfo] of global.activeSubprocesses) {
                if (!this.isProcessAlive(pid)) {
                    global.activeSubprocesses.delete(pid);
                }
            }
            
            const cleanedCount = initialSize - global.activeSubprocesses.size;
            if (cleanedCount > 0) {
                console.log(`   Cleaned ${cleanedCount} stale entries from global activeSubprocesses`);
            }
        }
        
        // Also clean any other global process maps
        ['_subprocessCache', '_processTracker', '_taskToolProcesses'].forEach(mapName => {
            if (global[mapName] && typeof global[mapName].clear === 'function') {
                const size = global[mapName].size || 0;
                global[mapName].clear();
                if (size > 0) {
                    console.log(`   Cleared ${size} entries from global ${mapName}`);
                }
            }
        });
    }
    
    isProcessAlive(pid) {
        try {
            process.kill(pid, 0); // Signal 0 checks if process exists
            return true;
        } catch (error) {
            return false;
        }
    }
    
    terminateLongRunningSubprocesses() {
        const now = Date.now();
        
        for (const [pid, processInfo] of this.state.activeSubprocesses) {
            const runtime = now - processInfo.lastSeen;
            
            if (runtime > this.config.subprocessTimeout) {
                console.log(`🔪 Terminating long-running subprocess PID ${pid} (runtime: ${Math.round(runtime / 1000)}s)`);
                this.terminateSubprocess(pid, processInfo.memoryUsage);
                this.state.activeSubprocesses.delete(pid);
            }
        }
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
        const staleThreshold = 30000; // 30 seconds (REDUCED)
        
        let cleanedCount = 0;
        for (const [pid, proc] of this.state.activeSubprocesses) {
            if (now - proc.lastSeen > staleThreshold || !this.isProcessAlive(pid)) {
                this.state.activeSubprocesses.delete(pid);
                cleanedCount++;
                
                // Also remove from history tracking
                if (this.state.subprocessHistory.has(pid)) {
                    this.state.subprocessHistory.delete(pid);
                }
            }
        }
        
        if (cleanedCount > 0) {
            console.log(`   Cleaned ${cleanedCount} stale subprocess entries`);
        }
        
        // Limit memory history size to prevent unbounded growth
        if (this.state.memoryHistory.length > 200) {
            this.state.memoryHistory = this.state.memoryHistory.slice(-100);
            console.log('   Trimmed memory history to prevent growth');
        }
        
        // Limit prediction history size
        if (this.state.predictions.length > 50) {
            this.state.predictions = this.state.predictions.slice(-25);
            console.log('   Trimmed prediction history to prevent growth');
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
        
        if (this.subprocessCleanupInterval) {
            clearInterval(this.subprocessCleanupInterval);
        }
        
        // Final cleanup of global maps
        this.cleanupGlobalSubprocessMaps();
        
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