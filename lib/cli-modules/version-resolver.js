#!/usr/bin/env node

/**
 * Claude PM Version Resolver Module
 * 
 * Extracted from bin/claude-pm lines 17-102
 * Handles version resolution across all deployment scenarios.
 * 
 * Part of ISS-0085 Phase 1: Core Module Extraction
 */

const fs = require('fs');
const path = require('path');

class VersionResolver {
    constructor() {
        this.versionCache = null;
        this.cacheTimestamp = null;
        this.cacheExpiry = 30000; // 30 seconds
    }

    /**
     * Universal version resolution for all deployment scenarios
     * @returns {string} Resolved version string
     * @throws {Error} If version cannot be resolved
     */
    resolveVersion() {
        // Check cache first
        if (this.versionCache && this.cacheTimestamp && 
            (Date.now() - this.cacheTimestamp) < this.cacheExpiry) {
            return this.versionCache;
        }

        let resolvedVersion = null;

        // Strategy 1: Try to find package.json relative to this script
        resolvedVersion = this._tryPackageJsonStrategy();
        if (resolvedVersion) {
            return this._cacheAndReturn(resolvedVersion);
        }

        // Strategy 2: Try VERSION file (source development scenario)
        resolvedVersion = this._tryVersionFileStrategy();
        if (resolvedVersion) {
            return this._cacheAndReturn(resolvedVersion);
        }

        // Strategy 3: Check for NPM package in node_modules
        resolvedVersion = this._tryNodeModulesStrategy();
        if (resolvedVersion) {
            return this._cacheAndReturn(resolvedVersion);
        }

        // Strategy 4: Use npm to resolve package version (if available)
        resolvedVersion = this._tryNpmCommandStrategy();
        if (resolvedVersion) {
            return this._cacheAndReturn(resolvedVersion);
        }

        // If all strategies fail, throw error with helpful message
        throw new Error(
            'Could not resolve Claude PM Framework version. ' +
            'This may indicate a corrupted installation or unsupported deployment scenario. ' +
            'Please reinstall using: npm install -g @bobmatnyc/claude-multiagent-pm'
        );
    }

    /**
     * Strategy 1: Package.json relative search
     * @returns {string|null} Version if found, null otherwise
     */
    _tryPackageJsonStrategy() {
        // Works for: source, npm global, npm local, deployed scenarios
        const packagePaths = [
            path.join(__dirname, '../package.json'),      // From lib/cli-modules
            path.join(__dirname, '../../package.json'),   // From project root
            path.join(__dirname, '../../../package.json'), // One level up if needed
            path.join(__dirname, '../../../../package.json') // Two levels up for deep npm installs
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
                // Continue to next path
            }
        }
        
        return null;
    }

    /**
     * Strategy 2: VERSION file search
     * @returns {string|null} Version if found, null otherwise
     */
    _tryVersionFileStrategy() {
        const versionPaths = [
            path.join(__dirname, '../VERSION'),      // From lib/cli-modules
            path.join(__dirname, '../../VERSION'),   // From project root
            path.join(__dirname, '../../../VERSION') // One level up
        ];
        
        for (const versionPath of versionPaths) {
            try {
                if (fs.existsSync(versionPath)) {
                    return fs.readFileSync(versionPath, 'utf8').trim();
                }
            } catch (e) {
                // Continue to next path
            }
        }
        
        return null;
    }

    /**
     * Strategy 3: Node modules search
     * @returns {string|null} Version if found, null otherwise
     */
    _tryNodeModulesStrategy() {
        try {
            const nodeModulesPaths = [
                path.join(process.cwd(), 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'package.json'),
                path.join(process.cwd(), '..', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'package.json'),
                // Try to use require.resolve
                require.resolve('@bobmatnyc/claude-multiagent-pm/package.json')
            ];
            
            for (const npmPackagePath of nodeModulesPaths) {
                if (fs.existsSync(npmPackagePath)) {
                    const pkg = JSON.parse(fs.readFileSync(npmPackagePath, 'utf8'));
                    if (pkg.name === '@bobmatnyc/claude-multiagent-pm' && pkg.version) {
                        return pkg.version;
                    }
                }
            }
        } catch (e) {
            // Continue to fallback
        }
        
        return null;
    }

    /**
     * Strategy 4: NPM command resolution
     * @returns {string|null} Version if found, null otherwise
     */
    _tryNpmCommandStrategy() {
        try {
            const { execSync } = require('child_process');
            const result = execSync('npm list @bobmatnyc/claude-multiagent-pm --depth=0 --json', { 
                encoding: 'utf8', 
                stdio: 'pipe',
                timeout: 5000 
            });
            const npmData = JSON.parse(result);
            if (npmData.dependencies && npmData.dependencies['@bobmatnyc/claude-multiagent-pm']) {
                return npmData.dependencies['@bobmatnyc/claude-multiagent-pm'].version;
            }
        } catch (e) {
            // npm command failed, continue
        }
        
        return null;
    }

    /**
     * Cache version and return it
     * @param {string} version - Version to cache
     * @returns {string} The cached version
     */
    _cacheAndReturn(version) {
        this.versionCache = version;
        this.cacheTimestamp = Date.now();
        return version;
    }

    /**
     * Clear version cache (useful for testing)
     */
    clearCache() {
        this.versionCache = null;
        this.cacheTimestamp = null;
    }

    /**
     * Get version resolution diagnostics
     * @returns {Object} Diagnostic information
     */
    getDiagnostics() {
        const diagnostics = {
            strategies: {
                packageJson: null,
                versionFile: null,
                nodeModules: null,
                npmCommand: null
            },
            cache: {
                hasCache: !!this.versionCache,
                cacheAge: this.cacheTimestamp ? Date.now() - this.cacheTimestamp : null,
                cachedVersion: this.versionCache
            }
        };

        // Test each strategy
        diagnostics.strategies.packageJson = this._tryPackageJsonStrategy();
        diagnostics.strategies.versionFile = this._tryVersionFileStrategy();
        diagnostics.strategies.nodeModules = this._tryNodeModulesStrategy();
        diagnostics.strategies.npmCommand = this._tryNpmCommandStrategy();

        return diagnostics;
    }

    /**
     * Module cleanup function
     */
    cleanup() {
        this.clearCache();
    }
}

// Module interface implementation
const versionResolver = new VersionResolver();

module.exports = {
    /**
     * Main module function - resolves version
     * @returns {string} Resolved version
     */
    main: () => {
        return versionResolver.resolveVersion();
    },

    /**
     * Module configuration
     */
    config: {
        name: 'version-resolver',
        version: '1.0.0',
        description: 'Universal version resolution for all deployment scenarios',
        extractedFrom: 'bin/claude-pm lines 17-102',
        phase: 1,
        riskLevel: 'low'
    },

    /**
     * Module dependencies
     */
    dependencies: [],

    /**
     * Initialize module
     * @param {Object} options - Initialization options
     */
    init: async (options = {}) => {
        if (options.cacheExpiry) {
            versionResolver.cacheExpiry = options.cacheExpiry;
        }
    },

    /**
     * Direct access to resolver instance for advanced usage
     */
    resolver: versionResolver,

    /**
     * Get version resolution diagnostics
     * @returns {Object} Diagnostic information
     */
    getDiagnostics: () => {
        return versionResolver.getDiagnostics();
    },

    /**
     * Clear version cache
     */
    clearCache: () => {
        versionResolver.clearCache();
    },

    /**
     * Module cleanup
     */
    cleanup: () => {
        versionResolver.cleanup();
    }
};