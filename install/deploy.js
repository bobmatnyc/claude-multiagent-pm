#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Portable Deployment Script
 * 
 * Creates fully functional framework deployments in any directory
 * with complete ai-trackdown-tools integration and 42-ticket management.
 * 
 * Usage:
 *   node install/deploy.js --target ~/Clients/project-name
 *   node install/deploy.js --target ~/Clients/project-name --verbose
 *   npm run deploy -- --target ~/Clients/project-name
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { spawn, execSync } = require('child_process');

class ClaudePMDeploymentEngine {
    constructor(options = {}) {
        this.targetDir = options.targetDir || process.cwd();
        this.platform = os.platform();
        this.verbose = options.verbose || false;
        this.skipValidation = options.skipValidation || false;
        this.dryRun = options.dryRun || false;
        
        this.packageDir = path.join(__dirname, '..');
        this.frameworkVersion = require('../package.json').version;
        
        // Source paths
        this.sources = {
            framework: path.join(this.packageDir, 'claude_pm'),
            templates: path.join(this.packageDir, 'templates'),
            schemas: path.join(this.packageDir, 'schemas'),
            config: path.join(this.packageDir, 'config'),
            docs: path.join(this.packageDir, 'docs'),
            requirements: path.join(this.packageDir, 'requirements'),
            scripts: path.join(this.packageDir, 'scripts'),
            tasks: path.join(this.packageDir, 'tasks')
        };
        
        this.aiTrackdownPath = this.findAiTrackdownPath();
    }

    /**
     * Log message with optional verbose filtering
     */
    log(message, force = false) {
        if (this.verbose || force) {
            console.log(`[Claude PM Deploy] ${message}`);
        }
    }

    /**
     * Find ai-trackdown-tools installation path
     */
    findAiTrackdownPath() {
        try {
            // Try to find in global node_modules
            const globalPath = execSync('npm root -g', { encoding: 'utf8' }).trim();
            const globalAiTrackdown = path.join(globalPath, '@bobmatnyc', 'ai-trackdown-tools', 'dist', 'index.js');
            
            if (fsSync.existsSync(globalAiTrackdown)) {
                this.log(`Found ai-trackdown-tools at: ${globalAiTrackdown}`);
                return globalAiTrackdown;
            }

            // Try to find in local node_modules
            const localPath = path.join(this.packageDir, '..', '..', 'node_modules', '@bobmatnyc', 'ai-trackdown-tools', 'dist', 'index.js');
            if (fsSync.existsSync(localPath)) {
                this.log(`Found ai-trackdown-tools at: ${localPath}`);
                return localPath;
            }

            // Try to find via npm ls
            const npmLs = execSync('npm ls -g @bobmatnyc/ai-trackdown-tools --depth=0 --parseable', { encoding: 'utf8' }).trim();
            if (npmLs) {
                const trackdownPath = path.join(npmLs, 'dist', 'index.js');
                if (fsSync.existsSync(trackdownPath)) {
                    this.log(`Found ai-trackdown-tools via npm ls: ${trackdownPath}`);
                    return trackdownPath;
                }
            }

            throw new Error('ai-trackdown-tools not found');
        } catch (error) {
            this.log(`Warning: Could not locate ai-trackdown-tools: ${error.message}`);
            return null;
        }
    }

