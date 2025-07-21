"""
Test Data Generators for E2E Testing

Provides utilities to generate test data for various scenarios.
"""

from typing import Dict, Any, List, Optional
import random
import string
import json
from datetime import datetime, timedelta
from pathlib import Path


class TestDataGenerators:
    """Collection of test data generators."""
    
    @staticmethod
    def random_string(length: int = 10, prefix: str = "") -> str:
        """Generate a random string."""
        chars = string.ascii_lowercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_part}" if prefix else random_part
    
    @staticmethod
    def generate_agent_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate random agent data."""
        agent_types = ["documentation", "qa", "engineer", "research", "ops"]
        specializations = [
            ["documentation", "changelog"],
            ["testing", "validation"],
            ["implementation", "coding"],
            ["investigation", "analysis"],
            ["deployment", "operations"]
        ]
        
        agents = []
        for i in range(count):
            agent_type = agent_types[i % len(agent_types)]
            agents.append({
                "id": f"{agent_type}_{i}",
                "name": f"{agent_type}_agent_{i}",
                "type": "core" if i < 3 else "custom",
                "specializations": specializations[i % len(specializations)],
                "path": f".claude-pm/agents/{agent_type}_{i}.md",
                "last_modified": datetime.now().isoformat(),
                "priority": i + 1
            })
        
        return agents
    
    @staticmethod
    def generate_task_data(count: int = 10) -> List[Dict[str, Any]]:
        """Generate random task data."""
        task_types = ["implement", "test", "document", "research", "deploy"]
        statuses = ["pending", "in_progress", "completed", "failed"]
        
        tasks = []
        for i in range(count):
            task_type = random.choice(task_types)
            tasks.append({
                "id": f"task_{i}",
                "type": task_type,
                "title": f"{task_type.title()} task {i}",
                "description": f"This is a test {task_type} task number {i}",
                "status": random.choice(statuses),
                "assigned_agent": f"{task_type}_agent",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "priority": random.randint(1, 5)
            })
        
        return tasks
    
    @staticmethod
    def generate_test_project(base_path: Path, project_name: str = None) -> Path:
        """Generate a complete test project structure."""
        if project_name is None:
            project_name = TestDataGenerators.random_string(8, "test_project_")
        
        project_path = base_path / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        dirs = [
            ".claude-pm/agents/project-specific",
            ".claude-pm/memory",
            ".claude-pm/config",
            "src",
            "tests",
            "docs"
        ]
        
        for dir_path in dirs:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create CLAUDE.md
        claude_md = project_path / "CLAUDE.md"
        claude_md.write_text(f"""# {project_name} Configuration

This is an auto-generated test project.

## Project Structure
- Framework Version: 0.7.0
- Project Type: Test
- Generated: {datetime.now().isoformat()}
""")
        
        # Create sample files
        (project_path / "README.md").write_text(f"# {project_name}\n\nTest project for E2E testing.")
        (project_path / "src" / "main.py").write_text("# Main application file\nprint('Hello, World!')")
        (project_path / "tests" / "test_main.py").write_text("# Test file\ndef test_main():\n    pass")
        
        return project_path
    
    @staticmethod
    def generate_git_history(count: int = 5) -> List[Dict[str, Any]]:
        """Generate mock git commit history."""
        commit_types = ["feat", "fix", "docs", "test", "refactor"]
        commits = []
        
        for i in range(count):
            commit_type = random.choice(commit_types)
            commits.append({
                "hash": TestDataGenerators.random_string(7),
                "type": commit_type,
                "message": f"{commit_type}: Test commit {i}",
                "author": "Test User",
                "email": "test@example.com",
                "date": (datetime.now() - timedelta(hours=i)).isoformat(),
                "files_changed": random.randint(1, 10)
            })
        
        return commits
    
    @staticmethod
    def generate_test_results(test_count: int = 20) -> Dict[str, Any]:
        """Generate mock test results."""
        passed = int(test_count * 0.8)  # 80% pass rate
        failed = test_count - passed
        
        return {
            "summary": {
                "total": test_count,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "duration": f"{random.uniform(1.0, 10.0):.2f}s"
            },
            "tests": [
                {
                    "name": f"test_{i}",
                    "status": "passed" if i < passed else "failed",
                    "duration": f"{random.uniform(0.01, 0.5):.3f}s",
                    "error": None if i < passed else f"AssertionError: Test {i} failed"
                }
                for i in range(test_count)
            ]
        }
    
    @staticmethod
    def generate_memory_entries(count: int = 10) -> List[Dict[str, Any]]:
        """Generate mock memory system entries."""
        entry_types = ["task_execution", "agent_interaction", "error", "success"]
        agents = ["documentation", "qa", "engineer", "research", "ops"]
        
        entries = []
        for i in range(count):
            entry_type = random.choice(entry_types)
            agent = random.choice(agents)
            
            entries.append({
                "id": f"memory_{i}",
                "type": entry_type,
                "agent": agent,
                "timestamp": (datetime.now() - timedelta(minutes=i * 5)).isoformat(),
                "content": {
                    "task": f"Test task {i}",
                    "result": "success" if entry_type != "error" else "failure",
                    "details": f"Memory entry for {entry_type} by {agent}"
                },
                "tags": [entry_type, agent, f"test_{i}"]
            })
        
        return entries
    
    @staticmethod
    def generate_config_variations() -> List[Dict[str, Any]]:
        """Generate various configuration variations for testing."""
        return [
            {
                "name": "minimal",
                "config": {
                    "version": "0.7.0",
                    "framework": {"test_mode": True}
                }
            },
            {
                "name": "subprocess_mode",
                "config": {
                    "version": "0.7.0",
                    "orchestration": {
                        "mode": "subprocess",
                        "timeout": 60
                    }
                }
            },
            {
                "name": "local_mode",
                "config": {
                    "version": "0.7.0",
                    "orchestration": {
                        "mode": "local",
                        "async_enabled": True
                    }
                }
            },
            {
                "name": "performance_optimized",
                "config": {
                    "version": "0.7.0",
                    "agents": {
                        "discovery": {
                            "cache_enabled": True,
                            "cache_ttl": 3600
                        }
                    },
                    "performance": {
                        "optimization_level": "high"
                    }
                }
            }
        ]
    
    @staticmethod
    def generate_error_scenarios() -> List[Dict[str, Any]]:
        """Generate various error scenarios for testing."""
        return [
            {
                "name": "missing_config",
                "type": "FileNotFoundError",
                "message": "Configuration file not found",
                "context": {"file": ".claude-pm/config.json"}
            },
            {
                "name": "invalid_agent",
                "type": "AgentNotFoundError", 
                "message": "Agent not found in registry",
                "context": {"agent": "nonexistent_agent"}
            },
            {
                "name": "subprocess_timeout",
                "type": "TimeoutError",
                "message": "Subprocess execution timed out",
                "context": {"timeout": 30, "command": "long_running_task"}
            },
            {
                "name": "api_failure",
                "type": "APIError",
                "message": "API request failed",
                "context": {"service": "openai", "status_code": 500}
            },
            {
                "name": "permission_denied",
                "type": "PermissionError",
                "message": "Permission denied accessing directory",
                "context": {"path": "/restricted/path"}
            }
        ]
    
    @staticmethod
    def save_test_data(data: Any, filename: str, output_dir: Path):
        """Save generated test data to file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file