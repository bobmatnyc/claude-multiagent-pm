# Custom Agent Development Guide

## Overview

The Claude Multi-Agent PM Framework (CMPM) provides a powerful and flexible system for creating custom agents that can integrate seamlessly with the existing 11-agent ecosystem. This guide covers everything from basic agent architecture to advanced deployment patterns.

## Agent Development Fundamentals

### Agent Architecture Overview

The CMPM framework uses a multi-layered agent architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│  Multi-Agent Orchestrator (Coordination Layer)             │
├─────────────────────────────────────────────────────────────┤
│  Standard Agents        │  User-Defined Agents             │
│  - architect           │  - code_organizer                │
│  - engineer            │  - domain_specific_*              │
│  - qa                  │  - security_*                     │
│  - researcher          │  - performance_*                  │
│  - security_engineer   │  - custom_*                       │
│  - performance_engineer│                                   │
│  - devops_engineer     │                                   │
│  - data_engineer       │                                   │
│  - ui_ux_engineer      │                                   │
│  - code_review_engineer│                                   │
│  - integration         │                                   │
│  - documentation       │                                   │
├─────────────────────────────────────────────────────────────┤
│  Memory Integration Layer (mem0AI)                         │
├─────────────────────────────────────────────────────────────┤
│  Enforcement Engine (Delegation Constraints)               │
└─────────────────────────────────────────────────────────────┘
```

### Agent Lifecycle

Every agent follows a standard lifecycle:

1. **Registration**: Agent defined in `framework/agent-roles/agents.json`
2. **Initialization**: Agent context and memory prepared
3. **Validation**: Enforcement engine validates permissions
4. **Execution**: Agent performs delegated tasks
5. **Memory Storage**: Results stored in memory system
6. **Cleanup**: Resources released and status updated

### Agent Design Patterns

#### 1. Inheritance Pattern
Custom agents inherit from existing base agents:

```python
class CustomSecurityAgent(SecurityAgent):
    def __init__(self, specialization="penetration_testing"):
        super().__init__()
        self.specialization = specialization
        self.domain_focus = "security_audit"
```

#### 2. Composition Pattern
Agents combine multiple capabilities:

```python
class CustomIntegrationAgent:
    def __init__(self):
        self.api_handler = APIHandler()
        self.data_processor = DataProcessor()
        self.security_validator = SecurityValidator()
```

#### 3. Delegation Pattern
Agents delegate specialized tasks:

```python
class CustomOrchestratorAgent:
    async def delegate_task(self, task_type, context):
        if task_type == "security_audit":
            return await self.security_agent.execute(context)
        elif task_type == "performance_test":
            return await self.performance_agent.execute(context)
```

## Creating Custom Agents

### User-Defined Agent System

The CMPM v4.2.0 framework introduces a powerful user-defined agent system that allows you to create and manage custom agents in your user configuration directory.

#### Agent Directory Structure

```
~/.claude-multiagent-pm/
├── agents/
│   ├── user-defined/                    # Custom agent definitions
│   │   ├── my-custom-agent.md           # Agent definition file
│   │   ├── domain-expert-agent.md       # Domain-specific agent
│   │   └── security-specialist.md       # Security-focused agent
│   └── training-modifications/          # Agent training improvements
│       ├── engineer-improvements.md     # Engineer agent enhancements
│       └── qa-enhancements.md          # QA agent improvements
├── config/
│   └── config.yaml                     # Main configuration
└── templates/
    └── agent-template.md               # Agent template
```

#### Creating a User-Defined Agent

1. **Create Agent Definition File**:
   ```bash
   # Create new agent in user-defined directory
   mkdir -p ~/.claude-multiagent-pm/agents/user-defined
   touch ~/.claude-multiagent-pm/agents/user-defined/my-custom-agent.md
   ```

2. **Register Agent in Configuration**:
   ```yaml
   # ~/.claude-multiagent-pm/config/config.yaml
   user_defined_agents:
     - name: "my-custom-agent"
       path: "~/.claude-multiagent-pm/agents/user-defined/my-custom-agent.md"
       enabled: true
       specialization: "domain-specific"
   ```

3. **Agent Auto-Loading**:
   The framework automatically loads user-defined agents at startup, making them available for orchestration alongside standard agents.

### Step 1: Agent Template Structure

Create a new agent using the standard template:

```markdown
# Custom Agent Name

## 🎯 Primary Role
**Brief description of the agent's primary function**

## 🔑 Authority & Permissions

### ✅ EXCLUSIVE Permissions
- List specific permissions this agent has
- File types it can write/read
- Services it can access

### ❌ FORBIDDEN Activities
- Activities this agent cannot perform
- Constraints it must respect

## 📋 Core Responsibilities

### 1. Primary Function
- Main responsibility description
- Key activities and tasks

### 2. Secondary Functions
- Supporting responsibilities
- Integration points with other agents

## 🔄 Workflow Integration

### Input from PM
```yaml
Context:
  - Expected input format
  - Required context information
  
Task:
  - Task assignment format
  - Specific requirements
```

### Output to PM
```yaml
Status:
  - Progress reporting format
  - Success/failure indicators
  
Results:
  - Output format
  - Deliverable specifications
```

## 🚨 Escalation Triggers

### Immediate PM Alert Required
- Conditions requiring immediate escalation
- Failure scenarios

### Context Needed from Other Agents
- Dependencies on other agents
- Required coordination points

## 📊 Success Metrics
- Key performance indicators
- Quality standards
- Measurement criteria

## 🧠 Learning Capture
- Knowledge patterns to capture
- Experience sharing protocols
```

### Step 2: Agent Configuration Schema

Define your agent in `framework/agent-roles/agents.json`:

```json
{
  "agent_registry": {
    "version": "1.0.0",
    "user_defined_agents": {
      "custom_security_auditor": {
        "name": "Custom Security Auditor Agent",
        "type": "user_defined",
        "base_type": "security_engineer",
        "file": "custom-security-auditor-agent.md",
        "description": "Specialized security auditing with penetration testing",
        "specialization": "security_audit",
        "domain_focus": "penetration_testing",
        "embedded_knowledge": [
          "OWASP Top 10 vulnerabilities",
          "Penetration testing methodologies",
          "Security compliance frameworks",
          "Threat modeling techniques"
        ],
        "delegation_triggers": [
          "security_audit_request",
          "vulnerability_assessment",
          "compliance_check",
          "penetration_test"
        ],
        "memory_categories": ["ERROR", "PATTERN", "TEAM"],
        "tools": ["security_scan", "vulnerability_assessment", "compliance_check"],
        "coordination_role": "security_specialist",
        "created": "2025-07-09",
        "version": "1.0.0"
      }
    }
  }
}
```

### Step 3: Agent Implementation

#### Basic Agent Class Structure

```python
"""
Custom Security Auditor Agent - Specialized security testing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from claude_pm.services.claude_pm_memory import ClaudePMMemory, MemoryCategory
from claude_pm.core.logging_config import get_logger
from claude_pm.core.enforcement import get_enforcement_engine

logger = get_logger(__name__)

class AuditType(str, Enum):
    """Types of security audits"""
    VULNERABILITY_SCAN = "vulnerability_scan"
    PENETRATION_TEST = "penetration_test"
    COMPLIANCE_CHECK = "compliance_check"
    CODE_REVIEW = "code_review"

@dataclass
class AuditResult:
    """Security audit result"""
    audit_type: AuditType
    severity: str
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_score: float
    report_path: str

class CustomSecurityAuditorAgent:
    """
    Custom Security Auditor Agent
    Specialized in penetration testing and security compliance
    """
    
    def __init__(self, memory: ClaudePMMemory):
        self.memory = memory
        self.enforcement_engine = get_enforcement_engine()
        self.agent_id = "custom_security_auditor"
        self.capabilities = [
            "vulnerability_scanning",
            "penetration_testing", 
            "compliance_checking",
            "security_code_review"
        ]
        
    async def execute_audit(self, audit_type: AuditType, 
                          target: str, 
                          context: Dict[str, Any]) -> AuditResult:
        """
        Execute a security audit
        
        Args:
            audit_type: Type of audit to perform
            target: Target system/code to audit
            context: Additional context for the audit
            
        Returns:
            AuditResult with findings and recommendations
        """
        logger.info(f"Starting {audit_type.value} audit on {target}")
        
        try:
            # Validate permissions
            if not await self._validate_audit_permissions(target, audit_type):
                raise PermissionError(f"Insufficient permissions for {audit_type.value}")
            
            # Prepare audit context with memory
            audit_context = await self._prepare_audit_context(target, audit_type, context)
            
            # Execute the audit
            if audit_type == AuditType.VULNERABILITY_SCAN:
                result = await self._perform_vulnerability_scan(target, audit_context)
            elif audit_type == AuditType.PENETRATION_TEST:
                result = await self._perform_penetration_test(target, audit_context)
            elif audit_type == AuditType.COMPLIANCE_CHECK:
                result = await self._perform_compliance_check(target, audit_context)
            elif audit_type == AuditType.CODE_REVIEW:
                result = await self._perform_security_code_review(target, audit_context)
            else:
                raise ValueError(f"Unsupported audit type: {audit_type}")
            
            # Store results in memory
            await self._store_audit_memory(result, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Audit execution failed: {e}")
            raise
    
    async def _validate_audit_permissions(self, target: str, audit_type: AuditType) -> bool:
        """Validate that the agent has permission to perform the audit"""
        # Implementation depends on enforcement engine
        return True
    
    async def _prepare_audit_context(self, target: str, audit_type: AuditType, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare audit context with relevant memories"""
        
        # Retrieve relevant security memories
        security_memories = await self.memory.retrieve_memories(
            category=MemoryCategory.ERROR,
            query=f"security {audit_type.value} {target}",
            limit=10
        )
        
        # Retrieve patterns
        pattern_memories = await self.memory.retrieve_memories(
            category=MemoryCategory.PATTERN,
            query=f"security audit {audit_type.value}",
            limit=5
        )
        
        audit_context = {
            "target": target,
            "audit_type": audit_type.value,
            "security_history": security_memories.data if security_memories.success else [],
            "audit_patterns": pattern_memories.data if pattern_memories.success else [],
            "original_context": context
        }
        
        return audit_context
    
    async def _perform_vulnerability_scan(self, target: str, 
                                        context: Dict[str, Any]) -> AuditResult:
        """Perform vulnerability scanning"""
        # Simulate vulnerability scan
        await asyncio.sleep(2)  # Simulate scan time
        
        findings = [
            {
                "vulnerability": "SQL Injection",
                "severity": "HIGH",
                "location": f"{target}/login.py:45",
                "description": "Unsanitized user input in database query",
                "cve": "CVE-2021-XXXX"
            },
            {
                "vulnerability": "XSS",
                "severity": "MEDIUM", 
                "location": f"{target}/templates/user_profile.html:12",
                "description": "Unescaped user input in template",
                "cve": "CVE-2021-YYYY"
            }
        ]
        
        recommendations = [
            "Implement parameterized queries for database operations",
            "Add input validation and sanitization",
            "Enable Content Security Policy (CSP) headers",
            "Update dependencies to latest secure versions"
        ]
        
        return AuditResult(
            audit_type=AuditType.VULNERABILITY_SCAN,
            severity="HIGH",
            findings=findings,
            recommendations=recommendations,
            compliance_score=0.75,
            report_path=f"/tmp/vuln_scan_{target}.html"
        )
    
    async def _perform_penetration_test(self, target: str,
                                      context: Dict[str, Any]) -> AuditResult:
        """Perform penetration testing"""
        # Simulate penetration test
        await asyncio.sleep(5)  # Simulate test time
        
        findings = [
            {
                "attack_vector": "Authentication Bypass",
                "severity": "CRITICAL",
                "success": True,
                "method": "JWT token manipulation",
                "impact": "Full system access achieved"
            },
            {
                "attack_vector": "Privilege Escalation",
                "severity": "HIGH",
                "success": True,
                "method": "Directory traversal",
                "impact": "Admin privileges obtained"
            }
        ]
        
        recommendations = [
            "Implement proper JWT validation",
            "Add rate limiting to authentication endpoints",
            "Implement proper access controls",
            "Add logging and monitoring for suspicious activities"
        ]
        
        return AuditResult(
            audit_type=AuditType.PENETRATION_TEST,
            severity="CRITICAL",
            findings=findings,
            recommendations=recommendations,
            compliance_score=0.45,
            report_path=f"/tmp/pentest_{target}.html"
        )
    
    async def _perform_compliance_check(self, target: str,
                                      context: Dict[str, Any]) -> AuditResult:
        """Perform compliance checking"""
        # Simulate compliance check
        await asyncio.sleep(3)  # Simulate check time
        
        findings = [
            {
                "standard": "OWASP Top 10",
                "compliance": "PARTIAL",
                "missing": ["A3: Injection", "A7: XSS"],
                "score": 0.8
            },
            {
                "standard": "SOC 2 Type II",
                "compliance": "FAIL",
                "missing": ["Access Controls", "Logging"],
                "score": 0.6
            }
        ]
        
        recommendations = [
            "Implement input validation framework",
            "Add comprehensive audit logging",
            "Implement access control matrix",
            "Add security awareness training"
        ]
        
        return AuditResult(
            audit_type=AuditType.COMPLIANCE_CHECK,
            severity="MEDIUM",
            findings=findings,
            recommendations=recommendations,
            compliance_score=0.7,
            report_path=f"/tmp/compliance_{target}.html"
        )
    
    async def _perform_security_code_review(self, target: str,
                                          context: Dict[str, Any]) -> AuditResult:
        """Perform security-focused code review"""
        # Simulate code review
        await asyncio.sleep(4)  # Simulate review time
        
        findings = [
            {
                "file": f"{target}/src/auth.py",
                "line": 23,
                "issue": "Hardcoded password",
                "severity": "CRITICAL",
                "suggestion": "Use environment variables or secure config"
            },
            {
                "file": f"{target}/src/api.py", 
                "line": 67,
                "issue": "Missing input validation",
                "severity": "HIGH",
                "suggestion": "Add input sanitization"
            }
        ]
        
        recommendations = [
            "Remove all hardcoded credentials",
            "Implement input validation library",
            "Add security linting to CI/CD pipeline",
            "Implement code scanning tools"
        ]
        
        return AuditResult(
            audit_type=AuditType.CODE_REVIEW,
            severity="CRITICAL",
            findings=findings,
            recommendations=recommendations,
            compliance_score=0.65,
            report_path=f"/tmp/code_review_{target}.html"
        )
    
    async def _store_audit_memory(self, result: AuditResult, context: Dict[str, Any]):
        """Store audit results in memory system"""
        
        # Store as error memory if critical findings
        if result.severity in ["CRITICAL", "HIGH"]:
            error_content = f"""
Security Audit - {result.audit_type.value}

Severity: {result.severity}
Compliance Score: {result.compliance_score}

Critical Findings:
{chr(10).join([f"- {f.get('vulnerability', f.get('attack_vector', f.get('issue', 'Unknown')))}: {f.get('severity', 'Unknown')}" for f in result.findings])}

Recommendations:
{chr(10).join([f"- {rec}" for rec in result.recommendations])}
""".strip()
            
            await self.memory.store_memory(
                category=MemoryCategory.ERROR,
                content=error_content,
                metadata={
                    "audit_type": result.audit_type.value,
                    "severity": result.severity,
                    "compliance_score": result.compliance_score,
                    "findings_count": len(result.findings)
                },
                tags=["security", "audit", result.audit_type.value]
            )
        
        # Store as pattern memory
        pattern_content = f"""
Security Audit Pattern - {result.audit_type.value}

Audit completed successfully
Compliance Score: {result.compliance_score}
Findings: {len(result.findings)}
Report: {result.report_path}

Common Issues Found:
{chr(10).join([f"- {f.get('vulnerability', f.get('attack_vector', f.get('issue', 'Unknown')))}" for f in result.findings[:3]])}
""".strip()
        
        await self.memory.store_memory(
            category=MemoryCategory.PATTERN,
            content=pattern_content,
            metadata={
                "audit_type": result.audit_type.value,
                "compliance_score": result.compliance_score,
                "success": True
            },
            tags=["security", "audit", "pattern", result.audit_type.value]
        )
