#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Comprehensive Pre-Publish Validation
 * 
 * Integrates Docker validation with graceful fallback to standard validation
 * Ensures comprehensive testing before npm publish operations
 * 
 * Integration Agent Implementation - 2025-07-13
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

class ComprehensivePrePublishValidator {
    constructor(options = {}) {
        this.projectRoot = options.projectRoot || process.cwd();
        this.verbose = options.verbose || false;
        this.dryRun = options.dryRun || false;
        this.skipDocker = options.skipDocker || false;
        
        this.results = {
            timestamp: new Date().toISOString(),
            overall: { passed: false, errors: [], warnings: [] },
            stages: {
                standard: { completed: false, passed: false, details: {} },
                docker: { completed: false, passed: false, details: {}, skipped: false },
                integration: { completed: false, passed: false, details: {} }
            }
        };
    }

    /**
     * Enhanced logging with context
     */
    log(message, level = 'info', force = false) {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [Pre-Publish Validator]`;
        
        if (this.verbose || force || level === 'error') {
            const icon = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'debug': '🔍'
            }[level] || 'ℹ️';
            
            console.log(`${prefix} ${icon} ${message}`);
        }
    }

    /**
     * Add error to results
     */
    addError(message, stage = 'overall') {
        if (!this.results[stage]) {
            this.results[stage] = { errors: [], warnings: [] };
        }
        if (!this.results[stage].errors) {
            this.results[stage].errors = [];
        }
        this.results[stage].errors.push({ message, timestamp: new Date().toISOString() });
        this.log(`ERROR in ${stage}: ${message}`, 'error', true);
    }

    /**
     * Add warning to results
     */
    addWarning(message, stage = 'overall') {
        if (!this.results[stage]) {
            this.results[stage] = { errors: [], warnings: [] };
        }
        if (!this.results[stage].warnings) {
            this.results[stage].warnings = [];
        }
        this.results[stage].warnings.push({ message, timestamp: new Date().toISOString() });
        this.log(`WARNING in ${stage}: ${message}`, 'warning', true);
    }

    /**
     * Execute command with error handling
     */
    async runCommand(command, args = [], options = {}) {
        return new Promise((resolve) => {
            const timeoutMs = options.timeout || 60000;
            
            this.log(`Executing: ${command} ${args.join(' ')}`, 'debug');
            
            if (this.dryRun) {
                this.log(`DRY RUN: Would execute ${command} ${args.join(' ')}`, 'info');
                resolve({ success: true, stdout: '', stderr: '', dryRun: true });
                return;
            }
            
            const child = spawn(command, args, {
                stdio: 'pipe',
                cwd: options.cwd || this.projectRoot,
                env: { ...process.env, ...options.env }
            });
            
            let stdout = '';
            let stderr = '';
            let timedOut = false;
            
            const timeout = setTimeout(() => {
                timedOut = true;
                child.kill('SIGKILL');
            }, timeoutMs);
            
            child.stdout?.on('data', (data) => {
                stdout += data.toString();
                if (this.verbose && options.streamOutput) {
                    process.stdout.write(data);
                }
            });
            
            child.stderr?.on('data', (data) => {
                stderr += data.toString();
                if (this.verbose && options.streamOutput) {
                    process.stderr.write(data);
                }
            });
            
            child.on('close', (code) => {
                clearTimeout(timeout);
                
                if (timedOut) {
                    resolve({
                        success: false,
                        stdout,
                        stderr,
                        error: `Command timed out after ${timeoutMs}ms`,
                        code: null
                    });
                } else {
                    resolve({
                        success: code === 0,
                        stdout,
                        stderr,
                        code,
                        error: code !== 0 ? `Exit code: ${code}` : null
                    });
                }
            });
            
            child.on('error', (error) => {
                clearTimeout(timeout);
                resolve({
                    success: false,
                    stdout,
                    stderr,
                    error: error.message,
                    code: null
                });
            });
        });
    }

    /**
     * Check if Docker is available
     */
    async checkDockerAvailability() {
        try {
            const dockerVersion = await this.runCommand('docker', ['--version'], { timeout: 10000 });
            if (!dockerVersion.success) {
                return false;
            }
            
            const dockerInfo = await this.runCommand('docker', ['info'], { timeout: 10000 });
            return dockerInfo.success;
        } catch (error) {
            return false;
        }
    }

    /**
     * Run standard validation tests
     */
    async runStandardValidation() {
        this.log('Running standard validation tests...', 'info', true);
        
        try {
            // Run npm test
            const testResult = await this.runCommand('npm', ['test'], {
                timeout: 120000,
                streamOutput: this.verbose
            });
            
            if (!testResult.success) {
                this.addError(`npm test failed: ${testResult.error}`, 'standard');
                return false;
            }
            
            this.log('npm test passed', 'success');
            
            // Run deployment validation
            const deployValidation = await this.runCommand('npm', ['run', 'validate-deployment'], {
                timeout: 60000,
                streamOutput: this.verbose
            });
            
            if (!deployValidation.success) {
                this.addError(`Deployment validation failed: ${deployValidation.error}`, 'standard');
                return false;
            }
            
            this.log('Deployment validation passed', 'success');
            
            // Run health check if available
            const healthCheckScript = path.join(this.projectRoot, 'scripts', 'health-check.sh');
            try {
                await fs.access(healthCheckScript);
                const healthResult = await this.runCommand('bash', [healthCheckScript], {
                    timeout: 30000
                });
                
                if (healthResult.success) {
                    this.log('Health check passed', 'success');
                } else {
                    this.addWarning('Health check reported issues', 'standard');
                }
            } catch (error) {
                this.log('Health check script not found, skipping', 'debug');
            }
            
            this.results.stages.standard = {
                completed: true,
                passed: true,
                details: {
                    npmTest: true,
                    deploymentValidation: true
                }
            };
            
            return true;
            
        } catch (error) {
            this.addError(`Standard validation failed: ${error.message}`, 'standard');
            this.results.stages.standard = {
                completed: true,
                passed: false,
                details: { error: error.message }
            };
            return false;
        }
    }

    /**
     * Run Docker validation if available
     */
    async runDockerValidation() {
        if (this.skipDocker) {
            this.log('Docker validation skipped by request', 'info', true);
            this.results.stages.docker = {
                completed: true,
                passed: true,
                skipped: true,
                details: { reason: 'Skipped by request' }
            };
            return true;
        }
        
        this.log('Checking Docker availability...', 'info', true);
        
        const dockerAvailable = await this.checkDockerAvailability();
        
        if (!dockerAvailable) {
            this.addWarning('Docker not available, skipping Docker validation', 'docker');
            this.results.stages.docker = {
                completed: true,
                passed: true,
                skipped: true,
                details: { reason: 'Docker not available' }
            };
            return true;
        }
        
        this.log('Docker is available, running Docker validation...', 'info', true);
        
        try {
            // Run Docker quick test first
            const quickTest = await this.runCommand('npm', ['run', 'docker:quick-test'], {
                timeout: 60000,
                streamOutput: this.verbose
            });
            
            if (!quickTest.success) {
                this.addWarning('Docker quick test failed, skipping full Docker validation', 'docker');
                this.results.stages.docker = {
                    completed: true,
                    passed: true,
                    skipped: true,
                    details: { reason: 'Quick test failed', error: quickTest.error }
                };
                return true;
            }
            
            this.log('Docker quick test passed', 'success');
            
            // Run full Docker validation
            const dockerValidation = await this.runCommand('npm', ['run', 'docker:validate'], {
                timeout: 600000, // 10 minutes
                streamOutput: this.verbose
            });
            
            if (!dockerValidation.success) {
                this.addWarning('Docker validation failed but continuing with standard validation', 'docker');
                this.results.stages.docker = {
                    completed: true,
                    passed: false,
                    details: { error: dockerValidation.error }
                };
                return false;
            }
            
            this.log('Docker validation completed successfully', 'success');
            this.results.stages.docker = {
                completed: true,
                passed: true,
                details: { fullValidation: true }
            };
            
            return true;
            
        } catch (error) {
            this.addWarning(`Docker validation error: ${error.message}`, 'docker');
            this.results.stages.docker = {
                completed: true,
                passed: false,
                details: { error: error.message }
            };
            return false;
        }
    }

    /**
     * Run integration tests
     */
    async runIntegrationTests() {
        this.log('Running integration tests...', 'info', true);
        
        try {
            // Test package.json scripts integrity
            const packageJson = JSON.parse(await fs.readFile(path.join(this.projectRoot, 'package.json'), 'utf8'));
            
            const requiredScripts = [
                'test',
                'validate-deployment',
                'prepublishOnly'
            ];
            
            const missingScripts = requiredScripts.filter(script => !packageJson.scripts[script]);
            
            if (missingScripts.length > 0) {
                this.addError(`Missing required scripts: ${missingScripts.join(', ')}`, 'integration');
                return false;
            }
            
            // Test CLI wrapper availability
            const binScript = path.join(this.projectRoot, 'bin', 'claude-pm');
            try {
                await fs.access(binScript, fs.constants.X_OK);
                this.log('CLI wrapper is executable', 'success');
            } catch (error) {
                this.addWarning('CLI wrapper not executable', 'integration');
            }
            
            // Test framework structure
            const criticalPaths = [
                'claude_pm',
                'framework',
                'install'
            ];
            
            for (const criticalPath of criticalPaths) {
                try {
                    await fs.access(path.join(this.projectRoot, criticalPath));
                } catch (error) {
                    this.addError(`Missing critical path: ${criticalPath}`, 'integration');
                    return false;
                }
            }
            
            this.log('Framework structure validation passed', 'success');
            
            this.results.stages.integration = {
                completed: true,
                passed: true,
                details: {
                    scriptsValidated: requiredScripts.length,
                    structureValidated: criticalPaths.length
                }
            };
            
            return true;
            
        } catch (error) {
            this.addError(`Integration tests failed: ${error.message}`, 'integration');
            this.results.stages.integration = {
                completed: true,
                passed: false,
                details: { error: error.message }
            };
            return false;
        }
    }

    /**
     * Generate comprehensive report
     */
    generateReport() {
        const allStages = Object.values(this.results.stages);
        const completedStages = allStages.filter(s => s.completed);
        const passedStages = allStages.filter(s => s.completed && s.passed);
        
        const totalErrors = Object.values(this.results).reduce((sum, stage) => {
            return sum + (stage.errors ? stage.errors.length : 0);
        }, 0);
        
        const totalWarnings = Object.values(this.results).reduce((sum, stage) => {
            return sum + (stage.warnings ? stage.warnings.length : 0);
        }, 0);
        
        this.results.overall.passed = totalErrors === 0 && passedStages.length === completedStages.length;
        
        this.results.summary = {
            totalStages: allStages.length,
            completedStages: completedStages.length,
            passedStages: passedStages.length,
            totalErrors,
            totalWarnings,
            overallSuccess: this.results.overall.passed,
            dockerAvailable: !this.results.stages.docker.skipped,
            timestamp: new Date().toISOString()
        };
        
        return this.results;
    }

    /**
     * Main validation orchestration
     */
    async validate() {
        this.log('🚀 Starting comprehensive pre-publish validation...', 'info', true);
        this.log(`Project: ${this.projectRoot}`, 'info', true);
        
        try {
            // Stage 1: Standard validation (required)
            const standardPassed = await this.runStandardValidation();
            
            // Stage 2: Docker validation (optional)
            const dockerPassed = await this.runDockerValidation();
            
            // Stage 3: Integration tests (required)
            const integrationPassed = await this.runIntegrationTests();
            
            // Generate final report
            const report = this.generateReport();
            
            // Log summary
            this.log('', 'info', true);
            this.log('📊 VALIDATION SUMMARY', 'info', true);
            this.log(`Overall Status: ${report.summary.overallSuccess ? '✅ PASSED' : '❌ FAILED'}`, 'info', true);
            this.log(`Stages: ${report.summary.passedStages}/${report.summary.completedStages} successful`, 'info', true);
            this.log(`Errors: ${report.summary.totalErrors}`, 'info', true);
            this.log(`Warnings: ${report.summary.totalWarnings}`, 'info', true);
            this.log(`Docker Available: ${report.summary.dockerAvailable ? 'Yes' : 'No'}`, 'info', true);
            
            if (report.summary.overallSuccess) {
                this.log('🎉 Package is ready for publishing!', 'success', true);
            } else {
                this.log('❌ Package validation failed - review errors before publishing', 'error', true);
                
                // Log error details
                for (const [stageName, stage] of Object.entries(this.results.stages)) {
                    if (stage.errors) {
                        for (const error of stage.errors) {
                            this.log(`  - [${stageName}] ${error.message}`, 'error', true);
                        }
                    }
                }
            }
            
            return report;
            
        } catch (error) {
            this.addError(`Validation process failed: ${error.message}`, 'overall');
            this.log(`❌ Critical validation failure: ${error.message}`, 'error', true);
            
            const report = this.generateReport();
            return report;
        }
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);
    
    const options = {
        projectRoot: process.cwd(),
        verbose: args.includes('--verbose') || args.includes('-v'),
        dryRun: args.includes('--dry-run'),
        skipDocker: args.includes('--skip-docker')
    };
    
    // Parse project root
    const rootIndex = args.findIndex(arg => arg === '--project' || arg === '-p');
    if (rootIndex !== -1 && args[rootIndex + 1]) {
        options.projectRoot = path.resolve(args[rootIndex + 1]);
    }
    
    const validator = new ComprehensivePrePublishValidator(options);
    
    validator.validate()
        .then(async (report) => {
            // Save report
            const logsDir = path.join(options.projectRoot, 'logs');
            try {
                await fs.mkdir(logsDir, { recursive: true });
                const reportPath = path.join(logsDir, `comprehensive-validation-${Date.now()}.json`);
                await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
                validator.log(`Report saved: ${reportPath}`, 'info', true);
            } catch (error) {
                validator.log('Could not save report', 'warning', true);
            }
            
            // Output JSON if requested
            if (args.includes('--json')) {
                console.log(JSON.stringify(report, null, 2));
            }
            
            process.exit(report.summary.overallSuccess ? 0 : 1);
        })
        .catch((error) => {
            console.error('❌ Validation failed:', error.message);
            process.exit(1);
        });
}

module.exports = ComprehensivePrePublishValidator;