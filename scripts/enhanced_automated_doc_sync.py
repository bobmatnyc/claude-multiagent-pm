#!/usr/bin/env python3
"""
Enhanced Automated Documentation Synchronization Service
FWK-008: Complete Documentation Synchronization System

This enhanced service integrates:
1. Enhanced documentation synchronization (progressive structure support)
2. Real-time validation and path checking
3. Intelligent change notifications
4. Health monitoring integration
5. Comprehensive error handling and recovery
"""

import asyncio
import signal
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from enhanced_doc_sync import EnhancedDocumentationSyncManager
from enhanced_doc_notification_system import DocumentationNotificationSystem

class EnhancedAutomatedDocSyncService:
    """Enhanced automated service for comprehensive documentation synchronization"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.sync_manager = EnhancedDocumentationSyncManager(str(claude_pm_root))
        self.notification_system = DocumentationNotificationSystem(str(claude_pm_root))
        
        # Service configuration
        self.sync_interval = 300  # 5 minutes
        self.validation_interval = 180  # 3 minutes (more frequent for validation)
        self.notification_check_interval = 600  # 10 minutes
        self.force_sync_interval = 3600  # 1 hour
        self.health_check_interval = 900  # 15 minutes
        
        # Service state
        self.running = False
        self.last_sync = None
        self.last_validation = None
        self.last_notification_check = None
        self.last_force_sync = None
        self.last_health_check = None
        
        # Performance monitoring
        self.performance_stats = {
            'sync_count': 0,
            'validation_count': 0,
            'notification_count': 0,
            'error_count': 0,
            'start_time': None,
            'last_error': None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def _perform_validation_only(self) -> bool:
        """Perform quick validation without full sync"""
        try:
            print("🔍 Performing quick validation check...")
            success = self.sync_manager.sync_documentation(validate_only=True)
            
            if success:
                print("✅ Quick validation completed successfully")
                self.last_validation = datetime.now()
                self.performance_stats['validation_count'] += 1
                return True
            else:
                print("⚠️ Quick validation found issues")
                return False
                
        except Exception as e:
            print(f"❌ Error during quick validation: {e}")
            self.performance_stats['error_count'] += 1
            self.performance_stats['last_error'] = str(e)
            return False

    async def _perform_full_sync(self, force: bool = False) -> bool:
        """Perform full documentation synchronization"""
        try:
            if force:
                print("🔄 Performing forced full documentation synchronization...")
            else:
                print("🔄 Performing full documentation synchronization...")
            
            success = self.sync_manager.sync_documentation(validate_only=False)
            
            if success:
                print("✅ Full documentation synchronization completed successfully")
                self.last_sync = datetime.now()
                self.performance_stats['sync_count'] += 1
                return True
            else:
                print("❌ Full documentation synchronization found issues")
                return False
                
        except Exception as e:
            print(f"❌ Error during full documentation synchronization: {e}")
            self.performance_stats['error_count'] += 1
            self.performance_stats['last_error'] = str(e)
            return False

    async def _check_notifications(self) -> bool:
        """Check for notification-worthy changes"""
        try:
            print("📧 Checking for notification-worthy changes...")
            success = self.notification_system.check_and_notify()
            
            if success:
                self.last_notification_check = datetime.now()
                self.performance_stats['notification_count'] += 1
                return True
            else:
                print("❌ Notification check failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during notification check: {e}")
            self.performance_stats['error_count'] += 1
            self.performance_stats['last_error'] = str(e)
            return False

    async def _perform_health_check(self) -> bool:
        """Perform health check and update monitoring systems"""
        try:
            print("🏥 Performing health check integration...")
            
            # Load latest statistics
            stats_file = self.claude_pm_root / "logs" / "latest_enhanced_doc_stats.json"
            
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                
                # Create health report
                health_report = {
                    'timestamp': datetime.now().isoformat(),
                    'service_status': 'healthy' if self.performance_stats['error_count'] == 0 else 'degraded',
                    'documentation_health': {
                        'validation_passed': len(stats.get('validation_issues', [])) == 0,
                        'total_issues': len(stats.get('validation_issues', [])),
                        'broken_links': len(stats.get('broken_links', [])),
                        'completion_percentage': stats.get('completion_percentage', 0)
                    },
                    'service_performance': self.performance_stats.copy(),
                    'uptime_hours': (datetime.now() - self.performance_stats['start_time']).total_seconds() / 3600 if self.performance_stats['start_time'] else 0
                }
                
                # Save health report
                health_file = self.claude_pm_root / "logs" / "enhanced_doc_sync_health.json"
                with open(health_file, 'w') as f:
                    json.dump(health_report, f, indent=2)
                
                self.last_health_check = datetime.now()
                print("✅ Health check completed successfully")
                return True
            else:
                print("⚠️ No statistics file found for health check")
                return False
                
        except Exception as e:
            print(f"❌ Error during health check: {e}")
            self.performance_stats['error_count'] += 1
            self.performance_stats['last_error'] = str(e)
            return False

    def _should_run_operation(self, last_run: datetime, interval: int) -> bool:
        """Check if enough time has passed to run an operation"""
        if last_run is None:
            return True
        return datetime.now() - last_run >= timedelta(seconds=interval)

    async def _service_loop(self):
        """Enhanced main service loop"""
        print("🚀 Starting enhanced automated documentation synchronization service...")
        print(f"📁 Claude PM Root: {self.claude_pm_root}")
        print(f"⏱️ Sync Interval: {self.sync_interval}s")
        print(f"🔍 Validation Interval: {self.validation_interval}s")
        print(f"📧 Notification Check Interval: {self.notification_check_interval}s")
        print(f"🔄 Force Sync Interval: {self.force_sync_interval}s")
        print(f"🏥 Health Check Interval: {self.health_check_interval}s")
        
        self.running = True
        self.performance_stats['start_time'] = datetime.now()
        
        # Perform initial operations
        await self._perform_full_sync(force=True)
        await self._check_notifications()
        await self._perform_health_check()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Quick validation check (most frequent)
                if self._should_run_operation(self.last_validation, self.validation_interval):
                    await self._perform_validation_only()
                
                # Regular full sync
                if self._should_run_operation(self.last_sync, self.sync_interval):
                    await self._perform_full_sync()
                
                # Notification check
                if self._should_run_operation(self.last_notification_check, self.notification_check_interval):
                    await self._check_notifications()
                
                # Forced sync
                if self._should_run_operation(self.last_force_sync, self.force_sync_interval):
                    await self._perform_full_sync(force=True)
                    self.last_force_sync = current_time
                
                # Health check
                if self._should_run_operation(self.last_health_check, self.health_check_interval):
                    await self._perform_health_check()
                
                # Sleep for a short period before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in service loop: {e}")
                self.performance_stats['error_count'] += 1
                self.performance_stats['last_error'] = str(e)
                await asyncio.sleep(60)  # Wait longer on error
        
        print("🛑 Enhanced automated documentation synchronization service stopped")
        self._print_service_summary()

    def _print_service_summary(self):
        """Print service performance summary"""
        if self.performance_stats['start_time']:
            uptime = datetime.now() - self.performance_stats['start_time']
            print(f"\n📊 Service Performance Summary:")
            print(f"  Uptime: {uptime}")
            print(f"  Sync Operations: {self.performance_stats['sync_count']}")
            print(f"  Validation Checks: {self.performance_stats['validation_count']}")
            print(f"  Notifications Sent: {self.performance_stats['notification_count']}")
            print(f"  Errors Encountered: {self.performance_stats['error_count']}")
            if self.performance_stats['last_error']:
                print(f"  Last Error: {self.performance_stats['last_error']}")

    def run(self):
        """Run the enhanced automated service"""
        try:
            asyncio.run(self._service_loop())
        except KeyboardInterrupt:
            print("\n🛑 Service interrupted by user")
        except Exception as e:
            print(f"❌ Service failed: {e}")
            return 1
        return 0

    def run_once(self):
        """Run enhanced synchronization once and exit"""
        async def run_once_async():
            print("🔄 Running enhanced documentation synchronization once...")
            await self._perform_full_sync(force=True)
            await self._check_notifications()
            await self._perform_health_check()
        
        try:
            asyncio.run(run_once_async())
            return 0
        except Exception as e:
            print(f"❌ One-time enhanced sync failed: {e}")
            return 1

    def status(self):
        """Show service status"""
        health_file = self.claude_pm_root / "logs" / "enhanced_doc_sync_health.json"
        
        if health_file.exists():
            try:
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
                
                print("📊 Enhanced Documentation Sync Service Status")
                print("=" * 50)
                print(f"Status: {health_data.get('service_status', 'unknown').upper()}")
                print(f"Last Check: {health_data.get('timestamp', 'unknown')}")
                
                doc_health = health_data.get('documentation_health', {})
                print(f"\nDocumentation Health:")
                print(f"  Validation Passed: {'✅' if doc_health.get('validation_passed') else '❌'}")
                print(f"  Total Issues: {doc_health.get('total_issues', 0)}")
                print(f"  Broken Links: {doc_health.get('broken_links', 0)}")
                print(f"  Completion: {doc_health.get('completion_percentage', 0):.1f}%")
                
                perf = health_data.get('service_performance', {})
                print(f"\nService Performance:")
                print(f"  Uptime: {health_data.get('uptime_hours', 0):.1f} hours")
                print(f"  Sync Operations: {perf.get('sync_count', 0)}")
                print(f"  Validation Checks: {perf.get('validation_count', 0)}")
                print(f"  Notifications: {perf.get('notification_count', 0)}")
                print(f"  Errors: {perf.get('error_count', 0)}")
                
                return 0
                
            except Exception as e:
                print(f"❌ Error reading status: {e}")
                return 1
        else:
            print("❌ No health status file found. Service may not be running.")
            return 1


def create_enhanced_systemd_service():
    """Create enhanced systemd service file"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    service_file_content = f"""[Unit]
