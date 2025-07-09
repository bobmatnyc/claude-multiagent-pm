#!/usr/bin/env python3
"""
Script to store PDF generation knowledge in Claude PM Framework memory system.
This script stores the PDF generation script, process documentation, and usage patterns
in the mem0AI memory system for future reference and reuse.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_pm.services.memory_service import get_memory_service


class PDFKnowledgeStorer:
    """Store PDF generation knowledge in memory system."""
    
    def __init__(self):
        """Initialize the PDF knowledge storer."""
        self.config = {
            "mem0ai_host": "localhost",
            "mem0ai_port": 8002,
            "mem0ai_timeout": 30
        }
        self.memory_service = get_memory_service(self.config)
        self.project_name = "claude-multiagent-pm"
    
    async def store_pdf_knowledge(self) -> None:
        """Store comprehensive PDF generation knowledge."""
        try:
            # Initialize memory service
            await self.memory_service.initialize()
            
            # Access the underlying memory client
            memory_client = self.memory_service.client
            
            if not memory_client.is_connected():
                print("❌ Failed to connect to memory service")
                return
            
            print("🔧 Storing PDF generation knowledge...")
            
            # Store PDF generation script template
            script_content = '''#!/bin/bash
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
cat "$DOCS_DIR/README.md" \\
    "$DOCS_DIR/00-structure-navigation.md" \\
    "$DOCS_DIR/01-getting-started.md" \\
    "$DOCS_DIR/02-architecture-concepts.md" \\
    "$DOCS_DIR/03-slash-commands-orchestration.md" \\
    "$DOCS_DIR/04-directory-organization.md" \\
    "$DOCS_DIR/05-custom-agents.md" \\
    "$DOCS_DIR/06-advanced-features.md" \\
    "$DOCS_DIR/07-troubleshooting-faq.md" > "$TEMP_DIR/complete-guide.md"

# Generate PDF with pandoc
pandoc "$TEMP_DIR/complete-guide.md" \\
    --output "$OUTPUT_FILE" \\
    --pdf-engine=xelatex \\
    --toc \\
    --toc-depth=3 \\
    --number-sections \\
    --variable geometry:margin=1in \\
    --variable fontsize=11pt \\
    --variable documentclass=article \\
    --variable colorlinks=true \\
    --variable linkcolor=blue \\
    --variable urlcolor=blue \\
    --variable toccolor=black \\
    --metadata title="Claude Multi-Agent PM Framework User Guide" \\
    --metadata author="CMPM Framework Team" \\
    --metadata date="$(date +%Y-%m-%d)"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ PDF generated successfully: $OUTPUT_FILE"
echo "📄 Guide ready for print and distribution"'''
            
            memory_id = await memory_client.add_memory(
                self.project_name,
                script_content,
                "pattern",
                tags=["pdf", "documentation", "build", "script", "pandoc"],
                metadata={
                    "script_name": "generate-pdf.sh",
                    "purpose": "Generate PDF from user guide sections",
                    "dependencies": ["pandoc", "xelatex"],
                    "output_format": "PDF",
                    "last_updated": "2025-07-09"
                }
            )
            
            if memory_id:
                print(f"✅ Stored PDF generation script (ID: {memory_id})")
            else:
                print("❌ Failed to store PDF generation script")
            
            # Store process documentation
            process_docs = '''PDF Generation Process Documentation

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
- Cross-referenced links and TOC'''
            
            process_id = await memory_client.add_memory(
                self.project_name,
                process_docs,
                "project",
                tags=["pdf", "documentation", "process", "workflow"],
                metadata={
                    "document_type": "process_documentation",
                    "purpose": "Document PDF generation workflow",
                    "scope": "User guide documentation",
                    "quality_level": "professional",
                    "last_updated": "2025-07-09"
                }
            )
            
            if process_id:
                print(f"✅ Stored process documentation (ID: {process_id})")
            else:
                print("❌ Failed to store process documentation")
            
            # Store usage patterns and best practices
            usage_patterns = '''PDF Generation Usage Patterns and Best Practices

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
- **Parallel Processing**: Single-threaded, suitable for most use cases'''
            
            patterns_id = await memory_client.add_memory(
                self.project_name,
                usage_patterns,
                "team",
                tags=["pdf", "usage", "best-practices", "patterns"],
                metadata={
                    "document_type": "usage_patterns",
                    "purpose": "Document PDF generation best practices",
                    "audience": "development_team",
                    "complexity": "intermediate",
                    "last_updated": "2025-07-09"
                }
            )
            
            if patterns_id:
                print(f"✅ Stored usage patterns (ID: {patterns_id})")
            else:
                print("❌ Failed to store usage patterns")
            
            # Store workflow template for future projects
            workflow_template = '''PDF Generation Workflow Template

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
- Keep backup of working configurations'''
            
            workflow_id = await memory_client.add_memory(
                self.project_name,
                workflow_template,
                "pattern",
                tags=["pdf", "workflow", "template", "implementation"],
                metadata={
                    "document_type": "workflow_template",
                    "purpose": "Standardized PDF generation implementation",
                    "reusability": "high",
                    "complexity": "intermediate",
                    "last_updated": "2025-07-09"
                }
            )
            
            if workflow_id:
                print(f"✅ Stored workflow template (ID: {workflow_id})")
            else:
                print("❌ Failed to store workflow template")
            
            # Get memory statistics
            stats = await memory_client.get_memory_stats(self.project_name)
            print(f"\n📊 Memory Statistics:")
            print(f"   Total memories: {stats.get('total', 0)}")
            print(f"   Categories: {stats.get('categories', {})}")
            
            print("\n✅ PDF generation knowledge successfully stored in framework memory!")
            print("🔄 Knowledge is now available for future reference and reuse across projects.")
            
        except Exception as e:
            print(f"❌ Error storing PDF knowledge: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup memory service
            await self.memory_service.cleanup()


async def main():
    """Main execution function."""
    storer = PDFKnowledgeStorer()
    await storer.store_pdf_knowledge()


if __name__ == "__main__":
    asyncio.run(main())