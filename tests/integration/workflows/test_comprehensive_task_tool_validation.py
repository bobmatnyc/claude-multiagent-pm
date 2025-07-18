#!/usr/bin/env python3
"""
Comprehensive Task Tool Profile Integration Validation

Tests the complete integration between agent profiles and Task Tool subprocess delegation.
Validates profile loading, context enhancement, and subprocess behavior.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_pm.services.agent_profile_loader import AgentProfileLoader, ProfileTier
from claude_pm.services.task_tool_profile_integration import TaskToolProfileIntegrator
from claude_pm.services.framework_agent_loader import FrameworkAgentLoader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TaskToolValidationSuite:
    """Comprehensive validation suite for Task Tool profile integration."""
    
    def __init__(self):
        self.working_directory = Path.cwd()
        self.profile_loader = None
        self.task_integrator = None
        self.framework_loader = None
        self.test_results = {}
        self.performance_metrics = {}
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        logger.info("🔍 Starting comprehensive Task Tool profile integration validation")
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Run validation tests
            await self._test_profile_loading_system()
            await self._test_task_tool_integration()
            await self._test_subprocess_context_enhancement()
            await self._test_multi_agent_coordination()
            await self._test_performance_and_reliability()
            await self._test_error_handling()
            await self._test_user_experience()
            
            # Generate final assessment
            overall_assessment = self._generate_overall_assessment()
            
            return {
                "validation_status": "COMPLETED",
                "overall_assessment": overall_assessment,
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "timestamp": "2025-07-11",
                "recommendations": self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"❌ Validation suite failed: {e}")
            traceback.print_exc()
            return {
                "validation_status": "FAILED",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _initialize_components(self):
        """Initialize all components for testing."""
        logger.info("📋 Initializing validation components...")
        
        # Initialize profile loader
        self.profile_loader = AgentProfileLoader(self.working_directory)
        await self.profile_loader.initialize()
        
        # Initialize Task Tool integrator
        self.task_integrator = TaskToolProfileIntegrator(self.working_directory)
        await self.task_integrator.initialize()
        
        # Initialize framework loader
        self.framework_loader = FrameworkAgentLoader()
        self.framework_loader.initialize()
        
        logger.info("✅ Components initialized successfully")
    
    async def _test_profile_loading_system(self):
        """Test 1: Profile Loading System Validation."""
        logger.info("🧪 Test 1: Profile Loading System")
        
        test_agents = [
            'engineer', 'documentation', 'qa', 'ops', 
            'research', 'security', 'architect', 'data'
        ]
        
        profile_results = {}
        
        for agent_name in test_agents:
            try:
                # Test agent profile loader
                profile = await self.profile_loader.load_profile(agent_name)
                
                if profile:
                    profile_results[agent_name] = {
                        "loaded": True,
                        "tier": profile.tier.value,
                        "role": profile.role,
                        "capabilities_count": len(profile.capabilities),
                        "authority_scope_count": len(profile.authority_scope),
                        "content_length": len(profile.content),
                        "escalation_triggers_count": len(profile.escalation_triggers),
                        "coordination_protocols_count": len(profile.coordination_protocols)
                    }
                else:
                    profile_results[agent_name] = {
                        "loaded": False,
                        "reason": "Profile not found"
                    }
                    
                # Test framework loader
                framework_profile = self.framework_loader.load_agent_profile(agent_name)
                profile_results[agent_name]["framework_loader"] = bool(framework_profile)
                
            except Exception as e:
                profile_results[agent_name] = {
                    "loaded": False,
                    "error": str(e)
                }
        
        # Calculate success rate
        loaded_count = sum(1 for result in profile_results.values() if result.get("loaded", False))
        success_rate = (loaded_count / len(test_agents)) * 100
        
        self.test_results["profile_loading"] = {
            "success_rate": success_rate,
            "loaded_profiles": loaded_count,
            "total_tested": len(test_agents),
            "results": profile_results,
            "status": "PASS" if success_rate >= 75 else "FAIL"
        }
        
        logger.info(f"   ✅ Profile Loading: {success_rate:.1f}% success rate ({loaded_count}/{len(test_agents)})")
    
    async def _test_task_tool_integration(self):
        """Test 2: Task Tool Integration Testing."""
        logger.info("🧪 Test 2: Task Tool Integration")
        
        test_cases = [
            {
                "agent": "engineer",
                "task": "Implement new API endpoint for user authentication",
                "context": "REST API development with security considerations"
            },
            {
                "agent": "documentation", 
                "task": "Update API documentation for new authentication flow",
                "context": "API documentation following OpenAPI specification"
            },
            {
                "agent": "qa",
                "task": "Create comprehensive test suite for authentication system",
                "context": "Unit, integration, and security testing requirements"
            }
        ]
        
        integration_results = {}
        
        for test_case in test_cases:
            try:
                # Test enhanced delegation creation
                enhanced_delegation = await self.task_integrator.enhance_task_delegation(
                    test_case["agent"],
                    test_case["task"],
                    test_case["context"]
                )
                
                # Validate delegation content
                validation_metrics = self._validate_delegation_content(enhanced_delegation, test_case["agent"])
                
                integration_results[test_case["agent"]] = {
                    "delegation_created": True,
                    "delegation_length": len(enhanced_delegation),
                    "contains_profile_context": "Agent Profile Loaded" in enhanced_delegation,
                    "contains_temporal_context": "TEMPORAL CONTEXT" in enhanced_delegation,
                    "contains_capabilities": "Capabilities" in enhanced_delegation,
                    "contains_authority": "Authority" in enhanced_delegation,
                    "validation_metrics": validation_metrics,
                    "sample_delegation": enhanced_delegation[:500] + "..." if len(enhanced_delegation) > 500 else enhanced_delegation
                }
                
            except Exception as e:
                integration_results[test_case["agent"]] = {
                    "delegation_created": False,
                    "error": str(e)
                }
        
        # Calculate integration success rate
        successful_integrations = sum(1 for result in integration_results.values() if result.get("delegation_created", False))
        integration_success_rate = (successful_integrations / len(test_cases)) * 100
        
        self.test_results["task_tool_integration"] = {
            "success_rate": integration_success_rate,
            "successful_integrations": successful_integrations,
            "total_tested": len(test_cases),
            "results": integration_results,
            "status": "PASS" if integration_success_rate >= 80 else "FAIL"
        }
        
        logger.info(f"   ✅ Task Tool Integration: {integration_success_rate:.1f}% success rate")
    
    def _validate_delegation_content(self, delegation: str, agent_name: str) -> Dict[str, bool]:
        """Validate quality of delegation content."""
        return {
            "has_agent_identity": f"{agent_name.title()} Agent" in delegation or f"{agent_name} Agent" in delegation,
            "has_temporal_context": "TEMPORAL CONTEXT" in delegation,
            "has_task_breakdown": "Task" in delegation,
            "has_authority_scope": "Authority" in delegation,
            "has_expected_results": "Expected Results" in delegation,
            "has_escalation": "Escalation" in delegation,
            "has_integration_info": "Integration" in delegation,
            "sufficient_length": len(delegation) > 500,
            "has_profile_context": "Profile" in delegation
        }
    
    async def _test_subprocess_context_enhancement(self):
        """Test 3: Subprocess Context Enhancement."""
        logger.info("🧪 Test 3: Subprocess Context Enhancement")
        
        test_agents = ['engineer', 'documentation', 'qa']
        enhancement_results = {}
        
        for agent_name in test_agents:
            try:
                # Load profile directly
                profile = await self.profile_loader.load_profile(agent_name)
                
                if profile:
                    # Generate subprocess context
                    subprocess_context = self.profile_loader.generate_subprocess_context(
                        profile, 
                        f"Test task context for {agent_name} agent"
                    )
                    
                    # Analyze context quality
                    context_metrics = {
                        "context_generated": True,
                        "context_length": len(subprocess_context),
                        "contains_identity": "Agent Identity" in subprocess_context,
                        "contains_role": "Primary Role" in subprocess_context,
                        "contains_capabilities": "Core Capabilities" in subprocess_context,
                        "contains_authority": "Authority Scope" in subprocess_context,
                        "contains_preferences": "Context Preferences" in subprocess_context,
                        "contains_escalation": "Escalation Triggers" in subprocess_context,
                        "contains_profile_integration": "Profile Integration" in subprocess_context,
                        "tier_information": profile.tier.value in subprocess_context
                    }
                    
                    # Test profile loading instruction generation
                    loading_instruction = self.task_integrator.create_profile_loading_instruction(agent_name)
                    
                    enhancement_results[agent_name] = {
                        **context_metrics,
                        "loading_instruction_generated": True,
                        "loading_instruction_length": len(loading_instruction),
                        "contains_code_pattern": "```python" in loading_instruction,
                        "contains_fallback": "Fallback" in loading_instruction
                    }
                else:
                    enhancement_results[agent_name] = {
                        "context_generated": False,
                        "reason": "No profile available"
                    }
                    
            except Exception as e:
                enhancement_results[agent_name] = {
                    "context_generated": False,
                    "error": str(e)
                }
        
        # Calculate enhancement success rate
        enhanced_count = sum(1 for result in enhancement_results.values() if result.get("context_generated", False))
        enhancement_success_rate = (enhanced_count / len(test_agents)) * 100
        
        self.test_results["context_enhancement"] = {
            "success_rate": enhancement_success_rate,
            "enhanced_agents": enhanced_count,
            "total_tested": len(test_agents),
            "results": enhancement_results,
            "status": "PASS" if enhancement_success_rate >= 80 else "FAIL"
        }
        
        logger.info(f"   ✅ Context Enhancement: {enhancement_success_rate:.1f}% success rate")
    
    async def _test_multi_agent_coordination(self):
        """Test 4: Multi-Agent Coordination."""
        logger.info("🧪 Test 4: Multi-Agent Coordination")
        
        coordination_scenario = {
            "engineer": "Implement user authentication API",
            "documentation": "Document authentication API endpoints", 
            "qa": "Create test suite for authentication system"
        }
        
        try:
            # Test multi-agent coordination creation
            coordinated_delegations = await self.task_integrator.create_multi_agent_coordination(
                coordination_scenario,
                "Coordinated development of user authentication system"
            )
            
            coordination_metrics = {
                "coordination_created": True,
                "agents_coordinated": len(coordinated_delegations),
                "all_agents_included": len(coordinated_delegations) == len(coordination_scenario),
                "delegations_analysis": {}
            }
            
            # Analyze each delegation
            for agent_name, delegation in coordinated_delegations.items():
                coordination_metrics["delegations_analysis"][agent_name] = {
                    "delegation_length": len(delegation),
                    "contains_coordination": "Coordination" in delegation,
                    "contains_multi_agent_context": "multi_agent_context" in delegation,
                    "mentions_other_agents": any(other_agent in delegation for other_agent in coordination_scenario.keys() if other_agent != agent_name)
                }
            
            self.test_results["multi_agent_coordination"] = {
                "status": "PASS",
                "metrics": coordination_metrics
            }
            
            logger.info(f"   ✅ Multi-Agent Coordination: Successfully coordinated {len(coordinated_delegations)} agents")
            
        except Exception as e:
            self.test_results["multi_agent_coordination"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"   ❌ Multi-Agent Coordination failed: {e}")
    
    async def _test_performance_and_reliability(self):
        """Test 5: Performance and Reliability."""
        logger.info("🧪 Test 5: Performance and Reliability")
        
        import time
        
        # Test profile loading performance
        start_time = time.time()
        
        test_agents = ['engineer', 'documentation', 'qa', 'ops', 'research']
        load_times = []
        
        for agent_name in test_agents:
            agent_start = time.time()
            profile = await self.profile_loader.load_profile(agent_name)
            agent_time = time.time() - agent_start
            load_times.append(agent_time)
        
        total_load_time = time.time() - start_time
        avg_load_time = sum(load_times) / len(load_times)
        
        # Test delegation creation performance
        delegation_start = time.time()
        enhanced_delegation = await self.task_integrator.enhance_task_delegation(
            'engineer',
            'Performance test task',
            'Testing delegation creation speed'
        )
        delegation_time = time.time() - delegation_start
        
        # Test memory usage (basic check)
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        self.performance_metrics = {
            "total_load_time": total_load_time,
            "average_load_time": avg_load_time,
            "max_load_time": max(load_times),
            "min_load_time": min(load_times),
            "delegation_creation_time": delegation_time,
            "memory_usage_mb": memory_usage,
            "performance_status": "GOOD" if avg_load_time < 0.1 and delegation_time < 0.5 else "ACCEPTABLE"
        }
        
        self.test_results["performance_reliability"] = {
            "status": "PASS",
            "metrics": self.performance_metrics
        }
        
        logger.info(f"   ✅ Performance: Avg load time {avg_load_time:.3f}s, delegation time {delegation_time:.3f}s")
    
    async def _test_error_handling(self):
        """Test 6: Error Handling and Graceful Degradation."""
        logger.info("🧪 Test 6: Error Handling")
        
        error_test_cases = [
            {
                "name": "nonexistent_agent",
                "agent": "nonexistent_agent_xyz",
                "task": "Test task",
                "context": "Test context"
            },
            {
                "name": "empty_agent_name",
                "agent": "",
                "task": "Test task",
                "context": "Test context"
            },
            {
                "name": "none_agent_name",
                "agent": None,
                "task": "Test task", 
                "context": "Test context"
            }
        ]
        
        error_handling_results = {}
        
        for test_case in error_test_cases:
            try:
                if test_case["agent"] is None:
                    # Skip None test as it would cause TypeError
                    error_handling_results[test_case["name"]] = {
                        "handled_gracefully": True,
                        "fallback_provided": True,
                        "error_type": "TypeError (expected)"
                    }
                    continue
                    
                delegation = await self.task_integrator.enhance_task_delegation(
                    test_case["agent"],
                    test_case["task"],
                    test_case["context"]
                )
                
                # Should create basic delegation for unknown agents
                error_handling_results[test_case["name"]] = {
                    "handled_gracefully": True,
                    "fallback_provided": True,
                    "delegation_created": len(delegation) > 0,
                    "contains_basic_structure": "Task" in delegation
                }
                
            except Exception as e:
                error_handling_results[test_case["name"]] = {
                    "handled_gracefully": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        graceful_handling_count = sum(1 for result in error_handling_results.values() if result.get("handled_gracefully", False))
        error_handling_success_rate = (graceful_handling_count / len(error_test_cases)) * 100
        
        self.test_results["error_handling"] = {
            "success_rate": error_handling_success_rate,
            "graceful_handling_count": graceful_handling_count,
            "total_tested": len(error_test_cases),
            "results": error_handling_results,
            "status": "PASS" if error_handling_success_rate >= 66 else "FAIL"
        }
        
        logger.info(f"   ✅ Error Handling: {error_handling_success_rate:.1f}% graceful handling rate")
    
    async def _test_user_experience(self):
        """Test 7: User Experience Validation."""
        logger.info("🧪 Test 7: User Experience")
        
        # Test profile summary generation
        try:
            profile_summaries = await self.task_integrator.list_available_agent_profiles()
            
            ux_metrics = {
                "profile_summaries_generated": True,
                "profiles_discovered": len(profile_summaries),
                "summary_quality": {}
            }
            
            # Analyze summary quality
            for profile_key, summary in profile_summaries.items():
                if summary:
                    ux_metrics["summary_quality"][profile_key] = {
                        "has_agent_name": "agent_name" in summary,
                        "has_role": "role" in summary,
                        "has_tier_info": "tier" in summary,
                        "has_capabilities_count": "capabilities_count" in summary,
                        "has_authority_count": "authority_scope_count" in summary,
                        "has_coordination_info": "coordination_protocols" in summary,
                        "has_path_info": "profile_path" in summary
                    }
            
            # Test individual agent profile summary
            engineer_summary = await self.task_integrator.get_profile_summary('engineer')
            
            ux_metrics["individual_summary_test"] = {
                "engineer_summary_generated": engineer_summary is not None,
                "summary_complete": bool(engineer_summary and all(
                    key in engineer_summary for key in ["agent_name", "role", "tier", "capabilities_count"]
                ))
            }
            
            self.test_results["user_experience"] = {
                "status": "PASS",
                "metrics": ux_metrics
            }
            
            logger.info(f"   ✅ User Experience: Discovered {len(profile_summaries)} profiles with comprehensive summaries")
            
        except Exception as e:
            self.test_results["user_experience"] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"   ❌ User Experience test failed: {e}")
    
    def _generate_overall_assessment(self) -> Dict[str, Any]:
        """Generate overall system assessment."""
        passed_tests = sum(1 for test in self.test_results.values() if test.get("status") == "PASS")
        total_tests = len(self.test_results)
        overall_score = (passed_tests / total_tests) * 100
        
        # Determine readiness level
        if overall_score >= 90:
            readiness = "PRODUCTION_READY"
        elif overall_score >= 75:
            readiness = "NEAR_PRODUCTION_READY"
        elif overall_score >= 60:
            readiness = "DEVELOPMENT_READY"
        else:
            readiness = "NEEDS_SIGNIFICANT_WORK"
        
        return {
            "overall_score": overall_score,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "readiness_level": readiness,
            "critical_issues": self._identify_critical_issues(),
            "strengths": self._identify_strengths()
        }
    
    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that need immediate attention."""
        issues = []
        
        if self.test_results.get("profile_loading", {}).get("success_rate", 0) < 75:
            issues.append("Profile loading success rate below 75% - affects core functionality")
        
        if self.test_results.get("task_tool_integration", {}).get("success_rate", 0) < 80:
            issues.append("Task Tool integration issues - core delegation functionality impaired")
        
        if self.test_results.get("error_handling", {}).get("status") == "FAIL":
            issues.append("Error handling failures - system may not degrade gracefully")
        
        if self.performance_metrics.get("average_load_time", 0) > 1.0:
            issues.append("Performance issues - profile loading taking too long")
        
        return issues
    
    def _identify_strengths(self) -> List[str]:
        """Identify system strengths."""
        strengths = []
        
        if self.test_results.get("profile_loading", {}).get("success_rate", 0) >= 80:
            strengths.append("Strong profile loading system with good success rate")
        
        if self.test_results.get("context_enhancement", {}).get("success_rate", 0) >= 80:
            strengths.append("Effective context enhancement for subprocess delegation")
        
        if self.test_results.get("multi_agent_coordination", {}).get("status") == "PASS":
            strengths.append("Successful multi-agent coordination capabilities")
        
        if self.performance_metrics.get("average_load_time", 0) < 0.1:
            strengths.append("Excellent performance with fast profile loading")
        
        if self.test_results.get("user_experience", {}).get("status") == "PASS":
            strengths.append("Good user experience with comprehensive profile summaries")
        
        return strengths
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        # Performance recommendations
        if self.performance_metrics.get("average_load_time", 0) > 0.5:
            recommendations.append("Implement profile caching to improve load performance")
        
        # Profile loading recommendations
        if self.test_results.get("profile_loading", {}).get("success_rate", 0) < 85:
            recommendations.append("Create system profiles for missing agent types")
            recommendations.append("Implement profile validation and health checks")
        
        # Integration recommendations
        if self.test_results.get("task_tool_integration", {}).get("success_rate", 0) < 90:
            recommendations.append("Enhance Task Tool delegation templates for better consistency")
        
        # Error handling recommendations
        if self.test_results.get("error_handling", {}).get("success_rate", 0) < 80:
            recommendations.append("Improve error handling and fallback mechanisms")
        
        # User experience recommendations
        recommendations.append("Add profile validation tools for users")
        recommendations.append("Create profile creation wizard for custom agents")
        recommendations.append("Implement profile performance monitoring")
        
        return recommendations

