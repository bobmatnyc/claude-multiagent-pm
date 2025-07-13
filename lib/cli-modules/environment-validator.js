#!/usr/bin/env node

/**
 * Claude PM Environment Validator Module
 * 
 * Extracted from bin/claude-pm environment validation logic
 * Handles platform detection, Python validation, and environment status checks.
 * 
 * Part of ISS-0085 Phase 1: Core Module Extraction
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

class EnvironmentValidator {
    constructor() {
        this.platformInfo = null;
        this.pythonInfo = null;
        this.validationCache = new Map();
        this.cacheExpiry = 60000; // 1 minute
    }

    /**
     * Comprehensive environment validation
     * @returns {Object} Validation results
     */
    validateEnvironment() {
        const cacheKey = 'environment';
        const cached = this._getCached(cacheKey);
        if (cached) return cached;

        const validation = {
            platform: this.detectPlatformInfo(),
            python: this.validatePython(),
            overall: false,
            errors: []
        };

        // Overall status determination
        validation.overall = validation.python !== null;
        
        if (!validation.python) {
            validation.errors.push('Python is not available or incompatible');
        }

        return this._setCached(cacheKey, validation);
    }

    /**
     * Detect comprehensive platform information
     * @returns {Object} Platform detection results
     */
    detectPlatformInfo() {
        if (this.platformInfo) return this.platformInfo;

        const platform = os.platform();
        const arch = os.arch();
        const release = os.release();

        this.platformInfo = {
            platform: platform,
            arch: arch,
            release: release,
            isWindows: platform === 'win32',
            isMacOS: platform === 'darwin',
            isLinux: platform === 'linux',
            isWSL2: this._detectWSL2(),
            npmGlobalBin: this._getNpmGlobalBin(),
            pathIssues: []
        };

        // Detect potential path issues
        if (this.platformInfo.isWSL2) {
            this.platformInfo.pathIssues = this._analyzeWSL2Path();
        }

        return this.platformInfo;
    }

    /**
     * Validate Python installation and compatibility
     * @returns {string|null} Python command if valid, null if invalid
     */
    validatePython() {
        if (this.pythonInfo) return this.pythonInfo;

        const pythonCommands = ['python3', 'python'];
        
        for (const pythonCmd of pythonCommands) {
            try {
                const { execSync } = require('child_process');
                
                // Check if command exists and get version
                const versionOutput = execSync(`${pythonCmd} --version`, {
                    encoding: 'utf8',
                    timeout: 5000,
                    stdio: 'pipe'
                }).trim();

                // Parse version
                const versionMatch = versionOutput.match(/Python (\d+)\.(\d+)\.(\d+)/);
                if (versionMatch) {
                    const major = parseInt(versionMatch[1]);
                    const minor = parseInt(versionMatch[2]);
                    
                    // Require Python 3.7+
                    if (major >= 3 && minor >= 7) {
                        this.pythonInfo = pythonCmd;
                        return pythonCmd;
                    }
                }
            } catch (error) {
                // Continue to next command
            }
        }

        this.pythonInfo = null;
        return null;
    }

    /**
     * Quick Claude CLI availability check
     * @returns {Object} Claude CLI status
     */
    quickClaudeCheck() {
        const cacheKey = 'claude-cli';
        const cached = this._getCached(cacheKey);
        if (cached) return cached;

        try {
            const { execSync } = require('child_process');
            execSync('claude --version', {
                encoding: 'utf8',
                timeout: 5000,
                stdio: 'pipe'
            });

            const result = { available: true, error: null, suggestion: null };
            return this._setCached(cacheKey, result);
        } catch (error) {
            const result = {
                available: false,
                error: 'Not installed or not in PATH',
                suggestion: 'Install from https://claude.ai/download and ensure it\'s in your PATH'
            };
            return this._setCached(cacheKey, result);
        }
    }

    /**
     * Display comprehensive environment status
     * @returns {Object} Environment status for display
     */
    displayEnvironmentStatus() {
        const validation = this.validateEnvironment();
        const claudeCheck = this.quickClaudeCheck();
        const platformInfo = this.detectPlatformInfo();

        return {
            validation,
            claudeCheck,
            platformInfo,
            overall: validation.overall && claudeCheck.available
        };
    }

    /**
     * Detect WSL2 environment
     * @returns {boolean} True if running in WSL2
     * @private
     */
    _detectWSL2() {
        try {
            if (os.platform() !== 'linux') return false;
            
            // Check /proc/version for WSL
            if (fs.existsSync('/proc/version')) {
                const version = fs.readFileSync('/proc/version', 'utf8');
                return version.toLowerCase().includes('wsl2') || 
                       version.toLowerCase().includes('microsoft');
            }
            
            // Check environment variables
            return !!(process.env.WSL_DISTRO_NAME || process.env.WSLENV);
        } catch (error) {
            return false;
        }
    }

    /**
     * Get NPM global bin directory
     * @returns {string|null} NPM global bin path
     * @private
     */
    _getNpmGlobalBin() {
        try {
            const { execSync } = require('child_process');
            return execSync('npm bin -g', {
                encoding: 'utf8',
                timeout: 5000,
                stdio: 'pipe'
            }).trim();
        } catch (error) {
            return null;
        }
    }

    /**
     * Analyze WSL2 path issues
     * @returns {Array} Array of detected path issues
     * @private
     */
    _analyzeWSL2Path() {
        const issues = [];
        const currentPath = process.env.PATH || '';
        const npmGlobalBin = this._getNpmGlobalBin();

        if (npmGlobalBin && !currentPath.includes(npmGlobalBin)) {
            issues.push({
                type: 'missing_npm_global',
                description: 'NPM global bin directory not in PATH',
                suggestion: `export PATH="${npmGlobalBin}:$PATH"`,
                severity: 'high'
            });
        }

        // Check for common WSL2 PATH issues
        if (!currentPath.includes('/usr/local/bin')) {
            issues.push({
                type: 'missing_usr_local_bin',
                description: '/usr/local/bin not in PATH',
                suggestion: 'export PATH="/usr/local/bin:$PATH"',
                severity: 'medium'
            });
        }

        return issues;
    }

    /**
     * Get cached value if still valid
     * @param {string} key - Cache key
     * @returns {any|null} Cached value or null
     * @private
     */
    _getCached(key) {
        const cached = this.validationCache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
            return cached.value;
        }
        return null;
    }

    /**
     * Set cached value with timestamp
     * @param {string} key - Cache key
     * @param {any} value - Value to cache
     * @returns {any} The cached value
     * @private
     */
    _setCached(key, value) {
        this.validationCache.set(key, {
            value: value,
            timestamp: Date.now()
        });
        return value;
    }

    /**
     * Clear all caches
     */
    clearCache() {
        this.validationCache.clear();
        this.platformInfo = null;
        this.pythonInfo = null;
    }

    /**
     * Get comprehensive diagnostics
     * @returns {Object} Diagnostic information
     */
    getDiagnostics() {
        return {
            cache: {
                size: this.validationCache.size,
                keys: Array.from(this.validationCache.keys())
            },
            platform: this.platformInfo,
            python: this.pythonInfo,
            environment: this.validateEnvironment(),
            claude: this.quickClaudeCheck()
        };
    }

    /**
     * Module cleanup
     */
    cleanup() {
        this.clearCache();
    }
}

