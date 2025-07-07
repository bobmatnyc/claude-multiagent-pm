"""
GitHub API Utility Functions for Claude PM Framework

This module provides utility functions for GitHub API operations including
project management, GraphQL queries, and advanced issue operations.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests


class GitHubProjectManager:
    """Manage GitHub Projects V2 for epic tracking"""
    
    def __init__(self, client, owner: str):
        self.client = client
        self.owner = owner  # Organization or user
        self.logger = logging.getLogger(f"{__name__}.GitHubProjectManager")
    
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
            self.logger.error(f"Could not get owner ID for {self.owner}")
            return None
        
        variables = {
            "ownerId": owner_id,
            "title": title,
            "description": description
        }
        
        result = self._execute_graphql(mutation, variables)
        if result and 'data' in result and 'createProjectV2' in result['data']:
            self.logger.info(f"Created project: {title}")
            return result
        
        self.logger.error(f"Failed to create project: {title}")
        return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects for the owner"""
        
        if self.owner.startswith('@'):
            # User projects
            query = f"""
            query {{
              user(login: "{self.owner[1:]}") {{
                projectsV2(first: 50) {{
                  nodes {{
                    id
                    number
                    title
                    url
                    closed
                  }}
                }}
              }}
            }}
            """
        else:
            # Organization projects
            query = f"""
            query {{
              organization(login: "{self.owner}") {{
                projectsV2(first: 50) {{
                  nodes {{
                    id
                    number
                    title
                    url
                    closed
                  }}
                }}
              }}
            }}
            """
        
        result = self._execute_graphql(query)
        if result and 'data' in result:
            data = result['data']
            projects_data = data.get('user', data.get('organization', {}))
            return projects_data.get('projectsV2', {}).get('nodes', [])
        
        return []
    
    def find_project_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Find project by title"""
        projects = self.list_projects()
        for project in projects:
            if project['title'] == title:
                return project
        return None
    
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
        if result and 'data' in result and 'addProjectV2ItemById' in result['data']:
            self.logger.debug(f"Added issue {issue_id} to project {project_id}")
            return True
        
        self.logger.error(f"Failed to add issue {issue_id} to project {project_id}")
        return False
    
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
        try:
            response = self.client.make_request(
                "POST",
                "/graphql",
                json={
                    "query": query,
                    "variables": variables or {}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'errors' in result:
                    self.logger.error(f"GraphQL errors: {result['errors']}")
                    return None
                return result
            else:
                self.logger.error(f"GraphQL request failed: {response.status_code} - {response.text}")
        
        except Exception as e:
            self.logger.error(f"GraphQL request exception: {e}")
        
        return None


class EpicManager:
    """Manage epic creation and issue linking using GitHub Projects"""
    
    def __init__(self, project_manager: GitHubProjectManager, issue_manager):
        self.project_manager = project_manager
        self.issue_manager = issue_manager
        self.logger = logging.getLogger(f"{__name__}.EpicManager")
    
    def create_epic_structure(self, epic_name: str, epic_id: str, tickets: List) -> Dict[str, Any]:
        """Create epic as project with linked issues"""
        
        # Create project for epic
        project_title = f"Epic: {epic_name} ({epic_id})"
        epic_description = f"Epic tracking for {epic_name}. This project tracks all tickets related to {epic_id}."
        
        project = self.project_manager.create_project(project_title, epic_description)
        
        if not project:
            return {"success": False, "error": "Failed to create project"}
        
        project_data = project['data']['createProjectV2']['projectV2']
        project_id = project_data['id']
        
        # Create issues and add to project
        created_issues = []
        linked_issues = 0
        
        for ticket in tickets:
            # Check if issue already exists
            existing_issue = self.issue_manager.find_existing_issue(ticket.ticket_id)
            
            if existing_issue:
                # Add existing issue to project
                issue_node_id = existing_issue.get('node_id')
                if issue_node_id and self.project_manager.add_issue_to_project(project_id, issue_node_id):
                    linked_issues += 1
                    self.logger.info(f"Linked existing issue #{existing_issue['number']} to epic {epic_id}")
            else:
                # Create new issue
                issue = self.issue_manager.create_issue_from_ticket(ticket)
                if issue:
                    # Add to project
                    issue_node_id = issue.get('node_id')
                    if issue_node_id and self.project_manager.add_issue_to_project(project_id, issue_node_id):
                        linked_issues += 1
                        self.logger.info(f"Created and linked issue #{issue['number']} to epic {epic_id}")
                    
                    created_issues.append(issue)
        
        return {
            "success": True,
            "project": project_data,
            "created_issues": created_issues,
            "linked_issues": linked_issues,
            "epic_id": epic_id
        }
    
    def ensure_epic_projects(self, epic_definitions: Dict[str, str]) -> Dict[str, Any]:
        """Ensure all epic projects exist"""
        
        results = {}
        
        for epic_id, epic_name in epic_definitions.items():
            project_title = f"Epic: {epic_name} ({epic_id})"
            
            # Check if project already exists
            existing_project = self.project_manager.find_project_by_title(project_title)
            
            if existing_project:
                results[epic_id] = {
                    "status": "exists",
                    "project": existing_project
                }
                self.logger.info(f"Epic project already exists: {epic_id}")
            else:
                # Create new project
                project = self.project_manager.create_project(
                    project_title,
                    f"Epic tracking for {epic_name}"
                )
                
                if project:
                    results[epic_id] = {
                        "status": "created",
                        "project": project['data']['createProjectV2']['projectV2']
                    }
                    self.logger.info(f"Created epic project: {epic_id}")
                else:
                    results[epic_id] = {
                        "status": "failed",
                        "error": "Could not create project"
                    }
                    self.logger.error(f"Failed to create epic project: {epic_id}")
        
        return results


class GitHubSearchManager:
    """Advanced search operations for GitHub"""
    
    def __init__(self, client, repository: str):
        self.client = client
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.GitHubSearchManager")
    
    def search_issues_by_labels(self, labels: List[str], state: str = "all") -> List[Dict[str, Any]]:
        """Search issues by labels"""
        
        label_query = " ".join([f"label:{label}" for label in labels])
        query = f"repo:{self.repository} is:issue {label_query} state:{state}"
        
        return self._search_issues(query)
    
    def search_issues_by_milestone(self, milestone: str, state: str = "all") -> List[Dict[str, Any]]:
        """Search issues by milestone"""
        
        query = f'repo:{self.repository} is:issue milestone:"{milestone}" state:{state}'
        return self._search_issues(query)
    
    def search_issues_by_epic(self, epic_id: str) -> List[Dict[str, Any]]:
        """Search issues belonging to an epic"""
        
        query = f"repo:{self.repository} is:issue label:epic-{epic_id.lower()}"
        return self._search_issues(query)
    
    def find_orphaned_issues(self) -> List[Dict[str, Any]]:
        """Find Claude PM issues without proper labels"""
        
        # Find issues with claude-pm-sync label but missing other required labels
        query = f"repo:{self.repository} is:issue label:claude-pm-sync"
        issues = self._search_issues(query)
        
        orphaned = []
        
        for issue in issues:
            labels = [label['name'] for label in issue['labels']]
            
            # Check for required label types
            has_priority = any(label.startswith('priority-') for label in labels)
            has_type = any(label.startswith('type-') or label.startswith('milestone-') or label.startswith('epic-') for label in labels)
            
            if not has_priority or not has_type:
                orphaned.append(issue)
        
        return orphaned
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get statistics about synced issues"""
        
        # All Claude PM issues
        all_issues = self.search_issues_by_labels(["claude-pm-sync"])
        
        # Group by status
        open_issues = [issue for issue in all_issues if issue['state'] == 'open']
        closed_issues = [issue for issue in all_issues if issue['state'] == 'closed']
        
        # Group by priority
        priority_counts = {}
        for issue in all_issues:
            labels = [label['name'] for label in issue['labels']]
            priority_labels = [label for label in labels if label.startswith('priority-')]
            
            if priority_labels:
                priority = priority_labels[0].replace('priority-', '')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Group by milestone
        milestone_counts = {}
        for issue in all_issues:
            milestone = issue.get('milestone')
            if milestone:
                milestone_title = milestone['title']
                milestone_counts[milestone_title] = milestone_counts.get(milestone_title, 0) + 1
        
        return {
            "total_issues": len(all_issues),
            "open_issues": len(open_issues),
            "closed_issues": len(closed_issues),
            "priority_breakdown": priority_counts,
            "milestone_breakdown": milestone_counts,
            "orphaned_issues": len(self.find_orphaned_issues())
        }
    
    def _search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Execute issue search query"""
        
        try:
            response = self.client.make_request(
                "GET",
                "/search/issues",
                params={
                    "q": query,
                    "per_page": 100,
                    "sort": "created",
                    "order": "desc"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                self.logger.error(f"Search failed: {response.status_code} - {response.text}")
        
        except Exception as e:
            self.logger.error(f"Search exception: {e}")
        
        return []


class GitHubBatchManager:
    """Batch operations for efficient API usage"""
    
    def __init__(self, client, repository: str, batch_size: int = 50):
        self.client = client
        self.repository = repository
        self.batch_size = batch_size
        self.logger = logging.getLogger(f"{__name__}.GitHubBatchManager")
    
    def batch_create_issues(self, tickets: List, milestone_manager, delay_ms: int = 100) -> Dict[str, Any]:
        """Create multiple issues in batches with rate limiting"""
        
        total_tickets = len(tickets)
        created = 0
        errors = 0
        results = []
        
        self.logger.info(f"Starting batch creation of {total_tickets} issues")
        
        for i in range(0, total_tickets, self.batch_size):
            batch = tickets[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_tickets + self.batch_size - 1) // self.batch_size
            
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} tickets)")
            
            for ticket in batch:
                try:
                    # Get milestone number
                    milestone_number = milestone_manager.get_milestone_number(ticket.milestone)
                    
                    # Create issue
                    from github_sync import GitHubIssueManager
                    issue_manager = GitHubIssueManager(self.client, self.repository)
                    result = issue_manager.create_issue_from_ticket(ticket, milestone_number)
                    
                    if result:
                        created += 1
                        results.append({
                            "ticket_id": ticket.ticket_id,
                            "issue_number": result['number'],
                            "issue_url": result['html_url'],
                            "status": "created"
                        })
                        self.logger.debug(f"Created issue #{result['number']} for {ticket.ticket_id}")
                    else:
                        errors += 1
                        results.append({
                            "ticket_id": ticket.ticket_id,
                            "status": "failed",
                            "error": "API request failed"
                        })
                
                except Exception as e:
                    errors += 1
                    results.append({
                        "ticket_id": ticket.ticket_id,
                        "status": "error",
                        "error": str(e)
                    })
                    self.logger.error(f"Error creating issue for {ticket.ticket_id}: {e}")
                
                # Rate limiting delay
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
            
            # Longer delay between batches
            if i + self.batch_size < total_tickets:
                time.sleep(1.0)
        
        self.logger.info(f"Batch creation complete: {created} created, {errors} errors")
        
        return {
            "total_processed": total_tickets,
            "created": created,
            "errors": errors,
            "results": results
        }
    
    def batch_update_labels(self, issues: List[Dict], new_labels: List[str]) -> Dict[str, Any]:
        """Update labels on multiple issues"""
        
        updated = 0
        errors = 0
        
        for issue in issues:
            try:
                response = self.client.make_request(
                    "PATCH",
                    f"/repos/{self.repository}/issues/{issue['number']}",
                    json={"labels": new_labels}
                )
                
                if response.status_code == 200:
                    updated += 1
                    self.logger.debug(f"Updated labels for issue #{issue['number']}")
                else:
                    errors += 1
                    self.logger.error(f"Failed to update labels for issue #{issue['number']}: {response.status_code}")
            
            except Exception as e:
                errors += 1
                self.logger.error(f"Error updating labels for issue #{issue['number']}: {e}")
        
        return {"updated": updated, "errors": errors}


class SyncValidator:
    """Validate sync operations and data integrity"""
    
    def __init__(self, client, repository: str):
        self.client = client
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.SyncValidator")
    
    def validate_sync_integrity(self, sync_records: Dict) -> Dict[str, Any]:
        """Validate integrity of sync records against GitHub"""
        
        validation_results = {
            "valid_records": 0,
            "invalid_records": 0,
            "missing_issues": [],
            "mismatched_issues": [],
            "orphaned_issues": []
        }
        
        # Check each sync record
        for ticket_id, record in sync_records.items():
            try:
                # Fetch the GitHub issue
                response = self.client.make_request(
                    "GET",
                    f"/repos/{self.repository}/issues/{record.github_issue_number}"
                )
                
                if response.status_code == 200:
                    issue = response.json()
                    
                    # Validate ticket ID in title
                    if f"[{ticket_id}]" in issue['title']:
                        validation_results["valid_records"] += 1
                    else:
                        validation_results["invalid_records"] += 1
                        validation_results["mismatched_issues"].append({
                            "ticket_id": ticket_id,
                            "issue_number": record.github_issue_number,
                            "expected_title_contains": f"[{ticket_id}]",
                            "actual_title": issue['title']
                        })
                
                elif response.status_code == 404:
                    validation_results["invalid_records"] += 1
                    validation_results["missing_issues"].append({
                        "ticket_id": ticket_id,
                        "issue_number": record.github_issue_number
                    })
                
            except Exception as e:
                self.logger.error(f"Error validating record for {ticket_id}: {e}")
                validation_results["invalid_records"] += 1
        
        # Find orphaned issues (GitHub issues without sync records)
        search_manager = GitHubSearchManager(self.client, self.repository)
        all_claude_pm_issues = search_manager.search_issues_by_labels(["claude-pm-sync"])
        
        synced_issue_numbers = {record.github_issue_number for record in sync_records.values()}
        
        for issue in all_claude_pm_issues:
            if issue['number'] not in synced_issue_numbers:
                validation_results["orphaned_issues"].append({
                    "issue_number": issue['number'],
                    "title": issue['title'],
                    "url": issue['html_url']
                })
        
        self.logger.info(f"Validation complete: {validation_results['valid_records']} valid, "
                        f"{validation_results['invalid_records']} invalid, "
                        f"{len(validation_results['orphaned_issues'])} orphaned")
        
        return validation_results
    
    def validate_ticket_format(self, ticket) -> List[str]:
        """Validate individual ticket format"""
        
        errors = []
        
        # Required fields
        required_fields = ['ticket_id', 'title', 'description', 'milestone', 'priority', 'status']
        for field in required_fields:
            if not getattr(ticket, field, None):
                errors.append(f"Missing required field: {field}")
        
        # Validate ticket ID format
        if ticket.ticket_id and not re.match(r'^[A-Z]+-\d+$', ticket.ticket_id):
            errors.append(f"Invalid ticket ID format: {ticket.ticket_id}")
        
        # Validate priority
        valid_priorities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        if ticket.priority and ticket.priority not in valid_priorities:
            errors.append(f"Invalid priority: {ticket.priority}")
        
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if ticket.status and ticket.status not in valid_statuses:
            errors.append(f"Invalid status: {ticket.status}")
        
        # Validate story points
        if ticket.story_points and (not isinstance(ticket.story_points, int) or ticket.story_points < 0):
            errors.append(f"Invalid story points: {ticket.story_points}")
        
        return errors
    
    def generate_sync_report(self, sync_results: Dict) -> str:
        """Generate comprehensive sync report"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_lines = [
            "# Claude PM to GitHub Sync Report",
            f"Generated: {timestamp}",
            f"Repository: {self.repository}",
            "",
            "## Summary",
            f"- Total tickets processed: {sync_results.get('total_tickets', 0)}",
            f"- Issues created: {sync_results.get('created', 0)}",
            f"- Issues updated: {sync_results.get('updated', 0)}",
            f"- Issues skipped: {sync_results.get('skipped', 0)}",
            f"- Errors: {sync_results.get('errors', 0)}",
            ""
        ]
        
        # Add error details if any
        if sync_results.get('errors', 0) > 0:
            report_lines.extend([
                "## Errors",
                "The following issues occurred during sync:",
                ""
            ])
            
            # Add specific error details here if available in sync_results
        
        # Add success details
        if sync_results.get('created', 0) > 0 or sync_results.get('updated', 0) > 0:
            report_lines.extend([
                "## Successfully Synced Issues",
                "Issues that were successfully created or updated:",
                ""
            ])
        
        return "\n".join(report_lines)


