"""
Automated Prompt Improvement Pipeline for Agent Training

This module implements an automated system for improving agent prompts based on
correction patterns, evaluation feedback, and performance metrics.

Key Features:
- Pattern analysis of correction data
- Automated prompt modification algorithms
- Improvement strategy selection
- Prompt template versioning and management
- Agent-specific improvement strategies
- Validation and effectiveness measurement

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import asdict

from claude_pm.services.correction_capture import CorrectionCapture

from .models import (
    ImprovementStrategy, PromptImprovement, CorrectionPattern, 
    ImprovementMetrics, DEFAULT_IMPROVEMENT_THRESHOLD,
    DEFAULT_PATTERN_MIN_FREQUENCY, DEFAULT_VALIDATION_TIMEOUT
)
from .pattern_analyzer import PatternAnalyzer
from .improvement_generator import ImprovementGenerator
from .validator import ImprovementValidator
from .metrics_manager import MetricsManager
from .storage_manager import StorageManager


class PromptImprover:
    """
    Automated prompt improvement pipeline for agent training
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.correction_capture = CorrectionCapture()
        # self.evaluation_system = MirascopeEvaluation()  # Service not available
        self.evaluation_system = None  # Placeholder until service is available
        
        # Storage paths
        self.base_path = Path(self.config.get('base_path', '.claude-pm/prompt_improvement'))
        
        # Initialize managers
        self.storage_manager = StorageManager(self.base_path, self.logger)
        self.pattern_analyzer = PatternAnalyzer(self.logger)
        self.improvement_generator = ImprovementGenerator(self.logger)
        self.metrics_manager = MetricsManager(self.logger)
        
        # Configuration
        self.improvement_threshold = self.config.get('improvement_threshold', DEFAULT_IMPROVEMENT_THRESHOLD)
        self.pattern_min_frequency = self.config.get('pattern_min_frequency', DEFAULT_PATTERN_MIN_FREQUENCY)
        self.validation_timeout = self.config.get('validation_timeout', DEFAULT_VALIDATION_TIMEOUT)
        
        # Initialize validator with threshold
        self.validator = ImprovementValidator(self.improvement_threshold, self.logger)
        
        # In-memory caches
        self.patterns_cache: Dict[str, CorrectionPattern] = {}
        self.improvements_cache: Dict[str, PromptImprovement] = {}
        self.metrics_cache: Dict[str, ImprovementMetrics] = {}
        
        self.logger.info("PromptImprover initialized successfully")
    
    async def analyze_correction_patterns(self, 
                                        agent_type: Optional[str] = None,
                                        days_back: int = 30) -> List[CorrectionPattern]:
        """
        Analyze correction patterns to identify improvement opportunities
        
        Args:
            agent_type: Specific agent type to analyze (optional)
            days_back: Number of days to look back for corrections
            
        Returns:
            List of correction patterns found
        """
        try:
            # Get correction data
            since_date = datetime.now() - timedelta(days=days_back)
            corrections = await self.correction_capture.get_corrections_since(since_date)
            
            if agent_type:
                corrections = [c for c in corrections if c.agent_type == agent_type]
            
            # Analyze patterns
            patterns = await self.pattern_analyzer.extract_patterns(corrections)
            
            # Filter by frequency threshold
            significant_patterns = self.pattern_analyzer.filter_significant_patterns(
                patterns, self.pattern_min_frequency
            )
            
            # Cache patterns
            for pattern in significant_patterns:
                self.patterns_cache[pattern.pattern_id] = pattern
                await self.storage_manager.save_pattern(pattern)
            
            self.logger.info(f"Analyzed {len(corrections)} corrections, found {len(significant_patterns)} significant patterns")
            return significant_patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing correction patterns: {e}")
            return []
    
    async def generate_prompt_improvements(self, 
                                         patterns: List[CorrectionPattern]) -> List[PromptImprovement]:
        """
        Generate prompt improvements based on correction patterns
        
        Args:
            patterns: List of correction patterns to address
            
        Returns:
            List of prompt improvements
        """
        improvements = await self.improvement_generator.generate_improvements(
            patterns,
            self.storage_manager.get_current_prompt,
            self.storage_manager.get_next_version
        )
        
        # Cache improvements
        for improvement in improvements:
            self.improvements_cache[improvement.improvement_id] = improvement
            await self.storage_manager.save_improvement(improvement)
        
        return improvements
    
    async def validate_improvements(self, improvements: List[PromptImprovement]) -> List[PromptImprovement]:
        """
        Validate prompt improvements using A/B testing and metrics
        
        Args:
            improvements: List of improvements to validate
            
        Returns:
            List of validated improvements
        """
        validated = await self.validator.validate_improvements(improvements)
        
        # Update storage for all improvements (including rejected ones)
        for improvement in improvements:
            self.improvements_cache[improvement.improvement_id] = improvement
            await self.storage_manager.save_improvement(improvement)
        
        return validated
    
    async def apply_improvements(self, improvements: List[PromptImprovement]) -> Dict[str, Any]:
        """
        Apply validated improvements to agent prompts
        
        Args:
            improvements: List of validated improvements to apply
            
        Returns:
            Application results
        """
        results = {
            'applied': [],
            'failed': [],
            'backed_up': []
        }
        
        for improvement in improvements:
            if improvement.validation_status != "approved":
                results['failed'].append({
                    'improvement_id': improvement.improvement_id,
                    'reason': 'Not approved for application'
                })
                continue
            
            try:
                # Backup current prompt
                current_prompt = await self.storage_manager.get_current_prompt(improvement.agent_type)
                if current_prompt:
                    backup_result = await self.storage_manager.backup_current_prompt(
                        improvement.agent_type, current_prompt
                    )
                    if backup_result:
                        results['backed_up'].append(backup_result)
                
                # Apply improvement
                success = await self.storage_manager.save_improved_prompt(
                    improvement.agent_type,
                    improvement.version,
                    improvement.improved_prompt
                )
                
                if success:
                    # Update version tracking
                    await self.storage_manager.update_version_tracking(improvement)
                    
                    results['applied'].append({
                        'improvement_id': improvement.improvement_id,
                        'agent_type': improvement.agent_type,
                        'version': improvement.version
                    })
                    
                    # Create and save metrics
                    metrics = await self.metrics_manager.create_improvement_metrics(improvement)
                    self.metrics_cache[improvement.improvement_id] = metrics
                    await self.storage_manager.save_metrics(metrics)
                    
                else:
                    results['failed'].append({
                        'improvement_id': improvement.improvement_id,
                        'reason': 'Failed to apply improvement'
                    })
                
            except Exception as e:
                self.logger.error(f"Error applying improvement {improvement.improvement_id}: {e}")
                results['failed'].append({
                    'improvement_id': improvement.improvement_id,
                    'reason': str(e)
                })
        
        self.logger.info(f"Applied {len(results['applied'])} improvements successfully")
        return results
    
    async def rollback_improvement(self, improvement_id: str, reason: str = "Manual rollback") -> bool:
        """
        Rollback an applied improvement
        
        Args:
            improvement_id: ID of improvement to rollback
            reason: Reason for rollback
            
        Returns:
            True if rollback successful
        """
        try:
            improvement = self.improvements_cache.get(improvement_id)
            if not improvement:
                # Try to load from storage
                improvement = await self.storage_manager.load_improvement(improvement_id)
                if not improvement:
                    return False
            
            # Find backup to restore
            backup_path = await self.storage_manager.find_backup_for_improvement(improvement)
            if not backup_path:
                return False
            
            # Restore backup
            success = await self.storage_manager.restore_prompt_from_backup(
                improvement.agent_type, backup_path
            )
            
            if success:
                # Update improvement record
                improvement.validation_status = "rolled_back"
                improvement.rollback_reason = reason
                await self.storage_manager.save_improvement(improvement)
                
                # Update metrics
                if improvement_id in self.metrics_cache:
                    await self.metrics_manager.update_rollback_metrics(
                        improvement_id, self.metrics_cache[improvement_id]
                    )
                    await self.storage_manager.save_metrics(self.metrics_cache[improvement_id])
                
                self.logger.info(f"Successfully rolled back improvement {improvement_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error rolling back improvement {improvement_id}: {e}")
            
        return False
    
    async def get_improvement_metrics(self, 
                                    agent_type: Optional[str] = None,
                                    days_back: int = 30) -> Dict[str, Any]:
        """
        Get improvement metrics and analytics
        
        Args:
            agent_type: Filter by agent type (optional)
            days_back: Number of days to analyze
            
        Returns:
            Improvement metrics and analytics
        """
        # Load improvements from storage
        since_date = datetime.now() - timedelta(days=days_back)
        improvements = await self.storage_manager.load_improvements_since(since_date)
        
        # Calculate metrics
        metrics = await self.metrics_manager.calculate_improvement_metrics(
            improvements, agent_type, days_back
        )
        
        # Add cache statistics
        metrics['system_status'] = {
            'total_patterns_cached': len(self.patterns_cache),
            'total_improvements_cached': len(self.improvements_cache),
            'total_metrics_cached': len(self.metrics_cache)
        }
        
        return metrics


