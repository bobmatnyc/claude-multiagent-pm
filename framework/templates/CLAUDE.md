# Claude Multi-Agent PM Configuration - {PROJECT_NAME}

This file provides guidance to Claude Code (claude.ai/code) when working with the {PROJECT_NAME} project within the Claude Multi-Agent PM framework.

## 🧠 MANDATORY BEHAVIORAL CHECKLIST

**INTERNALIZE THESE RESPONSES - CLAUDE MULTI-AGENT PM FRAMEWORK:**

□ **Task management = Claude Multi-Agent PM TrackDown** (`~/Projects/claude-multiagent-pm/trackdown/BACKLOG.md`)
□ **Framework questions = Claude Multi-Agent PM** (`~/Projects/claude-multiagent-pm/framework/CLAUDE.md`)
□ **Workflow questions = /docs/WORKFLOW.md**
□ **Project specs = /docs/PROJECT.md**
□ **Technical details = /docs/TOOLCHAIN.md**

### 🎯 IMMEDIATE RESPONSE PATTERNS

When user asks:
- "What's on the backlog?" → "Check `~/Projects/claude-multiagent-pm/trackdown/BACKLOG.md` for current tasks"
- "What tasks remain?" → "Check `~/Projects/claude-multiagent-pm/trackdown/` directory for remaining work"  
- "What's the workflow?" → "See /docs/WORKFLOW.md for workflow processes"

### ❌ COMMON ERRORS TO AVOID

**DO NOT:**
- ❌ Search local trackdown/ for framework tasks (use Claude-PM repo)
- ❌ Mix project-specific with framework tasks
- ❌ Work on projects without referencing Claude PM ticket numbers
- ❌ Make framework changes without proper tickets

**DO:**
- ✅ Always reference Claude PM TrackDown tickets (M01-XXX format)
- ✅ Use local docs/ for project-specific information
- ✅ Link commits to Claude PM tickets: "closes M01-XXX"

## Required Documentation

Before starting any work, review these documentation files:

1. **`/docs/PROJECT.md`** - Complete project overview, architecture, current status, and all project-specific information
2. **`/docs/TOOLCHAIN.md`** - Technical development tools, standards, and configuration
3. **`/docs/WORKFLOW.md`** - Development processes, methodologies, and TrackDown integration
4. **`/docs/INSTRUCTIONS.md`** - AI-specific prompts and behavioral instructions

All project-specific information, including commands, configuration, and implementation details, can be found in `/docs/PROJECT.md`.

## Project Context & Conventions

### Development Environment
{DEVELOPMENT_ENVIRONMENT_SPECIFICS}

### Project Structure
```
{PROJECT_STRUCTURE}
```

### Testing & Validation
{TESTING_COMMANDS}

### TrackDown Integration
- **CRITICAL**: All work must be done in TrackDown tasks with proper branching
- Branch naming: `task/{ticket-id}-{description}` or `epic/{epic-name}`
- Always link development work to TrackDown tickets
- Use epic/subticket workflow for complex documentation projects

### Post-Task Verification
Always run these commands after making changes:
```bash
{POST_TASK_COMMANDS}
```

## Important Notes

- **Documentation First**: Always consult PROJECT.md for project-specific guidance
- **Code as Truth**: When documentation conflicts with source code, assume code is correct
- **Task Linkage**: All todos and work must be linked to TrackDown tickets
- **Two-Click Rule**: All daily-use information must be accessible within 2 clicks from main docs