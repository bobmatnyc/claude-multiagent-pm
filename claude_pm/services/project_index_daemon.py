#!/usr/bin/env python3
"""
Project Index Daemon - MEM-007 Background Service

This daemon runs in the background to automatically keep the project index
up-to-date with change detection and scheduled refreshes.

Features:
- File system monitoring for automatic index updates
- Scheduled background indexing
- Change detection and incremental updates
- Performance optimization and throttling
- Health monitoring and error recovery
- Graceful shutdown and resource management
"""

import asyncio
import logging
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set
from dataclasses import dataclass, field

from ..core.logging_config import get_logger
from ..services.project_indexer import create_project_indexer
from ..services.project_memory_manager import create_project_memory_manager

logger = get_logger(__name__)


@dataclass
class DaemonConfig:
    """Configuration for the project index daemon."""

    # Monitoring settings
    scan_interval_minutes: int = 30  # Full scan every 30 minutes
    quick_scan_interval_minutes: int = 5  # Quick check every 5 minutes
    max_concurrent_indexing: int = 3  # Maximum concurrent project indexing

    # Performance settings
    throttle_delay_seconds: float = 0.1  # Delay between operations
    max_memory_usage_mb: int = 500  # Maximum memory usage

    # Health settings
    health_check_interval_minutes: int = 10
    max_consecutive_errors: int = 5
    error_backoff_minutes: int = 2

    # File watching settings
    watch_enabled: bool = True
    watch_extensions: Set[str] = field(
        default_factory=lambda: {
            ".md",
            ".json",
            ".toml",
            ".txt",
            ".yml",
            ".yaml",
            ".py",
            ".js",
            ".ts",
        }
    )
    ignore_patterns: Set[str] = field(
        default_factory=lambda: {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            "target",
            ".next",
            "coverage",
        }
    )


