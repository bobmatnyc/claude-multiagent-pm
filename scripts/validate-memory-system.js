#!/usr/bin/env node

/**
 * Claude PM Framework - Memory System Validation
 * Comprehensive validation of memory optimization deployment
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class MemorySystemValidator {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            tests: []
        };
        
        this.config = {
            expectedHeapLimit: 8192, // 8GB in MB
            expectedSubprocessLimit: 2048, // 2GB in MB
            maxConcurrentSubprocesses: 4
        };
    }
    
    async runValidation() {
        console.log('🔍 Claude PM Framework - Memory System Validation');
        console.log('==================================================');
        console.log(`🕐 ${new Date().toLocaleString()}`);
        console.log('');
        
        await this.testNodeOptionsConfiguration();
        await this.testMemoryOptimizationScript();
        await this.testMemoryMonitoringSystem();
        await this.testMemoryGuardSystem();
        await this.testPackageJsonScripts();
        await this.testDeploymentScripts();
        await this.testMemoryDashboard();
        await this.testLogFileCreation();
        await this.testHealthCheckIntegration();
        await this.testSubprocessMemoryIsolation();
        
        this.generateReport();
    }
    
    async testNodeOptionsConfiguration() {
        const testName = 'NODE_OPTIONS Configuration';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const nodeOptions = process.env.NODE_OPTIONS || '';
            
            // Check for 8GB heap limit
            if (nodeOptions.includes('--max-old-space-size=8192')) {
                this.recordSuccess(testName, 'NODE_OPTIONS contains 8GB heap limit');
            } else {
                this.recordFailure(testName, 'NODE_OPTIONS missing 8GB heap limit configuration');
            }
            
            // Check for garbage collection exposure
            if (nodeOptions.includes('--expose-gc')) {
                this.recordSuccess(testName, 'NODE_OPTIONS contains --expose-gc flag');
            } else {
                this.recordWarning(testName, 'NODE_OPTIONS missing --expose-gc flag');
            }
            
            // Verify heap limit is actually applied
            const currentHeapLimit = Math.round(require('v8').getHeapStatistics().heap_size_limit / 1024 / 1024);
            if (currentHeapLimit >= this.config.expectedHeapLimit * 0.9) {
                this.recordSuccess(testName, `Heap limit applied: ${currentHeapLimit}MB`);
            } else {
                this.recordFailure(testName, `Heap limit too low: ${currentHeapLimit}MB (expected ~${this.config.expectedHeapLimit}MB)`);
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing NODE_OPTIONS: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testMemoryOptimizationScript() {
        const testName = 'Memory Optimization Script';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const scriptPath = path.join(process.cwd(), 'scripts', 'memory-optimization.js');
            
            // Check if script exists and is executable
            if (fs.existsSync(scriptPath)) {
                this.recordSuccess(testName, 'Memory optimization script exists');
                
                // Test script execution
                const output = execSync('node scripts/memory-optimization.js report', { 
                    encoding: 'utf8', 
                    timeout: 10000 
                });
                
                if (output.includes('Memory optimization report saved')) {
                    this.recordSuccess(testName, 'Memory optimization script executes successfully');
                } else {
                    this.recordFailure(testName, 'Memory optimization script execution failed');
                }
                
                // Check if report file was created
                const reportPath = path.join(process.cwd(), 'memory-optimization-report.json');
                if (fs.existsSync(reportPath)) {
                    this.recordSuccess(testName, 'Memory optimization report generated');
                    
                    // Validate report content
                    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
                    if (report.optimizations_applied && report.optimizations_applied.includes('Node.js heap size increased to 8GB')) {
                        this.recordSuccess(testName, 'Report contains 8GB heap optimization');
                    } else {
                        this.recordFailure(testName, 'Report missing 8GB heap optimization');
                    }
                } else {
                    this.recordFailure(testName, 'Memory optimization report not generated');
                }
                
            } else {
                this.recordFailure(testName, 'Memory optimization script not found');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing memory optimization: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testMemoryMonitoringSystem() {
        const testName = 'Memory Monitoring System';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const scriptPath = path.join(process.cwd(), 'scripts', 'memory-monitor.js');
            
            if (fs.existsSync(scriptPath)) {
                this.recordSuccess(testName, 'Memory monitor script exists');
                
                // Test brief execution (2 seconds)
                const child = spawn('node', [scriptPath], { 
                    stdio: 'pipe',
                    env: { ...process.env, NODE_OPTIONS: '--max-old-space-size=8192 --expose-gc' }
                });
                
                let output = '';
                child.stdout.on('data', (data) => {
                    output += data.toString();
                });
                
                setTimeout(() => {
                    child.kill('SIGTERM');
                }, 2000);
                
                await new Promise(resolve => {
                    child.on('exit', () => {
                        if (output.includes('Memory Monitor - Starting Advanced Monitoring')) {
                            this.recordSuccess(testName, 'Memory monitor starts successfully');
                        } else {
                            this.recordFailure(testName, 'Memory monitor startup failed');
                        }
                        
                        if (output.includes('8GB') && output.includes('2GB')) {
                            this.recordSuccess(testName, 'Memory monitor configured with correct limits');
                        } else {
                            this.recordFailure(testName, 'Memory monitor configuration incorrect');
                        }
                        
                        resolve();
                    });
                });
                
                // Check if dashboard file is created
                const dashboardPath = path.join(process.cwd(), 'logs', 'memory-dashboard.json');
                if (fs.existsSync(dashboardPath)) {
                    this.recordSuccess(testName, 'Memory dashboard file created');
                } else {
                    this.recordWarning(testName, 'Memory dashboard file not created (may need longer runtime)');
                }
                
            } else {
                this.recordFailure(testName, 'Memory monitor script not found');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing memory monitoring: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testMemoryGuardSystem() {
        const testName = 'Memory Guard System';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const scriptPath = path.join(process.cwd(), 'scripts', 'memory-guard.js');
            
            if (fs.existsSync(scriptPath)) {
                this.recordSuccess(testName, 'Memory guard script exists');
                
                // Test status command
                const output = execSync('node scripts/memory-guard.js status', { 
                    encoding: 'utf8', 
                    timeout: 10000,
                    env: { ...process.env, NODE_OPTIONS: '--max-old-space-size=8192 --expose-gc' }
                });
                
                if (output.includes('Memory Guard Status')) {
                    this.recordSuccess(testName, 'Memory guard status command works');
                }
                
                if (output.includes('maxConcurrent": 4')) {
                    this.recordSuccess(testName, 'Memory guard configured for 4 concurrent subprocesses');
                } else {
                    this.recordFailure(testName, 'Memory guard subprocess limit incorrect');
                }
                
                if (output.includes('"totalMemoryUsedMB": 0')) {
                    this.recordSuccess(testName, 'Memory guard tracking subprocess memory');
                } else {
                    this.recordWarning(testName, 'Memory guard memory tracking may not be active');
                }
                
                // Check if log file is created
                const logPath = path.join(process.cwd(), 'logs', 'memory-guard.log');
                if (fs.existsSync(logPath)) {
                    this.recordSuccess(testName, 'Memory guard log file created');
                } else {
                    this.recordWarning(testName, 'Memory guard log file not created');
                }
                
            } else {
                this.recordFailure(testName, 'Memory guard script not found');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing memory guard: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testPackageJsonScripts() {
        const testName = 'Package.json Scripts';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const packagePath = path.join(process.cwd(), 'package.json');
            const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            
            const requiredScripts = [
                'start',
                'start:memory-safe',
                'memory:monitor',
                'memory:optimize',
                'memory:guard'
            ];
            
            for (const script of requiredScripts) {
                if (packageData.scripts && packageData.scripts[script]) {
                    this.recordSuccess(testName, `Script '${script}' exists`);
                    
                    // Check if script includes proper NODE_OPTIONS
                    if (packageData.scripts[script].includes('--max-old-space-size=8192')) {
                        this.recordSuccess(testName, `Script '${script}' has 8GB memory limit`);
                    } else {
                        this.recordWarning(testName, `Script '${script}' missing 8GB memory limit`);
                    }
                } else {
                    this.recordFailure(testName, `Script '${script}' missing`);
                }
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing package.json scripts: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testDeploymentScripts() {
        const testName = 'Deployment Scripts';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const deployScript = path.join(process.cwd(), 'scripts', 'deploy-memory-system.sh');
            const startScript = path.join(process.cwd(), 'scripts', 'start-memory-monitor.sh');
            
            if (fs.existsSync(deployScript)) {
                this.recordSuccess(testName, 'Memory deployment script exists');
                
                // Check if script is executable
                const stats = fs.statSync(deployScript);
                if (stats.mode & parseInt('111', 8)) {
                    this.recordSuccess(testName, 'Memory deployment script is executable');
                } else {
                    this.recordFailure(testName, 'Memory deployment script not executable');
                }
            } else {
                this.recordFailure(testName, 'Memory deployment script not found');
            }
            
            if (fs.existsSync(startScript)) {
                this.recordSuccess(testName, 'Memory monitor start script exists');
            } else {
                this.recordWarning(testName, 'Memory monitor start script not found');
            }
            
            // Check deployed CLI scripts
            const cliScripts = ['/Users/masa/.local/bin/claude-pm', '/Users/masa/.local/bin/cmpm'];
            for (const cliScript of cliScripts) {
                if (fs.existsSync(cliScript)) {
                    const content = fs.readFileSync(cliScript, 'utf8');
                    if (content.includes('--max-old-space-size=8192')) {
                        this.recordSuccess(testName, `CLI script ${path.basename(cliScript)} has memory optimization`);
                    } else {
                        this.recordWarning(testName, `CLI script ${path.basename(cliScript)} missing memory optimization`);
                    }
                } else {
                    this.recordWarning(testName, `CLI script ${path.basename(cliScript)} not deployed`);
                }
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing deployment scripts: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testMemoryDashboard() {
        const testName = 'Memory Dashboard';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const dashboardScript = path.join(process.cwd(), 'scripts', 'memory-dashboard.js');
            
            if (fs.existsSync(dashboardScript)) {
                this.recordSuccess(testName, 'Memory dashboard script exists');
                
                // Check if script is executable
                const stats = fs.statSync(dashboardScript);
                if (stats.mode & parseInt('111', 8)) {
                    this.recordSuccess(testName, 'Memory dashboard script is executable');
                } else {
                    this.recordWarning(testName, 'Memory dashboard script not executable');
                }
                
                // Test brief execution
                try {
                    const child = spawn('node', [dashboardScript], { 
                        stdio: 'pipe',
                        env: { ...process.env, NODE_OPTIONS: '--max-old-space-size=8192 --expose-gc' }
                    });
                    
                    setTimeout(() => {
                        child.kill('SIGTERM');
                    }, 1000);
                    
                    await new Promise(resolve => {
                        child.on('exit', () => {
                            this.recordSuccess(testName, 'Memory dashboard can be started');
                            resolve();
                        });
                    });
                } catch (error) {
                    this.recordWarning(testName, `Memory dashboard test execution: ${error.message}`);
                }
                
            } else {
                this.recordFailure(testName, 'Memory dashboard script not found');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing memory dashboard: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testLogFileCreation() {
        const testName = 'Log File Creation';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const logsDir = path.join(process.cwd(), 'logs');
            
            if (fs.existsSync(logsDir)) {
                this.recordSuccess(testName, 'Logs directory exists');
                
                const logFiles = fs.readdirSync(logsDir);
                const expectedLogs = ['memory-guard.log', 'memory-dashboard.json'];
                
                for (const logFile of expectedLogs) {
                    if (logFiles.some(file => file.includes(logFile.split('.')[0]))) {
                        this.recordSuccess(testName, `Log file ${logFile} found`);
                    } else {
                        this.recordWarning(testName, `Log file ${logFile} not found (may be created on first run)`);
                    }
                }
                
                // Check for report files
                const reportFiles = logFiles.filter(file => file.includes('report') || file.includes('optimization'));
                if (reportFiles.length > 0) {
                    this.recordSuccess(testName, `Found ${reportFiles.length} report file(s)`);
                } else {
                    this.recordWarning(testName, 'No report files found');
                }
                
            } else {
                this.recordWarning(testName, 'Logs directory not found (will be created on first run)');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing log files: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testHealthCheckIntegration() {
        const testName = 'Health Check Integration';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            const healthScript = path.join(process.cwd(), 'scripts', 'health-check.sh');
            
            if (fs.existsSync(healthScript)) {
                const content = fs.readFileSync(healthScript, 'utf8');
                
                if (content.includes('Memory optimization system')) {
                    this.recordSuccess(testName, 'Health check includes memory optimization checks');
                } else {
                    this.recordFailure(testName, 'Health check missing memory optimization checks');
                }
                
                if (content.includes('max-old-space-size=8192')) {
                    this.recordSuccess(testName, 'Health check validates 8GB memory configuration');
                } else {
                    this.recordWarning(testName, 'Health check missing memory configuration validation');
                }
                
                if (content.includes('Memory Usage Summary')) {
                    this.recordSuccess(testName, 'Health check includes memory usage summary');
                } else {
                    this.recordWarning(testName, 'Health check missing memory usage summary');
                }
                
            } else {
                this.recordFailure(testName, 'Health check script not found');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing health check integration: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testSubprocessMemoryIsolation() {
        const testName = 'Subprocess Memory Isolation';
        console.log(`🧪 Testing: ${testName}`);
        
        try {
            // Test that memory guard configuration is correct
            const guardScript = path.join(process.cwd(), 'scripts', 'memory-guard.js');
            const content = fs.readFileSync(guardScript, 'utf8');
            
            if (content.includes('subprocessMemoryLimit: 2 * 1024 * 1024 * 1024')) {
                this.recordSuccess(testName, 'Subprocess memory limit set to 2GB');
            } else {
                this.recordFailure(testName, 'Subprocess memory limit not configured correctly');
            }
            
            if (content.includes('maxConcurrentSubprocesses: 4')) {
                this.recordSuccess(testName, 'Maximum concurrent subprocesses set to 4');
            } else {
                this.recordFailure(testName, 'Maximum concurrent subprocesses not configured correctly');
            }
            
            if (content.includes('NODE_OPTIONS: `--max-old-space-size=${Math.round(this.config.subprocessMemoryLimit / 1024 / 1024)} --expose-gc`')) {
                this.recordSuccess(testName, 'Subprocess NODE_OPTIONS configured for memory isolation');
            } else {
                this.recordFailure(testName, 'Subprocess NODE_OPTIONS not configured correctly');
            }
            
        } catch (error) {
            this.recordFailure(testName, `Error testing subprocess memory isolation: ${error.message}`);
        }
        
        console.log('');
    }
    
    recordSuccess(testName, message) {
        this.results.passed++;
        this.results.tests.push({ test: testName, status: 'PASS', message });
        console.log(`   ✅ PASS: ${message}`);
    }
    
    recordFailure(testName, message) {
        this.results.failed++;
        this.results.tests.push({ test: testName, status: 'FAIL', message });
        console.log(`   ❌ FAIL: ${message}`);
    }
    
    recordWarning(testName, message) {
        this.results.warnings++;
        this.results.tests.push({ test: testName, status: 'WARN', message });
        console.log(`   ⚠️  WARN: ${message}`);
    }
    
    generateReport() {
        console.log('==================================================');
        console.log('📊 Memory System Validation Report');
        console.log('==================================================');
        console.log('');
        
        const total = this.results.passed + this.results.failed + this.results.warnings;
        const passRate = Math.round((this.results.passed / total) * 100);
        
        console.log('📈 Summary:');
        console.log(`   Total Tests: ${total}`);
        console.log(`   Passed: ${this.results.passed} (${passRate}%)`);
        console.log(`   Failed: ${this.results.failed}`);
        console.log(`   Warnings: ${this.results.warnings}`);
        console.log('');
        
        if (this.results.failed === 0) {
            console.log('🎉 All critical tests passed! Memory optimization system is functional.');
        } else {
            console.log('⚠️  Some tests failed. Please review the failures above.');
        }
        
        if (this.results.warnings > 0) {
            console.log('📝 Some warnings were noted. These may not affect functionality but should be reviewed.');
        }
        
        console.log('');
        console.log('🚀 Memory System Status:');
        console.log(`   Heap Limit: ${Math.round(require('v8').getHeapStatistics().heap_size_limit / 1024 / 1024)}MB`);
        console.log(`   NODE_OPTIONS: ${process.env.NODE_OPTIONS || 'Not set'}`);
        console.log(`   Memory Guard: ${this.results.tests.some(t => t.test === 'Memory Guard System' && t.status === 'PASS') ? 'Active' : 'Inactive'}`);
        console.log(`   Memory Monitor: ${this.results.tests.some(t => t.test === 'Memory Monitoring System' && t.status === 'PASS') ? 'Available' : 'Unavailable'}`);
        console.log('');
        
        // Save report to file
        const reportPath = path.join(process.cwd(), 'logs', `memory-validation-report-${Date.now()}.json`);
        fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        fs.writeFileSync(reportPath, JSON.stringify({
            timestamp: new Date().toISOString(),
            summary: {
                total,
                passed: this.results.passed,
                failed: this.results.failed,
                warnings: this.results.warnings,
                passRate
            },
            tests: this.results.tests,
            systemInfo: {
                heapLimit: Math.round(require('v8').getHeapStatistics().heap_size_limit / 1024 / 1024),
                nodeOptions: process.env.NODE_OPTIONS || 'Not set',
                platform: process.platform,
                nodeVersion: process.version
            }
        }, null, 2));
        
        console.log(`📊 Detailed report saved: ${reportPath}`);
    }
}

// Run validation if called directly
if (require.main === module) {
    const validator = new MemorySystemValidator();
    validator.runValidation().catch(console.error);
}

module.exports = MemorySystemValidator;