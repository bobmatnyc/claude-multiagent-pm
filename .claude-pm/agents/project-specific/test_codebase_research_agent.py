#!/usr/bin/env python3
"""
Integration Test for Codebase Research Agent
===========================================

Comprehensive test suite for the Codebase Research Agent to verify:
- Agent initialization and cleanup
- All core operations functionality
- Performance characteristics
- Knowledge accuracy and coverage
- Integration with framework patterns
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, Any

# Add project paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from codebase_research_agent import CodebaseResearchAgent


class CodebaseResearchAgentTester:
    """Comprehensive test suite for Codebase Research Agent."""
    
    def __init__(self):
        self.agent = None
        self.test_results = []
        self.performance_metrics = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite."""
        print("🧪 Starting Codebase Research Agent Integration Tests")
        print("=" * 60)
        
        try:
            # Initialize agent
            await self._test_agent_initialization()
            
            # Test core operations
            await self._test_codebase_question_answering()
            await self._test_architecture_analysis()
            await self._test_business_logic_explanation()
            await self._test_implementation_guidance()
            await self._test_pattern_research()
            
            # Test execute_operation interface
            await self._test_execute_operation_interface()
            
            # Test performance characteristics
            await self._test_performance_characteristics()
            
            # Test knowledge coverage
            await self._test_knowledge_coverage()
            
            # Test agent status and info
            await self._test_agent_status_and_info()
            
            # Cleanup
            await self._test_agent_cleanup()
            
            return self._generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            if self.agent:
                await self.agent._cleanup()
            return {"success": False, "error": str(e)}
    
    async def _test_agent_initialization(self):
        """Test agent initialization."""
        print("\n📋 Testing Agent Initialization...")
        
        start_time = time.time()
        self.agent = CodebaseResearchAgent()
        await self.agent._initialize()
        init_time = time.time() - start_time
        
        self.performance_metrics["initialization_time"] = init_time
        
        assert self.agent.running, "Agent should be running after initialization"
        assert self.agent.agent_type == "research", "Agent type should be 'research'"
        assert self.agent.agent_tier == "project", "Agent tier should be 'project'"
        assert len(self.agent.specializations) == 5, "Agent should have 5 specializations"
        assert "codebase" in self.agent.specializations, "Should have 'codebase' specialization"
        
        self.test_results.append({
            "test": "agent_initialization",
            "success": True,
            "init_time": init_time,
            "details": f"Initialized in {init_time:.3f}s"
        })
        
        print(f"✅ Agent initialized successfully in {init_time:.3f}s")
    
    async def _test_codebase_question_answering(self):
        """Test codebase question answering functionality."""
        print("\n📋 Testing Codebase Question Answering...")
        
        test_questions = [
            ("What is the agent hierarchy in Claude PM Framework?", "agent_hierarchy"),
            ("How does the framework architecture work?", "architecture"),
            ("What are the core services in the framework?", "services"),
            ("How does the push workflow operate?", "workflows"),
            ("What are the performance optimization strategies?", "performance"),
            ("What are the framework protection mechanisms?", "deployment")
        ]
        
        question_results = []
        total_time = 0
        
        for question, expected_category in test_questions:
            start_time = time.time()
            result = await self.agent.async_answer_codebase_question(question)
            query_time = time.time() - start_time
            total_time += query_time
            
            assert result["category"] == expected_category, f"Expected category {expected_category}, got {result['category']}"
            
            # Check for insights in various possible keys
            insights_found = False
            insights_count = 0
            
            insight_keys = [
                "key_insights", "core_components", "key_workflows", "key_optimizations", 
                "critical_protections", "key_integrations", "critical_services",
                "architectural_patterns", "implementation_patterns", "optimization_patterns",
                "core_patterns", "business_logic", "delegation_patterns"
            ]
            
            for key in insight_keys:
                if key in result and isinstance(result[key], (list, dict)) and len(result[key]) > 0:
                    insights_found = True
                    insights_count = len(result[key]) if isinstance(result[key], list) else len(str(result[key]))
                    break
            
            assert insights_found, f"Result should contain insights in one of the expected keys. Available keys: {list(result.keys())}"
            
            question_results.append({
                "question": question,
                "category": result["category"],
                "query_time": query_time,
                "insights_count": insights_count
            })
        
        avg_query_time = total_time / len(test_questions)
        self.performance_metrics["avg_question_time"] = avg_query_time
        
        self.test_results.append({
            "test": "codebase_question_answering",
            "success": True,
            "questions_tested": len(test_questions),
            "avg_query_time": avg_query_time,
            "details": question_results
        })
        
        print(f"✅ Question answering tested: {len(test_questions)} questions, avg {avg_query_time:.3f}s")
    
    async def _test_architecture_analysis(self):
        """Test architecture analysis functionality."""
        print("\n📋 Testing Architecture Analysis...")
        
        test_cases = [
            ("agent", "detailed"),
            ("service", "comprehensive"),
            (None, "overview"),  # Full architecture analysis
        ]
        
        analysis_results = []
        
        for component, depth in test_cases:
            start_time = time.time()
            result = await self.agent.async_analyze_architecture(component, depth)
            analysis_time = time.time() - start_time
            
            assert "component" in result, "Result should contain component info"
            assert result["analysis_depth"] == depth, f"Depth should be {depth}"
            
            analysis_results.append({
                "component": component or "full_architecture",
                "depth": depth,
                "analysis_time": analysis_time,
                "component_analyzed": result["component"]
            })
        
        self.test_results.append({
            "test": "architecture_analysis",
            "success": True,
            "analyses_performed": len(test_cases),
            "details": analysis_results
        })
        
        print(f"✅ Architecture analysis tested: {len(test_cases)} analyses")
    
    async def _test_business_logic_explanation(self):
        """Test business logic explanation functionality."""
        print("\n📋 Testing Business Logic Explanation...")
        
        test_workflows = [
            ("startup", "comprehensive"),
            ("push", "detailed"),
            (None, "summary"),  # All workflows
        ]
        
        logic_results = []
        
        for workflow, detail_level in test_workflows:
            start_time = time.time()
            result = await self.agent.async_explain_business_logic(workflow, detail_level)
            explanation_time = time.time() - start_time
            
            assert "detail_level" in result, "Result should contain detail level"
            assert result["detail_level"] == detail_level, f"Detail level should be {detail_level}"
            
            logic_results.append({
                "workflow": workflow or "all_workflows",
                "detail_level": detail_level,
                "explanation_time": explanation_time,
                "scope": result.get("scope", result.get("workflow", "unknown"))
            })
        
        self.test_results.append({
            "test": "business_logic_explanation",
            "success": True,
            "workflows_explained": len(test_workflows),
            "details": logic_results
        })
        
        print(f"✅ Business logic explanation tested: {len(test_workflows)} workflows")
    
    async def _test_implementation_guidance(self):
        """Test implementation guidance functionality."""
        print("\n📋 Testing Implementation Guidance...")
        
        test_tasks = [
            "create new agent",
            "implement new service",
            "optimize performance", 
            "setup workflow",
            "general framework task"
        ]
        
        guidance_results = []
        
        for task in test_tasks:
            start_time = time.time()
            result = await self.agent.async_guide_implementation(task)
            guidance_time = time.time() - start_time
            
            assert "guidance_type" in result, "Result should contain guidance type"
            # Check for steps/guidelines in various possible keys
            steps_found = False
            steps_count = 0
            
            step_keys = ["implementation_steps", "implementation_guidelines", "best_practices", "critical_requirements"]
            for key in step_keys:
                if key in result and isinstance(result[key], list) and len(result[key]) > 0:
                    steps_found = True
                    steps_count = len(result[key])
                    break
            
            assert steps_found, f"Result should contain steps/guidelines. Available keys: {list(result.keys())}"
            
            guidance_results.append({
                "task": task,
                "guidance_type": result["guidance_type"],
                "guidance_time": guidance_time,
                "steps_count": steps_count
            })
        
        self.test_results.append({
            "test": "implementation_guidance",
            "success": True,
            "tasks_guided": len(test_tasks),
            "details": guidance_results
        })
        
        print(f"✅ Implementation guidance tested: {len(test_tasks)} tasks")
    
    async def _test_pattern_research(self):
        """Test pattern research functionality."""
        print("\n📋 Testing Pattern Research...")
        
        test_patterns = [
            ("agent", "comprehensive"),
            ("service", "focused"),
            ("workflow", "comprehensive"),
            ("performance", "exhaustive"),
            ("all", "comprehensive")  # All patterns
        ]
        
        pattern_results = []
        
        for pattern_type, scope in test_patterns:
            start_time = time.time()
            result = await self.agent.async_research_patterns(pattern_type, scope)
            research_time = time.time() - start_time
            
            assert "pattern_type" in result, "Result should contain pattern type"
            assert result["research_scope"] == scope, f"Scope should be {scope}"
            
            pattern_results.append({
                "pattern_type": pattern_type,
                "scope": scope,
                "research_time": research_time,
                "patterns_found": result["pattern_type"]
            })
        
        self.test_results.append({
            "test": "pattern_research",
            "success": True,
            "patterns_researched": len(test_patterns),
            "details": pattern_results
        })
        
        print(f"✅ Pattern research tested: {len(test_patterns)} pattern types")
    
    async def _test_execute_operation_interface(self):
        """Test the general execute_operation interface."""
        print("\n📋 Testing Execute Operation Interface...")
        
        test_operations = [
            ("answer_codebase_question", {"question": "What is the framework version?"}),
            ("analyze_architecture", {"component": "agent", "depth": "detailed"}),
            ("explain_business_logic", {"workflow": "startup"}),
            ("guide_implementation", {"task": "create agent"}),
            ("research_patterns", {"pattern_type": "agent", "scope": "focused"}),
            ("unknown_operation", {"param": "test"})  # Test error handling
        ]
        
        operation_results = []
        
        for operation, kwargs in test_operations:
            start_time = time.time()
            result = await self.agent.execute_operation(operation, **kwargs)
            operation_time = time.time() - start_time
            
            assert "success" in result, "Result should contain success status"
            assert "operation" in result, "Result should contain operation name"
            assert "execution_time" in result, "Result should contain execution time"
            
            # All operations should succeed (unknown operations return helpful info)
            assert result["success"], f"Operation {operation} should succeed"
            
            # Unknown operation should return available operations
            if operation == "unknown_operation":
                assert "result" in result, "Unknown operation should return result info"
                assert "available_operations" in result["result"], "Should list available operations"
            
            operation_results.append({
                "operation": operation,
                "success": result["success"],
                "execution_time": operation_time,
                "reported_time": result["execution_time"]
            })
        
        self.test_results.append({
            "test": "execute_operation_interface",
            "success": True,
            "operations_tested": len(test_operations),
            "details": operation_results
        })
        
        print(f"✅ Execute operation interface tested: {len(test_operations)} operations")
    
    async def _test_performance_characteristics(self):
        """Test performance characteristics."""
        print("\n📋 Testing Performance Characteristics...")
        
        # Test repeated queries for cache performance
        repeated_queries = []
        cache_test_question = "What is the agent hierarchy?"
        
        for i in range(10):
            start_time = time.time()
            await self.agent.async_answer_codebase_question(cache_test_question)
            query_time = time.time() - start_time
            repeated_queries.append(query_time)
        
        avg_repeated_time = sum(repeated_queries) / len(repeated_queries)
        
        # Test concurrent operations
        concurrent_start = time.time()
        concurrent_tasks = [
            self.agent.async_answer_codebase_question("Test question 1"),
            self.agent.async_analyze_architecture("agent", "detailed"),
            self.agent.async_explain_business_logic("startup"),
            self.agent.async_guide_implementation("test task"),
            self.agent.async_research_patterns("agent", "focused")
        ]
        
        await asyncio.gather(*concurrent_tasks)
        concurrent_time = time.time() - concurrent_start
        
        self.performance_metrics.update({
            "avg_repeated_query_time": avg_repeated_time,
            "concurrent_operations_time": concurrent_time,
            "concurrent_ops_count": len(concurrent_tasks)
        })
        
        # Performance assertions
        assert avg_repeated_time < 0.1, "Repeated queries should be fast (< 100ms)"
        assert concurrent_time < 1.0, "Concurrent operations should complete quickly"
        
        self.test_results.append({
            "test": "performance_characteristics",
            "success": True,
            "avg_repeated_time": avg_repeated_time,
            "concurrent_time": concurrent_time,
            "details": "Performance within acceptable limits"
        })
        
        print(f"✅ Performance tested: {avg_repeated_time:.3f}s avg repeated, {concurrent_time:.3f}s concurrent")
    
    async def _test_knowledge_coverage(self):
        """Test knowledge coverage and accuracy."""
        print("\n📋 Testing Knowledge Coverage...")
        
        # Test knowledge categories
        knowledge = self.agent.FRAMEWORK_KNOWLEDGE
        
        required_categories = ["architecture", "business_logic", "deployment_patterns", "performance_optimization"]
        for category in required_categories:
            assert category in knowledge, f"Knowledge should contain {category}"
        
        # Test framework version
        assert knowledge["version"] == "0.9.0", "Framework version should be 0.9.0"
        
        # Test architecture knowledge depth
        arch = knowledge["architecture"]
        assert "core_philosophy" in arch, "Should have core philosophy"
        assert "agent_hierarchy" in arch, "Should have agent hierarchy info"
        assert "service_architecture" in arch, "Should have service architecture"
        
        # Test business logic knowledge
        business = knowledge["business_logic"]
        assert "operational_workflows" in business, "Should have operational workflows"
        assert "todowrite_integration" in business, "Should have TodoWrite integration"
        
        knowledge_size = len(str(knowledge))
        
        self.test_results.append({
            "test": "knowledge_coverage",
            "success": True,
            "knowledge_size": knowledge_size,
            "categories_count": len(knowledge),
            "framework_version": knowledge["version"],
            "details": "Comprehensive knowledge coverage verified"
        })
        
        print(f"✅ Knowledge coverage verified: {knowledge_size} chars, {len(knowledge)} categories")
    
    async def _test_agent_status_and_info(self):
        """Test agent status and info methods."""
        print("\n📋 Testing Agent Status and Info...")
        
        # Test get_agent_status
        status = await self.agent.get_agent_status()
        
        required_status_fields = [
            "agent_name", "agent_type", "agent_tier", "specializations",
            "framework_version", "running", "capabilities", "operations_count"
        ]
        
        for field in required_status_fields:
            assert field in status, f"Status should contain {field}"
        
        # Test get_agent_info
        info = self.agent.get_agent_info()
        
        required_info_sections = ["agent_metadata", "framework_info", "capabilities", "operational_info"]
        
        for section in required_info_sections:
            assert section in info, f"Info should contain {section}"
        
        self.test_results.append({
            "test": "agent_status_and_info",
            "success": True,
            "status_fields": len(status),
            "info_sections": len(info),
            "details": "Status and info methods working correctly"
        })
        
        print(f"✅ Status and info tested: {len(status)} status fields, {len(info)} info sections")
    
    async def _test_agent_cleanup(self):
        """Test agent cleanup."""
        print("\n📋 Testing Agent Cleanup...")
        
        # Agent should be running before cleanup
        assert self.agent.running, "Agent should be running before cleanup"
        
        # Perform cleanup
        await self.agent._cleanup()
        
        # Agent should not be running after cleanup
        assert not self.agent.running, "Agent should not be running after cleanup"
        
        self.test_results.append({
            "test": "agent_cleanup",
            "success": True,
            "details": "Agent cleanup completed successfully"
        })
        
        print("✅ Agent cleanup completed successfully")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 CODEBASE RESEARCH AGENT TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"📋 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {total_tests - successful_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\n⚡ Performance Metrics:")
        for metric, value in self.performance_metrics.items():
            print(f"   • {metric}: {value:.3f}s")
        
        print(f"\n🧪 Test Details:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}: {result.get('details', 'Completed')}")
        
        print("\n🎯 Agent Characteristics:")
        print(f"   • Type: research (specialized)")
        print(f"   • Tier: project (highest precedence)")
        print(f"   • Specializations: {len(self.agent.specializations)} areas")
        print(f"   • Capabilities: {len(self.agent.capabilities)} capabilities")
        print(f"   • Framework Version: {self.agent.FRAMEWORK_KNOWLEDGE['version']}")
        print(f"   • Knowledge Size: {len(str(self.agent.FRAMEWORK_KNOWLEDGE))} characters")
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("📚 Codebase Research Agent is ready for use as the FIRST PLACE TO GO for framework planning.")
        
        return {
            "success": True,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests/total_tests)*100,
            "performance_metrics": self.performance_metrics,
            "test_results": self.test_results,
            "agent_info": {
                "type": self.agent.agent_type,
                "tier": self.agent.agent_tier,
                "specializations": self.agent.specializations,
                "capabilities_count": len(self.agent.capabilities),
                "framework_version": self.agent.FRAMEWORK_KNOWLEDGE["version"],
                "knowledge_size": len(str(self.agent.FRAMEWORK_KNOWLEDGE))
            }
        }


async def main():
    """Run the complete test suite."""
    tester = CodebaseResearchAgentTester()
    
    try:
        report = await tester.run_all_tests()
        return report
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Run the test suite
    result = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if result.get("success", False) else 1
    sys.exit(exit_code)