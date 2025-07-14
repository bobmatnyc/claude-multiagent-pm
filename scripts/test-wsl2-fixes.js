#!/usr/bin/env node

/**
 * Claude PM Framework - WSL2 Fix Validation Script
 * Tests all WSL2-specific fixes and PATH configurations
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawn } = require('child_process');

class WSL2FixValidator {
    constructor() {
        this.testResults = [];
        this.packageRoot = path.join(__dirname, '..');
    }
    
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
    }
    
    addTestResult(test, passed, message) {
        this.testResults.push({ test, passed, message });
    }
    
    isWSL2Environment() {
        try {
            const isWSL = process.env.WSL_DISTRO_NAME || 
                         process.env.WSLENV ||
                         (process.platform === 'linux' && fs.existsSync('/proc/version'));
            
            if (!isWSL) return { isWSL2: false, reason: 'Not WSL environment' };
            
            if (fs.existsSync('/proc/version')) {
                const versionContent = fs.readFileSync('/proc/version', 'utf8');
                const isWSL2 = versionContent.includes('WSL2') || versionContent.includes('microsoft');
                return { 
                    isWSL2, 
                    reason: isWSL2 ? 'WSL2 detected' : 'WSL1 detected',
                    distro: process.env.WSL_DISTRO_NAME || 'Unknown'
                };
            }
            
            return { isWSL2: false, reason: 'Could not determine WSL version' };
        } catch (error) {
            return { isWSL2: false, reason: `Error detecting WSL: ${error.message}` };
        }
    }
    
    testWSL2Detection() {
        this.log('Testing WSL2 detection...', 'info');
        
        const wslInfo = this.isWSL2Environment();
        
        if (wslInfo.isWSL2) {
            this.log(`WSL2 detected: ${wslInfo.distro}`, 'success');
            this.addTestResult('WSL2 Detection', true, `${wslInfo.reason} - ${wslInfo.distro}`);
        } else {
            this.log(`Not WSL2: ${wslInfo.reason}`, 'warn');
            this.addTestResult('WSL2 Detection', false, wslInfo.reason);
        }
        
        return wslInfo.isWSL2;
    }
    
    testNpmGlobalBinDetection() {
        this.log('Testing npm global bin detection...', 'info');
        
        const methods = [
            {
                name: 'npm bin -g',
                cmd: 'npm bin -g'
            },
            {
                name: 'npm config get prefix',
                cmd: 'npm config get prefix',
                suffix: '/bin'
            },
            {
                name: 'NVM path construction',
                cmd: 'echo $HOME/.nvm/versions/node/$(node --version)/bin'
            }
        ];
        
        let globalBinFound = null;
        
        for (const method of methods) {
            try {
                let result = execSync(method.cmd, { encoding: 'utf8', timeout: 3000 }).trim();
                if (method.suffix) {
                    result += method.suffix;
                }
                
                if (result && fs.existsSync(result)) {
                    this.log(`${method.name}: ${result}`, 'success');
                    if (!globalBinFound) globalBinFound = result;
                    this.addTestResult(`NPM Global Bin (${method.name})`, true, result);
                } else {
                    this.log(`${method.name}: ${result} (not found)`, 'warn');
                    this.addTestResult(`NPM Global Bin (${method.name})`, false, `Path does not exist: ${result}`);
                }
            } catch (error) {
                this.log(`${method.name}: Error - ${error.message}`, 'error');
                this.addTestResult(`NPM Global Bin (${method.name})`, false, error.message);
            }
        }
        
        return globalBinFound;
    }
    
    testPATHConfiguration() {
        this.log('Testing PATH configuration...', 'info');
        
        const currentPath = process.env.PATH || '';
        const npmGlobalBin = this.testNpmGlobalBinDetection();
        
        if (npmGlobalBin) {
            const inPath = currentPath.includes(npmGlobalBin);
            if (inPath) {
                this.log(`npm global bin is in PATH: ${npmGlobalBin}`, 'success');
                this.addTestResult('PATH Configuration', true, `npm global bin found in PATH`);
            } else {
                this.log(`npm global bin NOT in PATH: ${npmGlobalBin}`, 'error');
                this.addTestResult('PATH Configuration', false, `${npmGlobalBin} not in PATH`);
            }
            return inPath;
        } else {
            this.log('Could not determine npm global bin directory', 'error');
            this.addTestResult('PATH Configuration', false, 'npm global bin directory not found');
            return false;
        }
    }
    
    testCommandAvailability() {
        this.log('Testing command availability...', 'info');
        
        const commands = [
            { name: 'node', required: true },
            { name: 'npm', required: true },
            { name: 'claude-pm', required: true },
            { name: 'aitrackdown', required: false },
            { name: 'claude', required: false }
        ];
        
        let allRequired = true;
        
        for (const cmd of commands) {
            try {
                execSync(`which ${cmd.name}`, { encoding: 'utf8', timeout: 3000 });
                try {
                    const version = execSync(`${cmd.name} --version`, { encoding: 'utf8', timeout: 3000 }).trim();
                    this.log(`${cmd.name}: ${version}`, 'success');
                    this.addTestResult(`Command Availability (${cmd.name})`, true, version);
                } catch (versionError) {
                    this.log(`${cmd.name}: Available but version check failed`, 'warn');
                    this.addTestResult(`Command Availability (${cmd.name})`, true, 'Available but version unknown');
                }
            } catch (error) {
                const level = cmd.required ? 'error' : 'warn';
                this.log(`${cmd.name}: Not found`, level);
                this.addTestResult(`Command Availability (${cmd.name})`, false, 'Command not found in PATH');
                if (cmd.required) allRequired = false;
            }
        }
        
        return allRequired;
    }
    
    testPostinstallWSL2Logic() {
        this.log('Testing postinstall WSL2 detection logic...', 'info');
        
        try {
            // Test the postinstall file exists and has WSL2 logic
            const postinstallPath = path.join(this.packageRoot, 'install', 'postinstall-minimal.js');
            
            if (!fs.existsSync(postinstallPath)) {
                this.log('Postinstall script not found', 'error');
                this.addTestResult('Postinstall WSL2 Logic', false, 'File not found');
                return false;
            }
            
            const postinstallContent = fs.readFileSync(postinstallPath, 'utf8');
            
            // Check for WSL2-specific patterns
            const wsl2Patterns = [
                'isWSL2Environment',
                'setupWSL2Environment',
                'getWSL2NpmGlobalBin',
                'configureWSL2Shell',
                'WSL2-specific'
            ];
            
            let foundPatterns = 0;
            for (const pattern of wsl2Patterns) {
                if (postinstallContent.includes(pattern)) {
                    foundPatterns++;
                    this.log(`Found WSL2 pattern: ${pattern}`, 'success');
                } else {
                    this.log(`Missing WSL2 pattern: ${pattern}`, 'warn');
                }
            }
            
            const success = foundPatterns >= 3; // At least 3 patterns should be present
            this.addTestResult('Postinstall WSL2 Logic', success, `Found ${foundPatterns}/${wsl2Patterns.length} WSL2 patterns`);
            return success;
            
        } catch (error) {
            this.log(`Error testing postinstall WSL2 logic: ${error.message}`, 'error');
            this.addTestResult('Postinstall WSL2 Logic', false, error.message);
            return false;
        }
    }
    
    testCLIWSL2Logic() {
        this.log('Testing CLI WSL2 detection logic...', 'info');
        
        try {
            const cliPath = path.join(this.packageRoot, 'bin', 'claude-pm');
            
            if (!fs.existsSync(cliPath)) {
                this.log('CLI script not found', 'error');
                this.addTestResult('CLI WSL2 Logic', false, 'File not found');
                return false;
            }
            
            const cliContent = fs.readFileSync(cliPath, 'utf8');
            
            // Check for WSL2-specific patterns
            const wsl2Patterns = [
                'detectPlatformInfo',
                'analyzeWSL2Path',
                'getNpmGlobalBin',
                'WSL2 Environment Detected',
                'wsl2Guidance'
            ];
            
            let foundPatterns = 0;
            for (const pattern of wsl2Patterns) {
                if (cliContent.includes(pattern)) {
                    foundPatterns++;
                    this.log(`Found CLI WSL2 pattern: ${pattern}`, 'success');
                } else {
                    this.log(`Missing CLI WSL2 pattern: ${pattern}`, 'warn');
                }
            }
            
            const success = foundPatterns >= 3; // At least 3 patterns should be present
            this.addTestResult('CLI WSL2 Logic', success, `Found ${foundPatterns}/${wsl2Patterns.length} WSL2 patterns`);
            return success;
            
        } catch (error) {
            this.log(`Error testing CLI WSL2 logic: ${error.message}`, 'error');
            this.addTestResult('CLI WSL2 Logic', false, error.message);
            return false;
        }
    }
    
    testWSL2FixScript() {
        this.log('Testing WSL2 fix script...', 'info');
        
        try {
            const fixScriptPath = path.join(this.packageRoot, 'scripts', 'wsl2-path-fix.sh');
            
            if (!fs.existsSync(fixScriptPath)) {
                this.log('WSL2 fix script not found', 'error');
                this.addTestResult('WSL2 Fix Script', false, 'File not found');
                return false;
            }
            
            // Check if script is executable
            const stats = fs.statSync(fixScriptPath);
            const isExecutable = stats.mode & fs.constants.S_IXUSR;
            
            if (!isExecutable) {
                this.log('WSL2 fix script is not executable', 'warn');
                this.addTestResult('WSL2 Fix Script', false, 'Script not executable');
                return false;
            }
            
            this.log('WSL2 fix script found and executable', 'success');
            this.addTestResult('WSL2 Fix Script', true, 'Script available and executable');
            return true;
            
        } catch (error) {
            this.log(`Error testing WSL2 fix script: ${error.message}`, 'error');
            this.addTestResult('WSL2 Fix Script', false, error.message);
            return false;
        }
    }
    
    generateReport() {
        this.log('Generating validation report...', 'info');
        
        const passed = this.testResults.filter(r => r.passed).length;
        const total = this.testResults.length;
        const percentage = Math.round((passed / total) * 100);
        
        console.log('\n' + '='.repeat(70));
        console.log('🐧 WSL2 FIX VALIDATION REPORT');
        console.log('='.repeat(70));
        console.log(`📊 Overall Score: ${passed}/${total} tests passed (${percentage}%)`);
        console.log('');
        
        // Group results by category
        const categories = {};
        for (const result of this.testResults) {
            const category = result.test.split(' (')[0];
            if (!categories[category]) categories[category] = [];
            categories[category].push(result);
        }
        
        for (const [category, results] of Object.entries(categories)) {
            console.log(`📋 ${category}:`);
            for (const result of results) {
                const status = result.passed ? '✅' : '❌';
                console.log(`   ${status} ${result.test}: ${result.message}`);
            }
            console.log('');
        }
        
        // Recommendations
        console.log('💡 Recommendations:');
        
        const failedTests = this.testResults.filter(r => !r.passed);
        if (failedTests.length === 0) {
            console.log('   🎉 All tests passed! WSL2 fixes are working correctly.');
        } else {
            console.log('   🔧 The following issues need attention:');
            for (const failed of failedTests) {
                console.log(`   • ${failed.test}: ${failed.message}`);
            }
            
            console.log('');
            console.log('   📚 Suggested actions:');
            console.log('   1. Run the WSL2 fix script: scripts/wsl2-path-fix.sh');
            console.log('   2. Restart your shell: source ~/.bashrc');
            console.log('   3. Reinstall missing packages: npm install -g @bobmatnyc/ai-trackdown-tools');
            console.log('   4. Check GitHub issue: https://github.com/bobmatnyc/claude-multiagent-pm/issues/1');
        }
        
        console.log('');
        console.log('='.repeat(70));
        
        return percentage >= 80; // Consider 80% or higher as success
    }
    
    async run() {
        console.log('🚀 Starting WSL2 Fix Validation');
        console.log('================================');
        console.log('');
        
        try {
            // Run all tests
            const isWSL2 = this.testWSL2Detection();
            this.testNpmGlobalBinDetection();
            this.testPATHConfiguration();
            this.testCommandAvailability();
            this.testPostinstallWSL2Logic();
            this.testCLIWSL2Logic();
            this.testWSL2FixScript();
            
            // Generate report
            const success = this.generateReport();
            
            if (!isWSL2) {
                console.log('ℹ️  Note: This validation was run outside of WSL2.');
                console.log('   For complete testing, run this script in a WSL2 environment.');
            }
            
            process.exit(success ? 0 : 1);
            
        } catch (error) {
            this.log(`Validation failed with error: ${error.message}`, 'error');
            console.error(error.stack);
            process.exit(1);
        }
    }
}

// Run validation if script is executed directly
if (require.main === module) {
    const validator = new WSL2FixValidator();
    validator.run();
}

module.exports = WSL2FixValidator;