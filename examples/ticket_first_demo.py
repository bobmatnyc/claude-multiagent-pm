#!/usr/bin/env python3
"""
Ticket-First Operations Mode Demo
================================

This script demonstrates how ticket-first operations mode works in practice.
It shows the complete flow from ticket creation to filtered execution.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import framework components
from claude_pm.orchestration.context_manager import ContextManager, ContextFilter
from claude_pm.services.ticketing_service import TicketingService, TicketData


class TicketFirstDemo:
    """Demonstrates ticket-first operations mode."""
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.tickets = {}  # Simple in-memory ticket storage for demo
        self.ticket_counter = 0
    
    def create_ticket(self, **kwargs) -> TicketData:
        """Create a ticket with metadata for context filtering."""
        self.ticket_counter += 1
        ticket_id = f"DEMO-{self.ticket_counter:03d}"
        
        ticket = TicketData(
            id=ticket_id,
            title=kwargs.get('title', 'Demo Ticket'),
            description=kwargs.get('description', ''),
            priority=kwargs.get('priority', 'medium'),
            labels=kwargs.get('labels', []),
            metadata=kwargs.get('metadata', {}),
            created_at=datetime.now()
        )
        
        self.tickets[ticket_id] = ticket
        print(f"\n✅ Created ticket {ticket_id}: {ticket.title}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Agent Type: {ticket.metadata.get('agent_type', 'N/A')}")
        
        return ticket
    
    def demonstrate_context_filtering(self, ticket: TicketData, full_context: Dict[str, Any]):
        """Show how context is filtered based on ticket metadata."""
        print(f"\n🔍 Filtering context for ticket {ticket.id}")
        print(f"   Full context files: {len(full_context.get('files', {}))}")
        
        # Filter context based on ticket's agent type
        agent_type = ticket.metadata.get('agent_type', 'orchestrator')
        filtered_context = self.context_manager.filter_context_for_agent(
            agent_type=agent_type,
            full_context=full_context
        )
        
        print(f"   Filtered context files: {len(filtered_context.get('files', {}))}")
        
        # Show which files were included
        if 'files' in filtered_context:
            print("\n   Included files:")
            for file_path in sorted(filtered_context['files'].keys()):
                print(f"     - {Path(file_path).name}")
        
        return filtered_context
    
    def run_documentation_task_demo(self):
        """Demo: Documentation task with filtered context."""
        print("\n" + "="*60)
        print("DEMO 1: Documentation Task")
        print("="*60)
        
        # Create a documentation ticket
        ticket = self.create_ticket(
            title="Update API documentation",
            description="Update the API docs with new endpoints",
            priority="high",
            labels=["documentation", "api"],
            metadata={
                "agent_type": "documentation",
                "context_requirements": {
                    "focus_on": ["docs", "api", "readme"],
                    "exclude": ["tests", "migrations"]
                }
            }
        )
        
        # Create sample project context
        full_context = {
            "files": {
                "/project/README.md": "# Project README",
                "/project/docs/API.md": "# API Documentation",
                "/project/docs/CHANGELOG.md": "# Changelog",
                "/project/src/main.py": "# Main application",
                "/project/tests/test_api.py": "# API tests",
                "/project/migrations/001_init.sql": "CREATE TABLE users;"
            }
        }
        
        # Demonstrate filtering
        filtered_context = self.demonstrate_context_filtering(ticket, full_context)
        
        # Show the filtered result
        print(f"\n📊 Context reduction: {self._calculate_reduction(full_context, filtered_context):.1f}%")
    
    def run_security_audit_demo(self):
        """Demo: Security audit with sensitive data filtering."""
        print("\n" + "="*60)
        print("DEMO 2: Security Audit Task")
        print("="*60)
        
        # Create a security ticket
        ticket = self.create_ticket(
            title="Security audit for authentication",
            description="Audit the authentication system for vulnerabilities",
            priority="critical",
            labels=["security", "audit", "authentication"],
            metadata={
                "agent_type": "security",
                "context_requirements": {
                    "include_patterns": ["auth", "security", "password"],
                    "scan_sensitive": True,
                    "max_depth": 3
                }
            }
        )
        
        # Create sample context with sensitive files
        full_context = {
            "files": {
                "/project/src/auth/login.py": "# Login logic",
                "/project/src/auth/password.py": "# Password handling",
                "/project/src/auth/tokens.py": "# JWT tokens",
                "/project/src/utils/helpers.py": "# Generic helpers",
                "/project/config/database.yml": "# DB config",
                "/project/.env": "SECRET_KEY=xxx",
                "/project/.env.example": "SECRET_KEY=changeme"
            }
        }
        
        # Register custom security filter
        security_filter = ContextFilter(
            agent_type="security",
            include_patterns=["auth", "security", "password", "token"],
            exclude_patterns=[r"\.env\.example"],
            priority_keywords=["authentication", "security", "vulnerability"]
        )
        self.context_manager.register_custom_filter("security", security_filter)
        
        # Demonstrate filtering
        filtered_context = self.demonstrate_context_filtering(ticket, full_context)
        
        print(f"\n🔒 Security-focused context prepared")
        print(f"   Excluded example files: ✓")
        print(f"   Included auth modules: ✓")
    
    def run_multi_agent_demo(self):
        """Demo: Multiple agents working on related tickets."""
        print("\n" + "="*60)
        print("DEMO 3: Multi-Agent Coordination")
        print("="*60)
        
        # Create an epic
        epic = self.create_ticket(
            title="Implement user management system",
            description="Complete user management with CRUD operations",
            priority="high",
            labels=["epic", "feature"],
            metadata={
                "agent_types": ["engineer", "qa", "documentation"],
                "subtasks": []
            }
        )
        
        # Create subtask tickets
        subtasks = [
            {
                "title": "Design database schema",
                "agent_type": "data_engineer",
                "focus": ["database", "schema", "migrations"]
            },
            {
                "title": "Implement user CRUD API",
                "agent_type": "engineer",
                "focus": ["api", "endpoints", "validation"]
            },
            {
                "title": "Write integration tests",
                "agent_type": "qa",
                "focus": ["tests", "integration", "coverage"]
            },
            {
                "title": "Document API endpoints",
                "agent_type": "documentation",
                "focus": ["docs", "api", "examples"]
            }
        ]
        
        print(f"\n📋 Creating subtasks for epic {epic.id}:")
        
        for subtask_info in subtasks:
            subtask = self.create_ticket(
                title=subtask_info["title"],
                description=f"Part of {epic.id}",
                labels=["subtask"],
                metadata={
                    "parent_id": epic.id,
                    "agent_type": subtask_info["agent_type"],
                    "focus_areas": subtask_info["focus"]
                }
            )
            epic.metadata["subtasks"].append(subtask.id)
        
        print(f"\n🔄 Each agent will receive filtered context based on their ticket")
    
    def run_priority_based_demo(self):
        """Demo: How ticket priority affects context scope."""
        print("\n" + "="*60)
        print("DEMO 4: Priority-Based Context Filtering")
        print("="*60)
        
        priorities = ["critical", "high", "medium", "low"]
        
        for priority in priorities:
            ticket = self.create_ticket(
                title=f"{priority.capitalize()} priority task",
                description=f"A {priority} priority task",
                priority=priority,
                metadata={
                    "agent_type": "engineer",
                    "context_scope": {
                        "critical": "full",
                        "high": "extended",
                        "medium": "standard",
                        "low": "minimal"
                    }[priority]
                }
            )
            
            # Simulate different context sizes based on priority
            context_size = {
                "critical": 50,
                "high": 30,
                "medium": 20,
                "low": 10
            }[priority]
            
            print(f"   Context scope: {ticket.metadata['context_scope']}")
            print(f"   Estimated files: ~{context_size}")
    
    def _calculate_reduction(self, full_context: Dict, filtered_context: Dict) -> float:
        """Calculate the percentage reduction in context size."""
        full_size = len(json.dumps(full_context))
        filtered_size = len(json.dumps(filtered_context))
        
        if full_size == 0:
            return 0.0
        
        return ((full_size - filtered_size) / full_size) * 100
    
    async def run_async_demo(self):
        """Demo: Async ticket processing simulation."""
        print("\n" + "="*60)
        print("DEMO 5: Async Ticket Processing")
        print("="*60)
        
        # Create multiple tickets
        tickets = []
        for i in range(3):
            ticket = self.create_ticket(
                title=f"Async task {i+1}",
                metadata={
                    "agent_type": ["qa", "engineer", "documentation"][i],
                    "processing_time": 0.5 + i * 0.2
                }
            )
            tickets.append(ticket)
        
        print("\n⏳ Processing tickets asynchronously...")
        
        # Simulate async processing
        async def process_ticket(ticket):
            await asyncio.sleep(ticket.metadata["processing_time"])
            return f"Completed {ticket.id}"
        
        # Process all tickets concurrently
        results = await asyncio.gather(
            *[process_ticket(ticket) for ticket in tickets]
        )
        
        print("\n✅ All tickets processed:")
        for result in results:
            print(f"   - {result}")


def main():
    """Run the demonstration."""
    print("🎯 Ticket-First Operations Mode Demonstration")
    print("=" * 60)
    
    demo = TicketFirstDemo()
    
    # Run synchronous demos
    demo.run_documentation_task_demo()
    demo.run_security_audit_demo()
    demo.run_multi_agent_demo()
    demo.run_priority_based_demo()
    
    # Run async demo
    print("\n" + "="*60)
    asyncio.run(demo.run_async_demo())
    
    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("\nKey Takeaways:")
    print("1. Tickets define the context scope for operations")
    print("2. Agent type determines which files are included")
    print("3. Priority affects the amount of context provided")
    print("4. Multiple agents can work on related tickets with isolated context")
    print("5. Async processing enables concurrent ticket handling")


if __name__ == "__main__":
    main()