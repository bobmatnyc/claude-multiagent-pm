#!/bin/bash
#
# CMPM-QA Framework Installation Script
# =====================================
# 
# Comprehensive deployment automation for the CMPM-QA browser extension system
# as an integrated component of the Claude PM Framework.
#
# Features:
# - Framework-integrated deployment strategy
# - Chrome extension installation and configuration
# - Native messaging host setup across platforms
# - Service bridge deployment and configuration
# - Health monitoring and validation automation
#
# This script supports the enhanced CMPM CLI commands:
# - cmpm:health dashboard
# - cmpm:qa-status, cmpm:qa-test, cmpm:qa-results commands
# - Framework health monitoring and agent registry integration

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="CMPM-QA Framework Installation"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Emoji for better UX
CHECKMARK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
BROWSER="🌐"
EXTENSION="🧩"
HEALTH="🏥"

# Default configuration
DEFAULT_EXTENSION_ID="cmpm-qa-extension"
DEFAULT_NATIVE_HOST="com.claude.pm.qa"
DEFAULT_PORT="9876"

# Logging functions
log_info() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

log_success() {
    echo -e "${GREEN}${CHECKMARK} $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

log_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

log_header() {
    echo -e "${PURPLE}${ROCKET} $1${NC}"
}

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "=========================================================="
    echo "  CMPM-QA Framework Installation Script"
    echo "  Version: $SCRIPT_VERSION"
    echo "  Framework Integration: Claude PM Framework v4.1.0"
    echo "=========================================================="
    echo -e "${NC}"
}

# Help function
show_help() {
    cat << EOF
CMPM-QA Framework Installation Script

USAGE:
    $0 [MODE] [OPTIONS]

MODES:
    --development       Development installation with debugging enabled
    --production        Production installation (default)
    --framework-only    Install only framework integration components
    --extension-only    Install only browser extension components
    --validate          Validate installation without installing

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose logging
    -f, --force         Force installation (overwrite existing)
    -s, --skip-chrome   Skip Chrome extension installation
    -n, --skip-native   Skip native messaging host setup
    --extension-id ID   Custom extension ID (default: $DEFAULT_EXTENSION_ID)
    --native-host HOST  Custom native host name (default: $DEFAULT_NATIVE_HOST)
    --port PORT         Custom service port (default: $DEFAULT_PORT)
    --dry-run           Show what would be done without executing

EXAMPLES:
    # Standard production installation
    $0 --production

    # Development installation with verbose logging
    $0 --development --verbose

    # Framework integration only
    $0 --framework-only

    # Validate existing installation
    $0 --validate

    # Custom configuration
    $0 --extension-id "my-qa-ext" --port 8888

FRAMEWORK INTEGRATION:
    This installation integrates with the Claude PM Framework to enhance:
    - Health monitoring dashboard (cmpm:health)
    - QA-specific commands (cmpm:qa-status, cmpm:qa-test, cmpm:qa-results)
    - Framework agent registry and service management
    - Memory-augmented testing capabilities

For more information, see: docs/CMPM_QA_DEPLOYMENT.md
EOF
}

# Parse command line arguments
parse_arguments() {
    INSTALL_MODE="production"
    VERBOSE=false
    FORCE_INSTALL=false
    SKIP_CHROME=false
    SKIP_NATIVE=false
    DRY_RUN=false
    EXTENSION_ID="$DEFAULT_EXTENSION_ID"
    NATIVE_HOST="$DEFAULT_NATIVE_HOST"
    SERVICE_PORT="$DEFAULT_PORT"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --development)
                INSTALL_MODE="development"
                shift
                ;;
            --production)
                INSTALL_MODE="production"
                shift
                ;;
            --framework-only)
                INSTALL_MODE="framework-only"
                shift
                ;;
            --extension-only)
                INSTALL_MODE="extension-only"
                shift
                ;;
            --validate)
                INSTALL_MODE="validate"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE_INSTALL=true
                shift
                ;;
            -s|--skip-chrome)
                SKIP_CHROME=true
                shift
                ;;
            -n|--skip-native)
                SKIP_NATIVE=true
                shift
                ;;
            --extension-id)
                EXTENSION_ID="$2"
                shift 2
                ;;
            --native-host)
                NATIVE_HOST="$2"
                shift 2
                ;;
            --port)
                SERVICE_PORT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Detect platform and configure paths
