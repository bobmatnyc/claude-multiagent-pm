#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - NPM Deployment Fix Script
 * 
 * Fixes common issues with NPM package installations:
 * 1. Updates deployed instance version to match NPM package
 * 2. Deploys framework/CLAUDE.md to working directory
 * 3. Fixes version display mismatches
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

class NPMDeploymentFixer {
    constructor() {
        this.packageJson = require('../package.json');
        this.version = this.packageJson.version;
        this.platform = os.platform();
        this.workingDir = process.cwd();
    }

    log(message, level = 'info') {
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : 'ℹ️';
        console.log(`${prefix} ${message}`);
    }

    /**
     * Update deployed instance configurations
     */
    async fixDeployedInstanceVersions() {
        this.log('Checking for deployed instances to update...');
        
        const deployedConfigPaths = [
            path.join(os.homedir(), '.local', '.claude-pm', 'config.json'),
            path.join(os.homedir(), '.claude-pm', 'config.json')
        ];
        
        let updated = false;
        
        for (const configPath of deployedConfigPaths) {
            if (fs.existsSync(configPath)) {
                try {
                    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                    
                    if (config.version !== this.version) {
                        this.log(`Found deployed instance with version ${config.version}, updating to ${this.version}`);
                        
                        // Update version info
                        config.version = this.version;
                        config.lastNpmUpdate = new Date().toISOString();
                        config.npmPackageVersion = this.version;
                        
                        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
                        this.log(`Updated deployed config: ${configPath}`, 'success');
                        updated = true;
                    } else {
                        this.log(`Deployed instance at ${path.dirname(configPath)} is already up-to-date`);
                    }
                } catch (error) {
                    this.log(`Failed to update config at ${configPath}: ${error.message}`, 'error');
                }
            }
        }
        
        if (!updated) {
            this.log('No deployed instances found that need updating');
        }
        
        return updated;
    }

