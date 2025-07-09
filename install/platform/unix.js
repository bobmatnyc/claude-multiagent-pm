#!/usr/bin/env node

/**
 * Claude Multi-Agent PM Framework - Unix Platform Installer
 * 
 * Unix-specific installation and configuration for the Claude PM Framework.
 * Handles Linux and macOS path conventions, service configuration, and permissions.
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

class UnixPlatformInstaller {
    constructor(options = {}) {
        this.targetDir = options.targetDir || process.cwd();
        this.verbose = options.verbose || false;
        this.createService = options.createService || false;
        this.platform = os.platform(); // 'linux' or 'darwin'
        
        this.homeDir = os.homedir();
        this.configDir = path.join(this.homeDir, '.config', 'claude-pm');
        this.binDir = path.join(this.homeDir, '.local', 'bin');
        this.systemdDir = path.join(this.homeDir, '.config', 'systemd', 'user');
    }

    /**
     * Log with Unix-specific formatting
     */
    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        
        if (this.verbose || level !== 'info') {
            console.log(`${prefix} [${timestamp}] ${message}`);
        }
    }

    /**
     * Check if running as root
     */
    isRoot() {
        return process.getuid && process.getuid() === 0;
    }

    /**
     * Detect package manager
     */
    detectPackageManager() {
        const managers = [
            { cmd: 'apt', name: 'apt' },
            { cmd: 'yum', name: 'yum' },
            { cmd: 'dnf', name: 'dnf' },
            { cmd: 'pacman', name: 'pacman' },
            { cmd: 'brew', name: 'homebrew' },
            { cmd: 'zypper', name: 'zypper' }
        ];
        
        for (const manager of managers) {
            try {
                execSync(`which ${manager.cmd}`, { stdio: 'ignore' });
                return manager.name;
            } catch (error) {
                // Manager not found, continue
            }
        }
        
        return null;
    }

    /**
     * Create Unix-specific directories
     */
    async createUnixDirectories() {
        this.log('Creating Unix-specific directories...');
        
        const directories = [
            this.configDir,
            path.join(this.configDir, 'logs'),
            path.join(this.configDir, 'temp'),
            this.binDir
        ];
        
        if (this.createService && this.platform === 'linux') {
            directories.push(this.systemdDir);
        }
        
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
     * Create Unix shell scripts
     */
    async createShellScripts() {
        this.log('Creating Unix shell scripts...');
        
        const scriptsDir = path.join(this.targetDir, 'scripts');
        await fs.mkdir(scriptsDir, { recursive: true });
        
        // Main claude-pm shell script
        const mainScript = `#!/bin/bash
# Claude Multi-Agent PM Framework - Unix Launcher
# Automatically detects Python and launches the framework

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Framework directory
FRAMEWORK_DIR="${this.targetDir}"

# Function to print colored output
print_info() {
    echo -e "\${GREEN}[INFO]\${NC} $1"
}

print_warn() {
    echo -e "\${YELLOW}[WARN]\${NC} $1"
}

print_error() {
    echo -e "\${RED}[ERROR]\${NC} $1"
}

# Check for Python 3
detect_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        # Check if it's Python 3
        if [[ \${PYTHON_VERSION} == 3.* ]]; then
            PYTHON_CMD="python"
        else
            print_error "Python 3.8+ is required. Found Python \${PYTHON_VERSION}"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check minimum version (3.8)
    MAJOR_VERSION=\$(echo \$PYTHON_VERSION | cut -d'.' -f1)
    MINOR_VERSION=\$(echo \$PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ \$MAJOR_VERSION -lt 3 ]] || [[ \$MAJOR_VERSION -eq 3 && \$MINOR_VERSION -lt 8 ]]; then
        print_error "Python 3.8+ is required. Found Python \${PYTHON_VERSION}"
        exit 1
    fi
    
    print_info "Using Python \${PYTHON_VERSION} (\${PYTHON_CMD})"
}

# Main execution
main() {
    print_info "Starting Claude PM Framework..."
    
    # Change to framework directory
    cd "\${FRAMEWORK_DIR}"
    
    # Detect Python
    detect_python
    
    # Check if framework exists
    if [[ ! -f "claude_pm/cli.py" ]]; then
        print_error "Framework CLI not found at claude_pm/cli.py"
        exit 1
    fi
    
    # Execute framework CLI with all arguments
    exec "\${PYTHON_CMD}" claude_pm/cli.py "$@"
}

# Handle Ctrl+C gracefully
trap 'print_info "Shutting down..."; exit 0' INT

# Run main function
main "$@"`;
        
        const scriptPath = path.join(scriptsDir, 'claude-pm');
        await fs.writeFile(scriptPath, mainScript);
        await fs.chmod(scriptPath, '755');
        
        // Health check script
        const healthScript = `#!/bin/bash
# Claude PM Framework - Health Check
echo "Checking Claude PM Framework health..."
cd "${this.targetDir}"
./scripts/claude-pm health status`;
        
        const healthPath = path.join(scriptsDir, 'health-check.sh');
        await fs.writeFile(healthPath, healthScript);
        await fs.chmod(healthPath, '755');
        
        // Installation script for user bin
        const installScript = `#!/bin/bash
# Claude PM Framework - Install to user bin
set -e

BIN_DIR="${this.binDir}"
SCRIPT_PATH="${path.join(scriptsDir, 'claude-pm')}"

echo "Installing Claude PM Framework to user bin..."

# Create bin directory if it doesn't exist
mkdir -p "\${BIN_DIR}"

# Create symlink or copy script
if [[ -L "\${BIN_DIR}/claude-pm" ]]; then
    echo "Removing existing symlink..."
    rm "\${BIN_DIR}/claude-pm"
fi

ln -s "\${SCRIPT_PATH}" "\${BIN_DIR}/claude-pm"
echo "Created symlink: \${BIN_DIR}/claude-pm -> \${SCRIPT_PATH}"

# Check if bin directory is in PATH
if [[ ":$PATH:" != *":\${BIN_DIR}:"* ]]; then
    echo ""
    echo "⚠️  Warning: \${BIN_DIR} is not in your PATH"
    echo "Add the following line to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "export PATH=\\"\${BIN_DIR}:\$PATH\\""
    echo ""
fi

echo "✅ Installation complete! You can now run 'claude-pm' from anywhere."`;
        
        const installPath = path.join(scriptsDir, 'install-user-bin.sh');
        await fs.writeFile(installPath, installScript);
        await fs.chmod(installPath, '755');
        
        this.log('Unix shell scripts created');
    }

    /**
     * Create systemd service (Linux only)
     */
    async createSystemdService() {
        if (this.platform !== 'linux' || !this.createService) {
            return;
        }
        
        this.log('Creating systemd user service...');
        
        const serviceContent = `[Unit]
Description=Claude Multi-Agent PM Framework
Documentation=https://github.com/bobmatnyc/claude-multiagent-pm
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=${this.targetDir}
ExecStart=${path.join(this.targetDir, 'scripts', 'claude-pm')} service start
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${this.targetDir} ${this.configDir}

# Environment
Environment=PYTHONUNBUFFERED=1
Environment=CLAUDE_PM_CONFIG_DIR=${this.configDir}

[Install]
WantedBy=default.target`;
        
        const servicePath = path.join(this.systemdDir, 'claude-pm.service');
        await fs.writeFile(servicePath, serviceContent);
        
        // Create service management scripts
        const serviceManager = `#!/bin/bash
# Claude PM Framework - Systemd Service Manager

set -e

case "$1" in
    install)
        echo "Installing Claude PM systemd service..."
        systemctl --user daemon-reload
        systemctl --user enable claude-pm.service
        echo "✅ Service installed. Use 'start' to begin."
        ;;
    start)
        echo "Starting Claude PM service..."
        systemctl --user start claude-pm.service
        systemctl --user status claude-pm.service --no-pager
        ;;
    stop)
        echo "Stopping Claude PM service..."
        systemctl --user stop claude-pm.service
        ;;
    restart)
        echo "Restarting Claude PM service..."
        systemctl --user restart claude-pm.service
        systemctl --user status claude-pm.service --no-pager
        ;;
    status)
        systemctl --user status claude-pm.service --no-pager
        ;;
    logs)
        journalctl --user -u claude-pm.service -f
        ;;
    uninstall)
        echo "Uninstalling Claude PM service..."
        systemctl --user stop claude-pm.service 2>/dev/null || true
        systemctl --user disable claude-pm.service 2>/dev/null || true
        systemctl --user daemon-reload
        echo "✅ Service uninstalled."
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|uninstall}"
        exit 1
        ;;
esac`;
        
        const managerPath = path.join(this.targetDir, 'scripts', 'service-manager.sh');
        await fs.writeFile(managerPath, serviceManager);
        await fs.chmod(managerPath, '755');
        
        this.log('Systemd service created');
    }

    /**
     * Create macOS LaunchAgent (macOS only)
     */
    async createLaunchAgent() {
        if (this.platform !== 'darwin' || !this.createService) {
            return;
        }
        
        this.log('Creating macOS LaunchAgent...');
        
        const launchAgentDir = path.join(this.homeDir, 'Library', 'LaunchAgents');
        await fs.mkdir(launchAgentDir, { recursive: true });
        
        const plistContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-pm.framework</string>
    <key>ProgramArguments</key>
    <array>
        <string>${path.join(this.targetDir, 'scripts', 'claude-pm')}</string>
        <string>service</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${this.targetDir}</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>${path.join(this.configDir, 'logs', 'claude-pm.log')}</string>
    <key>StandardErrorPath</key>
    <string>${path.join(this.configDir, 'logs', 'claude-pm.error.log')}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>CLAUDE_PM_CONFIG_DIR</key>
        <string>${this.configDir}</string>
    </dict>
</dict>
</plist>`;
        
        const plistPath = path.join(launchAgentDir, 'com.claude-pm.framework.plist');
        await fs.writeFile(plistPath, plistContent);
        
        // Create service management script for macOS
        const serviceManager = `#!/bin/bash
# Claude PM Framework - macOS LaunchAgent Manager

set -e

PLIST_PATH="$HOME/Library/LaunchAgents/com.claude-pm.framework.plist"

case "$1" in
    install)
        echo "Installing Claude PM LaunchAgent..."
        launchctl load "$PLIST_PATH"
        echo "✅ LaunchAgent installed."
        ;;
    start)
        echo "Starting Claude PM service..."
        launchctl start com.claude-pm.framework
        ;;
    stop)
        echo "Stopping Claude PM service..."
        launchctl stop com.claude-pm.framework
        ;;
    restart)
        echo "Restarting Claude PM service..."
        launchctl stop com.claude-pm.framework 2>/dev/null || true
        launchctl start com.claude-pm.framework
        ;;
    status)
        launchctl list | grep com.claude-pm.framework || echo "Service not running"
        ;;
    logs)
        tail -f "${path.join(this.configDir, 'logs', 'claude-pm.log')}"
        ;;
    uninstall)
        echo "Uninstalling Claude PM LaunchAgent..."
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        echo "✅ LaunchAgent uninstalled."
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|uninstall}"
        exit 1
        ;;