configure_environment() {
    log_header "Configuring Environment"

    # Detect platform
    case "$(uname -s)" in
        Darwin*)
            PLATFORM="macos"
            CHROME_EXTENSIONS_DIR="$HOME/Library/Application Support/Google/Chrome/Default/Extensions"
            NATIVE_MESSAGING_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
            ;;
        Linux*)
            PLATFORM="linux"
            CHROME_EXTENSIONS_DIR="$HOME/.config/google-chrome/Default/Extensions"
            NATIVE_MESSAGING_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            PLATFORM="windows"
            CHROME_EXTENSIONS_DIR="$APPDATA/Google/Chrome/User Data/Default/Extensions"
            NATIVE_MESSAGING_DIR="$APPDATA/Google/Chrome/User Data/Default/NativeMessagingHosts"
            ;;
        *)
            log_error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac

    # Framework paths
    FRAMEWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    CMPM_QA_ROOT="$FRAMEWORK_ROOT/cmpm-qa"
    EXTENSION_SOURCE="$CMPM_QA_ROOT/extension"
    NATIVE_HOST_SOURCE="$CMPM_QA_ROOT/native-host"
    SERVICE_SOURCE="$CMPM_QA_ROOT/service"
    SCRIPTS_DIR="$CMPM_QA_ROOT/scripts"

    # Installation paths
    QA_INSTALL_DIR="$FRAMEWORK_ROOT/.claude-pm/qa-extension"
    SERVICE_INSTALL_DIR="$QA_INSTALL_DIR/service"
    NATIVE_HOST_INSTALL_DIR="$QA_INSTALL_DIR/native-host"

    log_info "Platform: $PLATFORM"
    log_info "Framework Root: $FRAMEWORK_ROOT"
    log_info "CMPM-QA Root: $CMPM_QA_ROOT"
    log_info "QA Install Directory: $QA_INSTALL_DIR"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Chrome Extensions Directory: $CHROME_EXTENSIONS_DIR"
        log_info "Native Messaging Directory: $NATIVE_MESSAGING_DIR"
        log_info "Extension ID: $EXTENSION_ID"
        log_info "Native Host: $NATIVE_HOST"
        log_info "Service Port: $SERVICE_PORT"
    fi
}

# Validate prerequisites and environment
validate_prerequisites() {
    log_header "Validating Prerequisites"

    local errors=0

    # Check framework installation
    if [[ ! -f "$FRAMEWORK_ROOT/claude_pm/cli.py" ]]; then
        log_error "Claude PM Framework not found at $FRAMEWORK_ROOT"
        ((errors++))
    else
        log_success "Claude PM Framework detected"
    fi

    # Check Python environment
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        ((errors++))
    else
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python version: $python_version"
    fi

    # Check Node.js for native host (if needed)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js not found - native messaging host will use Python fallback"
    else
        local node_version=$(node --version)
        log_success "Node.js version: $node_version"
    fi

    # Check Chrome installation (if not skipping)
    if [[ "$SKIP_CHROME" == "false" ]]; then
        if ! check_chrome_installation; then
            log_error "Google Chrome not found - required for extension installation"
            ((errors++))
        else
            log_success "Google Chrome detected"
        fi
    fi

    # Platform-specific validations
    case $PLATFORM in
        macos)
            validate_macos_requirements
            ;;
        linux)
            validate_linux_requirements
            ;;
        windows)
            validate_windows_requirements
            ;;
    esac

    if [[ $errors -gt 0 ]]; then
        log_error "Prerequisites validation failed with $errors errors"
        exit 1
    fi

    log_success "Prerequisites validation completed"
}

check_chrome_installation() {
    local chrome_paths=()
    
    case $PLATFORM in
        macos)
            chrome_paths=(
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                "/Applications/Google Chrome.app"
            )
            ;;
        linux)
            chrome_paths=(
                "/usr/bin/google-chrome"
                "/usr/bin/google-chrome-stable"
                "/usr/bin/chromium-browser"
                "/snap/bin/chromium"
            )
            ;;
        windows)
            chrome_paths=(
                "/c/Program Files/Google/Chrome/Application/chrome.exe"
                "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            )
            ;;
    esac

    for path in "${chrome_paths[@]}"; do
        if [[ -e "$path" ]]; then
            CHROME_EXECUTABLE="$path"
            return 0
        fi
    done

    # Try to find in PATH
    if command -v google-chrome &> /dev/null; then
        CHROME_EXECUTABLE="google-chrome"
        return 0
    elif command -v chromium &> /dev/null; then
        CHROME_EXECUTABLE="chromium"
        return 0
    fi

    return 1
}

