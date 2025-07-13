#!/usr/bin/env node

/**
 * Claude PM Display Manager Module
 * 
 * Extracted from bin/claude-pm display and UI logic
 * Handles console output, help text, system info display, and user interaction.
 * 
 * Part of ISS-0085 Phase 1: Core Module Extraction
 */

const os = require('os');

class DisplayManager {
    constructor() {
        this.outputBuffer = [];
        this.enableBuffering = false;
        this.indentLevel = 0;
        this.indentStr = '   ';
    }

    /**
     * Show comprehensive help text
     * @param {string} version - Framework version
     */
    showHelp(version) {
        const helpText = `
Claude Multi-Agent PM Framework v${version}
Universal CLI for Claude-powered project management and task orchestration

🚀 USAGE:
  claude-pm [command] [options]

📋 COMMANDS:
  
  🎯 Core Operations:
  setup                    Initialize framework in current directory
  status                   Show framework and deployment status
  
  📊 Information & Diagnostics:
  --version, -v            Show version information
  --help, -h              Show this help message
  --system-info           Display comprehensive system information
  --deployment-info       Show deployment detection results
  --environment-status    Show environment compatibility status
  
  🔧 Maintenance & Tools:
  deploy-template         Manually deploy CLAUDE.md template
  --manage-claude-md      Manage framework CLAUDE.md deployment tree
  --claude-info           Detailed Claude CLI validation and troubleshooting
  
  ⚡ Quick Actions:
  claude [args...]        Launch Claude CLI with framework context (default)

🏗️  FRAMEWORK ARCHITECTURE:
  • Multi-Agent Orchestration: Coordinate specialized AI agents
  • Universal Deployment: Works in any environment (npm global, local, npx)
  • Memory Integration: Persistent context and learning capabilities
  • Template System: Automated CLAUDE.md deployment and management

🔍 DEPLOYMENT SCENARIOS:
  ✅ NPM Global Install: npm install -g @bobmatnyc/claude-multiagent-pm
  ✅ NPM Local Install: npm install @bobmatnyc/claude-multiagent-pm
  ✅ NPX Execution: npx @bobmatnyc/claude-multiagent-pm
  ✅ Source Development: Direct execution from source

🚨 TROUBLESHOOTING:
  • Environment Issues: claude-pm --environment-status
  • Deployment Problems: claude-pm --deployment-info
  • System Diagnostics: claude-pm --system-info
  • Template Issues: claude-pm deploy-template
  • Claude CLI Issues: claude-pm --claude-info

📖 DOCUMENTATION:
  • GitHub: https://github.com/bobmatnyc/claude-multiagent-pm
  • User Guide: ~/.claude-pm/docs/user-guide/
  • Framework Docs: ~/.claude-pm/docs/

🆘 SUPPORT:
  • Report Issues: GitHub Issues
  • Community: GitHub Discussions
  • Documentation: Run 'claude-pm --system-info' for local paths

---
Made with ❤️  for AI-powered development workflows
`.trim();

        this.output(helpText);
    }

