"""
Prompt Fixtures for E2E Testing

Provides pre-configured prompts and templates for testing.
"""

from typing import Dict, Any, List
import json


class PromptFixtures:
    """Collection of prompt fixtures for testing."""
    
    @staticmethod
    def task_tool_prompt(agent_type: str, task: str, context: str) -> str:
        """Create a standard task tool prompt."""
        return f"""**{agent_type.title()} Agent**: {task}

TEMPORAL CONTEXT: Today is 2025-07-19. Apply date awareness to task execution.

**Task**: {task}
- Execute the assigned task
- Provide clear results
- Report any issues encountered

**Context**: {context}

**Authority**: Domain-specific operations
**Expected Results**: Task completion with clear deliverables
**Escalation**: Report blockers or issues requiring PM intervention
"""
    
    @staticmethod
    def orchestration_prompt(tasks: List[str]) -> str:
        """Create an orchestration prompt for multiple tasks."""
        task_list = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        
        return f"""## Multi-Agent Orchestration Task

**Objective**: Coordinate multiple agents to complete the following tasks:

{task_list}

**Coordination Requirements**:
- Delegate each task to the appropriate agent
- Ensure proper sequencing of dependent tasks
- Integrate results from all agents
- Provide comprehensive status updates

**Success Criteria**:
- All tasks completed successfully
- Results properly integrated
- No conflicts between agent outputs
- Clear documentation of process
"""
    
    @staticmethod
    def init_command_prompt() -> str:
        """Create a prompt for initialization testing."""
        return """## Framework Initialization

**Task**: Initialize the Claude PM framework with proper configuration.

**Requirements**:
1. Verify framework installation
2. Create necessary directory structure
3. Set up agent hierarchy
4. Validate configuration

**Expected Outcome**:
- Framework fully initialized
- All directories created
- Agents discoverable
- Configuration valid
"""
    
    @staticmethod
    def agent_discovery_prompt(specializations: List[str]) -> str:
        """Create a prompt for agent discovery testing."""
        specs = ", ".join(specializations)
        
        return f"""## Agent Discovery Task

**Objective**: Discover agents with the following specializations: {specs}

**Requirements**:
1. Search all agent directories
2. Match specializations
3. Respect precedence rules
4. Return optimal agent

**Discovery Criteria**:
- Specialization match
- Directory precedence (project > user > system)
- Agent availability
- Performance considerations
"""
    
    @staticmethod
    def test_scenario_prompt(scenario_name: str, steps: List[str]) -> str:
        """Create a prompt for test scenario execution."""
        step_list = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
        
        return f"""## Test Scenario: {scenario_name}

**Scenario Steps**:
{step_list}

**Validation Requirements**:
- Each step must complete successfully
- Verify expected outcomes
- Check for side effects
- Validate state changes

**Success Metrics**:
- All steps executed
- No unexpected errors
- State validated
- Results documented
"""
    
    @staticmethod
    def mock_agent_response(agent_name: str, task: str, success: bool = True) -> Dict[str, Any]:
        """Create a mock agent response."""
        return {
            "agent": agent_name,
            "task": task,
            "status": "success" if success else "failure",
            "result": {
                "output": f"{agent_name} completed: {task}" if success else f"{agent_name} failed: {task}",
                "artifacts": [],
                "metrics": {
                    "duration": "2.5s",
                    "operations": 1
                }
            },
            "errors": [] if success else [{"type": "TestError", "message": "Mock failure"}]
        }
    
    @staticmethod
    def create_test_messages(count: int = 5) -> List[Dict[str, Any]]:
        """Create test messages for message bus testing."""
        messages = []
        for i in range(count):
            messages.append({
                "id": f"msg_{i}",
                "type": "test_message",
                "sender": f"agent_{i % 3}",
                "recipient": "orchestrator",
                "content": f"Test message {i}",
                "timestamp": f"2025-07-19T12:00:{i:02d}Z"
            })
        return messages
    
    @staticmethod
    def validation_prompt(validation_type: str, target: str) -> str:
        """Create a validation prompt."""
        return f"""## Validation Task: {validation_type}

**Target**: {target}

**Validation Steps**:
1. Check existence and accessibility
2. Validate structure and format
3. Verify functionality
4. Test edge cases

**Report Requirements**:
- Pass/fail status
- Detailed findings
- Recommendations
- Risk assessment
"""