# PDF Generation Knowledge Base

Generated: 2025-07-09T06:45:00.000000

## ✅ Chrome-based PDF Generation Success Pattern (CRITICAL)

**Category:** pattern
**Tags:** pdf, chrome, headless, success, documentation, critical
**Status:** production_ready
**Success Metrics:** 7.8MB professional output, 100% content completeness

### Critical Success Implementation

```bash
#!/bin/bash
# CMPM User Guide PDF Generation Script (Chrome-based)
# Usage: ./generate-pdf-chrome.sh [output-filename]

set -e

# Configuration
OUTPUT_FILE="${1:-CMPM-User-Guide-v4.1.0.pdf}"
HTML_FILE="CMPM-User-Guide-v4.1.0.html"
CURRENT_DIR="$(pwd)"

echo "🔧 Generating CMPM User Guide PDF using Chrome..."
echo "📝 Output file: $OUTPUT_FILE"

# Check if HTML file exists
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML file not found: $HTML_FILE"
    echo "💡 Run ./generate-pdf-simple.sh first to create the HTML version"
    exit 1
fi

# Check for Chrome
CHROME_PATH=""
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif command -v google-chrome &> /dev/null; then
    CHROME_PATH="google-chrome"
elif command -v chromium &> /dev/null; then
    CHROME_PATH="chromium"
else
    echo "❌ Chrome/Chromium not found"
    echo "💡 Please install Google Chrome or Chromium"
    exit 1
fi

echo "📄 Using Chrome at: $CHROME_PATH"
echo "🔧 Converting HTML to PDF..."

# Convert HTML to PDF using Chrome
"$CHROME_PATH" \
    --headless \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-dev-shm-usage \
    --no-sandbox \
    --print-to-pdf="$OUTPUT_FILE" \
    --print-to-pdf-no-header \
    --run-all-compositor-stages-before-draw \
    --virtual-time-budget=5000 \
    "file://$CURRENT_DIR/$HTML_FILE"

# Check if PDF was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ PDF generated successfully: $OUTPUT_FILE"
    echo "📄 File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "📊 Guide ready for print and distribution"
else
    echo "❌ PDF generation failed"
    echo "📋 HTML version is still available at: $HTML_FILE"
    exit 1
fi
```

### Key Success Factors

1. **Critical Chrome Configuration:**
   - `--virtual-time-budget=5000`: Ensures full page rendering
   - `--run-all-compositor-stages-before-draw`: Complete layout calculation
   - `--print-to-pdf-no-header`: Clean output without browser headers
   - `--disable-gpu`: Prevents rendering issues in headless mode

2. **Pipeline Requirements:**
   - HTML file must exist before PDF generation
   - Use pandoc for markdown → HTML conversion
   - Working directory must contain HTML file
   - File path must be absolute (`file://$CURRENT_DIR/$HTML_FILE`)

3. **Quality Validation:**
   - **File Size:** 7.8MB indicates rich content preservation
   - **Content Completeness:** All sections included
   - **Formatting:** Professional layout with syntax highlighting
   - **Navigation:** Structured TOC and professional formatting

### Framework Integration

This pattern represents the **FIRST SUCCESSFUL** PDF generation for the CMPM framework, achieving professional quality output suitable for print distribution. This approach should be used for all future PDF generation needs across the framework.

---

## PDF Generation Script Template (Legacy - Pandoc-based)

**Category:** pattern
**Tags:** pdf, documentation, build, script, pandoc

#!/bin/bash
# CMPM User Guide PDF Generation Script
# Usage: ./generate-pdf.sh [output-filename]

set -e

# Configuration
OUTPUT_FILE="${1:-cmpm-user-guide.pdf}"
DOCS_DIR="/Users/masa/Projects/claude-multiagent-pm/docs/user-guide"
TEMP_DIR="/tmp/cmpm-guide-build"

echo "🔧 Generating CMPM User Guide PDF..."

# Create temporary build directory
mkdir -p "$TEMP_DIR"

# Concatenate all sections in order
cat "$DOCS_DIR/README.md" \
    "$DOCS_DIR/00-structure-navigation.md" \
    "$DOCS_DIR/01-getting-started.md" \
    "$DOCS_DIR/02-architecture-concepts.md" \
    "$DOCS_DIR/03-slash-commands-orchestration.md" \
    "$DOCS_DIR/04-directory-organization.md" \
    "$DOCS_DIR/05-custom-agents.md" \
    "$DOCS_DIR/06-advanced-features.md" \
    "$DOCS_DIR/07-troubleshooting-faq.md" > "$TEMP_DIR/complete-guide.md"

# Generate PDF with pandoc
pandoc "$TEMP_DIR/complete-guide.md" \
    --output "$OUTPUT_FILE" \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --variable geometry:margin=1in \
    --variable fontsize=11pt \
    --variable documentclass=article \
    --variable colorlinks=true \
    --variable linkcolor=blue \
    --variable urlcolor=blue \
    --variable toccolor=black \
    --metadata title="Claude Multi-Agent PM Framework User Guide" \
    --metadata author="CMPM Framework Team" \
    --metadata date="$(date +%Y-%m-%d)"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ PDF generated successfully: $OUTPUT_FILE"
