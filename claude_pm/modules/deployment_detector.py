"""
Claude PM Framework - Deployment Detector Module

Extracted from cli.py as part of ISS-0085 Phase 2 modular architecture.
This module handles environment detection, service discovery, and system information gathering.

Functions originally from lines ~56-309 in cli.py:
- detect_aitrackdown_info: AI-Trackdown-Tools version and deployment detection
- detect_memory_manager_info: Memory manager service status and version detection 
- get_framework_version: Framework version resolution from VERSION file or package
- detect_claude_md_version: CLAUDE.md version parsing and information display
- display_directory_context: Enhanced directory and system information display

Dependencies:
- subprocess: For command execution and version detection
- pathlib: For path operations and file system navigation
- socket: For service connectivity testing
- json: For API response parsing
- urllib: For HTTP service checks
- rich.console: For formatted output display

Memory Target: <400KB (current: ~539 lines extracted)
"""

import subprocess
import os
import socket
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

# Import rich console for display functionality
try:
    from rich.console import Console
    console = Console()
except ImportError:
    # Fallback console if rich is not available
    class FallbackConsole:
        def print(self, *args, **kwargs):
            print(*args)
    console = FallbackConsole()


class DeploymentDetector:
    """
    Main deployment detector class that orchestrates environment detection.
    
    Provides a unified interface for detecting various system components,
    services, and deployment configurations within the Claude PM Framework.
    """
    
    def __init__(self, timeout: int = 3):
        """
        Initialize deployment detector with configurable timeout.
        
        Args:
            timeout: Default timeout in seconds for subprocess operations
        """
        self.timeout = timeout
        self._cache = {}
    
    def get_full_environment_info(self) -> Dict[str, Any]:
        """
        Get comprehensive environment information including all detected services.
        
        Returns:
            Dictionary containing all environment detection results
        """
        return {
            "aitrackdown_info": detect_aitrackdown_info(timeout=self.timeout),
            "memory_manager_info": detect_memory_manager_info(timeout=self.timeout),
            "framework_version": get_framework_version(),
            "claude_md_version": detect_claude_md_version(),
            "deployment_context": self._get_deployment_context()
        }
    
    def _get_deployment_context(self) -> Dict[str, str]:
        """Get deployment directory context information."""
        deployment_dir = (
            os.environ.get("CLAUDE_PM_DEPLOYMENT_DIR")
            or os.environ.get("CLAUDE_PM_FRAMEWORK_PATH")
            or "Not detected"
        )
        
        if deployment_dir == "Not detected":
            # Try to detect from current structure
            current_path = Path(__file__).parent.parent.parent
            if (current_path / "claude_pm").exists():
                deployment_dir = str(current_path)
        
        working_dir = os.environ.get("CLAUDE_PM_WORKING_DIR", os.getcwd())
        
        return {
            "deployment_dir": deployment_dir,
            "working_dir": working_dir
        }


