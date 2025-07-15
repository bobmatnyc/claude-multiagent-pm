#!/bin/bash
# CMPM User Guide PDF Generation Script (Simple)
# Usage: ./generate-pdf-simple.sh [output-filename]

set -e

# Configuration
OUTPUT_FILE="${1:-CMPM-User-Guide-v4.1.0.pdf}"
DOCS_DIR="/Users/masa/Projects/claude-multiagent-pm/docs/user-guide"
TEMP_DIR="/tmp/cmpm-guide-build"

echo "🔧 Generating CMPM User Guide PDF..."
echo "📝 Output file: $OUTPUT_FILE"

# Create temporary build directory
mkdir -p "$TEMP_DIR"

echo "📋 Combining all sections..."

# Create title page and combine all sections
{
    echo "# Claude Multi-Agent PM Framework"
    echo "## User Guide v4.1.0"
    echo ""
    echo "**Complete Developer Documentation**"
    echo ""
    echo "CMPM Framework Team"
    echo ""
    echo "$(date +'%B %d, %Y')"
    echo ""
    echo "---"
    echo ""
    
    # Table of Contents
    echo "# Table of Contents"
    echo ""
    echo "1. [Master User Guide](README.md)"
    echo "2. [Structure & Navigation](#structure--navigation)"
    echo "3. [Getting Started & Installation](#getting-started--installation)"
    echo "4. [Architecture & Core Concepts](#architecture--core-concepts)"
    echo "5. [Claude Slash Commands & Orchestration](#claude-slash-commands--orchestration)"
    echo "6. [Directory Organization & Best Practices](#directory-organization--best-practices)"
    echo "7. [Custom Agent Development](#custom-agent-development)"
    echo "8. [Advanced Features & Integration](#advanced-features--integration)"
    echo "9. [Troubleshooting & FAQ](#troubleshooting--faq)"
    echo ""
    echo "\\newpage"
    echo ""
    
    # Add each section with headers
    echo "# Master User Guide"
    cat "$DOCS_DIR/README.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Structure & Navigation"
    cat "$DOCS_DIR/00-structure-navigation.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Getting Started & Installation"
    cat "$DOCS_DIR/01-getting-started.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Architecture & Core Concepts"
    cat "$DOCS_DIR/02-architecture-concepts.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Claude Slash Commands & Orchestration"
    cat "$DOCS_DIR/03-slash-commands-orchestration.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Directory Organization & Best Practices"
    cat "$DOCS_DIR/04-directory-organization.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Custom Agent Development"
    cat "$DOCS_DIR/05-custom-agents.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Advanced Features & Integration"
    cat "$DOCS_DIR/06-advanced-features.md"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Troubleshooting & FAQ"
    cat "$DOCS_DIR/07-troubleshooting-faq.md"
    
} > "$TEMP_DIR/complete-guide.md"

echo "🔧 Converting to HTML..."

# Generate HTML first (simplified)
pandoc "$TEMP_DIR/complete-guide.md" \
    --output "$TEMP_DIR/guide.html" \
    --from markdown \
    --to html5 \
    --standalone \
    --highlight-style=tango \
    --metadata title="Claude Multi-Agent PM Framework User Guide v4.1.0"

echo "📄 HTML version created: $TEMP_DIR/guide.html"

# Try to find any available PDF converter
PDF_CREATED=false

if command -v wkhtmltopdf &> /dev/null; then
    echo "📄 Converting with wkhtmltopdf..."
    wkhtmltopdf \
        --page-size A4 \
        --margin-top 0.75in \
        --margin-right 0.75in \
        --margin-bottom 0.75in \
        --margin-left 0.75in \
        --enable-local-file-access \
        "$TEMP_DIR/guide.html" \
        "$OUTPUT_FILE" && PDF_CREATED=true
elif command -v weasyprint &> /dev/null; then
    echo "📄 Converting with weasyprint..."
    weasyprint "$TEMP_DIR/guide.html" "$OUTPUT_FILE" && PDF_CREATED=true
elif command -v prince &> /dev/null; then
    echo "📄 Converting with prince..."
    prince "$TEMP_DIR/guide.html" -o "$OUTPUT_FILE" && PDF_CREATED=true
elif command -v chromium &> /dev/null; then
    echo "📄 Converting with Chromium..."
    chromium --headless --disable-gpu --print-to-pdf="$OUTPUT_FILE" "$TEMP_DIR/guide.html" && PDF_CREATED=true
elif command -v google-chrome &> /dev/null; then
    echo "📄 Converting with Chrome..."
    google-chrome --headless --disable-gpu --print-to-pdf="$OUTPUT_FILE" "$TEMP_DIR/guide.html" && PDF_CREATED=true
else
    echo "❌ No PDF converter found. Trying pandoc direct conversion..."
    
    # Try pandoc direct to PDF without LaTeX
    if pandoc --list-extensions | grep -q "pdf"; then
        echo "📄 Trying pandoc direct PDF..."
        pandoc "$TEMP_DIR/complete-guide.md" \
            --output "$OUTPUT_FILE" \
            --from markdown \
            --standalone && PDF_CREATED=true
    fi
fi

if [ "$PDF_CREATED" = true ] && [ -f "$OUTPUT_FILE" ]; then
    echo "✅ PDF generated successfully: $OUTPUT_FILE"
    echo "📄 File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "📊 Guide ready for print and distribution"
    echo ""
    echo "🎯 Features included:"
    echo "   ✅ Complete user guide content"
    echo "   ✅ Professional formatting"
    echo "   ✅ Structured sections"
    echo "   ✅ Print-optimized layout"
else
    echo "❌ PDF generation failed. Creating HTML fallback..."
    
    # Copy HTML version as fallback
    HTML_OUTPUT="${OUTPUT_FILE%.pdf}.html"
    cp "$TEMP_DIR/guide.html" "$HTML_OUTPUT"
    echo "📋 HTML version saved as: $HTML_OUTPUT"
    echo "💡 You can open this in a browser and print to PDF manually"
    echo "💡 Or install: brew install wkhtmltopdf"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "🎉 CMMP User Guide generation complete!"