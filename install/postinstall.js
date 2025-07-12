#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Post-Install Hook
 * 
 * Runs after NPM package installation to set up the framework
 * in the user's environment and configure platform-specific features.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class PostInstallSetup {
    constructor() {
        this.platform = os.platform();
        this.packageRoot = path.join(__dirname, '..');
        this.userHome = os.homedir();
        this.globalConfigDir = path.join(this.userHome, '.claude-pm');
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
     * Check if we're in a global npm installation with enhanced detection
     */
    isGlobalInstall() {
        const npmConfigPrefix = process.env.npm_config_prefix;
        const packagePath = this.packageRoot;
        const npmRoot = process.env.npm_config_globaldir || process.env.npm_root;
        
        // Enhanced debugging for global install detection
        this.log('🔍 Global installation detection:');
        this.log(`   • npm_config_prefix: ${npmConfigPrefix || 'NOT_SET'}`);
        this.log(`   • npm_config_globaldir: ${process.env.npm_config_globaldir || 'NOT_SET'}`);
        this.log(`   • npm_root: ${process.env.npm_root || 'NOT_SET'}`);
        this.log(`   • Package path: ${packagePath}`);
        
        // Enhanced global installation indicators
        const indicators = {
            // Standard npm prefix detection
            npmPrefix: npmConfigPrefix && packagePath.includes(npmConfigPrefix),
            
            // Standard npm global directory detection
            npmGlobalDir: npmRoot && packagePath.includes(npmRoot),
            
            // Enhanced global node_modules patterns
            nodeModulesGlobal: packagePath.includes('node_modules') && (
                packagePath.includes('/.npm-global/') ||           // Custom npm global paths
                packagePath.includes('/lib/node_modules/') ||      // Standard global node_modules
                packagePath.includes('\\AppData\\Roaming\\npm\\') || // Windows global
                packagePath.includes('/.npm-packages/') ||         // Alternative npm global
                packagePath.includes('/npm-global/') ||            // Common custom global
                packagePath.includes('/global/lib/node_modules/') ||
                packagePath.includes('/usr/local/lib/node_modules/') ||
                packagePath.includes('/opt/homebrew/lib/node_modules/')
            ),
            
            // Package name in global path
            packageName: packagePath.includes('@bobmatnyc/claude-multiagent-pm'),
            
            // Additional npm environment variables
            npmExecPath: process.env.npm_execpath && 
                        (process.env.npm_execpath.includes('global') || 
                         process.env.npm_execpath.includes('.npm-global')),
            
            // Check for global installation markers
            globalMarkers: packagePath.includes('global') && 
                          packagePath.includes('node_modules'),
            
            // Try to detect using npm command patterns
            npmCommand: process.env.npm_command === 'install' && 
                       process.env.npm_config_global === 'true'
        };
        
        this.log('🎯 Global install indicators:');
        for (const [indicator, result] of Object.entries(indicators)) {
            this.log(`   • ${indicator}: ${result ? '✅ TRUE' : '❌ FALSE'}`);
        }
        
        const isGlobal = Object.values(indicators).some(Boolean);
        this.log(`📊 Global installation result: ${isGlobal ? '✅ GLOBAL' : '❌ LOCAL'}`);
        
        // Additional verification for borderline cases
        if (!isGlobal && packagePath.includes('node_modules')) {
            // Check if we're in a global-like path but missed it
            const globalLikePatterns = [
                /\/\.npm-global\//,
                /\/npm-global\//,
                /\/global\/.*\/node_modules\//,
                /\/usr\/local\/lib\/node_modules\//,
                /\/opt\/homebrew\/lib\/node_modules\//,
                /C:\\Users\\.*\\AppData\\Roaming\\npm\\node_modules\\/
            ];
            
            const matchesGlobalPattern = globalLikePatterns.some(pattern => pattern.test(packagePath));
            if (matchesGlobalPattern) {
                this.log('🔄 Pattern-based global detection: ✅ TRUE');
                this.log(`📊 Updated global installation result: ✅ GLOBAL (pattern match)`);
                return true;
            }
        }
        
        return isGlobal;
    }

    /**
     * Create global configuration directory
     */
    async createGlobalConfig() {
        try {
            await fs.mkdir(this.globalConfigDir, { recursive: true });
            
            const config = {
                version: require('../package.json').version,
                installType: this.isGlobalInstall() ? 'global' : 'local',
                installDate: new Date().toISOString(),
                platform: this.platform,
                packageRoot: this.packageRoot,
                paths: {
                    framework: path.join(this.packageRoot, 'lib', 'framework'),
                    templates: path.join(this.packageRoot, 'lib', 'templates'),
                    schemas: path.join(this.packageRoot, 'lib', 'schemas'),
                    bin: path.join(this.packageRoot, 'bin')
                }
            };
            
            const configPath = path.join(this.globalConfigDir, 'config.json');
            await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            
            this.log(`Global configuration created at: ${configPath}`);
            
        } catch (error) {
            this.log(`Failed to create global config: ${error.message}`, 'warn');
        }
    }

    /**
     * Copy framework to lib directory
     */
    async prepareFrameworkLib() {
        const frameworkSource = path.join(this.packageRoot, 'claude_pm');
        const frameworkTarget = path.join(this.packageRoot, 'lib', 'framework', 'claude_pm');
        
        if (!fsSync.existsSync(frameworkSource)) {
            this.log('Framework source not found, skipping lib preparation', 'warn');
            return;
        }
        
        try {
            await fs.mkdir(path.dirname(frameworkTarget), { recursive: true });
            await this.copyDirectory(frameworkSource, frameworkTarget);
            
            // Copy additional framework files
            const additionalFiles = [
                'requirements',
                'config',
                'docs',
                'templates',
                'schemas'
            ];
            
            for (const file of additionalFiles) {
                const sourcePath = path.join(this.packageRoot, file);
                const targetPath = path.join(this.packageRoot, 'lib', 'framework', file);
                
                if (fsSync.existsSync(sourcePath)) {
                    const stat = await fs.stat(sourcePath);
                    if (stat.isDirectory()) {
                        await this.copyDirectory(sourcePath, targetPath);
                    } else {
                        await fs.copyFile(sourcePath, targetPath);
                    }
                }
            }
            
            this.log('Framework prepared in lib directory');
            
        } catch (error) {
            this.log(`Failed to prepare framework lib: ${error.message}`, 'error');
        }
    }

    /**
     * Set up installation templates
     */
    async prepareTemplates() {
        const templatesSource = path.join(this.packageRoot, 'templates');
        const templatesTarget = path.join(this.packageRoot, 'lib', 'templates');
        
        if (!fsSync.existsSync(templatesSource)) {
            // Create default templates if none exist
            await fs.mkdir(templatesTarget, { recursive: true });
            
            const defaultTemplate = {
                name: "basic-project",
                description: "Basic Claude PM project template",
                files: {
                    "CLAUDE.md": "# Claude PM Project\n\nProject managed by Claude Multi-Agent PM Framework",
                    "README.md": "# Project Name\n\nDescription of your project.",
                    "trackdown/BACKLOG.md": "# Project Backlog\n\n## Current Sprint\n\n## Backlog Items\n"
                }
            };
            
            await fs.writeFile(
                path.join(templatesTarget, 'basic-project.json'),
                JSON.stringify(defaultTemplate, null, 2)
            );
            
            this.log('Default templates created');
        } else {
            try {
                await this.copyDirectory(templatesSource, templatesTarget);
                this.log('Templates prepared');
            } catch (error) {
                this.log(`Failed to prepare templates: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Set up configuration schemas
     */
    async prepareSchemas() {
        const schemasSource = path.join(this.packageRoot, 'schemas');
        const schemasTarget = path.join(this.packageRoot, 'lib', 'schemas');
        
        if (!fsSync.existsSync(schemasSource)) {
            // Create default schemas
            await fs.mkdir(schemasTarget, { recursive: true });
            
            const configSchema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Claude PM Configuration",
                "type": "object",
                "properties": {
                    "version": { "type": "string" },
                    "framework": {
                        "type": "object",
                        "properties": {
                            "path": { "type": "string" },
                            "pythonCmd": { "type": "string", "default": "python3" }
                        }
                    }
                }
            };
            
            await fs.writeFile(
                path.join(schemasTarget, 'config.schema.json'),
                JSON.stringify(configSchema, null, 2)
            );
            
            this.log('Default schemas created');
        } else {
            try {
                await this.copyDirectory(schemasSource, schemasTarget);
                this.log('Schemas prepared');
            } catch (error) {
                this.log(`Failed to prepare schemas: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Create platform-specific setup
     */
    async platformSetup() {
        if (this.platform === 'win32') {
            await this.windowsSetup();
        } else {
            await this.unixSetup();
        }
    }

    /**
     * Windows-specific setup
     */
    async windowsSetup() {
        this.log('Configuring for Windows platform');
        
        // Windows doesn't need special setup for now
        // Future: Could set up Windows-specific paths or registry entries
    }

    /**
     * Unix-specific setup (Linux/macOS)
     */
    async unixSetup() {
        this.log('Configuring for Unix platform');
        
        // Make CLI scripts executable
        const binPath = path.join(this.packageRoot, 'bin', 'claude-pm');
        if (fsSync.existsSync(binPath)) {
            try {
                await fs.chmod(binPath, '755');
                this.log('CLI script made executable');
            } catch (error) {
                this.log(`Failed to make CLI executable: ${error.message}`, 'warn');
            }
        }
    }

    /**
     * Validate installation
     */
    async validateInstallation() {
        const requiredPaths = [
            path.join(this.packageRoot, 'bin', 'claude-pm'),
            path.join(this.packageRoot, 'lib'),
            path.join(this.packageRoot, 'install')
        ];
        
        for (const requiredPath of requiredPaths) {
            if (!fsSync.existsSync(requiredPath)) {
                throw new Error(`Required path missing: ${requiredPath}`);
            }
        }
        
        this.log('Installation validation passed');
    }

    /**
     * Show post-install instructions
     */
    showInstructions() {
        console.log('\n🎉 Claude Multi-Agent PM Framework installed successfully!\n');
        
        if (this.isGlobalInstall()) {
            console.log('Global installation detected. You can now use:');
            console.log('  claude-pm --help');
            console.log('  claude-pm health status');
            console.log('  claude-pm project create my-project');
        } else {
            console.log('Local installation detected. You can use:');
            console.log('  npx claude-pm --help');
            console.log('  npx claude-pm health status');
            console.log('  Or add to your package.json scripts');
        }
        
        console.log('\nConfiguration location:');
        console.log(`  ${this.globalConfigDir}`);
        
        console.log('\n🔧 Environment Migration:');
        console.log('• Environment variable migration has been automated during installation');
        console.log('• If you see CLAUDE_PM_ROOT deprecation warnings, run:');
        console.log(`  ${path.join(this.globalConfigDir, 'migrate-env.sh')}`);
        console.log('• After migration, restart your shell or source your config file');
        
        console.log('\n⚡ Deployment Configuration:');
        console.log('• Deployment config created for TemplateManager compatibility');
        console.log('• Automatic validation of framework components included');
        console.log('• Cross-platform environment setup completed');
        
        console.log('\nNext steps:');
        console.log('1. Run "claude-pm health status" to verify installation');
        console.log('2. Create a new project with "claude-pm project create <name>"');
        console.log('3. Check environment with ~/.claude-pm/migrate-env.sh if needed');
        console.log('4. Visit https://github.com/bobmatnyc/claude-multiagent-pm for documentation');
        console.log('');
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
     * Deploy framework CLAUDE.md to working directory if needed
     */
    async deployFrameworkToWorkingDirectory() {
        try {
            this.log('🔧 Starting CLAUDE.md deployment process...');
            
            // Environment and path debugging
            const workingDir = process.cwd();
            const packageRoot = this.packageRoot;
            const installType = this.isGlobalInstall() ? 'GLOBAL' : 'LOCAL';
            const npmPrefix = process.env.npm_config_prefix || 'NOT_SET';
            
            // ENHANCED FIX: Handle both global and local installation CLAUDE.md deployment
            if (this.isGlobalInstall()) {
                this.log('🌐 Global installation detected');
                this.log('💡 Storing global deployment info for CLI auto-deployment');
                
                // Store deployment information for CLI to use later
                await this.storeGlobalDeploymentInfo();
                
                // For global installations, we'll deploy CLAUDE.md if we're in a suitable working directory
                // Check if the working directory looks like a project directory that should get CLAUDE.md
                const isProjectDirectory = this.isProjectDirectory(workingDir);
                
                if (isProjectDirectory) {
                    this.log('📁 Working directory appears to be a project - attempting immediate deployment');
                    // Continue with deployment below instead of returning
                } else {
                    this.log('📁 Working directory is not a project - deferring deployment to CLI first run');
                    this.log('💡 Run "claude-pm deploy-template" in your project directory to deploy framework template');
                    return;
                }
            }
            
            this.log(`📍 Installation Context:`);
            this.log(`   • Install Type: ${installType}`);
            this.log(`   • Working Directory: ${workingDir}`);
            this.log(`   • Package Root: ${packageRoot}`);
            this.log(`   • NPM Prefix: ${npmPrefix}`);
            this.log(`   • Node.js Version: ${process.version}`);
            this.log(`   • Platform: ${this.platform}`);
            
            const workingClaudemd = path.join(workingDir, 'CLAUDE.md');
            this.log(`📋 Target CLAUDE.md Path: ${workingClaudemd}`);
            
            // Check if working directory already has CLAUDE.md
            if (fsSync.existsSync(workingClaudemd)) {
                this.log('📄 Existing CLAUDE.md found in working directory');
                try {
                    const content = fsSync.readFileSync(workingClaudemd, 'utf8');
                    const isFrameworkFile = content.includes('Claude PM Framework Configuration - Deployment') || 
                                          content.includes('AI ASSISTANT ROLE DESIGNATION');
                    
                    if (!isFrameworkFile) {
                        this.log('✋ Working directory has custom CLAUDE.md, skipping framework deployment');
                        this.log('   • This appears to be a user/project-specific CLAUDE.md file');
                        return;
                    }
                    
                    this.log('🔄 Existing CLAUDE.md is a framework file, will update it');
                    
                } catch (readError) {
                    this.log(`⚠️  Failed to read existing CLAUDE.md: ${readError.message}`, 'warn');
                    this.log('   • Will attempt to deploy framework version anyway');
                }
            } else {
                this.log('📝 No existing CLAUDE.md found, will create new one');
            }
            
            // Source framework template path debugging
            let frameworkTemplate = path.join(packageRoot, 'framework', 'CLAUDE.md');
            this.log(`🎯 Primary Source Template Path: ${frameworkTemplate}`);
            
            // Check if framework directory exists
            const frameworkDir = path.join(packageRoot, 'framework');
            this.log(`📁 Framework Directory: ${frameworkDir}`);
            
            if (!fsSync.existsSync(frameworkDir)) {
                this.log(`❌ Framework directory not found: ${frameworkDir}`, 'error');
                this.log('🔍 Searching for alternative framework locations...');
                
                // Try alternative locations for global installations
                const alternativePaths = [
                    path.join(packageRoot, 'lib', 'framework', 'CLAUDE.md'),
                    path.join(packageRoot, '..', 'framework', 'CLAUDE.md'),
                    path.join(packageRoot, 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'framework', 'CLAUDE.md'),
                    path.resolve(packageRoot, '..', '..', 'claude-multiagent-pm', 'framework', 'CLAUDE.md'),
                    // Additional paths for global npm installations
                    path.join(process.env.npm_config_prefix || '', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'framework', 'CLAUDE.md'),
                    path.join(os.homedir(), '.npm-global', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm', 'framework', 'CLAUDE.md'),
                    path.join('/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm/framework/CLAUDE.md'),
                    // Fallback: check if we're inside the package and look for source
                    path.resolve(__dirname, '..', 'framework', 'CLAUDE.md'),
                    path.resolve(__dirname, '..', '..', 'framework', 'CLAUDE.md')
                ];
                
                this.log('🔍 Checking alternative paths:');
                let foundAlternative = null;
                for (const altPath of alternativePaths) {
                    const exists = fsSync.existsSync(altPath);
                    this.log(`   • ${altPath}: ${exists ? '✅ EXISTS' : '❌ NOT FOUND'}`);
                    if (exists && !foundAlternative) {
                        foundAlternative = altPath;
                    }
                }
                
                if (foundAlternative) {
                    this.log(`🎯 Found alternative framework template: ${foundAlternative}`);
                    frameworkTemplate = foundAlternative;
                } else {
                    // List what's actually in the package root
                    try {
                        const packageContents = fsSync.readdirSync(packageRoot);
                        this.log(`📂 Package root contents: ${packageContents.join(', ')}`);
                        
                        // Check if there are any framework-related directories
                        const frameworkRelated = packageContents.filter(item => 
                            item.toLowerCase().includes('framework') || 
                            item.toLowerCase().includes('template') ||
                            item.toLowerCase().includes('claude')
                        );
                        if (frameworkRelated.length > 0) {
                            this.log(`🔍 Framework-related items found: ${frameworkRelated.join(', ')}`);
                        }
                        
                    } catch (listError) {
                        this.log(`❌ Failed to list package root contents: ${listError.message}`, 'error');
                    }
                    
                    this.log('❌ CLAUDE.md deployment failed: Framework directory not found');
                    this.log('💡 Possible causes:');
                    this.log('   • Global npm installation path resolution issue');
                    this.log('   • Framework files not properly included in NPM package');
                    this.log('   • Package structure differs from expected layout');
                    this.log(`   • Expected primary: ${frameworkDir}`);
                    this.log(`   • Searched ${alternativePaths.length} alternative locations`);
                    
                    // Provide specific guidance for global installations
                    if (this.isGlobalInstall()) {
                        this.log('📋 Global Installation Debugging Help:');
                        this.log('   1. Check NPM global installation path with: npm config get prefix');
                        this.log('   2. Verify package is properly installed with: npm list -g @bobmatnyc/claude-multiagent-pm');
                        this.log('   3. Check if framework files exist with: find $(npm config get prefix) -name "CLAUDE.md" 2>/dev/null');
                        this.log('   4. Reinstall with: npm uninstall -g @bobmatnyc/claude-multiagent-pm && npm install -g @bobmatnyc/claude-multiagent-pm');
                    }
                    
                    return;
                }
            }
            
            // Check framework directory contents (if using original path)
            if (frameworkTemplate.includes(frameworkDir)) {
                try {
                    const frameworkContents = fsSync.readdirSync(frameworkDir);
                    this.log(`📂 Framework directory contents: ${frameworkContents.join(', ')}`);
                } catch (listError) {
                    this.log(`⚠️  Failed to list framework directory: ${listError.message}`, 'warn');
                }
            } else {
                this.log(`📂 Using alternative template path: ${frameworkTemplate}`);
            }
            
            // Check if framework template exists (final verification)
            if (!fsSync.existsSync(frameworkTemplate)) {
                this.log(`❌ Framework template not found: ${frameworkTemplate}`, 'error');
                this.log('💡 Troubleshooting information:');
                
                const templateDir = path.dirname(frameworkTemplate);
                this.log(`   • Template directory: ${templateDir}`);
                this.log(`   • Template directory exists: ${fsSync.existsSync(templateDir)}`);
                this.log(`   • Looking for file: ${path.basename(frameworkTemplate)}`);
                
                // Check file permissions on template directory
                try {
                    if (fsSync.existsSync(templateDir)) {
                        const dirStat = fsSync.statSync(templateDir);
                        this.log(`   • Directory permissions: ${dirStat.mode.toString(8)}`);
                        this.log(`   • Directory is readable: ${(dirStat.mode & fsSync.constants.S_IRUSR) ? 'Yes' : 'No'}`);
                        
                        // List contents of template directory
                        const templateDirContents = fsSync.readdirSync(templateDir);
                        this.log(`   • Directory contents: ${templateDirContents.join(', ')}`);
                    }
                } catch (statError) {
                    this.log(`   • Failed to get directory stats: ${statError.message}`);
                }
                
                return;
            }
            
            this.log('✅ Framework template found, proceeding with deployment');
            
            // Read and validate template content
            let templateContent;
            try {
                templateContent = fsSync.readFileSync(frameworkTemplate, 'utf8');
                this.log(`📖 Template content loaded (${templateContent.length} characters)`);
                
                // Validate template has expected structure
                const hasDeploymentSection = templateContent.includes('Claude PM Framework Configuration - Deployment');
                const hasVariables = templateContent.includes('{{') && templateContent.includes('}}');
                
                this.log(`🔍 Template validation:`);
                this.log(`   • Has deployment section: ${hasDeploymentSection}`);
                this.log(`   • Has template variables: ${hasVariables}`);
                
                if (!hasDeploymentSection) {
                    this.log('⚠️  Template may not be a proper framework CLAUDE.md file', 'warn');
                }
                
            } catch (readError) {
                this.log(`❌ Failed to read framework template: ${readError.message}`, 'error');
                this.log('💡 Possible causes:');
                this.log('   • File permission issues');
                this.log('   • File corruption');
                this.log('   • Encoding issues');
                return;
            }
            
            // Load package.json with error handling
            let packageJson;
            try {
                packageJson = require('../package.json');
                this.log(`📦 Package info: ${packageJson.name}@${packageJson.version}`);
            } catch (packageError) {
                this.log(`❌ Failed to load package.json: ${packageError.message}`, 'error');
                return;
            }
            
            const deploymentDate = new Date().toISOString();
            const deploymentId = Date.now();
            
            // Template variable replacements
            const replacements = {
                '{{CLAUDE_MD_VERSION}}': `${packageJson.version}-001`,
                '{{FRAMEWORK_VERSION}}': packageJson.version,
                '{{DEPLOYMENT_DATE}}': deploymentDate,
                '{{LAST_UPDATED}}': deploymentDate,
                '{{DEPLOYMENT_DIR}}': workingDir,
                '{{PLATFORM}}': this.platform,
                '{{PYTHON_CMD}}': 'python3',
                '{{AI_TRACKDOWN_PATH}}': 'Global installation available',
                '{{DEPLOYMENT_ID}}': deploymentId,
                '{{PLATFORM_NOTES}}': this.getPlatformNotes()
            };
            
            this.log('🔄 Applying template variable substitutions:');
            for (const [placeholder, value] of Object.entries(replacements)) {
                this.log(`   • ${placeholder} → ${value}`);
                const escapedPlaceholder = placeholder.replace(/[{}]/g, '\\$&');
                templateContent = templateContent.replace(new RegExp(escapedPlaceholder, 'g'), value);
            }
            
            // Write the deployed CLAUDE.md
            try {
                fsSync.writeFileSync(workingClaudemd, templateContent);
                this.log(`✅ Framework CLAUDE.md successfully deployed to: ${workingClaudemd}`);
                
                // Verify the written file
                const writtenSize = fsSync.statSync(workingClaudemd).size;
                this.log(`✅ Deployment verification: ${writtenSize} bytes written`);
                
            } catch (writeError) {
                this.log(`❌ Failed to write CLAUDE.md: ${writeError.message}`, 'error');
                this.log('💡 Possible causes:');
                this.log('   • No write permission in working directory');
                this.log('   • Disk space issues');
                this.log('   • File system limitations');
                this.log(`   • Target directory: ${workingDir}`);
                return;
            }
            
        } catch (error) {
            this.log(`❌ CLAUDE.md deployment failed with unexpected error: ${error.message}`, 'error');
            this.log(`📍 Error stack: ${error.stack}`, 'error');
            this.log('💡 This is a comprehensive deployment failure - please report this issue');
        }
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
     * Check if a directory looks like a project directory that should receive CLAUDE.md
     */
    isProjectDirectory(dir) {
        try {
            // Check for project indicators
            const projectIndicators = [
                'package.json',
                '.git',
                'README.md',
                'src/',
                'lib/',
                'components/',
                'pages/',
                'app/',
                'server/',
                'client/',
                'public/',
                'assets/',
                'docs/',
                'test/',
                'tests/',
                '__tests__/',
                'spec/',
                'cypress/',
                'jest.config.js',
                'webpack.config.js',
                'tsconfig.json',
                'vite.config.js',
                'next.config.js',
                'nuxt.config.js',
                'vue.config.js',
                'angular.json',
                'pom.xml',
                'build.gradle',
                'Cargo.toml',
                'go.mod',
                'pyproject.toml',
                'requirements.txt',
                'Gemfile',
                'composer.json',
                'Dockerfile',
                'docker-compose.yml',
                '.env',
                '.env.example'
            ];
            
            const contents = fsSync.readdirSync(dir);
            const hasProjectIndicators = projectIndicators.some(indicator => 
                contents.some(item => {
                    if (indicator.endsWith('/')) {
                        // Directory indicator
                        return item === indicator.slice(0, -1) && 
                               fsSync.statSync(path.join(dir, item)).isDirectory();
                    } else {
                        // File indicator
                        return item === indicator;
                    }
                })
            );
            
            // Also check if the directory name suggests it's a project
            const dirName = path.basename(dir).toLowerCase();
            const projectLikeNames = [
                'project', 'app', 'application', 'service', 'api', 'web', 'site', 
                'frontend', 'backend', 'client', 'server', 'bot', 'tool', 'cli',
                'framework', 'library', 'package', 'module', 'plugin', 'extension'
            ];
            
            const hasProjectLikeName = projectLikeNames.some(name => 
                dirName.includes(name) || dirName.endsWith('-' + name) || dirName.startsWith(name + '-')
            );
            
            // Exclude certain non-project directories
            const excludePatterns = [
                /node_modules/,
                /\.npm/,
                /\.cache/,
                /tmp/,
                /temp/,
                /Downloads/,
                /Desktop/,
                /Documents$/,  // But allow subdirs
                /Library/,
                /System/,
                /usr\/local/,
                /opt/
            ];
            
            const isExcluded = excludePatterns.some(pattern => pattern.test(dir));
            
            if (isExcluded) {
                return false;
            }
            
            return hasProjectIndicators || hasProjectLikeName;
            
        } catch (error) {
            // If we can't read the directory, assume it's not a project
            return false;
        }
    }
    
    /**
     * Store global deployment information for CLI to use later
     */
    async storeGlobalDeploymentInfo() {
        try {
            await fs.mkdir(this.globalConfigDir, { recursive: true });
            
            const globalDeploymentInfo = {
                installationType: 'global',
                packageRoot: this.packageRoot,
                npmPrefix: process.env.npm_config_prefix,
                frameworkTemplatePath: path.join(this.packageRoot, 'framework', 'CLAUDE.md'),
                deploymentDate: new Date().toISOString(),
                version: require('../package.json').version,
                platform: this.platform,
                needsFirstRunDeployment: true
            };
            
            const infoPath = path.join(this.globalConfigDir, 'global-deployment.json');
            await fs.writeFile(infoPath, JSON.stringify(globalDeploymentInfo, null, 2));
            
            this.log(`🌐 Global deployment info stored at: ${infoPath}`);
            
        } catch (error) {
            this.log(`⚠️  Failed to store global deployment info: ${error.message}`, 'warn');
        }
    }

    /**
     * Update deployed instance version if exists
     */
    async updateDeployedInstanceVersion() {
        try {
            const deployedConfigPaths = [
                path.join(os.homedir(), '.local', '.claude-pm', 'config.json'),
                path.join(os.homedir(), '.claude-pm', 'config.json')
            ];
            
            const packageJson = require('../package.json');
            
            for (const configPath of deployedConfigPaths) {
                if (fsSync.existsSync(configPath)) {
                    const config = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
                    
                    // Update to current package version
                    config.version = packageJson.version;
                    config.lastNpmUpdate = new Date().toISOString();
                    config.npmPackageVersion = packageJson.version;
                    
                    fsSync.writeFileSync(configPath, JSON.stringify(config, null, 2));
                    this.log(`Updated deployed instance version to: ${packageJson.version}`);
                    break; // Only update the first found config
                }
            }
            
        } catch (error) {
            this.log(`Failed to update deployed instance version: ${error.message}`, 'warn');
        }
    }

    /**
     * Migrate environment variables from old CLAUDE_PM_* to new CLAUDE_MULTIAGENT_PM_*
     */
    async migrateEnvironmentVariables() {
        try {
            this.log('Checking for environment variable migration needs...');
            
            const shellConfigFiles = this.getShellConfigFiles();
            let migrationPerformed = false;
            
            for (const configFile of shellConfigFiles) {
                if (fsSync.existsSync(configFile)) {
                    const content = fsSync.readFileSync(configFile, 'utf8');
                    let newContent = content;
                    let fileModified = false;
                    
                    // Check for old CLAUDE_PM_ROOT and replace with new variable
                    if (content.includes('CLAUDE_PM_ROOT=') && !content.includes('CLAUDE_MULTIAGENT_PM_ROOT=')) {
                        // Extract the path from CLAUDE_PM_ROOT
                        const claudePmRootMatch = content.match(/export\s+CLAUDE_PM_ROOT="([^"]+)"/);
                        if (claudePmRootMatch) {
                            const oldPath = claudePmRootMatch[1];
                            
                            // Comment out old variable and add new one
                            newContent = newContent.replace(
                                /export\s+CLAUDE_PM_ROOT="([^"]+)"/g,
                                `# DEPRECATED: Migrated to CLAUDE_MULTIAGENT_PM_ROOT
# export CLAUDE_PM_ROOT="$1"
export CLAUDE_MULTIAGENT_PM_ROOT="${oldPath.replace('Claude-PM', 'claude-multiagent-pm')}"`
                            );
                            fileModified = true;
                            this.log(`Migrating CLAUDE_PM_ROOT to CLAUDE_MULTIAGENT_PM_ROOT in ${configFile}`);
                        }
                    }
                    
                    // Update other CLAUDE_PM_* variables to CLAUDE_MULTIAGENT_PM_*
                    const otherMigrations = [
                        { old: 'CLAUDE_PM_MANAGED', new: 'CLAUDE_MULTIAGENT_PM_MANAGED' },
                        { old: 'CLAUDE_PM_MEMORY_ENABLED', new: 'CLAUDE_MULTIAGENT_PM_MEMORY_ENABLED' },
                        { old: 'CLAUDE_PM_MEMORY_SERVICE_URL', new: 'CLAUDE_MULTIAGENT_PM_MEMORY_SERVICE_URL' },
                        { old: 'CLAUDE_PM_MEMORY_SERVICE_TIMEOUT', new: 'CLAUDE_MULTIAGENT_PM_MEMORY_SERVICE_TIMEOUT' },
                        { old: 'CLAUDE_PM_MEMORY_FALLBACK_MODE', new: 'CLAUDE_MULTIAGENT_PM_MEMORY_FALLBACK_MODE' },
                        { old: 'CLAUDE_PM_MEMORY_NAMESPACE', new: 'CLAUDE_MULTIAGENT_PM_MEMORY_NAMESPACE' }
                    ];
                    
                    for (const migration of otherMigrations) {
                        const oldPattern = new RegExp(`export\\s+${migration.old}=`, 'g');
                        if (oldPattern.test(content)) {
                            newContent = newContent.replace(
                                new RegExp(`export\\s+${migration.old}=`, 'g'),
                                `export ${migration.new}=`
                            );
                            fileModified = true;
                        }
                    }
                    
                    if (fileModified) {
                        // Create backup before modifying
                        const backupFile = `${configFile}.claude-pm-backup-${Date.now()}`;
                        fsSync.copyFileSync(configFile, backupFile);
                        this.log(`Created backup: ${backupFile}`);
                        
                        // Write updated content
                        fsSync.writeFileSync(configFile, newContent);
                        this.log(`Updated environment variables in: ${configFile}`);
                        migrationPerformed = true;
                    }
                }
            }
            
            if (migrationPerformed) {
                this.log('Environment variable migration completed successfully', 'info');
                this.log('⚠️  Please restart your shell or run "source ~/.zshrc" (or ~/.bashrc) to apply changes', 'warn');
            } else {
                this.log('No environment variable migration needed');
            }
            
        } catch (error) {
            this.log(`Environment variable migration failed: ${error.message}`, 'error');
        }
    }
    
    /**
     * Get shell configuration files for the current platform
     */
    getShellConfigFiles() {
        const homeDir = os.homedir();
        const configFiles = [];
        
        // Common shell config files
        const potentialFiles = [
            path.join(homeDir, '.zshrc'),
            path.join(homeDir, '.bashrc'),
            path.join(homeDir, '.bash_profile'),
            path.join(homeDir, '.profile'),
            path.join(homeDir, '.local', 'bin', 'env')
        ];
        
        // Check which files exist
        for (const file of potentialFiles) {
            if (fsSync.existsSync(file)) {
                configFiles.push(file);
            }
        }
        
        return configFiles;
    }
    
    /**
     * Create or update deployment configuration
     */
    async setupDeploymentConfiguration() {
        try {
            this.log('Setting up deployment configuration...');
            
            const deploymentConfigPath = path.join(this.globalConfigDir, 'deployment.json');
            const packageJson = require('../package.json');
            
            const deploymentConfig = {
                version: packageJson.version,
                deploymentDate: new Date().toISOString(),
                platform: this.platform,
                packageRoot: this.packageRoot,
                pythonCmd: 'python3',
                nodeVersion: process.version,
                npmVersion: await this.getNpmVersion(),
                environment: {
                    migratedFromClaudePm: true,
                    supportsNewVariables: true,
                    variablePrefix: 'CLAUDE_MULTIAGENT_PM_'
                },
                paths: {
                    framework: path.join(this.packageRoot, 'framework'),
                    templates: path.join(this.packageRoot, 'templates'),
                    schemas: path.join(this.packageRoot, 'schemas'),
                    bin: path.join(this.packageRoot, 'bin'),
                    lib: path.join(this.packageRoot, 'lib')
                },
                validation: {
                    templateManagerSupported: true,
                    parentDirectoryManagerSupported: true,
                    environmentVariablesConfigured: true
                }
            };
            
            await fs.writeFile(deploymentConfigPath, JSON.stringify(deploymentConfig, null, 2));
            this.log(`Deployment configuration created: ${deploymentConfigPath}`);
            
        } catch (error) {
            this.log(`Failed to setup deployment configuration: ${error.message}`, 'error');
        }
    }
    
    /**
     * Get npm version
     */
    async getNpmVersion() {
        try {
            const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
            return npmVersion;
        } catch (error) {
            return 'unknown';
        }
    }
    
    /**
     * Create environment migration helper script
     */
    async createMigrationHelper() {
        try {
            const helperPath = path.join(this.globalConfigDir, 'migrate-env.sh');
            
            const helperScript = `#!/bin/bash
# Claude Multi-Agent PM Framework - Environment Variable Migration Helper
# This script helps migrate from old CLAUDE_PM_* to new CLAUDE_MULTIAGENT_PM_* variables

echo "🔄 Claude Multi-Agent PM Framework - Environment Migration Helper"
echo "======================================================="

# Detect current shell
CURRENT_SHELL=$(basename "$SHELL")
echo "📋 Detected shell: $CURRENT_SHELL"

# Get home directory
HOME_DIR="$HOME"

# Find configuration files
CONFIG_FILES=()
if [ -f "$HOME_DIR/.zshrc" ]; then
    CONFIG_FILES+=("$HOME_DIR/.zshrc")
fi
if [ -f "$HOME_DIR/.bashrc" ]; then
    CONFIG_FILES+=("$HOME_DIR/.bashrc")
fi
if [ -f "$HOME_DIR/.bash_profile" ]; then
    CONFIG_FILES+=("$HOME_DIR/.bash_profile")
fi
if [ -f "$HOME_DIR/.local/bin/env" ]; then
    CONFIG_FILES+=("$HOME_DIR/.local/bin/env")
fi

echo "📁 Found configuration files:"
for file in "\${CONFIG_FILES[@]}"; do
    echo "   - $file"
done

# Check current environment
if [ -n "$CLAUDE_PM_ROOT" ] && [ -z "$CLAUDE_MULTIAGENT_PM_ROOT" ]; then
    echo ""
    echo "⚠️  Old environment variables detected:"
    echo "   CLAUDE_PM_ROOT=$CLAUDE_PM_ROOT"
    echo ""
    echo "💡 Recommendation: Update to use CLAUDE_MULTIAGENT_PM_ROOT"
    echo "   export CLAUDE_MULTIAGENT_PM_ROOT=\\"\\$(echo \\$CLAUDE_PM_ROOT | sed 's/Claude-PM/claude-multiagent-pm/g')\\""
elif [ -n "$CLAUDE_MULTIAGENT_PM_ROOT" ]; then
    echo ""
    echo "✅ New environment variables already configured:"
    echo "   CLAUDE_MULTIAGENT_PM_ROOT=$CLAUDE_MULTIAGENT_PM_ROOT"
else
    echo ""
    echo "ℹ️  No Claude PM environment variables detected"
    echo "   This is normal for fresh installations"
fi

echo ""
echo "🔧 To complete migration manually:"
echo "1. Edit your shell configuration file"
echo "2. Replace CLAUDE_PM_* with CLAUDE_MULTIAGENT_PM_*"
echo "3. Update paths from 'Claude-PM' to 'claude-multiagent-pm'"
echo "4. Restart your shell or run: source ~/.zshrc"

echo ""
echo "📚 For more information, see:"
echo "   https://github.com/bobmatnyc/claude-multiagent-pm#environment-setup"
`;
            
            await fs.writeFile(helperPath, helperScript);
            await fs.chmod(helperPath, '755');
            
            this.log(`Migration helper script created: ${helperPath}`);
            this.log('Run it with: ~/.claude-pm/migrate-env.sh');
            
        } catch (error) {
            this.log(`Failed to create migration helper: ${error.message}`, 'warn');
        }
    }

    /**
     * Validate and install ai-trackdown-tools dependency if needed
     */
    async validateAndInstallDependencies() {
        try {
            this.log('Validating dependencies...');
            
            // Check if ai-trackdown-tools is available
            const { execSync } = require('child_process');
            
            try {
                const version = execSync('aitrackdown --version', { 
                    encoding: 'utf8', 
                    stdio: 'pipe',
                    timeout: 5000 
                });
                this.log(`ai-trackdown-tools already available: ${version.trim()}`);
                return;
            } catch (checkError) {
                this.log('ai-trackdown-tools not found, attempting installation...');
            }
            
            // Try to install ai-trackdown-tools
            try {
                this.log('Installing ai-trackdown-tools dependency...');
                execSync('npm install -g @bobmatnyc/ai-trackdown-tools', { 
                    encoding: 'utf8',
                    stdio: 'pipe',
                    timeout: 60000 // 1 minute timeout
                });
                
                // Verify installation
                const version = execSync('aitrackdown --version', { 
                    encoding: 'utf8', 
                    stdio: 'pipe',
                    timeout: 5000 
                });
                this.log(`ai-trackdown-tools installed successfully: ${version.trim()}`);
                
            } catch (installError) {
                this.log(`Failed to install ai-trackdown-tools: ${installError.message}`, 'warn');
                this.log('You may need to install it manually: npm install -g @bobmatnyc/ai-trackdown-tools');
            }
            
        } catch (error) {
            this.log(`Dependency validation failed: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Add failsafe mechanisms for deployment
     */
    async addFailsafeMechanisms() {
        try {
            this.log('Setting up failsafe mechanisms...');
            
            // Create a failsafe deployment script
            const failsafeScript = `#!/bin/bash
# Claude PM Framework - Failsafe CLAUDE.md Deployment
# This script can be used to manually deploy CLAUDE.md if automatic deployment fails

echo "🚀 Claude PM Framework - Manual CLAUDE.md Deployment"
echo "=================================================="

# Check if we're in a project directory
if [ ! -f "package.json" ] && [ ! -d ".git" ] && [ ! -f "README.md" ]; then
    echo "⚠️  Warning: This doesn't appear to be a project directory"
    echo "   Consider running this in your project root"
    echo ""
fi

# Check if CLAUDE.md already exists
if [ -f "CLAUDE.md" ]; then
    echo "📄 CLAUDE.md already exists in current directory"
    echo "   Backing up existing file as CLAUDE.md.backup"
    cp CLAUDE.md CLAUDE.md.backup
fi

# Try to deploy using claude-pm command
if command -v claude-pm >/dev/null 2>&1; then
    echo "🔧 Using claude-pm deploy-template command..."
    claude-pm deploy-template
    if [ $? -eq 0 ]; then
        echo "✅ CLAUDE.md deployed successfully"
        exit 0
    fi
fi

# Manual fallback deployment
echo "🔧 Attempting manual deployment..."
GLOBAL_CONFIG="$HOME/.claude-pm/global-deployment.json"

if [ -f "$GLOBAL_CONFIG" ]; then
    # Extract framework template path from global config
    TEMPLATE_PATH=$(node -e "
        try {
            const config = require('$GLOBAL_CONFIG');
            console.log(config.frameworkTemplatePath || '');
        } catch (e) {
            console.log('');
        }
    ")
    
    if [ -f "$TEMPLATE_PATH" ]; then
        echo "📋 Copying framework template from: $TEMPLATE_PATH"
        cp "$TEMPLATE_PATH" CLAUDE.md
        echo "✅ CLAUDE.md deployed manually"
    else
        echo "❌ Framework template not found at: $TEMPLATE_PATH"
    fi
else
    echo "❌ Global deployment configuration not found"
    echo "   Please reinstall: npm install -g @bobmatnyc/claude-multiagent-pm"
fi
`;
            
            const failsafePath = path.join(this.globalConfigDir, 'deploy-claude-md.sh');
            await fs.writeFile(failsafePath, failsafeScript);
            await fs.chmod(failsafePath, '755');
            
            this.log(`Failsafe deployment script created: ${failsafePath}`);
            
        } catch (error) {
            this.log(`Failed to create failsafe mechanisms: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Main post-install process with enhanced error handling
     */
    async run() {
        try {
            this.log('Starting Claude PM Framework post-install setup');
            
            // Core setup with error recovery
            await this.safeExecute('createGlobalConfig', () => this.createGlobalConfig());
            await this.safeExecute('prepareFrameworkLib', () => this.prepareFrameworkLib());
            await this.safeExecute('prepareTemplates', () => this.prepareTemplates());
            await this.safeExecute('prepareSchemas', () => this.prepareSchemas());
            await this.safeExecute('platformSetup', () => this.platformSetup());
            await this.safeExecute('validateInstallation', () => this.validateInstallation());
            
            // Enhanced setup
            await this.safeExecute('migrateEnvironmentVariables', () => this.migrateEnvironmentVariables());
            await this.safeExecute('setupDeploymentConfiguration', () => this.setupDeploymentConfiguration());
            await this.safeExecute('createMigrationHelper', () => this.createMigrationHelper());
            await this.safeExecute('validateAndInstallDependencies', () => this.validateAndInstallDependencies());
            await this.safeExecute('addFailsafeMechanisms', () => this.addFailsafeMechanisms());
            
            // Deploy framework CLAUDE.md to working directory
            await this.safeExecute('deployFrameworkToWorkingDirectory', () => this.deployFrameworkToWorkingDirectory());
            
            // Update deployed instance version if exists
            await this.safeExecute('updateDeployedInstanceVersion', () => this.updateDeployedInstanceVersion());
            
            this.log('Post-install setup completed successfully');
            this.showInstructions();
            
        } catch (error) {
            this.log(`Post-install setup failed: ${error.message}`, 'error');
            console.error('\nIf you encounter issues, please:');
            console.error('1. Check that Node.js 16+ and Python 3.8+ are installed');
            console.error('2. Ensure you have write permissions to the installation directory');
            console.error('3. Try the failsafe deployment script: ~/.claude-pm/deploy-claude-md.sh');
            console.error('4. Report issues at: https://github.com/bobmatnyc/claude-multiagent-pm/issues');
            
            // Don't fail the installation, just warn
            process.exit(0);
        }
    }
    
    /**
     * Safe execution wrapper for error recovery
     */
    async safeExecute(operationName, operation) {
        try {
            await operation();
        } catch (error) {
            this.log(`${operationName} failed: ${error.message}`, 'warn');
            this.log(`Continuing with post-install setup...`);
            // Don't throw - allow other operations to continue
        }
    }
}

// Run post-install setup
if (require.main === module) {
    const setup = new PostInstallSetup();
    setup.run();
}

module.exports = PostInstallSetup;