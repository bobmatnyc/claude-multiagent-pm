#!/bin/bash
#
# Chrome Extension Installation Script for CMPM-QA
# =================================================
#
# Automated Chrome extension installation and configuration for the CMPM-QA
# browser testing system. Supports both development and production deployments
# with comprehensive platform support.
#
# Features:
# - Cross-platform Chrome extension installation
# - Developer mode configuration for testing
# - Chrome Web Store preparation for production
# - Extension update and maintenance automation
# - Security validation and manifest verification

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="CMPM-QA Chrome Extension Setup"

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
BROWSER="🌐"
EXTENSION="🧩"
GEAR="⚙️"

# Default configuration
DEFAULT_EXTENSION_ID="cmpm-qa-extension"
DEFAULT_VERSION="1.0.0"

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
    echo -e "${PURPLE}${BROWSER} $1${NC}"
}

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "======================================================"
    echo "  CMPM-QA Chrome Extension Installation"
    echo "  Version: $SCRIPT_VERSION"
    echo "  Framework: Claude PM v4.1.0"
    echo "======================================================"
    echo -e "${NC}"
}

# Help function
show_help() {
    cat << EOF
CMPM-QA Chrome Extension Installation Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose logging
    -f, --force             Force installation (overwrite existing)
    --extension-id ID       Extension ID (default: $DEFAULT_EXTENSION_ID)
    --source-dir DIR        Source extension directory
    --install-dir DIR       Installation base directory
    --version VERSION       Extension version (default: $DEFAULT_VERSION)
    --dev-mode              Install in development mode
    --production            Prepare for production/Chrome Web Store
    --update                Update existing extension
    --uninstall             Uninstall extension
    --dry-run               Show what would be done without executing

INSTALLATION MODES:
    Development Mode:
        - Installs extension in unpacked format
        - Enables Chrome developer mode
        - Suitable for testing and development

    Production Mode:
        - Packages extension for Chrome Web Store
        - Validates manifest and security requirements
        - Creates distribution-ready package

EXAMPLES:
    # Development installation
    $0 --dev-mode --source-dir ./extension --install-dir ~/.claude-pm/qa

    # Production packaging
    $0 --production --source-dir ./extension --version 1.2.0

    # Update existing extension
    $0 --update --extension-id cmpm-qa-ext --version 1.1.0

    # Uninstall extension
    $0 --uninstall --extension-id cmpm-qa-ext

For more information, see: docs/CHROME_EXTENSION_DEPLOYMENT.md
EOF
}

# Parse command line arguments
parse_arguments() {
    EXTENSION_ID="$DEFAULT_EXTENSION_ID"
    SOURCE_DIR=""
    INSTALL_DIR=""
    EXTENSION_VERSION="$DEFAULT_VERSION"
    VERBOSE=false
    FORCE_INSTALL=false
    DEV_MODE=false
    PRODUCTION_MODE=false
    UPDATE_MODE=false
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
                FORCE_INSTALL=true
                shift
                ;;
            --extension-id)
                EXTENSION_ID="$2"
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
            --version)
                EXTENSION_VERSION="$2"
                shift 2
                ;;
            --dev-mode)
                DEV_MODE=true
                shift
                ;;
            --production)
                PRODUCTION_MODE=true
                shift
                ;;
            --update)
                UPDATE_MODE=true
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
    if [[ "$UNINSTALL_MODE" == "false" && -z "$SOURCE_DIR" ]]; then
        log_error "Source directory is required for installation"
        exit 1
    fi

    if [[ "$UNINSTALL_MODE" == "false" && -z "$INSTALL_DIR" ]]; then
        log_error "Install directory is required"
        exit 1
    fi
}

