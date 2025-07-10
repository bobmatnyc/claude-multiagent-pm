#!/bin/bash
#
# CMPM-QA Installation Validation Script
# =======================================
#
# Comprehensive validation and health monitoring for the CMPM-QA browser extension
# system installation. Validates all components, tests integration points, and
# provides detailed diagnostic information.
#
# Features:
# - Framework integration validation
# - Chrome extension status verification
# - Native messaging host connectivity testing
# - Service bridge operational validation
# - Health monitoring integration testing
# - Security configuration verification
# - Performance and connectivity testing

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="CMPM-QA Installation Validation"

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
HEALTH="🏥"
SHIELD="🛡️"
MAGNIFY="🔍"

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

log_success() {
    echo -e "${GREEN}${CHECKMARK} $1${NC}"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
    ((WARNING_TESTS++))
}

log_error() {
    echo -e "${RED}${CROSS} $1${NC}"
    ((FAILED_TESTS++))
}

log_header() {
    echo -e "${PURPLE}${MAGNIFY} $1${NC}"
}

log_test() {
    ((TOTAL_TESTS++))
    echo -n "Testing $1... "
}

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "======================================================"
    echo "  CMPM-QA Installation Validation"
    echo "  Version: $SCRIPT_VERSION"
    echo "  Framework: Claude PM v4.1.0"
    echo "======================================================"
    echo -e "${NC}"
}

# Help function
show_help() {
    cat << EOF
CMPM-QA Installation Validation Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose logging
    --qa-config FILE        QA configuration file path
    --quick                 Run quick validation (skip comprehensive tests)
    --deep                  Run deep validation (includes performance tests)
    --fix                   Attempt to fix common issues automatically
    --report FILE           Generate detailed report to file
    --json                  Output results in JSON format
    --no-color              Disable colored output

VALIDATION CATEGORIES:
    Framework Integration   Test framework CLI integration and health monitoring
    Extension Status        Verify Chrome extension installation and status
    Native Messaging        Test native messaging host connectivity
    Service Bridge          Validate service bridge operational status
    Security               Verify security configurations and permissions
    Performance            Test system performance and response times

EXAMPLES:
    # Standard validation
    $0 --qa-config ~/.claude-pm/qa-extension/config/qa-config.json

    # Quick validation for CI/CD
    $0 --quick --json --qa-config ./qa-config.json

    # Deep validation with auto-fix
    $0 --deep --fix --verbose

    # Generate detailed report
    $0 --report validation-report.html --qa-config ./qa-config.json

EXIT CODES:
    0    All tests passed
    1    Critical failures detected
    2    Warnings found but system operational
    3    Configuration or runtime errors

For more information, see: docs/VALIDATION_GUIDE.md
EOF
}

# Parse command line arguments
parse_arguments() {
    QA_CONFIG_FILE=""
    VERBOSE=false
    QUICK_MODE=false
    DEEP_MODE=false
    FIX_MODE=false
    REPORT_FILE=""
    JSON_OUTPUT=false
    NO_COLOR=false

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
            --qa-config)
                QA_CONFIG_FILE="$2"
                shift 2
                ;;
            --quick)
                QUICK_MODE=true
                shift
                ;;
            --deep)
                DEEP_MODE=true
                shift
                ;;
            --fix)
                FIX_MODE=true
                shift
                ;;
            --report)
                REPORT_FILE="$2"
                shift 2
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --no-color)
                NO_COLOR=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 3
                ;;
        esac
    done

    # Disable colors if requested
    if [[ "$NO_COLOR" == "true" ]]; then
        RED=''
        GREEN=''
        YELLOW=''
        BLUE=''
        PURPLE=''
        CYAN=''
        WHITE=''
        NC=''
    fi
}

