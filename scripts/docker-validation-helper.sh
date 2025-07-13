#!/bin/bash

# Claude Multi-Agent PM Framework - Docker Validation Helper
# Provides utilities for Docker-based pre-publish validation
# DevOps Agent Implementation - 2025-07-13

set -e

# Color codes and icons
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

CHECKMARK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
DOCKER="🐳"

# Project configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_SCRIPT="$PROJECT_ROOT/scripts/pre-publish-docker-validation.js"
CONFIG_FILE="$PROJECT_ROOT/config/docker-validation-config.json"
LOGS_DIR="$PROJECT_ROOT/logs"

# Validation configuration
DOCKER_IMAGE_TAG="claude-pm-validation"
CONTAINER_PREFIX="claude-pm-val"
NETWORK_NAME="claude-pm-test-net"
VOLUME_NAME="claude-pm-test-vol"

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

log_docker() {
    echo -e "${BLUE}${DOCKER} $1${NC}"
}

# Helper functions
show_help() {
    echo -e "${PURPLE}"
    echo "========================================================"
    echo "  Claude PM Framework - Docker Validation Helper"
    echo "  DevOps Agent Docker Validation Management"
    echo "========================================================"
    echo -e "${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  validate       - Run full Docker validation"
    echo "  quick-test     - Run basic Docker environment test"
    echo "  build-env      - Build validation environment only"
    echo "  clean          - Clean up Docker resources"
    echo "  status         - Show Docker validation status"
    echo "  logs           - Show recent validation logs"
    echo "  debug          - Run debug diagnostics"
    echo "  pre-publish    - Full pre-publish validation workflow"
    echo ""
    echo "Options:"
    echo "  --verbose, -v  - Enable verbose output"
    echo "  --dry-run      - Show commands without executing"
    echo "  --force        - Force cleanup even if containers running"
    echo "  --json         - Output JSON format (where applicable)"
    echo ""
    echo "Examples:"
    echo "  $0 validate --verbose"
    echo "  $0 pre-publish"
    echo "  $0 clean --force"
    echo "  $0 debug --json"
    echo ""
}

# Check Docker availability
check_docker() {
    log_header "Checking Docker Environment"
    
    # Check Docker daemon
    if ! docker --version &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        log_info "Start Docker Desktop or ensure Docker service is running"
        return 1
    fi
    
    log_success "Docker daemon is running"
    
    # Check Docker Compose
    if docker-compose --version &> /dev/null; then
        log_success "Docker Compose is available"
    else
        log_warning "Docker Compose not available"
    fi
    
    # Show Docker info
    local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_success "Docker version: $docker_version"
    
    return 0
}

# Run validation
run_validation() {
    local args=("$@")
    
    log_header "Running Docker Pre-Publish Validation"
    
    if ! check_docker; then
        log_error "Docker environment check failed"
        return 1
    fi
    
    log_docker "Starting validation with: node $VALIDATION_SCRIPT ${args[*]}"
    
    if [[ ! -f "$VALIDATION_SCRIPT" ]]; then
        log_error "Validation script not found: $VALIDATION_SCRIPT"
        return 1
    fi
    
    # Run the validation
    if node "$VALIDATION_SCRIPT" "${args[@]}"; then
        log_success "Docker validation completed successfully"
        return 0
    else
        log_error "Docker validation failed"
        return 1
    fi
}

# Quick Docker test
quick_test() {
    log_header "Quick Docker Environment Test"
    
    if ! check_docker; then
        return 1
    fi
    
    # Test basic Docker operations
    log_info "Testing Docker operations..."
    
    # Test image pull
    if docker pull hello-world &> /dev/null; then
        log_success "Docker image pull works"
    else
        log_error "Docker image pull failed"
        return 1
    fi
    
    # Test container run
    if docker run --rm hello-world &> /dev/null; then
        log_success "Docker container run works"
    else
        log_error "Docker container run failed"
        return 1
    fi
    
    # Test network creation
    local test_network="claude-pm-test-$$"
    if docker network create "$test_network" &> /dev/null; then
        log_success "Docker network creation works"
        docker network rm "$test_network" &> /dev/null
    else
        log_error "Docker network creation failed"
        return 1
    fi
    
    log_success "Quick Docker test passed"
    return 0
}

