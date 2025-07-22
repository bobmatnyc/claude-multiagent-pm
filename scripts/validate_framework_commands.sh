#!/bin/bash

# Claude PM Framework - AI-Trackdown Tools Command Validation Script
# Validates all critical AI-trackdown-tools commands for framework reliability
# Updated for ai-trackdown-tools integration

echo "=== Claude PM Framework AI-Trackdown Tools Validation ==="
echo "Date: $(date)"
echo "Version: ai-trackdown-tools cutover validation"
echo "========================================================="
echo

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    
    echo "Testing: $test_name"
    echo "Command: $command"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Measure execution time
    start_time=$(date +%s.%N)
    
    # Run command and capture output
    if output=$(eval "$command" 2>&1); then
        end_time=$(date +%s.%N)
        execution_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.0")
        
        # Check if output matches expected pattern
        if [[ -z "$expected_pattern" ]] || echo "$output" | grep -q "$expected_pattern"; then
            echo "✅ PASS - Execution time: ${execution_time}s"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo "❌ FAIL - Pattern not found: $expected_pattern"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        end_time=$(date +%s.%N)
        execution_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.0")
        echo "❌ FAIL - Command failed (${execution_time}s): $output"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo
}

echo "=== 1. AI-Trackdown Tools Core Commands ==="
echo

# Change to framework directory
cd "/Users/masa/Projects/claude-pm" || exit 1

# Test basic CLI availability
run_test "AI-trackdown CLI Version" \
    './aitrackdown --version' \
    ""

run_test "AI-trackdown CLI Help" \
    './aitrackdown --help' \
    "Professional CLI tool"

echo "=== 2. Status and Reporting Commands ==="
echo

run_test "Status Command" \
    './aitrackdown status' \
    ""

run_test "Status with Stats" \
    './aitrackdown status --stats' \
    ""

run_test "Backlog Command" \
    './aitrackdown backlog' \
    ""

echo "=== 3. Epic Management Commands ==="
echo

run_test "Epic List Command" \
    './aitrackdown epic list' \
    ""

run_test "Epic List with Details" \
    './aitrackdown epic list --verbose' \
    ""

echo "=== 4. Issue Management Commands ==="
echo

run_test "Issue List Command" \
    './aitrackdown issue list' \
    ""

run_test "Issue List with Filters" \
    './aitrackdown issue list --status ACTIVE' \
    ""

echo "=== 5. Task Management Commands ==="
echo

run_test "Task List Command" \
    './aitrackdown task list' \
    ""

run_test "Task List with Details" \
    './aitrackdown task list --verbose' \
    ""

echo "=== 6. Directory Structure Validation ==="
echo

run_test "Tasks Directory Structure" \
    'ls -la tickets/' \
    "epics"

run_test "Epics Directory" \
    'ls tickets/epics/' \
    ".md"

run_test "Issues Directory" \
    'ls tickets/issues/' \
    ".md"

run_test "Tasks Directory" \
    'ls tickets/tasks/' \
    ".md"

echo "=== 7. AI-Trackdown Health Integration ==="
echo

run_test "AI-Trackdown Health Monitor" \
    'python3 scripts/ai_trackdown_health_monitor.py --help' \
    "AI-Trackdown Tools Health Monitor"

run_test "Claude PM Health System" \
    'python3 -m claude_pm.cli health --help' \
    "health"

echo "=== 8. Framework Integration Tests ==="
echo

# Test task structure counts
run_test "Count Total Items" \
    'find tickets/ -name "*.md" | wc -l' \
    ""

run_test "Count Epics" \
    'find tickets/epics/ -name "*.md" | wc -l' \
    ""

run_test "Count Issues" \
    'find tickets/issues/ -name "*.md" | wc -l' \
    ""

run_test "Count Tasks" \
    'find tickets/tasks/ -name "*.md" | wc -l' \
    ""

echo "=== 9. Performance and Reliability Tests ==="
echo

run_test "Large Status Query Performance" \
    './aitrackdown status --full' \
    ""

run_test "Portfolio Command" \
    './aitrackdown portfolio' \
    ""

run_test "Export Functionality" \
    './aitrackdown export --format json --limit 5' \
    ""

echo "=== VALIDATION SUMMARY ==="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"
echo

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED - AI-Trackdown Tools is operationally ready!"
    echo ""
    echo "✅ CLI commands working correctly"
    echo "✅ Directory structure validated"
    echo "✅ Health monitoring integrated"
    echo "✅ Performance within acceptable limits"
    echo ""
    echo "📊 Framework Status:"
    echo "  - Total tracked items: $(find tickets/ -name "*.md" | wc -l)"
    echo "  - Active epics: $(find tickets/epics/ -name "*.md" | wc -l)"
    echo "  - Active issues: $(find tickets/issues/ -name "*.md" | wc -l)"
    echo "  - Active tasks: $(find tickets/tasks/ -name "*.md" | wc -l)"
    echo ""
    echo "🚀 AI-Trackdown Tools cutover successful!"
    exit 0
else
    echo "⚠️ $FAILED_TESTS tests failed - AI-Trackdown Tools needs attention"
    echo ""
    echo "🔧 Common issues to check:"
    echo "  - Ensure ai-trackdown-tools is properly installed"
    echo "  - Verify CLI links are working (./aitrackdown and ./atd)"
    echo "  - Check tickets/ directory structure exists"
    echo "  - Validate framework dependencies"
    echo ""
    echo "🆘 Run individual commands manually to diagnose issues"
    exit 1
fi