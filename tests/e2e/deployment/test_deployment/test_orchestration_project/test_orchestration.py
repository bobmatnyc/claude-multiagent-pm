"""Test script to verify orchestration deployment."""
import os
import sys

# Set orchestration flag
os.environ['CLAUDE_PM_ORCHESTRATION'] = 'ENABLED'

print("=== Orchestration Deployment Test ===")
print(f"Working directory: {os.getcwd()}")
print(f"CLAUDE_PM_ORCHESTRATION: {os.environ.get('CLAUDE_PM_ORCHESTRATION', 'NOT SET')}")

try:
    from claude_pm.orchestration.orchestration_detector import OrchestrationDetector
    from claude_pm.orchestration.backwards_compatible_orchestrator import BackwardsCompatibleOrchestrator
    from claude_pm.orchestration.context_manager import ContextManager
    
    # Test detection
    detector = OrchestrationDetector()
    print(f"\n✅ Orchestration detector initialized")
    print(f"   - Is enabled: {detector.is_orchestration_enabled()}")
    claude_md_path = detector.get_claude_md_path()
    print(f"   - CLAUDE.md path: {claude_md_path}")
    
    # Test backwards compatible orchestrator
    orchestrator = BackwardsCompatibleOrchestrator()
    print(f"\n✅ BackwardsCompatibleOrchestrator initialized")
    metrics = orchestrator.get_orchestration_metrics()
    print(f"   - Metrics: {metrics}")
    
    # Test context manager
    context_mgr = ContextManager()
    print(f"\n✅ ContextManager initialized")
    
    print("\n🎉 All orchestration components working correctly!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Runtime error: {e}")
    sys.exit(1)
