# CMPM-QA Framework Deployment Automation

## Overview

The CMPM-QA (Claude Multi-Agent PM Quality Assurance) deployment automation provides comprehensive deployment capabilities for the browser extension system as an integrated component of the Claude PM Framework. This deployment automation supports framework-integrated deployment, Chrome extension installation, native messaging host setup, and service bridge configuration across multiple platforms.

## Architecture

### Framework-Integrated Deployment Strategy

```
/claude-multiagent-pm/
├── cmpm-qa/                    # Integrated QA extension
│   ├── extension/              # Chrome extension (completed)
│   │   ├── manifest.json       # Extension manifest
│   │   ├── background.js       # Service worker
│   │   ├── content.js          # Content scripts
│   │   └── popup.html          # Extension popup
│   ├── native-host/           # Native messaging (completed)
│   │   ├── native_host.py      # Python implementation
│   │   ├── native_host.js      # Node.js implementation
│   │   └── host_config.json    # Host configuration
│   ├── service/               # Framework bridge (completed)
│   │   ├── qa_service.py       # HTTP service bridge
│   │   ├── static/             # Static resources
│   │   └── templates/          # Service templates
│   └── scripts/               # Deployment automation (completed)
│       ├── install-qa.sh       # Main installation script
│       ├── setup-extension.sh  # Extension installation
│       ├── configure-host.sh   # Native host setup
│       └── validate-install.sh # Installation validation
├── scripts/                   # Framework scripts (enhanced)
│   └── health-check.sh        # Enhanced with QA monitoring
└── deployment/                # Framework deployment (enhanced)
    └── scripts/
        └── deploy.sh          # Enhanced with QA integration
```

## Installation Components

### 1. Main Installation Script (`install-qa.sh`)

**Purpose**: Framework-integrated deployment with comprehensive automation

**Features**:
- Framework integration validation
- Cross-platform deployment (macOS, Linux, Windows)
- Development and production installation modes
- Automatic Chrome extension configuration
- Native messaging host setup
- Service bridge deployment
- Health monitoring integration

**Usage**:
```bash
# Standard production installation
./cmpm-qa/scripts/install-qa.sh --production

# Development installation with verbose logging
./cmpm-qa/scripts/install-qa.sh --development --verbose

# Framework integration only
./cmpm-qa/scripts/install-qa.sh --framework-only

# Custom configuration
./cmpm-qa/scripts/install-qa.sh --extension-id "my-qa-ext" --port 8888
```

### 2. Chrome Extension Setup (`setup-extension.sh`)

**Purpose**: Automated Chrome extension installation and configuration

**Features**:
- Development mode installation for testing
- Chrome Web Store preparation for production
- Cross-platform extension deployment
- Manifest validation and security checks
- Extension update and maintenance automation

**Usage**:
```bash
# Development installation
./setup-extension.sh --dev-mode --source-dir ./extension --install-dir ~/.claude-pm/qa

# Production packaging
./setup-extension.sh --production --source-dir ./extension --version 1.2.0

# Update existing extension
./setup-extension.sh --update --extension-id cmpm-qa-ext --version 1.1.0
```

### 3. Native Messaging Host Configuration (`configure-host.sh`)

**Purpose**: Native messaging host setup across platforms

**Features**:
- Cross-platform host registration (macOS, Linux, Windows)
- Python and Node.js implementation support
- Secure communication channel setup
- Host process management and monitoring
- Platform-specific security configurations

**Usage**:
```bash
# Standard configuration
./configure-host.sh --source-dir ./native-host --install-dir ~/.claude-pm/qa

# Test existing configuration
./configure-host.sh --test

# Uninstall native messaging host
./configure-host.sh --uninstall --native-host com.claude.pm.qa
```

### 4. Installation Validation (`validate-install.sh`)

**Purpose**: Comprehensive installation validation and health monitoring

**Features**:
- Framework integration validation
- Chrome extension status verification
- Native messaging host connectivity testing
- Service bridge operational validation
- Security configuration verification
- Performance and connectivity testing

**Usage**:
```bash
# Standard validation
./validate-install.sh --qa-config ~/.claude-pm/qa-extension/config/qa-config.json

# Quick validation for CI/CD
./validate-install.sh --quick --json --qa-config ./qa-config.json

# Deep validation with auto-fix
./validate-install.sh --deep --fix --verbose
```

## Framework Integration

### Health Monitoring Enhancement

The framework's `health-check.sh` script has been enhanced to include CMPM-QA monitoring:

**New QA Health Checks**:
- QA extension installation verification
- Configuration file validation
- Native messaging host connectivity
- CMPM QA commands availability
- Enhanced QA Agent accessibility
- Quick validation execution

**Usage**:
```bash
# Run enhanced health check
./scripts/health-check.sh

# Framework health with QA status
python3 -m claude_pm.cmpm_commands cmpm:health

# QA-specific status
python3 -m claude_pm.cmpm_commands cmpm:qa-status
```

### Deployment Script Integration