# Async convenience functions
async def analyze_and_improve_prompts(agent_type: Optional[str] = None,
                                    days_back: int = 30) -> Dict[str, Any]:
    """
    Convenience function to analyze patterns and generate improvements
    
    Args:
        agent_type: Specific agent type to analyze
        days_back: Number of days to look back
        
    Returns:
        Results of analysis and improvement generation
    """
    improver = PromptImprover()
    
    # Analyze patterns
    patterns = await improver.analyze_correction_patterns(agent_type, days_back)
    
    # Generate improvements
    improvements = await improver.generate_prompt_improvements(patterns)
    
    # Validate improvements
    validated = await improver.validate_improvements(improvements)
    
    return {
        'patterns_found': len(patterns),
        'improvements_generated': len(improvements),
        'improvements_validated': len(validated),
        'patterns': [asdict(p) for p in patterns],
        'improvements': [asdict(i) for i in improvements],
        'validated_improvements': [asdict(v) for v in validated]
    }


async def get_improvement_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive improvement dashboard
    
    Returns:
        Dashboard data with metrics and analytics
    """
    improver = PromptImprover()
    
    # Get metrics for different timeframes
    metrics_7d = await improver.get_improvement_metrics(days_back=7)
    metrics_30d = await improver.get_improvement_metrics(days_back=30)
    
    # Get agent-specific metrics
    agent_metrics = {}
    for agent_type in ['Documentation', 'QA', 'Engineer', 'Ops', 'Research']:
        agent_metrics[agent_type] = await improver.get_improvement_metrics(
            agent_type=agent_type, days_back=30
        )
    
    return {
        'dashboard_generated': datetime.now().isoformat(),
        'metrics': {
            'last_7_days': metrics_7d,
            'last_30_days': metrics_30d
        },
        'agent_metrics': agent_metrics
    }


# Export main class and convenience functions
__all__ = [
    'PromptImprover',
    'analyze_and_improve_prompts',
    'get_improvement_dashboard',
    'ImprovementStrategy',
    'PromptImprovement',
    'CorrectionPattern',
    'ImprovementMetrics'
]


if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize improver
        improver = PromptImprover()
        
        # Analyze patterns
        patterns = await improver.analyze_correction_patterns(days_back=30)
        print(f"Found {len(patterns)} patterns")
        
        # Generate improvements
        improvements = await improver.generate_prompt_improvements(patterns)
        print(f"Generated {len(improvements)} improvements")
        
        # Validate improvements
        validated = await improver.validate_improvements(improvements)
        print(f"Validated {len(validated)} improvements")
        
        # Get metrics
        metrics = await improver.get_improvement_metrics()
        print(f"Metrics: {metrics}")
    
    asyncio.run(main())