def detect_aitrackdown_info(timeout: int = 3) -> str:
    """
    Detect AI-Trackdown-Tools version and deployment method with optimized performance.
    
    Checks for AI-Trackdown-Tools in the following priority order:
    1. Global aitrackdown command (most common)
    2. Framework local CLI (second priority) 
    3. atd alias (last priority)
    
    Args:
        timeout: Timeout in seconds for subprocess operations
        
    Returns:
        String describing the detected version and deployment method
    """
    try:
        # Check for global aitrackdown command (most common case first)
        try:
            result = subprocess.run(
                ["aitrackdown", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                # Quick path detection without which command for performance
                try:
                    which_result = subprocess.run(
                        ["which", "aitrackdown"], 
                        capture_output=True, 
                        text=True, 
                        timeout=1
                    )
                    if which_result.returncode == 0:
                        path = which_result.stdout.strip()
                        if ".nvm" in path:
                            deployment = "global (nvm)"
                        elif "/usr/" in path or "/opt/" in path:
                            deployment = "global (system)"
                        elif "npm" in path:
                            deployment = "global (npm)"
                        else:
                            deployment = "global"
                    else:
                        deployment = "global"
                except:
                    deployment = "global"
                return f"v{version} ({deployment})"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check for framework local CLI (second priority)
        framework_cli = Path(__file__).parent.parent.parent / "bin" / "aitrackdown"
        if framework_cli.exists():
            try:
                result = subprocess.run(
                    [str(framework_cli), "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return f"v{version} (framework CLI)"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                # Try reading as file if execution fails
                try:
                    # Framework CLI might be a wrapper, check if it's accessible
                    return "detected (framework CLI)"
                except:
                    pass

        # Check for atd alias (last priority)
        try:
            result = subprocess.run(
                ["atd", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return f"v{version} (atd alias)"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        return "not found"

    except Exception as e:
        # Return more specific error information for debugging
        return "error"


def detect_memory_manager_info(timeout: int = 3) -> str:
    """
    Detect Memory Manager type, version, and status with memory count.
    
    Checks for mem0AI package installation and service status on localhost:8002.
    Provides memory count when service is active and accessible.
    
    Args:
        timeout: Timeout in seconds for subprocess and network operations
        
    Returns:
        String describing memory manager status including version, service state, and memory count
    """
    try:
        # Check for mem0AI package version (optimized)
        mem0_version = None
        try:
            result = subprocess.run(
                ["python3", "-c", "import mem0; print(mem0.__version__)"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                mem0_version = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check mem0AI service status and memory count
        service_status = "inactive"
        memory_count = 0
        try:
            # Quick socket check instead of HTTP request
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # 1 second timeout
            result = sock.connect_ex(("localhost", 8002))
            sock.close()
            if result == 0:
                service_status = "active"
                
                # If service is active, get memory count
                try:
                    with urllib.request.urlopen("http://localhost:8002/memories", timeout=2) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            memory_count = data.get('count', 0)
                except (urllib.error.URLError, json.JSONDecodeError, KeyError):
                    pass  # Keep memory_count as 0 if we can't retrieve it
        except Exception:
            service_status = "inactive"

        # Format output with memory count when service is active
        if mem0_version:
            if service_status == "active" and memory_count > 0:
                return f"mem0AI v{mem0_version} ({service_status}, {memory_count} memories)"
            elif service_status == "active":
                return f"mem0AI v{mem0_version} ({service_status}, 0 memories)"
            else:
                return f"mem0AI v{mem0_version} ({service_status})"
        else:
            if service_status == "active" and memory_count > 0:
                return f"mem0AI not available ({service_status}, {memory_count} memories)"
            elif service_status == "active":
                return f"mem0AI not available ({service_status}, 0 memories)"
            else:
                return f"mem0AI not available ({service_status})"

    except Exception:
        return "error"


def get_framework_version() -> str:
    """
    Get framework version from VERSION file or package info.
    
    Tries to read version information in the following priority order:
    1. VERSION file in parent directory (for source development)
    2. Package version from claude_pm module
    3. "unknown" as last resort fallback
    
    Returns:
        String containing the framework version
    """
    try:
        from pathlib import Path
        import claude_pm
        
        # Try VERSION file first (for source development)
        try:
            version_file = Path(__file__).parent.parent.parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
        except:
            pass
        
        # Fall back to package version
        return claude_pm.__version__
    except:
        # Last resort - should never happen in normal installs
        return "unknown"


def detect_claude_md_version() -> str:
    """
    Detect CLAUDE.md version and provide concise information.
    
    Searches for CLAUDE.md in the current working directory and extracts
    version information using regex pattern matching. Formats the display
    using the framework version for consistency.
    
    Returns:
        String describing CLAUDE.md status and version information
    """
    try:
        import re
        from pathlib import Path

        # Check for CLAUDE.md in current directory
        current_dir = Path.cwd()
        claude_md_path = current_dir / "CLAUDE.md"

        if not claude_md_path.exists():
            return "Not found"

        # Get framework version using our utility function
        framework_version = get_framework_version()

        # Read and parse CLAUDE.md content
        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract CLAUDE_MD_VERSION using regex that supports both formats
            version_match = re.search(r"CLAUDE_MD_VERSION:\s*([\d\.-]+)", content)
            if version_match:
                version = version_match.group(1)

                # Format display using VERSION file for framework part
                if "-" in version:
                    _, serial = version.split("-", 1)
                    return f"v{framework_version}-{serial}"
                else:
                    return f"v{framework_version} (Legacy format)"
            else:
                return "Found (no version detected)"

        except Exception as e:
            return f"Error reading file: {str(e)}"

    except Exception as e:
        return f"Detection error: {str(e)}"


def display_directory_context():
    """
    Display deployment and working directories with enhanced system information.
    
    Shows comprehensive system context including:
    - Deployment directory (framework path)
    - Working directory 
    - CLAUDE.md version information
    - AI-Trackdown-Tools status
    - Memory Manager status
    
    Uses rich console for formatted output with fallback for missing dependencies.
    """
    try:
        # Get deployment directory (framework path) with improved detection
        deployment_dir = (
            os.environ.get("CLAUDE_PM_DEPLOYMENT_DIR")
            or os.environ.get("CLAUDE_PM_FRAMEWORK_PATH")
            or None
        )

        if not deployment_dir:
            # Try to detect from current structure
            current_path = Path(__file__).parent.parent.parent
            if (current_path / "claude_pm").exists():
                deployment_dir = str(current_path)
            else:
                deployment_dir = "Not detected"

        # Get working directory with fallback
        working_dir = os.environ.get("CLAUDE_PM_WORKING_DIR", os.getcwd())

        # Get AI-Trackdown-Tools information
        aitrackdown_info = detect_aitrackdown_info()

        # Get Memory Manager information
        memory_info = detect_memory_manager_info()

        # Get CLAUDE.md version information
        claude_md_info = detect_claude_md_version()

        # Create enhanced display
        console.print(f"[dim]📁 Deployment: {deployment_dir}[/dim]")
        console.print(f"[dim]📂 Working: {working_dir}[/dim]")
        console.print(f"[dim]📄 CLAUDE.md: {claude_md_info}[/dim]")
        console.print(f"[dim]🔧 AI-Trackdown: {aitrackdown_info}[/dim]")
        console.print(f"[dim]🧠 Memory: {memory_info}[/dim]")
        console.print("")  # Add spacing

    except Exception as e:
        # Fallback to basic display if enhanced detection fails
        try:
            # Basic fallback
            deployment_dir = os.environ.get("CLAUDE_PM_DEPLOYMENT_DIR", "Not detected")
            working_dir = os.environ.get("CLAUDE_PM_WORKING_DIR", os.getcwd())
            console.print(f"[dim]📁 Deployment: {deployment_dir}[/dim]")
            console.print(f"[dim]📂 Working: {working_dir}[/dim]")
            console.print("")
        except:
            # Silent failure - don't break CLI if directory detection fails completely
            pass


# Legacy compatibility exports - maintain backward compatibility
_detect_aitrackdown_info = detect_aitrackdown_info
_detect_memory_manager_info = detect_memory_manager_info  
_get_framework_version = get_framework_version
_detect_claude_md_version = detect_claude_md_version
_display_directory_context = display_directory_context