# Load and validate QA configuration
load_qa_configuration() {
    log_header "Loading QA Configuration"

    # Try to find QA config if not specified
    if [[ -z "$QA_CONFIG_FILE" ]]; then
        local default_configs=(
            "$(pwd)/.claude-pm/qa-extension/config/qa-config.json"
            "$HOME/.claude-pm/qa-extension/config/qa-config.json"
            "$(pwd)/cmpm-qa/config/qa-config.json"
            "$(pwd)/qa-config.json"
        )

        for config in "${default_configs[@]}"; do
            if [[ -f "$config" ]]; then
                QA_CONFIG_FILE="$config"
                log_info "Found QA configuration: $config"
                break
            fi
        done
    fi

    if [[ -z "$QA_CONFIG_FILE" ]]; then
        log_error "QA configuration file not found"
        log_info "Specify with --qa-config or place in default location"
        exit 3
    fi

    if [[ ! -f "$QA_CONFIG_FILE" ]]; then
        log_error "QA configuration file not found: $QA_CONFIG_FILE"
        exit 3
    fi

    log_success "QA configuration file found"

    # Parse configuration using Python
    if command -v python3 &> /dev/null; then
        python3 << EOF
import json
import sys
import os

try:
    with open('$QA_CONFIG_FILE', 'r') as f:
        config = json.load(f)
    
    # Extract key configuration values
    extension_id = config.get('extension_id', 'unknown')
    native_host = config.get('native_host', 'unknown')
    service_port = config.get('service_port', 0)
    platform = config.get('platform', 'unknown')
    install_mode = config.get('install_mode', 'unknown')
    
    # Extract paths
    paths = config.get('paths', {})
    qa_install_dir = paths.get('qa_install_dir', '')
    service_install_dir = paths.get('service_install_dir', '')
    native_host_install_dir = paths.get('native_host_install_dir', '')
    
    # Write configuration to temporary file for shell script access
    with open('/tmp/qa_config_parsed.sh', 'w') as f:
        f.write(f'export QA_EXTENSION_ID="{extension_id}"\n')
        f.write(f'export QA_NATIVE_HOST="{native_host}"\n')
        f.write(f'export QA_SERVICE_PORT="{service_port}"\n')
        f.write(f'export QA_PLATFORM="{platform}"\n')
        f.write(f'export QA_INSTALL_MODE="{install_mode}"\n')
        f.write(f'export QA_INSTALL_DIR="{qa_install_dir}"\n')
        f.write(f'export QA_SERVICE_INSTALL_DIR="{service_install_dir}"\n')
        f.write(f'export QA_NATIVE_HOST_INSTALL_DIR="{native_host_install_dir}"\n')
    
    print("✅ Configuration parsed successfully")
    print(f"ℹ️ Extension ID: {extension_id}")
    print(f"ℹ️ Platform: {platform}")
    print(f"ℹ️ Install Mode: {install_mode}")

except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON in configuration: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error parsing configuration: {e}")
    sys.exit(1)
EOF
        
        if [[ $? -ne 0 ]]; then
            log_error "Configuration parsing failed"
            exit 3
        fi

        # Source the parsed configuration
        source /tmp/qa_config_parsed.sh
        rm -f /tmp/qa_config_parsed.sh

        log_success "Configuration loaded successfully"
    else
        log_error "Python 3 required for configuration parsing"
        exit 3
    fi
}

# Validate framework integration
validate_framework_integration() {
    log_header "Validating Framework Integration"

    # Test framework CLI availability
    log_test "Framework CLI availability"
    if command -v python3 &> /dev/null; then
        if python3 -c "import claude_pm.cli" 2>/dev/null; then
            log_success "Framework CLI module accessible"
        else
            log_error "Framework CLI module not accessible"
            return 1
        fi
    else
        log_error "Python 3 not available"
        return 1
    fi

    # Test CMPM commands
    log_test "CMPM health command"
    if python3 -c "from claude_pm.cmpm_commands import cmpm_health" 2>/dev/null; then
        log_success "CMPM health command available"
    else
        log_error "CMPM health command not available"
    fi

    log_test "CMPM QA commands"
    if python3 -c "from claude_pm.cmpm_commands import cmpm_qa_status, cmpm_qa_test" 2>/dev/null; then
        log_success "CMPM QA commands available"
    else
        log_error "CMPM QA commands not available"
    fi

    # Test Enhanced QA Agent
    log_test "Enhanced QA Agent"
    if python3 -c "from claude_pm.agents.enhanced_qa_agent import EnhancedQAAgent" 2>/dev/null; then
        log_success "Enhanced QA Agent available"
    else
        log_error "Enhanced QA Agent not available"
    fi

    # Test framework configuration integration
    log_test "Framework configuration integration"
    local framework_config="$(dirname "$QA_INSTALL_DIR")/../.claude-pm/config.json"
    if [[ -f "$framework_config" ]]; then
        if grep -q "qa_extension" "$framework_config" 2>/dev/null; then
            log_success "QA extension configured in framework"
        else
            log_warning "QA extension not found in framework configuration"
        fi
    else
        log_warning "Framework configuration file not found"
    fi

    return 0
}

