#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Template Deployment Utility
 * 
 * Deploys framework CLAUDE.md template to the current working directory.
 * This is called automatically by the CLI and can be run manually.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');

class TemplateDeployer {
    constructor(targetDir = null) {
        this.platform = os.platform();
        this.targetDir = targetDir || process.cwd();
        this.packageRoot = this.findPackageRoot();
    }

    /**
     * Find the package root directory
     */
    findPackageRoot() {
        // Try multiple strategies to find the package root
        const strategies = [
            // 1. Relative to this script (for local installations)
            path.resolve(__dirname, '..'),
            
            // 2. Global npm installation paths
            path.resolve(require.resolve('@bobmatnyc/claude-multiagent-pm/package.json'), '..'),
            
            // 3. Environment variable if set
            process.env.CLAUDE_MULTIAGENT_PM_ROOT,
            
            // 4. Common global npm paths
            path.join(process.env.npm_config_prefix || '', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'),
            path.join(os.homedir(), '.npm-global', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'),
            path.join('/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm')
        ].filter(Boolean);

        for (const candidate of strategies) {
            try {
                if (fsSync.existsSync(path.join(candidate, 'package.json'))) {
                    const packageJson = JSON.parse(fsSync.readFileSync(path.join(candidate, 'package.json'), 'utf8'));
                    if (packageJson.name === '@bobmatnyc/claude-multiagent-pm') {
                        return candidate;
                    }
                }
            } catch (error) {
                // Continue to next strategy
            }
        }

        throw new Error('Could not find Claude Multi-Agent PM Framework package root');
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
     * Check if target directory already has a custom CLAUDE.md
     */
    async hasCustomClaudeMd() {
        const claudeMdPath = path.join(this.targetDir, 'CLAUDE.md');
        
        if (!fsSync.existsSync(claudeMdPath)) {
            return false;
        }

        try {
            const content = fsSync.readFileSync(claudeMdPath, 'utf8');
            const isFrameworkFile = content.includes('Claude PM Framework Configuration - Deployment') || 
                                  content.includes('AI ASSISTANT ROLE DESIGNATION');
            return !isFrameworkFile;
        } catch (error) {
            // If we can't read it, assume it's custom
            return true;
        }
    }

    /**
     * Find framework template
     */
    findFrameworkTemplate() {
        const candidates = [
            path.join(this.packageRoot, 'framework', 'CLAUDE.md'),
            path.join(this.packageRoot, 'lib', 'framework', 'CLAUDE.md'),
            path.join(this.packageRoot, 'templates', 'CLAUDE.md')
        ];

        for (const candidate of candidates) {
            if (fsSync.existsSync(candidate)) {
                return candidate;
            }
        }

        throw new Error(`Framework template not found. Searched: ${candidates.join(', ')}`);
    }

    /**
     * Get platform-specific notes
     */
    getPlatformNotes() {
        switch (this.platform) {
            case 'darwin':
                return '**macOS-specific:**\n- Use `.sh` files for scripts\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\n- Health check: `scripts/health-check.sh`\n- May require Xcode Command Line Tools';
            case 'linux':
                return '**Linux-specific:**\n- Use `.sh` files for scripts\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\n- Health check: `scripts/health-check.sh`\n- Ensure proper file permissions';
            case 'win32':
                return '**Windows-specific:**\n- Use `.bat` files for scripts\n- CLI wrappers: `bin/aitrackdown.bat` and `bin/atd.bat`\n- Health check: `scripts/health-check.bat`\n- Path separators: Use backslashes in Windows paths';
            default:
                return `**Platform**: ${this.platform}\n- Use appropriate script extensions for your platform\n- Ensure proper file permissions on CLI wrappers`;
        }
    }

    /**
     * Deploy framework template to target directory
     */
    async deploy(options = {}) {
        try {
            this.log(`🚀 Deploying framework template to: ${this.targetDir}`);
            this.log(`📦 Package root: ${this.packageRoot}`);

            // Check if custom CLAUDE.md exists
            if (await this.hasCustomClaudeMd() && !options.force) {
                this.log('✋ Custom CLAUDE.md detected - skipping deployment');
                this.log('💡 Use --force to override existing custom CLAUDE.md');
                return false;
            }

            // Find framework template
            const templatePath = this.findFrameworkTemplate();
            this.log(`📄 Using template: ${templatePath}`);

            // Read template content
            const templateContent = fsSync.readFileSync(templatePath, 'utf8');
            
            // Load package info
            const packageJson = JSON.parse(fsSync.readFileSync(path.join(this.packageRoot, 'package.json'), 'utf8'));
            
            // Template variable replacements
            const deploymentDate = new Date().toISOString();
            const deploymentId = Date.now();
            
            const replacements = {
                '{{CLAUDE_MD_VERSION}}': `${packageJson.version}-001`,
                '{{FRAMEWORK_VERSION}}': packageJson.version,
                '{{DEPLOYMENT_DATE}}': deploymentDate,
                '{{LAST_UPDATED}}': deploymentDate,
                '{{DEPLOYMENT_DIR}}': this.targetDir,
                '{{PLATFORM}}': this.platform,
                '{{PYTHON_CMD}}': 'python3',
                '{{AI_TRACKDOWN_PATH}}': 'Global installation available',
                '{{DEPLOYMENT_ID}}': deploymentId,
                '{{PLATFORM_NOTES}}': this.getPlatformNotes()
            };

            this.log('🔄 Applying template substitutions');
            let deployedContent = templateContent;
            for (const [placeholder, value] of Object.entries(replacements)) {
                const escapedPlaceholder = placeholder.replace(/[{}]/g, '\\$&');
                deployedContent = deployedContent.replace(new RegExp(escapedPlaceholder, 'g'), value);
            }

            // Write deployed template
            const targetPath = path.join(this.targetDir, 'CLAUDE.md');
            fsSync.writeFileSync(targetPath, deployedContent);

            this.log(`✅ Framework template deployed successfully`);
            this.log(`📍 Location: ${targetPath}`);
            this.log(`📊 Size: ${fsSync.statSync(targetPath).size} bytes`);

            return true;

        } catch (error) {
            this.log(`❌ Template deployment failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Check if deployment is needed
     */
    async isDeploymentNeeded() {
        const claudeMdPath = path.join(this.targetDir, 'CLAUDE.md');
        
        if (!fsSync.existsSync(claudeMdPath)) {
            return true; // No CLAUDE.md exists
        }

        // Check if it's a framework file (would need updating)
        try {
            const content = fsSync.readFileSync(claudeMdPath, 'utf8');
            const isFrameworkFile = content.includes('Claude PM Framework Configuration - Deployment') || 
                                  content.includes('AI ASSISTANT ROLE DESIGNATION');
            return isFrameworkFile; // Framework files can be updated
        } catch (error) {
            return false; // Can't read, don't override
        }
    }
}

// CLI interface
async function main() {
    const args = process.argv.slice(2);
    const options = {
        force: args.includes('--force'),
        verbose: args.includes('--verbose'),
        check: args.includes('--check')
    };

    // Get target directory from args or use current directory
    const targetDir = args.find(arg => !arg.startsWith('--')) || process.cwd();

    try {
        const deployer = new TemplateDeployer(targetDir);

        if (options.check) {
            const needed = await deployer.isDeploymentNeeded();
            console.log(`Template deployment needed: ${needed ? 'YES' : 'NO'}`);
            process.exit(needed ? 1 : 0);
        }

        const success = await deployer.deploy(options);
        
        if (success) {
            console.log('\n🎉 Framework template deployed successfully!');
            console.log('\nNext steps:');
            console.log('1. The CLAUDE.md file contains your project configuration');
            console.log('2. You can now use claude-pm commands in this directory');
            console.log('3. Run "claude-pm health status" to verify installation');
        }

    } catch (error) {
        console.error(`\n❌ Deployment failed: ${error.message}`);
        console.error('\nTroubleshooting:');
        console.error('1. Ensure Claude Multi-Agent PM Framework is properly installed');
        console.error('2. Check file permissions in the target directory');
        console.error('3. Try running with --verbose flag for more details');
        process.exit(1);
    }
}

// Export for use as module
module.exports = TemplateDeployer;

// Run CLI if called directly
if (require.main === module) {
    main();
}