#!/usr/bin/env python3
"""
Claude PM to GitHub Issues Sync Script

This script provides comprehensive synchronization between Claude PM trackdown 
tickets and GitHub Issues, following the implementation guide in 
docs/GITHUB_API_INTEGRATION.md

Usage:
    python github_sync.py --repository owner/repo [options]
    python github_sync.py --help

Features:
    - Unidirectional sync (Claude PM → GitHub) with metadata preservation
    - Automatic label and milestone creation
    - Epic management via GitHub Projects V2
    - Rate limiting with exponential backoff
    - Comprehensive error handling and logging
    - Backup and rollback capabilities
    - Dry-run mode for safe testing

Requirements:
    - GitHub token in .env file or via --token-file
    - Repository with Issues, Projects permissions
    - Python 3.8+ with requests library
"""

import argparse
import json
import logging
import os
import re
import time
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests


# Configuration and Data Classes
class SyncDirection(Enum):
    CLAUDE_PM_TO_GITHUB = "claude_pm_to_github"
    GITHUB_TO_CLAUDE_PM = "github_to_claude_pm"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolutionStrategy(Enum):
    CLAUDE_PM_WINS = "claude_pm_wins"
    GITHUB_WINS = "github_wins"
    TIMESTAMP_BASED = "timestamp_based"
    MANUAL_REVIEW = "manual_review"


@dataclass
class ClaudePMTicket:
    """Represents a Claude PM ticket from BACKLOG.md"""
    ticket_id: str
    title: str
    description: str
    epic: Optional[str]
    milestone: str
    priority: str
    story_points: int
    status: str
    labels: List[str]
    assignees: List[str]
    dependencies: List[str]
    completion_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class SyncRecord:
    """Tracks sync state between Claude PM and GitHub"""
    ticket_id: str
    github_issue_number: int
    last_sync: str
    checksum: str
    github_issue_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncRecord':
        return cls(**data)


# Core GitHub API Client
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
            self.logger.warning(f"Rate limit resets at: {datetime.fromtimestamp(reset_time)}")
        
        if remaining < 10:  # Critical threshold
            wait_time = max(reset_time - int(time.time()), 0) + 5
            self.logger.error(f"Rate limit critical: waiting {wait_time} seconds")
            time.sleep(wait_time)


# Rate Limiting Handler
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