    /**
     * Display comprehensive system information
     * @param {Object} deploymentConfig - Deployment configuration
     * @param {string} version - Framework version
     */
    displaySystemInfo(deploymentConfig, version) {
        const platformInfo = {
            platform: os.platform(),
            arch: os.arch(),
            release: os.release(),
            nodeVersion: process.version,
            pid: process.pid
        };

        this.output('');
        this.output('🖥️  Claude Multi-Agent PM Framework - System Information');
        this.output('=' .repeat(70));
        this.output('');

        // Framework Information
        this.output('📦 Framework Information:');
        this.indent();
        this.output(`Version: v${version}`);
        this.output(`Node.js: ${platformInfo.nodeVersion}`);
        this.output(`Platform: ${platformInfo.platform} (${platformInfo.arch})`);
        this.output(`OS Release: ${platformInfo.release}`);
        this.output(`Process ID: ${platformInfo.pid}`);
        this.outdent();
        this.output('');

        // Deployment Information
        if (deploymentConfig && deploymentConfig.config) {
            this.output('🚀 Deployment Configuration:');
            this.indent();
            this.output(`Type: ${deploymentConfig.config.deploymentType || 'Unknown'}`);
            this.output(`Framework Path: ${deploymentConfig.config.frameworkPath || 'Not specified'}`);
            
            if (deploymentConfig.config.metadata) {
                const metadata = deploymentConfig.config.metadata;
                if (metadata.npmGlobalBin) {
                    this.output(`NPM Global Bin: ${metadata.npmGlobalBin}`);
                }
                if (metadata.deployedConfig) {
                    this.output(`Config Version: v${metadata.deployedConfig.version}`);
                    if (metadata.deployedConfig.deployedAt) {
                        this.output(`Deployed: ${new Date(metadata.deployedConfig.deployedAt).toLocaleString()}`);
                    }
                }
            }
            this.outdent();
            this.output('');
        }

        // Directory Information
        this.output('📁 Directory Information:');
        this.indent();
        this.output(`Working Directory: ${process.cwd()}`);
        this.output(`Home Directory: ${os.homedir()}`);
        this.output(`Temp Directory: ${os.tmpdir()}`);
        this.outdent();
        this.output('');

        // Memory Information
        const memUsage = process.memoryUsage();
        this.output('💾 Memory Usage:');
        this.indent();
        this.output(`Heap Used: ${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`);
        this.output(`Heap Total: ${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`);
        this.output(`External: ${Math.round(memUsage.external / 1024 / 1024)}MB`);
        this.output(`RSS: ${Math.round(memUsage.rss / 1024 / 1024)}MB`);
        this.outdent();
        this.output('');

        // Platform-specific notes
        const platformNotes = this.getPlatformNotes(platformInfo.platform);
        if (platformNotes.length > 0) {
            this.output(`🔧 ${platformInfo.platform.charAt(0).toUpperCase() + platformInfo.platform.slice(1)} Specific Notes:`);
            this.indent();
            platformNotes.forEach(note => this.output(`• ${note}`));
            this.outdent();
            this.output('');
        }

        this.output('🆘 Support Information:');
        this.indent();
        this.output('• Report Issues: https://github.com/bobmatnyc/claude-multiagent-pm/issues');
        this.output('• Documentation: ~/.claude-pm/docs/');
        this.output('• User Guide: ~/.claude-pm/docs/user-guide/');
        this.output('• System Diagnostics: claude-pm --deployment-info');
        this.outdent();
        this.output('');
    }

    /**
     * Display environment status with formatted output
     * @param {Object} environmentStatus - Environment validation results
     */
    displayEnvironmentStatus(environmentStatus) {
        const { validation, claudeCheck, platformInfo } = environmentStatus;

        this.output('');
        this.output('🌍 Environment Compatibility Status');
        this.output('=' .repeat(40));
        this.output('');

        // Platform information
        this.output(`🖥️  Platform: ${platformInfo.platform} (${platformInfo.arch})`);
        if (platformInfo.isWSL2) {
            this.output('🐧 WSL2 Environment Detected');
        }
        this.output('');

        // Python status
        if (validation.python) {
            this.output(`✅ Python: ${validation.python} (compatible)`);
        } else {
            this.output('❌ Python: Not available or incompatible');
        }

        // Claude CLI status
        if (claudeCheck.available) {
            this.output('✅ Claude CLI: Available (use --claude-info for detailed validation)');
        } else {
            this.output(`❌ Claude CLI: ${claudeCheck.error}`);
            this.output(`   → ${claudeCheck.suggestion}`);
        }

        // WSL2 specific issues
        if (platformInfo.isWSL2 && platformInfo.pathIssues && platformInfo.pathIssues.length > 0) {
            this.output('');
            this.output('🚨 WSL2 Path Issues Detected:');
            this.indent();
            platformInfo.pathIssues.forEach(issue => {
                this.output(`• ${issue.description}`);
                this.output(`  Fix: ${issue.suggestion}`);
            });
            this.outdent();
        }

        // Overall status
        this.output('');
        if (validation.overall && claudeCheck.available) {
            this.output('🎯 Environment Status: Ready for framework operations');
        } else {
            this.output('⚠️  Environment Status: Issues detected');
            validation.errors.forEach(error => {
                this.output(`   • ${error}`);
            });
        }

        this.output('');
    }

