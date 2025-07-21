#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Simple PyPI Installer
 * 
 * This minimal script only installs the Python package from PyPI.
 * All Python source files are excluded from the NPM package.
 */

const { execSync } = require('child_process');
const os = require('os');

class SimpleInstaller {
    constructor() {
        this.platform = os.platform();
    }

    log(message, level = 'info') {
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '✅';
        console.log(`${prefix} ${message}`);
    }

    findPython() {
        const commands = ['python3', 'python'];
        for (const cmd of commands) {
            try {
                const version = execSync(`${cmd} --version`, { stdio: 'pipe', encoding: 'utf8' });
                if (version.includes('Python 3.') && !version.includes('3.7')) {
                    return cmd;
                }
            } catch (e) {
                // Continue to next command
            }
        }
        return null;
    }

    async install() {
        this.log('Installing Claude Multi-Agent PM from PyPI...');
        
        const pythonCmd = this.findPython();
        if (!pythonCmd) {
            this.log('Python 3.8+ not found. Please install Python first.', 'error');
            process.exit(1);
        }

        try {
            // Install from PyPI (when published) or local package
            execSync(`${pythonCmd} -m pip install claude-multiagent-pm --upgrade`, {
                stdio: 'inherit'
            });
            
            this.log('Installation complete! Run "claude-pm init" to get started.');
        } catch (error) {
            this.log('Failed to install Python package. Falling back to local installation...', 'warn');
            
            // Fallback for development/pre-PyPI
            try {
                execSync(`${pythonCmd} -m pip install -e .`, {
                    stdio: 'inherit',
                    cwd: require('path').join(__dirname, '..')
                });
                this.log('Local development installation complete!');
            } catch (fallbackError) {
                this.log('Installation failed. Please check your Python environment.', 'error');
                process.exit(1);
            }
        }
    }
}

// Run installer
new SimpleInstaller().install().catch(console.error);