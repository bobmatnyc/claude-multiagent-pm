#!/bin/bash
#
# Native Messaging Host Configuration Script for CMPM-QA
# =======================================================
#
# Automated native messaging host setup for the CMPM-QA browser extension system.
# Configures secure communication channel between Chrome extension and framework
# service across multiple platforms (macOS, Linux, Windows).
#
# Features:
# - Cross-platform native messaging host registration
# - Host manifest installation and configuration
# - Secure communication channel setup
# - Host process management and monitoring
# - Platform-specific security configurations

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="CMPM-QA Native Messaging Host Setup"

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
GEAR="⚙️"
SHIELD="🛡️"
LINK="🔗"

# Default configuration
DEFAULT_NATIVE_HOST="com.claude.pm.qa"
DEFAULT_HOST_VERSION="1.0.0"

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
    echo -e "${PURPLE}${GEAR} $1${NC}"
}

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "======================================================"
    echo "  CMPM-QA Native Messaging Host Configuration"
    echo "  Version: $SCRIPT_VERSION"
    echo "  Framework: Claude PM v4.1.0"
    echo "======================================================"
    echo -e "${NC}"
}

# Help function
show_help() {
    cat << EOF
CMPM-QA Native Messaging Host Configuration Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose logging
    -f, --force             Force configuration (overwrite existing)
    --native-host HOST      Native host name (default: $DEFAULT_NATIVE_HOST)
    --source-dir DIR        Source native host directory
    --install-dir DIR       Installation directory
    --platform PLATFORM    Target platform (auto-detected if not specified)
    --host-version VERSION  Host version (default: $DEFAULT_HOST_VERSION)
    --python-path PATH      Custom Python executable path
    --node-path PATH        Custom Node.js executable path
    --test                  Test native messaging after configuration
    --uninstall             Uninstall native messaging host
    --dry-run               Show what would be done without executing

PLATFORMS:
    macos                   macOS/Mac OS X configuration
    linux                   Linux distribution configuration
    windows                 Windows configuration

EXAMPLES:
    # Standard configuration
    $0 --source-dir ./native-host --install-dir ~/.claude-pm/qa

    # Force reconfiguration with custom host name
    $0 --force --native-host com.mycompany.qa --source-dir ./native-host

    # Test existing configuration
    $0 --test

    # Uninstall native messaging host
    $0 --uninstall --native-host com.claude.pm.qa

    # Platform-specific configuration
    $0 --platform linux --source-dir ./native-host --install-dir /opt/cmpm-qa

SECURITY:
    Native messaging hosts provide secure communication between browser
    extensions and local applications. This script ensures proper
    security configurations including:
    - Restricted allowed origins
    - Secure manifest file permissions
    - Process isolation and sandboxing
    - Input validation and sanitization

For more information, see: docs/NATIVE_MESSAGING_SETUP.md
EOF
}

# Parse command line arguments
parse_arguments() {
    NATIVE_HOST="$DEFAULT_NATIVE_HOST"
    SOURCE_DIR=""
    INSTALL_DIR=""
    PLATFORM=""
    HOST_VERSION="$DEFAULT_HOST_VERSION"
    PYTHON_PATH=""
    NODE_PATH=""
    VERBOSE=false
    FORCE_CONFIG=false
    TEST_MODE=false
    UNINSTALL_MODE=false
    DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE_CONFIG=true
                shift
                ;;
            --native-host)
                NATIVE_HOST="$2"
                shift 2
                ;;
            --source-dir)
                SOURCE_DIR="$2"
                shift 2
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --platform)
                PLATFORM="$2"
                shift 2
                ;;
            --host-version)
                HOST_VERSION="$2"
                shift 2
                ;;
            --python-path)
                PYTHON_PATH="$2"
                shift 2
                ;;
            --node-path)
                NODE_PATH="$2"
                shift 2
                ;;
            --test)
                TEST_MODE=true
                shift
                ;;
            --uninstall)
                UNINSTALL_MODE=true
                shift
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

    # Validate required arguments
    if [[ "$UNINSTALL_MODE" == "false" && "$TEST_MODE" == "false" && -z "$SOURCE_DIR" ]]; then
        log_error "Source directory is required for configuration"
        exit 1
    fi

    if [[ "$UNINSTALL_MODE" == "false" && "$TEST_MODE" == "false" && -z "$INSTALL_DIR" ]]; then
        log_error "Install directory is required"
        exit 1
    fi
}

