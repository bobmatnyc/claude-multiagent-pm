#!/bin/bash

# Claude PM Framework - Migration Script
# Migrates existing installations to use CLAUDE_PM_ROOT (M01-039)
# ==============================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Icons
CHECKMARK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
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
echo -e "${CYAN}"
echo "=========================================================="
echo "  Claude PM Framework - Migration Tool"
echo "  CLAUDE_PM_ROOT Migration Assistant (M01-039)"
echo "=========================================================="
echo -e "${NC}"

# Help function
show_help() {
    cat << EOF
Claude PM Framework Migration Tool

USAGE:
    $0 [OPTIONS] [NEW_PATH]

OPTIONS:
    -h, --help              Show this help message
    -d, --dry-run           Show what would be done without executing
    -b, --backup            Create backup before migration
    -f, --force             Force migration without confirmations
    --from PATH             Specify source installation path
    --preserve-env          Keep existing environment configuration

EXAMPLES:
    # Migrate to custom location
    $0 /opt/claude-pm

    # Migrate with backup
    $0 --backup /srv/applications/claude-pm

    # Dry run to see what would happen
    $0 --dry-run /opt/claude-pm

    # Migrate from specific source
    $0 --from /old/path/Claude-PM /new/path/claude-pm

ENVIRONMENT VARIABLES:
    CLAUDE_PM_ROOT          Target migration path (alternative to argument)

This tool helps migrate existing Claude PM installations to support
the new CLAUDE_PM_ROOT environment variable system.
EOF
}

# Parse command line arguments
parse_arguments() {
    TARGET_PATH=""
    SOURCE_PATH=""
    DRY_RUN=false
    CREATE_BACKUP=false
    FORCE_MIGRATION=false
    PRESERVE_ENV=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -b|--backup)
                CREATE_BACKUP=true
                shift
                ;;
            -f|--force)
                FORCE_MIGRATION=true
                shift
                ;;
            --from)
                SOURCE_PATH="$2"
                shift 2
                ;;
            --preserve-env)
                PRESERVE_ENV=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                exit 1
                ;;
            *)
                if [[ -z "$TARGET_PATH" ]]; then
                    TARGET_PATH="$1"
                else
                    log_error "Multiple target paths specified"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Use CLAUDE_PM_ROOT if no target specified
    if [[ -z "$TARGET_PATH" && -n "${CLAUDE_PM_ROOT:-}" ]]; then
        TARGET_PATH="$CLAUDE_PM_ROOT"
        log_info "Using CLAUDE_PM_ROOT as target: $TARGET_PATH"
    fi

    if [[ -z "$TARGET_PATH" ]]; then
        log_error "Target path is required"
        echo "Use --help for usage information"
        exit 1
    fi
}