# Configure environment and paths
configure_environment() {
    log_header "Configuring Environment"

    # Detect platform
    case "$(uname -s)" in
        Darwin*)
            PLATFORM="macos"
            CHROME_CONFIG_DIR="$HOME/Library/Application Support/Google/Chrome"
            CHROME_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/Default/Extensions"
            CHROME_EXTERNAL_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/External Extensions"
            CHROME_PREFERENCES="$CHROME_CONFIG_DIR/Default/Preferences"
            ;;
        Linux*)
            PLATFORM="linux"
            CHROME_CONFIG_DIR="$HOME/.config/google-chrome"
            CHROME_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/Default/Extensions"
            CHROME_EXTERNAL_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/External Extensions"
            CHROME_PREFERENCES="$CHROME_CONFIG_DIR/Default/Preferences"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            PLATFORM="windows"
            CHROME_CONFIG_DIR="$APPDATA/Google/Chrome/User Data"
            CHROME_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/Default/Extensions"
            CHROME_EXTERNAL_EXTENSIONS_DIR="$CHROME_CONFIG_DIR/External Extensions"
            CHROME_PREFERENCES="$CHROME_CONFIG_DIR/Default/Preferences"
            ;;
        *)
            log_error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac

    # Extension paths
    if [[ -n "$INSTALL_DIR" ]]; then
        EXTENSION_INSTALL_DIR="$INSTALL_DIR/extension"
        EXTENSION_BUILD_DIR="$INSTALL_DIR/build"
        EXTENSION_DIST_DIR="$INSTALL_DIR/dist"
    fi

    EXTENSION_TARGET_DIR="$CHROME_EXTENSIONS_DIR/$EXTENSION_ID"

    log_info "Platform: $PLATFORM"
    log_info "Extension ID: $EXTENSION_ID"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Chrome Config Directory: $CHROME_CONFIG_DIR"
        log_info "Chrome Extensions Directory: $CHROME_EXTENSIONS_DIR"
        log_info "Extension Target Directory: $EXTENSION_TARGET_DIR"
        if [[ -n "$EXTENSION_INSTALL_DIR" ]]; then
            log_info "Extension Install Directory: $EXTENSION_INSTALL_DIR"
        fi
    fi
}

# Validate Chrome installation and prerequisites
validate_chrome() {
    log_header "Validating Chrome Installation"

    # Check if Chrome is installed
    local chrome_executable=""
    case $PLATFORM in
        macos)
            if [[ -d "/Applications/Google Chrome.app" ]]; then
                chrome_executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            fi
            ;;
        linux)
            if command -v google-chrome &> /dev/null; then
                chrome_executable="google-chrome"
            elif command -v google-chrome-stable &> /dev/null; then
                chrome_executable="google-chrome-stable"
            elif command -v chromium-browser &> /dev/null; then
                chrome_executable="chromium-browser"
            fi
            ;;
        windows)
            if [[ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]]; then
                chrome_executable="/c/Program Files/Google/Chrome/Application/chrome.exe"
            elif [[ -f "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" ]]; then
                chrome_executable="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            fi
            ;;
    esac

    if [[ -z "$chrome_executable" ]]; then
        log_error "Google Chrome not found"
        log_error "Please install Google Chrome from https://www.google.com/chrome/"
        exit 1
    fi

    log_success "Chrome executable found: $chrome_executable"
    CHROME_EXECUTABLE="$chrome_executable"

    # Check if Chrome directories exist
    if [[ ! -d "$CHROME_CONFIG_DIR" ]]; then
        log_warning "Chrome configuration directory not found"
        log_info "Please run Chrome at least once to create profile"
        if [[ "$FORCE_INSTALL" == "false" ]]; then
            exit 1
        fi
    else
        log_success "Chrome configuration directory found"
    fi

    # Create Chrome extensions directory if it doesn't exist
    if [[ ! -d "$CHROME_EXTENSIONS_DIR" && "$DRY_RUN" == "false" ]]; then
        mkdir -p "$CHROME_EXTENSIONS_DIR"
        log_success "Created Chrome extensions directory"
    fi
}

