"""
Pattern Analysis System for Agent Prompt Improvement

This module provides advanced pattern analysis capabilities for identifying
improvement opportunities in agent prompts based on correction data and
performance metrics.

Key Features:
- Statistical pattern detection
- Semantic similarity analysis
- Trend analysis and forecasting
- Multi-dimensional pattern classification
- Performance correlation analysis

Author: Claude PM Framework
Date: 2025-07-15
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import re
from collections import Counter, defaultdict
from pathlib import Path
import math

# For semantic analysis (would need to be installed)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_ML = True
except ImportError:
    HAS_ML = False


class PatternType(Enum):
    """Types of patterns that can be detected"""
    RECURRING_ERROR = "recurring_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONTEXT_MISMATCH = "context_mismatch"
    FORMAT_INCONSISTENCY = "format_inconsistency"
    LOGIC_FAILURE = "logic_failure"
    TIMEOUT_ISSUE = "timeout_issue"
    VALIDATION_FAILURE = "validation_failure"
    SEMANTIC_DRIFT = "semantic_drift"


@dataclass
class PatternMetrics:
    """Metrics for a detected pattern"""
    pattern_id: str
    frequency: int
    severity_score: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    confidence: float
    impact_score: float
    prediction_accuracy: float
    correlation_strength: float


@dataclass
class PatternCluster:
    """Cluster of related patterns"""
    cluster_id: str
    patterns: List[str]
    centroid_description: str
    similarity_score: float
    cluster_size: int
    dominant_agent_type: str


@dataclass
class PatternTrend:
    """Trend analysis for patterns"""
    pattern_id: str
    trend_type: str
    slope: float
    r_squared: float
    forecast_points: List[Tuple[datetime, float]]
    confidence_interval: Tuple[float, float]


class PatternAnalyzer:
    """
    Advanced pattern analysis system for agent prompt improvement
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.min_pattern_frequency = self.config.get('min_pattern_frequency', 3)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.trend_window_days = self.config.get('trend_window_days', 14)
        self.forecast_days = self.config.get('forecast_days', 7)
        
        # Storage
        self.base_path = Path(self.config.get('base_path', '.claude-pm/pattern_analysis'))
        self.patterns_path = self.base_path / 'patterns'
        self.clusters_path = self.base_path / 'clusters'
        self.trends_path = self.base_path / 'trends'
        
        # Create directories
        for path in [self.patterns_path, self.clusters_path, self.trends_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ML components if available
        self.vectorizer = None
        self.clusterer = None
        if HAS_ML:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.clusterer = KMeans(n_clusters=5, random_state=42)
        
        self.logger.info("PatternAnalyzer initialized successfully")
    
    async def analyze_correction_patterns(self, 
                                        corrections: List[Any],
                                        agent_type: Optional[str] = None) -> List[PatternMetrics]:
        """
        Analyze correction data for patterns
        
        Args:
            corrections: List of correction records
            agent_type: Filter by agent type
            
        Returns:
            List of detected patterns with metrics
        """
        try:
            if agent_type:
                corrections = [c for c in corrections if c.agent_type == agent_type]
            
            # Extract basic patterns
            basic_patterns = await self._extract_basic_patterns(corrections)
            
            # Perform advanced analysis
            pattern_metrics = []
            
            for pattern_key, pattern_data in basic_patterns.items():
                # Calculate comprehensive metrics
                metrics = await self._calculate_pattern_metrics(pattern_data, corrections)
                pattern_metrics.append(metrics)
            
            # Filter by significance
            significant_patterns = [
                p for p in pattern_metrics 
                if p.frequency >= self.min_pattern_frequency and p.confidence > 0.5
            ]
            
            # Perform clustering analysis
            clusters = await self._cluster_patterns(significant_patterns, corrections)
            
            # Analyze trends
            trends = await self._analyze_pattern_trends(significant_patterns, corrections)
            
            # Save analysis results
            await self._save_analysis_results(significant_patterns, clusters, trends)
            
            self.logger.info(f"Analyzed {len(corrections)} corrections, found {len(significant_patterns)} significant patterns")
            return significant_patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing correction patterns: {e}")
            return []
    
    async def _extract_basic_patterns(self, corrections: List[Any]) -> Dict[str, Any]:
        """Extract basic patterns from corrections"""
        patterns = defaultdict(lambda: {
            'frequencies': [],
            'timestamps': [],
            'error_types': [],
            'contexts': [],
            'agent_types': [],
            'corrections': [],
            'severities': []
        })
        
        for correction in corrections:
            # Create pattern key
            pattern_key = f"{correction.agent_type}_{correction.error_type}"
            
            # Aggregate pattern data
            pattern_data = patterns[pattern_key]
            pattern_data['frequencies'].append(1)
            pattern_data['timestamps'].append(correction.timestamp)
            pattern_data['error_types'].append(correction.error_type)
            pattern_data['contexts'].append(getattr(correction, 'context', ''))
            pattern_data['agent_types'].append(correction.agent_type)
            pattern_data['corrections'].append(correction.correction_applied)
            pattern_data['severities'].append(getattr(correction, 'severity', 'medium'))
        
        return dict(patterns)
    
    async def _calculate_pattern_metrics(self, 
                                       pattern_data: Dict[str, Any],
                                       all_corrections: List[Any]) -> PatternMetrics:
        """Calculate comprehensive metrics for a pattern"""
        try:
            # Basic metrics
            frequency = len(pattern_data['timestamps'])
            total_corrections = len(all_corrections)
            
            # Severity score (weighted by frequency and severity levels)
            severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            severity_scores = [severity_weights.get(s, 2) for s in pattern_data['severities']]
            severity_score = statistics.mean(severity_scores) if severity_scores else 2.0
            
            # Trend analysis
            trend_direction = self._calculate_trend_direction(pattern_data['timestamps'])
            
            # Confidence based on frequency and consistency
            confidence = min(0.95, (frequency / total_corrections) * 2 + 0.1)
            
            # Impact score (frequency * severity * trend factor)
            trend_factor = {'increasing': 1.5, 'stable': 1.0, 'decreasing': 0.7}[trend_direction]
            impact_score = (frequency / total_corrections) * severity_score * trend_factor
            
            # Prediction accuracy (based on trend consistency)
            prediction_accuracy = self._calculate_prediction_accuracy(pattern_data['timestamps'])
            
            # Correlation strength (temporal correlation)
            correlation_strength = self._calculate_correlation_strength(pattern_data['timestamps'])
            
            # Generate pattern ID
            pattern_id = f"pattern_{hash(str(pattern_data))}"[:12]
            
            return PatternMetrics(
                pattern_id=pattern_id,
                frequency=frequency,
                severity_score=severity_score,
                trend_direction=trend_direction,
                confidence=confidence,
                impact_score=impact_score,
                prediction_accuracy=prediction_accuracy,
                correlation_strength=correlation_strength
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern metrics: {e}")
            return PatternMetrics(
                pattern_id="error",
                frequency=0,
                severity_score=0.0,
                trend_direction="stable",
                confidence=0.0,
                impact_score=0.0,
                prediction_accuracy=0.0,
                correlation_strength=0.0
            )
    
    def _calculate_trend_direction(self, timestamps: List[datetime]) -> str:
        """Calculate trend direction from timestamps"""
        if len(timestamps) < 2:
            return "stable"
        
        # Sort timestamps
        sorted_times = sorted(timestamps)
        
        # Split into two halves and compare frequencies
        mid_point = len(sorted_times) // 2
        first_half = sorted_times[:mid_point]
        second_half = sorted_times[mid_point:]
        
        # Calculate time windows
        total_duration = (sorted_times[-1] - sorted_times[0]).total_seconds()
        if total_duration == 0:
            return "stable"
        
        first_half_rate = len(first_half) / (total_duration / 2)
        second_half_rate = len(second_half) / (total_duration / 2)
        
        # Determine trend
        if second_half_rate > first_half_rate * 1.2:
            return "increasing"
        elif second_half_rate < first_half_rate * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_prediction_accuracy(self, timestamps: List[datetime]) -> float:
        """Calculate prediction accuracy based on temporal regularity"""
        if len(timestamps) < 3:
            return 0.5
        
        # Calculate intervals between timestamps
        sorted_times = sorted(timestamps)
        intervals = []
        
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return 0.5
        
        # Calculate coefficient of variation (lower = more predictable)
        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return 0.5
        
        std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        cv = std_interval / mean_interval
        
        # Convert to accuracy (0-1 scale)
        return max(0.0, min(1.0, 1.0 - cv))
    
    def _calculate_correlation_strength(self, timestamps: List[datetime]) -> float:
        """Calculate temporal correlation strength"""
        if len(timestamps) < 2:
            return 0.0
        
        # Create time series data
        sorted_times = sorted(timestamps)
        base_time = sorted_times[0]
        
        # Convert to hours since base time
        time_points = [(t - base_time).total_seconds() / 3600 for t in sorted_times]
        
        # Calculate autocorrelation at lag 1
        if len(time_points) < 2:
            return 0.0
        
        # Simple correlation based on spacing consistency
        intervals = [time_points[i+1] - time_points[i] for i in range(len(time_points)-1)]
        
        if len(intervals) < 2:
            return 0.5
        
        # Calculate correlation as inverse of variance
        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return 0.0
        
        variance = statistics.variance(intervals)
        correlation = 1.0 / (1.0 + variance / (mean_interval ** 2))
        
        return min(1.0, correlation)
    
    async def _cluster_patterns(self, 
                              patterns: List[PatternMetrics],
                              corrections: List[Any]) -> List[PatternCluster]:
        """Cluster similar patterns together"""
        try:
            if not HAS_ML or len(patterns) < 2:
                return []
            
            # Extract text features for clustering
            pattern_texts = []
            pattern_mapping = {}
            
            for pattern in patterns:
                # Get pattern descriptions from corrections
                pattern_corrections = [
                    c for c in corrections 
                    if f"pattern_{hash(str(c.agent_type + '_' + c.error_type))}"[:12] == pattern.pattern_id
                ]
                
                if pattern_corrections:
                    # Combine correction descriptions
                    text = " ".join([
                        c.issue_description + " " + c.correction_applied 
                        for c in pattern_corrections
                    ])
                    pattern_texts.append(text)
                    pattern_mapping[len(pattern_texts) - 1] = pattern.pattern_id
            
            if len(pattern_texts) < 2:
                return []
            
            # Vectorize text
            try:
                vectors = self.vectorizer.fit_transform(pattern_texts)
                
                # Cluster patterns
                n_clusters = min(5, len(pattern_texts))
                self.clusterer.n_clusters = n_clusters
                cluster_labels = self.clusterer.fit_predict(vectors)
                
                # Create cluster objects
                clusters = []
                for cluster_id in range(n_clusters):
                    cluster_patterns = [
                        pattern_mapping[i] for i, label in enumerate(cluster_labels) 
                        if label == cluster_id
                    ]
                    
                    if cluster_patterns:
                        # Calculate cluster metrics
                        cluster_texts = [pattern_texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                        centroid_description = self._generate_cluster_description(cluster_texts)
                        
                        # Calculate similarity score
                        cluster_vectors = vectors[cluster_labels == cluster_id]
                        similarity_score = self._calculate_cluster_similarity(cluster_vectors)
                        
                        # Find dominant agent type
                        dominant_agent_type = self._find_dominant_agent_type(cluster_patterns, corrections)
                        
                        cluster = PatternCluster(
                            cluster_id=f"cluster_{cluster_id}",
                            patterns=cluster_patterns,
                            centroid_description=centroid_description,
                            similarity_score=similarity_score,
                            cluster_size=len(cluster_patterns),
                            dominant_agent_type=dominant_agent_type
                        )
                        clusters.append(cluster)
                
                return clusters
                
            except Exception as e:
                self.logger.error(f"Error in ML clustering: {e}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error clustering patterns: {e}")
            return []
    
    def _generate_cluster_description(self, cluster_texts: List[str]) -> str:
        """Generate description for cluster centroid"""
        if not cluster_texts:
            return "Empty cluster"
        
        # Simple approach: find most common words
        all_words = []
        for text in cluster_texts:
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.extend(words)
        
        # Get most frequent words
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(5)]
        
        return f"Common themes: {', '.join(common_words)}"
    
    def _calculate_cluster_similarity(self, vectors) -> float:
        """Calculate intra-cluster similarity"""
        try:
            if vectors.shape[0] < 2:
                return 1.0
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(vectors)
            
            # Get upper triangle (exclude diagonal)
            upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
            
            return float(np.mean(upper_triangle))
            
        except Exception as e:
            self.logger.error(f"Error calculating cluster similarity: {e}")
            return 0.0
    
    def _find_dominant_agent_type(self, pattern_ids: List[str], corrections: List[Any]) -> str:
        """Find dominant agent type in cluster"""
        agent_counts = Counter()
        
        for pattern_id in pattern_ids:
            # Find corrections for this pattern
            pattern_corrections = [
                c for c in corrections 
                if f"pattern_{hash(str(c.agent_type + '_' + c.error_type))}"[:12] == pattern_id
            ]
            
            for correction in pattern_corrections:
                agent_counts[correction.agent_type] += 1
        
        if agent_counts:
            return agent_counts.most_common(1)[0][0]
        
        return "unknown"
    
    async def _analyze_pattern_trends(self, 
                                    patterns: List[PatternMetrics],
                                    corrections: List[Any]) -> List[PatternTrend]:
        """Analyze trends in patterns"""
        trends = []
        
        for pattern in patterns:
            try:
                # Get pattern corrections
                pattern_corrections = [
                    c for c in corrections 
                    if f"pattern_{hash(str(c.agent_type + '_' + c.error_type))}"[:12] == pattern.pattern_id
                ]
                
                if len(pattern_corrections) < 3:
                    continue
                
                # Create time series
                timestamps = [c.timestamp for c in pattern_corrections]
                trend = await self._calculate_trend_analysis(pattern.pattern_id, timestamps)
                
                if trend:
                    trends.append(trend)
                    
            except Exception as e:
                self.logger.error(f"Error analyzing trend for pattern {pattern.pattern_id}: {e}")
                continue
        
        return trends
    
    async def _calculate_trend_analysis(self, 
                                      pattern_id: str,
                                      timestamps: List[datetime]) -> Optional[PatternTrend]:
        """Calculate detailed trend analysis for pattern"""
        try:
            if len(timestamps) < 3:
                return None
            
            # Sort timestamps
            sorted_times = sorted(timestamps)
            
            # Create time series (count per day)
            date_counts = Counter()
            for timestamp in sorted_times:
                date_key = timestamp.date()
                date_counts[date_key] += 1
            
            # Convert to arrays for regression
            dates = sorted(date_counts.keys())
            counts = [date_counts[date] for date in dates]
            
            if len(dates) < 2:
                return None
            
            # Simple linear regression
            x = list(range(len(dates)))
            y = counts
            
            # Calculate slope and R-squared
            slope, r_squared = self._linear_regression(x, y)
            
            # Generate forecast
            forecast_points = []
            base_date = dates[-1]
            
            for i in range(1, self.forecast_days + 1):
                forecast_date = base_date + timedelta(days=i)
                forecast_value = max(0, y[-1] + slope * i)
                forecast_points.append((forecast_date, forecast_value))
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(y, slope, r_squared)
            
            # Determine trend type
            if slope > 0.1:
                trend_type = "increasing"
            elif slope < -0.1:
                trend_type = "decreasing"
            else:
                trend_type = "stable"
            
            return PatternTrend(
                pattern_id=pattern_id,
                trend_type=trend_type,
                slope=slope,
                r_squared=r_squared,
                forecast_points=forecast_points,
                confidence_interval=confidence_interval
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating trend analysis: {e}")
            return None
    
    def _linear_regression(self, x: List[int], y: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and R-squared"""
        n = len(x)
        if n < 2:
            return 0.0, 0.0
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((y[i] - (y_mean + slope * (x[i] - x_mean))) ** 2 for i in range(n))
        
        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        return slope, max(0.0, r_squared)
    
    def _calculate_confidence_interval(self, 
                                     y: List[float], 
                                     slope: float,
                                     r_squared: float) -> Tuple[float, float]:
        """Calculate confidence interval for trend"""
        if len(y) < 2:
            return (0.0, 0.0)
        
        # Simple confidence interval based on standard error
        std_error = statistics.stdev(y) * math.sqrt(1 - r_squared)
        
        # 95% confidence interval
        confidence = 1.96 * std_error
        
        return (-confidence, confidence)
    
    async def detect_anomalies(self, 
                             patterns: List[PatternMetrics],
                             threshold: float = 2.0) -> List[PatternMetrics]:
        """
        Detect anomalous patterns using statistical methods
        
        Args:
            patterns: List of patterns to analyze
            threshold: Standard deviation threshold for anomaly detection
            
        Returns:
            List of anomalous patterns
        """
        try:
            if len(patterns) < 3:
                return []
            
            # Extract metrics for anomaly detection
            frequencies = [p.frequency for p in patterns]
            severities = [p.severity_score for p in patterns]
            impacts = [p.impact_score for p in patterns]
            
            # Calculate Z-scores
            anomalies = []
            
            for i, pattern in enumerate(patterns):
                # Frequency anomaly
                freq_zscore = self._calculate_zscore(frequencies[i], frequencies)
                
                # Severity anomaly
                sev_zscore = self._calculate_zscore(severities[i], severities)
                
                # Impact anomaly
                impact_zscore = self._calculate_zscore(impacts[i], impacts)
                
                # Check if any metric exceeds threshold
                if (abs(freq_zscore) > threshold or 
                    abs(sev_zscore) > threshold or 
                    abs(impact_zscore) > threshold):
                    anomalies.append(pattern)
            
            self.logger.info(f"Detected {len(anomalies)} anomalous patterns")
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _calculate_zscore(self, value: float, values: List[float]) -> float:
        """Calculate Z-score for anomaly detection"""
        if len(values) < 2:
            return 0.0
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        if std_val == 0:
            return 0.0
        
        return (value - mean_val) / std_val
    
    async def generate_improvement_priorities(self, 
                                            patterns: List[PatternMetrics],
                                            clusters: List[PatternCluster],
                                            trends: List[PatternTrend]) -> List[Dict[str, Any]]:
        """
        Generate prioritized improvement recommendations
        
        Args:
            patterns: Detected patterns
            clusters: Pattern clusters
            trends: Pattern trends
            
        Returns:
            List of prioritized improvement recommendations
        """
        try:
            priorities = []
            
            # Create priority score for each pattern
            for pattern in patterns:
                priority_score = self._calculate_priority_score(pattern, clusters, trends)
                
                # Find related cluster
                related_cluster = None
                for cluster in clusters:
                    if pattern.pattern_id in cluster.patterns:
                        related_cluster = cluster
                        break
                
                # Find related trend
                related_trend = None
                for trend in trends:
                    if trend.pattern_id == pattern.pattern_id:
                        related_trend = trend
                        break
                
                priority = {
                    'pattern_id': pattern.pattern_id,
                    'priority_score': priority_score,
                    'frequency': pattern.frequency,
                    'severity_score': pattern.severity_score,
                    'impact_score': pattern.impact_score,
                    'trend_direction': pattern.trend_direction,
                    'confidence': pattern.confidence,
                    'cluster_id': related_cluster.cluster_id if related_cluster else None,
                    'cluster_size': related_cluster.cluster_size if related_cluster else 1,
                    'trend_slope': related_trend.slope if related_trend else 0.0,
                    'improvement_urgency': self._calculate_urgency(pattern, related_trend),
                    'recommended_action': self._generate_action_recommendation(pattern, related_cluster, related_trend)
                }
                
                priorities.append(priority)
            
            # Sort by priority score
            priorities.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return priorities
            
        except Exception as e:
            self.logger.error(f"Error generating improvement priorities: {e}")
            return []
    
    def _calculate_priority_score(self, 
                                pattern: PatternMetrics,
                                clusters: List[PatternCluster],
                                trends: List[PatternTrend]) -> float:
        """Calculate priority score for pattern"""
        try:
            # Base score from pattern metrics
            base_score = (
                pattern.frequency * 0.2 +
                pattern.severity_score * 0.3 +
                pattern.impact_score * 0.3 +
                pattern.confidence * 0.2
            )
            
            # Trend multiplier
            trend_multiplier = 1.0
            for trend in trends:
                if trend.pattern_id == pattern.pattern_id:
                    if trend.trend_type == "increasing":
                        trend_multiplier = 1.5
                    elif trend.trend_type == "decreasing":
                        trend_multiplier = 0.8
                    break
            
            # Cluster multiplier (larger clusters get higher priority)
            cluster_multiplier = 1.0
            for cluster in clusters:
                if pattern.pattern_id in cluster.patterns:
                    cluster_multiplier = 1.0 + (cluster.cluster_size - 1) * 0.1
                    break
            
            return base_score * trend_multiplier * cluster_multiplier
            
        except Exception as e:
            self.logger.error(f"Error calculating priority score: {e}")
            return 0.0
    
    def _calculate_urgency(self, 
                          pattern: PatternMetrics,
                          trend: Optional[PatternTrend]) -> str:
        """Calculate urgency level for pattern"""
        if pattern.severity_score >= 3.0 and pattern.impact_score >= 0.5:
            return "critical"
        elif trend and trend.trend_type == "increasing" and pattern.confidence > 0.7:
            return "high"
        elif pattern.frequency > 10 or pattern.impact_score > 0.3:
            return "medium"
        else:
            return "low"
    
    def _generate_action_recommendation(self, 
                                      pattern: PatternMetrics,
                                      cluster: Optional[PatternCluster],
                                      trend: Optional[PatternTrend]) -> str:
        """Generate action recommendation for pattern"""
        if cluster and cluster.cluster_size > 3:
            return f"Address cluster-wide issue affecting {cluster.cluster_size} patterns"
        elif trend and trend.trend_type == "increasing":
            return "Immediate intervention needed - trend is increasing"
        elif pattern.severity_score >= 3.0:
            return "High-priority fix required"
        elif pattern.frequency > 10:
            return "Frequent issue - implement systematic solution"
        else:
            return "Monitor and improve incrementally"
    
    # Storage methods
    async def _save_analysis_results(self, 
                                   patterns: List[PatternMetrics],
                                   clusters: List[PatternCluster],
                                   trends: List[PatternTrend]):
        """Save analysis results to storage"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save patterns
            patterns_file = self.patterns_path / f"patterns_{timestamp}.json"
            with open(patterns_file, 'w') as f:
                json.dump([asdict(p) for p in patterns], f, indent=2)
            
            # Save clusters
            clusters_file = self.clusters_path / f"clusters_{timestamp}.json"
            with open(clusters_file, 'w') as f:
                json.dump([asdict(c) for c in clusters], f, indent=2)
            
            # Save trends
            trends_file = self.trends_path / f"trends_{timestamp}.json"
            with open(trends_file, 'w') as f:
                trends_data = []
                for trend in trends:
                    trend_dict = asdict(trend)
                    # Convert datetime objects to ISO format
                    trend_dict['forecast_points'] = [
                        (fp[0].isoformat(), fp[1]) for fp in trend.forecast_points
                    ]
                    trends_data.append(trend_dict)
                json.dump(trends_data, f, indent=2)
            
            self.logger.info(f"Saved analysis results with timestamp {timestamp}")
            
        except Exception as e:
            self.logger.error(f"Error saving analysis results: {e}")
    
    async def load_recent_analysis(self, days_back: int = 7) -> Dict[str, Any]:
        """Load recent analysis results"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Load patterns
            patterns = []
            for pattern_file in self.patterns_path.glob("patterns_*.json"):
                file_timestamp = datetime.strptime(
                    pattern_file.stem.split('_')[1], "%Y%m%d"
                )
                if file_timestamp >= cutoff_date:
                    with open(pattern_file, 'r') as f:
                        patterns.extend(json.load(f))
            
            # Load clusters
            clusters = []
            for cluster_file in self.clusters_path.glob("clusters_*.json"):
                file_timestamp = datetime.strptime(
                    cluster_file.stem.split('_')[1], "%Y%m%d"
                )
                if file_timestamp >= cutoff_date:
                    with open(cluster_file, 'r') as f:
                        clusters.extend(json.load(f))
            
            # Load trends
            trends = []
            for trend_file in self.trends_path.glob("trends_*.json"):
                file_timestamp = datetime.strptime(
                    trend_file.stem.split('_')[1], "%Y%m%d"
                )
                if file_timestamp >= cutoff_date:
                    with open(trend_file, 'r') as f:
                        trends.extend(json.load(f))
            
            return {
                'patterns': patterns,
                'clusters': clusters,
                'trends': trends,
                'analysis_period': f"Last {days_back} days",
                'loaded_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading recent analysis: {e}")
            return {'error': str(e)}


# Async convenience functions
async def run_comprehensive_analysis(corrections: List[Any], 
                                   agent_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Run comprehensive pattern analysis
    
    Args:
        corrections: List of correction records
        agent_type: Optional agent type filter
        
    Returns:
        Comprehensive analysis results
    """
    analyzer = PatternAnalyzer()
    
    # Analyze patterns
    patterns = await analyzer.analyze_correction_patterns(corrections, agent_type)
    
    # Detect anomalies
    anomalies = await analyzer.detect_anomalies(patterns)
    
    # Load recent analysis for comparison
    recent_analysis = await analyzer.load_recent_analysis()
    
    return {
        'analysis_timestamp': datetime.now().isoformat(),
        'patterns_detected': len(patterns),
        'anomalies_detected': len(anomalies),
        'patterns': [asdict(p) for p in patterns],
        'anomalies': [asdict(a) for a in anomalies],
        'recent_analysis': recent_analysis,
        'has_ml_support': HAS_ML
    }


if __name__ == "__main__":
    # Example usage
    async def main():
        # Mock correction data for testing
        mock_corrections = []
        
        # Initialize analyzer
        analyzer = PatternAnalyzer()
        
        # Run analysis
        patterns = await analyzer.analyze_correction_patterns(mock_corrections)
        print(f"Found {len(patterns)} patterns")
        
        # Detect anomalies
        anomalies = await analyzer.detect_anomalies(patterns)
        print(f"Detected {len(anomalies)} anomalies")
    
    asyncio.run(main())