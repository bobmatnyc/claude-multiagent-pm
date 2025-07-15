"""
Practical examples and utilities for hook processing service integration.
Demonstrates real-world usage patterns and best practices.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .hook_processing_service import (
    HookProcessingService, HookConfiguration, HookType, ErrorSeverity,
    SubagentStopHookExample, create_hook_processing_service
)


class AgentIntegrationHooks:
    """Practical hooks for agent integration scenarios."""
    
    def __init__(self, service: HookProcessingService):
        self.service = service
        self.logger = logging.getLogger(__name__)
        self.integration_stats = {
            'agents_monitored': 0,
            'errors_prevented': 0,
            'restarts_triggered': 0,
            'last_updated': datetime.now()
        }
    
    async def setup_documentation_agent_hooks(self):
        """Setup hooks specific to documentation agent monitoring."""
        # Pre-tool use hook for documentation tasks
        await self._register_hook(
            'doc_agent_pre_tool',
            HookType.PRE_TOOL_USE,
            self._handle_doc_agent_pre_tool,
            priority=90
        )
        
        # Post-tool use hook for documentation validation
        await self._register_hook(
            'doc_agent_post_tool',
            HookType.POST_TOOL_USE,
            self._handle_doc_agent_post_tool,
            priority=85
        )
        
        # Error detection for documentation-specific issues
        await self._register_hook(
            'doc_agent_error_detection',
            HookType.ERROR_DETECTION,
            self._handle_doc_agent_errors,
            priority=80
        )
    
    async def setup_qa_agent_hooks(self):
        """Setup hooks specific to QA agent monitoring."""
        await self._register_hook(
            'qa_agent_pre_test',
            HookType.PRE_TOOL_USE,
            self._handle_qa_agent_pre_test,
            priority=95
        )
        
        await self._register_hook(
            'qa_agent_post_test',
            HookType.POST_TOOL_USE,
            self._handle_qa_agent_post_test,
            priority=90
        )
        
        await self._register_hook(
            'qa_agent_failure_detection',
            HookType.SUBAGENT_STOP,
            self._handle_qa_agent_failures,
            priority=100
        )
    
    async def setup_version_control_hooks(self):
        """Setup hooks specific to version control agent monitoring."""
        await self._register_hook(
            'vc_agent_pre_git',
            HookType.PRE_TOOL_USE,
            self._handle_vc_agent_pre_git,
            priority=85
        )
        
        await self._register_hook(
            'vc_agent_post_git',
            HookType.POST_TOOL_USE,
            self._handle_vc_agent_post_git,
            priority=80
        )
        
        await self._register_hook(
            'vc_agent_conflict_detection',
            HookType.ERROR_DETECTION,
            self._handle_vc_agent_conflicts,
            priority=90
        )
    
    async def _register_hook(self, hook_id: str, hook_type: HookType, handler, priority: int = 50, prefer_async: bool = True):
        """Helper to register hooks with standard configuration."""
        config = HookConfiguration(
            hook_id=hook_id,
            hook_type=hook_type,
            handler=handler,
            priority=priority,
            timeout=15.0,
            retry_count=2,
            prefer_async=prefer_async
        )
        
        success = self.service.register_hook(config)
        if success:
            self.logger.info(f"Registered hook: {hook_id}")
        else:
            self.logger.error(f"Failed to register hook: {hook_id}")
    
    async def _handle_doc_agent_pre_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation agent pre-tool execution."""
        tool_name = context.get('tool_name', 'unknown')
        agent_context = context.get('agent_context', {})
        
        # Validate documentation context
        validation_results = {
            'context_valid': True,
            'warnings': [],
            'recommendations': []
        }
        
        # Check for required documentation context
        required_fields = ['project_root', 'documentation_type', 'target_audience']
        for field in required_fields:
            if field not in agent_context:
                validation_results['warnings'].append(f"Missing required field: {field}")
                validation_results['context_valid'] = False
        
        # Check for large documentation tasks
        if tool_name in ['generate_full_docs', 'create_api_docs']:
            validation_results['recommendations'].append(
                "Consider breaking large documentation tasks into smaller chunks"
            )
        
        return validation_results
    
    async def _handle_doc_agent_post_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation agent post-tool execution."""
        tool_result = context.get('tool_result', {})
        execution_time = context.get('execution_time', 0.0)
        
        # Validate documentation output
        validation_results = {
            'output_valid': True,
            'quality_metrics': {},
            'issues': []
        }
        
        # Check for documentation quality indicators
        if isinstance(tool_result, dict) and 'content' in tool_result:
            content = tool_result['content']
            validation_results['quality_metrics'] = {
                'length': len(content),
                'has_headings': '# ' in content or '## ' in content,
                'has_code_blocks': '```' in content,
                'has_links': '[' in content and '](' in content
            }
        
        # Performance check
        if execution_time > 60.0:
            validation_results['issues'].append(
                f"Documentation generation took {execution_time:.2f}s - consider optimization"
            )
        
        return validation_results
    
    async def _handle_doc_agent_errors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation agent error detection."""
        transcript = context.get('transcript', '')
        
        # Documentation-specific error patterns
        doc_errors = []
        
        error_patterns = [
            (r'markdown\s+(?:parse|syntax)\s+error', 'markdown_syntax_error'),
            (r'template\s+(?:not\s+found|error)', 'template_error'),
            (r'documentation\s+build\s+failed', 'build_failure'),
            (r'missing\s+(?:reference|link|image)', 'missing_reference'),
            (r'invalid\s+(?:yaml|json)\s+frontmatter', 'frontmatter_error')
        ]
        
        for pattern, error_type in error_patterns:
            import re
            if re.search(pattern, transcript, re.IGNORECASE):
                doc_errors.append({
                    'type': error_type,
                    'pattern': pattern,
                    'severity': 'medium',
                    'suggested_action': 'validate_documentation_syntax'
                })
        
        return {
            'documentation_errors': len(doc_errors),
            'errors': doc_errors,
            'recommendations': [
                'Run documentation linter',
                'Validate all links and references',
                'Check template syntax'
            ] if doc_errors else []
        }
    
    async def _handle_qa_agent_pre_test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle QA agent pre-test execution."""
        test_config = context.get('test_config', {})
        
        # Validate test configuration
        validation_results = {
            'config_valid': True,
            'test_warnings': [],
            'performance_tips': []
        }
        
        # Check for test configuration issues
        if 'test_paths' not in test_config:
            validation_results['test_warnings'].append("No test paths specified")
            validation_results['config_valid'] = False
        
        # Check for performance optimization opportunities
        if test_config.get('parallel_execution', False):
            validation_results['performance_tips'].append(
                "Parallel execution enabled - monitor resource usage"
            )
        
        return validation_results
    
    async def _handle_qa_agent_post_test(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle QA agent post-test execution."""
        test_results = context.get('test_results', {})
        
        # Analyze test results
        analysis_results = {
            'tests_passed': test_results.get('passed', 0),
            'tests_failed': test_results.get('failed', 0),
            'coverage_percentage': test_results.get('coverage', 0.0),
            'quality_score': 0.0,
            'recommendations': []
        }
        
        # Calculate quality score
        total_tests = analysis_results['tests_passed'] + analysis_results['tests_failed']
        if total_tests > 0:
            pass_rate = analysis_results['tests_passed'] / total_tests
            coverage_factor = analysis_results['coverage_percentage'] / 100.0
            analysis_results['quality_score'] = (pass_rate * 0.7) + (coverage_factor * 0.3)
        
        # Generate recommendations
        if analysis_results['tests_failed'] > 0:
            analysis_results['recommendations'].append(
                f"Address {analysis_results['tests_failed']} failing tests"
            )
        
        if analysis_results['coverage_percentage'] < 80.0:
            analysis_results['recommendations'].append(
                f"Improve test coverage (current: {analysis_results['coverage_percentage']:.1f}%)"
            )
        
        return analysis_results
    
    async def _handle_qa_agent_failures(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle QA agent failure detection."""
        transcript = context.get('transcript', '')
        
        # QA-specific failure patterns
        qa_failures = []
        
        failure_patterns = [
            (r'test\s+runner\s+(?:crashed|failed)', 'test_runner_failure'),
            (r'pytest\s+(?:error|exception)', 'pytest_error'),
            (r'test\s+timeout', 'test_timeout'),
            (r'assertion\s+error', 'assertion_failure'),
            (r'test\s+environment\s+setup\s+failed', 'environment_failure'),
            (r'coverage\s+report\s+generation\s+failed', 'coverage_failure')
        ]
        
        for pattern, failure_type in failure_patterns:
            import re
            if re.search(pattern, transcript, re.IGNORECASE):
                qa_failures.append({
                    'type': failure_type,
                    'pattern': pattern,
                    'severity': 'high',
                    'suggested_action': 'restart_test_runner'
                })
        
        # Update integration stats
        if qa_failures:
            self.integration_stats['restarts_triggered'] += 1
            self.integration_stats['last_updated'] = datetime.now()
        
        return {
            'qa_failures': len(qa_failures),
            'failures': qa_failures,
            'restart_recommended': len(qa_failures) > 0
        }
    
    async def _handle_vc_agent_pre_git(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle version control agent pre-Git execution."""
        git_command = context.get('git_command', '')
        repo_state = context.get('repo_state', {})
        
        # Validate Git operation
        validation_results = {
            'command_safe': True,
            'warnings': [],
            'preconditions': []
        }
        
        # Check for potentially dangerous operations
        dangerous_commands = ['reset --hard', 'push --force', 'rebase -i']
        for cmd in dangerous_commands:
            if cmd in git_command:
                validation_results['warnings'].append(f"Dangerous command detected: {cmd}")
                validation_results['command_safe'] = False
        
        # Check repository state
        if repo_state.get('has_uncommitted_changes', False):
            validation_results['preconditions'].append(
                "Repository has uncommitted changes - consider stashing"
            )
        
        return validation_results
    
    async def _handle_vc_agent_post_git(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle version control agent post-Git execution."""
        git_result = context.get('git_result', {})
        command_success = context.get('command_success', False)
        
        # Analyze Git operation result
        analysis_results = {
            'operation_successful': command_success,
            'repo_changes': [],
            'next_steps': []
        }
        
        # Analyze changes made
        if command_success and 'output' in git_result:
            output = git_result['output']
            
            # Detect common Git operation results
            if 'files changed' in output:
                analysis_results['repo_changes'].append('Files modified')
            if 'create mode' in output:
                analysis_results['repo_changes'].append('New files created')
            if 'delete mode' in output:
                analysis_results['repo_changes'].append('Files deleted')
            if 'Fast-forward' in output:
                analysis_results['repo_changes'].append('Fast-forward merge')
        
        # Generate next steps
        if not command_success:
            analysis_results['next_steps'].append('Investigate Git error')
        elif 'push' in context.get('git_command', ''):
            analysis_results['next_steps'].append('Verify remote repository state')
        
        return analysis_results
    
    async def _handle_vc_agent_conflicts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle version control agent conflict detection."""
        transcript = context.get('transcript', '')
        
        # Version control conflict patterns
        vc_conflicts = []
        
        conflict_patterns = [
            (r'merge\s+conflict', 'merge_conflict'),
            (r'rebase\s+conflict', 'rebase_conflict'),
            (r'push\s+rejected', 'push_rejected'),
            (r'non-fast-forward', 'non_fast_forward'),
            (r'working\s+tree\s+is\s+dirty', 'dirty_working_tree'),
            (r'branch\s+.*\s+not\s+found', 'branch_not_found')
        ]
        
        for pattern, conflict_type in conflict_patterns:
            import re
            if re.search(pattern, transcript, re.IGNORECASE):
                vc_conflicts.append({
                    'type': conflict_type,
                    'pattern': pattern,
                    'severity': 'medium',
                    'suggested_action': 'resolve_conflict_manually'
                })
        
        return {
            'version_control_conflicts': len(vc_conflicts),
            'conflicts': vc_conflicts,
            'manual_resolution_required': len(vc_conflicts) > 0
        }
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            **self.integration_stats,
            'service_status': self.service.get_service_status()
        }


class HookProcessingDemo:
    """Demonstration of hook processing service capabilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service: Optional[HookProcessingService] = None
        self.integration_hooks: Optional[AgentIntegrationHooks] = None
    
    async def setup_demo_environment(self):
        """Setup demonstration environment."""
        self.logger.info("Setting up hook processing demo environment...")
        
        # Create hook processing service
        config = {
            'max_workers': 2,
            'max_history': 100,
            'max_log_files': 5,
            'max_log_size_mb': 5,
            'project_root': None,  # Use current working directory
            'alert_thresholds': {
                'execution_time': 5.0,
                'error_rate': 0.2,
                'failure_rate': 0.1
            },
            'async_by_default': True
        }
        
        self.service = await create_hook_processing_service(config)
        
        # Setup integration hooks
        self.integration_hooks = AgentIntegrationHooks(self.service)
        await self.integration_hooks.setup_documentation_agent_hooks()
        await self.integration_hooks.setup_qa_agent_hooks()
        await self.integration_hooks.setup_version_control_hooks()
        
        self.logger.info("Demo environment setup complete")
    
    async def demonstrate_subagent_stop_detection(self):
        """Demonstrate SubagentStop error detection."""
        self.logger.info("Demonstrating SubagentStop error detection...")
        
        # Sample problematic transcript
        problematic_transcript = """
        Documentation Agent starting...
        Processing markdown files...
        ERROR: subprocess failed with exit code 1
        Memory allocation failed
        Agent process terminated unexpectedly
        Traceback (most recent call last):
            File "agent.py", line 45, in generate_docs
                result = subprocess.run(cmd, check=True)
        subprocess.CalledProcessError: Command failed
        """
        
        # Analyze transcript
        analysis_result = await self.service.analyze_subagent_transcript(
            problematic_transcript, 
            'documentation_agent'
        )
        
        self.logger.info(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
        
        # Demonstrate error-free transcript
        clean_transcript = """
        Documentation Agent starting...
        Processing markdown files...
        Generated 15 documentation files
        All operations completed successfully
        Documentation Agent finished
        """
        
        clean_analysis = await self.service.analyze_subagent_transcript(
            clean_transcript, 
            'documentation_agent'
        )
        
        self.logger.info(f"Clean analysis result: {json.dumps(clean_analysis, indent=2)}")
    
    async def demonstrate_hook_execution(self):
        """Demonstrate hook execution with various scenarios."""
        self.logger.info("Demonstrating hook execution scenarios...")
        
        # Test documentation agent hooks
        doc_context = {
            'tool_name': 'generate_api_docs',
            'agent_context': {
                'project_root': '/tmp/test_project',
                'documentation_type': 'api',
                'target_audience': 'developers'
            }
        }
        
        doc_results = await self.service.process_hooks(HookType.PRE_TOOL_USE, doc_context)
        self.logger.info(f"Documentation pre-tool results: {len(doc_results)} hooks executed")
        
        # Test QA agent hooks
        qa_context = {
            'test_config': {
                'test_paths': ['tests/'],
                'parallel_execution': True
            },
            'test_results': {
                'passed': 45,
                'failed': 3,
                'coverage': 78.5
            }
        }
        
        qa_results = await self.service.process_hooks(HookType.POST_TOOL_USE, qa_context)
        self.logger.info(f"QA post-tool results: {len(qa_results)} hooks executed")
        
        # Test version control hooks
        vc_context = {
            'git_command': 'git push origin main',
            'repo_state': {
                'has_uncommitted_changes': False,
                'current_branch': 'main'
            }
        }
        
        vc_results = await self.service.process_hooks(HookType.PRE_TOOL_USE, vc_context)
        self.logger.info(f"Version control pre-tool results: {len(vc_results)} hooks executed")
    
    async def demonstrate_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities."""
        self.logger.info("Demonstrating performance monitoring...")
        
        # Generate some test load
        for i in range(10):
            context = {
                'iteration': i,
                'execution_time': 0.5 + (i * 0.1),  # Gradually increasing time
                'hook_id': f'test_hook_{i}'
            }
            
            await self.service.process_hooks(HookType.PERFORMANCE_MONITOR, context)
            await asyncio.sleep(0.1)  # Small delay between executions
        
        # Get performance report
        status = self.service.get_service_status()
        self.logger.info(f"Performance report: {json.dumps(status['performance_report'], indent=2)}")
    
    async def demonstrate_error_recovery(self):
        """Demonstrate error recovery scenarios."""
        self.logger.info("Demonstrating error recovery...")
        
        # Register a hook that fails occasionally
        async def failing_hook(context):
            iteration = context.get('iteration', 0)
            if iteration % 3 == 0:  # Fail every 3rd iteration
                raise RuntimeError(f"Simulated failure at iteration {iteration}")
            return f"Success at iteration {iteration}"
        
        self.service.register_hook(HookConfiguration(
            hook_id='failing_demo_hook',
            hook_type=HookType.PRE_TOOL_USE,
            handler=failing_hook,
            priority=50,
            timeout=5.0,
            retry_count=1,
            prefer_async=True
        ))
        
        # Execute failing hook multiple times
        for i in range(6):
            context = {'iteration': i}
            results = await self.service.process_hooks(HookType.PRE_TOOL_USE, context)
            
            for result in results:
                if result.hook_id == 'failing_demo_hook':
                    self.logger.info(f"Iteration {i}: {'Success' if result.success else 'Failed'}")
        
        # Clean up
        self.service.unregister_hook('failing_demo_hook')
    
    async def run_complete_demo(self):
        """Run complete demonstration."""
        await self.setup_demo_environment()
        
        try:
            await self.demonstrate_subagent_stop_detection()
            await self.demonstrate_hook_execution()
            await self.demonstrate_performance_monitoring()
            await self.demonstrate_error_recovery()
            
            # Final status report
            final_status = self.service.get_service_status()
            self.logger.info(f"Final service status: {json.dumps(final_status, indent=2, default=str)}")
            
        finally:
            if self.service:
                await self.service.stop()
    
    def save_demo_results(self, filepath: str):
        """Save demo results to file."""
        if not self.service:
            return
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'service_status': self.service.get_service_status(),
            'integration_stats': self.integration_hooks.get_integration_stats() if self.integration_hooks else {}
        }
        
        Path(filepath).write_text(json.dumps(results, indent=2, default=str))
        self.logger.info(f"Demo results saved to: {filepath}")


# Utility functions for easy integration
async def quick_error_analysis(transcript: str, agent_type: str) -> Dict[str, Any]:
    """Quick error analysis for a single transcript."""
    service = await create_hook_processing_service({
        'max_workers': 1,
        'max_history': 10,
        'max_log_files': 2,
        'max_log_size_mb': 1,
        'async_by_default': True
    })
    
    try:
        result = await service.analyze_subagent_transcript(transcript, agent_type)
        return result
    finally:
        await service.stop()


async def setup_agent_monitoring(agent_types: List[str]) -> HookProcessingService:
    """Setup monitoring for specified agent types."""
    service = await create_hook_processing_service()
    integration_hooks = AgentIntegrationHooks(service)
    
    for agent_type in agent_types:
        if agent_type == 'documentation_agent':
            await integration_hooks.setup_documentation_agent_hooks()
        elif agent_type == 'qa_agent':
            await integration_hooks.setup_qa_agent_hooks()
        elif agent_type == 'version_control_agent':
            await integration_hooks.setup_version_control_hooks()
    
    return service


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstration
    demo = HookProcessingDemo()
    asyncio.run(demo.run_complete_demo())