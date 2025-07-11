#!/bin/bash
# Version Synchronization Script for Claude PM Framework
# Ensures all package files are synchronized with the VERSION file

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

echo -e "${BLUE}🔄 Claude PM Framework Version Synchronization${NC}"
echo "=================================================="

# Check if VERSION file exists
VERSION_FILE="$PROJECT_ROOT/VERSION"
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}❌ VERSION file not found at: $VERSION_FILE${NC}"
    exit 1
fi

# Read the target version
TARGET_VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r ')
echo -e "${BLUE}📍 Target Version: ${GREEN}$TARGET_VERSION${NC}"
echo

# Function to update version in a file using sed
update_version() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    local description="$4"
    
    if [[ -f "$file" ]]; then
        if grep -q "$pattern" "$file"; then
            sed -i.bak "$replacement" "$file"
            rm -f "${file}.bak"
            echo -e "  ✅ $description"
        else
            echo -e "  ⚠️  Pattern not found in $description"
        fi
    else
        echo -e "  ⚠️  File not found: $file"
    fi
}

# Update package.json
echo -e "${YELLOW}📦 Updating Node.js package files...${NC}"
update_version "$PROJECT_ROOT/package.json" \
    '"version":[[:space:]]*"[^"]*"' \
    's/"version":[[:space:]]*"[^"]*"/"version": "'$TARGET_VERSION'"/g' \
    "package.json version"

# Update pyproject.toml
echo -e "${YELLOW}🐍 Updating Python package files...${NC}"
update_version "$PROJECT_ROOT/pyproject.toml" \
    'version[[:space:]]*=[[:space:]]*"[^"]*"' \
    's/version[[:space:]]*=[[:space:]]*"[^"]*"/version = "'$TARGET_VERSION'"/g' \
    "pyproject.toml version"

update_version "$PROJECT_ROOT/pyproject.toml" \
    'fallback_version[[:space:]]*=[[:space:]]*"[^"]*"' \
    's/fallback_version[[:space:]]*=[[:space:]]*"[^"]*"/fallback_version = "'$TARGET_VERSION'"/g' \
    "pyproject.toml fallback_version"

# Update Python __init__.py
update_version "$PROJECT_ROOT/claude_pm/__init__.py" \
    '__version__[[:space:]]*=[[:space:]]*"[^"]*"' \
    's/__version__[[:space:]]*=[[:space:]]*"[^"]*"/__version__ = "'$TARGET_VERSION'"/g' \
    "claude_pm/__init__.py __version__"

# Update QA service files
echo -e "${YELLOW}🔧 Updating QA service files...${NC}"
update_version "$PROJECT_ROOT/cmpm-qa/service/qa_service.py" \
    'self\.framework_version[[:space:]]*=[[:space:]]*"[^"]*"' \
    's/self\.framework_version[[:space:]]*=[[:space:]]*"[^"]*"/self.framework_version = "'$TARGET_VERSION'"/g' \
    "QA service framework_version"

update_version "$PROJECT_ROOT/cmpm-qa/extension/manifest.json" \
    '"framework_version":[[:space:]]*"[^"]*"' \
    's/"framework_version":[[:space:]]*"[^"]*"/"framework_version": "'$TARGET_VERSION'"/g' \
    "QA extension manifest framework_version"

update_version "$PROJECT_ROOT/cmpm-qa/native-host/native_host.py" \
    '"framework_version":[[:space:]]*"[^"]*"' \
    's/"framework_version":[[:space:]]*"[^"]*"/"framework_version": "'$TARGET_VERSION'"/g' \
    "QA native host framework_version"

# Update README.md version references
echo -e "${YELLOW}📖 Updating documentation...${NC}"
update_version "$PROJECT_ROOT/README.md" \
    'Framework v[0-9]*\.[0-9]*\.[0-9]*' \
    's/Framework v[0-9]*\.[0-9]*\.[0-9]*/Framework v'$TARGET_VERSION'/g' \
    "README.md framework version references"

update_version "$PROJECT_ROOT/README.md" \
    'Version-[0-9]*\.[0-9]*\.[0-9]*-blue' \
    's/Version-[0-9]*\.[0-9]*\.[0-9]*-blue/Version-'$TARGET_VERSION'-blue/g' \
    "README.md version badge"

update_version "$PROJECT_ROOT/install/README.md" \
    '"version":[[:space:]]*"[^"]*"' \
    's/"version":[[:space:]]*"[^"]*"/"version": "'$TARGET_VERSION'"/g' \
    "install/README.md version"

echo
echo -e "${BLUE}🔍 Verification...${NC}"

# Verify versions are synchronized
echo -e "${YELLOW}Checking version consistency:${NC}"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); import claude_pm; print(claude_pm.__version__)" 2>/dev/null || echo "N/A")
    if [[ "$PYTHON_VERSION" == "$TARGET_VERSION" ]]; then
        echo -e "  ✅ Python package: $PYTHON_VERSION"
    else
        echo -e "  ❌ Python package: $PYTHON_VERSION (expected: $TARGET_VERSION)"
    fi
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -e "console.log(require('$PROJECT_ROOT/package.json').version)" 2>/dev/null || echo "N/A")
    if [[ "$NODE_VERSION" == "$TARGET_VERSION" ]]; then
        echo -e "  ✅ Node.js package: $NODE_VERSION"
    else
        echo -e "  ❌ Node.js package: $NODE_VERSION (expected: $TARGET_VERSION)"
    fi
fi

# Check VERSION file
FILE_VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r ')
if [[ "$FILE_VERSION" == "$TARGET_VERSION" ]]; then
    echo -e "  ✅ VERSION file: $FILE_VERSION"
else
    echo -e "  ❌ VERSION file: $FILE_VERSION (expected: $TARGET_VERSION)"
fi

echo
echo -e "${GREEN}✅ Version synchronization complete!${NC}"
echo -e "${BLUE}📋 Next steps for release:${NC}"
echo "1. Review changes: git diff"
echo "2. Test the build: make test"
echo "3. Commit changes: git add . && git commit -m 'chore: sync versions to $TARGET_VERSION'"
echo "4. Create release tag: git tag -a v$TARGET_VERSION -m 'Release version $TARGET_VERSION'"
echo "5. Push: git push && git push --tags"

# Generate package-lock.json if needed
if [[ -f "$PROJECT_ROOT/package.json" ]] && command -v npm &> /dev/null; then
    echo -e "${YELLOW}📦 Updating package-lock.json...${NC}"
    cd "$PROJECT_ROOT"
    npm install --package-lock-only
    echo -e "  ✅ package-lock.json updated"
fi

echo -e "${GREEN}🎉 All version files synchronized to: $TARGET_VERSION${NC}"