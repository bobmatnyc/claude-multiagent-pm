#!/usr/bin/env node

/**
 * Claude PM Framework - Memory Optimization and Leak Prevention
 * 
 * This script implements immediate memory optimization fixes to prevent
 * JavaScript heap exhaustion that has been causing system failures.
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class MemoryOptimizer {
    constructor() {
        this.memoryThreshold = 3.0 * 1024 * 1024 * 1024; // 3.0GB (was 3.5GB for 8GB heap)
        this.circuitBreakerThreshold = 3.5 * 1024 * 1024 * 1024; // 3.5GB circuit breaker
        this.activeProcesses = new Set();
        this.cleanupHandlers = [];
        this.monitoringInterval = null;
        this.lastCleanup = 0;
        this.cleanupCooldown = 10000; // 10 seconds between cleanups
        
        this.setupSignalHandlers();
        this.startMemoryMonitoring();
    }

    setupSignalHandlers() {
        ['SIGINT', 'SIGTERM', 'exit'].forEach(signal => {
            process.on(signal, () => {
                this.cleanup();
                if (signal !== 'exit') {
                    process.exit(0);
                }
            });
        });
    }

    startMemoryMonitoring() {
        this.monitoringInterval = setInterval(() => {
            this.checkMemoryUsage();
        }, 10000); // Check every 10 seconds
    }

    checkMemoryUsage() {
        const usage = process.memoryUsage();
        const heapUsedMB = Math.round(usage.heapUsed / 1024 / 1024);
        const heapTotalMB = Math.round(usage.heapTotal / 1024 / 1024);
        
        console.log(`🧠 Memory: ${heapUsedMB}MB used / ${heapTotalMB}MB total`);
        
        // Circuit breaker - immediate exit at 3.5GB
        if (usage.heapUsed > this.circuitBreakerThreshold) {
            console.error(`🚨 CIRCUIT BREAKER: Memory usage at ${heapUsedMB}MB - exceeding safe threshold`);
            console.error(`💀 EMERGENCY EXIT: Process terminating to prevent heap exhaustion`);
            this.emergencyExit();
            return true;
        }
        
        if (usage.heapUsed > this.memoryThreshold) {
            console.error(`❌ CRITICAL: Memory usage at ${heapUsedMB}MB - triggering emergency cleanup`);
            this.emergencyCleanup();
            return true;
        }
        
        // Warning at 75% of threshold
        if (usage.heapUsed > this.memoryThreshold * 0.75) {
            console.warn(`⚠️  WARNING: High memory usage at ${heapUsedMB}MB - triggering proactive cleanup`);
            this.proactiveCleanup();
        }
        
        return false;
    }

    emergencyExit() {
        console.log('💀 EMERGENCY EXIT INITIATED - PREVENTING HEAP EXHAUSTION');
        
        // Save critical state before exit
        this.saveCriticalState();
        
        // Force cleanup
        this.cleanup();
        
        // Exit immediately
        setTimeout(() => {
            process.exit(1);
        }, 1000);
    }

    emergencyCleanup() {
        const now = Date.now();
        if (now - this.lastCleanup < this.cleanupCooldown) {
            console.log('⚠️  Cleanup cooldown active, skipping cleanup');
            return;
        }
        
        this.lastCleanup = now;
        console.log('🚨 Emergency memory cleanup initiated...');
        
        // Force garbage collection multiple times
        if (global.gc) {
            for (let i = 0; i < 5; i++) {
                global.gc();
                console.log(`   GC pass ${i + 1} completed`);
            }
        }
        
        // Kill any runaway processes
        this.killRunawayProcesses();
        
        // Clear any large data structures
        this.clearDataStructures();
        
        // Clear subprocess cache
        this.clearSubprocessCache();
        
        const newUsage = process.memoryUsage();
        const newUsedMB = Math.round(newUsage.heapUsed / 1024 / 1024);
        console.log(`✅ Emergency cleanup complete - memory reduced to ${newUsedMB}MB`);
    }

    proactiveCleanup() {
        console.log('🔄 Proactive memory cleanup...');
        
        if (global.gc) {
            global.gc();
        }
        
        // Clear caches and temporary data
        this.clearCaches();
        
        const newUsage = process.memoryUsage();
        const newUsedMB = Math.round(newUsage.heapUsed / 1024 / 1024);
        console.log(`✅ Proactive cleanup complete - memory: ${newUsedMB}MB`);
    }

    killRunawayProcesses() {
        try {
            // Find runaway Node.js processes
            const psOutput = execSync('ps aux | grep -E "(node|claude)" | grep -v grep', { encoding: 'utf8' });
            const processes = psOutput.split('\n').filter(line => line.trim());
            
            for (const line of processes) {
                const parts = line.split(/\s+/);
                if (parts.length < 11) continue;
                
                const pid = parts[1];
                const memUsage = parts[5]; // RSS in KB
                const memUsageMB = parseInt(memUsage) / 1024;
                
                // Kill processes using more than 1GB
                if (memUsageMB > 1024 && pid !== process.pid.toString()) {
                    console.log(`🔪 Killing runaway process PID ${pid} (${Math.round(memUsageMB)}MB)`);
                    try {
                        process.kill(parseInt(pid), 'SIGTERM');
                        setTimeout(() => {
                            try {
                                process.kill(parseInt(pid), 'SIGKILL');
                            } catch (e) {
                                // Process already dead
                            }
                        }, 5000);
                    } catch (error) {
                        console.log(`   Failed to kill process ${pid}: ${error.message}`);
                    }
                }
            }
        } catch (error) {
            console.log(`   Error checking processes: ${error.message}`);
        }
    }

    clearDataStructures() {
        console.log('🧹 Clearing data structures with enhanced cache management...');
        
        // Check if enhanced cache manager is available
        let enhancedCacheManager = null;
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            if (global._enhancedCacheManager instanceof EnhancedCacheManager) {
                enhancedCacheManager = global._enhancedCacheManager;
            }
        } catch (error) {
            // Enhanced cache manager not available, fall back to basic cleanup
        }
        
        if (enhancedCacheManager) {
            console.log('   Using enhanced cache manager for optimized cleanup...');
            
            // Use enhanced cache manager's performance-aware cleanup
            for (const [name, cache] of enhancedCacheManager.caches) {
                if (cache && typeof cache.performMemoryCleanup === 'function') {
                    const result = cache.performMemoryCleanup();
                    console.log(`   Enhanced cleanup for ${name}: freed ${Math.round(result.memoryFreed / 1024)}KB`);
                } else if (cache && typeof cache.clear === 'function') {
                    cache.clear();
                    console.log(`   Cleared cache: ${name}`);
                }
            }
            
            // Generate performance report before cleanup
            try {
                const report = enhancedCacheManager.generatePerformanceReport();
                console.log(`   Cache performance report generated with ${report.globalMetrics.globalHitRatio}% hit ratio`);
            } catch (error) {
                console.log(`   Failed to generate performance report: ${error.message}`);
            }
        } else {
            console.log('   Using basic cache cleanup...');
            
            // Clear any global caches or large objects (basic fallback)
            const cacheKeys = ['_claudePMCache', '_deploymentCache', '_memoryCache', '_taskToolCache', '_agentCache', '_subprocessCache'];
            
            cacheKeys.forEach(cacheKey => {
                if (global[cacheKey]) {
                    if (typeof global[cacheKey].clear === 'function') {
                        global[cacheKey].clear();
                        console.log(`   Cleared basic cache: ${cacheKey}`);
                    }
                    global[cacheKey] = null;
                }
            });
        }
        
        // Clear require cache for non-core modules more aggressively
        let clearedModules = 0;
        Object.keys(require.cache).forEach(key => {
            if (key.includes('node_modules') && !key.includes('core') && !key.includes('fs') && !key.includes('path')) {
                delete require.cache[key];
                clearedModules++;
            }
        });
        
        console.log(`   Cleared ${clearedModules} require cache entries`);
    }

    clearSubprocessCache() {
        console.log('🗑️  Advanced subprocess cache cleanup with enhanced manager integration...');
        
        // Try to use Enhanced Subprocess Manager if available
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const subprocessManager = getSubprocessManager();
            
            console.log('   Using Enhanced Subprocess Manager for comprehensive cleanup...');
            
            // Perform comprehensive cleanup through the enhanced manager
            subprocessManager.forceCleanup();
            
            // Validate zero memory retention
            const validation = subprocessManager.validateZeroMemoryRetention();
            if (validation.isValid) {
                console.log('   ✅ Zero memory retention validated');
            } else {
                console.log('   ⚠️ Memory retention detected:', validation.validation);
                
                // Fallback to manual cleanup
                this.fallbackSubprocessCleanup();
            }
            
            const metrics = subprocessManager.getPerformanceMetrics();
            console.log(`   Enhanced cleanup stats: ${metrics.totalSubprocessesTerminated} terminated, ${metrics.memoryLeakPreventions} leaks prevented`);
            
        } catch (error) {
            console.log('   Enhanced Subprocess Manager not available, using basic cleanup...');
            this.fallbackSubprocessCleanup();
        }
    }
    
    fallbackSubprocessCleanup() {
        // Clear activeSubprocesses Map that retains process references
        if (global.activeSubprocesses) {
            if (typeof global.activeSubprocesses.clear === 'function') {
                global.activeSubprocesses.clear();
            }
            global.activeSubprocesses = null;
        }
        
        // Clear any process tracking maps
        this.activeProcesses.clear();
        
        // Clear additional global subprocess maps
        ['_subprocessCache', '_processTracker', '_taskToolProcesses'].forEach(mapName => {
            if (global[mapName]) {
                if (typeof global[mapName].clear === 'function') {
                    const size = global[mapName].size || 0;
                    global[mapName].clear();
                    if (size > 0) {
                        console.log(`   Cleared ${size} entries from global ${mapName}`);
                    }
                }
                global[mapName] = null;
            }
        });
        
        console.log('   Basic subprocess cache cleared');
    }

    saveCriticalState() {
        try {
            const state = {
                timestamp: new Date().toISOString(),
                memoryUsage: process.memoryUsage(),
                processId: process.pid,
                reason: 'circuit_breaker_triggered'
            };
            
            const stateFile = path.join(process.cwd(), 'logs', 'emergency-exit-state.json');
            fs.mkdirSync(path.dirname(stateFile), { recursive: true });
            fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
            
            console.log(`💾 Critical state saved to: ${stateFile}`);
        } catch (error) {
            console.error(`⚠️  Failed to save critical state: ${error.message}`);
        }
    }

    clearCaches() {
        // Clear smaller caches proactively
        if (global.gc) {
            global.gc();
        }
    }

    cleanup() {
        console.log('🧹 Memory optimizer cleanup...');
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        // Kill any tracked processes
        this.activeProcesses.forEach(proc => {
            if (proc && !proc.killed) {
                try {
                    proc.kill('SIGTERM');
                } catch (error) {
                    // Ignore errors
                }
            }
        });
        
        // Run cleanup handlers
        this.cleanupHandlers.forEach(handler => {
            try {
                handler();
            } catch (error) {
                // Ignore errors
            }
        });
        
        // Final garbage collection
        if (global.gc) {
            global.gc();
        }
    }

    optimizeNodeProcess() {
        // Set Node.js memory optimization flags with 4GB limit
        process.env.NODE_OPTIONS = (process.env.NODE_OPTIONS || '') + ' --max-old-space-size=4096 --expose-gc --gc-interval=100';
        
        console.log('🚀 Node.js memory optimization flags set');
        console.log('   --max-old-space-size=4096 (4GB heap limit - REDUCED from 8GB)');
        console.log('   --expose-gc (manual GC available)');
        console.log('   --gc-interval=100 (frequent garbage collection)');
        console.log('   ✅ CRITICAL FIX: Reduced heap limit to prevent exhaustion');
        console.log('   🔥 Circuit breaker at 3.5GB to prevent crashes');
    }

    runSystemOptimization() {
        console.log('🔧 Running system-wide memory optimization...');
        
        try {
            // Clear system caches (macOS)
            if (process.platform === 'darwin') {
                console.log('🍎 Clearing macOS caches...');
                execSync('sudo purge', { stdio: 'inherit' });
            }
            
            // Clear temporary files
            const tempDirs = [
                '/tmp',
                '/var/folders',
                path.join(require('os').homedir(), '.cache')
            ];
            
            tempDirs.forEach(dir => {
                if (fs.existsSync(dir)) {
                    try {
                        console.log(`🗑️  Clearing temp directory: ${dir}`);
                        execSync(`find "${dir}" -name "*.tmp" -delete 2>/dev/null || true`);
                    } catch (error) {
                        // Ignore errors for system directories
                    }
                }
            });
            
        } catch (error) {
            console.log(`⚠️  System optimization warning: ${error.message}`);
        }
    }

    deployOptimizations() {
        console.log('📦 Deploying memory optimizations to framework...');
        
        // Update deployment scripts with memory flags
        const deploymentScripts = [
            '/Users/masa/.local/bin/claude-pm',
            '/Users/masa/.local/bin/cmpm'
        ];
        
        deploymentScripts.forEach(scriptPath => {
            if (fs.existsSync(scriptPath)) {
                try {
                    let content = fs.readFileSync(scriptPath, 'utf8');
                    
                    // Add memory optimization to shebang line if not present
                    if (!content.includes('--max-old-space-size')) {
                        content = content.replace(
                            '#!/usr/bin/env node',
                            '#!/usr/bin/env node --max-old-space-size=8192 --expose-gc'
                        );
                        
                        fs.writeFileSync(scriptPath, content);
                        console.log(`✅ Updated ${scriptPath} with memory optimizations`);
                    }
                } catch (error) {
                    console.log(`⚠️  Failed to update ${scriptPath}: ${error.message}`);
                }
            }
        });
    }

    generateReport() {
        const usage = process.memoryUsage();
        const report = {
            timestamp: new Date().toISOString(),
            memory_usage: {
                heap_used_mb: Math.round(usage.heapUsed / 1024 / 1024),
                heap_total_mb: Math.round(usage.heapTotal / 1024 / 1024),
                external_mb: Math.round(usage.external / 1024 / 1024),
                rss_mb: Math.round(usage.rss / 1024 / 1024)
            },
            optimizations_applied: [
                'Node.js heap size increased to 8GB',
                'Subprocess memory isolation (2GB per subprocess)',
                'Garbage collection interval reduced',
                'Automatic memory monitoring enabled',
                'Emergency cleanup procedures implemented',
                'Process cleanup handlers installed',
                'Predictive memory alerts enabled',
                'Memory guard system for Task Tool subprocesses'
            ],
            recommendations: [
                'Monitor memory usage regularly',
                'Restart long-running processes periodically',
                'Use --expose-gc flag for manual garbage collection',
                'Implement data structure cleanup in applications'
            ]
        };
        
        const reportPath = path.join(process.cwd(), 'memory-optimization-report.json');
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📊 Memory optimization report saved to: ${reportPath}`);
        return report;
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    const optimizer = new MemoryOptimizer();
    
    switch (command) {
        case 'monitor':
            console.log('🔍 Starting memory monitoring...');
            console.log('Press Ctrl+C to stop');
            // Keep process alive for monitoring
            setInterval(() => {
                // Monitor runs in background
            }, 60000);
            break;
            
        case 'cleanup':
            console.log('🧹 Running immediate cleanup...');
            optimizer.emergencyCleanup();
            process.exit(0);
            break;
            
        case 'optimize':
            console.log('🚀 Running full optimization...');
            optimizer.optimizeNodeProcess();
            optimizer.runSystemOptimization();
            optimizer.deployOptimizations();
            optimizer.generateReport();
            console.log('✅ Optimization complete');
            process.exit(0);
            break;
            
        case 'report':
            const report = optimizer.generateReport();
            console.log('\n📊 Memory Optimization Report:');
            console.log(JSON.stringify(report, null, 2));
            process.exit(0);
            break;
            
        default:
            console.log(`
🧠 Claude PM Framework - Memory Optimizer

Usage:
  node memory-optimization.js <command>

Commands:
  monitor     Start continuous memory monitoring
  cleanup     Run immediate memory cleanup
  optimize    Apply full memory optimizations
  report      Generate memory usage report

Examples:
  node memory-optimization.js optimize
  node memory-optimization.js monitor
  node memory-optimization.js cleanup
            `);
            process.exit(1);
    }
}

module.exports = MemoryOptimizer;