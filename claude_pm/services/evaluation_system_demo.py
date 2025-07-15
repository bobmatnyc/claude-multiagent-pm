"""
Evaluation System Demo and Integration Test
==========================================

This script demonstrates the complete Mirascope evaluation system integration,
including all components working together:

- Mirascope evaluator with multiple criteria
- Correction capture and evaluation integration
- Performance optimization with caching
- Comprehensive metrics and analytics
- Monitoring and health checks
- Configuration management

This serves as both a demo and integration test for the entire system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from claude_pm.core.config import Config
from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType
from claude_pm.services.mirascope_evaluator import MirascopeEvaluator, EvaluationCriteria
from claude_pm.services.evaluation_integration import EvaluationIntegrationService
from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
from claude_pm.services.evaluation_performance import EvaluationPerformanceManager
from claude_pm.services.evaluation_monitoring import EvaluationMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvaluationSystemDemo:
    """
    Comprehensive demo of the evaluation system.
    
    Demonstrates all components working together in a realistic scenario.
    """
    
    def __init__(self):
        """Initialize demo with test configuration."""
        # Create test configuration
        self.config = Config({
            "enable_evaluation": True,
            "evaluation_provider": "auto",
            "evaluation_criteria": [
                "correctness", "relevance", "completeness", "clarity", "helpfulness"
            ],
            "evaluation_caching_enabled": True,
            "evaluation_cache_ttl_hours": 1,
            "evaluation_performance_enabled": True,
            "evaluation_monitoring_enabled": True,
            "auto_evaluate_corrections": True,
            "batch_evaluation_enabled": True,
            "evaluation_storage_path": "~/.claude-pm/training/demo"
        })
        
        # Initialize components
        self.correction_capture = None
        self.evaluator = None
        self.integration_service = None
        self.metrics_system = None
        self.performance_manager = None
        self.monitor = None
        
        # Demo data
        self.demo_agents = ["engineer", "researcher", "ops", "qa", "documentation"]
        self.demo_responses = [
            {
                "agent_type": "engineer",
                "response": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                "task": "Implement fibonacci function",
                "correction": "def fibonacci(n):\n    if n <= 1:\n        return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b",
                "correction_type": CorrectionType.TECHNICAL_CORRECTION
            },
            {
                "agent_type": "researcher", 
                "response": "Machine learning is a subset of AI that uses algorithms to learn from data.",
                "task": "Explain machine learning",
                "correction": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make predictions or decisions.",
                "correction_type": CorrectionType.CONTENT_CORRECTION
            },
            {
                "agent_type": "ops",
                "response": "docker run -d myapp",
                "task": "Deploy application with Docker",
                "correction": "docker run -d --name myapp -p 8080:8080 --restart unless-stopped myapp:latest",
                "correction_type": CorrectionType.TECHNICAL_CORRECTION
            },
            {
                "agent_type": "qa",
                "response": "The test passes.",
                "task": "Analyze test results",
                "correction": "All 47 tests pass successfully. Code coverage is 95.2%. No performance regressions detected. Ready for deployment.",
                "correction_type": CorrectionType.COMPLETENESS
            },
            {
                "agent_type": "documentation",
                "response": "This function calculates fibonacci numbers.",
                "task": "Document fibonacci function",
                "correction": "## Fibonacci Function\n\nCalculates the nth Fibonacci number using an iterative approach.\n\n**Parameters:**\n- n (int): The position in the Fibonacci sequence\n\n**Returns:**\n- int: The nth Fibonacci number\n\n**Time Complexity:** O(n)\n**Space Complexity:** O(1)",
                "correction_type": CorrectionType.FORMATTING_CORRECTION
            }
        ]
        
        # Statistics
        self.demo_start_time = None
        self.demo_stats = {
            "evaluations_completed": 0,
            "corrections_captured": 0,
            "cache_hits": 0,
            "performance_optimizations": 0,
            "alerts_triggered": 0
        }
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize all system components."""
        print("🚀 Initializing Evaluation System Components...")
        
        try:
            # Initialize correction capture
            self.correction_capture = CorrectionCapture(self.config)
            
            # Initialize evaluator
            self.evaluator = MirascopeEvaluator(self.config)
            
            # Initialize integration service
            self.integration_service = EvaluationIntegrationService(self.config)
            await self.integration_service.start_background_tasks()
            
            # Initialize metrics system
            self.metrics_system = EvaluationMetricsSystem(self.config)
            
            # Initialize performance manager
            self.performance_manager = EvaluationPerformanceManager(self.config)
            await self.performance_manager.initialize(self.evaluator)
            
            # Initialize monitoring
            self.monitor = EvaluationMonitor(self.config)
            self.monitor.register_services(
                evaluator=self.evaluator,
                integration_service=self.integration_service,
                metrics_system=self.metrics_system,
                performance_manager=self.performance_manager
            )
            await self.monitor.start_monitoring()
            
            print("✅ All components initialized successfully!")
            
            return {
                "initialized": True,
                "components": {
                    "correction_capture": self.correction_capture.enabled,
                    "evaluator": self.evaluator.enabled,
                    "integration_service": self.integration_service.enabled,
                    "metrics_system": self.metrics_system.enabled,
                    "performance_manager": self.performance_manager.enabled,
                    "monitor": self.monitor.enabled
                }
            }
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return {"initialized": False, "error": str(e)}
    
    async def run_demo_scenario(self) -> Dict[str, Any]:
        """Run comprehensive demo scenario."""
        print("\n🎯 Running Demo Scenario...")
        
        self.demo_start_time = time.time()
        
        # Phase 1: Basic evaluations
        print("\n📊 Phase 1: Basic Response Evaluations")
        await self._demo_basic_evaluations()
        
        # Phase 2: Corrections and integration
        print("\n🔄 Phase 2: Correction Capture and Integration")
        await self._demo_correction_integration()
        
        # Phase 3: Performance optimization
        print("\n⚡ Phase 3: Performance Optimization")
        await self._demo_performance_optimization()
        
        # Phase 4: Metrics and analytics
        print("\n📈 Phase 4: Metrics and Analytics")
        await self._demo_metrics_analytics()
        
        # Phase 5: Monitoring and health
        print("\n🏥 Phase 5: Monitoring and Health Checks")
        await self._demo_monitoring_health()
        
        # Phase 6: Batch processing
        print("\n🔄 Phase 6: Batch Processing")
        await self._demo_batch_processing()
        
        demo_duration = time.time() - self.demo_start_time
        
        return {
            "demo_completed": True,
            "duration_seconds": demo_duration,
            "statistics": self.demo_stats
        }
    
    async def _demo_basic_evaluations(self) -> None:
        """Demo basic evaluation functionality."""
        print("  → Evaluating agent responses...")
        
        for i, demo_data in enumerate(self.demo_responses):
            try:
                # Evaluate response
                result = await self.evaluator.evaluate_response(
                    agent_type=demo_data["agent_type"],
                    response_text=demo_data["response"],
                    context={"task_description": demo_data["task"]}
                )
                
                # Record metrics
                self.metrics_system.record_evaluation(result)
                
                # Update statistics
                self.demo_stats["evaluations_completed"] += 1
                
                print(f"    ✓ {demo_data['agent_type']}: {result.overall_score:.1f}/100")
                
            except Exception as e:
                print(f"    ✗ {demo_data['agent_type']}: Error - {e}")
        
        print(f"  → Completed {self.demo_stats['evaluations_completed']} evaluations")
    
    async def _demo_correction_integration(self) -> None:
        """Demo correction capture and integration."""
        print("  → Capturing corrections with automatic evaluation...")
        
        for demo_data in self.demo_responses:
            try:
                # Capture correction with automatic evaluation
                correction_id, evaluation_result = await self.integration_service.capture_and_evaluate_correction(
                    agent_type=demo_data["agent_type"],
                    original_response=demo_data["response"],
                    user_correction=demo_data["correction"],
                    context={"task_description": demo_data["task"]},
                    correction_type=demo_data["correction_type"],
                    subprocess_id=f"demo_subprocess_{demo_data['agent_type']}",
                    task_description=demo_data["task"],
                    severity="medium"
                )
                
                # Update statistics
                self.demo_stats["corrections_captured"] += 1
                if evaluation_result:
                    self.demo_stats["evaluations_completed"] += 1
                
                print(f"    ✓ {demo_data['agent_type']}: Correction captured and evaluated")
                
            except Exception as e:
                print(f"    ✗ {demo_data['agent_type']}: Error - {e}")
        
        print(f"  → Captured {self.demo_stats['corrections_captured']} corrections")
    
    async def _demo_performance_optimization(self) -> None:
        """Demo performance optimization features."""
        print("  → Testing performance optimization...")
        
        # Test caching by re-evaluating same responses
        cache_test_responses = self.demo_responses[:3]  # Test with first 3
        
        for demo_data in cache_test_responses:
            try:
                # First evaluation (should miss cache)
                start_time = time.time()
                result1 = await self.performance_manager.evaluate_response(
                    agent_type=demo_data["agent_type"],
                    response_text=demo_data["response"],
                    context={"task_description": demo_data["task"]}
                )
                first_time = time.time() - start_time
                
                # Second evaluation (should hit cache)
                start_time = time.time()
                result2 = await self.performance_manager.evaluate_response(
                    agent_type=demo_data["agent_type"],
                    response_text=demo_data["response"],
                    context={"task_description": demo_data["task"]}
                )
                second_time = time.time() - start_time
                
                # Check if caching improved performance
                if second_time < first_time * 0.5:  # 50% improvement
                    self.demo_stats["cache_hits"] += 1
                    print(f"    ✓ {demo_data['agent_type']}: Cache hit (performance improved by {((first_time - second_time) / first_time * 100):.1f}%)") 
                else:
                    print(f"    → {demo_data['agent_type']}: No cache performance improvement detected")
                
            except Exception as e:
                print(f"    ✗ {demo_data['agent_type']}: Performance test error - {e}")
        
        # Get performance statistics
        perf_stats = self.performance_manager.get_performance_stats()
        print(f"  → Cache hit rate: {perf_stats.get('cache_stats', {}).get('hit_rate', 0):.1f}%")
        print(f"  → Average evaluation time: {perf_stats.get('average_evaluation_time', 0):.1f}ms")
    
    async def _demo_metrics_analytics(self) -> None:
        """Demo metrics and analytics features."""
        print("  → Generating metrics and analytics...")
        
        # Get system health
        health = self.metrics_system.get_system_health()
        print(f"    → System health score: {health['health_score']:.1f}/100")
        
        # Get agent metrics
        for agent_type in self.demo_agents:
            agent_metrics = self.metrics_system.get_agent_metrics(agent_type)
            if agent_metrics['metrics']:
                print(f"    → {agent_type}: {agent_metrics['summary']}")
        
        # Get improvement recommendations
        recommendations = self.metrics_system.generate_improvement_recommendations()
        if recommendations:
            print(f"    → Generated {len(recommendations)} improvement recommendations")
            for rec in recommendations[:3]:  # Show first 3
                print(f"      • {rec.agent_type}: {rec.recommendation[:60]}...")
        
        # Generate report
        report_path = self.metrics_system.save_metrics_report()
        print(f"    → Saved metrics report: {Path(report_path).name}")
    
    async def _demo_monitoring_health(self) -> None:
        """Demo monitoring and health check features."""
        print("  → Running health checks and monitoring...")
        
        # Wait for monitoring to collect data
        await asyncio.sleep(2)
        
        # Get monitoring status
        monitoring_status = self.monitor.get_monitoring_status()
        print(f"    → Overall health: {monitoring_status['overall_health']}")
        print(f"    → Active alerts: {monitoring_status['active_alerts']}")
        
        # Get health check details
        health_details = self.monitor.get_health_check_details()
        for name, details in health_details.items():
            if details['last_result']:
                status = details['last_result'].get('status', 'unknown')
                print(f"    → {name}: {status}")
        
        # Generate monitoring report
        report_path = await self.monitor.save_monitoring_report()
        print(f"    → Saved monitoring report: {Path(report_path).name}")
    
    async def _demo_batch_processing(self) -> None:
        """Demo batch processing capabilities."""
        print("  → Testing batch processing...")
        
        # Create batch of evaluation requests
        batch_requests = []
        for i in range(10):
            demo_data = self.demo_responses[i % len(self.demo_responses)]
            batch_requests.append({
                "agent_type": demo_data["agent_type"],
                "response_text": f"{demo_data['response']} (batch item {i})",
                "context": {"task_description": f"{demo_data['task']} (batch {i})"}
            })
        
        # Process batch
        start_time = time.time()
        batch_results = []
        
        # Use performance manager for batch processing
        for request in batch_requests:
            try:
                result = await self.performance_manager.evaluate_response(
                    request["agent_type"],
                    request["response_text"],
                    request["context"]
                )
                batch_results.append(result)
            except Exception as e:
                print(f"    ✗ Batch item error: {e}")
        
        batch_time = time.time() - start_time
        
        if batch_results:
            avg_score = sum(r.overall_score for r in batch_results) / len(batch_results)
            print(f"    → Processed {len(batch_results)} items in {batch_time:.2f}s")
            print(f"    → Average score: {avg_score:.1f}/100")
            print(f"    → Throughput: {len(batch_results)/batch_time:.1f} evaluations/second")
    
    async def generate_demo_report(self) -> Dict[str, Any]:
        """Generate comprehensive demo report."""
        print("\n📋 Generating Demo Report...")
        
        # Get all component statistics
        correction_stats = self.correction_capture.get_correction_stats()
        evaluator_stats = self.evaluator.get_evaluation_statistics()
        integration_stats = self.integration_service.get_integration_statistics()
        performance_stats = self.performance_manager.get_performance_stats()
        monitoring_status = self.monitor.get_monitoring_status()
        
        # Generate comprehensive report
        report = {
            "demo_info": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": time.time() - self.demo_start_time if self.demo_start_time else 0,
                "demo_stats": self.demo_stats
            },
            "system_status": {
                "correction_capture": correction_stats,
                "evaluator": evaluator_stats,
                "integration": integration_stats,
                "performance": performance_stats,
                "monitoring": monitoring_status
            },
            "performance_analysis": {
                "average_evaluation_time": performance_stats.get("average_evaluation_time", 0),
                "cache_hit_rate": performance_stats.get("cache_stats", {}).get("hit_rate", 0),
                "evaluations_per_second": performance_stats.get("evaluations_per_second", 0),
                "system_health": monitoring_status.get("overall_health", "unknown")
            },
            "recommendations": [
                rec.to_dict() for rec in self.metrics_system.generate_improvement_recommendations()
            ]
        }
        
        # Save report
        report_path = self.config.get("evaluation_storage_path", "~/.claude-pm/training/demo")
        report_dir = Path(report_path).expanduser()
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"demo_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Demo report saved: {report_file}")
        
        return report
    
    async def shutdown_system(self) -> None:
        """Shutdown all system components."""
        print("\n🔄 Shutting down system components...")
        
        try:
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop_monitoring()
            
            # Stop performance manager
            if self.performance_manager:
                await self.performance_manager.shutdown()
            
            # Stop integration service
            if self.integration_service:
                await self.integration_service.stop_background_tasks()
            
            print("✅ System shutdown completed")
            
        except Exception as e:
            print(f"⚠️  Shutdown error: {e}")
    
    def print_demo_summary(self, report: Dict[str, Any]) -> None:
        """Print demo summary."""
        print("\n" + "="*60)
        print("📊 EVALUATION SYSTEM DEMO SUMMARY")
        print("="*60)
        
        demo_info = report["demo_info"]
        performance = report["performance_analysis"]
        
        print(f"Duration: {demo_info['duration_seconds']:.1f}s")
        print(f"Evaluations: {demo_info['demo_stats']['evaluations_completed']}")
        print(f"Corrections: {demo_info['demo_stats']['corrections_captured']}")
        print(f"Cache hits: {demo_info['demo_stats']['cache_hits']}")
        print(f"Average evaluation time: {performance['average_evaluation_time']:.1f}ms")
        print(f"Cache hit rate: {performance['cache_hit_rate']:.1f}%")
        print(f"System health: {performance['system_health']}")
        
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\nRecommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec['agent_type']}: {rec['recommendation'][:50]}...")
        
        print("\n✅ Demo completed successfully!")
        print("="*60)


async def main():
    """Run the evaluation system demo."""
    print("🚀 Starting Evaluation System Demo")
    print("="*60)
    
    demo = EvaluationSystemDemo()
    
    try:
        # Initialize system
        init_result = await demo.initialize_system()
        if not init_result["initialized"]:
            print(f"❌ Initialization failed: {init_result.get('error', 'Unknown error')}")
            return
        
        # Run demo scenario
        demo_result = await demo.run_demo_scenario()
        
        # Generate report
        report = await demo.generate_demo_report()
        
        # Print summary
        demo.print_demo_summary(report)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Shutdown system
        await demo.shutdown_system()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())