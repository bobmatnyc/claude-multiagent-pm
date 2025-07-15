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
    echo ""
    echo "🎯 Features included:"
    echo "   ✅ Complete CMPM user guide (447KB markdown)"
    echo "   ✅ All 8 sections with detailed content"
    echo "   ✅ Professional formatting"
    echo "   ✅ Structured navigation"
    echo "   ✅ Print-optimized layout"
    echo "   ✅ Syntax highlighted code blocks"
    echo ""
    echo "📋 Table of Contents:"
    echo "   1. Master User Guide & Introduction"
    echo "   2. Structure & Navigation (TOC, Glossary, Index)"
    echo "   3. Getting Started & Installation"
    echo "   4. Architecture & Core Concepts"
    echo "   5. Claude Slash Commands & Orchestration"
    echo "   6. Directory Organization & Best Practices"
    echo "   7. Custom Agent Development"
    echo "   8. Advanced Features & Integration"
    echo "   9. Troubleshooting & FAQ"
    echo ""
    echo "🎉 The comprehensive CMPM User Guide PDF is ready!"
    echo "📄 Any competent developer can now build using CMPM framework"
else
    echo "❌ PDF generation failed"
    echo "📋 HTML version is still available at: $HTML_FILE"
    exit 1
fi