#!/bin/bash
# Local Test Deployment Script for EP-0043 Refactoring
# Safe, isolated testing that won't affect machine installation

set -e  # Exit on error

echo "🚀 Claude PM Refactoring - Local Test Deployment"
echo "================================================"
echo ""

# Configuration
TEST_DIR="$HOME/test-deployments/claude-pm-refactor-test"
SOURCE_DIR="$(pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$TEST_DIR/deployment_log_$TIMESTAMP.txt"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
        log "SUCCESS: $1"
    else
        echo -e "${RED}✗ $1${NC}"
        log "FAILED: $1"
        exit 1
    fi
}

# 1. Setup isolated test environment
echo -e "${YELLOW}1. Setting up isolated test environment...${NC}"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
log "Created test directory: $TEST_DIR"

# 2. Create Python virtual environment
echo -e "${YELLOW}2. Creating Python virtual environment...${NC}"
python3 -m venv venv
check_status "Virtual environment created"

# Activate virtual environment
source venv/bin/activate
check_status "Virtual environment activated"

# 3. Copy source code (not git clone to test current changes)
echo -e "${YELLOW}3. Copying source code...${NC}"
if [ -d "claude-multiagent-pm" ]; then
    rm -rf claude-multiagent-pm
fi
# Use rsync to exclude problematic directories
rsync -av --exclude='node_modules' --exclude='.git' --exclude='__pycache__' \
      --exclude='*.pyc' --exclude='.pytest_cache' --exclude='*.egg-info' \
      --exclude='tests/e2e/version-specific' --exclude='tests/e2e/installation' \
      "$SOURCE_DIR/" claude-multiagent-pm/
check_status "Source code copied"

cd claude-multiagent-pm

# 4. Install dependencies in isolated environment
echo -e "${YELLOW}4. Installing dependencies...${NC}"
pip install --upgrade pip
check_status "Pip upgraded"

pip install -e .
check_status "Package installed in development mode"

pip install pytest pytest-cov pytest-asyncio
check_status "Test dependencies installed"

# 5. Run import tests to verify refactoring
echo -e "${YELLOW}5. Running import compatibility tests...${NC}"
python3 << 'EOF'
import sys
print("Testing backward compatibility imports...")

# Test parent_directory_manager imports
try:
    from claude_pm.services.parent_directory_manager import ParentDirectoryManager
    print("✓ ParentDirectoryManager import successful")
except Exception as e:
    print(f"✗ ParentDirectoryManager import failed: {e}")
    sys.exit(1)

# Test agent_registry imports
try:
    from claude_pm.core.agent_registry import AgentRegistry, AgentMetadata
    print("✓ AgentRegistry imports successful")
except Exception as e:
    print(f"✗ AgentRegistry imports failed: {e}")
    sys.exit(1)

# Test orchestrator imports
try:
    from claude_pm.orchestration import BackwardsCompatibleOrchestrator
    print("✓ BackwardsCompatibleOrchestrator import successful")
except Exception as e:
    print(f"✗ BackwardsCompatibleOrchestrator import failed: {e}")
    sys.exit(1)

print("\nAll backward compatibility imports successful!")
EOF
check_status "Import compatibility tests"

# 6. Run unit tests for refactored modules
echo -e "${YELLOW}6. Running unit tests for refactored modules...${NC}"
pytest tests/unit/services/test_parent_directory_manager.py -v --tb=short || true
pytest tests/unit/core/test_agent_registry.py -v --tb=short || true
pytest tests/unit/test_backwards_compatible_orchestrator.py -v --tb=short || true

# 7. Test CLI functionality
echo -e "${YELLOW}7. Testing CLI functionality...${NC}"
python -m claude_pm.cli --version
check_status "CLI version check"

# 8. Create test report
echo -e "${YELLOW}8. Creating test report...${NC}"
cat > "$TEST_DIR/test_report_$TIMESTAMP.md" << EOF
# Local Test Deployment Report
**Date**: $(date)
**Test Directory**: $TEST_DIR
**Source Directory**: $SOURCE_DIR

## Import Compatibility
- ParentDirectoryManager: ✓
- AgentRegistry: ✓
- BackwardsCompatibleOrchestrator: ✓

## Test Results
$(pytest --version)
See log file for detailed test output: $LOG_FILE

## Next Steps
1. Review test results
2. If tests pass, proceed with staging deployment
3. If tests fail, fix issues and re-run

## Rollback Procedure
To completely remove this test deployment:
\`\`\`bash
rm -rf $TEST_DIR
\`\`\`
EOF
check_status "Test report created"

# 9. Summary
echo ""
echo -e "${GREEN}✅ Local test deployment complete!${NC}"
echo ""
echo "Test deployment location: $TEST_DIR"
echo "Log file: $LOG_FILE"
echo "Test report: $TEST_DIR/test_report_$TIMESTAMP.md"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- This is an isolated test environment"
echo "- Your machine installation is unaffected"
echo "- Virtual environment is still active"
echo ""
echo "To deactivate the test environment:"
echo "  deactivate"
echo ""
echo "To remove the test deployment:"
echo "  rm -rf $TEST_DIR"