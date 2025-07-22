#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐳 Claude PM - Docker Installation Tests${NC}"
echo -e "${YELLOW}=================================================${NC}"
echo ""
echo "This test runs in Docker containers - completely isolated from your system."
echo ""

# Clean up any existing test containers
echo "Cleaning up previous test containers..."
docker rm -f claude-pm-test-pypi claude-pm-test-npm 2>/dev/null || true

# Test 1: PyPI Installation
echo -e "\n${YELLOW}Test 1: PyPI Installation${NC}"
echo -e "${YELLOW}------------------------${NC}"

# Build PyPI test image
echo "Building PyPI test image..."
docker build -f Dockerfile.pypi -t claude-pm-test:pypi . || {
    echo -e "${RED}Failed to build PyPI test image${NC}"
    exit 1
}

# Run PyPI tests
echo "Running PyPI installation tests..."
docker run --rm --name claude-pm-test-pypi claude-pm-test:pypi python scripts/test_docker_install.py || {
    echo -e "${RED}PyPI tests failed${NC}"
    PYPI_FAILED=1
}

# Test 2: NPM Installation
echo -e "\n${YELLOW}Test 2: NPM Installation${NC}"
echo -e "${YELLOW}------------------------${NC}"

# Build NPM test image
echo "Building NPM test image..."
docker build -f Dockerfile.npm -t claude-pm-test:npm . || {
    echo -e "${RED}Failed to build NPM test image${NC}"
    exit 1
}

# Run NPM tests
echo "Running NPM installation tests..."
docker run --rm --name claude-pm-test-npm claude-pm-test:npm python scripts/test_docker_install.py || {
    echo -e "${RED}NPM tests failed${NC}"
    NPM_FAILED=1
}

# Summary
echo -e "\n${YELLOW}=================================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}=================================================${NC}"

if [ -z "$PYPI_FAILED" ] && [ -z "$NPM_FAILED" ]; then
    echo -e "${GREEN}✅ All Docker installation tests passed!${NC}"
    echo -e "${GREEN}Both PyPI and NPM installations are working correctly.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed:${NC}"
    [ ! -z "$PYPI_FAILED" ] && echo -e "${RED}  - PyPI installation tests failed${NC}"
    [ ! -z "$NPM_FAILED" ] && echo -e "${RED}  - NPM installation tests failed${NC}"
    exit 1
fi