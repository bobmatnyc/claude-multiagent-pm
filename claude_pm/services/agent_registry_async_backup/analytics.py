"""Analytics and statistics for agent registry."""

import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .models import AgentMetadata
from .classification import AgentClassifier

logger = logging.getLogger(__name__)


class AgentAnalytics:
    """Provides analytics and statistics for agent registry."""
    
    def __init__(self, classifier: AgentClassifier):
        """Initialize analytics with classifier."""
        self.classifier = classifier
    
    async def get_registry_stats(
        self, 
        registry: Dict[str, AgentMetadata],
        discovery_paths: List[Path],
        last_discovery_time: Optional[float]
    ) -> Dict[str, Any]:
        """
        Get registry statistics and metrics.
        
        Args:
            registry: Agent registry
            discovery_paths: Agent discovery paths
            last_discovery_time: Last discovery timestamp
            
        Returns:
            Dictionary of registry statistics
        """
        stats = {
            'total_agents': len(registry),
            'validated_agents': len([a for a in registry.values() if a.validated]),
            'failed_agents': len([a for a in registry.values() if not a.validated]),
            'agent_types': len({metadata.type for metadata in registry.values()}),
            'agents_by_tier': {},
            'agents_by_type': {},
            'last_discovery': last_discovery_time,
            'discovery_paths': [str(p) for p in discovery_paths]
        }
        
        # Count by tier
        for metadata in registry.values():
            tier = metadata.tier
            stats['agents_by_tier'][tier] = stats['agents_by_tier'].get(tier, 0) + 1
        
        # Count by type
        for metadata in registry.values():
            agent_type = metadata.type
            stats['agents_by_type'][agent_type] = stats['agents_by_type'].get(agent_type, 0) + 1
        
        return stats
    
    async def get_enhanced_registry_stats(
        self,
        registry: Dict[str, AgentMetadata],
        discovery_paths: List[Path],
        last_discovery_time: Optional[float]
    ) -> Dict[str, Any]:
        """
        Get enhanced registry statistics including specialized agent metrics.
        
        Returns:
            Dictionary of enhanced registry statistics
        """
        base_stats = await self.get_registry_stats(registry, discovery_paths, last_discovery_time)
        
        # Enhanced statistics for specialized agents
        enhanced_stats = base_stats.copy()
        
        # Specialization statistics
        specialization_counts = {}
        framework_counts = {}
        domain_counts = {}
        role_counts = {}
        complexity_counts = {}
        hybrid_count = 0
        
        validation_scores = []
        
        for metadata in registry.values():
            # Count specializations
            for spec in metadata.specializations:
                specialization_counts[spec] = specialization_counts.get(spec, 0) + 1
            
            # Count frameworks
            for fw in metadata.frameworks:
                framework_counts[fw] = framework_counts.get(fw, 0) + 1
            
            # Count domains
            for domain in metadata.domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            # Count roles
            for role in metadata.roles:
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Count complexity levels
            complexity_counts[metadata.complexity_level] = complexity_counts.get(metadata.complexity_level, 0) + 1
            
            # Count hybrid agents
            if metadata.is_hybrid:
                hybrid_count += 1
            
            # Collect validation scores
            validation_scores.append(metadata.validation_score)
        
        enhanced_stats.update({
            'specialization_counts': specialization_counts,
            'framework_counts': framework_counts,
            'domain_counts': domain_counts,
            'role_counts': role_counts,
            'complexity_distribution': complexity_counts,
            'hybrid_agents': hybrid_count,
            'validation_metrics': {
                'average_score': sum(validation_scores) / len(validation_scores) if validation_scores else 0,
                'max_score': max(validation_scores) if validation_scores else 0,
                'min_score': min(validation_scores) if validation_scores else 0,
                'scores_above_threshold': len([s for s in validation_scores if s >= 50.0])
            },
            'discovery_beyond_core_9': {
                'total_specialized_types': len(self.classifier.specialized_agent_types),
                'discovered_specialized': len([a for a in registry.values() 
                                             if a.type in self.classifier.specialized_agent_types]),
                'custom_agents': len([a for a in registry.values() if a.type == 'custom'])
            }
        })
        
        return enhanced_stats
    
    async def get_model_usage_statistics(self, registry: Dict[str, AgentMetadata]) -> Dict[str, Any]:
        """
        Get statistics on model usage across all agents.
        
        Args:
            registry: Agent registry
            
        Returns:
            Dictionary with model usage statistics
        """
        stats = {
            "model_distribution": {},
            "agent_type_model_mapping": {},
            "complexity_level_distribution": {},
            "auto_selected_count": 0,
            "manually_configured_count": 0,
            "total_agents": len(registry)
        }
        
        for metadata in registry.values():
            # Count model distribution
            if metadata.preferred_model:
                stats["model_distribution"][metadata.preferred_model] = \
                    stats["model_distribution"].get(metadata.preferred_model, 0) + 1
            
            # Agent type to model mapping
            agent_type = metadata.type
            if agent_type not in stats["agent_type_model_mapping"]:
                stats["agent_type_model_mapping"][agent_type] = {}
            
            model = metadata.preferred_model or "none"
            stats["agent_type_model_mapping"][agent_type][model] = \
                stats["agent_type_model_mapping"][agent_type].get(model, 0) + 1
            
            # Complexity level distribution
            complexity = metadata.complexity_level
            if complexity not in stats["complexity_level_distribution"]:
                stats["complexity_level_distribution"][complexity] = {}
            
            stats["complexity_level_distribution"][complexity][model] = \
                stats["complexity_level_distribution"][complexity].get(model, 0) + 1
            
            # Auto vs manual selection
            if metadata.model_config.get("auto_selected"):
                stats["auto_selected_count"] += 1
            elif metadata.model_config.get("explicit") or metadata.model_config.get("manually_updated"):
                stats["manually_configured_count"] += 1
        
        return stats
    
    async def generate_performance_report(self, registry: Dict[str, AgentMetadata]) -> Dict[str, Any]:
        """
        Generate a performance report for the agent registry.
        
        Args:
            registry: Agent registry
            
        Returns:
            Performance report dictionary
        """
        report = {
            "timestamp": time.time(),
            "total_agents": len(registry),
            "performance_metrics": {},
            "optimization_opportunities": [],
            "health_indicators": {}
        }
        
        # Calculate average file sizes
        file_sizes = [m.file_size for m in registry.values() if m.file_size]
        if file_sizes:
            report["performance_metrics"]["average_file_size"] = sum(file_sizes) / len(file_sizes)
            report["performance_metrics"]["max_file_size"] = max(file_sizes)
            report["performance_metrics"]["min_file_size"] = min(file_sizes)
        
        # Validation performance
        validation_times = []
        for metadata in registry.values():
            if metadata.last_modified:
                validation_times.append(time.time() - metadata.last_modified)
        
        if validation_times:
            report["performance_metrics"]["average_age_seconds"] = sum(validation_times) / len(validation_times)
        
        # Health indicators
        validated_count = len([m for m in registry.values() if m.validated])
        report["health_indicators"]["validation_rate"] = validated_count / len(registry) if registry else 0
        
        # Complexity distribution health
        complexity_dist = {}
        for metadata in registry.values():
            complexity_dist[metadata.complexity_level] = complexity_dist.get(metadata.complexity_level, 0) + 1
        
        report["health_indicators"]["complexity_distribution"] = complexity_dist
        
        # Optimization opportunities
        if report["health_indicators"]["validation_rate"] < 0.8:
            report["optimization_opportunities"].append(
                "Low validation rate detected. Consider reviewing agent configurations."
            )
        
        large_files = [m for m in registry.values() if m.file_size and m.file_size > 50000]
        if large_files:
            report["optimization_opportunities"].append(
                f"Found {len(large_files)} large agent files (>50KB). Consider refactoring."
            )
        
        return report
    
    async def analyze_agent_coverage(self, registry: Dict[str, AgentMetadata]) -> Dict[str, Any]:
        """
        Analyze agent type coverage and gaps.
        
        Args:
            registry: Agent registry
            
        Returns:
            Coverage analysis dictionary
        """
        coverage = {
            "core_agent_coverage": {},
            "specialized_agent_coverage": {},
            "coverage_gaps": [],
            "coverage_percentage": 0.0
        }
        
        # Analyze core agent coverage
        discovered_types = {m.type for m in registry.values()}
        
        for core_type in self.classifier.core_agent_types:
            coverage["core_agent_coverage"][core_type] = core_type in discovered_types
        
        # Calculate core coverage percentage
        covered_core = sum(1 for v in coverage["core_agent_coverage"].values() if v)
        coverage["core_coverage_percentage"] = (covered_core / len(self.classifier.core_agent_types)) * 100
        
        # Analyze specialized agent coverage
        for spec_type in self.classifier.specialized_agent_types:
            coverage["specialized_agent_coverage"][spec_type] = spec_type in discovered_types
        
        # Identify gaps
        missing_core = [t for t in self.classifier.core_agent_types if t not in discovered_types]
        if missing_core:
            coverage["coverage_gaps"].append({
                "type": "core_agents",
                "missing": missing_core,
                "severity": "high"
            })
        
        # Calculate overall coverage
        total_types = len(self.classifier.core_agent_types) + len(self.classifier.specialized_agent_types)
        covered_types = len(discovered_types.intersection(
            self.classifier.core_agent_types.union(self.classifier.specialized_agent_types)
        ))
        coverage["coverage_percentage"] = (covered_types / total_types) * 100 if total_types > 0 else 0
        
        return coverage