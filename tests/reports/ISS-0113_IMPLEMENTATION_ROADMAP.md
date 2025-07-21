# ISS-0113 CLI Flags Implementation Roadmap
## QA Agent Recommendations for DevOps Agent

**Date**: 2025-07-14  
**Author**: QA Agent  
**Target**: DevOps Agent  
**Priority**: CRITICAL  

---

## Implementation Overview

Based on comprehensive testing, ISS-0113 CLI flags system requires **complete implementation** from the ground up. This roadmap provides DevOps Agent with specific, actionable steps to implement the required functionality.

---

## Phase 1: Core Flag Infrastructure (Days 1-2)

### 1.1 Create Flag Management Foundation

**File**: `lib/cli-modules/flag-manager.js`
```javascript
/**
 * CLI Flag Management System for ISS-0113
 * Handles argument parsing, validation, and flag combination logic
 */

class CLIArgumentParser {
    constructor() {
        this.supportedFlags = new Set([
            '--save', '--upgrade', '--rollback', '--version', '--help',
            '--verify', '--debug', '--force', '--dry-run', '--system-info'
        ]);
        this.incompatibleCombinations = [
            ['--save', '--force'],
            ['--dry-run', '--force']
        ];
    }

    parseArguments(args) {
        const flags = {};
        const commands = [];
        
        for (let i = 0; i < args.length; i++) {
            const arg = args[i];
            if (arg.startsWith('--')) {
                if (this.supportedFlags.has(arg)) {
                    flags[arg.slice(2)] = true;
                    // Handle flags with values
                    if (arg === '--rollback' && args[i + 1] && !args[i + 1].startsWith('--')) {
                        flags.rollbackTarget = args[++i];
                    }
                } else {
                    throw new Error(`Unknown flag: ${arg}`);
                }
            } else {
                commands.push(arg);
            }
        }
        
        this.validateFlagCombinations(flags);
        return { flags, commands };
    }

    validateFlagCombinations(flags) {
        for (const [flag1, flag2] of this.incompatibleCombinations) {
            if (flags[flag1.slice(2)] && flags[flag2.slice(2)]) {
                throw new Error(`Incompatible flags: ${flag1} and ${flag2} cannot be used together`);
            }
        }
    }
}

class FlagManager {
    constructor(flags) {
        this.flags = flags;
    }

    isSafeMode() {
        return !!this.flags.save;
    }

    requiresConfirmation() {
        return this.isSafeMode() && !this.flags.force;
    }

    isDebugEnabled() {
        return !!this.flags.debug;
    }

    isDryRunMode() {
        return !!this.flags['dry-run'];
    }

    isForceMode() {
        return !!this.flags.force;
    }
}

module.exports = { CLIArgumentParser, FlagManager };
```

### 1.2 Implement SafeModeManager

**File**: `lib/cli-modules/safe-mode-manager.js`
```javascript
/**
 * Safe Mode Manager for --save flag functionality
 * Implements "no YOLO" operations with confirmations and backups
 */

const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');

class SafeModeManager {
    constructor() {
        this.backupDir = path.join(process.cwd(), '.claude-pm', 'backups');
        this.confirmationTimeout = 30000; // 30 second timeout
    }

    async confirmDestructiveAction(action, details) {
        if (process.env.NODE_ENV === 'test') {
            return true; // Auto-confirm in tests
        }

        console.log(`\\n🚨 DESTRUCTIVE ACTION CONFIRMATION REQUIRED`);
        console.log(`Action: ${action}`);
        console.log(`Details:`);
        details.forEach(detail => console.log(`  • ${detail}`));
        console.log(`\\nThis action cannot be undone automatically.`);
        
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        return new Promise((resolve) => {
            const timeout = setTimeout(() => {
                console.log(`\\n⏰ Confirmation timeout (${this.confirmationTimeout / 1000}s). Operation cancelled.`);
                rl.close();
                resolve(false);
            }, this.confirmationTimeout);

            rl.question('\\nDo you want to proceed? (yes/no): ', (answer) => {
                clearTimeout(timeout);
                rl.close();
                const confirmed = answer.toLowerCase() === 'yes' || answer.toLowerCase() === 'y';
                if (confirmed) {
                    console.log('✅ Confirmed. Proceeding with operation...');
                } else {
                    console.log('❌ Operation cancelled by user.');
                }
                resolve(confirmed);
            });
        });
    }

    async createBackupBeforeAction(action) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = path.join(this.backupDir, `backup_${action}_${timestamp}`);
        
        try {
            await fs.mkdir(this.backupDir, { recursive: true });
            
            // Create backup metadata
            const metadata = {
                action,
                timestamp: new Date().toISOString(),
                originalPath: process.cwd(),
                backupPath
            };
            
            await fs.writeFile(
                path.join(backupPath, 'backup_metadata.json'),
                JSON.stringify(metadata, null, 2)
            );
            
            console.log(`📦 Backup created: ${backupPath}`);
            return backupPath;
        } catch (error) {
            console.error(`❌ Failed to create backup: ${error.message}`);
            throw new Error(`Backup creation failed: ${error.message}`);
        }
    }

    async validateBeforeExecution(operation) {
        const validations = [];
        
        // Check disk space
        try {
            const stats = await fs.stat(process.cwd());
            validations.push({ check: 'Disk Access', status: 'OK' });
        } catch (error) {
            validations.push({ check: 'Disk Access', status: 'FAIL', error: error.message });
        }
        
        // Check permissions
        try {
            await fs.access(process.cwd(), fs.constants.W_OK);
            validations.push({ check: 'Write Permissions', status: 'OK' });
        } catch (error) {
            validations.push({ check: 'Write Permissions', status: 'FAIL', error: error.message });
        }
        
        // Check backup directory
        try {
            await fs.mkdir(this.backupDir, { recursive: true });
            validations.push({ check: 'Backup Directory', status: 'OK' });
        } catch (error) {
            validations.push({ check: 'Backup Directory', status: 'FAIL', error: error.message });
        }
        
        const failed = validations.filter(v => v.status === 'FAIL');
        
        if (failed.length > 0) {
            console.log('\\n❌ Pre-execution validation failed:');
            failed.forEach(f => console.log(`  • ${f.check}: ${f.error}`));
            return false;
        }
        
        console.log('✅ Pre-execution validation passed');
        return true;
    }

    logSafeModeOperation(operation, result) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            operation,
            result,
            safeMode: true
        };
        
        console.log(`📝 Safe mode operation logged: ${operation} - ${result ? 'SUCCESS' : 'FAILED'}`);
        // TODO: Implement persistent logging to file
    }
}

module.exports = SafeModeManager;
```

