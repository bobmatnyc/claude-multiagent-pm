#!/bin/bash
# CMPM User Guide PDF Generation Script (HTML-based)
# Usage: ./generate-pdf-html.sh [output-filename]

set -e

# Configuration
OUTPUT_FILE="${1:-CMPM-User-Guide-v4.1.0.pdf}"
DOCS_DIR="/Users/masa/Projects/claude-multiagent-pm/docs/user-guide"
TEMP_DIR="/tmp/cmpm-guide-build"

echo "🔧 Generating CMPM User Guide PDF via HTML..."
echo "📝 Output file: $OUTPUT_FILE"

# Create temporary build directory
mkdir -p "$TEMP_DIR"

echo "📋 Combining all sections..."

# Combine all sections in order
{
    echo "---"
    echo "title: 'Claude Multi-Agent PM Framework User Guide'"
    echo "subtitle: 'Complete Developer Documentation'"
    echo "author: 'CMPM Framework Team'"
    echo "date: '$(date +"%B %d, %Y")'"
    echo "version: '4.1.0'"
    echo "---"
    echo ""
    
    # Add each section
    cat "$DOCS_DIR/README.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/00-structure-navigation.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/01-getting-started.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/02-architecture-concepts.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/03-slash-commands-orchestration.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/04-directory-organization.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/05-custom-agents.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/06-advanced-features.md"
    echo -e "\n---\n"
    
    cat "$DOCS_DIR/07-troubleshooting-faq.md"
    
} > "$TEMP_DIR/complete-guide.md"

echo "🔧 Converting to HTML first..."

# Generate HTML first
pandoc "$TEMP_DIR/complete-guide.md" \
    --output "$TEMP_DIR/guide.html" \
    --from markdown \
    --to html5 \
    --standalone \
    --table-of-contents \
    --toc-depth=3 \
    --number-sections \
    --highlight-style=tango \
    --css-file=/dev/null \
    --metadata title="Claude Multi-Agent PM Framework User Guide v4.1.0"

echo "🔧 Converting HTML to PDF..."

# Try different PDF generation methods
if command -v wkhtmltopdf &> /dev/null; then
    echo "📄 Using wkhtmltopdf..."
    wkhtmltopdf \
        --page-size A4 \
        --margin-top 0.75in \
        --margin-right 0.75in \
        --margin-bottom 0.75in \
        --margin-left 0.75in \
        --enable-local-file-access \
        --print-media-type \
        "$TEMP_DIR/guide.html" \
        "$OUTPUT_FILE"
elif command -v weasyprint &> /dev/null; then
    echo "📄 Using weasyprint..."
    weasyprint "$TEMP_DIR/guide.html" "$OUTPUT_FILE"
elif command -v prince &> /dev/null; then
    echo "📄 Using prince..."
    prince "$TEMP_DIR/guide.html" -o "$OUTPUT_FILE"
else
    echo "❌ No suitable PDF converter found."
    echo "💡 Please install one of: wkhtmltopdf, weasyprint, or prince"
    echo "📄 HTML version available at: $TEMP_DIR/guide.html"
    
    # Copy HTML version to current directory as fallback
    cp "$TEMP_DIR/guide.html" "${OUTPUT_FILE%.pdf}.html"
    echo "📋 HTML version saved as: ${OUTPUT_FILE%.pdf}.html"
    
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Check if file was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ PDF generated successfully: $OUTPUT_FILE"
    echo "📄 File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "📊 Guide ready for print and distribution"
    echo ""
    echo "🎯 Features included:"
    echo "   ✅ Complete table of contents"
    echo "   ✅ Professional formatting"
    echo "   ✅ Numbered sections"
    echo "   ✅ Syntax highlighted code blocks"
    echo "   ✅ Print-optimized layout"
else
    echo "❌ PDF generation failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "🎉 CMPM User Guide PDF generation complete!"