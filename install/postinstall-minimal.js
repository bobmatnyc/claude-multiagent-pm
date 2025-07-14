#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Minimal NPM Post-Installation Script
 * 
 * This minimal script replaces the complex postinstall.js and directs users
 * to run the Python-based claude-pm init command for post-installation setup.
 * 
 * All functionality previously in postinstall.js has been moved to:
 * - PostInstallationManager service (Python)
 * - SystemInitAgent integration
 * - claude-pm init command with post-install flags
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class MinimalPostInstall {
    constructor() {
        this.platform = os.platform();
        this.packageRoot = path.join(__dirname, '..');
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
    }

    /**
     * Log with timestamp
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '📦';
        console.log(`${prefix} [${timestamp}] ${message}`);
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
                packagePath.includes('\\AppData\\Roaming\\npm\\') ||
                packagePath.includes('/.nvm/versions/node/')
            ))
        );
    }

    /**
     * Install Python package
     */
     installPythonPackage() {
        this.log('Installing Python package...');
        
        try {
            // Find available Python command
            const pythonCommands = ['python3', 'python'];
            let pythonCmd = null;
            
            for (const cmd of pythonCommands) {
                try {
                    const version = execSync(`${cmd} --version`, { stdio: 'pipe', encoding: 'utf8' });
                    if (version.includes('Python 3.')) {
                        pythonCmd = cmd;
                        break;
                    }
                } catch (e) {
                    // Continue to next command
                }
            }
            
            if (!pythonCmd) {
                this.log('Python 3.8+ not found - skipping Python package installation', 'warn');
                return false;
            }
            
            this.log(`Using Python command: ${pythonCmd}`);
            
            // Install package in editable mode from current directory
            try {
                this.log('Installing Python package in editable mode...');
                execSync(`${pythonCmd} -m pip install --user -e .`, { 
                    cwd: this.packageRoot,
                    stdio: 'pipe' 
                });
                this.log('Python package installed successfully');
                return true;
            } catch (error) {
                // Try with --break-system-packages for externally managed environments
                const stderr = error.stderr ? error.stderr.toString() : '';
                if (stderr.includes('externally-managed-environment') || stderr.includes('externally managed')) {
                    this.log('Retrying with --break-system-packages for externally managed environment...');
                    try {
                        execSync(`${pythonCmd} -m pip install --user --break-system-packages -e .`, { 
                            cwd: this.packageRoot,
                            stdio: 'pipe' 
                        });
                        this.log('Python package installed successfully with --break-system-packages');
                        return true;
                    } catch (retryError) {
                        this.log(`Failed to install Python package: ${retryError.message}`, 'error');
                        return false;
                    }
                } else {
                    this.log(`Failed to install Python package: ${error.message}`, 'error');
                    return false;
                }
            }
        } catch (e) {
            this.log(`Python package installation error: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Check if claude-pm CLI is available
     */
    checkClaudePmAvailable() {
        try {
            // Try to find claude-pm command
            const commands = ['claude-pm', 'python -m claude_pm.cli', 'python3 -m claude_pm.cli'];
            
            for (const cmd of commands) {
                try {
                    execSync(`${cmd} --help`, { stdio: 'pipe' });
                    return { available: true, command: cmd };
                } catch (e) {
                    // Continue to next command
                }
            }
            
            return { available: false, command: null };
        } catch (e) {
            return { available: false, command: null };
        }
    }

    /**
     * Display post-installation instructions
     */
    displayInstructions() {
        console.log('\n' + '='.repeat(70));
        console.log('📦 Claude Multi-Agent PM Framework - Post-Installation');
        console.log('='.repeat(70));
        
        console.log('\n🔄 NPM installation completed successfully!');
        console.log('📍 Package installed to:', this.packageRoot);
        console.log('🌐 Global installation:', this.isGlobalInstall() ? 'Yes' : 'No');
        console.log('🖥️  Platform:', this.platform);
        
        console.log('\n📋 Next Steps:');
        console.log('   1. Complete the post-installation setup');
        console.log('   2. Initialize the Claude PM Framework');
        console.log('   3. Verify the installation');
        
        // Check if claude-pm CLI is available
        const cliCheck = this.checkClaudePmAvailable();
        
        if (cliCheck.available) {
            console.log('\n✅ Claude PM CLI detected!');
            console.log('\n🚀 Run the following command to complete setup:');
            console.log(`   ${cliCheck.command} init --post-install`);
            console.log('\n📖 Available options:');
            console.log('   claude-pm init --post-install      # Complete post-installation');
            console.log('   claude-pm init --postinstall-only  # Run only post-installation');
            console.log('   claude-pm init --validate          # Validate installation');
            console.log('   claude-pm init --help              # Show all options');
        } else {
            console.log('\n⚠️  Claude PM CLI not yet available');
            console.log('\n🔧 Manual setup required:');
            console.log('   1. Navigate to the package directory:');
            console.log(`      cd ${this.packageRoot}`);
            console.log('   2. Run post-installation manually:');
            console.log('      python -m claude_pm.cli init --post-install');
            console.log('   3. Or install the package globally:');
            console.log('      pip install -e .');
        }
        
        console.log('\n💡 What the post-installation process does:');
        console.log('   • Creates ~/.claude-pm/ directory structure');
        console.log('   • Deploys framework components');
        console.log('   • Initializes memory system');
        console.log('   • Configures CLI commands');
        console.log('   • Validates installation');
        
        console.log('\n📚 Documentation:');
        console.log('   • Check README.md for usage instructions');
        console.log('   • Visit ~/.claude-pm/logs/ for installation logs');
        console.log('   • Run claude-pm health to verify status');
        
        console.log('\n' + '='.repeat(70));
    }

    /**
     * Create basic directory structure
     */
    createBasicStructure() {
        try {
            // Create basic .claude-pm directory
            if (!fs.existsSync(this.globalConfigDir)) {
                fs.mkdirSync(this.globalConfigDir, { recursive: true });
                this.log(`Created basic directory: ${this.globalConfigDir}`);
            }
            
            // Create a marker file to indicate NPM installation
            const markerFile = path.join(this.globalConfigDir, '.npm-installed');
            const markerData = {
                npm_installation: true,
                timestamp: new Date().toISOString(),
                platform: this.platform,
                global_install: this.isGlobalInstall(),
                package_root: this.packageRoot,
                version: this.getPackageVersion()
            };
            
            fs.writeFileSync(markerFile, JSON.stringify(markerData, null, 2));
            this.log(`Created installation marker: ${markerFile}`);
            
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
     * Run minimal post-installation
     */
    run() {
        this.log('Starting minimal post-installation setup');
        
        try {
            // Create basic directory structure
            this.createBasicStructure();
            
            // Install Python package (critical for CLI functionality)
            this.log('Installing Python package for CLI functionality...');
            const pythonInstallSuccess = this.installPythonPackage();
            
            if (pythonInstallSuccess) {
                this.log('Python package installation completed successfully');
            } else {
                this.log('Python package installation failed - manual installation may be required', 'warn');
            }
            
            // Display instructions
            this.displayInstructions();
            
            this.log('Minimal post-installation completed');
            this.log('Run "claude-pm init --post-install" to complete setup');
            
            return true;
        } catch (e) {
            this.log(`Post-installation failed: ${e.message}`, 'error');
            console.error('\n❌ Post-installation failed!');
            console.error(`Error: ${e.message}`);
            console.error('\n🔧 Manual setup required:');
            console.error('   1. Check permissions for ~/.claude-pm/');
            console.error('   2. Verify Python and required dependencies');
            console.error('   3. Install Python package: pip install -e .');
            console.error('   4. Run claude-pm init --post-install manually');
            return false;
        }
    }
}

// Run the minimal post-installation
if (require.main === module) {
    const postInstall = new MinimalPostInstall();
    const success = postInstall.run();
    
    if (!success) {
        process.exit(1);
    }
}

module.exports = MinimalPostInstall;