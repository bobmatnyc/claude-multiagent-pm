#!/bin/bash
# Quick installation test without Docker
# Tests installation in temporary virtual environments

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Claude PM Quick Installation Test ===${NC}"
echo "Testing installations in temporary environments"
echo

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"
cd "$TEMP_DIR"

# Function to test PyPI installation
test_pypi() {
    echo -e "${YELLOW}Testing PyPI installation...${NC}"
    
    # Create virtual environment
    python3 -m venv pypi-test-env
    source pypi-test-env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install claude-multiagent-pm
    echo "Installing claude-multiagent-pm from PyPI..."
    if pip install claude-multiagent-pm; then
        echo -e "${GREEN}✓ PyPI installation successful${NC}"
        
        # Test import
        if python -c "import claude_pm; print(f'Version: {claude_pm.__version__}')"; then
            echo -e "${GREEN}✓ Python import successful${NC}"
        else
            echo -e "${RED}✗ Python import failed${NC}"
            return 1
        fi
        
        # Test CLI
        if claude-pm --version; then
            echo -e "${GREEN}✓ CLI command successful${NC}"
        else
            echo -e "${RED}✗ CLI command failed${NC}"
            return 1
        fi
        
        # Test ai-trackdown integration
        if python -c "import ai_trackdown_pytools; print('ai-trackdown integration OK')"; then
            echo -e "${GREEN}✓ ai-trackdown-pytools integration successful${NC}"
        else
            echo -e "${YELLOW}⚠ ai-trackdown-pytools not available (optional)${NC}"
        fi
        
    else
        echo -e "${RED}✗ PyPI installation failed${NC}"
        return 1
    fi
    
    deactivate
    return 0
}

# Function to test npm installation
test_npm() {
    echo -e "\n${YELLOW}Testing npm installation...${NC}"
    
    # Create local npm directory
    mkdir npm-test
    cd npm-test
    
    # Initialize npm project
    npm init -y > /dev/null 2>&1
    
    # Install claude-multiagent-pm
    echo "Installing @bobmatnyc/claude-multiagent-pm from npm..."
    if npm install @bobmatnyc/claude-multiagent-pm; then
        echo -e "${GREEN}✓ npm installation successful${NC}"
        
        # Test CLI using npx
        if npx claude-pm --version; then
            echo -e "${GREEN}✓ npm CLI command successful${NC}"
        else
            echo -e "${RED}✗ npm CLI command failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ npm installation failed${NC}"
        return 1
    fi
    
    cd ..
    return 0
}

# Run tests
all_passed=true

if ! test_pypi; then
    all_passed=false
fi

if ! test_npm; then
    all_passed=false
fi

# Clean up
echo -e "\n${YELLOW}Cleaning up...${NC}"
cd /
rm -rf "$TEMP_DIR"

# Summary
echo -e "\n${GREEN}=== Test Summary ===${NC}"
if [ "$all_passed" = true ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi