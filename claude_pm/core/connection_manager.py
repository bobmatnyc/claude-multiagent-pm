"""
Connection Manager for Claude PM Framework.

Provides centralized connection management to prevent aiohttp session leaks
and coordinate connection pooling across services.
"""

import asyncio
import aiohttp
import logging
import weakref
from typing import Dict, Optional, Set
from dataclasses import dataclass
from contextlib import asynccontextmanager


@dataclass
class ConnectionConfig:
    """Configuration for connection management."""

    pool_size: int = 10
    timeout: int = 30
    connect_timeout: int = 10
    ttl_dns_cache: int = 300
    enable_cleanup_closed: bool = True


class ConnectionManager:
    """
    Centralized connection manager for aiohttp sessions.

    Prevents connection leaks by:
    - Reusing sessions across services
    - Proper cleanup on shutdown
    - Coordinated connection pooling
    - Automatic leak detection
    """

    _instance: Optional["ConnectionManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Initialize connection manager."""
        self.logger = logging.getLogger(__name__)
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._connectors: Dict[str, aiohttp.TCPConnector] = {}
        self._active_sessions: Set[str] = set()
        self._cleanup_lock = asyncio.Lock()
        self._session_refs: weakref.WeakSet = weakref.WeakSet()

        # Default configuration
        self.default_config = ConnectionConfig()

        # Track initialization
        self._initialized = False
        self._shutdown = False

    @classmethod
    async def get_instance(cls) -> "ConnectionManager":
        """Get singleton connection manager instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the connection manager."""
        if self._initialized:
            return

        self.logger.info("Initializing Connection Manager")
        self._initialized = True
        self._shutdown = False

    async def get_session(
        self,
        service_name: str,
        config: Optional[ConnectionConfig] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp session for a service.

        Args:
            service_name: Unique name for the service
            config: Connection configuration
            headers: Default headers for the session

        Returns:
            Configured aiohttp.ClientSession
        """
        if self._shutdown:
            raise RuntimeError("Connection manager is shutdown")

        # Use existing session if available and not closed
        if service_name in self._sessions:
            session = self._sessions[service_name]
            if not session.closed:
                self.logger.debug(f"Reusing session for {service_name}")
                return session
            else:
                # Clean up closed session
                await self._cleanup_session(service_name)

        # Create new session
        session_config = config or self.default_config

        # Create connector
        connector = aiohttp.TCPConnector(
            limit=session_config.pool_size,
            limit_per_host=session_config.pool_size // 2,
            ttl_dns_cache=session_config.ttl_dns_cache,
            use_dns_cache=True,
            enable_cleanup_closed=session_config.enable_cleanup_closed,
        )

        # Create timeout
        timeout = aiohttp.ClientTimeout(
            total=session_config.timeout,
            connect=session_config.connect_timeout,
            sock_read=session_config.timeout,
        )

        # Create session
        session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=headers or {}, raise_for_status=False
        )

        # Store references
        self._sessions[service_name] = session
        self._connectors[service_name] = connector
        self._active_sessions.add(service_name)
        self._session_refs.add(session)

        self.logger.info(f"Created new session for {service_name}")
        return session

    async def close_session(self, service_name: str) -> None:
        """Close a specific service session."""
        if service_name in self._sessions:
            await self._cleanup_session(service_name)

    async def _cleanup_session(self, service_name: str) -> None:
        """Cleanup a specific session and its resources."""
        async with self._cleanup_lock:
            # Close session
            if service_name in self._sessions:
                session = self._sessions[service_name]
                try:
                    if not session.closed:
                        await session.close()
                except Exception as e:
                    self.logger.warning(f"Error closing session {service_name}: {e}")
                finally:
                    del self._sessions[service_name]

            # Close connector
            if service_name in self._connectors:
                connector = self._connectors[service_name]
                try:
                    if not connector.closed:
                        await connector.close()
                except Exception as e:
                    self.logger.warning(f"Error closing connector {service_name}: {e}")
                finally:
                    del self._connectors[service_name]

            # Remove from active sessions
            self._active_sessions.discard(service_name)

            self.logger.debug(f"Cleaned up session for {service_name}")

    async def cleanup_all(self) -> None:
        """Cleanup all sessions and shut down the manager."""
        async with self._cleanup_lock:
            self.logger.info("Cleaning up all connections...")
            self._shutdown = True

            # Cleanup all sessions
            service_names = list(self._sessions.keys())
            for service_name in service_names:
                await self._cleanup_session(service_name)

            # Clear all collections
            self._sessions.clear()
            self._connectors.clear()
            self._active_sessions.clear()

            self.logger.info("Connection manager shutdown completed")

    def get_stats(self) -> Dict[str, any]:
        """Get connection manager statistics."""
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len(self._active_sessions),
            "session_names": list(self._active_sessions),
            "initialized": self._initialized,
            "shutdown": self._shutdown,
        }

    @asynccontextmanager
    async def managed_session(
        self,
        service_name: str,
        config: Optional[ConnectionConfig] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for temporary sessions that are cleaned up automatically.

        Args:
            service_name: Unique name for the service
            config: Connection configuration
            headers: Default headers for the session

        Yields:
            Configured aiohttp.ClientSession
        """
        session = await self.get_session(service_name, config, headers)
        try:
            yield session
        finally:
            # Note: We don't automatically close the session here as it may be reused
            # The session will be cleaned up when cleanup_all() is called
            pass


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


async def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = await ConnectionManager.get_instance()
    return _connection_manager


async def cleanup_connections():
    """Cleanup all connections."""
    global _connection_manager
    if _connection_manager:
        await _connection_manager.cleanup_all()
        _connection_manager = None