# Epic definitions for the Claude PM Framework
CLAUDE_PM_EPICS = {
    "FEP-001": "Framework Infrastructure Setup",
    "FEP-002": "Multi-Agent Coordination Patterns", 
    "FEP-003": "Advanced Workflow Automation",
    "FEP-004": "Enterprise Orchestration Patterns",
    "FEP-007": "Claude Max + mem0AI Enhanced Architecture",
    "FEP-008": "Memory-Augmented Agent Ecosystem",
    "FEP-009": "Intelligent Task Decomposition System",
    "FEP-010": "Continuous Learning Engine",
    "FEP-011": "LangGraph State-Based Workflow Orchestration"
}


def setup_epic_projects(client, owner: str, repository: str) -> Dict[str, Any]:
    """Setup all epic projects for Claude PM Framework"""
    
    project_manager = GitHubProjectManager(client, owner)
    epic_manager = EpicManager(project_manager, None)
    
    return epic_manager.ensure_epic_projects(CLAUDE_PM_EPICS)


def validate_github_permissions(client, repository: str) -> Dict[str, bool]:
    """Validate that the GitHub token has required permissions"""
    
    logger = logging.getLogger(f"{__name__}.validate_permissions")
    permissions = {}
    
    # Test repository access
    try:
        response = client.make_request("GET", f"/repos/{repository}")
        permissions["repository_access"] = response.status_code == 200
    except Exception as e:
        logger.error(f"Repository access test failed: {e}")
        permissions["repository_access"] = False
    
    # Test issues permission
    try:
        response = client.make_request("GET", f"/repos/{repository}/issues", params={"per_page": 1})
        permissions["issues"] = response.status_code == 200
    except Exception as e:
        logger.error(f"Issues permission test failed: {e}")
        permissions["issues"] = False
    
    # Test labels permission
    try:
        response = client.make_request("GET", f"/repos/{repository}/labels", params={"per_page": 1})
        permissions["labels"] = response.status_code == 200
    except Exception as e:
        logger.error(f"Labels permission test failed: {e}")
        permissions["labels"] = False
    
    # Test milestones permission
    try:
        response = client.make_request("GET", f"/repos/{repository}/milestones", params={"per_page": 1})
        permissions["milestones"] = response.status_code == 200
    except Exception as e:
        logger.error(f"Milestones permission test failed: {e}")
        permissions["milestones"] = False
    
    return permissions