esac`;
        
        const managerPath = path.join(this.targetDir, 'scripts', 'service-manager.sh');
        await fs.writeFile(managerPath, serviceManager);
        await fs.chmod(managerPath, '755');
        
        this.log('macOS LaunchAgent created');
    }

    /**
     * Create Unix configuration
     */
    async createUnixConfig() {
        this.log('Creating Unix-specific configuration...');
        
        const packageManager = this.detectPackageManager();
        
        const config = {
            platform: this.platform,
            version: require('../../package.json').version,
            installDate: new Date().toISOString(),
            packageManager: packageManager,
            paths: {
                framework: this.targetDir,
                config: this.configDir,
                bin: this.binDir,
                logs: path.join(this.configDir, 'logs'),
                temp: path.join(this.configDir, 'temp'),
                scripts: path.join(this.targetDir, 'scripts')
            },
            unix: {
                pathSeparator: '/',
                lineEnding: '\\n',
                scriptExtension: '.sh',
                serviceSupport: this.createService,
                serviceType: this.platform === 'linux' ? 'systemd' : 'launchd'
            },
            commands: {
                python: 'python3',
                pip: 'python3 -m pip',
                launcher: path.join(this.targetDir, 'scripts', 'claude-pm')
            }
        };
        
        const configPath = path.join(this.configDir, 'config.json');
        await fs.writeFile(configPath, JSON.stringify(config, null, 2));
        
        this.log(`Unix configuration saved to: ${configPath}`);
    }

    /**
     * Set up shell integration
     */
    async setupShellIntegration() {
        this.log('Setting up shell integration...');
        
        const shellIntegrationScript = `#!/bin/bash