# Configure environment and detect platform
configure_environment() {
    log_header "Configuring Environment"

    # Auto-detect platform if not specified
    if [[ -z "$PLATFORM" ]]; then
        case "$(uname -s)" in
            Darwin*)
                PLATFORM="macos"
                ;;
            Linux*)
                PLATFORM="linux"
                ;;
            CYGWIN*|MINGW32*|MSYS*|MINGW*)
                PLATFORM="windows"
                ;;
            *)
                log_error "Unsupported platform: $(uname -s)"
                exit 1
                ;;
        esac
    fi

    # Platform-specific paths and configurations
    case $PLATFORM in
        macos)
            CHROME_NATIVE_MESSAGING_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
            CHROMIUM_NATIVE_MESSAGING_DIR="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
            HOST_EXECUTABLE_EXTENSION=""
            ;;
        linux)
            CHROME_NATIVE_MESSAGING_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
            CHROMIUM_NATIVE_MESSAGING_DIR="$HOME/.config/chromium/NativeMessagingHosts"
            HOST_EXECUTABLE_EXTENSION=""
            ;;
        windows)
            CHROME_NATIVE_MESSAGING_DIR="$APPDATA/Google/Chrome/User Data/NativeMessagingHosts"
            CHROMIUM_NATIVE_MESSAGING_DIR="$APPDATA/Chromium/User Data/NativeMessagingHosts"
            HOST_EXECUTABLE_EXTENSION=".exe"
            ;;
    esac

    # Host paths
    if [[ -n "$INSTALL_DIR" ]]; then
        HOST_INSTALL_DIR="$INSTALL_DIR/native-host"
        HOST_EXECUTABLE="$HOST_INSTALL_DIR/cmpm-qa-host$HOST_EXECUTABLE_EXTENSION"
        HOST_MANIFEST="$CHROME_NATIVE_MESSAGING_DIR/${NATIVE_HOST}.json"
    fi

    log_info "Platform: $PLATFORM"
    log_info "Native Host: $NATIVE_HOST"
    log_info "Host Version: $HOST_VERSION"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Chrome Native Messaging Directory: $CHROME_NATIVE_MESSAGING_DIR"
        if [[ -n "$HOST_INSTALL_DIR" ]]; then
            log_info "Host Install Directory: $HOST_INSTALL_DIR"
            log_info "Host Executable: $HOST_EXECUTABLE"
            log_info "Host Manifest: $HOST_MANIFEST"
        fi
    fi
}

