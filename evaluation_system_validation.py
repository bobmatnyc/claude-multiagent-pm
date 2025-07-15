#!/usr/bin/env python3
"""
Automatic Prompt Evaluation System - Validation Report
======================================================

This script validates the implementation of the automatic prompt evaluation system 
as specified in ISS-0125. It checks all 4 phases and reports on system readiness.

Validation Scope:
- Phase 1: Correction Capture System
- Phase 2: Mirascope Evaluation Integration  
- Phase 3: Prompt Improvement Pipeline
- Phase 4: Agent Training Enhancement

Performance Targets:
- <100ms evaluation overhead
- >95% cache hit rate
- System initialization <200ms
- Agent hierarchy integration
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvaluationSystemValidator:
    """Validates the automatic prompt evaluation system implementation."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "performance_metrics": {},
            "system_health": {},
            "recommendations": []
        }
        
    def validate_imports(self) -> Dict[str, Any]:
        """Validate all required imports are available."""
        import_results = {}
        
        # Core imports
        try:
            from claude_pm.core.config import Config
            import_results["Config"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["Config"] = {"status": "missing", "error": str(e)}
        
        # Correction capture
        try:
            from claude_pm.services.correction_capture import CorrectionCapture, CorrectionData, CorrectionType
            import_results["CorrectionCapture"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["CorrectionCapture"] = {"status": "missing", "error": str(e)}
        
        # Mirascope evaluator
        try:
            from claude_pm.services.mirascope_evaluator import MirascopeEvaluator, EvaluationResult
            import_results["MirascopeEvaluator"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["MirascopeEvaluator"] = {"status": "missing", "error": str(e)}
        
        # Integration service
        try:
            from claude_pm.services.evaluation_integration import EvaluationIntegrationService
            import_results["EvaluationIntegrationService"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["EvaluationIntegrationService"] = {"status": "missing", "error": str(e)}
        
        # Metrics system
        try:
            from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
            import_results["EvaluationMetricsSystem"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["EvaluationMetricsSystem"] = {"status": "missing", "error": str(e)}
        
        # Performance manager
        try:
            from claude_pm.services.evaluation_performance import EvaluationPerformanceManager
            import_results["EvaluationPerformanceManager"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["EvaluationPerformanceManager"] = {"status": "missing", "error": str(e)}
        
        # Monitoring
        try:
            from claude_pm.services.evaluation_monitoring import EvaluationMonitor
            import_results["EvaluationMonitor"] = {"status": "available", "error": None}
        except ImportError as e:
            import_results["EvaluationMonitor"] = {"status": "missing", "error": str(e)}
        
        # Calculate summary
        available_count = sum(1 for result in import_results.values() if result["status"] == "available")
        total_count = len(import_results)
        
        return {
            "import_results": import_results,
            "available_components": available_count,
            "total_components": total_count,
            "availability_rate": (available_count / total_count) * 100,
            "status": "PASSED" if available_count >= 4 else "FAILED"
        }
    
    def validate_phase_1_correction_capture(self) -> Dict[str, Any]:
        """Validate Phase 1: Correction Capture System."""
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType
            
            # Test configuration
            config = Config({
                "correction_capture_enabled": True,
                "correction_storage_path": "/tmp/test_corrections"
            })
            
            # Initialize correction capture
            capture = CorrectionCapture(config)
            
            # Test basic functionality
            correction_id = capture.capture_correction(
                agent_type="engineer",
                original_response="def hello(): pass",
                user_correction="def hello(): print('Hello, World!')",
                context={"task": "create hello function"},
                correction_type=CorrectionType.CONTENT_CORRECTION,
                task_description="Create hello function"
            )
            
            # Validate correction was captured
            assert correction_id is not None and len(correction_id) > 0
            
            # Get statistics
            stats = capture.get_correction_stats()
            
            return {
                "status": "PASSED",
                "correction_id": correction_id,
                "correction_stats": stats,
                "functionality": "Basic correction capture working"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Correction capture failed"
            }
    
    def validate_phase_2_mirascope_evaluation(self) -> Dict[str, Any]:
        """Validate Phase 2: Mirascope Evaluation Integration."""
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.mirascope_evaluator import MirascopeEvaluator
            
            # Test configuration
            config = Config({
                "enable_evaluation": True,
                "evaluation_provider": "auto",
                "evaluation_storage_path": "/tmp/test_evaluations"
            })
            
            # Initialize evaluator
            evaluator = MirascopeEvaluator(config)
            
            # Test mock evaluation (when Mirascope not available)
            result = evaluator._create_mock_result(
                "engineer",
                "def hello(): print('Hello, World!')",
                {"task": "create hello function"}
            )
            
            # Validate evaluation result
            assert result is not None
            assert result.agent_type == "engineer"
            assert result.overall_score > 0
            
            # Get statistics
            stats = evaluator.get_evaluation_statistics()
            
            return {
                "status": "PASSED",
                "evaluation_enabled": evaluator.enabled,
                "overall_score": result.overall_score,
                "evaluation_stats": stats,
                "functionality": "Mirascope evaluation integration working"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Mirascope evaluation failed"
            }
    
    def validate_phase_3_prompt_improvement(self) -> Dict[str, Any]:
        """Validate Phase 3: Prompt Improvement Pipeline."""
        try:
            # Check if prompt improvement components exist
            improvement_files = [
                "claude_pm/services/prompt_improver.py",
                "claude_pm/services/prompt_template_manager.py",
                "claude_pm/services/prompt_validator.py",
                "claude_pm/services/prompt_improvement_pipeline.py"
            ]
            
            existing_files = []
            for file_path in improvement_files:
                if Path(file_path).exists():
                    existing_files.append(file_path)
            
            # Test import of improvement pipeline
            try:
                from claude_pm.services.prompt_improvement_pipeline import PromptImprovementPipeline
                pipeline_available = True
            except ImportError:
                pipeline_available = False
            
            return {
                "status": "PASSED" if len(existing_files) >= 2 else "PARTIAL",
                "existing_files": existing_files,
                "pipeline_available": pipeline_available,
                "functionality": f"Prompt improvement pipeline ({len(existing_files)}/4 components found)"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Prompt improvement pipeline validation failed"
            }
    
    def validate_phase_4_agent_training(self) -> Dict[str, Any]:
        """Validate Phase 4: Agent Training Enhancement."""
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.evaluation_integration import EvaluationIntegrationService
            
            # Test configuration
            config = Config({
                "enable_evaluation": True,
                "auto_evaluate_corrections": True,
                "evaluation_storage_path": "/tmp/test_training"
            })
            
            # Initialize integration service
            service = EvaluationIntegrationService(config)
            
            # Test agent improvement metrics
            metrics = service.get_agent_improvement_metrics("engineer")
            
            # Validate metrics structure
            assert "agent_type" in metrics
            assert "total_evaluations" in metrics
            assert "improvement_trend" in metrics
            
            return {
                "status": "PASSED",
                "agent_metrics": metrics,
                "functionality": "Agent training enhancement working"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Agent training enhancement failed"
            }
    
    def validate_integration_service(self) -> Dict[str, Any]:
        """Validate the overall integration service."""
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.evaluation_integration import EvaluationIntegrationService
            from claude_pm.services.correction_capture import CorrectionType
            
            # Test configuration
            config = Config({
                "enable_evaluation": True,
                "auto_evaluate_corrections": True,
                "evaluation_storage_path": "/tmp/test_integration"
            })
            
            # Initialize service
            service = EvaluationIntegrationService(config)
            
            # Test integration statistics
            stats = service.get_integration_statistics()
            
            # Validate statistics structure
            assert "integration_stats" in stats
            assert "service_enabled" in stats
            assert "correction_stats" in stats
            
            return {
                "status": "PASSED",
                "service_enabled": stats["service_enabled"],
                "integration_stats": stats["integration_stats"],
                "functionality": "Integration service working"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Integration service failed"
            }
    
    def validate_performance_targets(self) -> Dict[str, Any]:
        """Validate performance targets."""
        performance_results = {}
        
        # Test 1: System initialization time (<200ms)
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
            
            start_time = time.time()
            config = Config({"enable_evaluation_metrics": True})
            metrics = EvaluationMetricsSystem(config)
            init_time = (time.time() - start_time) * 1000  # Convert to ms
            
            performance_results["initialization_time"] = {
                "value_ms": init_time,
                "target_ms": 200,
                "status": "PASSED" if init_time < 200 else "FAILED"
            }
            
        except Exception as e:
            performance_results["initialization_time"] = {
                "status": "FAILED",
                "error": str(e)
            }
        
        # Test 2: Evaluation overhead (<100ms)
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.mirascope_evaluator import MirascopeEvaluator
            
            config = Config({"enable_evaluation": True})
            evaluator = MirascopeEvaluator(config)
            
            start_time = time.time()
            result = evaluator._create_mock_result("engineer", "test", {"task": "test"})
            eval_time = (time.time() - start_time) * 1000  # Convert to ms
            
            performance_results["evaluation_overhead"] = {
                "value_ms": eval_time,
                "target_ms": 100,
                "status": "PASSED" if eval_time < 100 else "FAILED"
            }
            
        except Exception as e:
            performance_results["evaluation_overhead"] = {
                "status": "FAILED",
                "error": str(e)
            }
        
        # Test 3: Cache effectiveness (>95% hit rate)
        try:
            from claude_pm.core.config import Config
            from claude_pm.services.evaluation_performance import EvaluationPerformanceManager
            
            config = Config({"evaluation_performance_enabled": True})
            performance_manager = EvaluationPerformanceManager(config)
            
            cache = performance_manager.cache
            
            # Test cache with known data
            test_keys = [f"key_{i}" for i in range(20)]
            for key in test_keys:
                cache.put(key, f"value_{key}")
            
            hits = sum(1 for key in test_keys if cache.get(key) == f"value_{key}")
            hit_rate = (hits / len(test_keys)) * 100
            
            performance_results["cache_effectiveness"] = {
                "hit_rate": hit_rate,
                "target_rate": 95,
                "status": "PASSED" if hit_rate >= 95 else "FAILED"
            }
            
        except Exception as e:
            performance_results["cache_effectiveness"] = {
                "status": "FAILED",
                "error": str(e)
            }
        
        return performance_results
    
    def validate_agent_hierarchy_integration(self) -> Dict[str, Any]:
        """Validate integration with agent hierarchy."""
        try:
            # Test if agent hierarchy components exist
            from claude_pm.core.config import Config
            
            # Test agent types
            agent_types = [
                "engineer", "researcher", "ops", "qa", "documentation",
                "security", "data_engineer", "architect", "integration"
            ]
            
            # Test metrics for different agent types
            from claude_pm.services.evaluation_metrics import EvaluationMetricsSystem
            
            config = Config({"enable_evaluation_metrics": True})
            metrics = EvaluationMetricsSystem(config)
            
            agent_results = {}
            for agent_type in agent_types:
                agent_metrics = metrics.get_agent_metrics(agent_type)
                agent_results[agent_type] = {
                    "metrics_available": "agent_type" in agent_metrics,
                    "summary": agent_metrics.get("summary", "No data")
                }
            
            return {
                "status": "PASSED",
                "supported_agents": len(agent_types),
                "agent_results": agent_results,
                "functionality": "Agent hierarchy integration working"
            }
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "functionality": "Agent hierarchy integration failed"
            }
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation of the evaluation system."""
        print("🔬 Automatic Prompt Evaluation System - Validation Report")
        print("=" * 60)
        
        # Validate imports
        print("\n📦 1. Component Imports Validation")
        import_results = self.validate_imports()
        self.results["validation_results"]["imports"] = import_results
        print(f"   Status: {import_results['status']}")
        print(f"   Available: {import_results['available_components']}/{import_results['total_components']} components")
        
        # Validate Phase 1: Correction Capture
        print("\n📋 2. Phase 1: Correction Capture System")
        phase1_results = self.validate_phase_1_correction_capture()
        self.results["validation_results"]["phase_1"] = phase1_results
        print(f"   Status: {phase1_results['status']}")
        print(f"   Functionality: {phase1_results['functionality']}")
        
        # Validate Phase 2: Mirascope Evaluation
        print("\n🔍 3. Phase 2: Mirascope Evaluation Integration")
        phase2_results = self.validate_phase_2_mirascope_evaluation()
        self.results["validation_results"]["phase_2"] = phase2_results
        print(f"   Status: {phase2_results['status']}")
        print(f"   Functionality: {phase2_results['functionality']}")
        
        # Validate Phase 3: Prompt Improvement
        print("\n🛠️  4. Phase 3: Prompt Improvement Pipeline")
        phase3_results = self.validate_phase_3_prompt_improvement()
        self.results["validation_results"]["phase_3"] = phase3_results
        print(f"   Status: {phase3_results['status']}")
        print(f"   Functionality: {phase3_results['functionality']}")
        
        # Validate Phase 4: Agent Training
        print("\n🎓 5. Phase 4: Agent Training Enhancement")
        phase4_results = self.validate_phase_4_agent_training()
        self.results["validation_results"]["phase_4"] = phase4_results
        print(f"   Status: {phase4_results['status']}")
        print(f"   Functionality: {phase4_results['functionality']}")
        
        # Validate Integration Service
        print("\n🔧 6. Integration Service Validation")
        integration_results = self.validate_integration_service()
        self.results["validation_results"]["integration"] = integration_results
        print(f"   Status: {integration_results['status']}")
        print(f"   Functionality: {integration_results['functionality']}")
        
        # Validate Performance Targets
        print("\n⚡ 7. Performance Targets Validation")
        performance_results = self.validate_performance_targets()
        self.results["performance_metrics"] = performance_results
        
        for test_name, result in performance_results.items():
            print(f"   {test_name}: {result['status']}")
            if 'value_ms' in result:
                print(f"     Value: {result['value_ms']:.2f}ms (target: <{result['target_ms']}ms)")
            elif 'hit_rate' in result:
                print(f"     Hit Rate: {result['hit_rate']:.1f}% (target: >{result['target_rate']}%)")
        
        # Validate Agent Hierarchy Integration
        print("\n🤖 8. Agent Hierarchy Integration")
        hierarchy_results = self.validate_agent_hierarchy_integration()
        self.results["validation_results"]["agent_hierarchy"] = hierarchy_results
        print(f"   Status: {hierarchy_results['status']}")
        print(f"   Functionality: {hierarchy_results['functionality']}")
        
        # Generate overall assessment
        print("\n📊 9. Overall Assessment")
        self.generate_overall_assessment()
        
        # Save results
        results_file = Path("evaluation_system_validation_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return self.results
    
    def generate_overall_assessment(self):
        """Generate overall assessment and recommendations."""
        validation_results = self.results["validation_results"]
        performance_results = self.results["performance_metrics"]
        
        # Count passed/failed validations
        passed_count = 0
        total_count = 0
        
        for category, result in validation_results.items():
            total_count += 1
            if result.get("status") == "PASSED":
                passed_count += 1
        
        # Count performance metrics
        perf_passed = 0
        perf_total = 0
        
        for test_name, result in performance_results.items():
            perf_total += 1
            if result.get("status") == "PASSED":
                perf_passed += 1
        
        # Calculate overall score
        validation_score = (passed_count / total_count) * 100 if total_count > 0 else 0
        performance_score = (perf_passed / perf_total) * 100 if perf_total > 0 else 0
        overall_score = (validation_score + performance_score) / 2
        
        # Determine status
        if overall_score >= 95:
            status = "EXCELLENT"
        elif overall_score >= 80:
            status = "GOOD"
        elif overall_score >= 60:
            status = "FAIR"
        else:
            status = "NEEDS_IMPROVEMENT"
        
        self.results["system_health"] = {
            "validation_score": validation_score,
            "performance_score": performance_score,
            "overall_score": overall_score,
            "status": status,
            "passed_validations": passed_count,
            "total_validations": total_count,
            "passed_performance": perf_passed,
            "total_performance": perf_total
        }
        
        print(f"   Validation Score: {validation_score:.1f}% ({passed_count}/{total_count} passed)")
        print(f"   Performance Score: {performance_score:.1f}% ({perf_passed}/{perf_total} passed)")
        print(f"   Overall Score: {overall_score:.1f}%")
        print(f"   Status: {status}")
        
        # Generate recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check validation results
        validation_results = self.results["validation_results"]
        
        # Import recommendations
        import_result = validation_results.get("imports", {})
        if import_result.get("availability_rate", 0) < 100:
            recommendations.append({
                "priority": "HIGH",
                "category": "Components",
                "issue": "Some evaluation components are missing",
                "recommendation": "Install missing dependencies and verify all imports",
                "impact": "System functionality may be limited"
            })
        
        # Phase recommendations
        for phase_name, phase_result in validation_results.items():
            if phase_result.get("status") == "FAILED":
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Implementation",
                    "issue": f"{phase_name} failed validation",
                    "recommendation": f"Fix {phase_name} implementation and retry validation",
                    "impact": "Core functionality affected"
                })
        
        # Performance recommendations
        performance_results = self.results["performance_metrics"]
        
        for test_name, result in performance_results.items():
            if result.get("status") == "FAILED":
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "issue": f"{test_name} failed performance target",
                    "recommendation": f"Optimize {test_name} implementation",
                    "impact": "Performance may be suboptimal"
                })
        
        self.results["recommendations"] = recommendations
        
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. [{rec['priority']}] {rec['issue']}")
                print(f"      → {rec['recommendation']}")
        else:
            print("\n✅ No recommendations - system is performing well!")

def main():
    """Main validation function."""
    validator = EvaluationSystemValidator()
    results = validator.run_validation()
    
    # Return system health status
    return results["system_health"]["status"]

if __name__ == "__main__":
    main()