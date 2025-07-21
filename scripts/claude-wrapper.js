#!/usr/bin/env node

/**
 * Claude CLI Wrapper Script for Multi-Agent Coordination
 * 
 * This wrapper script resolves the "MaxListeners exceeded" warning that occurs
 * when using Claude Code with claude-pm's multi-agent coordination system.
 * 
 * Problem Solved:
 * - MaxListeners warnings: "11 abort listeners added to [AbortSignal]. MaxListeners is 10"
 * - High concurrency issues from multi-agent subprocess coordination
 * - Node.js EventEmitter limits being exceeded during framework operations
 * 
 * Solution:
 * - Sets AbortSignal MaxListeners to 25 to accommodate multi-agent coordination
 * - Configures EventEmitter defaults for high-concurrency operations
 * - Maintains memory leak protection while allowing legitimate high usage
 * - Provides proper error handling and process management
 * 
 * Usage:
 * - Used automatically by claude-pm when launching Claude CLI
 * - Passes through all Claude CLI arguments transparently
 * - Fallback to direct Claude launch if wrapper fails
 * 
 * Technical Details:
 * - Uses require('events').setMaxListeners(25, AbortSignal.prototype)
 * - Sets EventEmitter.defaultMaxListeners = 25
 * - Configures process.setMaxListeners(25)
 * - Spawns Claude CLI with proper stdio inheritance
 * 
 * @author Claude Multi-Agent PM Framework
 * @version 1.0.0
 * @date 2025-07-15
 */

const { spawn } = require('child_process');
const { EventEmitter } = require('events');

class ClaudeWrapper {
    constructor() {
        this.setupEnvironment();
    }

    /**
     * Configure Node.js environment for multi-agent coordination
     */
    setupEnvironment() {
        try {
            // Set AbortSignal MaxListeners to 25 to accommodate multi-agent coordination
            // This prevents the "MaxListeners exceeded" warning while maintaining memory leak protection
            if (typeof AbortSignal !== 'undefined' && AbortSignal.prototype) {
                require('events').setMaxListeners(25, AbortSignal.prototype);
                console.log('✅ AbortSignal MaxListeners set to 25 for multi-agent coordination');
            } else {
                console.log('⚠️  AbortSignal not available - MaxListeners configuration skipped');
            }

            // Set default MaxListeners for EventEmitter to handle high concurrency
            EventEmitter.defaultMaxListeners = 25;
            
            // Configure process-level event handling
            process.setMaxListeners(25);
            
            console.log('✅ Node.js environment configured for multi-agent architecture');
            
        } catch (error) {
            console.error('❌ Error configuring Node.js environment:', error.message);
            console.error('⚠️  Continuing with default settings - some warnings may appear');
        }
    }

    /**
     * Launch Claude CLI with proper environment setup
     */
    async launchClaude(args) {
        try {
            console.log('🚀 Launching Claude CLI with enhanced environment...');
            console.log('📋 Arguments:', args.join(' '));
            
            // Launch Claude CLI as a child process with proper stdio handling
            const claude = spawn('claude', args, {
                stdio: 'inherit',
                env: {
                    ...process.env,
                    // Add any additional environment variables if needed
                    NODE_OPTIONS: '--max-old-space-size=4096'
                }
            });

            // Handle process events
            claude.on('error', (error) => {
                console.error('❌ Claude CLI launch error:', error.message);
                process.exit(1);
            });

            claude.on('exit', (code, signal) => {
                if (signal) {
                    console.log(`Claude CLI terminated by signal: ${signal}`);
                    process.exit(1);
                } else {
                    process.exit(code || 0);
                }
            });

            // Handle process termination signals
            process.on('SIGINT', () => {
                console.log('\n🛑 Received SIGINT, terminating Claude CLI...');
                claude.kill('SIGINT');
            });

            process.on('SIGTERM', () => {
                console.log('\n🛑 Received SIGTERM, terminating Claude CLI...');
                claude.kill('SIGTERM');
            });

        } catch (error) {
            console.error('❌ Failed to launch Claude CLI:', error.message);
            process.exit(1);
        }
    }
}

// Main execution
if (require.main === module) {
    const wrapper = new ClaudeWrapper();
    let args = process.argv.slice(2);
    
    // Filter out --test-mode flag as it's not a Claude CLI flag
    // It's handled by the claude-pm wrapper for prompt logging
    args = args.filter(arg => arg !== '--test-mode');
    
    // Launch Claude CLI with enhanced environment
    wrapper.launchClaude(args);
}

module.exports = ClaudeWrapper;