validate_macos_requirements() {
    log_info "Validating macOS requirements..."
    
    # Check for Xcode command line tools (needed for some native components)
    if ! xcode-select -p &> /dev/null; then
        log_warning "Xcode command line tools not found - may be needed for native compilation"
    fi
    
    log_success "macOS requirements validated"
}

validate_linux_requirements() {
    log_info "Validating Linux requirements..."
    
    # Check for required packages
    local required_packages=("curl" "unzip")
    for package in "${required_packages[@]}"; do
        if ! command -v "$package" &> /dev/null; then
            log_error "Required package '$package' is not installed"
            return 1
        fi
    done
    
    log_success "Linux requirements validated"
}

validate_windows_requirements() {
    log_info "Validating Windows requirements..."
    
    # Check for PowerShell (usually available on Windows)
    if ! command -v powershell &> /dev/null; then
        log_warning "PowerShell not found - some features may be limited"
    fi
    
    log_success "Windows requirements validated"
}

# Create QA extension directory structure
create_qa_directories() {
    log_header "Creating QA Extension Directory Structure"

    local directories=(
        "$QA_INSTALL_DIR"
        "$SERVICE_INSTALL_DIR"
        "$NATIVE_HOST_INSTALL_DIR"
        "$QA_INSTALL_DIR/logs"
        "$QA_INSTALL_DIR/config"
        "$QA_INSTALL_DIR/temp"
    )

    for dir in "${directories[@]}"; do
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log_info "[DRY RUN] Would create directory: $dir"
        fi
    done
}

# Install framework integration components
install_framework_integration() {
    if [[ "$INSTALL_MODE" == "extension-only" ]]; then
        return 0
    fi

    log_header "${GEAR} Installing Framework Integration Components"

    # The enhanced QA agent is already integrated in the framework
    # Just need to ensure configuration is properly set up
    
    local qa_config="$QA_INSTALL_DIR/config/qa-config.json"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cat > "$qa_config" << EOF
{
    "extension_id": "$EXTENSION_ID",
    "native_host": "$NATIVE_HOST",
    "service_port": $SERVICE_PORT,
    "install_mode": "$INSTALL_MODE",
    "platform": "$PLATFORM",
    "install_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
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
        "qa_install_dir": "$QA_INSTALL_DIR",
        "service_install_dir": "$SERVICE_INSTALL_DIR",
        "native_host_install_dir": "$NATIVE_HOST_INSTALL_DIR",
        "chrome_extensions_dir": "$CHROME_EXTENSIONS_DIR",
        "native_messaging_dir": "$NATIVE_MESSAGING_DIR"
    }
}
EOF
        log_success "QA configuration file created"
    else
        log_info "[DRY RUN] Would create QA configuration file"
    fi

    # Update framework configuration to include QA extension
    local framework_config="$FRAMEWORK_ROOT/.claude-pm/config.json"
    if [[ -f "$framework_config" && "$DRY_RUN" == "false" ]]; then
        # Backup existing config
        cp "$framework_config" "$framework_config.backup"
        
        # Add QA extension configuration using Python
        python3 << EOF
import json
import sys

try:
    with open('$framework_config', 'r') as f:
        config = json.load(f)
except:
    config = {}

# Add QA extension configuration
if 'qa_extension' not in config:
    config['qa_extension'] = {}

config['qa_extension'].update({
    'enabled': True,
    'extension_id': '$EXTENSION_ID',
    'native_host': '$NATIVE_HOST',
    'service_port': $SERVICE_PORT,
    'install_dir': '$QA_INSTALL_DIR',
    'config_file': '$qa_config'
})

with open('$framework_config', 'w') as f:
    json.dump(config, f, indent=2)

print("Framework configuration updated")
EOF
        log_success "Framework configuration updated with QA extension settings"
    elif [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update framework configuration"
    fi
}

