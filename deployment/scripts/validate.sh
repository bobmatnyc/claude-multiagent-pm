#!/bin/bash

# Claude PM Framework - Environment Validation Script
# Validates CLAUDE_PM_ROOT configuration and deployment readiness
# ================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Icons
CHECKMARK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"

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
echo -e "${PURPLE}"
echo "========================================================"
echo "  Claude PM Framework - Environment Validation"
echo "  CLAUDE_PM_ROOT Support Validation (M01-039)"
echo "========================================================"
echo -e "${NC}"

# Initialize validation results
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# Helper function to increment error count
validation_error() {
    log_error "$1"
    ((VALIDATION_ERRORS++))
}

validation_warning() {
    log_warning "$1"
    ((VALIDATION_WARNINGS++))
}

# 1. Environment Variable Validation
log_header "Environment Variable Validation"

# Check CLAUDE_PM_ROOT
if [[ -n "${CLAUDE_PM_ROOT:-}" ]]; then
    log_success "CLAUDE_PM_ROOT is set: $CLAUDE_PM_ROOT"
    
    # Validate the path
    if [[ ! -d "$(dirname "$CLAUDE_PM_ROOT")" ]]; then
        validation_error "Parent directory of CLAUDE_PM_ROOT doesn't exist: $(dirname "$CLAUDE_PM_ROOT")"
    else
        log_success "Parent directory exists: $(dirname "$CLAUDE_PM_ROOT")"
    fi
    
    # Check path permissions
    if [[ ! -w "$(dirname "$CLAUDE_PM_ROOT")" ]]; then
        validation_error "No write permission to parent directory: $(dirname "$CLAUDE_PM_ROOT")"
    else
        log_success "Write permission confirmed for parent directory"
    fi
    
    CLAUDE_PM_PATH="$CLAUDE_PM_ROOT"
    BASE_PATH="$(dirname "$CLAUDE_PM_ROOT")"
    MANAGED_PATH="$BASE_PATH/managed"
else
    log_info "CLAUDE_PM_ROOT not set, using default paths"
    BASE_PATH="$HOME/Projects"
    CLAUDE_PM_PATH="$BASE_PATH/Claude-PM"
    MANAGED_PATH="$BASE_PATH/managed"
fi

log_info "Resolved paths:"
log_info "  Base Path: $BASE_PATH"
log_info "  Claude PM Path: $CLAUDE_PM_PATH"
log_info "  Managed Path: $MANAGED_PATH"

# 2. Python Environment Validation
log_header "Python Environment Validation"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 9 ]]; then
        log_success "Python version $PYTHON_VERSION (meets requirement >= 3.9)"
    else
        validation_error "Python version $PYTHON_VERSION is too old (requires >= 3.9)"
    fi
else
    validation_error "Python 3 is not installed or not in PATH"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    log_success "pip3 is available"
else
    validation_error "pip3 is not installed or not in PATH"
fi

# Check virtual environment capability
if python3 -m venv --help &> /dev/null; then
    log_success "Virtual environment support available"
else
    validation_error "Virtual environment support not available (install python3-venv)"
fi

# 3. System Dependencies Validation
log_header "System Dependencies Validation"

# Required system tools
REQUIRED_TOOLS=("git" "make" "curl")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        log_success "$tool is available"
    else
        validation_error "$tool is required but not installed"
    fi
done

# Optional tools (warnings only)
OPTIONAL_TOOLS=("docker" "docker-compose" "pm2" "systemctl")

for tool in "${OPTIONAL_TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        log_success "$tool is available (optional)"
    else
        validation_warning "$tool is not available (optional for advanced features)"
    fi
done

# 4. Directory Structure Validation
log_header "Directory Structure Validation"

# Check base directory
if [[ -d "$BASE_PATH" ]]; then
    log_success "Base directory exists: $BASE_PATH"
    
    # Check permissions
    if [[ -w "$BASE_PATH" ]]; then
        log_success "Base directory is writable"
    else
        validation_error "Base directory is not writable: $BASE_PATH"
    fi
else
    log_info "Base directory doesn't exist, will be created: $BASE_PATH"
    
    # Check if we can create it
    if [[ -w "$(dirname "$BASE_PATH")" ]]; then
        log_success "Can create base directory"
    else
        validation_error "Cannot create base directory (no write permission to $(dirname "$BASE_PATH"))"
    fi
fi

# Check Claude PM directory
if [[ -d "$CLAUDE_PM_PATH" ]]; then
    log_info "Claude PM directory already exists: $CLAUDE_PM_PATH"
    
    # Check if it's a valid installation
    if [[ -f "$CLAUDE_PM_PATH/pyproject.toml" ]]; then
        log_success "Existing installation detected"
    else
        validation_warning "Directory exists but doesn't appear to be a Claude PM installation"
    fi
else
    log_info "Claude PM directory will be created: $CLAUDE_PM_PATH"
fi

# Check managed directory
if [[ -d "$MANAGED_PATH" ]]; then
    log_success "Managed projects directory exists: $MANAGED_PATH"
else
    log_info "Managed projects directory will be created: $MANAGED_PATH"
fi

# 5. Configuration File Validation
log_header "Configuration File Validation"

# Get script directory and find deployment configs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$DEPLOYMENT_DIR/environments"

# Check environment configuration files
ENVIRONMENTS=("development" "staging" "production" "docker")