# Claude PM Framework - Shell Integration Setup

BIN_DIR="${this.binDir}"
SCRIPT_PATH="${path.join(this.targetDir, 'scripts', 'claude-pm')}"

# Detect shell
if [[ -n "$ZSH_VERSION" ]]; then
    SHELL_TYPE="zsh"
    RC_FILE="$HOME/.zshrc"
elif [[ -n "$BASH_VERSION" ]]; then
    SHELL_TYPE="bash"
    RC_FILE="$HOME/.bashrc"
else
    SHELL_TYPE="unknown"
    RC_FILE="$HOME/.profile"
fi

echo "Setting up Claude PM Framework for $SHELL_TYPE..."

# Add bin directory to PATH if not already present
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Adding $BIN_DIR to PATH in $RC_FILE"
    echo "" >> "$RC_FILE"
    echo "# Claude PM Framework" >> "$RC_FILE"
    echo "export PATH=\\"$BIN_DIR:\$PATH\\"" >> "$RC_FILE"
    
    echo "✅ PATH updated in $RC_FILE"
    echo "Please run 'source $RC_FILE' or restart your terminal."
else
    echo "✅ $BIN_DIR already in PATH"
fi

# Add shell completion (if supported)
if [[ "$SHELL_TYPE" == "bash" ]] || [[ "$SHELL_TYPE" == "zsh" ]]; then
    COMPLETION_SCRIPT="
