"""
Utility functions for prompt validation framework.

This module contains helper functions and utilities used throughout
the prompt validation system.
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any

from .models import TestResult


def generate_scenario_id(name: str) -> str:
    """Generate unique scenario ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_val = hashlib.md5(name.encode()).hexdigest()[:8]
    return f"scenario_{timestamp}_{hash_val}"


def generate_test_id(prompt_id: str, test_type: str) -> str:
    """Generate unique test ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_val = hashlib.md5(f"{prompt_id}_{test_type}".encode()).hexdigest()[:8]
    return f"test_{timestamp}_{hash_val}"


def generate_ab_test_id(prompt_a_id: str, prompt_b_id: str) -> str:
    """Generate unique A/B test ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_val = hashlib.md5(f"{prompt_a_id}_{prompt_b_id}".encode()).hexdigest()[:8]
    return f"ab_test_{timestamp}_{hash_val}"


def generate_report_id(prompt_id: str) -> str:
    """Generate unique report ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_val = hashlib.md5(prompt_id.encode()).hexdigest()[:8]
    return f"report_{timestamp}_{hash_val}"


def generate_recommendations(test_results: List[TestResult]) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    if not test_results:
        return ["No test results available for analysis"]
    
    # Calculate metrics
    success_rate = len([r for r in test_results if r.success]) / len(test_results)
    successful_results = [r for r in test_results if r.success]
    
    if successful_results:
        avg_score = sum(r.score for r in successful_results) / len(successful_results)
    else:
        avg_score = 0.0
    
    # Generate recommendations based on performance
    if success_rate < 0.7:
        recommendations.append("Low success rate - review prompt clarity and instructions")
    
    if avg_score < 0.6:
        recommendations.append("Low quality scores - enhance prompt with better examples and guidance")
    
    # Analyze common failure patterns
    failed_scenarios = [r.scenario_id for r in test_results if not r.success]
    if failed_scenarios:
        scenario_counts = {}
        for scenario_id in failed_scenarios:
            scenario_counts[scenario_id] = scenario_counts.get(scenario_id, 0) + 1
        
        most_failed = max(scenario_counts, key=scenario_counts.get)
        recommendations.append(f"Focus on improving performance for scenario: {most_failed}")
    
    # Performance recommendations
    slow_tests = [r for r in test_results if r.execution_time > 5.0]
    if slow_tests:
        recommendations.append("Consider optimizing prompt for better performance")
    
    # If everything is good
    if success_rate >= 0.9 and avg_score >= 0.8:
        recommendations.append("Excellent performance - consider this prompt for production use")
    
    return recommendations


def format_metrics_summary(metrics: Dict[str, Any]) -> str:
    """Format metrics into a human-readable summary"""
    parts = []
    
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'rate' in key or 'score' in key:
                parts.append(f"{key.replace('_', ' ').title()}: {value:.1%}")
            elif 'time' in key:
                parts.append(f"{key.replace('_', ' ').title()}: {value:.2f}s")
            else:
                parts.append(f"{key.replace('_', ' ').title()}: {value:.2f}")
        else:
            parts.append(f"{key.replace('_', ' ').title()}: {value}")
    
    return " | ".join(parts)