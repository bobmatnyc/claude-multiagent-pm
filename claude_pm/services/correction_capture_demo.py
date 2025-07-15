#!/usr/bin/env python3
"""
Correction Capture System Demo
=============================

This script demonstrates the correction capture system for automatic prompt evaluation.
It shows how to:
1. Initialize the correction capture system
2. Create Task Tool subprocesses with correction hooks
3. Capture corrections from user feedback
4. View correction statistics and reports

Usage:
    python -m claude_pm.services.correction_capture_demo
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.services.correction_capture import (
    CorrectionCapture, 
    CorrectionType, 
    capture_subprocess_correction,
    initialize_correction_capture_system,
    get_agent_correction_history
)
from claude_pm.utils.task_tool_helper import TaskToolHelper, TaskToolConfiguration
from claude_pm.core.config import Config


def print_section(title: str, content: str = ""):
    """Print a formatted section."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if content:
        print(content)


def demonstrate_correction_capture():
    """Demonstrate the correction capture system."""
    print_section("Correction Capture System Demo", "Testing Phase 1 implementation")
    
    # 1. Initialize the system
    print_section("1. System Initialization")
    init_result = initialize_correction_capture_system()
    print(f"Initialization successful: {init_result['initialized']}")
    
    if not init_result['initialized']:
        print(f"Error: {init_result.get('error', 'Unknown error')}")
        return
    
    print(f"Storage path: {init_result['storage_path']}")
    print(f"Service enabled: {init_result['service_enabled']}")
    
    # 2. Create Task Tool helper with correction capture
    print_section("2. Task Tool Helper with Correction Capture")
    config = TaskToolConfiguration(
        correction_capture_enabled=True,
        correction_capture_auto_hook=True
    )
    
    helper = TaskToolHelper(config=config)
    
    # Validate integration
    validation = helper.validate_integration()
    print(f"Integration valid: {validation['valid']}")
    print(f"Correction capture enabled: {validation.get('correction_capture', {}).get('enabled', False)}")
    
    # 3. Create a test subprocess
    print_section("3. Creating Test Subprocess")
    subprocess_result = helper.create_agent_subprocess(
        agent_type="engineer",
        task_description="Implement user authentication system",
        requirements=["JWT tokens", "Password hashing", "Session management"],
        deliverables=["Auth module", "Unit tests", "Documentation"],
        priority="high"
    )
    
    if subprocess_result['success']:
        subprocess_id = subprocess_result['subprocess_id']
        print(f"Created subprocess: {subprocess_id}")
        print(f"Correction hook created: {subprocess_result.get('correction_hook', {}).get('hook_id', 'None')}")
        
        # 4. Simulate capturing corrections
        print_section("4. Capturing Test Corrections")
        
        # Test correction 1: Content correction
        correction_1 = helper.capture_correction(
            subprocess_id=subprocess_id,
            original_response="def authenticate(user, password): return user == 'admin' and password == 'admin'",
            user_correction="def authenticate(user, password): return bcrypt.checkpw(password.encode('utf-8'), user.password_hash)",
            correction_type="TECHNICAL_CORRECTION",
            severity="high",
            user_feedback="Security issue: Never use hardcoded credentials. Use proper password hashing."
        )
        print(f"Captured correction 1: {correction_1}")
        
        # Test correction 2: Missing information
        correction_2 = helper.capture_correction(
            subprocess_id=subprocess_id,
            original_response="Authentication system implemented.",
            user_correction="Authentication system implemented with JWT tokens, password hashing using bcrypt, and session management with Redis.",
            correction_type="MISSING_INFORMATION",
            severity="medium",
            user_feedback="Response was too brief and didn't specify implementation details."
        )
        print(f"Captured correction 2: {correction_2}")
        
        # Test correction 3: Approach correction
        correction_3 = helper.capture_correction(
            subprocess_id=subprocess_id,
            original_response="Store passwords in plain text for simplicity.",
            user_correction="Use bcrypt for password hashing with appropriate salt rounds.",
            correction_type="APPROACH_CORRECTION",
            severity="critical",
            user_feedback="Major security vulnerability - never store passwords in plain text."
        )
        print(f"Captured correction 3: {correction_3}")
        
        # 5. View correction statistics
        print_section("5. Correction Statistics")
        stats = helper.get_correction_statistics()
        
        if stats['enabled']:
            print("Overall Statistics:")
            for key, value in stats['statistics'].items():
                print(f"  {key}: {value}")
        else:
            print(f"Statistics unavailable: {stats.get('message', 'Unknown error')}")
        
        # 6. Get agent-specific correction history
        print_section("6. Agent Correction History")
        engineer_corrections = get_agent_correction_history("engineer", limit=5)
        print(f"Found {len(engineer_corrections)} corrections for engineer agent")
        
        for i, correction in enumerate(engineer_corrections[:3], 1):
            print(f"\nCorrection {i}:")
            print(f"  ID: {correction.correction_id}")
            print(f"  Type: {correction.correction_type.value}")
            print(f"  Severity: {correction.severity}")
            print(f"  Timestamp: {correction.timestamp}")
            print(f"  User feedback: {correction.user_feedback[:100]}..." if correction.user_feedback else "  No feedback")
        
        # 7. Complete the subprocess
        print_section("7. Completing Subprocess")
        completion_result = helper.complete_subprocess(
            subprocess_id=subprocess_id,
            results={
                "summary": "Authentication system implemented with corrections applied",
                "deliverables": ["Auth module", "Unit tests", "Documentation"],
                "corrections_applied": 3
            }
        )
        print(f"Subprocess completed: {completion_result}")
        
    else:
        print(f"Failed to create subprocess: {subprocess_result.get('error', 'Unknown error')}")
    
    # 8. Final system validation
    print_section("8. Final System Validation")
    capture_service = CorrectionCapture()
    validation_result = capture_service.validate_storage_integrity()
    print(f"Storage integrity OK: {validation_result['integrity_ok']}")
    
    if validation_result['issues']:
        print("Issues found:")
        for issue in validation_result['issues']:
            print(f"  - {issue}")
    
    if validation_result['fixes_applied']:
        print("Fixes applied:")
        for fix in validation_result['fixes_applied']:
            print(f"  - {fix}")


