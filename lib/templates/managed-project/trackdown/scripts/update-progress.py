#!/usr/bin/env python3
"""
Progress tracking script for py-mcp-ipc implementation.

Updates task status, calculates progress metrics, and generates reports.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime
import json

class ProgressTracker:
    """Track implementation progress across phases and tasks."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.trackdown_dir = self.project_root / "trackdown"
        self.backlog_file = self.trackdown_dir / "BACKLOG.md"
        self.milestones_file = self.trackdown_dir / "MILESTONES.md"
        
    def parse_backlog(self) -> Dict[str, List[Dict]]:
        """Parse backlog file to extract task information."""
        if not self.backlog_file.exists():
            print(f"Error: Backlog file not found: {self.backlog_file}")
            return {}
            
        with open(self.backlog_file, 'r') as f:
            content = f.read()
            
        phases = {}
        current_phase = None
        
        for line in content.split('\n'):
            # Phase headers
            if line.startswith('### Phase'):
                current_phase = line.strip('# ').strip()
                phases[current_phase] = []
            
            # Task lines
            elif line.strip().startswith('- ['):
                if current_phase:
                    task_match = re.match(r'- \[([ x])\] \*\*\[([^\]]+)\]\*\* (.+)', line.strip())
                    if task_match:
                        completed = task_match.group(1) == 'x'
                        task_id = task_match.group(2)
                        description = task_match.group(3)
                        
                        phases[current_phase].append({
                            'id': task_id,
                            'description': description,
                            'completed': completed,
                            'line': line.strip()
                        })
        
        return phases
    
    def calculate_progress(self, phases: Dict) -> Dict[str, float]:
        """Calculate completion percentage for each phase."""
        progress = {}
        
        for phase_name, tasks in phases.items():
            if not tasks:
                progress[phase_name] = 0.0
                continue
                
            completed_tasks = sum(1 for task in tasks if task['completed'])
            total_tasks = len(tasks)
            progress[phase_name] = (completed_tasks / total_tasks) * 100
            
        return progress
    
    def generate_progress_report(self) -> str:
        """Generate a progress report."""
        phases = self.parse_backlog()
        progress = self.calculate_progress(phases)
        
        report = []
        report.append("# Python MCP Bus - Implementation Progress Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_tasks = sum(len(tasks) for tasks in phases.values())
        completed_tasks = sum(len([t for t in tasks if t['completed']]) for tasks in phases.values())
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        report.append(f"## Overall Progress: {overall_progress:.1f}% ({completed_tasks}/{total_tasks} tasks)")
        report.append("")
        
        for phase_name, tasks in phases.items():
            phase_progress = progress.get(phase_name, 0)
            completed = len([t for t in tasks if t['completed']])
            total = len(tasks)
            
            status_icon = "✅" if phase_progress == 100 else "🔄" if phase_progress > 0 else "⏳"
            
            report.append(f"### {status_icon} {phase_name}: {phase_progress:.1f}% ({completed}/{total})")
            
            for task in tasks:
                task_icon = "✅" if task['completed'] else "⬜"
                report.append(f"  {task_icon} {task['id']}: {task['description']}")
            
            report.append("")
        
        return "\n".join(report)
    
    def update_task_status(self, task_id: str, completed: bool) -> bool:
        """Update task completion status in backlog file."""
        if not self.backlog_file.exists():
            print(f"Error: Backlog file not found: {self.backlog_file}")
            return False
            
        with open(self.backlog_file, 'r') as f:
            content = f.read()
        
        # Find and update the task line
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            task_match = re.match(r'- \[([ x])\] \*\*\[([^\]]+)\]\*\*', line.strip())
            if task_match and task_match.group(2) == task_id:
                # Update the checkbox
                new_status = 'x' if completed else ' '
                lines[i] = re.sub(r'- \[([ x])\]', f'- [{new_status}]', line)
                updated = True
                break
        
        if updated:
            with open(self.backlog_file, 'w') as f:
                f.write('\n'.join(lines))
            print(f"Updated {task_id} status to {'completed' if completed else 'pending'}")
            return True
        else:
            print(f"Task {task_id} not found in backlog")
            return False
    
    def list_pending_tasks(self) -> List[Dict]:
        """List all pending tasks."""
        phases = self.parse_backlog()
        pending_tasks = []
        
        for phase_name, tasks in phases.items():
            for task in tasks:
                if not task['completed']:
                    task['phase'] = phase_name
                    pending_tasks.append(task)
        
        return pending_tasks

def main():
    """Main CLI interface for progress tracking."""
    if len(sys.argv) < 2:
        print("Usage: python update-progress.py <command> [args]")
        print("Commands:")
        print("  report                    - Generate progress report")
        print("  complete <task_id>        - Mark task as completed")
        print("  pending <task_id>         - Mark task as pending")
        print("  list-pending              - List all pending tasks")
        print("  stats                     - Show progress statistics")
        return
    
    # Find project root (directory containing trackdown folder)
    project_root = Path(__file__).parent.parent.parent
    if not (project_root / "trackdown").exists():
        print("Error: Could not find trackdown directory")
        return
    
    tracker = ProgressTracker(str(project_root))
    command = sys.argv[1]
    
    if command == "report":
        report = tracker.generate_progress_report()
        print(report)
        
        # Save report to file
        report_file = tracker.trackdown_dir / "progress_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")
    
    elif command == "complete":
        if len(sys.argv) < 3:
            print("Usage: python update-progress.py complete <task_id>")
            return
        task_id = sys.argv[2]
        tracker.update_task_status(task_id, True)
    
    elif command == "pending":
        if len(sys.argv) < 3:
            print("Usage: python update-progress.py pending <task_id>")
            return
        task_id = sys.argv[2]
        tracker.update_task_status(task_id, False)
    
    elif command == "list-pending":
        pending_tasks = tracker.list_pending_tasks()
        if pending_tasks:
            print("Pending Tasks:")
            for task in pending_tasks:
                print(f"  {task['id']}: {task['description']} ({task['phase']})")
        else:
            print("No pending tasks found!")
    
    elif command == "stats":
        phases = tracker.parse_backlog()
        progress = tracker.calculate_progress(phases)
        
        total_tasks = sum(len(tasks) for tasks in phases.values())
        completed_tasks = sum(len([t for t in tasks if t['completed']]) for tasks in phases.values())
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        print(f"Overall Progress: {overall_progress:.1f}% ({completed_tasks}/{total_tasks} tasks)")
        print("\nPhase Breakdown:")
        for phase_name, phase_progress in progress.items():
            tasks = phases[phase_name]
            completed = len([t for t in tasks if t['completed']])
            total = len(tasks)
            print(f"  {phase_name}: {phase_progress:.1f}% ({completed}/{total})")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()