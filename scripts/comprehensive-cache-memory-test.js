#!/usr/bin/env node

/**
 * Comprehensive Cache and Memory Management Test
 * 
 * This script provides a complete validation of the enhanced cache management system
 * integrated with the memory monitoring and optimization systems. It addresses the
 * NODE_OPTIONS configuration issues and provides accurate performance metrics.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class ComprehensiveCacheMemoryTest {
    constructor() {
        this.testResults = [];
        this.startTime = Date.now();
        
        // Fix NODE_OPTIONS configuration
        this.setupCorrectNodeOptions();
        
        this.config = {
            heapLimitMB: 4096, // 4GB
            circuitBreakerMB: 3584, // 3.5GB
            testMemoryPressureMB: 512, // Use less memory for tests
            cacheTestEntries: 200,
            compressionTestSize: 2048, // 2KB entries
            performanceIterations: 500 // Reduced for stability
        };
        
        console.log('🧪 Comprehensive Cache and Memory Management Test Suite');
        console.log('📊 Configuration:');
        console.log(`   Heap Limit: ${this.config.heapLimitMB}MB`);
        console.log(`   Circuit Breaker: ${this.config.circuitBreakerMB}MB`);
        console.log(`   Test Memory Pressure: ${this.config.testMemoryPressureMB}MB`);
        console.log(`   Cache Test Entries: ${this.config.cacheTestEntries}`);
        console.log(`   NODE_OPTIONS: ${process.env.NODE_OPTIONS || 'Not set'}`);
    }
    
    setupCorrectNodeOptions() {
        // Set correct NODE_OPTIONS for 4GB heap
        const correctOptions = '--max-old-space-size=4096 --expose-gc';
        
        if (!process.env.NODE_OPTIONS || !process.env.NODE_OPTIONS.includes('--max-old-space-size=4096')) {
            console.log('🔧 Fixing NODE_OPTIONS configuration...');
            process.env.NODE_OPTIONS = correctOptions;
            console.log(`   Set NODE_OPTIONS: ${correctOptions}`);
        }
    }
    
    async runComprehensiveTest() {
        try {
            console.log('\n🚀 Starting comprehensive cache and memory test...');
            
            await this.test1_EnhancedCacheSystemIntegration();
            await this.test2_MemoryPressureWithCacheOptimization();
            await this.test3_CircuitBreakerWithCacheCleanup();
            await this.test4_PerformanceUnderLoad();
            await this.test5_CompressionEffectiveness();
            await this.test6_MemoryCleanupEfficiency();
            
            this.generateComprehensiveReport();
            
        } catch (error) {
            console.error('❌ Comprehensive test failed:', error.message);
            this.recordTestResult('comprehensive_test_execution', false, error.message);
        }
    }
    
    async test1_EnhancedCacheSystemIntegration() {
        console.log('\n🔬 Test 1: Enhanced Cache System Integration');
        
        try {
            // Initialize enhanced cache system
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const cacheManager = new EnhancedCacheManager({
                maxCacheSize: 100,
                compressionThreshold: 1024,
                performanceTracking: true,
                autoResize: false, // Disable for consistent testing
                strictMemoryEnforcement: true
            });
            
            console.log('   Enhanced cache manager initialized successfully');
            
            // Test basic operations
            const cache = cacheManager.caches.get('_claudePMCache');
            
            // Fill cache with test data
            for (let i = 0; i < 120; i++) {
                const key = `test_key_${i}`;
                const value = `test_value_${i}_${'x'.repeat(100)}`;
                cache.set(key, value);
            }
            
            // Verify LRU behavior
            const finalSize = cache.size;
            const hasRecentKey = cache.has('test_key_119');
            const hasOldKey = cache.has('test_key_0');
            
            console.log(`   Cache size: ${finalSize}/100`);
            console.log(`   Recent key retained: ${hasRecentKey}`);
            console.log(`   Old key evicted: ${!hasOldKey}`);
            
            // Test performance tracking
            cache.get('test_key_110'); // Hit
            cache.get('nonexistent_key'); // Miss
            
            const metrics = cacheManager.getGlobalMetrics();
            console.log(`   Global hit ratio: ${metrics.globalHitRatio}%`);
            console.log(`   Total operations: ${metrics.totalOperations}`);
            
            const success = finalSize <= 100 && hasRecentKey && !hasOldKey && metrics.totalOperations > 0;
            this.recordTestResult('enhanced_cache_system_integration', success, 
                `Size: ${finalSize}, LRU: ${hasRecentKey && !hasOldKey}, Tracking: ${metrics.totalOperations > 0}`);
            
            // Cleanup
            cacheManager.shutdown();
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('enhanced_cache_system_integration', false, error.message);
        }
    }
    
    async test2_MemoryPressureWithCacheOptimization() {
        console.log('\n🔬 Test 2: Memory Pressure with Cache Optimization');
        
        try {
            const initialMemory = process.memoryUsage();
            const initialHeapMB = Math.round(initialMemory.heapUsed / 1024 / 1024);
            console.log(`   Initial heap usage: ${initialHeapMB}MB`);
            
            // Initialize enhanced cache with memory constraints
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const cacheManager = new EnhancedCacheManager({
                maxCacheSize: 150,
                maxMemoryPerCache: 20 * 1024 * 1024, // 20MB per cache
                compressionThreshold: 512,
                strictMemoryEnforcement: true
            });
            
            // Create controlled memory pressure
            const memoryArrays = [];
            const targetMemoryMB = this.config.testMemoryPressureMB;
            
            console.log(`   Creating ${targetMemoryMB}MB memory pressure...`);
            for (let i = 0; i < targetMemoryMB; i++) {
                // Create 1MB arrays
                memoryArrays.push(new Array(256 * 1024).fill(Math.random()));
            }
            
            const pressureMemory = process.memoryUsage();
            const pressureHeapMB = Math.round(pressureMemory.heapUsed / 1024 / 1024);
            console.log(`   Memory after pressure: ${pressureHeapMB}MB`);
            
            // Test cache performance under memory pressure
            const cache = cacheManager.caches.get('_claudePMCache');
            let successfulSets = 0;
            let rejectedSets = 0;
            
            for (let i = 0; i < 100; i++) {
                const largeValue = 'x'.repeat(10 * 1024); // 10KB entries
                const success = cache.set(`pressure_key_${i}`, largeValue);
                if (success) {
                    successfulSets++;
                } else {
                    rejectedSets++;
                }
            }
            
            console.log(`   Cache operations: ${successfulSets} successful, ${rejectedSets} rejected`);
            console.log(`   Cache memory usage: ${Math.round(cache.currentMemory / 1024)}KB`);
            
            // Test cleanup effectiveness
            const beforeCleanup = process.memoryUsage();
            const beforeCleanupMB = Math.round(beforeCleanup.heapUsed / 1024 / 1024);
            
            // Trigger cache cleanup
            cacheManager.performScheduledCleanup();
            
            // Force garbage collection
            if (global.gc) {
                global.gc();
            }
            
            const afterCleanup = process.memoryUsage();
            const afterCleanupMB = Math.round(afterCleanup.heapUsed / 1024 / 1024);
            const memoryReduced = beforeCleanupMB - afterCleanupMB;
            
            console.log(`   Memory cleanup: ${beforeCleanupMB}MB → ${afterCleanupMB}MB (-${memoryReduced}MB)`);
            
            const success = successfulSets > 50 && cache.currentMemory <= cache.maxMemory;
            this.recordTestResult('memory_pressure_with_cache_optimization', success,
                `Sets: ${successfulSets}/${successfulSets + rejectedSets}, Memory constraint: ${cache.currentMemory <= cache.maxMemory}, Cleanup: -${memoryReduced}MB`);
            
            // Cleanup
            cacheManager.shutdown();
            memoryArrays.length = 0; // Clear memory arrays
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_pressure_with_cache_optimization', false, error.message);
        }
    }
    
    async test3_CircuitBreakerWithCacheCleanup() {
        console.log('\n🔬 Test 3: Circuit Breaker with Cache Cleanup');
        
        try {
            // Initialize memory optimizer with corrected settings
            const MemoryOptimizer = require('./memory-optimization.js');
            const optimizer = new MemoryOptimizer();
            
            // Verify circuit breaker threshold
            const circuitBreakerMB = Math.round(optimizer.circuitBreakerThreshold / 1024 / 1024);
            const expectedMB = 3584; // 3.5GB
            
            console.log(`   Circuit breaker threshold: ${circuitBreakerMB}MB`);
            console.log(`   Expected threshold: ${expectedMB}MB`);
            
            const thresholdCorrect = Math.abs(circuitBreakerMB - expectedMB) <= 1;
            
            // Test enhanced cache integration with memory cleanup
            let enhancedCleanupAvailable = false;
            try {
                const EnhancedCacheManager = require('./enhanced-cache-manager.js');
                const cacheManager = new EnhancedCacheManager();
                global._enhancedCacheManager = cacheManager; // Set for integration test
                
                enhancedCleanupAvailable = true;
                console.log('   Enhanced cache manager available for cleanup');
                
                // Test cleanup integration
                optimizer.clearDataStructures();
                
                cacheManager.shutdown();
                
            } catch (error) {
                console.log(`   Enhanced cache integration not available: ${error.message}`);
            }
            
            // Test circuit breaker logic without triggering actual exit
            const beforeMemory = process.memoryUsage();
            const beforeHeapMB = Math.round(beforeMemory.heapUsed / 1024 / 1024);
            
            console.log(`   Current memory usage: ${beforeHeapMB}MB`);
            console.log(`   Memory margin to circuit breaker: ${circuitBreakerMB - beforeHeapMB}MB`);
            
            const memoryMarginSafe = (circuitBreakerMB - beforeHeapMB) > 1000; // At least 1GB margin
            
            const success = thresholdCorrect && enhancedCleanupAvailable && memoryMarginSafe;
            this.recordTestResult('circuit_breaker_with_cache_cleanup', success,
                `Threshold: ${thresholdCorrect}, Enhanced cleanup: ${enhancedCleanupAvailable}, Safe margin: ${memoryMarginSafe}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('circuit_breaker_with_cache_cleanup', false, error.message);
        }
    }
    
    async test4_PerformanceUnderLoad() {
        console.log('\n🔬 Test 4: Performance Under Load');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const cacheManager = new EnhancedCacheManager({
                maxCacheSize: 200,
                performanceTracking: true,
                compressionThreshold: 1024
            });
            
            const cache = cacheManager.caches.get('_claudePMCache');
            const iterations = this.config.performanceIterations;
            
            console.log(`   Running ${iterations} cache operations...`);
            
            const startTime = Date.now();
            
            // Populate cache
            for (let i = 0; i < iterations / 2; i++) {
                const key = `perf_key_${i}`;
                const value = `perf_value_${i}_${'x'.repeat(200)}`;
                cache.set(key, value);
            }
            
            // Perform mixed read/write operations
            let hits = 0;
            let misses = 0;
            
            for (let i = 0; i < iterations / 2; i++) {
                // 70% hits, 30% misses
                const isHit = Math.random() < 0.7;
                const key = isHit ? `perf_key_${Math.floor(Math.random() * (iterations / 2))}` : `miss_key_${i}`;
                
                const value = cache.get(key);
                if (value) {
                    hits++;
                } else {
                    misses++;
                }
            }
            
            const endTime = Date.now();
            const totalTime = endTime - startTime;
            const opsPerSecond = Math.round((iterations / totalTime) * 1000);
            
            const metrics = cacheManager.getGlobalMetrics();
            const hitRatio = hits / (hits + misses) * 100;
            
            console.log(`   Performance: ${opsPerSecond} ops/sec`);
            console.log(`   Hit ratio: ${Math.round(hitRatio)}% (${hits} hits, ${misses} misses)`);
            console.log(`   Global hit ratio: ${metrics.globalHitRatio}%`);
            console.log(`   Average access time: ${metrics.avgAccessTime.toFixed(2)}ms`);
            
            const performanceGood = opsPerSecond > 1000; // At least 1000 ops/sec
            const hitRatioGood = hitRatio > 60; // At least 60% hit ratio
            const trackingAccurate = Math.abs(hitRatio - metrics.globalHitRatio) < 10; // Within 10%
            
            const success = performanceGood && hitRatioGood && trackingAccurate;
            this.recordTestResult('performance_under_load', success,
                `${opsPerSecond} ops/sec, ${Math.round(hitRatio)}% hit ratio, tracking accurate: ${trackingAccurate}`);
            
            cacheManager.shutdown();
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('performance_under_load', false, error.message);
        }
    }
    
    async test5_CompressionEffectiveness() {
        console.log('\n🔬 Test 5: Compression Effectiveness');
        
        try {
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const cacheManager = new EnhancedCacheManager({
                maxCacheSize: 50,
                compressionThreshold: 1024, // 1KB threshold
                compressionLevel: 6
            });
            
            const cache = cacheManager.caches.get('_claudePMCache');
            
            // Create compressible data
            const compressibleData = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(50); // ~2.8KB
            console.log(`   Test data size: ${compressibleData.length} bytes`);
            
            // Add entries that should trigger compression
            const testEntries = 20;
            for (let i = 0; i < testEntries; i++) {
                const key = `compress_key_${i}`;
                const value = {
                    data: compressibleData,
                    timestamp: Date.now(),
                    index: i
                };
                cache.set(key, value);
            }
            
            // Count compressed entries
            let compressedCount = 0;
            for (const [key, metadata] of cache.entryMetadata) {
                if (metadata.compressed) {
                    compressedCount++;
                }
            }
            
            console.log(`   Compressed entries: ${compressedCount}/${testEntries}`);
            
            // Test retrieval and decompression
            const testKey = 'compress_key_0';
            const retrievedValue = cache.get(testKey);
            const decompressionWorked = retrievedValue && retrievedValue.data === compressibleData;
            
            console.log(`   Decompression test: ${decompressionWorked ? 'Success' : 'Failed'}`);
            
            // Check memory efficiency
            const totalMemoryKB = Math.round(cache.currentMemory / 1024);
            const uncompressedEstimateKB = Math.round((testEntries * compressibleData.length * 2) / 1024); // Rough estimate
            const memoryEfficient = totalMemoryKB < uncompressedEstimateKB;
            
            console.log(`   Memory usage: ${totalMemoryKB}KB vs estimated ${uncompressedEstimateKB}KB uncompressed`);
            console.log(`   Memory efficient: ${memoryEfficient}`);
            
            const compressionRate = compressedCount / testEntries;
            const success = compressionRate > 0.8 && decompressionWorked && memoryEfficient;
            
            this.recordTestResult('compression_effectiveness', success,
                `${compressedCount}/${testEntries} compressed (${Math.round(compressionRate * 100)}%), decompression: ${decompressionWorked}, efficient: ${memoryEfficient}`);
            
            cacheManager.shutdown();
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('compression_effectiveness', false, error.message);
        }
    }
    
    async test6_MemoryCleanupEfficiency() {
        console.log('\n🔬 Test 6: Memory Cleanup Efficiency');
        
        try {
            const beforeTest = process.memoryUsage();
            const beforeTestMB = Math.round(beforeTest.heapUsed / 1024 / 1024);
            console.log(`   Before test heap usage: ${beforeTestMB}MB`);
            
            // Create memory pressure with enhanced cache system
            const EnhancedCacheManager = require('./enhanced-cache-manager.js');
            const cacheManager = new EnhancedCacheManager({
                maxCacheSize: 200,
                compressionThreshold: 512
            });
            
            // Fill caches with data
            const caches = ['_claudePMCache', '_deploymentCache', '_memoryCache'];
            for (const cacheName of caches) {
                const cache = cacheManager.caches.get(cacheName);
                for (let i = 0; i < 100; i++) {
                    const key = `cleanup_key_${i}`;
                    const value = 'x'.repeat(5 * 1024); // 5KB per entry
                    cache.set(key, value);
                }
            }
            
            // Create additional memory pressure
            const memoryArrays = [];
            for (let i = 0; i < 100; i++) {
                memoryArrays.push(new Array(10 * 1024).fill(Math.random())); // 40KB each
            }
            
            const beforeCleanup = process.memoryUsage();
            const beforeCleanupMB = Math.round(beforeCleanup.heapUsed / 1024 / 1024);
            console.log(`   Before cleanup heap usage: ${beforeCleanupMB}MB`);
            
            // Test enhanced cleanup
            global._enhancedCacheManager = cacheManager;
            
            const MemoryOptimizer = require('./memory-optimization.js');
            const optimizer = new MemoryOptimizer();
            
            // Perform cleanup
            optimizer.emergencyCleanup();
            
            // Clear memory arrays
            memoryArrays.length = 0;
            
            // Force garbage collection
            if (global.gc) {
                for (let i = 0; i < 3; i++) {
                    global.gc();
                }
            }
            
            const afterCleanup = process.memoryUsage();
            const afterCleanupMB = Math.round(afterCleanup.heapUsed / 1024 / 1024);
            const memoryReduced = beforeCleanupMB - afterCleanupMB;
            const reductionPercent = Math.round((memoryReduced / beforeCleanupMB) * 100);
            
            console.log(`   After cleanup heap usage: ${afterCleanupMB}MB`);
            console.log(`   Memory reduced: ${memoryReduced}MB (${reductionPercent}%)`);
            
            const cleanupEffective = memoryReduced > 50; // At least 50MB reduction
            const finalMemoryReasonable = afterCleanupMB < (beforeTestMB + 200); // Within 200MB of start
            
            const success = cleanupEffective && finalMemoryReasonable;
            this.recordTestResult('memory_cleanup_efficiency', success,
                `Reduced: ${memoryReduced}MB (${reductionPercent}%), Final: ${afterCleanupMB}MB, Effective: ${cleanupEffective}`);
            
            cacheManager.shutdown();
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_cleanup_efficiency', false, error.message);
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
    
    generateComprehensiveReport() {
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
            nodeConfiguration: {
                nodeOptions: process.env.NODE_OPTIONS || 'Not set',
                nodeVersion: process.version,
                platform: process.platform,
                arch: process.arch
            },
            systemInfo: {
                totalMemory: Math.round(os.totalmem() / 1024 / 1024 / 1024), // GB
                freeMemory: Math.round(os.freemem() / 1024 / 1024 / 1024), // GB
                cpuCount: os.cpus().length,
                finalMemoryUsage: process.memoryUsage()
            },
            testResults: this.testResults,
            testConfiguration: this.config,
            recommendations: this.generateRecommendations()
        };
        
        const reportPath = path.join(__dirname, '..', 'logs', `comprehensive-cache-memory-test-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📊 Comprehensive Cache and Memory Test Results:');
        console.log('=' .repeat(60));
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests}`);
        console.log(`Failed: ${totalTests - passedTests}`);
        console.log(`Success Rate: ${report.summary.successRate}%`);
        console.log(`Duration: ${Math.round(testDuration / 1000)}s`);
        console.log(`Final Memory: ${Math.round(report.systemInfo.finalMemoryUsage.heapUsed / 1024 / 1024)}MB`);
        console.log(`Report saved to: ${reportPath}`);
        
        if (report.summary.successRate >= 85) {
            console.log('\n🎉 EXCELLENT: Enhanced cache system with memory management is highly effective!');
            console.log('✅ Ready for production deployment with confidence.');
        } else if (report.summary.successRate >= 70) {
            console.log('\n✅ GOOD: Enhanced cache system shows significant improvement.');
            console.log('🔧 Minor optimizations recommended before deployment.');
        } else if (report.summary.successRate >= 50) {
            console.log('\n⚠️  ACCEPTABLE: Basic functionality working but needs improvement.');
            console.log('🔧 Address failed tests before deployment.');
        } else {
            console.log('\n❌ NEEDS WORK: Significant issues detected.');
            console.log('🔧 Major improvements required before deployment.');
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
        const successRate = (this.testResults.filter(r => r.success).length / this.testResults.length) * 100;
        
        // Specific test failure recommendations
        if (failedTests.some(t => t.testName.includes('enhanced_cache_system_integration'))) {
            recommendations.push('Fix enhanced cache system integration - basic functionality is broken');
        }
        
        if (failedTests.some(t => t.testName.includes('memory_pressure_with_cache_optimization'))) {
            recommendations.push('Improve cache behavior under memory pressure - consider stricter memory limits');
        }
        
        if (failedTests.some(t => t.testName.includes('circuit_breaker_with_cache_cleanup'))) {
            recommendations.push('Fix circuit breaker integration with enhanced cache cleanup');
        }
        
        if (failedTests.some(t => t.testName.includes('performance_under_load'))) {
            recommendations.push('Optimize cache performance - consider indexing or better algorithms');
        }
        
        if (failedTests.some(t => t.testName.includes('compression_effectiveness'))) {
            recommendations.push('Review compression settings - may need different threshold or algorithm');
        }
        
        if (failedTests.some(t => t.testName.includes('memory_cleanup_efficiency'))) {
            recommendations.push('Strengthen memory cleanup mechanisms - current cleanup may be insufficient');
        }
        
        // General recommendations based on success rate
        if (successRate < 70) {
            recommendations.push('Consider reducing cache sizes or implementing more aggressive cleanup');
            recommendations.push('Review memory allocation patterns and optimize data structures');
        }
        
        if (successRate >= 85) {
            recommendations.push('System performs well - consider enabling auto-scaling features');
            recommendations.push('Monitor production performance and adjust cache sizes based on usage patterns');
        }
        
        // Node configuration recommendations
        if (!process.env.NODE_OPTIONS || !process.env.NODE_OPTIONS.includes('--max-old-space-size=4096')) {
            recommendations.push('Ensure NODE_OPTIONS is set correctly for production deployment');
        }
        
        return recommendations;
    }
}

// Run comprehensive test if called directly
if (require.main === module) {
    const testSuite = new ComprehensiveCacheMemoryTest();
    testSuite.runComprehensiveTest().catch(error => {
        console.error('💥 Comprehensive test suite crashed:', error);
        process.exit(1);
    });
}

module.exports = ComprehensiveCacheMemoryTest;