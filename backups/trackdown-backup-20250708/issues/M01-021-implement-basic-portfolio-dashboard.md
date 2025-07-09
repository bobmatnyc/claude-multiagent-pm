## **[M01-021]** Implement Basic Portfolio Dashboard Functionality

**Type:** Milestone Task  
**Milestone:** M01_Foundation  
**Epic:** FEP-001 Framework Infrastructure Setup  
**Priority:** High  
**Story Points:** 5  
**Assignee:** @claude  
**Status:** Completed  
**Sprint:** S01  
**Projects Affected:** claude-pm-portfolio-manager

**Description:**
Implement the core dashboard functionality for the Claude PM Portfolio Manager, including data services to read Claude PM project data, functional metric cards, and basic project tracking capabilities. This builds on the completed M01-020 project setup and makes the dashboard operational.

**Milestone Context:**
- Enables real-time monitoring of Claude PM framework operations
- Provides visibility into managed projects status and health
- Critical for achieving framework monitoring capabilities (Level 2)
- Supports S02 objectives for infrastructure deployment tracking

**Acceptance Criteria:**
- [ ] Implement data services to read from Claude-PM repository
- [ ] Create functional metric cards showing real project data
- [ ] Build project list component with basic project information
- [ ] Implement TrackDown ticket integration for basic ticket display
- [ ] Add real-time health monitoring for managed projects
- [ ] Ensure dashboard displays actual Claude PM data, not placeholder values

**Technical Notes:**
- Use existing React structure from M01-020 completion
- Implement services to read from ~/Projects/Claude-PM/trackdown/
- Parse BACKLOG.md and project directories for real data
- Use React Query for data fetching and caching
- Follow existing Tailwind styling patterns

**Cross-Project Dependencies:**
- [ ] Reads from Claude-PM/trackdown/BACKLOG.md
- [ ] Scans ~/Projects/managed/ for project data
- [ ] Integrates with existing TrackDown system
- [ ] Coordinates with framework health monitoring scripts

**Testing Strategy:**
- [ ] Unit tests for data parsing services
- [ ] Component tests for dashboard UI
- [ ] Integration tests with actual Claude-PM data
- [ ] Verify dashboard updates with real project changes

**Definition of Done:**
- [ ] Data services implemented and working with real Claude-PM data
- [ ] Dashboard displays accurate metrics from actual projects
- [ ] Project list shows real managed projects
- [ ] Ticket integration displays actual TrackDown tickets
- [ ] Development server runs without errors
- [ ] All new functionality has appropriate tests
- [ ] Code follows project linting and formatting standards
- [ ] Documentation updated for new dashboard capabilities

**Implementation Tasks:**
1. [ ] Create data services for reading Claude-PM repository data
2. [ ] Implement project scanning for ~/Projects/managed/
3. [ ] Build TrackDown ticket parser for BACKLOG.md
4. [ ] Update Dashboard component with real data integration
5. [ ] Enhance ProjectList component with actual project data
6. [ ] Add error handling and loading states
7. [ ] Implement basic health scoring algorithm
8. [ ] Test dashboard with actual Claude PM framework data