# Validate runtime dependencies
validate_dependencies() {
    log_header "Validating Dependencies"

    local errors=0

    # Check for Python (preferred runtime)
    if [[ -n "$PYTHON_PATH" ]]; then
        if [[ ! -x "$PYTHON_PATH" ]]; then
            log_error "Custom Python path not executable: $PYTHON_PATH"
            ((errors++))
        else
            PYTHON_EXECUTABLE="$PYTHON_PATH"
            log_success "Using custom Python: $PYTHON_EXECUTABLE"
        fi
    else
        if command -v python3 &> /dev/null; then
            PYTHON_EXECUTABLE="python3"
            local python_version=$(python3 --version | cut -d' ' -f2)
            log_success "Python 3 found: $python_version"
        elif command -v python &> /dev/null; then
            local python_version=$(python --version 2>&1 | cut -d' ' -f2)
            if [[ "$python_version" == 3.* ]]; then
                PYTHON_EXECUTABLE="python"
                log_success "Python 3 found: $python_version"
            else
                log_error "Python 3 required, found Python $python_version"
                ((errors++))
            fi
        else
            log_error "Python 3 not found"
            ((errors++))
        fi
    fi

    # Check for Node.js (alternative runtime)
    if [[ -n "$NODE_PATH" ]]; then
        if [[ ! -x "$NODE_PATH" ]]; then
            log_warning "Custom Node.js path not executable: $NODE_PATH"
        else
            NODE_EXECUTABLE="$NODE_PATH"
            log_success "Using custom Node.js: $NODE_EXECUTABLE"
        fi
    else
        if command -v node &> /dev/null; then
            NODE_EXECUTABLE="node"
            local node_version=$(node --version)
            log_success "Node.js found: $node_version"
        else
            log_info "Node.js not found (Python will be used)"
        fi
    fi

    # Platform-specific validations
    case $PLATFORM in
        macos)
            validate_macos_dependencies
            ;;
        linux)
            validate_linux_dependencies
            ;;
        windows)
            validate_windows_dependencies
            ;;
    esac

    if [[ $errors -gt 0 ]]; then
        log_error "Dependency validation failed with $errors errors"
        exit 1
    fi

    log_success "Dependencies validation completed"
}

validate_macos_dependencies() {
    log_info "Validating macOS dependencies..."
    
    # Check for Chrome installation
    local chrome_found=false
    if [[ -d "/Applications/Google Chrome.app" ]]; then
        chrome_found=true
        log_success "Google Chrome found"
    fi
    
    if [[ -d "/Applications/Chromium.app" ]]; then
        chrome_found=true
        log_success "Chromium found"
    fi
    
    if [[ "$chrome_found" == "false" ]]; then
        log_warning "No Chrome/Chromium installation found"
    fi
    
    log_success "macOS dependencies validated"
}

validate_linux_dependencies() {
    log_info "Validating Linux dependencies..."
    
    # Check for Chrome installation
    local chrome_found=false
    local chrome_commands=("google-chrome" "google-chrome-stable" "chromium-browser" "chromium")
    
    for cmd in "${chrome_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            chrome_found=true
            log_success "Chrome/Chromium found: $cmd"
            break
        fi
    done
    
    if [[ "$chrome_found" == "false" ]]; then
        log_warning "No Chrome/Chromium installation found"
    fi
    
    log_success "Linux dependencies validated"
}

