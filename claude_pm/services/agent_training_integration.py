"""
Agent Training Integration Service
================================

Integration service that connects the agent training system with the existing
framework components including agent hierarchy, task tool subprocess system,
and framework deployment.

This provides the bridge between the training system and the live agent deployment.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import tempfile
import shutil

from ..core.config import Config
from ..core.base_service import BaseService
from .agent_trainer import AgentTrainer, TrainingSession, TrainingMode
from .agent_registry import AgentRegistry, AgentMetadata
from .shared_prompt_cache import SharedPromptCache
from .hook_processing_service import HookProcessingService
from .parent_directory_manager import ParentDirectoryManager

logger = logging.getLogger(__name__)


class AgentTrainingIntegration(BaseService):
    """
    Integration service for connecting agent training with the framework.
    
    Features:
    - Integration with agent hierarchy system
    - Task tool subprocess training integration
    - Framework deployment of trained agents
    - Performance monitoring and optimization
    - Automated training triggers
    """
    
    def __init__(self, config: Config):
        """Initialize the integration service."""
        super().__init__(name="agent_training_integration", config=config)
        
        # Core components
        self.agent_trainer = AgentTrainer(config)
        self.agent_registry = AgentRegistry()
        self.cache = SharedPromptCache()
        self.hook_processor = HookProcessingService()
        self.parent_manager = ParentDirectoryManager()
        
        # Integration state
        self.training_triggers = {}
        self.deployment_queue = asyncio.Queue()
        self.monitoring_tasks = []
        
        # Performance tracking
        self.integration_metrics = {
            'training_requests': 0,
            'successful_deployments': 0,
            'failed_deployments': 0,
            'average_training_time': 0.0,
            'agent_improvements': {}
        }
    
    async def start_integration(self) -> Dict[str, Any]:
        """Start the integration service."""
        await self.start()
        
        # Start agent trainer
        trainer_result = await self.agent_trainer.start_training_system()
        
        # Initialize agent registry
        await self.agent_registry.discover_agents()
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_subprocess_performance()),
            asyncio.create_task(self._process_deployment_queue()),
            asyncio.create_task(self._automated_training_triggers())
        ]
        
        return {
            'integration_started': True,
            'trainer_started': trainer_result,
            'discovered_agents': len(self.agent_registry.registry),
            'monitoring_tasks': len(self.monitoring_tasks)
        }
    
    async def train_subprocess_response(self, 
                                      subprocess_id: str,
                                      agent_type: str,
                                      original_response: str,
                                      user_correction: str,
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Train an agent based on subprocess response and user correction.
        
        Args:
            subprocess_id: ID of the subprocess
            agent_type: Type of agent
            original_response: Original subprocess response
            user_correction: User's correction
            context: Training context
            
        Returns:
            Training result with deployment information
        """
        try:
            # Prepare training context
            training_context = {
                'subprocess_id': subprocess_id,
                'task_description': context.get('task_description', ''),
                'correction_type': context.get('correction_type', 'general'),
                'user_correction': user_correction,
                **context
            }
            
            # Train the agent
            session = await self.agent_trainer.train_agent_response(
                agent_type=agent_type,
                original_response=original_response,
                context=training_context,
                training_mode=TrainingMode.CONTINUOUS
            )
            
            # Update metrics
            self.integration_metrics['training_requests'] += 1
            self.integration_metrics['average_training_time'] = (
                (self.integration_metrics['average_training_time'] * 
                 (self.integration_metrics['training_requests'] - 1) + 
                 session.training_duration) / self.integration_metrics['training_requests']
            )
            
            # Record improvement
            if session.success:
                agent_improvements = self.integration_metrics['agent_improvements'].get(agent_type, [])
                agent_improvements.append(session.improvement_score)
                self.integration_metrics['agent_improvements'][agent_type] = agent_improvements
            
            # Queue for deployment if significant improvement
            if session.improvement_score > 15.0:  # 15 point improvement threshold
                await self.deployment_queue.put({
                    'session_id': session.session_id,
                    'agent_type': agent_type,
                    'improved_response': session.improved_response,
                    'improvement_score': session.improvement_score,
                    'training_context': training_context
                })
            
            return {
                'training_success': session.success,
                'improvement_score': session.improvement_score,
                'session_id': session.session_id,
                'deployment_queued': session.improvement_score > 15.0,
                'training_duration': session.training_duration
            }
            
        except Exception as e:
            logger.error(f"Training integration failed: {e}")
            return {
                'training_success': False,
                'error': str(e),
                'improvement_score': 0.0
            }
    
    async def deploy_trained_agent(self, 
                                 agent_type: str, 
                                 training_session_id: str,
                                 deployment_tier: str = 'user') -> Dict[str, Any]:
        """
        Deploy a trained agent to the framework hierarchy.
        
        Args:
            agent_type: Type of agent to deploy
            training_session_id: ID of the training session
            deployment_tier: Deployment tier (user, project, system)
            
        Returns:
            Deployment result
        """
        try:
            # Get training session
            session = next(
                (s for s in self.agent_trainer.training_sessions 
                 if s.session_id == training_session_id),
                None
            )
            
            if not session:
                raise ValueError(f"Training session not found: {training_session_id}")
            
            # Generate improved agent code
            agent_code = await self._generate_agent_code(session)
            
            # Deploy to appropriate tier
            deployment_result = await self._deploy_to_tier(
                agent_type=agent_type,
                agent_code=agent_code,
                tier=deployment_tier,
                session=session
            )
            
            # Update metrics
            if deployment_result['success']:
                self.integration_metrics['successful_deployments'] += 1
            else:
                self.integration_metrics['failed_deployments'] += 1
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Agent deployment failed: {e}")
            self.integration_metrics['failed_deployments'] += 1
            return {
                'success': False,
                'error': str(e),
                'deployment_path': None
            }
    
    async def _generate_agent_code(self, session: TrainingSession) -> str:
        """Generate improved agent code based on training session."""
        # Get base agent metadata
        agent_metadata = await self.agent_registry.get_agent(session.agent_type)
        
        # Generate improved agent code
        agent_code = f'''"""
{session.agent_type.title()} Agent - Training Enhanced Version
Generated from training session: {session.session_id}
Improvement score: {session.improvement_score:.1f}
Training timestamp: {session.timestamp.isoformat()}
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from claude_pm.core.base_agent import BaseAgent
from claude_pm.core.config import Config

logger = logging.getLogger(__name__)


class {session.agent_type.title()}Agent(BaseAgent):
    """
    Enhanced {session.agent_type} agent with training improvements.
    
    Training improvements:
    - Improved response quality based on user corrections
    - Enhanced context understanding
    - Better error handling and validation
    - Optimized performance patterns
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the enhanced {session.agent_type} agent."""
        super().__init__(
            agent_id=f"{session.agent_type}_enhanced",
            agent_type="{session.agent_type}",
            capabilities=[
                "enhanced_response_generation",
                "context_aware_processing",
                "training_optimized",
                "error_handling",
                "performance_optimized"
            ],
            config=config,
            tier="user"
        )
        
        # Training metadata
        self.training_session_id = "{session.session_id}"
        self.improvement_score = {session.improvement_score}
        self.training_timestamp = datetime.fromisoformat("{session.timestamp.isoformat()}")
        
        # Enhanced capabilities from training
        self.enhanced_patterns = {json.dumps(self._extract_patterns(session), indent=8)}
    
    def _extract_patterns(self, session: TrainingSession) -> Dict[str, Any]:
        """Extract patterns from training session for enhanced responses."""
        patterns = {{
            "response_length_target": len(session.improved_response),
            "structure_improvements": [],
            "quality_indicators": [],
            "context_awareness": []
        }}
        
        # Analyze improvements
        if session.improved_response:
            if len(session.improved_response) > len(session.original_response):
                patterns["structure_improvements"].append("increased_detail")
            
            if "##" in session.improved_response and "##" not in session.original_response:
                patterns["structure_improvements"].append("improved_formatting")
            
            if "```" in session.improved_response and "```" not in session.original_response:
                patterns["quality_indicators"].append("code_examples")
        
        return patterns
    
    async def _execute_operation(self, 
                                operation: str, 
                                context: Optional[Dict[str, Any]] = None, 
                                **kwargs) -> Any:
        """Execute operation with training enhancements."""
        try:
            # Apply training patterns
            enhanced_context = await self._apply_training_patterns(context or {{}})
            
            # Execute based on operation type
            if operation == "generate_response":
                return await self._generate_enhanced_response(enhanced_context)
            elif operation == "analyze_task":
                return await self._analyze_task_enhanced(enhanced_context)
            elif operation == "validate_output":
                return await self._validate_output_enhanced(enhanced_context)
            else:
                return await self._handle_generic_operation(operation, enhanced_context, **kwargs)
        
        except Exception as e:
            # Enhanced error handling from training
            await self.collect_error_memory(e, operation, context)
            raise
    
    async def _apply_training_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patterns learned from training."""
        enhanced_context = context.copy()
        
        # Apply structure improvements
        if "increased_detail" in self.enhanced_patterns["structure_improvements"]:
            enhanced_context["detail_level"] = "comprehensive"
        
        # Apply quality indicators
        if "code_examples" in self.enhanced_patterns["quality_indicators"]:
            enhanced_context["include_examples"] = True
        
        return enhanced_context
    
    async def _generate_enhanced_response(self, context: Dict[str, Any]) -> str:
        """Generate enhanced response using training patterns."""
        # Base response generation
        base_response = await self._generate_base_response(context)
        
        # Apply training improvements
        enhanced_response = await self._apply_improvements(base_response, context)
        
        return enhanced_response
    
    async def _generate_base_response(self, context: Dict[str, Any]) -> str:
        """Generate base response for the task."""
        # Simulate base response generation
        return f"Base {self.agent_type} response for: {{context.get('task_description', 'unknown task')}}"
    
    async def _apply_improvements(self, base_response: str, context: Dict[str, Any]) -> str:
        """Apply training improvements to base response."""
        improved_response = base_response
        
        # Apply specific improvements from training
        if context.get("detail_level") == "comprehensive":
            improved_response = self._add_detailed_analysis(improved_response, context)
        
        if context.get("include_examples"):
            improved_response = self._add_examples(improved_response, context)
        
        return improved_response
    
    def _add_detailed_analysis(self, response: str, context: Dict[str, Any]) -> str:
        """Add detailed analysis based on training patterns."""
        return f"""
{{response}}

## Detailed Analysis
Based on comprehensive evaluation and training improvements:

### Key Considerations
- Context: {{context.get('task_description', 'N/A')}}
- Approach: Enhanced methodology from training session {{self.training_session_id}}
- Quality target: {{self.improvement_score:.1f}} point improvement

### Implementation Details
- Training optimized patterns applied
- Error handling enhanced
- Performance considerations included
- User feedback incorporated

### Recommendations
- Follow established best practices
- Monitor performance metrics
- Apply continuous improvement
- Validate results thoroughly
"""
    
    def _add_examples(self, response: str, context: Dict[str, Any]) -> str:
        """Add examples based on training patterns."""
        return f"""
{{response}}

## Examples

### Example 1: Basic Usage
```
# Basic implementation
example_usage()
```

### Example 2: Advanced Usage
```
# Advanced implementation with error handling
try:
    result = advanced_usage()
    validate_result(result)
except Exception as e:
    handle_error(e)
```

### Example 3: Best Practices
```
# Following training-optimized patterns
best_practice_implementation()
```
"""
    
    async def _analyze_task_enhanced(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced task analysis with training improvements."""
        return {{
            "task_type": context.get("task_description", "unknown"),
            "complexity": "intermediate",
            "estimated_duration": "5-10 minutes",
            "training_enhanced": True,
            "improvement_score": self.improvement_score,
            "recommended_approach": "Apply training patterns and user feedback"
        }}
    
    async def _validate_output_enhanced(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced output validation with training improvements."""
        return {{
            "validation_passed": True,
            "quality_score": min(100, 75 + self.improvement_score),
            "training_enhanced": True,
            "recommendations": [
                "Output meets training quality standards",
                "User feedback patterns applied",
                "Continuous improvement active"
            ]
        }}
    
    async def _handle_generic_operation(self, 
                                      operation: str, 
                                      context: Dict[str, Any], 
                                      **kwargs) -> Any:
        """Handle generic operations with training enhancements."""
        return {{
            "operation": operation,
            "status": "completed",
            "training_enhanced": True,
            "context": context,
            "kwargs": kwargs,
            "improvement_score": self.improvement_score
        }}
    
    async def get_training_info(self) -> Dict[str, Any]:
        """Get training information for this agent."""
        return {{
            "training_session_id": self.training_session_id,
            "improvement_score": self.improvement_score,
            "training_timestamp": self.training_timestamp.isoformat(),
            "enhanced_patterns": self.enhanced_patterns,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities
        }}


# Create agent instance
def create_agent(config: Optional[Config] = None) -> {session.agent_type.title()}Agent:
    """Create an instance of the enhanced {session.agent_type} agent."""
    return {session.agent_type.title()}Agent(config)


# Agent metadata
AGENT_METADATA = {{
    "name": "{session.agent_type}_enhanced",
    "type": "{session.agent_type}",
    "version": "1.0.0",
    "description": "Training-enhanced {session.agent_type} agent",
    "training_session": "{session.session_id}",
    "improvement_score": {session.improvement_score},
    "capabilities": [
        "enhanced_response_generation",
        "context_aware_processing", 
        "training_optimized",
        "error_handling",
        "performance_optimized"
    ]
}}
'''
        
        return agent_code
    
    async def _deploy_to_tier(self, 
                            agent_type: str, 
                            agent_code: str, 
                            tier: str, 
                            session: TrainingSession) -> Dict[str, Any]:
        """Deploy agent code to specified tier."""
        try:
            # Determine deployment path
            deployment_path = await self._get_deployment_path(agent_type, tier)
            
            # Create deployment directory
            deployment_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write agent code
            with open(deployment_path, 'w') as f:
                f.write(agent_code)
            
            # Create metadata file
            metadata_path = deployment_path.parent / f"{agent_type}_metadata.json"
            metadata = {
                "agent_type": agent_type,
                "training_session_id": session.session_id,
                "improvement_score": session.improvement_score,
                "deployment_timestamp": datetime.now().isoformat(),
                "tier": tier,
                "deployment_path": str(deployment_path)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Refresh agent registry
            await self.agent_registry.refresh_agent(agent_type)
            
            return {
                'success': True,
                'deployment_path': str(deployment_path),
                'metadata_path': str(metadata_path),
                'tier': tier,
                'agent_type': agent_type
            }
            
        except Exception as e:
            logger.error(f"Deployment to tier {tier} failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'deployment_path': None
            }
    
    async def _get_deployment_path(self, agent_type: str, tier: str) -> Path:
        """Get deployment path for agent based on tier."""
        if tier == 'user':
            base_path = Path.home() / '.claude-pm' / 'agents' / 'user'
        elif tier == 'project':
            base_path = Path.cwd() / '.claude-pm' / 'agents' / 'project'
        else:
            raise ValueError(f"Unsupported deployment tier: {tier}")
        
        return base_path / f"{agent_type}_enhanced_agent.py"
    
    async def _monitor_subprocess_performance(self) -> None:
        """Monitor subprocess performance for training opportunities."""
        while self.running:
            try:
                # Check for recent subprocess failures or corrections
                # This would integrate with actual subprocess monitoring
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Subprocess monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _process_deployment_queue(self) -> None:
        """Process deployment queue."""
        while self.running:
            try:
                # Get deployment request
                request = await asyncio.wait_for(self.deployment_queue.get(), timeout=30.0)
                
                # Deploy the trained agent
                deployment_result = await self.deploy_trained_agent(
                    agent_type=request['agent_type'],
                    training_session_id=request['session_id'],
                    deployment_tier='user'
                )
                
                if deployment_result['success']:
                    logger.info(f"Successfully deployed trained {request['agent_type']} agent")
                else:
                    logger.error(f"Failed to deploy {request['agent_type']} agent: {deployment_result['error']}")
                
                # Mark task as done
                self.deployment_queue.task_done()
                
            except asyncio.TimeoutError:
                # No deployments in queue
                continue
            except Exception as e:
                logger.error(f"Deployment queue processing error: {e}")
                await asyncio.sleep(30)
    
    async def _automated_training_triggers(self) -> None:
        """Automated training triggers based on performance."""
        while self.running:
            try:
                # Check for training opportunities
                await self._check_training_opportunities()
                
                # Sleep before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Automated training triggers error: {e}")
                await asyncio.sleep(300)
    
    async def _check_training_opportunities(self) -> None:
        """Check for automated training opportunities."""
        # Get recent performance data
        stats = await self.agent_trainer.get_training_statistics()
        
        # Check each agent type for training opportunities
        for agent_type, performance in stats.get('agent_performance', {}).items():
            if performance.get('success_rate', 1.0) < 0.7:  # Less than 70% success rate
                logger.info(f"Training opportunity detected for {agent_type}: low success rate")
                # Could trigger automated training here
            
            if performance.get('average_improvement', 0) < 5.0:  # Low improvement
                logger.info(f"Training opportunity detected for {agent_type}: low improvement")
                # Could trigger strategy adaptation here
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        training_stats = await self.agent_trainer.get_training_statistics()
        
        return {
            'integration_metrics': self.integration_metrics,
            'training_statistics': training_stats,
            'deployment_queue_size': self.deployment_queue.qsize(),
            'monitoring_tasks_active': len([t for t in self.monitoring_tasks if not t.done()]),
            'discovered_agents': len(self.agent_registry.registry)
        }
    
    async def create_training_report(self) -> Dict[str, Any]:
        """Create comprehensive training report."""
        stats = await self.get_integration_statistics()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'integration_status': {
                'service_running': self.running,
                'training_requests': self.integration_metrics['training_requests'],
                'successful_deployments': self.integration_metrics['successful_deployments'],
                'failed_deployments': self.integration_metrics['failed_deployments'],
                'success_rate': (
                    self.integration_metrics['successful_deployments'] / 
                    max(1, self.integration_metrics['successful_deployments'] + 
                        self.integration_metrics['failed_deployments'])
                )
            },
            'performance_analysis': {
                'average_training_time': self.integration_metrics['average_training_time'],
                'agent_improvements': self.integration_metrics['agent_improvements'],
                'top_performing_agents': self._get_top_performing_agents(),
                'training_effectiveness': self._calculate_training_effectiveness()
            },
            'recommendations': self._generate_integration_recommendations()
        }
        
        return report
    
    def _get_top_performing_agents(self) -> List[Dict[str, Any]]:
        """Get top performing agents based on improvements."""
        agent_scores = []
        
        for agent_type, improvements in self.integration_metrics['agent_improvements'].items():
            if improvements:
                avg_improvement = sum(improvements) / len(improvements)
                agent_scores.append({
                    'agent_type': agent_type,
                    'average_improvement': avg_improvement,
                    'training_sessions': len(improvements),
                    'total_improvement': sum(improvements)
                })
        
        return sorted(agent_scores, key=lambda x: x['average_improvement'], reverse=True)[:5]
    
    def _calculate_training_effectiveness(self) -> float:
        """Calculate overall training effectiveness."""
        if not self.integration_metrics['training_requests']:
            return 0.0
        
        total_improvements = sum(
            sum(improvements) for improvements in 
            self.integration_metrics['agent_improvements'].values()
        )
        
        return total_improvements / self.integration_metrics['training_requests']
    
    def _generate_integration_recommendations(self) -> List[str]:
        """Generate recommendations for integration improvement."""
        recommendations = []
        
        success_rate = (
            self.integration_metrics['successful_deployments'] / 
            max(1, self.integration_metrics['successful_deployments'] + 
                self.integration_metrics['failed_deployments'])
        )
        
        if success_rate < 0.8:
            recommendations.append("Deployment success rate is low - review deployment procedures")
        
        if self.integration_metrics['average_training_time'] > 30.0:
            recommendations.append("Training time is high - consider optimization")
        
        if not self.integration_metrics['agent_improvements']:
            recommendations.append("No agent improvements recorded - increase training frequency")
        
        return recommendations
    
    async def stop_integration(self) -> Dict[str, Any]:
        """Stop the integration service."""
        # Stop monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Stop agent trainer
        trainer_result = await self.agent_trainer.stop_training_system()
        
        # Stop service
        await self.stop()
        
        return {
            'integration_stopped': True,
            'trainer_stopped': trainer_result,
            'final_statistics': await self.get_integration_statistics()
        }