#!/usr/bin/env node

/**
 * Claude PM CLI Module Test Framework
 * 
 * Provides comprehensive testing infrastructure for modularized CLI components.
 * Supports unit testing, integration testing, performance benchmarking, and compatibility validation.
 * 
 * Part of ISS-0085: Module extraction testing framework
 */

const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');

class ModuleTestFramework {
    constructor() {
        this.testResults = new Map();
        this.performanceMetrics = new Map();
        this.testStartTime = null;
        this.totalTests = 0;
        this.passedTests = 0;
        this.failedTests = 0;
        this.skippedTests = 0;
        this.moduleLoader = null;
    }

    /**
     * Initialize test framework with module loader
     * @param {Object} moduleLoader - Module loader instance
     */
    async init(moduleLoader) {
        this.moduleLoader = moduleLoader;
        this.testStartTime = performance.now();
        console.log('🧪 Initializing Claude PM CLI Module Test Framework');
        console.log('=' .repeat(60));
    }

    /**
     * Run comprehensive test suite for all modules
     * @returns {Object} Test results summary
     */
    async runFullTestSuite() {
        console.log('\n🚀 Running Full Module Test Suite...\n');

        // Phase 1: Unit tests for individual modules
        await this.runUnitTests();

        // Phase 2: Integration tests for module interactions
        await this.runIntegrationTests();

        // Phase 3: Performance benchmarks
        await this.runPerformanceTests();

        // Phase 4: Compatibility validation
        await this.runCompatibilityTests();

        return this.generateTestReport();
    }

    /**
     * Run unit tests for individual modules
     */
    async runUnitTests() {
        console.log('📋 Phase 1: Unit Tests');
        console.log('-' .repeat(30));

        const modules = ['version-resolver', 'environment-validator', 'display-manager'];
        
        for (const moduleName of modules) {
            await this.testModule(moduleName);
        }
    }

    /**
     * Test individual module functionality
     * @param {string} moduleName - Name of module to test
     */
    async testModule(moduleName) {
        console.log(`\n🔍 Testing module: ${moduleName}`);
        
        const testResult = {
            moduleName,
            tests: [],
            passed: 0,
            failed: 0,
            duration: 0,
            memoryImpact: 0
        };

        const startTime = performance.now();
        const initialMemory = process.memoryUsage().heapUsed;

        try {
            // Test module loading
            await this.testModuleLoading(moduleName, testResult);
            
            // Test module interface
            await this.testModuleInterface(moduleName, testResult);
            
            // Test module functionality
            await this.testModuleFunctionality(moduleName, testResult);
            
            // Test module cleanup
            await this.testModuleCleanup(moduleName, testResult);

        } catch (error) {
            this.addTestResult(testResult, 'module-execution', false, `Module test failed: ${error.message}`);
        }

        const endTime = performance.now();
        const finalMemory = process.memoryUsage().heapUsed;
        
        testResult.duration = endTime - startTime;
        testResult.memoryImpact = finalMemory - initialMemory;
        
        this.testResults.set(moduleName, testResult);
        this.updateTestCounts(testResult);
        
        console.log(`   ✅ Passed: ${testResult.passed}`);
        console.log(`   ❌ Failed: ${testResult.failed}`);
        console.log(`   ⏱️  Duration: ${Math.round(testResult.duration)}ms`);
        console.log(`   💾 Memory: ${Math.round(testResult.memoryImpact / 1024)}KB`);
    }

    /**
     * Test module loading functionality
     * @param {string} moduleName - Module name
     * @param {Object} testResult - Test result object
     */
    async testModuleLoading(moduleName, testResult) {
        try {
            const module = await this.moduleLoader.loadModule(moduleName);
            this.addTestResult(testResult, 'module-loading', !!module, 'Module loaded successfully');
            
            // Test module is cached
            const cachedModule = await this.moduleLoader.loadModule(moduleName);
            this.addTestResult(testResult, 'module-caching', module === cachedModule, 'Module caching works');
            
        } catch (error) {
            this.addTestResult(testResult, 'module-loading', false, `Loading failed: ${error.message}`);
        }
    }

    /**
     * Test module interface compliance
     * @param {string} moduleName - Module name
     * @param {Object} testResult - Test result object
     */
    async testModuleInterface(moduleName, testResult) {
        try {
            const module = await this.moduleLoader.loadModule(moduleName);
            
            // Test required methods
            this.addTestResult(testResult, 'main-method', typeof module.main === 'function', 'Main method exists');
            this.addTestResult(testResult, 'config-object', typeof module.config === 'object', 'Config object exists');
            this.addTestResult(testResult, 'dependencies-array', Array.isArray(module.dependencies), 'Dependencies array exists');
            this.addTestResult(testResult, 'cleanup-method', typeof module.cleanup === 'function', 'Cleanup method exists');
            
            // Test config properties
            if (module.config) {
                this.addTestResult(testResult, 'config-name', !!module.config.name, 'Config has name');
                this.addTestResult(testResult, 'config-version', !!module.config.version, 'Config has version');
                this.addTestResult(testResult, 'config-description', !!module.config.description, 'Config has description');
            }
            
        } catch (error) {
            this.addTestResult(testResult, 'interface-validation', false, `Interface test failed: ${error.message}`);
        }
    }

    /**
     * Test module-specific functionality
     * @param {string} moduleName - Module name
     * @param {Object} testResult - Test result object
     */
    async testModuleFunctionality(moduleName, testResult) {
        try {
            const module = await this.moduleLoader.loadModule(moduleName);
            
            switch (moduleName) {
                case 'version-resolver':
                    await this.testVersionResolver(module, testResult);
                    break;
                case 'environment-validator':
                    await this.testEnvironmentValidator(module, testResult);
                    break;
                case 'display-manager':
                    await this.testDisplayManager(module, testResult);
                    break;
            }
            
        } catch (error) {
            this.addTestResult(testResult, 'functionality-test', false, `Functionality test failed: ${error.message}`);
        }
    }

    /**
     * Test version resolver functionality
     * @param {Object} module - Version resolver module
     * @param {Object} testResult - Test result object
     */
    async testVersionResolver(module, testResult) {
        // Test version resolution
        try {
            const version = module.main();
            this.addTestResult(testResult, 'version-resolution', !!version, 'Version resolved successfully');
            this.addTestResult(testResult, 'version-format', /^\d+\.\d+\.\d+/.test(version), 'Version has valid format');
        } catch (error) {
            this.addTestResult(testResult, 'version-resolution', false, `Version resolution failed: ${error.message}`);
        }

        // Test diagnostics
        try {
            const diagnostics = module.getDiagnostics();
            this.addTestResult(testResult, 'diagnostics', !!diagnostics, 'Diagnostics available');
            this.addTestResult(testResult, 'diagnostics-strategies', !!diagnostics.strategies, 'Diagnostics has strategies');
        } catch (error) {
            this.addTestResult(testResult, 'diagnostics', false, `Diagnostics failed: ${error.message}`);
        }

        // Test cache functionality
        try {
            module.clearCache();
            this.addTestResult(testResult, 'cache-clear', true, 'Cache clear works');
        } catch (error) {
            this.addTestResult(testResult, 'cache-clear', false, `Cache clear failed: ${error.message}`);
        }
    }

    /**
     * Test environment validator functionality
     * @param {Object} module - Environment validator module
     * @param {Object} testResult - Test result object
     */
    async testEnvironmentValidator(module, testResult) {
        // Test environment validation
        try {
            const validation = module.main();
            this.addTestResult(testResult, 'environment-validation', !!validation, 'Environment validation works');
            this.addTestResult(testResult, 'validation-structure', 
                validation.platform && validation.hasOwnProperty('python') && validation.hasOwnProperty('overall'),
                'Validation has required properties');
        } catch (error) {
            this.addTestResult(testResult, 'environment-validation', false, `Environment validation failed: ${error.message}`);
        }

        // Test platform detection
        try {
            const platform = module.detectPlatformInfo();
            this.addTestResult(testResult, 'platform-detection', !!platform, 'Platform detection works');
            this.addTestResult(testResult, 'platform-properties', 
                platform.platform && platform.arch && platform.hasOwnProperty('isWSL2'),
                'Platform has required properties');
        } catch (error) {
            this.addTestResult(testResult, 'platform-detection', false, `Platform detection failed: ${error.message}`);
        }

        // Test Python validation
        try {
            const python = module.validatePython();
            this.addTestResult(testResult, 'python-validation', python !== undefined, 'Python validation completes');
        } catch (error) {
            this.addTestResult(testResult, 'python-validation', false, `Python validation failed: ${error.message}`);
        }
    }