# Claude PM Framework completion
_claude_pm_completion() {
    local cur prev opts
    COMPREPLY=()
    cur=\\"\${COMP_WORDS[COMP_CWORD]}\\"
    prev=\\"\${COMP_WORDS[COMP_CWORD-1]}\\"
    opts=\\"health memory project service workflow enforcement --help --version\\"
    
    COMPREPLY=( \\$(compgen -W \\"\\$opts\\" -- \\$cur) )
    return 0
}
complete -F _claude_pm_completion claude-pm"
    
    echo "$COMPLETION_SCRIPT" >> "$RC_FILE"
    echo "✅ Shell completion added"
fi`;
        
        const integrationPath = path.join(this.targetDir, 'scripts', 'setup-shell.sh');
        await fs.writeFile(integrationPath, shellIntegrationScript);
        await fs.chmod(integrationPath, '755');
        
        this.log('Shell integration script created');
    }

    /**
     * Unix-specific post-install tasks
     */
    async postInstallTasks() {
        this.log('Performing Unix post-install tasks...');
        
        // Create desktop entry (Linux only)
        if (this.platform === 'linux') {
            await this.createDesktopEntry();
        }
        
        // Set up log rotation
        await this.setupLogRotation();
        
        // Create man page
        await this.createManPage();
    }

    /**
     * Create Linux desktop entry
     */
    async createDesktopEntry() {
        try {
            const desktopDir = path.join(this.homeDir, '.local', 'share', 'applications');
            await fs.mkdir(desktopDir, { recursive: true });
            
            const desktopEntry = `[Desktop Entry]
Name=Claude PM Framework
Comment=Claude Multi-Agent Project Management Framework
Exec=${path.join(this.targetDir, 'scripts', 'claude-pm')}
Icon=application-x-executable
Terminal=true
Type=Application
Categories=Development;ProjectManagement;
Keywords=claude;ai;project;management;automation;`;
            
            const entryPath = path.join(desktopDir, 'claude-pm.desktop');
            await fs.writeFile(entryPath, desktopEntry);
            await fs.chmod(entryPath, '644');
            
            this.log('Desktop entry created');
            
        } catch (error) {
            this.log(`Failed to create desktop entry: ${error.message}`, 'warn');
        }
    }

    /**
     * Set up log rotation
     */
    async setupLogRotation() {
        const logRotateScript = `#!/bin/bash
# Claude PM Framework - Log Rotation

LOG_DIR="${path.join(this.configDir, 'logs')}"
MAX_SIZE="10M"
MAX_AGE="30"

find "$LOG_DIR" -name "*.log" -size +$MAX_SIZE -exec gzip {} \\;
find "$LOG_DIR" -name "*.log.gz" -mtime +$MAX_AGE -delete

