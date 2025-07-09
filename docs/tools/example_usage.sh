#!/bin/bash

# Example Usage Script for Documentation Validation Tools
# 
# This script demonstrates how to use the validation tools in different scenarios.
# It serves as both documentation and a practical example for implementation.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📖 Documentation Validation Tools - Example Usage${NC}"
echo "============================================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}📁 Working Directory: $BASE_DIR${NC}"
echo ""

# Example 1: Basic validation of current documentation
echo -e "${YELLOW}Example 1: Basic Documentation Validation${NC}"
echo "--------------------------------------------"
echo "Running comprehensive validation on documentation..."

python3 "$SCRIPT_DIR/comprehensive_doc_validator.py" "$BASE_DIR" \
    --output "$BASE_DIR/validation_example.json" \
    --verbose

echo -e "${GREEN}✅ Validation complete! Report saved to: validation_example.json${NC}"
echo ""

# Example 2: Drift detection with custom configuration
echo -e "${YELLOW}Example 2: Drift Detection${NC}"
echo "--------------------------------------------"
echo "Detecting documentation drift and outdated content..."

python3 "$SCRIPT_DIR/doc_drift_detector.py" "$BASE_DIR" \
    --output "$BASE_DIR/drift_example.json" \
    --max-age 21

echo -e "${GREEN}✅ Drift detection complete! Report saved to: drift_example.json${NC}"
echo ""

# Example 3: Quality assessment
echo -e "${YELLOW}Example 3: Quality Assessment${NC}"
echo "--------------------------------------------"
echo "Analyzing documentation quality and readability..."

python3 "$SCRIPT_DIR/doc_quality_checker.py" "$BASE_DIR" \
    --output "$BASE_DIR/quality_example.json" \
    --min-readability 45 \
    --max-sentence-length 22

echo -e "${GREEN}✅ Quality assessment complete! Report saved to: quality_example.json${NC}"
echo ""

# Example 4: Show report summaries
echo -e "${YELLOW}Example 4: Report Summaries${NC}"
echo "--------------------------------------------"

if [ -f "$BASE_DIR/validation_example.json" ]; then
    echo "📊 Validation Summary:"
    python3 -c "
import json
with open('$BASE_DIR/validation_example.json', 'r') as f:
    data = json.load(f)
    print(f'  Total checks: {data[\"summary\"][\"total\"]}')
    print(f'  Passed: {data[\"summary\"][\"passed\"]}')
    print(f'  Failed: {data[\"summary\"][\"failed\"]}')
    print(f'  Warnings: {data[\"summary\"][\"warnings\"]}')
"
fi

if [ -f "$BASE_DIR/drift_example.json" ]; then
    echo "🔄 Drift Summary:"
    python3 -c "
import json
with open('$BASE_DIR/drift_example.json', 'r') as f:
    data = json.load(f)
    print(f'  Total drift items: {data[\"summary\"][\"total_drift_items\"]}')
    print(f'  Critical: {data[\"summary\"][\"critical\"]}')
    print(f'  High: {data[\"summary\"][\"high\"]}')
    print(f'  Medium: {data[\"summary\"][\"medium\"]}')
    print(f'  Low: {data[\"summary\"][\"low\"]}')
"
fi

if [ -f "$BASE_DIR/quality_example.json" ]; then
    echo "📝 Quality Summary:"
    python3 -c "
import json
with open('$BASE_DIR/quality_example.json', 'r') as f:
    data = json.load(f)
    print(f'  Total issues: {data[\"summary\"][\"total_issues\"]}')
    print(f'  High severity: {data[\"summary\"][\"high_severity\"]}')
    print(f'  Medium severity: {data[\"summary\"][\"medium_severity\"]}')
    print(f'  Low severity: {data[\"summary\"][\"low_severity\"]}')
    if 'avg_readability' in data['summary']:
        print(f'  Average readability: {data[\"summary\"][\"avg_readability\"]:.1f}')
