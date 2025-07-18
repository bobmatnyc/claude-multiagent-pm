# Claude PM Framework - Local Python Orchestration System Design Document

## Executive Summary

This document outlines the design and implementation of a local Python orchestration system for the Claude PM Framework. The system addresses critical token limit issues caused by subprocess delegation while maintaining **100% backwards compatibility** with existing framework functionality.

## Problem Statement

### Current Issue
The Claude PM Framework currently uses subprocess delegation where each agent receives the full context:
- **Context Multiplication**: 10 agents × 50k tokens = 500k token consumption per workflow
- **Monthly Usage Explosion**: Aggregate token usage exceeds individual usage by 10x
- **Plan Limit Breaches**: Users hit monthly token limits due to context duplication
- **Cost Inefficiency**: Same context sent multiple times instead of filtered context

### Business Impact
- Users exhaust monthly token allowances quickly
- Framework becomes cost-prohibitive for regular use
- Competitive disadvantage due to inefficient token usage
- User adoption blocked by usage plan limitations

## Solution Overview

### Local Python Orchestration (Claude.md Triggered)
Replace subprocess delegation with local Python orchestration that:
- **Maintains 100% Backwards Compatibility**: No changes to existing workflows
- **Claude.md Triggered**: Activated by project-specific instructions
- **Eliminates Context Duplication**: Each agent gets only relevant context slice
- **Reduces Monthly Token Usage**: 80-90% reduction in aggregate token consumption
- **Manages State**: Local state management for agent coordination
- **Serial Execution**: Focus on core concept validation first
- **Uses Established Patterns**: Simple asyncio message passing

## Architecture Design

### 1. System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main Claude   │    │  Orchestrator   │    │   Message Bus   │
│  (PM Context)   │◄──►│   (Python)      │◄──►│   (asyncio)     │
│                 │    │                 │    │                 │
│ - Reads Claude.md│    │ - Agent loading │    │ - Request/resp  │
│ - Detects mode   │    │ - Context filter│    │ - Handler reg   │
│ - Delegates      │    │ - Serial exec   │    │ - Simple routing│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Context Manager │    │  Agent Workers  │
                       │   (Filtering)   │    │   (Mock Claude) │
                       │                 │    │                 │
                       │ - Agent filters │    │ - Profile aware │
                       │ - Shared context│    │ - Task handling │
                       │ - History mgmt  │    │ - Response fmt  │
                       └─────────────────┘    └─────────────────┘
```

### 2. Backwards Compatibility Strategy

#### No Breaking Changes
- **Existing Code**: All existing Python code remains unchanged
- **Existing Workflows**: Subprocess delegation continues to work
- **Existing APIs**: All APIs maintain same signatures
- **Existing Tests**: All tests continue to pass

#### Additive Enhancement
- **New Files Only**: All orchestration code in new files
- **Conditional Logic**: Orchestration activated only when Claude.md contains specific instructions
- **Fallback Mechanism**: Automatic fallback to subprocess delegation if orchestration fails

### 3. Claude.md Integration

#### Detection Logic
```python
# orchestration_detector.py
def detect_orchestration_mode(claude_md_content: str) -> str:
    """Detect orchestration mode from Claude.md content"""
    if 'CLAUDE_PM_ORCHESTRATION' in claude_md_content:
        return 'claude-pm'
    return 'claude-subprocess'
```

#### Claude.md Instructions Block
```markdown
# Claude PM Framework Instructions

## Claude PM Orchestration Mode
**CLAUDE_PM_ORCHESTRATION**: ENABLED

### Orchestration Instructions
- **USE Claude PM orchestration for all agent coordination**
- **DO NOT use built-in subprocess delegation tools**
- **DELEGATE tasks using orchestrator.delegate_to_agent(agent_type, task)**
- **EXECUTE tasks serially with context updates between agents**
- **FILTER context per agent type before delegation**

### Available Commands
- `orchestrator.delegate_to_agent(agent_type, task)` - Delegate task to specific agent
- `orchestrator.get_agent_status(agent_type)` - Get agent status
- `orchestrator.print_context_summary()` - Show context filtering

### Testing Tasks
1. **Documentation Task**: Generate comprehensive project README
2. **QA Task**: Run comprehensive test suite and report results
3. **Security Task**: Perform security scan and report findings
4. **Integration Task**: Demonstrate context sharing between agents

