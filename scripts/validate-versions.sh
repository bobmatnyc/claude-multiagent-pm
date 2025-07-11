#!/bin/bash
# Version Validation Script for Claude PM Framework
# Validates that all version references are consistent for Homebrew packaging

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🔍 Claude PM Framework Version Validation${NC}"
echo "=============================================="

# Read the canonical version from VERSION file
VERSION_FILE="$PROJECT_ROOT/VERSION"
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}❌ VERSION file not found at: $VERSION_FILE${NC}"
    exit 1
fi

CANONICAL_VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r ')
echo -e "${BLUE}📍 Canonical Version (from VERSION file): ${GREEN}$CANONICAL_VERSION${NC}"
echo

# Track validation results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to validate version in file
validate_version() {
    local file="$1"
    local pattern="$2"
    local description="$3"
    local expected="$4"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [[ ! -f "$file" ]]; then
        echo -e "  ⚠️  File not found: $file"
        return
    fi
    
    local found_version=$(grep -o "$pattern" "$file" 2>/dev/null | head -1 | sed 's/.*"\([^"]*\)".*/\1/' 2>/dev/null || echo "")
    
    if [[ -z "$found_version" ]]; then
        echo -e "  ❌ $description: Pattern not found"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return
    fi
    
    if [[ "$found_version" == "$expected" ]]; then
        echo -e "  ✅ $description: $found_version"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "  ❌ $description: $found_version (expected: $expected)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Function to validate Python importable version
validate_python_import() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); import claude_pm; print(claude_pm.__version__)" 2>/dev/null || echo "IMPORT_ERROR")
        
        if [[ "$python_version" == "IMPORT_ERROR" ]]; then
            echo -e "  ❌ Python import: Import failed"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        elif [[ "$python_version" == "$CANONICAL_VERSION" ]]; then
            echo -e "  ✅ Python import: $python_version"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "  ❌ Python import: $python_version (expected: $CANONICAL_VERSION)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo -e "  ⚠️  Python import: python3 not available"
    fi
}

# Function to validate Node.js package version
validate_node_package() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if command -v node &> /dev/null && [[ -f "$PROJECT_ROOT/package.json" ]]; then
        local node_version=$(node -e "console.log(require('$PROJECT_ROOT/package.json').version)" 2>/dev/null || echo "READ_ERROR")
        
        if [[ "$node_version" == "READ_ERROR" ]]; then
            echo -e "  ❌ Node.js package: Read failed"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        elif [[ "$node_version" == "$CANONICAL_VERSION" ]]; then
            echo -e "  ✅ Node.js package: $node_version"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "  ❌ Node.js package: $node_version (expected: $CANONICAL_VERSION)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo -e "  ⚠️  Node.js package: node not available or package.json missing"
    fi
}

echo -e "${YELLOW}🎯 Core Package Files:${NC}"
validate_version "$PROJECT_ROOT/package.json" '"version":[[:space:]]*"[^"]*"' "package.json" "$CANONICAL_VERSION"
validate_version "$PROJECT_ROOT/pyproject.toml" 'version[[:space:]]*=[[:space:]]*"[^"]*"' "pyproject.toml" "$CANONICAL_VERSION"
validate_version "$PROJECT_ROOT/claude_pm/__init__.py" '__version__[[:space:]]*=[[:space:]]*"[^"]*"' "claude_pm/__init__.py" "$CANONICAL_VERSION"

echo
echo -e "${YELLOW}🔧 QA Service Files:${NC}"
validate_version "$PROJECT_ROOT/cmpm-qa/service/qa_service.py" 'framework_version[[:space:]]*=[[:space:]]*"[^"]*"' "QA service" "$CANONICAL_VERSION"
validate_version "$PROJECT_ROOT/cmpm-qa/extension/manifest.json" '"framework_version":[[:space:]]*"[^"]*"' "QA extension" "$CANONICAL_VERSION"
validate_version "$PROJECT_ROOT/cmpm-qa/native-host/native_host.py" '"framework_version":[[:space:]]*"[^"]*"' "QA native host" "$CANONICAL_VERSION"

echo
echo -e "${YELLOW}📖 Documentation Files:${NC}"
validate_version "$PROJECT_ROOT/install/README.md" '"version":[[:space:]]*"[^"]*"' "install/README.md" "$CANONICAL_VERSION"

echo
echo -e "${YELLOW}🚀 Runtime Validation:${NC}"
validate_python_import
validate_node_package

echo
echo -e "${BLUE}📊 Validation Summary:${NC}"
echo "================================"
echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

# Calculate success percentage
if [[ $TOTAL_CHECKS -gt 0 ]]; then
    SUCCESS_RATE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    echo -e "Success Rate: ${GREEN}$SUCCESS_RATE%${NC}"
else
    echo -e "Success Rate: ${YELLOW}N/A${NC}"
fi

echo
if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo -e "${GREEN}✅ All version validations passed!${NC}"
    echo -e "${GREEN}🍺 Project is ready for Homebrew packaging${NC}"
    exit 0
else
    echo -e "${RED}❌ Version validation failed!${NC}"
    echo -e "${YELLOW}💡 Run './scripts/sync-versions.sh' to fix version inconsistencies${NC}"
    exit 1
fi