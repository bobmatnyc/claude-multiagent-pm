#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Fallback Post-Installation Script
 * 
 * This fallback script is triggered when the main postinstall-minimal.js
 * cannot be found or fails to execute. It provides essential functionality
 * to get users up and running even in problematic installation scenarios.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class FallbackPostInstall {
    constructor() {
        this.platform = os.platform();
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
        
        // Try to detect package root from various locations
        this.packageRoot = this.detectPackageRoot();
    }

    /**
     * Detect package root directory
     */
    detectPackageRoot() {
        const possibleRoots = [
            path.join(__dirname, '..'),                                    // Standard relative
            process.cwd(),                                                 // Current working directory
            path.join(this.userHome, '.npm-global', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'),
            path.join('/usr', 'local', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'),
            path.join(this.userHome, '.nvm', 'versions', 'node', '*', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm')
        ];

        for (const root of possibleRoots) {
            try {
                const packageJsonPath = path.join(root, 'package.json');
                if (fs.existsSync(packageJsonPath)) {
                    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                    if (packageJson.name === '@bobmatnyc/claude-multiagent-pm') {
                        return root;
                    }
                }
            } catch (e) {
                // Continue searching
            }
        }

        // Default fallback
        return path.join(__dirname, '..');
    }

    /**
     * Log with timestamp
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '🔄';
        console.log(`${prefix} [FALLBACK] ${message}`);
    }

    /**
     * Create essential directory structure
     */
    createEssentialStructure() {
        try {
            // Create .claude-pm directory
            if (!fs.existsSync(this.globalConfigDir)) {
                fs.mkdirSync(this.globalConfigDir, { recursive: true });
                this.log(`Created essential directory: ${this.globalConfigDir}`);
            }

            // Create essential subdirectories
            const essentialDirs = ['logs', 'config', 'cache', 'memory'];
            for (const dir of essentialDirs) {
                const dirPath = path.join(this.globalConfigDir, dir);
                if (!fs.existsSync(dirPath)) {
                    fs.mkdirSync(dirPath, { recursive: true });
                    this.log(`Created directory: ${dirPath}`);
                }
            }

            // Create fallback installation marker
            const markerFile = path.join(this.globalConfigDir, '.fallback-installed');
            const markerData = {
                fallback_installation: true,
                timestamp: new Date().toISOString(),
                platform: this.platform,
                package_root: this.packageRoot,
                detected_root: this.packageRoot
            };

            fs.writeFileSync(markerFile, JSON.stringify(markerData, null, 2));
            this.log(`Created fallback installation marker: ${markerFile}`);

            return true;
        } catch (e) {
            this.log(`Failed to create essential structure: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Install minimal Python dependencies
     */
    installMinimalPython() {
        try {
            // Find Python command
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
                this.log('Python 3 not found - skipping Python installation', 'warn');
                return false;
            }

            this.log(`Using Python command: ${pythonCmd}`);

            // Install absolute minimal dependencies for CLI functionality
            const minimalDeps = ['click>=8.1.0', 'rich>=13.7.0'];
            
            for (const dep of minimalDeps) {
                try {
                    execSync(`${pythonCmd} -m pip install --user ${dep}`, { stdio: 'pipe' });
                    this.log(`✅ ${dep} installed`);
                } catch (error) {
                    // Try with --break-system-packages
                    try {
                        execSync(`${pythonCmd} -m pip install --user --break-system-packages ${dep}`, { stdio: 'pipe' });
                        this.log(`✅ ${dep} installed (with --break-system-packages)`);
                    } catch (retryError) {
                        this.log(`❌ Failed to install ${dep}`, 'error');
                    }
                }
            }

            // Try to install the package itself
            if (fs.existsSync(path.join(this.packageRoot, 'pyproject.toml'))) {
                try {
                    execSync(`${pythonCmd} -m pip install --user -e .`, { 
                        cwd: this.packageRoot,
                        stdio: 'pipe' 
                    });
                    this.log('✅ Claude PM package installed');
                    return true;
                } catch (error) {
                    try {
                        execSync(`${pythonCmd} -m pip install --user --break-system-packages -e .`, { 
                            cwd: this.packageRoot,
                            stdio: 'pipe' 
                        });
                        this.log('✅ Claude PM package installed (with --break-system-packages)');
                        return true;
                    } catch (retryError) {
                        this.log('❌ Failed to install Claude PM package', 'error');
                        return false;
                    }
                }
            } else {
                this.log('pyproject.toml not found - skipping package installation', 'warn');
                return false;
            }
        } catch (e) {
            this.log(`Minimal Python installation error: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Display fallback instructions
     */
    displayFallbackInstructions() {
        console.log('\n' + '='.repeat(70));
        console.log('🔄 Claude Multi-Agent PM Framework - Fallback Installation');
        console.log('='.repeat(70));
        
        console.log('\n⚠️  Main post-installation process failed or was not found.');
        console.log('📦 Running fallback installation to get you up and running.');
        
        console.log('\n📍 Installation Details:');
        console.log('   Package Root:', this.packageRoot);
        console.log('   Config Directory:', this.globalConfigDir);
        console.log('   Platform:', this.platform);
        
        console.log('\n🚀 Next Steps:');
        console.log('   1. Run: claude-pm init --fallback-setup');
        console.log('   2. Or manually run: python -m claude_pm.cli init --post-install');
        console.log('   3. Validate with: claude-pm health');
        
        console.log('\n🔧 If Claude PM CLI is not available:');
        console.log('   1. Navigate to:', this.packageRoot);
        console.log('   2. Run: python -m pip install --user -e .');
        console.log('   3. Run: python -m claude_pm.cli init --post-install');
        
        console.log('\n📚 Documentation and Support:');
        console.log('   • Check ~/.claude-pm/logs/ for detailed logs');
        console.log('   • Review README.md for troubleshooting');
        console.log('   • Visit GitHub repository for issues and support');
        
        console.log('\n' + '='.repeat(70));
    }

    /**
     * Run fallback installation
     */
    run() {
        this.log('Starting fallback post-installation setup');
        
        try {
            // Create essential structure
            const structureSuccess = this.createEssentialStructure();
            if (!structureSuccess) {
                throw new Error('Failed to create essential directory structure');
            }

            // Install minimal Python setup
            this.log('Installing minimal Python dependencies...');
            const pythonSuccess = this.installMinimalPython();
            
            // Display instructions regardless of Python install success
            this.displayFallbackInstructions();
            
            if (pythonSuccess) {
                this.log('Fallback installation completed successfully');
                console.log('\n✅ Fallback installation completed!');
                console.log('🚀 Run "claude-pm init --fallback-setup" to continue setup.');
            } else {
                this.log('Fallback installation completed with Python issues', 'warn');
                console.log('\n⚠️  Fallback installation completed with issues.');
                console.log('🔧 Manual Python setup may be required.');
                console.log('📖 Check the instructions above for manual setup steps.');
            }
            
            return true;
        } catch (e) {
            this.log(`Fallback installation failed: ${e.message}`, 'error');
            console.error('\n❌ Fallback installation failed!');
            console.error(`Error: ${e.message}`);
            console.error('\n🆘 Emergency manual setup:');
            console.error('   1. Create directory: mkdir -p ~/.claude-pm');
            console.error('   2. Install Python package manually');
            console.error('   3. Contact support with error details');
            return false;
        }
    }
}

// Run the fallback post-installation
if (require.main === module) {
    const fallbackInstall = new FallbackPostInstall();
    const success = fallbackInstall.run();
    
    if (!success) {
        process.exit(1);
    }
}

module.exports = FallbackPostInstall;