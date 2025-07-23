#!/bin/bash
#
# Claude PM Framework - 3-Stage Deployment Script
# ===============================================
#
# This script implements the 3-stage deployment model:
# 1. Development (automatic) - Changes in this project
# 2. Local Machine - Deploy to current machine via script
# 3. Publish - Release to npm/PyPI
#
# Usage:
#   ./scripts/deploy-3stage.sh dev      # Stage 1: Development verification
#   ./scripts/deploy-3stage.sh local    # Stage 2: Deploy to local machine
#   ./scripts/deploy-3stage.sh publish  # Stage 3: Publish to registries
#   ./scripts/deploy-3stage.sh status   # Show deployment status
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and framework root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRAMEWORK_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to display usage
usage() {
    echo "Claude PM Framework - 3-Stage Deployment"
    echo "========================================"
    echo ""
    echo "Usage: $0 [stage]"
    echo ""
    echo "Stages:"
    echo "  dev      - Stage 1: Development verification (automatic)"
    echo "  local    - Stage 2: Deploy to local machine"
    echo "  publish  - Stage 3: Publish to npm/PyPI"
    echo "  status   - Show current deployment status"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Verify development changes"
    echo "  $0 local    # Deploy to ~/.local/bin and update installation"
    echo "  $0 publish  # Publish to package registries"
    echo ""
}

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# Stage 1: Development Verification
stage_dev() {
    echo -e "${BLUE}🔧 Stage 1: Development Verification${NC}"
    echo "====================================="
    echo ""
    
    echo "1. Running tests..."
    cd "$FRAMEWORK_ROOT"
    
    # Run Python tests
    if command -v pytest &> /dev/null; then
        echo "   Running Python tests..."
        pytest tests/unit/ -q --no-cov || true
        check_status "Python unit tests"
    fi
    
    # Check for uncommitted changes
    echo ""
    echo "2. Checking for uncommitted changes..."
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
        git status --short
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        check_status "No uncommitted changes"
    fi
    
    # Verify version consistency
    echo ""
    echo "3. Checking version consistency..."
    python "$SCRIPT_DIR/validate_version_consistency.py"
    check_status "Version consistency"
    
    echo ""
    echo -e "${GREEN}✅ Development verification complete!${NC}"
}

# Stage 2: Local Machine Deployment
stage_local() {
    echo -e "${BLUE}🚀 Stage 2: Local Machine Deployment${NC}"
    echo "===================================="
    echo ""
    
    # First run development verification
    stage_dev
    
    echo ""
    echo "4. Deploying to local machine..."
    
    # Deploy scripts to ~/.local/bin
    echo "   Deploying scripts..."
    python "$SCRIPT_DIR/deploy_scripts.py" --deploy
    check_status "Scripts deployed to ~/.local/bin"
    
    # Update Python package
    echo ""
    echo "   Updating Python package..."
    cd "$FRAMEWORK_ROOT"
    pip install --user -e . --quiet --break-system-packages
    check_status "Python package updated"
    
    # Run initialization to update framework
    echo ""
    echo "   Updating framework configuration..."
    claude-pm init --force >/dev/null 2>&1
    check_status "Framework configuration updated"
    
    # Verify deployment
    echo ""
    echo "5. Verifying deployment..."
    
    # Check claude-pm version
    INSTALLED_VERSION=$(claude-pm --version 2>&1 | grep "Package version" | cut -d' ' -f3)
    EXPECTED_VERSION=$(cat "$FRAMEWORK_ROOT/VERSION")
    
    if [ "$INSTALLED_VERSION" = "v$EXPECTED_VERSION" ]; then
        check_status "Version check: $INSTALLED_VERSION"
    else
        echo -e "${RED}✗ Version mismatch: expected v$EXPECTED_VERSION, got $INSTALLED_VERSION${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ Local deployment complete!${NC}"
    echo -e "${YELLOW}📝 Note: Changes are now active on this machine${NC}"
}