```

### Step 4: Agent Integration

#### Multi-Agent Orchestrator Integration

```python
"""
Integration with Multi-Agent Orchestrator
"""

from claude_pm.services.multi_agent_orchestrator import MultiAgentOrchestrator, AgentType

class CustomAgentType(AgentType):
    """Extended agent types with custom agents"""
    CUSTOM_SECURITY_AUDITOR = "custom_security_auditor"
    CUSTOM_PERFORMANCE_OPTIMIZER = "custom_performance_optimizer"
    CUSTOM_DATA_VALIDATOR = "custom_data_validator"

# Register custom agent in orchestrator
def register_custom_agents(orchestrator: MultiAgentOrchestrator):
    """Register custom agents with the orchestrator"""
    
    # Add custom security auditor
    orchestrator.agent_definitions[CustomAgentType.CUSTOM_SECURITY_AUDITOR] = {
        "name": "Custom Security Auditor Agent",
        "description": "Specialized security auditing and penetration testing",
        "memory_categories": [MemoryCategory.ERROR, MemoryCategory.PATTERN, MemoryCategory.TEAM],
        "specializations": ["vulnerability_scanning", "penetration_testing", "compliance_checking"],
        "context_keywords": ["security", "audit", "vulnerability", "penetration", "compliance"]
    }
    
    logger.info("Custom agents registered with orchestrator")

# Usage example
async def use_custom_security_agent():
    """Example of using custom security agent"""
    
    # Initialize memory and orchestrator
    memory = ClaudePMMemory()
    orchestrator = MultiAgentOrchestrator(base_repo_path="/path/to/repo", memory=memory)
    
    # Register custom agents
    register_custom_agents(orchestrator)
    
    # Create custom agent
    security_agent = CustomSecurityAuditorAgent(memory)
    
    # Execute security audit
    result = await security_agent.execute_audit(
        audit_type=AuditType.VULNERABILITY_SCAN,
        target="my-web-app",
        context={"framework": "fastapi", "database": "postgresql"}
    )
    
    print(f"Audit completed: {result.severity} - {len(result.findings)} findings")
    print(f"Compliance score: {result.compliance_score}")
```

## Agent Customization

### Extending Existing Agents

#### Method 1: Inheritance

```python
"""
Extending the Engineer Agent with specialized capabilities
"""

from claude_pm.framework.agent_roles.engineer_agent import EngineerAgent

class CustomFrontendEngineerAgent(EngineerAgent):
    """
    Custom Frontend Engineer Agent
    Specialized in React/TypeScript development
    """
    
    def __init__(self, memory: ClaudePMMemory):
        super().__init__(memory)
        self.specialization = "frontend_development"
        self.frameworks = ["react", "typescript", "next.js", "tailwind"]
        self.tools.extend(["webpack", "vite", "storybook"])
    
    async def create_component(self, component_name: str, props: Dict[str, Any]) -> Dict[str, Any]:
        """Create a React component with TypeScript"""
        
        # Retrieve component patterns from memory
        patterns = await self.memory.retrieve_memories(
            category=MemoryCategory.PATTERN,
            query=f"react component {component_name}",
            limit=3
        )
        
        # Generate component code
        component_code = self._generate_react_component(component_name, props, patterns)
        
        # Generate tests
        test_code = self._generate_component_tests(component_name, props)
        
        # Generate stories
        story_code = self._generate_component_stories(component_name, props)
        
        result = {
            "component_file": f"src/components/{component_name}.tsx",
            "test_file": f"src/components/{component_name}.test.tsx",
            "story_file": f"src/components/{component_name}.stories.tsx",
            "component_code": component_code,
            "test_code": test_code,
            "story_code": story_code
        }
        
        # Store pattern in memory
        await self._store_component_pattern(component_name, result)
        
        return result
    
    def _generate_react_component(self, name: str, props: Dict[str, Any], patterns: List[Dict]) -> str:
        """Generate React component code"""
        
        # Use patterns from memory to inform generation
        prop_types = self._infer_prop_types(props, patterns)
        
        component_code = f"""
import React from 'react';
import {{ FC }} from 'react';

interface {name}Props {{
{chr(10).join([f"  {prop}: {prop_type};" for prop, prop_type in prop_types.items()])}
}}

const {name}: FC<{name}Props> = ({{ {', '.join(prop_types.keys())} }}) => {{
  return (
    <div className="{name.lower()}">
      {/* Component implementation */}
    </div>
  );
}};

export default {name};
""".strip()
        
        return component_code
    
    def _generate_component_tests(self, name: str, props: Dict[str, Any]) -> str:
        """Generate Jest/React Testing Library tests"""
        
        test_code = f"""
import {{ render, screen }} from '@testing-library/react';
import {name} from './{name}';

describe('{name}', () => {{
  it('renders correctly', () => {{
    render(<{name} {' '.join([f'{prop}={{testValue}}' for prop in props.keys()])} />);
    expect(screen.getByTestId('{name.lower()}')).toBeInTheDocument();
  }});
  
  // Add more tests based on component functionality
}});
""".strip()
        
        return test_code
    
    def _generate_component_stories(self, name: str, props: Dict[str, Any]) -> str:
        """Generate Storybook stories"""
        
        story_code = f"""
import type {{ Meta, StoryObj }} from '@storybook/react';
import {{ {name} }} from './{name}';

const meta: Meta<typeof {name}> = {{
  title: 'Components/{name}',
  component: {name},
  parameters: {{
    layout: 'centered',
  }},
}};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {{
  args: {{
    {', '.join([f'{prop}: "example"' for prop in props.keys()])}
  }},
}};
""".strip()
        
        return story_code
```

#### Method 2: Composition

```python
"""
Composing multiple agent capabilities
"""

