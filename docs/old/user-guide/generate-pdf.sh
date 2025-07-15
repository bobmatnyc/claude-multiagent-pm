#!/bin/bash

# CMPM User Guide PDF Generation Script
# Generates a comprehensive PDF from all user guide sections

echo "📄 CMPM User Guide PDF Generation"
echo "================================="

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc is not installed. Please install pandoc first:"
    echo "   macOS: brew install pandoc"
    echo "   Ubuntu: sudo apt-get install pandoc"
    echo "   Windows: choco install pandoc"
    exit 1
fi

# Create output directory
mkdir -p output

# Set variables
OUTPUT_FILE="output/CMPM-User-Guide-v4.1.0.pdf"
TIMESTAMP=$(date +"%Y-%m-%d")

echo "📝 Generating comprehensive user guide PDF..."

# Create temporary combined file
TEMP_FILE="temp_combined.md"

# Start with README as cover page
cat README.md > $TEMP_FILE

# Add page break
echo -e "\n\\newpage\n" >> $TEMP_FILE

# Add table of contents from structure navigation
echo "# Table of Contents" >> $TEMP_FILE
echo "" >> $TEMP_FILE
# Extract TOC from structure navigation
sed -n '/## Complete Table of Contents/,/## Glossary of Terms/p' 00-structure-navigation.md | head -n -1 >> $TEMP_FILE

# Add page break
echo -e "\n\\newpage\n" >> $TEMP_FILE

# Add all sections in order
sections=(
    "01-getting-started.md"
    "02-architecture-concepts.md"
    "03-slash-commands-orchestration.md"
    "04-directory-organization.md"
    "05-custom-agents.md"
    "06-advanced-features.md"
    "07-troubleshooting-faq.md"
)

for section in "${sections[@]}"; do
    echo "   Adding $section..."
    cat "$section" >> $TEMP_FILE
    echo -e "\n\\newpage\n" >> $TEMP_FILE
done

# Add appendix from structure navigation
echo "# Appendix" >> $TEMP_FILE
echo "" >> $TEMP_FILE
sed -n '/## Glossary of Terms/,/## Navigation Guide/p' 00-structure-navigation.md | head -n -1 >> $TEMP_FILE

# Generate PDF with pandoc
echo "🔧 Converting to PDF..."
pandoc "$TEMP_FILE" -o "$OUTPUT_FILE" \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --highlight-style=github \
    --geometry=margin=1in \
    --variable=documentclass:article \
    --variable=fontsize:11pt \
    --variable=linestretch:1.15 \
    --variable=mainfont:"Georgia" \
    --variable=monofont:"Courier New" \
    --metadata title="Claude Multi-Agent PM Framework - User Guide" \
    --metadata author="CMPM Framework Team" \
    --metadata date="$TIMESTAMP" \
    --metadata version="4.1.0"

# Clean up temporary file
rm -f $TEMP_FILE

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo "✅ PDF generated successfully!"
    echo "📄 File: $OUTPUT_FILE"
    echo "📊 Size: $FILE_SIZE"
    echo "🎯 Version: 4.1.0"
    echo "📅 Generated: $TIMESTAMP"
    echo ""
    echo "💡 To view the PDF:"
    echo "   open $OUTPUT_FILE"
else
    echo "❌ PDF generation failed. Check pandoc installation and dependencies."
    exit 1
fi

echo ""
echo "🎉 User Guide PDF Generation Complete!"