# Validate Chrome extension status
validate_chrome_extension() {
    log_header "Validating Chrome Extension"

    # Detect platform for Chrome paths
    case "$(uname -s)" in
        Darwin*)
            CHROME_EXTENSIONS_DIR="$HOME/Library/Application Support/Google/Chrome/Default/Extensions"
            ;;
        Linux*)
            CHROME_EXTENSIONS_DIR="$HOME/.config/google-chrome/Default/Extensions"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            CHROME_EXTENSIONS_DIR="$APPDATA/Google/Chrome/User Data/Default/Extensions"
            ;;
    esac

    # Check Chrome installation
    log_test "Chrome installation"
    if command -v google-chrome &> /dev/null || [[ -d "/Applications/Google Chrome.app" ]] || [[ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]]; then
        log_success "Chrome installation found"
    else
        log_warning "Chrome installation not detected"
    fi

    # Check extension directory
    log_test "Extension installation directory"
    local extension_dir="$CHROME_EXTENSIONS_DIR/$QA_EXTENSION_ID"
    if [[ -d "$extension_dir" ]]; then
        log_success "Extension directory found"
        
        # Check for manifest and files
        log_test "Extension manifest file"
        local manifest_files=($(find "$extension_dir" -name "manifest.json" 2>/dev/null))
        if [[ ${#manifest_files[@]} -gt 0 ]]; then
            log_success "Extension manifest found"
            
            # Validate manifest content
            if command -v python3 &> /dev/null; then
                python3 << EOF
import json
import sys

try:
    with open('${manifest_files[0]}', 'r') as f:
        manifest = json.load(f)
    
    name = manifest.get('name', 'Unknown')
    version = manifest.get('version', 'Unknown')
    manifest_version = manifest.get('manifest_version', 'Unknown')
    
    print(f"✅ Extension: {name} v{version}")
    print(f"ℹ️ Manifest Version: {manifest_version}")
    
    # Check for CMPM-QA specific metadata
    cmpm_qa = manifest.get('cmpm_qa', {})
    if cmpm_qa:
        print(f"ℹ️ Framework Integration: Active")
        print(f"ℹ️ Framework Version: {cmpm_qa.get('framework_version', 'Unknown')}")
    else:
        print("⚠️ Framework metadata not found in manifest")

except Exception as e:
    print(f"❌ Error reading manifest: {e}")
    sys.exit(1)
EOF
            else
                log_warning "Python not available for manifest validation"
            fi
        else
            log_error "Extension manifest not found"
        fi
    else
        log_error "Extension not installed in Chrome directory"
    fi

    return 0
}

# Validate native messaging host
validate_native_messaging() {
    log_header "Validating Native Messaging Host"

    # Detect platform for native messaging paths
    case "$(uname -s)" in
        Darwin*)
            NATIVE_MESSAGING_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
            ;;
        Linux*)
            NATIVE_MESSAGING_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
            ;;
        CYGWIN*|MINGW32*|MSYS*|MINGW*)
            NATIVE_MESSAGING_DIR="$APPDATA/Google/Chrome/User Data/NativeMessagingHosts"
            ;;
    esac

    # Check native messaging manifest
    log_test "Native messaging manifest"
    local native_manifest="$NATIVE_MESSAGING_DIR/${QA_NATIVE_HOST}.json"
    if [[ -f "$native_manifest" ]]; then
        log_success "Native messaging manifest found"
        
        # Validate manifest content
        if command -v python3 &> /dev/null; then
            python3 << EOF
