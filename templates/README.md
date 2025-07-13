# Claude PM Templates

Templates and guidance for systematic project planning and implementation.

## Available Templates

### 📋 Research Design Document
**File**: `research-design-doc.md`
**Purpose**: Structured planning template for complex, multi-phase projects
**Use When**: Cross-system integration, architectural changes, performance-critical work, team coordination
**Example**: `example-research-doc.md` - Real-time chat feature implementation planning

### 📖 Planning Guides

#### Decision Framework
**File**: `when-to-use-research-docs.md`
**Purpose**: Quick guide to determine when research docs are needed vs. direct implementation

#### Workflow Integration
**File**: `research-workflow-integration.md`
**Purpose**: How research design docs integrate with claude-pm commands and workflow

### 🏗️ Project Templates
**File**: `basic-project.json`
**Purpose**: Basic project configuration template

## Quick Start

### For Complex Projects
```bash
# Copy research template
cp ~/.claude-pm/templates/research-design-doc.md ./docs/design/my-feature.md

# Plan with AI assistance
claude-pm plan research-doc my-feature
```

### For Simple Projects
```bash
# Direct implementation
claude-pm push  # AI handles simple changes directly
```

## Template Philosophy

**Research First**: For complex changes that affect multiple systems, require team coordination, or have high risk/impact.

**Implementation First**: For simple bug fixes, small features, and straightforward refactoring where the approach is obvious.

The goal is to use the right level of planning for each type of work - systematic analysis for complex projects, efficient execution for simple tasks.