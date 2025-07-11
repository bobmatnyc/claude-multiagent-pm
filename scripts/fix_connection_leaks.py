#!/usr/bin/env python3
"""
Connection Leak Fix Script

This script identifies and terminates processes that may be causing
aiohttp connection leaks in the Claude PM Framework.
"""

import asyncio
import os
import signal
import subprocess
import sys
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_leaked_processes() -> List[Dict[str, Any]]:
    """Find processes that may be causing connection leaks."""
    leaked_processes = []
    
    # Patterns that indicate potentially leaked processes
    leak_patterns = [
        "test_memory_health",
        "cmpm-health",
        "CMPMHealthMonitor",
        "python.*health",
        "memory_service.*timeout",
        "health.*monitor"
    ]
    
    try:
        # Get all Python processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning("Failed to get process list")
            return leaked_processes
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'python' not in line.lower():
                continue
                
            # Check for leak patterns
            for pattern in leak_patterns:
                if pattern.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            leaked_processes.append({
                                "pid": pid,
                                "pattern": pattern,
                                "command": line,
                                "user": parts[0]
                            })
                            break
                        except ValueError:
                            continue
                            
    except Exception as e:
        logger.error(f"Error finding leaked processes: {e}")
    
    return leaked_processes


def terminate_process(pid: int, force: bool = False) -> bool:
    """Terminate a process by PID."""
    try:
        # Check if process exists
        os.kill(pid, 0)
        
        # Try graceful termination first
        if not force:
            logger.info(f"Gracefully terminating process {pid}")
            os.kill(pid, signal.SIGTERM)
            
            # Wait a moment for graceful shutdown
            import time
            time.sleep(2)
            
            # Check if still running
            try:
                os.kill(pid, 0)
                # Still running, need to force kill
                force = True
            except ProcessLookupError:
                # Process terminated gracefully
                logger.info(f"Process {pid} terminated gracefully")
                return True
        
        if force:
            logger.warning(f"Force killing process {pid}")
            os.kill(pid, signal.SIGKILL)
            return True
            
    except ProcessLookupError:
        logger.info(f"Process {pid} not found (already terminated)")
        return True
    except PermissionError:
        logger.error(f"Permission denied to terminate process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {e}")
        return False
    
    return True


async def check_connection_health():
    """Check for connection health using the connection manager."""
    try:
        # Import our connection manager
        sys.path.append('/Users/masa/Projects/claude-multiagent-pm')
        from claude_pm.core.connection_manager import get_connection_manager
        
        # Get connection manager and check stats
        conn_manager = await get_connection_manager()
        stats = conn_manager.get_stats()
        
        logger.info("Connection Manager Stats:")
        logger.info(f"  Total sessions: {stats['total_sessions']}")
        logger.info(f"  Active sessions: {stats['active_sessions']}")
        logger.info(f"  Session names: {stats['session_names']}")
        logger.info(f"  Initialized: {stats['initialized']}")
        logger.info(f"  Shutdown: {stats['shutdown']}")
        
        # Cleanup if needed
        if stats['total_sessions'] > 0:
            logger.info("Cleaning up existing connections...")
            await conn_manager.cleanup_all()
            logger.info("Connection cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking connection health: {e}")
        return False


def main():
    """Main function to fix connection leaks."""
    logger.info("Claude PM Framework - Connection Leak Fix Script")
    logger.info("=" * 60)
    
    # Find leaked processes
    logger.info("Searching for potentially leaked processes...")
    leaked_processes = find_leaked_processes()
    
    if not leaked_processes:
        logger.info("No leaked processes found")
    else:
        logger.warning(f"Found {len(leaked_processes)} potentially leaked processes:")
        
        for proc in leaked_processes:
            logger.warning(f"  PID {proc['pid']}: {proc['pattern']} ({proc['user']})")
            logger.debug(f"    Command: {proc['command']}")
        
        # Ask for confirmation
        if len(sys.argv) > 1 and sys.argv[1] == "--auto":
            terminate_all = True
        else:
            response = input(f"\nTerminate {len(leaked_processes)} processes? (y/N): ")
            terminate_all = response.lower().startswith('y')
        
        if terminate_all:
            logger.info("Terminating leaked processes...")
            for proc in leaked_processes:
                success = terminate_process(proc['pid'])
                if success:
                    logger.info(f"  ✓ Terminated PID {proc['pid']}")
                else:
                    logger.error(f"  ✗ Failed to terminate PID {proc['pid']}")
        else:
            logger.info("Skipping process termination")
    
    # Check connection health
    logger.info("\nChecking connection health...")
    try:
        health_ok = asyncio.run(check_connection_health())
        if health_ok:
            logger.info("✓ Connection health check passed")
        else:
            logger.warning("✗ Connection health check failed")
    except Exception as e:
        logger.error(f"✗ Connection health check error: {e}")
    
    logger.info("\nConnection leak fix completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()