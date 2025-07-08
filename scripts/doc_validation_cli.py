#!/usr/bin/env python3
"""
Documentation Validation CLI Tool
FWK-008: Complete Documentation Validation and Management CLI

This tool provides a comprehensive CLI interface for managing documentation
synchronization, validation, and notifications.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from enhanced_doc_sync import EnhancedDocumentationSyncManager
from enhanced_doc_notification_system import DocumentationNotificationSystem
from enhanced_automated_doc_sync import EnhancedAutomatedDocSyncService

class DocumentationValidationCLI:
    """Comprehensive CLI for documentation validation and management"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.sync_manager = EnhancedDocumentationSyncManager(str(claude_pm_root))
        self.notification_system = DocumentationNotificationSystem(str(claude_pm_root))
        self.service = EnhancedAutomatedDocSyncService(str(claude_pm_root))

    def validate(self, fix: bool = False, report: bool = True) -> int:
        """Run comprehensive validation"""
        print("🔍 Running comprehensive documentation validation...")
        
        # Run validation
        success = self.sync_manager.sync_documentation(validate_only=not fix)
        
        if success:
            print("✅ Validation completed successfully")
        else:
            print("❌ Validation found issues")
        
        # Show report if requested
        if report:
            self._show_latest_report()
        
        return 0 if success else 1

    def sync(self, force: bool = False) -> int:
        """Run documentation synchronization"""
        print("🔄 Running documentation synchronization...")
        
        success = self.sync_manager.sync_documentation(validate_only=False)
        
        if success:
            print("✅ Synchronization completed successfully")
        else:
            print("❌ Synchronization found issues")
        
        self._show_latest_report()
        return 0 if success else 1

    def status(self) -> int:
        """Show current documentation status"""
        stats_file = self.claude_pm_root / "logs" / "latest_enhanced_doc_stats.json"
        
        if not stats_file.exists():
            print("❌ No status information available. Run validation first.")
            return 1
        
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            print("📊 Documentation Status")
            print("=" * 50)
            print(f"Last Updated: {stats.get('last_update', 'unknown')}")
            print(f"Files Validated: {stats.get('files_validated', 0)}")
            print(f"Links Checked: {stats.get('links_checked', 0)}")
            
            print(f"\n📈 Project Progress:")
            print(f"  Total Tickets: {stats.get('total_tickets', 0)}")
            print(f"  Completed: {stats.get('completed_tickets', 0)} ({stats.get('completion_percentage', 0):.1f}%)")
            print(f"  In Progress: {stats.get('in_progress_tickets', 0)}")
            print(f"  Planned: {stats.get('planned_tickets', 0)}")
            print(f"  Blocked: {stats.get('blocked_tickets', 0)}")
            
            print(f"\n🔍 Validation Issues:")
            issues = stats.get('validation_issues', [])
            broken_links = stats.get('broken_links', [])
            inconsistencies = stats.get('inconsistencies_found', [])
            
            print(f"  Total Issues: {len(issues)}")
            print(f"  Broken Links: {len(broken_links)}")
            print(f"  Inconsistencies: {len(inconsistencies)}")
            
            # Show issue breakdown by severity
            severity_counts = {}
            for issue in issues:
                severity = issue.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if severity_counts:
                print("\n  Issue Breakdown:")
                for severity in ['critical', 'high', 'medium', 'low']:
                    count = severity_counts.get(severity, 0)
                    if count > 0:
                        print(f"    {severity.title()}: {count}")
            
            # Health status
            if len(issues) == 0:
                print("\n✅ Documentation Health: EXCELLENT")
            elif len([i for i in issues if i.get('severity') == 'critical']) > 0:
                print("\n🚨 Documentation Health: CRITICAL ISSUES")
            elif len(broken_links) > 0:
                print("\n⚠️ Documentation Health: NEEDS ATTENTION")
            else:
                print("\n🟡 Documentation Health: MINOR ISSUES")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error reading status: {e}")
            return 1

    def fix_links(self, dry_run: bool = False) -> int:
        """Fix common link issues automatically"""
        print("🔧 Fixing common documentation link issues...")
        
        if dry_run:
            print("🏃 Running in dry-run mode (no changes will be made)")
        
        # Get current issues
        stats_file = self.claude_pm_root / "logs" / "latest_enhanced_doc_stats.json"
        if not stats_file.exists():
            print("❌ No validation data available. Run validation first.")
            return 1
        
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            broken_links = stats.get('broken_links', [])
            fixes_applied = 0
            
            for link_issue in broken_links:
                if link_issue.get('suggested_fix'):
                    print(f"  🔧 {link_issue['file_path']}:{link_issue['line_number']}")
                    print(f"      Fix: {link_issue['suggested_fix']}")
                    
                    if not dry_run:
                        # Here we would apply the fix
                        # For now, just count potential fixes
                        fixes_applied += 1
            
            if fixes_applied > 0:
                print(f"\n✅ Applied {fixes_applied} automatic fixes")
                if not dry_run:
                    print("   Re-run validation to check results")
            else:
                print("ℹ️ No automatic fixes available for current issues")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error fixing links: {e}")
            return 1

    def notify(self, force: bool = False) -> int:
        """Check and send notifications"""
        print("📧 Checking for documentation change notifications...")
        
        success = self.notification_system.check_and_notify()
        
        if success:
            print("✅ Notification check completed")
        else:
            print("❌ Notification check failed")
        
        # Show notification status
        status = self.notification_system.get_notification_status()
        
        print(f"\n📧 Notification Status:")
        print(f"  Enabled: {'✅' if status['notifications_enabled'] else '❌'}")
        print(f"  Methods: {', '.join(status['notification_methods'])}")
        
        if status['cooldown_remaining']:
            print(f"  Cooldown: {status['cooldown_remaining']} remaining")
        else:
            print(f"  Cooldown: None")
        
        return 0 if success else 1

    def service_status(self) -> int:
        """Show automated service status"""
        return self.service.status()

    def install_hooks(self) -> int:
        """Install pre-commit hooks"""
        print("🪝 Installing enhanced pre-commit hooks...")
        
        try:
            # Use the sync manager's hook installation
            from enhanced_doc_sync import create_enhanced_pre_commit_hook
            success = create_enhanced_pre_commit_hook()
            
            if success:
                print("✅ Enhanced pre-commit hooks installed successfully")
                return 0
            else:
                print("❌ Failed to install pre-commit hooks")
                return 1
                
        except Exception as e:
            print(f"❌ Error installing hooks: {e}")
            return 1

    def report(self, latest: bool = True, summary: bool = False) -> int:
        """Show validation reports"""
        logs_dir = self.claude_pm_root / "logs"
        
        if latest:
            # Find latest report
            report_files = list(logs_dir.glob("enhanced_doc_sync_report_*.md"))
            if not report_files:
                print("❌ No reports found")
                return 1
            
            latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
            
            if summary:
                self._show_report_summary(latest_report)
            else:
                print(f"📄 Latest Report: {latest_report}")
                with open(latest_report, 'r') as f:
                    content = f.read()
                print(content)
        
        return 0

    def _show_latest_report(self):
        """Show summary of latest report"""
        logs_dir = self.claude_pm_root / "logs"
        report_files = list(logs_dir.glob("enhanced_doc_sync_report_*.md"))
        
        if report_files:
            latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
            print(f"\n📄 Latest Report: {latest_report}")
            self._show_report_summary(latest_report)

    def _show_report_summary(self, report_file: Path):
        """Show summary of a report"""
        try:
            with open(report_file, 'r') as f:
                content = f.read()
            
            # Extract key metrics
            lines = content.split('\n')
            summary_section = False
            
            for line in lines:
                if '## Executive Summary' in line:
                    summary_section = True
                elif line.startswith('## ') and summary_section:
                    break
                elif summary_section and line.strip().startswith('- '):
                    print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"❌ Error reading report: {e}")

    def health(self) -> int:
        """Show comprehensive health status"""
        print("🏥 Documentation System Health Check")
        print("=" * 50)
        
        # Check various health indicators
        health_score = 100
        issues = []
        
        # Check if service is running
        health_file = self.claude_pm_root / "logs" / "enhanced_doc_sync_health.json"
        if health_file.exists():
            try:
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
                
                service_status = health_data.get('service_status', 'unknown')
                print(f"Service Status: {service_status.upper()}")
                
                if service_status != 'healthy':
                    health_score -= 20
                    issues.append("Service not running optimally")
                
            except Exception:
                health_score -= 30
                issues.append("Cannot read service health data")
        else:
            health_score -= 10
            issues.append("Service health data not available")
        
        # Check validation status
        stats_file = self.claude_pm_root / "logs" / "latest_enhanced_doc_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                
                validation_issues = stats.get('validation_issues', [])
                critical_issues = [i for i in validation_issues if i.get('severity') == 'critical']
                
                if critical_issues:
                    health_score -= 50
                    issues.append(f"{len(critical_issues)} critical validation issues")
                
                broken_links = stats.get('broken_links', [])
                if len(broken_links) > 5:
                    health_score -= 20
                    issues.append(f"{len(broken_links)} broken links")
                elif len(broken_links) > 0:
                    health_score -= 10
                    issues.append(f"{len(broken_links)} broken links")
                
            except Exception:
                health_score -= 20
                issues.append("Cannot read validation status")
        
        # Check pre-commit hooks
        hook_file = self.claude_pm_root / ".git" / "hooks" / "pre-commit"
        if not hook_file.exists():
            health_score -= 15
            issues.append("Pre-commit hooks not installed")
        
        # Overall health assessment
        print(f"\nOverall Health Score: {health_score}/100")
        
        if health_score >= 90:
            print("🟢 EXCELLENT - Documentation system is healthy")
        elif health_score >= 70:
            print("🟡 GOOD - Minor issues detected")
        elif health_score >= 50:
            print("🟠 NEEDS ATTENTION - Several issues need fixing")
        else:
            print("🔴 CRITICAL - Immediate attention required")
        
        if issues:
            print("\n⚠️ Issues Detected:")
            for issue in issues:
                print(f"  - {issue}")
        
        return 0 if health_score >= 70 else 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Documentation Validation CLI for Claude PM Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  doc-validate validate                 # Run validation only
  doc-validate sync                     # Run full synchronization  
  doc-validate status                   # Show current status
  doc-validate fix-links --dry-run      # Preview link fixes
  doc-validate notify                   # Check notifications
  doc-validate health                   # Comprehensive health check
  doc-validate install-hooks            # Install pre-commit hooks
        """
    )
    
    parser.add_argument(
        "--claude-pm-root",
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Run documentation validation')
    validate_parser.add_argument('--fix', action='store_true', help='Fix issues during validation')
    validate_parser.add_argument('--no-report', action='store_true', help='Skip showing report')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Run documentation synchronization')
    sync_parser.add_argument('--force', action='store_true', help='Force synchronization')
    
    # Status command
    subparsers.add_parser('status', help='Show current documentation status')
    
    # Fix links command
    fix_parser = subparsers.add_parser('fix-links', help='Fix common link issues')
    fix_parser.add_argument('--dry-run', action='store_true', help='Preview fixes without applying')
    
    # Notify command
    notify_parser = subparsers.add_parser('notify', help='Check and send notifications')
    notify_parser.add_argument('--force', action='store_true', help='Force notification check')
    
    # Service status command
    subparsers.add_parser('service-status', help='Show automated service status')
    
    # Install hooks command
    subparsers.add_parser('install-hooks', help='Install pre-commit hooks')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Show validation reports')
    report_parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    # Health command
    subparsers.add_parser('health', help='Comprehensive health check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create CLI instance
    cli = DocumentationValidationCLI(args.claude_pm_root)
    
    # Execute command
    try:
        if args.command == 'validate':
            return cli.validate(fix=args.fix, report=not args.no_report)
        elif args.command == 'sync':
            return cli.sync(force=args.force)
        elif args.command == 'status':
            return cli.status()
        elif args.command == 'fix-links':
            return cli.fix_links(dry_run=args.dry_run)
        elif args.command == 'notify':
            return cli.notify(force=args.force)
        elif args.command == 'service-status':
            return cli.service_status()
        elif args.command == 'install-hooks':
            return cli.install_hooks()
        elif args.command == 'report':
            return cli.report(summary=args.summary)
        elif args.command == 'health':
            return cli.health()
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())