#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Portable Deployment Script
 * 
 * Creates fully functional framework deployments in any directory
 * with complete ai-trackdown-tools integration and 42-ticket management.
 * 
 * IMPORTANT: This script preserves existing CLAUDE.md files by default
 * to protect custom project instructions.
 * 
 * Usage:
 *   node install/deploy.js --target ~/Clients/project-name
 *   node install/deploy.js --target ~/Clients/project-name --verbose
 *   npm run deploy -- --target ~/Clients/project-name
 *   
 * Flags:
 *   --target, -t     Target directory for deployment
 *   --verbose, -v    Show detailed output
 *   --dry-run        Show what would be done without making changes
 *   --force          DANGEROUS: Overwrite existing CLAUDE.md (creates backup)
 *   --skip-validation  Skip environment validation checks
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
        this.forceOverwrite = options.forceOverwrite || false;
        
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
        
        this.pythonPackageAvailable = this.checkPythonPackage();
    }

    /**
     * Check if directory is the framework source directory
     */
    isFrameworkSourceDirectory(directory) {
        const frameworkMarkers = [];
        
        // Check for pyproject.toml with our package name
        const pyprojectPath = path.join(directory, 'pyproject.toml');
        if (fsSync.existsSync(pyprojectPath)) {
            try {
                const content = fsSync.readFileSync(pyprojectPath, 'utf8');
                if (content.includes('name = "claude-multiagent-pm"')) {
                    frameworkMarkers.push('pyproject.toml (claude-multiagent-pm)');
                }
            } catch (error) {
                // Ignore read errors
            }
        }
        
        // Check for package.json with our package name
        const packageJsonPath = path.join(directory, 'package.json');
        if (fsSync.existsSync(packageJsonPath)) {
            try {
                const content = fsSync.readFileSync(packageJsonPath, 'utf8');
                if (content.includes('"@bobmatnyc/claude-multiagent-pm"')) {
                    frameworkMarkers.push('package.json (@bobmatnyc/claude-multiagent-pm)');
                }
            } catch (error) {
                // Ignore read errors
            }
        }
        
        // Check for claude_pm source directory
        if (fsSync.existsSync(path.join(directory, 'claude_pm'))) {
            frameworkMarkers.push('claude_pm/ source directory');
        }
        
        // Check if CLAUDE.md mentions framework developers
        const claudeMdPath = path.join(directory, 'CLAUDE.md');
        if (fsSync.existsSync(claudeMdPath)) {
            try {
                const content = fsSync.readFileSync(claudeMdPath, 'utf8');
                if (content.includes('FRAMEWORK DEVELOPERS ONLY')) {
                    frameworkMarkers.push('CLAUDE.md (development version)');
                }
            } catch (error) {
                // Ignore read errors
            }
        }
        
        // Additional framework indicators
        const indicators = [
            { path: 'tests/', name: 'tests/ directory' },
            { path: 'scripts/', name: 'scripts/ directory' },
            { path: 'requirements/', name: 'requirements/ directory' },
            { path: 'framework/', name: 'framework/ templates directory' },
            { path: '.github/workflows/', name: '.github/workflows/ directory' }
        ];
        
        for (const indicator of indicators) {
            if (fsSync.existsSync(path.join(directory, indicator.path))) {
                frameworkMarkers.push(indicator.name);
            }
        }
        
        return {
            isFramework: frameworkMarkers.length > 0,
            markers: frameworkMarkers
        };
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
     * Check if ai-trackdown-pytools Python package is available
     */
    checkPythonPackage() {
        try {
            const pythonCmd = this.pythonCmd || 'python3';
            // Check both module import and CLI availability
            execSync(`${pythonCmd} -c "import ai_trackdown_pytools; print('Module OK')"`, { stdio: 'pipe' });
            execSync(`${pythonCmd} -m ai_trackdown_pytools.cli --version`, { stdio: 'pipe' });
            this.log(`✓ Found ai-trackdown-pytools Python package`);
            return true;
        } catch (error) {
            this.log(`⚠ Warning: ai-trackdown-pytools not found - ticketing features will be unavailable`);
            this.log(`  Install with: pip install --user ai-trackdown-pytools==1.4.0`);
            return false;
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

        // Check ai-trackdown-pytools availability
        if (!this.pythonPackageAvailable) {
            this.log('⚠ WARNING: ai-trackdown-pytools is not installed. Ticketing features will be unavailable.');
            this.log('  Required for PM orchestration and ticket management.');
            this.log('  Install with: pip install --user ai-trackdown-pytools==1.4.0');
            this.log('  After installation, re-run deployment to enable ticketing.');
        } else {
            this.log('✓ ai-trackdown-pytools detected - ticketing features enabled');
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
     * Check MCP service availability and recommend installation
     */
    async checkMCPServices() {
        this.log('Checking MCP service availability...', true);
        
        const recommendedServices = [
            {
                name: 'MCP-Zen',
                description: 'Second opinion service that validates responses with another LLM',
                features: ['Zen quotes', 'Breathing exercises', 'Focus timers', 'Response validation'],
                installCommand: 'npx @modelcontextprotocol/server-zen',
                configExample: {
                    mcpServers: {
                        zen: {
                            command: "npx",
                            args: ["-y", "@modelcontextprotocol/server-zen"]
                        }
                    }
                }
            },
            {
                name: 'Context 7',
                description: 'Up-to-date code documentation and library examples fetcher',
                features: ['Library documentation fetching', 'Current API references', 'Version-specific examples'],
                installCommand: 'npx -y @upstash/context7-mcp',
                configExample: {
                    mcpServers: {
                        context7: {
                            command: "npx",
                            args: ["-y", "@upstash/context7-mcp"]
                        }
                    }
                }
            }
        ];

        this.mcpRecommendations = [];
        
        for (const service of recommendedServices) {
            try {
                // Check if service is available
                const checkCommand = service.name === 'MCP-Zen' ? 
                    'npx @modelcontextprotocol/server-zen --help' : 
                    'npx -y @upstash/context7-mcp --help';
                
                execSync(checkCommand, { stdio: 'ignore', timeout: 5000 });
                this.log(`✓ ${service.name} is available`);
            } catch (error) {
                this.log(`⚠ ${service.name} not found - will recommend installation`);
                this.mcpRecommendations.push(service);
            }
        }

        if (this.mcpRecommendations.length > 0) {
            this.log(`Found ${this.mcpRecommendations.length} MCP services to recommend`);
        } else {
            this.log('✓ All recommended MCP services are available');
        }

        return this.mcpRecommendations;
    }

    /**
     * Present MCP service recommendations to user
     */
    async presentMCPRecommendations() {
        if (!this.mcpRecommendations || this.mcpRecommendations.length === 0) {
            return;
        }

        this.log('🚀 MCP Service Recommendations', true);
        this.log('================================', true);
        this.log('The following MCP services can enhance your Claude PM Framework experience:', true);
        this.log('', true);

        for (const service of this.mcpRecommendations) {
            this.log(`📦 ${service.name}`, true);
            this.log(`   ${service.description}`, true);
            this.log(`   Features: ${service.features.join(', ')}`, true);
            this.log(`   Install: ${service.installCommand}`, true);
            this.log('', true);
        }

        this.log('After installation, these services will be available to your orchestrator', true);
        this.log('for enhanced development workflows and productivity features.', true);
        this.log('', true);

        // In a real CLI environment, you'd prompt for user input here
        // For now, we'll create the configuration file for easy setup
        await this.createMCPConfigurationFile();
    }

    /**
     * Create MCP configuration file for easy setup
     */
    async createMCPConfigurationFile() {
        this.log('Creating MCP configuration template...', true);
        
        const mcpDir = path.join(this.targetDir, '.mcp');
        await fs.mkdir(mcpDir, { recursive: true });
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would create MCP config in: ${mcpDir}`);
            return;
        }

        const config = {
            version: "1.0.0",
            description: "Claude PM Framework MCP Service Configuration",
            recommendedServices: this.mcpRecommendations.map(service => ({
                name: service.name,
                description: service.description,
                features: service.features,
                installCommand: service.installCommand,
                configuration: service.configExample
            })),
            usage: {
                setup: "1. Install recommended services using the provided commands",
                config: "2. Add service configurations to your Claude settings",
                orchestrator: "3. The orchestrator will auto-detect available services"
            }
        };

        const configPath = path.join(mcpDir, 'recommended-services.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));
        
        // Create installation script
        const installScript = this.createMCPInstallScript();
        const scriptPath = path.join(mcpDir, this.platform === 'win32' ? 'install-mcp-services.bat' : 'install-mcp-services.sh');
        await fs.writeFile(scriptPath, installScript);
        
        if (this.platform !== 'win32') {
            await fs.chmod(scriptPath, '755');
        }

        this.log(`✓ MCP configuration created at ${configPath}`);
        this.log(`✓ Installation script created at ${scriptPath}`);
    }

    /**
     * Create MCP service installation script
     */
    createMCPInstallScript() {
        if (this.platform === 'win32') {
            return `@echo off
REM Claude PM Framework - MCP Service Installation
REM Generated by deployment script v${this.frameworkVersion}

echo Installing recommended MCP services...
echo ========================================

${this.mcpRecommendations.map(service => `
echo Installing ${service.name}...
${service.installCommand}
if %errorlevel% neq 0 (
    echo Warning: Failed to install ${service.name}
) else (
    echo ✓ ${service.name} installed successfully
)
echo.
`).join('')}

echo ========================================
echo MCP service installation completed
echo.
echo Next steps:
echo 1. Configure services in your Claude settings
echo 2. Restart Claude to load new services
echo 3. The orchestrator will auto-detect available services
`;
        } else {
            return `#!/bin/bash
# Claude PM Framework - MCP Service Installation
# Generated by deployment script v${this.frameworkVersion}

echo "Installing recommended MCP services..."
echo "========================================"

${this.mcpRecommendations.map(service => `
echo "Installing ${service.name}..."
if ${service.installCommand}; then
    echo "✓ ${service.name} installed successfully"
else
    echo "⚠ Warning: Failed to install ${service.name}"
fi
echo
`).join('')}

echo "========================================"
echo "MCP service installation completed"
echo
echo "Next steps:"
echo "1. Configure services in your Claude settings"
echo "2. Restart Claude to load new services" 
echo "3. The orchestrator will auto-detect available services"
`;
        }
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
     * These wrappers ensure the Python CLI commands work correctly by:
     * 1. Activating any available virtual environment (project or global)
     * 2. Running the ai-trackdown-pytools CLI module
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
        
        // Copy the main claude-pm binary
        const sourceBin = path.join(this.packageDir, 'bin', 'claude-pm');
        const targetBin = path.join(binDir, 'claude-pm');
        await fs.copyFile(sourceBin, targetBin);
        
        // Copy package.json for version info
        const sourcePackageJson = path.join(this.packageDir, 'package.json');
        const targetPackageJson = path.join(this.targetDir, 'package.json');
        await fs.copyFile(sourcePackageJson, targetPackageJson);
        
        if (this.platform !== 'win32') {
            await fs.chmod(targetBin, '755');
        }
        
        this.log(`✓ AI-trackdown CLI wrappers created in ${binDir}`);
    }

    /**
     * Create Windows CLI wrapper (Python version)
     */
    createWindowsWrapper(command) {
        return `@echo off
REM Claude PM Framework - ${command} wrapper (Python version)
REM Generated by deployment script v${this.frameworkVersion}

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM Check if virtual environment exists and activate it
if exist "%PROJECT_DIR%\\venv\\Scripts\\activate.bat" (
    call "%PROJECT_DIR%\\venv\\Scripts\\activate.bat"
) else if exist "%PROJECT_DIR%\\.venv\\Scripts\\activate.bat" (
    call "%PROJECT_DIR%\\.venv\\Scripts\\activate.bat"
) else if exist "%USERPROFILE%\\.claude-pm\\venv\\Scripts\\activate.bat" (
    call "%USERPROFILE%\\.claude-pm\\venv\\Scripts\\activate.bat"
)

REM Run the Python CLI command
REM First try python3, then python
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 -m ai_trackdown_pytools.cli %*
) else (
    python -m ai_trackdown_pytools.cli %*
)
`;
    }

    /**
     * Create Unix CLI wrapper (Python version)
     */
    createUnixWrapper(command) {
        return `#!/bin/bash
# Claude PM Framework - ${command} wrapper (Python version)
# Generated by deployment script v${this.frameworkVersion}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists and activate it
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
elif [ -f "$HOME/.claude-pm/venv/bin/activate" ]; then
    source "$HOME/.claude-pm/venv/bin/activate"
fi

# Run the Python CLI command
# First try with python3, fallback to python if that fails
if command -v python3 >/dev/null 2>&1; then
    python3 -m ai_trackdown_pytools.cli "$@"
else
    python -m ai_trackdown_pytools.cli "$@"
fi
`;
    }

    /**
     * Initialize ticketing hierarchy
     */
    async initializeTicketingHierarchy() {
        this.log('Initializing ticketing hierarchy...', true);
        
        const ticketsDir = path.join(this.targetDir, 'tickets');
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would initialize ticketing hierarchy in: ${ticketsDir}`);
            return;
        }
        
        try {
            // Create ticketing structure (ai-trackdown-pytools format)
            await fs.mkdir(path.join(ticketsDir, 'epics'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'issues'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'tasks'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'prs'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'templates'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'archive'), { recursive: true });
            await fs.mkdir(path.join(ticketsDir, 'reports'), { recursive: true });
            
            // Create .ai-trackdown directory for tracking
            const trackingDir = path.join(ticketsDir, '.ai-trackdown');
            await fs.mkdir(trackingDir, { recursive: true });
            
            // Initialize counters file
            const countersPath = path.join(trackingDir, 'counters.json');
            if (!fsSync.existsSync(countersPath)) {
                const counters = {
                    epic: 0,
                    issue: 0,
                    task: 0,
                    pr: 0
                };
                await fs.writeFile(countersPath, JSON.stringify(counters, null, 2));
            }
            
            // Create README for tickets directory
            const readmePath = path.join(ticketsDir, 'README.md');
            const readmeContent = `# Tickets Directory

This directory contains all project tickets managed by ai-trackdown-pytools.

## Structure
- \`epics/\` - Large features spanning multiple sprints
- \`issues/\` - Standard development tasks
- \`tasks/\` - Small, focused work items
- \`prs/\` - Pull request tracking
- \`templates/\` - Ticket templates
- \`archive/\` - Closed tickets
- \`reports/\` - Sprint and progress reports

## Usage
Use the \`aitrackdown\` or \`atd\` CLI commands to manage tickets:

\`\`\`bash
# List all open tickets
aitrackdown list

# Create a new issue
aitrackdown create --type issue --title "Implement feature X"

# Update ticket status
aitrackdown update ISS-0001 --status in-progress
\`\`\`

For more information, see the framework documentation.
`;
            
            if (!fsSync.existsSync(readmePath)) {
                await fs.writeFile(readmePath, readmeContent);
            }
            
            this.log(`✓ Ticketing hierarchy initialized in ${ticketsDir}`);
            
            // Also check for legacy tasks directory
            const tasksDir = path.join(this.targetDir, 'tasks');
            if (fsSync.existsSync(tasksDir)) {
                this.log(`⚠ Legacy tasks/ directory found - migration may be needed`);
                this.log(`  Run 'claude-pm init' after deployment to migrate to tickets/`);
            }
            
        } catch (error) {
            throw new Error(`Failed to initialize ticketing hierarchy: ${error.message}`);
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
            pythonPackageAvailable: this.pythonPackageAvailable,
            aiTrackdownPath: path.join(this.targetDir, 'bin', this.platform === 'win32' ? 'aitrackdown.bat' : 'aitrackdown'),
            paths: {
                framework: path.join(this.targetDir, 'claude_pm'),
                templates: path.join(this.targetDir, 'templates'),
                schemas: path.join(this.targetDir, 'schemas'),
                tickets: path.join(this.targetDir, 'tickets'),
                bin: path.join(this.targetDir, 'bin'),
                config: configDir
            },
            features: {
                ticketingEnabled: this.pythonPackageAvailable,
                aiTrackdownIntegration: this.pythonPackageAvailable,
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
        this.log('Checking for existing CLAUDE.md...', true);
        
        // Check if we're in the framework source directory
        const frameworkCheck = this.isFrameworkSourceDirectory(this.targetDir);
        if (frameworkCheck.isFramework) {
            this.log(`⚠️  WARNING: Skipping CLAUDE.md generation - detected framework source directory`, true);
            this.log(`   Framework markers found: ${frameworkCheck.markers.join(', ')}`, true);
            this.log(`   Framework source should not have deployment CLAUDE.md`, true);
            return;
        }
        
        if (this.dryRun) {
            this.log(`[DRY RUN] Would check/generate CLAUDE.md in: ${this.targetDir}`);
            return;
        }
        
        const claudePath = path.join(this.targetDir, 'CLAUDE.md');
        
        try {
            // Check if CLAUDE.md already exists
            const fileExists = fsSync.existsSync(claudePath);
            
            if (fileExists && !this.forceOverwrite) {
                this.log(`⚠️  WARNING: CLAUDE.md already exists at ${claudePath}`, true);
                this.log(`   Preserving existing custom instructions.`, true);
                this.log(`   To regenerate, use --force flag (THIS WILL DESTROY CUSTOM CONTENT!)`, true);
                return;
            }
            
            if (fileExists && this.forceOverwrite) {
                this.log(`⚠️  WARNING: Overwriting existing CLAUDE.md due to --force flag`, true);
                this.log(`   THIS WILL DESTROY ANY CUSTOM INSTRUCTIONS!`, true);
                
                // Create backup of existing file
                const backupPath = `${claudePath}.backup.${Date.now()}`;
                await fs.copyFile(claudePath, backupPath);
                this.log(`   Created backup at: ${backupPath}`, true);
            }
            
            // Read template
            const templatePath = path.join(this.packageDir, 'framework', 'CLAUDE.md');
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
                '{{AI_TRACKDOWN_AVAILABLE}}': this.pythonPackageAvailable ? 'Available via Python' : 'Not installed',
                '{{NODE_VERSION}}': nodeVersion,
                '{{DEPLOYMENT_ID}}': deploymentId,
                '{{LAST_UPDATED}}': deploymentDate,
                '{{PLATFORM_NOTES}}': this.getPlatformNotes()
            };
            
            for (const [placeholder, value] of Object.entries(replacements)) {
                claudeTemplate = claudeTemplate.replace(new RegExp(placeholder, 'g'), value);
            }
            
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
if ./bin/aitrackdown --version >/dev/null 2>&1; then
    echo "✓ AI-trackdown CLI available"
    
    # Test ticketing commands
    if ./bin/aitrackdown list >/dev/null 2>&1; then
        echo "✓ Ticketing commands working"
    else
        echo "⚠ Ticketing commands not functioning properly"
    fi
else
    echo "⚠ AI-trackdown CLI not available - ticketing disabled"
    echo "  Install ai-trackdown-pytools: pip install --user ai-trackdown-pytools==1.4.0"
fi

# Check tickets directory
if [ -d "tickets" ]; then
    echo "✓ Tickets directory present"
else
    echo "⚠ Tickets directory missing"
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

REM Test AI-trackdown functionality
bin\\aitrackdown.bat --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ AI-trackdown CLI available
    
    REM Test ticketing commands
    bin\\aitrackdown.bat list >nul 2>&1
    if %errorlevel% == 0 (
        echo ✓ Ticketing commands working
    ) else (
        echo ⚠ Ticketing commands not functioning properly
    )
) else (
    echo ⚠ AI-trackdown CLI not available - ticketing disabled
    echo   Install ai-trackdown-pytools: pip install --user ai-trackdown-pytools==1.4.0
)

REM Check tickets directory
if exist "tickets" (
    echo ✓ Tickets directory present
) else (
    echo ⚠ Tickets directory missing
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
            await this.checkMCPServices();
            await this.deployFrameworkCore();
            await this.deployTemplatesAndSchemas();
            await this.createAiTrackdownWrappers();
            await this.initializeTicketingHierarchy();
            await this.generateDeploymentConfig();
            await this.generateClaudeConfig();
            await this.createHealthCheck();
            await this.presentMCPRecommendations();
            
            this.log('🎉 Claude PM Framework deployment completed successfully!', true);
            this.log(`Framework location: ${path.join(this.targetDir, 'claude_pm')}`, true);
            this.log(`Configuration: ${path.join(this.targetDir, '.claude-pm', 'config.json')}`, true);
            this.log(`Health check: ${path.join(this.targetDir, 'scripts', this.platform === 'win32' ? 'health-check.bat' : 'health-check.sh')}`, true);
            
            if (this.pythonPackageAvailable) {
                this.log(`✅ Ticketing enabled: ${path.join(this.targetDir, 'bin', 'aitrackdown')}`, true);
                this.log(`   Tickets directory: ${path.join(this.targetDir, 'tickets')}`, true);
                this.log(`   Use 'aitrackdown list' to view tickets`, true);
            } else {
                this.log(`⚠️ Ticketing disabled - install ai-trackdown-pytools to enable`, true);
                this.log(`   Run: pip install --user ai-trackdown-pytools==1.4.0`, true);
            }
            
            if (this.mcpRecommendations && this.mcpRecommendations.length > 0) {
                this.log(`MCP recommendations: ${path.join(this.targetDir, '.mcp', 'recommended-services.json')}`, true);
                this.log(`MCP install script: ${path.join(this.targetDir, '.mcp', this.platform === 'win32' ? 'install-mcp-services.bat' : 'install-mcp-services.sh')}`, true);
            }
            
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
        dryRun: args.includes('--dry-run'),
        forceOverwrite: args.includes('--force')
    };
    
    // Parse target directory
    const targetIndex = args.findIndex(arg => arg === '--target' || arg === '-t');
    if (targetIndex !== -1 && args[targetIndex + 1]) {
        options.targetDir = path.resolve(args[targetIndex + 1]);
    }
    
    // Show warning if force flag is used
    if (options.forceOverwrite) {
        console.log('⚠️  WARNING: --force flag detected!');
        console.log('   This will OVERWRITE any existing CLAUDE.md file.');
        console.log('   Custom instructions will be PERMANENTLY LOST!');
        console.log('   Press Ctrl+C to cancel, or wait 5 seconds to continue...');
        
        // Give user time to cancel
        setTimeout(() => {
            const deployer = new ClaudePMDeploymentEngine(options);
            
            deployer.deploy()
                .then(() => {
                    process.exit(0);
                })
                .catch((error) => {
                    console.error('Deployment failed:', error.message);
                    process.exit(1);
                });
        }, 5000);
    } else {
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
}

module.exports = ClaudePMDeploymentEngine;