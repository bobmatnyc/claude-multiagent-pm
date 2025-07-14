#!/usr/bin/env node

/**
 * Enhanced Cache System Initialization
 * 
 * Initializes the enhanced cache management system for the Claude PM Framework.
 * This script sets up:
 * - Enhanced LRU caches with compression
 * - Performance monitoring and analytics
 * - Memory-aware cleanup mechanisms
 * - Integration with existing memory monitoring
 */

const fs = require('fs');
const path = require('path');

class EnhancedCacheInitializer {
    constructor(options = {}) {
        this.config = {
            // Cache configuration
            maxCacheSize: options.maxCacheSize || 100,
            maxMemoryPerCache: options.maxMemoryPerCache || 50 * 1024 * 1024, // 50MB
            compressionThreshold: options.compressionThreshold || 1024, // 1KB
            compressionLevel: options.compressionLevel || 6,
            
            // Performance settings
            performanceTracking: options.performanceTracking !== false,
            autoResize: options.autoResize !== false,
            hitRatioOptimization: options.hitRatioOptimization !== false,
            
            // Memory management
            strictMemoryEnforcement: options.strictMemoryEnforcement !== false,
            cleanupThreshold: options.cleanupThreshold || 0.8, // 80%
            cleanupInterval: options.cleanupInterval || 30000, // 30 seconds
            
            // Integration settings
            replaceGlobalCaches: options.replaceGlobalCaches !== false,
            monitoringIntegration: options.monitoringIntegration !== false
        };
        
        this.manager = null;
        this.initialized = false;
    }
    
