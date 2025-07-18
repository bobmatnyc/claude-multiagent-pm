"""
Comprehensive QA Testing Suite for Async-by-Default Hook Processing Service
Tests async-by-default functionality, project-based logging, and performance benchmarks.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pm.services.hook_processing_service import (
    HookProcessingService, HookConfiguration, HookType, ErrorSeverity,
    ProjectBasedHookLogger, create_hook_processing_service, DEFAULT_CONFIG
)


class TestAsyncByDefaultHookProcessing(unittest.TestCase):
    """Test suite for async-by-default hook processing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.test_config = {
            'max_workers': 2,
            'max_history': 50,
            'max_log_files': 3,
            'max_log_size_mb': 1,
            'project_root': str(self.project_root),
            'async_by_default': True
        }
        self.service = None
        self.test_results = {
            'async_execution_count': 0,
            'sync_execution_count': 0,
            'performance_metrics': {},
            'logging_tests': {},
            'error_detections': []
        }
    
    def tearDown(self):
        """Clean up test environment."""
        if self.service:
            try:
                asyncio.run(self.service.stop())
            except Exception:
                pass
        
        # Clean up temp directory
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    async def async_setUp(self):
        """Async setup for service initialization."""
        self.service = HookProcessingService(self.test_config)
        await self.service.start()
    
    def test_async_by_default_configuration(self):
        """Test that hooks default to async execution."""
        print("\n🔍 Testing async-by-default configuration...")
        
        # Test default configuration
        config = HookConfiguration(
            hook_id='test_async_default',
            hook_type=HookType.PRE_TOOL_USE,
            handler=lambda x: "test_result"
        )
        
        # Should default to prefer_async=True and force_sync=False
        self.assertTrue(config.prefer_async, "Hooks should default to prefer_async=True")
        self.assertFalse(config.force_sync, "Hooks should default to force_sync=False")
        print("✅ Async-by-default configuration verified")
    
    def test_async_execution_behavior(self):
        """Test async execution behavior with real async functions."""
        print("\n🔍 Testing async execution behavior...")
        
        async def run_test():
            await self.async_setUp()
            
            # Test 1: Async handler should execute in async mode
            async def async_handler(context):
                await asyncio.sleep(0.01)  # Small async operation
                return f"async_result_{datetime.now().timestamp()}"
            
            async_config = HookConfiguration(
                hook_id='test_async_handler',
                hook_type=HookType.PRE_TOOL_USE,
                handler=async_handler,
                prefer_async=True
            )
            
            result = await self.service.execution_engine.execute_hook(async_config, {})
            
            self.assertTrue(result.success, "Async handler should execute successfully")
            self.assertIn('async_result_', str(result.result), "Async handler should return expected result")
            self.assertEqual(result.metadata['execution_mode'], 'async', "Should execute in async mode")
            self.assertTrue(result.metadata['is_async_handler'], "Should detect async handler")
            print(f"✅ Async handler executed successfully in {result.execution_time:.4f}s")
            
            # Test 2: Sync handler with async preference should run in executor
            def sync_handler(context):
                time.sleep(0.01)  # Small sync operation
                return f"sync_in_executor_{datetime.now().timestamp()}"
            
            sync_async_config = HookConfiguration(
                hook_id='test_sync_in_async',
                hook_type=HookType.PRE_TOOL_USE,
                handler=sync_handler,
                prefer_async=True,
                force_sync=False
            )
            
            result2 = await self.service.execution_engine.execute_hook(sync_async_config, {})
            
            self.assertTrue(result2.success, "Sync handler in async mode should execute successfully")
            self.assertIn('sync_in_executor_', str(result2.result), "Sync handler should return expected result")
            self.assertEqual(result2.metadata['execution_mode'], 'async', "Should execute in async mode via executor")
            self.assertFalse(result2.metadata['is_async_handler'], "Should detect sync handler")
            print(f"✅ Sync handler executed in async mode in {result2.execution_time:.4f}s")
            
            # Test 3: Force sync should override async preference
            force_sync_config = HookConfiguration(
                hook_id='test_force_sync',
                hook_type=HookType.PRE_TOOL_USE,
                handler=sync_handler,
                prefer_async=True,
                force_sync=True
            )
            
            result3 = await self.service.execution_engine.execute_hook(force_sync_config, {})
            
            self.assertTrue(result3.success, "Force sync should execute successfully")
            # Note: Even force_sync uses executor, but with force_sync flag set
            self.assertTrue(result3.metadata['force_sync'], "Should have force_sync flag set")
            print(f"✅ Force sync override executed in {result3.execution_time:.4f}s")
            
            self.test_results['async_execution_count'] = 3
        
        asyncio.run(run_test())
    
    def test_project_based_logging_directory_creation(self):
        """Test project-based logging directory structure creation."""
        print("\n🔍 Testing project-based logging directory creation...")
        
        logger = ProjectBasedHookLogger(project_root=str(self.project_root))
        
        # Check that directories were created
        hooks_dir = self.project_root / ".claude-pm" / "hooks"
        logs_dir = hooks_dir / "logs"
        
        self.assertTrue(hooks_dir.exists(), "Hooks directory should be created")
        self.assertTrue(logs_dir.exists(), "Logs directory should be created")
        
        # Check that subdirectories for each hook type were created
        for hook_type in HookType:
            type_dir = logs_dir / hook_type.value
            self.assertTrue(type_dir.exists(), f"Directory for {hook_type.value} should be created")
        
        print(f"✅ Directory structure created at {hooks_dir}")
        self.test_results['logging_tests']['directory_creation'] = True
    
    def test_project_based_logging_functionality(self):
        """Test project-based logging functionality."""
        print("\n🔍 Testing project-based logging functionality...")
        
        async def run_test():
            await self.async_setUp()
            
            # Create test hook that will generate logs
            async def test_logging_hook(context):
                await asyncio.sleep(0.01)
                return {"test_data": "logging_test", "timestamp": datetime.now().isoformat()}
            
            hook_config = HookConfiguration(
                hook_id='test_logging_hook',
                hook_type=HookType.PRE_TOOL_USE,
                handler=test_logging_hook,
                prefer_async=True
            )
            
            # Execute hook to generate logs
            test_context = {
                "test_execution": True,
                "log_test_data": "sample_data"
            }
            
            result = await self.service.execution_engine.execute_hook(hook_config, test_context)
            
            # Log the execution manually to test logging
            self.service.project_logger.log_hook_execution(hook_config, result, test_context)
            
            # Verify log file was created
            expected_log_file = self.service.project_logger._get_log_file_path(
                HookType.PRE_TOOL_USE, 
                'test_logging_hook'
            )
            
            self.assertTrue(expected_log_file.exists(), f"Log file should be created at {expected_log_file}")
            
            # Verify log content
            with expected_log_file.open('r') as f:
                log_content = f.read()
                log_entry = json.loads(log_content.strip())
                
                self.assertEqual(log_entry['hook_id'], 'test_logging_hook')
                self.assertEqual(log_entry['hook_type'], 'pre_tool_use')
                self.assertTrue(log_entry['success'])
                self.assertTrue(log_entry['prefer_async'])
                self.assertFalse(log_entry['force_sync'])
                self.assertIn('test_execution', log_entry['context_keys'])
            
            print(f"✅ Log entry created successfully: {expected_log_file}")
            
            # Test log retrieval
            retrieved_logs = self.service.project_logger.get_hook_logs(
                HookType.PRE_TOOL_USE, 
                'test_logging_hook'
            )
            
            self.assertEqual(len(retrieved_logs), 1, "Should retrieve one log entry")
            self.assertEqual(retrieved_logs[0]['hook_id'], 'test_logging_hook')
            
            print("✅ Log retrieval functionality verified")
            self.test_results['logging_tests']['functionality'] = True
        
        asyncio.run(run_test())
    
    def test_log_rotation_and_file_management(self):
        """Test log rotation and file management."""
        print("\n🔍 Testing log rotation and file management...")
        
        # Create logger with very small file size limit for testing
        logger = ProjectBasedHookLogger(
            project_root=str(self.project_root),
            max_log_files=2,
            max_log_size_mb=0.001  # Very small for testing rotation
        )
        
        # Create a sample hook config for testing
        hook_config = HookConfiguration(
            hook_id='rotation_test_hook',
            hook_type=HookType.ERROR_DETECTION,
            handler=lambda x: "test",
            prefer_async=True
        )
        
        # Create multiple log entries to trigger rotation
        for i in range(10):
            from claude_pm.services.hook_processing_service import HookExecutionResult
            
            result = HookExecutionResult(
                hook_id='rotation_test_hook',
                success=True,
                execution_time=0.1,
                result=f"test_result_{i}",
                metadata={'iteration': i}
            )
            
            context = {'test_data': f'large_data_entry_{i}' * 100}  # Make it large
            logger.log_hook_execution(hook_config, result, context)
        
        # Check that log files were rotated
        log_dir = logger.logs_dir / HookType.ERROR_DETECTION.value
        log_files = list(log_dir.glob("rotation_test_hook_*.log*"))
        
        # Should have rotated files due to size limit
        self.assertGreater(len(log_files), 1, "Should have multiple log files due to rotation")
        print(f"✅ Log rotation created {len(log_files)} files")
        
        # Test cleanup of old logs
        cleaned_count = logger.cleanup_old_logs(days_old=0)  # Clean all logs
        self.assertGreater(cleaned_count, 0, "Should have cleaned up some old logs")
        print(f"✅ Cleaned up {cleaned_count} old log files")
        
        self.test_results['logging_tests']['rotation'] = True
    
    def test_backward_compatibility_with_sync_configs(self):
        """Test backward compatibility with existing sync hook configurations."""
        print("\n🔍 Testing backward compatibility with sync configurations...")
        
        async def run_test():
            await self.async_setUp()
            
            # Test 1: Explicit sync configuration should still work
            def sync_handler(context):
                return "sync_result"
            
            sync_config = HookConfiguration(
                hook_id='legacy_sync_hook',
                hook_type=HookType.POST_TOOL_USE,
                handler=sync_handler,
                prefer_async=False,  # Explicitly set to sync
                force_sync=False
            )
            
            result = await self.service.execution_engine.execute_hook(sync_config, {})
            
            self.assertTrue(result.success, "Legacy sync configuration should work")
            self.assertEqual(result.result, "sync_result")
            print("✅ Legacy sync configuration compatibility verified")
            
            # Test 2: Old configurations without prefer_async should default to True
            old_style_config = HookConfiguration(
                hook_id='old_style_hook',
                hook_type=HookType.POST_TOOL_USE,
                handler=sync_handler
                # No explicit prefer_async or force_sync
            )
            
            # Default should be prefer_async=True
            self.assertTrue(old_style_config.prefer_async, "Should default to async preference")
            self.assertFalse(old_style_config.force_sync, "Should default to force_sync=False")
            
            result2 = await self.service.execution_engine.execute_hook(old_style_config, {})
            self.assertTrue(result2.success, "Old style configuration should work with new defaults")
            print("✅ Old style configuration compatibility verified")
            
            self.test_results['sync_execution_count'] = 2
        
        asyncio.run(run_test())
    
    def test_error_detection_logging(self):
        """Test error detection logging functionality."""
        print("\n🔍 Testing error detection logging...")
        
        async def run_test():
            await self.async_setUp()
            
            # Test error detection with sample problematic transcript
            problematic_transcript = """
            Documentation Agent starting...
            Processing markdown files...
            ERROR: subprocess failed with exit code 1
            Memory allocation failed
            Agent process terminated unexpectedly
            Traceback (most recent call last):
                File "agent.py", line 45, in generate_docs
            subprocess.CalledProcessError: Command failed
            """
            
            # Analyze transcript for errors
            analysis_result = await self.service.analyze_subagent_transcript(
                problematic_transcript,
                'documentation_agent'
            )
            
            self.assertTrue(analysis_result['analysis_complete'], "Analysis should complete")
            self.assertGreater(analysis_result['errors_detected'], 0, "Should detect errors in problematic transcript")
            
            # Check that error detection logs were created
            error_log_file = self.service.project_logger._get_log_file_path(
                HookType.ERROR_DETECTION,
                'error_detection'
            )
            
            self.assertTrue(error_log_file.exists(), f"Error detection log should be created at {error_log_file}")
            
            print(f"✅ Error detection logged {analysis_result['errors_detected']} errors")
            self.test_results['error_detections'].append({
                'transcript_length': len(problematic_transcript),
                'errors_detected': analysis_result['errors_detected'],
                'execution_results': len(analysis_result['execution_results'])
            })
        
        asyncio.run(run_test())
    
    def test_performance_monitoring_logs(self):
        """Test performance monitoring and logging."""
        print("\n🔍 Testing performance monitoring and logging...")
        
        async def run_test():
            await self.async_setUp()
            
            # Create performance test hooks
            async def fast_hook(context):
                await asyncio.sleep(0.01)
                return "fast_result"
            
            async def slow_hook(context):
                await asyncio.sleep(0.1)
                return "slow_result"
            
            fast_config = HookConfiguration(
                hook_id='fast_perf_hook',
                hook_type=HookType.PERFORMANCE_MONITOR,
                handler=fast_hook,
                prefer_async=True
            )
            
            slow_config = HookConfiguration(
                hook_id='slow_perf_hook',
                hook_type=HookType.PERFORMANCE_MONITOR,
                handler=slow_hook,
                prefer_async=True
            )
            
            # Register hooks
            self.service.register_hook(fast_config)
            self.service.register_hook(slow_config)
            
            # Execute hooks multiple times
            for i in range(5):
                context = {'iteration': i, 'hook_id': f'perf_test_{i}'}
                
                # Process performance monitoring hooks
                results = await self.service.process_hooks(HookType.PERFORMANCE_MONITOR, context)
                
                self.assertGreater(len(results), 0, "Should execute performance monitoring hooks")
            
            # Check performance logs
            perf_log_dir = self.service.project_logger.logs_dir / HookType.PERFORMANCE_MONITOR.value
            perf_log_files = list(perf_log_dir.glob("*.log"))
            
            self.assertGreater(len(perf_log_files), 0, "Should create performance monitoring logs")
            
            # Get performance report
            performance_report = self.service.monitoring_system.get_performance_report()
            
            self.assertIn('performance_metrics', performance_report)
            self.assertIn('recent_statistics', performance_report)
            
            print(f"✅ Performance monitoring logged to {len(perf_log_files)} files")
            print(f"   Executed {performance_report['performance_metrics']['total_hooks_executed']} hooks")
            
            self.test_results['performance_metrics'] = {
                'total_executions': performance_report['performance_metrics']['total_hooks_executed'],
                'average_time': performance_report['performance_metrics']['average_execution_time'],
                'success_rate': performance_report['recent_statistics']['success_rate']
            }
        
        asyncio.run(run_test())
    
    def test_async_vs_sync_performance_benchmark(self):
        """Benchmark performance difference between async-by-default vs sync-by-default."""
        print("\n🔍 Benchmarking async-by-default vs sync-by-default performance...")
        
        async def run_benchmark():
            # Test async-by-default performance
            async_service = HookProcessingService({
                **self.test_config,
                'async_by_default': True
            })
            await async_service.start()
            
            async def benchmark_hook(context):
                await asyncio.sleep(0.001)  # Small async operation
                return f"result_{context.get('iteration', 0)}"
            
            async_config = HookConfiguration(
                hook_id='benchmark_async_hook',
                hook_type=HookType.PRE_TOOL_USE,
                handler=benchmark_hook,
                prefer_async=True
            )
            
            # Benchmark async execution
            async_start = time.time()
            async_tasks = []
            for i in range(20):
                task = async_service.execution_engine.execute_hook(async_config, {'iteration': i})
                async_tasks.append(task)
            
            async_results = await asyncio.gather(*async_tasks)
            async_end = time.time()
            async_duration = async_end - async_start
            
            async_success_count = sum(1 for r in async_results if r.success)
            
            await async_service.stop()
            
            # Test sync-equivalent performance (force sync)
            sync_service = HookProcessingService({
                **self.test_config,
                'async_by_default': False
            })
            await sync_service.start()
            
            def sync_benchmark_hook(context):
                time.sleep(0.001)  # Small sync operation
                return f"result_{context.get('iteration', 0)}"
            
            sync_config = HookConfiguration(
                hook_id='benchmark_sync_hook',
                hook_type=HookType.PRE_TOOL_USE,
                handler=sync_benchmark_hook,
                prefer_async=False
            )
            
            # Benchmark sync execution (sequential)
            sync_start = time.time()
            sync_results = []
            for i in range(20):
                result = await sync_service.execution_engine.execute_hook(sync_config, {'iteration': i})
                sync_results.append(result)
            sync_end = time.time()
            sync_duration = sync_end - sync_start
            
            sync_success_count = sum(1 for r in sync_results if r.success)
            
            await sync_service.stop()
            
            # Calculate performance improvement
            performance_improvement = (sync_duration - async_duration) / sync_duration * 100
            
            print(f"📊 Performance Benchmark Results:")
            print(f"   Async-by-default: {async_duration:.4f}s ({async_success_count}/20 successful)")
            print(f"   Sync equivalent:  {sync_duration:.4f}s ({sync_success_count}/20 successful)")
            print(f"   Performance improvement: {performance_improvement:.1f}%")
            
            # Async should be faster for concurrent operations
            self.assertLess(async_duration, sync_duration, "Async should be faster for concurrent operations")
            self.assertEqual(async_success_count, 20, "All async executions should succeed")
            self.assertEqual(sync_success_count, 20, "All sync executions should succeed")
            
            self.test_results['performance_metrics']['benchmark'] = {
                'async_duration': async_duration,
                'sync_duration': sync_duration,
                'performance_improvement_percent': performance_improvement
            }
        
        asyncio.run(run_benchmark())
    
    def test_project_hook_summary(self):
        """Test project hook summary functionality."""
        print("\n🔍 Testing project hook summary...")
        
        async def run_test():
            await self.async_setUp()
            
            # Generate some hook activity
            test_hook = HookConfiguration(
                hook_id='summary_test_hook',
                hook_type=HookType.WORKFLOW_TRANSITION,
                handler=lambda x: "summary_test",
                prefer_async=True
            )
            
            self.service.register_hook(test_hook)
            
            # Execute hook to generate logs
            for i in range(3):
                await self.service.process_hooks(HookType.WORKFLOW_TRANSITION, {'test': i})
            
            # Get project summary
            summary = self.service.get_project_hook_summary()
            
            self.assertIn('project_root', summary)
            self.assertIn('hooks_directory', summary)
            self.assertIn('logs_directory', summary)
            self.assertIn('hook_types', summary)
            self.assertIn('total_log_files', summary)
            
            # Check that workflow_transition logs were created
            self.assertIn('workflow_transition', summary['hook_types'])
            workflow_stats = summary['hook_types']['workflow_transition']
            self.assertGreater(workflow_stats['log_files_count'], 0, "Should have created workflow transition logs")
            
            print(f"✅ Project summary generated:")
            print(f"   Project root: {summary['project_root']}")
            print(f"   Total log files: {summary['total_log_files']}")
            print(f"   Total log size: {summary['total_log_size_mb']:.2f} MB")
            
            self.test_results['logging_tests']['summary'] = summary
        
        asyncio.run(run_test())
    
    def generate_comprehensive_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        print(f"Test Environment:")
        print(f"  Project Root: {self.project_root}")
        print(f"  Temp Directory: {self.temp_dir}")
        print(f"  Configuration: {json.dumps(self.test_config, indent=2)}")
        
        print(f"\nExecution Summary:")
        print(f"  Async Executions: {self.test_results['async_execution_count']}")
        print(f"  Sync Executions: {self.test_results['sync_execution_count']}")
        
        if 'benchmark' in self.test_results['performance_metrics']:
            benchmark = self.test_results['performance_metrics']['benchmark']
            print(f"\nPerformance Benchmark:")
            print(f"  Async Duration: {benchmark['async_duration']:.4f}s")
            print(f"  Sync Duration: {benchmark['sync_duration']:.4f}s")
            print(f"  Improvement: {benchmark['performance_improvement_percent']:.1f}%")
        
        print(f"\nLogging Tests:")
        for test_name, result in self.test_results['logging_tests'].items():
            print(f"  {test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
        
        print(f"\nError Detection:")
        for detection in self.test_results['error_detections']:
            print(f"  Transcript Length: {detection['transcript_length']}")
            print(f"  Errors Detected: {detection['errors_detected']}")
            print(f"  Execution Results: {detection['execution_results']}")
        
        # Save detailed report
        report_file = self.project_root / "qa_test_report.json"
        with report_file.open('w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'test_config': self.test_config,
                'test_results': self.test_results,
                'project_structure': {
                    'claude_pm_dir': str(self.project_root / ".claude-pm"),
                    'hooks_dir': str(self.project_root / ".claude-pm" / "hooks"),
                    'logs_dir': str(self.project_root / ".claude-pm" / "hooks" / "logs")
                }
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        return report_file


def run_comprehensive_qa_testing():
    """Run all comprehensive QA tests."""
    print("🚀 Starting Comprehensive QA Testing for Async-by-Default Hook Processing")
    print("=" * 80)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test suite
    test_suite = TestAsyncByDefaultHookProcessing()
    test_suite.setUp()
    
    try:
        # Run all tests
        test_suite.test_async_by_default_configuration()
        test_suite.test_async_execution_behavior()
        test_suite.test_project_based_logging_directory_creation()
        test_suite.test_project_based_logging_functionality()
        test_suite.test_log_rotation_and_file_management()
        test_suite.test_backward_compatibility_with_sync_configs()
        test_suite.test_error_detection_logging()
        test_suite.test_performance_monitoring_logs()
        test_suite.test_async_vs_sync_performance_benchmark()
        test_suite.test_project_hook_summary()
        
        # Generate comprehensive report
        report_file = test_suite.generate_comprehensive_test_report()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"📊 Comprehensive report available at: {report_file}")
        
        return True, report_file
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None
        
    finally:
        test_suite.tearDown()


if __name__ == "__main__":
    success, report_file = run_comprehensive_qa_testing()
    exit(0 if success else 1)