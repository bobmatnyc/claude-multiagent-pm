#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Post-Install Hook
 * 
 * Runs after NPM package installation to set up the framework
 * in the user's environment and configure platform-specific features.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class PostInstallSetup {
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
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
    }

    /**
     * Check if we're in a global npm installation
     */
    isGlobalInstall() {
        const npmConfigPrefix = process.env.npm_config_prefix;
        const packagePath = this.packageRoot;
        
        return npmConfigPrefix && packagePath.includes(npmConfigPrefix);
    }

    /**
     * Create global configuration directory
     */
    async createGlobalConfig() {
        try {
            await fs.mkdir(this.globalConfigDir, { recursive: true });
            
            const config = {
                version: require('../package.json').version,
                installType: this.isGlobalInstall() ? 'global' : 'local',
                installDate: new Date().toISOString(),
                platform: this.platform,
                packageRoot: this.packageRoot,
                paths: {
                    framework: path.join(this.packageRoot, 'lib', 'framework'),
                    templates: path.join(this.packageRoot, 'lib', 'templates'),
                    schemas: path.join(this.packageRoot, 'lib', 'schemas'),
                    bin: path.join(this.packageRoot, 'bin')
                }
            };
            
            const configPath = path.join(this.globalConfigDir, 'config.json');
            await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            
            this.log(`Global configuration created at: ${configPath}`);
            
        } catch (error) {
            this.log(`Failed to create global config: ${error.message}`, 'warn');
        }
    }

    /**
     * Copy framework to lib directory
     */
    async prepareFrameworkLib() {
        const frameworkSource = path.join(this.packageRoot, 'claude_pm');
        const frameworkTarget = path.join(this.packageRoot, 'lib', 'framework', 'claude_pm');
        
        if (!fsSync.existsSync(frameworkSource)) {
            this.log('Framework source not found, skipping lib preparation', 'warn');
            return;
        }
        
        try {
            await fs.mkdir(path.dirname(frameworkTarget), { recursive: true });
            await this.copyDirectory(frameworkSource, frameworkTarget);
            
            // Copy additional framework files
            const additionalFiles = [
                'requirements',
                'config',
                'docs',
                'templates',
                'schemas'
            ];
            
            for (const file of additionalFiles) {
                const sourcePath = path.join(this.packageRoot, file);
                const targetPath = path.join(this.packageRoot, 'lib', 'framework', file);
                
                if (fsSync.existsSync(sourcePath)) {
                    const stat = await fs.stat(sourcePath);
                    if (stat.isDirectory()) {
                        await this.copyDirectory(sourcePath, targetPath);
                    } else {
                        await fs.copyFile(sourcePath, targetPath);
                    }
                }
            }
            
            this.log('Framework prepared in lib directory');
            
        } catch (error) {
            this.log(`Failed to prepare framework lib: ${error.message}`, 'error');
        }
    }

    /**
     * Set up installation templates
     */
    async prepareTemplates() {
        const templatesSource = path.join(this.packageRoot, 'templates');
        const templatesTarget = path.join(this.packageRoot, 'lib', 'templates');
        
        if (!fsSync.existsSync(templatesSource)) {
            // Create default templates if none exist
            await fs.mkdir(templatesTarget, { recursive: true });
            
            const defaultTemplate = {
                name: "basic-project",
                description: "Basic Claude PM project template",
                files: {
                    "CLAUDE.md": "# Claude PM Project\n\nProject managed by Claude Multi-Agent PM Framework",
                    "README.md": "# Project Name\n\nDescription of your project.",
                    "trackdown/BACKLOG.md": "# Project Backlog\n\n## Current Sprint\n\n## Backlog Items\n"
                }
            };
            
            await fs.writeFile(
                path.join(templatesTarget, 'basic-project.json'),
                JSON.stringify(defaultTemplate, null, 2)
            );
            
            this.log('Default templates created');
        } else {
            try {
                await this.copyDirectory(templatesSource, templatesTarget);
                this.log('Templates prepared');
            } catch (error) {
                this.log(`Failed to prepare templates: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Set up configuration schemas
     */
    async prepareSchemas() {
        const schemasSource = path.join(this.packageRoot, 'schemas');
        const schemasTarget = path.join(this.packageRoot, 'lib', 'schemas');
        
        if (!fsSync.existsSync(schemasSource)) {
            // Create default schemas
            await fs.mkdir(schemasTarget, { recursive: true });
            
            const configSchema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Claude PM Configuration",
                "type": "object",
                "properties": {
                    "version": { "type": "string" },
                    "framework": {
                        "type": "object",
                        "properties": {
                            "path": { "type": "string" },
                            "pythonCmd": { "type": "string", "default": "python3" }
                        }
                    }
                }
            };
            
            await fs.writeFile(
                path.join(schemasTarget, 'config.schema.json'),
                JSON.stringify(configSchema, null, 2)
            );
            
            this.log('Default schemas created');
        } else {
            try {
                await this.copyDirectory(schemasSource, schemasTarget);
                this.log('Schemas prepared');
            } catch (error) {
                this.log(`Failed to prepare schemas: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Create platform-specific setup
     */
    async platformSetup() {
        if (this.platform === 'win32') {
            await this.windowsSetup();
        } else {
            await this.unixSetup();
        }
    }

    /**
     * Windows-specific setup
     */
    async windowsSetup() {
        this.log('Configuring for Windows platform');
        
        // Windows doesn't need special setup for now
        // Future: Could set up Windows-specific paths or registry entries
    }

    /**
     * Unix-specific setup (Linux/macOS)
     */
    async unixSetup() {
        this.log('Configuring for Unix platform');
        
        // Make CLI scripts executable
        const binPath = path.join(this.packageRoot, 'bin', 'claude-pm');
        if (fsSync.existsSync(binPath)) {
            try {
                await fs.chmod(binPath, '755');
                this.log('CLI script made executable');
            } catch (error) {
                this.log(`Failed to make CLI executable: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Validate installation
     */
    async validateInstallation() {
        const requiredPaths = [
            path.join(this.packageRoot, 'bin', 'claude-pm'),
            path.join(this.packageRoot, 'lib'),
            path.join(this.packageRoot, 'install')
        ];
        
        for (const requiredPath of requiredPaths) {
            if (!fsSync.existsSync(requiredPath)) {
                throw new Error(`Required path missing: ${requiredPath}`);
            }
        }
        
        this.log('Installation validation passed');
    }

    /**
     * Show post-install instructions
     */
    showInstructions() {
        console.log('\n🎉 Claude Multi-Agent PM Framework installed successfully!\n');
        
        if (this.isGlobalInstall()) {
            console.log('Global installation detected. You can now use:');
            console.log('  claude-pm --help');
            console.log('  claude-pm health status');
            console.log('  claude-pm project create my-project');
        } else {
            console.log('Local installation detected. You can use:');
            console.log('  npx claude-pm --help');
            console.log('  npx claude-pm health status');
            console.log('  Or add to your package.json scripts');
        }
        
        console.log('\nConfiguration location:');
        console.log(`  ${this.globalConfigDir}`);
        
        console.log('\nNext steps:');
        console.log('1. Run "claude-pm health status" to verify installation');
        console.log('2. Create a new project with "claude-pm project create <name>"');
        console.log('3. Visit https://github.com/bobmatnyc/claude-multiagent-pm for documentation');
        console.log('');
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
     * Main post-install process
     */
    async run() {
        try {
            this.log('Starting Claude PM Framework post-install setup');
            
            await this.createGlobalConfig();
            await this.prepareFrameworkLib();
            await this.prepareTemplates();
            await this.prepareSchemas();
            await this.platformSetup();
            await this.validateInstallation();
            
            this.log('Post-install setup completed successfully');
            this.showInstructions();
            
        } catch (error) {
            this.log(`Post-install setup failed: ${error.message}`, 'error');
            console.error('\nIf you encounter issues, please:');
            console.error('1. Check that Node.js 16+ and Python 3.8+ are installed');
            console.error('2. Ensure you have write permissions to the installation directory');
            console.error('3. Report issues at: https://github.com/bobmatnyc/claude-multiagent-pm/issues');
            
            // Don't fail the installation, just warn
            process.exit(0);
        }
    }
}

// Run post-install setup
if (require.main === module) {
    const setup = new PostInstallSetup();
    setup.run();
}

module.exports = PostInstallSetup;