class ProjectIndexDaemon:
    """
    Background daemon for automated project indexing.

    Monitors the managed projects directory and automatically updates
    the project index when changes are detected.
    """

    def __init__(self, managed_path: Optional[str] = None, config: Optional[DaemonConfig] = None):
        """Initialize the daemon."""
        self.managed_path = Path(managed_path or "/Users/masa/Projects/managed")
        self.config = config or DaemonConfig()

        # Service components
        self.indexer = create_project_indexer(str(self.managed_path))
        self.memory_manager = create_project_memory_manager()

        # Daemon state
        self.running = False
        self.shutdown_requested = False
        self.last_full_scan = None
        self.last_quick_scan = None
        self.last_health_check = None

        # Error tracking
        self.consecutive_errors = 0
        self.last_error_time = None

        # Performance tracking
        self.stats = {
            "daemon_started": None,
            "total_scans": 0,
            "total_projects_indexed": 0,
            "total_errors": 0,
            "avg_scan_time": 0.0,
            "memory_usage_mb": 0.0,
            "last_successful_scan": None,
        }

        # Change detection
        self.project_checksums: dict[str, str] = {}
        self.pending_projects: Set[str] = set()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    async def start(self) -> None:
        """Start the daemon."""
        try:
            logger.info("Starting Project Index Daemon...")

            # Initialize services
            if not await self.indexer.initialize():
                raise RuntimeError("Failed to initialize project indexer")

            if not await self.memory_manager.initialize():
                raise RuntimeError("Failed to initialize memory manager")

            logger.info("Project Index Daemon services initialized")

            # Set daemon state
            self.running = True
            self.stats["daemon_started"] = datetime.now().isoformat()

            # Run main loop
            await self._main_loop()

        except Exception as e:
            logger.error(f"Failed to start Project Index Daemon: {e}")
            raise
        finally:
            await self._cleanup()

    async def _main_loop(self) -> None:
        """Main daemon loop."""
        logger.info("Project Index Daemon main loop started")

        # Initial full scan
        await self._perform_full_scan()

        while self.running and not self.shutdown_requested:
            try:
                # Check if we need to perform operations
                now = datetime.now()

                # Health check
                if self._should_perform_health_check(now):
                    await self._perform_health_check()

                # Full scan
                if self._should_perform_full_scan(now):
                    await self._perform_full_scan()

                # Quick scan for changes
                elif self._should_perform_quick_scan(now):
                    await self._perform_quick_scan()

                # Process pending projects
                if self.pending_projects:
                    await self._process_pending_projects()

                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

                # Reset error count on successful iteration
                self.consecutive_errors = 0

            except Exception as e:
                self.consecutive_errors += 1
                self.last_error_time = datetime.now()
                self.stats["total_errors"] += 1

                logger.error(f"Error in daemon main loop: {e}")

                # If too many consecutive errors, increase wait time
                if self.consecutive_errors >= self.config.max_consecutive_errors:
                    backoff_time = self.config.error_backoff_minutes * 60
                    logger.warning(f"Too many consecutive errors, backing off for {backoff_time}s")
                    await asyncio.sleep(backoff_time)
                    self.consecutive_errors = 0

        logger.info("Project Index Daemon main loop finished")

    def _should_perform_health_check(self, now: datetime) -> bool:
        """Check if we should perform a health check."""
        if not self.last_health_check:
            return True

        return (now - self.last_health_check).total_seconds() >= (
            self.config.health_check_interval_minutes * 60
        )

    def _should_perform_full_scan(self, now: datetime) -> bool:
        """Check if we should perform a full scan."""
        if not self.last_full_scan:
            return True

        return (now - self.last_full_scan).total_seconds() >= (
            self.config.scan_interval_minutes * 60
        )

    def _should_perform_quick_scan(self, now: datetime) -> bool:
        """Check if we should perform a quick scan."""
        if not self.last_quick_scan:
            return True

        return (now - self.last_quick_scan).total_seconds() >= (
            self.config.quick_scan_interval_minutes * 60
        )

    async def _perform_health_check(self) -> None:
        """Perform health check on services."""
        try:
            logger.debug("Performing health check...")

            # Check indexer
            indexer_stats = self.indexer.get_indexer_statistics()

            # Check memory manager
            memory_stats = self.memory_manager.get_performance_stats()

            # Update memory usage
            import psutil

            process = psutil.Process()
            self.stats["memory_usage_mb"] = process.memory_info().rss / 1024 / 1024

            # Log health status
            if indexer_stats.get("memory_connected") and memory_stats.get("memory_connected"):
                logger.debug("Health check passed - all services operational")
            else:
                logger.warning("Health check issues - some services may not be connected")

            self.last_health_check = datetime.now()

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def _perform_full_scan(self) -> None:
        """Perform a full project scan and index update."""
        try:
            logger.info("Starting full project scan...")
            start_time = time.time()

            # Perform full scan
            results = await self.indexer.scan_and_index_all(force_refresh=False)

            # Update statistics
            scan_time = time.time() - start_time
            self.stats["total_scans"] += 1
            self.stats["total_projects_indexed"] += results.get("projects_indexed", 0)
            self.stats["avg_scan_time"] = (
                self.stats["avg_scan_time"] * (self.stats["total_scans"] - 1) + scan_time
            ) / self.stats["total_scans"]
            self.stats["last_successful_scan"] = datetime.now().isoformat()

            logger.info(
                f"Full scan completed: {results.get('projects_found', 0)} projects found, "
                f"{results.get('projects_indexed', 0)} indexed, "
                f"{results.get('projects_updated', 0)} updated in {scan_time:.2f}s"
            )

            # Update project checksums for change detection
            await self._update_project_checksums()

            self.last_full_scan = datetime.now()

        except Exception as e:
            logger.error(f"Full scan failed: {e}")
            raise

    async def _perform_quick_scan(self) -> None:
        """Perform a quick scan to detect changes."""
        try:
            logger.debug("Performing quick scan for changes...")

            if not self.managed_path.exists():
                logger.warning(f"Managed path does not exist: {self.managed_path}")
                return

            # Check for new or modified projects
            project_dirs = [
                d for d in self.managed_path.iterdir() if d.is_dir() and not d.name.startswith(".")
            ]

            changes_detected = False

            for project_dir in project_dirs:
                project_name = project_dir.name

                # Calculate current checksum
                current_checksum = await self._calculate_project_checksum(project_dir)

                # Check if project is new or changed
                if (
                    project_name not in self.project_checksums
                    or self.project_checksums[project_name] != current_checksum
                ):

                    logger.info(f"Change detected in project: {project_name}")
                    self.pending_projects.add(project_name)
                    changes_detected = True

            if changes_detected:
                logger.info(f"Quick scan detected changes in {len(self.pending_projects)} projects")
            else:
                logger.debug("Quick scan completed - no changes detected")

            self.last_quick_scan = datetime.now()

        except Exception as e:
            logger.error(f"Quick scan failed: {e}")
            raise

    async def _process_pending_projects(self) -> None:
        """Process projects that have pending changes."""
        if not self.pending_projects:
            return

        try:
            logger.info(f"Processing {len(self.pending_projects)} pending projects...")

            # Process projects in batches
            processed = 0
            max_batch = self.config.max_concurrent_indexing

            while self.pending_projects and processed < max_batch:
                project_name = self.pending_projects.pop()

                try:
                    # Index specific project
                    project_dir = self.managed_path / project_name
                    if project_dir.exists():
                        result = await self.indexer._index_project(project_dir, force_refresh=False)

                        if result.get("error"):
                            logger.warning(f"Failed to index {project_name}: {result['error']}")
                        else:
                            logger.info(f"Successfully processed pending project: {project_name}")
                            processed += 1

                    # Throttle to prevent overwhelming the system
                    await asyncio.sleep(self.config.throttle_delay_seconds)

                except Exception as e:
                    logger.error(f"Error processing pending project {project_name}: {e}")

            if processed > 0:
                logger.info(f"Processed {processed} pending projects")

        except Exception as e:
            logger.error(f"Error processing pending projects: {e}")

    async def _update_project_checksums(self) -> None:
        """Update stored project checksums for change detection."""
        try:
            if not self.managed_path.exists():
                return

            project_dirs = [
                d for d in self.managed_path.iterdir() if d.is_dir() and not d.name.startswith(".")
            ]

            for project_dir in project_dirs:
                project_name = project_dir.name
                checksum = await self._calculate_project_checksum(project_dir)
                self.project_checksums[project_name] = checksum

            logger.debug(f"Updated checksums for {len(project_dirs)} projects")

        except Exception as e:
            logger.error(f"Error updating project checksums: {e}")

    async def _calculate_project_checksum(self, project_dir: Path) -> str:
        """Calculate a simple checksum for a project directory."""
        try:
            import hashlib

            # Use key files for checksum calculation
            key_files = ["CLAUDE.md", "package.json", "pyproject.toml", "README.md", "Makefile"]
            content_pieces = []

            for file_name in key_files:
                file_path = project_dir / file_name
                if file_path.exists():
                    try:
                        stat = file_path.stat()
                        content_pieces.append(f"{file_name}:{stat.st_mtime}:{stat.st_size}")
                    except Exception:
                        continue

            # Include directory listing
            try:
                dirs = [
                    d.name
                    for d in project_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(".")
                ]
                content_pieces.append(",".join(sorted(dirs)))
            except Exception:
                pass

            # Calculate hash
            content = "\n".join(content_pieces)
            return hashlib.md5(content.encode("utf-8")).hexdigest()

        except Exception:
            return ""

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            logger.info("Cleaning up Project Index Daemon resources...")

            if self.indexer:
                await self.indexer.cleanup()

            if self.memory_manager:
                await self.memory_manager.cleanup()

            self.running = False
            logger.info("Project Index Daemon cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_daemon_status(self) -> dict:
        """Get current daemon status and statistics."""
        return {
            "running": self.running,
            "shutdown_requested": self.shutdown_requested,
            "last_full_scan": self.last_full_scan.isoformat() if self.last_full_scan else None,
            "last_quick_scan": self.last_quick_scan.isoformat() if self.last_quick_scan else None,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "consecutive_errors": self.consecutive_errors,
            "pending_projects": len(self.pending_projects),
            "projects_tracked": len(self.project_checksums),
            "stats": self.stats,
            "config": {
                "scan_interval_minutes": self.config.scan_interval_minutes,
                "quick_scan_interval_minutes": self.config.quick_scan_interval_minutes,
                "health_check_interval_minutes": self.config.health_check_interval_minutes,
            },
        }

    async def force_scan(self) -> dict:
        """Force an immediate full scan."""
        logger.info("Forcing immediate full scan...")
        await self._perform_full_scan()
        return {"status": "completed", "timestamp": datetime.now().isoformat()}

    async def add_project_to_pending(self, project_name: str) -> None:
        """Add a project to the pending processing queue."""
        self.pending_projects.add(project_name)
        logger.info(f"Added {project_name} to pending processing queue")


# CLI integration and daemon management
async def run_daemon(managed_path: Optional[str] = None, config: Optional[DaemonConfig] = None):
    """Run the project index daemon."""
    daemon = ProjectIndexDaemon(managed_path, config)
    await daemon.start()


def create_daemon_config(**kwargs) -> DaemonConfig:
    """Create daemon configuration with overrides."""
    return DaemonConfig(**kwargs)


# Example usage and testing
if __name__ == "__main__":

    async def example_usage():
        """Example usage of ProjectIndexDaemon."""
        print("🔄 Project Index Daemon Example")

        # Create daemon with custom config
        config = create_daemon_config(
            scan_interval_minutes=10, quick_scan_interval_minutes=2  # More frequent for testing
        )

        daemon = ProjectIndexDaemon(config=config)

        try:
            # Run for a short time for demonstration
            print("Starting daemon...")
            await asyncio.wait_for(daemon.start(), timeout=60)  # Run for 1 minute

        except asyncio.TimeoutError:
            print("Daemon test completed")

        except KeyboardInterrupt:
            print("Daemon stopped by user")

        finally:
            await daemon._cleanup()

    # Run example
    asyncio.run(example_usage())
