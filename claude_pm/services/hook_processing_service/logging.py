"""
Project-based hook logging system with automatic directory management and log rotation.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import HookConfiguration, HookExecutionResult, ErrorDetectionResult, HookType


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
    
    def log_hook_execution(self, hook_config: HookConfiguration, result: HookExecutionResult, context: Dict[str, Any]):
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