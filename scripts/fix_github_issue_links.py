#!/usr/bin/env python3
"""
GitHub Issue Link Fixer for Claude PM Sync System

This script fixes all GitHub issue descriptions to use proper Git repository URLs
instead of local desktop paths for trackdown file references.

Problem: All 114 GitHub Issues in bobmatnyc/claude-pm contain links pointing to 
local desktop paths like `/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md`

Solution: Replace with proper Git repository URLs like 
`https://github.com/bobmatnyc/claude-pm/blob/main/trackdown/BACKLOG.md`

Features:
- Bulk update all GitHub issues
- Backup original descriptions before modification
- Rate limiting to respect GitHub API limits
- Dry-run mode for testing
- Comprehensive error handling and logging
- Progress tracking with status updates

Usage:
    python fix_github_issue_links.py --repository owner/repo [options]
    python fix_github_issue_links.py --help
"""

import argparse
import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests


@dataclass
class IssueBackup:
    """Backup record for original issue content"""
    issue_number: int
    issue_id: str
    original_title: str
    original_body: str
    backup_timestamp: str


@dataclass
class LinkFixResult:
    """Result of link fixing operation"""
    issue_number: int
    ticket_id: str
    success: bool
    changes_made: bool
    error_message: Optional[str] = None
    original_body: Optional[str] = None
    updated_body: Optional[str] = None


class GitHubAPIClient:
    """GitHub API client with authentication and rate limiting"""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })
        self.logger = logging.getLogger(f"{__name__}.GitHubAPIClient")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request with rate limit monitoring"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        self._check_rate_limit(response)
        return response
    
    def _check_rate_limit(self, response: requests.Response):
        """Monitor rate limit headers and warn when approaching limits"""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining < 100:  # Warning threshold
            self.logger.warning(f"Rate limit warning: {remaining} requests remaining")
            reset_datetime = datetime.fromtimestamp(reset_time)
            self.logger.warning(f"Rate limit resets at: {reset_datetime}")
        
        if remaining < 10:  # Critical threshold
            wait_time = max(reset_time - int(time.time()), 0) + 5
            self.logger.error(f"Rate limit critical: waiting {wait_time} seconds")
            time.sleep(wait_time)


class RateLimitHandler:
    """Handle rate limiting with exponential backoff"""
    
    def __init__(self, client: GitHubAPIClient):
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.RateLimitHandler")
    
    def handle_rate_limit(self, response: requests.Response) -> bool:
        """Handle rate limit responses with exponential backoff"""
        if response.status_code == 403:
            rate_limit_exceeded = response.headers.get('X-RateLimit-Remaining') == '0'
            
            if rate_limit_exceeded:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - int(time.time()), 0) + 5  # 5 second buffer
                
                self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds")
                time.sleep(wait_time)
                return True
        
        return False
    
    def exponential_backoff(self, attempt: int, max_attempts: int = 5) -> bool:
        """Implement exponential backoff for retries"""
        if attempt >= max_attempts:
            return False
        
        import random
        wait_time = (2 ** attempt) + (random.uniform(0, 1))
        self.logger.info(f"Retry attempt {attempt + 1}, waiting {wait_time:.2f} seconds")
        time.sleep(wait_time)
        return True


