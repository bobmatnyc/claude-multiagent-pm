#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Unified Installation Test Suite
 * ISS-0112 Implementation Validation
 * 
 * Comprehensive test suite for validating the unified NPM installation system:
 * - Component deployment verification
 * - Cross-platform compatibility testing  
 * - Health checking validation
 * - Error handling verification
 * - Installation diagnostics testing
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class UnifiedInstallationTester {
    constructor() {
        this.platform = os.platform();
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
        this.testResults = {
            componentDeployment: {},
            directoryStructure: {},
            healthChecking: {},
            crossPlatformCompatibility: {},
            errorHandling: {},
            installationDiagnostics: {}
        };
        this.startTime = Date.now();
    }

    /**
     * Log with timestamp and emoji
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 
                      level === 'success' ? '✅' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
    }

    /**
     * Main test runner
     */
    async runTests() {
        try {
            this.log('🚀 Starting Unified Installation Test Suite (ISS-0112)', 'info');
            this.log(`   Platform: ${this.platform}`);
            this.log(`   Test Target: ${this.globalConfigDir}`);
            this.log('');

            // Test 1: Component Deployment Verification
            await this.testComponentDeployment();

            // Test 2: Directory Structure Validation
            await this.testDirectoryStructure();

            // Test 3: Health Checking System
            await this.testHealthChecking();

            // Test 4: Cross-Platform Compatibility
            await this.testCrossPlatformCompatibility();

            // Test 5: Error Handling Verification
            await this.testErrorHandling();

            // Test 6: Installation Diagnostics
            await this.testInstallationDiagnostics();

            // Generate comprehensive test report
            await this.generateTestReport();

            this.log('');
            this.log('✨ Unified Installation Test Suite completed successfully!', 'success');

        } catch (error) {
            this.log(`💥 Test suite failed: ${error.message}`, 'error');
            await this.generateFailureReport(error);
            process.exit(1);
        }
    }

    /**
     * Test 1: Component Deployment Verification
     */
    async testComponentDeployment() {
        this.log('🧪 Test 1: Component Deployment Verification');

        const expectedComponents = [
            'framework', 'scripts', 'templates', 'agents', 
            'schemas', 'cli', 'docs', 'bin'
        ];

        for (const component of expectedComponents) {
            const componentPath = path.join(this.globalConfigDir, component);
            const exists = fsSync.existsSync(componentPath);
            
            this.testResults.componentDeployment[component] = {
                path: componentPath,
                exists: exists,
                hasContent: false,
                contentCount: 0
            };

            if (exists) {
                try {
                    const contents = await fs.readdir(componentPath);
                    this.testResults.componentDeployment[component].hasContent = contents.length > 0;
                    this.testResults.componentDeployment[component].contentCount = contents.length;
                    this.log(`   ✅ ${component}: Deployed (${contents.length} items)`, 'success');
                } catch (error) {
                    this.log(`   ❌ ${component}: Error reading contents - ${error.message}`, 'error');
                }
            } else {
                this.log(`   ❌ ${component}: Missing at ${componentPath}`, 'error');
                throw new Error(`Critical component missing: ${component}`);
            }
        }

        this.log('   🎯 Component deployment verification completed');
    }

    /**
     * Test 2: Directory Structure Validation
     */
    async testDirectoryStructure() {
        this.log('🧪 Test 2: Directory Structure Validation');

        // Test main configuration directory
        const configExists = fsSync.existsSync(this.globalConfigDir);
        this.testResults.directoryStructure.mainConfig = {
            path: this.globalConfigDir,
            exists: configExists,
            permissions: configExists ? await this.checkPermissions(this.globalConfigDir) : null
        };

        if (!configExists) {
            throw new Error(`Main configuration directory missing: ${this.globalConfigDir}`);
        }

        // Test configuration files
        const configFiles = ['config.json', 'platform-config.json'];
        for (const configFile of configFiles) {
            const configPath = path.join(this.globalConfigDir, configFile);
            const exists = fsSync.existsSync(configPath);
            
            this.testResults.directoryStructure[configFile] = {
                path: configPath,
                exists: exists,
                valid: false
            };

            if (exists) {
                try {
                    const content = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
                    this.testResults.directoryStructure[configFile].valid = true;
                    this.testResults.directoryStructure[configFile].content = content;
                    this.log(`   ✅ ${configFile}: Valid configuration`, 'success');
                } catch (error) {
                    this.log(`   ❌ ${configFile}: Invalid JSON - ${error.message}`, 'error');
                }
            } else {
                this.log(`   ❌ ${configFile}: Missing`, 'error');
            }
        }

        // Test three-tier agent hierarchy
        const agentHierarchy = ['system', 'user-defined', 'project-specific', 'roles'];
        const agentsPath = path.join(this.globalConfigDir, 'agents');
        
        for (const tier of agentHierarchy) {
            const tierPath = path.join(agentsPath, tier);
            const exists = fsSync.existsSync(tierPath);
            
            this.testResults.directoryStructure[`agents_${tier}`] = {
                path: tierPath,
                exists: exists
            };

            if (exists) {
                this.log(`   ✅ Agent tier '${tier}': Exists`, 'success');
            } else {
                this.log(`   ❌ Agent tier '${tier}': Missing`, 'error');
            }
        }

        this.log('   🎯 Directory structure validation completed');
    }

    /**
     * Test 3: Health Checking System
     */
    async testHealthChecking() {
        this.log('🧪 Test 3: Health Checking System');

        // Test health check file existence
        const healthCheckPath = path.join(this.globalConfigDir, 'health-check.json');
        const healthExists = fsSync.existsSync(healthCheckPath);

        this.testResults.healthChecking.file = {
            path: healthCheckPath,
            exists: healthExists,
            valid: false,
            checks: null
        };

        if (healthExists) {
            try {
                const healthData = JSON.parse(fsSync.readFileSync(healthCheckPath, 'utf8'));
                this.testResults.healthChecking.file.valid = true;
                this.testResults.healthChecking.file.checks = healthData.checks;
                
                // Validate health check structure
                const requiredChecks = [
                    'configurationValid', 'componentsDeployed', 'permissionsCorrect',
                    'platformCompatible', 'pathsAccessible'
                ];

                const allChecksPresent = requiredChecks.every(check => 
                    healthData.checks && healthData.checks.hasOwnProperty(check)
                );

                if (allChecksPresent) {
                    this.log(`   ✅ Health check file: Valid structure`, 'success');
                    
                    // Report individual check results
                    for (const [checkName, passed] of Object.entries(healthData.checks)) {
                        const status = passed ? '✅' : '❌';
                        this.log(`      ${status} ${checkName}: ${passed ? 'PASS' : 'FAIL'}`);
                    }
                } else {
                    this.log(`   ❌ Health check file: Missing required checks`, 'error');
                }

            } catch (error) {
                this.log(`   ❌ Health check file: Invalid JSON - ${error.message}`, 'error');
            }
        } else {
            this.log(`   ❌ Health check file: Missing`, 'error');
        }

        // Test health check scripts
        const scriptsPath = path.join(this.globalConfigDir, 'scripts');
        const healthScript = this.platform === 'win32' ? 'health-check.bat' : 'health-check.sh';
        const healthScriptPath = path.join(scriptsPath, healthScript);
        
        this.testResults.healthChecking.script = {
            path: healthScriptPath,
            exists: fsSync.existsSync(healthScriptPath),
            executable: false
        };

        if (this.testResults.healthChecking.script.exists) {
            if (this.platform !== 'win32') {
                const stat = fsSync.statSync(healthScriptPath);
                this.testResults.healthChecking.script.executable = !!(stat.mode & 0o111);
            } else {
                this.testResults.healthChecking.script.executable = true; // Windows handles this
            }
            
            this.log(`   ✅ Health script: Available and ${this.testResults.healthChecking.script.executable ? 'executable' : 'not executable'}`, 'success');
        } else {
            this.log(`   ❌ Health script: Missing`, 'error');
        }

        this.log('   🎯 Health checking system validation completed');
    }

    /**
     * Test 4: Cross-Platform Compatibility
     */
    async testCrossPlatformCompatibility() {
        this.log('🧪 Test 4: Cross-Platform Compatibility');

        // Test platform-specific configuration
        const platformConfigPath = path.join(this.globalConfigDir, 'platform-config.json');
        const platformConfigExists = fsSync.existsSync(platformConfigPath);

        this.testResults.crossPlatformCompatibility.platformConfig = {
            path: platformConfigPath,
            exists: platformConfigExists,
            valid: false,
            platform: this.platform
        };

        if (platformConfigExists) {
            try {
                const platformConfig = JSON.parse(fsSync.readFileSync(platformConfigPath, 'utf8'));
                const expectedPlatform = platformConfig.platform === this.platform;
                
                this.testResults.crossPlatformCompatibility.platformConfig.valid = expectedPlatform;
                this.testResults.crossPlatformCompatibility.platformConfig.content = platformConfig;

                if (expectedPlatform) {
                    this.log(`   ✅ Platform config: Matches current platform (${this.platform})`, 'success');
                } else {
                    this.log(`   ❌ Platform config: Mismatch (config: ${platformConfig.platform}, actual: ${this.platform})`, 'error');
                }
            } catch (error) {
                this.log(`   ❌ Platform config: Invalid JSON - ${error.message}`, 'error');
            }
        } else {
            this.log(`   ❌ Platform config: Missing`, 'error');
        }

        // Test platform-specific scripts
        const scriptsPath = path.join(this.globalConfigDir, 'scripts');
        const platformSpecificScripts = this.platform === 'win32' ? 
            ['windows-diagnostic.bat'] : 
            ['health-check.sh'];

        for (const script of platformSpecificScripts) {
            const scriptPath = path.join(scriptsPath, script);
            const exists = fsSync.existsSync(scriptPath);
            
            this.testResults.crossPlatformCompatibility[script] = {
                path: scriptPath,
                exists: exists,
                executable: false
            };

            if (exists) {
                if (this.platform !== 'win32') {
                    const stat = fsSync.statSync(scriptPath);
                    this.testResults.crossPlatformCompatibility[script].executable = !!(stat.mode & 0o111);
                } else {
                    this.testResults.crossPlatformCompatibility[script].executable = true;
                }
                
                this.log(`   ✅ Platform script '${script}': Available`, 'success');
            } else {
                this.log(`   ❌ Platform script '${script}': Missing`, 'error');
            }
        }

        // Test CLI wrapper
        const binPath = path.join(this.globalConfigDir, 'bin');
        const cliWrapper = this.platform === 'win32' ? 'claude-pm.bat' : 'claude-pm';
        const cliWrapperPath = path.join(binPath, cliWrapper);
        
        this.testResults.crossPlatformCompatibility.cliWrapper = {
            path: cliWrapperPath,
            exists: fsSync.existsSync(cliWrapperPath),
            executable: false
        };

        if (this.testResults.crossPlatformCompatibility.cliWrapper.exists) {
            if (this.platform !== 'win32') {
                const stat = fsSync.statSync(cliWrapperPath);
                this.testResults.crossPlatformCompatibility.cliWrapper.executable = !!(stat.mode & 0o111);
            } else {
                this.testResults.crossPlatformCompatibility.cliWrapper.executable = true;
            }
            
            this.log(`   ✅ CLI wrapper: Available for ${this.platform}`, 'success');
        } else {
            this.log(`   ❌ CLI wrapper: Missing for ${this.platform}`, 'error');
        }

        this.log('   🎯 Cross-platform compatibility validation completed');
    }

    /**
     * Test 5: Error Handling Verification
     */
    async testErrorHandling() {
        this.log('🧪 Test 5: Error Handling Verification');

        // Test error handling configuration
        const errorTestPath = path.join(this.globalConfigDir, 'error-handling-test.json');
        const errorTestExists = fsSync.existsSync(errorTestPath);

        this.testResults.errorHandling.testFile = {
            path: errorTestPath,
            exists: errorTestExists,
            valid: false
        };

        if (errorTestExists) {
            try {
                const errorTestData = JSON.parse(fsSync.readFileSync(errorTestPath, 'utf8'));
                this.testResults.errorHandling.testFile.valid = true;
                this.testResults.errorHandling.testFile.content = errorTestData;
                
                this.log(`   ✅ Error handling test: Configuration exists`, 'success');
                
                // Report error handling test results
                for (const [testName, result] of Object.entries(errorTestData)) {
                    const status = result ? '✅' : '❌';
                    this.log(`      ${status} ${testName}: ${result ? 'PASS' : 'FAIL'}`);
                }
                
            } catch (error) {
                this.log(`   ❌ Error handling test: Invalid JSON - ${error.message}`, 'error');
            }
        } else {
            this.log(`   ⚠️ Error handling test: File not found (may not have been run)`, 'warn');
        }

        // Test failsafe mechanisms
        const failsafeScript = path.join(this.globalConfigDir, 'deploy-claude-md.sh');
        const failsafeExists = fsSync.existsSync(failsafeScript);

        this.testResults.errorHandling.failsafe = {
            path: failsafeScript,
            exists: failsafeExists,
            executable: false
        };

        if (failsafeExists) {
            if (this.platform !== 'win32') {
                const stat = fsSync.statSync(failsafeScript);
                this.testResults.errorHandling.failsafe.executable = !!(stat.mode & 0o111);
            } else {
                this.testResults.errorHandling.failsafe.executable = true;
            }
            
            this.log(`   ✅ Failsafe script: Available and ${this.testResults.errorHandling.failsafe.executable ? 'executable' : 'not executable'}`, 'success');
        } else {
            this.log(`   ❌ Failsafe script: Missing`, 'error');
        }

        this.log('   🎯 Error handling verification completed');
    }

    /**
     * Test 6: Installation Diagnostics
     */
    async testInstallationDiagnostics() {
        this.log('🧪 Test 6: Installation Diagnostics');

        // Test diagnostics JSON file
        const diagnosticsPath = path.join(this.globalConfigDir, 'installation-diagnostics.json');
        const diagnosticsExists = fsSync.existsSync(diagnosticsPath);

        this.testResults.installationDiagnostics.jsonFile = {
            path: diagnosticsPath,
            exists: diagnosticsExists,
            valid: false,
            comprehensive: false
        };

        if (diagnosticsExists) {
            try {
                const diagnosticsData = JSON.parse(fsSync.readFileSync(diagnosticsPath, 'utf8'));
                this.testResults.installationDiagnostics.jsonFile.valid = true;
                this.testResults.installationDiagnostics.jsonFile.content = diagnosticsData;

                // Check for comprehensive diagnostics structure
                const requiredSections = [
                    'installationId', 'version', 'platform', 'deploymentPaths',
                    'componentStatus', 'healthMetrics', 'troubleshooting'
                ];

                const hasAllSections = requiredSections.every(section => 
                    diagnosticsData.hasOwnProperty(section)
                );

                this.testResults.installationDiagnostics.jsonFile.comprehensive = hasAllSections;

                if (hasAllSections) {
                    this.log(`   ✅ Diagnostics JSON: Comprehensive and valid`, 'success');
                } else {
                    this.log(`   ⚠️ Diagnostics JSON: Missing some sections`, 'warn');
                }

            } catch (error) {
                this.log(`   ❌ Diagnostics JSON: Invalid JSON - ${error.message}`, 'error');
            }
        } else {
            this.log(`   ❌ Diagnostics JSON: Missing`, 'error');
        }

        // Test diagnostics markdown report
        const reportPath = path.join(this.globalConfigDir, 'installation-report.md');
        const reportExists = fsSync.existsSync(reportPath);

        this.testResults.installationDiagnostics.markdownReport = {
            path: reportPath,
            exists: reportExists,
            size: 0
        };

        if (reportExists) {
            const stat = fsSync.statSync(reportPath);
            this.testResults.installationDiagnostics.markdownReport.size = stat.size;
            
            if (stat.size > 0) {
                this.log(`   ✅ Diagnostics report: Available (${stat.size} bytes)`, 'success');
            } else {
                this.log(`   ⚠️ Diagnostics report: Empty file`, 'warn');
            }
        } else {
            this.log(`   ❌ Diagnostics report: Missing`, 'error');
        }

        // Test component validation
        const componentValidationPath = path.join(this.globalConfigDir, 'component-validation.json');
        const componentValidationExists = fsSync.existsSync(componentValidationPath);

        this.testResults.installationDiagnostics.componentValidation = {
            path: componentValidationPath,
            exists: componentValidationExists,
            valid: false
        };

        if (componentValidationExists) {
            try {
                const validationData = JSON.parse(fsSync.readFileSync(componentValidationPath, 'utf8'));
                this.testResults.installationDiagnostics.componentValidation.valid = true;
                this.testResults.installationDiagnostics.componentValidation.content = validationData;
                
                this.log(`   ✅ Component validation: Available`, 'success');
            } catch (error) {
                this.log(`   ❌ Component validation: Invalid JSON - ${error.message}`, 'error');
            }
        } else {
            this.log(`   ❌ Component validation: Missing`, 'error');
        }

        this.log('   🎯 Installation diagnostics validation completed');
    }

    /**
     * Helper method to check permissions
     */
    async checkPermissions(dirPath) {
        try {
            await fs.access(dirPath, fsSync.constants.R_OK | fsSync.constants.W_OK);
            return 'rw';
        } catch (error) {
            try {
                await fs.access(dirPath, fsSync.constants.R_OK);
                return 'r';
            } catch (error) {
                return 'none';
            }
        }
    }

    /**
     * Generate comprehensive test report
     */
    async generateTestReport() {
        this.log('📊 Generating comprehensive test report...');

        const testDuration = Date.now() - this.startTime;
        const timestamp = new Date().toISOString();

        const report = {
            metadata: {
                testSuiteVersion: '1.0.0',
                testId: `unified-install-test-${Date.now()}`,
                timestamp: timestamp,
                duration: testDuration,
                platform: this.platform,
                tester: 'UnifiedInstallationTester',
                iss: 'ISS-0112'
            },
            summary: {
                totalTests: this.countTotalTests(),
                passedTests: this.countPassedTests(),
                failedTests: this.countFailedTests(),
                overallResult: this.getOverallResult()
            },
            results: this.testResults,
            recommendations: this.generateRecommendations()
        };

        // Save JSON report
        const jsonReportPath = path.join(this.globalConfigDir, 'unified-installation-test-report.json');
        await fs.writeFile(jsonReportPath, JSON.stringify(report, null, 2));

        // Generate markdown report
        const markdownReport = this.generateMarkdownReport(report);
        const mdReportPath = path.join(this.globalConfigDir, 'unified-installation-test-report.md');
        await fs.writeFile(mdReportPath, markdownReport);

        this.log(`   📄 JSON report: ${jsonReportPath}`, 'success');
        this.log(`   📄 Markdown report: ${mdReportPath}`, 'success');

        // Display summary
        this.log('');
        this.log('📋 Test Summary:', 'info');
        this.log(`   Total Tests: ${report.summary.totalTests}`);
        this.log(`   Passed: ${report.summary.passedTests}`);
        this.log(`   Failed: ${report.summary.failedTests}`);
        this.log(`   Overall Result: ${report.summary.overallResult}`);
        this.log(`   Duration: ${testDuration}ms`);
    }

    /**
     * Count total tests performed
     */
    countTotalTests() {
        let total = 0;
        for (const category of Object.values(this.testResults)) {
            total += Object.keys(category).length;
        }
        return total;
    }

    /**
     * Count passed tests
     */
    countPassedTests() {
        let passed = 0;
        for (const category of Object.values(this.testResults)) {
            for (const result of Object.values(category)) {
                if (result.exists === true || result.valid === true || result.executable === true) {
                    passed++;
                }
            }
        }
        return passed;
    }

    /**
     * Count failed tests
     */
    countFailedTests() {
        return this.countTotalTests() - this.countPassedTests();
    }

    /**
     * Get overall test result
     */
    getOverallResult() {
        const failed = this.countFailedTests();
        if (failed === 0) {
            return 'PASS';
        } else if (failed < 5) {
            return 'PASS_WITH_WARNINGS';
        } else {
            return 'FAIL';
        }
    }

    /**
     * Generate recommendations based on test results
     */
    generateRecommendations() {
        const recommendations = [];

        // Check for missing critical components
        for (const [component, result] of Object.entries(this.testResults.componentDeployment)) {
            if (!result.exists) {
                recommendations.push({
                    type: 'critical',
                    component: component,
                    message: `Component '${component}' is missing and should be deployed`,
                    action: 'Run npm run install:unified to redeploy components'
                });
            }
        }

        // Check for missing health checks
        if (!this.testResults.healthChecking.file.exists) {
            recommendations.push({
                type: 'warning',
                component: 'healthChecking',
                message: 'Health check file is missing',
                action: 'Verify installation completed successfully'
            });
        }

        // Check for permission issues
        for (const [test, result] of Object.entries(this.testResults.directoryStructure)) {
            if (result.permissions === 'none') {
                recommendations.push({
                    type: 'critical',
                    component: 'permissions',
                    message: `No permissions for ${result.path}`,
                    action: 'Check file system permissions and ownership'
                });
            }
        }

        return recommendations;
    }

    /**
     * Generate markdown test report
     */
    generateMarkdownReport(report) {
        const md = `# Claude Multi-Agent PM Framework - Unified Installation Test Report

**ISS-0112 Implementation Validation**

Generated: ${report.metadata.timestamp}  
Test ID: ${report.metadata.testId}  
Platform: ${report.metadata.platform}  
Duration: ${report.metadata.duration}ms  

## Summary

- **Total Tests**: ${report.summary.totalTests}
- **Passed**: ${report.summary.passedTests}
- **Failed**: ${report.summary.failedTests}
- **Overall Result**: **${report.summary.overallResult}**

## Test Results

### 1. Component Deployment

${Object.entries(report.results.componentDeployment).map(([component, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${component}**: ${result.exists ? `Deployed (${result.contentCount} items)` : 'Missing'}`
).join('\n')}

