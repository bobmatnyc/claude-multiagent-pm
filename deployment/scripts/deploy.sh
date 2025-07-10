#!/bin/bash

# Claude PM Framework - Universal Deployment Script
# Supports CLAUDE_PM_ROOT environment variable (M01-039)
# =================================================

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="Claude PM Framework Deployment"

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
DOCTOR="🏥"

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
    echo "  Claude PM Framework - Universal Deployment Script"
    echo "  Version: $SCRIPT_VERSION"
    echo "  CLAUDE_PM_ROOT Support: Enabled (M01-039)"
    echo "=========================================================="
    echo -e "${NC}"
}

# Help function
show_help() {
    cat << EOF
Claude PM Framework Deployment Script

USAGE:
    $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development     Local development deployment
    staging         Staging environment deployment  
    production      Production deployment
    docker          Docker container deployment
    cloud           Cloud provider deployment

OPTIONS:
    -h, --help              Show this help message
    -v, --validate-only     Validate configuration without deploying
    -b, --backup            Create backup before deployment
    -s, --skip-health       Skip health checks after deployment
    -f, --force             Force deployment (skip confirmations)
    -d, --debug             Enable debug mode
    --dry-run              Show what would be done without executing

ENVIRONMENT VARIABLES:
    CLAUDE_PM_ROOT          Custom framework installation path
                           Default: ~/Projects/Claude-PM
                           Examples:
                             export CLAUDE_PM_ROOT=/opt/claude-pm
                             export CLAUDE_PM_ROOT=/srv/apps/claude-pm

EXAMPLES:
    # Standard development deployment
    $0 development

    # Production deployment with backup
    $0 production --backup

    # Custom path deployment
    export CLAUDE_PM_ROOT=/opt/my-claude-pm
    $0 production

    # Validate configuration only
    $0 staging --validate-only

    # Docker deployment
    $0 docker

    # Cloud deployment (AWS/GCP/Azure)
    $0 cloud

For more information, see: docs/deployment/README.md
EOF
}

# Parse command line arguments
parse_arguments() {
    ENVIRONMENT=""
    VALIDATE_ONLY=false
    CREATE_BACKUP=false
    SKIP_HEALTH_CHECKS=false
    FORCE_DEPLOYMENT=false
    DEBUG_MODE=false
    DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            development|staging|production|docker|cloud)
                ENVIRONMENT="$1"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            -b|--backup)
                CREATE_BACKUP=true
                shift
                ;;
            -s|--skip-health)
                SKIP_HEALTH_CHECKS=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOYMENT=true
                shift
                ;;
            -d|--debug)
                DEBUG_MODE=true
                set -x  # Enable bash debug mode
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

    if [[ -z "$ENVIRONMENT" ]]; then
        log_error "Environment is required"
        echo "Use --help for usage information"
        exit 1
    fi
}

# Detect and configure paths based on CLAUDE_PM_ROOT
configure_paths() {
    log_header "Configuring Deployment Paths"

    # Determine Claude PM root path
    if [[ -n "${CLAUDE_PM_ROOT:-}" ]]; then
        CLAUDE_PM_PATH="$CLAUDE_PM_ROOT"
        BASE_PATH="$(dirname "$CLAUDE_PM_ROOT")"
        log_info "Using custom CLAUDE_PM_ROOT: $CLAUDE_PM_PATH"
    else
        BASE_PATH="$HOME/Projects"
        CLAUDE_PM_PATH="$BASE_PATH/Claude-PM"
        log_info "Using default path: $CLAUDE_PM_PATH"
    fi

    # Derived paths
    MANAGED_PATH="$BASE_PATH/managed"
    DEPLOYMENT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    ENV_FILE="$DEPLOYMENT_PATH/environments/$ENVIRONMENT.env"

    # Current script location (should be claude-pm for this deployment)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

    log_info "Base Path: $BASE_PATH"
    log_info "Claude PM Path: $CLAUDE_PM_PATH"
    log_info "Managed Projects Path: $MANAGED_PATH" 
    log_info "Deployment Config Path: $DEPLOYMENT_PATH"
    log_info "Environment File: $ENV_FILE"
    log_info "Project Root: $PROJECT_ROOT"
}

