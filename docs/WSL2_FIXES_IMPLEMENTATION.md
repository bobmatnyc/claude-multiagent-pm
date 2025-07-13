# Claude PM Framework - WSL2 PATH Configuration Fixes

## Overview

This document details the comprehensive fixes implemented to resolve WSL2 PATH configuration issues that prevented the Claude PM Framework from working properly in WSL2 environments with NVM-managed Node.js installations.

## Root Cause Analysis

### Problem Statement
Users in WSL2 environments with NVM-installed Node.js experienced the following issues:
1. `aitrackdown: not found` - ai-trackdown-tools dependency not accessible
2. `spawn claude ENOENT` - Claude CLI not found in PATH despite working normally
3. npm global packages not properly added to PATH in WSL2

### Root Causes
1. **NVM PATH Configuration**: WSL2 environments with NVM don't automatically configure npm global bin directories in PATH
2. **Shell Initialization**: WSL2 shell sessions don't always properly source NVM configuration
3. **Global Package Detection**: Standard npm global detection methods fail in NVM environments
4. **PATH Persistence**: PATH changes don't persist across shell sessions without proper shell configuration

## Implementation Details

### 1. Enhanced Global Installation Detection (`install/postinstall.js`)

#### WSL2-Specific Global Path Patterns
```javascript
// Enhanced global node_modules patterns (includes WSL2 patterns)
nodeModulesGlobal: packagePath.includes('node_modules') && (
    // ... existing patterns ...
    // WSL2-specific patterns
    packagePath.includes('/.nvm/versions/node/') ||    // NVM global packages in WSL2
    packagePath.includes('/nvm/versions/node/') ||     // Alternative NVM paths
    (packagePath.includes('/home/') && packagePath.includes('/.nvm/')) || // WSL2 home NVM
    (packagePath.includes('/mnt/c/') && packagePath.includes('node_modules')) // WSL2 Windows mount
),
```

#### WSL2 Environment Detection
```javascript
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
            return isWSL2;
        }
        
        return false;
    } catch (error) {
        return false;
    }
}
```

### 2. WSL2-Specific Setup Process

#### npm Global Bin Detection
```javascript
async getWSL2NpmGlobalBin() {
    try {
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
                    return binDir;
                }
            } catch (methodError) {
                // Try next method
            }
        }
        
        return null;
    } catch (error) {
        return null;
    }
}
```