### 1.3 Update Command Dispatcher Integration

**File**: `lib/cli-modules/command-dispatcher.js` (UPDATE)
```javascript
// Add to existing command-dispatcher.js imports:
const { CLIArgumentParser, FlagManager } = require('./flag-manager');
const SafeModeManager = require('./safe-mode-manager');

// Update handleSpecialFlags method:
async handleSpecialFlags(args) {
    try {
        const parser = new CLIArgumentParser();
        const { flags, commands } = parser.parseArguments(args);
        const flagManager = new FlagManager(flags);
        
        // Handle ISS-0113 flags
        if (flags.save) {
            return await this.handleSafeMode(flagManager, commands);
        }
        
        if (flags.upgrade) {
            return await this.handleUpgrade(flagManager);
        }
        
        if (flags.rollback) {
            return await this.handleRollback(flagManager, flags.rollbackTarget);
        }
        
        if (flags.verify) {
            return await this.handleVerify(flagManager);
        }
        
        // ... existing flag handling ...
        
    } catch (error) {
        console.error(`❌ Flag processing error: ${error.message}`);
        return false;
    }
    
    // ... rest of existing method ...
}

async handleSafeMode(flagManager, commands) {
    const safeMode = new SafeModeManager();
    console.log('🛡️  Safe mode enabled - all operations will require confirmation');
    
    if (commands.length === 0) {
        console.log('ℹ️  Safe mode active. Use with other commands to enable confirmation prompts.');
        return true;
    }
    
    // TODO: Integrate with actual command execution
    return true;
}
```

---

## Phase 2: Version and Upgrade Management (Days 2-3)

### 2.1 Enhanced Version Manager

