"""
Agent Handler Registration and Management
========================================

This module manages default agent handlers for local orchestration mode.
"""

from typing import Dict, Callable, Awaitable
from .message_bus import Request, Response, MessageStatus, SimpleMessageBus
from claude_pm.core.logging_config import get_logger

logger = get_logger(__name__)


class AgentHandlerManager:
    """Manages registration and creation of default agent handlers."""
    
    # Define agent-specific greetings
    AGENT_GREETINGS = {
        'security': """Hello! I'm the Security Agent.

I specialize in:
- Security analysis and vulnerability assessment
- Threat modeling and risk evaluation  
- Security policy implementation
- Incident response coordination
- Compliance verification

I'm here to help protect your project from security vulnerabilities and ensure best practices are followed.""",
        
        'engineer': """Hello! I'm the Engineer Agent.

I specialize in:
- Code implementation and development
- Software architecture design
- Technical problem solving
- Performance optimization
- Code quality and best practices

I'm here to help with all your engineering and development needs.""",
        
        'documentation': """Hello! I'm the Documentation Agent.

I specialize in:
- Technical documentation creation
- API documentation
- User guides and tutorials
- Code documentation standards
- Documentation health analysis

I'm here to ensure your project has clear, comprehensive documentation.""",
        
        'qa': """Hello! I'm the QA Agent.

I specialize in:
- Test planning and execution
- Quality assurance processes
- Test automation
- Bug tracking and verification
- Quality metrics and reporting

I'm here to ensure your project meets quality standards.""",
        
        'research': """Hello! I'm the Research Agent.

I specialize in:
- Technical research and investigation
- Library and framework analysis
- Best practices research
- Technology evaluation
- Solution exploration

I'm here to help investigate and analyze technical topics.""",
        
        'ops': """Hello! I'm the Ops Agent.

I specialize in:
- Deployment and operations
- Infrastructure management
- CI/CD pipeline setup
- Monitoring and alerting
- Performance optimization

I'm here to handle all operational aspects of your project.""",
        
        'version_control': """Hello! I'm the Version Control Agent.

I specialize in:
- Git operations and workflows
- Branch management
- Merge conflict resolution
- Version tagging and releases
- Repository maintenance

I'm here to manage all version control operations.""",
        
        'data_engineer': """Hello! I'm the Data Engineer Agent.

I specialize in:
- Database design and optimization
- Data pipeline development
- ETL processes
- Data storage solutions
- AI/ML API integrations

I'm here to handle all data engineering tasks."""
    }
    
    @classmethod
    def create_agent_handler(cls, agent_type: str) -> Callable[[Request], Awaitable[Response]]:
        """Create a handler for a specific agent type."""
        async def agent_handler(request: Request) -> Response:
            """Handler that provides agent-specific responses."""
            task_data = request.data
            task = task_data.get('task', '')
            
            # Check if this is a simple greeting/role query
            greeting_keywords = ['who are you', 'hello', 'hi', 'greet', 'introduce', 'role', 'what do you do']
            is_greeting = any(keyword in task.lower() for keyword in greeting_keywords)
            
            if is_greeting:
                # Provide agent-specific greeting
                result_text = cls.AGENT_GREETINGS.get(agent_type, f"""Hello! I'm the {agent_type.title()} Agent.

I'm ready to assist with {agent_type} tasks. Please let me know what you need help with!""")
            else:
                # For actual tasks, provide a task acknowledgment
                result_text = f"""**{agent_type.title()} Agent Response**

Task received: {task}

I understand you need help with this {agent_type} task. As the {agent_type.title()} Agent, I'll analyze the requirements and provide appropriate assistance.

Requirements:
{chr(10).join('- ' + req for req in (task_data.get('requirements') or ['None specified']))}

Deliverables:
{chr(10).join('- ' + dlv for dlv in (task_data.get('deliverables') or ['None specified']))}

Priority: {task_data.get('priority', 'medium')}

I'm processing this request using LOCAL orchestration for instant response."""
            
            return Response(
                request_id=request.id,
                correlation_id=request.correlation_id,
                agent_id=agent_type,
                status=MessageStatus.COMPLETED,
                data={"result": result_text}
            )
        
        return agent_handler
    
    @classmethod
    def register_default_handlers(cls, message_bus: SimpleMessageBus) -> None:
        """
        Register default handlers for all agent types to enable instant LOCAL mode.
        These handlers provide agent-specific responses based on their role.
        """
        # Register handlers for all common agent types
        agent_types = [
            'engineer', 'documentation', 'qa', 'research', 'ops', 
            'security', 'version_control', 'ticketing', 'data_engineer',
            'architect', 'ui_ux', 'performance', 'test', 'deployment'
        ]
        
        for agent_type in agent_types:
            try:
                handler = cls.create_agent_handler(agent_type)
                message_bus.register_handler(agent_type, handler)
                logger.debug(f"Registered specific handler for {agent_type} agent")
            except ValueError:
                # Handler already registered, skip
                pass
            except Exception as e:
                logger.warning(f"Failed to register handler for {agent_type}: {e}")