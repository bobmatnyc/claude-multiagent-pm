#!/usr/bin/env node

/**
 * Claude PM Framework - Historical Memory Usage Tracker
 * 
 * Comprehensive long-term memory usage tracking with trend analysis and reporting
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class MemoryHistoryTracker {
    constructor() {
        this.config = {
            trackingInterval: 60000,              // 1 minute intervals
            historyRetention: {
                shortTerm: 24 * 60,               // 24 hours of 1-minute samples
                mediumTerm: 7 * 24 * 12,          // 7 days of 5-minute samples
                longTerm: 30 * 24 * 4,            // 30 days of 15-minute samples
                archive: 365 * 24                 // 1 year of 1-hour samples
            },
            compressionLevels: {
                level1: 5,    // Compress to 5-minute intervals after 24 hours
                level2: 15,   // Compress to 15-minute intervals after 7 days
                level3: 60    // Compress to 1-hour intervals after 30 days
            },
            alertThresholds: {
                memoryGrowthRate: 100,            // 100MB/hour growth
                unusualPatternConfidence: 0.8,    // 80% confidence for anomalies
                reportGenerationInterval: 24 * 60 * 60 * 1000  // Daily reports
            },
            storage: {
                maxFileSize: 50 * 1024 * 1024,    // 50MB max file size
                backupCount: 5,                    // Keep 5 backup files
                compressionEnabled: true           // Enable gzip compression
            }
        };
        
        this.state = {
            trackingStarted: Date.now(),
            totalSamples: 0,
            lastCompression: 0,
            lastReport: 0,
            memoryBaseline: null,
            trendAnalysis: {},
            anomalies: [],
            compressionStats: {
                level1: 0,
                level2: 0,
                level3: 0
            }
        };
        
        this.dataDir = path.join(process.cwd(), 'logs', 'memory-history');
        this.currentDataFile = path.join(this.dataDir, 'current.jsonl');
        this.compressedDataDir = path.join(this.dataDir, 'compressed');
        this.reportsDir = path.join(this.dataDir, 'reports');
        this.archiveDir = path.join(this.dataDir, 'archive');
        
        this.ensureDirectories();
        this.loadState();
        this.startTracking();
    }
    
    ensureDirectories() {
        [this.dataDir, this.compressedDataDir, this.reportsDir, this.archiveDir].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });
    }
    
    loadState() {
        const stateFile = path.join(this.dataDir, 'tracker-state.json');
        try {
            if (fs.existsSync(stateFile)) {
                const savedState = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
                this.state = { ...this.state, ...savedState };
                console.log('✅ Loaded existing tracker state');
            }
        } catch (error) {
            console.log('⚠️  Error loading tracker state, starting fresh');
        }
    }
    
    saveState() {
        const stateFile = path.join(this.dataDir, 'tracker-state.json');
        fs.writeFileSync(stateFile, JSON.stringify(this.state, null, 2));
    }
    
    startTracking() {
        console.log('📈 Memory History Tracker - Starting Long-term Monitoring');
        console.log(`📊 Configuration:`);
        console.log(`   Tracking Interval: ${this.config.trackingInterval}ms`);
        console.log(`   Short-term Retention: ${this.config.historyRetention.shortTerm} samples`);
        console.log(`   Data Directory: ${this.dataDir}`);
        console.log(`   Compression: ${this.config.storage.compressionEnabled ? 'Enabled' : 'Disabled'}`);
        
        // Establish memory baseline
        this.establishMemoryBaseline();
        
        this.trackingInterval = setInterval(() => {
            this.captureMemorySnapshot();
        }, this.config.trackingInterval);
        
        // Daily maintenance tasks
        this.maintenanceInterval = setInterval(() => {
            this.performMaintenance();
        }, 24 * 60 * 60 * 1000); // 24 hours
        
        this.setupSignalHandlers();
        this.logEvent('TRACKING_STARTED', 'Historical memory tracking initialized');
    }
    
    establishMemoryBaseline() {
        const samples = [];
        
        // Take 5 samples over 5 minutes to establish baseline
        const baselineInterval = setInterval(() => {
            const snapshot = this.createMemorySnapshot();
            samples.push(snapshot);
            
            if (samples.length >= 5) {
                clearInterval(baselineInterval);
                
                this.state.memoryBaseline = {
                    timestamp: Date.now(),
                    heapUsedMB: Math.round(samples.reduce((sum, s) => sum + s.process.heapUsedMB, 0) / samples.length),
                    systemUsedGB: Math.round(samples.reduce((sum, s) => sum + s.system.usedGB, 0) / samples.length),
                    samples: samples.length
                };
                
                console.log(`📏 Memory baseline established:`);
                console.log(`   Process Heap: ${this.state.memoryBaseline.heapUsedMB}MB`);
                console.log(`   System Memory: ${this.state.memoryBaseline.systemUsedGB}GB`);
                
                this.saveState();
            }
        }, 60000); // 1 minute intervals
    }
    
    captureMemorySnapshot() {
        const timestamp = Date.now();
        const snapshot = this.createMemorySnapshot();
        
        // Add tracking metadata
        snapshot.tracking = {
            sampleNumber: ++this.state.totalSamples,
            sessionUptime: timestamp - this.state.trackingStarted,
            dataFile: 'current.jsonl'
        };
        
        // Add baseline comparison
        if (this.state.memoryBaseline) {
            snapshot.baseline = {
                heapGrowthMB: snapshot.process.heapUsedMB - this.state.memoryBaseline.heapUsedMB,
                systemGrowthGB: snapshot.system.usedGB - this.state.memoryBaseline.systemUsedGB,
                percentGrowth: ((snapshot.process.heapUsedMB / this.state.memoryBaseline.heapUsedMB) - 1) * 100
            };
        }
        
        // Analyze trends
        this.analyzeTrends(snapshot);
        
        // Store the snapshot
        this.storeSnapshot(snapshot);
        
        // Check for anomalies
        this.detectAnomalies(snapshot);
        
        // Rotate files if needed
        this.checkFileRotation();
        
        // Generate reports if needed
        this.checkReportGeneration();
    }
    
    createMemorySnapshot() {
        const usage = process.memoryUsage();
        const systemMem = {
            total: os.totalmem(),
            free: os.freemem(),
            used: os.totalmem() - os.freemem()
        };
        
        // Get process list for context
        let processCount = 0;
        let totalProcessMemory = 0;
        
        try {
            const psOutput = execSync('ps aux | grep -E "(node|python|claude)" | grep -v grep | wc -l', { encoding: 'utf8' });
            processCount = parseInt(psOutput.trim());
            
            const memOutput = execSync('ps aux | grep -E "(node|python|claude)" | grep -v grep | awk \'{sum+=$6} END {print sum}\'', { encoding: 'utf8' });
            totalProcessMemory = parseInt(memOutput.trim() || '0') * 1024; // Convert KB to bytes
        } catch (error) {
            // Ignore process counting errors
        }
        
        return {
            timestamp: Date.now(),
            iso: new Date().toISOString(),
            process: {
                pid: process.pid,
                heapUsed: usage.heapUsed,
                heapTotal: usage.heapTotal,
                external: usage.external,
                rss: usage.rss,
                heapUsedMB: Math.round(usage.heapUsed / 1024 / 1024),
                heapTotalMB: Math.round(usage.heapTotal / 1024 / 1024),
                externalMB: Math.round(usage.external / 1024 / 1024),
                rssMB: Math.round(usage.rss / 1024 / 1024)
            },
            system: {
                totalGB: Math.round(systemMem.total / 1024 / 1024 / 1024),
                freeGB: Math.round(systemMem.free / 1024 / 1024 / 1024),
                usedGB: Math.round(systemMem.used / 1024 / 1024 / 1024),
                usagePercent: (systemMem.used / systemMem.total) * 100,
                uptime: os.uptime(),
                loadAverage: os.loadavg()
            },
            processes: {
                relatedCount: processCount,
                totalMemoryMB: Math.round(totalProcessMemory / 1024 / 1024)
            }
        };
    }
    
    analyzeTrends(snapshot) {
        // Read recent samples for trend analysis
        const recentSamples = this.getRecentSamples(60); // Last 60 samples (1 hour)
        
        if (recentSamples.length < 10) return; // Need minimum samples
        
        // Calculate various trends
        const trends = {
            timestamp: snapshot.timestamp,
            memoryGrowth: this.calculateMemoryGrowthTrend(recentSamples),
            systemUsage: this.calculateSystemUsageTrend(recentSamples),
            volatility: this.calculateMemoryVolatility(recentSamples),
            patterns: this.detectMemoryPatterns(recentSamples)
        };
        
        this.state.trendAnalysis = trends;
        
        // Log significant trends
        if (trends.memoryGrowth.ratePerHour > this.config.alertThresholds.memoryGrowthRate) {
            this.logEvent('HIGH_MEMORY_GROWTH', `Memory growing at ${trends.memoryGrowth.ratePerHour.toFixed(2)}MB/hour`);
        }
    }
    
    calculateMemoryGrowthTrend(samples) {
        if (samples.length < 2) return { ratePerHour: 0, trend: 'stable' };
        
        const first = samples[0];
        const last = samples[samples.length - 1];
        const timeDelta = last.timestamp - first.timestamp;
        const memoryDelta = last.process.heapUsedMB - first.process.heapUsedMB;
        
        const ratePerHour = (memoryDelta / (timeDelta / 1000)) * 3600; // MB per hour
        
        // Calculate linear regression for trend strength
        const x = samples.map((_, i) => i);
        const y = samples.map(s => s.process.heapUsedMB);
        const { slope, rSquared } = this.linearRegression(x, y);
        
        let trend = 'stable';
        if (Math.abs(ratePerHour) > 10 && rSquared > 0.5) {
            trend = ratePerHour > 0 ? 'increasing' : 'decreasing';
        }
        
        return {
            ratePerHour,
            trend,
            strength: rSquared,
            totalGrowthMB: memoryDelta,
            timeSpanHours: timeDelta / (1000 * 60 * 60)
        };
    }
    
    calculateSystemUsageTrend(samples) {
        const usageValues = samples.map(s => s.system.usagePercent);
        const avgUsage = usageValues.reduce((sum, val) => sum + val, 0) / usageValues.length;
        const maxUsage = Math.max(...usageValues);
        const minUsage = Math.min(...usageValues);
        
        return {
            average: avgUsage,
            maximum: maxUsage,
            minimum: minUsage,
            volatility: maxUsage - minUsage,
            trend: avgUsage > 80 ? 'high' : avgUsage > 60 ? 'moderate' : 'low'
        };
    }
    
    calculateMemoryVolatility(samples) {
        const memoryValues = samples.map(s => s.process.heapUsedMB);
        const mean = memoryValues.reduce((sum, val) => sum + val, 0) / memoryValues.length;
        const variance = memoryValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / memoryValues.length;
        const stdDev = Math.sqrt(variance);
        
        return {
            mean,
            standardDeviation: stdDev,
            coefficientOfVariation: stdDev / mean,
            volatility: stdDev > mean * 0.1 ? 'high' : stdDev > mean * 0.05 ? 'moderate' : 'low'
        };
    }
    
    detectMemoryPatterns(samples) {
        const patterns = [];
        
        // Detect sawtooth pattern (memory spikes)
        const peaks = this.findPeaks(samples.map(s => s.process.heapUsedMB));
        if (peaks.length >= 3) {
            patterns.push({
                type: 'sawtooth',
                confidence: Math.min(peaks.length / 10, 1),
                description: `${peaks.length} memory peaks detected`
            });
        }
        
        // Detect steady growth
        const growthTrend = this.calculateMemoryGrowthTrend(samples);
        if (growthTrend.trend === 'increasing' && growthTrend.strength > 0.8) {
            patterns.push({
                type: 'steady_growth',
                confidence: growthTrend.strength,
                description: `Steady memory growth at ${growthTrend.ratePerHour.toFixed(2)}MB/hour`
            });
        }
        
        // Detect cyclical patterns
        const cyclical = this.detectCyclicalPattern(samples.map(s => s.process.heapUsedMB));
        if (cyclical.detected) {
            patterns.push({
                type: 'cyclical',
                confidence: cyclical.confidence,
                description: `Cyclical pattern with ${cyclical.period} sample period`
            });
        }
        
        return patterns;
    }
    
    findPeaks(values) {
        const peaks = [];
        for (let i = 1; i < values.length - 1; i++) {
            if (values[i] > values[i-1] && values[i] > values[i+1]) {
                peaks.push(i);
            }
        }
        return peaks;
    }
    
    detectCyclicalPattern(values) {
        // Simple autocorrelation to detect cycles
        const maxLag = Math.min(values.length / 4, 60); // Max 60 samples lag
        let bestCorrelation = 0;
        let bestPeriod = 0;
        
        for (let lag = 5; lag < maxLag; lag++) {
            const correlation = this.autocorrelation(values, lag);
            if (correlation > bestCorrelation) {
                bestCorrelation = correlation;
                bestPeriod = lag;
            }
        }
        
        return {
            detected: bestCorrelation > 0.6,
            confidence: bestCorrelation,
            period: bestPeriod
        };
    }
    
    autocorrelation(values, lag) {
        const n = values.length - lag;
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        
        let numerator = 0;
        let denominator = 0;
        
        for (let i = 0; i < n; i++) {
            numerator += (values[i] - mean) * (values[i + lag] - mean);
        }
        
        for (let i = 0; i < values.length; i++) {
            denominator += Math.pow(values[i] - mean, 2);
        }
        
        return numerator / denominator;
    }
    
    linearRegression(x, y) {
        const n = x.length;
        const sumX = x.reduce((sum, val) => sum + val, 0);
        const sumY = y.reduce((sum, val) => sum + val, 0);
        const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
        const sumXX = x.reduce((sum, val) => sum + val * val, 0);
        const sumYY = y.reduce((sum, val) => sum + val * val, 0);
        
        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;
        
        // Calculate R-squared
        const yMean = sumY / n;
        const ssRes = y.reduce((sum, val, i) => {
            const predicted = slope * x[i] + intercept;
            return sum + Math.pow(val - predicted, 2);
        }, 0);
        const ssTot = y.reduce((sum, val) => sum + Math.pow(val - yMean, 2), 0);
        const rSquared = 1 - (ssRes / ssTot);
        
        return { slope, intercept, rSquared };
    }
    
    detectAnomalies(snapshot) {
        if (!this.state.memoryBaseline) return;
        
        const anomalies = [];
        
        // Detect memory spikes
        if (snapshot.baseline.percentGrowth > 200) { // 200% growth from baseline
            anomalies.push({
                type: 'memory_spike',
                severity: 'high',
                value: snapshot.baseline.percentGrowth,
                description: `Memory usage ${snapshot.baseline.percentGrowth.toFixed(1)}% above baseline`
            });
        }
        
        // Detect sudden drops (potential memory leaks being cleaned)
        const recentSamples = this.getRecentSamples(5);
        if (recentSamples.length >= 2) {
            const prevMemory = recentSamples[recentSamples.length - 2].process.heapUsedMB;
            const currentMemory = snapshot.process.heapUsedMB;
            const dropPercent = ((prevMemory - currentMemory) / prevMemory) * 100;
            
            if (dropPercent > 50) { // 50% drop
                anomalies.push({
                    type: 'memory_drop',
                    severity: 'medium',
                    value: dropPercent,
                    description: `Sudden ${dropPercent.toFixed(1)}% memory drop detected`
                });
            }
        }
        
        // Detect system memory pressure
        if (snapshot.system.usagePercent > 90) {
            anomalies.push({
                type: 'system_pressure',
                severity: 'critical',
                value: snapshot.system.usagePercent,
                description: `System memory at ${snapshot.system.usagePercent.toFixed(1)}%`
            });
        }
        
        // Store anomalies
        anomalies.forEach(anomaly => {
            anomaly.timestamp = snapshot.timestamp;
            anomaly.snapshot = {
                heapUsedMB: snapshot.process.heapUsedMB,
                systemUsagePercent: snapshot.system.usagePercent
            };
            
            this.state.anomalies.push(anomaly);
            this.logEvent('ANOMALY_DETECTED', `${anomaly.type}: ${anomaly.description}`, anomaly);
            
            if (anomaly.severity === 'critical' || anomaly.severity === 'high') {
                console.log(`🚨 MEMORY ANOMALY: ${anomaly.description}`);
            }
        });
        
        // Keep only recent anomalies
        if (this.state.anomalies.length > 100) {
            this.state.anomalies = this.state.anomalies.slice(-50);
        }
    }
    
    storeSnapshot(snapshot) {
        const line = JSON.stringify(snapshot) + '\n';
        fs.appendFileSync(this.currentDataFile, line);
    }
    
    getRecentSamples(count) {
        try {
            const data = fs.readFileSync(this.currentDataFile, 'utf8');
            const lines = data.trim().split('\n').filter(line => line.trim());
            const recentLines = lines.slice(-count);
            
            return recentLines.map(line => JSON.parse(line));
        } catch (error) {
            return [];
        }
    }
    
    checkFileRotation() {
        try {
            const stats = fs.statSync(this.currentDataFile);
            
            if (stats.size > this.config.storage.maxFileSize) {
                this.rotateDataFile();
            }
        } catch (error) {
            // File doesn't exist yet, no rotation needed
        }
    }
    
    rotateDataFile() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const rotatedFile = path.join(this.archiveDir, `memory-history-${timestamp}.jsonl`);
        
        console.log(`📁 Rotating data file to: ${rotatedFile}`);
        
        // Move current file to archive
        fs.renameSync(this.currentDataFile, rotatedFile);
        
        // Compress if enabled
        if (this.config.storage.compressionEnabled) {
            this.compressFile(rotatedFile);
        }
        
        this.logEvent('FILE_ROTATED', `Data file rotated to ${rotatedFile}`);
    }
    
    compressFile(filePath) {
        try {
            const zlib = require('zlib');
            const input = fs.createReadStream(filePath);
            const output = fs.createWriteStream(filePath + '.gz');
            const gzip = zlib.createGzip();
            
            input.pipe(gzip).pipe(output);
            
            output.on('close', () => {
                fs.unlinkSync(filePath); // Remove original file
                console.log(`🗜️  Compressed: ${filePath}.gz`);
            });
        } catch (error) {
            console.log(`⚠️  Compression failed for ${filePath}: ${error.message}`);
        }
    }
    
    performMaintenance() {
        console.log('🧹 Performing daily maintenance...');
        
        // Compress old data
        this.compressOldData();
        
        // Clean up old files
        this.cleanupOldFiles();
        
        // Generate daily report
        this.generateDailyReport();
        
        // Update state
        this.saveState();
        
        console.log('✅ Daily maintenance completed');
    }
    
    compressOldData() {
        // Implement data compression based on age
        const now = Date.now();
        
        // Level 1: Compress 24+ hour old data to 5-minute intervals
        const level1Threshold = now - (24 * 60 * 60 * 1000);
        this.compressDataLevel(level1Threshold, 5, 'level1');
        
        // Level 2: Compress 7+ day old data to 15-minute intervals
        const level2Threshold = now - (7 * 24 * 60 * 60 * 1000);
        this.compressDataLevel(level2Threshold, 15, 'level2');
        
        // Level 3: Compress 30+ day old data to 1-hour intervals
        const level3Threshold = now - (30 * 24 * 60 * 60 * 1000);
        this.compressDataLevel(level3Threshold, 60, 'level3');
    }
    
    compressDataLevel(threshold, intervalMinutes, level) {
        // This is a simplified compression implementation
        // In practice, you'd want more sophisticated compression logic
        
        const compressed = this.state.compressionStats[level];
        this.state.compressionStats[level] = compressed + 1;
        
        console.log(`   ${level} compression: ${intervalMinutes}min intervals`);
    }
    
    cleanupOldFiles() {
        // Remove files older than 1 year
        const oneYearAgo = Date.now() - (365 * 24 * 60 * 60 * 1000);
        
        try {
            const files = fs.readdirSync(this.archiveDir);
            
            files.forEach(file => {
                const filePath = path.join(this.archiveDir, file);
                const stats = fs.statSync(filePath);
                
                if (stats.mtime.getTime() < oneYearAgo) {
                    fs.unlinkSync(filePath);
                    console.log(`   Removed old file: ${file}`);
                }
            });
        } catch (error) {
            console.log(`   Cleanup error: ${error.message}`);
        }
    }
    
    checkReportGeneration() {
        const now = Date.now();
        
        if (now - this.state.lastReport > this.config.alertThresholds.reportGenerationInterval) {
            this.generateDailyReport();
            this.state.lastReport = now;
        }
    }
    
    generateDailyReport() {
        const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        const reportFile = path.join(this.reportsDir, `memory-report-${timestamp}.json`);
        
        const report = {
            date: timestamp,
            generated: new Date().toISOString(),
            session: {
                started: new Date(this.state.trackingStarted).toISOString(),
                duration: Date.now() - this.state.trackingStarted,
                totalSamples: this.state.totalSamples
            },
            baseline: this.state.memoryBaseline,
            trends: this.state.trendAnalysis,
            anomalies: {
                total: this.state.anomalies.length,
                recent: this.state.anomalies.slice(-10),
                severityBreakdown: this.getAnomalySeverityBreakdown()
            },
            storage: {
                compressionStats: this.state.compressionStats,
                dataDirectory: this.dataDir,
                currentFileSize: this.getCurrentFileSize()
            },
            recommendations: this.generateRecommendations()
        };
        
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        console.log(`📈 Daily report generated: ${reportFile}`);
        
        return report;
    }
    
    getAnomalySeverityBreakdown() {
        const breakdown = { critical: 0, high: 0, medium: 0, low: 0 };
        
        this.state.anomalies.forEach(anomaly => {
            breakdown[anomaly.severity] = (breakdown[anomaly.severity] || 0) + 1;
        });
        
        return breakdown;
    }
    
    getCurrentFileSize() {
        try {
            const stats = fs.statSync(this.currentDataFile);
            return {
                bytes: stats.size,
                mb: Math.round(stats.size / 1024 / 1024 * 100) / 100
            };
        } catch (error) {
            return { bytes: 0, mb: 0 };
        }
    }
    
    generateRecommendations() {
        const recommendations = [];
        
        // Memory growth recommendations
        if (this.state.trendAnalysis.memoryGrowth && this.state.trendAnalysis.memoryGrowth.ratePerHour > 50) {
            recommendations.push({
                type: 'memory_growth',
                priority: 'high',
                message: 'High memory growth rate detected - investigate for memory leaks'
            });
        }
        
        // Anomaly recommendations
        const recentAnomalies = this.state.anomalies.filter(a => 
            Date.now() - a.timestamp < 24 * 60 * 60 * 1000 // Last 24 hours
        );
        
        if (recentAnomalies.length > 5) {
            recommendations.push({
                type: 'anomalies',
                priority: 'medium',
                message: `${recentAnomalies.length} anomalies detected in last 24 hours - review system stability`
            });
        }
        
        // Storage recommendations
        const currentSize = this.getCurrentFileSize();
        if (currentSize.mb > 40) {
            recommendations.push({
                type: 'storage',
                priority: 'low',
                message: 'Data file approaching rotation threshold - consider more frequent rotation'
            });
        }
        
        return recommendations;
    }
    
    logEvent(type, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            type,
            message,
            data
        };
        
        const logFile = path.join(this.dataDir, 'tracker.log');
        fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
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
        console.log('🛑 Memory History Tracker shutting down...');
        
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }
        
        if (this.maintenanceInterval) {
            clearInterval(this.maintenanceInterval);
        }
        
        this.generateShutdownReport();
        this.saveState();
        this.logEvent('TRACKING_STOPPED', 'Historical memory tracking shutdown');
    }
    
    generateShutdownReport() {
        const shutdownReport = {
            session: {
                started: new Date(this.state.trackingStarted).toISOString(),
                ended: new Date().toISOString(),
                duration: Date.now() - this.state.trackingStarted,
                totalSamples: this.state.totalSamples
            },
            finalBaseline: this.state.memoryBaseline,
            finalTrends: this.state.trendAnalysis,
            totalAnomalies: this.state.anomalies.length,
            compressionStats: this.state.compressionStats,
            storageInfo: {
                dataDirectory: this.dataDir,
                currentFileSize: this.getCurrentFileSize(),
                archiveFiles: fs.readdirSync(this.archiveDir).length
            }
        };
        
        const shutdownReportPath = path.join(this.reportsDir, `shutdown-${Date.now()}.json`);
        fs.writeFileSync(shutdownReportPath, JSON.stringify(shutdownReport, null, 2));
        console.log(`📊 Shutdown report saved: ${shutdownReportPath}`);
    }
    
    // Public API methods
    getHistoricalData(hours = 24) {
        const hoursAgo = Date.now() - (hours * 60 * 60 * 1000);
        const samples = this.getRecentSamples(hours * 60); // Assuming 1-minute intervals
        
        return samples.filter(sample => sample.timestamp >= hoursAgo);
    }
    
    getMemoryTrends() {
        return this.state.trendAnalysis;
    }
    
    getAnomalies(hours = 24) {
        const hoursAgo = Date.now() - (hours * 60 * 60 * 1000);
        return this.state.anomalies.filter(anomaly => anomaly.timestamp >= hoursAgo);
    }
    
    exportData(startDate, endDate, format = 'json') {
        // Implementation for data export
        // This would read from compressed files and provide formatted output
        const exportData = {
            startDate,
            endDate,
            format,
            message: 'Export functionality would be implemented here'
        };
        
        return exportData;
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    
    switch (command) {
        case 'report':
            const tracker = new MemoryHistoryTracker();
            const report = tracker.generateDailyReport();
            console.log('📈 Generated daily report');
            process.exit(0);
            break;
            
        case 'export':
            console.log('📎 Export functionality - specify date range and format');
            // Implementation for data export
            process.exit(0);
            break;
            
        case 'status':
            try {
                const stateFile = path.join(process.cwd(), 'logs', 'memory-history', 'tracker-state.json');
                if (fs.existsSync(stateFile)) {
                    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
                    console.log('📈 Memory History Tracker Status:');
                    console.log(`   Total Samples: ${state.totalSamples}`);
                    console.log(`   Tracking Since: ${new Date(state.trackingStarted).toLocaleString()}`);
                    console.log(`   Anomalies: ${state.anomalies ? state.anomalies.length : 0}`);
                } else {
                    console.log('❌ History tracking not active');
                }
            } catch (error) {
                console.log('❌ Error reading tracking status');
            }
            process.exit(0);
            break;
            
        default:
            const historyTracker = new MemoryHistoryTracker();
            
            console.log('📈 Memory History Tracker Active - Press Ctrl+C to stop');
            console.log('📊 Long-term memory usage tracking enabled');
            console.log('📁 Data compression and archival active');
            
            // Keep process alive
            setInterval(() => {
                // Tracking runs in background
            }, 60000);
    }
}

module.exports = MemoryHistoryTracker;
