# GitHub API Integration Guide for Claude PM Framework

This document provides comprehensive guidance for syncing Claude PM trackdown tickets to GitHub Issues using the GitHub API. It covers authentication, rate limiting, issues management, sync strategies, and implementation best practices for 2025.

## Table of Contents

1. [GitHub API Authentication & Setup](#github-api-authentication--setup)
2. [Issues Management via API](#issues-management-via-api)
3. [Projects & Epics Setup](#projects--epics-setup)
4. [Labels & Milestones Management](#labels--milestones-management)
5. [Sync Strategy Recommendations](#sync-strategy-recommendations)
6. [Implementation Examples](#implementation-examples)
7. [Error Handling & Monitoring](#error-handling--monitoring)

## GitHub API Authentication & Setup

### Personal Access Token (PAT) Best Practices 2025

#### 1. Fine-Grained Tokens (Recommended)
Use fine-grained personal access tokens instead of classic PATs for better security:

```python
# Example: Creating authenticated requests with fine-grained token
import requests
from typing import Dict, Any

class GitHubAPIClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        self._check_rate_limit(response)
        return response
    
    def _check_rate_limit(self, response: requests.Response):
        """Monitor rate limit headers and implement backoff if needed"""
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining < 10:  # Warning threshold
            print(f"Rate limit warning: {remaining} requests remaining")
            print(f"Rate limit resets at: {reset_time}")
```

#### 2. Required Token Permissions

For Claude PM ticket sync, your token needs these permissions:

**Repository Permissions:**
- `Issues`: Read and write (for creating/updating issues)
- `Metadata`: Read (for accessing repository metadata)
- `Pull requests`: Read (for linking issues to PRs)

**Organization Permissions (if applicable):**
- `Projects`: Read and write (for project board management)

#### 3. Secure Token Storage

```python
import os
from pathlib import Path
import json

class TokenManager:
    def __init__(self, config_path: str = "~/.claude_pm/github_config.json"):
        self.config_path = Path(config_path).expanduser()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def store_token(self, token: str, repository: str):
        """Store token securely (consider using keyring for production)"""
        config = self.load_config()
        config[repository] = {
            "token": token,  # In production, use keyring or environment variables
            "created_at": "2025-07-07",
            "permissions": ["issues", "metadata", "projects"]
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Secure the file
        os.chmod(self.config_path, 0o600)
    
    def load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_token(self, repository: str) -> str:
        """Retrieve token for repository"""
        config = self.load_config()
        return config.get(repository, {}).get("token")
```

### Rate Limiting Considerations

#### 1. Rate Limit Monitoring

```python
import time
from typing import Optional
import logging

class RateLimitHandler:
    def __init__(self, client: GitHubAPIClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
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
        
        wait_time = (2 ** attempt) + (random.uniform(0, 1))
        self.logger.info(f"Retry attempt {attempt + 1}, waiting {wait_time:.2f} seconds")
        time.sleep(wait_time)
        return True
```

#### 2. Authenticated vs Unauthenticated Limits

**Authenticated Requests:**
- Primary rate limit: 5,000 requests per hour
- Secondary rate limits apply for specific endpoints
- GitHub Apps scale with repository and user count

**Best Practices:**
- Always use authenticated requests for higher limits
- Monitor `X-RateLimit-Remaining` header
- Implement conditional requests with ETags
- Use GraphQL for complex queries to reduce request count

## Issues Management via API

### Creating Issues with Metadata

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re

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

class TicketParser:
    """Parse Claude PM tickets from BACKLOG.md format"""
    
    @staticmethod
    def parse_ticket_from_markdown(ticket_text: str) -> ClaudePMTicket:
        """Parse ticket from markdown format like MEM-001, M01-001, etc."""
        lines = ticket_text.strip().split('\n')
        
        # Extract ticket ID and title
        header_match = re.search(r'\*\*\[([^\]]+)\]\*\*\s+(.+)', lines[0])
        if not header_match:
            raise ValueError(f"Invalid ticket format: {lines[0]}")
        
        ticket_id = header_match.group(1)
        title = header_match.group(2)
        
        # Parse metadata
        metadata = {}
        description_lines = []
        in_description = False
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('**') and '**:' in line:
                key_match = re.search(r'\*\*([^*]+)\*\*:\s*(.+)', line)
                if key_match:
                    key = key_match.group(1).lower().replace(' ', '_')
                    value = key_match.group(2)
                    metadata[key] = value
            elif line.startswith('**Scope**:') or in_description:
                in_description = True
                if not line.startswith('**'):
                    description_lines.append(line)
        
        return ClaudePMTicket(
            ticket_id=ticket_id,
            title=title,
            description='\n'.join(description_lines),
            epic=metadata.get('epic'),
            milestone=metadata.get('milestone', 'M01'),
            priority=metadata.get('priority', 'MEDIUM'),
            story_points=int(metadata.get('story_points', 0)),
            status='pending',
            labels=TicketParser._extract_labels(metadata),
            assignees=[],
            dependencies=TicketParser._parse_dependencies(metadata.get('dependencies', ''))
        )
    
    @staticmethod
    def _extract_labels(metadata: Dict[str, str]) -> List[str]:
        """Extract GitHub labels from ticket metadata"""
        labels = []
        
        # Priority labels
        priority = metadata.get('priority', 'MEDIUM').upper()
        labels.append(f"priority-{priority.lower()}")
        
        # Epic labels
        if epic := metadata.get('epic'):
            labels.append(f"epic-{epic.lower()}")
        
        # Type labels based on ticket ID
        ticket_id = metadata.get('ticket_id', '')
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
        
        return labels
    
    @staticmethod
    def _parse_dependencies(deps_text: str) -> List[str]:
        """Parse dependencies from text like 'MEM-001 complete, MEM-002'"""
        if not deps_text:
            return []
        
        deps = []
        for dep in deps_text.split(','):
            dep = dep.strip()
            # Extract ticket IDs from dependency text
            match = re.search(r'([A-Z]+-\d+)', dep)
            if match:
                deps.append(match.group(1))
        
        return deps

class GitHubIssueManager:
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository  # format: "owner/repo"
        self.rate_limiter = RateLimitHandler(client)
    
    def create_issue_from_ticket(self, ticket: ClaudePMTicket) -> Optional[Dict[str, Any]]:
        """Create GitHub issue from Claude PM ticket"""
        
        issue_body = self._format_issue_body(ticket)
        
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "body": issue_body,
            "labels": ticket.labels,
            "assignees": ticket.assignees
        }
        
        # Add milestone if it exists
        if milestone_number := self._get_milestone_number(ticket.milestone):
            issue_data["milestone"] = milestone_number
        
        return self._make_request_with_retry(
            "POST", 
            f"/repos/{self.repository}/issues",
            json=issue_data
        )
    
    def _format_issue_body(self, ticket: ClaudePMTicket) -> str:
        """Format issue body with Claude PM metadata"""
        body_parts = [
            f"**Claude PM Ticket:** {ticket.ticket_id}",
            f"**Priority:** {ticket.priority}",
            f"**Story Points:** {ticket.story_points}",
            f"**Milestone:** {ticket.milestone}",
        ]
        
        if ticket.epic:
            body_parts.append(f"**Epic:** {ticket.epic}")
        
        if ticket.dependencies:
            deps_list = ", ".join(ticket.dependencies)
            body_parts.append(f"**Dependencies:** {deps_list}")
        
        body_parts.extend([
            "",
            "## Description",
            ticket.description,
            "",
            "---",
            "*This issue was automatically created from Claude PM Framework trackdown system.*"
        ])
        
        return "\n".join(body_parts)
    
    def update_issue(self, issue_number: int, ticket: ClaudePMTicket) -> Optional[Dict[str, Any]]:
        """Update existing GitHub issue"""
        
        issue_data = {
            "title": f"[{ticket.ticket_id}] {ticket.title}",
            "body": self._format_issue_body(ticket),
            "labels": ticket.labels,
            "state": "closed" if ticket.status == "completed" else "open"
        }
        
        return self._make_request_with_retry(
            "PATCH",
            f"/repos/{self.repository}/issues/{issue_number}",
            json=issue_data
        )
    
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
                    print(f"Validation error: {response.json()}")
                    return None
                
                response.raise_for_status()
                
            except requests.RequestException as e:
                if attempt == max_attempts - 1:
                    print(f"Request failed after {max_attempts} attempts: {e}")
                    return None
                
                if not self.rate_limiter.exponential_backoff(attempt):
                    return None
        
        return None
```

### Handling Issue States and Updates

```python
class IssueStateManager:
    """Manage issue state synchronization"""
    
    def __init__(self, issue_manager: GitHubIssueManager):
        self.issue_manager = issue_manager
    
    def sync_issue_state(self, ticket: ClaudePMTicket, github_issue: Dict[str, Any]) -> bool:
        """Sync issue state based on ticket status"""
        
        current_state = github_issue.get('state', 'open')
        target_state = self._get_target_state(ticket.status)
        
        if current_state != target_state:
            print(f"Updating issue #{github_issue['number']} state: {current_state} -> {target_state}")
            
            result = self.issue_manager.update_issue(
                github_issue['number'],
                ticket
            )
            
            return result is not None
        
        return True  # No update needed
    
    def _get_target_state(self, ticket_status: str) -> str:
        """Map ticket status to GitHub issue state"""
        status_mapping = {
            'completed': 'closed',
            'in_progress': 'open',
            'pending': 'open',
            'blocked': 'open'
        }
        
        return status_mapping.get(ticket_status.lower(), 'open')
```

## Projects & Epics Setup

### Creating GitHub Projects via API

```python
class GitHubProjectManager:
    def __init__(self, client: GitHubAPIClient, owner: str):
        self.client = client
        self.owner = owner  # Organization or user
    
    def create_project(self, title: str, description: str) -> Optional[Dict[str, Any]]:
        """Create GitHub Project (Projects V2)"""
        
        # Use GraphQL for Projects V2
        mutation = """
        mutation CreateProjectV2($ownerId: ID!, $title: String!, $description: String!) {
          createProjectV2(input: {
            ownerId: $ownerId
            title: $title
            description: $description
          }) {
            projectV2 {
              id
              number
              title
              url
            }
          }
        }
        """
        
        owner_id = self._get_owner_id()
        if not owner_id:
            return None
        
        variables = {
            "ownerId": owner_id,
            "title": title,
            "description": description
        }
        
        return self._execute_graphql(mutation, variables)
    
    def add_issue_to_project(self, project_id: str, issue_id: str) -> bool:
        """Add issue to project using GraphQL"""
        
        mutation = """
        mutation AddIssueToProject($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {
            projectId: $projectId
            contentId: $contentId
          }) {
            item {
              id
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id,
            "contentId": issue_id
        }
        
        result = self._execute_graphql(mutation, variables)
        return result is not None
    
    def _get_owner_id(self) -> Optional[str]:
        """Get owner ID for GraphQL operations"""
        if self.owner.startswith('@'):
            # User
            query = f"""
            query {{
              user(login: "{self.owner[1:]}") {{
                id
              }}
            }}
            """
        else:
            # Organization
            query = f"""
            query {{
              organization(login: "{self.owner}") {{
                id
              }}
            }}
            """
        
        result = self._execute_graphql(query)
        if result and result.get('data'):
            data = result['data']
            return data.get('user', data.get('organization', {})).get('id')
        
        return None
    
    def _execute_graphql(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Execute GraphQL query/mutation"""
        response = self.client.make_request(
            "POST",
            "/graphql",
            json={
                "query": query,
                "variables": variables or {}
            }
        )
        
        if response.status_code == 200:
            return response.json()
        
        return None

class EpicManager:
    """Manage epic creation and issue linking"""
    
    def __init__(self, project_manager: GitHubProjectManager, issue_manager: GitHubIssueManager):
        self.project_manager = project_manager
        self.issue_manager = issue_manager
    
    def create_epic_structure(self, epic_name: str, tickets: List[ClaudePMTicket]) -> Dict[str, Any]:
        """Create epic as project with linked issues"""
        
        # Create project for epic
        epic_description = f"Epic tracking for {epic_name}"
        project = self.project_manager.create_project(
            title=f"Epic: {epic_name}",
            description=epic_description
        )
        
        if not project:
            return {"success": False, "error": "Failed to create project"}
        
        project_id = project['data']['createProjectV2']['projectV2']['id']
        
        # Create issues and add to project
        created_issues = []
        for ticket in tickets:
            issue = self.issue_manager.create_issue_from_ticket(ticket)
            if issue:
                # Get issue node ID for GraphQL
                issue_node_id = issue.get('node_id')
                if issue_node_id:
                    self.project_manager.add_issue_to_project(project_id, issue_node_id)
                
                created_issues.append(issue)
        
        return {
            "success": True,
            "project": project,
            "issues": created_issues
        }
```

## Labels & Milestones Management

### Label Management System

```python
class GitHubLabelManager:
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
    
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
            {"name": "type-infrastructure", "color": "0052CC", "description": "Infrastructure task"},
            {"name": "type-integration", "color": "5319E7", "description": "Integration task"},
            
            # Milestone labels
            {"name": "milestone-foundation", "color": "C5DEF5", "description": "M01 Foundation milestone"},
            {"name": "milestone-automation", "color": "BFD4F2", "description": "M02 Automation milestone"},
            {"name": "milestone-orchestration", "color": "D4C5F9", "description": "M03 Orchestration milestone"},
            
            # Epic labels
            {"name": "epic-fep-007", "color": "F9D0C4", "description": "Claude Max + mem0AI Enhanced Architecture"},
            {"name": "epic-fep-008", "color": "FEF2C0", "description": "Memory-Augmented Agent Ecosystem"},
            {"name": "epic-fep-009", "color": "C5DEF5", "description": "Intelligent Task Decomposition System"},
            
            # Status labels
            {"name": "status-blocked", "color": "E99695", "description": "Task is blocked"},
            {"name": "status-needs-review", "color": "FBCA04", "description": "Needs review"},
            {"name": "claude-pm-sync", "color": "7057FF", "description": "Synced from Claude PM Framework"}
        ]
        
        existing_labels = self._get_existing_labels()
        existing_names = {label['name'] for label in existing_labels}
        
        for label_data in claude_pm_labels:
            if label_data['name'] not in existing_names:
                self._create_label(label_data)
            else:
                self._update_label(label_data)
        
        return True
    
    def _get_existing_labels(self) -> List[Dict[str, Any]]:
        """Get all existing labels in repository"""
        response = self.client.make_request(
            "GET",
            f"/repos/{self.repository}/labels"
        )
        
        if response.status_code == 200:
            return response.json()
        
        return []
    
    def _create_label(self, label_data: Dict[str, str]) -> bool:
        """Create a new label"""
        response = self.client.make_request(
            "POST",
            f"/repos/{self.repository}/labels",
            json=label_data
        )
        
        return response.status_code == 201
    
    def _update_label(self, label_data: Dict[str, str]) -> bool:
        """Update existing label"""
        response = self.client.make_request(
            "PATCH",
            f"/repos/{self.repository}/labels/{label_data['name']}",
            json={
                "color": label_data['color'],
                "description": label_data['description']
            }
        )
        
        return response.status_code == 200

class GitHubMilestoneManager:
    def __init__(self, client: GitHubAPIClient, repository: str):
        self.client = client
        self.repository = repository
    
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
        
        for milestone_data in milestones:
            if milestone_data['title'] not in existing_titles:
                self._create_milestone(milestone_data)
        
        return True
    
    def _get_existing_milestones(self) -> List[Dict[str, Any]]:
        """Get all existing milestones"""
        response = self.client.make_request(
            "GET",
            f"/repos/{self.repository}/milestones"
        )
        
        if response.status_code == 200:
            return response.json()
        
        return []
    
    def _create_milestone(self, milestone_data: Dict[str, str]) -> bool:
        """Create a new milestone"""
        response = self.client.make_request(
            "POST",
            f"/repos/{self.repository}/milestones",
            json=milestone_data
        )
        
        return response.status_code == 201
    
    def get_milestone_number(self, milestone_title: str) -> Optional[int]:
        """Get milestone number by title"""
        milestones = self._get_existing_milestones()
        
        for milestone in milestones:
            if milestone['title'] == milestone_title:
                return milestone['number']
        
        return None
```

## Sync Strategy Recommendations

### Bidirectional vs Unidirectional Sync

#### Recommended Approach: Hybrid Sync

```python
from enum import Enum
from datetime import datetime
import hashlib

class SyncDirection(Enum):
    CLAUDE_PM_TO_GITHUB = "claude_pm_to_github"
    GITHUB_TO_CLAUDE_PM = "github_to_claude_pm"
    BIDIRECTIONAL = "bidirectional"

class SyncRecord:
    def __init__(self, ticket_id: str, github_issue_number: int, 
                 last_sync: datetime, checksum: str):
        self.ticket_id = ticket_id
        self.github_issue_number = github_issue_number
        self.last_sync = last_sync
        self.checksum = checksum

class ClaudePMGitHubSync:
    def __init__(self, client: GitHubAPIClient, repository: str, 
                 backlog_path: str = "/Users/masa/Projects/claude-multiagent-pm/trackdown/BACKLOG.md"):
        self.client = client
        self.repository = repository
        self.backlog_path = backlog_path
        self.issue_manager = GitHubIssueManager(client, repository)
        self.label_manager = GitHubLabelManager(client, repository)
        self.milestone_manager = GitHubMilestoneManager(client, repository)
        
        # Sync tracking
        self.sync_records: Dict[str, SyncRecord] = {}
        self.sync_log_path = "/Users/masa/Projects/claude-multiagent-pm/sync/github_sync_log.json"
    
    def full_sync(self, direction: SyncDirection = SyncDirection.CLAUDE_PM_TO_GITHUB) -> Dict[str, Any]:
        """Perform full synchronization"""
        
        print("Starting Claude PM <-> GitHub sync...")
        
        # Ensure labels and milestones exist
        self.label_manager.ensure_claude_pm_labels()
        self.milestone_manager.ensure_claude_pm_milestones()
        
        # Load existing sync records
        self._load_sync_records()
        
        if direction in [SyncDirection.CLAUDE_PM_TO_GITHUB, SyncDirection.BIDIRECTIONAL]:
            claude_results = self._sync_claude_pm_to_github()
        else:
            claude_results = {"synced": 0, "errors": 0}
        
        if direction in [SyncDirection.GITHUB_TO_CLAUDE_PM, SyncDirection.BIDIRECTIONAL]:
            github_results = self._sync_github_to_claude_pm()
        else:
            github_results = {"synced": 0, "errors": 0}
        
        # Save sync records
        self._save_sync_records()
        
        return {
            "success": True,
            "claude_pm_to_github": claude_results,
            "github_to_claude_pm": github_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _sync_claude_pm_to_github(self) -> Dict[str, int]:
        """Sync Claude PM tickets to GitHub issues"""
        
        # Parse tickets from BACKLOG.md
        tickets = self._parse_backlog_tickets()
        
        synced = 0
        errors = 0
        
        for ticket in tickets:
            try:
                # Check if ticket already exists in GitHub
                existing_issue = self._find_existing_issue(ticket.ticket_id)
                
                if existing_issue:
                    # Update existing issue if changed
                    if self._ticket_changed(ticket, existing_issue):
                        result = self.issue_manager.update_issue(
                            existing_issue['number'], 
                            ticket
                        )
                        if result:
                            synced += 1
                            self._update_sync_record(ticket, existing_issue)
                else:
                    # Create new issue
                    result = self.issue_manager.create_issue_from_ticket(ticket)
                    if result:
                        synced += 1
                        self._create_sync_record(ticket, result)
                
            except Exception as e:
                print(f"Error syncing ticket {ticket.ticket_id}: {e}")
                errors += 1
        
        return {"synced": synced, "errors": errors}
    
    def _sync_github_to_claude_pm(self) -> Dict[str, int]:
        """Sync GitHub issues back to Claude PM (limited scope)"""
        
        # For now, only sync status changes and comments
        # Full bidirectional sync would require more complex conflict resolution
        
        synced = 0
        errors = 0
        
        # Get all Claude PM synced issues
        issues = self._get_claude_pm_issues()
        
        for issue in issues:
            try:
                ticket_id = self._extract_ticket_id(issue['title'])
                if ticket_id and ticket_id in self.sync_records:
                    # Check for status changes
                    if issue['state'] == 'closed':
                        # Mark ticket as completed in tracking
                        # This would require updating the BACKLOG.md or a separate status file
                        self._mark_ticket_completed(ticket_id)
                        synced += 1
                
            except Exception as e:
                print(f"Error syncing issue #{issue['number']}: {e}")
                errors += 1
        
        return {"synced": synced, "errors": errors}
    
    def _parse_backlog_tickets(self) -> List[ClaudePMTicket]:
        """Parse all tickets from BACKLOG.md"""
        with open(self.backlog_path, 'r') as f:
            content = f.read()
        
        tickets = []
        
        # Find all ticket sections (simplified parsing)
        ticket_pattern = r'### ([A-Z]+-\d+):[^#]+((?:\n(?!###)[^\n]*)*)'
        matches = re.findall(ticket_pattern, content, re.MULTILINE)
        
        for ticket_id, ticket_content in matches:
            try:
                # Parse individual ticket
                ticket = TicketParser.parse_ticket_from_markdown(
                    f"**[{ticket_id}]** {ticket_content}"
                )
                tickets.append(ticket)
            except Exception as e:
                print(f"Error parsing ticket {ticket_id}: {e}")
        
        return tickets
    
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
```

### Conflict Resolution Strategies

```python
class ConflictResolutionStrategy(Enum):
    CLAUDE_PM_WINS = "claude_pm_wins"
    GITHUB_WINS = "github_wins"
    TIMESTAMP_BASED = "timestamp_based"
    MANUAL_REVIEW = "manual_review"

class ConflictResolver:
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.CLAUDE_PM_WINS):
        self.strategy = strategy
    
    def resolve_conflict(self, claude_ticket: ClaudePMTicket, 
                        github_issue: Dict[str, Any],
                        last_sync: datetime) -> Dict[str, Any]:
        """Resolve sync conflict between Claude PM and GitHub"""
        
        conflict_data = {
            "ticket_id": claude_ticket.ticket_id,
            "github_issue_number": github_issue['number'],
            "conflicts": self._detect_conflicts(claude_ticket, github_issue),
            "resolution_strategy": self.strategy.value
        }
        
        if self.strategy == ConflictResolutionStrategy.CLAUDE_PM_WINS:
            return self._resolve_claude_pm_wins(claude_ticket, github_issue, conflict_data)
        elif self.strategy == ConflictResolutionStrategy.GITHUB_WINS:
            return self._resolve_github_wins(claude_ticket, github_issue, conflict_data)
        elif self.strategy == ConflictResolutionStrategy.TIMESTAMP_BASED:
            return self._resolve_timestamp_based(claude_ticket, github_issue, last_sync, conflict_data)
        else:  # MANUAL_REVIEW
            return self._queue_for_manual_review(claude_ticket, github_issue, conflict_data)
    
    def _detect_conflicts(self, claude_ticket: ClaudePMTicket, 
                         github_issue: Dict[str, Any]) -> List[str]:
        """Detect specific conflicts between sources"""
        conflicts = []
        
        # Title conflicts
        expected_title = f"[{claude_ticket.ticket_id}] {claude_ticket.title}"
        if github_issue['title'] != expected_title:
            conflicts.append("title_mismatch")
        
        # Status conflicts
        github_state = github_issue['state']
        expected_state = "closed" if claude_ticket.status == "completed" else "open"
        if github_state != expected_state:
            conflicts.append("status_mismatch")
        
        # Label conflicts
        github_labels = {label['name'] for label in github_issue['labels']}
        expected_labels = set(claude_ticket.labels)
        if github_labels != expected_labels:
            conflicts.append("labels_mismatch")
        
        return conflicts
```

## Implementation Examples

### Complete Sync Script Example

```python
#!/usr/bin/env python3
"""
Claude PM to GitHub Issues Sync Script
Usage: python sync_github.py --repository owner/repo --token-file ~/.github_token
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Sync Claude PM tickets to GitHub Issues")
    parser.add_argument("--repository", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--token-file", required=True, help="File containing GitHub token")
    parser.add_argument("--direction", choices=["to-github", "from-github", "bidirectional"], 
                       default="to-github", help="Sync direction")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without making changes")
    
    args = parser.parse_args()
    
    # Load token
    token_path = Path(args.token_file).expanduser()
    with open(token_path, 'r') as f:
        token = f.read().strip()
    
    # Initialize sync
    client = GitHubAPIClient(token)
    sync = ClaudePMGitHubSync(client, args.repository)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        # Implement dry run logic here
        return
    
    # Perform sync
    direction_map = {
        "to-github": SyncDirection.CLAUDE_PM_TO_GITHUB,
        "from-github": SyncDirection.GITHUB_TO_CLAUDE_PM,
        "bidirectional": SyncDirection.BIDIRECTIONAL
    }
    
    result = sync.full_sync(direction_map[args.direction])
    
    # Print results
    print(f"Sync completed at {result['timestamp']}")
    print(f"Claude PM -> GitHub: {result['claude_pm_to_github']['synced']} synced, "
          f"{result['claude_pm_to_github']['errors']} errors")
    print(f"GitHub -> Claude PM: {result['github_to_claude_pm']['synced']} synced, "
          f"{result['github_to_claude_pm']['errors']} errors")

if __name__ == "__main__":
    main()
```

### CLI Integration Example

```python
# Add to Claude PM CLI commands
@click.command()
@click.option('--repository', required=True, help='GitHub repository (owner/repo)')
@click.option('--direction', type=click.Choice(['to-github', 'from-github', 'bidirectional']), 
              default='to-github', help='Sync direction')
@click.option('--dry-run', is_flag=True, help='Show what would be synced')
def sync_github(repository: str, direction: str, dry_run: bool):
    """Sync Claude PM tickets with GitHub Issues"""
    
    # Load configuration
    config = load_claude_pm_config()
    token = config.get('github', {}).get('token')
    
    if not token:
        click.echo("GitHub token not configured. Run: claude-pm config github --token <token>")
        return
    
    client = GitHubAPIClient(token)
    sync = ClaudePMGitHubSync(client, repository)
    
    if dry_run:
        click.echo("DRY RUN: Analyzing sync requirements...")
        # Implement dry run analysis
        return
    
    with click.progressbar(label='Syncing with GitHub') as bar:
        result = sync.full_sync(SyncDirection[direction.upper().replace('-', '_')])
    
    click.echo(f"✅ Sync completed successfully")
    click.echo(f"   Claude PM -> GitHub: {result['claude_pm_to_github']['synced']} items")
    click.echo(f"   GitHub -> Claude PM: {result['github_to_claude_pm']['synced']} items")
```

## Error Handling & Monitoring

### Comprehensive Error Handling

```python
class GitHubSyncError(Exception):
    """Base exception for GitHub sync operations"""
    pass

class RateLimitExceededError(GitHubSyncError):
    """Raised when API rate limit is exceeded"""
    pass

class AuthenticationError(GitHubSyncError):
    """Raised when authentication fails"""
    pass

class SyncConflictError(GitHubSyncError):
    """Raised when sync conflicts cannot be resolved automatically"""
    pass

class SyncMonitor:
    def __init__(self, log_path: str = "/Users/masa/Projects/claude-multiagent-pm/logs/github_sync.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        import logging
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_sync_start(self, repository: str, direction: str):
        """Log sync operation start"""
        self.logger.info(f"Starting sync: {repository} ({direction})")
    
    def log_sync_complete(self, repository: str, results: Dict[str, Any]):
        """Log sync operation completion"""
        self.logger.info(f"Sync completed: {repository} - Results: {results}")
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        context_str = f" Context: {context}" if context else ""
        self.logger.error(f"Error in {operation}: {error}{context_str}")
    
    def generate_sync_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate sync report for date range"""
        
        # Parse log file for sync operations in date range
        # This is a simplified implementation
        
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "rate_limit_hits": 0,
            "most_common_errors": []
        }

# Usage in sync operations
def sync_with_monitoring():
    monitor = SyncMonitor()
    
    try:
        monitor.log_sync_start("owner/repo", "bidirectional")
        
        # Perform sync operations
        result = sync.full_sync()
        
        monitor.log_sync_complete("owner/repo", result)
        
    except RateLimitExceededError as e:
        monitor.log_error("rate_limit", e, {"remaining_requests": 0})
        # Implement backoff and retry
        
    except AuthenticationError as e:
        monitor.log_error("authentication", e)
        # Handle token refresh or user notification
        
    except SyncConflictError as e:
        monitor.log_error("conflict_resolution", e)
        # Queue for manual review
        
    except Exception as e:
        monitor.log_error("unexpected", e)
        # General error handling
```

## Data Integrity and Rollback

```python
class SyncBackupManager:
    def __init__(self, backup_path: str = "/Users/masa/Projects/claude-multiagent-pm/backups"):
        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, repository: str) -> str:
        """Create backup before sync operation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_path / f"github_sync_backup_{repository.replace('/', '_')}_{timestamp}.json"
        
        # Backup current state
        backup_data = {
            "timestamp": timestamp,
            "repository": repository,
            "github_issues": self._get_all_issues(repository),
            "claude_pm_tickets": self._get_all_tickets(),
            "sync_records": self._get_sync_records()
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        return str(backup_file)
    
    def rollback_sync(self, backup_file: str) -> bool:
        """Rollback sync operation using backup"""
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Implement rollback logic
        # This would involve:
        # 1. Restoring GitHub issues to previous state
        # 2. Restoring Claude PM ticket states
        # 3. Cleaning up sync records
        
        print(f"Rolling back sync using backup: {backup_file}")
        return True
```

## Conclusion

This comprehensive guide provides the foundation for implementing robust GitHub API integration with the Claude PM Framework. Key recommendations:

1. **Use fine-grained personal access tokens** with minimal required permissions
2. **Implement comprehensive rate limiting** with exponential backoff
3. **Start with unidirectional sync** (Claude PM -> GitHub) before attempting bidirectional
4. **Establish clear conflict resolution strategies** based on your team's workflow
5. **Implement thorough monitoring and backup systems** for data integrity
6. **Test with small batches** before full-scale deployment

The provided code examples offer a solid starting point for the engineer ops agent to build upon, with extensible patterns for error handling, monitoring, and conflict resolution.