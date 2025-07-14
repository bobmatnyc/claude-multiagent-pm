#!/usr/bin/env node

/**
 * Claude PM Framework - Memory Guard System for Task Tool Subprocess Creation
 * 
 * Implements memory constraints and isolation for subprocess operations
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class MemoryGuard {
    constructor() {
        this.config = {
            maxTotalMemory: 8 * 1024 * 1024 * 1024,    // 8GB total system limit
            subprocessMemoryLimit: 2 * 1024 * 1024 * 1024, // 2GB per subprocess
            maxConcurrentSubprocesses: 4,               // Maximum simultaneous subprocesses
            memoryCheckInterval: 10000,                 // Check every 10 seconds
            emergencyTerminationThreshold: 0.9,         // 90% of subprocess limit
            warningThreshold: 0.75,                     // 75% of subprocess limit
            processTimeout: 300000,                     // 5 minute default timeout
            cleanupGracePeriod: 10000                   // 10 second grace period for cleanup
        };
        
        this.state = {
            activeSubprocesses: new Map(),
            memoryAllocations: new Map(),
            startupTimes: new Map(),
            terminationQueue: new Set(),
            totalMemoryUsed: 0,
            lastCleanup: 0
        };
        
        this.setupGuard();
    }
    
    setupGuard() {
        console.log('🛡️ Memory Guard System - Initializing Subprocess Protection');
        console.log(`📊 Configuration:`);
        console.log(`   Total Memory Limit: ${Math.round(this.config.maxTotalMemory / 1024 / 1024 / 1024)}GB`);
        console.log(`   Subprocess Limit: ${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024 / 1024)}GB each`);
        console.log(`   Max Concurrent: ${this.config.maxConcurrentSubprocesses}`);
        console.log(`   Process Timeout: ${this.config.processTimeout / 1000}s`);
        
        this.startMemoryMonitoring();
        this.setupSignalHandlers();
        this.initializeLogging();
    }
    
    startMemoryMonitoring() {
        this.monitoringInterval = setInterval(() => {
            this.monitorSubprocessMemory();
            this.enforceMemoryLimits();
            this.cleanupCompletedProcesses();
        }, this.config.memoryCheckInterval);
        
        console.log('✅ Memory monitoring active');
    }
    
    /**
     * Create a memory-protected subprocess for Task Tool operations
     */
    async createProtectedSubprocess(command, args = [], options = {}) {
        // Check if we can create another subprocess
        const canCreate = await this.checkSubprocessCreationPermission();
        if (!canCreate.allowed) {
            throw new Error(`Subprocess creation denied: ${canCreate.reason}`);
        }
        
        // Set memory limits for the subprocess
        const protectedOptions = this.applyMemoryProtections(options);
        
        console.log(`🚀 Creating protected subprocess: ${command} ${args.join(' ')}`);
        console.log(`   Memory limit: ${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024)}MB`);
        console.log(`   Timeout: ${protectedOptions.timeout || this.config.processTimeout}ms`);
        
        const subprocess = spawn(command, args, protectedOptions);
        const pid = subprocess.pid;
        
        // Register subprocess with memory tracking
        this.registerSubprocess(pid, subprocess, command, args);
        
        // Set up monitoring for this specific subprocess
        this.setupSubprocessMonitoring(pid, subprocess);
        
        return subprocess;
    }
    
    async checkSubprocessCreationPermission() {
        // Check concurrent subprocess limit
        if (this.state.activeSubprocesses.size >= this.config.maxConcurrentSubprocesses) {
            return {
                allowed: false,
                reason: `Maximum concurrent subprocesses reached (${this.state.activeSubprocesses.size}/${this.config.maxConcurrentSubprocesses})`
            };
        }
        
        // Check total memory usage
        const currentUsage = process.memoryUsage();
        const systemMemory = this.getSystemMemoryInfo();
        
        if (currentUsage.heapUsed > this.config.maxTotalMemory * 0.8) {
            return {
                allowed: false,
                reason: `Main process memory usage too high (${Math.round(currentUsage.heapUsed / 1024 / 1024)}MB)`
            };
        }
        
        if (systemMemory.available < this.config.subprocessMemoryLimit * 1.5) {
            return {
                allowed: false,
                reason: `Insufficient system memory (${Math.round(systemMemory.available / 1024 / 1024)}MB available)`
            };
        }
        
        return { allowed: true };
    }
    
    applyMemoryProtections(options) {
        const protectedOptions = { ...options };
        
        // Set memory limit environment variables
        protectedOptions.env = {
            ...process.env,
            ...protectedOptions.env,
            NODE_OPTIONS: `--max-old-space-size=${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024)} --expose-gc`,
            MEMORY_LIMIT: this.config.subprocessMemoryLimit.toString(),
            SUBPROCESS_MEMORY_GUARD: 'true'
        };
        
        // Set default timeout
        if (!protectedOptions.timeout) {
            protectedOptions.timeout = this.config.processTimeout;
        }
        
        // Ensure stdio is configured for monitoring
        if (!protectedOptions.stdio) {
            protectedOptions.stdio = ['pipe', 'pipe', 'pipe'];
        }
        
        return protectedOptions;
    }
    
    registerSubprocess(pid, subprocess, command, args) {
        const registrationTime = Date.now();
        
        this.state.activeSubprocesses.set(pid, {
            pid,
            subprocess,
            command,
            args,
            startTime: registrationTime,
            lastMemoryCheck: registrationTime,
            memoryUsage: 0,
            peakMemoryUsage: 0,
            status: 'running',
            timeouts: 0,
            warnings: 0
        });
        
        this.state.startupTimes.set(pid, registrationTime);
        
        console.log(`📝 Registered subprocess PID ${pid}: ${command}`);
        this.logSubprocessEvent(pid, 'CREATED', { command, args });
    }
    
    setupSubprocessMonitoring(pid, subprocess) {
        // Monitor subprocess completion
        subprocess.on('exit', (code, signal) => {
            this.handleSubprocessExit(pid, code, signal);
        });
        
        subprocess.on('error', (error) => {
            this.handleSubprocessError(pid, error);
        });
        
        // Set up timeout protection
        const timeout = setTimeout(() => {
            this.handleSubprocessTimeout(pid);
        }, this.config.processTimeout);
        
        if (this.state.activeSubprocesses.has(pid)) {
            this.state.activeSubprocesses.get(pid).timeout = timeout;
        }
    }
    
    monitorSubprocessMemory() {
        if (this.state.activeSubprocesses.size === 0) return;
        
        try {
            const psOutput = execSync('ps -o pid,rss,pcpu,etime,comm -p ' + Array.from(this.state.activeSubprocesses.keys()).join(','), 
                { encoding: 'utf8', timeout: 5000 });
            
            const lines = psOutput.trim().split('\n').slice(1); // Skip header
            
            for (const line of lines) {
                const parts = line.trim().split(/\s+/);
                if (parts.length < 5) continue;
                
                const pid = parseInt(parts[0]);
                const memoryKB = parseInt(parts[1]);
                const memoryBytes = memoryKB * 1024;
                const cpuPercent = parseFloat(parts[2]);
                const elapsedTime = parts[3];
                const command = parts[4];
                
                if (this.state.activeSubprocesses.has(pid)) {
                    this.updateSubprocessMemory(pid, memoryBytes, cpuPercent, elapsedTime);
                }
            }
        } catch (error) {
            console.log(`⚠️ Error monitoring subprocess memory: ${error.message}`);
        }
    }
    
    updateSubprocessMemory(pid, memoryBytes, cpuPercent, elapsedTime) {
        const subprocessData = this.state.activeSubprocesses.get(pid);
        if (!subprocessData) return;
        
        const previousMemory = subprocessData.memoryUsage;
        subprocessData.memoryUsage = memoryBytes;
        subprocessData.peakMemoryUsage = Math.max(subprocessData.peakMemoryUsage, memoryBytes);
        subprocessData.cpuPercent = cpuPercent;
        subprocessData.elapsedTime = elapsedTime;
        subprocessData.lastMemoryCheck = Date.now();
        
        const memoryMB = Math.round(memoryBytes / 1024 / 1024);
        const limitMB = Math.round(this.config.subprocessMemoryLimit / 1024 / 1024);
        const memoryPercent = memoryBytes / this.config.subprocessMemoryLimit;
        
        // Log memory usage changes
        if (Math.abs(memoryBytes - previousMemory) > 50 * 1024 * 1024) { // 50MB change
            console.log(`📊 PID ${pid}: ${memoryMB}MB (${Math.round(memoryPercent * 100)}% of limit) CPU: ${cpuPercent}%`);
        }
        
        // Check for memory limit violations
        if (memoryPercent >= this.config.emergencyTerminationThreshold) {
            this.handleMemoryViolation(pid, memoryBytes, 'CRITICAL');
        } else if (memoryPercent >= this.config.warningThreshold) {
            this.handleMemoryViolation(pid, memoryBytes, 'WARNING');
        }
        
        this.logSubprocessEvent(pid, 'MEMORY_UPDATE', {
            memoryMB,
            memoryPercent: Math.round(memoryPercent * 100),
            cpuPercent,
            elapsedTime
        });
    }
    
    enforceMemoryLimits() {
        for (const [pid, data] of this.state.activeSubprocesses) {
            if (data.memoryUsage > this.config.subprocessMemoryLimit) {
                console.log(`🚨 PID ${pid} exceeded memory limit - terminating immediately`);
                this.terminateSubprocess(pid, 'MEMORY_LIMIT_EXCEEDED');
            }
        }
        
        // Check total system memory usage
        const totalSubprocessMemory = Array.from(this.state.activeSubprocesses.values())
            .reduce((sum, data) => sum + data.memoryUsage, 0);
        
        if (totalSubprocessMemory > this.config.maxTotalMemory * 0.8) {
            console.log(`⚠️ Total subprocess memory usage high (${Math.round(totalSubprocessMemory / 1024 / 1024)}MB) - triggering cleanup`);
            this.emergencyCleanup();
        }
    }
    
    handleMemoryViolation(pid, memoryBytes, severity) {
        const data = this.state.activeSubprocesses.get(pid);
        if (!data) return;
        
        const memoryMB = Math.round(memoryBytes / 1024 / 1024);
        const limitMB = Math.round(this.config.subprocessMemoryLimit / 1024 / 1024);
        
        if (severity === 'CRITICAL') {
            console.log(`🚨 CRITICAL: PID ${pid} using ${memoryMB}MB (limit: ${limitMB}MB) - terminating`);
            this.terminateSubprocess(pid, 'MEMORY_VIOLATION');
        } else if (severity === 'WARNING') {
            data.warnings++;
            console.log(`⚠️ WARNING: PID ${pid} using ${memoryMB}MB (${Math.round((memoryBytes / this.config.subprocessMemoryLimit) * 100)}% of limit)`);
            
            // Terminate if too many warnings
            if (data.warnings >= 3) {
                console.log(`🔄 PID ${pid} exceeded warning threshold - terminating`);
                this.terminateSubprocess(pid, 'REPEATED_WARNINGS');
            }
        }
        
        this.logSubprocessEvent(pid, 'MEMORY_VIOLATION', {
            severity,
            memoryMB,
            limitMB,
            warningCount: data.warnings
        });
    }
    
    terminateSubprocess(pid, reason) {
        const data = this.state.activeSubprocesses.get(pid);
        if (!data || this.state.terminationQueue.has(pid)) return;
        
        console.log(`🔪 Terminating subprocess PID ${pid}: ${reason}`);
        this.state.terminationQueue.add(pid);
        
        try {
            // Clear timeout
            if (data.timeout) {
                clearTimeout(data.timeout);
            }
            
            // Send SIGTERM first
            data.subprocess.kill('SIGTERM');
            console.log(`   Sent SIGTERM to PID ${pid}`);
            
            // Force kill after grace period
            setTimeout(() => {
                if (this.state.activeSubprocesses.has(pid)) {
                    try {
                        data.subprocess.kill('SIGKILL');
                        console.log(`   Sent SIGKILL to PID ${pid}`);
                    } catch (error) {
                        // Process already dead
                    }
                }
            }, this.config.cleanupGracePeriod);
            
            this.logSubprocessEvent(pid, 'TERMINATED', { reason });
            
        } catch (error) {
            console.log(`   Error terminating PID ${pid}: ${error.message}`);
        }
    }
    
    handleSubprocessExit(pid, code, signal) {
        const data = this.state.activeSubprocesses.get(pid);
        if (!data) return;
        
        const duration = Date.now() - data.startTime;
        const peakMemoryMB = Math.round(data.peakMemoryUsage / 1024 / 1024);
        
        console.log(`✅ Subprocess PID ${pid} exited (code: ${code}, signal: ${signal})`);
        console.log(`   Duration: ${Math.round(duration / 1000)}s, Peak memory: ${peakMemoryMB}MB`);
        
        this.cleanupSubprocess(pid);
        this.logSubprocessEvent(pid, 'EXITED', { code, signal, duration, peakMemoryMB });
    }
    
    handleSubprocessError(pid, error) {
        console.log(`❌ Subprocess PID ${pid} error: ${error.message}`);
        this.cleanupSubprocess(pid);
        this.logSubprocessEvent(pid, 'ERROR', { error: error.message });
    }
    
    handleSubprocessTimeout(pid) {
        const data = this.state.activeSubprocesses.get(pid);
        if (!data) return;
        
        data.timeouts++;
        console.log(`⏰ Subprocess PID ${pid} timeout (${data.timeouts} timeouts)`);
        
        this.terminateSubprocess(pid, 'TIMEOUT');
    }
    
    cleanupSubprocess(pid) {
        const data = this.state.activeSubprocesses.get(pid);
        if (!data) return;
        
        // Clear timeout
        if (data.timeout) {
            clearTimeout(data.timeout);
        }
        
        // Remove from tracking
        this.state.activeSubprocesses.delete(pid);
        this.state.memoryAllocations.delete(pid);
        this.state.startupTimes.delete(pid);
        this.state.terminationQueue.delete(pid);
        
        console.log(`🧹 Cleaned up subprocess PID ${pid}`);
    }
    
    cleanupCompletedProcesses() {
        const now = Date.now();
        const staleThreshold = 60000; // 1 minute
        
        for (const [pid, data] of this.state.activeSubprocesses) {
            if (now - data.lastMemoryCheck > staleThreshold) {
                console.log(`🧹 Cleaning up stale subprocess PID ${pid}`);
                this.cleanupSubprocess(pid);
            }
        }
    }
    
    emergencyCleanup() {
        console.log('🚨 EMERGENCY CLEANUP: Terminating all subprocesses');
        
        // Sort subprocesses by memory usage (highest first)
        const sortedProcesses = Array.from(this.state.activeSubprocesses.entries())
            .sort(([,a], [,b]) => b.memoryUsage - a.memoryUsage);
        
        // Terminate the most memory-intensive processes first
        for (const [pid, data] of sortedProcesses) {
            this.terminateSubprocess(pid, 'EMERGENCY_CLEANUP');
        }
        
        this.state.lastCleanup = Date.now();
    }
    
    getSystemMemoryInfo() {
        const total = os.totalmem();
        const free = os.freemem();
        return {
            total,
            free,
            used: total - free,
            available: free
        };
    }
    
    initializeLogging() {
        this.logFile = path.join(process.cwd(), 'logs', 'memory-guard.log');
        fs.mkdirSync(path.dirname(this.logFile), { recursive: true });
        
        console.log(`📝 Memory guard logging to: ${this.logFile}`);
    }
    
    logSubprocessEvent(pid, event, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            pid,
            event,
            data,
            activeSubprocesses: this.state.activeSubprocesses.size,
            totalMemoryUsage: Array.from(this.state.activeSubprocesses.values())
                .reduce((sum, proc) => sum + proc.memoryUsage, 0)
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
        console.log('🛑 Memory guard shutting down...');
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
        
        // Terminate all active subprocesses gracefully
        for (const [pid, data] of this.state.activeSubprocesses) {
            try {
                data.subprocess.kill('SIGTERM');
                console.log(`   Terminated subprocess PID ${pid}`);
            } catch (error) {
                // Ignore errors during shutdown
            }
        }
        
        // Generate final report
        this.generateShutdownReport();
        
        console.log('✅ Memory guard shutdown complete');
    }
    
    generateShutdownReport() {
        const reportPath = path.join(process.cwd(), 'logs', `memory-guard-report-${Date.now()}.json`);
        const report = {
            timestamp: new Date().toISOString(),
            configuration: this.config,
            finalState: {
                activeSubprocesses: this.state.activeSubprocesses.size,
                totalMemoryUsed: this.state.totalMemoryUsed,
                lastCleanup: this.state.lastCleanup
            },
            systemMemory: this.getSystemMemoryInfo(),
            subprocessSummary: Array.from(this.state.activeSubprocesses.values()).map(data => ({
                pid: data.pid,
                command: data.command,
                duration: Date.now() - data.startTime,
                peakMemoryMB: Math.round(data.peakMemoryUsage / 1024 / 1024),
                warnings: data.warnings,
                timeouts: data.timeouts
            }))
        };
        
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`📊 Shutdown report saved: ${reportPath}`);
    }
    
    getStatus() {
        return {
            activeSubprocesses: this.state.activeSubprocesses.size,
            maxConcurrent: this.config.maxConcurrentSubprocesses,
            totalMemoryUsedMB: Math.round(Array.from(this.state.activeSubprocesses.values())
                .reduce((sum, data) => sum + data.memoryUsage, 0) / 1024 / 1024),
            systemMemory: this.getSystemMemoryInfo(),
            recentTerminations: this.state.terminationQueue.size
        };
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    const guard = new MemoryGuard();
    
    switch (command) {
        case 'monitor':
            console.log('🛡️ Memory Guard - Active Monitoring Mode');
            console.log('Press Ctrl+C to stop');
            setInterval(() => {
                const status = guard.getStatus();
                console.log(`📊 Status: ${status.activeSubprocesses}/${status.maxConcurrent} subprocesses, ${status.totalMemoryUsedMB}MB used`);
            }, 30000);
            break;
            
        case 'status':
            const status = guard.getStatus();
            console.log('📊 Memory Guard Status:');
            console.log(JSON.stringify(status, null, 2));
            process.exit(0);
            break;
            
        default:
            console.log(`
🛡️ Claude PM Framework - Memory Guard System

Usage:
  node memory-guard.js <command>

Commands:
  monitor     Start continuous monitoring
  status      Show current status

Examples:
  node memory-guard.js monitor
  node memory-guard.js status
            `);
            process.exit(1);
    }
}

module.exports = MemoryGuard;