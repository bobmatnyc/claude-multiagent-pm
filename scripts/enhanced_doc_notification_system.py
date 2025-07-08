#!/usr/bin/env python3
"""
Enhanced Documentation Change Notification System
FWK-008: Real-time Documentation Change Notifications

This system provides real-time notifications when documentation changes
or validation issues are detected.
"""

import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(__file__))

from enhanced_doc_sync import EnhancedDocumentationSyncManager, ValidationIssue, DocumentationStats

class DocumentationNotificationSystem:
    """Enhanced notification system for documentation changes and issues"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.logs_dir = self.claude_pm_root / "logs"
        self.config_dir = self.claude_pm_root / "config"
        
        # Notification state files
        self.last_notification_file = self.logs_dir / "last_doc_notification.json"
        self.notification_history_file = self.logs_dir / "doc_notifications_history.json"
        
        # Load configuration
        self.config = self._load_notification_config()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Notification settings
        self.notification_cooldown = timedelta(hours=1)  # Don't spam notifications
        self.severity_thresholds = {
            'critical': 0,  # Always notify for critical issues
            'high': 3,      # Notify if more than 3 high issues
            'medium': 10,   # Notify if more than 10 medium issues
            'low': 25       # Notify if more than 25 low issues
        }

    def _load_notification_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        config_file = self.config_dir / "doc_sync_config.json"
        default_config = {
            "notifications_enabled": True,
            "notification_methods": ["file", "log"],
            "email_enabled": False,
            "email_smtp_server": "localhost",
            "email_smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "email_recipients": [],
            "slack_enabled": False,
            "slack_webhook_url": "",
            "file_notifications_dir": str(self.logs_dir),
            "significant_change_threshold": 5.0,
            "critical_issue_immediate": True
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                config = default_config.copy()
                config.update(loaded_config)
                return config
            except Exception as e:
                self.logger.warning(f"Error loading notification config: {e}")
        
        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for notification system"""
        logger = logging.getLogger('DocNotifications')
        logger.setLevel(logging.INFO)
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = self.logs_dir / "doc_notifications.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Clear existing handlers and add new one
        logger.handlers.clear()
        logger.addHandler(file_handler)
        
        return logger

    def check_and_notify(self) -> bool:
        """Check for notification-worthy changes and send notifications"""
        try:
            if not self.config.get("notifications_enabled", True):
                return True
            
            self.logger.info("Checking for notification-worthy documentation changes...")
            
            # Run validation to get current state
            sync_manager = EnhancedDocumentationSyncManager(str(self.claude_pm_root))
            success = sync_manager.sync_documentation(validate_only=True)
            
            # Load current statistics
            stats_file = self.logs_dir / "latest_enhanced_doc_stats.json"
            if not stats_file.exists():
                self.logger.warning("No statistics file found, skipping notification check")
                return True
            
            with open(stats_file, 'r') as f:
                current_stats = json.load(f)
            
            # Check if we should send notifications
            notification_data = self._analyze_changes(current_stats)
            
            if notification_data['should_notify']:
                return self._send_notifications(notification_data)
            else:
                self.logger.info("No significant changes detected, skipping notifications")
                return True
            
        except Exception as e:
            self.logger.error(f"Error in notification check: {e}")
            return False

    def _analyze_changes(self, current_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current statistics and determine if notifications should be sent"""
        notification_data = {
            'should_notify': False,
            'notification_type': 'info',
            'priority': 'low',
            'changes': [],
            'current_stats': current_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Load previous notification state
        previous_state = self._load_last_notification_state()
        
        # Check cooldown period
        if previous_state and self._is_in_cooldown(previous_state):
            return notification_data
        
        # Check for critical issues (always notify)
        critical_issues = [issue for issue in current_stats.get('validation_issues', []) 
                          if issue.get('severity') == 'critical']
        
        if critical_issues:
            notification_data.update({
                'should_notify': True,
                'notification_type': 'critical',
                'priority': 'critical',
                'changes': [f"Critical issues detected: {len(critical_issues)} critical validation problems"]
            })
            return notification_data
        
        # Check for significant changes
        if previous_state:
            changes = self._detect_significant_changes(previous_state, current_stats)
            if changes:
                notification_data.update({
                    'should_notify': True,
                    'notification_type': 'change',
                    'priority': self._determine_change_priority(changes),
                    'changes': changes
                })
                return notification_data
        
        # Check validation issue thresholds
        validation_issues = current_stats.get('validation_issues', [])
        issue_counts = {}
        for issue in validation_issues:
            severity = issue.get('severity', 'low')
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        threshold_exceeded = []
        for severity, threshold in self.severity_thresholds.items():
            count = issue_counts.get(severity, 0)
            if count > threshold:
                threshold_exceeded.append(f"{count} {severity} issues (threshold: {threshold})")
        
        if threshold_exceeded:
            notification_data.update({
                'should_notify': True,
                'notification_type': 'threshold',
                'priority': 'high' if any('critical' in t or 'high' in t for t in threshold_exceeded) else 'medium',
                'changes': threshold_exceeded
            })
        
        return notification_data

    def _load_last_notification_state(self) -> Optional[Dict[str, Any]]:
        """Load the last notification state"""
        if self.last_notification_file.exists():
            try:
                with open(self.last_notification_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading last notification state: {e}")
        return None

    def _is_in_cooldown(self, previous_state: Dict[str, Any]) -> bool:
        """Check if we're still in cooldown period"""
        last_notification = previous_state.get('timestamp')
        if not last_notification:
            return False
        
        try:
            last_time = datetime.fromisoformat(last_notification)
            return datetime.now() - last_time < self.notification_cooldown
        except Exception:
            return False

    def _detect_significant_changes(self, previous_state: Dict[str, Any], current_stats: Dict[str, Any]) -> List[str]:
        """Detect significant changes between states"""
        changes = []
        
        # Compare key metrics
        prev_stats = previous_state.get('current_stats', {})
        
        # Check completion percentage changes
        prev_completion = prev_stats.get('completion_percentage', 0)
        current_completion = current_stats.get('completion_percentage', 0)
        completion_change = current_completion - prev_completion
        
        if abs(completion_change) >= self.config.get('significant_change_threshold', 5.0):
            direction = "increased" if completion_change > 0 else "decreased"
            changes.append(f"Project completion {direction} by {abs(completion_change):.1f}% "
                          f"(from {prev_completion:.1f}% to {current_completion:.1f}%)")
        
        # Check validation issue changes
        prev_issues = len(prev_stats.get('validation_issues', []))
        current_issues = len(current_stats.get('validation_issues', []))
        issue_change = current_issues - prev_issues
        
        if abs(issue_change) >= 5:  # Significant issue count change
            direction = "increased" if issue_change > 0 else "decreased"
            changes.append(f"Validation issues {direction} by {abs(issue_change)} "
                          f"(from {prev_issues} to {current_issues})")
        
        # Check broken links changes
        prev_broken_links = len(prev_stats.get('broken_links', []))
        current_broken_links = len(current_stats.get('broken_links', []))
        link_change = current_broken_links - prev_broken_links
        
        if abs(link_change) >= 3:  # Significant broken link change
            direction = "increased" if link_change > 0 else "decreased"
            changes.append(f"Broken links {direction} by {abs(link_change)} "
                          f"(from {prev_broken_links} to {current_broken_links})")
        
        # Check new inconsistencies
        prev_inconsistencies = len(prev_stats.get('inconsistencies_found', []))
        current_inconsistencies = len(current_stats.get('inconsistencies_found', []))
        
        if current_inconsistencies > prev_inconsistencies:
            new_inconsistencies = current_inconsistencies - prev_inconsistencies
            changes.append(f"New documentation inconsistencies detected: {new_inconsistencies}")
        
        return changes

    def _determine_change_priority(self, changes: List[str]) -> str:
        """Determine priority based on types of changes"""
        if any('critical' in change.lower() for change in changes):
            return 'critical'
        elif any('inconsistencies' in change.lower() or 'increased' in change.lower() for change in changes):
            return 'high'
        elif any('decreased' in change.lower() for change in changes):
            return 'medium'
        else:
            return 'low'

    def _send_notifications(self, notification_data: Dict[str, Any]) -> bool:
        """Send notifications via configured methods"""
        success = True
        
        try:
            # Always log the notification
            self._log_notification(notification_data)
            
            # Send file notification
            if 'file' in self.config.get('notification_methods', []):
                success &= self._send_file_notification(notification_data)
            
            # Send email notification
            if 'email' in self.config.get('notification_methods', []) and self.config.get('email_enabled'):
                success &= self._send_email_notification(notification_data)
            
            # Send Slack notification
            if 'slack' in self.config.get('notification_methods', []) and self.config.get('slack_enabled'):
                success &= self._send_slack_notification(notification_data)
            
            # Update notification state
            self._save_notification_state(notification_data)
            
            # Update notification history
            self._update_notification_history(notification_data)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
            return False

    def _log_notification(self, notification_data: Dict[str, Any]):
        """Log the notification"""
        priority = notification_data['priority']
        notification_type = notification_data['notification_type']
        changes = notification_data['changes']
        
        self.logger.info(f"Sending {priority} notification ({notification_type}):")
        for change in changes:
            self.logger.info(f"  - {change}")

    def _send_file_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send file-based notification"""
        try:
            notification_file = self.logs_dir / "latest_doc_notification.txt"
            
            content = f"""# Documentation Change Notification
Timestamp: {notification_data['timestamp']}
Priority: {notification_data['priority']}
Type: {notification_data['notification_type']}

## Changes Detected:
"""
            
            for change in notification_data['changes']:
                content += f"- {change}\n"
            
            current_stats = notification_data['current_stats']
            content += f"""
## Current Status:
- Completion: {current_stats.get('completion_percentage', 0):.1f}%
- Total Issues: {len(current_stats.get('validation_issues', []))}
- Broken Links: {len(current_stats.get('broken_links', []))}
- Inconsistencies: {len(current_stats.get('inconsistencies_found', []))}

For detailed information, check the latest sync report in the logs directory.
"""
            
            with open(notification_file, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending file notification: {e}")
            return False

    def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            if not self.config.get('email_recipients'):
                return True  # No recipients configured
            
            # Create email content
            subject = f"[Claude PM] Documentation {notification_data['notification_type'].title()} - {notification_data['priority'].upper()}"
            
            body = f"""
Documentation Change Notification

Priority: {notification_data['priority'].upper()}
Timestamp: {notification_data['timestamp']}

Changes Detected:
"""
            
            for change in notification_data['changes']:
                body += f"• {change}\n"
            
            current_stats = notification_data['current_stats']
            body += f"""
Current Documentation Status:
• Project Completion: {current_stats.get('completion_percentage', 0):.1f}%
• Validation Issues: {len(current_stats.get('validation_issues', []))}
• Broken Links: {len(current_stats.get('broken_links', []))}
• Cross-file Inconsistencies: {len(current_stats.get('inconsistencies_found', []))}

Please check the documentation sync reports for detailed information.
"""
            
            # Send email (implementation would depend on SMTP configuration)
            self.logger.info(f"Email notification prepared (not sent - SMTP not configured)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
            return False

    def _send_slack_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send Slack notification"""
        try:
            # Slack webhook implementation would go here
            self.logger.info(f"Slack notification prepared (not sent - webhook not configured)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
            return False

    def _save_notification_state(self, notification_data: Dict[str, Any]):
        """Save the current notification state"""
        try:
            with open(self.last_notification_file, 'w') as f:
                json.dump(notification_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving notification state: {e}")

    def _update_notification_history(self, notification_data: Dict[str, Any]):
        """Update notification history"""
        try:
            history = []
            
            if self.notification_history_file.exists():
                try:
                    with open(self.notification_history_file, 'r') as f:
                        history = json.load(f)
                except:
                    history = []
            
            # Add current notification to history
            history_entry = {
                'timestamp': notification_data['timestamp'],
                'priority': notification_data['priority'],
                'type': notification_data['notification_type'],
                'changes_count': len(notification_data['changes']),
                'changes': notification_data['changes'][:3]  # Store only first 3 changes
            }
            
            history.append(history_entry)
            
            # Keep only last 50 notifications
            history = history[-50:]
            
            with open(self.notification_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating notification history: {e}")

    def get_notification_status(self) -> Dict[str, Any]:
        """Get current notification system status"""
        return {
            'notifications_enabled': self.config.get('notifications_enabled', False),
            'notification_methods': self.config.get('notification_methods', []),
            'last_notification': self._load_last_notification_state(),
            'cooldown_remaining': self._get_cooldown_remaining(),
            'config': {
                'cooldown_hours': self.notification_cooldown.total_seconds() / 3600,
                'severity_thresholds': self.severity_thresholds,
                'significant_change_threshold': self.config.get('significant_change_threshold')
            }
        }

    def _get_cooldown_remaining(self) -> Optional[str]:
        """Get remaining cooldown time"""
        previous_state = self._load_last_notification_state()
        if not previous_state:
            return None
        
        if self._is_in_cooldown(previous_state):
            last_notification = datetime.fromisoformat(previous_state['timestamp'])
            next_notification = last_notification + self.notification_cooldown
            remaining = next_notification - datetime.now()
            return str(remaining).split('.')[0]  # Remove microseconds
        
        return None


def main():
    """Main entry point for notification system testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Documentation Notification System"
    )
    parser.add_argument(
        "--claude-pm-root", 
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--check-now", 
        action="store_true",
        help="Check for notifications immediately"
    )
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show notification system status"
    )
    
    args = parser.parse_args()
    
    notification_system = DocumentationNotificationSystem(args.claude_pm_root)
    
    if args.status:
        status = notification_system.get_notification_status()
        print(json.dumps(status, indent=2))
        return 0
    
    if args.check_now:
        success = notification_system.check_and_notify()
        print("✅ Notification check completed successfully" if success else "❌ Notification check failed")
        return 0 if success else 1
    
    print("Enhanced Documentation Notification System")
    print("Use --check-now to test notifications or --status to see configuration")
    return 0


if __name__ == "__main__":
    exit(main())