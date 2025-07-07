#!/usr/bin/env python3
"""
Debug script to test ticket parsing and see what sections are found
"""

import re
import sys
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from github_sync import TicketParser


def debug_section_parsing():
    """Debug the section parsing logic"""
    import os
    claude_pm_root = os.getenv("CLAUDE_PM_ROOT", "/Users/masa/Projects/Claude-PM")
    backlog_path = f"{claude_pm_root}/trackdown/BACKLOG.md"
    
    with open(backlog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Debugging section parsing...")
    print(f"📄 Total content length: {len(content)} characters")
    print()
    
    # Test "In Progress" section
    print("🟡 Testing 'In Progress' section...")
    in_progress_pattern = r'### In Progress.*?(?=### |$)'
    in_progress_section = re.search(in_progress_pattern, content, re.DOTALL)
    
    if in_progress_section:
        section_content = in_progress_section.group(0)
        print(f"✅ Found 'In Progress' section ({len(section_content)} chars)")
        print("First 500 chars:")
        print(section_content[:500])
        print()
        
        # Test simple ticket parsing on this section
        tickets = TicketParser._parse_simple_tickets(section_content, status="completed")
        print(f"📊 Parsed {len(tickets)} tickets from 'In Progress' section")
        
        if tickets:
            for i, ticket in enumerate(tickets[:3]):
                print(f"   {i+1}. [{ticket.ticket_id}] {ticket.title}")
        
    else:
        print("❌ 'In Progress' section not found")
    
    print()
    
    # Test "Product Backlog" section
    print("🟢 Testing 'Product Backlog' section...")
    backlog_pattern = r'## 📋 Product Backlog.*?(?=## |$)'
    backlog_section = re.search(backlog_pattern, content, re.DOTALL)
    
    if backlog_section:
        section_content = backlog_section.group(0)
        print(f"✅ Found 'Product Backlog' section ({len(section_content)} chars)")
        print("First 500 chars:")
        print(section_content[:500])
        print()
        
        # Test simple ticket parsing on this section
        tickets = TicketParser._parse_simple_tickets(section_content, status="pending")
        print(f"📊 Parsed {len(tickets)} tickets from 'Product Backlog' section")
        
        if tickets:
            for i, ticket in enumerate(tickets[:3]):
                print(f"   {i+1}. [{ticket.ticket_id}] {ticket.title}")
        
    else:
        print("❌ 'Product Backlog' section not found")
    
    print()
    
    # Test "Priority Implementation Tickets" section
    print("🔥 Testing 'Priority Implementation Tickets' section...")
    priority_pattern = r'## 🚀 Priority Implementation Tickets.*?(?=## |$)'
    priority_section = re.search(priority_pattern, content, re.DOTALL)
    
    if priority_section:
        section_content = priority_section.group(0)
        print(f"✅ Found 'Priority Implementation Tickets' section ({len(section_content)} chars)")
        print("First 500 chars:")
        print(section_content[:500])
        print()
        
        # Test detailed ticket parsing on this section
        tickets = TicketParser._parse_detailed_tickets(section_content)
        print(f"📊 Parsed {len(tickets)} tickets from 'Priority Implementation Tickets' section")
        
        if tickets:
            for i, ticket in enumerate(tickets[:3]):
                print(f"   {i+1}. [{ticket.ticket_id}] {ticket.title}")
                print(f"       Priority: {ticket.priority}, Points: {ticket.story_points}")
        
    else:
        print("❌ 'Priority Implementation Tickets' section not found")
    
    print()


def debug_simple_ticket_pattern():
    """Debug the simple ticket pattern matching"""
    print("🔍 Testing simple ticket pattern...")
    
    test_lines = [
        "- [x] **[M01-001]** Establish core Claude PM directory structure",
        "- [ ] **[M01-010]** Set up ai-code-review integration across all M01 projects",
        "- [x] **[MEM-003]** Enhanced Multi-Agent Architecture Implementation ✅ COMPLETED",
    ]
    
    pattern = r'- \[([x ])\] \*\*\[([A-Z]+-\d+)\]\*\* (.+?)(?:\n|$)'
    
    for line in test_lines:
        match = re.search(pattern, line)
        if match:
            checkbox, ticket_id, title = match.groups()
            status = "completed" if checkbox == 'x' else "pending"
            print(f"✅ Matched: [{ticket_id}] {title[:50]}... (status: {status})")
        else:
            print(f"❌ No match: {line}")
    
    print()


def main():
    """Run debug tests"""
    print("🐛 Claude PM Ticket Parser - Debug Mode")
    print("=" * 60)
    
    debug_simple_ticket_pattern()
    debug_section_parsing()
    
    print("=" * 60)
    print("🏁 Debug complete")


if __name__ == "__main__":
    main()