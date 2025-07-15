#!/usr/bin/env python3
"""
Specialized Agent Discovery Demonstration - ISS-0118

Demonstrates the enhanced AgentRegistry capabilities for discovering specialized agents
beyond the base 9 core agent types, including:
- Pattern-based agent type classification
- Capability detection from agent file content
- Agent specialization metadata extraction
- Custom agent validation and verification
- Support for hybrid and composite agent types

Created: 2025-07-15
Engineer Agent Implementation for ISS-0118
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Framework imports
from claude_pm.services.agent_registry import AgentRegistry, AgentMetadata
from claude_pm.services.shared_prompt_cache import SharedPromptCache


class SpecializedAgentDiscoveryDemo:
    """Demonstration of specialized agent discovery capabilities."""
    
    def __init__(self):
        """Initialize the demo with registry and cache services."""
        self.cache_service = SharedPromptCache()
        self.registry = AgentRegistry(cache_service=self.cache_service)
        self.demo_results = {}
        
    async def run_comprehensive_demo(self) -> Dict[str, Any]:
        """
        Run comprehensive demonstration of specialized agent discovery.
        
        Returns:
            Dictionary of demo results and metrics
        """
        print("🚀 Starting Specialized Agent Discovery Demonstration")
        print("=" * 60)
        
        demo_start = time.time()
        
        # 1. Basic Discovery
        print("\n1️⃣ Basic Agent Discovery")
        basic_stats = await self._demo_basic_discovery()
        
        # 2. Specialized Agent Type Discovery
        print("\n2️⃣ Specialized Agent Type Discovery")
        specialized_stats = await self._demo_specialized_types()
        
        # 3. Framework-based Discovery
        print("\n3️⃣ Framework-based Agent Discovery")
        framework_stats = await self._demo_framework_discovery()
        
        # 4. Domain and Role Discovery
        print("\n4️⃣ Domain and Role-based Discovery")
        domain_role_stats = await self._demo_domain_role_discovery()
        
        # 5. Hybrid Agent Discovery
        print("\n5️⃣ Hybrid Agent Discovery")
        hybrid_stats = await self._demo_hybrid_discovery()
        
        # 6. Capability Search
        print("\n6️⃣ Capability-based Search")
        capability_stats = await self._demo_capability_search()
        
        # 7. Validation and Scoring
        print("\n7️⃣ Agent Validation and Scoring")
        validation_stats = await self._demo_validation_scoring()
        
        # 8. Enhanced Statistics
        print("\n8️⃣ Enhanced Registry Statistics")
        enhanced_stats = await self._demo_enhanced_statistics()
        
        demo_duration = time.time() - demo_start
        
        # Compile results
        self.demo_results = {
            'demo_metadata': {
                'timestamp': time.time(),
                'duration_seconds': demo_duration,
                'iss_ticket': 'ISS-0118',
                'agent_type': 'Engineer Agent',
                'implementation': 'Specialized Agent Discovery'
            },
            'discovery_results': {
                'basic_discovery': basic_stats,
                'specialized_types': specialized_stats,
                'framework_discovery': framework_stats,
                'domain_role_discovery': domain_role_stats,
                'hybrid_discovery': hybrid_stats,
                'capability_search': capability_stats,
                'validation_scoring': validation_stats,
                'enhanced_statistics': enhanced_stats
            },
            'performance_metrics': {
                'total_discovery_time': demo_duration,
                'discovery_efficiency': 'optimized' if demo_duration < 5.0 else 'standard'
            }
        }
        
        print(f"\n✅ Demo completed in {demo_duration:.2f} seconds")
        return self.demo_results
    
    async def _demo_basic_discovery(self) -> Dict[str, Any]:
        """Demonstrate basic agent discovery."""
        print("   🔍 Discovering all agents...")
        
        # Discover all agents
        agents = await self.registry.discover_agents()
        
        # Get basic statistics
        stats = await self.registry.get_registry_stats()
        
        print(f"   📊 Found {len(agents)} total agents")
        print(f"   🏗️ Discovery paths: {len(stats['discovery_paths'])}")
        print(f"   ✅ Validated agents: {stats['validated_agents']}")
        print(f"   ❌ Failed agents: {stats['failed_agents']}")
        
        return {
            'total_agents': len(agents),
            'discovery_paths': stats['discovery_paths'],
            'validated_count': stats['validated_agents'],
            'failed_count': stats['failed_agents'],
            'agent_types_found': stats['agents_by_type']
        }
    
    async def _demo_specialized_types(self) -> Dict[str, Any]:
        """Demonstrate specialized agent type discovery."""
        print("   🎯 Testing specialized agent type detection...")
        
        specialized_results = {}
        
        # Test some specialized types
        test_types = [
            'ui_ux', 'database', 'api', 'testing', 'performance',
            'analytics', 'machine_learning', 'frontend', 'backend',
            'cloud', 'infrastructure', 'orchestrator', 'architecture'
        ]
        
        for agent_type in test_types:
            agents = await self.registry.get_specialized_agents(agent_type)
            if agents:
                print(f"   🎯 {agent_type}: {len(agents)} agents")
                specialized_results[agent_type] = {
                    'count': len(agents),
                    'agents': [a.name for a in agents[:3]]  # Top 3
                }
        
        return specialized_results
    
    async def _demo_framework_discovery(self) -> Dict[str, Any]:
        """Demonstrate framework-based agent discovery."""
        print("   🛠️ Testing framework-based discovery...")
        
        framework_results = {}
        
        # Test common frameworks
        test_frameworks = [
            'fastapi', 'django', 'react', 'vue', 'docker',
            'kubernetes', 'tensorflow', 'pytorch', 'pandas'
        ]
        
        for framework in test_frameworks:
            agents = await self.registry.get_agents_by_framework(framework)
            if agents:
                print(f"   🛠️ {framework}: {len(agents)} agents")
                framework_results[framework] = {
                    'count': len(agents),
                    'agents': [a.name for a in agents]
                }
        
        return framework_results
    
    async def _demo_domain_role_discovery(self) -> Dict[str, Any]:
        """Demonstrate domain and role-based discovery."""
        print("   🏢 Testing domain and role discovery...")
        
        # Test domains
        domain_results = {}
        test_domains = ['e_commerce', 'healthcare', 'finance', 'education', 'ai_ml']
        
        for domain in test_domains:
            agents = await self.registry.get_agents_by_domain(domain)
            if agents:
                print(f"   🏢 Domain {domain}: {len(agents)} agents")
                domain_results[domain] = len(agents)
        
        # Test roles
        role_results = {}
        test_roles = [
            'frontend_developer', 'backend_developer', 'devops_engineer',
            'data_scientist', 'security_specialist'
        ]
        
        for role in test_roles:
            agents = await self.registry.get_agents_by_role(role)
            if agents:
                print(f"   👤 Role {role}: {len(agents)} agents")
                role_results[role] = len(agents)
        
        return {
            'domains': domain_results,
            'roles': role_results
        }
    
    async def _demo_hybrid_discovery(self) -> Dict[str, Any]:
        """Demonstrate hybrid agent discovery."""
        print("   🔗 Testing hybrid agent discovery...")
        
        hybrid_agents = await self.registry.get_hybrid_agents()
        
        hybrid_details = []
        for agent in hybrid_agents:
            print(f"   🔗 Hybrid: {agent.name} ({', '.join(agent.hybrid_types)})")
            hybrid_details.append({
                'name': agent.name,
                'primary_type': agent.type,
                'hybrid_types': agent.hybrid_types,
                'validation_score': agent.validation_score
            })
        
        return {
            'total_hybrid_agents': len(hybrid_agents),
            'hybrid_details': hybrid_details
        }
    
    async def _demo_capability_search(self) -> Dict[str, Any]:
        """Demonstrate capability-based search."""
        print("   🔍 Testing capability search...")
        
        search_results = {}
        test_capabilities = [
            'async', 'testing', 'api', 'database', 'machine_learning',
            'authentication', 'monitoring', 'deployment'
        ]
        
        for capability in test_capabilities:
            agents = await self.registry.search_agents_by_capability(capability)
            if agents:
                print(f"   🔍 Capability '{capability}': {len(agents)} agents")
                search_results[capability] = {
                    'count': len(agents),
                    'top_agents': [
                        {
                            'name': a.name,
                            'type': a.type,
                            'score': a.validation_score
                        } for a in agents[:3]
                    ]
                }
        
        return search_results
    
    async def _demo_validation_scoring(self) -> Dict[str, Any]:
        """Demonstrate agent validation and scoring."""
        print("   📊 Testing agent validation and scoring...")
        
        # Get agents by complexity
        complexity_results = {}
        complexity_levels = ['basic', 'intermediate', 'advanced', 'expert']
        
        for level in complexity_levels:
            agents = await self.registry.get_agents_by_complexity(level)
            if agents:
                print(f"   📊 Complexity {level}: {len(agents)} agents")
                avg_score = sum(a.validation_score for a in agents) / len(agents)
                complexity_results[level] = {
                    'count': len(agents),
                    'average_score': avg_score
                }
        
        return complexity_results
    
    async def _demo_enhanced_statistics(self) -> Dict[str, Any]:
        """Demonstrate enhanced registry statistics."""
        print("   📈 Generating enhanced statistics...")
        
        enhanced_stats = await self.registry.get_enhanced_registry_stats()
        
        # Print key metrics
        validation_metrics = enhanced_stats['validation_metrics']
        print(f"   📈 Average validation score: {validation_metrics['average_score']:.1f}")
        print(f"   📈 Agents above threshold: {validation_metrics['scores_above_threshold']}")
        
        discovery_metrics = enhanced_stats['discovery_beyond_core_9']
        print(f"   📈 Specialized types available: {discovery_metrics['total_specialized_types']}")
        print(f"   📈 Specialized agents found: {discovery_metrics['discovered_specialized']}")
        print(f"   📈 Custom agents: {discovery_metrics['custom_agents']}")
        
        # Summary of specializations found
        if enhanced_stats['specialization_counts']:
            print(f"   📈 Top specializations: {list(enhanced_stats['specialization_counts'].keys())[:5]}")
        
        return enhanced_stats
    
    def save_demo_results(self, output_path: str = None) -> str:
        """
        Save demo results to file.
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Path to saved results file
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = f"specialized_agent_discovery_demo_results_{timestamp}.json"
        
        output_file = Path(output_path)
        
        with open(output_file, 'w') as f:
            json.dump(self.demo_results, f, indent=2, default=str)
        
        print(f"\n💾 Demo results saved to: {output_file}")
        return str(output_file)