### Success Indicators
- ✓ Agents start successfully
- ✓ Context filtering working (different context per agent)
- ✓ Task delegation successful
- ✓ Information returned from agents
- ✓ Context updated between agent calls
```

## Implementation Specification

### 1. Orchestration Detection System

```python
# orchestration_detector.py
import os
import re
from typing import Optional

class OrchestrationDetector:
    """Detects orchestration mode from Claude.md content"""
    
    @staticmethod
    def detect_mode() -> str:
        """Detect orchestration mode from project Claude.md"""
        claude_md_path = os.path.join(os.getcwd(), '.claude-pm', 'CLAUDE.md')
        
        if not os.path.exists(claude_md_path):
            return 'claude-subprocess'
        
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for orchestration mode marker
            if 'CLAUDE_PM_ORCHESTRATION' in content and 'ENABLED' in content:
                return 'claude-pm'
                
        except Exception as e:
            print(f"Error reading Claude.md: {e}")
        
        return 'claude-subprocess'
    
    @staticmethod
    def get_orchestration_instructions() -> Optional[str]:
        """Extract orchestration instructions from Claude.md"""
        claude_md_path = os.path.join(os.getcwd(), '.claude-pm', 'CLAUDE.md')
        
        if not os.path.exists(claude_md_path):
            return None
        
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract orchestration section
            match = re.search(
                r'## Claude PM Orchestration Mode.*?(?=##|$)', 
                content, 
                re.DOTALL
            )
            
            if match:
                return match.group(0)
                
        except Exception as e:
            print(f"Error extracting orchestration instructions: {e}")
        
        return None
```

### 2. Backwards Compatible Integration

```python
# orchestration_integration.py
from typing import Dict, Any, Optional
from orchestration_detector import OrchestrationDetector

class BackwardsCompatibleOrchestrator:
    """Maintains 100% backwards compatibility with existing workflows"""
    
    def __init__(self):
        self.mode = OrchestrationDetector.detect_mode()
        self.orchestrator = None
        
        # Only initialize if orchestration mode is enabled
        if self.mode == 'claude-pm':
            try:
                from agent_orchestrator import AgentOrchestrator
                self.orchestrator = AgentOrchestrator('claude-pm')
                print("✓ Claude PM orchestration enabled")
            except ImportError as e:
                print(f"⚠ Orchestration not available: {e}")
                self.mode = 'claude-subprocess'
                self.orchestrator = None
    
    async def delegate_to_agent(self, agent_type: str, task: str) -> Dict[str, Any]:
        """Delegate task with automatic mode detection"""
        if self.mode == 'claude-pm' and self.orchestrator:
            try:
                return await self.orchestrator.delegate_to_agent(agent_type, task)
            except Exception as e:
                print(f"⚠ Orchestration failed, falling back to subprocess: {e}")
                return await self._subprocess_delegate(agent_type, task)
        else:
            return await self._subprocess_delegate(agent_type, task)
    
    async def _subprocess_delegate(self, agent_type: str, task: str) -> Dict[str, Any]:
        """Fallback to existing subprocess delegation"""
        # This calls your existing subprocess delegation code
        # No changes to existing functionality
        return {
            'agent_type': agent_type,
            'task': task,
            'result': f'Subprocess delegation result for {agent_type}: {task}',
            'status': 'completed',
            'mode': 'claude-subprocess'
        }
    
    def get_agent_status(self, agent_type: str) -> Dict[str, Any]:
        """Get agent status with mode awareness"""
        if self.mode == 'claude-pm' and self.orchestrator:
            return {
                'agent_type': agent_type,
                'mode': 'claude-pm',
                'orchestration_enabled': True
            }
        else:
            return {
                'agent_type': agent_type,
                'mode': 'claude-subprocess',
                'orchestration_enabled': False
            }
    
    def print_context_summary(self):
        """Print context summary for debugging"""
        if self.mode == 'claude-pm' and self.orchestrator:
            self.orchestrator.context_manager.print_context_summary()
        else:
            print("Context summary not available in subprocess mode")

# Global instance for backwards compatibility
orchestrator = BackwardsCompatibleOrchestrator()
```

### 3. Framework Integration Point

```python
# framework_integration.py
import asyncio
from orchestration_integration import orchestrator