# Build validation environment
build_environment() {
    local force_rebuild=false
    
    if [[ "$1" == "--force" ]]; then
        force_rebuild=true
    fi
    
    log_header "Building Docker Validation Environment"
    
    if ! check_docker; then
        return 1
    fi
    
    # Check if image already exists
    if docker images | grep -q "$DOCKER_IMAGE_TAG" && [[ "$force_rebuild" != "true" ]]; then
        log_info "Validation image already exists. Use --force to rebuild."
        return 0
    fi
    
    # Build the validation image
    local dockerfile_path="$PROJECT_ROOT/deployment/docker/Dockerfile"
    
    if [[ ! -f "$dockerfile_path" ]]; then
        log_error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    log_docker "Building validation image from $dockerfile_path"
    
    if docker build \
        -f "$dockerfile_path" \
        -t "${DOCKER_IMAGE_TAG}:testing" \
        --target testing \
        --build-arg "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg "VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        "$PROJECT_ROOT"; then
        log_success "Validation environment built successfully"
        return 0
    else
        log_error "Failed to build validation environment"
        return 1
    fi
}

# Clean up Docker resources
cleanup_docker() {
    local force_cleanup=false
    
    if [[ "$1" == "--force" ]]; then
        force_cleanup=true
    fi
    
    log_header "Cleaning Up Docker Validation Resources"
    
    # Stop and remove containers
    local containers=$(docker ps -a --filter "name=${CONTAINER_PREFIX}" -q)
    if [[ -n "$containers" ]]; then
        log_docker "Stopping and removing validation containers..."
        echo "$containers" | xargs docker stop &> /dev/null || true
        echo "$containers" | xargs docker rm &> /dev/null || true
        log_success "Containers cleaned up"
    fi
    
    # Remove network
    if docker network ls | grep -q "$NETWORK_NAME"; then
        log_docker "Removing validation network..."
        docker network rm "$NETWORK_NAME" &> /dev/null || true
        log_success "Network cleaned up"
    fi
    
    # Remove volume
    if docker volume ls | grep -q "$VOLUME_NAME"; then
        log_docker "Removing validation volume..."
        docker volume rm "$VOLUME_NAME" &> /dev/null || true
        log_success "Volume cleaned up"
    fi
    
    # Remove images (only if force)
    if [[ "$force_cleanup" == "true" ]]; then
        local images=$(docker images --filter "reference=${DOCKER_IMAGE_TAG}" -q)
        if [[ -n "$images" ]]; then
            log_docker "Removing validation images..."
            echo "$images" | xargs docker rmi -f &> /dev/null || true
            log_success "Images cleaned up"
        fi
    fi
    
    log_success "Docker cleanup completed"
}

# Show validation status
show_status() {
    log_header "Docker Validation Status"
    
    if ! check_docker; then
        return 1
    fi
    
    # Check validation image
    if docker images | grep -q "$DOCKER_IMAGE_TAG"; then
        log_success "Validation image exists"
        docker images | grep "$DOCKER_IMAGE_TAG" | head -1
    else
        log_warning "Validation image not found"
    fi
    
    # Check running containers
    local containers=$(docker ps --filter "name=${CONTAINER_PREFIX}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")
    if [[ -n "$containers" ]] && [[ "$containers" != "NAMES	STATUS	PORTS" ]]; then
        log_info "Running validation containers:"
        echo "$containers"
    else
        log_info "No validation containers running"
    fi
    
    # Check network
    if docker network ls | grep -q "$NETWORK_NAME"; then
        log_success "Validation network exists"
    else
        log_info "Validation network not found"
    fi
    
    # Check volume
    if docker volume ls | grep -q "$VOLUME_NAME"; then
        log_success "Validation volume exists"
    else
        log_info "Validation volume not found"
    fi
}

