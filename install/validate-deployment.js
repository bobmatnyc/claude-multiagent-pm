#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Deployment Validation Script
 * 
 * Validates that a deployment is fully functional and ready for use.
 * Tests all critical components including ai-trackdown-tools integration.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

class DeploymentValidator {
    constructor(options = {}) {
        this.deploymentDir = options.deploymentDir || process.cwd();
        this.verbose = options.verbose || false;
        this.errors = [];
        this.warnings = [];
    }

    /**
     * Log message with optional verbose filtering
     */
    log(message, force = false) {
        if (this.verbose || force) {
            console.log(`[Deployment Validator] ${message}`);
        }
    }

    /**
     * Add error to validation results
     */
    addError(message) {
        this.errors.push(message);
        this.log(`❌ ERROR: ${message}`, true);
    }

    /**
     * Add warning to validation results
     */
    addWarning(message) {
        this.warnings.push(message);
        this.log(`⚠ WARNING: ${message}`, true);
    }

    /**
     * Validate deployment directory structure
     */
    async validateStructure() {
        this.log('Validating deployment structure...', true);
        
        const requiredPaths = [
            'claude_pm',
            'templates',
            'schemas',
            'tasks',
            'bin',
            '.claude-pm',
            'CLAUDE.md'
        ];
        
        for (const requiredPath of requiredPaths) {
            const fullPath = path.join(this.deploymentDir, requiredPath);
            
            try {
                await fs.access(fullPath);
                this.log(`✓ ${requiredPath} exists`);
            } catch (error) {
                this.addError(`Required path missing: ${requiredPath}`);
            }
        }
        
        // Check ticketing hierarchy
        const ticketDirs = ['epics', 'issues', 'tasks', 'prs', 'templates', 'archive', 'reports'];
        for (const ticketDir of ticketDirs) {
            const ticketPath = path.join(this.deploymentDir, 'tickets', ticketDir);
            
            try {
                await fs.access(ticketPath);
                this.log(`✓ tickets/${ticketDir} exists`);
            } catch (error) {
                this.addError(`Ticketing directory missing: tickets/${ticketDir}`);
            }
        }
        
        // Check .ai-trackdown directory
        const trackingPath = path.join(this.deploymentDir, 'tickets', '.ai-trackdown', 'counters.json');
        try {
            await fs.access(trackingPath);
            this.log(`✓ tickets/.ai-trackdown/counters.json exists`);
        } catch (error) {
            this.addError(`Ticketing counters file missing: tickets/.ai-trackdown/counters.json`);
        }
    }

    /**
     * Validate configuration files
     */
    async validateConfiguration() {
        this.log('Validating configuration files...', true);
        
        const configPath = path.join(this.deploymentDir, '.claude-pm', 'config.json');
        
        try {
            const configData = await fs.readFile(configPath, 'utf8');
            const config = JSON.parse(configData);
            
            // Check required config fields
            const requiredFields = ['version', 'deployedAt', 'platform', 'deploymentDir'];
            for (const field of requiredFields) {
                if (!config[field]) {
                    this.addError(`Missing config field: ${field}`);
                } else {
                    this.log(`✓ Config field present: ${field}`);
                }
            }
            
            // Check optional but important fields
            if (config.aiTrackdownPath) {
                this.log(`✓ Ticketing path configured: ${config.aiTrackdownPath}`);
            } else {
                this.addWarning(`Ticketing path not configured - ticketing may be disabled`);
            }
            
            if (config.features && config.features.ticketingEnabled) {
                this.log(`✓ Ticketing feature enabled`);
            } else {
                this.addWarning(`Ticketing feature disabled - install ai-trackdown-pytools to enable`);
            }
            
            // Validate paths
            if (config.paths) {
                for (const [pathName, pathValue] of Object.entries(config.paths)) {
                    try {
                        await fs.access(pathValue);
                        this.log(`✓ Config path valid: ${pathName}`);
                    } catch (error) {
                        this.addError(`Invalid config path ${pathName}: ${pathValue}`);
                    }
                }
            }
            
        } catch (error) {
            this.addError(`Configuration validation failed: ${error.message}`);
        }
    }

