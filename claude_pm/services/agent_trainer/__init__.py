"""
Agent-Specific Training System - Phase 4 Implementation (Refactored)
==================================================================

Comprehensive agent training system with specialized training for each agent type,
continuous learning, advanced analytics, and distributed processing capabilities.

This module has been refactored using the Phase 2 delegation pattern to reduce
complexity and improve maintainability.

Features:
- Agent-specific training templates and strategies
- Continuous learning with real-time adaptation
- Advanced analytics and predictive modeling
- Multi-modal training support
- Distributed processing capabilities
- Integration with existing agent hierarchy

This implements Phase 4 of the automatic prompt evaluation system (ISS-0125).
"""

import asyncio
import hashlib
import logging
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any

from ...core.config import Config
from ...core.base_service import BaseService
from ..agent_registry import AgentRegistry
from ..mirascope_evaluator import MirascopeEvaluator
from ..correction_capture import CorrectionCapture
from ..evaluation_metrics import EvaluationMetricsSystem
from ..shared_prompt_cache import SharedPromptCache

# Import delegated modules
from .types import (
    TrainingMode, TrainingDataFormat, TrainingTemplate, 
    TrainingSession, LearningAdaptation, PerformancePrediction
)
from .strategies import create_training_strategy
from .response_improver import ResponseImprover
from .analytics import TrainingAnalytics
from .background_processor import BackgroundProcessor
from .metrics import TrainingMetrics
from .dashboard import TrainingDashboard

logger = logging.getLogger(__name__)