# Discover existing installations
discover_installations() {
    log_header "Discovering Existing Installations"

    # Common installation locations
    COMMON_LOCATIONS=(
        "$HOME/Projects/Claude-PM"
        "$HOME/Projects/claude-pm"
        "$HOME/Projects/claude-multiagent-pm"
        "/opt/claude-pm"
        "/opt/Claude-PM"
        "/usr/local/claude-pm"
        "/srv/claude-pm"
    )

    if [[ -n "$SOURCE_PATH" ]]; then
        INSTALLATION_CANDIDATES=("$SOURCE_PATH")
    else
        INSTALLATION_CANDIDATES=()
        
        for location in "${COMMON_LOCATIONS[@]}"; do
            if [[ -d "$location" ]]; then
                INSTALLATION_CANDIDATES+=("$location")
            fi
        done
    fi

    # Validate installations
    VALID_INSTALLATIONS=()
    
    for candidate in "${INSTALLATION_CANDIDATES[@]}"; do
        if [[ -f "$candidate/pyproject.toml" ]] || [[ -f "$candidate/package.json" ]] || [[ -d "$candidate/claude_pm" ]]; then
            VALID_INSTALLATIONS+=("$candidate")
            log_success "Found installation: $candidate"
        elif [[ -d "$candidate" ]]; then
            log_warning "Directory exists but doesn't appear to be Claude PM: $candidate"
        fi
    done

    if [[ ${#VALID_INSTALLATIONS[@]} -eq 0 ]]; then
        log_error "No valid Claude PM installations found"
        exit 1
    fi

    # Select source installation
    if [[ ${#VALID_INSTALLATIONS[@]} -eq 1 ]]; then
        SOURCE_INSTALLATION="${VALID_INSTALLATIONS[0]}"
        log_info "Using installation: $SOURCE_INSTALLATION"
    else
        log_info "Multiple installations found:"
        for i in "${!VALID_INSTALLATIONS[@]}"; do
            echo "  $((i+1)). ${VALID_INSTALLATIONS[i]}"
        done
        
        if [[ "$FORCE_MIGRATION" == "false" ]]; then
            read -p "Select installation to migrate [1]: " -r selection
            selection=${selection:-1}
            
            if [[ $selection =~ ^[0-9]+$ ]] && [[ $selection -ge 1 && $selection -le ${#VALID_INSTALLATIONS[@]} ]]; then
                SOURCE_INSTALLATION="${VALID_INSTALLATIONS[$((selection-1))]}"
            else
                log_error "Invalid selection"
                exit 1
            fi
        else
            SOURCE_INSTALLATION="${VALID_INSTALLATIONS[0]}"
            log_info "Force mode: using first installation: $SOURCE_INSTALLATION"
        fi
    fi
}

# Analyze installation
analyze_installation() {
    log_header "Analyzing Installation: $SOURCE_INSTALLATION"

    # Check installation type
    if [[ -f "$SOURCE_INSTALLATION/pyproject.toml" ]]; then
        INSTALLATION_TYPE="python"
        log_success "Python-based installation detected"
    elif [[ -f "$SOURCE_INSTALLATION/package.json" ]]; then
        INSTALLATION_TYPE="nodejs"
        log_success "Node.js-based installation detected"
    else
        INSTALLATION_TYPE="unknown"
        log_warning "Unknown installation type"
    fi

    # Check for virtual environment
    if [[ -d "$SOURCE_INSTALLATION/.venv" ]]; then
        HAS_VENV=true
        log_success "Virtual environment found"
    else
        HAS_VENV=false
        log_info "No virtual environment found"
    fi

    # Check for configuration files
    CONFIG_FILES=()
    
    if [[ -f "$SOURCE_INSTALLATION/.env" ]]; then
        CONFIG_FILES+=(".env")
        log_success "Environment configuration found"
    fi
    
    if [[ -f "$SOURCE_INSTALLATION/config.json" ]]; then
        CONFIG_FILES+=("config.json")
        log_success "JSON configuration found"
    fi
    
    if [[ -d "$SOURCE_INSTALLATION/config" ]]; then
        CONFIG_FILES+=("config/")
        log_success "Configuration directory found"
    fi

    # Check for data and logs
    DATA_DIRS=()
    
    if [[ -d "$SOURCE_INSTALLATION/logs" ]]; then
        DATA_DIRS+=("logs/")
        log_success "Logs directory found"
    fi
    
    if [[ -d "$SOURCE_INSTALLATION/data" ]]; then
        DATA_DIRS+=("data/")
        log_success "Data directory found"
    fi

    # Check for running services
    check_running_services
}

check_running_services() {
    log_info "Checking for running services..."

    RUNNING_SERVICES=()

    # Check for Python processes
    if pgrep -f "claude.pm" &> /dev/null; then
        RUNNING_SERVICES+=("claude-pm")
        log_warning "Claude PM processes are running"
    fi

    # Check for systemd services
    if command -v systemctl &> /dev/null; then
        if systemctl is-active claude-pm-health-monitor &> /dev/null; then
            RUNNING_SERVICES+=("systemd:claude-pm-health-monitor")
            log_warning "systemd service claude-pm-health-monitor is running"
        fi
    fi

    # Check for PM2 processes
    if command -v pm2 &> /dev/null; then
        if pm2 list | grep -q "claude-pm" &> /dev/null; then
            RUNNING_SERVICES+=("pm2:claude-pm")
            log_warning "PM2 processes found"
        fi
    fi

    if [[ ${#RUNNING_SERVICES[@]} -gt 0 ]]; then
        log_warning "Active services detected. Consider stopping them before migration."
    else
        log_success "No running services detected"
    fi
}

# Create migration plan
create_migration_plan() {
    log_header "Creating Migration Plan"

    # Validate target path
    if [[ -e "$TARGET_PATH" ]]; then
        if [[ -d "$TARGET_PATH" ]]; then
            if [[ "$(ls -A "$TARGET_PATH")" ]]; then
                log_warning "Target directory is not empty: $TARGET_PATH"
                if [[ "$FORCE_MIGRATION" == "false" ]]; then
                    read -p "Continue anyway? [y/N]: " -r
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        log_info "Migration cancelled"
                        exit 0
                    fi
                fi
            fi
        else
            log_error "Target path exists but is not a directory: $TARGET_PATH"
            exit 1
        fi
    fi

    # Check target directory permissions
    TARGET_PARENT="$(dirname "$TARGET_PATH")"
    if [[ ! -d "$TARGET_PARENT" ]]; then
        log_info "Parent directory will be created: $TARGET_PARENT"
    elif [[ ! -w "$TARGET_PARENT" ]]; then
        log_error "No write permission to target parent directory: $TARGET_PARENT"
        exit 1
    fi

    # Plan migration steps
    MIGRATION_STEPS=()

    if [[ "$CREATE_BACKUP" == "true" ]]; then
        MIGRATION_STEPS+=("backup")
    fi

    if [[ ${#RUNNING_SERVICES[@]} -gt 0 ]]; then
        MIGRATION_STEPS+=("stop_services")
    fi

    MIGRATION_STEPS+=("create_target")
    MIGRATION_STEPS+=("copy_files")

    if [[ "$HAS_VENV" == "true" ]]; then
        MIGRATION_STEPS+=("migrate_venv")
    fi

    MIGRATION_STEPS+=("update_config")
    MIGRATION_STEPS+=("update_scripts")

    if [[ ${#RUNNING_SERVICES[@]} -gt 0 ]]; then
        MIGRATION_STEPS+=("update_services")
    fi

    # Display migration plan
    log_info "Migration plan:"
    for step in "${MIGRATION_STEPS[@]}"; do
        case $step in
            backup) echo "  1. Create backup of source installation" ;;
            stop_services) echo "  2. Stop running services" ;;
            create_target) echo "  3. Create target directory structure" ;;
            copy_files) echo "  4. Copy framework files" ;;
            migrate_venv) echo "  5. Recreate virtual environment" ;;
            update_config) echo "  6. Update configuration files" ;;
            update_scripts) echo "  7. Update service scripts" ;;
            update_services) echo "  8. Update and restart services" ;;
        esac
    done

    echo ""
    echo -e "${BLUE}Source:${NC} $SOURCE_INSTALLATION"
    echo -e "${BLUE}Target:${NC} $TARGET_PATH"
    echo -e "${BLUE}Type:${NC} $INSTALLATION_TYPE"
}

# Execute migration
execute_migration() {
    log_header "Executing Migration"

    for step in "${MIGRATION_STEPS[@]}"; do
        case $step in
            backup) execute_backup ;;
            stop_services) execute_stop_services ;;
            create_target) execute_create_target ;;
            copy_files) execute_copy_files ;;
            migrate_venv) execute_migrate_venv ;;
            update_config) execute_update_config ;;
            update_scripts) execute_update_scripts ;;
            update_services) execute_update_services ;;
        esac
    done
}

execute_backup() {
    log_info "Creating backup..."

    local backup_dir="$HOME/claude-pm-migration-backup-$(date +%Y%m%d_%H%M%S)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$backup_dir"
        cp -r "$SOURCE_INSTALLATION" "$backup_dir/"
        log_success "Backup created: $backup_dir"
    else
        log_info "[DRY RUN] Would create backup: $backup_dir"
    fi
}

execute_stop_services() {
    log_info "Stopping services..."

    for service in "${RUNNING_SERVICES[@]}"; do
        if [[ "$DRY_RUN" == "false" ]]; then
            case $service in
                systemd:*)
                    service_name="${service#systemd:}"
                    sudo systemctl stop "$service_name" || true
                    log_success "Stopped systemd service: $service_name"
                    ;;
                pm2:*)
                    pm2 stop all || true
                    log_success "Stopped PM2 processes"
                    ;;
                *)
                    pkill -f "$service" || true
                    log_success "Stopped process: $service"
                    ;;
            esac
        else
            log_info "[DRY RUN] Would stop service: $service"
        fi
    done
}

