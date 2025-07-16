"""
Correction Capture Service
=========================

This service captures user corrections to agent responses for automatic prompt evaluation
and improvement. It's designed to integrate seamlessly with the Task Tool subprocess system
to improve agent behavior over time.

Key Features:
- Automatic correction capture from Task Tool subprocess responses
- JSON-based storage with proper file naming and rotation
- Data integrity validation and error handling
- Integration with existing framework configuration
- Seamless workflow integration without disrupting existing functionality

Phase 1 Implementation:
- Basic correction capture and storage
- Directory structure creation
- Task Tool integration hooks
- Configuration management

Future Phases:
- Mirascope evaluation integration
- Automatic prompt improvement
- Advanced analytics and reporting
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import uuid

from claude_pm.core.config import Config
from claude_pm.core.response_types import TaskToolResponse

logger = logging.getLogger(__name__)


class CorrectionType(Enum):
    """Types of corrections that can be captured."""
    CONTENT_CORRECTION = "content_correction"
    APPROACH_CORRECTION = "approach_correction"
    MISSING_INFORMATION = "missing_information"
    INCORRECT_INTERPRETATION = "incorrect_interpretation"
    QUALITY_IMPROVEMENT = "quality_improvement"
    FORMATTING_CORRECTION = "formatting_correction"
    TECHNICAL_CORRECTION = "technical_correction"


@dataclass
class CorrectionData:
    """Data structure for storing correction information."""
    correction_id: str
    agent_type: str
    original_response: str
    user_correction: str
    context: Dict[str, Any]
    correction_type: CorrectionType
    timestamp: str
    subprocess_id: Optional[str] = None
    task_description: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    user_feedback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['correction_type'] = self.correction_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrectionData':
        """Create from dictionary."""
        data['correction_type'] = CorrectionType(data['correction_type'])
        return cls(**data)


@dataclass
class CorrectionStorageConfig:
    """Configuration for correction storage."""
    storage_path: Path
    rotation_days: int = 30
    max_file_size_mb: int = 10
    backup_enabled: bool = True
    compression_enabled: bool = True
    
    def __post_init__(self):
        """Ensure storage path is a Path object."""
        if isinstance(self.storage_path, str):
            self.storage_path = Path(self.storage_path)


class CorrectionCapture:
    """
    Correction Capture Service
    
    Captures and stores user corrections to agent responses for automatic 
    prompt evaluation and improvement.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize correction capture service.
        
        Args:
            config: Configuration object with evaluation settings
        """
        self.config = config or Config()
        self.enabled = self.config.get("correction_capture_enabled", True)
        self.storage_config = self._create_storage_config()
        self.corrections_cache: List[CorrectionData] = []
        self.session_id = str(uuid.uuid4())
        
        if self.enabled:
            self._initialize_storage()
            logger.info(f"Correction capture service initialized with storage at {self.storage_config.storage_path}")
        else:
            logger.info("Correction capture service disabled by configuration")
    
    def _create_storage_config(self) -> CorrectionStorageConfig:
        """Create storage configuration from main config."""
        base_path = Path(self.config.get("evaluation_storage_path", "~/.claude-pm/training")).expanduser()
        
        return CorrectionStorageConfig(
            storage_path=base_path,
            rotation_days=self.config.get("correction_storage_rotation_days", 30),
            max_file_size_mb=self.config.get("correction_max_file_size_mb", 10),
            backup_enabled=self.config.get("correction_backup_enabled", True),
            compression_enabled=self.config.get("correction_compression_enabled", True)
        )
    
    def _initialize_storage(self) -> None:
        """Initialize storage directory structure."""
        try:
            # Create main directories
            corrections_dir = self.storage_config.storage_path / "corrections"
            evaluations_dir = self.storage_config.storage_path / "evaluations"
            agent_prompts_dir = self.storage_config.storage_path / "agent-prompts"
            
            # Create directories if they don't exist
            for directory in [corrections_dir, evaluations_dir, agent_prompts_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
            
            # Create session directory
            session_dir = corrections_dir / f"session_{self.session_id[:8]}"
            session_dir.mkdir(exist_ok=True)
            
            # Initialize metadata file
            metadata_file = self.storage_config.storage_path / "metadata.json"
            if not metadata_file.exists():
                metadata = {
                    "created": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "description": "Claude PM Framework Correction Capture Storage",
                    "session_count": 0
                }
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Update session count
            self._update_session_count()
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            raise
    
    def _update_session_count(self) -> None:
        """Update session count in metadata."""
        try:
            metadata_file = self.storage_config.storage_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                metadata["session_count"] = metadata.get("session_count", 0) + 1
                metadata["last_session"] = datetime.now().isoformat()
                metadata["last_session_id"] = self.session_id
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Failed to update session count: {e}")
    
    def capture_correction(
        self,
        agent_type: str,
        original_response: str,
        user_correction: str,
        context: Dict[str, Any],
        correction_type: CorrectionType = CorrectionType.CONTENT_CORRECTION,
        subprocess_id: Optional[str] = None,
        task_description: Optional[str] = None,
        severity: str = "medium",
        user_feedback: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Capture a correction from user feedback.
        
        Args:
            agent_type: Type of agent that produced the original response
            original_response: Original agent response
            user_correction: User's correction or feedback
            context: Context information about the task
            correction_type: Type of correction being made
            subprocess_id: ID of the subprocess if applicable
            task_description: Description of the task
            severity: Severity level of the correction
            user_feedback: Additional user feedback
            metadata: Additional metadata
            
        Returns:
            Correction ID
        """
        if not self.enabled:
            logger.debug("Correction capture disabled, skipping")
            return ""
        
        try:
            # Generate unique correction ID
            correction_id = f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Create correction data
            correction_data = CorrectionData(
                correction_id=correction_id,
                agent_type=agent_type,
                original_response=original_response,
                user_correction=user_correction,
                context=context,
                correction_type=correction_type,
                timestamp=datetime.now().isoformat(),
                subprocess_id=subprocess_id,
                task_description=task_description,
                severity=severity,
                user_feedback=user_feedback,
                metadata=metadata or {}
            )
            
            # Add to cache
            self.corrections_cache.append(correction_data)
            
            # Store to file
            self._store_correction(correction_data)
            
            logger.info(f"Captured correction {correction_id} for {agent_type}")
            
            return correction_id
            
        except Exception as e:
            logger.error(f"Failed to capture correction: {e}")
            return ""
    
    def _store_correction(self, correction_data: CorrectionData) -> None:
        """Store correction data to file."""
        try:
            # Create filename with timestamp and agent type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{correction_data.agent_type}_{timestamp}_{correction_data.correction_id}.json"
            
            # Store in session directory
            session_dir = self.storage_config.storage_path / "corrections" / f"session_{self.session_id[:8]}"
            correction_file = session_dir / filename
            
            # Write correction data
            with open(correction_file, 'w') as f:
                json.dump(correction_data.to_dict(), f, indent=2)
            
            logger.debug(f"Stored correction to {correction_file}")
            
        except Exception as e:
            logger.error(f"Failed to store correction: {e}")
            raise
    
    def get_corrections(
        self,
        agent_type: Optional[str] = None,
        since: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[CorrectionData]:
        """
        Retrieve stored corrections with optional filtering.
        
        Args:
            agent_type: Filter by agent type
            since: Only corrections since this date
            severity: Filter by severity level
            limit: Maximum number of corrections to return
            
        Returns:
            List of correction data
        """
        if not self.enabled:
            return []
        
        try:
            corrections = []
            
            # Load from cache first
            corrections.extend(self.corrections_cache)
            
            # Load from files
            corrections_dir = self.storage_config.storage_path / "corrections"
            if corrections_dir.exists():
                for session_dir in corrections_dir.iterdir():
                    if session_dir.is_dir():
                        for correction_file in session_dir.glob("*.json"):
                            try:
                                with open(correction_file, 'r') as f:
                                    data = json.load(f)
                                    correction = CorrectionData.from_dict(data)
                                    
                                    # Skip if already in cache
                                    if correction.correction_id not in [c.correction_id for c in self.corrections_cache]:
                                        corrections.append(correction)
                                        
                            except Exception as e:
                                logger.error(f"Failed to load correction from {correction_file}: {e}")
            
            # Apply filters
            if agent_type:
                corrections = [c for c in corrections if c.agent_type == agent_type]
            
            if since:
                corrections = [c for c in corrections if datetime.fromisoformat(c.timestamp) >= since]
            
            if severity:
                corrections = [c for c in corrections if c.severity == severity]
            
            # Sort by timestamp (newest first)
            corrections.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if limit:
                corrections = corrections[:limit]
            
            return corrections
            
        except Exception as e:
            logger.error(f"Failed to retrieve corrections: {e}")
            return []
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """Get statistics about captured corrections."""
        try:
            corrections = self.get_corrections()
            
            if not corrections:
                return {
                    "total_corrections": 0,
                    "agents_with_corrections": [],
                    "correction_types": {},
                    "severity_distribution": {},
                    "sessions_with_corrections": 0
                }
            
            # Calculate statistics
            agent_counts = {}
            type_counts = {}
            severity_counts = {}
            sessions = set()
            
            for correction in corrections:
                # Agent counts
                agent_counts[correction.agent_type] = agent_counts.get(correction.agent_type, 0) + 1
                
                # Type counts
                type_counts[correction.correction_type.value] = type_counts.get(correction.correction_type.value, 0) + 1
                
                # Severity counts
                severity_counts[correction.severity] = severity_counts.get(correction.severity, 0) + 1
                
                # Sessions (extract from correction_id or use current session)
                sessions.add(self.session_id)
            
            return {
                "total_corrections": len(corrections),
                "agents_with_corrections": list(agent_counts.keys()),
                "agent_correction_counts": agent_counts,
                "correction_types": type_counts,
                "severity_distribution": severity_counts,
                "sessions_with_corrections": len(sessions),
                "most_corrected_agent": max(agent_counts.items(), key=lambda x: x[1])[0] if agent_counts else None,
                "most_common_correction_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get correction stats: {e}")
            return TaskToolResponse(
                request_id=f"correction_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"total_corrections": 0}
            ).__dict__
    
    def cleanup_old_corrections(self, days_to_keep: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old correction files.
        
        Args:
            days_to_keep: Number of days to keep corrections (default from config)
            
        Returns:
            Cleanup summary
        """
        if not self.enabled:
            return {"message": "Correction capture disabled"}
        
        try:
            days_to_keep = days_to_keep or self.storage_config.rotation_days
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            removed_files = []
            removed_dirs = []
            total_size_removed = 0
            
            corrections_dir = self.storage_config.storage_path / "corrections"
            if corrections_dir.exists():
                for session_dir in corrections_dir.iterdir():
                    if session_dir.is_dir():
                        session_files = list(session_dir.glob("*.json"))
                        session_empty = True
                        
                        for correction_file in session_files:
                            try:
                                # Check file modification time
                                file_time = datetime.fromtimestamp(correction_file.stat().st_mtime)
                                
                                if file_time < cutoff_date:
                                    file_size = correction_file.stat().st_size
                                    correction_file.unlink()
                                    removed_files.append(str(correction_file))
                                    total_size_removed += file_size
                                else:
                                    session_empty = False
                                    
                            except Exception as e:
                                logger.error(f"Failed to process {correction_file}: {e}")
                                session_empty = False
                        
                        # Remove empty session directories
                        if session_empty and not list(session_dir.iterdir()):
                            session_dir.rmdir()
                            removed_dirs.append(str(session_dir))
            
            logger.info(f"Cleanup completed: removed {len(removed_files)} files, {len(removed_dirs)} directories, {total_size_removed} bytes")
            
            return {
                "removed_files": len(removed_files),
                "removed_directories": len(removed_dirs),
                "total_size_removed": total_size_removed,
                "cutoff_date": cutoff_date.isoformat(),
                "files_removed": removed_files if len(removed_files) < 20 else removed_files[:20] + ["..."]
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old corrections: {e}")
            return TaskToolResponse(
                request_id=f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"removed_files": 0, "removed_directories": 0}
            ).__dict__
    
    def validate_storage_integrity(self) -> Dict[str, Any]:
        """Validate storage integrity and fix any issues."""
        try:
            issues = []
            fixes_applied = []
            
            # Check if storage directories exist
            required_dirs = [
                self.storage_config.storage_path / "corrections",
                self.storage_config.storage_path / "evaluations",
                self.storage_config.storage_path / "agent-prompts"
            ]
            
            for directory in required_dirs:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    fixes_applied.append(f"Created missing directory: {directory}")
            
            # Check metadata file
            metadata_file = self.storage_config.storage_path / "metadata.json"
            if not metadata_file.exists():
                issues.append("Missing metadata file")
                self._initialize_storage()
                fixes_applied.append("Recreated metadata file")
            
            # Validate correction files
            corrections_dir = self.storage_config.storage_path / "corrections"
            corrupted_files = []
            
            if corrections_dir.exists():
                for session_dir in corrections_dir.iterdir():
                    if session_dir.is_dir():
                        for correction_file in session_dir.glob("*.json"):
                            try:
                                with open(correction_file, 'r') as f:
                                    data = json.load(f)
                                    CorrectionData.from_dict(data)  # Validate structure
                            except Exception as e:
                                issues.append(f"Corrupted correction file: {correction_file}")
                                corrupted_files.append(str(correction_file))
            
            return {
                "storage_path": str(self.storage_config.storage_path),
                "issues_found": len(issues),
                "issues": issues,
                "fixes_applied": fixes_applied,
                "corrupted_files": corrupted_files,
                "integrity_ok": len(issues) == 0
            }
            
        except Exception as e:
            logger.error(f"Storage integrity validation failed: {e}")
            return TaskToolResponse(
                request_id=f"integrity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"issues_found": -1, "integrity_ok": False}
            ).__dict__
    
    def export_corrections(self, format: str = "json") -> str:
        """
        Export all corrections to a single file.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Path to exported file
        """
        try:
            corrections = self.get_corrections()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                export_file = self.storage_config.storage_path / f"corrections_export_{timestamp}.json"
                
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_corrections": len(corrections),
                    "corrections": [c.to_dict() for c in corrections]
                }
                
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported {len(corrections)} corrections to {export_file}")
            return str(export_file)
            
        except Exception as e:
            logger.error(f"Failed to export corrections: {e}")
            raise
    
    def create_task_tool_integration_hook(self, subprocess_id: str, agent_type: str, task_description: str) -> Dict[str, Any]:
        """
        Create integration hook for Task Tool subprocess to capture corrections.
        
        Args:
            subprocess_id: ID of the subprocess
            agent_type: Type of agent
            task_description: Task description
            
        Returns:
            Integration hook information
        """
        try:
            hook_id = f"hook_{subprocess_id}"
            
            # Store hook information for later use
            hook_info = {
                "hook_id": hook_id,
                "subprocess_id": subprocess_id,
                "agent_type": agent_type,
                "task_description": task_description,
                "created": datetime.now().isoformat(),
                "active": True
            }
            
            # Store hook info in session directory
            session_dir = self.storage_config.storage_path / "corrections" / f"session_{self.session_id[:8]}"
            hook_file = session_dir / f"hook_{hook_id}.json"
            
            with open(hook_file, 'w') as f:
                json.dump(hook_info, f, indent=2)
            
            logger.info(f"Created Task Tool integration hook: {hook_id}")
            
            return hook_info
            
        except Exception as e:
            logger.error(f"Failed to create Task Tool integration hook: {e}")
            return TaskToolResponse(
                request_id=f"hook_{subprocess_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                success=False,
                error=str(e),
                performance_metrics={"hook_created": False, "subprocess_id": subprocess_id}
            ).__dict__


# Helper functions for easy integration
def capture_subprocess_correction(
    agent_type: str,
    original_response: str,
    user_correction: str,
    subprocess_id: str,
    task_description: str,
    correction_type: CorrectionType = CorrectionType.CONTENT_CORRECTION,
    severity: str = "medium"
) -> str:
    """
    Quick correction capture for subprocess responses.
    
    Args:
        agent_type: Type of agent
        original_response: Original agent response
        user_correction: User's correction
        subprocess_id: Subprocess ID
        task_description: Task description
        correction_type: Type of correction
        severity: Severity level
        
    Returns:
        Correction ID
    """
    capture_service = CorrectionCapture()
    
    return capture_service.capture_correction(
        agent_type=agent_type,
        original_response=original_response,
        user_correction=user_correction,
        context={"subprocess_id": subprocess_id, "task_description": task_description},
        correction_type=correction_type,
        subprocess_id=subprocess_id,
        task_description=task_description,
        severity=severity
    )


def get_agent_correction_history(agent_type: str, limit: int = 10) -> List[CorrectionData]:
    """
    Get recent corrections for a specific agent type.
    
    Args:
        agent_type: Type of agent
        limit: Maximum number of corrections to return
        
    Returns:
        List of correction data
    """
    capture_service = CorrectionCapture()
    return capture_service.get_corrections(agent_type=agent_type, limit=limit)


def initialize_correction_capture_system() -> Dict[str, Any]:
    """Initialize the correction capture system and return status."""
    try:
        capture_service = CorrectionCapture()
        validation_result = capture_service.validate_storage_integrity()
        stats = capture_service.get_correction_stats()
        
        return {
            "initialized": True,
            "storage_integrity": validation_result,
            "statistics": stats,
            "service_enabled": capture_service.enabled,
            "storage_path": str(capture_service.storage_config.storage_path)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize correction capture system: {e}")
        return TaskToolResponse(
            request_id=f"init_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            success=False,
            error=str(e),
            performance_metrics={"initialized": False, "service_enabled": False}
        ).__dict__


if __name__ == "__main__":
    # Test the correction capture system
    print("Testing Correction Capture System")
    print("=" * 50)
    
    # Initialize system
    init_result = initialize_correction_capture_system()
    print(f"Initialization: {init_result['initialized']}")
    
    if init_result['initialized']:
        print(f"Storage path: {init_result['storage_path']}")
        print(f"Service enabled: {init_result['service_enabled']}")
        
        # Test correction capture
        correction_id = capture_subprocess_correction(
            agent_type="engineer",
            original_response="def hello(): print('hello')",
            user_correction="def hello(): print('Hello, World!')",
            subprocess_id="test_subprocess_123",
            task_description="Create a hello function",
            correction_type=CorrectionType.CONTENT_CORRECTION,
            severity="low"
        )
        
        print(f"Captured correction: {correction_id}")
        
        # Test statistics
        capture_service = CorrectionCapture()
        stats = capture_service.get_correction_stats()
        print(f"Statistics: {stats}")
        
        # Test correction retrieval
        corrections = get_agent_correction_history("engineer", limit=5)
        print(f"Retrieved {len(corrections)} corrections for engineer")
        
    else:
        print(f"Initialization failed: {init_result.get('error', 'Unknown error')}")