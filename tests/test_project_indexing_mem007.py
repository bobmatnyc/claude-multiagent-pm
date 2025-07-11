#!/usr/bin/env python3
"""
Test Suite for MEM-007 Project Indexing System

Tests the project indexer, memory manager, and CLI integration
to ensure the intelligent project memory indexing system works correctly.
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from claude_pm.services.project_indexer import (
    ProjectIndexer,
    ProjectMetadata,
    ProjectType,
    TechStack,
)
from claude_pm.services.project_memory_manager import ProjectMemoryManager, SearchQuery, SearchMode
from claude_pm.services.project_index_daemon import ProjectIndexDaemon, DaemonConfig


class TestProjectIndexer:
    """Test the ProjectIndexer service."""

    @pytest.fixture
    async def mock_indexer(self):
        """Create a mock project indexer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            indexer = ProjectIndexer(temp_dir)

            # Mock the memory connection
            indexer.memory = AsyncMock()
            indexer.memory.is_connected.return_value = True
            indexer.memory.create_project_memory_space = AsyncMock(
                return_value=MagicMock(success=True)
            )
            indexer.memory.store_memory = AsyncMock(
                return_value=MagicMock(success=True, memory_id="test-id")
            )

            yield indexer, Path(temp_dir)

    def test_project_metadata_creation(self):
        """Test ProjectMetadata dataclass creation."""
        metadata = ProjectMetadata(
            name="test-project",
            path="/test/path",
            type=ProjectType.WEB_APP,
            tech_stack=TechStack.TYPESCRIPT_REACT,
            description="Test project",
        )

        assert metadata.name == "test-project"
        assert metadata.type == ProjectType.WEB_APP
        assert metadata.tech_stack == TechStack.TYPESCRIPT_REACT
        assert isinstance(metadata.to_dict(), dict)
        assert metadata.to_dict()["name"] == "test-project"

    @pytest.mark.asyncio
    async def test_indexer_initialization(self, mock_indexer):
        """Test indexer initialization."""
        indexer, temp_dir = mock_indexer

        # Test initialization
        result = await indexer.initialize()
        assert result is True
        assert indexer.memory is not None

    @pytest.mark.asyncio
    async def test_package_json_analysis(self, mock_indexer):
        """Test package.json file analysis."""
        indexer, temp_dir = mock_indexer

        # Create test project structure
        project_dir = temp_dir / "test-react-app"
        project_dir.mkdir()

        # Create package.json
        package_json = {
            "name": "test-react-app",
            "description": "A test React application",
            "dependencies": {"react": "^18.0.0", "next": "^13.0.0", "typescript": "^5.0.0"},
            "devDependencies": {"typescript": "^5.0.0"},
            "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
        }

        with open(project_dir / "package.json", "w") as f:
            json.dump(package_json, f)

        # Test metadata extraction
        metadata = await indexer._extract_project_metadata(project_dir)

        assert metadata is not None
        assert metadata.name == "test-react-app"
        assert metadata.description == "A test React application"
        assert "react" in metadata.dependencies
        assert "next" in metadata.dependencies
        assert "TypeScript" in metadata.languages
        assert "React" in metadata.frameworks
        assert "Next.js" in metadata.frameworks

    @pytest.mark.asyncio
    async def test_tech_stack_detection(self, mock_indexer):
        """Test technology stack detection."""
        indexer, temp_dir = mock_indexer

        # Create TypeScript Next.js project
        project_dir = temp_dir / "nextjs-app"
        project_dir.mkdir()

        # Create indicative files
        (project_dir / "next.config.js").touch()
        (project_dir / "next-env.d.ts").touch()
        (project_dir / "app").mkdir()

        metadata = ProjectMetadata(
            name="nextjs-app",
            path=str(project_dir),
            type=ProjectType.UNKNOWN,
            tech_stack=TechStack.UNKNOWN,
            description="",
        )

        # Test tech stack detection
        indexer._detect_tech_stack(project_dir, metadata)

        assert metadata.tech_stack == TechStack.TYPESCRIPT_NEXTJS

    @pytest.mark.asyncio
    async def test_project_type_detection(self, mock_indexer):
        """Test project type detection."""
        indexer, temp_dir = mock_indexer

        # Create CLI tool project
        project_dir = temp_dir / "cli-tool"
        project_dir.mkdir()
        (project_dir / "bin").mkdir()

        metadata = ProjectMetadata(
            name="cli-tool",
            path=str(project_dir),
            type=ProjectType.UNKNOWN,
            tech_stack=TechStack.UNKNOWN,
            description="",
        )

        # Test project type detection
        indexer._detect_project_type(project_dir, metadata)

        assert metadata.type == ProjectType.CLI_TOOL

    @pytest.mark.asyncio
    async def test_claude_md_analysis(self, mock_indexer):
        """Test CLAUDE.md file analysis."""
        indexer, temp_dir = mock_indexer

        project_dir = temp_dir / "documented-project"
        project_dir.mkdir()

        claude_md_content = """# Project Configuration - Test Project

## Project Overview

This is a comprehensive TypeScript CLI tool for testing purposes. 
It provides automated analysis and comprehensive reporting capabilities.

## Features

- Multi-provider support
- CLI interface with multiple commands
- Comprehensive test coverage
- Docker containerization support
- GitHub Actions CI/CD integration

## Architecture Decisions

- Chose TypeScript for type safety and developer experience
- Implemented modular architecture for extensibility
- Used Biome for fast linting and formatting
"""

        with open(project_dir / "CLAUDE.md", "w") as f:
            f.write(claude_md_content)

        metadata = ProjectMetadata(
            name="documented-project",
            path=str(project_dir),
            type=ProjectType.UNKNOWN,
            tech_stack=TechStack.UNKNOWN,
            description="",
        )

        # Test CLAUDE.md analysis
        await indexer._analyze_claude_md(project_dir / "CLAUDE.md", metadata)

        assert "comprehensive TypeScript CLI tool" in metadata.description
        assert len(metadata.features) > 0
        assert "Multi-provider support" in metadata.features
        assert len(metadata.architecture_decisions) > 0


