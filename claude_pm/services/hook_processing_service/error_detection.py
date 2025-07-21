"""
System for detecting errors in subprocess transcripts and agent outputs.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Any

from .models import ErrorDetectionResult, ErrorSeverity


class ErrorDetectionSystem:
    """System for detecting errors in subprocess transcripts and agent outputs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_patterns = self._initialize_error_patterns()
        self.detection_stats = {
            'total_analyses': 0,
            'errors_detected': 0,
            'false_positives': 0,
            'last_updated': datetime.now()
        }
    
    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error detection patterns for various scenarios."""
        return {
            'subagent_stop': {
                'patterns': [
                    r'subprocess\s+(?:failed|error|crashed|terminated)',
                    r'agent\s+(?:stopped|failed|crashed|terminated)',
                    r'task\s+(?:failed|error|interrupted)',
                    r'execution\s+(?:failed|error|interrupted)',
                    r'(?:timeout|timed\s+out).*agent',
                    r'memory\s+(?:error|exceeded|allocation\s+failed)',
                    r'connection\s+(?:lost|failed|timeout)',
                    r'authentication\s+(?:failed|error)',
                    r'permission\s+(?:denied|error)',
                    r'import\s+(?:error|failed)',
                    r'module\s+not\s+found',
                    r'syntax\s+error',
                    r'runtime\s+error',
                    r'exception\s+(?:occurred|raised)',
                    r'traceback\s+\(most\s+recent\s+call\s+last\)',
                ],
                'severity': ErrorSeverity.HIGH,
                'action': 'restart_subagent'
            },
            'version_mismatch': {
                'patterns': [
                    r'version\s+(?:mismatch|conflict|incompatible)',
                    r'incompatible\s+version',
                    r'requires\s+version\s+.*but\s+found',
                    r'dependency\s+version\s+conflict',
                    r'package\s+version\s+mismatch',
                ],
                'severity': ErrorSeverity.MEDIUM,
                'action': 'update_dependencies'
            },
            'resource_exhaustion': {
                'patterns': [
                    r'out\s+of\s+memory',
                    r'memory\s+exhausted',
                    r'disk\s+space\s+(?:full|exhausted)',
                    r'too\s+many\s+open\s+files',
                    r'resource\s+temporarily\s+unavailable',
                    r'connection\s+pool\s+exhausted',
                ],
                'severity': ErrorSeverity.CRITICAL,
                'action': 'cleanup_resources'
            },
            'network_issues': {
                'patterns': [
                    r'network\s+(?:error|timeout|unreachable)',
                    r'connection\s+(?:refused|timeout|reset)',
                    r'dns\s+resolution\s+failed',
                    r'ssl\s+(?:error|handshake\s+failed)',
                    r'certificate\s+(?:error|expired|invalid)',
                    r'api\s+(?:timeout|rate\s+limit|unavailable)',
                ],
                'severity': ErrorSeverity.MEDIUM,
                'action': 'retry_with_backoff'
            },
            'data_corruption': {
                'patterns': [
                    r'data\s+(?:corruption|corrupted|invalid)',
                    r'checksum\s+(?:mismatch|failed)',
                    r'file\s+(?:corrupted|truncated)',
                    r'database\s+(?:corruption|integrity\s+error)',
                    r'json\s+(?:decode|parse)\s+error',
                    r'malformed\s+(?:data|response)',
                ],
                'severity': ErrorSeverity.HIGH,
                'action': 'restore_from_backup'
            }
        }
    
    async def analyze_transcript(self, transcript: str, context: Dict[str, Any] = None) -> List[ErrorDetectionResult]:
        """Analyze subprocess transcript for error patterns."""
        self.detection_stats['total_analyses'] += 1
        results = []
        
        context = context or {}
        
        for error_type, config in self.error_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, transcript, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extract context around the error
                    start = max(0, match.start() - 100)
                    end = min(len(transcript), match.end() + 100)
                    error_context = transcript[start:end]
                    
                    # Create error detection result
                    result = ErrorDetectionResult(
                        error_detected=True,
                        error_type=error_type,
                        severity=config['severity'],
                        details={
                            'matched_pattern': pattern,
                            'matched_text': match.group(),
                            'context': error_context,
                            'position': match.start(),
                            'analysis_context': context
                        },
                        suggested_action=config['action']
                    )
                    
                    results.append(result)
                    self.detection_stats['errors_detected'] += 1
                    
                    self.logger.warning(f"Error detected: {error_type} - {match.group()}")
        
        return results
    
    async def analyze_agent_output(self, output: str, agent_type: str) -> List[ErrorDetectionResult]:
        """Analyze agent output for specific error patterns."""
        # Add agent-specific error patterns
        agent_patterns = {
            'documentation_agent': [
                r'failed\s+to\s+generate\s+documentation',
                r'markdown\s+(?:parse|render)\s+error',
                r'documentation\s+build\s+failed',
            ],
            'qa_agent': [
                r'test\s+(?:failed|error)',
                r'assertion\s+error',
                r'coverage\s+(?:below|insufficient)',
                r'quality\s+check\s+failed',
            ],
            'version_control_agent': [
                r'git\s+(?:error|failed)',
                r'merge\s+conflict',
                r'push\s+(?:failed|rejected)',
                r'branch\s+(?:error|not\s+found)',
            ]
        }
        
        results = []
        
        # Check general patterns
        general_results = await self.analyze_transcript(output, {'agent_type': agent_type})
        results.extend(general_results)
        
        # Check agent-specific patterns
        if agent_type in agent_patterns:
            for pattern in agent_patterns[agent_type]:
                matches = re.finditer(pattern, output, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    result = ErrorDetectionResult(
                        error_detected=True,
                        error_type=f'{agent_type}_error',
                        severity=ErrorSeverity.MEDIUM,
                        details={
                            'matched_pattern': pattern,
                            'matched_text': match.group(),
                            'agent_type': agent_type,
                            'position': match.start()
                        },
                        suggested_action='retry_agent_task'
                    )
                    results.append(result)
        
        return results
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get error detection statistics."""
        return {
            **self.detection_stats,
            'error_rate': (
                self.detection_stats['errors_detected'] / 
                max(1, self.detection_stats['total_analyses'])
            ),
            'patterns_count': sum(len(config['patterns']) for config in self.error_patterns.values())
        }