#### Shell Configuration Update
```javascript
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
                    const pathExport = `\\n# Claude PM Framework - WSL2 PATH configuration\\nexport PATH="${globalBinDir}:$PATH"\\n`;
                    
                    // Add PATH configuration
                    fsSync.appendFileSync(shellFile, pathExport);
                }
            }
        }
    } catch (error) {
        // Handle errors gracefully
    }
}
```

### 3. Enhanced CLI Detection (`bin/claude-pm`)

#### Platform Detection with WSL2
```javascript
function detectPlatformInfo() {
    const platform = os.platform();
    let isWSL2 = false;
    let wslDistro = null;
    let display = platform;
    
    // WSL2 Detection
    if (platform === 'linux') {
        try {
            // Check environment variables
            wslDistro = process.env.WSL_DISTRO_NAME;
            const wslEnv = process.env.WSLENV;
            
            if (wslDistro || wslEnv) {
                // Check /proc/version for WSL2 specifically
                if (fs.existsSync('/proc/version')) {
                    const versionContent = fs.readFileSync('/proc/version', 'utf8');
                    isWSL2 = versionContent.includes('WSL2') || versionContent.includes('microsoft');
                    
                    if (isWSL2) {
                        display = `Linux (WSL2${wslDistro ? ` - ${wslDistro}` : ''})`;
                    }
                }
            }
        } catch (error) {
            // Fallback to standard Linux detection
        }
    }
    
    return { platform, isWSL2, wslDistro, display };
}
```

#### WSL2 PATH Analysis
```javascript
function analyzeWSL2Path() {
    const issues = [];
    let hasIssues = false;
    
    try {
        const currentPath = process.env.PATH || '';
        const npmGlobalBin = getNpmGlobalBin();
        
        // Check if npm global bin is in PATH
        if (npmGlobalBin && !currentPath.includes(npmGlobalBin)) {
            issues.push(`NPM global bin directory not in PATH: ${npmGlobalBin}`);
            hasIssues = true;
        }
        
        // Check for NVM-related PATH issues
        const nvmDir = process.env.NVM_DIR;
        if (nvmDir && !currentPath.includes('.nvm')) {
            issues.push('NVM paths may not be properly configured in PATH');
            hasIssues = true;
        }
        
        // Check command accessibility
        ['claude-pm', 'aitrackdown'].forEach(cmd => {
            try {
                execSync(`which ${cmd}`, { encoding: 'utf8', timeout: 3000 });
            } catch (error) {
                issues.push(`${cmd} command not found in current PATH`);
                hasIssues = true;
            }
        });
        
    } catch (error) {
        issues.push(`PATH analysis failed: ${error.message}`);
        hasIssues = true;
    }
    
    return { hasIssues, issues };
}
```

### 4. Enhanced Error Handling with WSL2 Guidance

#### Claude CLI Validation Enhancement
```javascript
async validateEnvironment() {
    try {
        const launchConfig = await this.getOptimalLaunchCommand();
        return { valid: true, ... };
    } catch (error) {
        // Enhanced error handling for WSL2
        const platformInfo = detectPlatformInfo();
        
        if (platformInfo.isWSL2 && error.message.includes('not found')) {
            // WSL2-specific PATH issue diagnosis
            const pathAnalysis = analyzeWSL2Path();
            const wsl2Guidance = this.getWSL2Guidance(pathAnalysis);
            
            return {
                valid: false,
                error: error.message,
                wsl2Issues: pathAnalysis,
                wsl2Guidance: wsl2Guidance,
                isWSL2: true
            };
        }
        
        return { valid: false, error: error.message, isWSL2: platformInfo.isWSL2 };
    }
}
```

#### WSL2-Specific Error Messages
```javascript
claudeProcess.on('error', (error) => {
    console.error('❌ Failed to launch Claude:', error.message);
    
    // Enhanced WSL2 error handling
    const platformInfo = detectPlatformInfo();
    if (platformInfo.isWSL2 && error.message.includes('ENOENT')) {
        console.error('🐧 WSL2 Environment Detected - PATH Issue Likely');
        console.error('🚀 Quick WSL2 Fixes:');
        
        const npmGlobalBin = getNpmGlobalBin();
        if (npmGlobalBin) {
            console.error(`   1. export PATH="${npmGlobalBin}:$PATH"`);
        } else {
            console.error('   1. export PATH="$(npm bin -g):$PATH"');
        }
        console.error('   2. source ~/.bashrc');
        console.error('   3. claude-pm  # try again');
        
        console.error('🔧 Permanent WSL2 Fix:');
        console.error(`   echo 'export PATH="${npmGlobalBin}:$PATH"' >> ~/.bashrc`);
        console.error('   source ~/.bashrc');
        
        console.error('🔍 WSL2 Diagnostic:');
        console.error('   ~/.claude-pm/wsl2-diagnostic.sh');
    }
    
    // ... general troubleshooting steps
});
```

## Additional Tools

### 1. WSL2 PATH Fix Script (`scripts/wsl2-path-fix.sh`)

Comprehensive shell script that:
- Detects WSL2 environment
- Finds npm global bin directory using multiple methods
- Backs up existing shell configuration files
- Adds PATH configuration to appropriate shell files
- Tests the fix and provides verification
- Offers recovery guidance

### 2. WSL2 Fix Validation Script (`scripts/test-wsl2-fixes.js`)

Node.js validation script that:
- Tests WSL2 detection logic
- Validates npm global bin detection methods
- Checks PATH configuration
- Tests command availability
- Validates postinstall and CLI WSL2 logic
- Generates comprehensive validation report

### 3. WSL2 Diagnostic Script (Generated)

Runtime diagnostic script created by postinstall that:
- Analyzes current WSL2 environment
- Tests PATH configuration
- Provides immediate and permanent fix suggestions
- Offers comprehensive troubleshooting information

## Usage Instructions

### For Users Experiencing WSL2 Issues

1. **Quick Fix (immediate)**:
   ```bash
   export PATH="$(npm bin -g):$PATH"
   source ~/.bashrc
   claude-pm --version  # test
   ```

2. **Permanent Fix**:
   ```bash
   # Run the automated fix script
   ~/.claude-pm/scripts/wsl2-path-fix.sh
   
   # Or add manually to ~/.bashrc
   echo 'export PATH="$(npm bin -g):$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Diagnostic and Validation**:
   ```bash
   # Run WSL2 diagnostic
   ~/.claude-pm/wsl2-diagnostic.sh
   
   # Run validation tests
   node ~/.claude-pm/scripts/test-wsl2-fixes.js
   ```

