#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Enhanced NPM Post-Installation Script with Python Validation
 * 
 * This enhanced script includes comprehensive Python environment validation,
 * PATH ordering adjustments, and fallback mechanisms for different Python installations.
 * 
 * Enhanced by: Engineer Agent
 * Date: 2025-07-14
 * Memory Collection: Tracks installation issues and user feedback
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawn } = require('child_process');

class EnhancedPostInstallWithPython {
    constructor() {
        this.platform = os.platform();
        this.packageRoot = path.join(__dirname, '..');
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
        this.memoryCollection = [];
        this.detectedPythonEnvironments = [];
        this.bestPython = null;
    }

    /**
     * Log with timestamp and collect memory
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : '📦';
        console.log(`${prefix} [${timestamp}] ${message}`);
        
        // Collect memory for issues and feedback
        if (level === 'error' || level === 'warn') {
            this.collectMemory(
                level === 'error' ? 'error:runtime' : 'feedback:workflow',
                level === 'error' ? 'high' : 'medium',
                message
            );
        }
    }

    /**
     * Collect memory for installation issues and insights
     */
    collectMemory(category, priority, content, metadata = {}) {
        const memoryEntry = {
            timestamp: new Date().toISOString(),
            category: category,
            priority: priority,
            content: content,
            metadata: {
                ...metadata,
                platform: this.platform,
                packageRoot: this.packageRoot,
                installationType: this.isGlobalInstall() ? 'global' : 'local'
            },
            source_agent: 'Engineer',
            project_context: 'postinstall_python_validation',
            resolution_status: 'open'
        };
        this.memoryCollection.push(memoryEntry);
    }

    /**
     * Detect all available Python environments
     */
    detectPythonEnvironments() {
        this.log('🐍 Detecting Python environments...');
        
        // Priority order: system Python first, then others
        const pythonCandidates = [
            '/usr/bin/python3',
            '/System/Library/Frameworks/Python.framework/Versions/Current/bin/python3',
            '/Library/Frameworks/Python.framework/Versions/Current/bin/python3',
            '/usr/local/bin/python3',  // Homebrew Intel Mac
            '/opt/homebrew/bin/python3',  // Homebrew Apple Silicon
            'python3',  // PATH lookup
            'python'   // Fallback
        ];

        for (const candidate of pythonCandidates) {
            try {
                let pythonPath;
                
                // For absolute paths, check if file exists
                if (candidate.startsWith('/')) {
                    if (!fs.existsSync(candidate)) {
                        continue;
                    }
                    pythonPath = candidate;
                } else {
                    // For relative names, use which
                    try {
                        pythonPath = execSync(`which ${candidate}`, { encoding: 'utf8' }).trim();
                    } catch (e) {
                        continue;
                    }
                }

                // Test the Python executable
                const versionResult = execSync(`"${pythonPath}" --version`, { 
                    encoding: 'utf8', 
                    timeout: 5000 
                });

                if (versionResult.includes('Python 3.')) {
                    const versionMatch = versionResult.match(/Python (\\d+)\\.(\\d+)\\.(\\d+)/);
                    if (versionMatch) {
                        const major = parseInt(versionMatch[1]);
                        const minor = parseInt(versionMatch[2]);
                        
                        if (major === 3 && minor >= 8) {
                            // Additional validation: test basic import
                            try {
                                execSync(`"${pythonPath}" -c "import sys, os, json"`, { 
                                    encoding: 'utf8', 
                                    timeout: 5000,
                                    stdio: 'pipe'
                                });

                                const environment = {
                                    executable: pythonPath,
                                    version: versionResult.trim(),
                                    versionInfo: [major, minor, parseInt(versionMatch[3])],
                                    isSystem: pythonPath.includes('/usr/bin') || pythonPath.includes('/System/'),
                                    isHomebrew: pythonPath.includes('/opt/homebrew') || pythonPath.includes('/usr/local'),
                                    isPyenv: pythonPath.includes('.pyenv'),
                                    pathPriority: this.calculatePathPriority(pythonPath),
                                    works: true
                                };

                                this.detectedPythonEnvironments.push(environment);
                                this.log(`   Found: ${pythonPath} (${versionResult.trim()})`);
                            } catch (importError) {
                                this.log(`   Failed import test: ${pythonPath}`, 'warn');
                            }
                        }
                    }
                }
            } catch (error) {
                // Silently continue to next candidate
            }
        }

        // Sort by priority (system first, then by version)
        this.detectedPythonEnvironments.sort((a, b) => {
            if (a.isSystem && !b.isSystem) return -1;
            if (!a.isSystem && b.isSystem) return 1;
            return a.pathPriority - b.pathPriority;
        });

        this.log(`🔍 Detected ${this.detectedPythonEnvironments.length} working Python environments`);
        
        if (this.detectedPythonEnvironments.length > 0) {
            this.bestPython = this.detectedPythonEnvironments[0];
            this.log(`✅ Best Python: ${this.bestPython.executable} (${this.bestPython.version})`, 'success');
            
            this.collectMemory(
                'architecture:design', 'medium',
                `Selected Python environment: ${this.bestPython.executable}`,
                { python_environments: this.detectedPythonEnvironments }
            );
        } else {
            this.log('❌ No suitable Python environment found', 'error');
            this.collectMemory(
                'error:integration', 'critical',
                'No suitable Python environment found during postinstall'
            );
        }

        return this.detectedPythonEnvironments;
    }

