# AI Trackdown CLI v1.0.1

A professional CLI tool for AI-first project management with hierarchical Epic→Issue→Task workflows, comprehensive Pull Request management, token tracking, and YAML frontmatter support.

## What's New in v1.0.1

🚀 **Anywhere-Submit Functionality**: Execute commands from anywhere with `--project-dir` for seamless multi-project workflows  
🚀 **Enhanced Template System**: Bundled default templates with robust fallback mechanisms  
🚀 **Performance Optimizations**: 90%+ faster operations with intelligent indexing system  
🚀 **Fixed Directory Structure**: Unified path resolution and improved configuration management  
🚀 **Enhanced Help System**: Comprehensive help documentation and error handling  

## Features

✅ **Anywhere-Submit Capability**: Work with any project from anywhere using `--project-dir`  
✅ **AI-First Design**: Built for AI collaboration with context generation and token tracking  
✅ **Hierarchical Structure**: Epic → Issue → Task relationships with YAML frontmatter  
✅ **Complete PR Management**: 12 comprehensive PR commands with GitHub-independent workflows  
✅ **Agent-Optimized**: Batch operations and intelligent automation for AI-driven development  
✅ **Token Management**: Comprehensive token tracking and budget alerts  
✅ **AI Context Generation**: Automatic llms.txt generation for AI workflows  
✅ **Enhanced Template System**: Bundled defaults with project-specific overrides  
✅ **Performance Optimized**: <10ms response times with intelligent indexing  
✅ **Git-Native**: Local file-based storage with git integration  

## Installation

```bash
npm install -g ai-trackdown-tools
```

## Quick Start

```bash
# Initialize a new ai-trackdown project
aitrackdown init --framework ai-trackdown

# Create an epic
aitrackdown epic create "User Authentication System" --priority high

# Create an issue under the epic
aitrackdown issue create "Login Flow Implementation" --epic EP-0001

# Create a task under the issue
aitrackdown task create "JWT Token Validation" --issue ISS-0001

# Check project status
aitrackdown status

# Generate AI context file
aitrackdown ai generate-llms-txt
```

## Anywhere-Submit Functionality (v3.0.0)

Work with any project from anywhere using the `--project-dir` option:

```bash
# Execute commands from anywhere by specifying the project directory
aitrackdown --project-dir /path/to/project status
aitrackdown --project-dir /path/to/project epic create "New Epic"
aitrackdown --project-dir /path/to/project issue list --status active

# Useful for CI/CD pipelines and automated workflows
aitrackdown --project-dir $PROJECT_PATH pr create "Automated PR"

# Multi-project management from a single location
aitrackdown --project-dir ~/projects/app1 status
aitrackdown --project-dir ~/projects/app2 status
```

## AI-First Workflow

The CLI supports comprehensive AI development workflows with enhanced performance:

```bash
# Epic Management (< 50ms response time)
aitrackdown epic list
aitrackdown epic show EP-0001 --show-issues --show-tasks
aitrackdown epic complete EP-0001 --actual-tokens 1500

# Issue Management with anywhere-submit
aitrackdown --project-dir /path/to/project issue assign ISS-0001 developer
aitrackdown issue complete ISS-0001 --auto-complete-tasks

# Task Management with Token Tracking
aitrackdown task complete TSK-0001 --tokens 250
aitrackdown task list

# AI Features with Enhanced Performance
aitrackdown ai track-tokens --report --format table
aitrackdown ai context --item-id EP-0001 --add "requirements context"
```

## Pull Request Management

Comprehensive PR management with 12 powerful commands and enhanced performance:

```bash
# Create PR from completed tasks with anywhere-submit
aitrackdown --project-dir /path/to/project pr create "Implement user authentication" --issue ISS-0001 --from-tasks TSK-0001,TSK-0002

# List and filter PRs (< 100ms response time)
aitrackdown pr list --pr-status open --assignee @developer --priority high
aitrackdown pr list --format table --show-details

# Review and approve PRs with enhanced templates
aitrackdown pr review PR-0001 --approve --comments "LGTM! Great implementation"
aitrackdown pr approve PR-0001 --auto-merge --merge-strategy squash

# Batch operations for multiple PRs (< 1s for 10 PRs)
aitrackdown pr batch --operation approve --filter pr-status:open --filter assignee:@team
aitrackdown pr batch --operation merge --filter pr-status:approved --merge-strategy squash

# Advanced PR management with anywhere-submit
aitrackdown --project-dir /path/to/project pr dependencies PR-0001 --add-dependency PR-0002
aitrackdown pr sync --github --repo owner/repo --update-status
aitrackdown pr archive --status merged --older-than 6months
```

### PR Features

- **GitHub-Independent**: Complete PR lifecycle without external dependencies
- **File-based Storage**: PRs stored as markdown files with YAML frontmatter
- **Status-based Organization**: Automatic file movement (draft → open → review → approved → merged)
- **Enhanced Template System**: Bundled templates with fallback mechanisms
- **Batch Operations**: Efficient bulk operations for agent-driven workflows
- **Review System**: Structured reviews with approval tracking
- **Performance Optimized**: <100ms average response times with intelligent indexing
- **Anywhere-Submit**: Execute PR commands from any location with --project-dir

## Performance Improvements (v3.0.0)

### Intelligent Indexing System
- **90%+ Performance Improvement**: Operations that took 2-5 seconds now complete in <10ms
- **Automatic Index Management**: `.ai-trackdown-index` file provides instant lookups
- **Memory Efficient**: <5MB memory usage even for large projects (1000+ items)
- **Real-time Updates**: Index automatically updates when files change

### Performance Benchmarks
- **Status Command**: <10ms (was 2-5 seconds)
- **Epic List**: <50ms (was 3-8 seconds)
- **PR Operations**: <100ms average response time
- **Search Operations**: Instant hash-based lookups