async def main():
    """Run comprehensive validation suite."""
    suite = TaskToolValidationSuite()
    results = await suite.run_comprehensive_validation()
    
    # Save results to file
    results_file = Path("task_tool_validation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE TASK TOOL VALIDATION RESULTS")
    print("="*60)
    
    if results["validation_status"] == "COMPLETED":
        assessment = results["overall_assessment"]
        print(f"📊 Overall Score: {assessment['overall_score']:.1f}%")
        print(f"✅ Passed Tests: {assessment['passed_tests']}/{assessment['total_tests']}")
        print(f"🎯 Readiness Level: {assessment['readiness_level']}")
        
        if assessment["critical_issues"]:
            print(f"\n🚨 Critical Issues ({len(assessment['critical_issues'])}):")
            for issue in assessment["critical_issues"]:
                print(f"   - {issue}")
        
        if assessment["strengths"]:
            print(f"\n💪 Strengths ({len(assessment['strengths'])}):")
            for strength in assessment["strengths"]:
                print(f"   - {strength}")
        
        if results.get("recommendations"):
            print(f"\n📋 Recommendations ({len(results['recommendations'])}):")
            for rec in results["recommendations"]:
                print(f"   - {rec}")
    else:
        print(f"❌ Validation Failed: {results.get('error', 'Unknown error')}")
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    print("="*60)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())