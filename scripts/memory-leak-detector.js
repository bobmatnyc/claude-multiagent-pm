#!/usr/bin/env node

/**
 * Claude PM Framework - Advanced Memory Leak Detection System
 * 
 * Comprehensive memory leak detection with pattern analysis and automated remediation
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class MemoryLeakDetector {
    constructor() {
        this.config = {
            detectionInterval: 30000,        // 30 seconds
            memoryGrowthThreshold: 50,       // 50MB growth threshold
            leakConfidenceThreshold: 0.75,   // 75% confidence
            historySamples: 20,              // Number of samples for analysis
            processAgeThreshold: 300000,     // 5 minutes for process monitoring
            alertCooldown: 60000,            // 1 minute between alerts
            maxHeapSize: 4 * 1024 * 1024 * 1024, // 4GB heap limit
            alertThresholds: {
                warning: 0.6,    // 60% of max heap
                critical: 0.8,   // 80% of max heap
                emergency: 0.9   // 90% of max heap
            }
        };
        
        this.state = {
            memoryHistory: [],
            processHistory: new Map(),
            leakPatterns: [],
            lastAlert: 0,
            detectionStarted: Date.now(),
            alertsTriggered: 0,
            leaksDetected: 0,
            remediationsPerformed: 0
        };
        
        this.logFile = path.join(process.cwd(), 'logs', 'memory-leak-detection.log');
        this.reportFile = path.join(process.cwd(), 'logs', 'leak-detection-report.json');
        
        this.ensureLogsDirectory();
        this.startDetection();
    }
    
    ensureLogsDirectory() {
        const logsDir = path.dirname(this.logFile);
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }
    }
    
    startDetection() {
        console.log('🔍 Memory Leak Detector - Starting Advanced Pattern Analysis');
        console.log(`📊 Configuration:`);
        console.log(`   Detection Interval: ${this.config.detectionInterval}ms`);
        console.log(`   Growth Threshold: ${this.config.memoryGrowthThreshold}MB`);
        console.log(`   Confidence Threshold: ${this.config.leakConfidenceThreshold * 100}%`);
        console.log(`   Max Heap Size: ${Math.round(this.config.maxHeapSize / 1024 / 1024 / 1024)}GB`);
        
        this.detectionInterval = setInterval(() => {
            this.performLeakDetection();
        }, this.config.detectionInterval);
        
        this.setupSignalHandlers();
        this.logEvent('DETECTION_STARTED', 'Memory leak detection system initialized');
    }
    
    performLeakDetection() {
        const timestamp = Date.now();
        const memorySnapshot = this.captureMemorySnapshot(timestamp);
        
        this.state.memoryHistory.push(memorySnapshot);
        
        // Keep only recent history
        if (this.state.memoryHistory.length > this.config.historySamples * 2) {
            this.state.memoryHistory = this.state.memoryHistory.slice(-this.config.historySamples);
        }
        
        // Perform various detection algorithms
        this.detectMemoryLeaks(memorySnapshot);
        this.detectProcessLeaks();
        this.analyzeMemoryPatterns();
        this.checkThresholds(memorySnapshot);
        
        // Update detection report
        this.updateDetectionReport();
    }
    
    captureMemorySnapshot(timestamp) {
        const usage = process.memoryUsage();
        const systemMem = {
            total: os.totalmem(),
            free: os.freemem(),
            used: os.totalmem() - os.freemem()
        };
        
        return {
            timestamp,
            process: {
                pid: process.pid,
                heapUsed: usage.heapUsed,
                heapTotal: usage.heapTotal,
                external: usage.external,
                rss: usage.rss,
                heapUsedMB: Math.round(usage.heapUsed / 1024 / 1024),
                heapTotalMB: Math.round(usage.heapTotal / 1024 / 1024),
                heapPercent: (usage.heapUsed / this.config.maxHeapSize) * 100
            },
            system: {
                totalMB: Math.round(systemMem.total / 1024 / 1024),
                freeMB: Math.round(systemMem.free / 1024 / 1024),
                usedMB: Math.round(systemMem.used / 1024 / 1024),
                usagePercent: (systemMem.used / systemMem.total) * 100
            },
            runtime: timestamp - this.state.detectionStarted
        };
    }
    
    detectMemoryLeaks(currentSnapshot) {
        if (this.state.memoryHistory.length < 5) return;
        
        const recentHistory = this.state.memoryHistory.slice(-5);
        const growthAnalysis = this.analyzeMemoryGrowth(recentHistory);
        
        if (growthAnalysis.isLeak) {
            this.handleMemoryLeak(growthAnalysis, currentSnapshot);
        }
    }
    
    analyzeMemoryGrowth(samples) {
        if (samples.length < 2) return { isLeak: false };
        
        const first = samples[0];
        const last = samples[samples.length - 1];
        const timeDelta = last.timestamp - first.timestamp;
        const memoryDelta = last.process.heapUsed - first.process.heapUsed;
        
        // Calculate growth rate (bytes per second)
        const growthRate = memoryDelta / (timeDelta / 1000);
        const growthRateMB = growthRate / 1024 / 1024;
        
        // Calculate trend consistency
        let consistentGrowth = 0;
        for (let i = 1; i < samples.length; i++) {
            if (samples[i].process.heapUsed > samples[i-1].process.heapUsed) {
                consistentGrowth++;
            }
        }
        
        const growthConsistency = consistentGrowth / (samples.length - 1);
        
        // Detect leak based on multiple criteria
        const isLeak = (
            Math.abs(growthRateMB) > (this.config.memoryGrowthThreshold / 60) && // Growth per minute threshold
            growthConsistency >= this.config.leakConfidenceThreshold &&
            memoryDelta > this.config.memoryGrowthThreshold * 1024 * 1024 // Absolute growth threshold
        );
        
        return {
            isLeak,
            growthRate: growthRateMB,
            growthConsistency,
            memoryDeltaMB: Math.round(memoryDelta / 1024 / 1024),
            timeSpanSeconds: Math.round(timeDelta / 1000),
            confidence: growthConsistency,
            severity: this.calculateLeakSeverity(growthRateMB, growthConsistency)
        };
    }
    
    calculateLeakSeverity(growthRateMB, consistency) {
        const magnitude = Math.abs(growthRateMB);
        
        if (magnitude > 100 && consistency > 0.9) return 'CRITICAL';
        if (magnitude > 50 && consistency > 0.8) return 'HIGH';
        if (magnitude > 20 && consistency > 0.7) return 'MEDIUM';
        return 'LOW';
    }
    
    handleMemoryLeak(analysis, snapshot) {
        this.state.leaksDetected++;
        
        const leakEvent = {
            timestamp: snapshot.timestamp,
            type: 'MEMORY_LEAK_DETECTED',
            analysis,
            snapshot,
            remediationApplied: false
        };
        
        this.state.leakPatterns.push(leakEvent);
        
        // Trigger alert
        this.triggerLeakAlert(analysis, snapshot);
        
        // Apply automatic remediation based on severity
        if (analysis.severity === 'CRITICAL' || analysis.severity === 'HIGH') {
            this.applyAutomaticRemediation(analysis, snapshot);
            leakEvent.remediationApplied = true;
        }
        
        this.logEvent('MEMORY_LEAK', `Leak detected: ${analysis.growthRate.toFixed(2)}MB/min growth, ${analysis.severity} severity`);
    }
    
    detectProcessLeaks() {
        try {
            const psOutput = execSync('ps aux | grep -E "(node|python|claude)" | grep -v grep', { encoding: 'utf8' });
            const processes = psOutput.split('\n').filter(line => line.trim());
            
            for (const line of processes) {
                const parts = line.split(/\s+/);
                if (parts.length < 11) continue;
                
                const pid = parseInt(parts[1]);
                const memUsageKB = parseInt(parts[5]);
                const memUsageMB = memUsageKB / 1024;
                const cpuPercent = parseFloat(parts[2]);
                
                if (pid === process.pid) continue;
                
                this.trackProcessMemory(pid, memUsageMB, cpuPercent);
            }
            
            this.analyzeProcessLeaks();
        } catch (error) {
            this.logEvent('ERROR', `Process monitoring error: ${error.message}`);
        }
    }
    
    trackProcessMemory(pid, memUsageMB, cpuPercent) {
        const now = Date.now();
        
        if (!this.state.processHistory.has(pid)) {
            this.state.processHistory.set(pid, {
                pid,
                firstSeen: now,
                memoryHistory: [],
                lastUpdate: now,
                leakDetected: false
            });
        }
        
        const processData = this.state.processHistory.get(pid);
        processData.memoryHistory.push({
            timestamp: now,
            memoryMB: memUsageMB,
            cpuPercent
        });
        
        // Keep only recent history
        if (processData.memoryHistory.length > 20) {
            processData.memoryHistory = processData.memoryHistory.slice(-15);
        }
        
        processData.lastUpdate = now;
    }
    
    analyzeProcessLeaks() {
        const now = Date.now();
        
        for (const [pid, processData] of this.state.processHistory) {
            // Skip recently created processes
            if (now - processData.firstSeen < this.config.processAgeThreshold) continue;
            
            // Clean up stale processes
            if (now - processData.lastUpdate > 60000) { // 1 minute stale
                this.state.processHistory.delete(pid);
                continue;
            }
            
            // Analyze memory growth
            if (processData.memoryHistory.length >= 5) {
                const analysis = this.analyzeProcessMemoryGrowth(processData);
                
                if (analysis.isLeak && !processData.leakDetected) {
                    this.handleProcessLeak(pid, analysis, processData);
                    processData.leakDetected = true;
                }
            }
        }
    }
    
    analyzeProcessMemoryGrowth(processData) {
        const history = processData.memoryHistory;
        if (history.length < 2) return { isLeak: false };
        
        const first = history[0];
        const last = history[history.length - 1];
        const memoryGrowth = last.memoryMB - first.memoryMB;
        const timeSpan = last.timestamp - first.timestamp;
        const growthRate = (memoryGrowth / (timeSpan / 1000)) * 60; // MB per minute
        
        // Check for consistent growth
        let growthCount = 0;
        for (let i = 1; i < history.length; i++) {
            if (history[i].memoryMB > history[i-1].memoryMB) {
                growthCount++;
            }
        }
        
        const consistency = growthCount / (history.length - 1);
        
        const isLeak = (
            growthRate > 5 && // 5MB/min growth
            consistency > 0.7 &&
            memoryGrowth > 50 // 50MB total growth
        );
        
        return {
            isLeak,
            growthRate,
            consistency,
            memoryGrowth,
            timeSpanMinutes: Math.round(timeSpan / 60000),
            severity: growthRate > 20 ? 'HIGH' : growthRate > 10 ? 'MEDIUM' : 'LOW'
        };
    }
    
    handleProcessLeak(pid, analysis, processData) {
        this.logEvent('PROCESS_LEAK', `Process ${pid} leak detected: ${analysis.growthRate.toFixed(2)}MB/min`);
        
        if (analysis.severity === 'HIGH') {
            this.terminateLeakingProcess(pid, analysis);
        } else {
            this.triggerProcessLeakAlert(pid, analysis);
        }
    }
    
    terminateLeakingProcess(pid, analysis) {
        try {
            console.log(`🔪 Terminating leaking process PID ${pid} (${analysis.growthRate.toFixed(2)}MB/min growth)`);
            
            process.kill(pid, 'SIGTERM');
            
            setTimeout(() => {
                try {
                    process.kill(pid, 'SIGKILL');
                } catch (e) {
                    // Process already terminated
                }
            }, 5000);
            
            this.logEvent('PROCESS_TERMINATED', `Terminated leaking process ${pid}`);
            this.state.remediationsPerformed++;
            
        } catch (error) {
            this.logEvent('ERROR', `Failed to terminate process ${pid}: ${error.message}`);
        }
    }
    
    analyzeMemoryPatterns() {
        if (this.state.memoryHistory.length < 10) return;
        
        const recent = this.state.memoryHistory.slice(-10);
        
        // Detect sawtooth pattern (memory spikes)
        const sawtoothPattern = this.detectSawtoothPattern(recent);
        if (sawtoothPattern.detected) {
            this.logEvent('PATTERN_DETECTED', `Sawtooth memory pattern detected (${sawtoothPattern.peaks} peaks)`);
        }
        
        // Detect linear growth pattern
        const linearGrowth = this.detectLinearGrowth(recent);
        if (linearGrowth.detected) {
            this.logEvent('PATTERN_DETECTED', `Linear memory growth detected (${linearGrowth.rate.toFixed(2)}MB/min)`);
        }
    }
    
    detectSawtoothPattern(samples) {
        let peaks = 0;
        let valleys = 0;
        
        for (let i = 1; i < samples.length - 1; i++) {
            const prev = samples[i-1].process.heapUsed;
            const curr = samples[i].process.heapUsed;
            const next = samples[i+1].process.heapUsed;
            
            if (curr > prev && curr > next) peaks++;
            if (curr < prev && curr < next) valleys++;
        }
        
        return {
            detected: peaks >= 3 && valleys >= 2,
            peaks,
            valleys
        };
    }
    
    detectLinearGrowth(samples) {
        if (samples.length < 5) return { detected: false };
        
        const x = samples.map((_, i) => i);
        const y = samples.map(s => s.process.heapUsed);
        
        // Simple linear regression
        const n = samples.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
        
        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;
        
        // Calculate R-squared
        const yMean = sumY / n;
        const ssRes = y.reduce((sum, yi, i) => {
            const predicted = slope * x[i] + intercept;
            return sum + Math.pow(yi - predicted, 2);
        }, 0);
        const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
        const rSquared = 1 - (ssRes / ssTot);
        
        // Convert slope to MB/min
        const timeSpan = samples[samples.length - 1].timestamp - samples[0].timestamp;
        const rateMBPerMin = (slope * (60000 / (timeSpan / (samples.length - 1)))) / 1024 / 1024;
        
        return {
            detected: rSquared > 0.8 && rateMBPerMin > 1, // Strong correlation and growth
            rate: rateMBPerMin,
            correlation: rSquared
        };
    }
    
    checkThresholds(snapshot) {
        const heapPercent = snapshot.process.heapPercent / 100;
        
        if (heapPercent >= this.config.alertThresholds.emergency) {
            this.triggerThresholdAlert('EMERGENCY', snapshot, heapPercent);
            this.applyEmergencyRemediation(snapshot);
        } else if (heapPercent >= this.config.alertThresholds.critical) {
            this.triggerThresholdAlert('CRITICAL', snapshot, heapPercent);
        } else if (heapPercent >= this.config.alertThresholds.warning) {
            this.triggerThresholdAlert('WARNING', snapshot, heapPercent);
        }
    }
    
    triggerLeakAlert(analysis, snapshot) {
        const now = Date.now();
        if (now - this.state.lastAlert < this.config.alertCooldown) return;
        
        this.state.lastAlert = now;
        this.state.alertsTriggered++;
        
        console.log(`🚨 MEMORY LEAK DETECTED`);
        console.log(`   Growth Rate: ${analysis.growthRate.toFixed(2)}MB/min`);
        console.log(`   Severity: ${analysis.severity}`);
        console.log(`   Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
        console.log(`   Current Heap: ${snapshot.process.heapUsedMB}MB`);
    }
    
    triggerProcessLeakAlert(pid, analysis) {
        console.log(`⚠️  Process ${pid} showing memory leak pattern`);
        console.log(`   Growth Rate: ${analysis.growthRate.toFixed(2)}MB/min`);
        console.log(`   Severity: ${analysis.severity}`);
    }
    
    triggerThresholdAlert(level, snapshot, percent) {
        const now = Date.now();
        if (now - this.state.lastAlert < this.config.alertCooldown / 2) return;
        
        this.state.lastAlert = now;
        
        const symbol = level === 'EMERGENCY' ? '💀' : level === 'CRITICAL' ? '🚨' : '⚠️';
        console.log(`${symbol} ${level}: Memory at ${(percent * 100).toFixed(1)}%`);
        console.log(`   Heap Usage: ${snapshot.process.heapUsedMB}MB`);
        
        this.logEvent(`THRESHOLD_${level}`, `Memory threshold exceeded: ${(percent * 100).toFixed(1)}%`);
    }
    
    applyAutomaticRemediation(analysis, snapshot) {
        console.log(`🔧 Applying automatic remediation for ${analysis.severity} leak`);
        
        // Force garbage collection
        if (global.gc) {
            for (let i = 0; i < 3; i++) {
                global.gc();
            }
            console.log('   Forced garbage collection completed');
        }
        
        // Clear caches
        this.clearSystemCaches();
        
        // Terminate excessive processes if needed
        if (analysis.severity === 'CRITICAL') {
            this.terminateExcessiveProcesses();
        }
        
        this.state.remediationsPerformed++;
        this.logEvent('REMEDIATION_APPLIED', `Automatic remediation applied for ${analysis.severity} leak`);
    }
    
    applyEmergencyRemediation(snapshot) {
        console.log('💀 EMERGENCY REMEDIATION - PREVENTING SYSTEM CRASH');
        
        // Aggressive cleanup
        this.clearSystemCaches();
        this.terminateExcessiveProcesses();
        
        // Force multiple GC cycles
        if (global.gc) {
            for (let i = 0; i < 10; i++) {
                global.gc();
            }
        }
        
        // Save emergency state
        this.saveEmergencyState(snapshot);
        
        this.state.remediationsPerformed++;
        this.logEvent('EMERGENCY_REMEDIATION', 'Emergency remediation applied to prevent crash');
    }
    
    clearSystemCaches() {
        // Clear global caches
        ['_claudePMCache', '_deploymentCache', '_memoryCache', '_taskToolCache', '_agentCache'].forEach(cache => {
            if (global[cache] && typeof global[cache].clear === 'function') {
                global[cache].clear();
                global[cache] = null;
            }
        });
        
        // Clear subprocess tracking
        if (global.activeSubprocesses && typeof global.activeSubprocesses.clear === 'function') {
            global.activeSubprocesses.clear();
        }
        
        console.log('   System caches cleared');
    }
    
    terminateExcessiveProcesses() {
        const maxProcesses = 3;
        let terminated = 0;
        
        for (const [pid, processData] of this.state.processHistory) {
            if (terminated >= maxProcesses) break;
            
            const recentMemory = processData.memoryHistory.slice(-1)[0];
            if (recentMemory && recentMemory.memoryMB > 500) { // 500MB threshold
                try {
                    process.kill(pid, 'SIGTERM');
                    terminated++;
                    console.log(`   Terminated excessive process ${pid} (${recentMemory.memoryMB}MB)`);
                } catch (error) {
                    // Process may already be terminated
                }
            }
        }
        
        if (terminated > 0) {
            console.log(`   Terminated ${terminated} excessive processes`);
        }
    }
    
    saveEmergencyState(snapshot) {
        const emergencyState = {
            timestamp: new Date().toISOString(),
            reason: 'emergency_memory_threshold_exceeded',
            snapshot,
            memoryHistory: this.state.memoryHistory.slice(-10),
            leakPatterns: this.state.leakPatterns.slice(-5),
            processHistory: Array.from(this.state.processHistory.entries()).slice(0, 5)
        };
        
        const emergencyFile = path.join(process.cwd(), 'logs', 'emergency-leak-state.json');
        fs.writeFileSync(emergencyFile, JSON.stringify(emergencyState, null, 2));
        console.log(`   Emergency state saved to: ${emergencyFile}`);
    }
    
    updateDetectionReport() {
        const report = {
            timestamp: new Date().toISOString(),
            session: {
                started: new Date(this.state.detectionStarted).toISOString(),
                durationMinutes: Math.round((Date.now() - this.state.detectionStarted) / 60000),
                leaksDetected: this.state.leaksDetected,
                alertsTriggered: this.state.alertsTriggered,
                remediationsPerformed: this.state.remediationsPerformed
            },
            currentStatus: this.state.memoryHistory.length > 0 ? this.state.memoryHistory[this.state.memoryHistory.length - 1] : null,
            recentLeaks: this.state.leakPatterns.slice(-5),
            activeProcesses: this.state.processHistory.size,
            configuration: this.config
        };
        
        fs.writeFileSync(this.reportFile, JSON.stringify(report, null, 2));
    }
    
    logEvent(type, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            type,
            message,
            data,
            memoryUsage: process.memoryUsage()
        };
        
        fs.appendFileSync(this.logFile, JSON.stringify(logEntry) + '\n');
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
        console.log('🛑 Memory leak detector shutting down...');
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        this.generateFinalReport();
        this.logEvent('DETECTION_STOPPED', 'Memory leak detection system shutdown');
    }
    
    generateFinalReport() {
        const finalReport = {
            session: {
                started: new Date(this.state.detectionStarted).toISOString(),
                ended: new Date().toISOString(),
                duration: Date.now() - this.state.detectionStarted,
                totalLeaksDetected: this.state.leaksDetected,
                totalAlertsTriggered: this.state.alertsTriggered,
                totalRemediationsPerformed: this.state.remediationsPerformed
            },
            configuration: this.config,
            memoryHistory: this.state.memoryHistory,
            leakPatterns: this.state.leakPatterns,
            processHistory: Array.from(this.state.processHistory.entries()),
            finalMemoryUsage: process.memoryUsage()
        };
        
        const finalReportPath = path.join(process.cwd(), 'logs', `leak-detection-final-${Date.now()}.json`);
        fs.writeFileSync(finalReportPath, JSON.stringify(finalReport, null, 2));
        console.log(`📊 Final leak detection report saved: ${finalReportPath}`);
    }
}

// CLI Interface
if (require.main === module) {
    const detector = new MemoryLeakDetector();
    
    console.log('🔍 Memory Leak Detector Active - Press Ctrl+C to stop');
    console.log('📊 Advanced pattern analysis enabled');
    console.log('🔧 Automatic remediation available');
    
    // Keep process alive
    setInterval(() => {
        // Detection runs in background
    }, 60000);
}

module.exports = MemoryLeakDetector;
