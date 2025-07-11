"""
Unit Tests for ClaudePMMemory Class

Comprehensive test suite for the ClaudePMMemory class including:
- Connection management
- Memory operations
- Error handling
- Retry logic
- Statistics tracking
- Project space management
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from claude_pm.services.claude_pm_memory import (
    ClaudePMMemory,
    ClaudePMConfig,
    MemoryCategory,
    MemoryResponse,
    create_claude_pm_memory,
    claude_pm_memory_context,
)


@pytest.fixture
def memory_config():
    """Create test configuration."""
    return ClaudePMConfig(
        host="localhost",
        port=8002,
        timeout=5,
        max_retries=2,
        retry_delay=0.1,
        connection_pool_size=2,
        enable_logging=False,
    )


@pytest.fixture
def memory_instance(memory_config):
    """Create ClaudePMMemory instance for testing."""
    return ClaudePMMemory(memory_config)


@pytest.fixture
def mock_session():
    """Mock aiohttp session."""
    session = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_connector():
    """Mock aiohttp connector."""
    connector = AsyncMock()
    connector.close = AsyncMock()
    return connector


class TestClaudePMMemoryInit:
    """Test ClaudePMMemory initialization."""

    def test_default_initialization(self):
        """Test initialization with default configuration."""
        memory = ClaudePMMemory()

        assert memory.config.host == "localhost"
        assert memory.config.port == 8002
        assert memory.config.timeout == 30
        assert memory.config.max_retries == 3
        assert memory.base_url == "http://localhost:8002"
        assert not memory.is_connected()
        assert memory.stats["operations_count"] == 0

    def test_custom_configuration(self, memory_config):
        """Test initialization with custom configuration."""
        memory = ClaudePMMemory(memory_config)

        assert memory.config.host == "localhost"
        assert memory.config.port == 8002
        assert memory.config.timeout == 5
        assert memory.config.max_retries == 2
        assert memory.config.retry_delay == 0.1

    def test_categories_initialization(self, memory_instance):
        """Test that memory categories are properly initialized."""
        assert MemoryCategory.PROJECT in memory_instance.categories
        assert MemoryCategory.PATTERN in memory_instance.categories
        assert MemoryCategory.TEAM in memory_instance.categories
        assert MemoryCategory.ERROR in memory_instance.categories

        # Check category descriptions
        assert (
            "Architectural decisions"
            in memory_instance.categories[MemoryCategory.PROJECT]["description"]
        )
        assert (
            "Successful solutions"
            in memory_instance.categories[MemoryCategory.PATTERN]["description"]
        )


class TestConnectionManagement:
    """Test connection management functionality."""

    @pytest.mark.asyncio
    async def test_successful_connection(self, memory_instance, mock_session, mock_connector):
        """Test successful connection to mem0AI service."""
        with (
            patch("aiohttp.TCPConnector", return_value=mock_connector),
            patch("aiohttp.ClientSession", return_value=mock_session),
        ):

            # Mock successful health check
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await memory_instance.connect()

            assert result is True
            assert memory_instance.is_connected()
            assert memory_instance._session == mock_session
            assert memory_instance._connection_pool == mock_connector

    @pytest.mark.asyncio
    async def test_failed_connection(self, memory_instance):
        """Test failed connection to mem0AI service."""
        with (
            patch("aiohttp.TCPConnector") as mock_connector_class,
            patch("aiohttp.ClientSession") as mock_session_class,
        ):

            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Mock failed health check
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await memory_instance.connect()

            assert result is False
            assert not memory_instance.is_connected()

    @pytest.mark.asyncio
    async def test_disconnect(self, memory_instance, mock_session, mock_connector):
        """Test disconnection from mem0AI service."""
        # Set up connected state
        memory_instance._session = mock_session
        memory_instance._connection_pool = mock_connector
        memory_instance._connected = True

        await memory_instance.disconnect()

        mock_session.close.assert_called_once()
        mock_connector.close.assert_called_once()
        assert not memory_instance.is_connected()
        assert memory_instance._session is None
        assert memory_instance._connection_pool is None

    @pytest.mark.asyncio
    async def test_health_check_success(self, memory_instance, mock_session):
        """Test successful health check."""
        memory_instance._session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await memory_instance._health_check()

        assert result is True
        mock_session.get.assert_called_with("http://localhost:8002/health")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, memory_instance, mock_session):
        """Test failed health check."""
        memory_instance._session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await memory_instance._health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_ensure_connection_when_connected(self, memory_instance):
        """Test ensure_connection when already connected."""
        with patch.object(memory_instance, "is_connected", return_value=True):
            result = await memory_instance.ensure_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_connection_when_disconnected(self, memory_instance):
        """Test ensure_connection when disconnected."""
        with (
            patch.object(memory_instance, "is_connected", return_value=False),
            patch.object(memory_instance, "connect", return_value=True) as mock_connect,
        ):

            result = await memory_instance.ensure_connection()

            assert result is True
            mock_connect.assert_called_once()


class TestMemoryOperations:
    """Test core memory operations."""

    @pytest.mark.asyncio
    async def test_create_project_memory_space_success(self, memory_instance, mock_session):
        """Test successful project memory space creation."""
        memory_instance._session = mock_session

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.create_project_memory_space("test_project")

        assert response.success is True
        assert "test_project" in str(mock_session.post.call_args)
        assert memory_instance.stats["memory_spaces_created"] == 1

    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_instance, mock_session):
        """Test successful memory storage."""
        memory_instance._session = mock_session

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"id": "test-memory-id"}
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.store_memory(
                category=MemoryCategory.PROJECT,
                content="Test memory content",
                project_name="test_project",
                tags=["test"],
            )

        assert response.success is True
        assert response.memory_id == "test-memory-id"
        assert memory_instance.stats["memories_stored"] == 1

    @pytest.mark.asyncio
    async def test_store_memory_invalid_category(self, memory_instance, mock_session):
        """Test memory storage with invalid category."""
        memory_instance._session = mock_session

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.store_memory(
                category="invalid_category",  # This will cause validation error
                content="Test content",
                project_name="test_project",
            )

        assert response.success is False
        assert "Invalid category" in response.error

    @pytest.mark.asyncio
    async def test_retrieve_memories_success(self, memory_instance, mock_session):
        """Test successful memory retrieval."""
        memory_instance._session = mock_session

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "memories": [{"id": "1", "content": "Memory 1"}, {"id": "2", "content": "Memory 2"}]
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.retrieve_memories(
                category=MemoryCategory.PROJECT, query="test query", project_filter="test_project"
            )

        assert response.success is True
        assert response.data["count"] == 2
        assert memory_instance.stats["memories_retrieved"] == 2

    @pytest.mark.asyncio
    async def test_update_memory_success(self, memory_instance, mock_session):
        """Test successful memory update."""
        memory_instance._session = mock_session

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.put.return_value.__aenter__.return_value = mock_response

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.update_memory(
                memory_id="test-id", content="Updated content"
            )

        assert response.success is True
        assert response.data["memory_id"] == "test-id"

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, memory_instance, mock_session):
        """Test successful memory deletion."""
        memory_instance._session = mock_session

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_session.delete.return_value.__aenter__.return_value = mock_response

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.delete_memory("test-id")

        assert response.success is True
        assert response.data["status"] == "deleted"


class TestHighLevelMethods:
    """Test high-level convenience methods."""

    @pytest.mark.asyncio
    async def test_store_project_decision(self, memory_instance):
        """Test storing a project decision."""
        with patch.object(memory_instance, "store_memory") as mock_store:
            mock_store.return_value = MemoryResponse(success=True, memory_id="decision-id")

            response = await memory_instance.store_project_decision(
                project_name="test_project",
                decision="Use FastAPI",
                context="Need async support",
                reasoning="Better performance",
                alternatives=["Flask", "Django"],
                tags=["api"],
            )

        assert response.success is True
        mock_store.assert_called_once()

        # Check the call arguments
        call_args = mock_store.call_args
        assert call_args[1]["category"] == MemoryCategory.PROJECT
        assert "Use FastAPI" in call_args[1]["content"]
        assert "decision" in call_args[1]["tags"]


class TestRetryLogic:
    """Test retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, memory_instance, mock_session):
        """Test retry logic on network errors."""
        memory_instance._session = mock_session

        # First attempt fails, second succeeds
        side_effects = [
            aiohttp.ClientConnectorError(connection_key=None, os_error=None),
            AsyncMock(status=201, json=AsyncMock(return_value={"id": "test-id"})),
        ]

        mock_session.post.return_value.__aenter__.side_effect = side_effects

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.create_project_memory_space("test_project")

        assert response.success is True
        assert mock_session.post.call_count == 2  # One retry

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, memory_instance, mock_session):
        """Test behavior when max retries are exceeded."""
        memory_instance._session = mock_session

        # All attempts fail
        mock_session.post.return_value.__aenter__.side_effect = aiohttp.ClientConnectorError(
            connection_key=None, os_error=None
        )

        with patch.object(memory_instance, "ensure_connection", return_value=True):
            response = await memory_instance.create_project_memory_space("test_project")

        assert response.success is False
        assert "failed after" in response.error
        assert mock_session.post.call_count == memory_instance.config.max_retries


