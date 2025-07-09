#!/usr/bin/env python3
"""
Specialized script to sync completed tickets as closed GitHub Issues.
This focuses specifically on adding completed tickets that aren't already synced.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from github_sync import (
    TicketParser, GitHubAPIClient, GitHubIssueManager, 
    GitHubLabelManager, GitHubMilestoneManager, TokenManager,
    ClaudePMGitHubSync
)
import logging
import json
from pathlib import Path

def setup_logging():
    """Setup logging for this script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def sync_completed_tickets_only(repository: str, dry_run: bool = True):
    """Sync only completed tickets as closed GitHub Issues"""
    
    logger = logging.getLogger(__name__)
    
    # Load GitHub token
    token = TokenManager.load_token_from_env()
    if not token:
        logger.error("GitHub token not found in .env file")
        return False
    
    # Initialize GitHub client and managers
    client = GitHubAPIClient(token)
    issue_manager = GitHubIssueManager(client, repository)
    label_manager = GitHubLabelManager(client, repository)
    milestone_manager = GitHubMilestoneManager(client, repository)
    
    # Parse tickets from ai-trackdown-tools structure
    framework_path = "/Users/masa/Projects/claude-multiagent-pm"
    
    # Try to get completed tickets from ai-trackdown-tools
    try:
        import subprocess
        result = subprocess.run(
            ["aitrackdown", "status", "--filter", "status=done", "--export", "-"],
            cwd=framework_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse the JSON output from aitrackdown
            import json
            ai_trackdown_data = json.loads(result.stdout)
            tickets = []
            
            # Convert ai-trackdown format to expected ticket format
            for item in ai_trackdown_data.get('items', []):
                if item.get('status') == 'done':
                    # Create a ticket-like object
                    ticket = type('Ticket', (), {
                        'ticket_id': item.get('id', 'UNKNOWN'),
                        'title': item.get('title', 'No Title'),
                        'status': 'completed',
                        'milestone': item.get('milestone', 'No Milestone'),
                        'description': item.get('description', ''),
                        'priority': item.get('priority', 'medium'),
                        'assignee': item.get('assignee', 'unassigned')
                    })()
                    tickets.append(ticket)
        else:
            logger.warning(f"Failed to get completed tickets from ai-trackdown: {result.stderr}")
            tickets = []
    except Exception as e:
        logger.warning(f"Error parsing ai-trackdown data: {e}")
        tickets = []
    
    # Filter to completed tickets only
    completed_tickets = [t for t in tickets if t.status == 'completed']
    logger.info(f"Found {len(completed_tickets)} completed tickets")
    
    # Load existing sync records to avoid duplicates
    sync_log_path = "/Users/masa/Projects/claude-multiagent-pm/sync/github_sync_log.json"
    existing_tickets = set()
    if Path(sync_log_path).exists():
        with open(sync_log_path, 'r') as f:
            sync_data = json.load(f)
            existing_tickets = set(sync_data.get('sync_records', {}).keys())
    
    logger.info(f"Found {len(existing_tickets)} already synced tickets")
    
    # Ensure labels and milestones exist (dry-run skips this)
    if not dry_run:
        logger.info("Ensuring labels and milestones exist...")
        label_manager.ensure_claude_pm_labels()
        milestone_manager.ensure_claude_pm_milestones()
    
    # Process completed tickets
    created = 0
    updated = 0
    skipped = 0
    errors = 0
    
    for ticket in completed_tickets:
        try:
            # Check if already exists
            existing_issue = issue_manager.find_existing_issue(ticket.ticket_id)
            
            if existing_issue:
                # Check if it needs to be updated to closed state
                if existing_issue.get('state') == 'open':
                    if dry_run:
                        logger.info(f"DRY RUN: Would close issue #{existing_issue['number']} for {ticket.ticket_id}")
                        updated += 1
                    else:
                        # Get milestone number
                        milestone_number = milestone_manager.get_milestone_number(ticket.milestone)
                        result = issue_manager.update_issue(existing_issue['number'], ticket, milestone_number)
                        if result:
                            logger.info(f"Closed issue #{existing_issue['number']} for {ticket.ticket_id}")
                            updated += 1
                        else:
                            logger.error(f"Failed to close issue for {ticket.ticket_id}")
                            errors += 1
                else:
                    logger.debug(f"Issue #{existing_issue['number']} for {ticket.ticket_id} already closed")
                    skipped += 1
            else:
                # Create new closed issue
                if dry_run:
                    logger.info(f"DRY RUN: Would create closed issue for {ticket.ticket_id}")
                    created += 1
                else:
                    # Get milestone number
                    milestone_number = milestone_manager.get_milestone_number(ticket.milestone)
                    result = issue_manager.create_issue_from_ticket(ticket, milestone_number)
                    if result:
                        logger.info(f"Created closed issue #{result['number']} for {ticket.ticket_id}")
                        created += 1
                    else:
                        logger.error(f"Failed to create issue for {ticket.ticket_id}")
                        errors += 1
        
        except Exception as e:
            logger.error(f"Error processing {ticket.ticket_id}: {e}")
            errors += 1
    
    # Summary
    logger.info(f"\n=== Completed Tickets Sync Summary ===")
    logger.info(f"Total completed tickets: {len(completed_tickets)}")
    logger.info(f"New closed issues created: {created}")
    logger.info(f"Issues updated to closed: {updated}")
    logger.info(f"Already closed (skipped): {skipped}")
    logger.info(f"Errors: {errors}")
    
    if dry_run:
        logger.info("DRY RUN MODE - No actual changes were made")
    
    return errors == 0

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync completed tickets as closed GitHub Issues")
    parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--execute", action="store_true", help="Actually execute the sync (not dry-run)")
    
    args = parser.parse_args()
    
    if not args.execute and not args.dry_run:
        print("Please specify either --dry-run or --execute")
        return 1
    
    setup_logging()
    
    dry_run = not args.execute
    success = sync_completed_tickets_only(args.repository, dry_run)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())