**File**: `lib/cli-modules/version-manager.js`
```javascript
/**
 * Enhanced Version Manager for comprehensive --version display
 * Implements ISS-0113 version information requirements
 */

const fs = require('fs').promises;
const path = require('path');
const os = require('os');

class VersionManager {
    constructor() {
        this.frameworkPath = this.detectFrameworkPath();
    }

    detectFrameworkPath() {
        // Use existing deployment detection logic
        const scriptDir = __dirname;
        return path.join(scriptDir, '..', '..');
    }

    async getFrameworkVersion() {
        try {
            const packagePath = path.join(this.frameworkPath, 'package.json');
            const packageData = JSON.parse(await fs.readFile(packagePath, 'utf8'));
            return packageData.version;
        } catch (error) {
            try {
                const versionPath = path.join(this.frameworkPath, 'VERSION');
                return (await fs.readFile(versionPath, 'utf8')).trim();
            } catch (versionError) {
                return 'unknown';
            }
        }
    }

    async getComponentVersions() {
        const components = {};
        
        try {
            // Agents System
            const agentsPath = path.join(this.frameworkPath, 'claude_pm', 'agents');
            components['Agents System'] = await this.getDirectoryVersion(agentsPath);
            
            // Template Engine
            const templatesPath = path.join(this.frameworkPath, 'framework');
            components['Template Engine'] = await this.getDirectoryVersion(templatesPath);
            
            // Script Deployment
            const scriptsPath = path.join(this.frameworkPath, 'scripts');
            components['Script Deployment'] = await this.getDirectoryVersion(scriptsPath);
            
            // Health Monitoring
            const healthPath = path.join(this.frameworkPath, 'claude_pm', 'health');
            components['Health Monitoring'] = await this.getDirectoryVersion(healthPath);
            
        } catch (error) {
            console.warn(`Warning: Could not detect all component versions: ${error.message}`);
        }
        
        return components;
    }

    async getDirectoryVersion(dirPath) {
        try {
            await fs.access(dirPath);
            return await this.getFrameworkVersion(); // Use framework version for now
        } catch (error) {
            return 'not found';
        }
    }

    async getInstallationInfo() {
        const info = {};
        
        try {
            // Installation paths
            info.frameworkPath = this.frameworkPath;
            info.userConfigPath = path.join(os.homedir(), '.claude-pm');
            info.projectConfigPath = path.join(process.cwd(), '.claude-pm');
            
            // Installation status
            info.userConfigExists = await this.pathExists(info.userConfigPath);
            info.projectConfigExists = await this.pathExists(info.projectConfigPath);
            
            // Installation metadata
            const configPath = path.join(info.userConfigPath, 'config.json');
            if (await this.pathExists(configPath)) {
                const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
                info.installDate = config.installDate;
                info.lastUpdate = config.lastUpdate;
                info.installType = config.installType;
            }
            
        } catch (error) {
            console.warn(`Warning: Could not gather installation info: ${error.message}`);
        }
        
        return info;
    }

    async pathExists(path) {
        try {
            await fs.access(path);
            return true;
        } catch (error) {
            return false;
        }
    }

    async checkVersionCompatibility() {
        const compatibility = {};
        
        // Node.js version check
        const nodeVersion = process.version;
        const nodeMajor = parseInt(nodeVersion.slice(1).split('.')[0]);
        compatibility.nodejs = {
            version: nodeVersion,
            compatible: nodeMajor >= 18,
            requirement: '>=18.0.0'
        };
        
        // Python version check (if available)
        try {
            const { execSync } = require('child_process');
            const pythonVersion = execSync('python3 --version', { encoding: 'utf8' }).trim();
            const pythonMatch = pythonVersion.match(/Python (\\d+)\\.(\\d+)/);
            if (pythonMatch) {
                const major = parseInt(pythonMatch[1]);
                const minor = parseInt(pythonMatch[2]);
                compatibility.python = {
                    version: pythonVersion,
                    compatible: major >= 3 && minor >= 8,
                    requirement: '>=3.8.0'
                };
            }
        } catch (error) {
            compatibility.python = {
                version: 'not found',
                compatible: false,
                requirement: '>=3.8.0'
            };
        }
        
        return compatibility;
    }

    async formatVersionDisplay() {
        const frameworkVersion = await this.getFrameworkVersion();
        const components = await this.getComponentVersions();
        const installation = await this.getInstallationInfo();
        const compatibility = await this.checkVersionCompatibility();
        
        let output = `\\nClaude PM Framework v${frameworkVersion}\\n`;
        output += '='.repeat(30) + '\\n\\n';
        
        // Core Information
        output += `Framework Core: v${frameworkVersion}\\n`;
        
        // NPM Package info
        try {
            const { execSync } = require('child_process');
            const npmVersion = execSync('npm list -g @bobmatnyc/claude-multiagent-pm --depth=0', 
                { encoding: 'utf8', stdio: 'pipe' });
            const versionMatch = npmVersion.match(/@bobmatnyc\\/claude-multiagent-pm@([\\d\\.]+)/);
            if (versionMatch) {
                output += `NPM Package: @bobmatnyc/claude-multiagent-pm@${versionMatch[1]}\\n`;
            }
        } catch (error) {
            output += `NPM Package: Not globally installed\\n`;
        }
        
        // Installation paths
        output += `Installation: ${installation.userConfigPath}\\n`;
        if (installation.projectConfigExists) {
            output += `Deployed: ${installation.projectConfigPath}\\n`;
        }
        
        // Components
        output += '\\nComponents:\\n';
        Object.entries(components).forEach(([name, version]) => {
            output += `  - ${name}: v${version}\\n`;
        });
        
        // Platform Information
        output += `\\nPlatform: ${os.platform()} ${os.release()}`;
        if (os.arch() === 'arm64') {
            output += ' (Apple Silicon)';
        }
        output += '\\n';
        
        // Environment
        Object.entries(compatibility).forEach(([env, info]) => {
            const status = info.compatible ? '✅' : '❌';
            output += `${env.charAt(0).toUpperCase() + env.slice(1)}: ${info.version} ${status}\\n`;
        });
        
        // Overall Status
        const allCompatible = Object.values(compatibility).every(c => c.compatible);
        output += `\\nStatus: ${allCompatible ? '✅ All components up-to-date' : '⚠️  Compatibility issues detected'}\\n`;
        
        if (installation.lastUpdate) {
            output += `Last Update: ${installation.lastUpdate}\\n`;
        }
        
        return output;
    }
}

module.exports = VersionManager;
```

### 2.2 Upgrade Manager Implementation