echo "Log rotation completed: $(date)"`;
        
        const rotatePath = path.join(this.targetDir, 'scripts', 'rotate-logs.sh');
        await fs.writeFile(rotatePath, logRotateScript);
        await fs.chmod(rotatePath, '755');
        
        this.log('Log rotation script created');
    }

    /**
     * Create man page
     */
    async createManPage() {
        const manContent = `.TH CLAUDE-PM 1 "$(date +'%B %Y')" "Version $(cat package.json | grep version | cut -d'"' -f4)" "Claude PM Framework"
.SH NAME
claude-pm \\- Claude Multi-Agent Project Management Framework
.SH SYNOPSIS
.B claude-pm
[\\fIOPTION\\fR] [\\fICOMMAND\\fR] [\\fIARGS\\fR...]
.SH DESCRIPTION
Claude PM Framework is a multi-agent project management system powered by AI.
It provides intelligent task orchestration, memory-augmented workflows, and
automated project management capabilities.
.SH OPTIONS
.TP
.B \\-\\-help, \\-h
Show help information
.TP
.B \\-\\-version, \\-v
Show version information
.TP
.B \\-\\-verbose
Enable verbose output
.SH COMMANDS
.TP
.B health
Health monitoring and system status
.TP
.B memory
Memory management operations
.TP
.B project
Project management and operations
.TP
.B service
Service management and control
.TP
.B workflow
Workflow orchestration and automation
.TP
.B enforcement
Framework enforcement and validation
.SH FILES
.TP
.I ~/.config/claude-pm/config.json
Main configuration file
.TP
.I ~/.config/claude-pm/logs/
Log files directory
.TP
.I ~/.local/bin/claude-pm
User binary symlink
.SH EXAMPLES
.TP
Check system health:
.B claude-pm health status
.TP
Create a new project:
.B claude-pm project create my-project
.TP
Initialize memory system:
.B claude-pm memory init
.SH AUTHOR
Written by the Claude PM Framework development team.
.SH REPORTING BUGS
Report bugs to: https://github.com/bobmatnyc/claude-multiagent-pm/issues
.SH COPYRIGHT
This is free software; see the source for copying conditions.
.SH SEE ALSO
Documentation: https://github.com/bobmatnyc/claude-multiagent-pm`;
        
        const manDir = path.join(this.homeDir, '.local', 'share', 'man', 'man1');
        await fs.mkdir(manDir, { recursive: true });
        
        const manPath = path.join(manDir, 'claude-pm.1');
        await fs.writeFile(manPath, manContent);
        
        this.log('Man page created');
    }

    /**
     * Generate Unix installation report
     */
    generateInstallationReport() {
        const report = {
            platform: `Unix (${this.platform})`,
            targetDirectory: this.targetDir,
            configDirectory: this.configDir,
            binDirectory: this.binDir,
            scriptsCreated: [
                'claude-pm',
                'health-check.sh',
                'install-user-bin.sh',
                'setup-shell.sh',
                'service-manager.sh',
                'rotate-logs.sh'
            ],
            nextSteps: [
                'Run scripts/install-user-bin.sh to install to user bin',
                'Run scripts/setup-shell.sh to configure shell integration',
                'Run claude-pm --help to see available commands',
                this.createService ? 'Run scripts/service-manager.sh install to set up service' : null
            ].filter(Boolean),
            troubleshooting: [
                'Ensure Python 3.8+ is installed and accessible',
                'Check that ~/.local/bin is in your PATH',
                'Verify script permissions with ls -la scripts/',
                'Review logs in ~/.config/claude-pm/logs/'
            ]
        };
        
        return report;
    }

    /**
     * Main Unix installation process
     */
    async install() {
        try {
            this.log('Starting Unix platform installation...');
            
            await this.createUnixDirectories();
            await this.createShellScripts();
            await this.createUnixConfig();
            await this.setupShellIntegration();
            
            if (this.platform === 'linux') {
                await this.createSystemdService();
            } else if (this.platform === 'darwin') {
                await this.createLaunchAgent();
            }
            
            await this.postInstallTasks();
            
            const report = this.generateInstallationReport();
            
            this.log('Unix platform installation completed successfully!');
            
            console.log('\\n🎉 Unix Installation Complete!\\n');
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
            this.log(`Unix installation failed: ${error.message}`, 'error');
            throw error;
        }
    }
}

module.exports = UnixPlatformInstaller;