class GitHubIssueLinkFixer:
    """Main class for fixing GitHub issue links"""
    
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
        self.rate_limiter = RateLimitHandler(client)
        self.logger = logging.getLogger(f"{__name__}.GitHubIssueLinkFixer")
        
        # Backup storage
        self.backup_dir = Path("/Users/masa/Projects/Claude-PM/backups/link_fixes")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Results tracking
        self.results: List[LinkFixResult] = []
        self.backups: List[IssueBackup] = []
    
    def fix_all_issue_links(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix links in all GitHub issues"""
        self.logger.info(f"Starting GitHub issue link fixing (dry_run={dry_run})...")
        
        # Create backup timestamp
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Get all issues
            issues = self._get_all_issues()
            self.logger.info(f"Found {len(issues)} issues to process")
            
            # Process each issue
            processed = 0
            updated = 0
            errors = 0
            skipped = 0
            
            for i, issue in enumerate(issues, 1):
                self.logger.info(f"Processing issue {i}/{len(issues)}: #{issue['number']}")
                
                try:
                    result = self._process_single_issue(issue, dry_run, backup_timestamp)
                    self.results.append(result)
                    
                    processed += 1
                    if result.success and result.changes_made:
                        updated += 1
                    elif not result.changes_made:
                        skipped += 1
                    else:
                        errors += 1
                    
                    # Rate limiting delay
                    if i % 10 == 0:  # Every 10 issues
                        self.logger.info(f"Progress: {i}/{len(issues)} processed")
                        time.sleep(1)  # Brief pause to respect rate limits
                        
                except Exception as e:
                    self.logger.error(f"Error processing issue #{issue['number']}: {e}")
                    errors += 1
            
            # Save backup and results if not dry run
            if not dry_run:
                self._save_backups(backup_timestamp)
                self._save_results(backup_timestamp)
            
            # Generate summary
            summary = {
                "success": True,
                "total_issues": len(issues),
                "processed": processed,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
                "timestamp": datetime.now().isoformat(),
                "backup_timestamp": backup_timestamp if not dry_run else None,
                "dry_run": dry_run
            }
            
            self.logger.info(f"Link fixing completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Link fixing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run
            }
    
    def _get_all_issues(self) -> List[Dict[str, Any]]:
        """Get all issues from the repository"""
        all_issues = []
        page = 1
        per_page = 100
        
        while True:
            try:
                response = self.client.make_request(
                    "GET",
                    f"/repos/{self.repository}/issues",
                    params={
                        "state": "all",
                        "per_page": per_page,
                        "page": page
                    }
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch issues page {page}: {response.status_code}")
                    break
                
                issues = response.json()
                if not issues:  # No more issues
                    break
                
                all_issues.extend(issues)
                self.logger.debug(f"Fetched page {page}: {len(issues)} issues")
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error fetching issues page {page}: {e}")
                break
        
        return all_issues
    
    def _process_single_issue(self, issue: Dict[str, Any], dry_run: bool, backup_timestamp: str) -> LinkFixResult:
        """Process a single issue to fix its links"""
        issue_number = issue['number']
        original_body = issue['body'] or ""
        
        # Extract ticket ID from title
        ticket_id = self._extract_ticket_id(issue['title'])
        
        # Check if issue needs fixing
        if not self._needs_link_fixing(original_body):
            return LinkFixResult(
                issue_number=issue_number,
                ticket_id=ticket_id or "unknown",
                success=True,
                changes_made=False,
                original_body=original_body
            )
        
        # Create backup
        backup = IssueBackup(
            issue_number=issue_number,
            issue_id=issue['node_id'],
            original_title=issue['title'],
            original_body=original_body,
            backup_timestamp=backup_timestamp
        )
        self.backups.append(backup)
        
        # Fix the links
        updated_body = self._fix_links_in_body(original_body)
        
        if dry_run:
            self.logger.info(f"DRY RUN: Would update issue #{issue_number}")
            return LinkFixResult(
                issue_number=issue_number,
                ticket_id=ticket_id or "unknown",
                success=True,
                changes_made=True,
                original_body=original_body,
                updated_body=updated_body
            )
        
        # Update the issue
        try:
            success = self._update_issue_body(issue_number, updated_body)
            
            return LinkFixResult(
                issue_number=issue_number,
                ticket_id=ticket_id or "unknown",
                success=success,
                changes_made=success,
                original_body=original_body,
                updated_body=updated_body if success else None
            )
            
        except Exception as e:
            return LinkFixResult(
                issue_number=issue_number,
                ticket_id=ticket_id or "unknown",
                success=False,
                changes_made=False,
                error_message=str(e),
                original_body=original_body
            )
    
    def _needs_link_fixing(self, body: str) -> bool:
        """Check if issue body contains local paths that need fixing"""
        # Look for local file paths
        local_path_pattern = r'/Users/masa/Projects/Claude-PM/[^\s]*'
        return bool(re.search(local_path_pattern, body))
    
    def _fix_links_in_body(self, body: str) -> str:
        """Fix local file paths in issue body to use Git repository URLs"""
        # Pattern to match local file paths
        local_path_pattern = r'/Users/masa/Projects/Claude-PM/([^\s]*)'
        
        def replace_path(match):
            relative_path = match.group(1)
            # Convert to GitHub URL
            github_url = f"https://github.com/{self.repository}/blob/main/{relative_path}"
            return github_url
        
        # Replace all occurrences
        updated_body = re.sub(local_path_pattern, replace_path, body)
        
        return updated_body
    
    def _extract_ticket_id(self, title: str) -> Optional[str]:
        """Extract ticket ID from issue title"""
        match = re.search(r'\[([A-Z]+-\d+)\]', title)
        return match.group(1) if match else None
    
    def _update_issue_body(self, issue_number: int, new_body: str) -> bool:
        """Update issue body via GitHub API"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                response = self.client.make_request(
                    "PATCH",
                    f"/repos/{self.repository}/issues/{issue_number}",
                    json={"body": new_body}
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully updated issue #{issue_number}")
                    return True
                elif response.status_code == 403:
                    if self.rate_limiter.handle_rate_limit(response):
                        continue  # Retry after rate limit wait
                elif response.status_code == 422:
                    self.logger.error(f"Validation error for issue #{issue_number}: {response.json()}")
                    return False
                
                response.raise_for_status()
                
            except requests.RequestException as e:
                if attempt == max_attempts - 1:
                    self.logger.error(f"Failed to update issue #{issue_number} after {max_attempts} attempts: {e}")
                    return False
                
                if not self.rate_limiter.exponential_backoff(attempt):
                    return False
        
        return False
    
    def _save_backups(self, timestamp: str):
        """Save backup data to file"""
        backup_file = self.backup_dir / f"issue_backups_{timestamp}.json"
        
        try:
            backup_data = {
                "timestamp": timestamp,
                "repository": self.repository,
                "backups": [asdict(backup) for backup in self.backups]
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.backups)} backups to {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving backups: {e}")
    
    def _save_results(self, timestamp: str):
        """Save results data to file"""
        results_file = self.backup_dir / f"fix_results_{timestamp}.json"
        
        try:
            results_data = {
                "timestamp": timestamp,
                "repository": self.repository,
                "results": [asdict(result) for result in self.results]
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.results)} results to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")


