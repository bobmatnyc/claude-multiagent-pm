#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Universal Installation Script
 * 
 * Handles installation and deployment of the Claude PM Framework
 * to any target directory with platform-specific optimizations.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { spawn, execSync } = require('child_process');

class ClaudePMInstaller {
    constructor(options = {}) {
        this.targetDir = options.targetDir || process.cwd();
        this.platform = os.platform();
        this.verbose = options.verbose || false;
        this.skipValidation = options.skipValidation || false;
        
        this.packageDir = path.join(__dirname, '..');
        this.frameworkSource = path.join(this.packageDir, 'lib', 'framework');
        this.templatesSource = path.join(this.packageDir, 'lib', 'templates');
        this.schemasSource = path.join(this.packageDir, 'lib', 'schemas');
    }

    /**
     * Log message with optional verbose filtering
     */
    log(message, force = false) {
        if (this.verbose || force) {
            console.log(`[Claude PM Installer] ${message}`);
        }
    }

    /**
     * Validate environment requirements
     */
    async validateEnvironment() {
        if (this.skipValidation) {
            this.log('Skipping environment validation');
            return true;
        }

        this.log('Validating environment requirements...', true);

        // Check Node.js version
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        
        if (majorVersion < 16) {
            throw new Error(`Node.js 16.0.0 or higher required. Found: ${nodeVersion}`);
        }
        
        this.log(`✓ Node.js ${nodeVersion} detected`);

        // Check Python availability and version
        try {
            let pythonCmd = 'python3';
            let pythonVersion;
            
            try {
                pythonVersion = execSync(`${pythonCmd} --version`, { encoding: 'utf8' }).trim();
            } catch (error) {
                pythonCmd = 'python';
                pythonVersion = execSync(`${pythonCmd} --version`, { encoding: 'utf8' }).trim();
            }
            
            const versionMatch = pythonVersion.match(/Python (\d+)\.(\d+)/);
            if (!versionMatch) {
                throw new Error('Unable to parse Python version');
            }
            
            const [, major, minor] = versionMatch.map(Number);
            if (major < 3 || (major === 3 && minor < 8)) {
                throw new Error(`Python 3.8+ required. Found: ${pythonVersion}`);
            }
            
            this.log(`✓ ${pythonVersion} detected`);
            this.pythonCmd = pythonCmd;
            
        } catch (error) {
            throw new Error('Python 3.8+ is required but not found');
        }

        // Check disk space (require at least 100MB)
        try {
            const stats = await fs.stat(this.targetDir);
            // Basic check - in real implementation, you'd check available space
            this.log('✓ Target directory accessible');
        } catch (error) {
            throw new Error(`Target directory not accessible: ${this.targetDir}`);
        }

        this.log('Environment validation completed', true);
        return true;
    }

    /**
     * Copy framework files to target directory
     */
    async copyFramework() {
        this.log('Copying framework files...', true);
        
        const targetFramework = path.join(this.targetDir, 'claude_pm');
        
        try {
            await this.copyDirectory(this.frameworkSource, targetFramework);
            this.log(`✓ Framework copied to ${targetFramework}`);
        } catch (error) {
            throw new Error(`Failed to copy framework: ${error.message}`);
        }
    }

    /**
     * Copy templates to target directory
     */
    async copyTemplates() {
        this.log('Copying templates...', true);
        
        const targetTemplates = path.join(this.targetDir, 'templates');
        
        try {
            await this.copyDirectory(this.templatesSource, targetTemplates);
            this.log(`✓ Templates copied to ${targetTemplates}`);
        } catch (error) {
            throw new Error(`Failed to copy templates: ${error.message}`);
        }
    }

    /**
     * Copy schemas to target directory
     */
    async copySchemas() {
        this.log('Copying schemas...', true);
        
        const targetSchemas = path.join(this.targetDir, 'schemas');
        
        try {
            await this.copyDirectory(this.schemasSource, targetSchemas);
            this.log(`✓ Schemas copied to ${targetSchemas}`);
        } catch (error) {
            throw new Error(`Failed to copy schemas: ${error.message}`);
        }
    }