async def main():
    """Main demonstration function."""
    demo = SpecializedAgentDiscoveryDemo()
    
    # Run comprehensive demo
    results = await demo.run_comprehensive_demo()
    
    # Save results
    results_file = demo.save_demo_results()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎉 SPECIALIZED AGENT DISCOVERY DEMO COMPLETE")
    print("=" * 60)
    
    discovery_results = results['discovery_results']
    print(f"✅ Basic Discovery: {discovery_results['basic_discovery']['total_agents']} agents found")
    print(f"✅ Specialized Types: {len(discovery_results['specialized_types'])} types discovered")
    print(f"✅ Framework Discovery: {len(discovery_results['framework_discovery'])} frameworks found")
    print(f"✅ Hybrid Agents: {discovery_results['hybrid_discovery']['total_hybrid_agents']} hybrid agents")
    
    enhanced_stats = discovery_results['enhanced_statistics']['discovery_beyond_core_9']
    print(f"✅ Beyond Core 9: {enhanced_stats['discovered_specialized']} specialized agents")
    print(f"✅ Custom Agents: {enhanced_stats['custom_agents']} custom implementations")
    
    print(f"\n📊 Performance: {results['performance_metrics']['total_discovery_time']:.2f}s")
    print(f"📁 Results: {results_file}")
    
    return results


if __name__ == "__main__":
    # Run the demonstration
    results = asyncio.run(main())