#!/usr/bin/env node

/**
 * Claude PM CLI Module Loader
 * 
 * Provides dynamic loading infrastructure for modularized CLI components.
 * Implements graceful fallback to monolithic behavior if modules fail.
 * 
 * Part of ISS-0085: Modularize claude-pm script from monolithic 3,048-line file
 */

const fs = require('fs');
const path = require('path');

class ModuleLoader {
    constructor() {
        this.modulePath = __dirname;
        this.loadedModules = new Map();
        this.moduleCache = new Map();
        this.dependencies = new Map();
        this.memoryThreshold = 512 * 1024 * 1024; // 512MB per module
        this.enableFallback = true;
    }

    /**
     * Load a module with error handling and fallback support
     * @param {string} moduleName - Name of the module to load
     * @param {Object} options - Loading options
     * @returns {Object} Module instance or fallback behavior
     */
    async loadModule(moduleName, options = {}) {
        try {
            // Check cache first
            if (this.moduleCache.has(moduleName)) {
                return this.moduleCache.get(moduleName);
            }

            // Validate module exists
            const modulePath = path.join(this.modulePath, `${moduleName}.js`);
            if (!fs.existsSync(modulePath)) {
                throw new Error(`Module ${moduleName} not found at ${modulePath}`);
            }

            // Memory check before loading
            const initialMemory = process.memoryUsage();
            
            // Load module
            const moduleInstance = require(modulePath);
            
            // Validate module interface
            this.validateModuleInterface(moduleInstance, moduleName);
            
            // Check memory impact
            const postLoadMemory = process.memoryUsage();
            const memoryDelta = postLoadMemory.heapUsed - initialMemory.heapUsed;
            
            if (memoryDelta > this.memoryThreshold) {
                console.warn(`⚠️  Module ${moduleName} uses ${Math.round(memoryDelta / 1024 / 1024)}MB (threshold: ${Math.round(this.memoryThreshold / 1024 / 1024)}MB)`);
            }

            // Initialize module if it has init function
            if (typeof moduleInstance.init === 'function') {
                await moduleInstance.init(options);
            }

            // Cache successful load
            this.moduleCache.set(moduleName, moduleInstance);
            this.loadedModules.set(moduleName, {
                instance: moduleInstance,
                loadTime: Date.now(),
                memoryImpact: memoryDelta,
                options: options
            });

            console.log(`✅ Module ${moduleName} loaded successfully (${Math.round(memoryDelta / 1024)}KB)`);
            return moduleInstance;

        } catch (error) {
            console.error(`❌ Failed to load module ${moduleName}: ${error.message}`);
            
            if (this.enableFallback) {
                console.log(`🔄 Falling back to monolithic behavior for ${moduleName}`);
                return this.createFallbackModule(moduleName);
            } else {
                throw error;
            }
        }
    }

    /**
     * Validate module interface compliance
     * @param {Object} moduleInstance - The loaded module
     * @param {string} moduleName - Name for error reporting
     */
    validateModuleInterface(moduleInstance, moduleName) {
        const requiredMethods = ['main'];
        const optionalMethods = ['init', 'cleanup', 'getConfig'];
        
        for (const method of requiredMethods) {
            if (typeof moduleInstance[method] !== 'function') {
                throw new Error(`Module ${moduleName} missing required method: ${method}`);
            }
        }

        // Validate config if present
        if (moduleInstance.config && typeof moduleInstance.config !== 'object') {
            throw new Error(`Module ${moduleName} config must be an object`);
        }

        // Validate dependencies if present
        if (moduleInstance.dependencies && !Array.isArray(moduleInstance.dependencies)) {
            throw new Error(`Module ${moduleName} dependencies must be an array`);
        }
    }

    /**
     * Create fallback module that defers to monolithic implementation
     * @param {string} moduleName - Name of the module to create fallback for
     * @returns {Object} Fallback module interface
     */
    createFallbackModule(moduleName) {
        return {
            main: async (...args) => {
                console.warn(`⚠️  Using fallback for ${moduleName} - consider investigating module load failure`);
                // Return indication that monolithic fallback should be used
                return { useFallback: true, moduleName: moduleName };
            },
            config: { fallback: true },
            dependencies: [],
            cleanup: () => {
                // No-op for fallback
            }
        };
    }

