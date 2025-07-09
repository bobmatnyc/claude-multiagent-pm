# Claude PM Framework - Agent Delegation Guide

## 📋 Executive Summary

This guide provides comprehensive instructions for delegating tasks across the Claude PM Framework's multi-agent system. It includes decision trees, responsibility matrices, and escalation protocols to ensure optimal agent coordination.

## 🎯 Quick Reference - Agent Specializations

### Core Production Agents
- **Engineer Agent** - Source code implementation (MULTIPLE allowed)
- **Ops Agent** - Configuration, deployment, push operations (ONE per project)
- **QA Agent** - Testing, validation, quality assurance (ONE per project)
- **Research Agent** - Documentation, best practices (ONE per project)
- **Architect Agent** - Scaffolding, API specifications (ONE per project)

### Specialized Support Agents
- **Security Agent** - Security analysis, compliance (ONE per project)
- **Performance Agent** - Performance optimization, monitoring (ONE per project)
- **Documentation Agent** - Technical writing, user guides (ONE per project)
- **Integration Agent** - System integration, coordination (ONE per project)
- **Code Review Engineer** - Code review processes (MULTIPLE allowed)

## 🔄 Delegation Decision Framework

### 1. Pattern Recognition (Immediate Delegation)

| User Request Pattern | Target Agent | Action Required |
|---------------------|--------------|-----------------|
| "push" or "deploy" | Ops Agent | Comprehensive deployment pipeline |
| "test" or "validate" | QA Agent | Testing coordination |
| "security" or "audit" | Security Agent | Security analysis |
| "performance" or "optimize" | Performance Agent | Performance optimization |
| "document" or "write docs" | Research Agent | Documentation creation |
| "architecture" or "design" | Architect Agent | System design |

### 2. File Type Analysis

| File Pattern | Primary Agent | Secondary Agent | Notes |
|-------------|---------------|-----------------|--------|
| `.js`, `.py`, `.ts` | Engineer | Code Review Engineer | Source code files |
| `.config`, `.env`, `.json` | Ops | Security (if security-related) | Configuration files |
| `.test`, `.spec` | QA | Performance (if performance tests) | Test files |
| `.md`, `.docs` | Research | Documentation | Documentation files |
| `Dockerfile`, `docker-compose` | Ops | - | Deployment files |
| `.yaml`, `.yml` | Context-dependent | - | See decision matrix |

### 3. Complexity Assessment

#### Simple Tasks (Single Agent)
- Direct implementation of defined requirements
- Configuration of known systems
- Standard documentation updates
- Routine testing procedures

#### Complex Tasks (Multi-Agent Coordination)
- Feature development with multiple components
- Performance optimization across systems
- Security implementation with configuration changes
- Integration projects spanning multiple systems

#### Framework-Level Tasks (Orchestrator Coordination)
- Multi-project dependencies
- Framework architecture changes
- Cross-agent protocol updates
- Emergency escalations

### 4. Urgency Evaluation

#### Critical (Emergency Protocol)
- Production outages
- Security breaches
- Framework failures
- **Action**: Multi-agent emergency response team

#### High Priority (Dedicated Agent)
- Time-sensitive features
- Performance degradation
- Security vulnerabilities
- **Action**: Dedicated specialist assignment

#### Normal Priority (Standard Workflow)
- Feature enhancements
- Documentation updates
- Routine maintenance
- **Action**: Queue-based assignment

## 📊 Agent Responsibility Matrix

### Writing Authority Boundaries

| Agent Type | ✅ Exclusive Authority | ❌ Forbidden Activities |
|------------|------------------------|-------------------------|
| **Orchestrator** | Tickets, PM docs, project coordination | Source code, configuration, tests |
| **Engineer** | Source code, business logic, implementation | Configuration, tests, documentation |
| **Ops** | Configuration, deployment, CI/CD | Source code, tests, documentation |
| **QA** | Test files, quality scripts, validation | Source code, configuration, documentation |
| **Research** | Research docs, best practices | Source code, tests, configuration |
| **Architect** | Scaffolding, API specs, system design | Source code implementation, tests |
| **Security** | Security policies, compliance docs | Source code, configuration implementation |
| **Performance** | Performance configs, monitoring | Source code, deployment configs |
| **Documentation** | Technical docs, user guides | Source code, configuration, tests |
| **Integration** | Integration specs, coordination | Source code implementation, configuration |

### Escalation Paths

| Primary Agent | Escalation Trigger | Secondary Agent | Final Escalation |
|---------------|-------------------|-----------------|------------------|
| **Engineer** | Technical blocker >2-3 iterations | Architect | PM → CTO |
| **Ops** | Deployment failure >2-3 attempts | Engineer | PM → CTO |
| **QA** | Quality standards unmet >2-3 iterations | Engineer | PM → CTO |
| **Research** | Research inconclusive >2-3 approaches | Architect | PM → CTO |
| **Architect** | Architectural conflicts >2-3 iterations | Integration | PM → CTO |
| **Security** | Security issue unresolved >2-3 attempts | PM | PM → CTO |
| **Performance** | Performance targets unmet >2-3 attempts | Architect | PM → CTO |
| **Documentation** | Documentation requirements unclear | Research | PM → CTO |
| **Integration** | Integration conflicts >2-3 attempts | Architect | PM → CTO |

## 🚨 Emergency Delegation Protocols