### For Developers

1. **Test WSL2 Fixes**:
   ```bash
   node scripts/test-wsl2-fixes.js
   ```

2. **Manual WSL2 Setup Testing**:
   ```bash
   # Simulate WSL2 environment
   export WSL_DISTRO_NAME="Ubuntu"
   export WSLENV="PATH/l"
   
   # Test postinstall
   node install/postinstall.js
   
   # Test CLI
   node bin/claude-pm --env-status
   ```

## Testing Results

### WSL2 Fix Validation Report
The validation script tests:

✅ **WSL2 Detection**: Properly identifies WSL2 environments
✅ **NPM Global Bin Detection**: Multiple fallback methods work
✅ **PATH Configuration**: Detects and fixes PATH issues
✅ **Command Availability**: Verifies all required commands are accessible
✅ **Postinstall WSL2 Logic**: Confirms WSL2-specific code is present
✅ **CLI WSL2 Logic**: Validates enhanced error handling
✅ **WSL2 Fix Script**: Automated fix script is available and executable

### Coverage
- **Installation Types**: Global NPM with NVM in WSL2
- **Shell Types**: Bash and Zsh
- **NVM Configurations**: Various NVM installation paths
- **Error Scenarios**: `ENOENT`, PATH issues, missing dependencies

## Benefits

### User Experience
- **Automatic Detection**: WSL2 environments are automatically detected
- **Clear Guidance**: Specific, actionable error messages for WSL2 users
- **Multiple Fix Options**: Immediate, permanent, and automated fixes available
- **Comprehensive Diagnostics**: Detailed analysis of PATH and environment issues

### Developer Experience
- **Robust Detection**: Multiple fallback methods for npm global bin detection
- **Enhanced Error Handling**: WSL2-specific error paths with detailed guidance
- **Validation Tools**: Comprehensive testing and validation scripts
- **Documentation**: Detailed implementation and usage documentation

### Technical Robustness
- **Graceful Degradation**: Fixes don't break non-WSL2 environments
- **Multiple Fallbacks**: If one detection method fails, others are tried
- **Safe Configuration**: Backs up configuration files before modification
- **Comprehensive Testing**: Validation covers all critical paths

## Future Considerations

### Monitoring
- Track WSL2 user success rates through usage analytics
- Monitor GitHub issues for additional WSL2-related problems
- Collect feedback on fix effectiveness

### Enhancements
- Add support for additional shell types (fish, PowerShell)
- Implement automatic PATH repair on each CLI invocation
- Add Windows Terminal integration guidance
- Consider WSL-specific package distribution methods

### Maintenance
- Update WSL2 detection as WSL evolves
- Maintain compatibility with new NVM versions
- Keep fix scripts updated with latest best practices
- Regular testing in various WSL2 distributions

## Related Resources

- **GitHub Issue**: [#1 - WSL2 PATH Configuration Issues](https://github.com/bobmatnyc/claude-multiagent-pm/issues/1)
- **WSL2 Documentation**: [WSL2 Setup Guide](https://docs.microsoft.com/en-us/windows/wsl/)
- **NVM Documentation**: [NVM Installation and Usage](https://github.com/nvm-sh/nvm)
- **Fix Scripts**: `scripts/wsl2-path-fix.sh`, `scripts/test-wsl2-fixes.js`