    /**
     * Calculate path priority for Python executable (lower = higher priority)
     */
    calculatePathPriority(executable) {
        if (executable.includes('/usr/bin')) return 1;
        if (executable.includes('/System/')) return 2;
        if (executable.includes('/Library/Frameworks/Python.framework')) return 3;
        if (executable.includes('.pyenv')) return 4;
        if (executable.includes('/usr/local/bin')) return 5;
        if (executable.includes('/opt/homebrew')) return 6;
        if (executable.includes('conda')) return 7;
        return 8;
    }

    /**
     * Validate Python environment for Claude PM requirements
     */
    validatePythonEnvironment(pythonExecutable) {
        this.log(`🔍 Validating Python environment: ${pythonExecutable}`);
        
        const issues = [];

        try {
            // Check if executable exists and is executable
            if (!fs.existsSync(pythonExecutable)) {
                issues.push(`Python executable not found: ${pythonExecutable}`);
                return { valid: false, issues };
            }

            // Check required modules
            const requiredModules = ['subprocess', 'pathlib', 'json', 'sys', 'os'];
            for (const module of requiredModules) {
                try {
                    execSync(`"${pythonExecutable}" -c "import ${module}"`, { 
                        stdio: 'pipe', 
                        timeout: 5000 
                    });
                } catch (error) {
                    issues.push(`Required module '${module}' not available`);
                }
            }

            // Check pip availability
            try {
                execSync(`"${pythonExecutable}" -m pip --version`, { 
                    stdio: 'pipe', 
                    timeout: 5000 
                });
            } catch (error) {
                issues.push('pip not available with this Python installation');
            }

            const isValid = issues.length === 0;
            
            if (isValid) {
                this.log(`✅ Python environment validation passed`, 'success');
            } else {
                this.log(`❌ Python environment validation failed:`, 'error');
                issues.forEach(issue => this.log(`   - ${issue}`, 'error'));
                
                this.collectMemory(
                    'error:integration', 'high',
                    `Python validation failed: ${issues.join('; ')}`,
                    { python_executable: pythonExecutable, issues }
                );
            }

            return { valid: isValid, issues };

        } catch (error) {
            issues.push(`Validation error: ${error.message}`);
            this.collectMemory(
                'error:runtime', 'high',
                `Python validation exception: ${error.message}`,
                { python_executable: pythonExecutable }
            );
            return { valid: false, issues };
        }
    }

    /**
     * Adjust PATH to prioritize system Python
     */
    adjustPathForSystemPython() {
        this.log('🔧 Adjusting PATH to prioritize system Python...');
        
        const currentPath = process.env.PATH.split(path.delimiter);
        
        // Priority paths that should come first
        const priorityPaths = [
            '/usr/bin',
            '/bin',
            '/usr/sbin',
            '/sbin'
        ];

        // Build new PATH with system paths first
        const newPath = [];

        // Add priority paths first
        for (const pathEntry of priorityPaths) {
            if (!newPath.includes(pathEntry) && fs.existsSync(pathEntry)) {
                newPath.push(pathEntry);
            }
        }

        // Add remaining paths (excluding Homebrew paths temporarily)
        const homebrewPaths = ['/opt/homebrew/bin', '/opt/homebrew/sbin', '/usr/local/bin'];
        for (const pathEntry of currentPath) {
            if (!newPath.includes(pathEntry) && !homebrewPaths.includes(pathEntry)) {
                newPath.push(pathEntry);
            }
        }

        // Add Homebrew paths at the end
        for (const pathEntry of homebrewPaths) {
            if (!newPath.includes(pathEntry) && fs.existsSync(pathEntry)) {
                newPath.push(pathEntry);
            }
        }

        const adjustedPath = newPath.join(path.delimiter);
        process.env.PATH = adjustedPath;

        this.log('✅ PATH adjusted successfully', 'success');
        
        // Create PATH adjustment script for user
        this.createPathAdjustmentScript(adjustedPath);
        
        return adjustedPath;
    }

    /**
     * Create PATH adjustment script for user
     */
    createPathAdjustmentScript(adjustedPath) {
        const scriptPath = path.join(this.globalConfigDir, 'adjust_python_path.sh');
        
        const scriptContent = `#!/bin/bash
# Claude PM Python PATH Adjustment Script
# Generated: ${new Date().toISOString()}

echo "🐍 Adjusting PATH to prioritize system Python..."

# Export the optimized PATH
export PATH="${adjustedPath}"

echo "✅ PATH adjusted successfully"
echo "🔍 Current Python: $(which python3 2>/dev/null || which python 2>/dev/null || echo 'not found')"

# Verify Python version
if command -v python3 >/dev/null 2>&1; then
    echo "📋 Python version: $(python3 --version)"
else
    echo "⚠️  Warning: python3 not found in PATH"
fi

# To make this permanent, add the following to your ~/.bashrc or ~/.zshrc:
# export PATH="${adjustedPath}"
`;

        try {
            fs.writeFileSync(scriptPath, scriptContent);
            fs.chmodSync(scriptPath, 0o755);
            this.log(`📝 PATH adjustment script created: ${scriptPath}`);
            this.log(`💡 To apply: source ${scriptPath}`);
        } catch (error) {
            this.log(`Failed to create PATH adjustment script: ${error.message}`, 'warn');
        }
    }

    /**
     * Install Python requirements with enhanced error handling
     */
    installPythonRequirements(pythonExecutable) {
        this.log('📦 Installing Python requirements...');
        
        const requirementsPath = path.join(this.packageRoot, 'requirements', 'base.txt');
        
        if (!fs.existsSync(requirementsPath)) {
            this.log(`Requirements file not found: ${requirementsPath}`, 'warn');
            return false;
        }

        try {
            // Try standard installation first
            this.log('   Attempting standard pip installation...');
            execSync(`"${pythonExecutable}" -m pip install --user -r "${requirementsPath}"`, {
                stdio: 'pipe',
                timeout: 300000,  // 5 minutes
                cwd: this.packageRoot
            });
            
            this.log('✅ Requirements installed successfully', 'success');
            return true;
            
        } catch (error) {
            const stderr = error.stderr ? error.stderr.toString() : '';
            
            // If standard installation fails due to externally managed environment,
            // try with --break-system-packages
            if (stderr.includes('externally-managed-environment') || stderr.includes('externally managed')) {
                this.log('   Retrying with --break-system-packages...', 'warn');
                
                try {
                    execSync(`"${pythonExecutable}" -m pip install --user --break-system-packages -r "${requirementsPath}"`, {
                        stdio: 'pipe',
                        timeout: 300000,
                        cwd: this.packageRoot
                    });
                    
                    this.log('✅ Requirements installed successfully (with --break-system-packages)', 'success');
                    return true;
                    
                } catch (retryError) {
                    this.log(`❌ Requirements installation failed (retry): ${retryError.message}`, 'error');
                    this.collectMemory(
                        'error:integration', 'high',
                        `Requirements installation failed with --break-system-packages: ${retryError.message}`
                    );
                    return false;
                }
            } else {
                this.log(`❌ Requirements installation failed: ${error.message}`, 'error');
                this.collectMemory(
                    'error:integration', 'high',
                    `Requirements installation failed: ${error.message}`
                );
                return false;
            }
        }
    }

