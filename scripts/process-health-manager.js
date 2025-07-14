#!/usr/bin/env node

/**
 * Claude PM Framework - Process Health Manager
 * 
 * Comprehensive process health monitoring with memory-based restart policies
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const os = require('os');

class ProcessHealthManager {
    constructor() {
        this.config = {
            healthCheckInterval: 15000,      // 15 seconds
            memoryThresholds: {
                restart: 3.0 * 1024 * 1024 * 1024,    // 3GB restart threshold
                warning: 2.5 * 1024 * 1024 * 1024,    // 2.5GB warning
                critical: 3.5 * 1024 * 1024 * 1024    // 3.5GB critical
            },
            processLimits: {
                maxUptime: 6 * 60 * 60 * 1000,        // 6 hours max uptime
                maxRestarts: 5,                        // Max restarts per hour
                cooldownPeriod: 60000,                 // 1 minute between restarts
                maxConcurrentProcesses: 4              // Max processes to monitor
            },
            systemThresholds: {
                maxSystemMemoryUsage: 0.85,           // 85% system memory
                maxCpuUsage: 80,                       // 80% CPU usage
                minFreeDiskSpace: 1024 * 1024 * 1024   // 1GB free disk
            },
            alerting: {
                cooldownPeriod: 300000,                // 5 minutes between alerts
                escalationThreshold: 3,                // Escalate after 3 alerts
                notificationChannels: ['console', 'file', 'dashboard']
            }
        };
        
        this.state = {
            monitoredProcesses: new Map(),
            healthHistory: [],
            restartHistory: [],
            alertHistory: [],
            lastHealthCheck: 0,
            lastAlert: 0,
            systemHealth: {},
            startTime: Date.now()
        };
        
        this.logFile = path.join(process.cwd(), 'logs', 'process-health.log');
        this.healthReportFile = path.join(process.cwd(), 'logs', 'health-report.json');
        this.restartPolicyFile = path.join(process.cwd(), 'logs', 'restart-policies.json');
        
        this.ensureLogsDirectory();
        this.loadRestartPolicies();
        this.startHealthMonitoring();
    }
    
    ensureLogsDirectory() {
        const logsDir = path.dirname(this.logFile);
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }
    }
    
    loadRestartPolicies() {
        try {
            if (fs.existsSync(this.restartPolicyFile)) {
                const policies = JSON.parse(fs.readFileSync(this.restartPolicyFile, 'utf8'));
                this.restartPolicies = policies;
                console.log('✅ Loaded existing restart policies');
            } else {
                this.restartPolicies = this.createDefaultRestartPolicies();
                this.saveRestartPolicies();
            }
        } catch (error) {
            console.log('⚠️  Error loading restart policies, using defaults');
            this.restartPolicies = this.createDefaultRestartPolicies();
        }
    }
    
    createDefaultRestartPolicies() {
        return {
            'claude-pm': {
                enabled: true,
                memoryThreshold: 2.5 * 1024 * 1024 * 1024,  // 2.5GB
                maxUptime: 4 * 60 * 60 * 1000,              // 4 hours
                maxRestarts: 3,
                restartCommand: 'claude-pm',
                environment: process.env
            },
            'memory-monitor': {
                enabled: true,
                memoryThreshold: 1.0 * 1024 * 1024 * 1024,  // 1GB
                maxUptime: 24 * 60 * 60 * 1000,             // 24 hours
                maxRestarts: 5,
                restartCommand: 'node scripts/memory-monitor.js',
                environment: process.env
            },
            'leak-detector': {
                enabled: true,
                memoryThreshold: 800 * 1024 * 1024,         // 800MB
                maxUptime: 12 * 60 * 60 * 1000,             // 12 hours
                maxRestarts: 3,
                restartCommand: 'node scripts/memory-leak-detector.js',
                environment: process.env
            }
        };
    }
    
    saveRestartPolicies() {
        fs.writeFileSync(this.restartPolicyFile, JSON.stringify(this.restartPolicies, null, 2));
    }
    
    startHealthMonitoring() {
        console.log('🏥 Process Health Manager - Starting Comprehensive Monitoring');
        console.log(`📊 Configuration:`);
        console.log(`   Health Check Interval: ${this.config.healthCheckInterval}ms`);
        console.log(`   Memory Restart Threshold: ${Math.round(this.config.memoryThresholds.restart / 1024 / 1024 / 1024)}GB`);
        console.log(`   Max Concurrent Processes: ${this.config.processLimits.maxConcurrentProcesses}`);
        console.log(`   System Memory Threshold: ${this.config.systemThresholds.maxSystemMemoryUsage * 100}%`);
        
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, this.config.healthCheckInterval);
        
        this.setupSignalHandlers();
        this.logEvent('HEALTH_MONITORING_STARTED', 'Process health monitoring system initialized');
        
        // Start monitoring main process
        this.registerProcess(process.pid, 'main-process', {
            command: 'claude-pm-main',
            startTime: Date.now()
        });
    }
    
    registerProcess(pid, name, metadata = {}) {
        const processInfo = {
            pid,
            name,
            startTime: metadata.startTime || Date.now(),
            command: metadata.command || 'unknown',
            memoryHistory: [],
            cpuHistory: [],
            restartCount: 0,
            lastRestart: 0,
            healthStatus: 'healthy',
            alertCount: 0,
            lastAlert: 0,
            policy: this.restartPolicies[name] || this.createDefaultPolicy(name)
        };
        
        this.state.monitoredProcesses.set(pid, processInfo);
        this.logEvent('PROCESS_REGISTERED', `Registered process ${name} (PID: ${pid})`);
        
        console.log(`📝 Registered process: ${name} (PID: ${pid})`);
    }
    
    createDefaultPolicy(name) {
        return {
            enabled: true,
            memoryThreshold: this.config.memoryThresholds.restart,
            maxUptime: this.config.processLimits.maxUptime,
            maxRestarts: this.config.processLimits.maxRestarts,
            restartCommand: name,
            environment: process.env
        };
    }
    
    performHealthCheck() {
        const timestamp = Date.now();
        this.state.lastHealthCheck = timestamp;
        
        // Check system health
        const systemHealth = this.checkSystemHealth();
        this.state.systemHealth = systemHealth;
        
        // Check individual processes
        this.checkProcessHealth(timestamp);
        
        // Check for system-wide issues
        this.checkSystemThresholds(systemHealth);
        
        // Clean up stale processes
        this.cleanupStaleProcesses();
        
        // Update health report
        this.updateHealthReport();
        
        // Log health check completion
        if (this.state.healthHistory.length % 20 === 0) { // Every 5 minutes
            console.log(`🏥 Health check completed - ${this.state.monitoredProcesses.size} processes monitored`);
        }
    }
    
    checkSystemHealth() {
        const systemMem = {
            total: os.totalmem(),
            free: os.freemem(),
            used: os.totalmem() - os.freemem()
        };
        
        let cpuUsage = 0;
        try {
            const cpuData = os.loadavg()[0]; // 1-minute load average
            cpuUsage = Math.min(cpuData * 10, 100); // Rough CPU percentage
        } catch (error) {
            cpuUsage = 0;
        }
        
        let diskSpace = 0;
        try {
            const dfOutput = execSync('df -h / | tail -1', { encoding: 'utf8' });
            const parts = dfOutput.split(/\s+/);
            const available = parts[3];
            diskSpace = this.parseSize(available);
        } catch (error) {
            diskSpace = 0;
        }
        
        return {
            timestamp: Date.now(),
            memory: {
                totalGB: Math.round(systemMem.total / 1024 / 1024 / 1024),
                freeGB: Math.round(systemMem.free / 1024 / 1024 / 1024),
                usedGB: Math.round(systemMem.used / 1024 / 1024 / 1024),
                usagePercent: (systemMem.used / systemMem.total) * 100
            },
            cpu: {
                usagePercent: cpuUsage,
                loadAverage: os.loadavg()
            },
            disk: {
                availableBytes: diskSpace,
                availableGB: Math.round(diskSpace / 1024 / 1024 / 1024)
            },
            uptime: os.uptime()
        };
    }
    
    parseSize(sizeStr) {
        const units = { 'K': 1024, 'M': 1024*1024, 'G': 1024*1024*1024, 'T': 1024*1024*1024*1024 };
        const match = sizeStr.match(/^([0-9.]+)([KMGT]?)/);
        if (!match) return 0;
        
        const value = parseFloat(match[1]);
        const unit = match[2] || '';
        return value * (units[unit] || 1);
    }
    
    checkProcessHealth(timestamp) {
        try {
            const psOutput = execSync('ps aux | grep -E "(node|python|claude)" | grep -v grep', { encoding: 'utf8' });
            const runningProcesses = new Set();
            
            const processes = psOutput.split('\n').filter(line => line.trim());
            
            for (const line of processes) {
                const parts = line.split(/\s+/);
                if (parts.length < 11) continue;
                
                const pid = parseInt(parts[1]);
                const memUsageKB = parseInt(parts[5]);
                const memUsageBytes = memUsageKB * 1024;
                const cpuPercent = parseFloat(parts[2]);
                
                runningProcesses.add(pid);
                
                if (this.state.monitoredProcesses.has(pid)) {
                    this.updateProcessHealth(pid, memUsageBytes, cpuPercent, timestamp);
                } else {
                    // Auto-register significant processes
                    if (memUsageBytes > 100 * 1024 * 1024) { // 100MB threshold
                        this.autoRegisterProcess(pid, memUsageBytes, parts);
                    }
                }
            }
            
            // Mark missing processes as potentially terminated
            for (const [pid, processInfo] of this.state.monitoredProcesses) {
                if (!runningProcesses.has(pid)) {
                    this.handleMissingProcess(pid, processInfo);
                }
            }
            
        } catch (error) {
            this.logEvent('ERROR', `Process health check failed: ${error.message}`);
        }
    }
    
    updateProcessHealth(pid, memUsageBytes, cpuPercent, timestamp) {
        const processInfo = this.state.monitoredProcesses.get(pid);
        
        // Update memory and CPU history
        processInfo.memoryHistory.push({
            timestamp,
            memoryBytes: memUsageBytes,
            memoryMB: Math.round(memUsageBytes / 1024 / 1024)
        });
        
        processInfo.cpuHistory.push({
            timestamp,
            cpuPercent
        });
        
        // Keep only recent history
        if (processInfo.memoryHistory.length > 100) {
            processInfo.memoryHistory = processInfo.memoryHistory.slice(-50);
        }
        if (processInfo.cpuHistory.length > 100) {
            processInfo.cpuHistory = processInfo.cpuHistory.slice(-50);
        }
        
        // Check health thresholds
        this.evaluateProcessHealth(pid, processInfo, memUsageBytes, cpuPercent, timestamp);
    }
    
    evaluateProcessHealth(pid, processInfo, memUsageBytes, cpuPercent, timestamp) {
        const uptime = timestamp - processInfo.startTime;
        const policy = processInfo.policy;
        
        let healthIssues = [];
        let newHealthStatus = 'healthy';
        
        // Check memory threshold
        if (memUsageBytes > policy.memoryThreshold) {
            healthIssues.push(`memory_threshold_exceeded:${Math.round(memUsageBytes / 1024 / 1024)}MB`);
            newHealthStatus = 'unhealthy';
        }
        
        // Check uptime limit
        if (uptime > policy.maxUptime) {
            healthIssues.push(`max_uptime_exceeded:${Math.round(uptime / 60000)}min`);
            newHealthStatus = 'unhealthy';
        }
        
        // Check for memory leaks (consistent growth)
        if (processInfo.memoryHistory.length >= 10) {
            const memoryGrowth = this.analyzeMemoryGrowth(processInfo.memoryHistory);
            if (memoryGrowth.isLeak) {
                healthIssues.push(`memory_leak_detected:${memoryGrowth.growthRate.toFixed(2)}MB/min`);
                newHealthStatus = 'critical';
            }
        }
        
        // Check CPU usage
        if (cpuPercent > 90) {
            healthIssues.push(`high_cpu_usage:${cpuPercent}%`);
            if (newHealthStatus === 'healthy') newHealthStatus = 'warning';
        }
        
        // Update health status
        const previousStatus = processInfo.healthStatus;
        processInfo.healthStatus = newHealthStatus;
        
        // Handle health status changes
        if (newHealthStatus !== previousStatus) {
            this.handleHealthStatusChange(pid, processInfo, previousStatus, newHealthStatus, healthIssues);
        }
        
        // Apply restart policies if needed
        if (newHealthStatus === 'unhealthy' || newHealthStatus === 'critical') {
            this.considerProcessRestart(pid, processInfo, healthIssues);
        }
    }
    
    analyzeMemoryGrowth(memoryHistory) {
        if (memoryHistory.length < 5) return { isLeak: false };
        
        const recent = memoryHistory.slice(-10);
        const first = recent[0];
        const last = recent[recent.length - 1];
        
        const timeDelta = last.timestamp - first.timestamp;
        const memoryDelta = last.memoryBytes - first.memoryBytes;
        const growthRate = (memoryDelta / (timeDelta / 1000)) / 1024 / 1024 * 60; // MB per minute
        
        // Check for consistent growth
        let growthCount = 0;
        for (let i = 1; i < recent.length; i++) {
            if (recent[i].memoryBytes > recent[i-1].memoryBytes) {
                growthCount++;
            }
        }
        
        const consistency = growthCount / (recent.length - 1);
        
        return {
            isLeak: growthRate > 5 && consistency > 0.7, // 5MB/min with 70% consistency
            growthRate,
            consistency
        };
    }
    
    handleHealthStatusChange(pid, processInfo, previousStatus, newStatus, issues) {
        const event = {
            pid,
            name: processInfo.name,
            previousStatus,
            newStatus,
            issues,
            timestamp: Date.now()
        };
        
        this.logEvent('HEALTH_STATUS_CHANGE', `Process ${processInfo.name} (${pid}): ${previousStatus} → ${newStatus}`, event);
        
        // Trigger alerts for significant status changes
        if (newStatus === 'critical' || (previousStatus === 'healthy' && newStatus === 'unhealthy')) {
            this.triggerHealthAlert(pid, processInfo, newStatus, issues);
        }
    }
    
    considerProcessRestart(pid, processInfo, issues) {
        const now = Date.now();
        const policy = processInfo.policy;
        
        // Check if restart is enabled and within limits
        if (!policy.enabled) {
            this.logEvent('RESTART_SKIPPED', `Restart disabled for ${processInfo.name}`);
            return;
        }
        
        if (processInfo.restartCount >= policy.maxRestarts) {
            this.logEvent('RESTART_LIMIT_EXCEEDED', `Max restarts (${policy.maxRestarts}) exceeded for ${processInfo.name}`);
            this.triggerEscalationAlert(pid, processInfo, 'max_restarts_exceeded');
            return;
        }
        
        if (now - processInfo.lastRestart < this.config.processLimits.cooldownPeriod) {
            this.logEvent('RESTART_COOLDOWN', `Restart cooldown active for ${processInfo.name}`);
            return;
        }
        
        // Check for critical issues that require immediate restart
        const criticalIssues = issues.filter(issue => 
            issue.includes('memory_threshold_exceeded') ||
            issue.includes('memory_leak_detected') ||
            issue.includes('max_uptime_exceeded')
        );
        
        if (criticalIssues.length > 0) {
            this.performProcessRestart(pid, processInfo, criticalIssues);
        }
    }
    
    performProcessRestart(pid, processInfo, reasons) {
        console.log(`🔄 Restarting process ${processInfo.name} (PID: ${pid})`);
        console.log(`   Reasons: ${reasons.join(', ')}`);
        
        const restartEvent = {
            pid,
            name: processInfo.name,
            reasons,
            timestamp: Date.now(),
            restartAttempt: processInfo.restartCount + 1
        };
        
        this.state.restartHistory.push(restartEvent);
        processInfo.restartCount++;
        processInfo.lastRestart = Date.now();
        
        try {
            // Graceful termination
            process.kill(pid, 'SIGTERM');
            
            setTimeout(() => {
                try {
                    // Force kill if still running
                    process.kill(pid, 'SIGKILL');
                } catch (e) {
                    // Process already terminated
                }
                
                // Start new process if restart command is available
                if (processInfo.policy.restartCommand) {
                    this.startReplacementProcess(processInfo);
                }
                
            }, 5000);
            
            this.logEvent('PROCESS_RESTART', `Restarted ${processInfo.name} due to: ${reasons.join(', ')}`, restartEvent);
            
        } catch (error) {
            this.logEvent('RESTART_FAILED', `Failed to restart ${processInfo.name}: ${error.message}`);
        }
    }
    
    startReplacementProcess(processInfo) {
        try {
            const command = processInfo.policy.restartCommand;
            const args = command.split(' ');
            const executable = args.shift();
            
            console.log(`🚀 Starting replacement process: ${command}`);
            
            const newProcess = spawn(executable, args, {
                detached: true,
                stdio: 'ignore',
                env: processInfo.policy.environment
            });
            
            newProcess.unref();
            
            // Register the new process
            this.registerProcess(newProcess.pid, processInfo.name, {
                command: command,
                startTime: Date.now()
            });
            
            this.logEvent('REPLACEMENT_STARTED', `Started replacement process for ${processInfo.name} (PID: ${newProcess.pid})`);
            
        } catch (error) {
            this.logEvent('REPLACEMENT_FAILED', `Failed to start replacement for ${processInfo.name}: ${error.message}`);
        }
    }
    
    triggerHealthAlert(pid, processInfo, status, issues) {
        const now = Date.now();
        if (now - processInfo.lastAlert < this.config.alerting.cooldownPeriod) {
            return;
        }
        
        processInfo.lastAlert = now;
        processInfo.alertCount++;
        
        const alert = {
            timestamp: new Date().toISOString(),
            pid,
            processName: processInfo.name,
            healthStatus: status,
            issues,
            alertCount: processInfo.alertCount,
            memoryUsageMB: processInfo.memoryHistory.length > 0 ? 
                processInfo.memoryHistory[processInfo.memoryHistory.length - 1].memoryMB : 0
        };
        
        this.state.alertHistory.push(alert);
        
        // Keep only recent alerts
        if (this.state.alertHistory.length > 100) {
            this.state.alertHistory = this.state.alertHistory.slice(-50);
        }
        
        const symbol = status === 'critical' ? '🚨' : '⚠️';
        console.log(`${symbol} HEALTH ALERT: ${processInfo.name} (PID: ${pid}) - ${status.toUpperCase()}`);
        console.log(`   Issues: ${issues.join(', ')}`);
        
        this.logEvent('HEALTH_ALERT', `Health alert for ${processInfo.name}`, alert);
        
        // Check for escalation
        if (processInfo.alertCount >= this.config.alerting.escalationThreshold) {
            this.triggerEscalationAlert(pid, processInfo, 'repeated_health_alerts');
        }
    }
    
    triggerEscalationAlert(pid, processInfo, reason) {
        console.log(`🔥 ESCALATION ALERT: ${processInfo.name} (PID: ${pid})`);
        console.log(`   Reason: ${reason}`);
        console.log(`   Alert Count: ${processInfo.alertCount}`);
        console.log(`   Restart Count: ${processInfo.restartCount}`);
        
        const escalation = {
            timestamp: new Date().toISOString(),
            pid,
            processName: processInfo.name,
            reason,
            alertCount: processInfo.alertCount,
            restartCount: processInfo.restartCount,
            action: 'manual_intervention_required'
        };
        
        this.logEvent('ESCALATION_ALERT', `Escalation alert for ${processInfo.name}`, escalation);
    }
    
    autoRegisterProcess(pid, memUsageBytes, psParts) {
        // Extract process name from command
        const command = psparts.slice(10).join(' ');
        let name = 'auto-detected';
        
        if (command.includes('claude-pm')) name = 'claude-pm-auto';
        else if (command.includes('memory-monitor')) name = 'memory-monitor-auto';
        else if (command.includes('node')) name = 'node-process-auto';
        else if (command.includes('python')) name = 'python-process-auto';
        
        this.registerProcess(pid, name, {
            command,
            startTime: Date.now(),
            autoDetected: true
        });
        
        console.log(`🔍 Auto-detected process: ${name} (PID: ${pid}, Memory: ${Math.round(memUsageBytes / 1024 / 1024)}MB)`);
    }
    
    handleMissingProcess(pid, processInfo) {
        console.log(`❌ Process ${processInfo.name} (PID: ${pid}) no longer running`);
        
        // Check if this was an expected termination (recent restart)
        const now = Date.now();
        if (now - processInfo.lastRestart < 30000) { // 30 seconds
            this.logEvent('EXPECTED_TERMINATION', `Expected termination of ${processInfo.name} after restart`);
        } else {
            this.logEvent('UNEXPECTED_TERMINATION', `Unexpected termination of ${processInfo.name}`);
            
            // Consider restarting if enabled
            if (processInfo.policy.enabled && processInfo.restartCount < processInfo.policy.maxRestarts) {
                console.log(`🔄 Attempting to restart ${processInfo.name}...`);
                this.startReplacementProcess(processInfo);
            }
        }
        
        // Remove from monitoring after delay
        setTimeout(() => {
            this.state.monitoredProcesses.delete(pid);
        }, 60000); // 1 minute delay
    }
    
    checkSystemThresholds(systemHealth) {
        // Check system memory usage
        if (systemHealth.memory.usagePercent > this.config.systemThresholds.maxSystemMemoryUsage * 100) {
            this.triggerSystemAlert('HIGH_SYSTEM_MEMORY', `System memory at ${systemHealth.memory.usagePercent.toFixed(1)}%`);
        }
        
        // Check CPU usage
        if (systemHealth.cpu.usagePercent > this.config.systemThresholds.maxCpuUsage) {
            this.triggerSystemAlert('HIGH_CPU_USAGE', `CPU usage at ${systemHealth.cpu.usagePercent.toFixed(1)}%`);
        }
        
        // Check disk space
        if (systemHealth.disk.availableBytes < this.config.systemThresholds.minFreeDiskSpace) {
            this.triggerSystemAlert('LOW_DISK_SPACE', `Only ${systemHealth.disk.availableGB}GB disk space remaining`);
        }
    }
    
    triggerSystemAlert(type, message) {
        const now = Date.now();
        if (now - this.state.lastAlert < this.config.alerting.cooldownPeriod) {
            return;
        }
        
        this.state.lastAlert = now;
        
        console.log(`🌐 SYSTEM ALERT: ${type}`);
        console.log(`   ${message}`);
        
        this.logEvent('SYSTEM_ALERT', message, { type, timestamp: now });
    }
    
    cleanupStaleProcesses() {
        const staleThreshold = 5 * 60 * 1000; // 5 minutes
        const now = Date.now();
        
        for (const [pid, processInfo] of this.state.monitoredProcesses) {
            if (processInfo.memoryHistory.length === 0) continue;
            
            const lastUpdate = processInfo.memoryHistory[processInfo.memoryHistory.length - 1].timestamp;
            if (now - lastUpdate > staleThreshold) {
                console.log(`🧹 Removing stale process: ${processInfo.name} (PID: ${pid})`);
                this.state.monitoredProcesses.delete(pid);
            }
        }
    }
    
    updateHealthReport() {
        const report = {
            timestamp: new Date().toISOString(),
            session: {
                started: new Date(this.state.startTime).toISOString(),
                durationMinutes: Math.round((Date.now() - this.state.startTime) / 60000),
                totalProcessesMonitored: this.state.monitoredProcesses.size,
                totalRestarts: this.state.restartHistory.length,
                totalAlerts: this.state.alertHistory.length
            },
            systemHealth: this.state.systemHealth,
            processStatus: Array.from(this.state.monitoredProcesses.values()).map(p => ({
                pid: p.pid,
                name: p.name,
                healthStatus: p.healthStatus,
                uptimeMinutes: Math.round((Date.now() - p.startTime) / 60000),
                memoryMB: p.memoryHistory.length > 0 ? p.memoryHistory[p.memoryHistory.length - 1].memoryMB : 0,
                restartCount: p.restartCount,
                alertCount: p.alertCount
            })),
            recentRestarts: this.state.restartHistory.slice(-10),
            recentAlerts: this.state.alertHistory.slice(-10),
            configuration: this.config
        };
        
        fs.writeFileSync(this.healthReportFile, JSON.stringify(report, null, 2));
    }
    
    logEvent(type, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            type,
            message,
            data
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
        console.log('🛑 Process Health Manager shutting down...');
        
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        
        this.generateShutdownReport();
        this.logEvent('HEALTH_MONITORING_STOPPED', 'Process health monitoring system shutdown');
    }
    
    generateShutdownReport() {
        const shutdownReport = {
            session: {
                started: new Date(this.state.startTime).toISOString(),
                ended: new Date().toISOString(),
                duration: Date.now() - this.state.startTime,
                processesMonitored: this.state.monitoredProcesses.size,
                totalRestarts: this.state.restartHistory.length,
                totalAlerts: this.state.alertHistory.length
            },
            finalSystemHealth: this.state.systemHealth,
            restartHistory: this.state.restartHistory,
            alertHistory: this.state.alertHistory,
            processStats: Array.from(this.state.monitoredProcesses.values()).map(p => ({
                name: p.name,
                finalStatus: p.healthStatus,
                totalUptime: Date.now() - p.startTime,
                restartCount: p.restartCount,
                alertCount: p.alertCount
            }))
        };
        
        const shutdownReportPath = path.join(process.cwd(), 'logs', `health-shutdown-${Date.now()}.json`);
        fs.writeFileSync(shutdownReportPath, JSON.stringify(shutdownReport, null, 2));
        console.log(`📊 Shutdown report saved: ${shutdownReportPath}`);
    }
    
    // Public API methods
    getHealthStatus() {
        return {
            systemHealth: this.state.systemHealth,
            processCount: this.state.monitoredProcesses.size,
            healthyProcesses: Array.from(this.state.monitoredProcesses.values()).filter(p => p.healthStatus === 'healthy').length,
            recentAlerts: this.state.alertHistory.slice(-5),
            recentRestarts: this.state.restartHistory.slice(-5)
        };
    }
    
    addRestartPolicy(processName, policy) {
        this.restartPolicies[processName] = policy;
        this.saveRestartPolicies();
        console.log(`✅ Added restart policy for ${processName}`);
    }
    
    removeRestartPolicy(processName) {
        delete this.restartPolicies[processName];
        this.saveRestartPolicies();
        console.log(`🗑️  Removed restart policy for ${processName}`);
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    
    if (command === 'status') {
        try {
            const reportFile = path.join(process.cwd(), 'logs', 'health-report.json');
            if (fs.existsSync(reportFile)) {
                const report = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
                console.log('🏥 Process Health Status:');
                console.log(`   System Memory: ${report.systemHealth.memory.usagePercent.toFixed(1)}%`);
                console.log(`   Monitored Processes: ${report.processStatus.length}`);
                console.log(`   Recent Alerts: ${report.recentAlerts.length}`);
                console.log(`   Recent Restarts: ${report.recentRestarts.length}`);
            } else {
                console.log('❌ Health monitoring not active');
            }
        } catch (error) {
            console.log('❌ Error reading health status');
        }
        process.exit(0);
    } else {
        const healthManager = new ProcessHealthManager();
        
        console.log('🏥 Process Health Manager Active - Press Ctrl+C to stop');
        console.log('🔄 Memory-based restart policies enabled');
        console.log('📊 Comprehensive health monitoring active');
        
        // Keep process alive
        setInterval(() => {
            // Health monitoring runs in background
        }, 60000);
    }
}

module.exports = ProcessHealthManager;