    /**
     * Create configuration files
     */
    async createConfiguration() {
        this.log('Creating configuration files...', true);
        
        const configDir = path.join(this.targetDir, 'config');
        await fs.mkdir(configDir, { recursive: true });
        
        const config = {
            version: require('../package.json').version,
            installDate: new Date().toISOString(),
            platform: this.platform,
            targetDir: this.targetDir,
            pythonCmd: this.pythonCmd || 'python3',
            framework: {
                path: path.join(this.targetDir, 'claude_pm'),
                templates: path.join(this.targetDir, 'templates'),
                schemas: path.join(this.targetDir, 'schemas')
            }
        };
        
        const configPath = path.join(configDir, 'claude-pm.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));
        
        this.log(`✓ Configuration created at ${configPath}`);
    }

    /**
     * Install Python dependencies
     */
    async installPythonDependencies() {
        this.log('Installing Python dependencies...', true);
        
        const requirementsPath = path.join(this.targetDir, 'claude_pm', 'requirements', 'base.txt');
        
        if (!fsSync.existsSync(requirementsPath)) {
            this.log('⚠ No requirements file found, skipping Python dependencies');
            return;
        }
        
        return new Promise((resolve, reject) => {
            const pip = spawn(this.pythonCmd, ['-m', 'pip', 'install', '-r', requirementsPath], {
                stdio: this.verbose ? 'inherit' : 'pipe',
                cwd: this.targetDir
            });
            
            pip.on('close', (code) => {
                if (code === 0) {
                    this.log('✓ Python dependencies installed');
                    resolve();
                } else {
                    reject(new Error(`Failed to install Python dependencies (exit code: ${code})`));
                }
            });
            
            pip.on('error', (error) => {
                reject(new Error(`Failed to install Python dependencies: ${error.message}`));
            });
        });
    }

    /**
     * Set up platform-specific scripts
     */
    async setupPlatformScripts() {
        this.log('Setting up platform-specific scripts...', true);
        
        const scriptsDir = path.join(this.targetDir, 'scripts');
        await fs.mkdir(scriptsDir, { recursive: true });
        
        if (this.platform === 'win32') {
            await this.createWindowsScripts(scriptsDir);
        } else {
            await this.createUnixScripts(scriptsDir);
        }
        
        this.log('✓ Platform scripts configured');
    }

    /**
     * Create Windows-specific scripts
     */
    async createWindowsScripts(scriptsDir) {
        const startScript = `@echo off
echo Starting Claude PM Framework...
cd /d "${this.targetDir}"
${this.pythonCmd} claude_pm\\cli.py %*`;
        
        await fs.writeFile(path.join(scriptsDir, 'claude-pm.bat'), startScript);
    }

    /**
     * Create Unix-specific scripts
     */
    async createUnixScripts(scriptsDir) {
        const startScript = `#!/bin/bash
# Claude PM Framework startup script
cd "${this.targetDir}"
exec ${this.pythonCmd} claude_pm/cli.py "$@"`;
        
        const scriptPath = path.join(scriptsDir, 'claude-pm');
        await fs.writeFile(scriptPath, startScript);
        await fs.chmod(scriptPath, '755');
    }

    /**
     * Perform post-installation setup
     */
    async postInstallSetup() {
        this.log('Performing post-installation setup...', true);
        
        // Create logs directory
        const logsDir = path.join(this.targetDir, 'logs');
        await fs.mkdir(logsDir, { recursive: true });
        
        // Create temp directory for framework operations
        const tempDir = path.join(this.targetDir, 'temp');
        await fs.mkdir(tempDir, { recursive: true });
        
        // Create initial trackdown structure
        const trackdownDir = path.join(this.targetDir, 'trackdown');
        await fs.mkdir(trackdownDir, { recursive: true });
        
        this.log('✓ Post-installation setup completed');
    }

    /**
     * Recursively copy directory
     */
    async copyDirectory(src, dest) {
        await fs.mkdir(dest, { recursive: true });
        
        const items = await fs.readdir(src);
        
        for (const item of items) {
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            
            const stat = await fs.stat(srcPath);
            
            if (stat.isDirectory()) {
                await this.copyDirectory(srcPath, destPath);
            } else {
                await fs.copyFile(srcPath, destPath);
            }
        }
    }

    /**
     * Main installation process
     */
    async install() {
        try {
            this.log(`Starting Claude PM Framework installation to: ${this.targetDir}`, true);
            
            await this.validateEnvironment();
            await this.copyFramework();
            await this.copyTemplates();
            await this.copySchemas();
            await this.createConfiguration();
            await this.setupPlatformScripts();
            await this.postInstallSetup();
            
            // Install Python dependencies (optional, may fail in some environments)
            try {
                await this.installPythonDependencies();
            } catch (error) {
                this.log(`⚠ Warning: ${error.message}`);
                this.log('You may need to install Python dependencies manually');
            }
            
            this.log('🎉 Claude PM Framework installation completed successfully!', true);
            this.log(`Framework location: ${path.join(this.targetDir, 'claude_pm')}`, true);
            this.log(`Configuration: ${path.join(this.targetDir, 'config', 'claude-pm.json')}`, true);
            
            return true;
            
        } catch (error) {
            this.log(`❌ Installation failed: ${error.message}`, true);
            throw error;
        }
    }
}

// CLI interface when run directly
if (require.main === module) {
    const args = process.argv.slice(2);
    
    const options = {
        targetDir: process.cwd(),
        verbose: args.includes('--verbose') || args.includes('-v'),
        skipValidation: args.includes('--skip-validation')
    };
    
    // Parse target directory
    const targetIndex = args.findIndex(arg => arg === '--target' || arg === '-t');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
        options.targetDir = path.resolve(args[targetIndex + 1]);
    }
    
    const installer = new ClaudePMInstaller(options);
    
    installer.install()
        .then(() => {
            process.exit(0);
        })
        .catch((error) => {
            console.error('Installation failed:', error.message);
            process.exit(1);
        });
}

module.exports = ClaudePMInstaller;