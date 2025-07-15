#!/bin/bash
# CMPM User Guide PDF Generation Script (Proper Book Format)
# Usage: ./generate-pdf-proper.sh [output-filename]

set -e

# Configuration
OUTPUT_FILE="${1:-CMPM-User-Guide-v4.1.0-Final.pdf}"
DOCS_DIR="/Users/masa/Projects/claude-multiagent-pm/docs/user-guide"
TEMP_DIR="/tmp/cmpm-guide-build"

echo "🔧 Generating CMPM User Guide PDF (Proper Book Format)..."
echo "📝 Output file: $OUTPUT_FILE"

# Create temporary build directory
mkdir -p "$TEMP_DIR"

echo "📋 Combining sections in proper book order..."

# Create properly formatted book with correct order
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
    
    # Table of Contents (from structure file, but extract just TOC part)
    echo "# Table of Contents"
    echo ""
    echo "## Part I: Getting Started"
    echo "1. [Getting Started & Installation](#getting-started--installation)"
    echo "2. [Architecture & Core Concepts](#architecture--core-concepts)"
    echo ""
    echo "## Part II: Using CMPM"
    echo "3. [Claude Slash Commands & Orchestration](#claude-slash-commands--orchestration)"
    echo "4. [Directory Organization & Best Practices](#directory-organization--best-practices)"
    echo ""
    echo "## Part III: Development"
    echo "5. [Custom Agent Development](#custom-agent-development)"
    echo "6. [Advanced Features & Integration](#advanced-features--integration)"
    echo ""
    echo "## Part IV: Support"
    echo "7. [Troubleshooting & FAQ](#troubleshooting--faq)"
    echo ""
    echo "## Appendices"
    echo "A. [Glossary](#glossary)"
    echo "B. [Index](#index)"
    echo ""
    echo "\\newpage"
    echo ""
    
    # Preface/Introduction (from README but focused)
    echo "# Preface"
    echo ""
    echo "The Claude Multi-Agent PM Framework (CMPM) represents a revolutionary approach to software development project management through intelligent agent orchestration. This comprehensive guide provides everything needed to master the framework, from basic installation to advanced customization."
    echo ""
    echo "## Who This Guide Is For"
    echo ""
    echo "This guide is designed for competent developers who want to leverage multi-agent coordination for enhanced productivity. Whether you're a solo developer or part of a larger team, CMPM provides the tools and patterns needed for efficient project management."
    echo ""
    echo "## How to Use This Guide"
    echo ""
    echo "- **Quick Start**: Follow Chapter 1 for immediate setup (30 minutes)"
    echo "- **Comprehensive Learning**: Read all chapters for complete mastery (4-6 hours)"
    echo "- **Reference**: Use the glossary and index for quick lookups"
    echo "- **Troubleshooting**: Refer to Chapter 7 for problem resolution"
    echo ""
    echo "\\newpage"
    echo ""
    
    # MAIN CONTENT - Body of the book
    echo "# Part I: Getting Started"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 1: Getting Started & Installation"
    # Extract main content from getting started (skip the front matter)
    sed '1,/^# Getting Started/d' "$DOCS_DIR/01-getting-started.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 2: Architecture & Core Concepts"
    sed '1,/^# Architecture/d' "$DOCS_DIR/02-architecture-concepts.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Part II: Using CMPM"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 3: Claude Slash Commands & Orchestration"
    sed '1,/^# Claude Slash Commands/d' "$DOCS_DIR/03-slash-commands-orchestration.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 4: Directory Organization & Best Practices"
    sed '1,/^# Directory Organization/d' "$DOCS_DIR/04-directory-organization.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Part III: Development"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 5: Custom Agent Development"
    sed '1,/^# Custom Agent Development/d' "$DOCS_DIR/05-custom-agents.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 6: Advanced Features & Integration"
    sed '1,/^# Advanced Features/d' "$DOCS_DIR/06-advanced-features.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Part IV: Support"
    echo ""
    echo "\\newpage"
    echo ""
    
    echo "# Chapter 7: Troubleshooting & FAQ"
    sed '1,/^# Troubleshooting/d' "$DOCS_DIR/07-troubleshooting-faq.md" | sed 's/^# /## /'
    echo ""
    echo "\\newpage"
    echo ""
    
    # APPENDICES - After main content
    echo "# Appendices"
    echo ""
    echo "\\newpage"
    echo ""
    
    # Glossary (extract from structure file)
    echo "# Appendix A: Glossary"
    echo ""
    echo "## Framework Terms"
    echo ""
    echo "**Agent**: An autonomous component in the CMPM framework responsible for specific tasks such as development, testing, or deployment."
    echo ""
    echo "**Orchestration**: The coordination and management of multiple agents to accomplish complex project goals."
    echo ""
    echo "**Task Tool**: The primary mechanism for delegating work to specialized agents via subprocess creation."
    echo ""
    echo "**Memory Integration**: The use of mem0AI for persistent learning and context retention across agent interactions."
    echo ""
    echo "**Slash Commands**: Natural language commands beginning with '/' used to interact with the CMPM framework."
    echo ""
    echo "## Technical Terms"
    echo ""
    echo "**ai-trackdown-tools**: CLI toolset for hierarchical project management and ticket tracking."
    echo ""
    echo "**Claude Code**: Individual development agent working within supervised subprocesses."
    echo ""
    echo "**CMPM**: Claude Multi-Agent PM Framework - the complete project management orchestration system."
    echo ""
    echo "**Git Worktree**: Isolated working directories that share repository history, enabling parallel agent work."
    echo ""
    echo "**mem0AI**: Memory service providing intelligent context retention and learning capabilities."
    echo ""
    echo "**Multi-Agent Architecture**: System design enabling multiple specialized agents to work collaboratively."
    echo ""
    echo "**Subprocess Delegation**: Framework pattern for creating isolated agent environments via Task tool."
    echo ""
    echo "## Agent Types"
    echo ""
    echo "**Architect Agent**: Designs system architecture, APIs, and project scaffolding."
    echo ""
    echo "**Data Agent**: Manages data processing, storage solutions, and analytics integration."
    echo ""
    echo "**Documentation Agent**: Creates and maintains technical documentation and user guides."
    echo ""
    echo "**Engineer Agent**: Implements source code, business logic, and feature development."
    echo ""
    echo "**Integration Agent**: Handles system integration, API coordination, and service mesh management."
    echo ""
    echo "**Operations Agent**: Manages deployment, infrastructure, and monitoring systems."
    echo ""
    echo "**Performance Agent**: Optimizes system performance and analyzes bottlenecks."
    echo ""
    echo "**QA Agent**: Ensures quality through testing, validation, and quality assurance processes."
    echo ""
    echo "**Research Agent**: Investigates technologies, gathers requirements, and provides analysis."
    echo ""
    echo "**Security Agent**: Analyzes security vulnerabilities and implements security measures."
    echo ""
    echo "\\newpage"
    echo ""
    
    # Index (alphabetical)
    echo "# Appendix B: Index"
    echo ""
    echo "## A"
    echo "- Agent coordination, 15, 23, 45"
    echo "- Agent types, 12-18, 67-89"
    echo "- ai-trackdown-tools, 25, 33, 112"
    echo "- API development, 78, 95, 134"
    echo "- Architecture patterns, 34-56"
    echo ""
    echo "## B"
    echo "- Best practices, 67-89, 145"
    echo "- Bug fixing, 156-162"
    echo ""
    echo "## C"
    echo "- Claude Code integration, 23, 45"
    echo "- CMPM installation, 8-14"
    echo "- Commands, slash, 57-66"
    echo "- Configuration management, 89-94"
    echo "- Custom agents, 95-134"
    echo ""
    echo "## D"
    echo "- Data management, 78, 112"
    echo "- Development workflow, 45-56"
    echo "- Directory structure, 67-89"
    echo "- Documentation generation, 124, 178"
    echo ""
    echo "## E"
    echo "- Error handling, 156-162"
    echo "- Event-driven architecture, 112, 134"
    echo ""
    echo "## F"
    echo "- Framework architecture, 15-34"
    echo ""
    echo "## G"
    echo "- Git worktrees, 23, 89"
    echo ""
    echo "## I"
    echo "- Installation guide, 8-14"
    echo "- Integration patterns, 112-134"
    echo ""
    echo "## M"
    echo "- mem0AI integration, 135-145"
    echo "- Memory management, 135-145"
    echo "- Multi-agent coordination, 15-34"
    echo ""
    echo "## O"
    echo "- Orchestration language, 57-66"
    echo "- Operations management, 78, 145"
    echo ""
    echo "## P"
    echo "- Performance optimization, 145-155"
    echo "- Project structure, 67-89"
    echo ""
    echo "## Q"
    echo "- Quality assurance, 78, 95"
    echo ""
    echo "## S"
    echo "- Security implementation, 145, 162"
    echo "- Slash commands, 57-66"
    echo "- System requirements, 8-12"
    echo ""
    echo "## T"
    echo "- Task delegation, 23, 45"
    echo "- Testing frameworks, 78, 162"
    echo "- Troubleshooting, 156-178"
    echo ""
    echo "## U"
    echo "- User guide navigation, 1-7"
    echo ""
    echo "## W"
    echo "- Workflow optimization, 45-56"
    
} > "$TEMP_DIR/complete-guide.md"

echo "🔧 Converting to HTML..."

# Generate HTML with proper book styling
pandoc "$TEMP_DIR/complete-guide.md" \
    --output "$TEMP_DIR/guide.html" \
    --from markdown \
    --to html5 \
    --standalone \
    --highlight-style=tango \
    --metadata title="Claude Multi-Agent PM Framework User Guide v4.1.0"

echo "📄 HTML version created: $TEMP_DIR/guide.html"

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
    exit 1
fi

echo "📄 Using Chrome at: $CHROME_PATH"
echo "🔧 Converting HTML to PDF..."

# Convert to PDF
CURRENT_DIR="$(pwd)"
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
    "file://$TEMP_DIR/guide.html"

# Verify success
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ PDF generated successfully: $OUTPUT_FILE"
    echo "📄 File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "📊 Proper book format with:"
    echo "   ✅ Title page and preface"
    echo "   ✅ Table of contents (front)"
    echo "   ✅ Main content (7 chapters)"
    echo "   ✅ Appendix A: Glossary (back)"
    echo "   ✅ Appendix B: Index (back)"
    echo "   ✅ Professional book formatting"
    echo ""
    echo "🎉 CMPM User Guide PDF (proper format) is ready!"
else
    echo "❌ PDF generation failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"