    /**
     * Test display manager functionality
     * @param {Object} module - Display manager module
     * @param {Object} testResult - Test result object
     */
    async testDisplayManager(module, testResult) {
        // Test buffering functionality
        try {
            module.startBuffering();
            module.output('Test output');
            const buffer = module.getBuffer();
            this.addTestResult(testResult, 'output-buffering', buffer.length > 0, 'Output buffering works');
            
            module.clearBuffer();
            const clearedBuffer = module.getBuffer();
            this.addTestResult(testResult, 'buffer-clear', clearedBuffer.length === 0, 'Buffer clear works');
        } catch (error) {
            this.addTestResult(testResult, 'output-buffering', false, `Output buffering failed: ${error.message}`);
        }

        // Test indentation
        try {
            module.clearBuffer();
            module.startBuffering();
            module.output('Level 0');
            module.indent();
            module.output('Level 1');
            module.outdent();
            module.output('Level 0 again');
            
            const buffer = module.getBuffer();
            this.addTestResult(testResult, 'indentation', 
                buffer.length === 3 && buffer[1].startsWith('   '),
                'Indentation works correctly');
        } catch (error) {
            this.addTestResult(testResult, 'indentation', false, `Indentation failed: ${error.message}`);
        }

        // Test platform notes
        try {
            const notes = module.getPlatformNotes('darwin');
            this.addTestResult(testResult, 'platform-notes', Array.isArray(notes) && notes.length > 0, 'Platform notes work');
        } catch (error) {
            this.addTestResult(testResult, 'platform-notes', false, `Platform notes failed: ${error.message}`);
        }
    }

    /**
     * Test module cleanup functionality
     * @param {string} moduleName - Module name
     * @param {Object} testResult - Test result object
     */
    async testModuleCleanup(moduleName, testResult) {
        try {
            const module = await this.moduleLoader.loadModule(moduleName);
            await module.cleanup();
            this.addTestResult(testResult, 'cleanup', true, 'Cleanup completed successfully');
        } catch (error) {
            this.addTestResult(testResult, 'cleanup', false, `Cleanup failed: ${error.message}`);
        }
    }

    /**
     * Run integration tests for module interactions
     */
    async runIntegrationTests() {
        console.log('\n🔗 Phase 2: Integration Tests');
        console.log('-' .repeat(30));

        // Test module loader statistics
        await this.testModuleLoaderIntegration();
        
        // Test memory management across modules
        await this.testMemoryManagement();
    }

    /**
     * Test module loader integration
     */
    async testModuleLoaderIntegration() {
        console.log('\n🔍 Testing module loader integration...');
        
        try {
            const stats = this.moduleLoader.getStats();
            console.log(`   📊 Modules loaded: ${stats.totalModulesLoaded}`);
            console.log(`   💾 Total memory impact: ${stats.totalMemoryImpactMB}MB`);
            
            const health = this.moduleLoader.healthCheck();
            console.log(`   ✅ Health status: ${health.status}`);
            console.log(`   📋 Available modules: ${health.availableModules}`);
        } catch (error) {
            console.log(`   ❌ Integration test failed: ${error.message}`);
        }
    }

    /**
     * Test memory management across modules
     */
    async testMemoryManagement() {
        console.log('\n💾 Testing memory management...');
        
        const initialMemory = process.memoryUsage();
        
        // Load all modules
        const modules = ['version-resolver', 'environment-validator', 'display-manager'];
        for (const moduleName of modules) {
            await this.moduleLoader.loadModule(moduleName);
        }
        
        const loadedMemory = process.memoryUsage();
        
        // Cleanup all modules
        await this.moduleLoader.cleanup();
        
        const cleanedMemory = process.memoryUsage();
        
        const loadImpact = loadedMemory.heapUsed - initialMemory.heapUsed;
        const cleanupImpact = cleanedMemory.heapUsed - loadedMemory.heapUsed;
        
        console.log(`   📈 Memory impact of loading: ${Math.round(loadImpact / 1024)}KB`);
        console.log(`   📉 Memory cleanup impact: ${Math.round(cleanupImpact / 1024)}KB`);
        console.log(`   🎯 Net memory change: ${Math.round((cleanedMemory.heapUsed - initialMemory.heapUsed) / 1024)}KB`);
    }

    /**
     * Run performance tests
     */
    async runPerformanceTests() {
        console.log('\n⚡ Phase 3: Performance Tests');
        console.log('-' .repeat(30));

        await this.benchmarkModuleLoading();
        await this.benchmarkMemoryUsage();
    }

    /**
     * Benchmark module loading performance
     */
    async benchmarkModuleLoading() {
        console.log('\n⏱️  Benchmarking module loading...');
        
        const modules = ['version-resolver', 'environment-validator', 'display-manager'];
        
        for (const moduleName of modules) {
            const startTime = performance.now();
            await this.moduleLoader.loadModule(moduleName);
            const endTime = performance.now();
            
            const duration = endTime - startTime;
            console.log(`   ${moduleName}: ${Math.round(duration)}ms`);
            
            this.performanceMetrics.set(`${moduleName}-load-time`, duration);
        }
    }

