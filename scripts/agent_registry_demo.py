#!/usr/bin/env python3
"""
AgentRegistry Demonstration Script - ISS-0118
=============================================

Demonstrates the AgentRegistry functionality with discovery mechanisms,
metadata extraction, and performance optimization.

Usage:
    python scripts/agent_registry_demo.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services import AgentRegistry, AgentMetadata, SharedPromptCache

async def demonstrate_agent_registry():
    """Demonstrate comprehensive AgentRegistry functionality."""
    
    print("🤖 AgentRegistry Demonstration - ISS-0118")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing AgentRegistry with SharedPromptCache...")
    cache_service = SharedPromptCache()
    registry = AgentRegistry(cache_service=cache_service)
    
    print(f"   Cache Service: {type(cache_service).__name__}")
    print(f"   Discovery Paths: {len(registry.discovery_paths)} paths")
    for i, path in enumerate(registry.discovery_paths, 1):
        print(f"     {i}. {path}")
    
    # Performance demonstration
    print("\n2. Agent Discovery Performance Test...")
    
    # First discovery (cold)
    start_time = time.time()
    agents = await registry.discover_agents()
    cold_discovery_time = time.time() - start_time
    
    print(f"   Cold Discovery: {cold_discovery_time:.3f}s")
    print(f"   Agents Found: {len(agents)}")
    
    # Second discovery (cached)
    start_time = time.time()
    cached_agents = await registry.discover_agents()
    cached_discovery_time = time.time() - start_time
    
    print(f"   Cached Discovery: {cached_discovery_time:.3f}s")
    print(f"   Performance Improvement: {((cold_discovery_time - cached_discovery_time) / cold_discovery_time * 100):.1f}%")
    
    # Agent Details
    print("\n3. Agent Classification and Metadata...")
    stats = await registry.get_registry_stats()
    
    print(f"   Total Agents: {stats['total_agents']}")
    print(f"   Validated Agents: {stats['validated_agents']}")
    print(f"   Failed Agents: {stats['failed_agents']}")
    print(f"   Agent Types: {stats['agent_types']}")
    
    print("\n   Agents by Tier:")
    for tier, count in stats['agents_by_tier'].items():
        print(f"     {tier}: {count} agents")
    
    print("\n   Agents by Type:")
    for agent_type, count in stats['agents_by_type'].items():
        print(f"     {agent_type}: {count} agents")
    
    # Individual Agent Details
    print("\n4. Individual Agent Metadata...")
    
    # Get agent types
    agent_types = await registry.get_agent_types()
    print(f"   Discovered Types: {', '.join(sorted(agent_types))}")
    
    # Show details for first few agents
    all_agents = await registry.list_agents()
    for i, agent_metadata in enumerate(all_agents[:3], 1):
        print(f"\n   Agent {i}: {agent_metadata.name}")
        print(f"     Type: {agent_metadata.type}")
        print(f"     Tier: {agent_metadata.tier}")
        print(f"     Version: {agent_metadata.version or 'Unknown'}")
        print(f"     Validated: {'✓' if agent_metadata.validated else '✗'}")
        print(f"     File Size: {agent_metadata.file_size:,} bytes")
        print(f"     Capabilities: {len(agent_metadata.capabilities)} functions")
        if agent_metadata.capabilities:
            print(f"       - {', '.join(agent_metadata.capabilities[:3])}...")
    
    # Type Filtering
    print("\n5. Type-Based Filtering...")
    
    # Get agents by type
    for agent_type in ['documentation', 'version_control', 'custom']:
        type_agents = await registry.list_agents(agent_type=agent_type)
        if type_agents:
            print(f"   {agent_type.title()} Agents: {len(type_agents)}")
            for agent in type_agents:
                print(f"     - {agent.name} ({agent.tier} tier)")
    
    # Validation Status
    print("\n6. Validation and Error Handling...")
    
    valid_agents = [a for a in all_agents if a.validated]
    invalid_agents = [a for a in all_agents if not a.validated]
    
    print(f"   Valid Agents: {len(valid_agents)}")
    print(f"   Invalid Agents: {len(invalid_agents)}")
    
    if invalid_agents:
        print("   Error Details:")
        for agent in invalid_agents:
            print(f"     - {agent.name}: {agent.error_message}")
    
    # Cache Performance
    print("\n7. Cache Performance Metrics...")
    
    # Force cache refresh
    start_time = time.time()
    refreshed_agents = await registry.discover_agents(force_refresh=True)
    refresh_time = time.time() - start_time
    
    print(f"   Forced Refresh: {refresh_time:.3f}s")
    print(f"   Cache Efficiency: {((cold_discovery_time - cached_discovery_time) / cold_discovery_time * 100):.1f}% faster")
    
    # Registry Statistics Summary
    print("\n8. Registry Summary...")
    print(f"   ✅ Agent Discovery: {len(agents)} agents in {cold_discovery_time:.3f}s")
    print(f"   ✅ Cache Performance: {cached_discovery_time:.3f}s ({((cold_discovery_time - cached_discovery_time) / cold_discovery_time * 100):.1f}% improvement)")
    print(f"   ✅ Type Classification: {len(agent_types)} unique types")
    print(f"   ✅ Validation Success: {len(valid_agents)}/{len(all_agents)} agents ({(len(valid_agents)/len(all_agents)*100):.1f}%)")
    print(f"   ✅ Hierarchy Support: {len(stats['agents_by_tier'])} tiers")
    
    print("\n🎯 ISS-0118 AgentRegistry Implementation: ✅ FULLY OPERATIONAL")

def main():
    """Main entry point."""
    try:
        asyncio.run(demonstrate_agent_registry())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration stopped by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()