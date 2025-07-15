"""
Hook Processing Service - Core implementation for Claude PM Framework
Handles hook execution, error detection, and monitoring for agent workflows.
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from pathlib import Path
import weakref
import traceback
from concurrent.futures import ThreadPoolExecutor
import glob


class HookType(Enum):
    """Enumeration of supported hook types."""
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    SUBAGENT_STOP = "subagent_stop"
    ERROR_DETECTION = "error_detection"
    PERFORMANCE_MONITOR = "performance_monitor"
    WORKFLOW_TRANSITION = "workflow_transition"


class ErrorSeverity(Enum):
    """Error severity levels for hook processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HookExecutionResult:
    """Result of hook execution with metadata."""
    hook_id: str
    success: bool
    execution_time: float
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorDetectionResult:
    """Result of error detection analysis."""
    error_detected: bool
    error_type: str
    severity: ErrorSeverity
    details: Dict[str, Any]
    suggested_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HookConfiguration:
    """Configuration for a single hook."""
    hook_id: str
    hook_type: HookType
    handler: Callable
    priority: int = 0
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 3
    prefer_async: bool = True  # Default to async execution
    force_sync: bool = False   # Override to force sync execution
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectBasedHookLogger:
    """Project-based hook logging system with automatic directory management and log rotation."""
    
    def __init__(self, project_root: Optional[str] = None, max_log_files: int = 10, max_log_size_mb: int = 10):
        """Initialize project-based hook logger.
        
        Args:
            project_root: Project root directory (defaults to current working directory)
            max_log_files: Maximum number of log files to retain per hook type
            max_log_size_mb: Maximum size of individual log files in MB
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.max_log_files = max_log_files
        self.max_log_size_mb = max_log_size_mb
        self.logger = logging.getLogger(f"{__name__}.ProjectBasedHookLogger")
        
        # Create hooks logging directory structure
        self.hooks_dir = self.project_root / ".claude-pm" / "hooks"
        self.logs_dir = self.hooks_dir / "logs"
        self._ensure_directories()
        
        # Track log files per hook type
        self.log_files: Dict[str, Path] = {}
        
    def _ensure_directories(self):
        """Ensure hook logging directories exist."""
        try:
            self.hooks_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for each hook type
            for hook_type in HookType:
                type_dir = self.logs_dir / hook_type.value
                type_dir.mkdir(exist_ok=True)
                
        except Exception as e:
            self.logger.error(f"Failed to create hook logging directories: {e}")
    
    def _get_log_file_path(self, hook_type: HookType, hook_id: str) -> Path:
        """Get the log file path for a specific hook."""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{hook_id}_{date_str}.log"
        return self.logs_dir / hook_type.value / filename
    
    def _rotate_log_file(self, log_file: Path):
        """Rotate log file if it exceeds size limit."""
        try:
            if log_file.exists() and log_file.stat().st_size > (self.max_log_size_mb * 1024 * 1024):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_file = log_file.with_suffix(f".{timestamp}.log")
                log_file.rename(rotated_file)
                self.logger.info(f"Rotated log file: {log_file} -> {rotated_file}")
                
                # Clean up old log files
                self._cleanup_old_logs(log_file.parent, log_file.stem)
        except Exception as e:
            self.logger.error(f"Failed to rotate log file {log_file}: {e}")
    
    def _cleanup_old_logs(self, log_dir: Path, hook_id: str):
        """Clean up old log files for a specific hook."""
        try:
            # Find all log files for this hook
            pattern = f"{hook_id}_*.log*"
            log_files = list(log_dir.glob(pattern))
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove excess files
            for old_file in log_files[self.max_log_files:]:
                old_file.unlink()
                self.logger.info(f"Cleaned up old log file: {old_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs for {hook_id}: {e}")
    
    def log_hook_execution(self, hook_config: HookConfiguration, result: 'HookExecutionResult', context: Dict[str, Any]):
        """Log hook execution result to project-based logs."""
        try:
            log_file = self._get_log_file_path(hook_config.hook_type, hook_config.hook_id)
            
            # Rotate if necessary
            self._rotate_log_file(log_file)
            
            # Prepare log entry
            log_entry = {
                "timestamp": result.timestamp.isoformat(),
                "hook_id": hook_config.hook_id,
                "hook_type": hook_config.hook_type.value,
                "success": result.success,
                "execution_time": result.execution_time,
                "priority": hook_config.priority,
                "timeout": hook_config.timeout,
                "prefer_async": hook_config.prefer_async,
                "force_sync": hook_config.force_sync,
                "context_keys": list(context.keys()) if context else [],
                "result_type": type(result.result).__name__ if result.result else None,
                "error": result.error,
                "metadata": result.metadata
            }
            
            # Write to log file
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log hook execution for {hook_config.hook_id}: {e}")
    
    def log_error_detection(self, error_result: ErrorDetectionResult, context: Dict[str, Any]):
        """Log error detection result to project-based logs."""
        try:
            # Use ERROR_DETECTION hook type for error logging
            log_file = self._get_log_file_path(HookType.ERROR_DETECTION, "error_detection")
            
            # Rotate if necessary
            self._rotate_log_file(log_file)
            
            # Prepare error log entry
            error_entry = {
                "timestamp": error_result.timestamp.isoformat(),
                "error_type": error_result.error_type,
                "severity": error_result.severity.value,
                "error_detected": error_result.error_detected,
                "details": error_result.details,
                "suggested_action": error_result.suggested_action,
                "context": context
            }
            
            # Write to log file
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(error_entry) + "\n")
                
        except Exception as e:
            self.logger.error(f"Failed to log error detection: {e}")
    
    def get_hook_logs(self, hook_type: HookType, hook_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent hook logs for a specific hook."""
        try:
            log_file = self._get_log_file_path(hook_type, hook_id)
            
            if not log_file.exists():
                return []
            
            logs = []
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent logs first
            return logs[-limit:] if len(logs) > limit else logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs for {hook_id}: {e}")
            return []
    
    def get_project_hook_summary(self) -> Dict[str, Any]:
        """Get summary of all hook activity for the project."""
        try:
            summary = {
                "project_root": str(self.project_root),
                "hooks_directory": str(self.hooks_dir),
                "logs_directory": str(self.logs_dir),
                "hook_types": {},
                "total_log_files": 0,
                "total_log_size_mb": 0.0
            }
            
            for hook_type in HookType:
                type_dir = self.logs_dir / hook_type.value
                if type_dir.exists():
                    log_files = list(type_dir.glob("*.log*"))
                    total_size = sum(f.stat().st_size for f in log_files if f.exists())
                    
                    summary["hook_types"][hook_type.value] = {
                        "log_files_count": len(log_files),
                        "total_size_mb": total_size / (1024 * 1024),
                        "latest_activity": None
                    }
                    
                    # Find latest activity
                    if log_files:
                        latest_file = max(log_files, key=lambda f: f.stat().st_mtime)
                        summary["hook_types"][hook_type.value]["latest_activity"] = datetime.fromtimestamp(
                            latest_file.stat().st_mtime
                        ).isoformat()
                    
                    summary["total_log_files"] += len(log_files)
                    summary["total_log_size_mb"] += total_size / (1024 * 1024)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate project hook summary: {e}")
            return {"error": str(e)}
    
    def cleanup_old_logs(self, days_old: int = 30):
        """Clean up log files older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_timestamp = cutoff_date.timestamp()
            
            cleaned_files = 0
            for hook_type in HookType:
                type_dir = self.logs_dir / hook_type.value
                if type_dir.exists():
                    for log_file in type_dir.glob("*.log*"):
                        if log_file.stat().st_mtime < cutoff_timestamp:
                            log_file.unlink()
                            cleaned_files += 1
                            
            self.logger.info(f"Cleaned up {cleaned_files} old log files older than {days_old} days")
            return cleaned_files
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
            return 0


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


class HookExecutionEngine:
    """Engine for executing hooks with support for sync/async operations."""
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0,
            'last_updated': datetime.now()
        }
    
    async def execute_hook(self, hook_config: HookConfiguration, context: Dict[str, Any]) -> HookExecutionResult:
        """Execute a single hook with proper error handling and timeout.
        
        Now defaults to async execution unless force_sync is True.
        """
        start_time = time.time()
        self.execution_stats['total_executions'] += 1
        
        try:
            # Determine execution mode - async by default unless forced sync
            is_async_handler = asyncio.iscoroutinefunction(hook_config.handler)
            should_run_async = hook_config.prefer_async and not hook_config.force_sync
            
            # Execute hook with timeout based on execution mode
            if is_async_handler:
                # Handler is already async
                result = await asyncio.wait_for(
                    hook_config.handler(context),
                    timeout=hook_config.timeout
                )
            elif should_run_async and not hook_config.force_sync:
                # Run sync function in executor (async mode)
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        hook_config.handler,
                        context
                    ),
                    timeout=hook_config.timeout
                )
            else:
                # Force sync execution - run in executor but don't make it async
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        hook_config.handler,
                        context
                    ),
                    timeout=hook_config.timeout
                )
            
            execution_time = time.time() - start_time
            self.execution_stats['successful_executions'] += 1
            
            # Update average execution time
            self._update_average_execution_time(execution_time)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=True,
                execution_time=execution_time,
                result=result,
                metadata={
                    'execution_mode': 'async' if (is_async_handler or should_run_async) else 'sync',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync,
                    'is_async_handler': is_async_handler
                }
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.execution_stats['failed_executions'] += 1
            
            error_msg = f"Hook {hook_config.hook_id} timed out after {hook_config.timeout}s"
            self.logger.error(error_msg)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=False,
                execution_time=execution_time,
                error=error_msg,
                metadata={
                    'execution_mode': 'timeout',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats['failed_executions'] += 1
            
            error_msg = f"Hook {hook_config.hook_id} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return HookExecutionResult(
                hook_id=hook_config.hook_id,
                success=False,
                execution_time=execution_time,
                error=error_msg,
                metadata={
                    'execution_mode': 'error',
                    'prefer_async': hook_config.prefer_async,
                    'force_sync': hook_config.force_sync,
                    'exception_type': type(e).__name__, 
                    'traceback': traceback.format_exc()
                }
            )
    
    async def execute_hooks_batch(self, hook_configs: List[HookConfiguration], context: Dict[str, Any]) -> List[HookExecutionResult]:
        """Execute multiple hooks concurrently."""
        tasks = [
            self.execute_hook(hook_config, context)
            for hook_config in sorted(hook_configs, key=lambda h: h.priority, reverse=True)
            if hook_config.enabled
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                hook_config = hook_configs[i]
                processed_results.append(HookExecutionResult(
                    hook_id=hook_config.hook_id,
                    success=False,
                    execution_time=0.0,
                    error=f"Batch execution error: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _update_average_execution_time(self, execution_time: float):
        """Update running average of execution time."""
        current_avg = self.execution_stats['average_execution_time']
        total_executions = self.execution_stats['total_executions']
        
        # Calculate new average
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.execution_stats['average_execution_time'] = new_avg
        self.execution_stats['last_updated'] = datetime.now()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total = self.execution_stats['total_executions']
        return {
            **self.execution_stats,
            'success_rate': (
                self.execution_stats['successful_executions'] / max(1, total)
            ),
            'failure_rate': (
                self.execution_stats['failed_executions'] / max(1, total)
            )
        }
    
    def cleanup(self):
        """Clean up executor resources."""
        self.executor.shutdown(wait=True)


class HookConfigurationSystem:
    """System for managing hook configurations and registration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hooks: Dict[str, HookConfiguration] = {}
        self.hook_groups: Dict[HookType, List[str]] = {hook_type: [] for hook_type in HookType}
        self.weak_refs: Dict[str, weakref.ref] = {}
    
    def register_hook(self, hook_config: HookConfiguration) -> bool:
        """Register a new hook configuration."""
        try:
            if hook_config.hook_id in self.hooks:
                self.logger.warning(f"Hook {hook_config.hook_id} already registered, updating...")
            
            # Validate hook configuration
            if not callable(hook_config.handler):
                raise ValueError(f"Handler for hook {hook_config.hook_id} is not callable")
            
            # Store configuration
            self.hooks[hook_config.hook_id] = hook_config
            
            # Add to hook type group
            if hook_config.hook_id not in self.hook_groups[hook_config.hook_type]:
                self.hook_groups[hook_config.hook_type].append(hook_config.hook_id)
            
            # Create weak reference if handler is a bound method
            if hasattr(hook_config.handler, '__self__'):
                self.weak_refs[hook_config.hook_id] = weakref.ref(hook_config.handler.__self__)
            
            self.logger.info(f"Registered hook: {hook_config.hook_id} ({hook_config.hook_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hook {hook_config.hook_id}: {str(e)}")
            return False
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook configuration."""
        try:
            if hook_id not in self.hooks:
                self.logger.warning(f"Hook {hook_id} not found for unregistration")
                return False
            
            hook_config = self.hooks[hook_id]
            
            # Remove from hook type group
            if hook_id in self.hook_groups[hook_config.hook_type]:
                self.hook_groups[hook_config.hook_type].remove(hook_id)
            
            # Remove weak reference
            if hook_id in self.weak_refs:
                del self.weak_refs[hook_id]
            
            # Remove configuration
            del self.hooks[hook_id]
            
            self.logger.info(f"Unregistered hook: {hook_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister hook {hook_id}: {str(e)}")
            return False
    
    def get_hooks_by_type(self, hook_type: HookType) -> List[HookConfiguration]:
        """Get all enabled hooks of a specific type, sorted by priority."""
        hook_ids = self.hook_groups[hook_type]
        hooks = [self.hooks[hook_id] for hook_id in hook_ids if hook_id in self.hooks]
        
        # Filter enabled hooks and sort by priority
        enabled_hooks = [hook for hook in hooks if hook.enabled]
        return sorted(enabled_hooks, key=lambda h: h.priority, reverse=True)
    
    def get_hook(self, hook_id: str) -> Optional[HookConfiguration]:
        """Get a specific hook configuration."""
        return self.hooks.get(hook_id)
    
    def update_hook_status(self, hook_id: str, enabled: bool) -> bool:
        """Enable or disable a hook."""
        if hook_id not in self.hooks:
            return False
        
        self.hooks[hook_id].enabled = enabled
        self.logger.info(f"Hook {hook_id} {'enabled' if enabled else 'disabled'}")
        return True
    
    def get_configuration_stats(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        total_hooks = len(self.hooks)
        enabled_hooks = sum(1 for hook in self.hooks.values() if hook.enabled)
        
        return {
            'total_hooks': total_hooks,
            'enabled_hooks': enabled_hooks,
            'disabled_hooks': total_hooks - enabled_hooks,
            'hooks_by_type': {
                hook_type.value: len(self.hook_groups[hook_type])
                for hook_type in HookType
            },
            'dead_references': sum(
                1 for ref in self.weak_refs.values() if ref() is None
            )
        }
    
    def cleanup_dead_references(self):
        """Clean up dead weak references."""
        dead_refs = [
            hook_id for hook_id, ref in self.weak_refs.items()
            if ref() is None
        ]
        
        for hook_id in dead_refs:
            self.logger.info(f"Cleaning up dead reference for hook: {hook_id}")
            self.unregister_hook(hook_id)


class HookMonitoringSystem:
    """System for monitoring hook performance and health."""
    
    def __init__(self, max_history: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        self.execution_history: List[HookExecutionResult] = []
        self.error_history: List[ErrorDetectionResult] = []
        self.performance_metrics = {
            'total_hooks_executed': 0,
            'total_errors_detected': 0,
            'average_execution_time': 0.0,
            'peak_execution_time': 0.0,
            'last_updated': datetime.now()
        }
        self.alert_thresholds = {
            'execution_time': 10.0,  # seconds
            'error_rate': 0.1,  # 10%
            'failure_rate': 0.05  # 5%
        }
    
    def record_execution(self, result: HookExecutionResult):
        """Record a hook execution result."""
        self.execution_history.append(result)
        
        # Maintain history size
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)
        
        # Update metrics
        self.performance_metrics['total_hooks_executed'] += 1
        
        if result.execution_time > self.performance_metrics['peak_execution_time']:
            self.performance_metrics['peak_execution_time'] = result.execution_time
        
        # Update average execution time
        self._update_average_execution_time(result.execution_time)
        
        # Check for alerts
        self._check_performance_alerts(result)
    
    def record_error_detection(self, result: ErrorDetectionResult):
        """Record an error detection result."""
        self.error_history.append(result)
        
        # Maintain history size
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        self.performance_metrics['total_errors_detected'] += 1
        self.performance_metrics['last_updated'] = datetime.now()
        
        # Log critical errors
        if result.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error detected: {result.error_type}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        recent_executions = self.execution_history[-100:]  # Last 100 executions
        recent_errors = self.error_history[-100:]  # Last 100 errors
        
        # Calculate rates
        success_rate = 0.0
        failure_rate = 0.0
        if recent_executions:
            successful = sum(1 for r in recent_executions if r.success)
            success_rate = successful / len(recent_executions)
            failure_rate = (len(recent_executions) - successful) / len(recent_executions)
        
        # Error severity distribution
        error_severity_dist = {}
        for severity in ErrorSeverity:
            error_severity_dist[severity.value] = sum(
                1 for r in recent_errors if r.severity == severity
            )
        
        return {
            'performance_metrics': self.performance_metrics,
            'recent_statistics': {
                'success_rate': success_rate,
                'failure_rate': failure_rate,
                'error_rate': len(recent_errors) / max(1, len(recent_executions)),
                'executions_count': len(recent_executions),
                'errors_count': len(recent_errors)
            },
            'error_severity_distribution': error_severity_dist,
            'top_errors': self._get_top_errors(),
            'performance_trends': self._get_performance_trends(),
            'alerts': self._get_active_alerts()
        }
    
    def _update_average_execution_time(self, execution_time: float):
        """Update running average of execution time."""
        current_avg = self.performance_metrics['average_execution_time']
        total_executions = self.performance_metrics['total_hooks_executed']
        
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.performance_metrics['average_execution_time'] = new_avg
        self.performance_metrics['last_updated'] = datetime.now()
    
    def _check_performance_alerts(self, result: HookExecutionResult):
        """Check for performance alerts based on thresholds."""
        alerts = []
        
        # Execution time alert
        if result.execution_time > self.alert_thresholds['execution_time']:
            alerts.append({
                'type': 'slow_execution',
                'message': f"Hook {result.hook_id} took {result.execution_time:.2f}s",
                'severity': 'warning'
            })
        
        # Calculate recent failure rate
        recent_executions = self.execution_history[-50:]  # Last 50 executions
        if len(recent_executions) >= 10:
            failure_rate = sum(1 for r in recent_executions if not r.success) / len(recent_executions)
            if failure_rate > self.alert_thresholds['failure_rate']:
                alerts.append({
                    'type': 'high_failure_rate',
                    'message': f"Failure rate {failure_rate:.2%} exceeds threshold",
                    'severity': 'critical'
                })
        
        # Log alerts
        for alert in alerts:
            if alert['severity'] == 'critical':
                self.logger.critical(alert['message'])
            else:
                self.logger.warning(alert['message'])
    
    def _get_top_errors(self) -> List[Dict[str, Any]]:
        """Get most common errors."""
        error_counts = {}
        for error in self.error_history:
            key = error.error_type
            if key not in error_counts:
                error_counts[key] = {'count': 0, 'latest': error}
            error_counts[key]['count'] += 1
            if error.timestamp > error_counts[key]['latest'].timestamp:
                error_counts[key]['latest'] = error
        
        # Sort by count and return top 5
        top_errors = sorted(error_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        return [
            {
                'error_type': error_type,
                'count': data['count'],
                'latest_occurrence': data['latest'].timestamp.isoformat(),
                'severity': data['latest'].severity.value
            }
            for error_type, data in top_errors
        ]
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends."""
        if len(self.execution_history) < 10:
            return {'insufficient_data': True}
        
        # Calculate trends for last 50 executions
        recent = self.execution_history[-50:]
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        first_avg = sum(r.execution_time for r in first_half) / len(first_half)
        second_avg = sum(r.execution_time for r in second_half) / len(second_half)
        
        return {
            'execution_time_trend': 'improving' if second_avg < first_avg else 'degrading',
            'trend_percentage': abs((second_avg - first_avg) / first_avg) * 100,
            'first_half_avg': first_avg,
            'second_half_avg': second_avg
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""
        alerts = []
        
        # Check current failure rate
        recent_executions = self.execution_history[-20:]
        if len(recent_executions) >= 5:
            failure_rate = sum(1 for r in recent_executions if not r.success) / len(recent_executions)
            if failure_rate > self.alert_thresholds['failure_rate']:
                alerts.append({
                    'type': 'high_failure_rate',
                    'severity': 'critical',
                    'message': f"Current failure rate: {failure_rate:.2%}",
                    'threshold': self.alert_thresholds['failure_rate']
                })
        
        # Check recent error rate
        recent_errors = len([e for e in self.error_history if 
                           (datetime.now() - e.timestamp).total_seconds() < 300])  # Last 5 minutes
        if recent_errors > 5:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'message': f"Multiple errors in last 5 minutes: {recent_errors}",
                'threshold': 5
            })
        
        return alerts


