# Documentation Validation Tools

Automated validation and monitoring tools for comprehensive documentation quality assurance.

## Overview

This suite of tools provides automated validation, drift detection, and quality assessment for documentation, ensuring consistency, accuracy, and maintainability across the entire documentation set.

## Tools Included

### 1. Comprehensive Document Validator (`comprehensive_doc_validator.py`)

**Purpose**: Complete validation suite for links, code examples, and references.

**Features**:
- ✅ Internal and external link validation
- ✅ Code example syntax checking (Python, Bash, JavaScript, JSON)
- ✅ Ticket reference validation against ai-trackdown system
- ✅ Markdown structure validation
- ✅ File reference verification
- ✅ Anchor link validation
- ✅ Comprehensive error reporting

**Usage**:
```bash
# Basic validation
python3 comprehensive_doc_validator.py /path/to/docs

# With custom output
python3 comprehensive_doc_validator.py /path/to/docs --output validation_report.json

# Verbose output
python3 comprehensive_doc_validator.py /path/to/docs --verbose
```

### 2. Documentation Drift Detector (`doc_drift_detector.py`)

**Purpose**: Monitors for documentation drift and outdated content.

**Features**:
- 📅 File modification time tracking
- 🔄 API change detection
- ⚙️ Configuration drift monitoring
- 🔗 Broken reference detection
- 📊 Version mismatch identification
- 💡 Actionable recommendations

**Usage**:
```bash
# Basic drift detection
python3 doc_drift_detector.py /path/to/docs

# With custom configuration
python3 doc_drift_detector.py /path/to/docs --config drift_config.json

# Custom staleness threshold
python3 doc_drift_detector.py /path/to/docs --max-age 45
```

### 3. Documentation Quality Checker (`doc_quality_checker.py`)

**Purpose**: Automated quality assurance for documentation.

**Features**:
- 📝 Spell checking with technical dictionary
- 📖 Readability score analysis (Flesch Reading Ease)
- 🏗️ Structure consistency checking
- ✨ Grammar and style validation
- 🔍 Content completeness validation
- 📊 Comprehensive quality metrics

**Usage**:
```bash
# Basic quality check
python3 doc_quality_checker.py /path/to/docs

# Custom readability threshold
python3 doc_quality_checker.py /path/to/docs --min-readability 50

# Custom sentence length limit
python3 doc_quality_checker.py /path/to/docs --max-sentence-length 20
```

### 4. Setup Script (`setup_validation_tools.sh`)

**Purpose**: Environment setup and automation configuration.

**Features**:
- 🔧 Dependency installation
- 📁 Report directory creation
- ⚙️ Configuration file generation
- 🕒 Automated scheduling setup
- 🧪 Tool testing and validation

**Usage**:
```bash
# Basic setup
./setup_validation_tools.sh

# Install dependencies and create reports
./setup_validation_tools.sh --install-deps --create-reports

# Set up automated scheduling
./setup_validation_tools.sh --setup-cron

# Test all tools
./setup_validation_tools.sh --test-tools
```

## Installation & Setup

### Quick Start

1. **Run the setup script**:
   ```bash
   cd /path/to/docs/tools
   ./setup_validation_tools.sh
   ```

2. **Test the tools**:
   ```bash
   ./setup_validation_tools.sh --test-tools
   ```

3. **Run validation**:
   ```bash
   ./validate_all.sh
   ```

### Manual Setup

1. **Check Python requirements**:
   ```bash
   python3 --version  # Requires Python 3.8+
   ```

2. **Install optional dependencies**:
   ```bash
   pip3 install PyYAML requests --user
   ```

3. **Create report directories**:
   ```bash
   mkdir -p ../validation-reports/{validation,drift,quality}/{daily,weekly}
   ```

4. **Configure tools** (optional):
   ```bash
   mkdir -p ../config
   cp config/*.json ../config/
   ```

## Configuration

### Drift Detection Configuration

Edit `config/drift_config.json`:

```json
{
    "max_age_days": 30,
    "critical_files": [
        "README.md",
        "QUICK_START.md",
        "DEPLOYMENT_GUIDE.md"
    ],
    "api_patterns": [
        "aitrackdown\\s+\\w+",
        "mem0\\.\\w+"
    ],
    "ignore_patterns": [
        "archive/",
        "node_modules/",
        ".git/"
    ]
}
```

### Quality Check Configuration

Edit `config/quality_config.json`:

```json
{
    "readability": {
        "min_score": 40,
        "target_score": 60
    },
    "sentence_length": {
        "max_words": 25,
        "ideal_words": 20
    },
    "style_rules": {
        "avoid_passive_voice": true,
        "check_spelling": true,
        "check_grammar": true
    }
}
```

