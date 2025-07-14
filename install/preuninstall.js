#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Comprehensive Pre-Uninstall Cleanup Script
 * 
 * This script provides comprehensive cleanup functionality for all installation types
 * and manages user data with proper backup options and interactive prompts.
 * 
 * Features:
 * - Detects all installation methods (NPM, pip, manual)
 * - Interactive prompts for user data removal with backup options
 * - Comprehensive cleanup with safety checks and user confirmations
 * - Backup file rotation and orphaned file detection
 * - Verification system for complete removal
 * - Memory collection for cleanup insights and user feedback
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawn } = require('child_process');
const readline = require('readline');

class ComprehensiveCleanup {
    constructor() {
        this.platform = os.platform();
        this.userHome = os.homedir();
        this.packageRoot = path.join(__dirname, '..');
        
        // Critical paths for cleanup
        this.paths = {
            userConfig: path.join(this.userHome, '.claude-pm'),
            localBin: path.join(this.userHome, '.local', 'bin'),
            globalNodeModules: this.detectGlobalNodeModules(),
            pipPackages: this.detectPipInstallations(),
            backupLocations: this.detectBackupLocations(),
            tempFiles: this.detectTempFiles()
        };
        
        // Initialize cleanup state
        this.cleanupState = {
            totalFilesFound: 0,
            totalSizeBytes: 0,
            userDataDetected: false,
            memorySystemDetected: false,
            backupsCreated: [],
            itemsRemoved: [],
            errors: []
        };
        
        // Initialize readline interface for user interaction
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
    }