import json
import sys
import os

try:
    with open('$native_manifest', 'r') as f:
        manifest = json.load(f)
    
    name = manifest.get('name', 'Unknown')
    path = manifest.get('path', 'Unknown')
    msg_type = manifest.get('type', 'Unknown')
    allowed_origins = manifest.get('allowed_origins', [])
    
    print(f"✅ Host Name: {name}")
    print(f"ℹ️ Host Path: {path}")
    print(f"ℹ️ Type: {msg_type}")
    print(f"ℹ️ Allowed Origins: {len(allowed_origins)}")
    
    # Check if host executable exists
    if os.path.isfile(path) and os.access(path, os.X_OK):
        print(f"✅ Host executable is accessible")
    else:
        print(f"❌ Host executable not found or not executable: {path}")
        sys.exit(1)
    
    # Check allowed origins
    extension_origin = f"chrome-extension://$QA_EXTENSION_ID/"
    if extension_origin in allowed_origins:
        print(f"✅ Extension origin is allowed")
    else:
        print(f"❌ Extension origin not in allowed list")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error validating native messaging manifest: {e}")
    sys.exit(1)
EOF
            
            if [[ $? -ne 0 ]]; then
                log_error "Native messaging manifest validation failed"
                return 1
            fi
        else
            log_warning "Python not available for manifest validation"
        fi
    else
        log_error "Native messaging manifest not found: $native_manifest"
        return 1
    fi

    # Test host connectivity (if not in quick mode)
    if [[ "$QUICK_MODE" == "false" ]]; then
        log_test "Native host connectivity"
        local host_executable=$(python3 -c "
import json
with open('$native_manifest', 'r') as f:
    manifest = json.load(f)
print(manifest.get('path', ''))
" 2>/dev/null)

        if [[ -x "$host_executable" ]]; then
            # Test basic communication
            local test_response=$(echo '{"type":"ping","payload":{}}' | timeout 5 "$host_executable" 2>/dev/null || echo "")
            if [[ -n "$test_response" ]]; then
                log_success "Native host responds to test messages"
            else
                log_warning "Native host did not respond (may require specific initialization)"
            fi
        else
            log_error "Native host executable not found or not executable"
        fi
    fi

    return 0
}

# Validate service bridge
validate_service_bridge() {
    log_header "Validating Service Bridge"

    # Check service installation directory
    log_test "Service installation directory"
    if [[ -d "$QA_SERVICE_INSTALL_DIR" ]]; then
        log_success "Service installation directory found"
        
        # Check for service files
        log_test "Service implementation files"
        local service_files=(
            "$QA_SERVICE_INSTALL_DIR/qa_service.py"
            "$QA_SERVICE_INSTALL_DIR/qa_service.js"
            "$QA_SERVICE_INSTALL_DIR/start-qa-service.sh"
        )
        
        local found_service=false
        for file in "${service_files[@]}"; do
            if [[ -f "$file" ]]; then
                log_success "Found service file: $(basename "$file")"
                found_service=true
            fi
        done
        
        if [[ "$found_service" == "false" ]]; then
            log_warning "No service implementation files found"
        fi
    else
        log_error "Service installation directory not found: $QA_SERVICE_INSTALL_DIR"
    fi

    # Test service port availability (if not in quick mode)
    if [[ "$QUICK_MODE" == "false" && "$QA_SERVICE_PORT" != "0" ]]; then
        log_test "Service port availability"
        if command -v nc &> /dev/null; then
            if nc -z localhost "$QA_SERVICE_PORT" 2>/dev/null; then
                log_warning "Service port $QA_SERVICE_PORT is in use (service may be running)"
            else
                log_success "Service port $QA_SERVICE_PORT is available"
            fi
        elif command -v netstat &> /dev/null; then
            if netstat -an | grep -q ":$QA_SERVICE_PORT.*LISTEN"; then
                log_warning "Service port $QA_SERVICE_PORT is in use (service may be running)"
            else
                log_success "Service port $QA_SERVICE_PORT is available"
            fi
        else
            log_info "Cannot test port availability (nc/netstat not available)"
        fi
    fi

    return 0
}

