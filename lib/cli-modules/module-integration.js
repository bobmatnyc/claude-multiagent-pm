#!/usr/bin/env node

/**
 * Claude PM CLI Module Integration System
 * 
 * Provides the bridge between modular architecture and the monolithic claude-pm script.
 * Implements gradual migration, fallback mechanisms, and performance monitoring.
 * 
 * Part of ISS-0085: Module export/import system design
 */

const path = require('path');
const ModuleLoader = require('./module-loader');

class ModuleIntegrationSystem {
    constructor() {
        this.moduleLoader = new ModuleLoader();
        this.enableModular = true;
        this.fallbackMode = false;
        this.loadedModules = new Map();
        this.performanceMetrics = {
            totalLoadTime: 0,
            moduleLoadTimes: new Map(),
            memoryUsage: new Map(),
            fallbackCount: 0
        };
    }

    /**
     * Initialize the modular system
     * @param {Object} options - Initialization options
     */
    async init(options = {}) {
        this.enableModular = options.enableModular !== false;
        this.fallbackMode = options.fallbackMode || false;
        
        if (this.enableModular) {
            console.log('🔧 Initializing modular CLI system...');
        } else {
            console.log('📄 Running in monolithic mode');
        }
    }

    /**
     * Resolve version using modular or fallback approach
     * @returns {string} Resolved version
     */
    async resolveVersion() {
        if (this.enableModular && !this.fallbackMode) {
            try {
                const versionModule = await this.moduleLoader.loadModule('version-resolver');
                const result = versionModule.main();
                this.recordSuccess('version-resolver');
                return result;
            } catch (error) {
                console.warn(`⚠️  Version resolver module failed: ${error.message}`);
                return this.fallbackVersionResolve();
            }
        } else {
            return this.fallbackVersionResolve();
        }
    }

    /**
     * Validate environment using modular or fallback approach
     * @returns {Object} Environment validation results
     */
    async validateEnvironment() {
        if (this.enableModular && !this.fallbackMode) {
            try {
                const envModule = await this.moduleLoader.loadModule('environment-validator');
                const result = envModule.main();
                this.recordSuccess('environment-validator');
                return result;
            } catch (error) {
                console.warn(`⚠️  Environment validator module failed: ${error.message}`);
                return this.fallbackEnvironmentValidation();
            }
        } else {
            return this.fallbackEnvironmentValidation();
        }
    }

    /**
     * Display help using modular or fallback approach
     * @param {string} version - Framework version
     */
    async displayHelp(version) {
        if (this.enableModular && !this.fallbackMode) {
            try {
                const displayModule = await this.moduleLoader.loadModule('display-manager');
                displayModule.main(version);
                this.recordSuccess('display-manager');
                return;
            } catch (error) {
                console.warn(`⚠️  Display manager module failed: ${error.message}`);
                this.fallbackDisplayHelp(version);
            }
        } else {
            this.fallbackDisplayHelp(version);
        }
    }

    /**
     * Display system info using modular or fallback approach
     * @param {Object} deploymentConfig - Deployment configuration
     * @param {string} version - Framework version
     */
    async displaySystemInfo(deploymentConfig, version) {
        if (this.enableModular && !this.fallbackMode) {
            try {
                const displayModule = await this.moduleLoader.loadModule('display-manager');
                displayModule.displaySystemInfo(deploymentConfig, version);
                this.recordSuccess('display-manager');
                return;
            } catch (error) {
                console.warn(`⚠️  Display manager module failed: ${error.message}`);
                this.fallbackDisplaySystemInfo(deploymentConfig, version);
            }
        } else {
            this.fallbackDisplaySystemInfo(deploymentConfig, version);
        }
    }

