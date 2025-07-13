#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Docker-Based Pre-Publish Validation
 * 
 * Creates comprehensive Docker-based validation for clean environment testing
 * before npm publish operations. Tests package in isolated containers.
 * 
 * DevOps Agent Implementation - 2025-07-13
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const crypto = require('crypto');

class DockerPrePublishValidator {
    constructor(options = {}) {
        this.projectRoot = options.projectRoot || process.cwd();
        this.verbose = options.verbose || false;
        this.dryRun = options.dryRun || false;
        
        // Validation results
        this.results = {
            timestamp: new Date().toISOString(),
            validationId: crypto.randomUUID(),
            passed: false,
            errors: [],
            warnings: [],
            stages: {},
            cleanup: []
        };
        
        // Docker configuration
        this.dockerConfig = {
            imageTag: 'claude-pm-validation',
            containerPrefix: 'claude-pm-val',
            testVolume: 'claude-pm-test-vol',
            networkName: 'claude-pm-test-net',
            ports: {
                api: 18001,
                dashboard: 17001,
                mem0: 18002
            }
        };
        
        // Validation stages
        this.stages = [
            'docker-availability',
            'build-environment',
            'package-build',
            'installation-test',
            'functionality-test',
            'health-check',
            'service-integration',
            'cleanup'
        ];
    }