echo "📄 Guide ready for print and distribution"

---

## PDF Generation Process Documentation

**Category:** project
**Tags:** pdf, documentation, process, workflow

PDF Generation Process Documentation

## Overview
The PDF generation process for the Claude Multi-Agent PM Framework creates professional documentation suitable for print and distribution.

## Requirements
- pandoc: Universal document converter
- xelatex: LaTeX engine for PDF generation
- Properly structured markdown files in correct order

## Process Flow
1. **File Preparation**: Concatenate all user guide sections in logical order
2. **Content Processing**: Merge markdown files into single document
3. **PDF Generation**: Use pandoc with xelatex engine and professional formatting
4. **Cleanup**: Remove temporary files and directories

## Key Features
- Table of Contents (TOC) with 3-level depth
- Section numbering for easy navigation
- Professional styling with 1-inch margins
- Hyperlinked cross-references
- Branded metadata (title, author, date)

## File Order
1. README.md - Introduction and overview
2. 00-structure-navigation.md - Navigation guide
3. 01-getting-started.md - Getting started
4. 02-architecture-concepts.md - Architecture concepts
5. 03-slash-commands-orchestration.md - Command orchestration
6. 04-directory-organization.md - Directory structure
7. 05-custom-agents.md - Custom agents
8. 06-advanced-features.md - Advanced features
9. 07-troubleshooting-faq.md - Troubleshooting

## Output Quality
- Professional print-ready format
- Consistent styling throughout
- Clear section breaks and numbering
- Cross-referenced links and TOC

---

## PDF Generation Usage Patterns

**Category:** team
**Tags:** pdf, usage, best-practices, patterns

PDF Generation Usage Patterns and Best Practices

## Basic Usage
```bash
# Make script executable
chmod +x generate-pdf.sh

# Generate PDF with default name
./generate-pdf.sh

# Generate PDF with custom filename
./generate-pdf.sh my-custom-guide.pdf
```

## Best Practices
1. **File Organization**: Ensure all markdown files are in correct order
2. **Content Quality**: Validate markdown syntax before generation
3. **Dependencies**: Verify pandoc and xelatex are installed
4. **Testing**: Test generation process before production use
5. **Backup**: Keep backup of source files before major changes

## Common Issues and Solutions
- **Missing Dependencies**: Install pandoc and texlive-xetex
- **File Not Found**: Verify all markdown files exist in docs directory
- **Formatting Issues**: Check markdown syntax and fix any errors
- **Permission Errors**: Ensure script has execute permissions

## Customization Options
- **Styling**: Modify pandoc variables for different formatting
- **Content**: Update file list to include/exclude sections
- **Metadata**: Customize title, author, and date fields
- **Output**: Change output directory or filename patterns

## Integration Points
- **CI/CD**: Can be integrated into automated documentation builds
- **Version Control**: Track changes to documentation structure
- **Distribution**: Output suitable for sharing and printing
- **Archival**: Generate versioned documentation snapshots

## Performance Considerations
- **File Size**: Large guides may take longer to process
- **Memory Usage**: Complex formatting requires sufficient system memory
- **Temporary Files**: Script cleans up temporary files automatically
- **Parallel Processing**: Single-threaded, suitable for most use cases

---

## PDF Generation Workflow Template

**Category:** pattern
**Tags:** pdf, workflow, template, implementation

PDF Generation Workflow Template

## Template Overview
This template provides a standardized approach to implementing PDF generation for project documentation.

## Implementation Steps
1. **Setup Dependencies**
   - Install pandoc: `brew install pandoc` (macOS) or `apt-get install pandoc` (Ubuntu)
   - Install LaTeX: `brew install --cask mactex` (macOS) or `apt-get install texlive-xetex` (Ubuntu)

2. **Create Directory Structure**
   ```
   docs/
   ├── user-guide/
   │   ├── README.md
   │   ├── 00-navigation.md
   │   ├── 01-getting-started.md
   │   ├── ...
   │   └── generate-pdf.sh
   ```

3. **Configure Build Script**
   - Adapt file paths to project structure
   - Update metadata (title, author, organization)
   - Customize styling variables as needed

4. **Test Generation Process**
   - Verify all source files exist
   - Test script execution
   - Review output quality
   - Validate cross-references

5. **Integration Options**
   - Add to CI/CD pipeline
   - Create documentation release process
   - Automate versioning and distribution

## Customization Variables
- `OUTPUT_FILE`: Default output filename
- `DOCS_DIR`: Source documentation directory
- `TEMP_DIR`: Temporary build directory
- Pandoc variables: geometry, fontsize, documentclass, etc.

## Quality Assurance
- Run markdown linting before generation
- Test with different content sizes
- Verify cross-references work correctly
- Check output on different devices/viewers

## Maintenance
- Update script when directory structure changes
- Review and update metadata regularly
- Monitor for pandoc version compatibility
- Keep backup of working configurations

---

