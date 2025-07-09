#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Environment Validation
 * 
 * Comprehensive validation of system requirements and environment
 * setup for the Claude PM Framework installation.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawn } = require('child_process');

class EnvironmentValidator {
    constructor(options = {}) {
        this.verbose = options.verbose || false;
        this.skipOptional = options.skipOptional || false;
        this.targetDir = options.targetDir || process.cwd();
        
        this.platform = os.platform();
        this.arch = os.arch();
        this.nodeVersion = process.version;
        
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            details: []
        };
    }

    /**
     * Log validation result
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
        
        if (this.verbose || status !== 'info') {
            console.log(`${icon} [${timestamp}] ${message}`);
        }
        
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
     * Execute command safely and return result
     */
    async execCommand(command, options = {}) {
        try {
            const result = execSync(command, {
                encoding: 'utf8',
                timeout: options.timeout || 10000,
                ...options
            });
            return { success: true, output: result.trim() };
        } catch (error) {
            return { 
                success: false, 
                error: error.message,
                code: error.status
            };
        }
    }

    /**
     * Validate Node.js version and environment
     */
    async validateNodejs() {
        this.log('Validating Node.js environment...', 'info');
        
        // Check Node.js version
        const majorVersion = parseInt(this.nodeVersion.slice(1).split('.')[0]);
        const minorVersion = parseInt(this.nodeVersion.slice(1).split('.')[1]);
        
        if (majorVersion < 16) {
            this.log(
                `Node.js 16.0.0 or higher required. Found: ${this.nodeVersion}`, 
                'fail', 
                true
            );
            return false;
        }
        
        this.log(`Node.js ${this.nodeVersion} detected`, 'pass');
        
        // Check npm availability
        const npmCheck = await this.execCommand('npm --version');
        if (npmCheck.success) {
            this.log(`npm ${npmCheck.output} available`, 'pass');
        } else {
            this.log('npm not found', 'warn');
        }
        
        // Check npx availability
        const npxCheck = await this.execCommand('npx --version');
        if (npxCheck.success) {
            this.log(`npx ${npxCheck.output} available`, 'pass');
        } else {
            this.log('npx not found', 'warn');
        }
        
        return true;
    }

    /**
     * Validate Python environment
     */
    async validatePython() {
        this.log('Validating Python environment...', 'info');
        
        let pythonCmd = null;
        let pythonVersion = null;
        
        // Try python3 first
        const python3Check = await this.execCommand('python3 --version');
        if (python3Check.success) {
            pythonCmd = 'python3';
            pythonVersion = python3Check.output;
        } else {
            // Fall back to python
            const pythonCheck = await this.execCommand('python --version');
            if (pythonCheck.success) {
                pythonCmd = 'python';
                pythonVersion = pythonCheck.output;
            }
        }
        
        if (!pythonCmd) {
            this.log('Python not found. Python 3.8+ is required.', 'fail', true);
            return false;
        }
        
        // Parse version
        const versionMatch = pythonVersion.match(/Python (\d+)\.(\d+)\.(\d+)/);
        if (!versionMatch) {
            this.log(`Unable to parse Python version: ${pythonVersion}`, 'fail', true);
            return false;
        }
        
        const [, major, minor, patch] = versionMatch.map(Number);
        
        if (major < 3 || (major === 3 && minor < 8)) {
            this.log(
                `Python 3.8+ required. Found: ${pythonVersion}`, 
                'fail', 
                true
            );
            return false;
        }
        
        this.log(`${pythonVersion} detected`, 'pass');
        
        // Check pip availability
        const pipCheck = await this.execCommand(`${pythonCmd} -m pip --version`);
        if (pipCheck.success) {
            this.log(`pip available: ${pipCheck.output.split(' ')[1]}`, 'pass');
        } else {
            this.log('pip not found - may need manual dependency installation', 'warn');
        }
        
        // Check if virtual environment is recommended
        const venvCheck = await this.execCommand(`${pythonCmd} -m venv --help`);
        if (venvCheck.success) {
            this.log('Virtual environment support available', 'pass');
        } else {
            this.log('Virtual environment support not found', 'warn');
        }
        
        return true;
    }

    /**
     * Validate system requirements
     */
    async validateSystem() {
        this.log('Validating system requirements...', 'info');
        
        // Check platform support
        const supportedPlatforms = ['win32', 'darwin', 'linux'];
        if (!supportedPlatforms.includes(this.platform)) {
            this.log(`Unsupported platform: ${this.platform}`, 'warn');
        } else {
            this.log(`Supported platform: ${this.platform}`, 'pass');
        }
        
        // Check architecture
        const supportedArchs = ['x64', 'arm64'];
        if (!supportedArchs.includes(this.arch)) {
            this.log(`Unsupported architecture: ${this.arch}`, 'warn');
        } else {
            this.log(`Supported architecture: ${this.arch}`, 'pass');
        }
        
        // Check available memory
        const totalMemory = os.totalmem();
        const freeMemory = os.freemem();
        const totalGB = (totalMemory / 1024 / 1024 / 1024).toFixed(1);
        const freeGB = (freeMemory / 1024 / 1024 / 1024).toFixed(1);
        
        this.log(`System memory: ${totalGB}GB total, ${freeGB}GB free`, 'info');
        
        if (totalMemory < 2 * 1024 * 1024 * 1024) { // Less than 2GB
            this.log('Low system memory detected - may impact performance', 'warn');
        } else {
            this.log('Sufficient system memory available', 'pass');
        }
        
        // Check CPU cores
        const cpuCores = os.cpus().length;
        this.log(`CPU cores: ${cpuCores}`, 'info');
        
        if (cpuCores < 2) {
            this.log('Single core CPU detected - may impact performance', 'warn');
        } else {
            this.log('Multi-core CPU available', 'pass');
        }
        
        return true;
    }

    /**
     * Validate filesystem permissions and space
     */
    async validateFilesystem() {
        this.log('Validating filesystem...', 'info');
        
        try {
            // Check target directory exists and is writable
            await fs.access(this.targetDir, fs.constants.W_OK);
            this.log(`Target directory writable: ${this.targetDir}`, 'pass');
        } catch (error) {
            this.log(`Target directory not writable: ${this.targetDir}`, 'fail', true);
            return false;
        }
        
        // Check available disk space (rough estimate)
        try {
            const stats = await fs.stat(this.targetDir);
            this.log('Target directory accessible', 'pass');
        } catch (error) {
            this.log(`Target directory not accessible: ${error.message}`, 'fail', true);
            return false;
        }
        
        // Test file creation and deletion
        const testFile = path.join(this.targetDir, '.claude-pm-test');
        try {
            await fs.writeFile(testFile, 'test');
            await fs.unlink(testFile);
            this.log('File operations test passed', 'pass');
        } catch (error) {
            this.log(`File operations test failed: ${error.message}`, 'fail', true);
            return false;
        }
        
        return true;
    }

    /**
     * Validate network connectivity (optional)
     */
    async validateNetwork() {
        if (this.skipOptional) {
            this.log('Skipping network validation', 'info');
            return true;
        }
        
        this.log('Validating network connectivity...', 'info');
        
        // Test npm registry connectivity
        const npmTest = await this.execCommand('npm ping', { timeout: 15000 });
        if (npmTest.success) {
            this.log('npm registry connectivity confirmed', 'pass');
        } else {
            this.log('npm registry not accessible - may affect package installations', 'warn');
        }
        
        // Test PyPI connectivity (Python Package Index)
        const pipTest = await this.execCommand('pip index versions pip', { timeout: 15000 });
        if (pipTest.success) {
            this.log('PyPI connectivity confirmed', 'pass');
        } else {
            this.log('PyPI not accessible - may affect Python package installations', 'warn');
        }
        
        return true;
    }

    /**
     * Validate existing Claude PM installation
     */
    async validateExistingInstallation() {
        this.log('Checking for existing installations...', 'info');
        
        // Check for global npm installation
        const globalCheck = await this.execCommand('npm list -g claude-multiagent-pm');
        if (globalCheck.success) {
            this.log('Global Claude PM installation detected', 'warn');
        }
        
        // Check for local installation
        const localPackageJson = path.join(this.targetDir, 'package.json');
        if (fsSync.existsSync(localPackageJson)) {
            try {
                const packageData = JSON.parse(
                    await fs.readFile(localPackageJson, 'utf8')
                );
                if (packageData.dependencies && packageData.dependencies['claude-multiagent-pm']) {
                    this.log('Local Claude PM installation detected in dependencies', 'warn');
                }
            } catch (error) {
                // Ignore package.json parsing errors
            }
        }
        
        // Check for framework directory
        const frameworkDir = path.join(this.targetDir, 'claude_pm');
        if (fsSync.existsSync(frameworkDir)) {
            this.log('Claude PM framework directory exists', 'warn');
        }
        
        return true;
    }

    /**
     * Generate validation report
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
                arch: this.arch,
                nodeVersion: this.nodeVersion,
                timestamp: new Date().toISOString()
            },
            details: this.results.details
        };
        
        return report;
    }

    /**
     * Main validation process
     */
    async validate() {
        this.log('Starting Claude PM Framework environment validation', 'info');
        this.log(`Target directory: ${this.targetDir}`, 'info');
        this.log(`Platform: ${this.platform} (${this.arch})`, 'info');
        this.log(`Node.js: ${this.nodeVersion}`, 'info');
        
        console.log('\n🔍 Validating Environment Requirements...\n');
        
        try {
            await this.validateNodejs();
            await this.validatePython();
            await this.validateSystem();
            await this.validateFilesystem();
            await this.validateNetwork();
            await this.validateExistingInstallation();
            
            const report = this.generateReport();
            
            console.log('\n📊 Validation Summary:');
            console.log(`✅ Passed: ${report.summary.passed}`);
            console.log(`❌ Failed: ${report.summary.failed}`);
            console.log(`⚠️  Warnings: ${report.summary.warnings}`);
            
            if (report.summary.success) {
                console.log('\n🎉 Environment validation passed! Ready for Claude PM Framework installation.');
            } else {
                console.log('\n❌ Environment validation failed. Please address the critical issues above.');
            }
            
            return report;
            
        } catch (error) {
            this.log(`Validation process error: ${error.message}`, 'fail', true);
            console.log('\n❌ Environment validation encountered an error.');
            return this.generateReport();
        }
    }
}

// CLI interface when run directly
if (require.main === module) {
    const args = process.argv.slice(2);
    
    const options = {
        verbose: args.includes('--verbose') || args.includes('-v'),
        skipOptional: args.includes('--skip-optional'),
        targetDir: process.cwd()
    };
    
    // Parse target directory
    const targetIndex = args.findIndex(arg => arg === '--target' || arg === '-t');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
        options.targetDir = path.resolve(args[targetIndex + 1]);
    }
    
    const validator = new EnvironmentValidator(options);
    
    validator.validate()
        .then((report) => {
            process.exit(report.summary.success ? 0 : 1);
        })
        .catch((error) => {
            console.error('Validation failed:', error.message);
            process.exit(1);
        });
}

module.exports = EnvironmentValidator;