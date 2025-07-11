#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Complete Installation Test
 * 
 * Tests the complete installation flow including:
 * 1. NPM package installation
 * 2. Dependencies and CLI availability
 * 3. Version display consistency
 * 4. Framework CLAUDE.md deployment
 * 5. Memory system detection
 * 6. Complete end-to-end validation
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawn } = require('child_process');

class InstallationTester {
    constructor() {
        this.packageJson = require('../package.json');
        this.version = this.packageJson.version;
        this.testDir = path.join(os.tmpdir(), `claude-pm-test-${Date.now()}`);
        this.results = {
            passed: 0,
            failed: 0,
            tests: []
        };
    }

    log(message, level = 'info') {
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : level === 'test' ? '🧪' : 'ℹ️';
        console.log(`${prefix} ${message}`);
    }

    test(name, testFn) {
        this.log(`Testing: ${name}`, 'test');
        try {
            const result = testFn();
            if (result === true || result === undefined) {
                this.log(`✓ ${name}`, 'success');
                this.results.passed++;
                this.results.tests.push({ name, status: 'passed' });
                return true;
            } else {
                this.log(`✗ ${name}: ${result}`, 'error');
                this.results.failed++;
                this.results.tests.push({ name, status: 'failed', error: result });
                return false;
            }
        } catch (error) {
            this.log(`✗ ${name}: ${error.message}`, 'error');
            this.results.failed++;
            this.results.tests.push({ name, status: 'failed', error: error.message });
            return false;
        }
    }

    async setupTestEnvironment() {
        this.log(`Setting up test environment: ${this.testDir}`);
        
        // Create test directory
        fs.mkdirSync(this.testDir, { recursive: true });
        
        // Create package.json
        const testPackageJson = {
            name: "test-claude-pm-installation",
            version: "1.0.0",
            dependencies: {
                "@bobmatnyc/claude-multiagent-pm": `^${this.version}`
            }
        };
        
        fs.writeFileSync(
            path.join(this.testDir, 'package.json'), 
            JSON.stringify(testPackageJson, null, 2)
        );
        
        this.log(`✓ Test environment ready`);
    }

    async installPackage() {
        this.log('Installing NPM package...');
        
        try {
            execSync('npm install', {
                cwd: this.testDir,
                stdio: 'pipe',
                timeout: 60000 // 60 second timeout
            });
            
            this.log('✓ NPM package installed successfully');
            return true;
        } catch (error) {
            this.log(`Package installation failed: ${error.message}`, 'error');
            return false;
        }
    }

    testPackageStructure() {
        return this.test('Package structure exists', () => {
            const packageDir = path.join(this.testDir, 'node_modules', '@bobmatnyc', 'claude-multiagent-pm');
            
            if (!fs.existsSync(packageDir)) {
                return 'Package directory not found';
            }
            
            const requiredFiles = [
                'package.json',
                'bin/claude-pm',
                'claude_pm',
                'framework/CLAUDE.md',
                'install/postinstall.js'
            ];
            
            for (const file of requiredFiles) {
                if (!fs.existsSync(path.join(packageDir, file))) {
                    return `Required file missing: ${file}`;
                }
            }
            
            return true;
        });
    }

    testDependencyInstallation() {
        return this.test('Dependencies installed correctly', () => {
            const packageDir = path.join(this.testDir, 'node_modules', '@bobmatnyc', 'claude-multiagent-pm');
            const aiTrackdownDir = path.join(packageDir, 'node_modules', '@bobmatnyc', 'ai-trackdown-tools');
            
            if (!fs.existsSync(aiTrackdownDir)) {
                return '@bobmatnyc/ai-trackdown-tools dependency not installed';
            }
            
            const aiTrackdownPackage = path.join(aiTrackdownDir, 'package.json');
            if (!fs.existsSync(aiTrackdownPackage)) {
                return 'ai-trackdown-tools package.json not found';
            }
            
            return true;
        });
    }

    testCLIAvailability() {
        return this.test('CLI commands available', () => {
            try {
                const result = execSync('npx claude-pm --version', {
                    cwd: this.testDir,
                    encoding: 'utf8',
                    timeout: 10000
                });
                
                if (!result.includes(this.version)) {
                    return `Version mismatch: expected ${this.version}, got ${result.trim()}`;
                }
                
                return true;
            } catch (error) {
                return `CLI not available: ${error.message}`;
            }
        });
    }

