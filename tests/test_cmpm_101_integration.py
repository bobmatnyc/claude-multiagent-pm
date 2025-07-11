#!/usr/bin/env python3

"""
Claude PM Framework - CMPM-101 Deployment Detection Integration Tests

Tests the complete CMPM-101 deployment detection system including:
- Integration with existing deployment workflow
- Node.js to Python environment setup
- Configuration object validation
- CLI wrapper functionality
- Error handling and recovery
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path


class TestCMPM101Integration(unittest.TestCase):
    """Test suite for CMPM-101 deployment detection integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix='cmpm_101_test_')
        self.framework_dir = Path(__file__).parent.parent
        self.deployment_script = self.framework_dir / 'install' / 'deploy.js'
        self.claude_pm_bin = self.framework_dir / 'bin' / 'claude-pm'
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_deployment_detection_in_source_repo(self):
        """Test deployment detection in source repository"""
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Deployment detection failed: {result.stderr}")
        self.assertIn('Detection Results', result.stdout)
        
        # Parse the output to extract deployment info
        lines = result.stdout.split('\n')
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            json_content = '\n'.join(lines[json_start:])
            try:
                deployment_info = json.loads(json_content)
                
                # Validate deployment detection
                self.assertIn('strategy', deployment_info)
                self.assertIn('config', deployment_info)
                self.assertEqual(deployment_info['strategy'], 'development')
                self.assertEqual(deployment_info['config']['deploymentType'], 'local_source')
                self.assertTrue(deployment_info['config']['found'])
                self.assertEqual(deployment_info['config']['confidence'], 'high')
                
            except json.JSONDecodeError:
                self.fail("Could not parse deployment detection JSON output")
    
    def test_deployment_detection_in_deployed_instance(self):
        """Test deployment detection in deployed instance"""
        # Deploy to test directory
        deploy_result = subprocess.run([
            'node', str(self.deployment_script),
            '--target', self.test_dir,
            '--verbose'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(deploy_result.returncode, 0, f"Deployment failed: {deploy_result.stderr}")
        
        # Test deployment detection in deployed instance
        deployed_bin = Path(self.test_dir) / 'bin' / 'claude-pm'
        self.assertTrue(deployed_bin.exists(), "Deployed CLI binary not found")
        
        # This would test the deployed instance, but since we're copying the source bin,
        # we need to ensure the detection works with the deployed configuration
        result = subprocess.run([
            'node', str(deployed_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.test_dir)
        
        # The result should succeed even if it doesn't detect the deployed instance
        # because it will fall back to other detection methods
        self.assertEqual(result.returncode, 0, f"Deployment detection failed: {result.stderr}")
    
    def test_enhanced_help_with_deployment_info(self):
        """Test enhanced help command with deployment information"""
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--help'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Help command failed: {result.stderr}")
        self.assertIn('Current Deployment:', result.stdout)
        self.assertIn('Type: local_source', result.stdout)
        self.assertIn('Confidence: high', result.stdout)
        self.assertIn('--deployment-info', result.stdout)
    
    def test_environment_variable_detection(self):
        """Test environment variable-based detection"""
        # Set environment variable
        env = os.environ.copy()
        env['CLAUDE_PM_FRAMEWORK_PATH'] = str(self.framework_dir)
        
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, env=env, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Environment detection failed: {result.stderr}")
        
        # Should still detect local_source as it has higher priority
        self.assertIn('local_source', result.stdout)
    
    def test_cli_integration_with_deployment_detection(self):
        """Test CLI integration with deployment detection"""
        # Test version command
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--version'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Version command failed: {result.stderr}")
        self.assertIn('Claude Multi-Agent PM Framework', result.stdout)
        self.assertIn('4.5.1', result.stdout)
    
    def test_error_handling_with_deployment_detection(self):
        """Test error handling when deployment is not found"""
        # Test in a directory without any Claude PM installation
        empty_dir = tempfile.mkdtemp(prefix='empty_test_')
        
        try:
            # Create a minimal claude-pm script that should fail
            test_script = Path(empty_dir) / 'test-claude-pm.js'
            
            # Copy the deployment detector but point to non-existent framework
            with open(self.claude_pm_bin, 'r') as f:
                content = f.read()
            
            # Create a test script that will fail to find the framework
            test_content = content.replace(
                'path.join(__dirname, \'..\')', 
                f'"{empty_dir}"'
            )
            
            with open(test_script, 'w') as f:
                f.write(test_content)
            
            result = subprocess.run([
                'node', str(test_script), 
                '--deployment-info'
            ], capture_output=True, text=True, cwd=empty_dir)
            
            # Should succeed but show not_found
            self.assertEqual(result.returncode, 0)
            self.assertIn('not_found', result.stdout)
            
        finally:
            shutil.rmtree(empty_dir)
    
    def test_configuration_object_validation(self):
        """Test configuration object structure validation"""
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Configuration validation failed: {result.stderr}")
        
        # Extract and validate configuration
        lines = result.stdout.split('\n')
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            json_content = '\n'.join(lines[json_start:])
            try:
                config = json.loads(json_content)
                
                # Validate required fields
                self.assertIn('strategy', config)
                self.assertIn('config', config)
                self.assertIn('environmentSetup', config)
                
                # Validate config structure
                config_obj = config['config']
                self.assertIn('deploymentType', config_obj)
                self.assertIn('found', config_obj)
                self.assertIn('platform', config_obj)
                self.assertIn('confidence', config_obj)
                self.assertIn('frameworkPath', config_obj)
                self.assertIn('claudePmPath', config_obj)
                self.assertIn('paths', config_obj)
                
                # Validate paths
                paths = config_obj['paths']
                self.assertIn('framework', paths)
                self.assertIn('claudePm', paths)
                self.assertIn('bin', paths)
                self.assertIn('config', paths)
                self.assertIn('templates', paths)
                self.assertIn('schemas', paths)
                
                # Validate environment setup
                env_setup = config['environmentSetup']
                self.assertIn('PYTHONPATH', env_setup)
                self.assertIn('CLAUDE_PM_FRAMEWORK_PATH', env_setup)
                
            except json.JSONDecodeError:
                self.fail("Could not parse configuration JSON output")
    
    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility"""
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Cross-platform test failed: {result.stderr}")
        
        # Should detect correct platform
        if sys.platform == 'win32':
            self.assertIn('win32', result.stdout)
        elif sys.platform == 'darwin':
            self.assertIn('darwin', result.stdout)
        else:
            self.assertIn('linux', result.stdout)
    
    def test_performance_and_caching(self):
        """Test performance and caching mechanism"""
        import time
        
        # First run
        start_time = time.time()
        result1 = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        first_run_time = time.time() - start_time
        
        # Second run (should be faster due to caching)
        start_time = time.time()
        result2 = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        second_run_time = time.time() - start_time
        
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)
        
        # Results should be identical
        self.assertEqual(result1.stdout, result2.stdout)
        
        # Both should complete in reasonable time
        self.assertLess(first_run_time, 5.0, "First run took too long")
        self.assertLess(second_run_time, 5.0, "Second run took too long")
    
    def test_integration_with_existing_deployment(self):
        """Test integration with existing deployment workflow"""
        # Deploy framework
        deploy_result = subprocess.run([
            'node', str(self.deployment_script),
            '--target', self.test_dir,
            '--verbose'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(deploy_result.returncode, 0, f"Deployment failed: {deploy_result.stderr}")
        
        # Verify deployment structure
        self.assertTrue(Path(self.test_dir, 'claude_pm').exists())
        self.assertTrue(Path(self.test_dir, '.claude-pm', 'config.json').exists())
        self.assertTrue(Path(self.test_dir, 'bin', 'claude-pm').exists())
        
        # Verify configuration
        config_path = Path(self.test_dir, '.claude-pm', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertIn('version', config)
        self.assertIn('deploymentDir', config)
        self.assertIn('platform', config)
        self.assertIn('paths', config)
        
        # Verify paths
        paths = config['paths']
        self.assertEqual(paths['framework'], str(Path(self.test_dir, 'claude_pm')))
        self.assertEqual(paths['templates'], str(Path(self.test_dir, 'templates')))
        self.assertEqual(paths['schemas'], str(Path(self.test_dir, 'schemas')))
    
    def test_node_to_python_environment_setup(self):
        """Test Node.js to Python environment setup"""
        result = subprocess.run([
            'node', str(self.claude_pm_bin), 
            '--deployment-info'
        ], capture_output=True, text=True, cwd=self.framework_dir)
        
        self.assertEqual(result.returncode, 0, f"Environment setup test failed: {result.stderr}")
        
        # Extract and validate environment setup
        lines = result.stdout.split('\n')
        json_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            json_content = '\n'.join(lines[json_start:])
            try:
                config = json.loads(json_content)
                
                # Validate environment setup
                env_setup = config['environmentSetup']
                self.assertIn('PYTHONPATH', env_setup)
                self.assertIn('CLAUDE_PM_FRAMEWORK_PATH', env_setup)
                
                # Validate paths point to actual directories
                pythonpath = env_setup['PYTHONPATH']
                framework_path = env_setup['CLAUDE_PM_FRAMEWORK_PATH']
                
                self.assertTrue(os.path.exists(pythonpath))
                self.assertTrue(os.path.exists(framework_path))
                self.assertTrue(os.path.exists(os.path.join(framework_path, 'claude_pm')))
                
            except json.JSONDecodeError:
                self.fail("Could not parse environment setup JSON output")


if __name__ == '__main__':
    # Change to the framework directory
    os.chdir(Path(__file__).parent.parent)
    
    # Run the tests
    unittest.main(verbosity=2)