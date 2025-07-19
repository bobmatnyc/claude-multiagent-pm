#!/usr/bin/env python3
"""
Framework Protector Service - Extract from Parent Directory Manager
==================================================================

Handles framework protection operations for the Claude PM Framework.
This module is extracted from parent_directory_manager.py as part of
the refactoring effort (ISS-0154).

Key Features:
- Framework template protection
- File integrity validation
- Protection guidance and logging
- Critical file safeguarding

Created: 2025-07-18
Author: Engineer Agent
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum


class ProtectionLevel(Enum):
    """Protection levels for framework files."""
    CRITICAL = "critical"      # Never modify or delete
    PROTECTED = "protected"    # Modify only with explicit permission
    MANAGED = "managed"        # Can be modified following rules
    UNPROTECTED = "unprotected"  # No special protection


@dataclass
class ProtectionStatus:
    """Status of file protection."""
    file_path: Path
    protection_level: ProtectionLevel
    is_protected: bool
    reason: str
    checksum: Optional[str] = None
    last_validated: Optional[datetime] = None


class FrameworkProtector:
    """
    Manages framework protection operations for the Claude PM Framework.
    
    This class provides:
    - Critical file protection mechanisms
    - Integrity validation for framework files
    - Protection guidance and enforcement
    - Safeguards against accidental modifications
    """
    
    def __init__(self, framework_path: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize the Framework Protector.
        
        Args:
            framework_path: Path to the framework directory
            logger: Optional logger instance
        """
        self.framework_path = Path(framework_path)
        self.logger = logger or logging.getLogger(__name__)
        
        # Define critical protected files
        self.critical_files = {
            "framework/CLAUDE.md": ProtectionLevel.CRITICAL,
            "VERSION": ProtectionLevel.CRITICAL,
            "claude_pm/services/parent_directory_manager.py": ProtectionLevel.PROTECTED,
            ".claude-pm/framework_backups": ProtectionLevel.PROTECTED,
        }
        
        # Protection state
        self.protection_enabled = True
        self.validation_cache: Dict[str, ProtectionStatus] = {}
        
    def is_critical_file(self, file_path: Path) -> bool:
        """
        Check if a file is critical and should never be deleted.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is critical
        """
        # Normalize path for comparison
        try:
            relative_path = file_path.relative_to(self.framework_path)
        except ValueError:
            # Not within framework path
            return False
            
        str_path = str(relative_path).replace(os.sep, '/')
        
        # Check against critical files
        for critical_path, level in self.critical_files.items():
            if str_path == critical_path and level == ProtectionLevel.CRITICAL:
                return True
                
        return False
        
    def get_protection_status(self, file_path: Path) -> ProtectionStatus:
        """
        Get protection status for a file.
        
        Args:
            file_path: Path to check
            
        Returns:
            Protection status
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self.validation_cache:
            cached = self.validation_cache[cache_key]
            # Cache for 5 minutes
            if cached.last_validated and (datetime.now() - cached.last_validated).seconds < 300:
                return cached
                
        # Determine protection level
        protection_level = self._get_protection_level(file_path)
        is_protected = protection_level in [ProtectionLevel.CRITICAL, ProtectionLevel.PROTECTED]
        
        # Create status
        status = ProtectionStatus(
            file_path=file_path,
            protection_level=protection_level,
            is_protected=is_protected,
            reason=self._get_protection_reason(protection_level),
            checksum=self._calculate_checksum(file_path) if file_path.exists() else None,
            last_validated=datetime.now()
        )
        
        # Cache result
        self.validation_cache[cache_key] = status
        
        return status
        
    def _get_protection_level(self, file_path: Path) -> ProtectionLevel:
        """Get protection level for a file."""
        try:
            relative_path = file_path.relative_to(self.framework_path)
            str_path = str(relative_path).replace(os.sep, '/')
            
            # Check exact matches
            if str_path in self.critical_files:
                return self.critical_files[str_path]
                
            # Check patterns
            if str_path.startswith(".claude-pm/framework_backups/"):
                return ProtectionLevel.PROTECTED
            elif str_path.startswith("framework/") and str_path.endswith("CLAUDE.md"):
                return ProtectionLevel.CRITICAL
            elif str_path.startswith(".claude-pm/"):
                return ProtectionLevel.MANAGED
            else:
                return ProtectionLevel.UNPROTECTED
                
        except ValueError:
            # Not within framework
            return ProtectionLevel.UNPROTECTED
            
    def _get_protection_reason(self, level: ProtectionLevel) -> str:
        """Get human-readable protection reason."""
        reasons = {
            ProtectionLevel.CRITICAL: "Critical framework file - deletion would break all deployments",
            ProtectionLevel.PROTECTED: "Protected framework component - modification requires authorization",
            ProtectionLevel.MANAGED: "Managed by framework - follow modification guidelines",
            ProtectionLevel.UNPROTECTED: "No special protection required"
        }
        return reasons.get(level, "Unknown protection level")
        
    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate file checksum."""
        if not file_path.exists():
            return None
            
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None
            
    def protect_framework_template(self, framework_template_path: Path) -> None:
        """
        Apply protection to framework template.
        
        Args:
            framework_template_path: Path to framework template
        """
        if not framework_template_path.exists():
            self.logger.warning(f"Framework template not found: {framework_template_path}")
            return
            
        try:
            # Ensure read permissions
            current_mode = framework_template_path.stat().st_mode
            if not (current_mode & 0o444):  # Check if readable
                import stat
                framework_template_path.chmod(current_mode | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                self.logger.info(f"Set read permissions on: {framework_template_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to protect framework template: {e}")
            
    def validate_framework_integrity(self) -> Dict[str, Any]:
        """
        Validate integrity of critical framework files.
        
        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "critical_files_missing": [],
            "critical_files_modified": [],
            "protected_files_missing": [],
            "warnings": [],
            "checked_files": 0,
            "validation_time": datetime.now().isoformat()
        }
        
        # Check each critical/protected file
        for file_path, level in self.critical_files.items():
            full_path = self.framework_path / file_path
            results["checked_files"] += 1
            
            if not full_path.exists():
                if level == ProtectionLevel.CRITICAL:
                    results["critical_files_missing"].append(str(file_path))
                    results["valid"] = False
                elif level == ProtectionLevel.PROTECTED:
                    results["protected_files_missing"].append(str(file_path))
                    results["warnings"].append(f"Protected file missing: {file_path}")
                    
            else:
                # For critical files, we could check against known good checksums
                # For now, just verify they exist and are readable
                try:
                    with open(full_path, 'rb') as f:
                        f.read(1)  # Try to read one byte
                except Exception as e:
                    results["warnings"].append(f"Cannot read {file_path}: {e}")
                    
        return results
        
    def log_protection_guidance(self, target_file: Path, action: str) -> None:
        """
        Log detailed protection guidance for a file operation.
        
        Args:
            target_file: File being operated on
            action: Action being attempted (delete, modify, etc.)
        """
        status = self.get_protection_status(target_file)
        
        self.logger.error("")
        self.logger.error(f"🚫 {action.upper()} BLOCKED BY FRAMEWORK PROTECTION")
        self.logger.error("=" * 60)
        self.logger.error(f"Target file: {target_file}")
        self.logger.error(f"Protection level: {status.protection_level.value}")
        self.logger.error(f"Reason: {status.reason}")
        self.logger.error("")
        
        if status.protection_level == ProtectionLevel.CRITICAL:
            self.logger.error("⚠️  CRITICAL FILE WARNING:")
            self.logger.error("This file is ESSENTIAL for framework operation.")
            self.logger.error("Deletion or modification would break ALL framework deployments.")
            self.logger.error("")
            self.logger.error("🛡️  PROTECTION RATIONALE:")
            self.logger.error("• framework/CLAUDE.md - Master template for all deployments")
            self.logger.error("• VERSION - Framework version reference")
            self.logger.error("• Protection mechanisms - Prevent accidental corruption")
            
        elif status.protection_level == ProtectionLevel.PROTECTED:
            self.logger.error("📋 PROTECTED FILE NOTICE:")
            self.logger.error("This file is protected by framework policies.")
            self.logger.error("Modification requires explicit authorization.")
            self.logger.error("")
            self.logger.error("✅ TO MODIFY THIS FILE:")
            self.logger.error("1. Ensure you understand the implications")
            self.logger.error("2. Create a backup first")
            self.logger.error("3. Use appropriate framework commands")
            self.logger.error("4. Test thoroughly after modification")
            
        self.logger.error("")
        self.logger.error("📚 For more information, see framework documentation.")
        self.logger.error("=" * 60)
        self.logger.error("")
        
    def enforce_protection(self, file_path: Path, action: str) -> bool:
        """
        Enforce protection rules for a file operation.
        
        Args:
            file_path: File to operate on
            action: Action to perform
            
        Returns:
            True if action is allowed, False if blocked
        """
        if not self.protection_enabled:
            return True
            
        status = self.get_protection_status(file_path)
        
        # Block critical operations on critical files
        if status.protection_level == ProtectionLevel.CRITICAL:
            if action in ["delete", "remove", "unlink"]:
                self.log_protection_guidance(file_path, action)
                return False
                
        # Warn about protected files
        if status.protection_level == ProtectionLevel.PROTECTED:
            if action in ["modify", "edit", "write"]:
                self.logger.warning(f"Modifying protected file: {file_path}")
                
        return True
        
    def clear_validation_cache(self) -> None:
        """Clear the validation cache."""
        self.validation_cache.clear()
        self.logger.debug("Cleared protection validation cache")
        
    def get_protected_files_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all protected files.
        
        Returns:
            List of protected file information
        """
        protected_files = []
        
        for file_path, level in self.critical_files.items():
            full_path = self.framework_path / file_path
            info = {
                "path": str(file_path),
                "full_path": str(full_path),
                "protection_level": level.value,
                "exists": full_path.exists(),
                "reason": self._get_protection_reason(level)
            }
            
            if full_path.exists():
                try:
                    stat = full_path.stat()
                    info["size"] = stat.st_size
                    info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except Exception:
                    pass
                    
            protected_files.append(info)
            
        return protected_files