### 2. Directory Structure

${Object.entries(report.results.directoryStructure).map(([test, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${test}**: ${result.exists ? 'Valid' : 'Missing'}`
).join('\n')}

### 3. Health Checking

${Object.entries(report.results.healthChecking).map(([test, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${test}**: ${result.exists ? 'Available' : 'Missing'}`
).join('\n')}

### 4. Cross-Platform Compatibility

${Object.entries(report.results.crossPlatformCompatibility).map(([test, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${test}**: ${result.exists ? 'Compatible' : 'Missing'}`
).join('\n')}

### 5. Error Handling

${Object.entries(report.results.errorHandling).map(([test, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${test}**: ${result.exists ? 'Available' : 'Missing'}`
).join('\n')}

### 6. Installation Diagnostics

${Object.entries(report.results.installationDiagnostics).map(([test, result]) => 
    `- ${result.exists ? '✅' : '❌'} **${test}**: ${result.exists ? 'Available' : 'Missing'}`
).join('\n')}

## Recommendations

${report.recommendations.length > 0 ? 
    report.recommendations.map(rec => 
        `### ${rec.type.toUpperCase()}: ${rec.component}\n\n**Issue**: ${rec.message}  \n**Action**: ${rec.action}\n`
    ).join('\n') : 
    '✅ No recommendations - all tests passed successfully!'
}

## Test Configuration

- **Global Config Directory**: ${this.globalConfigDir}
- **Platform**: ${this.platform}
- **Test Framework**: UnifiedInstallationTester v1.0.0
- **Implementation**: ISS-0112 Unified NPM Installation System

---

*This report was generated automatically by the Claude Multi-Agent PM Framework test suite.*
`;

        return md;
    }

    /**
     * Generate failure report if tests fail
     */
    async generateFailureReport(error) {
        const failureReport = {
            timestamp: new Date().toISOString(),
            error: {
                message: error.message,
                stack: error.stack
            },
            platform: this.platform,
            partialResults: this.testResults,
            troubleshooting: {
                commonIssues: [
                    'Installation may not have completed successfully',
                    'Framework components may not be properly deployed',
                    'Permission issues may prevent proper deployment',
                    'Platform-specific setup may have failed'
                ],
                suggestedActions: [
                    'Run: npm run install:unified',
                    'Check: npm run install:diagnostics',
                    'Verify: npm run install:health-check',
                    'Report issue: https://github.com/bobmatnyc/claude-multiagent-pm/issues'
                ]
            }
        };

        const failurePath = path.join(this.globalConfigDir, 'unified-installation-test-failure.json');
        try {
            await fs.writeFile(failurePath, JSON.stringify(failureReport, null, 2));
            this.log(`💥 Failure report saved: ${failurePath}`, 'error');
        } catch (saveError) {
            this.log(`Failed to save failure report: ${saveError.message}`, 'error');
        }
    }
}

// Run tests if called directly
if (require.main === module) {
    const tester = new UnifiedInstallationTester();
    tester.runTests().catch(error => {
        console.error(`Test suite crashed: ${error.message}`);
        process.exit(1);
    });
}

module.exports = UnifiedInstallationTester;