class AgentTrainer(BaseService):
    """
    Comprehensive agent training system with specialized training for each agent type.
    
    Features:
    - Agent-specific training templates
    - Continuous learning and adaptation
    - Advanced analytics and forecasting
    - Multi-modal training support
    - Distributed processing capabilities
    """
    
    def __init__(self, config: Config):
        """Initialize the agent trainer."""
        super().__init__(name="agent_trainer", config=config)
        
        # Core components
        self.agent_registry = AgentRegistry()
        self.evaluator = MirascopeEvaluator(config)
        self.correction_capture = CorrectionCapture(config)
        self.metrics_system = EvaluationMetricsSystem(config)
        self.cache = SharedPromptCache()
        
        # Delegated components
        self.response_improver = ResponseImprover(self.cache)
        self.analytics = TrainingAnalytics()
        self.background_processor = BackgroundProcessor()
        self.metrics = TrainingMetrics()
        self.dashboard = TrainingDashboard()
        
        # Training state
        self.training_templates: Dict[str, TrainingTemplate] = {}
        self.training_strategies: Dict[str, Any] = {}
        self.training_sessions: List[TrainingSession] = []
        self.adaptations: List[LearningAdaptation] = []
        self.performance_predictions: List[PerformancePrediction] = []
        
        # Distributed processing
        self.worker_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        
        # Override background processor methods to call our methods
        self._setup_background_processor_callbacks()
        
        # Initialize training strategies
        self._initialize_training_strategies()
        
        # Initialize templates
        self._initialize_training_templates()
    
    def _setup_background_processor_callbacks(self):
        """Setup callbacks for background processor to call our methods."""
        async def handle_training_request(request):
            await self.train_agent_response(**request)
        
        async def trigger_continuous_learning():
            await self.analytics.analyze_performance_trends(
                self.training_sessions, self.training_strategies
            )
            new_adaptations = await self.background_processor.apply_learning_adaptations(
                self.analytics.trend_data, self.training_strategies
            )
            self.adaptations.extend(new_adaptations)
            await self.analytics.update_prediction_models(self.training_strategies)
        
        async def trigger_analytics_update():
            await self.analytics.update_trend_data(
                self.training_sessions, self.training_strategies
            )
            await self.analytics.generate_performance_predictions()
            self.performance_predictions = self.analytics.performance_predictions
            self.metrics.update_effectiveness_metrics(
                self.training_sessions, 
                len([a for a in self.adaptations if a.active])
            )
        
        async def trigger_adaptation_monitoring():
            await self.background_processor.monitor_adaptation_effectiveness(
                self.adaptations, self.training_sessions
            )
            await self.background_processor.adjust_adaptations(self.adaptations)
            self.adaptations = await self.background_processor.cleanup_old_adaptations(
                self.adaptations
            )
        
        # Set the callbacks
        self.background_processor._handle_training_request = handle_training_request
        self.background_processor._trigger_continuous_learning = trigger_continuous_learning
        self.background_processor._trigger_analytics_update = trigger_analytics_update
        self.background_processor._trigger_adaptation_monitoring = trigger_adaptation_monitoring
    
    def _initialize_training_strategies(self) -> None:
        """Initialize agent-specific training strategies."""
        # Core agent types
        core_agents = ['engineer', 'documentation', 'qa', 'research', 
                      'ops', 'security', 'ticketing', 'version_control', 
                      'data_engineer']
        
        for agent_type in core_agents:
            self.training_strategies[agent_type] = create_training_strategy(
                agent_type, self.config
            )
    
    def _initialize_training_templates(self) -> None:
        """Initialize training templates for different agent types."""
        templates = [
            TrainingTemplate(
                agent_type="engineer",
                template_id="code_optimization",
                description="Optimize code for performance and maintainability",
                training_strategy="iterative_improvement",
                prompt_template="""
                Optimize the following code:
                {original_response}
                
                Context: {task_description}
                
                Focus on:
                - Algorithm efficiency
                - Memory usage
                - Code readability
                - Error handling
                - Best practices
                """,
                success_criteria=["performance_improvement", "code_quality", "maintainability"],
                improvement_areas=["efficiency", "readability", "error_handling"],
                data_format=TrainingDataFormat.CODE,
                complexity_level="advanced"
            ),
            TrainingTemplate(
                agent_type="documentation",
                template_id="comprehensive_docs",
                description="Create comprehensive and user-friendly documentation",
                training_strategy="structured_improvement",
                prompt_template="""
                Improve the following documentation:
                {original_response}
                
                Context: {task_description}
                
                Ensure:
                - Clear structure and headings
                - Code examples with explanations
                - Complete parameter descriptions
                - Usage examples
                - Best practices
                """,
                success_criteria=["clarity", "completeness", "structure"],
                improvement_areas=["structure", "examples", "clarity"],
                data_format=TrainingDataFormat.DOCUMENTATION,
                complexity_level="intermediate"
            ),
            TrainingTemplate(
                agent_type="qa",
                template_id="comprehensive_testing",
                description="Comprehensive quality assurance and testing analysis",
                training_strategy="systematic_analysis",
                prompt_template="""
                Enhance the following QA analysis:
                {original_response}
                
                Context: {task_description}
                
                Include:
                - Test coverage analysis
                - Risk assessment
                - Performance metrics
                - Security considerations
                - Recommendations
                """,
                success_criteria=["coverage", "risk_assessment", "actionable_recommendations"],
                improvement_areas=["thoroughness", "metrics", "recommendations"],
                data_format=TrainingDataFormat.ANALYSIS,
                complexity_level="advanced"
            )
        ]
        
        for template in templates:
            self.training_templates[template.template_id] = template
    
    async def start_training_system(self) -> Dict[str, Any]:
        """Start the training system with background processing."""
        await self.start()
        
        # Start background processing tasks
        background_tasks = await self.background_processor.start_background_tasks()
        
        return {
            "training_system_started": True,
            "strategies_loaded": len(self.training_strategies),
            "templates_loaded": len(self.training_templates),
            "background_tasks_started": len(background_tasks)
        }
    
    async def train_agent_response(self, 
                                 agent_type: str, 
                                 original_response: str, 
                                 context: Dict[str, Any],
                                 training_mode: TrainingMode = TrainingMode.CONTINUOUS) -> TrainingSession:
        """
        Train and improve an agent's response.
        
        Args:
            agent_type: Type of agent to train
            original_response: Original response to improve
            context: Training context
            training_mode: Training mode to use
            
        Returns:
            TrainingSession with results
        """
        session_id = hashlib.md5(f"{agent_type}_{original_response}_{time.time()}".encode()).hexdigest()
        
        session = TrainingSession(
            session_id=session_id,
            agent_type=agent_type,
            training_mode=training_mode,
            template_id="",  # Will be set during training
            original_response=original_response,
            improved_response="",
            context=context
        )
        
        start_time = time.time()
        
        try:
            # Get training strategy
            strategy = self.training_strategies.get(agent_type)
            if not strategy:
                raise ValueError(f"No training strategy found for agent type: {agent_type}")
            
            # Evaluate original response
            session.evaluation_before = await self.evaluator.evaluate_response(
                agent_type=agent_type,
                response_text=original_response,
                context=context
            )
            
            # Generate training prompt
            training_prompt = await strategy.generate_training_prompt({
                'original_response': original_response,
                **context
            })
            
            # Get improved response using response improver
            session.improved_response = await self.response_improver.generate_improved_response(
                training_prompt, original_response, agent_type
            )
            
            # Evaluate improved response
            session.evaluation_after = await self.evaluator.evaluate_response(
                agent_type=agent_type,
                response_text=session.improved_response,
                context=context
            )
            
            # Calculate improvement
            if session.evaluation_before and session.evaluation_after:
                session.improvement_score = (
                    session.evaluation_after.overall_score - 
                    session.evaluation_before.overall_score
                )
                session.success = session.improvement_score > 0
            
            # Record training duration
            session.training_duration = time.time() - start_time
            
            # Store session
            self.training_sessions.append(session)
            
            # Update metrics
            self.metrics.update_training_metrics(session)
            
            # Check for adaptations
            new_adaptations = await self.metrics.check_adaptation_triggers(
                agent_type, session, self.training_sessions
            )
            self.adaptations.extend(new_adaptations)
            
            self.logger.info(f"Training session completed for {agent_type}: {session.improvement_score:.1f} point improvement")
            
            return session
            
        except Exception as e:
            self.logger.error(f"Training failed for {agent_type}: {e}")
            session.training_duration = time.time() - start_time
            session.success = False
            session.metadata['error'] = str(e)
            return session
    
    async def get_training_statistics(self) -> Dict[str, Any]:
        """Get comprehensive training statistics."""
        return self.metrics.get_training_statistics(
            self.training_strategies,
            self.training_sessions,
            self.performance_predictions,
            self.adaptations
        )
    
    async def get_agent_training_dashboard(self, agent_type: str) -> Dict[str, Any]:
        """Get comprehensive dashboard for specific agent training."""
        return self.dashboard.get_agent_training_dashboard(
            agent_type,
            self.training_sessions,
            self.adaptations,
            self.performance_predictions,
            self.analytics.trend_data
        )
    
    async def export_training_data(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Export training data for analysis or backup."""
        stats = await self.get_training_statistics()
        return self.dashboard.export_training_data(
            self.training_sessions,
            self.adaptations,
            self.performance_predictions,
            self.training_templates,
            stats,
            agent_type
        )
    
    async def stop_training_system(self) -> Dict[str, Any]:
        """Stop the training system and background tasks."""
        # Stop background processor
        await self.background_processor.stop_background_tasks()
        
        # Shutdown worker pool
        self.worker_pool.shutdown(wait=True)
        
        # Stop the service
        await self.stop()
        
        return {
            'training_system_stopped': True,
            'background_tasks_stopped': len(self.background_processor.processing_tasks),
            'final_statistics': await self.get_training_statistics()
        }
    
    async def _health_check(self) -> Dict[str, bool]:
        """Health check for the training system."""
        checks = await super()._health_check()
        
        # Training-specific health checks
        health_status = self.dashboard.get_training_health_status(
            self.training_sessions,
            self.background_processor.processing_tasks,
            self.training_strategies,
            self.training_templates
        )
        
        checks.update(health_status)
        checks['worker_pool_active'] = not self.worker_pool._shutdown
        
        return checks


# Export main class and types for backward compatibility
__all__ = [
    'AgentTrainer',
    'TrainingMode',
    'TrainingDataFormat', 
    'TrainingTemplate',
    'TrainingSession',
    'LearningAdaptation',
    'PerformancePrediction',
    'ResponseImprover',
    'TrainingAnalytics',
    'BackgroundProcessor',
    'TrainingMetrics',
    'TrainingDashboard',
    'create_training_strategy'
]