### Critical Infrastructure Issues
1. **Immediate**: Ops Agent takes lead
2. **Support**: Security Agent for security assessment
3. **Backup**: Engineer Agent for code-related issues
4. **Escalation**: PM → CTO if unresolved in 30 minutes

### Security Incidents
1. **Immediate**: Security Agent takes lead
2. **Support**: Ops Agent for configuration fixes
3. **Backup**: Engineer Agent for code vulnerabilities
4. **Escalation**: PM → CTO immediately

### Performance Degradation
1. **Immediate**: Performance Agent takes lead
2. **Support**: Ops Agent for infrastructure analysis
3. **Backup**: Engineer Agent for code optimization
4. **Escalation**: PM → CTO if SLA breach imminent

### Framework Failures
1. **Immediate**: Orchestrator assessment
2. **Support**: All relevant agents mobilized
3. **Backup**: Integration Agent for coordination
4. **Escalation**: PM → CTO → Business Owner

## 🔧 Cross-Agent Communication Protocols

### Standard Communication Format
```yaml
From: [Agent Type]
To: [Target Agent Type]
Priority: [Critical/High/Medium/Low]
Context: [Relevant background information]
Request: [Specific action needed]
Dependencies: [Other agents or resources needed]
Timeline: [Expected completion time]
Escalation: [Conditions for escalation]
```

### Async Communication Patterns
- **Status Updates**: Daily standups via shared ticket system
- **Blocking Issues**: Immediate escalation to PM
- **Knowledge Sharing**: Weekly cross-agent learning sessions
- **Quality Reviews**: Regular cross-agent code/work reviews

### Collaboration Checkpoints
- **Design Phase**: Architect → Engineer → QA → Ops
- **Implementation**: Engineer → QA → Ops → Security
- **Deployment**: Ops → QA → Performance → Documentation
- **Post-Deploy**: Performance → Security → Documentation → Research

## 🛡️ Quality Assurance & Violation Monitoring

### Agent Monitoring Responsibilities
Each agent MUST actively monitor for:
- ✅ **Authority Violations**: Agents writing outside permitted scope
- ✅ **Process Violations**: Skipping required procedures
- ✅ **Quality Violations**: Not meeting established standards
- ✅ **Communication Violations**: Failing to follow protocols

### Immediate Violation Response
1. **Detection**: Agent observes violation
2. **Documentation**: Record specific violation details
3. **Escalation**: Alert PM immediately
4. **Remediation**: Work with PM to resolve
5. **Prevention**: Update procedures to prevent recurrence

### Accountability Standards
- **Proactive Monitoring**: Watch for violations in domain
- **Immediate Reporting**: Report violations when detected
- **Quality Ownership**: Ensure deliverables meet standards
- **Process Compliance**: Follow established procedures
- **Continuous Vigilance**: Monitor framework adherence

## 📈 Performance Metrics & Success Indicators

### Agent Performance Metrics
- **Task Completion Rate**: Percentage of assigned tasks completed successfully
- **Escalation Rate**: Percentage of tasks requiring escalation
- **Quality Score**: Adherence to established quality standards
- **Collaboration Effectiveness**: Success rate of cross-agent coordination
- **Response Time**: Time from assignment to completion

### Framework Performance Indicators
- **Delegation Accuracy**: Percentage of tasks assigned to correct agent
- **Communication Overhead**: Time spent on cross-agent coordination
- **Violation Rate**: Frequency of authority or process violations
- **Emergency Response**: Time to resolve critical issues
- **Agent Utilization**: Efficiency of agent allocation

### Success Targets
- **Delegation Accuracy**: >95%
- **Communication Overhead**: <30% of total time
- **Violation Rate**: <5% of total tasks
- **Emergency Response**: <30 minutes for critical issues
- **Agent Utilization**: >70% productive time

## 🔄 Continuous Improvement Process

### Regular Reviews
- **Daily**: Agent performance and blocking issues
- **Weekly**: Cross-agent collaboration and communication
- **Monthly**: Framework effectiveness and optimization
- **Quarterly**: Agent role definition and responsibility updates

### Feedback Mechanisms
- **Agent Feedback**: Regular agent performance feedback
- **Process Feedback**: Suggestions for process improvements
- **User Feedback**: Stakeholder satisfaction with delegation
- **Framework Feedback**: Overall framework effectiveness

### Adaptation Procedures
- **Issue Identification**: Systematic identification of problems
- **Solution Development**: Collaborative solution development
- **Implementation**: Controlled rollout of improvements
- **Validation**: Measurement of improvement effectiveness

## 📚 Training & Development

### Agent Onboarding
- **Role Definition**: Clear understanding of agent responsibilities
- **Authority Boundaries**: Explicit writing and decision authority
- **Communication Protocols**: Standard communication procedures
- **Escalation Procedures**: When and how to escalate issues

### Skill Development
- **Technical Skills**: Domain-specific technical expertise
- **Communication Skills**: Effective cross-agent communication
- **Problem-Solving**: Systematic approach to issue resolution
- **Quality Standards**: Understanding of framework quality requirements

### Knowledge Management
- **Documentation**: Comprehensive documentation of procedures
- **Best Practices**: Capture and sharing of successful patterns
- **Lessons Learned**: Documentation of failures and improvements
- **Pattern Library**: Repository of proven solutions

---

**Guide Version**: v1.0.0  
**Last Updated**: 2025-07-09  
**Framework Version**: 4.0.0  
**Authority**: Claude PM Framework Orchestrator