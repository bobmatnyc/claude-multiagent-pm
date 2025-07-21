#!/usr/bin/env python3
"""
Subprocess Migration Helpers
============================

This module provides utilities to help migrate from raw subprocess calls
to the unified SubprocessManager.

Migration patterns:
- subprocess.run() -> manager.run()
- subprocess.Popen() -> manager.run() with appropriate config
- subprocess.check_output() -> manager.run() with check=True
- subprocess.check_call() -> manager.run() with check=True
- subprocess.call() -> manager.run()
"""

import subprocess
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
from .subprocess_manager import SubprocessManager, SubprocessResult


class SubprocessCompat:
    """
    Compatibility layer for migrating subprocess calls.
    
    This class provides drop-in replacements for subprocess functions
    that use the unified SubprocessManager under the hood.
    """
    
    def __init__(self, manager: Optional[SubprocessManager] = None):
        """Initialize with optional custom manager."""
        self.manager = manager or SubprocessManager()
    
    def run(
        self,
        args: Union[str, List[str]],
        *,
        capture_output: bool = False,
        text: bool = None,
        timeout: Optional[float] = None,
        check: bool = False,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Drop-in replacement for subprocess.run().
        
        Returns a subprocess.CompletedProcess for compatibility.
        """
        # Use manager
        result = self.manager.run(
            args,
            capture_output=capture_output,
            text=text if text is not None else False,
            timeout=timeout,
            check=check,
            shell=shell,
            cwd=cwd,
            env=env
        )
        
        # Convert to CompletedProcess
        completed = subprocess.CompletedProcess(
            args=result.command,
            returncode=result.returncode,
            stdout=result.stdout if capture_output else None,
            stderr=result.stderr if capture_output else None
        )
        
        # Raise if check=True and failed
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.command,
                output=result.stdout,
                stderr=result.stderr
            )
        
        return completed
    
    def check_output(
        self,
        args: Union[str, List[str]],
        *,
        timeout: Optional[float] = None,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        text: bool = False,
        **kwargs
    ) -> Union[str, bytes]:
        """
        Drop-in replacement for subprocess.check_output().
        """
        result = self.manager.run(
            args,
            capture_output=True,
            text=text,
            timeout=timeout,
            shell=shell,
            cwd=cwd,
            env=env,
            check=True
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.command,
                output=result.stdout,
                stderr=result.stderr
            )
        
        return result.stdout
    
    def check_call(
        self,
        args: Union[str, List[str]],
        *,
        timeout: Optional[float] = None,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> int:
        """
        Drop-in replacement for subprocess.check_call().
        """
        result = self.manager.run(
            args,
            capture_output=False,
            timeout=timeout,
            shell=shell,
            cwd=cwd,
            env=env,
            check=True
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.command
            )
        
        return 0
    
    def call(
        self,
        args: Union[str, List[str]],
        *,
        timeout: Optional[float] = None,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> int:
        """
        Drop-in replacement for subprocess.call().
        """
        result = self.manager.run(
            args,
            capture_output=False,
            timeout=timeout,
            shell=shell,
            cwd=cwd,
            env=env
        )
        
        return result.returncode


# Global compatibility instance
_compat = SubprocessCompat()

# Export compatibility functions
run = _compat.run
check_output = _compat.check_output
check_call = _compat.check_call
call = _compat.call


def migrate_subprocess_code(code: str) -> str:
    """
    Helper to suggest code migrations.
    
    This is a simple helper that suggests replacements.
    For actual refactoring, manual review is recommended.
    """
    suggestions = []
    
    # Check for subprocess imports
    if 'import subprocess' in code:
        suggestions.append(
            "Replace: import subprocess\n"
            "With:    from claude_pm.utils import subprocess_migration as subprocess"
        )
    
    # Check for direct subprocess calls
    patterns = [
        ('subprocess.run(', 'subprocess_migration.run('),
        ('subprocess.check_output(', 'subprocess_migration.check_output('),
        ('subprocess.check_call(', 'subprocess_migration.check_call('),
        ('subprocess.call(', 'subprocess_migration.call('),
        ('subprocess.Popen(', '# Consider using SubprocessManager.run() instead of Popen'),
    ]
    
    for old, new in patterns:
        if old in code:
            suggestions.append(f"Consider replacing: {old}\nWith: {new}")
    
    return '\n\n'.join(suggestions) if suggestions else "No subprocess calls detected."


# Example usage patterns for migration

def example_migrations():
    """Show example migration patterns."""
    
    print("=== Migration Examples ===\n")
    
    print("1. Basic subprocess.run():")
    print("   OLD: result = subprocess.run(['ls', '-la'], capture_output=True, text=True)")
    print("   NEW: from claude_pm.utils.subprocess_manager import SubprocessManager")
    print("        manager = SubprocessManager()")
    print("        result = manager.run(['ls', '-la'])")
    print()
    
    print("2. subprocess.check_output():")
    print("   OLD: output = subprocess.check_output(['git', 'status'], cwd=repo_path)")
    print("   NEW: result = manager.run(['git', 'status'], cwd=repo_path, check=True)")
    print("        output = result.stdout")
    print()
    
    print("3. subprocess.Popen() with streaming:")
    print("   OLD: proc = subprocess.Popen(['npm', 'install'], stdout=subprocess.PIPE)")
    print("        for line in proc.stdout:")
    print("            print(line)")
    print("   NEW: result = manager.run(['npm', 'install'], stream_output=True)")
    print()
    
    print("4. Async subprocess:")
    print("   OLD: proc = await asyncio.create_subprocess_exec(...)")
    print("   NEW: result = await manager.run_async(['command'], ...)")
    print()
    
    print("5. Using compatibility layer (minimal changes):")
    print("   OLD: import subprocess")
    print("        result = subprocess.run(...)")
    print("   NEW: from claude_pm.utils import subprocess_migration as subprocess")
    print("        result = subprocess.run(...)  # Same API!")


if __name__ == "__main__":
    example_migrations()