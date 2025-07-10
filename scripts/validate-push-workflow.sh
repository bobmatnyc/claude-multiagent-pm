#!/bin/bash

# Comprehensive Push Workflow Validation Script
# This script validates that the push workflow is properly configured

echo "🚀 Validating Comprehensive Push Workflow Configuration"
echo "======================================================"

# Check if we're in the correct directory
if [[ ! -f "CLAUDE.md" ]]; then
    echo "❌ Error: Must be run from claude-pm directory"
    exit 1
fi

# Validation results
VALIDATION_RESULTS=()

# Function to check file existence and content
check_file_content() {
    local file_path="$1"
    local search_pattern="$2"
    local description="$3"
    
    if [[ -f "$file_path" ]]; then
        if grep -q "$search_pattern" "$file_path"; then
            echo "✅ $description"
            VALIDATION_RESULTS+=("PASS: $description")
        else
            echo "❌ $description - Pattern not found"
            VALIDATION_RESULTS+=("FAIL: $description - Pattern not found")
        fi
    else
        echo "❌ $description - File not found: $file_path"
        VALIDATION_RESULTS+=("FAIL: $description - File not found")
    fi
}

# Function to check directory existence
check_directory() {
    local dir_path="$1"
    local description="$2"
    
    if [[ -d "$dir_path" ]]; then
        echo "✅ $description"
        VALIDATION_RESULTS+=("PASS: $description")
    else
        echo "❌ $description - Directory not found: $dir_path"
        VALIDATION_RESULTS+=("FAIL: $description - Directory not found")
    fi
}

echo ""
echo "🔍 Checking Ops Agent Configuration..."
echo "------------------------------------"

# Check ops agent push workflow
check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Comprehensive Push Operations" \
    "Ops agent has comprehensive push operations section"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Phase 1: Pre-Push Validation" \
    "Ops agent has pre-push validation phase"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Phase 2: Version Management" \
    "Ops agent has version management phase"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Phase 3: Documentation Updates" \
    "Ops agent has documentation update phase"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Phase 4: Git Operations" \
    "Ops agent has git operations phase"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Phase 5: Remote Deployment" \
    "Ops agent has remote deployment phase"

check_file_content \
    "framework/agent-roles/ops-agent.md" \
    "Push Error Handling & Rollback Procedures" \
    "Ops agent has error handling and rollback procedures"

echo ""
echo "🔍 Checking Orchestrator Configuration..."
echo "---------------------------------------"

# Check orchestrator push delegation
check_file_content \
    "CLAUDE.md" \
    "Push Operation Delegation" \
    "Orchestrator has push operation delegation"

check_file_content \
    "CLAUDE.md" \
    "Automatic Push Delegation" \
    "Orchestrator has automatic push delegation"

check_file_content \
    "CLAUDE.md" \
    "COMPREHENSIVE PUSH OPERATIONS" \
    "Orchestrator has comprehensive push operations section"

check_file_content \
    "CLAUDE.md" \
    "When user says \"push\"" \
    "Orchestrator recognizes push command"

echo ""
echo "🔍 Checking Documentation..."
echo "---------------------------"

# Check comprehensive push documentation
check_file_content \
    "docs/COMPREHENSIVE_PUSH_WORKFLOW.md" \
    "Comprehensive Push Operations Workflow" \
    "Comprehensive push workflow documentation exists"

check_file_content \
    "docs/COMPREHENSIVE_PUSH_WORKFLOW.md" \
    "Phase 1: Pre-Push Validation" \
    "Documentation has pre-push validation phase"

check_file_content \
    "docs/COMPREHENSIVE_PUSH_WORKFLOW.md" \
    "Error Handling" \
    "Documentation has error handling section"

check_file_content \
    "docs/COMPREHENSIVE_PUSH_WORKFLOW.md" \
    "Rollback Procedures" \
    "Documentation has rollback procedures"

echo ""
echo "🔍 Checking Project Structure..."
echo "------------------------------"

# Check key directories
check_directory \
    "framework/agent-roles" \
    "Agent roles directory exists"

check_directory \
    "docs" \
    "Documentation directory exists"

check_directory \
    "scripts" \
    "Scripts directory exists"

echo ""
echo "🔍 Checking Managed Projects..."
echo "-----------------------------"

# Check managed projects directory
check_directory \
    "/Users/masa/Projects/managed/ai-trackdown-tools" \
    "AI-Trackdown-Tools project exists"

check_directory \
    "/Users/masa/Projects/managed" \
    "Managed projects directory exists"

# Check for ai-trackdown-tools version scripts
if [[ -f "/Users/masa/Projects/managed/ai-trackdown-tools/package.json" ]]; then
    if grep -q "version:" "/Users/masa/Projects/managed/ai-trackdown-tools/package.json"; then
        echo "✅ AI-Trackdown-Tools has version scripts"
        VALIDATION_RESULTS+=("PASS: AI-Trackdown-Tools has version scripts")
    else
        echo "❌ AI-Trackdown-Tools missing version scripts"
        VALIDATION_RESULTS+=("FAIL: AI-Trackdown-Tools missing version scripts")
    fi
fi

echo ""
echo "📊 Validation Summary"
echo "==================="

# Count results
PASS_COUNT=$(printf '%s\n' "${VALIDATION_RESULTS[@]}" | grep -c "PASS:")
FAIL_COUNT=$(printf '%s\n' "${VALIDATION_RESULTS[@]}" | grep -c "FAIL:")
TOTAL_COUNT=$((PASS_COUNT + FAIL_COUNT))

echo "Total Checks: $TOTAL_COUNT"
echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo ""
    echo "🎉 All validations passed! Push workflow is properly configured."
    echo ""
    echo "✅ Ops agent has comprehensive push operations knowledge"
    echo "✅ Orchestrator will automatically delegate push operations"
    echo "✅ Documentation is complete and accessible"
    echo "✅ Error handling and rollback procedures are defined"
    echo ""
    echo "🚀 Push workflow is ready for use!"
    exit 0
else
    echo ""
    echo "❌ Some validations failed. Please review the following:"
    echo ""
    for result in "${VALIDATION_RESULTS[@]}"; do
        if [[ $result == FAIL:* ]]; then
            echo "  - ${result#FAIL: }"
        fi
    done
    echo ""
    echo "Please address the failures before using the push workflow."
    exit 1
fi