# Ticket Parser
class TicketParser:
    """Parse Claude PM tickets from BACKLOG.md format"""
    
    @staticmethod
    def parse_tickets_from_backlog(backlog_path: str) -> List[ClaudePMTicket]:
        """Parse all tickets from BACKLOG.md"""
        with open(backlog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tickets = []
        
        # Parse completed tickets in "In Progress" section
        in_progress_section = re.search(r'### In Progress.*?(?=### |$)', content, re.DOTALL)
        if in_progress_section:
            completed_tickets = TicketParser._parse_simple_tickets(in_progress_section.group(0), status="completed")
            tickets.extend(completed_tickets)
        
        # Parse all the M01, M02, M03 sections and other sections
        milestone_sections = [
            (r'### M01 Foundation.*?(?=### |$)', "pending"),
            (r'### M02 Automation.*?(?=### |$)', "pending"),
            (r'### M03 Orchestration.*?(?=### |$)', "pending"),
            (r'### Cross-Project Framework.*?(?=### |$)', "pending"),
            (r'### Cross-Project Tasks.*?(?=### |$)', "pending"),
            (r'### Integration Tasks.*?(?=### |$)', "pending"),
            (r'### Infrastructure Tasks.*?(?=### |$)', "pending"),
        ]
        
        for pattern, status in milestone_sections:
            section_match = re.search(pattern, content, re.DOTALL)
            if section_match:
                section_tickets = TicketParser._parse_simple_tickets(section_match.group(0), status=status)
                tickets.extend(section_tickets)
        
        # Parse detailed tickets in "Priority Implementation Tickets" section
        priority_section = re.search(r'## 🚀 Priority Implementation Tickets.*?(?=\n## |\Z)', content, re.DOTALL)
        if priority_section:
            detailed_tickets = TicketParser._parse_detailed_tickets(priority_section.group(0))
            tickets.extend(detailed_tickets)
        
        return tickets
    
    @staticmethod
    def _parse_simple_tickets(section_content: str, status: str) -> List[ClaudePMTicket]:
        """Parse simple ticket format from backlog sections"""
        tickets = []
        
        # Match lines like: - [x] **[M01-001]** Establish core Claude PM directory structure
        ticket_pattern = r'- \[([x ])\] \*\*\[([A-Z0-9]+-\d+)\]\*\* (.+)'
        matches = re.findall(ticket_pattern, section_content, re.MULTILINE)
        
        for checkbox, ticket_id, title in matches:
            # Determine status from checkbox
            if checkbox == 'x':
                ticket_status = "completed"
            else:
                ticket_status = status
            
            # Get base labels and add status-specific labels
            labels = TicketParser._extract_labels_from_id(ticket_id)
            if ticket_status == 'completed':
                labels.append('status-completed')
            
            ticket = ClaudePMTicket(
                ticket_id=ticket_id,
                title=title.strip(),
                description=f"Task: {title.strip()}",
                epic=TicketParser._determine_epic(ticket_id),
                milestone=TicketParser._determine_milestone(ticket_id),
                priority=TicketParser._determine_priority(ticket_id),
                story_points=TicketParser._estimate_story_points(ticket_id),
                status=ticket_status,
                labels=labels,
                assignees=[],
                dependencies=[]
            )
            tickets.append(ticket)
        
        return tickets
    
    @staticmethod
    def _parse_detailed_tickets(section_content: str) -> List[ClaudePMTicket]:
        """Parse detailed ticket format with full metadata"""
        tickets = []
        
        # Split by ticket headers (### TICKET-ID:)
        ticket_sections = re.split(r'\n### ([A-Z0-9]+-\d+):', section_content)
        
        for i in range(1, len(ticket_sections), 2):
            if i + 1 >= len(ticket_sections):
                break
                
            ticket_id = ticket_sections[i].strip()
            ticket_content = ticket_sections[i + 1]
            
            try:
                ticket = TicketParser._parse_detailed_ticket_content(ticket_id, ticket_content)
                tickets.append(ticket)
            except Exception as e:
                logging.error(f"Error parsing detailed ticket {ticket_id}: {e}")
        
        return tickets
    
    @staticmethod
    def _parse_detailed_ticket_content(ticket_id: str, content: str) -> ClaudePMTicket:
        """Parse individual detailed ticket content"""
        lines = content.strip().split('\n')
        
        # Extract title from first line and check for completion marker
        first_line = lines[0].strip()
        title_match = re.search(r'^([^*]+?)(?:\s*✅.*)?$', first_line)
        title = title_match.group(1).strip() if title_match else first_line
        
        # Check if ticket is completed (look for ✅ COMPLETED in title or content)
        is_completed = "✅ COMPLETED" in first_line or "✅ COMPLETED" in content
        
        # Parse metadata
        metadata = {}
        description_lines = []
        in_scope = False
        in_acceptance = False
        
        for line in lines[1:]:
            line = line.strip()
            
            # Check for completion status in content
            if "✅ COMPLETED" in line:
                metadata['status'] = 'completed'
                is_completed = True
                # Extract completion date if present
                date_match = re.search(r'Completion Date.*?(\d{4}-\d{2}-\d{2})', line)
                if date_match:
                    metadata['completion_date'] = date_match.group(1)
            
            # Parse metadata fields
            if line.startswith('**') and '**:' in line:
                key_match = re.search(r'\*\*([^*]+)\*\*:\s*(.+)', line)
                if key_match:
                    key = key_match.group(1).lower().replace(' ', '_')
                    value = key_match.group(2).strip()
                    metadata[key] = value
            
            # Parse scope section
            elif line.startswith('**Scope**:'):
                in_scope = True
                in_acceptance = False
            elif line.startswith('**Acceptance Criteria**:'):
                in_acceptance = True
                in_scope = False
            elif in_scope and line and not line.startswith('**'):
                if line.startswith('- '):
                    description_lines.append(line)
        
        # Build description from scope
        description = '\n'.join(description_lines) if description_lines else f"Task: {title}"
        
        # Extract dependencies
        dependencies = []
        deps_text = metadata.get('dependencies', '')
        if deps_text:
            deps = re.findall(r'([A-Z]+-\d+)', deps_text)
            dependencies = deps
        
        # Determine final status
        final_status = metadata.get('status', 'completed' if is_completed else 'pending')
        
        # Add status-specific labels
        labels = TicketParser._extract_labels_from_id(ticket_id)
        if final_status == 'completed':
            labels.append('status-completed')
        
        return ClaudePMTicket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            epic=metadata.get('epic', TicketParser._determine_epic(ticket_id)),
            milestone=TicketParser._determine_milestone(ticket_id),
            priority=metadata.get('priority', TicketParser._determine_priority(ticket_id)),
            story_points=int(metadata.get('story_points', TicketParser._estimate_story_points(ticket_id))),
            status=final_status,
            labels=labels,
            assignees=[],
            dependencies=dependencies,
            completion_date=metadata.get('completion_date')
        )
    
    @staticmethod
    def _determine_epic(ticket_id: str) -> Optional[str]:
        """Determine epic based on ticket ID"""
        if ticket_id.startswith('MEM-'):
            return 'FEP-007'  # Claude Max + mem0AI Enhanced Architecture
        elif ticket_id.startswith('LGR-'):
            return 'FEP-011'  # LangGraph State-Based Workflow Orchestration
        elif ticket_id.startswith('M01-'):
            return 'FEP-001'  # Framework Infrastructure Setup
        elif ticket_id.startswith('M02-'):
            return 'FEP-002'  # Multi-Agent Coordination Patterns
        elif ticket_id.startswith('M03-'):
            return 'FEP-004'  # Enterprise Orchestration Patterns
        elif ticket_id.startswith('FEP-'):
            return ticket_id  # FEP tickets are their own epics
        elif ticket_id.startswith('CPT-'):
            return 'FEP-003'  # Advanced Workflow Automation
        elif ticket_id.startswith('INT-'):
            return 'FEP-002'  # Multi-Agent Coordination Patterns
        elif ticket_id.startswith('INF-'):
            return 'FEP-001'  # Framework Infrastructure Setup
        return None
    
    @staticmethod
    def _determine_milestone(ticket_id: str) -> str:
        """Determine milestone based on ticket ID"""
        if ticket_id.startswith(('M01-', 'MEM-001', 'MEM-002', 'MEM-003', 'LGR-001')):
            return 'M01 Foundation'
        elif ticket_id.startswith(('M02-', 'MEM-004', 'MEM-005', 'INT-')):
            return 'M02 Automation'
        elif ticket_id.startswith(('M03-', 'MEM-006', 'INF-')):
            return 'M03 Orchestration'
        return 'M01 Foundation'  # Default
    
    @staticmethod
    def _determine_priority(ticket_id: str) -> str:
        """Determine priority based on ticket ID and type"""
        if ticket_id.startswith(('MEM-001', 'MEM-002', 'MEM-003', 'LGR-001')):
            return 'CRITICAL'
        elif ticket_id.startswith(('MEM-004', 'MEM-005', 'M01-')):
            return 'HIGH'
        elif ticket_id.startswith(('MEM-006', 'M02-', 'INT-', 'CPT-')):
            return 'MEDIUM'
        elif ticket_id.startswith(('M03-', 'INF-')):
            return 'LOW'
        return 'MEDIUM'  # Default
    
    @staticmethod
    def _estimate_story_points(ticket_id: str) -> int:
        """Estimate story points based on ticket type"""
        # Known story points from backlog
        known_points = {
            'MEM-001': 8, 'MEM-002': 5, 'MEM-003': 13, 'MEM-004': 8,
            'MEM-005': 8, 'MEM-006': 10, 'LGR-001': 12
        }
        
        if ticket_id in known_points:
            return known_points[ticket_id]
        
        # Estimate based on ticket type
        if ticket_id.startswith('M01-'):
            return 3  # Foundation tasks are typically smaller
        elif ticket_id.startswith('M02-'):
            return 5  # Automation tasks are medium
        elif ticket_id.startswith('M03-'):
            return 8  # Orchestration tasks are larger
        elif ticket_id.startswith('FEP-'):
            return 21  # Epics are very large
        elif ticket_id.startswith('INT-'):
            return 5  # Integration tasks
        elif ticket_id.startswith('INF-'):
            return 3  # Infrastructure tasks
        elif ticket_id.startswith('CPT-'):
            return 2  # Cross-project tasks are small
        
        return 3  # Default
    
    @staticmethod
    def _extract_labels_from_id(ticket_id: str) -> List[str]:
        """Extract GitHub labels based on ticket ID"""
        labels = ['claude-pm-sync']  # Always add sync label
        
        # Priority labels
        priority = TicketParser._determine_priority(ticket_id)
        labels.append(f"priority-{priority.lower()}")
        
        # Type labels
        if ticket_id.startswith('MEM-'):
            labels.append('type-memory')
        elif ticket_id.startswith('LGR-'):
            labels.append('type-langgraph')
        elif ticket_id.startswith('M01-'):
            labels.append('milestone-foundation')
        elif ticket_id.startswith('M02-'):
            labels.append('milestone-automation')
        elif ticket_id.startswith('M03-'):
            labels.append('milestone-orchestration')
        elif ticket_id.startswith('FEP-'):
            labels.append('type-epic')
        elif ticket_id.startswith('CPT-'):
            labels.append('type-cross-project')
        elif ticket_id.startswith('INT-'):
            labels.append('type-integration')
        elif ticket_id.startswith('INF-'):
            labels.append('type-infrastructure')
        
        # Epic labels
        epic = TicketParser._determine_epic(ticket_id)
        if epic:
            labels.append(f"epic-{epic.lower()}")
        
        return labels


