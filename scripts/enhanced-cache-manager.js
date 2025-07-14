#!/usr/bin/env node

/**
 * Claude PM Framework - Enhanced Cache Management System
 * 
 * Advanced LRU cache implementation with performance monitoring,
 * compression, serialization optimization, and stricter cleanup mechanisms.
 * 
 * Features:
 * - Enhanced LRU cache with configurable thresholds
 * - Cache hit/miss ratio tracking and optimization
 * - Cache compression and serialization optimization
 * - Performance monitoring and analytics
 * - Strict memory cleanup with configurable limits
 * - Auto-scaling cache sizes based on memory pressure
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { performance } = require('perf_hooks');

class EnhancedCacheManager {
    constructor(options = {}) {
        this.config = {
            maxCacheSize: options.maxCacheSize || 100,
            compressionThreshold: options.compressionThreshold || 1024, // Compress entries > 1KB
            compressionLevel: options.compressionLevel || 6,
            maxMemoryPerCache: options.maxMemoryPerCache || 50 * 1024 * 1024, // 50MB per cache
            cleanupThreshold: options.cleanupThreshold || 0.8, // Cleanup at 80% capacity
            performanceTracking: options.performanceTracking !== false,
            autoResize: options.autoResize !== false,
            serializationOptimization: options.serializationOptimization !== false,
            strictMemoryEnforcement: options.strictMemoryEnforcement !== false,
            hitRatioOptimization: options.hitRatioOptimization !== false
        };
        
        this.caches = new Map();
        this.metrics = new Map();
        this.compressionCache = new Map();
        this.cleanupInterval = null;
        this.performanceInterval = null;
        
        this.startTime = Date.now();
        this.totalOperations = 0;
        this.totalHits = 0;
        this.totalMisses = 0;
        this.totalCompressions = 0;
        this.totalEvictions = 0;
        
        this.initialize();
    }
    
    initialize() {
        console.log('🚀 Enhanced Cache Manager - Initializing Advanced Cache System');
        console.log('📊 Configuration:');
        console.log(`   Max Cache Size: ${this.config.maxCacheSize} entries`);
        console.log(`   Compression Threshold: ${this.config.compressionThreshold} bytes`);
        console.log(`   Max Memory Per Cache: ${Math.round(this.config.maxMemoryPerCache / 1024 / 1024)}MB`);
        console.log(`   Cleanup Threshold: ${Math.round(this.config.cleanupThreshold * 100)}%`);
        console.log(`   Performance Tracking: ${this.config.performanceTracking ? 'Enabled' : 'Disabled'}`);
        console.log(`   Auto Resize: ${this.config.autoResize ? 'Enabled' : 'Disabled'}`);
        console.log(`   Compression: ${this.config.compressionLevel}/9 level`);
        
        // Initialize default caches
        this.createCache('_claudePMCache');
        this.createCache('_deploymentCache');
        this.createCache('_memoryCache');
        this.createCache('_taskToolCache');
        this.createCache('_agentCache');
        this.createCache('_subprocessCache', { maxSize: 50 });
        
        this.startCleanupMonitoring();
        this.startPerformanceMonitoring();
        this.setupGlobalCaches();
        
        console.log('✅ Enhanced Cache Manager initialized');
    }
    
    createCache(name, options = {}) {
        const cacheConfig = {
            maxSize: options.maxSize || this.config.maxCacheSize,
            maxMemory: options.maxMemory || this.config.maxMemoryPerCache,
            compressionEnabled: options.compression !== false,
            strictMemory: options.strictMemory !== false
        };
        
        const cache = this.createEnhancedLRUCache(cacheConfig);
        this.caches.set(name, cache);
        
        // Initialize metrics for this cache
        this.metrics.set(name, {
            hits: 0,
            misses: 0,
            evictions: 0,
            compressions: 0,
            decompressions: 0,
            memoryUsage: 0,
            avgAccessTime: 0,
            lastCleanup: Date.now(),
            resizeEvents: 0,
            hitRatio: 0
        });
        
        console.log(`📦 Cache '${name}' created with max size: ${cacheConfig.maxSize}`);
        return cache;
    }
    
    createEnhancedLRUCache(config) {
        const cache = new Map();
        const manager = this;
        
        // Enhanced cache properties
        cache.maxSize = config.maxSize;
        cache.maxMemory = config.maxMemory;
        cache.currentMemory = 0;
        cache.compressionEnabled = config.compressionEnabled;
        cache.strictMemory = config.strictMemory;
        cache.accessOrder = [];
        cache.entryMetadata = new Map();
        
        // Enhanced get method with performance tracking
        cache.get = function(key) {
            const startTime = performance.now();
            manager.totalOperations++;
            
            if (this.has(key)) {
                // Move to end (most recently used)
                const value = Map.prototype.get.call(this, key);
                this.delete(key);
                this.set(key, value);
                
                // Update access tracking
                const metadata = this.entryMetadata.get(key) || {};
                metadata.accessCount = (metadata.accessCount || 0) + 1;
                metadata.lastAccess = Date.now();
                this.entryMetadata.set(key, metadata);
                
                // Track hit
                manager.totalHits++;
                const endTime = performance.now();
                manager.updateAccessTime(endTime - startTime);
                
                return manager.deserializeIfNeeded(value);
            }
            
            // Track miss
            manager.totalMisses++;
            const endTime = performance.now();
            manager.updateAccessTime(endTime - startTime);
            
            return undefined;
        };
        
        // Enhanced set method with compression and memory management
        cache.set = function(key, value) {
            const startTime = performance.now();
            const serializedValue = manager.serializeIfNeeded(value);
            const valueSize = manager.estimateSize(serializedValue);
            
            // Check memory limits before adding
            if (this.strictMemory && (this.currentMemory + valueSize) > this.maxMemory) {
                // Try cleanup first
                manager.performMemoryCleanup(this);
                
                // If still over limit, reject the entry
                if ((this.currentMemory + valueSize) > this.maxMemory) {
                    console.warn(`⚠️ Cache entry rejected: would exceed memory limit (${Math.round((this.currentMemory + valueSize) / 1024 / 1024)}MB > ${Math.round(this.maxMemory / 1024 / 1024)}MB)`);
                    return false;
                }
            }
            
            // Remove existing entry if present
            if (this.has(key)) {
                const existingValue = Map.prototype.get.call(this, key);
                this.currentMemory -= manager.estimateSize(existingValue);
                this.delete(key);
            } else if (this.size >= this.maxSize) {
                // Evict least recently used
                this.evictLRU();
            }
            
            // Compress if needed
            const finalValue = manager.compressIfNeeded(serializedValue);
            
            // Add new entry
            Map.prototype.set.call(this, key, finalValue);
            this.currentMemory += valueSize;
            
            // Update metadata
            this.entryMetadata.set(key, {
                size: valueSize,
                compressed: finalValue !== serializedValue,
                created: Date.now(),
                accessCount: 0,
                lastAccess: Date.now()
            });
            
            manager.totalOperations++;
            const endTime = performance.now();
            manager.updateAccessTime(endTime - startTime);
            
            return true;
        };
        
        // Enhanced eviction method
        cache.evictLRU = function() {
            if (this.size === 0) return;
            
            // Find least recently used entry
            const firstKey = this.keys().next().value;
            const metadata = this.entryMetadata.get(firstKey);
            
            if (metadata) {
                this.currentMemory -= metadata.size;
            }
            
            this.delete(firstKey);
            this.entryMetadata.delete(firstKey);
            manager.totalEvictions++;
        };
        
        // Memory cleanup method
        cache.performMemoryCleanup = function() {
            return manager.performMemoryCleanup(this);
        };
        
        // Enhanced clear method
        cache.clear = function() {
            Map.prototype.clear.call(this);
            this.entryMetadata.clear();
            this.currentMemory = 0;
            this.accessOrder = [];
        };
        
        // Cache analytics
        cache.getAnalytics = function() {
            return manager.getCacheAnalytics(this);
        };
        
        return cache;
    }
    
    compressIfNeeded(value) {
        if (!this.config.compressionThreshold) return value;
        
        const size = this.estimateSize(value);
        if (size > this.config.compressionThreshold) {
            try {
                const compressed = zlib.deflateSync(JSON.stringify(value), {
                    level: this.config.compressionLevel
                });
                
                this.totalCompressions++;
                console.log(`🗜️ Compressed entry: ${size} bytes → ${compressed.length} bytes (${Math.round((1 - compressed.length / size) * 100)}% reduction)`);
                
                return {
                    __compressed: true,
                    data: compressed,
                    originalSize: size
                };
            } catch (error) {
                console.warn(`⚠️ Compression failed: ${error.message}`);
                return value;
            }
        }
        
        return value;
    }
    
    deserializeIfNeeded(value) {
        if (value && value.__compressed) {
            try {
                const decompressed = zlib.inflateSync(value.data);
                return JSON.parse(decompressed.toString());
            } catch (error) {
                console.warn(`⚠️ Decompression failed: ${error.message}`);
                return null;
            }
        }
        
        return value;
    }
    
    serializeIfNeeded(value) {
        if (this.config.serializationOptimization) {
            // For complex objects, use optimized serialization
            if (typeof value === 'object' && value !== null) {
                try {
                    return JSON.parse(JSON.stringify(value)); // Deep clone + validate JSON serializable
                } catch (error) {
                    console.warn(`⚠️ Serialization failed: ${error.message}`);
                    return value;
                }
            }
        }
        
        return value;
    }
    
    estimateSize(value) {
        if (value && value.__compressed) {
            return value.data.length;
        }
        
        try {
            return JSON.stringify(value).length * 2; // Rough estimate in bytes (UTF-16)
        } catch (error) {
            return 1024; // Default estimate
        }
    }
    
    performMemoryCleanup(cache) {
        const beforeSize = cache.size;
        const beforeMemory = cache.currentMemory;
        
        // Strategy 1: Remove least accessed entries
        const entries = Array.from(cache.entryMetadata.entries())
            .sort((a, b) => (a[1].accessCount || 0) - (b[1].accessCount || 0));
        
        const removeCount = Math.floor(cache.size * 0.2); // Remove 20%
        const toRemove = entries.slice(0, removeCount);
        
        for (const [key] of toRemove) {
            if (cache.has(key)) {
                const metadata = cache.entryMetadata.get(key);
                cache.currentMemory -= metadata.size;
                cache.delete(key);
                cache.entryMetadata.delete(key);
            }
        }
        
        const cleanedSize = beforeSize - cache.size;
        const cleanedMemory = beforeMemory - cache.currentMemory;
        
        console.log(`🧹 Cache cleanup: removed ${cleanedSize} entries, freed ${Math.round(cleanedMemory / 1024)}KB`);
        
        return {
            entriesRemoved: cleanedSize,
            memoryFreed: cleanedMemory
        };
    }
    
    updateAccessTime(duration) {
        // Update running average of access times
        this.totalOperations++;
        this.avgAccessTime = ((this.avgAccessTime * (this.totalOperations - 1)) + duration) / this.totalOperations;
    }
    
    setupGlobalCaches() {
        // Replace global caches with enhanced implementations
        for (const [name, cache] of this.caches) {
            global[name] = cache;
        }
        
        console.log('✅ Global enhanced caches initialized');
    }
    
    startCleanupMonitoring() {
        this.cleanupInterval = setInterval(() => {
            this.performScheduledCleanup();
        }, 30000); // Every 30 seconds
        
        console.log('🧹 Enhanced cache cleanup monitoring started');
    }
    
    startPerformanceMonitoring() {
        if (!this.config.performanceTracking) return;
        
        this.performanceInterval = setInterval(() => {
            this.updatePerformanceMetrics();
            this.optimizeCachePerformance();
        }, 60000); // Every minute
        
        console.log('📊 Performance monitoring started');
    }
    
    performScheduledCleanup() {
        for (const [name, cache] of this.caches) {
            const metrics = this.metrics.get(name);
            const utilizationPercent = cache.size / cache.maxSize;
            const memoryPercent = cache.currentMemory / cache.maxMemory;
            
            // Cleanup if over threshold
            if (utilizationPercent > this.config.cleanupThreshold || memoryPercent > this.config.cleanupThreshold) {
                console.log(`🧹 Scheduled cleanup for cache '${name}': ${Math.round(utilizationPercent * 100)}% full, ${Math.round(memoryPercent * 100)}% memory`);
                
                const result = this.performMemoryCleanup(cache);
                metrics.lastCleanup = Date.now();
                
                // Update metrics
                metrics.evictions += result.entriesRemoved;
                metrics.memoryUsage = cache.currentMemory;
            }
        }
        
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }
    }
    
    updatePerformanceMetrics() {
        for (const [name, cache] of this.caches) {
            const metrics = this.metrics.get(name);
            
            // Update hit ratio
            const totalAccess = metrics.hits + metrics.misses;
            metrics.hitRatio = totalAccess > 0 ? metrics.hits / totalAccess : 0;
            
            // Update memory usage
            metrics.memoryUsage = cache.currentMemory;
            
            // Log performance summary
            if (totalAccess > 0) {
                console.log(`📊 Cache '${name}': ${Math.round(metrics.hitRatio * 100)}% hit ratio, ${cache.size}/${cache.maxSize} entries, ${Math.round(cache.currentMemory / 1024)}KB memory`);
            }
        }
    }
    
    optimizeCachePerformance() {
        if (!this.config.hitRatioOptimization) return;
        
        for (const [name, cache] of this.caches) {
            const metrics = this.metrics.get(name);
            
            // Auto-resize based on hit ratio and usage patterns
            if (this.config.autoResize) {
                this.autoResizeCache(name, cache, metrics);
            }
            
            // Optimize compression settings
            this.optimizeCompression(name, cache, metrics);
        }
    }
    
    autoResizeCache(name, cache, metrics) {
        const hitRatio = metrics.hitRatio;
        const utilizationPercent = cache.size / cache.maxSize;
        
        // Increase size if high hit ratio and high utilization
        if (hitRatio > 0.8 && utilizationPercent > 0.9 && cache.maxSize < 500) {
            const newSize = Math.min(cache.maxSize * 1.5, 500);
            cache.maxSize = Math.floor(newSize);
            metrics.resizeEvents++;
            console.log(`📈 Auto-resized cache '${name}' to ${cache.maxSize} entries (hit ratio: ${Math.round(hitRatio * 100)}%)`);
        }
        
        // Decrease size if low hit ratio and low utilization
        if (hitRatio < 0.3 && utilizationPercent < 0.5 && cache.maxSize > 50) {
            const newSize = Math.max(cache.maxSize * 0.8, 50);
            cache.maxSize = Math.floor(newSize);
            metrics.resizeEvents++;
            console.log(`📉 Auto-resized cache '${name}' to ${cache.maxSize} entries (hit ratio: ${Math.round(hitRatio * 100)}%)`);
        }
    }
    
    optimizeCompression(name, cache, metrics) {
        const compressionRatio = metrics.compressions / Math.max(1, metrics.hits + metrics.misses);
        
        // Adjust compression threshold based on effectiveness
        if (compressionRatio > 0.5 && this.config.compressionThreshold > 512) {
            this.config.compressionThreshold *= 0.9;
            console.log(`🗜️ Optimized compression threshold for '${name}': ${Math.round(this.config.compressionThreshold)} bytes`);
        }
    }
    
    getCacheAnalytics(cache) {
        const totalEntries = cache.size;
        const memoryUsage = cache.currentMemory;
        const entries = Array.from(cache.entryMetadata.entries());
        
        const analytics = {
            size: totalEntries,
            maxSize: cache.maxSize,
            utilizationPercent: Math.round((totalEntries / cache.maxSize) * 100),
            memoryUsage: Math.round(memoryUsage / 1024), // KB
            maxMemory: Math.round(cache.maxMemory / 1024), // KB
            memoryPercent: Math.round((memoryUsage / cache.maxMemory) * 100),
            avgEntrySize: totalEntries > 0 ? Math.round(memoryUsage / totalEntries) : 0,
            compressedEntries: entries.filter(([, meta]) => meta.compressed).length,
            oldestEntry: Math.min(...entries.map(([, meta]) => meta.created)),
            newestEntry: Math.max(...entries.map(([, meta]) => meta.created)),
            avgAccessCount: entries.length > 0 ? entries.reduce((sum, [, meta]) => sum + (meta.accessCount || 0), 0) / entries.length : 0
        };
        
        return analytics;
    }
    
    getGlobalMetrics() {
        const globalHitRatio = this.totalOperations > 0 ? this.totalHits / this.totalOperations : 0;
        const uptime = Date.now() - this.startTime;
        
        return {
            uptime,
            totalOperations: this.totalOperations,
            totalHits: this.totalHits,
            totalMisses: this.totalMisses,
            globalHitRatio: Math.round(globalHitRatio * 100),
            totalEvictions: this.totalEvictions,
            totalCompressions: this.totalCompressions,
            avgAccessTime: Math.round(this.avgAccessTime * 100) / 100, // ms
            cacheCount: this.caches.size,
            totalMemoryUsage: Array.from(this.caches.values()).reduce((sum, cache) => sum + cache.currentMemory, 0)
        };
    }
    
    generatePerformanceReport() {
        const globalMetrics = this.getGlobalMetrics();
        const cacheDetails = {};
        
        for (const [name, cache] of this.caches) {
            const metrics = this.metrics.get(name);
            const analytics = this.getCacheAnalytics(cache);
            
            cacheDetails[name] = {
                ...analytics,
                metrics: {
                    hits: metrics.hits,
                    misses: metrics.misses,
                    hitRatio: Math.round(metrics.hitRatio * 100),
                    evictions: metrics.evictions,
                    compressions: metrics.compressions,
                    resizeEvents: metrics.resizeEvents,
                    lastCleanup: new Date(metrics.lastCleanup).toISOString()
                }
            };
        }
        
        const report = {
            timestamp: new Date().toISOString(),
            globalMetrics,
            cacheDetails,
            configuration: this.config,
            recommendations: this.generateRecommendations(globalMetrics, cacheDetails)
        };
        
        const reportPath = path.join(process.cwd(), 'logs', `enhanced-cache-performance-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📊 Performance report generated: ${reportPath}`);
        return report;
    }
    
    generateRecommendations(globalMetrics, cacheDetails) {
        const recommendations = [];
        
        if (globalMetrics.globalHitRatio < 70) {
            recommendations.push('Consider increasing cache sizes or adjusting cache policies - global hit ratio is below 70%');
        }
        
        if (globalMetrics.avgAccessTime > 10) {
            recommendations.push('Average access time is high - consider enabling compression or optimizing serialization');
        }
        
        for (const [name, details] of Object.entries(cacheDetails)) {
            if (details.metrics.hitRatio < 50) {
                recommendations.push(`Cache '${name}' has low hit ratio (${details.metrics.hitRatio}%) - review cache key strategy`);
            }
            
            if (details.memoryPercent > 90) {
                recommendations.push(`Cache '${name}' is near memory limit (${details.memoryPercent}%) - consider increasing memory allocation`);
            }
            
            if (details.metrics.evictions > details.size * 0.5) {
                recommendations.push(`Cache '${name}' has high eviction rate - consider increasing cache size`);
            }
        }
        
        return recommendations;
    }
    
    shutdown() {
        console.log('🛑 Enhanced Cache Manager shutting down...');
        
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        
        if (this.performanceInterval) {
            clearInterval(this.performanceInterval);
        }
        
        // Generate final performance report
        this.generatePerformanceReport();
        
        // Clear all caches
        for (const [name, cache] of this.caches) {
            cache.clear();
        }
        
        console.log('✅ Enhanced Cache Manager shutdown complete');
    }
}

// CLI Interface
if (require.main === module) {
    const command = process.argv[2];
    const manager = new EnhancedCacheManager();
    
    switch (command) {
        case 'monitor':
            console.log('📊 Enhanced Cache Manager - Active Monitoring Mode');
            console.log('Press Ctrl+C to stop');
            
            setInterval(() => {
                const metrics = manager.getGlobalMetrics();
                console.log(`📊 Global: ${metrics.globalHitRatio}% hit ratio, ${metrics.totalOperations} ops, ${Math.round(metrics.totalMemoryUsage / 1024)}KB memory`);
            }, 30000);
            break;
            
        case 'report':
            const report = manager.generatePerformanceReport();
            console.log('\n📊 Enhanced Cache Performance Report:');
            console.log(`Global Hit Ratio: ${report.globalMetrics.globalHitRatio}%`);
            console.log(`Total Operations: ${report.globalMetrics.totalOperations}`);
            console.log(`Average Access Time: ${report.globalMetrics.avgAccessTime}ms`);
            console.log(`Total Memory Usage: ${Math.round(report.globalMetrics.totalMemoryUsage / 1024)}KB`);
            
            if (report.recommendations.length > 0) {
                console.log('\n💡 Recommendations:');
                report.recommendations.forEach(rec => console.log(`   • ${rec}`));
            }
            
            process.exit(0);
            break;
            
        case 'optimize':
            console.log('🚀 Running cache optimization...');
            manager.optimizeCachePerformance();
            manager.performScheduledCleanup();
            manager.generatePerformanceReport();
            console.log('✅ Optimization complete');
            process.exit(0);
            break;
            
        default:
            console.log(`
🚀 Claude PM Framework - Enhanced Cache Manager

Usage:
  node enhanced-cache-manager.js <command>

Commands:
  monitor     Start continuous monitoring
  report      Generate performance report
  optimize    Run cache optimization

Examples:
  node enhanced-cache-manager.js monitor
  node enhanced-cache-manager.js report
  node enhanced-cache-manager.js optimize
            `);
            process.exit(1);
    }
}

module.exports = EnhancedCacheManager;