"""
File I/O and versioning module

This module handles all file operations, storage, and version management
for the prompt improvement system.

Author: Claude PM Framework
Date: 2025-07-19
Version: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .models import (
    CorrectionPattern, PromptImprovement, ImprovementMetrics,
    ImprovementStrategy
)


class StorageManager:
    """Manages file I/O and versioning for prompt improvements"""
    
    def __init__(self, base_path: Path, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Storage paths
        self.base_path = base_path
        self.patterns_path = self.base_path / 'patterns'
        self.improvements_path = self.base_path / 'improvements'
        self.templates_path = self.base_path / 'templates'
        self.metrics_path = self.base_path / 'metrics'
        
        # Create directories
        for path in [self.patterns_path, self.improvements_path, 
                    self.templates_path, self.metrics_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    # Pattern storage methods
    async def save_pattern(self, pattern: CorrectionPattern):
        """Save correction pattern to storage"""
        try:
            pattern_file = self.patterns_path / f"{pattern.pattern_id}.json"
            with open(pattern_file, 'w') as f:
                # Convert datetime objects to ISO format
                pattern_dict = asdict(pattern)
                pattern_dict['first_seen'] = pattern.first_seen.isoformat()
                pattern_dict['last_seen'] = pattern.last_seen.isoformat()
                json.dump(pattern_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving pattern {pattern.pattern_id}: {e}")
    
    # Improvement storage methods
    async def save_improvement(self, improvement: PromptImprovement):
        """Save improvement to storage"""
        try:
            improvement_file = self.improvements_path / f"{improvement.improvement_id}.json"
            with open(improvement_file, 'w') as f:
                # Convert datetime and enum objects
                improvement_dict = asdict(improvement)
                improvement_dict['timestamp'] = improvement.timestamp.isoformat()
                improvement_dict['strategy'] = improvement.strategy.value
                json.dump(improvement_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving improvement {improvement.improvement_id}: {e}")
    
    async def load_improvement(self, improvement_id: str) -> Optional[PromptImprovement]:
        """Load improvement from storage"""
        try:
            improvement_file = self.improvements_path / f"{improvement_id}.json"
            if not improvement_file.exists():
                return None
            
            with open(improvement_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to objects
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            data['strategy'] = ImprovementStrategy(data['strategy'])
            
            return PromptImprovement(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading improvement {improvement_id}: {e}")
            return None
    
    async def load_improvements_since(self, since_date: datetime) -> List[PromptImprovement]:
        """Load improvements since given date"""
        improvements = []
        
        try:
            for improvement_file in self.improvements_path.glob("*.json"):
                improvement = await self.load_improvement(improvement_file.stem)
                if improvement and improvement.timestamp >= since_date:
                    improvements.append(improvement)
                    
        except Exception as e:
            self.logger.error(f"Error loading improvements since {since_date}: {e}")
        
        return improvements
    
    # Metrics storage methods
    async def save_metrics(self, metrics: ImprovementMetrics):
        """Save improvement metrics to storage"""
        try:
            metrics_file = self.metrics_path / f"{metrics.improvement_id}.json"
            with open(metrics_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving metrics {metrics.improvement_id}: {e}")
    
    # Template and version management
    async def backup_current_prompt(self, agent_type: str, prompt_content: str) -> Optional[Dict[str, Any]]:
        """Backup current prompt before applying improvement"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.templates_path / f"{agent_type}_backup_{timestamp}.txt"
            
            with open(backup_path, 'w') as f:
                f.write(prompt_content)
            
            return {
                'agent_type': agent_type,
                'backup_path': str(backup_path),
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error backing up prompt for {agent_type}: {e}")
            return None
    
    async def save_improved_prompt(self, agent_type: str, version: str, prompt_content: str) -> bool:
        """Save improved prompt with version"""
        try:
            template_path = self.templates_path / f"{agent_type}_v{version}.txt"
            
            with open(template_path, 'w') as f:
                f.write(prompt_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving improved prompt for {agent_type}: {e}")
            return False
    
    async def update_version_tracking(self, improvement: PromptImprovement):
        """Update version tracking for agent"""
        try:
            version_info = {
                'agent_type': improvement.agent_type,
                'version': improvement.version,
                'improvement_id': improvement.improvement_id,
                'timestamp': improvement.timestamp.isoformat(),
                'strategy': improvement.strategy.value
            }
            
            version_path = self.templates_path / f"{improvement.agent_type}_versions.json"
            versions = []
            
            if version_path.exists():
                with open(version_path, 'r') as f:
                    versions = json.load(f)
            
            versions.append(version_info)
            
            with open(version_path, 'w') as f:
                json.dump(versions, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating version tracking for {improvement.agent_type}: {e}")
    
    async def get_current_prompt(self, agent_type: str) -> Optional[str]:
        """Get current prompt for agent type"""
        try:
            # This would integrate with actual agent prompt storage system
            # For now, simulate with template file
            template_path = self.templates_path / f"{agent_type}_current.txt"
            
            if template_path.exists():
                with open(template_path, 'r') as f:
                    return f.read()
            
            # Return default prompt if none exists
            return f"Default prompt for {agent_type} agent"
            
        except Exception as e:
            self.logger.error(f"Error getting current prompt for {agent_type}: {e}")
            return None
    
    def get_next_version(self, agent_type: str) -> str:
        """Get next version number for agent type"""
        try:
            version_path = self.templates_path / f"{agent_type}_versions.json"
            
            if version_path.exists():
                with open(version_path, 'r') as f:
                    versions = json.load(f)
                
                if versions:
                    # Get latest version and increment
                    latest_version = max(versions, key=lambda x: x['timestamp'])['version']
                    version_parts = latest_version.split('.')
                    version_parts[-1] = str(int(version_parts[-1]) + 1)
                    return '.'.join(version_parts)
            
            return "1.0.0"
            
        except Exception as e:
            self.logger.error(f"Error getting next version for {agent_type}: {e}")
            return "1.0.0"
    
    async def find_backup_for_improvement(self, improvement: PromptImprovement) -> Optional[Path]:
        """Find backup file for improvement"""
        backup_pattern = f"{improvement.agent_type}_backup_*.txt"
        backup_files = list(self.templates_path.glob(backup_pattern))
        
        if not backup_files:
            return None
        
        # Return most recent backup before improvement timestamp
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files[0]
    
    async def restore_prompt_from_backup(self, agent_type: str, backup_path: Path) -> bool:
        """Restore prompt from backup"""
        try:
            with open(backup_path, 'r') as f:
                original_prompt = f.read()
            
            current_template = self.templates_path / f"{agent_type}_current.txt"
            
            with open(current_template, 'w') as f:
                f.write(original_prompt)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring prompt for {agent_type}: {e}")
            return False