class TokenManager:
    """Manage GitHub API tokens securely"""
    
    @staticmethod
    def load_token_from_env(env_file_path: str = "/Users/masa/Projects/Claude-PM/.env") -> Optional[str]:
        """Load GitHub token from .env file"""
        try:
            if Path(env_file_path).exists():
                with open(env_file_path, 'r') as f:
                    for line in f:
                        if line.startswith('GITHUB_TOKEN='):
                            return line.split('=', 1)[1].strip()
        except Exception as e:
            logging.error(f"Error loading token from .env: {e}")
        
        return None
    
    @staticmethod
    def load_token_from_file(token_file_path: str) -> Optional[str]:
        """Load GitHub token from specified file"""
        try:
            token_path = Path(token_file_path).expanduser()
            if token_path.exists():
                with open(token_path, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logging.error(f"Error loading token from file: {e}")
        
        return None


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    log_dir = Path("/Users/masa/Projects/Claude-PM/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "github_link_fix.log"),
            logging.StreamHandler()
        ]
    )


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Fix GitHub issue links to use Git repository URLs instead of local paths",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Fix all issue links (basic usage)
    python fix_github_issue_links.py --repository bobmatnyc/claude-pm
    
    # Dry run to see what would be changed
    python fix_github_issue_links.py --repository bobmatnyc/claude-pm --dry-run
    
    # Use custom token file
    python fix_github_issue_links.py --repository bobmatnyc/claude-pm --token-file ~/.github_token
    
    # Verbose logging
    python fix_github_issue_links.py --repository bobmatnyc/claude-pm --verbose
        """
    )
    
    parser.add_argument("--repository", required=True,
                       help="GitHub repository (owner/repo)")
    parser.add_argument("--token-file",
                       help="File containing GitHub token (defaults to .env)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be changed without making updates")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Load token
    if args.token_file:
        token = TokenManager.load_token_from_file(args.token_file)
    else:
        token = TokenManager.load_token_from_env()
    
    if not token:
        logger.error("GitHub token not found. Please provide via .env file or --token-file")
        return 1
    
    # Validate repository format
    if '/' not in args.repository:
        logger.error("Repository must be in format 'owner/repo'")
        return 1
    
    try:
        # Initialize fixer
        client = GitHubAPIClient(token)
        fixer = GitHubIssueLinkFixer(client, args.repository)
        
        # Perform link fixing
        logger.info(f"Starting link fixing for repository: {args.repository}")
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        result = fixer.fix_all_issue_links(args.dry_run)
        
        # Print results
        if result['success']:
            logger.info(f"✅ Link fixing completed at {result['timestamp']}")
            logger.info(f"Total issues: {result['total_issues']}")
            logger.info(f"Processed: {result['processed']}")
            logger.info(f"Updated: {result['updated']}")
            logger.info(f"Skipped (no changes needed): {result['skipped']}")
            logger.info(f"Errors: {result['errors']}")
            
            if result.get('backup_timestamp'):
                logger.info(f"Backups saved with timestamp: {result['backup_timestamp']}")
            
            if args.dry_run:
                logger.info("No changes were made due to --dry-run flag")
        else:
            logger.error(f"❌ Link fixing failed: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Link fixing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())