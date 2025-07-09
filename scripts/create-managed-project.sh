#!/bin/bash

# Create Managed Project - M01-035 Template System
# Generates standardized managed project structure with proper documentation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_PM_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_DIR="$CLAUDE_PM_DIR/templates/managed-project"
MANAGED_DIR="$HOME/Projects/managed"

# Template variables
PROJECT_NAME=""
PROJECT_TYPE=""
PROJECT_TITLE=""
PROJECT_DESCRIPTION=""
PRIMARY_LANGUAGE=""
AUTHOR_NAME="$(git config user.name || echo 'Developer')"
AUTHOR_EMAIL="$(git config user.email || echo 'developer@example.com')"
CREATION_DATE="$(date '+%Y-%m-%d')"
VERSION="0.1.0"

# Usage function
usage() {
    echo -e "${BLUE}Usage: $0 <project-name> <project-type>${NC}"
    echo ""
    echo -e "${YELLOW}Project Types:${NC}"
    echo "  python-cli    - Python CLI tool"
    echo "  python-api    - Python API service"
    echo "  nodejs-cli    - Node.js CLI tool"
    echo "  nextjs-web    - Next.js web application"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 my-python-tool python-cli"
    echo "  $0 my-web-app nextjs-web"
    echo "  $0 my-api-service python-api"
    echo ""
    exit 1
}

# Error handling
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Info message
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Warning message
warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Validate input
validate_input() {
    if [ $# -lt 2 ]; then
        error_exit "Missing required arguments"
    fi

    PROJECT_NAME="$1"
    PROJECT_TYPE="$2"

    # Validate project name
    if [[ ! "$PROJECT_NAME" =~ ^[a-z0-9-]+$ ]]; then
        error_exit "Project name must contain only lowercase letters, numbers, and hyphens"
    fi

    # Validate project type
    case "$PROJECT_TYPE" in
        python-cli|python-api|nodejs-cli|nextjs-web)
            ;;
        *)
            error_exit "Invalid project type: $PROJECT_TYPE"
            ;;
    esac

    # Check if project already exists
    if [ -d "$MANAGED_DIR/$PROJECT_NAME" ]; then
        error_exit "Project directory already exists: $MANAGED_DIR/$PROJECT_NAME"
    fi
}

# Set project-type specific variables
configure_project_type() {
    case "$PROJECT_TYPE" in
        python-cli)
            PRIMARY_LANGUAGE="Python"
            PROJECT_PREFIX="$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]')"
            PROJECT_PREFIX="${PROJECT_PREFIX//-/_}"
            PROJECT_PREFIX="$(echo "$PROJECT_PREFIX" | cut -c1-3)"
            LANGUAGE_VERSION="3.10+"
            FRAMEWORK="Click/Typer"
            ;;
        python-api)
            PRIMARY_LANGUAGE="Python"
            PROJECT_PREFIX="$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]')"
            PROJECT_PREFIX="${PROJECT_PREFIX//-/_}"
            PROJECT_PREFIX="$(echo "$PROJECT_PREFIX" | cut -c1-3)"
            LANGUAGE_VERSION="3.10+"
            FRAMEWORK="FastAPI"
            ;;
        nodejs-cli)
            PRIMARY_LANGUAGE="TypeScript"
            PROJECT_PREFIX="$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]')"
            PROJECT_PREFIX="${PROJECT_PREFIX//-/_}"
            PROJECT_PREFIX="$(echo "$PROJECT_PREFIX" | cut -c1-3)"
            LANGUAGE_VERSION="5.8+"
            FRAMEWORK="Commander.js"
            ;;
        nextjs-web)
            PRIMARY_LANGUAGE="TypeScript"
            PROJECT_PREFIX="$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]')"
            PROJECT_PREFIX="${PROJECT_PREFIX//-/_}"
            PROJECT_PREFIX="$(echo "$PROJECT_PREFIX" | cut -c1-3)"
            LANGUAGE_VERSION="5.8+"
            FRAMEWORK="Next.js 15+"
            ;;
    esac

    # Convert project name to title
    PROJECT_TITLE="$(echo "$PROJECT_NAME" | sed 's/-/ /g' | sed 's/\b\w/\u&/g')"
}