## Automation

### Daily Validation

Automatically run lightweight validation every day:

```bash
./setup_validation_tools.sh --setup-cron
```

This sets up:
- **Daily**: Quick validation at 2 AM
- **Weekly**: Comprehensive validation on Sundays at 3 AM

### Manual Automation

Add to your CI/CD pipeline:

```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation

on:
  push:
    paths:
      - 'docs/**'
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Run validation
        run: |
          cd docs/tools
          python3 comprehensive_doc_validator.py ..
          python3 doc_drift_detector.py ..
          python3 doc_quality_checker.py ..
```

## Reports

### Report Structure

```
validation-reports/
├── validation/          # Comprehensive validation reports
│   ├── daily/          # Daily validation results
│   └── weekly/         # Weekly comprehensive reports
├── drift/              # Drift detection reports
│   ├── daily/          # Daily drift monitoring
│   └── weekly/         # Weekly drift analysis
├── quality/            # Quality assessment reports
│   ├── daily/          # Daily quality checks
│   └── weekly/         # Weekly quality summaries
└── archive/            # Historical reports
```

### Report Format

All reports are generated in JSON format with standardized structure:

```json
{
    "timestamp": "2025-07-09T10:30:00",
    "base_directory": "/path/to/docs",
    "total_files": 25,
    "summary": {
        "total_issues": 5,
        "high_severity": 1,
        "medium_severity": 2,
        "low_severity": 2
    },
    "issues": [
        {
            "file_path": "example.md",
            "issue_type": "broken_link",
            "severity": "high",
            "description": "External link unavailable",
            "line_number": 15,
            "suggestion": "Update or remove broken link"
        }
    ],
    "recommendations": [
        "Fix broken external links",
        "Update outdated API references"
    ]
}
```

## Integration

### With Framework Tools

The validation tools integrate with the Claude PM Framework:

- **Ticket Validation**: Verifies ticket references against ai-trackdown system
- **API Validation**: Checks framework command references
- **Configuration Monitoring**: Tracks config changes affecting docs

### With Development Workflow

1. **Pre-commit Hooks**: Run validation before commits
2. **CI/CD Integration**: Automated validation on pushes
3. **Scheduled Monitoring**: Daily drift detection
4. **Quality Gates**: Fail builds on critical issues

## Error Handling

### Exit Codes

- `0`: Success, no critical issues
- `1`: High priority issues found
- `2`: Critical issues requiring immediate attention

### Common Issues

1. **External Link Timeouts**: Increase timeout in configuration
2. **Missing Dependencies**: Run setup script with `--install-deps`
3. **Permission Errors**: Check file permissions and paths
4. **API Validation Failures**: Ensure ai-trackdown tools are installed

## Best Practices

### Running Validation

1. **Daily**: Run drift detection and basic validation
2. **Weekly**: Run comprehensive validation including external links
3. **Pre-release**: Run full quality assessment
4. **Post-changes**: Run targeted validation on modified files

### Addressing Issues

1. **Critical**: Fix immediately (broken links, missing content)
2. **High**: Address within 24 hours (outdated API references)
3. **Medium**: Address within week (readability issues)
4. **Low**: Address during maintenance cycles (style issues)

### Maintenance

1. **Update Technical Dictionary**: Add new framework terms
2. **Review Configurations**: Adjust thresholds based on results
3. **Archive Old Reports**: Clean up historical reports monthly
4. **Update Dependencies**: Keep validation tools current

## Troubleshooting

### Common Issues

**Tool fails to run**:
```bash
# Check Python version
python3 --version

# Check file permissions
ls -la *.py

# Run setup script
./setup_validation_tools.sh --test-tools
```

**External link validation slow**:
```bash
# Run without external links
python3 comprehensive_doc_validator.py . --skip-external
```

**Permission denied on cron setup**:
```bash
# Check cron permissions
crontab -l

# Manual cron setup
echo "0 2 * * * /path/to/daily_validation.sh" | crontab -
```

### Debug Mode

Enable verbose output for debugging:

```bash
# Add debug information
python3 comprehensive_doc_validator.py . --verbose

# Check specific file
python3 doc_quality_checker.py specific_file.md
```

## Support

For issues or questions:

1. Check the tool's `--help` output
2. Review generated reports for specific errors
3. Test with setup script: `./setup_validation_tools.sh --test-tools`
4. Check configuration files in `../config/`

## Version History

- **v1.0.0**: Initial release with comprehensive validation suite
- **v1.1.0**: Added drift detection and quality checking
- **v1.2.0**: Enhanced automation and reporting capabilities