class TestSynchronousMethods:
    """Test synchronous wrapper methods."""

    def test_create_project_memory_space_sync(self, memory_instance):
        """Test synchronous project memory space creation."""
        with patch.object(memory_instance, "create_project_memory_space") as mock_async:
            mock_async.return_value = MemoryResponse(success=True)

            response = memory_instance.create_project_memory_space_sync("test_project")

        assert response.success is True
        mock_async.assert_called_once_with("test_project", "", None)

    def test_store_memory_sync(self, memory_instance):
        """Test synchronous memory storage."""
        with patch.object(memory_instance, "store_memory") as mock_async:
            mock_async.return_value = MemoryResponse(success=True, memory_id="test-id")

            response = memory_instance.store_memory_sync(MemoryCategory.PROJECT, "test content")

        assert response.success is True
        mock_async.assert_called_once()


class TestStatistics:
    """Test statistics tracking."""

    def test_update_stats_success(self, memory_instance):
        """Test statistics update for successful operation."""
        memory_instance._update_stats(True, 0.5)

        assert memory_instance.stats["operations_count"] == 1
        assert memory_instance.stats["successful_operations"] == 1
        assert memory_instance.stats["failed_operations"] == 0
        assert memory_instance.stats["avg_response_time"] == 0.5

    def test_update_stats_failure(self, memory_instance):
        """Test statistics update for failed operation."""
        memory_instance._update_stats(False, 1.0)

        assert memory_instance.stats["operations_count"] == 1
        assert memory_instance.stats["successful_operations"] == 0
        assert memory_instance.stats["failed_operations"] == 1
        assert memory_instance.stats["avg_response_time"] == 1.0

    def test_get_statistics(self, memory_instance):
        """Test getting comprehensive statistics."""
        memory_instance._update_stats(True, 0.5)
        memory_instance._update_stats(False, 1.0)

        stats = memory_instance.get_statistics()

        assert stats["operations_count"] == 2
        assert stats["successful_operations"] == 1
        assert stats["failed_operations"] == 1
        assert stats["success_rate"] == 50.0
        assert "categories_supported" in stats
        assert "config" in stats