    /**
     * Install Claude PM Python package
     */
    installClaudePmPackage(pythonExecutable) {
        this.log('📦 Installing Claude PM Python package...');

        try {
            // Try standard installation first
            this.log('   Installing package in editable mode...');
            execSync(`"${pythonExecutable}" -m pip install --user -e .`, {
                stdio: 'pipe',
                timeout: 120000,  // 2 minutes
                cwd: this.packageRoot
            });
            
            this.log('✅ Claude PM package installed successfully', 'success');
            return true;
            
        } catch (error) {
            const stderr = error.stderr ? error.stderr.toString() : '';
            
            // Try with --break-system-packages for externally managed environments
            if (stderr.includes('externally-managed-environment') || stderr.includes('externally managed')) {
                this.log('   Retrying package installation with --break-system-packages...', 'warn');
                
                try {
                    execSync(`"${pythonExecutable}" -m pip install --user --break-system-packages -e .`, {
                        stdio: 'pipe',
                        timeout: 120000,
                        cwd: this.packageRoot
                    });
                    
                    this.log('✅ Claude PM package installed successfully (with --break-system-packages)', 'success');
                    return true;
                    
                } catch (retryError) {
                    this.log(`❌ Package installation failed (retry): ${retryError.message}`, 'error');
                    this.collectMemory(
                        'error:integration', 'high',
                        `Claude PM package installation failed with --break-system-packages: ${retryError.message}`
                    );
                    return false;
                }
            } else {
                this.log(`❌ Package installation failed: ${error.message}`, 'error');
                this.collectMemory(
                    'error:integration', 'high',
                    `Claude PM package installation failed: ${error.message}`
                );
                return false;
            }
        }
    }

    /**
     * Test Claude PM installation
     */
    testClaudePmInstallation(pythonExecutable) {
        this.log('🧪 Testing Claude PM installation...');
        
        try {
            const testResult = execSync(`"${pythonExecutable}" -c "import claude_pm; print('Claude PM import successful')"`, {
                encoding: 'utf8',
                timeout: 10000,
                stdio: 'pipe'
            });
            
            this.log('✅ Claude PM import test passed', 'success');
            return true;
            
        } catch (error) {
            this.log(`⚠️  Claude PM import test failed: ${error.message}`, 'warn');
            this.collectMemory(
                'feedback:workflow', 'medium',
                `Claude PM import test failed: ${error.message}`
            );
            return false;
        }
    }

    /**
     * Save memory collection for debugging
     */
    saveMemoryCollection() {
        if (this.memoryCollection.length === 0) {
            return null;
        }

        try {
            const memoryData = {
                collection_timestamp: new Date().toISOString(),
                source_agent: 'Engineer',
                category: 'postinstall_python_validation',
                total_entries: this.memoryCollection.length,
                entries: this.memoryCollection
            };

            const memoryPath = path.join(this.globalConfigDir, `postinstall_memory_${Date.now()}.json`);
            fs.writeFileSync(memoryPath, JSON.stringify(memoryData, null, 2));
            
            this.log(`🧠 Memory collection saved: ${memoryPath}`);
            return memoryPath;
            
        } catch (error) {
            this.log(`Failed to save memory collection: ${error.message}`, 'warn');
            return null;
        }
    }

