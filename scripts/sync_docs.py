#!/usr/bin/env python3
"""
Documentation Status Synchronization System for Claude PM Framework
M01-041: Implement Documentation Status Synchronization System

This script ensures consistency between BACKLOG.md and TICKETING_SYSTEM.md by:
1. Parsing ticket status from trackdown/BACKLOG.md
2. Updating docs/TICKETING_SYSTEM.md with current completion statistics  
3. Validating consistency across all documentation files
4. Generating automated status reports
"""

import re
import os
import sys
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))

@dataclass
class TicketStatus:
    """Represents the status of a single ticket"""
    ticket_id: str
    title: str
    status: str  # 'completed', 'in_progress', 'pending', 'blocked'
    priority: str
    story_points: int
    epic: Optional[str] = None
    milestone: str = ""
    completion_date: Optional[str] = None
    source_file: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DocumentationStats:
    """Statistics for documentation synchronization report"""
    total_tickets: int
    completed_tickets: int
    in_progress_tickets: int
    pending_tickets: int
    blocked_tickets: int
    completion_percentage: float
    total_story_points: int
    completed_story_points: int
    phase_1_completion: float
    inconsistencies_found: List[str]
    last_update: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DocumentationSyncManager:
    """Manages synchronization between BACKLOG.md and TICKETING_SYSTEM.md"""
    
    def __init__(self, claude_pm_root: str = "/Users/masa/Projects/claude-multiagent-pm"):
        self.claude_pm_root = Path(claude_pm_root)
        self.backlog_path = self.claude_pm_root / "trackdown" / "BACKLOG.md"
        self.ticketing_path = self.claude_pm_root / "docs" / "TICKETING_SYSTEM.md"
        self.reports_dir = self.claude_pm_root / "logs"
        self.logger = self._setup_logging()
        
        # Status markers patterns
        self.status_patterns = {
            'completed': [r'\[x\]', r'✅ COMPLETED', r'✅'],
            'in_progress': [r'🔄', r'IN PROGRESS'],
            'pending': [r'\[ \]', r'PENDING'],
            'blocked': [r'🚫', r'BLOCKED']
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for documentation sync operations"""
        logger = logging.getLogger('DocSync')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.reports_dir / "doc_sync.log"
        self.reports_dir.mkdir(exist_ok=True)
        
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
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def parse_backlog_tickets(self) -> List[TicketStatus]:
        """Parse all tickets from BACKLOG.md with their current status"""
        self.logger.info(f"Parsing tickets from {self.backlog_path}")
        
        if not self.backlog_path.exists():
            raise FileNotFoundError(f"BACKLOG.md not found at {self.backlog_path}")
        
        with open(self.backlog_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        tickets = []
        
        # Parse simple ticket format from various sections
        for line_num, line in enumerate(lines, 1):
            ticket_match = re.match(r'- \[([x ])\] \*\*\[([A-Z0-9]+-\d+)\]\*\* (.+)', line)
            if ticket_match:
                checkbox, ticket_id, title = ticket_match.groups()
                
                # Determine status from checkbox and additional markers
                status = 'completed' if checkbox == 'x' else 'pending'
                
                # Check for additional status markers in the line
                for status_type, patterns in self.status_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            status = status_type
                            break
                
                # Extract completion date if present
                completion_date = None
                date_match = re.search(r'\((\d{4}-\d{2}-\d{2})\)', line)
                if date_match:
                    completion_date = date_match.group(1)
                
                ticket = TicketStatus(
                    ticket_id=ticket_id,
                    title=title.strip(),
                    status=status,
                    priority=self._determine_priority(ticket_id),
                    story_points=self._estimate_story_points(ticket_id, title),
                    epic=self._determine_epic(ticket_id),
                    milestone=self._determine_milestone(ticket_id),
                    completion_date=completion_date,
                    source_file="BACKLOG.md",
                    line_number=line_num
                )
                tickets.append(ticket)
        
        # Parse detailed tickets from Priority Implementation section
        detailed_tickets = self._parse_detailed_tickets(content)
        tickets.extend(detailed_tickets)
        
        self.logger.info(f"Parsed {len(tickets)} tickets from BACKLOG.md")
        return tickets

    def _parse_detailed_tickets(self, content: str) -> List[TicketStatus]:
        """Parse detailed ticket format with full metadata"""
        tickets = []
        
        # Find the Priority Implementation Tickets section
        priority_section_match = re.search(
            r'## 🚀 Priority Implementation Tickets.*?(?=\n## |\Z)', 
            content, 
            re.DOTALL
        )
        
        if not priority_section_match:
            return tickets
        
        section_content = priority_section_match.group(0)
        
        # Split by ticket headers (### TICKET-ID:)
        ticket_sections = re.split(r'\n### ([A-Z0-9]+-\d+):', section_content)
        
        for i in range(1, len(ticket_sections), 2):
            if i + 1 >= len(ticket_sections):
                break
                
            ticket_id = ticket_sections[i].strip()
            ticket_content = ticket_sections[i + 1]
            
            try:
                # Extract title
                title_match = re.search(r'^([^\n]+)', ticket_content.strip())
                title = title_match.group(1).strip() if title_match else f"Ticket {ticket_id}"
                
                # Extract status markers
                status = 'pending'
                completion_date = None
                
                if '✅ COMPLETED' in ticket_content:
                    status = 'completed'
                    # Look for completion date
                    date_match = re.search(r'Completion Date.*?(\d{4}-\d{2}-\d{2})', ticket_content)
                    if date_match:
                        completion_date = date_match.group(1)
                elif '🔄' in ticket_content or 'In Progress' in ticket_content:
                    status = 'in_progress'
                elif '🚫' in ticket_content or 'BLOCKED' in ticket_content:
                    status = 'blocked'
                
                # Extract story points
                points_match = re.search(r'Story Points.*?(\d+)', ticket_content)
                story_points = int(points_match.group(1)) if points_match else self._estimate_story_points(ticket_id, title)
                
                # Extract priority
                priority_match = re.search(r'Priority.*?(CRITICAL|HIGH|MEDIUM|LOW)', ticket_content, re.IGNORECASE)
                priority = priority_match.group(1).upper() if priority_match else self._determine_priority(ticket_id)
                
                ticket = TicketStatus(
                    ticket_id=ticket_id,
                    title=title,
                    status=status,
                    priority=priority,
                    story_points=story_points,
                    epic=self._determine_epic(ticket_id),
                    milestone=self._determine_milestone(ticket_id),
                    completion_date=completion_date,
                    source_file="BACKLOG.md",
                    line_number=0  # Can't determine line number easily for detailed format
                )
                tickets.append(ticket)
                
            except Exception as e:
                self.logger.error(f"Error parsing detailed ticket {ticket_id}: {e}")
        
        return tickets

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
        # Known story points for specific tickets
        known_points = {
            'MEM-001': 8, 'MEM-002': 5, 'MEM-003': 13, 'MEM-004': 8, 'MEM-005': 8, 'MEM-006': 10,
            'LGR-001': 12, 'LGR-002': 15, 'LGR-003': 10, 'LGR-004': 8, 'LGR-005': 6, 'LGR-006': 7
        }
        
        if ticket_id in known_points:
            return known_points[ticket_id]
        
        # Estimate based on title complexity
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

    def generate_statistics(self, tickets: List[TicketStatus]) -> DocumentationStats:
        """Generate comprehensive statistics from ticket data"""
        total = len(tickets)
        completed = sum(1 for t in tickets if t.status == 'completed')
        in_progress = sum(1 for t in tickets if t.status == 'in_progress')
        pending = sum(1 for t in tickets if t.status == 'pending')
        blocked = sum(1 for t in tickets if t.status == 'blocked')
        
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        total_story_points = sum(t.story_points for t in tickets)
        completed_story_points = sum(t.story_points for t in tickets if t.status == 'completed')
        
        # Calculate Phase 1 completion (MEM and LGR tickets)
        phase_1_tickets = [t for t in tickets if t.ticket_id.startswith(('MEM-', 'LGR-'))]
        phase_1_completed = sum(1 for t in phase_1_tickets if t.status == 'completed')
        phase_1_total = len(phase_1_tickets)
        phase_1_completion = (phase_1_completed / phase_1_total * 100) if phase_1_total > 0 else 0
        
        return DocumentationStats(
            total_tickets=total,
            completed_tickets=completed,
            in_progress_tickets=in_progress,
            pending_tickets=pending,
            blocked_tickets=blocked,
            completion_percentage=completion_percentage,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            phase_1_completion=phase_1_completion,
            inconsistencies_found=[],
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def validate_documentation_consistency(self, tickets: List[TicketStatus]) -> List[str]:
        """Validate consistency between BACKLOG.md and TICKETING_SYSTEM.md"""
        inconsistencies = []
        
        if not self.ticketing_path.exists():
            inconsistencies.append(f"TICKETING_SYSTEM.md not found at {self.ticketing_path}")
            return inconsistencies
        
        with open(self.ticketing_path, 'r', encoding='utf-8') as f:
            ticketing_content = f.read()
        
        # Check each ticket's status consistency
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
                backlog_status = ticket.status
                ticketing_has_completed = '✅ COMPLETED' in line or '✅' in line
                ticketing_has_pending = not ticketing_has_completed and ('[ ]' in line or 'Pending' in line)
                
                if backlog_status == 'completed' and not ticketing_has_completed:
                    inconsistencies.append(
                        f"{ticket.ticket_id}: BACKLOG.md shows completed but TICKETING_SYSTEM.md shows pending"
                    )
                elif backlog_status == 'pending' and ticketing_has_completed:
                    inconsistencies.append(
                        f"{ticket.ticket_id}: BACKLOG.md shows pending but TICKETING_SYSTEM.md shows completed"
                    )
        
        return inconsistencies

    def update_ticketing_system_md(self, tickets: List[TicketStatus], stats: DocumentationStats) -> bool:
        """Update TICKETING_SYSTEM.md with current statistics and status"""
        try:
            if not self.ticketing_path.exists():
                self.logger.error(f"TICKETING_SYSTEM.md not found at {self.ticketing_path}")
                return False
            
            with open(self.ticketing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the overview section with current statistics
            overview_pattern = r'(## Overview\n)([^#]*?)(?=\n## |\Z)'
            new_overview = f"""## Overview
The Claude PM Framework uses a sophisticated {stats.total_tickets}-ticket system for managing the Claude Max + mem0AI + LangGraph dual integration project. This document explains the current system status with {stats.completion_percentage:.0f}% overall completion ({stats.completed_tickets}/{stats.total_tickets} tickets), featuring completed zero-configuration memory integration and advanced workflow orchestration.

**Last Updated**: {stats.last_update}
**Phase 1 Completion**: {stats.phase_1_completion:.0f}%
**Total Story Points**: {stats.completed_story_points}/{stats.total_story_points}

"""
            
            content = re.sub(overview_pattern, new_overview, content, flags=re.DOTALL)
            
            # Update individual ticket statuses
            for ticket in tickets:
                # Update ticket status markers
                ticket_pattern = f"(\\*\\*{re.escape(ticket.ticket_id)}\\*\\*[^\\n]*)"
                
                def update_ticket_line(match):
                    line = match.group(1)
                    
                    # Remove existing status markers
                    line = re.sub(r'✅ COMPLETED', '', line)
                    line = re.sub(r'✅', '', line)
                    line = re.sub(r'🔄', '', line)
                    line = re.sub(r'🚫', '', line)
                    
                    # Add current status marker
                    if ticket.status == 'completed':
                        line += ' ✅ COMPLETED'
                        if ticket.completion_date:
                            line += f' ({ticket.completion_date})'
                    elif ticket.status == 'in_progress':
                        line += ' 🔄'
                    elif ticket.status == 'blocked':
                        line += ' 🚫'
                    
                    return line
                
                content = re.sub(ticket_pattern, update_ticket_line, content)
            
            # Write updated content
            with open(self.ticketing_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Updated TICKETING_SYSTEM.md with current statistics")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating TICKETING_SYSTEM.md: {e}")
            return False

    def generate_status_report(self, tickets: List[TicketStatus], stats: DocumentationStats) -> str:
        """Generate comprehensive status report"""
        report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.reports_dir / f"doc_sync_report_{report_timestamp}.md"
        
        # Group tickets by status
        completed_tickets = [t for t in tickets if t.status == 'completed']
        in_progress_tickets = [t for t in tickets if t.status == 'in_progress']
        pending_tickets = [t for t in tickets if t.status == 'pending']
        blocked_tickets = [t for t in tickets if t.status == 'blocked']
        
        # Group by milestone
        milestone_stats = {}
        for ticket in tickets:
            milestone = ticket.milestone
            if milestone not in milestone_stats:
                milestone_stats[milestone] = {'total': 0, 'completed': 0, 'story_points': 0, 'completed_points': 0}
            
            milestone_stats[milestone]['total'] += 1
            milestone_stats[milestone]['story_points'] += ticket.story_points
            
            if ticket.status == 'completed':
                milestone_stats[milestone]['completed'] += 1
                milestone_stats[milestone]['completed_points'] += ticket.story_points
        
        report_content = f"""# Documentation Synchronization Report
Generated: {stats.last_update}

## Executive Summary
- **Total Tickets**: {stats.total_tickets}
- **Completed**: {stats.completed_tickets} ({stats.completion_percentage:.1f}%)
- **In Progress**: {stats.in_progress_tickets}
- **Pending**: {stats.pending_tickets}
- **Blocked**: {stats.blocked_tickets}
- **Story Points**: {stats.completed_story_points}/{stats.total_story_points} ({stats.completed_story_points/stats.total_story_points*100:.1f}%)
- **Phase 1 Completion**: {stats.phase_1_completion:.1f}%

## Milestone Progress
"""
        
        for milestone, data in milestone_stats.items():
            completion_pct = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            points_pct = (data['completed_points'] / data['story_points'] * 100) if data['story_points'] > 0 else 0
            report_content += f"- **{milestone}**: {data['completed']}/{data['total']} tickets ({completion_pct:.1f}%), {data['completed_points']}/{data['story_points']} points ({points_pct:.1f}%)\n"
        
        if stats.inconsistencies_found:
            report_content += "\n## ⚠️ Inconsistencies Found\n"
            for inconsistency in stats.inconsistencies_found:
                report_content += f"- {inconsistency}\n"
        else:
            report_content += "\n## ✅ No Inconsistencies Found\nAll documentation files are synchronized.\n"
        
        report_content += f"""
## Completed Tickets ({len(completed_tickets)})
"""
        for ticket in completed_tickets:
            report_content += f"- **{ticket.ticket_id}**: {ticket.title} ({ticket.story_points} pts)"
            if ticket.completion_date:
                report_content += f" - Completed: {ticket.completion_date}"
            report_content += "\n"
        
        if in_progress_tickets:
            report_content += f"\n## In Progress Tickets ({len(in_progress_tickets)})\n"
            for ticket in in_progress_tickets:
                report_content += f"- **{ticket.ticket_id}**: {ticket.title} ({ticket.story_points} pts)\n"
        
        if blocked_tickets:
            report_content += f"\n## Blocked Tickets ({len(blocked_tickets)})\n"
            for ticket in blocked_tickets:
                report_content += f"- **{ticket.ticket_id}**: {ticket.title} ({ticket.story_points} pts)\n"
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Generated status report: {report_path}")
        return str(report_path)

    def sync_documentation(self, validate_only: bool = False) -> bool:
        """Main synchronization method"""
        try:
            self.logger.info("Starting documentation synchronization...")
            
            # Parse tickets from BACKLOG.md
            tickets = self.parse_backlog_tickets()
            
            # Generate statistics
            stats = self.generate_statistics(tickets)
            
            # Validate consistency
            inconsistencies = self.validate_documentation_consistency(tickets)
            stats.inconsistencies_found = inconsistencies
            
            if inconsistencies:
                self.logger.warning(f"Found {len(inconsistencies)} inconsistencies:")
                for inconsistency in inconsistencies:
                    self.logger.warning(f"  - {inconsistency}")
            
            # Generate status report
            report_path = self.generate_status_report(tickets, stats)
            
            if not validate_only:
                # Update TICKETING_SYSTEM.md
                update_success = self.update_ticketing_system_md(tickets, stats)
                if not update_success:
                    self.logger.error("Failed to update TICKETING_SYSTEM.md")
                    return False
            
            # Save statistics as JSON for monitoring
            stats_path = self.reports_dir / "latest_doc_stats.json"
            with open(stats_path, 'w') as f:
                json.dump(stats.to_dict(), f, indent=2)
            
            self.logger.info(f"Documentation synchronization completed successfully")
            self.logger.info(f"Status report: {report_path}")
            
            return len(inconsistencies) == 0
            
        except Exception as e:
            self.logger.error(f"Error during documentation synchronization: {e}")
            return False


def create_pre_commit_hook():
    """Create pre-commit hook for documentation consistency"""
    claude_pm_root = Path("/Users/masa/Projects/claude-multiagent-pm")
    git_hooks_dir = claude_pm_root / ".git" / "hooks"
    
    if not git_hooks_dir.exists():
        print("Warning: .git/hooks directory not found. Pre-commit hook not installed.")
        return False
    
    hook_path = git_hooks_dir / "pre-commit"
    hook_content = f"""#!/bin/bash
# Documentation consistency pre-commit hook for Claude PM Framework

echo "Checking documentation consistency..."

# Run documentation sync validation
python3 "{claude_pm_root}/scripts/sync_docs.py" --validate-only

if [ $? -ne 0 ]; then
    echo "❌ Documentation inconsistencies found. Please run 'python3 scripts/sync_docs.py' to fix."
    exit 1
fi

echo "✅ Documentation consistency check passed."
exit 0
"""
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make executable
    os.chmod(hook_path, 0o755)
    
    print(f"✅ Pre-commit hook installed at {hook_path}")
    return True


def main():
    """Main entry point for sync_docs.py"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Documentation Status Synchronization System for Claude PM Framework"
    )
    parser.add_argument(
        "--claude-pm-root", 
        default="/Users/masa/Projects/claude-multiagent-pm",
        help="Root directory of Claude PM Framework"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Only validate consistency, don't update files"
    )
    parser.add_argument(
        "--install-hooks", 
        action="store_true",
        help="Install pre-commit hooks for documentation consistency"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Suppress console output (log to file only)"
    )
    
    args = parser.parse_args()
    
    if args.install_hooks:
        success = create_pre_commit_hook()
        return 0 if success else 1
    
    # Setup sync manager
    sync_manager = DocumentationSyncManager(args.claude_pm_root)
    
    if args.quiet:
        # Remove console handler
        sync_manager.logger.handlers = [h for h in sync_manager.logger.handlers if not isinstance(h, logging.StreamHandler)]
    
    # Run synchronization
    success = sync_manager.sync_documentation(validate_only=args.validate_only)
    
    if success:
        print("✅ Documentation synchronization completed successfully")
        return 0
    else:
        print("❌ Documentation synchronization failed")
        return 1


if __name__ == "__main__":
    exit(main())