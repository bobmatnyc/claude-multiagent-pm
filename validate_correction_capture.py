#!/usr/bin/env python3
"""
Validation script for correction capture implementation.
"""

import sys
import os
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_imports():
    """Test that all required imports work."""
    try:
        # Test core imports
        from claude_pm.core.config import Config
        print("✓ Core config import successful")
        
        # Test correction capture imports
        from claude_pm.services.correction_capture import (
            CorrectionCapture,
            CorrectionType,
            CorrectionData,
            capture_subprocess_correction,
            initialize_correction_capture_system
        )
        print("✓ Correction capture imports successful")
        
        # Test Task Tool integration imports
        from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
        print("✓ Task Tool helper imports successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def validate_basic_functionality():
    """Test basic correction capture functionality."""
    try:
        from claude_pm.services.correction_capture import CorrectionCapture, CorrectionType
        from claude_pm.core.config import Config
        
        # Test initialization
        config = Config({'correction_capture_enabled': True})
        capture = CorrectionCapture(config)
        print("✓ CorrectionCapture initialization successful")
        
        # Test directory structure
        storage_path = capture.storage_config.storage_path
        print(f"✓ Storage path configured: {storage_path}")
        
        # Test correction capture
        correction_id = capture.capture_correction(
            agent_type="engineer",
            original_response="def hello(): pass",
            user_correction="def hello(): print('Hello, World!')",
            context={"task": "Create hello function"},
            correction_type=CorrectionType.CONTENT_CORRECTION,
            severity="medium"
        )
        
        if correction_id:
            print(f"✓ Correction capture successful: {correction_id}")
        else:
            print("✗ Correction capture failed")
            return False
        
        # Test statistics
        stats = capture.get_correction_stats()
        if stats.get("total_corrections", 0) > 0:
            print(f"✓ Statistics generation successful: {stats['total_corrections']} corrections")
        else:
            print("✗ Statistics generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_task_tool_integration():
    """Test Task Tool integration."""
    try:
        from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
        
        # Create helper with correction capture enabled
        config = TaskToolConfiguration(
            correction_capture_enabled=True,
            correction_capture_auto_hook=True
        )
        
        helper = TaskToolHelper(config=config)
        print("✓ Task Tool helper initialization successful")
        
        # Test subprocess creation
        subprocess_result = helper.create_agent_subprocess(
            agent_type="engineer",
            task_description="Test task for correction capture",
            requirements=["Test requirement"],
            deliverables=["Test deliverable"]
        )
        
        if subprocess_result.get("success"):
            subprocess_id = subprocess_result["subprocess_id"]
            print(f"✓ Subprocess creation successful: {subprocess_id}")
            
            # Test correction capture
            correction_id = helper.capture_correction(
                subprocess_id=subprocess_id,
                original_response="Test response",
                user_correction="Corrected response",
                correction_type="CONTENT_CORRECTION",
                severity="medium"
            )
            
            if correction_id:
                print(f"✓ Subprocess correction capture successful: {correction_id}")
            else:
                print("✗ Subprocess correction capture failed")
                return False
            
            # Test completion
            completion_result = helper.complete_subprocess(
                subprocess_id=subprocess_id,
                results={"summary": "Test completed"}
            )
            
            if completion_result:
                print("✓ Subprocess completion successful")
            else:
                print("✗ Subprocess completion failed")
                return False
                
        else:
            print(f"✗ Subprocess creation failed: {subprocess_result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Task Tool integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_config_integration():
    """Test configuration integration."""
    try:
        from claude_pm.core.config import Config
        
        # Test default configuration
        config = Config()
        
        # Check evaluation-related config values
        evaluation_enabled = config.get("enable_evaluation", False)
        storage_path = config.get("evaluation_storage_path", "")
        correction_enabled = config.get("correction_capture_enabled", False)
        
        print(f"✓ Configuration loaded successfully")
        print(f"  - Evaluation enabled: {evaluation_enabled}")
        print(f"  - Storage path: {storage_path}")
        print(f"  - Correction capture enabled: {correction_enabled}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration integration test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("CORRECTION CAPTURE IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Import Validation", validate_imports),
        ("Basic Functionality", validate_basic_functionality),
        ("Task Tool Integration", validate_task_tool_integration),
        ("Configuration Integration", validate_config_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                print(f"✓ {test_name} PASSED")
                passed += 1
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 All validation tests passed! Correction capture system is ready.")
        return 0
    else:
        print("❌ Some validation tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())