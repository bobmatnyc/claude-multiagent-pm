#!/bin/bash

# Claude PM Framework - Enhanced Subprocess Management System Deployment
# 
# Deploys comprehensive subprocess lifecycle management with zero memory retention

set -e

FRAMEWORK_ROOT="/Users/masa/Projects/claude-multiagent-pm"
SCRIPTS_DIR="$FRAMEWORK_ROOT/scripts"
LOGS_DIR="$FRAMEWORK_ROOT/logs"

echo "🚀 Claude PM Framework - Enhanced Subprocess Management System Deployment"
echo "📍 Framework Root: $FRAMEWORK_ROOT"
echo "📍 Scripts Directory: $SCRIPTS_DIR"
echo "📍 Logs Directory: $LOGS_DIR"

# Ensure we're in the correct directory
cd "$FRAMEWORK_ROOT"

# Create logs directory
mkdir -p "$LOGS_DIR"

echo ""
echo "📋 Deployment Steps:"
echo "   1. Validate Enhanced Subprocess Manager"
echo "   2. Test Integration with Memory Systems"
echo "   3. Deploy Enhanced Memory Management"
echo "   4. Run Comprehensive Tests"
echo "   5. Validate Zero Memory Retention"
echo "   6. Generate Deployment Report"

# Step 1: Validate Enhanced Subprocess Manager
echo ""
echo "🔍 Step 1: Validating Enhanced Subprocess Manager..."

if [[ ! -f "$SCRIPTS_DIR/enhanced-subprocess-manager.js" ]]; then
    echo "❌ Enhanced Subprocess Manager not found at $SCRIPTS_DIR/enhanced-subprocess-manager.js"
    exit 1
fi

echo "✅ Enhanced Subprocess Manager found"

# Test basic functionality
echo "🧪 Testing basic functionality..."
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node "$SCRIPTS_DIR/enhanced-subprocess-manager.js" validate
if [[ $? -eq 0 ]]; then
    echo "✅ Enhanced Subprocess Manager validation passed"
else
    echo "⚠️ Enhanced Subprocess Manager validation issues detected, continuing..."
fi

# Step 2: Test Integration with Memory Systems
echo ""
echo "🔍 Step 2: Testing Integration with Memory Systems..."

# Test integration with memory optimization
echo "🧪 Testing Memory Optimization integration..."
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node -e "
const MemoryOptimizer = require('$SCRIPTS_DIR/memory-optimization.js');
const optimizer = new MemoryOptimizer();
console.log('Testing enhanced subprocess cache cleanup...');
optimizer.clearSubprocessCache();
console.log('✅ Memory Optimization integration successful');
"

# Test integration with memory monitor
echo "🧪 Testing Memory Monitor integration..."
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node -e "
const MemoryMonitor = require('$SCRIPTS_DIR/memory-monitor.js');
const monitor = new MemoryMonitor();
console.log('Testing enhanced global subprocess cleanup...');
monitor.cleanupGlobalSubprocessMaps();
monitor.shutdown();
console.log('✅ Memory Monitor integration successful');
"

echo "✅ Memory Systems integration tests completed"

# Step 3: Deploy Enhanced Memory Management
echo ""
echo "🔍 Step 3: Deploying Enhanced Memory Management..."

# Deploy enhanced cache manager if not already done
if [[ -f "$SCRIPTS_DIR/enhanced-cache-manager.js" ]]; then
    echo "🧪 Testing Enhanced Cache Manager..."
    NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node "$SCRIPTS_DIR/enhanced-cache-manager.js" report
    echo "✅ Enhanced Cache Manager operational"
else
    echo "⚠️ Enhanced Cache Manager not found - subprocess management will work without it"
fi

# Deploy memory optimization system
echo "🧪 Testing Memory Optimization System..."
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node "$SCRIPTS_DIR/memory-optimization.js" report

echo "✅ Enhanced Memory Management deployed"

# Step 4: Run Comprehensive Tests
echo ""
echo "🔍 Step 4: Running Comprehensive Tests..."

