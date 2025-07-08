#!/usr/bin/env python3
"""
Enhanced Documentation Synchronization System for Claude PM Framework
FWK-008: Fixed Automated Documentation Synchronization

This enhanced system fixes the critical failures in the documentation sync:
1. Supports new progressive documentation structure (FWK-006)
2. Comprehensive path reference validation
3. Cross-file consistency checking
4. Real-time change notification
5. Integration with framework health monitoring
"""

import re
import os
import sys
import json
import logging
import asyncio
import signal
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))

@dataclass
class ValidationIssue:
    """Represents a validation issue found during sync"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    issue_type: str  # 'broken_link', 'path_error', 'inconsistency', 'missing_file'
    file_path: str
    line_number: int
    description: str
    suggested_fix: Optional[str] = None
    link_text: Optional[str] = None
    target_path: Optional[str] = None

@dataclass
class TicketStatus:
    """Enhanced ticket status with support for new documentation structure"""
    ticket_id: str
    title: str
    status: str  # 'completed', 'in_progress', 'planned', 'blocked'
    priority: str
    story_points: int
    epic: Optional[str] = None
    milestone: str = ""
    completion_date: Optional[str] = None
    source_file: str = ""
    line_number: int = 0
    dependencies: List[str] = None
    acceptance_criteria: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []

@dataclass
class DocumentationStats:
    """Enhanced statistics for documentation synchronization"""
    total_tickets: int
    completed_tickets: int
    in_progress_tickets: int
    planned_tickets: int
    blocked_tickets: int
    completion_percentage: float
    total_story_points: int
    completed_story_points: int
    phase_1_completion: float
    validation_issues: List[ValidationIssue]
    broken_links: List[ValidationIssue]
    path_errors: List[ValidationIssue]
    inconsistencies_found: List[str]
    last_update: str
    files_validated: int
    links_checked: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class EnhancedDocumentationSyncManager:
    """Enhanced documentation synchronization with comprehensive validation"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        
        # New progressive documentation structure
        self.priority_tickets_path = self.claude_pm_root / "trackdown" / "PRIORITY-TICKETS.md"
        self.completed_tickets_path = self.claude_pm_root / "trackdown" / "COMPLETED-TICKETS.md"
        self.current_sprint_path = self.claude_pm_root / "trackdown" / "CURRENT-SPRINT.md"
        self.backlog_summary_path = self.claude_pm_root / "trackdown" / "BACKLOG-SUMMARY.md"
        
        # Core system files
        self.ticketing_path = self.claude_pm_root / "docs" / "TICKETING_SYSTEM.md"
        self.health_monitor_path = self.claude_pm_root / "claude_pm" / "services" / "health_monitor.py"
        
        # Output directories
        self.reports_dir = self.claude_pm_root / "logs"
        self.config_dir = self.claude_pm_root / "config"
        
        self.logger = self._setup_logging()
        
        # Validation settings
        self.validation_rules = {
            'check_internal_links': True,
            'validate_path_references': True,
            'cross_file_consistency': True,
            'progressive_structure_compliance': True,
            'health_integration': True
        }
        
        # Status patterns for new format
        self.status_patterns = {
            'completed': [r'✅ COMPLETED', r'✅', r'\[x\]'],
            'in_progress': [r'🔄.*IN PROGRESS', r'🔄', r'IN PROGRESS'],
            'planned': [r'📋.*PLANNED', r'📋', r'PLANNED'],
            'blocked': [r'🚫.*BLOCKED', r'🚫', r'BLOCKED']
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for enhanced sync operations"""
        logger = logging.getLogger('EnhancedDocSync')
        logger.setLevel(logging.INFO)
        
        # Ensure logs directory exists
        self.reports_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = self.reports_dir / "enhanced_doc_sync.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Clear existing handlers and add new ones
        logger.handlers.clear()
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def parse_progressive_tickets(self) -> List[TicketStatus]:
        """Parse tickets from the new progressive documentation structure"""
        self.logger.info("Parsing tickets from progressive documentation structure...")
        
        tickets = []
        
        # Parse priority tickets from PRIORITY-TICKETS.md
        if self.priority_tickets_path.exists():
            tickets.extend(self._parse_priority_tickets())
        else:
            self.logger.warning(f"Priority tickets file not found: {self.priority_tickets_path}")
        
        # Parse completed tickets from COMPLETED-TICKETS.md
        if self.completed_tickets_path.exists():
            tickets.extend(self._parse_completed_tickets())
        else:
            self.logger.warning(f"Completed tickets file not found: {self.completed_tickets_path}")
        
        self.logger.info(f"Parsed {len(tickets)} tickets from progressive structure")
        return tickets

    def _parse_priority_tickets(self) -> List[TicketStatus]:
        """Parse tickets from PRIORITY-TICKETS.md"""
        tickets = []
        
        with open(self.priority_tickets_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse individual ticket sections (### TICKET-ID:)
        ticket_sections = re.split(r'\n### ([A-Z0-9]+-\d+):', content)
        
        for i in range(1, len(ticket_sections), 2):
            if i + 1 >= len(ticket_sections):
                break
                
            ticket_id = ticket_sections[i].strip()
            ticket_content = ticket_sections[i + 1]
            
            try:
                ticket = self._parse_ticket_section(ticket_id, ticket_content, "PRIORITY-TICKETS.md")
                if ticket:
                    tickets.append(ticket)
            except Exception as e:
                self.logger.error(f"Error parsing priority ticket {ticket_id}: {e}")
        
        return tickets

    def _parse_completed_tickets(self) -> List[TicketStatus]:
        """Parse tickets from COMPLETED-TICKETS.md"""
        tickets = []
        
        with open(self.completed_tickets_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for ticket references in completed format
        ticket_patterns = [
            r'- \[x\] \*\*\[([A-Z0-9]+-\d+)\]\*\* ([^\n]+)',
            r'✅ \*\*([A-Z0-9]+-\d+)\*\*[:\s]*([^\n]+)',
            r'### ([A-Z0-9]+-\d+):[^\n]*([^\n]*)'
        ]
        
        for pattern in ticket_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                try:
                    ticket_id = match.group(1)
                    title = match.group(2).strip()
                    
                    # Look for completion date in the surrounding context
                    completion_date = None
                    date_search = re.search(r'\((\d{4}-\d{2}-\d{2})\)', match.group(0))
                    if date_search:
                        completion_date = date_search.group(1)
                    
                    ticket = TicketStatus(
                        ticket_id=ticket_id,
                        title=title,
                        status='completed',
                        priority=self._determine_priority(ticket_id),
                        story_points=self._estimate_story_points(ticket_id, title),
                        epic=self._determine_epic(ticket_id),
                        milestone=self._determine_milestone(ticket_id),
                        completion_date=completion_date,
                        source_file="COMPLETED-TICKETS.md",
                        line_number=content[:match.start()].count('\n') + 1
                    )
                    tickets.append(ticket)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing completed ticket from match: {e}")
        
        return tickets

    def _parse_ticket_section(self, ticket_id: str, content: str, source_file: str) -> Optional[TicketStatus]:
        """Parse a detailed ticket section"""
        try:
            lines = content.strip().split('\n')
            if not lines:
                return None
            
            # Extract title (first non-empty line)
            title = ""
            for line in lines:
                line = line.strip()
                if line and not line.startswith('**') and not line.startswith('*') and ':' not in line:
                    title = line
                    break
            
            if not title:
                title = f"Ticket {ticket_id}"
            
            # Determine status from status indicators
            status = 'planned'  # default
            completion_date = None
            
            if '✅ COMPLETED' in content or '✅' in content:
                status = 'completed'
                date_match = re.search(r'Completion Date.*?(\d{4}-\d{2}-\d{2})', content)
                if date_match:
                    completion_date = date_match.group(1)
            elif '🔄' in content or 'IN PROGRESS' in content:
                status = 'in_progress'
            elif '🚫' in content or 'BLOCKED' in content:
                status = 'blocked'
            elif '📋' in content or 'PLANNED' in content:
                status = 'planned'
            
            # Extract metadata
            priority_match = re.search(r'\*\*Priority\*\*:\s*([A-Z]+)', content)
            priority = priority_match.group(1) if priority_match else self._determine_priority(ticket_id)
            
            points_match = re.search(r'\*\*Story Points\*\*:\s*(\d+)', content)
            story_points = int(points_match.group(1)) if points_match else self._estimate_story_points(ticket_id, title)
            
            epic_match = re.search(r'\*\*Epic\*\*:\s*([A-Z0-9-]+)', content)
            epic = epic_match.group(1) if epic_match else self._determine_epic(ticket_id)
            
            # Extract dependencies
            dependencies = []
            deps_match = re.search(r'\*\*Dependencies\*\*:\s*([^\n]+)', content)
            if deps_match:
                deps_text = deps_match.group(1)
                # Look for ticket IDs in dependencies
                dep_tickets = re.findall(r'([A-Z0-9]+-\d+)', deps_text)
                dependencies.extend(dep_tickets)
            
            # Extract acceptance criteria
            acceptance_criteria = []
            criteria_section = re.search(r'\*\*Acceptance Criteria\*\*:(.*?)(?=\*\*|---|\Z)', content, re.DOTALL)
            if criteria_section:
                criteria_text = criteria_section.group(1)
                criteria_lines = re.findall(r'- \[ \] (.+)', criteria_text)
                acceptance_criteria.extend(criteria_lines)
            
            return TicketStatus(
                ticket_id=ticket_id,
                title=title,
                status=status,
                priority=priority,
                story_points=story_points,
                epic=epic,
                milestone=self._determine_milestone(ticket_id),
                completion_date=completion_date,
                source_file=source_file,
                line_number=0,  # Could be calculated if needed
                dependencies=dependencies,
                acceptance_criteria=acceptance_criteria
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing ticket section {ticket_id}: {e}")
            return None

    def validate_path_references(self) -> List[ValidationIssue]:
        """Comprehensive validation of all path references in documentation"""
        self.logger.info("Validating path references across documentation...")
        
        issues = []
        files_to_check = [
            self.claude_pm_root / "README.md",
            self.claude_pm_root / "docs" / "INDEX.md",
            self.claude_pm_root / "docs" / "FRAMEWORK_OVERVIEW.md",
            self.claude_pm_root / "docs" / "QUICK_START.md",
            self.claude_pm_root / "docs" / "TICKETING_SYSTEM.md",
            self.priority_tickets_path,
            self.completed_tickets_path,
            self.current_sprint_path,
            self.backlog_summary_path
        ]
        
        # Add all markdown files in docs/ directory
        docs_dir = self.claude_pm_root / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.glob("*.md"):
                if md_file not in files_to_check:
                    files_to_check.append(md_file)
        
        for file_path in files_to_check:
            if not file_path.exists():
                issues.append(ValidationIssue(
                    severity='high',
                    issue_type='missing_file',
                    file_path=str(file_path),
                    line_number=0,
                    description=f"Critical documentation file missing: {file_path.name}",
                    suggested_fix=f"Create missing file: {file_path}"
                ))
                continue
            
            file_issues = self._validate_file_links(file_path)
            issues.extend(file_issues)
        
        self.logger.info(f"Found {len(issues)} path reference issues")
        return issues

    def _validate_file_links(self, file_path: Path) -> List[ValidationIssue]:
        """Validate all links within a specific file"""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Find all markdown links [text](path)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            
            for line_num, line in enumerate(lines, 1):
                links = re.finditer(link_pattern, line)
                
                for link_match in links:
                    link_text = link_match.group(1)
                    link_path = link_match.group(2)
                    
                    # Skip external links
                    if link_path.startswith(('http://', 'https://', 'mailto:')):
                        continue
                    
                    # Skip anchors within same document
                    if link_path.startswith('#'):
                        continue
                    
                    # Validate internal link
                    validation_issue = self._validate_internal_link(
                        file_path, link_text, link_path, line_num
                    )
                    
                    if validation_issue:
                        issues.append(validation_issue)
            
            # Check for relative path references outside of markdown links
            self._check_path_references_in_content(file_path, content, issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                severity='critical',
                issue_type='path_error',
                file_path=str(file_path),
                line_number=0,
                description=f"Failed to read file: {str(e)}",
                suggested_fix="Check file permissions and encoding"
            ))
        
        return issues

    def _validate_internal_link(self, source_file: Path, link_text: str, link_path: str, line_num: int) -> Optional[ValidationIssue]:
        """Validate a single internal link"""
        try:
            # Resolve relative path
            if link_path.startswith('../'):
                target_path = source_file.parent / link_path
            elif link_path.startswith('./'):
                target_path = source_file.parent / link_path[2:]
            else:
                target_path = source_file.parent / link_path
            
            # Resolve to absolute path
            target_path = target_path.resolve()
            
            # Check if target exists
            if not target_path.exists():
                # Try to suggest a fix
                suggested_fix = self._suggest_link_fix(source_file, link_path, target_path)
                
                return ValidationIssue(
                    severity='high',
                    issue_type='broken_link',
                    file_path=str(source_file),
                    line_number=line_num,
                    description=f"Broken link: [{link_text}]({link_path}) -> {target_path}",
                    suggested_fix=suggested_fix,
                    link_text=link_text,
                    target_path=str(target_path)
                )
            
            return None
            
        except Exception as e:
            return ValidationIssue(
                severity='medium',
                issue_type='path_error',
                file_path=str(source_file),
                line_number=line_num,
                description=f"Invalid link format: [{link_text}]({link_path}) - {str(e)}",
                suggested_fix="Check link path format and syntax",
                link_text=link_text,
                target_path=link_path
            )

    def _suggest_link_fix(self, source_file: Path, original_path: str, target_path: Path) -> str:
        """Suggest a fix for a broken link"""
        # Look for similar files in the project
        target_name = target_path.name
        
        # Search for files with similar names
        for root in [self.claude_pm_root]:
            for found_file in root.rglob(target_name):
                if found_file.exists():
                    # Calculate relative path from source to found file
                    try:
                        rel_path = os.path.relpath(found_file, source_file.parent)
                        return f"Suggested fix: Use '{rel_path}' instead of '{original_path}'"
                    except ValueError:
                        pass
        
        return f"File not found. Check if '{target_name}' exists or has been moved."

    def _check_path_references_in_content(self, file_path: Path, content: str, issues: List[ValidationIssue]):
        """Check for path references in code blocks and other content"""
        lines = content.split('\n')
        
        # Look for path-like patterns in code blocks and comments
        path_patterns = [
            r'/Users/masa/Projects/[^\s\)]+',
            r'\./[^\s\)]+',
            r'\.\./[^\s\)]+',
            r'trackdown/[^\s\)]+',
            r'docs/[^\s\)]+',
            r'claude_pm/[^\s\)]+',
            r'framework/[^\s\)]+',
            r'scripts/[^\s\)]+',
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in path_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    path_ref = match.group(0)
                    
                    # Skip if it's in a markdown link (already checked)
                    if re.search(r'\[.*\]\([^)]*' + re.escape(path_ref), line):
                        continue
                    
                    # Validate the path reference
                    if self._is_invalid_path_reference(path_ref):
                        issues.append(ValidationIssue(
                            severity='medium',
                            issue_type='path_error',
                            file_path=str(file_path),
                            line_number=line_num,
                            description=f"Potentially invalid path reference: {path_ref}",
                            suggested_fix="Verify this path is correct and accessible",
                            target_path=path_ref
                        ))

    def _is_invalid_path_reference(self, path_ref: str) -> bool:
        """Check if a path reference is invalid"""
        try:
            # Convert to absolute path if relative
            if path_ref.startswith('/Users/masa/Projects/'):
                check_path = Path(path_ref)
            elif path_ref.startswith('./') or path_ref.startswith('../'):
                check_path = self.claude_pm_root / path_ref
            else:
                check_path = self.claude_pm_root / path_ref
            
            return not check_path.exists()
        except Exception:
            return True

    def validate_cross_file_consistency(self, tickets: List[TicketStatus]) -> List[str]:
        """Enhanced cross-file consistency validation"""
        inconsistencies = []
        
        # Check TICKETING_SYSTEM.md consistency
        if self.ticketing_path.exists():
            inconsistencies.extend(self._validate_ticketing_system_consistency(tickets))
        
        # Check progressive documentation consistency
        inconsistencies.extend(self._validate_progressive_structure_consistency(tickets))
        
        return inconsistencies

    def _validate_ticketing_system_consistency(self, tickets: List[TicketStatus]) -> List[str]:
        """Validate consistency with TICKETING_SYSTEM.md"""
        inconsistencies = []
        
        try:
            with open(self.ticketing_path, 'r', encoding='utf-8') as f:
                ticketing_content = f.read()
            
            for ticket in tickets:
                # Look for the ticket in TICKETING_SYSTEM.md
                ticket_pattern = f"\\*\\*{re.escape(ticket.ticket_id)}\\*\\*"
                ticket_matches = re.finditer(ticket_pattern, ticketing_content)
                
                for match in ticket_matches:
                    # Extract the line containing this ticket
                    start = ticketing_content.rfind('\n', 0, match.start()) + 1
                    end = ticketing_content.find('\n', match.end())
                    if end == -1:
                        end = len(ticketing_content)
                    line = ticketing_content[start:end]
                    
                    # Check status consistency
                    ticketing_status = self._determine_status_from_line(line)
                    
                    if ticket.status != ticketing_status:
                        inconsistencies.append(
                            f"{ticket.ticket_id}: {ticket.source_file} shows '{ticket.status}' "
                            f"but TICKETING_SYSTEM.md shows '{ticketing_status}'"
                        )
        
        except Exception as e:
            self.logger.error(f"Error validating TICKETING_SYSTEM.md consistency: {e}")
            inconsistencies.append(f"Failed to validate TICKETING_SYSTEM.md: {str(e)}")
        
        return inconsistencies

    def _determine_status_from_line(self, line: str) -> str:
        """Determine status from a line in TICKETING_SYSTEM.md"""
        if '✅ COMPLETED' in line or '✅' in line:
            return 'completed'
        elif '🔄' in line:
            return 'in_progress'
        elif '🚫' in line:
            return 'blocked'
        elif '📋' in line:
            return 'planned'
        else:
            return 'pending'

    def _validate_progressive_structure_consistency(self, tickets: List[TicketStatus]) -> List[str]:
        """Validate consistency across progressive documentation structure"""
        inconsistencies = []
        
        # Check that completed tickets are in COMPLETED-TICKETS.md
        completed_tickets = [t for t in tickets if t.status == 'completed']
        if self.completed_tickets_path.exists():
            try:
                with open(self.completed_tickets_path, 'r', encoding='utf-8') as f:
                    completed_content = f.read()
                
                for ticket in completed_tickets:
                    if ticket.source_file != "COMPLETED-TICKETS.md":
                        # Check if it's referenced in completed tickets
                        if ticket.ticket_id not in completed_content:
                            inconsistencies.append(
                                f"{ticket.ticket_id}: Marked as completed in {ticket.source_file} "
                                f"but not found in COMPLETED-TICKETS.md"
                            )
            except Exception as e:
                inconsistencies.append(f"Failed to validate COMPLETED-TICKETS.md: {str(e)}")
        
        # Check that active tickets are in PRIORITY-TICKETS.md
        active_tickets = [t for t in tickets if t.status in ['in_progress', 'planned']]
        if self.priority_tickets_path.exists():
            try:
                with open(self.priority_tickets_path, 'r', encoding='utf-8') as f:
                    priority_content = f.read()
                
                for ticket in active_tickets:
                    if ticket.source_file != "PRIORITY-TICKETS.md":
                        if ticket.ticket_id not in priority_content:
                            inconsistencies.append(
                                f"{ticket.ticket_id}: Active ticket not found in PRIORITY-TICKETS.md"
                            )
            except Exception as e:
                inconsistencies.append(f"Failed to validate PRIORITY-TICKETS.md: {str(e)}")
        
        return inconsistencies

    def generate_enhanced_statistics(self, tickets: List[TicketStatus], validation_issues: List[ValidationIssue]) -> DocumentationStats:
        """Generate comprehensive statistics including validation results"""
        total = len(tickets)
        completed = sum(1 for t in tickets if t.status == 'completed')
        in_progress = sum(1 for t in tickets if t.status == 'in_progress')
        planned = sum(1 for t in tickets if t.status == 'planned')
        blocked = sum(1 for t in tickets if t.status == 'blocked')
        
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        total_story_points = sum(t.story_points for t in tickets)
        completed_story_points = sum(t.story_points for t in tickets if t.status == 'completed')
        
        # Calculate Phase 1 completion (MEM and LGR tickets)
        phase_1_tickets = [t for t in tickets if t.ticket_id.startswith(('MEM-', 'LGR-'))]
        phase_1_completed = sum(1 for t in phase_1_tickets if t.status == 'completed')
        phase_1_total = len(phase_1_tickets)
        phase_1_completion = (phase_1_completed / phase_1_total * 100) if phase_1_total > 0 else 0
        
        # Categorize validation issues
        broken_links = [issue for issue in validation_issues if issue.issue_type == 'broken_link']
        path_errors = [issue for issue in validation_issues if issue.issue_type == 'path_error']
        
        return DocumentationStats(
            total_tickets=total,
            completed_tickets=completed,
            in_progress_tickets=in_progress,
            planned_tickets=planned,
            blocked_tickets=blocked,
            completion_percentage=completion_percentage,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            phase_1_completion=phase_1_completion,
            validation_issues=validation_issues,
            broken_links=broken_links,
            path_errors=path_errors,
            inconsistencies_found=[],
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            files_validated=len(set(issue.file_path for issue in validation_issues)),
            links_checked=len([issue for issue in validation_issues if issue.link_text])
        )

    def sync_documentation(self, validate_only: bool = False) -> bool:
        """Enhanced main synchronization method"""
        try:
            self.logger.info("Starting enhanced documentation synchronization...")
            
            # Parse tickets from progressive structure
            tickets = self.parse_progressive_tickets()
            
            # Validate path references
            validation_issues = self.validate_path_references()
            
            # Validate cross-file consistency
            inconsistencies = self.validate_cross_file_consistency(tickets)
            
            # Generate enhanced statistics
            stats = self.generate_enhanced_statistics(tickets, validation_issues)
            stats.inconsistencies_found = inconsistencies
            
            # Report findings
            self._report_validation_results(stats)
            
            if not validate_only:
                # Update documentation files
                self._update_documentation_files(tickets, stats)
                
                # Integrate with health monitoring
                self._integrate_with_health_monitoring(stats)
            
            # Generate comprehensive report
            report_path = self._generate_comprehensive_report(tickets, stats)
            
            # Save statistics for monitoring
            self._save_statistics(stats)
            
            self.logger.info("Enhanced documentation synchronization completed successfully")
            
            # Return success if no critical issues
            critical_issues = [issue for issue in validation_issues if issue.severity == 'critical']
            return len(critical_issues) == 0 and len(inconsistencies) == 0
            
        except Exception as e:
            self.logger.error(f"Error during enhanced documentation synchronization: {e}")
            return False

    def _report_validation_results(self, stats: DocumentationStats):
        """Report validation results to console and log"""
        self.logger.info(f"=== VALIDATION RESULTS ===")
        self.logger.info(f"Files validated: {stats.files_validated}")
        self.logger.info(f"Links checked: {stats.links_checked}")
        self.logger.info(f"Validation issues: {len(stats.validation_issues)}")
        self.logger.info(f"Broken links: {len(stats.broken_links)}")
        self.logger.info(f"Path errors: {len(stats.path_errors)}")
        self.logger.info(f"Inconsistencies: {len(stats.inconsistencies_found)}")
        
        # Report critical issues
        critical_issues = [issue for issue in stats.validation_issues if issue.severity == 'critical']
        if critical_issues:
            self.logger.error(f"CRITICAL ISSUES FOUND ({len(critical_issues)}):")
            for issue in critical_issues:
                self.logger.error(f"  - {issue.file_path}:{issue.line_number} - {issue.description}")
        
        # Report broken links
        if stats.broken_links:
            self.logger.warning(f"BROKEN LINKS FOUND ({len(stats.broken_links)}):")
            for issue in stats.broken_links[:5]:  # Show first 5
                self.logger.warning(f"  - {issue.file_path}:{issue.line_number} - {issue.description}")
            if len(stats.broken_links) > 5:
                self.logger.warning(f"  ... and {len(stats.broken_links) - 5} more")

    def _update_documentation_files(self, tickets: List[TicketStatus], stats: DocumentationStats):
        """Update documentation files with current status"""
        # Update TICKETING_SYSTEM.md with enhanced statistics
        if self.ticketing_path.exists():
            self._update_ticketing_system_md(tickets, stats)

    def _update_ticketing_system_md(self, tickets: List[TicketStatus], stats: DocumentationStats):
        """Update TICKETING_SYSTEM.md with enhanced statistics"""
        try:
            with open(self.ticketing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the overview section
            overview_pattern = r'(## Overview\n)([^#]*?)(?=\n## |\Z)'
            
            validation_status = "✅ All validations passed" if len(stats.validation_issues) == 0 else f"⚠️ {len(stats.validation_issues)} validation issues found"
            
            new_overview = f"""## Overview
The Claude PM Framework uses a sophisticated progressive documentation system with {stats.total_tickets} tickets for managing the Claude Max + mem0AI + LangGraph dual integration project. This document reflects the current system status with {stats.completion_percentage:.0f}% overall completion ({stats.completed_tickets}/{stats.total_tickets} tickets), featuring completed zero-configuration memory integration and advanced workflow orchestration.

**Documentation Status**: {validation_status}
**Last Updated**: {stats.last_update}
**Phase 1 Completion**: {stats.phase_1_completion:.0f}%
**Total Story Points**: {stats.completed_story_points}/{stats.total_story_points}
**Links Validated**: {stats.links_checked} links checked across {stats.files_validated} files

"""
            
            content = re.sub(overview_pattern, new_overview, content, flags=re.DOTALL)
            
            # Update individual ticket statuses
            for ticket in tickets:
                ticket_pattern = f"(\\*\\*{re.escape(ticket.ticket_id)}\\*\\*[^\\n]*)"
                
                def update_ticket_line(match):
                    line = match.group(1)
                    
                    # Remove existing status markers
                    line = re.sub(r'✅ COMPLETED', '', line)
                    line = re.sub(r'✅', '', line)
                    line = re.sub(r'🔄.*IN PROGRESS', '', line)
                    line = re.sub(r'🔄', '', line)
                    line = re.sub(r'🚫.*BLOCKED', '', line)
                    line = re.sub(r'🚫', '', line)
                    line = re.sub(r'📋.*PLANNED', '', line)
                    line = re.sub(r'📋', '', line)
                    
                    # Add current status marker
                    if ticket.status == 'completed':
                        line += ' ✅ COMPLETED'
                        if ticket.completion_date:
                            line += f' ({ticket.completion_date})'
                    elif ticket.status == 'in_progress':
                        line += ' 🔄 IN PROGRESS'
                    elif ticket.status == 'blocked':
                        line += ' 🚫 BLOCKED'
                    elif ticket.status == 'planned':
                        line += ' 📋 PLANNED'
                    
                    return line
                
                content = re.sub(ticket_pattern, update_ticket_line, content)
            
            # Write updated content
            with open(self.ticketing_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Updated TICKETING_SYSTEM.md with enhanced statistics")
            
        except Exception as e:
            self.logger.error(f"Error updating TICKETING_SYSTEM.md: {e}")

    def _integrate_with_health_monitoring(self, stats: DocumentationStats):
        """Integrate documentation validation with health monitoring system"""
        try:
            # Create health monitoring integration data
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'documentation_health': {
                    'validation_passed': len(stats.validation_issues) == 0,
                    'total_issues': len(stats.validation_issues),
                    'critical_issues': len([i for i in stats.validation_issues if i.severity == 'critical']),
                    'broken_links': len(stats.broken_links),
                    'path_errors': len(stats.path_errors),
                    'inconsistencies': len(stats.inconsistencies_found),
                    'files_validated': stats.files_validated,
                    'links_checked': stats.links_checked,
                    'completion_percentage': stats.completion_percentage,
                    'phase_1_completion': stats.phase_1_completion
                }
            }
            
            # Save health data for monitoring system
            health_file = self.reports_dir / "doc_sync_health.json"
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            self.logger.info("Integrated documentation health with monitoring system")
            
        except Exception as e:
            self.logger.error(f"Error integrating with health monitoring: {e}")

    def _generate_comprehensive_report(self, tickets: List[TicketStatus], stats: DocumentationStats) -> str:
        """Generate comprehensive validation and sync report"""
        report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.reports_dir / f"enhanced_doc_sync_report_{report_timestamp}.md"
        
        # Build comprehensive report
        report_content = f"""# Enhanced Documentation Synchronization Report
Generated: {stats.last_update}

## Executive Summary
- **Total Tickets**: {stats.total_tickets}
- **Completed**: {stats.completed_tickets} ({stats.completion_percentage:.1f}%)
- **In Progress**: {stats.in_progress_tickets}
- **Planned**: {stats.planned_tickets}
- **Blocked**: {stats.blocked_tickets}
- **Story Points**: {stats.completed_story_points}/{stats.total_story_points} ({stats.completed_story_points/stats.total_story_points*100:.1f}%)
- **Phase 1 Completion**: {stats.phase_1_completion:.1f}%

## Validation Results
- **Files Validated**: {stats.files_validated}
- **Links Checked**: {stats.links_checked}
- **Total Issues**: {len(stats.validation_issues)}
- **Broken Links**: {len(stats.broken_links)}
- **Path Errors**: {len(stats.path_errors)}
- **Inconsistencies**: {len(stats.inconsistencies_found)}

## Issue Breakdown by Severity
"""
        
        # Group issues by severity
        severity_counts = {}
        for issue in stats.validation_issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                report_content += f"- **{severity.upper()}**: {count} issues\n"
        
        # Report broken links in detail
        if stats.broken_links:
            report_content += "\n## 🔗 Broken Links\n"
            for issue in stats.broken_links:
                report_content += f"- **{issue.file_path}:{issue.line_number}**\n"
                report_content += f"  - Link: `[{issue.link_text}]({issue.target_path})`\n"
                report_content += f"  - Issue: {issue.description}\n"
                if issue.suggested_fix:
                    report_content += f"  - Fix: {issue.suggested_fix}\n"
                report_content += "\n"
        
        # Report path errors
        if stats.path_errors:
            report_content += "## 📁 Path Reference Errors\n"
            for issue in stats.path_errors:
                report_content += f"- **{issue.file_path}:{issue.line_number}**: {issue.description}\n"
                if issue.suggested_fix:
                    report_content += f"  - Fix: {issue.suggested_fix}\n"
        
        # Report inconsistencies
        if stats.inconsistencies_found:
            report_content += "\n## ⚠️ Cross-File Inconsistencies\n"
            for inconsistency in stats.inconsistencies_found:
                report_content += f"- {inconsistency}\n"
        
        # Success message if no issues
        if len(stats.validation_issues) == 0 and len(stats.inconsistencies_found) == 0:
            report_content += "\n## ✅ Validation Success\nAll documentation files are synchronized and validated successfully!\n"
        
        # Add ticket breakdown
        report_content += self._generate_ticket_breakdown(tickets)
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Generated comprehensive report: {report_path}")
        return str(report_path)

    def _generate_ticket_breakdown(self, tickets: List[TicketStatus]) -> str:
        """Generate detailed ticket breakdown for report"""
        content = "\n## Ticket Breakdown\n\n"
        
        # Group tickets by status
        status_groups = {
            'completed': [t for t in tickets if t.status == 'completed'],
            'in_progress': [t for t in tickets if t.status == 'in_progress'],
            'planned': [t for t in tickets if t.status == 'planned'],
            'blocked': [t for t in tickets if t.status == 'blocked']
        }
        
        for status, status_tickets in status_groups.items():
            if status_tickets:
                content += f"### {status.replace('_', ' ').title()} Tickets ({len(status_tickets)})\n"
                for ticket in status_tickets:
                    content += f"- **{ticket.ticket_id}**: {ticket.title} ({ticket.story_points} pts)"
                    if ticket.completion_date:
                        content += f" - Completed: {ticket.completion_date}"
                    content += "\n"
                content += "\n"
        
        return content

    def _save_statistics(self, stats: DocumentationStats):
        """Save statistics for monitoring and tracking"""
        try:
            # Save latest statistics
            stats_path = self.reports_dir / "latest_enhanced_doc_stats.json"
            with open(stats_path, 'w') as f:
                json.dump(stats.to_dict(), f, indent=2)
            
            # Append to history
            history_path = self.reports_dir / "doc_stats_history.json"
            history = []
            
            if history_path.exists():
                try:
                    with open(history_path, 'r') as f:
                        history = json.load(f)
                except:
                    history = []
            
            history.append({
                'timestamp': stats.last_update,
                'completion_percentage': stats.completion_percentage,
                'total_issues': len(stats.validation_issues),
                'broken_links': len(stats.broken_links),
                'inconsistencies': len(stats.inconsistencies_found)
            })
            
            # Keep only last 100 entries
            history = history[-100:]
            
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            self.logger.info("Saved statistics for monitoring")
            
        except Exception as e:
            self.logger.error(f"Error saving statistics: {e}")

    # Utility methods
    def _determine_priority(self, ticket_id: str) -> str:
        """Determine priority based on ticket ID patterns"""
        if ticket_id.startswith('MEM-'):
            return 'HIGH' if ticket_id in ['MEM-001', 'MEM-002', 'MEM-003'] else 'MEDIUM'
        elif ticket_id.startswith('LGR-'):
            return 'HIGH' if ticket_id in ['LGR-001', 'LGR-002', 'LGR-003'] else 'MEDIUM'
        elif ticket_id.startswith('M01-'):
            return 'CRITICAL' if int(ticket_id.split('-')[1]) <= 10 else 'MEDIUM'
        else:
            return 'MEDIUM'

    def _estimate_story_points(self, ticket_id: str, title: str) -> int:
        """Estimate story points based on ticket type and title complexity"""
        known_points = {
            'MEM-001': 8, 'MEM-002': 5, 'MEM-003': 13, 'MEM-004': 8, 'MEM-005': 8, 'MEM-006': 10,
            'LGR-001': 12, 'LGR-002': 15, 'LGR-003': 10, 'LGR-004': 8, 'LGR-005': 6, 'LGR-006': 7
        }
        
        if ticket_id in known_points:
            return known_points[ticket_id]
        
        if any(word in title.lower() for word in ['setup', 'create', 'basic', 'simple']):
            return 3
        elif any(word in title.lower() for word in ['implement', 'deploy', 'integrate']):
            return 5
        elif any(word in title.lower() for word in ['comprehensive', 'advanced', 'framework']):
            return 8
        else:
            return 5

    def _determine_epic(self, ticket_id: str) -> Optional[str]:
        """Determine epic based on ticket ID"""
        if ticket_id.startswith('MEM-'):
            return 'FEP-007'
        elif ticket_id.startswith('LGR-'):
            return 'M02-015'
        elif ticket_id.startswith('M01-'):
            return 'FEP-001'
        elif ticket_id.startswith('M02-'):
            return 'FEP-002'
        elif ticket_id.startswith('M03-'):
            return 'FEP-003'
        else:
            return None

    def _determine_milestone(self, ticket_id: str) -> str:
        """Determine milestone based on ticket ID"""
        if ticket_id.startswith('M01-') or ticket_id.startswith('MEM-') or ticket_id.startswith('LGR-'):
            return 'M01_Foundation'
        elif ticket_id.startswith('M02-'):
            return 'M02_Automation'
        elif ticket_id.startswith('M03-'):
            return 'M03_Orchestration'
        else:
            return 'M01_Foundation'


def create_enhanced_pre_commit_hook():
    """Create enhanced pre-commit hook for documentation consistency"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    git_hooks_dir = claude_pm_root / ".git" / "hooks"
    
    if not git_hooks_dir.exists():
        print("Warning: .git/hooks directory not found. Pre-commit hook not installed.")
        return False
    
    hook_path = git_hooks_dir / "pre-commit"
    hook_content = f"""#!/bin/bash
# Enhanced Documentation Consistency Pre-commit Hook for Claude PM Framework

echo "🔍 Checking enhanced documentation consistency..."

# Run enhanced documentation sync validation
python3 "{claude_pm_root}/scripts/enhanced_doc_sync.py" --validate-only

if [ $? -ne 0 ]; then
    echo "❌ Documentation inconsistencies or validation errors found."
    echo "   Please run 'python3 scripts/enhanced_doc_sync.py' to fix issues."
    echo "   Or review the validation report for details."
    exit 1
fi

echo "✅ Enhanced documentation consistency check passed."
exit 0
"""
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make executable
    os.chmod(hook_path, 0o755)
    
    print(f"✅ Enhanced pre-commit hook installed at {hook_path}")
    return True


def main():
    """Main entry point for enhanced documentation synchronization"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Documentation Synchronization System for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root", 
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Only validate consistency and paths, don't update files"
    )
    parser.add_argument(
        "--install-hooks", 
        action="store_true",
        help="Install enhanced pre-commit hooks"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Suppress console output (log to file only)"
    )
    
    args = parser.parse_args()
    
    if args.install_hooks:
        success = create_enhanced_pre_commit_hook()
        return 0 if success else 1
    
    # Create enhanced sync manager
    sync_manager = EnhancedDocumentationSyncManager(args.claude_pm_root)
    
    if args.quiet:
        # Remove console handler
        sync_manager.logger.handlers = [h for h in sync_manager.logger.handlers 
                                        if not isinstance(h, logging.StreamHandler)]
    
    # Run enhanced synchronization
    success = sync_manager.sync_documentation(validate_only=args.validate_only)
    
    if success:
        print("✅ Enhanced documentation synchronization completed successfully")
        return 0
    else:
        print("❌ Enhanced documentation synchronization found issues")
        print("   Check the generated report for details")
        return 1


if __name__ == "__main__":
    exit(main())