"""
Evaluation Integration Service
=============================

This service integrates the Mirascope evaluation system with the correction capture system,
providing seamless automatic evaluation of agent responses and corrections.

Key Features:
- Automatic evaluation trigger on correction capture
- Unified interface for evaluation and correction data
- Performance monitoring and optimization
- Batch processing for efficiency
- Integration with existing Task Tool subprocess system

Integration Points:
- CorrectionCapture: Automatic evaluation on correction capture
- Task Tool: Evaluation hooks for subprocess responses
- Agent responses: Real-time evaluation of agent outputs
- Analytics: Performance metrics and improvement tracking
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from claude_pm.core.config import Config
from claude_pm.services.correction_capture import CorrectionCapture, CorrectionData, CorrectionType
from claude_pm.services.mirascope_evaluator import MirascopeEvaluator, EvaluationResult, EvaluationCriteria

logger = logging.getLogger(__name__)


@dataclass
class EvaluationIntegrationStats:
    """Statistics for evaluation integration."""
    total_evaluations: int = 0
    automatic_evaluations: int = 0
    manual_evaluations: int = 0
    corrections_evaluated: int = 0
    average_evaluation_time_ms: float = 0
    cache_hit_rate: float = 0
    errors: int = 0
    last_evaluation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EvaluationIntegrationService:
    """
    Service that integrates evaluation with correction capture.
    
    Provides unified interface for automatic evaluation of agent responses
    and corrections, with performance optimization and monitoring.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize evaluation integration service.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.enabled = self.config.get("enable_evaluation", True)
        
        # Initialize component services
        self.correction_capture = CorrectionCapture(self.config)
        self.evaluator = MirascopeEvaluator(self.config)
        
        # Integration configuration
        self.auto_evaluate_corrections = self.config.get("auto_evaluate_corrections", True)
        self.auto_evaluate_responses = self.config.get("auto_evaluate_responses", True)
        self.batch_evaluation_enabled = self.config.get("batch_evaluation_enabled", True)
        self.batch_evaluation_interval = self.config.get("batch_evaluation_interval_minutes", 5)
        
        # Statistics tracking
        self.stats = EvaluationIntegrationStats()
        
        # Background task management
        self.background_tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
        
        # Initialize storage
        self.storage_path = Path(self.config.get("evaluation_storage_path", "~/.claude-pm/training")).expanduser()
        self.integration_dir = self.storage_path / "integration"
        self.integration_dir.mkdir(parents=True, exist_ok=True)
        
        if self.enabled:
            logger.info("Evaluation integration service initialized")
        else:
            logger.info("Evaluation integration service disabled")
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for batch evaluation."""
        if not self.enabled or not self.batch_evaluation_enabled:
            return
        
        # Start batch evaluation task
        task = asyncio.create_task(self._batch_evaluation_loop())
        self.background_tasks.append(task)
        
        logger.info("Started evaluation integration background tasks")
    
    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        self.shutdown_event.set()
        
        # Cancel all tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        logger.info("Stopped evaluation integration background tasks")
    
    async def _batch_evaluation_loop(self) -> None:
        """Background loop for batch evaluation of corrections."""
        while not self.shutdown_event.is_set():
            try:
                # Run batch evaluation
                await self._run_batch_evaluation()
                
                # Wait for next interval
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=self.batch_evaluation_interval * 60
                )
                
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in batch evaluation loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _run_batch_evaluation(self) -> None:
        """Run batch evaluation of pending corrections."""
        try:
            # Get recent corrections that haven't been evaluated
            corrections = self.correction_capture.get_corrections(
                since=datetime.now() - timedelta(hours=24),
                limit=100
            )
            
            # Filter out corrections that already have evaluations
            pending_corrections = []
            for correction in corrections:
                if not await self._has_evaluation(correction.correction_id):
                    pending_corrections.append(correction)
            
            if pending_corrections:
                logger.info(f"Running batch evaluation for {len(pending_corrections)} corrections")
                
                # Evaluate in batches
                results = await self.evaluator.batch_evaluate_corrections(pending_corrections)
                
                # Update statistics
                self.stats.corrections_evaluated += len(results)
                self.stats.automatic_evaluations += len(results)
                self.stats.total_evaluations += len(results)
                
                # Store integration results
                for result in results:
                    await self._store_integration_result(result)
                
                logger.info(f"Completed batch evaluation of {len(results)} corrections")
            
        except Exception as e:
            logger.error(f"Batch evaluation failed: {e}")
            self.stats.errors += 1
    
    async def _has_evaluation(self, correction_id: str) -> bool:
        """Check if correction already has an evaluation."""
        # Check if evaluation file exists
        evaluation_files = list(self.evaluator.evaluations_dir.glob(f"*_{correction_id}.json"))
        return len(evaluation_files) > 0
    
    async def _store_integration_result(self, result: EvaluationResult) -> None:
        """Store integration result linking evaluation to correction."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_{timestamp}_{result.evaluation_id}.json"
            
            integration_data = {
                "evaluation_id": result.evaluation_id,
                "correction_id": result.correction_id,
                "agent_type": result.agent_type,
                "overall_score": result.overall_score,
                "evaluation_time_ms": result.evaluation_time_ms,
                "timestamp": datetime.now().isoformat(),
                "integration_type": "automatic" if result.correction_id else "manual"
            }
            
            integration_file = self.integration_dir / filename
            with open(integration_file, 'w') as f:
                json.dump(integration_data, f, indent=2)
            
            logger.debug(f"Stored integration result: {integration_file}")
            
        except Exception as e:
            logger.error(f"Failed to store integration result: {e}")
    
    async def capture_and_evaluate_correction(
        self,
        agent_type: str,
        original_response: str,
        user_correction: str,
        context: Dict[str, Any],
        correction_type: CorrectionType = CorrectionType.CONTENT_CORRECTION,
        subprocess_id: Optional[str] = None,
        task_description: Optional[str] = None,
        severity: str = "medium",
        user_feedback: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Optional[EvaluationResult]]:
        """
        Capture correction and automatically evaluate it.
        
        Args:
            agent_type: Type of agent
            original_response: Original agent response
            user_correction: User's correction
            context: Task context
            correction_type: Type of correction
            subprocess_id: Subprocess ID if applicable
            task_description: Task description
            severity: Severity level
            user_feedback: Additional user feedback
            metadata: Additional metadata
            
        Returns:
            Tuple of (correction_id, evaluation_result)
        """
        try:
            # Capture correction
            correction_id = self.correction_capture.capture_correction(
                agent_type=agent_type,
                original_response=original_response,
                user_correction=user_correction,
                context=context,
                correction_type=correction_type,
                subprocess_id=subprocess_id,
                task_description=task_description,
                severity=severity,
                user_feedback=user_feedback,
                metadata=metadata
            )
            
            evaluation_result = None
            
            # Evaluate if enabled
            if self.enabled and self.auto_evaluate_corrections and correction_id:
                try:
                    # Create correction data for evaluation
                    correction_data = CorrectionData(
                        correction_id=correction_id,
                        agent_type=agent_type,
                        original_response=original_response,
                        user_correction=user_correction,
                        context=context,
                        correction_type=correction_type,
                        timestamp=datetime.now().isoformat(),
                        subprocess_id=subprocess_id,
                        task_description=task_description,
                        severity=severity,
                        user_feedback=user_feedback,
                        metadata=metadata or {}
                    )
                    
                    # Evaluate correction
                    evaluation_result = await self.evaluator.evaluate_correction(correction_data)
                    
                    # Update statistics
                    self.stats.corrections_evaluated += 1
                    self.stats.automatic_evaluations += 1
                    self.stats.total_evaluations += 1
                    self.stats.last_evaluation = datetime.now().isoformat()
                    
                    # Store integration result
                    await self._store_integration_result(evaluation_result)
                    
                    logger.info(f"Captured and evaluated correction {correction_id} (score: {evaluation_result.overall_score:.1f})")
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate correction {correction_id}: {e}")
                    self.stats.errors += 1
            
            return correction_id, evaluation_result
            
        except Exception as e:
            logger.error(f"Failed to capture and evaluate correction: {e}")
            self.stats.errors += 1
            return "", None
    
    async def evaluate_agent_response(
        self,
        agent_type: str,
        response_text: str,
        context: Dict[str, Any],
        store_result: bool = True
    ) -> Optional[EvaluationResult]:
        """
        Evaluate agent response without correction data.
        
        Args:
            agent_type: Type of agent
            response_text: Response to evaluate
            context: Task context
            store_result: Whether to store the result
            
        Returns:
            Evaluation result
        """
        if not self.enabled or not self.auto_evaluate_responses:
            return None
        
        try:
            # Evaluate response
            result = await self.evaluator.evaluate_response(
                agent_type=agent_type,
                response_text=response_text,
                context=context
            )
            
            # Update statistics
            self.stats.manual_evaluations += 1
            self.stats.total_evaluations += 1
            self.stats.last_evaluation = datetime.now().isoformat()
            
            # Store integration result if requested
            if store_result:
                await self._store_integration_result(result)
            
            logger.info(f"Evaluated {agent_type} response (score: {result.overall_score:.1f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to evaluate agent response: {e}")
            self.stats.errors += 1
            return None
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get statistics about evaluation integration."""
        # Get component statistics
        correction_stats = self.correction_capture.get_correction_stats()
        evaluator_stats = self.evaluator.get_evaluation_statistics()
        
        # Update integration stats
        if evaluator_stats.get("total_evaluations", 0) > 0:
            self.stats.average_evaluation_time_ms = evaluator_stats.get("average_time_ms", 0)
            self.stats.cache_hit_rate = evaluator_stats.get("cache_hit_rate", 0)
        
        return {
            "integration_stats": self.stats.to_dict(),
            "correction_stats": correction_stats,
            "evaluator_stats": evaluator_stats,
            "service_enabled": self.enabled,
            "auto_evaluate_corrections": self.auto_evaluate_corrections,
            "auto_evaluate_responses": self.auto_evaluate_responses,
            "batch_evaluation_enabled": self.batch_evaluation_enabled,
            "background_tasks_running": len(self.background_tasks)
        }
    
    async def get_evaluation_history(
        self,
        agent_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get evaluation history with optional filtering.
        
        Args:
            agent_type: Filter by agent type
            since: Only results since this date
            limit: Maximum number of results
            
        Returns:
            List of evaluation history entries
        """
        try:
            history = []
            
            # Load integration results
            if self.integration_dir.exists():
                for integration_file in self.integration_dir.glob("integration_*.json"):
                    try:
                        with open(integration_file, 'r') as f:
                            data = json.load(f)
                        
                        # Apply filters
                        if agent_type and data.get("agent_type") != agent_type:
                            continue
                        
                        if since:
                            result_time = datetime.fromisoformat(data.get("timestamp", ""))
                            if result_time < since:
                                continue
                        
                        history.append(data)
                        
                    except Exception as e:
                        logger.error(f"Failed to load integration result {integration_file}: {e}")
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply limit
            if limit:
                history = history[:limit]
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get evaluation history: {e}")
            return []
    
    async def get_agent_improvement_metrics(self, agent_type: str) -> Dict[str, Any]:
        """
        Get improvement metrics for a specific agent type.
        
        Args:
            agent_type: Type of agent to analyze
            
        Returns:
            Improvement metrics
        """
        try:
            # Get evaluation history for this agent
            history = await self.get_evaluation_history(agent_type=agent_type, limit=100)
            
            if not history:
                return {
                    "agent_type": agent_type,
                    "total_evaluations": 0,
                    "average_score": 0,
                    "improvement_trend": "unknown",
                    "recent_performance": "unknown"
                }
            
            # Calculate metrics
            scores = [entry.get("overall_score", 0) for entry in history]
            average_score = sum(scores) / len(scores)
            
            # Calculate improvement trend (compare first half vs second half)
            if len(scores) >= 10:
                midpoint = len(scores) // 2
                recent_scores = scores[:midpoint]  # Newer scores (reversed order)
                older_scores = scores[midpoint:]
                
                recent_avg = sum(recent_scores) / len(recent_scores)
                older_avg = sum(older_scores) / len(older_scores)
                
                improvement = recent_avg - older_avg
                
                if improvement > 5:
                    trend = "improving"
                elif improvement < -5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            # Recent performance (last 10 evaluations)
            recent_scores = scores[:10]
            recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
            
            if recent_avg >= 85:
                recent_performance = "excellent"
            elif recent_avg >= 75:
                recent_performance = "good"
            elif recent_avg >= 65:
                recent_performance = "fair"
            else:
                recent_performance = "needs_improvement"
            
            return {
                "agent_type": agent_type,
                "total_evaluations": len(history),
                "average_score": average_score,
                "recent_average_score": recent_avg,
                "improvement_trend": trend,
                "recent_performance": recent_performance,
                "score_distribution": {
                    "min": min(scores),
                    "max": max(scores),
                    "median": sorted(scores)[len(scores) // 2] if scores else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get improvement metrics for {agent_type}: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_integration_data(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old integration data.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Cleanup summary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            removed_files = []
            total_size_removed = 0
            
            if self.integration_dir.exists():
                for integration_file in self.integration_dir.glob("integration_*.json"):
                    try:
                        # Check file modification time
                        file_time = datetime.fromtimestamp(integration_file.stat().st_mtime)
                        
                        if file_time < cutoff_date:
                            file_size = integration_file.stat().st_size
                            integration_file.unlink()
                            removed_files.append(str(integration_file))
                            total_size_removed += file_size
                            
                    except Exception as e:
                        logger.error(f"Failed to process {integration_file}: {e}")
            
            # Also cleanup component services
            correction_cleanup = self.correction_capture.cleanup_old_corrections(days_to_keep)
            evaluation_cleanup = await self.evaluator.cleanup_old_evaluations(days_to_keep)
            
            logger.info(f"Integration cleanup completed: removed {len(removed_files)} files, {total_size_removed} bytes")
            
            return {
                "integration_cleanup": {
                    "removed_files": len(removed_files),
                    "total_size_removed": total_size_removed,
                    "files_removed": removed_files if len(removed_files) < 10 else removed_files[:10] + ["..."]
                },
                "correction_cleanup": correction_cleanup,
                "evaluation_cleanup": evaluation_cleanup,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup integration data: {e}")
            return {"error": str(e)}
    
    async def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate comprehensive improvement report."""
        try:
            # Get overall statistics
            stats = self.get_integration_statistics()
            
            # Get agent-specific metrics
            agent_metrics = {}
            correction_stats = stats.get("correction_stats", {})
            
            for agent_type in correction_stats.get("agents_with_corrections", []):
                metrics = await self.get_agent_improvement_metrics(agent_type)
                agent_metrics[agent_type] = metrics
            
            # Get recent evaluation history
            recent_history = await self.get_evaluation_history(limit=20)
            
            # Generate summary
            total_evaluations = stats.get("integration_stats", {}).get("total_evaluations", 0)
            corrections_evaluated = stats.get("integration_stats", {}).get("corrections_evaluated", 0)
            
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_evaluations": total_evaluations,
                    "corrections_evaluated": corrections_evaluated,
                    "evaluation_rate": (corrections_evaluated / total_evaluations) if total_evaluations > 0 else 0,
                    "service_enabled": self.enabled,
                    "average_evaluation_time": stats.get("evaluator_stats", {}).get("average_time_ms", 0)
                },
                "agent_metrics": agent_metrics,
                "recent_activity": recent_history,
                "performance_stats": stats.get("evaluator_stats", {}),
                "correction_stats": correction_stats
            }
            
            # Store report
            report_file = self.integration_dir / f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Generated improvement report: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate improvement report: {e}")
            return {"error": str(e)}


# Global service instance
_integration_service: Optional[EvaluationIntegrationService] = None


def get_integration_service(config: Optional[Config] = None) -> EvaluationIntegrationService:
    """Get global integration service instance."""
    global _integration_service
    
    if _integration_service is None:
        _integration_service = EvaluationIntegrationService(config)
    
    return _integration_service


async def initialize_integration_service(config: Optional[Config] = None) -> Dict[str, Any]:
    """Initialize the evaluation integration service."""
    try:
        service = get_integration_service(config)
        
        # Start background tasks
        await service.start_background_tasks()
        
        # Get initial statistics
        stats = service.get_integration_statistics()
        
        return {
            "initialized": True,
            "service_enabled": service.enabled,
            "auto_evaluate_corrections": service.auto_evaluate_corrections,
            "auto_evaluate_responses": service.auto_evaluate_responses,
            "batch_evaluation_enabled": service.batch_evaluation_enabled,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize integration service: {e}")
        return {"initialized": False, "error": str(e)}


async def shutdown_integration_service() -> None:
    """Shutdown the evaluation integration service."""
    global _integration_service
    
    if _integration_service:
        await _integration_service.stop_background_tasks()
        _integration_service = None


# Helper functions for easy integration
async def capture_and_evaluate_subprocess_correction(
    agent_type: str,
    original_response: str,
    user_correction: str,
    subprocess_id: str,
    task_description: str,
    correction_type: CorrectionType = CorrectionType.CONTENT_CORRECTION,
    severity: str = "medium",
    config: Optional[Config] = None
) -> Tuple[str, Optional[EvaluationResult]]:
    """
    Capture and evaluate subprocess correction.
    
    Args:
        agent_type: Type of agent
        original_response: Original response
        user_correction: User's correction
        subprocess_id: Subprocess ID
        task_description: Task description
        correction_type: Type of correction
        severity: Severity level
        config: Optional configuration
        
    Returns:
        Tuple of (correction_id, evaluation_result)
    """
    service = get_integration_service(config)
    
    return await service.capture_and_evaluate_correction(
        agent_type=agent_type,
        original_response=original_response,
        user_correction=user_correction,
        context={"subprocess_id": subprocess_id, "task_description": task_description},
        correction_type=correction_type,
        subprocess_id=subprocess_id,
        task_description=task_description,
        severity=severity
    )


async def evaluate_task_tool_response(
    agent_type: str,
    response_text: str,
    task_description: str,
    config: Optional[Config] = None
) -> Optional[EvaluationResult]:
    """
    Evaluate Task Tool response.
    
    Args:
        agent_type: Type of agent
        response_text: Response to evaluate
        task_description: Task description
        config: Optional configuration
        
    Returns:
        Evaluation result
    """
    service = get_integration_service(config)
    
    return await service.evaluate_agent_response(
        agent_type=agent_type,
        response_text=response_text,
        context={"task_description": task_description, "source": "task_tool"}
    )


if __name__ == "__main__":
    # Test the integration service
    print("Testing Evaluation Integration Service")
    print("=" * 50)
    
    # Test initialization
    async def test_integration():
        init_result = await initialize_integration_service()
        print(f"Initialization: {init_result['initialized']}")
        print(f"Service enabled: {init_result['service_enabled']}")
        
        if init_result['initialized']:
            # Test correction capture and evaluation
            correction_id, evaluation_result = await capture_and_evaluate_subprocess_correction(
                agent_type="engineer",
                original_response="def hello(): print('hello')",
                user_correction="def hello(): print('Hello, World!')",
                subprocess_id="test_subprocess_123",
                task_description="Create a hello function",
                correction_type=CorrectionType.CONTENT_CORRECTION,
                severity="low"
            )
            
            print(f"Correction ID: {correction_id}")
            if evaluation_result:
                print(f"Evaluation Score: {evaluation_result.overall_score:.1f}")
                print(f"Evaluation Time: {evaluation_result.evaluation_time_ms:.2f}ms")
            
            # Test response evaluation
            response_result = await evaluate_task_tool_response(
                agent_type="engineer",
                response_text="def calculate(a, b): return a + b",
                task_description="Create a calculation function"
            )
            
            if response_result:
                print(f"Response Evaluation Score: {response_result.overall_score:.1f}")
            
            # Get statistics
            service = get_integration_service()
            stats = service.get_integration_statistics()
            print(f"Integration Statistics: {stats['integration_stats']}")
            
            # Cleanup
            await shutdown_integration_service()
        
        else:
            print(f"Initialization failed: {init_result.get('error', 'Unknown error')}")
    
    # Run async test
    asyncio.run(test_integration())