    /**
     * Deploy framework CLAUDE.md to working directory
     */
    async deployFrameworkClaudemd() {
        this.log('Checking framework CLAUDE.md deployment...');
        
        const workingClaudemd = path.join(this.workingDir, 'CLAUDE.md');
        
        // Check if working directory already has a user CLAUDE.md
        if (fs.existsSync(workingClaudemd)) {
            const content = fs.readFileSync(workingClaudemd, 'utf8');
            
            // If it's a user/project file, don't overwrite
            if (!content.includes('Claude PM Framework Configuration - Deployment') && 
                !content.includes('AI ASSISTANT ROLE DESIGNATION')) {
                this.log('Working directory has custom CLAUDE.md, skipping framework deployment');
                return false;
            }
            
            // If it's an old framework file, check if it needs updating
            if (content.includes('{{FRAMEWORK_VERSION}}') || content.includes('{{CLAUDE_MD_VERSION}}')) {
                this.log('Found template CLAUDE.md with placeholders, updating...');
            } else {
                // Check version in existing framework file
                const versionMatch = content.match(/FRAMEWORK_VERSION:\s*(\S+)/);
                if (versionMatch && versionMatch[1] === this.version) {
                    this.log('Framework CLAUDE.md is already up-to-date');
                    return false;
                }
            }
        }
        
        // Find framework template
        const possibleTemplatePaths = [
            path.join(__dirname, '..', 'framework', 'CLAUDE.md'),
            path.join(this.workingDir, 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'framework', 'CLAUDE.md')
        ];
        
        let frameworkTemplate = null;
        for (const templatePath of possibleTemplatePaths) {
            if (fs.existsSync(templatePath)) {
                frameworkTemplate = templatePath;
                break;
            }
        }
        
        if (!frameworkTemplate) {
            this.log('Framework CLAUDE.md template not found', 'warn');
            return false;
        }
        
        try {
            let templateContent = fs.readFileSync(frameworkTemplate, 'utf8');
            
            const deploymentDate = new Date().toISOString();
            const deploymentId = Date.now();
            
            // Replace template variables
            const replacements = {
                '{{CLAUDE_MD_VERSION}}': `${this.version}-002`,
                '{{FRAMEWORK_VERSION}}': this.version,
                '{{DEPLOYMENT_DATE}}': deploymentDate,
                '{{LAST_UPDATED}}': deploymentDate,
                '{{DEPLOYMENT_DIR}}': this.workingDir,
                '{{PLATFORM}}': this.platform,
                '{{PYTHON_CMD}}': 'python3',
                '{{AI_TRACKDOWN_PATH}}': 'Global installation available',
                '{{DEPLOYMENT_ID}}': deploymentId,
                '{{PLATFORM_NOTES}}': this.getPlatformNotes()
            };
            
            for (const [placeholder, value] of Object.entries(replacements)) {
                const escapedPlaceholder = placeholder.replace(/[{}]/g, '\\$&');
                templateContent = templateContent.replace(new RegExp(escapedPlaceholder, 'g'), value);
            }
            
            // Debug: Check if all placeholders were replaced
            const remainingPlaceholders = templateContent.match(/{{[^}]+}}/g);
            if (remainingPlaceholders) {
                this.log(`Warning: Some placeholders not replaced: ${remainingPlaceholders.join(', ')}`, 'warn');
            }
            
            fs.writeFileSync(workingClaudemd, templateContent);
            this.log(`Framework CLAUDE.md deployed to: ${workingClaudemd}`, 'success');
            return true;
            
        } catch (error) {
            this.log(`Failed to deploy framework CLAUDE.md: ${error.message}`, 'error');
            return false;
        }
    }

    /**
     * Get platform-specific notes
     */
    getPlatformNotes() {
        switch (this.platform) {
            case 'darwin':
                return '**macOS-specific:**\\n- Use `.sh` files for scripts\\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\\n- Health check: `scripts/health-check.sh`\\n- May require Xcode Command Line Tools';
            case 'linux':
                return '**Linux-specific:**\\n- Use `.sh` files for scripts\\n- CLI wrappers: `bin/aitrackdown` and `bin/atd`\\n- Health check: `scripts/health-check.sh`\\n- Ensure proper file permissions';
            case 'win32':
                return '**Windows-specific:**\\n- Use `.bat` files for scripts\\n- CLI wrappers: `bin/aitrackdown.bat` and `bin/atd.bat`\\n- Health check: `scripts/health-check.bat`\\n- Path separators: Use backslashes in Windows paths';
            default:
                return `**Platform**: ${this.platform}\\n- Use appropriate script extensions for your platform\\n- Ensure proper file permissions on CLI wrappers`;
        }
    }

    /**
     * Run all fixes
     */
    async run() {
        this.log(`🔧 Starting NPM deployment fixes for version ${this.version}`);
        this.log(`📁 Working directory: ${this.workingDir}`);
        console.log('');
        
        try {
            const versionsUpdated = await this.fixDeployedInstanceVersions();
            const claudemdDeployed = await this.deployFrameworkClaudemd();
            
            console.log('');
            this.log('📊 Fix Summary:', 'info');
            this.log(`   - Deployed instances updated: ${versionsUpdated ? 'Yes' : 'No'}`);
            this.log(`   - Framework CLAUDE.md deployed: ${claudemdDeployed ? 'Yes' : 'No'}`);
            
            if (versionsUpdated || claudemdDeployed) {
                console.log('');
                this.log('🎉 Fixes completed successfully!', 'success');
                this.log('Run "npx claude-pm --system-info" to verify fixes');
            } else {
                console.log('');
                this.log('✨ Everything is already up-to-date!', 'success');
            }
            
        } catch (error) {
            this.log(`Fix process failed: ${error.message}`, 'error');
            process.exit(1);
        }
    }
}

// CLI execution
if (require.main === module) {
    const fixer = new NPMDeploymentFixer();
    fixer.run();
}

module.exports = NPMDeploymentFixer;