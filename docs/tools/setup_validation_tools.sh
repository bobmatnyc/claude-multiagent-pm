#!/bin/bash

# Setup Script for Documentation Validation Tools
# 
# This script sets up the validation environment, installs dependencies,
# and configures automated validation scheduling for documentation tools.
#
# Usage: ./setup_validation_tools.sh [options]
#
# Options:
#   --install-deps     Install required dependencies
#   --setup-cron       Set up automated validation scheduling
#   --create-reports   Create validation report directories
#   --help            Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$SCRIPT_DIR"

# Configuration
PYTHON_VERSION="3.8"
REPORTS_DIR="$BASE_DIR/validation-reports"
CONFIG_DIR="$BASE_DIR/config"
CRON_SCHEDULE="0 2 * * *"  # Daily at 2 AM

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Documentation Validation Tools Setup

This script sets up the validation environment for documentation tools.

Usage: $0 [OPTIONS]

Options:
    --install-deps     Install required Python dependencies
    --setup-cron       Set up automated validation scheduling
    --create-reports   Create validation report directories
    --config-only      Only create configuration files
    --test-tools       Test all validation tools
    --help            Show this help message

Examples:
    $0 --install-deps --create-reports
    $0 --setup-cron
    $0 --test-tools

EOF
}

check_python() {
    log_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VER="3.8"
    
    if [ "$(printf '%s\n' "$REQUIRED_VER" "$PYTHON_VER" | sort -V | head -n1)" != "$REQUIRED_VER" ]; then
        log_error "Python $REQUIRED_VER or higher is required. Found: $PYTHON_VER"
        exit 1
    fi
    
    log_success "Python $PYTHON_VER is compatible"
}

check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check for required system commands
    local deps=("git" "node" "bash")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_warning "Optional dependencies missing: ${missing[*]}"
        log_info "Some validation features may be limited"
    else
        log_success "All system dependencies available"
    fi
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Create requirements.txt for validation tools
    cat > "$TOOLS_DIR/requirements.txt" << EOF
# Documentation Validation Tools Dependencies
# Standard library modules are used primarily, but these may be useful

# Optional: Enhanced spell checking
# pyspellchecker>=0.7.0

# Optional: Advanced text analysis
# textstat>=0.7.0

# Optional: YAML parsing (usually included in Python)
# PyYAML>=6.0

# Optional: Enhanced HTTP requests
# requests>=2.25.0

# Optional: JSON schema validation
# jsonschema>=4.0.0

# Optional: Configuration management
# python-dotenv>=0.19.0

# Optional: Enhanced logging
# colorlog>=6.0.0
EOF
    
    # Install basic dependencies if pip is available
    if command -v pip3 &> /dev/null; then
        log_info "Installing optional dependencies..."
        
        # Install only if not already present
        python3 -c "import yaml" 2>/dev/null || pip3 install PyYAML --user --quiet
        
        log_success "Python dependencies installed"
    else
        log_warning "pip3 not available, skipping optional dependencies"
    fi
}

