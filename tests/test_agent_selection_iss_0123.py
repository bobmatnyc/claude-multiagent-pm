#!/usr/bin/env python3
"""
Test Suite for ISS-0123: Agent Selection Bug Fix
===============================================

This test suite validates that the agent selection improvements work correctly
for all 17+ test scenarios. It tests the AgentKeywordParser and the full
orchestration flow through BackwardsCompatibleOrchestrator.

Test Categories:
1. Core agent selection via keywords
2. Explicit @agent_name syntax
3. Agent hierarchy precedence
4. Fuzzy matching capabilities
5. Performance metrics
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.core.agent_keyword_parser import AgentKeywordParser
from claude_pm.orchestration.backwards_compatible_orchestrator import (
    BackwardsCompatibleOrchestrator,
    OrchestrationMode
)
from claude_pm.services.agent_registry_sync import AgentRegistry
from claude_pm.services.shared_prompt_cache import SharedPromptCache


class AgentSelectionTester:
    """Test harness for agent selection validation."""
    
    def __init__(self):
        self.parser = AgentKeywordParser()
        self.orchestrator = None
        self.registry = None
        self.results = []
        self.start_time = None
        
    async def setup(self):
        """Initialize test environment."""
        print("Setting up test environment...")
        
        # Initialize orchestrator with LOCAL mode forced
        self.orchestrator = BackwardsCompatibleOrchestrator(
            force_mode=OrchestrationMode.LOCAL
        )
        
        # Initialize agent registry
        cache = SharedPromptCache.get_instance()
        self.registry = AgentRegistry(cache_service=cache)
        
        # Discover available agents
        available_agents = self.registry.discover_agents()
        print(f"Discovered {len(available_agents)} agents in registry")
        
        self.start_time = time.time()
        
    def test_keyword_parsing(self, description: str, expected_agent: str) -> Dict:
        """Test keyword parser directly."""
        start = time.perf_counter()
        detected_agent = self.parser.parse_task_description(description)
        duration = (time.perf_counter() - start) * 1000
        
        success = detected_agent == expected_agent
        
        return {
            "test": "keyword_parsing",
            "description": description,
            "expected": expected_agent,
            "detected": detected_agent,
            "success": success,
            "duration_ms": duration,
            "suggestions": self.parser.suggest_agent_type(description)
        }
    
    async def test_orchestration_selection(self, description: str, expected_agent: str) -> Dict:
        """Test full orchestration agent selection."""
        start = time.perf_counter()
        
        # Test with generic agent type to force keyword detection
        result, return_code = await self.orchestrator.delegate_to_agent(
            agent_type="agent",  # Generic type to trigger keyword parsing
            task_description=description,
            requirements=["Test requirement"],
            deliverables=["Test deliverable"]
        )
        
        duration = (time.perf_counter() - start) * 1000
        
        # Extract selected agent from subprocess info
        selected_agent = None
        if isinstance(result, dict) and "subprocess_info" in result:
            selected_agent = result["subprocess_info"].get("agent_type")
        
        success = selected_agent == expected_agent
        
        # Extract performance metrics
        local_orch = result.get("local_orchestration", {}) if isinstance(result, dict) else {}
        
        return {
            "test": "orchestration_selection",
            "description": description,
            "expected": expected_agent,
            "selected": selected_agent,
            "success": success,
            "duration_ms": duration,
            "return_code": return_code,
            "agent_tier": local_orch.get("agent_tier"),
            "context_filtering_ms": local_orch.get("context_filtering_ms", 0),
            "token_reduction_percent": local_orch.get("token_reduction_percent", 0)
        }
    
    async def run_all_tests(self) -> Dict:
        """Run all 17+ test scenarios."""
        print("\n" + "="*70)
        print("ISS-0123: Agent Selection Test Suite")
        print("="*70)
        
        # Define test scenarios
        test_scenarios = [
            # Core agent keyword tests
            ("Update the API documentation", "documentation"),
            ("Create a new ticket for performance issues", "ticketing"),
            ("Implement user authentication with JWT", "engineer"),
            ("Run regression tests on the payment module", "qa"),
            ("Scan for security vulnerabilities in dependencies", "security"),
            ("Investigate best practices for microservices", "research"),
            ("Set up PostgreSQL database schema", "data_engineer"),
            ("Deploy application to production server", "ops"),
            ("Create new feature branch for ISS-123", "version_control"),
            
            # Explicit @agent_name syntax tests
            ("@pm_agent Update project timeline and milestones", "pm_agent"),
            ("@security Perform penetration testing", "security"),
            ("@engineer Fix the memory leak issue", "engineer"),
            
            # Fuzzy matching tests
            ("implmnt new payment gateway", "engineer"),  # Typo: implmnt
            ("reserch ML algorithms", "research"),  # Typo: reserch
            ("documnt the new API endpoints", "documentation"),  # Typo: documnt
            
            # Multi-keyword tests
            ("Write unit tests and update test documentation", "qa"),  # Should match QA
            ("Research database optimization and implement caching", "research"),  # Mixed keywords
        ]
        
        results = {
            "total_tests": len(test_scenarios) * 2,  # keyword + orchestration
            "passed": 0,
            "failed": 0,
            "test_results": [],
            "performance_metrics": {},
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None
        }
        
        # Run keyword parsing tests
        print("\n1. Testing Keyword Parser")
        print("-" * 40)
        
        for description, expected in test_scenarios:
            result = self.test_keyword_parsing(description, expected)
            results["test_results"].append(result)
            
            if result["success"]:
                results["passed"] += 1
                status = "✅ PASS"
            else:
                results["failed"] += 1
                status = "❌ FAIL"
            
            print(f"{status} | {description[:40]:40} | Expected: {expected:15} | Got: {result['detected'] or 'None':15} | {result['duration_ms']:.2f}ms")
        
        # Run orchestration tests
        print("\n2. Testing Full Orchestration Flow")
        print("-" * 40)
        
        for description, expected in test_scenarios:
            result = await self.test_orchestration_selection(description, expected)
            results["test_results"].append(result)
            
            if result["success"]:
                results["passed"] += 1
                status = "✅ PASS"
            else:
                results["failed"] += 1
                status = "❌ FAIL"
            
            tier_info = f"({result['agent_tier']})" if result.get('agent_tier') else ""
            print(f"{status} | {description[:40]:40} | Expected: {expected:15} | Got: {result['selected'] or 'None':15} {tier_info} | {result['duration_ms']:.2f}ms")
        
        # Test agent hierarchy
        print("\n3. Testing Agent Hierarchy Precedence")
        print("-" * 40)
        
        # Check registry for agents at different tiers
        all_agents = self.registry.discover_agents()
        agents_by_tier = {"project": [], "user": [], "system": []}
        
        for agent_name, metadata in all_agents.items():
            tier = metadata.tier if hasattr(metadata, 'tier') else 'unknown'
            if tier in agents_by_tier:
                agents_by_tier[tier].append(metadata.type)
        
        print(f"Project-level agents: {len(agents_by_tier['project'])}")
        print(f"User-level agents: {len(agents_by_tier['user'])}")
        print(f"System-level agents: {len(agents_by_tier['system'])}")
        
        # Calculate performance metrics
        end_time = time.time()
        duration = end_time - self.start_time
        
        results["end_time"] = datetime.now().isoformat()
        results["duration_seconds"] = duration
        
        # Calculate average performance metrics
        keyword_tests = [r for r in results["test_results"] if r["test"] == "keyword_parsing"]
        orch_tests = [r for r in results["test_results"] if r["test"] == "orchestration_selection"]
        
        results["performance_metrics"] = {
            "avg_keyword_parsing_ms": sum(t["duration_ms"] for t in keyword_tests) / len(keyword_tests) if keyword_tests else 0,
            "avg_orchestration_ms": sum(t["duration_ms"] for t in orch_tests) / len(orch_tests) if orch_tests else 0,
            "avg_context_filtering_ms": sum(t.get("context_filtering_ms", 0) for t in orch_tests) / len(orch_tests) if orch_tests else 0,
            "avg_token_reduction_percent": sum(t.get("token_reduction_percent", 0) for t in orch_tests) / len(orch_tests) if orch_tests else 0,
            "agents_by_tier": agents_by_tier
        }
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']} ({results['passed']/results['total_tests']*100:.1f}%)")
        print(f"Failed: {results['failed']} ({results['failed']/results['total_tests']*100:.1f}%)")
        print(f"Duration: {duration:.2f} seconds")
        print(f"\nPerformance Metrics:")
        print(f"  - Avg Keyword Parsing: {results['performance_metrics']['avg_keyword_parsing_ms']:.2f}ms")
        print(f"  - Avg Orchestration: {results['performance_metrics']['avg_orchestration_ms']:.2f}ms")
        print(f"  - Avg Context Filtering: {results['performance_metrics']['avg_context_filtering_ms']:.2f}ms")
        print(f"  - Avg Token Reduction: {results['performance_metrics']['avg_token_reduction_percent']:.1f}%")
        
        # Get orchestrator metrics
        orch_metrics = self.orchestrator.get_orchestration_metrics()
        if orch_metrics["total_orchestrations"] > 0:
            print(f"\nOrchestrator Statistics:")
            print(f"  - Total Orchestrations: {orch_metrics['total_orchestrations']}")
            print(f"  - Success Rate: {orch_metrics['success_rate']:.1f}%")
            print(f"  - Local Mode Used: {orch_metrics['local_orchestrations']}")
            print(f"  - Subprocess Mode Used: {orch_metrics['subprocess_orchestrations']}")
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate detailed test report."""
        report = []
        report.append("# ISS-0123: Agent Selection Test Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"Test Duration: {results['duration_seconds']:.2f} seconds")
        report.append(f"\n## Summary")
        report.append(f"- Total Tests: {results['total_tests']}")
        report.append(f"- Passed: {results['passed']} ({results['passed']/results['total_tests']*100:.1f}%)")
        report.append(f"- Failed: {results['failed']}")
        
        report.append(f"\n## Performance Metrics")
        metrics = results['performance_metrics']
        report.append(f"- Average Keyword Parsing: {metrics['avg_keyword_parsing_ms']:.2f}ms")
        report.append(f"- Average Orchestration: {metrics['avg_orchestration_ms']:.2f}ms")
        report.append(f"- Average Context Filtering: {metrics['avg_context_filtering_ms']:.2f}ms")
        report.append(f"- Average Token Reduction: {metrics['avg_token_reduction_percent']:.1f}%")
        
        report.append(f"\n## Agent Hierarchy")
        report.append(f"- Project Agents: {len(metrics['agents_by_tier']['project'])}")
        report.append(f"- User Agents: {len(metrics['agents_by_tier']['user'])}")
        report.append(f"- System Agents: {len(metrics['agents_by_tier']['system'])}")
        
        # Failed tests details
        failed_tests = [t for t in results['test_results'] if not t['success']]
        if failed_tests:
            report.append(f"\n## Failed Tests")
            for test in failed_tests:
                report.append(f"\n### {test['description']}")
                report.append(f"- Test Type: {test['test']}")
                report.append(f"- Expected: {test['expected']}")
                report.append(f"- Got: {test.get('detected') or test.get('selected') or 'None'}")
                if test.get('suggestions'):
                    report.append(f"- Suggestions: {test['suggestions'][:3]}")
        
        return "\n".join(report)


async def main():
    """Run the test suite."""
    tester = AgentSelectionTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run tests
        results = await tester.run_all_tests()
        
        # Generate report
        report = tester.generate_report(results)
        
        # Save report
        report_path = Path(__file__).parent / "test_agent_selection_report.md"
        report_path.write_text(report)
        print(f"\n✅ Test report saved to: {report_path}")
        
        # Update ticket with results
        success_rate = results['passed'] / results['total_tests'] * 100
        print(f"\n📋 ISS-0123 Update:")
        print(f"[QA Agent] Test results: {results['passed']}/{results['total_tests']} scenarios passing ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("✅ Target success rate (>90%) achieved!")
        else:
            print(f"⚠️  Success rate {success_rate:.1f}% is below target (90%)")
        
        # Return exit code based on success
        return 0 if results['failed'] == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)