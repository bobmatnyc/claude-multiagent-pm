#!/usr/bin/env python3
"""
Agent Modification Tracking Demo - ISS-0118 Implementation
==========================================================

Comprehensive demonstration of the agent modification tracking and persistence
system integration with AgentRegistry and SharedPromptCache.

This demo shows:
- Agent modification tracking in real-time
- Persistence operations across hierarchy tiers
- Cache invalidation and registry synchronization
- Backup and restore functionality
- Conflict detection and resolution
- Performance monitoring and metrics

Usage:
    python scripts/agent_modification_demo.py --demo basic
    python scripts/agent_modification_demo.py --demo advanced
    python scripts/agent_modification_demo.py --demo performance
"""

import asyncio
import json
import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.agent_modification_tracker import (
    AgentModificationTracker, 
    ModificationType, 
    ModificationTier
)
from claude_pm.services.agent_persistence_service import (
    AgentPersistenceService,
    PersistenceStrategy
)
from claude_pm.services.agent_lifecycle_manager import (
    AgentLifecycleManager,
    LifecycleOperation
)
from claude_pm.services.shared_prompt_cache import SharedPromptCache
from claude_pm.services.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentModificationDemo:
    """Comprehensive demonstration of agent modification tracking system."""
    
    def __init__(self):
        """Initialize demo components."""
        self.temp_dir = None
        self.cache_service = None
        self.registry_service = None
        self.tracker_service = None
        self.persistence_service = None
        self.lifecycle_manager = None
        
        # Demo data
        self.demo_agents = {
            'custom_analyzer': {
                'content': '''#!/usr/bin/env python3
"""
Custom Analyzer Agent - Demo Agent
==================================

Custom agent for specialized analysis tasks.
"""

class CustomAnalyzerAgent:
    """Custom analyzer for specialized tasks."""
    
    def __init__(self):
        self.capabilities = ["analysis", "custom_processing", "reporting"]
    
    async def analyze(self, data):
        """Perform custom analysis."""
        return {"status": "analyzed", "data": data}
    
    async def generate_report(self, analysis_result):
        """Generate analysis report."""
        return f"Report: {analysis_result}"
''',
                'type': 'custom',
                'tier': ModificationTier.USER
            },
            'project_helper': {
                'content': '''#!/usr/bin/env python3
"""
Project Helper Agent - Demo Agent
=================================

Project-specific helper agent for local tasks.
"""

class ProjectHelperAgent:
    """Helper agent for project-specific tasks."""
    
    def __init__(self):
        self.capabilities = ["project_management", "task_coordination", "local_operations"]
    
    async def coordinate_task(self, task_name):
        """Coordinate project task."""
        return {"task": task_name, "status": "coordinated"}
    
    async def manage_project_state(self, state_data):
        """Manage project state."""
        return {"state": "managed", "data": state_data}
''',
                'type': 'project_helper',
                'tier': ModificationTier.PROJECT
            }
        }
    
    async def setup(self):
        """Set up demo environment."""
        logger.info("🚀 Setting up Agent Modification Tracking Demo")
        
        # Create temporary directory for demo
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_demo_"))
        logger.info(f"Demo directory: {self.temp_dir}")
        
        # Create agent directories
        user_agents_dir = self.temp_dir / '.claude-pm' / 'agents' / 'user'
        project_agents_dir = self.temp_dir / '.claude-pm' / 'agents' / 'project'
        user_agents_dir.mkdir(parents=True, exist_ok=True)
        project_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize services
        try:
            # SharedPromptCache
            self.cache_service = SharedPromptCache.get_instance({
                "max_size": 100,
                "max_memory_mb": 10,
                "default_ttl": 300
            })
            await self.cache_service.start()
            
            # AgentRegistry
            self.registry_service = AgentRegistry(cache_service=self.cache_service)
            
            # AgentModificationTracker
            self.tracker_service = AgentModificationTracker({
                "enable_monitoring": True,
                "backup_enabled": True,
                "validation_enabled": True
            })
            await self.tracker_service.start()
            
            # AgentPersistenceService
            self.persistence_service = AgentPersistenceService({
                "default_strategy": PersistenceStrategy.USER_OVERRIDE.value,
                "enable_auto_sync": True,
                "enable_conflict_detection": True
            })
            await self.persistence_service.start()
            
            # AgentLifecycleManager
            self.lifecycle_manager = AgentLifecycleManager({
                "enable_auto_backup": True,
                "enable_auto_validation": True,
                "enable_cache_invalidation": True,
                "enable_registry_sync": True
            })
            await self.lifecycle_manager.start()
            
            logger.info("✅ All services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    async def cleanup(self):
        """Clean up demo environment."""
        logger.info("🧹 Cleaning up demo environment")
        
        # Stop services
        services = [
            self.lifecycle_manager,
            self.persistence_service,
            self.tracker_service,
            self.cache_service
        ]
        
        for service in services:
            if service:
                try:
                    await service.stop()
                except Exception as e:
                    logger.warning(f"Error stopping service: {e}")
        
        # Clean up temporary directory
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
        
        logger.info("✅ Cleanup completed")
    
    async def run_basic_demo(self):
        """Run basic modification tracking demonstration."""
        logger.info("\n" + "="*60)
        logger.info("🎯 BASIC MODIFICATION TRACKING DEMO")
        logger.info("="*60)
        
        try:
            # Demo 1: Create agent
            logger.info("\n📝 Demo 1: Creating new agent")
            agent_name = "custom_analyzer"
            agent_data = self.demo_agents[agent_name]
            
            create_result = await self.lifecycle_manager.create_agent(
                agent_name=agent_name,
                agent_content=agent_data['content'],
                tier=agent_data['tier'],
                agent_type=agent_data['type']
            )
            
            logger.info(f"✅ Agent creation result: {create_result.success}")
            logger.info(f"   Duration: {create_result.duration_ms:.1f}ms")
            logger.info(f"   Modification ID: {create_result.modification_id}")
            logger.info(f"   Cache invalidated: {create_result.cache_invalidated}")
            
            # Demo 2: Modify agent
            logger.info("\n✏️  Demo 2: Modifying existing agent")
            modified_content = agent_data['content'].replace(
                'Custom analyzer for specialized tasks.',
                'Enhanced custom analyzer with advanced capabilities.'
            )
            
            update_result = await self.lifecycle_manager.update_agent(
                agent_name=agent_name,
                agent_content=modified_content,
                change_reason="Enhanced capabilities"
            )
            
            logger.info(f"✅ Agent update result: {update_result.success}")
            logger.info(f"   Duration: {update_result.duration_ms:.1f}ms")
            logger.info(f"   Modification ID: {update_result.modification_id}")
            
            # Demo 3: View modification history
            logger.info("\n📊 Demo 3: Viewing modification history")
            history = await self.tracker_service.get_modification_history(agent_name)
            if history:
                logger.info(f"   Total modifications: {history.total_modifications}")
                logger.info(f"   First seen: {history.first_seen}")
                logger.info(f"   Last modified: {history.last_modified}")
                logger.info("   Recent modifications:")
                for mod in history.get_recent_modifications(24):
                    logger.info(f"     - {mod.modification_type.value} at {mod.modification_datetime}")
            
            # Demo 4: Cache performance
            logger.info("\n⚡ Demo 4: Cache performance verification")
            cache_metrics = self.cache_service.get_metrics()
            logger.info(f"   Cache hits: {cache_metrics['hits']}")
            logger.info(f"   Cache misses: {cache_metrics['misses']}")
            logger.info(f"   Hit rate: {cache_metrics['hit_rate']:.1%}")
            logger.info(f"   Cache size: {cache_metrics['entry_count']} entries")
            
        except Exception as e:
            logger.error(f"❌ Basic demo failed: {e}")
            raise
    
    async def run_advanced_demo(self):
        """Run advanced modification tracking demonstration."""
        logger.info("\n" + "="*60)
        logger.info("🎯 ADVANCED MODIFICATION TRACKING DEMO")
        logger.info("="*60)
        
        try:
            # Demo 1: Multi-tier agent management
            logger.info("\n🏗️  Demo 1: Multi-tier agent management")
            
            # Create agents in different tiers
            for agent_name, agent_data in self.demo_agents.items():
                logger.info(f"   Creating {agent_name} in {agent_data['tier'].value} tier")
                
                result = await self.lifecycle_manager.create_agent(
                    agent_name=agent_name,
                    agent_content=agent_data['content'],
                    tier=agent_data['tier'],
                    agent_type=agent_data['type']
                )
                
                logger.info(f"   ✅ Created with success: {result.success}")
            
            # Demo 2: Persistence strategy testing
            logger.info("\n💾 Demo 2: Persistence strategy testing")
            
            test_agent = "persistence_test"
            test_content = '''# Test Agent for Persistence
def test_function():
    return "persistence test"
'''
            
            # Test different strategies
            strategies = [
                PersistenceStrategy.TIER_SPECIFIC,
                PersistenceStrategy.USER_OVERRIDE,
                PersistenceStrategy.DISTRIBUTED
            ]
            
            for strategy in strategies:
                logger.info(f"   Testing strategy: {strategy.value}")
                
                persistence_record = await self.persistence_service.persist_agent(
                    agent_name=f"{test_agent}_{strategy.value}",
                    agent_content=test_content,
                    source_tier=ModificationTier.USER,
                    strategy=strategy,
                    test_strategy=strategy.value
                )
                
                logger.info(f"   ✅ Persistence success: {persistence_record.success}")
                logger.info(f"      Target tier: {persistence_record.target_tier.value}")
            
            # Demo 3: Backup and restore
            logger.info("\n🔄 Demo 3: Backup and restore functionality")
            
            # Modify an agent to create backup
            agent_name = "custom_analyzer"
            modified_content = "# Modified content for backup test\ndef backup_test(): pass"
            
            await self.lifecycle_manager.update_agent(
                agent_name=agent_name,
                agent_content=modified_content,
                create_backup=True
            )
            
            # Get agent status
            agent_status = await self.lifecycle_manager.get_agent_status(agent_name)
            logger.info(f"   Agent version: {agent_status.version}")
            logger.info(f"   Backup paths: {len(agent_status.backup_paths)}")
            
            # Restore from backup
            if agent_status.backup_paths:
                restore_result = await self.lifecycle_manager.restore_agent(
                    agent_name=agent_name,
                    backup_path=agent_status.backup_paths[-1]
                )
                logger.info(f"   ✅ Restore success: {restore_result.success}")
            
            # Demo 4: Registry synchronization
            logger.info("\n🔄 Demo 4: Registry synchronization")
            
            # Discover agents through registry
            await self.registry_service.discover_agents()
            registry_stats = await self.registry_service.get_registry_stats()
            
            logger.info(f"   Discovered agents: {registry_stats['total_agents']}")
            logger.info(f"   Validated agents: {registry_stats['validated_agents']}")
            logger.info(f"   Agent types: {registry_stats['agent_types']}")
            logger.info(f"   Agents by tier: {registry_stats['agents_by_tier']}")
            
        except Exception as e:
            logger.error(f"❌ Advanced demo failed: {e}")
            raise
    
    async def run_performance_demo(self):
        """Run performance benchmarking demonstration."""
        logger.info("\n" + "="*60)
        logger.info("🎯 PERFORMANCE BENCHMARKING DEMO")
        logger.info("="*60)
        
        try:
            # Demo 1: Bulk agent operations
            logger.info("\n⚡ Demo 1: Bulk agent operations performance")
            
            num_agents = 10
            start_time = time.time()
            
            # Create multiple agents
            for i in range(num_agents):
                agent_name = f"perf_agent_{i:03d}"
                agent_content = f'''# Performance Test Agent {i}
class PerfAgent{i}:
    def __init__(self):
        self.agent_id = {i}
    
    def process(self):
        return f"Processing from agent {self.agent_id}"
'''
                
                await self.lifecycle_manager.create_agent(
                    agent_name=agent_name,
                    agent_content=agent_content,
                    tier=ModificationTier.USER,
                    agent_type="performance_test"
                )
            
            bulk_create_time = time.time() - start_time
            logger.info(f"   ✅ Created {num_agents} agents in {bulk_create_time:.3f}s")
            logger.info(f"   Average per agent: {(bulk_create_time/num_agents)*1000:.1f}ms")
            
            # Demo 2: Modification tracking performance
            logger.info("\n📊 Demo 2: Modification tracking performance")
            
            start_time = time.time()
            
            # Perform rapid modifications
            for i in range(num_agents):
                agent_name = f"perf_agent_{i:03d}"
                modified_content = f"# Modified at {time.time()}\ndef modified_function(): pass"
                
                await self.lifecycle_manager.update_agent(
                    agent_name=agent_name,
                    agent_content=modified_content
                )
            
            bulk_modify_time = time.time() - start_time
            logger.info(f"   ✅ Modified {num_agents} agents in {bulk_modify_time:.3f}s")
            logger.info(f"   Average per modification: {(bulk_modify_time/num_agents)*1000:.1f}ms")
            
            # Demo 3: Cache performance analysis
            logger.info("\n🚀 Demo 3: Cache performance analysis")
            
            cache_metrics = self.cache_service.get_metrics()
            logger.info(f"   Total cache operations: {cache_metrics['hits'] + cache_metrics['misses']}")
            logger.info(f"   Cache hit rate: {cache_metrics['hit_rate']:.1%}")
            logger.info(f"   Cache memory usage: {cache_metrics['size_mb']:.2f} MB")
            logger.info(f"   Cache entries: {cache_metrics['entry_count']}")
            
            # Demo 4: Overall system metrics
            logger.info("\n📈 Demo 4: Overall system performance metrics")
            
            # Tracker stats
            tracker_stats = await self.tracker_service.get_modification_stats()
            logger.info(f"   Total agents tracked: {tracker_stats['total_agents_tracked']}")
            logger.info(f"   Total modifications: {tracker_stats['total_modifications']}")
            logger.info(f"   Active modifications: {tracker_stats['active_modifications']}")
            
            # Persistence stats
            persistence_stats = await self.persistence_service.get_persistence_stats()
            logger.info(f"   Persistence operations: {persistence_stats['total_operations']}")
            logger.info(f"   Success rate: {persistence_stats['success_rate']:.1f}%")
            
            # Lifecycle stats
            lifecycle_stats = await self.lifecycle_manager.get_lifecycle_stats()
            logger.info(f"   Lifecycle operations: {lifecycle_stats['performance_metrics']['total_operations']}")
            logger.info(f"   Average duration: {lifecycle_stats['performance_metrics']['average_duration_ms']:.1f}ms")
            
        except Exception as e:
            logger.error(f"❌ Performance demo failed: {e}")
            raise
    
    async def generate_final_report(self):
        """Generate comprehensive final report."""
        logger.info("\n" + "="*60)
        logger.info("📋 FINAL COMPREHENSIVE REPORT")
        logger.info("="*60)
        
        try:
            report = {
                'timestamp': time.time(),
                'demo_summary': {
                    'total_agents_created': 0,
                    'total_modifications': 0,
                    'total_persistence_operations': 0,
                    'cache_performance': {},
                    'registry_stats': {},
                    'overall_performance': {}
                }
            }
            
            # Collect comprehensive statistics
            if self.tracker_service:
                tracker_stats = await self.tracker_service.get_modification_stats()
                report['tracker_stats'] = tracker_stats
                report['demo_summary']['total_modifications'] = tracker_stats['total_modifications']
            
            if self.persistence_service:
                persistence_stats = await self.persistence_service.get_persistence_stats()
                report['persistence_stats'] = persistence_stats
                report['demo_summary']['total_persistence_operations'] = persistence_stats['total_operations']
            
            if self.cache_service:
                cache_metrics = self.cache_service.get_metrics()
                report['cache_metrics'] = cache_metrics
                report['demo_summary']['cache_performance'] = {
                    'hit_rate': cache_metrics['hit_rate'],
                    'total_operations': cache_metrics['hits'] + cache_metrics['misses']
                }
            
            if self.registry_service:
                registry_stats = await self.registry_service.get_registry_stats()
                report['registry_stats'] = registry_stats
                report['demo_summary']['registry_stats'] = registry_stats
            
            if self.lifecycle_manager:
                lifecycle_stats = await self.lifecycle_manager.get_lifecycle_stats()
                report['lifecycle_stats'] = lifecycle_stats
                report['demo_summary']['overall_performance'] = lifecycle_stats['performance_metrics']
            
            # Save report to file
            report_file = self.temp_dir / 'agent_modification_demo_report.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"📄 Full report saved to: {report_file}")
            
            # Print summary
            logger.info("\n🎯 DEMO SUMMARY:")
            logger.info(f"   Total modifications tracked: {report['demo_summary']['total_modifications']}")
            logger.info(f"   Total persistence operations: {report['demo_summary']['total_persistence_operations']}")
            
            if 'cache_performance' in report['demo_summary']:
                cache_perf = report['demo_summary']['cache_performance']
                logger.info(f"   Cache hit rate: {cache_perf.get('hit_rate', 0):.1%}")
                logger.info(f"   Cache operations: {cache_perf.get('total_operations', 0)}")
            
            if 'overall_performance' in report['demo_summary']:
                perf = report['demo_summary']['overall_performance']
                logger.info(f"   Average operation time: {perf.get('average_duration_ms', 0):.1f}ms")
                logger.info(f"   Success rate: {(perf.get('successful_operations', 0) / max(perf.get('total_operations', 1), 1) * 100):.1f}%")
            
            logger.info("\n✅ Agent Modification Tracking Demo completed successfully!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate final report: {e}")
            raise


async def main():
    """Main demo execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Modification Tracking Demo')
    parser.add_argument('--demo', choices=['basic', 'advanced', 'performance', 'all'], 
                       default='all', help='Demo type to run')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    demo = AgentModificationDemo()
    
    try:
        await demo.setup()
        
        if args.demo in ['basic', 'all']:
            await demo.run_basic_demo()
        
        if args.demo in ['advanced', 'all']:
            await demo.run_advanced_demo()
        
        if args.demo in ['performance', 'all']:
            await demo.run_performance_demo()
        
        # Generate final report
        report = await demo.generate_final_report()
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())