    /**
     * Get platform-specific notes
     * @param {string} platform - Platform identifier
     * @returns {Array} Array of platform notes
     */
    getPlatformNotes(platform) {
        switch (platform) {
            case 'darwin':
                return [
                    'Xcode Command Line Tools may be required',
                    'Homebrew recommended for additional tools',
                    'Use Terminal or iTerm2 for best experience'
                ];
            case 'win32':
                return [
                    'Windows PowerShell or Command Prompt supported',
                    'WSL2 recommended for enhanced compatibility',
                    'Node.js should be installed via official installer'
                ];
            case 'linux':
                return [
                    'Most Linux distributions supported',
                    'Build tools may be required: build-essential',
                    'Check package manager for Node.js installation'
                ];
            default:
                return ['Platform-specific optimizations may be available'];
        }
    }

    /**
     * Output text with current indentation
     * @param {string} text - Text to output
     */
    output(text) {
        const indentedText = this.indentStr.repeat(this.indentLevel) + text;
        
        if (this.enableBuffering) {
            this.outputBuffer.push(indentedText);
        } else {
            console.log(indentedText);
        }
    }

    /**
     * Increase indentation level
     */
    indent() {
        this.indentLevel++;
    }

    /**
     * Decrease indentation level
     */
    outdent() {
        if (this.indentLevel > 0) {
            this.indentLevel--;
        }
    }

    /**
     * Enable output buffering
     */
    startBuffering() {
        this.enableBuffering = true;
        this.outputBuffer = [];
    }

    /**
     * Disable buffering and return buffered content
     * @returns {Array} Array of buffered output lines
     */
    stopBuffering() {
        this.enableBuffering = false;
        const buffer = [...this.outputBuffer];
        this.outputBuffer = [];
        return buffer;
    }

    /**
     * Clear output buffer
     */
    clearBuffer() {
        this.outputBuffer = [];
    }

    /**
     * Get current buffer content
     * @returns {Array} Current buffer content
     */
    getBuffer() {
        return [...this.outputBuffer];
    }

    /**
     * Module cleanup
     */
    cleanup() {
        this.clearBuffer();
        this.indentLevel = 0;
        this.enableBuffering = false;
    }
}

// Module interface implementation
const displayManager = new DisplayManager();

module.exports = {
    /**
     * Main module function - shows help
     * @param {string} version - Framework version
     */
    main: (version) => {
        return displayManager.showHelp(version);
    },

    /**
     * Module configuration
     */
    config: {
        name: 'display-manager',
        version: '1.0.0',
        description: 'Console output, help text, system info display, and user interaction',
        extractedFrom: 'bin/claude-pm display and UI logic',
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
        if (options.enableBuffering) {
            displayManager.startBuffering();
        }
        if (options.indentStr) {
            displayManager.indentStr = options.indentStr;
        }
    },

    /**
     * Direct access to display manager instance
     */
    manager: displayManager,

    /**
     * Show help text
     */
    showHelp: (version) => {
        return displayManager.showHelp(version);
    },

    /**
     * Display system information
     */
    displaySystemInfo: (deploymentConfig, version) => {
        return displayManager.displaySystemInfo(deploymentConfig, version);
    },

    /**
     * Display environment status
     */
    displayEnvironmentStatus: (environmentStatus) => {
        return displayManager.displayEnvironmentStatus(environmentStatus);
    },

    /**
     * Get platform notes
     */
    getPlatformNotes: (platform) => {
        return displayManager.getPlatformNotes(platform);
    },

    /**
     * Output management
     */
    output: (text) => displayManager.output(text),
    indent: () => displayManager.indent(),
    outdent: () => displayManager.outdent(),
    startBuffering: () => displayManager.startBuffering(),
    stopBuffering: () => displayManager.stopBuffering(),
    clearBuffer: () => displayManager.clearBuffer(),
    getBuffer: () => displayManager.getBuffer(),

    /**
     * Module cleanup
     */
    cleanup: () => {
        displayManager.cleanup();
    }
};