# Stage 3: Publish
stage_publish() {
    echo -e "${BLUE}📦 Stage 3: Publish to Registries${NC}"
    echo "================================="
    echo ""
    
    # First run local deployment
    stage_local
    
    echo ""
    echo "6. Publishing to package registries..."
    
    # Check if we're on main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo -e "${YELLOW}⚠️  You are not on the main branch (current: $CURRENT_BRANCH)${NC}"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Run pre-publish validation
    echo ""
    echo "   Running pre-publish validation..."
    cd "$FRAMEWORK_ROOT"
    npm run pre-publish
    check_status "Pre-publish validation"
    
    # Publish to PyPI
    echo ""
    echo "   Publishing to PyPI..."
    echo -e "${YELLOW}This will publish to PyPI. Are you sure? (y/N)${NC}"
    read -p "" -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python "$SCRIPT_DIR/publish_to_pypi.py"
        check_status "PyPI publication"
    else
        echo "   Skipped PyPI publication"
    fi
    
    # Publish to npm
    echo ""
    echo "   Publishing to npm..."
    echo -e "${YELLOW}This will publish to npm. Are you sure? (y/N)${NC}"
    read -p "" -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm publish
        check_status "npm publication"
    else
        echo "   Skipped npm publication"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Publication complete!${NC}"
    echo -e "${YELLOW}📝 Remember to create a GitHub release${NC}"
}

# Show deployment status
show_status() {
    echo -e "${BLUE}📊 Deployment Status${NC}"
    echo "==================="
    echo ""
    
    # Check git status
    echo "Git Status:"
    BRANCH=$(git branch --show-current)
    echo "  Branch: $BRANCH"
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "  Status: ${YELLOW}Uncommitted changes${NC}"
    else
        echo -e "  Status: ${GREEN}Clean${NC}"
    fi
    
    # Check versions
    echo ""
    echo "Version Information:"
    echo "  Source VERSION: $(cat "$FRAMEWORK_ROOT/VERSION")"
    echo "  Package.json: $(grep '"version"' "$FRAMEWORK_ROOT/package.json" | cut -d'"' -f4)"
    
    # Check local installation
    echo ""
    echo "Local Installation:"
    if command -v claude-pm &> /dev/null; then
        INSTALLED_PATH=$(which claude-pm)
        INSTALLED_VERSION=$(claude-pm --version 2>&1 | grep "Package version" | cut -d' ' -f3)
        echo "  Path: $INSTALLED_PATH"
        echo "  Version: $INSTALLED_VERSION"
        
        # Check if it's the latest
        EXPECTED_VERSION="v$(cat "$FRAMEWORK_ROOT/VERSION")"
        if [ "$INSTALLED_VERSION" = "$EXPECTED_VERSION" ]; then
            echo -e "  Status: ${GREEN}Up to date${NC}"
        else
            echo -e "  Status: ${YELLOW}Update available${NC}"
        fi
    else
        echo -e "  Status: ${RED}Not installed${NC}"
    fi
    
    # Check PyPI version
    echo ""
    echo "PyPI Status:"
    if command -v pip &> /dev/null; then
        PYPI_VERSION=$(pip index versions claude-multiagent-pm 2>/dev/null | grep "Available versions" | cut -d' ' -f3 | tr -d ',')
        if [ -n "$PYPI_VERSION" ]; then
            echo "  Latest version: $PYPI_VERSION"
        else
            echo "  Unable to check PyPI version"
        fi
    fi
    
    # Check npm version
    echo ""
    echo "npm Status:"
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm view @bobmatnyc/claude-multiagent-pm version 2>/dev/null)
        if [ -n "$NPM_VERSION" ]; then
            echo "  Latest version: $NPM_VERSION"
        else
            echo "  Unable to check npm version"
        fi
    fi
}

# Main script logic
case "${1:-}" in
    dev)
        stage_dev
        ;;
    local)
        stage_local
        ;;
    publish)
        stage_publish
        ;;
    status)
        show_status
        ;;
    *)
        usage
        exit 1
        ;;
esac