    /**
     * Validate deployment environment
     */
    async validateEnvironment() {
        if (this.skipValidation) {
            this.log('Skipping environment validation');
            return true;
        }

        this.log('Validating deployment environment...', true);

        // Check Node.js version
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        
        if (majorVersion < 16) {
            throw new Error(`Node.js 16.0.0 or higher required. Found: ${nodeVersion}`);
        }
        
        this.log(`✓ Node.js ${nodeVersion} detected`);

        // Check Python availability
        try {
            let pythonCmd = 'python3';
            let pythonVersion;
            
            try {
                pythonVersion = execSync(`${pythonCmd} --version`, { encoding: 'utf8' }).trim();
            } catch (error) {
                pythonCmd = 'python';
                pythonVersion = execSync(`${pythonCmd} --version`, { encoding: 'utf8' }).trim();
            }
            
            const versionMatch = pythonVersion.match(/Python (\d+)\.(\d+)/);
            if (!versionMatch) {
                throw new Error('Unable to parse Python version');
            }
            
            const [, major, minor] = versionMatch.map(Number);
            if (major < 3 || (major === 3 && minor < 8)) {
                throw new Error(`Python 3.8+ required. Found: ${pythonVersion}`);
            }
            
            this.log(`✓ ${pythonVersion} detected`);
            this.pythonCmd = pythonCmd;
            
        } catch (error) {
            throw new Error('Python 3.8+ is required but not found');
        }

        // Check ai-trackdown-tools availability
        if (!this.aiTrackdownPath) {
            throw new Error('ai-trackdown-tools@1.0.1+ is required but not found. Install with: npm install -g @bobmatnyc/ai-trackdown-tools');
        }

        // Check target directory
        try {
            await fs.mkdir(this.targetDir, { recursive: true });
            this.log(`✓ Target directory ready: ${this.targetDir}`);
        } catch (error) {
            throw new Error(`Target directory not accessible: ${this.targetDir}`);
        }

        this.log('Environment validation completed', true);
        return true;
    }