# This replaces or enhances your existing agent delegation code
async def delegate_to_agent(agent_type: str, task: str) -> Dict[str, Any]:
    """Enhanced agent delegation with automatic orchestration"""
    return await orchestrator.delegate_to_agent(agent_type, task)

def get_agent_status(agent_type: str) -> Dict[str, Any]:
    """Enhanced agent status with orchestration awareness"""
    return orchestrator.get_agent_status(agent_type)

def print_context_summary():
    """Enhanced context summary with orchestration support"""
    orchestrator.print_context_summary()

# Backwards compatible aliases
async def claude_delegate_to_agent(agent_type: str, task: str) -> Dict[str, Any]:
    """Backwards compatible alias"""
    return await delegate_to_agent(agent_type, task)
```

### 2. Message Bus Implementation (Minimal)

```python
# message_bus.py
import asyncio
import uuid
from typing import Dict, Any, Callable

class SimpleMessageBus:
    def __init__(self):
        self.channels = {}
        self.pending_requests = {}
        
    async def request_response(self, channel: str, request: Dict[str, Any], timeout: int = 30):
        """Send request and wait for response"""
        request_id = str(uuid.uuid4())
        request['request_id'] = request_id
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_requests[request_id] = response_future
        
        # Send request to channel handler
        if channel in self.channels:
            asyncio.create_task(self.channels[channel](request))
        
        try:
            # Wait for response
            return await asyncio.wait_for(response_future, timeout=timeout)
        finally:
            # Cleanup
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
    
    def register_handler(self, channel: str, handler: Callable):
        """Register handler for channel"""
        self.channels[channel] = handler
    
    async def send_response(self, request_id: str, response: Dict[str, Any]):
        """Send response back to waiting request"""
        if request_id in self.pending_requests:
            if not self.pending_requests[request_id].done():
                self.pending_requests[request_id].set_result(response)

# Global message bus instance
message_bus = SimpleMessageBus()
```

### 3. Agent Orchestrator Implementation (Serial Only)

```python
# agent_orchestrator.py
import asyncio
from typing import Dict, Any, Optional
from message_bus import message_bus
from context_manager import ContextManager
from claude_pm.core.agent_registry import AgentRegistry

class AgentOrchestrator:
    def __init__(self, orchestration_mode: str = 'claude-subprocess'):
        self.mode = orchestration_mode
        self.agent_registry = AgentRegistry()
        self.context_manager = ContextManager()
        self.active_agents = set()
        
    async def delegate_to_agent(self, agent_type: str, task: str, context_filter: Optional[str] = None):
        """Delegate task to specific agent"""
        if self.mode == 'claude-subprocess':
            # Use existing subprocess delegation
            return await self._claude_subprocess_delegate(agent_type, task)
        else:
            return await self._claude_pm_delegate(agent_type, task, context_filter)
    
    async def _claude_pm_delegate(self, agent_type: str, task: str, context_filter: Optional[str] = None):
        """Local Python agent delegation"""
        print(f"Delegating to {agent_type} agent: {task}")
        
        # Ensure agent worker is running
        if agent_type not in self.active_agents:
            await self._start_agent_worker(agent_type)
        
        # Get agent profile from registry
        agent_profile = self.agent_registry.get_agent(agent_type)
        
        # Get filtered context
        filtered_context = self.context_manager.get_agent_context(agent_type, context_filter)
        
        print(f"Context size for {agent_type}: {len(str(filtered_context))} characters")
        
        # Create agent message
        agent_message = {
            'type': 'task_request',
            'agent_type': agent_type,
            'task': task,
            'context': filtered_context,
            'profile': agent_profile
        }
        
        # Send to agent worker
        response = await message_bus.request_response(
            f'agent_{agent_type}', 
            agent_message,
            timeout=30
        )
        
        print(f"Response from {agent_type}: {response.get('status', 'unknown')}")
        
        # Update context with response
        self.context_manager.update_context(agent_type, response)
        
        return response
    
    async def _start_agent_worker(self, agent_type: str):
        """Start agent worker if not already running"""
        if agent_type not in self.active_agents:
            from agent_worker import AgentWorker
            worker = AgentWorker(agent_type)
            
            # Register worker handler
            message_bus.register_handler(f'agent_{agent_type}', worker.handle_task)
            
            self.active_agents.add(agent_type)
            print(f"Started {agent_type} agent worker")
    
    async def _claude_subprocess_delegate(self, agent_type: str, task: str):
        """Fallback to existing subprocess delegation"""
        print(f"Using subprocess delegation for {agent_type}: {task}")
        
        # This would call your existing subprocess delegation code
        return {
            'agent_type': agent_type,
            'task': task,
            'result': f'Subprocess result for {agent_type}: {task}',
            'status': 'completed'
        }