    /**
     * Validate CLI wrappers
     */
    async validateCLIWrappers() {
        this.log('Validating CLI wrappers...', true);
        
        const platform = process.platform;
        const binDir = path.join(this.deploymentDir, 'bin');
        
        const expectedWrappers = platform === 'win32' ? 
            ['aitrackdown.bat', 'atd.bat'] : 
            ['aitrackdown', 'atd'];
        
        for (const wrapper of expectedWrappers) {
            const wrapperPath = path.join(binDir, wrapper);
            
            try {
                await fs.access(wrapperPath);
                
                // Check if executable (Unix only)
                if (platform !== 'win32') {
                    const stats = await fs.stat(wrapperPath);
                    if (!(stats.mode & 0o111)) {
                        this.addError(`CLI wrapper not executable: ${wrapper}`);
                    } else {
                        this.log(`✓ CLI wrapper executable: ${wrapper}`);
                    }
                } else {
                    this.log(`✓ CLI wrapper exists: ${wrapper}`);
                }
                
            } catch (error) {
                this.addError(`CLI wrapper missing: ${wrapper}`);
            }
        }
    }

    /**
     * Test AI-trackdown functionality
     */
    async testAiTrackdownIntegration() {
        this.log('Testing AI-trackdown integration...', true);
        
        const platform = process.platform;
        const cliPath = path.join(this.deploymentDir, 'bin', platform === 'win32' ? 'aitrackdown.bat' : 'aitrackdown');
        
        try {
            // Check if CLI wrapper exists
            await fs.access(cliPath);
            
            // Test version command
            const versionResult = await this.runCommand(cliPath, ['--version'], {
                cwd: this.deploymentDir,
                timeout: 10000
            });
            
            if (versionResult.success) {
                this.log('✓ AI-trackdown version command works');
                
                // Test list command (core ticketing functionality)
                const listResult = await this.runCommand(cliPath, ['list'], {
                    cwd: this.deploymentDir,
                    timeout: 10000
                });
                
                if (listResult.success) {
                    this.log('✓ AI-trackdown ticketing commands work');
                } else {
                    this.addWarning(`AI-trackdown ticketing not fully functional: ${listResult.error}`);
                    this.addWarning(`Install ai-trackdown-pytools: pip install --user ai-trackdown-pytools==1.4.0`);
                }
            } else {
                this.addWarning(`AI-trackdown CLI not functional - ticketing disabled`);
                this.addWarning(`This is expected if ai-trackdown-pytools is not installed`);
                this.addWarning(`Install with: pip install --user ai-trackdown-pytools==1.4.0`);
            }
            
            // Test help command
            const helpResult = await this.runCommand(cliPath, ['--help'], {
                cwd: this.deploymentDir,
                timeout: 10000
            });
            
            if (helpResult.success) {
                this.log('✓ AI-trackdown help command works');
            } else {
                this.log(`⚠ AI-trackdown help command unavailable`);
            }
            
        } catch (error) {
            this.addWarning(`AI-trackdown CLI wrappers present but package not installed`);
            this.addWarning(`This is normal - install ai-trackdown-pytools to enable ticketing`);
        }
    }

    /**
     * Validate Python environment
     */
    async validatePythonEnvironment() {
        this.log('Validating Python environment...', true);
        
        try {
            // Read config to get Python command
            const configPath = path.join(this.deploymentDir, '.claude-pm', 'config.json');
            const configData = await fs.readFile(configPath, 'utf8');
            const config = JSON.parse(configData);
            
            const pythonCmd = config.pythonCmd || 'python3';
            
            // Test Python version
            const pythonVersion = execSync(`${pythonCmd} --version`, { 
                encoding: 'utf8',
                cwd: this.deploymentDir 
            }).trim();
            
            this.log(`✓ Python available: ${pythonVersion}`);
            
            // Test if framework core is importable
            const testImport = await this.runCommand(pythonCmd, ['-c', 'import claude_pm; print("Framework importable")'], {
                cwd: this.deploymentDir,
                timeout: 10000
            });
            
            if (testImport.success) {
                this.log('✓ Framework core importable');
            } else {
                this.addWarning(`Framework core import failed: ${testImport.error}`);
            }
            
        } catch (error) {
            this.addError(`Python environment validation failed: ${error.message}`);
        }
    }

