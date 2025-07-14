#!/usr/bin/env node

/**
 * Enhanced Subprocess Management Test Suite
 * 
 * Comprehensive testing for subprocess lifecycle management and zero memory retention.
 * Tests integration with enhanced cache manager and memory monitoring systems.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');

class EnhancedSubprocessTestSuite {
    constructor() {
        this.testResults = [];
        this.startTime = Date.now();
        this.maxTestDuration = 300000; // 5 minutes max test duration
        
        // Test configuration
        this.testConfig = {
            maxSubprocesses: 2,
            subprocessMemoryLimit: 1024 * 1024 * 1024, // 1GB for testing
            subprocessTimeout: 60000, // 1 minute for testing
            cleanupInterval: 15000, // 15 seconds for testing
            memoryCheckInterval: 5000, // 5 seconds for testing
            stressTestDuration: 60000, // 1 minute stress test
            memoryLeakThreshold: 100 * 1024 * 1024 // 100MB threshold
        };
        
        console.log('🧪 Enhanced Subprocess Management Test Suite Starting...');
        console.log('📊 Test Configuration:');
        console.log(`   Max Subprocesses: ${this.testConfig.maxSubprocesses}`);
        console.log(`   Memory Limit: ${Math.round(this.testConfig.subprocessMemoryLimit / 1024 / 1024)}MB`);
        console.log(`   Subprocess Timeout: ${this.testConfig.subprocessTimeout / 1000}s`);
        console.log(`   Test Duration: ${this.maxTestDuration / 1000}s`);
    }
    
    async runAllTests() {
        try {
            console.log('\n🔬 Starting Enhanced Subprocess Management Tests...\n');
            
            await this.test1_SubprocessManagerInitialization();
            await this.test2_BasicSubprocessTracking();
            await this.test3_MemoryLimitEnforcement();
            await this.test4_TimeoutManagement();
            await this.test5_ZombieProcessDetection();
            await this.test6_GlobalMapCleanup();
            await this.test7_IntegrationWithCacheManager();
            await this.test8_MemoryLeakDetection();
            await this.test9_ConcurrentSubprocessManagement();
            await this.test10_ZeroMemoryRetentionValidation();
            await this.test11_StressTestWithMultipleSubprocesses();
            await this.test12_SystemIntegrationTest();
            
            this.generateComprehensiveTestReport();
            
        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            this.recordTestResult('test_suite_execution', false, error.message);
        }
    }
    
    async test1_SubprocessManagerInitialization() {
        console.log('🔬 Test 1: Enhanced Subprocess Manager Initialization');
        
        try {
            const { EnhancedSubprocessManager } = require('./enhanced-subprocess-manager.js');
            
            const manager = new EnhancedSubprocessManager({
                maxConcurrentSubprocesses: this.testConfig.maxSubprocesses,
                subprocessMemoryLimit: this.testConfig.subprocessMemoryLimit,
                subprocessTimeout: this.testConfig.subprocessTimeout,
                cleanupInterval: this.testConfig.cleanupInterval,
                memoryCheckInterval: this.testConfig.memoryCheckInterval,
                detailedLogging: true
            });
            
            const activeCount = manager.getActiveSubprocessCount();
            const metrics = manager.getPerformanceMetrics();
            
            console.log(`   Manager initialized with ${activeCount} active subprocesses`);
            console.log(`   Initial metrics: ${JSON.stringify(metrics)}`);
            
            const success = activeCount >= 0 && metrics !== null;
            this.recordTestResult('subprocess_manager_initialization', success, 
                `Active: ${activeCount}, Metrics available: ${metrics !== null}`);
            
            // Clean up
            manager.shutdown();
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('subprocess_manager_initialization', false, error.message);
        }
    }
    
    async test2_BasicSubprocessTracking() {
        console.log('\n🔬 Test 2: Basic Subprocess Tracking');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                maxConcurrentSubprocesses: this.testConfig.maxSubprocesses,
                detailedLogging: true
            });
            
            const initialCount = manager.getActiveSubprocessCount();
            
            // Create a test subprocess
            const testProcess = spawn('sleep', ['30'], { detached: false });
            const pid = testProcess.pid;
            
            console.log(`   Created test subprocess PID ${pid}`);
            
            // Track the subprocess
            manager.trackSubprocess(pid, {
                command: 'sleep 30',
                memoryUsage: 10 * 1024 * 1024 // 10MB
            });
            
            const afterTrackingCount = manager.getActiveSubprocessCount();
            const processInfo = manager.getSubprocessInfo(pid);
            
            console.log(`   Subprocess count: ${initialCount} → ${afterTrackingCount}`);
            console.log(`   Process info tracked: ${processInfo !== undefined}`);
            
            // Clean up
            testProcess.kill('SIGTERM');
            await this.sleep(2000); // Wait for termination
            
            manager.untrackSubprocess(pid, 'test_cleanup');
            const finalCount = manager.getActiveSubprocessCount();
            
            console.log(`   Final subprocess count: ${finalCount}`);
            
            const success = (afterTrackingCount === initialCount + 1) && 
                           (processInfo !== undefined) && 
                           (finalCount === initialCount);
            
            this.recordTestResult('basic_subprocess_tracking', success,
                `Initial: ${initialCount}, After tracking: ${afterTrackingCount}, Final: ${finalCount}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('basic_subprocess_tracking', false, error.message);
        }
    }
    
    async test3_MemoryLimitEnforcement() {
        console.log('\n🔬 Test 3: Memory Limit Enforcement');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                subprocessMemoryLimit: 50 * 1024 * 1024, // 50MB limit for testing
                strictMemoryEnforcement: true,
                detailedLogging: true
            });
            
            // Create a test subprocess and simulate high memory usage
            const testProcess = spawn('sleep', ['60'], { detached: false });
            const pid = testProcess.pid;
            
            console.log(`   Created test subprocess PID ${pid} with 50MB memory limit`);
            
            // Track with high memory usage (exceeding limit)
            manager.trackSubprocess(pid, {
                command: 'memory_test',
                memoryUsage: 100 * 1024 * 1024 // 100MB (exceeds 50MB limit)
            });
            
            const initialCount = manager.getActiveSubprocessCount();
            
            // Trigger memory check
            await this.sleep(1000);
            manager.performMemoryAwareCleanup();
            
            await this.sleep(3000); // Wait for termination
            
            const finalCount = manager.getActiveSubprocessCount();
            const processStillExists = manager.getSubprocessInfo(pid) !== undefined;
            
            console.log(`   Process count after memory enforcement: ${initialCount} → ${finalCount}`);
            console.log(`   Process still tracked: ${processStillExists}`);
            
            // Clean up if still exists
            if (testProcess.pid && !testProcess.killed) {
                testProcess.kill('SIGKILL');
            }
            
            const success = !processStillExists; // Process should be terminated for exceeding memory limit
            this.recordTestResult('memory_limit_enforcement', success,
                `Memory limit enforced: ${!processStillExists}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_limit_enforcement', false, error.message);
        }
    }
    
    async test4_TimeoutManagement() {
        console.log('\n🔬 Test 4: Timeout Management');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                subprocessTimeout: 5000, // 5 second timeout for testing
                detailedLogging: true
            });
            
            // Create a long-running subprocess
            const testProcess = spawn('sleep', ['30'], { detached: false });
            const pid = testProcess.pid;
            
            console.log(`   Created long-running subprocess PID ${pid} with 5s timeout`);
            
            // Track with creation time in the past (to simulate timeout)
            const pastTime = Date.now() - 10000; // 10 seconds ago
            manager.trackSubprocess(pid, {
                command: 'sleep 30',
                created: pastTime,
                memoryUsage: 10 * 1024 * 1024
            });
            
            const initialCount = manager.getActiveSubprocessCount();
            
            // Trigger timeout cleanup
            await this.sleep(1000);
            manager.performComprehensiveCleanup();
            
            await this.sleep(3000); // Wait for termination
            
            const finalCount = manager.getActiveSubprocessCount();
            const processStillExists = manager.getSubprocessInfo(pid) !== undefined;
            
            console.log(`   Process count after timeout: ${initialCount} → ${finalCount}`);
            console.log(`   Process still tracked: ${processStillExists}`);
            
            // Clean up if still exists
            if (testProcess.pid && !testProcess.killed) {
                testProcess.kill('SIGKILL');
            }
            
            const success = !processStillExists; // Process should be terminated for timeout
            this.recordTestResult('timeout_management', success,
                `Timeout enforced: ${!processStillExists}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('timeout_management', false, error.message);
        }
    }
    
    async test5_ZombieProcessDetection() {
        console.log('\n🔬 Test 5: Zombie Process Detection');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                zombieDetectionEnabled: true,
                detailedLogging: true
            });
            
            const initialMetrics = manager.getPerformanceMetrics();
            const initialZombiesKilled = initialMetrics.totalZombieProcessesKilled;
            
            console.log(`   Initial zombies killed: ${initialZombiesKilled}`);
            
            // Trigger zombie detection
            manager.performComprehensiveCleanup();
            
            const finalMetrics = manager.getPerformanceMetrics();
            const finalZombiesKilled = finalMetrics.totalZombieProcessesKilled;
            
            console.log(`   Final zombies killed: ${finalZombiesKilled}`);
            
            // Test passes if zombie detection runs without error
            const success = finalZombiesKilled >= initialZombiesKilled;
            this.recordTestResult('zombie_process_detection', success,
                `Zombies killed: ${finalZombiesKilled - initialZombiesKilled}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('zombie_process_detection', false, error.message);
        }
    }
    
    async test6_GlobalMapCleanup() {
        console.log('\n🔬 Test 6: Global Map Cleanup');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager();
            
            // Create test global maps
            global._testSubprocessCache = new Map();
            global._testProcessTracker = new Map();
            
            // Add test entries
            global._testSubprocessCache.set('test1', { data: 'test' });
            global._testProcessTracker.set('test2', { data: 'test' });
            
            console.log(`   Created test global maps with entries`);
            
            const initialCacheSize = global._testSubprocessCache.size;
            const initialTrackerSize = global._testProcessTracker.size;
            
            console.log(`   Initial sizes: cache=${initialCacheSize}, tracker=${initialTrackerSize}`);
            
            // Trigger comprehensive cleanup
            manager.cleanupGlobalProcessMaps();
            
            // Check if global maps were cleaned
            const finalCacheSize = global._testSubprocessCache ? global._testSubprocessCache.size : 0;
            const finalTrackerSize = global._testProcessTracker ? global._testProcessTracker.size : 0;
            
            console.log(`   Final sizes: cache=${finalCacheSize}, tracker=${finalTrackerSize}`);
            
            const success = (finalCacheSize === 0) && (finalTrackerSize === 0);
            this.recordTestResult('global_map_cleanup', success,
                `Maps cleaned: cache ${initialCacheSize}→${finalCacheSize}, tracker ${initialTrackerSize}→${finalTrackerSize}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('global_map_cleanup', false, error.message);
        }
    }
    
    async test7_IntegrationWithCacheManager() {
        console.log('\n🔬 Test 7: Integration with Enhanced Cache Manager');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            
            // Try to initialize enhanced cache manager
            let cacheManagerAvailable = false;
            try {
                const EnhancedCacheManager = require('./enhanced-cache-manager.js');
                global._enhancedCacheManager = new EnhancedCacheManager();
                cacheManagerAvailable = true;
                console.log('   Enhanced Cache Manager initialized');
            } catch (error) {
                console.log('   Enhanced Cache Manager not available for integration test');
            }
            
            const manager = getSubprocessManager({
                integrationWithMonitoring: true
            });
            
            // Trigger cleanup to test integration
            manager.performIntegrationCleanup();
            
            const success = true; // Test passes if no errors thrown
            this.recordTestResult('integration_with_cache_manager', success,
                `Cache manager available: ${cacheManagerAvailable}, Integration cleanup successful`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('integration_with_cache_manager', false, error.message);
        }
    }
    
    async test8_MemoryLeakDetection() {
        console.log('\n🔬 Test 8: Memory Leak Detection');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager();
            
            // Create a test subprocess
            const testProcess = spawn('sleep', ['60'], { detached: false });
            const pid = testProcess.pid;
            
            console.log(`   Created test subprocess PID ${pid} for memory leak simulation`);
            
            manager.trackSubprocess(pid, {
                command: 'memory_leak_test',
                memoryUsage: 50 * 1024 * 1024 // 50MB
            });
            
            // Simulate memory growth pattern
            const memoryGrowthPattern = [
                60 * 1024 * 1024,  // 60MB
                80 * 1024 * 1024,  // 80MB
                100 * 1024 * 1024, // 100MB
                120 * 1024 * 1024, // 120MB
                150 * 1024 * 1024  // 150MB
            ];
            
            for (let i = 0; i < memoryGrowthPattern.length; i++) {
                manager.trackMemoryUsage(pid, memoryGrowthPattern[i]);
                await this.sleep(100); // Small delay between measurements
            }
            
            const initialMetrics = manager.getPerformanceMetrics();
            const initialLeaksDetected = initialMetrics.totalMemoryLeaksDetected;
            
            console.log(`   Simulated memory growth pattern, leaks detected: ${initialLeaksDetected}`);
            
            // Clean up
            testProcess.kill('SIGTERM');
            manager.untrackSubprocess(pid, 'test_cleanup');
            
            const finalMetrics = manager.getPerformanceMetrics();
            const finalLeaksDetected = finalMetrics.totalMemoryLeaksDetected;
            
            const leaksDetected = finalLeaksDetected > initialLeaksDetected;
            console.log(`   Memory leak detection working: ${leaksDetected}`);
            
            this.recordTestResult('memory_leak_detection', leaksDetected,
                `Leaks detected: ${finalLeaksDetected - initialLeaksDetected}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('memory_leak_detection', false, error.message);
        }
    }
    
    async test9_ConcurrentSubprocessManagement() {
        console.log('\n🔬 Test 9: Concurrent Subprocess Management');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                maxConcurrentSubprocesses: 2,
                detailedLogging: true
            });
            
            // Create multiple test subprocesses
            const testProcesses = [];
            for (let i = 0; i < 4; i++) {
                const testProcess = spawn('sleep', ['30'], { detached: false });
                testProcesses.push(testProcess);
                
                manager.trackSubprocess(testProcess.pid, {
                    command: `concurrent_test_${i}`,
                    memoryUsage: 30 * 1024 * 1024 // 30MB each
                });
            }
            
            console.log(`   Created ${testProcesses.length} concurrent subprocesses`);
            
            const activeCount = manager.getActiveSubprocessCount();
            console.log(`   Active subprocess count: ${activeCount}`);
            
            // Trigger limit enforcement
            manager.enforceSubprocessLimits();
            
            await this.sleep(3000); // Wait for termination
            
            const finalActiveCount = manager.getActiveSubprocessCount();
            console.log(`   Final active count after limit enforcement: ${finalActiveCount}`);
            
            // Clean up remaining processes
            for (const testProcess of testProcesses) {
                if (testProcess.pid && !testProcess.killed) {
                    testProcess.kill('SIGKILL');
                    manager.untrackSubprocess(testProcess.pid, 'test_cleanup');
                }
            }
            
            const success = finalActiveCount <= 2; // Should enforce 2 subprocess limit
            this.recordTestResult('concurrent_subprocess_management', success,
                `Concurrent limit enforced: ${activeCount} → ${finalActiveCount}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('concurrent_subprocess_management', false, error.message);
        }
    }
    
    async test10_ZeroMemoryRetentionValidation() {
        console.log('\n🔬 Test 10: Zero Memory Retention Validation');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager();
            
            // Create and clean up several subprocesses
            const testProcesses = [];
            for (let i = 0; i < 3; i++) {
                const testProcess = spawn('sleep', ['5'], { detached: false });
                testProcesses.push(testProcess);
                
                manager.trackSubprocess(testProcess.pid, {
                    command: `retention_test_${i}`,
                    memoryUsage: 20 * 1024 * 1024
                });
            }
            
            console.log(`   Created ${testProcesses.length} test subprocesses for retention validation`);
            
            // Wait for processes to finish naturally
            await this.sleep(7000);
            
            // Perform comprehensive cleanup
            manager.performComprehensiveCleanup();
            
            // Validate zero memory retention
            const validation = manager.validateZeroMemoryRetention();
            
            console.log(`   Memory retention validation: ${validation.isValid ? 'PASSED' : 'FAILED'}`);
            if (!validation.isValid) {
                console.log(`   Validation details:`, validation.validation);
            }
            
            // Clean up any remaining processes
            for (const testProcess of testProcesses) {
                if (testProcess.pid && !testProcess.killed) {
                    testProcess.kill('SIGKILL');
                }
            }
            
            this.recordTestResult('zero_memory_retention_validation', validation.isValid,
                `Validation: ${JSON.stringify(validation.validation)}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('zero_memory_retention_validation', false, error.message);
        }
    }
    
    async test11_StressTestWithMultipleSubprocesses() {
        console.log('\n🔬 Test 11: Stress Test with Multiple Subprocesses');
        
        try {
            const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
            const manager = getSubprocessManager({
                maxConcurrentSubprocesses: 3,
                cleanupInterval: 5000, // 5 second cleanup for stress test
                detailedLogging: false // Reduce logging for stress test
            });
            
            const stressTestDuration = 30000; // 30 seconds
            const processCreationInterval = 2000; // Create process every 2 seconds
            
            console.log(`   Starting ${stressTestDuration / 1000}s stress test...`);
            
            const initialMetrics = manager.getPerformanceMetrics();
            const createdProcesses = [];
            
            const stressInterval = setInterval(() => {
                // Create a short-lived subprocess
                const testProcess = spawn('sleep', ['3'], { detached: false });
                createdProcesses.push(testProcess);
                
                manager.trackSubprocess(testProcess.pid, {
                    command: 'stress_test',
                    memoryUsage: Math.random() * 100 * 1024 * 1024 // Random memory 0-100MB
                });
                
                console.log(`   Created stress test subprocess PID ${testProcess.pid}`);
            }, processCreationInterval);
            
            // Run stress test
            await this.sleep(stressTestDuration);
            clearInterval(stressInterval);
            
            console.log(`   Stress test complete, performing final cleanup...`);
            
            // Final cleanup
            manager.performComprehensiveCleanup();
            await this.sleep(3000);
            
            const finalMetrics = manager.getPerformanceMetrics();
            const finalActiveCount = manager.getActiveSubprocessCount();
            
            // Clean up any remaining processes
            for (const testProcess of createdProcesses) {
                if (testProcess.pid && !testProcess.killed) {
                    testProcess.kill('SIGKILL');
                }
            }
            
            const processesCreated = finalMetrics.totalSubprocessesCreated - initialMetrics.totalSubprocessesCreated;
            const processesTerminated = finalMetrics.totalSubprocessesTerminated - initialMetrics.totalSubprocessesTerminated;
            
            console.log(`   Stress test results: ${processesCreated} created, ${processesTerminated} terminated, ${finalActiveCount} remaining`);
            
            const success = (finalActiveCount <= 3) && (processesCreated > 0); // Should handle stress without issues
            this.recordTestResult('stress_test_multiple_subprocesses', success,
                `Created: ${processesCreated}, Terminated: ${processesTerminated}, Remaining: ${finalActiveCount}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('stress_test_multiple_subprocesses', false, error.message);
        }
    }
    
    async test12_SystemIntegrationTest() {
        console.log('\n🔬 Test 12: System Integration Test');
        
        try {
            // Test integration with all memory management systems
            const integrationResults = {};
            
            // Test Enhanced Subprocess Manager
            try {
                const { getSubprocessManager } = require('./enhanced-subprocess-manager.js');
                const manager = getSubprocessManager();
                integrationResults.enhancedSubprocessManager = true;
                console.log('   ✅ Enhanced Subprocess Manager integration successful');
            } catch (error) {
                integrationResults.enhancedSubprocessManager = false;
                console.log('   ❌ Enhanced Subprocess Manager integration failed');
            }
            
            // Test Memory Optimization integration
            try {
                const MemoryOptimizer = require('./memory-optimization.js');
                const optimizer = new MemoryOptimizer();
                optimizer.clearSubprocessCache(); // Should use enhanced manager
                integrationResults.memoryOptimization = true;
                console.log('   ✅ Memory Optimization integration successful');
            } catch (error) {
                integrationResults.memoryOptimization = false;
                console.log('   ❌ Memory Optimization integration failed');
            }
            
            // Test Memory Monitor integration
            try {
                const MemoryMonitor = require('./memory-monitor.js');
                const monitor = new MemoryMonitor();
                monitor.cleanupGlobalSubprocessMaps(); // Should use enhanced manager
                integrationResults.memoryMonitor = true;
                console.log('   ✅ Memory Monitor integration successful');
                monitor.shutdown();
            } catch (error) {
                integrationResults.memoryMonitor = false;
                console.log('   ❌ Memory Monitor integration failed');
            }
            
            // Test Enhanced Cache Manager integration
            try {
                const EnhancedCacheManager = require('./enhanced-cache-manager.js');
                const cacheManager = new EnhancedCacheManager();
                integrationResults.enhancedCacheManager = true;
                console.log('   ✅ Enhanced Cache Manager integration successful');
                cacheManager.shutdown();
            } catch (error) {
                integrationResults.enhancedCacheManager = false;
                console.log('   ❌ Enhanced Cache Manager integration failed');
            }
            
            const successfulIntegrations = Object.values(integrationResults).filter(result => result).length;
            const totalIntegrations = Object.keys(integrationResults).length;
            
            console.log(`   Integration results: ${successfulIntegrations}/${totalIntegrations} successful`);
            
            const success = successfulIntegrations >= 3; // At least 3 out of 4 integrations should work
            this.recordTestResult('system_integration_test', success,
                `Integrations: ${JSON.stringify(integrationResults)}`);
            
        } catch (error) {
            console.log(`   ❌ Test failed: ${error.message}`);
            this.recordTestResult('system_integration_test', false, error.message);
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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
    
    generateComprehensiveTestReport() {
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
                totalMemory: require('os').totalmem(),
                freeMemory: require('os').freemem(),
                cpuCount: require('os').cpus().length
            },
            testConfiguration: this.testConfig,
            recommendations: this.generateRecommendations()
        };
        
        const reportPath = path.join(__dirname, '..', 'logs', `enhanced-subprocess-test-report-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📊 Enhanced Subprocess Management Test Results:');
        console.log(`   Total Tests: ${totalTests}`);
        console.log(`   Passed: ${passedTests}`);
        console.log(`   Failed: ${totalTests - passedTests}`);
        console.log(`   Success Rate: ${report.summary.successRate}%`);
        console.log(`   Duration: ${Math.round(testDuration / 1000)}s`);
        console.log(`   Report saved to: ${reportPath}`);
        
        if (report.summary.successRate >= 90) {
            console.log('\n🎉 Enhanced Subprocess Management is HIGHLY EFFECTIVE! Ready for deployment.');
        } else if (report.summary.successRate >= 75) {
            console.log('\n✅ Enhanced Subprocess Management is EFFECTIVE! Minor improvements recommended.');
        } else {
            console.log('\n⚠️  Some critical tests failed. Review implementation before deployment.');
        }
        
        if (report.recommendations.length > 0) {
            console.log('\n💡 Recommendations:');
            report.recommendations.forEach(rec => console.log(`   • ${rec}`));
        }
        
        return report;
    }
    
    generateRecommendations() {
        const recommendations = [];
        const passedTests = this.testResults.filter(r => r.success).length;
        const totalTests = this.testResults.length;
        const successRate = (passedTests / totalTests) * 100;
        
        if (successRate < 90) {
            const failedTests = this.testResults.filter(r => !r.success);
            recommendations.push(`Review failed tests: ${failedTests.map(t => t.testName).join(', ')}`);
        }
        
        const memoryTests = this.testResults.filter(r => r.testName.includes('memory'));
        const memoryTestsPassed = memoryTests.filter(r => r.success).length;
        
        if (memoryTestsPassed < memoryTests.length) {
            recommendations.push('Memory management tests show issues - review memory limits and leak detection');
        }
        
        const integrationTest = this.testResults.find(r => r.testName === 'system_integration_test');
        if (integrationTest && !integrationTest.success) {
            recommendations.push('System integration issues detected - ensure all components are properly integrated');
        }
        
        if (successRate >= 90) {
            recommendations.push('Excellent performance - system ready for production deployment');
        }
        
        return recommendations;
    }
}

// Run tests if called directly
if (require.main === module) {
    const testSuite = new EnhancedSubprocessTestSuite();
    testSuite.runAllTests().catch(error => {
        console.error('💥 Enhanced subprocess test suite crashed:', error);
        process.exit(1);
    });
}

module.exports = EnhancedSubprocessTestSuite;