def demonstrate_direct_correction_capture():
    """Demonstrate direct correction capture without Task Tool helper."""
    print_section("Direct Correction Capture Demo", "Testing direct service usage")
    
    # Initialize correction capture service
    capture_service = CorrectionCapture()
    
    if not capture_service.enabled:
        print("Correction capture service is disabled")
        return
    
    # Capture some example corrections
    print_section("Capturing Direct Corrections")
    
    corrections = [
        {
            "agent_type": "documentation",
            "original_response": "Function does something.",
            "user_correction": "Function authenticates users using JWT tokens and bcrypt password hashing.",
            "correction_type": CorrectionType.MISSING_INFORMATION,
            "context": {"task": "Document authentication function"},
            "severity": "medium",
            "user_feedback": "Documentation was too vague and didn't explain the actual functionality."
        },
        {
            "agent_type": "qa",
            "original_response": "Tests look good.",
            "user_correction": "Tests are missing edge cases for empty passwords, SQL injection attempts, and concurrent login attempts.",
            "correction_type": CorrectionType.QUALITY_IMPROVEMENT,
            "context": {"task": "Review authentication tests"},
            "severity": "high",
            "user_feedback": "Need more comprehensive test coverage."
        },
        {
            "agent_type": "security",
            "original_response": "Use simple password validation.",
            "user_correction": "Implement password complexity requirements: minimum 12 characters, uppercase, lowercase, numbers, and special characters.",
            "correction_type": CorrectionType.TECHNICAL_CORRECTION,
            "context": {"task": "Define password policy"},
            "severity": "high",
            "user_feedback": "Security requirements were insufficient."
        }
    ]
    
    captured_ids = []
    for correction in corrections:
        correction_id = capture_service.capture_correction(**correction)
        captured_ids.append(correction_id)
        print(f"Captured correction: {correction_id}")
    
    # Get statistics
    print_section("Statistics After Direct Capture")
    stats = capture_service.get_correction_stats()
    print(f"Total corrections: {stats['total_corrections']}")
    print(f"Agents with corrections: {stats['agents_with_corrections']}")
    print(f"Correction types: {stats['correction_types']}")
    print(f"Most corrected agent: {stats['most_corrected_agent']}")
    
    # Test data export
    print_section("Data Export Test")
    try:
        export_path = capture_service.export_corrections(format="json")
        print(f"Exported corrections to: {export_path}")
    except Exception as e:
        print(f"Export failed: {e}")
    
    # Test cleanup
    print_section("Cleanup Test")
    cleanup_result = capture_service.cleanup_old_corrections(days_to_keep=365)  # Keep everything for demo
    print(f"Cleanup completed: {cleanup_result}")


if __name__ == "__main__":
    print("=" * 80)
    print("CLAUDE PM FRAMEWORK - CORRECTION CAPTURE SYSTEM DEMO")
    print("=" * 80)
    
    try:
        # Run Task Tool integration demo
        demonstrate_correction_capture()
        
        # Run direct capture demo
        demonstrate_direct_correction_capture()
        
        print_section("Demo Complete", "All correction capture features demonstrated successfully!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()