The main framework deployment script (`deployment/scripts/deploy.sh`) now includes CMPM-QA integration:

**Enhanced Deployment Flow**:
1. Standard framework deployment
2. CMPM-QA component detection
3. QA directory structure creation
4. Automated QA installation (optional)
5. Validation and health checks
6. Enhanced deployment summary

**Usage**:
```bash
# Framework deployment with QA extension
./deployment/scripts/deploy.sh development

# Production deployment with QA
./deployment/scripts/deploy.sh production --backup
```

## Platform Support

### macOS Configuration
- **Chrome Path**: `/Applications/Google Chrome.app`
- **Extensions**: `~/Library/Application Support/Google/Chrome/Default/Extensions`
- **Native Messaging**: `~/Library/Application Support/Google/Chrome/NativeMessagingHosts`
- **Security**: Gatekeeper and code signing considerations

### Linux Configuration
- **Chrome Path**: `/usr/bin/google-chrome` or `/usr/bin/chromium-browser`
- **Extensions**: `~/.config/google-chrome/Default/Extensions`
- **Native Messaging**: `~/.config/google-chrome/NativeMessagingHosts`
- **Security**: SELinux and AppArmor compatibility

### Windows Configuration
- **Chrome Path**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **Extensions**: `%APPDATA%\Google\Chrome\User Data\Default\Extensions`
- **Native Messaging**: `%APPDATA%\Google\Chrome\User Data\NativeMessagingHosts`
- **Security**: Windows Defender and UAC considerations

## Configuration Management

### QA Configuration File (`qa-config.json`)

```json
{
    "extension_id": "cmpm-qa-extension",
    "native_host": "com.claude.pm.qa",
    "service_port": 9876,
    "install_mode": "production",
    "platform": "macos",
    "install_date": "2025-07-10T12:00:00Z",
    "framework_integration": {
        "health_monitoring": true,
        "memory_integration": true,
        "cli_commands": [
            "cmpm:qa-status",
            "cmpm:qa-test",
            "cmpm:qa-results"
        ]
    },
    "paths": {
        "qa_install_dir": "~/.claude-pm/qa-extension",
        "service_install_dir": "~/.claude-pm/qa-extension/service",
        "native_host_install_dir": "~/.claude-pm/qa-extension/native-host",
        "chrome_extensions_dir": "~/Library/Application Support/Google/Chrome/Default/Extensions",
        "native_messaging_dir": "~/Library/Application Support/Google/Chrome/NativeMessagingHosts"
    }
}
```

### Framework Configuration Integration

The QA extension integrates with the main framework configuration:

```json
{
    "qa_extension": {
        "enabled": true,
        "extension_id": "cmpm-qa-extension",
        "native_host": "com.claude.pm.qa",
        "service_port": 9876,
        "install_dir": "~/.claude-pm/qa-extension",
        "config_file": "~/.claude-pm/qa-extension/config/qa-config.json"
    }
}
```

## Security Considerations

### Chrome Extension Security
- **Manifest V3**: Uses latest Chrome extension manifest version
- **Permissions**: Minimal required permissions (storage, activeTab, scripting, nativeMessaging)
- **Host Permissions**: Restricted to localhost for development
- **Content Security Policy**: Strict CSP for security

### Native Messaging Security
- **Allowed Origins**: Restricted to specific extension ID
- **Process Isolation**: Native host runs in separate process
- **Input Validation**: All messages validated and sanitized
- **Error Handling**: Secure error messages without information leakage

### Service Bridge Security
- **CORS Configuration**: Proper CORS setup for browser access
- **API Authentication**: Token-based authentication for production
- **HTTPS Support**: SSL/TLS support for secure communication
- **Rate Limiting**: Request rate limiting and abuse prevention

## Troubleshooting

### Common Issues

**1. Extension Not Loading**
```bash
# Check Chrome developer mode
# Navigate to chrome://extensions/
# Ensure "Developer mode" is enabled
# Check for extension errors in Chrome console

# Validate extension installation
./cmpm-qa/scripts/validate-install.sh --qa-config ./qa-config.json
```

**2. Native Messaging Connection Failed**
```bash
# Check native host manifest
cat ~/.config/google-chrome/NativeMessagingHosts/com.claude.pm.qa.json

# Test native host directly
echo '{"type":"ping","payload":{}}' | ./native-host/native_host.py

# Validate host configuration
./cmpm-qa/scripts/configure-host.sh --test
```

**3. Service Bridge Not Responding**
```bash
# Check service status
curl http://localhost:9876/health

# Check service logs
tail -f ~/.claude-pm/qa-extension/logs/qa-service.log

# Restart service
./qa-extension/service/start-qa-service.sh
```

### Diagnostic Commands

```bash
# Comprehensive health check
./scripts/health-check.sh

# QA-specific validation
./cmpm-qa/scripts/validate-install.sh --deep --verbose

# Framework health with QA status
python3 -m claude_pm.cmpm_commands cmpm:health

# QA extension status
python3 -m claude_pm.cmpm_commands cmpm:qa-status

# Test QA functionality
python3 -m claude_pm.cmpm_commands cmpm:qa-test --browser
```