# Validate security configurations
validate_security() {
    log_header "Validating Security Configuration"

    # Check file permissions
    log_test "Installation directory permissions"
    if [[ -d "$QA_INSTALL_DIR" ]]; then
        local perms=$(stat -c "%a" "$QA_INSTALL_DIR" 2>/dev/null || stat -f "%A" "$QA_INSTALL_DIR" 2>/dev/null || echo "unknown")
        if [[ "$perms" == "755" || "$perms" == "700" ]]; then
            log_success "Install directory permissions are secure"
        else
            log_warning "Install directory permissions may be too permissive: $perms"
        fi
    fi

    # Check configuration file permissions
    log_test "Configuration file permissions"
    if [[ -f "$QA_CONFIG_FILE" ]]; then
        local perms=$(stat -c "%a" "$QA_CONFIG_FILE" 2>/dev/null || stat -f "%A" "$QA_CONFIG_FILE" 2>/dev/null || echo "unknown")
        if [[ "$perms" == "644" || "$perms" == "600" ]]; then
            log_success "Configuration file permissions are secure"
        else
            log_warning "Configuration file permissions may be too permissive: $perms"
        fi
    fi

    # Check for sensitive data in configuration
    log_test "Configuration security scan"
    if grep -qi "password\|secret\|key\|token" "$QA_CONFIG_FILE" 2>/dev/null; then
        log_warning "Configuration file may contain sensitive data"
    else
        log_success "No obvious sensitive data in configuration"
    fi

    return 0
}

