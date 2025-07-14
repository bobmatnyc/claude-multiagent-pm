#!/usr/bin/env python3
"""
Python Environment Manager for Claude PM Framework

Handles PATH ordering, Python version detection, and environment validation
to ensure system Python is prioritized over Homebrew Python and proper
version requirements are met.

Author: Engineer Agent
Date: 2025-07-14
Memory Collection: Tracks Python environment issues and user feedback
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PythonEnvironment:
    """Data class representing a Python environment."""
    executable: str
    version: str
    version_info: Tuple[int, int, int]
    is_system: bool
    is_homebrew: bool
    is_pyenv: bool
    is_conda: bool
    path_priority: int
    works: bool
    error_message: Optional[str] = None


@dataclass
class PathAnalysis:
    """Data class representing PATH analysis results."""
    original_path: List[str]
    python_paths: List[str]
    system_python_priority: Optional[int]
    homebrew_python_priority: Optional[int]
    recommended_path: List[str]
    path_issues: List[str]


class PythonEnvironmentManager:
    """
    Comprehensive Python environment manager for Claude PM Framework.
    
    Features:
    - Python version detection and validation
    - PATH ordering management (prioritize system Python)
    - Environment health checking
    - Automatic Python path detection
    - Fallback mechanisms for different Python installations
    - Memory collection for issues and user feedback
    """
    
    MIN_PYTHON_VERSION = (3, 8, 0)
    SUPPORTED_PYTHON_VERSIONS = [(3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13)]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Python Environment Manager."""
        self.logger = logger or self._setup_logger()
        self.memory_collection = []
        self.platform_system = platform.system().lower()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the Python Environment Manager."""
        logger = logging.getLogger("PythonEnvironmentManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def collect_memory(self, category: str, priority: str, content: str, 
                      metadata: Optional[Dict] = None) -> None:
        """Collect memory for issues, feedback, and operational insights."""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "priority": priority,
            "content": content,
            "metadata": metadata or {},
            "source_agent": "Engineer",
            "project_context": "python_environment_management",
            "resolution_status": "open"
        }
        self.memory_collection.append(memory_entry)
        self.logger.info(f"Memory collected: {category} - {priority} - {content[:50]}...")
    
    def detect_all_python_environments(self) -> List[PythonEnvironment]:
        """
        Detect all available Python environments on the system.
        
        Returns:
            List of PythonEnvironment objects representing detected Python installations
        """
        environments = []
        checked_paths = set()
        
        # Common Python executable names
        python_names = ['python3', 'python', 'python3.8', 'python3.9', 'python3.10', 
                       'python3.11', 'python3.12', 'python3.13']
        
        # Search in PATH
        for name in python_names:
            try:
                executable = shutil.which(name)
                if executable and executable not in checked_paths:
                    env = self._analyze_python_executable(executable)
                    if env and env.works:
                        environments.append(env)
                        checked_paths.add(executable)
            except Exception as e:
                self.collect_memory(
                    "error:runtime", "medium", 
                    f"Error detecting Python executable {name}: {e}"
                )
        
        # Search in common installation directories
        common_paths = self._get_common_python_paths()
        for path in common_paths:
            if path.exists() and str(path) not in checked_paths:
                env = self._analyze_python_executable(str(path))
                if env and env.works:
                    environments.append(env)
                    checked_paths.add(str(path))
        
        # Sort by priority (system first, then by version)
        environments.sort(key=lambda x: (not x.is_system, x.path_priority, x.version_info), reverse=True)
        
        self.logger.info(f"Detected {len(environments)} working Python environments")
        return environments
    
    def _get_common_python_paths(self) -> List[Path]:
        """Get common Python installation paths based on platform."""
        paths = []
        
        if self.platform_system == "darwin":  # macOS
            paths.extend([
                Path("/usr/bin/python3"),
                Path("/usr/local/bin/python3"),
                Path("/opt/homebrew/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.8/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.9/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"),
                Path("/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"),
            ])
            
            # Add pyenv paths
            pyenv_root = Path.home() / ".pyenv" / "versions"
            if pyenv_root.exists():
                for version_dir in pyenv_root.iterdir():
                    if version_dir.is_dir():
                        python_exe = version_dir / "bin" / "python3"
                        if python_exe.exists():
                            paths.append(python_exe)
        
        elif self.platform_system == "linux":
            paths.extend([
                Path("/usr/bin/python3"),
                Path("/usr/local/bin/python3"),
                Path("/opt/python/bin/python3"),
            ])
            
            # Add pyenv paths for Linux
            pyenv_root = Path.home() / ".pyenv" / "versions"
            if pyenv_root.exists():
                for version_dir in pyenv_root.iterdir():
                    if version_dir.is_dir():
                        python_exe = version_dir / "bin" / "python3"
                        if python_exe.exists():
                            paths.append(python_exe)
        
        elif self.platform_system == "windows":
            # Windows paths
            python_launcher = Path("C:\\Windows\\py.exe")
            if python_launcher.exists():
                paths.append(python_launcher)
            
            # AppData paths
            appdata_python = Path.home() / "AppData" / "Local" / "Programs" / "Python"
            if appdata_python.exists():
                for version_dir in appdata_python.iterdir():
                    if version_dir.is_dir():
                        python_exe = version_dir / "python.exe"
                        if python_exe.exists():
                            paths.append(python_exe)
        
        return paths
    
    def _analyze_python_executable(self, executable: str) -> Optional[PythonEnvironment]:
        """
        Analyze a Python executable and return environment information.
        
        Args:
            executable: Path to Python executable
            
        Returns:
            PythonEnvironment object or None if analysis fails
        """
        try:
            # Get version information
            result = subprocess.run(
                [executable, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode != 0:
                return PythonEnvironment(
                    executable=executable,
                    version="unknown",
                    version_info=(0, 0, 0),
                    is_system=False,
                    is_homebrew=False,
                    is_pyenv=False,
                    is_conda=False,
                    path_priority=999,
                    works=False,
                    error_message=f"Version check failed: {result.stderr}"
                )
            
            version_str = result.stdout.strip().replace("Python ", "")
            version_parts = version_str.split(".")
            version_info = tuple(int(part) for part in version_parts[:3])
            
            # Determine installation type
            is_system = "/usr/bin" in executable or "/System/" in executable
            is_homebrew = "/opt/homebrew" in executable or "/usr/local" in executable
            is_pyenv = ".pyenv" in executable
            is_conda = "conda" in executable or "anaconda" in executable or "miniconda" in executable
            
            # Determine path priority (lower number = higher priority)
            path_priority = self._calculate_path_priority(executable)
            
            # Test if it works with a simple import
            test_result = subprocess.run(
                [executable, "-c", "import sys; print(sys.version_info[:3])"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            works = test_result.returncode == 0
            error_message = None if works else f"Import test failed: {test_result.stderr}"
            
            return PythonEnvironment(
                executable=executable,
                version=version_str,
                version_info=version_info,
                is_system=is_system,
                is_homebrew=is_homebrew,
                is_pyenv=is_pyenv,
                is_conda=is_conda,
                path_priority=path_priority,
                works=works,
                error_message=error_message
            )
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "medium",
                f"Failed to analyze Python executable {executable}: {e}"
            )
            return None
    
    def _calculate_path_priority(self, executable: str) -> int:
        """Calculate path priority for Python executable (lower = higher priority)."""
        if "/usr/bin" in executable:
            return 1  # Highest priority - system Python
        elif "/System/" in executable:
            return 2  # macOS system Python
        elif "/Library/Frameworks/Python.framework" in executable:
            return 3  # Python.org installer
        elif ".pyenv" in executable:
            return 4  # pyenv managed
        elif "/usr/local/bin" in executable:
            return 5  # Homebrew on Intel Mac
        elif "/opt/homebrew" in executable:
            return 6  # Homebrew on Apple Silicon
        elif "conda" in executable:
            return 7  # Conda environments
        else:
            return 8  # Other installations
    
    def analyze_current_path(self) -> PathAnalysis:
        """
        Analyze the current PATH environment variable for Python-related issues.
        
        Returns:
            PathAnalysis object with detailed PATH analysis
        """
        current_path = os.environ.get("PATH", "").split(os.pathsep)
        python_paths = []
        system_python_priority = None
        homebrew_python_priority = None
        path_issues = []
        
        # Find Python-related paths
        for i, path_entry in enumerate(current_path):
            if any(python_dir in path_entry.lower() for python_dir in 
                   ["/python", "python", ".pyenv", "conda", "homebrew"]):
                python_paths.append(path_entry)
                
                # Check for system Python priority
                if "/usr/bin" in path_entry or "/System/" in path_entry:
                    if system_python_priority is None:
                        system_python_priority = i
                
                # Check for Homebrew Python priority
                if "/opt/homebrew" in path_entry or "/usr/local" in path_entry:
                    if homebrew_python_priority is None:
                        homebrew_python_priority = i
        
        # Identify issues
        if (system_python_priority is not None and 
            homebrew_python_priority is not None and
            homebrew_python_priority < system_python_priority):
            path_issues.append("Homebrew Python has higher priority than system Python")
        
        if not any("/usr/bin" in path for path in current_path[:5]):
            path_issues.append("System binary path (/usr/bin) not in top 5 PATH entries")
        
        # Generate recommended PATH
        recommended_path = self._generate_recommended_path(current_path)
        
        return PathAnalysis(
            original_path=current_path,
            python_paths=python_paths,
            system_python_priority=system_python_priority,
            homebrew_python_priority=homebrew_python_priority,
            recommended_path=recommended_path,
            path_issues=path_issues
        )
    
    def _generate_recommended_path(self, current_path: List[str]) -> List[str]:
        """Generate a recommended PATH with proper Python prioritization."""
        # Essential system paths that should come first
        priority_paths = [
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin"
        ]
        
        # Framework and development paths
        framework_paths = [
            "/Library/Frameworks/Python.framework/Versions/Current/bin",
            "/usr/local/bin"
        ]
        
        # Homebrew paths (lower priority)
        homebrew_paths = [
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin"
        ]
        
        # User paths
        user_paths = [
            str(Path.home() / ".local" / "bin"),
            str(Path.home() / "bin")
        ]
        
        # Build recommended path
        recommended = []
        
        # Add priority paths first
        for path in priority_paths:
            if path not in recommended and Path(path).exists():
                recommended.append(path)
        
        # Add framework paths
        for path in framework_paths:
            if path not in recommended and Path(path).exists():
                recommended.append(path)
        
        # Add user paths
        for path in user_paths:
            if path not in recommended and Path(path).exists():
                recommended.append(path)
        
        # Add remaining paths from current PATH (except Homebrew)
        for path in current_path:
            if (path not in recommended and 
                not any(hb_path in path for hb_path in homebrew_paths) and
                Path(path).exists()):
                recommended.append(path)
        
        # Add Homebrew paths at the end
        for path in homebrew_paths:
            if path not in recommended and Path(path).exists():
                recommended.append(path)
        
        return recommended
    
    def get_best_python_environment(self) -> Optional[PythonEnvironment]:
        """
        Get the best Python environment for Claude PM Framework.
        
        Returns:
            Best PythonEnvironment or None if no suitable environment found
        """
        environments = self.detect_all_python_environments()
        
        if not environments:
            self.collect_memory(
                "error:integration", "critical",
                "No working Python environments detected on system"
            )
            return None
        
        # Filter by minimum version requirement
        suitable_environments = [
            env for env in environments 
            if env.version_info >= self.MIN_PYTHON_VERSION
        ]
        
        if not suitable_environments:
            self.collect_memory(
                "error:integration", "critical",
                f"No Python environments meet minimum version {self.MIN_PYTHON_VERSION}"
            )
            return None
        
        # Prefer system Python, then by version
        best_environment = suitable_environments[0]  # Already sorted by priority
        
        self.logger.info(f"Selected Python environment: {best_environment.executable} "
                        f"(v{best_environment.version})")
        
        return best_environment
    
    def validate_python_environment(self, python_executable: str) -> Tuple[bool, List[str]]:
        """
        Validate a Python environment for Claude PM Framework requirements.
        
        Args:
            python_executable: Path to Python executable to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check if executable exists and is executable
            if not Path(python_executable).exists():
                issues.append(f"Python executable not found: {python_executable}")
                return False, issues
            
            if not os.access(python_executable, os.X_OK):
                issues.append(f"Python executable not executable: {python_executable}")
                return False, issues
            
            # Check version
            env = self._analyze_python_executable(python_executable)
            if not env:
                issues.append("Failed to analyze Python executable")
                return False, issues
            
            if not env.works:
                issues.append(f"Python executable fails basic tests: {env.error_message}")
                return False, issues
            
            if env.version_info < self.MIN_PYTHON_VERSION:
                issues.append(f"Python version {env.version} is below minimum "
                            f"{'.'.join(map(str, self.MIN_PYTHON_VERSION))}")
                return False, issues
            
            # Test required modules
            required_modules = ['subprocess', 'pathlib', 'json', 'sys', 'os']
            for module in required_modules:
                test_result = subprocess.run(
                    [python_executable, "-c", f"import {module}"],
                    capture_output=True,
                    timeout=5
                )
                if test_result.returncode != 0:
                    issues.append(f"Required module '{module}' not available")
            
            # Test pip availability
            pip_result = subprocess.run(
                [python_executable, "-m", "pip", "--version"],
                capture_output=True,
                timeout=5
            )
            if pip_result.returncode != 0:
                issues.append("pip not available with this Python installation")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Validation error: {e}")
            self.collect_memory(
                "error:runtime", "high",
                f"Python environment validation failed for {python_executable}: {e}"
            )
            return False, issues
    
    def create_path_script(self, output_path: Optional[str] = None) -> str:
        """
        Create a shell script to adjust PATH ordering for proper Python prioritization.
        
        Args:
            output_path: Optional custom output path for the script
            
        Returns:
            Path to the created script
        """
        if output_path is None:
            output_path = "/tmp/adjust_python_path.sh"
        
        path_analysis = self.analyze_current_path()
        recommended_path = os.pathsep.join(path_analysis.recommended_path)
        
        script_content = f'''#!/bin/bash
# Python PATH Adjustment Script
# Generated by Claude PM Framework Python Environment Manager
# Date: {datetime.now().isoformat()}

# Original PATH (for reference)
# {os.pathsep.join(path_analysis.original_path)}

# Issues detected:
{chr(10).join(f"# - {issue}" for issue in path_analysis.path_issues)}

echo "🐍 Adjusting PATH to prioritize system Python..."

# Export the optimized PATH
export PATH="{recommended_path}"

echo "✅ PATH adjusted successfully"
echo "🔍 Current Python: $(which python3 2>/dev/null || which python 2>/dev/null || echo 'not found')"

# Verify Python version
if command -v python3 >/dev/null 2>&1; then
    echo "📋 Python version: $(python3 --version)"
else
    echo "⚠️  Warning: python3 not found in PATH"
fi

# Display current PATH for verification
echo "📁 Current PATH:"
echo "$PATH" | tr ':' '\\n' | nl
'''
        
        try:
            with open(output_path, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(output_path, 0o755)
            
            self.logger.info(f"Created PATH adjustment script: {output_path}")
            return output_path
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Failed to create PATH adjustment script: {e}"
            )
            raise
    
    def install_requirements(self, python_executable: str, 
                           requirements_file: Optional[str] = None) -> bool:
        """
        Install Python requirements using the specified Python executable.
        
        Args:
            python_executable: Path to Python executable to use
            requirements_file: Optional custom requirements file path
            
        Returns:
            True if installation succeeded, False otherwise
        """
        if requirements_file is None:
            # Use base requirements from the framework
            framework_path = Path(__file__).parent.parent
            requirements_file = framework_path / "requirements" / "base.txt"
        
        if not Path(requirements_file).exists():
            self.collect_memory(
                "error:integration", "high",
                f"Requirements file not found: {requirements_file}"
            )
            return False
        
        try:
            self.logger.info(f"Installing requirements using {python_executable}")
            
            # Try standard installation first
            result = subprocess.run([
                python_executable, "-m", "pip", "install", "--user", 
                "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Requirements installed successfully")
                return True
            
            # If standard installation fails due to externally managed environment,
            # try with --break-system-packages
            if ("externally-managed-environment" in result.stderr or 
                "externally managed" in result.stderr):
                
                self.logger.info("Retrying installation with --break-system-packages")
                result = subprocess.run([
                    python_executable, "-m", "pip", "install", "--user",
                    "--break-system-packages", "-r", str(requirements_file)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.logger.info("Requirements installed successfully (with --break-system-packages)")
                    return True
            
            # Log failure for memory collection
            self.collect_memory(
                "error:integration", "high",
                f"Requirements installation failed: {result.stderr}"
            )
            self.logger.error(f"Requirements installation failed: {result.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            self.collect_memory(
                "error:runtime", "medium",
                "Requirements installation timed out"
            )
            self.logger.error("Requirements installation timed out")
            return False
        except Exception as e:
            self.collect_memory(
                "error:runtime", "high",
                f"Requirements installation error: {e}"
            )
            self.logger.error(f"Requirements installation error: {e}")
            return False
    
    def generate_environment_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive Python environment report.
        
        Args:
            output_path: Optional custom output path for the report
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/python_environment_report_{timestamp}.json"
        
        # Gather comprehensive environment information
        environments = self.detect_all_python_environments()
        path_analysis = self.analyze_current_path()
        best_env = self.get_best_python_environment()
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python_version": sys.version
            },
            "path_analysis": asdict(path_analysis),
            "detected_environments": [asdict(env) for env in environments],
            "best_environment": asdict(best_env) if best_env else None,
            "minimum_version_requirement": self.MIN_PYTHON_VERSION,
            "supported_versions": self.SUPPORTED_PYTHON_VERSIONS,
            "memory_collection": self.memory_collection
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"Environment report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.collect_memory(
                "error:runtime", "medium",
                f"Failed to generate environment report: {e}"
            )
            raise
    
    def save_memory_collection(self, output_path: Optional[str] = None) -> str:
        """
        Save collected memory data for debugging and improvements.
        
        Args:
            output_path: Optional custom output path for memory data
            
        Returns:
            Path to the saved memory file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/python_env_memory_{timestamp}.json"
        
        memory_data = {
            "collection_timestamp": datetime.now().isoformat(),
            "source_agent": "Engineer",
            "category": "python_environment_management",
            "total_entries": len(self.memory_collection),
            "entries": self.memory_collection
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(memory_data, f, indent=2, default=str)
            
            self.logger.info(f"Memory collection saved: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save memory collection: {e}")
            raise


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Python Environment Manager for Claude PM Framework"
    )
    parser.add_argument("--detect", action="store_true", 
                       help="Detect all Python environments")
    parser.add_argument("--analyze-path", action="store_true",
                       help="Analyze current PATH for Python issues")
    parser.add_argument("--best-env", action="store_true",
                       help="Find the best Python environment")
    parser.add_argument("--validate", type=str, metavar="PYTHON_EXE",
                       help="Validate a specific Python executable")
    parser.add_argument("--create-path-script", type=str, nargs="?", const="/tmp/adjust_python_path.sh",
                       help="Create PATH adjustment script")
    parser.add_argument("--install-requirements", type=str, metavar="PYTHON_EXE",
                       help="Install requirements using specified Python executable")
    parser.add_argument("--generate-report", type=str, nargs="?", const=None,
                       help="Generate comprehensive environment report")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    manager = PythonEnvironmentManager()
    
    try:
        if args.detect:
            environments = manager.detect_all_python_environments()
            print(f"\n🐍 Detected {len(environments)} Python environments:")
            for i, env in enumerate(environments, 1):
                print(f"{i}. {env.executable}")
                print(f"   Version: {env.version}")
                print(f"   Type: {'System' if env.is_system else 'Homebrew' if env.is_homebrew else 'PyEnv' if env.is_pyenv else 'Other'}")
                print(f"   Works: {'✅' if env.works else '❌'}")
                if env.error_message:
                    print(f"   Error: {env.error_message}")
                print()
        
        if args.analyze_path:
            analysis = manager.analyze_current_path()
            print("\n📁 PATH Analysis:")
            print(f"Python-related paths found: {len(analysis.python_paths)}")
            if analysis.path_issues:
                print("Issues detected:")
                for issue in analysis.path_issues:
                    print(f"  ⚠️  {issue}")
            else:
                print("✅ No PATH issues detected")
        
        if args.best_env:
            best_env = manager.get_best_python_environment()
            if best_env:
                print(f"\n🎯 Best Python environment: {best_env.executable}")
                print(f"   Version: {best_env.version}")
                print(f"   Type: {'System' if best_env.is_system else 'Homebrew' if best_env.is_homebrew else 'Other'}")
            else:
                print("\n❌ No suitable Python environment found")
        
        if args.validate:
            is_valid, issues = manager.validate_python_environment(args.validate)
            print(f"\n🔍 Validation of {args.validate}:")
            if is_valid:
                print("✅ Python environment is valid")
            else:
                print("❌ Python environment has issues:")
                for issue in issues:
                    print(f"  - {issue}")
        
        if args.create_path_script:
            script_path = manager.create_path_script(args.create_path_script)
            print(f"\n📝 PATH adjustment script created: {script_path}")
            print("To use: source " + script_path)
        
        if args.install_requirements:
            success = manager.install_requirements(args.install_requirements)
            if success:
                print(f"\n✅ Requirements installed successfully using {args.install_requirements}")
            else:
                print(f"\n❌ Requirements installation failed using {args.install_requirements}")
        
        if args.generate_report is not None:
            report_path = manager.generate_environment_report(args.generate_report)
            print(f"\n📊 Environment report generated: {report_path}")
        
        # Save memory collection if any data was collected
        if manager.memory_collection:
            memory_path = manager.save_memory_collection()
            print(f"\n🧠 Memory collection saved: {memory_path}")
    
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()