execute_create_target() {
    log_info "Creating target directory structure..."

    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$TARGET_PATH"
        mkdir -p "$(dirname "$TARGET_PATH")/managed"
        log_success "Target directory created: $TARGET_PATH"
    else
        log_info "[DRY RUN] Would create: $TARGET_PATH"
    fi
}

execute_copy_files() {
    log_info "Copying framework files..."

    if [[ "$DRY_RUN" == "false" ]]; then
        # Copy all files except virtual environment
        rsync -av --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
              "$SOURCE_INSTALLATION/" "$TARGET_PATH/"
        log_success "Files copied to target location"
    else
        log_info "[DRY RUN] Would copy files to: $TARGET_PATH"
    fi
}

execute_migrate_venv() {
    log_info "Recreating virtual environment..."

    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$TARGET_PATH"
        
        # Create new virtual environment
        python3 -m venv .venv
        source .venv/bin/activate
        
        # Install dependencies
        if [[ -f "requirements/production.txt" ]]; then
            pip install -r requirements/production.txt
        elif [[ -f "requirements.txt" ]]; then
            pip install -r requirements.txt
        fi
        
        # Install package
        pip install -e .
        
        log_success "Virtual environment recreated"
    else
        log_info "[DRY RUN] Would recreate virtual environment"
    fi
}

