#!/bin/bash
# CMPM User Guide PDF Generation Script (Fixed)
# Usage: ./generate-pdf-fixed.sh [output-filename]

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

# Combine all sections in order with proper headers
{
    echo "---"
    echo "title: 'Claude Multi-Agent PM Framework User Guide'"
    echo "subtitle: 'Complete Developer Documentation'"
    echo "author: 'CMPM Framework Team'"
    echo "date: '$(date +"%B %d, %Y")'"
    echo "version: '4.1.0'"
    echo "toc: true"
    echo "toc-depth: 3"
    echo "numbersections: true"
    echo "documentclass: article"
    echo "geometry: margin=1in"
    echo "fontsize: 11pt"
    echo "linkcolor: blue"
    echo "urlcolor: blue"
    echo "---"
    echo ""
    
    # Add each section
    cat "$DOCS_DIR/README.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/00-structure-navigation.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/01-getting-started.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/02-architecture-concepts.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/03-slash-commands-orchestration.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/04-directory-organization.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/05-custom-agents.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/06-advanced-features.md"
    echo -e "\n\\newpage\n"
    
    cat "$DOCS_DIR/07-troubleshooting-faq.md"
    
} > "$TEMP_DIR/complete-guide.md"

echo "🔧 Converting to PDF with pandoc..."

# Generate PDF with pandoc (simplified options for compatibility)
pandoc "$TEMP_DIR/complete-guide.md" \
    --output "$OUTPUT_FILE" \
    --pdf-engine=pdflatex \
    --from markdown \
    --to pdf \
    --standalone \
    --table-of-contents \
    --number-sections \
    --highlight-style=tango \
    --variable colorlinks=true \
    --variable links-as-notes=true

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
    echo "   ✅ Cross-references and links"
    echo "   ✅ Print-optimized layout"
else
    echo "❌ PDF generation failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "🎉 CMPM User Guide PDF generation complete!"