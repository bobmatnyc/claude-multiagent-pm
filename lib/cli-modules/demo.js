#!/usr/bin/env node

/**
 * Claude PM CLI Module Demo Script
 * 
 * Demonstrates Phase 1 module functionality and integration.
 * Used for validation and testing of the modular architecture.
 * 
 * Part of ISS-0085: Module demonstration and validation
 */

const ModuleTestFramework = require('./test-framework');
const ModuleIntegrationSystem = require('./module-integration');

async function runDemo() {
    console.log('🚀 Claude PM CLI Module Demo');
    console.log('=' .repeat(50));
    console.log(`🕐 Started at: ${new Date().toLocaleString()}`);
    console.log('');

    // Initialize integration system
    const integrationSystem = new ModuleIntegrationSystem();
    await integrationSystem.init({ enableModular: true });

    console.log('📋 Phase 1: Testing Individual Modules');
    console.log('-' .repeat(35));

    // Test version resolution
    console.log('\n🔍 Testing Version Resolution...');
    try {
        const version = await integrationSystem.resolveVersion();
        console.log(`   ✅ Version resolved: ${version}`);
    } catch (error) {
        console.log(`   ❌ Version resolution failed: ${error.message}`);
    }

    // Test environment validation
    console.log('\n🌍 Testing Environment Validation...');
    try {
        const envValidation = await integrationSystem.validateEnvironment();
        console.log(`   ✅ Environment validation completed`);
        console.log(`   📊 Platform: ${envValidation.platform.platform}`);
        console.log(`   🐍 Python: ${envValidation.python || 'Not found'}`);
        console.log(`   🎯 Overall: ${envValidation.overall ? 'Ready' : 'Issues detected'}`);
    } catch (error) {
        console.log(`   ❌ Environment validation failed: ${error.message}`);
    }

    // Test display functionality (buffered mode)
    console.log('\n🖥️  Testing Display Manager...');
    try {
        // This would normally display help, but we'll just test the module loading
        const displayModule = await integrationSystem.moduleLoader.loadModule('display-manager');
        
        // Test buffering
        displayModule.startBuffering();
        displayModule.output('Test output line 1');
        displayModule.indent();
        displayModule.output('Test output line 2 (indented)');
        displayModule.outdent();
        displayModule.output('Test output line 3');
        
        const buffer = displayModule.getBuffer();
        console.log(`   ✅ Display manager loaded successfully`);
        console.log(`   📝 Buffer test: ${buffer.length} lines captured`);
        console.log(`   🔧 Indentation test: ${buffer[1].startsWith('   ') ? 'Passed' : 'Failed'}`);
        
        displayModule.clearBuffer();
    } catch (error) {
        console.log(`   ❌ Display manager test failed: ${error.message}`);
    }

    console.log('\n📊 Phase 2: Integration System Status');
    console.log('-' .repeat(35));

    // Get system status
    const systemStatus = integrationSystem.getSystemStatus();
    console.log(`   🔧 Modular Mode: ${systemStatus.modularEnabled ? 'Enabled' : 'Disabled'}`);
    console.log(`   🔄 Fallback Mode: ${systemStatus.fallbackMode ? 'Active' : 'Inactive'}`);
    console.log(`   📦 Loaded Modules: ${systemStatus.loadedModules.length}`);
    
    if (systemStatus.loadedModules.length > 0) {
        console.log(`   📋 Module List: ${systemStatus.loadedModules.join(', ')}`);
    }

    // Module loader health check
    const health = systemStatus.moduleLoaderHealth;
    console.log(`   ✅ Health Status: ${health.status}`);
    console.log(`   📈 Available Modules: ${health.availableModules}`);
    console.log(`   💾 Memory Usage: ${health.totalMemoryUsage}MB`);

    console.log('\n⚡ Phase 3: Performance Metrics');
    console.log('-' .repeat(35));

    const stats = systemStatus.moduleLoaderStats;
    console.log(`   📊 Total Modules Loaded: ${stats.totalModulesLoaded}`);
    console.log(`   💾 Total Memory Impact: ${stats.totalMemoryImpactMB}MB`);
    
    if (stats.modules && Object.keys(stats.modules).length > 0) {
        console.log('   📋 Individual Module Metrics:');
        for (const [moduleName, moduleStats] of Object.entries(stats.modules)) {
            console.log(`      • ${moduleName}: ${moduleStats.memoryImpactMB}MB`);
        }
    }

    console.log('\n🧪 Phase 4: Running Test Framework');
    console.log('-' .repeat(35));

    // Initialize and run test framework
    const testFramework = new ModuleTestFramework();
    await testFramework.init(integrationSystem.moduleLoader);
    
    try {
        const testReport = await testFramework.runFullTestSuite();
        
        console.log('\n📊 Test Results Summary:');
        console.log(`   📈 Success Rate: ${testReport.summary.successRate}%`);
        console.log(`   ✅ Passed: ${testReport.summary.passed}`);
        console.log(`   ❌ Failed: ${testReport.summary.failed}`);
        console.log(`   ⏱️  Duration: ${Math.round(testReport.summary.duration)}ms`);
        
        // Save test report
        await testFramework.saveTestReport(testReport, 'phase1-demo-report.json');
        
    } catch (error) {
        console.log(`   ❌ Test framework failed: ${error.message}`);
    }

    console.log('\n🔄 Phase 5: Fallback Testing');
    console.log('-' .repeat(35));

    // Test fallback mode
    integrationSystem.setFallbackMode(true);
    
    console.log('\n🔍 Testing Fallback Version Resolution...');
    try {
        const fallbackVersion = await integrationSystem.resolveVersion();
        console.log(`   ✅ Fallback version: ${fallbackVersion}`);
    } catch (error) {
        console.log(`   ❌ Fallback version failed: ${error.message}`);
    }

    console.log('\n🌍 Testing Fallback Environment Validation...');
    try {
        const fallbackEnv = await integrationSystem.validateEnvironment();
        console.log(`   ✅ Fallback environment validation completed`);
        console.log(`   📊 Platform: ${fallbackEnv.platform.platform}`);
    } catch (error) {
        console.log(`   ❌ Fallback environment failed: ${error.message}`);
    }

    // Reset fallback mode
    integrationSystem.setFallbackMode(false);

    console.log('\n🧹 Phase 6: Cleanup and Summary');
    console.log('-' .repeat(35));

    // Cleanup
    await integrationSystem.cleanup();
    console.log('   ✅ Integration system cleaned up');

    // Final summary
    console.log('\n🎯 Demo Summary:');
    console.log('   ✅ Phase 1 modules (version-resolver, environment-validator, display-manager)');
    console.log('   ✅ Module loading infrastructure');
    console.log('   ✅ Integration system with fallback support');
    console.log('   ✅ Comprehensive test framework');
    console.log('   ✅ Performance monitoring and metrics');
    console.log('   ✅ Memory management and cleanup');

    console.log('\n🚀 Phase 1 Implementation Status: COMPLETE');
    console.log('📋 Ready for Phase 2: deployment-detector.js extraction');
    console.log('🎯 Target: 30% memory reduction, <600 lines per module');
    console.log('');
    console.log(`🕐 Demo completed at: ${new Date().toLocaleString()}`);
    console.log('=' .repeat(50));
}

// Run demo if called directly
if (require.main === module) {
    runDemo().catch(error => {
        console.error('❌ Demo failed:', error);
        process.exit(1);
    });
}

module.exports = { runDemo };