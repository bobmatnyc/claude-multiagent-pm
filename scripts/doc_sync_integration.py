#!/usr/bin/env python3
"""
Documentation Synchronization Integration Script
Part of M01-041: Implement Documentation Status Synchronization System

This script provides integration between documentation synchronization and 
the existing Claude PM health monitoring infrastructure.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))

from sync_docs import DocumentationSyncManager, DocumentationStats
from doc_notification_system import DocumentationNotificationSystem
from doc_sync_config import DocSyncConfigManager

class DocSyncHealthIntegration:
    """Integrates documentation sync with Claude PM health monitoring"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.config_manager = DocSyncConfigManager(claude_pm_root)
        self.config = self.config_manager.get_effective_config()
        
        # Health monitoring paths
        self.health_dir = self.claude_pm_root / "logs"
        self.health_report_file = self.health_dir / "health-report.json"
        self.health_status_file = self.health_dir / "monitor-status.json"
        
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for health integration"""
        logger = logging.getLogger('DocSyncHealth')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            # Create file handler
            log_file = self.health_dir / "doc_sync_health.log"
            self.health_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, self.config.log_level))
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def check_documentation_health(self) -> Dict[str, Any]:
        """Check documentation health and return status"""
        health_status = {
            'service': 'documentation_sync',
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'details': {},
            'metrics': {},
            'alerts': []
        }
        
        try:
            # Run documentation synchronization check
            sync_manager = DocumentationSyncManager(str(self.claude_pm_root))
            
            # Parse tickets and generate statistics
            tickets = sync_manager.parse_backlog_tickets()
            stats = sync_manager.generate_statistics(tickets)
            
            # Check for inconsistencies
            inconsistencies = sync_manager.validate_documentation_consistency(tickets)
            stats.inconsistencies_found = inconsistencies
            
            # Determine health status
            if inconsistencies:
                health_status['status'] = 'warning' if len(inconsistencies) <= 3 else 'error'
                health_status['alerts'].append(f"{len(inconsistencies)} documentation inconsistencies found")
            else:
                health_status['status'] = 'healthy'
            
            # Add detailed metrics
            health_status['metrics'] = {
                'total_tickets': stats.total_tickets,
                'completed_tickets': stats.completed_tickets,
                'completion_percentage': stats.completion_percentage,
                'phase_1_completion': stats.phase_1_completion,
                'total_story_points': stats.total_story_points,
                'completed_story_points': stats.completed_story_points,
                'inconsistencies_count': len(inconsistencies),
                'last_sync': stats.last_update
            }
            
            # Add detailed information
            health_status['details'] = {
                'backlog_file': str(self.claude_pm_root / "trackdown" / "BACKLOG.md"),
                'ticketing_file': str(self.claude_pm_root / "docs" / "TICKETING_SYSTEM.md"),
                'tickets_parsed': len(tickets),
                'inconsistencies': inconsistencies[:5] if inconsistencies else []  # Show first 5
            }
            
            self.logger.info(f"Documentation health check completed: {health_status['status']}")
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['alerts'].append(f"Documentation health check failed: {str(e)}")
            self.logger.error(f"Error during documentation health check: {e}")
        
        return health_status
    
    def update_health_monitoring(self) -> bool:
        """Update the health monitoring system with documentation status"""
        try:
            doc_health = self.check_documentation_health()
            
            # Read existing health report
            health_report = {}
            if self.health_report_file.exists():
                try:
                    with open(self.health_report_file, 'r') as f:
                        health_report = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not read existing health report: {e}")
                    health_report = {}
            
            # Update with documentation status
            health_report['services'] = health_report.get('services', {})
            health_report['services']['documentation_sync'] = doc_health
            health_report['last_updated'] = datetime.now().isoformat()
            
            # Calculate overall health status
            service_statuses = [service['status'] for service in health_report['services'].values()]
            if 'error' in service_statuses:
                health_report['overall_status'] = 'error'
            elif 'warning' in service_statuses:
                health_report['overall_status'] = 'warning'
            else:
                health_report['overall_status'] = 'healthy'
            
            # Write updated health report
            with open(self.health_report_file, 'w') as f:
                json.dump(health_report, f, indent=2)
            
            # Update monitor status file
            monitor_status = {
                'documentation_sync': {
                    'enabled': True,
                    'last_check': datetime.now().isoformat(),
                    'status': doc_health['status'],
                    'next_check': 'continuous'
                }
            }
            
            if self.health_status_file.exists():
                try:
                    with open(self.health_status_file, 'r') as f:
                        existing_status = json.load(f)
                        existing_status.update(monitor_status)
                        monitor_status = existing_status
                except Exception as e:
                    self.logger.warning(f"Could not read existing monitor status: {e}")
            
            with open(self.health_status_file, 'w') as f:
                json.dump(monitor_status, f, indent=2)
            
            self.logger.info("Updated health monitoring with documentation status")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating health monitoring: {e}")
            return False
    
    def run_full_sync_with_health_update(self) -> bool:
        """Run full documentation sync and update health monitoring"""
        try:
            self.logger.info("Starting full documentation sync with health update")
            
            # Run documentation synchronization
            sync_manager = DocumentationSyncManager(str(self.claude_pm_root))
            sync_success = sync_manager.sync_documentation(validate_only=False)
            
            # Check for notifications
            if self.config.health_monitoring_enabled:
                notification_system = DocumentationNotificationSystem(str(self.claude_pm_root))
                notification_system.check_and_notify()
            
            # Update health monitoring
            health_success = self.update_health_monitoring()
            
            success = sync_success and health_success
            self.logger.info(f"Full sync with health update completed: {'success' if success else 'failed'}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during full sync with health update: {e}")
            return False
    
    def generate_health_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive health summary for documentation"""
        try:
            doc_health = self.check_documentation_health()
            
            # Load latest statistics
            stats_file = self.claude_pm_root / "logs" / "latest_doc_stats.json"
            latest_stats = None
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    latest_stats = json.load(f)
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'documentation_health': doc_health,
                'configuration': self.config.to_dict(),
                'latest_statistics': latest_stats,
                'integration_status': {
                    'health_monitoring_enabled': self.config.health_monitoring_enabled,
                    'notification_system_active': True,
                    'pre_commit_hooks_installed': (self.claude_pm_root / ".git" / "hooks" / "pre-commit").exists(),
                    'automated_sync_configured': (self.claude_pm_root / "claude-pm-doc-sync.service").exists()
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating health summary: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

def main():
    """Main entry point for documentation sync health integration"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Synchronization Health Integration for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root",
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check documentation health status"
    )
    parser.add_argument(
        "--update-health",
        action="store_true",
        help="Update health monitoring with documentation status"
    )
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="Run full sync with health monitoring update"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate comprehensive health summary"
    )
    parser.add_argument(
        "--output-file",
        help="Output file for summary (default: stdout)"
    )
    
    args = parser.parse_args()
    
    integration = DocSyncHealthIntegration(args.claude_pm_root)
    
    if args.check_health:
        health_status = integration.check_documentation_health()
        print(json.dumps(health_status, indent=2))
        return 0 if health_status['status'] in ['healthy', 'warning'] else 1
    
    if args.update_health:
        success = integration.update_health_monitoring()
        print(f"{'✅' if success else '❌'} Health monitoring update")
        return 0 if success else 1
    
    if args.full_sync:
        success = integration.run_full_sync_with_health_update()
        print(f"{'✅' if success else '❌'} Full sync with health update")
        return 0 if success else 1
    
    if args.summary or not any([args.check_health, args.update_health, args.full_sync]):
        summary = integration.generate_health_summary()
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Health summary written to {args.output_file}")
        else:
            print(json.dumps(summary, indent=2))
        
        return 0
    
    return 0

if __name__ == "__main__":
    exit(main())