"
fi

echo ""

# Example 5: Integration with development workflow
echo -e "${YELLOW}Example 5: Development Workflow Integration${NC}"
echo "--------------------------------------------"
echo "Example of how to integrate validation into development workflow:"

cat << 'EOF'

# Pre-commit validation
git diff --name-only --cached | grep '\.md$' | while read file; do
    echo "Validating $file..."
    python3 tools/comprehensive_doc_validator.py "$file"
done

# CI/CD integration
if [ "$CI" = "true" ]; then
    echo "Running CI validation..."
    python3 tools/comprehensive_doc_validator.py . --output ci_validation.json
    
    # Fail build if critical issues found
    if [ $? -eq 1 ]; then
        echo "❌ Critical documentation issues found"
        exit 1
    fi
fi

# Scheduled maintenance
if [ "$(date +%u)" -eq 7 ]; then  # Sunday
    echo "Running weekly comprehensive validation..."
    python3 tools/comprehensive_doc_validator.py . --output weekly_validation.json
    python3 tools/doc_drift_detector.py . --output weekly_drift.json
    python3 tools/doc_quality_checker.py . --output weekly_quality.json
fi

EOF

echo ""

# Example 6: Custom validation scenarios
echo -e "${YELLOW}Example 6: Custom Validation Scenarios${NC}"
echo "--------------------------------------------"
echo "Custom validation examples:"

cat << 'EOF'

# Validate specific file types
find . -name "*.md" -path "*/user-guide/*" | while read file; do
    python3 tools/doc_quality_checker.py "$file"
done

# Focus on critical files only
CRITICAL_FILES=(
    "README.md"
    "QUICK_START.md"
    "DEPLOYMENT_GUIDE.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Validating critical file: $file"
        python3 tools/comprehensive_doc_validator.py "$file"
    fi
done

# Check for specific issues
echo "Checking for broken ticket references..."
python3 tools/comprehensive_doc_validator.py . | grep "Ticket reference not found"

echo "Checking for low readability..."
python3 tools/doc_quality_checker.py . | grep "Low readability"

EOF

echo ""

# Example 7: Report analysis
echo -e "${YELLOW}Example 7: Report Analysis${NC}"
echo "--------------------------------------------"
echo "Analyzing validation reports programmatically:"

cat << 'EOF'

# Extract high-priority issues
python3 -c "
import json
with open('validation_example.json', 'r') as f:
    data = json.load(f)
    
high_priority = [r for r in data['results'] if r['status'] == 'fail']
print(f'High priority issues: {len(high_priority)}')

for issue in high_priority[:5]:  # Show first 5
    print(f'  {issue[\"file\"]}:{issue[\"line_number\"]} - {issue[\"message\"]}')
"

# Track improvement over time
python3 -c "
import json
import glob
from datetime import datetime

reports = glob.glob('validation_*.json')
for report in sorted(reports):
    with open(report, 'r') as f:
        data = json.load(f)
        timestamp = data['timestamp']
        failed = data['summary']['failed']
        print(f'{timestamp}: {failed} failed checks')
"

EOF

echo ""

# Cleanup example files
echo -e "${YELLOW}Cleanup${NC}"
echo "--------------------------------------------"
echo "Cleaning up example report files..."

rm -f "$BASE_DIR/validation_example.json"
rm -f "$BASE_DIR/drift_example.json"
rm -f "$BASE_DIR/quality_example.json"

echo -e "${GREEN}✅ Example usage demonstration complete!${NC}"
echo ""
echo "💡 Next Steps:"
echo "1. Run setup script: ./setup_validation_tools.sh"
echo "2. Configure automated validation: ./setup_validation_tools.sh --setup-cron"
echo "3. Customize configurations in ../config/"
echo "4. Integrate with your development workflow"
echo ""
echo "📚 For more information, see the README.md file"