    /**
     * Deploy framework core
     */
    async deployFrameworkCore() {
        this.log('Deploying framework core...', true);
        
        const targetFramework = path.join(this.targetDir, 'claude_pm');
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would copy framework to: ${targetFramework}`);
            return;
        }
        
        try {
            await this.copyDirectory(this.sources.framework, targetFramework);
            this.log(`✓ Framework core deployed to ${targetFramework}`);
        } catch (error) {
            throw new Error(`Failed to deploy framework core: ${error.message}`);
        }
    }

    /**
     * Deploy templates and schemas
     */
    async deployTemplatesAndSchemas() {
        this.log('Deploying templates and schemas...', true);
        
        const deployments = [
            { src: this.sources.templates, dest: path.join(this.targetDir, 'templates') },
            { src: this.sources.schemas, dest: path.join(this.targetDir, 'schemas') },
            { src: this.sources.requirements, dest: path.join(this.targetDir, 'requirements') }
        ];
        
        for (const { src, dest } of deployments) {
            if (this.dryRun) {
                this.log(`[DRY RUN] Would deploy ${path.basename(src)} to: ${dest}`);
                continue;
            }
            
            try {
                await this.copyDirectory(src, dest);
                this.log(`✓ ${path.basename(src)} deployed to ${dest}`);
            } catch (error) {
                throw new Error(`Failed to deploy ${path.basename(src)}: ${error.message}`);
            }
        }
    }

    /**
     * Create ai-trackdown-tools CLI wrappers
     */
    async createAiTrackdownWrappers() {
        this.log('Creating ai-trackdown-tools CLI wrappers...', true);
        
        const binDir = path.join(this.targetDir, 'bin');
        await fs.mkdir(binDir, { recursive: true });
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would create CLI wrappers in: ${binDir}`);
            return;
        }
        
        // Create aitrackdown wrapper
        const aitrackdownScript = this.platform === 'win32' ? 
            this.createWindowsWrapper('aitrackdown') : 
            this.createUnixWrapper('aitrackdown');
        
        const aitrackdownPath = path.join(binDir, this.platform === 'win32' ? 'aitrackdown.bat' : 'aitrackdown');
        await fs.writeFile(aitrackdownPath, aitrackdownScript);
        
        if (this.platform !== 'win32') {
            await fs.chmod(aitrackdownPath, '755');
        }
        
        // Create atd alias wrapper
        const atdScript = this.platform === 'win32' ? 
            this.createWindowsWrapper('atd') : 
            this.createUnixWrapper('atd');
        
        const atdPath = path.join(binDir, this.platform === 'win32' ? 'atd.bat' : 'atd');
        await fs.writeFile(atdPath, atdScript);
        
        if (this.platform !== 'win32') {
            await fs.chmod(atdPath, '755');
        }
        
        this.log(`✓ AI-trackdown CLI wrappers created in ${binDir}`);
    }

    /**
     * Create Windows CLI wrapper
     */
    createWindowsWrapper(command) {
        return `@echo off
REM Claude PM Framework - ${command} wrapper
REM Generated by deployment script v${this.frameworkVersion}

cd /d "${this.targetDir}"
node "${this.aiTrackdownPath}" %*
`;
    }

    /**
     * Create Unix CLI wrapper
     */
    createUnixWrapper(command) {
        return `#!/bin/bash
# Claude PM Framework - ${command} wrapper
# Generated by deployment script v${this.frameworkVersion}

cd "${this.targetDir}"
node "${this.aiTrackdownPath}" "$@"
`;
    }

    /**
     * Initialize task hierarchy
     */
    async initializeTaskHierarchy() {
        this.log('Initializing task hierarchy...', true);
        
        const tasksDir = path.join(this.targetDir, 'tasks');
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would initialize task hierarchy in: ${tasksDir}`);
            return;
        }
        
        try {
            // Copy existing tasks structure if available
            if (fsSync.existsSync(this.sources.tasks)) {
                await this.copyDirectory(this.sources.tasks, tasksDir);
            } else {
                // Create basic structure
                await fs.mkdir(path.join(tasksDir, 'epics'), { recursive: true });
                await fs.mkdir(path.join(tasksDir, 'issues'), { recursive: true });
                await fs.mkdir(path.join(tasksDir, 'tasks'), { recursive: true });
                await fs.mkdir(path.join(tasksDir, 'prs'), { recursive: true });
                await fs.mkdir(path.join(tasksDir, 'templates'), { recursive: true });
            }
            
            this.log(`✓ Task hierarchy initialized in ${tasksDir}`);
        } catch (error) {
            throw new Error(`Failed to initialize task hierarchy: ${error.message}`);
        }
    }

    /**
     * Generate deployment-specific configuration
     */
    async generateDeploymentConfig() {
        this.log('Generating deployment configuration...', true);
        
        const configDir = path.join(this.targetDir, '.claude-pm');
        await fs.mkdir(configDir, { recursive: true });
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would generate config in: ${configDir}`);
            return;
        }
        
        const config = {
            version: this.frameworkVersion,
            deployedAt: new Date().toISOString(),
            platform: this.platform,
            deploymentDir: this.targetDir,
            pythonCmd: this.pythonCmd || 'python3',
            aiTrackdownPath: this.aiTrackdownPath,
            paths: {
                framework: path.join(this.targetDir, 'claude_pm'),
                templates: path.join(this.targetDir, 'templates'),
                schemas: path.join(this.targetDir, 'schemas'),
                tasks: path.join(this.targetDir, 'tasks'),
                bin: path.join(this.targetDir, 'bin'),
                config: configDir
            },
            features: {
                aiTrackdownIntegration: true,
                memoryIntegration: true,
                multiAgentSupport: true,
                portableDeployment: true
            }
        };
        
        const configPath = path.join(configDir, 'config.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));
        
        this.log(`✓ Deployment configuration created at ${configPath}`);
    }

    /**
     * Generate deployment-specific CLAUDE.md
     */
    async generateClaudeConfig() {
        this.log('Generating deployment CLAUDE.md...', true);
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would generate CLAUDE.md in: ${this.targetDir}`);
            return;
        }
        
        try {
            // Read template
            const templatePath = path.join(this.packageDir, 'templates', 'deployment-claude.md');
            let claudeTemplate = await fs.readFile(templatePath, 'utf8');
            
            // Replace placeholders
            const nodeVersion = process.version;
            const deploymentId = Date.now();
            const deploymentDate = new Date().toISOString();
            
            const replacements = {
                '{{DEPLOYMENT_DIR}}': this.targetDir,
                '{{FRAMEWORK_VERSION}}': this.frameworkVersion,
                '{{DEPLOYMENT_DATE}}': deploymentDate,
                '{{PLATFORM}}': this.platform,
                '{{PYTHON_CMD}}': this.pythonCmd || 'python3',
                '{{AI_TRACKDOWN_PATH}}': this.aiTrackdownPath || 'ai-trackdown-tools not found',
                '{{NODE_VERSION}}': nodeVersion,
                '{{DEPLOYMENT_ID}}': deploymentId,
                '{{LAST_UPDATED}}': deploymentDate,
                '{{PLATFORM_NOTES}}': this.getPlatformNotes()
            };
            
            for (const [placeholder, value] of Object.entries(replacements)) {
                claudeTemplate = claudeTemplate.replace(new RegExp(placeholder, 'g'), value);
            }
            
            const claudePath = path.join(this.targetDir, 'CLAUDE.md');
            await fs.writeFile(claudePath, claudeTemplate);
            
            this.log(`✓ CLAUDE.md generated at ${claudePath}`);
        } catch (error) {
            throw new Error(`Failed to generate CLAUDE.md: ${error.message}`);
        }
    }

    /**
     * Get platform-specific notes
     */
    getPlatformNotes() {
        switch (this.platform) {
            case 'win32':
                return `**Windows-specific:**
- Use \`.bat\` files for scripts
- CLI wrappers: \`bin/aitrackdown.bat\` and \`bin/atd.bat\`
- Health check: \`scripts/health-check.bat\`
- Path separators: Use backslashes in Windows paths`;
            
            case 'darwin':
                return `**macOS-specific:**
- Use \`.sh\` files for scripts
- CLI wrappers: \`bin/aitrackdown\` and \`bin/atd\`
- Health check: \`scripts/health-check.sh\`
- May require Xcode Command Line Tools`;
            
            case 'linux':
                return `**Linux-specific:**
- Use \`.sh\` files for scripts
- CLI wrappers: \`bin/aitrackdown\` and \`bin/atd\`
- Health check: \`scripts/health-check.sh\`
- Ensure proper file permissions`;
            
            default:
                return `**Platform**: ${this.platform}
- Use appropriate script extensions for your platform
- Ensure proper file permissions on CLI wrappers`;
        }
    }

    /**
     * Create health check script
     */
    async createHealthCheck() {
        this.log('Creating health check script...', true);
        
        const scriptsDir = path.join(this.targetDir, 'scripts');
        await fs.mkdir(scriptsDir, { recursive: true });
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would create health check in: ${scriptsDir}`);
            return;
        }
        
        const healthScript = this.platform === 'win32' ? 
            this.createWindowsHealthCheck() : 
            this.createUnixHealthCheck();
        
        const healthPath = path.join(scriptsDir, this.platform === 'win32' ? 'health-check.bat' : 'health-check.sh');
        await fs.writeFile(healthPath, healthScript);
        
        if (this.platform !== 'win32') {
            await fs.chmod(healthPath, '755');
        }
        
        this.log(`✓ Health check script created at ${healthPath}`);
    }

    /**
     * Create Unix health check script
     */
    createUnixHealthCheck() {
        return `#!/bin/bash
# Claude PM Framework - Health Check
# Generated by deployment script v${this.frameworkVersion}

echo "🔍 Claude PM Framework Health Check"
echo "======================================"

cd "${this.targetDir}"

# Check framework core
if [ -d "claude_pm" ]; then
    echo "✓ Framework core present"
else
    echo "❌ Framework core missing"
    exit 1
fi

# Check CLI wrappers
if [ -x "bin/aitrackdown" ]; then
    echo "✓ aitrackdown CLI available"
else
    echo "❌ aitrackdown CLI missing"
    exit 1
fi

# Check configuration
if [ -f ".claude-pm/config.json" ]; then
    echo "✓ Deployment configuration present"
else
    echo "❌ Deployment configuration missing"
    exit 1
fi

# Test AI-trackdown functionality
if ./bin/aitrackdown status >/dev/null 2>&1; then
    echo "✓ AI-trackdown integration working"
else
    echo "⚠ AI-trackdown integration issue"
fi

# Check Python environment
if ${this.pythonCmd} --version >/dev/null 2>&1; then
    echo "✓ Python environment ready"
else
    echo "❌ Python environment issue"
    exit 1
fi

echo "======================================"
echo "🎉 Health check completed successfully"
`;
    }

    /**
     * Create Windows health check script
     */
    createWindowsHealthCheck() {
        return `@echo off
REM Claude PM Framework - Health Check
REM Generated by deployment script v${this.frameworkVersion}

echo 🔍 Claude PM Framework Health Check
echo ======================================

cd /d "${this.targetDir}"

REM Check framework core
if exist "claude_pm" (
    echo ✓ Framework core present
) else (
    echo ❌ Framework core missing
    exit /b 1
)

REM Check CLI wrappers
if exist "bin\\aitrackdown.bat" (
    echo ✓ aitrackdown CLI available
) else (
    echo ❌ aitrackdown CLI missing
    exit /b 1
)

REM Check configuration
if exist ".claude-pm\\config.json" (
    echo ✓ Deployment configuration present
) else (
    echo ❌ Deployment configuration missing
    exit /b 1
)

REM Check Python environment
${this.pythonCmd} --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python environment ready
) else (
    echo ❌ Python environment issue
    exit /b 1
)

