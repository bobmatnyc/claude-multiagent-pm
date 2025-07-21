#!/usr/bin/env node

/**
 * Claude PM Framework - Deployment Detection System Tests
 * 
 * Tests the comprehensive deployment detection system including:
 * - Local source development detection
 * - NPM global installation detection
 * - NPX execution detection
 * - NPM local installation detection
 * - Deployed instance detection
 * - Environment-based detection
 * - Fallback detection
 * - Configuration object validation
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Import the deployment detector
const { DeploymentDetector, getFrameworkPath, getDeploymentConfig } = require('../bin/claude-pm');

class DeploymentDetectionTestSuite {
    constructor() {
        this.testResults = [];
        this.detector = new DeploymentDetector();
    }

    /**
     * Log test result
     */
    logResult(testName, passed, message = '') {
        const result = {
            test: testName,
            passed: passed,
            message: message,
            timestamp: new Date().toISOString()
        };
        this.testResults.push(result);
        
        const status = passed ? '✓' : '✗';
        const color = passed ? '\x1b[32m' : '\x1b[31m';
        console.log(`${color}${status} ${testName}\x1b[0m${message ? ` - ${message}` : ''}`);
    }

    /**
     * Test deployment detector instantiation
     */
    testDeploymentDetectorInstantiation() {
        try {
            const detector = new DeploymentDetector();
            assert(detector instanceof DeploymentDetector, 'Detector should be instance of DeploymentDetector');
            assert(typeof detector.platform === 'string', 'Platform should be string');
            assert(detector.detectionCache instanceof Map, 'Detection cache should be Map');
            
            this.logResult('Deployment Detector Instantiation', true);
        } catch (error) {
            this.logResult('Deployment Detector Instantiation', false, error.message);
        }
    }

    /**
     * Test local source detection
     */
    testLocalSourceDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectLocalSource();
            
            // This should succeed in the actual source repository
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.confidence === 'string', 'Confidence should be string');
                assert(result.packageJson && typeof result.packageJson === 'object', 'Package JSON should be object');
            }
            
            this.logResult('Local Source Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('Local Source Detection', false, error.message);
        }
    }

    /**
     * Test NPM global detection
     */
    testNpmGlobalDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectNpmGlobal();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.globalPath === 'string', 'Global path should be string');
            }
            
            this.logResult('NPM Global Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('NPM Global Detection', false, error.message);
        }
    }

    /**
     * Test NPX execution detection
     */
    testNpxExecutionDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectNpxExecution();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.npxCachePath === 'string', 'NPX cache path should be string');
            }
            
            this.logResult('NPX Execution Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('NPX Execution Detection', false, error.message);
        }
    }

    /**
     * Test NPM local detection
     */
    testNpmLocalDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectNpmLocal();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.projectRoot === 'string', 'Project root should be string');
            }
            
            this.logResult('NPM Local Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('NPM Local Detection', false, error.message);
        }
    }

    /**
     * Test deployed instance detection
     */
    testDeployedInstanceDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectDeployedInstance();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.deployedConfig === 'object', 'Deployed config should be object');
            }
            
            this.logResult('Deployed Instance Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('Deployed Instance Detection', false, error.message);
        }
    }

    /**
     * Test environment-based detection
     */
    testEnvironmentBasedDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectEnvironmentBased();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.environmentSource === 'string', 'Environment source should be string');
            }
            
            this.logResult('Environment-based Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('Environment-based Detection', false, error.message);
        }
    }

    /**
     * Test fallback detection
     */
    testFallbackDetection() {
        try {
            const detector = new DeploymentDetector();
            const result = detector._detectFallback();
            
            assert(typeof result === 'object', 'Result should be object');
            assert(typeof result.found === 'boolean', 'Found should be boolean');
            
            if (result.found) {
                assert(typeof result.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof result.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof result.fallbackPath === 'string', 'Fallback path should be string');
            }
            
            this.logResult('Fallback Detection', true, `Found: ${result.found}`);
        } catch (error) {
            this.logResult('Fallback Detection', false, error.message);
        }
    }

    /**
     * Test configuration object structure
     */
    testConfigurationObjectStructure() {
        try {
            const detector = new DeploymentDetector();
            const config = detector.detectDeployment();
            
            // Validate required fields
            assert(typeof config === 'object', 'Config should be object');
            assert(typeof config.deploymentType === 'string', 'Deployment type should be string');
            assert(typeof config.found === 'boolean', 'Found should be boolean');
            assert(typeof config.platform === 'string', 'Platform should be string');
            assert(typeof config.detectedAt === 'string', 'Detected at should be string');
            assert(typeof config.confidence === 'string', 'Confidence should be string');
            
            if (config.found) {
                assert(typeof config.frameworkPath === 'string', 'Framework path should be string');
                assert(typeof config.claudePmPath === 'string', 'Claude PM path should be string');
                assert(typeof config.paths === 'object', 'Paths should be object');
                
                // Validate paths object
                assert(typeof config.paths.framework === 'string', 'Framework path should be string');
                assert(typeof config.paths.claudePm === 'string', 'Claude PM path should be string');
                assert(typeof config.paths.bin === 'string', 'Bin path should be string');
                assert(typeof config.paths.config === 'string', 'Config path should be string');
                assert(typeof config.paths.templates === 'string', 'Templates path should be string');
                assert(typeof config.paths.schemas === 'string', 'Schemas path should be string');
                
                // Validate metadata if present
                if (config.metadata) {
                    assert(typeof config.metadata === 'object', 'Metadata should be object');
                }
            } else {
                assert(typeof config.error === 'string', 'Error should be string when not found');
            }
            
            this.logResult('Configuration Object Structure', true);
        } catch (error) {
            this.logResult('Configuration Object Structure', false, error.message);
        }
    }

    /**
     * Test deployment strategy generation
     */
    testDeploymentStrategyGeneration() {
        try {
            const detector = new DeploymentDetector();
            const strategy = detector.getDeploymentStrategy();
            
            assert(typeof strategy === 'object', 'Strategy should be object');
            assert(typeof strategy.strategy === 'string', 'Strategy type should be string');
            assert(typeof strategy.config === 'object', 'Config should be object');
            
            if (strategy.strategy !== 'install_required') {
                assert(typeof strategy.pythonPath === 'string', 'Python path should be string');
                assert(typeof strategy.environmentSetup === 'object', 'Environment setup should be object');
                
                // Validate environment setup
                assert(typeof strategy.environmentSetup.PYTHONPATH === 'string', 'PYTHONPATH should be string');
                assert(typeof strategy.environmentSetup.CLAUDE_PM_FRAMEWORK_PATH === 'string', 'Framework path should be string');
            } else {
                assert(typeof strategy.recommendation === 'string', 'Recommendation should be string');
            }
            
            this.logResult('Deployment Strategy Generation', true, `Strategy: ${strategy.strategy}`);
        } catch (error) {
            this.logResult('Deployment Strategy Generation', false, error.message);
        }
    }

    /**
     * Test caching mechanism
     */
    testCachingMechanism() {
        try {
            const detector = new DeploymentDetector();
            
            // First detection
            const config1 = detector.detectDeployment();
            const cacheSize1 = detector.detectionCache.size;
            
            // Second detection (should use cache)
            const config2 = detector.detectDeployment();
            const cacheSize2 = detector.detectionCache.size;
            
            assert(cacheSize1 === 1, 'Cache should have one entry after first detection');
            assert(cacheSize2 === 1, 'Cache should still have one entry after second detection');
            assert(JSON.stringify(config1) === JSON.stringify(config2), 'Cached result should be identical');
            
            this.logResult('Caching Mechanism', true);
        } catch (error) {
            this.logResult('Caching Mechanism', false, error.message);
        }
    }

    /**
     * Test error handling
     */
    testErrorHandling() {
        try {
            const detector = new DeploymentDetector();
            
            // Test with invalid detection methods
            const invalidResult = detector._buildConfig('invalid_type', { found: false, error: 'Test error' });
            
            assert(typeof invalidResult === 'object', 'Invalid result should be object');
            assert(invalidResult.deploymentType === 'invalid_type', 'Deployment type should be preserved');
            assert(invalidResult.found === false, 'Found should be false');
            assert(typeof invalidResult.error === 'string', 'Error should be string');
            
            this.logResult('Error Handling', true);
        } catch (error) {
            this.logResult('Error Handling', false, error.message);
        }
    }

    /**
     * Test framework path integration
     */
    testFrameworkPathIntegration() {
        try {
            // Test getFrameworkPath function
            const frameworkPath = getFrameworkPath();
            assert(typeof frameworkPath === 'string', 'Framework path should be string');
            assert(frameworkPath.length > 0, 'Framework path should not be empty');
            
            // Test getDeploymentConfig function
            const deploymentConfig = getDeploymentConfig();
            assert(typeof deploymentConfig === 'object', 'Deployment config should be object');
            assert(typeof deploymentConfig.strategy === 'string', 'Strategy should be string');
            assert(typeof deploymentConfig.config === 'object', 'Config should be object');
            
            this.logResult('Framework Path Integration', true);
        } catch (error) {
            this.logResult('Framework Path Integration', false, error.message);
        }
    }

    /**
     * Test cross-platform compatibility
     */
    testCrossPlatformCompatibility() {
        try {
            const detector = new DeploymentDetector();
            const config = detector.detectDeployment();
            
            // Test platform detection
            assert(['win32', 'darwin', 'linux'].includes(config.platform), 'Platform should be supported');
            
            // Test path handling
            if (config.found) {
                const pathSeparator = config.platform === 'win32' ? '\\' : '/';
                assert(config.frameworkPath.includes(pathSeparator) || config.frameworkPath.length === 1, 'Path should use correct separator');
            }
            
            this.logResult('Cross-platform Compatibility', true, `Platform: ${config.platform}`);
        } catch (error) {
            this.logResult('Cross-platform Compatibility', false, error.message);
        }
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🧪 Running Claude PM Framework Deployment Detection Tests');
        console.log('=' .repeat(60));
        
        // Run all test methods
        this.testDeploymentDetectorInstantiation();
        this.testLocalSourceDetection();
        this.testNpmGlobalDetection();
        this.testNpxExecutionDetection();
        this.testNpmLocalDetection();
        this.testDeployedInstanceDetection();
        this.testEnvironmentBasedDetection();
        this.testFallbackDetection();
        this.testConfigurationObjectStructure();
        this.testDeploymentStrategyGeneration();
        this.testCachingMechanism();
        this.testErrorHandling();
        this.testFrameworkPathIntegration();
        this.testCrossPlatformCompatibility();
        
        // Generate test report
        this.generateTestReport();
    }

    /**
     * Generate comprehensive test report
     */
    generateTestReport() {
        const passedTests = this.testResults.filter(r => r.passed).length;
        const failedTests = this.testResults.filter(r => r.failed).length;
        const totalTests = this.testResults.length;
        
        console.log('\n' + '=' .repeat(60));
        console.log('🧪 Test Results Summary');
        console.log('=' .repeat(60));
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: \x1b[32m${passedTests}\x1b[0m`);
        console.log(`Failed: \x1b[31m${failedTests}\x1b[0m`);
        console.log(`Success Rate: ${Math.round((passedTests / totalTests) * 100)}%`);
        
        if (failedTests > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults.filter(r => !r.passed).forEach(test => {
                console.log(`   - ${test.test}: ${test.message}`);
            });
        }
        
        // Generate detailed report
        const reportPath = path.join(__dirname, 'deployment_detection_test_report.json');
        const report = {
            testSuite: 'Deployment Detection System',
            timestamp: new Date().toISOString(),
            platform: os.platform(),
            totalTests: totalTests,
            passedTests: passedTests,
            failedTests: failedTests,
            successRate: Math.round((passedTests / totalTests) * 100),
            results: this.testResults
        };
        
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`\n📄 Detailed report saved to: ${reportPath}`);
        
        // Exit with appropriate code
        process.exit(failedTests > 0 ? 1 : 0);
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const testSuite = new DeploymentDetectionTestSuite();
    testSuite.runAllTests();
}

module.exports = DeploymentDetectionTestSuite;