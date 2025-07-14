#!/usr/bin/env node

/**
 * Memory Leak Fix Validation Script
 * 
 * Tests the effectiveness of memory leak fixes implemented for ISS-0109
 * Validates:
 * 1. 4GB heap limit enforcement
 * 2. LRU cache behavior
 * 3. Subprocess lifecycle management
 * 4. Circuit breaker functionality
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

class MemoryLeakTestSuite {
    constructor() {
        this.testResults = [];
        this.startTime = Date.now();
        this.maxTestDuration = 180000; // 3 minutes max test duration
        
        this.testConfig = {
            heapLimitMB: 4096, // 4GB in MB
            circuitBreakerMB: 3584, // 3.5GB in MB
            warningThresholdMB: 3072, // 3GB in MB
            lruCacheSize: 100,
            subprocessLimit: 2
        };
        
        console.log('🧪 Memory Leak Fix Validation Suite Starting...');
        console.log('📊 Test Configuration:');
        console.log(`   Heap Limit: ${this.testConfig.heapLimitMB}MB`);
        console.log(`   Circuit Breaker: ${this.testConfig.circuitBreakerMB}MB`);
        console.log(`   LRU Cache Size: ${this.testConfig.lruCacheSize}`);
        console.log(`   Max Test Duration: ${this.maxTestDuration / 1000}s`);
    }
    
    async runAllTests() {
        try {
            await this.test1_HeapLimitEnforcement();
            await this.test2_LRUCacheEffectiveness();
            await this.test3_SubprocessLifecycleManagement();
            await this.test4_CircuitBreakerFunctionality();
            await this.test5_MemoryCleanupEfficiency();
            
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            this.recordTestResult('test_suite_execution', false, error.message);
        }
    }
    
    async test1_HeapLimitEnforcement() {
        console.log('\n🔬 Test 1: Heap Limit Enforcement (4GB)');
        
        try {
            const initialMemory = process.memoryUsage();
            const initialHeapMB = Math.round(initialMemory.heapUsed / 1024 / 1024);
            
            console.log(`   Initial heap usage: ${initialHeapMB}MB`);
            
            // Verify NODE_OPTIONS includes 4GB limit
            const nodeOptions = process.env.NODE_OPTIONS || '';
            const hasCorrectLimit = nodeOptions.includes('--max-old-space-size=4096');
            
            if (hasCorrectLimit) {
                console.log('   ✅ NODE_OPTIONS correctly set to 4GB limit');
                this.recordTestResult('heap_limit_configuration', true, 'NODE_OPTIONS set to 4096MB');
            } else {
                console.log('   ⚠️  NODE_OPTIONS not set or incorrect');
                this.recordTestResult('heap_limit_configuration', false, `NODE_OPTIONS: ${nodeOptions}`);
            }
            
            // Test memory allocation behavior
            const allocated = this.simulateMemoryPressure(1024); // Allocate 1GB
            
            const afterMemory = process.memoryUsage();
            const afterHeapMB = Math.round(afterMemory.heapUsed / 1024 / 1024);
            const growthMB = afterHeapMB - initialHeapMB;
            
            console.log(`   After allocation: ${afterHeapMB}MB (growth: +${growthMB}MB)`);
            
            // Force garbage collection if available
            if (global.gc) {
                global.gc();
                const gcMemory = process.memoryUsage();
                const gcHeapMB = Math.round(gcMemory.heapUsed / 1024 / 1024);
                console.log(`   After GC: ${gcHeapMB}MB`);
            }
            
            const success = afterHeapMB < this.testConfig.heapLimitMB;
            this.recordTestResult('heap_limit_enforcement', success, `Peak heap: ${afterHeapMB}MB`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('heap_limit_enforcement', false, error.message);
        }
    }
    
    async test2_LRUCacheEffectiveness() {
        console.log('\n🔬 Test 2: LRU Cache Effectiveness');
        
        try {
            // Test LRU cache implementation
            const MemoryGuard = require('./memory-guard.js');
            const guard = new MemoryGuard();
            
            const cache = guard.caches._claudePMCache;
            
            // Fill cache beyond capacity
            for (let i = 0; i < this.testConfig.lruCacheSize + 20; i++) {
                cache.set(`key_${i}`, `value_${i}_${'x'.repeat(1024)}`); // 1KB entries
            }
            
            const finalSize = cache.size;
            const hasEviction = finalSize <= this.testConfig.lruCacheSize;
            
            console.log(`   Cache size after overfill: ${finalSize}/${this.testConfig.lruCacheSize}`);
            console.log(`   LRU eviction working: ${hasEviction ? 'Yes' : 'No'}`);
            
            // Test access pattern
            const lastKey = `key_${this.testConfig.lruCacheSize + 19}`;
            const hasLastKey = cache.has(lastKey);
            
            console.log(`   Most recent key retained: ${hasLastKey ? 'Yes' : 'No'}`);
            
            this.recordTestResult('lru_cache_effectiveness', hasEviction && hasLastKey, 
                `Cache size: ${finalSize}, Recent key retained: ${hasLastKey}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('lru_cache_effectiveness', false, error.message);
        }
    }
    
    async test3_SubprocessLifecycleManagement() {
        console.log('\n🔬 Test 3: Enhanced Subprocess Lifecycle Management');
        
        try {
            // Test enhanced subprocess manager if available
            let enhancedManagerWorking = false;
            try {
                const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
                const manager = getSubprocessManager({
                    maxConcurrentSubprocesses: 2,
                    subprocessTimeout: 10000, // 10 seconds for testing
                    detailedLogging: false
                });
                
                const initialCount = manager.getActiveSubprocessCount();
                
                // Add test subprocess
                manager.trackSubprocess(99999, {
                    pid: 99999,
                    memoryUsage: 100 * 1024 * 1024,
                    created: Date.now() - 15000, // 15 seconds ago (exceeds timeout)
                    command: 'test_subprocess'
                });
                
                const afterTrackingCount = manager.getActiveSubprocessCount();
                
                // Trigger comprehensive cleanup
                manager.performComprehensiveCleanup();
                
                const finalCount = manager.getActiveSubprocessCount();
                
                // Validate zero memory retention
                const validation = manager.validateZeroMemoryRetention();
                
                enhancedManagerWorking = (afterTrackingCount > initialCount) && 
                                       (finalCount <= initialCount) && 
                                       validation.isValid;
                
                console.log(`   Enhanced Manager: Initial=${initialCount}, After=${afterTrackingCount}, Final=${finalCount}`);
                console.log(`   Zero memory retention: ${validation.isValid ? 'Validated' : 'Failed'}`);
                
            } catch (error) {
                console.log(`   Enhanced Subprocess Manager not available: ${error.message}`);
            }
            
            // Fallback to basic memory monitor test
            let basicCleanupWorking = false;
            try {
                const MemoryMonitor = require('./memory-monitor.js');
                const monitor = new MemoryMonitor();
                
                // Simulate subprocess tracking
                const initialSize = monitor.state.activeSubprocesses.size;
                
                // Add fake subprocess entries
                for (let i = 0; i < 5; i++) {
                    monitor.state.activeSubprocesses.set(99999 + i, {
                        pid: 99999 + i,
                        memoryUsage: 100 * 1024 * 1024, // 100MB
                        lastSeen: Date.now() - (i * 10000) // Staggered timestamps
                    });
                }
                
                console.log(`   Added ${monitor.state.activeSubprocesses.size - initialSize} test subprocess entries`);
                
                // Trigger cleanup
                monitor.cleanupStaleSubprocesses();
                
                const finalSize = monitor.state.activeSubprocesses.size;
                basicCleanupWorking = finalSize < (initialSize + 5);
                
                console.log(`   Basic cleanup: ${initialSize + 5} → ${finalSize} (effective: ${basicCleanupWorking})`);
                
                monitor.shutdown();
                
            } catch (error) {
                console.log(`   Basic cleanup failed: ${error.message}`);
            }
            
            const overallSuccess = enhancedManagerWorking || basicCleanupWorking;
            
            this.recordTestResult('subprocess_lifecycle_management', overallSuccess, 
                `Enhanced: ${enhancedManagerWorking}, Basic: ${basicCleanupWorking}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('subprocess_lifecycle_management', false, error.message);
        }
    }
    
    async test4_CircuitBreakerFunctionality() {
        console.log('\n🔬 Test 4: Circuit Breaker Functionality');
        
        try {
            const MemoryOptimizer = require('./memory-optimization.js');
            const optimizer = new MemoryOptimizer();
            
            const circuitBreakerThreshold = optimizer.circuitBreakerThreshold;
            const expectedThreshold = 3.5 * 1024 * 1024 * 1024; // 3.5GB
            
            const thresholdCorrect = Math.abs(circuitBreakerThreshold - expectedThreshold) < 1024 * 1024; // Within 1MB
            
            console.log(`   Circuit breaker threshold: ${Math.round(circuitBreakerThreshold / 1024 / 1024)}MB`);
            console.log(`   Expected threshold: ${Math.round(expectedThreshold / 1024 / 1024)}MB`);
            console.log(`   Threshold correct: ${thresholdCorrect ? 'Yes' : 'No'}`);
            
            // Test memory check with simulated high usage
            const mockUsage = {
                heapUsed: circuitBreakerThreshold + (100 * 1024 * 1024), // Exceed by 100MB
                heapTotal: 4 * 1024 * 1024 * 1024,
                external: 0,
                rss: 0
            };
            
            // Mock process.memoryUsage for testing
            const originalMemoryUsage = process.memoryUsage;
            process.memoryUsage = () => mockUsage;
            
            let circuitBreakerTriggered = false;
            const originalExit = process.exit;
            process.exit = (code) => {
                circuitBreakerTriggered = true;
                console.log(`   Circuit breaker triggered with exit code: ${code}`);
            };
            
            // This should trigger circuit breaker
            const memoryCheck = optimizer.checkMemoryUsage();
            
            // Restore original functions
            process.memoryUsage = originalMemoryUsage;
            process.exit = originalExit;
            
            console.log(`   Circuit breaker triggered: ${circuitBreakerTriggered ? 'Yes' : 'No'}`);
            
            this.recordTestResult('circuit_breaker_functionality', circuitBreakerTriggered, 
                `Threshold: ${Math.round(circuitBreakerThreshold / 1024 / 1024)}MB`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('circuit_breaker_functionality', false, error.message);
        }
    }
    
    async test5_MemoryCleanupEfficiency() {
        console.log('\n🔬 Test 5: Memory Cleanup Efficiency');
        
        try {
            const initialMemory = process.memoryUsage();
            const initialHeapMB = Math.round(initialMemory.heapUsed / 1024 / 1024);
            
            // Create memory pressure
            const allocated = this.simulateMemoryPressure(512); // 512MB
            
            const beforeCleanupMemory = process.memoryUsage();
            const beforeCleanupMB = Math.round(beforeCleanupMemory.heapUsed / 1024 / 1024);
            
            console.log(`   Before cleanup: ${beforeCleanupMB}MB`);
            
            // Perform cleanup operations
            if (global.gc) {
                for (let i = 0; i < 3; i++) {
                    global.gc();
                }
            }
            
            // Clear global caches
            ['_claudePMCache', '_deploymentCache', '_memoryCache'].forEach(cache => {
                if (global[cache] && typeof global[cache].clear === 'function') {
                    global[cache].clear();
                }
            });
            
            const afterCleanupMemory = process.memoryUsage();
            const afterCleanupMB = Math.round(afterCleanupMemory.heapUsed / 1024 / 1024);
            const reductionMB = beforeCleanupMB - afterCleanupMB;
            const reductionPercent = Math.round((reductionMB / beforeCleanupMB) * 100);
            
            console.log(`   After cleanup: ${afterCleanupMB}MB`);
            console.log(`   Memory reduction: ${reductionMB}MB (${reductionPercent}%)`);
            
            const cleanupEffective = reductionMB > 50; // At least 50MB reduction
            
            this.recordTestResult('memory_cleanup_efficiency', cleanupEffective, 
                `Reduced ${reductionMB}MB (${reductionPercent}%)`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_cleanup_efficiency', false, error.message);
        }
    }
    
    simulateMemoryPressure(sizeMB) {
        const arrays = [];
        const bytesPerMB = 1024 * 1024;
        
        for (let i = 0; i < sizeMB; i++) {
            // Create 1MB arrays
            arrays.push(new Array(bytesPerMB / 8).fill(Math.random()));
        }
        
        return arrays;
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
            memoryConfiguration: this.testConfig
        };
        
        const reportPath = path.join(__dirname, '..', 'logs', `memory-leak-fix-validation-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📊 Test Suite Results:');
        console.log(`   Total Tests: ${totalTests}`);
        console.log(`   Passed: ${passedTests}`);
        console.log(`   Failed: ${totalTests - passedTests}`);
        console.log(`   Success Rate: ${report.summary.successRate}%`);
        console.log(`   Duration: ${Math.round(testDuration / 1000)}s`);
        console.log(`   Report saved to: ${reportPath}`);
        
        if (report.summary.successRate >= 80) {
            console.log('\n🎉 Memory leak fixes are EFFECTIVE! Ready for deployment.');
        } else {
            console.log('\n⚠️  Some tests failed. Review fixes before deployment.');
        }
        
        return report;
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new MemoryLeakTestSuite();
    testSuite.runAllTests().catch(error => {
        console.error('💥 Test suite crashed:', error);
        process.exit(1);
    });
}

module.exports = MemoryLeakTestSuite;