# Performance tests (deep mode only)
run_performance_tests() {
    if [[ "$DEEP_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Running Performance Tests"

    # Test framework command response time
    log_test "Framework command response time"
    local start_time=$(date +%s%N)
    if python3 -c "from claude_pm.cmpm_commands import CMPMHealthMonitor; import asyncio; asyncio.run(CMPMHealthMonitor().get_framework_health())" >/dev/null 2>&1; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
        if [[ $response_time -lt 5000 ]]; then
            log_success "Framework response time: ${response_time}ms (good)"
        elif [[ $response_time -lt 10000 ]]; then
            log_warning "Framework response time: ${response_time}ms (acceptable)"
        else
            log_warning "Framework response time: ${response_time}ms (slow)"
        fi
    else
        log_error "Framework health check failed"
    fi

    # Test memory usage
    log_test "Memory usage analysis"
    if command -v ps &> /dev/null; then
        local memory_usage=$(ps aux | grep -E "(python.*claude_pm|node.*qa)" | grep -v grep | awk '{sum += $6} END {print sum+0}')
        if [[ $memory_usage -lt 100000 ]]; then  # Less than 100MB
            log_success "Memory usage: ${memory_usage}KB (efficient)"
        elif [[ $memory_usage -lt 500000 ]]; then  # Less than 500MB
            log_warning "Memory usage: ${memory_usage}KB (moderate)"
        else
            log_warning "Memory usage: ${memory_usage}KB (high)"
        fi
    else
        log_info "Cannot analyze memory usage (ps not available)"
    fi

    return 0
}

# Attempt to fix common issues
fix_common_issues() {
    if [[ "$FIX_MODE" == "false" ]]; then
        return 0
    fi

    log_header "Attempting to Fix Common Issues"

    # Fix file permissions
    if [[ -d "$QA_INSTALL_DIR" ]]; then
        log_info "Fixing directory permissions..."
        chmod 755 "$QA_INSTALL_DIR"
        chmod 644 "$QA_CONFIG_FILE" 2>/dev/null || true
        log_success "Directory permissions fixed"
    fi

    # Recreate missing directories
    local required_dirs=(
        "$QA_INSTALL_DIR/logs"
        "$QA_INSTALL_DIR/temp"
        "$(dirname "$QA_CONFIG_FILE")"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created missing directory: $dir"
        fi
    done

    return 0
}

# Generate validation report
generate_report() {
    if [[ -z "$REPORT_FILE" ]]; then
        return 0
    fi

    log_header "Generating Validation Report"

    if [[ "$REPORT_FILE" == *.html ]]; then
        generate_html_report
    elif [[ "$REPORT_FILE" == *.json ]]; then
        generate_json_report
    else
        generate_text_report
    fi

    log_success "Report generated: $REPORT_FILE"
}

generate_html_report() {
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>CMPM-QA Validation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 15px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .pass { color: green; }
        .warn { color: orange; }
        .fail { color: red; }
        .summary { background: #f9f9f9; padding: 10px; border-left: 4px solid #ccc; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CMPM-QA Validation Report</h1>
        <p>Generated: $(date)</p>
        <p>Configuration: $QA_CONFIG_FILE</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: $TOTAL_TESTS</p>
        <p class="pass">Passed: $PASSED_TESTS</p>
        <p class="warn">Warnings: $WARNING_TESTS</p>
        <p class="fail">Failed: $FAILED_TESTS</p>
    </div>
    
    <div class="section">
        <h2>Configuration</h2>
        <p>Extension ID: $QA_EXTENSION_ID</p>
        <p>Native Host: $QA_NATIVE_HOST</p>
        <p>Platform: $QA_PLATFORM</p>
        <p>Install Mode: $QA_INSTALL_MODE</p>
    </div>
    
    <div class="section">
        <p><em>Detailed test results would be included here in a full implementation.</em></p>
    </div>
</body>
</html>
EOF
}

generate_json_report() {
    cat > "$REPORT_FILE" << EOF
{
    "validation_report": {
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "script_version": "$SCRIPT_VERSION",
        "configuration_file": "$QA_CONFIG_FILE",
        "summary": {
            "total_tests": $TOTAL_TESTS,
            "passed_tests": $PASSED_TESTS,
            "warning_tests": $WARNING_TESTS,
            "failed_tests": $FAILED_TESTS,
            "success_rate": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
        },
        "configuration": {
            "extension_id": "$QA_EXTENSION_ID",
            "native_host": "$QA_NATIVE_HOST",
            "service_port": $QA_SERVICE_PORT,
            "platform": "$QA_PLATFORM",
            "install_mode": "$QA_INSTALL_MODE",
            "install_directory": "$QA_INSTALL_DIR"
        },
        "validation_categories": {
            "framework_integration": "tested",
            "chrome_extension": "tested",
            "native_messaging": "tested",
            "service_bridge": "tested",
            "security": "tested",
            "performance": "$(if [[ "$DEEP_MODE" == "true" ]]; then echo "tested"; else echo "skipped"; fi)"
        }
    }
}
EOF
}

generate_text_report() {
    cat > "$REPORT_FILE" << EOF
CMPM-QA Validation Report
========================

Generated: $(date)
Script Version: $SCRIPT_VERSION
Configuration: $QA_CONFIG_FILE

Summary
-------
Total Tests: $TOTAL_TESTS
Passed: $PASSED_TESTS
Warnings: $WARNING_TESTS
Failed: $FAILED_TESTS
Success Rate: $(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")%

Configuration
------------
Extension ID: $QA_EXTENSION_ID
Native Host: $QA_NATIVE_HOST
Service Port: $QA_SERVICE_PORT
Platform: $QA_PLATFORM
Install Mode: $QA_INSTALL_MODE
Install Directory: $QA_INSTALL_DIR

Validation Categories
-------------------
Framework Integration: Tested
Chrome Extension: Tested
Native Messaging: Tested
Service Bridge: Tested
Security: Tested
Performance: $(if [[ "$DEEP_MODE" == "true" ]]; then echo "Tested"; else echo "Skipped"; fi)

EOF
}

# Show validation summary
show_summary() {
    log_header "Validation Summary"
    
    echo -e "${CYAN}Configuration File:${NC} $QA_CONFIG_FILE"
    echo -e "${CYAN}Extension ID:${NC} $QA_EXTENSION_ID"
    echo -e "${CYAN}Platform:${NC} $QA_PLATFORM"
    echo -e "${CYAN}Install Mode:${NC} $QA_INSTALL_MODE"
    echo ""
    
    echo -e "${CYAN}Test Results:${NC}"
    echo -e "  Total Tests: $TOTAL_TESTS"
    echo -e "  ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "  ${YELLOW}Warnings: $WARNING_TESTS${NC}"
    echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
    
    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    fi
    echo -e "  Success Rate: ${success_rate}%"
    echo ""
    
    # Determine overall status
    if [[ $FAILED_TESTS -eq 0 && $WARNING_TESTS -eq 0 ]]; then
        log_success "CMPM-QA installation is fully operational!"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Test QA functionality: python3 -m claude_pm.cmpm_commands cmpm:qa-test"
        echo "2. Monitor health: python3 -m claude_pm.cmpm_commands cmpm:health"
        echo "3. View test results: python3 -m claude_pm.cmpm_commands cmpm:qa-results"
        EXIT_CODE=0
    elif [[ $FAILED_TESTS -eq 0 ]]; then
        log_warning "CMMP-QA installation is operational with warnings"
        echo ""
        echo "Review the warnings above and consider addressing them for optimal performance."
        EXIT_CODE=2
    else
        log_error "CMPM-QA installation has critical issues"
        echo ""
        echo "Critical failures detected. Please review the errors above and:"
        echo "1. Check the installation logs"
        echo "2. Verify all prerequisites are met"
        echo "3. Re-run the installation if necessary"
        echo "4. Use --fix mode to attempt automatic repairs"
        EXIT_CODE=1
    fi
    
    if [[ -n "$REPORT_FILE" ]]; then
        echo ""
        echo -e "${BLUE}Detailed report:${NC} $REPORT_FILE"
    fi
}

# JSON output function
output_json() {
    if [[ "$JSON_OUTPUT" == "false" ]]; then
        return 0
    fi

    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    fi

    cat << EOF
{
    "cmpm_qa_validation": {
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "script_version": "$SCRIPT_VERSION",
        "configuration_file": "$QA_CONFIG_FILE",
        "test_summary": {
            "total_tests": $TOTAL_TESTS,
            "passed_tests": $PASSED_TESTS,
            "warning_tests": $WARNING_TESTS,
            "failed_tests": $FAILED_TESTS,
            "success_rate": $success_rate
        },
        "configuration": {
            "extension_id": "$QA_EXTENSION_ID",
            "native_host": "$QA_NATIVE_HOST",
            "service_port": $QA_SERVICE_PORT,
            "platform": "$QA_PLATFORM",
            "install_mode": "$QA_INSTALL_MODE"
        },
        "status": "$(if [[ $FAILED_TESTS -eq 0 && $WARNING_TESTS -eq 0 ]]; then echo "healthy"; elif [[ $FAILED_TESTS -eq 0 ]]; then echo "warning"; else echo "error"; fi)",
        "exit_code": $EXIT_CODE
    }
}
EOF
}

# Main validation workflow
main() {
    show_banner
    parse_arguments "$@"
    
    load_qa_configuration
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Validation Configuration:"
        echo "  QA Config: $QA_CONFIG_FILE"
        echo "  Quick Mode: $QUICK_MODE"
        echo "  Deep Mode: $DEEP_MODE"
        echo "  Fix Mode: $FIX_MODE"
        echo "  JSON Output: $JSON_OUTPUT"
        echo ""
    fi
    
    # Run validation tests
    validate_framework_integration
    validate_chrome_extension
    validate_native_messaging
    validate_service_bridge
    validate_security
    run_performance_tests
    
    # Fix issues if requested
    fix_common_issues
    
    # Generate reports
    generate_report
    
    # Show results
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        output_json
    else
        show_summary
    fi
    
    exit $EXIT_CODE
}

# Initialize exit code
EXIT_CODE=0

# Run main function with all arguments
main "$@"