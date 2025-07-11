#!/usr/bin/env python3
"""
Enhanced QA Agent with Browser Extension Integration
====================================================

Advanced QA agent implementation for the Claude PM Framework with browser extension
integration, memory-augmented testing, and framework CLI integration.

This agent extends the existing QA capabilities with:
- Browser extension communication and coordination
- Memory-augmented test pattern recognition using mem0AI
- Framework CLI integration with QA-specific commands
- Health monitoring integration for QA extension status
- Agent hierarchy integration following three-tier model
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from ..core.config import Config
from ..services.memory_service import MemoryService
from ..services.multi_agent_orchestrator import MultiAgentOrchestrator
from ..services.health_dashboard import HealthDashboardOrchestrator
from ..services.memory.memory_trigger_service import MemoryTriggerService
from ..services.memory.trigger_orchestrator import TriggerEvent
from ..services.memory.trigger_types import TriggerType, TriggerPriority
from ..services.memory.interfaces.models import MemoryCategory

logger = logging.getLogger(__name__)


class BrowserExtensionCommunicator:
    """Manages communication with the CMPM-QA browser extension."""
    
    def __init__(self, config: Config):
        self.config = config
        self.extension_id = config.get("qa_extension.extension_id", "cmpm-qa-extension")
        self.native_messaging_host = config.get("qa_extension.native_host", "com.claude.pm.qa")
        self.communication_timeout = config.get("qa_extension.timeout", 30)
        
    async def send_test_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send test command to browser extension."""
        try:
            # Prepare command with security headers
            secured_command = {
                "id": command.get("id", f"cmd_{int(time.time())}"),
                "type": command.get("type", "test_command"),
                "payload": command.get("payload", {}),
                "timestamp": datetime.now().isoformat(),
                "source": "enhanced_qa_agent"
            }
            
            # For now, simulate extension communication
            # In real implementation, this would use native messaging
            logger.info(f"Sending command to browser extension: {secured_command['type']}")
            
            # Simulate response
            response = {
                "id": secured_command["id"],
                "status": "success",
                "result": {
                    "tests_executed": command.get("payload", {}).get("test_count", 1),
                    "tests_passed": command.get("payload", {}).get("test_count", 1),
                    "execution_time": 1.5,
                    "screenshots": ["screenshot_1.png"],
                    "logs": ["Test completed successfully"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Browser extension communication error: {e}")
            return {
                "id": command.get("id", "unknown"),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_extension_health(self) -> Dict[str, Any]:
        """Get health status of browser extension."""
        try:
            # Simulate health check
            health_status = {
                "status": "healthy",
                "extension_version": "1.0.0",
                "browser_compatible": True,
                "native_messaging_active": True,
                "last_activity": datetime.now().isoformat(),
                "test_capabilities": ["screenshot", "interaction", "validation"],
                "connected_browsers": ["chrome"]
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Extension health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class MemoryAugmentedTesting:
    """Provides memory-augmented testing capabilities using mem0AI."""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        
    async def analyze_test_patterns(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results for patterns using memory intelligence."""
        try:
            # Prepare test data for memory analysis
            test_data = {
                "session_id": f"qa_session_{int(time.time())}",
                "test_results": test_results,
                "analysis_timestamp": datetime.now().isoformat(),
                "context": "qa_pattern_analysis"
            }
            
            # Store test results in memory for pattern recognition
            await self.memory_service.store_memory(
                text=f"QA Test Results: {len(test_results)} tests analyzed",
                metadata=test_data
            )
            
            # Analyze patterns (simplified implementation)
            patterns = {
                "success_rate": sum(1 for r in test_results if r.get("status") == "passed") / len(test_results) if test_results else 0,
                "common_failures": self._extract_failure_patterns(test_results),
                "performance_trends": self._analyze_performance_trends(test_results),
                "recommendations": self._generate_recommendations(test_results)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Memory-augmented analysis failed: {e}")
            return {"error": str(e)}
    
    def _extract_failure_patterns(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Extract common failure patterns from test results."""
        failures = [r for r in test_results if r.get("status") == "failed"]
        failure_reasons = [f.get("error", "Unknown error") for f in failures]
        
        # Simplified pattern detection
        patterns = []
        if any("timeout" in reason.lower() for reason in failure_reasons):
            patterns.append("timeout_issues")
        if any("network" in reason.lower() for reason in failure_reasons):
            patterns.append("network_connectivity")
        if any("element not found" in reason.lower() for reason in failure_reasons):
            patterns.append("ui_element_instability")
            
        return patterns
    
    def _analyze_performance_trends(self, test_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze performance trends from test results."""
        execution_times = [r.get("execution_time", 0) for r in test_results if r.get("execution_time")]
        
        if not execution_times:
            return {"average_time": 0, "trend": "stable"}
        
        avg_time = sum(execution_times) / len(execution_times)
        return {
            "average_time": avg_time,
            "max_time": max(execution_times),
            "min_time": min(execution_times),
            "trend": "improving" if avg_time < 5.0 else "degrading"
        }
    
    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate testing recommendations based on results."""
        recommendations = []
        
        failed_tests = [r for r in test_results if r.get("status") == "failed"]
        if len(failed_tests) > len(test_results) * 0.2:  # More than 20% failure rate
            recommendations.append("Investigate high failure rate - consider test stability improvements")
        
        slow_tests = [r for r in test_results if r.get("execution_time", 0) > 10.0]
        if slow_tests:
            recommendations.append("Optimize slow test execution - consider parallel execution or test optimization")
        
        if not test_results:
            recommendations.append("No test results available - ensure test execution is working properly")
        
        return recommendations


class EnhancedQAAgent:
    """
    Enhanced QA Agent with browser extension integration and memory-augmented testing.
    
    Provides comprehensive QA capabilities including:
    - Browser-based testing coordination
    - Memory-augmented test pattern recognition
    - Framework CLI integration
    - Health monitoring integration
    - Agent hierarchy coordination
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.framework_path = Path.cwd()
        
        # Initialize core services
        self.memory_service = MemoryService()
        
        # Initialize orchestrator with proper parameters
        try:
            from ..services.memory_service import ClaudePMMemory
            memory_instance = ClaudePMMemory()
            self.orchestrator = MultiAgentOrchestrator(
                base_repo_path=str(self.framework_path),
                memory=memory_instance
            )
        except Exception as e:
            logger.warning(f"Could not initialize MultiAgentOrchestrator: {e}")
            self.orchestrator = None
        
        self.health_dashboard = HealthDashboardOrchestrator()
        
        # Initialize QA-specific components
        self.browser_communicator = BrowserExtensionCommunicator(self.config)
        self.memory_testing = MemoryAugmentedTesting(self.memory_service)
        
        # QA Agent configuration
        self.agent_id = "enhanced_qa_agent"
        self.agent_version = "1.0.0"
        self.test_timeout = self.config.get("qa.test_timeout", 300)  # 5 minutes
        self.parallel_tests = self.config.get("qa.parallel_tests", True)
        
        # Memory integration
        self.memory_trigger_service: Optional[MemoryTriggerService] = None
        self.memory_enhanced = False
        
        logger.info(f"Enhanced QA Agent initialized (v{self.agent_version})")
    
    async def execute_browser_tests(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser-based tests using the extension."""
        try:
            logger.info("Starting browser-based test execution")
            
            # Prepare test command for browser extension
            test_command = {
                "type": "execute_tests",
                "payload": {
                    "test_suite": test_config.get("test_suite", "default"),
                    "test_urls": test_config.get("urls", ["http://localhost:3000"]),
                    "test_scenarios": test_config.get("scenarios", ["basic_functionality"]),
                    "screenshot_capture": test_config.get("screenshots", True),
                    "performance_metrics": test_config.get("performance", True)
                }
            }
            
            # Send command to browser extension
            extension_response = await self.browser_communicator.send_test_command(test_command)
            
            if extension_response.get("status") == "success":
                # Analyze results with memory intelligence
                test_results = [extension_response.get("result", {})]
                patterns = await self.memory_testing.analyze_test_patterns(test_results)
                
                result = {
                    "status": "success",
                    "test_results": extension_response.get("result"),
                    "pattern_analysis": patterns,
                    "execution_summary": {
                        "total_tests": test_results[0].get("tests_executed", 0),
                        "passed_tests": test_results[0].get("tests_passed", 0),
                        "execution_time": test_results[0].get("execution_time", 0),
                        "screenshots_captured": len(test_results[0].get("screenshots", []))
                    }
                }
                
                # Create memory trigger for browser testing
                await self._create_memory_trigger("browser_testing", {
                    "project_name": test_config.get("project_name", "unknown"),
                    "test_type": "browser",
                    "test_scenarios": test_config.get("scenarios", [])
                }, result)
                
                return result
            else:
                return {
                    "status": "error",
                    "error": extension_response.get("error", "Browser test execution failed"),
                    "details": extension_response
                }
                
        except Exception as e:
            logger.error(f"Browser test execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_framework_tests(self, test_type: str = "all") -> Dict[str, Any]:
        """Run framework-level tests (unit, integration, etc.)."""
        try:
            logger.info(f"Running framework tests: {test_type}")
            
            # Determine test command based on project type
            test_commands = self._get_test_commands(test_type)
            
            results = []
            for cmd_info in test_commands:
                cmd_name = cmd_info["name"]
                cmd = cmd_info["command"]
                
                logger.info(f"Executing {cmd_name}: {' '.join(cmd)}")
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.test_timeout,
                        cwd=self.framework_path
                    )
                    
                    test_result = {
                        "test_type": cmd_name,
                        "status": "passed" if result.returncode == 0 else "failed",
                        "return_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": 0  # Simplified
                    }
                    
                    results.append(test_result)
                    
                except subprocess.TimeoutExpired:
                    results.append({
                        "test_type": cmd_name,
                        "status": "timeout",
                        "error": f"Test timed out after {self.test_timeout} seconds"
                    })
                except Exception as e:
                    results.append({
                        "test_type": cmd_name,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Analyze results
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.get("status") == "passed")
            
            # Store results in memory for pattern analysis
            patterns = await self.memory_testing.analyze_test_patterns(results)
            
            result = {
                "status": "success" if passed_tests == total_tests else "partial_failure",
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests,
                    "success_rate": passed_tests / total_tests if total_tests > 0 else 0
                },
                "detailed_results": results,
                "pattern_analysis": patterns
            }
            
            # Create memory trigger for test execution
            await self._create_memory_trigger("test_execution", {
                "project_name": self.framework_path.name,
                "test_type": test_type,
                "execution_time": sum(r.get("execution_time", 0) for r in results)
            }, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Framework test execution failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_test_commands(self, test_type: str) -> List[Dict[str, Any]]:
        """Get appropriate test commands based on project type and test type."""
        commands = []
        
        # Check for different project types and their test commands
        if (self.framework_path / "package.json").exists():
            # Node.js project
            if test_type in ["all", "unit"]:
                commands.append({"name": "npm_test", "command": ["npm", "test"]})
            if test_type in ["all", "lint"]:
                commands.append({"name": "npm_lint", "command": ["npm", "run", "lint"]})
        
        if (self.framework_path / "pyproject.toml").exists() or (self.framework_path / "requirements.txt").exists():
            # Python project
            if test_type in ["all", "unit"]:
                commands.append({"name": "pytest", "command": ["python", "-m", "pytest", "-v"]})
            if test_type in ["all", "lint"]:
                commands.append({"name": "flake8", "command": ["python", "-m", "flake8", "."]})
        
        # Framework-specific tests
        if test_type in ["all", "framework"]:
            commands.append({"name": "framework_health", "command": ["python", "-m", "claude_pm.cmpm_commands", "cmpm:health"]})
        
        return commands if commands else [{"name": "echo_test", "command": ["echo", "No tests configured"]}]
    
    async def get_qa_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of QA system."""
        try:
            # Get extension health
            extension_health = await self.browser_communicator.get_extension_health()
            
            # Get memory service health
            memory_health = await self.memory_service.health_check()
            
            # Check framework test capabilities
            framework_health = {
                "test_commands_available": len(self._get_test_commands("all")) > 0,
                "test_timeout_configured": self.test_timeout > 0,
                "parallel_tests_enabled": self.parallel_tests,
                "framework_path_valid": self.framework_path.exists()
            }
            
            # Calculate overall health score
            health_components = [
                extension_health.get("status") == "healthy",
                memory_health.get("status") == "healthy",
                framework_health["test_commands_available"],
                framework_health["framework_path_valid"]
            ]
            
            health_score = sum(health_components) / len(health_components) * 100
            
            return {
                "status": "healthy" if health_score >= 75 else "degraded" if health_score >= 50 else "unhealthy",
                "health_score": health_score,
                "extension_health": extension_health,
                "memory_health": memory_health,
                "framework_health": framework_health,
                "agent_version": self.agent_version,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"QA health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def coordinate_with_agents(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate QA activities with other agents in the hierarchy."""
        try:
            logger.info(f"Coordinating QA task: {task_type}")
            
            # Use orchestrator for agent coordination if available
            if self.orchestrator:
                coordination_result = await self.orchestrator.coordinate_agents({
                    "task_type": task_type,
                    "requesting_agent": self.agent_id,
                    "context": context,
                    "qa_requirements": {
                        "test_coverage": context.get("test_coverage", 80),
                        "quality_gates": context.get("quality_gates", ["unit_tests", "linting"]),
                        "browser_testing": context.get("browser_testing", False)
                    }
                })
                return coordination_result
            else:
                # Fallback coordination without orchestrator
                logger.warning("MultiAgentOrchestrator not available, using fallback coordination")
                return {
                    "status": "partial_success",
                    "message": "QA coordination completed without full orchestrator integration",
                    "qa_requirements": {
                        "test_coverage": context.get("test_coverage", 80),
                        "quality_gates": context.get("quality_gates", ["unit_tests", "linting"]),
                        "browser_testing": context.get("browser_testing", False)
                    }
                }
            
        except Exception as e:
            logger.error(f"Agent coordination failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        try:
            report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report = f"""
# Enhanced QA Agent Test Report
Generated: {report_timestamp}
Agent Version: {self.agent_version}

## Test Execution Summary
- Status: {test_results.get('status', 'unknown')}
- Total Tests: {test_results.get('summary', {}).get('total_tests', 0)}
- Passed Tests: {test_results.get('summary', {}).get('passed_tests', 0)}
- Failed Tests: {test_results.get('summary', {}).get('failed_tests', 0)}
- Success Rate: {test_results.get('summary', {}).get('success_rate', 0):.1%}

## Pattern Analysis
"""
            
            # Add pattern analysis if available
            pattern_analysis = test_results.get('pattern_analysis', {})
            if pattern_analysis:
                report += f"- Success Rate: {pattern_analysis.get('success_rate', 0):.1%}\n"
                report += f"- Common Failures: {', '.join(pattern_analysis.get('common_failures', []))}\n"
                
                recommendations = pattern_analysis.get('recommendations', [])
                if recommendations:
                    report += "\n## Recommendations\n"
                    for i, rec in enumerate(recommendations, 1):
                        report += f"{i}. {rec}\n"
            
            # Add detailed results
            detailed_results = test_results.get('detailed_results', [])
            if detailed_results:
                report += "\n## Detailed Results\n"
                for result in detailed_results:
                    status_emoji = "✅" if result.get('status') == 'passed' else "❌"
                    report += f"{status_emoji} {result.get('test_type', 'unknown')}: {result.get('status', 'unknown')}\n"
            
            report += f"\n---\nGenerated by Enhanced QA Agent v{self.agent_version}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Test report generation failed: {e}")
            return f"Error generating test report: {str(e)}"
    
    # Memory Integration Methods
    
    def enable_memory_integration(self, memory_service: MemoryTriggerService):
        """Enable memory integration for the QA Agent."""
        self.memory_trigger_service = memory_service
        self.memory_enhanced = True
        logger.info("Enhanced QA Agent memory integration enabled")
    
    async def _create_memory_trigger(self, operation: str, context: Dict[str, Any], result: Dict[str, Any]):
        """Create memory trigger for QA operations."""
        if not self.memory_enhanced or not self.memory_trigger_service:
            return
        
        try:
            # Prepare memory content
            memory_content = self._generate_memory_content(operation, context, result)
            
            # Prepare metadata
            metadata = {
                "agent_id": self.agent_id,
                "agent_type": "qa",
                "operation": operation,
                "project_name": context.get("project_name", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "success": result.get("status") == "success"
            }
            
            # Add operation-specific metadata
            if operation == "test_execution":
                metadata.update({
                    "test_type": context.get("test_type", "unknown"),
                    "total_tests": result.get("summary", {}).get("total_tests", 0),
                    "passed_tests": result.get("summary", {}).get("passed_tests", 0),
                    "failed_tests": result.get("summary", {}).get("failed_tests", 0),
                    "success_rate": result.get("summary", {}).get("success_rate", 0)
                })
            elif operation == "browser_testing":
                metadata.update({
                    "test_results": result.get("test_results", {}),
                    "screenshots_count": result.get("execution_summary", {}).get("screenshots_captured", 0),
                    "execution_time": result.get("execution_summary", {}).get("execution_time", 0)
                })
            elif operation == "quality_validation":
                metadata.update({
                    "validation_status": result.get("status", "unknown"),
                    "quality_score": context.get("quality_score", 0)
                })
            
            # Create trigger event
            trigger_event = TriggerEvent(
                trigger_type=TriggerType.OPERATION_COMPLETION,
                priority=TriggerPriority.HIGH if operation == "test_execution" else TriggerPriority.MEDIUM,
                project_name=context.get("project_name", "unknown"),
                event_id=f"qa_agent_{operation}_{int(time.time())}",
                content=memory_content,
                category=MemoryCategory.WORKFLOW,
                tags=["qa", operation, "testing"],
                metadata=metadata,
                source="enhanced_qa_agent",
                context=context
            )
            
            # Process trigger
            orchestrator = self.memory_trigger_service.get_trigger_orchestrator()
            if orchestrator:
                await orchestrator.process_trigger(trigger_event)
                logger.info(f"Created memory trigger for QA operation: {operation}")
            
        except Exception as e:
            logger.error(f"Failed to create memory trigger for {operation}: {e}")
    
    def _generate_memory_content(self, operation: str, context: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Generate memory content for QA operations."""
        project_name = context.get("project_name", "unknown")
        
        if operation == "test_execution":
            test_type = context.get("test_type", "unknown")
            total_tests = result.get("summary", {}).get("total_tests", 0)
            passed_tests = result.get("summary", {}).get("passed_tests", 0)
            success_rate = result.get("summary", {}).get("success_rate", 0)
            return f"Test execution for {project_name}. Type: {test_type}, Results: {passed_tests}/{total_tests} passed ({success_rate:.1%})"
        
        elif operation == "browser_testing":
            test_results = result.get("test_results", {})
            screenshots_count = result.get("execution_summary", {}).get("screenshots_captured", 0)
            return f"Browser testing for {project_name}. Results: {test_results}, Screenshots: {screenshots_count}"
        
        elif operation == "quality_validation":
            validation_status = result.get("status", "unknown")
            return f"Quality validation for {project_name}. Status: {validation_status}"
        
        else:
            return f"QA operation {operation} completed for {project_name}"


# Factory function for creating QA agent instances
def create_enhanced_qa_agent(config: Optional[Config] = None) -> EnhancedQAAgent:
    """Create and configure an Enhanced QA Agent instance."""
    return EnhancedQAAgent(config)


# CLI integration function
async def execute_qa_command(command: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute QA command for CLI integration."""
    options = options or {}
    
    try:
        qa_agent = create_enhanced_qa_agent()
        
        if command == "status":
            return await qa_agent.get_qa_health_status()
        
        elif command == "test":
            test_type = options.get("type", "all")
            if options.get("browser", False):
                test_config = {
                    "test_suite": options.get("suite", "default"),
                    "urls": options.get("urls", ["http://localhost:3000"]),
                    "screenshots": options.get("screenshots", True)
                }
                return await qa_agent.execute_browser_tests(test_config)
            else:
                return await qa_agent.run_framework_tests(test_type)
        
        elif command == "results":
            # Return recent test results (simplified)
            return {
                "status": "success",
                "message": "Test results retrieved",
                "results": []
            }
        
        else:
            return {
                "status": "error",
                "error": f"Unknown QA command: {command}"
            }
            
    except Exception as e:
        logger.error(f"QA command execution failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }