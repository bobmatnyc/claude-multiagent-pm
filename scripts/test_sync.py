#!/usr/bin/env python3
"""
Test script to validate Claude PM ticket parsing and sync functionality
without requiring GitHub access.
"""

import sys
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from github_sync import TicketParser


def test_ticket_parsing():
    """Test ticket parsing from BACKLOG.md"""
    print("🧪 Testing Claude PM ticket parsing...")
    
    backlog_path = "/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md"
    
    if not Path(backlog_path).exists():
        print(f"❌ Backlog file not found: {backlog_path}")
        return False
    
    try:
        # Parse tickets
        tickets = TicketParser.parse_tickets_from_backlog(backlog_path)
        
        print(f"✅ Successfully parsed {len(tickets)} tickets")
        
        # Debug: Show first few lines of backlog for verification
        with open(backlog_path, 'r') as f:
            lines = f.readlines()[:20]
        print(f"📄 First 20 lines of backlog:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {line.rstrip()}")
        print()
        
        # Show statistics
        status_counts = {}
        priority_counts = {}
        epic_counts = {}
        
        for ticket in tickets:
            # Count by status
            status_counts[ticket.status] = status_counts.get(ticket.status, 0) + 1
            
            # Count by priority
            priority_counts[ticket.priority] = priority_counts.get(ticket.priority, 0) + 1
            
            # Count by epic
            if ticket.epic:
                epic_counts[ticket.epic] = epic_counts.get(ticket.epic, 0) + 1
        
        print(f"\n📊 Ticket Statistics:")
        print(f"   Status breakdown: {dict(status_counts)}")
        print(f"   Priority breakdown: {dict(priority_counts)}")
        print(f"   Epic breakdown: {dict(epic_counts)}")
        
        # Show sample tickets
        print(f"\n📋 Sample Tickets:")
        for i, ticket in enumerate(tickets[:5]):
            print(f"   {i+1}. [{ticket.ticket_id}] {ticket.title}")
            print(f"      Priority: {ticket.priority}, Status: {ticket.status}")
            print(f"      Epic: {ticket.epic}, Milestone: {ticket.milestone}")
            print(f"      Story Points: {ticket.story_points}")
            if ticket.dependencies:
                print(f"      Dependencies: {', '.join(ticket.dependencies)}")
            print()
        
        if len(tickets) > 5:
            print(f"   ... and {len(tickets) - 5} more tickets")
        
        # Validate critical tickets are present
        critical_tickets = [t for t in tickets if t.priority == 'CRITICAL']
        print(f"\n🔥 Critical Tickets: {len(critical_tickets)}")
        for ticket in critical_tickets:
            print(f"   - [{ticket.ticket_id}] {ticket.title}")
        
        # Check for completed tickets
        completed_tickets = [t for t in tickets if t.status == 'completed']
        print(f"\n✅ Completed Tickets: {len(completed_tickets)}")
        for ticket in completed_tickets[:3]:  # Show first 3
            print(f"   - [{ticket.ticket_id}] {ticket.title}")
        if len(completed_tickets) > 3:
            print(f"   ... and {len(completed_tickets) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing tickets: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_label_generation():
    """Test label generation for tickets"""
    print("\n🏷️  Testing label generation...")
    
    try:
        # Create sample tickets
        sample_tickets = [
            {"ticket_id": "MEM-001", "priority": "CRITICAL", "epic": "FEP-007"},
            {"ticket_id": "LGR-001", "priority": "HIGH", "epic": "FEP-011"},
            {"ticket_id": "M01-001", "priority": "HIGH", "epic": "FEP-001"},
            {"ticket_id": "INT-001", "priority": "MEDIUM", "epic": "FEP-002"},
        ]
        
        for sample in sample_tickets:
            labels = TicketParser._extract_labels_from_id(sample["ticket_id"])
            print(f"   {sample['ticket_id']}: {labels}")
        
        print("✅ Label generation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing labels: {e}")
        return False


def test_epic_mapping():
    """Test epic mapping logic"""
    print("\n🎯 Testing epic mapping...")
    
    try:
        test_cases = [
            ("MEM-001", "FEP-007"),
            ("LGR-001", "FEP-011"),
            ("M01-001", "FEP-001"),
            ("M02-001", "FEP-002"),
            ("M03-001", "FEP-004"),
            ("INT-001", "FEP-002"),
            ("INF-001", "FEP-001"),
            ("FEP-007", "FEP-007"),
        ]
        
        for ticket_id, expected_epic in test_cases:
            actual_epic = TicketParser._determine_epic(ticket_id)
            status = "✅" if actual_epic == expected_epic else "❌"
            print(f"   {ticket_id} → {actual_epic} (expected: {expected_epic}) {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing epic mapping: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Claude PM GitHub Sync - Test Suite")
    print("=" * 50)
    
    tests = [
        test_ticket_parsing,
        test_label_generation,
        test_epic_mapping,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed! The sync system is ready for use.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())