class CustomFullStackAgent:
    """
    Custom Full Stack Agent
    Combines frontend, backend, and database capabilities
    """
    
    def __init__(self, memory: ClaudePMMemory):
        self.memory = memory
        self.frontend_agent = CustomFrontendEngineerAgent(memory)
        self.backend_agent = CustomBackendEngineerAgent(memory)
        self.database_agent = CustomDatabaseEngineerAgent(memory)
        self.integration_agent = IntegrationAgent(memory)
    
    async def create_full_stack_feature(self, feature_name: str, 
                                      requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete full-stack feature"""
        
        results = {}
        
        # Create database schema
        if requirements.get("database"):
            results["database"] = await self.database_agent.create_schema(
                feature_name, requirements["database"]
            )
        
        # Create backend API
        if requirements.get("api"):
            results["backend"] = await self.backend_agent.create_api(
                feature_name, requirements["api"]
            )
        
        # Create frontend components
        if requirements.get("frontend"):
            results["frontend"] = await self.frontend_agent.create_component(
                feature_name, requirements["frontend"]
            )
        
        # Create integration tests
        results["integration"] = await self.integration_agent.create_integration_tests(
            feature_name, results
        )
        
        return results
```

### Agent Parameter Tuning

#### Configuration Parameters

```python
"""
Agent configuration and parameter tuning
"""

@dataclass
class AgentConfig:
    """Configuration for custom agents"""
    
    # Performance parameters
    max_parallel_tasks: int = 3
    timeout_seconds: int = 300
    retry_attempts: int = 2
    
    # Memory parameters
    memory_categories: List[MemoryCategory] = None
    memory_limit: int = 100
    memory_ttl_hours: int = 24
    
    # Quality parameters
    quality_threshold: float = 0.8
    test_coverage_minimum: float = 0.85
    
    # Security parameters
    security_scan_enabled: bool = True
    vulnerability_threshold: str = "MEDIUM"
    
    # Logging parameters
    log_level: str = "INFO"
    detailed_logging: bool = False
    
    # ai-trackdown-tools configuration
    ai_trackdown_tools: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,                    # Enable ai-trackdown-tools integration
        "cli_command": "aitrackdown",       # CLI command to use
        "timeout": 30,                      # Command timeout in seconds
        "fallback_method": "logging",       # Fallback when unavailable
        "retry_attempts": 3,                # Number of retry attempts
        "retry_delay": 1,                   # Delay between retries
        "verbose_logging": False,           # Enable verbose output
        "subprocess_timeout": 60,           # Subprocess timeout
        "max_concurrent_operations": 3,     # Max concurrent operations for agent
        "process_cleanup_timeout": 10,      # Process cleanup timeout
        "agent_specific_settings": {
            "create_tickets": True,         # Allow agent to create tickets
            "update_tickets": True,         # Allow agent to update tickets
            "complete_tickets": True,       # Allow agent to complete tickets
            "delete_tickets": False,        # Prevent agent from deleting tickets
        }
    })

class ConfigurableAgent:
    """Base class for configurable agents"""
    
    def __init__(self, config: AgentConfig, memory: ClaudePMMemory):
        self.config = config
        self.memory = memory
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(getattr(logging, config.log_level))
    
    async def execute_with_config(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with configuration parameters"""
        
        # Apply timeout
        try:
            result = await asyncio.wait_for(
                self._execute_task(task),
                timeout=self.config.timeout_seconds
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Task timed out after {self.config.timeout_seconds}s")
            raise
        
        # Apply quality threshold
        if result.get("quality_score", 1.0) < self.config.quality_threshold:
            self.logger.warning(f"Quality score {result['quality_score']} below threshold")
        
        return result
    
    async def create_tracking_ticket(self, ticket_type: str, title: str, description: str = "", 
                                   epic_id: str = None, issue_id: str = None) -> Dict[str, Any]:
        """Create a tracking ticket using ai-trackdown-tools"""
        if not self.config.ai_trackdown_tools["enabled"]:
            self.logger.info("ai-trackdown-tools disabled, skipping ticket creation")
            return {"status": "skipped", "reason": "ai-trackdown-tools disabled"}
        
        if not self.config.ai_trackdown_tools["agent_specific_settings"]["create_tickets"]:
            self.logger.warning("Agent not permitted to create tickets")
            return {"status": "denied", "reason": "create_tickets permission denied"}
        
        try:
            cli_command = self.config.ai_trackdown_tools["cli_command"]
            timeout = self.config.ai_trackdown_tools["timeout"]
            
            # Build command based on ticket type
            if ticket_type == "epic":
                cmd = [cli_command, "epic", "create", "--title", title, "--description", description]
            elif ticket_type == "issue":
                cmd = [cli_command, "issue", "create", "--title", title]
                if description:
                    cmd.extend(["--description", description])
                if epic_id:
                    cmd.extend(["--epic", epic_id])
            elif ticket_type == "task":
                cmd = [cli_command, "task", "create", "--title", title]
                if description:
                    cmd.extend(["--description", description])
                if issue_id:
                    cmd.extend(["--issue", issue_id])
            else:
                raise ValueError(f"Unknown ticket type: {ticket_type}")
            
            # Execute command
            import subprocess
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully created {ticket_type} ticket: {title}")
                return {"status": "success", "output": result.stdout.strip()}
            else:
                self.logger.error(f"Failed to create {ticket_type} ticket: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            self.logger.error(f"Error creating {ticket_type} ticket: {e}")
            # Fallback to logging if configured
            if self.config.ai_trackdown_tools["fallback_method"] == "logging":
                self.logger.info(f"FALLBACK: Would create {ticket_type} ticket: {title}")
                return {"status": "fallback", "method": "logging"}
            return {"status": "error", "error": str(e)}
    
    async def update_tracking_ticket(self, ticket_id: str, status: str = None, 
                                   description: str = None) -> Dict[str, Any]:
        """Update a tracking ticket using ai-trackdown-tools"""
        if not self.config.ai_trackdown_tools["enabled"]:
            return {"status": "skipped", "reason": "ai-trackdown-tools disabled"}
        
        if not self.config.ai_trackdown_tools["agent_specific_settings"]["update_tickets"]:
            self.logger.warning("Agent not permitted to update tickets")
            return {"status": "denied", "reason": "update_tickets permission denied"}
        
        try:
            cli_command = self.config.ai_trackdown_tools["cli_command"]
            timeout = self.config.ai_trackdown_tools["timeout"]
            
            # Determine ticket type from ID
            if ticket_id.startswith("EP-"):
                ticket_type = "epic"
            elif ticket_id.startswith("ISS-"):
                ticket_type = "issue"
            elif ticket_id.startswith("TSK-"):
                ticket_type = "task"
            else:
                raise ValueError(f"Unknown ticket ID format: {ticket_id}")
            
            # Build update command
            cmd = [cli_command, ticket_type, "update", ticket_id]
            if status:
                cmd.extend(["--status", status])
            if description:
                cmd.extend(["--description", description])
            
            # Execute command
            import subprocess
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully updated {ticket_type} ticket: {ticket_id}")
                return {"status": "success", "output": result.stdout.strip()}
            else:
                self.logger.error(f"Failed to update {ticket_type} ticket: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket_id}: {e}")
            if self.config.ai_trackdown_tools["fallback_method"] == "logging":
                self.logger.info(f"FALLBACK: Would update ticket {ticket_id} with status: {status}")
                return {"status": "fallback", "method": "logging"}
            return {"status": "error", "error": str(e)}
    
    async def complete_tracking_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Complete a tracking ticket using ai-trackdown-tools"""
        if not self.config.ai_trackdown_tools["enabled"]:
            return {"status": "skipped", "reason": "ai-trackdown-tools disabled"}
        
        if not self.config.ai_trackdown_tools["agent_specific_settings"]["complete_tickets"]:
            self.logger.warning("Agent not permitted to complete tickets")
            return {"status": "denied", "reason": "complete_tickets permission denied"}
        
        try:
            cli_command = self.config.ai_trackdown_tools["cli_command"]
            timeout = self.config.ai_trackdown_tools["timeout"]
            
            # Determine ticket type from ID
            if ticket_id.startswith("EP-"):
                ticket_type = "epic"
            elif ticket_id.startswith("ISS-"):
                ticket_type = "issue"
            elif ticket_id.startswith("TSK-"):
                ticket_type = "task"
            else:
                raise ValueError(f"Unknown ticket ID format: {ticket_id}")
            
            # Build complete command
            cmd = [cli_command, ticket_type, "complete", ticket_id]
            
            # Execute command
            import subprocess
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully completed {ticket_type} ticket: {ticket_id}")
                return {"status": "success", "output": result.stdout.strip()}
            else:
                self.logger.error(f"Failed to complete {ticket_type} ticket: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            self.logger.error(f"Error completing ticket {ticket_id}: {e}")
            if self.config.ai_trackdown_tools["fallback_method"] == "logging":
                self.logger.info(f"FALLBACK: Would complete ticket {ticket_id}")
                return {"status": "fallback", "method": "logging"}
            return {"status": "error", "error": str(e)}
```

### Prompt Engineering for Agents

#### Structured Prompts

```python
"""
Prompt engineering for custom agents
"""

class AgentPromptTemplate:
    """Template for agent prompts"""
    
    def __init__(self, agent_type: str, specialization: str):
        self.agent_type = agent_type
        self.specialization = specialization
        self.base_prompt = self._create_base_prompt()
    
    def _create_base_prompt(self) -> str:
        """Create base prompt for agent"""
        return f"""
You are a {self.agent_type} agent specialized in {self.specialization}.

Your primary responsibilities include:
- [Specific responsibility 1]
- [Specific responsibility 2]
- [Specific responsibility 3]

You have access to the following tools and capabilities:
- Memory system with categories: PROJECT, PATTERN, TEAM, ERROR
- Enforcement engine for permission validation
- Multi-agent coordination system

Context from memory:
{{memory_context}}

Current task:
{{task_description}}

Please provide a detailed response that includes:
1. Analysis of the task
2. Step-by-step approach
3. Expected outputs
4. Potential risks or considerations
5. Next steps or recommendations
"""
    
    def format_prompt(self, task_description: str, memory_context: Dict[str, Any]) -> str:
        """Format prompt with task and memory context"""
        
        # Format memory context
        formatted_memory = self._format_memory_context(memory_context)
        
        # Format the prompt
        formatted_prompt = self.base_prompt.format(
            task_description=task_description,
            memory_context=formatted_memory
        )
        
        return formatted_prompt
    
    def _format_memory_context(self, memory_context: Dict[str, Any]) -> str:
        """Format memory context for prompt"""
        
        sections = []
        
        # Patterns
        if memory_context.get("patterns"):
            sections.append("Relevant Patterns:")
            for pattern in memory_context["patterns"][:3]:
                sections.append(f"- {pattern.get('content', 'Unknown')[:100]}...")
        
        # Historical errors
        if memory_context.get("historical_errors"):
            sections.append("Historical Issues to Avoid:")
            for error in memory_context["historical_errors"][:2]:
                sections.append(f"- {error.get('content', 'Unknown')[:100]}...")
        
        # Team standards
        if memory_context.get("team_standards"):
            sections.append("Team Standards:")
            for standard in memory_context["team_standards"][:2]:
                sections.append(f"- {standard.get('content', 'Unknown')[:100]}...")
        
        return "\n".join(sections) if sections else "No relevant memory context available"

class CustomAgentPrompts:
    """Collection of prompts for different agent types"""
    
    @staticmethod
    def security_audit_prompt(target: str, audit_type: str) -> str:
        """Prompt for security audit tasks"""
        return f"""
You are a Custom Security Auditor Agent performing a {audit_type} on {target}.

Your security audit should include:
1. **Vulnerability Assessment**
   - Identify potential security weaknesses
   - Classify vulnerabilities by severity (CRITICAL, HIGH, MEDIUM, LOW)
   - Provide CVE references where applicable

2. **Compliance Check**
   - Verify against OWASP Top 10
   - Check industry standards (SOC 2, ISO 27001)
   - Evaluate security controls effectiveness

3. **Recommendations**
   - Provide specific remediation steps
   - Include implementation priority
   - Suggest preventive measures

4. **Risk Assessment**
   - Evaluate business impact
   - Assess likelihood of exploitation
   - Provide risk mitigation strategies

Please provide a comprehensive security audit report.
"""
    
    @staticmethod
    def code_review_prompt(code_context: str, review_type: str) -> str:
        """Prompt for code review tasks"""
        return f"""
You are a Code Review Engineer Agent performing a {review_type} review.

Code context: {code_context}

Your review should cover:
1. **Code Quality**
   - Adherence to coding standards
   - Code maintainability and readability
   - Design patterns usage

2. **Security Analysis**
   - Input validation
   - Authentication and authorization
   - Data protection measures

3. **Performance Considerations**
   - Algorithm efficiency
   - Resource usage
   - Scalability factors

4. **Testing Coverage**
   - Unit test completeness
   - Integration test coverage
   - Edge case handling

Please provide detailed feedback with specific line-by-line comments where appropriate.
"""
```

## Advanced Agent Features

### Memory Integration Patterns

#### Custom Memory Categories

```python
"""
Custom memory categories for specialized agents
"""

class CustomMemoryCategory(str, Enum):
    """Extended memory categories"""
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    CODE_REVIEW = "code_review"
    DEPLOYMENT_LOG = "deployment_log"
    USER_FEEDBACK = "user_feedback"

class EnhancedMemoryIntegration:
    """Enhanced memory integration for custom agents"""
    
    def __init__(self, memory: ClaudePMMemory):
        self.memory = memory
        self.custom_categories = CustomMemoryCategory
    
    async def store_specialized_memory(self, 
                                     category: CustomMemoryCategory,
                                     content: str,
                                     metadata: Dict[str, Any],
                                     tags: List[str]) -> str:
        """Store specialized memory with custom categories"""
        
        # Enhance metadata with category-specific information
        enhanced_metadata = {
            **metadata,
            "custom_category": category.value,
            "timestamp": datetime.now().isoformat(),
            "agent_type": "custom"
        }
        
        # Store in appropriate base category
        base_category_mapping = {
            CustomMemoryCategory.SECURITY_AUDIT: MemoryCategory.ERROR,
            CustomMemoryCategory.PERFORMANCE_BENCHMARK: MemoryCategory.PATTERN,
            CustomMemoryCategory.CODE_REVIEW: MemoryCategory.TEAM,
            CustomMemoryCategory.DEPLOYMENT_LOG: MemoryCategory.PROJECT,
            CustomMemoryCategory.USER_FEEDBACK: MemoryCategory.TEAM
        }
        
        base_category = base_category_mapping.get(category, MemoryCategory.PATTERN)
        
        response = await self.memory.store_memory(
            category=base_category,
            content=content,
            metadata=enhanced_metadata,
            tags=tags + [category.value]
        )
        
        return response.memory_id if response.success else None
    
    async def retrieve_specialized_memory(self,
                                        category: CustomMemoryCategory,
                                        query: str,
                                        limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve specialized memory by custom category"""
        
        # Map to base category
        base_category_mapping = {
            CustomMemoryCategory.SECURITY_AUDIT: MemoryCategory.ERROR,
            CustomMemoryCategory.PERFORMANCE_BENCHMARK: MemoryCategory.PATTERN,
            CustomMemoryCategory.CODE_REVIEW: MemoryCategory.TEAM,
            CustomMemoryCategory.DEPLOYMENT_LOG: MemoryCategory.PROJECT,
            CustomMemoryCategory.USER_FEEDBACK: MemoryCategory.TEAM
        }
        
        base_category = base_category_mapping.get(category, MemoryCategory.PATTERN)
        
        # Retrieve with enhanced query
        enhanced_query = f"{query} {category.value}"
        
        response = await self.memory.retrieve_memories(
            category=base_category,
            query=enhanced_query,
            limit=limit
        )
        
        if response.success:
            # Filter by custom category
            filtered_memories = [
                memory for memory in response.data.get("memories", [])
                if memory.get("metadata", {}).get("custom_category") == category.value
            ]
            return filtered_memories
        
        return []
```

### Cross-Agent Communication

#### Message Bus System

```python
"""
Cross-agent communication system
"""

@dataclass
class AgentMessage:
    """Message between agents"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 5
    requires_response: bool = False

class AgentMessageBus:
    """Message bus for inter-agent communication"""
    
    def __init__(self):
        self.message_queue: Dict[str, List[AgentMessage]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.subscriptions: Dict[str, List[str]] = {}
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send message to another agent"""
        
        # Add to recipient's queue
        if message.to_agent not in self.message_queue:
            self.message_queue[message.to_agent] = []
        
        self.message_queue[message.to_agent].append(message)
        
        # Sort by priority
        self.message_queue[message.to_agent].sort(key=lambda m: m.priority, reverse=True)
        
        # Notify subscribers
        await self._notify_subscribers(message.to_agent, message)
        
        return True
    
    async def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """Receive messages for an agent"""
        
        messages = self.message_queue.get(agent_id, [])
        self.message_queue[agent_id] = []  # Clear after reading
        
        return messages
    
    def subscribe(self, agent_id: str, message_type: str, handler: Callable):
        """Subscribe to specific message types"""
        
        if message_type not in self.subscriptions:
            self.subscriptions[message_type] = []
        
        self.subscriptions[message_type].append(agent_id)
        self.message_handlers[f"{agent_id}_{message_type}"] = handler
    
    async def _notify_subscribers(self, recipient: str, message: AgentMessage):
        """Notify subscribers of new messages"""
        
        subscribers = self.subscriptions.get(message.message_type, [])
        
        for subscriber in subscribers:
            if subscriber == recipient:
                handler_key = f"{subscriber}_{message.message_type}"
                handler = self.message_handlers.get(handler_key)
                
                if handler:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Message handler error: {e}")

class CommunicatingAgent:
    """Base class for agents that communicate with each other"""
    
    def __init__(self, agent_id: str, message_bus: AgentMessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Set up message handlers for this agent"""
        
        # Subscribe to common message types
        self.message_bus.subscribe(self.agent_id, "task_request", self._handle_task_request)
        self.message_bus.subscribe(self.agent_id, "status_update", self._handle_status_update)
        self.message_bus.subscribe(self.agent_id, "error_notification", self._handle_error_notification)
    
    async def send_task_request(self, target_agent: str, task: Dict[str, Any]) -> str:
        """Send task request to another agent"""
        
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=target_agent,
            message_type="task_request",
            content=task,
            timestamp=datetime.now(),
            priority=7,
            requires_response=True
        )
        
        await self.message_bus.send_message(message)
        return message.message_id
    
    async def send_status_update(self, target_agent: str, status: Dict[str, Any]):
        """Send status update to another agent"""
        
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=target_agent,
            message_type="status_update",
            content=status,
            timestamp=datetime.now(),
            priority=5
        )
        
        await self.message_bus.send_message(message)
    
    async def _handle_task_request(self, message: AgentMessage):
        """Handle incoming task request"""
        logger.info(f"Received task request from {message.from_agent}")
        
        # Process the task
        result = await self._process_task(message.content)
        
        # Send response if required
        if message.requires_response:
            await self.send_task_response(message.from_agent, message.message_id, result)
    
    async def _handle_status_update(self, message: AgentMessage):
        """Handle incoming status update"""
        logger.info(f"Received status update from {message.from_agent}: {message.content}")
    
    async def _handle_error_notification(self, message: AgentMessage):
        """Handle incoming error notification"""
        logger.error(f"Received error notification from {message.from_agent}: {message.content}")
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task (to be implemented by subclasses)"""
        return {"status": "completed", "result": "task processed"}
```

### Event Handling and Triggers

#### Event-Driven Architecture

```python
"""
Event-driven architecture for custom agents
"""

class AgentEvent:
    """Base class for agent events"""
    
    def __init__(self, event_type: str, source: str, data: Dict[str, Any]):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.source = source
        self.data = data
        self.timestamp = datetime.now()

class EventHandler:
    """Base class for event handlers"""
    
    async def handle(self, event: AgentEvent) -> bool:
        """Handle an event"""
        raise NotImplementedError

class SecurityEventHandler(EventHandler):
    """Handler for security events"""
    
    def __init__(self, security_agent: CustomSecurityAuditorAgent):
        self.security_agent = security_agent
    
    async def handle(self, event: AgentEvent) -> bool:
        """Handle security events"""
        
        if event.event_type == "vulnerability_detected":
            await self._handle_vulnerability_detected(event)
            return True
        elif event.event_type == "security_scan_completed":
            await self._handle_scan_completed(event)
            return True
        
        return False
    
    async def _handle_vulnerability_detected(self, event: AgentEvent):
        """Handle vulnerability detection"""
        
        vulnerability = event.data.get("vulnerability", {})
        severity = vulnerability.get("severity", "UNKNOWN")
        
        # Trigger immediate response for critical vulnerabilities
        if severity == "CRITICAL":
            await self.security_agent.execute_audit(
                audit_type=AuditType.VULNERABILITY_SCAN,
                target=event.data.get("target", "unknown"),
                context={"priority": "immediate", "triggered_by": event.event_id}
            )

class EventBus:
    """Event bus for agent events"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.event_log: List[AgentEvent] = []
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe to events"""
        
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
    
    async def publish(self, event: AgentEvent):
        """Publish an event"""
        
        # Log the event
        self.event_log.append(event)
        
        # Notify handlers
        handlers = self.handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_event_history(self, event_type: Optional[str] = None) -> List[AgentEvent]:
        """Get event history"""
        
        if event_type:
            return [event for event in self.event_log if event.event_type == event_type]
        
        return self.event_log.copy()

class EventDrivenAgent:
    """Base class for event-driven agents"""
    
    def __init__(self, agent_id: str, event_bus: EventBus):
        self.agent_id = agent_id
        self.event_bus = event_bus
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event handlers (to be implemented by subclasses)"""
        pass
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event"""
        
        event = AgentEvent(
            event_type=event_type,
            source=self.agent_id,
            data=data
        )
        
        await self.event_bus.publish(event)
```

### Error Handling and Recovery

#### Comprehensive Error Handling

```python
"""
Comprehensive error handling and recovery for custom agents
"""

class AgentError(Exception):
    """Base exception for agent errors"""
    
    def __init__(self, message: str, error_code: str, recoverable: bool = True):
        super().__init__(message)
        self.error_code = error_code
        self.recoverable = recoverable
        self.timestamp = datetime.now()

class ValidationError(AgentError):
    """Validation error"""
    
    def __init__(self, message: str, field: str):
        super().__init__(message, "VALIDATION_ERROR", recoverable=True)
        self.field = field

class AuthorizationError(AgentError):
    """Authorization error"""
    
    def __init__(self, message: str, resource: str):
        super().__init__(message, "AUTHORIZATION_ERROR", recoverable=False)
        self.resource = resource

class TimeoutError(AgentError):
    """Timeout error"""
    
    def __init__(self, message: str, timeout_seconds: int):
        super().__init__(message, "TIMEOUT_ERROR", recoverable=True)
        self.timeout_seconds = timeout_seconds

class ErrorRecoveryStrategy:
    """Strategy for error recovery"""
    
    async def can_recover(self, error: AgentError) -> bool:
        """Check if error can be recovered"""
        return error.recoverable
    
    async def recover(self, error: AgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from error"""
        raise NotImplementedError

class RetryStrategy(ErrorRecoveryStrategy):
    """Retry strategy for recoverable errors"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def recover(self, error: AgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry the failed operation"""
        
        retries = context.get("retries", 0)
        
        if retries >= self.max_retries:
            raise error
        
        # Exponential backoff
        wait_time = self.backoff_factor ** retries
        await asyncio.sleep(wait_time)
        
        return {
            "action": "retry",
            "retries": retries + 1,
            "wait_time": wait_time
        }

class FallbackStrategy(ErrorRecoveryStrategy):
    """Fallback strategy for non-recoverable errors"""
    
    def __init__(self, fallback_handler: Callable):
        self.fallback_handler = fallback_handler
    
    async def recover(self, error: AgentError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fallback handler"""
        
        result = await self.fallback_handler(error, context)
        
        return {
            "action": "fallback",
            "result": result
        }

class ResilientAgent:
    """Base class for resilient agents with error handling"""
    
    def __init__(self, agent_id: str, memory: ClaudePMMemory):
        self.agent_id = agent_id
        self.memory = memory
        self.recovery_strategies = self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self) -> Dict[str, ErrorRecoveryStrategy]:
        """Set up recovery strategies"""
        
        return {
            "VALIDATION_ERROR": RetryStrategy(max_retries=2),
            "TIMEOUT_ERROR": RetryStrategy(max_retries=3, backoff_factor=1.5),
            "AUTHORIZATION_ERROR": FallbackStrategy(self._handle_authorization_fallback)
        }
    
    async def execute_with_recovery(self, operation: Callable, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation with error recovery"""
        
        max_recovery_attempts = 3
        recovery_attempts = 0
        
        while recovery_attempts < max_recovery_attempts:
            try:
                result = await operation(context)
                return result
                
            except AgentError as error:
                recovery_attempts += 1
                
                # Log the error
                await self._log_error(error, context)
                
                # Attempt recovery
                recovery_strategy = self.recovery_strategies.get(error.error_code)
                
                if recovery_strategy and await recovery_strategy.can_recover(error):
                    recovery_result = await recovery_strategy.recover(error, context)
                    
                    # Update context with recovery information
                    context.update(recovery_result)
                    
                    if recovery_result.get("action") == "retry":
                        continue
                    elif recovery_result.get("action") == "fallback":
                        return recovery_result
                
                # If no recovery strategy or recovery failed, re-raise
                raise error
            
            except Exception as e:
                # Convert to AgentError
                agent_error = AgentError(
                    message=str(e),
                    error_code="UNKNOWN_ERROR",
                    recoverable=False
                )
                
                await self._log_error(agent_error, context)
                raise agent_error
        
        # If we've exhausted recovery attempts
        raise AgentError("Max recovery attempts exceeded", "RECOVERY_FAILED", recoverable=False)
    
    async def _log_error(self, error: AgentError, context: Dict[str, Any]):
        """Log error to memory system"""
        
        error_content = f"""
Agent Error - {self.agent_id}

Error Code: {error.error_code}
Message: {error.message}
Recoverable: {error.recoverable}
Timestamp: {error.timestamp}

Context:
{json.dumps(context, indent=2)}
""".strip()
        
        await self.memory.store_memory(
            category=MemoryCategory.ERROR,
            content=error_content,
            metadata={
                "agent_id": self.agent_id,
                "error_code": error.error_code,
                "recoverable": error.recoverable,
                "timestamp": error.timestamp.isoformat()
            },
            tags=["agent_error", self.agent_id, error.error_code]
        )
    
    async def _handle_authorization_fallback(self, error: AuthorizationError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle authorization fallback"""
        
        return {
            "status": "authorization_failed",
            "message": f"Access denied to {error.resource}",
            "suggested_action": "Contact system administrator"
        }
```

## Agent Deployment and Management

### Agent Registration and Discovery

#### Service Registry

```python
"""
Agent registration and discovery system
"""

@dataclass
class AgentRegistration:
    """Agent registration information"""
    agent_id: str
    agent_type: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    health_check_url: str
    metadata: Dict[str, Any]
    status: str = "active"
    registered_at: datetime = None
    last_heartbeat: datetime = None

class AgentRegistry:
    """Registry for managing agent instances"""
    
    def __init__(self):
        self.agents: Dict[str, AgentRegistration] = {}
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90   # seconds
    
    async def register_agent(self, registration: AgentRegistration) -> bool:
        """Register an agent"""
        
        registration.registered_at = datetime.now()
        registration.last_heartbeat = datetime.now()
        
        self.agents[registration.agent_id] = registration
        
        logger.info(f"Agent {registration.agent_id} registered")
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
            return True
        
        return False
    
    async def update_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat"""
        
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.now()
            return True
        
        return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent registration"""
        return self.agents.get(agent_id)
    
    async def discover_agents(self, agent_type: Optional[str] = None,
                            capabilities: Optional[List[str]] = None) -> List[AgentRegistration]:
        """Discover agents by type or capabilities"""
        
        agents = list(self.agents.values())
        
        # Filter by type
        if agent_type:
            agents = [agent for agent in agents if agent.agent_type == agent_type]
        
        # Filter by capabilities
        if capabilities:
            agents = [
                agent for agent in agents
                if all(cap in agent.capabilities for cap in capabilities)
            ]
        
        # Filter by health
        now = datetime.now()
        healthy_agents = [
            agent for agent in agents
            if (now - agent.last_heartbeat).total_seconds() < self.heartbeat_timeout
        ]
        
        return healthy_agents
    
    async def cleanup_stale_agents(self):
        """Remove stale agents that haven't sent heartbeats"""
        
        now = datetime.now()
        stale_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if (now - agent.last_heartbeat).total_seconds() > self.heartbeat_timeout
        ]
        
        for agent_id in stale_agents:
            await self.unregister_agent(agent_id)
            logger.warning(f"Removed stale agent {agent_id}")

class DiscoverableAgent:
    """Base class for discoverable agents"""
    
    def __init__(self, agent_id: str, agent_type: str, registry: AgentRegistry):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.registry = registry
        self.heartbeat_task = None
    
    async def start(self):
        """Start the agent and register with registry"""
        
        registration = AgentRegistration(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            name=self.get_name(),
            description=self.get_description(),
            version=self.get_version(),
            capabilities=self.get_capabilities(),
            endpoints=self.get_endpoints(),
            health_check_url=self.get_health_check_url(),
            metadata=self.get_metadata()
        )
        
        await self.registry.register_agent(registration)
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """Stop the agent and unregister"""
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        await self.registry.unregister_agent(self.agent_id)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        
        while True:
            try:
                await self.registry.update_heartbeat(self.agent_id)
                await asyncio.sleep(self.registry.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Retry in 5 seconds
    
    def get_name(self) -> str:
        """Get agent name (to be implemented by subclasses)"""
        return f"{self.agent_type}_agent"
    
    def get_description(self) -> str:
        """Get agent description (to be implemented by subclasses)"""
        return f"Custom {self.agent_type} agent"
    
    def get_version(self) -> str:
        """Get agent version (to be implemented by subclasses)"""
        return "1.0.0"
    
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities (to be implemented by subclasses)"""
        return []
    
    def get_endpoints(self) -> Dict[str, str]:
        """Get agent endpoints (to be implemented by subclasses)"""
        return {}
    
    def get_health_check_url(self) -> str:
        """Get health check URL (to be implemented by subclasses)"""
        return f"http://localhost:8000/health/{self.agent_id}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata (to be implemented by subclasses)"""
        return {}
```

### Version Control for Agents

#### Agent Versioning System

```python
"""
Version control system for agents
"""

@dataclass
class AgentVersion:
    """Agent version information"""
    agent_id: str
    version: str
    release_date: datetime
    changes: List[str]
    compatibility: Dict[str, str]  # Framework version compatibility
    deprecated: bool = False
    migration_notes: str = ""

class AgentVersionManager:
    """Manager for agent versions"""
    
    def __init__(self):
        self.versions: Dict[str, List[AgentVersion]] = {}
    
    def register_version(self, version: AgentVersion):
        """Register a new agent version"""
        
        if version.agent_id not in self.versions:
            self.versions[version.agent_id] = []
        
        self.versions[version.agent_id].append(version)
        
        # Sort by version (semantic versioning)
        self.versions[version.agent_id].sort(key=lambda v: self._parse_version(v.version))
    
    def get_latest_version(self, agent_id: str) -> Optional[AgentVersion]:
        """Get the latest version of an agent"""
        
        versions = self.versions.get(agent_id, [])
        active_versions = [v for v in versions if not v.deprecated]
        
        return active_versions[-1] if active_versions else None
    
    def get_compatible_version(self, agent_id: str, framework_version: str) -> Optional[AgentVersion]:
        """Get a compatible version for a framework version"""
        
        versions = self.versions.get(agent_id, [])
        
        for version in reversed(versions):  # Start with latest
            if not version.deprecated:
                required_version = version.compatibility.get("framework", "1.0.0")
                if self._is_compatible(framework_version, required_version):
                    return version
        
        return None
    
    def _parse_version(self, version: str) -> tuple:
        """Parse semantic version string"""
        return tuple(map(int, version.split('.')))
    
    def _is_compatible(self, current: str, required: str) -> bool:
        """Check if current version is compatible with required version"""
        current_parts = self._parse_version(current)
        required_parts = self._parse_version(required)
        
        # Major version must match, minor version must be >= required
        return (current_parts[0] == required_parts[0] and
                current_parts[1] >= required_parts[1])

class VersionedAgent:
    """Base class for versioned agents"""
    
    def __init__(self, agent_id: str, version: str, version_manager: AgentVersionManager):
        self.agent_id = agent_id
        self.version = version
        self.version_manager = version_manager
        self._register_version()
    
    def _register_version(self):
        """Register this agent version"""
        
        version_info = AgentVersion(
            agent_id=self.agent_id,
            version=self.version,
            release_date=datetime.now(),
            changes=self.get_version_changes(),
            compatibility=self.get_compatibility_info()
        )
        
        self.version_manager.register_version(version_info)
    
    def get_version_changes(self) -> List[str]:
        """Get changes in this version (to be implemented by subclasses)"""
        return []
    
    def get_compatibility_info(self) -> Dict[str, str]:
        """Get compatibility information (to be implemented by subclasses)"""
        return {"framework": "1.0.0"}
    
    async def check_for_updates(self) -> Optional[AgentVersion]:
        """Check if there's a newer version available"""
        
        latest = self.version_manager.get_latest_version(self.agent_id)
        
        if latest and latest.version != self.version:
            current_version = self.version_manager._parse_version(self.version)
            latest_version = self.version_manager._parse_version(latest.version)
            
            if latest_version > current_version:
                return latest
        
        return None
```

### Testing and Validation

#### Agent Testing Framework

```python
"""
Testing framework for custom agents
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List

class AgentTestCase:
    """Base class for agent test cases"""
    
    def __init__(self, agent_class, test_name: str):
        self.agent_class = agent_class
        self.test_name = test_name
        self.mock_memory = Mock()
        self.mock_orchestrator = Mock()
    
    async def setup(self):
        """Set up test environment"""
        # Create mock memory
        self.mock_memory.store_memory = AsyncMock(return_value=Mock(success=True, memory_id="test_id"))
        self.mock_memory.retrieve_memories = AsyncMock(return_value=Mock(success=True, data={"memories": []}))
        
        # Create agent instance
        self.agent = self.agent_class(self.mock_memory)
    
    async def teardown(self):
        """Clean up test environment"""
        if hasattr(self.agent, 'cleanup'):
            await self.agent.cleanup()

class SecurityAuditorAgentTest(AgentTestCase):
    """Test suite for CustomSecurityAuditorAgent"""
    
    def __init__(self):
        super().__init__(CustomSecurityAuditorAgent, "SecurityAuditorAgent")
    
    async def test_vulnerability_scan(self):
        """Test vulnerability scanning functionality"""
        await self.setup()
        
        # Test vulnerability scan
        result = await self.agent.execute_audit(
            audit_type=AuditType.VULNERABILITY_SCAN,
            target="test-app",
            context={"framework": "fastapi"}
        )
        
        # Assertions
        assert result.audit_type == AuditType.VULNERABILITY_SCAN
        assert len(result.findings) > 0
        assert result.compliance_score is not None
        assert result.recommendations is not None
        
        # Verify memory storage was called
        self.mock_memory.store_memory.assert_called()
        
        await self.teardown()
    
    async def test_penetration_test(self):
        """Test penetration testing functionality"""
        await self.setup()
        
        # Test penetration test
        result = await self.agent.execute_audit(
            audit_type=AuditType.PENETRATION_TEST,
            target="test-app",
            context={"target_url": "https://test.example.com"}
        )
        
        # Assertions
        assert result.audit_type == AuditType.PENETRATION_TEST
        assert len(result.findings) > 0
        assert all(f.get("attack_vector") for f in result.findings)
        
        await self.teardown()
    
    async def test_compliance_check(self):
        """Test compliance checking functionality"""
        await self.setup()
        
        # Test compliance check
        result = await self.agent.execute_audit(
            audit_type=AuditType.COMPLIANCE_CHECK,
            target="test-app",
            context={"standards": ["OWASP", "SOC2"]}
        )
        
        # Assertions
        assert result.audit_type == AuditType.COMPLIANCE_CHECK
        assert 0 <= result.compliance_score <= 1
        assert len(result.recommendations) > 0
        
        await self.teardown()

class AgentTestRunner:
    """Test runner for agent tests"""
    
    def __init__(self):
        self.test_cases: List[AgentTestCase] = []
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def add_test_case(self, test_case: AgentTestCase):
        """Add a test case"""
        self.test_cases.append(test_case)
    
    async def run_all_tests(self) -> Dict[str, Dict[str, Any]]:
        """Run all test cases"""
        
        for test_case in self.test_cases:
            await self._run_test_case(test_case)
        
        return self.results
    
    async def _run_test_case(self, test_case: AgentTestCase):
        """Run a single test case"""
        
        test_name = test_case.test_name
        self.results[test_name] = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        # Get all test methods
        test_methods = [method for method in dir(test_case) if method.startswith("test_")]
        
        for method_name in test_methods:
            try:
                method = getattr(test_case, method_name)
                await method()
                self.results[test_name]["passed"] += 1
                print(f"✓ {test_name}.{method_name}")
            except Exception as e:
                self.results[test_name]["failed"] += 1
                self.results[test_name]["errors"].append(f"{method_name}: {str(e)}")
                print(f"✗ {test_name}.{method_name}: {e}")

# Usage example
async def run_agent_tests():
    """Run all agent tests"""
    
    runner = AgentTestRunner()
    
    # Add test cases
    runner.add_test_case(SecurityAuditorAgentTest())
    # runner.add_test_case(OtherAgentTest())
    
    # Run tests
    results = await runner.run_all_tests()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"{test_name}: {result['passed']}/{total} passed")
        
        if result["errors"]:
            print("  Errors:")
            for error in result["errors"]:
                print(f"    - {error}")

if __name__ == "__main__":
    asyncio.run(run_agent_tests())
```

### Production Deployment Patterns

#### Deployment Configuration

```python
"""
Production deployment patterns for custom agents
"""

@dataclass
class DeploymentConfig:
    """Configuration for agent deployment"""
    
    # Environment settings
    environment: str = "production"
    log_level: str = "INFO"
    metrics_enabled: bool = True
    
    # Scaling settings
    min_instances: int = 1
    max_instances: int = 10
    cpu_threshold: float = 70.0
    memory_threshold: float = 80.0
    
    # Health check settings
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_retries: int = 3
    
    # Security settings
    tls_enabled: bool = True
    api_key_required: bool = True
    rate_limiting: Dict[str, int] = None
    
    # Monitoring settings
    monitoring_enabled: bool = True
    metrics_endpoint: str = "/metrics"
    tracing_enabled: bool = True

class ProductionAgent:
    """Base class for production-ready agents"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self.rate_limiter = RateLimiter(config.rate_limiting or {})
    
    async def start(self):
        """Start the agent in production mode"""
        
        # Initialize monitoring
        if self.config.monitoring_enabled:
            await self.metrics.start()
        
        # Start health checks
        await self.health_checker.start(
            interval=self.config.health_check_interval,
            timeout=self.config.health_check_timeout
        )
        
        logger.info(f"Agent started in {self.config.environment} mode")
    
    async def stop(self):
        """Stop the agent gracefully"""
        
        # Stop health checks
        await self.health_checker.stop()
        
        # Stop metrics collection
        if self.config.monitoring_enabled:
            await self.metrics.stop()
        
        logger.info("Agent stopped gracefully")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming requests with production safeguards"""
        
        # Rate limiting
        if not await self.rate_limiter.check_rate_limit(request.get("client_id", "unknown")):
            raise Exception("Rate limit exceeded")
        
        # Metrics
        start_time = time.time()
        
        try:
            # Process request
            result = await self._process_request(request)
            
            # Record success metrics
            self.metrics.record_request_success(time.time() - start_time)
            
            return result
            
        except Exception as e:
            # Record error metrics
            self.metrics.record_request_error(str(e))
            raise
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request (to be implemented by subclasses)"""
        raise NotImplementedError

class MetricsCollector:
    """Collects and exports metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def start(self):
        """Start metrics collection"""
        logger.info("Metrics collection started")
    
    async def stop(self):
        """Stop metrics collection"""
        logger.info("Metrics collection stopped")
    
    def record_request_success(self, response_time: float):
        """Record successful request"""
        self.request_count += 1
        self.success_count += 1
        self.response_times.append(response_time)
    
    def record_request_error(self, error: str):
        """Record request error"""
        self.request_count += 1
        self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "requests_total": self.request_count,
            "requests_successful": self.success_count,
            "requests_failed": self.error_count,
            "average_response_time": avg_response_time,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0
        }

class HealthChecker:
    """Health check implementation"""
    
    def __init__(self):
        self.healthy = True
        self.last_check = None
        self.check_task = None
    
    async def start(self, interval: int, timeout: int):
        """Start health checks"""
        self.check_task = asyncio.create_task(self._health_check_loop(interval, timeout))
    
    async def stop(self):
        """Stop health checks"""
        if self.check_task:
            self.check_task.cancel()
    
    async def _health_check_loop(self, interval: int, timeout: int):
        """Health check loop"""
        
        while True:
            try:
                # Perform health check
                self.healthy = await self._perform_health_check()
                self.last_check = datetime.now()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.healthy = False
                await asyncio.sleep(5)
    
    async def _perform_health_check(self) -> bool:
        """Perform actual health check"""
        # Implement health check logic
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "healthy": self.healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "uptime": time.time() - (self.last_check.timestamp() if self.last_check else time.time())
        }
```

## Real-World Examples

### Building a Custom Security Agent

Here's a complete example of building a custom security agent:

```python
"""
Real-world example: Custom Security Agent
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime
import hashlib

@dataclass
class SecurityFinding:
    """Security finding data structure"""
    finding_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # XSS, SQL_INJECTION, AUTHENTICATION, etc.
    title: str
    description: str
    location: str
    remediation: str
    references: List[str]
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None

class ComprehensiveSecurityAgent:
    """
    Comprehensive Security Agent
    Real-world implementation with multiple security analysis capabilities
    """
    
    def __init__(self, memory: ClaudePMMemory):
        self.memory = memory
        self.agent_id = "comprehensive_security_agent"
        self.version = "1.0.0"
        
        # Security analysis modules
        self.vulnerability_scanner = VulnerabilityScanner()
        self.static_analyzer = StaticCodeAnalyzer()
        self.dependency_checker = DependencyChecker()
        self.configuration_auditor = ConfigurationAuditor()
        
        # Reporting
        self.report_generator = SecurityReportGenerator()
        
        logger.info(f"ComprehensiveSecurityAgent v{self.version} initialized")
    
    async def perform_comprehensive_audit(self, target: str, 
                                        audit_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive security audit
        
        Args:
            target: Target application or codebase path
            audit_config: Configuration for the audit
            
        Returns:
            Comprehensive audit results
        """
        
        audit_id = self._generate_audit_id(target)
        logger.info(f"Starting comprehensive security audit {audit_id} for {target}")
        
        # Initialize audit context
        audit_context = {
            "audit_id": audit_id,
            "target": target,
            "config": audit_config,
            "start_time": datetime.now(),
            "findings": [],
            "summary": {}
        }
        
        try:
            # 1. Static Code Analysis
            if audit_config.get("static_analysis", True):
                static_findings = await self._perform_static_analysis(target, audit_context)
                audit_context["findings"].extend(static_findings)
            
            # 2. Dependency Vulnerability Check
            if audit_config.get("dependency_check", True):
                dependency_findings = await self._check_dependencies(target, audit_context)
                audit_context["findings"].extend(dependency_findings)
            
            # 3. Configuration Security Audit
            if audit_config.get("config_audit", True):
                config_findings = await self._audit_configuration(target, audit_context)
                audit_context["findings"].extend(config_findings)
            
            # 4. Dynamic Vulnerability Scanning (if URL provided)
            if audit_config.get("dynamic_scan", False) and audit_config.get("target_url"):
                dynamic_findings = await self._perform_dynamic_scan(
                    audit_config["target_url"], audit_context
                )
                audit_context["findings"].extend(dynamic_findings)
            
            # 5. Generate comprehensive report
            audit_context["summary"] = self._generate_audit_summary(audit_context["findings"])
            audit_context["end_time"] = datetime.now()
            
            # 6. Store results in memory
            await self._store_audit_results(audit_context)
            
            # 7. Generate reports
            report_paths = await self._generate_reports(audit_context)
            audit_context["reports"] = report_paths
            
            logger.info(f"Comprehensive audit {audit_id} completed with {len(audit_context['findings'])} findings")
            
            return audit_context
            
        except Exception as e:
            logger.error(f"Comprehensive audit failed: {e}")
            audit_context["error"] = str(e)
            audit_context["end_time"] = datetime.now()
            return audit_context
    
    async def _perform_static_analysis(self, target: str, 
                                     context: Dict[str, Any]) -> List[SecurityFinding]:
        """Perform static code analysis"""
        
        logger.info("Performing static code analysis")
        findings = []
        
        # Analyze Python files
        python_findings = await self.static_analyzer.analyze_python_code(target)
        findings.extend(python_findings)
        
        # Analyze JavaScript/TypeScript files
        js_findings = await self.static_analyzer.analyze_javascript_code(target)
        findings.extend(js_findings)
        
        # Analyze configuration files
        config_findings = await self.static_analyzer.analyze_config_files(target)
        findings.extend(config_findings)
        
        logger.info(f"Static analysis completed: {len(findings)} findings")
        return findings
    
    async def _check_dependencies(self, target: str, 
                                context: Dict[str, Any]) -> List[SecurityFinding]:
        """Check for vulnerable dependencies"""
        
        logger.info("Checking dependencies for vulnerabilities")
        findings = []
        
        # Check Python dependencies
        python_deps = await self.dependency_checker.check_python_dependencies(target)
        findings.extend(python_deps)
        
        # Check Node.js dependencies
        node_deps = await self.dependency_checker.check_node_dependencies(target)
        findings.extend(node_deps)
        
        logger.info(f"Dependency check completed: {len(findings)} vulnerable dependencies found")
        return findings
    
    async def _audit_configuration(self, target: str, 
                                 context: Dict[str, Any]) -> List[SecurityFinding]:
        """Audit configuration security"""
        
        logger.info("Auditing configuration security")
        findings = []
        
        # Check database configurations
        db_findings = await self.configuration_auditor.audit_database_config(target)
        findings.extend(db_findings)
        
        # Check web server configurations
        web_findings = await self.configuration_auditor.audit_web_config(target)
        findings.extend(web_findings)
        
        # Check environment variables
        env_findings = await self.configuration_auditor.audit_environment_config(target)
        findings.extend(env_findings)
        
        logger.info(f"Configuration audit completed: {len(findings)} findings")
        return findings
    
    async def _perform_dynamic_scan(self, target_url: str, 
                                  context: Dict[str, Any]) -> List[SecurityFinding]:
        """Perform dynamic vulnerability scanning"""
        
        logger.info(f"Performing dynamic scan on {target_url}")
        findings = []
        
        # Web vulnerability scanning
        web_findings = await self.vulnerability_scanner.scan_web_application(target_url)
        findings.extend(web_findings)
        
        # SSL/TLS configuration check
        ssl_findings = await self.vulnerability_scanner.check_ssl_configuration(target_url)
        findings.extend(ssl_findings)
        
        # HTTP security headers check
        header_findings = await self.vulnerability_scanner.check_security_headers(target_url)
        findings.extend(header_findings)
        
        logger.info(f"Dynamic scan completed: {len(findings)} findings")
        return findings
    
    def _generate_audit_summary(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Generate audit summary"""
        
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        category_counts = {}
        
        for finding in findings:
            severity_counts[finding.severity] += 1
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1
        
        # Calculate risk score
        risk_score = (
            severity_counts["CRITICAL"] * 10 +
            severity_counts["HIGH"] * 7 +
            severity_counts["MEDIUM"] * 4 +
            severity_counts["LOW"] * 1
        )
        
        return {
            "total_findings": len(findings),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "risk_score": risk_score,
            "risk_level": self._calculate_risk_level(risk_score),
            "compliance_score": self._calculate_compliance_score(findings)
        }
    
    def _calculate_risk_level(self, risk_score: int) -> str:
        """Calculate overall risk level"""
        if risk_score >= 50:
            return "CRITICAL"
        elif risk_score >= 30:
            return "HIGH"
        elif risk_score >= 15:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_compliance_score(self, findings: List[SecurityFinding]) -> float:
        """Calculate compliance score (0-1)"""
        if not findings:
            return 1.0
        
        total_weight = len(findings)
        penalty_weight = sum(
            10 if f.severity == "CRITICAL" else
            7 if f.severity == "HIGH" else
            4 if f.severity == "MEDIUM" else 1
            for f in findings
        )
        
        return max(0, 1 - (penalty_weight / (total_weight * 10)))
    
    async def _store_audit_results(self, audit_context: Dict[str, Any]):
        """Store audit results in memory"""
        
        # Store summary
        summary_content = f"""
Comprehensive Security Audit - {audit_context['audit_id']}

Target: {audit_context['target']}
Duration: {(audit_context['end_time'] - audit_context['start_time']).total_seconds():.2f} seconds

Summary:
- Total Findings: {audit_context['summary']['total_findings']}
- Risk Level: {audit_context['summary']['risk_level']}
- Risk Score: {audit_context['summary']['risk_score']}
- Compliance Score: {audit_context['summary']['compliance_score']:.2f}

Severity Distribution:
- Critical: {audit_context['summary']['severity_distribution']['CRITICAL']}
- High: {audit_context['summary']['severity_distribution']['HIGH']}
- Medium: {audit_context['summary']['severity_distribution']['MEDIUM']}
- Low: {audit_context['summary']['severity_distribution']['LOW']}
""".strip()
        
        await self.memory.store_memory(
            category=MemoryCategory.PATTERN,
            content=summary_content,
            metadata={
                "audit_id": audit_context["audit_id"],
                "target": audit_context["target"],
                "risk_level": audit_context["summary"]["risk_level"],
                "total_findings": audit_context["summary"]["total_findings"],
                "compliance_score": audit_context["summary"]["compliance_score"]
            },
            tags=["security", "audit", "comprehensive", audit_context["summary"]["risk_level"].lower()]
        )
        
        # Store critical findings
        critical_findings = [f for f in audit_context["findings"] if f.severity == "CRITICAL"]
        if critical_findings:
            critical_content = f"""
Critical Security Findings - {audit_context['audit_id']}

{chr(10).join([f"- {f.title}: {f.description}" for f in critical_findings[:5]])}

Immediate action required for {len(critical_findings)} critical findings.
""".strip()
            
            await self.memory.store_memory(
                category=MemoryCategory.ERROR,
                content=critical_content,
                metadata={
                    "audit_id": audit_context["audit_id"],
                    "finding_count": len(critical_findings),
                    "severity": "CRITICAL"
                },
                tags=["security", "critical", "audit", "immediate_action"]
            )
    
    async def _generate_reports(self, audit_context: Dict[str, Any]) -> Dict[str, str]:
        """Generate various report formats"""
        
        report_paths = {}
        
        # HTML Report
        html_report = await self.report_generator.generate_html_report(audit_context)
        report_paths["html"] = html_report
        
        # JSON Report
        json_report = await self.report_generator.generate_json_report(audit_context)
        report_paths["json"] = json_report
        
        # PDF Report
        pdf_report = await self.report_generator.generate_pdf_report(audit_context)
        report_paths["pdf"] = pdf_report
        
        # SARIF Report (for CI/CD integration)
        sarif_report = await self.report_generator.generate_sarif_report(audit_context)
        report_paths["sarif"] = sarif_report
        
        return report_paths
    
    def _generate_audit_id(self, target: str) -> str:
        """Generate unique audit ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_hash = hashlib.md5(target.encode()).hexdigest()[:8]
        return f"audit_{timestamp}_{target_hash}"

# Supporting classes for the security agent

class VulnerabilityScanner:
    """Vulnerability scanning implementation"""
    
    async def scan_web_application(self, url: str) -> List[SecurityFinding]:
        """Scan web application for vulnerabilities"""
        findings = []
        
        # Simulate vulnerability scanning
        await asyncio.sleep(2)
        
        # Example findings
        findings.append(SecurityFinding(
            finding_id="WEB_001",
            severity="HIGH",
            category="XSS",
            title="Cross-Site Scripting (XSS) vulnerability",
            description="Reflected XSS vulnerability in search parameter",
            location=f"{url}/search?q=<script>alert('xss')</script>",
            remediation="Implement input validation and output encoding",
            references=["https://owasp.org/www-community/attacks/xss/"],
            cvss_score=6.1
        ))
        
        return findings
    
    async def check_ssl_configuration(self, url: str) -> List[SecurityFinding]:
        """Check SSL/TLS configuration"""
        findings = []
        
        # Simulate SSL check
        await asyncio.sleep(1)
        
        # Example finding
        findings.append(SecurityFinding(
            finding_id="SSL_001",
            severity="MEDIUM",
            category="SSL_TLS",
            title="Weak SSL/TLS configuration",
            description="Server supports weak cipher suites",
            location=url,
            remediation="Disable weak cipher suites and enable only strong ones",
            references=["https://wiki.mozilla.org/Security/Server_Side_TLS"]
        ))
        
        return findings
    
    async def check_security_headers(self, url: str) -> List[SecurityFinding]:
        """Check HTTP security headers"""
        findings = []
        
        # Simulate header check
        await asyncio.sleep(0.5)
        
        # Example finding
        findings.append(SecurityFinding(
            finding_id="HDR_001",
            severity="LOW",
            category="SECURITY_HEADERS",
            title="Missing security headers",
            description="Missing Content-Security-Policy header",
            location=url,
            remediation="Add Content-Security-Policy header",
            references=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP"]
        ))
        
        return findings

class StaticCodeAnalyzer:
    """Static code analysis implementation"""
    
    async def analyze_python_code(self, target: str) -> List[SecurityFinding]:
        """Analyze Python code for security issues"""
        findings = []
        
        # Simulate code analysis
        await asyncio.sleep(1)
        
        # Example finding
        findings.append(SecurityFinding(
            finding_id="PY_001",
            severity="CRITICAL",
            category="HARDCODED_SECRETS",
            title="Hardcoded database password",
            description="Database password is hardcoded in source code",
            location=f"{target}/config/database.py:15",
            remediation="Move password to environment variables or secure configuration",
            references=["https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password"]
        ))
        
        return findings
    
    async def analyze_javascript_code(self, target: str) -> List[SecurityFinding]:
        """Analyze JavaScript code for security issues"""
        findings = []
        
        # Simulate JS analysis
        await asyncio.sleep(1)
        
        # Example finding
        findings.append(SecurityFinding(
            finding_id="JS_001",
            severity="HIGH",
            category="DOM_XSS",
            title="DOM-based XSS vulnerability",
            description="User input is directly inserted into DOM without sanitization",
            location=f"{target}/static/js/main.js:42",
            remediation="Sanitize user input before DOM manipulation",
            references=["https://owasp.org/www-community/attacks/DOM_Based_XSS"]
        ))
        
        return findings
    
    async def analyze_config_files(self, target: str) -> List[SecurityFinding]:
        """Analyze configuration files for security issues"""
        findings = []
        
        # Simulate config analysis
        await asyncio.sleep(0.5)
        
        # Example finding
        findings.append(SecurityFinding(
            finding_id="CFG_001",
            severity="MEDIUM",
            category="INSECURE_CONFIG",
            title="Debug mode enabled in production",
            description="Debug mode is enabled which can expose sensitive information",
            location=f"{target}/config/settings.py:8",
            remediation="Disable debug mode in production environment",
            references=["https://docs.djangoproject.com/en/stable/ref/settings/#debug"]
        ))
        
        return findings

# Usage example
async def main():
    """Example usage of the comprehensive security agent"""
    
    # Initialize memory
    memory = ClaudePMMemory()
    
    # Create security agent
    security_agent = ComprehensiveSecurityAgent(memory)
    
    # Configure audit
    audit_config = {
        "static_analysis": True,
        "dependency_check": True,
        "config_audit": True,
        "dynamic_scan": True,
        "target_url": "https://example.com",
        "report_formats": ["html", "json", "pdf"]
    }
    
    # Perform comprehensive audit
    results = await security_agent.perform_comprehensive_audit(
        target="/path/to/application",
        audit_config=audit_config
    )
    
    # Print summary
    print(f"Audit completed: {results['summary']['total_findings']} findings")
    print(f"Risk level: {results['summary']['risk_level']}")
    print(f"Compliance score: {results['summary']['compliance_score']:.2f}")
    
    # Print reports
    print("\nGenerated reports:")
    for format_type, path in results.get("reports", {}).items():
        print(f"  {format_type.upper()}: {path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Creating Domain-Specific Agents

#### E-commerce Agent Example

```python
"""
Domain-specific agent example: E-commerce Analytics Agent
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

class EcommerceMetricType(str, Enum):
    """Types of e-commerce metrics"""
    SALES_REVENUE = "sales_revenue"
    CONVERSION_RATE = "conversion_rate"
    AVERAGE_ORDER_VALUE = "average_order_value"
    CART_ABANDONMENT = "cart_abandonment"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    INVENTORY_TURNOVER = "inventory_turnover"
    RETURN_RATE = "return_rate"
    CUSTOMER_ACQUISITION_COST = "customer_acquisition_cost"

@dataclass
class EcommerceAnalysis:
    """E-commerce analysis result"""
    metric_type: EcommerceMetricType
    value: float
    trend: str  # "increasing", "decreasing", "stable"
    period: str
    insights: List[str]
    recommendations: List[str]
    data_quality_score: float

class EcommerceAnalyticsAgent:
    """
    E-commerce Analytics Agent
    Specialized in analyzing e-commerce metrics and providing business insights
    """
    
    def __init__(self, memory: ClaudePMMemory):
        self.memory = memory
        self.agent_id = "ecommerce_analytics_agent"
        self.specialization = "ecommerce_analytics"
        
        # Analytics modules
        self.sales_analyzer = SalesAnalyzer()
        self.customer_analyzer = CustomerAnalyzer()
        self.inventory_analyzer = InventoryAnalyzer()
        self.marketing_analyzer = MarketingAnalyzer()
        
        # Data connectors
        self.data_connectors = {
            "shopify": ShopifyConnector(),
            "woocommerce": WooCommerceConnector(),
            "magento": MagentoConnector(),
            "custom": CustomAPIConnector()
        }
    
    async def analyze_ecommerce_metrics(self, 
                                      platform: str,
                                      metrics: List[EcommerceMetricType],
                                      date_range: Dict[str, str]) -> Dict[str, EcommerceAnalysis]:
        """
        Analyze e-commerce metrics for the specified platform and date range
        
        Args:
            platform: E-commerce platform (shopify, woocommerce, etc.)
            metrics: List of metrics to analyze
            date_range: Date range for analysis
            
        Returns:
            Dictionary of analysis results by metric type
        """
        
        logger.info(f"Analyzing e-commerce metrics for {platform}")
        
        # Get data connector
        connector = self.data_connectors.get(platform)
        if not connector:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Fetch data
        raw_data = await connector.fetch_data(date_range)
        
        # Analyze each metric
        results = {}
        
        for metric in metrics:
            try:
                analysis = await self._analyze_metric(metric, raw_data, date_range)
                results[metric.value] = analysis
                
                # Store insights in memory
                await self._store_analysis_memory(platform, analysis)
                
            except Exception as e:
                logger.error(f"Failed to analyze {metric.value}: {e}")
                results[metric.value] = None
        
        return results
    
    async def _analyze_metric(self, 
                            metric: EcommerceMetricType,
                            data: Dict[str, Any],
                            date_range: Dict[str, str]) -> EcommerceAnalysis:
        """Analyze a specific metric"""
        
        if metric == EcommerceMetricType.SALES_REVENUE:
            return await self._analyze_sales_revenue(data, date_range)
        elif metric == EcommerceMetricType.CONVERSION_RATE:
            return await self._analyze_conversion_rate(data, date_range)
        elif metric == EcommerceMetricType.AVERAGE_ORDER_VALUE:
            return await self._analyze_average_order_value(data, date_range)
        elif metric == EcommerceMetricType.CART_ABANDONMENT:
            return await self._analyze_cart_abandonment(data, date_range)
        elif metric == EcommerceMetricType.CUSTOMER_LIFETIME_VALUE:
            return await self._analyze_customer_lifetime_value(data, date_range)
        else:
            raise ValueError(f"Unsupported metric: {metric}")
    
    async def _analyze_sales_revenue(self, data: Dict[str, Any], 
                                   date_range: Dict[str, str]) -> EcommerceAnalysis:
        """Analyze sales revenue metrics"""
        
        # Get sales data
        sales_data = data.get("sales", [])
        
        # Calculate metrics
        total_revenue = sum(sale.get("amount", 0) for sale in sales_data)
        
        # Get historical data for trend analysis
        historical_data = await self._get_historical_data("sales_revenue", date_range)
        trend = self._calculate_trend(total_revenue, historical_data)
        
        # Generate insights
        insights = []
        recommendations = []
        
        if trend == "increasing":
            insights.append("Sales revenue is trending upward")
            recommendations.append("Continue current marketing strategies")
        elif trend == "decreasing":
            insights.append("Sales revenue is declining")
            recommendations.append("Review pricing strategy and marketing campaigns")
        
        # Peak sales analysis
        peak_sales_day = max(sales_data, key=lambda x: x.get("amount", 0))
        insights.append(f"Peak sales day: {peak_sales_day.get('date')} with ${peak_sales_day.get('amount', 0):.2f}")
        
        # Category performance
        category_performance = self._analyze_category_performance(sales_data)
        insights.extend(category_performance)
        
        return EcommerceAnalysis(
            metric_type=EcommerceMetricType.SALES_REVENUE,
            value=total_revenue,
            trend=trend,
            period=f"{date_range['start']} to {date_range['end']}",
            insights=insights,
            recommendations=recommendations,
            data_quality_score=self._calculate_data_quality(sales_data)
        )
    
    async def _analyze_conversion_rate(self, data: Dict[str, Any], 
                                     date_range: Dict[str, str]) -> EcommerceAnalysis:
        """Analyze conversion rate metrics"""
        
        # Get traffic and conversion data
        sessions = data.get("sessions", 0)
        conversions = data.get("conversions", 0)
        
        # Calculate conversion rate
        conversion_rate = (conversions / sessions * 100) if sessions > 0 else 0
        
        # Get historical data
        historical_data = await self._get_historical_data("conversion_rate", date_range)
        trend = self._calculate_trend(conversion_rate, historical_data)
        
        # Generate insights
        insights = []
        recommendations = []
        
        if conversion_rate < 2.0:
            insights.append("Conversion rate is below industry average (2-3%)")
            recommendations.append("Optimize checkout process and product pages")
        elif conversion_rate > 5.0:
            insights.append("Conversion rate is above industry average")
            recommendations.append("Scale successful strategies to other products")
        
        # Channel analysis
        channel_performance = self._analyze_channel_performance(data.get("channels", []))
        insights.extend(channel_performance["insights"])
        recommendations.extend(channel_performance["recommendations"])
        
        return EcommerceAnalysis(
            metric_type=EcommerceMetricType.CONVERSION_RATE,
            value=conversion_rate,
            trend=trend,
            period=f"{date_range['start']} to {date_range['end']}",
            insights=insights,
            recommendations=recommendations,
            data_quality_score=self._calculate_data_quality([sessions, conversions])
        )
    
    async def generate_business_report(self, platform: str, 
                                     date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate comprehensive business report"""
        
        # Analyze all key metrics
        all_metrics = [
            EcommerceMetricType.SALES_REVENUE,
            EcommerceMetricType.CONVERSION_RATE,
            EcommerceMetricType.AVERAGE_ORDER_VALUE,
            EcommerceMetricType.CART_ABANDONMENT,
            EcommerceMetricType.CUSTOMER_LIFETIME_VALUE
        ]
        
        analysis_results = await self.analyze_ecommerce_metrics(
            platform, all_metrics, date_range
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(analysis_results)
        
        # Generate action items
        action_items = self._generate_action_items(analysis_results)
        
        # Generate forecasts
        forecasts = await self._generate_forecasts(analysis_results)
        
        report = {
            "report_id": f"ecommerce_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "platform": platform,
            "date_range": date_range,
            "executive_summary": executive_summary,
            "detailed_analysis": analysis_results,
            "action_items": action_items,
            "forecasts": forecasts,
            "generated_at": datetime.now().isoformat()
        }
        
        # Store report in memory
        await self._store_report_memory(report)
        
        return report
    
    def _generate_executive_summary(self, analysis_results: Dict[str, EcommerceAnalysis]) -> Dict[str, Any]:
        """Generate executive summary"""
        
        # Calculate overall performance score
        performance_scores = []
        for analysis in analysis_results.values():
            if analysis:
                if analysis.trend == "increasing":
                    performance_scores.append(100)
                elif analysis.trend == "stable":
                    performance_scores.append(75)
                else:
                    performance_scores.append(50)
        
        overall_score = sum(performance_scores) / len(performance_scores) if performance_scores else 0
        
        # Key highlights
        highlights = []
        concerns = []
        
        for metric, analysis in analysis_results.items():
            if analysis and analysis.trend == "increasing":
                highlights.append(f"{metric.replace('_', ' ').title()} is trending upward")
            elif analysis and analysis.trend == "decreasing":
                concerns.append(f"{metric.replace('_', ' ').title()} is declining")
        
        return {
            "overall_performance_score": overall_score,
            "performance_level": "Excellent" if overall_score >= 85 else "Good" if overall_score >= 70 else "Needs Improvement",
            "key_highlights": highlights,
            "areas_of_concern": concerns
        }
    
    def _generate_action_items(self, analysis_results: Dict[str, EcommerceAnalysis]) -> List[Dict[str, Any]]:
        """Generate prioritized action items"""
        
        action_items = []
        
        for metric, analysis in analysis_results.items():
            if analysis and analysis.recommendations:
                for recommendation in analysis.recommendations:
                    priority = "High" if analysis.trend == "decreasing" else "Medium"
                    
                    action_items.append({
                        "metric": metric,
                        "action": recommendation,
                        "priority": priority,
                        "expected_impact": "High" if priority == "High" else "Medium"
                    })
        
        # Sort by priority
        action_items.sort(key=lambda x: 0 if x["priority"] == "High" else 1)
        
        return action_items
```

This comprehensive custom agent development guide provides:

1. **Complete agent architecture understanding**
2. **Step-by-step development process**
3. **Advanced features like memory integration, cross-agent communication, and event handling**
4. **Production deployment patterns**
5. **Real-world examples with working code**
6. **Testing and validation frameworks**
7. **Security and performance considerations**

The guide covers everything needed to create sophisticated custom agents that integrate seamlessly with the CMPM framework while providing domain-specific capabilities.

## Template System Integration

### Agent Template Management

The CMPM v4.2.0 framework includes an enhanced template system for rapid agent development:

#### Template Directory Structure

```
~/.claude-multiagent-pm/templates/
├── agents/
│   ├── basic-agent-template.md           # Basic agent template
│   ├── specialized-agent-template.md     # Specialized agent template
│   └── multi-domain-agent-template.md    # Multi-domain agent template
├── configurations/
│   ├── agent-config-template.yaml        # Agent configuration template
│   └── workflow-template.yaml            # Workflow configuration template
└── examples/
    ├── data-analysis-agent.md            # Data analysis agent example
    └── security-audit-agent.md           # Security audit agent example
```

#### Using Templates

1. **Create Agent from Template**:
   ```bash
   # Copy template to user-defined directory
   cp ~/.claude-multiagent-pm/templates/agents/basic-agent-template.md \
      ~/.claude-multiagent-pm/agents/user-defined/my-new-agent.md
   
   # Customize the agent definition
   vim ~/.claude-multiagent-pm/agents/user-defined/my-new-agent.md
   ```

2. **Template Variables**:
   Templates support variable substitution for rapid customization:
   ```yaml
   # Template variables
   agent_name: "{{AGENT_NAME}}"
   specialization: "{{SPECIALIZATION}}"
   domain_focus: "{{DOMAIN_FOCUS}}"
   ```

3. **Template Generation**:
   ```bash
   # Generate agent from template with variables
   claude-pm generate agent --template=basic-agent-template \
     --name="data-processor" \
     --specialization="data-analysis" \
     --domain="financial-data"
   ```

### Template Best Practices

1. **Template Naming**: Use descriptive names that indicate the agent's purpose
2. **Variable Consistency**: Maintain consistent variable naming across templates
3. **Documentation**: Include comprehensive documentation within templates
4. **Version Control**: Track template changes and maintain compatibility

This template system enables rapid agent development while maintaining consistency and best practices across all user-defined agents.

---

**Framework Version**: 4.2.0  
**Last Updated**: 2025-07-09  
**Documentation Version**: 2.0.0  
**Author**: Claude Technical Documentation Agent  
**Review Status**: Ready for Production Use

---

*This custom agent development guide provides comprehensive information for creating, testing, and deploying user-defined agents within the CMPM framework. For additional support, please refer to the framework documentation or contact the development team.*