## Performance Optimization

### Extension Performance
- **Lazy Loading**: Content scripts loaded on demand
- **Memory Management**: Proper cleanup of resources
- **Background Processing**: Efficient service worker implementation
- **Caching**: Intelligent caching of results and configurations

### Native Host Performance
- **Async Processing**: Non-blocking message processing
- **Resource Management**: Efficient memory and CPU usage
- **Connection Pooling**: Reuse of framework connections
- **Error Recovery**: Automatic recovery from transient failures

### Service Bridge Performance
- **HTTP Keep-Alive**: Persistent connections for efficiency
- **Response Caching**: Intelligent caching of API responses
- **Compression**: Response compression for faster transfers
- **Connection Limits**: Proper connection management

## Maintenance and Updates

### Update Procedures

**1. Extension Updates**
```bash
# Update extension version
./cmpm-qa/scripts/setup-extension.sh --update --version 1.2.0

# Validate update
./cmpm-qa/scripts/validate-install.sh --quick
```

**2. Native Host Updates**
```bash
# Update native host
./cmpm-qa/scripts/configure-host.sh --force --source-dir ./native-host

# Test updated host
./cmpm-qa/scripts/configure-host.sh --test
```

**3. Service Updates**
```bash
# Restart service with new version
./qa-extension/service/start-qa-service.sh

# Validate service health
curl http://localhost:9876/health
```

### Monitoring and Logging

**Log Locations**:
- Extension logs: Chrome DevTools Console
- Native host logs: `~/.claude-pm/qa-extension/logs/native-host.log`
- Service logs: `~/.claude-pm/qa-extension/logs/qa-service.log`
- Framework logs: `~/.claude-pm/logs/`

**Health Monitoring**:
- Framework health: `python3 -m claude_pm.cmpm_commands cmpm:health`
- QA health: `python3 -m claude_pm.cmpm_commands cmpm:qa-status`
- Service health: `curl http://localhost:9876/health`

## Development and Testing

### Development Environment Setup

```bash
# Install QA extension in development mode
./cmpm-qa/scripts/install-qa.sh --development --verbose

# Enable Chrome developer mode
# Load unpacked extension from installation directory

# Start service in development mode
CMPM_QA_PORT=9876 python3 ./cmpm-qa/service/qa_service.py

# Run development tests
python3 -m claude_pm.cmpm_commands cmpm:qa-test --browser --urls http://localhost:3000
```

### Testing Framework Integration

```bash
# Test framework integration
python3 -c "from claude_pm.agents.enhanced_qa_agent import EnhancedQAAgent; print('QA Agent Available')"

# Test CMPM commands
python3 -m claude_pm.cmpm_commands cmpm:qa-status --json

# Validate complete installation
./cmpm-qa/scripts/validate-install.sh --deep --report validation-report.html
```

## Production Deployment

### Pre-Production Checklist

- [ ] Framework prerequisites validated
- [ ] Chrome/Chromium installation verified
- [ ] Security configurations reviewed
- [ ] Performance benchmarks completed
- [ ] Backup procedures tested
- [ ] Monitoring and alerting configured

### Production Installation

```bash
# Production framework deployment with QA
./deployment/scripts/deploy.sh production --backup

# Validate production installation
./cmpm-qa/scripts/validate-install.sh --qa-config /opt/claude-pm/.claude-pm/qa-extension/config/qa-config.json

# Configure production monitoring
systemctl enable claude-pm-qa-service
systemctl start claude-pm-qa-service
```

### Production Monitoring

```bash
# Service health check
curl -f http://localhost:9876/health || echo "Service Down"

# Framework health
python3 -m claude_pm.cmpm_commands cmpm:health

# Log monitoring
tail -f /opt/claude-pm/.claude-pm/qa-extension/logs/qa-service.log
```

## Support and Documentation

### Additional Resources

- **Framework Documentation**: `/docs/`
- **QA Agent Documentation**: `/docs/agents/enhanced_qa_agent.md`
- **Security Guidelines**: `/docs/security/`
- **Performance Tuning**: `/docs/performance/`

### Support Channels

- **Issues**: Create issues in the framework repository
- **Discussions**: Use framework discussions for questions
- **Documentation**: Refer to inline script help (`--help`)

### Contributing

- **Bug Reports**: Include validation output and logs
- **Feature Requests**: Describe use case and requirements
- **Pull Requests**: Follow framework contribution guidelines

---

## Summary

The CMPM-QA deployment automation provides comprehensive, framework-integrated deployment capabilities for the browser extension system. With cross-platform support, automated installation, comprehensive validation, and enhanced health monitoring, the deployment automation ensures reliable and maintainable QA extension deployments as an integral component of the Claude PM Framework.

The automation supports both development and production environments, with proper security configurations, performance optimizations, and extensive troubleshooting capabilities. Integration with the existing framework infrastructure provides seamless deployment and operational management.