for env in "${ENVIRONMENTS[@]}"; do
    env_file="$ENV_DIR/$env.env"
    if [[ -f "$env_file" ]]; then
        log_success "Environment config exists: $env.env"
        
        # Basic syntax check
        if source "$env_file" &> /dev/null; then
            log_success "Environment config syntax is valid: $env.env"
        else
            validation_error "Environment config has syntax errors: $env.env"
        fi
    else
        validation_error "Environment config missing: $env.env"
    fi
done

# 6. Framework Configuration Test
log_header "Framework Configuration Test"

# Test if we can import and use the configuration system
CLAUDE_PM_ROOT_TEST="$CLAUDE_PM_ROOT" python3 -c "
import os
import sys
import tempfile
from pathlib import Path

# Add current project to path for testing
sys.path.insert(0, '$SCRIPT_DIR/../../')

try:
    from claude_pm.core.config import Config
    print('✅ Config import successful')
    
    # Test with custom CLAUDE_PM_ROOT
    if os.environ.get('CLAUDE_PM_ROOT_TEST'):
        os.environ['CLAUDE_PM_ROOT'] = os.environ['CLAUDE_PM_ROOT_TEST']
    
    config = Config()
    
    print(f'✅ Config initialization successful')
    print(f'   Base Path: {config.get(\"base_path\")}')
    print(f'   Claude PM Path: {config.get(\"claude_pm_path\")}')
    print(f'   Managed Path: {config.get(\"managed_path\")}')
    
    # Test path resolution
    expected_claude_pm = os.environ.get('CLAUDE_PM_ROOT') or str(Path.home() / 'Projects' / 'Claude-PM')
    actual_claude_pm = config.get('claude_pm_path')
    
    if actual_claude_pm == expected_claude_pm:
        print('✅ Path resolution working correctly')
    else:
        print(f'❌ Path resolution error: expected {expected_claude_pm}, got {actual_claude_pm}')
        sys.exit(1)
        
except ImportError as e:
    print(f'❌ Failed to import Config: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Configuration test failed: {e}')
    sys.exit(1)
" 2>/dev/null || validation_error "Framework configuration test failed"

# 7. Memory Service Validation
log_header "Memory Service Validation"

# Check for mem0AI dependencies
python3 -c "
try:
    import aiohttp
    print('✅ aiohttp available for mem0AI integration')
except ImportError:
    print('⚠️ aiohttp not available (install with: pip install aiohttp)')
    
try:
    import yaml
    print('✅ PyYAML available for configuration')
except ImportError:
    print('❌ PyYAML required but not available')
" 2>/dev/null || validation_warning "Some Python dependencies may be missing"

# 8. Network and Ports Validation
log_header "Network and Ports Validation"

# Check if default ports are available
DEFAULT_PORTS=(8002 7001 8001)

for port in "${DEFAULT_PORTS[@]}"; do
    if command -v netstat &> /dev/null; then
        if netstat -ln | grep ":$port " &> /dev/null; then
            validation_warning "Port $port is already in use"
        else
            log_success "Port $port is available"
        fi
    elif command -v ss &> /dev/null; then
        if ss -ln | grep ":$port " &> /dev/null; then
            validation_warning "Port $port is already in use"
        else
            log_success "Port $port is available"
        fi
    else
        log_info "Cannot check port availability (netstat/ss not available)"
        break
    fi
done

# 9. Security Validation
log_header "Security Validation"

# Check file permissions
if [[ $(umask) == "0022" ]] || [[ $(umask) == "0002" ]]; then
    log_success "Umask setting is appropriate"
else
    validation_warning "Umask setting may create security issues: $(umask)"
fi

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
    validation_warning "Running as root is not recommended for development"
else
    log_success "Not running as root (good for security)"
fi

# 10. Final Validation Summary
log_header "Validation Summary"

echo ""
echo -e "${BLUE}Validation Results:${NC}"
echo -e "  Total Errors: ${RED}$VALIDATION_ERRORS${NC}"
echo -e "  Total Warnings: ${YELLOW}$VALIDATION_WARNINGS${NC}"
echo ""

if [[ $VALIDATION_ERRORS -eq 0 ]]; then
    if [[ $VALIDATION_WARNINGS -eq 0 ]]; then
        log_success "All validations passed! Environment is ready for deployment."
        echo ""
        echo -e "${GREEN}You can proceed with deployment:${NC}"
        echo "  ./deployment/scripts/deploy.sh development"
        echo "  ./deployment/scripts/deploy.sh production"
        echo ""
    else
        log_success "Validation passed with warnings. Environment is ready for deployment."
        echo ""
        echo -e "${YELLOW}Address warnings for optimal experience:${NC}"
        echo "  - Install optional tools for advanced features"
        echo "  - Review port conflicts for services"
        echo ""
        echo -e "${GREEN}You can proceed with deployment:${NC}"
        echo "  ./deployment/scripts/deploy.sh development"
        echo ""
    fi
    exit 0
else
    log_error "Validation failed with $VALIDATION_ERRORS errors."
    echo ""
    echo -e "${RED}Please fix the errors above before deployment:${NC}"
    echo "  - Install missing system dependencies"
    echo "  - Fix Python environment issues"
    echo "  - Resolve permission problems"
    echo "  - Configure required paths"
    echo ""
    echo -e "${BLUE}For help:${NC}"
    echo "  - Review deployment documentation"
    echo "  - Check system requirements"
    echo "  - Run this script again after fixes"
    exit 1
fi