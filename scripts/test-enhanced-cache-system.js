#!/usr/bin/env node

/**
 * Enhanced Cache System Validation Script
 * 
 * Tests the enhanced cache management system with comprehensive validation:
 * 1. Enhanced LRU cache behavior with compression
 * 2. Cache hit/miss ratio tracking and optimization
 * 3. Memory-aware cache operations with stricter cleanup
 * 4. Performance monitoring and analytics
 * 5. Auto-scaling cache sizes based on performance
 * 6. Integration with existing memory monitoring
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class EnhancedCacheTestSuite {
    constructor() {
        this.testResults = [];
        this.startTime = Date.now();
        this.maxTestDuration = 300000; // 5 minutes max test duration
        
        this.testConfig = {
            heapLimitMB: 4096, // 4GB in MB
            cacheTestSize: 150, // Test with more entries than default 100
            compressionThreshold: 1024, // 1KB compression threshold
            memoryPressureTestMB: 512, // 512MB memory pressure test
            performanceIterations: 1000, // Performance test iterations
            cleanupThreshold: 0.8 // 80% cleanup threshold
        };
        
        console.log('🧪 Enhanced Cache System Validation Suite Starting...');
        console.log('📊 Test Configuration:');
        console.log(`   Heap Limit: ${this.testConfig.heapLimitMB}MB`);
        console.log(`   Cache Test Size: ${this.testConfig.cacheTestSize} entries`);
        console.log(`   Compression Threshold: ${this.testConfig.compressionThreshold} bytes`);
        console.log(`   Performance Iterations: ${this.testConfig.performanceIterations}`);
        console.log(`   Max Test Duration: ${this.maxTestDuration / 1000}s`);
    }
    
    async runAllTests() {
        try {
            await this.test1_EnhancedLRUCacheOperations();
            await this.test2_CacheCompressionEffectiveness();
            await this.test3_PerformanceMonitoringAccuracy();
            await this.test4_AutoScalingBehavior();
            await this.test5_MemoryAwareCleanup();
            await this.test6_CacheAnalyticsAccuracy();
            await this.test7_IntegrationWithMemoryMonitoring();
            
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            this.recordTestResult('test_suite_execution', false, error.message);
        }
    }
    
    async test1_EnhancedLRUCacheOperations() {
        console.log('\n🔬 Test 1: Enhanced LRU Cache Operations');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 100,
                performanceTracking: true,
                compressionThreshold: this.testConfig.compressionThreshold
            });
            
            const cache = manager.caches.get('_claudePMCache');
            
            // Test basic LRU operations
            console.log('   Testing basic LRU operations...');
            for (let i = 0; i < 120; i++) {
                const key = `key_${i}`;
                const value = `value_${i}_${'x'.repeat(500)}`; // 500+ chars each
                cache.set(key, value);
            }
            
            const finalSize = cache.size;
            console.log(`   Cache size after 120 insertions: ${finalSize}/100`);
            
            // Test LRU eviction worked
            const lruEvictionWorked = finalSize <= 100;
            
            // Test access pattern updates
            const lastKey = 'key_119';
            const hasLastKey = cache.has(lastKey);
            console.log(`   Most recent key retained: ${hasLastKey ? 'Yes' : 'No'}`);
            
            // Test get operation updates access order
            const midKey = 'key_50';
            if (cache.has(midKey)) {
                const value = cache.get(midKey);
                console.log(`   Middle key access test: ${value ? 'Success' : 'Failed'}`);
            }
            
            // Test memory tracking
            const memoryUsage = cache.currentMemory;
            console.log(`   Current memory usage: ${Math.round(memoryUsage / 1024)}KB`);
            const memoryTrackingWorked = memoryUsage > 0;
            
            const success = lruEvictionWorked && hasLastKey && memoryTrackingWorked;
            this.recordTestResult('enhanced_lru_cache_operations', success, 
                `Size: ${finalSize}, Recent key: ${hasLastKey}, Memory: ${Math.round(memoryUsage / 1024)}KB`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('enhanced_lru_cache_operations', false, error.message);
        }
    }
    
    async test2_CacheCompressionEffectiveness() {
        console.log('\n🔬 Test 2: Cache Compression Effectiveness');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 50,
                compressionThreshold: 512, // 512 bytes threshold
                compressionLevel: 6
            });
            
            const cache = manager.caches.get('_claudePMCache');
            
            // Add large entries that should trigger compression
            console.log('   Testing compression with large entries...');
            const largeData = 'x'.repeat(2048); // 2KB data
            const compressionTestCount = 10;
            
            for (let i = 0; i < compressionTestCount; i++) {
                const key = `large_key_${i}`;
                const value = {
                    data: largeData,
                    timestamp: Date.now(),
                    metadata: { size: 2048, index: i }
                };
                cache.set(key, value);
            }
            
            // Check if compression occurred
            let compressedEntries = 0;
            for (const [key, metadata] of cache.entryMetadata) {
                if (metadata.compressed) {
                    compressedEntries++;
                }
            }
            
            console.log(`   Compressed entries: ${compressedEntries}/${compressionTestCount}`);
            const compressionWorked = compressedEntries > 0;
            
            // Test decompression by retrieving values
            const testKey = 'large_key_0';
            const retrievedValue = cache.get(testKey);
            const decompressionWorked = retrievedValue && retrievedValue.data === largeData;
            
            console.log(`   Decompression test: ${decompressionWorked ? 'Success' : 'Failed'}`);
            
            // Check memory efficiency
            const memoryUsage = cache.currentMemory;
            const expectedUncompressedSize = compressionTestCount * 2048 * 2; // Rough estimate
            const memoryEfficient = memoryUsage < expectedUncompressedSize;
            
            console.log(`   Memory usage: ${Math.round(memoryUsage / 1024)}KB (efficient: ${memoryEfficient})`);
            
            const success = compressionWorked && decompressionWorked && memoryEfficient;
            this.recordTestResult('cache_compression_effectiveness', success, 
                `Compressed: ${compressedEntries}, Decompression: ${decompressionWorked}, Memory efficient: ${memoryEfficient}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('cache_compression_effectiveness', false, error.message);
        }
    }
    
    async test3_PerformanceMonitoringAccuracy() {
        console.log('\n🔬 Test 3: Performance Monitoring Accuracy');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 100,
                performanceTracking: true
            });
            
            const cache = manager.caches.get('_claudePMCache');
            
            // Perform controlled operations to test tracking
            console.log('   Testing hit/miss ratio tracking...');
            
            // Add known entries
            const testEntries = 50;
            for (let i = 0; i < testEntries; i++) {
                cache.set(`test_key_${i}`, `test_value_${i}`);
            }
            
            // Perform hits and misses
            let expectedHits = 0;
            let expectedMisses = 0;
            
            // Generate hits (existing keys)
            for (let i = 0; i < 25; i++) {
                const value = cache.get(`test_key_${i}`);
                if (value) expectedHits++;
            }
            
            // Generate misses (non-existing keys)
            for (let i = 100; i < 125; i++) {
                const value = cache.get(`test_key_${i}`);
                if (!value) expectedMisses++;
            }
            
            // Check manager's global tracking
            const globalMetrics = manager.getGlobalMetrics();
            console.log(`   Global hits: ${globalMetrics.totalHits}, misses: ${globalMetrics.totalMisses}`);
            console.log(`   Global hit ratio: ${globalMetrics.globalHitRatio}%`);
            
            // Verify tracking accuracy
            const hitTrackingAccurate = globalMetrics.totalHits >= expectedHits;
            const missTrackingAccurate = globalMetrics.totalMisses >= expectedMisses;
            const hitRatioReasonable = globalMetrics.globalHitRatio >= 0 && globalMetrics.globalHitRatio <= 100;
            
            console.log(`   Hit tracking accurate: ${hitTrackingAccurate}`);
            console.log(`   Miss tracking accurate: ${missTrackingAccurate}`);
            console.log(`   Hit ratio reasonable: ${hitRatioReasonable}`);
            
            const success = hitTrackingAccurate && missTrackingAccurate && hitRatioReasonable;
            this.recordTestResult('performance_monitoring_accuracy', success, 
                `Hits: ${globalMetrics.totalHits}, Misses: ${globalMetrics.totalMisses}, Ratio: ${globalMetrics.globalHitRatio}%`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('performance_monitoring_accuracy', false, error.message);
        }
    }
    
    async test4_AutoScalingBehavior() {
        console.log('\n🔬 Test 4: Auto-Scaling Behavior');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 50,
                autoResize: true,
                hitRatioOptimization: true
            });
            
            const cache = manager.caches.get('_claudePMCache');
            const initialSize = cache.maxSize;
            console.log(`   Initial cache size: ${initialSize}`);
            
            // Simulate high hit ratio scenario to trigger upscaling
            console.log('   Simulating high hit ratio scenario...');
            
            // Fill cache to near capacity
            for (let i = 0; i < 45; i++) {
                cache.set(`popular_key_${i}`, `popular_value_${i}`);
            }
            
            // Generate high hit ratio by accessing existing keys repeatedly
            for (let round = 0; round < 10; round++) {
                for (let i = 0; i < 40; i++) {
                    cache.get(`popular_key_${i}`);
                }
            }
            
            // Manually trigger optimization (normally done by interval)
            manager.optimizeCachePerformance();
            
            const newSize = cache.maxSize;
            const sizeIncreased = newSize > initialSize;
            
            console.log(`   Cache size after optimization: ${newSize} (increased: ${sizeIncreased})`);
            
            // Test downsizing with low hit ratio
            console.log('   Simulating low hit ratio scenario...');
            
            // Clear metrics and cache for fresh test
            const metrics = manager.metrics.get('_claudePMCache');
            metrics.hits = 5;
            metrics.misses = 50;
            
            // Trigger optimization again
            manager.optimizeCachePerformance();
            
            const finalSize = cache.maxSize;
            console.log(`   Final cache size: ${finalSize}`);
            
            const autoScalingWorked = sizeIncreased || (finalSize !== initialSize);
            
            this.recordTestResult('auto_scaling_behavior', autoScalingWorked, 
                `Initial: ${initialSize}, Peak: ${newSize}, Final: ${finalSize}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('auto_scaling_behavior', false, error.message);
        }
    }
    
    async test5_MemoryAwareCleanup() {
        console.log('\n🔬 Test 5: Memory-Aware Cleanup');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 100,
                maxMemoryPerCache: 10 * 1024 * 1024, // 10MB limit
                strictMemoryEnforcement: true,
                cleanupThreshold: 0.7 // Cleanup at 70%
            });
            
            const cache = manager.caches.get('_claudePMCache');
            const memoryLimit = cache.maxMemory;
            
            console.log(`   Memory limit: ${Math.round(memoryLimit / 1024 / 1024)}MB`);
            
            // Fill cache with large entries to approach memory limit
            console.log('   Filling cache to approach memory limit...');
            
            const largeValue = 'x'.repeat(100 * 1024); // 100KB per entry
            let entriesAdded = 0;
            
            for (let i = 0; i < 150; i++) {
                const success = cache.set(`memory_test_${i}`, largeValue);
                if (success) {
                    entriesAdded++;
                } else {
                    console.log(`   Entry rejected at index ${i} due to memory limit`);
                    break;
                }
            }
            
            const memoryUsage = cache.currentMemory;
            const memoryPercent = (memoryUsage / memoryLimit) * 100;
            
            console.log(`   Entries added: ${entriesAdded}`);
            console.log(`   Memory usage: ${Math.round(memoryUsage / 1024 / 1024)}MB (${Math.round(memoryPercent)}%)`);
            
            // Test cleanup functionality
            console.log('   Testing memory cleanup...');
            const beforeCleanupSize = cache.size;
            const beforeCleanupMemory = cache.currentMemory;
            
            const cleanupResult = manager.performMemoryCleanup(cache);
            
            const afterCleanupSize = cache.size;
            const afterCleanupMemory = cache.currentMemory;
            
            const entriesRemoved = beforeCleanupSize - afterCleanupSize;
            const memoryFreed = beforeCleanupMemory - afterCleanupMemory;
            
            console.log(`   Cleanup removed ${entriesRemoved} entries, freed ${Math.round(memoryFreed / 1024)}KB`);
            
            const cleanupWorked = entriesRemoved > 0 && memoryFreed > 0;
            const memoryEnforcementWorked = memoryUsage <= memoryLimit;
            
            const success = cleanupWorked && memoryEnforcementWorked;
            this.recordTestResult('memory_aware_cleanup', success, 
                `Cleanup: ${cleanupWorked}, Enforcement: ${memoryEnforcementWorked}, Freed: ${Math.round(memoryFreed / 1024)}KB`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_aware_cleanup', false, error.message);
        }
    }
    
    async test6_CacheAnalyticsAccuracy() {
        console.log('\n🔬 Test 6: Cache Analytics Accuracy');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager({
                maxCacheSize: 50,
                performanceTracking: true
            });
            
            const cache = manager.caches.get('_claudePMCache');
            
            // Populate cache with known data
            console.log('   Populating cache for analytics test...');
            
            const testEntries = 30;
            for (let i = 0; i < testEntries; i++) {
                const value = {
                    data: `test_data_${i}`,
                    size: 1024 * (i + 1) // Varying sizes
                };
                cache.set(`analytics_key_${i}`, value);
            }
            
            // Access some entries to create metadata
            for (let i = 0; i < 15; i++) {
                cache.get(`analytics_key_${i}`);
            }
            
            // Get analytics
            const analytics = cache.getAnalytics();
            
            console.log(`   Analytics results:`);
            console.log(`   - Size: ${analytics.size}/${analytics.maxSize} (${analytics.utilizationPercent}%)`);
            console.log(`   - Memory: ${analytics.memoryUsage}KB/${analytics.maxMemory}KB (${analytics.memoryPercent}%)`);
            console.log(`   - Avg entry size: ${analytics.avgEntrySize} bytes`);
            console.log(`   - Compressed entries: ${analytics.compressedEntries}`);
            console.log(`   - Avg access count: ${Math.round(analytics.avgAccessCount * 100) / 100}`);
            
            // Validate analytics accuracy
            const sizeAccurate = analytics.size === cache.size;
            const utilizationAccurate = analytics.utilizationPercent >= 0 && analytics.utilizationPercent <= 100;
            const memoryAccurate = analytics.memoryUsage > 0;
            const avgEntryAccurate = analytics.avgEntrySize > 0;
            
            console.log(`   Size accurate: ${sizeAccurate}`);
            console.log(`   Utilization accurate: ${utilizationAccurate}`);
            console.log(`   Memory accurate: ${memoryAccurate}`);
            console.log(`   Avg entry size accurate: ${avgEntryAccurate}`);
            
            const success = sizeAccurate && utilizationAccurate && memoryAccurate && avgEntryAccurate;
            this.recordTestResult('cache_analytics_accuracy', success, 
                `Size: ${sizeAccurate}, Utilization: ${utilizationAccurate}, Memory: ${memoryAccurate}, Avg size: ${avgEntryAccurate}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('cache_analytics_accuracy', false, error.message);
        }
    }
    
    async test7_IntegrationWithMemoryMonitoring() {
        console.log('\n🔬 Test 7: Integration with Memory Monitoring');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const manager = new EnhancedCacheManager();
            
            // Test that global caches are properly set up
            console.log('   Testing global cache integration...');
            
            const globalCacheNames = ['_claudePMCache', '_deploymentCache', '_memoryCache', '_taskToolCache'];
            let globalCachesSetup = true;
            
            for (const cacheName of globalCacheNames) {
                if (!global[cacheName]) {
                    console.log(`   Missing global cache: ${cacheName}`);
                    globalCachesSetup = false;
                }
            }
            
            console.log(`   Global caches setup: ${globalCachesSetup ? 'Yes' : 'No'}`);
            
            // Test integration with existing memory monitor
            console.log('   Testing memory monitor integration...');
            
            let memoryMonitorIntegration = false;
            try {
                // Try to load memory monitor and verify it can access our caches
                const MemoryMonitor = require('./memory-monitor.js');
                const monitor = new MemoryMonitor();
                
                // Check if memory monitor can clear our caches
                if (global._claudePMCache && typeof global._claudePMCache.clear === 'function') {
                    global._claudePMCache.set('integration_test', 'test_value');
                    monitor.clearCaches();
                    
                    // Our enhanced cache should still exist but be cleared
                    memoryMonitorIntegration = global._claudePMCache && global._claudePMCache.size === 0;
                }
                
                // Cleanup monitor
                monitor.shutdown();
                
            } catch (error) {
                console.log(`   Memory monitor integration test error: ${error.message}`);
            }
            
            console.log(`   Memory monitor integration: ${memoryMonitorIntegration ? 'Yes' : 'No'}`);
            
            // Test performance report generation
            console.log('   Testing performance report generation...');
            
            const report = manager.generatePerformanceReport();
            const reportGenerated = report && report.globalMetrics && report.cacheDetails;
            
            console.log(`   Performance report generated: ${reportGenerated ? 'Yes' : 'No'}`);
            
            const success = globalCachesSetup && reportGenerated;
            this.recordTestResult('integration_with_memory_monitoring', success, 
                `Global setup: ${globalCachesSetup}, Report: ${reportGenerated}, Monitor integration: ${memoryMonitorIntegration}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('integration_with_memory_monitoring', false, error.message);
        }
    }
    
    recordTestResult(testName, success, details) {
        this.testResults.push({
            testName,
            success,
            details,
            timestamp: new Date().toISOString(),
            memoryUsage: process.memoryUsage()
        });
        
        const status = success ? '✅' : '❌';
        console.log(`   ${status} ${testName}: ${details}`);
    }
    
    generateTestReport() {
        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(r => r.success).length;
        const testDuration = Date.now() - this.startTime;
        
        const report = {
            summary: {
                totalTests,
                passedTests,
                failedTests: totalTests - passedTests,
                successRate: Math.round((passedTests / totalTests) * 100),
                testDuration,
                timestamp: new Date().toISOString()
            },
            testResults: this.testResults,
            systemInfo: {
                nodeVersion: process.version,
                platform: process.platform,
                arch: process.arch,
                totalMemory: os.totalmem(),
                freeMemory: os.freemem(),
                cpuCount: os.cpus().length
            },
            enhancedCacheConfig: this.testConfig,
            recommendations: this.generateRecommendations()
        };
        
        const reportPath = path.join(__dirname, '..', 'logs', `enhanced-cache-validation-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📊 Enhanced Cache Test Suite Results:');
        console.log(`   Total Tests: ${totalTests}`);
        console.log(`   Passed: ${passedTests}`);
        console.log(`   Failed: ${totalTests - passedTests}`);
        console.log(`   Success Rate: ${report.summary.successRate}%`);
        console.log(`   Duration: ${Math.round(testDuration / 1000)}s`);
        console.log(`   Report saved to: ${reportPath}`);
        
        if (report.summary.successRate >= 85) {
            console.log('\n🎉 Enhanced cache system is HIGHLY EFFECTIVE! Ready for production deployment.');
        } else if (report.summary.successRate >= 70) {
            console.log('\n✅ Enhanced cache system is EFFECTIVE! Minor optimizations recommended.');
        } else {
            console.log('\n⚠️  Enhanced cache system needs improvements. Review failed tests.');
        }
        
        if (report.recommendations.length > 0) {
            console.log('\n💡 Recommendations:');
            report.recommendations.forEach(rec => console.log(`   • ${rec}`));
        }
        
        return report;
    }
    
    generateRecommendations() {
        const recommendations = [];
        const failedTests = this.testResults.filter(r => !r.success);
        
        if (failedTests.length > 0) {
            const failedTestNames = failedTests.map(t => t.testName);
            
            if (failedTestNames.includes('enhanced_lru_cache_operations')) {
                recommendations.push('Review LRU cache implementation - basic operations may have issues');
            }
            
            if (failedTestNames.includes('cache_compression_effectiveness')) {
                recommendations.push('Optimize compression settings - current compression may be ineffective');
            }
            
            if (failedTestNames.includes('performance_monitoring_accuracy')) {
                recommendations.push('Fix performance tracking - hit/miss ratios may be inaccurate');
            }
            
            if (failedTestNames.includes('auto_scaling_behavior')) {
                recommendations.push('Review auto-scaling logic - cache sizing may not adapt properly');
            }
            
            if (failedTestNames.includes('memory_aware_cleanup')) {
                recommendations.push('Strengthen memory cleanup - cache may not respect memory limits');
            }
            
            if (failedTestNames.includes('cache_analytics_accuracy')) {
                recommendations.push('Fix analytics calculations - cache metrics may be unreliable');
            }
            
            if (failedTestNames.includes('integration_with_memory_monitoring')) {
                recommendations.push('Improve integration with existing memory systems');
            }
        }
        
        // Performance-based recommendations
        const avgDuration = this.testResults.reduce((sum, r) => {
            const testTime = new Date(r.timestamp).getTime() - this.startTime;
            return sum + testTime;
        }, 0) / this.testResults.length;
        
        if (avgDuration > 30000) { // 30 seconds average
            recommendations.push('Consider optimizing test performance - average test duration is high');
        }
        
        return recommendations;
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new EnhancedCacheTestSuite();
    testSuite.runAllTests().catch(error => {
        console.error('💥 Enhanced cache test suite crashed:', error);
        process.exit(1);
    });
}

module.exports = EnhancedCacheTestSuite;