execute_update_config() {
    log_info "Updating configuration files..."

    if [[ "$DRY_RUN" == "false" ]]; then
        # Update .env file if it exists
        if [[ -f "$TARGET_PATH/.env" && "$PRESERVE_ENV" == "false" ]]; then
            # Add or update CLAUDE_PM_ROOT
            if grep -q "^CLAUDE_PM_ROOT=" "$TARGET_PATH/.env"; then
                sed -i.bak "s|^CLAUDE_PM_ROOT=.*|CLAUDE_PM_ROOT=$TARGET_PATH|" "$TARGET_PATH/.env"
            else
                echo "" >> "$TARGET_PATH/.env"
                echo "# Migration: Set CLAUDE_PM_ROOT" >> "$TARGET_PATH/.env"
                echo "CLAUDE_PM_ROOT=$TARGET_PATH" >> "$TARGET_PATH/.env"
            fi
            log_success "Updated .env file"
        fi

        # Create shell environment file
        cat > "$TARGET_PATH/set-environment.sh" << EOF
#!/bin/bash
# Claude PM Framework - Environment Setup
# Generated by migration script on $(date)

export CLAUDE_PM_ROOT="$TARGET_PATH"
export PATH="\$CLAUDE_PM_ROOT/.venv/bin:\$PATH"

echo "Claude PM environment configured:"
echo "  CLAUDE_PM_ROOT: \$CLAUDE_PM_ROOT"
echo ""
echo "To activate:"
echo "  source $TARGET_PATH/set-environment.sh"
echo "  source $TARGET_PATH/.venv/bin/activate"
EOF
        chmod +x "$TARGET_PATH/set-environment.sh"
        log_success "Created environment setup script"
    else
        log_info "[DRY RUN] Would update configuration files"
    fi
}