class TestProjectMemoryManager:
    """Test the ProjectMemoryManager service."""

    @pytest.fixture
    async def mock_memory_manager(self):
        """Create a mock memory manager."""
        manager = ProjectMemoryManager()

        # Mock the memory connection
        manager.memory = AsyncMock()
        manager.memory.is_connected.return_value = True

        # Mock memory responses
        manager.memory.retrieve_memories = AsyncMock(
            return_value=MagicMock(
                success=True,
                data={
                    "memories": [
                        {
                            "id": "test-memory-id",
                            "metadata": {
                                "project_data": {
                                    "name": "test-project",
                                    "type": "web_app",
                                    "tech_stack": "typescript_react",
                                    "description": "Test project description",
                                    "languages": ["TypeScript", "JavaScript"],
                                    "frameworks": ["React", "Next.js"],
                                    "features": ["Component architecture", "Test suite"],
                                    "tags": ["web_app", "typescript_react", "react"],
                                }
                            },
                        }
                    ]
                },
            )
        )

        yield manager

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, mock_memory_manager):
        """Test memory manager initialization."""
        manager = mock_memory_manager

        result = await manager.initialize()
        assert result is True
        assert manager.memory is not None

    @pytest.mark.asyncio
    async def test_get_project_info(self, mock_memory_manager):
        """Test getting project information."""
        manager = mock_memory_manager
        await manager.initialize()

        project_info = await manager.get_project_info("test-project")

        assert project_info is not None
        assert project_info["name"] == "test-project"
        assert project_info["type"] == "web_app"
        assert project_info["tech_stack"] == "typescript_react"
        assert "cache_hit" in project_info
        assert "retrieved_at" in project_info

    def test_search_query_creation(self):
        """Test SearchQuery creation and cache key generation."""
        query = SearchQuery(
            query="typescript react",
            mode=SearchMode.HYBRID,
            filters={"project_type": "web_app"},
            limit=10,
        )

        assert query.query == "typescript react"
        assert query.mode == SearchMode.HYBRID
        assert query.filters["project_type"] == "web_app"
        assert isinstance(query.to_cache_key(), str)

    @pytest.mark.asyncio
    async def test_search_projects(self, mock_memory_manager):
        """Test project search functionality."""
        manager = mock_memory_manager
        await manager.initialize()

        search_query = SearchQuery(query="typescript", mode=SearchMode.HYBRID, limit=5)

        results = await manager.search_projects(search_query)

        assert len(results) > 0
        assert hasattr(results[0], "project_name")
        assert hasattr(results[0], "relevance_score")
        assert hasattr(results[0], "match_reasons")

    def test_relevance_scoring(self, mock_memory_manager):
        """Test relevance score calculation."""
        manager = mock_memory_manager

        project_data = {
            "name": "react-typescript-app",
            "description": "A React application built with TypeScript",
            "tech_stack": "typescript_react",
            "languages": ["TypeScript", "JavaScript"],
            "frameworks": ["React"],
            "features": ["Component architecture"],
            "tags": ["web_app", "typescript", "react"],
        }

        score, reasons = manager._calculate_relevance_score(
            project_data, "react typescript", "react typescript javascript"
        )

        assert score > 0.0
        assert score <= 1.0
        assert len(reasons) > 0
        assert any("react" in reason.lower() for reason in reasons)

    @pytest.mark.asyncio
    async def test_project_recommendations(self, mock_memory_manager):
        """Test project recommendation system."""
        manager = mock_memory_manager
        await manager.initialize()

        recommendations = await manager.get_project_recommendations("test-project", limit=3)

        # Should return recommendations based on mocked data
        assert isinstance(recommendations, list)

    def test_performance_stats(self, mock_memory_manager):
        """Test performance statistics tracking."""
        manager = mock_memory_manager

        stats = manager.get_performance_stats()

        assert "queries_total" in stats
        assert "cache_hit_rate" in stats
        assert "avg_response_time_ms" in stats
        assert "memory_connected" in stats


