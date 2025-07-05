# Claude PM - Master Framework Configuration

## 🧠 MANDATORY BEHAVIORAL CHECKLIST

**INTERNALIZE THESE RESPONSES - CRITICAL FOR ALL CLAUDE PM WORK:**

□ **ALL TASKS REQUIRE TICKETS** - Every change needs a TrackDown ticket in Claude-PM repo
□ **Task tracking = Claude-PM/trackdown/** - NOT individual project repos
□ **Framework questions = Claude-PM/docs/**
□ **Cross-project coordination = Claude-PM/integration/**

### 🎯 IMMEDIATE RESPONSE PATTERNS

When user asks:
- "What's on the backlog?" → "Check `Claude-PM/trackdown/BACKLOG.md` for current tasks"
- "What tasks remain?" → "Check `Claude-PM/trackdown/` directory for remaining work"  
- "What's the framework status?" → "Run `Claude-PM/trackdown/scripts/health-check.sh`"
- "How do I create a task?" → "Use templates in `Claude-PM/trackdown/templates/`"

### ❌ CRITICAL ERRORS TO AVOID

**DO NOT:**
- ❌ Create tasks without TrackDown tickets
- ❌ Mix PM tracking with project code repos
- ❌ Work on projects without referencing ticket numbers
- ❌ Make framework changes without proper tickets

**DO:**
- ✅ Always create tickets before starting work
- ✅ Reference ticket numbers in all project commits
- ✅ Keep PM tracking in dedicated Claude-PM repository
- ✅ Use milestone prefixes: M01-XXX, M02-XXX, FEP-XXX

## Project Management Architecture

### Repository Structure
```
~/Projects/Claude-PM/        # THIS repository - all PM activities
├── trackdown/               # TrackDown project management
├── framework/               # Framework configuration  
├── integration/             # Cross-project coordination
└── docs/                    # Framework documentation

~/Projects/[project-name]/   # Individual project repositories
├── CLAUDE.md               # Project-specific config (references PM repo)
├── code files...           # Project code only
└── git commits reference   # PM tickets: "closes M01-007"
```

## Mandatory Ticket System

### EVERY task requires a ticket:
- **Milestone Tasks**: M01-XXX, M02-XXX, M03-XXX
- **Framework Epics**: FEP-XXX (cross-project initiatives)
- **Integration Tasks**: INT-XXX (cross-project coordination)
- **Infrastructure**: INF-XXX (framework infrastructure)

### Workflow:
1. Create ticket in `Claude-PM/trackdown/BACKLOG.md`
2. Work on task in individual project repo
3. Reference ticket in commits: `git commit -m "feat: implement X - closes M01-007"`
4. Update ticket status in Claude-PM repo
5. Commit PM updates: `git commit -m "chore: update M01-007 status"`

## Framework Integration Points

### Health Monitoring
- Run `Claude-PM/trackdown/scripts/health-check.sh` for framework status
- Scans all projects in `~/Projects/` for health indicators
- Updates `Claude-PM/integration/project-mapping.json`

### Custom Slash Commands
- `/pm:daily-standup` - Morning framework status and planning
- `/pm:health-check` - Run framework health monitoring
- `/pm:create-ticket` - Create new TrackDown ticket
- `/pm:milestone-progress` - Show milestone progress

### Cross-Project Coordination
- All projects reference this framework configuration
- Standardized CLAUDE.md templates deployed to projects
- Dependency tracking through integration scripts

## Development Guidelines

### Before Starting ANY Work:
1. **Check for existing ticket** in Claude-PM/trackdown/BACKLOG.md
2. **Create ticket if none exists** using appropriate template
3. **Reference ticket** in all project work
4. **Update ticket status** as work progresses

### Project-Specific Work:
- Work happens in individual project repositories
- Follow project-specific CLAUDE.md instructions
- Always reference PM tickets in commit messages
- PM updates happen in Claude-PM repository

### Framework Updates:
- All framework changes tracked as tickets
- Templates and configurations managed in Claude-PM repo
- Health monitoring and cross-project scripts centralized

## Success Metrics

### Target Metrics (from M01 Foundation):
- 60%+ productivity improvement over baseline
- <30 minute project setup time
- 70% context switching reduction
- 90%+ task completion rate

### Framework Maturity Levels:
- **Level 1**: Basic structure ✅ 
- **Level 2**: Automated workflows (M01 target)
- **Level 3**: Orchestrated systems (M02 target)
- **Level 4**: Optimized ecosystem (M03 target)

## Quick Reference

### Daily Workflow:
```bash
# Navigate to PM repository
cd ~/Projects/Claude-PM

# Check framework health
./trackdown/scripts/health-check.sh

# Update task status in BACKLOG.md
# Commit PM changes
git add . && git commit -m "chore: update task status"
git push

# Work in individual project
cd ~/Projects/[project-name]
# Make changes, reference tickets in commits
git commit -m "feat: implement feature - closes M01-007"
```

### Emergency Procedures:
- Critical issues get immediate tickets with CRITICAL priority
- Framework health failures trigger immediate investigation
- Cross-project dependency failures escalated to framework team

---

**Repository**: ~/Projects/Claude-PM/
**Framework Version**: v1.0.0-alpha
**Last Updated**: 2025-07-05