#!/usr/bin/env python3
"""
Test script to verify completed ticket handling in GitHub sync
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from github_sync import TicketParser, GitHubIssueManager, GitHubAPIClient, TokenManager

def test_completed_tickets():
    """Test that completed tickets would be synced as closed issues"""
    
    # Parse tickets
    backlog_path = "/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md"
    tickets = TicketParser.parse_tickets_from_backlog(backlog_path)
    
    completed_tickets = [t for t in tickets if t.status == 'completed']
    print(f"Found {len(completed_tickets)} completed tickets:")
    
    for ticket in completed_tickets:
        print(f"\n=== {ticket.ticket_id} ===")
        print(f"Title: {ticket.title}")
        print(f"Status: {ticket.status}")
        print(f"Labels: {ticket.labels}")
        print(f"Epic: {ticket.epic}")
        print(f"Milestone: {ticket.milestone}")
        if ticket.completion_date:
            print(f"Completion Date: {ticket.completion_date}")
        
        # Test issue formatting
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "labels": ticket.labels,
            "state": "closed" if ticket.status == "completed" else "open"
        }
        print(f"GitHub Issue State: {issue_data['state']}")
        print(f"Has status-completed label: {'status-completed' in ticket.labels}")

if __name__ == "__main__":
    test_completed_tickets()