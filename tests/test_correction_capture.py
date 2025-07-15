"""
Test suite for the correction capture system.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the correction capture components
from claude_pm.services.correction_capture import (
    CorrectionCapture,
    CorrectionType,
    CorrectionData,
    CorrectionStorageConfig,
    capture_subprocess_correction,
    get_agent_correction_history,
    initialize_correction_capture_system
)
from claude_pm.core.config import Config


class TestCorrectionCapture(unittest.TestCase):
    """Test cases for the correction capture system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test storage
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test config
        self.test_config = Config({
            "correction_capture_enabled": True,
            "evaluation_storage_path": str(self.temp_path),
            "correction_storage_rotation_days": 7,
            "evaluation_logging_enabled": True
        })
        
        # Initialize correction capture with test config
        self.correction_capture = CorrectionCapture(self.test_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test correction capture initialization."""
        self.assertTrue(self.correction_capture.enabled)
        self.assertEqual(self.correction_capture.storage_config.storage_path, self.temp_path)
        
        # Check that directories were created
        self.assertTrue((self.temp_path / "corrections").exists())
        self.assertTrue((self.temp_path / "evaluations").exists())
        self.assertTrue((self.temp_path / "agent-prompts").exists())
        
        # Check metadata file
        metadata_file = self.temp_path / "metadata.json"
        self.assertTrue(metadata_file.exists())
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            self.assertIn("created", metadata)
            self.assertIn("version", metadata)
    
    def test_correction_data_structure(self):
        """Test CorrectionData structure and serialization."""
        correction_data = CorrectionData(
            correction_id="test_123",
            agent_type="engineer",
            original_response="def hello(): pass",
            user_correction="def hello(): print('Hello, World!')",
            context={"task": "Create hello function"},
            correction_type=CorrectionType.CONTENT_CORRECTION,
            timestamp=datetime.now().isoformat(),
            severity="medium"
        )
        
        # Test serialization
        data_dict = correction_data.to_dict()
        self.assertIn("correction_id", data_dict)
        self.assertIn("agent_type", data_dict)
        self.assertEqual(data_dict["correction_type"], "content_correction")
        
        # Test deserialization
        restored_data = CorrectionData.from_dict(data_dict)
        self.assertEqual(restored_data.correction_id, "test_123")
        self.assertEqual(restored_data.agent_type, "engineer")
        self.assertEqual(restored_data.correction_type, CorrectionType.CONTENT_CORRECTION)
    
    def test_capture_correction(self):
        """Test capturing a correction."""
        correction_id = self.correction_capture.capture_correction(
            agent_type="engineer",
            original_response="def calculate(): return 1 + 1",
            user_correction="def calculate(): return 2 + 2",
            context={"task": "Fix calculation"},
            correction_type=CorrectionType.TECHNICAL_CORRECTION,
            severity="low",
            user_feedback="Wrong calculation result"
        )
        
        self.assertIsNotNone(correction_id)
        self.assertNotEqual(correction_id, "")
        self.assertTrue(correction_id.startswith("corr_"))
        
        # Check that correction was stored
        corrections = self.correction_capture.get_corrections()
        self.assertEqual(len(corrections), 1)
        self.assertEqual(corrections[0].correction_id, correction_id)
        self.assertEqual(corrections[0].agent_type, "engineer")
    
    def test_get_corrections_filtering(self):
        """Test retrieving corrections with filtering."""
        # Create multiple corrections
        corrections_data = [
            {
                "agent_type": "engineer",
                "original_response": "code 1",
                "user_correction": "fixed code 1",
                "context": {"task": "task 1"},
                "correction_type": CorrectionType.CONTENT_CORRECTION,
                "severity": "high"
            },
            {
                "agent_type": "documentation",
                "original_response": "doc 1",
                "user_correction": "fixed doc 1",
                "context": {"task": "task 2"},
                "correction_type": CorrectionType.MISSING_INFORMATION,
                "severity": "medium"
            },
            {
                "agent_type": "engineer",
                "original_response": "code 2",
                "user_correction": "fixed code 2",
                "context": {"task": "task 3"},
                "correction_type": CorrectionType.TECHNICAL_CORRECTION,
                "severity": "low"
            }
        ]
        
        # Capture corrections
        for correction in corrections_data:
            self.correction_capture.capture_correction(**correction)
        
        # Test filtering by agent type
        engineer_corrections = self.correction_capture.get_corrections(agent_type="engineer")
        self.assertEqual(len(engineer_corrections), 2)
        
        doc_corrections = self.correction_capture.get_corrections(agent_type="documentation")
        self.assertEqual(len(doc_corrections), 1)
        
        # Test filtering by severity
        high_corrections = self.correction_capture.get_corrections(severity="high")
        self.assertEqual(len(high_corrections), 1)
        
        # Test limit
        limited_corrections = self.correction_capture.get_corrections(limit=2)
        self.assertEqual(len(limited_corrections), 2)
    
    def test_correction_statistics(self):
        """Test correction statistics generation."""
        # Initially no corrections
        stats = self.correction_capture.get_correction_stats()
        self.assertEqual(stats["total_corrections"], 0)
        self.assertEqual(stats["agents_with_corrections"], [])
        
        # Add some corrections
        self.correction_capture.capture_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="fixed test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION,
            severity="high"
        )
        
        self.correction_capture.capture_correction(
            agent_type="engineer",
            original_response="test2",
            user_correction="fixed test2",
            context={"task": "test2"},
            correction_type=CorrectionType.TECHNICAL_CORRECTION,
            severity="medium"
        )
        
        # Check updated stats
        stats = self.correction_capture.get_correction_stats()
        self.assertEqual(stats["total_corrections"], 2)
        self.assertIn("engineer", stats["agents_with_corrections"])
        self.assertEqual(stats["agent_correction_counts"]["engineer"], 2)
        self.assertEqual(stats["most_corrected_agent"], "engineer")
    
    def test_storage_integrity_validation(self):
        """Test storage integrity validation."""
        validation_result = self.correction_capture.validate_storage_integrity()
        
        self.assertTrue(validation_result["integrity_ok"])
        self.assertEqual(validation_result["issues_found"], 0)
        self.assertEqual(str(validation_result["storage_path"]), str(self.temp_path))
    
    def test_task_tool_integration_hook(self):
        """Test Task Tool integration hook creation."""
        hook_info = self.correction_capture.create_task_tool_integration_hook(
            subprocess_id="test_subprocess_123",
            agent_type="engineer",
            task_description="Test task"
        )
        
        self.assertIn("hook_id", hook_info)
        self.assertIn("subprocess_id", hook_info)
        self.assertEqual(hook_info["subprocess_id"], "test_subprocess_123")
        self.assertEqual(hook_info["agent_type"], "engineer")
        self.assertTrue(hook_info["active"])
    
    def test_export_corrections(self):
        """Test correction export functionality."""
        # Add a correction
        self.correction_capture.capture_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="fixed test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        # Export corrections
        export_path = self.correction_capture.export_corrections(format="json")
        export_file = Path(export_path)
        
        self.assertTrue(export_file.exists())
        self.assertTrue(export_file.name.startswith("corrections_export_"))
        
        # Verify export content
        with open(export_file, 'r') as f:
            export_data = json.load(f)
            self.assertIn("export_timestamp", export_data)
            self.assertIn("total_corrections", export_data)
            self.assertIn("corrections", export_data)
            self.assertEqual(export_data["total_corrections"], 1)
    
    def test_cleanup_old_corrections(self):
        """Test cleanup of old corrections."""
        # Create a correction
        self.correction_capture.capture_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="fixed test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        # Run cleanup (should not remove anything since we're keeping everything)
        cleanup_result = self.correction_capture.cleanup_old_corrections(days_to_keep=30)
        
        self.assertIn("removed_files", cleanup_result)
        self.assertIn("removed_directories", cleanup_result)
        self.assertIn("total_size_removed", cleanup_result)
        
        # Should have removed 0 files since they're new
        self.assertEqual(cleanup_result["removed_files"], 0)
    
    def test_disabled_correction_capture(self):
        """Test correction capture when disabled."""
        # Create disabled config
        disabled_config = Config({
            "correction_capture_enabled": False,
            "evaluation_storage_path": str(self.temp_path)
        })
        
        disabled_capture = CorrectionCapture(disabled_config)
        
        self.assertFalse(disabled_capture.enabled)
        
        # Should return empty string when disabled
        correction_id = disabled_capture.capture_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="fixed test",
            context={"task": "test"},
            correction_type=CorrectionType.CONTENT_CORRECTION
        )
        
        self.assertEqual(correction_id, "")


class TestCorrectionCaptureHelpers(unittest.TestCase):
    """Test helper functions for correction capture."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test storage
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock config to use temp directory
        self.config_patch = patch('claude_pm.services.correction_capture.Config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value.get.side_effect = lambda key, default=None: {
            "correction_capture_enabled": True,
            "evaluation_storage_path": str(self.temp_path),
            "correction_storage_rotation_days": 7,
            "evaluation_logging_enabled": True
        }.get(key, default)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.config_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_capture_subprocess_correction(self):
        """Test the helper function for capturing subprocess corrections."""
        correction_id = capture_subprocess_correction(
            agent_type="engineer",
            original_response="def hello(): pass",
            user_correction="def hello(): print('Hello, World!')",
            subprocess_id="test_subprocess_123",
            task_description="Create hello function",
            correction_type=CorrectionType.CONTENT_CORRECTION,
            severity="medium"
        )
        
        self.assertIsNotNone(correction_id)
        self.assertNotEqual(correction_id, "")
        self.assertTrue(correction_id.startswith("corr_"))
    
    def test_get_agent_correction_history(self):
        """Test getting agent correction history."""
        # First capture a correction
        capture_subprocess_correction(
            agent_type="engineer",
            original_response="test",
            user_correction="fixed test",
            subprocess_id="test_subprocess_123",
            task_description="Test task",
            correction_type=CorrectionType.CONTENT_CORRECTION,
            severity="medium"
        )
        
        # Get history
        history = get_agent_correction_history("engineer", limit=5)
        
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].agent_type, "engineer")
    
    def test_initialize_correction_capture_system(self):
        """Test system initialization helper."""
        init_result = initialize_correction_capture_system()
        
        self.assertTrue(init_result["initialized"])
        self.assertTrue(init_result["service_enabled"])
        self.assertIn("storage_path", init_result)
        self.assertIn("storage_integrity", init_result)
        self.assertIn("statistics", init_result)


if __name__ == "__main__":
    unittest.main()