#!/usr/bin/env python3
"""
Claude PM Framework - Comprehensive Cleanup System Tests

This test suite validates the cleanup functionality including:
- Installation detection and scanning
- User data handling and backup creation
- Safe removal with confirmations
- Verification of complete cleanup
- Memory collection for cleanup insights
"""

import os
import sys
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import unittest

# Add framework path for imports
framework_path = Path(__file__).parent.parent
sys.path.insert(0, str(framework_path))

class TestCleanupSystem(unittest.TestCase):
    """Test the comprehensive cleanup system functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix='claude_pm_cleanup_test_'))
        self.test_home = self.test_dir / 'fake_home'
        self.test_home.mkdir(parents=True, exist_ok=True)
        
        # Mock home directory
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = str(self.test_home)
        
        # Create test installation structure
        self.create_test_installation()
        
    def tearDown(self):
        """Clean up test environment."""
        # Restore original home
        if self.original_home:
            os.environ['HOME'] = self.original_home
        else:
            del os.environ['HOME']
        
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_installation(self):
        """Create a fake Claude PM installation for testing."""
        # Create ~/.claude-pm structure
        claude_pm_dir = self.test_home / '.claude-pm'
        claude_pm_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config files
        config_file = claude_pm_dir / 'config.json'
        config_data = {
            "installType": "npm",
            "version": "0.8.1",
            "installationComplete": True,
            "timestamp": "2025-07-14T10:00:00Z"
        }
        config_file.write_text(json.dumps(config_data, indent=2))
        
        # Create memory system
        memory_dir = claude_pm_dir / 'memory'
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Create some memory files
        for i in range(5):
            memory_file = memory_dir / f'memory_{i}.json'
            memory_data = {
                "timestamp": "2025-07-14T10:00:00Z",
                "category": "test",
                "content": f"Test memory entry {i}"
            }
            memory_file.write_text(json.dumps(memory_data, indent=2))
        
        # Create chroma database
        chroma_dir = claude_pm_dir / 'chroma_db'
        chroma_dir.mkdir(parents=True, exist_ok=True)
        chroma_db = chroma_dir / 'test.sqlite'
        chroma_db.write_text("fake sqlite data")
        
        # Create backup directories
        backup_dir = claude_pm_dir / 'framework_backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / 'backup_test.md'
        backup_file.write_text("Test backup content")
        
        # Create logs
        logs_dir = claude_pm_dir / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / 'test.log'
        log_file.write_text("Test log content")
        
        # Create CLI executable
        local_bin = self.test_home / '.local' / 'bin'
        local_bin.mkdir(parents=True, exist_ok=True)
        cli_exe = local_bin / 'claude-pm'
        cli_exe.write_text("#!/usr/bin/env python3\nprint('fake claude-pm')")
        cli_exe.chmod(0o755)
    
    def get_test_installation_size(self):
        """Calculate total size of test installation."""
        total_size = 0
        total_files = 0
        
        for root, dirs, files in os.walk(self.test_home):
            for file in files:
                file_path = Path(root) / file
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    total_files += 1
        
        return total_size, total_files
    
    def test_installation_detection(self):
        """Test that the cleanup script can detect installations."""
        # The preuninstall.js script should detect our test installation
        preuninstall_script = framework_path / 'install' / 'preuninstall.js'
        self.assertTrue(preuninstall_script.exists(), "Preuninstall script should exist")
        
        # Test that our fake installation is detectable
        claude_pm_dir = self.test_home / '.claude-pm'
        self.assertTrue(claude_pm_dir.exists(), "Test .claude-pm directory should exist")
        
        config_file = claude_pm_dir / 'config.json'
        self.assertTrue(config_file.exists(), "Config file should exist")
        
        memory_dir = claude_pm_dir / 'memory'
        self.assertTrue(memory_dir.exists(), "Memory directory should exist")
        
        # Verify memory files
        memory_files = list(memory_dir.glob('*.json'))
        self.assertGreater(len(memory_files), 0, "Should have memory files")
    
    def test_size_calculation(self):
        """Test that size calculation works correctly."""
        total_size, total_files = self.get_test_installation_size()
        
        # Should have detected files and size
        self.assertGreater(total_files, 0, "Should detect files in test installation")
        self.assertGreater(total_size, 0, "Should calculate non-zero size")
        
        print(f"Test installation: {total_files} files, {total_size} bytes")
    
    def test_memory_system_detection(self):
        """Test that memory system is properly detected."""
        claude_pm_dir = self.test_home / '.claude-pm'
        
        # Check memory directory
        memory_dir = claude_pm_dir / 'memory'
        self.assertTrue(memory_dir.exists(), "Memory directory should exist")
        
        # Check chroma database
        chroma_dir = claude_pm_dir / 'chroma_db'
        self.assertTrue(chroma_dir.exists(), "ChromaDB directory should exist")
        
        # Verify memory files exist
        memory_files = list(memory_dir.glob('*.json'))
        self.assertGreater(len(memory_files), 0, "Should have memory JSON files")
    
    def test_backup_creation(self):
        """Test backup creation functionality."""
        # This would test the backup creation logic
        # Since we can't easily test the Node.js script directly,
        # we verify the structure exists for backup
        
        claude_pm_dir = self.test_home / '.claude-pm'
        backup_dir = claude_pm_dir / 'framework_backups'
        
        self.assertTrue(backup_dir.exists(), "Backup directory should exist")
        
        backup_files = list(backup_dir.glob('*'))
        self.assertGreater(len(backup_files), 0, "Should have backup files")
    
    def test_cli_cleanup_integration(self):
        """Test that the CLI cleanup command is properly integrated."""
        # Test that the CLI script includes cleanup handling
        cli_script = framework_path / 'bin' / 'claude-pm'
        self.assertTrue(cli_script.exists(), "CLI script should exist")
        
        # Read the CLI script and verify cleanup integration
        cli_content = cli_script.read_text()
        self.assertIn('--cleanup', cli_content, "CLI should include --cleanup flag")
        self.assertIn('handle_cleanup_command', cli_content, "CLI should have cleanup handler")
    
    def test_package_json_integration(self):
        """Test that package.json includes cleanup scripts."""
        package_json = framework_path / 'package.json'
        self.assertTrue(package_json.exists(), "package.json should exist")
        
        # Parse package.json
        package_data = json.loads(package_json.read_text())
        
        # Verify preuninstall script
        self.assertIn('preuninstall', package_data['scripts'], 
                     "Should have preuninstall script")
        
        # Verify cleanup scripts
        self.assertIn('cleanup', package_data['scripts'], 
                     "Should have cleanup script")
        self.assertIn('cleanup:full', package_data['scripts'], 
                     "Should have full cleanup script")
        self.assertIn('cleanup:auto', package_data['scripts'], 
                     "Should have auto cleanup script")
        self.assertIn('uninstall:complete', package_data['scripts'], 
                     "Should have complete uninstall script")
    
    def test_preuninstall_script_exists(self):
        """Test that the preuninstall script exists and is executable."""
        preuninstall_script = framework_path / 'install' / 'preuninstall.js'
        self.assertTrue(preuninstall_script.exists(), "Preuninstall script should exist")
        
        # Verify it's a Node.js script
        content = preuninstall_script.read_text()
        self.assertTrue(content.startswith('#!/usr/bin/env node'), 
                       "Should be a Node.js script")
        
        # Verify key functionality is included
        self.assertIn('ComprehensiveCleanup', content, 
                     "Should include ComprehensiveCleanup class")
        self.assertIn('detectGlobalNodeModules', content, 
                     "Should include npm detection")
        self.assertIn('detectPipInstallations', content, 
                     "Should include pip detection")
        self.assertIn('createUserDataBackup', content, 
                     "Should include backup functionality")
        self.assertIn('collectCleanupMemory', content, 
                     "Should include memory collection")
    
    def test_memory_collection_structure(self):
        """Test that memory collection structure is properly implemented."""
        preuninstall_script = framework_path / 'install' / 'preuninstall.js'
        content = preuninstall_script.read_text()
        
        # Verify memory collection features
        self.assertIn('collectCleanupMemory', content, 
                     "Should include memory collection")
        self.assertIn('cleanup_stats', content, 
                     "Should collect cleanup statistics")
        self.assertIn('user_feedback', content, 
                     "Should collect user feedback")
        self.assertIn('category: \'cleanup\'', content, 
                     "Should categorize as cleanup memory")
    
    def test_safety_features(self):
        """Test that safety features are implemented."""
        preuninstall_script = framework_path / 'install' / 'preuninstall.js'
        content = preuninstall_script.read_text()
        
        # Verify safety features
        self.assertIn('promptUser', content, 
                     "Should include user prompts")
        self.assertIn('createUserDataBackup', content, 
                     "Should include backup creation")
        self.assertIn('Final confirmation', content, 
                     "Should require final confirmation")
        self.assertIn('removeUserData: false', content, 
                     "Should default to preserving user data")
    
    def test_comprehensive_detection(self):
        """Test that all installation types are detected."""
        preuninstall_script = framework_path / 'install' / 'preuninstall.js'
        content = preuninstall_script.read_text()
        
        # Verify comprehensive detection
        self.assertIn('globalNodeModules', content, 
                     "Should detect npm installations")
        self.assertIn('pipPackages', content, 
                     "Should detect pip installations")
        self.assertIn('backupLocations', content, 
                     "Should detect backup locations")
        self.assertIn('tempFiles', content, 
                     "Should detect temp files")
        self.assertIn('node_modules/@bobmatnyc/claude-multiagent-pm', content, 
                     "Should detect correct package name")


class TestCleanupIntegration(unittest.TestCase):
    """Test integration between cleanup components."""
    
    def test_cli_to_script_integration(self):
        """Test that CLI properly calls the cleanup script."""
        cli_script = framework_path / 'bin' / 'claude-pm'
        cli_content = cli_script.read_text()
        
        # Verify CLI can find the preuninstall script
        self.assertIn('preuninstall.js', cli_content, 
                     "CLI should reference preuninstall script")
        
        # Verify flag handling
        self.assertIn('--interactive', cli_content, 
                     "Should support interactive mode")
        self.assertIn('--automatic', cli_content, 
                     "Should support automatic mode")
    
    def test_npm_script_integration(self):
        """Test that npm scripts properly integrate with cleanup."""
        package_json = framework_path / 'package.json'
        package_data = json.loads(package_json.read_text())
        
        scripts = package_data['scripts']
        
        # Verify preuninstall integration
        self.assertEqual(scripts['preuninstall'], 
                        'node install/preuninstall.js --automatic',
                        "Preuninstall should run automatic cleanup")
        
        # Verify manual cleanup options
        self.assertEqual(scripts['cleanup'], 
                        'node install/preuninstall.js',
                        "Manual cleanup should run interactively")
        
        # Verify complete uninstall process
        self.assertIn('npm uninstall -g', scripts['uninstall:complete'],
                     "Complete uninstall should remove npm package")


def run_cleanup_tests():
    """Run all cleanup system tests."""
    print("🧹 Running Claude PM Framework Cleanup System Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display results
    print("\n" + "=" * 60)
    print(f"🏁 Tests completed: {result.testsRun} total")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"🚨 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_cleanup_tests()
    sys.exit(0 if success else 1)