class TestProjectIndexDaemon:
    """Test the ProjectIndexDaemon service."""

    @pytest.fixture
    def mock_daemon(self):
        """Create a mock daemon."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DaemonConfig(
                scan_interval_minutes=1,  # Short intervals for testing
                quick_scan_interval_minutes=1,
                health_check_interval_minutes=1,
            )

            daemon = ProjectIndexDaemon(temp_dir, config)

            # Mock the services
            daemon.indexer = AsyncMock()
            daemon.indexer.initialize = AsyncMock(return_value=True)
            daemon.indexer.scan_and_index_all = AsyncMock(
                return_value={
                    "projects_found": 2,
                    "projects_indexed": 1,
                    "projects_updated": 1,
                    "projects_skipped": 0,
                    "performance": {"scan_time_seconds": 0.5},
                }
            )
            daemon.indexer.cleanup = AsyncMock()

            daemon.memory_manager = AsyncMock()
            daemon.memory_manager.initialize = AsyncMock(return_value=True)
            daemon.memory_manager.get_performance_stats = AsyncMock(
                return_value={"memory_connected": True}
            )
            daemon.memory_manager.cleanup = AsyncMock()

            yield daemon, Path(temp_dir)

    def test_daemon_config_creation(self):
        """Test daemon configuration creation."""
        config = DaemonConfig(
            scan_interval_minutes=15, quick_scan_interval_minutes=3, health_check_interval_minutes=5
        )

        assert config.scan_interval_minutes == 15
        assert config.quick_scan_interval_minutes == 3
        assert config.health_check_interval_minutes == 5
        assert isinstance(config.watch_extensions, set)
        assert isinstance(config.ignore_patterns, set)

    @pytest.mark.asyncio
    async def test_daemon_initialization(self, mock_daemon):
        """Test daemon initialization."""
        daemon, temp_dir = mock_daemon

        # Mock the main loop to avoid infinite running
        daemon._main_loop = AsyncMock()

        await daemon.start()

        # Verify services were initialized
        daemon.indexer.initialize.assert_called_once()
        daemon.memory_manager.initialize.assert_called_once()
        daemon._main_loop.assert_called_once()

    def test_daemon_status(self, mock_daemon):
        """Test daemon status reporting."""
        daemon, temp_dir = mock_daemon

        status = daemon.get_daemon_status()

        assert "running" in status
        assert "stats" in status
        assert "config" in status
        assert "pending_projects" in status
        assert "projects_tracked" in status

    @pytest.mark.asyncio
    async def test_checksum_calculation(self, mock_daemon):
        """Test project checksum calculation."""
        daemon, temp_dir = mock_daemon

        # Create test project
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()

        # Create some test files
        (project_dir / "README.md").write_text("Test readme")
        (project_dir / "package.json").write_text('{"name": "test"}')

        checksum = await daemon._calculate_project_checksum(project_dir)

        assert isinstance(checksum, str)
        assert len(checksum) > 0

        # Checksum should be consistent
        checksum2 = await daemon._calculate_project_checksum(project_dir)
        assert checksum == checksum2

    @pytest.mark.asyncio
    async def test_force_scan(self, mock_daemon):
        """Test force scan functionality."""
        daemon, temp_dir = mock_daemon

        # Mock the scan method
        daemon._perform_full_scan = AsyncMock()

        result = await daemon.force_scan()

        assert result["status"] == "completed"
        assert "timestamp" in result
        daemon._perform_full_scan.assert_called_once()


class TestCLIIntegration:
    """Test CLI command integration."""

    @patch("claude_pm.services.project_indexer.create_project_indexer")
    @patch("claude_pm.services.project_memory_manager.create_project_memory_manager")
    def test_cli_imports(self, mock_memory_manager, mock_indexer):
        """Test that CLI can import the required services."""
        # This test ensures the imports work correctly
        from claude_pm.services.project_indexer import create_project_indexer
        from claude_pm.services.project_memory_manager import (
            create_project_memory_manager,
            SearchQuery,
            SearchMode,
        )

        assert create_project_indexer is not None
        assert create_project_memory_manager is not None
        assert SearchQuery is not None
        assert SearchMode is not None


class TestSystemIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test the complete indexing and retrieval workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock project structure
            project_dir = temp_path / "test-integration-project"
            project_dir.mkdir()

            # Create package.json
            package_json = {
                "name": "test-integration-project",
                "description": "Integration test project",
                "dependencies": {"react": "^18.0.0"},
                "scripts": {"dev": "react-scripts start"},
            }

            with open(project_dir / "package.json", "w") as f:
                json.dump(package_json, f)

            # Create CLAUDE.md
            claude_md = """# Test Integration Project

