#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Windows Platform Installer
 * 
 * Windows-specific installation and configuration for the Claude PM Framework.
 * Handles Windows path conventions, registry settings, and service configuration.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class WindowsPlatformInstaller {
    constructor(options = {}) {
        this.targetDir = options.targetDir || process.cwd();
        this.verbose = options.verbose || false;
        this.createService = options.createService || false;
        
        this.appDataDir = path.join(process.env.APPDATA || '', 'claude-pm');
        this.programDataDir = path.join(process.env.PROGRAMDATA || 'C:\\ProgramData', 'claude-pm');
    }

    /**
     * Log with Windows-specific formatting
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        
        if (this.verbose || level !== 'info') {
            console.log(`${prefix} [${timestamp}] ${message}`);
        }
    }

    /**
     * Create Windows-specific directories
     */
    async createWindowsDirectories() {
        this.log('Creating Windows-specific directories...');
        
        const directories = [
            this.appDataDir,
            path.join(this.appDataDir, 'logs'),
            path.join(this.appDataDir, 'temp'),
            path.join(this.appDataDir, 'config')
        ];
        
        for (const dir of directories) {
            try {
                await fs.mkdir(dir, { recursive: true });
                this.log(`Created directory: ${dir}`);
            } catch (error) {
                this.log(`Failed to create directory ${dir}: ${error.message}`, 'error');
                throw error;
            }
        }
    }

    /**
     * Create Windows batch scripts
     */
    async createBatchScripts() {
        this.log('Creating Windows batch scripts...');
        
        const scriptsDir = path.join(this.targetDir, 'scripts');
        await fs.mkdir(scriptsDir, { recursive: true });
        
        // Main claude-pm.bat script
        const mainScript = `@echo off
setlocal enabledelayedexpansion

REM Claude Multi-Agent PM Framework - Windows Launcher
REM Automatically detects Python and launches the framework

echo Starting Claude PM Framework...

REM Check for Python 3
where python3 >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :run_framework
)

REM Check for Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    REM Verify it's Python 3
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        set VERSION=%%i
        for /f "tokens=1 delims=." %%j in ("!VERSION!") do (
            if %%j geq 3 (
                set PYTHON_CMD=python
                goto :run_framework
            )
        )
    )
)

echo Error: Python 3.8+ is required but not found
echo Please install Python from https://python.org
exit /b 1

:run_framework
echo Using !PYTHON_CMD!
cd /d "${this.targetDir.replace(/\//g, '\\')}"
!PYTHON_CMD! claude_pm\\cli.py %*
exit /b %errorlevel%`;
        
        await fs.writeFile(path.join(scriptsDir, 'claude-pm.bat'), mainScript);
        
        // Health check script
        const healthScript = `@echo off
echo Checking Claude PM Framework health...
cd /d "${this.targetDir.replace(/\//g, '\\')}"
call scripts\\claude-pm.bat health status
`;
        
        await fs.writeFile(path.join(scriptsDir, 'health-check.bat'), healthScript);
        
        // Service installer script (if requested)
        if (this.createService) {
            await this.createServiceScripts(scriptsDir);
        }
        
        this.log('Windows batch scripts created');
    }

    /**
     * Create Windows service scripts
     */
    async createServiceScripts(scriptsDir) {
        this.log('Creating Windows service scripts...');
        
        const serviceInstaller = `@echo off
REM Claude PM Framework - Windows Service Installer
REM Requires Administrator privileges

echo Installing Claude PM Framework as Windows Service...
echo This requires Administrator privileges.

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: This script must be run as Administrator
    pause
    exit /b 1
)

REM Install using NSSM (Non-Sucking Service Manager) if available
where nssm >nul 2>nul
if %errorlevel% equ 0 (
    echo Using NSSM to install service...
    nssm install "ClaudePMFramework" "${this.targetDir.replace(/\//g, '\\\\')}\\\\scripts\\\\claude-pm.bat"
    nssm set "ClaudePMFramework" DisplayName "Claude PM Framework"
    nssm set "ClaudePMFramework" Description "Claude Multi-Agent Project Management Framework"
    nssm set "ClaudePMFramework" Start SERVICE_AUTO_START
    nssm start "ClaudePMFramework"
    echo Service installed successfully
) else (
    echo NSSM not found. Please install NSSM or use Windows Task Scheduler
    echo Download NSSM from: https://nssm.cc/
)

pause`;
        
        await fs.writeFile(path.join(scriptsDir, 'install-service.bat'), serviceInstaller);
        
        const serviceUninstaller = `@echo off
REM Claude PM Framework - Windows Service Uninstaller
REM Requires Administrator privileges

echo Uninstalling Claude PM Framework Windows Service...

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: This script must be run as Administrator
    pause
    exit /b 1
)

REM Uninstall using NSSM
where nssm >nul 2>nul
if %errorlevel% equ 0 (
    nssm stop "ClaudePMFramework"
    nssm remove "ClaudePMFramework" confirm
    echo Service uninstalled successfully
) else (
    echo NSSM not found. Service may need manual removal
)

pause`;
        
        await fs.writeFile(path.join(scriptsDir, 'uninstall-service.bat'), serviceUninstaller);
    }

    /**
     * Create Windows configuration
     */
    async createWindowsConfig() {
        this.log('Creating Windows-specific configuration...');
        
        const config = {
            platform: 'windows',
            version: require('../../package.json').version,
            installDate: new Date().toISOString(),
            paths: {
                framework: this.targetDir,
                appData: this.appDataDir,
                logs: path.join(this.appDataDir, 'logs'),
                temp: path.join(this.appDataDir, 'temp'),
                scripts: path.join(this.targetDir, 'scripts')
            },
            windows: {
                pathSeparator: '\\\\',
                lineEnding: '\\r\\n',
                scriptExtension: '.bat',
                serviceSupport: this.createService
            },
            commands: {
                python: 'python3 || python',
                pip: 'python -m pip',
                launcher: path.join(this.targetDir, 'scripts', 'claude-pm.bat')
            }
        };
        
        const configPath = path.join(this.appDataDir, 'config', 'windows.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));
        
        this.log(`Windows configuration saved to: ${configPath}`);
    }

    /**
     * Set up Windows PATH integration
     */
    async setupPathIntegration() {
        this.log('Setting up Windows PATH integration...');
        
        try {
            // Create a PowerShell script to add to PATH
            const powershellScript = `
# Claude PM Framework - PATH Integration
$claudePMPath = "${this.targetDir.replace(/\//g, '\\\\')}"
$scriptsPath = "$claudePMPath\\\\scripts"

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

# Check if already in PATH
if ($currentPath -notlike "*$scriptsPath*") {
    Write-Host "Adding Claude PM Framework to user PATH..."
    $newPath = "$currentPath;$scriptsPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "PATH updated. Please restart your command prompt."
} else {
    Write-Host "Claude PM Framework already in PATH"
}
`;
            
            const psScriptPath = path.join(this.targetDir, 'scripts', 'add-to-path.ps1');
            await fs.writeFile(psScriptPath, powershellScript);
            
            // Create a batch file to run the PowerShell script
            const batScript = `@echo off
echo Adding Claude PM Framework to Windows PATH...
powershell -ExecutionPolicy Bypass -File "%~dp0add-to-path.ps1"
pause`;
            
            await fs.writeFile(path.join(this.targetDir, 'scripts', 'add-to-path.bat'), batScript);
            
            this.log('PATH integration scripts created');
            
        } catch (error) {
            this.log(`Failed to create PATH integration: ${error.message}`, 'warn');
        }
    }

    /**
     * Create Windows shortcuts
     */
    async createShortcuts() {
        this.log('Creating Windows shortcuts...');
        
        try {
            // Create a VBScript to generate shortcuts
            const vbScript = `
Set objShell = CreateObject("WScript.Shell")
Set objDesktop = objShell.SpecialFolders("Desktop")

' Create desktop shortcut
Set objShortcut = objShell.CreateShortcut(objDesktop & "\\Claude PM Framework.lnk")
objShortcut.TargetPath = "${this.targetDir.replace(/\//g, '\\\\')}" & "\\scripts\\claude-pm.bat"
objShortcut.WorkingDirectory = "${this.targetDir.replace(/\//g, '\\\\')}"
objShortcut.Description = "Claude Multi-Agent PM Framework"
objShortcut.IconLocation = "${this.targetDir.replace(/\//g, '\\\\')}" & "\\scripts\\claude-pm.bat,0"
objShortcut.Save

WScript.Echo "Desktop shortcut created"
`;
            
            const vbsPath = path.join(this.targetDir, 'scripts', 'create-shortcuts.vbs');
            await fs.writeFile(vbsPath, vbScript);
            
            // Create batch file to run VBScript
            const batScript = `@echo off
echo Creating Windows shortcuts...
cscript "%~dp0create-shortcuts.vbs" //NoLogo
echo Shortcuts created on Desktop
pause`;
            
            await fs.writeFile(path.join(this.targetDir, 'scripts', 'create-shortcuts.bat'), batScript);
            
            this.log('Shortcut creation scripts generated');
            
        } catch (error) {
            this.log(`Failed to create shortcuts: ${error.message}`, 'warn');
        }
    }

    /**
     * Windows-specific post-install tasks
     */
    async postInstallTasks() {
        this.log('Performing Windows post-install tasks...');
        
        // Create registry entries for file associations (optional)
        try {
            const regScript = `Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Classes\\.claudepm]
@="ClaudePMProject"

[HKEY_CURRENT_USER\\Software\\Classes\\ClaudePMProject]
@="Claude PM Project File"

[HKEY_CURRENT_USER\\Software\\Classes\\ClaudePMProject\\shell\\open\\command]
@="\\"${this.targetDir.replace(/\//g, '\\\\')}\\\\scripts\\\\claude-pm.bat\\" \\"%1\\""`;
            
            const regPath = path.join(this.targetDir, 'scripts', 'file-associations.reg');
            await fs.writeFile(regPath, regScript);
            
            this.log('Registry file created for file associations');
            
        } catch (error) {
            this.log(`Failed to create registry entries: ${error.message}`, 'warn');
        }
    }

    /**
     * Generate Windows installation report
     */
    generateInstallationReport() {
        const report = {
            platform: 'Windows',
            targetDirectory: this.targetDir,
            appDataDirectory: this.appDataDir,
            scriptsCreated: [
                'claude-pm.bat',
                'health-check.bat',
                'add-to-path.bat',
                'create-shortcuts.bat'
            ],
            nextSteps: [
                'Run scripts/claude-pm.bat to start the framework',
                'Run scripts/add-to-path.bat to add to Windows PATH',
                'Run scripts/create-shortcuts.bat to create desktop shortcuts',
                'Optional: Run scripts/install-service.bat as Administrator for service installation'
            ],
            troubleshooting: [
                'Ensure Python 3.8+ is installed and in PATH',
                'Run Command Prompt as Administrator for service installation',
                'Check Windows Defender/Antivirus if scripts are blocked',
                'Verify execution policy for PowerShell scripts'
            ]
        };
        
        return report;
    }

    /**
     * Main Windows installation process
     */
    async install() {
        try {
            this.log('Starting Windows platform installation...', true);
            
            await this.createWindowsDirectories();
            await this.createBatchScripts();
            await this.createWindowsConfig();
            await this.setupPathIntegration();
            await this.createShortcuts();
            await this.postInstallTasks();
            
            const report = this.generateInstallationReport();
            
            this.log('Windows platform installation completed successfully!');
            
            console.log('\\n🎉 Windows Installation Complete!\\n');
            console.log('Next Steps:');
            report.nextSteps.forEach((step, index) => {
                console.log(`${index + 1}. ${step}`);
            });
            
            console.log('\\nTroubleshooting:');
            report.troubleshooting.forEach(tip => {
                console.log(`• ${tip}`);
            });
            
            return report;
            
        } catch (error) {
            this.log(`Windows installation failed: ${error.message}`, 'error');
            throw error;
        }
    }
}

module.exports = WindowsPlatformInstaller;