    /**
     * Benchmark memory usage
     */
    async benchmarkMemoryUsage() {
        console.log('\n💾 Benchmarking memory usage...');
        
        const stats = this.moduleLoader.getStats();
        for (const [moduleName, moduleStats] of Object.entries(stats.modules)) {
            console.log(`   ${moduleName}: ${moduleStats.memoryImpactMB}MB`);
        }
        
        console.log(`   Total: ${stats.totalMemoryImpactMB}MB`);
    }

    /**
     * Run compatibility tests
     */
    async runCompatibilityTests() {
        console.log('\n🔧 Phase 4: Compatibility Tests');
        console.log('-' .repeat(30));

        // Test Node.js version compatibility
        this.testNodeJSCompatibility();
        
        // Test platform compatibility
        this.testPlatformCompatibility();
    }

    /**
     * Test Node.js version compatibility
     */
    testNodeJSCompatibility() {
        console.log('\n🟢 Testing Node.js compatibility...');
        
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.match(/^v(\d+)/)[1]);
        
        console.log(`   Node.js version: ${nodeVersion}`);
        
        if (majorVersion >= 14) {
            console.log('   ✅ Node.js version is compatible');
        } else {
            console.log('   ⚠️  Node.js version may have compatibility issues');
        }
    }

    /**
     * Test platform compatibility
     */
    testPlatformCompatibility() {
        console.log('\n🖥️  Testing platform compatibility...');
        
        const platform = process.platform;
        const supportedPlatforms = ['darwin', 'linux', 'win32'];
        
        console.log(`   Platform: ${platform}`);
        
        if (supportedPlatforms.includes(platform)) {
            console.log('   ✅ Platform is supported');
        } else {
            console.log('   ⚠️  Platform support may be limited');
        }
    }

    /**
     * Add test result
     * @param {Object} testResult - Test result object
     * @param {string} testName - Name of the test
     * @param {boolean} passed - Whether test passed
     * @param {string} message - Test message
     */
    addTestResult(testResult, testName, passed, message) {
        testResult.tests.push({
            name: testName,
            passed: passed,
            message: message
        });
        
        if (passed) {
            testResult.passed++;
        } else {
            testResult.failed++;
        }
    }

    /**
     * Update global test counts
     * @param {Object} testResult - Test result object
     */
    updateTestCounts(testResult) {
        this.totalTests += testResult.tests.length;
        this.passedTests += testResult.passed;
        this.failedTests += testResult.failed;
    }

    /**
     * Generate comprehensive test report
     * @returns {Object} Test report
     */
    generateTestReport() {
        const endTime = performance.now();
        const totalDuration = endTime - this.testStartTime;
        
        const report = {
            summary: {
                totalTests: this.totalTests,
                passed: this.passedTests,
                failed: this.failedTests,
                skipped: this.skippedTests,
                successRate: this.totalTests > 0 ? (this.passedTests / this.totalTests * 100).toFixed(2) : 0,
                duration: totalDuration
            },
            modules: Array.from(this.testResults.values()),
            performance: Object.fromEntries(this.performanceMetrics),
            timestamp: new Date().toISOString()
        };

        this.displayTestReport(report);
        return report;
    }

    /**
     * Display test report
     * @param {Object} report - Test report
     */
    displayTestReport(report) {
        console.log('\n📊 Test Report Summary');
        console.log('=' .repeat(40));
        console.log(`Total Tests: ${report.summary.totalTests}`);
        console.log(`Passed: ${report.summary.passed} ✅`);
        console.log(`Failed: ${report.summary.failed} ❌`);
        console.log(`Success Rate: ${report.summary.successRate}%`);
        console.log(`Total Duration: ${Math.round(report.summary.duration)}ms`);
        
        if (report.summary.failed > 0) {
            console.log('\n❌ Failed Tests:');
            for (const moduleResult of report.modules) {
                const failedTests = moduleResult.tests.filter(test => !test.passed);
                if (failedTests.length > 0) {
                    console.log(`\n   ${moduleResult.moduleName}:`);
                    for (const test of failedTests) {
                        console.log(`   • ${test.name}: ${test.message}`);
                    }
                }
            }
        }
        
        console.log('\n✅ Test suite completed!');
    }

    /**
     * Save test report to file
     * @param {Object} report - Test report
     * @param {string} filename - Output filename
     */
    async saveTestReport(report, filename = 'module-test-report.json') {
        try {
            const reportPath = path.join(__dirname, filename);
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            console.log(`📄 Test report saved to: ${reportPath}`);
        } catch (error) {
            console.error(`❌ Failed to save test report: ${error.message}`);
        }
    }
}

module.exports = ModuleTestFramework;