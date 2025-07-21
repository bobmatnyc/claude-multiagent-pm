"""
Pattern analysis and extraction module

This module handles the analysis of correction patterns and extraction of
improvement opportunities from correction data.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib

from .models import CorrectionPattern, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW


class PatternAnalyzer:
    """Analyzes correction patterns to identify improvement opportunities"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    async def extract_patterns(self, corrections: List[Any]) -> List[CorrectionPattern]:
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
            return SEVERITY_HIGH
        elif percentage >= 0.1:
            return SEVERITY_MEDIUM
        else:
            return SEVERITY_LOW
    
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
    
    def filter_significant_patterns(self, patterns: List[CorrectionPattern], 
                                   min_frequency: int) -> List[CorrectionPattern]:
        """Filter patterns by frequency threshold"""
        return [p for p in patterns if p.frequency >= min_frequency]