    /**
     * Generate installation report
     */
    generateInstallationReport(success, pythonExecutable) {
        const reportData = {
            timestamp: new Date().toISOString(),
            success: success,
            python_executable: pythonExecutable,
            platform: {
                system: os.platform(),
                release: os.release(),
                arch: os.arch(),
                homedir: this.userHome
            },
            detected_environments: this.detectedPythonEnvironments,
            best_python: this.bestPython,
            package_root: this.packageRoot,
            global_install: this.isGlobalInstall(),
            memory_entries: this.memoryCollection.length
        };

        try {
            const reportPath = path.join(this.globalConfigDir, `installation_report_${Date.now()}.json`);
            fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
            
            this.log(`📊 Installation report saved: ${reportPath}`);
            return reportPath;
            
        } catch (error) {
            this.log(`Failed to save installation report: ${error.message}`, 'warn');
            return null;
        }
    }

    /**
     * Check if we're in a global npm installation
     */
    isGlobalInstall() {
        const npmConfigPrefix = process.env.npm_config_prefix;
        const packagePath = this.packageRoot;
        const npmRoot = process.env.npm_config_globaldir || process.env.npm_root;
        
        return (
            (npmConfigPrefix && packagePath.includes(npmConfigPrefix)) ||
            (npmRoot && packagePath.includes(npmRoot)) ||
            (packagePath.includes('node_modules') && (
                packagePath.includes('/.npm-global/') ||
                packagePath.includes('/lib/node_modules/') ||
                packagePath.includes('\\\\AppData\\\\Roaming\\\\npm\\\\') ||
                packagePath.includes('/.nvm/versions/node/')
            ))
        );
    }