### Template System Enhancements
- **Bundled Templates**: Default templates included with CLI installation
- **Robust Fallbacks**: Automatic fallback to bundled templates when project templates missing
- **Multiple Path Resolution**: Works across different build structures and deployment methods

## Project Structure

ai-trackdown creates a hierarchical project structure:

```
project/
├── .ai-trackdown/
│   ├── config.yaml              # Project configuration
│   ├── templates/               # YAML frontmatter templates
│   └── cache/                   # Local cache files
├── tasks/                       # Unified directory structure (v3.0.0)
│   ├── .ai-trackdown-index      # Performance indexing system (v3.0.0)
│   ├── epics/
│   │   └── EP-0001-feature-name.md  # Epic with YAML frontmatter
│   ├── issues/
│   │   └── ISS-0001-issue-name.md   # Issues linked to epics
│   ├── tasks/
│   │   └── TSK-0001-task-name.md    # Tasks linked to issues
│   ├── prs/                     # Pull Request management (v2.0.0)
│   │   ├── draft/               # Draft PRs
│   │   ├── active/
│   │   │   ├── open/            # Open PRs ready for review
│   │   │   ├── review/          # PRs under review
│   │   │   └── approved/        # Approved PRs ready to merge
│   │   ├── merged/              # Successfully merged PRs
│   │   ├── closed/              # Closed/rejected PRs
│   │   ├── reviews/             # PR review files
│   │   └── logs/                # Operation logs
│   └── templates/               # Project-specific templates
│       ├── pr-review-default.yaml   # Default PR review template
│       ├── pr-review-quick.yaml     # Quick PR review template
│       └── pr-review-security.yaml  # Security PR review template
└── llms.txt                     # Generated AI context
```

## YAML Frontmatter

All items use structured YAML frontmatter for metadata:

```yaml
---
epic_id: EP-0001
title: User Authentication System
status: active
priority: high
assignee: developer
estimated_tokens: 2000
actual_tokens: 1500
ai_context: [authentication, security, user-management]
related_issues: [ISS-0001, ISS-0002]
---

# Epic Description
Comprehensive user authentication system with JWT tokens...
```

## Migration from Legacy Systems

Convert existing projects to ai-trackdown format:

```bash
# Migrate from old trackdown structure
aitrackdown migrate --from-trackdown ./old-project

# Import from various formats
aitrackdown migrate --from-json project-data.json
aitrackdown migrate --from-csv tasks.csv
```

## Command Reference

### Epic Commands
- `epic create` - Create new epic with YAML frontmatter
- `epic list` - List epics  
- `epic show` - Show detailed epic with `--show-issues` and `--show-tasks` options
- `epic update` - Update epic fields and metadata
- `epic complete` - Mark epic complete with token tracking

### Issue Commands  
- `issue create` - Create issue linked to epic
- `issue assign` - Assign issue to team member
- `issue complete` - Complete issue with auto-task completion
- `issue list` - List issues (basic listing)
- `issue show` - Show detailed issue information

### Task Commands
- `task create` - Create task linked to issue
- `task complete` - Complete task with time/token tracking
- `task list` - List tasks (basic listing)
- `task update` - Update task status and metadata

### Pull Request Commands (v2.0.0+)
- `pr create` - Create PR from templates with auto-linking
- `pr list` - List PRs with advanced filtering (`--pr-status`, `--assignee`, `--priority`, `--epic`, etc.)
- `pr show` - Show detailed PR with relationships
- `pr update` - Update PR properties and metadata
- `pr review` - Create structured PR reviews
- `pr approve` - Approve PR with optional auto-merge
- `pr merge` - Merge PR with strategy selection
- `pr close` - Close PR without merging
- `pr batch` - Perform bulk operations on multiple PRs
- `pr dependencies` - Manage PR dependencies
- `pr sync` - Synchronize with external systems
- `pr archive` - Archive old PRs with compression

### AI Commands
- `ai generate-llms-txt` - Generate AI context file
- `ai track-tokens` - Track and report token usage
- `ai context` - Manage AI context for items

### Project Commands
- `init` - Initialize new ai-trackdown project
- `status` - Show project overview with metrics (< 10ms with indexing)
- `export` - Export project data in various formats

## v3.0.0 Changelog

### Major Enhancements

#### Anywhere-Submit Functionality
- **Global Project Access**: Execute commands from any location using `--project-dir`
- **CI/CD Integration**: Perfect for automated workflows and build systems
- **Multi-Project Management**: Manage multiple projects from a single location

#### Performance Revolution
- **90%+ Speed Improvement**: Intelligent indexing system (.ai-trackdown-index)
- **Sub-10ms Operations**: Status and listing commands complete in <10ms
- **Memory Efficient**: <5MB memory usage for large projects
- **Real-time Updates**: Index automatically maintains itself

#### Enhanced Template System
- **Bundled Templates**: Default templates included with CLI installation
- **Robust Fallbacks**: Automatic fallback when project templates missing
- **Multiple Path Resolution**: Works across different build structures
- **Zero Configuration**: Works out-of-the-box without setup

#### Directory Structure Improvements
- **Unified Path Resolution**: Consistent path handling across all commands
- **Configurable Root**: Use `--root-dir` or `--tasks-dir` for custom layouts
- **Legacy Compatibility**: Seamless migration from older structures

### Bug Fixes
- Fixed template loading issues in different deployment scenarios
- Resolved path resolution conflicts in distributed environments
- Improved error handling and user feedback
- Fixed CLI option parsing inconsistencies

### Migration Notes
- All existing projects continue to work without changes
- New projects automatically get performance optimizations
- Legacy projects benefit from performance improvements immediately
- No breaking changes to existing command syntax

