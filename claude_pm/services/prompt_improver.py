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
Date: 2025-07-15
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import statistics
from pathlib import Path

from claude_pm.services.correction_capture import CorrectionCapture
# from claude_pm.services.mirascope_evaluation import MirascopeEvaluation  # Service not available


class ImprovementStrategy(Enum):
    """Improvement strategy types"""
    ADDITIVE = "additive"          # Add context/instructions
    REPLACEMENT = "replacement"    # Replace problematic sections
    CONTEXTUAL = "contextual"      # Context-aware improvements
    STRUCTURAL = "structural"      # Structural prompt changes


@dataclass
class PromptImprovement:
    """Represents a single prompt improvement"""
    improvement_id: str
    agent_type: str
    strategy: ImprovementStrategy
    original_prompt: str
    improved_prompt: str
    improvement_reason: str
    confidence_score: float
    timestamp: datetime
    version: str
    validation_status: str = "pending"
    effectiveness_score: Optional[float] = None
    rollback_reason: Optional[str] = None


@dataclass
class CorrectionPattern:
    """Represents a pattern found in corrections"""
    pattern_id: str
    agent_type: str
    pattern_type: str
    frequency: int
    severity: str
    common_issues: List[str]
    suggested_improvement: str
    confidence: float
    first_seen: datetime
    last_seen: datetime


