#!/usr/bin/env python3
"""
Claude PM GitHub Sync CLI Interface

This script provides a comprehensive command-line interface for syncing
Claude PM trackdown tickets to GitHub Issues with full management capabilities.

Commands:
    sync     - Sync tickets to GitHub Issues  
    status   - Show sync status and statistics
    validate - Validate sync integrity
    setup    - Setup GitHub repository (labels, milestones, projects)
    report   - Generate sync reports
    rollback - Rollback sync operation
    cleanup  - Clean up old logs and backups

Usage:
    python github_sync_cli.py sync --repository owner/repo
    python github_sync_cli.py status
    python github_sync_cli.py setup --repository owner/repo
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import our sync modules
from github_sync import (
    GitHubAPIClient, ClaudePMGitHubSync, SyncDirection, TokenManager
)
from github_utils import (
    GitHubProjectManager, EpicManager, GitHubSearchManager, 
    SyncValidator, setup_epic_projects, validate_github_permissions,
    CLAUDE_PM_EPICS
)
from sync_logger import (
    SyncLogger, SyncMonitor, setup_sync_logging,
    SyncEventType, SyncErrorSeverity
)


class GitHubSyncCLI:
    """Main CLI interface for GitHub sync operations"""
    
    def __init__(self):
        self.sync_logger = None
        self.monitor = None
        self.client = None
        self.repository = None
    
    def setup_logging(self, verbose: bool = False):
        """Initialize logging system"""
        self.sync_logger, self.monitor = setup_sync_logging(verbose=verbose)
    
    def load_github_client(self, token_file: str = None) -> bool:
        """Load GitHub client with authentication"""
        try:
            if token_file:
                token = TokenManager.load_token_from_file(token_file)
            else:
                token = TokenManager.load_token_from_env()
            
            if not token:
                print("❌ GitHub token not found. Please provide via .env file or --token-file")
                return False
            
            self.client = GitHubAPIClient(token)
            return True
            
        except Exception as e:
            print(f"❌ Error loading GitHub client: {e}")
            return False
    
    def validate_repository(self, repository: str) -> bool:
        """Validate repository format and access"""
        if '/' not in repository:
            print("❌ Repository must be in format 'owner/repo'")
            return False
        
        self.repository = repository
        
        # Test repository access
        try:
            response = self.client.make_request("GET", f"/repos/{repository}")
            if response.status_code != 200:
                print(f"❌ Cannot access repository {repository}: {response.status_code}")
                return False
            
            print(f"✅ Repository access confirmed: {repository}")
            return True
            
        except Exception as e:
            print(f"❌ Error accessing repository {repository}: {e}")
            return False
    
    def cmd_sync(self, args) -> int:
        """Execute sync command"""
        print("🔄 Starting Claude PM to GitHub sync...")
        
        # Setup
        if not self.load_github_client(args.token_file):
            return 1
        
        if not self.validate_repository(args.repository):
            return 1
        
        # Check backlog file
        if not Path(args.backlog_path).exists():
            print(f"❌ Backlog file not found: {args.backlog_path}")
            return 1
        
        try:
            # Initialize sync
            sync = ClaudePMGitHubSync(self.client, self.repository, args.backlog_path)
            
            # Map direction
            direction_map = {
                "to-github": SyncDirection.CLAUDE_PM_TO_GITHUB,
                "from-github": SyncDirection.GITHUB_TO_CLAUDE_PM,
                "bidirectional": SyncDirection.BIDIRECTIONAL
            }
            
            # Log sync start
            self.sync_logger.log_sync_start(self.repository, args.direction, args.dry_run)
            
            if args.dry_run:
                print("🔍 DRY RUN MODE - No changes will be made")
            
            # Perform sync
            result = sync.full_sync(direction_map[args.direction], args.dry_run)
            
            # Log completion
            self.sync_logger.log_sync_complete(self.repository, result)
            
            # Print results
            if result['success']:
                print("✅ Sync completed successfully!")
                
                claude_results = result['claude_pm_to_github']
                github_results = result['github_to_claude_pm']
                
                print(f"\n📊 Results:")
                print(f"   Claude PM → GitHub: {claude_results.get('synced', 0)} synced")
                print(f"   - Created: {claude_results.get('created', 0)}")
                print(f"   - Updated: {claude_results.get('updated', 0)}")
                print(f"   - Skipped: {claude_results.get('skipped', 0)}")
                print(f"   - Errors: {claude_results.get('errors', 0)}")
                
                if github_results.get('synced', 0) > 0:
                    print(f"   GitHub → Claude PM: {github_results.get('synced', 0)} synced")
                
                if result.get('backup_file'):
                    print(f"   Backup: {result['backup_file']}")
                
                if args.dry_run:
                    print("\n💡 Run without --dry-run to apply changes")
            else:
                print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
                return 1
            
            return 0
            
        except Exception as e:
            self.sync_logger.log_error(e)
            print(f"❌ Sync failed: {e}")
            return 1
    
    def cmd_status(self, args) -> int:
        """Show sync status and statistics"""
        print("📈 Claude PM GitHub Sync Status\n")
        
        # Load sync records
        sync_log_path = "/Users/masa/Projects/Claude-PM/sync/github_sync_log.json"
        
        if not Path(sync_log_path).exists():
            print("📭 No sync records found. Run a sync first.")
            return 0
        
        try:
            with open(sync_log_path, 'r') as f:
                sync_data = json.load(f)
            
            print(f"Repository: {sync_data.get('repository', 'N/A')}")
            print(f"Last Sync: {sync_data.get('last_sync', 'N/A')}")
            print(f"Total Records: {len(sync_data.get('sync_records', {}))}")
            
            # If we have a repository and client, get more stats
            if args.repository and self.load_github_client(args.token_file):
                search_manager = GitHubSearchManager(self.client, args.repository)
                stats = search_manager.get_sync_statistics()
                
                print(f"\n📊 GitHub Statistics:")
                print(f"   Total Issues: {stats['total_issues']}")
                print(f"   Open Issues: {stats['open_issues']}")
                print(f"   Closed Issues: {stats['closed_issues']}")
                print(f"   Orphaned Issues: {stats['orphaned_issues']}")
                
                if stats['priority_breakdown']:
                    print(f"\n   Priority Breakdown:")
                    for priority, count in stats['priority_breakdown'].items():
                        print(f"     {priority}: {count}")
                
                if stats['milestone_breakdown']:
                    print(f"\n   Milestone Breakdown:")
                    for milestone, count in stats['milestone_breakdown'].items():
                        print(f"     {milestone}: {count}")
            
            # Show recent errors if any
            if self.sync_logger:
                error_stats = self.sync_logger.get_error_statistics(hours=24)
                if error_stats['errors'] > 0:
                    print(f"\n⚠️  Recent Issues (24h):")
                    print(f"   Errors: {error_stats['errors']}")
                    print(f"   Warnings: {error_stats['warnings']}")
                    print(f"   Error Rate: {error_stats['error_rate']:.1f}%")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error reading status: {e}")
            return 1
    
    def cmd_validate(self, args) -> int:
        """Validate sync integrity"""
        print("🔍 Validating sync integrity...")
        
        if not self.load_github_client(args.token_file):
            return 1
        
        if not self.validate_repository(args.repository):
            return 1
        
        try:
            # Load sync records
            sync_log_path = "/Users/masa/Projects/Claude-PM/sync/github_sync_log.json"
            
            if not Path(sync_log_path).exists():
                print("📭 No sync records found. Run a sync first.")
                return 0
            
            with open(sync_log_path, 'r') as f:
                sync_data = json.load(f)
                sync_records = sync_data.get('sync_records', {})
            
            # Validate
            validator = SyncValidator(self.client, self.repository)
            results = validator.validate_sync_integrity(sync_records)
            
            print(f"✅ Validation Results:")
            print(f"   Valid Records: {results['valid_records']}")
            print(f"   Invalid Records: {results['invalid_records']}")
            print(f"   Missing Issues: {len(results['missing_issues'])}")
            print(f"   Mismatched Issues: {len(results['mismatched_issues'])}")
            print(f"   Orphaned Issues: {len(results['orphaned_issues'])}")
            
            # Show details for issues
            if results['missing_issues']:
                print(f"\n❌ Missing Issues:")
                for issue in results['missing_issues']:
                    print(f"   - {issue['ticket_id']} (issue #{issue['issue_number']})")
            
            if results['mismatched_issues']:
                print(f"\n⚠️  Mismatched Issues:")
                for issue in results['mismatched_issues']:
                    print(f"   - {issue['ticket_id']}: expected '{issue['expected_title_contains']}' in title")
            
            if results['orphaned_issues']:
                print(f"\n🔍 Orphaned Issues (no sync record):")
                for issue in results['orphaned_issues'][:5]:  # Show first 5
                    print(f"   - #{issue['issue_number']}: {issue['title']}")
                
                if len(results['orphaned_issues']) > 5:
                    print(f"   ... and {len(results['orphaned_issues']) - 5} more")
            
            return 0
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return 1
    
    def cmd_setup(self, args) -> int:
        """Setup GitHub repository with labels, milestones, and projects"""
        print("🛠️  Setting up GitHub repository...")
        
        if not self.load_github_client(args.token_file):
            return 1
        
        if not self.validate_repository(args.repository):
            return 1
        
        try:
            owner = self.repository.split('/')[0]
            
            # Test permissions first
            print("🔐 Validating permissions...")
            permissions = validate_github_permissions(self.client, self.repository)
            
            missing_permissions = [perm for perm, has_access in permissions.items() if not has_access]
            if missing_permissions:
                print(f"❌ Missing permissions: {', '.join(missing_permissions)}")
                return 1
            
            print("✅ All required permissions confirmed")
            
            # Create sync object to access managers
            sync = ClaudePMGitHubSync(self.client, self.repository)
            
            # Setup labels
            print("🏷️  Setting up labels...")
            sync.label_manager.ensure_claude_pm_labels()
            print("✅ Labels setup complete")
            
            # Setup milestones
            print("🎯 Setting up milestones...")
            sync.milestone_manager.ensure_claude_pm_milestones()
            print("✅ Milestones setup complete")
            
            # Setup epic projects if requested
            if args.setup_epics:
                print("📋 Setting up epic projects...")
                results = setup_epic_projects(self.client, owner, self.repository)
                
                created = sum(1 for r in results.values() if r.get('status') == 'created')
                existing = sum(1 for r in results.values() if r.get('status') == 'exists')
                failed = sum(1 for r in results.values() if r.get('status') == 'failed')
                
                print(f"✅ Epic projects setup: {created} created, {existing} existing, {failed} failed")
                
                if failed > 0:
                    print("⚠️  Some epic projects failed to create")
            
            print("✅ Repository setup complete!")
            return 0
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return 1
    
    def cmd_report(self, args) -> int:
        """Generate sync reports"""
        print("📄 Generating sync report...")
        
        try:
            if self.sync_logger is None:
                # Load events from file if logger not initialized
                events_file = "/Users/masa/Projects/Claude-PM/logs/sync_events.jsonl"
                if not Path(events_file).exists():
                    print("📭 No sync events found. Run a sync first.")
                    return 0
            
            report_content = self.sync_logger.generate_sync_report(args.output)
            
            if args.output:
                print(f"✅ Report saved to: {args.output}")
            else:
                print("📄 Sync Report:")
                print("=" * 50)
                print(report_content)
            
            return 0
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return 1
    
    def cmd_cleanup(self, args) -> int:
        """Clean up old logs and backups"""
        print("🧹 Cleaning up old files...")
        
        try:
            log_dir = Path("/Users/masa/Projects/Claude-PM/logs")
            backup_dir = Path("/Users/masa/Projects/Claude-PM/backups")
            
            cleaned_files = 0
            
            # Clean old log files (keep last 5)
            if log_dir.exists():
                for log_file in ["github_sync.log", "sync_errors.log", "api_requests.log"]:
                    log_files = sorted(log_dir.glob(f"{log_file}.*"), key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    for old_file in log_files[5:]:  # Keep 5 most recent
                        old_file.unlink()
                        cleaned_files += 1
                        print(f"   Removed: {old_file.name}")
            
            # Clean old backups (keep last 10)
            if backup_dir.exists():
                backup_files = sorted(backup_dir.glob("github_sync_backup_*.json"), 
                                    key=lambda x: x.stat().st_mtime, reverse=True)
                
                for old_backup in backup_files[10:]:  # Keep 10 most recent
                    old_backup.unlink()
                    cleaned_files += 1
                    print(f"   Removed: {old_backup.name}")
            
            print(f"✅ Cleanup complete: {cleaned_files} files removed")
            return 0
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return 1


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Claude PM GitHub Sync CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Sync tickets to GitHub
    python github_sync_cli.py sync --repository owner/repo
    
    # Dry run to see what would change
    python github_sync_cli.py sync --repository owner/repo --dry-run
    
    # Setup repository with labels and milestones
    python github_sync_cli.py setup --repository owner/repo
    
    # Check sync status
    python github_sync_cli.py status --repository owner/repo
    
    # Validate sync integrity
    python github_sync_cli.py validate --repository owner/repo
    
    # Generate report
    python github_sync_cli.py report --output sync_report.md
        """
    )
    
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--token-file", help="File containing GitHub token")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync tickets to GitHub Issues")
    sync_parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    sync_parser.add_argument("--direction", choices=["to-github", "from-github", "bidirectional"], 
                           default="to-github", help="Sync direction")
    sync_parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    sync_parser.add_argument("--backlog-path", default="/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md",
                           help="Path to BACKLOG.md file")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show sync status")
    status_parser.add_argument("--repository", help="GitHub repository (owner/repo)")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate sync integrity")
    validate_parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup GitHub repository")
    setup_parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    setup_parser.add_argument("--setup-epics", action="store_true", help="Create epic projects")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate sync report")
    report_parser.add_argument("--output", help="Output file (default: print to console)")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old logs and backups")
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI
    cli = GitHubSyncCLI()
    cli.setup_logging(args.verbose)
    
    # Route to appropriate command
    command_map = {
        "sync": cli.cmd_sync,
        "status": cli.cmd_status,
        "validate": cli.cmd_validate,
        "setup": cli.cmd_setup,
        "report": cli.cmd_report,
        "cleanup": cli.cmd_cleanup
    }
    
    try:
        return command_map[args.command](args)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())