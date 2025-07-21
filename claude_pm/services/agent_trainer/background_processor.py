"""
Agent Training Background Processor
==================================

This module handles background processing tasks including continuous learning loops,
analytics updates, and adaptation monitoring.

Classes:
    BackgroundProcessor: Main class for background processing tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np

from .types import (
    TrainingSession, LearningAdaptation, TrainingMode
)

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Handles background processing for the agent training system."""
    
    def __init__(self):
        """Initialize the background processor."""
        self.logger = logger
        self.running = False
        self.processing_tasks = []
        self.training_queue = asyncio.Queue()
    
    async def start_background_tasks(self) -> List[asyncio.Task]:
        """Start all background processing tasks."""
        self.running = True
        
        self.processing_tasks = [
            asyncio.create_task(self._process_training_queue()),
            asyncio.create_task(self._continuous_learning_loop()),
            asyncio.create_task(self._analytics_update_loop()),
            asyncio.create_task(self._adaptation_monitoring_loop())
        ]
        
        return self.processing_tasks
    
    async def stop_background_tasks(self) -> None:
        """Stop all background processing tasks."""
        self.running = False
        
        # Cancel all tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
    
    async def queue_training_request(self, request: Dict[str, Any]) -> None:
        """Add a training request to the queue."""
        await self.training_queue.put(request)
    
    async def _process_training_queue(self) -> None:
        """Process training requests from the queue."""
        while self.running:
            try:
                # Get training request from queue
                request = await asyncio.wait_for(self.training_queue.get(), timeout=5.0)
                
                # Process the training request (delegated to main trainer)
                # This will be called by the main AgentTrainer
                await self._handle_training_request(request)
                
                # Mark task as done
                self.training_queue.task_done()
                
            except asyncio.TimeoutError:
                # No requests in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error processing training queue: {e}")
                await asyncio.sleep(1)
    
    async def _continuous_learning_loop(self) -> None:
        """Continuous learning loop for real-time adaptation."""
        while self.running:
            try:
                # These methods will be called on the main trainer instance
                await self._trigger_continuous_learning()
                
                # Sleep for next iteration
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in continuous learning loop: {e}")
                await asyncio.sleep(60)  # 1 minute on error
    
    async def _analytics_update_loop(self) -> None:
        """Update analytics and performance forecasts."""
        while self.running:
            try:
                # These methods will be called on the main trainer instance
                await self._trigger_analytics_update()
                
                # Sleep for next iteration
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in analytics update loop: {e}")
                await asyncio.sleep(120)  # 2 minutes on error
    
    async def _adaptation_monitoring_loop(self) -> None:
        """Monitor adaptation effectiveness."""
        while self.running:
            try:
                # These methods will be called on the main trainer instance
                await self._trigger_adaptation_monitoring()
                
                # Sleep for next iteration
                await asyncio.sleep(900)  # 15 minutes
                
            except Exception as e:
                self.logger.error(f"Error in adaptation monitoring loop: {e}")
                await asyncio.sleep(180)  # 3 minutes on error
    
    # These methods will be overridden to call the main trainer's methods
    async def _handle_training_request(self, request: Dict[str, Any]) -> None:
        """Handle a training request. To be overridden."""
        pass
    
    async def _trigger_continuous_learning(self) -> None:
        """Trigger continuous learning. To be overridden."""
        pass
    
    async def _trigger_analytics_update(self) -> None:
        """Trigger analytics update. To be overridden."""
        pass
    
    async def _trigger_adaptation_monitoring(self) -> None:
        """Trigger adaptation monitoring. To be overridden."""
        pass
    
    async def apply_learning_adaptations(self,
                                       trend_data: Dict[str, Any],
                                       training_strategies: Dict[str, Any]) -> List[LearningAdaptation]:
        """Apply learning adaptations based on performance."""
        adaptations = []
        
        for agent_type, strategy in training_strategies.items():
            # Get recent performance data
            recent_data = list(trend_data[agent_type])[-10:]  # Last 10 data points
            
            if not recent_data:
                continue
            
            # Calculate performance metrics
            avg_performance = np.mean([d['average_improvement'] for d in recent_data])
            trend_slope = np.mean([d['trend_slope'] for d in recent_data])
            
            # Determine if adaptation is needed
            if avg_performance < 10.0 or trend_slope < -0.5:
                # Performance declining, adapt strategy
                await strategy.adapt_strategy({
                    'average_score': avg_performance,
                    'trend_slope': trend_slope,
                    'agent_type': agent_type
                })
                
                # Return any new adaptations
                if strategy.adaptations:
                    adaptations.extend(strategy.adaptations)
        
        return adaptations
    
    async def monitor_adaptation_effectiveness(self,
                                            adaptations: List[LearningAdaptation],
                                            training_sessions: List[TrainingSession]) -> None:
        """Monitor the effectiveness of applied adaptations."""
        for adaptation in adaptations:
            if not adaptation.active:
                continue
            
            # Get sessions after adaptation was applied
            post_adaptation_sessions = [
                session for session in training_sessions
                if (session.agent_type == adaptation.agent_type and 
                    session.timestamp > adaptation.applied_at)
            ]
            
            if len(post_adaptation_sessions) < 3:
                continue  # Need at least 3 sessions to evaluate
            
            # Calculate effectiveness
            avg_improvement = np.mean([s.improvement_score for s in post_adaptation_sessions])
            success_rate = len([s for s in post_adaptation_sessions if s.success]) / len(post_adaptation_sessions)
            
            # Update effectiveness score
            adaptation.effectiveness_score = (avg_improvement / 100.0) * 0.7 + success_rate * 0.3
    
    async def adjust_adaptations(self, adaptations: List[LearningAdaptation]) -> None:
        """Adjust adaptations based on effectiveness."""
        for adaptation in adaptations:
            if adaptation.effectiveness_score < 0.3:  # Low effectiveness
                adaptation.active = False
                self.logger.info(f"Disabled ineffective adaptation: {adaptation.adaptation_type} for {adaptation.agent_type}")
    
    async def cleanup_old_adaptations(self, adaptations: List[LearningAdaptation]) -> List[LearningAdaptation]:
        """Clean up old adaptations."""
        cutoff_time = datetime.now() - timedelta(days=30)  # 30 days
        
        original_count = len(adaptations)
        active_adaptations = [
            adaptation for adaptation in adaptations
            if adaptation.applied_at > cutoff_time
        ]
        
        cleaned_count = original_count - len(active_adaptations)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old adaptations")
        
        return active_adaptations
    
    def get_background_task_status(self) -> Dict[str, Any]:
        """Get status of background tasks."""
        return {
            'running': self.running,
            'active_tasks': len([t for t in self.processing_tasks if not t.done()]),
            'queue_size': self.training_queue.qsize(),
            'task_status': {
                'training_queue': not self.processing_tasks[0].done() if self.processing_tasks else False,
                'continuous_learning': not self.processing_tasks[1].done() if len(self.processing_tasks) > 1 else False,
                'analytics_update': not self.processing_tasks[2].done() if len(self.processing_tasks) > 2 else False,
                'adaptation_monitoring': not self.processing_tasks[3].done() if len(self.processing_tasks) > 3 else False,
            }
        }