# Validate environment and prerequisites
validate_environment() {
    log_header "Validating Environment: $ENVIRONMENT"

    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    log_success "Environment configuration found"

    # Validate Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python version: $PYTHON_VERSION"

    # Check for required tools
    local required_tools=("git" "pip3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' is not installed"
            exit 1
        fi
        log_success "$tool is available"
    done

    # Validate directory structure
    if [[ ! -d "$BASE_PATH" ]]; then
        log_warning "Base directory doesn't exist: $BASE_PATH"
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$BASE_PATH"
            log_success "Created base directory: $BASE_PATH"
        else
            log_info "[DRY RUN] Would create: $BASE_PATH"
        fi
    fi

    # Environment-specific validations
    case $ENVIRONMENT in
        production)
            validate_production_requirements
            ;;
        docker)
            validate_docker_requirements
            ;;
        cloud)
            validate_cloud_requirements
            ;;
    esac
}

validate_production_requirements() {
    log_info "Validating production requirements..."

    # Check for production secrets
    if grep -q "REPLACE_WITH_" "$ENV_FILE"; then
        log_error "Production environment file contains placeholder values"
        log_error "Please configure all REPLACE_WITH_* values in $ENV_FILE"
        exit 1
    fi

    # Check SSL certificates path
    if [[ -n "${CLAUDE_PM_SSL_CERT_PATH:-}" && ! -f "${CLAUDE_PM_SSL_CERT_PATH:-}" ]]; then
        log_warning "SSL certificate not found (will need to be configured)"
    fi

    log_success "Production requirements validated"
}

validate_docker_requirements() {
    log_info "Validating Docker requirements..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is required for Docker deployment"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is required for Docker deployment"
        exit 1
    fi

    log_success "Docker requirements validated"
}

validate_cloud_requirements() {
    log_info "Validating cloud requirements..."
    
    # Check for cloud CLI tools (AWS, GCP, Azure)
    local cloud_tools=("aws" "gcloud" "az")
    local found_tool=false
    
    for tool in "${cloud_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log_success "$tool CLI is available"
            found_tool=true
            break
        fi
    done
    
    if [[ "$found_tool" == "false" ]]; then
        log_warning "No cloud CLI tools found (aws, gcloud, az)"
        log_info "You may need to install cloud provider CLI tools"
    fi
}