execute_update_scripts() {
    log_info "Updating service scripts..."

    if [[ "$DRY_RUN" == "false" ]]; then
        # Update systemd service files
        if [[ -f "$TARGET_PATH/claude-pm-health-monitor.service" ]]; then
            sed -i.bak "s|ExecStart=.*|ExecStart=$TARGET_PATH/.venv/bin/python $TARGET_PATH/scripts/automated_health_monitor.py|" \
                "$TARGET_PATH/claude-pm-health-monitor.service"
            log_success "Updated systemd service file"
        fi

        # Update PM2 ecosystem file
        if [[ -f "$TARGET_PATH/ecosystem.config.js" ]]; then
            sed -i.bak "s|cwd:.*|cwd: '$TARGET_PATH',|" "$TARGET_PATH/ecosystem.config.js"
            sed -i.bak "s|script:.*|script: '$TARGET_PATH/.venv/bin/python',|" "$TARGET_PATH/ecosystem.config.js"
            log_success "Updated PM2 ecosystem file"
        fi

        # Update cron jobs
        if [[ -f "$TARGET_PATH/claude-pm-doc-sync.cron" ]]; then
            sed -i.bak "s|/path/to/claude-pm|$TARGET_PATH|g" "$TARGET_PATH/claude-pm-doc-sync.cron"
            log_success "Updated cron job file"
        fi
    else
        log_info "[DRY RUN] Would update service scripts"
    fi
}

execute_update_services() {
    log_info "Updating and restarting services..."

    if [[ "$DRY_RUN" == "false" ]]; then
        for service in "${RUNNING_SERVICES[@]}"; do
            case $service in
                systemd:*)
                    service_name="${service#systemd:}"
                    if [[ -f "$TARGET_PATH/$service_name.service" ]]; then
                        sudo cp "$TARGET_PATH/$service_name.service" /etc/systemd/system/
                        sudo systemctl daemon-reload
                        sudo systemctl start "$service_name"
                        log_success "Updated and restarted systemd service: $service_name"
                    fi
                    ;;
                pm2:*)
                    cd "$TARGET_PATH"
                    pm2 start ecosystem.config.js
                    log_success "Restarted PM2 processes"
                    ;;
            esac
        done
    else
        log_info "[DRY RUN] Would update and restart services"
    fi
}

# Show migration summary
show_migration_summary() {
    log_header "Migration Summary"

    echo -e "${CYAN}Migration completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Source Installation:${NC} $SOURCE_INSTALLATION"
    echo -e "${BLUE}Target Installation:${NC} $TARGET_PATH"
    echo -e "${BLUE}Installation Type:${NC} $INSTALLATION_TYPE"
    echo ""

    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Set environment variable:"
    echo "   export CLAUDE_PM_ROOT=\"$TARGET_PATH\""
    echo ""
    echo "2. Activate environment:"
    echo "   source $TARGET_PATH/set-environment.sh"
    echo "   source $TARGET_PATH/.venv/bin/activate"
    echo ""
    echo "3. Test installation:"
    echo "   claude-pm util info"
    echo "   claude-pm health check"
    echo ""
    echo "4. Update shell profile (optional):"
    echo "   echo 'export CLAUDE_PM_ROOT=\"$TARGET_PATH\"' >> ~/.bashrc"
    echo "   echo 'source $TARGET_PATH/set-environment.sh' >> ~/.bashrc"
    echo ""

    if [[ "$CREATE_BACKUP" == "true" ]]; then
        echo -e "${YELLOW}Backup Information:${NC}"
        echo "Original installation backed up before migration"
        echo "Remove backup manually after confirming migration success"
        echo ""
    fi

    echo -e "${BLUE}For support:${NC}"
    echo "- Run: claude-pm util doctor"
    echo "- Check logs: $TARGET_PATH/logs/"
    echo "- Documentation: $TARGET_PATH/docs/"
}

# Ask for confirmation
ask_confirmation() {
    if [[ "$FORCE_MIGRATION" == "true" ]]; then
        return 0
    fi
    
    read -p "$1 [y/N]: " -r
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Main migration workflow
main() {
    parse_arguments "$@"
    discover_installations
    analyze_installation
    create_migration_plan
    
    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    elif [[ "$FORCE_MIGRATION" == "false" ]]; then
        if ! ask_confirmation "Proceed with migration?"; then
            log_info "Migration cancelled by user"
            exit 0
        fi
    fi
    
    execute_migration
    
    if [[ "$DRY_RUN" == "false" ]]; then
        show_migration_summary
    else
        log_info "Dry run completed - no changes were made"
    fi
}

# Run main function
main "$@"