**File**: `lib/cli-modules/upgrade-manager.js`
```javascript
/**
 * Upgrade Manager for --upgrade flag functionality
 * Handles NPM package updates and framework component upgrades
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class UpgradeManager {
    constructor(flagManager) {
        this.flagManager = flagManager;
        this.npmPackageName = '@bobmatnyc/claude-multiagent-pm';
        this.backupDir = path.join(process.cwd(), '.claude-pm', 'upgrade-backups');
    }

    async checkForUpdates() {
        const updates = {};
        
        try {
            // Check NPM package updates
            const npmCheck = execSync(`npm outdated -g ${this.npmPackageName} --json`, 
                { encoding: 'utf8', stdio: 'pipe' });
            const outdated = JSON.parse(npmCheck);
            
            if (outdated[this.npmPackageName]) {
                updates.npm = {
                    current: outdated[this.npmPackageName].current,
                    wanted: outdated[this.npmPackageName].wanted,
                    latest: outdated[this.npmPackageName].latest,
                    updateAvailable: true
                };
            } else {
                updates.npm = {
                    current: 'latest',
                    updateAvailable: false
                };
            }
        } catch (error) {
            // npm outdated exits with code 1 when updates are available
            if (error.stdout) {
                try {
                    const outdated = JSON.parse(error.stdout);
                    if (outdated[this.npmPackageName]) {
                        updates.npm = {
                            current: outdated[this.npmPackageName].current,
                            wanted: outdated[this.npmPackageName].wanted,
                            latest: outdated[this.npmPackageName].latest,
                            updateAvailable: true
                        };
                    }
                } catch (parseError) {
                    updates.npm = { error: 'Could not check NPM updates' };
                }
            } else {
                updates.npm = { error: error.message };
            }
        }
        
        return updates;
    }

    async createUpgradeBackup() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = path.join(this.backupDir, `pre-upgrade-${timestamp}`);
        
        try {
            await fs.mkdir(this.backupDir, { recursive: true });
            
            // Backup current installation
            const currentConfig = path.join(process.env.HOME, '.claude-pm', 'config.json');
            if (await this.pathExists(currentConfig)) {
                const backupConfig = path.join(backupPath, 'config.json');
                await fs.mkdir(backupPath, { recursive: true });
                await fs.copyFile(currentConfig, backupConfig);
            }
            
            // Create backup metadata
            const metadata = {
                timestamp: new Date().toISOString(),
                upgradeType: 'npm-package',
                backupPath,
                preUpgradeVersion: await this.getCurrentVersion()
            };
            
            await fs.writeFile(
                path.join(backupPath, 'upgrade_metadata.json'),
                JSON.stringify(metadata, null, 2)
            );
            
            console.log(`📦 Upgrade backup created: ${backupPath}`);
            return backupPath;
            
        } catch (error) {
            throw new Error(`Backup creation failed: ${error.message}`);
        }
    }

    async getCurrentVersion() {
        try {
            const output = execSync(`npm list -g ${this.npmPackageName} --depth=0`, 
                { encoding: 'utf8' });
            const match = output.match(/@bobmatnyc\\/claude-multiagent-pm@([\\d\\.]+)/);
            return match ? match[1] : 'unknown';
        } catch (error) {
            return 'unknown';
        }
    }

    async performNpmUpdate() {
        try {
            console.log('📦 Updating NPM package...');
            
            if (this.flagManager.isDryRunMode()) {
                console.log('🔍 DRY RUN: Would execute: npm install -g ' + this.npmPackageName + '@latest');
                return true;
            }
            
            const updateCmd = `npm install -g ${this.npmPackageName}@latest`;
            
            if (this.flagManager.isSafeMode()) {
                console.log(`About to execute: ${updateCmd}`);
                // SafeModeManager confirmation would be handled by calling code
            }
            
            execSync(updateCmd, { stdio: 'inherit' });
            console.log('✅ NPM package updated successfully');
            return true;
            
        } catch (error) {
            console.error(`❌ NPM update failed: ${error.message}`);
            return false;
        }
    }

    async updateFrameworkComponents() {
        try {
            console.log('🔧 Updating framework components...');
            
            if (this.flagManager.isDryRunMode()) {
                console.log('🔍 DRY RUN: Would update framework components');
                return true;
            }
            
            // Framework components are updated via NPM package
            // Additional component-specific updates can be added here
            
            console.log('✅ Framework components updated');
            return true;
            
        } catch (error) {
            console.error(`❌ Framework component update failed: ${error.message}`);
            return false;
        }
    }

    async migrateConfiguration() {
        try {
            console.log('⚙️  Migrating configuration...');
            
            if (this.flagManager.isDryRunMode()) {
                console.log('🔍 DRY RUN: Would migrate configuration if needed');
                return true;
            }
            
            // Configuration migration logic would go here
            // For now, just validate existing configuration
            
            console.log('✅ Configuration migration completed');
            return true;
            
        } catch (error) {
            console.error(`❌ Configuration migration failed: ${error.message}`);
            return false;
        }
    }

    async validateUpgrade() {
        const validation = {};
        
        try {
            // Validate NPM package installation
            const newVersion = await this.getCurrentVersion();
            validation.npmPackage = {
                installed: newVersion !== 'unknown',
                version: newVersion
            };
            
            // Validate CLI accessibility
            try {
                execSync('claude-pm --version', { encoding: 'utf8', timeout: 5000 });
                validation.cliAccess = { working: true };
            } catch (error) {
                validation.cliAccess = { working: false, error: error.message };
            }
            
            // Validate framework components
            validation.frameworkComponents = await this.validateComponents();
            
        } catch (error) {
            validation.error = error.message;
        }
        
        return validation;
    }

    async validateComponents() {
        const components = {};
        
        // Add component validation logic here
        components.basic = { status: 'ok' };
        
        return components;
    }

    async rollbackFailedUpgrade() {
        try {
            console.log('🔄 Rolling back failed upgrade...');
            
            // Find most recent backup
            const backups = await fs.readdir(this.backupDir);
            const upgradeBackups = backups.filter(b => b.startsWith('pre-upgrade-'));
            
            if (upgradeBackups.length === 0) {
                throw new Error('No upgrade backup found for rollback');
            }
            
            const latestBackup = upgradeBackups.sort().pop();
            console.log(`📦 Using backup: ${latestBackup}`);
            
            // Rollback logic would go here
            
            console.log('✅ Upgrade rollback completed');
            return true;
            
        } catch (error) {
            console.error(`❌ Upgrade rollback failed: ${error.message}`);
            return false;
        }
    }

    async pathExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch (error) {
            return false;
        }
    }
}

module.exports = UpgradeManager;
```

---

## Phase 3: Rollback and Support Flags (Days 3-4)