# Create backup of existing installation
create_backup() {
    if [[ "$CREATE_BACKUP" == "false" ]]; then
        return 0
    fi

    log_header "Creating Backup"

    local backup_dir="$BASE_PATH/backups/claude-pm-$(date +%Y%m%d_%H%M%S)"
    
    if [[ -d "$CLAUDE_PM_PATH" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$backup_dir"
            cp -r "$CLAUDE_PM_PATH" "$backup_dir/"
            log_success "Backup created: $backup_dir"
        else
            log_info "[DRY RUN] Would create backup: $backup_dir"
        fi
    else
        log_info "No existing installation to backup"
    fi
}

# Deploy the framework
deploy_framework() {
    log_header "Deploying Claude PM Framework"

    # Create directory structure
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$CLAUDE_PM_PATH"
        mkdir -p "$MANAGED_PATH"
        mkdir -p "$CLAUDE_PM_PATH/logs"
        mkdir -p "$CLAUDE_PM_PATH/config"
    else
        log_info "[DRY RUN] Would create directory structure"
    fi

    # Copy framework files
    if [[ "$DRY_RUN" == "false" ]]; then
        # Copy from current project to target location
        cp -r "$PROJECT_ROOT"/* "$CLAUDE_PM_PATH/" 2>/dev/null || true
        log_success "Framework files copied to $CLAUDE_PM_PATH"
    else
        log_info "[DRY RUN] Would copy framework files"
    fi

    # Copy and configure environment file
    local target_env="$CLAUDE_PM_PATH/.env"
    if [[ "$DRY_RUN" == "false" ]]; then
        cp "$ENV_FILE" "$target_env"
        
        # Update CLAUDE_PM_ROOT in the env file if it was customized
        if [[ -n "${CLAUDE_PM_ROOT:-}" ]]; then
            sed -i.bak "s|^# CLAUDE_PM_ROOT=.*|CLAUDE_PM_ROOT=$CLAUDE_PM_ROOT|" "$target_env" || true
            sed -i.bak "s|^CLAUDE_PM_ROOT=.*|CLAUDE_PM_ROOT=$CLAUDE_PM_ROOT|" "$target_env" || true
        fi
        
        log_success "Environment configuration installed"
    else
        log_info "[DRY RUN] Would install environment configuration"
    fi

    # Install dependencies based on environment
    case $ENVIRONMENT in
        development)
            install_development_dependencies
            ;;
        production)
            install_production_dependencies
            ;;
        docker)
            deploy_docker
            ;;
        cloud)
            deploy_cloud
            ;;
        *)
            install_development_dependencies
            ;;
    esac
    
    # Deploy CMPM-QA extension if available
    deploy_cmpm_qa_extension
}

install_development_dependencies() {
    log_info "Installing development dependencies..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$CLAUDE_PM_PATH"
        
        # Create virtual environment if it doesn't exist
        if [[ ! -d ".venv" ]]; then
            python3 -m venv .venv
            log_success "Virtual environment created"
        fi
        
        # Activate virtual environment
        source .venv/bin/activate
        
        # Install dependencies
        if [[ -f "requirements/dev.txt" ]]; then
            pip install -r requirements/dev.txt
        elif [[ -f "requirements.txt" ]]; then
            pip install -r requirements.txt
        fi
        
        # Install in development mode
        pip install -e .
        
        log_success "Development dependencies installed"
    else
        log_info "[DRY RUN] Would install development dependencies"
    fi
}

install_production_dependencies() {
    log_info "Installing production dependencies..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$CLAUDE_PM_PATH"
        
        # Create virtual environment
        if [[ ! -d ".venv" ]]; then
            python3 -m venv .venv
            log_success "Virtual environment created"
        fi
        
        # Activate virtual environment
        source .venv/bin/activate
        
        # Install production dependencies only
        if [[ -f "requirements/production.txt" ]]; then
            pip install -r requirements/production.txt
        elif [[ -f "requirements.txt" ]]; then
            pip install -r requirements.txt
        fi
        
        # Install package
        pip install .
        
        log_success "Production dependencies installed"
    else
        log_info "[DRY RUN] Would install production dependencies"
    fi
}

deploy_docker() {
    log_info "Deploying with Docker..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$CLAUDE_PM_PATH"
        
        # Build and start containers
        if [[ -f "docker-compose.yml" ]]; then
            docker-compose up -d --build
            log_success "Docker containers started"
        else
            log_warning "docker-compose.yml not found, skipping Docker deployment"
        fi
    else
        log_info "[DRY RUN] Would deploy with Docker"
    fi
}

deploy_cloud() {
    log_info "Cloud deployment not fully implemented in this version"
    log_info "Please use cloud-specific deployment scripts in deployment/cloud/"
}

# Deploy CMPM-QA extension components
deploy_cmpm_qa_extension() {
    log_header "Deploying CMPM-QA Extension"
    
    # Check if CMPM-QA directory exists
    local cmpm_qa_source="$PROJECT_ROOT/cmpm-qa"
    local cmpm_qa_target="$CLAUDE_PM_PATH/cmpm-qa"
    
    if [[ ! -d "$cmpm_qa_source" ]]; then
        log_info "CMPM-QA extension not found - skipping (optional component)"
        return 0
    fi
    
    log_info "CMPM-QA extension found, deploying components..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Copy CMPM-QA directory structure
        cp -r "$cmpm_qa_source" "$cmpm_qa_target"
        log_success "CMPM-QA files copied to deployment location"
        
        # Make scripts executable
        chmod +x "$cmpm_qa_target/scripts"/*.sh 2>/dev/null || true
        log_success "CMPM-QA scripts made executable"
        
        # Create QA extension configuration directory
        mkdir -p "$CLAUDE_PM_PATH/.claude-pm/qa-extension/config"
        mkdir -p "$CLAUDE_PM_PATH/.claude-pm/qa-extension/logs"
        log_success "CMPM-QA directories created"
        
        # Check if we should run QA installation
        case $ENVIRONMENT in
            development)
                log_info "Development environment detected"
                if ask_confirmation "Install CMPM-QA extension components?"; then
                    install_cmpm_qa_components
                fi
                ;;
            production)
                log_info "Production environment detected"
                if ask_confirmation "Install CMPM-QA extension for production?"; then
                    install_cmpm_qa_components
                fi
                ;;
            *)
                log_info "CMPM-QA components copied but not installed"
                log_info "Run '$CLAUDE_PM_PATH/cmpm-qa/scripts/install-qa.sh' to install"
                ;;
        esac
    else
        log_info "[DRY RUN] Would deploy CMPM-QA extension"
    fi
}

# Install CMPM-QA components using the specialized installer
install_cmpm_qa_components() {
    log_info "Installing CMPM-QA components..."
    
    local qa_installer="$CLAUDE_PM_PATH/cmpm-qa/scripts/install-qa.sh"
    local qa_install_dir="$CLAUDE_PM_PATH/.claude-pm/qa-extension"
    
    if [[ -x "$qa_installer" ]]; then
        # Run QA installer with appropriate flags
        local install_flags=""
        
        # Add environment-specific flags
        case $ENVIRONMENT in
            development)
                install_flags="--development --verbose"
                ;;
            production)
                install_flags="--production"
                ;;
        esac
        
        # Add force flag if force deployment is enabled
        if [[ "$FORCE_DEPLOYMENT" == "true" ]]; then
            install_flags="$install_flags --force"
        fi
        
        log_info "Running CMPM-QA installer..."
        if "$qa_installer" $install_flags --install-dir "$qa_install_dir"; then
            log_success "CMPM-QA installation completed"
            
            # Run validation to ensure installation succeeded
            local qa_validator="$CLAUDE_PM_PATH/cmpm-qa/scripts/validate-install.sh"
            if [[ -x "$qa_validator" ]]; then
                log_info "Validating CMPM-QA installation..."
                if "$qa_validator" --quick --qa-config "$qa_install_dir/config/qa-config.json"; then
                    log_success "CMPM-QA validation passed"
                else
                    log_warning "CMPM-QA validation failed - manual review recommended"
                fi
            fi
        else
            log_warning "CMPM-QA installation failed - extension will not be available"
            log_info "You can install manually later using: $qa_installer"
        fi
    else
        log_warning "CMPM-QA installer not found or not executable"
    fi
}

# Configure services
configure_services() {
    log_header "Configuring Services"

    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$CLAUDE_PM_PATH"
        
        # Set up systemd services for production
        if [[ "$ENVIRONMENT" == "production" && -f "claude-pm-health-monitor.service" ]]; then
            log_info "Setting up systemd services..."
            
            # Update service file with correct paths
            sed "s|/path/to/claude-pm|$CLAUDE_PM_PATH|g" claude-pm-health-monitor.service > /tmp/claude-pm-health-monitor.service
            
            if [[ "$FORCE_DEPLOYMENT" == "true" ]] || ask_confirmation "Install systemd service?"; then
                sudo cp /tmp/claude-pm-health-monitor.service /etc/systemd/system/
                sudo systemctl daemon-reload
                sudo systemctl enable claude-pm-health-monitor
                log_success "Systemd service configured"
            fi
        fi
        
        # Configure cron jobs for monitoring
        if [[ -f "claude-pm-doc-sync.cron" ]]; then
            log_info "Setting up cron jobs..."
            
            # Update cron job with correct paths
            sed "s|/path/to/claude-pm|$CLAUDE_PM_PATH|g" claude-pm-doc-sync.cron > /tmp/claude-pm.cron
            
            if [[ "$FORCE_DEPLOYMENT" == "true" ]] || ask_confirmation "Install cron jobs?"; then
                crontab /tmp/claude-pm.cron
                log_success "Cron jobs configured"
            fi
        fi
    else
        log_info "[DRY RUN] Would configure services"
    fi
}

# Run health checks
run_health_checks() {
    if [[ "$SKIP_HEALTH_CHECKS" == "true" ]]; then
        log_info "Skipping health checks"
        return 0
    fi

    log_header "Running Health Checks"

    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$CLAUDE_PM_PATH"
        
        # Activate virtual environment
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        fi
        
        # Test basic functionality
        if command -v claude-pm &> /dev/null; then
            log_info "Testing CLI functionality..."
            if claude-pm util info > /dev/null 2>&1; then
                log_success "CLI is working"
            else
                log_warning "CLI test failed"
            fi
            
            # Test health monitoring
            log_info "Testing health monitoring..."
            if claude-pm health check > /dev/null 2>&1; then
                log_success "Health monitoring is working"
            else
                log_warning "Health monitoring test failed"
            fi
        else
            log_warning "CLI not available in PATH"
        fi
        
        # Test environment configuration
        log_info "Testing environment configuration..."
        if python3 -c "
from claude_pm.core.config import Config
config = Config()
print(f'Base Path: {config.get(\"base_path\")}')
print(f'Claude PM Path: {config.get(\"claude_pm_path\")}')
print(f'Managed Path: {config.get(\"managed_path\")}')
" > /dev/null 2>&1; then
            log_success "Environment configuration is working"
        else
            log_warning "Environment configuration test failed"
        fi
        
    else
        log_info "[DRY RUN] Would run health checks"
    fi
}

# Helper function for user confirmation
ask_confirmation() {
    if [[ "$FORCE_DEPLOYMENT" == "true" ]]; then
        return 0
    fi
    
    read -p "$1 [y/N]: " -r
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Show deployment summary
show_deployment_summary() {
    log_header "Deployment Summary"
    
    echo -e "${CYAN}Environment:${NC} $ENVIRONMENT"
    echo -e "${CYAN}Claude PM Path:${NC} $CLAUDE_PM_PATH"
    echo -e "${CYAN}Base Path:${NC} $BASE_PATH"
    echo -e "${CYAN}Managed Path:${NC} $MANAGED_PATH"
    echo -e "${CYAN}Environment File:${NC} $ENV_FILE"
    
    if [[ -n "${CLAUDE_PM_ROOT:-}" ]]; then
        echo -e "${CYAN}Custom Root:${NC} $CLAUDE_PM_ROOT"
    fi
    
    # Check if CMPM-QA was deployed
    local qa_status="Not deployed"
    if [[ -d "$CLAUDE_PM_PATH/cmpm-qa" ]]; then
        qa_status="Available"
        if [[ -d "$CLAUDE_PM_PATH/.claude-pm/qa-extension" ]]; then
            qa_status="Installed"
        fi
    fi
    echo -e "${CYAN}CMPM-QA Extension:${NC} $qa_status"
    
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Activate virtual environment: source $CLAUDE_PM_PATH/.venv/bin/activate"
    echo "2. Test CLI: claude-pm util info"
    echo "3. Check health: claude-pm health check"
    echo "4. View documentation: $CLAUDE_PM_PATH/docs/"
    
    if [[ "$qa_status" == "Installed" ]]; then
        echo ""
        echo -e "${BLUE}CMPM-QA Extension:${NC}"
        echo "5. Test QA status: python3 -m claude_pm.cmpm_commands cmpm:qa-status"
        echo "6. Run QA tests: python3 -m claude_pm.cmpm_commands cmpm:qa-test --browser"
        echo "7. Validate QA: $CLAUDE_PM_PATH/cmpm-qa/scripts/validate-install.sh"
    elif [[ "$qa_status" == "Available" ]]; then
        echo ""
        echo -e "${BLUE}CMPM-QA Extension (available but not installed):${NC}"
        echo "5. Install QA: $CLAUDE_PM_PATH/cmpm-qa/scripts/install-qa.sh"
        echo "6. Validate QA: $CLAUDE_PM_PATH/cmpm-qa/scripts/validate-install.sh"
    fi
    echo ""
    echo -e "${BLUE}For support:${NC}"
    echo "- Run: claude-pm util doctor"
    echo "- Check logs: $CLAUDE_PM_PATH/logs/"
    echo "- Documentation: $CLAUDE_PM_PATH/docs/"
}

# Main deployment workflow
main() {
    show_banner
    parse_arguments "$@"
    configure_paths
    
    # Show configuration summary
    if [[ "$DEBUG_MODE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        echo "Configuration Summary:"
        echo "  Environment: $ENVIRONMENT"
        echo "  Claude PM Path: $CLAUDE_PM_PATH"
        echo "  Base Path: $BASE_PATH"
        echo "  Managed Path: $MANAGED_PATH"
        echo "  Environment File: $ENV_FILE"
        echo ""
    fi
    
    validate_environment
    
    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        log_success "Validation completed successfully"
        exit 0
    fi
    
    # Confirm deployment
    if [[ "$FORCE_DEPLOYMENT" == "false" ]] && [[ "$DRY_RUN" == "false" ]]; then
        echo ""
        log_warning "This will deploy Claude PM Framework to: $CLAUDE_PM_PATH"
        if ! ask_confirmation "Continue with deployment?"; then
            log_info "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    create_backup
    deploy_framework
    configure_services
    run_health_checks
    
    if [[ "$DRY_RUN" == "false" ]]; then
        show_deployment_summary
    else
        log_info "[DRY RUN] Deployment simulation completed"
    fi
}

# Run main function with all arguments
main "$@"