# Install Chrome extension
install_chrome_extension() {
    if [[ "$SKIP_CHROME" == "true" || "$INSTALL_MODE" == "framework-only" ]]; then
        log_info "Skipping Chrome extension installation"
        return 0
    fi

    log_header "${BROWSER} Installing Chrome Extension"

    # Call the specialized extension installation script
    if [[ -f "$SCRIPTS_DIR/setup-extension.sh" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            bash "$SCRIPTS_DIR/setup-extension.sh" \
                --extension-id "$EXTENSION_ID" \
                --source-dir "$EXTENSION_SOURCE" \
                --install-dir "$QA_INSTALL_DIR" \
                ${VERBOSE:+--verbose} \
                ${FORCE_INSTALL:+--force}
            log_success "Chrome extension installation completed"
        else
            log_info "[DRY RUN] Would install Chrome extension"
        fi
    else
        log_error "Extension installation script not found: $SCRIPTS_DIR/setup-extension.sh"
        return 1
    fi
}

# Setup native messaging host
setup_native_messaging() {
    if [[ "$SKIP_NATIVE" == "true" || "$INSTALL_MODE" == "framework-only" ]]; then
        log_info "Skipping native messaging host setup"
        return 0
    fi

    log_header "${GEAR} Setting Up Native Messaging Host"

    # Call the specialized native host configuration script
    if [[ -f "$SCRIPTS_DIR/configure-host.sh" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            bash "$SCRIPTS_DIR/configure-host.sh" \
                --native-host "$NATIVE_HOST" \
                --source-dir "$NATIVE_HOST_SOURCE" \
                --install-dir "$NATIVE_HOST_INSTALL_DIR" \
                --platform "$PLATFORM" \
                ${VERBOSE:+--verbose} \
                ${FORCE_INSTALL:+--force}
            log_success "Native messaging host setup completed"
        else
            log_info "[DRY RUN] Would setup native messaging host"
        fi
    else
        log_error "Native host configuration script not found: $SCRIPTS_DIR/configure-host.sh"
        return 1
    fi
}

# Install service bridge
install_service_bridge() {
    if [[ "$INSTALL_MODE" == "extension-only" ]]; then
        log_info "Skipping service bridge installation"
        return 0
    fi

    log_header "${GEAR} Installing Service Bridge"

    if [[ "$DRY_RUN" == "false" ]]; then
        # Copy service files
        if [[ -d "$SERVICE_SOURCE" ]]; then
            cp -r "$SERVICE_SOURCE"/* "$SERVICE_INSTALL_DIR/"
            log_success "Service bridge files copied"
        else
            log_warning "Service source directory not found: $SERVICE_SOURCE"
        fi

        # Create service startup script
        local service_script="$SERVICE_INSTALL_DIR/start-qa-service.sh"
        cat > "$service_script" << EOF
#!/bin/bash
# CMPM-QA Service Bridge Startup Script
# Generated by install-qa.sh v$SCRIPT_VERSION

cd "\$(dirname "\$0")"

# Set environment variables
export CMPM_QA_PORT=$SERVICE_PORT
export CMPM_QA_HOST=$NATIVE_HOST
export CMPM_QA_CONFIG="$qa_config"
export PYTHONPATH="$FRAMEWORK_ROOT:\$PYTHONPATH"

# Start the service
if [[ -f "qa_service.py" ]]; then
    python3 qa_service.py
elif [[ -f "qa_service.js" ]]; then
    node qa_service.js
else
    echo "Error: No service implementation found"
    exit 1
fi
EOF
        chmod +x "$service_script"
        log_success "Service startup script created"

        # Create systemd service file for Linux production installations
        if [[ "$PLATFORM" == "linux" && "$INSTALL_MODE" == "production" ]]; then
            local systemd_service="$QA_INSTALL_DIR/cmpm-qa-service.service"
            cat > "$systemd_service" << EOF
[Unit]
Description=CMPM-QA Service Bridge
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SERVICE_INSTALL_DIR
ExecStart=$service_script
Restart=always
RestartSec=10
Environment=PYTHONPATH=$FRAMEWORK_ROOT

[Install]
WantedBy=multi-user.target
EOF
            log_success "Systemd service file created (not installed yet)"
        fi
    else
        log_info "[DRY RUN] Would install service bridge"
    fi
}

# Validate installation
validate_installation() {
    log_header "${HEALTH} Validating Installation"

    # Call the specialized validation script
    if [[ -f "$SCRIPTS_DIR/validate-install.sh" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            bash "$SCRIPTS_DIR/validate-install.sh" \
                --qa-config "$QA_INSTALL_DIR/config/qa-config.json" \
                ${VERBOSE:+--verbose}
            
            if [[ $? -eq 0 ]]; then
                log_success "Installation validation completed successfully"
            else
                log_error "Installation validation failed"
                return 1
            fi
        else
            log_info "[DRY RUN] Would validate installation"
        fi
    else
        log_error "Validation script not found: $SCRIPTS_DIR/validate-install.sh"
        return 1
    fi
}

# Show installation summary
show_installation_summary() {
    log_header "Installation Summary"
    
    echo -e "${CYAN}Installation Mode:${NC} $INSTALL_MODE"
    echo -e "${CYAN}Platform:${NC} $PLATFORM"
    echo -e "${CYAN}Extension ID:${NC} $EXTENSION_ID"
    echo -e "${CYAN}Native Host:${NC} $NATIVE_HOST"
    echo -e "${CYAN}Service Port:${NC} $SERVICE_PORT"
    echo -e "${CYAN}Install Directory:${NC} $QA_INSTALL_DIR"
    echo ""
    
    if [[ "$SKIP_CHROME" == "false" ]]; then
        echo -e "${GREEN}${EXTENSION} Chrome Extension:${NC} Installed"
    else
        echo -e "${YELLOW}${EXTENSION} Chrome Extension:${NC} Skipped"
    fi
    
    if [[ "$SKIP_NATIVE" == "false" ]]; then
        echo -e "${GREEN}${GEAR} Native Messaging:${NC} Configured"
    else
        echo -e "${YELLOW}${GEAR} Native Messaging:${NC} Skipped"
    fi
    
    if [[ "$INSTALL_MODE" != "extension-only" ]]; then
        echo -e "${GREEN}${ROCKET} Framework Integration:${NC} Active"
    else
        echo -e "${YELLOW}${ROCKET} Framework Integration:${NC} Skipped"
    fi
    
    echo ""
    log_success "CMPM-QA installation completed successfully!"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Test QA extension: python3 -m claude_pm.cmpm_commands cmpm:qa-status"
    echo "2. Run health check: python3 -m claude_pm.cmpm_commands cmpm:health"
    echo "3. Execute tests: python3 -m claude_pm.cmpm_commands cmpm:qa-test --browser"
    echo "4. View results: python3 -m claude_pm.cmpm_commands cmpm:qa-results"
    echo ""
    echo -e "${BLUE}Configuration files:${NC}"
    echo "- QA Config: $QA_INSTALL_DIR/config/qa-config.json"
    echo "- Framework Config: $FRAMEWORK_ROOT/.claude-pm/config.json"
    echo "- Logs: $QA_INSTALL_DIR/logs/"
    echo ""
    echo -e "${BLUE}For support:${NC}"
    echo "- Run validation: $SCRIPTS_DIR/validate-install.sh"
    echo "- Check logs: tail -f $QA_INSTALL_DIR/logs/qa-service.log"
    echo "- Documentation: $FRAMEWORK_ROOT/docs/CMPM_QA_DEPLOYMENT.md"
}

# Main installation workflow
main() {
    show_banner
    parse_arguments "$@"
    configure_environment
    
    # Show configuration summary in verbose mode
    if [[ "$VERBOSE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        echo "Installation Configuration:"
        echo "  Mode: $INSTALL_MODE"
        echo "  Platform: $PLATFORM"
        echo "  Extension ID: $EXTENSION_ID"
        echo "  Native Host: $NATIVE_HOST"
        echo "  Service Port: $SERVICE_PORT"
        echo "  QA Install Dir: $QA_INSTALL_DIR"
        echo "  Skip Chrome: $SKIP_CHROME"
        echo "  Skip Native: $SKIP_NATIVE"
        echo ""
    fi
    
    validate_prerequisites
    
    if [[ "$INSTALL_MODE" == "validate" ]]; then
        validate_installation
        exit 0
    fi
    
    # Confirm installation
    if [[ "$FORCE_INSTALL" == "false" ]] && [[ "$DRY_RUN" == "false" ]]; then
        echo ""
        log_warning "This will install CMPM-QA components to: $QA_INSTALL_DIR"
        read -p "Continue with installation? [y/N]: " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled by user"
            exit 0
        fi
    fi
    
    create_qa_directories
    install_framework_integration
    install_chrome_extension
    setup_native_messaging
    install_service_bridge
    validate_installation
    
    if [[ "$DRY_RUN" == "false" ]]; then
        show_installation_summary
    else
        log_info "[DRY RUN] Installation simulation completed"
    fi
}

# Run main function with all arguments
main "$@"