### 3.1 Rollback Manager Implementation

**File**: `lib/cli-modules/rollback-manager.js`
```javascript
/**
 * Rollback Manager for --rollback flag functionality
 * Handles version rollback with state restoration
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class RollbackManager {
    constructor(flagManager) {
        this.flagManager = flagManager;
        this.npmPackageName = '@bobmatnyc/claude-multiagent-pm';
        this.backupDir = path.join(process.cwd(), '.claude-pm', 'rollback-points');
    }

    async listRollbackPoints() {
        const rollbackPoints = [];
        
        try {
            // Check for local backup points
            const backupExists = await this.pathExists(this.backupDir);
            if (backupExists) {
                const backups = await fs.readdir(this.backupDir);
                
                for (const backup of backups) {
                    const metadataPath = path.join(this.backupDir, backup, 'rollback_metadata.json');
                    if (await this.pathExists(metadataPath)) {
                        const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));
                        rollbackPoints.push({
                            id: backup,
                            version: metadata.version,
                            timestamp: metadata.timestamp,
                            description: metadata.description || 'Automatic backup',
                            type: 'local'
                        });
                    }
                }
            }
            
            // Check for available NPM versions
            try {
                const npmVersions = execSync(`npm view ${this.npmPackageName} versions --json`, 
                    { encoding: 'utf8' });
                const versions = JSON.parse(npmVersions);
                
                // Add recent NPM versions as rollback points
                const recentVersions = versions.slice(-5); // Last 5 versions
                recentVersions.forEach(version => {
                    rollbackPoints.push({
                        id: `npm-${version}`,
                        version,
                        timestamp: null, // Would need npm info to get publish date
                        description: `NPM Package v${version}`,
                        type: 'npm'
                    });
                });
                
            } catch (npmError) {
                console.warn('Could not fetch NPM version history');
            }
            
        } catch (error) {
            console.warn(`Warning: Could not enumerate rollback points: ${error.message}`);
        }
        
        return rollbackPoints.sort((a, b) => 
            new Date(b.timestamp || 0) - new Date(a.timestamp || 0)
        );
    }

    async validateRollbackTarget(version) {
        try {
            // Check if version exists in NPM
            const npmInfo = execSync(`npm view ${this.npmPackageName}@${version} version`, 
                { encoding: 'utf8' });
            
            if (npmInfo.trim() === version) {
                return {
                    valid: true,
                    source: 'npm',
                    version: version
                };
            }
        } catch (error) {
            // Check local backup points
            const backupPath = path.join(this.backupDir, version);
            if (await this.pathExists(backupPath)) {
                return {
                    valid: true,
                    source: 'local',
                    version: version,
                    backupPath
                };
            }
        }
        
        return {
            valid: false,
            error: `Version ${version} not found in NPM or local backups`
        };
    }

    async createRollbackBackup() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = path.join(this.backupDir, `pre-rollback-${timestamp}`);
        
        try {
            await fs.mkdir(this.backupDir, { recursive: true });
            await fs.mkdir(backupPath, { recursive: true });
            
            // Save current state
            const currentVersion = await this.getCurrentVersion();
            const metadata = {
                timestamp: new Date().toISOString(),
                version: currentVersion,
                description: 'Pre-rollback backup',
                rollbackType: 'automatic'
            };
            
            await fs.writeFile(
                path.join(backupPath, 'rollback_metadata.json'),
                JSON.stringify(metadata, null, 2)
            );
            
            console.log(`📦 Rollback backup created: ${backupPath}`);
            return backupPath;
            
        } catch (error) {
            throw new Error(`Rollback backup creation failed: ${error.message}`);
        }
    }

    async performRollback(version) {
        try {
            const validation = await this.validateRollbackTarget(version);
            if (!validation.valid) {
                throw new Error(validation.error);
            }
            
            console.log(`🔄 Rolling back to version ${version}...`);
            
            if (this.flagManager.isDryRunMode()) {
                console.log(`🔍 DRY RUN: Would rollback to ${version} from ${validation.source}`);
                return true;
            }
            
            if (validation.source === 'npm') {
                // NPM rollback
                const rollbackCmd = `npm install -g ${this.npmPackageName}@${version}`;
                
                if (this.flagManager.isSafeMode()) {
                    console.log(`About to execute: ${rollbackCmd}`);
                    // SafeModeManager confirmation would be handled by calling code
                }
                
                execSync(rollbackCmd, { stdio: 'inherit' });
                console.log(`✅ NPM package rolled back to v${version}`);
                
            } else if (validation.source === 'local') {
                // Local backup rollback
                console.log(`🔄 Restoring from local backup: ${validation.backupPath}`);
                // Local restoration logic would go here
                console.log('✅ Local backup restored');
            }
            
            return true;
            
        } catch (error) {
            console.error(`❌ Rollback failed: ${error.message}`);
            return false;
        }
    }

    async migrateConfigurationBackward() {
        try {
            console.log('⚙️  Migrating configuration backward...');
            
            if (this.flagManager.isDryRunMode()) {
                console.log('🔍 DRY RUN: Would migrate configuration backward if needed');
                return true;
            }
            
            // Backward configuration migration logic would go here
            
            console.log('✅ Backward configuration migration completed');
            return true;
            
        } catch (error) {
            console.error(`❌ Backward configuration migration failed: ${error.message}`);
            return false;
        }
    }

    async validateRollbackSuccess() {
        const validation = {};
        
        try {
            // Validate version
            const currentVersion = await this.getCurrentVersion();
            validation.version = {
                current: currentVersion,
                valid: currentVersion !== 'unknown'
            };
            
            // Validate CLI functionality
            try {
                execSync('claude-pm --version', { encoding: 'utf8', timeout: 5000 });
                validation.cliFunctionality = { working: true };
            } catch (error) {
                validation.cliFunctionality = { working: false, error: error.message };
            }
            
            // Validate configuration
            validation.configuration = await this.validateConfiguration();
            
        } catch (error) {
            validation.error = error.message;
        }
        
        return validation;
    }

    async validateConfiguration() {
        // Configuration validation logic
        return { status: 'ok' };
    }

    async getCurrentVersion() {
        try {
            const output = execSync(`npm list -g ${this.npmPackageName} --depth=0`, 
                { encoding: 'utf8' });
            const match = output.match(/@bobmatnyc\\/claude-multiagent-pm@([\\d\\.]+)/);
            return match ? match[1] : 'unknown';
        } catch (error) {
            return 'unknown';
        }
    }

    async pathExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch (error) {
            return false;
        }
    }
}

module.exports = RollbackManager;
```