# Create directory structure
create_structure() {
    info "Creating project directory structure..."
    
    mkdir -p "$MANAGED_DIR/$PROJECT_NAME"
    cd "$MANAGED_DIR/$PROJECT_NAME"
    
    # Create standard directories
    mkdir -p docs
    mkdir -p tasks/{epics,issues,tasks,prs,templates,scripts}
    
    success "Directory structure created"
}

# Process template file
process_template() {
    local template_file="$1"
    local output_file="$2"
    
    # Read template and substitute variables
    sed -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
        -e "s/{{PROJECT_TYPE}}/$PROJECT_TYPE/g" \
        -e "s/{{PROJECT_TITLE}}/$PROJECT_TITLE/g" \
        -e "s/{{PROJECT_DESCRIPTION}}/$PROJECT_DESCRIPTION/g" \
        -e "s/{{PRIMARY_LANGUAGE}}/$PRIMARY_LANGUAGE/g" \
        -e "s/{{LANGUAGE_VERSION}}/$LANGUAGE_VERSION/g" \
        -e "s/{{FRAMEWORK}}/$FRAMEWORK/g" \
        -e "s/{{PROJECT_PREFIX}}/$PROJECT_PREFIX/g" \
        -e "s/{{AUTHOR_NAME}}/$AUTHOR_NAME/g" \
        -e "s/{{AUTHOR_EMAIL}}/$AUTHOR_EMAIL/g" \
        -e "s/{{CREATION_DATE}}/$CREATION_DATE/g" \
        -e "s/{{VERSION}}/$VERSION/g" \
        "$template_file" > "$output_file"
}

# Copy documentation templates
copy_documentation() {
    info "Setting up documentation templates..."
    
    # Core documentation
    process_template "$TEMPLATE_DIR/README.md.template" "README.md"
    process_template "$TEMPLATE_DIR/CLAUDE.md.template" "CLAUDE.md"
    
    # Docs directory
    process_template "$TEMPLATE_DIR/docs/INSTRUCTIONS.md.template" "docs/INSTRUCTIONS.md"
    process_template "$TEMPLATE_DIR/docs/PROJECT.md.template" "docs/PROJECT.md"
    process_template "$TEMPLATE_DIR/docs/WORKFLOW.md.template" "docs/WORKFLOW.md"
    process_template "$TEMPLATE_DIR/docs/TOOLCHAIN.md.template" "docs/TOOLCHAIN.md"
    
    success "Documentation templates configured"
}

# Copy TrackDown system
copy_trackdown() {
    info "Setting up TrackDown task management system..."
    
    # Initialize AI-Trackdown Tools structure
    info "Initializing AI-Trackdown Tools..."
    
    # Create tasks directory structure
    mkdir -p "tasks/"{epics,issues,tasks,prs,templates,scripts}
    
    # Initialize with ai-trackdown-tools
    if command -v aitrackdown &> /dev/null; then
        aitrackdown init "$PROJECT_NAME" --tasks-dir tasks 2>/dev/null || true
    fi
    
    # Copy templates if they exist
    if [ -d "$TEMPLATE_DIR/trackdown/templates" ]; then
        cp -r "$TEMPLATE_DIR/trackdown/templates/"* "tasks/templates/" 2>/dev/null || true
    fi
    
    # Scripts
    if [ -f "$TEMPLATE_DIR/trackdown/scripts/update-progress.py" ]; then
        cp "$TEMPLATE_DIR/trackdown/scripts/update-progress.py" "tasks/scripts/" 2>/dev/null || true
        chmod +x "tasks/scripts/update-progress.py" 2>/dev/null || true
    fi
    
    success "AI-Trackdown Tools system configured"
}