Description=Enhanced Claude PM Automated Documentation Synchronization Service
After=network.target

[Service]
Type=simple
User=masa
WorkingDirectory={claude_pm_root}
ExecStart=/usr/bin/python3 {claude_pm_root}/scripts/enhanced_automated_doc_sync.py --daemon
Restart=always
RestartSec=30
StandardOutput=append:{claude_pm_root}/logs/enhanced_automated_doc_sync.log
StandardError=append:{claude_pm_root}/logs/enhanced_automated_doc_sync_error.log

# Resource limits
MemoryLimit=512M
CPUQuota=50%

# Graceful shutdown
TimeoutStopSec=30
KillMode=mixed

[Install]
WantedBy=multi-user.target
"""
    
    service_file_path = claude_pm_root / "enhanced-claude-pm-doc-sync.service"
    with open(service_file_path, 'w') as f:
        f.write(service_file_content)
    
    print(f"✅ Enhanced systemd service file created: {service_file_path}")
    print(f"To install: sudo cp {service_file_path} /etc/systemd/system/")
    print("To enable: sudo systemctl enable enhanced-claude-pm-doc-sync.service")
    print("To start: sudo systemctl start enhanced-claude-pm-doc-sync.service")
    print("To check status: sudo systemctl status enhanced-claude-pm-doc-sync.service")
    return service_file_path


def create_enhanced_cron_job():
    """Create enhanced cron job for periodic documentation sync"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    cron_entry = f"# Enhanced Claude PM Documentation Synchronization\n"
    cron_entry += f"# Run every 5 minutes with enhanced validation\n"
    cron_entry += f"*/5 * * * * python3 {claude_pm_root}/scripts/enhanced_automated_doc_sync.py --once >> {claude_pm_root}/logs/cron_enhanced_doc_sync.log 2>&1\n"
    
    cron_file = claude_pm_root / "enhanced-claude-pm-doc-sync.cron"
    with open(cron_file, 'w') as f:
        f.write(cron_entry)
    
    print(f"✅ Enhanced cron job file created: {cron_file}")
    print(f"To install: crontab {cron_file}")
    print("To view current crontab: crontab -l")
    return cron_file


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Automated Documentation Synchronization Service for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root", 
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--daemon", 
        action="store_true",
        help="Run as continuous daemon service"
    )
    parser.add_argument(
        "--once", 
        action="store_true",
        help="Run enhanced synchronization once and exit"
    )
    parser.add_argument(
        "--status", 
        action="store_true",
        help="Show service status"
    )
    parser.add_argument(
        "--create-systemd-service", 
        action="store_true",
        help="Create enhanced systemd service file"
    )
    parser.add_argument(
        "--create-cron-job", 
        action="store_true",
        help="Create enhanced cron job file"
    )
    parser.add_argument(
        "--sync-interval", 
        type=int, 
        default=300,
        help="Full synchronization interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--validation-interval", 
        type=int, 
        default=180,
        help="Quick validation interval in seconds (default: 180)"
    )
    
    args = parser.parse_args()
    
    if args.create_systemd_service:
        create_enhanced_systemd_service()
        return 0
    
    if args.create_cron_job:
        create_enhanced_cron_job()
        return 0
    
    # Create enhanced service instance
    service = EnhancedAutomatedDocSyncService(args.claude_pm_root)
    service.sync_interval = args.sync_interval
    service.validation_interval = args.validation_interval
    
    if args.status:
        return service.status()
    elif args.once:
        return service.run_once()
    elif args.daemon:
        return service.run()
    else:
        # Default: run once
        return service.run_once()


if __name__ == "__main__":
    exit(main())