    async initialize() {
        console.log('🚀 Initializing Enhanced Cache System...');
        console.log('📊 Configuration:');
        console.log(`   Max Cache Size: ${this.config.maxCacheSize} entries`);
        console.log(`   Max Memory Per Cache: ${Math.round(this.config.maxMemoryPerCache / 1024 / 1024)}MB`);
        console.log(`   Compression Threshold: ${this.config.compressionThreshold} bytes`);
        console.log(`   Performance Tracking: ${this.config.performanceTracking ? 'Enabled' : 'Disabled'}`);
        console.log(`   Auto Resize: ${this.config.autoResize ? 'Enabled' : 'Disabled'}`);
        console.log(`   Memory Enforcement: ${this.config.strictMemoryEnforcement ? 'Strict' : 'Lenient'}`);
        
        try {
            // Load enhanced cache manager
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            
            // Create manager instance with configuration
            this.manager = new EnhancedCacheManager(this.config);
            
            // Store globally for integration
            if (this.config.replaceGlobalCaches) {
                global._enhancedCacheManager = this.manager;
                console.log('✅ Enhanced cache manager stored globally');
            }
            
            // Setup monitoring integration
            if (this.config.monitoringIntegration) {
                this.setupMonitoringIntegration();
            }
            
            // Verify initialization
            this.verifyInitialization();
            
            this.initialized = true;
            console.log('✅ Enhanced Cache System initialization complete');
            
            return {
                success: true,
                manager: this.manager,
                config: this.config
            };
            
        } catch (error) {
            console.error('❌ Enhanced Cache System initialization failed:', error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    setupMonitoringIntegration() {
        console.log('🔗 Setting up monitoring integration...');
        
        try {
            // Check if memory monitor is available and integrate
            if (fs.existsSync(path.join(__dirname, 'memory-monitor.js'))) {
                console.log('   Found memory monitor - integration available');
                
                // Override global cache cleanup to use enhanced system
                const originalClearCaches = global.clearCaches;
                global.clearCaches = () => {
                    if (this.manager) {
                        console.log('🧹 Using enhanced cache cleanup...');
                        this.manager.performScheduledCleanup();
                    } else if (originalClearCaches) {
                        originalClearCaches();
                    }
                };
                
                console.log('   ✅ Enhanced cache cleanup integrated');
            }
            
            // Check if memory guard is available and integrate
            if (fs.existsSync(path.join(__dirname, 'memory-guard.js'))) {
                console.log('   Found memory guard - cache limits will be respected');
                
                // Ensure cache memory limits align with guard limits
                const guardMemoryLimit = 1.5 * 1024 * 1024 * 1024; // 1.5GB from memory-guard
                const adjustedCacheLimit = Math.min(this.config.maxMemoryPerCache, guardMemoryLimit / 6); // 6 caches
                
                if (adjustedCacheLimit < this.config.maxMemoryPerCache) {
                    console.log(`   ⚙️  Adjusted cache memory limit to ${Math.round(adjustedCacheLimit / 1024 / 1024)}MB for guard compatibility`);
                    
                    // Update cache limits
                    for (const [name, cache] of this.manager.caches) {
                        cache.maxMemory = adjustedCacheLimit;
                    }
                }
                
                console.log('   ✅ Memory guard integration complete');
            }
            
        } catch (error) {
            console.warn('⚠️ Monitoring integration failed:', error.message);
        }
    }
    
    verifyInitialization() {
        console.log('🔍 Verifying enhanced cache system...');
        
        const verificationResults = {
            managerCreated: !!this.manager,
            cachesCreated: false,
            globalIntegration: false,
            performanceTracking: false,
            memoryLimits: false
        };
        
        if (this.manager) {
            // Check caches were created
            verificationResults.cachesCreated = this.manager.caches.size > 0;
            console.log(`   Caches created: ${this.manager.caches.size} caches`);
            
            // Check global integration
            verificationResults.globalIntegration = global._claudePMCache && 
                typeof global._claudePMCache.get === 'function';
            console.log(`   Global integration: ${verificationResults.globalIntegration ? 'Yes' : 'No'}`);
            
            // Check performance tracking
            const metrics = this.manager.getGlobalMetrics();
            verificationResults.performanceTracking = metrics && 
                typeof metrics.totalOperations === 'number';
            console.log(`   Performance tracking: ${verificationResults.performanceTracking ? 'Yes' : 'No'}`);
            
            // Check memory limits
            const cache = this.manager.caches.get('_claudePMCache');
            verificationResults.memoryLimits = cache && cache.maxMemory > 0;
            console.log(`   Memory limits: ${verificationResults.memoryLimits ? 'Yes' : 'No'}`);
        }
        
        const allChecksPass = Object.values(verificationResults).every(result => result === true);
        
        if (allChecksPass) {
            console.log('✅ All verification checks passed');
        } else {
            const failedChecks = Object.entries(verificationResults)
                .filter(([key, value]) => !value)
                .map(([key]) => key);
            console.warn(`⚠️ Verification checks failed: ${failedChecks.join(', ')}`);
        }
        
        return verificationResults;
    }
    
    getStatus() {
        if (!this.initialized || !this.manager) {
            return {
                initialized: false,
                error: 'Enhanced cache system not initialized'
            };
        }
        
        const globalMetrics = this.manager.getGlobalMetrics();
        const cacheStatus = {};
        
        for (const [name, cache] of this.manager.caches) {
            const analytics = cache.getAnalytics();
            cacheStatus[name] = {
                size: analytics.size,
                maxSize: analytics.maxSize,
                utilizationPercent: analytics.utilizationPercent,
                memoryUsageKB: analytics.memoryUsage,
                memoryPercent: analytics.memoryPercent,
                compressedEntries: analytics.compressedEntries
            };
        }
        
        return {
            initialized: true,
            globalMetrics,
            cacheStatus,
            config: this.config
        };
    }
    
    generateInitializationReport() {
        const status = this.getStatus();
        
        const report = {
            timestamp: new Date().toISOString(),
            initialization: {
                success: this.initialized,
                config: this.config
            },
            status,
            verification: this.verifyInitialization(),
            systemInfo: {
                nodeVersion: process.version,
                platform: process.platform,
                arch: process.arch,
                memoryUsage: process.memoryUsage()
            }
        };
        
        const reportPath = path.join(process.cwd(), 'logs', `enhanced-cache-initialization-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📊 Initialization report saved: ${reportPath}`);
        return report;
    }
    
    shutdown() {
        if (this.manager) {
            console.log('🛑 Shutting down enhanced cache system...');
            this.manager.shutdown();
            this.manager = null;
            this.initialized = false;
            
            // Clean up global references
            if (global._enhancedCacheManager) {
                delete global._enhancedCacheManager;
            }
            
            console.log('✅ Enhanced cache system shutdown complete');
        }
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    const initializer = new EnhancedCacheInitializer();
    
    switch (command) {
        case 'init':
        case 'initialize':
            console.log('🚀 Initializing enhanced cache system...');
            initializer.initialize().then(result => {
                if (result.success) {
                    console.log('✅ Enhanced cache system ready');
                    initializer.generateInitializationReport();
                    
                    // Keep running for testing
                    console.log('📊 Press Ctrl+C to stop monitoring');
                    setInterval(() => {
                        const status = initializer.getStatus();
                        if (status.initialized) {
                            console.log(`📊 Global: ${status.globalMetrics.globalHitRatio}% hit ratio, ${status.globalMetrics.totalOperations} ops`);
                        }
                    }, 30000);
                } else {
                    console.error('❌ Initialization failed');
                    process.exit(1);
                }
            });
            break;
            
        case 'status':
            initializer.initialize().then(result => {
                if (result.success) {
                    const status = initializer.getStatus();
                    console.log('\n📊 Enhanced Cache System Status:');
                    console.log(JSON.stringify(status, null, 2));
                    initializer.shutdown();
                } else {
                    console.error('❌ Failed to get status - system not initialized');
                }
                process.exit(0);
            });
            break;
            
        case 'test':
            console.log('🧪 Testing enhanced cache system...');
            initializer.initialize().then(result => {
                if (result.success) {
                    // Run basic test
                    const cache = global._claudePMCache;
                    if (cache) {
                        // Test basic operations
                        cache.set('test_key', 'test_value');
                        const value = cache.get('test_key');
                        const testPassed = value === 'test_value';
                        
                        console.log(`✅ Basic test: ${testPassed ? 'PASSED' : 'FAILED'}`);
                        
                        // Test compression
                        const largeValue = 'x'.repeat(2048);
                        cache.set('large_test', largeValue);
                        const retrievedLarge = cache.get('large_test');
                        const compressionTest = retrievedLarge === largeValue;
                        
                        console.log(`✅ Compression test: ${compressionTest ? 'PASSED' : 'FAILED'}`);
                        
                        initializer.generateInitializationReport();
                    }
                    
                    initializer.shutdown();
                } else {
                    console.error('❌ Test failed - system not initialized');
                }
                process.exit(0);
            });
            break;
            
        default:
            console.log(`
🚀 Enhanced Cache System Initializer

Usage:
  node initialize-enhanced-cache.js <command>

Commands:
  init, initialize    Initialize enhanced cache system
  status             Show system status
  test               Run basic functionality test

Examples:
  node initialize-enhanced-cache.js init
  node initialize-enhanced-cache.js status
  node initialize-enhanced-cache.js test
            `);
            process.exit(1);
    }
}

module.exports = EnhancedCacheInitializer;