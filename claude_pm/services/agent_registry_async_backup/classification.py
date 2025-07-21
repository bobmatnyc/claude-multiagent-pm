"""Agent type classification functionality."""

import logging
from pathlib import Path
from typing import List, Tuple, Set

logger = logging.getLogger(__name__)


class AgentClassifier:
    """Handles agent type classification and complexity assessment."""
    
    def __init__(self):
        """Initialize agent classifier with type definitions."""
        self.core_agent_types = {
            'documentation', 'ticketing', 'version_control', 'qa', 'research',
            'ops', 'security', 'engineer', 'data_engineer'
        }
        
        # Extended specialized agent types for ISS-0118
        self.specialized_agent_types = {
            'ui_ux', 'database', 'api', 'testing', 'performance', 'monitoring',
            'analytics', 'deployment', 'integration', 'workflow', 'content',
            'machine_learning', 'data_science', 'frontend', 'backend', 'mobile',
            'devops', 'cloud', 'infrastructure', 'compliance', 'audit',
            'project_management', 'business_analysis', 'customer_support',
            'marketing', 'sales', 'finance', 'legal', 'hr', 'training',
            'documentation_specialist', 'code_review', 'architecture',
            'orchestrator', 'scaffolding', 'memory_management', 'knowledge_base'
        }
    
    def classify_agent_type(self, agent_name: str, agent_file: Path) -> str:
        """
        Enhanced agent type classification supporting specialized agents beyond core 9 types.
        
        Args:
            agent_name: Agent name
            agent_file: Agent file path
            
        Returns:
            Agent type classification
        """
        name_lower = agent_name.lower()
        
        # First check for core agent types (highest priority)
        for core_type in self.core_agent_types:
            if core_type in name_lower or name_lower in core_type:
                return core_type
        
        # Enhanced pattern-based classification for specialized agents
        classification_patterns = {
            # UI/UX and Frontend specializations
            'ui_ux': ['ui', 'ux', 'design', 'interface', 'user_experience', 'frontend_design'],
            'frontend': ['frontend', 'front_end', 'react', 'vue', 'angular', 'web_ui', 'client_side'],
            
            # Backend and Infrastructure specializations
            'backend': ['backend', 'back_end', 'server', 'api_server', 'microservice'],
            'database': ['database', 'db', 'sql', 'nosql', 'mysql', 'postgres', 'mongodb', 'redis'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'service', 'web_service'],
            
            # Testing and Quality specializations
            'testing': ['test', 'testing', 'unit_test', 'integration_test', 'e2e', 'automation'],
            'performance': ['performance', 'benchmark', 'optimization', 'profiling', 'load_test'],
            'monitoring': ['monitoring', 'observability', 'metrics', 'logging', 'alerting'],
            
            # DevOps and Infrastructure specializations
            'devops': ['devops', 'ci_cd', 'pipeline', 'automation', 'build'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'container'],
            'infrastructure': ['infrastructure', 'terraform', 'ansible', 'provisioning'],
            'deployment': ['deployment', 'deploy', 'release', 'staging', 'production'],
            
            # Data and Analytics specializations
            'analytics': ['analytics', 'metrics', 'reporting', 'business_intelligence', 'dashboard'],
            'machine_learning': ['ml', 'machine_learning', 'ai', 'model', 'training', 'prediction'],
            'data_science': ['data_science', 'data_scientist', 'analysis', 'statistics', 'modeling'],
            
            # Business and Process specializations
            'project_management': ['pm', 'project_management', 'scrum', 'agile', 'planning'],
            'business_analysis': ['business_analyst', 'requirements', 'specification', 'process'],
            'compliance': ['compliance', 'audit', 'governance', 'policy', 'regulatory'],
            
            # Content and Communication specializations
            'content': ['content', 'copywriting', 'documentation', 'technical_writing'],
            'customer_support': ['support', 'helpdesk', 'customer_service', 'ticketing'],
            'marketing': ['marketing', 'campaign', 'promotion', 'seo', 'social_media'],
            
            # Framework-specific specializations
            'orchestrator': ['orchestrator', 'coordinator', 'workflow', 'pipeline'],
            'scaffolding': ['scaffolding', 'template', 'generator', 'boilerplate'],
            'architecture': ['architect', 'architecture', 'design_pattern', 'system_design'],
            'code_review': ['code_review', 'review', 'quality_assurance', 'peer_review'],
            'memory_management': ['memory', 'cache', 'storage', 'persistence'],
            'knowledge_base': ['knowledge', 'kb', 'documentation', 'wiki', 'reference'],
            
            # Integration and Workflow specializations
            'integration': ['integration', 'connector', 'bridge', 'adapter', 'sync'],
            'workflow': ['workflow', 'process', 'automation', 'orchestration']
        }
        
        # Check specialized agent patterns
        for agent_type, patterns in classification_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return agent_type
        
        # Enhanced core agent type pattern matching (fallback)
        core_patterns = {
            'documentation': ['doc', 'docs', 'manual', 'guide', 'readme'],
            'ticketing': ['ticket', 'issue', 'bug', 'task', 'jira'],
            'version_control': ['version', 'git', 'vcs', 'commit', 'branch', 'merge'],
            'qa': ['qa', 'quality', 'assurance', 'validation', 'verification'],
            'research': ['research', 'analyze', 'investigate', 'study', 'explore'],
            'ops': ['ops', 'operations', 'maintenance', 'administration'],
            'security': ['security', 'auth', 'permission', 'vulnerability', 'encryption'],
            'engineer': ['engineer', 'code', 'develop', 'programming', 'implementation'],
            'data_engineer': ['data_engineer', 'etl', 'pipeline', 'warehouse']
        }
        
        for core_type, patterns in core_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return core_type
        
        # Path-based classification hints
        path_str = str(agent_file).lower()
        if 'frontend' in path_str or 'ui' in path_str:
            return 'frontend'
        elif 'backend' in path_str or 'api' in path_str:
            return 'backend'
        elif 'database' in path_str or 'db' in path_str:
            return 'database'
        elif 'test' in path_str:
            return 'testing'
        elif 'deploy' in path_str:
            return 'deployment'
        
        return 'custom'
    
    def detect_hybrid_agent(self, agent_type: str, specializations: List[str]) -> Tuple[bool, List[str]]:
        """
        Detect if agent is hybrid (combines multiple agent types).
        
        Args:
            agent_type: Primary agent type
            specializations: List of specializations
            
        Returns:
            Tuple of (is_hybrid, hybrid_types)
        """
        hybrid_types = []
        
        # Check if agent combines multiple core types
        core_type_indicators = {
            'documentation': ['docs', 'documentation', 'technical_writing'],
            'ticketing': ['ticketing', 'issue', 'bug_tracking'],
            'version_control': ['git', 'version', 'branching'],
            'qa': ['testing', 'quality', 'validation'],
            'research': ['research', 'analysis', 'investigation'],
            'ops': ['operations', 'deployment', 'infrastructure'],
            'security': ['security', 'auth', 'vulnerability'],
            'engineer': ['engineering', 'development', 'coding'],
            'data_engineer': ['data', 'pipeline', 'etl']
        }
        
        primary_type = agent_type
        detected_types = set()
        
        for spec in specializations:
            for core_type, indicators in core_type_indicators.items():
                if any(indicator in spec.lower() for indicator in indicators):
                    detected_types.add(core_type)
        
        # If more than one core type detected, it's hybrid
        if len(detected_types) > 1 or (len(detected_types) == 1 and primary_type not in detected_types):
            hybrid_types = list(detected_types)
            if primary_type not in hybrid_types:
                hybrid_types.append(primary_type)
            return True, hybrid_types
        
        return False, []
    
    def assess_complexity_level(self, capabilities: List[str], specializations: List[str]) -> str:
        """
        Assess agent complexity level based on capabilities and specializations.
        
        Args:
            capabilities: List of capabilities
            specializations: List of specializations
            
        Returns:
            Complexity level ('basic', 'intermediate', 'advanced', 'expert')
        """
        total_features = len(capabilities) + len(specializations)
        
        # Count advanced features
        advanced_indicators = [
            'async_', 'class:', 'framework:', 'machine_learning', 'ai',
            'microservices', 'kubernetes', 'blockchain', 'neural_network'
        ]
        
        advanced_count = sum(1 for cap in capabilities 
                           if any(indicator in cap.lower() for indicator in advanced_indicators))
        
        # Assess complexity
        if total_features >= 20 or advanced_count >= 5:
            return 'expert'
        elif total_features >= 15 or advanced_count >= 3:
            return 'advanced'
        elif total_features >= 8 or advanced_count >= 1:
            return 'intermediate'
        else:
            return 'basic'
    
    def get_all_agent_types(self) -> Set[str]:
        """Get all available agent types (core + specialized)."""
        return self.core_agent_types.union(self.specialized_agent_types)