    testVersionConsistency() {
        return this.test('Version display consistency', () => {
            try {
                const versionOutput = execSync('npx claude-pm --version', {
                    cwd: this.testDir,
                    encoding: 'utf8',
                    timeout: 10000
                });
                
                const systemInfoOutput = execSync('npx claude-pm --system-info', {
                    cwd: this.testDir,
                    encoding: 'utf8',
                    timeout: 15000
                });
                
                if (!versionOutput.includes(`v${this.version}`)) {
                    return `Version command doesn't show v${this.version}`;
                }
                
                if (!systemInfoOutput.includes(`v${this.version}`)) {
                    return `System info doesn't show v${this.version}`;
                }
                
                return true;
            } catch (error) {
                return `Version consistency check failed: ${error.message}`;
            }
        });
    }

    testFrameworkDeployment() {
        return this.test('Framework CLAUDE.md deployment', () => {
            // Run fix script to deploy framework
            try {
                const packageDir = path.join(this.testDir, 'node_modules', '@bobmatnyc', 'claude-multiagent-pm');
                const fixScript = path.join(packageDir, 'scripts', 'fix_npm_deployment.js');
                
                if (fs.existsSync(fixScript)) {
                    execSync(`node "${fixScript}"`, {
                        cwd: this.testDir,
                        stdio: 'pipe',
                        timeout: 10000
                    });
                }
                
                // Check if CLAUDE.md was deployed
                const claudemdPath = path.join(this.testDir, 'CLAUDE.md');
                if (!fs.existsSync(claudemdPath)) {
                    return 'CLAUDE.md not deployed to working directory';
                }
                
                const content = fs.readFileSync(claudemdPath, 'utf8');
                
                if (content.includes('{{FRAMEWORK_VERSION}}')) {
                    return 'Template variables not replaced in CLAUDE.md';
                }
                
                if (!content.includes(this.version)) {
                    return `CLAUDE.md doesn't contain version ${this.version}`;
                }
                
                return true;
            } catch (error) {
                return `Framework deployment failed: ${error.message}`;
            }
        });
    }

    testMemorySystemDetection() {
        return this.test('Memory system detection', () => {
            try {
                const systemInfoOutput = execSync('npx claude-pm --system-info', {
                    cwd: this.testDir,
                    encoding: 'utf8',
                    timeout: 15000
                });
                
                if (!systemInfoOutput.includes('🧠 Memory:')) {
                    return 'Memory system not detected in system info';
                }
                
                return true;
            } catch (error) {
                return `Memory system detection failed: ${error.message}`;
            }
        });
    }

    testAiTrackdownIntegration() {
        return this.test('AI-trackdown integration', () => {
            try {
                const systemInfoOutput = execSync('npx claude-pm --system-info', {
                    cwd: this.testDir,
                    encoding: 'utf8',
                    timeout: 15000
                });
                
                if (!systemInfoOutput.includes('🔍 AI-trackdown-tools Version:')) {
                    return 'AI-trackdown tools not detected';
                }
                
                return true;
            } catch (error) {
                return `AI-trackdown integration test failed: ${error.message}`;
            }
        });
    }

    async cleanup() {
        try {
            fs.rmSync(this.testDir, { recursive: true, force: true });
            this.log(`✓ Test environment cleaned up`);
        } catch (error) {
            this.log(`Warning: Could not clean up test directory: ${error.message}`, 'warn');
        }
    }

    async runAllTests() {
        this.log(`🧪 Starting complete installation test for v${this.version}`);
        console.log('');
        
        try {
            await this.setupTestEnvironment();
            
            const installSuccess = await this.installPackage();
            if (!installSuccess) {
                this.log('Installation failed, skipping remaining tests', 'error');
                return false;
            }
            
            console.log('');
            this.log('Running validation tests...', 'test');
            
            this.testPackageStructure();
            this.testDependencyInstallation();
            this.testCLIAvailability();
            this.testVersionConsistency();
            this.testFrameworkDeployment();
            this.testMemorySystemDetection();
            this.testAiTrackdownIntegration();
            
            console.log('');
            this.log('📊 Test Results:', 'info');
            this.log(`   - Passed: ${this.results.passed}`);
            this.log(`   - Failed: ${this.results.failed}`);
            this.log(`   - Total:  ${this.results.passed + this.results.failed}`);
            
            if (this.results.failed === 0) {
                console.log('');
                this.log('🎉 All tests passed! Installation is working correctly.', 'success');
                return true;
            } else {
                console.log('');
                this.log('⚠️ Some tests failed. See details above.', 'warn');
                return false;
            }
            
        } catch (error) {
            this.log(`Test execution failed: ${error.message}`, 'error');
            return false;
        } finally {
            await this.cleanup();
        }
    }
}

// CLI execution
if (require.main === module) {
    const tester = new InstallationTester();
    
    tester.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Test runner failed:', error.message);
            process.exit(1);
        });
}

module.exports = InstallationTester;