## Project Overview
This is a test project for integration testing.

## Features
- React components
- Integration testing
"""

            with open(project_dir / "CLAUDE.md", "w") as f:
                f.write(claude_md)

            # Test indexer
            indexer = ProjectIndexer(str(temp_path))

            # Mock memory for testing
            indexer.memory = AsyncMock()
            indexer.memory.is_connected.return_value = True
            indexer.memory.create_project_memory_space = AsyncMock(
                return_value=MagicMock(success=True)
            )
            indexer.memory.store_memory = AsyncMock(
                return_value=MagicMock(success=True, memory_id="test-id")
            )

            await indexer.initialize()

            # Test metadata extraction
            metadata = await indexer._extract_project_metadata(project_dir)

            assert metadata is not None
            assert metadata.name == "test-integration-project"
            assert metadata.description == "Integration test project"
            assert "React" in metadata.frameworks
            assert len(metadata.features) > 0

            await indexer.cleanup()


if __name__ == "__main__":
    # Run tests
    print("🧪 Running MEM-007 Project Indexing Tests...")

    # Simple test runner for basic verification
    import asyncio

    async def run_basic_tests():
        """Run basic tests without pytest."""
        print("✅ Testing ProjectMetadata creation...")
        metadata = ProjectMetadata(
            name="test",
            path="/test",
            type=ProjectType.WEB_APP,
            tech_stack=TechStack.TYPESCRIPT_REACT,
            description="Test",
        )
        assert metadata.name == "test"
        print("   ✓ ProjectMetadata creation works")

        print("✅ Testing SearchQuery creation...")
        query = SearchQuery(query="test", mode=SearchMode.HYBRID)
        assert query.query == "test"
        assert isinstance(query.to_cache_key(), str)
        print("   ✓ SearchQuery creation works")

        print("✅ Testing DaemonConfig creation...")
        config = DaemonConfig(scan_interval_minutes=10)
        assert config.scan_interval_minutes == 10
        print("   ✓ DaemonConfig creation works")

        print(
            "\n🎉 Basic tests passed! Run 'pytest tests/test_project_indexing_mem007.py' for full test suite."
        )

    asyncio.run(run_basic_tests())