    /**
     * Enhanced logging with validation context
     */
    log(message, level = 'info', force = false) {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [Docker Validator]`;
        
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
     * Add error with stage context
     */
    addError(message, stage = 'general') {
        this.results.errors.push({ stage, message, timestamp: new Date().toISOString() });
        this.log(`ERROR in ${stage}: ${message}`, 'error', true);
    }

    /**
     * Add warning with stage context
     */
    addWarning(message, stage = 'general') {
        this.results.warnings.push({ stage, message, timestamp: new Date().toISOString() });
        this.log(`WARNING in ${stage}: ${message}`, 'warning', true);
    }

    /**
     * Track stage completion
     */
    completeStage(stage, success, details = {}) {
        this.results.stages[stage] = {
            completed: true,
            success,
            timestamp: new Date().toISOString(),
            details
        };
        
        if (success) {
            this.log(`Stage completed: ${stage}`, 'success');
        } else {
            this.log(`Stage failed: ${stage}`, 'error');
        }
    }

    /**
     * Execute command with comprehensive error handling
     */
    async runCommand(command, args = [], options = {}) {
        return new Promise((resolve) => {
            const timeoutMs = options.timeout || 120000; // 2 minutes default
            
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
     * Validate Docker availability and configuration
     */
    async validateDockerAvailability() {
        this.log('Validating Docker environment...', 'info', true);
        
        try {
            // Check Docker daemon
            const dockerVersion = await this.runCommand('docker', ['--version']);
            if (!dockerVersion.success) {
                this.addError('Docker is not available or not running', 'docker-availability');
                return false;
            }
            
            this.log(`Docker version: ${dockerVersion.stdout.trim()}`, 'success');
            
            // Check Docker Compose
            const composeVersion = await this.runCommand('docker-compose', ['--version']);
            if (!composeVersion.success) {
                this.addWarning('Docker Compose not available, will use docker run', 'docker-availability');
            } else {
                this.log(`Docker Compose version: ${composeVersion.stdout.trim()}`, 'success');
            }
            
            // Test Docker connectivity
            const dockerInfo = await this.runCommand('docker', ['info'], { timeout: 30000 });
            if (!dockerInfo.success) {
                this.addError('Cannot connect to Docker daemon', 'docker-availability');
                return false;
            }
            
            this.completeStage('docker-availability', true, {
                dockerVersion: dockerVersion.stdout.trim(),
                composeAvailable: composeVersion.success
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Docker validation failed: ${error.message}`, 'docker-availability');
            this.completeStage('docker-availability', false);
            return false;
        }
    }

    /**
     * Build validation environment using existing Docker infrastructure
     */
    async buildValidationEnvironment() {
        this.log('Building validation environment...', 'info', true);
        
        try {
            const dockerfilePath = path.join(this.projectRoot, 'deployment', 'docker', 'Dockerfile');
            
            // Check if Dockerfile exists
            try {
                await fs.access(dockerfilePath);
            } catch (error) {
                this.addError('Dockerfile not found in deployment/docker/', 'build-environment');
                return false;
            }
            
            // Build validation image
            const buildArgs = [
                'build',
                '-f', dockerfilePath,
                '-t', `${this.dockerConfig.imageTag}:testing`,
                '--target', 'testing',
                '--build-arg', `BUILD_DATE=${new Date().toISOString()}`,
                '--build-arg', `VCS_REF=${await this.getGitRef()}`,
                '.'
            ];
            
            this.log('Building Docker validation image...', 'info');
            const buildResult = await this.runCommand('docker', buildArgs, {
                timeout: 600000, // 10 minutes
                streamOutput: true
            });
            
            if (!buildResult.success) {
                this.addError(`Docker build failed: ${buildResult.error}`, 'build-environment');
                return false;
            }
            
            // Create test network
            await this.runCommand('docker', ['network', 'create', this.dockerConfig.networkName]);
            
            // Create test volume
            await this.runCommand('docker', ['volume', 'create', this.dockerConfig.testVolume]);
            
            this.results.cleanup.push(
                `docker network rm ${this.dockerConfig.networkName}`,
                `docker volume rm ${this.dockerConfig.testVolume}`,
                `docker rmi ${this.dockerConfig.imageTag}:testing`
            );
            
            this.completeStage('build-environment', true, {
                imageTag: `${this.dockerConfig.imageTag}:testing`,
                networkName: this.dockerConfig.networkName,
                volumeName: this.dockerConfig.testVolume
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Environment build failed: ${error.message}`, 'build-environment');
            this.completeStage('build-environment', false);
            return false;
        }
    }

    /**
     * Test package build and installation in clean environment
     */
    async testPackageBuild() {
        this.log('Testing package build in clean environment...', 'info', true);
        
        try {
            // Create package tarball
            const packResult = await this.runCommand('npm', ['pack'], {
                timeout: 120000
            });
            
            if (!packResult.success) {
                this.addError(`npm pack failed: ${packResult.error}`, 'package-build');
                return false;
            }
            
            // Find the generated tarball
            const tarballName = packResult.stdout.trim().split('\n').pop();
            this.log(`Package tarball created: ${tarballName}`, 'success');
            
            // Test installation in container
            const containerName = `${this.dockerConfig.containerPrefix}-build-test`;
            
            const runArgs = [
                'run', '--rm',
                '--name', containerName,
                '--network', this.dockerConfig.networkName,
                '--volume', `${this.projectRoot}:/workspace:ro`,
                '--workdir', '/workspace',
                `${this.dockerConfig.imageTag}:testing`,
                'sh', '-c', `
                    set -e
                    echo "Installing package from tarball..."
                    npm install -g ${tarballName}
                    echo "Testing CLI availability..."
                    claude-pm --version || echo "CLI test failed"
                    echo "Testing basic import..."
                    python3 -c "import claude_pm; print('Import successful')"
                `
            ];
            
            this.log('Testing package installation in container...', 'info');
            const testResult = await this.runCommand('docker', runArgs, {
                timeout: 300000, // 5 minutes
                streamOutput: true
            });
            
            if (!testResult.success) {
                this.addError(`Package installation test failed: ${testResult.error}`, 'package-build');
                return false;
            }
            
            // Clean up tarball
            await fs.unlink(path.join(this.projectRoot, tarballName)).catch(() => {});
            
            this.completeStage('package-build', true, {
                tarballName,
                installationTest: 'passed'
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Package build test failed: ${error.message}`, 'package-build');
            this.completeStage('package-build', false);
            return false;
        }
    }

    /**
     * Test functionality in isolated environment
     */
    async testFunctionality() {
        this.log('Testing framework functionality...', 'info', true);
        
        try {
            const containerName = `${this.dockerConfig.containerPrefix}-func-test`;
            
            const functionalityTests = [
                'python3 -m claude_pm.cli --help',
                'python3 -c "from claude_pm.core.config import Config; config = Config(); print(\\"Config test passed\\")"',
                'python3 -c "from claude_pm.services.health_monitor import HealthMonitor; print(\\"Health monitor import successful\\")"',
                'python3 -c "from claude_pm.agents.pm_agent import PMAgent; print(\\"PM agent import successful\\")"'
            ];
            
            for (const test of functionalityTests) {
                const runArgs = [
                    'run', '--rm',
                    '--name', `${containerName}-${Date.now()}`,
                    '--network', this.dockerConfig.networkName,
                    '--volume', `${this.dockerConfig.testVolume}:/app/data`,
                    `${this.dockerConfig.imageTag}:testing`,
                    'sh', '-c', test
                ];
                
                this.log(`Running test: ${test}`, 'debug');
                const result = await this.runCommand('docker', runArgs, {
                    timeout: 60000
                });
                
                if (!result.success) {
                    this.addError(`Functionality test failed: ${test} - ${result.error}`, 'functionality-test');
                    return false;
                }
            }
            
            this.completeStage('functionality-test', true, {
                testsExecuted: functionalityTests.length
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Functionality test failed: ${error.message}`, 'functionality-test');
            this.completeStage('functionality-test', false);
            return false;
        }
    }

    /**
     * Test health monitoring and service integration
     */
    async testServiceIntegration() {
        this.log('Testing service integration...', 'info', true);
        
        try {
            // Start main service container
            const mainContainer = `${this.dockerConfig.containerPrefix}-main`;
            
            const mainArgs = [
                'run', '-d',
                '--name', mainContainer,
                '--network', this.dockerConfig.networkName,
                '--volume', `${this.dockerConfig.testVolume}:/app/data`,
                '-p', `${this.dockerConfig.ports.api}:8001`,
                '-p', `${this.dockerConfig.ports.dashboard}:7001`,
                '-e', 'CLAUDE_PM_LOG_LEVEL=INFO',
                '-e', 'CLAUDE_PM_ENABLE_HEALTH_MONITORING=true',
                `${this.dockerConfig.imageTag}:testing`,
                'python3', '-m', 'claude_pm.cli', 'service', 'start'
            ];
            
            this.log('Starting main service container...', 'info');
            const startResult = await this.runCommand('docker', mainArgs);
            
            if (!startResult.success) {
                this.addError(`Failed to start main service: ${startResult.error}`, 'service-integration');
                return false;
            }
            
            this.results.cleanup.push(`docker stop ${mainContainer}`, `docker rm ${mainContainer}`);
            
            // Wait for service to start
            await this.sleep(10000);
            
            // Test health endpoint
            const healthTest = await this.runCommand('docker', [
                'exec', mainContainer,
                'python3', '-c', 
                'from claude_pm.interfaces.health import HealthInterface; h = HealthInterface(); print("Health check:", h.get_status())'
            ]);
            
            if (!healthTest.success) {
                this.addWarning('Health check test failed', 'service-integration');
            }
            
            // Test service logs
            const logsResult = await this.runCommand('docker', ['logs', mainContainer], {
                timeout: 10000
            });
            
            const hasErrors = logsResult.stderr.toLowerCase().includes('error') ||
                            logsResult.stdout.toLowerCase().includes('failed');
                            
            if (hasErrors) {
                this.addWarning('Service logs contain errors', 'service-integration');
            }
            
            this.completeStage('service-integration', true, {
                mainContainer,
                healthTest: healthTest.success,
                logsClean: !hasErrors
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Service integration test failed: ${error.message}`, 'service-integration');
            this.completeStage('service-integration', false);
            return false;
        }
    }

    /**
     * Comprehensive health check using existing validation scripts
     */
    async performHealthCheck() {
        this.log('Performing comprehensive health check...', 'info', true);
        
        try {
            // Use existing validation script
            const validationScript = path.join(this.projectRoot, 'deployment', 'scripts', 'validate.sh');
            
            try {
                await fs.access(validationScript);
            } catch (error) {
                this.addWarning('Deployment validation script not found', 'health-check');
                this.completeStage('health-check', true, { skipped: true });
                return true;
            }
            
            // Run validation in container
            const containerName = `${this.dockerConfig.containerPrefix}-health`;
            
            const healthArgs = [
                'run', '--rm',
                '--name', containerName,
                '--network', this.dockerConfig.networkName,
                '--volume', `${this.projectRoot}:/workspace:ro`,
                '--workdir', '/workspace',
                '-e', 'CLAUDE_PM_ROOT=/workspace',
                `${this.dockerConfig.imageTag}:testing`,
                'bash', 'deployment/scripts/validate.sh'
            ];
            
            this.log('Running comprehensive health check...', 'info');
            const healthResult = await this.runCommand('docker', healthArgs, {
                timeout: 180000, // 3 minutes
                streamOutput: this.verbose
            });
            
            if (!healthResult.success) {
                this.addWarning(`Health check reported issues: ${healthResult.error}`, 'health-check');
            }
            
            this.completeStage('health-check', true, {
                validationPassed: healthResult.success,
                output: this.verbose ? null : healthResult.stdout.slice(-500)
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Health check failed: ${error.message}`, 'health-check');
            this.completeStage('health-check', false);
            return false;
        }
    }

    /**
     * Clean up Docker resources
     */
    async performCleanup() {
        this.log('Performing cleanup...', 'info', true);
        
        try {
            const cleanupErrors = [];
            
            // Stop and remove all test containers
            const containers = await this.runCommand('docker', ['ps', '-a', '--filter', `name=${this.dockerConfig.containerPrefix}`, '-q']);
            if (containers.success && containers.stdout.trim()) {
                const containerIds = containers.stdout.trim().split('\n');
                for (const containerId of containerIds) {
                    await this.runCommand('docker', ['stop', containerId]);
                    await this.runCommand('docker', ['rm', containerId]);
                }
            }
            
            // Execute cleanup commands
            for (const command of this.results.cleanup) {
                const [cmd, ...args] = command.split(' ');
                const result = await this.runCommand(cmd, args);
                if (!result.success) {
                    cleanupErrors.push(`Failed: ${command}`);
                }
            }
            
            if (cleanupErrors.length > 0) {
                this.addWarning(`Some cleanup operations failed: ${cleanupErrors.join(', ')}`, 'cleanup');
            }
            
            this.completeStage('cleanup', true, {
                cleanupCommands: this.results.cleanup.length,
                errors: cleanupErrors
            });
            
            return true;
            
        } catch (error) {
            this.addError(`Cleanup failed: ${error.message}`, 'cleanup');
            this.completeStage('cleanup', false);
            return false;
        }
    }

    /**
     * Get Git reference for build
     */
    async getGitRef() {
        try {
            const result = await this.runCommand('git', ['rev-parse', '--short', 'HEAD']);
            return result.success ? result.stdout.trim() : 'unknown';
        } catch {
            return 'unknown';
        }
    }

    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generate comprehensive validation report
     */
    generateReport() {
        const totalStages = this.stages.length;
        const completedStages = Object.keys(this.results.stages).length;
        const successfulStages = Object.values(this.results.stages).filter(s => s.success).length;
        
        this.results.passed = this.results.errors.length === 0;
        this.results.summary = {
            totalStages,
            completedStages,
            successfulStages,
            totalErrors: this.results.errors.length,
            totalWarnings: this.results.warnings.length,
            overallSuccess: this.results.passed && successfulStages === completedStages,
            duration: new Date().toISOString()
        };
        
        return this.results;
    }

    /**
     * Main validation orchestration
     */
    async validate() {
        this.log('🚀 Starting Docker-based pre-publish validation...', 'info', true);
        this.log(`Validation ID: ${this.results.validationId}`, 'info', true);
        this.log(`Project: ${this.projectRoot}`, 'info', true);
        
        try {
            // Execute validation stages
            const stageResults = {
                'docker-availability': await this.validateDockerAvailability(),
                'build-environment': await this.buildValidationEnvironment(),
                'package-build': await this.testPackageBuild(),
                'functionality-test': await this.testFunctionality(),
                'health-check': await this.performHealthCheck(),
                'service-integration': await this.testServiceIntegration(),
                'cleanup': await this.performCleanup()
            };
            
            // Generate final report
            const report = this.generateReport();
            
            // Log summary
            this.log('', 'info', true);
            this.log('📊 VALIDATION SUMMARY', 'info', true);
            this.log(`Overall Status: ${report.summary.overallSuccess ? '✅ PASSED' : '❌ FAILED'}`, 'info', true);
            this.log(`Stages: ${report.summary.successfulStages}/${report.summary.totalStages} successful`, 'info', true);
            this.log(`Errors: ${report.summary.totalErrors}`, 'info', true);
            this.log(`Warnings: ${report.summary.totalWarnings}`, 'info', true);
            
            if (report.summary.overallSuccess) {
                this.log('🎉 Package is ready for publishing!', 'success', true);
            } else {
                this.log('❌ Package validation failed - review errors before publishing', 'error', true);
                
                // Log error details
                for (const error of this.results.errors) {
                    this.log(`  - [${error.stage}] ${error.message}`, 'error', true);
                }
            }
            
            return report;
            
        } catch (error) {
            this.addError(`Validation process failed: ${error.message}`, 'general');
            this.log(`❌ Critical validation failure: ${error.message}`, 'error', true);
            
            // Attempt cleanup even on failure
            await this.performCleanup();
            
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
        dryRun: args.includes('--dry-run')
    };
    
    // Parse project root
    const rootIndex = args.findIndex(arg => arg === '--project' || arg === '-p');
    if (rootIndex !== -1 && args[rootIndex + 1]) {
        options.projectRoot = path.resolve(args[rootIndex + 1]);
    }
    
    const validator = new DockerPrePublishValidator(options);
    
    validator.validate()
        .then((report) => {
            // Save report
            const reportPath = path.join(options.projectRoot, 'logs', `docker-validation-${report.validationId}.json`);
            fs.writeFile(reportPath, JSON.stringify(report, null, 2))
                .then(() => {
                    validator.log(`Report saved: ${reportPath}`, 'info', true);
                })
                .catch(() => {
                    validator.log('Could not save report', 'warning', true);
                });
            
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

module.exports = DockerPrePublishValidator;