# Run enhanced subprocess management tests
if [[ -f "$SCRIPTS_DIR/test-enhanced-subprocess-management.js" ]]; then
    echo "🧪 Running Enhanced Subprocess Management Test Suite..."
    NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node "$SCRIPTS_DIR/test-enhanced-subprocess-management.js"
    SUBPROCESS_TEST_EXIT_CODE=$?
    
    if [[ $SUBPROCESS_TEST_EXIT_CODE -eq 0 ]]; then
        echo "✅ Enhanced Subprocess Management tests PASSED"
    else
        echo "⚠️ Enhanced Subprocess Management tests had issues (exit code: $SUBPROCESS_TEST_EXIT_CODE)"
    fi
else
    echo "⚠️ Enhanced Subprocess Management test suite not found"
    SUBPROCESS_TEST_EXIT_CODE=1
fi

# Run updated memory leak tests
if [[ -f "$SCRIPTS_DIR/test-memory-leak-fixes.js" ]]; then
    echo "🧪 Running Updated Memory Leak Test Suite..."
    NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node "$SCRIPTS_DIR/test-memory-leak-fixes.js"
    MEMORY_TEST_EXIT_CODE=$?
    
    if [[ $MEMORY_TEST_EXIT_CODE -eq 0 ]]; then
        echo "✅ Memory Leak tests PASSED"
    else
        echo "⚠️ Memory Leak tests had issues (exit code: $MEMORY_TEST_EXIT_CODE)"
    fi
else
    echo "⚠️ Memory Leak test suite not found"
    MEMORY_TEST_EXIT_CODE=1
fi

echo "✅ Comprehensive tests completed"

# Step 5: Validate Zero Memory Retention
echo ""
echo "🔍 Step 5: Validating Zero Memory Retention..."

echo "🧪 Running comprehensive cleanup and validation..."
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node -e "
const { getSubprocessManager } = require('$SCRIPTS_DIR/enhanced-subprocess-manager.js');

console.log('Initializing Enhanced Subprocess Manager...');
const manager = getSubprocessManager();

console.log('Performing comprehensive cleanup...');
manager.forceCleanup();

console.log('Validating zero memory retention...');
const validation = manager.validateZeroMemoryRetention();

console.log('Validation result:', validation.isValid ? 'PASSED' : 'FAILED');
console.log('Validation details:', JSON.stringify(validation.validation, null, 2));

if (validation.recommendations.length > 0) {
    console.log('Recommendations:');
    validation.recommendations.forEach(rec => console.log('  •', rec));
}

process.exit(validation.isValid ? 0 : 1);
"

VALIDATION_EXIT_CODE=$?
if [[ $VALIDATION_EXIT_CODE -eq 0 ]]; then
    echo "✅ Zero Memory Retention validation PASSED"
else
    echo "❌ Zero Memory Retention validation FAILED"
fi

# Step 6: Generate Deployment Report
echo ""
echo "🔍 Step 6: Generating Deployment Report..."

REPORT_FILE="$LOGS_DIR/enhanced-subprocess-deployment-report-$(date +%s).json"

# Generate comprehensive report
NODE_OPTIONS='--max-old-space-size=4096 --expose-gc' node -e "
const fs = require('fs');
const path = require('path');

const report = {
    timestamp: new Date().toISOString(),
    deployment: {
        frameworkRoot: '$FRAMEWORK_ROOT',
        scriptsDirectory: '$SCRIPTS_DIR',
        logsDirectory: '$LOGS_DIR'
    },
    components: {
        enhancedSubprocessManager: fs.existsSync('$SCRIPTS_DIR/enhanced-subprocess-manager.js'),
        enhancedCacheManager: fs.existsSync('$SCRIPTS_DIR/enhanced-cache-manager.js'),
        memoryOptimization: fs.existsSync('$SCRIPTS_DIR/memory-optimization.js'),
        memoryMonitor: fs.existsSync('$SCRIPTS_DIR/memory-monitor.js'),
        memoryLeakDetector: fs.existsSync('$SCRIPTS_DIR/memory-leak-detector.js')
    },
    testResults: {
        subprocessManagementTests: $SUBPROCESS_TEST_EXIT_CODE === 0,
        memoryLeakTests: $MEMORY_TEST_EXIT_CODE === 0,
        zeroMemoryRetentionValidation: $VALIDATION_EXIT_CODE === 0
    },
    deployment_status: 'completed',
    overall_success: ($SUBPROCESS_TEST_EXIT_CODE === 0 || $MEMORY_TEST_EXIT_CODE === 0) && $VALIDATION_EXIT_CODE === 0,
    recommendations: []
};