# Create first ticket (handoff)
create_handoff_ticket() {
    info "Creating implementation handoff ticket..."
    
    cat > "tasks/issues/${PROJECT_PREFIX}-000-implementation-handoff.md" << EOF
## **[${PROJECT_PREFIX}-000]** Implementation Handoff - Project Takeover

**Type**: Implementation Handoff  
**Phase**: Pre-Implementation  
**Week**: Week 0 (Preparation)  
**Priority**: Critical  
**Story Points**: 2  
**Assignee**: @new-implementer  
**Status**: Ready  
**Dependencies**: Template setup complete

**Description:**
First task for project coder taking over $PROJECT_TITLE implementation. This ticket guides through the complete project handoff process, environment setup, and readiness validation before beginning Phase 1 implementation.

**Handoff Context:**
- All documentation and planning completed by template system
- Project structure and configuration files ready for development
- Task management system (AI-Trackdown Tools) operational
- Ready for systematic implementation

**Handoff Requirements:**
- [ ] Read and understand all project documentation
- [ ] Set up development environment successfully
- [ ] Validate understanding of technical architecture
- [ ] Confirm development workflow and tools
- [ ] Review implementation roadmap and timeline

**Essential Reading (Priority Order):**
1. **[README.md](../../README.md)** - Project overview and quick start
2. **[docs/INSTRUCTIONS.md](../../docs/INSTRUCTIONS.md)** - Implementation instructions
3. **[docs/PROJECT.md](../../docs/PROJECT.md)** - Business context and specifications
4. **[docs/WORKFLOW.md](../../docs/WORKFLOW.md)** - Development workflow
5. **[docs/TOOLCHAIN.md](../../docs/TOOLCHAIN.md)** - Technology stack

**Environment Setup Checklist:**
- [ ] $PRIMARY_LANGUAGE $LANGUAGE_VERSION installed and verified
- [ ] Git configured for project repository
- [ ] Development environment created
- [ ] Dependencies installed
- [ ] IDE configured with project settings

**Understanding Validation:**
- [ ] Can explain the core project architecture
- [ ] Understands the $PROJECT_TYPE requirements
- [ ] Familiar with $FRAMEWORK integration
- [ ] Comfortable with implementation phases
- [ ] Ready to begin systematic development

**Development Workflow Validation:**
- [ ] Can run initial project setup commands
- [ ] Understands test-driven development approach
- [ ] Familiar with code quality tools
- [ ] Knows how to run test suites
- [ ] Comfortable with git workflow and commit standards

**Implementation Readiness:**
- [ ] Development environment fully functional
- [ ] All documentation read and understood
- [ ] Technical architecture concepts clear
- [ ] Ready to start Phase 1: Core Infrastructure
- [ ] Committed to systematic implementation

**Next Steps After Handoff:**
1. **[${PROJECT_PREFIX}-001]** Set up development environment and package structure
2. **[${PROJECT_PREFIX}-002]** Implement core components
3. Continue with Phase 1 implementation following roadmap

**Success Criteria:**
- [ ] Complete understanding of project scope and architecture
- [ ] Development environment working and validated
- [ ] Confident in implementation approach and timeline
- [ ] Ready to begin systematic implementation

**Definition of Done:**
- [ ] All handoff reading completed and understood
- [ ] Development environment setup and tested
- [ ] Technical concepts validated and confirmed
- [ ] Ready to begin Phase 1 implementation
- [ ] Handoff accepted and documented

---

**Ready for Implementation**: Complete this handoff process before beginning actual implementation work.
EOF
    
    success "Handoff ticket created: ${PROJECT_PREFIX}-000"
}

# Copy project-specific configuration
copy_configuration() {
    info "Setting up project-specific configuration..."
    
    case "$PROJECT_TYPE" in
        python-*)
            cp "$TEMPLATE_DIR/config/python/pyproject.toml.template" "pyproject.toml.template"
            process_template "pyproject.toml.template" "pyproject.toml"
            rm "pyproject.toml.template"
            ;;
        nodejs-*|nextjs-*)
            cp "$TEMPLATE_DIR/config/nodejs/package.json.template" "package.json.template"
            process_template "package.json.template" "package.json"
            rm "package.json.template"
            
            cp "$TEMPLATE_DIR/config/nodejs/tsconfig.json.template" "tsconfig.json"
            cp "$TEMPLATE_DIR/config/nodejs/biome.json.template" "biome.json"
            ;;
    esac
    
    # Common files
    cat > ".gitignore" << EOF
