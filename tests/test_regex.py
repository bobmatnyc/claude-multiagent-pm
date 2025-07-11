#!/usr/bin/env python3
"""
Test regex patterns for ticket parsing
"""

import re

def test_ticket_patterns():
    """Test different ticket patterns"""
    
    test_lines = [
        "- [x] **[M01-001]** Establish core Claude PM directory structure",
        "- [ ] **[M01-010]** Set up ai-code-review integration across all M01 projects", 
        "- [x] **[MEM-003]** Enhanced Multi-Agent Architecture Implementation ✅ COMPLETED",
        "- [ ] **[FEP-007]** Claude Max + mem0AI Enhanced Architecture (NEW - HIGH PRIORITY)",
    ]
    
    patterns = [
        r'- \[([x ])\] \*\*\[([A-Z]+-\d+)\]\*\* (.+?)(?:\n|$)',
        r'- \[([x ])\] \*\*\[([A-Z]+-\d+)\]\*\* (.+)',
        r'- \[([x ])\] \*\*\[([A-Z0-9]+-\d+)\]\*\* (.+)',
        r'- \[([x ])\] \*\*\[([A-Z0-9]+-\d+)\]\*\* (.+?)(?:\s*✅|\s*\(|$)',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"🧪 Testing pattern {i}: {pattern}")
        
        for line in test_lines:
            match = re.search(pattern, line)
            if match:
                checkbox, ticket_id, title = match.groups()
                status = "completed" if checkbox == 'x' else "pending"
                print(f"  ✅ {ticket_id}: {title[:50]}... (status: {status})")
            else:
                print(f"  ❌ No match: {line[:60]}...")
        print()


def test_actual_file_content():
    """Test against actual file content"""
    
    with open("/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md", 'r') as f:
        content = f.read()
    
    # Find the In Progress section
    in_progress_section = re.search(r'### In Progress.*?(?=### |$)', content, re.DOTALL)
    
    if in_progress_section:
        section_content = in_progress_section.group(0)
        lines = section_content.split('\n')
        
        print("📄 Actual lines from 'In Progress' section:")
        for i, line in enumerate(lines[:10]):
            if line.strip() and line.startswith('- '):
                print(f"  {i}: '{line}'")
                
                # Test the pattern
                pattern = r'- \[([x ])\] \*\*\[([A-Z0-9]+-\d+)\]\*\* (.+)'
                match = re.search(pattern, line)
                if match:
                    checkbox, ticket_id, title = match.groups()
                    print(f"    ✅ Matched: {ticket_id} - {title[:40]}...")
                else:
                    print(f"    ❌ No match")
        print()


if __name__ == "__main__":
    print("🔍 Regex Pattern Testing")
    print("=" * 50)
    
    test_ticket_patterns()
    test_actual_file_content()
    
    print("=" * 50)
    print("🏁 Testing complete")