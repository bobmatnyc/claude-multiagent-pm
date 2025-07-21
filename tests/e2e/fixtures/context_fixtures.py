"""
Context Fixtures for E2E Testing

Provides pre-configured contexts and data structures for testing context management.
"""

from typing import Dict, Any, List
from datetime import datetime
import json


class ContextFixtures:
    """Collection of context fixtures for testing."""
    
    @staticmethod
    def minimal_context() -> Dict[str, Any]:
        """Create a minimal valid context."""
        return {
            "project_info": {
                "name": "test-project",
                "version": "1.0.0"
            }
        }
    
    @staticmethod
    def full_project_context() -> Dict[str, Any]:
        """Create a complete project context with all common fields."""
        return {
            "project_info": {
                "name": "full-test-project",
                "version": "2.0.0",
                "description": "A complete test project",
                "path": "/test/project/path",
                "created": "2025-07-01T00:00:00Z",
                "modified": "2025-07-19T00:00:00Z"
            },
            "files": {
                "README.md": {
                    "content": "# Test Project\nThis is a test project.",
                    "type": "markdown",
                    "size": 50
                },
                "src/main.py": {
                    "content": "def main():\n    print('Hello World')",
                    "type": "python",
                    "size": 40
                },
                "tests/test_main.py": {
                    "content": "def test_main():\n    assert True",
                    "type": "python",
                    "size": 35
                },
                "package.json": {
                    "content": '{"name": "test", "version": "2.0.0"}',
                    "type": "json",
                    "size": 40
                }
            },
            "git_info": {
                "branch": "main",
                "commit": "abc123def456",
                "status": "clean",
                "remote": "origin",
                "ahead": 0,
                "behind": 0
            },
            "dependencies": {
                "python": ["pytest>=7.0.0", "requests>=2.28.0"],
                "npm": ["jest@29.0.0", "webpack@5.0.0"]
            },
            "environment": {
                "python_version": "3.11.0",
                "node_version": "18.0.0",
                "os": "darwin",
                "architecture": "arm64"
            }
        }
    
    @staticmethod
    def agent_specific_contexts() -> Dict[str, Dict[str, Any]]:
        """Create contexts tailored for specific agent types."""
        return {
            "documentation": {
                "docs": {
                    "README.md": {"content": "# Main README"},
                    "docs/API.md": {"content": "# API Reference"},
                    "docs/GUIDE.md": {"content": "# User Guide"}
                },
                "project_info": {"name": "doc-project", "version": "1.0.0"},
                "recent_changes": ["Added API docs", "Updated user guide"]
            },
            "qa": {
                "test_files": {
                    "test_unit.py": {"content": "unit tests"},
                    "test_integration.py": {"content": "integration tests"}
                },
                "test_results": {
                    "unit": {"passed": 50, "failed": 0},
                    "integration": {"passed": 20, "failed": 2}
                },
                "coverage": {
                    "overall": 85.5,
                    "uncovered_files": ["utils.py", "helpers.py"]
                }
            },
            "security": {
                "scan_results": {
                    "vulnerabilities": [],
                    "warnings": ["Outdated dependency: requests"],
                    "last_scan": "2025-07-19T10:00:00Z"
                },
                "security_files": {
                    ".env": {"content": "# Environment variables"},
                    "security.yml": {"content": "security: config"}
                }
            },
            "engineer": {
                "source_files": {
                    "main.py": {"content": "# Main application"},
                    "utils.py": {"content": "# Utility functions"},
                    "models.py": {"content": "# Data models"}
                },
                "build_config": {
                    "language": "python",
                    "framework": "fastapi",
                    "build_tool": "poetry"
                }
            },
            "ops": {
                "deployment_config": {
                    "docker-compose.yml": {"content": "version: '3.8'"},
                    "Dockerfile": {"content": "FROM python:3.11"},
                    ".github/workflows/ci.yml": {"content": "name: CI"}
                },
                "infrastructure": {
                    "provider": "aws",
                    "region": "us-east-1",
                    "services": ["ec2", "rds", "s3"]
                }
            }
        }
    
    @staticmethod
    def error_context() -> Dict[str, Any]:
        """Create a context representing an error state."""
        return {
            "status": "error",
            "error": {
                "type": "RuntimeError",
                "message": "Failed to complete operation",
                "traceback": "Traceback (most recent call last)...",
                "timestamp": datetime.now().isoformat()
            },
            "failed_operation": {
                "type": "deployment",
                "target": "production",
                "stage": "pre-deployment-validation"
            }
        }
    
    @staticmethod
    def multi_agent_workflow_context() -> Dict[str, Any]:
        """Create a context for testing multi-agent workflows."""
        return {
            "workflow": {
                "id": "workflow-123",
                "type": "feature-release",
                "stages": ["development", "testing", "documentation", "release"]
            },
            "current_stage": "testing",
            "completed_stages": {
                "development": {
                    "agent": "engineer",
                    "status": "success",
                    "output": {"files_changed": 10, "tests_added": 5}
                }
            },
            "pending_stages": ["documentation", "release"],
            "shared_artifacts": {
                "changelog_draft": "## Changes\n- Feature X\n- Bug fix Y",
                "test_report": "All tests passing"
            }
        }
    
    @staticmethod
    def large_context(file_count: int = 100) -> Dict[str, Any]:
        """Create a large context for performance testing."""
        return {
            "project_info": {
                "name": "large-project",
                "file_count": file_count
            },
            "files": {
                f"file_{i}.py": {
                    "content": f"# File {i}\n" + ("x" * 1000),
                    "type": "python",
                    "size": 1000 + i
                }
                for i in range(file_count)
            },
            "metadata": {
                "total_size": file_count * 1000,
                "last_analysis": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def priority_context() -> Dict[str, Any]:
        """Create a context with priority items that should never be filtered."""
        return {
            # High priority items
            "critical_error": "Database connection lost",
            "security_alert": "Unauthorized access attempt detected",
            "system_status": "degraded",
            
            # Normal priority items
            "project_info": {"name": "test", "version": "1.0.0"},
            "recent_logs": ["Log entry 1", "Log entry 2"],
            
            # Low priority items
            "debug_info": {"verbose": True, "trace_level": 3},
            "historical_data": [{"date": "2025-01-01", "value": 100}] * 1000
        }
    
    @staticmethod
    def temporal_context() -> Dict[str, Any]:
        """Create a context with temporal/time-sensitive data."""
        now = datetime.now()
        return {
            "temporal_info": {
                "current_date": now.isoformat(),
                "sprint": {
                    "number": 42,
                    "start": "2025-07-15",
                    "end": "2025-07-29",
                    "days_remaining": 10
                },
                "release": {
                    "version": "2.0.0",
                    "target_date": "2025-08-01",
                    "freeze_date": "2025-07-25"
                }
            },
            "deadlines": {
                "feature_complete": "2025-07-22",
                "code_freeze": "2025-07-25",
                "release": "2025-08-01"
            },
            "time_sensitive_tasks": [
                {"task": "Complete API migration", "due": "2025-07-20"},
                {"task": "Security audit", "due": "2025-07-23"}
            ]
        }
    
    @staticmethod
    def hierarchical_context() -> Dict[str, Any]:
        """Create a context with hierarchical data for testing inheritance."""
        return {
            "global": {
                "organization": "TestCorp",
                "policies": ["security-first", "test-driven"]
            },
            "project": {
                "name": "test-app",
                "team": "alpha",
                "inherits": ["global.policies"]
            },
            "module": {
                "name": "auth",
                "owner": "john.doe",
                "inherits": ["project.team", "global.organization"]
            },
            "overrides": {
                "module.auth.timeout": 300,
                "project.test-app.debug": True
            }
        }
    
    @staticmethod
    def create_interaction_history(count: int = 5) -> List[Dict[str, Any]]:
        """Create a history of agent interactions."""
        interactions = []
        agents = ["documentation", "qa", "engineer", "ops"]
        
        for i in range(count):
            agent = agents[i % len(agents)]
            interactions.append({
                "timestamp": f"2025-07-19T10:{i:02d}:00Z",
                "agent": agent,
                "task": f"Task {i} for {agent}",
                "result": {
                    "status": "success" if i % 3 != 0 else "failure",
                    "duration": f"{10 + i}s",
                    "tokens_used": 500 + (i * 100)
                }
            })
        
        return interactions