    /**
     * Display environment status using modular or fallback approach
     * @param {Object} environmentStatus - Environment status data
     */
    async displayEnvironmentStatus(environmentStatus) {
        if (this.enableModular && !this.fallbackMode) {
            try {
                const displayModule = await this.moduleLoader.loadModule('display-manager');
                displayModule.displayEnvironmentStatus(environmentStatus);
                this.recordSuccess('display-manager');
                return;
            } catch (error) {
                console.warn(`⚠️  Display manager module failed: ${error.message}`);
                this.fallbackDisplayEnvironmentStatus(environmentStatus);
            }
        } else {
            this.fallbackDisplayEnvironmentStatus(environmentStatus);
        }
    }

    /**
     * Get comprehensive status of modular system
     * @returns {Object} System status
     */
    getSystemStatus() {
        const moduleLoaderHealth = this.moduleLoader.healthCheck();
        const moduleLoaderStats = this.moduleLoader.getStats();

        return {
            modularEnabled: this.enableModular,
            fallbackMode: this.fallbackMode,
            loadedModules: Array.from(this.loadedModules.keys()),
            moduleLoaderHealth,
            moduleLoaderStats,
            performanceMetrics: {
                ...this.performanceMetrics,
                moduleLoadTimes: Object.fromEntries(this.performanceMetrics.moduleLoadTimes),
                memoryUsage: Object.fromEntries(this.performanceMetrics.memoryUsage)
            }
        };
    }

    /**
     * Record successful module usage
     * @param {string} moduleName - Name of the module
     */
    recordSuccess(moduleName) {
        if (!this.loadedModules.has(moduleName)) {
            this.loadedModules.set(moduleName, {
                firstLoad: Date.now(),
                useCount: 1,
                lastUsed: Date.now()
            });
        } else {
            const moduleInfo = this.loadedModules.get(moduleName);
            moduleInfo.useCount++;
            moduleInfo.lastUsed = Date.now();
        }
    }

    /**
     * Record fallback usage
     * @param {string} reason - Reason for fallback
     */
    recordFallback(reason) {
        this.performanceMetrics.fallbackCount++;
        console.log(`🔄 Using fallback: ${reason}`);
    }

    // ========================================================================================
    // FALLBACK IMPLEMENTATIONS (Monolithic Behavior)
    // ========================================================================================

    /**
     * Fallback version resolution (extracted from original bin/claude-pm)
     * @returns {string} Resolved version
     */
    fallbackVersionResolve() {
        this.recordFallback('Version resolver module unavailable');
        
        // Simplified version of original resolveVersion() function
        const fs = require('fs');
        const path = require('path');
        
        // Strategy 1: Try package.json
        const packagePaths = [
            path.join(__dirname, '../package.json'),
            path.join(__dirname, '../../package.json'),
            path.join(__dirname, '../../../package.json')
        ];
        
        for (const packagePath of packagePaths) {
            try {
                if (fs.existsSync(packagePath)) {
                    const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
                    if (pkg.name === '@bobmatnyc/claude-multiagent-pm' && pkg.version) {
                        return pkg.version;
                    }
                }
            } catch (e) {
                // Continue
            }
        }
        
        // Strategy 2: Try VERSION file
        const versionPaths = [
            path.join(__dirname, '../VERSION'),
            path.join(__dirname, '../../VERSION')
        ];
        
        for (const versionPath of versionPaths) {
            try {
                if (fs.existsSync(versionPath)) {
                    return fs.readFileSync(versionPath, 'utf8').trim();
                }
            } catch (e) {
                // Continue
            }
        }
        
        return 'unknown';
    }

    /**
     * Fallback environment validation
     * @returns {Object} Basic environment validation
     */
    fallbackEnvironmentValidation() {
        this.recordFallback('Environment validator module unavailable');
        
        const os = require('os');
        
        // Basic validation
        let pythonCmd = null;
        try {
            const { execSync } = require('child_process');
            execSync('python3 --version', { stdio: 'pipe', timeout: 5000 });
            pythonCmd = 'python3';
        } catch (e) {
            try {
                execSync('python --version', { stdio: 'pipe', timeout: 5000 });
                pythonCmd = 'python';
            } catch (e2) {
                // No Python found
            }
        }
        
        return {
            platform: {
                platform: os.platform(),
                arch: os.arch(),
                isWSL2: false // Simplified detection
            },
            python: pythonCmd,
            overall: !!pythonCmd,
            errors: pythonCmd ? [] : ['Python not available']
        };
    }

