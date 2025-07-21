#!/usr/bin/env python3
"""
GitHub Sync Test Stub for Integration Tests
============================================

Minimal stub for integration test compatibility.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


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
        # Check if file exists
        if not Path(backlog_path).exists():
            return []
        
        # Return mock tickets for testing
        return [
            Ticket("ISS-0001", "Test issue 1", "open"),
            Ticket("ISS-0002", "Test issue 2", "completed"),
            Ticket("TSK-0001", "Test task 1", "in_progress"),
        ]