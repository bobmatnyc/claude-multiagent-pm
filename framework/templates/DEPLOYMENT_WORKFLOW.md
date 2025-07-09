# Standardized Deployment Workflow Template

## 🎯 Overview
This is the standardized 5-step deployment workflow that all managed projects must follow. It ensures consistent deployment practices with browser auto-launch and QA screenshot verification.

## 📋 Standard Deployment Workflow

### Step 1: Ops Agent - Local Server Deployment + Health Check
**Agent**: Ops Agent  
**Responsibility**: Deploy application and verify health

**Tasks**:
- [ ] Deploy application to local development environment
- [ ] Verify server is running and healthy
- [ ] Confirm all services are operational
- [ ] Validate configuration and dependencies
- [ ] Record deployment timestamp and details

**Success Criteria**:
- Server responds to health check endpoints
- Application starts without errors
- All required services are running
- No configuration or dependency issues

### Step 2: Ops Agent - Automatic Browser Launch
**Agent**: Ops Agent  
**Responsibility**: Launch browser to deployed application

**Tasks**:
- [ ] Execute standard browser launch command: `open -a "Microsoft Edge" [URL]`
- [ ] Verify browser launches successfully
- [ ] Confirm application loads in browser
- [ ] Notify QA Agent of browser launch
- [ ] Provide deployment URL to QA Agent

**Success Criteria**:
- Browser launches without errors
- Application loads in browser
- QA Agent receives notification and URL
- No browser compatibility issues

### Step 3: QA Agent - Screenshot Capture + Visual Verification
**Agent**: QA Agent  
**Responsibility**: Capture screenshots and verify deployment

**Tasks**:
- [ ] Take full-page screenshot of deployed application
- [ ] Verify application loads without errors
- [ ] Check main interface displays correctly
- [ ] Validate navigation elements are visible
- [ ] Test basic functionality (if applicable)
- [ ] Document any issues found

**Success Criteria**:
- Screenshot captured successfully
- Application displays correctly
- No obvious UI/UX issues
- Basic functionality works as expected
- Performance appears normal

### Step 4: QA Agent - Deployment Success Documentation
**Agent**: QA Agent  
**Responsibility**: Document verification results

**Tasks**:
- [ ] Save screenshot evidence with timestamp
- [ ] Create deployment verification report
- [ ] Document what was verified and results
- [ ] Report any issues found to Ops Agent
- [ ] Confirm deployment ready for development team

**Success Criteria**:
- Screenshot evidence saved
- Verification report completed
- Issues properly documented
- Clear handoff status provided

### Step 5: Framework - Handoff to Development Agents
**Agent**: Framework Orchestrator  
**Responsibility**: Coordinate handoff to development team

**Tasks**:
- [ ] Confirm deployment verification completion
- [ ] Review screenshot evidence and verification report
- [ ] Coordinate handoff to appropriate development agents
- [ ] Update project status and deployment records
- [ ] Notify stakeholders of deployment success

**Success Criteria**:
- Deployment verification confirmed
- Evidence reviewed and approved
- Development team notified
- Project status updated

## 🔄 Workflow Integration Points

### Ops Agent → QA Agent Handoff
- **Trigger**: Successful browser launch
- **Information**: Deployment URL, environment context, timestamp
- **Coordination**: Direct notification to QA Agent
- **Verification**: QA Agent acknowledges receipt

### QA Agent → Framework Handoff
- **Trigger**: Completed screenshot verification
- **Information**: Screenshot evidence, verification report, status
- **Coordination**: Status update to Framework Orchestrator
- **Verification**: Framework confirms handoff completion

## 📊 Quality Standards

### Deployment Health Requirements
- [ ] Server responds to health checks
- [ ] Application starts without errors
- [ ] All services operational
- [ ] No configuration issues

### Browser Launch Requirements
- [ ] Browser launches successfully
- [ ] Application loads in browser
- [ ] No compatibility issues
- [ ] QA Agent properly notified

### Screenshot Verification Requirements
- [ ] Full-page screenshot captured
- [ ] Application displays correctly
- [ ] No UI/UX issues present
- [ ] Basic functionality verified

### Documentation Requirements
- [ ] Screenshot evidence saved
- [ ] Verification report completed
- [ ] Issues properly documented
- [ ] Clear handoff status provided

## 🚨 Issue Escalation

### Deployment Issues
- **Who**: Ops Agent
- **When**: Server health check fails, browser launch fails
- **Action**: Report to Framework Orchestrator immediately
- **Information**: Error details, environment context, attempted fixes

### Visual Verification Issues
- **Who**: QA Agent
- **When**: Screenshot shows errors, UI issues, functionality problems
- **Action**: Report to Ops Agent and Framework Orchestrator
- **Information**: Screenshot evidence, issue description, severity assessment

### Coordination Issues
- **Who**: Any agent
- **When**: Handoff fails, communication breakdown, workflow blocked
- **Action**: Escalate to Framework Orchestrator
- **Information**: Workflow step, agents involved, blocking issue

## 📈 Success Metrics

### Deployment Efficiency
- Time from deployment start to browser launch
- Browser launch success rate
- Screenshot verification completion rate
- Overall workflow completion time

### Quality Metrics
- Deployment success rate (no issues found)
- Visual verification accuracy
- Issue detection rate
- Documentation completeness

### Coordination Metrics
- Handoff success rate
- Communication effectiveness
- Workflow adherence
- Stakeholder satisfaction

## 🔧 Template Usage

### For New Projects
1. Copy this template to project deployment documentation
2. Customize URLs and project-specific requirements
3. Train agents on workflow expectations
4. Establish monitoring and metrics collection

### For Existing Projects
1. Review current deployment practices
2. Identify gaps compared to standard workflow
3. Implement missing steps gradually
4. Update agent instructions and documentation

---

**Template Version**: v1.0.0  
**Last Updated**: 2025-07-08  
**Framework**: Claude PM Multi-Agent Framework  
**Scope**: All managed projects