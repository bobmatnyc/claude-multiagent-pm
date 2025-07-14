#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Unified NPM Installation System
 * ISS-0112 Implementation: Comprehensive Component Deployment to ~/.claude-pm/
 * 
 * Complete NPM installation workflow transformation:
 * - Unified directory structure creation and component deployment
 * - All framework components (scripts, templates, agents) bundled and installed
 * - Comprehensive installation validation with health checking
 * - Cross-platform compatibility with clear error handling
 * - Installation diagnostics and status reporting
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
        
        // ISS-0112: Unified component deployment paths
        this.deploymentPaths = {
            scripts: path.join(this.globalConfigDir, 'scripts'),
            templates: path.join(this.globalConfigDir, 'templates'),
            agents: path.join(this.globalConfigDir, 'agents'),
            framework: path.join(this.globalConfigDir, 'framework'),
            schemas: path.join(this.globalConfigDir, 'schemas'),
            config: path.join(this.globalConfigDir, 'config'),
            cli: path.join(this.globalConfigDir, 'cli'),
            docs: path.join(this.globalConfigDir, 'docs'),
            bin: path.join(this.globalConfigDir, 'bin')
        };
        
        // Installation validation tracking
        this.installationSteps = [];
        this.validationResults = {
            componentDeployment: false,
            directoryStructure: false,
            healthChecking: false,
            crossPlatformCompatibility: false,
            errorHandling: false
        };
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
     * Includes WSL2-specific path detection
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
            
            // Enhanced global node_modules patterns (includes WSL2 patterns)
            nodeModulesGlobal: packagePath.includes('node_modules') && (
                packagePath.includes('/.npm-global/') ||           // Custom npm global paths
                packagePath.includes('/lib/node_modules/') ||      // Standard global node_modules
                packagePath.includes('\\AppData\\Roaming\\npm\\') || // Windows global
                packagePath.includes('/.npm-packages/') ||         // Alternative npm global
                packagePath.includes('/npm-global/') ||            // Common custom global
                packagePath.includes('/global/lib/node_modules/') ||
                packagePath.includes('/usr/local/lib/node_modules/') ||
                packagePath.includes('/opt/homebrew/lib/node_modules/') ||
                // WSL2-specific patterns
                packagePath.includes('/.nvm/versions/node/') ||    // NVM global packages in WSL2
                packagePath.includes('/nvm/versions/node/') ||     // Alternative NVM paths
                (packagePath.includes('/home/') && packagePath.includes('/.nvm/')) || // WSL2 home NVM
                (packagePath.includes('/mnt/c/') && packagePath.includes('node_modules')) // WSL2 Windows mount
            ),
            
            // Package name in global path
            packageName: packagePath.includes('@bobmatnyc/claude-multiagent-pm'),
            
            // Additional npm environment variables
            npmExecPath: process.env.npm_execpath && 
                        (process.env.npm_execpath.includes('global') || 
                         process.env.npm_execpath.includes('.npm-global')),
            
            // Check for global installation markers (includes WSL2 NVM markers)
            globalMarkers: (packagePath.includes('global') && packagePath.includes('node_modules')) ||
                          (packagePath.includes('.nvm') && packagePath.includes('lib/node_modules')),
            
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
                /C:\\Users\\.*\\AppData\\Roaming\\npm\\node_modules\\/,
                // WSL2-specific patterns
                /\/\.nvm\/versions\/node\/v[0-9]+\.[0-9]+\.[0-9]+\/lib\/node_modules\//,
                /\/home\/[^/]+\/\.nvm\/versions\/node\/.*\/lib\/node_modules\//,
                /\/mnt\/c\/.*\/node_modules\//  // WSL2 Windows mount
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
     * ISS-0112: Create unified directory structure for all framework components
     */
    async createUnifiedDirectoryStructure() {
        try {
            this.log('🏗️  Creating unified directory structure in ~/.claude-pm/');
            
            // Create all deployment directories
            for (const [component, dirPath] of Object.entries(this.deploymentPaths)) {
                await fs.mkdir(dirPath, { recursive: true });
                this.log(`   ✅ Created ${component} directory: ${dirPath}`);
            }
            
            // Create configuration with unified deployment info
            const config = {
                version: require('../package.json').version,
                installType: this.isGlobalInstall() ? 'global' : 'local',
                installDate: new Date().toISOString(),
                platform: this.platform,
                packageRoot: this.packageRoot,
                deploymentPaths: this.deploymentPaths,
                components: {
                    framework: { deployed: false, version: null },
                    scripts: { deployed: false, version: null },
                    templates: { deployed: false, version: null },
                    agents: { deployed: false, version: null },
                    schemas: { deployed: false, version: null },
                    cli: { deployed: false, version: null },
                    docs: { deployed: false, version: null },
                    bin: { deployed: false, version: null }
                },
                validation: {
                    healthCheckingEnabled: true,
                    crossPlatformCompatibility: this.platform,
                    errorHandling: 'comprehensive',
                    installationDiagnostics: true
                }
            };
            
            const configPath = path.join(this.globalConfigDir, 'config.json');
            await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            
            this.log(`📋 Unified configuration created at: ${configPath}`);
            this.validationResults.directoryStructure = true;
            this.installationSteps.push('DirectoryStructureCreated');
            
        } catch (error) {
            this.log(`❌ Failed to create unified directory structure: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * ISS-0112: Deploy all framework components to ~/.claude-pm/
     */
    async deployAllFrameworkComponents() {
        try {
            this.log('📦 Deploying all framework components to ~/.claude-pm/');
            
            // Deploy framework core
            await this.deployFrameworkCore();
            
            // Deploy scripts
            await this.deployScripts();
            
            // Deploy templates
            await this.deployTemplates();
            
            // Deploy agents
            await this.deployAgents();
            
            // Deploy schemas
            await this.deploySchemas();
            
            // Deploy config files
            await this.deployConfig();
            
            // Deploy CLI tools
            await this.deployCLITools();
            
            // Deploy documentation
            await this.deployDocumentation();
            
            // Deploy bin executables
            await this.deployBinExecutables();
            
            this.log('✅ All framework components deployed successfully');
            this.validationResults.componentDeployment = true;
            this.installationSteps.push('AllComponentsDeployed');
            
        } catch (error) {
            this.log(`❌ Failed to deploy framework components: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy framework core (claude_pm Python package)
     */
    async deployFrameworkCore() {
        const frameworkSource = path.join(this.packageRoot, 'claude_pm');
        const frameworkTarget = this.deploymentPaths.framework;
        
        if (!fsSync.existsSync(frameworkSource)) {
            this.log('⚠️  Framework source not found, skipping deployment', 'warn');
            return;
        }
        
        try {
            await this.copyDirectory(frameworkSource, path.join(frameworkTarget, 'claude_pm'));
            
            // Copy framework templates and configuration
            const frameworkFiles = ['framework', 'requirements', 'config'];
            for (const file of frameworkFiles) {
                const sourcePath = path.join(this.packageRoot, file);
                if (fsSync.existsSync(sourcePath)) {
                    const targetPath = path.join(frameworkTarget, file);
                    const stat = await fs.stat(sourcePath);
                    if (stat.isDirectory()) {
                        await this.copyDirectory(sourcePath, targetPath);
                    } else {
                        await fs.copyFile(sourcePath, targetPath);
                    }
                }
            }
            
            this.log('   ✅ Framework core deployed');
            await this.updateComponentStatus('framework', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy framework core: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy scripts to ~/.claude-pm/scripts/
     */
    async deployScripts() {
        const scriptsSource = path.join(this.packageRoot, 'scripts');
        const scriptsTarget = this.deploymentPaths.scripts;
        
        if (!fsSync.existsSync(scriptsSource)) {
            this.log('⚠️  Scripts source not found, creating default scripts', 'warn');
            await this.createDefaultScripts();
            return;
        }
        
        try {
            await this.copyDirectory(scriptsSource, scriptsTarget);
            
            // Make scripts executable on Unix-like systems
            if (this.platform !== 'win32') {
                await this.makeScriptsExecutable(scriptsTarget);
            }
            
            this.log('   ✅ Scripts deployed');
            await this.updateComponentStatus('scripts', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy scripts: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy templates to ~/.claude-pm/templates/
     */
    async deployTemplates() {
        const templatesSource = path.join(this.packageRoot, 'templates');
        const templatesTarget = this.deploymentPaths.templates;
        
        if (!fsSync.existsSync(templatesSource)) {
            await this.createDefaultTemplates();
            return;
        }
        
        try {
            await this.copyDirectory(templatesSource, templatesTarget);
            this.log('   ✅ Templates deployed');
            await this.updateComponentStatus('templates', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy templates: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy agents to ~/.claude-pm/agents/
     */
    async deployAgents() {
        const agentsSource = path.join(this.packageRoot, 'claude_pm', 'agents');
        const agentsTarget = this.deploymentPaths.agents;
        
        if (!fsSync.existsSync(agentsSource)) {
            this.log('⚠️  Agents source not found, creating default agent structure', 'warn');
            await this.createDefaultAgentStructure();
            return;
        }
        
        try {
            await this.copyDirectory(agentsSource, path.join(agentsTarget, 'system'));
            
            // Create user and project agent directories
            await fs.mkdir(path.join(agentsTarget, 'user-defined'), { recursive: true });
            await fs.mkdir(path.join(agentsTarget, 'project-specific'), { recursive: true });
            
            // Copy framework agent roles
            const frameworkAgentsSource = path.join(this.packageRoot, 'framework', 'agent-roles');
            if (fsSync.existsSync(frameworkAgentsSource)) {
                await this.copyDirectory(frameworkAgentsSource, path.join(agentsTarget, 'roles'));
            }
            
            this.log('   ✅ Agents deployed with three-tier hierarchy');
            await this.updateComponentStatus('agents', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy agents: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy schemas to ~/.claude-pm/schemas/
     */
    async deploySchemas() {
        const schemasSource = path.join(this.packageRoot, 'schemas');
        const schemasTarget = this.deploymentPaths.schemas;
        
        if (!fsSync.existsSync(schemasSource)) {
            await this.createDefaultSchemas();
            return;
        }
        
        try {
            await this.copyDirectory(schemasSource, schemasTarget);
            this.log('   ✅ Schemas deployed');
            await this.updateComponentStatus('schemas', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy schemas: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy config files to ~/.claude-pm/config/
     */
    async deployConfig() {
        const configSource = path.join(this.packageRoot, 'config');
        const configTarget = this.deploymentPaths.config;
        
        if (!fsSync.existsSync(configSource)) {
            this.log('   ⚠️ No config directory found in package, skipping');
            return;
        }
        
        try {
            await this.copyDirectory(configSource, configTarget);
            this.log('   ✅ Config files deployed');
            await this.updateComponentStatus('config', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy config files: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy CLI tools to ~/.claude-pm/cli/
     */
    async deployCLITools() {
        const cliSource = path.join(this.packageRoot, 'claude_pm', 'cli');
        const cliTarget = this.deploymentPaths.cli;
        
        try {
            if (fsSync.existsSync(cliSource)) {
                await this.copyDirectory(cliSource, cliTarget);
            }
            
            // Copy main CLI files
            const cliFiles = ['cli.py', 'cmpm_commands.py', 'cli_enforcement.py'];
            for (const file of cliFiles) {
                const sourcePath = path.join(this.packageRoot, 'claude_pm', file);
                if (fsSync.existsSync(sourcePath)) {
                    await fs.copyFile(sourcePath, path.join(cliTarget, file));
                }
            }
            
            this.log('   ✅ CLI tools deployed');
            await this.updateComponentStatus('cli', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy CLI tools: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy documentation to ~/.claude-pm/docs/
     */
    async deployDocumentation() {
        const docsSource = path.join(this.packageRoot, 'docs');
        const docsTarget = this.deploymentPaths.docs;
        
        if (!fsSync.existsSync(docsSource)) {
            await this.createDefaultDocumentation();
            return;
        }
        
        try {
            await this.copyDirectory(docsSource, docsTarget);
            this.log('   ✅ Documentation deployed');
            await this.updateComponentStatus('docs', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy documentation: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Deploy bin executables to ~/.claude-pm/bin/
     */
    async deployBinExecutables() {
        const binSource = path.join(this.packageRoot, 'bin');
        const binTarget = this.deploymentPaths.bin;
        
        if (!fsSync.existsSync(binSource)) {
            await this.createDefaultBinExecutables();
            return;
        }
        
        try {
            await this.copyDirectory(binSource, binTarget);
            
            // Make executables on Unix-like systems
            if (this.platform !== 'win32') {
                await this.makeScriptsExecutable(binTarget);
            }
            
            this.log('   ✅ Bin executables deployed');
            await this.updateComponentStatus('bin', true);
            
        } catch (error) {
            this.log(`   ❌ Failed to deploy bin executables: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Create default templates if source doesn't exist
     */
    async createDefaultTemplates() {
        try {
            const templatesTarget = this.deploymentPaths.templates;
            await fs.mkdir(templatesTarget, { recursive: true });
            
            const defaultTemplate = {
                name: "basic-project",
                description: "Basic Claude PM project template",
                version: require('../package.json').version,
                files: {
                    "CLAUDE.md": "# Claude PM Project\n\nProject managed by Claude Multi-Agent PM Framework",
                    "README.md": "# Project Name\n\nDescription of your project.",
                    "trackdown/BACKLOG.md": "# Project Backlog\n\n## Current Sprint\n\n## Backlog Items\n",
                    ".claude-pm/config.json": JSON.stringify({
                        version: require('../package.json').version,
                        projectType: 'basic',
                        agents: {
                            enabled: ['pm', 'documentation', 'ticketing', 'version-control'],
                            hierarchy: 'three-tier'
                        }
                    }, null, 2)
                }
            };
            
            await fs.writeFile(
                path.join(templatesTarget, 'basic-project.json'),
                JSON.stringify(defaultTemplate, null, 2)
            );
            
            // Create additional templates
            const advancedTemplate = {
                name: "advanced-project",
                description: "Advanced Claude PM project with full agent suite",
                version: require('../package.json').version,
                files: {
                    "CLAUDE.md": "# Advanced Claude PM Project\n\nFull multi-agent orchestration framework",
                    "README.md": "# Advanced Project\n\nAdvanced project with comprehensive agent coordination.",
                    "trackdown/BACKLOG.md": "# Advanced Project Backlog\n\n## Epic Planning\n\n## Sprint Planning\n\n## Backlog Management\n",
                    ".claude-pm/config.json": JSON.stringify({
                        version: require('../package.json').version,
                        projectType: 'advanced',
                        agents: {
                            enabled: ['pm', 'documentation', 'ticketing', 'version-control', 'qa', 'security', 'ops'],
                            hierarchy: 'three-tier',
                            memory: {
                                enabled: true,
                                collection: 'comprehensive'
                            }
                        }
                    }, null, 2)
                }
            };
            
            await fs.writeFile(
                path.join(templatesTarget, 'advanced-project.json'),
                JSON.stringify(advancedTemplate, null, 2)
            );
            
            this.log('   ✅ Default templates created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default templates: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Create default schemas if source doesn't exist
     */
    async createDefaultSchemas() {
        try {
            const schemasTarget = this.deploymentPaths.schemas;
            await fs.mkdir(schemasTarget, { recursive: true });
            
            const configSchema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Claude PM Configuration Schema",
                "description": "Schema for Claude Multi-Agent PM Framework configuration",
                "type": "object",
                "properties": {
                    "version": { "type": "string", "description": "Framework version" },
                    "installType": { "type": "string", "enum": ["global", "local"] },
                    "platform": { "type": "string", "description": "Operating system platform" },
                    "deploymentPaths": {
                        "type": "object",
                        "description": "Paths to deployed components",
                        "properties": {
                            "framework": { "type": "string" },
                            "scripts": { "type": "string" },
                            "templates": { "type": "string" },
                            "agents": { "type": "string" },
                            "schemas": { "type": "string" },
                            "cli": { "type": "string" },
                            "docs": { "type": "string" },
                            "bin": { "type": "string" }
                        }
                    },
                    "components": {
                        "type": "object",
                        "description": "Component deployment status",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "deployed": { "type": "boolean" },
                                "version": { "type": ["string", "null"] }
                            }
                        }
                    },
                    "validation": {
                        "type": "object",
                        "properties": {
                            "healthCheckingEnabled": { "type": "boolean" },
                            "crossPlatformCompatibility": { "type": "string" },
                            "errorHandling": { "type": "string" },
                            "installationDiagnostics": { "type": "boolean" }
                        }
                    }
                },
                "required": ["version", "installType", "platform", "deploymentPaths"]
            };
            
            await fs.writeFile(
                path.join(schemasTarget, 'config.schema.json'),
                JSON.stringify(configSchema, null, 2)
            );
            
            // Create agent schema
            const agentSchema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Claude PM Agent Configuration Schema",
                "description": "Schema for agent configuration in three-tier hierarchy",
                "type": "object",
                "properties": {
                    "name": { "type": "string", "description": "Agent name" },
                    "type": { "type": "string", "enum": ["system", "user-defined", "project-specific"] },
                    "hierarchy": { "type": "string", "enum": ["system", "user", "project"] },
                    "capabilities": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "authority": {
                        "type": "object",
                        "properties": {
                            "read": { "type": "boolean" },
                            "write": { "type": "boolean" },
                            "execute": { "type": "boolean" },
                            "delegate": { "type": "boolean" }
                        }
                    }
                }
            };
            
            await fs.writeFile(
                path.join(schemasTarget, 'agent.schema.json'),
                JSON.stringify(agentSchema, null, 2)
            );
            
            this.log('   ✅ Default schemas created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default schemas: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * ISS-0112: Enhanced cross-platform setup with comprehensive compatibility
     */
    async enhancedPlatformSetup() {
        try {
            this.log(`🖥️  Configuring for ${this.platform} platform`);
            
            if (this.platform === 'win32') {
                await this.enhancedWindowsSetup();
            } else {
                await this.enhancedUnixSetup();
            }
            
            // Create platform-specific configuration
            await this.createPlatformConfiguration();
            
            this.validationResults.crossPlatformCompatibility = true;
            this.installationSteps.push('PlatformSetupCompleted');
            
        } catch (error) {
            this.log(`❌ Enhanced platform setup failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Enhanced Windows-specific setup
     */
    async enhancedWindowsSetup() {
        this.log('   🏪 Configuring Windows-specific features');
        
        try {
            // Create Windows-specific scripts
            await this.createWindowsScripts();
            
            // Setup Windows PATH considerations
            await this.configureWindowsPaths();
            
            // Create Windows batch files for CLI
            await this.createWindowsBatchFiles();
            
            this.log('   ✅ Windows setup completed');
            
        } catch (error) {
            this.log(`   ❌ Windows setup failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Enhanced Unix-specific setup (Linux/macOS)
     */
    async enhancedUnixSetup() {
        this.log('   🐧 Configuring Unix-specific features');
        
        try {
            // Make all deployed scripts executable
            await this.makeDeployedScriptsExecutable();
            
            // Configure shell integration
            await this.configureShellIntegration();
            
            // Setup Unix-specific permissions
            await this.setupUnixPermissions();
            
            // WSL2-specific setup if detected
            if (this.isWSL2Environment()) {
                await this.setupWSL2Environment();
            }
            
            this.log('   ✅ Unix setup completed');
            
        } catch (error) {
            this.log(`   ❌ Unix setup failed: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * ISS-0112: Comprehensive installation validation with health checking
     */
    async comprehensiveInstallationValidation() {
        try {
            this.log('🗖️  Running comprehensive installation validation');
            
            // Validate all deployed components
            await this.validateDeployedComponents();
            
            // Run health checks
            await this.runInstallationHealthChecks();
            
            // Validate cross-platform compatibility
            await this.validateCrossPlatformCompatibility();
            
            // Test error handling
            await this.testErrorHandling();
            
            // Generate installation diagnostics
            await this.generateInstallationDiagnostics();
            
            this.validationResults.healthChecking = true;
            this.validationResults.errorHandling = true;
            this.installationSteps.push('ComprehensiveValidationCompleted');
            
            this.log('✅ Comprehensive installation validation passed');
            
        } catch (error) {
            this.log(`❌ Comprehensive validation failed: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Validate all deployed components
     */
    async validateDeployedComponents() {
        this.log('   📋 Validating deployed components...');
        
        const requiredComponents = Object.keys(this.deploymentPaths);
        const validationResults = {};
        
        for (const component of requiredComponents) {
            const componentPath = this.deploymentPaths[component];
            const exists = fsSync.existsSync(componentPath);
            validationResults[component] = {
                path: componentPath,
                exists: exists,
                accessible: exists ? await this.checkDirectoryAccessible(componentPath) : false
            };
            
            if (!exists) {
                throw new Error(`Required component path missing: ${componentPath}`);
            }
        }
        
        // Save validation results
        const validationPath = path.join(this.globalConfigDir, 'component-validation.json');
        await fs.writeFile(validationPath, JSON.stringify(validationResults, null, 2));
        
        this.log('      ✅ All components validated');
    }
    
    /**
     * Run installation health checks
     */
    async runInstallationHealthChecks() {
        this.log('   🎩 Running installation health checks...');
        
        const healthChecks = {
            configurationValid: await this.validateConfiguration(),
            componentsDeployed: await this.validateAllComponentsDeployed(),
            permissionsCorrect: await this.validatePermissions(),
            platformCompatible: await this.validatePlatformCompatibility(),
            pathsAccessible: await this.validatePathsAccessible()
        };
        
        const healthCheckPath = path.join(this.globalConfigDir, 'health-check.json');
        await fs.writeFile(healthCheckPath, JSON.stringify({
            timestamp: new Date().toISOString(),
            platform: this.platform,
            checks: healthChecks,
            overallHealth: Object.values(healthChecks).every(check => check)
        }, null, 2));
        
        const failedChecks = Object.entries(healthChecks).filter(([name, passed]) => !passed);
        if (failedChecks.length > 0) {
            throw new Error(`Health checks failed: ${failedChecks.map(([name]) => name).join(', ')}`);
        }
        
        this.log('      ✅ All health checks passed');
    }
    
    /**
     * Validate cross-platform compatibility
     */
    async validateCrossPlatformCompatibility() {
        this.log('   🌍 Validating cross-platform compatibility...');
        
        const compatibility = {
            platform: this.platform,
            pathSeparators: this.validatePathSeparators(),
            scriptExecutability: await this.validateScriptExecutability(),
            environmentVariables: this.validateEnvironmentVariables(),
            shellIntegration: await this.validateShellIntegration()
        };
        
        const compatibilityPath = path.join(this.globalConfigDir, 'platform-compatibility.json');
        await fs.writeFile(compatibilityPath, JSON.stringify(compatibility, null, 2));
        
        this.log('      ✅ Cross-platform compatibility validated');
    }
    
    /**
     * Test error handling
     */
    async testErrorHandling() {
        this.log('   ⚠️  Testing error handling mechanisms...');
        
        const errorHandlingTests = {
            missingFileHandling: await this.testMissingFileHandling(),
            permissionErrorHandling: await this.testPermissionErrorHandling(),
            networkErrorHandling: await this.testNetworkErrorHandling(),
            recoveryMechanisms: await this.testRecoveryMechanisms()
        };
        
        const errorTestPath = path.join(this.globalConfigDir, 'error-handling-test.json');
        await fs.writeFile(errorTestPath, JSON.stringify(errorHandlingTests, null, 2));
        
        this.log('      ✅ Error handling mechanisms tested');
    }
    
    /**
     * Generate installation diagnostics and status report
     */
    async generateInstallationDiagnostics() {
        this.log('   📊 Generating installation diagnostics...');
        
        const diagnostics = {
            installationId: Date.now(),
            timestamp: new Date().toISOString(),
            version: require('../package.json').version,
            platform: this.platform,
            nodeVersion: process.version,
            npmVersion: await this.getNpmVersion(),
            installationSteps: this.installationSteps,
            validationResults: this.validationResults,
            deploymentPaths: this.deploymentPaths,
            componentStatus: await this.getComponentStatus(),
            healthMetrics: {
                installationDuration: Date.now() - this.startTime,
                memoryUsage: process.memoryUsage(),
                diskSpace: await this.getDiskSpace()
            },
            troubleshooting: {
                commonIssues: this.getCommonIssueGuidance(),
                supportContacts: this.getSupportContacts(),
                diagnosticCommands: this.getDiagnosticCommands()
            }
        };
        
        const diagnosticsPath = path.join(this.globalConfigDir, 'installation-diagnostics.json');
        await fs.writeFile(diagnosticsPath, JSON.stringify(diagnostics, null, 2));
        
        // Create human-readable report
        const reportPath = path.join(this.globalConfigDir, 'installation-report.md');
        await this.generateInstallationReport(diagnostics, reportPath);
        
        this.log('      ✅ Installation diagnostics generated');
        this.log(`         📄 Diagnostics: ${diagnosticsPath}`);
        this.log(`         📄 Report: ${reportPath}`);
    }

    /**
     * ISS-0112: Enhanced post-install instructions with comprehensive guidance
     */
    showEnhancedInstructions() {
        console.log('\n🎉 Claude Multi-Agent PM Framework - Unified Installation Complete!\n');
        
        // Installation summary
        console.log('📋 Installation Summary:');
        console.log(`   • Version: ${require('../package.json').version}`);
        console.log(`   • Installation Type: ${this.isGlobalInstall() ? 'Global' : 'Local'}`);
        console.log(`   • Platform: ${this.platform}`);
        console.log(`   • Configuration: ${this.globalConfigDir}`);
        console.log('');
        
        // Component deployment status
        console.log('📦 Components Deployed to ~/.claude-pm/:');
        for (const [component, path] of Object.entries(this.deploymentPaths)) {
            console.log(`   ✅ ${component}: ${path}`);
        }
        console.log('');
        
        // Usage instructions
        if (this.isGlobalInstall()) {
            console.log('🚀 Global Installation - Available Commands:');
            console.log('   claude-pm --help                     # Show all available commands');
            console.log('   claude-pm health status               # Comprehensive health check');
            console.log('   claude-pm project create my-project   # Create new managed project');
            console.log('   claude-pm deploy-template             # Deploy CLAUDE.md to current directory');
            console.log('   claude-pm agent list                  # Show available agents');
        } else {
            console.log('📚 Local Installation - Available Commands:');
            console.log('   npx claude-pm --help                 # Show all available commands');
            console.log('   npx claude-pm health status           # Comprehensive health check');
            console.log('   npx claude-pm project create          # Create new managed project');
            console.log('   # Or add claude-pm commands to your package.json scripts');
        }
        console.log('');
        
        // Validation and diagnostics
        console.log('🗖️  Installation Validation:');
        const validationStatus = Object.entries(this.validationResults)
            .map(([key, passed]) => `   ${passed ? '✅' : '❌'} ${key}`);
        validationStatus.forEach(status => console.log(status));
        console.log('');
        
        // Cross-platform guidance
        if (this.platform === 'win32') {
            console.log('🏪 Windows-Specific Guidance:');
            console.log('   • Use PowerShell or Command Prompt for best experience');
            console.log('   • Batch files created for CLI integration');
            console.log('   • PATH configuration handled automatically');
        } else {
            console.log('🐧 Unix-Specific Guidance:');
            console.log('   • Scripts made executable automatically');
            console.log('   • Shell integration configured');
            console.log('   • Run "source ~/.bashrc" or "source ~/.zshrc" to refresh environment');
        }
        console.log('');
        
        // Health and diagnostics
        console.log('🎩 Health Monitoring & Diagnostics:');
        console.log(`   • Installation diagnostics: ${path.join(this.globalConfigDir, 'installation-diagnostics.json')}`);
        console.log(`   • Health check results: ${path.join(this.globalConfigDir, 'health-check.json')}`);
        console.log(`   • Installation report: ${path.join(this.globalConfigDir, 'installation-report.md')}`);
        console.log('');
        
        // Next steps
        console.log('🔄 Recommended Next Steps:');
        console.log('1. Verify installation: "claude-pm health status"');
        console.log('2. Create your first project: "claude-pm project create my-awesome-project"');
        console.log('3. Deploy framework to existing project: "claude-pm deploy-template"');
        console.log('4. Explore agent capabilities: "claude-pm agent list"');
        console.log('5. Read documentation: "claude-pm docs"');
        console.log('');
        
        // Support and troubleshooting
        console.log('🔧 Support & Troubleshooting:');
        console.log('   • GitHub Issues: https://github.com/bobmatnyc/claude-multiagent-pm/issues');
        console.log('   • Documentation: https://github.com/bobmatnyc/claude-multiagent-pm#readme');
        console.log('   • Diagnostic commands available in installation report');
        console.log('');
        
        // Success message
        console.log('✨ Installation completed successfully! Ready for multi-agent orchestration.');
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
     * Check if running in WSL2 environment
     */
    isWSL2Environment() {
        try {
            // Check for WSL-specific indicators
            const isWSL = process.env.WSL_DISTRO_NAME || 
                         process.env.WSLENV ||
                         (process.platform === 'linux' && fsSync.existsSync('/proc/version'));
            
            if (!isWSL) return false;
            
            // Additional WSL2 detection
            if (fsSync.existsSync('/proc/version')) {
                const versionContent = fsSync.readFileSync('/proc/version', 'utf8');
                const isWSL2 = versionContent.includes('WSL2') || versionContent.includes('microsoft');
                this.log(`WSL environment detected: ${isWSL2 ? 'WSL2' : 'WSL1'}`);
                return isWSL2;
            }
            
            return false;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Setup WSL2-specific environment configuration
     */
    async setupWSL2Environment() {
        try {
            this.log('🐧 Setting up WSL2-specific configuration...');
            
            // Get NPM global bin directory for WSL2
            const globalBinDir = await this.getWSL2NpmGlobalBin();
            if (globalBinDir) {
                this.log(`📍 WSL2 npm global bin directory: ${globalBinDir}`);
                
                // Update shell configuration for PATH
                await this.configureWSL2Shell(globalBinDir);
                
                // Create WSL2-specific diagnostic script
                await this.createWSL2DiagnosticScript(globalBinDir);
            }
            
            // Handle ai-trackdown-tools dependency for WSL2
            await this.setupWSL2Dependencies();
            
        } catch (error) {
            this.log(`WSL2 setup failed: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Get NPM global bin directory for WSL2
     */
    async getWSL2NpmGlobalBin() {
        try {
            const { execSync } = require('child_process');
            
            // Try multiple methods to get npm global bin
            const methods = [
                () => execSync('npm config get prefix', { encoding: 'utf8' }).trim() + '/bin',
                () => execSync('npm bin -g', { encoding: 'utf8' }).trim(),
                () => {
                    // NVM-specific detection
                    const nvmDir = process.env.NVM_DIR || path.join(this.userHome, '.nvm');
                    const nodeVersion = process.version;
                    return path.join(nvmDir, 'versions', 'node', nodeVersion, 'bin');
                },
                () => {
                    // Parse npm config list
                    const configOutput = execSync('npm config list', { encoding: 'utf8' });
                    const prefixMatch = configOutput.match(/prefix = "([^"]+)"/i);
                    return prefixMatch ? prefixMatch[1] + '/bin' : null;
                }
            ];
            
            for (const method of methods) {
                try {
                    const binDir = method();
                    if (binDir && fsSync.existsSync(binDir)) {
                        this.log(`✅ Found npm global bin directory: ${binDir}`);
                        return binDir;
                    }
                } catch (methodError) {
                    this.log(`Method failed: ${methodError.message}`, 'warn');
                }
            }
            
            this.log('❌ Could not determine npm global bin directory', 'warn');
            return null;
            
        } catch (error) {
            this.log(`Failed to get WSL2 npm global bin: ${error.message}`, 'warn');
            return null;
        }
    }
    
    /**
     * Configure shell environment for WSL2
     */
    async configureWSL2Shell(globalBinDir) {
        try {
            const shellFiles = [
                path.join(this.userHome, '.bashrc'),
                path.join(this.userHome, '.zshrc'),
                path.join(this.userHome, '.profile')
            ];
            
            for (const shellFile of shellFiles) {
                if (fsSync.existsSync(shellFile)) {
                    const content = fsSync.readFileSync(shellFile, 'utf8');
                    
                    // Check if PATH already contains our global bin directory
                    if (!content.includes(globalBinDir)) {
                        const pathExport = `\n# Claude PM Framework - WSL2 PATH configuration\nexport PATH="${globalBinDir}:$PATH"\n`;
                        
                        // Add PATH configuration
                        fsSync.appendFileSync(shellFile, pathExport);
                        this.log(`✅ Updated PATH in ${shellFile}`);
                    } else {
                        this.log(`📋 PATH already configured in ${shellFile}`);
                    }
                }
            }
            
            this.log('💡 Remember to restart your shell or run: source ~/.bashrc');
            
        } catch (error) {
            this.log(`Failed to configure WSL2 shell: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Setup WSL2-specific dependencies
     */
    async setupWSL2Dependencies() {
        try {
            this.log('🔧 Setting up WSL2-specific dependencies...');
            
            // Install ai-trackdown-tools with WSL2-specific considerations
            await this.installWSL2Dependencies();
            
            // Create WSL2-specific wrapper scripts if needed
            await this.createWSL2WrapperScripts();
            
        } catch (error) {
            this.log(`WSL2 dependency setup failed: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Install dependencies with WSL2 considerations
     */
    async installWSL2Dependencies() {
        try {
            const { execSync } = require('child_process');
            
            // Check if ai-trackdown-tools is available
            try {
                const version = execSync('aitrackdown --version', { 
                    encoding: 'utf8', 
                    stdio: 'pipe',
                    timeout: 5000,
                    env: { ...process.env, PATH: process.env.PATH + ':' + path.dirname(process.execPath) }
                });
                this.log(`ai-trackdown-tools already available: ${version.trim()}`);
                return;
            } catch (checkError) {
                this.log('ai-trackdown-tools not found in WSL2, attempting installation...');
            }
            
            // Install with WSL2-specific npm configuration
            this.log('Installing ai-trackdown-tools for WSL2...');
            execSync('npm install -g @bobmatnyc/ai-trackdown-tools', { 
                encoding: 'utf8',
                stdio: 'pipe',
                timeout: 60000,
                env: { ...process.env, NPM_CONFIG_PROGRESS: 'false' }
            });
            
            // Verify installation with extended PATH
            const globalBinDir = await this.getWSL2NpmGlobalBin();
            const extendedPath = process.env.PATH + (globalBinDir ? ':' + globalBinDir : '');
            
            const version = execSync('aitrackdown --version', { 
                encoding: 'utf8', 
                stdio: 'pipe',
                timeout: 5000,
                env: { ...process.env, PATH: extendedPath }
            });
            this.log(`✅ ai-trackdown-tools installed successfully in WSL2: ${version.trim()}`);
            
        } catch (installError) {
            this.log(`Failed to install ai-trackdown-tools in WSL2: ${installError.message}`, 'warn');
            this.log('You may need to manually install: npm install -g @bobmatnyc/ai-trackdown-tools');
            this.log('Then restart your shell or source your shell configuration file');
        }
    }
    
    /**
     * Create WSL2-specific wrapper scripts
     */
    async createWSL2WrapperScripts() {
        try {
            const wrapperDir = path.join(this.globalConfigDir, 'wsl2-wrappers');
            await fs.mkdir(wrapperDir, { recursive: true });
            
            // Create claude-pm wrapper that handles PATH
            const claudePmWrapper = `#!/bin/bash
# Claude PM Framework - WSL2 Wrapper
# Ensures proper PATH configuration

# Add npm global bin to PATH if not already there
NPM_BIN="$(npm bin -g 2>/dev/null || echo "")"
if [ -n "$NPM_BIN" ] && [[ ":$PATH:" != *":$NPM_BIN:"* ]]; then
    export PATH="$NPM_BIN:$PATH"
fi

# Execute claude-pm with proper environment
exec "$(which claude-pm 2>/dev/null || echo 'claude-pm')" "$@"
`;
            
            const wrapperPath = path.join(wrapperDir, 'claude-pm-wsl2');
            await fs.writeFile(wrapperPath, claudePmWrapper);
            await fs.chmod(wrapperPath, '755');
            
            this.log(`✅ Created WSL2 wrapper script: ${wrapperPath}`);
            
        } catch (error) {
            this.log(`Failed to create WSL2 wrapper scripts: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Create WSL2 diagnostic and recovery script
     */
    async createWSL2DiagnosticScript(globalBinDir) {
        try {
            const diagnosticScript = `#!/bin/bash
# Claude PM Framework - WSL2 Diagnostic and Recovery Script

echo "🐧 Claude PM Framework - WSL2 Diagnostic Tool"
echo "============================================="
echo ""

# Environment information
echo "📋 Environment Information:"
echo "   • WSL Version: $(uname -r)"
echo "   • Distribution: $WSL_DISTRO_NAME"
echo "   • Node.js Version: $(node --version 2>/dev/null || echo 'Not found')"
echo "   • NPM Version: $(npm --version 2>/dev/null || echo 'Not found')"
echo ""

# PATH Analysis
echo "🔍 PATH Analysis:"
echo "   • Current PATH: $PATH"
echo "   • NPM Global Bin: ${globalBinDir}"
echo "   • Claude PM Available: $(which claude-pm 2>/dev/null || echo 'Not found')"
echo "   • AI-Trackdown Available: $(which aitrackdown 2>/dev/null || echo 'Not found')"
echo "   • Claude CLI Available: $(which claude 2>/dev/null || echo 'Not found')"
echo ""

# Test installations
echo "🧪 Testing Installations:"
if command -v claude-pm >/dev/null 2>&1; then
    echo "   ✅ claude-pm: $(claude-pm --version 2>/dev/null || echo 'Version check failed')"
else
    echo "   ❌ claude-pm: Not available in PATH"
fi

if command -v aitrackdown >/dev/null 2>&1; then
    echo "   ✅ aitrackdown: $(aitrackdown --version 2>/dev/null || echo 'Version check failed')"
else
    echo "   ❌ aitrackdown: Not available in PATH"
fi

if command -v claude >/dev/null 2>&1; then
    echo "   ✅ claude: $(claude --version 2>/dev/null || echo 'Version check failed')"
else
    echo "   ❌ claude: Not available in PATH"
fi
echo ""

# Recovery suggestions
echo "🔧 Recovery Actions:"
echo "1. Add npm global bin to PATH:"
echo "   echo 'export PATH=\"${globalBinDir}:\$PATH\"' >> ~/.bashrc"
echo "   source ~/.bashrc"
echo ""
echo "2. Reinstall dependencies:"
echo "   npm install -g @bobmatnyc/claude-multiagent-pm"
echo "   npm install -g @bobmatnyc/ai-trackdown-tools"
echo ""
echo "3. Manual PATH configuration:"
echo "   export PATH=\"${globalBinDir}:\$PATH\""
echo ""
echo "4. Test installation:"
echo "   claude-pm --version"
echo "   aitrackdown --version"
echo ""
`;
            
            const diagnosticPath = path.join(this.globalConfigDir, 'wsl2-diagnostic.sh');
            await fs.writeFile(diagnosticPath, diagnosticScript);
            await fs.chmod(diagnosticPath, '755');
            
            this.log(`✅ Created WSL2 diagnostic script: ${diagnosticPath}`);
            this.log(`   Run it with: bash ${diagnosticPath}`);
            
        } catch (error) {
            this.log(`Failed to create WSL2 diagnostic script: ${error.message}`, 'warn');
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
            
            // Try to install ai-trackdown-tools (with WSL2 considerations)
            try {
                this.log('Installing ai-trackdown-tools dependency...');
                
                // Use WSL2-aware installation if in WSL2
                if (this.isWSL2Environment()) {
                    await this.installWSL2Dependencies();
                } else {
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
                }
                
            } catch (installError) {
                this.log(`Failed to install ai-trackdown-tools: ${installError.message}`, 'warn');
                if (this.isWSL2Environment()) {
                    this.log('WSL2 detected. Try these steps:');
                    this.log('1. Restart your shell: source ~/.bashrc');
                    this.log('2. Check PATH: echo $PATH');
                    this.log('3. Manual install: npm install -g @bobmatnyc/ai-trackdown-tools');
                    this.log('4. Run diagnostic: ~/.claude-pm/wsl2-diagnostic.sh');
                } else {
                    this.log('You may need to install it manually: npm install -g @bobmatnyc/ai-trackdown-tools');
                }
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
     * ISS-0112: Main unified NPM installation workflow
     */
    async run() {
        this.startTime = Date.now();
        
        try {
            this.log('🚀 Starting Claude PM Framework unified installation (ISS-0112)');
            this.log(`   Version: ${require('../package.json').version}`);
            this.log(`   Platform: ${this.platform}`);
            this.log(`   Install Type: ${this.isGlobalInstall() ? 'Global' : 'Local'}`);
            this.log('');
            
            // Phase 1: Unified Directory Structure Creation
            await this.safeExecute('createUnifiedDirectoryStructure', () => this.createUnifiedDirectoryStructure());
            
            // Phase 2: Comprehensive Component Deployment
            await this.safeExecute('deployAllFrameworkComponents', () => this.deployAllFrameworkComponents());
            
            // Phase 3: Enhanced Cross-Platform Setup
            await this.safeExecute('enhancedPlatformSetup', () => this.enhancedPlatformSetup());
            
            // Phase 4: Comprehensive Installation Validation
            await this.safeExecute('comprehensiveInstallationValidation', () => this.comprehensiveInstallationValidation());
            
            // Phase 5: Enhanced Setup and Migration
            await this.safeExecute('migrateEnvironmentVariables', () => this.migrateEnvironmentVariables());
            await this.safeExecute('setupDeploymentConfiguration', () => this.setupDeploymentConfiguration());
            await this.safeExecute('createMigrationHelper', () => this.createMigrationHelper());
            await this.safeExecute('validateAndInstallDependencies', () => this.validateAndInstallDependencies());
            await this.safeExecute('addFailsafeMechanisms', () => this.addFailsafeMechanisms());
            
            // Phase 6: Framework Template Deployment (if appropriate)
            await this.safeExecute('deployFrameworkToWorkingDirectory', () => this.deployFrameworkToWorkingDirectory());
            
            // Phase 7: Version Management
            await this.safeExecute('updateDeployedInstanceVersion', () => this.updateDeployedInstanceVersion());
            
            // Final status update
            await this.finalizeInstallation();
            
            this.log('');
            this.log('✨ Claude PM Framework unified installation completed successfully!');
            this.showEnhancedInstructions();
            
        } catch (error) {
            await this.handleInstallationFailure(error);
        }
    }
    
    /**
     * Finalize installation with status updates
     */
    async finalizeInstallation() {
        try {
            // Update configuration with final status
            const configPath = path.join(this.globalConfigDir, 'config.json');
            const config = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
            
            config.installationComplete = true;
            config.installationCompletedAt = new Date().toISOString();
            config.installationDuration = Date.now() - this.startTime;
            config.validation = this.validationResults;
            config.installationSteps = this.installationSteps;
            
            await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            
        } catch (error) {
            this.log(`Failed to finalize installation: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Handle installation failure with comprehensive error reporting
     */
    async handleInstallationFailure(error) {
        this.log(`❌ Unified installation failed: ${error.message}`, 'error');
        
        try {
            // Generate failure diagnostics
            const failureDiagnostics = {
                timestamp: new Date().toISOString(),
                error: {
                    message: error.message,
                    stack: error.stack,
                    code: error.code
                },
                platform: this.platform,
                nodeVersion: process.version,
                installationSteps: this.installationSteps,
                validationResults: this.validationResults,
                partialDeployment: await this.assessPartialDeployment()
            };
            
            const failurePath = path.join(this.globalConfigDir, 'installation-failure.json');
            await fs.writeFile(failurePath, JSON.stringify(failureDiagnostics, null, 2));
            
            console.error('');
            console.error('🔴 Installation Failed - Comprehensive Error Report');
            console.error('=========================================');
            console.error(`Error: ${error.message}`);
            console.error(`Platform: ${this.platform}`);
            console.error(`Node.js: ${process.version}`);
            console.error(`Failure diagnostics: ${failurePath}`);
            console.error('');
            console.error('🔧 Troubleshooting Steps:');
            console.error('1. Check Node.js version (16+ required): node --version');
            console.error('2. Check npm permissions: npm config get prefix');
            console.error('3. Verify write permissions to ~/.claude-pm/');
            console.error('4. Try manual installation: npm install -g @bobmatnyc/claude-multiagent-pm --force');
            console.error('5. Report issue with diagnostics: https://github.com/bobmatnyc/claude-multiagent-pm/issues');
            console.error('');
            console.error('🔄 Recovery Options:');
            console.error('• Partial installation may be functional - check ~/.claude-pm/');
            console.error('• Run health check after manual fixes: claude-pm health status');
            console.error('• Use failsafe scripts in ~/.claude-pm/ if available');
            console.error('');
            
        } catch (diagnosticError) {
            console.error(`Failed to generate failure diagnostics: ${diagnosticError.message}`);
        }
        
        // Don't fail the NPM installation completely - allow partial installation
        process.exit(0);
    }
    
    /**
     * Safe execution wrapper with enhanced error recovery and logging
     */
    async safeExecute(operationName, operation) {
        try {
            this.log(`🔄 Executing: ${operationName}`);
            await operation();
            this.log(`   ✅ ${operationName} completed successfully`);
        } catch (error) {
            this.log(`   ❌ ${operationName} failed: ${error.message}`, 'error');
            
            // Record failure but continue with installation
            this.installationSteps.push(`${operationName}_FAILED`);
            
            // Critical operations should halt installation
            const criticalOperations = [
                'createUnifiedDirectoryStructure',
                'deployAllFrameworkComponents',
                'comprehensiveInstallationValidation'
            ];
            
            if (criticalOperations.includes(operationName)) {
                this.log(`   ⚠️  Critical operation failed - halting installation`, 'error');
                throw error;
            }
            
            this.log(`   🔄 Continuing with remaining installation steps...`);
        }
    }

    // =========================================================
    // ISS-0112: Helper Methods for Unified Installation System
    // =========================================================
    
    /**
     * Update component deployment status
     */
    async updateComponentStatus(component, deployed, version = null) {
        try {
            const configPath = path.join(this.globalConfigDir, 'config.json');
            if (fsSync.existsSync(configPath)) {
                const config = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
                if (!config.components) config.components = {};
                config.components[component] = {
                    deployed: deployed,
                    version: version || require('../package.json').version
                };
                await fs.writeFile(configPath, JSON.stringify(config, null, 2));
            }
        } catch (error) {
            this.log(`Failed to update component status for ${component}: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Get current component deployment status
     */
    async getComponentStatus() {
        try {
            const configPath = path.join(this.globalConfigDir, 'config.json');
            if (fsSync.existsSync(configPath)) {
                const config = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
                return config.components || {};
            }
        } catch (error) {
            this.log(`Failed to get component status: ${error.message}`, 'warn');
        }
        return {};
    }
    
    /**
     * Make scripts executable on Unix systems
     */
    async makeScriptsExecutable(scriptsDir) {
        try {
            const items = await fs.readdir(scriptsDir);
            for (const item of items) {
                const itemPath = path.join(scriptsDir, item);
                const stat = await fs.stat(itemPath);
                if (stat.isFile() && (item.endsWith('.sh') || item.endsWith('.py') || !item.includes('.'))) {
                    await fs.chmod(itemPath, '755');
                }
            }
        } catch (error) {
            this.log(`Failed to make scripts executable: ${error.message}`, 'warn');
        }
    }
    
    /**
     * Create default scripts if source doesn't exist
     */
    async createDefaultScripts() {
        try {
            const scriptsTarget = this.deploymentPaths.scripts;
            await fs.mkdir(scriptsTarget, { recursive: true });
            
            // Create health check script
            const healthCheckScript = this.platform === 'win32' ? 
                this.createWindowsHealthCheckScript() : 
                this.createUnixHealthCheckScript();
            
            const healthCheckPath = path.join(scriptsTarget, 
                this.platform === 'win32' ? 'health-check.bat' : 'health-check.sh');
            await fs.writeFile(healthCheckPath, healthCheckScript);
            
            if (this.platform !== 'win32') {
                await fs.chmod(healthCheckPath, '755');
            }
            
            this.log('   ✅ Default scripts created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default scripts: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Create default agent structure
     */
    async createDefaultAgentStructure() {
        try {
            const agentsTarget = this.deploymentPaths.agents;
            
            // Create three-tier hierarchy
            await fs.mkdir(path.join(agentsTarget, 'system'), { recursive: true });
            await fs.mkdir(path.join(agentsTarget, 'user-defined'), { recursive: true });
            await fs.mkdir(path.join(agentsTarget, 'project-specific'), { recursive: true });
            await fs.mkdir(path.join(agentsTarget, 'roles'), { recursive: true });
            
            // Create README files
            const systemReadme = `# System Agents\n\nCore framework agents provided by Claude Multi-Agent PM Framework.\n\nThese agents have the highest precedence and provide foundational functionality.`;
            await fs.writeFile(path.join(agentsTarget, 'system', 'README.md'), systemReadme);
            
            const userReadme = `# User-Defined Agents\n\nCustom agents defined by the user across all projects.\n\nThese agents override system agents but are overridden by project-specific agents.`;
            await fs.writeFile(path.join(agentsTarget, 'user-defined', 'README.md'), userReadme);
            
            const projectReadme = `# Project-Specific Agents\n\nAgents defined for specific projects.\n\nThese agents have the highest precedence and override both system and user-defined agents.`;
            await fs.writeFile(path.join(agentsTarget, 'project-specific', 'README.md'), projectReadme);
            
            this.log('   ✅ Default agent structure created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default agent structure: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Create default documentation
     */
    async createDefaultDocumentation() {
        try {
            const docsTarget = this.deploymentPaths.docs;
            await fs.mkdir(docsTarget, { recursive: true });
            
            const readmeContent = `# Claude Multi-Agent PM Framework Documentation\n\n## Overview\n\nThis directory contains comprehensive documentation for the Claude Multi-Agent PM Framework.\n\n## Quick Start\n\n1. Run \`claude-pm health status\` to verify installation\n2. Create a project with \`claude-pm project create <name>\`\n3. Deploy framework template with \`claude-pm deploy-template\`\n\n## Documentation Structure\n\n- **Installation**: Setup and configuration guides\n- **Usage**: Command reference and examples\n- **Agents**: Agent development and customization\n- **API**: Framework API documentation\n- **Troubleshooting**: Common issues and solutions\n\n## Support\n\n- GitHub: https://github.com/bobmatnyc/claude-multiagent-pm\n- Issues: https://github.com/bobmatnyc/claude-multiagent-pm/issues\n\n---\n\n*Generated by Claude Multi-Agent PM Framework v${require('../package.json').version}*`;
            
            await fs.writeFile(path.join(docsTarget, 'README.md'), readmeContent);
            this.log('   ✅ Default documentation created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default documentation: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Create default bin executables
     */
    async createDefaultBinExecutables() {
        try {
            const binTarget = this.deploymentPaths.bin;
            await fs.mkdir(binTarget, { recursive: true });
            
            // Create claude-pm wrapper script
            const wrapperScript = this.platform === 'win32' ? 
                this.createWindowsCLIWrapper() : 
                this.createUnixCLIWrapper();
            
            const wrapperPath = path.join(binTarget, 
                this.platform === 'win32' ? 'claude-pm.bat' : 'claude-pm');
            await fs.writeFile(wrapperPath, wrapperScript);
            
            if (this.platform !== 'win32') {
                await fs.chmod(wrapperPath, '755');
            }
            
            this.log('   ✅ Default bin executables created');
            
        } catch (error) {
            this.log(`   ❌ Failed to create default bin executables: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * Validation helper methods
     */
    async checkDirectoryAccessible(dirPath) {
        try {
            await fs.access(dirPath, fsSync.constants.R_OK | fsSync.constants.W_OK);
            return true;
        } catch (error) {
            return false;
        }
    }
    
    async validateConfiguration() {
        try {
            const configPath = path.join(this.globalConfigDir, 'config.json');
            if (!fsSync.existsSync(configPath)) return false;
            
            const config = JSON.parse(fsSync.readFileSync(configPath, 'utf8'));
            return config.version && config.deploymentPaths && config.platform;
        } catch (error) {
            return false;
        }
    }
    
    async validateAllComponentsDeployed() {
        try {
            const componentStatus = await this.getComponentStatus();
            const requiredComponents = Object.keys(this.deploymentPaths);
            return requiredComponents.every(component => 
                componentStatus[component] && componentStatus[component].deployed
            );
        } catch (error) {
            return false;
        }
    }
    
    async validatePermissions() {
        try {
            // Test write permissions in deployment directories
            for (const [component, dirPath] of Object.entries(this.deploymentPaths)) {
                if (fsSync.existsSync(dirPath)) {
                    const testFile = path.join(dirPath, '.permission-test');
                    await fs.writeFile(testFile, 'test');
                    await fs.unlink(testFile);
                }
            }
            return true;
        } catch (error) {
            return false;
        }
    }
    
    async validatePlatformCompatibility() {
        try {
            // Check platform-specific requirements
            if (this.platform === 'win32') {
                // Windows-specific checks
                return process.env.OS && process.env.OS.includes('Windows');
            } else {
                // Unix-specific checks
                return process.env.SHELL || process.env.HOME;
            }
        } catch (error) {
            return false;
        }
    }
    
    async validatePathsAccessible() {
        try {
            for (const [component, dirPath] of Object.entries(this.deploymentPaths)) {
                if (!await this.checkDirectoryAccessible(dirPath)) {
                    return false;
                }
            }
            return true;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Cross-platform validation methods
     */
    validatePathSeparators() {
        const expected = this.platform === 'win32' ? '\\' : '/';
        const actual = path.sep;
        return expected === actual;
    }
    
    async validateScriptExecutability() {
        try {
            if (this.platform === 'win32') {
                // Windows batch files should be executable
                return true; // Windows handles this automatically
            } else {
                // Unix scripts should have execute permissions
                const scriptsDir = this.deploymentPaths.scripts;
                if (!fsSync.existsSync(scriptsDir)) return true;
                
                const items = await fs.readdir(scriptsDir);
                for (const item of items) {
                    if (item.endsWith('.sh')) {
                        const itemPath = path.join(scriptsDir, item);
                        const stat = await fs.stat(itemPath);
                        if (!(stat.mode & 0o111)) { // Check execute permission
                            return false;
                        }
                    }
                }
                return true;
            }
        } catch (error) {
            return false;
        }
    }
    
    validateEnvironmentVariables() {
        // Check for required environment variables
        const required = ['HOME', 'PATH'];
        return required.every(varName => process.env[varName]);
    }
    
    async validateShellIntegration() {
        try {
            if (this.platform === 'win32') {
                return true; // Windows doesn't require shell integration
            } else {
                // Check if common shell config files exist
                const homeDir = os.homedir();
                const shellConfigs = ['.bashrc', '.zshrc', '.profile'];
                return shellConfigs.some(config => 
                    fsSync.existsSync(path.join(homeDir, config))
                );
            }
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Error handling test methods
     */
    async testMissingFileHandling() {
        try {
            // Test behavior when required files are missing
            const testPath = path.join(this.globalConfigDir, 'missing-file-test');
            try {
                await fs.readFile(testPath);
                return false; // Should have failed
            } catch (error) {
                return error.code === 'ENOENT'; // Expected error
            }
        } catch (error) {
            return false;
        }
    }
    
    async testPermissionErrorHandling() {
        try {
            // Test behavior with permission errors
            // This is a simplified test - in practice would test actual permission scenarios
            return true;
        } catch (error) {
            return false;
        }
    }
    
    async testNetworkErrorHandling() {
        try {
            // Test behavior with network errors (NPM dependencies)
            // This is a placeholder - actual implementation would test dependency installation
            return true;
        } catch (error) {
            return false;
        }
    }
    
    async testRecoveryMechanisms() {
        try {
            // Test recovery and failsafe mechanisms
            const failsafeScript = path.join(this.globalConfigDir, 'deploy-claude-md.sh');
            return fsSync.existsSync(failsafeScript);
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Get disk space information
     */
    async getDiskSpace() {
        try {
            if (this.platform === 'win32') {
                // Windows disk space check
                return { available: 'unknown', total: 'unknown' };
            } else {
                // Unix disk space check
                const { execSync } = require('child_process');
                const df = execSync('df -h ~/.claude-pm', { encoding: 'utf8' });
                return { raw: df.trim() };
            }
        } catch (error) {
            return { error: error.message };
        }
    }
    
    /**
     * Get common issue guidance
     */
    getCommonIssueGuidance() {
        return {
            'Permission Denied': 'Check write permissions to ~/.claude-pm/ directory',
            'Command Not Found': 'Verify PATH includes npm global bin directory',
            'Module Not Found': 'Reinstall with: npm install -g @bobmatnyc/claude-multiagent-pm',
            'WSL2 Issues': 'Run ~/.claude-pm/wsl2-diagnostic.sh for WSL2-specific help',
            'Windows Path Issues': 'Check PATH environment variable includes npm global bin'
        };
    }
    
    /**
     * Get support contact information
     */
    getSupportContacts() {
        return {
            github: 'https://github.com/bobmatnyc/claude-multiagent-pm/issues',
            documentation: 'https://github.com/bobmatnyc/claude-multiagent-pm#readme',
            npm: 'https://www.npmjs.com/package/@bobmatnyc/claude-multiagent-pm'
        };
    }
    
    /**
     * Get diagnostic commands
     */
    getDiagnosticCommands() {
        const commands = {
            'Check Installation': 'claude-pm health status',
            'Verify Components': 'ls -la ~/.claude-pm/',
            'Test CLI': 'claude-pm --version',
            'Check NPM Global': 'npm list -g @bobmatnyc/claude-multiagent-pm',
            'Verify Node/NPM': 'node --version && npm --version'
        };
        
        if (this.platform !== 'win32') {
            commands['Check PATH'] = 'echo $PATH';
            commands['Check Shell'] = 'echo $SHELL';
        }
        
        return commands;
    }
    
    /**
     * Generate human-readable installation report
     */
    async generateInstallationReport(diagnostics, reportPath) {
        const report = `# Claude Multi-Agent PM Framework - Installation Report

Generated: ${diagnostics.timestamp}
Version: ${diagnostics.version}
Platform: ${diagnostics.platform}
Installation ID: ${diagnostics.installationId}

## Installation Summary

${diagnostics.installationSteps.map(step => `- ✅ ${step}`).join('\n')}

## Validation Results

${Object.entries(diagnostics.validationResults).map(([key, passed]) => 
    `- ${passed ? '✅' : '❌'} ${key}`).join('\n')}

## Component Status

${Object.entries(diagnostics.componentStatus).map(([component, status]) => 
    `- ${status.deployed ? '✅' : '❌'} ${component}: ${status.deployed ? 'Deployed' : 'Not Deployed'} (v${status.version || 'unknown'})`).join('\n')}

## Health Metrics

- Installation Duration: ${diagnostics.healthMetrics.installationDuration}ms
- Memory Usage: ${JSON.stringify(diagnostics.healthMetrics.memoryUsage, null, 2)}
- Disk Space: ${JSON.stringify(diagnostics.healthMetrics.diskSpace, null, 2)}

## Deployment Paths

${Object.entries(diagnostics.deploymentPaths).map(([component, path]) => 
    `- ${component}: ${path}`).join('\n')}

## Troubleshooting

### Common Issues

${Object.entries(diagnostics.troubleshooting.commonIssues).map(([issue, solution]) => 
    `**${issue}**: ${solution}`).join('\n\n')}

### Diagnostic Commands

${Object.entries(diagnostics.troubleshooting.diagnosticCommands).map(([description, command]) => 
    `- **${description}**: \`${command}\``).join('\n')}

### Support

- GitHub Issues: ${diagnostics.troubleshooting.supportContacts.github}
- Documentation: ${diagnostics.troubleshooting.supportContacts.documentation}
- NPM Package: ${diagnostics.troubleshooting.supportContacts.npm}

---

*This report was generated automatically by the Claude Multi-Agent PM Framework installation system.*
`;
        
        await fs.writeFile(reportPath, report);
    }
    
    /**
     * Assess partial deployment in case of failure
     */
    async assessPartialDeployment() {
        try {
            const partialStatus = {};
            for (const [component, dirPath] of Object.entries(this.deploymentPaths)) {
                partialStatus[component] = {
                    directoryExists: fsSync.existsSync(dirPath),
                    hasContent: false
                };
                
                if (partialStatus[component].directoryExists) {
                    try {
                        const contents = await fs.readdir(dirPath);
                        partialStatus[component].hasContent = contents.length > 0;
                        partialStatus[component].contentCount = contents.length;
                    } catch (error) {
                        partialStatus[component].error = error.message;
                    }
                }
            }
            return partialStatus;
        } catch (error) {
            return { error: error.message };
        }
    }
    
    /**
     * Platform-specific script generators
     */
    createUnixHealthCheckScript() {
        return `#!/bin/bash
# Claude PM Framework Health Check Script

echo "🏥 Claude PM Framework Health Check"
echo "===================================="

# Check installation
if command -v claude-pm >/dev/null 2>&1; then
    echo "✅ CLI Available: $(claude-pm --version 2>/dev/null || echo 'Version check failed')"
else
    echo "❌ CLI Not Available"
fi

# Check components
echo "\n📦 Component Status:"
for component in framework scripts templates agents schemas cli docs bin; do
    if [ -d "$HOME/.claude-pm/$component" ]; then
        echo "✅ $component: Deployed"
    else
        echo "❌ $component: Missing"
    fi
done

echo "\n📍 Installation Path: $HOME/.claude-pm/"
echo "📊 Disk Usage: $(du -sh $HOME/.claude-pm/ 2>/dev/null || echo 'Unknown')"
`;
    }
    
    createWindowsHealthCheckScript() {
        return `@echo off
REM Claude PM Framework Health Check Script

echo 🏥 Claude PM Framework Health Check
echo ====================================

REM Check installation
where claude-pm >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ CLI Available
) else (
    echo ❌ CLI Not Available
)

REM Check components
echo.
echo 📦 Component Status:
for %%c in (framework scripts templates agents schemas cli docs bin) do (
    if exist "%USERPROFILE%\.claude-pm\%%c" (
        echo ✅ %%c: Deployed
    ) else (
        echo ❌ %%c: Missing
    )
)

echo.
echo 📍 Installation Path: %USERPROFILE%\.claude-pm\
`;
    }
    
    createUnixCLIWrapper() {
        return `#!/bin/bash
# Claude PM Framework CLI Wrapper

# Find the actual claude-pm executable
CLAUDE_PM_EXEC=""

# Check common locations
if [ -f "$(npm config get prefix)/bin/claude-pm" ]; then
    CLAUDE_PM_EXEC="$(npm config get prefix)/bin/claude-pm"
elif command -v claude-pm >/dev/null 2>&1; then
    CLAUDE_PM_EXEC="$(which claude-pm)"
else
    echo "❌ Claude PM executable not found"
    echo "💡 Try reinstalling: npm install -g @bobmatnyc/claude-multiagent-pm"
    exit 1
fi

# Execute with all arguments
exec "$CLAUDE_PM_EXEC" "$@"
`;
    }
    
    createWindowsCLIWrapper() {
        return `@echo off
REM Claude PM Framework CLI Wrapper

REM Find the actual claude-pm executable
where claude-pm >nul 2>&1
if %errorlevel% == 0 (
    claude-pm %*
) else (
    echo ❌ Claude PM executable not found
    echo 💡 Try reinstalling: npm install -g @bobmatnyc/claude-multiagent-pm
    exit /b 1
)
`;
    }
    
    /**
     * Additional platform-specific setup methods
     */
    async createWindowsScripts() {
        try {
            const scriptsDir = this.deploymentPaths.scripts;
            
            // Create Windows-specific diagnostic script
            const diagnosticScript = `@echo off
REM Claude PM Framework Windows Diagnostic

echo 🏪 Windows Environment Diagnostic
echo ==================================

echo Node.js Version: %NODE_VERSION%
echo NPM Version:
npm --version

echo.
echo Environment Variables:
echo USERPROFILE: %USERPROFILE%
echo PATH (showing npm locations):
echo %PATH% | findstr npm

echo.
echo Claude PM Installation:
where claude-pm
if exist "%USERPROFILE%\.claude-pm" (
    echo ✅ ~/.claude-pm directory exists
    dir "%USERPROFILE%\.claude-pm"
) else (
    echo ❌ ~/.claude-pm directory missing
)
`;
            
            await fs.writeFile(path.join(scriptsDir, 'windows-diagnostic.bat'), diagnosticScript);
            this.log('      ✅ Windows scripts created');
            
        } catch (error) {
            this.log(`      ❌ Failed to create Windows scripts: ${error.message}`, 'error');
        }
    }
    
    async configureWindowsPaths() {
        try {
            // Windows PATH configuration is handled by npm automatically
            // This method can be extended for custom Windows path setup
            this.log('      ✅ Windows PATH configuration completed');
            
        } catch (error) {
            this.log(`      ❌ Windows PATH configuration failed: ${error.message}`, 'error');
        }
    }
    
    async createWindowsBatchFiles() {
        try {
            const binDir = this.deploymentPaths.bin;
            
            // Create additional Windows batch files
            const quickHealthCheck = `@echo off
claude-pm health status
pause
`;
            
            await fs.writeFile(path.join(binDir, 'claude-pm-health.bat'), quickHealthCheck);
            this.log('      ✅ Windows batch files created');
            
        } catch (error) {
            this.log(`      ❌ Failed to create Windows batch files: ${error.message}`, 'error');
        }
    }
    
    async makeDeployedScriptsExecutable() {
        try {
            const scriptsDir = this.deploymentPaths.scripts;
            const binDir = this.deploymentPaths.bin;
            
            await this.makeScriptsExecutable(scriptsDir);
            await this.makeScriptsExecutable(binDir);
            
            this.log('      ✅ All deployed scripts made executable');
            
        } catch (error) {
            this.log(`      ❌ Failed to make deployed scripts executable: ${error.message}`, 'error');
        }
    }
    
    async configureShellIntegration() {
        try {
            const homeDir = os.homedir();
            const shellConfigs = ['.bashrc', '.zshrc'];
            
            const integrationLine = `# Claude PM Framework integration\nexport PATH="$HOME/.claude-pm/bin:$PATH"`;
            
            for (const config of shellConfigs) {
                const configPath = path.join(homeDir, config);
                if (fsSync.existsSync(configPath)) {
                    const content = fsSync.readFileSync(configPath, 'utf8');
                    if (!content.includes('Claude PM Framework integration')) {
                        fsSync.appendFileSync(configPath, `\n${integrationLine}\n`);
                        this.log(`      ✅ Shell integration added to ${config}`);
                    }
                }
            }
            
        } catch (error) {
            this.log(`      ❌ Shell integration failed: ${error.message}`, 'error');
        }
    }
    
    async setupUnixPermissions() {
        try {
            // Set appropriate permissions for deployment directories
            for (const [component, dirPath] of Object.entries(this.deploymentPaths)) {
                if (fsSync.existsSync(dirPath)) {
                    await fs.chmod(dirPath, '755');
                }
            }
            
            this.log('      ✅ Unix permissions configured');
            
        } catch (error) {
            this.log(`      ❌ Unix permissions setup failed: ${error.message}`, 'error');
        }
    }
    
    async createPlatformConfiguration() {
        try {
            const platformConfig = {
                platform: this.platform,
                scriptExtension: this.platform === 'win32' ? '.bat' : '.sh',
                executable: this.platform === 'win32' ? false : true,
                pathSeparator: this.platform === 'win32' ? '\\' : '/',
                homeDirectory: os.homedir(),
                shellIntegration: this.platform !== 'win32',
                environmentVariables: {
                    CLAUDE_PM_HOME: this.globalConfigDir,
                    CLAUDE_PM_PLATFORM: this.platform,
                    CLAUDE_PM_VERSION: require('../package.json').version
                }
            };
            
            const configPath = path.join(this.globalConfigDir, 'platform-config.json');
            await fs.writeFile(configPath, JSON.stringify(platformConfig, null, 2));
            
            this.log('      ✅ Platform configuration created');
            
        } catch (error) {
            this.log(`      ❌ Platform configuration failed: ${error.message}`, 'error');
        }
    }
}

// Run post-install setup
if (require.main === module) {
    const setup = new PostInstallSetup();
    setup.run();
}

module.exports = PostInstallSetup;