    /**
     * Load module with dependency resolution
     * @param {string} moduleName - Name of the module to load
     * @param {Object} options - Loading options
     * @returns {Object} Module instance with resolved dependencies
     */
    async loadModuleWithDependencies(moduleName, options = {}) {
        const moduleInstance = await this.loadModule(moduleName, options);
        
        if (moduleInstance.dependencies && moduleInstance.dependencies.length > 0) {
            const resolvedDependencies = {};
            
            for (const depName of moduleInstance.dependencies) {
                if (!this.loadedModules.has(depName)) {
                    resolvedDependencies[depName] = await this.loadModule(depName, options);
                } else {
                    resolvedDependencies[depName] = this.loadedModules.get(depName).instance;
                }
            }
            
            // Inject dependencies if module supports it
            if (typeof moduleInstance.injectDependencies === 'function') {
                moduleInstance.injectDependencies(resolvedDependencies);
            }
        }
        
        return moduleInstance;
    }

    /**
     * Cleanup all loaded modules
     */
    async cleanup() {
        console.log('🧹 Cleaning up loaded modules...');
        
        for (const [moduleName, moduleData] of this.loadedModules) {
            try {
                if (typeof moduleData.instance.cleanup === 'function') {
                    await moduleData.instance.cleanup();
                }
                console.log(`✅ Cleaned up module: ${moduleName}`);
            } catch (error) {
                console.error(`❌ Failed to cleanup module ${moduleName}: ${error.message}`);
            }
        }
        
        // Clear caches
        this.loadedModules.clear();
        this.moduleCache.clear();
        this.dependencies.clear();
        
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }
    }

    /**
     * Get module loading statistics
     * @returns {Object} Loading statistics
     */
    getStats() {
        const stats = {
            totalModulesLoaded: this.loadedModules.size,
            totalMemoryImpact: 0,
            modules: {}
        };

        for (const [moduleName, moduleData] of this.loadedModules) {
            stats.totalMemoryImpact += moduleData.memoryImpact;
            stats.modules[moduleName] = {
                loadTime: moduleData.loadTime,
                memoryImpact: moduleData.memoryImpact,
                memoryImpactMB: Math.round(moduleData.memoryImpact / 1024 / 1024 * 100) / 100
            };
        }

        stats.totalMemoryImpactMB = Math.round(stats.totalMemoryImpact / 1024 / 1024 * 100) / 100;
        return stats;
    }

    /**
     * List available modules
     * @returns {Array} Available module names
     */
    listAvailableModules() {
        try {
            const files = fs.readdirSync(this.modulePath);
            return files
                .filter(file => file.endsWith('.js') && file !== 'module-loader.js')
                .map(file => file.replace('.js', ''))
                .sort();
        } catch (error) {
            console.error(`❌ Failed to list modules: ${error.message}`);
            return [];
        }
    }

    /**
     * Health check for module loading system
     * @returns {Object} Health status
     */
    healthCheck() {
        const availableModules = this.listAvailableModules();
        const stats = this.getStats();
        
        return {
            status: 'healthy',
            availableModules: availableModules.length,
            loadedModules: stats.totalModulesLoaded,
            totalMemoryUsage: stats.totalMemoryImpactMB,
            memoryThresholdMB: Math.round(this.memoryThreshold / 1024 / 1024),
            fallbackEnabled: this.enableFallback,
            modules: availableModules
        };
    }
}

// Setup cleanup handlers
const moduleLoader = new ModuleLoader();

process.on('exit', () => {
    moduleLoader.cleanup();
});

process.on('SIGINT', () => {
    moduleLoader.cleanup();
    process.exit(0);
});

process.on('SIGTERM', () => {
    moduleLoader.cleanup();
    process.exit(0);
});

module.exports = ModuleLoader;