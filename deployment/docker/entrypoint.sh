#!/bin/bash

# Claude PM Framework - Docker Entrypoint Script
# CLAUDE_PM_ROOT Container Support (M01-039)
# ===========================================

set -e

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [ENTRYPOINT]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [ENTRYPOINT]${NC} ✅ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [ENTRYPOINT]${NC} ⚠️ $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ENTRYPOINT]${NC} ❌ $1"
}

# Print banner
echo -e "${BLUE}"
echo "========================================================"
echo "  Claude PM Framework - Docker Container"
echo "  Version: ${CLAUDE_PM_VERSION:-unknown}"
echo "  CLAUDE_PM_ROOT: ${CLAUDE_PM_ROOT}"
echo "========================================================"
echo -e "${NC}"

# Environment validation
validate_environment() {
    log "Validating container environment..."

    # Check required environment variables
    if [[ -z "${CLAUDE_PM_ROOT}" ]]; then
        log_error "CLAUDE_PM_ROOT environment variable is not set"
        exit 1
    fi

    # Check directory structure
    local required_dirs=(
        "${CLAUDE_PM_ROOT}"
        "${CLAUDE_PM_DATA_PATH:-/app/data}"
        "${CLAUDE_PM_LOGS_PATH:-/app/logs}"
        "${CLAUDE_PM_CONFIG_PATH:-/app/config}"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warning "Directory does not exist: $dir"
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        fi
    done

    # Check Python environment
    if ! python -c "import claude_pm" &> /dev/null; then
        log_error "Claude PM package is not properly installed"
        exit 1
    fi

    log_success "Environment validation completed"
}

# Initialize configuration
initialize_configuration() {
    log "Initializing configuration..."

    # Set default environment variables for container
    export ENVIRONMENT="${ENVIRONMENT:-docker}"
    export CLAUDE_PM_LOG_LEVEL="${CLAUDE_PM_LOG_LEVEL:-INFO}"
    export CLAUDE_PM_LOG_TO_STDOUT="${CLAUDE_PM_LOG_TO_STDOUT:-true}"
    export CLAUDE_PM_LOG_JSON_FORMAT="${CLAUDE_PM_LOG_JSON_FORMAT:-true}"

    # Container-specific settings
    export CLAUDE_PM_CONTAINER="true"
    export CLAUDE_PM_HEALTH_CHECK_ENABLED="${CLAUDE_PM_HEALTH_CHECK_ENABLED:-true}"
    export CLAUDE_PM_METRICS_ENABLED="${CLAUDE_PM_METRICS_ENABLED:-true}"

    # Network configuration
    export CLAUDE_PM_DASHBOARD_PORT="${CLAUDE_PM_DASHBOARD_PORT:-7001}"
    export CLAUDE_PM_API_PORT="${CLAUDE_PM_API_PORT:-8001}"

    # Service discovery (Docker Compose)
    export MEM0AI_HOST="${MEM0AI_HOST:-mem0ai-service}"
    export MEM0AI_PORT="${MEM0AI_PORT:-8002}"

    log_success "Configuration initialized"
}

# Test configuration
test_configuration() {
    log "Testing Claude PM configuration..."

    # Test configuration loading
    if python -c "
from claude_pm.core.config import Config
config = Config()
print(f'Base Path: {config.get(\"base_path\")}')
print(f'Claude PM Path: {config.get(\"claude_pm_path\")}')
print(f'Managed Path: {config.get(\"managed_path\")}')
print(f'Log Level: {config.get(\"log_level\")}')
" 2>/dev/null; then
        log_success "Configuration test passed"
    else
        log_error "Configuration test failed"
        exit 1
    fi
}

# Setup signal handlers
setup_signal_handlers() {
    log "Setting up signal handlers..."

    # Graceful shutdown function
    shutdown_handler() {
        log "Received shutdown signal, performing graceful shutdown..."
        
        # Stop services if running
        if pgrep -f "claude-pm" > /dev/null; then
            log "Stopping Claude PM services..."
            pkill -TERM -f "claude-pm" || true
            
            # Wait for graceful shutdown
            local timeout=30
            while [[ $timeout -gt 0 ]] && pgrep -f "claude-pm" > /dev/null; do
                sleep 1
                ((timeout--))
            done
            
            # Force kill if still running
            if pgrep -f "claude-pm" > /dev/null; then
                log_warning "Force killing remaining processes..."
                pkill -KILL -f "claude-pm" || true
            fi
        fi
        
        log_success "Graceful shutdown completed"
        exit 0
    }

    # Trap signals
    trap shutdown_handler SIGTERM SIGINT SIGQUIT

    log_success "Signal handlers configured"
}

# Health check function
health_check() {
    log "Performing container health check..."

    # Check if Python can import the package
    if ! python -c "from claude_pm.core.config import Config; Config()" &> /dev/null; then
        log_error "Health check failed: Cannot import Claude PM"
        return 1
    fi

    # Check if services are responsive (if running)
    if pgrep -f "claude-pm" > /dev/null; then
        # Add specific service health checks here
        log_success "Services are running"
    fi

    log_success "Health check passed"
    return 0
}

# Development mode setup
setup_development_mode() {
    if [[ "${ENVIRONMENT}" == "development" ]] || [[ "${CLAUDE_PM_DEV_MODE}" == "true" ]]; then
        log "Setting up development mode..."

        # Enable debug logging
        export CLAUDE_PM_LOG_LEVEL="DEBUG"
        export CLAUDE_PM_DEBUG="true"
        export CLAUDE_PM_VERBOSE="true"

        # Enable hot reload if requested
        if [[ "${CLAUDE_PM_HOT_RELOAD}" == "true" ]]; then
            log "Hot reload enabled"
        fi

        log_success "Development mode configured"
    fi
}

# Wait for dependencies
wait_for_dependencies() {
    log "Waiting for service dependencies..."

    # Wait for mem0AI service if configured
    if [[ -n "${MEM0AI_HOST:-}" ]] && [[ "${MEM0AI_HOST}" != "localhost" ]]; then
        local max_attempts=30
        local attempt=1

        while [[ $attempt -le $max_attempts ]]; do
            if nc -z "${MEM0AI_HOST}" "${MEM0AI_PORT:-8002}" 2>/dev/null; then
                log_success "mem0AI service is available at ${MEM0AI_HOST}:${MEM0AI_PORT:-8002}"
                break
            fi

            log "Waiting for mem0AI service... (attempt $attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        done

        if [[ $attempt -gt $max_attempts ]]; then
            log_warning "mem0AI service not available, continuing anyway"
        fi
    fi

    # Wait for database if configured
    if [[ -n "${DATABASE_URL:-}" ]]; then
        log "Waiting for database connection..."
        # Add database connection check here
    fi

    log_success "Dependency check completed"
}

# Execute pre-start hooks
execute_pre_start_hooks() {
    log "Executing pre-start hooks..."

    # Run migrations if needed
    if [[ -f "${CLAUDE_PM_ROOT}/migrations/migrate.py" ]]; then
        log "Running database migrations..."
        python "${CLAUDE_PM_ROOT}/migrations/migrate.py"
    fi

    # Initialize data directories
    local data_dirs=(
        "${CLAUDE_PM_DATA_PATH}/projects"
        "${CLAUDE_PM_LOGS_PATH}/health"
        "${CLAUDE_PM_LOGS_PATH}/services"
    )

    for dir in "${data_dirs[@]}"; do
        mkdir -p "$dir"
    done

    log_success "Pre-start hooks completed"
}

# Main container startup logic
main() {
    log "Starting Claude PM Framework container..."

    # Core initialization
    validate_environment
    initialize_configuration
    setup_signal_handlers
    setup_development_mode
    test_configuration

    # Service preparation
    wait_for_dependencies
    execute_pre_start_hooks

    # Handle different command types
    if [[ $# -eq 0 ]] || [[ "${1:-}" == "start" ]]; then
        # Default: start all services
        log "Starting Claude PM services..."
        exec python -m claude_pm.cli service start
        
    elif [[ "$1" == "health" ]]; then
        # Health check command
        health_check
        exit $?
        
    elif [[ "$1" == "shell" ]]; then
        # Interactive shell
        log "Starting interactive shell..."
        exec /bin/bash
        
    elif [[ "$1" == "test" ]]; then
        # Run tests
        log "Running tests..."
        if [[ -d "${CLAUDE_PM_ROOT}/tests" ]]; then
            exec python -m pytest "${CLAUDE_PM_ROOT}/tests" -v
        else
            log_error "Tests directory not found"
            exit 1
        fi
        
    elif [[ "$1" == "validate" ]]; then
        # Validate configuration
        log "Validating configuration..."
        exec python -c "
from claude_pm.core.config import Config
config = Config()
print('✅ Configuration is valid')
print(f'Claude PM Root: {config.get(\"claude_pm_path\")}')
print(f'Environment: {config.get(\"environment\", \"unknown\")}')
"
        
    elif [[ "$1" == "claude-pm" ]]; then
        # Direct CLI command
        shift
        exec python -m claude_pm.cli "$@"
        
    else
        # Custom command
        log "Executing custom command: $*"
        exec "$@"
    fi
}

# Run main function with all arguments
main "$@"