    /**
     * Create basic directory structure
     */
    createBasicStructure() {
        try {
            // Create basic .claude-pm directory
            if (!fs.existsSync(this.globalConfigDir)) {
                fs.mkdirSync(this.globalConfigDir, { recursive: true });
                this.log(`Created directory: ${this.globalConfigDir}`);
            }
            
            // Create logs directory
            const logsDir = path.join(this.globalConfigDir, 'logs');
            if (!fs.existsSync(logsDir)) {
                fs.mkdirSync(logsDir, { recursive: true });
                this.log(`Created logs directory: ${logsDir}`);
            }
            
            // Create a marker file to indicate enhanced NPM installation
            const markerFile = path.join(this.globalConfigDir, '.npm-installed-enhanced');
            const markerData = {
                npm_installation: true,
                enhanced_python_validation: true,
                timestamp: new Date().toISOString(),
                platform: this.platform,
                global_install: this.isGlobalInstall(),
                package_root: this.packageRoot,
                version: this.getPackageVersion(),
                python_environments: this.detectedPythonEnvironments,
                best_python: this.bestPython
            };
            
            fs.writeFileSync(markerFile, JSON.stringify(markerData, null, 2));
            this.log(`Created enhanced installation marker: ${markerFile}`);
            
            return true;
        } catch (e) {
            this.log(`Failed to create basic structure: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Get package version
     */
    getPackageVersion() {
        try {
            const packageJsonPath = path.join(this.packageRoot, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                return packageJson.version;
            }
            return 'unknown';
        } catch (e) {
            return 'unknown';
        }
    }

    /**
     * Display final instructions
     */
    displayFinalInstructions(success, pythonExecutable) {
        console.log('\\n' + '='.repeat(70));
        console.log('🐍 Claude Multi-Agent PM Framework - Enhanced Post-Installation');
        console.log('='.repeat(70));
        
        if (success) {
            console.log('\\n✅ Installation completed successfully!');
            console.log(`🐍 Python executable: ${pythonExecutable}`);
            console.log('📍 Package installed to:', this.packageRoot);
            console.log('🌐 Global installation:', this.isGlobalInstall() ? 'Yes' : 'No');
            
            console.log('\\n🚀 Next Steps:');
            console.log('   1. Complete framework initialization:');
            console.log('      claude-pm init --post-install');
            console.log('   2. Verify installation:');
            console.log('      claude-pm --system-info');
            console.log('   3. Apply PATH optimization (optional):');
            console.log(`      source ${path.join(this.globalConfigDir, 'adjust_python_path.sh')}`);
            
        } else {
            console.log('\\n❌ Installation encountered issues!');
            console.log('\\n🔧 Troubleshooting steps:');
            console.log('   1. Check Python installation (Python 3.8+ required)');
            console.log('   2. Verify pip is available');
            console.log('   3. Run manual installation:');
            console.log(`      cd ${this.packageRoot}`);
            console.log('      python3 scripts/install_with_python_validation.py');
            console.log('   4. Check installation logs in ~/.claude-pm/logs/');
        }
        
        console.log('\\n📚 Python Environment Summary:');
        if (this.detectedPythonEnvironments.length > 0) {
            this.detectedPythonEnvironments.forEach((env, index) => {
                const marker = index === 0 ? '🎯' : '  ';
                console.log(`${marker} ${env.executable} (${env.version})`);
                console.log(`     Type: ${env.isSystem ? 'System' : env.isHomebrew ? 'Homebrew' : 'Other'}`);
            });
        } else {
            console.log('   ❌ No suitable Python environments detected');
        }
        
        console.log('\\n' + '='.repeat(70));
    }

    /**
     * Run enhanced post-installation
     */
    run() {
        this.log('🚀 Starting enhanced post-installation with Python validation');
        
        let success = false;
        let pythonExecutable = null;
        
        try {
            // Create basic directory structure
            this.createBasicStructure();
            
            // Adjust PATH to prioritize system Python
            this.adjustPathForSystemPython();
            
            // Detect Python environments
            this.detectPythonEnvironments();
            
            if (!this.bestPython) {
                this.log('❌ No suitable Python environment found', 'error');
                this.displayFinalInstructions(false, null);
                return false;
            }
            
            pythonExecutable = this.bestPython.executable;
            
            // Validate Python environment
            const validation = this.validatePythonEnvironment(pythonExecutable);
            if (!validation.valid) {
                this.log('❌ Python environment validation failed', 'error');
                this.displayFinalInstructions(false, pythonExecutable);
                return false;
            }
            
            // Install Python requirements
            const requirementsSuccess = this.installPythonRequirements(pythonExecutable);
            if (!requirementsSuccess) {
                this.log('⚠️  Requirements installation failed - continuing anyway', 'warn');
            }
            
            // Install Claude PM package
            const packageSuccess = this.installClaudePmPackage(pythonExecutable);
            if (!packageSuccess) {
                this.log('❌ Claude PM package installation failed', 'error');
                this.displayFinalInstructions(false, pythonExecutable);
                return false;
            }
            
            // Test installation
            this.testClaudePmInstallation(pythonExecutable);
            
            success = true;
            this.log('🎉 Enhanced post-installation completed successfully!', 'success');
            
        } catch (error) {
            this.log(`❌ Post-installation failed: ${error.message}`, 'error');
            this.collectMemory(
                'error:runtime', 'critical',
                `Post-installation failed: ${error.message}`,
                { stack: error.stack }
            );
        } finally {
            // Save memory collection and generate report
            this.saveMemoryCollection();
            this.generateInstallationReport(success, pythonExecutable);
            
            // Display final instructions
            this.displayFinalInstructions(success, pythonExecutable);
        }
        
        return success;
    }
}

// Run the enhanced post-installation
if (require.main === module) {
    const postInstall = new EnhancedPostInstallWithPython();
    const success = postInstall.run();
    
    if (!success) {
        process.exit(1);
    }
}

module.exports = EnhancedPostInstallWithPython;