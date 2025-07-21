"""
Storage and persistence operations for the prompt improvement pipeline.

This module handles saving, loading, and managing pipeline execution
records, results, and configuration data.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
from dataclasses import asdict, is_dataclass

from .types import (
    PipelineExecution, PipelineResults, PipelineConfig,
    PipelineStatus, PipelineStage
)


class StorageManager:
    """Manages persistence of pipeline data"""
    
    def __init__(self, base_path: str):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(base_path)
        
        # Create directory structure
        self.executions_dir = self.base_path / "executions"
        self.results_dir = self.base_path / "results"
        self.archives_dir = self.base_path / "archives"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.executions_dir, self.results_dir, self.archives_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"exec_{timestamp}_{unique_id}"
    
    async def save_pipeline_results(self, results: PipelineResults) -> str:
        """
        Save pipeline results to storage
        
        Args:
            results: Pipeline results to save
            
        Returns:
            Path to saved results file
        """
        try:
            filename = f"results_{results.execution_id}.json"
            filepath = self.results_dir / filename
            
            # Convert to serializable format
            results_data = self._serialize_dataclass(results)
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved pipeline results to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving pipeline results: {e}")
            raise
    
    async def save_execution_record(self, execution: PipelineExecution) -> str:
        """
        Save execution record to storage
        
        Args:
            execution: Execution record to save
            
        Returns:
            Path to saved execution file
        """
        try:
            filename = f"execution_{execution.execution_id}.json"
            filepath = self.executions_dir / filename
            
            # Convert to serializable format
            execution_data = self._serialize_dataclass(execution)
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(execution_data, f, indent=2, default=str)
            
            self.logger.debug(f"Saved execution record to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving execution record: {e}")
            raise
    
    async def load_execution_record(self, execution_id: str) -> Optional[PipelineExecution]:
        """
        Load execution record from storage
        
        Args:
            execution_id: ID of execution to load
            
        Returns:
            Execution record or None if not found
        """
        try:
            filename = f"execution_{execution_id}.json"
            filepath = self.executions_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Reconstruct execution object
            return self._deserialize_execution(data)
            
        except Exception as e:
            self.logger.error(f"Error loading execution record: {e}")
            return None
    
    async def load_pipeline_results(self, execution_id: str) -> Optional[PipelineResults]:
        """
        Load pipeline results from storage
        
        Args:
            execution_id: ID of execution results to load
            
        Returns:
            Pipeline results or None if not found
        """
        try:
            filename = f"results_{execution_id}.json"
            filepath = self.results_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Reconstruct results object
            return self._deserialize_results(data)
            
        except Exception as e:
            self.logger.error(f"Error loading pipeline results: {e}")
            return None
    
    async def list_executions(self, 
                            status: Optional[PipelineStatus] = None,
                            days_back: int = 30) -> List[Dict[str, Any]]:
        """
        List execution records with optional filtering
        
        Args:
            status: Filter by status (optional)
            days_back: Number of days to look back
            
        Returns:
            List of execution summaries
        """
        try:
            executions = []
            cutoff_date = datetime.now().timestamp() - (days_back * 86400)
            
            for filepath in self.executions_dir.glob("execution_*.json"):
                # Check file age
                if filepath.stat().st_mtime < cutoff_date:
                    continue
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Apply status filter if specified
                    if status and data.get('status') != status.value:
                        continue
                    
                    # Create summary
                    summary = {
                        'execution_id': data.get('execution_id'),
                        'status': data.get('status'),
                        'start_time': data.get('start_time'),
                        'end_time': data.get('end_time'),
                        'agent_types': data.get('config', {}).get('agent_types', []),
                        'total_improvements': data.get('total_improvements', 0),
                        'deployed_improvements': data.get('deployed_improvements', 0)
                    }
                    
                    executions.append(summary)
                    
                except Exception as e:
                    self.logger.warning(f"Error reading execution file {filepath}: {e}")
                    continue
            
            # Sort by start time (newest first)
            executions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Error listing executions: {e}")
            return []
    
    async def archive_old_records(self, days_to_keep: int = 90) -> int:
        """
        Archive old execution records and results
        
        Args:
            days_to_keep: Number of days to keep active records
            
        Returns:
            Number of records archived
        """
        try:
            archived_count = 0
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
            
            # Archive executions
            for filepath in self.executions_dir.glob("execution_*.json"):
                if filepath.stat().st_mtime < cutoff_date:
                    archive_path = self.archives_dir / filepath.name
                    filepath.rename(archive_path)
                    archived_count += 1
            
            # Archive results
            for filepath in self.results_dir.glob("results_*.json"):
                if filepath.stat().st_mtime < cutoff_date:
                    archive_path = self.archives_dir / filepath.name
                    filepath.rename(archive_path)
                    archived_count += 1
            
            self.logger.info(f"Archived {archived_count} old records")
            return archived_count
            
        except Exception as e:
            self.logger.error(f"Error archiving old records: {e}")
            return 0
    
    async def cleanup_archives(self, days_to_keep: int = 365) -> int:
        """
        Clean up very old archived records
        
        Args:
            days_to_keep: Number of days to keep archived records
            
        Returns:
            Number of records deleted
        """
        try:
            deleted_count = 0
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
            
            for filepath in self.archives_dir.glob("*.json"):
                if filepath.stat().st_mtime < cutoff_date:
                    filepath.unlink()
                    deleted_count += 1
            
            self.logger.info(f"Deleted {deleted_count} old archived records")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up archives: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            stats = {
                'executions': {
                    'count': len(list(self.executions_dir.glob("execution_*.json"))),
                    'size_mb': sum(f.stat().st_size for f in self.executions_dir.glob("*.json")) / 1024 / 1024
                },
                'results': {
                    'count': len(list(self.results_dir.glob("results_*.json"))),
                    'size_mb': sum(f.stat().st_size for f in self.results_dir.glob("*.json")) / 1024 / 1024
                },
                'archives': {
                    'count': len(list(self.archives_dir.glob("*.json"))),
                    'size_mb': sum(f.stat().st_size for f in self.archives_dir.glob("*.json")) / 1024 / 1024
                }
            }
            
            stats['total_size_mb'] = (
                stats['executions']['size_mb'] + 
                stats['results']['size_mb'] + 
                stats['archives']['size_mb']
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {}
    
    def _serialize_dataclass(self, obj: Any) -> Any:
        """Recursively serialize dataclass objects"""
        if is_dataclass(obj):
            return {k: self._serialize_dataclass(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [self._serialize_dataclass(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize_dataclass(v) for k, v in obj.items()}
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        else:
            return obj
    
    def _deserialize_execution(self, data: Dict[str, Any]) -> PipelineExecution:
        """Deserialize execution record from JSON data"""
        # Convert string timestamps back to datetime
        if 'start_time' in data:
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and data['end_time']:
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        
        # Convert status and stage enums
        if 'status' in data:
            data['status'] = PipelineStatus(data['status'])
        if 'current_stage' in data and data['current_stage']:
            data['current_stage'] = PipelineStage(data['current_stage'])
        
        # Reconstruct config
        if 'config' in data:
            data['config'] = PipelineConfig(**data['config'])
        
        return PipelineExecution(**data)
    
    def _deserialize_results(self, data: Dict[str, Any]) -> PipelineResults:
        """Deserialize pipeline results from JSON data"""
        # Convert timestamp
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return PipelineResults(**data)