```

### 4. Context Manager Implementation (Simplified)

```python
# context_manager.py
from typing import Dict, Any, Optional
import json

class ContextManager:
    def __init__(self):
        self.shared_context = {
            'project_info': {
                'name': 'claude-pm-framework',
                'version': '0.9.0',
                'description': 'Multi-agent orchestration framework'
            },
            'current_task': '',
            'code_files': ['agent_orchestrator.py', 'message_bus.py', 'context_manager.py'],
            'test_files': ['test_orchestration.py'],
            'config_files': ['claude.md', 'pyproject.toml'],
            'docs': ['README.md', 'user-guide.md'],
            'dependencies': ['asyncio', 'typing', 'json']
        }
        self.agent_contexts = {}
        
        # Simple context filters - each agent gets specific data
        self.context_filters = {
            'Documentation': ['project_info', 'docs', 'code_files'],
            'QA': ['test_files', 'code_files', 'project_info'],
            'Security': ['config_files', 'dependencies', 'code_files'],
            'Engineer': ['code_files', 'project_info', 'dependencies'],
            'Ops': ['config_files', 'dependencies', 'project_info']
        }
    
    def get_agent_context(self, agent_type: str, context_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get filtered context for specific agent"""
        # Start with basic context
        agent_context = {
            'agent_type': agent_type,
            'current_task': self.shared_context.get('current_task', ''),
        }
        
        # Apply agent-specific context filter
        if agent_type in self.context_filters:
            filtered_data = {}
            for key in self.context_filters[agent_type]:
                if key in self.shared_context:
                    filtered_data[key] = self.shared_context[key]
            agent_context['filtered_data'] = filtered_data
        
        # Add agent-specific history (last 3 interactions)
        if agent_type in self.agent_contexts:
            agent_context['agent_history'] = self.agent_contexts[agent_type][-3:]
        
        return agent_context
    
    def update_context(self, agent_type: str, result: Dict[str, Any]):
        """Update context with agent result"""
        if agent_type not in self.agent_contexts:
            self.agent_contexts[agent_type] = []
        
        # Store agent result
        self.agent_contexts[agent_type].append({
            'task': result.get('task', ''),
            'result': result.get('result', ''),
            'status': result.get('status', 'unknown')
        })
        
        # Update shared context if result contains updates
        if 'shared_updates' in result:
            self.shared_context.update(result['shared_updates'])
    
    def get_context_size(self, agent_type: str) -> int:
        """Get approximate context size for agent"""
        context = self.get_agent_context(agent_type)
        return len(json.dumps(context))
    
    def print_context_summary(self):
        """Print context summary for debugging"""
        print("\n=== Context Summary ===")
        print(f"Shared context keys: {list(self.shared_context.keys())}")
        for agent_type, filter_keys in self.context_filters.items():
            context_size = self.get_context_size(agent_type)
            print(f"{agent_type}: {filter_keys} ({context_size} chars)")
```

### 5. Agent Worker Implementation (Simplified)

```python
# agent_worker.py
import json
import time
from typing import Dict, Any
from message_bus import message_bus

class AgentWorker:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        
    async def handle_task(self, message: Dict[str, Any]):
        """Handle incoming task with filtered context"""
        print(f"\n{self.agent_type} Agent received task: {message['task']}")
        
        try:
            # Create focused prompt
            prompt = self.create_agent_prompt(
                message['task'],
                message['context'],
                message['profile']
            )
            
            print(f"{self.agent_type} Agent prompt size: {len(prompt)} characters")
            
            # Simulate Claude API call
            response = await self.call_claude_api(prompt)
            
            # Parse response
            result = self.parse_agent_response(response)
            
            print(f"{self.agent_type} Agent completed task successfully")
            
            # Send response back
            await message_bus.send_response(
                message['request_id'],
                {
                    'agent_type': self.agent_type,
                    'task': message['task'],
                    'result': result,
                    'status': 'completed',
                    'context_size': len(prompt)
                }
            )
            
        except Exception as e:
            print(f"{self.agent_type} Agent error: {str(e)}")
            
            # Send error response
            await message_bus.send_response(
                message['request_id'],
                {
                    'agent_type': self.agent_type,
                    'task': message['task'],
                    'error': str(e),
                    'status': 'failed'
                }
            )
    
    async def call_claude_api(self, prompt: str) -> str:
        """Mock Claude API call - replace with actual implementation"""
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Generate mock response based on agent type
        mock_responses = {
            'Documentation': 'Generated comprehensive documentation for the project',
            'QA': 'Ran all tests successfully - 15 passed, 0 failed',
            'Security': 'Security scan completed - no vulnerabilities found',
            'Engineer': 'Code implementation completed with proper error handling',
            'Ops': 'Deployment configuration validated and updated'
        }
        
        base_response = mock_responses.get(self.agent_type, f'{self.agent_type} task completed')
        
        return f"""{{
    "result": "{base_response}",
    "shared_updates": {{"last_update": "{time.time()}", "agent": "{self.agent_type}"}},
    "next_actions": ["Review results", "Continue with next task"],
    "recommendations": ["Consider running related tasks"]
}}"""
    
    def create_agent_prompt(self, task: str, context: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """Create focused prompt for this agent"""
        # Show filtered context for debugging
        filtered_keys = list(context.get('filtered_data', {}).keys())
        
        return f"""You are a {self.agent_type} agent.

Your capabilities: {profile.get('capabilities', 'General agent capabilities')}

Task: {task}

Context available to you: {filtered_keys}
Context data: {json.dumps(context.get('filtered_data', {}), indent=2)}

Project info: {context.get('project_info', {})}

Previous interactions: {len(context.get('agent_history', []))} items

Respond in JSON format with:
- result: Your main response
- shared_updates: Info to share with other agents
- next_actions: Follow-up actions needed
- recommendations: Recommendations for other agents
"""
    
    def parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse agent response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'result': response,
                'shared_updates': {},
                'next_actions': [],
                'recommendations': []
            }
```

### 6. CLI Implementation

### 6. Test Project Claude.md Template

```markdown
# Test Project - Claude PM Framework with Local Orchestration

## Project Overview
This is a test project to validate the Claude PM Framework's local Python orchestration capabilities.

## Claude PM Orchestration Mode
**CLAUDE_PM_ORCHESTRATION**: ENABLED

### Orchestration Instructions
- **USE Claude PM orchestration for all agent coordination**
- **DO NOT use built-in subprocess delegation tools**
- **DELEGATE tasks using orchestrator.delegate_to_agent(agent_type, task)**
- **EXECUTE tasks serially with context updates between agents**
- **FILTER context per agent type before delegation**

### Available Commands
- `orchestrator.delegate_to_agent(agent_type, task)` - Delegate task to specific agent
- `orchestrator.get_agent_status(agent_type)` - Get agent status
- `orchestrator.print_context_summary()` - Show context filtering

### Test Scenario Tasks

#### Phase 1: Individual Agent Testing
1. **Documentation Agent**: "Generate a comprehensive README.md for this test project including setup instructions and usage examples"
2. **QA Agent**: "Create a test plan for validating the orchestration system and run basic functionality tests"
3. **Security Agent**: "Perform security analysis on the orchestration system and identify potential vulnerabilities"

#### Phase 2: Context Sharing Validation
4. **Engineer Agent**: "Review the documentation generated and implement any missing code examples"
5. **Documentation Agent**: "Update the README with the code examples created by the Engineer agent"
6. **QA Agent**: "Test the code examples and report on their functionality"

#### Phase 3: Integration Testing
7. **Ops Agent**: "Create deployment configuration for the orchestration system"
8. **Security Agent**: "Review the deployment configuration for security best practices"
9. **Documentation Agent**: "Document the deployment process and security considerations"

### Success Criteria
- ✓ All agents start successfully without errors
- ✓ Context filtering working (each agent gets different context)
- ✓ Task delegation successful with proper responses
- ✓ Information returned from agents to orchestrator
- ✓ Context updated between agent calls
- ✓ Agents can reference previous agent outputs
- ✓ No monthly token usage issues with multiple agents

### Expected Behavior
When you run tasks in this project, the system should:
1. **Detect orchestration mode** from this Claude.md file
2. **Initialize Claude PM orchestration** instead of subprocess delegation
3. **Filter context** per agent type before delegation
4. **Execute tasks serially** with context propagation
5. **Return detailed results** including context size and agent status

### Debug Information
- Show context filtering in action
- Display agent startup messages
- Report context sizes per agent
- Show agent communication flow
- Validate backwards compatibility

## Testing Instructions

To test the orchestration system, start with Phase 1 tasks:

1. Ask Claude to delegate the Documentation task
2. Observe the orchestration system startup
3. Check that context filtering is working
4. Verify the agent responds appropriately
5. Continue with remaining tasks to test context sharing

Example prompt:
"Please delegate the Documentation task from Phase 1 to generate a comprehensive README for this test project. Show me the Claude PM orchestration system in action."
```
```

## Testing Strategy

### 1. Development Testing (Python Code)

**Location**: Develop in main Claude PM Framework project
**Purpose**: Debug and validate Python orchestration components

```python
# test_orchestration_dev.py
import asyncio
from orchestration_integration import orchestrator

async def test_development():
    """Test orchestration during development"""
    print("=== Development Testing ===\n")
    
    # Test mode detection
    mode = orchestrator.mode
    print(f"Detected orchestration mode: {mode}")
    
    # Test agent delegation
    result = await orchestrator.delegate_to_agent('Documentation', 'Test task')
    print(f"Delegation result: {result}")
    
    # Test context filtering
    orchestrator.print_context_summary()

if __name__ == "__main__":
    asyncio.run(test_development())
```

### 2. Integration Testing (Claude Interface)

**Location**: Separate test project with orchestration Claude.md
**Purpose**: Test full Claude PM Framework integration

#### Test Project Setup
1. Create new test project directory
2. Initialize with Claude PM Framework
3. Add orchestration-enabled Claude.md (see template above)
4. Test with Claude prompts

#### Test Prompts for Claude

**Phase 1: Basic Orchestration**
```
"Please delegate the Documentation task from Phase 1 to generate a comprehensive README for this test project. Show me the orchestration system in action and confirm that context filtering is working."
```

**Phase 2: Context Sharing**
```
"Now delegate the QA task to create a test plan. The QA agent should be able to reference the documentation that was just generated. Show me how context is shared between agents."
```

**Phase 3: Multi-Agent Flow**
```
"Execute the complete Phase 2 workflow: Engineer agent reviews documentation, Documentation agent updates with code examples, and QA agent tests the examples. Demonstrate the full orchestration flow."
```

### 3. Expected Test Results

#### Successful Orchestration Indicators
```
✓ Orchestration mode detected: claude-pm
✓ Local Python orchestration enabled
✓ Started Documentation agent worker
✓ Documentation Agent received task: Generate comprehensive README
✓ Documentation Agent prompt size: 387 characters
✓ Documentation Agent completed task successfully
✓ Response from Documentation: completed
✓ Context updated with agent result
```

### Context Filtering Validation
```
=== Token Usage Comparison ===
Subprocess Delegation (Current):
- Documentation Agent: 50,000 tokens (full context)
- QA Agent: 50,000 tokens (full context)
- Security Agent: 50,000 tokens (full context)
- Total: 150,000 tokens

Local Orchestration (New):
- Documentation Agent: 12,000 tokens (filtered context)
- QA Agent: 8,000 tokens (filtered context)
- Security Agent: 10,000 tokens (filtered context)
- Total: 30,000 tokens

Token Savings: 120,000 tokens (80% reduction)
```

#### Agent Communication Flow
```
Delegating to Documentation agent: Generate comprehensive README
Context size for Documentation: 245 characters
Documentation result: Generated comprehensive documentation for the project
Delegating to QA agent: Create test plan
Context size for QA: 198 characters
QA result: Created comprehensive test plan with 15 test cases
```

### 4. Backwards Compatibility Validation

#### Fallback Testing
- Test with orchestration disabled (no LOCAL_PYTHON_ORCHESTRATION in Claude.md)
- Verify subprocess delegation still works
- Test error handling when orchestration fails

#### Existing Workflow Testing
- Run existing framework commands
- Verify no breaking changes
- Test all existing agent types

## Migration Strategy

### Phase 1: Development (Week 1)
**Location**: Main Claude PM Framework project
**Goal**: Implement orchestration components

- [ ] Create orchestration_detector.py with Claude.md parsing
- [ ] Implement BackwardsCompatibleOrchestrator with fallback
- [ ] Add SimpleMessageBus, ContextManager, AgentWorker
- [ ] Create framework_integration.py with existing API compatibility
- [ ] Test with development test script

### Phase 2: Integration Testing (Week 2)
**Location**: Separate test project
**Goal**: Validate Claude interface integration

- [ ] Create test project with orchestration Claude.md
- [ ] Test basic agent delegation from Claude prompts
- [ ] Validate context filtering with different agent types
- [ ] Test multi-agent workflows with context sharing
- [ ] Verify backwards compatibility with subprocess fallback

### Phase 3: Real-world Testing (Week 3)
**Location**: Production-like test project
**Goal**: Validate production readiness

- [ ] Test with larger context sizes
- [ ] Validate error handling and recovery
- [ ] Test with all 9 core agent types
- [ ] Performance testing with serial execution
- [ ] Stress testing with context updates

### Phase 4: Documentation and Rollout (Week 4)
**Goal**: Prepare for wider adoption

- [ ] Update framework documentation
- [ ] Create orchestration user guide
- [ ] Add troubleshooting guide
- [ ] Prepare rollout strategy for existing users

## Implementation Files

### Core Files (Main Project)
```
claude_pm/
├── orchestration/
│   ├── __init__.py
│   ├── orchestration_detector.py      # Claude.md parsing
│   ├── orchestration_integration.py   # Backwards compatible wrapper
│   ├── message_bus.py                 # Simple async message bus
│   ├── context_manager.py             # Context filtering
│   ├── agent_orchestrator.py          # Agent coordination
│   └── agent_worker.py                # Agent task handling
├── framework_integration.py           # API compatibility layer
└── test_orchestration_dev.py          # Development testing
```

### Test Project Files
```
test_orchestration_project/
├── .claude-pm/
│   └── CLAUDE.md                      # Orchestration instructions
├── README.md                          # Generated by Documentation agent
├── test_plan.md                       # Generated by QA agent
└── deployment_config.yaml             # Generated by Ops agent
```

## Success Metrics

### Token Efficiency
- **Target**: 80-90% reduction in monthly token usage
- **Measurement**: Total tokens consumed per multi-agent workflow
- **Baseline**: 500k tokens for 10-agent workflow (full context duplication)
- **Goal**: <100k tokens for 10-agent workflow (filtered context)

### Cost Impact
- **Target**: Users stay within monthly plan limits
- **Measurement**: Monthly token consumption vs plan allowances
- **Baseline**: Users hitting plan limits with 5-10 workflows
- **Goal**: Users can run 50+ workflows within plan limits

### User Experience
- **Target**: Framework becomes cost-effective for regular use
- **Measurement**: User adoption and retention rates
- **Baseline**: Users limiting framework usage due to token costs
- **Goal**: Users can use framework without token usage concerns

## Risk Mitigation

### Technical Risks
1. **Backwards Compatibility**: Mitigation - comprehensive fallback system
2. **Context Filtering Accuracy**: Mitigation - extensive testing per agent type
3. **Agent Worker Stability**: Mitigation - error handling and restart mechanisms
4. **Performance**: Mitigation - simple serial execution first

### Adoption Risks
1. **User Confusion**: Mitigation - clear documentation and gradual rollout
2. **Complex Setup**: Mitigation - simple Claude.md configuration
3. **Debugging Difficulty**: Mitigation - verbose logging and status commands

## Future Enhancements

### Post-MVP Features
1. **Parallel Execution**: Add back parallel agent execution
2. **Real Claude Integration**: Replace mock responses with actual Claude API
3. **Agent State Persistence**: Add pause/resume capabilities
4. **Performance Monitoring**: Add metrics collection and reporting
5. **Advanced Context Filtering**: Machine learning-based context optimization

This design provides a solid foundation for testing the core orchestration concepts while maintaining complete backwards compatibility and providing a clear path for future enhancements.