    /**
     * Fallback help display
     * @param {string} version - Framework version
     */
    fallbackDisplayHelp(version) {
        this.recordFallback('Display manager module unavailable');
        
        console.log(`Claude Multi-Agent PM Framework v${version}`);
        console.log('Universal CLI for Claude-powered project management');
        console.log('');
        console.log('USAGE:');
        console.log('  claude-pm [command] [options]');
        console.log('');
        console.log('OPTIONS:');
        console.log('  --version, -v    Show version');
        console.log('  --help, -h       Show help');
        console.log('  --system-info    Show system information');
        console.log('');
        console.log('For full help, try upgrading to the latest version.');
    }

    /**
     * Fallback system info display
     * @param {Object} deploymentConfig - Deployment configuration
     * @param {string} version - Framework version
     */
    fallbackDisplaySystemInfo(deploymentConfig, version) {
        this.recordFallback('Display manager module unavailable');
        
        const os = require('os');
        
        console.log('');
        console.log('Claude Multi-Agent PM Framework - System Information');
        console.log('='.repeat(50));
        console.log('');
        console.log(`Version: v${version}`);
        console.log(`Platform: ${os.platform()} (${os.arch()})`);
        console.log(`Node.js: ${process.version}`);
        console.log(`Working Directory: ${process.cwd()}`);
        
        const memUsage = process.memoryUsage();
        console.log(`Memory: ${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`);
        console.log('');
        console.log('For detailed system information, upgrade to the latest version.');
        console.log('');
    }

    /**
     * Fallback environment status display
     * @param {Object} environmentStatus - Environment status
     */
    fallbackDisplayEnvironmentStatus(environmentStatus) {
        this.recordFallback('Display manager module unavailable');
        
        console.log('');
        console.log('Environment Status (Basic)');
        console.log('='.repeat(30));
        
        if (environmentStatus.validation) {
            console.log(`Platform: ${environmentStatus.validation.platform.platform}`);
            console.log(`Python: ${environmentStatus.validation.python || 'Not found'}`);
            console.log(`Status: ${environmentStatus.validation.overall ? 'Ready' : 'Issues detected'}`);
        }
        
        console.log('');
        console.log('For detailed environment status, upgrade to the latest version.');
        console.log('');
    }

    /**
     * Cleanup all modules and resources
     */
    async cleanup() {
        console.log('🧹 Cleaning up modular system...');
        
        try {
            await this.moduleLoader.cleanup();
        } catch (error) {
            console.error(`❌ Error during cleanup: ${error.message}`);
        }
        
        this.loadedModules.clear();
        this.performanceMetrics = {
            totalLoadTime: 0,
            moduleLoadTimes: new Map(),
            memoryUsage: new Map(),
            fallbackCount: 0
        };
    }

    /**
     * Enable or disable modular mode
     * @param {boolean} enabled - Whether to enable modular mode
     */
    setModularMode(enabled) {
        this.enableModular = enabled;
        if (enabled) {
            console.log('✅ Modular mode enabled');
        } else {
            console.log('📄 Modular mode disabled - using monolithic fallback');
        }
    }

    /**
     * Force fallback mode for all operations
     * @param {boolean} force - Whether to force fallback mode
     */
    setFallbackMode(force) {
        this.fallbackMode = force;
        if (force) {
            console.log('🔄 Fallback mode enabled - modules will not be loaded');
        } else {
            console.log('⚡ Fallback mode disabled - modules will be used when available');
        }
    }
}

// Export for integration with bin/claude-pm
module.exports = ModuleIntegrationSystem;