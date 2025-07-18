#!/usr/bin/env python3
"""
Base Agent Management Demo
==========================

Demonstrates how to use the BaseAgentManager API to update base_agent.md
in a structured way while enforcing the template structure.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.services.base_agent_manager import (
    BaseAgentManager, BaseAgentSection,
    get_base_agent_manager, update_base_agent_section, validate_base_agent
)


def main():
    """Run base agent management demo."""
    print("=" * 60)
    print("Base Agent Management API Demo")
    print("=" * 60)
    print()
    
    # Initialize manager
    manager = get_base_agent_manager()
    
    # Demo 1: Validate current structure
    print("1. Validating Base Agent Structure:")
    print("-" * 40)
    validation = validate_base_agent()
    for section, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {section}")
    print()
    
    # Demo 2: Read current base agent
    print("2. Reading Current Base Agent:")
    print("-" * 40)
    base_agent = manager.read_base_agent()
    if base_agent:
        print(f"   Title: {base_agent.title}")
        print(f"   Description: {base_agent.description[:50]}...")
        print(f"   Sections found: {len(base_agent.raw_sections)}")
        print(f"   Escalation triggers: {len(base_agent.escalation_triggers)}")
    print()
    
    # Demo 3: Add a new behavioral rule
    print("3. Adding New Behavioral Rule:")
    print("-" * 40)
    new_rule = "Always include execution time metrics in performance reports"
    success = manager.add_behavioral_rule("Performance Reporting", new_rule)
    if success:
        print(f"   ✅ Added rule: {new_rule}")
    else:
        print(f"   ⚠️  Rule already exists or failed to add")
    print()
    
    # Demo 4: Add a new quality standard
    print("4. Adding New Quality Standard:")
    print("-" * 40)
    new_standard = "Maintain API response time below 100ms (p95)"
    success = manager.add_quality_standard("API Performance", new_standard)
    if success:
        print(f"   ✅ Added standard: {new_standard}")
    else:
        print(f"   ⚠️  Standard already exists or failed to add")
    print()
    
    # Demo 5: Add an escalation trigger
    print("5. Adding New Escalation Trigger:")
    print("-" * 40)
    new_trigger = "AI API rate limits exceeded repeatedly"
    success = manager.add_escalation_trigger(new_trigger)
    if success:
        print(f"   ✅ Added trigger: {new_trigger}")
    else:
        print(f"   ⚠️  Trigger already exists or failed to add")
    print()
    
    # Demo 6: Update a specific section
    print("6. Updating Temporal Context Section:")
    print("-" * 40)
    new_temporal_content = """
You must integrate temporal awareness into all operations:
- Consider current date and time in planning and prioritization
- Account for sprint deadlines and release schedules  
- Factor in time zones for global teams
- Track time-sensitive tasks and expirations
- Maintain historical context for decisions
- Consider business hours and holidays when scheduling
- Account for dependency timelines across agents
"""
    
    result = update_base_agent_section(BaseAgentSection.TEMPORAL_CONTEXT, new_temporal_content)
    if result:
        print("   ✅ Temporal context section updated successfully")
    else:
        print("   ❌ Failed to update temporal context section")
    print()
    
    # Demo 7: Structured updates with dictionary
    print("7. Performing Structured Updates:")
    print("-" * 40)
    updates = {
        "title": "Base Agent Instructions",
        "description": "These instructions are prepended to EVERY agent prompt. They contain common rules, behaviors, and constraints that apply to ALL agents."
    }
    
    updated = manager.update_base_agent(updates, backup=True)
    if updated:
        print("   ✅ Base agent updated with new title and description")
        print("   📁 Backup created before update")
    else:
        print("   ❌ Failed to update base agent")
    print()
    
    # Demo 8: Show section enum values for API reference
    print("8. Available Section Types for Updates:")
    print("-" * 40)
    for section in BaseAgentSection:
        print(f"   - BaseAgentSection.{section.name}: '{section.value}'")
    print()
    
    print("✅ Demo completed successfully!")
    print()
    print("Key API Methods:")
    print("- manager.read_base_agent() - Read current base agent")
    print("- manager.update_base_agent(updates, backup=True) - Update with dict")
    print("- manager.update_section(section, content) - Update specific section")
    print("- manager.add_behavioral_rule(category, rule) - Add behavioral rule")
    print("- manager.add_quality_standard(category, standard) - Add quality standard")
    print("- manager.add_escalation_trigger(trigger) - Add escalation trigger")
    print("- manager.validate_structure() - Validate all sections present")


if __name__ == "__main__":
    main()