class HookProcessingService:
    """Main service for processing hooks with comprehensive error detection and monitoring."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize subsystems
        self.error_detection = ErrorDetectionSystem()
        self.execution_engine = HookExecutionEngine(
            max_workers=self.config.get('max_workers', 4)
        )
        self.configuration_system = HookConfigurationSystem()
        self.monitoring_system = HookMonitoringSystem(
            max_history=self.config.get('max_history', 1000)
        )
        
        # Initialize project-based logging
        self.project_logger = ProjectBasedHookLogger(
            project_root=self.config.get('project_root'),
            max_log_files=self.config.get('max_log_files', 10),
            max_log_size_mb=self.config.get('max_log_size_mb', 10)
        )
        
        # Service state
        self.is_running = False
        self.startup_time = None
        
        # Register default hooks
        self._register_default_hooks()
    
    def _register_default_hooks(self):
        """Register default hooks for common scenarios."""
        # SubagentStop error detection hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='subagent_stop_detector',
            hook_type=HookType.SUBAGENT_STOP,
            handler=self._handle_subagent_stop,
            priority=100,
            timeout=5.0,
            prefer_async=True
        ))
        
        # Performance monitoring hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='performance_monitor',
            hook_type=HookType.PERFORMANCE_MONITOR,
            handler=self._handle_performance_monitoring,
            priority=50,
            timeout=3.0,
            prefer_async=True
        ))
        
        # General error detection hook (async by default)
        self.register_hook(HookConfiguration(
            hook_id='error_detector',
            hook_type=HookType.ERROR_DETECTION,
            handler=self._handle_error_detection,
            priority=90,
            timeout=10.0,
            prefer_async=True
        ))
    
    async def _handle_subagent_stop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SubagentStop error detection."""
        transcript = context.get('transcript', '')
        agent_type = context.get('agent_type', 'unknown')
        
        # Analyze transcript for subagent stop errors
        error_results = await self.error_detection.analyze_transcript(transcript, {
            'agent_type': agent_type,
            'analysis_type': 'subagent_stop'
        })
        
        # Filter for subagent stop errors
        subagent_errors = [r for r in error_results if r.error_type == 'subagent_stop']
        
        if subagent_errors:
            self.logger.warning(f"SubagentStop errors detected for {agent_type}: {len(subagent_errors)}")
            
            # Record errors for monitoring and project logging
            for error in subagent_errors:
                self.monitoring_system.record_error_detection(error)
                self.project_logger.log_error_detection(error, context)
            
            return {
                'errors_detected': len(subagent_errors),
                'errors': [
                    {
                        'type': error.error_type,
                        'severity': error.severity.value,
                        'details': error.details,
                        'suggested_action': error.suggested_action
                    }
                    for error in subagent_errors
                ],
                'recommended_action': 'restart_subagent'
            }
        
        return {'errors_detected': 0, 'status': 'healthy'}
    
    async def _handle_performance_monitoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance monitoring."""
        execution_time = context.get('execution_time', 0.0)
        hook_id = context.get('hook_id', 'unknown')
        
        # Check for performance issues
        alerts = []
        if execution_time > 5.0:
            alerts.append({
                'type': 'slow_execution',
                'message': f"Hook {hook_id} execution time: {execution_time:.2f}s",
                'severity': 'warning'
            })
        
        return {
            'execution_time': execution_time,
            'alerts': alerts,
            'performance_report': self.monitoring_system.get_performance_report()
        }
    
    async def _handle_error_detection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general error detection."""
        transcript = context.get('transcript', '')
        agent_type = context.get('agent_type', 'unknown')
        
        # Analyze for all error types
        error_results = await self.error_detection.analyze_transcript(transcript, {
            'agent_type': agent_type,
            'analysis_type': 'general'
        })
        
        # Record errors for monitoring and project logging
        for error in error_results:
            self.monitoring_system.record_error_detection(error)
            self.project_logger.log_error_detection(error, context)
        
        return {
            'errors_detected': len(error_results),
            'errors': [
                {
                    'type': error.error_type,
                    'severity': error.severity.value,
                    'details': error.details,
                    'suggested_action': error.suggested_action
                }
                for error in error_results
            ]
        }
    
    def register_hook(self, hook_config: HookConfiguration) -> bool:
        """Register a hook configuration."""
        return self.configuration_system.register_hook(hook_config)
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook configuration."""
        return self.configuration_system.unregister_hook(hook_id)
    
    async def process_hooks(self, hook_type: HookType, context: Dict[str, Any]) -> List[HookExecutionResult]:
        """Process all hooks of a specific type."""
        if not self.is_running:
            self.logger.warning("Hook processing service is not running")
            return []
        
        # Get hooks for this type
        hooks = self.configuration_system.get_hooks_by_type(hook_type)
        if not hooks:
            return []
        
        # Execute hooks
        results = await self.execution_engine.execute_hooks_batch(hooks, context)
        
        # Record results for monitoring and project logging
        for result in results:
            self.monitoring_system.record_execution(result)
            # Find the corresponding hook configuration for project logging
            hook_config = None
            for hook in hooks:
                if hook.hook_id == result.hook_id:
                    hook_config = hook
                    break
            if hook_config:
                self.project_logger.log_hook_execution(hook_config, result, context)
        
        return results
    
    async def analyze_subagent_transcript(self, transcript: str, agent_type: str) -> Dict[str, Any]:
        """Analyze subagent transcript for errors and issues."""
        context = {
            'transcript': transcript,
            'agent_type': agent_type,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Process SubagentStop hooks
        results = await self.process_hooks(HookType.SUBAGENT_STOP, context)
        
        # Process general error detection hooks
        error_results = await self.process_hooks(HookType.ERROR_DETECTION, context)
        
        # Combine results
        all_results = results + error_results
        
        # Extract error information
        detected_errors = []
        for result in all_results:
            if result.success and result.result:
                result_data = result.result
                if isinstance(result_data, dict) and 'errors' in result_data:
                    detected_errors.extend(result_data['errors'])
        
        return {
            'analysis_complete': True,
            'transcript_length': len(transcript),
            'agent_type': agent_type,
            'errors_detected': len(detected_errors),
            'errors': detected_errors,
            'execution_results': [
                {
                    'hook_id': r.hook_id,
                    'success': r.success,
                    'execution_time': r.execution_time,
                    'error': r.error
                }
                for r in all_results
            ],
            'analysis_timestamp': context['analysis_timestamp']
        }
    
    async def start(self):
        """Start the hook processing service."""
        if self.is_running:
            self.logger.warning("Hook processing service is already running")
            return
        
        self.logger.info("Starting hook processing service...")
        self.is_running = True
        self.startup_time = datetime.now()
        
        # Perform startup health checks
        await self._perform_startup_checks()
        
        self.logger.info("Hook processing service started successfully")
    
    async def stop(self):
        """Stop the hook processing service."""
        if not self.is_running:
            self.logger.warning("Hook processing service is not running")
            return
        
        self.logger.info("Stopping hook processing service...")
        self.is_running = False
        
        # Cleanup resources
        self.execution_engine.cleanup()
        self.configuration_system.cleanup_dead_references()
        
        self.logger.info("Hook processing service stopped")
    
    async def _perform_startup_checks(self):
        """Perform startup health checks."""
        checks = [
            ('Error Detection System', self._check_error_detection_health),
            ('Execution Engine', self._check_execution_engine_health),
            ('Configuration System', self._check_configuration_health),
            ('Monitoring System', self._check_monitoring_health)
        ]
        
        for check_name, check_func in checks:
            try:
                await check_func()
                self.logger.info(f"✅ {check_name} health check passed")
            except Exception as e:
                self.logger.error(f"❌ {check_name} health check failed: {str(e)}")
                raise
    
    async def _check_error_detection_health(self):
        """Check error detection system health."""
        # Test error detection with sample data
        sample_transcript = "Test transcript with no errors"
        results = await self.error_detection.analyze_transcript(sample_transcript)
        
        # Should return empty results for clean transcript
        if not isinstance(results, list):
            raise RuntimeError("Error detection system not returning proper results")
    
    async def _check_execution_engine_health(self):
        """Check execution engine health."""
        # Test with a simple hook
        async def test_hook(context):
            return "test_result"
        
        test_config = HookConfiguration(
            hook_id='health_check_test',
            hook_type=HookType.PRE_TOOL_USE,
            handler=test_hook,
            timeout=1.0
        )
        
        result = await self.execution_engine.execute_hook(test_config, {})
        
        if not result.success:
            raise RuntimeError(f"Execution engine test failed: {result.error}")
    
    async def _check_configuration_health(self):
        """Check configuration system health."""
        stats = self.configuration_system.get_configuration_stats()
        
        if stats['total_hooks'] == 0:
            raise RuntimeError("No hooks registered in configuration system")
    
    async def _check_monitoring_health(self):
        """Check monitoring system health."""
        report = self.monitoring_system.get_performance_report()
        
        if not isinstance(report, dict):
            raise RuntimeError("Monitoring system not generating proper reports")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status."""
        return {
            'service_info': {
                'is_running': self.is_running,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'uptime_seconds': (
                    (datetime.now() - self.startup_time).total_seconds()
                    if self.startup_time else 0
                )
            },
            'error_detection_stats': self.error_detection.get_detection_stats(),
            'execution_stats': self.execution_engine.get_execution_stats(),
            'configuration_stats': self.configuration_system.get_configuration_stats(),
            'performance_report': self.monitoring_system.get_performance_report(),
            'project_logging': self.project_logger.get_project_hook_summary()
        }
    
    def get_hook_logs(self, hook_type: HookType, hook_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get project-based hook logs for a specific hook."""
        return self.project_logger.get_hook_logs(hook_type, hook_id, limit)
    
    def get_project_hook_summary(self) -> Dict[str, Any]:
        """Get summary of all project-based hook activity."""
        return self.project_logger.get_project_hook_summary()
    
    def cleanup_project_logs(self, days_old: int = 30) -> int:
        """Clean up project-based hook logs older than specified days."""
        return self.project_logger.cleanup_old_logs(days_old)


# Example usage and practical implementations
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


# Factory function for easy service creation
async def create_hook_processing_service(config: Optional[Dict[str, Any]] = None) -> HookProcessingService:
    """Create and start a hook processing service."""
    service = HookProcessingService(config)
    await service.start()
    return service


# Example configuration
DEFAULT_CONFIG = {
    'max_workers': 4,
    'max_history': 1000,
    'max_log_files': 10,
    'max_log_size_mb': 10,
    'project_root': None,  # Defaults to current working directory
    'alert_thresholds': {
        'execution_time': 10.0,
        'error_rate': 0.1,
        'failure_rate': 0.05
    },
    'async_by_default': True  # New default behavior
}