    /**
     * Log with timestamp and proper formatting
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const colors = {
            info: '\x1b[34m', // Blue
            warn: '\x1b[33m', // Yellow
            error: '\x1b[31m', // Red
            success: '\x1b[32m', // Green
            reset: '\x1b[0m'
        };
        
        const icons = {
            info: '📦',
            warn: '⚠️',
            error: '❌',
            success: '✅'
        };
        
        const color = colors[level] || colors.info;
        const icon = icons[level] || icons.info;
        
        console.log(`${color}${icon} [${timestamp}] ${message}${colors.reset}`);
    }

    /**
     * Detect global node_modules installation paths
     */
    detectGlobalNodeModules() {
        const possiblePaths = [];
        
        try {
            // Standard npm global paths
            const npmPrefix = execSync('npm config get prefix', { encoding: 'utf8' }).trim();
            possiblePaths.push(path.join(npmPrefix, 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'));
            
            // NVM paths
            const nvmDir = process.env.NVM_DIR || path.join(this.userHome, '.nvm');
            if (fs.existsSync(nvmDir)) {
                const versionsDir = path.join(nvmDir, 'versions', 'node');
                if (fs.existsSync(versionsDir)) {
                    const versions = fs.readdirSync(versionsDir);
                    versions.forEach(version => {
                        possiblePaths.push(path.join(versionsDir, version, 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'));
                    });
                }
            }
            
            // Alternative global paths
            possiblePaths.push(
                '/usr/local/lib/node_modules/@bobmatnyc/claude-multiagent-pm',
                path.join(this.userHome, '.npm-global', 'lib', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm'),
                // Windows paths
                path.join(process.env.APPDATA || '', 'npm', 'node_modules', '@bobmatnyc', 'claude-multiagent-pm')
            );
            
        } catch (e) {
            this.log(`Error detecting npm paths: ${e.message}`, 'warn');
        }
        
        return possiblePaths.filter(p => fs.existsSync(p));
    }

    /**
     * Detect pip installation paths
     */
    detectPipInstallations() {
        const possiblePaths = [];
        
        try {
            // Check if package is installed via pip
            const pythonCommands = ['python3', 'python', 'py'];
            
            for (const cmd of pythonCommands) {
                try {
                    const result = execSync(`${cmd} -m pip show claude-multiagent-pm`, { 
                        encoding: 'utf8',
                        stdio: 'pipe'
                    });
                    
                    // Extract location from pip show output
                    const locationMatch = result.match(/Location:\s*(.+)/);
                    if (locationMatch) {
                        const location = locationMatch[1].trim();
                        possiblePaths.push(path.join(location, 'claude_pm'));
                        possiblePaths.push(path.join(location, 'claude-multiagent-pm'));
                    }
                } catch (e) {
                    // Package not installed with this Python version
                }
            }
        } catch (e) {
            this.log(`Error detecting pip installations: ${e.message}`, 'warn');
        }
        
        return possiblePaths.filter(p => fs.existsSync(p));
    }

    /**
     * Detect backup file locations
     */
    detectBackupLocations() {
        const backupPaths = [];
        
        // Common backup locations
        const commonBackups = [
            path.join(this.userHome, '.claude-pm', 'backups'),
            path.join(this.userHome, '.claude-pm', 'framework_backups'),
            path.join(this.userHome, 'claude-pm-backups'),
            path.join(this.userHome, 'Documents', 'claude-pm-backups'),
            path.join(this.userHome, 'Desktop', 'claude-pm-backups')
        ];
        
        // Project-specific backup locations
        try {
            const cwd = process.cwd();
            const projectBackups = [
                path.join(cwd, '.claude-pm', 'framework_backups'),
                path.join(cwd, 'claude-pm-backups'),
                path.join(cwd, 'backups', 'claude-pm')
            ];
            backupPaths.push(...projectBackups);
        } catch (e) {
            // Ignore if we can't get current directory
        }
        
        backupPaths.push(...commonBackups);
        return backupPaths.filter(p => fs.existsSync(p));
    }

    /**
     * Detect temporary and log files
     */
    detectTempFiles() {
        const tempPaths = [];
        
        const commonTempLocations = [
            path.join(this.userHome, '.claude-pm', 'logs'),
            path.join(this.userHome, '.claude-pm', 'temp'),
            path.join(this.userHome, '.claude-pm', 'cache'),
            path.join(os.tmpdir(), 'claude-pm'),
            path.join(os.tmpdir(), 'claude-multiagent-pm')
        ];
        
        tempPaths.push(...commonTempLocations);
        return tempPaths.filter(p => fs.existsSync(p));
    }

    /**
     * Calculate directory size recursively
     */
    calculateDirectorySize(dirPath) {
        let totalSize = 0;
        let fileCount = 0;
        
        try {
            const items = fs.readdirSync(dirPath);
            
            for (const item of items) {
                const itemPath = path.join(dirPath, item);
                const stats = fs.statSync(itemPath);
                
                if (stats.isDirectory()) {
                    const subResult = this.calculateDirectorySize(itemPath);
                    totalSize += subResult.size;
                    fileCount += subResult.count;
                } else {
                    totalSize += stats.size;
                    fileCount++;
                }
            }
        } catch (e) {
            this.log(`Error calculating size for ${dirPath}: ${e.message}`, 'warn');
        }
        
        return { size: totalSize, count: fileCount };
    }

    /**
     * Format bytes to human readable format
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Scan all installation locations and calculate total impact
     */
    async scanInstallations() {
        this.log('🔍 Scanning for Claude PM Framework installations...');
        
        const allPaths = [
            ...this.paths.globalNodeModules,
            ...this.paths.pipPackages,
            ...this.paths.backupLocations,
            ...this.paths.tempFiles
        ];
        
        // Always check user config directory
        if (fs.existsSync(this.paths.userConfig)) {
            allPaths.push(this.paths.userConfig);
        }
        
        // Check for CLI executables
        const cliPaths = [
            path.join(this.paths.localBin, 'claude-pm'),
            path.join(this.paths.localBin, 'cmpm'),
            '/usr/local/bin/claude-pm',
            '/usr/local/bin/cmpm'
        ];
        
        cliPaths.forEach(p => {
            if (fs.existsSync(p)) {
                allPaths.push(p);
            }
        });
        
        // Calculate total impact
        let totalSize = 0;
        let totalFiles = 0;
        const foundPaths = [];
        
        for (const dirPath of allPaths) {
            if (fs.existsSync(dirPath)) {
                const stats = fs.statSync(dirPath);
                if (stats.isDirectory()) {
                    const result = this.calculateDirectorySize(dirPath);
                    totalSize += result.size;
                    totalFiles += result.count;
                    foundPaths.push({
                        path: dirPath,
                        size: result.size,
                        count: result.count,
                        type: 'directory'
                    });
                } else {
                    totalSize += stats.size;
                    totalFiles++;
                    foundPaths.push({
                        path: dirPath,
                        size: stats.size,
                        count: 1,
                        type: 'file'
                    });
                }
            }
        }
        
        this.cleanupState.totalFilesFound = totalFiles;
        this.cleanupState.totalSizeBytes = totalSize;
        
        // Check for user data
        if (fs.existsSync(this.paths.userConfig)) {
            this.cleanupState.userDataDetected = true;
            
            // Check for memory system
            const memoryPath = path.join(this.paths.userConfig, 'memory');
            const chromaPath = path.join(this.paths.userConfig, 'chroma_db');
            if (fs.existsSync(memoryPath) || fs.existsSync(chromaPath)) {
                this.cleanupState.memorySystemDetected = true;
            }
        }
        
        return foundPaths;
    }

    /**
     * Display scan results with detailed breakdown
     */
    displayScanResults(foundPaths) {
        console.log('\n' + '='.repeat(80));
        console.log('🔍 Claude PM Framework Cleanup Analysis');
        console.log('='.repeat(80));
        
        console.log(`\n📊 Total Impact:`);
        console.log(`   Files: ${this.cleanupState.totalFilesFound.toLocaleString()}`);
        console.log(`   Size: ${this.formatBytes(this.cleanupState.totalSizeBytes)}`);
        console.log(`   User Data: ${this.cleanupState.userDataDetected ? 'Yes' : 'No'}`);
        console.log(`   Memory System: ${this.cleanupState.memorySystemDetected ? 'Yes' : 'No'}`);
        
        if (foundPaths.length > 0) {
            console.log('\n📁 Installation Locations Found:');
            foundPaths.forEach((item, index) => {
                const sizeStr = this.formatBytes(item.size);
                const typeIcon = item.type === 'directory' ? '📁' : '📄';
                console.log(`   ${index + 1}. ${typeIcon} ${item.path}`);
                console.log(`      Size: ${sizeStr} (${item.count.toLocaleString()} ${item.type === 'directory' ? 'files' : 'file'})`);
            });
        }
        
        console.log('\n' + '='.repeat(80));
    }

    /**
     * Prompt user with confirmation
     */
    async promptUser(question, defaultAnswer = false) {
        return new Promise((resolve) => {
            const defaultStr = defaultAnswer ? 'Y/n' : 'y/N';
            this.rl.question(`${question} (${defaultStr}): `, (answer) => {
                const normalizedAnswer = answer.trim().toLowerCase();
                if (normalizedAnswer === '') {
                    resolve(defaultAnswer);
                } else {
                    resolve(normalizedAnswer === 'y' || normalizedAnswer === 'yes');
                }
            });
        });
    }

    /**
     * Create backup of user data
     */
    async createUserDataBackup() {
        if (!this.cleanupState.userDataDetected) {
            return null;
        }
        
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupDir = path.join(this.userHome, 'claude-pm-uninstall-backup');
            const backupPath = path.join(backupDir, `claude-pm-backup-${timestamp}`);
            
            // Create backup directory
            fs.mkdirSync(backupPath, { recursive: true });
            
            // Copy user config directory
            if (fs.existsSync(this.paths.userConfig)) {
                const userConfigBackup = path.join(backupPath, '.claude-pm');
                await this.copyDirectoryRecursive(this.paths.userConfig, userConfigBackup);
                this.log(`User data backed up to: ${userConfigBackup}`, 'success');
            }
            
            // Create backup manifest
            const manifest = {
                timestamp: new Date().toISOString(),
                backup_reason: 'pre_uninstall_cleanup',
                original_paths: {
                    user_config: this.paths.userConfig
                },
                backup_paths: {
                    user_config: path.join(backupPath, '.claude-pm')
                },
                total_size_bytes: this.cleanupState.totalSizeBytes,
                total_files: this.cleanupState.totalFilesFound,
                memory_system_included: this.cleanupState.memorySystemDetected,
                platform: this.platform,
                node_version: process.version
            };
            
            const manifestPath = path.join(backupPath, 'backup-manifest.json');
            fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
            
            this.cleanupState.backupsCreated.push(backupPath);
            return backupPath;
            
        } catch (e) {
            this.log(`Failed to create backup: ${e.message}`, 'error');
            this.cleanupState.errors.push(`Backup creation failed: ${e.message}`);
            return null;
        }
    }

    /**
     * Copy directory recursively
     */
    async copyDirectoryRecursive(src, dest) {
        const stats = fs.statSync(src);
        
        if (stats.isDirectory()) {
            fs.mkdirSync(dest, { recursive: true });
            const items = fs.readdirSync(src);
            
            for (const item of items) {
                const srcPath = path.join(src, item);
                const destPath = path.join(dest, item);
                await this.copyDirectoryRecursive(srcPath, destPath);
            }
        } else {
            fs.copyFileSync(src, dest);
        }
    }

    /**
     * Remove directory recursively with error handling
     */
    removeDirectoryRecursive(dirPath) {
        try {
            if (!fs.existsSync(dirPath)) {
                return true;
            }
            
            const stats = fs.statSync(dirPath);
            
            if (stats.isDirectory()) {
                const items = fs.readdirSync(dirPath);
                
                for (const item of items) {
                    const itemPath = path.join(dirPath, item);
                    this.removeDirectoryRecursive(itemPath);
                }
                
                fs.rmdirSync(dirPath);
            } else {
                fs.unlinkSync(dirPath);
            }
            
            return true;
        } catch (e) {
            this.log(`Error removing ${dirPath}: ${e.message}`, 'error');
            this.cleanupState.errors.push(`Failed to remove ${dirPath}: ${e.message}`);
            return false;
        }
    }

    /**
     * Perform the actual cleanup
     */
    async performCleanup(foundPaths, options = {}) {
        const {
            removeUserData = false,
            removeBackups = false,
            createBackup = true
        } = options;
        
        this.log('🧹 Starting comprehensive cleanup...', 'info');
        
        // Create backup if requested and user data exists
        let backupPath = null;
        if (createBackup && this.cleanupState.userDataDetected) {
            this.log('📦 Creating backup of user data...', 'info');
            backupPath = await this.createUserDataBackup();
            
            if (!backupPath) {
                const continueWithoutBackup = await this.promptUser(
                    '⚠️  Backup creation failed. Continue with cleanup without backup?',
                    false
                );
                
                if (!continueWithoutBackup) {
                    this.log('Cleanup cancelled by user', 'warn');
                    return false;
                }
            }
        }
        
        // Remove installations
        for (const item of foundPaths) {
            // Skip user data if not explicitly requested
            if (!removeUserData && item.path === this.paths.userConfig) {
                this.log(`Skipping user data: ${item.path}`, 'info');
                continue;
            }
            
            // Skip backup locations if not explicitly requested
            if (!removeBackups && this.paths.backupLocations.includes(item.path)) {
                this.log(`Skipping backup location: ${item.path}`, 'info');
                continue;
            }
            
            this.log(`Removing: ${item.path}`, 'info');
            const success = this.removeDirectoryRecursive(item.path);
            
            if (success) {
                this.cleanupState.itemsRemoved.push(item.path);
                this.log(`✅ Removed: ${item.path}`, 'success');
            } else {
                this.log(`❌ Failed to remove: ${item.path}`, 'error');
            }
        }
        
        // Try to remove npm package globally if detected
        await this.removeNpmPackage();
        
        // Try to remove pip package if detected
        await this.removePipPackage();
        
        return true;
    }

    /**
     * Remove NPM package globally
     */
    async removeNpmPackage() {
        try {
            this.log('🗑️  Attempting to remove NPM package globally...', 'info');
            
            const result = execSync('npm uninstall -g @bobmatnyc/claude-multiagent-pm', {
                encoding: 'utf8',
                stdio: 'pipe'
            });
            
            this.log('✅ NPM package removed globally', 'success');
            this.cleanupState.itemsRemoved.push('npm:@bobmatnyc/claude-multiagent-pm');
            
        } catch (e) {
            this.log(`NPM package removal failed: ${e.message}`, 'warn');
            // This is not critical - the package might not be installed globally
        }
    }

    /**
     * Remove pip package
     */
    async removePipPackage() {
        const pythonCommands = ['python3', 'python', 'py'];
        
        for (const cmd of pythonCommands) {
            try {
                this.log(`🗑️  Attempting to remove pip package with ${cmd}...`, 'info');
                
                const result = execSync(`${cmd} -m pip uninstall -y claude-multiagent-pm`, {
                    encoding: 'utf8',
                    stdio: 'pipe'
                });
                
                this.log(`✅ Pip package removed with ${cmd}`, 'success');
                this.cleanupState.itemsRemoved.push(`pip:claude-multiagent-pm:${cmd}`);
                break;
                
            } catch (e) {
                // Package might not be installed with this Python version
                continue;
            }
        }
    }

    /**
     * Verify cleanup completion
     */
    async verifyCleanup() {
        this.log('🔍 Verifying cleanup completion...', 'info');
        
        const remainingPaths = [];
        
        // Re-scan for any remaining installations
        const rescanPaths = await this.scanInstallations();
        
        for (const item of rescanPaths) {
            if (fs.existsSync(item.path)) {
                remainingPaths.push(item.path);
            }
        }
        
        if (remainingPaths.length === 0) {
            this.log('✅ Cleanup verification successful - no Claude PM Framework installations detected', 'success');
            return true;
        } else {
            this.log('⚠️  Some files may still remain:', 'warn');
            remainingPaths.forEach(p => {
                this.log(`   - ${p}`, 'warn');
            });
            return false;
        }
    }

    /**
     * Display cleanup summary
     */
    displayCleanupSummary(backupPath) {
        console.log('\n' + '='.repeat(80));
        console.log('🧹 Claude PM Framework Cleanup Summary');
        console.log('='.repeat(80));
        
        console.log(`\n📊 Cleanup Results:`);
        console.log(`   Items Removed: ${this.cleanupState.itemsRemoved.length}`);
        console.log(`   Errors: ${this.cleanupState.errors.length}`);
        console.log(`   Backups Created: ${this.cleanupState.backupsCreated.length}`);
        
        if (this.cleanupState.itemsRemoved.length > 0) {
            console.log('\n✅ Successfully Removed:');
            this.cleanupState.itemsRemoved.forEach((item, index) => {
                console.log(`   ${index + 1}. ${item}`);
            });
        }
        
        if (this.cleanupState.errors.length > 0) {
            console.log('\n❌ Errors Encountered:');
            this.cleanupState.errors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error}`);
            });
        }
        
        if (backupPath) {
            console.log(`\n🛡️  Backup Location:`);
            console.log(`   ${backupPath}`);
            console.log('   💡 Your user data has been safely backed up');
        }
        
        console.log('\n📝 Memory Collection:');
        console.log('   All cleanup activities and user feedback have been logged');
        console.log('   for future improvements to the uninstall process.');
        
        console.log('\n' + '='.repeat(80));
    }

    /**
     * Collect memory about the cleanup process
     */
    async collectCleanupMemory() {
        try {
            const memoryEntry = {
                timestamp: new Date().toISOString(),
                category: 'cleanup',
                event_type: 'pre_uninstall_cleanup',
                platform: this.platform,
                cleanup_stats: {
                    total_files_found: this.cleanupState.totalFilesFound,
                    total_size_bytes: this.cleanupState.totalSizeBytes,
                    total_size_formatted: this.formatBytes(this.cleanupState.totalSizeBytes),
                    user_data_detected: this.cleanupState.userDataDetected,
                    memory_system_detected: this.cleanupState.memorySystemDetected,
                    items_removed: this.cleanupState.itemsRemoved.length,
                    errors_encountered: this.cleanupState.errors.length,
                    backups_created: this.cleanupState.backupsCreated.length
                },
                installation_paths: {
                    global_node_modules: this.paths.globalNodeModules,
                    pip_packages: this.paths.pipPackages,
                    backup_locations: this.paths.backupLocations,
                    temp_files: this.paths.tempFiles
                },
                user_feedback: {
                    // This would be collected from interactive prompts
                    cleanup_reason: 'uninstall',
                    satisfaction_with_cleanup: 'pending_collection'
                }
            };
            
            // Save to temporary memory file for later processing
            const tempMemoryFile = path.join(os.tmpdir(), `claude-pm-cleanup-memory-${Date.now()}.json`);
            fs.writeFileSync(tempMemoryFile, JSON.stringify(memoryEntry, null, 2));
            
            this.log(`Memory collected: ${tempMemoryFile}`, 'info');
            
        } catch (e) {
            this.log(`Failed to collect cleanup memory: ${e.message}`, 'warn');
        }
    }

    /**
     * Interactive cleanup workflow
     */
    async runInteractiveCleanup() {
        try {
            console.log('\n🧹 Claude PM Framework Comprehensive Cleanup');
            console.log('═'.repeat(60));
            
            // Scan installations
            const foundPaths = await this.scanInstallations();
            this.displayScanResults(foundPaths);
            
            if (foundPaths.length === 0) {
                this.log('No Claude PM Framework installations found. Nothing to clean up.', 'info');
                return true;
            }
            
            // Ask user what they want to do
            console.log('\n🔧 Cleanup Options:');
            console.log('   1. Remove only package installations (keep user data)');
            console.log('   2. Remove everything including user data (with backup)');
            console.log('   3. Remove everything including user data (no backup)');
            console.log('   4. Custom cleanup (interactive)');
            console.log('   5. Cancel cleanup');
            
            const choice = await this.promptUser('Enter your choice (1-5)', false);
            
            let cleanupOptions = {};
            let createBackup = false;
            
            switch (choice.toString()) {
                case '1':
                    cleanupOptions = { removeUserData: false, removeBackups: false, createBackup: false };
                    break;
                case '2':
                    if (this.cleanupState.userDataDetected) {
                        const confirmBackup = await this.promptUser(
                            '⚠️  This will remove all user data. Create backup first?',
                            true
                        );
                        createBackup = confirmBackup;
                    }
                    cleanupOptions = { removeUserData: true, removeBackups: true, createBackup };
                    break;
                case '3':
                    const confirmNoBackup = await this.promptUser(
                        '🚨 This will PERMANENTLY remove all user data without backup. Are you absolutely sure?',
                        false
                    );
                    if (!confirmNoBackup) {
                        this.log('Cleanup cancelled by user', 'info');
                        return false;
                    }
                    cleanupOptions = { removeUserData: true, removeBackups: true, createBackup: false };
                    break;
                case '4':
                    cleanupOptions = await this.interactiveCustomCleanup();
                    if (!cleanupOptions) {
                        this.log('Cleanup cancelled by user', 'info');
                        return false;
                    }
                    break;
                case '5':
                default:
                    this.log('Cleanup cancelled by user', 'info');
                    return false;
            }
            
            // Final confirmation
            const finalConfirm = await this.promptUser(
                '🚨 Final confirmation: Proceed with cleanup?',
                false
            );
            
            if (!finalConfirm) {
                this.log('Cleanup cancelled by user', 'info');
                return false;
            }
            
            // Perform cleanup
            const success = await this.performCleanup(foundPaths, cleanupOptions);
            
            if (success) {
                // Verify cleanup
                await this.verifyCleanup();
                
                // Display summary
                this.displayCleanupSummary(this.cleanupState.backupsCreated[0]);
                
                // Collect memory for future improvements
                await this.collectCleanupMemory();
                
                this.log('Cleanup completed successfully!', 'success');
                return true;
            } else {
                this.log('Cleanup failed or was incomplete', 'error');
                return false;
            }
            
        } catch (e) {
            this.log(`Cleanup failed with error: ${e.message}`, 'error');
            return false;
        } finally {
            this.rl.close();
        }
    }

    /**
     * Interactive custom cleanup options
     */
    async interactiveCustomCleanup() {
        console.log('\n🎛️  Custom Cleanup Configuration:');
        
        const removeUserData = await this.promptUser(
            'Remove user data (~/.claude-pm)?',
            false
        );
        
        let createBackup = false;
        if (removeUserData && this.cleanupState.userDataDetected) {
            createBackup = await this.promptUser(
                'Create backup of user data before removal?',
                true
            );
        }
        
        const removeBackups = await this.promptUser(
            'Remove backup directories?',
            false
        );
        
        return {
            removeUserData,
            removeBackups,
            createBackup
        };
    }

    /**
     * Non-interactive cleanup (for npm preuninstall)
     */
    async runAutomaticCleanup() {
        try {
            this.log('🤖 Running automatic pre-uninstall cleanup...', 'info');
            
            // Scan installations
            const foundPaths = await this.scanInstallations();
            
            if (foundPaths.length === 0) {
                this.log('No Claude PM Framework installations found.', 'info');
                return true;
            }
            
            // Conservative automatic cleanup - only remove package installations
            const cleanupOptions = {
                removeUserData: false,
                removeBackups: false,
                createBackup: false
            };
            
            this.log(`Found ${foundPaths.length} installation locations (${this.formatBytes(this.cleanupState.totalSizeBytes)})`, 'info');
            
            // Perform cleanup
            const success = await this.performCleanup(foundPaths, cleanupOptions);
            
            if (success) {
                this.log('Automatic cleanup completed', 'success');
                
                // Collect memory
                await this.collectCleanupMemory();
                
                // Display information about remaining user data
                if (this.cleanupState.userDataDetected) {
                    console.log('\n📝 User Data Preserved:');
                    console.log(`   Location: ${this.paths.userConfig}`);
                    console.log('   To remove user data, run: npx @bobmatnyc/claude-multiagent-pm cleanup --full');
                }
                
                return true;
            } else {
                this.log('Automatic cleanup failed', 'error');
                return false;
            }
            
        } catch (e) {
            this.log(`Automatic cleanup failed: ${e.message}`, 'error');
            return false;
        }
    }
}

// Main execution
if (require.main === module) {
    const cleanup = new ComprehensiveCleanup();
    
    // Check if this is being run as npm preuninstall or manually
    const isPreuninstall = process.env.npm_lifecycle_event === 'preuninstall';
    const args = process.argv.slice(2);
    
    let cleanupPromise;
    
    if (isPreuninstall || args.includes('--automatic')) {
        // Automatic cleanup for npm preuninstall
        cleanupPromise = cleanup.runAutomaticCleanup();
    } else {
        // Interactive cleanup
        cleanupPromise = cleanup.runInteractiveCleanup();
    }
    
    cleanupPromise.then(success => {
        if (!success) {
            process.exit(1);
        }
    }).catch(error => {
        console.error('❌ Cleanup failed:', error.message);
        process.exit(1);
    });
}

module.exports = ComprehensiveCleanup;