#!/usr/bin/env python3
"""
Automated Documentation Synchronization Service
Part of M01-041: Implement Documentation Status Synchronization System

This service runs continuously to monitor and synchronize documentation,
integrating with the Claude PM health monitoring system.
"""

import asyncio
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from sync_docs import DocumentationSyncManager
from doc_notification_system import DocumentationNotificationSystem

class AutomatedDocSyncService:
    """Automated service for continuous documentation synchronization"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.sync_manager = DocumentationSyncManager(str(claude_pm_root))
        self.notification_system = DocumentationNotificationSystem(str(claude_pm_root))
        
        # Service configuration
        self.sync_interval = 300  # 5 minutes
        self.notification_check_interval = 600  # 10 minutes
        self.force_sync_interval = 3600  # 1 hour
        
        # Service state
        self.running = False
        self.last_sync = None
        self.last_notification_check = None
        self.last_force_sync = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def _sync_documentation(self, force: bool = False) -> bool:
        """Perform documentation synchronization"""
        try:
            if force:
                print("🔄 Performing forced documentation synchronization...")
            else:
                print("🔄 Performing documentation synchronization...")
            
            success = self.sync_manager.sync_documentation(validate_only=False)
            
            if success:
                print("✅ Documentation synchronization completed successfully")
                self.last_sync = datetime.now()
                return True
            else:
                print("❌ Documentation synchronization failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during documentation synchronization: {e}")
            return False

    async def _check_notifications(self) -> bool:
        """Check for notification-worthy changes"""
        try:
            print("📧 Checking for notification-worthy changes...")
            success = self.notification_system.check_and_notify()
            
            if success:
                self.last_notification_check = datetime.now()
                return True
            else:
                print("❌ Notification check failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during notification check: {e}")
            return False

    async def _service_loop(self):
        """Main service loop"""
        print("🚀 Starting automated documentation synchronization service...")
        print(f"📁 Claude PM Root: {self.claude_pm_root}")
        print(f"⏱️ Sync Interval: {self.sync_interval}s")
        print(f"📧 Notification Check Interval: {self.notification_check_interval}s")
        print(f"🔄 Force Sync Interval: {self.force_sync_interval}s")
        
        self.running = True
        
        # Perform initial sync
        await self._sync_documentation(force=True)
        await self._check_notifications()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for regular sync
                if (self.last_sync is None or 
                    current_time - self.last_sync >= timedelta(seconds=self.sync_interval)):
                    await self._sync_documentation()
                
                # Check if it's time for notification check
                if (self.last_notification_check is None or 
                    current_time - self.last_notification_check >= timedelta(seconds=self.notification_check_interval)):
                    await self._check_notifications()
                
                # Check if it's time for forced sync
                if (self.last_force_sync is None or 
                    current_time - self.last_force_sync >= timedelta(seconds=self.force_sync_interval)):
                    await self._sync_documentation(force=True)
                    self.last_force_sync = current_time
                
                # Sleep for a short period before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in service loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
        
        print("🛑 Automated documentation synchronization service stopped")

    def run(self):
        """Run the automated service"""
        try:
            asyncio.run(self._service_loop())
        except KeyboardInterrupt:
            print("\n🛑 Service interrupted by user")
        except Exception as e:
            print(f"❌ Service failed: {e}")
            return 1
        return 0

    def run_once(self):
        """Run synchronization once and exit"""
        async def run_once_async():
            await self._sync_documentation(force=True)
            await self._check_notifications()
        
        try:
            asyncio.run(run_once_async())
            return 0
        except Exception as e:
            print(f"❌ One-time sync failed: {e}")
            return 1


def create_systemd_service():
    """Create systemd service file for automated documentation sync"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    service_file_content = f"""[Unit]
Description=Claude PM Automated Documentation Synchronization Service
After=network.target

[Service]
Type=simple
User=masa
WorkingDirectory={claude_pm_root}
ExecStart=/usr/bin/python3 {claude_pm_root}/scripts/automated_doc_sync.py --daemon
Restart=always
RestartSec=10
StandardOutput=append:{claude_pm_root}/logs/automated_doc_sync.log
StandardError=append:{claude_pm_root}/logs/automated_doc_sync_error.log

[Install]
WantedBy=multi-user.target
"""
    
    service_file_path = claude_pm_root / "claude-pm-doc-sync.service"
    with open(service_file_path, 'w') as f:
        f.write(service_file_content)
    
    print(f"✅ Systemd service file created: {service_file_path}")
    print(f"To install: sudo cp {service_file_path} /etc/systemd/system/")
    print("To enable: sudo systemctl enable claude-pm-doc-sync.service")
    print("To start: sudo systemctl start claude-pm-doc-sync.service")
    return service_file_path


def create_cron_job():
    """Create cron job for periodic documentation sync"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    cron_entry = f"# Claude PM Documentation Synchronization\n"
    cron_entry += f"# Run every 10 minutes\n"
    cron_entry += f"*/10 * * * * python3 {claude_pm_root}/scripts/automated_doc_sync.py --once >> {claude_pm_root}/logs/cron_doc_sync.log 2>&1\n"
    
    cron_file = claude_pm_root / "claude-pm-doc-sync.cron"
    with open(cron_file, 'w') as f:
        f.write(cron_entry)
    
    print(f"✅ Cron job file created: {cron_file}")
    print(f"To install: crontab {cron_file}")
    print("To view current crontab: crontab -l")
    return cron_file


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated Documentation Synchronization Service for Claude PM Framework"
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
        help="Run synchronization once and exit"
    )
    parser.add_argument(
        "--create-systemd-service", 
        action="store_true",
        help="Create systemd service file"
    )
    parser.add_argument(
        "--create-cron-job", 
        action="store_true",
        help="Create cron job file"
    )
    parser.add_argument(
        "--sync-interval", 
        type=int, 
        default=300,
        help="Synchronization interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--notification-interval", 
        type=int, 
        default=600,
        help="Notification check interval in seconds (default: 600)"
    )
    
    args = parser.parse_args()
    
    if args.create_systemd_service:
        create_systemd_service()
        return 0
    
    if args.create_cron_job:
        create_cron_job()
        return 0
    
    # Create service instance
    service = AutomatedDocSyncService(args.claude_pm_root)
    service.sync_interval = args.sync_interval
    service.notification_check_interval = args.notification_interval
    
    if args.once:
        return service.run_once()
    elif args.daemon:
        return service.run()
    else:
        # Default: run once
        return service.run_once()


if __name__ == "__main__":
    exit(main())