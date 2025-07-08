#!/usr/bin/env python3
"""
Enforcement Integration Demo - FWK-003 Technical Enforcement Layer

This demo shows the Technical Enforcement Layer in action with the multi-agent orchestrator.
Demonstrates delegation constraint enforcement, file access control, and violation monitoring.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.core.enforcement import (
    get_enforcement_engine, EnforcementEngine, Agent, Action,
    AgentType, ActionType, ViolationSeverity, FileCategory,
    enforce_file_access, validate_agent_action
)
from claude_pm.services.claude_pm_memory import create_claude_pm_memory
from claude_pm.services.multi_agent_orchestrator import (
    MultiAgentOrchestrator, AgentTask, AgentType as OrchestratorAgentType,
    create_multi_agent_orchestrator
)


async def demo_basic_enforcement():
    """Demonstrate basic enforcement functionality."""
    print("\n" + "="*60)
    print("🔒 TECHNICAL ENFORCEMENT LAYER (FWK-003) DEMO")
    print("="*60)
    
    # Get the global enforcement engine
    engine = get_enforcement_engine()
    
    print(f"\n✅ Enforcement Engine Status: {'ENABLED' if engine.enabled else 'DISABLED'}")
    
    # Test scenarios that should PASS
    print("\n🟢 AUTHORIZED ACTIONS (Should Pass):")
    authorized_tests = [
        ("orchestrator", "CLAUDE.md", "write", "PM files"),
        ("engineer", "src/main.py", "write", "source code"),
        ("qa", "tests/test_main.py", "write", "test files"),
        ("operations", "docker/Dockerfile", "write", "configuration"),
        ("researcher", "docs/research.md", "write", "research docs"),
        ("architect", "templates/api.yml", "write", "scaffolding"),
    ]
    
    for agent_type, file_path, action, description in authorized_tests:
        result = enforce_file_access(agent_type, file_path, action)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {agent_type.upper():15} {action} {file_path:25} ({description})")
    
    # Test scenarios that should FAIL
    print("\n🔴 UNAUTHORIZED ACTIONS (Should Fail):")
    unauthorized_tests = [
        ("orchestrator", "src/main.py", "write", "CRITICAL: Orchestrator accessing code"),
        ("engineer", "CLAUDE.md", "write", "Engineer accessing PM files"),
        ("qa", "src/main.py", "write", "QA accessing source code"),
        ("operations", "src/main.py", "write", "Ops accessing source code"),
        ("researcher", "src/main.py", "write", "Researcher accessing source code"),
    ]
    
    for agent_type, file_path, action, description in unauthorized_tests:
        result = enforce_file_access(agent_type, file_path, action)
        status = "❌ BLOCKED" if not result else "⚠️  UNEXPECTED PASS"
        print(f"  {status} {agent_type.upper():15} {action} {file_path:25} ({description})")
    
    # Show enforcement statistics
    stats = engine.get_enforcement_stats()
    print(f"\n📊 ENFORCEMENT STATISTICS:")
    print(f"  Total Violations: {stats['total_violations']}")
    print(f"  Active Alerts: {stats['active_alerts']}")
    print(f"  Critical Violations: {stats['critical_violations']}")
    
    if stats['recent_violations']:
        print(f"\n⚠️  Recent Violations:")
        for violation in stats['recent_violations'][-3:]:  # Last 3
            print(f"    {violation['severity'].upper()}: {violation['agent']} - {violation['violation_type']}")


async def demo_detailed_validation():
    """Demonstrate detailed validation with full results."""
    print("\n" + "="*60)
    print("🔍 DETAILED VALIDATION ANALYSIS")
    print("="*60)
    
    # Test critical violation: Orchestrator accessing source code
    print("\n🚨 CRITICAL VIOLATION ANALYSIS:")
    result = validate_agent_action("orchestrator", "write", "src/main.py", "critical-test")
    
    print(f"  Action: Orchestrator writing to src/main.py")
    print(f"  Result: {'AUTHORIZED' if result.is_valid else 'BLOCKED'}")
    print(f"  Violations: {len(result.violations)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    if result.violations:
        print("\n  🚨 Violation Details:")
        for i, violation in enumerate(result.violations, 1):
            print(f"    {i}. Type: {violation.violation_type}")
            print(f"       Severity: {violation.severity.value.upper()}")
            print(f"       Description: {violation.description}")
            if violation.resolution_guidance:
                print(f"       Resolution: {violation.resolution_guidance}")
            print()
    
    # Test authorized action for comparison
    print("\n✅ AUTHORIZED ACTION ANALYSIS:")
    result = validate_agent_action("engineer", "write", "src/main.py", "authorized-test")
    
    print(f"  Action: Engineer writing to src/main.py")
    print(f"  Result: {'AUTHORIZED' if result.is_valid else 'BLOCKED'}")
    print(f"  File Category: {result.context.get('file_category', 'unknown')}")
    
    if result.warnings:
        print(f"  Warnings: {result.warnings}")


async def demo_orchestrator_integration():
    """Demonstrate enforcement integration with multi-agent orchestrator."""
    print("\n" + "="*60)
    print("🤖 MULTI-AGENT ORCHESTRATOR INTEGRATION")
    print("="*60)
    
    try:
        # Create memory instance
        memory = await create_claude_pm_memory()
        
        # Create orchestrator with enforcement
        base_repo = str(project_root)
        orchestrator = await create_multi_agent_orchestrator(base_repo, memory, max_parallel=3)
        
        print(f"✅ Orchestrator initialized with enforcement engine")
        
        # Get orchestrator stats including enforcement
        stats = orchestrator.get_orchestrator_stats()
        print(f"\n📊 ORCHESTRATOR STATS WITH ENFORCEMENT:")
        print(f"  Agent Types: {len(stats['agent_types'])}")
        print(f"  Max Parallel: {stats['max_parallel']}")
        
        if 'enforcement' in stats:
            enforcement_stats = stats['enforcement']
            if 'error' not in enforcement_stats:
                print(f"  Enforcement Enabled: {enforcement_stats.get('enforcement_enabled', 'unknown')}")
                print(f"  Total Violations: {enforcement_stats.get('total_violations', 0)}")
                print(f"  Active Alerts: {enforcement_stats.get('active_alerts', 0)}")
            else:
                print(f"  Enforcement Error: {enforcement_stats['error']}")
        
        # Test submitting tasks that will trigger enforcement
        print(f"\n🧪 TESTING TASK AUTHORIZATION:")
        
        # Test 1: Orchestrator task (should pass if it's PM work)
        try:
            task_id = await orchestrator.submit_task(
                agent_type=OrchestratorAgentType.ORCHESTRATOR,
                description="Review project documentation and create status report",
                project_name="enforcement-demo",
                context={"target_files": ["CLAUDE.md", "BACKLOG.md"]},
                priority=7
            )
            print(f"  ✅ Orchestrator PM task submitted: {task_id}")
        except Exception as e:
            print(f"  ❌ Orchestrator task failed: {e}")
        
        # Test 2: Engineer task (should pass for code work)
        try:
            task_id = await orchestrator.submit_task(
                agent_type=OrchestratorAgentType.ENGINEER,
                description="Implement new feature in main module",
                project_name="enforcement-demo",
                context={"target_files": ["src/main.py", "src/utils.py"]},
                priority=8
            )
            print(f"  ✅ Engineer code task submitted: {task_id}")
        except Exception as e:
            print(f"  ❌ Engineer task failed: {e}")
        
        # Test 3: QA task (should pass for test work)
        try:
            task_id = await orchestrator.submit_task(
                agent_type=OrchestratorAgentType.QA,
                description="Write comprehensive test suite",
                project_name="enforcement-demo",
                context={"target_files": ["tests/test_main.py", "tests/test_utils.py"]},
                priority=6
            )
            print(f"  ✅ QA test task submitted: {task_id}")
        except Exception as e:
            print(f"  ❌ QA task failed: {e}")
        
        print(f"\n📋 Tasks in queue: {len(orchestrator.task_queue)}")
        
        # Cleanup
        await orchestrator.cleanup()
        
    except Exception as e:
        print(f"❌ Orchestrator integration error: {e}")
        import traceback
        traceback.print_exc()


async def demo_violation_monitoring():
    """Demonstrate violation monitoring and reporting."""
    print("\n" + "="*60)
    print("📊 VIOLATION MONITORING & REPORTING")
    print("="*60)
    
    engine = get_enforcement_engine()
    
    # Generate some violations for demonstration
    print("🧪 Generating test violations...")
    
    violation_scenarios = [
        ("orchestrator", "src/main.py", "write"),      # Critical
        ("orchestrator", "src/utils.py", "write"),     # Critical  
        ("engineer", "CLAUDE.md", "write"),            # High
        ("qa", "src/test.py", "write"),                # High (wrong file type)
        ("operations", "src/config.py", "write"),      # High
    ]
    
    for agent_type, file_path, action in violation_scenarios:
        result = validate_agent_action(agent_type, action, file_path)
        if not result.is_valid:
            print(f"  ⚠️  Generated violation: {agent_type} -> {file_path}")
    
    # Get violation monitor
    monitor = engine.violation_monitor
    
    # Show alerts
    alerts = monitor.get_violation_alerts()
    print(f"\n🚨 ACTIVE ALERTS: {len(alerts)}")
    
    for alert in alerts[:3]:  # Show first 3
        print(f"  Alert {alert.alert_id}: {alert.alert_level.value.upper()}")
        print(f"    Message: {alert.message}")
        print(f"    Time: {alert.timestamp.strftime('%H:%M:%S')}")
        print()
    
    # Generate daily report
    print("📈 GENERATING DAILY VIOLATION REPORT...")
    report = monitor.generate_violation_report()
    
    print(f"\n📊 VIOLATION REPORT ({report.report_id}):")
    print(f"  Time Range: {report.start_time.strftime('%H:%M')} - {report.end_time.strftime('%H:%M')}")
    print(f"  Total Violations: {report.summary['total_violations']}")
    
    if report.summary['by_severity']:
        print(f"  By Severity:")
        for severity, count in report.summary['by_severity'].items():
            print(f"    {severity.upper()}: {count}")
    
    if report.summary['by_agent_type']:
        print(f"  By Agent Type:")
        for agent_type, count in report.summary['by_agent_type'].items():
            print(f"    {agent_type.upper()}: {count}")
    
    if report.recommendations:
        print(f"  📋 Recommendations:")
        for rec in report.recommendations:
            print(f"    • {rec}")


async def demo_file_classification():
    """Demonstrate file classification system."""
    print("\n" + "="*60)
    print("📁 FILE CLASSIFICATION SYSTEM")
    print("="*60)
    
    from claude_pm.core.enforcement import FileClassifier
    
    test_files = [
        # Source code files
        "src/main.py", "app.js", "component.tsx", "utils.java",
        
        # Configuration files  
        "Dockerfile", "docker-compose.yml", "package.json", "requirements.txt",
        
        # Test files
        "test_main.py", "app.test.js", "tests/integration.py",
        
        # Documentation
        "README.md", "CHANGELOG.md", "docs/api.rst",
        
        # Project management
        "CLAUDE.md", "BACKLOG.md", "trackdown/issue-001.md",
        
        # Scaffolding
        "templates/component.js", "api-spec.yml", "swagger.yml",
        
        # Research docs
        "research/analysis.md", "docs/research/evaluation.md"
    ]
    
    print("🏷️  FILE CLASSIFICATION RESULTS:")
    category_counts = {}
    
    for file_path in test_files:
        category = FileClassifier.classify_file(file_path)
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # Color coding for categories
        color_map = {
            FileCategory.SOURCE_CODE: "🔵",
            FileCategory.CONFIGURATION: "🟡", 
            FileCategory.TEST_FILES: "🟢",
            FileCategory.DOCUMENTATION: "⚪",
            FileCategory.PROJECT_MANAGEMENT: "🔴",
            FileCategory.SCAFFOLDING: "🟣",
            FileCategory.RESEARCH_DOCS: "🟤"
        }
        
        color = color_map.get(category, "⚫")
        print(f"  {color} {category.value:20} {file_path}")
    
    print(f"\n📊 CLASSIFICATION SUMMARY:")
    for category, count in category_counts.items():
        print(f"  {category.value}: {count} files")


async def main():
    """Run the complete enforcement integration demo."""
    print("🚀 Starting Technical Enforcement Layer (FWK-003) Integration Demo...")
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Basic enforcement functionality
        await demo_basic_enforcement()
        
        # Detailed validation analysis
        await demo_detailed_validation()
        
        # File classification system
        await demo_file_classification()
        
        # Violation monitoring and reporting
        await demo_violation_monitoring()
        
        # Multi-agent orchestrator integration
        await demo_orchestrator_integration()
        
        print("\n" + "="*60)
        print("🎉 TECHNICAL ENFORCEMENT LAYER DEMO COMPLETED")
        print("="*60)
        
        # Final summary
        engine = get_enforcement_engine()
        stats = engine.get_enforcement_stats()
        
        print(f"\n🏁 FINAL ENFORCEMENT STATISTICS:")
        print(f"  Enforcement Status: {'ACTIVE' if stats['enforcement_enabled'] else 'INACTIVE'}")
        print(f"  Total Violations Detected: {stats['total_violations']}")
        print(f"  Active Alerts: {stats['active_alerts']}")
        print(f"  Critical Violations: {stats['critical_violations']}")
        
        if stats['total_violations'] > 0:
            print(f"\n⚠️  Framework integrity violations detected!")
            print(f"     The enforcement system successfully identified and blocked")
            print(f"     {stats['total_violations']} unauthorized actions, maintaining")
            print(f"     compliance with CLAUDE.md delegation constraints.")
        else:
            print(f"\n✅ Framework integrity maintained!")
            print(f"     No violations detected during demo execution.")
        
        print(f"\n🔒 Technical Enforcement Layer (FWK-003) is operational and")
        print(f"    protecting framework integrity through delegation constraint")
        print(f"    enforcement, file access control, and violation monitoring.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # Configure logging for demo
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise in demo output
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)