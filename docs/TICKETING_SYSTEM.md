# Claude PM Framework Ticketing System

## Overview
The Claude PM Framework uses a sophisticated ticketing system for managing project tasks across multiple milestones and phases. This document explains the system structure, conventions, and processes for AI assistants working with the framework.

## Ticketing Structure

### Ticket ID Format
All tickets follow specific naming conventions:

```
[PREFIX]-[NUMBER]: [Title]
```

### Ticket Prefixes

#### Milestone Tasks (Core Project Work)
- **M01-XXX**: Foundation phase tickets (infrastructure, basic setup)
- **M02-XXX**: Automation phase tickets (workflow systems, multi-agent coordination) 
- **M03-XXX**: Orchestration phase tickets (advanced systems, optimization)

#### Framework Epic Tasks (Cross-Project)
- **FEP-XXX**: Framework Epic tickets spanning multiple milestones
- **CPT-XXX**: Cross-Project Tasks affecting multiple managed projects
- **INT-XXX**: Integration Tasks for service mesh and API connections
- **INF-XXX**: Infrastructure Tasks for deployment, monitoring, security

#### Memory Enhancement Tasks (Claude Max + mem0AI)
- **MEM-XXX**: Core memory integration and enhancement tickets

### Priority Levels
- **CRITICAL**: Must be completed for system to function
- **HIGH**: Important for milestone completion
- **MEDIUM**: Standard feature development
- **LOW**: Nice-to-have enhancements

## Current Active Tickets (42 Total)

### Phase 1: Critical MEM Tickets (6 tickets, 52 story points)
1. **MEM-001**: Core mem0AI Integration Setup (8 points) - CRITICAL
2. **MEM-002**: Memory Schema Design and Implementation (5 points) - HIGH  
3. **MEM-003**: Enhanced Multi-Agent Architecture (13 points) - HIGH
4. **MEM-004**: Memory-Driven Context Management (8 points) - HIGH
5. **MEM-005**: Intelligent Task Decomposition (8 points) - MEDIUM
6. **MEM-006**: Continuous Learning Engine (10 points) - MEDIUM

### M02 Automation Tickets (6 new tickets)
- **M02-009**: Core mem0AI Integration Setup (Links to MEM-001)
- **M02-010**: Enhanced Multi-Agent Architecture Implementation
- **M02-011**: Memory-Driven Context Management System  
- **M02-012**: Parallel Agent Execution Framework
- **M02-013**: Memory-Augmented Agent Capabilities
- **M02-014**: Intelligent Workflow Selection System

### M03 Orchestration Tickets (6 new tickets)
- **M03-007**: Continuous Learning Engine Implementation
- **M03-008**: Pattern Recognition and Success Analysis
- **M03-009**: Team Knowledge Amplification System
- **M03-010**: Memory-Seeded Project Templates
- **M03-011**: Advanced Memory Analytics and Insights
- **M03-012**: Performance Optimization with Memory Metrics

### Framework Epic Tickets (4 new)
- **FEP-007**: Claude Max + mem0AI Enhanced Architecture
- **FEP-008**: Memory-Augmented Agent Ecosystem  
- **FEP-009**: Intelligent Task Decomposition System
- **FEP-010**: Continuous Learning Engine

### Integration Tickets (5 new)
- **INT-006**: mem0AI Service Integration and Configuration
- **INT-007**: Claude Max API Integration and Token Management
- **INT-008**: Memory Schema Design and Implementation
- **INT-009**: Agent Context Preparation System
- **INT-010**: Parallel Agent Coordination Protocol

### Infrastructure Tickets (5 new)
- **INF-006**: Memory Storage and Retrieval Optimization
- **INF-007**: Memory Hygiene and Retention Policies
- **INF-008**: Agent Isolation Infrastructure (Git Worktrees)
- **INF-009**: Memory Analytics and Monitoring Dashboard
- **INF-010**: Backup and Recovery for Memory Systems

## Key Files to Reference

### Primary Documentation
- `/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md` - Complete ticket backlog
- `/Users/masa/Projects/Claude-PM/docs/design/claude-pm-max-mem0.md` - Technical design document
- `/Users/masa/Projects/Claude-PM/trackdown/MILESTONES.md` - Milestone organization

### Project Structure
- `/Users/masa/Projects/Claude-PM/trackdown/` - All ticketing and project management
- `/Users/masa/Projects/Claude-PM/framework/` - Core framework implementation
- `/Users/masa/Projects/managed/` - Individual managed projects

## Implementation Strategy

### Phase 1 (Current Priority)
Focus on the 6 critical MEM-XXX tickets (52 story points total):
1. Establish core mem0AI integration with OpenAI API
2. Design memory schema for projects, patterns, teams, and errors  
3. Implement 10-agent ecosystem with memory augmentation
4. Create parallel execution framework (max 5 concurrent agents)
5. Build intelligent task decomposition using memory patterns
6. Deploy continuous learning engine for pattern recognition

### Dependencies
- mem0ai service running on port 8002
- OpenAI API access for Claude Max unlimited tokens
- Git worktree infrastructure for agent isolation

## Working with the Ticketing System

### IMPORTANT: "Backlog" vs "Todo List"
When users ask about the "backlog", they mean the **Claude PM Framework backlog** located at:
```
/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md
```

This is NOT the same as Claude Code's todo list tool. The framework backlog contains 42 active tickets for the Claude Max + mem0AI enhancement project.

### For AI Assistants
1. **Always check BACKLOG.md first** - Contains complete current state
2. **Reference ticket IDs correctly** - Use exact format [PREFIX-NUMBER]  
3. **Update ticket status** - Track progress through completion
4. **Link related tickets** - Many tickets have dependencies
5. **Follow priority order** - CRITICAL tickets must be completed first

### Quick Commands for Backlog Review
```bash
# View current sprint status
grep -A20 "## 🎯 Current Sprint" /Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md

# View priority tickets (Phase 1)
grep -A50 "## 🚀 Priority Implementation Tickets" /Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md

# View all MEM tickets
grep "MEM-" /Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md
```

### Ticket Status Tracking
- **[ ]** Pending/Not Started
- **[x]** Completed 
- **🔄** In Progress (use when actively working)
- **🚫** Blocked (with blocker explanation)

### Story Points System
- 1-3 points: Simple tasks (few hours)
- 5-8 points: Standard tasks (1-2 days) 
- 10-13 points: Complex tasks (3-5 days)
- 20+ points: Epic tasks (break down further)

## Integration with mem0AI Enhancement

The ticketing system now incorporates memory-driven development where:
- Past successful decompositions inform new ticket creation
- Memory patterns guide estimation accuracy
- Continuous learning improves future planning
- Cross-project knowledge amplifies team effectiveness

This transform Claude PM from basic orchestration into an **intelligent learning system** that improves with every completed ticket.

## Repository Location
https://github.com/bobmatnyc/claude-pm

All 42 tickets have been committed and are ready for implementation.