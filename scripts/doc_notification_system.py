#!/usr/bin/env python3
"""
Documentation Status Notification System for Claude PM Framework
Part of M01-041: Implement Documentation Status Synchronization System

This system provides automated notifications for documentation status updates,
integrating with the existing health monitoring infrastructure.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))

from sync_docs import DocumentationSyncManager, DocumentationStats

class DocumentationNotificationSystem:
    """Handles notifications for documentation status changes"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.logs_dir = self.claude_pm_root / "logs"
        self.notifications_log = self.logs_dir / "doc_notifications.log"
        self.stats_history = self.logs_dir / "doc_stats_history.json"
        self.logger = self._setup_logging()
        
        # Notification thresholds
        self.significant_change_threshold = 5  # 5% change in completion
        self.alert_on_inconsistencies = True
        self.notification_cooldown = 3600  # 1 hour between notifications

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for notification system"""
        logger = logging.getLogger('DocNotifications')
        logger.setLevel(logging.INFO)
        
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(self.notifications_log)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger

    def load_previous_stats(self) -> Optional[DocumentationStats]:
        """Load the previous statistics for comparison"""
        try:
            if self.stats_history.exists():
                with open(self.stats_history, 'r') as f:
                    history = json.load(f)
                    if history and len(history) > 0:
                        # Get the most recent entry
                        latest = max(history, key=lambda x: x['timestamp'])
                        return DocumentationStats(**latest['stats'])
            return None
        except Exception as e:
            self.logger.error(f"Error loading previous stats: {e}")
            return None

    def save_stats_to_history(self, stats: DocumentationStats) -> None:
        """Save current statistics to history"""
        try:
            history = []
            if self.stats_history.exists():
                with open(self.stats_history, 'r') as f:
                    history = json.load(f)
            
            # Add current stats
            history.append({
                'timestamp': datetime.now().isoformat(),
                'stats': stats.to_dict()
            })
            
            # Keep only last 100 entries
            history = history[-100:]
            
            with open(self.stats_history, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving stats to history: {e}")

    def detect_significant_changes(self, previous: Optional[DocumentationStats], current: DocumentationStats) -> List[str]:
        """Detect significant changes between previous and current stats"""
        changes = []
        
        if previous is None:
            changes.append(f"📊 Initial documentation scan: {current.total_tickets} tickets, {current.completion_percentage:.1f}% complete")
            return changes
        
        # Check completion percentage change
        completion_diff = current.completion_percentage - previous.completion_percentage
        if abs(completion_diff) >= self.significant_change_threshold:
            direction = "📈" if completion_diff > 0 else "📉"
            changes.append(f"{direction} Completion changed by {completion_diff:+.1f}% ({previous.completion_percentage:.1f}% → {current.completion_percentage:.1f}%)")
        
        # Check new completed tickets
        new_completed = current.completed_tickets - previous.completed_tickets
        if new_completed > 0:
            changes.append(f"✅ {new_completed} new tickets completed")
        
        # Check new blocked/in-progress tickets
        new_in_progress = current.in_progress_tickets - previous.in_progress_tickets
        if new_in_progress > 0:
            changes.append(f"🔄 {new_in_progress} tickets moved to in-progress")
        
        new_blocked = current.blocked_tickets - previous.blocked_tickets
        if new_blocked > 0:
            changes.append(f"🚫 {new_blocked} tickets became blocked")
        
        # Check story points progress
        points_diff = current.completed_story_points - previous.completed_story_points
        if points_diff > 0:
            changes.append(f"📊 {points_diff} story points completed")
        
        # Check Phase 1 progress
        phase1_diff = current.phase_1_completion - previous.phase_1_completion
        if abs(phase1_diff) >= 5:  # 5% threshold for Phase 1
            direction = "📈" if phase1_diff > 0 else "📉"
            changes.append(f"{direction} Phase 1 progress: {phase1_diff:+.1f}% ({previous.phase_1_completion:.1f}% → {current.phase_1_completion:.1f}%)")
        
        return changes

    def should_send_notification(self) -> bool:
        """Check if enough time has passed since last notification"""
        try:
            last_notification_file = self.logs_dir / "last_doc_notification.txt"
            if last_notification_file.exists():
                with open(last_notification_file, 'r') as f:
                    last_time = datetime.fromisoformat(f.read().strip())
                    if datetime.now() - last_time < timedelta(seconds=self.notification_cooldown):
                        return False
            return True
        except Exception:
            return True

    def record_notification_sent(self) -> None:
        """Record that a notification was sent"""
        try:
            last_notification_file = self.logs_dir / "last_doc_notification.txt"
            with open(last_notification_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            self.logger.error(f"Error recording notification time: {e}")

    def send_notification(self, changes: List[str], stats: DocumentationStats) -> None:
        """Send notification about documentation changes"""
        if not changes:
            return
        
        if not self.should_send_notification():
            self.logger.debug("Skipping notification due to cooldown period")
            return
        
        # Format notification message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_lines = [
            f"📋 Claude PM Documentation Update - {timestamp}",
            "",
            "🔄 Changes detected:",
        ]
        
        for change in changes:
            message_lines.append(f"  • {change}")
        
        message_lines.extend([
            "",
            f"📊 Current Status:",
            f"  • Total Tickets: {stats.total_tickets}",
            f"  • Completed: {stats.completed_tickets} ({stats.completion_percentage:.1f}%)",
            f"  • Story Points: {stats.completed_story_points}/{stats.total_story_points} ({stats.completed_story_points/stats.total_story_points*100:.1f}%)",
            f"  • Phase 1: {stats.phase_1_completion:.1f}% complete",
        ])
        
        if stats.inconsistencies_found:
            message_lines.extend([
                "",
                f"⚠️ Inconsistencies Found: {len(stats.inconsistencies_found)}",
            ])
            for inconsistency in stats.inconsistencies_found[:3]:  # Show first 3
                message_lines.append(f"  • {inconsistency}")
            if len(stats.inconsistencies_found) > 3:
                message_lines.append(f"  • ... and {len(stats.inconsistencies_found) - 3} more")
        
        notification_message = "\n".join(message_lines)
        
        # Log the notification
        self.logger.info("Documentation notification sent:")
        for line in message_lines:
            self.logger.info(line)
        
        # Write to notification file for external monitoring
        notification_file = self.logs_dir / "latest_doc_notification.txt"
        with open(notification_file, 'w') as f:
            f.write(notification_message)
        
        # Write to health alerts log for integration with health monitoring
        health_alerts_log = self.logs_dir / "health-alerts.log"
        with open(health_alerts_log, 'a') as f:
            f.write(f"\n[DOC-NOTIFICATION] {timestamp}\n")
            f.write(notification_message)
            f.write("\n" + "="*50 + "\n")
        
        self.record_notification_sent()
        
        print("📧 Documentation notification sent")
        print(f"📁 Notification saved to: {notification_file}")

    def check_and_notify(self) -> bool:
        """Main method to check documentation status and send notifications if needed"""
        try:
            # Get current documentation status
            sync_manager = DocumentationSyncManager(str(self.claude_pm_root))
            tickets = sync_manager.parse_backlog_tickets()
            current_stats = sync_manager.generate_statistics(tickets)
            
            # Check for inconsistencies
            inconsistencies = sync_manager.validate_documentation_consistency(tickets)
            current_stats.inconsistencies_found = inconsistencies
            
            # Load previous stats for comparison
            previous_stats = self.load_previous_stats()
            
            # Detect changes
            changes = self.detect_significant_changes(previous_stats, current_stats)
            
            # Add inconsistency alerts
            if inconsistencies and self.alert_on_inconsistencies:
                changes.append(f"⚠️ {len(inconsistencies)} documentation inconsistencies detected")
            
            # Send notification if there are significant changes
            if changes:
                self.send_notification(changes, current_stats)
            
            # Save current stats for next comparison
            self.save_stats_to_history(current_stats)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in documentation notification check: {e}")
            return False


def main():
    """Main entry point for doc notification system"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Status Notification System for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root", 
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force notification even if no significant changes"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test notification system without checking for changes"
    )
    
    args = parser.parse_args()
    
    notification_system = DocumentationNotificationSystem(args.claude_pm_root)
    
    if args.test:
        # Test notification with dummy data
        from sync_docs import DocumentationStats
        test_stats = DocumentationStats(
            total_tickets=136,
            completed_tickets=61,
            in_progress_tickets=0,
            pending_tickets=75,
            blocked_tickets=0,
            completion_percentage=44.9,
            total_story_points=724,
            completed_story_points=334,
            phase_1_completion=75.0,
            inconsistencies_found=[],
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        test_changes = ["🧪 Test notification from documentation system"]
        notification_system.send_notification(test_changes, test_stats)
        print("✅ Test notification sent")
        return 0
    
    if args.force:
        # Temporarily disable cooldown
        notification_system.notification_cooldown = 0
    
    success = notification_system.check_and_notify()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())