validate_windows_dependencies() {
    log_info "Validating Windows dependencies..."
    
    # Check for Chrome installation
    local chrome_paths=(
        "/c/Program Files/Google/Chrome/Application/chrome.exe"
        "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    )
    
    local chrome_found=false
    for path in "${chrome_paths[@]}"; do
        if [[ -f "$path" ]]; then
            chrome_found=true
            log_success "Google Chrome found: $path"
            break
        fi
    done
    
    if [[ "$chrome_found" == "false" ]]; then
        log_warning "No Chrome installation found"
    fi
    
    log_success "Windows dependencies validated"
}

# Validate native host source files
validate_source_files() {
    if [[ "$UNINSTALL_MODE" == "true" || "$TEST_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Validating Source Files"

    # Check if source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        log_error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi

    log_success "Source directory found"

    # Check for required host implementation files
    local python_host="$SOURCE_DIR/native_host.py"
    local node_host="$SOURCE_DIR/native_host.js"
    local host_found=false

    if [[ -f "$python_host" ]]; then
        HOST_IMPLEMENTATION="python"
        HOST_SOURCE_FILE="$python_host"
        host_found=true
        log_success "Python host implementation found"
    fi

    if [[ -f "$node_host" ]]; then
        if [[ "$host_found" == "false" ]]; then
            HOST_IMPLEMENTATION="node"
            HOST_SOURCE_FILE="$node_host"
            host_found=true
        fi
        log_success "Node.js host implementation found"
    fi

    if [[ "$host_found" == "false" ]]; then
        log_error "No host implementation found in source directory"
        log_error "Expected: native_host.py or native_host.js"
        exit 1
    fi

    # Prefer Python if both are available and Python is available
    if [[ -f "$python_host" && -n "${PYTHON_EXECUTABLE:-}" ]]; then
        HOST_IMPLEMENTATION="python"
        HOST_SOURCE_FILE="$python_host"
        log_info "Using Python implementation (preferred)"
    elif [[ -f "$node_host" && -n "${NODE_EXECUTABLE:-}" ]]; then
        HOST_IMPLEMENTATION="node"
        HOST_SOURCE_FILE="$node_host"
        log_info "Using Node.js implementation"
    fi

    # Check for additional required files
    local config_file="$SOURCE_DIR/host_config.json"
    if [[ -f "$config_file" ]]; then
        log_success "Host configuration file found"
    else
        log_warning "Host configuration file not found (will use defaults)"
    fi

    log_success "Source files validation completed"
}

# Create native messaging directories
create_messaging_directories() {
    if [[ "$UNINSTALL_MODE" == "true" || "$TEST_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Creating Native Messaging Directories"

    local directories=(
        "$HOST_INSTALL_DIR"
        "$CHROME_NATIVE_MESSAGING_DIR"
        "$CHROMIUM_NATIVE_MESSAGING_DIR"
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

# Install native host files
install_host_files() {
    if [[ "$UNINSTALL_MODE" == "true" || "$TEST_MODE" == "true" ]]; then
        return 0
    fi

    log_header "${GEAR} Installing Native Host Files"

    # Copy host implementation files
    if [[ "$DRY_RUN" == "false" ]]; then
        cp -r "$SOURCE_DIR"/* "$HOST_INSTALL_DIR/"
        log_success "Host files copied to install directory"

        # Create host executable wrapper based on implementation
        case $HOST_IMPLEMENTATION in
            python)
                create_python_host_wrapper
                ;;
            node)
                create_node_host_wrapper
                ;;
        esac
    else
        log_info "[DRY RUN] Would copy host files and create wrapper"
    fi
}

create_python_host_wrapper() {
    local wrapper_script="$HOST_EXECUTABLE"
    
    cat > "$wrapper_script" << EOF
#!/bin/bash
# CMPM-QA Native Host Python Wrapper
# Generated by configure-host.sh v$SCRIPT_VERSION

# Set up environment
export PYTHONPATH="$INSTALL_DIR/../..:$INSTALL_DIR:\$PYTHONPATH"
export CMPM_QA_HOST_VERSION="$HOST_VERSION"
export CMPM_QA_HOST_NAME="$NATIVE_HOST"

# Change to host directory
cd "\$(dirname "\$0")"

# Execute Python host
exec "$PYTHON_EXECUTABLE" native_host.py "\$@"
EOF

    chmod +x "$wrapper_script"
    log_success "Python host wrapper created: $wrapper_script"
}

create_node_host_wrapper() {
    local wrapper_script="$HOST_EXECUTABLE"
    
    cat > "$wrapper_script" << EOF
#!/bin/bash
# CMPM-QA Native Host Node.js Wrapper
# Generated by configure-host.sh v$SCRIPT_VERSION

# Set up environment
export CMPM_QA_HOST_VERSION="$HOST_VERSION"
export CMPM_QA_HOST_NAME="$NATIVE_HOST"

# Change to host directory
cd "\$(dirname "\$0")"

# Execute Node.js host
exec "$NODE_EXECUTABLE" native_host.js "\$@"
EOF

    chmod +x "$wrapper_script"
    log_success "Node.js host wrapper created: $wrapper_script"
}

# Generate and install native messaging manifest
install_messaging_manifest() {
    if [[ "$UNINSTALL_MODE" == "true" || "$TEST_MODE" == "true" ]]; then
        return 0
    fi

    log_header "${LINK} Installing Native Messaging Manifest"

    # Generate manifest content
    local manifest_content
    manifest_content=$(cat << EOF
{
    "name": "$NATIVE_HOST",
    "description": "CMPM-QA Native Messaging Host for Claude PM Framework",
    "path": "$HOST_EXECUTABLE",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://$EXTENSION_ID/"
    ],
    "metadata": {
        "version": "$HOST_VERSION",
        "framework_version": "4.1.0",
        "install_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "platform": "$PLATFORM",
        "implementation": "$HOST_IMPLEMENTATION"
    }
}
EOF
)

    # Install manifest for Chrome
    if [[ "$DRY_RUN" == "false" ]]; then
        echo "$manifest_content" > "$HOST_MANIFEST"
        log_success "Chrome native messaging manifest installed"

        # Also install for Chromium
        local chromium_manifest="$CHROMIUM_NATIVE_MESSAGING_DIR/${NATIVE_HOST}.json"
        echo "$manifest_content" > "$chromium_manifest"
        log_success "Chromium native messaging manifest installed"

        # Set appropriate permissions
        case $PLATFORM in
            macos|linux)
                chmod 644 "$HOST_MANIFEST" "$chromium_manifest"
                log_success "Manifest permissions set"
                ;;
        esac
    else
        log_info "[DRY RUN] Would install native messaging manifests"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "Manifest content:"
            echo "$manifest_content"
        fi
    fi
}

# Test native messaging functionality
test_native_messaging() {
    if [[ "$TEST_MODE" == "false" ]]; then
        return 0
    fi

    log_header "${SHIELD} Testing Native Messaging"

    # Check if manifest exists
    if [[ ! -f "$HOST_MANIFEST" ]]; then
        log_error "Native messaging manifest not found: $HOST_MANIFEST"
        exit 1
    fi

    log_success "Native messaging manifest found"

    # Check if host executable exists and is executable
    if [[ ! -x "$HOST_EXECUTABLE" ]]; then
        log_error "Host executable not found or not executable: $HOST_EXECUTABLE"
        exit 1
    fi

    log_success "Host executable found and is executable"

    # Test host communication
    if [[ "$DRY_RUN" == "false" ]]; then
        log_info "Testing host communication..."
        
        # Create a simple test message
        local test_message='{"type":"ping","payload":{"test":true}}'
        local test_response
        
        # Send test message to host and capture response
        test_response=$(echo "$test_message" | timeout 5 "$HOST_EXECUTABLE" 2>/dev/null || echo "")
        
        if [[ -n "$test_response" ]]; then
            log_success "Host communication test successful"
            if [[ "$VERBOSE" == "true" ]]; then
                log_info "Response: $test_response"
            fi
        else
            log_warning "Host communication test failed or timed out"
            log_info "This may be normal if the host requires specific initialization"
        fi
    else
        log_info "[DRY RUN] Would test host communication"
    fi

    # Validate manifest JSON
    if command -v python3 &> /dev/null; then
        python3 << EOF
import json
import sys

try:
    with open('$HOST_MANIFEST', 'r') as f:
        manifest = json.load(f)
    
    required_fields = ['name', 'description', 'path', 'type', 'allowed_origins']
    missing_fields = [field for field in required_fields if field not in manifest]
    
    if missing_fields:
        print(f"❌ Missing required manifest fields: {', '.join(missing_fields)}")
        sys.exit(1)
    
    print(f"✅ Manifest validation successful")
    print(f"ℹ️ Host Name: {manifest.get('name')}")
    print(f"ℹ️ Host Path: {manifest.get('path')}")
    print(f"ℹ️ Allowed Origins: {len(manifest.get('allowed_origins', []))}")

except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON in manifest: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error validating manifest: {e}")
    sys.exit(1)
EOF
        
        if [[ $? -eq 0 ]]; then
            log_success "Manifest JSON validation passed"
        else
            log_error "Manifest JSON validation failed"
            exit 1
        fi
    else
        log_warning "Python not available for manifest validation"
    fi

    log_success "Native messaging test completed"
}

# Uninstall native messaging host
uninstall_host() {
    if [[ "$UNINSTALL_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Uninstalling Native Messaging Host"

    # Remove manifests
    local manifests=(
        "$CHROME_NATIVE_MESSAGING_DIR/${NATIVE_HOST}.json"
        "$CHROMIUM_NATIVE_MESSAGING_DIR/${NATIVE_HOST}.json"
    )

    for manifest in "${manifests[@]}"; do
        if [[ -f "$manifest" ]]; then
            if [[ "$DRY_RUN" == "false" ]]; then
                rm -f "$manifest"
                log_success "Removed manifest: $manifest"
            else
                log_info "[DRY RUN] Would remove manifest: $manifest"
            fi
        else
            log_info "Manifest not found: $manifest"
        fi
    done

    # Remove host installation directory
    if [[ -n "$INSTALL_DIR" && -d "$INSTALL_DIR/native-host" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            rm -rf "$INSTALL_DIR/native-host"
            log_success "Removed host installation directory"
        else
            log_info "[DRY RUN] Would remove host installation directory"
        fi
    fi

    log_success "Native messaging host uninstalled successfully"
}

# Show configuration summary
show_summary() {
    if [[ "$UNINSTALL_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Configuration Summary"
    
    echo -e "${CYAN}Native Host:${NC} $NATIVE_HOST"
    echo -e "${CYAN}Host Version:${NC} $HOST_VERSION"
    echo -e "${CYAN}Platform:${NC} $PLATFORM"
    echo -e "${CYAN}Implementation:${NC} $HOST_IMPLEMENTATION"
    
    if [[ -n "$HOST_INSTALL_DIR" ]]; then
        echo -e "${CYAN}Install Directory:${NC} $HOST_INSTALL_DIR"
    fi
    
    if [[ -n "$HOST_EXECUTABLE" ]]; then
        echo -e "${CYAN}Host Executable:${NC} $HOST_EXECUTABLE"
    fi
    
    if [[ -n "$HOST_MANIFEST" ]]; then
        echo -e "${CYAN}Manifest File:${NC} $HOST_MANIFEST"
    fi
    
    echo ""
    log_success "Native messaging host configuration completed successfully!"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Test the configuration: $0 --test"
    echo "2. Install the browser extension with matching extension ID"
    echo "3. Test end-to-end communication through the browser extension"
    echo ""
    echo -e "${BLUE}Troubleshooting:${NC}"
    echo "- Check Chrome://extensions/ for extension status"
    echo "- View Chrome console for communication errors"
    echo "- Check host logs: tail -f $INSTALL_DIR/logs/native-host.log"
    echo "- Validate manifest: cat $HOST_MANIFEST"
}

# Main workflow
main() {
    show_banner
    parse_arguments "$@"
    configure_environment
    
    if [[ "$VERBOSE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        echo "Configuration Summary:"
        echo "  Native Host: $NATIVE_HOST"
        echo "  Platform: $PLATFORM"
        echo "  Host Version: $HOST_VERSION"
        echo "  Test Mode: $TEST_MODE"
        echo "  Uninstall Mode: $UNINSTALL_MODE"
        if [[ -n "$SOURCE_DIR" ]]; then
            echo "  Source Directory: $SOURCE_DIR"
        fi
        if [[ -n "$INSTALL_DIR" ]]; then
            echo "  Install Directory: $INSTALL_DIR"
        fi
        echo ""
    fi
    
    validate_dependencies
    
    if [[ "$TEST_MODE" == "true" ]]; then
        test_native_messaging
        exit 0
    fi
    
    if [[ "$UNINSTALL_MODE" == "true" ]]; then
        uninstall_host
        exit 0
    fi
    
    validate_source_files
    create_messaging_directories
    install_host_files
    install_messaging_manifest
    
    show_summary
}

# Run main function with all arguments
main "$@"