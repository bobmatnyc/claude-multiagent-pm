"""
Analytics and trend analysis functionality for prompt validation.

This module provides comprehensive analytics capabilities including
test trends, scenario performance analysis, and metric visualization.
"""

import statistics
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .models import TestResult


class AnalyticsEngine:
    """Handles analytics and trend analysis for prompt validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_test_analytics(self, 
                               all_results: List[TestResult],
                               prompt_id: Optional[str] = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """
        Get test analytics and metrics
        
        Args:
            all_results: List of all test results
            prompt_id: Specific prompt to analyze (optional)
            days_back: Number of days to analyze
            
        Returns:
            Test analytics data
        """
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Filter results by date
            filtered_results = [r for r in all_results if r.timestamp >= since_date]
            
            if prompt_id:
                filtered_results = [r for r in filtered_results if r.prompt_version == prompt_id]
            
            # Calculate analytics
            analytics = {
                'period': {
                    'days_back': days_back,
                    'start_date': since_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'summary': self._calculate_summary_metrics(filtered_results),
                'performance_metrics': self._calculate_performance_metrics(filtered_results),
                'test_trends': self._calculate_test_trends(filtered_results),
                'scenario_analysis': self._analyze_scenario_performance(filtered_results),
                'recent_tests': self._get_recent_tests(filtered_results, limit=10)
            }
            
            # Add quality insights
            analytics['quality_insights'] = self._generate_quality_insights(analytics)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting test analytics: {e}")
            return {'error': str(e)}
    
    def _calculate_summary_metrics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate summary metrics"""
        if not results:
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'average_score': 0.0,
                'success_rate': 0.0
            }
        
        passed_tests = [r for r in results if r.success]
        failed_tests = [r for r in results if not r.success]
        
        return {
            'total_tests': len(results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'average_score': statistics.mean([r.score for r in passed_tests]) if passed_tests else 0.0,
            'success_rate': len(passed_tests) / len(results)
        }
    
    def _calculate_performance_metrics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not results:
            return {
                'avg_execution_time': 0.0,
                'min_execution_time': 0.0,
                'max_execution_time': 0.0
            }
        
        execution_times = [r.execution_time for r in results]
        
        metrics = {
            'avg_execution_time': statistics.mean(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times)
        }
        
        # Add percentiles if enough data
        if len(execution_times) >= 10:
            sorted_times = sorted(execution_times)
            metrics['median_execution_time'] = statistics.median(sorted_times)
            metrics['p95_execution_time'] = sorted_times[int(len(sorted_times) * 0.95)]
            metrics['p99_execution_time'] = sorted_times[int(len(sorted_times) * 0.99)]
        
        return metrics
    
    def _calculate_test_trends(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate test trends over time"""
        try:
            if not results:
                return {}
            
            # Sort by timestamp
            sorted_results = sorted(results, key=lambda r: r.timestamp)
            
            # Calculate daily trends
            daily_stats = {}
            for result in sorted_results:
                date_key = result.timestamp.date()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'total': 0,
                        'passed': 0,
                        'scores': []
                    }
                
                daily_stats[date_key]['total'] += 1
                if result.success:
                    daily_stats[date_key]['passed'] += 1
                    daily_stats[date_key]['scores'].append(result.score)
            
            # Calculate trend metrics
            dates = sorted(daily_stats.keys())
            success_rates = []
            avg_scores = []
            
            for date in dates:
                stats = daily_stats[date]
                success_rate = stats['passed'] / stats['total']
                avg_score = statistics.mean(stats['scores']) if stats['scores'] else 0.0
                
                success_rates.append(success_rate)
                avg_scores.append(avg_score)
            
            # Calculate trend direction
            trend_info = self._analyze_trend_direction(success_rates, avg_scores)
            
            # Format daily stats
            formatted_daily_stats = {
                str(date): {
                    'success_rate': daily_stats[date]['passed'] / daily_stats[date]['total'],
                    'avg_score': statistics.mean(daily_stats[date]['scores']) if daily_stats[date]['scores'] else 0.0,
                    'total_tests': daily_stats[date]['total']
                }
                for date in dates
            }
            
            return {
                'success_rate_trend': trend_info['success_trend'],
                'score_trend': trend_info['score_trend'],
                'trend_summary': trend_info['summary'],
                'daily_stats': formatted_daily_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating test trends: {e}")
            return {}
    
    def _analyze_trend_direction(self, success_rates: List[float], avg_scores: List[float]) -> Dict[str, str]:
        """Analyze trend direction and provide summary"""
        if len(success_rates) < 2:
            return {
                'success_trend': 'stable',
                'score_trend': 'stable',
                'summary': 'Insufficient data for trend analysis'
            }
        
        # Calculate trend using simple linear regression
        success_trend = self._calculate_simple_trend(success_rates)
        score_trend = self._calculate_simple_trend(avg_scores)
        
        # Generate summary
        summary_parts = []
        if success_trend > 0.05:
            summary_parts.append("Success rate is improving")
        elif success_trend < -0.05:
            summary_parts.append("Success rate is declining")
        else:
            summary_parts.append("Success rate is stable")
        
        if score_trend > 0.05:
            summary_parts.append("quality scores are improving")
        elif score_trend < -0.05:
            summary_parts.append("quality scores are declining")
        else:
            summary_parts.append("quality scores are stable")
        
        return {
            'success_trend': 'improving' if success_trend > 0.05 else ('declining' if success_trend < -0.05 else 'stable'),
            'score_trend': 'improving' if score_trend > 0.05 else ('declining' if score_trend < -0.05 else 'stable'),
            'summary': ' and '.join(summary_parts)
        }
    
    def _calculate_simple_trend(self, values: List[float]) -> float:
        """Calculate simple trend coefficient"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression coefficient
        n = len(values)
        x_values = list(range(n))
        
        mean_x = sum(x_values) / n
        mean_y = sum(values) / n
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
        denominator = sum((x - mean_x) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _analyze_scenario_performance(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze performance by scenario"""
        try:
            scenario_stats = {}
            
            for result in results:
                scenario_id = result.scenario_id
                if scenario_id not in scenario_stats:
                    scenario_stats[scenario_id] = {
                        'total_tests': 0,
                        'passed_tests': 0,
                        'scores': [],
                        'execution_times': []
                    }
                
                stats = scenario_stats[scenario_id]
                stats['total_tests'] += 1
                stats['execution_times'].append(result.execution_time)
                
                if result.success:
                    stats['passed_tests'] += 1
                    stats['scores'].append(result.score)
            
            # Calculate metrics for each scenario
            scenario_analysis = {}
            for scenario_id, stats in scenario_stats.items():
                scenario_analysis[scenario_id] = {
                    'success_rate': stats['passed_tests'] / stats['total_tests'],
                    'avg_score': statistics.mean(stats['scores']) if stats['scores'] else 0.0,
                    'avg_execution_time': statistics.mean(stats['execution_times']),
                    'total_tests': stats['total_tests']
                }
            
            # Identify best and worst performing scenarios
            if scenario_analysis:
                sorted_scenarios = sorted(
                    scenario_analysis.items(),
                    key=lambda x: x[1]['success_rate'],
                    reverse=True
                )
                
                return {
                    'scenarios': scenario_analysis,
                    'best_performing': sorted_scenarios[0][0] if sorted_scenarios else None,
                    'worst_performing': sorted_scenarios[-1][0] if sorted_scenarios else None
                }
            
            return scenario_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing scenario performance: {e}")
            return {}
    
    def _get_recent_tests(self, results: List[TestResult], limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent test results formatted"""
        sorted_results = sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                'test_id': r.test_id,
                'scenario_id': r.scenario_id,
                'success': r.success,
                'score': r.score,
                'execution_time': r.execution_time,
                'timestamp': r.timestamp.isoformat()
            }
            for r in sorted_results
        ]
    
    def _generate_quality_insights(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate quality insights based on analytics"""
        insights = []
        
        # Success rate insights
        success_rate = analytics['summary']['success_rate']
        if success_rate < 0.7:
            insights.append("Low success rate indicates prompt clarity issues")
        elif success_rate > 0.9:
            insights.append("Excellent success rate shows strong prompt effectiveness")
        
        # Performance insights
        avg_time = analytics['performance_metrics']['avg_execution_time']
        if avg_time > 5.0:
            insights.append("High execution times suggest prompt optimization needed")
        elif avg_time < 1.0:
            insights.append("Excellent performance with fast execution times")
        
        # Trend insights
        trends = analytics.get('test_trends', {})
        if trends.get('success_rate_trend') == 'improving':
            insights.append("Positive trend in success rates shows continuous improvement")
        elif trends.get('success_rate_trend') == 'declining':
            insights.append("Declining success rates require immediate attention")
        
        # Scenario insights
        scenario_analysis = analytics.get('scenario_analysis', {})
        if scenario_analysis.get('worst_performing'):
            insights.append(f"Focus improvement efforts on scenario: {scenario_analysis['worst_performing']}")
        
        return insights