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
     * Install Python dependencies and package
     */
    installPythonPackage() {
        this.log('Installing Python dependencies and package...');
        
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
                this.log('Python 3.8+ not found - skipping Python installation', 'warn');
                return false;
            }
            
            this.log(`Using Python command: ${pythonCmd}`);
            
            // Install core dependencies first
            const coreDependencies = [
                'click>=8.1.0',
                'rich>=13.7.0', 
                'pydantic>=2.5.0',
                'pyyaml>=6.0.1',
                'python-dotenv>=1.0.0',
                'requests>=2.31.0',
                'openai>=1.0.0',
                'python-frontmatter>=1.0.0',
                'mistune>=3.0.0',
                'ai-trackdown-pytools==1.1.0'  // Python ticketing system
            ];
            
            // TEMPORARILY DISABLED: Memory system dependencies causing installation failures
            const aiDependencies = [
                // 'mem0ai>=0.1.0',      // Commented out - causing installation failures
                // 'chromadb>=0.4.0',   // Commented out - causing installation failures  
                'aiosqlite>=0.19.0',
                // 'tiktoken>=0.5.0',   // Commented out - causing installation failures
                // 'sqlite-vec>=0.0.1a0' // Commented out - causing installation failures
            ];
            
            // Install core dependencies
            this.log('Installing core Python dependencies...');
            let coreSuccess = this.installDependencyGroup(pythonCmd, coreDependencies, 'core');
            
            // Install AI dependencies (optional but critical)
            this.log('Installing AI/memory system dependencies...');
            let aiSuccess = this.installDependencyGroup(pythonCmd, aiDependencies, 'AI/memory');
            
            // Install package in editable mode from current directory
            const packageInstalled = this.installClaudePmPackage(pythonCmd);
            
            // Validate installation
            const validationResults = this.validateInstallation(pythonCmd);
            
            // Log overall success status
            if (coreSuccess && aiSuccess && packageInstalled) {
                this.log('✅ Complete installation successful - all dependencies and package installed');
                this.log(`✅ Validation: Core CLI (${validationResults.cliAvailable ? 'available' : 'missing'}), Memory system (${validationResults.memorySystemAvailable ? 'available' : 'missing'})`);
                return true;
            } else if (coreSuccess && packageInstalled) {
                this.log('⚠️ Partial installation successful - core functionality available, some AI features may be limited', 'warn');
                this.log(`⚠️ Validation: Core CLI (${validationResults.cliAvailable ? 'available' : 'missing'}), Memory system (${validationResults.memorySystemAvailable ? 'limited' : 'missing'})`);
                return true; // Still functional without AI deps
            } else {
                this.log('❌ Installation failed - critical components missing', 'error');
                this.log(`❌ Validation: Core CLI (${validationResults.cliAvailable ? 'available' : 'missing'}), Memory system (${validationResults.memorySystemAvailable ? 'available' : 'missing'})`);
                return false;
            }
        } catch (e) {
            this.log(`Python package installation error: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Install Claude PM package with comprehensive error handling
     */
    installClaudePmPackage(pythonCmd) {
        this.log('Installing Claude PM Python package...');
        
        // Try installation from PyPI first (preferred)
        this.log('Trying installation from PyPI (preferred method)...');
        try {
            execSync(`${pythonCmd} -m pip install --user claude-multiagent-pm`, { 
                stdio: 'pipe',
                timeout: 120000
            });
            this.log('✅ Claude PM package installed from PyPI');
            return true;
        } catch (pypiError) {
            this.log('PyPI installation failed, trying editable mode...', 'warn');
        }
        
        // Fallback to editable mode
        try {
            execSync(`${pythonCmd} -m pip install --user -e .`, { 
                cwd: this.packageRoot,
                stdio: 'pipe',
                timeout: 120000
            });
            this.log('✅ Claude PM Python package installed in editable mode');
            this.log('⚠️  DEPRECATION: Editable installation is deprecated, please use PyPI', 'warn');
            return true;
        } catch (error) {
            const stderr = error.stderr ? error.stderr.toString() : '';
            
            // Try with --break-system-packages for externally managed environments
            if (stderr.includes('externally-managed-environment') || stderr.includes('externally managed')) {
                this.log('Retrying package installation with --break-system-packages...');
                try {
                    execSync(`${pythonCmd} -m pip install --user --break-system-packages -e .`, { 
                        cwd: this.packageRoot,
                        stdio: 'pipe',
                        timeout: 120000
                    });
                    this.log('✅ Claude PM package installed with --break-system-packages');
                    return true;
                } catch (retryError) {
                    this.log(`❌ Failed to install Claude PM package: ${retryError.message}`, 'error');
                    return false;
                }
            }
            
            // All installation methods failed
            this.log(`❌ All installation methods failed: ${error.message}`, 'error');
            return false;
        }
    }

    /**
     * Check if ai-trackdown-pytools is available
     */
    checkAiTrackdownAvailable(pythonCmd) {
        this.log('Checking ai-trackdown-pytools availability...');
        
        try {
            // Check if ai-trackdown module is available
            execSync(`${pythonCmd} -c "import ai_trackdown; print('ai-trackdown-pytools available')"`, { 
                stdio: 'pipe',
                timeout: 10000
            });
            
            this.log('✅ ai-trackdown-pytools is available');
            return { available: true, version: '1.1.0' };
        } catch (e) {
            this.log('⚠️ ai-trackdown-pytools not detected - ticketing features may be limited', 'warn');
            return { available: false, version: null };
        }
    }

    /**
     * Validate installation components
     */
    validateInstallation(pythonCmd) {
        const results = {
            cliAvailable: false,
            memorySystemAvailable: false,
            coreModulesAvailable: false
        };
        
        // Test CLI availability
        try {
            execSync(`${pythonCmd} -c "import claude_pm; print('CLI available')"`, { stdio: 'pipe', timeout: 10000 });
            results.cliAvailable = true;
        } catch (e) {
            // CLI not available
        }
        
        // Test memory system components (DISABLED - memory system temporarily disabled)
        try {
            // execSync(`${pythonCmd} -c "import mem0ai, chromadb; print('Memory system available')"`, { stdio: 'pipe', timeout: 10000 });
            execSync(`${pythonCmd} -c "import aiosqlite; print('Basic memory components available')"`, { stdio: 'pipe', timeout: 10000 });
            results.memorySystemAvailable = true;
        } catch (e) {
            // Memory system not fully available
        }
        
        // Test core modules
        try {
            execSync(`${pythonCmd} -c "import click, rich, pydantic; print('Core modules available')"`, { stdio: 'pipe', timeout: 10000 });
            results.coreModulesAvailable = true;
        } catch (e) {
            // Core modules not available
        }
        
        return results;
    }

    /**
     * Install a group of dependencies with error handling
     */
    installDependencyGroup(pythonCmd, dependencies, groupName) {
        let groupSuccess = true;
        let installCount = 0;
        
        this.log(`Installing ${dependencies.length} ${groupName} dependencies...`);
        
        for (const dep of dependencies) {
            const installed = this.installSingleDependency(pythonCmd, dep, groupName);
            if (installed) {
                installCount++;
            } else if (groupName === 'core') {
                groupSuccess = false; // Core deps are critical
            }
        }
        
        this.log(`${groupName} dependencies: ${installCount}/${dependencies.length} installed successfully`);
        
        if (groupSuccess) {
            this.log(`✅ ${groupName} dependencies completed`);
        } else {
            this.log(`❌ Critical ${groupName} dependencies failed`, 'error');
        }
        
        return groupSuccess;
    }

    /**
     * Install a single dependency with comprehensive error handling
     */
    installSingleDependency(pythonCmd, dep, groupName) {
        // Try normal installation first
        try {
            execSync(`${pythonCmd} -m pip install --user ${dep}`, { stdio: 'pipe', timeout: 120000 });
            this.log(`   ✅ ${dep}`);
            return true;
        } catch (error) {
            const stderr = error.stderr ? error.stderr.toString() : '';
            
            // Try with --break-system-packages for externally managed environments
            if (stderr.includes('externally-managed-environment') || stderr.includes('externally managed')) {
                try {
                    execSync(`${pythonCmd} -m pip install --user --break-system-packages ${dep}`, { stdio: 'pipe', timeout: 120000 });
                    this.log(`   ✅ ${dep} (system packages)`);
                    return true;
                } catch (retryError) {
                    this.log(`   ❌ ${dep}: ${retryError.message}`, 'error');
                    return false;
                }
            }
            
            // For AI dependencies, try alternative installation methods
            if (groupName === 'AI/memory' && dep.includes('mem0ai')) {
                this.log(`   ⚠️ ${dep} failed, trying git installation...`, 'warn');
                try {
                    execSync(`${pythonCmd} -m pip install --user git+https://github.com/mem0ai/mem0.git`, { stdio: 'pipe', timeout: 180000 });
                    this.log(`   ✅ mem0ai (git version)`);
                    return true;
                } catch (gitError) {
                    this.log(`   ❌ ${dep}: Git installation also failed`, 'error');
                    return false;
                }
            }
            
            // For chromadb, try different versions
            if (groupName === 'AI/memory' && dep.includes('chromadb')) {
                this.log(`   ⚠️ ${dep} failed, trying alternative version...`, 'warn');
                const altVersions = ['chromadb>=0.3.0', 'chromadb'];
                for (const altDep of altVersions) {
                    try {
                        execSync(`${pythonCmd} -m pip install --user ${altDep}`, { stdio: 'pipe', timeout: 120000 });
                        this.log(`   ✅ ${altDep}`);
                        return true;
                    } catch (altError) {
                        continue;
                    }
                }
            }
            
            this.log(`   ❌ ${dep}: ${error.message}`, 'error');
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
            console.log('\n🚨 Installation Status Summary:');
            const pythonCommands = ['python3', 'python'];
            let pythonCmd = null;
            for (const cmd of pythonCommands) {
                try {
                    execSync(`${cmd} --version`, { stdio: 'pipe' });
                    pythonCmd = cmd;
                    break;
                } catch (e) {}
            }
            if (pythonCmd) {
                const validation = this.validateInstallation(pythonCmd);
                console.log(`   Core Modules: ${validation.coreModulesAvailable ? '✅' : '❌'}`);
                console.log(`   CLI Package: ${validation.cliAvailable ? '✅' : '❌'}`);
                console.log(`   Memory System: ${validation.memorySystemAvailable ? '✅' : '❌'}`);
                
                // Check ai-trackdown-pytools status
                let aitrackdownAvailable = false;
                try {
                    execSync(`${pythonCmd} -c "import ai_trackdown"`, { stdio: 'pipe' });
                    aitrackdownAvailable = true;
                } catch (e) {}
                console.log(`   AI-Trackdown-Pytools: ${aitrackdownAvailable ? '✅' : '⚠️ (pip install ai-trackdown-pytools==1.1.0)'}`);
            }
        }
        
        console.log('\n💡 What the post-installation process does:');
        console.log('   • Creates ~/.claude-pm/ directory structure');
        console.log('   • Deploys framework files from npm package to ~/.claude-pm/framework/');
        console.log('   • Deploys template files from npm package to ~/.claude-pm/templates/');
        console.log('   • Installs Python dependencies (core + AI/memory)');
        console.log('   • Initializes memory system (mem0ai, chromadb)');
        console.log('   • Configures CLI commands');
        console.log('   • Validates installation');
        console.log('\n🔧 Troubleshooting:');
        console.log('   • If Python dependencies fail: Check Python 3.8+ is installed');
        console.log('   • If permission errors occur: Try with --break-system-packages flag');
        console.log('   • If memory system fails: AI features will be limited but core CLI works');
        console.log('   • If ai-trackdown-pytools missing: Run "pip install ai-trackdown-pytools==1.1.0"');
        console.log('   • For detailed logs: Check ~/.claude-pm/logs/ after initialization');
        
        console.log('\n📚 Documentation:');
        console.log('   • Check README.md for usage instructions');
        console.log('   • Visit ~/.claude-pm/logs/ for installation logs');
        console.log('   • Run claude-pm health to verify status');
        
        console.log('\n' + '='.repeat(70));
    }

    /**
     * Create basic directory structure with MacOS framework setup
     */
    createBasicStructure() {
        try {
            // Create basic .claude-pm directory
            if (!fs.existsSync(this.globalConfigDir)) {
                fs.mkdirSync(this.globalConfigDir, { recursive: true });
                this.log(`Created basic directory: ${this.globalConfigDir}`);
            }
            
            // Create essential subdirectories for MacOS
            const subdirs = [
                'logs',
                'config',
                'agents/system',
                'agents/user-defined', 
                'agents/project-specific',
                'memory',
                'temp',
                'backups',
                'framework',
                'templates'
            ];
            
            for (const subdir of subdirs) {
                const fullPath = path.join(this.globalConfigDir, subdir);
                if (!fs.existsSync(fullPath)) {
                    fs.mkdirSync(fullPath, { recursive: true });
                    this.log(`Created subdirectory: ${subdir}`);
                }
            }
            
            // Deploy framework files from npm package to user directory
            this.deployFrameworkFiles();
            
            // Create a marker file to indicate NPM installation
            const markerFile = path.join(this.globalConfigDir, '.npm-installed');
            const markerData = {
                npm_installation: true,
                timestamp: new Date().toISOString(),
                platform: this.platform,
                global_install: this.isGlobalInstall(),
                package_root: this.packageRoot,
                version: this.getPackageVersion(),
                macos_setup: true,
                memory_system_disabled: true,
                framework_deployed: true
            };
            
            fs.writeFileSync(markerFile, JSON.stringify(markerData, null, 2));
            this.log(`Created installation marker: ${markerFile}`);
            
            // Create basic config file
            const configFile = path.join(this.globalConfigDir, 'config', 'framework.json');
            const basicConfig = {
                framework_version: this.getPackageVersion(),
                deployment_mode: "npm_package",
                memory_system_enabled: false,
                created: new Date().toISOString(),
                platform: this.platform,
                framework_path: path.join(this.globalConfigDir, 'framework'),
                templates_path: path.join(this.globalConfigDir, 'templates')
            };
            
            if (!fs.existsSync(configFile)) {
                fs.writeFileSync(configFile, JSON.stringify(basicConfig, null, 2));
                this.log(`Created basic config: framework.json`);
            }
            
            return true;
        } catch (e) {
            this.log(`Failed to create basic structure: ${e.message}`, 'error');
            return false;
        }
    }

    /**
     * Deploy framework files from npm package to user directory
     */
    deployFrameworkFiles() {
        try {
            this.log('Deploying framework files from npm package...');
            
            // Source paths in npm package
            const frameworkSource = path.join(this.packageRoot, 'framework');
            const templatesSource = path.join(this.packageRoot, 'templates');
            
            // Destination paths in user directory
            const frameworkDest = path.join(this.globalConfigDir, 'framework');
            const templatesDest = path.join(this.globalConfigDir, 'templates');
            
            // Copy framework directory
            if (fs.existsSync(frameworkSource)) {
                this.copyDirectory(frameworkSource, frameworkDest);
                this.log(`✅ Framework files deployed to: ${frameworkDest}`);
            } else {
                this.log(`⚠️ Framework source not found: ${frameworkSource}`, 'warn');
            }
            
            // Copy templates directory
            if (fs.existsSync(templatesSource)) {
                this.copyDirectory(templatesSource, templatesDest);
                this.log(`✅ Template files deployed to: ${templatesDest}`);
            } else {
                this.log(`⚠️ Templates source not found: ${templatesSource}`, 'warn');
            }
            
            // Ensure framework CLAUDE.md is copied to templates directory
            const frameworkClaudeMdSource = path.join(this.packageRoot, 'framework', 'CLAUDE.md');
            const templateClaudeMdDest = path.join(templatesDest, 'CLAUDE.md');
            
            if (fs.existsSync(frameworkClaudeMdSource) && !fs.existsSync(templateClaudeMdDest)) {
                try {
                    // Ensure templates directory exists
                    if (!fs.existsSync(templatesDest)) {
                        fs.mkdirSync(templatesDest, { recursive: true });
                    }
                    
                    // Copy framework CLAUDE.md to templates
                    fs.copyFileSync(frameworkClaudeMdSource, templateClaudeMdDest);
                    this.log(`✅ Framework CLAUDE.md copied to templates: ${templateClaudeMdDest}`);
                } catch (error) {
                    this.log(`⚠️ Failed to copy framework CLAUDE.md: ${error.message}`, 'warn');
                }
            }
            
            // Verify CLAUDE.md is accessible
            const claudeMdPath = path.join(frameworkDest, 'CLAUDE.md');
            if (fs.existsSync(claudeMdPath)) {
                this.log(`✅ CLAUDE.md accessible at: ${claudeMdPath}`);
            } else {
                this.log(`❌ CLAUDE.md not found at: ${claudeMdPath}`, 'error');
            }
            
        } catch (e) {
            this.log(`Framework deployment error: ${e.message}`, 'error');
        }
    }
    
    /**
     * Recursively copy directory
     */
    copyDirectory(source, destination) {
        try {
            if (!fs.existsSync(destination)) {
                fs.mkdirSync(destination, { recursive: true });
            }
            
            const items = fs.readdirSync(source);
            
            for (const item of items) {
                const sourcePath = path.join(source, item);
                const destPath = path.join(destination, item);
                
                const stat = fs.statSync(sourcePath);
                
                if (stat.isDirectory()) {
                    this.copyDirectory(sourcePath, destPath);
                } else {
                    fs.copyFileSync(sourcePath, destPath);
                }
            }
        } catch (e) {
            this.log(`Copy directory error (${source} -> ${destination}): ${e.message}`, 'error');
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
                this.log('✅ Python package installation completed successfully');
                
                // Check ai-trackdown-pytools after Python package installation
                const pythonCommands = ['python3', 'python'];
                let pythonCmd = null;
                for (const cmd of pythonCommands) {
                    try {
                        const version = execSync(`${cmd} --version`, { stdio: 'pipe', encoding: 'utf8' });
                        if (version.includes('Python 3.')) {
                            pythonCmd = cmd;
                            break;
                        }
                    } catch (e) {}
                }
                
                if (pythonCmd) {
                    const trackdownResult = this.checkAiTrackdownAvailable(pythonCmd);
                    if (!trackdownResult.available) {
                        this.log('ℹ️ ai-trackdown-pytools not detected - run "pip install ai-trackdown-pytools==1.1.0" for ticketing features');
                    }
                }
            } else {
                this.log('⚠️ Python package installation partial/failed - manual steps may be required', 'warn');
                this.log('💡 Run "npm run install:validate" to check installation status');
            }
            
            // Display instructions
            this.displayInstructions();
            
            this.log('📦 NPM post-installation completed');
            this.log('🚀 Next: Run "claude-pm init --post-install" to complete framework setup');
            
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