# Validate extension source and manifest
validate_extension_source() {
    if [[ "$UNINSTALL_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Validating Extension Source"

    # Check if source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        log_error "Extension source directory not found: $SOURCE_DIR"
        exit 1
    fi

    log_success "Extension source directory found"

    # Check for manifest.json
    local manifest_file="$SOURCE_DIR/manifest.json"
    if [[ ! -f "$manifest_file" ]]; then
        log_error "Extension manifest not found: $manifest_file"
        exit 1
    fi

    log_success "Extension manifest found"

    # Validate manifest structure
    if command -v python3 &> /dev/null; then
        python3 << EOF
import json
import sys

try:
    with open('$manifest_file', 'r') as f:
        manifest = json.load(f)
    
    # Check required fields
    required_fields = ['manifest_version', 'name', 'version']
    missing_fields = [field for field in required_fields if field not in manifest]
    
    if missing_fields:
        print(f"❌ Missing required manifest fields: {', '.join(missing_fields)}")
        sys.exit(1)
    
    # Validate manifest version
    if manifest.get('manifest_version') not in [2, 3]:
        print(f"❌ Unsupported manifest version: {manifest.get('manifest_version')}")
        sys.exit(1)
    
    # Extract extension info
    print(f"✅ Extension Name: {manifest.get('name')}")
    print(f"✅ Extension Version: {manifest.get('version')}")
    print(f"✅ Manifest Version: {manifest.get('manifest_version')}")
    
    # Check for permissions
    permissions = manifest.get('permissions', [])
    if permissions:
        print(f"ℹ️ Permissions: {', '.join(permissions)}")
    
    # Check for content scripts
    content_scripts = manifest.get('content_scripts', [])
    if content_scripts:
        print(f"ℹ️ Content Scripts: {len(content_scripts)} defined")
    
    # Check for background scripts
    background = manifest.get('background', {})
    if background:
        print(f"ℹ️ Background Script: {background.get('service_worker', background.get('scripts', 'defined'))}")

except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON in manifest: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error validating manifest: {e}")
    sys.exit(1)
EOF
        
        if [[ $? -ne 0 ]]; then
            log_error "Manifest validation failed"
            exit 1
        fi
    else
        log_warning "Python not available for manifest validation"
    fi

    # Check for required extension files
    local required_files=("manifest.json")
    local recommended_files=("icon.png" "background.js" "content.js")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$SOURCE_DIR/$file" ]]; then
            log_error "Required extension file missing: $file"
            exit 1
        fi
    done

    for file in "${recommended_files[@]}"; do
        if [[ -f "$SOURCE_DIR/$file" ]]; then
            log_success "Found recommended file: $file"
        fi
    done

    log_success "Extension source validation completed"
}

# Copy and prepare extension files
prepare_extension_files() {
    if [[ "$UNINSTALL_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Preparing Extension Files"

    # Create extension installation directory
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$EXTENSION_INSTALL_DIR"
        mkdir -p "$EXTENSION_BUILD_DIR"
        log_success "Created extension directories"
    else
        log_info "[DRY RUN] Would create extension directories"
    fi

    # Copy extension files
    if [[ "$DRY_RUN" == "false" ]]; then
        cp -r "$SOURCE_DIR"/* "$EXTENSION_INSTALL_DIR/"
        log_success "Extension files copied to install directory"
    else
        log_info "[DRY RUN] Would copy extension files"
    fi

    # Update manifest with correct extension ID and version
    local manifest_file="$EXTENSION_INSTALL_DIR/manifest.json"
    if [[ "$DRY_RUN" == "false" && -f "$manifest_file" ]]; then
        # Update extension version
        python3 << EOF
import json

with open('$manifest_file', 'r') as f:
    manifest = json.load(f)

# Update version if specified
if '$EXTENSION_VERSION' != '$DEFAULT_VERSION':
    manifest['version'] = '$EXTENSION_VERSION'

# Add framework-specific metadata
if 'cmpm_qa' not in manifest:
    manifest['cmpm_qa'] = {}

manifest['cmpm_qa'].update({
    'framework_version': '4.1.0',
    'install_date': '$(date -u +"%Y-%m-%dT%H:%M:%SZ")',
    'install_mode': '${"development" if [[ "$DEV_MODE" == "true" ]]; then echo "development"; else echo "production"; fi}',
    'platform': '$PLATFORM'
})

with open('$manifest_file', 'w') as f:
    json.dump(manifest, f, indent=2)
EOF
        log_success "Manifest updated with framework metadata"
    elif [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update manifest file"
    fi
}

# Install extension in development mode
install_development_extension() {
    if [[ "$DEV_MODE" == "false" && "$PRODUCTION_MODE" == "false" ]]; then
        DEV_MODE=true  # Default to development mode
    fi

    if [[ "$DEV_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Installing Extension in Development Mode"

    # Create symlink or copy to Chrome extensions directory
    if [[ "$DRY_RUN" == "false" ]]; then
        # Remove existing installation if present
        if [[ -d "$EXTENSION_TARGET_DIR" ]]; then
            if [[ "$FORCE_INSTALL" == "true" ]]; then
                rm -rf "$EXTENSION_TARGET_DIR"
                log_success "Removed existing extension installation"
            else
                log_error "Extension already installed at $EXTENSION_TARGET_DIR"
                log_error "Use --force to overwrite or --update to update"
                exit 1
            fi
        fi

        # Create extension directory with version
        local extension_version_dir="$EXTENSION_TARGET_DIR/$EXTENSION_VERSION"
        mkdir -p "$extension_version_dir"
        
        # Copy extension files to Chrome directory
        cp -r "$EXTENSION_INSTALL_DIR"/* "$extension_version_dir/"
        log_success "Extension installed to Chrome extensions directory"

        # Create external extension manifest for automatic loading
        if [[ ! -d "$CHROME_EXTERNAL_EXTENSIONS_DIR" ]]; then
            mkdir -p "$CHROME_EXTERNAL_EXTENSIONS_DIR"
        fi

        local external_manifest="$CHROME_EXTERNAL_EXTENSIONS_DIR/${EXTENSION_ID}.json"
        cat > "$external_manifest" << EOF
{
    "external_update_url": "https://clients2.google.com/service/update2/crx",
    "external_version": "$EXTENSION_VERSION"
}
EOF
        log_success "External extension manifest created"

    else
        log_info "[DRY RUN] Would install extension in development mode"
    fi

    # Instructions for manual enabling
    echo ""
    log_info "Manual Steps Required:"
    echo "1. Open Chrome and navigate to: chrome://extensions/"
    echo "2. Enable 'Developer mode' in the top right"
    echo "3. Click 'Load unpacked' and select: $EXTENSION_TARGET_DIR/$EXTENSION_VERSION"
    echo "4. The extension should now be loaded and visible in the extensions list"
    echo ""
}

# Prepare extension for production/Chrome Web Store
prepare_production_extension() {
    if [[ "$PRODUCTION_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Preparing Extension for Production"

    # Create distribution directory
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$EXTENSION_DIST_DIR"
        log_success "Created distribution directory"
    else
        log_info "[DRY RUN] Would create distribution directory"
    fi

    # Package extension as .crx file
    if [[ "$DRY_RUN" == "false" ]]; then
        local crx_file="$EXTENSION_DIST_DIR/${EXTENSION_ID}-${EXTENSION_VERSION}.crx"
        local zip_file="$EXTENSION_DIST_DIR/${EXTENSION_ID}-${EXTENSION_VERSION}.zip"

        # Create ZIP file for Chrome Web Store
        cd "$EXTENSION_INSTALL_DIR"
        zip -r "$zip_file" ./* -x ".*" "node_modules/*" "src/*" "*.md"
        log_success "Created ZIP package: $zip_file"

        # Create manifest for distribution
        local dist_manifest="$EXTENSION_DIST_DIR/distribution-manifest.json"
        cat > "$dist_manifest" << EOF
{
    "extension_id": "$EXTENSION_ID",
    "version": "$EXTENSION_VERSION",
    "package_zip": "$(basename "$zip_file")",
    "created_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "platform": "$PLATFORM",
    "framework_version": "4.1.0",
    "chrome_web_store_ready": true,
    "files": {
        "zip_package": "$(basename "$zip_file")",
        "size_bytes": $(stat -f%z "$zip_file" 2>/dev/null || stat -c%s "$zip_file" 2>/dev/null || echo 0)
    }
}
EOF
        log_success "Created distribution manifest"

        echo ""
        log_success "Production package created successfully!"
        echo "ZIP file for Chrome Web Store: $zip_file"
        echo "Distribution manifest: $dist_manifest"
        echo ""
        echo "Next steps for Chrome Web Store submission:"
        echo "1. Go to: https://chrome.google.com/webstore/devconsole/"
        echo "2. Upload the ZIP file: $zip_file"
        echo "3. Fill in the store listing details"
        echo "4. Submit for review"
    else
        log_info "[DRY RUN] Would create production package"
    fi
}

# Update existing extension
update_extension() {
    if [[ "$UPDATE_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Updating Existing Extension"

    # Check if extension is currently installed
    if [[ ! -d "$EXTENSION_TARGET_DIR" ]]; then
        log_error "Extension not found for update: $EXTENSION_ID"
        log_info "Use installation mode instead of update mode"
        exit 1
    fi

    log_success "Found existing extension installation"

    # Backup current version
    if [[ "$DRY_RUN" == "false" ]]; then
        local backup_dir="$EXTENSION_TARGET_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        cp -r "$EXTENSION_TARGET_DIR" "$backup_dir"
        log_success "Created backup: $backup_dir"
    else
        log_info "[DRY RUN] Would create backup of existing extension"
    fi

    # Proceed with installation (which will overwrite)
    FORCE_INSTALL=true
    install_development_extension
}

# Uninstall extension
uninstall_extension() {
    if [[ "$UNINSTALL_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Uninstalling Extension"

    # Remove from Chrome extensions directory
    if [[ -d "$EXTENSION_TARGET_DIR" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            rm -rf "$EXTENSION_TARGET_DIR"
            log_success "Removed extension from Chrome directory"
        else
            log_info "[DRY RUN] Would remove extension from Chrome directory"
        fi
    else
        log_warning "Extension not found in Chrome directory: $EXTENSION_TARGET_DIR"
    fi

    # Remove external extension manifest
    local external_manifest="$CHROME_EXTERNAL_EXTENSIONS_DIR/${EXTENSION_ID}.json"
    if [[ -f "$external_manifest" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            rm -f "$external_manifest"
            log_success "Removed external extension manifest"
        else
            log_info "[DRY RUN] Would remove external extension manifest"
        fi
    fi

    # Remove installation directory
    if [[ -n "$INSTALL_DIR" && -d "$EXTENSION_INSTALL_DIR" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            rm -rf "$EXTENSION_INSTALL_DIR"
            log_success "Removed extension installation directory"
        else
            log_info "[DRY RUN] Would remove installation directory"
        fi
    fi

    echo ""
    log_success "Extension uninstalled successfully!"
    echo ""
    echo "Manual Steps:"
    echo "1. Open Chrome and navigate to: chrome://extensions/"
    echo "2. Find the extension in the list and click 'Remove'"
    echo "3. Confirm removal in the dialog"
}

# Show installation summary
show_summary() {
    if [[ "$UNINSTALL_MODE" == "true" ]]; then
        return 0
    fi

    log_header "Installation Summary"
    
    echo -e "${CYAN}Extension ID:${NC} $EXTENSION_ID"
    echo -e "${CYAN}Version:${NC} $EXTENSION_VERSION"
    echo -e "${CYAN}Platform:${NC} $PLATFORM"
    echo -e "${CYAN}Install Mode:${NC} $(if [[ "$DEV_MODE" == "true" ]]; then echo "Development"; else echo "Production"; fi)"
    
    if [[ -n "$EXTENSION_INSTALL_DIR" ]]; then
        echo -e "${CYAN}Install Directory:${NC} $EXTENSION_INSTALL_DIR"
    fi
    
    if [[ "$DEV_MODE" == "true" ]]; then
        echo -e "${CYAN}Chrome Extension Path:${NC} $EXTENSION_TARGET_DIR"
    fi
    
    if [[ "$PRODUCTION_MODE" == "true" && -n "$EXTENSION_DIST_DIR" ]]; then
        echo -e "${CYAN}Distribution Directory:${NC} $EXTENSION_DIST_DIR"
    fi
    
    echo ""
    log_success "Chrome extension setup completed successfully!"
}

# Main workflow
main() {
    show_banner
    parse_arguments "$@"
    configure_environment
    
    if [[ "$VERBOSE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        echo "Configuration Summary:"
        echo "  Extension ID: $EXTENSION_ID"
        echo "  Version: $EXTENSION_VERSION"
        echo "  Platform: $PLATFORM"
        echo "  Development Mode: $DEV_MODE"
        echo "  Production Mode: $PRODUCTION_MODE"
        echo "  Update Mode: $UPDATE_MODE"
        echo "  Uninstall Mode: $UNINSTALL_MODE"
        if [[ -n "$SOURCE_DIR" ]]; then
            echo "  Source Directory: $SOURCE_DIR"
        fi
        if [[ -n "$INSTALL_DIR" ]]; then
            echo "  Install Directory: $INSTALL_DIR"
        fi
        echo ""
    fi
    
    validate_chrome
    validate_extension_source
    
    if [[ "$UPDATE_MODE" == "true" ]]; then
        update_extension
    elif [[ "$UNINSTALL_MODE" == "true" ]]; then
        uninstall_extension
    else
        prepare_extension_files
        install_development_extension
        prepare_production_extension
    fi
    
    show_summary
}

# Run main function with all arguments
main "$@"