echo ======================================
echo 🎉 Health check completed successfully
`;
    }

    /**
     * Recursively copy directory
     */
    async copyDirectory(src, dest) {
        await fs.mkdir(dest, { recursive: true });
        
        const items = await fs.readdir(src);
        
        for (const item of items) {
            const srcPath = path.join(src, item);
            const destPath = path.join(dest, item);
            
            const stat = await fs.stat(srcPath);
            
            if (stat.isDirectory()) {
                await this.copyDirectory(srcPath, destPath);
            } else {
                await fs.copyFile(srcPath, destPath);
            }
        }
    }

    /**
     * Main deployment process
     */
    async deploy() {
        try {
            this.log(`🚀 Starting Claude PM Framework deployment to: ${this.targetDir}`, true);
            
            await this.validateEnvironment();
            await this.deployFrameworkCore();
            await this.deployTemplatesAndSchemas();
            await this.createAiTrackdownWrappers();
            await this.initializeTaskHierarchy();
            await this.generateDeploymentConfig();
            await this.generateClaudeConfig();
            await this.createHealthCheck();
            
            this.log('🎉 Claude PM Framework deployment completed successfully!', true);
            this.log(`Framework location: ${path.join(this.targetDir, 'claude_pm')}`, true);
            this.log(`Configuration: ${path.join(this.targetDir, '.claude-pm', 'config.json')}`, true);
            this.log(`Health check: ${path.join(this.targetDir, 'scripts', this.platform === 'win32' ? 'health-check.bat' : 'health-check.sh')}`, true);
            this.log(`AI-trackdown CLI: ${path.join(this.targetDir, 'bin', 'aitrackdown')}`, true);
            
            return true;
            
        } catch (error) {
            this.log(`❌ Deployment failed: ${error.message}`, true);
            throw error;
        }
    }
}

// CLI interface when run directly
if (require.main === module) {
    const args = process.argv.slice(2);
    
    const options = {
        targetDir: process.cwd(),
        verbose: args.includes('--verbose') || args.includes('-v'),
        skipValidation: args.includes('--skip-validation'),
        dryRun: args.includes('--dry-run')
    };
    
    // Parse target directory
    const targetIndex = args.findIndex(arg => arg === '--target' || arg === '-t');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
        options.targetDir = path.resolve(args[targetIndex + 1]);
    }
    
    const deployer = new ClaudePMDeploymentEngine(options);
    
    deployer.deploy()
        .then(() => {
            process.exit(0);
        })
        .catch((error) => {
            console.error('Deployment failed:', error.message);
            process.exit(1);
        });
}

module.exports = ClaudePMDeploymentEngine;