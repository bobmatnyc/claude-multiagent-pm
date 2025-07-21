"""
Default handlers and example implementations for hook processing.
"""

import re
from typing import Dict, Any, List


class SubagentStopHookExample:
    """Example implementation of SubagentStop error detection hooks."""
    
    @staticmethod
    async def detect_agent_crashes(context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect agent crashes from subprocess transcripts."""
        transcript = context.get('transcript', '')
        agent_type = context.get('agent_type', 'unknown')
        
        # Specific patterns for different agent types
        agent_crash_patterns = {
            'documentation_agent': [
                r'failed\s+to\s+generate\s+documentation',
                r'markdown\s+parser\s+crashed',
                r'documentation\s+build\s+failed'
            ],
            'qa_agent': [
                r'test\s+runner\s+crashed',
                r'pytest\s+(?:failed|error)',
                r'test\s+execution\s+terminated'
            ],
            'version_control_agent': [
                r'git\s+process\s+failed',
                r'merge\s+conflict\s+unresolved',
                r'repository\s+corruption'
            ]
        }
        
        detected_issues = []
        
        # Check for general subprocess failures
        general_patterns = [
            r'subprocess\s+terminated\s+with\s+code\s+(?!0)',
            r'agent\s+process\s+killed',
            r'memory\s+exhausted.*agent',
            r'timeout.*agent\s+execution'
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, transcript, re.IGNORECASE):
                detected_issues.append({
                    'type': 'subprocess_failure',
                    'pattern': pattern,
                    'agent_type': agent_type,
                    'severity': 'high'
                })
        
        # Check for agent-specific issues
        if agent_type in agent_crash_patterns:
            for pattern in agent_crash_patterns[agent_type]:
                if re.search(pattern, transcript, re.IGNORECASE):
                    detected_issues.append({
                        'type': f'{agent_type}_crash',
                        'pattern': pattern,
                        'agent_type': agent_type,
                        'severity': 'critical'
                    })
        
        return {
            'issues_detected': len(detected_issues),
            'issues': detected_issues,
            'recommended_actions': [
                'restart_agent',
                'check_resource_availability',
                'validate_environment'
            ] if detected_issues else []
        }
    
    @staticmethod
    async def detect_resource_exhaustion(context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect resource exhaustion that might cause agent stops."""
        transcript = context.get('transcript', '')
        
        resource_patterns = [
            (r'out\s+of\s+memory', 'memory_exhaustion'),
            (r'disk\s+space\s+full', 'disk_full'),
            (r'too\s+many\s+open\s+files', 'file_descriptor_limit'),
            (r'connection\s+pool\s+exhausted', 'connection_limit'),
            (r'cpu\s+usage\s+(?:high|100%)', 'cpu_exhaustion')
        ]
        
        detected_resources = []
        
        for pattern, resource_type in resource_patterns:
            if re.search(pattern, transcript, re.IGNORECASE):
                detected_resources.append({
                    'type': resource_type,
                    'pattern': pattern,
                    'severity': 'critical'
                })
        
        return {
            'resource_issues': len(detected_resources),
            'issues': detected_resources,
            'recommended_actions': [
                'cleanup_resources',
                'increase_limits',
                'restart_system'
            ] if detected_resources else []
        }