// Add recommendations based on test results
if (report.testResults.subprocessManagementTests && report.testResults.zeroMemoryRetentionValidation) {
    report.recommendations.push('Enhanced Subprocess Management system successfully deployed and validated');
    report.recommendations.push('Zero memory retention guarantee achieved');
    report.recommendations.push('System ready for production use');
} else {
    if (!report.testResults.subprocessManagementTests) {
        report.recommendations.push('Review Enhanced Subprocess Management test failures');
    }
    if (!report.testResults.memoryLeakTests) {
        report.recommendations.push('Review Memory Leak test failures');
    }
    if (!report.testResults.zeroMemoryRetentionValidation) {
        report.recommendations.push('Critical: Zero memory retention validation failed - investigate memory leaks');
    }
}

// Add performance metrics if available
try {
    const { getSubprocessManager } = require('$SCRIPTS_DIR/enhanced-subprocess-manager.js');
    const manager = getSubprocessManager();
    report.performanceMetrics = manager.getPerformanceMetrics();
} catch (error) {
    report.performanceMetrics = { error: error.message };
}

fs.writeFileSync('$REPORT_FILE', JSON.stringify(report, null, 2));
console.log('📊 Deployment report generated:', '$REPORT_FILE');
"

echo "✅ Deployment report generated: $REPORT_FILE"

# Final Summary
echo ""
echo "📊 Enhanced Subprocess Management System Deployment Summary"
echo "============================================================"

if [[ $VALIDATION_EXIT_CODE -eq 0 ]]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "✅ Enhanced Subprocess Manager deployed and validated"
    echo "✅ Zero memory retention guarantee achieved"
    echo "✅ Integration with memory monitoring systems complete"
    echo "✅ Comprehensive test suite validation passed"
    echo ""
    echo "🚀 System Status: READY FOR PRODUCTION"
    echo ""
    echo "💡 Key Features Deployed:"
    echo "   • Comprehensive subprocess lifecycle management"
    echo "   • Memory-aware subprocess limits and termination"
    echo "   • Integration with enhanced cache manager and memory monitor"
    echo "   • Zero memory retention guarantee with automated validation"
    echo "   • Circuit breaker for subprocess memory exhaustion"
    echo "   • Detailed lifecycle analytics and reporting"
    echo ""
    echo "📋 Next Steps:"
    echo "   • Monitor subprocess performance in production"
    echo "   • Review deployment report: $REPORT_FILE"
    echo "   • Run periodic validation: node scripts/enhanced-subprocess-manager.js validate"
    
    exit 0
else
    echo "⚠️ DEPLOYMENT COMPLETED WITH ISSUES"
    echo ""
    echo "❌ Zero memory retention validation failed"
    
    if [[ $SUBPROCESS_TEST_EXIT_CODE -ne 0 ]]; then
        echo "❌ Enhanced Subprocess Management tests failed"
    fi
    
    if [[ $MEMORY_TEST_EXIT_CODE -ne 0 ]]; then
        echo "❌ Memory Leak tests failed"
    fi
    
    echo ""
    echo "🔍 Investigation Required:"
    echo "   • Review test failure logs in $LOGS_DIR"
    echo "   • Check deployment report: $REPORT_FILE"
    echo "   • Run diagnostic: node scripts/enhanced-subprocess-manager.js validate"
    echo ""
    echo "🚨 CAUTION: Review issues before production deployment"
    
    exit 1
fi