    /**
     * Validate health check script
     */
    async validateHealthCheck() {
        this.log('Validating health check script...', true);
        
        const platform = process.platform;
        const healthScript = path.join(this.deploymentDir, 'scripts', platform === 'win32' ? 'health-check.bat' : 'health-check.sh');
        
        try {
            await fs.access(healthScript);
            
            // Test health check execution
            const result = await this.runCommand(healthScript, [], {
                cwd: this.deploymentDir,
                timeout: 30000
            });
            
            if (result.success) {
                this.log('✓ Health check script works');
            } else {
                this.addWarning(`Health check script failed: ${result.error}`);
            }
            
        } catch (error) {
            this.addError(`Health check script validation failed: ${error.message}`);
        }
    }

    /**
     * Run command with timeout
     */
    runCommand(command, args, options = {}) {
        return new Promise((resolve) => {
            const child = spawn(command, args, {
                ...options,
                stdio: 'pipe'
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout?.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr?.on('data', (data) => {
                stderr += data.toString();
            });
            
            const timeout = setTimeout(() => {
                child.kill();
                resolve({ success: false, error: 'Command timeout' });
            }, options.timeout || 30000);
            
            child.on('close', (code) => {
                clearTimeout(timeout);
                resolve({
                    success: code === 0,
                    stdout,
                    stderr,
                    error: code !== 0 ? `Exit code: ${code}` : null
                });
            });
            
            child.on('error', (error) => {
                clearTimeout(timeout);
                resolve({
                    success: false,
                    error: error.message
                });
            });
        });
    }

    /**
     * Generate validation report
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            deploymentDir: this.deploymentDir,
            validation: {
                passed: this.errors.length === 0,
                errors: this.errors,
                warnings: this.warnings,
                summary: {
                    totalErrors: this.errors.length,
                    totalWarnings: this.warnings.length,
                    status: this.errors.length === 0 ? 'PASS' : 'FAIL'
                }
            }
        };
        
        return report;
    }

    /**
     * Main validation process
     */
    async validate() {
        try {
            this.log(`🔍 Starting deployment validation for: ${this.deploymentDir}`, true);
            
            await this.validateStructure();
            await this.validateConfiguration();
            await this.validateCLIWrappers();
            await this.testAiTrackdownIntegration();
            await this.validatePythonEnvironment();
            await this.validateHealthCheck();
            
            const report = this.generateReport();
            
            if (report.validation.passed) {
                this.log('🎉 Deployment validation completed successfully!', true);
                this.log(`Errors: ${report.validation.summary.totalErrors}`, true);
                this.log(`Warnings: ${report.validation.summary.totalWarnings}`, true);
            } else {
                this.log('❌ Deployment validation failed', true);
                this.log(`Errors: ${report.validation.summary.totalErrors}`, true);
                this.log(`Warnings: ${report.validation.summary.totalWarnings}`, true);
            }
            
            return report;
            
        } catch (error) {
            this.log(`❌ Validation failed: ${error.message}`, true);
            throw error;
        }
    }
}

// CLI interface when run directly
if (require.main === module) {
    const args = process.argv.slice(2);
    
    const options = {
        deploymentDir: process.cwd(),
        verbose: args.includes('--verbose') || args.includes('-v')
    };
    
    // Parse deployment directory
    const targetIndex = args.findIndex(arg => arg === '--target' || arg === '-t');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
        options.deploymentDir = path.resolve(args[targetIndex + 1]);
    }
    
    const validator = new DeploymentValidator(options);
    
    validator.validate()
        .then((report) => {
            if (args.includes('--json')) {
                console.log(JSON.stringify(report, null, 2));
            }
            process.exit(report.validation.passed ? 0 : 1);
        })
        .catch((error) => {
            console.error('Validation failed:', error.message);
            process.exit(1);
        });
}

module.exports = DeploymentValidator;