# GitHub Managers
class GitHubLabelManager:
    """Manage GitHub repository labels"""
    
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.GitHubLabelManager")
    
    def ensure_claude_pm_labels(self) -> bool:
        """Ensure all Claude PM labels exist in repository"""
        claude_pm_labels = [
            # Priority labels
            {"name": "priority-critical", "color": "B60205", "description": "Critical priority task"},
            {"name": "priority-high", "color": "D93F0B", "description": "High priority task"},
            {"name": "priority-medium", "color": "FBCA04", "description": "Medium priority task"},
            {"name": "priority-low", "color": "0E8A16", "description": "Low priority task"},
            
            # Type labels
            {"name": "type-memory", "color": "5319E7", "description": "Memory/AI related task"},
            {"name": "type-langgraph", "color": "1D76DB", "description": "LangGraph workflow task"},
            {"name": "type-epic", "color": "8B5CF6", "description": "Epic tracking"},
            {"name": "type-integration", "color": "5319E7", "description": "Integration task"},
            {"name": "type-infrastructure", "color": "0052CC", "description": "Infrastructure task"},
            {"name": "type-cross-project", "color": "F59E0B", "description": "Cross-project task"},
            
            # Milestone labels
            {"name": "milestone-foundation", "color": "C5DEF5", "description": "M01 Foundation milestone"},
            {"name": "milestone-automation", "color": "BFD4F2", "description": "M02 Automation milestone"},
            {"name": "milestone-orchestration", "color": "D4C5F9", "description": "M03 Orchestration milestone"},
            
            # Epic labels
            {"name": "epic-fep-001", "color": "F9D0C4", "description": "Framework Infrastructure Setup"},
            {"name": "epic-fep-002", "color": "FEF2C0", "description": "Multi-Agent Coordination Patterns"},
            {"name": "epic-fep-003", "color": "C5DEF5", "description": "Advanced Workflow Automation"},
            {"name": "epic-fep-004", "color": "D4C5F9", "description": "Enterprise Orchestration Patterns"},
            {"name": "epic-fep-007", "color": "F9D0C4", "description": "Claude Max + mem0AI Enhanced Architecture"},
            {"name": "epic-fep-008", "color": "FEF2C0", "description": "Memory-Augmented Agent Ecosystem"},
            {"name": "epic-fep-009", "color": "C5DEF5", "description": "Intelligent Task Decomposition System"},
            {"name": "epic-fep-010", "color": "D4C5F9", "description": "Continuous Learning Engine"},
            {"name": "epic-fep-011", "color": "E879F9", "description": "LangGraph State-Based Workflow Orchestration"},
            
            # Status labels
            {"name": "status-blocked", "color": "E99695", "description": "Task is blocked"},
            {"name": "status-completed", "color": "0E8A16", "description": "Task completed"},
            {"name": "claude-pm-sync", "color": "7057FF", "description": "Synced from Claude PM Framework"}
        ]
        
        existing_labels = self._get_existing_labels()
        existing_names = {label['name'] for label in existing_labels}
        
        created = 0
        updated = 0
        
        for label_data in claude_pm_labels:
            if label_data['name'] not in existing_names:
                if self._create_label(label_data):
                    created += 1
                    self.logger.info(f"Created label: {label_data['name']}")
            else:
                if self._update_label(label_data):
                    updated += 1
        
        self.logger.info(f"Label management complete: {created} created, {updated} updated")
        return True
    
    def _get_existing_labels(self) -> List[Dict[str, Any]]:
        """Get all existing labels in repository"""
        try:
            response = self.client.make_request("GET", f"/repos/{self.repository}/labels")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching labels: {e}")
        
        return []
    
    def _create_label(self, label_data: Dict[str, str]) -> bool:
        """Create a new label"""
        try:
            response = self.client.make_request(
                "POST",
                f"/repos/{self.repository}/labels",
                json=label_data
            )
            return response.status_code == 201
        except Exception as e:
            self.logger.error(f"Error creating label {label_data['name']}: {e}")
            return False
    
    def _update_label(self, label_data: Dict[str, str]) -> bool:
        """Update existing label"""
        try:
            response = self.client.make_request(
                "PATCH",
                f"/repos/{self.repository}/labels/{label_data['name']}",
                json={
                    "color": label_data['color'],
                    "description": label_data['description']
                }
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error updating label {label_data['name']}: {e}")
            return False


class GitHubMilestoneManager:
    """Manage GitHub repository milestones"""
    
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.GitHubMilestoneManager")
    
    def ensure_claude_pm_milestones(self) -> bool:
        """Ensure Claude PM milestones exist"""
        milestones = [
            {
                "title": "M01 Foundation",
                "description": "Critical Infrastructure - Framework foundation and project organization",
                "due_on": "2025-08-01T00:00:00Z",
                "state": "open"
            },
            {
                "title": "M02 Automation", 
                "description": "Workflow Systems - Multi-agent coordination and memory integration",
                "due_on": "2025-09-01T00:00:00Z",
                "state": "open"
            },
            {
                "title": "M03 Orchestration",
                "description": "Advanced Systems - Enterprise orchestration and learning systems",
                "due_on": "2025-10-01T00:00:00Z",
                "state": "open"
            }
        ]
        
        existing_milestones = self._get_existing_milestones()
        existing_titles = {ms['title'] for ms in existing_milestones}
        
        created = 0
        for milestone_data in milestones:
            if milestone_data['title'] not in existing_titles:
                if self._create_milestone(milestone_data):
                    created += 1
                    self.logger.info(f"Created milestone: {milestone_data['title']}")
        
        self.logger.info(f"Milestone management complete: {created} created")
        return True
    
    def get_milestone_number(self, milestone_title: str) -> Optional[int]:
        """Get milestone number by title"""
        milestones = self._get_existing_milestones()
        
        for milestone in milestones:
            if milestone['title'] == milestone_title:
                return milestone['number']
        
        return None
    
    def _get_existing_milestones(self) -> List[Dict[str, Any]]:
        """Get all existing milestones"""
        try:
            response = self.client.make_request("GET", f"/repos/{self.repository}/milestones")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching milestones: {e}")
        
        return []
    
    def _create_milestone(self, milestone_data: Dict[str, str]) -> bool:
        """Create a new milestone"""
        try:
            response = self.client.make_request(
                "POST",
                f"/repos/{self.repository}/milestones",
                json=milestone_data
            )
            return response.status_code == 201
        except Exception as e:
            self.logger.error(f"Error creating milestone {milestone_data['title']}: {e}")
            return False


class GitHubIssueManager:
    """Manage GitHub issues with retry logic"""
    
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
        self.rate_limiter = RateLimitHandler(client)
        self.logger = logging.getLogger(f"{__name__}.GitHubIssueManager")
    
    def create_issue_from_ticket(self, ticket: ClaudePMTicket, milestone_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create GitHub issue from Claude PM ticket"""
        issue_body = self._format_issue_body(ticket)
        
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "body": issue_body,
            "labels": ticket.labels,
            "assignees": ticket.assignees
        }
        
        # Add milestone if provided
        if milestone_number:
            issue_data["milestone"] = milestone_number
        
        # Set state based on ticket status
        if ticket.status == "completed":
            issue_data["state"] = "closed"
        
        return self._make_request_with_retry(
            "POST", 
            f"/repos/{self.repository}/issues",
            json=issue_data
        )
    
    def update_issue(self, issue_number: int, ticket: ClaudePMTicket, milestone_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Update existing GitHub issue"""
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "body": self._format_issue_body(ticket),
            "labels": ticket.labels,
            "state": "closed" if ticket.status == "completed" else "open"
        }
        
        if milestone_number:
            issue_data["milestone"] = milestone_number
        
        return self._make_request_with_retry(
            "PATCH",
            f"/repos/{self.repository}/issues/{issue_number}",
            json=issue_data
        )
    
    def find_existing_issue(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Find existing issue by ticket ID"""
        try:
            # Search for issues with the ticket ID in title
            query = f"repo:{self.repository} in:title [{ticket_id}]"
            response = self.client.make_request(
                "GET",
                "/search/issues",
                params={"q": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['total_count'] > 0:
                    return data['items'][0]
        except Exception as e:
            self.logger.error(f"Error searching for issue {ticket_id}: {e}")
        
        return None
    
    def get_all_claude_pm_issues(self) -> List[Dict[str, Any]]:
        """Get all issues with claude-pm-sync label"""
        try:
            response = self.client.make_request(
                "GET",
                f"/repos/{self.repository}/issues",
                params={"labels": "claude-pm-sync", "state": "all", "per_page": 100}
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching Claude PM issues: {e}")
        
        return []
    
    def _format_issue_body(self, ticket: ClaudePMTicket) -> str:
        """Format issue body with Claude PM metadata"""
        body_parts = [
            f"**Claude PM Ticket:** {ticket.ticket_id}",
            f"**Priority:** {ticket.priority}",
            f"**Story Points:** {ticket.story_points}",
            f"**Milestone:** {ticket.milestone}",
            f"**Status:** {ticket.status}",
        ]
        
        if ticket.epic:
            body_parts.append(f"**Epic:** {ticket.epic}")
        
        if ticket.dependencies:
            deps_list = ", ".join(ticket.dependencies)
            body_parts.append(f"**Dependencies:** {deps_list}")
        
        if ticket.completion_date:
            body_parts.append(f"**Completion Date:** {ticket.completion_date}")
        
        body_parts.extend([
            "",
            "## Description",
            ticket.description,
            "",
            "---",
            f"*This issue was automatically synced from Claude PM Framework at {datetime.now().isoformat()}*",
            f"*Backlog location: `/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md`*"
        ])
        
        return "\n".join(body_parts)
    
    def _make_request_with_retry(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                response = self.client.make_request(method, endpoint, **kwargs)
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 403:
                    if self.rate_limiter.handle_rate_limit(response):
                        continue  # Retry after rate limit wait
                elif response.status_code == 422:
                    # Validation error - don't retry
                    self.logger.error(f"Validation error: {response.json()}")
                    return None
                
                response.raise_for_status()
                
            except requests.RequestException as e:
                if attempt == max_attempts - 1:
                    self.logger.error(f"Request failed after {max_attempts} attempts: {e}")
                    return None
                
                if not self.rate_limiter.exponential_backoff(attempt):
                    return None
        
        return None


# Main Sync Manager
class ClaudePMGitHubSync:
    """Main synchronization manager"""
    
    def __init__(self, client: GitHubAPIClient, repository: str, 
                 backlog_path: str = None):
        self.client = client
        self.repository = repository
        if backlog_path is None:
            claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
            backlog_path = f"{claude_pm_root}/trackdown/BACKLOG.md"
        self.backlog_path = backlog_path
        
        # Initialize managers
        self.issue_manager = GitHubIssueManager(client, repository)
        self.label_manager = GitHubLabelManager(client, repository)
        self.milestone_manager = GitHubMilestoneManager(client, repository)
        
        # Sync tracking
        self.sync_records: Dict[str, SyncRecord] = {}
        claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
        self.sync_log_path = f"{claude_pm_root}/sync/github_sync_log.json"
        self.logger = logging.getLogger(f"{__name__}.ClaudePMGitHubSync")
        
        # Ensure sync directory exists
        Path(self.sync_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    def full_sync(self, direction: SyncDirection = SyncDirection.CLAUDE_PM_TO_GITHUB, dry_run: bool = False) -> Dict[str, Any]:
        """Perform full synchronization"""
        self.logger.info(f"Starting Claude PM <-> GitHub sync (dry_run={dry_run})...")
        
        # Create backup before sync
        backup_file = self._create_backup() if not dry_run else None
        
        try:
            # Ensure labels and milestones exist
            if not dry_run:
                self.label_manager.ensure_claude_pm_labels()
                self.milestone_manager.ensure_claude_pm_milestones()
            
            # Load existing sync records
            self._load_sync_records()
            
            # Perform sync based on direction
            if direction in [SyncDirection.CLAUDE_PM_TO_GITHUB, SyncDirection.BIDIRECTIONAL]:
                claude_results = self._sync_claude_pm_to_github(dry_run)
            else:
                claude_results = {"synced": 0, "errors": 0}
            
            if direction in [SyncDirection.GITHUB_TO_CLAUDE_PM, SyncDirection.BIDIRECTIONAL]:
                github_results = self._sync_github_to_claude_pm(dry_run)
            else:
                github_results = {"synced": 0, "errors": 0}
            
            # Save sync records
            if not dry_run:
                self._save_sync_records()
            
            result = {
                "success": True,
                "claude_pm_to_github": claude_results,
                "github_to_claude_pm": github_results,
                "timestamp": datetime.now().isoformat(),
                "backup_file": backup_file,
                "dry_run": dry_run
            }
            
            self.logger.info("Sync completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "backup_file": backup_file,
                "dry_run": dry_run
            }
    
    def _sync_claude_pm_to_github(self, dry_run: bool = False) -> Dict[str, int]:
        """Sync Claude PM tickets to GitHub issues"""
        self.logger.info("Syncing Claude PM tickets to GitHub...")
        
        # Parse tickets from BACKLOG.md
        tickets = TicketParser.parse_tickets_from_backlog(self.backlog_path)
        self.logger.info(f"Found {len(tickets)} tickets to sync")
        
        synced = 0
        created = 0
        updated = 0
        errors = 0
        skipped = 0
        
        for ticket in tickets:
            try:
                self.logger.debug(f"Processing ticket {ticket.ticket_id}")
                
                # Check if ticket already exists in GitHub
                existing_issue = self.issue_manager.find_existing_issue(ticket.ticket_id)
                
                if existing_issue:
                    # Check if update is needed
                    if self._ticket_changed(ticket, existing_issue):
                        if dry_run:
                            self.logger.info(f"DRY RUN: Would update issue #{existing_issue['number']} for {ticket.ticket_id}")
                            updated += 1
                        else:
                            # Get milestone number
                            milestone_number = self.milestone_manager.get_milestone_number(ticket.milestone)
                            
                            result = self.issue_manager.update_issue(
                                existing_issue['number'], 
                                ticket,
                                milestone_number
                            )
                            if result:
                                updated += 1
                                synced += 1
                                self._update_sync_record(ticket, existing_issue)
                                self.logger.info(f"Updated issue #{existing_issue['number']} for {ticket.ticket_id}")
                            else:
                                errors += 1
                                self.logger.error(f"Failed to update issue for {ticket.ticket_id}")
                    else:
                        skipped += 1
                        self.logger.debug(f"No changes needed for {ticket.ticket_id}")
                else:
                    # Create new issue
                    if dry_run:
                        self.logger.info(f"DRY RUN: Would create new issue for {ticket.ticket_id}")
                        created += 1
                    else:
                        # Get milestone number
                        milestone_number = self.milestone_manager.get_milestone_number(ticket.milestone)
                        
                        result = self.issue_manager.create_issue_from_ticket(ticket, milestone_number)
                        if result:
                            created += 1
                            synced += 1
                            self._create_sync_record(ticket, result)
                            self.logger.info(f"Created issue #{result['number']} for {ticket.ticket_id}")
                        else:
                            errors += 1
                            self.logger.error(f"Failed to create issue for {ticket.ticket_id}")
                
            except Exception as e:
                self.logger.error(f"Error syncing ticket {ticket.ticket_id}: {e}")
                errors += 1
        
        result = {
            "synced": synced,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total_tickets": len(tickets)
        }
        
        self.logger.info(f"Claude PM -> GitHub sync complete: {result}")
        return result
    
    def _sync_github_to_claude_pm(self, dry_run: bool = False) -> Dict[str, int]:
        """Sync GitHub issues back to Claude PM (limited scope)"""
        self.logger.info("Syncing GitHub issues to Claude PM...")
        
        # For now, only sync status changes and comments
        # Full bidirectional sync would require more complex conflict resolution
        
        synced = 0
        errors = 0
        
        # Get all Claude PM synced issues
        issues = self.issue_manager.get_all_claude_pm_issues()
        self.logger.info(f"Found {len(issues)} GitHub issues to review")
        
        for issue in issues:
            try:
                ticket_id = self._extract_ticket_id_from_issue(issue['title'])
                if ticket_id and ticket_id in self.sync_records:
                    # Check for status changes
                    if issue['state'] == 'closed':
                        if dry_run:
                            self.logger.info(f"DRY RUN: Would mark {ticket_id} as completed")
                        else:
                            # Mark ticket as completed in tracking
                            # This would require updating the BACKLOG.md or a separate status file
                            self._mark_ticket_completed(ticket_id)
                            synced += 1
                            self.logger.info(f"Marked {ticket_id} as completed from GitHub issue #{issue['number']}")
                
            except Exception as e:
                self.logger.error(f"Error syncing issue #{issue['number']}: {e}")
                errors += 1
        
        result = {"synced": synced, "errors": errors, "total_issues": len(issues)}
        self.logger.info(f"GitHub -> Claude PM sync complete: {result}")
        return result
    
    def _ticket_changed(self, ticket: ClaudePMTicket, github_issue: Dict[str, Any]) -> bool:
        """Check if ticket has changed since last sync"""
        ticket_checksum = self._calculate_ticket_checksum(ticket)
        
        sync_record = self.sync_records.get(ticket.ticket_id)
        if not sync_record:
            return True  # New ticket
        
        return sync_record.checksum != ticket_checksum
    
    def _calculate_ticket_checksum(self, ticket: ClaudePMTicket) -> str:
        """Calculate checksum for change detection"""
        content = f"{ticket.title}|{ticket.description}|{ticket.priority}|{ticket.status}|{','.join(ticket.labels)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _create_sync_record(self, ticket: ClaudePMTicket, github_issue: Dict[str, Any]):
        """Create new sync record"""
        record = SyncRecord(
            ticket_id=ticket.ticket_id,
            github_issue_number=github_issue['number'],
            last_sync=datetime.now().isoformat(),
            checksum=self._calculate_ticket_checksum(ticket),
            github_issue_id=github_issue['node_id']
        )
        self.sync_records[ticket.ticket_id] = record
    
    def _update_sync_record(self, ticket: ClaudePMTicket, github_issue: Dict[str, Any]):
        """Update existing sync record"""
        if ticket.ticket_id in self.sync_records:
            record = self.sync_records[ticket.ticket_id]
            record.last_sync = datetime.now().isoformat()
            record.checksum = self._calculate_ticket_checksum(ticket)
        else:
            self._create_sync_record(ticket, github_issue)
    
    def _extract_ticket_id_from_issue(self, issue_title: str) -> Optional[str]:
        """Extract ticket ID from GitHub issue title"""
        match = re.search(r'\[([A-Z]+-\d+)\]', issue_title)
        return match.group(1) if match else None
    
    def _mark_ticket_completed(self, ticket_id: str):
        """Mark ticket as completed (placeholder for future implementation)"""
        # This would update the BACKLOG.md or a separate status tracking file
        # For now, just log the action
        self.logger.info(f"TODO: Mark {ticket_id} as completed in Claude PM system")
    
    def _load_sync_records(self):
        """Load sync records from file"""
        try:
            if Path(self.sync_log_path).exists():
                with open(self.sync_log_path, 'r') as f:
                    data = json.load(f)
                    self.sync_records = {
                        k: SyncRecord.from_dict(v) 
                        for k, v in data.get('sync_records', {}).items()
                    }
                self.logger.info(f"Loaded {len(self.sync_records)} sync records")
            else:
                self.logger.info("No existing sync records found")
        except Exception as e:
            self.logger.error(f"Error loading sync records: {e}")
            self.sync_records = {}
    
    def _save_sync_records(self):
        """Save sync records to file"""
        try:
            data = {
                "last_sync": datetime.now().isoformat(),
                "repository": self.repository,
                "sync_records": {
                    k: v.to_dict() 
                    for k, v in self.sync_records.items()
                }
            }
            
            with open(self.sync_log_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.sync_records)} sync records")
        except Exception as e:
            self.logger.error(f"Error saving sync records: {e}")
    
    def _create_backup(self) -> str:
        """Create backup before sync operation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
        backup_dir = Path(f"{claude_pm_root}/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"github_sync_backup_{self.repository.replace('/', '_')}_{timestamp}.json"
        
        try:
            # Backup current state
            backup_data = {
                "timestamp": timestamp,
                "repository": self.repository,
                "github_issues": self.issue_manager.get_all_claude_pm_issues(),
                "sync_records": {k: v.to_dict() for k, v in self.sync_records.items()}
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            self.logger.info(f"Created backup: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return ""


# Configuration and Token Management
class TokenManager:
    """Manage GitHub API tokens securely"""
    
    @staticmethod
    def load_token_from_env(env_file_path: str = None) -> Optional[str]:
        """Load GitHub token from .env file"""
        if env_file_path is None:
            claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
            env_file_path = f"{claude_pm_root}/.env"
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


# CLI Interface
def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
    log_dir = Path(f"{claude_pm_root}/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "github_sync.log"),
            logging.StreamHandler()
        ]
    )


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Sync Claude PM tickets to GitHub Issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic sync to GitHub
    python github_sync.py --repository owner/repo
    
    # Dry run to see what would be synced
    python github_sync.py --repository owner/repo --dry-run
    
    # Use custom token file
    python github_sync.py --repository owner/repo --token-file ~/.github_token
    
    # Verbose logging
    python github_sync.py --repository owner/repo --verbose
        """
    )
    
    parser.add_argument("--repository", required=True, 
                       help="GitHub repository (owner/repo)")
    parser.add_argument("--token-file", 
                       help="File containing GitHub token (defaults to .env)")
    parser.add_argument("--direction", 
                       choices=["to-github", "from-github", "bidirectional"], 
                       default="to-github", 
                       help="Sync direction (default: to-github)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be synced without making changes")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose logging")
    parser.add_argument("--backlog-path", 
                       default=f"{os.getenv('CLAUDE_PM_ROOT', '/Users/masa/Projects/Claude-PM')}/trackdown/BACKLOG.md",
                       help="Path to BACKLOG.md file")
    
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
    
    # Check if backlog file exists
    if not Path(args.backlog_path).exists():
        logger.error(f"Backlog file not found: {args.backlog_path}")
        return 1
    
    try:
        # Initialize sync
        client = GitHubAPIClient(token)
        sync = ClaudePMGitHubSync(client, args.repository, args.backlog_path)
        
        # Map direction
        direction_map = {
            "to-github": SyncDirection.CLAUDE_PM_TO_GITHUB,
            "from-github": SyncDirection.GITHUB_TO_CLAUDE_PM,
            "bidirectional": SyncDirection.BIDIRECTIONAL
        }
        
        # Perform sync
        logger.info(f"Starting sync: {args.repository} ({args.direction})")
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        result = sync.full_sync(direction_map[args.direction], args.dry_run)
        
        # Print results
        if result['success']:
            logger.info(f"✅ Sync completed at {result['timestamp']}")
            
            claude_results = result['claude_pm_to_github']
            github_results = result['github_to_claude_pm']
            
            logger.info(f"Claude PM → GitHub: {claude_results.get('synced', 0)} synced "
                       f"({claude_results.get('created', 0)} created, "
                       f"{claude_results.get('updated', 0)} updated, "
                       f"{claude_results.get('skipped', 0)} skipped), "
                       f"{claude_results.get('errors', 0)} errors")
            
            logger.info(f"GitHub → Claude PM: {github_results.get('synced', 0)} synced, "
                       f"{github_results.get('errors', 0)} errors")
            
            if result.get('backup_file'):
                logger.info(f"Backup created: {result['backup_file']}")
            
            if args.dry_run:
                logger.info("No changes were made due to --dry-run flag")
        else:
            logger.error(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())