#!/usr/bin/env node

/**
 * Enhanced NPM Postinstall Script with Global Install Support
 * Addresses NPM 7+ postinstall execution issues for global installations
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class EnhancedPostinstallHandler {
    constructor() {
        this.platform = os.platform();
        this.packageRoot = path.join(__dirname, '..');
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
        this.logFile = path.join(this.userHome, '.claude-pm-postinstall.log');
        this.startTime = Date.now();
        
        // Enhanced detection for global vs local install
        this.installType = this.detectInstallationType();
        this.npmVersion = this.getNpmVersion();
        this.isProblematicNpm = this.isProblematicNpmVersion();
    }

    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        const logEntry = `${prefix} [${timestamp}] ${message}`;
        
        console.log(logEntry);
        
        try {
            fsSync.appendFileSync(this.logFile, logEntry + '\n');
        } catch (error) {
            // Fail silently if logging fails
        }
    }

    detectInstallationType() {
        const npmConfigPrefix = process.env.npm_config_prefix;
        const packagePath = process.cwd();
        const npmRoot = process.env.npm_config_globaldir || process.env.npm_root;
        
        // Enhanced global installation detection
        const globalIndicators = {
            npmPrefix: npmConfigPrefix && packagePath.includes(npmConfigPrefix),
            npmGlobalDir: npmRoot && packagePath.includes(npmRoot),
            nodeModulesGlobal: packagePath.includes('node_modules') && (
                packagePath.includes('/.npm-global/') ||
                packagePath.includes('/lib/node_modules/') ||
                packagePath.includes('/.nvm/versions/node/') ||
                packagePath.includes('/usr/local/lib/node_modules/') ||
                packagePath.includes('/opt/homebrew/lib/node_modules/')
            )
        };
        
        const isGlobal = Object.values(globalIndicators).some(Boolean);
        return isGlobal ? 'global' : 'local';
    }

    getNpmVersion() {
        try {
            return execSync('npm --version', { encoding: 'utf8' }).trim();
        } catch (error) {
            return null;
        }
    }

    isProblematicNpmVersion() {
        if (!this.npmVersion) return false;
        const majorVersion = parseInt(this.npmVersion.split('.')[0]);
        return majorVersion >= 7; // NPM 7+ has postinstall issues
    }

    async ensureDirectoryExists(dirPath) {
        try {
            await fs.mkdir(dirPath, { recursive: true });
            return true;
        } catch (error) {
            this.log(`Failed to create directory ${dirPath}: ${error.message}`, 'error');
            return false;
        }
    }

    async createMinimalSetup() {
        this.log('🔧 Creating minimal framework setup...');
        this.log('   📁 Setting up directory structure');
        
        // Ensure .claude-pm directory exists
        const success = await this.ensureDirectoryExists(this.globalConfigDir);
        if (!success) {
            throw new Error('Failed to create .claude-pm directory');
        }
        this.log('   ✅ Created .claude-pm directory');
        
        // Create basic structure
        const basicDirs = [
            path.join(this.globalConfigDir, 'scripts'),
            path.join(this.globalConfigDir, 'templates'),
            path.join(this.globalConfigDir, 'agents'),
            path.join(this.globalConfigDir, 'config')
        ];
        
        let dirCount = 0;
        for (const dir of basicDirs) {
            await this.ensureDirectoryExists(dir);
            dirCount++;
            this.log(`   📂 [${dirCount}/${basicDirs.length}] Created: ${path.relative(this.globalConfigDir, dir)}`);
        }
        
        // Create a basic config file
        this.log('   📄 Writing configuration file...');
        const configFile = path.join(this.globalConfigDir, 'config', 'postinstall.json');
        const configData = {
            version: require('../package.json').version,
            installType: this.installType,
            npmVersion: this.npmVersion,
            timestamp: new Date().toISOString(),
            platform: this.platform,
            postinstallExecuted: true
        };
        
        try {
            await fs.writeFile(configFile, JSON.stringify(configData, null, 2));
            this.log('   ✅ Configuration file created successfully');
        } catch (error) {
            this.log(`   ❌ Failed to create config file: ${error.message}`, 'error');
        }
        
        this.log('✅ Minimal framework setup completed');
        return true;
    }

    async runFullInstallation() {
        this.log('🚀 Running full installation via original postinstall.js...');
        this.log('   ⚙️  Initializing comprehensive setup process');
        
        try {
            // Import and run the original postinstall
            this.log('   📦 Loading postinstall module...');
            const PostInstallSetup = require('./postinstall.js');
            const setup = new PostInstallSetup();
            
            this.log('   🔄 Executing comprehensive installation...');
            await setup.run();
            
            this.log('   ✅ Full installation completed successfully');
            return true;
        } catch (error) {
            this.log(`   ❌ Full installation failed: ${error.message}`, 'error');
            this.log('   ⚠️  Falling back to minimal setup mode');
            return false;
        }
    }

    async createExecutionMarker() {
        const markerFile = path.join(this.userHome, '.claude-pm-postinstall-executed');
        const markerData = {
            timestamp: new Date().toISOString(),
            installType: this.installType,
            npmVersion: this.npmVersion,
            platform: this.platform,
            nodeVersion: process.version,
            executionTime: Date.now() - this.startTime,
            success: true
        };
        
        try {
            await fs.writeFile(markerFile, JSON.stringify(markerData, null, 2));
            this.log('✅ Created execution marker');
        } catch (error) {
            this.log(`Failed to create execution marker: ${error.message}`, 'error');
        }
    }

    async run() {
        console.log('\n' + '='.repeat(60));
        console.log('📦 Claude Multi-Agent PM Framework - Enhanced Postinstall');
        console.log('='.repeat(60));
        
        this.log('🚀 Starting Enhanced NPM Postinstall Handler');
        this.log(`   📌 Version: ${require('../package.json').version}`);
        this.log(`   📍 Install Type: ${this.installType}`);
        this.log(`   📋 NPM Version: ${this.npmVersion}`);
        this.log(`   🖥️  Platform: ${this.platform}`);
        
        if (this.isProblematicNpm && this.installType === 'global') {
            this.log('⚠️  NPM 7+ global install detected - using enhanced compatibility mode');
        }
        
        try {
            this.log('\n🔄 Phase 1: Minimal Setup');
            console.log('   Setting up essential directory structure...');
            await this.createMinimalSetup();
            
            this.log('\n🔄 Phase 2: Full Installation');
            // Try full installation if we're in a safe environment
            if (this.installType === 'local' || !this.isProblematicNpm) {
                console.log('   Running comprehensive installation...');
                const fullInstallSuccess = await this.runFullInstallation();
                if (!fullInstallSuccess) {
                    this.log('⚠️  Full installation failed, but minimal setup completed', 'warn');
                    console.log('   ⚠️  Some features may be limited - run "claude-pm init" to complete setup');
                }
            } else {
                this.log('⚠️  Skipping full installation due to NPM/global install compatibility issues', 'warn');
                this.log('✨ Framework will initialize automatically on first use');
                console.log('   ✨ Framework will initialize automatically on first use');
            }
            
            this.log('\n🔄 Phase 3: Finalization');
            console.log('   Creating execution markers...');
            await this.createExecutionMarker();
            
            console.log('\n' + '='.repeat(60));
            console.log('✅ Enhanced postinstall completed successfully!');
            console.log('📁 Log file: ' + this.logFile);
            console.log('🚀 Ready to use: claude-pm --help');
            console.log('='.repeat(60));
            
        } catch (error) {
            console.log('\n' + '='.repeat(60));
            console.log('❌ Enhanced postinstall failed!');
            console.log('='.repeat(60));
            
            this.log(`Enhanced postinstall failed: ${error.message}`, 'error');
            
            // Create error marker
            const errorMarkerFile = path.join(this.userHome, '.claude-pm-postinstall-error');
            try {
                await fs.writeFile(errorMarkerFile, JSON.stringify({
                    timestamp: new Date().toISOString(),
                    error: error.message,
                    installType: this.installType,
                    npmVersion: this.npmVersion
                }, null, 2));
            } catch (writeError) {
                // Fail silently
            }
            
            throw error;
        }
    }
}

// Run enhanced postinstall
if (require.main === module) {
    const handler = new EnhancedPostinstallHandler();
    handler.run().catch(error => {
        console.error('❌ Enhanced postinstall failed:', error.message);
        process.exit(1);
    });
}

module.exports = EnhancedPostinstallHandler;