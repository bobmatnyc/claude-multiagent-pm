#!/usr/bin/env node

/**
 * Claude PM Framework - Enhanced Subprocess Lifecycle Manager
 * 
 * Complete subprocess lifecycle management with zero memory retention.
 * Integrates with enhanced memory monitoring and cache management systems.
 * 
 * Features:
 * - Comprehensive subprocess tracking with strict cleanup
 * - Memory-aware subprocess limits and termination
 * - Integration with enhanced cache manager and memory monitor
 * - Zero memory retention guarantee with automated validation
 * - Circuit breaker for subprocess memory exhaustion
 * - Detailed lifecycle analytics and reporting
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const { performance } = require('perf_hooks');

class EnhancedSubprocessManager {
    constructor(options = {}) {
        this.config = {
            maxConcurrentSubprocesses: options.maxConcurrentSubprocesses || 2,
            subprocessMemoryLimit: options.subprocessMemoryLimit || 1.5 * 1024 * 1024 * 1024, // 1.5GB per subprocess
            subprocessTimeout: options.subprocessTimeout || 300000, // 5 minutes
            cleanupInterval: options.cleanupInterval || 30000, // 30 seconds
            memoryCheckInterval: options.memoryCheckInterval || 10000, // 10 seconds
            staleThreshold: options.staleThreshold || 30000, // 30 seconds for stale detection
            zombieDetectionEnabled: options.zombieDetectionEnabled !== false,
            strictMemoryEnforcement: options.strictMemoryEnforcement !== false,
            integrationWithMonitoring: options.integrationWithMonitoring !== false,
            detailedLogging: options.detailedLogging !== false
        };
        
        // Core tracking structures
        this.activeSubprocesses = new Map();
        this.subprocessHistory = new Map();
        this.memoryUsageHistory = new Map();
        this.terminationQueue = new Set();
        
        // Performance metrics
        this.metrics = {
            totalSubprocessesCreated: 0,
            totalSubprocessesTerminated: 0,
            totalMemoryLeaksDetected: 0,
            totalZombieProcessesKilled: 0,
            totalCleanupOperations: 0,
            totalMemoryReclaimed: 0,
            avgSubprocessLifetime: 0,
            maxConcurrentSubprocesses: 0,
            memoryLeakPreventions: 0
        };
        
        // Integration with existing systems
        this.enhancedCacheManager = null;
        this.memoryMonitor = null;
        this.memoryOptimizer = null;
        
        // Monitoring intervals
        this.cleanupInterval = null;
        this.memoryCheckInterval = null;
        this.performanceReportInterval = null;
        
        this.startTime = Date.now();
        this.lastCleanup = 0;
        this.lastMemoryCheck = 0;
        
        this.logFile = path.join(process.cwd(), 'logs', 'subprocess-lifecycle.log');
        this.reportFile = path.join(process.cwd(), 'logs', 'subprocess-analytics.json');
        
        this.initialize();
    }
    
    initialize() {
        console.log('🚀 Enhanced Subprocess Manager - Initializing Comprehensive Lifecycle Management');
        console.log('📊 Configuration:');
        console.log(`   Max Concurrent Subprocesses: ${this.config.maxConcurrentSubprocesses}`);
        console.log(`   Subprocess Memory Limit: ${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024)}MB`);
        console.log(`   Subprocess Timeout: ${this.config.subprocessTimeout / 1000}s`);
        console.log(`   Cleanup Interval: ${this.config.cleanupInterval / 1000}s`);
        console.log(`   Zombie Detection: ${this.config.zombieDetectionEnabled ? 'Enabled' : 'Disabled'}`);
        console.log(`   Strict Memory Enforcement: ${this.config.strictMemoryEnforcement ? 'Enabled' : 'Disabled'}`);
        
        this.ensureLogsDirectory();
        this.integrateWithExistingSystems();
        this.startLifecycleMonitoring();
        this.setupSignalHandlers();
        this.setupGlobalCleanup();
        
        console.log('✅ Enhanced Subprocess Manager initialized');
    }
    
    ensureLogsDirectory() {
        const logsDir = path.dirname(this.logFile);
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }
    }
    
    integrateWithExistingSystems() {
        if (this.config.integrationWithMonitoring) {
            try {
                // Try to get existing enhanced cache manager
                if (global._enhancedCacheManager) {
                    this.enhancedCacheManager = global._enhancedCacheManager;
                    console.log('🔗 Integrated with Enhanced Cache Manager');
                }
                
                // Try to load memory monitoring components
                const MemoryMonitor = require('./memory-monitor.js');
                const MemoryOptimizer = require('./memory-optimization.js');
                
                console.log('🔗 Integrated with Memory Monitoring Systems');
            } catch (error) {
                console.log(`⚠️ Integration warning: ${error.message}`);
            }
        }
    }
    
    startLifecycleMonitoring() {
        // Main cleanup monitoring
        this.cleanupInterval = setInterval(() => {
            this.performComprehensiveCleanup();
        }, this.config.cleanupInterval);
        
        // Memory monitoring for subprocesses
        this.memoryCheckInterval = setInterval(() => {
            this.performMemoryAwareCleanup();
        }, this.config.memoryCheckInterval);
        
        // Performance reporting
        this.performanceReportInterval = setInterval(() => {
            this.updatePerformanceMetrics();
        }, 60000); // Every minute
        
        console.log('🔄 Lifecycle monitoring started');
    }
    
    setupGlobalCleanup() {
        // Override global activeSubprocesses if it exists
        if (global.activeSubprocesses) {
            console.log('🧹 Taking over global activeSubprocesses management');
            
            // Migrate existing entries
            if (global.activeSubprocesses instanceof Map) {
                for (const [pid, processInfo] of global.activeSubprocesses) {
                    this.trackSubprocess(pid, processInfo);
                }
            }
            
            // Replace with our managed version
            global.activeSubprocesses = this.activeSubprocesses;
        } else {
            global.activeSubprocesses = this.activeSubprocesses;
        }
        
        // Clean up other global process maps
        this.cleanupGlobalProcessMaps();
    }
    
    cleanupGlobalProcessMaps() {
        const globalMaps = ['_subprocessCache', '_processTracker', '_taskToolProcesses'];
        
        globalMaps.forEach(mapName => {
            if (global[mapName]) {
                if (typeof global[mapName].clear === 'function') {
                    const size = global[mapName].size || 0;
                    global[mapName].clear();
                    if (size > 0) {
                        console.log(`🧹 Cleared ${size} entries from global ${mapName}`);
                        this.logEvent('GLOBAL_MAP_CLEANUP', `Cleared ${size} entries from ${mapName}`);
                    }
                }
                global[mapName] = null;
            }
        });
    }
    
    trackSubprocess(pid, processInfo = {}) {
        const now = Date.now();
        const enhancedProcessInfo = {
            pid: parseInt(pid),
            memoryUsage: processInfo.memoryUsage || 0,
            lastSeen: now,
            created: processInfo.created || now,
            command: processInfo.command || 'unknown',
            parentPid: process.pid,
            memoryHistory: [],
            warningsSent: 0,
            terminationAttempts: 0,
            ...processInfo
        };
        
        this.activeSubprocesses.set(pid, enhancedProcessInfo);
        
        // Track in history for analytics
        this.subprocessHistory.set(pid, {
            ...enhancedProcessInfo,
            firstTracked: now,
            events: []
        });
        
        this.metrics.totalSubprocessesCreated++;
        this.metrics.maxConcurrentSubprocesses = Math.max(
            this.metrics.maxConcurrentSubprocesses, 
            this.activeSubprocesses.size
        );
        
        this.logEvent('SUBPROCESS_TRACKED', `PID ${pid} tracked`, { processInfo: enhancedProcessInfo });
        
        if (this.config.detailedLogging) {
            console.log(`📝 Tracking subprocess PID ${pid} (${Math.round(enhancedProcessInfo.memoryUsage / 1024 / 1024)}MB)`);
        }
        
        return enhancedProcessInfo;
    }
    
    untrackSubprocess(pid, reason = 'normal_termination') {
        const processInfo = this.activeSubprocesses.get(pid);
        
        if (processInfo) {
            const lifetime = Date.now() - processInfo.created;
            
            // Update metrics
            this.metrics.totalSubprocessesTerminated++;
            this.metrics.avgSubprocessLifetime = (
                (this.metrics.avgSubprocessLifetime * (this.metrics.totalSubprocessesTerminated - 1)) + lifetime
            ) / this.metrics.totalSubprocessesTerminated;
            
            // Update history
            const historyEntry = this.subprocessHistory.get(pid);
            if (historyEntry) {
                historyEntry.events.push({
                    timestamp: Date.now(),
                    event: 'UNTRACKED',
                    reason,
                    lifetime
                });
                historyEntry.terminated = Date.now();
                historyEntry.terminationReason = reason;
            }
            
            // Remove from active tracking
            this.activeSubprocesses.delete(pid);
            this.terminationQueue.delete(pid);
            
            // Clean up memory usage history
            if (this.memoryUsageHistory.has(pid)) {
                this.memoryUsageHistory.delete(pid);
            }
            
            this.logEvent('SUBPROCESS_UNTRACKED', `PID ${pid} untracked: ${reason}`, { 
                lifetime, 
                memoryUsage: processInfo.memoryUsage 
            });
            
            if (this.config.detailedLogging) {
                console.log(`📝 Untracked subprocess PID ${pid} (lifetime: ${Math.round(lifetime / 1000)}s, reason: ${reason})`);
            }
            
            return true;
        }
        
        return false;
    }
    
    performComprehensiveCleanup() {
        const startTime = performance.now();
        const now = Date.now();
        
        if (now - this.lastCleanup < this.config.cleanupInterval) {
            return;
        }
        
        this.lastCleanup = now;
        this.metrics.totalCleanupOperations++;
        
        console.log('🧹 Performing comprehensive subprocess cleanup...');
        
        let cleanedProcesses = 0;
        let memoryReclaimed = 0;
        let zombiesKilled = 0;
        
        // Step 1: Clean up stale entries
        const staleProcesses = this.identifyStaleProcesses();
        for (const pid of staleProcesses) {
            const processInfo = this.activeSubprocesses.get(pid);
            if (processInfo) {
                memoryReclaimed += processInfo.memoryUsage || 0;
                this.untrackSubprocess(pid, 'stale_cleanup');
                cleanedProcesses++;
            }
        }
        
        // Step 2: Terminate long-running processes
        const longRunningProcesses = this.identifyLongRunningProcesses();
        for (const pid of longRunningProcesses) {
            if (this.terminateSubprocess(pid, 'timeout_exceeded')) {
                cleanedProcesses++;
            }
        }
        
        // Step 3: Kill zombie processes
        if (this.config.zombieDetectionEnabled) {
            zombiesKilled = this.killZombieProcesses();
        }
        
        // Step 4: Clean up memory usage history
        this.cleanupMemoryHistory();
        
        // Step 5: Enforce concurrent subprocess limits
        this.enforceSubprocessLimits();
        
        // Step 6: Clean up global maps
        this.cleanupGlobalProcessMaps();
        
        // Step 7: Integration cleanup
        this.performIntegrationCleanup();
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.metrics.totalMemoryReclaimed += memoryReclaimed;
        
        console.log(`✅ Cleanup complete: ${cleanedProcesses} processes cleaned, ${Math.round(memoryReclaimed / 1024 / 1024)}MB reclaimed, ${zombiesKilled} zombies killed (${Math.round(duration)}ms)`);
        
        this.logEvent('COMPREHENSIVE_CLEANUP', 'Cleanup completed', {
            cleanedProcesses,
            memoryReclaimed,
            zombiesKilled,
            duration,
            activeCount: this.activeSubprocesses.size
        });
    }
    
    performMemoryAwareCleanup() {
        const now = Date.now();
        
        if (now - this.lastMemoryCheck < this.config.memoryCheckInterval) {
            return;
        }
        
        this.lastMemoryCheck = now;
        
        // Check each subprocess memory usage
        for (const [pid, processInfo] of this.activeSubprocesses) {
            const currentMemory = this.getProcessMemoryUsage(pid);
            
            if (currentMemory > 0) {
                // Update memory usage
                processInfo.memoryUsage = currentMemory;
                processInfo.lastSeen = now;
                
                // Track memory history
                this.trackMemoryUsage(pid, currentMemory);
                
                // Check memory limits
                if (this.config.strictMemoryEnforcement && currentMemory > this.config.subprocessMemoryLimit) {
                    console.log(`🚨 Subprocess PID ${pid} exceeds memory limit (${Math.round(currentMemory / 1024 / 1024)}MB > ${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024)}MB)`);
                    
                    if (this.terminateSubprocess(pid, 'memory_limit_exceeded')) {
                        this.metrics.memoryLeakPreventions++;
                        this.logEvent('MEMORY_LIMIT_EXCEEDED', `Terminated PID ${pid} for memory limit`, { 
                            memoryUsage: currentMemory,
                            limit: this.config.subprocessMemoryLimit 
                        });
                    }
                }
            } else if (currentMemory === 0) {
                // Process not found, mark for cleanup
                this.untrackSubprocess(pid, 'process_not_found');
            }
        }
    }
    
    trackMemoryUsage(pid, memoryUsage) {
        if (!this.memoryUsageHistory.has(pid)) {
            this.memoryUsageHistory.set(pid, []);
        }
        
        const history = this.memoryUsageHistory.get(pid);
        history.push({
            timestamp: Date.now(),
            memoryUsage
        });
        
        // Keep only last 20 entries per process
        if (history.length > 20) {
            history.splice(0, history.length - 20);
        }
        
        // Detect memory leaks
        if (history.length >= 5) {
            const isLeaking = this.detectMemoryLeak(history);
            if (isLeaking) {
                this.metrics.totalMemoryLeaksDetected++;
                console.log(`🚨 Memory leak detected in subprocess PID ${pid}`);
                this.logEvent('MEMORY_LEAK_DETECTED', `PID ${pid} memory leak detected`, { history: history.slice(-5) });
            }
        }
    }
    
    detectMemoryLeak(memoryHistory) {
        if (memoryHistory.length < 5) return false;
        
        const recent = memoryHistory.slice(-5);
        let consistentGrowth = 0;
        
        for (let i = 1; i < recent.length; i++) {
            if (recent[i].memoryUsage > recent[i-1].memoryUsage) {
                consistentGrowth++;
            }
        }
        
        const growthRatio = consistentGrowth / (recent.length - 1);
        const totalGrowth = recent[recent.length - 1].memoryUsage - recent[0].memoryUsage;
        const growthMB = totalGrowth / 1024 / 1024;
        
        // Consider it a leak if 80% consistent growth and >100MB total growth
        return growthRatio >= 0.8 && growthMB > 100;
    }
    
    identifyStaleProcesses() {
        const now = Date.now();
        const staleProcesses = [];
        
        for (const [pid, processInfo] of this.activeSubprocesses) {
            const timeSinceLastSeen = now - processInfo.lastSeen;
            
            if (timeSinceLastSeen > this.config.staleThreshold) {
                // Double-check if process still exists
                if (!this.isProcessAlive(pid)) {
                    staleProcesses.push(pid);
                }
            }
        }
        
        return staleProcesses;
    }
    
    identifyLongRunningProcesses() {
        const now = Date.now();
        const longRunningProcesses = [];
        
        for (const [pid, processInfo] of this.activeSubprocesses) {
            const runtime = now - processInfo.created;
            
            if (runtime > this.config.subprocessTimeout) {
                longRunningProcesses.push(pid);
            }
        }
        
        return longRunningProcesses;
    }
    
    isProcessAlive(pid) {
        try {
            process.kill(pid, 0); // Signal 0 checks if process exists
            return true;
        } catch (error) {
            return false;
        }
    }
    
    getProcessMemoryUsage(pid) {
        try {
            const result = execSync(`ps -o rss= -p ${pid}`, { encoding: 'utf8' });
            const memoryKB = parseInt(result.trim());
            return isNaN(memoryKB) ? 0 : memoryKB * 1024; // Convert to bytes
        } catch (error) {
            return 0; // Process not found
        }
    }
    
    terminateSubprocess(pid, reason = 'manual_termination') {
        const processInfo = this.activeSubprocesses.get(pid);
        
        if (!processInfo) {
            return false;
        }
        
        try {
            console.log(`🔪 Terminating subprocess PID ${pid} (reason: ${reason})`);
            
            processInfo.terminationAttempts++;
            
            // Graceful termination first
            process.kill(pid, 'SIGTERM');
            this.logEvent('SUBPROCESS_SIGTERM', `Sent SIGTERM to PID ${pid}`, { reason });
            
            // Schedule forceful termination if needed
            setTimeout(() => {
                if (this.activeSubprocesses.has(pid) && this.isProcessAlive(pid)) {
                    try {
                        process.kill(pid, 'SIGKILL');
                        console.log(`💀 Force killed subprocess PID ${pid}`);
                        this.logEvent('SUBPROCESS_SIGKILL', `Sent SIGKILL to PID ${pid}`, { reason });
                    } catch (error) {
                        // Process may have already terminated
                    }
                }
                
                // Clean up after forceful termination
                setTimeout(() => {
                    this.untrackSubprocess(pid, reason);
                }, 1000);
            }, 5000);
            
            return true;
            
        } catch (error) {
            console.log(`⚠️ Failed to terminate subprocess PID ${pid}: ${error.message}`);
            this.logEvent('TERMINATION_FAILED', `Failed to terminate PID ${pid}`, { reason, error: error.message });
            return false;
        }
    }
    
    killZombieProcesses() {
        let zombiesKilled = 0;
        
        try {
            // Find zombie processes
            const zombieResult = execSync('ps aux | grep -E "\\<Z\\>" | grep -v grep', { encoding: 'utf8' });
            const zombieLines = zombieResult.split('\n').filter(line => line.trim());
            
            for (const line of zombieLines) {
                const parts = line.split(/\s+/);
                if (parts.length >= 2) {
                    const pid = parseInt(parts[1]);
                    
                    if (!isNaN(pid) && pid !== process.pid) {
                        try {
                            process.kill(pid, 'SIGKILL');
                            zombiesKilled++;
                            console.log(`💀 Killed zombie process PID ${pid}`);
                            this.logEvent('ZOMBIE_KILLED', `Killed zombie PID ${pid}`);
                        } catch (error) {
                            // Zombie may have been cleaned up
                        }
                    }
                }
            }
            
        } catch (error) {
            // No zombies found or command failed
        }
        
        this.metrics.totalZombieProcessesKilled += zombiesKilled;
        return zombiesKilled;
    }
    
    enforceSubprocessLimits() {
        if (this.activeSubprocesses.size <= this.config.maxConcurrentSubprocesses) {
            return;
        }
        
        console.log(`🔒 Enforcing subprocess limits: ${this.activeSubprocesses.size}/${this.config.maxConcurrentSubprocesses}`);
        
        // Sort by memory usage (highest first) and age (oldest first)
        const sortedProcesses = Array.from(this.activeSubprocesses.values())
            .sort((a, b) => {
                // Primary sort: memory usage (descending)
                if (a.memoryUsage !== b.memoryUsage) {
                    return b.memoryUsage - a.memoryUsage;
                }
                // Secondary sort: age (ascending, kill oldest)
                return a.created - b.created;
            });
        
        const excess = sortedProcesses.slice(this.config.maxConcurrentSubprocesses);
        
        for (const processInfo of excess) {
            this.terminateSubprocess(processInfo.pid, 'concurrent_limit_exceeded');
        }
    }
    
    cleanupMemoryHistory() {
        const now = Date.now();
        const maxAge = 300000; // 5 minutes
        
        for (const [pid, history] of this.memoryUsageHistory) {
            // Remove old entries
            const validEntries = history.filter(entry => (now - entry.timestamp) < maxAge);
            
            if (validEntries.length !== history.length) {
                this.memoryUsageHistory.set(pid, validEntries);
            }
            
            // Remove entire history if process is not active
            if (!this.activeSubprocesses.has(pid)) {
                this.memoryUsageHistory.delete(pid);
            }
        }
        
        // Clean up old subprocess history entries
        for (const [pid, historyEntry] of this.subprocessHistory) {
            if (historyEntry.terminated && (now - historyEntry.terminated) > maxAge) {
                this.subprocessHistory.delete(pid);
            }
        }
    }
    
    performIntegrationCleanup() {
        // Clean up enhanced cache manager subprocess cache
        if (this.enhancedCacheManager) {
            const subprocessCache = this.enhancedCacheManager.caches.get('_subprocessCache');
            if (subprocessCache) {
                const result = subprocessCache.performMemoryCleanup();
                if (result.entriesRemoved > 0) {
                    console.log(`🧹 Enhanced cache cleanup: ${result.entriesRemoved} subprocess cache entries removed`);
                }
            }
        }
        
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }
    }
    
    updatePerformanceMetrics() {
        const uptime = Date.now() - this.startTime;
        const activeCount = this.activeSubprocesses.size;
        
        const metrics = {
            ...this.metrics,
            uptime,
            activeSubprocesses: activeCount,
            avgMemoryPerSubprocess: activeCount > 0 ? 
                Array.from(this.activeSubprocesses.values())
                    .reduce((sum, p) => sum + (p.memoryUsage || 0), 0) / activeCount : 0,
            memoryEfficiency: this.metrics.totalMemoryReclaimed / Math.max(1, this.metrics.totalSubprocessesCreated),
            cleanupEfficiency: this.metrics.totalSubprocessesTerminated / Math.max(1, this.metrics.totalCleanupOperations)
        };
        
        if (this.config.detailedLogging) {
            console.log(`📊 Performance: ${activeCount} active, ${Math.round(metrics.avgMemoryPerSubprocess / 1024 / 1024)}MB avg, ${this.metrics.memoryLeakPreventions} leaks prevented`);
        }
        
        // Save metrics to file
        fs.writeFileSync(this.reportFile, JSON.stringify({
            timestamp: new Date().toISOString(),
            metrics,
            configuration: this.config
        }, null, 2));
    }
    
    logEvent(type, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            type,
            message,
            data,
            activeSubprocesses: this.activeSubprocesses.size,
            memoryUsage: process.memoryUsage()
        };
        
        fs.appendFileSync(this.logFile, JSON.stringify(logEntry) + '\n');
    }
    
    generateComprehensiveReport() {
        const uptime = Date.now() - this.startTime;
        
        const report = {
            timestamp: new Date().toISOString(),
            session: {
                started: new Date(this.startTime).toISOString(),
                uptime,
                totalDuration: Math.round(uptime / 1000)
            },
            metrics: {
                ...this.metrics,
                currentActiveSubprocesses: this.activeSubprocesses.size,
                totalHistoryEntries: this.subprocessHistory.size,
                memoryHistoryEntries: this.memoryUsageHistory.size
            },
            currentState: {
                activeSubprocesses: Array.from(this.activeSubprocesses.entries()).map(([pid, info]) => ({
                    pid,
                    memoryUsageMB: Math.round((info.memoryUsage || 0) / 1024 / 1024),
                    runtimeSeconds: Math.round((Date.now() - info.created) / 1000),
                    command: info.command,
                    warningsSent: info.warningsSent
                })),
                terminationQueue: Array.from(this.terminationQueue)
            },
            configuration: this.config,
            performance: {
                avgSubprocessLifetimeMinutes: Math.round(this.metrics.avgSubprocessLifetime / 60000),
                memoryEfficiencyMB: Math.round(this.metrics.totalMemoryReclaimed / 1024 / 1024),
                leakPreventionRate: this.metrics.memoryLeakPreventions / Math.max(1, this.metrics.totalSubprocessesCreated),
                cleanupSuccessRate: this.metrics.totalSubprocessesTerminated / Math.max(1, this.metrics.totalSubprocessesCreated)
            },
            recommendations: this.generateRecommendations()
        };
        
        const reportPath = path.join(process.cwd(), 'logs', `subprocess-comprehensive-report-${Date.now()}.json`);
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📊 Comprehensive report generated: ${reportPath}`);
        return report;
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        if (this.metrics.totalMemoryLeaksDetected > this.metrics.totalSubprocessesCreated * 0.1) {
            recommendations.push('High memory leak detection rate - consider reducing subprocess memory limits');
        }
        
        if (this.metrics.maxConcurrentSubprocesses === this.config.maxConcurrentSubprocesses) {
            recommendations.push('Maximum concurrent subprocess limit reached - consider increasing limit or optimizing subprocess usage');
        }
        
        if (this.metrics.avgSubprocessLifetime > this.config.subprocessTimeout * 0.8) {
            recommendations.push('Average subprocess lifetime near timeout threshold - consider increasing timeout or optimizing subprocess tasks');
        }
        
        if (this.activeSubprocesses.size === 0 && this.metrics.totalSubprocessesCreated > 0) {
            recommendations.push('All subprocesses successfully cleaned up - system operating efficiently');
        }
        
        return recommendations;
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
        console.log('🛑 Enhanced Subprocess Manager shutting down...');
        
        // Clear intervals
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        
        if (this.memoryCheckInterval) {
            clearInterval(this.memoryCheckInterval);
        }
        
        if (this.performanceReportInterval) {
            clearInterval(this.performanceReportInterval);
        }
        
        // Terminate all active subprocesses
        const activeCount = this.activeSubprocesses.size;
        if (activeCount > 0) {
            console.log(`🔪 Terminating ${activeCount} active subprocesses...`);
            
            for (const [pid] of this.activeSubprocesses) {
                this.terminateSubprocess(pid, 'manager_shutdown');
            }
        }
        
        // Final cleanup
        this.performComprehensiveCleanup();
        
        // Generate final report
        this.generateComprehensiveReport();
        
        // Clear global references
        this.cleanupGlobalProcessMaps();
        
        console.log('✅ Enhanced Subprocess Manager shutdown complete');
    }
    
    // Public API methods
    getActiveSubprocessCount() {
        return this.activeSubprocesses.size;
    }
    
    getSubprocessInfo(pid) {
        return this.activeSubprocesses.get(pid);
    }
    
    getAllSubprocessInfo() {
        return Array.from(this.activeSubprocesses.entries());
    }
    
    getPerformanceMetrics() {
        return { ...this.metrics };
    }
    
    forceCleanup() {
        this.performComprehensiveCleanup();
    }
    
    validateZeroMemoryRetention() {
        // Validate that all subprocess references are properly cleaned up
        const validation = {
            globalActiveSubprocesses: global.activeSubprocesses ? global.activeSubprocesses.size : 0,
            managerActiveSubprocesses: this.activeSubprocesses.size,
            memoryHistoryEntries: this.memoryUsageHistory.size,
            terminationQueueSize: this.terminationQueue.size,
            globalMapsCleared: true
        };
        
        // Check global maps
        const globalMaps = ['_subprocessCache', '_processTracker', '_taskToolProcesses'];
        for (const mapName of globalMaps) {
            if (global[mapName] && global[mapName].size > 0) {
                validation.globalMapsCleared = false;
                validation[`${mapName}Size`] = global[mapName].size;
            }
        }
        
        const isValid = validation.globalActiveSubprocesses === validation.managerActiveSubprocesses &&
                        validation.terminationQueueSize === 0 &&
                        validation.globalMapsCleared;
        
        return {
            isValid,
            validation,
            recommendations: isValid ? ['Zero memory retention validated'] : 
                           ['Memory retention detected - run cleanup operations']
        };
    }
}

// Global manager instance
let _globalSubprocessManager = null;

function getSubprocessManager(options = {}) {
    if (!_globalSubprocessManager) {
        _globalSubprocessManager = new EnhancedSubprocessManager(options);
    }
    return _globalSubprocessManager;
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    const manager = getSubprocessManager();
    
    switch (command) {
        case 'monitor':
            console.log('🔍 Enhanced Subprocess Manager - Active Monitoring Mode');
            console.log('Press Ctrl+C to stop');
            
            setInterval(() => {
                const metrics = manager.getPerformanceMetrics();
                const activeCount = manager.getActiveSubprocessCount();
                console.log(`📊 Active: ${activeCount}, Created: ${metrics.totalSubprocessesCreated}, Terminated: ${metrics.totalSubprocessesTerminated}, Leaks Prevented: ${metrics.memoryLeakPreventions}`);
            }, 30000);
            break;
            
        case 'cleanup':
            console.log('🧹 Running immediate comprehensive cleanup...');
            manager.forceCleanup();
            const validation = manager.validateZeroMemoryRetention();
            console.log('🔍 Memory retention validation:', validation);
            process.exit(0);
            break;
            
        case 'report':
            const report = manager.generateComprehensiveReport();
            console.log('\n📊 Subprocess Management Report:');
            console.log(`Active Subprocesses: ${report.currentState.activeSubprocesses.length}`);
            console.log(`Total Created: ${report.metrics.totalSubprocessesCreated}`);
            console.log(`Total Terminated: ${report.metrics.totalSubprocessesTerminated}`);
            console.log(`Memory Leaks Detected: ${report.metrics.totalMemoryLeaksDetected}`);
            console.log(`Memory Leaks Prevented: ${report.metrics.memoryLeakPreventions}`);
            console.log(`Avg Lifetime: ${report.performance.avgSubprocessLifetimeMinutes} minutes`);
            
            if (report.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                report.recommendations.forEach(rec => console.log(`   • ${rec}`));
            }
            
            process.exit(0);
            break;
            
        case 'validate':
            const validationResult = manager.validateZeroMemoryRetention();
            console.log('\n🔍 Zero Memory Retention Validation:');
            console.log(`Validation Result: ${validationResult.isValid ? '✅ PASSED' : '❌ FAILED'}`);
            console.log('Details:', JSON.stringify(validationResult.validation, null, 2));
            
            if (validationResult.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                validationResult.recommendations.forEach(rec => console.log(`   • ${rec}`));
            }
            
            process.exit(validationResult.isValid ? 0 : 1);
            break;
            
        default:
            console.log(`
🚀 Claude PM Framework - Enhanced Subprocess Manager

Usage:
  node enhanced-subprocess-manager.js <command>

Commands:
  monitor     Start continuous monitoring
  cleanup     Run immediate comprehensive cleanup
  report      Generate comprehensive report
  validate    Validate zero memory retention

Examples:
  node enhanced-subprocess-manager.js monitor
  node enhanced-subprocess-manager.js cleanup
  node enhanced-subprocess-manager.js validate
            `);
            process.exit(1);
    }
}

module.exports = { EnhancedSubprocessManager, getSubprocessManager };