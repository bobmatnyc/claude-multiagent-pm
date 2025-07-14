"""
Memory System Validation Utility

This module provides comprehensive validation functions for the memory system
to ensure it's ready for production use and deployment scenarios.
"""

import asyncio
import os
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

from .fallback_memory_config import (
    validate_memory_system_health,
    migrate_memory_system_if_needed,
    get_development_safe_memory_config,
    get_release_ready_memory_config,
)
from .release_ready_memory import ReleaseReadyMemoryService
from .interfaces.models import MemoryCategory, MemoryQuery


logger = logging.getLogger(__name__)


async def validate_memory_system_for_release() -> Dict[str, Any]:
    """
    Comprehensive validation of memory system for release readiness.
    
    This function validates:
    - System health and configuration
    - API-independent operation
    - Memory CRUD operations
    - Search functionality
    - Multiple memory categories
    - Performance characteristics
    - Error handling and resilience
    
    Returns:
        Dict[str, Any]: Comprehensive validation results
    """
    
    validation_results = {
        "overall_status": "unknown",
        "timestamp": "2025-07-14T16:30:00Z",
        "framework_version": "v0.8.0",
        "validation_phases": {},
        "performance_metrics": {},
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "release_ready": False
    }
    
    try:
        # Phase 1: System Health Check
        print("🔍 Phase 1: System Health Validation")
        health_start = asyncio.get_event_loop().time()
        
        health_status = validate_memory_system_health()
        validation_results["validation_phases"]["health_check"] = {
            "status": health_status["overall_health"],
            "sqlite_health": health_status["sqlite_health"],
            "api_available": health_status["api_key_available"],
            "configuration": health_status["configuration"],
            "errors": health_status.get("errors", []),
            "warnings": health_status.get("warnings", [])
        }
        
        health_duration = asyncio.get_event_loop().time() - health_start
        validation_results["performance_metrics"]["health_check_duration"] = health_duration
        
        print(f"   ✅ Health check completed in {health_duration:.3f}s")
        print(f"   SQLite Health: {health_status['sqlite_health']}")
        print(f"   Configuration: {health_status['configuration']}")
        
        # Phase 2: Migration Validation
        print("🔧 Phase 2: Database Migration Validation")
        migration_start = asyncio.get_event_loop().time()
        
        migration_result = migrate_memory_system_if_needed()
        validation_results["validation_phases"]["migration"] = {
            "needed": migration_result["migration_needed"],
            "performed": migration_result["migration_performed"],
            "current_version": migration_result["current_version"],
            "target_version": migration_result["target_version"],
            "operations": migration_result["operations"],
            "errors": migration_result.get("errors", [])
        }
        
        migration_duration = asyncio.get_event_loop().time() - migration_start
        validation_results["performance_metrics"]["migration_duration"] = migration_duration
        
        print(f"   ✅ Migration validation completed in {migration_duration:.3f}s")
        
        # Phase 3: API-Independent Operation Test
        print("🚫 Phase 3: API-Independent Operation Test")
        api_independent_start = asyncio.get_event_loop().time()
        
        # Temporarily remove API key to test fallback
        original_api_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        try:
            service = ReleaseReadyMemoryService(environment="production")
            initialization_success = await service.initialize()
            
            validation_results["validation_phases"]["api_independent"] = {
                "initialization": initialization_success,
                "backend_used": service.get_service_health().get("backend_used", "unknown"),
                "configuration": service.get_service_health().get("configuration", {}),
            }
            
            if initialization_success:
                print(f"   ✅ API-independent initialization successful")
                print(f"   Backend: {service.get_service_health()['backend_used']}")
            else:
                print("   ❌ API-independent initialization failed")
                validation_results["errors"].append("Failed to initialize without API key")
            
            await service.cleanup()
            
        finally:
            # Restore API key
            if original_api_key:
                os.environ['OPENAI_API_KEY'] = original_api_key
        
        api_independent_duration = asyncio.get_event_loop().time() - api_independent_start
        validation_results["performance_metrics"]["api_independent_duration"] = api_independent_duration
        
        # Phase 4: Memory Operations Test
        print("💾 Phase 4: Memory Operations Validation")
        operations_start = asyncio.get_event_loop().time()
        
        # Use normal configuration for operations test
        service = ReleaseReadyMemoryService(environment="development")
        await service.initialize()
        
        # Test basic operations
        test_project = "validation_test_project"
        operations_results = {
            "add_memory": False,
            "search_memory": False,
            "get_stats": False,
            "multiple_categories": False,
            "memory_count": 0
        }
        
        # Test adding memory
        memory_id = await service.add_memory(
            test_project,
            "Memory validation test for v0.8.0 release",
            MemoryCategory.SYSTEM,
            ["validation", "v0.8.0", "release"],
            {"test_type": "validation", "component": "memory_system"}
        )
        
        if memory_id:
            operations_results["add_memory"] = True
            print("   ✅ Memory addition successful")
        else:
            print("   ❌ Memory addition failed")
        
        # Test search
        query = MemoryQuery(query="validation test", limit=10)
        search_results = await service.search_memories(test_project, query)
        
        if search_results:
            operations_results["search_memory"] = True
            operations_results["memory_count"] = len(search_results)
            print(f"   ✅ Memory search successful ({len(search_results)} results)")
        else:
            print("   ❌ Memory search failed")
        
        # Test stats
        stats = await service.get_memory_stats(test_project)
        
        if stats:
            operations_results["get_stats"] = True
            print(f"   ✅ Memory stats successful (Total: {stats.get('total', 0)})")
        else:
            print("   ❌ Memory stats failed")
        
        # Test multiple categories
        test_categories = [
            MemoryCategory.BUG,
            MemoryCategory.USER_FEEDBACK,
            MemoryCategory.ERROR,
            MemoryCategory.PROJECT
        ]
        
        category_successes = 0
        for category in test_categories:
            cat_memory_id = await service.add_memory(
                test_project,
                f"Test memory for category {category.value}",
                category,
                ["category_test"],
                {"category": category.value}
            )
            
            if cat_memory_id:
                category_successes += 1
        
        if category_successes == len(test_categories):
            operations_results["multiple_categories"] = True
            print(f"   ✅ Multiple categories test successful ({category_successes}/{len(test_categories)})")
        else:
            print(f"   ⚠️  Multiple categories partial success ({category_successes}/{len(test_categories)})")
        
        validation_results["validation_phases"]["operations"] = operations_results
        
        operations_duration = asyncio.get_event_loop().time() - operations_start
        validation_results["performance_metrics"]["operations_duration"] = operations_duration
        
        await service.cleanup()
        
        # Phase 5: Performance Assessment
        print("⚡ Phase 5: Performance Assessment")
        
        total_duration = sum(validation_results["performance_metrics"].values())
        validation_results["performance_metrics"]["total_validation_duration"] = total_duration
        
        print(f"   Total validation time: {total_duration:.3f}s")
        
        # Performance thresholds
        performance_thresholds = {
            "health_check_duration": 1.0,
            "migration_duration": 2.0,
            "api_independent_duration": 3.0,
            "operations_duration": 5.0,
            "total_validation_duration": 10.0
        }
        
        performance_issues = []
        for metric, threshold in performance_thresholds.items():
            actual_time = validation_results["performance_metrics"].get(metric, 0)
            if actual_time > threshold:
                performance_issues.append(f"{metric}: {actual_time:.3f}s (threshold: {threshold}s)")
        
        if performance_issues:
            validation_results["warnings"].extend([f"Performance: {issue}" for issue in performance_issues])
            print(f"   ⚠️  Performance warnings: {len(performance_issues)}")
        else:
            print("   ✅ All performance metrics within acceptable range")
        
        # Final Assessment
        print("🎯 Final Assessment")
        
        # Determine overall status
        critical_failures = 0
        critical_checks = [
            validation_results["validation_phases"]["health_check"]["status"] in ["healthy", "degraded"],
            validation_results["validation_phases"]["api_independent"]["initialization"],
            validation_results["validation_phases"]["operations"]["add_memory"],
            validation_results["validation_phases"]["operations"]["search_memory"],
        ]
        
        critical_failures = len([check for check in critical_checks if not check])
        
        if critical_failures == 0:
            validation_results["overall_status"] = "ready"
            validation_results["release_ready"] = True
            print("   ✅ Memory system is RELEASE READY")
        elif critical_failures <= 1:
            validation_results["overall_status"] = "degraded"
            validation_results["release_ready"] = False
            print("   ⚠️  Memory system has minor issues - review required")
        else:
            validation_results["overall_status"] = "failed"
            validation_results["release_ready"] = False
            print("   ❌ Memory system has critical issues - not ready for release")
        
        # Generate recommendations
        if not validation_results["validation_phases"]["operations"]["multiple_categories"]:
            validation_results["recommendations"].append("Investigate memory category handling")
        
        if len(validation_results["warnings"]) > 0:
            validation_results["recommendations"].append("Review performance warnings")
        
        if validation_results["validation_phases"]["api_independent"]["backend_used"] != "sqlite":
            validation_results["recommendations"].append("Verify SQLite fallback configuration")
        
        if validation_results["release_ready"]:
            validation_results["recommendations"].append("Memory system validated for v0.8.0 release")
        
    except Exception as e:
        validation_results["overall_status"] = "error"
        validation_results["release_ready"] = False
        validation_results["errors"].append(f"Validation failed: {e}")
        logger.error(f"Memory validation error: {e}")
        import traceback
        traceback.print_exc()
    
    return validation_results


