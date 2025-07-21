#!/bin/bash
# CI/CD Integration Script for Refactoring Validation
# 
# This script can be used in CI/CD pipelines to validate refactoring work
# before merging pull requests.

set -e  # Exit on any error

echo "======================================"
echo "🔍 Refactoring Validation CI/CD Check"
echo "======================================"

# Get the list of changed Python files
CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep "\.py$" || true)

if [ -z "$CHANGED_FILES" ]; then
    echo "✅ No Python files changed. Skipping validation."
    exit 0
fi

# Check if any of the changed files are in our refactoring target list
TARGET_FILES=(
    "claude_pm/services/parent_directory_manager.py"
    "claude_pm/core/agent_registry.py"
    "claude_pm/agents/orchestration/backwards_compatible_orchestrator.py"
    "claude_pm/core/agent_registry_sync.py"
    "claude_pm/services/health_monitor.py"
    "claude_pm/services/template_manager.py"
    "claude_pm/services/continuous_learning_engine.py"
    "claude_pm/services/unified_core_service.py"
    "claude_pm/agents/system_init_agent.py"
    "claude_pm/utils/ticket_parser.py"
    "claude_pm/agents/agent_loader.py"
    "claude_pm/__main__.py"
    "claude_pm/agents/base_agent_loader.py"
    "claude_pm/services/shared_prompt_cache.py"
    "claude_pm/services/project_config_repository.py"
    "claude_pm/utils/directory_utils.py"
)

VALIDATION_NEEDED=false
MODULES_TO_VALIDATE=""

for file in $CHANGED_FILES; do
    for target in "${TARGET_FILES[@]}"; do
        if [ "$file" = "$target" ]; then
            VALIDATION_NEEDED=true
            MODULES_TO_VALIDATE="$MODULES_TO_VALIDATE $file"
            break
        fi
    done
done

if [ "$VALIDATION_NEEDED" = false ]; then
    echo "✅ No refactoring target files changed. Skipping validation."
    exit 0
fi

echo ""
echo "🎯 Refactoring target files detected:"
echo "$MODULES_TO_VALIDATE"
echo ""

# Install test harness requirements
echo "📦 Installing test harness requirements..."
pip install -r tests/refactoring_harness/requirements.txt

# Run validation for each changed module
FAILED_MODULES=""
for module in $MODULES_TO_VALIDATE; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Validating: $module"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if python tests/refactoring_harness/validate_refactoring.py "$module"; then
        echo "✅ $module - PASSED"
    else
        echo "❌ $module - FAILED"
        FAILED_MODULES="$FAILED_MODULES $module"
    fi
done

# Summary
echo ""
echo "======================================"
echo "📊 Validation Summary"
echo "======================================"

if [ -z "$FAILED_MODULES" ]; then
    echo "✅ All refactored modules passed validation!"
    echo ""
    echo "Ready for code review and merge."
    exit 0
else
    echo "❌ Validation failed for modules:"
    echo "$FAILED_MODULES"
    echo ""
    echo "Please fix the issues and push again."
    echo "See detailed reports in tests/refactoring_harness/reports/"
    exit 1
fi