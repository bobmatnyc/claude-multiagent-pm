#!/bin/bash
# Claude PM Framework - Docker Installation Test Runner
# Tests both PyPI and npm installations in clean Docker containers

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${GREEN}=== Claude PM Docker Installation Tests ===${NC}"
echo "Testing clean installations in isolated Docker containers"
echo

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Determine docker-compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Get version and git info
CLAUDE_PM_VERSION=$(cat VERSION)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Export for docker-compose
export CLAUDE_PM_VERSION
export BUILD_DATE
export VCS_REF

# Create results directory
mkdir -p test-results
rm -rf test-results/*

# Function to run a test
run_test() {
    local service=$1
    local name=$2
    
    echo -e "${YELLOW}Running $name test...${NC}"
    
    # Build the image
    echo "Building $service image..."
    $DOCKER_COMPOSE build $service
    
    # Run the test
    echo "Running $service tests..."
    if $DOCKER_COMPOSE run --rm $service > "test-results/${service}-output.log" 2>&1; then
        echo -e "${GREEN}✓ $name test passed${NC}"
        echo "PASSED" > "test-results/${service}-status.txt"
        return 0
    else
        echo -e "${RED}✗ $name test failed${NC}"
        echo "FAILED" > "test-results/${service}-status.txt"
        return 1
    fi
}

# Run tests
echo "Starting installation tests..."
echo

# Track overall success
all_passed=true

# Run PyPI test
if ! run_test "pypi-test" "PyPI installation"; then
    all_passed=false
fi
echo

# Run npm test
if ! run_test "npm-test" "npm installation"; then
    all_passed=false
fi
echo

# Run integration test
if ! run_test "integration-test" "integration"; then
    all_passed=false
fi
echo

# Generate summary report
echo -e "${YELLOW}Generating test report...${NC}"
cat > test-results/summary.md << EOF
# Claude PM Installation Test Report

**Date**: $(date)
**Version**: $CLAUDE_PM_VERSION
**Git Ref**: $VCS_REF

## Test Results

### PyPI Installation Test
**Status**: $(cat test-results/pypi-test-status.txt 2>/dev/null || echo "NOT RUN")

\`\`\`
$(tail -n 20 test-results/pypi-test-output.log 2>/dev/null || echo "No output available")
\`\`\`

### npm Installation Test
**Status**: $(cat test-results/npm-test-status.txt 2>/dev/null || echo "NOT RUN")

\`\`\`
$(tail -n 20 test-results/npm-test-output.log 2>/dev/null || echo "No output available")
\`\`\`

### Integration Test
**Status**: $(cat test-results/integration-test-status.txt 2>/dev/null || echo "NOT RUN")

\`\`\`
$(tail -n 20 test-results/integration-test-output.log 2>/dev/null || echo "No output available")
\`\`\`

## Summary

- PyPI Test: $(cat test-results/pypi-test-status.txt 2>/dev/null || echo "NOT RUN")
- npm Test: $(cat test-results/npm-test-status.txt 2>/dev/null || echo "NOT RUN")
- Integration Test: $(cat test-results/integration-test-status.txt 2>/dev/null || echo "NOT RUN")

EOF

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
$DOCKER_COMPOSE down --remove-orphans

# Show results
echo
echo -e "${GREEN}=== Test Summary ===${NC}"
echo "PyPI Test: $(cat test-results/pypi-test-status.txt 2>/dev/null || echo "NOT RUN")"
echo "npm Test: $(cat test-results/npm-test-status.txt 2>/dev/null || echo "NOT RUN")"
echo "Integration Test: $(cat test-results/integration-test-status.txt 2>/dev/null || echo "NOT RUN")"
echo
echo "Full results available in: test-results/"
echo "- PyPI output: test-results/pypi-test-output.log"
echo "- npm output: test-results/npm-test-output.log"
echo "- Integration output: test-results/integration-test-output.log"
echo "- Summary: test-results/summary.md"

# Exit with appropriate code
if [ "$all_passed" = true ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi