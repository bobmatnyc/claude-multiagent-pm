"""
Build configuration for claude-multiagent-pm wheel distribution.

This module defines the build process and ensures all necessary files
are included in the Python wheel for proper deployment.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any


class WheelBuildConfig:
    """Configuration for building claude-multiagent-pm wheels."""
    
    # Package metadata
    PACKAGE_NAME = "claude-multiagent-pm"
    VERSION = "1.2.3"
    
    # Required directories to include
    REQUIRED_DIRS = [
        "claude_pm",
        "framework",  # Will be copied to claude_pm/data/framework
    ]
    
    # Files that must be included in the wheel
    CRITICAL_FILES = [
        "claude_pm/__init__.py",
        "claude_pm/cli.py",
        "claude_pm/data/framework/CLAUDE.md",
        "claude_pm/data/framework/VERSION",
        "claude_pm/data/framework/agent-roles/base_agent.md",
    ]
    
    # Minimum file counts for validation
    MIN_FILE_COUNTS = {
        "python_files": 200,
        "markdown_files": 30,
        "framework_files": 10,
        "agent_files": 5,
    }
    
    @classmethod
    def prepare_build(cls) -> None:
        """Prepare the package for building."""
        # Ensure framework data is copied to package
        framework_src = Path("framework")
        framework_dst = Path("claude_pm/data/framework")
        
        if framework_src.exists() and not framework_dst.exists():
            print(f"Copying {framework_src} to {framework_dst}")
            framework_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(framework_src, framework_dst)
    
    @classmethod
    def get_package_data(cls) -> Dict[str, List[str]]:
        """Return package_data configuration for setuptools."""
        return {
            "claude_pm": [
                "py.typed",
                "**/*.md",
                "**/*.yml",
                "**/*.yaml",
                "**/*.json",
                "agents/**/*",
                "config/**/*",
                "templates/**/*",
                "data/framework/**/*",
            ]
        }
    
    @classmethod
    def validate_wheel_contents(cls, wheel_path: Path) -> bool:
        """Validate that the wheel contains all necessary files."""
        import zipfile
        
        with zipfile.ZipFile(wheel_path, 'r') as whl:
            files = whl.namelist()
            
            # Check critical files
            for critical_file in cls.CRITICAL_FILES:
                if critical_file not in files:
                    print(f"Missing critical file: {critical_file}")
                    return False
            
            # Check file counts
            py_files = [f for f in files if f.endswith('.py')]
            md_files = [f for f in files if f.endswith('.md')]
            framework_files = [f for f in files if 'data/framework/' in f]
            agent_files = [f for f in files if 'agent-roles/' in f]
            
            if len(py_files) < cls.MIN_FILE_COUNTS['python_files']:
                print(f"Insufficient Python files: {len(py_files)}")
                return False
            
            if len(md_files) < cls.MIN_FILE_COUNTS['markdown_files']:
                print(f"Insufficient Markdown files: {len(md_files)}")
                return False
            
            if len(framework_files) < cls.MIN_FILE_COUNTS['framework_files']:
                print(f"Insufficient framework files: {len(framework_files)}")
                return False
            
            if len(agent_files) < cls.MIN_FILE_COUNTS['agent_files']:
                print(f"Insufficient agent files: {len(agent_files)}")
                return False
            
            print(f"Wheel validation passed:")
            print(f"  - Python files: {len(py_files)}")
            print(f"  - Markdown files: {len(md_files)}")
            print(f"  - Framework files: {len(framework_files)}")
            print(f"  - Agent files: {len(agent_files)}")
            
            return True


if __name__ == "__main__":
    # Run preparation steps
    WheelBuildConfig.prepare_build()
    print("Build preparation complete. Run 'python -m build' to build the wheel.")