class TestFactoryFunctions:
    """Test factory functions and context managers."""

    def test_create_claude_pm_memory(self):
        """Test factory function for creating ClaudePMMemory."""
        memory = create_claude_pm_memory(host="test-host", port=9000, timeout=10)

        assert isinstance(memory, ClaudePMMemory)
        assert memory.config.host == "test-host"
        assert memory.config.port == 9000
        assert memory.config.timeout == 10

    @pytest.mark.asyncio
    async def test_claude_pm_memory_context(self):
        """Test async context manager."""
        with (
            patch("claude_pm.services.claude_pm_memory.ClaudePMMemory.connect") as mock_connect,
            patch(
                "claude_pm.services.claude_pm_memory.ClaudePMMemory.disconnect"
            ) as mock_disconnect,
        ):

            mock_connect.return_value = True

            async with claude_pm_memory_context() as memory:
                assert isinstance(memory, ClaudePMMemory)

            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, memory_instance):
        """Test handling of connection errors."""
        with patch("aiohttp.ClientSession", side_effect=Exception("Connection failed")):
            result = await memory_instance.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_operation_without_connection(self, memory_instance):
        """Test operations when not connected."""
        # Ensure we're not connected
        memory_instance._connected = False
        memory_instance._session = None

        response = await memory_instance.store_memory(MemoryCategory.PROJECT, "test content")

        assert response.success is False
        assert "Failed to establish connection" in response.error


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