@dataclass
class ImprovementMetrics:
    """Metrics for improvement effectiveness"""
    improvement_id: str
    success_rate: float
    error_reduction: float
    performance_improvement: float
    user_satisfaction: float
    rollback_rate: float
    adoption_rate: float


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
        self.patterns_path = self.base_path / 'patterns'
        self.improvements_path = self.base_path / 'improvements'
        self.templates_path = self.base_path / 'templates'
        self.metrics_path = self.base_path / 'metrics'
        
        # Create directories
        for path in [self.patterns_path, self.improvements_path, 
                    self.templates_path, self.metrics_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.improvement_threshold = self.config.get('improvement_threshold', 0.7)
        self.pattern_min_frequency = self.config.get('pattern_min_frequency', 3)
        self.validation_timeout = self.config.get('validation_timeout', 300)
        
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
            patterns = await self._extract_patterns(corrections)
            
            # Filter by frequency threshold
            significant_patterns = [
                p for p in patterns 
                if p.frequency >= self.pattern_min_frequency
            ]
            
            # Cache patterns
            for pattern in significant_patterns:
                self.patterns_cache[pattern.pattern_id] = pattern
                await self._save_pattern(pattern)
            
            self.logger.info(f"Analyzed {len(corrections)} corrections, found {len(significant_patterns)} significant patterns")
            return significant_patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing correction patterns: {e}")
            return []
    
    async def _extract_patterns(self, corrections: List[Any]) -> List[CorrectionPattern]:
        """Extract patterns from correction data"""
        patterns = {}
        
        for correction in corrections:
            # Analyze correction type and context
            pattern_key = f"{correction.agent_type}_{correction.error_type}"
            
            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    'agent_type': correction.agent_type,
                    'pattern_type': correction.error_type,
                    'frequency': 0,
                    'issues': [],
                    'corrections': [],
                    'first_seen': correction.timestamp,
                    'last_seen': correction.timestamp
                }
            
            # Update pattern data
            pattern_data = patterns[pattern_key]
            pattern_data['frequency'] += 1
            pattern_data['issues'].append(correction.issue_description)
            pattern_data['corrections'].append(correction.correction_applied)
            pattern_data['last_seen'] = max(pattern_data['last_seen'], correction.timestamp)
        
        # Convert to CorrectionPattern objects
        pattern_objects = []
        for key, data in patterns.items():
            # Calculate severity based on frequency and impact
            severity = self._calculate_severity(data['frequency'], len(corrections))
            
            # Find common issues
            common_issues = self._find_common_issues(data['issues'])
            
            # Generate improvement suggestion
            suggested_improvement = self._generate_improvement_suggestion(
                data['agent_type'], 
                data['pattern_type'], 
                common_issues
            )
            
            # Calculate confidence
            confidence = min(0.9, data['frequency'] / len(corrections) * 2)
            
            pattern = CorrectionPattern(
                pattern_id=self._generate_pattern_id(key),
                agent_type=data['agent_type'],
                pattern_type=data['pattern_type'],
                frequency=data['frequency'],
                severity=severity,
                common_issues=common_issues,
                suggested_improvement=suggested_improvement,
                confidence=confidence,
                first_seen=data['first_seen'],
                last_seen=data['last_seen']
            )
            
            pattern_objects.append(pattern)
        
        return pattern_objects
    
    def _calculate_severity(self, frequency: int, total_corrections: int) -> str:
        """Calculate severity level based on frequency"""
        percentage = frequency / total_corrections if total_corrections > 0 else 0
        
        if percentage >= 0.3:
            return "high"
        elif percentage >= 0.1:
            return "medium"
        else:
            return "low"
    
    def _find_common_issues(self, issues: List[str]) -> List[str]:
        """Find common issues in the list"""
        # Simple implementation - could be enhanced with NLP
        issue_counts = {}
        for issue in issues:
            words = issue.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    issue_counts[word] = issue_counts.get(word, 0) + 1
        
        # Return top common words/phrases
        common = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [item[0] for item in common]
    
    def _generate_improvement_suggestion(self, 
                                       agent_type: str, 
                                       pattern_type: str, 
                                       common_issues: List[str]) -> str:
        """Generate improvement suggestion based on pattern"""
        suggestions = {
            'Documentation': {
                'format_error': "Add explicit formatting guidelines and examples",
                'incomplete_info': "Include completeness checklist in prompt",
                'version_mismatch': "Add version validation instructions"
            },
            'QA': {
                'test_failure': "Add comprehensive test case templates",
                'incomplete_coverage': "Include coverage requirements in prompt",
                'validation_error': "Add validation step-by-step instructions"
            },
            'Engineer': {
                'syntax_error': "Add syntax validation requirements",
                'logic_error': "Include logical validation steps",
                'performance_issue': "Add performance consideration guidelines"
            }
        }
        
        # Get agent-specific suggestions
        agent_suggestions = suggestions.get(agent_type, {})
        suggestion = agent_suggestions.get(pattern_type, 
                                         f"Review and improve {pattern_type} handling")
        
        # Enhance with common issues
        if common_issues:
            suggestion += f" Focus on: {', '.join(common_issues[:3])}"
        
        return suggestion
    
    def _generate_pattern_id(self, pattern_key: str) -> str:
        """Generate unique pattern ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_val = hashlib.md5(pattern_key.encode()).hexdigest()[:8]
        return f"pattern_{timestamp}_{hash_val}"
    
    async def generate_prompt_improvements(self, 
                                         patterns: List[CorrectionPattern]) -> List[PromptImprovement]:
        """
        Generate prompt improvements based on correction patterns
        
        Args:
            patterns: List of correction patterns to address
            
        Returns:
            List of prompt improvements
        """
        improvements = []
        
        for pattern in patterns:
            try:
                # Get current prompt for agent
                current_prompt = await self._get_current_prompt(pattern.agent_type)
                if not current_prompt:
                    continue
                
                # Select improvement strategy
                strategy = self._select_improvement_strategy(pattern)
                
                # Generate improved prompt
                improved_prompt = await self._apply_improvement_strategy(
                    current_prompt, pattern, strategy
                )
                
                if improved_prompt and improved_prompt != current_prompt:
                    improvement = PromptImprovement(
                        improvement_id=self._generate_improvement_id(),
                        agent_type=pattern.agent_type,
                        strategy=strategy,
                        original_prompt=current_prompt,
                        improved_prompt=improved_prompt,
                        improvement_reason=pattern.suggested_improvement,
                        confidence_score=pattern.confidence,
                        timestamp=datetime.now(),
                        version=self._get_next_version(pattern.agent_type)
                    )
                    
                    improvements.append(improvement)
                    self.improvements_cache[improvement.improvement_id] = improvement
                    await self._save_improvement(improvement)
                
            except Exception as e:
                self.logger.error(f"Error generating improvement for pattern {pattern.pattern_id}: {e}")
                continue
        
        self.logger.info(f"Generated {len(improvements)} prompt improvements")
        return improvements
    
    def _select_improvement_strategy(self, pattern: CorrectionPattern) -> ImprovementStrategy:
        """Select appropriate improvement strategy for pattern"""
        # Strategy selection logic based on pattern characteristics
        if pattern.severity == "high":
            if "format" in pattern.pattern_type.lower():
                return ImprovementStrategy.STRUCTURAL
            else:
                return ImprovementStrategy.REPLACEMENT
        elif pattern.severity == "medium":
            return ImprovementStrategy.CONTEXTUAL
        else:
            return ImprovementStrategy.ADDITIVE
    
    async def _apply_improvement_strategy(self, 
                                        current_prompt: str, 
                                        pattern: CorrectionPattern,
                                        strategy: ImprovementStrategy) -> str:
        """Apply improvement strategy to generate improved prompt"""
        improvement_text = self._get_improvement_text(pattern, strategy)
        
        if strategy == ImprovementStrategy.ADDITIVE:
            return self._apply_additive_improvement(current_prompt, improvement_text)
        elif strategy == ImprovementStrategy.REPLACEMENT:
            return self._apply_replacement_improvement(current_prompt, improvement_text, pattern)
        elif strategy == ImprovementStrategy.CONTEXTUAL:
            return self._apply_contextual_improvement(current_prompt, improvement_text, pattern)
        elif strategy == ImprovementStrategy.STRUCTURAL:
            return self._apply_structural_improvement(current_prompt, improvement_text, pattern)
        
        return current_prompt
    
    def _get_improvement_text(self, pattern: CorrectionPattern, strategy: ImprovementStrategy) -> str:
        """Get improvement text based on pattern and strategy"""
        base_text = pattern.suggested_improvement
        
        if strategy == ImprovementStrategy.ADDITIVE:
            return f"\n\n**Additional Guidelines for {pattern.pattern_type}:**\n{base_text}"
        elif strategy == ImprovementStrategy.REPLACEMENT:
            return f"**Updated {pattern.pattern_type} Requirements:**\n{base_text}"
        elif strategy == ImprovementStrategy.CONTEXTUAL:
            return f"**Context-Aware {pattern.pattern_type} Handling:**\n{base_text}"
        elif strategy == ImprovementStrategy.STRUCTURAL:
            return f"**Structural Requirements for {pattern.pattern_type}:**\n{base_text}"
        
        return base_text
    
    def _apply_additive_improvement(self, prompt: str, improvement: str) -> str:
        """Apply additive improvement strategy"""
        # Add improvement at the end of the prompt
        return f"{prompt}\n{improvement}"
    
    def _apply_replacement_improvement(self, prompt: str, improvement: str, pattern: CorrectionPattern) -> str:
        """Apply replacement improvement strategy"""
        # Replace sections related to the pattern
        # Simple implementation - could be enhanced with better text processing
        lines = prompt.split('\n')
        improved_lines = []
        
        for line in lines:
            if pattern.pattern_type.lower() in line.lower():
                improved_lines.append(improvement)
            else:
                improved_lines.append(line)
        
        return '\n'.join(improved_lines)
    
    def _apply_contextual_improvement(self, prompt: str, improvement: str, pattern: CorrectionPattern) -> str:
        """Apply contextual improvement strategy"""
        # Add context-aware improvements in relevant sections
        sections = prompt.split('\n\n')
        improved_sections = []
        
        for section in sections:
            improved_sections.append(section)
            if pattern.agent_type.lower() in section.lower():
                improved_sections.append(improvement)
        
        return '\n\n'.join(improved_sections)
    
    def _apply_structural_improvement(self, prompt: str, improvement: str, pattern: CorrectionPattern) -> str:
        """Apply structural improvement strategy"""
        # Add structural improvements at the beginning
        return f"{improvement}\n\n{prompt}"
    
    async def validate_improvements(self, improvements: List[PromptImprovement]) -> List[PromptImprovement]:
        """
        Validate prompt improvements using A/B testing and metrics
        
        Args:
            improvements: List of improvements to validate
            
        Returns:
            List of validated improvements
        """
        validated = []
        
        for improvement in improvements:
            try:
                # Run validation tests
                validation_result = await self._run_validation_test(improvement)
                
                if validation_result['success']:
                    improvement.validation_status = "approved"
                    improvement.effectiveness_score = validation_result['effectiveness']
                    validated.append(improvement)
                    
                    # Update cache and storage
                    self.improvements_cache[improvement.improvement_id] = improvement
                    await self._save_improvement(improvement)
                    
                else:
                    improvement.validation_status = "rejected"
                    improvement.rollback_reason = validation_result.get('reason', 'Validation failed')
                    await self._save_improvement(improvement)
                
            except Exception as e:
                self.logger.error(f"Error validating improvement {improvement.improvement_id}: {e}")
                improvement.validation_status = "error"
                improvement.rollback_reason = str(e)
                await self._save_improvement(improvement)
        
        self.logger.info(f"Validated {len(validated)} out of {len(improvements)} improvements")
        return validated
    
    async def _run_validation_test(self, improvement: PromptImprovement) -> Dict[str, Any]:
        """Run validation test for improvement"""
        try:
            # Create test scenarios
            test_scenarios = await self._create_test_scenarios(improvement.agent_type)
            
            # Test original prompt
            original_results = await self._test_prompt_performance(
                improvement.original_prompt, 
                test_scenarios
            )
            
            # Test improved prompt
            improved_results = await self._test_prompt_performance(
                improvement.improved_prompt, 
                test_scenarios
            )
            
            # Calculate effectiveness
            effectiveness = self._calculate_effectiveness(original_results, improved_results)
            
            # Success criteria
            success = effectiveness > self.improvement_threshold
            
            return {
                'success': success,
                'effectiveness': effectiveness,
                'original_score': original_results['average_score'],
                'improved_score': improved_results['average_score'],
                'reason': f"Effectiveness: {effectiveness:.2f}" if success else "Below threshold"
            }
            
        except Exception as e:
            return {
                'success': False,
                'effectiveness': 0.0,
                'reason': f"Validation error: {str(e)}"
            }
    
    async def _create_test_scenarios(self, agent_type: str) -> List[Dict[str, Any]]:
        """Create test scenarios for agent type"""
        scenarios = {
            'Documentation': [
                {'task': 'Generate changelog', 'expected_elements': ['version', 'changes', 'date']},
                {'task': 'Update README', 'expected_elements': ['structure', 'examples', 'usage']},
                {'task': 'API documentation', 'expected_elements': ['endpoints', 'parameters', 'responses']}
            ],
            'QA': [
                {'task': 'Run test suite', 'expected_elements': ['coverage', 'results', 'failures']},
                {'task': 'Validate code', 'expected_elements': ['syntax', 'logic', 'standards']},
                {'task': 'Performance test', 'expected_elements': ['metrics', 'benchmarks', 'analysis']}
            ],
            'Engineer': [
                {'task': 'Implement feature', 'expected_elements': ['code', 'tests', 'documentation']},
                {'task': 'Fix bug', 'expected_elements': ['diagnosis', 'solution', 'prevention']},
                {'task': 'Optimize performance', 'expected_elements': ['analysis', 'improvements', 'metrics']}
            ]
        }
        
        return scenarios.get(agent_type, [
            {'task': 'Generic task', 'expected_elements': ['completion', 'quality', 'documentation']}
        ])
    
    async def _test_prompt_performance(self, prompt: str, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test prompt performance against scenarios"""
        results = []
        
        for scenario in scenarios:
            try:
                # Use evaluation system to test prompt
                if self.evaluation_system:
                    result = await self.evaluation_system.evaluate_prompt(
                        prompt, 
                        scenario['task'], 
                        scenario['expected_elements']
                    )
                else:
                    # Placeholder result when evaluation system is not available
                    result = {
                        'success': True,
                        'score': 0.5,
                        'details': 'Evaluation system not available - placeholder result'
                    }
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error testing scenario: {e}")
                results.append({'score': 0.0, 'error': str(e)})
        
        # Calculate average performance
        scores = [r.get('score', 0.0) for r in results]
        average_score = statistics.mean(scores) if scores else 0.0
        
        return {
            'results': results,
            'average_score': average_score,
            'total_scenarios': len(scenarios),
            'successful_scenarios': len([r for r in results if r.get('score', 0) > 0.5])
        }
    
    def _calculate_effectiveness(self, original: Dict[str, Any], improved: Dict[str, Any]) -> float:
        """Calculate improvement effectiveness"""
        original_score = original.get('average_score', 0.0)
        improved_score = improved.get('average_score', 0.0)
        
        if original_score == 0:
            return 1.0 if improved_score > 0 else 0.0
        
        return (improved_score - original_score) / original_score
    
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
                backup_result = await self._backup_current_prompt(improvement.agent_type)
                if backup_result:
                    results['backed_up'].append(backup_result)
                
                # Apply improvement
                success = await self._apply_improvement_to_agent(improvement)
                
                if success:
                    results['applied'].append({
                        'improvement_id': improvement.improvement_id,
                        'agent_type': improvement.agent_type,
                        'version': improvement.version
                    })
                    
                    # Update metrics
                    await self._update_improvement_metrics(improvement)
                    
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
    
    async def _backup_current_prompt(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Backup current prompt before applying improvement"""
        try:
            current_prompt = await self._get_current_prompt(agent_type)
            if current_prompt:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.templates_path / f"{agent_type}_backup_{timestamp}.txt"
                
                with open(backup_path, 'w') as f:
                    f.write(current_prompt)
                
                return {
                    'agent_type': agent_type,
                    'backup_path': str(backup_path),
                    'timestamp': timestamp
                }
                
        except Exception as e:
            self.logger.error(f"Error backing up prompt for {agent_type}: {e}")
            
        return None
    
    async def _apply_improvement_to_agent(self, improvement: PromptImprovement) -> bool:
        """Apply improvement to agent prompt"""
        try:
            # This would integrate with actual agent prompt storage system
            # For now, save to template file
            template_path = self.templates_path / f"{improvement.agent_type}_v{improvement.version}.txt"
            
            with open(template_path, 'w') as f:
                f.write(improvement.improved_prompt)
            
            # Update version tracking
            version_info = {
                'agent_type': improvement.agent_type,
                'version': improvement.version,
                'improvement_id': improvement.improvement_id,
                'timestamp': improvement.timestamp.isoformat(),
                'strategy': improvement.strategy.value
            }
            
            version_path = self.templates_path / f"{improvement.agent_type}_versions.json"
            versions = []
            
            if version_path.exists():
                with open(version_path, 'r') as f:
                    versions = json.load(f)
            
            versions.append(version_info)
            
            with open(version_path, 'w') as f:
                json.dump(versions, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying improvement to {improvement.agent_type}: {e}")
            return False
    
    async def _update_improvement_metrics(self, improvement: PromptImprovement):
        """Update metrics for applied improvement"""
        try:
            metrics = ImprovementMetrics(
                improvement_id=improvement.improvement_id,
                success_rate=0.0,  # To be updated with actual usage data
                error_reduction=0.0,
                performance_improvement=improvement.effectiveness_score or 0.0,
                user_satisfaction=0.0,
                rollback_rate=0.0,
                adoption_rate=1.0  # Initially 100% since it's applied
            )
            
            self.metrics_cache[improvement.improvement_id] = metrics
            await self._save_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"Error updating metrics for {improvement.improvement_id}: {e}")
    
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
                improvement = await self._load_improvement(improvement_id)
                if not improvement:
                    return False
            
            # Find backup to restore
            backup_path = await self._find_backup_for_improvement(improvement)
            if not backup_path:
                return False
            
            # Restore backup
            with open(backup_path, 'r') as f:
                original_prompt = f.read()
            
            # Apply rollback
            success = await self._apply_rollback(improvement.agent_type, original_prompt)
            
            if success:
                # Update improvement record
                improvement.validation_status = "rolled_back"
                improvement.rollback_reason = reason
                await self._save_improvement(improvement)
                
                # Update metrics
                if improvement_id in self.metrics_cache:
                    self.metrics_cache[improvement_id].rollback_rate = 1.0
                    await self._save_metrics(self.metrics_cache[improvement_id])
                
                self.logger.info(f"Successfully rolled back improvement {improvement_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error rolling back improvement {improvement_id}: {e}")
            
        return False
    
    async def _find_backup_for_improvement(self, improvement: PromptImprovement) -> Optional[Path]:
        """Find backup file for improvement"""
        backup_pattern = f"{improvement.agent_type}_backup_*.txt"
        backup_files = list(self.templates_path.glob(backup_pattern))
        
        if not backup_files:
            return None
        
        # Return most recent backup before improvement timestamp
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files[0]
    
    async def _apply_rollback(self, agent_type: str, original_prompt: str) -> bool:
        """Apply rollback by restoring original prompt"""
        try:
            # This would integrate with actual agent prompt storage system
            current_template = self.templates_path / f"{agent_type}_current.txt"
            
            with open(current_template, 'w') as f:
                f.write(original_prompt)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying rollback for {agent_type}: {e}")
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
        try:
            # Load all improvements from timeframe
            since_date = datetime.now() - timedelta(days=days_back)
            improvements = await self._load_improvements_since(since_date)
            
            if agent_type:
                improvements = [i for i in improvements if i.agent_type == agent_type]
            
            # Calculate metrics
            total_improvements = len(improvements)
            approved_improvements = len([i for i in improvements if i.validation_status == "approved"])
            applied_improvements = len([i for i in improvements if i.validation_status == "approved"])
            rolled_back = len([i for i in improvements if i.validation_status == "rolled_back"])
            
            # Effectiveness metrics
            effectiveness_scores = [i.effectiveness_score for i in improvements if i.effectiveness_score is not None]
            avg_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0
            
            # Strategy distribution
            strategy_counts = {}
            for improvement in improvements:
                strategy = improvement.strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            # Agent type distribution
            agent_counts = {}
            for improvement in improvements:
                agent_type = improvement.agent_type
                agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
            
            return {
                'period': {
                    'days_back': days_back,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'summary': {
                    'total_improvements': total_improvements,
                    'approved_improvements': approved_improvements,
                    'applied_improvements': applied_improvements,
                    'rolled_back': rolled_back,
                    'approval_rate': approved_improvements / total_improvements if total_improvements > 0 else 0.0,
                    'rollback_rate': rolled_back / applied_improvements if applied_improvements > 0 else 0.0
                },
                'effectiveness': {
                    'average_effectiveness': avg_effectiveness,
                    'improvements_with_scores': len(effectiveness_scores),
                    'effectiveness_distribution': self._calculate_effectiveness_distribution(effectiveness_scores)
                },
                'strategy_distribution': strategy_counts,
                'agent_distribution': agent_counts,
                'recent_improvements': [
                    {
                        'improvement_id': i.improvement_id,
                        'agent_type': i.agent_type,
                        'strategy': i.strategy.value,
                        'status': i.validation_status,
                        'effectiveness': i.effectiveness_score,
                        'timestamp': i.timestamp.isoformat()
                    }
                    for i in sorted(improvements, key=lambda x: x.timestamp, reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting improvement metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_effectiveness_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate effectiveness score distribution"""
        if not scores:
            return {}
        
        ranges = {
            'excellent': 0,  # > 0.8
            'good': 0,       # 0.6 - 0.8
            'moderate': 0,   # 0.4 - 0.6
            'poor': 0        # < 0.4
        }
        
        for score in scores:
            if score > 0.8:
                ranges['excellent'] += 1
            elif score > 0.6:
                ranges['good'] += 1
            elif score > 0.4:
                ranges['moderate'] += 1
            else:
                ranges['poor'] += 1
        
        return ranges
    
    # Storage methods
    async def _save_pattern(self, pattern: CorrectionPattern):
        """Save correction pattern to storage"""
        try:
            pattern_file = self.patterns_path / f"{pattern.pattern_id}.json"
            with open(pattern_file, 'w') as f:
                # Convert datetime objects to ISO format
                pattern_dict = asdict(pattern)
                pattern_dict['first_seen'] = pattern.first_seen.isoformat()
                pattern_dict['last_seen'] = pattern.last_seen.isoformat()
                json.dump(pattern_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving pattern {pattern.pattern_id}: {e}")
    
    async def _save_improvement(self, improvement: PromptImprovement):
        """Save improvement to storage"""
        try:
            improvement_file = self.improvements_path / f"{improvement.improvement_id}.json"
            with open(improvement_file, 'w') as f:
                # Convert datetime and enum objects
                improvement_dict = asdict(improvement)
                improvement_dict['timestamp'] = improvement.timestamp.isoformat()
                improvement_dict['strategy'] = improvement.strategy.value
                json.dump(improvement_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving improvement {improvement.improvement_id}: {e}")
    
    async def _save_metrics(self, metrics: ImprovementMetrics):
        """Save improvement metrics to storage"""
        try:
            metrics_file = self.metrics_path / f"{metrics.improvement_id}.json"
            with open(metrics_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving metrics {metrics.improvement_id}: {e}")
    
    async def _load_improvement(self, improvement_id: str) -> Optional[PromptImprovement]:
        """Load improvement from storage"""
        try:
            improvement_file = self.improvements_path / f"{improvement_id}.json"
            if not improvement_file.exists():
                return None
            
            with open(improvement_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to objects
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            data['strategy'] = ImprovementStrategy(data['strategy'])
            
            return PromptImprovement(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading improvement {improvement_id}: {e}")
            return None
    
    async def _load_improvements_since(self, since_date: datetime) -> List[PromptImprovement]:
        """Load improvements since given date"""
        improvements = []
        
        try:
            for improvement_file in self.improvements_path.glob("*.json"):
                improvement = await self._load_improvement(improvement_file.stem)
                if improvement and improvement.timestamp >= since_date:
                    improvements.append(improvement)
                    
        except Exception as e:
            self.logger.error(f"Error loading improvements since {since_date}: {e}")
        
        return improvements
    
    async def _get_current_prompt(self, agent_type: str) -> Optional[str]:
        """Get current prompt for agent type"""
        try:
            # This would integrate with actual agent prompt storage system
            # For now, simulate with template file
            template_path = self.templates_path / f"{agent_type}_current.txt"
            
            if template_path.exists():
                with open(template_path, 'r') as f:
                    return f.read()
            
            # Return default prompt if none exists
            return f"Default prompt for {agent_type} agent"
            
        except Exception as e:
            self.logger.error(f"Error getting current prompt for {agent_type}: {e}")
            return None
    
    def _get_next_version(self, agent_type: str) -> str:
        """Get next version number for agent type"""
        try:
            version_path = self.templates_path / f"{agent_type}_versions.json"
            
            if version_path.exists():
                with open(version_path, 'r') as f:
                    versions = json.load(f)
                
                if versions:
                    # Get latest version and increment
                    latest_version = max(versions, key=lambda x: x['timestamp'])['version']
                    version_parts = latest_version.split('.')
                    version_parts[-1] = str(int(version_parts[-1]) + 1)
                    return '.'.join(version_parts)
            
            return "1.0.0"
            
        except Exception as e:
            self.logger.error(f"Error getting next version for {agent_type}: {e}")
            return "1.0.0"
    
    def _generate_improvement_id(self) -> str:
        """Generate unique improvement ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        return f"improvement_{timestamp}_{uuid.uuid4().hex[:8]}"


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
        'agent_metrics': agent_metrics,
        'system_status': {
            'total_patterns_cached': len(improver.patterns_cache),
            'total_improvements_cached': len(improver.improvements_cache),
            'total_metrics_cached': len(improver.metrics_cache)
        }
    }


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