// Module interface implementation
const environmentValidator = new EnvironmentValidator();

module.exports = {
    /**
     * Main module function - validates environment
     * @returns {Object} Environment validation results
     */
    main: () => {
        return environmentValidator.validateEnvironment();
    },

    /**
     * Module configuration
     */
    config: {
        name: 'environment-validator',
        version: '1.0.0',
        description: 'Platform detection, Python validation, and environment status checks',
        extractedFrom: 'bin/claude-pm environment validation logic',
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
            environmentValidator.cacheExpiry = options.cacheExpiry;
        }
    },

    /**
     * Direct access to validator instance
     */
    validator: environmentValidator,

    /**
     * Validate Python installation
     */
    validatePython: () => {
        return environmentValidator.validatePython();
    },

    /**
     * Detect platform information
     */
    detectPlatformInfo: () => {
        return environmentValidator.detectPlatformInfo();
    },

    /**
     * Quick Claude CLI check
     */
    quickClaudeCheck: () => {
        return environmentValidator.quickClaudeCheck();
    },

    /**
     * Display environment status
     */
    displayEnvironmentStatus: () => {
        return environmentValidator.displayEnvironmentStatus();
    },

    /**
     * Get diagnostics
     */
    getDiagnostics: () => {
        return environmentValidator.getDiagnostics();
    },

    /**
     * Clear cache
     */
    clearCache: () => {
        environmentValidator.clearCache();
    },

    /**
     * Module cleanup
     */
    cleanup: () => {
        environmentValidator.cleanup();
    }
};