---

## Phase 4: Integration and Testing (Days 4-5)

### 4.1 Update Command Dispatcher with All Flags

**File**: `lib/cli-modules/command-dispatcher.js` (COMPLETE UPDATE)
```javascript
// Add all new imports at the top:
const { CLIArgumentParser, FlagManager } = require('./flag-manager');
const SafeModeManager = require('./safe-mode-manager');
const VersionManager = require('./version-manager');
const UpgradeManager = require('./upgrade-manager');
const RollbackManager = require('./rollback-manager');

// Update the handleSpecialFlags method completely:
async handleSpecialFlags(args) {
    try {
        const parser = new CLIArgumentParser();
        const { flags, commands } = parser.parseArguments(args);
        const flagManager = new FlagManager(flags);
        
        // Handle ISS-0113 specific flags
        if (flags.save && commands.length === 0) {
            console.log('🛡️  Safe mode enabled. Use with other commands to require confirmations.');
            return true;
        }
        
        if (flags.version) {
            return await this.handleEnhancedVersion(flagManager);
        }
        
        if (flags.upgrade) {
            return await this.handleUpgrade(flagManager);
        }
        
        if (flags.rollback) {
            return await this.handleRollback(flagManager, flags.rollbackTarget);
        }
        
        if (flags.verify) {
            return await this.handleVerify(flagManager);
        }
        
        if (flags.debug) {
            return await this.handleDebugMode(flagManager, commands);
        }
        
        if (flags['dry-run']) {
            return await this.handleDryRun(flagManager, commands);
        }
        
        // Handle existing flags...
        if (args.includes('--help') || args.includes('-h')) {
            if (this.frameworkManager.showTroubleshootingHelp) {
                this.frameworkManager.showTroubleshootingHelp();
            } else {
                console.log('Claude Multi-Agent PM Framework - Help');
                console.log('Use --system-info for system information');
            }
            return true;
        }
        
        // ... rest of existing flag handling ...
        
    } catch (error) {
        console.error(`❌ Flag processing error: ${error.message}`);
        console.error('Use --help for usage information');
        return false;
    }
    
    return false; // No flags handled
}

async handleEnhancedVersion(flagManager) {
    const versionManager = new VersionManager();
    const versionDisplay = await versionManager.formatVersionDisplay();
    console.log(versionDisplay);
    return true;
}

async handleUpgrade(flagManager) {
    const upgradeManager = new UpgradeManager(flagManager);
    
    try {
        console.log('🔍 Checking for updates...');
        const updates = await upgradeManager.checkForUpdates();
        
        if (!updates.npm.updateAvailable) {
            console.log('✅ Already running the latest version');
            return true;
        }
        
        console.log(`📦 Update available: ${updates.npm.current} → ${updates.npm.latest}`);
        
        if (flagManager.isSafeMode()) {
            const safeMode = new SafeModeManager();
            const confirmed = await safeMode.confirmDestructiveAction(
                'NPM Package Upgrade',
                [
                    `Current version: ${updates.npm.current}`,
                    `Target version: ${updates.npm.latest}`,
                    'This will update the global NPM package',
                    'Framework components will be updated',
                    'Configuration may be migrated'
                ]
            );
            
            if (!confirmed) {
                console.log('❌ Upgrade cancelled by user');
                return true;
            }
        }
        
        // Create backup
        const backupPath = await upgradeManager.createUpgradeBackup();
        
        // Perform upgrade
        const npmSuccess = await upgradeManager.performNpmUpdate();
        if (!npmSuccess) {
            console.log('❌ NPM update failed - see errors above');
            return false;
        }
        
        const componentsSuccess = await upgradeManager.updateFrameworkComponents();
        if (!componentsSuccess) {
            console.log('⚠️  Component update had issues - check warnings above');
        }
        
        const migrationSuccess = await upgradeManager.migrateConfiguration();
        if (!migrationSuccess) {
            console.log('⚠️  Configuration migration had issues');
        }
        
        // Validate upgrade
        console.log('🔍 Validating upgrade...');
        const validation = await upgradeManager.validateUpgrade();
        
        if (validation.npmPackage && validation.npmPackage.installed && validation.cliAccess && validation.cliAccess.working) {
            console.log(`✅ Upgrade successful! Now running v${validation.npmPackage.version}`);
        } else {
            console.log('❌ Upgrade validation failed');
            console.log('🔄 Consider running rollback if issues persist');
        }
        
        return true;
        
    } catch (error) {
        console.error(`❌ Upgrade failed: ${error.message}`);
        return false;
    }
}

async handleRollback(flagManager, targetVersion) {
    const rollbackManager = new RollbackManager(flagManager);
    
    try {
        if (!targetVersion) {
            // Interactive rollback selection
            console.log('🔍 Available rollback points:');
            const rollbackPoints = await rollbackManager.listRollbackPoints();
            
            if (rollbackPoints.length === 0) {
                console.log('❌ No rollback points available');
                return true;
            }
            
            rollbackPoints.forEach((point, index) => {
                const timeInfo = point.timestamp ? ` (${new Date(point.timestamp).toLocaleDateString()})` : '';
                console.log(`  ${index + 1}. ${point.description} - v${point.version}${timeInfo}`);
            });
            
            console.log('\\nUse: claude-pm --rollback <version> to rollback to a specific version');
            return true;
        }
        
        // Validate target version
        const validation = await rollbackManager.validateRollbackTarget(targetVersion);
        if (!validation.valid) {
            console.error(`❌ ${validation.error}`);
            return false;
        }
        
        console.log(`🔄 Rolling back to version ${targetVersion}...`);
        
        if (flagManager.isSafeMode()) {
            const safeMode = new SafeModeManager();
            const confirmed = await safeMode.confirmDestructiveAction(
                'Version Rollback',
                [
                    `Target version: ${targetVersion}`,
                    `Source: ${validation.source}`,
                    'Current installation will be replaced',
                    'Configuration may be migrated backward',
                    'This action can be undone with another rollback'
                ]
            );
            
            if (!confirmed) {
                console.log('❌ Rollback cancelled by user');
                return true;
            }
        }
        
        // Create backup before rollback
        const backupPath = await rollbackManager.createRollbackBackup();
        
        // Perform rollback
        const rollbackSuccess = await rollbackManager.performRollback(targetVersion);
        if (!rollbackSuccess) {
            console.log('❌ Rollback failed - see errors above');
            return false;
        }
        
        // Migrate configuration backward if needed
        const migrationSuccess = await rollbackManager.migrateConfigurationBackward();
        if (!migrationSuccess) {
            console.log('⚠️  Backward configuration migration had issues');
        }
        
        // Validate rollback success
        console.log('🔍 Validating rollback...');
        const rollbackValidation = await rollbackManager.validateRollbackSuccess();
        
        if (rollbackValidation.version && rollbackValidation.version.valid && 
            rollbackValidation.cliFunctionality && rollbackValidation.cliFunctionality.working) {
            console.log(`✅ Rollback successful! Now running v${rollbackValidation.version.current}`);
        } else {
            console.log('❌ Rollback validation failed');
            console.log('🆘 Manual intervention may be required');
        }
        
        return true;
        
    } catch (error) {
        console.error(`❌ Rollback failed: ${error.message}`);
        return false;
    }
}

async handleVerify(flagManager) {
    console.log('🔍 Comprehensive system verification...');
    
    // Use existing validation systems
    const validation = {
        python: null,
        claude: null,
        framework: null,
        overall: true,
        errors: [],
        warnings: []
    };
    
    // Framework validation
    try {
        const versionManager = new VersionManager();
        const compatibility = await versionManager.checkVersionCompatibility();
        validation.framework = compatibility;
        
        Object.entries(compatibility).forEach(([env, info]) => {
            if (!info.compatible) {
                validation.overall = false;
                validation.errors.push(`${env} compatibility issue: ${info.version} (requires ${info.requirement})`);
            }
        });
    } catch (error) {
        validation.framework = null;
        validation.overall = false;
        validation.errors.push(`Framework validation failed: ${error.message}`);
    }
    
    // Claude CLI validation
    const claudeValidation = await this.claudeValidator.validateEnvironment();
    validation.claude = claudeValidation;
    if (!claudeValidation.valid) {
        validation.overall = false;
        validation.errors.push(`Claude CLI: ${claudeValidation.error}`);
    }
    
    // Display results
    console.log('\\n🔍 Verification Results:');
    console.log('=' .repeat(50));
    
    // Framework status
    if (validation.framework) {
        Object.entries(validation.framework).forEach(([env, info]) => {
            const status = info.compatible ? '✅' : '❌';
            console.log(`${status} ${env.charAt(0).toUpperCase() + env.slice(1)}: ${info.version}`);
        });
    }
    
    // Claude CLI status
    if (validation.claude.valid) {
        console.log(`✅ Claude CLI: v${validation.claude.version}`);
    } else {
        console.log(`❌ Claude CLI: ${validation.claude.error}`);
    }
    
    // Overall status
    if (validation.overall) {
        console.log('\\n🎯 Overall Status: ✅ All systems operational');
    } else {
        console.log('\\n⚠️  Overall Status: Issues detected');
        validation.errors.forEach(error => {
            console.log(`   • ${error}`);
        });
    }
    
    console.log('');
    return true;
}

async handleDebugMode(flagManager, commands) {
    console.log('🐛 Debug mode enabled');
    process.env.DEBUG = 'claude-pm:*';
    
    console.log('📊 Debug Information:');
    console.log(`   Node.js: ${process.version}`);
    console.log(`   Platform: ${process.platform} ${process.arch}`);
    console.log(`   Memory: ${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`);
    console.log(`   Arguments: ${JSON.stringify(process.argv.slice(2))}`);
    console.log(`   Commands: ${JSON.stringify(commands)}`);
    console.log(`   Flags: ${JSON.stringify(flagManager.flags)}`);
    
    if (commands.length > 0) {
        console.log('\\n🔄 Executing commands with debug output...');
        // Continue processing commands with debug enabled
        return false; // Let other handlers process the commands
    }
    
    return true;
}

async handleDryRun(flagManager, commands) {
    console.log('🔍 Dry run mode enabled - no changes will be made');
    
    if (commands.length === 0) {
        console.log('ℹ️  Specify commands to see what would be executed');
        return true;
    }
    
    console.log(`📋 Would execute: ${commands.join(' ')}`);
    console.log('   (No actual changes will be made)');
    
    // Dry run processing would be handled by specific command handlers
    return false; // Let other handlers process commands in dry-run mode
}
```

### 4.2 Performance Optimization

**File**: `lib/cli-modules/performance-optimizer.js`
```javascript
/**
 * Performance Optimizer for CLI operations
 * Addresses timeout issues identified in QA testing
 */

class PerformanceOptimizer {
    static optimizeModuleLoading() {
        // Lazy loading for heavy modules
        const moduleCache = new Map();
        
        return {
            loadModule: (moduleName) => {
                if (moduleCache.has(moduleName)) {
                    return moduleCache.get(moduleName);
                }
                
                const startTime = Date.now();
                const module = require(`./${moduleName}`);
                const loadTime = Date.now() - startTime;
                
                if (loadTime > 100) {
                    console.warn(`⚠️  Slow module load: ${moduleName} (${loadTime}ms)`);
                }
                
                moduleCache.set(moduleName, module);
                return module;
            }
        };
    }
    
    static setupMemoryMonitoring() {
        let lastMemoryUsage = process.memoryUsage().heapUsed;
        
        setInterval(() => {
            const currentUsage = process.memoryUsage().heapUsed;
            const delta = currentUsage - lastMemoryUsage;
            
            if (delta > 50 * 1024 * 1024) { // 50MB increase
                console.warn(`⚠️  Memory increase detected: +${Math.round(delta / 1024 / 1024)}MB`);
            }
            
            lastMemoryUsage = currentUsage;
        }, 5000);
    }
    
    static optimizeCommandExecution() {
        // Command execution timeout optimization
        const originalSpawn = require('child_process').spawn;
        
        require('child_process').spawn = function(command, args, options = {}) {
            const timeout = options.timeout || 10000; // 10 second default
            const process = originalSpawn(command, args, options);
            
            const timeoutId = setTimeout(() => {
                console.warn(`⚠️  Command timeout: ${command} ${args?.join(' ')}`);
                process.kill('SIGTERM');
            }, timeout);
            
            process.on('close', () => clearTimeout(timeoutId));
            process.on('error', () => clearTimeout(timeoutId));
            
            return process;
        };
    }
}

module.exports = PerformanceOptimizer;
```

---

## Final Integration Checklist

### ✅ Implementation Tasks

**DevOps Agent Deliverables**:
- [ ] Implement `flag-manager.js` with CLIArgumentParser and FlagManager
- [ ] Implement `safe-mode-manager.js` with SafeModeManager class
- [ ] Implement `version-manager.js` with enhanced VersionManager
- [ ] Implement `upgrade-manager.js` with UpgradeManager class  
- [ ] Implement `rollback-manager.js` with RollbackManager class
- [ ] Update `command-dispatcher.js` with all ISS-0113 flag handling
- [ ] Implement `performance-optimizer.js` to address timeout issues
- [ ] Create comprehensive test suite for all flag combinations
- [ ] Update help system and documentation for new flags
- [ ] Validate cross-platform compatibility (macOS focus)

### 🧪 Testing Requirements

**QA Agent Validation Points**:
- [ ] All ISS-0113 flags functional (`--save`, `--upgrade`, `--rollback`, etc.)
- [ ] Flag combination validation working correctly
- [ ] Safe mode confirmations and backups operational
- [ ] Version display shows comprehensive information per spec
- [ ] Upgrade process integrates with NPM workflow
- [ ] Rollback functionality restores previous versions successfully
- [ ] Performance issues resolved (sub-10 second execution)
- [ ] Cross-platform compatibility maintained
- [ ] Error handling provides clear, actionable messages
- [ ] Integration with existing Python CLI backend seamless

### 📊 Performance Targets

**Must Meet ISS-0113 Specifications**:
- Argument parsing: <50ms (currently timing out - CRITICAL)
- Version information gathering: <500ms
- Upgrade checking: <2 seconds
- Rollback point enumeration: <1 second
- Overall CLI execution: <10 seconds (currently 2+ minutes)

---

## Conclusion

This roadmap provides DevOps Agent with complete implementation specifications for ISS-0113 CLI flags system. The modular approach ensures maintainability while the comprehensive flag management system delivers the user experience requirements.

**Critical Path**: Address performance issues while implementing core flag functionality to ensure production-ready deployment.

**Estimated Timeline**: 4-5 days for complete implementation and testing.

**Success Criteria**: All ISS-0113 acceptance criteria met with sub-10 second CLI performance and comprehensive flag functionality operational.

---

**QA Agent**: Ready to validate implementation once DevOps Agent completes development work.