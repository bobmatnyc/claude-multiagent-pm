"""
Improvement strategy and generation module

This module handles the generation of prompt improvements based on correction
patterns using various improvement strategies.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import List, Optional
import uuid

from .models import (
    CorrectionPattern, PromptImprovement, ImprovementStrategy,
    SEVERITY_HIGH, SEVERITY_MEDIUM
)


class ImprovementGenerator:
    """Generates prompt improvements based on correction patterns"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    async def generate_improvements(self, 
                                  patterns: List[CorrectionPattern],
                                  get_current_prompt_func,
                                  get_next_version_func) -> List[PromptImprovement]:
        """
        Generate prompt improvements based on correction patterns
        
        Args:
            patterns: List of correction patterns to address
            get_current_prompt_func: Function to get current prompt for agent
            get_next_version_func: Function to get next version number
            
        Returns:
            List of prompt improvements
        """
        improvements = []
        
        for pattern in patterns:
            try:
                # Get current prompt for agent
                current_prompt = await get_current_prompt_func(pattern.agent_type)
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
                        version=get_next_version_func(pattern.agent_type)
                    )
                    
                    improvements.append(improvement)
                
            except Exception as e:
                self.logger.error(f"Error generating improvement for pattern {pattern.pattern_id}: {e}")
                continue
        
        self.logger.info(f"Generated {len(improvements)} prompt improvements")
        return improvements
    
    def _select_improvement_strategy(self, pattern: CorrectionPattern) -> ImprovementStrategy:
        """Select appropriate improvement strategy for pattern"""
        # Strategy selection logic based on pattern characteristics
        if pattern.severity == SEVERITY_HIGH:
            if "format" in pattern.pattern_type.lower():
                return ImprovementStrategy.STRUCTURAL
            else:
                return ImprovementStrategy.REPLACEMENT
        elif pattern.severity == SEVERITY_MEDIUM:
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
    
    def _generate_improvement_id(self) -> str:
        """Generate unique improvement ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"improvement_{timestamp}_{uuid.uuid4().hex[:8]}"