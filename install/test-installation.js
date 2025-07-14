#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Installation Test Script
 * 
 * Comprehensive testing of NPM package installation and Python integration
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class InstallationTester {
    constructor() {
        this.platform = os.platform();
        this.packageRoot = path.join(__dirname, '..');
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
        
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            details: []
        };
    }

    /**
     * Log test result
     */
    log(message, status = 'info', critical = false) {
        const timestamp = new Date().toISOString();
        const icons = {
            pass: '✅',
            fail: '❌',
            warn: '⚠️',
            info: 'ℹ️'
        };
        
        const icon = icons[status] || icons.info;
        console.log(`${icon} [${timestamp}] ${message}`);
        
        this.results.details.push({
            timestamp,
            message,
            status,
            critical
        });
        
        if (status === 'pass') this.results.passed++;
        else if (status === 'fail') this.results.failed++;
        else if (status === 'warn') this.results.warnings++;
    }

    /**
     * Execute command safely
     */
    execCommand(command, options = {}) {
        try {
            const result = execSync(command, {
                encoding: 'utf8',
                timeout: options.timeout || 30000,
                stdio: 'pipe',
                ...options
            });
            return { success: true, output: result.trim() };
        } catch (error) {
            return { 
                success: false, 
                error: error.message,
                stderr: error.stderr ? error.stderr.toString() : '',
                code: error.status
            };
        }
    }

    /**
     * Test Python environment and dependencies
     */
    testPythonEnvironment() {
        this.log('Testing Python environment...', 'info');
        
        // Find Python command
        const pythonCommands = ['python3', 'python'];
        let pythonCmd = null;
        
        for (const cmd of pythonCommands) {
            const result = this.execCommand(`${cmd} --version`);
            if (result.success && result.output.includes('Python 3.')) {
                pythonCmd = cmd;
                this.log(`Python command found: ${cmd} (${result.output})`, 'pass');
                break;
            }
        }
        
        if (!pythonCmd) {
            this.log('Python 3.8+ not found', 'fail', true);
            return false;
        }
        
        // Test core dependencies
        const coreDeps = [
            'click', 'rich', 'pydantic', 'yaml', 
            'dotenv', 'requests', 'openai'
        ];
        
        let coreSuccess = true;
        for (const dep of coreDeps) {
            const result = this.execCommand(`${pythonCmd} -c "import ${dep}; print('${dep} available')"`);
            if (result.success) {
                this.log(`Core dependency ${dep} available`, 'pass');
            } else {
                this.log(`Core dependency ${dep} missing`, 'fail');
                coreSuccess = false;
            }
        }
        
        // Test AI dependencies (optional)
        const aiDeps = [
            'mem0', 'chromadb', 'aiosqlite', 'tiktoken'
        ];
        
        let aiSuccess = true;
        for (const dep of aiDeps) {
            const result = this.execCommand(`${pythonCmd} -c "import ${dep}; print('${dep} available')"`);
            if (result.success) {
                this.log(`AI dependency ${dep} available`, 'pass');
            } else {
                this.log(`AI dependency ${dep} missing`, 'warn');
                aiSuccess = false;
            }
        }
        
        return { pythonCmd, coreSuccess, aiSuccess };
    }

    /**
     * Test Claude PM package installation
     */
    testClaudePmPackage(pythonCmd) {
        this.log('Testing Claude PM package installation...', 'info');
        
        // Test package import
        const importResult = this.execCommand(`${pythonCmd} -c "import claude_pm; print('Package import successful')"`);
        if (importResult.success) {
            this.log('Claude PM package import successful', 'pass');
        } else {
            this.log(`Claude PM package import failed: ${importResult.error}`, 'fail', true);
            return false;
        }
        
        // Test CLI module
        const cliResult = this.execCommand(`${pythonCmd} -c "from claude_pm.cli import main; print('CLI module available')"`);
        if (cliResult.success) {
            this.log('Claude PM CLI module available', 'pass');
        } else {
            this.log(`Claude PM CLI module failed: ${cliResult.error}`, 'fail');
        }
        
        // Test core components
        const components = [
            'claude_pm.core.base_agent',
            'claude_pm.services.claude_pm_memory',
            'claude_pm.agents.pm_agent'
        ];
        
        for (const component of components) {
            const result = this.execCommand(`${pythonCmd} -c "import ${component}; print('${component} available')"`);
            if (result.success) {
                this.log(`Component ${component} available`, 'pass');
            } else {
                this.log(`Component ${component} missing: ${result.error}`, 'warn');
            }
        }
        
        return true;
    }

    /**
     * Test CLI command availability
     */
    testCliCommands(pythonCmd) {
        this.log('Testing CLI command availability...', 'info');
        
        // Test direct Python module execution
        const moduleResult = this.execCommand(`${pythonCmd} -m claude_pm.cli --help`);
        if (moduleResult.success) {
            this.log('Python module CLI execution works', 'pass');
        } else {
            this.log(`Python module CLI failed: ${moduleResult.error}`, 'fail');
        }
        
        // Test installed CLI command
        const cliResult = this.execCommand('claude-pm --help');
        if (cliResult.success) {
            this.log('Global claude-pm command available', 'pass');
        } else {
            this.log('Global claude-pm command not available (expected for local install)', 'warn');
        }
        
        return moduleResult.success;
    }

    /**
     * Test directory structure
     */
    testDirectoryStructure() {
        this.log('Testing directory structure...', 'info');
        
        // Check package directory structure
        const requiredDirs = [
            'bin', 'claude_pm', 'install', 'framework'
        ];
        
        for (const dir of requiredDirs) {
            const dirPath = path.join(this.packageRoot, dir);
            if (fs.existsSync(dirPath)) {
                this.log(`Directory ${dir} exists`, 'pass');
            } else {
                this.log(`Directory ${dir} missing`, 'fail');
            }
        }
        
        // Check package files
        const requiredFiles = [
            'package.json', 'pyproject.toml', 'bin/claude-pm'
        ];
        
        for (const file of requiredFiles) {
            const filePath = path.join(this.packageRoot, file);
            if (fs.existsSync(filePath)) {
                this.log(`File ${file} exists`, 'pass');
            } else {
                this.log(`File ${file} missing`, 'fail');
            }
        }
        
        // Check .claude-pm directory
        if (fs.existsSync(this.globalConfigDir)) {
            this.log('.claude-pm directory exists', 'pass');
        } else {
            this.log('.claude-pm directory missing (will be created on init)', 'warn');
        }
        
        return true;
    }

    /**
     * Test configuration files
     */
    testConfigurationFiles() {
        this.log('Testing configuration files...', 'info');
        
        // Test package.json
        try {
            const packageJson = JSON.parse(fs.readFileSync(path.join(this.packageRoot, 'package.json'), 'utf8'));
            
            if (packageJson.name === '@bobmatnyc/claude-multiagent-pm') {
                this.log('Package name correct', 'pass');
            } else {
                this.log(`Package name incorrect: ${packageJson.name}`, 'fail');
            }
            
            if (packageJson.bin && packageJson.bin['claude-pm']) {
                this.log('CLI binary configured', 'pass');
            } else {
                this.log('CLI binary not configured', 'fail');
            }
            
            if (packageJson.files && packageJson.files.includes('pyproject.toml')) {
                this.log('pyproject.toml included in NPM package', 'pass');
            } else {
                this.log('pyproject.toml not included in NPM package', 'fail');
            }
            
        } catch (error) {
            this.log(`Package.json parsing failed: ${error.message}`, 'fail');
        }
        
        // Test pyproject.toml
        try {
            const pyprojectContent = fs.readFileSync(path.join(this.packageRoot, 'pyproject.toml'), 'utf8');
            
            if (pyprojectContent.includes('claude-multiagent-pm')) {
                this.log('pyproject.toml contains correct package name', 'pass');
            } else {
                this.log('pyproject.toml package name issue', 'warn');
            }
            
            if (pyprojectContent.includes('[project.scripts]')) {
                this.log('CLI scripts configured in pyproject.toml', 'pass');
            } else {
                this.log('CLI scripts not configured in pyproject.toml', 'warn');
            }
            
        } catch (error) {
            this.log(`pyproject.toml reading failed: ${error.message}`, 'fail');
        }
        
        return true;
    }

    /**
     * Generate installation test report
     */
    generateReport() {
        const report = {
            summary: {
                passed: this.results.passed,
                failed: this.results.failed,
                warnings: this.results.warnings,
                total: this.results.passed + this.results.failed + this.results.warnings,
                success: this.results.failed === 0
            },
            system: {
                platform: this.platform,
                timestamp: new Date().toISOString(),
                packageRoot: this.packageRoot
            },
            details: this.results.details
        };
        
        return report;
    }

    /**
     * Run comprehensive installation test
     */
    async runTests() {
        console.log('\n🧪 Claude PM Framework - Installation Test\n');
        console.log('='.repeat(50));
        
        this.log('Starting installation test suite', 'info');
        
        try {
            // Test directory structure
            this.testDirectoryStructure();
            
            // Test configuration files
            this.testConfigurationFiles();
            
            // Test Python environment
            const pythonTest = this.testPythonEnvironment();
            
            if (pythonTest && pythonTest.pythonCmd) {
                // Test Claude PM package
                this.testClaudePmPackage(pythonTest.pythonCmd);
                
                // Test CLI commands
                this.testCliCommands(pythonTest.pythonCmd);
            }
            
            // Generate report
            const report = this.generateReport();
            
            console.log('\n📊 Installation Test Summary:');
            console.log(`✅ Passed: ${report.summary.passed}`);
            console.log(`❌ Failed: ${report.summary.failed}`);
            console.log(`⚠️  Warnings: ${report.summary.warnings}`);
            
            if (report.summary.success) {
                console.log('\n🎉 Installation test passed! Claude PM Framework is ready to use.');
                console.log('\n🚀 Next steps:');
                console.log('   1. Run: claude-pm init --post-install');
                console.log('   2. Run: claude-pm init --validate');
                console.log('   3. Start using: claude-pm help');
            } else {
                console.log('\n❌ Installation test failed. Please address the issues above.');
                console.log('\n🔧 Common fixes:');
                console.log('   1. Ensure Python 3.8+ is installed');
                console.log('   2. Install missing dependencies: pip install -e .');
                console.log('   3. Check file permissions and paths');
                console.log('   4. Retry: npm run install:dependencies');
            }
            
            return report;
            
        } catch (error) {
            this.log(`Test suite error: ${error.message}`, 'fail', true);
            console.log('\n❌ Installation test encountered an error.');
            return this.generateReport();
        }
    }
}

// Run tests when script is executed directly
if (require.main === module) {
    const tester = new InstallationTester();
    
    tester.runTests()
        .then((report) => {
            process.exit(report.summary.success ? 0 : 1);
        })
        .catch((error) => {
            console.error('Installation test failed:', error.message);
            process.exit(1);
        });
}

module.exports = InstallationTester;