create_report_directories() {
    log_info "Creating validation report directories..."
    
    # Create main reports directory
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$REPORTS_DIR/validation"
    mkdir -p "$REPORTS_DIR/drift"
    mkdir -p "$REPORTS_DIR/quality"
    mkdir -p "$REPORTS_DIR/archive"
    
    # Create subdirectories for different report types
    mkdir -p "$REPORTS_DIR/validation/daily"
    mkdir -p "$REPORTS_DIR/validation/weekly"
    mkdir -p "$REPORTS_DIR/drift/daily"
    mkdir -p "$REPORTS_DIR/drift/weekly"
    mkdir -p "$REPORTS_DIR/quality/daily"
    mkdir -p "$REPORTS_DIR/quality/weekly"
    
    # Create .gitignore for reports
    cat > "$REPORTS_DIR/.gitignore" << EOF
# Validation reports are generated automatically
*.json
*.html
*.txt
*.log

# Keep directory structure
!.gitignore
!README.md
EOF
    
    # Create README for reports directory
    cat > "$REPORTS_DIR/README.md" << EOF
# Documentation Validation Reports

This directory contains automated validation reports for the documentation.

## Directory Structure

- \`validation/\` - Comprehensive validation reports
- \`drift/\` - Documentation drift detection reports
- \`quality/\` - Quality assessment reports
- \`archive/\` - Archived historical reports

## Report Types

### Daily Reports
- Generated automatically each day
- Focus on immediate issues and changes
- Located in \`*/daily/\` subdirectories

### Weekly Reports
- Comprehensive analysis with trends
- Generated every Sunday
- Located in \`*/weekly/\` subdirectories

## Usage

Reports are generated automatically by the validation tools:

\`\`\`bash
# Run individual validation
python3 ../tools/comprehensive_doc_validator.py . --output validation/manual-$(date +%Y%m%d).json

# Run drift detection
python3 ../tools/doc_drift_detector.py . --output drift/manual-$(date +%Y%m%d).json

# Run quality check
python3 ../tools/doc_quality_checker.py . --output quality/manual-$(date +%Y%m%d).json
\`\`\`
EOF
    
    log_success "Report directories created in $REPORTS_DIR"
}

create_config_files() {
    log_info "Creating configuration files..."
    
    mkdir -p "$CONFIG_DIR"
    
    # Create drift detection configuration
    cat > "$CONFIG_DIR/drift_config.json" << EOF
{
    "max_age_days": 30,
    "critical_files": [
        "README.md",
        "QUICK_START.md",
        "DEPLOYMENT_GUIDE.md",
        "TICKETING_SYSTEM.md",
        "FRAMEWORK_OVERVIEW.md"
    ],
    "api_patterns": [
        "aitrackdown\\\\s+\\\\w+",
        "atd\\\\s+\\\\w+",
        "mem0\\\\.\\\\w+",
        "claude\\\\.\\\\w+"
    ],
    "config_files": [
        "package.json",
        "requirements.txt",
        "*.yml",
        "*.yaml",
        "*.json"
    ],
    "ignore_patterns": [
        "archive/",
        "node_modules/",
        ".git/",
        "*.tmp",
        "*.log",
        "validation-reports/"
    ]
}
EOF
    
    # Create validation configuration
    cat > "$CONFIG_DIR/validation_config.json" << EOF
{
    "external_link_timeout": 10,
    "max_retries": 3,
    "ignore_domains": [
        "localhost",
        "127.0.0.1",
        "example.com"
    ],
    "skip_file_patterns": [
        "archive/",
        "node_modules/",
        ".git/",
        "validation-reports/"
    ],
    "required_sections": [
        "## Description",
        "## Usage",
        "## Installation"
    ]
}
EOF
    
    # Create quality checking configuration
    cat > "$CONFIG_DIR/quality_config.json" << EOF
{
    "readability": {
        "min_score": 40,
        "target_score": 60
    },
    "sentence_length": {
        "max_words": 25,
        "ideal_words": 20
    },
    "paragraph_length": {
        "max_sentences": 8,
        "ideal_sentences": 4
    },
    "technical_terms": [
        "aitrackdown",
        "mem0",
        "claude",
        "multiagent",
        "orchestrator"
    ],
    "style_rules": {
        "avoid_passive_voice": true,
        "check_spelling": true,
        "check_grammar": true,
        "check_consistency": true
    }
}
EOF
    
    log_success "Configuration files created in $CONFIG_DIR"
}

create_wrapper_scripts() {
    log_info "Creating wrapper scripts..."
    
    # Create comprehensive validation script
    cat > "$TOOLS_DIR/validate_all.sh" << 'EOF'
#!/bin/bash

# Comprehensive Documentation Validation Script
# Runs all validation tools and generates consolidated report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$BASE_DIR/validation-reports"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PREFIX="validation_$TIMESTAMP"

echo "🔍 Starting comprehensive documentation validation..."
echo "📁 Base directory: $BASE_DIR"
echo "📊 Reports will be saved to: $REPORTS_DIR"

# Run comprehensive validation
echo "1️⃣ Running comprehensive document validation..."
python3 "$SCRIPT_DIR/comprehensive_doc_validator.py" "$BASE_DIR" \
    --output "$REPORTS_DIR/validation/${REPORT_PREFIX}_comprehensive.json"

# Run drift detection
echo "2️⃣ Running drift detection..."
python3 "$SCRIPT_DIR/doc_drift_detector.py" "$BASE_DIR" \
    --config "$BASE_DIR/config/drift_config.json" \
    --output "$REPORTS_DIR/drift/${REPORT_PREFIX}_drift.json"

# Run quality check
echo "3️⃣ Running quality check..."
python3 "$SCRIPT_DIR/doc_quality_checker.py" "$BASE_DIR" \
    --output "$REPORTS_DIR/quality/${REPORT_PREFIX}_quality.json"

echo "✅ Validation complete! Reports saved with prefix: $REPORT_PREFIX"
echo "📊 Check $REPORTS_DIR for detailed results"
EOF
    
    chmod +x "$TOOLS_DIR/validate_all.sh"
    
    # Create daily validation script
    cat > "$TOOLS_DIR/daily_validation.sh" << 'EOF'
#!/bin/bash

# Daily Documentation Validation Script
# Lightweight validation for daily monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$BASE_DIR/validation-reports"

DATE=$(date +%Y%m%d)
REPORT_PREFIX="daily_$DATE"

echo "📅 Running daily documentation validation for $DATE..."

# Run quick validation (skip external links for speed)
python3 "$SCRIPT_DIR/comprehensive_doc_validator.py" "$BASE_DIR" \
    --output "$REPORTS_DIR/validation/daily/${REPORT_PREFIX}_validation.json"

# Run drift detection
python3 "$SCRIPT_DIR/doc_drift_detector.py" "$BASE_DIR" \
    --config "$BASE_DIR/config/drift_config.json" \
    --output "$REPORTS_DIR/drift/daily/${REPORT_PREFIX}_drift.json"

echo "✅ Daily validation complete!"
EOF
    
    chmod +x "$TOOLS_DIR/daily_validation.sh"
    
    log_success "Wrapper scripts created"
}

setup_cron_jobs() {
    log_info "Setting up automated validation scheduling..."
    
    # Create cron job for daily validation
    CRON_JOB="$CRON_SCHEDULE $TOOLS_DIR/daily_validation.sh >> $REPORTS_DIR/cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$TOOLS_DIR/daily_validation.sh"; then
        log_warning "Cron job already exists for daily validation"
    else
        # Add cron job
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        log_success "Daily validation cron job added"
    fi
    
    # Create weekly validation cron job (Sundays at 3 AM)
    WEEKLY_CRON="0 3 * * 0 $TOOLS_DIR/validate_all.sh >> $REPORTS_DIR/weekly_cron.log 2>&1"
    
    if crontab -l 2>/dev/null | grep -q "$TOOLS_DIR/validate_all.sh"; then
        log_warning "Cron job already exists for weekly validation"
    else
        (crontab -l 2>/dev/null; echo "$WEEKLY_CRON") | crontab -
        log_success "Weekly validation cron job added"
    fi
    
    log_info "Cron jobs configured:"
    log_info "  Daily: $CRON_SCHEDULE"
    log_info "  Weekly: Sundays at 3 AM"
}

test_validation_tools() {
    log_info "Testing validation tools..."
    
    # Test comprehensive validator
    echo "Testing comprehensive document validator..."
    if python3 "$TOOLS_DIR/comprehensive_doc_validator.py" "$BASE_DIR" --output /tmp/test_validation.json; then
        log_success "Comprehensive validator test passed"
        rm -f /tmp/test_validation.json
    else
        log_error "Comprehensive validator test failed"
        return 1
    fi
    
    # Test drift detector
    echo "Testing drift detector..."
    if python3 "$TOOLS_DIR/doc_drift_detector.py" "$BASE_DIR" --output /tmp/test_drift.json; then
        log_success "Drift detector test passed"
        rm -f /tmp/test_drift.json
    else
        log_error "Drift detector test failed"
        return 1
    fi
    
    # Test quality checker
    echo "Testing quality checker..."
    if python3 "$TOOLS_DIR/doc_quality_checker.py" "$BASE_DIR" --output /tmp/test_quality.json; then
        log_success "Quality checker test passed"
        rm -f /tmp/test_quality.json
    else
        log_error "Quality checker test failed"
        return 1
    fi
    
    log_success "All validation tools passed testing"
}

# Main execution
main() {
    echo "🚀 Documentation Validation Tools Setup"
    echo "=========================================="
    
    # Parse command line arguments
    INSTALL_DEPS=false
    SETUP_CRON=false
    CREATE_REPORTS=false
    CONFIG_ONLY=false
    TEST_TOOLS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-deps)
                INSTALL_DEPS=true
                shift
                ;;
            --setup-cron)
                SETUP_CRON=true
                shift
                ;;
            --create-reports)
                CREATE_REPORTS=true
                shift
                ;;
            --config-only)
                CONFIG_ONLY=true
                shift
                ;;
            --test-tools)
                TEST_TOOLS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no options provided, run basic setup
    if [ "$INSTALL_DEPS" = false ] && [ "$SETUP_CRON" = false ] && [ "$CREATE_REPORTS" = false ] && [ "$CONFIG_ONLY" = false ] && [ "$TEST_TOOLS" = false ]; then
        log_info "Running basic setup (use --help for options)"
        INSTALL_DEPS=true
        CREATE_REPORTS=true
        CONFIG_ONLY=true
    fi
    
    # Run setup steps
    check_python
    check_dependencies
    
    if [ "$INSTALL_DEPS" = true ]; then
        install_python_dependencies
    fi
    
    if [ "$CREATE_REPORTS" = true ]; then
        create_report_directories
    fi
    
    if [ "$CONFIG_ONLY" = true ] || [ "$INSTALL_DEPS" = true ]; then
        create_config_files
        create_wrapper_scripts
    fi
    
    if [ "$SETUP_CRON" = true ]; then
        setup_cron_jobs
    fi
    
    if [ "$TEST_TOOLS" = true ]; then
        test_validation_tools
    fi
    
    echo ""
    log_success "Documentation validation tools setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Run validation: $TOOLS_DIR/validate_all.sh"
    echo "  2. Check reports: $REPORTS_DIR"
    echo "  3. Configure cron: $0 --setup-cron"
    echo ""
    echo "📖 Tool usage:"
    echo "  • Comprehensive validation: python3 $TOOLS_DIR/comprehensive_doc_validator.py"
    echo "  • Drift detection: python3 $TOOLS_DIR/doc_drift_detector.py"
    echo "  • Quality checking: python3 $TOOLS_DIR/doc_quality_checker.py"
    echo ""
}

# Run main function
main "$@"