# Show recent logs
show_logs() {
    log_header "Recent Validation Logs"
    
    if [[ ! -d "$LOGS_DIR" ]]; then
        log_warning "Logs directory not found: $LOGS_DIR"
        return 1
    fi
    
    # Find recent validation logs
    local log_files=$(find "$LOGS_DIR" -name "docker-validation-*.json" -type f -mtime -7 | sort -r | head -5)
    
    if [[ -z "$log_files" ]]; then
        log_info "No recent validation logs found"
        return 0
    fi
    
    log_info "Recent validation logs:"
    for log_file in $log_files; do
        local timestamp=$(basename "$log_file" | sed 's/docker-validation-\(.*\)\.json/\1/')
        local success=$(jq -r '.summary.overallSuccess // false' "$log_file" 2>/dev/null)
        local errors=$(jq -r '.summary.totalErrors // 0' "$log_file" 2>/dev/null)
        
        if [[ "$success" == "true" ]]; then
            log_success "$(basename "$log_file") - SUCCESS"
        else
            log_error "$(basename "$log_file") - FAILED ($errors errors)"
        fi
    done
}

# Debug diagnostics
run_debug() {
    local output_json=false
    
    if [[ "$1" == "--json" ]]; then
        output_json=true
    fi
    
    log_header "Docker Validation Debug Diagnostics"
    
    local debug_info=()
    
    # Docker system info
    debug_info+=("Docker System Info:")
    debug_info+=("$(docker system info 2>&1 | head -10)")
    debug_info+=("")
    
    # Docker images
    debug_info+=("Validation Images:")
    debug_info+=("$(docker images | grep claude-pm || echo 'No validation images found')")
    debug_info+=("")
    
    # Docker containers
    debug_info+=("Validation Containers:")
    debug_info+=("$(docker ps -a | grep claude-pm || echo 'No validation containers found')")
    debug_info+=("")
    
    # Docker networks
    debug_info+=("Validation Networks:")
    debug_info+=("$(docker network ls | grep claude-pm || echo 'No validation networks found')")
    debug_info+=("")
    
    # Docker volumes
    debug_info+=("Validation Volumes:")
    debug_info+=("$(docker volume ls | grep claude-pm || echo 'No validation volumes found')")
    debug_info+=("")
    
    # System resources
    debug_info+=("System Resources:")
    debug_info+=("$(docker system df)")
    debug_info+=("")
    
    if [[ "$output_json" == "true" ]]; then
        # Output as JSON
        echo "{"
        echo "  \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\","
        echo "  \"debug_info\": ["
        for ((i=0; i<${#debug_info[@]}; i++)); do
            echo -n "    \"${debug_info[i]//\"/\\\"}\""
            if [[ $i -lt $((${#debug_info[@]} - 1)) ]]; then
                echo ","
            else
                echo ""
            fi
        done
        echo "  ]"
        echo "}"
    else
        # Output as text
        for line in "${debug_info[@]}"; do
            echo "$line"
        done
    fi
}

# Pre-publish workflow
pre_publish_workflow() {
    local args=("$@")
    
    log_header "Pre-Publish Docker Validation Workflow"
    
    # Step 1: Environment check
    if ! check_docker; then
        log_error "Pre-publish validation failed: Docker environment not ready"
        return 1
    fi
    
    # Step 2: Build environment
    log_info "Building validation environment..."
    if ! build_environment; then
        log_error "Pre-publish validation failed: Could not build environment"
        return 1
    fi
    
    # Step 3: Run full validation
    log_info "Running comprehensive validation..."
    if ! run_validation "${args[@]}"; then
        log_error "Pre-publish validation failed: Validation tests failed"
        return 1
    fi
    
    # Step 4: Cleanup
    log_info "Cleaning up validation resources..."
    cleanup_docker
    
    log_success "Pre-publish validation workflow completed successfully"
    log_info "Package is ready for npm publish"
    return 0
}

# Main command dispatcher
main() {
    local command="$1"
    shift
    
    case "$command" in
        "validate")
            run_validation "$@"
            ;;
        "quick-test")
            quick_test
            ;;
        "build-env")
            build_environment "$@"
            ;;
        "clean")
            cleanup_docker "$@"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "debug")
            run_debug "$@"
            ;;
        "pre-publish")
            pre_publish_workflow "$@"
            ;;
        "help" | "--help" | "-h" | "")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"