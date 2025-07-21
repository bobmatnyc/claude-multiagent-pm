#!/usr/bin/env python3
"""
GitHub Sync Test Stub
=====================

Minimal stub for E2E test compatibility.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class Ticket:
    """Represents a parsed ticket."""
    def __init__(self, ticket_id: str, title: str, status: str = "open"):
        self.ticket_id = ticket_id
        self.title = title
        self.status = status
        self.labels = []
        self.epic = None
        self.milestone = None
        self.completion_date = None if status != "completed" else datetime.now()


class TicketParser:
    """Parses ticket files."""
    
    @staticmethod
    def parse_tickets_from_backlog(backlog_path: str) -> List[Ticket]:
        """Parse tickets from a backlog file."""
        # Return mock completed tickets for testing
        return [
            Ticket("ISS-0001", "First completed issue", "completed"),
            Ticket("ISS-0002", "Second completed issue", "completed"),
            Ticket("TSK-0001", "First completed task", "completed"),
        ]


class TokenManager:
    """Manages GitHub tokens."""
    
    def __init__(self):
        self.token = None
    
    def get_token(self) -> Optional[str]:
        """Get the GitHub token."""
        return "mock-token-for-testing"


class GitHubAPIClient:
    """GitHub API client stub."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token


class GitHubIssueManager:
    """Manages GitHub issues."""
    
    def __init__(self, api_client: Optional[GitHubAPIClient] = None):
        self.api_client = api_client or GitHubAPIClient()