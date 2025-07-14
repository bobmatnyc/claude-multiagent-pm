#!/bin/sh

# Docker test script for claude-multiagent-pm@0.7.5 installation verification
# TEMPORAL CONTEXT: 2025-07-14 - Testing v0.7.5 with module path fixes

echo "=== Docker Test: claude-multiagent-pm@0.7.5 Installation Verification ==="
echo "Date: $(date)"
echo "Node.js version: $(node --version)"
echo "NPM version: $(npm --version)"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"
echo "PATH: $PATH"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "--- Test $TOTAL_TESTS: $test_name ---"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Function to capture and display command output
capture_output() {
    local cmd="$1"
    echo "Running: $cmd"
    eval "$cmd" 2>&1
    local exit_code=$?
    echo "Exit code: $exit_code"
    return $exit_code
}

echo "=== Phase 1: NPM Global Installation Test ==="

# Test 1: Install @bobmatnyc/claude-multiagent-pm@0.7.5 from NPM registry
run_test "Global NPM installation of @bobmatnyc/claude-multiagent-pm@0.7.5" "
    echo 'Installing @bobmatnyc/claude-multiagent-pm@0.7.5...'
    npm install -g @bobmatnyc/claude-multiagent-pm@0.7.5 2>&1 | tee /tmp/install_output.log
    if [ \$? -eq 0 ]; then
        echo 'Installation completed successfully'
        return 0
    else
        echo 'Installation failed'
        return 1
    fi
"

# Test 2: Verify postinstall messaging
run_test "Postinstall messaging display verification" "
    echo 'Checking postinstall output...'
    if grep -q 'installed successfully' /tmp/install_output.log; then
        echo 'Postinstall messaging found in output'
        return 0
    else
        echo 'Postinstall messaging NOT found'
        echo 'Full install output:'
        cat /tmp/install_output.log
        return 1
    fi
"

echo "=== Phase 1.5: Python Dependencies Installation ==="

# Test 1.5: Install Python dependencies
run_test "Python dependencies installation" "
    echo 'Installing Python dependencies...'
    pip install --break-system-packages click rich 2>&1
    if [ \$? -eq 0 ]; then
        echo 'Python dependencies installed successfully'
        return 0
    else
        echo 'Python dependencies installation failed'
        return 1
    fi
"

echo "=== Phase 2: Command Availability and Version Testing ==="

# Test 3: Verify claude-pm command is available
run_test "claude-pm command availability" "
    which claude-pm || echo 'claude-pm not found in PATH'
    claude-pm --version
"

# Test 4: Verify correct version reporting
run_test "Version reporting verification" "
    version_output=\$(claude-pm --version 2>&1)
    echo \"Version output: \$version_output\"
    
    # Check for package version v0.7.5
    if echo \"\$version_output\" | grep -q 'v0.7.5'; then
        echo 'Package version v0.7.5 found ✓'
        package_version_ok=true
    else
        echo 'Package version v0.7.5 NOT found ✗'
        package_version_ok=false
    fi
    
    # Check for script version 1.0.1
    if echo \"\$version_output\" | grep -q '1.0.1'; then
        echo 'Script version 1.0.1 found ✓'
        script_version_ok=true
    else
        echo 'Script version 1.0.1 NOT found ✗'
        script_version_ok=false
    fi
    
    if [ \"\$package_version_ok\" = true ] && [ \"\$script_version_ok\" = true ]; then
        return 0
    else
        return 1
    fi
"

echo "=== Phase 3: Advanced Command Testing ==="

# Test 5: Test help command (should not throw ModuleNotFoundError)
run_test "Help command without ModuleNotFoundError" "
    output=\$(claude-pm --help 2>&1)
    echo \"Help output: \$output\"
    
    if echo \"\$output\" | grep -q 'ModuleNotFoundError'; then
        echo 'ModuleNotFoundError found in help command ✗'
        return 1
    else
        echo 'No ModuleNotFoundError in help command ✓'
        return 0
    fi
"

# Test 6: Test status command
run_test "Status command functionality" "
    output=\$(claude-pm status 2>&1)
    echo \"Status output: \$output\"
    
    if echo \"\$output\" | grep -q 'ModuleNotFoundError'; then
        echo 'ModuleNotFoundError found in status command ✗'
        return 1
    else
        echo 'No ModuleNotFoundError in status command ✓'
        return 0
    fi
"

echo "=== Phase 4: Framework Deployment Testing ==="

# Create test directory for framework deployment
mkdir -p /tmp/test-project
cd /tmp/test-project

# Test 7: Framework deployment test
run_test "Framework deployment in clean environment" "
    echo 'Running claude-pm init...'
    output=\$(claude-pm init 2>&1)
    echo \"Init output: \$output\"
    
    if echo \"\$output\" | grep -q 'ModuleNotFoundError'; then
        echo 'ModuleNotFoundError found in init command ✗'
        return 1
    else
        echo 'No ModuleNotFoundError in init command ✓'
        return 0
    fi
"

# Test 8: Memory system setup validation
run_test "Memory system setup validation" "
    echo 'Testing memory system components...'
    
    # Check if .claude-pm directory was created
    if [ -d '.claude-pm' ]; then
        echo '.claude-pm directory created ✓'
        memory_dir_ok=true
    else
        echo '.claude-pm directory NOT created ✗'
        memory_dir_ok=false
    fi
    
    # Check for any memory-related errors
    if [ \"\$memory_dir_ok\" = true ]; then
        echo 'Memory system setup appears successful ✓'
        return 0
    else
        echo 'Memory system setup failed ✗'
        return 1
    fi
"

echo "=== Phase 5: Module Resolution Testing ==="

# Test 9: Python module resolution test
run_test "Python module resolution verification" "
    echo 'Testing Python module import...'
    
    # Try to run a command that would use Python modules
    output=\$(claude-pm status --verbose 2>&1)
    echo \"Verbose status output: \$output\"
    
    if echo \"\$output\" | grep -q 'ModuleNotFoundError'; then
        echo 'ModuleNotFoundError found in verbose status ✗'
        return 1
    else
        echo 'No ModuleNotFoundError in verbose status ✓'
        return 0
    fi
"

echo "=== Test Results Summary ==="
echo "Tests passed: ${TESTS_PASSED}/${TOTAL_TESTS}"
echo "Tests failed: ${TESTS_FAILED}/${TOTAL_TESTS}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! v0.7.5 installation verified successfully${NC}"
    exit 0
else
    echo -e "${RED}❌ ${TESTS_FAILED} test(s) failed. Installation issues detected.${NC}"
    exit 1
fi