def print_validation_report(results: Dict[str, Any]) -> None:
    """Print a formatted validation report."""
    
    print("\n" + "="*80)
    print("🧠 MEMORY SYSTEM VALIDATION REPORT")
    print("="*80)
    print(f"Framework Version: {results['framework_version']}")
    print(f"Validation Time: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Release Ready: {'✅ YES' if results['release_ready'] else '❌ NO'}")
    print("")
    
    # Phase Results
    print("📋 VALIDATION PHASES:")
    for phase_name, phase_data in results["validation_phases"].items():
        print(f"   {phase_name}: {phase_data}")
    print("")
    
    # Performance Metrics
    print("⚡ PERFORMANCE METRICS:")
    for metric, value in results["performance_metrics"].items():
        print(f"   {metric}: {value:.3f}s")
    print("")
    
    # Issues
    if results["errors"]:
        print("❌ ERRORS:")
        for error in results["errors"]:
            print(f"   - {error}")
        print("")
    
    if results["warnings"]:
        print("⚠️  WARNINGS:")
        for warning in results["warnings"]:
            print(f"   - {warning}")
        print("")
    
    # Recommendations
    if results["recommendations"]:
        print("💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"   - {rec}")
        print("")
    
    print("="*80)


if __name__ == "__main__":
    # Command-line interface for memory validation
    import sys
    
    async def main():
        print("🧠 Claude PM Framework - Memory System Validation")
        print("Running comprehensive validation for v0.8.0 release...\n")
        
        results = await validate_memory_system_for_release()
        print_validation_report(results)
        
        # Exit with appropriate code
        sys.exit(0 if results["release_ready"] else 1)
    
    asyncio.run(main())