# Dependencies
node_modules/
__pycache__/
*.pyc
.pytest_cache/

# Build outputs
dist/
build/
*.egg-info/

# Development
.env
.env.local
.venv/
venv/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Coverage
coverage/
htmlcov/
.coverage
.nyc_output/

# Temporary
tmp/
temp/
EOF
    
    success "Configuration files created"
}

# Prompt for project details
prompt_for_details() {
    echo -e "${BLUE}Project Setup - $PROJECT_TITLE${NC}"
    echo ""
    
    # Project description
    read -p "Enter project description: " PROJECT_DESCRIPTION
    if [ -z "$PROJECT_DESCRIPTION" ]; then
        PROJECT_DESCRIPTION="A $PROJECT_TYPE project"
    fi
    
    echo ""
    info "Project configuration:"
    echo "  Name: $PROJECT_NAME"
    echo "  Type: $PROJECT_TYPE"
    echo "  Title: $PROJECT_TITLE"
    echo "  Description: $PROJECT_DESCRIPTION"
    echo "  Language: $PRIMARY_LANGUAGE $LANGUAGE_VERSION"
    echo "  Framework: $FRAMEWORK"
    echo "  Author: $AUTHOR_NAME <$AUTHOR_EMAIL>"
    echo ""
    
    read -p "Continue with project creation? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        error_exit "Project creation cancelled"
    fi
}

# Initialize git repository
init_git() {
    info "Initializing git repository..."
    
    git init
    git add .
    git commit -m "feat: initial project setup from template

- Generated $PROJECT_TYPE project structure
- Documentation complete and ready for implementation
- TrackDown task management system configured
- First ticket: ${PROJECT_PREFIX}-000 implementation handoff

🤖 Generated with Claude PM M01-035 Template System"
    
    success "Git repository initialized with initial commit"
}

# Generate summary
generate_summary() {
    echo ""
    echo -e "${GREEN}🎉 Project Created Successfully!${NC}"
    echo ""
    echo -e "${BLUE}Project: $PROJECT_TITLE${NC}"
    echo "Location: $MANAGED_DIR/$PROJECT_NAME"
    echo "Type: $PROJECT_TYPE"
    echo "Language: $PRIMARY_LANGUAGE"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. cd $MANAGED_DIR/$PROJECT_NAME"
    echo "2. Read README.md for project overview"
    echo "3. Complete ${PROJECT_PREFIX}-000 implementation handoff"
    echo "4. Begin systematic implementation"
    echo ""
    echo -e "${YELLOW}Key Files:${NC}"
    echo "  📋 tasks/issues/${PROJECT_PREFIX}-000-implementation-handoff.md - Start here"
    echo "  📖 docs/INSTRUCTIONS.md - Implementation guide"
    echo "  📊 Use 'aitrackdown status' for task tracking"
    echo "  ⚙️  CLAUDE.md - Project configuration"
    echo ""
    echo -e "${YELLOW}Task Management:${NC}"
    echo "  aitrackdown status --stats"
    echo "  aitrackdown epic list"
    echo "  aitrackdown issue list"
    echo "  aitrackdown task list"
    echo ""
    echo -e "${GREEN}Ready for Implementation! 🚀${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Claude PM M01-035 - Managed Project Template System${NC}"
    echo ""
    
    # Validate arguments
    if [ $# -eq 0 ]; then
        usage
    fi
    
    validate_input "$@"
    configure_project_type
    prompt_for_details
    
    # Create project
    create_structure
    copy_documentation
    copy_trackdown
    create_handoff_ticket
    copy_configuration
    init_git
    
    generate_summary
}

# Run main function
main "$@"